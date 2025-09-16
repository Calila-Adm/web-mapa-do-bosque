#!/usr/bin/env python3
"""
Script para listar as tabelas disponíveis no Supabase
"""

import os
import sys
import requests

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.env import load_environment_variables

def list_supabase_tables():
    """Lista as tabelas disponíveis via API REST do Supabase"""

    print("=" * 60)
    print("LISTANDO TABELAS DO SUPABASE")
    print("=" * 60)

    # Load environment variables
    load_environment_variables(base_dir=PROJECT_ROOT)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("\n❌ Erro: Credenciais do Supabase não configuradas!")
        return False

    print(f"\n✅ URL: {supabase_url[:30]}...")

    # Use the REST API to query the schema information
    # Supabase exposes the OpenAPI spec
    api_url = f"{supabase_url}/rest/v1/"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }

    try:
        # Get the OpenAPI spec which lists all available endpoints/tables
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            print("\n✅ Conectado ao Supabase REST API")
            print("\n📋 Endpoints disponíveis:")

            # Try to get a simple endpoint to see what's available
            # Let's try to get the root to see available tables
            print("\nPara listar as tabelas disponíveis, você pode:")
            print("1. Acessar o Supabase Dashboard")
            print("2. Verificar a documentação da API em: " + supabase_url + "/rest/v1/")
            print("3. Usar o SQL Editor no Dashboard do Supabase com:")
            print("""
   SELECT schemaname, tablename
   FROM pg_tables
   WHERE schemaname IN ('instagram-data-fetch-scib',
                        'instagram-data-fetch-sbgp',
                        'instagram-data-fetch-sbi')
   ORDER BY schemaname, tablename;
            """)

        else:
            print(f"\n❌ Erro ao conectar: Status {response.status_code}")

    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")

    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    list_supabase_tables()