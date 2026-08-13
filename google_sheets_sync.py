"""
google_sheets_sync.py
──────────────────────────────────────────────────────────────────────
Đồng bộ Sổ Lệnh Giấy và Quyết định Agent lên Google Sheets.
Giúp duy trì dữ liệu bền vững khi triển khai ứng dụng trên Streamlit Cloud.
"""

import os
import streamlit as st
import pandas as pd

def is_google_sheets_enabled() -> bool:
    """Kiểm tra xem Google Sheets Secrets đã được cấu hình đầy đủ hay chưa."""
    try:
        if "GOOGLE_SHEET_KEY" in st.secrets and st.secrets["GOOGLE_SHEET_KEY"]:
            if "gcp_service_account" in st.secrets:
                sa = st.secrets["gcp_service_account"]
                if sa.get("client_email") and sa.get("private_key"):
                    return True
    except Exception:
        pass
    return False

def get_gspread_client():
    """Khởi tạo gspread client sử dụng gcp_service_account từ st.secrets."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    sa_dict = dict(st.secrets["gcp_service_account"])
    
    # Xử lý xuống dòng private_key nếu bị escaped
    if "private_key" in sa_dict and isinstance(sa_dict["private_key"], str):
        sa_dict["private_key"] = sa_dict["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(sa_dict, scopes=scopes)
    return gspread.authorize(creds)

def sync_trades_to_google_sheets(trades_list: list) -> bool:
    """
    Đồng bộ danh sách lệnh (Trade objects) lên tab `trades` trên Google Sheets.
    """
    if not is_google_sheets_enabled():
        return False

    try:
        gc = get_gspread_client()
        sheet_key = st.secrets["GOOGLE_SHEET_KEY"]
        sh = gc.open_by_key(sheet_key)

        try:
            ws = sh.worksheet("trades")
        except Exception:
            ws = sh.add_worksheet(title="trades", rows=1000, cols=20)

        headers = [
            "id", "symbol", "signal_date", "entry_date", "entry_price",
            "stop_loss", "take_profit", "exit_date", "exit_price",
            "position_size_pct", "components", "reasons", "status", "created_at"
        ]

        rows = [headers]
        for t in trades_list:
            rows.append([
                getattr(t, "id", ""),
                getattr(t, "symbol", ""),
                getattr(t, "signal_date", ""),
                getattr(t, "entry_date", ""),
                getattr(t, "entry_price", ""),
                getattr(t, "stop_loss", ""),
                getattr(t, "take_profit", ""),
                getattr(t, "exit_date", ""),
                getattr(t, "exit_price", ""),
                getattr(t, "position_size_pct", 30),
                getattr(t, "components", ""),
                getattr(t, "reasons", ""),
                getattr(t, "status", ""),
                getattr(t, "created_at", "")
            ])

        ws.clear()
        ws.update(range_name="A1", values=rows)
        return True
    except Exception as e:
        st.warning(f"⚠️ Không thể đồng bộ Google Sheets: {e}")
        return False

def load_trades_from_google_sheets() -> list:
    """
    Tải danh sách lệnh từ tab `trades` trên Google Sheets nếu DB cục bộ rỗng.
    """
    if not is_google_sheets_enabled():
        return []

    try:
        gc = get_gspread_client()
        sheet_key = st.secrets["GOOGLE_SHEET_KEY"]
        sh = gc.open_by_key(sheet_key)
        ws = sh.worksheet("trades")
        records = ws.get_all_records()
        return records
    except Exception:
        return []
