#!/bin/bash
# Synapse Docker Setup Script
# Usage: ./docker-setup.sh

set -e

echo "================================"
echo "Synapse Docker Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✓ Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it from https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker Compose is installed"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

echo "✓ Docker daemon is running"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please update .env with your API keys if needed:"
    echo "   - GEMINI_API_KEY (optional, get from https://makersuite.google.com/app/apikey)"
    echo "   - DEEPGRAM_API_KEY (optional)"
    echo "   - SUPABASE_URL and SUPABASE_KEY (optional)"
    echo ""
else
    echo "✓ .env file already exists"
fi

echo "🚀 Building Docker images..."
docker-compose build

echo ""
echo "✓ Docker images built successfully"
echo ""

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✓ Services started"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Synapse is ready!"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend:        http://localhost:3000"
echo "   Backend API:     http://localhost:8000"
echo "   API Docs:        http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "   View logs:       docker-compose logs -f"
echo "   Stop services:   docker-compose down"
echo "   Restart:         docker-compose restart"
echo "   Backend shell:   docker-compose exec backend bash"
echo "   Frontend shell:  docker-compose exec frontend bash"
echo ""
echo "📖 For more help, see DOCKER_SETUP.md"
