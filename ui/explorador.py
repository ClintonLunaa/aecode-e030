"""Inspector CCv2 inline: interfaz de lectura; consume resultados, no resuelve el modelo."""
import numpy as np
import streamlit as st

# Presentación del inspector separada de los datos científicos.
from pathlib import Path

CSS = Path(__file__).with_name("mesa_modal.css").read_text(encoding="utf-8")
JS = Path(__file__).with_name("mesa_modal.js").read_text(encoding="utf-8")

_COMPONENT=st.components.v2.component(
    "aecode_inspector_estructural",
    html="<div id='structural-explorer'></div>",
    css=CSS,js=JS,isolate_styles=True)

def payload(r,mode=1,floor=3):
    phi=r.datos[["Modo_1","Modo_2","Modo_3"]].to_numpy(float)
    return {"firma":r.firma,"edition":r.edicion,"state":r.estado,
        "periods":r.periodos.tolist(),"participation":r.participacion.Participacion_pct.tolist(),"masses":r.datos.Masa_t.tolist(),
        "phiRaw":phi.tolist(),"phiNormalized":(phi/np.max(np.abs(phi),axis=0)).tolist(),
        "gamma":r.gamma.tolist(),"Sa":r.espectro.Sa_m_s2.tolist(),
        "F":r.fuerzas.tolist(),"V":r.cortantes.tolist(),
        "Vcomb":r.combinacion.Vrnc_h_kN.tolist(),"h":r.parametros["altura_piso"],
        "focus":{"mode":mode,"floor":floor}}

def foco_valido(value):
    return (isinstance(value,dict) and set(value)=={"mode","floor"}
        and type(value["mode"]) is int and type(value["floor"]) is int
        and value["mode"] in (1,2,3) and value["floor"] in (1,2,3,4,5))

def inspector(r):
    st.session_state.setdefault("lens_mode_control",1)
    st.session_state.setdefault("lens_floor_control",3)
    key="inspector_"+r.firma[:12]
    def sincronizar():
        state=st.session_state.get(key,{})
        selection=state.get("selection") if hasattr(state,"get") else getattr(state,"selection",None)
        if foco_valido(selection):
            st.session_state.lens_mode_control=selection["mode"]
            st.session_state.lens_floor_control=selection["floor"]
    mode=st.session_state.lens_mode_control;floor=st.session_state.lens_floor_control
    _COMPONENT(data=payload(r,mode,floor),key=key,
        default={"selection":{"mode":mode,"floor":floor}},
        on_selection_change=sincronizar,width="stretch",height="content")
    with st.expander("Controles nativos alternativos · modo y piso"):
        st.caption("Misma selección, disponible también con widgets nativos.")
        a,b=st.columns(2)
        a.select_slider("Modo de interés",options=[1,2,3],key="lens_mode_control")
        b.select_slider("Piso de interés",options=[1,2,3,4,5],key="lens_floor_control")
    return mode,floor
