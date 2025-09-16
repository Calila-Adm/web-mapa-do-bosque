#!/usr/bin/env python3
"""
Teste direto da API REST do Supabase
"""

import os
import sys
import requests
import json

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.env import load_environment_variables

def test_direct_api():
    """Testa acesso direto via API REST"""

    print("=" * 60)
    print("TESTE DIRETO DA API REST")
    print("=" * 60)

    # Load environment variables
    load_environment_variables(base_dir=PROJECT_ROOT)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("\n❌ Erro: Credenciais não configuradas!")
        return False

    # Headers para a API REST
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    print(f"\n✅ URL: {supabase_url[:30]}...")

    # Tentar acessar as tabelas diretamente via REST
    tables_to_test = [
        "Post",
        "PostInsight",
        "instagram-data-fetch-scib.Post",
        "instagram-data-fetch-sbgp.Post",
        "instagram-data-fetch-sbi.Post"
    ]

    for table in tables_to_test:
        print(f"\n📋 Testando: {table}")
        url = f"{supabase_url}/rest/v1/{table}"

        try:
            # Tentar fazer uma query com limit
            params = {"select": "*", "limit": "1"}
            response = requests.get(url, headers=headers, params=params)

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Sucesso! Registros retornados: {len(data)}")
                if data:
                    print(f"   Campos disponíveis: {list(data[0].keys())[:5]}...")
            elif response.status_code == 404:
                print(f"   ❌ Tabela não encontrada na API REST")
            elif response.status_code == 401:
                print(f"   ❌ Não autorizado")
            else:
                print(f"   ❌ Erro: {response.text[:100]}")

        except Exception as e:
            print(f"   ❌ Erro na requisição: {str(e)[:100]}")

    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    test_direct_api()