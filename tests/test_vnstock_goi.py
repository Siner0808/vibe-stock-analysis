"""Test phép kiểm hạng gói vnstock (thế hệ 5, BƯỚC 260).

Chạy OFFLINE bằng cách tiêm hàm đọc `(status, usage)` và hàm đăng nhập.

TRỌNG TÂM: trạng thái thứ ba.

Một phép kiểm hạng gói mà khi mất mạng lại trả "khớp" thì chính nó trở
thành đúng thứ nó sinh ra để bắt — một dòng trạng thái báo xanh mà không
kiểm gì. Nên `dat` chỉ True khi ĐÃ kiểm VÀ khớp; mọi đường hỏng đều phải
rơi vào `CHUA_KIEM_DUOC`, không rơi vào `KHOP`.
"""
import pytest

import vnstock_goi as vg


def _doc(hang="silver", hang_cb=None, xac_nhan=True, con_han=True,
         het_han="2026-11-22T02:49:13Z", ky=None, phut=300):
    """Hàm đọc giả, trả đúng HÌNH DẠNG `vnstock.status()` / `vnstock.usage()` đo 06/11/2026."""
    def _f():
        st = {"schema_version": 1, "authenticated": xac_nhan, "active": con_han,
              "tier": hang, "expires_at": het_han}
        us = {"tier": hang_cb or hang, "authenticated": xac_nhan,
              "limits": {"per_minute": phut, "per_hour": 15000},
              "rule": {"routes": "*", "periods": ky}}
        return st, us
    return _f


def _ok():
    return {"ok": True, "source": "st.secrets", "error": "", "tier": "silver"}


def _goi(doc=None, dang_nhap=_ok, **kw):
    vg.xoa_cache()
    return vg.kiem_goi(doc=doc or _doc(), dang_nhap=dang_nhap, **kw)


# ─────────────────────────────────────────────────────────────────────
# 1. Bắt được hai kiểu lệch còn lại
# ─────────────────────────────────────────────────────────────────────

def test_hang_may_chu_khac_hang_thu_vien_thi_LECH():
    t = _goi(_doc(hang="silver", hang_cb="free", ky=8, phut=60))
    assert t.tinh_trang == vg.LECH
    assert t.dat is False
    assert t.hang_may_chu == "silver" and t.hang_cuc_bo == "free"
    assert "silver" in t.dong_log() and "free" in t.dong_log()
    assert "8 kỳ" in t.dong_log(), t.dong_log()
    assert t.mo_ta_lech() == "mua silver · chạy như free"
    print(f"PASS  {t.dong_log()[:90]}…")


def test_goi_het_hieu_luc_thi_LECH():
    t = _goi(_doc(con_han=False))
    assert t.tinh_trang == vg.LECH and t.dat is False
    assert "không còn hiệu lực" in t.dong_log()
    assert t.mo_ta_lech() == "máy chủ báo gói không còn hiệu lực"
    print(f"PASS  {t.dong_log()[:90]}…")


def test_khop_thi_dat():
    t = _goi(_doc(hang="silver", ky=None, phut=300))
    assert t.tinh_trang == vg.KHOP and t.dat is True
    assert "hết hạn 2026-11-22" in t.dong_log()
    assert t.han_muc_phut == 300 and t.ky_bctc is None
    assert "không giới hạn số kỳ" in t.dong_log()
    print(f"PASS  {t.dong_log()[:90]}…")


def test_ky_bctc_va_han_muc_doc_DONG_tu_usage():
    """Không chép bảng cứng: hạng nào thì `usage()` nói số đó."""
    t = _goi(_doc(hang="free", ky=8, phut=60))
    assert t.tinh_trang == vg.KHOP and t.ky_bctc == 8 and t.han_muc_phut == 60
    assert "BCTC 8 kỳ" in t.dong_log()
    print("PASS  số kỳ và hạn mức lấy từ usage()")


# ─────────────────────────────────────────────────────────────────────
# 2. Trạng thái thứ ba — quan trọng nhất file này
# ─────────────────────────────────────────────────────────────────────

def test_mat_mang_KHONG_duoc_bao_khop():
    """Nếu đường hỏng cho ra "khớp" thì phép kiểm này vô dụng đúng lúc cần."""
    def _no():
        raise ConnectionError("mạng hỏng")

    t = _goi(_no)
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC
    assert t.dat is False
    assert "ConnectionError" in t.ly_do
    assert "chưa kiểm được" in t.dong_log()
    print(f"PASS  mất mạng -> {t.tinh_trang}, không phải KHỚP")


@pytest.mark.parametrize("rac", [(None, None), ([], []), ("chuỗi", "chuỗi"), ({}, {}),
                                 ({"tier": None}, {"tier": None}),
                                 ({"tier": "silver"}, {})])
def test_may_chu_tra_rac_thi_CHUA_KIEM_DUOC(rac):
    t = _goi(lambda: rac)
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC, f"{rac!r} -> {t.tinh_trang}"
    assert t.dat is False
    print(f"PASS  thư viện trả {str(rac)[:22]!r:<26} -> chưa kiểm được")


def test_khoa_chua_duoc_xac_nhan_thi_CHUA_KIEM_DUOC_khong_phai_KHOP():
    """`authenticated` False (hạng khách) mà cả hai hàm cùng nói 'guest' trông NHƯ khớp.
    Đúng cái bẫy của thế hệ 5: hai bên đọc cùng một nguồn nên phải đòi xác nhận khoá."""
    t = _goi(_doc(hang="guest", xac_nhan=False, phut=10, ky=0))
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC and t.dat is False
    assert "hạng khách" in t.ly_do
    print("PASS  khách (chưa xác nhận khoá) -> chưa kiểm được, không KHỚP")


def test_khong_co_khoa_thi_CHUA_KIEM_DUOC():
    t = _goi(dang_nhap=lambda: {"ok": False, "error": "chưa cấu hình VNSTOCK_API_KEY"})
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC
    assert "chưa cấu hình" in t.ly_do
    print("PASS  không có khoá -> chưa kiểm được, nói rõ vì sao")


def test_dang_nhap_that_bai_thi_CHUA_KIEM_DUOC_va_noi_ly_do():
    t = _goi(dang_nhap=lambda: {"ok": False,
                                "error": "AuthError: khoá không hợp lệ"})
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC and t.dat is False
    assert "đăng nhập vnstock thất bại" in t.ly_do and "AuthError" in t.ly_do
    print("PASS  đăng nhập hỏng -> chưa kiểm được, lý do nằm trong ly_do")


def test_dang_nhap_no_thi_khong_lam_do_ca_app():
    def _no():
        raise RuntimeError("kho khoá hỏng")
    t = _goi(dang_nhap=_no)
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC
    print("PASS  đăng nhập nổ -> vẫn trả trạng thái, không ném")


def test_dat_CHI_True_khi_khop():
    """`dat` là thứ giao diện dùng để tô màu. Nó không được True ở đâu khác."""
    assert _goi(_doc(hang="silver", hang_cb="free")).dat is False       # LỆCH
    assert _goi(lambda: (None, None)).dat is False                     # CHƯA KIỂM
    assert _goi(_doc(hang="silver")).dat is True                       # KHỚP
    print("PASS  dat=True chỉ ở đúng một nhánh")


# ─────────────────────────────────────────────────────────────────────
# 3. Không rò rỉ, không ném, không tự sửa hạng
# ─────────────────────────────────────────────────────────────────────

def test_khong_bao_gio_lo_khoa():
    khoa = "vnstock_KHOA_GIA_KHONG_PHAI_KHOA_THAT"
    t = _goi(dang_nhap=lambda: {"ok": False, "error": "AuthError: " + "<khoá>"})
    ca = " ".join([t.dong_log(), t.ly_do, repr(t)])
    assert khoa not in ca and "KHOA_GIA" not in ca
    print("PASS  khoá không lọt vào log, ly_do hay repr")


def test_chi_DOC_khong_ghi_de_phep_kiem_giay_phep():
    """Module này CHỈ ĐỌC: không gọi `vnstock.login` / `logout`, không đụng `vnai`.

    Đăng nhập là việc của `vnstock_auth`; ở đây chỉ hỏi `status()` và `usage()`. Ép hạng
    sẽ làm app tiếp tục khẳng định silver sau ngày hết hạn — đúng lời nói dối âm thầm mà
    file này sinh ra để phát hiện.
    """
    import ast
    import os
    nguon = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "vnstock_goi.py"), encoding="utf-8").read()
    cay = ast.parse(nguon)
    thuoc_tinh_goi = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
    for cam in ("login", "logout", "setup_api_key", "change_api_key", "_cached_tier"):
        assert cam not in thuoc_tinh_goi, f"module đang gọi/ghi {cam}"
    ten_nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ten_nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ten_nhap.add(n.module.split(".")[0])
    assert "vnai" not in ten_nhap, "thế hệ 5 không còn vnai"
    print("PASS  chỉ đọc, không gọi login/logout và không nhập vnai")


def test_cache_khong_dinh_khi_tiem_ham():
    """Tiêm hàm vào thì phải bỏ qua cache, nếu không ca sau nhận kết quả ca trước."""
    a = _goi(_doc(hang="silver"))
    b = _goi(_doc(hang="golden"))
    assert a.hang_may_chu == "silver" and b.hang_may_chu == "golden"
    print("PASS  hàm đọc tiêm vào không bị cache che")


def test_doc_that_dung_status_va_usage_cua_vnstock(monkeypatch):
    """Đường KHÔNG tiêm `doc` phải gọi đúng hai hàm công khai của thế hệ 5."""
    import sys
    import types
    gia = types.ModuleType("vnstock")
    goi = []
    gia.status = lambda: (goi.append("status"),
                          {"authenticated": True, "active": True, "tier": "silver",
                           "expires_at": "2026-11-22T00:00:00Z"})[1]
    gia.usage = lambda: (goi.append("usage"),
                         {"tier": "silver", "limits": {"per_minute": 300},
                          "rule": {"periods": None}})[1]
    monkeypatch.setitem(sys.modules, "vnstock", gia)
    vg.xoa_cache()
    t = vg.kiem_goi(dang_nhap=_ok, dung_cache=False)
    assert t.tinh_trang == vg.KHOP, t
    assert goi == ["status", "usage"], goi
    print("PASS  đường thật gọi vnstock.status() rồi vnstock.usage()")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("(cần pytest vì dùng monkeypatch)")


# ─────────────────────────────────────────────────────────────────────
# 4. Cache BCTC không được đóng băng ở hạng gói cũ
# ─────────────────────────────────────────────────────────────────────

def _fetch_mod():
    import importlib
    return importlib.import_module("fetch_fundamentals")


def _duong(tmp_path, sym, co=True):
    d = {n: tmp_path / f"{sym}_{n}.csv" for n in ("ratio", "income", "balance")}
    if co:
        for p in d.values():
            p.write_text("item_id,2026-Q2\nroe,20\n", encoding="utf-8")
    return d


def test_chua_co_cache_thi_tai(tmp_path):
    ff = _fetch_mod()
    tai, vi_sao = ff.can_tai("FPT", _duong(tmp_path, "FPT", co=False), {}, "free")
    assert tai and "chưa có cache" in vi_sao
    print("PASS  chưa có cache -> tải")


def test_cung_hang_thi_bo_qua(tmp_path):
    ff = _fetch_mod()
    tai, vi_sao = ff.can_tai("FPT", _duong(tmp_path, "FPT"), {"FPT": "free"}, "free")
    assert not tai and "hạng free" in vi_sao
    print("PASS  cùng hạng -> bỏ qua")


def test_doi_hang_thi_TAI_LAI(tmp_path):
    """Đúng tình huống ngày ông cài xong 4 package còn thiếu.

    Không có nhánh này thì 60 file CSV tải lúc hạng free ở lại vĩnh viễn
    với 8 kỳ, và mọi phép đo sau đó vẫn đứng trên dữ liệu bị cắt.
    """
    ff = _fetch_mod()
    tai, vi_sao = ff.can_tai("FPT", _duong(tmp_path, "FPT"),
                             {"FPT": "free"}, "silver")
    assert tai, "đổi hạng mà không tải lại -> cache đóng băng ở 8 kỳ"
    assert "free" in vi_sao and "silver" in vi_sao
    print(f"PASS  free -> silver: tải lại ({vi_sao})")


def test_cache_khong_co_trong_so_tay_thi_TAI_LAI(tmp_path):
    """60 file commit trước 22/08/2026 đều không có mục trong sổ tay."""
    ff = _fetch_mod()
    tai, vi_sao = ff.can_tai("FPT", _duong(tmp_path, "FPT"), {}, "silver")
    assert tai and "không rõ" in vi_sao
    print("PASS  cache cũ không rõ hạng -> tải lại một lần")


def test_thieu_mot_file_thi_van_tai(tmp_path):
    ff = _fetch_mod()
    d = _duong(tmp_path, "FPT")
    d["balance"].unlink()
    tai, _ = ff.can_tai("FPT", d, {"FPT": "silver"}, "silver")
    assert tai, "thiếu 1 trong 3 bảng mà vẫn bỏ qua -> cache khuyết vĩnh viễn"
    print("PASS  thiếu một bảng -> vẫn tải")


# ─────────────────────────────────────────────────────────────────────
# 5. Tải THIẾU bảng không được ghi sổ tay — bẫy đo được 23/08/2026
# ─────────────────────────────────────────────────────────────────────
#
# MBB có `income` 34 kỳ MỚI nằm cạnh `balance` 8 kỳ CŨ, vì lần tải balance
# ném `UnboundLocalError` còn hai bảng kia thành công. Cả ba file cùng tên,
# cùng thư mục, cùng trông hợp lệ. `load_features()` đọc được, chỉ trả NaN
# ở 26 kỳ — không nổ, không log.
#
# Nguy hiểm nằm ở dòng `so_tay[sym] = hang` chạy bất kể thiếu hay đủ: lần
# chạy sau thấy "đã có cache đúng hạng" và BỎ QUA. Sổ tay dựng ra để chống
# đóng băng cache lại tự đóng băng cache.


def _chay_main(tmp_path, monkeypatch, tra_ve, ma="FPT"):
    """Chạy `main()` với mạng bị chặn, trả (ma_thoat, thu_muc, so_tay)."""
    import json
    import sys
    import types

    ff = _fetch_mod()
    monkeypatch.setattr(ff, "OUT", tmp_path)
    monkeypatch.setattr(ff, "SO_TAY", tmp_path / "_hang_da_tai.json")
    monkeypatch.setattr(ff, "VN100_SYMBOLS", [ma])
    monkeypatch.setattr(ff, "hang_hien_tai", lambda: "silver")
    monkeypatch.setattr(ff, "fetch_symbol", lambda s: tra_ve)
    monkeypatch.setattr(ff.time, "sleep", lambda *_: None)

    # Chặn hai lời gọi mạng ở đầu main(); cả hai đã nằm trong try/except.
    for ten in ("vnstock_auth", "vnstock_goi"):
        gia = types.ModuleType(ten)
        monkeypatch.setitem(sys.modules, ten, gia)

    monkeypatch.setattr(sys, "argv", ["fetch_fundamentals.py"])
    ma_thoat = ff.main()
    so_tay = {}
    p = tmp_path / "_hang_da_tai.json"
    if p.exists():
        so_tay = json.loads(p.read_text(encoding="utf-8"))
    return ma_thoat, tmp_path, so_tay


def _bang(so_ky: int):
    import pandas as pd
    cot = {f"2026-Q{(i % 4) + 1}": [i] for i in range(so_ky)}
    return pd.DataFrame({"item_id": ["roe"], **cot})


def test_tai_DU_ba_bang_thi_ghi_so_tay(tmp_path, monkeypatch):
    du = {n: _bang(3) for n in ("ratio", "income", "balance")}
    ma_thoat, thu_muc, so_tay = _chay_main(tmp_path, monkeypatch, du)
    assert ma_thoat == 0
    assert so_tay == {"FPT": "silver"}
    assert all((thu_muc / f"FPT_{n}.csv").exists() for n in du)
    print("PASS  đủ ba bảng -> ghi sổ tay")


def test_tai_THIEU_bang_thi_KHONG_ghi_so_tay(tmp_path, monkeypatch):
    """Không có gác này, lần chạy sau bỏ qua mã và cái thiếu thành vĩnh viễn."""
    thieu = {n: _bang(3) for n in ("ratio", "income")}
    _, _, so_tay = _chay_main(tmp_path, monkeypatch, thieu)
    assert "FPT" not in so_tay, (
        "ghi sổ tay khi thiếu bảng -> lần sau bỏ qua, cache khuyết vĩnh viễn")
    print("PASS  thiếu bảng -> không ghi sổ tay")


def test_tai_THIEU_bang_thi_XOA_ban_cu_khong_de_lai_ban_lai(tmp_path,
                                                            monkeypatch):
    """Đúng tình huống MBB: income mới 34 kỳ nằm cạnh balance cũ 8 kỳ."""
    cu = tmp_path / "FPT_balance.csv"
    cu.write_text("item_id,2024-Q1\nroe,1\n", encoding="utf-8")
    thieu = {n: _bang(34) for n in ("ratio", "income")}
    _chay_main(tmp_path, monkeypatch, thieu)
    assert not cu.exists(), (
        "để lại bảng cũ cạnh hai bảng mới -> ba file trông hợp lệ nhưng "
        "thuộc hai lần tải khác nhau, và không gì nói ra điều đó")
    print("PASS  thiếu bảng -> xoá bản cũ còn sót")


def test_khong_tai_duoc_bang_nao_thi_khong_dong_vao_dia(tmp_path,
                                                        monkeypatch):
    cu = tmp_path / "FPT_balance.csv"
    cu.write_text("item_id,2024-Q1\nroe,1\n", encoding="utf-8")
    _, _, so_tay = _chay_main(tmp_path, monkeypatch, {})
    assert cu.exists(), "dict rỗng là 'không tải được', không phải 'thiếu'"
    assert "FPT" not in so_tay
    print("PASS  không tải được bảng nào -> giữ nguyên đĩa")
