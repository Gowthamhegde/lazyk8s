@echo off
setlocal

echo ⎈  Installing lazyk8s...

:: Check python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌  Python not found. Install from https://python.org/downloads
    echo     Make sure to check "Add Python to PATH" during install.
    pause & exit /b 1
)

:: Check kubectl
kubectl version --client >nul 2>&1
if errorlevel 1 (
    echo ❌  kubectl not found. Install from https://kubernetes.io/docs/tasks/tools/
    pause & exit /b 1
)

:: Install textual
echo 📦  Installing dependencies...
pip install textual --quiet

:: Download lazyk8s
set INSTALL_DIR=%USERPROFILE%\.local\bin
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

curl -fsSL https://raw.githubusercontent.com/Gowthamhegde/lazyk8s/main/lazyk8s -o "%INSTALL_DIR%\lazyk8s.py"

:: Create wrapper batch file so user can just type lazyk8s
echo @python "%INSTALL_DIR%\lazyk8s.py" %%* > "%INSTALL_DIR%\lazyk8s.bat"

:: Add to PATH if needed
echo %PATH% | find /i "%INSTALL_DIR%" >nul
if errorlevel 1 (
    setx PATH "%PATH%;%INSTALL_DIR%"
    echo    ➜  Added %INSTALL_DIR% to PATH — restart your terminal.
)

echo.
echo ✅  Done! Run: lazyk8s
pause
