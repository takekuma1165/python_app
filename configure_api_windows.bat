@echo off
setlocal
cd /d "%~dp0"
if exist ".env" goto edit
if not exist ".env.example" goto missing
copy ".env.example" ".env" >nul
if errorlevel 1 goto failed
:edit
echo Edit OPENAI_API_KEY in Notepad. Never share the key in chat.
echo Save the file, then restart the app to apply the settings.
start "" /wait notepad.exe ".env"
exit /b 0
:missing
echo .env.example was not found. Extract the entire ZIP folder first.
pause
exit /b 1
:failed
echo Cannot create .env. Check folder permissions.
pause
exit /b 1
