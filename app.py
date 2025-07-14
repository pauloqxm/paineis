import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

# ————————————————
# Carrega GeoJSONs
# ————————————————
with open("rio_quixera.geojson", "r", encoding="utf-8") as f:
    geojson_quixera = json.load(f)
with open("Açudes_Monitorados.geojson", "r", encoding="utf-8") as f:
    geojson_acudes = json.load(f)
with open("Sedes_Municipais.geojson", "r", encoding="utf-8") as f:
    geojson_sedes = json.load(f)
with open("c_gestoras.geojson", "r", encoding="utf-8") as f:
    geojson_c_gestoras = json.load(f)
with open("poligno_municipios.geojson", "r", encoding="utf-8") as f:
    geojson_poligno = json.load(f)

# ————————————————
# Configuração da página
# ————————————————
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# ————————————————
# Cabeçalho fixo
# ————————————————
st.markdown(
    """
    <style>
    .fixed-header {
        position: fixed;
        top: 0;
        left: 260px;
        right: 0;
        height: 70px;
        background-color: #e0f0ff;
        border-bottom: 2px solid #ccc;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 12px;
        padding: 10px 20px;
        z-index: 1000;
    }
    .stApp {
        padding-top: 80px;
    }
    @media (max-width: 768px) {
        .fixed-header {
            left: 0;
            width: 100vw;
            padding: 10px;
        }
    }
    </style>
    <div class="fixed-header">
        <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" alt="Logo COGERH" style="height:50px;">
        <h2 style="margin:0; color:#003366;">Operação 2025.2</h2>
    </div>
    """,
    unsafe_allow_html=True
)

# ————————————————
# Barra lateral (menu + rodapé)
# ————————————————
with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"],
        icons=["droplet", "map"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

    # — Rodapé da sidebar —
    st.markdown(
        """
        <style>
        /* torna o contêiner da navegação relativo */
        [data-testid="stSidebarNav"] {
            position: relative;
            padding-bottom: 100px; /* espaço para o rodapé */
        }
        /* imagem no rodapé */
        [data-testid="stSidebarNav"]::after {
            content: "";
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 60px;
            background-image: url('https://i.ibb.co/tpQrmPb0/csbh.png');
            background-size: contain;
            background-repeat: no-repeat;
        }
        /* texto abaixo da imagem */
        [data-testid="stSidebarNav"]::before {
            content: "GRBANABUIU";
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 14px;
            font-weight: bold;
            color: #003366;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# ————————————————
# Aba 1: Vazões - GRBANABUIU
# ————————————————
if aba == "Vazões - GRBANABUIU":
    @st.cache_data
    def load_data():
        url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
        df = pd.read_csv(url)
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
        df["Mês"] = df["Data"].dt.to_period("M").astype(str)
        return df

    df = load_data()
    st.title("💧 Vazões - GRBANABUIU")

    # Filtros
    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório", df["Reservatório Monitorado"].unique())
        meses = st.multiselect("📆 Mês", df["Mês"].unique())
        intervalo = st.date_input("📅 Intervalo", (df["Data"].min(), df["Data"].max()), format="DD/MM/YYYY")
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa",
                                ["OpenStreetMap", "Stamen Terrain", "Stamen Toner",
                                 "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"])

    df_f = df.copy()
    if estacoes:
        df_f = df_f[df_f["Reservatório Monitorado"].isin(estacoes)]
    if meses:
        df_f = df_f[df_f["Mês"].isin(meses)]
    if isinstance(intervalo, tuple):
        df_f = df_f[(df_f["Data"] >= pd.to_datetime(intervalo[0])) & (df_f["Data"] <= pd.to_datetime(intervalo[1]))]

    st.subheader("📈 Evolução da Vazão")
    fig = go.Figure()
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    for i, res in enumerate(df_f["Reservatório Monitorado"].unique()):
        dfr = df_f[df_f["Reservatório Monitorado"] == res].sort_values("Data")
        dfr["Suavizada"] = dfr["Vazão Operada"].rolling(5, center=True, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=dfr["Data"], y=dfr["Suavizada"],
            mode="lines", name=res,
            line=dict(shape="spline", color=cores[i % len(cores)], width=2, smoothing=1.3)
        ))
    st.plotly_chart(fig, use_container_width=True)

    # ... restante do código ...

# ————————————————
# Aba 2: Açudes Monitorados
# ————————————————
elif aba == "🗺️ Açudes Monitorados":
    st.title("🗺️ Açudes Monitorados")
    tile = st.sidebar.selectbox("🗺️ Estilo", ["OpenStreetMap", "Esri Satellite"])
    with open("Açudes_Monitorados.geojson", "r", encoding="utf-8") as f:
        data = json.load(f)
    m = folium.Map(location=[-5.2, -39.2], zoom_start=7, tiles=tile)
    folium.GeoJson(data, tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])).add_to(m)
    folium_static(m, width=None)
