#!/usr/bin/env python3
"""
WBR Dashboard - Aplicação Principal
====================================
Dashboard modular para análise de métricas WBR.
"""
import os
import sys

# Adiciona o diretório raiz ao path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from src.utils.env import load_environment_variables
from src.config.database import validate_database_config
from src.ui.login import show_login_page
from src.auth import load_auth_token
from src.ui.components.sidebar import SidebarComponent
from src.ui.pages import DashboardPage, InstagramPage

# Configuração inicial
load_environment_variables(base_dir=PROJECT_ROOT)
st.set_page_config(page_title="WBR Dashboard", layout="wide", page_icon="📊")

# Validação do banco de dados
valid, error = validate_database_config()
if not valid:
    st.error(f"❌ Configuração inválida: {error}")
    st.stop()

# Autenticação
if "authenticated" not in st.session_state:
    auth = load_auth_token()
    if auth:
        st.session_state.update({
            "authenticated": True,
            "username": auth["username"],
            "auth_token": auth["token"]
        })
    else:
        st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    show_login_page()
    st.stop()

# Inicializa componentes e páginas
sidebar = SidebarComponent()
pages = {
    'dashboard': DashboardPage(),
    'instagram': InstagramPage()
}

# Renderiza sidebar e obtém filtros
filters = sidebar.render()

# Menu de navegação
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

cols = st.columns(2)
buttons = [
    ("📊 Dashboard", "dashboard"),
    ("📱 Instagram", "instagram")
]

for col, (label, key) in zip(cols, buttons):
    with col:
        if st.button(label, width="stretch", type="primary" if st.session_state.page == key else "secondary"):
            st.session_state.page = key
            st.rerun()

st.markdown("---")

# Renderiza página selecionada
pages[st.session_state.page].render(filters)