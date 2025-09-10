from datetime import datetime, timedelta
import pandas as pd

# Mantemos funções simples existentes para compatibilidade com outros usos
def process_data(df):
    # ...existing code...
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    return df

def calculate_metrics(df):
    # ...existing code...
    metrics = {}
    metrics['total'] = df['value'].sum() if 'value' in df.columns else 0
    metrics['average'] = df['value'].mean() if 'value' in df.columns else 0
    metrics['max'] = df['value'].max() if 'value' in df.columns else 0
    metrics['min'] = df['value'].min() if 'value' in df.columns else 0
    return metrics

def prepare_data_for_visualization(df):
    # ...existing code...
    visualization_data = {
        'dates': df.index.tolist(),
        'values': df['value'].tolist() if 'value' in df.columns else []
    }
    return visualization_data


# ============================================
# CONFIG PADRÃO (alinhado ao main.py original)
# ============================================
# Use standardized column names from BigQuery client
COLUNA_DATA = 'date'
COLUNA_METRICA = 'metric_value'


def processar_dados_wbr(df: pd.DataFrame, data_referencia: pd.Timestamp | None = None, coluna_data: str = 'date', coluna_metrica: str = 'metric_value'):
    """
    Processa dados no formato WBR brasileiro: 6 semanas + ano fiscal (Jan-Dez),
    com alinhamento de semanas ISO e detecção de mês parcial.

    Args:
        df: DataFrame com colunas de data e métrica
        data_referencia: Data final para análise (default: última data disponível)
        coluna_data: Nome da coluna de data (default: 'date')
        coluna_metrica: Nome da coluna de métrica (default: 'metric_value')
    Returns:
        dict com séries semanais/mensais de CY e PY, flags de mês parcial e anos usados.
    """
    # Always work with a copy to avoid modifying the original
    df_work = df.copy()
    
    # Ensure the date column is datetime before any operations
    df_work[coluna_data] = pd.to_datetime(df_work[coluna_data])
    
    if data_referencia is None:
        data_referencia = df_work[coluna_data].max()
    else:
        data_referencia = pd.to_datetime(data_referencia)

    # Set the date column as index
    df_work = df_work.set_index(coluna_data)
    
    # Ensure index is DatetimeIndex
    if not isinstance(df_work.index, pd.DatetimeIndex):
        df_work.index = pd.to_datetime(df_work.index)

    ano_atual = data_referencia.year
    inicio_ano_cy = pd.Timestamp(year=ano_atual, month=1, day=1)
    fim_ano_cy = data_referencia

    # Semanas CY (alinhadas ao domingo)
    fim_semana = pd.Timestamp(data_referencia).to_period('W-SUN').end_time
    inicio_6sem = fim_semana - timedelta(weeks=6)
    df_6sem_cy = df_work[(df_work.index > inicio_6sem) & (df_work.index <= fim_semana)]
    semanas_cy = df_6sem_cy.resample('W').agg({coluna_metrica: 'sum'}).tail(6)

    # Meses CY (Jan–Dez do ano de referência), mantendo meses sem dados
    df_ano_cy = df_work[(df_work.index >= inicio_ano_cy) & (df_work.index <= fim_ano_cy)]
    df_12m_cy = df_ano_cy.resample('MS').agg({coluna_metrica: 'sum'})
    # Reindexa para 12 meses do ano (Jan–Dez)
    idx_cy = pd.date_range(start=pd.Timestamp(year=ano_atual, month=1, day=1), periods=12, freq='MS')
    df_12m_cy = df_12m_cy.reindex(idx_cy)
    # Zera meses com ausencia total de dados no período (mantém NaN onde apropriado)
    # Mantemos NaN para meses futuros (após o mês da data de referência)
    mes_ref = data_referencia.month
    futuros_mask = df_12m_cy.index.month > mes_ref
    # Para meses posteriores ao mês de referência, mantemos NaN; para meses anteriores vazios, coloca 0
    df_12m_cy.loc[~futuros_mask, coluna_metrica] = df_12m_cy.loc[~futuros_mask, coluna_metrica].fillna(0)

    # Detectar mês parcial CY (com base no mês da data de referência e dados reais)
    mes_parcial_cy = False
    dias_mes_parcial_cy = 0
    inicio_mes_ref = data_referencia.replace(day=1)
    fim_mes_ref = (inicio_mes_ref + pd.offsets.MonthEnd(1))
    dados_mes_ref = df_work[(df_work.index >= inicio_mes_ref) & (df_work.index <= data_referencia)]
    if not dados_mes_ref.empty:
        dias_mes_parcial_cy = len(dados_mes_ref.index.normalize().unique())
        # Parcial se a data de referência não é o último dia do mês
        mes_parcial_cy = data_referencia < fim_mes_ref

    # PY
    ano_anterior = data_referencia.year - 1
    inicio_ano_py = pd.Timestamp(year=ano_anterior, month=1, day=1)
    fim_ano_py = pd.Timestamp(year=ano_anterior, month=12, day=31)

    # Semanas PY usando metodologia de Deslocamento Fixo de 364 dias
    # Esta abordagem garante que sempre comparamos o mesmo dia da semana
    # Segunda com Segunda, Terça com Terça, etc.
    # 364 dias = 52 semanas exatas, preservando o alinhamento semanal
    
    # Para PY, simplesmente voltamos 364 dias (52 semanas) para cada data CY
    # Isso mantém o mesmo padrão semanal (fins de semana, dias úteis, etc.)
    OFFSET_DIAS = 364  # 52 semanas × 7 dias
    
    # Calcula o período PY aplicando o offset de 364 dias
    fim_semana_py = fim_semana - timedelta(days=OFFSET_DIAS)
    inicio_6sem_py = fim_semana_py - timedelta(weeks=6)
    
    # Obtém os dados PY para o período correspondente
    df_6sem_py = df_work[(df_work.index > inicio_6sem_py) & (df_work.index <= fim_semana_py)]
    semanas_py = df_6sem_py.resample('W').agg({coluna_metrica: 'sum'}).tail(6)

    # Meses PY (Jan–Dez do ano anterior), mantendo meses sem dados como 0
    df_ano_py = df_work[(df_work.index >= inicio_ano_py) & (df_work.index <= fim_ano_py)]
    df_12m_py = df_ano_py.resample('MS').agg({coluna_metrica: 'sum'})
    idx_py = pd.date_range(start=pd.Timestamp(year=ano_anterior, month=1, day=1), periods=12, freq='MS')
    df_12m_py = df_12m_py.reindex(idx_py)
    df_12m_py[coluna_metrica] = df_12m_py[coluna_metrica].fillna(0)

    # Para PY, calculamos mês parcial baseado no offset de 364 dias
    mes_parcial_py = False
    dias_mes_parcial_py = 0
    
    # Usa a data PY com offset de 364 dias para consistência
    if fim_semana_py is not None:
        inicio_mes_py = fim_semana_py.replace(day=1)
        fim_mes_py = (inicio_mes_py + pd.offsets.MonthEnd(1))
        dados_mes_py = df_work[(df_work.index >= inicio_mes_py) & (df_work.index <= fim_semana_py)]
        if not dados_mes_py.empty:
            dias_mes_parcial_py = len(dados_mes_py.index.normalize().unique())
            mes_parcial_py = fim_semana_py < fim_mes_py

    return {
        'semanas_cy': semanas_cy,
        'meses_cy': df_12m_cy,
        'semanas_py': semanas_py,
        'meses_py': df_12m_py,
        'mes_parcial_cy': mes_parcial_cy,
        'dias_mes_parcial_cy': dias_mes_parcial_cy,
        'mes_parcial_py': mes_parcial_py,
        'dias_mes_parcial_py': dias_mes_parcial_py,
        'ano_atual': ano_atual,
        'ano_anterior': ano_anterior
    }