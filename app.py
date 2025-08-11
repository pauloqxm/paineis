import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from streamlit_folium import folium_static

# ---------------- CONFIGURAÇÃO DE PÁGINA ----------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# ---------------- CABEÇALHO FIXO ----------------
st.markdown("""
    <style>
    .fixed-header {
        top: 0;
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
        <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" alt="Logo COGERH" style="height: 50px;">
        <h2 style="margin: 0; color: #003366;">Operação 2025.2</h2>
    </div>
""", unsafe_allow_html=True)

# ---------------- FUNÇÕES ----------------
def convert_vazao(series, unidade):
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
    df = pd.read_csv(url)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Mês'] = df['Data'].dt.to_period('M').astype(str)
    return df

# ---------------- GEOJSONs ----------------
with open("trechos_perene.geojson", "r", encoding="utf-8") as f:
    geojson_trechos = json.load(f)
with open("Açudes_Monitorados.geojson", "r", encoding="utf-8") as f:
    geojson_acudes = json.load(f)
with open("Sedes_Municipais.geojson", "r", encoding="utf-8") as f:
    geojson_sedes = json.load(f)
with open("c_gestoras.geojson", "r", encoding="utf-8") as f:
    geojson_c_gestoras = json.load(f)
with open("poligno_municipios.geojson", "r", encoding="utf-8") as f:
    geojson_poligno = json.load(f)
with open("bacia_banabuiu.geojson", "r", encoding="utf-8") as f:
    geojson_bacia = json.load(f)
with open("pontos_controle.geojson", "r", encoding="utf-8") as f:
    geojson_pontos = json.load(f)

# ---------------- CARREGAR DADOS ----------------
if 'df' not in st.session_state:
    st.session_state.df = carregar_dados()

if st.button("🔄 Atualizar dados agora", help="Busca os dados mais recentes"):
    with st.spinner('Atualizando dados...'):
        st.session_state.df = carregar_dados()
    st.rerun()

df = st.session_state.df

st.title("💧 Vazões - GRBANABUIU")

# ---------------- FILTROS EM COLUNAS ----------------
col1, col2, col3 = st.columns(3)
with col1:
    estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
with col2:
    meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
with col3:
    unidade_sel = st.selectbox("🧪 Unidade de Vazão", ["L/s", "m³/s"], index=0)

col4, col5 = st.columns(2)
with col4:
    datas_disponiveis = df['Data'].dropna().sort_values()
    data_min = datas_disponiveis.min()
    data_max = datas_disponiveis.max()
    intervalo_data = st.date_input("📅 Intervalo de Datas", (data_min, data_max), format="DD/MM/YYYY")
with col5:
    mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
        "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
        "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
    ], index=0)

# ---------------- FILTRAR DF ----------------
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

# ---------------- GRÁFICO ----------------
st.subheader("📈 Evolução da Vazão Operada por Reservatório")
fig = go.Figure()
cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
reservatorios_filtrados = df_filtrado['Reservatório Monitorado'].unique()

for i, reservatorio in enumerate(reservatorios_filtrados):
    df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values(by="Data")
    df_res = df_res.groupby('Data', as_index=False).last()
    y_vals, unit_suffix = convert_vazao(df_res["Vazão Operada"], unidade_sel)
    cor = cores[i % len(cores)]
    fig.add_trace(go.Scatter(
        x=df_res["Data"], y=y_vals,
        mode="lines+markers", name=reservatorio,
        line=dict(shape='hv', width=2, color=cor),
        marker=dict(size=5),
        hovertemplate=f"<b>{reservatorio}</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
    ))

fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
fig.update_layout(
    xaxis_title="Data",
    yaxis_title=f"Vazão Operada ({'m³/s' if unidade_sel=='m³/s' else 'L/s'})",
    legend_title="Reservatório",
    template="plotly_white",
    margin=dict(l=40, r=20, t=40, b=40)
)
st.plotly_chart(fig, use_container_width=True)

# ---------------- MAPA COM CAMADAS ----------------
st.subheader("🗺️ Mapa dos Reservatórios com Camadas")
df_mapa = df_filtrado.copy()
df_mapa[['lat', 'lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
df_mapa = df_mapa.dropna(subset=['lat', 'lon']).drop_duplicates(subset=['Reservatório Monitorado'])

if not df_mapa.empty:
    center = [df_mapa['lat'].mean(), df_mapa['lon'].mean()]
    tile_urls = {"Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"}
    tile_attr = {"Esri Satellite": "Tiles © Esri — Source: Esri, etc."}
    if mapa_tipo in tile_urls:
        m = folium.Map(location=center, zoom_start=8, tiles=None)
        folium.TileLayer(tiles=tile_urls[mapa_tipo], attr=tile_attr[mapa_tipo], name=mapa_tipo).add_to(m)
    else:
        m = folium.Map(location=center, zoom_start=8, tiles=mapa_tipo)

    # Camadas do mapa
    folium.GeoJson(geojson_bacia, name="Bacia do Banabuiu",
                   tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
                   style_function=lambda x: {"color": "darkblue", "weight": 2}).add_to(m)

    trechos_layer = folium.FeatureGroup(name="Trechos Perenizados", show=False)
    folium.GeoJson(geojson_trechos,
                   tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]),
                   style_function=lambda x: {"color": "darkblue", "weight": 1}).add_to(trechos_layer)
    trechos_layer.add_to(m)

    pontos_layer = folium.FeatureGroup(name="Pontos de Controle", show=False)
    for feature in geojson_pontos["features"]:
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]
        nome_municipio = props.get("Name", "Sem nome")
        folium.Marker(location=[coords[1], coords[0]],
                      icon=folium.CustomIcon("https://i.ibb.co/HfCcFWjb/marker.png", icon_size=(22, 22)),
                      tooltip=nome_municipio).add_to(pontos_layer)
    pontos_layer.add_to(m)

    acudes_layer = folium.FeatureGroup(name="Açudes Monitorados", show=False)
    folium.GeoJson(geojson_acudes,
                   tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]),
                   style_function=lambda x: {"color": "darkgreen", "weight": 2}).add_to(acudes_layer)
    acudes_layer.add_to(m)

    sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
    for feature in geojson_sedes["features"]:
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]
        nome_municipio = props.get("NOME_MUNIC", "Sem nome")
        folium.Marker(location=[coords[1], coords[0]],
                      icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(22, 22)),
                      tooltip=nome_municipio).add_to(sedes_layer)
    sedes_layer.add_to(m)

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
        folium.Marker(location=[coords[1], coords[0]],
                      icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30, 30)),
                      tooltip=nome_gestora,
                      popup=folium.Popup(popup_info, max_width=300)).add_to(gestoras_layer)
    gestoras_layer.add_to(m)

    municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
    folium.GeoJson(geojson_poligno,
                   tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]),
                   style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}).add_to(municipios_layer)
    municipios_layer.add_to(m)

    # Pinos dos Reservatórios
    for _, row in df_mapa.iterrows():
        try:
            val = float(row.get('Vazao_Aloc', float('nan')))
        except Exception:
            val = float('nan')
        val_conv, unit_suf = convert_vazao(pd.Series([val]), unidade_sel)
        val_txt = f"{val_conv.iloc[0]:.3f} {unit_suf}" if pd.notna(val_conv.iloc[0]) else "—"
        data_txt = row['Data'].date() if pd.notna(row['Data']) else "—"
        popup_info = f"<strong>Reservatório:</strong> {row['Reservatório Monitorado']}<br><strong>Data:</strong> {data_txt}<br><strong>Vazão Alocada:</strong> {val_txt}"
        folium.Marker(location=[row["lat"], row["lon"]],
                      popup=folium.Popup(popup_info, max_width=300),
                      icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)),
                      tooltip=row["Reservatório Monitorado"]).add_to(m)

    folium.LayerControl().add_to(m)
    folium_static(m, width=1200)
else:
    st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

# ---------------- BARRA MÉDIA ----------------
st.subheader("🏞️ Média da Vazão Operada por Reservatório")
media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
media_conv, unit_bar = convert_vazao(media_vazao["Vazão Operada"], unidade_sel)
media_vazao["Vazão (conv)"] = media_conv

st.plotly_chart(
    px.bar(media_vazao, x="Reservatório Monitorado", y="Vazão (conv)",
           text_auto='.2s', labels={"Vazão (conv)": f"Média ({unit_bar})"}),
    use_container_width=True
)

# ---------------- TABELA ----------------
st.subheader("📋 Tabela Detalhada")
st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)
