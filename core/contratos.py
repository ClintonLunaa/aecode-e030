"""Contrato y estados públicos, separados de la aceptación reglamentaria."""
from dataclasses import dataclass

VERSION = "3.0.0-rc1"
ESQUEMA = "aecode.escenario/3"
EDICIONES = ("ET1_LEGACY", "E030_2026")
VERIFICABLE = "VERIFICABLE_DENTRO_ALCANCE"
EXPLORATORIO = "EXPLORATORIO_NO_VALIDADO"
INVALIDO = "INVALIDO"
NO_EVALUADO = "NO_EVALUADO"
HISTORICO = ("Expresión histórica ET1 (no válida como amplificación "
             "reglamentaria de cortantes)")
UNIDADES = {"masa": "t", "longitud": "m", "periodo": "s",
            "aceleracion": "m/s²", "fuerza": "kN", "modo": "adimensional"}
LIMITES = {
    "altura_piso": (.1, 12.), "ct": (.1, 200.), "z": (.01, 1.),
    "u": (.1, 3.), "s": (.1, 3.), "r": (.1, 12.),
    "tp": (.01, 9.), "tl": (.01, 20.), "gravedad": (1., 20.),
    "t1": (.001, 20.), "t2": (.001, 20.), "t3": (.001, 20.),
}
FUENTES = {
    "ET1_LEGACY": "Reproducción horizontal ET1; texto E.030 anterior, arts. 14 y 29.",
    "E030_2026": "RM 183-2026-VIVIENDA, arts. 18, 40, 41, 42.3 y 44.",
}
ALCANCE = ("Posprocesamiento de 5 masas y 3 eigenpares suministrados en una dirección. "
           "No se resuelven K/M, torsión, combinación direccional, derivas ni diseño de elementos.")
ADVERTENCIAS = (
    ALCANCE,
    HISTORICO + ": 0.75 × R × Vcombinado.",
    "La edición espectral no certifica el cumplimiento integral E.030.",
    "Modificar masas no recalcula los períodos ni formas modales.",
    "Unidades declaradas por el usuario: 1 t·m/s² = 1 kN.",
    "NO_VERIFICADO_OPENSees: no existe modelo equivalente documentado.",
)

@dataclass(frozen=True)
class Control:
    codigo: str
    nombre: str
    estado: str
    detalle: str
