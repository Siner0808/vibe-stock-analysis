"""Test phép kiểm hạng gói vnstock.

Chạy OFFLINE bằng cách tiêm hàm tải và hàm lấy khoá.

TRỌNG TÂM: trạng thái thứ ba.

Một phép kiểm hạng gói mà khi mất mạng lại trả "khớp" thì chính nó trở
thành đúng thứ nó sinh ra để bắt — một dòng trạng thái báo xanh mà không
kiểm gì. Nên `dat` chỉ True khi ĐÃ kiểm VÀ khớp; mọi đường hỏng đều phải
rơi vào `CHUA_KIEM_DUOC`, không rơi vào `KHOP`.
"""
import pytest

import vnstock_goi as vg


def _tra(hang="silver", con_han=True, goi=("vnstock_data", "vnstock_ta"),
         het_han="2026-11-22T02:49:13.000Z"):
    """Hàm tải giả, trả đúng hình dạng máy chủ vnstocks.com trả về thật."""
    def _f(url, tham_so, cho):
        assert "api_key" in tham_so and "device_id" in tham_so
        return {"deviceRegistered": True, "userType": "paid",
                "hasActiveSubscription": con_han,
                "subscription": {"tier": hang, "endDate": het_han,
                                 "isActive": con_han},
                "availablePackages": list(goi)}
    return _f


def _cuc_bo(monkeypatch, hang="free", ky=8, phut=60):
    monkeypatch.setattr(vg, "_hang_cuc_bo", lambda: (hang, ky, phut))


def _khoa():
    return "vnstock_KHOA_GIA_KHONG_PHAI_KHOA_THAT"


def _goi(monkeypatch, **kw):
    vg.xoa_cache()
    return vg.kiem_goi(tai_ve=kw.pop("tai_ve", _tra()), lay_khoa=_khoa, **kw)


# ─────────────────────────────────────────────────────────────────────
# 1. Bắt được đúng cái lệch đã xảy ra thật
# ─────────────────────────────────────────────────────────────────────

def test_may_chu_silver_ma_cuc_bo_free_thi_LECH(monkeypatch):
    """Đúng tình huống đo được ngày 22/08/2026."""
    _cuc_bo(monkeypatch, "free", 8, 60)
    t = _goi(monkeypatch)
    assert t.tinh_trang == vg.LECH
    assert t.dat is False
    assert t.hang_may_chu == "silver" and t.hang_cuc_bo == "free"
    assert "silver" in t.dong_log() and "free" in t.dong_log()
    assert "8 kỳ" in t.dong_log(), t.dong_log()
    print(f"PASS  {t.dong_log()[:90]}…")


def test_khop_thi_dat(monkeypatch):
    _cuc_bo(monkeypatch, "silver", None, 300)
    t = _goi(monkeypatch)
    assert t.tinh_trang == vg.KHOP and t.dat is True
    assert "hết hạn 2026-11-22" in t.dong_log()
    print(f"PASS  {t.dong_log()[:90]}…")


def test_liet_ke_dung_goi_con_thieu(monkeypatch):
    """Tên gói ở đây phải là tên KHÔNG BAO GIỜ cài được.

    Bản đầu dùng `vnstock_data` và `vnstock_news` làm ví dụ "chưa cài".
    Ngày 22/08/2026 hai gói đó được cài thật và test đỏ — nó đang đo môi
    trường chứ không đo logic lọc. Một test buộc vào trạng thái máy sẽ
    đỏ đúng lúc mọi thứ đang chạy tốt.
    """
    _cuc_bo(monkeypatch)
    t = _goi(monkeypatch,
             tai_ve=_tra(goi=("goi_khong_ton_tai_a", "pytest",
                              "goi_khong_ton_tai_b")))
    assert "pytest" not in t.goi_thieu, "pytest có cài, không được coi là thiếu"
    assert set(t.goi_thieu) == {"goi_khong_ton_tai_a", "goi_khong_ton_tai_b"}
    print(f"PASS  thiếu đúng {t.goi_thieu}, bỏ qua gói đã cài")


def test_khong_thieu_goi_nao_thi_khong_noi_thua(monkeypatch):
    _cuc_bo(monkeypatch)
    t = _goi(monkeypatch, tai_ve=_tra(goi=("pytest", "pandas")))
    assert t.goi_thieu == ()
    assert "Chưa cài" not in t.dong_log()
    print("PASS  không thiếu gói -> không thêm câu thừa")


# ─────────────────────────────────────────────────────────────────────
# 2. Trạng thái thứ ba — quan trọng nhất file này
# ─────────────────────────────────────────────────────────────────────

def test_mat_mang_KHONG_duoc_bao_khop(monkeypatch):
    """Nếu đường hỏng cho ra "khớp" thì phép kiểm này vô dụng đúng lúc cần."""
    def _no(url, tham_so, cho):
        raise ConnectionError("mạng hỏng")

    _cuc_bo(monkeypatch)
    t = _goi(monkeypatch, tai_ve=_no)
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC
    assert t.dat is False
    assert "ConnectionError" in t.ly_do
    assert "chưa kiểm được" in t.dong_log()
    print(f"PASS  mất mạng -> {t.tinh_trang}, không phải KHỚP")


@pytest.mark.parametrize("rac", [None, [], "chuỗi", {}, {"userType": None},
                                 {"subscription": {}}])
def test_may_chu_tra_rac_thi_CHUA_KIEM_DUOC(monkeypatch, rac):
    _cuc_bo(monkeypatch)
    t = _goi(monkeypatch, tai_ve=lambda u, p, c: rac)
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC, f"{rac!r} -> {t.tinh_trang}"
    assert t.dat is False
    print(f"PASS  máy chủ trả {str(rac)[:22]!r:<26} -> chưa kiểm được")


def test_khong_co_khoa_thi_CHUA_KIEM_DUOC(monkeypatch):
    _cuc_bo(monkeypatch)
    vg.xoa_cache()
    t = vg.kiem_goi(tai_ve=_tra(), lay_khoa=lambda: "")
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC
    assert "chưa cấu hình" in t.ly_do
    print("PASS  không có khoá -> chưa kiểm được, nói rõ vì sao")


def test_lay_khoa_no_thi_khong_lam_do_ca_app(monkeypatch):
    _cuc_bo(monkeypatch)
    vg.xoa_cache()
    def _no():
        raise RuntimeError("kho khoá hỏng")
    t = vg.kiem_goi(tai_ve=_tra(), lay_khoa=_no)
    assert t.tinh_trang == vg.CHUA_KIEM_DUOC
    print("PASS  kho khoá hỏng -> vẫn trả trạng thái, không ném")


def test_dat_CHI_True_khi_khop(monkeypatch):
    """`dat` là thứ giao diện dùng để tô màu. Nó không được True ở đâu khác."""
    _cuc_bo(monkeypatch, "free")
    assert _goi(monkeypatch).dat is False                      # LỆCH
    assert _goi(monkeypatch, tai_ve=lambda u, p, c: None).dat is False
    _cuc_bo(monkeypatch, "silver")
    assert _goi(monkeypatch).dat is True                       # KHỚP
    print("PASS  dat=True chỉ ở đúng một nhánh")


# ─────────────────────────────────────────────────────────────────────
# 3. Không rò rỉ, không ném, không tự sửa hạng
# ─────────────────────────────────────────────────────────────────────

def test_khong_bao_gio_lo_khoa(monkeypatch):
    _cuc_bo(monkeypatch)
    t = _goi(monkeypatch)
    ca = " ".join([t.dong_log(), t.ly_do, repr(t)])
    assert _khoa() not in ca and "KHOA_GIA" not in ca
    print("PASS  khoá không lọt vào log, ly_do hay repr")


def test_khong_ghi_de_hang_cua_vnai(monkeypatch):
    """Module này CHỈ ĐỌC.

    Ép `authenticator._cached_tier = "silver"` sẽ làm app tiếp tục khẳng
    định silver sau ngày hết hạn rồi cắt dữ liệu sai mà không ai biết —
    đúng lời nói dối âm thầm mà file này sinh ra để phát hiện.
    """
    import os
    nguon = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "vnstock_goi.py"), encoding="utf-8").read()
    ma = nguon.split('"""', 2)[2]          # bỏ docstring đầu file
    for cam in ("_cached_tier =", "PERIOD_LIMITS[", "PERIOD_LIMITS =",
                "get_max_periods =", "_detect_tier ="):
        assert cam not in ma, f"module đang ghi đè phép kiểm giấy phép: {cam}"
    print("PASS  chỉ đọc, không ghi đè phép kiểm giấy phép nào")


def test_ma_may_hong_thi_khong_nem(monkeypatch, tmp_path):
    """Không đọc được hw_info.json thì trả chuỗi rỗng, không nổ."""
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert vg._ma_may() == ""
    print("PASS  thiếu hw_info.json -> mã máy rỗng, không ném")


def test_cache_khong_dinh_khi_tiem_ham(monkeypatch):
    """Tiêm hàm tải thì phải bỏ qua cache, nếu không ca sau nhận kết quả ca trước."""
    _cuc_bo(monkeypatch)
    a = _goi(monkeypatch, tai_ve=_tra(hang="silver"))
    b = _goi(monkeypatch, tai_ve=_tra(hang="golden"))
    assert a.hang_may_chu == "silver" and b.hang_may_chu == "golden"
    print("PASS  hàm tải tiêm vào không bị cache che")


def test_bang_ky_bctc_khop_voi_vnai():
    """Bảng chép ở đây phải khớp bảng thật của vnai.

    Chép cứng một bảng rồi để nó trôi khỏi nguồn gốc là cách con số trên
    giao diện âm thầm sai đi.
    """
    try:
        from vnai.beam.fundamental import PERIOD_LIMITS
    except Exception:
        pytest.skip("vnai không có ở môi trường này")
    for hang, ky in PERIOD_LIMITS.items():
        assert vg.KY_BCTC_THEO_HANG.get(hang, "thiếu") == ky, (
            f"hạng {hang}: vnai nói {ky}, bảng ở đây nói "
            f"{vg.KY_BCTC_THEO_HANG.get(hang, 'thiếu')}")
    print(f"PASS  bảng kỳ BCTC khớp vnai ({len(PERIOD_LIMITS)} hạng)")


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
