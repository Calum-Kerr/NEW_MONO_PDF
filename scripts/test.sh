#!/bin/bash

# Test script for PDF tools platform

echo "🧪 Running tests for PDF tools platform..."

# Check if we're in the right directory
if [ ! -f "Procfile" ]; then
    echo "❌ Error: Procfile not found. Make sure you're in the project root directory."
    exit 1
fi

# Function to test API endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local expected_status=${3:-200}
    
    echo "🔍 Testing $method $endpoint..."
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "http://localhost:5000$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -X "$method" "http://localhost:5000$endpoint" \
                  -H "Content-Type: application/json" \
                  -d '{"test": "data"}')
    fi
    
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo "✅ $endpoint - Status: $status_code"
        return 0
    else
        echo "❌ $endpoint - Expected: $expected_status, Got: $status_code"
        return 1
    fi
}

# Start test API server
echo "🚀 Starting test API server..."
cd api
FLASK_ENV=development python test_app.py &
API_PID=$!
cd ..

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Test API endpoints
echo "🔗 Testing API endpoints..."
failed_tests=0

test_endpoint "/health" "GET" "200" || ((failed_tests++))
test_endpoint "/api/debug/info" "GET" "200" || ((failed_tests++))
test_endpoint "/api/auth/login" "POST" "200" || ((failed_tests++))
test_endpoint "/api/auth/register" "POST" "200" || ((failed_tests++))

# Test frontend servers
echo "🌐 Testing frontend servers..."

# Start SnackPDF frontend
cd snackpdf
python3 -m http.server 3000 &
SNACK_PID=$!
cd ..

# Start RevisePDF frontend
cd revisepdf
python3 -m http.server 3001 &
REVISE_PID=$!
cd ..

# Wait for servers to start
sleep 2

# Test frontend availability
echo "🔍 Testing frontend availability..."

snack_status=$(curl -s -w "%{http_code}" http://localhost:3000 | tail -3c)
if [ "$snack_status" = "200" ]; then
    echo "✅ SnackPDF frontend - Status: 200"
else
    echo "❌ SnackPDF frontend - Status: $snack_status"
    ((failed_tests++))
fi

revise_status=$(curl -s -w "%{http_code}" http://localhost:3001 | tail -3c)
if [ "$revise_status" = "200" ]; then
    echo "✅ RevisePDF frontend - Status: 200"
else
    echo "❌ RevisePDF frontend - Status: $revise_status"
    ((failed_tests++))
fi

# Test file structure
echo "📁 Testing file structure..."

required_files=(
    "api/app.py"
    "api/test_app.py"
    "api/requirements.txt"
    "core/auth.py"
    "core/payments.py"
    "core/files.py"
    "core/utils.py"
    "supabase/schema.sql"
    "snackpdf/index.html"
    "snackpdf/css/style.css"
    "snackpdf/js/app.js"
    "revisepdf/index.html"
    "revisepdf/css/editor.css"
    "scripts/setup.sh"
    "scripts/deploy.sh"
    "scripts/dev.sh"
    "Procfile"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        ((failed_tests++))
    fi
done

# Cleanup
echo "🧹 Cleaning up test servers..."
kill $API_PID 2>/dev/null
kill $SNACK_PID 2>/dev/null
kill $REVISE_PID 2>/dev/null

# Results
echo ""
if [ $failed_tests -eq 0 ]; then
    echo "🎉 All tests passed! The platform is ready for deployment."
    exit 0
else
    echo "❌ $failed_tests test(s) failed. Please check the issues above."
    exit 1
fi