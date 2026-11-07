"""Gác bảng màu giao diện kiểu Apple tối (BƯỚC 262).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Màu là một KẾT LUẬN hiển thị: tăng xanh lá, giảm đỏ, trần tím, sàn xanh lam,
tham chiếu vàng (`mau_bang_gia`). Hai lỗi lặng lẽ nhất khi chỉnh màu:

  · màu chủ đạo/nút bấm quay lại xanh lá — xanh lá phải chỉ nghĩa "tăng";
  · một màu ngữ nghĩa nhạt đi dưới ngưỡng đọc được (WCAG 4,5:1) trên nền thẻ.

Nên gác kiểm bốn nhóm, và TỰ TÍNH độ tương phản (không chép số từ ai):

  1. `.streamlit/config.toml` mang đúng token nền/chữ/màu chủ đạo.
  2. Năm màu bảng giá + màu chủ đạo + màu cảnh báo: có mặt trong CSS của
     `app.py`, đôi một khác nhau, và màu chủ đạo KHÔNG phải màu "tăng".
  3. Độ tương phản ≥ 4,5:1 của chữ chính/phụ, năm màu ngữ nghĩa và màu chủ đạo
     trên canvas `#000000` VÀ trên thẻ `#272729` (và `#2a2a2c`).
  4. Mọi hex trong ba module hiển thị nằm trong bảng màu; không `gradient`,
     không `#00e676`; mọi `box-shadow` là `none` hoặc vòng focus 2px.

Màu "tím" và "đỏ" KHÔNG dùng đúng mẫu Apple dark chuẩn (`#bf5af2`, `#ff453a`):
hai mẫu ấy chỉ đạt 4,23 và 4,38 trên thẻ `#272729` — dưới 4,5 — nên dùng
`#c96cf6` và `#ff5a50` (BƯỚC 262).
"""
from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

# ── Token (nguồn duy nhất của gác này) ──────────────────────────────────────
CANVAS = "#000000"
THE = "#272729"
THE_PHU = "#2a2a2c"
VIEN = "#333333"
CHU_CHINH = "#ffffff"
CHU_PHU = "#cccccc"
CHU_BA = "#7a7a7a"
CHU_DAU = "#2997ff"          # màu tương tác DUY NHẤT
VONG_FOCUS = "#0071e3"
CANH_BAO = "#ff9f0a"

TRAN = "#c96cf6"             # tím
TANG = "#30d158"             # xanh lá
THAM_CHIEU = "#ffd60a"       # vàng
GIAM = "#ff5a50"             # đỏ
SAN = "#64d2ff"              # xanh lam (cyan, khác màu chủ đạo)
NAM_MAU = {"tran": TRAN, "tang": TANG, "tham_chieu": THAM_CHIEU,
           "giam": GIAM, "san": SAN}

BANG_MAU = {CANVAS, THE, THE_PHU, VIEN, CHU_CHINH, CHU_PHU, CHU_BA, CHU_DAU,
            VONG_FOCUS, CANH_BAO, *NAM_MAU.values()}

MODUN_HIEN_THI = ("app.py", "trade_review.py", "master_agent.py")
NGUONG_TUONG_PHAN = 4.5


def _doc(ten: str) -> str:
    return (GOC / ten).read_text(encoding="utf-8")


def _do_sang(hex_: str) -> float:
    h = hex_.lstrip("#")
    kenh = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        kenh.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * kenh[0] + 0.7152 * kenh[1] + 0.0722 * kenh[2]


def tuong_phan(a: str, b: str) -> float:
    """Tỷ lệ tương phản WCAG 2.x giữa hai màu hex."""
    x, y = sorted((_do_sang(a), _do_sang(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def _bien_css(ten: str) -> str:
    """Giá trị biến CSS `--c-<ten>` khai ở khối :root của app.py."""
    m = re.search(rf"--c-{re.escape(ten)}:\s*(#[0-9a-fA-F]{{6}})\s*;", _doc("app.py"))
    assert m, f"app.py không khai biến CSS --c-{ten}"
    return m.group(1).lower()


# ── 0. Hàm đo tự kiểm ────────────────────────────────────────────────────────
def test_ham_tuong_phan_dung_o_hai_dau_va_diem_da_biet():
    assert tuong_phan("#000000", "#ffffff") == pytest.approx(21.0, abs=1e-6)
    assert tuong_phan("#777777", "#777777") == pytest.approx(1.0, abs=1e-9)
    # Mẫu Apple dark chuẩn trên thẻ: đã đo 4,23 / 4,38 (dưới ngưỡng).
    assert tuong_phan("#bf5af2", THE) < NGUONG_TUONG_PHAN
    assert tuong_phan("#ff453a", THE) < NGUONG_TUONG_PHAN


# ── 1. config.toml ───────────────────────────────────────────────────────────
def test_config_toml_mang_dung_token():
    t = tomllib.loads(_doc(".streamlit/config.toml"))["theme"]
    assert t["primaryColor"].lower() == CHU_DAU
    assert t["backgroundColor"].lower() == CANVAS
    assert t["secondaryBackgroundColor"].lower() == THE
    assert t["textColor"].lower() == CHU_CHINH


def test_mau_chu_dao_khong_phai_xanh_la_tang():
    t = tomllib.loads(_doc(".streamlit/config.toml"))["theme"]
    assert t["primaryColor"].lower() != TANG
    assert _bien_css("acc") != TANG
    assert _bien_css("acc") != SAN, "màu chủ đạo không được trùng sàn (xanh lam)"


# ── 2. Năm màu bảng giá trong CSS ────────────────────────────────────────────
@pytest.mark.parametrize("bien, mong", [("p", TRAN), ("g", TANG), ("a", THAM_CHIEU),
                                         ("r", GIAM), ("san", SAN)])
def test_nam_mau_bang_gia_trong_css(bien, mong):
    assert _bien_css(bien) == mong


def test_nam_mau_bang_gia_doi_mot_khac_nhau_va_khac_mau_chu_dao():
    gia_tri = list(NAM_MAU.values()) + [CHU_DAU, CANH_BAO]
    assert len(set(gia_tri)) == len(gia_tri)
    css = {k: _bien_css(k) for k in ("p", "g", "a", "r", "san", "acc", "o")}
    assert len(set(css.values())) == len(css)


def test_cac_lop_bang_gia_noi_dung_bien():
    van = _doc("app.py")
    for lop, bien in ((".bg-tran", "p"), (".bg-tang", "g"), (".bg-tc", "a"),
                      (".bg-giam", "r"), (".bg-san", "san")):
        assert re.search(rf"{re.escape(lop)}\s*\{{\s*color:\s*var\(--c-{bien}\)", van), lop


# ── 3. Tương phản WCAG ───────────────────────────────────────────────────────
@pytest.mark.parametrize("nen", [CANVAS, THE, THE_PHU])
@pytest.mark.parametrize("ten, mau", [("chu_chinh", CHU_CHINH), ("chu_phu", CHU_PHU),
                                       ("chu_dao", CHU_DAU), ("canh_bao", CANH_BAO),
                                       *NAM_MAU.items()])
def test_tuong_phan_toi_thieu_4_5(ten, mau, nen):
    tp = tuong_phan(mau, nen)
    assert tp >= NGUONG_TUONG_PHAN, f"{ten} {mau} trên {nen}: {tp:.2f} < {NGUONG_TUONG_PHAN}"


def test_chu_ba_doc_duoc_tren_canvas():
    assert tuong_phan(CHU_BA, CANVAS) >= NGUONG_TUONG_PHAN


def test_chu_tren_nut_chu_dao_doc_duoc():
    assert tuong_phan(CANVAS, CHU_DAU) >= NGUONG_TUONG_PHAN
    m = re.search(r'kind="primary"\]\s*\{\s*background:\s*(#[0-9a-f]{6})[^;]*;\s*color:\s*(#[0-9a-f]{6})',
                  _doc("app.py"))
    assert m, "không tìm thấy nút primary trong CSS"
    assert (m.group(1), m.group(2)) == (CHU_DAU, CANVAS)


def test_bien_chu_va_nen_css_la_token():
    assert _bien_css("bg") == CANVAS and _bien_css("s1") == THE and _bien_css("s2") == THE_PHU
    assert _bien_css("t1") == CHU_CHINH and _bien_css("t2") == CHU_PHU and _bien_css("t3") == CHU_BA
    assert _bien_css("s3") == VIEN and _bien_css("border") == VIEN
    assert _bien_css("focus") == VONG_FOCUS and _bien_css("o") == CANH_BAO


# ── 4. Không lạc màu / không gradient / không phát sáng ──────────────────────
def test_moi_hex_trong_modun_hien_thi_nam_trong_bang_mau():
    la = {}
    for ten in MODUN_HIEN_THI:
        for hx in re.findall(r"#[0-9a-fA-F]{6}\b", _doc(ten)):
            if hx.lower() not in BANG_MAU:
                la.setdefault(hx.lower(), []).append(ten)
    assert not la, f"hex ngoài bảng màu: {la}"


def test_khong_con_xanh_la_cu_hay_gradient():
    for ten in MODUN_HIEN_THI + (".streamlit/config.toml",):
        van = _doc(ten).lower()
        assert "#00e676" not in van, ten
        assert "#00d97e" not in van, ten
        assert "gradient" not in van, ten
        assert "drop-shadow" not in van, ten


def test_box_shadow_chi_none_hoac_vong_focus():
    van = _doc("app.py")
    for m in re.finditer(r"box-shadow:\s*([^;]+);", van):
        gia_tri = m.group(1).replace("!important", "").strip()
        assert gia_tri == "none" or gia_tri == f"0 0 0 2px {VONG_FOCUS}", gia_tri


def _hang_so_modul(ten: str) -> dict[str, str]:
    cay = ast.parse(_doc(ten))
    kq = {}
    for nut in cay.body:
        if isinstance(nut, ast.Assign) and isinstance(nut.value, ast.Constant) \
                and isinstance(nut.value.value, str):
            for muc in nut.targets:
                if isinstance(muc, ast.Name):
                    kq[muc.id] = nut.value.value.lower()
    return kq


def test_trade_review_mau_len_xuong_la_tang_giam():
    h = _hang_so_modul("trade_review.py")
    assert h["COLOR_UP"] == TANG and h["COLOR_TP"] == TANG
    assert h["COLOR_DOWN"] == GIAM and h["COLOR_SL"] == GIAM
    assert h["COLOR_ENTRY"] == CHU_DAU


def test_nen_bieu_do_la_canvas_hoac_the():
    cho_phep = {CANVAS, THE}
    cay = ast.parse(_doc("app.py"))
    cay2 = ast.parse(_doc("trade_review.py"))
    thay = 0
    for c in (cay, cay2):
        for nut in ast.walk(c):
            if isinstance(nut, ast.keyword) and nut.arg in ("paper_bgcolor", "plot_bgcolor"):
                thay += 1
                assert isinstance(nut.value, ast.Constant)
                assert nut.value.value.lower() in cho_phep, nut.value.value
    assert thay >= 6, "quần thể nền biểu đồ rỗng/nhỏ bất thường"


def test_nen_tang_giam_giu_dung_ca_hai_bieu_do():
    """Cả hai biểu đồ nến của app: tăng = TANG, giảm = GIAM (đọc bằng AST)."""
    cay = ast.parse(_doc("app.py"))
    tang, giam = [], []
    for nut in ast.walk(cay):
        if isinstance(nut, ast.keyword) and isinstance(nut.value, ast.Constant):
            if nut.arg in ("increasing_line_color", "increasing_fillcolor"):
                tang.append(nut.value.value.lower())
            if nut.arg in ("decreasing_line_color", "decreasing_fillcolor"):
                giam.append(nut.value.value.lower())
    assert len(tang) == 4 and len(giam) == 4
    assert set(tang) == {TANG} and set(giam) == {GIAM}


def test_master_agent_mau_hanh_dong_trong_bang_mau():
    van = _doc("master_agent.py")
    mau = re.findall(r'action_color(?:"\s*:\s*|\s*=\s*)"(#[0-9a-fA-F]{6})"', van)
    assert len(mau) == 6
    assert all(m.lower() in BANG_MAU for m in mau)
    assert "#30d158" in mau and GIAM in mau and CHU_BA in mau
