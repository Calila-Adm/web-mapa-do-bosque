# 🚀 Rodando Ngrok + Streamlit no Docker

Este setup permite expor seu localhost através do Ngrok, tudo rodando dentro do Docker!

## 📋 Como Funciona

1. **Docker** roda sua aplicação Streamlit
2. **Ngrok** (dentro do mesmo container) expõe para internet
3. Você recebe uma URL pública acessível de qualquer lugar

## 🔧 Configuração Rápida

### 1️⃣ Adicione seu token do Ngrok ao `.env`:
```bash
NGROK_AUTH_TOKEN=2hxXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 2️⃣ Execute o script PowerShell:
```powershell
.\run-ngrok-docker.ps1
```

Ou manualmente:

### 3️⃣ Comandos Manuais (se preferir):
```bash
# Definir token
set NGROK_AUTH_TOKEN=seu_token_aqui

# Construir imagem
docker build -f Dockerfile.ngrok -t wbr-ngrok .

# Rodar
docker-compose -f docker-compose-ngrok.yml up
```

## 🌐 Acessando a Aplicação

Após iniciar, você terá:

1. **URL Pública Ngrok**: `https://xxxxx.ngrok-free.app`
   - Acessível de qualquer lugar do mundo
   - Muda a cada reinicialização (conta grátis)

2. **Dashboard Ngrok**: `http://localhost:4040`
   - Monitor de requisições
   - Estatísticas de uso

3. **Local** (opcional): `http://localhost:8501`
   - Acesso direto local

## 📝 Ver a URL Pública

```powershell
# Ver logs e encontrar URL
docker logs wbr-streamlit-ngrok

# Ou monitorar em tempo real
docker logs -f wbr-streamlit-ngrok
```

Procure por uma linha como:
```
Forwarding https://abc123.ngrok-free.app -> http://localhost:8501
```

## 🛠️ Comandos Úteis

```powershell
# Parar
docker-compose -f docker-compose-ngrok.yml down

# Reiniciar
docker-compose -f docker-compose-ngrok.yml restart

# Ver logs
docker logs -f wbr-streamlit-ngrok

# Entrar no container
docker exec -it wbr-streamlit-ngrok bash

# Limpar tudo
docker-compose -f docker-compose-ngrok.yml down -v
```

## ⚙️ Personalização

### Mudar região do Ngrok
No `Dockerfile.ngrok`, adicione ao comando ngrok:
```bash
ngrok http 8501 --region=sa  # sa = South America
```

Regiões disponíveis: `us`, `eu`, `ap`, `au`, `sa`, `jp`, `in`

### Adicionar autenticação básica
```bash
ngrok http 8501 --basic-auth="usuario:senha"
```

### Domínio customizado (conta paga)
```bash
ngrok http 8501 --domain=meu-app.ngrok.app
```

## 🔍 Troubleshooting

### Container não inicia
```powershell
# Ver logs detalhados
docker logs wbr-streamlit-ngrok

# Verificar se o token está correto
echo $env:NGROK_AUTH_TOKEN
```

### Ngrok não conecta
- Verifique se o token está correto
- Confirme que não há firewall bloqueando
- Tente outra região

### URL não aparece nos logs
```powershell
# Espere mais um pouco e tente
Start-Sleep -Seconds 10
docker logs wbr-streamlit-ngrok | Select-String "https://"
```

## 🎯 Vantagens desta Abordagem

✅ **Tudo em um container** - Fácil de gerenciar
✅ **Portável** - Funciona em qualquer máquina com Docker
✅ **Isolado** - Não afeta seu sistema
✅ **Reproduzível** - Sempre funciona da mesma forma
✅ **Versionado** - Pode fazer rollback facilmente

## 🚨 Importante

- A URL muda a cada restart (conta grátis)
- Limite de 40 conexões/minuto (conta grátis)
- Sessão expira após 2 horas de inatividade
- Visitantes verão página de aviso do Ngrok