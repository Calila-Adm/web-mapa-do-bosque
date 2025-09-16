#!/usr/bin/env python3
"""
Script para descobrir o que está disponível na API do Supabase
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

def discover_api():
    """Descobre o que está disponível na API"""

    print("=" * 60)
    print("DESCOBERTA DA API SUPABASE")
    print("=" * 60)

    # Load environment variables
    load_environment_variables(base_dir=PROJECT_ROOT)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("\n❌ Erro: Credenciais não configuradas!")
        return False

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Accept": "application/json"
    }

    print(f"\n📍 URL Base: {supabase_url}")

    # Teste 1: Verificar OpenAPI spec
    print("\n🔍 Buscando especificação OpenAPI...")
    try:
        # O Supabase expõe a spec em /rest/v1/
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers)

        if response.status_code == 200:
            print("✅ API REST acessível")

            # Tentar pegar o swagger/openapi
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                if 'paths' in data:
                    print("\n📋 Endpoints disponíveis:")
                    paths = list(data['paths'].keys())
                    for path in paths[:10]:  # Mostrar primeiros 10
                        print(f"   - {path}")
                    if len(paths) > 10:
                        print(f"   ... e mais {len(paths) - 10} endpoints")
            elif response.headers.get('content-type', '').startswith('application/openapi+json'):
                print("✅ OpenAPI spec disponível")
        else:
            print(f"⚠️ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {str(e)[:100]}")

    # Teste 2: Tentar listar tables/functions disponíveis
    print("\n🔍 Tentando descobrir recursos disponíveis...")

    # Tentar alguns endpoints comuns
    test_endpoints = [
        "/rest/v1/",
        "/rest/v1/rpc/",
        "/rest/v1/rpc/test_instagram_access",  # Se você criou a função RPC
        "/rest/v1/Post",
        "/rest/v1/public.Post",
    ]

    for endpoint in test_endpoints:
        url = f"{supabase_url}{endpoint}"
        print(f"\n   Testando: {endpoint}")

        try:
            response = requests.get(url, headers=headers)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ Endpoint disponível!")
                # Verificar se retorna dados
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 Retornou {len(data)} registros")
                    elif isinstance(data, dict):
                        print(f"   📊 Retornou objeto com chaves: {list(data.keys())[:5]}")
                except:
                    pass
            elif response.status_code == 404:
                print("   ❌ Não encontrado")
            elif response.status_code == 401:
                print("   ❌ Não autorizado")

        except Exception as e:
            print(f"   ❌ Erro: {str(e)[:50]}")

    # Teste 3: Verificar se RPC functions estão disponíveis
    print("\n🔍 Verificando funções RPC...")
    rpc_url = f"{supabase_url}/rest/v1/rpc/"

    try:
        response = requests.get(rpc_url, headers=headers)
        if response.status_code != 404:
            print("✅ Endpoint RPC disponível")
            print("   Você pode criar funções SQL e chamá-las via /rest/v1/rpc/nome_funcao")
        else:
            print("⚠️ Endpoint RPC não encontrado")
    except:
        pass

    print("\n" + "=" * 60)
    print("DESCOBERTA CONCLUÍDA")
    print("=" * 60)

    print("\n💡 RECOMENDAÇÃO:")
    print("Como as tabelas nos schemas customizados não estão acessíveis,")
    print("você deve criar VIEWS ou FUNCTIONS no schema 'public'.")
    print("\nExecute no SQL Editor do Supabase:")
    print("""
-- Opção 1: Criar uma VIEW
CREATE OR REPLACE VIEW public.instagram_posts_all AS
SELECT
    'SCIB' as shopping,
    p.*,
    i.likes,
    i.comments,
    i.shares,
    i.saves
FROM "instagram-data-fetch-scib"."Post" p
LEFT JOIN "instagram-data-fetch-scib"."PostInsight" i ON p.id = i."postId"
UNION ALL
SELECT
    'SBGP' as shopping,
    p.*,
    i.likes,
    i.comments,
    i.shares,
    i.saves
FROM "instagram-data-fetch-sbgp"."Post" p
LEFT JOIN "instagram-data-fetch-sbgp"."PostInsight" i ON p.id = i."postId"
UNION ALL
SELECT
    'SBI' as shopping,
    p.*,
    i.likes,
    i.comments,
    i.shares,
    i.saves
FROM "instagram-data-fetch-sbi"."Post" p
LEFT JOIN "instagram-data-fetch-sbi"."PostInsight" i ON p.id = i."postId";
    """)

    return True

if __name__ == "__main__":
    discover_api()