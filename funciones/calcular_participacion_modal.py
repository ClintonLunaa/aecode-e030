"""Funcion 4: factores de participacion y masas modales efectivas."""

import numpy as np
import pandas as pd


def calcular_participacion_modal(masas, modos):
    """Calcula Gamma y el porcentaje de masa efectiva de cada modo."""
    masas = np.asarray(masas, dtype=float)
    modos = np.asarray(modos, dtype=float)
    if modos.ndim != 2 or modos.shape[0] != masas.size:
        raise ValueError("modos debe tener una fila por cada masa de piso.")
    if np.any(masas <= 0):
        raise ValueError("Todas las masas deben ser positivas.")

    matriz_masas = np.diag(masas)
    numeradores = modos.T @ masas
    denominadores = np.diag(modos.T @ matriz_masas @ modos)
    if np.any(np.isclose(denominadores, 0.0)):
        raise ValueError("No se puede calcular la participacion de un modo nulo.")

    factores_gamma = numeradores / denominadores
    masas_efectivas = numeradores**2 / denominadores
    porcentajes = 100.0 * masas_efectivas / masas.sum()
    porcentajes_acumulados = np.cumsum(porcentajes)

    tabla = pd.DataFrame(
        {
            "Modo": np.arange(1, modos.shape[1] + 1),
            "Gamma": factores_gamma,
            "Masa_efectiva_t": masas_efectivas,
            "Participacion_pct": porcentajes,
            "Participacion_acumulada_pct": porcentajes_acumulados,
        }
    )
    return factores_gamma, tabla
