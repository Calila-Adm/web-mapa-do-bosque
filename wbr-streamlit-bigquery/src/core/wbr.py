import pandas as pd
import logging
from typing import Dict, Any, Optional
import datetime

from .processing import processar_dados_wbr
from .charts import criar_grafico_wbr
from .wbr_metrics import WBRCalculator

logger = logging.getLogger(__name__)

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


def calcular_metricas_wbr(
    df: pd.DataFrame,
    data_referencia: Optional[datetime.date] = None,
    coluna_data: str = 'date',
    coluna_metrica: str = 'metric_value',
    metricas_derivadas: Optional[Dict[str, Dict]] = None
) -> Dict[str, Any]:
    """
    Calculate WBR metrics using the enhanced WBRCalculator class.
    
    Args:
        df: Input DataFrame with metrics
        data_referencia: Reference date for analysis (default: latest date)
        coluna_data: Date column name
        coluna_metrica: Primary metric column name
        metricas_derivadas: Optional dict of derived metrics to calculate
        
    Returns:
        Dictionary with calculated metrics, comparisons, and summaries
    """
    try:
        # Ensure date column is datetime
        df_work = df.copy()
        df_work[coluna_data] = pd.to_datetime(df_work[coluna_data])
        
        # Use data_referencia or get latest date
        if data_referencia is None:
            data_referencia = df_work[coluna_data].max()
        else:
            data_referencia = pd.to_datetime(data_referencia)
        
        # Auto-detect numeric columns for aggregation
        numeric_cols = df_work.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if coluna_data in numeric_cols:
            numeric_cols.remove(coluna_data)
        
        # Build aggregation map (default to sum for all numeric columns)
        aggregation_map = {col: 'sum' for col in numeric_cols}
        
        # Classify metrics (heuristic: ratios/rates are usually percentages)
        ratio_metrics = [col for col in numeric_cols if any(
            term in col.lower() for term in ['rate', 'ratio', 'percent', 'pct']
        )]
        value_metrics = [col for col in numeric_cols if col not in ratio_metrics]
        
        logger.info(f"Auto-detected {len(numeric_cols)} numeric columns for WBR analysis")
        
        # Create WBRCalculator instance
        calc = WBRCalculator(
            df_work,
            data_referencia,
            aggregation_map,
            value_metrics=value_metrics,
            ratio_metrics=ratio_metrics,
            validate_data=False,  # Skip validation for speed
            cache_enabled=True,
            date_column=coluna_data,
            metric_column=coluna_metrica
        )
        
        # Add derived metrics if specified
        if metricas_derivadas:
            for metric_name, config in metricas_derivadas.items():
                metric_type = config.get('type', 'division')
                
                if metric_type == 'division':
                    calc.add_div_metric(
                        metric_name,
                        config['numerator'],
                        config['denominator'],
                        handle_zero=config.get('handle_zero', 'nan'),
                        description=config.get('description', '')
                    )
                elif metric_type == 'product':
                    calc.add_product_metric(
                        metric_name,
                        config['col_a'],
                        config['col_b'],
                        description=config.get('description', '')
                    )
                elif metric_type == 'difference':
                    calc.add_diff_metric(
                        metric_name,
                        config['col_a'],
                        config['col_b'],
                        description=config.get('description', '')
                    )
                
                logger.debug(f"Added derived metric: {metric_name}")
        
        # Calculate all comparisons
        comparisons = {}
        for metric in numeric_cols:
            try:
                wow_result = calc.compute_wow(metric)
                yoy_result = calc.compute_yoy_last_week(metric)
                
                comparisons[metric] = {
                    'wow': {
                        'current': wow_result['CY'].current_value,
                        'previous': wow_result['CY'].previous_value,
                        'percent_change': wow_result['CY'].percent_change,
                        'is_improvement': wow_result['CY'].is_improvement
                    },
                    'yoy': {
                        'current': yoy_result.current_value,
                        'previous': yoy_result.previous_value,
                        'percent_change': yoy_result.percent_change,
                        'is_improvement': yoy_result.is_improvement
                    }
                }
            except Exception as e:
                logger.warning(f"Failed to calculate comparisons for {metric}: {e}")
                comparisons[metric] = {
                    'wow': {'current': None, 'previous': None, 'percent_change': None},
                    'yoy': {'current': None, 'previous': None, 'percent_change': None}
                }
        
        # Get formatted results for Streamlit
        streamlit_data = calc.get_metrics_for_streamlit()
        
        # Build comprehensive result
        result = {
            'success': True,
            'reference_date': data_referencia.isoformat(),
            'metrics_analyzed': len(numeric_cols),
            'comparisons': comparisons,
            'trailing_weeks': {
                'current_year': calc.cy_trailing_six_weeks.to_dict('records'),
                'previous_year': calc.py_trailing_six_weeks.to_dict('records')
            },
            'summary': calc.export_summary().to_dict('records'),
            'streamlit_data': streamlit_data,
            'metadata': {
                'value_metrics': value_metrics,
                'ratio_metrics': ratio_metrics,
                'derived_metrics': list(calc.metric_definitions.keys())
            }
        }
        
        logger.info(f"WBR metrics calculated successfully for {len(numeric_cols)} metrics")
        return result
        
    except Exception as e:
        logger.error(f"Failed to calculate WBR metrics: {e}")
        # Return error result with fallback to basic processing
        return {
            'success': False,
            'error': str(e),
            'reference_date': data_referencia.isoformat() if data_referencia else None,
            'fallback_data': {
                'message': 'Using simplified processing due to error',
                'basic_stats': {
                    'row_count': len(df),
                    'date_range': f"{df[coluna_data].min()} to {df[coluna_data].max()}" if coluna_data in df else None
                }
            }
        }
