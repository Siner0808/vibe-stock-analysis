@echo off
chcp 65001 > nul
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║   🤖 ANTIGRAVITY QUANT TRADING PIPELINE V3                  ║
echo ║   7 Tang Phan Tich -- 71 Ma -- 16 Nganh -- Von 1 Ty VND    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
.venv\Scripts\python.exe v3_pipeline\run_pipeline.py
echo.
echo Pipeline hoan tat. Kiem tra Telegram va daily_trading_report_v3.md
echo.
pause
