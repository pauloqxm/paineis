import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import json
import locale
import datetime
# Define o locale para pt-BR
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("⚠️ Não foi possível aplicar o locale pt_BR no ambiente atual.")

with open("rio_quixera.geojson", "r", encoding="utf-8") as f:
    geojson_quixera = json.load(f)
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Dashboard Vazões", layout="wide")

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
        df = pd.read_excel("GRBANABUIU_VAZÕES.xlsx")
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['Mês'] = df['Data'].dt.to_period('M').astype(str)
        return df

    df = load_data()

    with open("Açudes_Monitorados.geojson", "r", encoding="utf-8") as f:
        geojson_acudes = json.load(f)

    st.title("💧 Vazões - GRBANABUIU")

    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        datas_disponiveis = df['Data'].dropna().sort_values()
        data_min = datas_disponiveis.min()
        data_max = datas_disponiveis.max()
        intervalo_data = st.date_input(
            "📅 Intervalo de Datas",
            (data_min, data_max),
            format="DD/MM/YYYY"
        )
        mapa_tipo = st.selectbox(
            "🗺️ Estilo do Mapa",
            options=[
                "OpenStreetMap",
                "Stamen Terrain",
                "Stamen Toner",
                "CartoDB positron",
                "CartoDB dark_matter",
                "Esri Satellite"
            ],
            index=0
        )
        mostrar_acudes = st.checkbox("💧 Exibir Açudes Monitorados no mapa", value=True)

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

    for reservatorio in df_filtrado['Reservatório Monitorado'].unique():
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values(by="Data")
        fig.add_trace(go.Scatter(
            x=df_res["Data"],
            y=df_res["Vazão Operada"],
            mode="lines+markers",
            name=reservatorio,
            line=dict(shape='linear')  # linha reta tradicional
        ))

    if len(df_filtrado['Reservatório Monitorado'].unique()) == 1:
        media_geral = df_filtrado["Vazão Operada"].mean()
        fig.add_hline(
            y=media_geral,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Média: {media_geral:.2f} l/s",
            annotation_position="top left"
        )

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Vazão Operada",
        legend_title="Reservatório Monitorado"
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

        if mostrar_acudes:
            folium.GeoJson(
                geojson_acudes,
                name="Açudes Monitorados",
                tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])
            ).add_to(m)

        folium.GeoJson(
            geojson_quixera,
            name="Trecho Perenizado",
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Trecho:"]),
            style_function=lambda x: {"color": "darkblue", "weight": 2}
        ).add_to(m)

        for _, row in df_mapa.iterrows():
            popup_info = f"""
            <strong>Reservatório:</strong> {row['Reservatório Monitorado']}<br>
            <strong>Data:</strong> {row['Data'].date()}<br>
            <strong>Vazão Operada:</strong> {row['Vazão Operada']} m³/s
            """
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_info, max_width=300),
                icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
                tooltip=row["Reservatório Monitorado"]
            ).add_to(m)

        folium.LayerControl().add_to(m)
        folium_static(m)
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
        "OpenStreetMap",
        "Stamen Terrain",
        "Stamen Toner",
        "CartoDB positron",
        "CartoDB dark_matter",
        "Esri Satellite"
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
    folium_static(m)
