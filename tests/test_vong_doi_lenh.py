"""Test vòng đời lệnh.

Sổ lệnh giấy hiện coi mọi lệnh là khớp TOÀN BỘ ngay tại giá mong muốn. Đó
là giả định thầm lặng và nó luôn nghiêng về phía làm kết quả đẹp lên. Test
ở đây khoá bốn kết cục mà giả định đó bỏ qua:

  khớp một phần · sàn từ chối · hết phiên bị huỷ · giá đặt không với tới

Chạy offline:  python3 tests/test_vong_doi_lenh.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vong_doi_lenh as vd
from truot_gia import BAN, MUA


def nen(high=22_600, low=22_400, volume=600_000) -> dict:
    return {"high": high, "low": low, "volume": volume}


# ── 1. Từ chối ngay khi đặt ──────────────────────────────────────────
def test_tu_choi_lenh_le():
    """HOSE không nhận lệnh dưới một lô chẵn."""
    l = vd.dat_lenh("ACB", MUA, 50, 22_500, 22_500)
    assert l.trang_thai == vd.TU_CHOI and "lô chẵn" in l.ly_do
    print(f"PASS  lệnh 50 CP -> TỪ CHỐI: {l.ly_do[:44]}...")


def test_lam_tron_xuong_lo_chan():
    l = vd.dat_lenh("ACB", MUA, 1_250, 22_500, 22_500)
    assert l.khoi_luong == 1_200, "phải tròn XUỐNG, không được tròn lên"
    print(f"PASS  đặt 1.250 CP -> nhận {l.khoi_luong} CP (tròn xuống lô chẵn)")


def test_tu_choi_ngoai_bien_do():
    """Biên độ HOSE ±7%. Ngoài khoảng đó sàn không nhận."""
    tc = 22_500
    cao = vd.dat_lenh("ACB", MUA, 1_000, tc * 1.08, tc)
    thap = vd.dat_lenh("ACB", BAN, 1_000, tc * 0.92, tc)
    assert cao.trang_thai == vd.TU_CHOI and "biên độ" in cao.ly_do
    assert thap.trang_thai == vd.TU_CHOI
    trong = vd.dat_lenh("ACB", MUA, 1_000, tc * 1.06, tc)
    assert trong.trang_thai == vd.MOI, "trong biên độ thì phải nhận"
    print(f"PASS  +8% -> TỪ CHỐI · +6% -> nhận. {cao.ly_do[:40]}...")


def test_huong_sai_thi_no():
    try:
        vd.dat_lenh("ACB", "LONG", 1_000, 22_500, 22_500)
        raise AssertionError("hướng sai mà vẫn tạo được lệnh")
    except vd.LenhError:
        pass
    print("PASS  hướng không hợp lệ -> LenhError ngay khi đặt")


# ── 2. Khớp một phần — kết cục sổ hiện tại bỏ qua ───────────────────
def test_khop_mot_phan_khi_thanh_khoan_khong_du():
    """Lệnh 500.000 CP vào nến chỉ giao dịch 90.000 CP thì không thể khớp
    đủ. Sổ hiện tại vẫn ghi khớp đủ."""
    l = vd.dat_lenh("ACB", MUA, 500_000, 22_500, 22_500)
    r = vd.khop_trong_nen(l, nen(volume=90_000))
    assert l.trang_thai == vd.KHOP_MOT_PHAN
    assert r["khop"] == 9_000, f"10% của 90.000 = 9.000, nhận {r['khop']}"
    assert l.con_lai == 491_000
    print(f"PASS  muốn 500.000 CP, nến 90.000 CP -> khớp {r['khop']:,} "
          f"({l.trang_thai})")


def test_khop_du_qua_nhieu_nen():
    """Phần dư chờ nến sau. Giá bình quân là gia quyền, không phải trung
    bình cộng."""
    l = vd.dat_lenh("ACB", MUA, 30_000, 22_500, 22_500)
    for _ in range(4):
        vd.khop_trong_nen(l, nen(volume=100_000))
    assert l.trang_thai == vd.KHOP_DU and l.da_khop == 30_000
    assert l.gia_binh_quan is not None and l.gia_binh_quan > 22_500
    print(f"PASS  30.000 CP khớp đủ qua {l.so_nen_da_cho} nến, "
          f"giá bình quân {l.gia_binh_quan:,.0f}")


def test_chua_khop_thi_gia_binh_quan_la_None():
    """None chứ KHÔNG phải 0 — số 0 sẽ lẫn với một mức giá thật ở mọi
    phép tính phía sau."""
    l = vd.dat_lenh("ACB", MUA, 1_000, 22_500, 22_500)
    assert l.gia_binh_quan is None
    print("PASS  chưa khớp -> giá bình quân None, không phải 0")


# ── 3. Giá đặt không với tới nến ─────────────────────────────────────
def test_mua_gia_thap_hon_day_nen_thi_khong_khop():
    l = vd.dat_lenh("ACB", MUA, 1_000, 21_000, 22_500)
    r = vd.khop_trong_nen(l, nen(high=22_600, low=22_400))
    assert r["khop"] == 0 and "không với tới" in r["ly_do"]
    assert l.trang_thai == vd.MOI, "không khớp thì vẫn treo, không tự huỷ"
    print("PASS  mua 21.000 khi nến đáy 22.400 -> không khớp, lệnh vẫn treo")


def test_ban_gia_cao_hon_dinh_nen_thi_khong_khop():
    l = vd.dat_lenh("ACB", BAN, 1_000, 23_500, 22_500)
    r = vd.khop_trong_nen(l, nen(high=22_600, low=22_400))
    assert r["khop"] == 0
    print("PASS  bán 23.500 khi nến đỉnh 22.600 -> không khớp")


# ── 4. Hết phiên thì huỷ phần dư ─────────────────────────────────────
def test_het_phien_huy_phan_du():
    """Lệnh treo vô hạn là thứ không tồn tại — cuối phiên sàn xoá hết lệnh
    chưa khớp."""
    l = vd.dat_lenh("ACB", MUA, 900_000, 22_500, 22_500)
    for _ in range(vd.SO_NEN_CHO_TOI_DA):
        vd.khop_trong_nen(l, nen(volume=50_000))
    assert l.trang_thai == vd.HUY, l.trang_thai
    assert "huỷ phần dư" in l.ly_do and l.con_lai > 0
    print(f"PASS  hết {vd.SO_NEN_CHO_TOI_DA} nến -> HUỶ. {l.ly_do}")


def test_lenh_da_xong_thi_khong_khop_them():
    l = vd.dat_lenh("ACB", MUA, 1_000, 22_500, 22_500)
    vd.khop_trong_nen(l, nen(volume=600_000))
    assert l.trang_thai == vd.KHOP_DU
    r = vd.khop_trong_nen(l, nen(volume=600_000))
    assert r["khop"] == 0 and l.da_khop == 1_000, "không được khớp thêm"
    print("PASS  lệnh đã KHỚP_ĐỦ -> nến sau không khớp thêm")


# ── 5. Đối soát ý định với thực tế ───────────────────────────────────
def test_doi_soat_do_duoc_do_lech():
    """`lech_pct` là con số mà sổ lệnh hiện tại luôn coi bằng 0."""
    l = vd.dat_lenh("ACB", MUA, 30_000, 22_500, 22_500)
    for _ in range(4):
        vd.khop_trong_nen(l, nen(volume=100_000))
    d = vd.doi_soat(l)
    assert d["ty_le_khop"] == 1.0 and d["lech_pct"] > 0
    assert d["so_lan_khop"] >= 1
    print(f"PASS  đối soát: khớp {d['ty_le_khop']:.0%} qua {d['so_lan_khop']} "
          f"lần, lệch {d['lech_pct']:.3f}% so với giá muốn")


def test_doi_soat_lenh_bi_tu_choi():
    l = vd.dat_lenh("ACB", MUA, 50, 22_500, 22_500)
    d = vd.doi_soat(l)
    assert d["trang_thai"] == vd.TU_CHOI
    assert d["da_khop"] == 0 and d["lech_pct"] is None
    print("PASS  lệnh bị từ chối -> đối soát trả lệch=None, không phải 0")


def test_ty_le_khop_toi_da_doi_duoc():
    """Tỷ lệ khớp tối đa là GIẢ ĐỊNH — phải đổi được để thử độ nhạy."""
    a = vd.dat_lenh("ACB", MUA, 500_000, 22_500, 22_500)
    b = vd.dat_lenh("ACB", MUA, 500_000, 22_500, 22_500)
    vd.khop_trong_nen(a, nen(volume=100_000), ty_le_khop_toi_da=0.05)
    vd.khop_trong_nen(b, nen(volume=100_000), ty_le_khop_toi_da=0.20)
    assert b.da_khop == 4 * a.da_khop, (a.da_khop, b.da_khop)
    print(f"PASS  tỷ lệ 5% -> {a.da_khop:,} CP · 20% -> {b.da_khop:,} CP")


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
