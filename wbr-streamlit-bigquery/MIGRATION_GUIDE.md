# Guia de Migração: BigQuery → PostgreSQL

Este guia explica como alternar entre BigQuery e PostgreSQL no dashboard WBR.

## 📋 Status Atual

- ✅ Suporte para PostgreSQL implementado
- ✅ BigQuery mantido (comentado)
- ✅ Factory pattern para fácil alternância entre bancos

## 🔄 Como Alternar Entre Bancos

### 1. Para usar PostgreSQL (configuração atual)

Edite seu arquivo `.env`:

```bash
# Define o tipo de banco
DB_TYPE=postgresql

# Configuração PostgreSQL - Opção 1: URL completa
DATABASE_URL=postgresql://usuario:senha@host:5432/banco

# OU Opção 2: Parâmetros individuais
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=seu_banco
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_SCHEMA=public
POSTGRES_TABLE=wbr_metrics
```

### 2. Para voltar ao BigQuery

Edite seu arquivo `.env`:

```bash
# Define o tipo de banco
DB_TYPE=bigquery

# Configuração BigQuery
BIGQUERY_PROJECT_ID=seu-projeto
BIGQUERY_DATASET=seu_dataset
BIGQUERY_TABLE=brief_fluxo_de_pessoas
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credentials.json
```

## 📦 Dependências

### PostgreSQL
```bash
pip install psycopg2-binary
```

### BigQuery (se quiser reativar)
```bash
pip install google-cloud-bigquery google-cloud-bigquery-storage db-dtypes
```

## 🗄️ Estrutura das Tabelas PostgreSQL

Crie suas tabelas no PostgreSQL com esta estrutura:

### Tabela: fluxo_pessoas
```sql
CREATE TABLE public.fluxo_pessoas (
    id SERIAL PRIMARY KEY,
    data_entrada DATE NOT NULL,
    quantidade INTEGER NOT NULL,
    shopping VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para melhor performance
CREATE INDEX idx_fluxo_pessoas_data ON public.fluxo_pessoas(data_entrada);
```

### Tabela: fluxo_veiculos
```sql
CREATE TABLE public.fluxo_veiculos (
    id SERIAL PRIMARY KEY,
    data_fluxo DATE NOT NULL,
    entradas INTEGER NOT NULL,
    shopping VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para melhor performance
CREATE INDEX idx_fluxo_veiculos_data ON public.fluxo_veiculos(data_fluxo);
```

## 🔍 Arquivos Modificados

1. **`src/data/postgresql_client.py`** - Novo cliente PostgreSQL
2. **`src/data/database_factory.py`** - Factory para escolher o banco
3. **`src/app/streamlit_app.py`** - Suporta ambos os bancos
4. **`requirements.txt`** - Dependências atualizadas
5. **`.env.example`** - Template com ambas configurações
6. **`src/data/queries/wbr_postgres.sql`** - Query SQL para PostgreSQL

## ⚙️ Configurações Avançadas

### Mapeamento de Colunas

Se suas tabelas têm nomes de colunas diferentes, configure no `.env`:

```bash
# Sobrescrever nomes de colunas
WBR_DATE_COL=data_customizada
WBR_METRIC_COL=valor_customizado
WBR_SHOPPING_COL=loja

# Para tabelas específicas no PostgreSQL
POSTGRES_TABLE_PESSOAS=minha_tabela_pessoas
POSTGRES_TABLE_VEICULOS=minha_tabela_veiculos
```

### SSL para PostgreSQL

Para conexões seguras:

```bash
POSTGRES_SSLMODE=require  # Opções: disable, allow, prefer, require
```

## 🚀 Executando

Após configurar o `.env`:

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar o dashboard
streamlit run src/app/streamlit_app.py
```

## 🔧 Troubleshooting

### Erro: "PostgreSQL credentials not found"
- Verifique se `DATABASE_URL` ou os parâmetros individuais estão configurados
- Confirme que `DB_TYPE=postgresql` está definido

### Erro: "psycopg2 not installed"
```bash
pip install psycopg2-binary
```

### Erro: "Table not found"
- Verifique `POSTGRES_SCHEMA` e `POSTGRES_TABLE`
- Confirme que as tabelas existem no banco

## 📝 Notas

- O código mantém compatibilidade com BigQuery
- Fácil alternância entre bancos via `.env`
- Caching do Streamlit funciona com ambos os bancos
- KPIs e gráficos são idênticos independente do banco