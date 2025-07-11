
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
st.set_page_config(page_title="Dashboard de Diárias e Frota", layout="wide")

# 📁 Menu lateral para navegação
aba = st.sidebar.radio("📌 Selecione uma aba:", ["Diárias", "Controle de Frota"])

if aba == "Diárias":
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

elif aba == "Controle de Frota":
    @st.cache_data
    def load_data_frota():
        return pd.read_excel('CONTROLE_FROTA.xlsx')

    st.title("🚗 Controle de Frota")
    df_frota = load_data_frota()

    st.dataframe(df_frota, use_container_width=True)
