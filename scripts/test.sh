#!/bin/bash

# NewsLens Test Script
# This script runs all tests for the project

set -e

echo "🧪 Running NewsLens Tests"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Backend Tests
echo "🔧 Testing Backend..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run Python tests if they exist
if [ -d "tests" ]; then
    print_status "Running Python tests..."
    python -m pytest tests/ -v
else
    print_warning "No tests directory found. Creating basic test structure..."
    mkdir -p tests
    cat > tests/test_basic.py << EOF
import pytest
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from app.main import app
        from app.bias_analyzer import BiasAnalyzer
        from app.news_fetcher import fetch_articles
        from app.summarization_service import SummarizationService
        from app.article_clustering import ArticleClusterer
        from app.tldr_service import TLDRService
        print("✅ All modules imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")

def test_bias_analyzer():
    """Test bias analyzer initialization"""
    try:
        analyzer = BiasAnalyzer()
        assert analyzer is not None
        print("✅ Bias analyzer initialized successfully")
    except Exception as e:
        pytest.fail(f"Bias analyzer initialization failed: {e}")

if __name__ == "__main__":
    test_imports()
    test_bias_analyzer()
    print("✅ All basic tests passed!")
EOF
    python tests/test_basic.py
fi

cd ..

# Frontend Tests
echo "🎨 Testing Frontend..."
cd frontend/vite-project

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "Node modules not found. Installing dependencies..."
    npm install
fi

# Build test
print_status "Testing frontend build..."
npm run build

cd ../..

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
print_status "Backend tests completed"
print_status "Frontend tests completed"

echo ""
echo "🎉 All tests completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start the backend: cd backend && uvicorn app.main:app --reload"
echo "2. Start the frontend: cd frontend/vite-project && npm run dev"
echo "3. Visit http://localhost:5173 to see the application"