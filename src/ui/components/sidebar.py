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
        # Lazy initialization
        self._data_service = None
        self.db_type = get_database_type()

    @property
    def data_service(self):
        """Lazy loading do data service"""
        if self._data_service is None:
            from src.services.data_service import get_data_service
            self._data_service = get_data_service()
        return self._data_service

    def render(self) -> Dict[str, Any]:
        """
        Renderiza sidebar e retorna filtros selecionados

        Returns:
            Dicionário com filtros selecionados
        """
        # CSS para personalizar a cor da sidebar
        st.markdown("""
        <style>
        .stSidebar > div:first-child {
            background-color: #383C43 !important;
        }
        .stSidebar {
            background-color: #383C43 !important;
        }
        .stSidebar > div {
            background-color: #383C43 !important;
        }
        /* Força a cor mesmo durante redimensionamento */
        .stSidebar * {
            background-color: inherit !important;
        }
        .stSidebar .element-container {
            background-color: transparent !important;
        }
        /* Cor geral dos textos da sidebar */
        .stSidebar .stMarkdown {
            color: #FAFAFA !important;
        }
        /* Labels dos elementos de filtro */
        .stSidebar .stSelectbox label {
            color: #FAFAFA !important;
        }
        .stSidebar .stRadio label {
            color: #FAFAFA !important;
        }
        .stSidebar .stDateInput label {
            color: #FAFAFA !important;
        }
        .stSidebar .stTextInput label {
            color: #FAFAFA !important;
        }
        /* Estilo personalizado para o título principal "Mapa do Bosque" */
        .sidebar-title {
            font-size: 33.5px !important;
            font-weight: bold !important;
            text-align: center !important;
            color: #FAFAFA !important;
            margin-top: -40px !important;
            margin-bottom: 30px !important;
            padding: 10px 0 !important;
        }
        /* Estilos para títulos das seções "Data" e "Shopping" */
        .section-title {
            font-size: 22px !important;
            font-weight: bold !important;
            color: #FAFAFA !important;
            margin: 15px 0 7px 0 !important;
            padding: 5px 0 !important;
        }
        /* Forçar cor dos headers nativos do Streamlit */
        .stSidebar h1, .stSidebar h2, .stSidebar h3 {
            color: #FAFAFA !important;
        }
        .stSidebar .stMarkdown h1, .stSidebar .stMarkdown h2, .stSidebar .stMarkdown h3 {
            color: #FAFAFA !important;
        }
        /* Cor do texto dos elementos de input e seleção */
        .stSidebar .stSelectbox > div > div {
            color: #FAFAFA !important;
        }
        .stSidebar .stDateInput > div > div {
            color: #FAFAFA !important;
        }
        .stSidebar .stTextInput > div > div {
            color: #FAFAFA !important;
        }
        /* Estilo específico para o campo interno de data */
        .stSidebar .stDateInput input {
            color: #FAFAFA !important;
            background-color: #383C43 !important;
            border: 1px solid #383C43 !important;
        }
        .stSidebar .stDateInput input:focus {
            border-color: #383C43 !important;
            outline: none !important;
            background-color: #383C43 !important;
        }
        .stSidebar .stDateInput input[type="text"] {
            color: #FAFAFA !important;
        }
        .stSidebar input[type="date"] {
            color: #FAFAFA !important;
        }
        /* Forçar cor em todos os inputs da sidebar */
        .stSidebar input {
            color: #FAFAFA !important;
        }
        /* Estilo para o ícone de calendário */
        .stSidebar .stDateInput button {
            color: #FAFAFA !important;
            background-color: #2C3037 !important;
        }
        /* Forçar cor do texto no date picker */
        .stSidebar [data-baseweb="input"] {
            color: #FAFAFA !important;
        }
        .stSidebar [data-baseweb="input"] input {
            color: #FAFAFA !important;
        }
        /* Dar mais espaço entre títulos e campos */
        .stSidebar .stDateInput {
            margin-top: 5px !important;
        }
        .stSidebar .stSelectbox {
            margin-top: 5px !important;
        }
        .stSidebar .stTextInput {
            margin-top: 5px !important;
        }
        /* Esconder labels dos campos */
        .stSidebar .stDateInput label {
            display: none !important;
        }
        .stSidebar .stSelectbox label {
            display: none !important;
        }
        .stSidebar .stTextInput label {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

        with st.sidebar:
            st.markdown('<h1 class="sidebar-title">Mapa do Bosque</h1>', unsafe_allow_html=True)

            # Obtém intervalo de datas disponível
            min_date_available, max_date_available = self.data_service.get_available_date_range()

            # Filtro de data
            date_filters = self._render_date_filter(min_date_available, max_date_available)

            # Filtro de shopping
            shopping_filter = self._render_shopping_filter()


            # Combina todos os filtros
            filters = {
                **date_filters,
                'shopping': shopping_filter,
                'metodo_semana': 'travelling'  # Sempre usar travelling week
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
        st.markdown('<h2 class="section-title">📅 Data</h2>', unsafe_allow_html=True)

        # Verifica se temos dados disponíveis
        if min_date is not None and max_date is not None:
            # Converte para objetos date para o widget date_input
            min_date_obj = min_date.date() if hasattr(min_date, 'date') else min_date
            max_date_obj = max_date.date() if hasattr(max_date, 'date') else max_date

            # Valor padrão é a data mais recente com dados
            default_date = max_date_obj

            data_ref = st.date_input(
                "Data",
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
                "Data",
                value=datetime.now(),
                help="Data final do período"
            )

        # Normaliza para Timestamp
        try:
            data_ref_ts = pd.Timestamp(data_ref)
        except Exception:
            data_ref_ts = pd.Timestamp(datetime.now() if max_date is None else max_date)

        # Valida se data_ref_ts é válido
        if pd.isna(data_ref_ts) or data_ref_ts is None:
            data_ref_ts = pd.Timestamp(datetime.now())

        # Calcula o período de análise baseado na data de referência
        ano_ref = data_ref_ts.year if hasattr(data_ref_ts, 'year') else datetime.now().year

        # Valida ano_ref
        if pd.isna(ano_ref) or ano_ref is None:
            ano_ref = datetime.now().year

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

            st.markdown('<h2 class="section-title">🏪 Shopping</h2>', unsafe_allow_html=True)
            filtro_shopping = st.selectbox(
                "Shopping",
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
            st.markdown('<h2 class="section-title">🏪 Shopping</h2>', unsafe_allow_html=True)
            filtro_shopping = st.text_input(
                "Shopping",
                placeholder="Digite o nome do shopping",
                help="Deixe vazio para ver todos"
            )
            return filtro_shopping if filtro_shopping else None




