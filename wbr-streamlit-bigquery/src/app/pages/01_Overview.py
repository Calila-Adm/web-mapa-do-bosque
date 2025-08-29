import os
import sys
import streamlit as st
from src.utils.env import load_environment_variables
from src.data.bigquery_client import BigQueryClient
from src.wbr import gerar_grafico_wbr

# Ensure project root is on path and envs are loaded
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
load_environment_variables(base_dir=PROJECT_ROOT)

# Initialize BigQuery client
bq_client = BigQueryClient()

st.title("WBR Overview")
st.subheader("Gráfico WBR (6 semanas + meses)")

with st.sidebar:
    st.caption("Conexão BigQuery (Overview)")
    bq_project = st.text_input("Project ID", value=os.getenv("BIGQUERY_PROJECT_ID", ""))
    bq_dataset = st.text_input("Dataset", value=os.getenv("BIGQUERY_DATASET", ""))

    default_table = os.getenv("BIGQUERY_TABLE", "")
    if default_table and default_table.count('.') >= 1:
        default_table = default_table.split('.')[-1]

    tables = []
    @st.cache_data(ttl=600, show_spinner=False)
    def list_tables_cached(project_id: str, dataset: str):
        return BigQueryClient().list_tables(project_id=project_id, dataset=dataset)

    if bq_project and bq_dataset:
        try:
            tables = list_tables_cached(bq_project, bq_dataset)
        except Exception as e:
            st.caption(f"Não foi possível listar tabelas: {e}")

    if tables:
        idx = tables.index(default_table) if default_table in tables else 0
        bq_table = st.selectbox("Table", options=tables, index=idx)
    else:
        bq_table = st.text_input("Table", value=os.getenv("BIGQUERY_TABLE", ""))

    coluna_data = st.text_input("Coluna de data", value=os.getenv("WBR_DATE_COL", ""))
    coluna_metrica = st.text_input("Coluna métrica", value=os.getenv("WBR_METRIC_COL", ""))

@st.cache_data(show_spinner=True)
def load_wbr_data(project_id: str, dataset: str, table: str, date_col: str | None, metric_col: str | None):
    if not date_col or not metric_col:
        inferred = bq_client.infer_wbr_columns(project_id=project_id, dataset=dataset, table=table)
        date_col = date_col or inferred[0]
        metric_col = metric_col or inferred[1]
    return bq_client.fetch_wbr_data(project_id=project_id, dataset=dataset, table=table, date_col=date_col, metric_col=metric_col)

if not bq_project or not bq_dataset or not bq_table:
    st.info("Defina Project/Dataset/Table para carregar os dados.")
    df = None
else:
    df = load_wbr_data(bq_project, bq_dataset, bq_table, coluna_data or None, coluna_metrica or None)

if df is None or df.empty:
    st.info("Sem dados para exibir.")
else:
    # O DataFrame tem colunas 'date' e 'metric_value' pela SQL
    fig = gerar_grafico_wbr(
        df,
        coluna_data="date",
        coluna_pessoas="metric_value",
        titulo="INSIRA O TÍTULO",
        unidade="INSIRA A UNIDADE",
    )
    st.plotly_chart(fig, use_container_width=True)