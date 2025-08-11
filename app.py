import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
import datetime
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta, timezone

# Carregar arquivos GeoJSON
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

# Configuração da página
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# -------- Cabeçalho Personalizado --------
fuso_brasilia = timezone(timedelta(hours=-3))
agora = datetime.now(fuso_brasilia)

dias_semana = {
    'Monday': 'Segunda-feira',
    'Tuesday': 'Terça-feira',
    'Wednesday': 'Quarta-feira',
    'Thursday': 'Quinta-feira',
    'Friday': 'Sexta-feira',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}

meses = {
    'January': 'janeiro',
    'February': 'fevereiro',
    'March': 'março',
    'April': 'abril',
    'May': 'maio',
    'June': 'junho',
    'July': 'julho',
    'August': 'agosto',
    'September': 'setembro',
    'October': 'outubro',
    'November': 'novembro',
    'December': 'dezembro'
}

dia_semana = dias_semana[agora.strftime('%A')]
mes = meses[agora.strftime('%B')]
data_hoje = f"{dia_semana}, {agora.day:02d} de {mes} de {agora.year}"

st.markdown(f"""
    <style>
    [data-testid="stHeader"] {{
        visibility: hidden;
    }}

    .custom-header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(135deg, #228B22 0%, #006400 50%, #004d00 100%);
        color: white;
        padding: 12px 5%;
        font-family: 'Segoe UI', Roboto, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 9999;
    }}

    /* ... (outros estilos do cabeçalho) ... */
    </style>

    <div class="custom-header">
        <!-- ... (conteúdo do cabeçalho) ... -->
    </div>
""", unsafe_allow_html=True)

# -------- Menu Social com Filtros Modernos --------
st.markdown("""
    <style>
    /* Estilos do menu social */
    .social-menu-container {
        /* ... (estilos existentes) ... */
    }
    
    /* Estilos dos filtros modernos */
    .modern-filters {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    .filter-card {
        background: white;
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        border: 1px solid rgba(0, 0, 0, 0.03);
        transition: all 0.2s ease;
    }
    
    .filter-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* ... (outros estilos CSS) ... */
    </style>
""", unsafe_allow_html=True)

# Container dos filtros modernos
with st.container():
    st.markdown('<div class="modern-filters">', unsafe_allow_html=True)
    
    # Carregar dados
    @st.cache_data
    def carregar_dados():
        url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
        df = pd.read_csv(url)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mês'] = df['Data'].dt.to_period('M').astype(str)
        return df

    if 'df' not in st.session_state:
        st.session_state.df = carregar_dados()
    df = st.session_state.df

    # Linha 1 - Filtros principais
    cols = st.columns([1, 1, 1, 1])
    
    with cols[0]:
        with st.container():
            st.markdown('<div class="filter-card">', unsafe_allow_html=True)
            reservatorios = st.multiselect(
                "🏞️ Reservatórios",
                options=df['Reservatório Monitorado'].dropna().unique(),
                default=df['Reservatório Monitorado'].dropna().unique()[0:1],
                key="filtro_reservatorios"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[1]:
        with st.container():
            st.markdown('<div class="filter-card">', unsafe_allow_html=True)
            acudes = st.multiselect(
                "🏞️ Açudes Monitorados",
                options=df['Açude Monitorado'].dropna().unique(),
                default=df['Açude Monitorado'].dropna().unique()[0:1],
                key="filtro_acudes"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[2]:
        with st.container():
            st.markdown('<div class="filter-card">', unsafe_allow_html=True)
            unidade_sel = st.selectbox(
                "🧪 Unidade",
                options=["L/s", "m³/s"],
                index=0,
                key="filtro_unidade"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    with cols[3]:
        with st.container():
            st.markdown('<div class="filter-card">', unsafe_allow_html=True)
            mapa_tipo = st.selectbox(
                "🗺️ Estilo do Mapa",
                options=["OpenStreetMap", "Stamen Terrain", "Stamen Toner", 
                        "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
                index=0,
                key="filtro_mapa"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Linha 2 - Filtro de data e botão
    cols2 = st.columns([3, 1])
    
    with cols2[0]:
        with st.container():
            st.markdown('<div class="filter-card">', unsafe_allow_html=True)
            datas_disponiveis = df['Data'].dropna().sort_values()
            data_min = datas_disponiveis.min()
            data_max = datas_disponiveis.max()
            intervalo_data = st.date_input(
                "📅 Período",
                value=(data_min, data_max),
                format="DD/MM/YYYY",
                key="filtro_data"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    with cols2[1]:
        with st.container():
            st.markdown('<div class="filter-card" style="display: flex; align-items: flex-end; height: 100%;">', unsafe_allow_html=True)
            if st.button("🔄 Atualizar Dados", use_container_width=True):
                with st.spinner('Atualizando...'):
                    st.session_state.df = carregar_dados()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# -------- Funções Utilitárias --------
def convert_vazao(series, unidade):
    """Converte entre L/s e m³/s"""
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

# -------- Abas Principais --------
tab1, tab2 = st.tabs(["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"])

with tab1:
    st.title("💧 Vazões - GRBANABUIU")

    # Aplicar filtros
    df_filtrado = df.copy()
    if reservatorios:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(reservatorios)]
    if acudes:
        df_filtrado = df_filtrado[df_filtrado['Açude Monitorado'].isin(acudes)]
    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[
            (df_filtrado['Data'] >= pd.to_datetime(inicio)) &
            (df_filtrado['Data'] <= pd.to_datetime(fim))
        ]

    # ... (restante do código das visualizações da aba 1) ...

with tab2:
    st.title("🗺️ Açudes Monitorados")
    # ... (código da aba 2) ...
