"""Test đọc chỉ số định giá (P/E, EPS, Beta).

Sự cố 13/08/2026: panel định giá hiện `—` cho mọi mã. Hai nguyên nhân
chồng lên nhau, và nguyên nhân thứ hai nguy hiểm hơn hẳn:

  1. Nguồn VCI trả 16 cột ĐỀU TÊN '2018'. Truy cập theo nhãn cột khi có
     nhãn trùng cho ra một Series chứ không phải một số -> pd.to_numeric
     ra NaN -> mọi chỉ số im lặng thành None.
  2. Chính dữ liệu đó là của năm 2018. Nếu chỉ sửa (1) mà không chặn (2),
     giao diện sẽ hiện P/E = 13,24 của tám năm trước như chỉ số hôm nay —
     tệ hơn hẳn việc hiện `—`.

Test ở đây dựng lại ĐÚNG hai hình dạng bảng thật, chạy offline.

Chạy offline:  python3 tests/test_financial_ratio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import financial_collector as fc


def bang_kbs() -> pd.DataFrame:
    """Hình dạng nguồn KBS: cột năm phân biệt, mới nhất bên trái."""
    return pd.DataFrame({
        "item": ["Thu nhập trên mỗi cổ phần của 4 quý gần nhất (EPS)",
                 "Giá trị sổ sách của cổ phiếu (BVPS)",
                 "Chỉ số giá thị trường trên thu nhập (P/E)",
                 "Beta"],
        "item_id": ["trailing_eps", "book_value_per_share_bvps",
                    "pe_ratio", "beta"],
        "2025": [3229.59, 18401.02, 7.43, 0.84],
        "2024": [3974.57, 18685.49, 6.49, 0.90],
        "2023": [4368.94, 18268.55, 5.47, 0.95],
    })


def bang_vci_hong() -> pd.DataFrame:
    """Hình dạng nguồn VCI cho ACB: 16 cột ĐỀU tên '2018', bốn quý lặp lại.

    pd.DataFrame không cho trùng tên khi dựng từ dict, nên dựng bằng
    danh sách cột — đúng như vnstock trả về."""
    hang = [
        ["Năm", "0", "year"] + ["2018"] * 8,
        ["Quý", "0", "quarter"] + [1, 2, 3, 4] * 2,
        ["P/E", "P/E", "pe_ratio"] + [13.24, 10.25, 8.35, 7.53] * 2,
    ]
    cot = ["item", "item_en", "item_id"] + ["2018"] * 8
    return pd.DataFrame(hang, columns=cot)


# ── 1. Cột trùng tên không được làm hỏng phép đọc ────────────────────
def test_cot_trung_ten_van_doc_duoc_gia_tri():
    """Đây là lỗi gốc: nhãn trùng -> row['2018'] trả Series, không phải số."""
    df = bang_vci_hong()
    assert df.columns.duplicated().any(), "bản dựng phải có cột trùng tên"

    gia_tri, nam = fc._row_latest(df, "pe_ratio", "p/e")
    assert gia_tri is not None, "cột trùng tên vẫn làm mất giá trị"
    assert nam == 2018
    print(f"PASS  bảng 16 cột trùng tên '2018' -> đọc được {gia_tri} (năm {nam})")


def test_year_columns_tra_ve_vi_tri_khong_phai_nhan():
    df = bang_vci_hong()
    cot = fc._year_columns(df)
    assert cot == [(2018, 10)], f"phải gộp về một năm, một vị trí: {cot}"
    assert all(isinstance(p, int) for _, p in cot)
    print(f"PASS  16 cột '2018' -> gộp còn {cot} (năm, vị trí)")


# ── 2. Đọc đúng năm mới nhất ─────────────────────────────────────────
def test_lay_dung_nam_moi_nhat():
    df = bang_kbs()
    pe, nam = fc._row_latest(df, "pe_ratio", "p/e")
    assert (pe, nam) == (7.43, 2025), f"phải lấy 2025, nhận {(pe, nam)}"
    eps, nam_eps = fc._row_latest(df, "trailing_eps", "(eps)")
    assert (eps, nam_eps) == (3229.59, 2025)
    beta, _ = fc._row_latest(df, "beta")
    assert beta == 0.84
    print(f"PASS  lấy đúng năm mới nhất: P/E {pe}, EPS {eps}, Beta {beta} (2025)")


def test_tu_khoa_rieng_nhat_dat_truoc():
    """`(eps)` không được khớp nhầm dòng BVPS hay dòng khác."""
    df = bang_kbs()
    eps, _ = fc._row_latest(df, "trailing_eps", "(eps)")
    assert eps == 3229.59, "khớp nhầm chỉ tiêu khác"
    print("PASS  từ khoá riêng nhất khớp đúng dòng EPS")


def test_khong_co_chi_tieu_thi_tra_none():
    """Không tìm thấy thì trả None — KHÔNG đoán, không lấy dòng gần đúng."""
    df = bang_kbs()
    assert fc._row_latest(df, "khong_ton_tai_dau_ca") == (None, None)
    print("PASS  không tìm thấy chỉ tiêu -> (None, None), không đoán")


# ── 3. Chốt độ tươi — phần quan trọng nhất ───────────────────────────
def test_bo_chi_so_qua_cu():
    """Sửa được cột trùng tên mà không chặn dữ liệu cũ thì giao diện sẽ
    hiện P/E 2018 như chỉ số hôm nay — tệ hơn hiện `—`."""
    loc, da_bo = fc._loc_qua_cu(
        {"P/E": (13.24, 2018), "EPS": (None, None), "Beta": (0.84, 2025)},
        nam_min=2024)
    assert loc["P/E"] is None, "P/E 2018 phải bị bỏ"
    assert loc["Beta"] == 0.84, "Beta 2025 phải được giữ"
    assert da_bo == ["P/E (2018)"], f"phải nói rõ đã bỏ gì: {da_bo}"
    print(f"PASS  bỏ P/E (2018), giữ Beta (2025), báo rõ: {da_bo}")


def test_giu_nam_lien_truoc():
    """Báo cáo năm chốt sau vài tháng — năm liền trước là bình thường,
    không được coi là cũ."""
    loc, da_bo = fc._loc_qua_cu({"P/E": (7.43, 2025)}, nam_min=2024)
    assert loc["P/E"] == 7.43 and da_bo == []
    print("PASS  số liệu năm liền trước vẫn được giữ")


def test_thieu_nam_thi_khong_bo_nham():
    """Bảng dạng cột không có năm -> nam=None. Không được bỏ oan."""
    loc, da_bo = fc._loc_qua_cu({"P/E": (7.43, None)}, nam_min=2024)
    assert loc["P/E"] == 7.43 and da_bo == []
    print("PASS  không biết năm -> giữ nguyên, không bỏ oan")


def test_nguong_do_tuoi_hop_ly():
    """NAM_TOI_DA_CU phải đủ rộng cho báo cáo năm chốt chậm, đủ hẹp để
    chặn dữ liệu hỏng kiểu 2018."""
    assert 1 <= fc.NAM_TOI_DA_CU <= 3, fc.NAM_TOI_DA_CU
    import datetime as dt
    nam_min = dt.date.today().year - fc.NAM_TOI_DA_CU
    assert nam_min <= 2025, "ngưỡng không được loại số liệu 2025"
    assert nam_min > 2018, "ngưỡng phải loại được số liệu 2018"
    print(f"PASS  ngưỡng độ tươi: nhận từ {nam_min} trở lại đây")


# ── 4. Chuỗi nhiều năm cũng dùng vị trí cột ──────────────────────────
def test_row_series_dung_vi_tri_cot():
    df = bang_kbs()
    nam, gia_tri = fc._row_series(df, "pe_ratio", "p/e")
    assert nam == ["2023", "2024", "2025"], nam
    assert gia_tri == [5.47, 6.49, 7.43], gia_tri
    print(f"PASS  chuỗi nhiều năm đúng thứ tự tăng dần: {list(zip(nam, gia_tri))}")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n===== {len(fns) - failed}/{len(fns)} test PASS =====")
    sys.exit(1 if failed else 0)
