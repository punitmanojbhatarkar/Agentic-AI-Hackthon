#!/bin/bash
# SupplySense Quick Start Script
# Starts both backend API server and frontend dev server

echo "🚀 SupplySense Quick Start"
echo "========================="
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check if Node/npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js"
    exit 1
fi

echo "✅ Python and Node.js found"
echo ""

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install flask flask-cors -q

# Start backend in background
echo "🔧 Starting backend API server (http://localhost:5000)..."
python backend/api.py &
BACKEND_PID=$!
sleep 2

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install -q
    cd ..
fi

# Start frontend
echo "⚡ Starting frontend dev server (http://localhost:3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✨ SupplySense is running!"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" SIGINT
wait
