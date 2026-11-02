@echo off
setlocal
cd /d "%~dp0"

python -m PyInstaller --noconfirm --clean --onefile --windowed --name ControleFacas --add-data "controle_facas.db;." tela2.py
if errorlevel 1 (
    echo.
    echo Falha ao criar o executavel. Verifique a instalacao do Python e do PyInstaller.
    pause
    exit /b 1
)

echo.
echo Executavel criado em: "%~dp0dist\ControleFacas.exe"
echo O banco inicial foi incluido no executavel. Os dados serao mantidos em %%LOCALAPPDATA%%\ControleFacas.
pause
