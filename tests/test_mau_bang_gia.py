"""Test năm màu bảng giá.

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Màu là một KẾT LUẬN, y hệt nhãn "Pha C — Wyckoff Spring" từng hiện cho mọi
mã có điểm ≥ 60. Khác biệt duy nhất: màu còn khó bắt lỗi hơn chữ, vì không
ai nhìn một ô tím rồi tự hỏi "dựa vào đâu mà tím".

Cạm bẫy cụ thể ở đây là ngưỡng phần trăm. `pct >= 6.9 → trần` chạy đúng
phần lớn phiên nên không ai kiểm lại, rồi sai vào đúng lúc quan trọng. Đo
thật ngày 21/08/2026:

    SSI  HOSE  +6,96%  →  ĐÚNG là trần   (trần 20.750, đóng 20.750)
    SHS  HNX   +8,16%  →  KHÔNG trần     (trần 16.100, đóng 15.900)

Một ngưỡng cứng tô sai ít nhất một trong hai. Nên các test dưới đây kiểm
hai nhóm tính chất:

  · KẾT LUẬN ĐÚNG — trần/sàn/tham chiếu phải nhận ra được khi có biên độ.
    Thiếu nhóm này, module có thể luôn trả "chưa biết" mà vẫn xanh.

  · KHÔNG KẾT LUẬN BỪA — biên độ của phiên khác, hoặc không đối chiếu được
    ngày, hoặc giá nằm ngoài biên độ, đều phải làm mất màu tím/xanh lam.
    Thiếu nhóm này, module có thể tô tím bừa và cũng vẫn xanh.
"""
import pandas as pd
import pytest

import mau_bang_gia as mbg

# Số thật, đọc từ bảng giá VCI phiên 2026-08-21.
SSI = {"tham_chieu": 19400.0, "tran": 20750.0, "san": 18050.0,
       "ngay": "2026-08-21", "san_gd": "HSX", "gia_khop": 20750.0,
       "loi": None}
SHS = {"tham_chieu": 14700.0, "tran": 16100.0, "san": 13300.0,
       "ngay": "2026-08-21", "san_gd": "HNX", "gia_khop": 15900.0,
       "loi": None}


# ─────────────────────────────────────────────────────────────────────
# Kết luận đúng
# ─────────────────────────────────────────────────────────────────────

def test_dong_cua_bang_tran_thi_la_tran():
    m = mbg.mau_cho_phien(20750.0, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.TRAN
    assert m.nhan == "TRẦN"
    assert m.lop_css == "bg-tran"
    assert m.phan_tram == pytest.approx(6.96, abs=0.01)


def test_dong_cua_bang_san_thi_la_san():
    m = mbg.mau_cho_phien(18050.0, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.SAN
    assert m.lop_css == "bg-san"


def test_dung_bang_tham_chieu_thi_la_tham_chieu_khong_phai_tang():
    """Bản cũ dùng `change >= 0` nên đứng giá bị tô xanh và ghi "▲ +0"."""
    m = mbg.mau_cho_phien(19400.0, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.THAM_CHIEU
    assert m.lop_css == "bg-tc"
    assert m.mui_ten == "="


def test_tren_tham_chieu_nhung_chua_kich_bien_thi_chi_la_tang():
    m = mbg.mau_cho_phien(20700.0, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.TANG
    assert m.lop_css == "bg-tang"


def test_duoi_tham_chieu_nhung_chua_kich_bien_thi_chi_la_giam():
    m = mbg.mau_cho_phien(19000.0, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.GIAM
    assert m.lop_css == "bg-giam"


def test_hnx_tang_hon_bay_phan_tram_ma_khong_tran():
    """Đúng ca mà mọi ngưỡng phần trăm cứng đều tô sai.

    SHS 21/08/2026 tăng +8,16% — vượt xa biên HOSE 7% — nhưng nó nằm trên
    HNX (biên 10%) và trần là 16.100, cao hơn giá đóng cửa 15.900.
    """
    m = mbg.mau_cho_phien(15900.0, 14700.0, "2026-08-21", SHS)
    assert m.phan_tram > 8.0, "ca này phải vượt ngưỡng 7% mới có ý nghĩa"
    assert m.ma == mbg.TANG
    assert m.lop_css != "bg-tran"


def test_hnx_kich_bien_muoi_phan_tram_thi_van_la_tran():
    """Chiều ngược lại: đừng đổi ngưỡng cứng 7% thành ngưỡng cứng 10%."""
    m = mbg.mau_cho_phien(16100.0, 14700.0, "2026-08-21", SHS)
    assert m.ma == mbg.TRAN


# ─────────────────────────────────────────────────────────────────────
# Không kết luận bừa
# ─────────────────────────────────────────────────────────────────────

def test_bang_gia_thuoc_phien_khac_thi_mat_quyen_noi_tran():
    """Sáng thứ Hai bảng giá đã lật sang phiên mới còn nến vẫn là thứ Sáu."""
    m = mbg.mau_cho_phien(20750.0, 19400.0, "2026-08-20", SSI)
    assert m.ma != mbg.TRAN
    assert m.ma == mbg.TANG
    assert not m.biet_bien_do
    assert "2026-08-21" in m.ghi_chu and "2026-08-20" in m.ghi_chu


def test_khong_biet_ngay_nen_thi_mat_quyen_noi_tran():
    """Không đối chiếu được ngày thì biên độ không dùng được, dù nó đúng."""
    m = mbg.mau_cho_phien(20750.0, 19400.0, None, SSI)
    assert m.ma == mbg.TANG
    assert not m.biet_bien_do
    assert "ngày" in m.ghi_chu


def test_gia_nam_ngoai_bien_do_thi_vut_bien_do():
    """Điều kiện phủ định: chuyện này không xảy ra trên sàn thật.

    Xảy ra nghĩa là biên độ nhận được thuộc phiên khác — ví dụ chuỗi giá
    đã điều chỉnh hồi tố sau chia tách nhưng bảng giá thì chưa.
    """
    m = mbg.mau_cho_phien(25000.0, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.TANG
    assert not m.biet_bien_do
    assert "ngoài biên độ" in m.ghi_chu
    # Tham chiếu cũng phải rơi về giá phiên trước, không mượn nửa vời số
    # của bảng giá đã bị bác.
    assert m.tham_chieu == 19400.0


def test_bang_gia_loi_thi_tut_xuong_ba_mau():
    hong = {"tham_chieu": None, "tran": None, "san": None, "ngay": None,
            "san_gd": None, "gia_khop": None, "loi": "ConnectionError"}
    m = mbg.mau_cho_phien(20750.0, 19400.0, "2026-08-21", hong)
    assert m.ma == mbg.TANG
    assert not m.biet_bien_do
    assert m.lop_css in ("bg-tang", "bg-giam", "bg-tc")


def test_khong_co_bang_gia_thi_khong_bao_gio_ra_tran_hay_san():
    """Quét mọi mức giá quanh biên: không có biên độ thì không có tím/lam."""
    for gia in range(18000, 21001, 50):
        m = mbg.mau_cho_phien(float(gia), 19400.0, "2026-08-21", None)
        assert m.ma not in (mbg.TRAN, mbg.SAN), f"tô bừa ở giá {gia}"
        assert m.lop_css not in ("bg-tran", "bg-san")


def test_khong_co_tham_chieu_nao_thi_noi_chua_biet():
    m = mbg.mau_cho_phien(20750.0, None, None, None)
    assert m.ma == mbg.KHONG_BIET
    assert m.lop_css == "bg-kb"
    assert m.thay_doi is None


def test_khong_co_gia_dong_cua_thi_noi_chua_biet():
    m = mbg.mau_cho_phien(None, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.KHONG_BIET


# ─────────────────────────────────────────────────────────────────────
# Tham chiếu và dung sai
# ─────────────────────────────────────────────────────────────────────

def test_uu_tien_tham_chieu_cua_bang_gia_hon_gia_phien_truoc():
    """Ngày giao dịch không hưởng quyền: hai con số này KHÁC nhau.

    Chuỗi giá lịch sử đã điều chỉnh hồi tố nên `close.iloc[-2]` không còn
    là giá tham chiếu mà sở dùng để tính biên độ.
    """
    bang = dict(SSI, tham_chieu=19000.0, tran=20330.0, san=17670.0)
    m = mbg.mau_cho_phien(20000.0, 19400.0, "2026-08-21", bang)
    assert m.tham_chieu == 19000.0
    assert m.thay_doi == pytest.approx(1000.0)
    assert m.phan_tram == pytest.approx(1000.0 / 19000.0 * 100)


def test_dung_sai_gia_nuot_sai_so_dau_phay_dong_cua_float():
    """20.75 × 1000 ra 20750.000000000004, không phải 20750."""
    m = mbg.mau_cho_phien(20.75 * 1000, 19400.0, "2026-08-21", SSI)
    assert m.ma == mbg.TRAN


def test_dung_sai_chi_so_khong_duoc_nuot_phien_doi_duoi_nua_diem():
    """VN-INDEX đổi 0,3 điểm là đổi thật; dung sai của GIÁ sẽ nuốt mất nó."""
    nuot = mbg.mau_cho_phien(1768.42, 1768.12, dung_sai=mbg.DUNG_SAI)
    assert nuot.ma == mbg.THAM_CHIEU, "chứng minh dung sai giá nuốt được"

    dung = mbg.mau_cho_phien(1768.42, 1768.12,
                             dung_sai=mbg.DUNG_SAI_CHI_SO)
    assert dung.ma == mbg.TANG


def test_dung_sai_chi_so_phai_ap_dung_ca_chieu_giam():
    """Chiều giảm là chiều dễ quên: đột biến chỉ sửa nhánh âm vẫn xanh."""
    nuot = mbg.mau_cho_phien(1767.82, 1768.12, dung_sai=mbg.DUNG_SAI)
    assert nuot.ma == mbg.THAM_CHIEU, "chứng minh dung sai giá nuốt được"

    dung = mbg.mau_cho_phien(1767.82, 1768.12,
                             dung_sai=mbg.DUNG_SAI_CHI_SO)
    assert dung.ma == mbg.GIAM
    assert dung.lop_css == "bg-giam"


def test_chi_so_dung_dung_sai_rieng_van_bat_duoc_phien_dung_gia():
    m = mbg.mau_cho_phien(1768.12, 1768.12, dung_sai=mbg.DUNG_SAI_CHI_SO)
    assert m.ma == mbg.THAM_CHIEU


# ─────────────────────────────────────────────────────────────────────
# Bảng màu và giao diện phải khớp nhau
# ─────────────────────────────────────────────────────────────────────

def test_nam_trang_thai_cho_nam_mau_khac_nhau():
    lop = [mbg._LOP[k] for k in (mbg.TRAN, mbg.TANG, mbg.THAM_CHIEU,
                                 mbg.GIAM, mbg.SAN)]
    assert len(set(lop)) == 5, "hai trạng thái dùng chung một màu"


def test_moi_lop_css_deu_duoc_dinh_nghia_trong_app():
    """Đổi tên một bên mà quên bên kia thì chữ mất màu, không ai báo lỗi."""
    import pathlib
    app = (pathlib.Path(__file__).resolve().parent.parent / "app.py"
           ).read_text(encoding="utf-8")
    for lop in mbg._LOP.values():
        assert f".{lop} " in app or f".{lop}{{" in app, \
            f"app.py chưa định nghĩa CSS cho .{lop}"


def test_app_khong_tu_ket_luan_tran_bang_nguong_phan_tram():
    """Chặn đường quay lại của `pct >= 6.9`.

    Nếu ai đó thêm ngưỡng cứng vào app.py, module này thành đồ trang trí
    còn màu lại do một luật khác quyết định — hai nguồn sự thật.
    """
    import pathlib
    app = (pathlib.Path(__file__).resolve().parent.parent / "app.py"
           ).read_text(encoding="utf-8")
    import ast
    cay = ast.parse(app)
    da_nhap = any(
        (isinstance(n, ast.Import) and any(a.name == "mau_bang_gia"
                                           for a in n.names))
        or (isinstance(n, ast.ImportFrom) and n.module == "mau_bang_gia")
        for n in ast.walk(cay))
    assert da_nhap, "app.py phải IMPORT module này, không chỉ nhắc tên nó"
    than = "\n".join(d for d in app.splitlines()
                     if not d.lstrip().startswith("#"))
    for cam in ("6.9", "6,9", "> 6.8", ">= 7.0"):
        assert cam not in than, f"app.py có ngưỡng phần trăm cứng: {cam!r}"


# ─────────────────────────────────────────────────────────────────────
# `doc_bang_gia` không bao giờ được ném
# ─────────────────────────────────────────────────────────────────────

def test_doc_bang_gia_khong_nem_khi_thu_vien_hong(monkeypatch):
    import builtins
    that = builtins.__import__

    def gia(ten, *a, **k):
        if ten == "vnstock":
            raise ImportError("vnstock chưa cài")
        return that(ten, *a, **k)

    monkeypatch.setattr(builtins, "__import__", gia)
    r = mbg.doc_bang_gia("SSI")
    assert r["loi"] is not None and "ImportError" in r["loi"]
    assert r["tran"] is None and r["tham_chieu"] is None


def test_doc_bang_gia_bao_loi_khi_bang_rong(monkeypatch):
    class _T:
        def __init__(self, *a, **k):
            pass

        def price_board(self, ma):
            return pd.DataFrame()

    import sys
    import types
    gia = types.ModuleType("vnstock")
    gia.Trading = _T
    monkeypatch.setitem(sys.modules, "vnstock", gia)
    r = mbg.doc_bang_gia("XXX")
    assert r["loi"] is not None
    assert r["tran"] is None


def test_doc_bang_gia_doc_duoc_cot_multiindex(monkeypatch):
    """vnstock 4.x trả cột MultiIndex; bản khác trả cột phẳng."""
    class _T:
        def __init__(self, *a, **k):
            pass

        def price_board(self, ma):
            return pd.DataFrame(
                [[ "SSI", 20750, 18050, 19400, "HSX", "2026-08-21", 20750]],
                columns=pd.MultiIndex.from_tuples([
                    ("listing", "symbol"), ("listing", "ceiling"),
                    ("listing", "floor"), ("listing", "ref_price"),
                    ("listing", "exchange"), ("listing", "trading_date"),
                    ("match", "match_price"),
                ]))

    import sys
    import types
    gia = types.ModuleType("vnstock")
    gia.Trading = _T
    monkeypatch.setitem(sys.modules, "vnstock", gia)
    r = mbg.doc_bang_gia("SSI")
    assert r["loi"] is None
    assert (r["tham_chieu"], r["tran"], r["san"]) == (19400.0, 20750.0, 18050.0)
    assert r["ngay"] == "2026-08-21"
    assert r["san_gd"] == "HSX"
