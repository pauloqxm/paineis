import streamlit as st
import pandas as pd
import plotly.express as px

# 🌐 Estilo CSS para deixar a barra lateral azul
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    </style>
    """, unsafe_allow_html=True)

# ⚙️ Configuração da página
st.set_page_config(page_title="Dashboard Integrado", layout="wide")

# Menu lateral para selecionar a aba
aba = st.sidebar.radio("📁 Selecione uma aba:", ["📊 Dashboard de Diárias", "🚗 Controle de Frota"])

# ===============================
# 📊 ABA 1: DASHBOARD DE DIÁRIAS
# ===============================
if aba == "📊 Dashboard de Diárias":
    @st.cache_data
    def load_data_diarias():
        df = pd.read_excel('DIARIAS.xlsx', sheet_name='DIARIAS')
        df['Data Inicio'] = pd.to_datetime(df['Data Inicio'])
        df['Data Fim'] = pd.to_datetime(df['Data Fim'])
        df['Mês'] = df['Data Inicio'].dt.to_period('M').astype(str)
        return df

    df = load_data_diarias()

    st.title("📊 Dashboard de Diárias")

    with st.sidebar:
        st.header("🧰 Filtros")
        solicitantes = st.multiselect("🧑‍💼 Solicitante", df['Solicitante'].unique())
        gerencias = st.multiselect("🏢 Gerência", df['Gerencia'].unique())
        meses = st.multiselect("🗓️ Mês", df['Mês'].unique())
        destinos = st.multiselect("📍 Destino", df['Destino'].unique())

    df_filtrado = df.copy()
    if solicitantes:
        df_filtrado = df_filtrado[df_filtrado['Solicitante'].isin(solicitantes)]
    if gerencias:
        df_filtrado = df_filtrado[df_filtrado['Gerencia'].isin(gerencias)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
    if destinos:
        df_filtrado = df_filtrado[df_filtrado['Destino'].isin(destinos)]

    col1, col2 = st.columns(2)
    col1.metric("🧾 Total de Diárias", df_filtrado['Qtde'].sum())
    col2.metric("💰 Valor Total (R$)", f"{df_filtrado['Valor Total'].sum():,.2f}")

    st.subheader("💼 Valor por Gerência")
    st.plotly_chart(px.bar(df_filtrado.groupby('Gerencia')['Valor Total'].sum().reset_index(),
                           x='Gerencia', y='Valor Total', text_auto='.2s'), use_container_width=True)

    st.subheader("📅 Valor por Mês")
    st.plotly_chart(px.bar(df_filtrado.groupby('Mês')['Valor Total'].sum().reset_index(),
                           x='Mês', y='Valor Total', text_auto='.2s'), use_container_width=True)

    st.subheader("🧑‍💼 Valor por Solicitante")
    st.plotly_chart(px.bar(df_filtrado.groupby('Solicitante')['Valor Total'].sum().reset_index().sort_values(by='Valor Total'),
                           x='Valor Total', y='Solicitante', orientation='h', text_auto='.2s'), use_container_width=True)

    st.subheader("🗺️ Destinos (Gráfico de Pizza)")
    st.plotly_chart(px.pie(df_filtrado, names='Destino', values='Qtde', hole=0.3), use_container_width=True)

    st.subheader("📋 Detalhamento das Diárias")
    st.dataframe(df_filtrado.sort_values(by='Data Inicio', ascending=False), use_container_width=True)

# ===============================
# 🚗 ABA 2: CONTROLE DE FROTA
# ===============================
elif aba == "🚗 Controle de Frota":
    @st.cache_data
    def load_frota():
        df_frota = pd.read_excel('BASE_FROTA.xlsx')
        df_frota['Data'] = pd.to_datetime(df_frota['Data'], errors='coerce')
        df_frota['Mês'] = df_frota['Data'].dt.to_period('M').astype(str)
        return df_frota

    df_frota = load_frota()

    st.title("🚗 Controle de Frota")

    with st.sidebar:
        st.header("🚙 Filtros da Frota")
        veiculos = st.multiselect("🚗 Veículo", df_frota['Veículo'].dropna().unique())
        combustivel = st.multiselect("⛽ Tipo de Combustível", df_frota['Combustível'].dropna().unique())
        meses_frota = st.multiselect("🗓️ Mês", df_frota['Mês'].dropna().unique())

    df_frota_filtrado = df_frota.copy()
    if veiculos:
        df_frota_filtrado = df_frota_filtrado[df_frota_filtrado['Veículo'].isin(veiculos)]
    if combustivel:
        df_frota_filtrado = df_frota_filtrado[df_frota_filtrado['Combustível'].isin(combustivel)]
    if meses_frota:
        df_frota_filtrado = df_frota_filtrado[df_frota_filtrado['Mês'].isin(meses_frota)]

    st.subheader("💰 Gastos por Veículo")
    st.plotly_chart(px.bar(df_frota_filtrado.groupby('Veículo')['Custo'].sum().reset_index(),
                           x='Veículo', y='Custo', text_auto='.2s'), use_container_width=True)

    st.subheader("⛽ Tipos de Combustível")
    st.plotly_chart(px.pie(df_frota_filtrado, names='Combustível', values='Custo', hole=0.3), use_container_width=True)

    st.subheader("📉 Gastos Mensais")
    st.plotly_chart(px.line(df_frota_filtrado.groupby('Mês')['Custo'].sum().reset_index(),
                            x='Mês', y='Custo', markers=True), use_container_width=True)

    st.subheader("📋 Detalhamento da Frota")
    st.dataframe(df_frota_filtrado.sort_values(by='Data', ascending=False), use_container_width=True)
