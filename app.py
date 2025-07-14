import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
import datetime
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

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

st.markdown("""
    <style>
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
        position: relative;
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
    </style>
    </style>
""", unsafe_allow_html=True)
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

st.markdown("""
    <style>
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        background-color: #e0f0ff;
        display: flex;
        align-items: right;
        gap: 12px;
        padding: 10px 20px;
        border-bottom: 2px solid #ccc;
    }
    .stApp {
        padding-top: 80px;
    }
    </style>
    <div class="fixed-header">
        <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" alt="Logo COGERH" style="height: 50px;">
        <h2 style="margin: 0; color: #003366;">Operação 2025.2</h2>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"],
        icons=["droplet", "map"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
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
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        datas_disponiveis = df['Data'].dropna().sort_values()
        data_min = datas_disponiveis.min()
        data_max = datas_disponiveis.max()
        intervalo_data = st.date_input("📅 Intervalo de Datas", (data_min, data_max), format="DD/MM/YYYY")
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
            "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
            "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
        ], index=0)

    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(inicio)) & (df_filtrado['Data'] <= pd.to_datetime(fim))]

    st.subheader("📈 Evolução da Vazão Operada por Reservatório")

    fig = go.Figure()
    cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    datas = df_filtrado["Data"].sort_values()
    x_range = [datas.min(), datas.max()]

    reservatorios_filtrados = df_filtrado['Reservatório Monitorado'].unique()
    for i, reservatorio in enumerate(reservatorios_filtrados):
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values(by="Data")
        # Aplicando média móvel para suavização
        df_res['Vazão Suavizada'] = df_res['Vazão Operada'].rolling(window=5, center=True, min_periods=1).mean()
        cor = cores[i % len(cores)]
        fig.add_trace(go.Scatter(
            x=df_res["Data"],
            y=df_res["Vazão Suavizada"],
            mode="lines",
            name=reservatorio,
            line=dict(shape='spline', width=2, color=cor, smoothing=1.3),
            hoverinfo='text',
            hovertext=[f"<b>{reservatorio}</b><br>Data: {d.strftime('%d/%m/%Y')}<br>Vazão: {v:.2f} l/s" 
                      for d, v in zip(df_res['Data'], df_res['Vazão Operada'])]
        ))

    if len(reservatorios_filtrados) == 1:
        media_res = df_filtrado["Vazão Operada"].mean()
        fig.add_trace(go.Scatter(
            x=x_range,
            y=[media_res, media_res],
            mode="lines+text",
            name=f"Média: {media_res:.2f} l/s",
            line=dict(color="red", width=4, dash="dash"),
            text=[f"Média: {media_res:.2f} l/s", ""],
            textposition="top right",
            showlegend=False
        ))

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Vazão Operada (l/s)",
        legend_title="Reservatório",
        template="simple_white",
        hovermode="closest",
        margin=dict(l=40, r=20, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺️ Mapa dos Reservatórios com Pinos")
    df_mapa = df_filtrado.copy()
    df_mapa[['lat', 'lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
    df_mapa = df_mapa.dropna(subset=['lat', 'lon']).drop_duplicates(subset=['Reservatório Monitorado'])

    tile_urls = {
        "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    }
    tile_attr = {
        "Esri Satellite": "Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, etc."
    }

    if not df_mapa.empty:
        center = [df_mapa['lat'].mean(), df_mapa['lon'].mean()]
        if mapa_tipo in tile_urls:
            m = folium.Map(location=center, zoom_start=8, tiles=None)
            folium.TileLayer(tiles=tile_urls[mapa_tipo], attr=tile_attr[mapa_tipo], name=mapa_tipo).add_to(m)
        else:
            m = folium.Map(location=center, zoom_start=8, tiles=mapa_tipo)

        #Camada Trecho Perenizado
        folium.GeoJson(
            geojson_quixera,
            name="Trecho Perenizado",
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Trecho:"]),
            style_function=lambda x: {"color": "darkblue", "weight": 2}
        ).add_to(m)

        # Camada Açudes Monitorados
        acudes_layer = folium.FeatureGroup(name="Açudes Monitorados", show=False)
        folium.GeoJson(
            geojson_acudes,
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]),
            style_function=lambda x: {"color": "darkgreen", "weight": 2}
        ).add_to(acudes_layer)
        acudes_layer.add_to(m)
        
        # Camada Sedes Municipais com ícone PNG personalizado
        sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
        for feature in geojson_sedes["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            nome_municipio = props.get("NOME_MUNIC", "Sem nome")
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(22, 22)),
                tooltip=nome_municipio
            ).add_to(sedes_layer)
        sedes_layer.add_to(m)
        
        # Camada Comissões Gestoras
        gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
        for feature in geojson_c_gestoras["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            nome_gestora = props.get("SISTEMAH3", "Sem nome")
            popup_info = f"""
            <strong>Célula Gestora:</strong> {nome_gestora}<br>
            <strong>Ano de Formação:</strong> {props.get("ANOFORMA1", "N/A")}<br>
            <strong>Sistema:</strong> {props.get("SISTEMAH3", "N/A")}<br>
            <strong>Município:</strong> {props.get("MUNICIPI6", "N/A")}
            """
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30, 30)),
                tooltip=nome_gestora,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(gestoras_layer)
        gestoras_layer.add_to(m)

        # Camada Polígono dos Municípios com borda azul fina
        municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
        folium.GeoJson(
            geojson_poligno,
            tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]),
            style_function=lambda x: {
                "fillOpacity": 0,
                "color": "blue",
                "weight": 1
            }
        ).add_to(municipios_layer)
        municipios_layer.add_to(m)

        for _, row in df_mapa.iterrows():
            popup_info = f"""
<strong>Reservatório:</strong> {row['Reservatório Monitorado']}<br>
<strong>Data:</strong> {row['Data'].date()}<br>
<strong>Vazão Alocada:</strong> {row['Vazao_Aloc']} l/s
"""
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_info, max_width=300),
                icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)),
                tooltip=row["Reservatório Monitorado"]
            ).add_to(m)

        folium.LayerControl().add_to(m)
        folium_static(m, width=1200)  # Ajuste para mapa wide
    else:
        st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
    st.plotly_chart(
        px.bar(
            media_vazao,
            x="Reservatório Monitorado",
            y="Vazão Operada",
            text_auto='.2s'
        ),
        use_container_width=True
    )

    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)

elif aba == "🗺️ Açudes Monitorados":
    st.title("🗺️ Açudes Monitorados")

    tile_option = st.sidebar.selectbox("🗺️ Estilo do Mapa (Açudes)", [
        "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
        "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
    ], key="acudes_map_tile")

    tile_urls = {
        "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    }
    tile_attr = {
        "Esri Satellite": "Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, etc."
    }

    with open("Açudes_Monitorados.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    center = [-5.2, -39.2]
    if tile_option in tile_urls:
        m = folium.Map(location=center, zoom_start=7, tiles=None)
        folium.TileLayer(tiles=tile_urls[tile_option], attr=tile_attr[tile_option], name=tile_option).add_to(m)
    else:
        m = folium.Map(location=center, zoom_start=7, tiles=tile_option)

    folium.GeoJson(
        geojson_data,
        name="Açudes",
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])
    ).add_to(m)

    folium.LayerControl().add_to(m)
    folium_static(m, width=None)  # Ajuste para mapa wide
