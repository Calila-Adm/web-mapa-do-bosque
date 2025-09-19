from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

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


# ============================================
# ENHANCED WBR AGGREGATION SYSTEM
# ============================================

def compute_trailing_weeks(
    daily_df: pd.DataFrame,
    cfg,  # WBRConfig instance
    *,
    fill_missing_weeks: bool = True,
    strict_7day_span: bool = True,
    reindex_missing_days: bool = False,
    use_absolute_week_number: bool = False
) -> pd.DataFrame:
    """
    Generate weekly DataFrame with exactly N trailing weeks based on week_ending anchor.

    This function implements non-ISO calendar logic: weeks are always 7-day blocks
    ending on the specified week_ending date, regardless of ISO week boundaries.

    Each row represents the aggregation of daily records present between StartDate and
    EndDate (inclusive). Weeks are fixed 7-day blocks determined by counting backwards
    from week_ending. Non-existent days are not fabricated; if reindex_missing_days=True,
    they appear only as NaN before aggregation.

    Args:
        daily_df: DataFrame with daily data (must have date column)
        cfg: WBRConfig instance with week_ending, trailing_weeks, and aggregation functions
        fill_missing_weeks: If True, pad with empty weeks to ensure exact N weeks (default: True)
        strict_7day_span: If True, enforce exactly 7-day week spans (default: True)
        reindex_missing_days: If True, fill missing days with NaN before aggregation (default: False)
        use_absolute_week_number: If True, use cfg.week_number for labeling (default: False)

    Returns:
        DataFrame with weekly aggregations, exactly N weeks with columns:
        [WeekIndex, StartDate, EndDate, Date, Intervalo, WeekEndingWeekday,
         WkLabel, WkLabelFull, <metrics...>]

    Raises:
        ValueError: For invalid configuration or data issues
        KeyError: If aggregation columns not found in DataFrame
    """
    # Validate inputs
    if daily_df is None or daily_df.empty:
        raise ValueError("daily_df cannot be None or empty")

    # Check if cfg has the required attributes instead of isinstance check
    # This avoids import issues
    if not hasattr(cfg, 'week_ending') or not hasattr(cfg, 'trailing_weeks') or not hasattr(cfg, 'aggf'):
        raise ValueError("cfg must be a WBRConfig instance with week_ending, trailing_weeks, and aggf attributes")

    # Validate aggregation functions against DataFrame columns
    cfg.validate_aggf_columns(daily_df.columns.tolist())

    # Work with a copy to avoid modifying original data
    df_work = daily_df.copy()

    # Auto-detect date column - normalize to 'Date' for consistency
    date_col = None
    for possible_col in ['date', 'Date', 'DATE']:
        if possible_col in df_work.columns:
            date_col = possible_col
            break

    if date_col is None:
        raise ValueError("No date column found. DataFrame must contain 'date', 'Date', or 'DATE' column")

    # Normalize column name to 'Date' as per specification
    if date_col != 'Date':
        df_work = df_work.rename(columns={date_col: 'Date'})
        date_col = 'Date'

    # Ensure date column is datetime
    df_work['Date'] = pd.to_datetime(df_work['Date'])

    # Remove duplicates by aggregating (sum for numeric columns)
    if df_work['Date'].duplicated().any():
        numeric_cols = df_work.select_dtypes(include=[np.number]).columns.tolist()
        agg_dict = {col: 'sum' for col in numeric_cols}
        df_work = df_work.groupby('Date').agg(agg_dict).reset_index()

    # Sort by date for consistency
    df_work = df_work.sort_values('Date').reset_index(drop=True)

    # Calculate week boundaries using strict 7-day spans
    week_ending = pd.to_datetime(cfg.week_ending)
    trailing_weeks = cfg.trailing_weeks

    # Generate chronological list of anchors: A_1 ... A_N where A_N = cfg.week_ending
    # and A_i = week_ending - 7*(N-i) days
    week_anchors = []
    for i in range(trailing_weeks):
        # Week i ends (trailing_weeks - 1 - i) * 7 days before week_ending
        days_back = (trailing_weeks - 1 - i) * 7
        anchor = week_ending - timedelta(days=days_back)
        week_anchors.append(anchor)

    # Generate week boundaries (N weeks of exactly 7 days each)
    week_boundaries = []
    for anchor in week_anchors:
        week_end = anchor
        week_start = week_end - timedelta(days=6)  # 7-day span: start to end inclusive
        week_boundaries.append((week_start, week_end))

    # Aggregate data for each week
    weekly_results = []

    for week_idx, (week_start, week_end) in enumerate(week_boundaries):
        # If reindex_missing_days is True, create full date range for this week
        if reindex_missing_days:
            week_date_range = pd.date_range(start=week_start, end=week_end, freq='D')
            week_df = pd.DataFrame({'Date': week_date_range})
            # Merge with actual data
            week_data = week_df.merge(
                df_work[(df_work['Date'] >= week_start) & (df_work['Date'] <= week_end)],
                on='Date',
                how='left'
            )
        else:
            # Filter data for this week (inclusive of both start and end dates)
            mask = (df_work['Date'] >= week_start) & (df_work['Date'] <= week_end)
            week_data = df_work.loc[mask].copy()

        # Initialize week result with required metadata
        week_result = {
            'WeekIndex': week_idx + 1,  # 1-based index (1 = oldest week)
            'StartDate': week_start,
            'EndDate': week_end,
            'Date': week_end,  # Redundancy as per specification
            'Intervalo': f"{week_start.strftime('%Y-%m-%d')} → {week_end.strftime('%Y-%m-%d')}",
            'WeekEndingWeekday': week_end.strftime('%a'),  # Short weekday name (Mon, Tue, etc.)
        }

        # Calculate WkLabel based on mode
        if use_absolute_week_number and cfg.week_number is not None:
            # Mode B: Use cfg.week_number for the last week and decrement backwards
            week_result['WkLabel'] = f"Wk{cfg.week_number - (trailing_weeks - 1 - week_idx)}"
        else:
            # Mode A (default): Simple Wk1..WkN
            week_result['WkLabel'] = f"Wk{week_idx + 1}"

        # WkLabelFull combines label with week ending date
        week_result['WkLabelFull'] = f"{week_result['WkLabel']} (WE {week_end.strftime('%Y-%m-%d')})"

        if week_data.empty:
            # No data for this week
            if fill_missing_weeks:
                # Fill with 0 or NaN based on aggregation function
                # Document that we don't create artificial data
                for col, agg_func in cfg.aggf.items():
                    if agg_func in ['sum', 'count']:
                        week_result[col] = 0  # Sum/count of nothing is 0
                    else:
                        week_result[col] = np.nan  # No data for averages, etc.
            else:
                # Skip this week entirely if not filling missing weeks
                continue
        else:
            # Aggregate data for this week - only aggregate existing rows
            # No artificial data creation as per specification
            for col, agg_func in cfg.aggf.items():
                if col not in week_data.columns:
                    week_result[col] = np.nan
                    continue

                try:
                    if agg_func == 'sum':
                        week_result[col] = week_data[col].sum()
                    elif agg_func == 'mean':
                        week_result[col] = week_data[col].mean()
                    elif agg_func == 'median':
                        week_result[col] = week_data[col].median()
                    elif agg_func == 'min':
                        week_result[col] = week_data[col].min()
                    elif agg_func == 'max':
                        week_result[col] = week_data[col].max()
                    elif agg_func == 'count':
                        week_result[col] = week_data[col].count()
                    elif agg_func == 'std':
                        week_result[col] = week_data[col].std()
                    elif agg_func == 'var':
                        week_result[col] = week_data[col].var()
                    else:
                        # Fallback to pandas aggregation
                        week_result[col] = week_data[col].agg(agg_func)

                except Exception as e:
                    import logging
                    logging.warning(f"Aggregation failed for column {col} with function {agg_func}: {e}")
                    week_result[col] = np.nan

        weekly_results.append(week_result)

    # Convert to DataFrame
    result_df = pd.DataFrame(weekly_results)

    # Ensure we have exactly N weeks if fill_missing_weeks is True
    if fill_missing_weeks and len(result_df) < trailing_weeks:
        # This shouldn't happen with the new logic, but keep as safety check
        raise ValueError(f"Internal error: Expected {trailing_weeks} weeks, got {len(result_df)}")

    # Sort by EndDate to ensure chronological order (oldest to most recent)
    result_df = result_df.sort_values('EndDate').reset_index(drop=True)

    # Reorder columns as per specification
    # [WeekIndex, StartDate, EndDate, Date, Intervalo, WeekEndingWeekday, WkLabel, WkLabelFull, <metrics...>]
    base_columns = ['WeekIndex', 'StartDate', 'EndDate', 'Date', 'Intervalo',
                    'WeekEndingWeekday', 'WkLabel', 'WkLabelFull']

    # Add metric columns
    metric_columns = list(cfg.aggf.keys())

    # Combine column order
    column_order = base_columns + metric_columns

    # Reorder DataFrame columns
    available_columns = [col for col in column_order if col in result_df.columns]
    result_df = result_df[available_columns]

    # Validate result
    if fill_missing_weeks and len(result_df) != trailing_weeks:
        raise ValueError(f"Expected exactly {trailing_weeks} weeks, got {len(result_df)}")

    return result_df


# ============================================
# VALIDATION FUNCTIONS
# ============================================

def validate_wbr_inputs(
    daily_df: pd.DataFrame,
    cfg,  # WBRConfig instance
    strict_validation: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive validation of WBR inputs.

    Args:
        daily_df: Input DataFrame with daily data
        cfg: WBRConfig instance
        strict_validation: If True, raise exceptions for errors

    Returns:
        Dictionary with validation results

    Raises:
        ValueError: If strict_validation=True and validation fails
    """
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'info': []
    }

    # Validate DataFrame
    if daily_df is None:
        validation_result['errors'].append("DataFrame is None")
        validation_result['valid'] = False
    elif daily_df.empty:
        validation_result['errors'].append("DataFrame is empty")
        validation_result['valid'] = False
    else:
        validation_result['info'].append(f"DataFrame has {len(daily_df)} rows")

        # Check for date column
        date_cols = [col for col in ['date', 'Date', 'DATE'] if col in daily_df.columns]
        if not date_cols:
            validation_result['errors'].append("No date column found (expected 'date', 'Date', or 'DATE')")
            validation_result['valid'] = False
        else:
            date_col = date_cols[0]
            validation_result['info'].append(f"Using date column: {date_col}")

            # Validate date column data type
            if not pd.api.types.is_datetime64_any_dtype(daily_df[date_col]):
                try:
                    pd.to_datetime(daily_df[date_col])
                    validation_result['warnings'].append(f"Date column '{date_col}' is not datetime but can be converted")
                except Exception as e:
                    validation_result['errors'].append(f"Date column '{date_col}' cannot be converted to datetime: {e}")
                    validation_result['valid'] = False

            # Check for date range coverage
            if validation_result['valid']:
                df_dates = pd.to_datetime(daily_df[date_col])
                min_date = df_dates.min()
                max_date = df_dates.max()

                validation_result['info'].append(f"Date range: {min_date.date()} to {max_date.date()}")

                # Check if week_ending is within or after data range
                if hasattr(cfg, 'week_ending') and cfg.week_ending:
                    if cfg.week_ending.date() < min_date.date():
                        validation_result['warnings'].append(f"week_ending ({cfg.week_ending.date()}) is before data start ({min_date.date()})")
                    elif cfg.week_ending.date() > max_date.date():
                        validation_result['warnings'].append(f"week_ending ({cfg.week_ending.date()}) is after data end ({max_date.date()})")

                # Check if we have enough data for trailing weeks
                if hasattr(cfg, 'trailing_weeks'):
                    days_needed = cfg.trailing_weeks * 7
                    days_available = (max_date - min_date).days + 1
                    if days_available < days_needed:
                        validation_result['warnings'].append(f"Limited data: need {days_needed} days for {cfg.trailing_weeks} weeks, have {days_available} days")

    # Validate WBRConfig
    if not hasattr(cfg, 'week_ending') or not hasattr(cfg, 'trailing_weeks') or not hasattr(cfg, 'aggf'):
        validation_result['errors'].append("cfg must be a WBRConfig instance with required attributes")
        validation_result['valid'] = False
    else:
        validation_result['info'].append(f"WBRConfig: {cfg.trailing_weeks} weeks ending {cfg.week_ending.date()}")

        # Validate aggregation functions
        if cfg.aggf:
            try:
                cfg.validate_aggf_columns(daily_df.columns.tolist())
                validation_result['info'].append(f"Aggregation functions validated for {len(cfg.aggf)} columns")
            except ValueError as e:
                validation_result['errors'].append(f"Aggregation validation failed: {e}")
                validation_result['valid'] = False
        else:
            validation_result['warnings'].append("No aggregation functions specified in WBRConfig")

    # Check for data quality issues
    if validation_result['valid'] and not daily_df.empty:
        # Check for duplicates
        if len(date_cols) > 0:
            date_col = date_cols[0]
            duplicates = daily_df.duplicated(subset=[date_col]).sum()
            if duplicates > 0:
                validation_result['warnings'].append(f"Found {duplicates} duplicate dates")

        # Check for missing values in key columns
        if cfg.aggf:
            for col in cfg.aggf.keys():
                if col in daily_df.columns:
                    missing_count = daily_df[col].isna().sum()
                    if missing_count > 0:
                        missing_pct = (missing_count / len(daily_df)) * 100
                        validation_result['warnings'].append(f"Column '{col}' has {missing_count} missing values ({missing_pct:.1f}%)")

    # Summary
    validation_result['summary'] = {
        'total_errors': len(validation_result['errors']),
        'total_warnings': len(validation_result['warnings']),
        'validation_passed': validation_result['valid']
    }

    # Raise exception if strict validation and errors found
    if strict_validation and not validation_result['valid']:
        error_msg = "WBR validation failed:\n" + "\n".join(validation_result['errors'])
        raise ValueError(error_msg)

    return validation_result


def validate_weekly_output(
    weekly_df: pd.DataFrame,
    expected_weeks: int,
    required_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate the output of compute_trailing_weeks function.

    Args:
        weekly_df: Output DataFrame from compute_trailing_weeks
        expected_weeks: Expected number of weeks
        required_columns: List of columns that must be present

    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'info': []
    }

    if weekly_df is None:
        validation_result['errors'].append("Weekly DataFrame is None")
        validation_result['valid'] = False
        return validation_result

    if weekly_df.empty:
        validation_result['errors'].append("Weekly DataFrame is empty")
        validation_result['valid'] = False
        return validation_result

    # Check number of weeks
    actual_weeks = len(weekly_df)
    if actual_weeks != expected_weeks:
        validation_result['errors'].append(f"Expected {expected_weeks} weeks, got {actual_weeks}")
        validation_result['valid'] = False
    else:
        validation_result['info'].append(f"Correct number of weeks: {actual_weeks}")

    # Check required columns
    if required_columns:
        missing_cols = set(required_columns) - set(weekly_df.columns)
        if missing_cols:
            validation_result['errors'].append(f"Missing required columns: {missing_cols}")
            validation_result['valid'] = False

    # Check for EndDate column (previously week_ending)
    date_col = 'EndDate' if 'EndDate' in weekly_df.columns else 'week_ending' if 'week_ending' in weekly_df.columns else None

    if date_col is None:
        validation_result['errors'].append("Missing 'EndDate' or 'week_ending' column")
        validation_result['valid'] = False
    else:
        # Validate week ending dates
        week_endings = pd.to_datetime(weekly_df[date_col])

        # Check chronological order
        if not week_endings.is_monotonic_increasing:
            validation_result['warnings'].append("Week ending dates are not in chronological order")

        # Check for 7-day intervals (allowing for some tolerance)
        if len(week_endings) > 1:
            intervals = week_endings.diff().dt.days.dropna()
            if not all(6 <= interval <= 8 for interval in intervals):  # Allow 1-day tolerance
                validation_result['warnings'].append("Week intervals are not exactly 7 days")

        validation_result['info'].append(f"Week range: {week_endings.min().date()} to {week_endings.max().date()}")

    return validation_result


# ============================================
# INTERNAL TEST AND DEMONSTRATION
# ============================================

if __name__ == "__main__":
    """
    Internal test block to demonstrate WBR functionality.
    Run this module directly to see the WBR system in action.
    """
    import sys
    import os

    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    try:
        from src.config.settings import WBRConfig
        from src.core.wbr_utility import (compute_wow, compute_last_prev, attach_wow,
                                          get_last_week_row, get_prev_week_row)
    except ImportError:
        # Alternative imports for direct execution
        from config.settings import WBRConfig
        from wbr_utility import (compute_wow, compute_last_prev, attach_wow,
                                 get_last_week_row, get_prev_week_row)

    print("=" * 60)
    print("WBR AGGREGATION SYSTEM - DEMONSTRATION")
    print("=" * 60)

    try:
        # 1. Create sample daily data
        print("\n1. Creating sample daily data...")

        import random
        random.seed(42)  # For reproducible results

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)  # 3 months of data

        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        # Generate realistic sample data
        sample_data = []
        for date in date_range:
            # Simulate weekly patterns and trends
            base_orders = 100 + (date.weekday() < 5) * 50  # Higher on weekdays
            base_revenue = base_orders * random.uniform(45, 85)

            # Add some trend and noise
            trend_factor = 1 + (date - start_date).days * 0.001  # Slight upward trend
            noise_factor = random.uniform(0.8, 1.2)

            orders = int(base_orders * trend_factor * noise_factor)
            revenue = round(base_revenue * trend_factor * noise_factor, 2)

            sample_data.append({
                'date': date,
                'orders': orders,
                'revenue': revenue,
                'customers': int(orders * random.uniform(0.7, 0.9))  # Some customers place multiple orders
            })

        daily_df = pd.DataFrame(sample_data)
        print(f"Generated {len(daily_df)} days of sample data")
        print(f"Date range: {daily_df['date'].min().date()} to {daily_df['date'].max().date()}")
        print(f"Sample data preview:\n{daily_df.head()}")

        # 2. Create WBR Configuration
        print("\n2. Creating WBR Configuration...")

        # Use last day of March as week_ending
        week_ending_date = "31-MAR-2024"

        config = WBRConfig(
            week_ending=week_ending_date,
            trailing_weeks=6,
            aggf={
                'orders': 'sum',
                'revenue': 'sum',
                'customers': 'sum'
            },
            week_number=13  # Example week number
        )
        print(f"Created WBRConfig: {config}")

        # 3. Validate inputs
        print("\n3. Validating inputs...")
        validation_result = validate_wbr_inputs(daily_df, config, strict_validation=False)

        print(f"Validation passed: {validation_result['valid']}")
        if validation_result['errors']:
            print(f"Errors: {validation_result['errors']}")
        if validation_result['warnings']:
            print(f"Warnings: {validation_result['warnings']}")
        for info in validation_result['info']:
            print(f"Info: {info}")

        # 4. Compute trailing weeks
        print("\n4. Computing trailing weeks aggregation...")

        weekly_df = compute_trailing_weeks(
            daily_df,
            config,
            fill_missing_weeks=True,
            strict_7day_span=True,
            use_absolute_week_number=True
        )

        print(f"Generated weekly DataFrame with {len(weekly_df)} weeks")
        print("\nWeekly aggregation results:")
        # Use the new column names from specification
        display_cols = ['WeekIndex', 'EndDate', 'WkLabel', 'orders', 'revenue', 'customers']
        print(weekly_df[display_cols].to_string())

        # 5. Validate output
        print("\n5. Validating weekly output...")
        output_validation = validate_weekly_output(
            weekly_df,
            expected_weeks=6,
            required_columns=['orders', 'revenue', 'customers']
        )

        print(f"Output validation passed: {output_validation['valid']}")
        if output_validation['errors']:
            print(f"Errors: {output_validation['errors']}")
        if output_validation['warnings']:
            print(f"Warnings: {output_validation['warnings']}")
        for info in output_validation['info']:
            print(f"Info: {info}")

        # 6. Demonstrate WOW comparison
        print("\n6. Computing Week-over-Week (WOW) comparisons...")

        wow_results = compute_wow(weekly_df)
        for metric, wow_pct in wow_results.items():
            if wow_pct is not None:
                print(f"  {metric.upper()}: {wow_pct:.1f}% change")
            else:
                print(f"  {metric.upper()}: No WOW data available")

        # 7. Demonstrate last vs prev comparison
        print("\n7. Computing last vs previous comparison...")

        last_prev_results = compute_last_prev(weekly_df)
        for metric, (prev, last) in last_prev_results.items():
            print(f"\n{metric.upper()}:")
            prev_str = f"{prev:.2f}" if prev is not None else "N/A"
            last_str = f"{last:.2f}" if last is not None else "N/A"
            print(f"  Previous week: {prev_str}")
            print(f"  Last week: {last_str}")
            if prev and last:
                change = last - prev
                pct_change = (change / prev * 100) if prev != 0 else 0
                print(f"  Change: {change:.2f} ({pct_change:.1f}%)")

        # 8. Test attach_wow function
        print("\n8. Testing attach_wow function...")

        df_with_wow = attach_wow(weekly_df, apply_to='last', decimals=2)
        last_row = df_with_wow.iloc[-1]
        print("WOW columns added to last week:")
        for col in df_with_wow.columns:
            if 'WOW_PCT' in col:
                value = last_row[col]
                if pd.notna(value):
                    print(f"  {col}: {value:.2f}%")

        # 9. Test get_last_week_row and get_prev_week_row
        print("\n9. Testing week row accessor functions...")

        last_week = get_last_week_row(weekly_df)
        prev_week = get_prev_week_row(weekly_df)

        print(f"Last week (WeekIndex={last_week['WeekIndex']}, {last_week['WkLabel']}):")
        print(f"  Date range: {last_week['Intervalo']}")
        print(f"  Orders: {last_week['orders']}")

        print(f"Previous week (WeekIndex={prev_week['WeekIndex']}, {prev_week['WkLabel']}):")
        print(f"  Date range: {prev_week['Intervalo']}")
        print(f"  Orders: {prev_week['orders']}")

        # 10. Test YAML configuration
        print("\n10. Testing YAML configuration...")

        yaml_config = """
        week_ending: "31-MAR-2024"
        trailing_weeks: 4
        week_number: 13
        aggf:
          orders: sum
          revenue: sum
          customers: sum
        """

        try:
            config_from_yaml = WBRConfig.from_yaml(yaml_config)
            print(f"Created from YAML: {config_from_yaml}")
        except ImportError:
            print("YAML support not available (PyYAML not installed)")
            # Test with dict instead
            print("Testing from_dict as alternative...")
            config_dict = {
                'week_ending': '31-MAR-2024',
                'trailing_weeks': 4,
                'week_number': 13,
                'aggf': {'orders': 'sum', 'revenue': 'sum', 'customers': 'sum'}
            }
            config_from_yaml = WBRConfig.from_dict(config_dict)
            print(f"Created from dict: {config_from_yaml}")

        # Test with 4 weeks instead of 6
        weekly_df_4 = compute_trailing_weeks(daily_df, config_from_yaml)
        print(f"4-week aggregation generated {len(weekly_df_4)} weeks")

        # Verify column structure
        expected_cols = ['WeekIndex', 'StartDate', 'EndDate', 'Date', 'Intervalo',
                        'WeekEndingWeekday', 'WkLabel', 'WkLabelFull']
        missing = [col for col in expected_cols if col not in weekly_df_4.columns]
        if not missing:
            print("✓ All required columns present in output")
        else:
            print(f"✗ Missing columns: {missing}")

        print("\n" + "=" * 60)
        print("WBR AGGREGATION SYSTEM DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)