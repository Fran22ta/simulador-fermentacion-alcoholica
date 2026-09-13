import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Simulador de Fermentación Alcohólica",
    page_icon="🍷",
    layout="wide"
)

st.title("🍷 Simulador de Fermentación Alcohólica")
st.write(
    "Modifica las condiciones del mosto y observa cómo afectan "
    "al desarrollo de la fermentación."
)

# ============================================================
# CONTROLES
# ============================================================

st.sidebar.header("Condiciones iniciales")

azucar_inicial = st.sidebar.slider(
    "Azúcar inicial (g/L)",
    min_value=150,
    max_value=320,
    value=220,
    step=5
)

temperatura = st.sidebar.slider(
    "Temperatura (°C)",
    min_value=10.0,
    max_value=38.0,
    value=22.0,
    step=0.5
)

yan = st.sidebar.slider(
    "YAN (mg/L)",
    min_value=20,
    max_value=350,
    value=180,
    step=10
)

ph = st.sidebar.slider(
    "pH",
    min_value=2.6,
    max_value=4.2,
    value=3.4,
    step=0.1
)

inoculo = st.sidebar.slider(
    "Inóculo (millones células/mL)",
    min_value=0.1,
    max_value=5.0,
    value=1.0,
    step=0.1
)

dias = st.sidebar.slider(
    "Duración de la simulación (días)",
    min_value=5,
    max_value=20,
    value=15
)

# ============================================================
# FUNCIONES DEL MODELO
# ============================================================

def factor_temperatura(temp):

    if temp < 12:
        return 0.05

    elif temp < 16:
        return 0.30

    elif temp < 20:
        return 0.70

    elif temp <= 26:
        return 1.00

    elif temp <= 30:
        return 0.85

    elif temp <= 33:
        return 0.50

    elif temp <= 35:
        return 0.20

    else:
        return 0.03


def factor_yan(valor):

    if valor < 50:
        return 0.20

    elif valor < 100:
        return 0.45

    elif valor < 150:
        return 0.75

    else:
        return 1.00


def factor_ph(valor):

    if valor < 2.8:
        return 0.25

    elif valor < 3.0:
        return 0.60

    elif valor <= 3.8:
        return 1.00

    elif valor <= 4.0:
        return 0.85

    else:
        return 0.70


def factor_inoculo(valor):

    return min(1.0, valor / 1.0)


def factor_etanol(valor):

    if valor < 10:
        return 1.00

    elif valor < 12:
        return 0.90

    elif valor < 14:
        return 0.70

    elif valor < 15:
        return 0.45

    else:
        return 0.20


def factor_osmotico(azucar):

    if azucar <= 220:
        return 1.00

    elif azucar <= 250:
        return 0.90

    elif azucar <= 280:
        return 0.75

    else:
        return 0.55


# ============================================================
# SIMULACIÓN
# ============================================================

paso = 0.1

tiempos = np.arange(0, dias + paso, paso)

azucar = float(azucar_inicial)
etanol = 0.0

datos = []

for dia in tiempos:

    # Factores de actividad
    f_temp = factor_temperatura(temperatura)
    f_yan = factor_yan(yan)
    f_ph = factor_ph(ph)
    f_inoculo = factor_inoculo(inoculo)
    f_etoh = factor_etanol(etanol)
    f_osm = factor_osmotico(azucar)

    actividad = (
        f_temp
        * f_yan
        * f_ph
        * f_inoculo
        * f_etoh
        * f_osm
    )

    # Fase inicial de adaptación
    if dia < 0.5:
        factor_fase = 0.20

    elif dia < 1.0:
        factor_fase = 0.60

    else:
        factor_fase = 1.00

    # Velocidad máxima de consumo de azúcar
    velocidad_maxima = 35.0

    velocidad = (
        velocidad_maxima
        * actividad
        * factor_fase
    )

    # Ralentización cuando queda poco azúcar
    if azucar < 20:
        velocidad = velocidad * (azucar / 20)

    consumo = velocidad * paso

    consumo = min(consumo, azucar)

    # Guardamos el azúcar antes de consumirlo
    azucar_anterior = azucar

    # Consumo de azúcar
    azucar = max(0.0, azucar - consumo)

    # Producción aproximada de etanol
    etanol = etanol + consumo / 17.0

    # Brix simplificado
    brix = azucar / 10.0

    # Densidad didáctica aproximada
    densidad = (
        0.998
        + (0.00038 * azucar)
        - (0.0012 * etanol)
    )

    # Producción relativa de CO2
    co2 = consumo / paso if paso > 0 else 0

    datos.append(
        {
            "Día": dia,
            "Azúcar (g/L)": azucar,
            "Brix": brix,
            "Densidad": densidad,
            "Alcohol (% vol)": etanol,
            "Actividad": actividad * 100,
            "CO2 relativo": co2
        }
    )


# ============================================================
# TABLA DE RESULTADOS
# ============================================================

df = pd.DataFrame(datos)

azucar_final = df["Azúcar (g/L)"].iloc[-1]
alcohol_final = df["Alcohol (% vol)"].iloc[-1]
densidad_final = df["Densidad"].iloc[-1]

# Consumo durante aproximadamente el último día
indice_dia_anterior = max(0, len(df) - 11)

consumo_ultimo_dia = (
    df["Azúcar (g/L)"].iloc[indice_dia_anterior]
    - azucar_final
)

# ============================================================
# DIAGNÓSTICO
# ============================================================

if azucar_final <= 4:

    estado = "FERMENTACIÓN COMPLETA"
    simbolo = "🟢"

elif consumo_ultimo_dia < 2:

    estado = "FERMENTACIÓN PARADA"
    simbolo = "🔴"

else:

    estado = "FERMENTACIÓN LENTA"
    simbolo = "🟠"


# ============================================================
# RESULTADOS PRINCIPALES
# ============================================================

st.header("Resultados de la fermentación")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Azúcar residual",
    f"{azucar_final:.1f} g/L"
)

col2.metric(
    "Alcohol",
    f"{alcohol_final:.1f} % vol"
)

col3.metric(
    "Densidad final",
    f"{densidad_final:.3f}"
)

col4.metric(
    "Diagnóstico",
    f"{simbolo} {estado}"
)

# ============================================================
# GRÁFICA AZÚCAR Y ALCOHOL
# ============================================================

st.subheader("Evolución del azúcar y del alcohol")

fig1 = go.Figure()

fig1.add_trace(
    go.Scatter(
        x=df["Día"],
        y=df["Azúcar (g/L)"],
        mode="lines",
        name="Azúcar (g/L)",
        line=dict(width=4)
    )
)

fig1.add_trace(
    go.Scatter(
        x=df["Día"],
        y=df["Alcohol (% vol)"],
        mode="lines",
        name="Alcohol (% vol)",
        yaxis="y2",
        line=dict(width=4)
    )
)

fig1.update_layout(
    xaxis=dict(
        title="Tiempo (días)"
    ),
    yaxis=dict(
        title="Azúcar (g/L)"
    ),
    yaxis2=dict(
        title="Alcohol (% vol)",
        overlaying="y",
        side="right"
    ),
    hovermode="x unified",
    height=500
)

st.plotly_chart(fig1, use_container_width=True)


# ============================================================
# DENSIDAD
# ============================================================

st.subheader("Evolución de la densidad")

fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(
        x=df["Día"],
        y=df["Densidad"],
        mode="lines",
        name="Densidad",
        line=dict(width=4)
    )
)

fig2.update_layout(
    xaxis_title="Tiempo (días)",
    yaxis_title="Densidad",
    height=400
)

st.plotly_chart(fig2, use_container_width=True)


# ============================================================
# ACTIVIDAD FERMENTATIVA
# ============================================================

st.subheader("Actividad relativa de la levadura")

fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=df["Día"],
        y=df["Actividad"],
        mode="lines",
        name="Actividad",
        line=dict(width=4)
    )
)

fig3.update_layout(
    xaxis_title="Tiempo (días)",
    yaxis_title="Actividad relativa (%)",
    height=400
)

st.plotly_chart(fig3, use_container_width=True)


# ============================================================
# CO2
# ============================================================

st.subheader("Producción relativa de CO₂")

fig4 = go.Figure()

fig4.add_trace(
    go.Scatter(
        x=df["Día"],
        y=df["CO2 relativo"],
        mode="lines",
        name="CO₂",
        fill="tozeroy"
    )
)

fig4.update_layout(
    xaxis_title="Tiempo (días)",
    yaxis_title="Producción relativa de CO₂",
    height=400
)

st.plotly_chart(fig4, use_container_width=True)


# ============================================================
# DIAGNÓSTICO DIDÁCTICO
# ============================================================

st.header("Diagnóstico de las condiciones")

problemas = []

if yan < 100:
    problemas.append(
        "YAN bajo: posible limitación nutricional."
    )

if temperatura < 16:
    problemas.append(
        "Temperatura baja: reducción de la actividad metabólica."
    )

if temperatura > 30:
    problemas.append(
        "Temperatura elevada: riesgo de inhibición o pérdida de viabilidad."
    )

if ph < 3.0:
    problemas.append(
        "pH bajo: condiciones desfavorables para la actividad fermentativa."
    )

if ph > 4.0:
    problemas.append(
        "pH elevado: mayor riesgo de desarrollo de microorganismos alterantes."
    )

if azucar_inicial > 280:
    problemas.append(
        "Azúcar inicial elevado: posible estrés osmótico."
    )

if inoculo < 0.5:
    problemas.append(
        "Inóculo bajo: implantación inicial insuficiente."
    )

if len(problemas) == 0:

    st.success(
        "Las condiciones seleccionadas son favorables para la fermentación."
    )

else:

    for problema in problemas:
        st.warning(problema)


# ============================================================
# ACTIVIDAD PARA EL ALUMNO
# ============================================================

st.header("Actividad del alumno")

st.info(
    """
    Analiza las curvas antes de modificar los parámetros.

    1. ¿La fermentación es normal, lenta o está parada?

    2. ¿Qué factor consideras limitante?

    3. ¿Qué medida correctora aplicarías?

    4. Modifica únicamente ese parámetro.

    5. Compara la nueva curva con la fermentación anterior.
    """
)


# ============================================================
# DATOS DIARIOS
# ============================================================

st.header("Datos analíticos")

# Extraemos aproximadamente un dato por día
df_diario = df.iloc[::10].copy()

df_diario["Día"] = df_diario["Día"].round(0).astype(int)

st.dataframe(
    df_diario.round(
        {
            "Azúcar (g/L)": 1,
            "Brix": 1,
            "Densidad": 3,
            "Alcohol (% vol)": 1,
            "Actividad": 1,
            "CO2 relativo": 1
        }
    ),
    use_container_width=True
)