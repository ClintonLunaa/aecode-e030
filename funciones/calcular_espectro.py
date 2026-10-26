"""Funcion 3: pseudoaceleracion, frecuencia y desplazamiento espectral."""

import numpy as np
import pandas as pd


def calcular_espectro(periodos, factores_c, z, u, s, r, gravedad=9.81):
    """Devuelve una tabla espectral para todos los modos analizados."""
    periodos = np.asarray(periodos, dtype=float)
    factores_c = np.asarray(factores_c, dtype=float)
    if periodos.shape != factores_c.shape:
        raise ValueError("periodos y factores_c deben tener la misma forma.")
    if np.any(periodos <= 0) or min(z, u, s, r, gravedad) <= 0:
        raise ValueError("Los periodos y parametros espectrales deben ser positivos.")

    pseudoaceleracion = gravedad * z * u * factores_c * s / r
    frecuencia_angular = 2.0 * np.pi / periodos
    desplazamiento_espectral = pseudoaceleracion / frecuencia_angular**2

    return pd.DataFrame(
        {
            "Modo": np.arange(1, periodos.size + 1),
            "T_s": periodos,
            "C": factores_c,
            "Sa_m_s2": pseudoaceleracion,
            "Omega_rad_s": frecuencia_angular,
            "Sd_m": desplazamiento_espectral,
        }
    )
