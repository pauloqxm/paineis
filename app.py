
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json

st.set_page_config(page_title="Dashboard SDA - Folium", layout="wide")

# Barra fixa no topo
st.markdown(
    """
    <style>
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #004080;
            color: white;
            text-align: center;
            padding: 10px 0;
            z-index: 9999;
        }
        .reportview-container .main {
            padding-top: 70px;
        }
    </style>
    <div class='fixed-header'><h2>BASE DE DADOS ESPACIAIS</h2></div>
    """,
    unsafe_allow_html=True
)


# Carregar dados
df = pd.read_excel("Produtores_SDA.xlsx")
df[["LATITUDE", "LONGITUDE"]] = df["COORDENADAS"].str.split(",", expand=True)
df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
df["ORDENHA?"] = df["ORDENHA?"].str.upper().fillna("NAO")
df["INSEMINA?"] = df["INSEMINA?"].str.upper().fillna("NAO")

# Carregar GeoJSON
with open("distrito.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

with open("Chafarizes.geojson") as f:
    chafarizes_geojson = json.load(f)
with open("Pocos.geojson") as f:
    pocos_geojson = json.load(f)
with open("Sistemas de Abastecimento.geojson") as f:
    sistemas_geojson = json.load(f)
with open("Assentamentos.geojson") as f:
    assentamentos_geojson = json.load(f)


# Filtros
st.sidebar.title("🔎 Filtros")


# Botão para reiniciar filtros usando session_state
if st.sidebar.button("🔄 Reiniciar Filtros"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


tecnicos = st.sidebar.multiselect("👨‍🔧 Técnico", sorted(df["TECNICO"].dropna().unique()))
distritos = st.sidebar.multiselect("📍 Distrito", sorted(df["DISTRITO"].dropna().unique()))
compradores = st.sidebar.multiselect("🛒 Comprador", sorted(df["COMPRADOR"].dropna().unique()))
produtor = st.sidebar.text_input("🔍 Buscar Produtor")

# Estilo do mapa
tile_option = st.sidebar.selectbox("🗺️ Estilo do Mapa", [
    "OpenStreetMap",
    "Stamen Terrain",
    "Stamen Toner",
    "CartoDB positron",
    "CartoDB dark_matter",
    "Esri Satellite"
])

tile_urls = {
    "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
}

tile_attr = {
    "Esri Satellite": "Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, etc."
}

# Aplicar filtros
df_filtrado = df.copy()
if tecnicos:
    df_filtrado = df_filtrado[df_filtrado["TECNICO"].isin(tecnicos)]
if distritos:
    df_filtrado = df_filtrado[df_filtrado["DISTRITO"].isin(distritos)]
if compradores:
    df_filtrado = df_filtrado[df_filtrado["COMPRADOR"].isin(compradores)]
if produtor:
    df_filtrado = df_filtrado[df_filtrado["PRODUTOR"].str.contains(produtor, case=False, na=False)]

# Tabela
st.success(f"{len(df_filtrado)} registro(s) encontrado(s).")
st.title("📋 Dados dos Produtores")
st.dataframe(df_filtrado[["TECNICO","PRODUTOR","APELIDO","FAZENDA","DISTRITO","ORDENHA?","INSEMINA?","LATICINIO","COMPRADOR"]], use_container_width=True)

# Mapa
st.subheader("🗺️ Mapa com Distritos e Produtores")

if not df_filtrado.empty:
    center = [df_filtrado["LATITUDE"].mean(), df_filtrado["LONGITUDE"].mean()]
    if tile_option in tile_urls:
        m = folium.Map(location=center, zoom_start=10, tiles=None)
        folium.TileLayer(tiles=tile_urls[tile_option], attr=tile_attr[tile_option], name=tile_option).add_to(m)
    else:
        m = folium.Map(location=center, zoom_start=10, tiles=tile_option)

    folium.GeoJson(geojson_data, name="Distritos").add_to(m)

    for _, row in df_filtrado.iterrows():
        popup_info = f"""
        <strong>Apelido:</strong> {row['APELIDO']}<br>
        <strong>Produção dia:</strong> {row['PRODUCAO']}<br>
        <strong>Fazenda:</strong> {row['FAZENDA']}<br>
        <strong>Distrito:</strong> {row['DISTRITO']}<br>
        <strong>Escolaridade:</strong> {row['ESCOLARIDADE']}<br>
         """
        folium.Marker(
            location=[row["LATITUDE"], row["LONGITUDE"]],
            icon=folium.Icon(color="blue", icon="info-sign"),
            popup=folium.Popup(popup_info, max_width=300),
            tooltip=row["PRODUTOR"]
        ).add_to(m)

    
    # Camada de Chafarizes
    chafarizes_layer = folium.FeatureGroup(name="Chafarizes", show=False)
    for feature in chafarizes_geojson["features"]:
        coords = feature["geometry"]["coordinates"]
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=5,
            color="blue",
            fill=True,
            fill_opacity=0.7,
            tooltip="Chafariz"
        )

        folium.Marker(
            location=[coords[1], coords[0]],
            tooltip="Chafariz",
            icon=folium.Icon(color="blue", icon="tint", prefix="fa")
        ).add_to(chafarizes_layer)
    
        # Removido CircleMarker .add_to(chafarizes_layer)
    chafarizes_layer.add_to(m)

    # Camada de Poços
    pocos_layer = folium.FeatureGroup(name="Poços", show=False)
    for feature in pocos_geojson["features"]:
        coords = feature["geometry"]["coordinates"]
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=5,
            color="green",
            fill=True,
            fill_opacity=0.7,
            tooltip="Poço"
        )

        folium.Marker(
            location=[coords[1], coords[0]],
            tooltip="Poço",
            icon=folium.Icon(color="green", icon="water", prefix="fa")
        ).add_to(pocos_layer)
    
        # Removido CircleMarker .add_to(pocos_layer)
    pocos_layer.add_to(m)

    # Camada de Sistemas de Abastecimento com ícone personalizado e popup com nome da comunidade
    sistemas_layer = folium.FeatureGroup(name="Sistemas de Abastecimento", show=False)
    for feature in sistemas_geojson["features"]:
        coords = feature["geometry"]["coordinates"]
        comunidade = feature["properties"].get("Comunidade", "Sem nome")
        folium.Marker(
            location=[coords[1], coords[0]],
            popup=folium.Popup(f"Comunidade: {comunidade}", max_width=200),
            icon=folium.CustomIcon("water-tank.png", icon_size=(30, 30))
        ).add_to(sistemas_layer)
    sistemas_layer.add_to(m)

    # Camada de Assentamentos
    # Adiciona apenas features do tipo Point
    
    assentamentos_layer = folium.FeatureGroup(name="Assentamentos", show=False)
    for feature in assentamentos_geojson["features"]:
        if feature["geometry"]["type"] != "Point":
            continue
        coords = feature["geometry"]["coordinates"]
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=5,
            color="purple",
            fill=True,
            fill_opacity=0.7,
            tooltip="Assentamento"
        )

        folium.Marker(
            location=[coords[1], coords[0]],
            tooltip="Assentamento",
            icon=folium.Icon(color="purple", icon="home", prefix="fa")
        ).add_to(assentamentos_layer)
    
        # Removido CircleMarker .add_to(assentamentos_layer)
    assentamentos_layer.add_to(m)

    folium.LayerControl().add_to(m)
    folium_static(m)
else:
    st.info("Nenhum produtor encontrado com os filtros selecionados.")
