import pandas as pd
import os
from typing import Optional, Tuple, List
from urllib.parse import urlparse, quote_plus
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine.url import make_url
import psycopg2
from psycopg2.extras import RealDictCursor


class PostgreSQLClient:
    def __init__(self):
        # Conexão lazy, similar ao BigQuery
        self.engine = None
        self.connection_string = None

    def authenticate(self):
        """Create SQLAlchemy engine for PostgreSQL (lazy)."""
        if self.engine is not None:
            return self.engine
        
        # Primeiro tenta DATABASE_URL (padrão Heroku/Railway)
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            # Converte postgres:// para postgresql:// (SQLAlchemy requer postgresql://)
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            try:
                # Usa make_url do SQLAlchemy para parsing robusto
                url = make_url(database_url)
                
                # Adiciona SSL mode se não estiver presente
                sslmode = os.getenv("POSTGRES_SSLMODE", "prefer")
                if 'sslmode' not in (url.query or {}):
                    url = url.update_query_dict({'sslmode': sslmode})
                
                self.connection_string = str(url)
                
            except Exception as e:
                # Fallback: tenta parsing manual para URLs problemáticas
                print(f"Warning: Error parsing DATABASE_URL with SQLAlchemy: {e}")
                print("Attempting manual parsing...")
                
                # Parse manual mais cuidadoso
                parsed = urlparse(database_url)
                
                # Extrai componentes com cuidado
                username = parsed.username or ""
                password = parsed.password or ""
                hostname = parsed.hostname or "localhost"
                port = parsed.port or 5432
                database = parsed.path.lstrip('/') if parsed.path else ""
                
                # Escapa caracteres especiais na senha
                if password:
                    password = quote_plus(password)
                if username:
                    username = quote_plus(username)
                
                sslmode = os.getenv("POSTGRES_SSLMODE", "prefer")
                
                # Reconstrói a URL com componentes escapados
                self.connection_string = (
                    f"postgresql://{username}:{password}@{hostname}:{port}/{database}?sslmode={sslmode}"
                )
                
                print(f"Debug: Reconstructed connection string (password hidden): "
                      f"postgresql://{username}:***@{hostname}:{port}/{database}?sslmode={sslmode}")
                
        else:
            # Tenta parâmetros individuais
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            database = os.getenv("POSTGRES_DATABASE")
            user = os.getenv("POSTGRES_USER")
            password = os.getenv("POSTGRES_PASSWORD")
            sslmode = os.getenv("POSTGRES_SSLMODE", "prefer")
            
            if not all([database, user]):
                raise ValueError(
                    "PostgreSQL credentials not found. Set DATABASE_URL or individual "
                    "POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD."
                )
            
            # Escapa caracteres especiais
            if password:
                password = quote_plus(password)
            if user:
                user = quote_plus(user)
            
            # Constrói a connection string para SQLAlchemy
            self.connection_string = (
                f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"
            )
        
        # Cria o engine SQLAlchemy
        try:
            self.engine = create_engine(self.connection_string, pool_pre_ping=True)
            # Testa a conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ PostgreSQL connection successful")
        except Exception as e:
            print(f"✗ PostgreSQL connection failed: {e}")
            raise
            
        return self.engine

    def run_query(self, query: str) -> pd.DataFrame:
        """Run a SQL query against PostgreSQL and return a pandas DataFrame."""
        engine = self.authenticate()
        
        # Usa pandas com SQLAlchemy engine (forma recomendada)
        df = pd.read_sql_query(query, engine)
        return df

    def fetch_wbr_data(self, *, schema: str | None = None, table: str | None = None,
                       date_col: str | None = None, metric_col: str | None = None, 
                       shopping_col: str | None = None) -> pd.DataFrame:
        """Fetch WBR data using SQL template and env/parameter variables.

        Uses POSTGRES_SCHEMA, POSTGRES_TABLE if args not provided.
        """
        # Sempre usa o arquivo wbr.sql genérico
        sql_path = os.path.join(os.path.dirname(__file__), 'queries', 'wbr.sql')
        
        with open(sql_path, 'r') as file:
            query = file.read()

        schema = schema or os.getenv('POSTGRES_SCHEMA', 'public')
        table = table or os.getenv('POSTGRES_TABLE')

        if not table:
            raise ValueError(
                "Missing PostgreSQL table. Set POSTGRES_TABLE in .env or pass table parameter."
            )

        # PostgreSQL usa schema.table
        qualified_table = f'"{schema}"."{table}"'
        
        # Colunas com defaults
        date_col = date_col or os.getenv('WBR_DATE_COL', 'date')
        metric_col = metric_col or os.getenv('WBR_METRIC_COL', 'metric_value')
        shopping_col = shopping_col or os.getenv('WBR_SHOPPING_COL', 'NULL')
        
        # Substituições específicas para PostgreSQL
        # 1. Referência da tabela
        query = query.replace('{{table_reference}}', qualified_table)
        
        # 2. Cast de data (PostgreSQL usa CAST ou ::date)
        date_cast = f"DATE({date_col})"
        query = query.replace('{{date_cast}}', date_cast)
        
        # 3. Coluna de métrica
        query = query.replace('{{metric_col}}', metric_col)
        
        # 4. Coluna de shopping
        query = query.replace('{{shopping_col}}', shopping_col)
        
        # 5. Filtro de data (PostgreSQL syntax)
        # Calcula o início do ano passado e data atual
        date_filter = f"""
        DATE({date_col}) BETWEEN 
            DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 year'
            AND CURRENT_DATE
        """
        query = query.replace('{{date_filter}}', date_filter)
        
        # Adiciona hint para usar índices se existirem
        # PostgreSQL usa comentários /*+ ... */ para hints (se pg_hint_plan estiver instalado)
        # Ou podemos adicionar um SET para forçar uso de índices
        optimized_query = f"""
        -- Force index usage if available
        SET enable_seqscan = OFF;
        
        {query}
        
        -- Reset to default
        SET enable_seqscan = ON;
        """
        
        # Por segurança, executa apenas a query principal (sem os SETs) se der erro
        try:
            return self.run_query(query)  # Usa query sem SETs por enquanto
        except Exception as e:
            # Se falhar, tenta sem otimizações
            raise e

    def list_tables(self, *, schema: str | None = None) -> List[str]:
        """List table names in a schema.
        
        When schema is omitted, read from env or use 'public'.
        """
        engine = self.authenticate()
        schema = schema or os.getenv('POSTGRES_SCHEMA', 'public')
        
        # Usa SQLAlchemy Inspector para listar tabelas
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema=schema)
        
        return tables

    def infer_wbr_columns(self, *, schema: str | None = None, 
                          table: str | None = None) -> Tuple[Optional[str], Optional[str]]:
        """Infer likely date and metric columns from a table schema.
        
        Returns (date_col, metric_col), any of which may be None if not inferred.
        """
        engine = self.authenticate()
        schema = schema or os.getenv('POSTGRES_SCHEMA', 'public')
        table = table or os.getenv('POSTGRES_TABLE')
        
        if not table:
            return (None, None)
        
        # Usa SQLAlchemy Inspector para obter metadados da tabela
        inspector = inspect(engine)
        try:
            columns = inspector.get_columns(table, schema=schema)
        except Exception:
            return (None, None)
        
        if not columns:
            return (None, None)
        
        # Candidatos para coluna de data
        date_candidates = {'date', 'data', 'dt', 'event_date', 'created_at', 
                          'timestamp', 'datetime', 'fecha', 'data_referencia', 'data_entrada', 'data_fluxo'}
        
        # Candidatos para coluna de métrica
        metric_candidates = {'metric', 'value', 'valor', 'quantidade', 'amount', 
                           'total', 'count', 'visits', 'volume', 'metric_value',
                           'fluxo', 'pessoas', 'veiculos', 'entradas'}
        
        date_col = None
        metric_col = None
        
        # Procura colunas de data e métrica
        for col in columns:
            col_name_lower = col['name'].lower()
            col_type = str(col['type']).lower()
            
            # Verifica se é uma coluna de data
            if not date_col:
                if 'date' in col_type or 'timestamp' in col_type:
                    if col_name_lower in date_candidates:
                        date_col = col['name']
                    elif not date_col:  # Fallback para qualquer coluna de data
                        date_col = col['name']
            
            # Verifica se é uma coluna numérica para métrica
            if not metric_col:
                if any(t in col_type for t in ['int', 'float', 'numeric', 'decimal', 'real', 'double']):
                    if col_name_lower in metric_candidates or \
                       any(hint in col_name_lower for hint in metric_candidates):
                        metric_col = col['name']
                    elif not metric_col:  # Fallback para qualquer coluna numérica
                        metric_col = col['name']
        
        return (date_col, metric_col)

    def close(self):
        """Dispose of the SQLAlchemy engine."""
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def __del__(self):
        """Ensure engine is disposed when object is destroyed."""
        self.close()