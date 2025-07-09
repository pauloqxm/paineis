
import streamlit as st
import pandas as pd
import plotly.express as px

# 🔒 Proteção por senha
def check_password():
    def password_entered():
        if st.session_state["password"] == "minhasenha123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔒 Digite a senha para acessar", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("❌ Senha incorreta. Tente novamente", type="password", on_change=password_entered, key="password")
        st.stop()

check_password()

# 🌐 Estilo CSS para deixar a barra lateral azul
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    </style>
    """, unsafe_allow_html=True)

# ⚙️ Configuração da página
st.set_page_config(page_title="Dashboard de Diárias", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel('DIARIAS.xlsx', sheet_name='DIARIAS')
    df['Data Inicio'] = pd.to_datetime(df['Data Inicio'])
    df['Data Fim'] = pd.to_datetime(df['Data Fim'])
    df['Mês'] = df['Data Inicio'].dt.to_period('M').astype(str)
    return df

df = load_data()

st.title("📊 Dashboard de Diárias")

# 📌 Filtros
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

# 📊 Indicadores
col1, col2 = st.columns(2)
col1.metric("🧾 Total de Diárias", df_filtrado['Qtde'].sum())
col2.metric("💰 Valor Total (R$)", f"{df_filtrado['Valor Total'].sum():,.2f}")

# 📈 Gráficos
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

# 📋 Tabela
st.subheader("📋 Detalhamento das Diárias")
st.dataframe(df_filtrado.sort_values(by='Data Inicio', ascending=False), use_container_width=True)
