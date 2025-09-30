#!/bin/bash

# NewsLens Lint Script
# This script checks code style and quality

set -e

echo "🔍 Running NewsLens Lint Checks"
echo "==============================="

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

# Backend Linting
echo "🔧 Linting Backend..."
cd backend

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Python linting
print_status "Checking Python code style..."

# Check if flake8 is installed
if command -v flake8 &> /dev/null; then
    flake8 app/ --max-line-length=100 --ignore=E203,W503
    print_status "Python linting completed"
else
    print_warning "flake8 not installed. Install with: pip install flake8"
fi

# Check if black is installed
if command -v black &> /dev/null; then
    print_status "Checking code formatting with black..."
    black --check app/
    print_status "Code formatting check completed"
else
    print_warning "black not installed. Install with: pip install black"
fi

cd ..

# Frontend Linting
echo "🎨 Linting Frontend..."
cd frontend/vite-project

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "Node modules not found. Installing dependencies..."
    npm install
fi

# ESLint
print_status "Checking JavaScript/TypeScript code style..."
if npx eslint --version &> /dev/null; then
    npx eslint src/ --ext .ts,.tsx,.js,.jsx
    print_status "ESLint check completed"
else
    print_warning "ESLint not found. Install with: npm install -g eslint"
fi

# Prettier
print_status "Checking code formatting with Prettier..."
if npx prettier --version &> /dev/null; then
    npx prettier --check src/
    print_status "Prettier formatting check completed"
else
    print_warning "Prettier not found. Install with: npm install -g prettier"
fi

cd ../..

# Summary
echo ""
echo "📊 Lint Summary"
echo "==============="
print_status "Backend linting completed"
print_status "Frontend linting completed"

echo ""
echo "🎉 All lint checks completed!"
echo ""
echo "To fix formatting issues:"
echo "1. Backend: black app/"
echo "2. Frontend: npx prettier --write src/"
