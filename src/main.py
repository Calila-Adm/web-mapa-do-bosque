#!/usr/bin/env python3
"""
WBR Dashboard - Aplicação Principal Otimizada
==============================================
Dashboard modular para análise de métricas WBR com otimizações de performance.
"""
import os
import sys
import streamlit as st

# Adiciona o diretório raiz ao path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ============================================================
# CONFIGURAÇÃO STREAMLIT - APENAS 1X
# ============================================================
if 'app_configured' not in st.session_state:
    st.set_page_config(
        page_title="WBR Dashboard",
        layout="wide",
        page_icon="📊"
    )
    st.session_state.app_configured = True

# ============================================================
# IMPORTS MÍNIMOS E LAZY
# ============================================================

@st.cache_data(ttl=3600)
def load_env():
    """Carrega ambiente apenas 1x"""
    from src.utils.env import load_environment_variables
    load_environment_variables(base_dir=PROJECT_ROOT)
    return True

@st.cache_data(ttl=3600)
def validate_db():
    """Valida DB apenas 1x por hora"""
    from src.config.database import validate_database_config
    return validate_database_config()

# Carrega ambiente
load_env()

# Valida banco
valid, error = validate_db()
if not valid:
    st.error(f"❌ Erro de configuração: {error}")
    st.stop()

# ============================================================
# AUTENTICAÇÃO CORRIGIDA
# ============================================================

# Inicializa estado de autenticação
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.auth_token = None

# Verifica token salvo APENAS se não autenticado
if not st.session_state.authenticated:
    try:
        from src.auth import load_auth_token
        saved_token = load_auth_token()

        # Valida se token existe E é válido
        if saved_token and saved_token.get("token") and saved_token.get("username"):
            # Aqui você deveria validar o token com o servidor
            # Por hora, aceita se existe
            st.session_state.authenticated = True
            st.session_state.username = saved_token["username"]
            st.session_state.auth_token = saved_token["token"]
    except:
        # Se falhar, continua não autenticado
        pass

# Se ainda não autenticado, mostra login
if not st.session_state.authenticated:
    from src.ui.login import show_login_page
    show_login_page()
    st.stop()

# ============================================================
# CACHE INTELIGENTE DE COMPONENTES - CRIAÇÃO LAZY REAL
# ============================================================

class ComponentCache:
    """Cache singleton para componentes"""
    _instance = None
    _sidebar = None
    _pages = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_sidebar(cls):
        """Obtém sidebar - cria apenas quando chamado"""
        if cls._sidebar is None:
            from src.ui.components.sidebar import SidebarComponent
            cls._sidebar = SidebarComponent()
        return cls._sidebar

    @classmethod
    def get_page(cls, page_name: str):
        """Obtém página - cria apenas quando necessário"""
        if page_name not in cls._pages:
            if page_name == 'dashboard':
                from src.ui.pages import DashboardPage
                cls._pages[page_name] = DashboardPage()
            elif page_name == 'instagram':
                from src.ui.pages import InstagramPage
                cls._pages[page_name] = InstagramPage()
        return cls._pages.get(page_name)

# Instância global do cache
component_cache = ComponentCache()

# ============================================================
# INTERFACE PRINCIPAL
# ============================================================

# Importa funções CSS apenas uma vez
from src.ui.styles.user_menu import get_user_button_css, get_logout_button_css

# CSS carregado apenas 1x
if 'css_loaded' not in st.session_state:
    st.markdown(get_user_button_css(), unsafe_allow_html=True)
    st.session_state.css_loaded = True

# Estado do popup do usuário
if 'show_user_popup' not in st.session_state:
    st.session_state.show_user_popup = False

# Botão do usuário
user_col1, user_col2, user_col3 = st.columns([1, 10, 1])
with user_col1:
    if st.button("👤", key="user_button", help="Menu do usuário"):
        st.session_state.show_user_popup = not st.session_state.show_user_popup

# Popup do usuário - com botão integrado
if st.session_state.show_user_popup:
    # Botão funcional de sair
    if st.button("🚪 Sair", key="logout_popup", help="Sair do sistema"):
        from src.auth import logout
        logout()

    # Aplicar CSS para posicionar o botão de logout
    if 'logout_css_loaded' not in st.session_state:
        st.markdown(get_logout_button_css(), unsafe_allow_html=True)
        st.session_state.logout_css_loaded = True

# ============================================================
# SIDEBAR - CARREGA APENAS QUANDO RENDERIZA
# ============================================================

sidebar = component_cache.get_sidebar()
filters = sidebar.render()

# ============================================================
# NAVEGAÇÃO OTIMIZADA
# ============================================================

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
            if st.session_state.page != key:
                st.session_state.page = key
                st.rerun()

st.markdown("---")

# ============================================================
# RENDERIZAÇÃO - APENAS PÁGINA ATUAL
# ============================================================

# Obtém e renderiza APENAS a página atual
current_page = component_cache.get_page(st.session_state.page)
if current_page:
    try:
        current_page.render(filters)
    except Exception as e:
        st.error(f"Erro ao renderizar página: {e}")

# ============================================================
# DEBUG DE PERFORMANCE (OPCIONAL)
# ============================================================

if os.getenv("DEBUG_PERFORMANCE", "false").lower() == "true":
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔍 Debug")
        st.caption(f"Página: {st.session_state.page}")
        st.caption(f"Usuário: {st.session_state.get('username', 'N/A')}")
        st.caption(f"Cache Pages: {len(component_cache._pages)}")