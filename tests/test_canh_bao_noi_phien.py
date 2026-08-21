"""Test cảnh báo chạm SL/TP trong phiên.

Một cái chuông có hai cách hỏng, và cách thứ hai tệ hơn:

  · Không kêu khi đáng kêu  -> mất một cảnh báo.
  · Kêu oan                  -> vài lần là người ta tắt chuông, rồi lần
                                kêu thật cũng bị bỏ qua.

Nên các test dưới đây kiểm cả hai chiều, và đặc biệt kiểm cái bẫy đã ghi ở
NGUYEN-TAC-DO-LUONG.md: lệch hệ đơn vị làm `low <= stop_loss` LUÔN đúng,
tức kêu oan cho mọi mã, mọi phiên.

Và một bất biến không được phép mất: **module này KHÔNG đổi trạng thái sổ
lệnh.** Toàn bộ backtest đóng lệnh trên nến NGÀY; nếu sổ thật đóng theo nến
30 phút thì nó được đo bằng một thước khác với mọi kết quả ngoài mẫu.

Chạy offline: hàm tải nến bị thay bằng hàm giả.
"""
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import canh_bao_noi_phien as cb

VN = timezone(timedelta(hours=7))
BAY_GIO = datetime(2026, 8, 21, 14, 0, tzinfo=VN)


def _nen(gia: list, dau: str = "2026-08-21 09:00") -> pd.DataFrame:
    """Nến 30 phút. `gia` là [(low, high), ...] theo VNĐ."""
    t0 = pd.Timestamp(dau)
    return pd.DataFrame({
        "time": [t0 + pd.Timedelta(minutes=30 * i) for i in range(len(gia))],
        "open": [(l + h) / 2 for l, h in gia],
        "high": [h for _, h in gia],
        "low": [l for l, _ in gia],
        "close": [(l + h) / 2 for l, h in gia],
        "volume": [100_000] * len(gia),
    })


def _so(lenh: list) -> str:
    """Sổ lệnh tạm chỉ có bảng trades."""
    fd, p = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE trades (symbol TEXT, entry_date TEXT, "
              "entry_price REAL, stop_loss REAL, take_profit REAL, "
              "status TEXT)")
    for t in lenh:
        c.execute("INSERT INTO trades VALUES (?,?,?,?,?,?)",
                  (t["symbol"], "2026-08-01", t.get("entry_price", 22000.0),
                   t["stop_loss"], t["take_profit"], t.get("status", "OPEN")))
    c.commit()
    c.close()
    return p


def _don(p):
    if p and os.path.exists(p):
        os.remove(p)


# ─────────────────────────────────────────────────────────────────────
# 1. Kêu khi đáng kêu
# ─────────────────────────────────────────────────────────────────────

def test_cham_stop_loss_thi_bao_kem_thoi_diem_va_do_tre():
    lenh = {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}
    # Nến thứ ba (10:00) thủng 21.158.
    nen = _nen([(21600, 21900), (21500, 21800), (21100, 21400),
                (21200, 21500)])
    r = cb.kiem_mot(lenh, nen, BAY_GIO)

    assert r is not None, "thủng stop-loss mà không báo"
    assert r.loai == "SL"
    assert r.luc_nen == "2026-08-21 10:00", r.luc_nen
    assert abs(r.gia_cham - 21100.0) < 1e-6
    # 10:00 -> 14:00 là 240 phút.
    assert abs(r.tre_phut - 240) < 1, r.tre_phut
    print("PASS  chạm SL -> báo đúng nến, đúng giá, đúng độ trễ")


def test_lay_nen_DAU_TIEN_cham_chu_khong_phai_nen_gan_nhat():
    """Câu hỏi là 'chạm lúc nào'. Lấy nến gần nhất thì độ trễ báo ra
    nhỏ hơn thực tế — tức tự khen mình nhanh hơn mình vốn có."""
    lenh = {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}
    nen = _nen([(21600, 21900), (21000, 21300), (21050, 21350),
                (21020, 21320)])
    r = cb.kiem_mot(lenh, nen, BAY_GIO)
    assert r.luc_nen == "2026-08-21 09:30", (
        f"báo nến {r.luc_nen} — đáng lẽ nến đầu tiên chạm là 09:30")
    print("PASS  lấy nến ĐẦU TIÊN chạm, nên độ trễ là độ trễ thật")


def test_cham_take_profit_thi_bao_TP():
    lenh = {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}
    nen = _nen([(25800, 26100)])
    r = cb.kiem_mot(lenh, nen, BAY_GIO)
    assert r is not None and r.loai == "TP", r
    assert abs(r.gia_cham - 26100.0) < 1e-6
    print("PASS  chạm TP -> báo TP")


def test_cung_mot_nen_cham_ca_HAI_thi_lay_SL():
    """Bất biến 3. Trong một cây nến 30 phút vẫn không biết bên nào trước."""
    lenh = {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}
    nen = _nen([(21000, 26500)])
    r = cb.kiem_mot(lenh, nen, BAY_GIO)
    assert r.loai == "SL", f"chạm cả hai mà báo {r.loai} — trái bất biến 3"
    print("PASS  một nến chạm cả hai -> lấy SL (giả định bất lợi)")


# ─────────────────────────────────────────────────────────────────────
# 2. Im khi đáng im
# ─────────────────────────────────────────────────────────────────────

def test_chua_cham_gi_thi_KHONG_bao():
    lenh = {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}
    nen = _nen([(21550, 21900), (21600, 22750), (21700, 22100)])
    assert cb.kiem_mot(lenh, nen, BAY_GIO) is None
    print("PASS  chưa chạm -> im")


def test_khong_co_nen_thi_im_chu_khong_no():
    lenh = {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}
    assert cb.kiem_mot(lenh, _nen([]), BAY_GIO) is None
    assert cb.kiem_mot(lenh, None, BAY_GIO) is None
    print("PASS  không có nến -> im")


# ─────────────────────────────────────────────────────────────────────
# 3. Cái bẫy: lệch hệ đơn vị
# ─────────────────────────────────────────────────────────────────────

def test_lech_don_vi_thi_NO_chu_khong_bao_dong_gia():
    """Nến theo NGHÌN ĐỒNG, mốc theo VNĐ.

    Không chặn thì `low <= stop_loss` đúng với MỌI nến của MỌI mã — chuông
    kêu mỗi phiên cho mọi vị thế, và vài lần như thế là chuông bị tắt.
    """
    lenh = {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}
    nen_nghin = _nen([(21.5, 21.9), (21.6, 22.7)])
    try:
        cb.kiem_mot(lenh, nen_nghin, BAY_GIO)
    except cb.DonViLechError as e:
        assert "lệch" in str(e)
        print("PASS  lệch đơn vị -> nổ, không báo động giả")
        return
    raise AssertionError("nến nghìn đồng so với mốc VNĐ mà vẫn chạy")


def test_lech_don_vi_o_mot_ma_khong_lam_im_ca_chuong():
    """Một mã hỏng không được nuốt cảnh báo của mã khác."""
    p = _so([
        {"symbol": "XXX", "stop_loss": 21158.0, "take_profit": 26052.0},
        {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0},
    ])
    try:
        def tai(sym, ngay):
            if sym == "XXX":
                return _nen([(21.5, 21.9)])           # nghìn đồng -> lệch
            return _nen([(21000, 21400)])             # VNĐ, thủng SL

        r = cb.quet(p, "2026-08-21", BAY_GIO, tai)
        assert r["so_vi_the"] == 2
        assert len(r["canh_bao"]) == 1, r["canh_bao"]
        assert r["canh_bao"][0].symbol == "ACB"
        assert len(r["loi"]) == 1 and "XXX" in r["loi"][0]
        print("PASS  một mã lệch đơn vị -> ghi lỗi riêng, mã kia vẫn được báo")
    finally:
        _don(p)


def test_mot_ma_khong_tai_duoc_nen_khong_lam_im_ca_chuong():
    p = _so([
        {"symbol": "XXX", "stop_loss": 21158.0, "take_profit": 26052.0},
        {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0},
    ])
    try:
        def tai(sym, ngay):
            if sym == "XXX":
                raise RuntimeError("nguồn trả bảng rỗng")
            return _nen([(21000, 21400)])

        r = cb.quet(p, "2026-08-21", BAY_GIO, tai)
        assert len(r["canh_bao"]) == 1 and r["canh_bao"][0].symbol == "ACB"
        assert len(r["loi"]) == 1 and "RuntimeError" in r["loi"][0]
        print("PASS  một mã lỗi mạng -> ghi lỗi riêng, mã kia vẫn được báo")
    finally:
        _don(p)


# ─────────────────────────────────────────────────────────────────────
# 4. KHÔNG ĐỘNG VÀO SỔ  (bất biến quan trọng nhất của module này)
# ─────────────────────────────────────────────────────────────────────

def test_quet_KHONG_doi_gi_trong_so_lenh():
    """Sổ thật phải được đo bằng cùng một thước với mọi backtest: nến NGÀY.

    Nếu cái chuông này đóng lệnh theo nến 30 phút thì sổ thật không còn đối
    chiếu được với bất kỳ kết quả ngoài mẫu nào.
    """
    p = _so([{"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}])
    try:
        def doc_het():
            c = sqlite3.connect(p)
            try:
                return c.execute("SELECT * FROM trades").fetchall()
            finally:
                c.close()

        truoc = doc_het()
        r = cb.quet(p, "2026-08-21", BAY_GIO,
                    lambda s, n: _nen([(21000, 21400)]))
        assert len(r["canh_bao"]) == 1, "tiền đề sai: đáng lẽ có cảnh báo"
        assert doc_het() == truoc, "sổ lệnh đã bị thay đổi"
        print("PASS  có cảnh báo nhưng sổ lệnh không suy suyển")
    finally:
        _don(p)


def test_chi_quet_lenh_dang_MO():
    p = _so([
        {"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0},
        {"symbol": "FPT", "stop_loss": 21158.0, "take_profit": 26052.0,
         "status": "CLOSED"},
    ])
    try:
        r = cb.quet(p, "2026-08-21", BAY_GIO,
                    lambda s, n: _nen([(21000, 21400)]))
        assert r["so_vi_the"] == 1, f"quét {r['so_vi_the']} lệnh — có cả CLOSED"
        assert {c.symbol for c in r["canh_bao"]} == {"ACB"}
        print("PASS  chỉ quét lệnh đang mở")
    finally:
        _don(p)


# ─────────────────────────────────────────────────────────────────────
# 5. Workflow phải thật sự gọi
# ─────────────────────────────────────────────────────────────────────

def test_workflow_goi_dung_module():
    import io
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(goc, ".github", "workflows", "quet-so-lenh.yml")
    s = io.open(p, encoding="utf-8").read()
    assert "canh_bao_noi_phien" in s, "workflow chưa gọi module cảnh báo"
    print("PASS  workflow gọi đúng module")


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            ham()
    print("\nTẤT CẢ ĐỀU QUA")


# ─────────────────────────────────────────────────────────────────────
# 6. Chỉ xét nến của ĐÚNG hôm nay
# ─────────────────────────────────────────────────────────────────────

def test_bo_nen_cua_ngay_KHAC():
    """Nguồn trả dư ngày — không lọc thì báo lại chuyện hôm qua mỗi ngày.

    Đo thật 21/08/2026: `idd.tai("ACB", "2026-08-21", "2026-08-21", "30m")`
    trả 12 nến, có cả 2026-08-20 14:00, trong khi một phiên HOSE chỉ có 9
    nến 30 phút.
    """
    p = _so([{"symbol": "ACB", "stop_loss": 21158.0, "take_profit": 26052.0}])
    try:
        hom_qua = _nen([(21000, 21300)], dau="2026-08-20 14:00")   # thủng SL
        hom_nay = _nen([(21500, 21900)], dau="2026-08-21 09:00")   # chưa thủng
        gop = pd.concat([hom_qua, hom_nay], ignore_index=True)

        r = cb.quet(p, "2026-08-21", BAY_GIO, lambda s, n: gop)
        assert r["canh_bao"] == [], (
            f"báo lại chuyện hôm qua: {[c.dong_log() for c in r['canh_bao']]}")

        # Và vẫn báo khi chính hôm nay thủng.
        hom_nay_thung = _nen([(21000, 21300)], dau="2026-08-21 09:00")
        gop2 = pd.concat([hom_qua, hom_nay_thung], ignore_index=True)
        r2 = cb.quet(p, "2026-08-21", BAY_GIO, lambda s, n: gop2)
        assert len(r2["canh_bao"]) == 1
        assert r2["canh_bao"][0].luc_nen.startswith("2026-08-21"), \
            r2["canh_bao"][0].luc_nen
        print("PASS  bỏ nến ngày khác, vẫn báo khi hôm nay thủng")
    finally:
        _don(p)


def test_loc_dung_ngay_giu_nguyen_khi_rong():
    assert cb.loc_dung_ngay(None, "2026-08-21") is None
    assert len(cb.loc_dung_ngay(_nen([]), "2026-08-21")) == 0
    print("PASS  lọc ngày trên bảng rỗng -> không nổ")
