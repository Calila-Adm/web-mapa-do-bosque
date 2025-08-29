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

    # Meses CY (Jan–Dez do ano de referência), mantendo meses sem dados
    df_ano_cy = df[(df.index >= inicio_ano_cy) & (df.index <= fim_ano_cy)]
    df_12m_cy = df_ano_cy.resample('MS').agg({COLUNA_METRICA: 'sum'})
    # Reindexa para 12 meses do ano (Jan–Dez)
    idx_cy = pd.date_range(start=pd.Timestamp(year=ano_atual, month=1, day=1), periods=12, freq='MS')
    df_12m_cy = df_12m_cy.reindex(idx_cy)
    # Zera meses com ausencia total de dados no período (mantém NaN onde apropriado)
    # Mantemos NaN para meses futuros (após o mês da data de referência)
    mes_ref = data_referencia.month
    futuros_mask = df_12m_cy.index.month > mes_ref
    # Para meses posteriores ao mês de referência, mantemos NaN; para meses anteriores vazios, coloca 0
    df_12m_cy.loc[~futuros_mask, COLUNA_METRICA] = df_12m_cy.loc[~futuros_mask, COLUNA_METRICA].fillna(0)

    # Detectar mês parcial CY (com base no mês da data de referência e dados reais)
    mes_parcial_cy = False
    dias_mes_parcial_cy = 0
    inicio_mes_ref = data_referencia.replace(day=1)
    fim_mes_ref = (inicio_mes_ref + pd.offsets.MonthEnd(1))
    dados_mes_ref = df[(df.index >= inicio_mes_ref) & (df.index <= data_referencia)]
    if not dados_mes_ref.empty:
        dias_mes_parcial_cy = len(dados_mes_ref.index.normalize().unique())
        # Parcial se a data de referência não é o último dia do mês
        mes_parcial_cy = data_referencia < fim_mes_ref

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

    # Meses PY (Jan–Dez do ano anterior), mantendo meses sem dados como 0
    df_ano_py = df[(df.index >= inicio_ano_py) & (df.index <= fim_ano_py)]
    df_12m_py = df_ano_py.resample('MS').agg({COLUNA_METRICA: 'sum'})
    idx_py = pd.date_range(start=pd.Timestamp(year=ano_anterior, month=1, day=1), periods=12, freq='MS')
    df_12m_py = df_12m_py.reindex(idx_py)
    df_12m_py[COLUNA_METRICA] = df_12m_py[COLUNA_METRICA].fillna(0)

    mes_parcial_py = False
    dias_mes_parcial_py = 0
    inicio_mes_py = fim_semana_py.replace(day=1)
    fim_mes_py = (inicio_mes_py + pd.offsets.MonthEnd(1))
    dados_mes_py = df[(df.index >= inicio_mes_py) & (df.index <= fim_semana_py)]
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