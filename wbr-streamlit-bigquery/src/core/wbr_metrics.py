"""
WBR Metrics Calculator - Enhanced Version
Handles metric calculations, comparisons, and derived metrics for WBR system.
Integrated with existing BigQuery/Streamlit project.
"""

import pandas as pd
import numpy as np
import datetime
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from dateutil import relativedelta
from functools import lru_cache
import warnings

# Import from local module
from .wbr_utility import (
    create_trailing_six_weeks, 
    DataValidator, 
    WBRValidationError,
    prepare_data_for_wbr
)

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics for proper handling in calculations."""
    VALUE = "value"      # Absolute values (e.g., revenue, orders)
    RATIO = "ratio"      # Ratios/percentages (e.g., conversion rate)
    COUNT = "count"      # Counts (e.g., number of users)


@dataclass
class MetricDefinition:
    """Definition of a derived metric."""
    name: str
    formula: str
    metric_type: MetricType
    dependencies: List[str]
    description: str = ""
    
    def __hash__(self):
        return hash(self.name)


@dataclass
class ComparisonResult:
    """Result of metric comparison (WOW/YOY)."""
    metric_name: str
    comparison_type: str
    current_value: Decimal
    previous_value: Decimal
    absolute_change: Decimal
    percent_change: Optional[Decimal]
    is_improvement: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return {
            'metric': self.metric_name,
            'type': self.comparison_type,
            'current': self.current_value,
            'previous': self.previous_value,
            'absolute_change': self.absolute_change,
            'percent_change': self.percent_change,
            'is_improvement': self.is_improvement
        }


class WBRCalculator:
    """
    Advanced calculator for WBR metrics with caching and validation.
    Compatible with existing BigQuery/Streamlit infrastructure.
    """
    
    def __init__(
        self,
        daily_df: pd.DataFrame,
        week_ending: Union[datetime.date, datetime.datetime, pd.Timestamp],
        aggregation_map: Dict[str, str],
        value_metrics: Optional[List[str]] = None,
        ratio_metrics: Optional[List[str]] = None,
        num_weeks: int = 6,
        validate_data: bool = True,
        cache_enabled: bool = True,
        date_column: str = 'date',  # Default to project standard
        metric_column: str = 'metric_value'  # Default to project standard
    ):
        """
        Initialize WBR Calculator with BigQuery/Streamlit compatibility.
        
        Args:
            daily_df: DataFrame with daily data
            week_ending: End date of the analysis period
            aggregation_map: Dictionary of aggregation methods
            value_metrics: List of metrics treated as absolute values
            ratio_metrics: List of metrics treated as ratios
            num_weeks: Number of weeks in trailing window
            validate_data: Whether to validate input data
            cache_enabled: Whether to enable calculation caching
            date_column: Name of date column (default: 'date')
            metric_column: Name of primary metric column
        """
        # Store column names for compatibility
        self.date_column = date_column
        self.metric_column = metric_column
        
        # Prepare data
        self.daily_df = prepare_data_for_wbr(daily_df, date_column, metric_column)
        
        # Validate inputs if requested
        if validate_data:
            validator = DataValidator()
            validation = validator.validate_dataframe(
                self.daily_df,
                required_columns=list(aggregation_map.keys()),
                date_column=date_column
            )
            if not validation.is_valid:
                raise WBRValidationError(f"Data validation failed: {validation.errors}")
            if validation.warnings:
                for warning in validation.warnings:
                    logger.warning(warning)
        
        # Store configuration
        self.week_ending = pd.to_datetime(week_ending)
        self.aggregation_map = aggregation_map
        self.num_weeks = num_weeks
        self.cache_enabled = cache_enabled
        
        # Metric classification
        self.value_metrics = set(value_metrics or [])
        self.ratio_metrics = set(ratio_metrics or [])
        self._validate_metric_classification()
        
        # Metric definitions registry
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        
        # Build trailing windows
        logger.info(f"Building {num_weeks}-week trailing windows for {week_ending}")
        self._build_trailing_windows()
        
        # Initialize derived metrics DataFrames
        self.derived_cy = pd.DataFrame(index=self.cy_trailing_six_weeks.index)
        self.derived_py = pd.DataFrame(index=self.py_trailing_six_weeks.index)
        
        # Cache for expensive calculations
        self._calculation_cache = {} if cache_enabled else None
        
    def _validate_metric_classification(self):
        """Validate that metrics aren't classified in multiple categories."""
        overlap = self.value_metrics & self.ratio_metrics
        if overlap:
            raise ValueError(f"Metrics classified in multiple categories: {overlap}")
    
    def _build_trailing_windows(self):
        """Build current year and previous year trailing windows."""
        # Current Year (CY) trailing window
        self.cy_trailing_six_weeks = create_trailing_six_weeks(
            self.daily_df,
            self.week_ending,
            self.aggregation_map,
            self.num_weeks,
            date_column=self.date_column
        )
        
        # Previous Year (PY) trailing window - 364 days for better alignment
        py_week_ending = self.week_ending - datetime.timedelta(days=364)
        
        # Filter PY data
        days_back = (self.num_weeks * 7) - 1
        py_start = py_week_ending - datetime.timedelta(days=days_back)
        py_mask = (
            (self.daily_df[self.date_column] >= py_start) & 
            (self.daily_df[self.date_column] <= py_week_ending)
        )
        py_daily = self.daily_df[py_mask]
        
        if py_daily.empty:
            logger.warning(f"No data found for PY period: {py_start} to {py_week_ending}")
            # Create empty DataFrame with same structure
            self.py_trailing_six_weeks = pd.DataFrame(
                columns=self.cy_trailing_six_weeks.columns
            )
            for _ in range(self.num_weeks):
                self.py_trailing_six_weeks = pd.concat([
                    self.py_trailing_six_weeks,
                    pd.DataFrame({col: [pd.NA] for col in self.cy_trailing_six_weeks.columns})
                ], ignore_index=True)
        else:
            self.py_trailing_six_weeks = create_trailing_six_weeks(
                py_daily,
                py_week_ending,
                self.aggregation_map,
                self.num_weeks,
                date_column=self.date_column
            )
    
    def add_product_metric(
        self,
        name: str,
        col_a: str,
        col_b: str,
        description: str = ""
    ) -> 'WBRCalculator':
        """Add a metric calculated as product of two columns."""
        self._validate_columns_exist([col_a, col_b])
        
        self.metric_definitions[name] = MetricDefinition(
            name=name,
            formula=f"{col_a} * {col_b}",
            metric_type=MetricType.VALUE,
            dependencies=[col_a, col_b],
            description=description or f"Product of {col_a} and {col_b}"
        )
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            self.derived_cy[name] = (
                self._get_column(self.cy_trailing_six_weeks, col_a) * 
                self._get_column(self.cy_trailing_six_weeks, col_b)
            )
            self.derived_py[name] = (
                self._get_column(self.py_trailing_six_weeks, col_a) * 
                self._get_column(self.py_trailing_six_weeks, col_b)
            )
        
        logger.debug(f"Added product metric: {name} = {col_a} * {col_b}")
        return self
    
    def add_diff_metric(
        self,
        name: str,
        col_a: str,
        col_b: str,
        description: str = ""
    ) -> 'WBRCalculator':
        """Add a metric calculated as difference between two columns."""
        self._validate_columns_exist([col_a, col_b])
        
        self.metric_definitions[name] = MetricDefinition(
            name=name,
            formula=f"{col_a} - {col_b}",
            metric_type=MetricType.VALUE,
            dependencies=[col_a, col_b],
            description=description or f"Difference between {col_a} and {col_b}"
        )
        
        self.derived_cy[name] = (
            self._get_column(self.cy_trailing_six_weeks, col_a) - 
            self._get_column(self.cy_trailing_six_weeks, col_b)
        )
        self.derived_py[name] = (
            self._get_column(self.py_trailing_six_weeks, col_a) - 
            self._get_column(self.py_trailing_six_weeks, col_b)
        )
        
        logger.debug(f"Added difference metric: {name} = {col_a} - {col_b}")
        return self
    
    def add_div_metric(
        self,
        name: str,
        numerator: str,
        denominator: str,
        handle_zero: str = "nan",
        description: str = ""
    ) -> 'WBRCalculator':
        """Add a metric calculated as division of two columns."""
        self._validate_columns_exist([numerator, denominator])
        
        self.metric_definitions[name] = MetricDefinition(
            name=name,
            formula=f"{numerator} / {denominator}",
            metric_type=MetricType.RATIO,
            dependencies=[numerator, denominator],
            description=description or f"Ratio of {numerator} to {denominator}"
        )
        
        self.derived_cy[name] = self._safe_divide(
            self._get_column(self.cy_trailing_six_weeks, numerator),
            self._get_column(self.cy_trailing_six_weeks, denominator),
            handle_zero
        )
        self.derived_py[name] = self._safe_divide(
            self._get_column(self.py_trailing_six_weeks, numerator),
            self._get_column(self.py_trailing_six_weeks, denominator),
            handle_zero
        )
        
        logger.debug(f"Added division metric: {name} = {numerator} / {denominator}")
        return self
    
    def add_custom_metric(
        self,
        name: str,
        func: callable,
        dependencies: List[str],
        metric_type: MetricType = MetricType.VALUE,
        description: str = ""
    ) -> 'WBRCalculator':
        """Add a custom metric using a user-defined function."""
        self._validate_columns_exist(dependencies)
        
        self.metric_definitions[name] = MetricDefinition(
            name=name,
            formula="custom",
            metric_type=metric_type,
            dependencies=dependencies,
            description=description or f"Custom metric: {name}"
        )
        
        try:
            self.derived_cy[name] = func(self.cy_trailing_six_weeks)
            self.derived_py[name] = func(self.py_trailing_six_weeks)
        except Exception as e:
            logger.error(f"Failed to calculate custom metric {name}: {e}")
            raise ValueError(f"Custom metric calculation failed: {e}")
        
        logger.debug(f"Added custom metric: {name}")
        return self
    
    @lru_cache(maxsize=128)
    def compute_wow(self, metric: str) -> Dict[str, ComparisonResult]:
        """Compute Week-over-Week comparison for a metric."""
        cy_result = self._compute_wow_single(
            self._get_metric_series(metric, 'cy'),
            metric,
            'CY'
        )
        
        py_result = self._compute_wow_single(
            self._get_metric_series(metric, 'py'),
            metric,
            'PY'
        )
        
        return {
            'CY': cy_result,
            'PY': py_result
        }
    
    def _compute_wow_single(
        self,
        series: pd.Series,
        metric: str,
        year_label: str
    ) -> ComparisonResult:
        """Compute WOW for a single series."""
        try:
            valid_values = series.dropna()
            if len(valid_values) < 2:
                logger.warning(f"Insufficient data for WOW calculation: {metric} ({year_label})")
                return ComparisonResult(
                    metric_name=f"{metric}_{year_label}",
                    comparison_type="WOW",
                    current_value=np.nan,
                    previous_value=np.nan,
                    absolute_change=np.nan,
                    percent_change=None
                )
            
            current = valid_values.iloc[-1]
            previous = valid_values.iloc[-2]
            
            absolute_change = current - previous
            percent_change = None if previous == 0 else ((current / previous - 1) * 100)
            
            is_improvement = None
            if metric in self.ratio_metrics:
                is_improvement = absolute_change > 0
            elif metric in self.value_metrics:
                is_improvement = absolute_change > 0
            
            return ComparisonResult(
                metric_name=f"{metric}_{year_label}",
                comparison_type="WOW",
                current_value=Decimal(str(current)),
                previous_value=Decimal(str(previous)),
                absolute_change=Decimal(str(absolute_change)),
                percent_change=Decimal(str(percent_change)) if percent_change else None,
                is_improvement=is_improvement
            )
            
        except Exception as e:
            logger.error(f"WOW calculation failed for {metric}: {e}")
            return ComparisonResult(
                metric_name=f"{metric}_{year_label}",
                comparison_type="WOW",
                current_value=np.nan,
                previous_value=np.nan,
                absolute_change=np.nan,
                percent_change=None
            )
    
    @lru_cache(maxsize=128)
    def compute_yoy_last_week(self, metric: str) -> ComparisonResult:
        """Compute Year-over-Year comparison for the most recent week."""
        cy_series = self._get_metric_series(metric, 'cy')
        py_series = self._get_metric_series(metric, 'py')
        
        try:
            cy_last = cy_series.dropna().iloc[-1] if not cy_series.dropna().empty else np.nan
            py_last = py_series.dropna().iloc[-1] if not py_series.dropna().empty else np.nan
            
            if pd.isna(cy_last) or pd.isna(py_last):
                logger.warning(f"Missing data for YOY calculation: {metric}")
                return ComparisonResult(
                    metric_name=metric,
                    comparison_type="YOY",
                    current_value=np.nan,
                    previous_value=np.nan,
                    absolute_change=np.nan,
                    percent_change=None
                )
            
            absolute_change = cy_last - py_last
            percent_change = None if py_last == 0 else ((cy_last / py_last - 1) * 100)
            
            return ComparisonResult(
                metric_name=metric,
                comparison_type="YOY",
                current_value=Decimal(str(cy_last)),
                previous_value=Decimal(str(py_last)),
                absolute_change=Decimal(str(absolute_change)),
                percent_change=Decimal(str(percent_change)) if percent_change else None,
                is_improvement=absolute_change > 0
            )
            
        except Exception as e:
            logger.error(f"YOY calculation failed for {metric}: {e}")
            return ComparisonResult(
                metric_name=metric,
                comparison_type="YOY",
                current_value=np.nan,
                previous_value=np.nan,
                absolute_change=np.nan,
                percent_change=None
            )
    
    def export_trailing(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Export combined DataFrames with original and derived metrics."""
        cy = pd.concat([self.cy_trailing_six_weeks, self.derived_cy], axis=1)
        
        py_original = self.py_trailing_six_weeks.add_prefix("PY__")
        py_derived = self.derived_py.add_prefix("PY__")
        py = pd.concat([py_original, py_derived], axis=1)
        
        logger.info(f"Exported trailing windows: CY shape={cy.shape}, PY shape={py.shape}")
        return cy, py
    
    def export_summary(self) -> pd.DataFrame:
        """Export a summary DataFrame with key metrics and comparisons."""
        summary_data = []
        
        all_metrics = set(self.aggregation_map.keys()) | set(self.derived_cy.columns)
        
        for metric in all_metrics:
            try:
                wow_result = self.compute_wow(metric)
                yoy_result = self.compute_yoy_last_week(metric)
                
                summary_data.append({
                    'Metric': metric,
                    'Current_Week': wow_result['CY'].current_value,
                    'Previous_Week': wow_result['CY'].previous_value,
                    'WOW_%': wow_result['CY'].percent_change,
                    'YOY_%': yoy_result.percent_change,
                    'Type': self._get_metric_type(metric).value
                })
            except Exception as e:
                logger.warning(f"Failed to summarize metric {metric}: {e}")
                continue
        
        return pd.DataFrame(summary_data)
    
    def get_metrics_for_streamlit(self) -> Dict[str, Any]:
        """
        Get metrics formatted for Streamlit display.
        Compatible with existing Streamlit components.
        """
        cy, py = self.export_trailing()
        summary = self.export_summary()
        
        return {
            'current_year': cy.to_dict('records'),
            'previous_year': py.to_dict('records'),
            'summary': summary.to_dict('records'),
            'metrics': {
                'total_metrics': len(summary),
                'improved_metrics': len(summary[summary['WOW_%'] > 0]) if 'WOW_%' in summary else 0,
                'declined_metrics': len(summary[summary['WOW_%'] < 0]) if 'WOW_%' in summary else 0
            }
        }
    
    def get_dashboard_kpis(self) -> Dict[str, Any]:
        """
        Get simplified KPIs for dashboard cards (replacement for calcular_kpis).
        Uses the robust 6-week trailing window logic but returns simple KPIs.
        
        Returns:
            Dictionary compatible with existing dashboard KPI cards
        """
        try:
            # Get the primary metric column
            metric_col = self.metric_column
            
            # Check if metric exists in original or derived
            if metric_col in self.cy_trailing_six_weeks.columns:
                cy_series = self.cy_trailing_six_weeks[metric_col]
                py_series = self.py_trailing_six_weeks[metric_col]
            elif metric_col in self.derived_cy.columns:
                cy_series = self.derived_cy[metric_col]
                py_series = self.derived_py[metric_col]
            else:
                # Fallback to first numeric column
                numeric_cols = self.cy_trailing_six_weeks.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    metric_col = numeric_cols[0]
                    cy_series = self.cy_trailing_six_weeks[metric_col]
                    py_series = self.py_trailing_six_weeks[metric_col]
                else:
                    raise ValueError("No numeric columns found for KPI calculation")
            
            # Last week value (week 6, index 5)
            ultima_semana = cy_series.iloc[5] if not pd.isna(cy_series.iloc[5]) else 0
            
            # Previous week value (week 5, index 4)
            semana_anterior = cy_series.iloc[4] if not pd.isna(cy_series.iloc[4]) else 0
            
            # Last week previous year
            ultima_semana_py = py_series.iloc[5] if not pd.isna(py_series.iloc[5]) else 0
            
            # Calculate WOW
            wow_pct = 0
            wow_abs = ultima_semana - semana_anterior
            if semana_anterior != 0:
                wow_pct = ((ultima_semana / semana_anterior - 1) * 100)
            
            # Calculate YOY for last week
            yoy_pct = 0
            if ultima_semana_py != 0:
                yoy_pct = ((ultima_semana / ultima_semana_py - 1) * 100)
            
            # Calculate month-to-date (sum of current month weeks)
            # This is simplified - in production you might want actual MTD
            mes_atual = cy_series.sum()  # Sum of all 6 weeks as proxy for MTD
            mes_py = py_series.sum()
            
            mtd_pct = 0
            if mes_py != 0:
                mtd_pct = ((mes_atual / mes_py - 1) * 100)
            
            return {
                'ultima_semana': Decimal(str(ultima_semana)),
                'var_semanal': Decimal(str(wow_pct)),
                'yoy_semanal': Decimal(str(yoy_pct)),
                'mes_atual': Decimal(str(mes_atual)),
                'yoy_mensal': Decimal(str(mtd_pct)),
                'trimestre_atual': Decimal(str(mes_atual)),  # Simplified
                'yoy_trimestral': Decimal(str(mtd_pct)),     # Simplified
                'ano_atual': Decimal(str(mes_atual)),         # Simplified
                'yoy_anual': Decimal(str(mtd_pct)),          # Simplified
                'wow_pct': Decimal(str(wow_pct)),
                'wow_abs': Decimal(str(wow_abs)),
                'mtd_atual': Decimal(str(mes_atual)),
                'mtd_pct': Decimal(str(mtd_pct))
            }
            
        except Exception as e:
            logger.warning(f"Error calculating dashboard KPIs: {e}")
            # Return safe defaults
            return {
                'ultima_semana': 0,
                'var_semanal': 0,
                'yoy_semanal': 0,
                'mes_atual': 0,
                'yoy_mensal': 0,
                'trimestre_atual': 0,
                'yoy_trimestral': 0,
                'ano_atual': 0,
                'yoy_anual': 0,
                'wow_pct': 0,
                'wow_abs': 0,
                'mtd_atual': 0,
                'mtd_pct': 0
            }
    
    def _validate_columns_exist(self, columns: List[str]):
        """Validate that required columns exist in data."""
        all_columns = set(self.cy_trailing_six_weeks.columns) | set(self.derived_cy.columns)
        missing = set(columns) - all_columns
        if missing:
            raise ValueError(f"Columns not found: {missing}")
    
    def _get_column(self, df: pd.DataFrame, col: str) -> pd.Series:
        """Get column from main DataFrame or derived metrics."""
        if col in df.columns:
            return df[col]
        elif col in self.derived_cy.columns:
            return self.derived_cy[col] if df is self.cy_trailing_six_weeks else self.derived_py[col]
        else:
            raise ValueError(f"Column '{col}' not found")
    
    def _get_metric_series(self, metric: str, year: str) -> pd.Series:
        """Get metric series for CY or PY."""
        if year == 'cy':
            if metric in self.derived_cy.columns:
                return self.derived_cy[metric]
            return self.cy_trailing_six_weeks[metric] if metric in self.cy_trailing_six_weeks else pd.Series()
        else:
            if metric in self.derived_py.columns:
                return self.derived_py[metric]
            return self.py_trailing_six_weeks[metric] if metric in self.py_trailing_six_weeks else pd.Series()
    
    def _get_metric_type(self, metric: str) -> MetricType:
        """Determine the type of a metric."""
        if metric in self.metric_definitions:
            return self.metric_definitions[metric].metric_type
        elif metric in self.ratio_metrics:
            return MetricType.RATIO
        elif metric in self.value_metrics:
            return MetricType.VALUE
        else:
            return MetricType.COUNT
    
    @staticmethod
    def _safe_divide(
        numerator: pd.Series,
        denominator: pd.Series,
        handle_zero: str = "nan"
    ) -> pd.Series:
        """Safely divide two series handling division by zero."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            
            if handle_zero == "nan":
                return numerator / denominator
            elif handle_zero == "zero":
                return numerator.divide(denominator).fillna(0)
            elif handle_zero == "inf":
                result = numerator / denominator
                return result.replace([np.inf, -np.inf], np.nan)
            else:
                raise ValueError(f"Invalid handle_zero option: {handle_zero}")


# Função para compatibilidade com o código existente (substitui calcular_kpis de kpis.py)
def calcular_kpis(df: pd.DataFrame, data_referencia: pd.Timestamp = None, coluna_data: str = 'date', coluna_metrica: str = 'metric_value') -> Dict[str, Any]:
    """
    Função de compatibilidade que substitui a antiga calcular_kpis de kpis.py.
    Usa a lógica robusta das 6 semanas móveis do WBRCalculator.
    
    Args:
        df: DataFrame com dados
        data_referencia: Data de referência para análise
        coluna_data: Nome da coluna de data
        coluna_metrica: Nome da coluna de métrica principal
        
    Returns:
        Dictionary com KPIs para o dashboard
    """
    try:
        # Se data_referencia não for fornecida, usar a última data disponível
        if data_referencia is None:
            if coluna_data in df.columns:
                data_referencia = df[coluna_data].max()
            else:
                data_referencia = pd.Timestamp.now()
        
        # Auto-detectar colunas numéricas para agregação
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if coluna_data in numeric_cols:
            numeric_cols.remove(coluna_data)
        
        # Se não houver colunas numéricas, usar apenas a coluna métrica
        if not numeric_cols and coluna_metrica in df.columns:
            numeric_cols = [coluna_metrica]
        
        # Criar mapa de agregação (somar todas as métricas numéricas)
        aggregation_map = {col: 'sum' for col in numeric_cols}
        
        # Criar calculadora WBR com a lógica das 6 semanas móveis
        calc = WBRCalculator(
            df,
            data_referencia,
            aggregation_map,
            value_metrics=numeric_cols,
            ratio_metrics=[],
            validate_data=False,  # Skip validation for speed
            cache_enabled=False,
            date_column=coluna_data,
            metric_column=coluna_metrica
        )
        
        # Retornar KPIs formatados para o dashboard
        return calc.get_dashboard_kpis()
        
    except Exception as e:
        logger.error(f"Error in calcular_kpis compatibility function: {e}")
        # Return safe defaults to prevent dashboard crash
        return {
            'ultima_semana': 0,
            'var_semanal': 0,
            'yoy_semanal': 0,
            'mes_atual': 0,
            'yoy_mensal': 0,
            'trimestre_atual': 0,
            'yoy_trimestral': 0,
            'ano_atual': 0,
            'yoy_anual': 0,
            'wow_pct': 0,
            'wow_abs': 0,
            'mtd_atual': 0,
            'mtd_pct': 0
        }


# Backward compatibility class
    """
    Simplified WBR calculator for backward compatibility.
    Use WBRCalculator for new implementations.
    """
    
    def __init__(self, df: pd.DataFrame, week_ending: datetime.date):
        """Initialize with minimal parameters."""
        # Auto-detect numeric columns for aggregation
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        agg_map = {col: 'sum' for col in numeric_cols}
        
        self.calculator = WBRCalculator(
            df,
            week_ending,
            agg_map,
            validate_data=False,
            cache_enabled=False
        )
    
    def get_trailing_weeks(self) -> pd.DataFrame:
        """Get current year trailing weeks."""
        return self.calculator.cy_trailing_six_weeks
    
    def get_comparison(self) -> pd.DataFrame:
        """Get simple comparison summary."""
        return self.calculator.export_summary()