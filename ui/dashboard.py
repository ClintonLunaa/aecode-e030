"""Panel general: resultados y gráficos del escenario actual."""
from html import escape
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dataclasses import asdict
from diagnosticos import resumen_calculos, nombre_edicion
from core.contratos import INVALIDO, NO_EVALUADO
from ui.explorador import inspector
from visualizaciones import (grafico_espectro,grafico_participacion,grafico_formas,
    grafico_fuerzas,grafico_cortantes,grafico_combinado)
CSS="<style>"+(Path(__file__).with_name("studio.css")).read_text(encoding="utf8")+"</style>"

def estilos():
    st.html(CSS)

def cabecera(r):
    ed=nombre_edicion(r.edicion)
    periods="".join(f'<div><span>MODO {j+1}</span><strong>{t:.3f} <small>s</small></strong></div>' for j,t in enumerate(r.periodos))
    st.html(f"""<header class="studio-hero"><div class="studio-top"><div class="studio-logo"><svg class="studio-mark" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 27V9L16 3l11 6v18M5 15l11-6 11 6M5 21l11-6 11 6M16 3v24M3 27h26" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>AECODE<span>E.030 Studio</span></div><span class="studio-edition">{escape(ed)}</span></div>
    <div class="studio-main"><div><div class="studio-kicker">ANÁLISIS DE RESPUESTA SÍSMICA</div><h1>Análisis modal espectral</h1><p>Consulta el espectro, los modos de vibración y la respuesta de cada piso.</p></div>
    <div class="studio-periods" aria-label="Períodos suministrados">{periods}</div></div></header>""")
    st.html('<div class="aec-meta">CASO DE EJEMPLO · 5 PISOS · 3 MODOS INGRESADOS</div>')

def figura(r,fn,num,title,description,mode=1,floor=3):
    with st.container(border=True,key="figura_"+str(num)):
        st.html(f'<div class="aec-figure-head"><h3><span>{num:02d}</span>{title}</h3><p>{description}</p></div>')
        fig=go.Figure(fn(r))
        # Solo layout de una copia: los arrays físicos y el constructor no cambian.
        for a in fig.layout.annotations or ():
            if a.xref=="paper" and a.yref=="paper" and a.y is not None and a.y>1.1:
                a.text=title+" · "+nombre_edicion(r.edicion)
                a.y=1.12;a.font.size=11
        fig.update_layout(height=435,margin=dict(l=58,r=22,t=65,b=115),
            legend=dict(orientation="h",y=-.24,x=0,font=dict(size=12),itemwidth=30),
            font=dict(family="Segoe UI, Arial, sans-serif",size=12,color="#26354D"))
        fig.update_xaxes(title_font_size=12,tickfont_size=11,title_standoff=8)
        fig.update_yaxes(title_font_size=12,tickfont_size=11,title_standoff=8)
        if num==1:
            fig.add_vline(x=float(r.periodos[mode-1]),line_color="#b98639",line_dash="dot",line_width=2)
        elif num==2:
            fig.add_vrect(x0=mode-.28,x1=mode+.28,fillcolor="#e9c98c",opacity=.16,line_width=0,layer="below")
        elif num in (3,5,6):
            fig.add_hrect(y0=(floor-.1 if num==3 else floor-1),y1=(floor+.1 if num==3 else floor),fillcolor="#e9c98c",opacity=.16,line_width=0,layer="below")
        elif num==4:
            fig.add_hrect(y0=floor-1-.4,y1=floor-1+.4,fillcolor="#e9c98c",opacity=.16,line_width=0,layer="below")
        fig.update_layout(meta={**(fig.layout.meta or {}), "modo_seleccionado":mode, "piso_seleccionado":floor})
        st.plotly_chart(fig,width="stretch",theme=None,key="grafico_"+str(num),
            config={"displaylogo":False,"responsive":True,
                "toImageButtonOptions":{"format":"png","scale":2,"filename":"AECODE_"+r.firma[:8]}})

def dashboard(r):
    k=resumen_calculos(r)
    cabecera(r)
    with st.container(key="indicadores"):
        cols=st.columns(4)
        cols[0].metric("Cortante combinado",f'{k["v_combinada"]:.2f} kN',
            help="Combinación de cortantes: 25 % de suma absoluta y 75 % de SRSS.")
        cols[1].metric("Masa efectiva acumulada",f'{k["acumulada_pct"]:.2f} %',
            help="Cobertura de los tres modos suministrados. No demuestra conformidad integral.")
        cols[2].metric("Período T1",f'{r.periodos[0]:.3f} s')
        cols[3].metric("Masa sísmica",f'{k["masa_total_t"]:.2f} t')
    if r.estado==INVALIDO:
        st.error("Los datos ingresados no son consistentes. Corrígelos en Escenario antes de descargar los resultados.")
    else:
        st.html('<div class="aec-status"><b>Sobre este cálculo</b><span>Los períodos y las formas modales son datos ingresados. El programa calcula la respuesta, pero no determina por sí solo el cumplimiento sísmico del edificio.</span></div>')
    st.html('<div class="aec-section"><h2>Explorador estructural</h2><span>Selecciona un modo y un nivel para seguir su respuesta</span></div>')
    mode,floor=inspector(r)
    st.html(f'<div class="lens-focus"><b>Piso {floor} · modo {mode}</b><span>T = {r.periodos[mode-1]:.3f} s · F = {r.fuerzas[floor-1,mode-1]:.4f} kN · V = {r.cortantes[floor-1,mode-1]:.4f} kN</span></div>')
    st.html('<div class="aec-section"><h2>Lecturas del análisis</h2><span>Espectro, fuerzas y cortantes por nivel</span></div>')
    with st.container(key="studio_charts"):
        views=st.tabs(["01 · Demanda", "02 · Respuesta modal", "03 · Cortantes"])
        with views[0]:
            st.html('<div class="aec-section" id="espectro"><h2>Demanda y participación</h2><span>Espectro calculado y participación de los tres modos</span></div>')
            with st.container(key="par_graficos_1"):
                a,b=st.columns(2,gap="medium")
                with a:figura(r,grafico_espectro,1,"Espectro reducido","Sa/g frente al período. Los puntos identifican los tres modos.",mode,floor)
                with b:figura(r,grafico_participacion,2,"Masa efectiva","Aporte individual y acumulado sobre un único eje porcentual.",mode,floor)
        with views[1]:
            st.html('<div class="aec-section" id="respuesta"><h2>Respuesta en los niveles</h2><span>De base a cubierta · signos conservados</span></div>')
            with st.container(key="par_graficos_2"):
                a,b=st.columns(2,gap="medium")
                with a:figura(r,grafico_formas,3,"Formas modales","Ordenadas relativas normalizadas; no son desplazamientos de diseño.",mode,floor)
                with b:figura(r,grafico_fuerzas,4,"Fuerzas de piso","Fuerzas nodales por modo. El signo expresa la respuesta modal.",mode,floor)
        with views[2]:
            st.html('<div class="aec-section"><h2>Cortantes y combinación</h2><span>Distribución constante en cada entrepiso</span></div>')
            with st.container(key="par_graficos_3"):
                a,b=st.columns(2,gap="medium")
                with a:figura(r,grafico_cortantes,5,"Cortantes modales","Suma de fuerzas desde el nivel indicado hasta cubierta.",mode,floor)
                with b:figura(r,grafico_combinado,6,"Combinación de cortantes","25% suma absoluta + 75% SRSS. SRSS no es CQC.",mode,floor)
    # La comparación normativa se muestra solo cuando el usuario aporta las
    # hipótesis necesarias en Escenario. El caso de ejemplo no contiene esos datos.
    if r.minimo["estado"] != NO_EVALUADO:
        info = r.minimo
        st.html('<div class="aec-section"><h2>Comparación estática y dinámica</h2><span>Con las hipótesis indicadas en Escenario</span></div>')
        with st.container(border=True):
            a, b, c = st.columns(3)
            a.metric("Cortante calculado", f'{info["V_dinamico_kN"]:.2f} kN')
            b.metric("Mínimo de referencia", f'{info["V_minimo_kN"]:.2f} kN')
            c.metric("Comparación", "Cumple el mínimo" if info["satisface_comparacion"] else "Requiere ajuste")
            st.caption("Comparación con las hipótesis declaradas por el usuario. El programa no modifica automáticamente las fuerzas.")
