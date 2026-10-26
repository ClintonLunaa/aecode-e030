"""Cálculo modal a partir de masas, períodos y formas modales ingresados."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
import csv
import hashlib
import json
import numpy as np
import pandas as pd
from funciones.calcular_periodo_aproximado import calcular_periodo_aproximado
from funciones.calcular_espectro import calcular_espectro
from funciones.combinar_cortantes import combinar_cortantes
from core.contratos import (VERSION, ESQUEMA, EDICIONES, LIMITES, UNIDADES,
                           ADVERTENCIAS, Control, VERIFICABLE, EXPLORATORIO,
                           INVALIDO, NO_EVALUADO)
from core.espectros import factor_c
from core.modal import respuesta_estable
from core.norma_e030 import cortante_minimo

COLUMNAS_CSV = ["Piso", "Masa_t", "Modo_1", "Modo_2", "Modo_3"]
PARAMETROS_ORIGINALES = {
    "altura_piso": 3., "ct": 35., "z": .45, "u": 1.,
    "s": 1., "r": 8., "tp": .4, "tl": 2.5,
    "gravedad": 9.81, "t1": .556, "t2": .193, "t3": .126,
}
ORIGEN_ET1 = "ET1: eigenpares suministrados; rigidez y apoyos no documentados."
MAX_BYTES = 2_000_000

def datos_originales():
    return pd.DataFrame([
        [1,31.80,.03112,-.08102,.10415],
        [2,31.80,.05959,-.10193,.03021],
        [3,31.80,.08302,-.05484,-.09525],
        [4,31.80,.09940,.03358,-.05769],
        [5,27.50,.10834,.10609,.09176],
    ], columns=COLUMNAS_CSV)

def validar_datos(datos):
    if not isinstance(datos, pd.DataFrame):
        raise ValueError("Se requiere una tabla de datos.")
    if datos.columns.duplicated().any() or set(datos.columns) != set(COLUMNAS_CSV):
        raise ValueError("Columnas exactas y únicas: " + ",".join(COLUMNAS_CSV))
    if len(datos) != 5:
        raise ValueError("Se conservan exactamente 5 pisos y 3 modos.")
    tabla = datos[COLUMNAS_CSV].copy()
    for c in COLUMNAS_CSV:
        tabla[c] = pd.to_numeric(
            tabla[c].astype(str).str.strip().str.replace(",", ".", regex=False),
            errors="coerce")
    if not np.isfinite(tabla.to_numpy(float)).all():
        raise ValueError("Masas y modos deben ser números finitos, sin celdas vacías.")
    if not np.array_equal(tabla.Piso.to_numpy(), np.arange(1,6)):
        raise ValueError("Pisos 1,2,3,4,5, únicos y ordenados de base a cubierta.")
    if not tabla.Masa_t.between(.001, 1e9).all():
        raise ValueError("Masa por piso fuera del rango operativo 0.001–1e9 t.")
    if np.any(np.max(np.abs(tabla.iloc[:,2:].to_numpy()), axis=0) == 0):
        raise ValueError("Ningún vector modal puede ser nulo.")
    tabla["Piso"] = tabla.Piso.astype(int)
    return tabla.reset_index(drop=True)

def _texto(contenido):
    if not isinstance(contenido, bytes) or not contenido or len(contenido) > MAX_BYTES:
        raise ValueError("Archivo vacío o mayor de 2 MB.")
    try:
        txt = contenido.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo debe estar codificado en UTF-8.") from exc
    if not txt:
        raise ValueError("El archivo no contiene datos (vacío, espacios o solo BOM).")
    return txt

def cargar_csv(contenido):
    """CSV parcial: masas/modos; no restaura parámetros globales."""
    txt = _texto(contenido)
    sep = ";" if ";" in txt.splitlines()[0] else ","
    try:
        filas = list(csv.reader(StringIO(txt), delimiter=sep, strict=True))
        if not filas or filas[0] != COLUMNAS_CSV:
            raise ValueError("Encabezado exacto: " + sep.join(COLUMNAS_CSV))
        if any(len(f) != len(COLUMNAS_CSV) for f in filas[1:]):
            raise ValueError("Cada fila debe contener cinco columnas, sin campos sobrantes.")
        return validar_datos(pd.DataFrame(filas[1:], columns=filas[0]))
    except (csv.Error, pd.errors.ParserError) as exc:
        raise ValueError("Estructura CSV inválida.") from exc

def _parametros(parametros):
    p = PARAMETROS_ORIGINALES.copy()
    if parametros is not None:
        if not isinstance(parametros, dict) or set(parametros) - set(p):
            raise ValueError("Parámetros desconocidos o contrato inválido.")
        p.update(parametros)
    if any(isinstance(v, bool) for v in p.values()):
        raise ValueError("No se admiten booleanos como parámetros numéricos.")
    try:
        p = {k:float(v) for k,v in p.items()}
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Parámetros numéricos inválidos.") from exc
    for k,v in p.items():
        a,b = LIMITES[k]
        if not np.isfinite(v) or not a <= v <= b:
            raise ValueError(f"{k}: valor finito dentro de {a:g}–{b:g}.")
    if p["tl"] <= p["tp"]:
        raise ValueError("Se exige TL > TP > 0.")
    if not p["t1"] > p["t2"] > p["t3"]:
        raise ValueError("Se requiere T1 > T2 > T3 > 0.")
    return p

@dataclass(frozen=True)
class Resultado:
    parametros: dict
    datos: pd.DataFrame
    periodos: np.ndarray
    altura_total: float
    periodo_aproximado: float
    espectro: pd.DataFrame
    participacion: pd.DataFrame
    tabla_modal: pd.DataFrame
    aceleraciones: np.ndarray
    fuerzas: np.ndarray
    cortantes: np.ndarray
    combinacion: pd.DataFrame
    tablas: dict
    gamma: np.ndarray
    avisos: tuple
    edicion: str
    procedencia: str
    controles: tuple
    estado: str
    firma: str
    fecha_utc: str
    correlacion_masa: np.ndarray
    minimo: dict
    premisas_minimo: dict | None

def analizar(datos=None, parametros=None, *, edicion="ET1_LEGACY",
             procedencia=ORIGEN_ET1, control_minimo=None):
    d = validar_datos(datos_originales() if datos is None else datos)
    p = _parametros(parametros)
    if edicion not in EDICIONES:
        raise ValueError("Edición no admitida.")
    if not isinstance(procedencia,str) or not 3 <= len(procedencia.strip()) <= 2000:
        raise ValueError("Documente procedencia de los modos (3–2000 caracteres).")
    # Copia JSON impide mutaciones externas de premisas tras construir el resultado.
    try:
        premisas = json.loads(json.dumps(control_minimo, allow_nan=False))
    except (ValueError,TypeError) as exc:
        raise ValueError("Premisas del control mínimo inválidas.") from exc
    periodos = np.array([p["t1"],p["t2"],p["t3"]])
    masas = d.Masa_t.to_numpy(float)
    modos = d.iloc[:,2:].to_numpy(float)
    h,ta = calcular_periodo_aproximado(5,p["altura_piso"],p["ct"])
    esp = calcular_espectro(periodos, factor_c(periodos,p["tp"],p["tl"],edicion),
                           p["z"],p["u"],p["s"],p["r"],p["gravedad"])
    gamma,part,a,f,v,corr = respuesta_estable(masas,modos,esp.Sa_m_s2.to_numpy())
    comb = combinar_cortantes(d.Piso.to_numpy(),v,p["r"])
    # Se mantiene el nombre interno Vreal_kN solo para regresión ET1.
    if not np.isfinite(comb.to_numpy()).all():
        raise ValueError("Combinación no finita: revise entradas.")
    acumulada = float(part.Participacion_acumulada_pct.iloc[-1])
    off = corr - np.eye(3)
    error = float(np.max(np.abs(off)))
    singular = np.linalg.svd(modos / np.max(np.abs(modos),axis=0),
                             compute_uv=False)
    dependientes = bool(singular[-1] <= 1e-10 * singular[0])
    imposible = acumulada > 100.01  # 0.01 puntos porcentuales, no criterio E.030.
    orto_estado = INVALIDO if dependientes else (
        VERIFICABLE if error <= 1e-8 else EXPLORATORIO)
    cobertura = INVALIDO if imposible else (
        VERIFICABLE if acumulada >= 90 else EXPLORATORIO)
    minimo = cortante_minimo(p,float(masas.sum()),float(comb.Vrnc_h_kN.iloc[0]),
                            edicion,premisas)
    controles = (
        Control("M01","Cobertura de masa",cobertura,
                f"{acumulada:.8f}%; objetivo 90%. >100.01% invalida (tolerancia numérica, no normativa)."),
        Control("M02","Ortogonalidad M / independencia",orto_estado,
                f"Máx. |correlación|={error:.8g}; dependencia lineal={dependientes}. "
                "1e-8 es tolerancia algebraica de diagnóstico, no aceptación de un modelo."),
        Control("M03","Orden de períodos",VERIFICABLE,"T1>T2>T3>0; entradas suministradas."),
        Control("M04","Equilibrio modal",VERIFICABLE,
                "Cortante basal = suma de fuerzas, signos conservados; residuos comprobados."),
        Control("M05","Unidades declaradas",NO_EVALUADO,
                "Hipótesis del contrato: t,m,s,kN. No se deducen las unidades del archivo."),
        Control("M06","Origen de los eigenpares",NO_EVALUADO,
                procedencia + " No se dispone de K para calcular residuales eigen."),
        Control("M07","Conformidad E.030 integral",NO_EVALUADO,
                "No evaluada: faltan verificaciones fuera del alcance del posprocesador."),
        Control("C01","Cortante mínimo condicionado",minimo["estado"],minimo["motivo"]),
    )
    if not np.allclose(v[0],f.sum(axis=0),rtol=1e-12,atol=1e-10):
        raise ValueError("Fallo interno de equilibrio modal.")
    estado = INVALIDO if any(c.estado == INVALIDO for c in controles) else EXPLORATORIO
    avisos = list(ADVERTENCIAS)
    if estado == INVALIDO:
        avisos.insert(0,"INVALIDO: no utilizar estos resultados para diseño ni informe validado.")
    if error > 1e-8:
        avisos.append("Formas suministradas no perfectamente ortogonales en M; "
                      "no se atribuye automáticamente al redondeo.")
    if not np.array_equal(masas,datos_originales().Masa_t.to_numpy()):
        avisos.append("Masas modificadas: períodos y formas NO recalculados desde rigidez.")
    payload = {
        "esquema":ESQUEMA,"version":VERSION,"edicion":edicion,"unidades":UNIDADES,
        "parametros":p,"datos":d.to_dict("records"),
        "procedencia":procedencia,"control_minimo":premisas,
    }
    firma = hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,
                           allow_nan=False,separators=(",",":")).encode()).hexdigest()
    tablas = {"Datos":d,"Espectro":esp,"Participacion":part,
              "Aceleraciones":pd.DataFrame({"Piso":d.Piso,**{
                  f"Aceleracion_M{i+1}_m_s2":a[:,i] for i in range(3)}}),
              "Fuerzas":pd.DataFrame({"Piso":d.Piso,**{f"F_M{i+1}_kN":f[:,i] for i in range(3)}}),
              "Cortantes":pd.DataFrame({"Piso":d.Piso,**{f"V_M{i+1}_kN":v[:,i] for i in range(3)}}),
              "Combinacion":comb}
    return Resultado(p,d,periodos,h,ta,esp,part,esp.merge(part,on="Modo"),a,f,v,
                     comb,tablas,gamma,tuple(avisos),edicion,procedencia,controles,
                     estado,firma,datetime.now(timezone.utc).isoformat(),corr,minimo,premisas)

def escenario(r):
    """Copia profunda restaurable: el consumidor no puede mutar el resultado."""
    obj={"esquema":ESQUEMA,"version":VERSION,"edicion":r.edicion,
         "unidades":UNIDADES,"parametros":r.parametros,
         "datos":r.datos.to_dict("records"),"procedencia":r.procedencia,
         "control_minimo":r.premisas_minimo}
    return json.loads(json.dumps(obj,ensure_ascii=False,allow_nan=False))

def _sin_claves_duplicadas(pares):
    salida = {}
    for k,v in pares:
        if k in salida:
            raise ValueError("Clave JSON duplicada: "+k)
        salida[k]=v
    return salida

def cargar_escenario(contenido):
    try:
        obj = json.loads(_texto(contenido),object_pairs_hook=_sin_claves_duplicadas,
                         parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Número JSON no finito.")))
    except json.JSONDecodeError as exc:
        raise ValueError("JSON inválido.") from exc
    campos = {"esquema","version","edicion","unidades","parametros","datos",
              "procedencia","control_minimo"}
    if not isinstance(obj,dict) or set(obj) != campos:
        raise ValueError("Contrato de escenario JSON incompleto o campos desconocidos.")
    if obj["esquema"] != ESQUEMA or obj["version"] != VERSION or obj["unidades"] != UNIDADES:
        raise ValueError("Esquema, versión o unidades de escenario no admitidos.")
    if not isinstance(obj["parametros"],dict) or set(obj["parametros"]) != set(PARAMETROS_ORIGINALES):
        raise ValueError("El escenario debe contener los 12 parámetros.")
    if not isinstance(obj["datos"],list):
        raise ValueError("Los datos deben ser una lista de registros.")
    try:
        d=pd.DataFrame(obj["datos"])
    except (ValueError,TypeError) as exc:
        raise ValueError("Tabla JSON inválida.") from exc
    return analizar(d,obj["parametros"],edicion=obj["edicion"],
                    procedencia=obj["procedencia"],control_minimo=obj["control_minimo"])
