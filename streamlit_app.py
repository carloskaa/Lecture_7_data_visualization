import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
import datetime

# --- Configuración de la Página ---
# st.set_page_config() debe ser el primer comando de Streamlit
st.set_page_config(page_title="Dashboard de Rendimiento FV", page_icon="☀️", layout="wide")


# --- Carga y Cacheo de Datos ---
# Usamos @st.cache_data para que los datos se carguen solo una vez
@st.cache_data
def cargar_datos(ruta_csv):
    df = pd.read_csv(ruta_csv)

    # Convertimos 'Timestamp' a datetime.
    # errors='coerce' convertirá las fechas malas (como '2loc 08:45:00') en 'NaT' (Not a Time)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    # ¡Importante! Eliminamos las filas que no se pudieron convertir (las que tienen NaT)
    df = df.dropna(subset=["Timestamp"])

    # Extraemos 'Fecha' para el filtro de fecha
    df["Fecha"] = df["Timestamp"].dt.date
    return df


# Cargamos los datos
df = cargar_datos("datos_pv.csv")

# --- Barra Lateral (Filtros) ---
st.sidebar.header("Filtros del Dashboard ☀️")

# Filtro 1: Selección de Inversor
# Obtenemos la lista única de inversores
lista_inversores = df["Nombre_Inversor"].unique()
# Usamos multiselect para permitir seleccionar uno o ambos
inversores_seleccionados = st.sidebar.multiselect(
    "Selecciona Inversor(es):",
    options=lista_inversores,
    default=lista_inversores,  # Por defecto, mostrar ambos
)

# Filtro 2: Selector de Rango de Fechas
# Obtenemos las fechas min y max para el selector
min_fecha = df["Fecha"].min()
max_fecha = df["Fecha"].max()

# st.date_input permite seleccionar un rango
fechas_seleccionadas = st.sidebar.date_input(
    "Selecciona el rango de fechas:",
    value=(min_fecha, max_fecha),  # Valor por defecto (todo el rango)
    min_value=min_fecha,
    max_value=max_fecha,
    format="YYYY-MM-DD",
)

# Aseguramos que el filtro de fecha funcione (inicio y fin)
try:
    fecha_inicio, fecha_fin = fechas_seleccionadas
except ValueError:
    st.sidebar.error("Selecciona un rango de fechas válido (inicio y fin).")
    st.stop()  # Detiene la ejecución si el rango no es válido

# --- Filtrado del DataFrame ---
# Aplicamos los filtros seleccionados al DataFrame
df_filtrado = df[
    (df["Nombre_Inversor"].isin(inversores_seleccionados))
    & (df["Fecha"] >= fecha_inicio)
    & (df["Fecha"] <= fecha_fin)
]

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# --- Página Principal ---
st.title("Dashboard de Rendimiento Fotovoltaico ☀️")
st.markdown(
    f"Mostrando datos desde **{fecha_inicio.strftime('%Y-%m-%d')}** hasta **{fecha_fin.strftime('%Y-%m-%d')}**"
)

# --- KPIs (Indicadores Clave de Rendimiento) ---
st.header("KPIs de Rendimiento")

# Calculamos los KPIs basados en los datos filtrados
# 1. Energía Total (kWh). La potencia está en kW, los intervalos son de 15 min (0.25h)
energia_total_kwh = df_filtrado["Potencia_AC_kW"].sum() * 0.25  # 0.25h = 15 min
# 2. Potencia Pico (kW)
potencia_pico_kw = df_filtrado["Potencia_AC_kW"].max()
# 3. Irradiancia Máxima
irradiancia_max = df_filtrado["Irradiancia_GHI_W_m2"].max()
# 4. HSP (Horas Solares Pico Equivalentes)
# Es la energía total (kWh) dividida por la potencia pico del sistema (kWp)
# Asumimos una potencia pico de 50 kWp por inversor (lo simulamos así)
potencia_pico_sistema_kwp = 50 * len(inversores_seleccionados)
hsp = energia_total_kwh / potencia_pico_sistema_kwp

# Mostramos los KPIs en columnas
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Energía Total Generada", value=f"{energia_total_kwh:,.0f} kWh")
col2.metric(label="Potencia AC Pico", value=f"{potencia_pico_kw:,.1f} kW")
col3.metric(label="Irradiancia Máxima", value=f"{irradiancia_max:,.0f} W/m²")
col4.metric(label="Horas Solares Pico (HSP)", value=f"{hsp:,.2f} h")

st.markdown("---")

# --- Gráfico Principal: Series de Tiempo (Usando Plotly) ---
st.header("Análisis de Series de Tiempo")

# Creamos una figura de Plotly con ejes Y secundarios
fig_ts = make_subplots(specs=[[{"secondary_y": True}]])

# Agrupamos por inversor para pintar una línea por cada uno
for inversor in df_filtrado["Nombre_Inversor"].unique():
    df_inv = df_filtrado[df_filtrado["Nombre_Inversor"] == inversor]

    # Añadir traza de Potencia
    fig_ts.add_trace(
        go.Scatter(
            x=df_inv["Timestamp"],
            y=df_inv["Potencia_AC_kW"],
            name=f"Potencia ({inversor})",
            mode="lines",
            line=dict(width=2),
        ),
        secondary_y=False,  # Eje Y primario (izquierda)
    )

# Añadimos la Irradiancia (solo una vez)
# Tomamos la media si hay dos inversores (la irradiancia debería ser la misma)
df_irradiancia = df_filtrado.groupby("Timestamp")["Irradiancia_GHI_W_m2"].mean().reset_index()
fig_ts.add_trace(
    go.Scatter(
        x=df_irradiancia["Timestamp"],
        y=df_irradiancia["Irradiancia_GHI_W_m2"],
        name="Irradiancia (W/m²)",
        mode="lines",
        line=dict(color="rgba(255, 165, 0, 0.5)", dash="dot"),  # Naranja punteado
    ),
    secondary_y=True,  # Eje Y secundario (derecha)
)

# Configuración de los ejes y el layout
fig_ts.update_layout(
    title="Potencia AC vs. Irradiancia GHI",
    xaxis_title="Fecha y Hora",
    yaxis_title="Potencia AC (kW)",
    yaxis2_title="Irradiancia GHI (W/m²)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_ts, use_container_width=True)


# --- Gráficos de Análisis Secundarios ---
st.header("Análisis de Correlación y Distribución")
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    # Gráfico 1: Curva de Potencia (Irradiancia vs Potencia)
    # Usamos Seaborn para esto, ya que 'hue' es muy conveniente
    st.subheader("Curva de Potencia (Scatter Plot)")

    # Filtramos solo datos diurnos para un gráfico más limpio
    df_diurno = df_filtrado[df_filtrado["Irradiancia_GHI_W_m2"] > 50]

    fig_scatter, ax_scatter = plt.subplots()
    sns.scatterplot(
        data=df_diurno,
        x="Irradiancia_GHI_W_m2",
        y="Potencia_AC_kW",
        hue="Nombre_Inversor",
        alpha=0.5,
        s=5,  # Tamaño de punto pequeño
        ax=ax_scatter,
    )
    ax_scatter.set_title("Potencia vs. Irradiancia")
    ax_scatter.set_xlabel("Irradiancia (W/m²)")
    ax_scatter.set_ylabel("Potencia (kW)")
    ax_scatter.grid(True)
    st.pyplot(fig_scatter)
    st.caption(
        """
    **Análisis:** - **Día 1 (07-01):** Curva perfecta.
    - **Día 2 (07-02):** Puntos bajos (nublado).
    - **Día 3 (07-03):** Se ve un 'techo' plano arriba (clipping/recorte) y puntos dispersos por nubes.
    """
    )

with col_graf2:
    # Gráfico 2: Distribución de Potencia (Boxplot)
    st.subheader("Distribución de Potencia por Inversor")

    fig_box, ax_box = plt.subplots()
    sns.boxplot(
        data=df_diurno,  # Usamos los mismos datos diurnos
        x="Nombre_Inversor",
        y="Potencia_AC_kW",
        ax=ax_box,
    )
    ax_box.set_title("Distribución de la Potencia Diurna")
    ax_box.set_xlabel("Inversor")
    ax_box.set_ylabel("Potencia (kW)")
    st.pyplot(fig_box)
    st.caption(
        """
    **Análisis:**
    - Compara la mediana (línea central) y los rangos de producción de cada inversor.
    - El 'Inversor-B' fue simulado para ser ligeramente menos eficiente, lo que se refleja aquí.
    """
    )

# --- Tabla de Datos Crudos (Opcional) ---
st.markdown("---")
if st.checkbox("Mostrar datos crudos filtrados"):
    st.subheader("Datos Crudos")
    st.dataframe(df_filtrado)
