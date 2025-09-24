"""
Componente da barra lateral com filtros
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
import os
from src.services.data_service import DataService
from src.auth import logout
from src.config.database import get_database_type


class SidebarComponent:
    """Componente para renderização da sidebar com filtros"""

    def __init__(self):
        self.data_service = DataService()
        self.db_type = get_database_type()

    def render(self) -> Dict[str, Any]:
        """
        Renderiza sidebar e retorna filtros selecionados

        Returns:
            Dicionário com filtros selecionados
        """
        with st.sidebar:
            st.header("🎯 Filtros")

            # Obtém intervalo de datas disponível
            min_date_available, max_date_available = self.data_service.get_available_date_range()

            # Filtro de data
            date_filters = self._render_date_filter(min_date_available, max_date_available)

            # Filtro de shopping
            shopping_filter = self._render_shopping_filter()

            st.markdown("---")

            # Seletor de layout
            layout = self._render_layout_selector()

            st.markdown("---")

            # Seção de usuário
            self._render_user_section()

            st.markdown("---")

            # Informação de conexão
            self._render_connection_info()

            # Combina todos os filtros
            filters = {
                **date_filters,
                'shopping': shopping_filter,
                'layout': layout
            }

            return filters

    def _render_date_filter(
        self,
        min_date: Optional[pd.Timestamp],
        max_date: Optional[pd.Timestamp]
    ) -> Dict[str, pd.Timestamp]:
        """
        Renderiza filtro de data

        Args:
            min_date: Data mínima disponível
            max_date: Data máxima disponível

        Returns:
            Dicionário com datas selecionadas
        """
        st.subheader("📅 Data de Referência")

        # Verifica se temos dados disponíveis
        if min_date is not None and max_date is not None:
            # Converte para objetos date para o widget date_input
            min_date_obj = min_date.date() if hasattr(min_date, 'date') else min_date
            max_date_obj = max_date.date() if hasattr(max_date, 'date') else max_date

            # Valor padrão é a data mais recente com dados
            default_date = max_date_obj

            data_ref = st.date_input(
                "Selecione a data",
                value=default_date,
                min_value=min_date_obj,
                max_value=max_date_obj,
                help=f"Selecione uma data entre {min_date_obj.strftime('%d/%m/%Y')} e {max_date_obj.strftime('%d/%m/%Y')}"
            )
        else:
            # Sem dados disponíveis ou erro ao carregar dados
            st.error("⚠️ Não foi possível determinar o período de dados disponível")
            st.info("Verifique a conexão com o banco de dados")
            # Usa entrada de data alternativa sem restrições
            data_ref = st.date_input(
                "Selecione a data",
                value=datetime.now(),
                help="Data final do período"
            )

        # Normaliza para Timestamp
        try:
            data_ref_ts = pd.Timestamp(data_ref)
        except Exception:
            data_ref_ts = pd.Timestamp(datetime.now() if max_date is None else max_date)

        # Calcula o período de análise baseado na data de referência
        ano_ref = data_ref_ts.year
        ano_anterior = ano_ref - 1

        # Data inicial: 1º de janeiro do ano anterior (para comparação YoY)
        data_inicio_ts = pd.Timestamp(f'{ano_anterior}-01-01')

        # Se a data inicial calculada está antes dos dados disponíveis, ajusta
        if min_date is not None and data_inicio_ts < min_date:
            data_inicio_ts = min_date
            st.warning(f"⚠️ Ajustado início para {data_inicio_ts.strftime('%d/%m/%Y')} (primeiro dado disponível)")

        # Data final: data selecionada
        data_fim_ts = data_ref_ts

        # Validação adicional
        if min_date is not None and max_date is not None:
            dias_disponiveis = (max_date - min_date).days
            if dias_disponiveis < 365:
                st.warning(f"⚠️ Apenas {dias_disponiveis} dias de dados disponíveis. Comparação YoY pode ser limitada.")

        return {
            'data_inicio': data_inicio_ts,
            'data_fim': data_fim_ts,
            'data_referencia': data_ref_ts
        }

    def _render_shopping_filter(self) -> Optional[str]:
        """
        Renderiza filtro de shopping

        Returns:
            Shopping selecionado ou None para todos
        """
        # Obtém shoppings disponíveis
        available_shoppings = self.data_service.get_available_shoppings()

        if available_shoppings:
            # Adiciona opção "Todos" no início
            shopping_options = ["Todos"] + available_shoppings

            # Define índice padrão para SCIB se disponível, senão usa "Todos"
            default_index = 0  # Padrão para "Todos"
            if "SCIB" in shopping_options:
                default_index = shopping_options.index("SCIB")

            filtro_shopping = st.selectbox(
                "🏪 Shopping",
                options=shopping_options,
                index=default_index,  # SCIB como padrão se disponível
                help="Selecione o shopping para filtrar os dados"
            )

            # Converte "Todos" para None para o filtro
            if filtro_shopping == "Todos":
                return None
            return filtro_shopping
        else:
            # Fallback para entrada de texto
            filtro_shopping = st.text_input(
                "🏪 Shopping (opcional)",
                placeholder="Digite o nome do shopping",
                help="Deixe vazio para ver todos"
            )
            return filtro_shopping if filtro_shopping else None

    def _render_layout_selector(self) -> str:
        """
        Renderiza seletor de layout

        Returns:
            Layout selecionado
        """
        st.header("📐 Layout")

        layout_opcao = st.radio(
            "Disposição dos gráficos:",
            options=["Um abaixo do outro", "Abas"],
            help="Escolha como visualizar os gráficos"
        )

        return layout_opcao

    def _render_user_section(self):
        """Renderiza seção de informações do usuário"""
        st.markdown("### 👤 Usuário")
        st.info(f"Logado como: **{st.session_state.get('username', 'Usuário')}**")

        if st.button("🚪 Sair", width="stretch", type="secondary"):
            logout()

    def _render_connection_info(self):
        """Renderiza informação sobre a conexão do banco de dados"""
        if self.db_type == "supabase":
            schema = os.getenv('SUPABASE_SCHEMA_MAPA', 'mapa_do_bosque')
            st.caption(f"🔗 Conectado a: Supabase - {schema}")
        else:
            db_info = os.getenv('POSTGRES_DATABASE', 'PostgreSQL')
            host_info = os.getenv('POSTGRES_HOST', 'localhost')
            st.caption(f"🔗 Conectado a: PostgreSQL - {db_info}@{host_info}")