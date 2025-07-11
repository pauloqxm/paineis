import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

# 🌐 Estilo da barra lateral
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #e0f0ff;
    }
    </style>
    """, unsafe_allow_html=True)

# ⚙️ Configuração
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# 📁 Menu lateral
with st.sidebar:
    aba = option_menu(
        menu_title="Painel",
        options=["Vazões - GRBANABUIU"],
        icons=["droplet"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

if aba == "Vazões - GRBANABUIU":
    @st.cache_data
    def load_data():
        df = pd.read_excel("GRBANABUIU_VAZÕES.xlsx")
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['Mês'] = df['Data'].dt.to_period('M').astype(str)
        return df

    df = load_data()

    st.title("💧 Vazões - GRBANABUIU")

    with st.sidebar:
        st.header("🔎 Filtros")
        estacoes = st.multiselect("🏞️ Reservatório Monitorado", df['Reservatório Monitorado'].dropna().unique())
        meses = st.multiselect("📆 Mês", df['Mês'].dropna().unique())

    df_filtrado = df.copy()
    if estacoes:
        df_filtrado = df_filtrado[df_filtrado['Reservatório Monitorado'].isin(estacoes)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(meses)]

    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    st.plotly_chart(
        px.line(
            df_filtrado,
            x="Data",
            y="Vazão Operada",
            color="Reservatório Monitorado",
            markers=True
        ),
        use_container_width=True
    )

    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
    st.plotly_chart(
        px.bar(
            media_vazao,
            x="Reservatório Monitorado",
            y="Vazão Operada",
            text_auto='.2s'
        ),
        use_container_width=True
    )

    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)
