@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto check_python
py -3 --version >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto python_error
:check_python
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 goto python_error
fc /b "requirements.txt" ".venv\miyabi-requirements.txt" >nul 2>&1
if not errorlevel 1 goto launch
 echo Installing required packages. Please wait...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto install_error
copy /y "requirements.txt" ".venv\miyabi-requirements.txt" >nul
:launch
echo Starting Miyabi Writing Studio...
echo Keep this window open while using the app. Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
if errorlevel 1 goto launch_error
exit /b 0
:python_error
echo Python 3.11 or newer is required. Install Python 3.12 from python.org.
echo Select "Add python.exe to PATH", then try again.
pause
exit /b 1
:install_error
echo Installation failed. Check your internet connection and the message above.
pause
exit /b 1
:launch_error
echo Startup failed. Please keep the error message above for troubleshooting.
pause
exit /b 1
