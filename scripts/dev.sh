#!/bin/bash

# Development server script for PDF tools platform

echo "🚀 Starting development servers..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./scripts/setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f "api/.env" ]; then
    echo "❌ Environment file not found. Copy api/.env.example to api/.env and configure it."
    exit 1
fi

# Start the Flask API server
echo "🔥 Starting Flask API server on port 5000..."
cd api
export FLASK_ENV=development
export FLASK_APP=app.py
python app.py &
API_PID=$!
cd ..

# Start a simple HTTP server for frontend files
echo "🌐 Starting frontend servers..."

# Start SnackPDF frontend on port 3000
echo "🍿 Starting SnackPDF frontend on port 3000..."
cd snackpdf
python3 -m http.server 3000 &
SNACK_PID=$!
cd ..

# Start RevisePDF frontend on port 3001
echo "✏️ Starting RevisePDF frontend on port 3001..."
cd revisepdf
python3 -m http.server 3001 &
REVISE_PID=$!
cd ..

echo ""
echo "✅ Development servers started!"
echo ""
echo "📍 Available endpoints:"
echo "  • API Server:      http://localhost:5000"
echo "  • SnackPDF:        http://localhost:3000"
echo "  • RevisePDF:       http://localhost:3001"
echo ""
echo "📋 API endpoints:"
echo "  • Health check:    http://localhost:5000/health"
echo "  • Debug info:      http://localhost:5000/api/debug/info"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $API_PID 2>/dev/null
    kill $SNACK_PID 2>/dev/null
    kill $REVISE_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for any process to exit
wait