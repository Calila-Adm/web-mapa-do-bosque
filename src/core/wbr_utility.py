"""
WBR Utility Module - Enhanced Version
Handles temporal window operations and data padding for WBR system.
Integrated with existing project structure.
"""

import pandas as pd
import numpy as np
import datetime
import logging
from decimal import Decimal
from typing import Dict, Optional, Union, Any, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: list
    warnings: list


class WBRValidationError(Exception):
    """Custom exception for WBR validation errors."""
    pass


class DataValidator:
    """Validates input data for WBR processing."""
    
    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame,
        required_columns: list = None,
        date_column: str = 'date'  # Changed default to match project standard
    ) -> ValidationResult:
        """
        Validates DataFrame structure and content.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            date_column: Name of the date column (default: 'date' for BigQuery compatibility)
            
        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        
        if df is None or df.empty:
            errors.append("DataFrame is empty or None")
            return ValidationResult(False, errors, warnings)
        
        # Also check for 'Date' for backward compatibility
        if date_column not in df.columns and 'Date' not in df.columns:
            errors.append(f"Required column '{date_column}' or 'Date' not found")
        
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                errors.append(f"Missing required columns: {missing}")
        
        # Check for datetime type
        actual_date_col = date_column if date_column in df.columns else 'Date' if 'Date' in df.columns else None
        if actual_date_col:
            if not pd.api.types.is_datetime64_any_dtype(df[actual_date_col]):
                warnings.append(f"Column '{actual_date_col}' is not datetime type")
        
        # Check for duplicate dates
        if actual_date_col and df[actual_date_col].duplicated().any():
            warnings.append("Duplicate dates found in data")
        
        # Check for negative values in numeric columns (excluding ratios and percentages)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Skip columns that might legitimately have negative values
            if 'growth' in col.lower() or 'change' in col.lower() or 'diff' in col.lower():
                continue
            if (df[col] < 0).any():
                warnings.append(f"Negative values found in column '{col}'")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


def create_new_row(
    week_end_date: Optional[Union[datetime.date, datetime.datetime, str]],
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Creates a new row with NaN values for a given week ending date.
    Maintains compatibility with existing codebase.
    
    Args:
        week_end_date: The ending date of the week
        df: DataFrame to add the row to
        
    Returns:
        DataFrame with the new row added
    """
    try:
        date_obj = None
        if week_end_date is not None:
            if isinstance(week_end_date, (datetime.date, datetime.datetime)):
                date_obj = pd.to_datetime(week_end_date)
            else:
                date_obj = pd.to_datetime(week_end_date)
        
        row = {col: pd.NA for col in df.columns}
        
        # Support both 'Date' and 'date' columns
        date_col = 'Date' if 'Date' in df.columns else 'date' if 'date' in df.columns else None
        if date_col:
            row[date_col] = date_obj
        
        # Create new DataFrame with the row and concatenate
        new_row_df = pd.DataFrame([row])
        if df.empty:
            return new_row_df
        return pd.concat([new_row_df, df], ignore_index=True)
        
    except Exception as e:
        logger.error(f"Error creating new row: {e}")
        raise ValueError(f"Failed to create new row: {e}")


def create_trailing_six_weeks(
    df: pd.DataFrame,
    week_ending: Union[datetime.date, datetime.datetime],
    aggregation_map: Dict[str, str],
    num_weeks: int = 6,
    validate_input: bool = True,
    date_column: Optional[str] = None
) -> pd.DataFrame:
    """
    Creates a weekly aggregated DataFrame for trailing N weeks.
    Enhanced version with validation and better error handling.
    
    Args:
        df: DataFrame with daily data
        week_ending: The last date of the analysis period
        aggregation_map: Dictionary mapping column names to aggregation functions
        num_weeks: Number of weeks to include (default: 6)
        validate_input: Whether to validate input data (default: True)
        date_column: Name of date column (auto-detected if None)
        
    Returns:
        DataFrame with exactly N weeks of aggregated data
    """
    # Auto-detect date column if not specified
    if date_column is None:
        if 'date' in df.columns:
            date_column = 'date'
        elif 'Date' in df.columns:
            date_column = 'Date'
        else:
            raise ValueError("No date column found. Please specify date_column parameter.")
    
    if validate_input:
        validation = DataValidator.validate_dataframe(
            df, 
            required_columns=list(aggregation_map.keys()),
            date_column=date_column
        )
        if not validation.is_valid:
            raise WBRValidationError(f"Validation failed: {validation.errors}")
        if validation.warnings:
            for warning in validation.warnings:
                logger.warning(warning)
    
    # Ensure we work with a copy
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    week_ending = pd.to_datetime(week_ending)
    
    # Map ISO weekday to pandas resample rule
    week_map = {
        1: 'W-MON', 2: 'W-TUE', 3: 'W-WED', 
        4: 'W-THU', 5: 'W-FRI', 6: 'W-SAT', 7: 'W-SUN'
    }
    
    iso_day = week_ending.isoweekday()
    if iso_day not in week_map:
        raise ValueError(f"Invalid ISO weekday: {iso_day}")
    
    rule = week_map[iso_day]
    logger.debug(f"Using resample rule: {rule} for week ending on {week_ending}")
    
    # Calculate date range (N weeks + buffer)
    days_to_look_back = (num_weeks * 7) - 1
    start_date = week_ending - datetime.timedelta(days=days_to_look_back)
    
    # Filter data for the period
    mask = (df[date_column] <= week_ending) & (df[date_column] >= start_date)
    trailing_daily = df.loc[mask].copy()
    
    if trailing_daily.empty:
        logger.warning(f"No data found between {start_date} and {week_ending}")
    
    try:
        # Perform weekly aggregation
        weekly = (trailing_daily
                 .resample(rule, on=date_column, label='right', closed='right')
                 .agg(aggregation_map)
                 .reset_index()
                 .sort_values(date_column))
        
        # Rename date column back to standard name if needed
        if date_column != 'Date':
            weekly = weekly.rename(columns={date_column: 'Date'})
        
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise ValueError(f"Failed to aggregate data: {e}")
    
    # Ensure exactly N weeks with padding if necessary
    date_col_final = 'Date'
    if weekly.empty:
        earliest_week = week_ending
    else:
        earliest_week = weekly.iloc[0][date_col_final]
    
    # Add padding rows if needed
    while len(weekly) < num_weeks:
        earliest_week -= datetime.timedelta(days=7)
        weekly = create_new_row(earliest_week, weekly)
        logger.debug(f"Added padding row for week ending {earliest_week}")
    
    # Ensure we have exactly N weeks
    weekly = weekly.sort_values(date_col_final).tail(num_weeks).reset_index(drop=True)
    
    logger.info(f"Created {num_weeks}-week trailing window with {len(weekly)} rows")
    return weekly


def exclude_empty_or_all_na(
    df: pd.DataFrame,
    threshold: Decimal = Decimal('1.0')
) -> pd.DataFrame:
    """
    Removes columns that are empty or have too many NA values.
    
    Args:
        df: DataFrame to clean
        threshold: Proportion of NA values to trigger removal (1.0 = all NA)
        
    Returns:
        DataFrame with empty/NA columns removed
    """
    na_proportion = df.isna().sum() / len(df)
    columns_to_keep = na_proportion[na_proportion < threshold].index
    
    removed = set(df.columns) - set(columns_to_keep)
    if removed:
        logger.info(f"Removed columns with >{threshold*100}% NA: {removed}")
    
    return df[columns_to_keep]


def get_week_bounds(
    week_ending: datetime.date,
    num_weeks: int = 6
) -> Tuple[datetime.date, datetime.date]:
    """
    Calculate the start and end dates for a trailing N-week period.
    
    Args:
        week_ending: Last date of the period
        num_weeks: Number of weeks to include
        
    Returns:
        Tuple of (start_date, end_date)
    """
    days_back = (num_weeks * 7) - 1
    start_date = week_ending - datetime.timedelta(days=days_back)
    return start_date, week_ending


def prepare_data_for_wbr(
    df: pd.DataFrame,
    date_column: str = 'date',
    metric_column: str = 'metric_value'
) -> pd.DataFrame:
    """
    Prepare data for WBR processing, ensuring compatibility with existing system.
    
    Args:
        df: Input DataFrame
        date_column: Name of date column
        metric_column: Name of metric column
        
    Returns:
        Prepared DataFrame with standardized columns
    """
    df_prepared = df.copy()
    
    # Ensure date column is datetime
    df_prepared[date_column] = pd.to_datetime(df_prepared[date_column])
    
    # Sort by date
    df_prepared = df_prepared.sort_values(date_column)
    
    # Remove duplicates if any
    df_prepared = df_prepared.drop_duplicates(subset=[date_column])
    
    # Reset index
    df_prepared = df_prepared.reset_index(drop=True)
    
    return df_prepared


# ============================================
# WBR METRICS UTILITIES (WOW, Last vs Prev)
# ============================================

def compute_wow_comparison(
    weekly_df: pd.DataFrame,
    metric_column: str,
    date_column: str = 'week_ending'
) -> Dict[str, Any]:
    """
    Compute Week-over-Week (WOW) comparison from weekly aggregated data.

    Args:
        weekly_df: DataFrame with weekly data (must be sorted by date)
        metric_column: Name of the metric column to compare
        date_column: Name of the date column (default: 'week_ending')

    Returns:
        Dictionary with WOW comparison results
    """
    if len(weekly_df) < 2:
        return {
            'current': None,
            'previous': None,
            'absolute_change': None,
            'percent_change': None,
            'comparison_type': 'wow'
        }

    # Get last two weeks (most recent first after sorting)
    weekly_sorted = weekly_df.sort_values(date_column, ascending=False)

    current_week = weekly_sorted.iloc[0]
    previous_week = weekly_sorted.iloc[1]

    current_value = current_week[metric_column]
    previous_value = previous_week[metric_column]

    # Handle NaN values
    if pd.isna(current_value) or pd.isna(previous_value):
        return {
            'current': current_value,
            'previous': previous_value,
            'absolute_change': None,
            'percent_change': None,
            'comparison_type': 'wow'
        }

    absolute_change = current_value - previous_value
    percent_change = None

    if previous_value != 0:
        percent_change = (absolute_change / previous_value) * 100

    return {
        'current': current_value,
        'previous': previous_value,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'comparison_type': 'wow',
        'current_date': current_week[date_column],
        'previous_date': previous_week[date_column]
    }


def compute_last_vs_prev_weeks(
    weekly_df: pd.DataFrame,
    metric_columns: Union[str, List[str]],
    date_column: str = 'week_ending',
    num_periods: int = 2
) -> Dict[str, Dict[str, Any]]:
    """
    Compare last N periods for multiple metrics.

    Args:
        weekly_df: DataFrame with weekly data
        metric_columns: Single column name or list of column names
        date_column: Name of the date column
        num_periods: Number of periods to compare (default: 2)

    Returns:
        Dictionary with comparison results for each metric
    """
    if isinstance(metric_columns, str):
        metric_columns = [metric_columns]

    if len(weekly_df) < num_periods:
        logger.warning(f"Insufficient data: need {num_periods} periods, got {len(weekly_df)}")
        return {}

    # Sort by date descending (most recent first)
    weekly_sorted = weekly_df.sort_values(date_column, ascending=False)

    results = {}

    for metric in metric_columns:
        if metric not in weekly_df.columns:
            logger.warning(f"Metric column '{metric}' not found in DataFrame")
            continue

        metric_results = {
            'periods': [],
            'comparisons': []
        }

        # Extract last N periods
        for i in range(num_periods):
            if i < len(weekly_sorted):
                period_data = weekly_sorted.iloc[i]
                metric_results['periods'].append({
                    'period_index': i,
                    'date': period_data[date_column],
                    'value': period_data[metric]
                })

        # Calculate period-to-period comparisons
        for i in range(len(metric_results['periods']) - 1):
            current = metric_results['periods'][i]
            previous = metric_results['periods'][i + 1]

            current_val = current['value']
            previous_val = previous['value']

            if pd.isna(current_val) or pd.isna(previous_val):
                comparison = {
                    'from_period': i + 1,
                    'to_period': i,
                    'absolute_change': None,
                    'percent_change': None
                }
            else:
                absolute_change = current_val - previous_val
                percent_change = None
                if previous_val != 0:
                    percent_change = (absolute_change / previous_val) * 100

                comparison = {
                    'from_period': i + 1,
                    'to_period': i,
                    'absolute_change': absolute_change,
                    'percent_change': percent_change
                }

            metric_results['comparisons'].append(comparison)

        results[metric] = metric_results

    return results


def calculate_trailing_aggregates(
    weekly_df: pd.DataFrame,
    metric_columns: Union[str, List[str]],
    aggregate_func: str = 'sum',
    periods: Optional[List[int]] = None
) -> Dict[str, Dict[int, Any]]:
    """
    Calculate trailing aggregates (e.g., last 2 weeks, last 3 weeks, etc.)

    Args:
        weekly_df: DataFrame with weekly data (sorted by date)
        metric_columns: Columns to aggregate
        aggregate_func: Aggregation function ('sum', 'mean', 'median', etc.)
        periods: List of trailing periods to calculate (default: [2, 3, 4, 6])

    Returns:
        Dictionary with trailing aggregates for each metric and period
    """
    if isinstance(metric_columns, str):
        metric_columns = [metric_columns]

    if periods is None:
        periods = [2, 3, 4, 6]

    # Sort by date ascending for trailing calculations
    weekly_sorted = weekly_df.sort_values('week_ending', ascending=True)

    results = {}

    for metric in metric_columns:
        if metric not in weekly_df.columns:
            continue

        metric_results = {}

        for period in periods:
            if len(weekly_sorted) >= period:
                # Get last N periods
                last_n_periods = weekly_sorted.tail(period)

                try:
                    if aggregate_func == 'sum':
                        aggregate_value = last_n_periods[metric].sum()
                    elif aggregate_func == 'mean':
                        aggregate_value = last_n_periods[metric].mean()
                    elif aggregate_func == 'median':
                        aggregate_value = last_n_periods[metric].median()
                    elif aggregate_func == 'min':
                        aggregate_value = last_n_periods[metric].min()
                    elif aggregate_func == 'max':
                        aggregate_value = last_n_periods[metric].max()
                    else:
                        aggregate_value = last_n_periods[metric].agg(aggregate_func)

                    metric_results[period] = {
                        'value': aggregate_value,
                        'periods_included': len(last_n_periods),
                        'date_range': {
                            'start': last_n_periods.iloc[0]['week_ending'],
                            'end': last_n_periods.iloc[-1]['week_ending']
                        }
                    }
                except Exception as e:
                    logger.error(f"Aggregation failed for {metric} over {period} periods: {e}")
                    metric_results[period] = {
                        'value': None,
                        'periods_included': 0,
                        'error': str(e)
                    }
            else:
                metric_results[period] = {
                    'value': None,
                    'periods_included': len(weekly_sorted),
                    'note': f'Insufficient data: need {period} periods, have {len(weekly_sorted)}'
                }

        results[metric] = metric_results

    return results


def detect_trend_direction(
    weekly_df: pd.DataFrame,
    metric_column: str,
    min_periods: int = 3,
    date_column: str = 'week_ending'
) -> Dict[str, Any]:
    """
    Detect trend direction for a metric over time.

    Args:
        weekly_df: DataFrame with weekly data
        metric_column: Column to analyze for trends
        min_periods: Minimum periods needed for trend detection
        date_column: Name of the date column

    Returns:
        Dictionary with trend analysis results
    """
    if len(weekly_df) < min_periods:
        return {
            'trend': 'insufficient_data',
            'periods_analyzed': len(weekly_df),
            'min_periods_required': min_periods
        }

    # Sort by date
    weekly_sorted = weekly_df.sort_values(date_column)

    # Remove NaN values
    clean_data = weekly_sorted.dropna(subset=[metric_column])

    if len(clean_data) < min_periods:
        return {
            'trend': 'insufficient_clean_data',
            'periods_analyzed': len(clean_data),
            'periods_total': len(weekly_df)
        }

    values = clean_data[metric_column].values

    # Simple trend detection using differences
    differences = np.diff(values)

    positive_changes = np.sum(differences > 0)
    negative_changes = np.sum(differences < 0)
    no_changes = np.sum(differences == 0)

    total_changes = len(differences)

    # Determine trend
    if positive_changes > negative_changes * 1.5:  # Strong upward trend
        trend = 'upward'
    elif negative_changes > positive_changes * 1.5:  # Strong downward trend
        trend = 'downward'
    elif abs(positive_changes - negative_changes) <= 1:  # Roughly equal
        trend = 'stable'
    else:
        trend = 'mixed'

    return {
        'trend': trend,
        'periods_analyzed': len(clean_data),
        'positive_changes': positive_changes,
        'negative_changes': negative_changes,
        'no_changes': no_changes,
        'total_changes': total_changes,
        'latest_value': values[-1],
        'first_value': values[0],
        'overall_change': values[-1] - values[0],
        'overall_change_percent': ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else None
    }


# ============================================
# SPECIFICATION-REQUIRED METRICS FUNCTIONS
# ============================================

def compute_last_prev(df_sem: pd.DataFrame) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """
    Compute last and previous week values for each metric.

    Args:
        df_sem: Weekly DataFrame (sorted by date)

    Returns:
        Dictionary mapping metric names to (prev, last) tuples
    """
    if len(df_sem) < 2:
        # Not enough data for comparison
        return {}

    # Identify metric columns (exclude metadata columns)
    metadata_cols = ['WeekIndex', 'StartDate', 'EndDate', 'Date', 'Intervalo',
                     'WeekEndingWeekday', 'WkLabel', 'WkLabelFull', 'week_ending',
                     'week_start', 'days_in_week', 'week_number', 'year', 'relative_week']

    metric_cols = [col for col in df_sem.columns if col not in metadata_cols]

    # Get last two rows (assuming sorted chronologically)
    last_row = df_sem.iloc[-1]
    prev_row = df_sem.iloc[-2]

    results = {}
    for metric in metric_cols:
        if metric in last_row.index and metric in prev_row.index:
            last_val = last_row[metric]
            prev_val = prev_row[metric]

            # Convert to None if NaN
            last_val = None if pd.isna(last_val) else float(last_val)
            prev_val = None if pd.isna(prev_val) else float(prev_val)

            results[metric] = (prev_val, last_val)

    return results


def compute_wow(df_sem: pd.DataFrame, decimals: int = 2) -> Dict[str, Optional[float]]:
    """
    Compute Week-over-Week percentage change for each metric.

    Args:
        df_sem: Weekly DataFrame
        decimals: Number of decimal places to round to

    Returns:
        Dictionary mapping metric names to WOW percentage change
        Returns NaN if prev==0 or if fewer than 2 non-NaN values exist
    """
    last_prev_values = compute_last_prev(df_sem)

    results = {}
    for metric, (prev_val, last_val) in last_prev_values.items():
        if prev_val is None or last_val is None:
            results[metric] = None
        elif prev_val == 0:
            results[metric] = None  # Can't calculate percentage from zero base
        else:
            wow_pct = ((last_val - prev_val) / prev_val) * 100
            results[metric] = round(wow_pct, decimals)

    return results


def attach_wow(df_sem: pd.DataFrame, apply_to: str = 'last', decimals: int = 2) -> pd.DataFrame:
    """
    Attach WOW percentage columns to the DataFrame.

    Args:
        df_sem: Weekly DataFrame
        apply_to: 'last' to add WOW only to last row, 'all' for all rows
        decimals: Number of decimal places

    Returns:
        DataFrame with added <metric>_WOW_PCT columns
    """
    df_result = df_sem.copy()

    # Identify metric columns
    metadata_cols = ['WeekIndex', 'StartDate', 'EndDate', 'Date', 'Intervalo',
                     'WeekEndingWeekday', 'WkLabel', 'WkLabelFull', 'week_ending',
                     'week_start', 'days_in_week', 'week_number', 'year', 'relative_week']

    metric_cols = [col for col in df_sem.columns if col not in metadata_cols]

    if apply_to == 'last':
        # Calculate WOW for last week only
        if len(df_result) >= 2:
            wow_values = compute_wow(df_result, decimals)

            # Add WOW columns, set value only for last row
            for metric in metric_cols:
                wow_col = f"{metric}_WOW_PCT"
                df_result[wow_col] = np.nan
                if metric in wow_values:
                    df_result.loc[len(df_result) - 1, wow_col] = wow_values[metric]

    elif apply_to == 'all':
        # Calculate WOW for all weeks (each compared to previous)
        for metric in metric_cols:
            wow_col = f"{metric}_WOW_PCT"
            df_result[wow_col] = np.nan

            for i in range(1, len(df_result)):
                prev_val = df_result.iloc[i - 1][metric]
                curr_val = df_result.iloc[i][metric]

                if pd.notna(prev_val) and pd.notna(curr_val) and prev_val != 0:
                    wow_pct = ((curr_val - prev_val) / prev_val) * 100
                    df_result.loc[i, wow_col] = round(wow_pct, decimals)

    return df_result


def get_last_week_row(df_sem: pd.DataFrame) -> pd.Series:
    """
    Get the last week's data row.

    Args:
        df_sem: Weekly DataFrame

    Returns:
        Series with last week's data
    """
    if df_sem.empty:
        return pd.Series()

    return df_sem.iloc[-1]


def get_prev_week_row(df_sem: pd.DataFrame) -> pd.Series:
    """
    Get the previous week's data row.

    Args:
        df_sem: Weekly DataFrame

    Returns:
        Series with previous week's data
    """
    if len(df_sem) < 2:
        return pd.Series()

    return df_sem.iloc[-2]


# Backward compatibility functions
def create_trailing_window(
    df: pd.DataFrame,
    end_date: datetime.date,
    weeks: int = 6,
    aggregation: str = 'sum'
) -> pd.DataFrame:
    """
    Legacy function for backward compatibility.
    Creates a trailing window with simple aggregation.
    """
    # Build aggregation map from all numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    agg_map = {col: aggregation for col in numeric_cols}

    return create_trailing_six_weeks(
        df,
        end_date,
        agg_map,
        num_weeks=weeks,
        validate_input=False
    )