#!/usr/bin/env python3
"""
Test script to verify date comparison logic for WoW calculations.
Ensures that the same calendar dates are compared between years.
"""

import pandas as pd
from datetime import datetime, timedelta
from src.core.processing import processar_dados_wbr

# Create test data for 2024 and 2025
print("Testing Date Comparison Logic")
print("=" * 60)

# Test case: 2025-08-31 (Sunday)
test_date = pd.Timestamp('2025-08-31')
print(f"\nTest Date: {test_date.strftime('%Y-%m-%d (%A)')}")

# Create sample data spanning 2024 and 2025
date_range = pd.date_range(start='2024-01-01', end='2025-12-31', freq='D')
df = pd.DataFrame({
    'date': date_range,
    'metric_value': range(len(date_range))  # Simple incrementing values
})

# Process data
result = processar_dados_wbr(df, test_date, 'date', 'metric_value')

# Extract week information
print("\nCurrent Year (2025) - Last Week:")
if not result['semanas_cy'].empty:
    last_week_cy = result['semanas_cy'].index[-1]
    # Get the start of the week
    week_start_cy = last_week_cy - timedelta(days=6)
    print(f"  Period: {week_start_cy.strftime('%Y-%m-%d')} to {last_week_cy.strftime('%Y-%m-%d')}")
    print(f"  Days: {(last_week_cy - week_start_cy).days + 1}")

print("\nPrevious Year (2024) - Comparison Week:")
if not result['semanas_py'].empty:
    last_week_py = result['semanas_py'].index[-1]
    # Calculate expected dates (same calendar dates, different year)
    expected_start = week_start_cy.replace(year=2024)
    expected_end = last_week_cy.replace(year=2024)
    
    # Get actual week start for PY
    week_start_py = last_week_py - timedelta(days=6)
    
    print(f"  Expected: {expected_start.strftime('%Y-%m-%d')} to {expected_end.strftime('%Y-%m-%d')}")
    print(f"  Actual:   {week_start_py.strftime('%Y-%m-%d')} to {last_week_py.strftime('%Y-%m-%d')}")
    print(f"  Days: {(last_week_py - week_start_py).days + 1}")
    
    # Check if dates match
    if week_start_py.day == week_start_cy.day and week_start_py.month == week_start_cy.month:
        print("\n✅ SUCCESS: Dates are correctly aligned (same calendar dates)")
    else:
        print("\n❌ ISSUE: Dates are not aligned properly")
        print(f"   CY uses days {week_start_cy.day}-{last_week_cy.day} of month {week_start_cy.month}")
        print(f"   PY uses days {week_start_py.day}-{last_week_py.day} of month {week_start_py.month}")

# Test another case: partial week
print("\n" + "=" * 60)
test_date2 = pd.Timestamp('2025-08-28')  # Thursday
print(f"\nTest Date 2 (Partial Week): {test_date2.strftime('%Y-%m-%d (%A)')}")

result2 = processar_dados_wbr(df, test_date2, 'date', 'metric_value')

print("\nPartial Week Analysis:")
print(f"  Partial week detected: {result2.get('semana_parcial', False)}")
if result2.get('semana_parcial'):
    print(f"  Days in partial week: {result2.get('dias_semana_parcial', 0)}")