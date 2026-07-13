@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoLogo -NoProfile -WindowStyle Hidden -File "%SCRIPT_DIR%Start-TalentAdvisor.ps1"
exit /b %ERRORLEVEL%
