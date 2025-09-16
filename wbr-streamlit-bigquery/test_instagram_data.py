#!/usr/bin/env python3
"""
Script para testar o acesso aos dados do Instagram no Supabase
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.env import load_environment_variables
from supabase import create_client, Client

def test_instagram_data_access():
    """Testa o acesso direto às tabelas do Instagram"""

    print("=" * 60)
    print("TESTE DE ACESSO AOS DADOS DO INSTAGRAM")
    print("=" * 60)

    # Load environment variables
    load_environment_variables(base_dir=PROJECT_ROOT)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("\n❌ Erro: Credenciais do Supabase não configuradas!")
        return False

    print(f"\n✅ Credenciais encontradas")

    # Initialize Supabase client
    client: Client = create_client(supabase_url, supabase_key)
    print("✅ Cliente Supabase inicializado")

    # Test schemas
    schemas = {
        'SCIB': os.getenv("SUPABASE_SCHEMA_1", "instagram-data-fetch-scib"),
        'SBGP': os.getenv("SUPABASE_SCHEMA_2", "instagram-data-fetch-sbgp"),
        'SBI': os.getenv("SUPABASE_SCHEMA_3", "instagram-data-fetch-sbi")
    }

    print(f"\n📁 Testando acesso aos schemas:")
    for shopping, schema in schemas.items():
        print(f"\n  {shopping} (schema: {schema}):")

        # Test Post table
        try:
            table_name = f'{schema}.Post'
            print(f"    Testando {table_name}...")

            response = client.table(table_name).select("*").limit(1).execute()

            if response.data:
                print(f"    ✅ Tabela Post acessível - {len(response.data)} registro(s)")
            else:
                print(f"    ⚠️ Tabela Post vazia")

        except Exception as e:
            error_msg = str(e)
            if "relation" in error_msg and "does not exist" in error_msg:
                print(f"    ❌ Tabela Post não existe")
            elif "permission" in error_msg:
                print(f"    ❌ Sem permissão para acessar Post")
            else:
                print(f"    ❌ Erro: {error_msg[:100]}")

        # Test PostInsight table
        try:
            table_name = f'{schema}.PostInsight'
            print(f"    Testando {table_name}...")

            response = client.table(table_name).select("*").limit(1).execute()

            if response.data:
                print(f"    ✅ Tabela PostInsight acessível - {len(response.data)} registro(s)")
            else:
                print(f"    ⚠️ Tabela PostInsight vazia")

        except Exception as e:
            error_msg = str(e)
            if "relation" in error_msg and "does not exist" in error_msg:
                print(f"    ❌ Tabela PostInsight não existe")
            elif "permission" in error_msg:
                print(f"    ❌ Sem permissão para acessar PostInsight")
            else:
                print(f"    ❌ Erro: {error_msg[:100]}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_instagram_data_access()