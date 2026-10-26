"""Normalización segura, reutilizando participación/respuesta numéricas ET1."""
import numpy as np
from funciones.calcular_participacion_modal import calcular_participacion_modal
from funciones.calcular_respuesta_modal import calcular_respuesta_modal

def respuesta_estable(masas, modos, sa):
    escalas = np.max(np.abs(modos), axis=0)
    if np.any(escalas == 0):
        raise ValueError("Ningún vector modal puede ser nulo.")
    q = modos / escalas
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        try:
            gamma_q, participacion = calcular_participacion_modal(masas, q)
            gamma = gamma_q / escalas
            aceleraciones, fuerzas, cortantes = calcular_respuesta_modal(
                masas, q, sa, gamma_q)
        except FloatingPointError as exc:
            raise ValueError("Escala modal no representable con precisión float64.") from exc
    participacion["Gamma"] = gamma
    peso_q = np.sqrt(masas / masas.sum())[:, None] * q
    peso_q /= np.sqrt(np.sum(peso_q ** 2, axis=0))
    corr = peso_q.T @ peso_q
    off = corr - np.eye(3)
    if not all(np.isfinite(x).all() for x in
               (gamma, participacion.to_numpy(), aceleraciones, fuerzas, cortantes, corr)):
        raise ValueError("El cálculo produjo resultados no finitos. Revise escalas.")
    return gamma, participacion, aceleraciones, fuerzas, cortantes, corr
