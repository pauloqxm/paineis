

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

#-----------------BARA FIXA------------
st.markdown(f"""
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
tab1, tab2, tab3 = st.tabs(["🏠 Pagina Iicial", "🗺️ Açudes Monitorados", "📜 Documentos Oficiais"])

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
        margin: -15px 0;
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
        • Visualização dos açudes monitorados na bacia do Banabuiú<br>
        • Filtros interativos para análise dos dados<br>
        • Tabela detalhada com informações técnicas
    </p>
</div>
""", unsafe_allow_html=True)

    @st.cache_data(ttl=3600)
    def load_reservatorios_data():
        try:
            url = "https://docs.google.com/spreadsheets/d/1zZ0RCyYj-AzA_dhWzxRziDWjgforbaH7WIoSEd2EKdk/export?format=csv"
            df = pd.read_csv(url)

            if 'Latitude' in df.columns and 'Longitude' in df.columns:
                df['Latitude'] = pd.to_numeric(df['Latitude'].astype(str).str.replace(',', '.'), errors='coerce')
                df['Longitude'] = pd.to_numeric(df['Longitude'].astype(str).str.replace(',', '.'), errors='coerce')
                df = df.dropna(subset=['Latitude', 'Longitude'])
            else:
                st.error("Colunas 'Latitude' e 'Longitude' são necessárias")
                return pd.DataFrame()

            if 'Data de Coleta' in df.columns:
                df['Data de Coleta'] = pd.to_datetime(df['Data de Coleta'], errors='coerce', dayfirst=True)
                df = df.dropna(subset=['Data de Coleta'])

            numeric_cols = {
                'Percentual': lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.').str.replace('%', '').str.strip(), errors='coerce'),
                'Volume': lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.').str.strip(), errors='coerce'),
                'Cota Sangria': lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.').str.strip(), errors='coerce'),
                'Nivel': lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.').str.strip(), errors='coerce')
            }

            for col, converter in numeric_cols.items():
                if col in df.columns:
                    df[col] = converter(df[col])
                    df[col] = df[col].fillna(0)

            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()

    df_full = load_reservatorios_data()

    if df_full.empty:
        st.warning("Não foi possível carregar os dados dos reservatórios.")
        st.stop()

    # --- Filtros Interativos ---
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            min_date = df_full['Data de Coleta'].min().date()
            max_date = df_full['Data de Coleta'].max().date()
            date_range = st.date_input(
                "Período:",
                value=(max_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            if len(date_range) == 2:
                start_date, end_date = date_range
            else:
                st.warning("Selecione um intervalo válido")
                st.stop()

        with col2:
            reservatorios = sorted(df_full['Reservatório'].unique())
            reservatorio_filtro = st.multiselect(
                "Reservatório(s):",
                options=reservatorios,
                default=reservatorios,
                placeholder="Selecione..."
            )

        with col3:
            municipios = ['Todos'] + sorted(df_full['Município'].unique().tolist())
            municipio_filtro = st.selectbox(
                "Município:",
                options=municipios,
                index=0
            )

        min_perc = float(df_full['Percentual'].min()) if 'Percentual' in df_full.columns else 0
        max_perc = float(df_full['Percentual'].max()) if 'Percentual' in df_full.columns else 100
        perc_range = st.slider(
            "Percentual de Volume (%):",
            min_value=min_perc,
            max_value=max_perc,
            value=(min_perc, max_perc),
            step=0.1
        )

    # Aplicar filtros
    df_filtrado = df_full[
        (df_full['Data de Coleta'].dt.date >= start_date) &
        (df_full['Data de Coleta'].dt.date <= end_date) &
        (df_full['Reservatório'].isin(reservatorio_filtro)) &
        (df_full['Percentual'] >= perc_range[0]) &
        (df_full['Percentual'] <= perc_range[1])
    ].copy()

    if municipio_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Município'] == municipio_filtro].copy()

    # Obter última medição por reservatório para o mapa
    df_mapa = df_filtrado.sort_values('Data de Coleta', ascending=False).drop_duplicates(subset=['Reservatório']).copy()

# ================================================================
# 🗺️ MAPA INTERATIVO
# ================================================================
st.subheader("🌍 Mapa dos Açudes")

# Container para as configurações do mapa
with st.expander("Configurações do Mapa", expanded=False):
    tile_option = st.selectbox(
        "Estilo do Mapa:",
        ["OpenStreetMap", "Stamen Terrain", "Stamen Toner",
         "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
        index=0
    )

# Mapeamento dos estilos de mapa
tile_config = {
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    },
    "Stamen Terrain": {
        "tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'
    },
    "CartoDB positron": {
        "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
        "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'
    },
    "CartoDB dark_matter": {
        "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
        "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'
    },
    "Esri Satellite": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles &copy; Esri &mdash; Source: Esri"
    },
    "Stamen Toner": {
        "tiles": "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
        "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'
    }
}

# Inicia o mapa se houver dados filtrados
if not df_filtrado.empty:
    # --- Funções de estilização para os marcadores ---
    def get_marker_color(percentual):
        """Retorna a cor do marcador com base no percentual de volume."""
        if pd.isna(percentual):
            return '#808080'
        if 0 <= percentual <= 10:
            return '#808080'
        elif 10.1 <= percentual <= 30:
            return '#FF0000'
        elif 30.1 <= percentual <= 50:
            return '#FFFF00'
        elif 50.1 <= percentual <= 70:
            return '#008000'
        elif 70.1 <= percentual <= 100:
            return '#0000FF'
        else:
            return '#800080'

    def create_svg_icon(color, size=15):
        """Cria um ícone SVG de triângulo em base64."""
        svg = f"""
        <svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <polygon points="50,0 100,100 0,100" fill="{color}" stroke="#000000" stroke-width="5"/>
        </svg>
        """
        svg_bytes = svg.encode('utf-8')
        svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"

    # Calcula o centro do mapa
    mapa_center = [df_mapa['Latitude'].mean(), df_mapa['Longitude'].mean()]
    m = folium.Map(location=mapa_center, zoom_start=9, tiles=None)

    # Adiciona a camada de base selecionada
    folium.TileLayer(
        tiles=tile_config.get(tile_option, {}).get("tiles", "OpenStreetMap"),
        attr=tile_config.get(tile_option, {}).get("attr", ''),
        name=tile_option
    ).add_to(m)

    # --- CAMADA BACIA DO BANABUIÚ ---
    try:
        folium.GeoJson(
            geojson_bacia,
            name="Bacia do Banabuiú",
            style_function=lambda x: {"color": "blue", "weight": 2, "fillOpacity": 0.1},
            tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"])
        ).add_to(m)
    except NameError:
        st.warning("A variável 'geojson_bacia' não foi encontrada. Camada da bacia não adicionada.")

    # --- CAMADA COMISSÕES GESTORAS ---
    gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
    try:
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
            folium.Marker(
                [coords[1], coords[0]],
                icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30, 30)),
                tooltip=nome_g,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(gestoras_layer)
        gestoras_layer.add_to(m)
    except NameError:
        st.warning("A variável 'geojson_c_gestoras' não foi encontrada. Camada de comissões gestoras não adicionada.")

    # --- CAMADA MUNICÍPIOS ---
    municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
    try:
        folium.GeoJson(
            geojson_poligno,
            tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]),
            style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}
        ).add_to(municipios_layer)
        municipios_layer.add_to(m)
    except NameError:
        st.warning("A variável 'geojson_poligno' não foi encontrada. Camada de municípios não adicionada.")

    # --- CAMADA AÇUDES (MARCADORES) ---
    for _, row in df_mapa.iterrows():
        try:
            percentual_str = f"{float(row['Percentual']):.2f}%"
            percentual_val = float(row['Percentual'])
        except (ValueError, TypeError):
            percentual_str = 'N/A'
            percentual_val = None

        try:
            volume_str = f"{float(row['Volume']):,.2f} hm³".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            volume_str = 'N/A'

        try:
            cota_sangria_str = f"{float(row['Cota Sangria']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            cota_sangria_str = 'N/A'

        ultima_data_filtrada = df_filtrado[df_filtrado['Reservatório'] == row['Reservatório']]['Data de Coleta'].max()
        data_formatada = ultima_data_filtrada.strftime('%d/%m/%Y') if pd.notnull(ultima_data_filtrada) else 'N/A'
        
        icon_color = get_marker_color(percentual_val)

        popup_content = f"""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
        <div style='font-family: "Segoe UI", sans-serif; width: 280px; background: linear-gradient(to bottom, #f9f9f9, #ffffff); border-radius: 8px; border-left: 5px solid {icon_color}; padding: 12px; box-shadow: 0 3px 10px rgba(0,0,0,0.2);'>
            <div style='color: #006400; font-size: 18px; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px;'><i class="fas fa-water" style="margin-right: 8px;"></i>{row['Reservatório']}</div>
            <div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class="fas fa-calendar-alt" style="margin-right: 5px;"></i>Data:</span><span style='color: #333;'>{data_formatada}</span></div>
            <div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class="fas fa-city" style="margin-right: 5px;"></i>Município:</span><span style='color: #333;'>{row.get('Município', 'N/A')}</span></div>
            <div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class="fas fa-chart-bar" style="margin-right: 5px;"></i>Volume:</span><span style='color: #1a5276; font-weight: 500;'>{volume_str}</span></div>
            <div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class="fas fa-percentage" style="margin-right: 5px;"></i>Percentual:</span><span style='color: #27ae60; font-weight: 600;'>{percentual_str}</span></div>
            <div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class="fas fa-ruler" style="margin-right: 5px;"></i>Cota Sangria:</span><span style='color: #7d3c98; font-weight: 500;'>{cota_sangria_str} m</span></div>
        </div>
        """

        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.CustomIcon(
                create_svg_icon(icon_color),
                icon_size=(15, 15),
                icon_anchor=(7, 7)
            ),
            tooltip=f"{row['Reservatório']} - {data_formatada}"
        ).add_to(m)

    # Adiciona o controle de camadas e outros plugins
    folium.LayerControl().add_to(m)
    Fullscreen(position='topleft').add_to(m)
    MousePosition(position='bottomleft').add_to(m)

    folium_static(m, width=1200)
else:
    st.warning("Nenhum reservatório encontrado com os filtros aplicados.")

# ================================================================
# 📊 TABELA DE DADOS DETALHADOS INTERATIVOS
# ================================================================
st.subheader("📊 Dados Detalhados Interativos")

if not df_filtrado.empty:
    # Definir as faixas de percentual e cores
    faixas_percentual = [
        (0, 10, '#808080', 'Muito Crítica'),        # Cinza
        (10.1, 30, '#FF0000', 'Crítica'),            # Vermelho
        (30.1, 50, '#FFFF00', 'Alerta'),             # Amarelo
        (50.1, 70, '#008000', 'Confortável'),        # Verde
        (70.1, 100, '#0000FF', 'Muito Confortável'), # Azul
        (100.1, float('inf'), '#800080', 'Vertendo') # Roxo
    ]

    # Função para determinar cor e status com tratamento de NaN
    def get_status_color(percentual):
        if pd.isna(percentual):
            return '#FFFFFF', 'N/A', '#000000'
        for min_val, max_val, color, status in faixas_percentual:
            if min_val <= percentual <= max_val:
                text_color = '#FFFFFF' if color in ['#808080', '#FF0000', '#0000FF', '#800080'] else '#000000'
                return color, status, text_color
        return '#FFFFFF', 'Não classificado', '#000000'

    # Aplicar cores e status ao DataFrame para uso no estilismo
    df_filtrado[['Cor', 'Status', 'TextColor']] = df_filtrado['Percentual'].apply(
        lambda x: pd.Series(get_status_color(x))
    )

    # Calcular a coluna Sangria
    df_filtrado['Sangria'] = df_filtrado['Cota Sangria'] - df_filtrado['Nivel']

    # Ordem das colunas
    colunas_exibir = [
        'Data de Coleta', 'Reservatório', 'Município', 'Volume',
        'Percentual', 'Status', 'Cota Sangria', 'Nivel', 'Sangria'
    ]

    # Função para aplicar estilo condicional com cor de texto
    def colorize_row(row):
        idx = row.name
        bg_color = df_filtrado.loc[idx, 'Cor']
        text_color = df_filtrado.loc[idx, 'TextColor']
        return [f'background-color: {bg_color}; color: {text_color}; font-weight: bold;' for _ in row]

    # Aplicar estilo ao DataFrame
    styled_df = df_filtrado[colunas_exibir].copy().style.apply(colorize_row, axis=1)

    # Configuração das colunas, incluindo as formatações corretas
    column_config = {
        "Percentual": st.column_config.ProgressColumn(
            "Percentual",
            format="%.1f%%",
            min_value=0,
            max_value=100,
            help="Percentual de volume armazenado"
        ),
        "Volume": st.column_config.NumberColumn(
            "Volume",
            format="%.2f hm³",
            help="Volume armazenado em hectômetros cúbicos (hm³)"
        ),
        "Cota Sangria": st.column_config.NumberColumn(
            "Cota Sangria",
            format="%.2f m",
            help="Altura (em metros) do nível de sangria do reservatório"
        ),
        "Nivel": st.column_config.NumberColumn(
            "Nível",
            format="%.2f m",
            help="Altura atual (em metros) da lâmina d'água no reservatório"
        ),
        "Sangria": st.column_config.NumberColumn(
            "Margem de Sangria",
            format="%.2f m",
            help="Diferença (em metros) entre a cota de sangria e o nível atual"
        ),
        "Status": st.column_config.TextColumn(
            "Status",
            help="Classificação conforme o percentual de armazenamento"
        ),
        "Data de Coleta": st.column_config.DateColumn(
            "Data de Coleta",
            format="DD/MM/YYYY",
            help="Data da última medição"
        )
    }

    # Exibir tabela estilizada
    st.dataframe(
        styled_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_order=colunas_exibir
    )

    # Legenda interativa
    st.markdown("""
    <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 1px solid #ddd;">
        <h4 style="margin-bottom: 12px; color: #333; font-size: 16px;">Legenda de Status:</h4>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
    """ +
    '\n'.join([
        f"""<div style="display: flex; align-items: center; padding: 4px;">
            <div style="width: 24px; height: 24px; background: {color};
                    margin-right: 10px; border: 1px solid #ccc; border-radius: 4px;"></div>
            <span style="font-size: 14px;">{status} ({'≥' if min_val == 100.1 else ''}{min_val}-{'' if max_val == float('inf') else max_val}%)</span>
        </div>"""
        for min_val, max_val, color, status in faixas_percentual
    ]) +
    """
        </div>
    </div>
    """, unsafe_allow_html=True)
    
# ----------------------------------------------------------------------------------------------------------------------
# 📊 GRÁFICO DE LINHA DO VOLUME POR RESERVATÓRIO
# ----------------------------------------------------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📈 Volume dos Reservatórios ao Longo do Tempo")
    
    df_reservatorio = df_filtrado[df_filtrado['Reservatório'].isin(reservatorio_filtro)].sort_values('Data de Coleta')
    
    if not df_reservatorio.empty:
        df_reservatorio['Data de Coleta'] = df_reservatorio['Data de Coleta'].dt.date
        
        # --- Alterações para usar Altair ---
        # Definir a seleção para o scroll
        brush = alt.selection_interval(encodings=['x'])
        
        # Gráfico principal (com zoom)
        main_chart = alt.Chart(df_reservatorio).mark_line().encode(
            x=alt.X('Data de Coleta', axis=alt.Axis(title='Data')),
            y=alt.Y('Volume', axis=alt.Axis(title='Volume (hm³)')), # <-- Eixo Y com a unidade
            color='Reservatório:N',
            tooltip=['Data de Coleta', 'Reservatório', 'Volume']
        ).properties(
            title='Evolução do Volume',
            height=300
        ).add_selection(
            brush
        )
    
        # Gráfico de visão geral (o scrollbar)
        overview_chart = alt.Chart(df_reservatorio).mark_line().encode(
            x=alt.X('Data de Coleta', axis=None),
            y=alt.Y('Volume', title='Volume (hm³)', axis=None),
            color='Reservatório:N'
        ).properties(
            height=50
        ).add_selection(
            brush
        )
        
        # Combina os dois gráficos
        st.altair_chart(main_chart & overview_chart, use_container_width=True)
    else:
        st.warning(f"Não há dados de volume para o(s) reservatório(s) selecionado(s) no período.")
    
    st.markdown("---")
    
    # Botão de download
    with st.expander("📥 Opções de Download", expanded=False):
        st.download_button(
            label="Baixar dados completos (CSV)",
            data=df_filtrado.drop(columns=['Cor', 'Status', 'TextColor']).to_csv(index=False, encoding='utf-8-sig', sep=';'),
            file_name=f"reservatorios_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            help="Download com todos os dados numéricos originais"
        )
    
    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.", icon="⚠️")

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
    
#--------------------------RODAPÉ----------------------

st.markdown(f"""
<style>
.footer-mobile-full {{
    position: relative;
    width: 100vw; /* Usa a largura total da viewport */
    left: 50%; /* Posiciona a partir do meio */
    right: 50%; /* Posiciona a partir do meio */
    margin-left: -50vw; /* Compensa a posição */
    margin-right: -50vw; /* Compensa a posição */
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
}}
</style>

<div class="footer-mobile-full">
    <div class="footer-content">
        <div class="footer-row">
            <div class="footer-item">
                📞 (88) 99999-9999
            </div>
            <span class="footer-divider">|</span>
            <div class="footer-item">
                📧 vocedenuncia@qvocedenuncia
            </div>
            <span class="footer-divider">|</span>
            <div class="footer-item">
                <b>Plataforma Você Denuncia</b>
            </div>
        </div>
        <div class="footer-address">
            🏢 R. 14 de Agosto, 123 - Centro, Quixeramobim - CE, 63800-000
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
