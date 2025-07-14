import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

# Carregar dados geoespaciais
geojson_files = {
    "rio_quixera": "rio_quixera.geojson",
    "acudes": "Açudes_Monitorados.geojson",
    "sedes": "Sedes_Municipais.geojson",
    "gestoras": "c_gestoras.geojson",
    "municipios": "poligno_municipios.geojson"
}

geojson_data = {}
for name, path in geojson_files.items():
    with open(path, "r", encoding="utf-8") as f:
        geojson_data[name] = json.load(f)

# Configuração da página
st.set_page_config(page_title="Dashboard Vazões", layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    .stPlotlyChart {border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# Menu lateral
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

    # Filtros
    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        
        datas_disponiveis = df['Data'].dropna().sort_values()
        data_min, data_max = datas_disponiveis.min(), datas_disponiveis.max()
        intervalo_data = st.date_input(
            "📅 Intervalo de Datas", 
            (data_min, data_max), 
            format="DD/MM/YYYY"
        )
        
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
            "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
            "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
        ], index=0)

    # Aplicar filtros
    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[
            (df_filtrado['Data'] >= pd.to_datetime(inicio)) & 
            (df_filtrado['Data'] <= pd.to_datetime(fim))
        ]

    # Gráfico de Vazão Operada
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    
    fig = go.Figure()
    cores = px.colors.qualitative.Plotly
    
    for i, reservatorio in enumerate(df_filtrado['Reservatório Monitorado'].unique()):
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values("Data")
        df_res['Vazão Suavizada'] = df_res['Vazão Operada'].rolling(3, center=True, min_periods=1).mean()
        
        fig.add_trace(go.Scatter(
            x=df_res["Data"],
            y=df_res["Vazão Suavizada"],
            mode="lines",
            name=reservatorio,
            line=dict(shape='spline', width=2, color=cores[i], smoothing=1.3),
            hovertemplate=(
                "<b>%{text}</b><br>" +
                "Data: %{x|%d/%m/%Y}<br>" +
                "Vazão: %{y:.2f} l/s<extra></extra>"
            ),
            text=[reservatorio]*len(df_res)
        ))

    if len(df_filtrado['Reservatório Monitorado'].unique()) == 1:
        media = df_filtrado["Vazão Operada"].mean()
        fig.add_hline(
            y=media, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Média: {media:.2f} l/s", 
            annotation_position="top right"
        )

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Vazão Operada (l/s)",
        legend_title="Reservatório",
        template="plotly_white",
        hovermode="closest",
        margin=dict(l=40, r=20, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Mapa Interativo
    st.subheader("🗺️ Mapa dos Reservatórios")
    
    df_mapa = df_filtrado.copy()
    if 'Coordendas' in df_mapa.columns:
        df_mapa[['lat', 'lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
        df_mapa = df_mapa.dropna(subset=['lat', 'lon']).drop_duplicates('Reservatório Monitorado')

    if not df_mapa.empty:
        m = folium.Map(
            location=[df_mapa['lat'].mean(), df_mapa['lon'].mean()],
            zoom_start=8,
            tiles=mapa_tipo if mapa_tipo != "Esri Satellite" else None
        )
        
        if mapa_tipo == "Esri Satellite":
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Tiles © Esri",
                name="Satélite"
            ).add_to(m)

        # Camadas GeoJSON
        camadas = {
            "Trecho Perenizado": {
                "data": geojson_data["rio_quixera"],
                "style": {"color": "darkblue", "weight": 2},
                "tooltip": {"fields": ["Name"], "aliases": ["Trecho:"]}
            },
            "Açudes Monitorados": {
                "data": geojson_data["acudes"],
                "style": {"color": "darkgreen", "weight": 2},
                "tooltip": {"fields": ["Name"], "aliases": ["Açude:"]},
                "show": False
            },
            "Polígonos Municipais": {
                "data": geojson_data["municipios"],
                "style": {"fillOpacity": 0, "color": "blue", "weight": 1},
                "tooltip": {"fields": ["DESCRICA1"], "aliases": ["Município:"]},
                "show": False
            }
        }

        for nome, config in camadas.items():
            layer = folium.FeatureGroup(name=nome, show=config.get("show", True))
            folium.GeoJson(
                config["data"],
                style_function=lambda x, c=config: c["style"],
                tooltip=folium.GeoJsonTooltip(**config["tooltip"])
            ).add_to(layer)
            layer.add_to(m)

        # Marcadores personalizados
        icones = {
            "Sedes Municipais": {
                "icon": "https://cdn-icons-png.flaticon.com/512/854/854878.png",
                "size": (22, 22)
            },
            "Comissões Gestoras": {
                "icon": "https://cdn-icons-png.flaticon.com/512/4144/4144517.png",
                "size": (30, 30)
            }
        }

        for nome, source in [("Sedes Municipais", "sedes"), ("Comissões Gestoras", "gestoras")]:
            layer = folium.FeatureGroup(name=nome, show=False)
            for feature in geojson_data[source]["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                
                if nome == "Sedes Municipais":
                    folium.Marker(
                        location=[coords[1], coords[0]],
                        icon=folium.CustomIcon(icones[nome]["icon"], icon_size=icones[nome]["size"]),
                        tooltip=props.get("NOME_MUNIC", "Sem nome")
                    ).add_to(layer)
                else:
                    popup = folium.Popup(
                        f"""<strong>Célula Gestora:</strong> {props.get("SISTEMAH3", "N/A")}<br>
                        <strong>Ano de Formação:</strong> {props.get("ANOFORMA1", "N/A")}<br>
                        <strong>Município:</strong> {props.get("MUNICIPI6", "N/A")}""",
                        max_width=300
                    )
                    folium.Marker(
                        location=[coords[1], coords[0]],
                        icon=folium.CustomIcon(icones[nome]["icon"], icon_size=icones[nome]["size"]),
                        tooltip=props.get("SISTEMAH3", "Sem nome"),
                        popup=popup
                    ).add_to(layer)
            layer.add_to(m)

        # Marcadores dos reservatórios
        for _, row in df_mapa.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(
                    f"""<strong>Reservatório:</strong> {row['Reservatório Monitorado']}<br>
                    <strong>Data:</strong> {row['Data'].date()}<br>
                    <strong>Vazão Alocada:</strong> {row['Vazao_Aloc']} l/s""",
                    max_width=300
                ),
                icon=folium.CustomIcon(
                    "https://i.ibb.co/kvvL870/hydro-dam.png",
                    icon_size=(30, 30)
                ),
                tooltip=row["Reservatório Monitorado"]
            ).add_to(m)

        folium.LayerControl().add_to(m)
        folium_static(m, width=1200)
    else:
        st.warning("Nenhum dado disponível para exibição no mapa com os filtros atuais.")

    # Visualizações adicionais
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🏞️ Média de Vazão")
        st.plotly_chart(
            px.bar(
                df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index(),
                x="Reservatório Monitorado",
                y="Vazão Operada",
                text_auto='.2f',
                color="Reservatório Monitorado",
                color_discrete_sequence=cores
            ).update_layout(showlegend=False),
            use_container_width=True
        )

    with col2:
        st.subheader("📋 Dados Filtrados")
        st.dataframe(
            df_filtrado.sort_values("Data", ascending=False),
            use_container_width=True,
            height=300
        )

else:  # Açudes Monitorados
    st.title("🗺️ Açudes Monitorados")
    
    tile_option = st.sidebar.selectbox(
        "🗺️ Estilo do Mapa",
        ["OpenStreetMap", "Stamen Terrain", "Stamen Toner",
         "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
        key="acudes_map"
    )
    
    m = folium.Map(location=[-5.2, -39.2], zoom_start=7)
    
    if tile_option == "Esri Satellite":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles © Esri",
            name="Satélite"
        ).add_to(m)
    else:
        m = folium.Map(location=[-5.2, -39.2], zoom_start=7, tiles=tile_option)
    
    folium.GeoJson(
        geojson_data["acudes"],
        name="Açudes",
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    folium_static(m, width=1200)
