#!/bin/bash

# Script para sincronizar dados do TD para Supabase
# Uso:
#   sh scripts/sync_td_to_supabase.sh                    # Usa valores do .env
#   sh scripts/sync_td_to_supabase.sh <host> <port> <user> <connection_string>  # Usa parâmetros

# Tabelas a sincronizar
TABLES=(
    "mapa_do_bosque.fluxo_de_pessoas"
    "mapa_do_bosque.fluxo_de_veiculos"
    "mapa_do_bosque.vendas_gshop"
)

# Função para carregar arquivo .env
load_env() {
    # Determina o diretório raiz do projeto (um nível acima de scripts/)
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    ENV_FILE="$PROJECT_ROOT/.env"

    if [ -f "$ENV_FILE" ]; then
        echo "📋 Carregando configurações do .env..."
        # Carrega variáveis do .env de forma segura
        set -a  # Auto-export variáveis
        source "$ENV_FILE"
        set +a  # Desativa auto-export
        return 0
    else
        echo "🔍 Procurando .env em: $ENV_FILE"
        return 1
    fi
}

# Se não foram passados parâmetros, tenta usar .env
if [ $# -eq 0 ]; then
    # Carregar .env
    load_env
    if [ $? -ne 0 ]; then
        echo "❌ Erro: Arquivo .env não encontrado"
        echo ""
        echo "Crie um arquivo .env com as variáveis:"
        echo "  POSTGRES_HOST=host_do_banco_td"
        echo "  POSTGRES_PORT=5432"
        echo "  POSTGRES_DATABASE=nome_do_banco"
        echo "  POSTGRES_USER=usuario_td"
        echo "  POSTGRES_PASSWORD=senha_td  # (opcional)"
        echo "  SUPABASE_DATABASE_URL=postgresql://..."
        exit 1
    fi

    # Usar valores do .env - TD usa as mesmas variáveis POSTGRES_*
    TD_HOST="${POSTGRES_HOST}"
    TD_PORT="${POSTGRES_PORT:-5432}"
    TD_USER="${POSTGRES_USER}"
    TD_PASSWORD="${POSTGRES_PASSWORD}"
    TD_DATABASE="${POSTGRES_DATABASE:-TD}"  # Usa TD como padrão se não especificado
    SUPABASE_CONN="${SUPABASE_DATABASE_URL}"

    # Verificar se as variáveis essenciais existem
    if [ -z "$TD_HOST" ] || [ -z "$TD_USER" ] || [ -z "$SUPABASE_CONN" ]; then
        echo "❌ Erro: Variáveis obrigatórias não encontradas no .env"
        echo ""
        echo "Adicione ao seu .env:"
        echo "  POSTGRES_HOST=ip_do_banco_td"
        echo "  POSTGRES_USER=usuario_td"
        echo "  SUPABASE_DATABASE_URL=postgresql://..."
        echo ""
        echo "Ou execute com parâmetros:"
        echo "  $0 <host> <port> <user> <supabase_connection_string>"
        exit 1
    fi

    echo "✅ Usando configurações do .env"
    echo "   TD: $TD_USER@$TD_HOST:$TD_PORT (banco: $TD_DATABASE)"

elif [ $# -eq 4 ]; then
    # Usar parâmetros passados
    TD_HOST="$1"
    TD_PORT="$2"
    TD_USER="$3"
    SUPABASE_CONN="$4"
    TD_DATABASE="TD"  # Padrão quando usando parâmetros
    echo "✅ Usando parâmetros fornecidos"

else
    echo "❌ Erro: Número incorreto de parâmetros"
    echo ""
    echo "Uso:"
    echo "  $0                    # Usa valores do .env"
    echo "  $0 <host> <port> <user> <supabase_connection_string>  # Usa parâmetros"
    echo ""
    echo "Exemplo com parâmetros:"
    echo "  $0 192.168.1.100 5432 admin 'postgresql://user:pass@host:port/db'"
    exit 1
fi

# Criar diretório de dumps se não existir
echo "📁 Criando diretório dumps..."
mkdir -p dumps

# Fazer dump do banco TD
echo "📥 Fazendo dump do banco TD..."
echo "   Host: $TD_HOST:$TD_PORT"
echo "   User: $TD_USER"
echo "   Tabelas: ${#TABLES[@]} tabelas"

# Se tiver senha no .env, exporta para o pg_dump usar
if [ ! -z "$TD_PASSWORD" ]; then
    export PGPASSWORD="$TD_PASSWORD"
fi

# Construir argumentos -t para cada tabela
TABLE_ARGS=""
for table in "${TABLES[@]}"; do
    TABLE_ARGS="$TABLE_ARGS -t $table"
done

pg_dump -h "$TD_HOST" -p "$TD_PORT" -U "$TD_USER" -d "$TD_DATABASE" \
    $TABLE_ARGS \
    --no-owner --no-privileges \
    --clean --if-exists \
    -F p > ./dumps/db.sql

# Limpar variável de senha
unset PGPASSWORD

if [ $? -eq 0 ]; then
    echo "✅ Dump criado com sucesso: ./dumps/db.sql"
else
    echo "❌ Erro ao criar dump"
    exit 1
fi

# Importar para Supabase (o dump já contém comandos de limpeza)
echo "📤 Importando para Supabase..."
psql "$SUPABASE_CONN" -f ./dumps/db.sql

if [ $? -eq 0 ]; then
    echo "✅ Dados sincronizados com sucesso!"
else
    echo "❌ Erro ao importar para Supabase"
    exit 1
fi

echo "🎉 Sincronização concluída!"
