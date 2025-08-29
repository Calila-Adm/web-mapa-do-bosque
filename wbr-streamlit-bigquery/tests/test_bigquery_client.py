import pytest
from src.data.bigquery_client import BigQueryClient

@pytest.fixture
def bigquery_client():
    return BigQueryClient()

def test_initialize_client(bigquery_client):
    assert bigquery_client is not None

def test_run_query_signature(bigquery_client):
    # Apenas valida que o método existe e aceita uma string
    assert hasattr(bigquery_client, 'run_query')
    # Não executa contra o BigQuery real em CI

def test_fetch_wbr_method_exists(bigquery_client):
    assert hasattr(bigquery_client, 'fetch_wbr_data')