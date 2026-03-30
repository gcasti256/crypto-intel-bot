#!/bin/bash
# Crypto Intel Bot — One-Click Deployment
# Usage: curl -sSL https://raw.githubusercontent.com/gcasti256/crypto-intel-bot/main/deploy.sh | bash

set -euo pipefail

REPO="https://github.com/gcasti256/crypto-intel-bot.git"
INSTALL_DIR="/opt/crypto-intel-bot"

echo "==========================================="
echo "  Crypto Intel Bot — Deployment"
echo "==========================================="
echo ""

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[1/4] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "[1/4] Docker already installed"
fi

# Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null 2>&1; then
    echo "[2/4] Installing Docker Compose plugin..."
    apt-get update -qq && apt-get install -y -qq docker-compose-plugin
else
    echo "[2/4] Docker Compose already installed"
fi

# Clone or update repo
if [ ! -d "$INSTALL_DIR" ]; then
    echo "[3/4] Cloning repository..."
    git clone "$REPO" "$INSTALL_DIR"
else
    echo "[3/4] Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main
fi

cd "$INSTALL_DIR"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "==========================================="
    echo "  Configuration Required"
    echo "==========================================="
    echo ""
    echo "  Edit $INSTALL_DIR/.env with your credentials:"
    echo ""
    echo "    DISCORD_TOKEN=your-discord-bot-token    (required)"
    echo "    GROQ_API_KEY=your-groq-api-key          (optional, for AI)"
    echo "    DOMAIN=your-domain.com                  (for HTTPS)"
    echo ""
    echo "  Then run:"
    echo "    cd $INSTALL_DIR"
    echo "    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
    echo ""
    exit 0
fi

# Start services
echo "[4/4] Starting services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo ""
echo "==========================================="
echo "  Crypto Intel Bot is running!"
echo "==========================================="
echo ""
echo "  Dashboard: https://${DOMAIN:-localhost}"
echo "  Logs:      docker compose logs -f"
echo "  Stop:      docker compose down"
echo ""
