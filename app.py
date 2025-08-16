
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
import base64
import unicodedata2  # pode ser removido se não usar
import altair as alt  # pode ser removido se não usar
from datetime import datetime, timedelta, timezone
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MiniMap, MousePosition, MeasureControl, MarkerCluster

#==============def render home -> #L126
#==============def render açudes -> #L539
#==============def render_docs -> #L852
#==============def render_dados -> #L953

# ---------------- CONFIG GERAL ----------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# ---------------- ARQUIVOS GEOJSON ----------------
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

# ---------------- TOPO CUSTOM ----------------
fuso_brasilia = timezone(timedelta(hours=-3))
agora = datetime.now(fuso_brasilia)
dias_semana = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
meses = {"January": "janeiro", "February": "fevereiro", "March": "março", "April": "abril", "May": "maio", "June": "junho", "July": "julho", "August": "agosto", "September": "setembro", "October": "outubro", "November": "novembro", "December": "dezembro"}
data_hoje = f"{dias_semana[agora.strftime('%A')]}, {agora.day:02d} de {meses[agora.strftime('%B')]} de {agora.year}"

# ----------------- BARRA FIXA (HEADER) ------------
st.markdown(
    f"""
<style>
[data-testid="stHeader"]{{visibility:hidden;}}
.custom-header{{position:fixed;top:0;left:0;width:100%;
background:linear-gradient(135deg,#228B22 0%,#006400 50%,#004d00 100%);
color:white;padding:8px 5%;font-family:'Segoe UI',Roboto,sans-serif;
box-shadow:0 4px 12px rgba(0,0,0,.1);z-index:9999}}
.header-container{{max-width:1200px;margin: 8px auto;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px}}
.header-brand{{display:flex;align-items:center;gap:10px;flex:1;min-width:200px}}
.header-logo{{height:36px;filter:drop-shadow(0 2px 2px rgba(0,0,0,.2))}}
.header-title{{font-size:clamp(14px,3vw,18px);font-weight:600;letter-spacing:.5px;text-shadow:0 1px 3px rgba(0,0,0,.3)}}
.header-date{{background:rgba(255,255,255,.15);padding:4px 10px;border-radius:20px;font-size:clamp(10px,2.5vw,13px);font-weight:500;display:flex;align-items:center;gap:6px;backdrop-filter:blur(5px);white-space:nowrap}}
.header-links{{display:flex;align-items:center;gap:15px}}
.dropdown{{position:relative;display:inline-block}}
.dropdown-content{{display:none;position:absolute;background-color:#006400;min-width:160px;box-shadow:0 8px 16px rgba(0,0,0,0.2);z-index:1;border-radius:8px;padding:8px 0}}
.dropdown:hover .dropdown-content{{display:block}}
.dropdown-btn{{background:rgba(255,255,255,0.1);border:none;color:white;padding:8px 12px;border-radius:20px;cursor:pointer;display:flex;align-items:center;gap:5px;font-size:13px}}
.dropdown-btn:hover{{background:rgba(255,255,255,0.2)}}
.dropdown-content a{{color:white;padding:8px 16px;text-decoration:none;display:block;font-size:13px}}
.dropdown-content a:hover{{background-color:#004d00}}
.main .block-container{{padding-top:90px}}
.filter-card{{border:1px solid #e6e6e6;border-radius:1px;padding:1px 1px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.06);margin-top:6px}}
.filter-title{{font-weight:600;margin-bottom:6px}}
.quick-chips span{{display:inline-block;border:1px solid #dcdcdc;border-radius:999px;padding:4px 10px;margin-right:6px;margin-top:4px;cursor:pointer;font-size:12px}}
.quick-chips span:hover{{background:#f5f5f5}}
.kpi-card{{border:1px solid #eaeaea;border-radius:14px;padding:14px;background:linear-gradient(180deg,#ffffff 0%, #fafafa 100%);box-shadow:0 6px 16px rgba(0,0,0,.06);text-align:center}}
.kpi-value{{font-size:22px;font-weight:700;margin-top:4px}}
.st-emotion-cache-1q7spjk{{color:#228B22!important;font-weight:bold}}
.st-emotion-cache-1q7spjk:hover{{color:#006400!important}}
.map-style-selector{{margin-top:-10px}}
@media(max-width:600px){{
 .main .block-container{{padding-top:110px}}
 .header-links{{gap:10px}}
 .dropdown-btn{{padding:6px 10px}}
}}
</style>
<div class="custom-header">
  <div class="header-container">
    <div class="header-brand">
      <img src="https://cdn-icons-png.flaticon.com/512/1006/1006363.png" class="header-logo">
      <div>
        <div class="header-title">Acompanhamento da Operação</div>
        <div style="opacity:.9;font-size:13px">📌 Bacia do Banabuiu</div>
      </div>
    </div>
    <div class="header-links">
      <div class="dropdown">
        <button class="dropdown-btn">Sistema<span>▼</span></button>
        <div class="dropdown-content">
          <a href="https://www.srh.ce.gov.br/" target="_blank" rel="noopener">🏢 SRH</a>
          <a href="https://www.sohidra.ce.gov.br/" target="_blank" rel="noopener">💧 COGERH</a>
          <a href="https://www.sohidra.ce.gov.br/" target="_blank" rel="noopener">🚰 SOHIDRA</a>
          <a href="https://www.funceme.br/" target="_blank" rel="noopener">🌦️ FUNCEME</a>
        </div>
      </div>
      <div class="dropdown">
        <button class="dropdown-btn">Comitê<span>▼</span></button>
        <div class="dropdown-content">
          <a href="https://www.cbhbanabuiu.com.br/institucional/" target="_blank" rel="noopener">💼 Institucional</a>
          <a href="https://www.cbhbanabuiu.com.br/institucional/Regimento/" target="_blank" rel="noopener">📃 Regimento</a>
          <a href="https://www.cbhbanabuiu.com.br/institucional/conheca-nossa-bacia-hidrografica/" target="_blank" rel="noopener">💦 A Bacia</a>
        </div>
      </div>
      <div class="header-date">📅 {data_hoje}</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------- UTIL ----------------
def convert_vazao(series, unidade):
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"


@st.cache_data(ttl=300)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
    df = pd.read_csv(url)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    return df


# =========================
# FUNÇÕES DE CADA ABA
# =========================


def render_home():
    # === CONTEÚDO DA ABA 1 (🏠 Página Inicial) ===
    df = carregar_dados()

    # barra de ações
    cA1, cA2, cA3 = st.columns([1, 1, 1])
    with cA1:
        if st.button("🔄 Atualizar agora"):
            carregar_dados.clear()
            df = carregar_dados()
            st.success("Atualizado.")

    st.markdown(
        """
<style>
.custom-title {
    font-family: 'Segoe UI', Roboto, sans-serif !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #006400 !important;
    text-align: center !important;
    margin: 8px 0 10px 0 !important;
    padding: 12px 22px !important;
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    background: rgba(144, 238, 144, 0.15) !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
}
.custom-title::before, .custom-title::after { content: ""; flex: 1; height: 2px; background: linear-gradient(90deg, transparent, #228B22); border-radius: 2px; }
.custom-title::after { background: linear-gradient(90deg, #228B22, transparent); }
.custom-title span { display: inline-flex; align-items: center; justify-content: center; font-size: 18px; }
@media (max-width: 600px) {
    .custom-title { flex-direction: column; gap: 4px; padding: 6px 12px; }
    .custom-title::before, .custom-title::after { width: 70%; height: 1.5px; }
}
</style>
<h1 class="custom-title"><span>💧</span> Painel de Vazões </span></h1>
""",
        unsafe_allow_html=True,
    )

    # ------------- Filtros -------------
    with st.expander("☰ Filtros", expanded=False):
        st.markdown('<div class="filter-card"><div class="filter-title">Opções de Filtro</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            estacoes = st.multiselect("🏞️ Reservatório", df["Reservatório Monitorado"].dropna().unique())
            operacao = st.multiselect("🔧 Operação", df["Operação"].dropna().unique())
        with col2:
            meses = st.multiselect("📆 Mês", df["Mês"].dropna().unique())
        col3, col4 = st.columns(2)
        with col3:
            datas_disponiveis = df["Data"].dropna().sort_values()
            data_min = datas_disponiveis.min()
            data_max = datas_disponiveis.max()
            intervalo_data = st.date_input("📅 Intervalo", (data_min, data_max), format="DD/MM/YYYY")
        with col4:
            unidade_sel = st.selectbox("🧪 Unidade", ["L/s", "m³/s"], index=0)
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------- Filtragem -------------
    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado["Reservatório Monitorado"].isin(estacoes)]
    if operacao:
        df_filtrado = df_filtrado[df_filtrado["Operação"].isin(operacao)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado["Mês"].isin(meses)]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[(df_filtrado["Data"] >= pd.to_datetime(inicio)) & (df_filtrado["Data"] <= pd.to_datetime(fim))]

    # ------------- KPIs -------------
    st.markdown(
        """
    <style>
    .kpi-container { display: flex; gap: 16px; margin: -15px 0; flex-wrap: wrap; justify-content: space-between; }
    .kpi-card { flex: 1; min-width: 180px; background: linear-gradient(135deg, #e0f5ec, #b2dfdb); border-radius: 12px; padding: 16px; box-shadow: 0 3px 8px rgba(0,0,0,0.08); text-align: center; transition: transform .2s, box-shadow .2s; }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.15); }
    .kpi-label { font-size: 14px; font-weight: 600; color: #004d40; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .5px; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #00695c; }
    @media (max-width: 768px) { .kpi-container { flex-direction: column; } }
    </style>
    """,
        unsafe_allow_html=True,
    )

    reservatorios_count = df_filtrado["Reservatório Monitorado"].nunique()
    registros_count = len(df_filtrado)
    ultima_data = df_filtrado["Data"].max().strftime("%d/%m/%Y") if not df_filtrado.empty else "—"
    unidade_show = "m³/s" if unidade_sel == "m³/s" else "L/s"
    st.markdown(
        f"""
    <div class="kpi-container">
        <div class="kpi-card"><div class="kpi-label">Reservatórios</div><div class="kpi-value">{reservatorios_count}</div></div>
        <div class="kpi-card"><div class="kpi-label">Registros</div><div class="kpi-value">{registros_count}</div></div>
        <div class="kpi-card"><div class="kpi-label">Última Data</div><div class="kpi-value">{ultima_data}</div></div>
        <div class="kpi-card"><div class="kpi-label">Unidade</div><div class="kpi-value">{unidade_show}</div></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ======================GRÁFICO SÉRIE TEMPORAL
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    fig = go.Figure()
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
    reservatorios = df_filtrado["Reservatório Monitorado"].dropna().unique()

    for i, r in enumerate(reservatorios):
        dfr = df_filtrado[df_filtrado["Reservatório Monitorado"] == r].sort_values("Data").groupby("Data", as_index=False).last()
        y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
        fig.add_trace(go.Scatter(x=dfr["Data"], y=y_vals, mode="lines+markers", name=r, line=dict(shape="hv", width=2, color=cores[i % len(cores)]), marker=dict(size=5), hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"))
        if len(reservatorios) == 1 and len(dfr) > 1:
            dfr["dias_ativos"] = dfr["Data"].diff().dt.days.fillna(0)
            dfr.loc[dfr.index[-1], "dias_ativos"] = (df_filtrado["Data"].max() - dfr["Data"].iloc[-1]).days + 1
            media_pond = (dfr["Vazão Operada"] * dfr["dias_ativos"]).sum() / dfr["dias_ativos"].sum()
            media_pond_conv, _ = convert_vazao(pd.Series([media_pond]), unidade_sel)
            fig.add_hline(y=media_pond_conv.iloc[0], line_dash="dash", line_width=2, line_color="red", annotation_text=f"Média Ponderada: {media_pond_conv.iloc[0]:.2f} {unit_suffix}", annotation_position="top right")

    # Configurações de layout atualizadas
    fig.update_layout(xaxis_title="Data", yaxis_title=f"Vazão Operada ({'m³/s' if unidade_sel=='m³/s' else 'L/s'})", legend_title="Reservatório", template="plotly_white", margin=dict(l=40, r=20, t=10, b=40), height=600, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), xaxis=dict(rangeslider=dict(visible=True, thickness=0.1, bgcolor="#f5f5f5", bordercolor="#cccccc", borderwidth=1)))  # Aumenta a altura do gráfico  # Legenda horizontal  # Ancora na parte inferior  # Posição abaixo do gráfico  # Centraliza horizontalmente  # Posição central

    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    # ------------- Abas de gráficos agregados -------------
    gtab1, gtab2 = st.tabs(["📊 Média mensal", "📦 Distribuição (boxplot)"])
    with gtab1:
        if not df_filtrado.empty:
            dmm = df_filtrado.assign(mes_num=df_filtrado["Data"].dt.to_period("M").astype(str)).groupby(["Reservatório Monitorado", "mes_num"], as_index=False)["Vazão Operada"].mean()
            yconv, sufx = convert_vazao(dmm["Vazão Operada"], unidade_sel)
            dmm["Vazão (conv)"] = yconv
            figm = px.bar(dmm, x="mes_num", y="Vazão (conv)", color="Reservatório Monitorado", labels={"mes_num": "Mês", "Vazão (conv)": f"Média ({sufx})"}, barmode="group")
            st.plotly_chart(figm, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sem dados para média mensal.")

    # ======================MENU
    with gtab2:
        if not df_filtrado.empty and df_filtrado["Reservatório Monitorado"].nunique() > 0:
            # Sempre calcule volume em m³ (independente da unidade exibida no app)
            # A coluna 'Vazão Operada' está originalmente em L/s, então dividimos por 1000 para obter m³/s.
            df_box = df_filtrado.copy()

            volumes = []
            for reservatorio in df_box["Reservatório Monitorado"].unique():
                df_res = df_box[df_box["Reservatório Monitorado"] == reservatorio].sort_values("Data").copy()

                # Dias entre medições no próprio reservatório
                df_res["dias_entre_medicoes"] = df_res["Data"].diff().dt.days.fillna(0)

                # Garante que a última medição cubra até o fim do período filtrado
                ultima_data_res = df_res["Data"].iloc[-1]
                fim_periodo = df_box["Data"].max() if pd.notna(df_box["Data"].max()) else ultima_data_res
                df_res.loc[df_res.index[-1], "dias_entre_medicoes"] = (fim_periodo - ultima_data_res).days + 1

                # Fluxo base em m³/s (origem L/s)
                vazao_m3s = df_res["Vazão Operada"] / 1000.0

                # Volume acumulado em m³ no período (m³/s * s)
                segundos_por_dia = 86400
                df_res["volume_periodo_m3"] = vazao_m3s * segundos_por_dia * df_res["dias_entre_medicoes"]
                volume_total_m3 = df_res["volume_periodo_m3"].sum()

                volumes.append({"Reservatório Monitorado": reservatorio, "Volume Acumulado (m³)": volume_total_m3})

            df_volumes = pd.DataFrame(volumes)

            # --------- Formatação condicional em 3 níveis ----------
            def fmt_m3(x):
                if pd.isna(x):
                    return "—"
                if x >= 1_000_000:
                    return f"{x/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " milhões m³"
                elif x >= 1_000:
                    return f"{x/1e3:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mil m³"
                else:
                    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m³"

            df_volumes["Volume Formatado"] = df_volumes["Volume Acumulado (m³)"].apply(fmt_m3)

            # Escala do gráfico sempre em "milhões m³" para uniformidade
            df_volumes["Volume Eixo Y"] = df_volumes["Volume Acumulado (m³)"] / 1e6
            y_max = float(df_volumes["Volume Eixo Y"].max()) if not df_volumes.empty else 0.0
            y_max = y_max * 1.1 if y_max > 0 else 1.0  # evita domínio [0,0]

            y_title = "Volume Acumulado (milhões m³)"

            # --------- Gráfico (emoji 💧 dimensionado pelo volume) ----------
            chart = alt.Chart(df_volumes).mark_text(align="center", baseline="bottom", dy=10).encode(x=alt.X("Reservatório Monitorado:N", title="Reservatório"), y=alt.Y("Volume Eixo Y:Q", title=y_title, scale=alt.Scale(domain=[0, y_max])), text=alt.value("💧"), size=alt.Size("Volume Eixo Y:Q", scale=alt.Scale(range=[10, 300]), legend=None), color=alt.value("steelblue"), tooltip=[alt.Tooltip("Reservatório Monitorado:N", title="Reservatório"), alt.Tooltip("Volume Formatado:N", title="Volume Total")]).properties(title="Volume Acumulado por Reservatório", height=600).interactive()

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Sem dados suficientes para o gráfico de volume.")

    # ------------- Mapa com camadas -------------
    st.subheader("🗺️ Mapa dos Reservatórios com Camadas")
    df_mapa = df_filtrado.copy()
    # aceita 'Coordenadas' (correta) e 'Coordendas' (caso esteja assim na planilha)
    coord_col = "Coordenadas" if "Coordenadas" in df_mapa.columns else ("Coordendas" if "Coordendas" in df_mapa.columns else None)
    if coord_col:
        try:
            df_mapa[["lat", "lon"]] = df_mapa[coord_col].str.split(",", expand=True).astype(float)
        except Exception:
            # tentativas de normalização: tira espaços
            df_mapa[["lat", "lon"]] = df_mapa[coord_col].str.replace(" ", "").str.split(",", expand=True).astype(float)
    df_mapa = df_mapa.dropna(subset=["lat", "lon"]).drop_duplicates(subset=["Reservatório Monitorado"])

    with st.expander("☰ Estilo do Mapa", expanded=False):
        mapa_tipo = st.selectbox("Selecione o estilo:", ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"], index=0, key="map_style_selector", label_visibility="collapsed")

    tile_urls = {"OpenStreetMap": None, "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png", "Stamen Toner": "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png", "CartoDB positron": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", "CartoDB dark_matter": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"}
    tile_attr = {"OpenStreetMap": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>', "Stamen Terrain": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under CC BY 3.0. Data by OpenStreetMap, under ODbL.', "Stamen Toner": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under CC BY 3.0. Data by OpenStreetMap, under ODbL.', "CartoDB positron": '&copy; <a href="https://carto.com/attributions">CARTO</a>', "CartoDB dark_matter": '&copy; <a href="https://carto.com/attributions">CARTO</a>', "Esri Satellite": "Tiles &copy; Esri — Sources: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, GIS User Community"}

    if not df_mapa.empty:
        center = [df_mapa["lat"].mean(), df_mapa["lon"].mean()]
        m = folium.Map(location=center, zoom_start=8, tiles=None)
        if mapa_tipo == "OpenStreetMap":
            folium.TileLayer(tiles="OpenStreetMap").add_to(m)
        else:
            folium.TileLayer(tiles=tile_urls[mapa_tipo], attr=tile_attr[mapa_tipo], name=mapa_tipo).add_to(m)

        Fullscreen(position="topleft").add_to(m)
        MiniMap(toggle_display=True, minimized=True).add_to(m)
        MousePosition(position="bottomleft", separator=" | ", prefix="Coords").add_to(m)
        MeasureControl(primary_length_unit="meters").add_to(m)

        folium.GeoJson(geojson_bacia, name="Bacia do Banabuiu", tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]), style_function=lambda x: {"color": "darkblue", "weight": 2}).add_to(m)

        trechos_layer = folium.FeatureGroup(name="Trechos Perenizados", show=False)
        folium.GeoJson(geojson_trechos, tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]), style_function=lambda x: {"color": "darkblue", "weight": 1}).add_to(trechos_layer)
        trechos_layer.add_to(m)

        pontos_layer = folium.FeatureGroup(name="Pontos de Controle", show=False)
        for feature in geojson_pontos["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            nome_municipio = props.get("Name", "Sem nome")
            folium.Marker([coords[1], coords[0]], icon=folium.CustomIcon("https://i.ibb.co/HfCcFWjb/marker.png", icon_size=(22, 22)), tooltip=nome_municipio).add_to(pontos_layer)
        pontos_layer.add_to(m)

        acudes_layer = folium.FeatureGroup(name="Açudes Monitorados", show=False)
        folium.GeoJson(geojson_acudes, tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]), style_function=lambda x: {"color": "darkgreen", "weight": 2}).add_to(acudes_layer)
        acudes_layer.add_to(m)

        sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
        for feature in geojson_sedes["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            nome = props.get("NOME_MUNIC", "Sem nome")
            folium.Marker([coords[1], coords[0]], icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(22, 22)), tooltip=nome).add_to(sedes_layer)
        sedes_layer.add_to(m)

        gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
        for feature in geojson_c_gestoras["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            nome_g = props.get("SISTEMAH3", "Sem nome")
            popup_info = f"""
<div style='font-family: "Segoe UI", Arial, sans-serif; padding: 12px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-top: 4px solid #228B22; min-width: 200px;'>
  <div style='font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;'>{nome_g}</div>
  <div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Ano de Formação</div><div style='color: #2c3e50;'>{props.get("ANOFORMA1","N/A")}</div></div>
  <div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Sistema</div><div style='color: #2c3e50;'>{props.get("SISTEMAH3","N/A")}</div></div>
  <div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Município</div><div style='color: #228B22; font-weight: 500;'>{props.get("MUNICIPI6","N/A")}</div></div>
</div>
"""
            folium.Marker([coords[1], coords[0]], icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30, 30)), tooltip=nome_g, popup=folium.Popup(popup_info, max_width=300)).add_to(gestoras_layer)
        gestoras_layer.add_to(m)

        municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
        folium.GeoJson(geojson_poligno, tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]), style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}).add_to(municipios_layer)
        municipios_layer.add_to(m)

        cluster = MarkerCluster(name="Reservatórios (pinos)").add_to(m)
        for _, row in df_mapa.iterrows():
            try:
                val = float(row.get("Vazao_Aloc", float("nan")))
            except Exception:
                val = float("nan")
            val_conv, unit_suf = convert_vazao(pd.Series([val]), unidade_show)  # usa unidade atual
            val_num = val_conv.iloc[0] if not pd.isna(val_conv.iloc[0]) else None
            val_txt = f"{val_num:.3f} {unit_suf}" if val_num is not None else "—"
            data_txt = row["Data"].date() if pd.notna(row["Data"]) else "—"
            popup_info = f"""
<div style='font-family: "Segoe UI", Arial, sans-serif; padding: 12px; background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-left: 4px solid #228B22; min-width: 220px;'>
  <div style='font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px; border-bottom: 1px solid #dfe6e9; padding-bottom: 6px;'>
    {row['Reservatório Monitorado']}
  </div>
  <div style='margin-bottom: 4px;'><span style='display:inline-block;width:100px;font-weight:500;color:#7f8c8d;'>Data:</span><span style='color:#2c3e50;'>{data_txt}</span></div>
  <div style='margin-bottom: 4px;'><span style='display:inline-block;width:100px;font-weight:500;color:#7f8c8d;'>Vazão:</span><span style='color:#228B22;font-weight:600;'>{val_txt}</span></div>
  <div style='margin-top: 8px; font-size: 12px; color: #7f8c8d; text-align: right;'>Sistema de Monitoramento</div>
</div>
"""
            folium.Marker([row["lat"], row["lon"]], popup=folium.Popup(popup_info, max_width=300), icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)), tooltip=row["Reservatório Monitorado"]).add_to(cluster)

        folium.LayerControl(collapsed=True, position="topright").add_to(m)
        folium_static(m, width=1200)
    else:
        st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

    # ------------- Média por reservatório -------------
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    if not df_filtrado.empty:
        media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
        media_conv, unit_bar = convert_vazao(media_vazao["Vazão Operada"], unidade_sel)
        media_vazao["Vazão (conv)"] = media_conv
        st.plotly_chart(px.bar(media_vazao, x="Reservatório Monitorado", y="Vazão (conv)", text_auto=".2s", labels={"Vazão (conv)": f"Média ({unit_bar})"}), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Sem dados para a média.")

    # ------------- Tabela -------------
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)

# === CONTEÚDO DA ABA 2 (🗺️ Açudes Monitorados) ===
def render_acudes():
    st.title("🗺️ Açudes Monitorados")
    st.markdown(
        """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Visualização dos açudes monitorados na bacia do Banabuiú<br>
    • Filtros interativos para análise dos dados<br>
    • Tabela detalhada com informações técnicas
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    @st.cache_data(ttl=3600)
    def load_reservatorios_data():
        try:
            url = "https://docs.google.com/spreadsheets/d/1zZ0RCyYj-AzA_dhWzxRziDWjgforbaH7WIoSEd2EKdk/export?format=csv"
            df = pd.read_csv(url)

            # Normalizações de tipo
            if {"Latitude", "Longitude"} <= set(df.columns):
                df["Latitude"] = pd.to_numeric(
                    df["Latitude"].astype(str).str.replace(",", "."), errors="coerce"
                )
                df["Longitude"] = pd.to_numeric(
                    df["Longitude"].astype(str).str.replace(",", "."), errors="coerce"
                )
                df = df.dropna(subset=["Latitude", "Longitude"])
            else:
                st.error("Colunas 'Latitude' e 'Longitude' são necessárias")
                return pd.DataFrame()

            if "Data de Coleta" in df.columns:
                df["Data de Coleta"] = pd.to_datetime(
                    df["Data de Coleta"], errors="coerce", dayfirst=True
                )
                df = df.dropna(subset=["Data de Coleta"])

            # Converter numéricos
            converters = {
                "Percentual": lambda s: pd.to_numeric(
                    s.astype(str).str.replace(",", ".").str.replace("%", "").str.strip(),
                    errors="coerce",
                ),
                "Volume": lambda s: pd.to_numeric(
                    s.astype(str).str.replace(",", ".").str.strip(), errors="coerce"
                ),
                "Cota Sangria": lambda s: pd.to_numeric(
                    s.astype(str).str.replace(",", ".").str.strip(), errors="coerce"
                ),
                "Nivel": lambda s: pd.to_numeric(
                    s.astype(str).str.replace(",", ".").str.strip(), errors="coerce"
                ),
            }
            for col, conv in converters.items():
                if col in df.columns:
                    df[col] = conv(df[col])

            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return pd.DataFrame()

    df_full = load_reservatorios_data()
    if df_full.empty:
        st.warning("Não foi possível carregar os dados dos reservatórios.")
        st.stop()

    # --- Filtros ---
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            min_date = df_full["Data de Coleta"].min().date()
            max_date = df_full["Data de Coleta"].max().date()
            date_range = st.date_input(
                "Período:", value=(max_date, max_date),
                min_value=min_date, max_value=max_date
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
            else:
                st.warning("Selecione um intervalo válido")
                st.stop()

        with col2:
            reservatorios = sorted(df_full["Reservatório"].dropna().astype(str).unique())
            reservatorio_filtro = st.multiselect(
                "Reservatório(s):", options=reservatorios,
                default=reservatorios, placeholder="Selecione..."
            )

        with col3:
            municipios = ["Todos"] + sorted(
                df_full["Município"].dropna().astype(str).unique().tolist()
            )
            municipio_filtro = st.selectbox("Município:", options=municipios, index=0)

        # Slider Percentual à prova de NaN/série vazia
        if "Percentual" in df_full.columns:
            perc_series = df_full["Percentual"].dropna()
            if not perc_series.empty:
                min_perc = float(perc_series.min())
                max_perc = float(perc_series.max())
            else:
                min_perc, max_perc = 0.0, 100.0
        else:
            min_perc, max_perc = 0.0, 100.0

        perc_range = st.slider(
            "Percentual de Volume (%):",
            min_value=float(min_perc),
            max_value=float(max_perc),
            value=(float(min_perc), float(max_perc)),
            step=0.1,
        )

    # --- Aplicar filtros ---
    if not reservatorio_filtro:
        reservatorio_filtro = reservatorios  # tudo

    mask = (
        (df_full["Data de Coleta"].dt.date >= start_date) &
        (df_full["Data de Coleta"].dt.date <= end_date) &
        (df_full["Reservatório"].astype(str).isin(reservatorio_filtro)) &
        (df_full["Percentual"].between(perc_range[0], perc_range[1], inclusive="both"))
    )
    df_filtrado = df_full.loc[mask].copy()

    if municipio_filtro != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["Município"].astype(str) == municipio_filtro
        ].copy()

    # Última medição por reservatório para o mapa
    df_mapa = (
        df_filtrado.sort_values("Data de Coleta", ascending=False)
                   .drop_duplicates(subset=["Reservatório"])
                   .copy()
    )

    # ===================== Mapa Interativo =====================
    st.subheader("🌍 Mapa dos Açudes")
    with st.expander("Configurações do Mapa", expanded=False):
        tile_option = st.selectbox(
            "Estilo do Mapa:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner",
             "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0
        )

    tile_config = {
        "OpenStreetMap": {
            "tiles": "OpenStreetMap",
            "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        },
        "Stamen Terrain": {
            "tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
            "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
        },
        "CartoDB positron": {
            "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
            "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        },
        "CartoDB dark_matter": {
            "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
            "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        },
        "Esri Satellite": {
            "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "attr": "Tiles &copy; Esri — Source: Esri",
        },
        "Stamen Toner": {
            "tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
            "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
        },
    }

    def get_marker_color(percentual):
        if pd.isna(percentual) or 0 <= percentual <= 10:
            return "#808080"
        if 10.1 <= percentual <= 30:
            return "#FF0000"
        if 30.1 <= percentual <= 50:
            return "#FFFF00"
        if 50.1 <= percentual <= 70:
            return "#008000"
        if 70.1 <= percentual <= 100:
            return "#0000FF"
        return "#800080"

    def create_svg_icon(color, size=15):
        svg = (
            f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<polygon points="50,0 100,100 0,100" fill="{color}" '
            f'stroke="#000000" stroke-width="5"/></svg>'
        )
        svg_b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{svg_b64}"

    if not df_filtrado.empty:
        mapa_center = [df_mapa["Latitude"].mean(), df_mapa["Longitude"].mean()]
        m = folium.Map(location=mapa_center, zoom_start=9, tiles=None)
        folium.TileLayer(
            tiles=tile_config[tile_option]["tiles"],
            attr=tile_config[tile_option]["attr"],
            name=tile_option,
        ).add_to(m)

        # Bacia (se disponível)
        try:
            folium.GeoJson(
                geojson_bacia,
                name="Bacia do Banabuiú",
                style_function=lambda x: {"color": "blue", "weight": 2, "fillOpacity": 0.1},
                tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
            ).add_to(m)
        except NameError:
            st.warning("Camada da bacia não adicionada (geojson_bacia não encontrado).")

        # Comissões Gestoras
        gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
        try:
            for feature in geojson_c_gestoras["features"]:
                props = feature["properties"]
                lon, lat = feature["geometry"]["coordinates"]
                nome_g = props.get("SISTEMAH3", "Sem nome")

                popup_info = (
                    "<div style='font-family: \"Segoe UI\", Arial, sans-serif; padding: 12px; "
                    "background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); "
                    "border-top: 4px solid #228B22; min-width: 200px;'>"
                    f"<div style='font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;'>{nome_g}</div>"
                    f"<div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Ano de Formação</div>"
                    f"<div style='color: #2c3e50;'>{props.get('ANOFORMA1','N/A')}</div></div>"
                    f"<div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Sistema</div>"
                    f"<div style='color: #2c3e50;'>{props.get('SISTEMAH3','N/A')}</div></div>"
                    f"<div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Município</div>"
                    f"<div style='color: #228B22; font-weight: 500;'>{props.get('MUNICIPI6','N/A')}</div></div>"
                    "</div>"
                )

                folium.Marker(
                    [lat, lon],
                    icon=folium.CustomIcon(
                        "https://cdn-icons-png.flaticon.com/512/4144/4144517.png",
                        icon_size=(30, 30),
                    ),
                    tooltip=nome_g,
                    popup=folium.Popup(popup_info, max_width=300),
                ).add_to(gestoras_layer)
            gestoras_layer.add_to(m)
        except NameError:
            st.warning("Camada de comissões gestoras não adicionada (geojson_c_gestoras não encontrado).")

        # Municípios (se disponível)
        municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
        try:
            folium.GeoJson(
                geojson_poligno,
                tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]),
                style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1},
            ).add_to(municipios_layer)
            municipios_layer.add_to(m)
        except NameError:
            st.warning("Camada de municípios não adicionada (geojson_poligno não encontrado).")

        # Marcadores dos reservatórios
        for _, row in df_mapa.iterrows():
            try:
                percentual_val = float(row["Percentual"])
                percentual_str = f"{percentual_val:.2f}%"
            except (ValueError, TypeError):
                percentual_val, percentual_str = None, "N/A"

            try:
                volume_str = (
                    f"{float(row['Volume']):,.2f} hm³"
                    .replace(",", "X").replace(".", ",").replace("X", ".")
                )
            except (ValueError, TypeError):
                volume_str = "N/A"

            try:
                cota_sangria_str = (
                    f"{float(row['Cota Sangria']):,.2f}"
                    .replace(",", "X").replace(".", ",").replace("X", ".")
                )
            except (ValueError, TypeError):
                cota_sangria_str = "N/A"

            ultima_data = df_filtrado[
                df_filtrado["Reservatório"] == row["Reservatório"]
            ]["Data de Coleta"].max()
            data_formatada = ultima_data.strftime("%d/%m/%Y") if pd.notnull(ultima_data) else "N/A"
            icon_color = get_marker_color(percentual_val)

            popup_content = (
                '<link rel="stylesheet" '
                'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">'
                f"<div style='font-family: \"Segoe UI\", sans-serif; width: 280px; "
                f"background: linear-gradient(to bottom, #f9f9f9, #ffffff); border-radius: 8px; "
                f"border-left: 5px solid {icon_color}; padding: 12px; "
                f"box-shadow: 0 3px 10px rgba(0,0,0,0.2);'>"
                f"<div style='color: #006400; font-size: 18px; font-weight: 700; margin-bottom: 10px; "
                f"border-bottom: 1px solid #e0e0e0; padding-bottom: 8px;'>"
                f"<i class='fas fa-water' style='margin-right: 8px;'></i>{row['Reservatório']}</div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; "
                f"font-weight: 600; color: #555;'><i class='fas fa-calendar-alt' style='margin-right: 5px;'></i>Data:</span>"
                f"<span style='color: #333;'>{data_formatada}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; "
                f"font-weight: 600; color: #555;'><i class='fas fa-city' style='margin-right: 5px;'></i>Município:</span>"
                f"<span style='color: #333;'>{row.get('Município', 'N/A')}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; "
                f"font-weight: 600; color: #555;'><i class='fas fa-chart-bar' style='margin-right: 5px;'></i>Volume:</span>"
                f"<span style='color: #1a5276; font-weight: 500;'>{volume_str}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; "
                f"font-weight: 600; color: #555;'><i class='fas fa-percentage' style='margin-right: 5px;'></i>Percentual:</span>"
                f"<span style='color: #27ae60; font-weight: 600;'>{percentual_str}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; "
                f"font-weight: 600; color: #555;'><i class='fas fa-ruler' style='margin-right: 5px;'></i>Cota Sangria:</span>"
                f"<span style='color: #7d3c98; font-weight: 500;'>{cota_sangria_str} m</span></div>"
                "</div>"
            )

            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.CustomIcon(create_svg_icon(icon_color), icon_size=(15, 15), icon_anchor=(7, 7)),
                tooltip=f"{row['Reservatório']} - {data_formatada}",
            ).add_to(m)

        folium.LayerControl().add_to(m)
        Fullscreen(position="topleft").add_to(m)
        MousePosition(position="bottomleft").add_to(m)
        folium_static(m, width=1200)
    else:
        st.warning("Não há reservatórios com os filtros aplicados.")

# ===================== Tabela Interativa =====================
    st.subheader("📊 Dados Detalhados Interativos")
    if not df_filtrado.empty:
        faixas_percentual = [(0, 10, "#808080", "Muito Crítica"), (10.1, 30, "#FF0000", "Crítica"), (30.1, 50, "#FFFF00", "Alerta"), (50.1, 70, "#008000", "Confortável"), (70.1, 100, "#0000FF", "Muito Confortável"), (100.1, float("inf"), "#800080", "Vertendo")]

        def get_status_color(percentual):
            if pd.isna(percentual):
                return "#FFFFFF", "N/A", "#000000"
            for min_val, max_val, color, status in faixas_percentual:
                if min_val <= percentual <= max_val:
                    text_color = "#FFFFFF" if color in ["#808080", "#FF0000", "#0000FF", "#800080"] else "#000000"
                    return color, status, text_color
            return "#FFFFFF", "Não classificado", "#000000"

        df_filtrado[["Cor", "Status", "TextColor"]] = df_filtrado["Percentual"].apply(lambda x: pd.Series(get_status_color(x)))
        df_filtrado["Sangria"] = df_filtrado["Cota Sangria"] - df_filtrado["Nivel"]

        colunas_exibir = ["Data de Coleta", "Reservatório", "Município", "Volume", "Percentual", "Status", "Cota Sangria", "Nivel", "Sangria"]

        def colorize_row(row):
            idx = row.name
            bg_color = df_filtrado.loc[idx, "Cor"]
            text_color = df_filtrado.loc[idx, "TextColor"]
            return [f"background-color: {bg_color}; color: {text_color}; font-weight: bold;" for _ in row]

        styled_df = df_filtrado[colunas_exibir].copy().style.apply(colorize_row, axis=1)

        column_config = {"Percentual": st.column_config.ProgressColumn("Percentual", format="%.1f%%", min_value=0, max_value=100), "Volume": st.column_config.NumberColumn("Volume", format="%.2f hm³"), "Cota Sangria": st.column_config.NumberColumn("Cota Sangria", format="%.2f m"), "Nivel": st.column_config.NumberColumn("Nível", format="%.2f m"), "Sangria": st.column_config.NumberColumn("Margem de Sangria", format="%.2f m"), "Status": st.column_config.TextColumn("Status"), "Data de Coleta": st.column_config.DateColumn("Data de Coleta", format="DD/MM/YYYY")}

        st.dataframe(styled_df, column_config=column_config, use_container_width=True, hide_index=True, height=600, column_order=colunas_exibir)

        st.markdown(
            """
        <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 1px solid #ddd;">
          <h4 style="margin-bottom: 12px; color: #333; font-size: 16px;">Legenda de Status:</h4>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
        """
            + "\n".join(
                [
                    f"""<div style="display: flex; align-items: center; padding: 4px;">
                    <div style="width: 24px; height: 24px; background: {color}; margin-right: 10px; border: 1px solid #ccc; border-radius: 4px;"></div>
                    <span style="font-size: 14px;">{status} ({'≥' if min_val == 100.1 else ''}{min_val}-{'' if max_val == float('inf') else max_val}%)</span>
                </div>"""
                    for min_val, max_val, color, status in faixas_percentual
                ]
            )
            + "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.subheader("📈 Volume dos Reservatórios ao Longo do Tempo")
        df_reservatorio = df_filtrado[df_filtrado["Reservatório"].isin(reservatorio_filtro)].sort_values("Data de Coleta")
        if not df_reservatorio.empty:
            df_reservatorio["Data de Coleta"] = df_reservatorio["Data de Coleta"].dt.date
            df_plot = df_reservatorio.pivot_table(index="Data de Coleta", columns="Reservatório", values="Volume", aggfunc="mean")
            st.line_chart(df_plot)
        else:
            st.warning("Não há dados de volume para o(s) reservatório(s) selecionado(s) no período.")

        st.markdown("---")
        with st.expander("📥 Opções de Download", expanded=False):
            st.download_button(label="Baixar dados completos (CSV)", data=df_filtrado.drop(columns=["Cor", "Status", "TextColor"]).to_csv(index=False, encoding="utf-8-sig", sep=";"), file_name=f"reservatorios_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.", icon="⚠️")


# === CONTEÚDO DA ABA 3 (📜 Documentos Oficiais) ===
def render_docs():

    st.title("📜 Documentos para Download")

    SHEET_ID = "1-Tn_ZDHH-mNgJAY1WtjWd_Pyd2f5kv_ZU8dhL0caGDI"
    GID = "0"
    URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

    st.markdown(
        """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Atas e apresentações das reuniões da Bacia do Banabuiú<br>
    • Organizadas por operação, reservatório e parâmetros<br>
    • Dados de vazão média aprovados
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    @st.cache_data(ttl=3600)
    def load_data():
        try:
            df = pd.read_csv(URL, encoding="utf-8-sig").dropna(how="all")
            for col in ["Operação", "Data da Reunião", "Reservatório/Sistema", "Local da Reunião", "Parâmetros aprovados", "Vazão média"]:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()

    df = load_data()

    with st.container():
        st.markdown("**Filtrar documentos**")
        col1, col2 = st.columns(2)
        with col1:
            ops = ["Todos"] + sorted(df["Operação"].unique()) if "Operação" in df.columns else ["Todos"]
            filtro_operacao = st.selectbox("Operação", ops, index=0)
        with col2:
            datas = ["Todos"] + sorted(df["Data da Reunião"].unique()) if "Data da Reunião" in df.columns else ["Todos"]
            filtro_data = st.selectbox("Data da Reunião", datas, index=0)
        busca = st.text_input("Buscar em todos os campos", "")

    df_filtrado = df.copy()
    if filtro_operacao != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Operação"] == filtro_operacao]
    if filtro_data != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Data da Reunião"] == filtro_data]
    if busca:
        busca_lower = busca.lower().strip()
        mask = df_filtrado.apply(lambda row: any(busca_lower in str(val).lower() for val in row.values), axis=1)
        df_filtrado = df_filtrado[mask]

    st.markdown(f"**{len(df_filtrado)} registros encontrados**")

    table_style = """
    <style>
    .table-container { overflow: auto; margin: 1rem 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: center; }
    th { background-color: #f8f9fa; position: sticky; top: 0; }
    .download-btn { display: inline-block; padding: 4px 10px; background: #28a745; color: white !important; border-radius: 4px; text-decoration: none; font-size: 13px; }
    .no-data { color: #6c757d; font-style: italic; padding: 1rem; }
    </style>
    """

    table_html = f"""{table_style}
    <div class="table-container"><table>
      <thead><tr>
        <th>Operação</th><th>Reservatório</th><th>Data</th><th>Local</th>
        <th>Parâmetros</th><th>Vazão</th><th>Apresentação</th><th>Ata</th>
      </tr></thead><tbody>"""

    if not df_filtrado.empty:
        for _, row in df_filtrado.iterrows():
            cells = [row.get("Operação", ""), row.get("Reservatório/Sistema", ""), row.get("Data da Reunião", ""), row.get("Local da Reunião", ""), row.get("Parâmetros aprovados", ""), row.get("Vazão média", ""), row.get("Apresentação", ""), row.get("Ata da Reunião", "")]
            for i in [6, 7]:
                if not cells[i] or str(cells[i]).lower() in ["nan", "none", ""]:
                    cells[i] = "—"
                else:
                    cells[i] = f'<a class="download-btn" href="{cells[i]}" target="_blank">Baixar</a>'
            table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"
    else:
        table_html += '<tr><td colspan="8" class="no-data">Nenhum registro encontrado</td></tr>'

    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)


def render_dados():
    st.title("📈 Simulações")

    st.markdown("""
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Linha comparativa de <b>Cota Inicial (m)</b> e <b>Cota Dia (m)</b><br>
    • Filtros por <b>Data</b> e <b>Açude</b><br>
    • Linha de <b>Volume (m³)</b> ao longo do tempo
  </p>
</div>
""", unsafe_allow_html=True)

    # --- Carregamento
    sheet_url = "https://docs.google.com/spreadsheets/d/1C40uaNmLUeu-k_FGEPZOgF8FwpSU00C9PtQu8Co4AUI/export?format=csv"
    try:
        df = pd.read_csv(sheet_url, sep=',', decimal=',')
    except Exception as e:
        st.error(f"Não foi possível ler a planilha: {e}")
        return

    colunas = ["Data", "Açude", "Município", "Região Hidrográfica", "Cota Inicial (m)", "Cota Dia (m)", "Volume (m³)",
               "Volume (%)", "Evapor. Parcial (mm)", "Cota Interm. (m)", "Volume Interm. (m³)",
               "Liberação (m³/s)", "Liberação (m³)", "Volume Final (m³)", "Cota Final (m)", "Coordendas"]
    faltantes = [c for c in colunas if c not in df.columns]
    if faltantes:
        st.error(f"As seguintes colunas não foram encontradas na planilha: {', '.join(faltantes)}")
        return

    df = df[colunas].copy()

    df["Data"] = pd.to_datetime(
        df["Data"].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce"
    )
    df = df.dropna(subset=["Data"])
    
    colunas_numericas = ["Cota Inicial (m)", "Cota Dia (m)", "Volume (m³)", "Volume (%)", "Evapor. Parcial (mm)"]
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # ✅ Formatar a coluna de volume com base no valor
    def formatar_volume(volume):
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.2f} milhões/m³"
        elif volume > 0:
            return f"{volume / 1_000:.2f} mil/m³"
        else:
            return "0 m³"
            
    df['Volume_formatado'] = df['Volume (m³)'].apply(formatar_volume)

    # --- Estilos
    st.markdown("""
    <style>
      .filter-card { border:1px solid #e6e6e6; border-radius:14px; padding:14px;
                      background:linear-gradient(180deg,#ffffff 0%, #fafafa 100%);
                      box-shadow:0 6px 16px rgba(0,0,0,.06); margin:6px 0 16px 0; }
      .filter-title { font-weight:700; color:#006400; margin-bottom:8px; letter-spacing:.2px; }
      .expander-rounded > details { border:1px solid #e6e6e6 !important; border-radius:14px !important;
                                     background:#fff !important; box-shadow:0 4px 14px rgba(0,0,0,.06) !important;
                                     padding:6px 6px 0 6px !important; }
      .expander-rounded summary { font-weight:600 !important; color:#006400 !important; }
    </style>
    """, unsafe_allow_html=True)

    # --- Filtros
    with st.container():
        st.markdown('<div class="expander-rounded">', unsafe_allow_html=True)
        with st.expander("☰ Filtros (clique para expandir)", expanded=True):
            st.markdown('<div class="filter-card"><div class="filter-title">Filtros de Visualização</div>', unsafe_allow_html=True)

            c1, c2 = st.columns([2, 3])

            with c1:
                opcoes_acudes = sorted(df["Açude"].dropna().unique().tolist())
                acudes_sel = st.multiselect("Açude", options=opcoes_acudes, default=opcoes_acudes)

            with c2:
                datas_validas = df["Data"]
                if not datas_validas.empty:
                    data_min = datas_validas.min().date()
                    data_max = datas_validas.max().date()
                    periodo = st.date_input(
                        "Período",
                        value=(data_min, data_max),
                        min_value=data_min,
                        max_value=data_max,
                        # ✅ Atualizado para a/m/a
                        format="DD/MM/YYYY" 
                    )
                else:
                    periodo = None

            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Aplicar filtros
    dff = df.copy()
    if acudes_sel:
        dff = dff[dff["Açude"].isin(acudes_sel)]
        
    if periodo:
        if len(periodo) == 1:
            ini = fim = pd.to_datetime(periodo[0])
        else:
            ini, fim = [pd.to_datetime(d) for d in periodo]
        
        dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]

    if dff.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    dff = dff.sort_values(["Açude", "Data"])

    # --- Gráfico 1
    st.subheader("📈 Cotas (Cota Inicial x Cota Dia)")
    fig_cotas = go.Figure()
    for acude in sorted(dff["Açude"].dropna().unique()):
        base = dff[dff["Açude"] == acude].sort_values("Data")
        fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Inicial (m)"],
                                        mode="lines+markers", name=f"{acude} - Cota Inicial (m)",
                                        hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
        fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Dia (m)"],
                                        mode="lines+markers", name=f"{acude} - Cota Dia (m)",
                                        hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
    fig_cotas.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                            xaxis_title="Data", yaxis_title="Cota (m)", height=480)
    st.plotly_chart(fig_cotas, use_container_width=True, config={"displaylogo": False})

    # --- Gráfico 2
    st.subheader("📈 Volume (m³)")
    fig_vol = go.Figure()
    for acude in sorted(dff["Açude"].dropna().unique()):
        base = dff[dff["Açude"] == acude].sort_values("Data")
        fig_vol.add_trace(go.Scatter(
            x=base["Data"], 
            y=base["Volume (m³)"],
            mode="lines+markers", 
            name=f"{acude} - Volume (m³)",
            # ✅ Atualizado para usar o Volume_formatado
            hovertemplate="%{x|%d/%m/%Y} • " + base["Volume_formatado"] + "<extra></extra>"
        ))
    fig_vol.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                            xaxis_title="Data", yaxis_title="Volume (m³)", height=420)
    st.plotly_chart(fig_vol, use_container_width=True, config={"displaylogo": False})

    # --- Tabela
    with st.expander("📋 Ver dados filtrados"):
        st.dataframe(dff.sort_values(["Açude", "Data"], ascending=[True, False]), use_container_width=True)



# =========================
# CRIAÇÃO DAS ABAS
# =========================
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Página Inicial", "🗺️ Açudes Monitorados", "📜 Documentos Oficiais", "📈 Simulações"])

with tab1:
    render_home()

with tab2:
    render_acudes()

with tab3:
    render_docs()

with tab4:
    render_dados()

# ======================RODAPÉ (GLOBAL)
st.markdown(
    f"""
    <style>
    .footer-mobile-full {{
        position: relative;
        width: 100vw;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        margin-top: 40px;
        background: none;
        color: #000000;
        padding: 10px 0;
        font-family: 'Segoe UI', Roboto, sans-serif;
        border-top: 3px solid #fad905;
        text-align: center;
        box-shadow: none;
    }}

    .footer-content {{
        display: flex;
        flex-direction: column;
        gap: 8px;
        width: 90%;
        margin: 0 auto;
        position: relative;
    }}

    .footer-row {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 12px;
    }}

    .footer-item {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
    }}

    .footer-divider {{
        color: rgba(0,0,0,0.4);
        font-size: 14px;
    }}

    .footer-address {{
        font-size: 13px;
        opacity: 0.9;
        margin-top: 4px;
    }}

    .footer-logos {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin-top: 10px;
    }}

    .footer-logos img {{
        height: 60px;
    }}

    /* Botão Voltar ao Topo */
    .back-to-top {{
        position: absolute;
        right: 20px;
        bottom: 20px;
        background-color: #fad905;
        color: #000;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }}

    .back-to-top:hover {{
        background-color: #e6c800;
        transform: translateY(-2px);
    }}

    /* Mobile First */
    @media (min-width: 481px) {{
        .footer-row {{
            gap: 16px;
        }}
        .footer-item {{
            font-size: 15px;
        }}
    }}

    @media (max-width: 480px) {{
        .footer-row {{
            flex-direction: column;
            gap: 8px;
        }}
        .footer-divider {{
            display: none;
        }}
        .footer-item {{
            font-size: 13px;
        }}
        .footer-address {{
            font-size: 12px;
        }}
        .footer-logos img {{
            height: 50px;
        }}
        .back-to-top {{
            right: 10px;
            bottom: 10px;
            width: 35px;
            height: 35px;
            font-size: 18px;
        }}
    }}
    </style>

    <div class="footer-mobile-full">
        <div class="footer-content">
            <div class="footer-logos">
                <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" alt="COGERH Logo">
                <img src="https://i.ibb.co/tpQrmPb0/csbh.png" alt="CSBH Logo">
            </div>
            <div class="footer-row">
                <div class="footer-item">
                    <b>Secretaria Executiva do CSBH Banabuiú: COGERH – Gerência da Bacia do Banabuiú</b>
                </div>
            </div>
            <div class="footer-row">
                <div class="footer-item">
                    📧 comite.banabuiu@cogerh.com.br 
                </div>
                <span class="footer-divider">|</span>
                <div class="footer-item">
                    📞 (85) 3513-9055
                </div>
            </div>
            <div class="footer-address">
                🏢 Rua Dona Francisca Santiago, 44 – Centro. CEP 63800-000 – Quixeramobim/CE
            </div>
            <button class="back-to-top" id="backToTopBtn2">↑</button>
        </div>
    </div>

    <script>
    // Adiciona o event listener para o botão
    document.getElementById("backToTopBtn2").addEventListener("click", function() {{
        window.scrollTo({{
            top: 0,
            behavior: 'smooth'
        }});
    }});
    </script>
    """,
    unsafe_allow_html=True,
)
