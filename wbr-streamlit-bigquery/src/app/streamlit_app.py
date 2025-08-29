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
    titulo = st.text_input("Título", value="INSIRA O TÍTULO")
    unidade = st.text_input("Unidade", value="INSIRA A UNIDADE")
    data_ref = st.date_input("Data de referência")
    st.markdown("---")
    st.caption("Conexão BigQuery")
    bq_project = st.text_input("Project ID", value=os.getenv("BIGQUERY_PROJECT_ID", ""))
    bq_dataset = st.text_input("Dataset", value=os.getenv("BIGQUERY_DATASET", ""))
    # List tables dynamically when project/dataset are provided
    default_table = os.getenv("BIGQUERY_TABLE", "")
    # If default_table is fully qualified (project.dataset.table), reduce to table_id for matching
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
        preselect_index = tables.index(default_table) if default_table in tables else 0
        bq_table = st.selectbox("Table", options=tables, index=preselect_index)
    else:
        bq_table = st.text_input("Table", value=default_table)

    # Try to infer columns when we have project/dataset/table
    inferred_date = None
    inferred_metric = None
    if bq_project and bq_dataset and bq_table:
        try:
            inferred_date, inferred_metric = bq_client.infer_wbr_columns(project_id=bq_project, dataset=bq_dataset, table=bq_table)
        except Exception as e:
            st.caption(f"Não foi possível inferir colunas: {e}")

    # Prefill with env or inferred
    default_date_col = os.getenv("WBR_DATE_COL", "") or (inferred_date or "")
    default_metric_col = os.getenv("WBR_METRIC_COL", "") or (inferred_metric or "")
    coluna_data = st.text_input("Coluna de data", value=default_date_col)
    coluna_metrica = st.text_input("Coluna métrica", value=default_metric_col)
    if inferred_date or inferred_metric:
        st.caption(f"Inferido: data='{inferred_date}' métrica='{inferred_metric}'")

@st.cache_data(show_spinner=True)
def load_wbr_data(project_id: str, dataset: str, table: str, date_col: str | None, metric_col: str | None):
    # If no columns provided, attempt to infer from schema
    if not date_col or not metric_col:
        inferred = bq_client.infer_wbr_columns(project_id=project_id, dataset=dataset, table=table)
        date_col = date_col or inferred[0]
        metric_col = metric_col or inferred[1]
    return bq_client.fetch_wbr_data(project_id=project_id, dataset=dataset, table=table, date_col=date_col, metric_col=metric_col)

if not bq_project or not bq_dataset or not bq_table:
    st.warning("Defina Project/Dataset/Table do BigQuery na barra lateral.")
    df = None
else:
    df = load_wbr_data(bq_project, bq_dataset, bq_table, coluna_data or None, coluna_metrica or None)

if df is None or df.empty:
    st.warning("Sem dados do BigQuery.")
else:
    # DataFrame retornado já traz colunas normalizadas: 'date' e 'metric_value'
    # Os campos da sidebar (coluna_data/coluna_metrica) são usados apenas para montar a SQL.
    fig = gerar_grafico_wbr(
        df,
        coluna_data="date",
        coluna_pessoas="metric_value",
        titulo=titulo,
        unidade=unidade,
        data_referencia=data_ref.isoformat() if data_ref else None,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Dados carregados do BigQuery usando a consulta em src/data/queries/wbr.sql")