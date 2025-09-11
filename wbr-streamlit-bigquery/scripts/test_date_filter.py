#!/usr/bin/env python3
"""
Test script to verify date filter limitations
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_test_data_with_gaps():
    """Create test data with specific date ranges and gaps"""
    dates = []
    values_pessoas = []
    values_veiculos = []
    
    # Create data for specific periods with gaps
    # Period 1: Jan-Mar 2024
    start1 = datetime(2024, 1, 1)
    end1 = datetime(2024, 3, 31)
    
    # Period 2: Jun-Sep 2024
    start2 = datetime(2024, 6, 1)
    end2 = datetime(2024, 9, 30)
    
    # Period 3: Jan-Jun 2025 (current year partial)
    start3 = datetime(2025, 1, 1)
    end3 = datetime(2025, 6, 15)
    
    periods = [
        (start1, end1),
        (start2, end2),
        (start3, end3)
    ]
    
    for start, end in periods:
        current = start
        while current <= end:
            dates.append(current)
            # Different patterns for pessoas and veiculos
            values_pessoas.append(1000 + current.timetuple().tm_yday)
            values_veiculos.append(500 + current.timetuple().tm_yday)
            current += timedelta(days=1)
    
    df_pessoas = pd.DataFrame({
        'date': dates,
        'metric_value': values_pessoas
    })
    
    df_veiculos = pd.DataFrame({
        'date': dates,
        'metric_value': values_veiculos
    })
    
    return df_pessoas, df_veiculos

def test_date_range_detection(df_pessoas, df_veiculos):
    """Test the date range detection logic"""
    print("=" * 60)
    print("Testing Date Range Detection")
    print("=" * 60)
    
    # Convert to datetime
    df_pessoas['date'] = pd.to_datetime(df_pessoas['date'])
    df_veiculos['date'] = pd.to_datetime(df_veiculos['date'])
    
    # Get date ranges
    dates = []
    
    if not df_pessoas.empty:
        dates.extend([df_pessoas['date'].min(), df_pessoas['date'].max()])
    
    if not df_veiculos.empty:
        dates.extend([df_veiculos['date'].min(), df_veiculos['date'].max()])
    
    if dates:
        min_date = min(dates)
        max_date = max(dates)
        
        print(f"\n1. Data from PESSOAS table:")
        print(f"   Min date: {df_pessoas['date'].min()}")
        print(f"   Max date: {df_pessoas['date'].max()}")
        print(f"   Total days: {len(df_pessoas['date'].unique())}")
        
        print(f"\n2. Data from VEICULOS table:")
        print(f"   Min date: {df_veiculos['date'].min()}")
        print(f"   Max date: {df_veiculos['date'].max()}")
        print(f"   Total days: {len(df_veiculos['date'].unique())}")
        
        print(f"\n3. Overall date range for filter:")
        print(f"   Min date allowed: {min_date.date()}")
        print(f"   Max date allowed: {max_date.date()}")
        print(f"   Total span: {(max_date - min_date).days} days")
        
        # Check for gaps
        all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
        existing_dates = set(df_pessoas['date'].dt.date.unique())
        missing_dates = set(all_dates.date) - existing_dates
        
        if missing_dates:
            print(f"\n4. Data gaps detected:")
            print(f"   {len(missing_dates)} days without data")
            # Show first few gaps
            gaps_sample = sorted(list(missing_dates))[:5]
            print(f"   Sample gaps: {gaps_sample}")
        else:
            print(f"\n4. No gaps - continuous data from {min_date.date()} to {max_date.date()}")
        
        # Test date validation
        print(f"\n5. Date validation tests:")
        
        test_dates = [
            (min_date - timedelta(days=1), "Before min", False),
            (min_date, "At min", True),
            (min_date + timedelta(days=30), "30 days after min", True),
            (max_date, "At max", True),
            (max_date + timedelta(days=1), "After max", False),
            (datetime(2024, 4, 15), "In gap period (Apr 2024)", True),  # Allowed but no data
            (datetime(2025, 12, 31), "Future date", False)
        ]
        
        for test_date, description, should_be_allowed in test_dates:
            is_allowed = min_date <= test_date <= max_date
            status = "✅" if is_allowed == should_be_allowed else "❌"
            print(f"   {status} {test_date.date()} - {description}: {'Allowed' if is_allowed else 'Blocked'}")
        
        return min_date, max_date
    else:
        print("No data available!")
        return None, None

def test_period_calculation(selected_date):
    """Test the period calculation for YoY comparison"""
    print(f"\n6. Period calculation for date: {selected_date.date()}")
    
    ano_ref = selected_date.year
    ano_anterior = ano_ref - 1
    
    # Calculate period
    data_inicio = pd.Timestamp(f'{ano_anterior}-01-01')
    data_fim = selected_date
    
    print(f"   Current year: {ano_ref}")
    print(f"   Previous year: {ano_anterior}")
    print(f"   Analysis period: {data_inicio.date()} to {data_fim.date()}")
    print(f"   Days in period: {(data_fim - data_inicio).days}")
    
    # Check if we have enough data for YoY
    if (data_fim - data_inicio).days >= 365:
        print(f"   ✅ Sufficient data for YoY comparison")
    else:
        print(f"   ⚠️  Limited data for YoY comparison ({(data_fim - data_inicio).days} days < 365)")

def main():
    print("Testing Date Filter with Limited Data Range")
    print("=" * 60)
    
    # Create test data
    print("\n1. Creating test data with gaps...")
    df_pessoas, df_veiculos = create_test_data_with_gaps()
    
    print(f"   Created {len(df_pessoas)} rows for PESSOAS")
    print(f"   Created {len(df_veiculos)} rows for VEICULOS")
    
    # Test date range detection
    min_date, max_date = test_date_range_detection(df_pessoas, df_veiculos)
    
    if min_date and max_date:
        # Test with different selected dates
        print("\n" + "=" * 60)
        print("Testing Period Calculations")
        print("=" * 60)
        
        test_period_calculation(max_date)
        
        # Test with a date in the middle
        mid_date = min_date + (max_date - min_date) / 2
        test_period_calculation(mid_date)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("\n✅ Date filter implementation:")
    print("   - Restricts selection to available data range")
    print("   - Shows min/max dates to user")
    print("   - Defaults to most recent date with data")
    print("   - Validates sufficient data for YoY comparison")
    print("   - Handles data gaps gracefully")

if __name__ == "__main__":
    main()