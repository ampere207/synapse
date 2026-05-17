#!/bin/bash

# Synapse Quick Start Script
# Run this script to set up and start Synapse

set -e

echo "🚀 Synapse - Quick Start Setup"
echo "================================"
echo ""

# Check Docker installation
echo "✓ Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✓ Docker installed: $(docker --version)"

# Check Docker Compose installation
echo "✓ Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it."
    exit 1
fi
echo "✓ Docker Compose installed: $(docker-compose --version)"

# Check if .env exists
echo "✓ Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  - Created .env file from .env.example"
    echo "  ⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY"
else
    echo "  - .env file already exists"
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Run this script from the synapse root directory."
    exit 1
fi

echo ""
echo "✓ All prerequisites met!"
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Add your GEMINI_API_KEY"
echo "3. Run: docker-compose up"
echo ""
echo "Services will be available at:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
