import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu

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

# Page configuration
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    .fixed-header {
        background-color: #e0f0ff;
        padding: 10px 20px;
        border-bottom: 2px solid #ccc;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    </style>
    <div class="fixed-header">
        <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" alt="Logo COGERH" style="height: 50px;">
        <h2 style="margin: 0; color: #003366;">Operação 2025.2</h2>
    </div>
""", unsafe_allow_html=True)

# Navigation menu
with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU", "🗺️ Açudes Monitorados"],
        icons=["droplet", "map"],
        menu_icon="cast",
        default_index=0
    )

# Flow conversion function
def convert_vazao(series, unidade):
    """Convert flow values between L/s and m³/s (input em L/s, retorna (valores, sufixo))"""
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

if aba == "Vazões - GRBANABUIU":
    @st.cache_data
    def load_data():
        """Load flow data from Google Sheets"""
        url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
        df = pd.read_csv(url)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mês'] = df['Data'].dt.to_period('M').astype(str)
        return df

    df = load_data()

    st.title("💧 Vazões - GRBANABUIU")

    # Filters
    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())
        data_min, data_max = df['Data'].min(), df['Data'].max()
        inicio, fim = st.date_input("📅 Intervalo de Datas", [data_min, data_max])
        unidade_sel = st.selectbox("🧪 Unidade de Vazão", ["L/s", "m³/s"])
        mapa_tipo = st.selectbox("🗺️ Estilo do Mapa", [
            "OpenStreetMap", "Stamen Terrain", "Stamen Toner",
            "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"
        ])

    # Apply filters
    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    df_filtrado = df_filtrado[
        (df_filtrado['Data'] >= pd.to_datetime(inicio)) & 
        (df_filtrado['Data'] <= pd.to_datetime(fim))
    ]

    # Time series chart
    st.subheader("📈 Evolução da Vazão Operada")
    
    fig = go.Figure()
    cores = px.colors.qualitative.Plotly
    y_unit = "m³/s" if unidade_sel == "m³/s" else "L/s"  # evita 'unit' indefinido

    for i, reservatorio in enumerate(df_filtrado['Reservatório Monitorado'].dropna().unique()):
        df_res = df_filtrado[df_filtrado['Reservatório Monitorado'] == reservatorio].sort_values('Data')
        # remove duplicatas por dia, mantendo o último registro
        df_res = df_res.groupby('Data', as_index=False).last()
        
        y_vals, unit = convert_vazao(df_res['Vazão Operada'], unidade_sel)
        
        fig.add_trace(go.Scatter(
            x=df_res['Data'],
            y=y_vals,
            mode='lines+markers',
            name=reservatorio,
            line=dict(shape='hv', width=2, color=cores[i % len(cores)]),
            marker=dict(size=6),
            hovertemplate=(
                f"<b>{reservatorio}</b><br>"
                "Data: %{x|%d/%m/%Y}<br>"
                f"Vazão: %{{y:.2f}} {unit}<extra></extra>"
            )
        ))

    fig.update_layout(
        xaxis_title='Data',
        yaxis_title=f'Vazão Operada ({y_unit})',
        template='plotly_white',
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Interactive map
    st.subheader("🗺️ Mapa dos Reservatórios")
    
    # Prepare map data
    df_mapa = df_filtrado.copy()
    # lida com "lat, lon" com espaços
    df_mapa[['lat', 'lon']] = df_mapa['Coordendas'].str.split(',', expand=True)
    df_mapa['lat'] = pd.to_numeric(df_mapa['lat'].str.strip(), errors='coerce')
    df_mapa['lon'] = pd.to_numeric(df_mapa['lon'].str.strip(), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['lat', 'lon']).drop_duplicates('Reservatório Monitorado')

    if not df_mapa.empty:
        # Base map configuration
        m = folium.Map(
            location=[df_mapa['lat'].mean(), df_mapa['lon'].mean()],
            zoom_start=8,
            tiles=mapa_tipo if mapa_tipo not in ['Esri Satellite'] else None,
            control_scale=True
        )
        
        # Add special tile layer if needed
        if mapa_tipo == 'Esri Satellite':
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satélite'
            ).add_to(m)

        # 1. Watershed layer
        folium.GeoJson(
            geojson_bacia,
            name='Bacia do Banabuiú',
            style_function=lambda x: {
                'fillColor': '#1E90FF',
                'color': 'darkblue',
                'weight': 2,
                'fillOpacity': 0.1
            },
            tooltip=folium.GeoJsonTooltip(fields=['DESCRICA1'], aliases=['Bacia:'])
        ).add_to(m)

        # 2. Perennial streams
        folium.GeoJson(
            geojson_trechos,
            name='Trechos Perenizados',
            style_function=lambda x: {
                'color': '#4682B4',
                'weight': 3,
                'dashArray': '5, 5'
            },
            tooltip=folium.GeoJsonTooltip(fields=['Name'], aliases=['Trecho:'])
        ).add_to(m)

        # 3. Monitored reservoirs
        folium.GeoJson(
            geojson_acudes,
            name='Açudes Monitorados',
            style_function=lambda x: {
                'color': '#006400',
                'weight': 2,
                'fillColor': '#7CFC00',
                'fillOpacity': 0.3
            },
            tooltip=folium.GeoJsonTooltip(fields=['Name', 'Capacidade'], aliases=['Açude:', 'Capacidade (m³):'])
        ).add_to(m)

        # 4. Municipal boundaries
        folium.GeoJson(
            geojson_poligno,
            name='Municípios',
            style_function=lambda x: {
                'color': 'blue',
                'weight': 1,
                'fillOpacity': 0.1
            },
            tooltip=folium.GeoJsonTooltip(fields=['DESCRICA1'], aliases=['Município:'])
        ).add_to(m)

        # 5. Control points
        for feature in geojson_pontos['features']:
            coords = feature['geometry']['coordinates']
            nome = feature['properties']['Name']
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.CustomIcon('https://i.ibb.co/HfCcFWjb/marker.png', icon_size=(22, 22)),
                tooltip=nome,
                popup=f'<b>Ponto de Controle:</b> {nome}'
            ).add_to(m)

        # 6. Municipal seats
        for feature in geojson_sedes['features']:
            coords = feature['geometry']['coordinates']
            nome = feature['properties']['NOME_MUNIC']
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.CustomIcon('https://cdn-icons-png.flaticon.com/512/854/854878.png', icon_size=(22, 22)),
                tooltip=nome,
                popup=f'<b>Sede Municipal:</b> {nome}'
            ).add_to(m)

        # 7. Management committees
        for feature in geojson_c_gestoras['features']:
            coords = feature['geometry']['coordinates']
            props = feature['properties']
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.CustomIcon('https://cdn-icons-png.flaticon.com/512/4144/4144517.png', icon_size=(30, 30)),
                tooltip=props['SISTEMAH3'],
                popup=f"""
                <b>Comissão Gestora:</b> {props['SISTEMAH3']}<br>
                <b>Município:</b> {props['MUNICIPI6']}<br>
                <b>Ano de Formação:</b> {props['ANOFORMA1']}
                """
            ).add_to(m)

        # 8. Monitored reservoirs (points)
        for _, row in df_mapa.iterrows():
            vazao, unit = convert_vazao(pd.Series([row['Vazão Operada']]), unidade_sel)
            folium.Marker(
                location=[row['lat'], row['lon']],
                icon=folium.CustomIcon('https://i.ibb.co/kvvL870/hydro-dam.png', icon_size=(30, 30)),
                tooltip=row['Reservatório Monitorado'],
                popup=f"""
                <b>Reservatório:</b> {row['Reservatório Monitorado']}<br>
                <b>Vazão:</b> {vazao.iloc[0]:.2f} {unit}<br>
                <b>Data:</b> {row['Data'].strftime('%d/%m/%Y')}
                """
            ).add_to(m)

        # Layer control
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Display map with error handling
        try:
            folium_static(m, width=1200)
        except Exception as e:
            st.warning(f"Erro ao renderizar mapa: {str(e)}")
            st.components.v1.html(m._repr_html_(), width=1200, height=600)
    else:
        st.warning("Nenhum dado disponível para exibir no mapa.")

    # ---------------- Média PONDERADA por reservatório (corrigida) ----------------
    st.subheader("📊 Média Ponderada por Reservatório")

    # usamos o período do filtro (inicio, fim) para ponderar corretamente até o fim do intervalo
    periodo_fim = pd.to_datetime(fim)

    def calcular_media_ponderada(grp):
        g = grp.sort_values('Data').copy()
        # remove duplicatas por dia (último valor)
        g = g.groupby('Data', as_index=False).last()
        if g.empty:
            return 0.0
        # próxima data (para duração do patamar)
        g['prox_data'] = g['Data'].shift(-1)
        g.loc[g.index[-1], 'prox_data'] = periodo_fim  # último patamar vai até o fim do intervalo
        # duração em dias (inclusivo no último dia do patamar)
        g['dias'] = (g['prox_data'] - g['Data']).dt.days
        g.loc[g['dias'] < 0, 'dias'] = 0  # segurança
        # média ponderada
        numerador = (g['Vazão Operada'] * g['dias']).sum()
        denominador = g['dias'].sum()
        return float(numerador / denominador) if denominador > 0 else 0.0

    medias = (df_filtrado.groupby('Reservatório Monitorado', as_index=True)
              .apply(calcular_media_ponderada)
              .reset_index(name='Média Ponderada (L/s)'))

    # converte para unidade escolhida
    medias['Média Conv'], unit_bar = convert_vazao(medias['Média Ponderada (L/s)'], unidade_sel)

    fig_bar = px.bar(
        medias,
        x='Reservatório Monitorado',
        y='Média Conv',
        text_auto='.2f',
        labels={'Reservatório Monitorado': 'Reservatório', 'Média Conv': f'Média Ponderada ({unit_bar})'},
        color='Reservatório Monitorado',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Data table
    st.subheader("📋 Dados Completos")
    st.dataframe(df_filtrado.sort_values('Data', ascending=False), use_container_width=True)

elif aba == "🗺️ Açudes Monitorados":
    st.title("🗺️ Açudes Monitorados")
    
    m = folium.Map(location=[-5.2, -39.2], zoom_start=7)
    folium.GeoJson(
        geojson_acudes,
        name='Açudes',
        style_function=lambda x: {
            'color': '#006400',
            'weight': 2,
            'fillColor': '#7CFC00',
            'fillOpacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(fields=['Name', 'Capacidade'], aliases=['Açude:', 'Capacidade (m³):'])
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    try:
        folium_static(m, width=1200)
    except Exception as e:
        st.warning(f"Erro ao renderizar mapa: {str(e)}")
        st.components.v1.html(m._repr_html_(), width=1200, height=600)
