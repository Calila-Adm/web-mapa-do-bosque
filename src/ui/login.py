"""
Login page UI component for authentication.
"""

import streamlit as st
from src.auth import check_credentials, generate_token, save_auth_token


def show_login_page():
    """
    Display the login page with authentication form.
    """
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("# 🔐 WBR Dashboard")
        st.markdown("### Portal de Análise de Métricas")
        st.markdown("---")

        # Create login form
        with st.form("login_form", clear_on_submit=False):
            st.markdown("#### Faça login para continuar")

            username = st.text_input(
                "Usuário",
                placeholder="Digite seu usuário",
                key="login_username"
            )

            password = st.text_input(
                "Senha",
                type="password",
                placeholder="Digite sua senha",
                key="login_password"
            )

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                submit_button = st.form_submit_button(
                    "🚀 Entrar",
                    use_container_width=True,
                    type="primary"
                )

            # Process login attempt
            if submit_button:
                if not username:
                    st.error("❌ Por favor, digite seu usuário")
                elif not password:
                    st.error("❌ Por favor, digite sua senha")
                elif check_credentials(username, password):
                    # Set session state for authenticated user
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username

                    # Generate and store auth token
                    token = generate_token(username)
                    st.session_state["auth_token"] = token

                    # Save token to local file for persistence
                    save_auth_token(username, token)

                    st.success("✅ Login realizado com sucesso!")
                    # Trigger app rerun to load main dashboard
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos")

        # Footer information
        st.markdown("---")
        st.caption("🔒 Sistema protegido por autenticação")
        st.caption("Entre em contato com o administrador para obter credenciais")