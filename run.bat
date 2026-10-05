@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo === AI Agents Thumbnails - SNES Retro ===
echo.

if not exist ".venv" (
    echo [1/3] Criando ambiente virtual...
    python -m venv .venv || goto :erro
)
call ".venv\Scripts\activate.bat"

echo [2/3] Instalando dependencias...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt || goto :erro

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo Arquivo .env criado. Coloque sua OPENAI_API_KEY nele e rode de novo.
    notepad ".env"
    goto :fim
)

echo.
set "QUERY=%~1"
if "%QUERY%"=="" set /p "QUERY=Tema do video (ENTER = Os 5 melhores jogos de SNES): "

echo.
echo [3/3] Rodando os agentes...
python main.py "%QUERY%" || goto :erro
goto :sair

:erro
echo.
echo Algo deu errado. Veja as mensagens acima.

:fim
pause

:sair
endlocal
