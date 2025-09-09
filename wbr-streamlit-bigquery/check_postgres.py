#!/usr/bin/env python3
"""
Script para verificar e descobrir automaticamente tabelas e colunas no PostgreSQL.
Execute este script para ver o que está disponível no seu banco.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.env import load_environment_variables
from src.data.postgresql_client import PostgreSQLClient

# Carrega variáveis de ambiente
load_environment_variables()

def main():
    print("=" * 60)
    print("🔍 VERIFICADOR DE ESTRUTURA POSTGRESQL")
    print("=" * 60)
    
    try:
        # Conecta ao PostgreSQL
        client = PostgreSQLClient()
        engine = client.authenticate()
        print("✅ Conexão estabelecida com sucesso!\n")
        
        # Define o schema
        schema = os.getenv("POSTGRES_SCHEMA", "mapa_do_bosque")
        print(f"📁 Schema configurado: {schema}\n")
        
        # Lista todas as tabelas no schema
        print(f"📋 Tabelas encontradas no schema '{schema}':")
        print("-" * 40)
        
        tables = client.list_tables(schema=schema)
        
        if not tables:
            print(f"⚠️  Nenhuma tabela encontrada no schema '{schema}'")
            print("\nVerificando outros schemas disponíveis...")
            
            # Lista todos os schemas
            query = """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
            """
            result = client.run_query(query)
            print("\n📂 Schemas disponíveis:")
            for idx, row in result.iterrows():
                schema_name = row['schema_name']
                print(f"  - {schema_name}")
                
                # Lista tabelas em cada schema
                tables_in_schema = client.list_tables(schema=schema_name)
                if tables_in_schema:
                    for table in tables_in_schema:
                        print(f"      └─ {table}")
        else:
            # Para cada tabela encontrada
            for table in tables:
                print(f"\n📊 Tabela: {table}")
                
                # Detecta colunas automaticamente
                date_col, metric_col = client.infer_wbr_columns(schema=schema, table=table)
                
                print(f"   ├─ Coluna de data detectada: {date_col or '❌ Não encontrada'}")
                print(f"   └─ Coluna de métrica detectada: {metric_col or '❌ Não encontrada'}")
                
                # Mostra estrutura completa da tabela
                query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = '{schema}' AND table_name = '{table}'
                ORDER BY ordinal_position;
                """
                columns_df = client.run_query(query)
                
                print(f"\n   📌 Estrutura completa:")
                for _, col in columns_df.iterrows():
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"      - {col['column_name']}: {col['data_type']} ({nullable})")
                
                # Conta registros
                try:
                    count_query = f'SELECT COUNT(*) as total FROM "{schema}"."{table}"'
                    count_result = client.run_query(count_query)
                    total = count_result['total'].iloc[0]
                    print(f"\n   📈 Total de registros: {total:,}")
                except Exception as e:
                    print(f"\n   ⚠️  Erro ao contar registros: {e}")
        
        print("\n" + "=" * 60)
        print("💡 CONFIGURAÇÃO RECOMENDADA PARA .env:")
        print("-" * 40)
        
        # Sugere configuração baseada no que foi encontrado
        if 'fluxo_de_pessoas' in tables:
            date_col_pessoas, metric_col_pessoas = client.infer_wbr_columns(schema=schema, table='fluxo_de_pessoas')
            print(f"POSTGRES_SCHEMA={schema}")
            print(f"POSTGRES_TABLE_PESSOAS=fluxo_de_pessoas")
            if date_col_pessoas:
                print(f"# Coluna de data detectada: {date_col_pessoas}")
            if metric_col_pessoas:
                print(f"# Coluna de métrica detectada: {metric_col_pessoas}")
        
        if 'fluxo_de_veiculos' in tables:
            date_col_veiculos, metric_col_veiculos = client.infer_wbr_columns(schema=schema, table='fluxo_de_veiculos')
            print(f"\nPOSTGRES_TABLE_VEICULOS=fluxo_de_veiculos")
            if date_col_veiculos:
                print(f"# Coluna de data detectada: {date_col_veiculos}")
            if metric_col_veiculos:
                print(f"# Coluna de métrica detectada: {metric_col_veiculos}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")
        print("\nVerifique suas configurações no arquivo .env:")
        print("  - DATABASE_URL ou")
        print("  - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())