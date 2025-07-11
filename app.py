
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

# 🌐 Estilo da barra lateral
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    </style>
    """, unsafe_allow_html=True)

# ⚙️ Configuração
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# 📁 Menu lateral
with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU"],
        icons=["droplet"],
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

    st.title("💧 Vazões - GRBANABUIU")

    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        mapa_tipo = st.selectbox(
            "🗺️ Estilo do Mapa",
            options=["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0
        )

    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]

    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    st.plotly_chart(
        px.line(
            df_filtrado,
            x="Data",
            y="Vazão Operada",
            color="Reservatório Monitorado",
            markers=True
        ),
        use_container_width=True
    )

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
