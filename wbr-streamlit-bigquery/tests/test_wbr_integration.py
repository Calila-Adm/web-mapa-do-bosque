"""
Integration tests for enhanced WBR system
Tests the integration of wbr_utility, wbr_metrics, and wbr modules
"""

import pytest
import pandas as pd
import numpy as np
import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.wbr_utility import (
    create_trailing_six_weeks,
    DataValidator,
    WBRValidationError,
    prepare_data_for_wbr
)

from src.core.wbr_metrics import (
    WBRCalculator,
    MetricType,
    ComparisonResult
)

from src.core.wbr import (
    calcular_metricas_wbr,
    gerar_grafico_wbr
)


class TestWBRUtilityIntegration:
    """Test WBR utility functions with project structure."""
    
    @pytest.fixture
    def sample_bigquery_data(self):
        """Create sample data matching BigQuery structure."""
        dates = pd.date_range('2024-01-01', periods=450, freq='D')
        return pd.DataFrame({
            'date': dates,  # Using 'date' to match project standard
            'metric_value': np.random.randint(100, 500, len(dates)),
            'shopping': ['Shopping A'] * len(dates),
            'year': [d.year for d in dates]
        })
    
    def test_create_trailing_weeks_with_date_column(self, sample_bigquery_data):
        """Test trailing weeks creation with 'date' column."""
        week_ending = datetime.date(2025, 1, 10)
        agg_map = {'metric_value': 'sum'}
        
        result = create_trailing_six_weeks(
            sample_bigquery_data,
            week_ending,
            agg_map,
            date_column='date'  # Specify project standard column
        )
        
        assert len(result) == 6
        assert 'Date' in result.columns  # Output standardized to 'Date'
        assert 'metric_value' in result.columns
    
    def test_data_validator_with_project_columns(self, sample_bigquery_data):
        """Test data validation with project-specific columns."""
        validator = DataValidator()
        result = validator.validate_dataframe(
            sample_bigquery_data,
            required_columns=['metric_value', 'shopping'],
            date_column='date'
        )
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_prepare_data_for_wbr(self, sample_bigquery_data):
        """Test data preparation function."""
        prepared = prepare_data_for_wbr(
            sample_bigquery_data,
            date_column='date',
            metric_column='metric_value'
        )
        
        assert 'date' in prepared.columns
        assert pd.api.types.is_datetime64_any_dtype(prepared['date'])
        assert prepared['date'].is_monotonic_increasing  # Should be sorted


class TestWBRMetricsIntegration:
    """Test WBR metrics calculator with project structure."""
    
    @pytest.fixture
    def calculator_with_data(self):
        """Create calculator with sample data."""
        dates = pd.date_range('2024-01-01', periods=450, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'orders': np.random.randint(50, 150, len(dates)),
            'revenue': np.random.randint(1000, 5000, len(dates)),
            'sessions': np.random.randint(200, 600, len(dates)),
            'metric_value': np.random.randint(100, 300, len(dates))
        })
        
        calc = WBRCalculator(
            df,
            datetime.date(2025, 1, 10),
            {'orders': 'sum', 'revenue': 'sum', 'sessions': 'sum', 'metric_value': 'sum'},
            value_metrics=['orders', 'revenue'],
            ratio_metrics=[],
            date_column='date',
            metric_column='metric_value'
        )
        
        return calc
    
    def test_calculator_initialization(self, calculator_with_data):
        """Test calculator initializes correctly."""
        calc = calculator_with_data
        
        assert calc.date_column == 'date'
        assert calc.metric_column == 'metric_value'
        assert len(calc.cy_trailing_six_weeks) == 6
        assert len(calc.py_trailing_six_weeks) == 6
    
    def test_add_metrics_chain(self, calculator_with_data):
        """Test method chaining for adding metrics."""
        calc = calculator_with_data
        
        result = (calc
                 .add_div_metric('aov', 'revenue', 'orders')
                 .add_div_metric('conversion_rate', 'orders', 'sessions'))
        
        assert 'aov' in calc.derived_cy.columns
        assert 'conversion_rate' in calc.derived_cy.columns
        assert result is calc  # Check chaining returns self
    
    def test_streamlit_export(self, calculator_with_data):
        """Test export format for Streamlit."""
        calc = calculator_with_data
        calc.add_div_metric('aov', 'revenue', 'orders')
        
        streamlit_data = calc.get_metrics_for_streamlit()
        
        assert 'current_year' in streamlit_data
        assert 'previous_year' in streamlit_data
        assert 'summary' in streamlit_data
        assert 'metrics' in streamlit_data
        assert isinstance(streamlit_data['current_year'], list)


class TestWBRMainIntegration:
    """Test main WBR functions integration."""
    
    @pytest.fixture
    def sample_streamlit_data(self):
        """Create sample data for Streamlit dashboard."""
        dates = pd.date_range('2024-01-01', periods=450, freq='D')
        return pd.DataFrame({
            'date': dates,
            'metric_value': np.random.randint(100, 500, len(dates)),
            'orders': np.random.randint(50, 150, len(dates)),
            'revenue': np.random.randint(1000, 5000, len(dates))
        })
    
    def test_calcular_metricas_wbr_success(self, sample_streamlit_data):
        """Test successful metrics calculation."""
        result = calcular_metricas_wbr(
            sample_streamlit_data,
            data_referencia=datetime.date(2025, 1, 10),
            coluna_data='date',
            coluna_metrica='metric_value'
        )
        
        assert result['success'] is True
        assert 'comparisons' in result
        assert 'trailing_weeks' in result
        assert 'summary' in result
        assert 'streamlit_data' in result
        assert result['metrics_analyzed'] > 0
    
    def test_calcular_metricas_wbr_with_derived(self, sample_streamlit_data):
        """Test metrics calculation with derived metrics."""
        metricas_derivadas = {
            'aov': {
                'type': 'division',
                'numerator': 'revenue',
                'denominator': 'orders',
                'description': 'Average Order Value'
            }
        }
        
        result = calcular_metricas_wbr(
            sample_streamlit_data,
            coluna_data='date',
            metricas_derivadas=metricas_derivadas
        )
        
        assert result['success'] is True
        assert 'aov' in result['metadata']['derived_metrics']
    
    def test_calcular_metricas_wbr_error_handling(self):
        """Test error handling in metrics calculation."""
        # Invalid data
        invalid_df = pd.DataFrame({'invalid': [1, 2, 3]})
        
        result = calcular_metricas_wbr(
            invalid_df,
            coluna_data='date',  # Column doesn't exist
            coluna_metrica='metric_value'
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert 'fallback_data' in result
    
    def test_auto_detection_of_metrics(self, sample_streamlit_data):
        """Test automatic detection of numeric columns."""
        result = calcular_metricas_wbr(sample_streamlit_data)
        
        assert result['success'] is True
        # Should detect metric_value, orders, revenue
        assert result['metrics_analyzed'] == 3
        
        # Check classifications
        assert 'orders' in result['metadata']['value_metrics']
        assert 'revenue' in result['metadata']['value_metrics']


class TestBackwardCompatibility:
    """Test backward compatibility with existing codebase."""
    
    def test_gerar_grafico_wbr_compatibility(self):
        """Test that gerar_grafico_wbr still works."""
        # Create minimal test data
        df = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=30),
            'metric_value': np.random.randint(100, 200, 30)
        })
        
        # This should not raise an error
        try:
            # We can't actually render the chart in tests, but we can check it doesn't crash
            fig = gerar_grafico_wbr(
                df,
                coluna_data='date',
                coluna_pessoas='metric_value',
                titulo='Test',
                unidade='units'
            )
            # If we get here without error, compatibility is maintained
            assert True
        except ImportError:
            # Charts module might not be available in test environment
            pytest.skip("Charts module not available in test environment")
        except Exception as e:
            # Check if it's an expected error (like missing plotly)
            if "plotly" in str(e).lower() or "chart" in str(e).lower():
                pytest.skip(f"Charting dependency not available: {e}")
            else:
                raise


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame(columns=['date', 'metric_value'])
        
        result = calcular_metricas_wbr(empty_df)
        
        assert result['success'] is False
        assert 'fallback_data' in result
    
    def test_single_day_data(self):
        """Test with only one day of data."""
        df = pd.DataFrame({
            'date': [datetime.date(2025, 1, 1)],
            'metric_value': [100]
        })
        
        result = calcular_metricas_wbr(df)
        
        # Should handle gracefully even with insufficient data
        assert 'success' in result
        if result['success']:
            # WOW/YOY might be None/NaN but shouldn't crash
            assert 'comparisons' in result
    
    def test_missing_previous_year_data(self):
        """Test when previous year data is missing."""
        # Only 30 days of data (no previous year)
        df = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=30),
            'metric_value': np.random.randint(100, 200, 30)
        })
        
        result = calcular_metricas_wbr(
            df,
            data_referencia=datetime.date(2025, 1, 30)
        )
        
        if result['success']:
            # YOY should be None or NaN
            for metric, comparison in result['comparisons'].items():
                yoy = comparison.get('yoy', {})
                assert yoy.get('percent_change') is None or pd.isna(yoy.get('percent_change'))
    
    def test_all_zero_values(self):
        """Test with all zero values (division by zero scenarios)."""
        df = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=60),
            'orders': [0] * 60,
            'revenue': np.random.randint(100, 200, 60)
        })
        
        metricas_derivadas = {
            'aov': {
                'type': 'division',
                'numerator': 'revenue',
                'denominator': 'orders',
                'handle_zero': 'nan'
            }
        }
        
        result = calcular_metricas_wbr(
            df,
            metricas_derivadas=metricas_derivadas
        )
        
        # Should handle division by zero gracefully
        assert 'error' not in result or result['success'] is True


class TestPerformance:
    """Test performance with larger datasets."""
    
    def test_large_dataset_performance(self):
        """Test with 2 years of data."""
        import time
        
        # Create 2 years of data
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=730),
            'metric_value': np.random.randint(100, 1000, 730),
            'orders': np.random.randint(50, 200, 730),
            'revenue': np.random.randint(1000, 10000, 730)
        })
        
        start_time = time.time()
        result = calcular_metricas_wbr(df)
        elapsed_time = time.time() - start_time
        
        assert result['success'] is True
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed_time < 5.0
        print(f"Performance test: {elapsed_time:.2f} seconds for 730 days")


if __name__ == "__main__":
    pytest.main([__file__, '-v'])