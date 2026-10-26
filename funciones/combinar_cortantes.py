"""Funcion 6: combinacion modal indicada en el entregable."""

import numpy as np
import pandas as pd


def combinar_cortantes(pisos, cortantes_modales, factor_reduccion):
    """Calcula Vsum_abs, Vrcsc, Vrnc_h y Vreal para cada piso."""
    pisos = np.asarray(pisos, dtype=int)
    cortantes_modales = np.asarray(cortantes_modales, dtype=float)
    if cortantes_modales.ndim != 2 or cortantes_modales.shape[0] != pisos.size:
        raise ValueError("Debe existir una fila de cortantes por piso.")
    if factor_reduccion <= 0:
        raise ValueError("El factor R debe ser positivo.")

    vsum_abs = np.sum(np.abs(cortantes_modales), axis=1)
    vrcsc = np.sqrt(np.sum(cortantes_modales**2, axis=1))
    vrnc_h = 0.25 * vsum_abs + 0.75 * vrcsc
    vreal = 0.75 * factor_reduccion * vrnc_h

    return pd.DataFrame(
        {
            "Piso": pisos,
            "Vsum_abs_kN": vsum_abs,
            "Vrcsc_kN": vrcsc,
            "Vrnc_h_kN": vrnc_h,
            "Vreal_kN": vreal,
        }
    )
