"""Gác chữ, bo góc, nút bấm và nhịp lề của giao diện kiểu Apple (BƯỚC 263).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
BƯỚC 262 đổi MÀU (`tests/test_bang_mau_apple.py`). BƯỚC 263 làm nửa sau:
chữ, bo góc, nút bấm, nhịp lề. Bốn thứ này đều là hằng số nằm trong một khối CSS
dạng chuỗi, nên hỏng LẶNG LẼ (không có lỗi cú pháp, chỉ là giao diện lệch):

  · bộ chữ UI/số trôi về JetBrains Mono hoặc Inter trần → cột số không còn
    thẳng hàng, và máy Apple không dùng SF Pro;
  · một nút/thẻ/ô nhập quay về góc cũ (14px, 10px, 6px…) vì ai đó chép CSS;
  · cỡ chữ < 11px quay lại (đọc không nổi trên nền đen);
  · padding/margin/gap lệch khỏi lưới 4px.

Gác đọc KHỐI CSS BẰNG PHÂN TÍCH (tách luật `selector { khai báo }`), không
`"x" in src` — vì chú thích cũng chứa chữ. Mỗi phép phân tích có một phép thử
"quần thể không rỗng" để một bộ tách hỏng không cho xanh giả.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

NGAN_XEP_CHU = ('"SF Pro Text", "SF Pro Display", -apple-system, BlinkMacSystemFont, '
                '"Inter", system-ui, sans-serif')
NGAN_XEP_TIEU_DE = ('"SF Pro Display", "SF Pro Text", -apple-system, BlinkMacSystemFont, '
                    '"Inter", system-ui, sans-serif')
BO_GOC = {"--r-card": "18px", "--r-input": "11px", "--r-chip": "8px", "--r-pill": "9999px"}
CHO_PHEP_BO_GOC = {"18px", "11px", "8px", "9999px", "50%"}
CHU_TOI_THIEU_PX = 11
LUOI_PX = 4


def _doc(ten: str) -> str:
    return (GOC / ten).read_text(encoding="utf-8")


def _khoi_css() -> str:
    m = re.search(r"<style>(.*?)</style>", _doc("app.py"), re.DOTALL)
    assert m, "app.py không còn khối <style>"
    return m.group(1)


def _luat_css() -> list[tuple[str, dict[str, str]]]:
    """Tách khối CSS thành [(selector, {thuộc tính: giá trị})]. Bỏ chú thích và @import."""
    van = re.sub(r"/\*.*?\*/", "", _khoi_css(), flags=re.DOTALL)
    van = re.sub(r"@import url\([^)]*\);", "", van)  # URL chứa dấu `;`
    kq = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", van):
        khai = {}
        for dong in m.group(2).split(";"):
            if ":" in dong:
                k, _, v = dong.partition(":")
                khai[k.strip()] = " ".join(v.replace("!important", "").split())
        kq.append((" ".join(m.group(1).split()), khai))
    return kq


def _bien_goc() -> dict[str, str]:
    for sel, khai in _luat_css():
        if sel == ":root":
            return khai
    raise AssertionError("app.py không còn khối :root")


def _chon(selector_chua: str) -> list[dict[str, str]]:
    """Mọi luật có selector (tách theo dấu phẩy) chứa đúng chuỗi `selector_chua`."""
    kq = []
    for sel, khai in _luat_css():
        if any(selector_chua == s.strip() for s in sel.split(",")):
            kq.append(khai)
    return kq


def _giai_bien(gia_tri: str) -> str:
    m = re.fullmatch(r"var\((--[\w-]+)\)", gia_tri.strip())
    return _bien_goc()[m.group(1)] if m else gia_tri.strip()


def _bo_goc_cua(selector: str) -> str:
    luat = [k for k in _chon(selector) if "border-radius" in k]
    assert luat, f"không có luật border-radius cho {selector}"
    return _giai_bien(luat[-1]["border-radius"])


# ── 0. Bộ tách tự kiểm ──────────────────────────────────────────────────────
def test_bo_tach_css_khong_rong_va_doc_dung_mot_luat_da_biet():
    luat = _luat_css()
    assert len(luat) >= 60, f"chỉ tách được {len(luat)} luật — bộ tách hỏng?"
    assert _bien_goc()["--c-bg"] == "#000000"
    assert _chon(".cht"), "không thấy luật .cht"


# ── 1. Bộ chữ ────────────────────────────────────────────────────────────────
def test_bo_chu_ui_va_tieu_de_dung_chuoi():
    b = _bien_goc()
    assert b["--ff"] == NGAN_XEP_CHU
    assert b["--fd"] == NGAN_XEP_TIEU_DE


def test_chu_so_dung_cung_bo_chu_voi_ui_khong_con_monospace():
    b = _bien_goc()
    assert b["--fm"] == "var(--ff)"
    van = _doc("app.py")
    assert "JetBrains" not in van and "monospace" not in van.lower()


def test_khong_them_yeu_cau_phong_chu_ngoai():
    """Chỉ còn đúng một @import (Inter, bản thay thế SF Pro); không thêm họ chữ nào."""
    nhap = re.findall(r"@import url\('([^']+)'\)", _doc("app.py"))
    assert len(nhap) == 1
    ho = re.findall(r"family=([A-Za-z+]+)", nhap[0])
    assert ho == ["Inter"], ho


def test_body_dung_bien_ff():
    gop = " ".join(k.get("font-family", "") for s, k in _luat_css()
                   if 'html' in s and 'body' in s)
    assert "var(--ff)" in gop


def test_tieu_de_trong_so_600_va_chu_hoi_khit():
    for sel in ("h1", "h2", "h3", "h4", "h5", "h6", ".logo-t", ".sb-brand-name", ".cht"):
        luat = _chon(sel)
        assert luat, sel
        gop = {k: v for kh in luat for k, v in kh.items()}
        assert gop["font-weight"] == "600", (sel, gop.get("font-weight"))
        ls = float(gop["letter-spacing"].replace("px", ""))
        assert ls < 0, (sel, ls)
        assert gop["font-family"] == "var(--fd)", sel


def test_so_dung_tabular_nums_cho_moi_lop_so():
    luat = _luat_css()
    co_tabular = set()
    for sel, khai in luat:
        if khai.get("font-variant-numeric") == "tabular-nums":
            co_tabular |= {s.strip() for s in sel.split(",")}
    so = [sel for sel, khai in luat
          if khai.get("font-family") == "var(--fm)" and re.fullmatch(r"\.[\w-]+", sel)]
    assert len(so) >= 7, f"quần thể lớp số quá nhỏ: {so}"
    thieu = [s for s in so if s not in co_tabular]
    assert not thieu, f"lớp dùng chữ số mà thiếu tabular-nums: {thieu}"
    # Ô dựng bằng style nội tuyến `font-family:var(--fm)` cũng phải được phủ.
    assert '[style*="var(--fm)"]' in co_tabular
    assert '[data-testid="stMetricValue"]' in co_tabular


# ── 2. Bo góc ────────────────────────────────────────────────────────────────
def test_bon_moc_bo_goc_dung_gia_tri():
    b = _bien_goc()
    for ten, mong in BO_GOC.items():
        assert b[ten] == mong, ten
    for cu in ("--r-sm", "--r-md", "--r-lg"):
        assert cu not in b, f"{cu} là mốc cũ, phải gỡ"


def test_moi_border_radius_trong_app_thuoc_bang_cho_phep():
    van = _doc("app.py")
    gia_tri = re.findall(r"border-radius:\s*([^;\"'}]+)", van)
    assert len(gia_tri) >= 25, f"quần thể border-radius nhỏ bất thường: {len(gia_tri)}"
    la = sorted({g for g in gia_tri
                 if _giai_bien(g.replace("!important", "").strip()) not in CHO_PHEP_BO_GOC})
    assert not la, f"border-radius ngoài bảng 18/11/8/9999/50%: {la}"


@pytest.mark.parametrize("selector, mong", [
    (".topbar", "18px"), (".sb-card", "18px"), (".card", "18px"),
    (".md-cell", "11px"), (".sig-item", "11px"), (".a-row", "11px"), (".mb", "11px"),
    (".badge", "8px"), (".live-pill", "8px"), (".ptag", "8px"), (".stag", "8px"),
    ('[data-testid="stExpander"]', "18px"),
    ('[data-testid="stExpander"] details', "18px"),
    ('div[data-baseweb="input"]', "11px"),
    ('div[data-baseweb="select"] > div', "11px"),
    ('[data-testid="stSidebar"] div[data-baseweb="input"]', "11px"),
    (".stButton > button", "9999px"),
    (".stDownloadButton > button", "9999px"),
    ('[data-testid="stSidebar"] div[data-testid="column"] button', "9999px"),
])
def test_bo_goc_theo_loai_phan_tu(selector, mong):
    assert _bo_goc_cua(selector) == mong


def test_nut_primary_la_vien_thuoc():
    luat = [k for s, k in _luat_css() if 'kind="primary"' in s]
    assert luat
    assert _giai_bien(luat[0]["border-radius"]) == "9999px"


def test_nut_bam_xuong_thu_nho_095_va_giu_vong_focus():
    nhan = [(s, k) for s, k in _luat_css() if ":active" in s]
    assert nhan, "không có trạng thái :active"
    ds = " ".join(s for s, _ in nhan)
    assert ".stButton > button:active" in ds
    assert '[data-testid="stSidebar"] div[data-testid="column"] button:active' in ds
    assert all(k.get("transform") == "scale(0.95)" for _, k in nhan)
    # vòng focus 2px #0071e3 còn nguyên
    assert "0 0 0 2px #0071e3" in _doc("app.py")


# ── 3. Cỡ chữ ────────────────────────────────────────────────────────────────
def test_khong_co_font_size_nho_hon_11px():
    van = _doc("app.py")
    px = [float(x) for x in re.findall(r"font-size:\s*(\d+(?:\.\d+)?)px", van)]
    rem = [float(x) * 16 for x in re.findall(r"font-size:\s*(\d+(?:\.\d+)?)rem", van)]
    assert len(px) >= 40, f"quần thể font-size nhỏ bất thường: {len(px)}"
    nho = sorted({v for v in px + rem if v < CHU_TOI_THIEU_PX})
    assert not nho, f"font-size dưới {CHU_TOI_THIEU_PX}px: {nho}"


def test_chu_trong_bieu_do_plotly_khong_nho_hon_11():
    cay = ast.parse(_doc("trade_review.py"))
    dem = 0
    for nut in ast.walk(cay):
        if isinstance(nut, ast.keyword) and nut.arg in ("annotation_font", "textfont", "font") \
                and isinstance(nut.value, ast.Call):
            for kw in nut.value.keywords:
                if kw.arg == "size":
                    dem += 1
                    assert isinstance(kw.value, ast.Constant)
                    assert kw.value.value >= CHU_TOI_THIEU_PX, (nut.arg, kw.value.value)
    assert dem >= 3, "quần thể cỡ chữ biểu đồ rỗng/nhỏ"


# ── 4. Nhịp lề: bội số của 4px ───────────────────────────────────────────────
_KHAI_LE = re.compile(
    r"(?<![\w-])((?:padding|margin|gap)(?:-top|-bottom|-left|-right)?)\s*:\s*([^;\"'}]*)")


def _gia_tri_le() -> list[tuple[str, str]]:
    kq = []
    for m in _KHAI_LE.finditer(_doc("app.py")):
        for tok in re.findall(r"-?\d+(?:\.\d+)?px", m.group(2)):
            kq.append((m.group(1), tok))
    return kq


def test_padding_margin_gap_la_boi_so_cua_4px():
    tat_ca = _gia_tri_le()
    assert len(tat_ca) >= 80, f"quần thể giá trị lề nhỏ bất thường: {len(tat_ca)}"
    lech = sorted({f"{k}:{t}" for k, t in tat_ca if abs(float(t[:-2])) % LUOI_PX != 0})
    assert not lech, f"lề lệch lưới {LUOI_PX}px: {lech}"


def test_bo_tach_le_bat_duoc_mot_gia_tri_lech_dat_san():
    mau = "<div style=\"padding: 10px 14px; gap:6px; margin-top:-32px\">"
    ra = [t for m in _KHAI_LE.finditer(mau) for t in re.findall(r"-?\d+(?:\.\d+)?px", m.group(2))]
    assert ra == ["10px", "14px", "6px", "-32px"]
