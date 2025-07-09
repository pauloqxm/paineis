
import streamlit as st
import pandas as pd
import plotly.express as px

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

# Filtros
st.sidebar.header("Filtros")
solicitantes = st.sidebar.multiselect("Solicitante", df['Solicitante'].unique())
gerencias = st.sidebar.multiselect("Gerência", df['Gerencia'].unique())
meses = st.sidebar.multiselect("Mês", df['Mês'].unique())
destinos = st.sidebar.multiselect("Destino", df['Destino'].unique())

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

col1, col2 = st.columns(2)
col1.metric("Total de Diárias", total_diarias)
col2.metric("Valor Total (R$)", f"{valor_total:,.2f}")

# Gráfico de barras - Valor por Gerência
st.subheader("💼 Valor Total por Gerência")
grafico1 = px.bar(df_filtrado.groupby('Gerencia')['Valor Total'].sum().reset_index(),
                  x='Gerencia', y='Valor Total', title='', text_auto='.2s')
st.plotly_chart(grafico1, use_container_width=True)

# Gráfico de barras - Valor por Mês
st.subheader("📅 Valor Total por Mês")
grafico2 = px.bar(df_filtrado.groupby('Mês')['Valor Total'].sum().reset_index(),
                  x='Mês', y='Valor Total', title='', text_auto='.2s')
st.plotly_chart(grafico2, use_container_width=True)

# Gráfico de barras - Valor por Solicitante
st.subheader("🧑‍💼 Valor Total por Solicitante")
grafico3 = px.bar(df_filtrado.groupby('Solicitante')['Valor Total'].sum().reset_index().sort_values(by='Valor Total', ascending=False),
                  x='Valor Total', y='Solicitante', orientation='h', text_auto='.2s')
st.plotly_chart(grafico3, use_container_width=True)

# Tabela de dados
st.subheader("📋 Detalhamento das Diárias")
st.dataframe(df_filtrado.sort_values(by='Data Inicio', ascending=False))
