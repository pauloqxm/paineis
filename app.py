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
.header-container{{max-width:1200px;margin:0 auto;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px}}
.header-brand{{display:flex;align-items:center;gap:10px;flex:1;min-width:200px}}
.header-logo{{height:36px;filter:drop-shadow(0 2px 2px rgba(0,0,0,.2))}}
.header-title{{font-size:clamp(14px,3vw,18px);font-weight:600;letter-spacing:.5px;text-shadow:0 1px 3px rgba(0,0,0,.3)}}
.header-date{{background:rgba(255,255,255,.15);padding:4px 10px;border-radius:20px;font-size:clamp(10px,2.5vw,13px);font-weight:500;display:flex;align-items:center;gap:6px;backdrop-filter:blur(5px);white-space:nowrap}}
.main .block-container{{padding-top:90px}}
/* cartão dos filtros */
.filter-card{{border:1px solid #e6e6e6;border-radius:14px;padding:12px 16px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.06);margin-top:6px}}
.filter-title{{font-weight:600;margin-bottom:6px}}
.quick-chips span{{display:inline-block;border:1px solid #dcdcdc;border-radius:999px;padding:4px 10px;margin-right:6px;margin-top:4px;cursor:pointer;font-size:12px}}
.quick-chips span:hover{{background:#f5f5f5}}
.kpi-card{{border:1px solid #eaeaea;border-radius:14px;padding:14px;background:linear-gradient(180deg,#ffffff 0%, #fafafa 100%);box-shadow:0 6px 16px rgba(0,0,0,.06);text-align:center}}
.kpi-value{{font-size:22px;font-weight:700;margin-top:4px}}
@media(max-width:600px){{
 .main .block-container{{padding-top:110px}}
}}
</style>
<div class="custom-header">
  <div class="header-container">
    <div class="header-brand">
      <img src="https://cdn-icons-png.flaticon.com/512/1006/1006363.png" class="header-logo">
      <div>
        <div class="header-title">Você Fiscaliza | Quixeramobim - CE</div>
        <div style="opacity:.9;font-size:13px">📌 Monitoramento de Recursos Públicos</div>
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
tab1, tab2 = st.tabs(["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"])

with tab1:
    # dados
    df = carregar_dados()

    # barra de ações
    cA1, cA2, cA3 = st.columns([1,1,2])
    with cA1:
        if st.button("🔄 Atualizar agora"):
            carregar_dados.clear()
            df = carregar_dados()
            st.success("Atualizado.")
    with cA2:
        st.download_button("⬇️ Baixar CSV filtrado", df.to_csv(index=False).encode("utf-8"), file_name="vazoes.csv", mime="text/csv")

    st.title("💧 Vazões - GRBANABUIU")

    # --------- FILTROS ----------
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<div class="filter-title">Filtros</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        estacoes = st.multiselect("🏞️ Reservatório", df['Reservatório Monitorado'].dropna().unique())
    with col2:
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
    with col3:
        datas_disponiveis = df['Data'].dropna().sort_values()
        data_min = datas_disponiveis.min()
        data_max = datas_disponiveis.max()
        intervalo_data = st.date_input("📅 Intervalo", (data_min, data_max), format="DD/MM/YYYY")
    with col4:
        unidade_sel = st.selectbox("🧪 Unidade", ["L/s", "m³/s"], index=0)
        mapa_tipo = st.selectbox("🗺️ Estilo do mapa",
                                 ["OpenStreetMap","Stamen Terrain","Stamen Toner","CartoDB positron","CartoDB dark_matter","Esri Satellite"],
                                 index=0)
    # chips de período rápido
    cchip1, cchip2 = st.columns([3,1])
    with cchip1:
        st.markdown(
            '<div class="quick-chips">'
            '<span id="p30">Últimos 30 dias</span>'
            '<span id="p90">Últimos 90 dias</span>'
            '<span id="p365">Últimos 12 meses</span>'
            '</div>',
            unsafe_allow_html=True
        )
    with cchip2:
        st.caption("Dica: clique nos chips para ajustar rápido ⤴️")

    st.markdown('</div>', unsafe_allow_html=True)

    # aplica chips (via query_params simples)
    qs = st.query_params
    if "chip" in qs:
        chip = qs["chip"]
        fim = data_max if pd.notna(data_max) else pd.Timestamp.today()
        if chip == "30": intervalo_data = (fim - pd.Timedelta(days=30), fim)
        if chip == "90": intervalo_data = (fim - pd.Timedelta(days=90), fim)
        if chip == "365": intervalo_data = (fim - pd.Timedelta(days=365), fim)

    # filtro no df
    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(inicio)) &
                                  (df_filtrado['Data'] <= pd.to_datetime(fim))]

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="kpi-card">Reservatórios<br><div class="kpi-value">{}</div></div>'.format(
            df_filtrado['Reservatório Monitorado'].nunique()), unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card">Registros<br><div class="kpi-value">{}</div></div>'.format(
            len(df_filtrado)), unsafe_allow_html=True)
    with k3:
        if not df_filtrado.empty:
            ult = df_filtrado['Data'].max()
            ult_txt = ult.strftime("%d/%m/%Y")
        else:
            ult_txt = "—"
        st.markdown(f'<div class="kpi-card">Última data<br><div class="kpi-value">{ult_txt}</div></div>', unsafe_allow_html=True)
    with k4:
        unidade_show = "m³/s" if unidade_sel == "m³/s" else "L/s"
        st.markdown(f'<div class="kpi-card">Unidade<br><div class="kpi-value">{unidade_show}</div></div>', unsafe_allow_html=True)

    # --------- GRÁFICOS ----------
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
        
        # Adiciona linha da média ponderada apenas se houver apenas um reservatório selecionado
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
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1a", step="year", stepmode="backward"),
                    dict(step="all", label="Tudo")
                ])
            )
        )
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    # abas extras de análise
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
        
        # Cálculo do volume acumulado
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
            
            volume_formatado = f"{volume_total/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " Mm³"
            
            volumes.append({
                'Reservatório Monitorado': reservatorio,
                'Volume Acumulado': volume_total/1e6,  # Já em milhões de m³
                'Volume Formatado': volume_formatado
            })
        
        df_volumes = pd.DataFrame(volumes)
        
        # Criar figura simples com volume no eixo Y
        figb = px.bar(
            df_volumes,
            x='Reservatório Monitorado',
            y='Volume Acumulado',
            text='Volume Formatado',
            labels={'Volume Acumulado': 'Volume Acumulado (Mm³)'},
            title='Volumes Acumulados por Reservatório'
        )
        
        # Ajustar formatação
        figb.update_traces(
            textposition='outside',
            marker_color='#1f77b4',
            textfont=dict(size=12, color='black')
        )
        
        figb.update_layout(
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            yaxis=dict(
                title='Volume Acumulado (Mm³)',
                titlefont=dict(size=14)
            ),
            xaxis=dict(
                title='Reservatório',
                titlefont=dict(size=14)
            )
        )
        
        st.plotly_chart(figb, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Sem dados suficientes para exibir os volumes.")

    # -------------------- MAPA --------------------
    st.subheader("🗺️ Mapa dos Reservatórios com Camadas")
    df_mapa = df_filtrado.copy()
    if 'Coordendas' in df_mapa.columns:
        df_mapa[['lat','lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
    df_mapa = df_mapa.dropna(subset=['lat','lon']).drop_duplicates(subset=['Reservatório Monitorado'])

    tile_urls = {"Esri Satellite":"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"}
    tile_attr = {"Esri Satellite":"Tiles © Esri"}

    if not df_mapa.empty:
        center = [df_mapa['lat'].mean(), df_mapa['lon'].mean()]
        if mapa_tipo in tile_urls:
            m = folium.Map(location=center, zoom_start=8, tiles=None)
            folium.TileLayer(tiles=tile_urls[mapa_tipo], attr=tile_attr[mapa_tipo], name=mapa_tipo).add_to(m)
        else:
            m = folium.Map(location=center, zoom_start=8, tiles=mapa_tipo)

        # plugins
        Fullscreen(position='topleft').add_to(m)
        MiniMap(toggle_display=True, minimized=True).add_to(m)
        MousePosition(position='bottomleft', separator=' | ', prefix='Coords').add_to(m)
        MeasureControl(primary_length_unit='meters').add_to(m)

        # camadas
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
<strong>Célula Gestora:</strong> {nome_g}<br>
<strong>Ano de Formação:</strong> {props.get("ANOFORMA1","N/A")}<br>
<strong>Sistema:</strong> {props.get("SISTEMAH3","N/A")}<br>
<strong>Município:</strong> {props.get("MUNICIPI6","N/A")}
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

        # pinos reservatórios com cluster
        cluster = MarkerCluster(name="Reservatórios (pinos)").add_to(m)
        for _, row in df_mapa.iterrows():
            try:
                val = float(row.get('Vazao_Aloc', float('nan')))
            except Exception:
                val = float('nan')
            val_conv, unit_suf = convert_vazao(pd.Series([val]), unidade_sel)
            val_txt = f"{val_conv.iloc[0]:.3f} {unit_suf}" if pd.notna(val_conv.iloc[0]) else "—"
            data_txt = row['Data'].date() if pd.notna(row['Data']) else "—"
            popup_info = f"<strong>Reservatório:</strong> {row['Reservatório Monitorado']}<br><strong>Data:</strong> {data_txt}<br><strong>Vazão Alocada:</strong> {val_txt}"
            folium.Marker([row["lat"], row["lon"]],
                          popup=folium.Popup(popup_info, max_width=300),
                          icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30,30)),
                          tooltip=row["Reservatório Monitorado"]).add_to(cluster)

        folium.LayerControl(collapsed=True, position='topright').add_to(m)
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
    tile_option = st.selectbox("🗺️ Estilo do Mapa (Açudes)",
                               ["OpenStreetMap","Stamen Terrain","Stamen Toner","CartoDB positron","CartoDB dark_matter","Esri Satellite"],
                               key="acudes_map_tile")
    tile_urls = {"Esri Satellite":"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"}
    tile_attr = {"Esri Satellite":"Tiles © Esri"}

    with open("Açudes_Monitorados.geojson", "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    center = [-5.2, -39.2]
    if tile_option in tile_urls:
        m2 = folium.Map(location=center, zoom_start=7, tiles=None)
        folium.TileLayer(tiles=tile_urls[tile_option], attr=tile_attr[tile_option], name=tile_option).add_to(m2)
    else:
        m2 = folium.Map(location=center, zoom_start=7, tiles=tile_option)

    folium.GeoJson(geojson_data, name="Açudes",
                   tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"])).add_to(m2)
    folium.LayerControl(collapsed=True).add_to(m2)
    folium_static(m2, width=None)

# --------- JS simples para acionar chips ajustando query param ---------
st.markdown("""
<script>
const setChip = (val) => {
  const url = new URL(window.location);
  url.searchParams.set('chip', val);
  window.location.href = url.toString();
}
document.getElementById('p30')?.addEventListener('click', ()=>setChip('30'));
document.getElementById('p90')?.addEventListener('click', ()=>setChip('90'));
document.getElementById('p365')?.addEventListener('click', ()=>setChip('365'));
</script>
""", unsafe_allow_html=True)
