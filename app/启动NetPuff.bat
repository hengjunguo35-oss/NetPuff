@echo off
chcp 65001 >nul
title NetPuff
cd /d "%~dp0"

where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw ..\src\netpuff.py
  exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
  start "" python ..\src\netpuff.py
  exit /b 0
)

echo.
echo 未检测到 Python，请先安装：https://www.python.org/downloads/
echo 安装时务必勾选 "Add python.exe to PATH"。
echo.
pause
