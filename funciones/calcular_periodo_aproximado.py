"""Funcion 1: periodo fundamental aproximado segun H/Ct."""

import numpy as np


def calcular_periodo_aproximado(numero_pisos, altura_piso, coeficiente_ct):
    """Calcula la altura total y el periodo aproximado del edificio."""
    datos = np.asarray([numero_pisos, altura_piso, coeficiente_ct], dtype=float)
    if np.any(datos <= 0):
        raise ValueError("El numero de pisos, la altura y Ct deben ser positivos.")

    altura_total = datos[0] * datos[1]
    periodo_aproximado = altura_total / datos[2]
    return float(altura_total), float(periodo_aproximado)
