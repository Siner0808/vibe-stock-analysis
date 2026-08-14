"""Test tầng dữ liệu nến nội phiên.

Nguồn trả về LƯỚI 24/7, không phải chuỗi phiên. Đo trên ACB khung 30 phút,
một năm: 17.521 nến thô nhưng chỉ 2.242 nến thật — 87,2% là ô rỗng, gồm cả
03:00 sáng Chủ Nhật.

Hai bẫy phải chặn ở tầng này, vì lọt xuống dưới là hỏng hết:
  1. Ô rỗng của lưới 24/7 — đưa vào chỉ báo là tính cả giờ không giao dịch
  2. Giá theo NGHÌN ĐỒNG — so với stop_loss theo VNĐ thì `low <= sl` luôn đúng

Chạy offline:  python3 tests/test_intraday_data.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import intraday_data as idd


def luoi_24_7(ngay: str = "2026-08-03", gia: float = 22.2) -> pd.DataFrame:
    """Dựng lại đúng thứ nguồn trả về: 48 khung 30 phút cho CẢ ngày,
    chỉ 9 khung trong phiên là có giá."""
    moc = pd.date_range(f"{ngay} 00:00", f"{ngay} 23:30", freq="30min")
    trong_phien = {"09:00", "09:30", "10:00", "10:30", "11:00",
                   "13:00", "13:30", "14:00", "14:30"}
    hang = []
    for t in moc:
        co = t.strftime("%H:%M") in trong_phien
        hang.append({
            "time": t,
            "open": gia if co else None, "high": gia + 0.1 if co else None,
            "low": gia - 0.1 if co else None, "close": gia if co else None,
            "volume": 500_000 if co else 0,
        })
    return pd.DataFrame(hang)


# ── 1. Lọc rác của lưới 24/7 ─────────────────────────────────────────
def test_bo_o_rong_cua_luoi_24_7():
    tho = luoi_24_7()
    sach = idd.loc_rac(tho)
    assert len(tho) == 48, f"lưới phải có 48 khung, có {len(tho)}"
    assert len(sach) == 9, f"chỉ 9 nến trong phiên, nhận {len(sach)}"
    gio = sorted(sach["time"].dt.strftime("%H:%M"))
    assert gio == ["09:00", "09:30", "10:00", "10:30", "11:00",
                   "13:00", "13:30", "14:00", "14:30"], gio
    print(f"PASS  48 khung thô -> 9 nến thật ({100*39/48:.0f}% là rác, đã bỏ)")


def test_bo_nen_cuoi_tuan():
    """Lưới có cả thứ Bảy Chủ Nhật. Giá cuối tuần là thứ không tồn tại."""
    t7 = luoi_24_7("2026-08-08")     # thứ Bảy
    cn = luoi_24_7("2026-08-09")     # Chủ Nhật
    assert len(idd.loc_rac(t7)) == 0, "nến thứ Bảy phải bị bỏ"
    assert len(idd.loc_rac(cn)) == 0, "nến Chủ Nhật phải bị bỏ"
    print("PASS  nến thứ Bảy và Chủ Nhật bị loại hết")


def test_bo_ca_khi_nguon_tra_0_thay_vi_nan():
    """Nguồn có lúc trả 0 thay vì NaN cho khung ngoài giờ. Lọc theo NaN
    thôi là chưa đủ — 0 lọt qua sẽ thành giá bằng 0."""
    tho = luoi_24_7()
    tho.loc[tho["close"].isna(), ["open", "high", "low", "close"]] = 0.0
    sach = idd.loc_rac(tho)
    assert len(sach) == 9, f"khung ngoài giờ giá 0 phải bị bỏ, còn {len(sach)}"
    assert (sach["close"] > 0).all()
    print("PASS  khung ngoài giờ trả 0 thay vì NaN cũng bị loại")


def test_giu_nguyen_thu_tu_thoi_gian():
    tho = luoi_24_7().sample(frac=1, random_state=0)   # xáo trộn
    sach = idd.loc_rac(tho)
    assert sach["time"].is_monotonic_increasing, "phải sắp lại theo thời gian"
    print("PASS  dữ liệu xáo trộn -> sắp lại đúng thứ tự thời gian")


# ── 2. Đơn vị giá ────────────────────────────────────────────────────
def test_quy_nghin_dong_ve_vnd():
    """22.20 nghìn đồng phải thành 22.200 VNĐ. Không quy đổi thì
    `low <= stop_loss` luôn đúng và mọi lệnh đóng ngay phiên sau."""
    sach = idd._quy_ve_vnd(idd.loc_rac(luoi_24_7(gia=22.2)))
    assert 20_000 < sach["close"].iloc[0] < 25_000, sach["close"].iloc[0]
    assert (sach["high"] >= sach["low"]).all(), "quy đổi làm hỏng quan hệ H/L"
    print(f"PASS  22.20 nghìn đồng -> {sach['close'].iloc[0]:,.0f} VNĐ")


def test_gia_da_la_vnd_thi_khong_nhan_them():
    sach = idd._quy_ve_vnd(idd.loc_rac(luoi_24_7(gia=22_200)))
    assert 20_000 < sach["close"].iloc[0] < 25_000, "không được nhân 1000 lần nữa"
    print("PASS  giá đã là VNĐ -> giữ nguyên, không nhân thừa")


# ── 3. Chẩn đoán chất lượng ──────────────────────────────────────────
def test_bao_dong_khi_qua_it_phien():
    sach = idd.loc_rac(luoi_24_7())
    bc = idd.kiem_tra(sach, "30m")
    assert bc["dat"] is False and "quá ít" in bc["ghi_chu"]
    assert bc["so_phien"] == 1 and bc["nen_moi_phien"] == 9.0
    print(f"PASS  1 phiên -> đạt=False, nói rõ: {bc['ghi_chu']}")


def test_dat_khi_du_phien():
    khung = [luoi_24_7(str(d.date())) for d in
             pd.bdate_range("2026-06-01", periods=30)]
    sach = idd.loc_rac(pd.concat(khung, ignore_index=True))
    bc = idd.kiem_tra(sach, "30m")
    assert bc["dat"] is True, bc
    assert bc["so_phien"] == 30 and bc["nen_moi_phien"] == 9.0
    print(f"PASS  30 phiên × 9 nến -> đạt=True ({bc['so_nen']} nến)")


def test_phat_hien_phien_thung():
    day = luoi_24_7("2026-06-01")
    thung = luoi_24_7("2026-06-02").head(20)      # phiên chỉ còn 2 nến
    sach = idd.loc_rac(pd.concat([day, thung], ignore_index=True))
    bc = idd.kiem_tra(sach, "30m")
    assert "2026-06-02" in bc["phien_thung"], bc["phien_thung"]
    print(f"PASS  bắt được phiên thủng dữ liệu: {bc['phien_thung']}")


# ── 4. Gộp về nến ngày để đối chiếu ──────────────────────────────────
def test_gop_noi_phien_thanh_nen_ngay():
    """Hai nguồn cùng mô tả một phiên thì phải khớp. Có phép gộp này mới
    phát hiện được khi một trong hai sai."""
    moc = pd.date_range("2026-08-03 09:00", periods=9, freq="30min")
    df = pd.DataFrame({
        "time": moc,
        "open":  [22.0, 22.1, 22.3, 22.2, 22.4, 22.5, 22.3, 22.2, 22.1],
        "high":  [22.2, 22.4, 22.5, 22.4, 22.6, 22.7, 22.5, 22.4, 22.3],
        "low":   [21.9, 22.0, 22.2, 22.1, 22.3, 22.4, 22.2, 22.1, 22.0],
        "close": [22.1, 22.3, 22.2, 22.4, 22.5, 22.3, 22.2, 22.1, 22.2],
        "volume": [100] * 9,
    })
    ngay = idd.gop_theo_phien(df)
    assert len(ngay) == 1
    r = ngay.iloc[0]
    assert r["open"] == 22.0, "open phải là nến ĐẦU phiên"
    assert r["close"] == 22.2, "close phải là nến CUỐI phiên"
    assert r["high"] == 22.7 and r["low"] == 21.9
    assert r["volume"] == 900
    print(f"PASS  9 nến -> 1 nến ngày: O{r['open']} H{r['high']} "
          f"L{r['low']} C{r['close']} V{r['volume']:.0f}")


# ── 5. Không đoán, không lấp ─────────────────────────────────────────
def test_khung_sai_thi_no():
    try:
        idd.tai("ACB", "2026-01-01", "2026-08-01", khung="7m")
        raise AssertionError("khung không hợp lệ mà vẫn chạy")
    except idd.IntradayError as e:
        assert "không hợp lệ" in str(e)
    print("PASS  khung lạ -> IntradayError, không đoán khung gần nhất")


def test_bang_rong_tra_ve_bang_rong_dung_cot():
    sach = idd.loc_rac(pd.DataFrame())
    assert sach.empty and list(sach.columns)[:5] == ["time", "open", "high", "low", "close"]
    bc = idd.kiem_tra(sach, "30m")
    assert bc["dat"] is False
    print("PASS  bảng rỗng -> rỗng đúng cấu trúc, đạt=False")


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
