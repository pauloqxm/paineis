
import streamlit as st
import pandas as pd
import plotly.express as px

# Configurações iniciais
st.set_page_config(page_title="Dashboard de Diárias", layout="wide")

# Carregar os dados
@st.cache_data
def load_data():
    url = 'DIARIAS.xlsx'
    df = pd.read_excel(url, sheet_name='DIARIAS')
    df['Data Inicio'] = pd.to_datetime(df['Data Inicio'])
    df['Data Fim'] = pd.to_datetime(df['Data Fim'])
    df['Mês'] = df['Data Inicio'].dt.to_period('M').astype(str)
    return df

df = load_data()

st.title("📊 Dashboard de Diárias")

# Filtros com ícones
with st.sidebar:
    st.header("🧰 Filtros")
    solicitantes = st.multiselect("🧑‍💼 Solicitante", df['Solicitante'].unique())
    gerencias = st.multiselect("🏢 Gerência", df['Gerencia'].unique())
    meses = st.multiselect("🗓️ Mês", df['Mês'].unique())
    destinos = st.multiselect("📍 Destino", df['Destino'].unique())

# Aplicar filtros
df_filtrado = df.copy()
if solicitantes:
    df_filtrado = df_filtrado[df_filtrado['Solicitante'].isin(solicitantes)]
if gerencias:
    df_filtrado = df_filtrado[df_filtrado['Gerencia'].isin(gerencias)]
if meses:
    df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]
if destinos:
    df_filtrado = df_filtrado[df_filtrado['Destino'].isin(destinos)]

# KPIs
total_diarias = df_filtrado['Qtde'].sum()
valor_total = df_filtrado['Valor Total'].sum()

st.markdown("### 📌 Visão Geral")
col1, col2 = st.columns(2)
col1.metric("🧾 Total de Diárias", total_diarias)
col2.metric("💰 Valor Total (R$)", f"{valor_total:,.2f}")

# Gráfico de barras - Valor por Gerência
st.markdown("### 💼 Valor Total por Gerência")
grafico1 = px.bar(df_filtrado.groupby('Gerencia')['Valor Total'].sum().reset_index(),
                  x='Gerencia', y='Valor Total', text_auto='.2s', title='')
st.plotly_chart(grafico1, use_container_width=True)

# Gráfico de barras - Valor por Mês
st.markdown("### 📅 Valor Total por Mês")
grafico2 = px.bar(df_filtrado.groupby('Mês')['Valor Total'].sum().reset_index(),
                  x='Mês', y='Valor Total', text_auto='.2s', title='')
st.plotly_chart(grafico2, use_container_width=True)

# Gráfico de barras - Valor por Solicitante
st.markdown("### 🧑‍💼 Valor Total por Solicitante")
grafico3 = px.bar(df_filtrado.groupby('Solicitante')['Valor Total'].sum().reset_index().sort_values(by='Valor Total', ascending=False),
                  x='Valor Total', y='Solicitante', orientation='h', text_auto='.2s', title='')
st.plotly_chart(grafico3, use_container_width=True)

# Gráfico de pizza - Distribuição de Diárias por Destino
st.markdown("### 🗺️ Distribuição de Diárias por Destino")
grafico_pizza = px.pie(df_filtrado, names='Destino', values='Qtde',
                       title='Proporção de Diárias por Destino',
                       hole=0.3)  # deixa com estilo de rosquinha
st.plotly_chart(grafico_pizza, use_container_width=True)

# Tabela
st.markdown("### 📋 Detalhamento das Diárias")
st.dataframe(df_filtrado.sort_values(by='Data Inicio', ascending=False), use_container_width=True)
