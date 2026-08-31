@echo off
chcp 65001 > nul
echo ╔══════════════════════════════════════════════════════════════╗
echo ║   🤖 ANTIGRAVITY TELEGRAM BOT INTERACTIVE LISTENER          ║
echo ║   Lang nghe tin nhan & Tuong tac 2 chieu tren Telegram      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
.venv\Scripts\python.exe telegram_bot_interactive.py
pause
