import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from datetime import datetime, timedelta, timezone
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MiniMap, MousePosition, MeasureControl, MarkerCluster

# ---------------- CONFIG GERAL ----------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# ---------------- UTILS - FUNÇÕES REUTILIZÁVEIS ----------------

@st.cache_data(ttl=3600)
def load_geojson(file_path):
    """Carrega arquivos GeoJSON com cache."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=300)
def carregar_dados():
    """
    Carrega e pré-processa os dados da planilha.
    Usa caching para evitar múltiplas chamadas.
    """
    url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
    df = pd.read_csv(url)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Mês'] = df['Data'].dt.to_period('M').astype(str)
    # Extrai coordenadas no carregamento para evitar reprocessamento
    if 'Coordendas' in df.columns:
        df[['lat', 'lon']] = df['Coordendas'].str.split(',', expand=True).astype(float)
    return df

def convert_vazao(series, unidade):
    """Converte valores de vazão de L/s para m³/s ou vice-versa."""
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

def get_current_date():
    """Retorna a data e hora formatadas para o cabeçalho."""
    fuso_brasilia = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_brasilia)
    dias_semana = {'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira', 'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
    meses = {'January': 'janeiro', 'February': 'fevereiro', 'March': 'março', 'April': 'abril', 'May': 'maio', 'June': 'junho', 'July': 'julho', 'August': 'agosto', 'September': 'setembro', 'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'}
    return f"{dias_semana[agora.strftime('%A')]}, {agora.day:02d} de {meses[agora.strftime('%B')]} de {agora.year}"

# Refatora a criação do mapa Folium em uma função
def create_folium_map(center, zoom, tile_option, tile_urls, tile_attr, layers):
    """Gera um mapa Folium com camadas pré-definidas e plugins."""
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)

    # Adiciona a camada base
    if tile_option == "OpenStreetMap":
        folium.TileLayer(tiles='OpenStreetMap').add_to(m)
    else:
        folium.TileLayer(
            tiles=tile_urls[tile_option],
            attr=tile_attr[tile_option],
            name=tile_option
        ).add_to(m)

    # Adiciona plugins
    Fullscreen(position='topleft').add_to(m)
    MiniMap(toggle_display=True, minimized=True).add_to(m)
    MousePosition(position='bottomleft', separator=' | ', prefix='Coords').add_to(m)
    MeasureControl(primary_length_unit='meters').add_to(m)

    # Adiciona camadas GeoJSON
    for layer in layers:
        folium.GeoJson(layer['data'], name=layer['name'], tooltip=layer.get('tooltip'), style_function=layer.get('style')).add_to(m)
    
    folium.LayerControl(collapsed=True, position='topright').add_to(m)
    return m

# ---------------- ARQUIVOS GEOJSON (com caching) ----------------
geojson_trechos = load_geojson("trechos_perene.geojson")
geojson_acudes = load_geojson("Açudes_Monitorados.geojson")
geojson_sedes = load_geojson("Sedes_Municipais.geojson")
geojson_c_gestoras = load_geojson("c_gestoras.geojson")
geojson_poligno = load_geojson("poligno_municipios.geojson")
geojson_bacia = load_geojson("bacia_banabuiu.geojson")
geojson_pontos = load_geojson("pontos_controle.geojson")

# ---------------- TOPO CUSTOM ----------------
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
.custom-title{{font-family: 'Segoe UI', Roboto, sans-serif !important;font-size: 20px !important;font-weight: 700 !important;color: #006400 !important;text-align: center !important;margin: 8px 0 10px 0 !important;padding: 12px 22px !important;position: relative !important;display: flex !important;align-items: center !important;justify-content: center !important;gap: 8px !important;background: rgba(144, 238, 144, 0.15) !important;border-radius: 8px !important;box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;}}
.custom-title::before, .custom-title::after{{content: "" !important;flex: 1 !important;height: 2px !important;background: linear-gradient(90deg, transparent, #228B22) !important;border-radius: 2px !important;}}
.custom-title::after{{background: linear-gradient(90deg, #228B22, transparent) !important;}}
.custom-title span{{display: inline-flex !important;align-items: center !important;justify-content: center !important;font-size: 18px !important;}}
@media (max-width: 600px){{.custom-title{{flex-direction: column !important;gap: 4px !important;padding: 6px 12px !important;}}.custom-title::before, .custom-title::after{{width: 70% !important;height: 1.5px !important;}}}}
.kpi-container{{display: flex;gap: 16px;margin: -20px 0;flex-wrap: wrap;justify-content: space-between;}}
.kpi-card{{flex: 1;min-width: 180px;background: linear-gradient(135deg, #e0f5ec, #b2dfdb);border-radius: 12px;padding: 16px;box-shadow: 0 3px 8px rgba(0,0,0,0.08);text-align: center;transition: transform 0.2s ease, box-shadow 0.2s ease;}}
.kpi-card:hover{{transform: translateY(-3px);box-shadow: 0 5px 15px rgba(0,0,0,0.15);}}
.kpi-label{{font-size: 14px;font-weight: 600;color: #004d40;margin-bottom: 6px;text-transform: uppercase;letter-spacing: 0.5px;}}
.kpi-value{{font-size: 24px;font-weight: 700;color: #00695c;}}
@media (max-width: 768px){{.kpi-container{{flex-direction: column;}}}}
.map-style-selector {{margin-top: -10px;}}
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
    <div class="header-date">📅 {get_current_date()}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"])

with tab1:
    # dados
    df = carregar_dados()

    # Botão de atualização na área principal
    if st.button("🔄 Atualizar agora"):
        carregar_dados.clear()
        df = carregar_dados()
        st.success("Dados atualizados com sucesso!")

    st.markdown("""
    <h1 class="custom-title">
        <span>💧</span> Painel de Vazões
    </h1>
    """, unsafe_allow_html=True)

    # --------- FILTROS (AGORA EM MENU HAMBURGUER) ----------   
    with st.expander("☰ Filtros", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            estacoes = st.multiselect("🏞️ Reservatório", df['Reservatório Monitorado'].dropna().unique())
        with col2:
            operacao = st.multiselect("🔧 Operação", df['Operação'].dropna().unique())
        with col3:
            meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        with col4:
            datas_disponiveis = df['Data'].dropna().sort_values()
            data_min = datas_disponiveis.min()
            data_max = datas_disponiveis.max()
            intervalo_data = st.date_input("📅 Intervalo", (data_min, data_max), format="DD/MM/YYYY")
    
    unidade_sel = st.selectbox("🧪 Unidade de Medida", ["L/s", "m³/s"], index=0, help="Selecione a unidade de vazão para os gráficos.")

    # Aplicar filtros no dataframe
    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if operacao:
        df_filtrado = df_filtrado[df_filtrado['Operação'].isin(operacao)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(inicio)) & (df_filtrado['Data'] <= pd.to_datetime(fim))]

    # --- KPIs Modernos ---
    reservatorios_count = df_filtrado['Reservatório Monitorado'].nunique()
    registros_count = len(df_filtrado)
    ultima_data = df_filtrado['Data'].max().strftime("%d/%m/%Y") if not df_filtrado.empty and pd.notna(df_filtrado['Data'].max()) else "—"
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

    # --------- GRÁFICOS ----------
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    if not df_filtrado.empty:
        fig = go.Figure()
        cores = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#17becf','#e377c2']
        reservatorios = df_filtrado['Reservatório Monitorado'].dropna().unique()
        
        for i, r in enumerate(reservatorios):
            dfr = (df_filtrado[df_filtrado['Reservatório Monitorado'] == r].sort_values('Data').groupby('Data', as_index=False).last())
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
            xaxis_title="Data", yaxis_title=f"Vazão Operada ({unit_suffix})", legend_title="Reservatório",
            template="plotly_white", margin=dict(l=40, r=20, t=10, b=40),
            xaxis=dict(rangeslider=dict(visible=True, thickness=0.1, bgcolor='#f5f5f5'), rangeselector=None)
        )
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Sem dados para a evolução da vazão. Ajuste os filtros.")

    # Abas extras de análise
    gtab1, gtab2, gtab3 = st.tabs(["📊 Média mensal", "📦 Distribuição (boxplot)", "📈 Volume Acumulado"])
    
    with gtab1:
        if not df_filtrado.empty:
            dmm = (df_filtrado.assign(mes_num=df_filtrado['Data'].dt.to_period('M').astype(str)).groupby(['Reservatório Monitorado','mes_num'], as_index=False)['Vazão Operada'].mean())
            yconv, sufx = convert_vazao(dmm['Vazão Operada'], unidade_sel)
            dmm['Vazão (conv)'] = yconv
            figm = px.bar(dmm, x='mes_num', y='Vazão (conv)', color='Reservatório Monitorado',
                          labels={'mes_num':'Mês','Vazão (conv)':f'Média ({sufx})'}, barmode='group')
            st.plotly_chart(figm, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sem dados para média mensal.")
            
    with gtab2:
        if not df_filtrado.empty and df_filtrado['Reservatório Monitorado'].nunique() > 0:
            yconv, sufx = convert_vazao(df_filtrado['Vazão Operada'], unidade_sel)
            df_box = df_filtrado.copy()
            df_box['Vazão (conv)'] = yconv
            
            figb = go.Figure()
            for r in df_box['Reservatório Monitorado'].unique():
                figb.add_trace(go.Box(
                    y=df_box[df_box['Reservatório Monitorado'] == r]['Vazão (conv)'],
                    name=r, boxpoints='all', jitter=0.5, pointpos=0, marker_color='#1f77b4', line_color='#1f77b4'
                ))
            
            figb.update_layout(
                title='Distribuição de Vazões', xaxis_title='Reservatório', yaxis_title=f'Vazão Operada ({sufx})',
                showlegend=False
            )
            st.plotly_chart(figb, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sem dados suficientes para boxplot.")

    with gtab3:
        if not df_filtrado.empty and df_filtrado['Reservatório Monitorado'].nunique() > 0:
            yconv, _ = convert_vazao(df_filtrado['Vazão Operada'], unidade_sel)
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
                
                volumes.append({'Reservatório Monitorado': reservatorio, 'Volume Acumulado': volume_total, 'Volume Formatado': volume_formatado})
            
            df_volumes = pd.DataFrame(volumes)

            fig_volume = px.bar(
                df_volumes,
                x='Reservatório Monitorado',
                y='Volume Acumulado',
                title='Volume Acumulado por Reservatório',
                labels={'Volume Acumulado': 'Volume Acumulado (m³)'},
                text=df_volumes['Volume Formatado']
            )

            fig_volume.update_layout(
                xaxis_title='Reservatório',
                yaxis_title='Volume Acumulado (m³)'
            )
            
            st.plotly_chart(fig_volume, use_container_width=True)

        else:
            st.info("Sem dados suficientes para calcular o volume acumulado.")


    # -------------------- MAPA --------------------
    st.subheader("🗺️ Mapa dos Reservatórios com Camadas")
    df_mapa = df_filtrado.dropna(subset=['lat', 'lon']).drop_duplicates(subset=['Reservatório Monitorado'])

    with st.expander("☰ Estilo do Mapa", expanded=False):
        mapa_tipo = st.selectbox(
            "Selecione o estilo:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0, key="map_style_selector", label_visibility="collapsed"
        )

    tile_urls = {
        "OpenStreetMap": None, "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
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
        
        # Define as camadas a serem passadas para a função do mapa
        map_layers = [
            {'data': geojson_bacia, 'name': "Bacia do Banabuiu", 'tooltip': folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]), 'style': lambda x: {"color": "darkblue", "weight": 2}},
            {'data': geojson_trechos, 'name': "Trechos Perenizados", 'tooltip': folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]), 'style': lambda x: {"color": "darkblue", "weight": 1}},
            {'data': geojson_pontos, 'name': "Pontos de Controle", 'tooltip': folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]), 'style': None},
            {'data': geojson_acudes, 'name': "Açudes Monitorados", 'tooltip': folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]), 'style': lambda x: {"color": "darkgreen", "weight": 2}},
            {'data': geojson_sedes, 'name': "Sedes Municipais", 'tooltip': folium.GeoJsonTooltip(fields=["NOME_MUNIC"], aliases=["Município:"]), 'style': None},
            {'data': geojson_c_gestoras, 'name': "Comissões Gestoras", 'tooltip': folium.GeoJsonTooltip(fields=["SISTEMAH3"], aliases=["Sistema:"]), 'style': None},
            {'data': geojson_poligno, 'name': "Polígonos Municipais", 'tooltip': folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]), 'style': lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}}
        ]
        
        m = create_folium_map(center, 8, mapa_tipo, tile_urls, tile_attr, map_layers)

        # Adiciona os pinos de reservatórios com cluster
        cluster = MarkerCluster(name="Reservatórios (pinos)").add_to(m)
        for _, row in df_mapa.iterrows():
            val = float(row.get('Vazao_Aloc', float('nan')))
            val_conv, unit_suf = convert_vazao(pd.Series([val]), unidade_sel)
            val_txt = f"{val_conv.iloc[0]:.3f} {unit_suf}" if pd.notna(val_conv.iloc[0]) else "—"
            data_txt = row['Data'].date().strftime("%d/%m/%Y") if pd.notna(row['Data']) else "—"
            
            popup_info = f"""
            <div style='font-family: "Segoe UI", Arial, sans-serif;padding: 12px;background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);border-radius: 8px;box-shadow: 0 4px 12px rgba(0,0,0,0.15);border-left: 4px solid #228B22;min-width: 220px;'>
                <div style='font-size: 16px;font-weight: 600;color: #2c3e50;margin-bottom: 8px;border-bottom: 1px solid #dfe6e9;padding-bottom: 6px;'>{row['Reservatório Monitorado']}</div>
                <div style='margin-bottom: 4px;'><span style='display: inline-block;width: 100px;font-weight: 500;color: #7f8c8d;'>Data:</span><span style='color: #2c3e50;'>{data_txt}</span></div>
                <div style='margin-bottom: 4px;'><span style='display: inline-block;width: 100px;font-weight: 500;color: #7f8c8d;'>Vazão:</span><span style='color: #228B22;font-weight: 600;'>{val_txt}</span></div>
                <div style='margin-top: 8px;font-size: 12px;color: #7f8c8d;text-align: right;'>Sistema de Monitoramento</div>
            </div>"""
            folium.Marker(
                [row["lat"], row["lon"]],
                popup=folium.Popup(popup_info, max_width=300),
                icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)),
                tooltip=row["Reservatório Monitorado"]
            ).add_to(cluster)

        folium_static(m, width=1200)
    else:
        st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

    # --------- MÉDIA POR RESERVATÓRIO + TABELA ----------
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

with tab2:
    st.title("🗺️ Açudes Monitorados")
    
    with st.expander("☰ Estilo do Mapa", expanded=False):
        tile_option = st.selectbox(
            "Selecione o estilo:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            key="acudes_map_tile", label_visibility="collapsed"
        )
    
    tile_urls = {
        "OpenStreetMap": None, "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
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
    
    center_acudes = [-5.2, -39.2]
    
    # Camadas para a segunda aba (apenas açudes)
    acudes_layer_tab2 = [{'data': geojson_acudes, 'name': "Açudes", 'tooltip': folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])}]
    
    m2 = create_folium_map(center_acudes, 7, tile_option, tile_urls, tile_attr, acudes_layer_tab2)
    folium_static(m2, width=1200)
