import streamlit as st
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# -------------------------------
# 1. Cargar datos desde CSV
# -------------------------------
ACTIVOS_FEB_24 = pd.read_csv("activos_feb_24.csv")

# -------------------------------
# 2. Procesamiento de datos
# -------------------------------
# Convertir fechas
ACTIVOS_FEB_24["FECHA DE NACIMIENTO (DD/MM/YYYY)"] = pd.to_datetime(
    ACTIVOS_FEB_24["FECHA DE NACIMIENTO (DD/MM/YYYY)"], format="%d/%m/%Y", errors="coerce"
)
ACTIVOS_FEB_24["FECHA DE INGRESO (DD/MM/YYYY)"] = pd.to_datetime(
    ACTIVOS_FEB_24["FECHA DE INGRESO (DD/MM/YYYY)"], format="%d/%m/%Y", errors="coerce"
)

# Calcular edad
hoy = date.today()
ACTIVOS_FEB_24["EDAD"] = ACTIVOS_FEB_24["FECHA DE NACIMIENTO (DD/MM/YYYY)"].dt.year.apply(
    lambda x: hoy.year - x if pd.notnull(x) else None
)
ACTIVOS_FEB_24["EDAD"] = pd.to_numeric(ACTIVOS_FEB_24["EDAD"], errors="coerce")

# Crear rango de edad
ACTIVOS_FEB_24["RANGO_EDAD"] = pd.cut(
    ACTIVOS_FEB_24["EDAD"].fillna(-1),
    bins=[18, 25, 35, 45, 55, 65, 100],
    labels=["18-25", "26-35", "36-45", "46-55", "56-65", "65+"],
    right=True
)
ACTIVOS_FEB_24.loc[ACTIVOS_FEB_24["EDAD"].isna(), "RANGO_EDAD"] = pd.NA

# Año y mes de ingreso
ACTIVOS_FEB_24["AÑO"] = ACTIVOS_FEB_24["FECHA DE INGRESO (DD/MM/YYYY)"].dt.year.astype("Int64")
ACTIVOS_FEB_24["MES_NUM"] = ACTIVOS_FEB_24["FECHA DE INGRESO (DD/MM/YYYY)"].dt.month
meses_es = {
    1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
    7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
}
ACTIVOS_FEB_24["MES"] = ACTIVOS_FEB_24["MES_NUM"].map(meses_es)

# -------------------------------
# 3. Dashboard interactivo
# -------------------------------
st.title("📊 Dashboard People Analytics - Febrero 2024")

# --- Filtros interactivos ---
st.sidebar.header("Filtros")
filtro_unidad = st.sidebar.multiselect("Unidad de Negocio", ACTIVOS_FEB_24["UNIDAD DE NEGOCIO"].dropna().unique())
filtro_año = st.sidebar.multiselect("Año de ingreso", sorted(ACTIVOS_FEB_24["AÑO"].dropna().unique()))
filtro_mes = st.sidebar.multiselect("Mes de ingreso", ACTIVOS_FEB_24["MES"].dropna().unique())

# Aplicar filtros
df_filtrado = ACTIVOS_FEB_24.copy()
if filtro_unidad:
    df_filtrado = df_filtrado[df_filtrado["UNIDAD DE NEGOCIO"].isin(filtro_unidad)]
if filtro_año:
    df_filtrado = df_filtrado[df_filtrado["AÑO"].isin(filtro_año)]
if filtro_mes:
    df_filtrado = df_filtrado[df_filtrado["MES"].isin(filtro_mes)]

# -------------------------------
# 4. Gráficos
# -------------------------------

# Distribución por género
st.subheader("Distribución por género")
fig, ax = plt.subplots()
df_filtrado['GENERO (F/M)'].value_counts().plot(kind="bar", ax=ax)
st.pyplot(fig)

# Distribución por Unidad de Negocio
st.subheader("Distribución por Unidad de Negocio")
fig, ax = plt.subplots()
df_filtrado['UNIDAD DE NEGOCIO'].value_counts().plot(kind="bar", ax=ax)
st.pyplot(fig)

# Cumpleaños por mes
st.subheader("Cumpleaños por mes")
cumple_mes = df_filtrado["FECHA DE NACIMIENTO (DD/MM/YYYY)"].dt.month.value_counts().sort_index()
fig, ax = plt.subplots()
sns.barplot(x=[meses_es[m] for m in cumple_mes.index], y=cumple_mes.values, ax=ax)
plt.xticks(rotation=45)
st.pyplot(fig)

# Top 10 puestos
st.subheader("Top 10 puestos con mayor headcount")
top_puestos = df_filtrado["POSICION / PUESTO / CARGO"].value_counts().head(10)
fig, ax = plt.subplots()
sns.barplot(x=top_puestos.values, y=top_puestos.index, ax=ax)
st.pyplot(fig)

# Heatmap de ingresos por unidad de negocio
st.subheader("Estacionalidad de ingresos por Unidad de Negocio")
ingresos_unidad_mes = (
    df_filtrado.groupby(["UNIDAD DE NEGOCIO", "MES"]).size().unstack(fill_value=0)
)
ingresos_unidad_mes = ingresos_unidad_mes.fillna(0).astype(int)
fig, ax = plt.subplots(figsize=(10,6))
sns.heatmap(ingresos_unidad_mes, annot=True, fmt="d", cmap="crest", ax=ax)
st.pyplot(fig)

# Distribución por rango de edad
st.subheader("Distribución por rango de edad")
fig, ax = plt.subplots()
df_filtrado["RANGO_EDAD"].value_counts().sort_index().plot(kind="bar", ax=ax)
st.pyplot(fig)

# Headcount por país
st.subheader("Headcount por país")
fig, ax = plt.subplots()
df_filtrado["pais"].value_counts().plot(kind="barh", ax=ax)
st.pyplot(fig)

# Tendencia de ingresos por año
st.subheader("Tendencia de ingresos por año")
ingresos_año = df_filtrado["AÑO"].value_counts().sort_index()
fig, ax = plt.subplots()
sns.lineplot(x=ingresos_año.index, y=ingresos_año.values, marker="o", ax=ax)
st.pyplot(fig)

# Distribución por género y rango de edad
st.subheader("Distribución por género y rango de edad")
genero_edad = df_filtrado.groupby(["RANGO_EDAD","GENERO (F/M)"]).size().unstack(fill_value=0)
fig, ax = plt.subplots()
genero_edad.plot(kind="bar", stacked=True, ax=ax)
st.pyplot(fig)