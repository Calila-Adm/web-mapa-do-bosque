import streamlit as st
from src.data.bigquery_client import BigQueryClient
from src.wbr import gerar_grafico_wbr

# Initialize BigQuery client
bq_client = BigQueryClient()

# Fetch data from BigQuery via predefined SQL
df = bq_client.fetch_wbr_data()

st.title("WBR Overview")
st.subheader("Gráfico WBR (6 semanas + meses)")

if df is None or df.empty:
    st.info("Sem dados para exibir.")
else:
    fig = gerar_grafico_wbr(
        df,
        coluna_data="INSIRA A COLUNA DATA",
        coluna_pessoas="INSIRA A COLUNA METRICA",
        titulo="INSIRA O TÍTULO",
        unidade="INSIRA A UNIDADE",
    )
    st.plotly_chart(fig, use_container_width=True)