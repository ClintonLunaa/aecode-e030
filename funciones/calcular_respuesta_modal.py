"""Funcion 5: aceleraciones, fuerzas y cortantes de cada modo."""

import numpy as np


def calcular_respuesta_modal(masas, modos, pseudoaceleraciones, factores_gamma):
    """Calcula U, F y V; las filas se ordenan del piso 1 al ultimo piso."""
    masas = np.asarray(masas, dtype=float)
    modos = np.asarray(modos, dtype=float)
    pseudoaceleraciones = np.asarray(pseudoaceleraciones, dtype=float)
    factores_gamma = np.asarray(factores_gamma, dtype=float)

    if modos.shape != (masas.size, pseudoaceleraciones.size):
        raise ValueError("Las dimensiones de masas, modos y espectro no son compatibles.")
    if factores_gamma.shape != pseudoaceleraciones.shape:
        raise ValueError("Debe existir un factor Gamma por cada modo.")

    aceleraciones = modos * factores_gamma * pseudoaceleraciones
    fuerzas = masas[:, None] * aceleraciones
    cortantes = np.flip(np.cumsum(np.flip(fuerzas, axis=0), axis=0), axis=0)
    return aceleraciones, fuerzas, cortantes
