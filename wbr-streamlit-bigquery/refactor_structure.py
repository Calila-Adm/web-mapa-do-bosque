#!/usr/bin/env python3
"""
Script de refatoração automática da estrutura do projeto.
Execute este script para reorganizar o projeto em uma estrutura modular.
"""

import os
import shutil
from pathlib import Path
import re

# Define o diretório base
BASE_DIR = Path(__file__).parent

def create_directories():
    """Cria a nova estrutura de diretórios"""
    print("📁 Criando nova estrutura de diretórios...")
    
    directories = [
        "src/clients",
        "src/clients/database",
        "src/clients/sql",
        "src/core",
        "src/ui",
        "src/config",
        "scripts",
        "docs",
        "tests/unit",
        "tests/integration",
    ]
    
    for dir_path in directories:
        path = BASE_DIR / dir_path
        path.mkdir(parents=True, exist_ok=True)
        
        # Adiciona __init__.py em diretórios Python
        if dir_path.startswith("src/") and not dir_path.endswith("sql"):
            init_file = path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Package initialization."""\n')
    
    print("✅ Estrutura de diretórios criada")

def move_files():
    """Move arquivos para suas novas localizações"""
    print("\n📦 Movendo arquivos...")
    
    moves = [
        # Clientes de banco de dados
        ("src/data/bigquery_client.py", "src/clients/database/bigquery.py"),
        ("src/data/postgresql_client.py", "src/clients/database/postgresql.py"),
        ("src/data/database_factory.py", "src/clients/database/factory.py"),
        ("src/data/queries/wbr.sql", "src/clients/sql/queries.sql"),
        
        # Core business logic
        ("src/wbr/core.py", "src/core/wbr.py"),
        ("src/wbr/processing.py", "src/core/processing.py"),
        ("src/wbr/kpis.py", "src/core/kpis.py"),
        ("src/wbr/charts.py", "src/core/charts.py"),
        
        # Scripts auxiliares
        ("check_postgres.py", "scripts/check_database.py"),
        
        # Documentação
        ("MIGRATION_GUIDE.md", "docs/MIGRATION_GUIDE.md"),
    ]
    
    for source, dest in moves:
        src_path = BASE_DIR / source
        dst_path = BASE_DIR / dest
        
        if src_path.exists():
            # Cria diretório de destino se não existir
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move o arquivo
            shutil.move(str(src_path), str(dst_path))
            print(f"  ✓ {source} → {dest}")
        else:
            print(f"  ⚠ {source} não encontrado")

def create_main_py():
    """Cria o novo main.py baseado no streamlit_app.py"""
    print("\n🎯 Criando main.py...")
    
    streamlit_app = BASE_DIR / "src/app/streamlit_app.py"
    main_py = BASE_DIR / "src/main.py"
    
    if streamlit_app.exists():
        content = streamlit_app.read_text()
        
        # Atualiza imports
        replacements = [
            (r'from src\.data\.database_factory import', 'from src.clients.database.factory import'),
            (r'from src\.wbr import', 'from src.core.wbr import'),
            (r'from src\.wbr\.kpis import', 'from src.core.kpis import'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Adiciona header
        header = '''#!/usr/bin/env python3
"""
WBR Dashboard - Main Application Entry Point
============================================
Dashboard principal para análise de métricas WBR (Working Backwards Reporting).
"""

'''
        content = header + content
        
        main_py.write_text(content)
        print("✅ main.py criado com sucesso")

def create_ui_components():
    """Separa componentes de UI do main.py"""
    print("\n🎨 Criando componentes de UI...")
    
    # Cria layouts.py
    layouts_content = '''"""
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
'''
    
    (BASE_DIR / "src/ui/layouts.py").write_text(layouts_content)
    
    # Cria components.py
    components_content = '''"""
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
'''
    
    (BASE_DIR / "src/ui/components.py").write_text(components_content)
    
    print("✅ Componentes de UI criados")

def create_config_files():
    """Cria arquivos de configuração centralizados"""
    print("\n⚙️ Criando arquivos de configuração...")
    
    # settings.py
    settings_content = '''"""
Configurações centralizadas do aplicativo.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Database Configuration
DB_CONFIG = {
    "type": os.getenv("DB_TYPE", "postgresql"),
    "postgres": {
        "schema": os.getenv("POSTGRES_SCHEMA", "mapa_do_bosque"),
        "tables": {
            "pessoas": os.getenv("POSTGRES_TABLE_PESSOAS", "fluxo_de_pessoas"),
            "veiculos": os.getenv("POSTGRES_TABLE_VEICULOS", "fluxo_de_veiculos"),
        }
    },
    "bigquery": {
        "project": os.getenv("BIGQUERY_PROJECT_ID"),
        "dataset": os.getenv("BIGQUERY_DATASET"),
    }
}

# Application Settings
APP_CONFIG = {
    "title": "WBR Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Chart Settings
CHART_CONFIG = {
    "height": 400,
    "template": "plotly_white",
    "colors": {
        "pessoas": "#1E90FF",
        "veiculos": "#FF6B6B",
    }
}
'''
    
    (BASE_DIR / "src/config/settings.py").write_text(settings_content)
    
    # constants.py
    constants_content = '''"""
Constantes e enumerações do aplicativo.
"""

from enum import Enum

class MetricType(Enum):
    """Tipos de métricas disponíveis."""
    PESSOAS = "pessoas"
    VEICULOS = "veiculos"

class TimeGranularity(Enum):
    """Granularidade temporal para agregações."""
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"
    QUARTERLY = "Q"
    YEARLY = "Y"

class KPIType(Enum):
    """Tipos de KPIs calculados."""
    YOY = "yoy"  # Year over Year
    WOW = "wow"  # Week over Week
    MTD = "mtd"  # Month to Date
    QTD = "qtd"  # Quarter to Date
    YTD = "ytd"  # Year to Date

# Table configurations
TABLES_CONFIG = {
    MetricType.PESSOAS: {
        'titulo': 'Fluxo de Pessoas',
        'unidade': 'pessoas',
        'icon': '👥',
        'color': '#1E90FF'
    },
    MetricType.VEICULOS: {
        'titulo': 'Fluxo de Veículos',
        'unidade': 'veículos',
        'icon': '🚗',
        'color': '#FF6B6B'
    }
}
'''
    
    (BASE_DIR / "src/config/constants.py").write_text(constants_content)
    
    print("✅ Arquivos de configuração criados")

def update_imports_in_files():
    """Atualiza imports em todos os arquivos Python"""
    print("\n🔄 Atualizando imports...")
    
    # Mapeamento de imports antigos para novos
    import_map = {
        'from src.data.bigquery_client': 'from src.clients.database.bigquery',
        'from src.data.postgresql_client': 'from src.clients.database.postgresql',
        'from src.data.database_factory': 'from src.clients.database.factory',
        'from src.wbr.core': 'from src.core.wbr',
        'from src.wbr.processing': 'from src.core.processing',
        'from src.wbr.kpis': 'from src.core.kpis',
        'from src.wbr.charts': 'from src.core.charts',
        'from src.wbr': 'from src.core.wbr',
    }
    
    # Atualiza imports em todos os arquivos .py
    for py_file in BASE_DIR.rglob("src/**/*.py"):
        if py_file.is_file():
            content = py_file.read_text()
            modified = False
            
            for old_import, new_import in import_map.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    modified = True
            
            if modified:
                py_file.write_text(content)
                print(f"  ✓ Atualizado: {py_file.relative_to(BASE_DIR)}")

def cleanup_old_structure():
    """Remove diretórios e arquivos antigos não utilizados"""
    print("\n🧹 Limpando estrutura antiga...")
    
    to_remove = [
        "src/app",  # Após mover streamlit_app.py
        "src/data",  # Após mover clientes
        "src/wbr",   # Após mover para core
        "notebooks",  # Não utilizado
    ]
    
    for path in to_remove:
        full_path = BASE_DIR / path
        if full_path.exists():
            if full_path.is_dir():
                shutil.rmtree(full_path)
                print(f"  ✓ Removido diretório: {path}")
            else:
                full_path.unlink()
                print(f"  ✓ Removido arquivo: {path}")

def create_pyproject_toml():
    """Cria pyproject.toml para configuração moderna Python"""
    print("\n📝 Criando pyproject.toml...")
    
    content = '''[tool.poetry]
name = "wbr-dashboard"
version = "2.0.0"
description = "Dashboard WBR com suporte para BigQuery e PostgreSQL"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.8"
streamlit = "^1.28.0"
pandas = "^2.0.0"
numpy = "^1.24.0"
plotly = "^5.0.0"
psycopg2-binary = "^2.9.0"
sqlalchemy = "^2.0.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
black = "^23.0.0"
flake8 = "^6.0.0"
mypy = "^1.0.0"

[tool.black]
line-length = 100
target-version = ['py38']

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''
    
    (BASE_DIR / "pyproject.toml").write_text(content)
    print("✅ pyproject.toml criado")

def main():
    """Executa a refatoração completa"""
    print("🚀 INICIANDO REFATORAÇÃO DA ESTRUTURA DO PROJETO")
    print("=" * 50)
    
    # Confirma com o usuário
    response = input("\n⚠️  Este script irá reorganizar toda a estrutura do projeto.\n"
                    "   Certifique-se de ter um backup ou commit atual.\n"
                    "   Deseja continuar? (s/N): ")
    
    if response.lower() != 's':
        print("\n❌ Refatoração cancelada.")
        return
    
    print("\n" + "=" * 50)
    
    # Executa as etapas
    create_directories()
    move_files()
    create_main_py()
    create_ui_components()
    create_config_files()
    update_imports_in_files()
    cleanup_old_structure()
    create_pyproject_toml()
    
    print("\n" + "=" * 50)
    print("✨ REFATORAÇÃO CONCLUÍDA COM SUCESSO!")
    print("\n📋 Próximos passos:")
    print("  1. Revise as mudanças com: git status")
    print("  2. Teste a aplicação: streamlit run src/main.py")
    print("  3. Atualize o Makefile se necessário")
    print("  4. Commit das mudanças: git add -A && git commit -m 'refactor: reorganize project structure'")
    print("\n💡 Dica: Use 'make run' após atualizar o Makefile")

if __name__ == "__main__":
    main()