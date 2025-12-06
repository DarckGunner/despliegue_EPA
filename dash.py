# app.py
# Dashboard para análisis de hallazgos en EPA.ESP
# Compatible con tu dataset datSetFinalll.csv

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -------------------------
# Normalización de columnas
# -------------------------
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mapea las columnas reales del dataset a columnas estándar.
    Basado en tu archivo datSetFinalll.csv.
    """

    mapping = {
        "Año": "Año",
        "Fuente": "Fuente",
        "Código": "Proceso",
        "Descripcion": "Descripción",
        "Descripción": "Descripción",
        "AccionesPlanteadas": "AccionesPlanteadas"
    }

    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

    # Columnas obligatorias
    required = ["Año", "Fuente", "Proceso"]
    for col in required:
        if col not in df.columns:
            df[col] = np.nan

    # Columns opcionales
    if "Descripción" not in df.columns:
        df["Descripción"] = ""

    if "AccionesPlanteadas" not in df.columns:
        df["AccionesPlanteadas"] = ""

    # Año a numérico
    def parse_year(x):
        try:
            return int(str(x).strip()[:4])
        except:
            return np.nan

    df["Año"] = df["Año"].apply(parse_year)

    df["Fuente"] = df["Fuente"].astype(str).str.strip()
    df["Proceso"] = df["Proceso"].astype(str).str.strip()

    df = df.dropna(subset=["Año"], how="all")

    return df


# -------------------------
# Visualizaciones
# -------------------------
def fig_donut(df):
    counts = df["Fuente"].value_counts().reset_index()
    counts.columns = ["Fuente", "Count"]
    fig = px.pie(counts, names="Fuente", values="Count", hole=0.45,
                 title="Distribución de hallazgos por fuente")
    fig.update_traces(textinfo="percent+label")
    return fig

def fig_line_year(df):
    counts = df.groupby("Año").size().reset_index(name="Count")
    fig = px.line(counts, x="Año", y="Count", markers=True,
                  title="Hallazgos por año")
    return fig

def fig_bar_process(df):
    counts = df["Proceso"].value_counts().reset_index()
    counts.columns = ["Proceso", "Count"]
    counts = counts.sort_values("Count", ascending=True)
    fig = px.bar(counts, x="Count", y="Proceso",
                 orientation="h",
                 title="Hallazgos por proceso")
    return fig

def fig_lines_source(df):
    tmp = df.copy()
    grouped = tmp.groupby(["Año", "Fuente"]).size().reset_index(name="Count")
    fig = px.line(grouped, x="Año", y="Count", color="Fuente",
                  markers=True,
                  title="Evolución de hallazgos por fuente")
    return fig


# -------------------------
# Streamlit App
# -------------------------
st.set_page_config(page_title="Dashboard EPA.ESP", layout="wide")

st.title("Dashboard de Hallazgos - EPA.ESP")
st.write("Cargue un archivo CSV o Excel con el dataset de hallazgos.")

# Upload
uploaded = st.file_uploader("Cargar archivo", type=["csv", "xlsx"])

if uploaded is None:
    st.info("Sube un archivo para comenzar.")
    st.stop()

try:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
except:
    st.error("Error leyendo el archivo. Revisa el formato.")
    st.stop()

df = standardize_columns(df)

# Sidebar filtros
st.sidebar.title("Filtros")
years = sorted(df["Año"].dropna().unique().tolist())
fuentes = sorted(df["Fuente"].dropna().unique().tolist())
procesos = sorted(df["Proceso"].dropna().unique().tolist())

sel_year = st.sidebar.multiselect("Año", years)
sel_fuente = st.sidebar.multiselect("Fuente", fuentes)
sel_proc = st.sidebar.multiselect("Proceso", procesos)

fdf = df.copy()

if sel_year:
    fdf = fdf[fdf["Año"].isin(sel_year)]
if sel_fuente:
    fdf = fdf[fdf["Fuente"].isin(sel_fuente)]
if sel_proc:
    fdf = fdf[fdf["Proceso"].isin(sel_proc)]

# Navegación
page = st.sidebar.radio("Página", ["Página 1 - General", "Página 2 - Comparativa"])

# KPIs
st.subheader("Indicadores principales")
col1, col2, col3 = st.columns(3)
col1.metric("Hallazgos totales", len(fdf))
if "interna" in [s.lower() for s in df["Fuente"].dropna().unique()]:
    count_interna = len(fdf[fdf["Fuente"].str.lower() == "interna"])
    pct = round(count_interna / len(fdf) * 100 if len(fdf) > 0 else 0, 1)
    col2.metric("Auditoría interna (%)", f"{pct}%")
else:
    col2.metric("Fuente mayoritaria", fdf["Fuente"].value_counts().idxmax())
if not fdf["Año"].dropna().empty:
    col3.metric("Año con más hallazgos", int(fdf["Año"].value_counts().idxmax()))

# Página 1
if page.startswith("Página 1"):
    colA, colB = st.columns([1, 2])
    colA.plotly_chart(fig_donut(fdf), use_container_width=True)
    colB.plotly_chart(fig_line_year(fdf), use_container_width=True)

    st.plotly_chart(fig_bar_process(fdf), use_container_width=True)

    st.download_button(
        "Descargar datos filtrados",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="hallazgos_filtrados.csv"
    )

# Página 2
else:
    st.plotly_chart(fig_lines_source(fdf), use_container_width=True)
    st.write("Vista detallada de registros:")
    st.dataframe(fdf, use_container_width=True)
