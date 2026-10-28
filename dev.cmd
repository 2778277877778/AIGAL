@echo off
rem dev.cmd - launcher for dev.ps1
rem Windows PowerShell blocks .ps1 by default (execution policy), so this
rem starts it with -ExecutionPolicy Bypass. System settings are not changed.
rem Usage: dev.cmd lint / test / run / compile / distribute
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dev.ps1" %*
exit /b %ERRORLEVEL%
