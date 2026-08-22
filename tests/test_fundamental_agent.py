"""Test Agent Cơ Bản.

Chạy hoàn toàn OFFLINE bằng cách tiêm hàm tải bảng giả. Test gọi mạng thì
đỏ khi mất mạng và xanh khi nguồn trả rác — cả hai đều nói sai sự thật.

Bốn cái bẫy ghi ở đầu `fundamental_agent.py` đều có test riêng ở đây. Bẫy
mà không có test là bẫy sẽ quay lại.
"""
import pandas as pd
import pytest

import fundamental_agent as fa


def _bang(nam=2025, **dong):
    """Bảng chỉ số giả: một cột item_id, một cột năm."""
    return pd.DataFrame({"item_id": list(dong),
                         str(nam): [dong[k] for k in dong]})


def _dn(nam=2025, **ghi_de):
    """Doanh nghiệp thường, số liệu lành mạnh — nền để đột biến từng chỉ tiêu."""
    goc = dict(roe=20.0, roa=10.0, pe_ratio=14.0, pb_ratio=2.0,
               trailing_eps=5000.0, dividend_yield=2.0, net_margin=16.0,
               debt_to_equity=45.0, interest_coverage=12.0,
               equity_to_assets=50.0,
               profit_after_tax_for_shareholders_of_the_parent_company=18.0,
               owners_equity=12.0, total_assets=10.0)
    goc.update(ghi_de)
    return _bang(nam, **goc)


def _nh(nam=2025, **ghi_de):
    """Ngân hàng: KHÔNG có net_margin / debt_to_equity / interest_coverage."""
    goc = dict(roe=18.0, roa=1.8, pe_ratio=8.0, pb_ratio=1.3,
               trailing_eps=3200.0, dividend_yield=4.0,
               net_interest_margin_nim=3.8, equity_total_assets=9.5,
               profit_after_tax_for_shareholders_of_the_parent_company=10.0,
               owners_equity=13.0, total_assets=18.0)
    goc.update(ghi_de)
    return _bang(nam, **goc)


def _agent(bang):
    return fa.FundamentalAgent(tai_bang=lambda ma: bang)


# ─────────────────────────────────────────────────────────────────────
# 1. Không có dữ liệu là một kết quả hợp lệ — và không được thành số 50
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bang", [None, pd.DataFrame(), "không phải bảng"])
def test_khong_lay_duoc_bang_thi_available_False(bang):
    r = _agent(bang).analyze("XYZ")
    assert r["available"] is False
    assert r["diem"] is None, (
        "điểm phải là None. Một số 50 'trung tính' sẽ lặng lẽ được cộng vào "
        "công thức và trông y như đã tính tới yếu tố cơ bản")
    assert r["signals"] and r["signals"][0].startswith("⚠️")
    print(f"PASS  không có bảng -> available=False, diem=None")


def test_thieu_cot_item_id_thi_noi_ro_cau_truc_doi():
    r = _agent(pd.DataFrame({"ten": ["roe"], "2025": [20.0]})).analyze("XYZ")
    assert r["available"] is False
    assert "item_id" in r["signals"][0]
    print("PASS  thiếu item_id -> nói rõ cấu trúc nguồn đã đổi")


def test_bang_khong_co_cot_nam():
    r = _agent(pd.DataFrame({"item_id": ["roe"], "gia_tri": [20.0]})).analyze("XYZ")
    assert r["available"] is False
    assert "năm" in r["signals"][0]
    print("PASS  không có cột năm -> từ chối")


def test_so_lieu_qua_cu_thi_BO_chu_khong_hien():
    """Bẫy 4: số liệu năm 2019 trông y hệt số liệu hiện hành trên giao diện."""
    r = _agent(_dn(nam=2019)).analyze("XYZ")
    assert r["available"] is False
    assert "2019" in r["signals"][0]
    print(f"PASS  số liệu cũ -> bỏ · {r['signals'][0][:60]}…")


def test_bang_co_nam_nhung_khong_nhan_ra_chi_tieu_nao():
    r = _agent(_bang(2025, chi_tieu_la_hoac=1.0)).analyze("XYZ")
    assert r["available"] is False
    assert "tên dòng đã đổi" in r["signals"][0]
    print("PASS  đúng năm nhưng lạ tên dòng -> từ chối, không chấm bừa")


# ─────────────────────────────────────────────────────────────────────
# 2. Bẫy 1 — ba dòng "tăng trưởng" đội lốt số dư
# ─────────────────────────────────────────────────────────────────────

def test_ba_dong_tang_truong_duoc_hieu_la_phan_tram():
    """`total_assets` = -3,81 là TĂNG TRƯỞNG -3,81%, không phải tổng tài sản âm.

    Số đo thật trên FPT năm 2022. Đọc nhầm dòng này thành số dư thì mọi
    chỉ số dẫn xuất đều sai mà không có gì kêu lên.
    """
    c = fa.doc_chi_so("FPT", lambda ma: _dn(total_assets=-3.81,
                                            owners_equity=18.39,
                                            **{"profit_after_tax_for_shareholders"
                                               "_of_the_parent_company": 22.43}))
    assert c.tts_tang_pct == -3.81
    assert c.vcsh_tang_pct == 18.39
    assert c.ln_tang_pct == 22.43
    assert not hasattr(c, "tong_tai_san"), (
        "không được có trường nào mang nghĩa 'số dư' cho ba dòng này")
    print("PASS  ba dòng tăng trưởng mang hậu tố _tang_pct, đọc đúng nghĩa")


def test_loi_nhuan_suy_giam_manh_thi_canh_bao():
    r = _agent(_dn(**{"profit_after_tax_for_shareholders_of_the_parent"
                      "_company": -32.0})).analyze("XYZ")
    assert "lợi nhuận suy giảm mạnh" in r["canh_bao"]
    assert any("-32.0%" in s for s in r["signals"])
    print("PASS  lợi nhuận -32% -> cảnh báo, và in đúng dấu")


# ─────────────────────────────────────────────────────────────────────
# 3. Bẫy 2 — ngân hàng có bộ chỉ tiêu khác
# ─────────────────────────────────────────────────────────────────────

def test_nhan_ra_ngan_hang_va_khong_cham_bang_thuoc_doanh_nghiep():
    r = _agent(_nh()).analyze("ACB")
    assert r["nhom"] == fa.NGAN_HANG
    c = r["chi_so"]
    assert c.no_vay_tren_vcsh_pct is None and c.bien_ln_pct is None, (
        "ngân hàng không được mang chỉ tiêu của doanh nghiệp sản xuất")
    assert c.nim_pct == 3.8 and c.vcsh_tren_tts_pct == 9.5
    assert not any("Nợ vay/Vốn chủ" in s for s in r["signals"])
    assert any("NIM" in s for s in r["signals"])
    print("PASS  ngân hàng -> chấm bằng NIM và đệm vốn, không bằng D/E")


def test_ngan_hang_co_dong_debt_to_equity_van_khong_dung_no():
    """Vay tiền là NGHIỆP VỤ của ngân hàng, không phải dấu hiệu rủi ro.

    Nguồn có thể trả thêm dòng này bất cứ lúc nào; module phải bỏ qua nó
    theo nhóm ngành chứ không theo việc dòng đó có tồn tại hay không.
    """
    r = _agent(_nh(debt_to_equity=800.0)).analyze("ACB")
    assert r["nhom"] == fa.NGAN_HANG
    assert r["chi_so"].no_vay_tren_vcsh_pct is None
    assert "đòn bẩy cao" not in r["canh_bao"]
    print("PASS  ngân hàng có D/E 800% vẫn không bị coi là đòn bẩy cao")


def test_ngan_hang_dem_von_mong_thi_canh_bao():
    r = _agent(_nh(equity_total_assets=5.0)).analyze("XYZ")
    assert "đệm vốn mỏng" in r["canh_bao"]
    print("PASS  vốn chủ/tổng tài sản 5% -> cảnh báo đệm vốn mỏng")


def test_doanh_nghiep_thuong_nhan_dung_nhom():
    r = _agent(_dn()).analyze("FPT")
    assert r["nhom"] == fa.PHI_NGAN_HANG
    assert r["chi_so"].nim_pct is None
    assert any("Nợ vay/Vốn chủ" in s for s in r["signals"])
    print("PASS  doanh nghiệp thường -> chấm bằng D/E và biên lợi nhuận")


# ─────────────────────────────────────────────────────────────────────
# 4. Bẫy 3 — cột rỗng đội lốt số 0
# ─────────────────────────────────────────────────────────────────────

def test_khong_dung_roe_trailling():
    """Nguồn trả `roe_trailling = 0.0` cho MỌI mã, MỌI năm.

    Dùng nó thì mọi doanh nghiệp đều có ROE bằng 0 — một kết quả sai đều
    tay, tức là loại sai khó thấy nhất.
    """
    r = _agent(_dn(roe=22.0, roe_trailling=0.0, roa_trailling=0.0)).analyze("XYZ")
    assert r["chi_so"].roe_pct == 22.0
    assert any("ROE 22.0%" in s for s in r["signals"])
    assert "roe_trailling" in fa.KHONG_DUNG
    print("PASS  bỏ qua roe_trailling, đọc đúng roe = 22%")


# ─────────────────────────────────────────────────────────────────────
# 5. Chấm điểm
# ─────────────────────────────────────────────────────────────────────

def test_roe_am_bi_phat_nang_va_canh_bao():
    tot = _agent(_dn()).analyze("A")["diem"]
    xau = _agent(_dn(roe=-5.0)).analyze("B")
    assert xau["diem"] < tot
    assert "ROE âm" in xau["canh_bao"]
    print(f"PASS  ROE âm: {tot} -> {xau['diem']}, có cảnh báo")


def test_kha_nang_tra_lai_duoi_2_lan_thi_canh_bao():
    r = _agent(_dn(interest_coverage=1.2)).analyze("XYZ")
    assert "khả năng trả lãi dưới 2 lần" in r["canh_bao"]
    assert any("🔴" in s and "trả lãi" in s for s in r["signals"])
    print("PASS  trả lãi 1,2 lần -> cảnh báo đỏ")


def test_diem_luon_nam_trong_0_100():
    """Cộng dồn không chặn thì một mã đủ xấu sẽ ra điểm âm."""
    cuc_xau = _agent(_dn(roe=-40.0, interest_coverage=0.2, debt_to_equity=900.0,
                         net_margin=-20.0, pe_ratio=-3.0, pb_ratio=9.0,
                         **{"profit_after_tax_for_shareholders_of_the_parent"
                            "_company": -80.0})).analyze("X")
    cuc_tot = _agent(_dn(roe=45.0, interest_coverage=90.0, debt_to_equity=2.0,
                         net_margin=45.0, pe_ratio=4.0, pb_ratio=0.6,
                         **{"profit_after_tax_for_shareholders_of_the_parent"
                            "_company": 120.0})).analyze("Y")
    assert fa.DIEM_MIN <= cuc_xau["diem"] <= fa.DIEM_MAX
    assert fa.DIEM_MIN <= cuc_tot["diem"] <= fa.DIEM_MAX
    assert cuc_xau["diem"] < cuc_tot["diem"]
    print(f"PASS  điểm bị chặn: {cuc_xau['diem']} … {cuc_tot['diem']}")


def test_xep_hang_don_dieu_theo_diem():
    bac = [fa._xep_hang(d) for d in (10, 35, 50, 62, 80)]
    assert bac == ["XẤU", "YẾU", "TRUNG BÌNH", "KHÁ", "TỐT"], bac
    print("PASS  xếp hạng đơn điệu theo điểm")


def test_thieu_mot_chi_tieu_thi_bo_qua_chu_khong_coi_la_0():
    """Thiếu biên lợi nhuận KHÔNG được đọc thành biên lợi nhuận 0%."""
    day_du = _agent(_dn()).analyze("A")
    thieu = _agent(_dn(net_margin=None)).analyze("B")
    assert thieu["available"] is True
    assert thieu["diem"] > _agent(_dn(net_margin=0.0)).analyze("C")["diem"]
    print(f"PASS  thiếu chỉ tiêu ({thieu['diem']}) khác chỉ tiêu bằng 0")


def test_cham_hai_lan_ra_cung_ket_qua():
    """Bất biến 2: cùng đầu vào -> cùng đầu ra."""
    a = _agent(_dn()).analyze("XYZ")
    b = _agent(_dn()).analyze("XYZ")
    assert a["diem"] == b["diem"] and a["signals"] == b["signals"]
    print("PASS  tái lập")


def test_moi_tin_hieu_deu_neu_con_so():
    """Một dòng như '✅ Tài chính lành mạnh' không kiểm chứng được.

    Mỗi tín hiệu phải dẫn con số đã dùng để kết luận.
    """
    for r in (_agent(_dn()).analyze("A"), _agent(_nh()).analyze("B")):
        for s in r["signals"]:
            assert any(ch.isdigit() for ch in s), s
    print("PASS  mọi tín hiệu đều dẫn số")


def test_cache_khong_dinh_khi_tiem_ham_gia():
    """Tiêm hàm tải thì phải bỏ qua cache, nếu không ca test thứ hai sẽ
    nhận kết quả của ca thứ nhất."""
    fa.xoa_cache()
    mot = _agent(_dn(roe=25.0)).analyze("SAME")
    hai = _agent(_dn(roe=5.0)).analyze("SAME")
    assert mot["chi_so"].roe_pct == 25.0 and hai["chi_so"].roe_pct == 5.0
    print("PASS  hàm tải tiêm vào không bị cache che")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_") and not hasattr(ham, "pytestmark"):
            ham()
