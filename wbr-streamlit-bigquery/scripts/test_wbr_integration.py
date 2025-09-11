#!/usr/bin/env python3
"""
Script to test the integrated WBR system
Demonstrates the enhanced WBR functionality
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import datetime
from src.core.wbr import calcular_metricas_wbr
from src.core.wbr_metrics import WBRCalculator
from src.core.wbr_utility import create_trailing_six_weeks, DataValidator


def generate_sample_data(days=450):
    """Generate sample data for testing."""
    print("📊 Generating sample data...")
    
    np.random.seed(42)
    dates = pd.date_range(end=datetime.date.today(), periods=days, freq='D')
    
    # Create realistic patterns
    base_orders = 100
    weekly_pattern = np.sin(np.arange(days) * 2 * np.pi / 7) * 20
    trend = np.linspace(0, 50, days)
    noise = np.random.normal(0, 10, days)
    
    df = pd.DataFrame({
        'date': dates,
        'orders': np.maximum(1, base_orders + weekly_pattern + trend + noise).astype(int),
        'revenue': np.random.gamma(2, 500, days),
        'sessions': np.random.poisson(500, days),
        'conversions': np.random.poisson(20, days),
        'metric_value': np.random.randint(100, 300, days)
    })
    
    print(f"✅ Generated {len(df)} days of data")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Columns: {', '.join(df.columns)}")
    
    return df


def test_basic_functionality():
    """Test basic WBR functionality."""
    print("\n🔧 Testing Basic Functionality")
    print("-" * 50)
    
    # Generate data
    df = generate_sample_data(90)
    
    # Test data validation
    print("\n1️⃣ Testing Data Validation...")
    validator = DataValidator()
    validation = validator.validate_dataframe(df, date_column='date')
    
    if validation.is_valid:
        print("   ✅ Data validation passed")
    else:
        print(f"   ❌ Validation errors: {validation.errors}")
        return False
    
    if validation.warnings:
        print(f"   ⚠️ Warnings: {validation.warnings}")
    
    # Test trailing weeks creation
    print("\n2️⃣ Testing Trailing Weeks Creation...")
    week_ending = datetime.date.today()
    agg_map = {'orders': 'sum', 'revenue': 'sum', 'sessions': 'sum'}
    
    try:
        trailing = create_trailing_six_weeks(
            df, 
            week_ending, 
            agg_map,
            date_column='date'
        )
        print(f"   ✅ Created {len(trailing)} weeks of data")
        print(f"   Columns: {', '.join(trailing.columns)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True


def test_metrics_calculator():
    """Test WBR metrics calculator."""
    print("\n📈 Testing Metrics Calculator")
    print("-" * 50)
    
    # Generate data
    df = generate_sample_data(450)  # Need more data for YOY
    week_ending = datetime.date.today()
    
    print("\n1️⃣ Creating WBRCalculator...")
    try:
        calc = WBRCalculator(
            df,
            week_ending,
            {'orders': 'sum', 'revenue': 'sum', 'sessions': 'sum'},
            value_metrics=['orders', 'revenue'],
            date_column='date',
            metric_column='metric_value'
        )
        print("   ✅ Calculator created successfully")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n2️⃣ Adding Derived Metrics...")
    try:
        calc.add_div_metric('AOV', 'revenue', 'orders', description='Average Order Value')
        calc.add_div_metric('ConversionRate', 'conversions', 'sessions', description='Conversion Rate')
        print("   ✅ Added 2 derived metrics")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n3️⃣ Computing Comparisons...")
    try:
        wow = calc.compute_wow('orders')
        yoy = calc.compute_yoy_last_week('revenue')
        
        print(f"   📊 Orders WOW: {wow['CY'].percent_change:.1f}%" if wow['CY'].percent_change else "   📊 Orders WOW: N/A")
        print(f"   📊 Revenue YOY: {yoy.percent_change:.1f}%" if yoy.percent_change else "   📊 Revenue YOY: N/A")
        print("   ✅ Comparisons computed successfully")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True


def test_main_integration():
    """Test main integration function."""
    print("\n🎯 Testing Main Integration")
    print("-" * 50)
    
    # Generate data
    df = generate_sample_data(450)
    
    print("\n1️⃣ Testing calcular_metricas_wbr...")
    
    # Define derived metrics
    metricas_derivadas = {
        'AOV': {
            'type': 'division',
            'numerator': 'revenue',
            'denominator': 'orders',
            'description': 'Average Order Value'
        }
    }
    
    try:
        result = calcular_metricas_wbr(
            df,
            data_referencia=datetime.date.today(),
            coluna_data='date',
            coluna_metrica='metric_value',
            metricas_derivadas=metricas_derivadas
        )
        
        if result['success']:
            print("   ✅ Metrics calculated successfully")
            print(f"   📊 Metrics analyzed: {result['metrics_analyzed']}")
            print(f"   📅 Reference date: {result['reference_date']}")
            
            # Show some comparisons
            if 'comparisons' in result and result['comparisons']:
                print("\n   📈 Sample Comparisons:")
                for metric, comp in list(result['comparisons'].items())[:3]:
                    wow_pct = comp['wow'].get('percent_change')
                    yoy_pct = comp['yoy'].get('percent_change')
                    
                    wow_str = f"{wow_pct:.1f}%" if wow_pct is not None else "N/A"
                    yoy_str = f"{yoy_pct:.1f}%" if yoy_pct is not None else "N/A"
                    
                    print(f"      {metric}: WOW={wow_str}, YOY={yoy_str}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    
    print("\n2️⃣ Testing Streamlit Data Export...")
    try:
        if result['success'] and 'streamlit_data' in result:
            streamlit_data = result['streamlit_data']
            print(f"   ✅ Streamlit data exported")
            print(f"   📊 Current year records: {len(streamlit_data.get('current_year', []))}")
            print(f"   📊 Previous year records: {len(streamlit_data.get('previous_year', []))}")
            print(f"   📊 Summary records: {len(streamlit_data.get('summary', []))}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 WBR System Integration Test")
    print("=" * 60)
    
    # Track test results
    results = []
    
    # Run tests
    print("\n📋 Running Tests...")
    
    results.append(("Basic Functionality", test_basic_functionality()))
    results.append(("Metrics Calculator", test_metrics_calculator()))
    results.append(("Main Integration", test_main_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The WBR system is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)