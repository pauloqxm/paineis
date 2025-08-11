# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

# --------------------------------------------------------------------------------------
# CONFIG + ESTILOS
# --------------------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

st.markdown("""
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
    .fixed-header {
        position: fixed;
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
    .stApp { padding-top: 120px; }
    </style>
    <div class="fixed-header">
        <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" alt="Logo COGERH" style="height: 50px;">
        <h2 style="margin: 0; color: #003366;">Operação 2025.2</h2>
    </div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# LOAD GEOJSONS (robusto)
# --------------------------------------------------------------------------------------
def load_geojson(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"type": "FeatureCollection", "features": []}

geojson_trechos   = load_geojson("trechos_perene.geojson")
geojson_acudes    = load_geojson("Açudes_Monitorados.geojson")
geojson_sedes     = load_geojson("Sedes_Municipais.geojson")
geojson_c_gestoras= load_geojson("c_gestoras.geojson")
geojson_poligno   = load_geojson("poligno_municipios.geojson")
geojson_bacia     = load_geojson("bacia_banabuiu.geojson")
geojson_pontos    = load_geojson("pontos_controle.geojson")

# --------------------------------------------------------------------------------------
# SIDEBAR MENU
# --------------------------------------------------------------------------------------
with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"],
        icons=["droplet", "map"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

# --------------------------------------------------------------------------------------
# FUNÇÕES UTILITÁRIAS
# --------------------------------------------------------------------------------------
def to_float_br(series: pd.Series) -> pd.Series:
    """Converte string com vírgula decimal para float."""
    s = series.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce')

def convert_vazao(values: pd.Series, unidade: str):
    """Converte valores entre L/s e m³/s."""
    if unidade == "L/s":
        return values, "L/s", 1.0
    else:
        return values / 1000.0, "m³/s", 1/1000.0

def parse_latlon(value):
    """Aceita 'lat,lon' ou 'lon,lat'; aplica heurística para CE."""
    if pd.isna(value):
        return np.nan, np.nan
    parts = str(value).split(",")
    if len(parts) != 2:
        return np.nan, np.nan
    try:
        a = float(parts[0].strip().replace(" ", ""))
        b = float(parts[1].strip().replace(" ", ""))
    except ValueError:
        return np.nan, np.nan

    def plausible(lat, lon):
        return -90 <= lat <= 90 and -180 <= lon <= 180

    if plausible(a, b):
        lat, lon = a, b
    elif plausible(b, a):
        lat, lon = b, a
    else:
        return np.nan, np.nan

    # Faixa aproximada para o Nordeste/CE
    if not (-12 <= lat <= 5) or not (-60 <= lon <= -25):
        if (-12 <= lon <= 5) and (-60 <= lat <= -25):
            lat, lon = lon, lat
    return lat, lon

# --------------------------------------------------------------------------------------
# ABA: VAZÕES - GRBANABUIU
# --------------------------------------------------------------------------------------
if aba == "Vazões - GRBANABUIU":

    @st.cache_data
    def load_data():
        url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mês'] = df['Data'].dt.to_period('M').astype(str)
        # padroniza numéricos possíveis
        for col_num in ["Vazão Operada", "Vazao_Aloc"]:
            if col_num in df.columns:
                df[col_num] = to_float_br(df[col_num])
        return df

    df = load_data()

    st.title("💧 Vazões - GRBANABUIU")

    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", sorted(df['Reservatório Monitorado'].dropna().unique()))
        meses = st.multiselect("📆 Mês", sorted(df['Mês'].dropna().unique()))
        datas_disponiveis = df['Data'].dropna().sort_values()
        data_min = datas_disponiveis.min()
        data_max = datas_disponiveis.max()
        intervalo_data = st.date_input("📅 Intervalo de Datas", (data_min, data_max), format="DD/MM/YYYY")

        unidade = st.selectbox("🧪 Unidade de Vazão", ["L/s", "m³/s"], index=0)
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
            "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
            "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
        ], index=0)

    # --- filtro base
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

    # ----------------------------------------------------------------------------------
    # GRÁFICO: Evolução da Vazão Operada por Reservatório (degraus, ffill, unit-aware)
    # ----------------------------------------------------------------------------------
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")

    colf1, colf2, colf3 = st.sidebar.columns([1, 1, 1])
    with colf1:
        freq_label = st.selectbox("⏱️ Frequência", 
                                  ["Original (pontual)", "Diária", "Semanal", "Mensal"], index=0)
    with colf2:
        agg_label = st.selectbox("📊 Agregação", 
                                 ["Último do período", "Média", "Mediana"], index=0)
    with colf3:
        ffill_opt = st.checkbox("↔️ Manter valor até a próxima alteração", value=True)

    base = (df_filtrado
            .loc[:, ["Data", "Reservatório Monitorado", "Vazão Operada"]]
            .dropna(subset=["Data", "Reservatório Monitorado", "Vazão Operada"])
            .sort_values(["Reservatório Monitorado", "Data"])
            .copy())

    if freq_label != "Original (pontual)":
        rule = {"Diária": "D", "Semanal": "W-SUN", "Mensal": "MS"}[freq_label]
        agg_fun = {"Último do período": "last", "Média": "mean", "Mediana": "median"}[agg_label]
        base = (base
                .set_index("Data")
                .groupby("Reservatório Monitorado")
                .resample(rule)
                .agg({"Vazão Operada": agg_fun})
                .reset_index())
    else:
        rule = "D"  # para ffill diário quando habilitado

    if ffill_opt and not base.empty:
        base = (base
                .sort_values(["Reservatório Monitorado", "Data"])
                .groupby("Reservatório Monitorado", as_index=False, group_keys=False)
                .apply(lambda g: g.set_index("Data").asfreq(rule).ffill())
                .reset_index())

    if not base.empty:
        base["Vazão Convertida"], unidade_str, _ = convert_vazao(base["Vazão Operada"], unidade)

    fig = go.Figure()
    reservatorios = base["Reservatório Monitorado"].dropna().unique() if not base.empty else []

    for res in reservatorios:
        g = base[base["Reservatório Monitorado"] == res].dropna(subset=["Vazão Convertida"])
        if g.empty:
            continue
        fig.add_trace(go.Scatter(
            x=g["Data"], y=g["Vazão Convertida"],
            mode="lines+markers",
            name=res,
            line=dict(width=2),
            marker=dict(size=5),
            connectgaps=False,
            line_shape="hv" if ffill_opt else "linear",
            hovertemplate="<b>%{customdata}</b><br>Data: %{x|%d/%m/%Y}<br>Vazão: %{y:.2f} " + unidade_str + "<extra></extra>",
            customdata=np.array([res]*len(g))
        ))

    if len(reservatorios) == 1 and not base.empty:
        media_res = base["Vazão Convertida"].mean()
        fig.add_trace(go.Scatter(
            x=[base["Data"].min(), base["Data"].max()],
            y=[media_res, media_res],
            mode="lines",
            name=f"Média no período: {media_res:.2f} {unidade_str}",
            line=dict(color="red", width=3, dash="dash")
        ))

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title=f"Vazão Operada ({unidade_str if not base.empty else '—'})",
        legend_title="Reservatório",
        template="simple_white",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=40, b=40),
        yaxis=dict(rangemode="tozero", tickformat="~s")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Representação em degraus (hv) para refletir mudanças operacionais discretas. "
        "A opção de manter valor até a próxima alteração preenche dias sem leitura com o último valor."
    )

    # ----------------------------------------------------------------------------------
    # MAPA (detecção de coluna de coordenadas + unidade no popup)
    # ----------------------------------------------------------------------------------
    st.subheader("🗺️ Mapa dos Reservatórios com Pinos")

    coord_col_candidates = ["Coordendas", "Coordenadas", "Coordenada", "Coordenadas (lat,lon)"]
    coord_col = next((c for c in coord_col_candidates if c in df_filtrado.columns), None)

    if coord_col is None:
        st.info("Nenhuma coluna de coordenadas encontrada. Esperado algo como 'Coordenadas' com 'lat,lon'.")
    else:
        df_mapa = df_filtrado.copy()
        latlons = df_mapa[coord_col].apply(parse_latlon)
        df_mapa["lat"] = latlons.apply(lambda x: x[0])
        df_mapa["lon"] = latlons.apply(lambda x: x[1])
        df_mapa = df_mapa.dropna(subset=["lat", "lon"]).drop_duplicates(subset=["Reservatório Monitorado"])

        if "Vazao_Aloc" in df_mapa.columns:
            df_mapa["Vazao_Aloc_Conv"] = convert_vazao(df_mapa["Vazao_Aloc"], unidade)[0]
        else:
            df_mapa["Vazao_Aloc_Conv"] = np.nan

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

            # Camadas auxiliares (bacia, trechos, pontos, etc.)
            folium.GeoJson(
                geojson_bacia, name="Bacia do Banabuiu",
                tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
                style_function=lambda x: {"color": "darkblue", "weight": 2}
            ).add_to(m)

            trechos_layer = folium.FeatureGroup(name="Trechos Perenizados", show=False)
            folium.GeoJson(
                geojson_trechos,
                tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]),
                style_function=lambda x: {"color": "darkblue", "weight": 1}
            ).add_to(trechos_layer)
            trechos_layer.add_to(m)

            pontos_layer = folium.FeatureGroup(name="Pontos de Controle", show=False)
            for feature in geojson_pontos.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [None, None])
                if coords and len(coords) == 2:
                    nome_municipio = props.get("Name", "Sem nome")
                    folium.Marker(
                        location=[coords[1], coords[0]],
                        icon=folium.CustomIcon("https://i.ibb.co/HfCcFWjb/marker.png", icon_size=(22, 22)),
                        tooltip=nome_municipio
                    ).add_to(pontos_layer)
            pontos_layer.add_to(m)

            acudes_layer = folium.FeatureGroup(name="Açudes Monitorados", show=False)
            folium.GeoJson(
                geojson_acudes,
                tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]),
                style_function=lambda x: {"color": "darkgreen", "weight": 2}
            ).add_to(acudes_layer)
            acudes_layer.add_to(m)

            sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
            for feature in geojson_sedes.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [None, None])
                if coords and len(coords) == 2:
                    nome_municipio = props.get("NOME_MUNIC", "Sem nome")
                    folium.Marker(
                        location=[coords[1], coords[0]],
                        icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(22, 22)),
                        tooltip=nome_municipio
                    ).add_to(sedes_layer)
            sedes_layer.add_to(m)

            gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
            for feature in geojson_c_gestoras.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [None, None])
                if coords and len(coords) == 2:
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

            municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
            folium.GeoJson(
                geojson_poligno,
                tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]),
                style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}
            ).add_to(municipios_layer)
            municipios_layer.add_to(m)

            for _, row in df_mapa.iterrows():
                vazao_txt = f"{row['Vazao_Aloc_Conv']:.2f} {unidade}" if not pd.isna(row["Vazao_Aloc_Conv"]) else "—"
                data_txt = row['Data'].date() if pd.notna(row['Data']) else "—"
                popup_info = f"""
<strong>Reservatório:</strong> {row['Reservatório Monitorado']}<br>
<strong>Data:</strong> {data_txt}<br>
<strong>Vazão Alocada:</strong> {vazao_txt}
"""
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=folium.Popup(popup_info, max_width=300),
                    icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)),
                    tooltip=row["Reservatório Monitorado"]
                ).add_to(m)

            folium.LayerControl().add_to(m)
            folium_static(m, width=1200)
        else:
            st.info("Nenhum ponto com coordenadas válidas para plotar no mapa.")

    # ----------------------------------------------------------------------------------
    # BARRA: Média da Vazão por Reservatório (unit-aware)
    # ----------------------------------------------------------------------------------
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    media_vazao = (df_filtrado
                   .dropna(subset=["Reservatório Monitorado", "Vazão Operada"])
                   .groupby("Reservatório Monitorado", as_index=False)["Vazão Operada"]
                   .mean())
    if not media_vazao.empty:
        media_vazao["Vazão Convertida"], unidade_bar, _ = convert_vazao(media_vazao["Vazão Operada"], unidade)
        fig_bar = px.bar(
            media_vazao,
            x="Reservatório Monitorado",
            y="Vazão Convertida",
            text_auto='.2s',
            labels={"Vazão Convertida": f"Média ({unidade_bar})", "Reservatório Monitorado": "Reservatório"}
        )
        fig_bar.update_layout(yaxis=dict(tickformat="~s"))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Sem dados suficientes para calcular a média no filtro atual.")

    # ----------------------------------------------------------------------------------
    # TABELA DETALHADA
    # ----------------------------------------------------------------------------------
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)

# --------------------------------------------------------------------------------------
# ABA: 🗺️ AÇUDES MONITORADOS (visão simples por GeoJSON)
# --------------------------------------------------------------------------------------
elif aba == "🗺️ Açudes Monitorados":
    st.title("🗺️ Açudes Monitorados")

    tile_option = st.sidebar.selectbox("🗺️ Estilo do Mapa (Açudes)", [
        "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
        "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
    ], key="acudes_map_tile")

    center = [-5.2, -39.2]
    tile_urls = {
        "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    }
    tile_attr = {
        "Esri Satellite": "Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, etc."
    }

    if tile_option in tile_urls:
        m = folium.Map(location=center, zoom_start=7, tiles=None)
        folium.TileLayer(tiles=tile_urls[tile_option], attr=tile_attr[tile_option], name=tile_option).add_to(m)
    else:
        m = folium.Map(location=center, zoom_start=7, tiles=tile_option)

    folium.GeoJson(
        geojson_acudes,
        name="Açudes",
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])
    ).add_to(m)

    folium.LayerControl().add_to(m)
    folium_static(m, width=None)
