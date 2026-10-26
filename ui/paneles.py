"""Lectura de resultados, comparación y exportación del estado ejecutado."""
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
from motor_web import analizar
from core.contratos import INVALIDO, NO_EVALUADO
from diagnosticos import resumen_calculos, nombre_edicion, estado_claro
from laboratorio import barrido,PARAMETROS
from visualizaciones import (grafico_espectro,grafico_participacion,grafico_formas,
    grafico_fuerzas,grafico_cortantes,grafico_combinado,grafico_edificio_2d,
    tiempos_animacion)
from exportacion import (crear_excel,crear_pdf,csv_contextual,tablas_exportables)
CONFIG={"displaylogo":False,"responsive":True,
        "toImageButtonOptions":{"format":"png","scale":2,"filename":"AECODE_ET2"}}

def plot(fn,r,key):
    st.plotly_chart(fn(r),width="stretch",config=CONFIG,key=key)

def resumen(r):
    k=resumen_calculos(r)
    st.header("Del espectro a la respuesta")
    st.write("Tres modos suministrados. Una lectura clara de sus aportes y límites.")
    a,b=st.columns(2)
    a.metric("Cortante combinado",f'{k["v_combinada"]:.2f} kN',border=True,
             help="0.25 suma absoluta + 0.75 SRSS; respuesta reducida, sin ajuste mínimo automático.")
    b.metric("Masa efectiva acumulada",f'{k["acumulada_pct"]:.2f} %',border=True)
    a,b=st.columns(2)
    a.metric("T1 suministrado",f"{r.periodos[0]:.3f} s",border=True)
    b.metric("Masa sísmica",f'{k["masa_total_t"]:.2f} t',border=True)
    st.caption(f'SRSS basal: {k["v_srss"]:.4f} kN · La cobertura no demuestra origen físico ni conformidad integral.')
    plot(grafico_espectro,r,"resumen_espectro")
    plot(grafico_participacion,r,"resumen_masa")
    if r.minimo["estado"] != NO_EVALUADO:
        st.subheader("Comparación estática y dinámica")
        dato = r.minimo
        st.write(f'Cortante calculado: {dato["V_dinamico_kN"]:.2f} kN; mínimo requerido: {dato["V_minimo_kN"]:.2f} kN.')
        st.caption("Comparación con las hipótesis indicadas en Escenario; las fuerzas no se ajustan automáticamente.")

def respuesta(r):
    st.header("Respuesta por piso")
    st.caption("Orden base → cubierta. Se conservan signos de fuerzas y cortantes modales.")
    plot(grafico_formas,r,"formas")
    plot(grafico_fuerzas,r,"fuerzas")
    plot(grafico_cortantes,r,"cortantes")
    st.caption("Escalones: cada valor corresponde al entrepiso inmediatamente inferior al nivel indicado.")
    plot(grafico_combinado,r,"combinado")
    with st.expander("Ver tablas de fuerzas y cortantes"):
        st.dataframe(r.tablas["Fuerzas"],hide_index=True,width="stretch")
        st.dataframe(r.tablas["Cortantes"],hide_index=True,width="stretch")

def laboratorio(r):
    st.header("Laboratorio de decisiones")
    st.write("Compara con el caso ET1 y aísla el efecto algebraico de un parámetro. Las formas y períodos no se recalculan desde K/M.")
    base=analizar(edicion=r.edicion)
    kb=resumen_calculos(base);ka=resumen_calculos(r)
    filas=[]
    for label,key,unit in [("Vcombinado","v_combinada","kN"),
                            ("Sa1/g","sa1_g","—"),("Masa","masa_total_t","t"),
                            ("Cobertura","acumulada_pct","%")]:
        delta=ka[key]-kb[key]
        filas.append({"Magnitud":label,"Unidad":unit,"ET1":kb[key],"Actual":ka[key],
                       "Δ absoluto":delta,"Δ relativo (%)":100*delta/kb[key]})
    st.dataframe(pd.DataFrame(filas).round(6),hide_index=True,width="stretch")
    st.caption("Comparación con el ejemplo original, calculada con la misma edición espectral.")
    variable=st.selectbox("Variable del experimento",list(PARAMETROS),format_func=PARAMETROS.get)
    rango=st.slider("Rango de variación (%)",10,50,30,5)
    df=barrido(r,variable,rango/100)
    import plotly.graph_objects as go
    from visualizaciones import estilo,contexto,AZUL
    fig=go.Figure()
    fig.add_scatter(x=df.Valor,y=df.Delta_V_pct,mode="lines+markers",
                    name="Δ Vcombinado",line=dict(color=AZUL,width=3))
    estilo(fig,PARAMETROS[variable],"Δ Vcombinado (%)",height=430,legenda=False)
    contexto(fig,r,"Sensibilidad respecto al escenario")
    st.plotly_chart(fig,width="stretch",config=CONFIG,key="sensibilidad")
    vista = df[["Valor", "Vcombinado_kN", "Sa1_g", "Masa_efectiva_pct", "Estado"]].copy()
    vista["Estado"] = vista["Estado"].map(estado_claro)
    st.dataframe(vista, hide_index=True, width="stretch")
    # Descarga con escenario, estado y firma: no una curva sin contexto.
    datos=df.copy();datos["Referencia"]=r.firma[:12];datos["Edicion"]=nombre_edicion(r.edicion)
    datos["Estado"] = datos["Estado"].map(estado_claro)
    st.download_button("Descargar experimento CSV",datos.to_csv(index=False).encode("utf-8-sig"),
                       file_name="sensibilidad_"+r.firma[:8]+".csv",mime="text/csv",
                       disabled=r.estado==INVALIDO)
    st.subheader("Un ciclo de la forma modal")
    modo=st.select_slider("Modo",options=[1,2,3])
    ampl=st.slider("Amplitud ilustrativa (—)",.5,3.,1.5,.1)
    st.plotly_chart(grafico_edificio_2d(r,modo,ampl),width="stretch",config=CONFIG,key="animacion")
    tiempos,dt,slow=tiempos_animacion(r,modo)
    st.caption(f"φ normalizada · T={r.periodos[modo-1]:.4f} s · sin(2πt/T). Reproducción ralentizada ×{slow:.2f}; amplitud sin unidades, no desplazamiento de diseño.")
    st.caption("Se presenta una vista en dos dimensiones para facilitar la lectura de las formas modales.")

def exportacion(r):
    st.header("Exportar resultados")
    st.write("Descarga las tablas o los informes con los parámetros y resultados del escenario actual.")

    if r.estado == INVALIDO:
        st.error("Los datos no son consistentes; corrígelos antes de exportar resultados.")
        st.warning("Revisa las masas y las formas modales antes de exportar.")
        return

    tablas = tablas_exportables(r)
    nombre = st.selectbox("Tabla de resultados", list(tablas))
    st.dataframe(tablas[nombre].round(6), hide_index=True, width="stretch")
    st.download_button(
        "Descargar tabla CSV", csv_contextual(r, nombre),
        file_name=nombre + ".csv", mime="text/csv")

    if st.button("Preparar informes", type="primary"):
        with st.spinner("Preparando reportes..."):
            st.session_state.exportaciones = {
                "firma": r.firma,
                "pdf": crear_pdf(r),
                "xlsx": crear_excel(r),
            }

    informes = st.session_state.get("exportaciones")
    if informes and informes["firma"] == r.firma:
        st.download_button("Descargar informe PDF", informes["pdf"],
                           file_name="Informe_sismico_E030.pdf", mime="application/pdf")
        st.download_button("Descargar reporte Excel", informes["xlsx"],
                           file_name="Resultados_sismicos_E030.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    ruta = Path(__file__).resolve().parents[1] / "assets" / "infografia_et2.png"
    if ruta.exists():
        with st.expander("Infografía del caso original"):
            st.image(str(ruta), width="stretch")
