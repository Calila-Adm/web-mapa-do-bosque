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
from typing import Dict, Optional, Union, Any, Tuple
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
        
        return pd.concat([pd.DataFrame([row]), df], ignore_index=True)
        
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