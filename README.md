# WBR Dashboard - Mapa do Bosque

Dashboard modular para análise de métricas WBR (Working Backwards Reporting) com integração Supabase/PostgreSQL. O sistema apresenta dados através de gráficos interativos e indicadores-chave de desempenho (KPIs) para análise de fluxo de pessoas, veículos, vendas e métricas do Instagram.

## Estrutura do Projeto

```
.
├── src/
│   ├── main.py                       # Aplicação principal Streamlit
│   ├── auth.py                       # Sistema de autenticação
│   ├── clients/
│   │   ├── database/
│   │   │   ├── factory.py           # Factory para criação de clientes DB
│   │   │   ├── supabase_postgres.py # Cliente Supabase/PostgreSQL
│   │   │   └── postgresql.py        # Cliente PostgreSQL genérico
│   │   └── sql/
│   │       ├── instagram_queries.py # Queries para dados do Instagram
│   │       └── queries.sql          # Queries SQL gerais
│   ├── config/
│   │   ├── database.py              # Configurações de banco de dados
│   │   └── settings.py              # Configurações gerais da aplicação
│   ├── core/
│   │   ├── wbr.py                   # Lógica principal WBR
│   │   ├── wbr_metrics.py           # Cálculos de métricas WBR
│   │   ├── wbr_utility.py           # Utilitários para WBR
│   │   ├── processing.py            # Processamento de dados
│   │   └── charts.py                # Geração de gráficos Plotly
│   ├── services/
│   │   ├── data_service.py          # Serviço de acesso a dados
│   │   └── metrics_service.py       # Serviço de cálculo de métricas
│   ├── ui/
│   │   ├── login.py                 # Página de login
│   │   ├── pages/
│   │   │   ├── __init__.py         # Exporta páginas disponíveis
│   │   │   ├── dashboard.py        # Página principal do dashboard
│   │   │   └── instagram.py        # Página de métricas do Instagram
│   │   └── components/
│   │       ├── sidebar.py          # Componente da barra lateral
│   │       ├── charts.py           # Componente de gráficos
│   │       ├── metrics.py          # Componente de métricas/KPIs
│   │       └── data_preview.py     # Componente de preview de dados
│   └── utils/
│       ├── env.py                   # Carregamento de variáveis ambiente
│       └── logging.py               # Configuração de logging
├── scripts/
│   ├── sync_td_to_supabase.sh      # Script de sincronização TD→Supabase
│   └── check_database.py            # Script de verificação do banco
├── config/
│   └── wbr_config.yaml             # Configurações WBR em YAML
├── .secrets/
│   └── .env                        # Variáveis de ambiente sensíveis
├── .streamlit/
│   └── config.toml                 # Configuração do Streamlit
├── pyproject.toml                  # Dependências do projeto (uv/pip)
├── uv.lock                         # Lock file do uv
├── requirements.txt                # Dependências Python
├── Dockerfile                      # Imagem Docker da aplicação
├── docker-compose.yml              # Orquestração com ngrok
└── README.md                       # Esta documentação
```

## Instruções de Configuração

### Pré-requisitos
- Python 3.10 ou superior
- Conta Supabase com banco PostgreSQL configurado
- Credenciais de acesso ao banco de dados

### Opção 1: Usando uv (Recomendado - Mais rápido)

1. **Clone o Repositório**
   ```bash
   git clone <repository-url>
   cd web-mapa-do-bosque
   ```

2. **Instalar uv** (se ainda não tiver)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Instalar Dependências com uv**
   ```bash
   uv sync
   ```

4. **Configurar Variáveis de Ambiente**
   - Copie `.env.example` para `.secrets/.env`
   - Configure as seguintes variáveis principais:
     - `SUPABASE_DATABASE_URL`: URL de conexão do Supabase
     - `SUPABASE_SCHEMA_MAPA`: Schema principal (default: mapa_do_bosque)
     - `SUPABASE_METRIC_COL`: Nome da coluna de métrica (default: value)
     - Credenciais de autenticação do dashboard

5. **Executar a Aplicação**
   ```bash
   uv run streamlit run src/main.py
   ```

### Opção 2: Usando pip tradicional

1. **Clone o Repositório**
   ```bash
   git clone <repository-url>
   cd web-mapa-do-bosque
   ```

2. **Criar Ambiente Virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows use `venv\Scripts\activate`
   ```

3. **Instalar Dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variáveis de Ambiente**
   - Copie `.env.example` para `.secrets/.env`
   - Configure as variáveis conforme descrito na Opção 1

5. **Executar a Aplicação**
   ```bash
   streamlit run src/main.py
   ```


## Deploy com Docker + ngrok

O projeto inclui suporte completo para Docker com exposição pública via ngrok.

### Configuração Docker

1. **Preparar Variáveis de Ambiente**
   ```bash
   cp .env.example .secrets/.env
   ```
   Configure em `.secrets/.env`:
   - `SUPABASE_DATABASE_URL`: URL de conexão do Supabase
   - `NGROK_AUTHTOKEN`: Token do ngrok (para exposição pública)

2. **Build e Execução**
   ```bash
   docker-compose up --build
   ```

3. **Acessar a Aplicação**
   - Local: http://localhost:8501
   - Público (ngrok): http://localhost:4040 (interface do ngrok)
   - A URL pública será exibida na interface do ngrok

## Uso do Sistema

### Funcionalidades Principais

1. **Dashboard Principal**
   - Visualização de fluxo de pessoas
   - Análise de fluxo de veículos
   - Métricas de vendas
   - Gráficos WBR com comparações YoY, WoW, MTD, QTD, YTD

2. **Métricas do Instagram**
   - Engajamento total (likes, comentários, compartilhamentos)
   - Alcance e impressões
   - Análise por shopping (SCIB, SBGP, SBI)
   - Tendências temporais

3. **Filtros Disponíveis**
   - Por período (data inicial e final)
   - Por shopping específico
   - Por ano de comparação

### Sincronização de Dados

Para sincronizar dados de um banco PostgreSQL local para o Supabase:

```bash
sh scripts/sync_td_to_supabase.sh
```

**Configuração necessária em `.secrets/.env`:**
- Origem: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Destino: `SUPABASE_DATABASE_URL`

**Tabelas sincronizadas** (configuráveis no script):
- `mapa_do_bosque.fluxo_de_pessoas`
- `mapa_do_bosque.fluxo_de_veiculos`
- `mapa_do_bosque.vendas_gshop`

## Testes

Para executar os testes:
```bash
pytest tests/
```

## Tecnologias Utilizadas

- **Frontend**: Streamlit
- **Visualização**: Plotly
- **Banco de Dados**: Supabase/PostgreSQL
- **Processamento**: Pandas, NumPy
- **Autenticação**: Sistema customizado com tokens
- **Deploy**: Docker, ngrok

## Contribuições

Contribuições são bem-vindas! Por favor, abra uma issue ou envie um pull request para melhorias ou correções.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para detalhes.