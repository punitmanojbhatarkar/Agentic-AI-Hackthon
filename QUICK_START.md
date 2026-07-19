#!/usr/bin/env bash
# SUPPLYSENSE QUICK START GUIDE
# Get the full system running in < 5 minutes

echo "🚀 SupplySense Quick Start"
echo "========================="
echo ""

# Step 1: Backend Dependencies
echo "Step 1: Installing backend dependencies..."
pip install flask flask-cors -q 2>/dev/null || pip install flask flask-cors
echo "✅ Backend ready"
echo ""

# Step 2: Start Backend
echo "Step 2: Starting backend API (http://localhost:5000)..."
python backend/api.py &
BACKEND_PID=$!
echo "✅ Backend running (PID: $BACKEND_PID)"
sleep 2
echo ""

# Step 3: Frontend Dependencies
echo "Step 3: Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install -q
fi
echo "✅ Frontend dependencies installed"
echo ""

# Step 4: Start Frontend
echo "Step 4: Starting frontend (http://localhost:3000)..."
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend running (PID: $FRONTEND_PID)"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ SupplySense is LIVE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Frontend:  http://localhost:3000"
echo "🔧 Backend:   http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Trap Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT
wait
