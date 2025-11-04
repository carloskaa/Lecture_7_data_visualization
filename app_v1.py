# Este es el contenido de nuestro PRIMER archivo .py

import streamlit as st
import pandas as pd
import numpy as np

# --- Función de Datos ---
# (Copiamos la función de la celda anterior)
def simular_datos_pv():
    timestamps = pd.date_range(start='2025-07-01', periods=72, freq='h')
    horas_dia = np.arange(0, 72)
    ciclo_solar_base = np.sin(np.pi * (horas_dia % 24) / 24) ** 2
    irradiancia_base = np.maximum(0, ciclo_solar_base * 1000 + np.random.normal(0, 5, 72))
    irradiancia_dia1 = irradiancia_base
    potencia_dia1 = irradiancia_dia1 * 0.15
    irradiancia_dia2 = np.maximum(0, irradiancia_base * 0.4 + np.random.normal(0, 20, 72))
    potencia_dia2 = irradiancia_dia2 * 0.15
    irradiancia_dia3 = irradiancia_base
    potencia_dia3 = irradiancia_dia3 * 0.15
    potencia_dia3[24+11] *= 0.3
    potencia_dia3[24+14] *= 0.4
    df_wide = pd.DataFrame(
        data={'Potencia_Dia1': potencia_dia1, 'Irradiancia_Dia1': irradiancia_dia1,
              'Potencia_Dia2': potencia_dia2, 'Irradiancia_Dia2': irradiancia_dia2,
              'Potencia_Dia3': potencia_dia3, 'Irradiancia_Dia3': irradiancia_dia3},
        index=timestamps)
    df_reset = df_wide.reset_index().rename(columns={'index': 'Timestamp'})
    df_d1 = df_reset[['Timestamp', 'Irradiancia_Dia1', 'Potencia_Dia1']].rename(
        columns={'Irradiancia_Dia1': 'Irradiancia', 'Potencia_Dia1': 'Potencia'})
    df_d1['Dia'] = 'Día 1 (Soleado)'
    df_d2 = df_reset[['Timestamp', 'Irradiancia_Dia2', 'Potencia_Dia2']].rename(
        columns={'Irradiancia_Dia2': 'Irradiancia', 'Potencia_Dia2': 'Potencia'})
    df_d2['Dia'] = 'Día 2 (Nublado)'
    df_d3 = df_reset[['Timestamp', 'Irradiancia_Dia3', 'Potencia_Dia3']].rename(
        columns={'Irradiancia_Dia3': 'Irradiancia', 'Potencia_Dia3': 'Potencia'})
    df_d3['Dia'] = 'Día 3 (Parcial)'
    return pd.concat([df_d1, df_d2, df_d3])

# --- Caching de Datos ---
# ¡Importante! Usamos un "decorador" de cache.
# Esto evita que Streamlit vuelva a simular los datos CADA VEZ 
# que el usuario hace clic en algo.
@st.cache_data
def cargar_datos():
    return simular_datos_pv()

# --- Construcción de la App ---
df = cargar_datos()

# st.title() -> Muestra un título grande
st.title('Mi Primer Dashboard de Energía Solar ☀️')

# st.write() -> Es el "print" de Streamlit, es mágico y muestra 
# (casi) cualquier cosa: texto, dataframes, markdown, etc.
st.write("Estos son los datos simulados de 3 días en formato largo.")

# st.dataframe() -> Muestra un DataFrame interactivo (puedes ordenar, etc.)
st.dataframe(df)
