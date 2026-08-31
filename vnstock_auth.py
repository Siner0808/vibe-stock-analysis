"""
vnstock_auth.py
──────────────────────────────────────────────────────────────────────
Nạp API key vnstock từ cấu hình NGOÀI mã nguồn.

Repo này từng để lộ một API key công khai trên GitHub. Nguyên tắc rút ra:
key không bao giờ nằm trong file .py, kể cả dưới dạng chẻ chuỗi rồi nối lại.

Thứ tự tìm key:
    1. st.secrets["VNSTOCK_API_KEY"]   (.streamlit/secrets.toml — đã gitignore)
    2. biến môi trường VNSTOCK_API_KEY
    3. cấu hình sẵn có của vnai (~/.vnstock/) nếu bạn đã chạy setup trước đó

Không có key vẫn chạy được: các endpoint công khai (giá OHLCV) không cần key.
Chỉ những endpoint nâng cao mới cần.
"""
from __future__ import annotations

import os

_STATE: dict[str, object] = {"done": False, "ok": False, "source": "", "error": ""}


def _read_key() -> tuple[str | None, str]:
    """Trả (key, nguồn). Không log, không in ra key."""
    try:
        import streamlit as st
        key = st.secrets.get("VNSTOCK_API_KEY")
        if key:
            return str(key).strip(), "st.secrets"
    except Exception:
        pass
    key = os.environ.get("VNSTOCK_API_KEY")
    if key:
        return key.strip(), "biến môi trường"
    return None, ""


def ensure_api_key(force: bool = False) -> dict:
    """Đăng ký API key với vnstock. Idempotent — gọi nhiều lần vẫn an toàn.

    Trả về dict trạng thái, KHÔNG chứa key:
        {"ok": bool, "source": str, "error": str, "configured": bool}
    """
    if _STATE["done"] and not force:
        return _status()

    _STATE["done"] = True
    key, source = _read_key()

    if not key:
        # Có thể vnai đã được cấu hình sẵn từ lần chạy trước trên máy này
        try:
            import vnai
            if vnai.get_api_key():
                _STATE.update(ok=True, source="cấu hình vnai sẵn có", error="")
                return _status()
        except Exception:
            pass
        _STATE.update(ok=False, source="", error="chưa cấu hình VNSTOCK_API_KEY")
        return _status()

    try:
        import vnstock
        vnstock.change_api_key(key)
        _STATE.update(ok=True, source=source, error="")
    except Exception as e:
        _STATE.update(ok=False, source=source,
                      error=f"{type(e).__name__}: {str(e)[:120]}")
    return _status()


def _status() -> dict:
    return {"ok": bool(_STATE["ok"]), "source": str(_STATE["source"]),
            "error": str(_STATE["error"]),
            "configured": bool(_STATE["ok"])}


def status_message() -> str:
    """Câu mô tả ngắn cho giao diện. Không bao giờ lộ key."""
    s = ensure_api_key()
    if s["ok"]:
        return f"✅ Đã nạp API key vnstock (nguồn: {s['source']})"
    if s["error"].startswith("chưa cấu hình"):
        return ("ℹ️ Chưa cấu hình API key vnstock. Dữ liệu giá vẫn hoạt động; "
                "một số chỉ số nâng cao có thể không khả dụng. "
                "Thêm `VNSTOCK_API_KEY` vào `.streamlit/secrets.toml`.")
    return f"⚠️ Không nạp được API key vnstock: {s['error']}"
