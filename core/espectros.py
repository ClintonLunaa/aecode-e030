"""Única fuente espectral V3. Fuente: E.030-2026 p.13, arts.18/34/41."""
import numpy as np
from .contratos import EDICIONES

def factor_c(periodos, tp, tl, edicion="ET1_LEGACY", *, estatico=False):
    if edicion not in EDICIONES:
        raise ValueError("Edición no admitida.")
    t = np.asarray(periodos, dtype=float)
    if not np.isfinite(t).all() or np.any(t <= 0):
        raise ValueError("Los períodos deben ser positivos y finitos.")
    if not np.isfinite([tp, tl]).all() or not 0 < tp < tl:
        raise ValueError("Se requiere TL > TP > 0.")
    # Operaciones solo en la máscara: no calcular divisiones fuera de dominio.
    c = np.full(t.shape, 2.5, dtype=float)
    media = (t > tp) & (t <= tl)
    larga = t > tl
    c[media] = 2.5 * tp / t[media]
    c[larga] = 2.5 * (tp / t[larga]) * (tl / t[larga])
    if edicion == "E030_2026" and not estatico:
        corta = t < .2 * tp
        c[corta] = 1 + 7.5 * t[corta] / tp
    return c

def ordenada_g(periodos, p, edicion):
    return p["z"] * p["u"] * p["s"] * factor_c(
        periodos, p["tp"], p["tl"], edicion) / p["r"]
