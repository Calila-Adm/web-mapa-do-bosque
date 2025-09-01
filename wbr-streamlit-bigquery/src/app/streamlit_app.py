import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.env import load_environment_variables
from src.data.bigquery_client import BigQueryClient
from src.wbr import gerar_grafico_wbr
from src.wbr.kpis import calcular_kpis

# Load environment variables
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, '..'))
load_environment_variables(base_dir=PROJECT_ROOT)

# Normalize credential path to absolute (if relative)
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if cred_path and not os.path.isabs(cred_path):
    abs_path = os.path.join(PROJECT_ROOT, cred_path)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path

# Initialize the BigQuery client
bq_client = BigQueryClient()

# Page configuration
st.set_page_config(page_title="WBR Dashboard", layout="wide", page_icon="📊")

# Hardcoded configurations for each table
TABLES_CONFIG = {
    'pessoas': {
        'table': 'brief_fluxo_de_pessoas',
        'date_col': 'data_de_entrada',
        'metric_col': 'quantidade_de_registros_de_entrada',
        'titulo': 'Fluxo de Pessoas',
        'unidade': 'pessoas',
        'icon': '👥',
        'color': '#1E90FF'  # Blue
    },
    'veiculos': {
        'table': 'brief_fluxo_de_veiculos',
        'date_col': 'data_fluxo',
        'metric_col': 'entradas_veiculos',
        'titulo': 'Fluxo de Veículos',
        'unidade': 'veículos',
        'icon': '🚗',
        'color': '#FF6B6B'  # Red
    }
}

# Get BigQuery configuration from environment
BQ_PROJECT = os.getenv("BIGQUERY_PROJECT_ID")
BQ_DATASET = os.getenv("BIGQUERY_DATASET")

# Check if BigQuery is configured
if not BQ_PROJECT or not BQ_DATASET:
    st.error("❌ Configuração do BigQuery não encontrada!")
    st.info("Configure as seguintes variáveis de ambiente:")
    st.code("""
    BIGQUERY_PROJECT_ID=seu-projeto
    BIGQUERY_DATASET=seu-dataset
    GOOGLE_APPLICATION_CREDENTIALS=caminho/para/credentials.json
    """)
    st.stop()

# Title and description
st.title("📊 Dashboard WBR - Análise de Fluxo")
st.markdown("---")

# Sidebar with filters only (no BigQuery configuration)
with st.sidebar:
    st.header("🎯 Filtros")
    
    # Date reference for calculations
    data_ref = st.date_input(
        "📅 Data de Referência",
        value=datetime.now(),
        help="Data base para cálculos de KPIs"
    )
    
    # Year filter
    filtro_ano = st.selectbox(
        "📆 Ano",
        options=[None] + list(range(2020, 2026)),
        format_func=lambda x: "Todos os anos" if x is None else str(x)
    )
    
    # Shopping filter (optional - will be populated if column exists)
    shopping_col = os.getenv("WBR_SHOPPING_COL", "shopping")
    filtro_shopping = st.text_input(
        "🏢 Shopping (opcional)",
        placeholder="Digite o nome do shopping",
        help="Deixe vazio para ver todos"
    )
    
    st.markdown("---")
    st.header("📐 Layout")
    
    # Layout selector
    layout_opcao = st.radio(
        "Disposição dos gráficos:",
        options=["Lado a lado", "Um abaixo do outro", "Abas"],
        help="Escolha como visualizar os gráficos"
    )
    
    st.markdown("---")
    st.caption(f"🔗 Conectado a: {BQ_PROJECT}.{BQ_DATASET}")

# Cache function for loading data
@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def load_table_data(config: dict, project: str, dataset: str):
    """Load data from BigQuery for a specific table configuration"""
    try:
        df = bq_client.fetch_wbr_data(
            project_id=project,
            dataset=dataset,
            table=config['table'],
            date_col=config['date_col'],
            metric_col=config['metric_col'],
            shopping_col=shopping_col if filtro_shopping else None
        )
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {config['titulo']}: {str(e)}")
        return None

def apply_filters(df: pd.DataFrame, year_filter=None, shopping_filter=None):
    """Apply filters to dataframe"""
    if df is None or df.empty:
        return df
    
    # Apply year filter
    if year_filter:
        df = df[df['date'].dt.year == year_filter]
    
    # Apply shopping filter
    if shopping_filter and 'shopping' in df.columns:
        df = df[df['shopping'].str.contains(shopping_filter, case=False, na=False)]
    
    return df

def render_metrics(df: pd.DataFrame, titulo: str):
    """Render KPI metrics for a dataframe"""
    if df is None or df.empty:
        st.warning(f"Sem dados para calcular KPIs de {titulo}")
        return
    
    try:
        kpis = calcular_kpis(df, data_referencia=data_ref)
        
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
            data_referencia=data_ref
        )
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{config['table']}")
        
        # Display metrics below chart
        render_metrics(df, config['titulo'])
        
        # Optional: Show data preview
        with st.expander("📋 Ver dados brutos"):
            st.dataframe(
                df[['date', 'metric_value']].tail(30),
                use_container_width=True,
                hide_index=True
            )
    
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

# Load data for both tables
with st.spinner("Carregando dados..."):
    df_pessoas = load_table_data(TABLES_CONFIG['pessoas'], BQ_PROJECT, BQ_DATASET)
    df_veiculos = load_table_data(TABLES_CONFIG['veiculos'], BQ_PROJECT, BQ_DATASET)
    
    # Apply filters
    df_pessoas_filtered = apply_filters(df_pessoas, filtro_ano, filtro_shopping) if df_pessoas is not None else None
    df_veiculos_filtered = apply_filters(df_veiculos, filtro_ano, filtro_shopping) if df_veiculos is not None else None

# Render based on selected layout
if layout_opcao == "Lado a lado":
    # Two columns layout
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.subheader(f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}")
        if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
            st.info(f"📊 {len(df_pessoas_filtered):,} registros")
            render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
        else:
            st.warning("Nenhum dado de pessoas encontrado")
    
    with col2:
        st.subheader(f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}")
        if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
            st.info(f"📊 {len(df_veiculos_filtered):,} registros")
            render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
        else:
            st.warning("Nenhum dado de veículos encontrado")

elif layout_opcao == "Um abaixo do outro":
    # Vertical layout
    st.subheader(f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}")
    if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
        st.info(f"📊 {len(df_pessoas_filtered):,} registros")
        render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
    else:
        st.warning("Nenhum dado de pessoas encontrado")
    
    st.markdown("---")
    
    st.subheader(f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}")
    if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
        st.info(f"📊 {len(df_veiculos_filtered):,} registros")
        render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
    else:
        st.warning("Nenhum dado de veículos encontrado")

else:  # Abas
    # Tabs layout
    tab_pessoas, tab_veiculos = st.tabs([
        f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}",
        f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}"
    ])
    
    with tab_pessoas:
        if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
            st.info(f"📊 {len(df_pessoas_filtered):,} registros")
            render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
        else:
            st.warning("Nenhum dado de pessoas encontrado")
    
    with tab_veiculos:
        if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
            st.info(f"📊 {len(df_veiculos_filtered):,} registros")
            render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
        else:
            st.warning("Nenhum dado de veículos encontrado")

# Footer
st.markdown("---")
st.caption("💡 Dica: Use os filtros na barra lateral para refinar a análise")