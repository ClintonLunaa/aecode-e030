"""Explicación del procedimiento modal y de sus datos de entrada."""
import streamlit as st
from core.contratos import FUENTES
from diagnosticos import resumen_calculos

def mostrar_metodologia(r):
    p=r.parametros;k=resumen_calculos(r)
    st.header("Cómo se obtiene cada respuesta")
    st.write("Entradas → espectro → participación → fuerzas → cortantes → combinación.")
    with st.expander("1 · Idealización, geometría y procedencia",expanded=True):
        st.write(r.procedencia)
        st.latex(r"H=n h,\qquad T_a=H/C_t")
        st.write(f"H={r.altura_total:.3f} m; Ta={r.periodo_aproximado:.6f} s; T1 suministrado={r.periodos[0]:.6f} s.")
        st.write("Se representan cinco niveles con masas concentradas y se usan tres formas modales y períodos proporcionados por el ejercicio. Si se modifican las masas, los períodos y las formas siguen siendo datos de entrada.")
    with st.expander("2 · Factor C y espectro reducido",expanded=True):
        if r.edicion=="E030_2026":
            st.latex(r"C(T)=\begin{cases}1+7.5T/T_P&T<0.2T_P\\2.5&0.2T_P\leq T\leq T_P\\2.5T_P/T&T_P<T\leq T_L\\2.5T_PT_L/T^2&T>T_L\end{cases}")
        else:
            st.latex(r"C(T)=\begin{cases}2.5&T\leq T_P\\2.5T_P/T&T_P<T\leq T_L\\2.5T_PT_L/T^2&T>T_L\end{cases}")
        st.latex(r"S_a(T)=\frac{ZUCS}{R}g,\quad \omega=2\pi/T,\quad S_d=S_a/\omega^2")
        st.write(FUENTES[r.edicion])
        st.write(f'C(T1)={k["c1"]:.8f}; Sa1/g={k["sa1_g"]:.8f}; Sa1={r.espectro.Sa_m_s2.iloc[0]:.8f} m/s².')
        st.caption("Sd corresponde al oscilador modal, no es directamente deriva. La rama corta dinámica 2026 no se usa en el estático; art.18.3 mantiene C=2.5 hasta TP.")
        st.dataframe(r.espectro.round(8),hide_index=True,width="stretch")
    with st.expander("3 · Participación y normalización"):
        st.latex(r"\Gamma_r=\frac{\phi_r^T M1}{\phi_r^T M\phi_r},\quad M_r^*=\frac{(\phi_r^TM1)^2}{\phi_r^TM\phi_r}")
        st.write(f'Gamma1={k["gamma1"]:.8g}; masa efectiva modo1={k["efectiva_pct"]:.6f}%; acumulada={k["acumulada_pct"]:.8f}%.')
        st.write("Internamente se normaliza cada columna por su máximo absoluto antes de operar; Gamma se devuelve referido al vector original. Se conserva φ·Gamma frente a escala y signo.")
        st.caption("La ortogonalidad de los modos suministrados puede comprobarse respecto de las masas ingresadas; esa comprobación no equivale a resolver el modelo estructural.")
        st.dataframe(r.participacion.round(8),hide_index=True,width="stretch")
    with st.expander("4 · Fuerzas de piso, cortantes y unidades"):
        st.latex(r"a_{ir}=\phi_{ir}\Gamma_rS_{a,r},\quad F_{ir}=m_i a_{ir},\quad V_{ir}=\sum_{k=i}^nF_{kr}")
        st.write("1 t·m/s² = 1 kN. Fuerzas nodales y cortantes conservan signos. Un vector invertido cambia también Gamma y no altera las fuerzas físicas.")
        st.write(f"ΣF del primer modo={r.fuerzas[:,0].sum():.8f} kN; V basal modal={r.cortantes[0,0]:.8f} kN.")
    with st.expander("5 · Combinación de cortantes"):
        st.latex(r"V_{comb}=0.25\sum_r|V_r|+0.75\sqrt{\sum_rV_r^2}")
        st.write("Alternativa E.030 art.42.3 (2026) / art.29.3.4 (anterior). SRSS no es CQC; no se computa matriz de correlación CQC.")
        st.write(f'SRSS={k["v_srss"]:.8f} kN; Vcomb={k["v_combinada"]:.8f} kN.')
        with st.expander("Aclaración respecto al primer entregable"):
            st.write("En el primer entregable se aplicó el factor 0.75 R a un cortante. "
                     "Ese procedimiento no corresponde a la amplificación reglamentaria "
                     "de fuerzas y no interviene en los resultados actuales. "
                     "Se conserva únicamente como antecedente académico.")
    with st.expander("6 · Comprobación del cortante mínimo"):
        st.write("Art.44/34 (2026), art.29.4/25 (anterior): comparar con 80% del estático para regularidad REGULAR y 90% para IRREGULAR. C/R estático ≥0.11.")
        st.latex(r"V_{est}=ZUS\max(C/R,0.11)P,\quad P=\sum m_i g")
        if r.minimo["estado"] == "NO_EVALUADO":
            st.write("Para comparar el cortante mínimo, ingresa y sustenta las hipótesis "
                     "correspondientes en la sección Escenario.")
        else:
            st.write(f'Cortante dinámico: {r.minimo["V_dinamico_kN"]:.2f} kN; '
                     f'mínimo de referencia: {r.minimo["V_minimo_kN"]:.2f} kN.')
            st.write("La comparación utiliza las hipótesis introducidas; no corrige automáticamente las fuerzas.")
        st.caption("La comprobación no constituye una validación completa del diseño estructural.")
    with st.expander("7 · Datos y alcance del análisis"):
        st.markdown(
            "**Datos de entrada.** Masas, períodos y formas modales del ejercicio. "
            "El programa considera una dirección de análisis."
        )
        st.markdown(
            "**Resultados.** Espectro de aceleraciones, participación modal, "
            "fuerzas laterales y cortantes por piso."
        )
        st.markdown(
            "**Alcance.** Para obtener los modos directamente se necesitarían "
            "las propiedades de rigidez y las condiciones de apoyo del edificio. "
            "El diseño y la verificación de sus elementos estructurales "
            "no forman parte de este ejercicio."
        )
        if r.minimo["estado"] == "NO_EVALUADO":
            st.caption(
                "La comparación del cortante mínimo requiere el período estático "
                "justificado, la regularidad y los factores de diseño. Estos datos "
                "pueden completarse en Escenario."
            )
        else:
            st.caption(
                "La comparación del cortante mínimo se realiza con los datos "
                "adicionales introducidos en Escenario."
            )
        st.markdown(
            "[E.030 modificada mediante RM 183-2026-VIVIENDA]"
            "(https://www.gob.pe/institucion/vivienda/normas-legales/8081915-183-2026-vivienda)"
            " · [RM 217-2026-VIVIENDA, disposición transitoria]"
            "(https://www.gob.pe/institucion/vivienda/normas-legales/8219609-217-2026-vivienda)"
        )
