"""Comprobación condicionada; no selecciona ni certifica premisas del edificio."""
import numpy as np
from .espectros import factor_c
from .contratos import Control, VERIFICABLE, EXPLORATORIO, NO_EVALUADO

def cortante_minimo(p, masa_total, v_dinamico, edicion, premisas=None):
    if not premisas:
        return {"estado": NO_EVALUADO, "motivo":
                "Faltan período estático justificado, regularidad, dirección y sustento de peso/factores."}
    if not isinstance(premisas,dict):
        raise ValueError("Premisas del control mínimo deben ser un objeto JSON.")
    campos = {"periodo_s", "justificacion_periodo", "regularidad", "direccion",
              "sustento_peso", "sustento_factores", "confirmadas"}
    if set(premisas) != campos:
        raise ValueError("Contrato del control mínimo incompleto o con campos desconocidos.")
    try:
        ts = float(premisas["periodo_s"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Período estático inválido.") from exc
    textos = ("justificacion_periodo", "direccion", "sustento_peso", "sustento_factores")
    if any(not isinstance(premisas[k], str) or len(premisas[k].strip()) < 3
           or len(premisas[k]) > 2000 for k in textos):
        raise ValueError("Documente período, dirección, peso y factores (3–2000 caracteres cada uno).")
    if not np.isfinite(ts) or not .001 <= ts <= 20:
        raise ValueError("Período estático fuera del rango operativo .001–20 s.")
    if premisas["regularidad"] not in ("REGULAR", "IRREGULAR"):
        raise ValueError("Declare regularidad REGULAR o IRREGULAR.")
    if premisas["confirmadas"] is not True:
        return {"estado": NO_EVALUADO, "motivo": "Premisas no confirmadas por el usuario."}
    c = float(factor_c(ts, p["tp"], p["tl"], edicion, estatico=True))
    c_r = max(c / p["r"], .11)  # Art.34.2 (2026) / art.25 anterior.
    peso = masa_total * p["gravedad"]
    vest = p["z"] * p["u"] * p["s"] * c_r * peso
    umbral = .8 if premisas["regularidad"] == "REGULAR" else .9
    minimo = umbral * vest
    factor = max(1., minimo / v_dinamico) if v_dinamico > 0 else None
    satisface = bool(v_dinamico >= minimo)
    return {
        "estado": VERIFICABLE if satisface else EXPLORATORIO,
        "motivo": ("Comparación aritmética con premisas declaradas por el usuario; "
                   "no certifica su validez ni conformidad integral. "
                   + ("No requiere ajuste en esta comparación." if satisface else
                      "Requiere ajuste proporcional de fuerzas; no aplicado automáticamente.")),
        "periodo_estatico_s": ts, "C_estatico": c, "C_R_efectivo": c_r,
        "peso_kN": peso, "V_estatico_kN": vest, "fraccion_minima": umbral,
        "V_minimo_kN": minimo, "V_dinamico_kN": float(v_dinamico),
        "satisface_comparacion": satisface, "factor_fuerzas_requerido": factor,
        "fuente": "E.030 art.44/34 (2026); art.29.4/25 (anterior).",
    }
