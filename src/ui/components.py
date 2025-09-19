"""
Componentes reutilizáveis de UI.
"""

import streamlit as st
from typing import Optional

def info_card(title: str, value: Any, icon: str = "📊", color: Optional[str] = None):
    """Cria um card de informação estilizado."""
    container = st.container()
    with container:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write(icon)
        with col2:
            st.subheader(title)
            if color:
                st.markdown(f'<p style="color:{color};font-size:24px;font-weight:bold">{value}</p>', 
                           unsafe_allow_html=True)
            else:
                st.write(value)
    return container

def loading_spinner(message: str = "Carregando..."):
    """Wrapper para spinner de carregamento."""
    return st.spinner(message)
