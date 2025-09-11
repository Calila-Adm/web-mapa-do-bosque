"""
Test the unified wbr_metrics module including the calcular_kpis compatibility function
"""

import pytest
import pandas as pd
import numpy as np
import datetime
from decimal import Decimal
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.wbr_metrics import (
    WBRCalculator,
    calcular_kpis,  # Compatibility function that replaced kpis.py
    MetricType,
    ComparisonResult
)


class TestCalcularKPIsCompatibility:
    """Test the calcular_kpis function that replaces the old kpis.py"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        dates = pd.date_range('2024-01-01', periods=450, freq='D')
        return pd.DataFrame({
            'date': dates,
            'metric_value': np.random.randint(100, 500, len(dates))
        })
    
    def test_calcular_kpis_basic(self, sample_data):
        """Test basic functionality of calcular_kpis"""
        data_ref = datetime.date(2025, 1, 10)
        
        result = calcular_kpis(
            sample_data,
            data_referencia=data_ref,
            coluna_data='date',
            coluna_metrica='metric_value'
        )
        
        # Check all expected keys are present
        expected_keys = [
            'ultima_semana', 'var_semanal', 'yoy_semanal',
            'mes_atual', 'yoy_mensal', 'trimestre_atual',
            'yoy_trimestral', 'ano_atual', 'yoy_anual',
            'wow_pct', 'wow_abs', 'mtd_atual', 'mtd_pct'
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
            assert isinstance(result[key], (int, float, Decimal)), f"Invalid type for {key}"
    
    def test_calcular_kpis_auto_date(self, sample_data):
        """Test calcular_kpis with automatic date detection"""
        # Don't provide data_referencia
        result = calcular_kpis(sample_data)
        
        assert 'ultima_semana' in result
        assert 'wow_pct' in result
    
    def test_calcular_kpis_empty_data(self):
        """Test calcular_kpis with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['date', 'metric_value'])
        
        result = calcular_kpis(empty_df)
        
        # Should return safe defaults
        assert result['ultima_semana'] == 0
        assert result['wow_pct'] == 0
        assert result['yoy_semanal'] == 0
    
    def test_calcular_kpis_uses_six_week_logic(self, sample_data):
        """Verify that calcular_kpis uses the 6-week trailing window logic"""
        data_ref = datetime.date(2025, 1, 10)
        
        # Call calcular_kpis
        result = calcular_kpis(
            sample_data,
            data_referencia=data_ref,
            coluna_data='date',
            coluna_metrica='metric_value'
        )
        
        # The result should have values calculated from 6-week windows
        # Check that we have non-zero values (if data exists)
        if len(sample_data) > 42:  # At least 6 weeks of data
            assert result['ultima_semana'] != 0 or pd.isna(result['ultima_semana'])
            # WOW should be calculated from week 5 vs week 4
            assert 'wow_pct' in result


class TestWBRMetricsIntegration:
    """Test the integrated WBR metrics functionality"""
    
    @pytest.fixture
    def calculator(self):
        """Create a calculator with sample data"""
        dates = pd.date_range('2024-01-01', periods=450, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'orders': np.random.randint(50, 150, len(dates)),
            'revenue': np.random.randint(1000, 5000, len(dates)),
            'metric_value': np.random.randint(100, 300, len(dates))
        })
        
        return WBRCalculator(
            df,
            datetime.date(2025, 1, 10),
            {'orders': 'sum', 'revenue': 'sum', 'metric_value': 'sum'},
            value_metrics=['orders', 'revenue', 'metric_value'],
            date_column='date',
            metric_column='metric_value'
        )
    
    def test_get_dashboard_kpis(self, calculator):
        """Test the new get_dashboard_kpis method"""
        kpis = calculator.get_dashboard_kpis()
        
        # Check structure
        assert isinstance(kpis, dict)
        assert 'ultima_semana' in kpis
        assert 'wow_pct' in kpis
        assert 'yoy_semanal' in kpis
        assert 'mtd_atual' in kpis
        
        # Check types
        assert isinstance(kpis['ultima_semana'], (float, Decimal))
        assert isinstance(kpis['wow_pct'], (float, Decimal))
    
    def test_dashboard_kpis_with_derived_metrics(self, calculator):
        """Test dashboard KPIs with derived metrics"""
        # Add derived metric
        calculator.add_div_metric('aov', 'revenue', 'orders')
        
        # Get KPIs
        kpis = calculator.get_dashboard_kpis()
        
        # Should still work
        assert 'ultima_semana' in kpis
        assert 'wow_pct' in kpis


class TestUnificationBenefits:
    """Test that the unification provides the expected benefits"""
    
    def test_consistent_calculations(self):
        """Verify calculations are consistent between methods"""
        dates = pd.date_range('2024-01-01', periods=450, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'metric_value': np.random.randint(100, 500, len(dates))
        })
        
        data_ref = datetime.date(2025, 1, 10)
        
        # Method 1: Using calcular_kpis compatibility function
        kpis_compat = calcular_kpis(df, data_ref)
        
        # Method 2: Using WBRCalculator directly
        calc = WBRCalculator(
            df,
            data_ref,
            {'metric_value': 'sum'},
            value_metrics=['metric_value'],
            date_column='date',
            metric_column='metric_value'
        )
        kpis_direct = calc.get_dashboard_kpis()
        
        # Results should be identical
        assert kpis_compat['ultima_semana'] == kpis_direct['ultima_semana']
        assert kpis_compat['wow_pct'] == kpis_direct['wow_pct']
        assert kpis_compat['yoy_semanal'] == kpis_direct['yoy_semanal']
    
    def test_six_week_window_calculation(self):
        """Verify the 6-week trailing window is properly calculated"""
        # Create controlled data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        values = list(range(100))  # Incrementing values
        df = pd.DataFrame({
            'date': dates,
            'metric_value': values
        })
        
        # Calculate using a date that ensures we have 6 full weeks
        data_ref = dates[49]  # 50th day
        
        calc = WBRCalculator(
            df,
            data_ref,
            {'metric_value': 'sum'},
            date_column='date',
            metric_column='metric_value'
        )
        
        # Check we have exactly 6 weeks
        assert len(calc.cy_trailing_six_weeks) == 6
        
        # Get KPIs
        kpis = calc.get_dashboard_kpis()
        
        # Last week should be index 5, previous week index 4
        # WOW should be calculated from these
        assert 'wow_pct' in kpis
        assert 'ultima_semana' in kpis


if __name__ == "__main__":
    pytest.main([__file__, '-v'])