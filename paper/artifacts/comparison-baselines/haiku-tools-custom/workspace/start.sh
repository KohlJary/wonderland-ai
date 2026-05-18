#!/bin/bash
# Quick start script for Markdown Notebook

set -e

echo "🚀 Starting Markdown Notebook..."
echo ""

# Check if .venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "✓ Using Python virtual environment"
source .venv/bin/activate

# Install/update dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📚 Installing Python dependencies..."
    pip install -q fastapi uvicorn sqlalchemy pydantic
fi

# Check Node dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "📚 Installing Node.js dependencies..."
    cd frontend && npm install -q && cd ..
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Starting services..."
echo ""
echo "Run these commands in separate terminals:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    source .venv/bin/activate"
echo "    python src/backend/main.py"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "Then open http://localhost:5173 in your browser!"
echo ""
