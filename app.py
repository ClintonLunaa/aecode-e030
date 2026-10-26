"""Aplicación web del análisis modal espectral E.030."""
import streamlit as st

from motor_web import analizar
from core.contratos import INVALIDO
from ui.entradas import entradas, aplicar
from ui.dashboard import estilos, dashboard
from ui.paneles import respuesta, laboratorio, exportacion
from metodologia_ui import mostrar_metodologia

# Configuración e inicialización del caso base.
st.set_page_config(
    page_title="AECODE · Análisis modal E.030",
    page_icon=":material/architecture:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "resultado" not in st.session_state:
    st.session_state.resultado = analizar(edicion="E030_2026")
    st.session_state.revision = 0
    st.session_state.exportaciones = None

resultado = st.session_state.resultado
estilos()

# Navegación y estado del análisis.
with st.sidebar:
    st.html('<div class="aec-brand"><small>AECODE / PYTHON + IA</small>E.030 Studio</div>')
    pagina = st.radio(
        "Área de trabajo",
        ["Resumen", "Escenario", "Respuesta por piso", "Laboratorio", "Metodología", "Exportación"],
        key="pagina",
    )
    st.caption("Modelo académico · 5 pisos · 3 modos")
    st.badge("Revisar entradas" if resultado.estado == INVALIDO else "Caso de ejemplo",
             color="red" if resultado.estado == INVALIDO else "gray")
    if st.button("Restaurar caso original", icon=":material/restart_alt:", width="stretch"):
        aplicar(analizar(edicion=resultado.edicion))

# Navegación accesible también cuando el panel lateral está cerrado.
with st.container(key="app_navigation"):
    a, b = st.columns([4, 1], vertical_alignment="center")
    with a:
        st.caption("AECODE  /  ANÁLISIS SÍSMICO  /  " + pagina.upper())
    with b:
        with st.popover("Secciones", icon=":material/menu:", width="stretch"):
            for destino in ["Resumen", "Escenario", "Respuesta por piso", "Laboratorio", "Metodología", "Exportación"]:
                st.button(
                    destino,
                    key="nav_" + destino,
                    width="stretch",
                    type="primary" if destino == pagina else "secondary",
                    on_click=lambda vista=destino: st.session_state.update(pagina=vista),
                )

# Mostrar una sola página, sin volver a calcular las demás.
if pagina == "Resumen":
    dashboard(resultado)

elif pagina == "Escenario":
    entradas(resultado)

elif pagina == "Respuesta por piso":
    respuesta(resultado)

elif pagina == "Laboratorio":
    laboratorio(resultado)

elif pagina == "Metodología":
    mostrar_metodologia(resultado)

elif pagina == "Exportación":
    exportacion(resultado)

# El análisis usa períodos y formas modales suministrados; no resuelve un modelo FEM.
