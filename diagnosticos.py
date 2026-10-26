"""Diagnósticos V3; adaptador de siete controles para pruebas históricas."""
from dataclasses import dataclass
import numpy as np
from core.contratos import INVALIDO, VERIFICABLE

@dataclass(frozen=True)
class Control:
    codigo: str
    nombre: str
    estado: str
    detalle: str

def diagnosticar(r):
    """Vista API V2 de compatibilidad; la UI/exports V3 usan r.controles."""
    return [Control(c.codigo,c.nombre,
                    "REVISAR" if c.estado == INVALIDO else
                    "OK" if c.estado == VERIFICABLE else "INFORMATIVO",
                    c.detalle) for c in r.controles[:7]]

def resumen_calculos(r):
    return {
        "masa_total_t":float(r.datos.Masa_t.sum()),
        "sa1_g":float(r.espectro.Sa_m_s2.iloc[0]/r.parametros["gravedad"]),
        "c1":float(r.espectro.C.iloc[0]),"gamma1":float(r.gamma[0]),
        "efectiva_pct":float(r.participacion.Participacion_pct.iloc[0]),
        "acumulada_pct":float(r.participacion.Participacion_acumulada_pct.iloc[-1]),
        "v_srss":float(r.combinacion.Vrcsc_kN.iloc[0]),
        "v_combinada":float(r.combinacion.Vrnc_h_kN.iloc[0]),
        "v_et1":float(r.combinacion.Vreal_kN.iloc[0]),
        "ta_s":r.periodo_aproximado,
    }


def nombre_edicion(edicion):
    return "E.030 (2026)" if edicion == "E030_2026" else "E.030 (versión del ET1)"


def estado_claro(estado):
    return {
        "VERIFICABLE_DENTRO_ALCANCE": "Comprobado",
        "EXPLORATORIO_NO_VALIDADO": "Requiere revisión",
        "NO_EVALUADO": "Sin datos suficientes",
        "INVALIDO": "Datos incorrectos",
    }.get(estado, "Pendiente")


def notas_de_revision(r):
    """Explicaciones para el informe y la interfaz, sin códigos del motor."""
    masa = float(r.participacion.Participacion_acumulada_pct.iloc[-1])
    orto = next(c for c in r.controles if c.codigo == "M02")
    texto_ortogonalidad = (
        "Las tres formas ingresadas son independientes, pero no completamente ortogonales "
        "respecto de las masas (correlación cruzada máxima: "
        f"{float((abs(r.correlacion_masa - np.eye(3))).max()):.4f})."
        if orto.estado != "VERIFICABLE_DENTRO_ALCANCE" and orto.estado != "INVALIDO"
        else "La comprobación de independencia y ortogonalidad de las formas ingresadas no detectó observaciones."
    )
    if orto.estado == "INVALIDO":
        texto_ortogonalidad = "Las formas ingresadas presentan dependencia lineal y deben corregirse."
    if r.minimo["estado"] == "NO_EVALUADO":
        texto_minimo = ("No se comparó el cortante mínimo: es necesario justificar el período estático, "
                         "la regularidad, la dirección y los factores de diseño.")
    else:
        texto_minimo = ("Comparación del cortante mínimo con las hipótesis declaradas: "
                        + estado_claro(r.minimo["estado"]).lower() + ". " + r.minimo["motivo"])
    return [
        ("Participación modal", f"Los tres modos representan el {masa:.2f} % de la masa ingresada."),
        ("Períodos y equilibrio", "Los períodos están ordenados y las fuerzas de piso suman los cortantes modales calculados."),
        ("Formas modales", texto_ortogonalidad),
        ("Origen de los datos", "Los períodos y las formas modales se proporcionan en el ejercicio. No se dispone de la rigidez ni de las condiciones de apoyo para obtenerlos directamente."),
        ("Unidades", "Se emplean toneladas, metros, segundos y kN según las unidades declaradas; comprueba que los archivos importados correspondan a esas unidades."),
        ("Cortante mínimo", texto_minimo),
        ("Alcance", "El programa calcula el espectro, la participación modal, las fuerzas y los cortantes a partir de las masas, los períodos y las formas modales ingresados. La obtención de los modos mediante un modelo estructural y las verificaciones de diseño no forman parte de este ejercicio."),
    ]
