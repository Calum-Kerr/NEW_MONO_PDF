#!/bin/bash

# Development setup script for PDF tools platform

echo "🔧 Setting up PDF tools development environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "📚 Installing backend dependencies..."
cd api
pip install -r requirements.txt
cd ..

# Create environment file if it doesn't exist
if [ ! -f "api/.env" ]; then
    echo "⚙️ Creating environment file..."
    cp api/.env.example api/.env
    echo "Please edit api/.env with your configuration values"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p temp

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit api/.env with your configuration"
echo "2. Set up your Supabase project and run the schema.sql"
echo "3. Configure your Stripe account and get API keys"
echo "4. Run the development server: ./scripts/dev.sh"
echo ""
echo "For production deployment, use: ./scripts/deploy.sh"