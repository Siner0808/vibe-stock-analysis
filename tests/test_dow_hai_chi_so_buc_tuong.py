"""Bức tường của `dow_hai_chi_so` (BƯỚC 308, Dow phần 2, Lát 2, mốc B7) — gác nhập và gác lời.

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
ĐO 39 (`docs/TIEU-CHI-DOC-TRUOC.md`, mục *Bức tường*) ký rằng ô trạng thái cặp VN30 – VNMidcap là một ô MÔ TẢ: không
là tín hiệu, bộ lọc, vùng kế hoạch, thành phần điểm hay phép đo lợi nhuận. Hai điều ấy được canh bằng AST chứ không
bằng lời hứa:

  (a) GÁC NHẬP. `dow_hai_chi_so.py` CHỈ được nhập bởi `app.py` và `tools/mo_ta_dow_hai_chi_so.py` (hai file ấy là
      Lát 3 và Lát 4, chưa tồn tại ở BƯỚC 308, nên quần thể người nhập hiện RỖNG: gác này chưa có thứ để chặn, và nói
      thẳng điều đó; nó có thật khi một file lạ nhập mô-đun, xem `test_gac_nhap_cat_duoc_mot_file_la`). Chính mô-đun
      chỉ được nhập `__future__`, `dataclasses` và `cau_truc_gia`; không nhập `paper_*`, `master_agent`,
      `analysis_agents`, `ke_hoach_vao_lenh`, `san_dau`, `cham_bong`, `run_daily`, `sheets_store`, `backtest/*`, và
      không nhập `tools/do_dow_cau_truc.py`, nên không có đường tới lợi nhuận.
  (b) GÁC LỜI. Mọi hằng chuỗi của mô-đun (và mọi chuỗi nó thật sự sinh ra, ở `tests/test_dow_hai_chi_so.py`) vắng
      các cụm bị cấm ở `CAM_LOI` bên dưới.

`dow_hai_chi_so.py` NHẬP `cau_truc_gia` (để lấy `CAP_SWING`, `CHOCH`, `TANG`, `GIAM`), nên dòng `"dow_hai_chi_so.py"` trong
`tests/test_cau_truc_gia.py::CHO_PHEP_NHAP` (BƯỚC 307 thêm, chưa có gì canh) nay được canh thật: bỏ dòng ấy thì
`test_chi_nguoi_trong_danh_sach_dong_duoc_nhap_cau_truc_gia` ở file kia đỏ; file này canh thêm rằng danh sách ấy ĐÚNG
bốn tên (không thừa, không thiếu).

Gác (c) của đặc tả (biến nhận kết quả ở `app.py` chỉ nằm giữa `DOW2-BAT-DAU … DOW2-KET-THUC`) thuộc Lát 4, khi `app.py`
có khối ấy. `CHO_PHEP_DOC_KET_QUA_THAT` (ở `tools/do_dow_cau_truc.py`) giữ `False`: phần 2 không mở nó.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cau_truc_gia as C  # noqa: E402
import duyet_repo  # noqa: E402

NGUON = GOC / "dow_hai_chi_so.py"
TEN_MO_DUN = "dow_hai_chi_so"
#: Người được nhập: đặc tả mục 1 và phần *Bức tường* của ĐO 39. Danh sách ĐÓNG.
CHO_PHEP_NHAP = {"app.py", "tools/mo_ta_dow_hai_chi_so.py"}
#: Mô-đun được nhập (danh sách trắng, chặt hơn danh sách cấm của đặc tả).
DUOC_NHAP = {"__future__", "dataclasses", "cau_truc_gia"}
#: Danh sách cấm của đặc tả (phần 1 mục 8.3 và ĐO 39 *Bức tường*), để lỗi nói đúng tên.
CAM_NHAP = ("paper_", "master_agent", "analysis_agents", "ke_hoach_vao_lenh", "san_dau", "cham_bong", "run_daily",
            "sheets_store", "backtest", "do_dow_cau_truc")
#: Cụm cấm trong chuỗi hiển thị (ĐO 39 *Bức tường*, gác (b)); "sẽ" so theo TỪ, các cụm khác so theo chuỗi con.
CAM_LOI = ("dự báo", "tín hiệu mua", "tín hiệu bán", "khuyến nghị", "đáng mua", "xác nhận xu hướng chính")
TU_CAM = ("sẽ",)
KHONG_GOI = {"now", "today", "now_vn", "today_vn", "utcnow", "time", "read_csv", "get", "request", "urlopen", "open",
             "to_csv", "to_json", "write_text", "read_text", "print", "input"}


def _nhap_va_goi(duong):
    cay = ast.parse(pathlib.Path(duong).read_text(encoding="utf-8"))
    nhap, goi = set(), set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
            nhap |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
            nhap.add(n.module)
        elif isinstance(n, ast.Call):
            f = n.func
            goi.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return nhap, goi


def _file_ma_nguon(goc=GOC):
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(goc, "*.py") if not (set(p.relative_to(goc).parts) & bo)]


def _nguoi_nhap(goc, ten=TEN_MO_DUN):
    return {p.relative_to(goc).as_posix() for p in _file_ma_nguon(goc) if ten in _nhap_va_goi(p)[0]}


def _chuoi_trong_ma(duong):
    cay = ast.parse(pathlib.Path(duong).read_text(encoding="utf-8"))
    return [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _chu_cam(van: str) -> list[str]:
    thap = van.lower()
    thay = [c for c in CAM_LOI if c in thap]
    thay += [t for t in TU_CAM if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", thap)]
    return thay


# ── (a) GÁC NHẬP ──────────────────────────────────────────────────────────────────────────
def test_mo_dun_ton_tai_va_nam_o_goc_repo():
    assert NGUON.exists()
    assert NGUON.relative_to(GOC).as_posix() == "dow_hai_chi_so.py"


def test_chi_hai_file_duoc_nhap_dow_hai_chi_so():
    nguoi = _nguoi_nhap(GOC)
    assert nguoi <= CHO_PHEP_NHAP, f"dow_hai_chi_so CHỈ ĐỂ ĐỌC; đang có người lạ: {sorted(nguoi - CHO_PHEP_NHAP)}"
    assert NGUON.relative_to(GOC).as_posix() not in nguoi, "mô-đun không tự nhập mình"


def test_gac_nhap_cat_duoc_mot_file_la(tmp_path):
    """Gác nhập là gác RỖNG ở BƯỚC 308 (chưa file nào nhập); phép tự kiểm: dựng một cây giả có một file lạ nhập mô-đun
    và một file được phép, gác phải chỉ đúng file lạ. Quần thể của hàm gác là cây giả, không phải cây thật."""
    (tmp_path / "ke_hoach_la.py").write_text("import dow_hai_chi_so\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("from dow_hai_chi_so import ghep_cap\n", encoding="utf-8")
    (tmp_path / "khong_lien_quan.py").write_text("import json\n", encoding="utf-8")
    nguoi = _nguoi_nhap(tmp_path)
    assert nguoi == {"ke_hoach_la.py", "app.py"}
    assert nguoi - CHO_PHEP_NHAP == {"ke_hoach_la.py"}


def test_duong_cham_diem_va_giao_dich_KHONG_nhap_dow_hai_chi_so():
    """Mọi file của danh sách cấm của phần 1 (`CAM_NHAP` ở `tests/test_cau_truc_gia.py`) không nhập mô-đun mới."""
    for ten in ("paper_trading.py", "paper_runner.py", "paper_metrics.py", "master_agent.py", "analysis_agents.py",
                "ke_hoach_vao_lenh.py", "san_dau.py", "cham_bong.py", "run_daily.py", "sheets_store.py"):
        duong = GOC / ten
        assert duong.exists(), f"{ten} biến mất — sửa danh sách, đừng bỏ qua"
        assert TEN_MO_DUN not in _nhap_va_goi(duong)[0], ten
    ds = duyet_repo.duyet(GOC / "backtest", "*.py")
    assert ds, "quần thể rỗng"
    assert not [p for p in ds if TEN_MO_DUN in _nhap_va_goi(p)[0]]


def test_mo_dun_chi_nhap_danh_sach_trang_va_khong_nhap_gi_cam():
    nhap, goi = _nhap_va_goi(NGUON)
    goc_nhap = {m.split(".")[0] for m in nhap}
    assert goc_nhap <= DUOC_NHAP, f"nhập thứ ngoài danh sách trắng: {sorted(goc_nhap - DUOC_NHAP)}"
    cam = sorted(m for m in nhap for c in CAM_NHAP if m.startswith(c))
    assert not cam, f"nhập thứ bị cấm (có đường tới lợi nhuận): {cam}"
    assert "tools.do_dow_cau_truc" not in nhap


def test_mo_dun_khong_dong_ho_khong_mang_khong_ghi_file():
    _, goi = _nhap_va_goi(NGUON)
    assert not (KHONG_GOI & goi), sorted(KHONG_GOI & goi)


def test_mo_dun_NHAP_cau_truc_gia_nen_dong_CHO_PHEP_NHAP_la_dong_that():
    """Mô-đun phải nhập `cau_truc_gia` thật (không bắt chước hằng số bằng chuỗi gõ tay); nhờ thế dòng `CHO_PHEP_NHAP`
    của BƯỚC 307 có thứ để canh."""
    assert "cau_truc_gia" in _nhap_va_goi(NGUON)[0]


def test_CHO_PHEP_NHAP_cua_phan_1_dung_bon_ten():
    """Danh sách ĐÓNG ở `tests/test_cau_truc_gia.py` đúng bốn tên: ba của phần 1 + mô-đun này. Đọc bằng AST, không
    nhập file test."""
    cay = ast.parse((GOC / "tests" / "test_cau_truc_gia.py").read_text(encoding="utf-8"))
    tap = None
    for n in ast.walk(cay):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CHO_PHEP_NHAP" for t in n.targets):
            tap = {e.value for e in n.value.elts}
    assert tap == {"app.py", "tools/do_dow_cau_truc.py", "tools/mo_ta_cau_truc_gia.py", "dow_hai_chi_so.py"}


def test_khoa_doc_ket_qua_that_van_False():
    """Khoá của ĐO 34 nằm ở `tools/do_dow_cau_truc.py` (đọc bằng AST, không chạy dụng cụ): phần 2 không mở nó."""
    cay = ast.parse((GOC / "tools" / "do_dow_cau_truc.py").read_text(encoding="utf-8"))
    gia_tri = [n.value.value for n in cay.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
               and any(isinstance(t, ast.Name) and t.id == "CHO_PHEP_DOC_KET_QUA_THAT" for t in n.targets)]
    assert gia_tri == [False]


# ── (b) GÁC LỜI ───────────────────────────────────────────────────────────────────────────
def test_gac_loi_bat_duoc_tung_cum_cam_va_tu_se():
    """Tự kiểm của gác lời: mỗi cụm cấm đều bị bắt, và 'sẽ' chỉ bị bắt khi là TỪ."""
    for c in CAM_LOI:
        assert _chu_cam(f"cả hai chuỗi {c} nhé") == [c], c
    assert _chu_cam("điều này sẽ xảy ra") == ["sẽ"]
    assert _chu_cam("Xuống Dự Báo") == ["dự báo"]                      # không phân biệt hoa thường
    assert _chu_cam("Đã xác nhận · giảm; cùng đảo chiều swing xuống") == []
    assert _chu_cam("cả sẽ") == ["sẽ"]
    assert _chu_cam("kiểm sẽn") == []                                   # không phải từ


def test_chuoi_hien_thi_cua_mo_dun_vang_cum_cam():
    chuoi = _chuoi_trong_ma(NGUON)
    assert len(chuoi) >= 12, "quần thể chuỗi phải khác rỗng (gác không được xanh vì không có gì để đọc)"
    assert any("Đã xác nhận" in c for c in chuoi) and any("Chưa đủ bằng chứng" in c for c in chuoi)
    bat = {c: _chu_cam(c) for c in chuoi if _chu_cam(c)}
    assert not bat, f"chuỗi chứa cụm bị cấm: {bat}"


def test_chu_xac_nhan_chi_nghia_la_hai_chuoi_cung_dao_chieu_swing():
    """Hai chữ nói thẳng của ĐO 39 trên ô: 'xác nhận' ở đây chỉ là hai chuỗi cùng đảo chiều swing (xấp xỉ), không phải
    xu hướng chính của Dow. Câu mô tả trạng thái xác nhận phải NÓI thế, không nói 'xu hướng'."""
    import dow_hai_chi_so as D
    ngay = [f"2024-01-{d:02d}" for d in range(1, 11)]
    lat_a = (D.Lat(2, ngay[2], C.GIAM),)
    lat_b = (D.Lat(4, ngay[4], C.GIAM),)
    doan = D.ghep_cap(lat_a, lat_b, 5, ngay=ngay)
    h = D.hien_thi(D.trang_thai_cap_tai(doan, 5), "VN30", "VNMidcap")
    van = (h.tieu_de + " " + h.mo_ta).lower()
    assert "đảo chiều swing" in van and "xu hướng" not in van
