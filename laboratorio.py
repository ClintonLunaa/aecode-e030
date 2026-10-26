"""Experimentos de posprocesamiento, con edición y estado conservados."""
import numpy as np
import pandas as pd
from motor_web import analizar
PARAMETROS = {"z":"Z · factor de zona","u":"U · uso","s":"S · suelo",
              "r":"R · reducción","t1":"T1 · período (s)"}

def barrido(r,parametro="z",amplitud=.3,puntos=17):
    if parametro not in PARAMETROS or not 0 < amplitud <= .5 or not 5 <= puntos <= 51:
        raise ValueError("Barrido fuera de contrato.")
    registros=[]
    for f in np.linspace(1-amplitud,1+amplitud,puntos):
        p=r.parametros.copy();p[parametro]*=float(f)
        try:
            q=analizar(r.datos,p,edicion=r.edicion,procedencia=r.procedencia,
                       control_minimo=r.premisas_minimo)
        except ValueError:
            continue
        registros.append({
            "Factor":f,"Valor":p[parametro],
            "Vreal_ET1_kN":float(q.combinacion.Vreal_kN.iloc[0]),
            "Vcombinado_kN":float(q.combinacion.Vrnc_h_kN.iloc[0]),
            "Sa1_g":float(q.espectro.Sa_m_s2.iloc[0]/p["gravedad"]),
            "Masa_efectiva_pct":float(q.participacion.Participacion_acumulada_pct.iloc[-1]),
            "Delta_V_pct":100*(q.combinacion.Vrnc_h_kN.iloc[0]/r.combinacion.Vrnc_h_kN.iloc[0]-1),
            "Estado":q.estado,
        })
    if not registros:raise ValueError("Ningún escenario admisible en el barrido.")
    return pd.DataFrame(registros)
