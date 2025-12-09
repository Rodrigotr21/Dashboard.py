import streamlit as st
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import os

# Configurar página
st.set_page_config(
    page_title="Dashboard People Analytics - ROSTADINA EIRL",
    page_icon="📊",
    layout="wide"
)

# -------------------------------
# 1. Cargar datos desde CSV
# -------------------------------
st.title("📊 Dashboard People Analytics - ROSTADINA EIRL")

# Cargar datos
try:
    ACTIVOS_FEB_24 = pd.read_csv("activos_feb_24.csv")
    st.sidebar.success(f"✅ Datos cargados correctamente")
    st.sidebar.info(f"📊 Total de registros: {len(ACTIVOS_FEB_24)}")
    
except FileNotFoundError:
    st.error("❌ Archivo 'activos_feb_24.csv' no encontrado")
    st.stop()
except Exception as e:
    st.error(f"❌ Error al cargar el archivo: {str(e)}")
    st.stop()

# Mostrar vista previa de los datos
with st.expander("🔍 Ver estructura de datos completos", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Primeras 10 filas:**")
        # Crear copia para mostrar sin columna sensible
        df_mostrar = ACTIVOS_FEB_24.copy()
        # Definir posibles nombres de columna sensible
        columnas_sensibles = [
            'DOCUMENTO IDENTIDAD / CEDULA / RUT',
            'DOCUMENTO IDENTIDAD',
            'CEDULA',
            'RUT',
            'DNI',
            'IDENTIFICACION'
        ]
        # Eliminar columna sensible si existe
        for col in columnas_sensibles:
            if col in df_mostrar.columns:
                df_mostrar = df_mostrar.drop(columns=[col])
                st.info(f"⚠️ Columna sensible '{col}' oculta por seguridad")
                break
        
        st.dataframe(df_mostrar.head(10))
    with col2:
        st.write("**Información del dataset:**")
        st.write(f"- Total registros: {len(ACTIVOS_FEB_24)}")
        st.write(f"- Total columnas: {len(ACTIVOS_FEB_24.columns)}")
        st.write("**Columnas disponibles:**")
        for col in ACTIVOS_FEB_24.columns:
            # Marcar columna sensible
            es_sensible = any(sensible.lower() in col.lower() for sensible in ['documento', 'cedula', 'rut', 'dni', 'identidad'])
            if es_sensible:
                st.write(f"- ❌ {col} **(OCULTO POR SEGURIDAD)**")
            else:
                st.write(f"- {col}")

# -------------------------------
# 2. Procesamiento de datos
# -------------------------------
# Hacer una copia para no modificar el original
df_processed = ACTIVOS_FEB_24.copy()

# Eliminar columna sensible del dataframe procesado
columnas_sensibles = [
    'DOCUMENTO IDENTIDAD / CEDULA / RUT',
    'DOCUMENTO IDENTIDAD',
    'CEDULA',
    'RUT',
    'DNI',
    'IDENTIFICACION'
]

for col in columnas_sensibles:
    if col in df_processed.columns:
        df_processed = df_processed.drop(columns=[col])
        st.sidebar.warning(f"🔒 Columna '{col}' eliminada por seguridad")

# Lista para almacenar columnas procesadas
columnas_procesadas = []

# FUNCIÓN MEJORADA: Procesar fechas de manera flexible
def procesar_fecha_flexible(df, posibles_nombres, nombre_salida):
    """Intenta procesar fechas con diferentes nombres posibles"""
    for nombre_col in posibles_nombres:
        if nombre_col in df.columns:
            try:
                # Intentar diferentes formatos
                df[nombre_salida] = pd.to_datetime(
                    df[nombre_col], 
                    dayfirst=True,  # Importante para formato latino
                    errors='coerce'
                )
                
                # Verificar si se convirtieron algunas fechas
                if df[nombre_salida].notna().any():
                    columnas_procesadas.append((nombre_col, nombre_salida))
                    return True
            except:
                continue
    return False

# Procesar fecha de nacimiento (probando diferentes nombres posibles)
fecha_nac_posibles = [
    'FECHA DE NACIMIENTO (DD/MM/YYYY)',
    'FECHA_NACIMIENTO',
    'FECHA NACIMIENTO',
    'NACIMIENTO',
    'FECHA_NAC'
]

fecha_nac_procesada = procesar_fecha_flexible(
    df_processed, 
    fecha_nac_posibles, 
    "FECHA_NAC"
)

# Procesar fecha de ingreso (probando diferentes nombres posibles)
fecha_ing_posibles = [
    'FECHA DE INGRESO (DD/MM/YYYY)',
    'FECHA_INGRESO',
    'FECHA INGRESO',
    'INGRESO',
    'FECHA_ING'
]

fecha_ing_procesada = procesar_fecha_flexible(
    df_processed, 
    fecha_ing_posibles, 
    "FECHA_INGRESO"
)

# Mostrar qué columnas se procesaron
if columnas_procesadas:
    st.sidebar.info("📅 Columnas de fecha procesadas:")
    for orig, nueva in columnas_procesadas:
        st.sidebar.write(f"  • {orig} → {nueva}")

# Calcular edad si tenemos fecha de nacimiento
if fecha_nac_procesada:
    try:
        hoy = date.today()
        df_processed["EDAD"] = df_processed["FECHA_NAC"].apply(
            lambda x: hoy.year - x.year - ((hoy.month, hoy.day) < (x.month, x.day)) 
            if pd.notnull(x) else None
        )
        df_processed["EDAD"] = pd.to_numeric(df_processed["EDAD"], errors="coerce")
        
        # Clasificación por grupos etarios (solo si hay edades válidas)
        if df_processed["EDAD"].notna().any():
            df_processed["RANGO_EDAD"] = pd.cut(
                df_processed["EDAD"],
                bins=[18, 25, 35, 45, 55, 65, 100],
                labels=["18-25", "26-35", "36-45", "46-55", "56-65", "65+"],
                right=True,
                include_lowest=True
            )
            st.sidebar.success("✅ Edad y rangos calculados")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error calculando edad: {str(e)}")

# Procesar año y mes de ingreso
if fecha_ing_procesada:
    try:
        df_processed["AÑO_INGRESO"] = df_processed["FECHA_INGRESO"].dt.year
        df_processed["MES_NUM"] = df_processed["FECHA_INGRESO"].dt.month
        meses_es = {
            1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
            7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
        }
        df_processed["MES_INGRESO"] = df_processed["MES_NUM"].map(meses_es)
        st.sidebar.success("✅ Fechas de ingreso procesadas")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error procesando fechas de ingreso: {str(e)}")

# -------------------------------
# 3. CONFIGURAR FILTROS (VERSIÓN SIMPLIFICADA)
# -------------------------------
st.sidebar.header("🎛️ Filtros")

# NOTA IMPORTANTE: Usaremos df_processed directamente
df_filtrado = df_processed.copy()

# FUNCIÓN MEJORADA PARA CREAR FILTROS
def crear_filtro_seguro(columna_nombre, label, df, default_all=True):
    """Crea un filtro que no elimina datos si está vacío"""
    if columna_nombre in df.columns:
        # Obtener valores únicos y limpiar
        valores = df[columna_nombre].dropna().unique()
        valores = [v for v in valores if str(v).strip() != '']
        
        if len(valores) > 0:
            # Convertir a string y ordenar
            opciones = sorted([str(v).strip() for v in valores], key=lambda x: str(x))
            
            if default_all:
                seleccion = st.sidebar.multiselect(
                    f"{label} ({len(opciones)} opciones)",
                    options=opciones,
                    default=opciones  # Por defecto selecciona TODOS
                )
            else:
                seleccion = st.sidebar.multiselect(
                    f"{label} ({len(opciones)} opciones)",
                    options=opciones,
                    default=[]
                )
            
            return seleccion if seleccion else opciones  # Si no hay selección, devolver todos
    return []

# Diccionario para mapear nombres amigables
nombres_amigables = {
    "UNIDAD DE NEGOCIO": "Unidad de Negocio",
    "GENERO (F/M)": "Género",
    "POSICION / PUESTO / CARGO": "Puesto",
    "pais": "País",
    "RANGO_EDAD": "Rango de Edad",
    "AÑO_INGRESO": "Año de Ingreso",
    "MES_INGRESO": "Mes de Ingreso",
    "EDAD": "Edad"
}

# Crear filtros para las columnas comunes
filtros_aplicados = {}

# Columnas para filtros (priorizar las más importantes)
columnas_para_filtros = [
    "UNIDAD DE NEGOCIO",
    "GENERO (F/M)",
    "POSICION / PUESTO / CARGO",
    "pais",
    "RANGO_EDAD",
    "AÑO_INGRESO",
    "MES_INGRESO"
]

for columna in columnas_para_filtros:
    label = nombres_amigables.get(columna, columna)
    valores_filtro = crear_filtro_seguro(columna, label, df_processed)
    if valores_filtro:
        filtros_aplicados[columna] = valores_filtro

# -------------------------------
# 4. APLICAR FILTROS (VERSIÓN CORREGIDA)
# -------------------------------
st.sidebar.header("📊 Estadísticas")

# Mostrar estadísticas ANTES de filtrar
st.sidebar.write(f"**Total registros:** {len(df_processed)}")

# Aplicar filtros de manera INCREMENTAL
df_temp = df_processed.copy()

for columna, valores in filtros_aplicados.items():
    if columna in df_temp.columns and valores:
        try:
            # Convertir a string para comparación
            mask = df_temp[columna].astype(str).str.strip().isin([str(v).strip() for v in valores])
            registros_antes = len(df_temp)
            df_temp = df_temp[mask]
            registros_despues = len(df_temp)
            
            if registros_despues < registros_antes:
                st.sidebar.info(f"Filtro '{nombres_amigables.get(columna, columna)}': {registros_despues} registros")
        except Exception as e:
            st.sidebar.warning(f"Error en filtro {columna}: {str(e)}")

# Asignar el resultado filtrado
df_filtrado = df_temp

# Mostrar estadísticas DESPUÉS de filtrar
st.sidebar.write(f"**Registros filtrados:** {len(df_filtrado)}")

if len(df_filtrado) == 0:
    st.sidebar.error("⚠️ ¡Cuidado! Los filtros eliminaron todos los registros")
    st.sidebar.info("💡 Sugerencia: Selecciona menos opciones en los filtros")
elif len(df_filtrado) < len(df_processed):
    st.sidebar.success(f"✅ Filtrado aplicado: {len(df_filtrado)} de {len(df_processed)} registros")
else:
    st.sidebar.info("ℹ️ Mostrando todos los registros disponibles")

# -------------------------------
# 5. MOSTRAR GRÁFICOS (VERSIÓN ROBUSTA)
# -------------------------------
st.header("📈 Visualizaciones de Datos - ROSTADINA EIRL")

# Verificar si hay datos filtrados
if df_filtrado.empty:
    st.warning("""
    ⚠️ **No hay datos visibles después de aplicar los filtros.**
    
    **Sugerencias:**
    1. **Selecciona más opciones** en los filtros del sidebar
    2. **Verifica los datos originales** en la sección 'Ver estructura de datos'
    3. **Prueba con un solo filtro** a la vez
    4. **Asegúrate** de que los datos tengan valores en las columnas filtradas
    
    **Datos disponibles por columna:**
    """)
    
    # Mostrar qué columnas tienen datos
    columnas_con_datos = []
    for col in df_processed.columns:
        no_nulos = df_processed[col].notna().sum()
        if no_nulos > 0:
            columnas_con_datos.append((col, no_nulos))
    
    for col, count in sorted(columnas_con_datos, key=lambda x: x[1], reverse=True)[:10]:
        st.write(f"- **{col}**: {count} registros con datos")
    
    # Mostrar algunos valores de ejemplo para columnas importantes
    columnas_importantes = ["UNIDAD DE NEGOCIO", "GENERO (F/M)", "pais", "POSICION / PUESTO / CARGO"]
    st.write("\n**Valores de ejemplo en columnas importantes:**")
    
    for col in columnas_importantes:
        if col in df_processed.columns:
            valores = df_processed[col].dropna().unique()[:5]
            if len(valores) > 0:
                st.write(f"- **{col}**: {', '.join([str(v) for v in valores])}")
    
    # Mostrar datos sin filtros como fallback
    st.info("📋 **Mostrando datos sin filtros para referencia:**")
    st.dataframe(df_processed.head(20))
    
    # Usar datos sin filtrar para gráficos
    df_para_graficos = df_processed
    st.warning("⚠️ Mostrando gráficos con datos SIN FILTRAR")
    
else:
    # Usar datos filtrados para gráficos
    df_para_graficos = df_filtrado
    st.success(f"✅ Mostrando gráficos con {len(df_filtrado)} registros filtrados")

# -------------------------------
# 6. CREAR GRÁFICOS (SIEMPRE)
# -------------------------------
# Crear gráficos incluso si hay pocos datos

# FUNCIÓN MEJORADA PARA CREAR GRÁFICOS
def crear_grafico_seguro(df, columna, titulo, tipo='bar', top_n=10):
    """Crea un gráfico seguro incluso con pocos datos"""
    if columna in df.columns:
        try:
            # Limpiar datos
            datos_limpios = df[columna].dropna()
            if datos_limpios.empty:
                return None
            
            # Contar valores
            conteo = datos_limpios.value_counts().head(top_n)
            if conteo.empty:
                return None
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if tipo == 'bar':
                colors = plt.cm.Set3(range(len(conteo)))
                bars = ax.bar(conteo.index.astype(str), conteo.values, color=colors)
                ax.set_ylabel('Cantidad')
                
                # Agregar valores en barras
                for bar, valor in zip(bars, conteo.values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + 0.5,
                           str(valor), ha='center', va='bottom')
                
                plt.xticks(rotation=45, ha='right')
                
            elif tipo == 'barh':
                colors = plt.cm.Set2(range(len(conteo)))
                bars = ax.barh(range(len(conteo)), conteo.values, color=colors)
                ax.set_yticks(range(len(conteo)))
                ax.set_yticklabels(conteo.index.astype(str))
                ax.set_xlabel('Cantidad')
                
                # Agregar valores en barras
                for i, valor in enumerate(conteo.values):
                    ax.text(valor + 0.5, i, str(valor), va='center')
            
            elif tipo == 'pie':
                colors = plt.cm.Pastel1(range(len(conteo)))
                wedges, texts, autotexts = ax.pie(conteo.values, 
                                                 labels=conteo.index.astype(str),
                                                 colors=colors,
                                                 autopct='%1.1f%%',
                                                 startangle=90)
                ax.axis('equal')
            
            ax.set_title(f"{titulo} (Total: {len(datos_limpios)})")
            plt.tight_layout()
            
            return fig
        
        except Exception as e:
            st.warning(f"No se pudo crear gráfico para '{columna}': {str(e)}")
            return None
    return None

# Organizar gráficos en pestañas
tab1, tab2, tab3 = st.tabs(["👥 Demografía", "🏢 Organización", "📅 Temporal"])

with tab1:
    st.subheader("Análisis Demográfico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de género
        fig_genero = crear_grafico_seguro(
            df_para_graficos, 
            "GENERO (F/M)", 
            "Distribución por Género",
            tipo='pie'
        )
        if fig_genero:
            st.pyplot(fig_genero)
        else:
            st.info("No hay datos de género disponibles")
    
    with col2:
        # Gráfico de rango de edad
        if "RANGO_EDAD" in df_para_graficos.columns:
            fig_edad = crear_grafico_seguro(
                df_para_graficos,
                "RANGO_EDAD",
                "Distribución por Rango de Edad",
                tipo='bar'
            )
            if fig_edad:
                st.pyplot(fig_edad)
            else:
                st.info("No hay datos de rango de edad")
        else:
            st.info("No se pudo calcular el rango de edad")

with tab2:
    st.subheader("Análisis Organizacional")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de unidades de negocio
        fig_unidad = crear_grafico_seguro(
            df_para_graficos,
            "UNIDAD DE NEGOCIO",
            "Distribución por Unidad de Negocio",
            tipo='bar',
            top_n=15
        )
        if fig_unidad:
            st.pyplot(fig_unidad)
        else:
            st.info("No hay datos de unidades de negocio")
    
    with col2:
        # Gráfico de puestos
        fig_puestos = crear_grafico_seguro(
            df_para_graficos,
            "POSICION / PUESTO / CARGO",
            "Top 10 Puestos",
            tipo='barh',
            top_n=10
        )
        if fig_puestos:
            st.pyplot(fig_puestos)
        else:
            st.info("No hay datos de puestos")

with tab3:
    st.subheader("Análisis Temporal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de año de ingreso
        if "AÑO_INGRESO" in df_para_graficos.columns:
            fig_anio = crear_grafico_seguro(
                df_para_graficos,
                "AÑO_INGRESO",
                "Ingresos por Año",
                tipo='bar'
            )
            if fig_anio:
                st.pyplot(fig_anio)
            else:
                st.info("No hay datos de año de ingreso")
    
    with col2:
        # Gráfico de mes de ingreso
        if "MES_INGRESO" in df_para_graficos.columns:
            fig_mes = crear_grafico_seguro(
                df_para_graficos,
                "MES_INGRESO",
                "Ingresos por Mes",
                tipo='bar'
            )
            if fig_mes:
                st.pyplot(fig_mes)
            else:
                st.info("No hay datos de mes de ingreso")
    
    # Gráfico de cumpleaños por mes
    st.subheader("🎂 Cumpleaños por Mes")
    if "FECHA_NAC" in df_para_graficos.columns:
        try:
            cumple_mes = df_para_graficos["FECHA_NAC"].dt.month.value_counts().sort_index()
            if not cumple_mes.empty:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                meses_es = {
                    1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
                    7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
                }
                
                meses_nombres = [meses_es.get(m, f"Mes {m}") for m in cumple_mes.index]
                colores = plt.cm.Pastel2(range(len(cumple_mes)))
                
                bars = ax.bar(meses_nombres, cumple_mes.values, color=colores)
                ax.set_title(f"Cumpleaños por Mes (Total: {len(df_para_graficos['FECHA_NAC'].dropna())})")
                ax.set_xlabel('Mes')
                ax.set_ylabel('Cantidad de Cumpleaños')
                plt.xticks(rotation=45, ha='right')
                
                # Agregar valores
                for bar, valor in zip(bars, cumple_mes.values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, height + 0.5,
                           str(valor), ha='center', va='bottom')
                
                st.pyplot(fig)
        except:
            st.info("No se pudieron procesar las fechas de cumpleaños")

# -------------------------------
# 7. MOSTRAR DATOS FILTRADOS (VERSIÓN SEGURA)
# -------------------------------
with st.expander("📋 Ver datos procesados", expanded=False):
    st.write(f"**Total de registros mostrados:** {len(df_para_graficos)}")
    
    # Selector para ver diferentes vistas
    vista = st.radio(
        "Seleccionar vista:",
        ["Vista general", "Ver todas las columnas", "Estadísticas básicas"],
        horizontal=True
    )
    
    if vista == "Vista general":
        # Mostrar columnas principales (excluyendo sensibles)
        columnas_principales = []
        columnas_excluir = [
            'DOCUMENTO IDENTIDAD / CEDULA / RUT',
            'DOCUMENTO IDENTIDAD',
            'CEDULA',
            'RUT',
            'DNI',
            'IDENTIFICACION'
        ]
        
        for col in ["UNIDAD DE NEGOCIO", "GENERO (F/M)", "POSICION / PUESTO / CARGO", 
                   "pais", "EDAD", "RANGO_EDAD", "AÑO_INGRESO"]:
            if col in df_para_graficos.columns and col not in columnas_excluir:
                columnas_principales.append(col)
        
        if columnas_principales:
            st.dataframe(df_para_graficos[columnas_principales].head(50))
        else:
            st.dataframe(df_para_graficos.head(50))
    
    elif vista == "Ver todas las columnas":
        # Crear copia para mostrar sin columna sensible
        df_mostrar_todas = df_para_graficos.copy()
        
        # Lista de posibles nombres de columnas sensibles
        columnas_sensibles = [
            'DOCUMENTO IDENTIDAD / CEDULA / RUT',
            'DOCUMENTO IDENTIDAD',
            'CEDULA',
            'RUT',
            'DNI',
            'IDENTIFICACION',
            'DOCUMENTO',
            'IDENTIDAD'
        ]
        
        # Verificar si hay alguna columna sensible
        columnas_encontradas = []
        for col_sensible in columnas_sensibles:
            for col_df in df_mostrar_todas.columns:
                if col_sensible.lower() in str(col_df).lower():
                    columnas_encontradas.append(col_df)
        
        # Eliminar columnas sensibles
        if columnas_encontradas:
            df_mostrar_todas = df_mostrar_todas.drop(columns=columnas_encontradas)
            st.warning(f"🔒 **PROTECCIÓN DE DATOS:** Se han ocultado {len(columnas_encontradas)} columnas sensibles")
            for col in columnas_encontradas:
                st.info(f"⚠️ Columna '{col}' oculta por seguridad")
        
        st.dataframe(df_mostrar_todas.head(30))
    
    else:  # Estadísticas básicas
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Conteos por categoría:**")
            columnas_estadisticas = ["UNIDAD DE NEGOCIO", "GENERO (F/M)", "pais"]
            for columna in columnas_estadisticas:
                if columna in df_para_graficos.columns:
                    conteo = df_para_graficos[columna].value_counts().head(10)
                    st.write(f"**{columna}:**")
                    for valor, cantidad in conteo.items():
                        st.write(f"  {valor}: {cantidad}")
        
        with col2:
            st.write("**Estadísticas numéricas:**")
            if "EDAD" in df_para_graficos.columns:
                st.write(f"**Edad (datos anonimizados):**")
                st.write(f"  Mínima: {df_para_graficos['EDAD'].min():.0f}")
                st.write(f"  Máxima: {df_para_graficos['EDAD'].max():.0f}")
                st.write(f"  Promedio: {df_para_graficos['EDAD'].mean():.1f}")
                st.write(f"  Mediana: {df_para_graficos['EDAD'].median():.1f}")
    
    # Botón para descargar (sin datos sensibles)
    st.markdown("---")
    st.write("**📥 Descargar datos (sin información sensible):**")
    
    # Crear dataframe seguro para descarga
    df_descargar = df_para_graficos.copy()
    
    # Eliminar columnas sensibles antes de descargar
    columnas_sensibles_descarga = [
        'DOCUMENTO IDENTIDAD / CEDULA / RUT',
        'DOCUMENTO IDENTIDAD',
        'CEDULA',
        'RUT',
        'DNI',
        'IDENTIFICACION'
    ]
    
    columnas_eliminadas = []
    for col in columnas_sensibles_descarga:
        for col_df in df_descargar.columns:
            if col.lower() in str(col_df).lower():
                df_descargar = df_descargar.drop(columns=[col_df])
                columnas_eliminadas.append(col_df)
    
    if columnas_eliminadas:
        st.info(f"✅ Para descarga: Se han eliminado {len(columnas_eliminadas)} columnas sensibles")
    
    csv = df_descargar.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos como CSV (seguro)",
        data=csv,
        file_name="datos_rostadina_seguro.csv",
        mime="text/csv",
        help="Archivo CSV sin información sensible como documentos de identidad"
    )

# -------------------------------
# 8. PIE DE PÁGINA
# -------------------------------
st.markdown("---")
st.markdown("### 📊 Dashboard People Analytics")
st.markdown("**ROSTADINA EIRL** - Reporte de Recursos Humanos")
st.markdown("*Datos actualizados: Febrero 2024*")
st.caption("""
🔒 **Protección de datos activada:** La información sensible como documentos de identidad ha sido ocultada para proteger la privacidad.
""")
st.caption("Desarrollado con Streamlit | © 2025 ROSTADINA EIRL. Todos los derechos reservados.")