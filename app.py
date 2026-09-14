"""FRAUD//SCAN - dashboard de analisis de fraude con tarjeta de credito.

Ejecutar:  streamlit run app.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import fraud_stats as fs
import theme as th

st.set_page_config(
    page_title="FRAUD//SCAN",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(th.CSS, unsafe_allow_html=True)


@st.cache_data
def cargar() -> pd.DataFrame:
    return fs.load_data()


@st.cache_data
def scorecard_global(_df: pd.DataFrame) -> dict:
    # La scorecard se construye SIEMPRE sobre el dataset completo: si dependiera del filtro,
    # la misma transaccion cambiaria de puntuacion segun lo que el usuario tuviera marcado.
    return fs.build_scorecard(_df)


DF = cargar()
BASE_GLOBAL = float(DF[fs.TARGET].mean())
CARD = scorecard_global(DF)

CLAVES_FILTRO = [
    "f_amount", "f_hour", "f_trust", "f_vel", "f_age",
    "f_cat", "f_ext", "f_loc", "f_clase",
]


def reset_filtros() -> None:
    for clave in CLAVES_FILTRO:
        st.session_state.pop(clave, None)


# --------------------------------------------------------------------------------------
# Sidebar: filtros
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="banner"><div class="titulo">FRAUD//SCAN</div>'
        '<div class="sub">panel de control · v1.0</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(th.prompt("FILTROS"), unsafe_allow_html=True)

    rango_monto = st.slider(
        "MONTO ($)",
        float(DF.amount.min()), float(DF.amount.max()),
        (float(DF.amount.min()), float(DF.amount.max())),
        key="f_amount",
    )
    rango_hora = st.slider("HORA DEL DIA", 0, 23, (0, 23), key="f_hour")
    rango_trust = st.slider(
        "CONFIANZA DEL DISPOSITIVO",
        int(DF.device_trust_score.min()), int(DF.device_trust_score.max()),
        (int(DF.device_trust_score.min()), int(DF.device_trust_score.max())),
        key="f_trust",
    )
    rango_vel = st.slider(
        "VELOCIDAD 24H",
        int(DF.velocity_last_24h.min()), int(DF.velocity_last_24h.max()),
        (int(DF.velocity_last_24h.min()), int(DF.velocity_last_24h.max())),
        key="f_vel",
    )
    rango_edad = st.slider(
        "EDAD DEL TITULAR",
        int(DF.cardholder_age.min()), int(DF.cardholder_age.max()),
        (int(DF.cardholder_age.min()), int(DF.cardholder_age.max())),
        key="f_age",
    )

    categorias = sorted(DF.merchant_category.unique())
    sel_cat = st.multiselect("CATEGORIA DE COMERCIO", categorias, default=categorias, key="f_cat")
    sel_ext = st.radio("TRANSACCION EXTRANJERA", ["Todas", "Si", "No"], horizontal=True, key="f_ext")
    sel_loc = st.radio("DISCREPANCIA DE UBICACION", ["Todas", "Si", "No"], horizontal=True, key="f_loc")
    sel_clase = st.radio("CLASE", ["Todas", "Solo fraude", "Solo legitimas"], key="f_clase")

    st.markdown(th.prompt("OPCIONES"), unsafe_allow_html=True)
    usar_global = st.checkbox(
        "Calcular predictores sobre el dataset completo",
        value=False,
        help="Activalo cuando el filtro deje muy pocos fraudes: el lift y el IV necesitan "
             "ambas clases y una muestra suficiente para significar algo.",
    )
    st.button("RESET", on_click=reset_filtros)


def aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    m = (
        df.amount.between(*rango_monto)
        & df.transaction_hour.between(*rango_hora)
        & df.device_trust_score.between(*rango_trust)
        & df.velocity_last_24h.between(*rango_vel)
        & df.cardholder_age.between(*rango_edad)
        & df.merchant_category.isin(sel_cat)
    )
    if sel_ext != "Todas":
        m &= df.foreign_transaction == int(sel_ext == "Si")
    if sel_loc != "Todas":
        m &= df.location_mismatch == int(sel_loc == "Si")
    if sel_clase == "Solo fraude":
        m &= df[fs.TARGET] == 1
    elif sel_clase == "Solo legitimas":
        m &= df[fs.TARGET] == 0
    return df[m]


F = aplicar_filtros(DF)

pct = len(F) / len(DF) * 100 if len(DF) else 0
st.sidebar.markdown(
    th.nota(f"<b>{len(F):,}</b> de {len(DF):,} transacciones ({pct:.1f}%)".replace(",", ".")),
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------------------
# Cabecera
# --------------------------------------------------------------------------------------
st.markdown(
    '<div class="banner"><div class="titulo">FRAUD//SCAN</div>'
    '<div class="sub">analisis de transacciones con tarjeta · deteccion de patrones de fraude'
    '</div></div>',
    unsafe_allow_html=True,
)

if F.empty:
    st.error("El filtro no deja ninguna transaccion. Pulsa RESET en la barra lateral.")
    st.stop()

tab_overview, tab_pred, tab_tx = st.tabs(["> OVERVIEW", "> PREDICTORES", "> TRANSACCIONES"])


# --------------------------------------------------------------------------------------
# OVERVIEW
# --------------------------------------------------------------------------------------
with tab_overview:
    n_fraude = int(F[fs.TARGET].sum())
    tasa = F[fs.TARGET].mean()
    monto_riesgo = float(F.loc[F[fs.TARGET] == 1, "amount"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transacciones", f"{len(F):,}".replace(",", "."))
    c2.metric("Fraudes", f"{n_fraude:,}".replace(",", "."))
    # Sin filtros el delta seria "+0.00 pp" con flecha roja: ruido visual, mejor ocultarlo.
    desvio = (tasa - BASE_GLOBAL) * 100
    c3.metric(
        "Tasa de fraude",
        f"{tasa * 100:.2f}%",
        delta=f"{desvio:+.2f} pp vs global" if abs(desvio) >= 0.01 else None,
        delta_color="inverse",
    )
    c4.metric("Monto en riesgo", f"${monto_riesgo:,.0f}".replace(",", "."))

    st.markdown(
        th.prompt("tasa de fraude por hora", "la madrugada concentra el riesgo"),
        unsafe_allow_html=True,
    )
    por_hora = F.groupby("transaction_hour")[fs.TARGET].agg(["mean", "count"]).reindex(range(24))
    fig = go.Figure(
        go.Bar(
            x=por_hora.index,
            y=por_hora["mean"] * 100,
            marker=dict(
                color=por_hora["mean"].fillna(0),
                colorscale=th.ESCALA_RIESGO,
                line=dict(color=th.GRID, width=1),
            ),
            customdata=np.stack([por_hora["count"].fillna(0)], axis=-1),
            hovertemplate="Hora %{x}:00<br>Tasa %{y:.2f}%<br>%{customdata[0]:.0f} transacciones<extra></extra>",
        )
    )
    fig.add_hline(
        y=BASE_GLOBAL * 100,
        line=dict(color=th.CIAN, dash="dot", width=1),
        annotation_text=f"base global {BASE_GLOBAL * 100:.2f}%",
        annotation_font_color=th.CIAN,
    )
    fig.update_layout(**th.plotly_layout(300))
    fig.update_xaxes(title="hora", dtick=2)
    fig.update_yaxes(title="% fraude")
    st.plotly_chart(fig, width="stretch")

    izq, der = st.columns(2)

    with izq:
        st.markdown(
            th.prompt("confianza del dispositivo", "el predictor mas fuerte"),
            unsafe_allow_html=True,
        )
        t = fs.binned_rates(F, "device_trust_score")
        fig = go.Figure(
            go.Bar(
                x=t["bin"].astype(str),
                y=t["tasa"] * 100,
                marker=dict(color=[th.ROJO, th.AMBAR, th.VERDE_TENUE, th.VERDE]),
                text=[f"{v:.2f}%" for v in t["tasa"] * 100],
                textposition="outside",
                textfont=dict(color=th.TEXTO),
                customdata=np.stack([t["n"], t["n_fraude"]], axis=-1),
                hovertemplate="%{x}<br>Tasa %{y:.2f}%<br>%{customdata[1]} de %{customdata[0]}<extra></extra>",
            )
        )
        fig.update_layout(**th.plotly_layout(300))
        fig.update_yaxes(title="% fraude")
        st.plotly_chart(fig, width="stretch")

    with der:
        st.markdown(
            th.prompt("monto", "sin apenas poder predictivo"),
            unsafe_allow_html=True,
        )
        fig = go.Figure()
        for etiqueta, clase, color in [("Legitimas", 0, th.VERDE_TENUE), ("Fraude", 1, th.ROJO)]:
            serie = F.loc[F[fs.TARGET] == clase, "amount"]
            if not serie.empty:
                fig.add_trace(
                    go.Histogram(
                        x=serie,
                        name=etiqueta,
                        histnorm="probability density",
                        opacity=0.6,
                        marker=dict(color=color),
                        nbinsx=40,
                    )
                )
        fig.update_layout(**th.plotly_layout(300), barmode="overlay")
        fig.update_xaxes(title="monto ($)")
        fig.update_yaxes(title="densidad")
        st.plotly_chart(fig, width="stretch")
        st.markdown(
            th.nota(
                "Las dos distribuciones se solapan casi por completo: por eso el monto queda "
                "abajo en el ranking de predictores."
            ),
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------------------
# PREDICTORES
# --------------------------------------------------------------------------------------
with tab_pred:
    base_datos = DF if usar_global else F
    origen = "dataset completo" if usar_global else "seleccion filtrada"
    fiable, motivo = fs.es_fiable(base_datos)

    st.markdown(
        th.prompt("ranking de predictores", f"calculado sobre la {origen}"),
        unsafe_allow_html=True,
    )
    st.markdown(
        th.nota(
            f"Tasa base ({origen}): <b>{base_datos[fs.TARGET].mean() * 100:.2f}%</b> · "
            f"global: <b>{BASE_GLOBAL * 100:.2f}%</b> · "
            f"{int(base_datos[fs.TARGET].sum())} fraudes sobre {len(base_datos):,} filas".replace(",", ".")
        ),
        unsafe_allow_html=True,
    )

    if not fiable:
        st.warning(
            f"{motivo}\n\nActiva **Calcular predictores sobre el dataset completo** en la barra "
            "lateral, o amplia el filtro. No se muestran lift ni IV porque con esta muestra "
            "serian enganosos."
        )
    else:
        rank = fs.rank_features(base_datos)
        vista = rank[["variable", "poder", "iv", "lift_max", "bin_riesgo", "tasa_max", "corr"]].copy()
        vista["tasa_max"] = vista["tasa_max"] * 100

        st.dataframe(
            vista,
            column_config={
                "variable": st.column_config.TextColumn("VARIABLE", width="medium"),
                "poder": st.column_config.TextColumn("PODER", width="small"),
                "iv": st.column_config.ProgressColumn(
                    "INFORMATION VALUE",
                    format="%.3f",
                    min_value=0.0,
                    max_value=float(max(rank["iv"].max(), 0.001)),
                ),
                "lift_max": st.column_config.NumberColumn("LIFT MAX", format="%.2fx"),
                "bin_riesgo": st.column_config.TextColumn("SEGMENTO MAS RIESGOSO"),
                "tasa_max": st.column_config.NumberColumn("TASA EN ESE SEGMENTO", format="%.2f%%"),
                "corr": st.column_config.NumberColumn("CORRELACION", format="%.3f"),
            },
            hide_index=True,
            width="stretch",
        )
        st.markdown(
            th.nota(
                "Pulsa cualquier cabecera para reordenar. <b>Information Value</b> mide cuanta "
                "informacion aporta la variable para separar fraude de legitimo: "
                "&lt;0,02 inutil · &lt;0,1 debil · &lt;0,3 medio · superior fuerte. "
                "<b>Lift</b> es cuantas veces la tasa base alcanza el peor segmento "
                f"(solo se consideran segmentos con al menos {fs.MIN_BIN_N} transacciones)."
            ),
            unsafe_allow_html=True,
        )

        fuertes = rank[rank["poder"].isin(["FUERTE", "MEDIO"])]
        flojas = rank[rank["poder"].isin(["DEBIL", "INUTIL"])]
        chips_si = "".join(
            f'<span class="chip" style="color:{th.COLOR_PODER[p]}">{v} · IV {i:.2f}</span>'
            for v, p, i in zip(fuertes["variable"], fuertes["poder"], fuertes["iv"])
        )
        chips_no = "".join(
            f'<span class="chip" style="color:{th.COLOR_PODER[p]}">{v} · IV {i:.2f}</span>'
            for v, p, i in zip(flojas["variable"], flojas["poder"], flojas["iv"])
        )
        col_si, col_no = st.columns(2)
        with col_si:
            st.markdown(th.prompt("SI predicen fraude"), unsafe_allow_html=True)
            st.markdown(chips_si or "-", unsafe_allow_html=True)
        with col_no:
            st.markdown(th.prompt("NO predicen fraude"), unsafe_allow_html=True)
            st.markdown(chips_no or "-", unsafe_allow_html=True)

        # ---------------- Drill-down por variable ----------------
        st.markdown(th.prompt("detalle por variable"), unsafe_allow_html=True)
        etiqueta_sel = st.selectbox("Variable a inspeccionar", rank["variable"].tolist())
        col_sel = rank.loc[rank["variable"] == etiqueta_sel, "columna"].iloc[0]

        base_ref = base_datos[fs.TARGET].mean()
        detalle = fs.woe_iv(base_datos, col_sel)
        tasas = fs.binned_rates(base_datos, col_sel)
        detalle = detalle.merge(tasas[["bin", "lift"]], on="bin")

        g_izq, g_der = st.columns([3, 2])
        with g_izq:
            fig = go.Figure(
                go.Bar(
                    x=detalle["bin"].astype(str),
                    y=detalle["tasa"] * 100,
                    marker=dict(
                        color=detalle["lift"].fillna(0),
                        colorscale=th.ESCALA_RIESGO,
                        cmin=0,
                        cmax=max(float(detalle["lift"].max() or 1), 1.0),
                        line=dict(color=th.GRID, width=1),
                    ),
                    text=[f"{v:.2f}%" for v in detalle["tasa"] * 100],
                    textposition="outside",
                    textfont=dict(color=th.TEXTO),
                    customdata=np.stack([detalle["n"], detalle["n_fraude"], detalle["lift"]], axis=-1),
                    hovertemplate=(
                        "%{x}<br>Tasa %{y:.2f}%<br>Lift %{customdata[2]:.2f}x"
                        "<br>%{customdata[1]} fraudes de %{customdata[0]}<extra></extra>"
                    ),
                )
            )
            fig.add_hline(
                y=base_ref * 100,
                line=dict(color=th.CIAN, dash="dot", width=1),
                annotation_text=f"base {base_ref * 100:.2f}%",
                annotation_font_color=th.CIAN,
            )
            fig.update_layout(
                **th.plotly_layout(340, titulo=f"Tasa de fraude por segmento · {etiqueta_sel}")
            )
            fig.update_yaxes(title="% fraude")
            st.plotly_chart(fig, width="stretch")

        with g_der:
            tabla = detalle[["bin", "n", "n_fraude", "tasa", "lift", "woe", "iv_bin"]].copy()
            tabla["tasa"] = tabla["tasa"] * 100
            st.dataframe(
                tabla,
                column_config={
                    "bin": st.column_config.TextColumn("SEGMENTO"),
                    "n": st.column_config.NumberColumn("N", format="%d"),
                    "n_fraude": st.column_config.NumberColumn("FRAUDES", format="%d"),
                    "tasa": st.column_config.NumberColumn("TASA", format="%.2f%%"),
                    "lift": st.column_config.NumberColumn("LIFT", format="%.2fx"),
                    "woe": st.column_config.NumberColumn("WoE", format="%.3f"),
                    "iv_bin": st.column_config.NumberColumn("IV PARCIAL", format="%.3f"),
                },
                hide_index=True,
                width="stretch",
            )
            st.markdown(
                th.nota(
                    "<b>WoE</b> positivo = el segmento concentra mas fraude de lo que le "
                    "tocaria por tamano. La columna N indica si el segmento tiene muestra "
                    "suficiente para fiarse del dato."
                ),
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------------------
# TRANSACCIONES
# --------------------------------------------------------------------------------------
with tab_tx:
    st.markdown(
        th.prompt("registro de transacciones", "ordenable y exportable"),
        unsafe_allow_html=True,
    )

    tabla = F.copy()
    tabla["risk_score"] = fs.risk_score(tabla, CARD)

    COLUMNAS = {
        "risk_score": "RIESGO",
        "transaction_id": "ID",
        "amount": "MONTO",
        "transaction_hour": "HORA",
        "merchant_category": "COMERCIO",
        "foreign_transaction": "EXTRANJERA",
        "location_mismatch": "UBIC. DISCREPA",
        "device_trust_score": "CONFIANZA DISP.",
        "velocity_last_24h": "VELOCIDAD 24H",
        "cardholder_age": "EDAD",
        "is_fraud": "FRAUDE",
    }

    c1, c2, c3 = st.columns([2, 1, 1])
    campo = c1.selectbox(
        "Ordenar por",
        list(COLUMNAS),
        format_func=lambda c: COLUMNAS[c],
        index=0,
    )
    sentido = c2.radio("Sentido", ["Descendente", "Ascendente"], horizontal=True)
    limite = c3.number_input("Filas a mostrar", 50, 10000, 500, step=50)

    tabla = tabla.sort_values(campo, ascending=(sentido == "Ascendente")).head(int(limite))

    st.dataframe(
        tabla[list(COLUMNAS)],
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "RIESGO", format="%.0f", min_value=0, max_value=100,
                help="Puntuacion WoE derivada de la tabla de predictores. No es un modelo "
                     "entrenado: es la suma de los pesos de cada segmento.",
            ),
            "transaction_id": st.column_config.NumberColumn("ID", format="%d"),
            "amount": st.column_config.NumberColumn("MONTO", format="$%.2f"),
            "transaction_hour": st.column_config.NumberColumn("HORA", format="%d:00"),
            "merchant_category": st.column_config.TextColumn("COMERCIO"),
            "foreign_transaction": st.column_config.CheckboxColumn("EXTRANJERA"),
            "location_mismatch": st.column_config.CheckboxColumn("UBIC. DISCREPA"),
            "device_trust_score": st.column_config.ProgressColumn(
                "CONFIANZA DISP.", format="%d", min_value=0, max_value=100
            ),
            "velocity_last_24h": st.column_config.NumberColumn("VELOCIDAD 24H", format="%d"),
            "cardholder_age": st.column_config.NumberColumn("EDAD", format="%d"),
            "is_fraud": st.column_config.CheckboxColumn("FRAUDE"),
        },
        hide_index=True,
        width="stretch",
        height=520,
    )

    st.markdown(
        th.nota(
            "El orden del selector se aplica sobre <b>toda</b> la seleccion filtrada antes de "
            "recortar a las filas mostradas; pulsar una cabecera reordena solo lo que ya esta "
            "en pantalla."
        ),
        unsafe_allow_html=True,
    )

    st.download_button(
        "DESCARGAR SELECCION (CSV)",
        data=F.assign(risk_score=fs.risk_score(F, CARD).round(1)).to_csv(index=False).encode("utf-8"),
        file_name="fraude_seleccion.csv",
        mime="text/csv",
    )
