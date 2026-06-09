@echo off
echo.
echo ╔══════════════════════════════════════╗
echo ║         NeuroVision — Start          ║
echo ╚══════════════════════════════════════╝
echo.

REM Check .env
if not exist "backend\.env" (
    echo [ERRO] backend\.env nao encontrado.
    echo Copie backend\.env.example para backend\.env e defina GROQ_API_KEY
    pause
    exit /b 1
)

REM Backend
echo [1/2] Iniciando backend FastAPI...
cd backend

if not exist ".venv" (
    echo Criando ambiente virtual Python...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
start "NeuroVision Backend" cmd /k "call .venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

cd ..

REM Frontend
echo [2/2] Iniciando frontend Next.js...
cd frontend

if not exist "node_modules" (
    echo Instalando dependencias npm...
    npm install
)

start "NeuroVision Frontend" cmd /k "npm run dev"
cd ..

echo.
echo Aguarde alguns segundos e acesse:
echo   Frontend  ^>  http://localhost:3000
echo   Backend   ^>  http://localhost:8000
echo   API Docs  ^>  http://localhost:8000/docs
echo.
pause
