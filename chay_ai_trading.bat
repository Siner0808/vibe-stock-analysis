@echo off
chcp 65001 > nul
echo ========================================================================
echo               ANTIGRAVITY AI TRADING ENGINE (VON 1 TY VND)
echo ========================================================================
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
.venv\Scripts\python.exe ai_trading_engine.py
echo.
echo Da xuat bao cao tai: daily_trading_report.md
echo Da cap nhat so lenh tai: order_book.csv
echo.
pause
