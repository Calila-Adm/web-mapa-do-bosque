#!/usr/bin/env python3
"""
Test script to verify visual fixes for partial weeks and months
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

from src.core.processing import processar_dados_wbr, COLUNA_DATA, COLUNA_METRICA
from src.core.charts import criar_grafico_wbr

def create_test_data():
    """Create test data with partial week and month"""
    dates = []
    values = []
    
    # Create data from Jan 2024 to Sep 11, 2025 (partial month and week)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 9, 11)  # Middle of the week and month
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        # Create realistic values
        base_value = 1000 + (current_date.month * 50) + (current_date.day * 10)
        values.append(base_value)
        current_date += timedelta(days=1)
    
    df = pd.DataFrame({
        COLUNA_DATA: dates,
        COLUNA_METRICA: values
    })
    
    return df, pd.Timestamp(end_date)

def verify_graph_traces(fig):
    """Verify that the graph has the correct traces for partial periods"""
    print("\n📊 Analyzing Graph Traces:")
    print("=" * 60)
    
    trace_info = []
    for i, trace in enumerate(fig.data):
        trace_dict = {
            'index': i,
            'name': trace.name,
            'mode': trace.mode,
            'line_dash': getattr(trace.line, 'dash', None),
            'marker_symbol': getattr(trace.marker, 'symbol', None),
            'showlegend': trace.showlegend,
            'yaxis': trace.yaxis
        }
        trace_info.append(trace_dict)
        
        # Check for partial indicators
        is_partial = False
        if trace.hovertemplate and '(parcial)' in trace.hovertemplate:
            is_partial = True
        
        print(f"\nTrace {i}: {trace.name}")
        print(f"  Mode: {trace.mode}")
        print(f"  Line: {getattr(trace.line, 'dash', 'solid')}")
        print(f"  Marker: {getattr(trace.marker, 'symbol', 'default')}")
        print(f"  Axis: {trace.yaxis}")
        print(f"  Legend: {'Shown' if trace.showlegend != False else 'Hidden'}")
        if is_partial:
            print(f"  ⚠️  Contains '(parcial)' in tooltip")
    
    # Verify specific requirements
    print("\n✅ Verification Results:")
    
    # Check for dashed lines for partial periods
    dashed_traces = [t for t in trace_info if t['line_dash'] == 'dash']
    print(f"  Dashed line traces: {len(dashed_traces)}")
    
    # Check for diamond-open markers
    open_markers = [t for t in trace_info if t['marker_symbol'] == 'diamond-open']
    print(f"  Open diamond markers: {len(open_markers)}")
    
    # Check that "(Parcial)" is not in legend names
    legend_with_partial = [t for t in trace_info if t['showlegend'] != False and 'Parcial' in (t['name'] or '')]
    if legend_with_partial:
        print(f"  ❌ Found '(Parcial)' in legend: {[t['name'] for t in legend_with_partial]}")
    else:
        print(f"  ✅ No '(Parcial)' in legend names")
    
    return trace_info

def main():
    print("Testing Visual Fixes for Partial Weeks and Months")
    print("=" * 60)
    
    # Create test data
    print("\n1. Creating test data...")
    df, data_ref = create_test_data()
    print(f"   Created {len(df)} rows of data")
    print(f"   Date range: {df[COLUNA_DATA].min()} to {df[COLUNA_DATA].max()}")
    print(f"   Reference date: {data_ref} (Sep 11, 2025 - Wednesday)")
    
    # Process data
    print("\n2. Processing data for WBR...")
    dados = processar_dados_wbr(df, data_ref)
    
    # Check partial flags
    print("\n3. Checking partial period flags:")
    print(f"   Semana parcial: {dados.get('semana_parcial', False)}")
    print(f"   Dias na semana parcial: {dados.get('dias_semana_parcial', 7)}")
    print(f"   Mês parcial CY: {dados.get('mes_parcial_cy', False)}")
    print(f"   Dias no mês parcial CY: {dados.get('dias_mes_parcial_cy', 0)}")
    
    # Create graph
    print("\n4. Creating graph...")
    fig = criar_grafico_wbr(
        dados,
        df,
        data_ref,
        titulo="Test Graph",
        unidade="Units"
    )
    
    # Verify traces
    traces = verify_graph_traces(fig)
    
    print("\n5. Summary:")
    print("=" * 60)
    print("Expected behavior:")
    print("  ✅ Partial week (Wk 37) should have:")
    print("     - Open diamond marker")
    print("     - Dashed line connecting to previous week")
    print("     - Tooltip with '(parcial)' only on the last point")
    print("     - NO '(Parcial)' in legend")
    print("\n  ✅ Partial month (September) should have:")
    print("     - Open diamond marker")
    print("     - Dashed line connecting to previous month")
    print("     - Tooltip with '(parcial)' only on September")
    print("     - NO '(Parcial)' in legend")

if __name__ == "__main__":
    main()