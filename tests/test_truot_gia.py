"""Test mô hình trượt giá.

Trượt giá là thứ dễ mô hình hoá theo hướng có lợi cho mình nhất, vì không
ai kiểm chứng được ngay. Test ở đây khoá hai điều:

  1. Trượt LUÔN bất lợi — mua đắt hơn, bán rẻ hơn, không có ngoại lệ
  2. Điều kiện biên đúng — nuốt trọn nến thì tác động bằng biên độ nến

Chạy offline:  python3 tests/test_truot_gia.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import truot_gia as tg


def nen(high=22_600, low=22_400, volume=600_000) -> dict:
    return {"high": high, "low": low, "volume": volume}


# ── 1. Bước giá HOSE ─────────────────────────────────────────────────
def test_buoc_gia_theo_dai_gia_hose():
    """Đối chiếu với giá khớp thật: ACB 22.550 bước 50đ, VNM 57.900 bước 100đ."""
    assert tg.buoc_gia(8_500) == 10, "dưới 10.000 -> 10đ"
    assert tg.buoc_gia(12_500) == 50, "SHB ~12.500 -> 50đ"
    assert tg.buoc_gia(22_550) == 50, "ACB ~22.550 -> 50đ"
    assert tg.buoc_gia(49_950) == 50
    assert tg.buoc_gia(57_900) == 100, "VNM ~57.900 -> 100đ"
    assert tg.buoc_gia(120_000) == 100
    print("PASS  bước giá HOSE: <10k→10đ · 10–50k→50đ · ≥50k→100đ")


def test_san_khac_co_buoc_gia_khac():
    assert tg.buoc_gia(22_550, "HNX") == 100
    assert tg.buoc_gia(22_550, "UPCOM") == 100
    print("PASS  HNX/UPCOM dùng bước 100đ, không nhầm sang bảng HOSE")


# ── 2. Làm tròn LUÔN bất lợi ─────────────────────────────────────────
def test_lam_tron_luon_bat_loi():
    """Bất biến 3: giả định bất lợi. Làm tròn về gần nhất sẽ cho kết quả
    đẹp hơn thực tế một cách có hệ thống."""
    assert tg.lam_tron_bat_loi(22_510, tg.MUA) == 22_550, "mua phải tròn LÊN"
    assert tg.lam_tron_bat_loi(22_540, tg.BAN) == 22_500, "bán phải tròn XUỐNG"
    # ngay cả khi rất gần mức dưới, mua vẫn không được làm tròn xuống
    assert tg.lam_tron_bat_loi(22_501, tg.MUA) == 22_550
    assert tg.lam_tron_bat_loi(22_549, tg.BAN) == 22_500
    print("PASS  mua tròn lên, bán tròn xuống — không bao giờ về gần nhất")


def test_gia_dung_buoc_thi_giu_nguyen():
    assert tg.lam_tron_bat_loi(22_550, tg.MUA) == 22_550
    assert tg.lam_tron_bat_loi(22_550, tg.BAN) == 22_550
    print("PASS  giá đã đúng lưới bước giá -> giữ nguyên")


# ── 3. Trượt luôn đi ngược lợi ích ───────────────────────────────────
def test_mua_luon_dat_hon_ban_luon_re_hon():
    gia = 22_500
    m = tg.truot_gia(gia, tg.MUA, nen(), 10_000)
    b = tg.truot_gia(gia, tg.BAN, nen(), 10_000)
    assert m["gia_khop"] > gia, f"mua phải đắt hơn: {m['gia_khop']} vs {gia}"
    assert b["gia_khop"] < gia, f"bán phải rẻ hơn: {b['gia_khop']} vs {gia}"
    print(f"PASS  mục tiêu {gia:,} → mua {m['gia_khop']:,.0f} · "
          f"bán {b['gia_khop']:,.0f}")


def test_lenh_cang_lon_truot_cang_nhieu():
    gia = 22_500
    nho = tg.truot_gia(gia, tg.MUA, nen(), 1_000)
    lon = tg.truot_gia(gia, tg.MUA, nen(), 300_000)
    assert lon["gia_khop"] > nho["gia_khop"], "lệnh lớn phải trượt nhiều hơn"
    assert lon["phan_tac_dong"] > nho["phan_tac_dong"]
    print(f"PASS  1.000 CP trượt {nho['truot_vnd']:,.0f}đ · "
          f"300.000 CP trượt {lon['truot_vnd']:,.0f}đ")


def test_lenh_nho_tra_dung_MOT_buoc_gia():
    """Lệnh bé tí vẫn phải vượt chênh lệch mua-bán — nhưng ĐÚNG một bước,
    không phải hai.

    Bản đầu cộng một bước rồi lại làm tròn lên, thành ra tính hai lần: lệnh
    1 cổ phiếu trả 100đ thay vì 50đ. Với cổ phiếu 22.500đ đó là 0,22% mỗi
    lệnh — cùng độ lớn với toàn bộ lợi thế đang đo (+0,79%/lệnh). Bi quan
    quá mức cũng là đo sai.
    """
    r = tg.truot_gia(22_500, tg.MUA, nen(), 1)
    assert r["truot_vnd"] == 50, f"phải đúng 1 bước (50đ), nhận {r['truot_vnd']}"
    b = tg.truot_gia(22_500, tg.BAN, nen(), 1)
    assert b["truot_vnd"] == 50 and b["gia_khop"] == 22_450
    print(f"PASS  lệnh 1 CP trượt đúng {r['truot_vnd']:,.0f}đ — một bước, "
          f"không tính hai lần")


def test_khong_bao_gio_khop_dung_gia_muc_tieu():
    """Kể cả nến phẳng lì, khối lượng khổng lồ: không ai khớp ngay ở đúng
    giá mình muốn."""
    r = tg.truot_gia(22_500, tg.MUA, nen(high=22_500, low=22_500,
                                         volume=99_000_000), 100)
    assert r["gia_khop"] != 22_500
    assert r["truot_vnd"] == 50
    print("PASS  nến phẳng, lệnh tí hon -> vẫn trượt đúng một bước")


# ── 4. Điều kiện biên của quy luật căn bậc hai ───────────────────────
def test_nuot_tron_nen_thi_tac_dong_bang_bien_do():
    """Điều kiện biên kiểm tra được: tỷ trọng = 1 thì tác động = biên độ nến.
    Sai công thức là test này đỏ ngay."""
    n = nen(high=22_600, low=22_400, volume=500_000)
    r = tg.truot_gia(22_500, tg.MUA, n, 500_000)
    assert r["ty_trong_kl"] == 1.0
    assert abs(r["phan_tac_dong"] - 200) < 0.01, r["phan_tac_dong"]
    print(f"PASS  nuốt trọn nến → tác động {r['phan_tac_dong']:.0f}đ = "
          f"đúng biên độ nến (22.600−22.400)")


def test_khong_vuot_qua_toan_bo_nen():
    """Đặt lớn hơn cả nến cũng không làm tỷ trọng vượt 1 — nếu không, công
    thức căn bậc hai sẽ cho tác động vô lý."""
    r = tg.truot_gia(22_500, tg.MUA, nen(volume=100_000), 10_000_000)
    assert r["ty_trong_kl"] == 1.0
    print("PASS  lệnh lớn hơn cả nến -> tỷ trọng chặn ở 1.0")


def test_nen_bien_dong_manh_thi_truot_nhieu_hon():
    """Thang đo lấy từ biên độ nến thật, nên nó tự co giãn theo phiên."""
    yen = tg.truot_gia(22_500, tg.MUA, nen(22_550, 22_450), 60_000)
    manh = tg.truot_gia(22_500, tg.MUA, nen(23_000, 22_000), 60_000)
    assert manh["phan_tac_dong"] > yen["phan_tac_dong"] * 3
    print(f"PASS  nến biên độ 100đ → tác động {yen['phan_tac_dong']:.0f}đ · "
          f"biên độ 1.000đ → {manh['phan_tac_dong']:.0f}đ")


# ── 5. Không nuốt lỗi, không im lặng ─────────────────────────────────
def test_nen_khong_thanh_khoan_thi_noi_ro():
    """Nến không có khối lượng thì KHÔNG mô hình hoá được tác động. Phải
    nói ra, không được im lặng coi tác động = 0."""
    r = tg.truot_gia(22_500, tg.MUA, nen(volume=0), 10_000)
    assert r["phan_tac_dong"] == 0.0
    assert "không có khối lượng" in r["ghi_chu"]
    assert r["truot_vnd"] >= 50, "vẫn phải trả chênh lệch mua-bán"
    print(f"PASS  nến không thanh khoản -> nói rõ: {r['ghi_chu']}")


def test_huong_sai_thi_no():
    try:
        tg.truot_gia(22_500, "LONG", nen(), 1_000)
        raise AssertionError("hướng sai mà vẫn chạy")
    except ValueError as e:
        assert "huong" in str(e)
    print("PASS  hướng không hợp lệ -> ValueError, không đoán")


def test_bang_tach_khoan_du_thanh_phan():
    """Trả về bảng tách khoản chứ không phải một con số — một con số trần
    trụi sẽ nhanh chóng bị dùng như thể nó là sự thật đã đo."""
    r = tg.truot_gia(22_500, tg.MUA, nen(), 60_000)
    for k in ("gia_khop", "truot_vnd", "truot_pct", "phan_chenh_lech",
              "phan_tac_dong", "ty_trong_kl", "buoc_gia", "ghi_chu"):
        assert k in r, f"thiếu thành phần {k}"
    assert abs(r["truot_pct"] - 100*r["truot_vnd"]/22_500) < 1e-9
    print(f"PASS  bảng tách khoản đủ 8 thành phần, kiểm tra được")


# ── 6. Lô chẵn ───────────────────────────────────────────────────────
def test_lam_tron_lo_chan():
    assert tg.khoi_luong_hop_le(1_250) == 1_200, "phải tròn XUỐNG bội số 100"
    assert tg.khoi_luong_hop_le(99) == 0, "dưới một lô thì không đặt được"
    assert tg.khoi_luong_hop_le(100) == 100
    print("PASS  lô chẵn 100: 1.250→1.200 · 99→0")


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
