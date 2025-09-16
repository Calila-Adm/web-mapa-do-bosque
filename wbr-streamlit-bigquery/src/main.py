#!/usr/bin/env python3
"""
WBR Dashboard - Main Application Entry Point
============================================
Dashboard principal para análise de métricas WBR (Working Backwards Reporting).
"""

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.env import load_environment_variables
# from src.clients.database.bigquery import BigQueryClient  # Comentado - usando factory agora
from src.clients.database.factory import get_database_client, get_table_config, fetch_data_generic, get_multiple_clients, get_supabase_table_config
from src.core.wbr import gerar_grafico_wbr, calcular_metricas_wbr
from src.core.wbr_metrics import calcular_kpis  # Now using unified wbr_metrics

# Load environment variables
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, '..'))
load_environment_variables(base_dir=PROJECT_ROOT)

# Database configuration
db_type = os.getenv("DB_TYPE", "postgresql").lower()

# Normalize credential path for BigQuery (if using BigQuery)
if db_type == "bigquery":
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and not os.path.isabs(cred_path):
        abs_path = os.path.join(PROJECT_ROOT, cred_path)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path

# Initialize database clients
db_client = get_database_client()  # Primary client
db_clients = get_multiple_clients()  # All available clients

# Page configuration
st.set_page_config(page_title="WBR Dashboard", layout="wide", page_icon="📊")

# Get table configurations
TABLES_CONFIG = get_table_config(db_type)  # Primary database tables

# Get Supabase table configurations if available
SUPABASE_CONFIG = {}
if 'supabase' in db_clients:
    SUPABASE_CONFIG = get_supabase_table_config()

# Check database configuration
if db_type == "bigquery":
    BQ_PROJECT = os.getenv("BIGQUERY_PROJECT_ID")
    BQ_DATASET = os.getenv("BIGQUERY_DATASET")
    if not BQ_PROJECT or not BQ_DATASET:
        st.error("❌ Configuração do BigQuery não encontrada!")
        st.info("Configure as seguintes variáveis de ambiente:")
        st.code("""
        BIGQUERY_PROJECT_ID=seu-projeto
        BIGQUERY_DATASET=seu-dataset
        GOOGLE_APPLICATION_CREDENTIALS=caminho/para/credentials.json
        """)
        st.stop()
elif db_type in ["postgresql", "postgres"]:
    # Check PostgreSQL configuration
    if not os.getenv("DATABASE_URL") and not (os.getenv("POSTGRES_DATABASE") and os.getenv("POSTGRES_USER")):
        st.error("❌ Configuração do PostgreSQL não encontrada!")
        st.info("Configure DATABASE_URL ou as variáveis individuais:")
        st.code("""
        DATABASE_URL=postgresql://user:password@host:port/dbname
        # OU
        POSTGRES_HOST=localhost
        POSTGRES_PORT=5432
        POSTGRES_DATABASE=seu-banco
        POSTGRES_USER=seu-usuario
        POSTGRES_PASSWORD=sua-senha
        """)
        st.stop()
else:
    st.error(f"❌ Tipo de banco de dados não reconhecido: {db_type}")
    st.info("Configure DB_TYPE como 'bigquery' ou 'postgresql' no arquivo .env")
    st.stop()

# Cache function for getting available date range
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def get_available_date_range():
    """Get the min and max dates available in the database - optimized version"""
    try:
        dates = []
        
        # For BigQuery, we can optimize with a specific query
        if db_type == "bigquery":
            for table_name in ['pessoas', 'veiculos', 'vendas']:
                config = TABLES_CONFIG[table_name]
                query = f"""
                SELECT 
                    MIN({config['coluna_data']}) as min_date,
                    MAX({config['coluna_data']}) as max_date
                FROM `{config['table']}`
                WHERE {config['coluna_data']} IS NOT NULL
                """
                try:
                    result = db_client.query(query).to_dataframe()
                    if not result.empty:
                        dates.extend([result['min_date'].iloc[0], result['max_date'].iloc[0]])
                except Exception:
                    pass
        else:
            # For PostgreSQL or other databases, load minimal data
            for table_name in ['pessoas', 'veiculos', 'vendas']:
                config = TABLES_CONFIG[table_name]
                try:
                    # Try to get just the date column
                    df = fetch_data_generic(
                        client=db_client,
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
            # Filter out None/NaT values
            valid_dates = [d for d in dates if pd.notna(d)]
            if valid_dates:
                min_date = min(valid_dates)
                max_date = max(valid_dates)
                return pd.Timestamp(min_date), pd.Timestamp(max_date)
        
        return None, None
            
    except Exception as e:
        st.error(f"Erro ao buscar range de datas: {str(e)}")
        return None, None

# Title and description
st.title("📊 Dashboard WBR - Análise de Fluxo")
st.markdown("---")

# Cache function for getting available shoppings
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def get_available_shoppings():
    """Get unique shopping values from all tables"""
    # First, check if we should use mock data for demonstration
    use_mock_data = os.getenv("USE_MOCK_SHOPPING_DATA", "false").lower() == "true"

    if use_mock_data:
        # Return the actual shopping list used in the system
        return [
            "SCIB",
            "SBGP",
            "SBI"
        ]

    # Try to get real data from database
    try:
        all_shoppings = set()
        shopping_col = os.getenv("WBR_SHOPPING_COL", "shopping")

        # Try a simpler approach - just check if any data has shopping column
        test_query = None

        if db_type == "bigquery":
            # For BigQuery - check first table only to see if column exists
            config = TABLES_CONFIG.get('pessoas', {})
            if config.get('table'):
                test_query = f"""
                SELECT DISTINCT {shopping_col} as shopping
                FROM `{config['table']}`
                WHERE {shopping_col} IS NOT NULL
                LIMIT 50
                """
                try:
                    result = db_client.query(test_query).to_dataframe()
                    if not result.empty and 'shopping' in result.columns:
                        all_shoppings.update(result['shopping'].dropna().tolist())
                except:
                    pass  # Column doesn't exist
        else:
            # For PostgreSQL - simpler check
            for table_name in ['pessoas', 'veiculos', 'vendas']:
                config = TABLES_CONFIG.get(table_name, {})
                schema = config.get('schema', 'mapa_do_bosque')
                table = config.get('table', table_name)

                # Try simple query without TRIM
                test_query = f"""
                SELECT DISTINCT {shopping_col} as shopping
                FROM {schema}.{table}
                WHERE {shopping_col} IS NOT NULL
                LIMIT 50
                """
                try:
                    result = pd.read_sql(test_query, db_client.connection)
                    if not result.empty and 'shopping' in result.columns:
                        all_shoppings.update(result['shopping'].dropna().tolist())
                except:
                    continue  # Try next table

        # Convert to sorted list
        shopping_list = sorted(list(all_shoppings))

        # If no data found, return the actual shopping list
        if not shopping_list:
            # Return the real shopping centers from the system
            return [
                "SCIB",
                "SBGP",
                "SBI"
            ]

        return shopping_list

    except Exception as e:
        # If all fails, return the real shopping list so the dropdown still works
        print(f"DEBUG: Using default shopping list due to: {str(e)}")
        return [
            "SCIB",
            "SBGP",
            "SBI"
        ]

# Get available date range before showing the sidebar
min_date_available, max_date_available = get_available_date_range()

# Get available shoppings
available_shoppings = get_available_shoppings()

# Sidebar with filters only (no BigQuery configuration)
with st.sidebar:
    st.header("🎯 Filtros")
    
    # Date reference filter
    st.subheader("📅 Data de Referência")
    
    # Check if we have data available
    if min_date_available is not None and max_date_available is not None:
        # Convert to date objects for the date_input widget
        min_date = min_date_available.date() if hasattr(min_date_available, 'date') else min_date_available
        max_date = max_date_available.date() if hasattr(max_date_available, 'date') else max_date_available
        
        # Default value should be the most recent date with data, not today
        default_date = max_date
        
        # Show available date range - REMOVIDO conforme solicitado
        # st.caption(f"📊 Dados disponíveis: {min_date.strftime('%d/%m/%Y')} até {max_date.strftime('%d/%m/%Y')}")
        
        data_ref = st.date_input(
            "Selecione a data",
            value=default_date,
            min_value=min_date,
            max_value=max_date,
            help=f"Selecione uma data entre {min_date.strftime('%d/%m/%Y')} e {max_date.strftime('%d/%m/%Y')}"
        )
    else:
        # No data available or error loading data
        st.error("⚠️ Não foi possível determinar o período de dados disponível")
        st.info("Verifique a conexão com o banco de dados")
        # Use a fallback date input without restrictions
        data_ref = st.date_input(
            "Selecione a data",
            value=datetime.now(),
            help="Data final do período"
        )
    
    # Normaliza para Timestamp
    try:
        data_ref_ts = pd.Timestamp(data_ref)
    except Exception:
        data_ref_ts = pd.Timestamp(datetime.now() if max_date_available is None else max_date_available)
    
    # Calcula o período de análise baseado na data de referência
    # Precisamos de DOIS anos de dados para comparação YoY
    ano_ref = data_ref_ts.year
    ano_anterior = ano_ref - 1
    ano_inicio = ano_ref - 2  # Pega desde 2 anos atrás
    
    # Data inicial: 1º de janeiro do ano anterior
    # Para garantir que temos dados suficientes para comparação
    data_inicio_ts = pd.Timestamp(f'{ano_anterior}-01-01')
    
    # Se a data inicial calculada está antes dos dados disponíveis, ajusta
    if min_date_available is not None and data_inicio_ts < min_date_available:
        data_inicio_ts = min_date_available
        st.warning(f"⚠️ Ajustado início para {data_inicio_ts.strftime('%d/%m/%Y')} (primeiro dado disponível)")
    
    # Data final: data selecionada
    data_fim_ts = data_ref_ts
    
    # Validação adicional: verifica se temos dados suficientes para comparação YoY
    if min_date_available is not None and max_date_available is not None:
        dias_disponiveis = (max_date_available - min_date_available).days
        if dias_disponiveis < 365:
            st.warning(f"⚠️ Apenas {dias_disponiveis} dias de dados disponíveis. Comparação YoY pode ser limitada.")
    
    # Informações de período e comparação removidas conforme solicitado
    
    # Shopping filter (optional - will be populated if column exists)
    shopping_col = os.getenv("WBR_SHOPPING_COL", "shopping")

    # Always show dropdown since we guarantee to have shopping options
    if available_shoppings:
        # Add "Todos" option at the beginning
        shopping_options = ["Todos"] + available_shoppings

        filtro_shopping = st.selectbox(
            "🏪 Shopping",
            options=shopping_options,
            index=0,  # Default to "Todos"
            help="Selecione o shopping para filtrar os dados"
        )

        # Convert "Todos" to None for the filter
        if filtro_shopping == "Todos":
            filtro_shopping = None
    else:
        # This should not happen anymore, but keep as fallback
        filtro_shopping = st.text_input(
            "🏪 Shopping (opcional)",
            placeholder="Digite o nome do shopping",
            help="Deixe vazio para ver todos"
        )
    
    st.markdown("---")
    st.header("📐 Layout")
    
    # Layout selector - removida opção "Lado a lado"
    layout_opcao = st.radio(
        "Disposição dos gráficos:",
        options=["Um abaixo do outro", "Abas"],
        help="Escolha como visualizar os gráficos"
    )
    
    st.markdown("---")
    # Mostra informação de conexão apropriada
    if db_type == "bigquery":
        st.caption(f"🔗 Conectado a: BigQuery - {os.getenv('BIGQUERY_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET')}")
    else:
        db_info = os.getenv('POSTGRES_DATABASE', 'PostgreSQL')
        host_info = os.getenv('POSTGRES_HOST', 'localhost')
        st.caption(f"🔗 Conectado a: PostgreSQL - {db_info}@{host_info}")

# Cache function for loading data
@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def load_table_data(config: dict):
    """Load data from database for a specific table configuration"""
    try:
        # Use the generic fetch function from factory
        df = fetch_data_generic(
            client=db_client,
            config=config,
            year_filter=None,  # Applied later in apply_filters
            shopping_filter=None  # Applied later in apply_filters
        )
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {config['titulo']}: {str(e)}")
        return None

def apply_filters(df: pd.DataFrame, date_start=None, date_end=None, year_filter=None, shopping_filter=None):
    """Apply filters to dataframe"""
    if df is None or df.empty:
        return df
    
    # Apply date range filter
    if date_start and date_end:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= date_start) & (df['date'] <= date_end)]
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df[(df.index >= date_start) & (df.index <= date_end)]
    
    # Apply year filter (if no date range specified)
    elif year_filter:
        if 'date' in df.columns:
            df = df[pd.to_datetime(df['date']).dt.year == year_filter]
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df[df.index.year == year_filter]
    
    # Apply shopping filter
    if shopping_filter and 'shopping' in df.columns:
        # Use exact match for dropdown selection
        df = df[df['shopping'] == shopping_filter]
    
    return df

def render_metrics(df: pd.DataFrame, titulo: str):
    """Render KPI metrics for a dataframe"""
    if df is None or df.empty:
        st.warning(f"Sem dados para calcular KPIs de {titulo}")
        return
    
    try:
        kpis = calcular_kpis(df, data_referencia=data_ref_ts)
        
        # Usar 2 colunas para métricas em layout mais compacto
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="📈 YoY",
                value=f"{kpis.get('yoy_pct', 0):.1f}%",
                delta=f"{kpis.get('yoy_abs', 0):,.0f}",
                help="Comparação Year-over-Year"
            )
            st.metric(
                label="📅 MTD",
                value=f"{kpis.get('mtd_atual', 0):,.0f}",
                delta=f"{kpis.get('mtd_pct', 0):.1f}%",
                help="Month-to-Date"
            )
        
        with col2:
            st.metric(
                label="📊 WoW",
                value=f"{kpis.get('wow_pct', 0):.1f}%",
                delta=f"{kpis.get('wow_abs', 0):,.0f}",
                help="Comparação Week-over-Week"
            )
            st.metric(
                label="📌 Média",
                value=f"{df['metric_value'].mean():,.0f}",
                help="Média do período"
            )
    except Exception as e:
        st.error(f"Erro ao calcular KPIs: {str(e)}")

def render_chart(config: dict, df: pd.DataFrame):
    """Render WBR chart for a specific configuration"""
    if df is None or df.empty:
        st.warning(f"Sem dados disponíveis para {config['titulo']}")
        return
    
    try:
        # Generate WBR chart
        # O DataFrame vem com colunas normalizadas: 'date' e 'metric_value'
        fig = gerar_grafico_wbr(
            df=df,
            coluna_data='date',  # Nome da coluna normalizada
            coluna_pessoas='metric_value',  # Nome da coluna normalizada
            titulo=f"{config['icon']} {config['titulo']}",
            unidade=config['unidade'],
            data_referencia=data_ref_ts
        )

        # Display chart
        st.plotly_chart(fig, width='stretch', key=f"chart_{config['table']}")

        # Display metrics below chart - REMOVIDO conforme solicitado
        # render_metrics(df, config['titulo'])

        # Optional: Show data preview
        with st.expander("📋 Ver dados brutos"):
            # Be resilient if 'date' is the index
            display_df = df.reset_index()
            # If reset_index created a column named 'index' and 'date' doesn't exist, rename it to 'date'
            if 'date' not in display_df.columns and 'index' in display_df.columns:
                display_df = display_df.rename(columns={'index': 'date'})
            
            # Agrupar por data e somar metric_value para visualização diária
            if 'date' in display_df.columns and 'metric_value' in display_df.columns:
                # Garantir que date seja datetime
                display_df['date'] = pd.to_datetime(display_df['date'])
                # Agrupar por data (apenas a parte da data, sem hora)
                daily_df = display_df.groupby(display_df['date'].dt.date).agg({
                    'metric_value': 'sum'
                }).reset_index()
                daily_df.columns = ['Data', 'Total_Diario']
                
                # Ordenar por data (mais recente primeiro)
                daily_df = daily_df.sort_values('Data', ascending=False)
                
                # Adicionar dia da semana
                daily_df['Dia_Semana'] = pd.to_datetime(daily_df['Data']).dt.strftime('%a')
                dias_pt = {'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui', 
                          'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'}
                daily_df['Dia_Semana'] = daily_df['Dia_Semana'].replace(dias_pt)
                
                # Formatar a data para exibição
                daily_df['Data'] = pd.to_datetime(daily_df['Data']).dt.strftime('%d/%m/%Y')
                
                # Formatar o valor com separador de milhares
                daily_df['Total_Diario'] = daily_df['Total_Diario'].apply(lambda x: f"{x:,.0f}")
                
                # Reorganizar colunas
                daily_df = daily_df[['Data', 'Dia_Semana', 'Total_Diario']]
                daily_df.columns = ['Data', 'Dia', 'Total Diário']
                
                # Mostrar últimos 30 dias
                st.dataframe(daily_df.head(30), width='stretch', hide_index=True)
            else:
                # Fallback para o comportamento original se as colunas esperadas não existirem
                cols = [c for c in ['date', 'metric_value'] if c in display_df.columns]
                st.dataframe(display_df[cols].tail(30), width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

# Load data for all tables
with st.spinner("Carregando dados..."):
    df_pessoas = load_table_data(TABLES_CONFIG['pessoas'])
    df_veiculos = load_table_data(TABLES_CONFIG['veiculos'])
    df_vendas = load_table_data(TABLES_CONFIG['vendas'])
    
    # Apply filters
    df_pessoas_filtered = apply_filters(
        df_pessoas, 
        date_start=data_inicio_ts,
        date_end=data_fim_ts,
        year_filter=None,
        shopping_filter=filtro_shopping
    ) if df_pessoas is not None else None
    
    df_veiculos_filtered = apply_filters(
        df_veiculos,
        date_start=data_inicio_ts,
        date_end=data_fim_ts,
        year_filter=None,
        shopping_filter=filtro_shopping
    ) if df_veiculos is not None else None
    
    df_vendas_filtered = apply_filters(
        df_vendas,
        date_start=data_inicio_ts,
        date_end=data_fim_ts,
        year_filter=None,
        shopping_filter=filtro_shopping
    ) if df_vendas is not None else None

# Show active filters as info
if filtro_shopping:
    st.info(f"🏪 **Filtro ativo:** Shopping {filtro_shopping}")

# Render based on selected layout
if layout_opcao == "Um abaixo do outro":
    # Vertical layout
    st.subheader(f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}")
    if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
        render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
    else:
        st.warning("Nenhum dado de pessoas encontrado")
    
    st.markdown("---")
    
    st.subheader(f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}")
    if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
        render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
    else:
        st.warning("Nenhum dado de veículos encontrado")
    
    st.markdown("---")
    
    st.subheader(f"{TABLES_CONFIG['vendas']['icon']} {TABLES_CONFIG['vendas']['titulo']}")
    if df_vendas_filtered is not None and not df_vendas_filtered.empty:
        render_chart(TABLES_CONFIG['vendas'], df_vendas_filtered)
    else:
        st.warning("Nenhum dado de vendas encontrado")

else:  # Abas
    # Tabs layout
    tab_pessoas, tab_veiculos, tab_vendas = st.tabs([
        f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}",
        f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}",
        f"{TABLES_CONFIG['vendas']['icon']} {TABLES_CONFIG['vendas']['titulo']}"
    ])
    
    with tab_pessoas:
        if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
            render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
        else:
            st.warning("Nenhum dado de pessoas encontrado")
    
    with tab_veiculos:
        if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
            render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
        else:
            st.warning("Nenhum dado de veículos encontrado")
    
    with tab_vendas:
        if df_vendas_filtered is not None and not df_vendas_filtered.empty:
            render_chart(TABLES_CONFIG['vendas'], df_vendas_filtered)
        else:
            st.warning("Nenhum dado de vendas encontrado")

# Instagram Metrics Section from Supabase PostgreSQL
# Verifica se temos a connection string do Supabase configurada
if os.getenv("SUPABASE_DATABASE_URL"):
    st.markdown("---")
    st.header("📱 Métricas do Instagram")

    # Import Supabase PostgreSQL client and plotly
    from src.clients.database.supabase_postgres import SupabaseClient
    import plotly.graph_objects as go
    import plotly.express as px

    # Initialize Supabase PostgreSQL client
    try:
        supabase_client = SupabaseClient()
        supabase_connected = supabase_client.test_connection()
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        supabase_connected = False

    if supabase_connected:
        # Get date range for queries
        date_start_str = data_inicio_ts.strftime('%Y-%m-%d')
        date_end_str = data_fim_ts.strftime('%Y-%m-%d')

        # Get shopping filter from sidebar (if exists)
        shopping_filter_instagram = filtro_shopping if filtro_shopping != "Todos" else None

        # Load engagement data with caching
        @st.cache_data(ttl=300, show_spinner=False)
        def load_instagram_engagement_data(date_start, date_end, shopping_filter=None):
            """Carrega dados de engajamento do Instagram"""
            try:
                df = supabase_client.get_engagement_data(
                    date_start=date_start,
                    date_end=date_end,
                    shopping_filter=shopping_filter
                )
                if not df.empty:
                    df['data'] = pd.to_datetime(df['data'])
                return df
            except Exception as e:
                st.error(f"Erro ao carregar dados de engajamento: {str(e)}")
                return pd.DataFrame()


    # Load data
    with st.spinner('Carregando dados do Instagram...'):
        # Load engagement data (contains likes, comments, shares, saves)
        df_engagement = load_instagram_engagement_data(date_start_str, date_end_str, shopping_filter_instagram)

        # Load post count data
        @st.cache_data(ttl=300, show_spinner=False)
        def load_instagram_post_count_data(date_start, date_end, shopping_filter=None):
            """Carrega contagem de posts do Instagram"""
            try:
                df = supabase_client.get_post_count_data(
                    date_start=date_start,
                    date_end=date_end,
                    shopping_filter=shopping_filter
                )
                if not df.empty:
                    df['data'] = pd.to_datetime(df['data'])
                    # Renomeia colunas para compatibilidade
                    df.columns = ['shopping', 'data', 'total_posts']
                return df
            except Exception as e:
                st.error(f"Erro ao carregar contagem de posts: {str(e)}")
                return pd.DataFrame()

        # Carrega dados dentro do bloco if supabase_connected
        if supabase_connected:
            with st.spinner('Carregando dados do Instagram...'):
                df_engagement = load_instagram_engagement_data(date_start_str, date_end_str, shopping_filter_instagram)
                df_post_count = load_instagram_post_count_data(date_start_str, date_end_str, shopping_filter_instagram)

    # Define colors for each shopping
    shopping_colors = {
        'SCIB': '#1f77b4',  # Blue
        'SBGP': '#2ca02c',  # Green
        'SBI': '#d62728'    # Red
    }

    # Create tabs for different metrics
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Engajamento Total",
        "❤️ Likes",
        "💬 Comentários",
        "🔄 Compartilhamentos",
        "💾 Salvamentos",
        "📝 Posts Publicados"
    ])

    # Function to create time series chart
    def create_instagram_chart(df, metric_col, title, y_label):
        """Cria gráfico de linha temporal para métrica do Instagram"""
        if df.empty:
            st.warning(f"Sem dados disponíveis para {title}")
            return None

        fig = go.Figure()

        # If shopping filter is active, show single line
        if shopping_filter_instagram:
            fig.add_trace(go.Scatter(
                x=df['data'],
                y=df[metric_col],
                mode='lines+markers',
                name=shopping_filter_instagram,
                line=dict(color=shopping_colors.get(shopping_filter_instagram, '#1f77b4'), width=2),
                marker=dict(size=6)
            ))
        else:
            # Show lines for each shopping
            for shopping in df['shopping'].unique():
                df_shop = df[df['shopping'] == shopping]
                fig.add_trace(go.Scatter(
                    x=df_shop['data'],
                    y=df_shop[metric_col],
                    mode='lines+markers',
                    name=shopping,
                    line=dict(color=shopping_colors.get(shopping, '#666'), width=2),
                    marker=dict(size=6)
                ))

        fig.update_layout(
            title=title,
            xaxis_title="Data",
            yaxis_title=y_label,
            hovermode='x unified',
            showlegend=True if not shopping_filter_instagram else False,
            height=400
        )

        return fig

    # Tab 1: Engajamento Total
    with tab1:
        if not df_engagement.empty:
            fig = create_instagram_chart(
                df_engagement,
                'engajamento_total',
                'Engajamento Total por Dia',
                'Total de Interações'
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # Show summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", f"{df_engagement['engajamento_total'].sum():,.0f}")
                with col2:
                    st.metric("Média Diária", f"{df_engagement['engajamento_total'].mean():,.0f}")
                with col3:
                    st.metric("Máximo", f"{df_engagement['engajamento_total'].max():,.0f}")
                with col4:
                    st.metric("Posts", f"{df_engagement['total_posts'].sum():,.0f}")
        else:
            st.info("Sem dados de engajamento disponíveis")

    # Tab 2: Likes
    with tab2:
        if not df_engagement.empty:
            fig = create_instagram_chart(
                df_engagement,
                'total_likes',
                'Total de Likes por Dia',
                'Quantidade de Likes'
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Likes", f"{df_engagement['total_likes'].sum():,.0f}")
                with col2:
                    st.metric("Média por Dia", f"{df_engagement['total_likes'].mean():,.0f}")
                with col3:
                    avg_per_post = df_engagement['total_likes'].sum() / max(df_engagement['total_posts'].sum(), 1)
                    st.metric("Média por Post", f"{avg_per_post:,.0f}")
        else:
            st.info("Sem dados de likes disponíveis")

    # Tab 3: Comentários
    with tab3:
        if not df_engagement.empty:
            fig = create_instagram_chart(
                df_engagement,
                'total_comentarios',
                'Total de Comentários por Dia',
                'Quantidade de Comentários'
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Comentários", f"{df_engagement['total_comentarios'].sum():,.0f}")
                with col2:
                    st.metric("Média por Dia", f"{df_engagement['total_comentarios'].mean():,.0f}")
                with col3:
                    avg_per_post = df_engagement['total_comentarios'].sum() / max(df_engagement['total_posts'].sum(), 1)
                    st.metric("Média por Post", f"{avg_per_post:,.0f}")
        else:
            st.info("Sem dados de comentários disponíveis")

    # Tab 4: Compartilhamentos
    with tab4:
        if not df_engagement.empty:
            fig = create_instagram_chart(
                df_engagement,
                'total_compartilhamentos',
                'Total de Compartilhamentos por Dia',
                'Quantidade de Compartilhamentos'
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", f"{df_engagement['total_compartilhamentos'].sum():,.0f}")
                with col2:
                    st.metric("Média por Dia", f"{df_engagement['total_compartilhamentos'].mean():,.0f}")
                with col3:
                    avg_per_post = df_engagement['total_compartilhamentos'].sum() / max(df_engagement['total_posts'].sum(), 1)
                    st.metric("Média por Post", f"{avg_per_post:,.0f}")
        else:
            st.info("Sem dados de compartilhamentos disponíveis")

    # Tab 5: Salvamentos
    with tab5:
        if not df_engagement.empty:
            fig = create_instagram_chart(
                df_engagement,
                'total_salvos',
                'Total de Salvamentos por Dia',
                'Quantidade de Salvamentos'
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Salvamentos", f"{df_engagement['total_salvos'].sum():,.0f}")
                with col2:
                    st.metric("Média por Dia", f"{df_engagement['total_salvos'].mean():,.0f}")
                with col3:
                    avg_per_post = df_engagement['total_salvos'].sum() / max(df_engagement['total_posts'].sum(), 1)
                    st.metric("Média por Post", f"{avg_per_post:,.0f}")
        else:
            st.info("Sem dados de salvamentos disponíveis")

    # Tab 6: Posts Publicados
    with tab6:
        if not df_post_count.empty:
            # Prepare data for chart
            df_post_chart = df_post_count.copy()
            df_post_chart.columns = ['shopping', 'data', 'total_posts']

            fig = create_instagram_chart(
                df_post_chart,
                'total_posts',
                'Quantidade de Posts Publicados',
                'Número de Posts'
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Posts", f"{df_post_chart['total_posts'].sum():,.0f}")
                with col2:
                    st.metric("Média por Dia", f"{df_post_chart['total_posts'].mean():,.1f}")
                with col3:
                    days = (df_post_chart['data'].max() - df_post_chart['data'].min()).days + 1
                    st.metric("Período (dias)", f"{days}")

# Advanced WBR Metrics Section
st.markdown("---")
st.header("📊 Métricas WBR Avançadas")

with st.expander("🔍 Análise Detalhada de Métricas WBR", expanded=False):
    # Check if we have data to analyze
    if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
        st.subheader("Pessoas - Análise WOW/YOY")
        
        # Calculate advanced metrics
        metricas_derivadas = {
            'taxa_crescimento': {
                'type': 'division',
                'numerator': 'metric_value',
                'denominator': 'metric_value',
                'description': 'Taxa de crescimento relativa'
            }
        } if 'metric_value' in df_pessoas_filtered.columns else None
        
        metrics_result = calcular_metricas_wbr(
            df_pessoas_filtered,
            data_referencia=data_ref_ts,
            coluna_data='date',
            coluna_metrica='metric_value',
            metricas_derivadas=metricas_derivadas
        )
        
        if metrics_result.get('success'):
            # Display comparisons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Métricas Analisadas",
                    metrics_result.get('metrics_analyzed', 0)
                )
            
            with col2:
                summary = metrics_result.get('summary', [])
                if summary:
                    avg_wow = sum(s.get('WOW_%', 0) or 0 for s in summary) / len(summary)
                    st.metric(
                        "WOW Médio",
                        f"{avg_wow:.1f}%",
                        delta=f"{avg_wow:.1f}%"
                    )
            
            with col3:
                if summary:
                    avg_yoy = sum(s.get('YOY_%', 0) or 0 for s in summary) / len(summary)
                    st.metric(
                        "YOY Médio",
                        f"{avg_yoy:.1f}%",
                        delta=f"{avg_yoy:.1f}%"
                    )
            
            # Show summary table
            if summary:
                st.subheader("📈 Resumo de Métricas")
                summary_df = pd.DataFrame(summary)
                st.dataframe(
                    summary_df,
                    width='stretch',
                    hide_index=True
                )
            
            # Show trailing weeks comparison
            st.subheader("📅 Comparação de Semanas")
            tab1, tab2 = st.tabs(["Ano Atual", "Ano Anterior"])
            
            with tab1:
                cy_data = metrics_result.get('trailing_weeks', {}).get('current_year', [])
                if cy_data:
                    st.dataframe(pd.DataFrame(cy_data), width='stretch', hide_index=True)
            
            with tab2:
                py_data = metrics_result.get('trailing_weeks', {}).get('previous_year', [])
                if py_data:
                    st.dataframe(pd.DataFrame(py_data), width='stretch', hide_index=True)
        else:
            st.warning(f"Não foi possível calcular métricas avançadas: {metrics_result.get('error', 'Erro desconhecido')}")
    else:
        st.info("Carregue dados primeiro para ver as métricas WBR avançadas")

# Footer
st.markdown("---")
st.caption("💡 Dica: Use os filtros na barra lateral para refinar a análise")