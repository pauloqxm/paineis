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

# Load GeoJSON files
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

# Configure page
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# -------- Data Loading --------
@st.cache_data
def carregar_dados():
    """Load data from Google Sheets"""
    url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
    df = pd.read_csv(url)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Mês'] = df['Data'].dt.to_period('M').astype(str)
    return df

df = carregar_dados()

# -------- Header with Date --------
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

    .header-container {{
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .header-brand {{
        display: flex;
        align-items: center;
        gap: 15px;
    }}

    .header-logo {{
        height: 40px;
        filter: drop-shadow(0 2px 2px rgba(0,0,0,0.2));
    }}

    .header-title {{
        font-size: 18px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }}

    .header-date {{
        background: rgba(255,255,255,0.15);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
        backdrop-filter: blur(5px);
    }}

    .main .block-container {{
        padding-top: 90px;
    }}
    </style>

    <div class="custom-header">
        <div class="header-container">
            <div class="header-brand">
                <img src="https://cdn-icons-png.flaticon.com/512/1006/1006363.png" class="header-logo">
                <div>
                    <div class="header-title">Você Fiscaliza | Quixeramobim - CE</div>
                </div>
            </div>
            <div class="header-date">
                📅 {data_hoje}
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# -------- Social Menu with Filters --------
st.markdown(f"""
    <style>
    .social-menu-container {{
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        width: 100vw;
        background-color: #04a5c9;
        color: white;
        padding: 6px 32px;
        font-family: Tahoma, sans-serif;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        margin-top: -40px;
        border-bottom: 3px solid #b6b8ba;
        z-index: 1;
    }}

    .social-links {{
        display: flex;
        gap: 30px;
    }}

    .social-menu-container a {{
        color: white;
        text-decoration: none;
        transition: color 0.3s ease;
    }}

    .social-menu-container a:hover {{
        color: #fad905;
    }}

    .menu-toggle {{
        display: none;
        cursor: pointer;
        padding: 5px;
    }}

    .menu-icon {{
        display: inline-block;
        width: 25px;
        height: 3px;
        background-color: white;
        position: relative;
    }}

    .menu-icon:before, .menu-icon:after {{
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        background-color: white;
    }}

    .menu-icon:before {{
        top: -8px;
    }}

    .menu-icon:after {{
        top: 8px;
    }}

    .filters-dropdown {{
        width: 100%;
        padding: 10px 0;
        background-color: #038db5;
    }}

    .filter-group {{
        margin-bottom: 10px;
    }}

    .filter-label {{
        color: white;
        font-weight: bold;
        margin-right: 10px;
        font-size: 13px;
    }}

    @media (max-width: 768px) {{
        .social-links {{
            display: none;
        }}
        
        .menu-toggle {{
            display: block;
        }}
        
        .social-menu-container {{
            flex-direction: column;
            align-items: flex-start;
            padding: 10px 20px;
        }}
        
        .filters-dropdown {{
            display: none;
        }}
        
        .filters-dropdown.show {{
            display: block;
        }}
    }}

    @media (min-width: 769px) {{
        .filters-dropdown {{
            display: block !important;
        }}
    }}
    </style>

    <div class="social-menu-container">
        <div class="social-links">
            <a href="https://www.instagram.com/seuusuario" target="_blank">📸 Instagram</a>
            <a href="https://www.facebook.com/seuusuario" target="_blank">📘 Facebook</a>
            <a href="https://wa.me/5588999999999" target="_blank">💬 WhatsApp</a>
        </div>
        
        <div class="menu-toggle" onclick="toggleFilters()">
            <div class="menu-icon"></div>
        </div>
        
        <div class="filters-dropdown" id="filtersDropdown">
            <div class="filter-group">
                <span class="filter-label">🏞️ Reservatórios:</span>
            </div>
            <div class="filter-group">
                <span class="filter-label">🏞️ Açudes Monitorados:</span>
            </div>
        </div>
    </div>

    <script>
    function toggleFilters() {{
        var dropdown = document.getElementById('filtersDropdown');
        dropdown.classList.toggle('show');
    }}
    </script>
""", unsafe_allow_html=True)

# Add filters below the menu
col1, col2 = st.columns(2)

with col1:
    reservatorios = st.multiselect(
        "Selecione os reservatórios:",
        options=df['Reservatório Monitorado'].dropna().unique(),
        default=df['Reservatório Monitorado'].dropna().unique()[0:1],
        key="filtro_reservatorios",
        label_visibility="collapsed"
    )

with col2:
    acudes = st.multiselect(
        "Selecione os açudes:",
        options=df['Açude Monitorado'].dropna().unique(),
        default=df['Açude Monitorado'].dropna().unique()[0:1],
        key="filtro_acudes",
        label_visibility="collapsed"
    )

# -------- Utility Functions --------
def convert_vazao(series, unidade):
    """Convert flow units between L/s and m³/s"""
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

# -------- Main Tabs --------
tab1, tab2 = st.tabs(["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"])

with tab1:
    if st.button("🔄 Atualizar dados agora"):
        with st.spinner('Atualizando dados...'):
            df = carregar_dados()
        st.rerun()
    
    st.title("💧 Vazões - GRBANABUIU")

    # Filter data based on selections
    df_filtrado = df.copy()
    if reservatorios:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(reservatorios)]
    if acudes:
        df_filtrado = df_filtrado[df_filtrado['Açude Monitorado'].isin(acudes)]

    # Add date filter
    datas_disponiveis = df_filtrado['Data'].dropna().sort_values()
    data_min = datas_disponiveis.min()
    data_max = datas_disponiveis.max()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        intervalo_data = st.date_input("📅 Intervalo de Datas", (data_min, data_max), format="DD/MM/YYYY")
    with col2:
        unidade_sel = st.selectbox("🧪 Unidade de Vazão", ["L/s", "m³/s"], index=0)
    with col3:
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
            "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
            "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
        ], index=0)

    if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
        inicio, fim = intervalo_data
        df_filtrado = df_filtrado[
            (df_filtrado['Data'] >= pd.to_datetime(inicio)) &
            (df_filtrado['Data'] <= pd.to_datetime(fim))
        ]

    # Flow evolution chart
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    fig = go.Figure()
    cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for i, reservatorio in enumerate(df_filtrado['Reservatório Monitorado'].unique()):
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values(by="Data")
        df_res = df_res.groupby('Data', as_index=False).last()

        y_vals, unit_suffix = convert_vazao(df_res["Vazão Operada"], unidade_sel)

        fig.add_trace(go.Scatter(
            x=df_res["Data"],
            y=y_vals,
            mode="lines+markers",
            name=reservatorio,
            line=dict(shape='hv', width=2, color=cores[i % len(cores)]),
            marker=dict(size=5),
            hovertemplate=(
                f"<b>{reservatorio}</b><br>"
                "Data: %{x|%d/%m/%Y}<br>"
                f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
            )
        ))

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title=f"Vazão Operada ({'m³/s' if unidade_sel=='m³/s' else 'L/s'})",
        legend_title="Reservatório",
        template="plotly_white",
        hovermode="closest",
        margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor='white'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Map visualization
    st.subheader("🗺️ Mapa dos Reservatórios com Pinos")
    df_mapa = df_filtrado.copy()
    df_mapa[['lat', 'lon']] = df_mapa['Coordendas'].str.split(',', expand=True).astype(float)
    df_mapa = df_mapa.dropna(subset=['lat', 'lon']).drop_duplicates(subset=['Reservatório Monitorado'])

    if not df_mapa.empty:
        center = [df_mapa['lat'].mean(), df_mapa['lon'].mean()]
        m = folium.Map(location=center, zoom_start=8, tiles=mapa_tipo)

        # Add all your GeoJSON layers here...
        folium.GeoJson(
            geojson_bacia,
            name="Bacia do Banabuiu",
            style_function=lambda x: {"color": "darkblue", "weight": 2}
        ).add_to(m)

        # Add markers for reservoirs
        for _, row in df_mapa.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=row["Reservatório Monitorado"],
                icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30))
            ).add_to(m)

        folium.LayerControl().add_to(m)
        folium_static(m, width=1200)
    else:
        st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

    # Average flow bar chart
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
    media_conv, unit_bar = convert_vazao(media_vazao["Vazão Operada"], unidade_sel)
    
    st.plotly_chart(
        px.bar(
            media_vazao,
            x="Reservatório Monitorado",
            y=media_conv,
            labels={"y": f"Média ({unit_bar})"}
        ),
        use_container_width=True
    )

    # Data table
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)

with tab2:
    st.title("🗺️ Açudes Monitorados")
    
    # Add your açudes monitoring content here...
    # This would include similar visualizations but focused on açudes
