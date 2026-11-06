@echo off
rem Doble clic para hablar con Viernes.
cd /d "%~dp0"
where claude >nul 2>nul
if errorlevel 1 (
  echo Falta instalar Claude Code. Guia: https://code.claude.com/docs/en/setup
  pause
  exit /b 1
)
claude
