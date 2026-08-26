"""Gác cho `experiment_fundamentals.py` — script quyết định TRONG_SO_CO_BAN.

Ba lỗi thật, không lỗi nào làm script nổ:

1. Script chưa bao giờ chạy nổi trên Windows. Nó chết ở `print` dòng tiêu
   đề vì console mặc định cp1258 — TRƯỚC khi đo bất cứ thứ gì. Một script
   đo lường không chạy được thì mọi con số nó lẽ ra sinh ra đều không tồn
   tại, và không có gì trên đĩa nói ra điều đó.

2. `tcrit` tra sai bảng. Bảng có khoá là SỐ QUAN SÁT nhưng lời gọi truyền
   `len(per) - 1`, tức BẬC TỰ DO. Hai lỗi con:
     • n = 3 rơi ra ngoài bảng và nhận hằng số 2,1 trong khi t thật là
       4,303 — khoảng tin cậy hẹp lại **hơn một nửa**, tức dễ tuyên bố
       "CÓ tín hiệu" hơn hẳn. Đúng chiều mà `NGUYEN-TAC-DO-LUONG.md` cảnh
       báo: lỗi đo lường gần như không bao giờ làm kết quả xấu đi.
     • n ≥ 10 nhận 2,1 cho mọi bậc tự do. Với n = 10 (df = 9) t thật là
       2,262 — vẫn hẹp hơn thật 7%.

3. `forward_return` ghép quý 2018 với cửa sổ giá 2022. Xem mục 4 bên dưới.
   Lỗi này NGỦ YÊN cho tới ngày cache BCTC được làm mới lùi về 2018 —
   tức chính hành động sửa dữ liệu đã đánh thức nó.
"""
import ast
import importlib
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent


def _mod():
    return importlib.import_module("experiment_fundamentals")


# ─────────────────────────────────────────────────────────────────────
# 1. Tra đúng bảng
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n,t_that", [
    (3, 4.303),    # df = 2
    (4, 3.182),    # df = 3
    (5, 2.776),    # df = 4
    (10, 2.262),   # df = 9  — bản cũ trả 2,1
    (30, 2.045),   # df = 29
])
def test_tra_theo_bac_tu_do_khong_phai_so_quan_sat(n, t_that):
    got = _mod().t_crit_95(n)
    assert abs(got - t_that) < 1e-9, (
        f"n={n} (df={n-1}) phải cho t={t_that}, nhận {got}")
    print(f"PASS  n={n:>3} -> t={got}")


def test_n_bang_3_khong_duoc_lot_xuong_hang_so():
    """Cái lỗ nguy hiểm nhất của bản cũ.

    `len(per) < 3` bị bỏ qua, nên n = 3 là mẫu NHỎ NHẤT thật sự đi qua
    phép kiểm. Đó cũng đúng là ô rơi ra ngoài bảng cũ.
    """
    t = _mod().t_crit_95(3)
    assert t > 4.0, f"n=3 phải dùng t≈4,303, nhận {t} — KTC hẹp bằng nửa"
    print(f"PASS  n=3 -> {t} (không phải 2,1)")


# ─────────────────────────────────────────────────────────────────────
# 2. Không kết luận bừa khi ra ngoài bảng
# ─────────────────────────────────────────────────────────────────────

def test_ngoai_bang_luon_nghieng_ve_phia_khoang_RONG():
    """Bậc tự do không có trong bảng phải lấy mốc THẤP hơn, không phải cao.

    Lấy mốc thấp hơn => t lớn hơn => khoảng rộng hơn => khó tuyên bố có
    tín hiệu hơn. Hướng sai của phép làm tròn ở đây tạo ra tín hiệu giả.
    """
    m = _mod()
    for n in (36, 45, 70, 130, 500):
        df = n - 1
        moc_duoi = max(k for k in m._T95 if k <= df)
        assert m.t_crit_95(n) == m._T95[moc_duoi]
        assert m.t_crit_95(n) >= m._T95[min(
            (k for k in m._T95 if k >= df), default=moc_duoi)]
    print("PASS  ngoài bảng -> nghiêng về phía KTC rộng")


def test_khong_tang_khi_them_quan_sat():
    """Thêm dữ liệu không bao giờ được làm khoảng tin cậy RỘNG ra."""
    m = _mod()
    truoc = None
    for n in range(3, 400):
        t = m.t_crit_95(n)
        if truoc is not None:
            assert t <= truoc + 1e-12, (
                f"n={n}: t={t} lớn hơn n={n-1}: t={truoc}")
        truoc = t
    print("PASS  t đơn điệu không tăng theo n")


def test_khong_bao_gio_thap_hon_gioi_han_chuan():
    m = _mod()
    for n in (3, 10, 100, 10_000):
        assert m.t_crit_95(n) >= 1.96, f"n={n} cho t={m.t_crit_95(n)} < 1,96"
    print("PASS  không ô nào xuống dưới 1,96")


# ─────────────────────────────────────────────────────────────────────
# 3. Script phải chạy được trên Windows — đọc AST, không đọc chuỗi
# ─────────────────────────────────────────────────────────────────────

def test_phai_dat_lai_ma_hoa_stdout():
    """`"reconfigure" in src` sẽ khớp phải chính đoạn chú thích ở trên.

    Gác này đọc cây cú pháp: phải có một LỜI GỌI `.reconfigure(...)` thật.
    """
    cay = ast.parse((GOC / "experiment_fundamentals.py").read_text(
        encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "reconfigure" in goi, (
        "thiếu sys.stdout.reconfigure(encoding='utf-8') — script sẽ chết ở "
        "dòng print đầu tiên trên console cp1258")
    print("PASS  có gọi reconfigure (xác nhận bằng AST)")


# ─────────────────────────────────────────────────────────────────────
# 4. Quý nằm TRƯỚC cache giá phải bị loại, không được nhận giá gần nhất
# ─────────────────────────────────────────────────────────────────────
#
# `t.searchsorted(ngay)` trả 0 cho MỌI ngày sớm hơn dữ liệu. Không kiểm
# thì `c[0 + horizon] / c[0]` chạy bình thường và trả về lợi nhuận 60
# phiên ĐẦU TIÊN của cache — cùng một con số cho mọi quý trước đó.
#
# Lỗi này ngủ yên suốt thời gian cache BCTC chỉ lùi tới 2024-Q3. Ngày
# 23/08/2026 cache được làm mới lên 34 kỳ (2018-Q1) và nó thức dậy:
# 14/33 kỳ trong phép đo thành bản sao của một cửa sổ giá duy nhất.


def _gia(tu: str, so_phien: int = 400):
    import pandas as pd
    ngay = pd.bdate_range(tu, periods=so_phien)
    return pd.DataFrame({
        "time": [str(d)[:10] for d in ngay],
        "close": [100.0 + i for i in range(so_phien)],
    })


def test_quy_truoc_cache_gia_phai_tra_None():
    m = _mod()
    px = _gia("2022-01-03")
    assert m.forward_return(px, "2018-05-15", 60) is None, (
        "quý 2018 nhận lợi nhuận của cửa sổ giá 2022 -> ghép sai bốn năm")
    print("PASS  quý trước cache giá -> None")


def test_moi_quy_truoc_cache_khong_duoc_ra_CUNG_MOT_so():
    """Triệu chứng nhìn thấy được của lỗi: nhiều kỳ, một con số."""
    m = _mod()
    px = _gia("2022-01-03")
    ra = [m.forward_return(px, f"{n}-05-15", 60) for n in range(2018, 2022)]
    assert set(ra) == {None}, f"bốn quý khác nhau cho ra {set(ra)}"
    print("PASS  bốn kỳ trước cache -> đều None, không phải cùng một số")


def test_dung_phien_dau_tien_thi_VAN_tinh():
    """Chặn phải chặt vừa đủ: bằng phiên đầu là hợp lệ, không được loại."""
    m = _mod()
    px = _gia("2022-01-03")
    r = m.forward_return(px, "2022-01-03", 60)
    assert r is not None and r > 0, f"phiên đầu tiên bị loại oan (nhận {r})"
    print(f"PASS  đúng phiên đầu -> vẫn tính ({r:.2f}%)")


def test_ngay_sau_cache_van_tra_None():
    m = _mod()
    px = _gia("2022-01-03", so_phien=100)
    assert m.forward_return(px, "2030-01-01", 60) is None
    print("PASS  ngày sau cache -> None")


def test_truoc_khi_co_gia_doc_dung_hai_phia():
    m = _mod()
    px = _gia("2022-01-03")
    assert m.truoc_khi_co_gia(px, "2021-12-31")
    assert not m.truoc_khi_co_gia(px, "2022-01-03")
    assert not m.truoc_khi_co_gia(px, "2023-06-01")
    print("PASS  ranh giới trước/không-trước đúng cả hai phía")
