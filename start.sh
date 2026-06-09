#!/usr/bin/env bash
# NeuroVision — Local development start script
set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║         NeuroVision — Start          ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Check .env ──────────────────────────────────────────────────────────────
if [ ! -f "./backend/.env" ]; then
  echo "⚠  backend/.env not found."
  echo "   Copy backend/.env.example → backend/.env and set GROQ_API_KEY"
  exit 1
fi

# ── Backend ─────────────────────────────────────────────────────────────────
echo "▶  Starting backend (FastAPI)..."
cd backend

if [ ! -d ".venv" ]; then
  echo "   Creating Python virtual environment..."
  python -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate

pip install -q -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

cd ..

# ── Frontend ─────────────────────────────────────────────────────────────────
echo "▶  Starting frontend (Next.js)..."
cd frontend

if [ ! -d "node_modules" ]; then
  echo "   Installing npm packages..."
  npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

cd ..

echo ""
echo "✓  NeuroVision is running:"
echo "   Frontend → http://localhost:3000"
echo "   Backend  → http://localhost:8000"
echo "   API Docs → http://localhost:8000/docs"
echo ""
echo "   Press Ctrl+C to stop"

# Wait for both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
