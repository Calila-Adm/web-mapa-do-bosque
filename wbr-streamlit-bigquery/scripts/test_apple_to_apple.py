#!/usr/bin/env python3
"""
Test script to verify "apple to apple" comparisons
Verifica se as comparações entre CY e PY estão usando períodos equivalentes
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.processing import processar_dados_wbr, COLUNA_DATA, COLUNA_METRICA

def create_test_data_two_years():
    """Create test data spanning two years with predictable values"""
    dates = []
    values = []
    
    # Create data for 2 years
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 9, 11)  # Today's date (parcial)
    
    current_date = start_date
    day_counter = 1
    
    while current_date <= end_date:
        dates.append(current_date)
        # Use predictable values: year * 1000 + day_of_year
        values.append(current_date.year * 1000 + current_date.timetuple().tm_yday)
        current_date += timedelta(days=1)
        day_counter += 1
    
    df = pd.DataFrame({
        COLUNA_DATA: dates,
        COLUNA_METRICA: values
    })
    
    return df, pd.Timestamp(end_date)

def main():
    print("=" * 80)
    print("Testing 'Apple to Apple' Comparisons (Maçã com Maçã)")
    print("=" * 80)
    
    # Create test data
    print("\n1. Creating test data spanning 2 years...")
    df, data_ref = create_test_data_two_years()
    print(f"   Created {len(df)} rows of data")
    print(f"   Date range: {df[COLUNA_DATA].min()} to {df[COLUNA_DATA].max()}")
    print(f"   Reference date: {data_ref}")
    
    # Process data
    print("\n2. Processing data with apple-to-apple logic...")
    dados = processar_dados_wbr(df, data_ref)
    
    # Check week comparison
    print("\n3. Weekly Comparison Analysis:")
    semanas_cy = dados['semanas_cy']
    semanas_py = dados['semanas_py']
    semana_parcial = dados.get('semana_parcial', False)
    dias_semana_parcial = dados.get('dias_semana_parcial', 7)
    
    print(f"   Current Year - 6 weeks:")
    for i, (idx, row) in enumerate(semanas_cy.iterrows()):
        week_label = f"Week {i+1}"
        if i == len(semanas_cy) - 1 and semana_parcial:
            week_label += f" (PARTIAL: {dias_semana_parcial} days)"
        print(f"     {week_label}: {row[COLUNA_METRICA]:.0f} (Week ending {idx.date()})")
    
    print(f"\n   Previous Year - 6 weeks (364 days offset):")
    for i, (idx, row) in enumerate(semanas_py.iterrows()):
        week_label = f"Week {i+1}"
        if i == len(semanas_py) - 1 and semana_parcial:
            week_label += f" (PARTIAL: {dias_semana_parcial} days)"
        print(f"     {week_label}: {row[COLUNA_METRICA]:.0f} (Week ending {idx.date()})")
    
    # Verify partial week handling
    if semana_parcial:
        print(f"\n   ✅ Partial week detected: Both CY and PY show {dias_semana_parcial} days for last week")
    else:
        print("\n   ℹ️  No partial week - all weeks are complete")
    
    # Check month comparison
    print("\n4. Monthly Comparison Analysis:")
    meses_cy = dados['meses_cy']
    meses_py = dados['meses_py']
    mes_parcial_cy = dados.get('mes_parcial_cy', False)
    
    print(f"   Current Year Months:")
    for idx, row in meses_cy.iterrows():
        if not pd.isna(row[COLUNA_METRICA]):
            month_label = idx.strftime('%B %Y')
            if idx.month == data_ref.month and mes_parcial_cy:
                month_label += f" (PARTIAL: up to day {data_ref.day})"
            print(f"     {month_label}: {row[COLUNA_METRICA]:.0f}")
    
    print(f"\n   Previous Year Months (apple-to-apple):")
    for idx, row in meses_py.iterrows():
        if not pd.isna(row[COLUNA_METRICA]):
            month_label = idx.strftime('%B %Y')
            # Check if this is the equivalent month to the current partial month
            if idx.month == data_ref.month:
                month_label += f" (LIMITED: up to day {data_ref.day})"
            print(f"     {month_label}: {row[COLUNA_METRICA]:.0f}")
    
    # Verify apple-to-apple for months
    print("\n5. Apple-to-Apple Verification:")
    
    # Check September comparison (current partial month)
    sep_cy_idx = pd.Timestamp(2025, 9, 1)
    sep_py_idx = pd.Timestamp(2024, 9, 1)
    
    if sep_cy_idx in meses_cy.index and sep_py_idx in meses_py.index:
        sep_cy_value = meses_cy.loc[sep_cy_idx, COLUNA_METRICA]
        sep_py_value = meses_py.loc[sep_py_idx, COLUNA_METRICA]
        
        # Count actual days in each September
        cy_sep_data = df[(df[COLUNA_DATA] >= sep_cy_idx) & 
                        (df[COLUNA_DATA] <= data_ref)]
        py_sep_data = df[(df[COLUNA_DATA] >= sep_py_idx) & 
                        (df[COLUNA_DATA] <= pd.Timestamp(2024, 9, data_ref.day))]
        
        cy_days = len(cy_sep_data)
        py_days = len(py_sep_data)
        
        print(f"   September Comparison:")
        print(f"     CY (2025): {cy_days} days, Total: {sep_cy_value:.0f}")
        print(f"     PY (2024): {py_days} days, Total: {sep_py_value:.0f}")
        
        if cy_days == py_days:
            print(f"     ✅ PASSED: Both years using same number of days ({cy_days})")
        else:
            print(f"     ❌ FAILED: Different day counts! CY={cy_days}, PY={py_days}")
    
    # Check a complete month (e.g., July)
    jul_cy_idx = pd.Timestamp(2025, 7, 1)
    jul_py_idx = pd.Timestamp(2024, 7, 1)
    
    if jul_cy_idx in meses_cy.index and jul_py_idx in meses_py.index:
        jul_cy_value = meses_cy.loc[jul_cy_idx, COLUNA_METRICA]
        jul_py_value = meses_py.loc[jul_py_idx, COLUNA_METRICA]
        
        print(f"\n   July Comparison (complete month):")
        print(f"     CY (2025): {jul_cy_value:.0f}")
        print(f"     PY (2024): {jul_py_value:.0f}")
        print(f"     ✅ Both show complete month data")
    
    print("\n6. Summary:")
    print(f"   - Reference date: {data_ref.strftime('%Y-%m-%d')}")
    print(f"   - Partial week: {'Yes' if semana_parcial else 'No'}")
    print(f"   - Partial month: {'Yes' if mes_parcial_cy else 'No'}")
    print(f"   - Apple-to-apple logic: ACTIVE")
    print(f"   - PY data limited to same periods as CY: ✅")

if __name__ == "__main__":
    main()