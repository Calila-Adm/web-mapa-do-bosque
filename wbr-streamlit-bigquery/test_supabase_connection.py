#!/usr/bin/env python3
"""
Script para testar conexão direta PostgreSQL com Supabase
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.env import load_environment_variables
from src.clients.database.supabase_postgres import SupabaseClient

def test_supabase_connection():
    """Testa a conexão e acesso aos dados"""

    print("=" * 60)
    print("TESTE DE CONEXÃO POSTGRESQL - SUPABASE")
    print("=" * 60)

    # Load environment variables
    load_environment_variables(base_dir=PROJECT_ROOT)

    # Verificar configuração
    db_url = os.getenv("SUPABASE_DATABASE_URL")
    if not db_url:
        print("\n❌ Erro: SUPABASE_DATABASE_URL não configurada!")
        print("Configure no .env:")
        print("SUPABASE_DATABASE_URL=postgresql://postgres.xxx:SENHA@aws-0-us-east-2.pooler.supabase.com:5432/postgres")
        return False

    # Ocultar senha ao exibir
    url_parts = db_url.split(":")
    if len(url_parts) >= 3:
        password_part = url_parts[2].split("@")[0] if "@" in url_parts[2] else ""
        if password_part:
            safe_url = db_url.replace(password_part, "****")
        else:
            safe_url = db_url[:50] + "..."
        print(f"\n✅ URL configurada: {safe_url}")

    # Schemas configurados
    schemas = {
        'SCIB': os.getenv("SUPABASE_SCHEMA_1", "instagram-data-fetch-scib"),
        'SBGP': os.getenv("SUPABASE_SCHEMA_2", "instagram-data-fetch-sbgp"),
        'SBI': os.getenv("SUPABASE_SCHEMA_3", "instagram-data-fetch-sbi")
    }

    print("\n📋 Schemas configurados:")
    for shop, schema in schemas.items():
        print(f"   {shop}: {schema}")

    try:
        # Inicializar cliente
        print("\n🔗 Conectando ao Supabase PostgreSQL...")
        client = SupabaseClient()

        # Teste 1: Conexão básica
        print("\n1️⃣ Testando conexão básica...")
        if client.test_connection():
            print("   ✅ Conexão estabelecida com sucesso!")
        else:
            print("   ❌ Falha na conexão")
            return False

        # Teste 2: Verificar schemas
        print("\n2️⃣ Verificando schemas disponíveis...")
        query = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'instagram%'
        ORDER BY schema_name;
        """

        result = client.query(query)
        if not result.empty:
            print("   ✅ Schemas encontrados:")
            for schema in result['schema_name'].tolist():
                print(f"      - {schema}")
        else:
            print("   ⚠️ Nenhum schema instagram-* encontrado")

        # Teste 3: Verificar tabelas em cada schema
        print("\n3️⃣ Verificando tabelas nos schemas...")
        for shop, schema in schemas.items():
            print(f"\n   Schema: {schema}")

            query = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
            ORDER BY table_name;
            """

            result = client.query(query)
            if not result.empty:
                tables = result['table_name'].tolist()
                print(f"   ✅ Tabelas encontradas ({len(tables)}):")
                for table in tables[:5]:  # Mostrar apenas as 5 primeiras
                    print(f"      - {table}")
                if len(tables) > 5:
                    print(f"      ... e mais {len(tables) - 5} tabelas")
            else:
                print("   ❌ Nenhuma tabela encontrada")

        # Teste 4: Buscar dados de engajamento
        print("\n4️⃣ Testando busca de dados de engajamento...")

        # Usar últimos 7 dias
        date_end = datetime.now().date()
        date_start = date_end - timedelta(days=7)

        df = client.get_engagement_data(
            date_start=str(date_start),
            date_end=str(date_end)
        )

        if not df.empty:
            print(f"   ✅ Dados encontrados: {len(df)} registros")
            print("\n   📊 Amostra dos dados:")
            print(df.head().to_string())

            # Estatísticas por shopping
            print("\n   📈 Estatísticas por shopping:")
            stats = df.groupby('shopping').agg({
                'engajamento_total': 'sum',
                'total_posts': 'sum'
            })
            print(stats.to_string())
        else:
            print("   ⚠️ Nenhum dado de engajamento encontrado")

        # Teste 5: Buscar contagem de posts
        print("\n5️⃣ Testando contagem de posts...")

        df = client.get_post_count_data(
            date_start=str(date_start),
            date_end=str(date_end)
        )

        if not df.empty:
            print(f"   ✅ Dados encontrados: {len(df)} registros")
            print("\n   📊 Posts por shopping:")
            stats = df.groupby('shopping')['value'].sum()
            for shop, count in stats.items():
                print(f"      {shop}: {count} posts")
        else:
            print("   ⚠️ Nenhum dado de posts encontrado")

        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("=" * 60)

        return True

    except ImportError:
        print("\n❌ Erro: Biblioteca SQLAlchemy não instalada!")
        print("Execute: pip install sqlalchemy psycopg2-binary")
        return False
    except Exception as e:
        print(f"\n❌ Erro durante teste: {str(e)}")
        import traceback
        print("\n📋 Stack trace:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)