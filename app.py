

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
import base64
import unicodedata2
from datetime import datetime, timedelta, timezone
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MiniMap, MousePosition, MeasureControl, MarkerCluster

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
dias_semana = {'Monday':'Segunda-feira','Tuesday':'Terça-feira','Wednesday':'Quarta-feira','Thursday':'Quinta-feira','Friday':'Sexta-feira','Saturday':'Sábado','Sunday':'Domingo'}
meses = {'January':'janeiro','February':'fevereiro','March':'março','April':'abril','May':'maio','June':'junho','July':'julho','August':'agosto','September':'setembro','October':'outubro','November':'novembro','December':'dezembro'}
data_hoje = f"{dias_semana[agora.strftime('%A')]}, {agora.day:02d} de {meses[agora.strftime('%B')]} de {agora.year}"

st.markdown(f"""
<style>
[data-testid="stHeader"]{{visibility:hidden;}}
.custom-header{{position:fixed;top:0;left:0;width:100%;
background:linear-gradient(135deg,#228B22 0%,#006400 50%,#004d00 100%);
color:white;padding:12px 5%;font-family:'Segoe UI',Roboto,sans-serif;
box-shadow:0 4px 12px rgba(0,0,0,.1);z-index:9999}}
.header-container{{max-width:1200px;margin: 8px; auto;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px}}
.header-brand{{display:flex;align-items:center;gap:10px;flex:1;min-width:200px}}
.header-logo{{height:36px;filter:drop-shadow(0 2px 2px rgba(0,0,0,.2))}}
.header-title{{font-size:clamp(14px,3vw,18px);font-weight:600;letter-spacing:.5px;text-shadow:0 1px 3px rgba(0,0,0,.3)}}
.header-date{{background:rgba(255,255,255,.15);padding:4px 10px;border-radius:20px;font-size:clamp(10px,2.5vw,13px);font-weight:500;display:flex;align-items:center;gap:6px;backdrop-filter:blur(5px);white-space:nowrap}}
.main .block-container{{padding-top:90px}}
/* cartão dos filtros */
.filter-card{{border:1px solid #e6e6e6;border-radius:1px;padding:1px 1px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.06);margin-top:6px}}
.filter-title{{font-weight:600;margin-bottom:6px}}
.quick-chips span{{display:inline-block;border:1px solid #dcdcdc;border-radius:999px;padding:4px 10px;margin-right:6px;margin-top:4px;cursor:pointer;font-size:12px}}
.quick-chips span:hover{{background:#f5f5f5}}
.kpi-card{{border:1px solid #eaeaea;border-radius:14px;padding:14px;background:linear-gradient(180deg,#ffffff 0%, #fafafa 100%);box-shadow:0 6px 16px rgba(0,0,0,.06);text-align:center}}
.kpi-value{{font-size:22px;font-weight:700;margin-top:4px}}
/* Estilo do menu hamburguer */
.st-emotion-cache-1q7spjk {{  /* Classe do ícone do expander */
    color: #228B22 !important;
    font-weight: bold;
}}
.st-emotion-cache-1q7spjk:hover {{
    color: #006400 !important;
}}
.map-style-selector {{
    margin-top: -10px;
}}
@media(max-width:600px){{
 .main .block-container{{padding-top:110px}}
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
    <div class="header-date">📅 {data_hoje}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------- UTIL ----------------
def convert_vazao(series, unidade):
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

@st.cache_data(ttl=300)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
    df = pd.read_csv(url)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Mês'] = df['Data'].dt.to_period('M').astype(str)
    return df

# ---------------- TABS ----------------
# Adicionando a nova aba aqui
tab1, tab2, tab3 = st.tabs(["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados", "📜 Documentos Oficiais"])

with tab1:
    # dados
    df = carregar_dados()

    # barra de ações
    cA1, cA2, cA3 = st.columns([1,1,1])
    with cA1:
        if st.button("🔄 Atualizar agora"):
            carregar_dados.clear()
            df = carregar_dados()
            st.success("Atualizado.")

    st.markdown("""
<style>
.custom-title {
    font-family: 'Segoe UI', Roboto, sans-serif !important;
    font-size: 20px !important; /* Fonte fixa */
    font-weight: 700 !important;
    color: #006400 !important;
    text-align: center !important;
    margin: 8px 0 10px 0 !important;
    padding: 12px 22px !important; /* Retângulo mais estreito */
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    background: rgba(144, 238, 144, 0.15) !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
}

.custom-title::before, .custom-title::after {
    content: "" !important;
    flex: 1 !important;
    height: 2px !important;
    background: linear-gradient(90deg, transparent, #228B22) !important;
    border-radius: 2px !important;
}

.custom-title::after {
    background: linear-gradient(90deg, #228B22, transparent) !important;
}

.custom-title span {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 18px !important; /* Ícones do mesmo tamanho da fonte */
}

@media (max-width: 600px) {
    .custom-title {
        flex-direction: column !important;
        gap: 4px !important;
        padding: 6px 12px !important;
    }
    .custom-title::before, .custom-title::after {
        width: 70% !important;
        height: 1.5px !important;
    }
}
</style>

<h1 class="custom-title">
    <span>💧</span> Painel de Vazões </span>
</h1>
""", unsafe_allow_html=True)

    with st.expander("☰ Filtros", expanded=False):
        st.markdown("""
        <style>
        .filter-container {
            margin-top: 5px;
            padding: 5px; 
        }
        </style>
        <div class="filter-container">
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">Opções de Filtro</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            estacoes = st.multiselect("🏞️ Reservatório", df['Reservatório Monitorado'].dropna().unique())
            operacao = st.multiselect("🔧 Operação", df['Operação'].dropna().unique())
        with col2:
            meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        
        col3, col4 = st.columns(2)
        with col3:
            datas_disponiveis = df['Data'].dropna().sort_values()
            data_min = datas_disponiveis.min()
            data_max = datas_disponiveis.max()
            intervalo_data = st.date_input("📅 Intervalo", (data_min, data_max), format="DD/MM/YYYY")
        with col4:
            unidade_sel = st.selectbox("🧪 Unidade", ["L/s", "m³/s"], index=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if operacao:
        df_filtrado = df_filtrado[df_filtrado['Operação'].isin(operacao)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(inicio)) &
                                  (df_filtrado['Data'] <= pd.to_datetime(fim))]

    st.markdown("""
    <style>
    .kpi-container {
        display: flex;
        gap: 16px;
        margin: -20px 0;
        flex-wrap: wrap;
        justify-content: space-between;
    }
    
    .kpi-card {
        flex: 1;
        min-width: 180px;
        background: linear-gradient(135deg, #e0f5ec, #b2dfdb);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.08);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.15);
    }
    
    .kpi-label {
        font-size: 14px;
        font-weight: 600;
        color: #004d40;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #00695c;
    }
    
    /* Mobile: empilhar KPIs */
    @media (max-width: 768px) {
        .kpi-container {
            flex-direction: column;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    reservatorios_count = df_filtrado['Reservatório Monitorado'].nunique()
    registros_count = len(df_filtrado)
    ultima_data = df_filtrado['Data'].max().strftime("%d/%m/%Y") if not df_filtrado.empty else "—"
    unidade_show = "m³/s" if unidade_sel == "m³/s" else "L/s"
    
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Reservatórios</div>
            <div class="kpi-value">{reservatorios_count}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Registros</div>
            <div class="kpi-value">{registros_count}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Última Data</div>
            <div class="kpi-value">{ultima_data}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Unidade</div>
            <div class="kpi-value">{unidade_show}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    fig = go.Figure()
    cores = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#17becf','#e377c2']
    reservatorios = df_filtrado['Reservatório Monitorado'].dropna().unique()
    
    for i, r in enumerate(reservatorios):
        dfr = (df_filtrado[df_filtrado['Reservatório Monitorado'] == r]
               .sort_values('Data').groupby('Data', as_index=False).last())
        y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
        fig.add_trace(go.Scatter(
            x=dfr["Data"], y=y_vals, mode="lines+markers", name=r,
            line=dict(shape='hv', width=2, color=cores[i % len(cores)]),
            marker=dict(size=5),
            hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
        ))
        
        if len(reservatorios) == 1 and len(dfr) > 1:
            dfr['dias_ativos'] = dfr['Data'].diff().dt.days.fillna(0)
            dfr.loc[dfr.index[-1], 'dias_ativos'] = (df_filtrado['Data'].max() - dfr['Data'].iloc[-1]).days + 1
            media_pond = (dfr['Vazão Operada'] * dfr['dias_ativos']).sum() / dfr['dias_ativos'].sum()
            media_pond_conv, _ = convert_vazao(pd.Series([media_pond]), unidade_sel)
            fig.add_hline(y=media_pond_conv.iloc[0], line_dash="dash", line_width=2, line_color="red",
                          annotation_text=f"Média Ponderada: {media_pond_conv.iloc[0]:.2f} {unit_suffix}",
                          annotation_position="top right")
    
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title=f"Vazão Operada ({'m³/s' if unidade_sel=='m³/s' else 'L/s'})",
        legend_title="Reservatório",
        template="plotly_white",
        margin=dict(l=40,r=20,t=10,b=40),
        xaxis=dict(
            rangeslider=dict(
                visible=True,
                thickness=0.1,
                bgcolor='#f5f5f5'
            ),
            rangeselector=None
        )
    )
    
    fig.update_xaxes(
        rangeslider=dict(
            bordercolor="#cccccc",
            borderwidth=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    gtab1, gtab2 = st.tabs(["📊 Média mensal", "📦 Distribuição (boxplot)"])
    with gtab1:
        if not df_filtrado.empty:
            dmm = (df_filtrado.assign(mes_num=df_filtrado['Data'].dt.to_period('M').astype(str))
                   .groupby(['Reservatório Monitorado','mes_num'], as_index=False)['Vazão Operada'].mean())
            yconv, sufx = convert_vazao(dmm['Vazão Operada'], unidade_sel)
            dmm['Vazão (conv)'] = yconv
            figm = px.bar(dmm, x='mes_num', y='Vazão (conv)', color='Reservatório Monitorado',
                          labels={'mes_num':'Mês','Vazão (conv)':f'Média ({sufx})'},
                          barmode='group')
            st.plotly_chart(figm, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sem dados para média mensal.")
            
    with gtab2:
        if not df_filtrado.empty and df_filtrado['Reservatório Monitorado'].nunique() > 0:
            yconv, sufx = convert_vazao(df_filtrado['Vazão Operada'], unidade_sel)
            df_box = df_filtrado.copy()
            df_box['Vazão (conv)'] = yconv
            
            volumes = []
            for reservatorio in df_box['Reservatório Monitorado'].unique():
                df_res = df_box[df_box['Reservatório Monitorado'] == reservatorio].sort_values('Data')
                
                df_res['dias_entre_medicoes'] = df_res['Data'].diff().dt.days.fillna(0)
                ultima_data = df_res['Data'].iloc[-1]
                fim_periodo = df_box['Data'].max() if pd.notna(df_box['Data'].max()) else ultima_data
                df_res.loc[df_res.index[-1], 'dias_entre_medicoes'] = (fim_periodo - ultima_data).days + 1
                
                segundos_por_dia = 86400
                df_res['volume_periodo'] = df_res['Vazão (conv)'] * segundos_por_dia * df_res['dias_entre_medicoes']
                volume_total = df_res['volume_periodo'].sum()
                
                volume_formatado = f"{volume_total/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " milhões m³"
                
                volumes.append({
                    'Reservatório Monitorado': reservatorio,
                    'Volume Acumulado': volume_total,
                    'Volume Formatado': volume_formatado
                })
            
            df_volumes = pd.DataFrame(volumes)
            
            figb = go.Figure()
            
            for r in df_box['Reservatório Monitorado'].unique():
                figb.add_trace(go.Box(
                    y=df_box[df_box['Reservatório Monitorado'] == r]['Vazão (conv)'],
                    name=r,
                    boxpoints='all',
                    jitter=0.5,
                    pointpos=0,
                    marker_color='#1f77b4',
                    line_color='#1f77b4',
                    hoverinfo='none'
                ))
            
            for i, row in df_volumes.iterrows():
                figb.add_trace(go.Scatter(
                    x=[row['Reservatório Monitorado']],
                    y=[df_box[df_box['Reservatório Monitorado'] == row['Reservatório Monitorado']]['Vazão (conv)'].max()],
                    mode='markers',
                    marker=dict(opacity=0),
                    hoverinfo='text',
                    hovertext=f"Volume Acumulado: {row['Volume Formatado']}",
                    showlegend=False
                ))
            
            figb.update_layout(
                title='Distribuição de Vazões',
                xaxis_title='Reservatório',
                yaxis_title=f'Vazão Operada ({sufx})',
                showlegend=False,
                hovermode='closest'
            )
            
            for i, row in df_volumes.iterrows():
                figb.add_annotation(
                    x=row['Reservatório Monitorado'],
                    y=df_box[df_box['Reservatório Monitorado'] == row['Reservatório Monitorado']]['Vazão (conv)'].max(),
                    text=f"<b style='color:red;font-size:14px'>VOLUME: {row['Volume Formatado']}</b>",
                    showarrow=False,
                    yshift=20,
                    font=dict(size=12),
                    bordercolor="red",
                    borderwidth=1,
                    borderpad=4
                )
            
            st.plotly_chart(figb, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sem dados suficientes para boxplot.")

    st.subheader("🗺️ Mapa dos Reservatórios com Camadas")
    df_mapa = df_filtrado.copy()
    if 'Coordendas' in df_mapa.columns:
        df_mapa[['lat','lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
    df_mapa = df_mapa.dropna(subset=['lat','lon']).drop_duplicates(subset=['Reservatório Monitorado'])

    with st.expander("☰ Estilo do Mapa", expanded=False):
        mapa_tipo = st.selectbox(
            "Selecione o estilo:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner",
             "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0,
            key="map_style_selector",
            label_visibility="collapsed"
        )

    tile_urls = {
        "OpenStreetMap": None,
        "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        "Stamen Toner": "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
        "CartoDB positron": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
        "CartoDB dark_matter": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
        "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }

    tile_attr = {
        "OpenStreetMap": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        "Stamen Terrain": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        "Stamen Toner": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        "CartoDB positron": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        "CartoDB dark_matter": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        "Esri Satellite": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    }

    if not df_mapa.empty:
        center = [df_mapa['lat'].mean(), df_mapa['lon'].mean()]
        m = folium.Map(location=center, zoom_start=8, tiles=None)
        
        if mapa_tipo == "OpenStreetMap":
            folium.TileLayer(tiles='OpenStreetMap').add_to(m)
        else:
            folium.TileLayer(
                tiles=tile_urls[mapa_tipo],
                attr=tile_attr[mapa_tipo],
                name=mapa_tipo
            ).add_to(m)

        Fullscreen(position='topleft').add_to(m)
        MiniMap(toggle_display=True, minimized=True).add_to(m)
        MousePosition(position='bottomleft', separator=' | ', prefix='Coords').add_to(m)
        MeasureControl(primary_length_unit='meters').add_to(m)

        folium.GeoJson(geojson_bacia, name="Bacia do Banabuiu",
                       tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
                       style_function=lambda x: {"color":"darkblue","weight":2}).add_to(m)

        trechos_layer = folium.FeatureGroup(name="Trechos Perenizados", show=False)
        folium.GeoJson(geojson_trechos,
                       tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]),
                       style_function=lambda x: {"color":"darkblue","weight":1}).add_to(trechos_layer)
        trechos_layer.add_to(m)

        pontos_layer = folium.FeatureGroup(name="Pontos de Controle", show=False)
        for feature in geojson_pontos["features"]:
            props = feature["properties"]; coords = feature["geometry"]["coordinates"]
            nome_municipio = props.get("Name","Sem nome")
            folium.Marker([coords[1], coords[0]],
                          icon=folium.CustomIcon("https://i.ibb.co/HfCcFWjb/marker.png", icon_size=(22,22)),
                          tooltip=nome_municipio).add_to(pontos_layer)
        pontos_layer.add_to(m)

        acudes_layer = folium.FeatureGroup(name="Açudes Monitorados", show=False)
        folium.GeoJson(geojson_acudes,
                       tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]),
                       style_function=lambda x: {"color":"darkgreen","weight":2}).add_to(acudes_layer)
        acudes_layer.add_to(m)

        sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
        for feature in geojson_sedes["features"]:
            props = feature["properties"]; coords = feature["geometry"]["coordinates"]
            nome = props.get("NOME_MUNIC","Sem nome")
            folium.Marker([coords[1], coords[0]],
                          icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(22,22)),
                          tooltip=nome).add_to(sedes_layer)
        sedes_layer.add_to(m)

        gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
        for feature in geojson_c_gestoras["features"]:
            props = feature["properties"]; coords = feature["geometry"]["coordinates"]
            nome_g = props.get("SISTEMAH3","Sem nome")
            popup_info = f"""
<div style='
    font-family: "Segoe UI", Arial, sans-serif;
    padding: 12px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-top: 4px solid #228B22;
    min-width: 200px;
'>
    <div style='
        font-size: 16px; 
        font-weight: 600; 
        color: #2c3e50;
        margin-bottom: 8px;
    '>
        {nome_g}
    </div>
    
    <div style='margin: 6px 0;'>
        <div style='font-weight: 500; color: #7f8c8d;'>Ano de Formação</div>
        <div style='color: #2c3e50;'>{props.get("ANOFORMA1","N/A")}</div>
    </div>
    
    <div style='margin: 6px 0;'>
        <div style='font-weight: 500; color: #7f8c8d;'>Sistema</div>
        <div style='color: #2c3e50;'>{props.get("SISTEMAH3","N/A")}</div>
    </div>
    
    <div style='margin: 6px 0;'>
        <div style='font-weight: 500; color: #7f8c8d;'>Município</div>
        <div style='color: #228B22; font-weight: 500;'>{props.get("MUNICIPI6","N/A")}</div>
    </div>
</div>
"""
            
            folium.Marker([coords[1], coords[0]],
                          icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30,30)),
                          tooltip=nome_g,
                          popup=folium.Popup(popup_info, max_width=300)).add_to(gestoras_layer)
        gestoras_layer.add_to(m)

        municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
        folium.GeoJson(geojson_poligno,
                       tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]),
                       style_function=lambda x: {"fillOpacity":0,"color":"blue","weight":1}).add_to(municipios_layer)
        municipios_layer.add_to(m)

        cluster = MarkerCluster(name="Reservatórios (pinos)").add_to(m)
        for _, row in df_mapa.iterrows():
            try:
                val = float(row.get('Vazao_Aloc', float('nan')))
            except Exception:
                val = float('nan')
            val_conv, unit_suf = convert_vazao(pd.Series([val]), unidade_sel)
            val_txt = f"{val_conv.iloc[0]:.3f} {unit_suf}" if pd.notna(val_conv.iloc[0]) else "—"
            data_txt = row['Data'].date() if pd.notna(row['Data']) else "—"
            popup_info = f"""
<div style='
    font-family: "Segoe UI", Arial, sans-serif;
    padding: 12px;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    border-left: 4px solid #228B22;
    min-width: 220px;
'>
    <div style='
        font-size: 16px; 
        font-weight: 600; 
        color: #2c3e50;
        margin-bottom: 8px;
        border-bottom: 1px solid #dfe6e9;
        padding-bottom: 6px;
    '>
        {row['Reservatório Monitorado']}
    </div>
    
    <div style='margin-bottom: 4px;'>
        <span style='
            display: inline-block;
            width: 100px;
            font-weight: 500;
            color: #7f8c8d;
        '>Data:</span>
        <span style='color: #2c3e50;'>{data_txt}</span>
    </div>
    
    <div style='margin-bottom: 4px;'>
        <span style='
            display: inline-block;
            width: 100px;
            font-weight: 500;
            color: #7f8c8d;
        '>Vazão:</span>
        <span style='
            color: #228B22;
            font-weight: 600;
        '>{val_txt}</span>
    </div>
    
    <div style='
        margin-top: 8px;
        font-size: 12px;
        color: #7f8c8d;
        text-align: right;
    '>
        Sistema de Monitoramento
    </div>
</div>
"""
            folium.Marker([row["lat"], row["lon"]],
                          popup=folium.Popup(popup_info, max_width=300),
                          icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30,30)),
                          tooltip=row["Reservatório Monitorado"]).add_to(cluster)

        folium.LayerControl(collapsed=True, position='topright').add_to(m)
        folium_static(m, width=1200)
    else:
        st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    if not df_filtrado.empty:
        media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
        media_conv, unit_bar = convert_vazao(media_vazao["Vazão Operada"], unidade_sel)
        media_vazao["Vazão (conv)"] = media_conv
        st.plotly_chart(
            px.bar(media_vazao, x="Reservatório Monitorado", y="Vazão (conv)",
                   text_auto='.2s', labels={"Vazão (conv)": f"Média ({unit_bar})"}),
            use_container_width=True, config={"displaylogo": False}
        )
    else:
        st.info("Sem dados para a média.")

    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)

#================PÁGINA > AÇUDES MONITORADOS==================

with tab2:
    st.title("🗺️ Açudes Monitorados")
    
    with st.expander("☰ Estilo do Mapa", expanded=False):
        tile_option = st.selectbox(
            "Selecione o estilo:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner",
             "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            key="acudes_map_tile",
            label_visibility="collapsed"
        )
    
    tile_urls = {
        "OpenStreetMap": None,
        "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        "Stamen Toner": "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
        "CartoDB positron": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
        "CartoDB dark_matter": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
        "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }

    tile_attr = {
        "OpenStreetMap": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        "Stamen Terrain": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        "Stamen Toner": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        "CartoDB positron": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        "CartoDB dark_matter": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        "Esri Satellite": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    }

    # Inicializa o mapa com zoom mais próximo (aumentei o zoom_start para 9)
    m2 = folium.Map(location=[-5.2, -39.2], zoom_start=8.5, tiles=None)

    # Adiciona a camada da bacia primeiro para calcular o bounds
    bacia_layer = folium.GeoJson(geojson_bacia, 
                               name="Bacia do Banabuiu",
                               tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
                               style_function=lambda x: {"color":"darkblue","weight":2})
    bacia_layer.add_to(m2)

    # Carregar dados da planilha Google
    @st.cache_data(ttl=3600)
    def load_reservatorios_data():
        try:
            url = "https://docs.google.com/spreadsheets/d/1zZ0RCyYj-AzA_dhWzxRziDWjgforbaH7WIoSEd2EKdk/export?format=csv"
            df = pd.read_csv(url)
            
            # Verificar e corrigir formato das coordenadas
            df['Latitude'] = pd.to_numeric(df['Latitude'].str.replace(',', '.'), errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'].str.replace(',', '.'), errors='coerce')
            
            # Filtrar apenas linhas com coordenadas válidas
            df = df.dropna(subset=['Latitude', 'Longitude'])
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados dos reservatórios: {str(e)}")
            return pd.DataFrame()

    df_reservatorios = load_reservatorios_data()

    # Adicionar camada de reservatórios
    reservatorios_layer = folium.FeatureGroup(name="Reservatórios (Dados Atualizados)", show=True)
    
    if not df_reservatorios.empty:
        for _, row in df_reservatorios.iterrows():
            try:
                if not (-90 <= row['Latitude'] <= 90) or not (-180 <= row['Longitude'] <= 180):
                    continue
                    
                popup_info = f"""
<div style='font-family: "Segoe UI", Arial, sans-serif; padding: 14px; background: white; border-radius: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.15); border-left: 5px solid #228B22; min-width: 250px;'>
    <div style='font-size: 17px; font-weight: 700; color: #006400; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 8px;'>
        {row.get('Reservatório', 'N/A')}
    </div>
    <div style='margin: 8px 0;'><div style='font-weight: 600; color: #555;'>Região Hidrográfica:</div><div style='color: #333;'>{row.get('Região Hidrográfica', 'N/A')}</div></div>
    <div style='margin: 8px 0;'><div style='font-weight: 600; color: #555;'>Município:</div><div style='color: #333;'>{row.get('Município', 'N/A')}</div></div>
    <div style='margin: 8px 0;'><div style='font-weight: 600; color: #555;'>Cota Sangria:</div><div style='color: #333;'>{row.get('Cota Sangria', 'N/A')}</div></div>
    <div style='margin: 8px 0;'><div style='font-weight: 600; color: #555;'>Volume (hm³):</div><div style='color: #333;'>{row.get('Volume', 'N/A')}</div></div>
    <div style='margin: 8px 0;'><div style='font-weight: 600; color: #555;'>Percentual:</div><div style='color: #228B22; font-weight: 700;'>{row.get('Percentual', 'N/A')}%</div></div>
</div>
"""
                folium.Marker(
                    [row['Latitude'], row['Longitude']],
                    icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/3059/3059518.png", icon_size=(28, 28)),
                    tooltip=row.get('Reservatório', 'Reservatório'),
                    popup=folium.Popup(popup_info, max_width=300)
                ).add_to(reservatorios_layer)
                
            except Exception as e:
                st.sidebar.error(f"Erro ao plotar reservatório {row.get('Reservatório', '')}: {str(e)}")
                continue
    
    reservatorios_layer.add_to(m2)

    # Demais camadas (Comissões Gestoras, Açudes, etc.)
    gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
    for feature in geojson_c_gestoras["features"]:
        props = feature["properties"]; coords = feature["geometry"]["coordinates"]
        nome_g = props.get("SISTEMAH3","Sem nome")
        popup_info = f"""...""" # (mantido igual ao anterior)
        folium.Marker(
            [coords[1], coords[0]],
            icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30,30)),
            tooltip=nome_g,
            popup=folium.Popup(popup_info, max_width=300)
        ).add_to(gestoras_layer)
    gestoras_layer.add_to(m2)

    # Configurações base do mapa
    if tile_option == "OpenStreetMap":
        folium.TileLayer(tiles='OpenStreetMap').add_to(m2)
    else:
        folium.TileLayer(
            tiles=tile_urls[tile_option],
            attr=tile_attr[tile_option],
            name=tile_option
        ).add_to(m2)

    # Controles do mapa
    Fullscreen(position='topleft').add_to(m2)
    MiniMap(toggle_display=True, minimized=True).add_to(m2)
    MousePosition(position='bottomleft', separator=' | ', prefix='Coords').add_to(m2)
    MeasureControl(primary_length_unit='meters').add_to(m2)

    # Camada de Açudes
    folium.GeoJson(geojson_acudes, name="Açudes", tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])).add_to(m2)
    
    # Controle de camadas
    folium.LayerControl(collapsed=True, position='topright').add_to(m2)
    
    # Exibir mapa
    folium_static(m2, width=1200)

#================PÁGINA > DOCUMENTOS OFICIAS==================

with tab3:
    st.title("📜 Documentos para Download")

    SHEET_ID = "1-Tn_ZDHH-mNgJAY1WtjWd_Pyd2f5kv_ZU8dhL0caGDI"
    GID = "0"
    URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

    st.markdown("""
<div style="
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
    border-radius: 12px;
    padding: 20px;
    border-left: 4px solid #228B22;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 20px;
">
    <p style="
        font-family: 'Segoe UI', Roboto, sans-serif;
        color: #2c3e50;
        font-size: 16px;
        line-height: 1.6;
        margin: 0;
    ">
        <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
        • Atas e apresentações das reuniões da Bacia do Banabuiú<br>
        • Organizadas por operação, reservatório e parâmetros<br>
        • Dados de vazão média aprovados
    </p>
</div>
""", unsafe_allow_html=True)

    # Carregar dados com tratamento robusto
    @st.cache_data(ttl=3600)
    def load_data():
        try:
            df = pd.read_csv(URL, encoding='utf-8-sig').dropna(how='all')
            # Converter colunas para string com tratamento de valores nulos
            text_cols = ["Operação", "Data da Reunião", "Reservatório/Sistema", 
                        "Local da Reunião", "Parâmetros aprovados", "Vazão média"]
            for col in text_cols:
                if col in df.columns:
                    df[col] = df[col].fillna('').astype(str)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()

    df = load_data()

    # Container para filtros
    with st.container(border=True):
        st.markdown("**Filtrar documentos**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ops = ["Todos"] + sorted(df["Operação"].unique()) if "Operação" in df.columns else ["Todos"]
            filtro_operacao = st.selectbox("Operação", ops, index=0)
        
        with col2:
            datas = ["Todos"] + sorted(df["Data da Reunião"].unique()) if "Data da Reunião" in df.columns else ["Todos"]
            filtro_data = st.selectbox("Data da Reunião", datas, index=0)
        
        busca = st.text_input("Buscar em todos os campos", "")

    # Aplicar filtros
    df_filtrado = df.copy()

    if filtro_operacao != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Operação"] == filtro_operacao]

    if filtro_data != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Data da Reunião"] == filtro_data]

    # Busca simplificada sem unicodedata
    if busca:
        busca_lower = busca.lower().strip()
        mask = df_filtrado.apply(
            lambda row: any(busca_lower in str(val).lower() for val in row.values), 
            axis=1
        )
        df_filtrado = df_filtrado[mask]

    # Contador de resultados
    st.markdown(f"**{len(df_filtrado)} registros encontrados**")

    # CSS otimizado
    table_style = """
    <style>
    .table-container {
        overflow: auto;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: center;
    }
    th {
        background-color: #f8f9fa;
        position: sticky;
        top: 0;
    }
    .download-btn {
        display: inline-block;
        padding: 4px 10px;
        background: #28a745;
        color: white !important;
        border-radius: 4px;
        text-decoration: none;
        font-size: 13px;
    }
    .no-data {
        color: #6c757d;
        font-style: italic;
        padding: 1rem;
    }
    </style>
    """

    # Construir tabela HTML de forma segura
    table_html = f"""
    {table_style}
    <div class="table-container">
    <table>
        <thead>
            <tr>
                <th>Operação</th>
                <th>Reservatório</th>
                <th>Data</th>
                <th>Local</th>
                <th>Parâmetros</th>
                <th>Vazão</th>
                <th>Apresentação</th>
                <th>Ata</th>
            </tr>
        </thead>
        <tbody>
    """

    if not df_filtrado.empty:
        for _, row in df_filtrado.iterrows():
            # Extrair valores com tratamento seguro
            cells = [
                row.get('Operação', ''),
                row.get('Reservatório/Sistema', ''),
                row.get('Data da Reunião', ''),
                row.get('Local da Reunião', ''),
                row.get('Parâmetros aprovados', ''),
                row.get('Vazão média', ''),
                row.get('Apresentação', ''),
                row.get('Ata da Reunião', '')
            ]
            
            # Processar links de download
            for i in [6, 7]:  # Índices dos campos de links
                if not cells[i] or str(cells[i]).lower() in ['nan', 'none', '']:
                    cells[i] = "—"
                else:
                    cells[i] = f'<a class="download-btn" href="{cells[i]}" target="_blank">Baixar</a>'
            
            # Adicionar linha à tabela
            table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"
    else:
        table_html += '<tr><td colspan="8" class="no-data">Nenhum registro encontrado</td></tr>'

    table_html += """
        </tbody>
    </table>
    </div>
    """

    # Exibir tabela
    st.markdown(table_html, unsafe_allow_html=True)
