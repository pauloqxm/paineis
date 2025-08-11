import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from streamlit_folium import folium_static

# ---------------------- CONFIGURAÇÃO ----------------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# ---------------------- CARREGAR GEOJSON ----------------------
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

# ---------------------- FUNÇÕES ----------------------
def convert_vazao(series, unidade):
    """Converte L/s para m³/s se necessário."""
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

def carregar_dados():
    """Carrega os dados do Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
    df = pd.read_csv(url)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Mês'] = df['Data'].dt.to_period('M').astype(str)
    return df

# ---------------------- CABEÇALHO ----------------------
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; padding:10px; border-bottom:2px solid #ccc;">
    <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" style="height:50px;">
    <h2 style="margin:0; color:#003366;">Operação 2025.2</h2>
</div>
""", unsafe_allow_html=True)

# ---------------------- CARREGAR DADOS ----------------------
if 'df' not in st.session_state:
    st.session_state.df = carregar_dados()
if st.button("🔄 Atualizar dados agora"):
    with st.spinner('Atualizando dados...'):
        st.session_state.df = carregar_dados()
    st.rerun()
df = st.session_state.df

# ---------------------- FILTROS ----------------------
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
with col2:
    meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
with col3:
    datas_disp = df['Data'].dropna().sort_values()
    data_min, data_max = datas_disp.min(), datas_disp.max()
    intervalo_data = st.date_input("📅 Período", (data_min, data_max), format="DD/MM/YYYY")
with col4:
    unidade_sel = st.selectbox("🧪 Unidade de Vazão", ["L/s", "m³/s"], index=0)
with col5:
    mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
        "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
        "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
    ])

# ---------------------- FILTRO APLICADO ----------------------
df_filtrado = df.copy()
if estacoes:
    df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
if meses:
    df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
    inicio, fim = intervalo_data
    df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.to_datetime(inicio)) & (df_filtrado['Data'] <= pd.to_datetime(fim))]

# ---------------------- TABS ----------------------
tab1, tab2, tab3 = st.tabs(["📈 Séries Temporais", "🗺️ Mapa", "📊 Distribuição"])

# ===== TAB 1: Gráfico de Linhas =====
with tab1:
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    fig = go.Figure()
    cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

    reservatorios_filtrados = df_filtrado['Reservatório Monitorado'].unique()
    for i, reservatorio in enumerate(reservatorios_filtrados):
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values(by="Data")
        df_res = df_res.groupby('Data', as_index=False).last()
        y_vals, unit_suffix = convert_vazao(df_res["Vazão Operada"], unidade_sel)
        fig.add_trace(go.Scatter(
            x=df_res["Data"], y=y_vals,
            mode="lines+markers", name=reservatorio,
            line=dict(shape='hv', width=2, color=cores[i % len(cores)]),
            hovertemplate=f"<b>{reservatorio}</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
        ))

    # Média ponderada se houver 1 reservatório
    if len(reservatorios_filtrados) == 1:
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorios_filtrados[0]].sort_values(by="Data")
        df_res = df_res.groupby('Data', as_index=False).last()
        if len(df_res) > 1:
            df_res['dias_ativos'] = df_res['Data'].diff().dt.days.fillna(0)
            df_res.loc[df_res.index[-1], 'dias_ativos'] = (df_filtrado['Data'].max() - df_res['Data'].iloc[-1]).days + 1
            media_pond = (df_res['Vazão Operada'] * df_res['dias_ativos']).sum() / df_res['dias_ativos'].sum()
        else:
            media_pond = df_res['Vazão Operada'].iloc[0] if len(df_res) == 1 else 0
        media_pond, unit_suffix = convert_vazao(pd.Series([media_pond]), unidade_sel)
        fig.add_hline(y=media_pond.iloc[0], line_dash="dash", line_color="red",
                      annotation_text=f"Média: {media_pond.iloc[0]:.2f} {unit_suffix}",
                      annotation_position="top right")

    fig.update_layout(template="plotly_white", hovermode="closest")
    st.plotly_chart(fig, use_container_width=True)

# ===== TAB 2: Mapa =====
with tab2:
    st.subheader("🗺️ Mapa dos Reservatórios com Pinos")
    df_mapa = df_filtrado.copy()
    df_mapa[['lat', 'lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
    df_mapa = df_mapa.dropna(subset=['lat', 'lon']).drop_duplicates(subset=['Reservatório Monitorado'])

    if not df_mapa.empty:
        center = [df_mapa['lat'].mean(), df_mapa['lon'].mean()]
        m = folium.Map(location=center, zoom_start=8, tiles=mapa_tipo)

        folium.GeoJson(geojson_bacia, name="Bacia do Banabuiu").add_to(m)
        folium.GeoJson(geojson_trechos, name="Trechos Perenizados").add_to(m)
        folium.GeoJson(geojson_acudes, name="Açudes Monitorados").add_to(m)
        folium.GeoJson(geojson_poligno, name="Municípios").add_to(m)

        for _, row in df_mapa.iterrows():
            popup_info = f"<b>{row['Reservatório Monitorado']}</b><br>Data: {row['Data'].date()}<br>Vazão: {row['Vazão Operada']}"
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=popup_info
            ).add_to(m)
        folium.LayerControl().add_to(m)
        folium_static(m, width=1200)
    else:
        st.info("Nenhum ponto para exibir no mapa.")

# ===== TAB 3: Boxplot + Volume =====
with tab3:
    st.subheader("📊 Distribuição das Vazões por Reservatório")
    if "Volume Acumulado" in df_filtrado.columns and not df_filtrado.empty:
        soma_volume = df_filtrado["Volume Acumulado"].sum()
        st.markdown(
            f"""
            <div style="background: linear-gradient(90deg, #00b4d8, #0077b6);
                        padding: 12px; border-radius: 8px; color: white;
                        font-size: 16px; font-weight: bold; text-align: center;">
                💦 Volume acumulado no período: {soma_volume:,.2f} m³
            </div>
            """,
            unsafe_allow_html=True
        )

    if not df_filtrado.empty:
        fig_box = px.box(
            df_filtrado, x="Reservatório Monitorado", y="Vazão Operada",
            points="all", color="Reservatório Monitorado"
        )
        fig_box.update_layout(template="plotly_white", showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para o filtro selecionado.")
