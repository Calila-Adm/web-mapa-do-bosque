"""
Serviço de dados - Gerenciamento de dados e cache
"""
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import streamlit as st
import os
from src.clients.database.factory import get_database_client, fetch_data_generic
from src.config.database import get_table_config, get_database_type


@st.cache_resource
def get_data_service():
    """Cria DataService uma única vez com cache de recurso"""
    return DataService()


class DataService:
    """Serviço para gerenciamento de dados"""

    def __init__(self):
        self.db_client = get_database_client()
        self.db_type = get_database_type()
        self.tables_config = get_table_config()

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_available_date_range(_self) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
        """
        Obtém as datas mínima e máxima disponíveis no banco de dados

        Returns:
            Tuple com data mínima e máxima disponíveis
        """
        try:
            dates = []

            # Para PostgreSQL/Supabase, carrega dados mínimos
            for table_name in ['pessoas', 'veiculos', 'vendas']:
                config = _self.tables_config[table_name]
                try:
                    # Busca dados da tabela
                    df = fetch_data_generic(
                        client=_self.db_client,
                        config=config,
                        year_filter=None,
                        shopping_filter=None
                    )

                    if df is not None and not df.empty:
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            dates.extend([df['date'].min(), df['date'].max()])
                        elif isinstance(df.index, pd.DatetimeIndex):
                            dates.extend([df.index.min(), df.index.max()])
                except Exception:
                    pass

            if dates:
                # Filtra valores None/NaT
                valid_dates = [d for d in dates if pd.notna(d)]
                if valid_dates:
                    min_date = min(valid_dates)
                    max_date = max(valid_dates)
                    return pd.Timestamp(min_date), pd.Timestamp(max_date)

            return None, None

        except Exception as e:
            st.error(f"Erro ao buscar range de datas: {str(e)}")
            return None, None

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_available_shoppings(_self) -> List[str]:
        """
        Obtém valores únicos de shopping de todas as tabelas

        Returns:
            Lista de shoppings disponíveis
        """
        # Primeiro, verifica se devemos usar dados simulados para demonstração
        use_mock_data = os.getenv("USE_MOCK_SHOPPING_DATA", "false").lower() == "true"

        if use_mock_data:
            # Retorna a lista real de shoppings usada no sistema
            return ["SCIB", "SBGP", "SBI"]

        # Tenta obter dados reais do banco de dados
        try:
            all_shoppings = set()
            shopping_col = os.getenv("WBR_SHOPPING_COL", "shopping")

            # Para PostgreSQL - verificação mais simples
            for table_name in ['pessoas', 'veiculos', 'vendas']:
                config = _self.tables_config.get(table_name, {})
                schema = config.get('schema', 'mapa_do_bosque')
                table = config.get('table', table_name)

                # Tenta consulta simples
                test_query = f"""
                SELECT DISTINCT {shopping_col} as shopping
                FROM {schema}.{table}
                WHERE {shopping_col} IS NOT NULL
                LIMIT 50
                """
                try:
                    result = pd.read_sql(test_query, _self.db_client.connection)
                    if not result.empty and 'shopping' in result.columns:
                        all_shoppings.update(result['shopping'].dropna().tolist())
                except:
                    continue

            # Converte para lista ordenada
            shopping_list = sorted(list(all_shoppings))

            # Se nenhum dado encontrado, retorna a lista real de shoppings
            if not shopping_list:
                return ["SCIB", "SBGP", "SBI"]

            return shopping_list

        except Exception as e:
            # Se tudo falhar, retorna a lista real de shoppings
            print(f"DEBUG: Using default shopping list due to: {str(e)}")
            return ["SCIB", "SBGP", "SBI"]

    @st.cache_data(ttl=300, show_spinner=False)
    def load_table_data(_self, table_name: str, config: Dict[str, Any],
                       date_reference: Optional[pd.Timestamp] = None,
                       shopping_filter: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Carrega dados do banco de dados para uma tabela específica

        Args:
            table_name: Nome da tabela
            config: Configuração da tabela
            date_reference: Data de referência para filtro
            shopping_filter: Filtro de shopping

        Returns:
            DataFrame com os dados já filtrados ou None em caso de erro
        """
        try:
            # Usa a função de busca genérica da factory com filtros
            df = fetch_data_generic(
                client=_self.db_client,
                config=config,
                year_filter=None,
                shopping_filter=shopping_filter,
                date_reference=date_reference
            )
            return df
        except Exception as e:
            st.error(f"Erro ao carregar {config.get('titulo', table_name)}: {str(e)}")
            return None