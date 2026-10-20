@echo off
rem Install the NAS542 root CA into the machine-wide Trusted Root store.
rem RIGHT-CLICK this file -> "Run as administrator".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-ca-machine.ps1"
echo.
pause
