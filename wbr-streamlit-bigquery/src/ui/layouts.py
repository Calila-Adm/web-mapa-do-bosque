"""
UI Layouts para o dashboard WBR.
"""

import streamlit as st
from typing import Dict, Any

def render_sidebar(config: Dict[str, Any]) -> Dict[str, Any]:
    """Renderiza a sidebar com filtros e configurações."""
    with st.sidebar:
        st.header("🎯 Filtros")
        
        filters = {}
        
        # Adicione aqui a lógica da sidebar
        # que estava no streamlit_app.py
        
        return filters

def render_metrics_row(metrics: Dict[str, Any]):
    """Renderiza uma linha de métricas KPI."""
    cols = st.columns(len(metrics))
    
    for col, (key, value) in zip(cols, metrics.items()):
        with col:
            st.metric(label=key, value=value.get('value'), delta=value.get('delta'))

def render_chart_container(chart_config: Dict[str, Any]):
    """Renderiza um container para gráficos."""
    with st.container():
        st.plotly_chart(chart_config['figure'], use_container_width=True)
