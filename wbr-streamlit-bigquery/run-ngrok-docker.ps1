# Script para rodar Streamlit + Ngrok no Docker (Windows)

Write-Host "🚀 Iniciando Streamlit + Ngrok no Docker" -ForegroundColor Green

# Verificar se o token do Ngrok está configurado
$token = $env:NGROK_AUTH_TOKEN
if (-not $token) {
    $token = Read-Host "Digite seu NGROK_AUTH_TOKEN"
    if (-not $token) {
        Write-Host "❌ Token do Ngrok é obrigatório!" -ForegroundColor Red
        Write-Host "Obtenha em: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Yellow
        exit 1
    }
}

# Salvar token temporariamente
$env:NGROK_AUTH_TOKEN = $token

Write-Host "🔨 Construindo imagem Docker..." -ForegroundColor Yellow
docker build -f Dockerfile.ngrok -t wbr-ngrok .

Write-Host "📦 Iniciando container..." -ForegroundColor Yellow
docker-compose -f docker-compose-ngrok.yml up -d

Write-Host "" -ForegroundColor Green
Write-Host "✅ Container iniciado com sucesso!" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "🌐 URLs de Acesso:" -ForegroundColor Cyan
Write-Host "   - Ngrok Dashboard: http://localhost:4040" -ForegroundColor White
Write-Host "   - Local Streamlit: http://localhost:8501" -ForegroundColor White
Write-Host "" -ForegroundColor Green

# Aguardar um pouco para o Ngrok iniciar
Start-Sleep -Seconds 5

# Mostrar logs para ver a URL pública do Ngrok
Write-Host "📋 URL Pública do Ngrok:" -ForegroundColor Yellow
$ngrokUrl = docker logs wbr-streamlit-ngrok 2>&1 | Select-String "url=https" | Select-Object -Last 1
if ($ngrokUrl) {
    $url = ($ngrokUrl -split "url=")[1]
    Write-Host "🌐 Acesse sua aplicação em: $url" -ForegroundColor Green
} else {
    Write-Host "⏳ Aguardando URL... Execute: docker logs wbr-streamlit-ngrok" -ForegroundColor Yellow
}

Write-Host "" -ForegroundColor Green
Write-Host "💡 Comandos úteis:" -ForegroundColor Yellow
Write-Host "   Ver logs:    docker logs -f wbr-streamlit-ngrok" -ForegroundColor Gray
Write-Host "   Parar:       docker-compose -f docker-compose-ngrok.yml down" -ForegroundColor Gray
Write-Host "   Reiniciar:   docker-compose -f docker-compose-ngrok.yml restart" -ForegroundColor Gray