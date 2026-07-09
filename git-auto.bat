@echo off
REM Simple Git automation script for the Bot de Investimentos project
REM Usage: git-auto.bat "Commit message"

REM Check if commit message provided
if "%~1"=="" (
    echo Usage: %~nx0 "Commit message"
    echo Example: %~nx0 "Add data collection script"
    exit /b 1
)

REM Git commands
git add .
git commit -m "%~1"
git push origin main

echo Changes committed and pushed successfully!