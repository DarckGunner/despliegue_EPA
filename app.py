# app.py
# Dashboard unificado (una sola página) adaptado a datSetFinalll.csv

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -------------------------
# Normalización de columnas (robusta)
# -------------------------
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:

    df = df.rename(columns={c: c.strip() for c in df.columns})

    mapping = {}
    if "Codigo" in df.columns:
        mapping["Codigo"] = "Codigo"
    elif "Codigo " in df.columns:
        mapping["Codigo "] = "Codigo"

    if "Descripcion" in df.columns:
        mapping["Descripcion"] = "Descripción"

    if "Fecha reporte" in df.columns:
        mapping["Fecha reporte"] = "FechaReporte"
    elif "FechaReporte" in df.columns:
        mapping["FechaReporte"] = "FechaReporte"

    if "AccionesPlanteadas" in df.columns:
        mapping["AccionesPlanteadas"] = "AccionesPlanteadas"

    df = df.rename(columns=mapping)

    # Crear faltantes
    if "Proceso" not in df.columns:
        if "Codigo" in df.columns:
            df["Proceso"] = df["Codigo"].astype(str).str.strip()
        else:
            df["Proceso"] = ""

    if "Fuente" not in df.columns:
        df["Fuente"] = ""

    if "Descripción" not in df.columns:
        df["Descripción"] = ""

    if "AccionesPlanteadas" not in df.columns:
        df["AccionesPlanteadas"] = ""

    df["Proceso"] = df["Proceso"].astype(str).str.strip()
    df["Fuente"] = df["Fuente"].astype(str).str.strip()
    df["Descripción"] = df["Descripción"].astype(str).str.strip()

    def extract_year(x):
        if pd.isna(x):
            return np.nan
        try:
            return pd.to_datetime(x, errors="coerce").year
        except:
            return np.nan

    if "FechaReporte" in df.columns:
        df["Año"] = df["FechaReporte"].apply(extract_year)
    else:
        fecha_cols = [c for c in df.columns if "fecha" in c.lower()]
        año_series = pd.Series([np.nan] * len(df))
        for c in fecha_cols:
            año_series = año_series.fillna(df[c].apply(extract_year))
        df["Año"] = año_series

    df = df.dropna(subset=["Año"], how="all").reset_index(drop=True)
    return df


# -------------------------
# Visualizaciones
# -------------------------
def fig_donut(df):
    if df.empty or df["Fuente"].dropna().empty:
        return px.pie(title="Sin datos")

    counts = df["Fuente"].value_counts().reset_index()
    counts.columns = ["Fuente", "Count"]
    fig = px.pie(counts, names="Fuente", values="Count", hole=0.45,
                 title="Distribución de hallazgos por fuente")
    fig.update_traces(textinfo="percent+label")
    return fig

def fig_line_year(df):
    if df.empty or df["Año"].dropna().empty:
        return px.line(title="Sin datos")

    counts = df.groupby("Año").size().reset_index(name="Count")
    return px.line(counts, x="Año", y="Count", markers=True,
                   title="Hallazgos por año")

def fig_bar_process(df):
    if df.empty or df["Proceso"].dropna().empty:
        return px.bar(title="Sin datos")

    counts = df["Proceso"].value_counts().reset_index()
    counts.columns = ["Proceso", "Count"]
    counts = counts.sort_values("Count", ascending=True)

    return px.bar(counts, x="Count", y="Proceso", orientation="h",
                  title="Hallazgos por proceso")

def fig_lines_source(df):
    if df.empty or df["Fuente"].dropna().empty or df["Año"].dropna().empty:
        return px.line(title="Sin datos")

    grouped = df.groupby(["Año", "Fuente"]).size().reset_index(name="Count")
    return px.line(grouped, x="Año", y="Count", color="Fuente",
                   markers=True, title="Evolución de hallazgos por fuente")


# -------------------------
# Streamlit App (UNA SOLA PÁGINA)
# -------------------------
st.set_page_config(page_title="Dashboard EPA.ESP", layout="wide")

st.title("Dashboard de Hallazgos - EPA.ESP")
st.write("Cargue un archivo CSV o Excel con el dataset de hallazgos.")

uploaded = st.file_uploader("Cargar archivo", type=["csv", "xlsx"])

if uploaded is None:
    st.info("Sube un archivo para comenzar.")
    st.stop()

try:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Error leyendo el archivo ({e})")
    st.stop()

df = standardize_columns(df)

# -------------------------
# FILTROS
# -------------------------
st.sidebar.title("Filtros")

years = sorted([int(y) for y in df["Año"].dropna().unique().tolist()])
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

# -------------------------
# KPIs
# -------------------------
st.subheader("Indicadores principales")
col1, col2, col3, col4 = st.columns(4)

if fdf.empty:
    col1.metric("Hallazgos totales", 0)
    col2.metric("Fuente mayoritaria", "Sin datos")
    col3.metric("Año con más hallazgos", "Sin datos")
    col4.metric("Proceso con más hallazgos", "Sin datos")
else:
    # Total de hallazgos
    col1.metric("Hallazgos totales", len(fdf))

    # Fuente mayoritaria
    vc_fuente = fdf["Fuente"].value_counts()
    col2.metric("Fuente mayoritaria", vc_fuente.idxmax() if not vc_fuente.empty else "Sin datos")

    # Año con más hallazgos
    vc_year = fdf["Año"].value_counts()
    col3.metric("Año con más hallazgos",
                int(vc_year.idxmax()) if not vc_year.empty else "Sin datos")

    # 🔥 Proceso con más hallazgos (NUEVO KPI)
    vc_proc = fdf["Proceso"].value_counts()
    col4.metric("Proceso con más hallazgos",
                vc_proc.idxmax() if not vc_proc.empty else "Sin datos")

# -------------------------
# TODOS LOS GRÁFICOS EN UNA SOLA PÁGINA
# -------------------------
st.subheader("Gráficos")

# Primera fila: Donut + Línea por año
c1, c2 = st.columns([1, 2])
c1.plotly_chart(fig_donut(fdf), use_container_width=True)
c2.plotly_chart(fig_line_year(fdf), use_container_width=True)

# Segunda fila: Barras horizontales por proceso
st.plotly_chart(fig_bar_process(fdf), use_container_width=True)

# Tercera fila: línea comparativa por fuente
st.plotly_chart(fig_lines_source(fdf), use_container_width=True)

# -------------------------
# DESCRIPCIÓN AUTOMÁTICA DEL DASHBOARD
# -------------------------
st.subheader("Descripción automática del análisis")

if fdf.empty:
    st.write("No hay datos para generar una descripción automática. Ajusta los filtros.")
else:
    # --- análisis automático ---
    total = len(fdf)

    # Fuente principal
    vc_fuente = fdf["Fuente"].value_counts()
    fuente_principal = vc_fuente.idxmax() if not vc_fuente.empty else "Sin datos"
    cant_fuente_principal = vc_fuente.max() if not vc_fuente.empty else 0

    # Proceso principal
    vc_proc = fdf["Proceso"].value_counts()
    proceso_principal = vc_proc.idxmax() if not vc_proc.empty else "Sin datos"
    cant_proc_principal = vc_proc.max() if not vc_proc.empty else 0

    # Año con más casos
    vc_years = fdf["Año"].value_counts()
    año_principal = int(vc_years.idxmax()) if not vc_years.empty else "Sin datos"
    cant_año_principal = vc_years.max() if not vc_years.empty else 0

    # Construcción del texto
    descripcion = f"""
El conjunto de datos filtrado contiene **{total} hallazgos**.  
La **fuente más frecuente** es **{fuente_principal}**, con **{cant_fuente_principal} registros**, lo que indica que este origen representa una proporción significativa del total analizado.

En cuanto a los procesos, el **proceso con mayor número de hallazgos** es **{proceso_principal}**, alcanzando **{cant_proc_principal} casos**, lo que sugiere una posible concentración de oportunidades de mejora en esa área.

Respecto a la evolución temporal, el **año con más hallazgos** es **{año_principal}**, con **{cant_año_principal} registros**, lo que puede evidenciar un período de mayor actividad, auditoría o incremento en los reportes.

En conjunto, estos indicadores permiten identificar patrones relevantes en las fuentes de hallazgos, los procesos involucrados y su comportamiento a lo largo del tiempo, facilitando la toma de decisiones y priorización de acciones correctivas.
"""

    st.write(descripcion)

