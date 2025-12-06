import streamlit as st
import pandas as pd
import plotly.express as px

# ============================
#   CONFIGURACIÓN INICIAL
# ============================
st.set_page_config(
    page_title="Dashboard de Hallazgos",
    layout="wide"
)

st.title("Dashboard de Hallazgos Institucionales")
st.write(
    "Este dashboard permite explorar de forma dinámica el comportamiento de los hallazgos de auditoría, "
    "incluyendo su distribución por proceso, su evolución en el tiempo, y los patrones más relevantes "
    "que emergen del análisis descriptivo."
)

# ============================
#   CARGA DEL ARCHIVO
# ============================
st.sidebar.header("Carga del archivo")
uploaded_file = st.sidebar.file_uploader("Subir archivo CSV", type=["csv"])

if uploaded_file is None:
    st.warning("Por favor sube un archivo CSV para iniciar.")
    st.stop()

df = pd.read_csv(uploaded_file)

# ============================
#   NORMALIZACIÓN DE COLUMNAS
# ============================
def standardize_columns(df):
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    for col in df.columns:
        try:
            df[col] = df[col].astype(str).str.strip()
        except:
            pass
    return df

df = standardize_columns(df)

# Validación básica
required_cols = ["Proceso", "Hallazgo", "Fecha", "Accion_del_Hallazgo"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Falta la columna requerida: **{col}**")
        st.stop()

df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Año"] = df["Fecha"].dt.year

# ============================
#   FILTROS
# ============================
st.sidebar.header("Filtros")

years = sorted(df["Año"].dropna().unique())
procesos = sorted(df["Proceso"].unique())
acciones = sorted(df["Accion_del_Hallazgo"].unique())

year_filter = st.sidebar.multiselect("Año", years)
proceso_filter = st.sidebar.multiselect("Proceso", procesos)
accion_filter = st.sidebar.multiselect("Acción del hallazgo", acciones)

if st.sidebar.button("Limpiar filtros"):
    year_filter = []
    proceso_filter = []
    accion_filter = []

filtered_df = df.copy()

if year_filter:
    filtered_df = filtered_df[filtered_df["Año"].isin(year_filter)]

if proceso_filter:
    filtered_df = filtered_df[filtered_df["Proceso"].isin(proceso_filter)]

if accion_filter:
    filtered_df = filtered_df[filtered_df["Accion_del_Hallazgo"].isin(accion_filter)]

# ============================
#   MÉTRICAS PRINCIPALES
# ============================
st.header("Indicadores Generales")

col1, col2, col3 = st.columns(3)

col1.metric("Total de Hallazgos", len(filtered_df))
col2.metric("Procesos Involucrados", filtered_df["Proceso"].nunique())
col3.metric("Años Analizados", filtered_df["Año"].nunique())

# ============================
#   HALLAZGOS PRINCIPALES
# ============================
st.header("Hallazgos Principales")

st.subheader("Hallazgos más frecuentes")
hall_freq = filtered_df["Hallazgo"].value_counts().nlargest(10)
st.write(hall_freq)

# ---- PROCESO CON MÁS HALLAZGOS ----
st.subheader("Proceso con más hallazgos")

proc_count = (
    filtered_df["Proceso"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "Proceso", "Proceso": "Cantidad"})
)

if not proc_count.empty:
    proceso_top = proc_count.iloc[0]
    st.markdown(
        f"""
        **Proceso con mayor cantidad de hallazgos:**  
        - **{proceso_top['Proceso']}** con **{proceso_top['Cantidad']} hallazgos**.
        """
    )
    st.dataframe(proc_count)

# ============================
#   GRÁFICO: HALLAZGOS POR PROCESO
# ============================
st.header("Distribución de Hallazgos por Proceso")

if not proc_count.empty:
    fig_proc = px.bar(
        proc_count,
        x="Cantidad",
        y="Proceso",
        orientation="h",
        title="Cantidad de hallazgos por proceso"
    )
    st.plotly_chart(fig_proc, use_container_width=True)

# ============================
#   GRÁFICO: EVOLUCIÓN TEMPORAL
# ============================
st.header("Evolución Temporal de los Hallazgos")

evol_df = filtered_df.groupby("Año").size().reset_index(name="Cantidad")

if not evol_df.empty:
    fig_evo = px.line(
        evol_df,
        x="Año",
        y="Cantidad",
        markers=True,
        title="Hallazgos por año"
    )
    st.plotly_chart(fig_evo, use_container_width=True)

# ============================
#   DESCRIPCIÓN AUTOMÁTICA
# ============================
st.header("Descripción Automática del Dashboard")

st.write(
    """
    Este dashboard consolida los resultados del análisis descriptivo en una herramienta visual diseñada
    para facilitar la interpretación de los hallazgos institucionales. Cada sección integra componentes clave
    del comportamiento de los datos, permitiendo una navegación clara y un análisis progresivo. La estructura
    reúne todos los gráficos, métricas y tablas en una sola página, lo que simplifica la exploración sin necesidad
    de cambiar de vista o cargar elementos adicionales.

    Los filtros permiten ajustar dinámicamente la información consultada, facilitando estudios específicos por
    año, proceso o tipo de acción. La herramienta se adapta automáticamente a los criterios seleccionados,
    actualizando los indicadores generales, los hallazgos más frecuentes, la identificación del proceso con mayor
    número de observaciones, así como la evolución temporal y la distribución de hallazgos por proceso.

    Gracias a su diseño unificado y a su lógica interactiva, este dashboard respalda la interpretación rigurosa de la
    información y se convierte en un recurso fundamental para la toma de decisiones en auditoría y gestión institucional.
    """
)
