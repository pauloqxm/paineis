import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
import datetime
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

# Carrega os GeoJSONs
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

# Configuração geral da página
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# Cabeçalho fixo
st.markdown(
    """
    <style>
    .fixed-header {
        position: fixed;
        top: 0;
        left: 260px;
        right: 0;
        height: 70px;
        z-index: 1000;
        background-color: #e0f0ff;
        border-bottom: 2px solid #ccc;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 12px;
        padding: 10px 20px;
        box-sizing: border-box;
    }
    .stApp {
        padding-top: 80px;
    }
    @media screen and (max-width: 768px) {
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

# Sidebar com menu e rodapé
with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"],
        icons=["droplet", "map"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

    # Rodapé da sidebar
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            position: relative;
        }
        [data-testid="stSidebarNav"]::after {
            content: "";
            position: absolute;
            bottom: 60px;
            left: 0;
            right: 0;
            margin: auto;
            width: 60px;
            height: 60px;
            background-image: url('https://i.ibb.co/tpQrmPb0/csbh.png');
            background-size: contain;
            background-repeat: no-repeat;
        }
        [data-testid="stSidebarNav"]::before {
            content: "GRBANABUIU";
            position: absolute;
            bottom: 10px;
            left: 0;
            right: 0;
            margin: auto;
            font-size:14px;
            font-weight:bold;
            color:#003366;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Aba 1: Vazões
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

    # Filtros na sidebar
    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        dados = df.dropna(subset=['Data']).sort_values(by='Data')
        intervalo_data = st.date_input("📅 Intervalo de Datas",
                                       (dados['Data'].min(), dados['Data'].max()),
                                       format="DD/MM/YYYY")
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa",
                                 ["OpenStreetMap", "Stamen Terrain", "Stamen Toner",
                                  "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
                                 index=0)

    # Aplicar filtros
    df_f = df.copy()
    if estacoes:
        df_f = df_f[df_f['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_f = df_f[df_f['Mês'].isin(meses)]
    if isinstance(intervalo_data, tuple):
        df_f = df_f[(df_f['Data'] >= pd.to_datetime(intervalo_data[0])) &
                    (df_f['Data'] <= pd.to_datetime(intervalo_data[1]))]

    # Gráfico de evolução
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    fig = go.Figure()
    cores = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b']
    for i, res in enumerate(df_f['Reservatório Monitorado'].unique()):
        df_r = df_f[df_f['Reservatório Monitorado']==res].sort_values('Data')
        df_r['Vazão Suavizada'] = df_r['Vazão Operada'].rolling(window=5,center=True,min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=df_r['Data'], y=df_r['Vazão Suavizada'],
            mode='lines', name=res,
            line=dict(shape='spline', width=2, color=cores[i%len(cores)], smoothing=1.3),
            hovertext=[f"<b>{res}</b><br>Data: {d:%d/%m/%Y}<br>Vazão: {v:.2f} l/s"
                       for d,v in zip(df_r['Data'], df_r['Vazão Operada'])],
            hoverinfo='text'
        ))
    if len(df_f['Reservatório Monitorado'].unique())==1:
        mres = df_f['Vazão Operada'].mean()
        fig.add_hline(y=mres, line_dash="dash", line_color="red",
                      annotation_text=f"Média: {mres:.2f} l/s", annotation_position="top right")
    fig.update_layout(xaxis_title="Data", yaxis_title="Vazão Operada (l/s)",
                      template="simple_white", hovermode="closest",
                      margin=dict(l=40,r=20,t=40,b=40))
    st.plotly_chart(fig, use_container_width=True)

    # Mapa
    st.subheader("🗺️ Mapa dos Reservatórios com Pinos")
    df_m = df_f.dropna(subset=['Coordendas']).copy()
    df_m[['lat','lon']] = df_m['Coordendas'].str.split(',',expand=True).astype(float)
    df_m = df_m.drop_duplicates('Reservatório Monitorado')
    if not df_m.empty:
        center=[df_m['lat'].mean(), df_m['lon'].mean()]
        if mapa_tipo=="Esri Satellite":
            m=folium.Map(location=center,zoom_start=8,tiles=None)
            folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                             attr="© Esri",name=mapa_tipo).add_to(m)
        else:
            m=folium.Map(location=center,zoom_start=8,tiles=mapa_tipo)
        # Camadas...
        folium.GeoJson(geojson_quixera,name="Trecho Perenizado",
                       style_function=lambda x:{"color":"darkblue","weight":2}).add_to(m)
        ac=folium.FeatureGroup(name="Açudes Monitorados",show=False)
        folium.GeoJson(geojson_acudes,style_function=lambda x:{"color":"darkgreen","weight":2}).add_to(ac); ac.add_to(m)
        # Sedes
        sd=folium.FeatureGroup(name="Sedes Municipais",show=False)
        for feat in geojson_sedes['features']:
            coords=feat['geometry']['coordinates']
            folium.Marker(location=[coords[1],coords[0]],
                          icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png",icon_size=(22,22)),
                          tooltip=feat['properties'].get("NOME_MUNIC","")).add_to(sd)
        sd.add_to(m)
        # Gestoras
        gg=folium.FeatureGroup(name="Comissões Gestoras",show=False)
        for feat in geojson_c_gestoras['features']:
            coords=feat['geometry']['coordinates']
            popup=f"<strong>{feat['properties'].get('SISTEMAH3','')}</strong>"
            folium.Marker(location=[coords[1],coords[0]],
                          icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png",icon_size=(30,30)),
                          tooltip=feat['properties'].get('SISTEMAH3',''),popup=popup).add_to(gg)
        gg.add_to(m)
        # Municípios
        mn=folium.FeatureGroup(name="Polígonos Municipais",show=False)
        folium.GeoJson(geojson_poligno,style_function=lambda x:{"fillOpacity":0,"color":"blue","weight":1}).add_to(mn)
        mn.add_to(m)
        # Pinos de reservatórios
        for _,r in df_m.iterrows():
            popup=f"<strong>{r['Reservatório Monitorado']}</strong><br>Vazão: {r['Vazão Operada']:.2f} l/s"
            folium.Marker(location=[r['lat'],r['lon']],
                          icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png",icon_size=(30,30)),
                          popup=popup).add_to(m)
        folium.LayerControl().add_to(m)
        folium_static(m, width=1200)
    else:
        st.info("Nenhum ponto com coordenadas disponíveis.")

    # Média e tabela
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    med = df_f.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
    st.plotly_chart(px.bar(med, x="Reservatório Monitorado", y="Vazão Operada", text_auto='.2f'),
                    use_container_width=True)

    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_f.sort_values("Data", ascending=False), use_container_width=True)

# Aba 2: Açudes Monitorados
elif aba == "🗺️ Açudes Monitorados":
    st.title("🗺️ Açudes Monitorados")

    tile_option = st.sidebar.selectbox("🗺️ Estilo do Mapa (Açudes)",
                                       ["OpenStreetMap","Stamen Terrain","Stamen Toner",
                                        "CartoDB positron","CartoDB dark_matter","Esri Satellite"])
    with open("Açudes_Monitorados.geojson","r",encoding="utf-8") as f:
        data = json.load(f)

    center = [-5.2, -39.2]
    if tile_option=="Esri Satellite":
        m=folium.Map(location=center,zoom_start=7,tiles=None)
        folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                         attr="© Esri",name=tile_option).add_to(m)
    else:
        m=folium.Map(location=center,zoom_start=7,tiles=tile_option)

    folium.GeoJson(data,name="Açudes",tooltip=folium.GeoJsonTooltip(fields=["Name"],aliases=["Açude:"])).add_to(m)
    folium.LayerControl().add_to(m)
    folium_static(m, width=None)
