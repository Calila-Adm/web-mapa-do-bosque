import pandas as pd

from .processing import processar_dados_wbr, COLUNA_DATA, COLUNA_METRICA
from .charts import criar_grafico_wbr

TITULO_GRAFICO = 'INSIRA O TÍTULO'
UNIDADE_METRICA = 'INSIRA A UNIDADE'


def gerar_grafico_wbr(df: pd.DataFrame,
                      coluna_data: str | None = None,
                      coluna_pessoas: str | None = None,
                      titulo: str | None = None,
                      unidade: str | None = None,
                      data_referencia: str | pd.Timestamp | None = None):
    if coluna_data is None:
        coluna_data = COLUNA_DATA
    if coluna_pessoas is None:
        coluna_pessoas = COLUNA_METRICA
    if titulo is None:
        titulo = TITULO_GRAFICO
    if unidade is None:
        unidade = UNIDADE_METRICA

    if coluna_data not in df.columns:
        raise ValueError(f"DataFrame não contém a coluna de data: {coluna_data}")
    if coluna_pessoas not in df.columns:
        raise ValueError(f"DataFrame não contém a coluna de pessoas: {coluna_pessoas}")

    df = df.rename(columns={coluna_data: COLUNA_DATA, coluna_pessoas: COLUNA_METRICA}).copy()
    df[COLUNA_DATA] = pd.to_datetime(df[COLUNA_DATA])

    if data_referencia is None:
        data_referencia = df[COLUNA_DATA].max()
    else:
        data_referencia = pd.to_datetime(data_referencia)

    dados_processados = processar_dados_wbr(df, data_referencia)

    fig = criar_grafico_wbr(dados_processados, df, data_referencia, titulo=titulo, unidade=unidade)
    return fig
