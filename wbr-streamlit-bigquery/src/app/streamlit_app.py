import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from src.utils.env import load_environment_variables
from src.data.bigquery_client import BigQueryClient
from src.wbr import gerar_grafico_wbr

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, '..'))
load_environment_variables(base_dir=PROJECT_ROOT)  # Carrega .env do root do app

# Normalize credential path to absolute (if relative)
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if cred_path and not os.path.isabs(cred_path):
    abs_path = os.path.join(PROJECT_ROOT, cred_path)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path

# Initialize the BigQuery client
bq_client = BigQueryClient()

st.set_page_config(page_title="WBR Dashboard", layout="wide")
st.title("WBR Dashboard")

with st.sidebar:
    st.header("Parâmetros")
    coluna_data = st.text_input("Coluna de data", value="INSIRA A COLUNA DATA")
    coluna_metrica = st.text_input("Coluna métrica", value="INSIRA A COLUNA METRICA")
    titulo = st.text_input("Título", value="INSIRA O TÍTULO")
    unidade = st.text_input("Unidade", value="INSIRA A UNIDADE")
    data_ref = st.date_input("Data de referência")
    st.markdown("---")
    st.caption("Conexão BigQuery")
    bq_project = st.text_input("Project ID", value=os.getenv("BIGQUERY_PROJECT_ID", ""))
    bq_dataset = st.text_input("Dataset", value=os.getenv("BIGQUERY_DATASET", ""))
    bq_table = st.text_input("Table", value=os.getenv("BIGQUERY_TABLE", ""))

@st.cache_data(show_spinner=True)
def load_wbr_data(project_id: str, dataset: str, table: str):
    return bq_client.fetch_wbr_data(project_id=project_id, dataset=dataset, table=table)

if not bq_project or not bq_dataset or not bq_table:
    st.warning("Defina Project/Dataset/Table do BigQuery na barra lateral.")
    df = None
else:
    df = load_wbr_data(bq_project, bq_dataset, bq_table)

if df is None or df.empty:
    st.warning("Sem dados do BigQuery.")
else:
    fig = gerar_grafico_wbr(
        df,
        coluna_data=coluna_data,
        coluna_pessoas=coluna_metrica,
        titulo=titulo,
        unidade=unidade,
        data_referencia=data_ref.isoformat() if data_ref else None,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Dados carregados do BigQuery usando a consulta em src/data/queries/wbr.sql")