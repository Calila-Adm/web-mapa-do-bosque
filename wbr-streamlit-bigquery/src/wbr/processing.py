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
COLUNA_DATA = 'INSIRA A COLUNA DATA'
COLUNA_METRICA = 'INSIRA A COLUNA METRICA'


def processar_dados_wbr(df: pd.DataFrame, data_referencia: pd.Timestamp | None = None):
    """
    Processa dados no formato WBR brasileiro: 6 semanas + ano fiscal (Jan-Dez),
    com alinhamento de semanas ISO e detecção de mês parcial.

    Args:
        df: DataFrame com colunas configuradas em COLUNA_DATA e COLUNA_METRICA
        data_referencia: Data final para análise (default: última data disponível)
    Returns:
        dict com séries semanais/mensais de CY e PY, flags de mês parcial e anos usados.
    """
    if data_referencia is None:
        data_referencia = pd.to_datetime(df[COLUNA_DATA].max())

    df = df.copy()
    df[COLUNA_DATA] = pd.to_datetime(df[COLUNA_DATA])
    df = df.set_index(COLUNA_DATA)

    ano_atual = data_referencia.year
    inicio_ano_cy = pd.Timestamp(year=ano_atual, month=1, day=1)
    fim_ano_cy = data_referencia

    # Semanas CY (alinhadas ao domingo)
    fim_semana = pd.Timestamp(data_referencia).to_period('W-SUN').end_time
    inicio_6sem = fim_semana - timedelta(weeks=6)
    df_6sem_cy = df[(df.index > inicio_6sem) & (df.index <= fim_semana)]
    semanas_cy = df_6sem_cy.resample('W').agg({COLUNA_METRICA: 'sum'}).tail(6)

    # Meses CY (Jan até data ref)
    df_ano_cy = df[(df.index >= inicio_ano_cy) & (df.index <= fim_ano_cy)]
    df_12m_cy = df_ano_cy.resample('ME').agg({COLUNA_METRICA: 'sum'})
    df_12m_cy = df_12m_cy[df_12m_cy[COLUNA_METRICA] > 0]

    # Detectar mês parcial CY
    mes_parcial_cy = False
    dias_mes_parcial_cy = 0
    if len(df_12m_cy) > 0:
        ultimo_mes = df_12m_cy.index[-1]
        if ultimo_mes.month == data_referencia.month and ultimo_mes.year == data_referencia.year:
            inicio_mes = data_referencia.replace(day=1)
            dias_com_dados = df[(df.index >= inicio_mes) & (df.index <= data_referencia)]
            dias_mes_parcial_cy = len(dias_com_dados.index.unique())
            mes_parcial_cy = data_referencia.day < ultimo_mes.days_in_month

    # PY
    ano_anterior = data_referencia.year - 1
    inicio_ano_py = pd.Timestamp(year=ano_anterior, month=1, day=1)
    fim_ano_py = pd.Timestamp(year=ano_anterior, month=12, day=31)

    # Semanas PY (mesma semana ISO)
    from datetime import date
    semana_atual = data_referencia.isocalendar()[1]
    try:
        fim_semana_py = date.fromisocalendar(ano_anterior, semana_atual, 7)
        fim_semana_py = pd.Timestamp(fim_semana_py)
    except ValueError:
        fim_semana_py = pd.Timestamp(date.fromisocalendar(ano_anterior, 52, 7))

    inicio_6sem_py = fim_semana_py - timedelta(weeks=6)
    df_6sem_py = df[(df.index > inicio_6sem_py) & (df.index <= fim_semana_py)]
    semanas_py = df_6sem_py.resample('W').agg({COLUNA_METRICA: 'sum'}).tail(6)

    # Meses PY (Jan-Dez)
    df_ano_py = df[(df.index >= inicio_ano_py) & (df.index <= fim_ano_py)]
    df_12m_py = df_ano_py.resample('ME').agg({COLUNA_METRICA: 'sum'})
    df_12m_py = df_12m_py[df_12m_py[COLUNA_METRICA] > 0]

    mes_parcial_py = False
    dias_mes_parcial_py = 0
    if len(df_12m_py) > 0:
        ultimo_mes_py = df_12m_py.index[-1]
        if ultimo_mes_py.month == fim_semana_py.month and ultimo_mes_py.year == fim_semana_py.year:
            inicio_mes_py = fim_semana_py.replace(day=1)
            dias_com_dados_py = df[(df.index >= inicio_mes_py) & (df.index <= fim_semana_py)]
            dias_mes_parcial_py = len(dias_com_dados_py.index.unique())
            mes_parcial_py = fim_semana_py.day < ultimo_mes_py.days_in_month

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