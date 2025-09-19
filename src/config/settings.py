"""
Configurações centralizadas do aplicativo.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Database Configuration
DB_CONFIG = {
    "type": os.getenv("DB_TYPE", "postgresql"),
    "postgres": {
        "schema": os.getenv("POSTGRES_SCHEMA", "mapa_do_bosque"),
        "tables": {
            "pessoas": os.getenv("POSTGRES_TABLE_PESSOAS", "fluxo_de_pessoas"),
            "veiculos": os.getenv("POSTGRES_TABLE_VEICULOS", "fluxo_de_veiculos"),
            "vendas": os.getenv("POSTGRES_TABLE_VENDAS", "vendas_gshop"),
        }
    },
    "bigquery": {
        "project": os.getenv("BIGQUERY_PROJECT_ID"),
        "dataset": os.getenv("BIGQUERY_DATASET"),
    }
}

# Application Settings
APP_CONFIG = {
    "title": "WBR Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Chart Settings
CHART_CONFIG = {
    "height": 400,
    "template": "plotly_white",
    "colors": {
        "pessoas": "#1E90FF",
        "veiculos": "#FF6B6B",
        "vendas": "#28A745",
    }
}

# WBR Configuration Classes
import datetime
from typing import Dict, Optional, Union

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class WBRConfig:
    """
    Configuration class for Weekly Business Review (WBR) aggregation.

    Attributes:
        week_ending: datetime - The anchor date for week ending (last day of the week)
        week_number: int | None - Optional external week label
        trailing_weeks: int - Number of trailing weeks to include (default: 6)
        aggf: dict - Aggregation functions for each column
    """

    def __init__(
        self,
        week_ending: Union[str, datetime.datetime, datetime.date],
        trailing_weeks: int = 6,
        aggf: Optional[Dict[str, str]] = None,
        week_number: Optional[int] = None
    ):
        """
        Initialize WBR configuration.

        Args:
            week_ending: Week ending date in format DD-MMM-YYYY or datetime object
            trailing_weeks: Number of trailing weeks (must be > 0)
            aggf: Aggregation functions dict (e.g., {'Orders': 'sum', 'Revenue': 'mean'})
            week_number: Optional external week number label
        """
        self.week_ending = self._parse_week_ending(week_ending)
        self.trailing_weeks = self._validate_trailing_weeks(trailing_weeks)
        self.aggf = aggf or {}
        self.week_number = week_number

    def _parse_week_ending(self, week_ending: Union[str, datetime.datetime, datetime.date]) -> datetime.datetime:
        """Parse and validate week_ending date."""
        if isinstance(week_ending, datetime.datetime):
            return week_ending
        elif isinstance(week_ending, datetime.date):
            return datetime.datetime.combine(week_ending, datetime.time())
        elif isinstance(week_ending, str):
            # Parse DD-MMM-YYYY format (case insensitive)
            try:
                return datetime.datetime.strptime(week_ending.upper(), "%d-%b-%Y")
            except ValueError:
                # Try other common formats
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        return datetime.datetime.strptime(week_ending, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Invalid week_ending format: {week_ending}. Expected DD-MMM-YYYY format.")
        else:
            raise ValueError(f"week_ending must be string or datetime, got {type(week_ending)}")

    def _validate_trailing_weeks(self, trailing_weeks: int) -> int:
        """Validate trailing_weeks parameter."""
        if not isinstance(trailing_weeks, int) or trailing_weeks <= 0:
            raise ValueError(f"trailing_weeks must be a positive integer, got {trailing_weeks}")
        return trailing_weeks

    def validate_aggf_columns(self, df_columns: list) -> None:
        """
        Validate that aggf keys exist in DataFrame columns.

        Args:
            df_columns: List of DataFrame column names

        Raises:
            ValueError: If aggf contains invalid column names
        """
        if not self.aggf:
            return

        missing_cols = set(self.aggf.keys()) - set(df_columns)
        if missing_cols:
            raise ValueError(f"Aggregation columns not found in DataFrame: {missing_cols}")

        # Check if numeric columns have valid aggregation functions
        valid_agg_funcs = {'sum', 'mean', 'median', 'min', 'max', 'count', 'std', 'var'}
        for col, func in self.aggf.items():
            if func not in valid_agg_funcs:
                raise ValueError(f"Invalid aggregation function '{func}' for column '{col}'. "
                               f"Valid functions: {valid_agg_funcs}")

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'WBRConfig':
        """
        Create WBRConfig from dictionary.

        Args:
            config_dict: Dictionary containing configuration parameters

        Returns:
            WBRConfig instance
        """
        required_keys = ['week_ending']
        missing_keys = set(required_keys) - set(config_dict.keys())
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")

        return cls(
            week_ending=config_dict['week_ending'],
            trailing_weeks=config_dict.get('trailing_weeks', 6),
            aggf=config_dict.get('aggf', {}),
            week_number=config_dict.get('week_number')
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'WBRConfig':
        """
        Create WBRConfig from YAML string.

        Args:
            yaml_str: YAML formatted configuration string

        Returns:
            WBRConfig instance
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for YAML configuration. Install with: pip install pyyaml")

        try:
            config_dict = yaml.safe_load(yaml_str)
            return cls.from_dict(config_dict)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse YAML configuration: {e}")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'week_ending': self.week_ending.strftime("%d-%b-%Y"),
            'trailing_weeks': self.trailing_weeks,
            'aggf': self.aggf,
            'week_number': self.week_number
        }

    def __repr__(self) -> str:
        return f"WBRConfig(week_ending={self.week_ending.date()}, trailing_weeks={self.trailing_weeks}, aggf={self.aggf})"
