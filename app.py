import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

# Função para conversão de unidades
def convert_vazao(series, unidade):
    if unidade == "m³/s":
        return series / 1000, "m³/s"
    return series, "L/s"

# Carregar arquivos GeoJSON
def load_geojson(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

geojson_trechos = load_geojson("trechos_perene.geojson")
geojson_acudes = load_geojson("Açudes_Monitorados.geojson")
geojson_sedes = load_geojson("Sedes_Municipais.geojson")
geojson_c_gestoras = load_geojson("c_gestoras.geojson")
geojson_poligno = load_geojson("poligno_municipios.geojson")
geojson_bacia = load_geojson("bacia_banabuiu.geojson")
geojson_pontos = load_geojson("pontos_controle.geojson")

st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# CSS Sidebar e Cabeçalho
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    [data-testid="stSidebar"]::after {
        content: "";
        position: fixed;
        bottom: 60px;
        left: 0;
        width: 240px;
        height: 50px;
        background-image: url('https://i.ibb.co/tpQrmPb0/csbh.png');
        background-repeat: no-repeat;
        background-size: contain;
        background-position: center;
        z-index: 999;
    }
    .fixed-header {
        top: 50px;
        left: 0;
        right: 0;
        z-index: 1000;
        background-color: #e0f0ff;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 12px;
        padding: 10px 20px;
        border-bottom: 2px solid #ccc;
    }
    .stApp {
        padding-top: 80px;
    }
    </style>
    <div class="fixed-header">
        <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" style="height: 50px;">
        <h2 style="margin: 0; color: #003366;">Operação 2025.2</h2>
    </div>
""", unsafe_allow_html=True)

# Menu lateral
with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"],
        icons=["droplet", "map"],
        default_index=0
    )

if aba == "Vazões - GRBANABUIU":
    @st.cache_data
    def load_data():
        url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
        df = pd.read_csv(url)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mês'] = df['Data'].dt.to_period('M').astype(str)
        return df

    df = load_data()

    st.title("💧 Vazões - GRBANABUIU")

    with st.sidebar:
        st.header("🔎 Filtros")
        unidade_sel = st.radio("Unidade", ["L/s", "m³/s"], index=0)
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        datas_disponiveis = df['Data'].dropna().sort_values()
        data_min, data_max = datas_disponiveis.min(), datas_disponiveis.max()
        intervalo_data = st.date_input("📅 Intervalo de Datas", (data_min, data_max), format="DD/MM/YYYY")
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
            "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
            "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
        ], index=0)

    # Filtro de dados
    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    if isinstance(intervalo_data, tuple):
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(inicio)) & (df_filtrado['Data'] <= pd.to_datetime(fim))]

    st.subheader("📈 Evolução da Vazão Operada por Reservatório")

    fig = go.Figure()
    cores = px.colors.qualitative.Set2
    datas = df_filtrado["Data"].sort_values()
    x_range = [datas.min(), datas.max()]

    reservatorios_filtrados = df_filtrado['Reservatório Monitorado'].unique()
    for i, reservatorio in enumerate(reservatorios_filtrados):
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values(by="Data")
        y_vals, unit_suffix = convert_vazao(df_res['Vazão Operada'], unidade_sel)
        df_res['Vazão Suavizada'] = y_vals.rolling(window=5, center=True, min_periods=1).mean()

        fig.add_trace(go.Scatter(
            x=df_res["Data"],
            y=df_res["Vazão Suavizada"],
            mode="lines",
            name=reservatorio,
            line=dict(shape='spline', width=2, color=cores[i % len(cores)], smoothing=1.3),
            hovertemplate=(
                f"<b>{reservatorio}</b><br>"
                "Data: %{x|%d/%m/%Y}<br>"
                f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
            )
        ))

    # Média ponderada se apenas um reservatório
    if len(reservatorios_filtrados) == 1:
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorios_filtrados[0]].sort_values(by="Data")
        df_res = df_res.groupby('Data', as_index=False).last()
        y_vals, unit_suffix = convert_vazao(df_res["Vazão Operada"], unidade_sel)

        df_daily = pd.DataFrame({'Data': pd.date_range(df_res["Data"].min(), df_res["Data"].max(), freq='D')})
        df_daily["VazaoConv"] = pd.Series(y_vals.values, index=df_res["Data"]).reindex(df_daily["Data"]).ffill()
        media_val = df_daily["VazaoConv"].mean()

        fig.add_trace(go.Scatter(
            x=x_range,
            y=[media_val, media_val],
            mode="lines+text",
            name=f"Média: {media_val:.3f} {unit_suffix}",
            line=dict(color="red", width=4, dash="dash"),
            text=[f"Média: {media_val:.3f} {unit_suffix}", ""],
            textposition="top right",
            showlegend=False
        ))

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title=f"Vazão Operada ({unit_suffix})",
        legend_title="Reservatório",
        template="simple_white",
        hovermode="closest"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Mapa com todas as camadas (mesmo que antes)
    st.subheader("🗺️ Mapa dos Reservatórios com Pinos")
    df_mapa = df_filtrado.copy()
    if 'Coordendas' in df_mapa.columns:
        df_mapa[['lat', 'lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
        df_mapa = df_mapa.dropna(subset=['lat', 'lon']).drop_duplicates(subset=['Reservatório Monitorado'])

    if not df_mapa.empty:
        center = [df_mapa['lat'].mean(), df_mapa['lon'].mean()]
        m = folium.Map(location=center, zoom_start=8, tiles=mapa_tipo)

        folium.GeoJson(geojson_bacia, name="Bacia do Banabuiu").add_to(m)
        folium.GeoJson(geojson_trechos, name="Trechos Perenizados").add_to(m)
        folium.GeoJson(geojson_acudes, name="Açudes Monitorados").add_to(m)
        folium.GeoJson(geojson_poligno, name="Polígonos Municipais").add_to(m)

        for _, row in df_mapa.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)),
                tooltip=row["Reservatório Monitorado"]
            ).add_to(m)

        folium.LayerControl().add_to(m)
        folium_static(m, width=1200)

    # Média da Vazão Operada
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
    media_vazao["Vazão Operada"], unit_suffix = convert_vazao(media_vazao["Vazão Operada"], unidade_sel)
    st.plotly_chart(px.bar(media_vazao, x="Reservatório Monitorado", y="Vazão Operada", text_auto='.2f'), use_container_width=True)

    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)

elif aba == "🗺️ Açudes Monitorados":
    st.title("🗺️ Açudes Monitorados")
    tile_option = st.sidebar.selectbox("🗺️ Estilo do Mapa (Açudes)", [
        "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
        "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
    ])
    center = [-5.2, -39.2]
    m = folium.Map(location=center, zoom_start=7, tiles=tile_option)
    folium.GeoJson(geojson_acudes, name="Açudes").add_to(m)
    folium.LayerControl().add_to(m)
    folium_static(m, width=1200)
