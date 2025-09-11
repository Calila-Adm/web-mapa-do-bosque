#!/usr/bin/env python3
"""
Test script to verify KPI consistency between graph and KPI display
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

from src.core.processing import processar_dados_wbr, COLUNA_DATA, COLUNA_METRICA
from src.core.charts import criar_grafico_wbr

def create_test_data():
    """Create test data with known values for verification"""
    # Create 10 weeks of data to ensure we have enough for 6-week window
    dates = []
    values = []
    
    # Start from 10 weeks ago
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=10)
    
    current_date = start_date
    week_num = 1
    
    while current_date <= end_date:
        # Create 7 days per week with increasing values
        for day in range(7):
            dates.append(current_date + timedelta(days=day))
            # Use predictable values: week_num * 100 + day * 10
            values.append(week_num * 100 + day * 10)
        current_date += timedelta(weeks=1)
        week_num += 1
    
    df = pd.DataFrame({
        COLUNA_DATA: dates,
        COLUNA_METRICA: values
    })
    
    return df, end_date

def extract_kpi_values_from_graph(fig):
    """Extract KPI values from the graph annotations"""
    kpis = {}
    
    # Find the KPI annotations (they are at y=-0.44 in paper coordinates)
    for annotation in fig.layout.annotations:
        if hasattr(annotation, 'yref') and annotation.yref == 'paper':
            if annotation.y == -0.44:  # This is where KPI values are placed
                # Get the corresponding header
                for header_ann in fig.layout.annotations:
                    if header_ann.yref == 'paper' and header_ann.y == -0.38:
                        if header_ann.x == annotation.x:
                            header_text = header_ann.text.replace('<b>', '').replace('</b>', '')
                            kpis[header_text] = annotation.text
    
    return kpis

def main():
    print("=" * 60)
    print("Testing KPI Consistency between Graph and Display")
    print("=" * 60)
    
    # Create test data
    print("\n1. Creating test data...")
    df, data_ref = create_test_data()
    print(f"   Created {len(df)} rows of data")
    print(f"   Date range: {df[COLUNA_DATA].min()} to {df[COLUNA_DATA].max()}")
    print(f"   Reference date: {data_ref}")
    
    # Process data to get weekly aggregations
    print("\n2. Processing data for WBR...")
    dados = processar_dados_wbr(df, data_ref)
    
    # Extract weekly values
    semanas_cy = dados['semanas_cy'][COLUNA_METRICA].values
    semanas_py = dados['semanas_py'][COLUNA_METRICA].values
    
    print(f"\n3. Weekly data (Current Year - last 6 weeks):")
    for i, val in enumerate(semanas_cy):
        print(f"   Week {i+1}: {val:.0f}")
    
    print(f"\n   Last week value: {semanas_cy[-1]:.0f}")
    print(f"   Previous week value: {semanas_cy[-2]:.0f}" if len(semanas_cy) > 1 else "   Previous week: N/A")
    
    # Calculate expected KPIs
    ultima_semana = semanas_cy[-1] if len(semanas_cy) > 0 else 0
    semana_anterior = semanas_cy[-2] if len(semanas_cy) > 1 else 0
    ultima_semana_py = semanas_py[-1] if len(semanas_py) > 0 else 0
    
    wow_expected = 0
    if semana_anterior != 0:
        wow_expected = ((ultima_semana / semana_anterior - 1) * 100)
    
    yoy_expected = 0
    if ultima_semana_py != 0:
        yoy_expected = ((ultima_semana / ultima_semana_py - 1) * 100)
    
    print(f"\n4. Expected KPI values:")
    print(f"   LastWk: {ultima_semana:.0f}")
    print(f"   WOW: {wow_expected:+.1f}%")
    print(f"   YOY: {yoy_expected:+.1f}%")
    
    # Create graph and extract KPIs
    print("\n5. Creating graph and extracting KPIs...")
    fig = criar_grafico_wbr(
        dados, 
        df, 
        data_ref,
        titulo="Test Graph",
        unidade="Units"
    )
    
    kpis = extract_kpi_values_from_graph(fig)
    
    print(f"\n6. KPIs from graph:")
    for key, value in kpis.items():
        if key in ['LastWk', 'WOW', 'YOY(Semana)']:
            print(f"   {key}: {value}")
    
    # Verify consistency
    print("\n7. Verification Results:")
    
    # Check if LastWk matches
    lastwk_from_graph = kpis.get('LastWk', 'N/A')
    
    # Format expected value the same way as the graph
    if ultima_semana >= 1_000_000_000:
        expected_formatted = f"{ultima_semana/1_000_000_000:.1f}B"
    elif ultima_semana >= 1_000_000:
        expected_formatted = f"{ultima_semana/1_000_000:.1f}M"
    elif ultima_semana >= 1_000:
        expected_formatted = f"{ultima_semana/1_000:.1f}k"
    else:
        expected_formatted = f"{ultima_semana:.0f}"
    
    if lastwk_from_graph == expected_formatted:
        print(f"   ✅ LastWk is CONSISTENT: {lastwk_from_graph}")
    else:
        print(f"   ❌ LastWk MISMATCH!")
        print(f"      Graph shows: {lastwk_from_graph}")
        print(f"      Expected: {expected_formatted}")
    
    # Check graph data matches
    graph_traces = fig.data
    for trace in graph_traces:
        if 'Semanas' in trace.name and str(data_ref.year) in trace.name:
            graph_y_values = trace.y
            if len(graph_y_values) > 0:
                last_graph_value = graph_y_values[-1]
                print(f"\n   Graph trace last value: {last_graph_value:.0f}")
                print(f"   Processed data last value: {ultima_semana:.0f}")
                if abs(last_graph_value - ultima_semana) < 0.01:
                    print(f"   ✅ Graph data matches processed data")
                else:
                    print(f"   ❌ Graph data does not match!")

if __name__ == "__main__":
    main()