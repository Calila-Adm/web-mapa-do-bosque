#!/bin/bash
# Script para corrigir conflito de rede entre Docker e rede 172.17.x.x
# Este script remove a rota conflitante e ajusta o IP da interface docker0

# Remove a rota conflitante da rede 172.17.0.0/16 (se existir)
sudo ip route del 172.17.0.0/16 2>/dev/null

# Remove o IP antigo da interface docker0 (se existir)
sudo ip addr del 172.17.0.1/16 dev docker0 2>/dev/null

# Adiciona o novo IP configurado no daemon.json do Docker Desktop
sudo ip addr add 10.10.0.1/16 dev docker0 2>/dev/null

# Adiciona rota para garantir acesso ao IP específico
sudo ip route add 172.17.2.11/32 via 172.25.144.1 2>/dev/null

# Mensagem silenciosa de sucesso (comentada por padrão)
# echo "Rotas Docker corrigidas com sucesso"