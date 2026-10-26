"""Carga, edición y confirmación explícita del escenario."""
import streamlit as st
from motor_web import (analizar,datos_originales,cargar_csv,
                       PARAMETROS_ORIGINALES)
from core.contratos import EDICIONES, LIMITES
from diagnosticos import nombre_edicion

ETIQUETAS={
    "z":"Z · zona","u":"U · uso","s":"S · suelo","r":"R · reducción",
    "tp":"TP (s)","tl":"TL (s)","t1":"T1 (s)","t2":"T2 (s)","t3":"T3 (s)",
    "altura_piso":"Altura de piso (m)","ct":"Ct · estimación H/Ct",
    "gravedad":"Gravedad (m/s²)",
}

def aplicar(q):
    st.session_state.resultado=q
    st.session_state.revision+=1
    st.session_state.exportaciones=None
    st.rerun()

def entradas(r):
    st.header("Escenario y procedencia")
    st.write("Modifica los parámetros y pulsa Calcular para actualizar el análisis.")
    rev=st.session_state.revision
    st.subheader("Masas y formas modales")
    st.caption("El CSV carga las masas de los cinco pisos y sus tres formas modales. Los períodos y factores se editan abajo. Masas en toneladas.")
    archivo=st.file_uploader("Importar masas y modos CSV",type=["csv"],key=f"csv_{rev}")
    d=r.datos.copy()
    if archivo:
        try:
            d=cargar_csv(archivo.getvalue())
            st.success("CSV leído. Revisa la tabla y pulsa Calcular.")
        except ValueError as exc:
            st.error("Archivo rechazado: "+str(exc))
            st.info("El resultado anterior continúa disponible. Retira el archivo para editar.")
            return
    mostrar_min=st.checkbox("Incluir datos para comparar el cortante mínimo",
                            value=r.premisas_minimo is not None,key=f"min_{rev}",
                            help="Esta comparación requiere datos adicionales del proyecto, que no forman parte del ejemplo original.")
    with st.form(f"escenario_{rev}"):
        ed=st.selectbox("Edición espectral",EDICIONES,
                        index=EDICIONES.index(r.edicion),
                        format_func=nombre_edicion,
                        help="La versión de 2026 incorpora un tramo inicial en el espectro dinámico.")
        a,b=st.columns(2)
        p={}
        for col,claves,titulo in [
            (a,["z","u","s","r","tp","tl"],"Factores espectrales"),
            (b,["t1","t2","t3","altura_piso","ct","gravedad"],"Períodos y geometría"),
        ]:
            with col:
                st.markdown("#### "+titulo)
                for k in claves:
                    low,high=LIMITES[k]
                    p[k]=st.number_input(ETIQUETAS[k],min_value=low,max_value=high,
                        value=float(r.parametros[k]),step=.01,format="%.4f",key=f"{k}_{rev}")
        st.caption("Los factores se declaran manualmente; el programa no selecciona sitio, categoría, EMS o sistema estructural.")
        editada=st.data_editor(d,hide_index=True,num_rows="fixed",
            disabled=["Piso"],key=f"tabla_{rev}",width="stretch",
            column_config={
                "Piso":st.column_config.NumberColumn("Piso",format="%d"),
                "Masa_t":st.column_config.NumberColumn("Masa (t)",min_value=.001,max_value=1e9,format="%.4f"),
                **{f"Modo_{j}":st.column_config.NumberColumn(f"φ{j} (—)",format="%.6g") for j in range(1,4)},
            })
        origen=st.text_area("Origen de los períodos y formas modales",value=r.procedencia,max_chars=2000)
        premisas=None
        if mostrar_min:
            st.markdown("#### Comparación estática / dinámica condicionada")
            st.caption("No se elige automáticamente T1 o H/Ct. La fuente del período y las demás premisas son responsabilidad del usuario.")
            ref=r.premisas_minimo or {}
            t=st.number_input("T estático justificado (s)",.001,20.,
                             value=float(ref.get("periodo_s",r.periodos[0])),format="%.5f")
            just=st.text_input("Justificación y fuente del período",value=ref.get("justificacion_periodo",""))
            reg=st.selectbox("Regularidad declarada",["REGULAR","IRREGULAR"],
                             index=0 if ref.get("regularidad","REGULAR")=="REGULAR" else 1)
            direc=st.text_input("Dirección y modelo de referencia",value=ref.get("direccion",""))
            peso=st.text_input("Sustento del peso sísmico",value=ref.get("sustento_peso",""))
            factores=st.text_input("Sustento de Z, U, S y R",value=ref.get("sustento_factores",""))
            confirmar=st.checkbox("Confirmo las premisas documentadas",value=ref.get("confirmadas",False))
            if confirmar:
                premisas=dict(periodo_s=t,justificacion_periodo=just,regularidad=reg,
                              direccion=direc,sustento_peso=peso,sustento_factores=factores,confirmadas=True)
        submit=st.form_submit_button("Calcular escenario",type="primary",width="stretch")
    if submit:
        try:
            aplicar(analizar(editada,p,edicion=ed,procedencia=origen,control_minimo=premisas))
        except ValueError as exc:
            st.error("Cálculo rechazado: "+str(exc))
    st.download_button("Plantilla CSV del ET1",datos_originales().to_csv(index=False).encode("utf-8-sig"),
                        file_name="plantilla_ET1_masas_modos.csv",mime="text/csv")
    st.caption("Cambiar masas conserva T y φ suministrados. Este posprocesador no resuelve eigenvalores ni actualiza rigidez.")
