@echo off
rem dev.cmd - launcher for dev.ps1
rem Windows PowerShell blocks downloaded .ps1 by default (execution policy), so
rem this starts it with RemoteSigned: local scripts run, downloaded ones still
rem must be signed. System settings are not changed.
rem Usage: dev.cmd lint / test / run / compile / distribute
setlocal
powershell -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0dev.ps1" %*
exit /b %ERRORLEVEL%
