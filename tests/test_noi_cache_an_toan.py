"""BƯỚC 180 — nối cache giá AN TOÀN: không trộn hai cơ sở giá, không ghi nến
chưa đóng.

Ca gốc (số do LEADER đo ở máy 12/10/2026, dữ liệu thật; đám mây không có
`vnstock` nên không tái lập): nguồn ĐIỀU CHỈNH LÙI cả lịch sử sau sự kiện
quyền. `extend_history` cũ giữ dòng CŨ khi trùng ngày và nối dòng MỚI cho
ngày chưa có. Với HDB: dòng cũ (≤ 03/09) ở cơ sở chưa điều chỉnh, dòng mới
04/09 ở cơ sở đã nhân 0,77 ⇒ bậc −23% GIẢ ở ngày không có sự kiện nào.

Mọi đáp số dưới đây là SỐ tính tay trên dữ liệu giả (phép tính ở chú thích).
Không mạng, không đồng hồ thật, không ghi vào `backtest/cache` của repo.
"""
from __future__ import annotations

import ast
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import extend_history as eh  # noqa: E402
import market_filter as mf  # noqa: E402
from backtest import data as bt  # noqa: E402
from data_quality import VN_TZ  # noqa: E402

#: Sau giờ đóng cửa của một ngày làm việc xa hơn mọi chuỗi giả bên dưới:
#: không nến nào là "hôm nay".
SAU_DONG = datetime(2026, 9, 30, 16, 0, tzinfo=VN_TZ)


def _bd(tu: str, n: int) -> list[str]:
    return list(pd.bdate_range(tu, periods=n).strftime("%Y-%m-%d"))


def _df(ngay: list[str], close: list[float]) -> pd.DataFrame:
    assert len(ngay) == len(close)
    return pd.DataFrame({
        "time": ngay, "open": close, "high": close, "low": close,
        "close": close, "volume": [1000] * len(ngay)})


def _dung(monkeypatch, tmp_path, ma: str, cu: pd.DataFrame, moi):
    monkeypatch.setattr(bt, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(bt, "fetch_one", lambda s, a, b, **k: moi)
    cu.to_csv(tmp_path / f"{ma}.csv", index=False)
    return tmp_path / f"{ma}.csv"


def _chay(ma="TST", start="2026-07-01", end="2026-09-30", **kw):
    bao: dict = {}
    kw.setdefault("bay_gio", SAU_DONG)
    doi = bt.extend_history([ma], start, end, bao_cao=bao, **kw)
    return doi, bao


# ───────────────────────── so_co_so — hàm thuần ─────────────────────────

def test_a_cung_co_so_hop_nhat_nhu_cu(tmp_path, monkeypatch):
    """Cũ 6 ngày (08-03 → 08-10), mới 7 ngày (thêm 08-11), khớp tuyệt đối.
    Ngày trùng đã đóng = 6 − 1 (bỏ ngày cuối của cũ) = 5; 0 ngày lệch.
    Hợp nhất = 7 dòng, close 10…16."""
    ngay = _bd("2026-08-03", 7)
    cu = _df(ngay[:6], [10, 11, 12, 13, 14, 15])
    moi = _df(ngay, [10, 11, 12, 13, 14, 15, 16])
    kq = bt.so_co_so(cu, moi, SAU_DONG)
    assert kq.nhan == bt.CUNG_CO_SO
    assert (kq.so_ngay_trung, kq.so_ngay_lech) == (5, 0)
    assert kq.ty_le_min == 1.0 and kq.ty_le_max == 1.0

    f = _dung(monkeypatch, tmp_path, "TST", cu, moi)
    doi, bao = _chay()
    assert "TST" in doi and bao["TST"].nhan == bt.CUNG_CO_SO
    sau = pd.read_csv(f)
    assert list(sau["time"]) == ngay
    assert list(sau["close"]) == [10, 11, 12, 13, 14, 15, 16]


def test_b_ca_HDB_mat_cung_co_so_file_cu_khong_doi_mot_byte(
        tmp_path, monkeypatch, capsys):
    """Dựng lại NGUYÊN VĂN ca HDB: mọi ngày trùng của mới = cũ × 0,77.

    Cũ 8 ngày close 100…114 bước 2; mới 9 ngày = 0,77 × (100…114) rồi ngày
    thứ 9 = 88 (= 0,77 × 114,29; cơ sở MỚI). Bản cũ nối được ngày 9 vào đuôi
    cơ sở cũ ⇒ bậc 114 → 88 = −22,8% giả. Ngày trùng đã đóng = 8 − 1 = 7,
    cả 7 lệch 23%.
    """
    ngay = _bd("2026-08-03", 9)
    gia_cu = [100, 102, 104, 106, 108, 110, 112, 114]
    cu = _df(ngay[:8], gia_cu)
    moi = _df(ngay, [round(g * 0.77, 4) for g in gia_cu] + [88.0])

    kq = bt.so_co_so(cu, moi, SAU_DONG)
    assert kq.nhan == bt.LECH_CO_SO
    assert (kq.so_ngay_trung, kq.so_ngay_lech) == (7, 7)
    assert kq.ty_le_min == pytest.approx(0.77, abs=1e-9)
    assert kq.ty_le_max == pytest.approx(0.77, abs=1e-9)
    assert (kq.ngay_lech_dau, kq.ngay_lech_cuoi) == (ngay[0], ngay[6])

    f = _dung(monkeypatch, tmp_path, "HDB", cu, moi)
    truoc = f.read_bytes()
    doi, bao = _chay("HDB")
    assert doi == {}, "mã LECH_CO_SO không được tính là đã đổi"
    assert bao["HDB"].nhan == bt.LECH_CO_SO
    assert f.read_bytes() == truoc, "file cũ phải giữ nguyên TỪNG BYTE"
    # dòng báo: mã, số ngày lệch / số ngày trùng, tỷ lệ min/max
    ra = capsys.readouterr().out
    assert "HDB" in ra and "LECH_CO_SO" in ra and "7/7" in ra
    assert "min 0.770000" in ra and "max 0.770000" in ra
    assert "KHÔNG hợp nhất" in ra


def test_c_mot_ngay_le_lech_0_03_phan_tram_la_sua_so(tmp_path, monkeypatch):
    """Một ngày giữa chuỗi: cũ 100, mới 100,03 (lệch 0,03% < 0,1%) → CUNG."""
    ngay = _bd("2026-08-03", 7)
    gia = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    cu = _df(ngay[:6], gia)
    moi_gia = [100.03, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]
    kq = bt.so_co_so(cu, _df(ngay, moi_gia), SAU_DONG)
    assert kq.nhan == bt.CUNG_CO_SO and kq.so_ngay_lech == 0
    assert kq.ty_le_max == pytest.approx(1.0003, abs=1e-9)


def test_c2_ngay_le_lech_lon_van_la_mot_ngay_le():
    """Một ngày lệch 5% giữa chuỗi vẫn là CUNG (< 2 ngày); hai ngày thì LECH."""
    ngay = _bd("2026-08-03", 7)
    gia = [100.0] * 6
    cu = _df(ngay[:6], gia)
    mot = _df(ngay, [105.0, 100, 100, 100, 100, 100, 100])
    hai = _df(ngay, [105.0, 105.0, 100, 100, 100, 100, 100])
    assert bt.so_co_so(cu, mot, SAU_DONG).nhan == bt.CUNG_CO_SO
    kq = bt.so_co_so(cu, hai, SAU_DONG)
    assert kq.nhan == bt.LECH_CO_SO and kq.so_ngay_lech == 2


def test_c3_ranh_gioi_ngưỡng_hai_phia():
    """Hai ngày cùng lệch 0,09% → CUNG; hai ngày lệch 0,11% → LECH.
    100 × 1,0009 = 100,09 (chênh 0,09 ≤ 0,1) ; 100 × 1,0011 = 100,11 (chênh
    0,11 > 0,1)."""
    ngay = _bd("2026-08-03", 6)
    cu = _df(ngay[:5], [100.0] * 5)
    nho = _df(ngay, [100.09, 100.09, 100, 100, 100, 100])
    lon = _df(ngay, [100.11, 100.11, 100, 100, 100, 100])
    assert bt.so_co_so(cu, nho, SAU_DONG).nhan == bt.CUNG_CO_SO
    assert bt.so_co_so(cu, lon, SAU_DONG).nhan == bt.LECH_CO_SO


def test_d_doan_co_tuc_tien_tru_0_5_phan_tram_la_LECH():
    """Mốc GDKHQ ở ngày thứ 7 của 10: mọi ngày TRƯỚC mốc mới = cũ × 0,995.

    Ngày trùng đã đóng = 10 − 1 = 9; 6 ngày đầu lệch 0,5% (> 0,1%), 3 ngày
    sau khớp ⇒ 6/9 lệch ⇒ LECH_CO_SO, tỷ lệ min 0,995.
    """
    ngay = _bd("2026-08-03", 11)
    gia = [100.0 + k for k in range(10)]                # 100…109
    cu = _df(ngay[:10], gia)
    moi_gia = [g * 0.995 for g in gia[:6]] + gia[6:] + [110.0]
    kq = bt.so_co_so(cu, _df(ngay, moi_gia), SAU_DONG)
    assert kq.nhan == bt.LECH_CO_SO
    assert (kq.so_ngay_trung, kq.so_ngay_lech) == (9, 6)
    assert kq.ty_le_min == pytest.approx(0.995, abs=1e-9)
    assert kq.ty_le_max == 1.0
    assert (kq.ngay_lech_dau, kq.ngay_lech_cuoi) == (ngay[0], ngay[5])


def test_e_ngay_cuoi_cu_la_nen_chua_dong_khong_tinh_va_lay_ban_moi(
        tmp_path, monkeypatch):
    """Ngày cuối của cũ lệch 0,45% (nến chưa đóng của lượt kéo giữa phiên),
    các ngày khác khớp: không được tính vào phép so → CUNG_CO_SO (5 ngày
    trùng, 0 lệch), và ngày cuối ấy lấy giá của lượt MỚI (22,20), không giữ
    22,30 — ca ACB."""
    ngay = _bd("2026-08-03", 7)
    cu = _df(ngay[:6], [20.0, 20.5, 21.0, 21.5, 22.0, 22.30])
    moi = _df(ngay, [20.0, 20.5, 21.0, 21.5, 22.0, 22.20, 22.4])
    kq = bt.so_co_so(cu, moi, SAU_DONG)
    assert kq.nhan == bt.CUNG_CO_SO
    assert (kq.so_ngay_trung, kq.so_ngay_lech) == (5, 0)

    f = _dung(monkeypatch, tmp_path, "ACB", cu, moi)
    doi, _ = _chay("ACB")
    assert "ACB" in doi
    sau = pd.read_csv(f).set_index("time")["close"]
    assert sau[ngay[5]] == 22.20, "ngày cuối cũ phải lấy bản MỚI (đã đóng)"
    assert sau[ngay[0]] == 20.0 and sau[ngay[4]] == 22.0
    assert len(sau) == 7


def test_e2_cac_ngay_trung_khac_van_giu_ban_cu(tmp_path, monkeypatch):
    """Chỉ ngày CUỐI của cũ được thay. Ngày trùng khác lệch 0,05% (sửa số lẻ,
    CUNG) vẫn giữ bản cũ — lý do giữ (sổ đã dùng dữ liệu cũ) còn đúng."""
    ngay = _bd("2026-08-03", 7)
    cu = _df(ngay[:6], [10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    moi = _df(ngay, [10.005, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    f = _dung(monkeypatch, tmp_path, "TST", cu, moi)
    _chay()
    assert pd.read_csv(f).set_index("time")["close"][ngay[0]] == 10.0


def test_g_khong_co_ngay_trung_la_KHONG_SO_DUOC(tmp_path, monkeypatch, capsys):
    """Cũ 08-03…08-10, mới 08-12…08-18: không ngày nào chung."""
    cu = _df(_bd("2026-08-03", 6), [10.0] * 6)
    moi = _df(_bd("2026-08-12", 5), [10.0] * 5)
    kq = bt.so_co_so(cu, moi, SAU_DONG)
    assert kq.nhan == bt.KHONG_SO_DUOC and kq.so_ngay_trung == 0

    f = _dung(monkeypatch, tmp_path, "TST", cu, moi)
    truoc = f.read_bytes()
    doi, bao = _chay()
    assert doi == {} and bao["TST"].nhan == bt.KHONG_SO_DUOC
    assert f.read_bytes() == truoc
    ra = capsys.readouterr().out
    assert "KHONG_SO_DUOC" in ra and "không có ngày trùng" in ra


def test_g2_chi_trung_dung_ngay_cuoi_cua_cu_cung_la_KHONG_SO_DUOC():
    """Ngày trùng duy nhất là ngày cuối của cũ (bị bỏ vì có thể là nến dở)."""
    ngay = _bd("2026-08-03", 6)
    cu = _df(ngay[:3], [10.0, 11.0, 12.0])
    moi = _df(ngay[2:], [999.0, 13.0, 14.0, 15.0])
    assert bt.so_co_so(cu, moi, SAU_DONG).nhan == bt.KHONG_SO_DUOC


def test_g3_thieu_cot_rong_va_gia_tri_vo_nghia_la_KHONG_SO_DUOC():
    ngay = _bd("2026-08-03", 6)
    ok = _df(ngay, [10.0] * 6)
    assert bt.so_co_so(None, ok, SAU_DONG).nhan == bt.KHONG_SO_DUOC
    assert bt.so_co_so(ok, ok.iloc[0:0], SAU_DONG).nhan == bt.KHONG_SO_DUOC
    assert bt.so_co_so(ok.drop(columns=["close"]), ok,
                       SAU_DONG).nhan == bt.KHONG_SO_DUOC
    assert bt.so_co_so(ok, ok.drop(columns=["time"]),
                       SAU_DONG).nhan == bt.KHONG_SO_DUOC
    # cũ toàn giá 0 / NaN: không ngày nào chia được
    xau = _df(ngay, [0.0, float("nan"), 0.0, -1.0, 0.0, 0.0])
    assert bt.so_co_so(xau, ok, SAU_DONG).nhan == bt.KHONG_SO_DUOC


def test_so_co_so_tu_bo_nen_chua_dong_cua_luot_moi():
    """10:00 ngày 09-09: nến 09-09 của lượt mới CHƯA đóng nên không vào phép
    so. Cũ có 4 ngày 09-07…09-10 (09-10 là ngày cuối, bị bỏ), mới có 09-07
    (khớp), 09-08 (lệch 5%) và 09-09 (lệch 5%, dở). Bỏ nến dở: chỉ 1 ngày
    lệch → CUNG_CO_SO. Không bỏ: 2 ngày lệch → LECH_CO_SO."""
    sang = datetime(2026, 9, 9, 10, 0, tzinfo=VN_TZ)
    cu = _df(["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10"],
             [100.0] * 4)
    moi = _df(["2026-09-07", "2026-09-08", "2026-09-09"], [100.0, 105.0, 105.0])
    kq = bt.so_co_so(cu, moi, sang)
    assert kq.nhan == bt.CUNG_CO_SO
    assert (kq.so_ngay_trung, kq.so_ngay_lech) == (2, 1)


def test_so_co_so_la_ham_thuan_khong_ghi_vao_dau_vao():
    ngay = _bd("2026-08-03", 7)
    cu = _df(ngay[:6], [10.0] * 6)
    moi = _df(ngay, [10.0] * 7)
    cu0, moi0 = cu.copy(), moi.copy()
    bt.so_co_so(cu, moi, SAU_DONG)
    bt.hop_nhat(cu, moi)
    pd.testing.assert_frame_equal(cu, cu0)
    pd.testing.assert_frame_equal(moi, moi0)


# ───────────────────── nến chưa đóng không vào cache ─────────────────────

def test_f_nen_hom_nay_chua_dong_khong_duoc_ghi(tmp_path, monkeypatch):
    """Thứ Tư 2026-09-09 là hôm nay. 10:00 → nến 09-09 CHƯA đóng → không
    ghi; 15:30 → ĐÃ đóng (GIO_NEN_DA_DONG = 15:30) → ghi."""
    ngay = _bd("2026-08-31", 8)                       # 08-31 … 09-09
    assert ngay[-1] == "2026-09-09"
    cu = _df(ngay[:6], [10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    moi = _df(ngay, [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0])

    sang = datetime(2026, 9, 9, 10, 0, tzinfo=VN_TZ)
    f = _dung(monkeypatch, tmp_path, "TST", cu, moi)
    _chay(end="2026-09-09", bay_gio=sang)
    assert list(pd.read_csv(f)["time"])[-1] == "2026-09-08"

    chieu = datetime(2026, 9, 9, 15, 30, tzinfo=VN_TZ)
    cu.to_csv(f, index=False)
    _chay(end="2026-09-09", bay_gio=chieu)
    assert list(pd.read_csv(f)["time"])[-1] == "2026-09-09"


def test_f2_nen_cuoi_cua_cache_cu_ngay_hom_nay_chua_dong_cung_bi_bo(
        tmp_path, monkeypatch):
    """Cache cũ (ghi bởi bản trước) có nến 09-09 dở; lượt mới lúc 10:00 không
    có nến ấy. Hợp nhất giữ dòng cũ (vì mới không có) — hàng rào cuối phải
    bỏ nó. Cũ bắt đầu 08-17, `start` 07-01 → buộc kéo lại."""
    ngay_cu = _bd("2026-08-17", 18)                    # … 09-09
    assert ngay_cu[-1] == "2026-09-09"
    cu = _df(ngay_cu, [10.0 + k for k in range(18)])
    ngay_moi = _bd("2026-07-01", 50)                   # … 09-08
    assert ngay_moi[-1] == "2026-09-08"
    gia_moi = {d: 10.0 + k for k, d in enumerate(ngay_cu)}
    moi = _df(ngay_moi, [gia_moi.get(d, 5.0) for d in ngay_moi])
    sang = datetime(2026, 9, 9, 10, 0, tzinfo=VN_TZ)
    f = _dung(monkeypatch, tmp_path, "TST", cu, moi)
    doi, bao = _chay(end="2026-09-09", bay_gio=sang)
    assert bao["TST"].nhan == bt.CUNG_CO_SO
    sau = pd.read_csv(f)
    assert sau["time"].iloc[-1] == "2026-09-08"
    assert sau["time"].iloc[0] == ngay_moi[0]


def test_luot_moi_chi_co_nen_chua_dong_thi_khong_ghi_gi(tmp_path, monkeypatch,
                                                         capsys):
    """Mã mới (chưa có cache) mà lượt kéo lúc 10:00 chỉ có nến hôm nay dở:
    không tạo file (và không nổ ở `merged.iloc[0]`). Có cache cũ + `thay_ca_chuoi`
    thì file cũ giữ nguyên."""
    sang = datetime(2026, 9, 9, 10, 0, tzinfo=VN_TZ)
    monkeypatch.setattr(bt, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(bt, "fetch_one",
                        lambda s, a, b, **k: _df(["2026-09-09"], [5.0]))
    doi, _ = _chay("MOI", start="2026-09-01", end="2026-09-09", bay_gio=sang)
    assert doi == {} and not (tmp_path / "MOI.csv").exists()
    assert "chỉ có nến chưa đóng" in capsys.readouterr().out

    cu = _df(["2026-09-07", "2026-09-08"], [1.0, 2.0])
    f = _dung(monkeypatch, tmp_path, "CU", cu,
              _df(["2026-09-09"], [5.0]))
    truoc = f.read_bytes()
    doi, _ = _chay("CU", start="2026-09-01", end="2026-09-09", bay_gio=sang,
                   thay_ca_chuoi=True)
    assert doi == {} and f.read_bytes() == truoc


def test_bo_nen_dang_do_ham_thuan():
    ngay = ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10"]
    df = _df(ngay, [1.0, 2.0, 3.0, 4.0])
    sang = datetime(2026, 9, 9, 10, 0, tzinfo=VN_TZ)
    # 09-10 là nến TƯƠNG LAI, 09-09 là hôm nay chưa đóng → bỏ cả hai
    assert list(bt.bo_nen_dang_do(df, sang)["time"]) == ngay[:2]
    # 15:29 chưa đóng, 15:30 đã đóng
    ngay2 = ngay[:3]
    d2 = _df(ngay2, [1.0, 2.0, 3.0])
    assert len(bt.bo_nen_dang_do(
        d2, datetime(2026, 9, 9, 15, 29, tzinfo=VN_TZ))) == 2
    assert len(bt.bo_nen_dang_do(
        d2, datetime(2026, 9, 9, 15, 30, tzinfo=VN_TZ))) == 3
    # idempotent và giữ nguyên Timestamp
    ts = df.assign(time=pd.to_datetime(df["time"]))
    r = bt.bo_nen_dang_do(ts, sang)
    assert pd.api.types.is_datetime64_any_dtype(r["time"])
    assert len(bt.bo_nen_dang_do(r, sang)) == len(r)
    # rỗng / thiếu cột không nổ
    assert len(bt.bo_nen_dang_do(df.iloc[0:0], sang)) == 0
    assert bt.bo_nen_dang_do(df.drop(columns=["time"]), sang) is not None


def test_download_khong_ghi_nen_chua_dong(tmp_path, monkeypatch):
    ngay = ["2026-09-07", "2026-09-08", "2026-09-09"]
    monkeypatch.setattr(bt, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(bt, "fetch_one",
                        lambda s, a, b, **k: _df(ngay, [1.0, 2.0, 3.0]))
    sang = datetime(2026, 9, 9, 10, 0, tzinfo=VN_TZ)
    bt.download(["TST"], "2026-09-01", "2026-09-09", bay_gio=sang)
    assert list(pd.read_csv(tmp_path / "TST.csv")["time"]) == ngay[:2]
    bt.download(["TST"], "2026-09-01", "2026-09-09", force=True,
                bay_gio=datetime(2026, 9, 9, 15, 30, tzinfo=VN_TZ))
    assert list(pd.read_csv(tmp_path / "TST.csv")["time"]) == ngay


def test_extend_history_chi_hoi_dong_ho_MOT_lan(tmp_path, monkeypatch):
    """Ba mã, `bay_gio` không truyền: `now_vn` được gọi đúng một lần."""
    dem = []
    sang = datetime(2026, 9, 30, 16, 0, tzinfo=VN_TZ)
    monkeypatch.setattr(bt, "now_vn", lambda: dem.append(1) or sang)
    monkeypatch.setattr(bt, "CACHE_DIR", tmp_path)
    ngay = _bd("2026-08-03", 5)
    monkeypatch.setattr(bt, "fetch_one",
                        lambda s, a, b, **k: _df(ngay, [1.0] * 5))
    bt.extend_history(["AAA", "BBB", "CCC"], "2026-08-01", "2026-09-30")
    assert len(dem) == 1


def test_market_filter_khong_ghi_nen_chua_dong_vao_cache_vnindex(
        tmp_path, monkeypatch):
    """Cache VNINDEX rỗng → tải mạng → ghi cache nhưng bỏ nến dở."""
    ngay = ["2026-09-07", "2026-09-08", "2026-09-09"]
    monkeypatch.setattr(bt, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(bt, "fetch_one",
                        lambda s, a, b, **k: _df(ngay, [1.0, 2.0, 3.0]))
    monkeypatch.setattr(mf, "now_vn",
                        lambda: datetime(2026, 9, 9, 10, 0, tzinfo=VN_TZ))
    mf.get_vni_df.cache_clear()
    try:
        df = mf.get_vni_df()
    finally:
        mf.get_vni_df.cache_clear()
    assert list(pd.read_csv(tmp_path / "VNINDEX.csv")["time"]) == ngay[:2]
    assert df is not None and len(df) == 3, (
        "thứ tự ưu tiên cache/mạng và giá trị trả về không đổi")


def test_h_thay_ca_chuoi_ghi_de_bang_dung_luot_moi(tmp_path, monkeypatch, capsys):
    """Cùng ca (b). `thay_ca_chuoi=True` → file = đúng lượt mới (9 dòng, close
    0,77 × cũ rồi 88) — kể cả khi mã 'đã đủ và đã tươi' (cũ bắt đầu 08-03,
    start 08-01 ⇒ đủ lịch sử; end 08-13 ⇒ đuôi cũ 1 ngày ⇒ bình thường BỎ QUA)."""
    ngay = _bd("2026-08-03", 9)
    gia_cu = [100, 102, 104, 106, 108, 110, 112, 114]
    cu = _df(ngay[:8], gia_cu)
    gia_moi = [round(g * 0.77, 4) for g in gia_cu] + [88.0]
    moi = _df(ngay, gia_moi)
    f = _dung(monkeypatch, tmp_path, "HDB", cu, moi)

    doi, bao = _chay("HDB", start="2026-08-01", end="2026-08-13",
                     thay_ca_chuoi=True)
    sau = pd.read_csv(f)
    assert "HDB" in doi
    assert list(sau["time"]) == ngay
    assert list(sau["close"]) == gia_moi
    ra = capsys.readouterr().out
    assert "THAY CẢ CHUỖI" in ra and "không tái lập" in ra.replace("KHÔNG", "không")


def test_h2_thay_ca_chuoi_noi_ro_so_phien_cu_bi_mat(tmp_path, monkeypatch, capsys):
    """Lượt mới NGẮN hơn cache cũ (nguồn giới hạn độ sâu): in rõ số phiên đầu
    bị mất — đúng sự cố VNINDEX 1.724 → 1.655 phiên."""
    ngay = _bd("2026-06-01", 40)
    cu = _df(ngay, [10.0] * 40)
    moi = _df(ngay[10:], [10.0] * 30)
    _dung(monkeypatch, tmp_path, "TST", cu, moi)
    _chay(start="2026-06-01", thay_ca_chuoi=True)
    assert "MẤT 10 phiên đầu" in capsys.readouterr().out


def test_mac_dinh_thay_ca_chuoi_la_False():
    cay = ast.parse((GOC / "backtest" / "data.py").read_text(encoding="utf-8"))
    ham = next(n for n in cay.body
               if isinstance(n, ast.FunctionDef) and n.name == "extend_history")
    ten = [a.arg for a in ham.args.kwonlyargs]
    mac = dict(zip(ten, ham.args.kw_defaults))
    assert "thay_ca_chuoi" in mac
    assert isinstance(mac["thay_ca_chuoi"], ast.Constant)
    assert mac["thay_ca_chuoi"].value is False


def test_ma_moi_chua_co_cache_van_tai_binh_thuong(tmp_path, monkeypatch):
    ngay = _bd("2026-08-03", 5)
    monkeypatch.setattr(bt, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(bt, "fetch_one",
                        lambda s, a, b, **k: _df(ngay, [1, 2, 3, 4, 5.0]))
    doi, bao = _chay("MOI", start="2026-08-01")
    assert doi["MOI"][2] == 5 and "MOI" not in bao
    assert len(pd.read_csv(tmp_path / "MOI.csv")) == 5


# ───────────────────────── gác dây nối bằng AST ─────────────────────────

def _goi(node) -> set[str]:
    return {getattr(n.func, "id", getattr(n.func, "attr", ""))
            for n in ast.walk(node) if isinstance(n, ast.Call)}


def _ham(duong: str, ten: str):
    cay = ast.parse((GOC / duong).read_text(encoding="utf-8"))
    return next(n for n in ast.walk(cay)
                if isinstance(n, ast.FunctionDef) and n.name == ten)


def test_extend_history_that_su_goi_so_co_so_hop_nhat_va_bo_nen_dang_do():
    goi = _goi(_ham("backtest/data.py", "extend_history"))
    assert {"so_co_so", "hop_nhat", "bo_nen_dang_do", "now_vn"} <= goi


def test_hop_nhat_chi_duoc_goi_sau_khi_so_co_so_cho_CUNG_CO_SO():
    """`hop_nhat` trong `extend_history` nằm SAU một lần `continue` cho
    LECH_CO_SO — đọc thứ tự câu lệnh bằng AST."""
    ham = _ham("backtest/data.py", "extend_history")

    def dong(ten):
        return [n.lineno for n in ast.walk(ham) if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") == ten]

    # nhánh `if kq.nhan == LECH_CO_SO:` kết thúc bằng continue
    nhanh = [n for n in ast.walk(ham)
             if isinstance(n, ast.If) and "LECH_CO_SO" in ast.unparse(n.test)]
    assert len(nhanh) == 1
    assert isinstance(nhanh[0].body[-1], ast.Continue)
    assert len(dong("so_co_so")) == 1 and len(dong("hop_nhat")) == 1
    assert dong("so_co_so")[0] < nhanh[0].lineno < dong("hop_nhat")[0]


def test_download_va_market_filter_goi_bo_nen_dang_do():
    assert "bo_nen_dang_do" in _goi(_ham("backtest/data.py", "download"))
    assert "bo_nen_dang_do" in _goi(_ham("market_filter.py", "get_vni_df"))


def test_cli_extend_history_noi_dung_ba_tham_so():
    main = _ham("extend_history.py", "main")
    lenh = [n for n in ast.walk(main) if isinstance(n, ast.Call)
            and getattr(n.func, "id", "") == "extend_history"]
    assert len(lenh) == 1
    ten = {k.arg for k in lenh[0].keywords}
    assert {"thay_ca_chuoi", "bay_gio", "bao_cao"} <= ten
    src = ast.unparse(main)
    assert "--thay-ca-chuoi" in src and "now_vn()" in src
    assert hasattr(eh, "extend_history")
