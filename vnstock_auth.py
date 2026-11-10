"""
vnstock_auth.py
──────────────────────────────────────────────────────────────────────
Nạp API key vnstock từ cấu hình NGOÀI mã nguồn.

Repo này từng để lộ một API key công khai trên GitHub. Nguyên tắc rút ra:
key không bao giờ nằm trong file .py, kể cả dưới dạng chẻ chuỗi rồi nối lại.

Thứ tự tìm key:
    1. st.secrets["VNSTOCK_API_KEY"]   (.streamlit/secrets.toml — đã gitignore)
    2. biến môi trường VNSTOCK_API_KEY
    3. lần đăng nhập sẵn có của vnstock trên máy này (`vnstock.status()`)

THẾ HỆ 5 (BƯỚC 260): không đăng nhập là HẠNG KHÁCH — 10 lượt/phút và OHLCV cắt
còn ~1 năm (đo 06/11/2026), chứ không còn "vẫn chạy được, chỉ thiếu chỉ số nâng
cao" như thế hệ 4. Nên một lần đăng nhập HỎNG không được nuốt: nó nằm trong
`ensure_api_key()["error"]`, hiện ở `status_message()`, và `bat_buoc_dang_nhap()`
ném `DangNhapLoi` để lượt quét dừng thay vì chạy tiếp ở hạng khách.

`vnstock.change_api_key` đã bị gỡ ở thế hệ 5 (nó ném AttributeError, mà bản cũ
của file này nuốt nó thành `{"ok": False}` nên khoá không bao giờ được áp);
thay bằng `vnstock.login(khoá)`.
"""
from __future__ import annotations

import os

_STATE: dict[str, object] = {"done": False, "ok": False, "source": "", "error": "",
                             "tier": ""}


class DangNhapLoi(RuntimeError):
    """Có khoá nhưng đăng nhập vnstock thất bại — chạy tiếp là chạy ở hạng khách."""


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
        # Có thể vnstock đã được đăng nhập sẵn từ lần chạy trước trên máy này.
        try:
            import vnstock
            st = vnstock.status()
            if isinstance(st, dict) and st.get("authenticated") is True:
                _STATE.update(ok=True, source="đăng nhập sẵn có của vnstock",
                              error="", tier=str(st.get("tier") or ""))
                return _status()
        except Exception:
            pass
        _STATE.update(ok=False, source="", tier="",
                      error="chưa cấu hình VNSTOCK_API_KEY")
        return _status()

    try:
        import vnstock
        kq = vnstock.login(key)
        if isinstance(kq, dict) and kq.get("authenticated") is True:
            _STATE.update(ok=True, source=source, error="",
                          tier=str(kq.get("tier") or ""))
        else:
            # Máy chủ trả lời nhưng KHÔNG xác nhận khoá: vẫn là hạng khách.
            hang = kq.get("tier") if isinstance(kq, dict) else None
            _STATE.update(ok=False, source=source, tier=str(hang or ""),
                          error=f"máy chủ không xác nhận khoá (hạng {hang or '?'})")
    except Exception as e:
        # Thông báo lỗi của thư viện có thể chép lại khoá; không để nó lọt ra.
        mo_ta = f"{type(e).__name__}: {str(e)[:120]}".replace(key, "<khoá>")
        _STATE.update(ok=False, source=source, tier="", error=mo_ta)
    return _status()


def bat_buoc_dang_nhap() -> dict:
    """Đăng nhập, và NÉM `DangNhapLoi` nếu không được — cho lượt quét hằng ngày.

    Hạng khách cắt OHLCV còn ~1 năm và cho 10 lượt/phút; một lượt quét chạy tiếp
    ở hạng ấy ra tín hiệu trên cửa sổ ngắn mà không báo gì (cửa sổ dài là luật
    của CLAUDE.md, mục Tín hiệu). Thà dừng và đỏ job để chuông báo.
    """
    s = ensure_api_key()
    if not s["ok"]:
        raise DangNhapLoi(
            f"không đăng nhập được vnstock: {s['error']}. Chạy tiếp là chạy "
            f"ở hạng khách (10 lượt/phút, OHLCV ~1 năm).")
    return s


def _status() -> dict:
    return {"ok": bool(_STATE["ok"]), "source": str(_STATE["source"]),
            "error": str(_STATE["error"]), "tier": str(_STATE["tier"]),
            "configured": bool(_STATE["ok"])}


def status_message() -> str:
    """Câu mô tả ngắn cho giao diện. Không bao giờ lộ key."""
    s = ensure_api_key()
    if s["ok"]:
        hang = f", hạng {s['tier']}" if s["tier"] else ""
        return f"✅ Đã đăng nhập vnstock (nguồn khoá: {s['source']}{hang})"
    if s["error"].startswith("chưa cấu hình"):
        return ("⚠️ Chưa cấu hình API key vnstock — chạy ở HẠNG KHÁCH: 10 lượt/phút, "
                "dữ liệu giá cắt còn ~1 năm. "
                "Thêm `VNSTOCK_API_KEY` vào `.streamlit/secrets.toml`.")
    return f"⚠️ Không nạp được API key vnstock: {s['error']}"
