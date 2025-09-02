import pandas as pd

from .processing import processar_dados_wbr
from .charts import criar_grafico_wbr

TITULO_GRAFICO = 'INSIRA O TÍTULO'
UNIDADE_METRICA = 'INSIRA A UNIDADE'


def gerar_grafico_wbr(df: pd.DataFrame,
                      coluna_data: str = 'date',
                      coluna_pessoas: str = 'metric_value',
                      titulo: str | None = None,
                      unidade: str | None = None,
                      data_referencia: str | pd.Timestamp | None = None):
    if titulo is None:
        titulo = TITULO_GRAFICO
    if unidade is None:
        unidade = UNIDADE_METRICA

    if coluna_data not in df.columns:
        raise ValueError(f"DataFrame não contém a coluna de data: {coluna_data}. Colunas disponíveis: {df.columns.tolist()}")
    if coluna_pessoas not in df.columns:
        raise ValueError(f"DataFrame não contém a coluna de pessoas: {coluna_pessoas}. Colunas disponíveis: {df.columns.tolist()}")

    # Ensure date column is datetime (work with a copy)
    df_original = df.copy()
    df_original[coluna_data] = pd.to_datetime(df_original[coluna_data])

    if data_referencia is None:
        data_referencia = df_original[coluna_data].max()
    else:
        data_referencia = pd.to_datetime(data_referencia)

    # Pass column names to processar_dados_wbr
    dados_processados = processar_dados_wbr(df_original, data_referencia, coluna_data=coluna_data, coluna_metrica=coluna_pessoas)

    # Pass the original df with its column names
    fig = criar_grafico_wbr(dados_processados, df_original, data_referencia, titulo=titulo, unidade=unidade)
    return fig
