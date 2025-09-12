from datetime import datetime, timedelta
import pandas as pd
import numpy as np

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
    # Verifica se estamos no meio de uma semana (semana parcial)
    fim_semana_completa = pd.Timestamp(data_referencia).to_period('W-SUN').end_time
    semana_parcial = data_referencia < fim_semana_completa
    
    # Se temos uma semana parcial, ajusta o fim para a data de referência
    if semana_parcial:
        fim_semana = data_referencia
        # Calcula quantos dias temos na semana atual
        inicio_semana_atual = pd.Timestamp(data_referencia).to_period('W-SUN').start_time
        dias_semana_parcial = (data_referencia - inicio_semana_atual).days + 1
    else:
        fim_semana = fim_semana_completa
        dias_semana_parcial = 7
    
    inicio_6sem = fim_semana - timedelta(weeks=6)
    df_6sem_cy = df_work[(df_work.index > inicio_6sem) & (df_work.index <= fim_semana)]
    semanas_cy = df_6sem_cy.resample('W-SUN').agg({coluna_metrica: 'sum'}).tail(6)

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

    # PY - Comparação "Maçã com Maçã"
    ano_anterior = data_referencia.year - 1
    inicio_ano_py = pd.Timestamp(year=ano_anterior, month=1, day=1)
    
    # Para comparação justa, PY deve ter apenas até o mesmo dia/mês que CY
    # Se CY está em 10/julho, PY deve mostrar apenas até 10/julho do ano anterior
    try:
        fim_ano_py = pd.Timestamp(year=ano_anterior, month=data_referencia.month, day=data_referencia.day)
    except ValueError:
        # Caso especial: 29 de fevereiro -> 28 de fevereiro no ano não-bissexto
        fim_ano_py = pd.Timestamp(year=ano_anterior, month=data_referencia.month, day=28)

    # Semanas PY - Comparação "Maçã com Maçã" 
    # Usa as mesmas datas do calendário, apenas mudando o ano
    # Isso garante comparação justa: 25-31 agosto 2025 vs 25-31 agosto 2024
    
    # Calcula a data equivalente no ano anterior (mesmo mês/dia)
    try:
        # Tenta criar a mesma data no ano anterior
        data_ref_py = data_referencia.replace(year=ano_anterior)
    except ValueError:
        # Caso especial: 29 de fevereiro em ano bissexto -> 28 de fevereiro
        data_ref_py = pd.Timestamp(year=ano_anterior, month=data_referencia.month, day=28)
    
    # Se CY tem semana parcial, PY também deve ter
    if semana_parcial:
        # Para PY, usa exatamente o mesmo período calendário
        fim_semana_py = data_ref_py
        # Calcula quantos dias atrás começou a semana em CY para aplicar o mesmo em PY
        dias_desde_inicio_semana = (data_referencia - inicio_semana_atual).days
        inicio_semana_py = data_ref_py - timedelta(days=dias_desde_inicio_semana)
        # 6 semanas atrás mantendo o alinhamento
        inicio_6sem_py = inicio_semana_py - timedelta(weeks=5)
    else:
        # Para semana completa, usa exatamente 7 dias terminando na mesma data
        fim_semana_py = data_ref_py
        # Retrocede exatamente 6 semanas (42 dias) a partir do fim
        inicio_6sem_py = fim_semana_py - timedelta(days=41)  # 6 semanas = 42 dias, menos 1 pois é inclusive
    
    # Para PY, vamos processar manualmente cada semana para garantir alinhamento exato de datas
    semanas_py_list = []
    
    # Processa cada uma das 6 semanas com as mesmas datas do calendário
    for i in range(6):
        # Calcula o período da semana i (0 = 6 semanas atrás, 5 = semana atual)
        semanas_atras = 5 - i
        
        if i == 5 and semana_parcial:
            # Última semana é parcial
            inicio_sem_cy = inicio_semana_atual
            fim_sem_cy = data_referencia
        else:
            # Semanas completas
            fim_sem_cy = fim_semana - timedelta(weeks=semanas_atras)
            inicio_sem_cy = fim_sem_cy - timedelta(days=6)
        
        # Usa exatamente as mesmas datas no ano anterior
        try:
            inicio_sem_py = inicio_sem_cy.replace(year=ano_anterior)
            fim_sem_py = fim_sem_cy.replace(year=ano_anterior)
        except ValueError:
            # Caso especial para 29 de fevereiro
            inicio_sem_py = pd.Timestamp(year=ano_anterior, month=inicio_sem_cy.month, 
                                       day=min(inicio_sem_cy.day, 28))
            fim_sem_py = pd.Timestamp(year=ano_anterior, month=fim_sem_cy.month,
                                     day=min(fim_sem_cy.day, 28))
        
        # Filtra e soma os dados para essa semana
        df_semana_py = df_work[(df_work.index >= inicio_sem_py) & (df_work.index <= fim_sem_py)]
        valor_semana = df_semana_py[coluna_metrica].sum() if not df_semana_py.empty else 0
        
        # Adiciona à lista com o timestamp do último dia da semana
        semanas_py_list.append(pd.Series({coluna_metrica: valor_semana}, name=fim_sem_py))
    
    # Cria o DataFrame das semanas PY
    semanas_py = pd.DataFrame(semanas_py_list)
    semanas_py.index = pd.DatetimeIndex([s.name for s in semanas_py_list])

    # Meses PY - Comparação "Maçã com Maçã"
    # Para cada mês, use apenas até o mesmo dia que CY
    df_ano_py = df_work[(df_work.index >= inicio_ano_py) & (df_work.index <= fim_ano_py)]
    
    # Processa mês a mês para garantir comparação justa
    meses_py_list = []
    for mes in range(1, 13):
        inicio_mes_py = pd.Timestamp(year=ano_anterior, month=mes, day=1)
        
        # Se é o mês da data de referência, limita ao mesmo dia
        if mes == data_referencia.month:
            fim_mes_py = pd.Timestamp(year=ano_anterior, month=mes, day=data_referencia.day)
        # Se é um mês anterior ao mês de referência, usa o mês completo
        elif mes < data_referencia.month:
            fim_mes_py = inicio_mes_py + pd.offsets.MonthEnd(0)
        # Se é um mês posterior, não tem dados (será NaN)
        else:
            meses_py_list.append(pd.Series({coluna_metrica: np.nan}, name=inicio_mes_py))
            continue
        
        # Filtra dados do mês
        dados_mes = df_ano_py[(df_ano_py.index >= inicio_mes_py) & (df_ano_py.index <= fim_mes_py)]
        if not dados_mes.empty:
            soma_mes = dados_mes[coluna_metrica].sum()
        else:
            soma_mes = 0
        
        meses_py_list.append(pd.Series({coluna_metrica: soma_mes}, name=inicio_mes_py))
    
    # Cria DataFrame com todos os meses
    df_12m_py = pd.DataFrame(meses_py_list)
    df_12m_py.index = pd.date_range(start=pd.Timestamp(year=ano_anterior, month=1, day=1), periods=12, freq='MS')

    # Para PY, o mês parcial deve seguir a mesma lógica de CY para comparação justa
    # Se CY tem mês parcial (não chegou ao fim do mês), PY também tem mês parcial para o mesmo mês
    mes_parcial_py = mes_parcial_cy  # PY tem mês parcial se CY tem
    dias_mes_parcial_py = 0
    
    # Calcula os dias no mês parcial PY (mesmo mês do ano anterior)
    if mes_parcial_cy:
        # Para o mês da data de referência no ano anterior
        inicio_mes_ref_py = pd.Timestamp(year=ano_anterior, month=data_referencia.month, day=1)
        # Limita ao mesmo dia que CY para comparação justa
        fim_mes_ref_py = pd.Timestamp(year=ano_anterior, month=data_referencia.month, day=data_referencia.day)
        dados_mes_ref_py = df_work[(df_work.index >= inicio_mes_ref_py) & (df_work.index <= fim_mes_ref_py)]
        if not dados_mes_ref_py.empty:
            dias_mes_parcial_py = len(dados_mes_ref_py.index.normalize().unique())

    return {
        'semanas_cy': semanas_cy,
        'meses_cy': df_12m_cy,
        'semanas_py': semanas_py,
        'meses_py': df_12m_py,
        'mes_parcial_cy': mes_parcial_cy,
        'dias_mes_parcial_cy': dias_mes_parcial_cy,
        'mes_parcial_py': mes_parcial_py,
        'dias_mes_parcial_py': dias_mes_parcial_py,
        'semana_parcial': semana_parcial,
        'dias_semana_parcial': dias_semana_parcial if semana_parcial else 7,
        'ano_atual': ano_atual,
        'ano_anterior': ano_anterior
    }