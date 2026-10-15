"""BƯỚC 192 (mốc D2) — dụng cụ ĐO 26: nhãn sự kiện quyền đối chiếu lịch sự kiện VCI.

Bản ký: `docs/TIEU-CHI-DOC-TRUOC.md`, `## ĐO 26` (commit f93394c, trước dụng cụ).
File này khoá việc dụng cụ THI HÀNH đúng bản ký, trên một "thế giới" giả có đáp
án tính tay:

  HDB #122 (tiến-về-trước): vào 28/09 giá 27.950, nguồn mở 21.500 ⇒ f_vào = 1,3;
      ra 09/10 giá 21.000, nến ra [20.800; 22.000] ⇒ 21.000 ÷ 1,3 = 16.154 < 20.384
      ⇒ `SU_KIEN_TRONG_LUC_GIU`. Lịch: CK 5% + CK 25% ngày 09/10 ∈ (28/09, 09/10]
      ⇒ DƯƠNG THẬT. F = 1,05 × 1,25 = 1,3125; |1,3 ÷ 1,3125 − 1| = 0,0095 ≤ 0,02.
  SSX ×12 (mô phỏng): vào 01/09 giá 24.000, nguồn mở 20.000 ⇒ f_vào = 1,2; ra 10/09
      giá 24.600 ⇒ 24.600 ÷ 1,2 = 20.500 ∈ [20.000; 21.000] ⇒ `SACH`, e = 0. Lịch:
      CK 20% ngày 20/09 — SAU ngày ra ⇒ không có sự kiện trong lúc giữ; F = 1,2 khớp.
  AAA ×3 (mô phỏng): không sự kiện nào; nguồn mở 20.000 · 19.800 · 20.200 với giá
      vào 20.000 ⇒ |f_vào − 1| = 0 · 0,0101 · 0,0099 ⇒ max 0,0101 ≤ 0,025.

  ⇒ đối chứng (ii): N = 13 (HDB + 12 SSX), khớp 13/13; (iii): {122} = {122};
    0 dương tính giả, 0 âm tính giả; max e = 0 ≤ 0,01 ⇒ kết cục A.

Biến thể đổi đúng một thứ, đáp án ghi tại chỗ. Đột biến: `docs/STATE.md` BƯỚC 192.
"""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do26_nguong_su_kien_quyen as do26  # noqa: E402
import paper_trading as pt  # noqa: E402
import su_kien_quyen as skq  # noqa: E402
from paper_trading import Status  # noqa: E402

KEO = "2026-10-14"
V, R = "2026-09-28", "2026-10-09"          # HDB #122
V2, R2 = "2026-09-01", "2026-09-10"        # SSX, AAA, FNX


def _trade(id, ma, vao, gia_vao, ra, gia_ra, tien=False, tt=Status.CLOSED):
    return pt.Trade(id=id, symbol=ma, signal_date=vao, entry_date=vao,
                    entry_price=gia_vao, exit_date=ra, exit_price=gia_ra,
                    exit_reason="STOP_LOSS", stop_loss=1.0, take_profit=2.0,
                    size_pct=10.0, entry_score=70, status=tt,
                    created_at=(1_790_000_000.0 + id * 86400) if tien else None)


def _sk(ma, ma_sk, td, ngay, r=None, v=None):
    return {"ticker": ma, "eventCode": ma_sk, "eventTitleVi": td,
            "exrightDate": f"{ngay}T00:00:00", "exerciseRatio": r, "valuePerShare": v}


CK_THUONG = "Phát hành cổ phiếu - Cổ phiếu thưởng tỉ lệ 5.0%"
CK_CO_TUC = "Phát hành cổ phiếu - Trả Cổ tức bằng Cổ phiếu tỉ lệ 25.0%"


class _So:
    def __init__(self, trades):
        self._t = trades

    def all_trades(self):
        return list(self._t)


class TheGioi:
    """Sổ + nến + lịch giả. `nen[ma][ngày] = (mở, thấp, cao)` VNĐ."""

    def __init__(self):
        self.trades = [_trade(122, "HDB", V, 27950, R, 21000, tien=True)]
        self.nen = {"HDB": {V: (21500, 21000, 22000), R: (20800, 20800, 22000)}}
        self.lich = {"HDB": [_sk("HDB", "ISS", CK_THUONG, R, r=0.05),
                             _sk("HDB", "ISS", CK_CO_TUC, R, r=0.25)]}
        for i in range(12):
            self.trades.append(_trade(10 + i, "SSX", V2, 24000, R2, 24600))
        self.nen["SSX"] = {V2: (20000, 19900, 20100), R2: (20500, 20000, 21000)}
        self.lich["SSX"] = [_sk("SSX", "ISS", CK_THUONG, "2026-09-20", r=0.2)]
        for i, mo in enumerate((20000, 19800, 20200)):
            ma = f"AA{i}"
            self.trades.append(_trade(30 + i, ma, V2, 20000, R2, 20500))
            self.nen[ma] = {V2: (mo, mo - 100, mo + 100), R2: (20500, 20000, 21000)}
            self.lich[ma] = []
        self.goi_tai: list = []
        self.goi_lich: list = []
        self.hong_tai_lan: dict = {}

    def tai(self, ma, tu, den):
        self.goi_tai.append((ma, tu, den))
        n = sum(1 for m, _, _ in self.goi_tai if m == ma)
        if self.hong_tai_lan.get(ma) == n or ma not in self.nen:
            return "FAILED", None, 1.0
        ngay = sorted(self.nen[ma])
        return "OK", pd.DataFrame({
            "time": ngay,
            "open": [self.nen[ma][d][0] / 1000 for d in ngay],
            "low": [self.nen[ma][d][1] / 1000 for d in ngay],
            "high": [self.nen[ma][d][2] / 1000 for d in ngay],
            "close": [self.nen[ma][d][0] / 1000 for d in ngay]}), 1000.0

    def tai_lich(self, ma, tu):
        self.goi_lich.append((ma, tu))
        if ma not in self.lich:
            raise ConnectionError("giả: không tải được lịch")
        return list(self.lich[ma])

    def chay(self, capsys=None, argv=None):
        ma = do26.main(argv or [], keo=lambda: (_So(self.trades), {}), tai=self.tai,
                       tai_lich=self.tai_lich, hom_nay=KEO)
        ra = capsys.readouterr().out if capsys else ""
        return ma, ra

    def tong_hop(self):
        nen = {m: skq.dung_nen(sorted(b), [b[d][0] for d in sorted(b)],
                               [b[d][1] for d in sorted(b)], [b[d][2] for d in sorted(b)],
                               1.0) for m, b in self.nen.items()}
        lich = {m: do26.chuan_hoa(m, rows) for m, rows in self.lich.items()}
        dong = do26.cham(self.trades, nen, lich, KEO)
        import nen_su_kien_quyen as nsk
        tap = set(nsk.loai_tu_nen(self.trades, nen))
        return do26.tong_hop(dong, tap)


# ───────────────────────── 1. Phân loại và chuẩn hoá lịch ─────────────────────────

@pytest.mark.parametrize("ma_sk, td, loai", [
    ("DIV", "Trả cổ tức bằng tiền mặt - Cả năm 2025 - 1,000 VND", do26.TM),
    ("ISS", CK_THUONG, do26.CK),
    ("ISS", CK_CO_TUC, do26.CK),
    ("ISS", "Phát hành cổ phiếu - Quyền mua CP cho Cổ đông hiện hữu tỉ lệ 20.0%", do26.QM),
    ("ISS", "Phát hành cổ phiếu - Phát hành riêng lẻ tỉ lệ 14.0%", None),
    ("ISS", "Phát hành cổ phiếu - Phát hành cho CBCNV tỉ lệ 0.4%", None),
    ("ISS", "Phát hành cổ phiếu - Chuyển từ trái phiếu chuyển đổi tỉ lệ 5.8%", None),
    ("DDINS", "Đăng kí Mua 1,000,000 HDB", None),
])
def test_phan_loai_theo_BAN_KY(ma_sk, td, loai):
    assert do26.phan_loai(ma_sk, td) == loai


def test_phan_loai_chiu_chu_NFD():
    import unicodedata
    td = unicodedata.normalize("NFD", CK_THUONG)
    assert td != CK_THUONG and do26.phan_loai("ISS", td) == do26.CK


def test_chuan_hoa_bo_dong_khong_ngay_GDKHQ_va_sai_ma_va_sap_theo_ngay():
    rows = [_sk("HDB", "ISS", CK_CO_TUC, "2026-10-09", r=0.25),
            {**_sk("HDB", "ISS", "Phát hành riêng lẻ", "2026-08-24", r=0.14)},
            {**_sk("HDB", "ISS", CK_THUONG, "2025-12-18", r=0.0469)},
            {**_sk("VNM", "DIV", "tiền mặt", "2025-10-16", v=2500)},
            {"ticker": "HDB", "eventCode": "ISS", "eventTitleVi": CK_THUONG,
             "exrightDate": None, "exerciseRatio": 0.05}]
    sk = do26.chuan_hoa("HDB", rows)
    assert [(s.ngay, s.loai, s.ty_le) for s in sk] == [
        ("2025-12-18", "CK", 0.0469), ("2026-10-09", "CK", 0.25)]


def test_chuan_hoa_doc_ca_khoa_snake_case():
    rows = [{"ticker": "VNM", "event_code": "DIV", "event_title_vi": "tiền mặt",
             "exright_date": "2026-06-26", "value_per_share": 1850.0}]
    assert [(s.loai, s.ngay, s.tien) for s in do26.chuan_hoa("VNM", rows)] == [
        ("TM", "2026-06-26", 1850.0)]


def test_trong_khoang_la_NUA_MO_vao_dong_ra():
    sk = do26.chuan_hoa("X", [_sk("X", "DIV", "tiền mặt", d, v=500)
                               for d in (V2, "2026-09-05", R2, "2026-09-11")])
    assert [s.ngay for s in do26.trong_khoang(sk, V2, R2)] == ["2026-09-05", R2]


# ───────────────────────── 2. Số TÍNH TAY ─────────────────────────

def test_he_so_hai_mo_hinh_tinh_tay():
    sk = do26.chuan_hoa("X", [_sk("X", "ISS", CK_CO_TUC, "2026-09-02", r=0.25),
                              _sk("X", "DIV", "tiền mặt", "2026-09-03", v=1000)])
    assert do26.he_so(sk, 20000, "M_CK") == pytest.approx(1.25)
    # 1,25 × 1/(1 − 1000/20000) = 1,25 / 0,95 = 1,315789...
    assert do26.he_so(sk, 20000, "M_CKTM") == pytest.approx(1.25 / 0.95)


def test_he_so_None_khi_co_QM_hoac_thieu_so():
    qm = do26.chuan_hoa("X", [_sk("X", "ISS", "Quyền mua CP", "2026-09-02", r=0.2)])
    thieu = do26.chuan_hoa("X", [_sk("X", "ISS", CK_THUONG, "2026-09-02", r=None)])
    assert do26.he_so(qm, 20000, "M_CK") is None
    assert do26.he_so(thieu, 20000, "M_CK") is None


def test_lech_xuong_tinh_tay():
    # 23.640 ÷ 1,2 = 19.700; (20.000 − 19.700) ÷ 20.000 = 0,015
    assert do26.lech_xuong(23640, 1.2, 20000) == pytest.approx(0.015)
    assert do26.lech_xuong(24600, 1.2, 20000) == 0.0


def test_p95_hang_gan_nhat():
    assert do26.p95([]) is None
    assert do26.p95([0.3]) == 0.3
    # N = 20: phần tử thứ ⌈19⌉ = 19 của dãy tăng 1..20 -> 19
    assert do26.p95([float(i) for i in range(20, 0, -1)]) == 19.0
    # N = 21: ⌈19,95⌉ = 20 -> 20
    assert do26.p95([float(i) for i in range(1, 22)]) == 20.0


# ───────────────────────── 3. Thế giới chuẩn -> kết cục A ─────────────────────────

def test_the_gioi_chuan_cho_ket_cuc_A_va_dung_tung_con_so():
    th = TheGioi().tong_hop()
    assert th["dc1"] and th["dc2"] and th["dc3"]
    assert th["n2"] == 13 and th["khop"] == {"M_CK": 13, "M_CKTM": 13}
    assert th["duong_tinh_gia"] == [] and th["am_tinh_gia_lon"] == []
    assert len(th["nhom_noi_bien"]) == 12 and th["max_e"] == 0.0
    assert len(th["nhom_sach"]) == 3
    assert th["max_lech_sach"] == pytest.approx(0.0101, abs=1e-4)   # 20.000 / 19.800 − 1
    assert th["tap_cu"] == {122}
    assert th["ket_cuc"] == "A"


def test_CLI_the_gioi_chuan_ma_thoat_0_in_M0_va_tai_moi_ma_mot_lan(capsys):
    tg = TheGioi()
    ma, ra = tg.chay(capsys)
    assert ma == 0
    assert "KẾT CỤC (ký trước): A" in ra
    assert "M0  giờ kéo" in ra and "băm sổ" in ra and "băm lịch" in ra
    lan_lich = [m for m, _ in tg.goi_lich]
    assert sorted(lan_lich) == sorted(set(lan_lich))                  # lịch: mỗi mã MỘT lần
    assert {tu for _, tu in tg.goi_lich} == {"2026-08-22"}            # 01/09 − 10 ngày
    # nến: một lượt cho mọi mã, cộng một lượt của `tap_loai` cho mã có lệnh tiến đã đóng
    assert sorted(m for m, _, _ in tg.goi_tai) == sorted(
        ["HDB", "HDB", "SSX", "AA0", "AA1", "AA2"])


def test_CLI_ma_thoat_2_khi_khong_doc_duoc_so(capsys):
    assert do26.main([], keo=lambda: None) == 2
    assert "CHUA DOC DUOC SO" in capsys.readouterr().err


def test_CLI_ghi_json_tho_khi_duoc_yeu_cau(tmp_path, capsys):
    tep = tmp_path / "do26.json"
    ma, _ = TheGioi().chay(capsys, ["--json", str(tep)])
    import json
    d = json.loads(tep.read_text(encoding="utf-8"))
    assert ma == 0 and d["ket_cuc"] == "A" and len(d["dong"]) == 16


# ───────────────────────── 4. Biến thể: mỗi biến thể đổi MỘT thứ ─────────────────────────

def test_B_duong_tinh_gia_nhan_su_kien_ma_KHONG_co_su_kien(capsys):
    tg = TheGioi()
    # FPX: dựng y hệt HDB (nhãn SU_KIEN) nhưng lịch RỖNG ⇒ dương tính giả, mô phỏng
    tg.trades.append(_trade(200, "FPX", V, 27950, R, 21000))
    tg.nen["FPX"] = dict(tg.nen["HDB"])
    tg.lich["FPX"] = []
    th = tg.tong_hop()
    assert [d.id for d in th["duong_tinh_gia"]] == [200]
    assert th["duong_tinh_gia_tien"] == []
    assert th["ket_cuc"] == "B"
    ma, ra = tg.chay(capsys)
    assert ma == 1 and "DƯƠNG TÍNH GIẢ: 1 (trong đó tiến-về-trước, đang bị loại: 0)" in ra


def test_B_duong_tinh_gia_TIEN_VE_TRUOC_duoc_dem_rieng():
    tg = TheGioi()
    tg.trades.append(_trade(201, "FPX", V, 27950, R, 21000, tien=True))
    tg.nen["FPX"] = dict(tg.nen["HDB"])
    tg.lich["FPX"] = []
    th = tg.tong_hop()
    assert [d.id for d in th["duong_tinh_gia_tien"]] == [201]
    assert th["tap_cu"] == {122, 201} and th["dc3"]          # tap_loai cũng loại #201
    assert th["ket_cuc"] == "B"


def test_C_am_tinh_gia_lon_CK_10_phan_tram_trong_luc_giu_ma_nhan_SACH():
    tg = TheGioi()
    # FNX: nguồn KHÔNG điều chỉnh (mở 20.000 = giá vào) ⇒ f_vào 1 ⇒ SACH; lịch có CK 10%
    # ngày 05/09 ∈ (01/09, 10/09] ⇒ F = 1,1 > 1,05 ⇒ âm tính giả lớn. Đối chứng (ii):
    # FNX vào nhóm (f 1 ≠ F 1,1 -> trượt), khớp 13/14 = 92,9% ≥ 80% ⇒ vẫn qua.
    tg.trades.append(_trade(300, "FNX", V2, 20000, R2, 20500))
    tg.nen["FNX"] = {V2: (20000, 19900, 20100), R2: (20500, 20000, 21000)}
    tg.lich["FNX"] = [_sk("FNX", "ISS", CK_THUONG, "2026-09-05", r=0.10)]
    th = tg.tong_hop()
    assert [d.id for d in th["am_tinh_gia_lon"]] == [300]
    assert th["n2"] == 14 and th["khop"]["M_CK"] == 13 and th["dc2"]
    assert th["ket_cuc"] == "C"


def test_C_bien_DUNG_5_phan_tram_KHONG_phai_am_tinh_gia_lon():
    tg = TheGioi()
    # CK đúng 5%: F = 1,05, KHÔNG > 1 + 0,05 (so dạng nhân; 1,05 − 1 > 0,05 trong float)
    tg.trades.append(_trade(301, "FNX", V2, 20000, R2, 20500))
    tg.nen["FNX"] = {V2: (20000, 19900, 20100), R2: (20500, 20000, 21000)}
    tg.lich["FNX"] = [_sk("FNX", "ISS", CK_THUONG, "2026-09-05", r=0.05)]
    th = tg.tong_hop()
    assert th["am_tinh_gia_lon"] == []
    assert th["ket_cuc"] == "A"


def test_B_va_C_cung_luc():
    tg = TheGioi()
    tg.trades.append(_trade(200, "FPX", V, 27950, R, 21000))
    tg.nen["FPX"] = dict(tg.nen["HDB"])
    tg.lich["FPX"] = []
    tg.trades.append(_trade(300, "FNX", V2, 20000, R2, 20500))
    tg.nen["FNX"] = {V2: (20000, 19900, 20100), R2: (20500, 20000, 21000)}
    tg.lich["FNX"] = [_sk("FNX", "ISS", CK_THUONG, "2026-09-05", r=0.10)]
    assert tg.tong_hop()["ket_cuc"] == "B+C"


def test_A_phay_bien_NOI_BIEN_mong():
    tg = TheGioi()
    # Một lệnh SSX ra ở 23.640: 23.640 ÷ 1,2 = 19.700 ≥ 20.000 × 0,98 = 19.600 ⇒ vẫn SACH,
    # nhưng e = 0,015 > NOI_BIEN/2 = 0,01 ⇒ A′.
    tg.trades[1] = _trade(10, "SSX", V2, 24000, R2, 23640)
    th = tg.tong_hop()
    assert th["max_e"] == pytest.approx(0.015)
    assert th["duong_tinh_gia"] == [] and th["ket_cuc"] == "A′"


def test_A_phay_bien_NGUONG_LECH_mong():
    tg = TheGioi()
    # AA0 mở 19.400 ⇒ f_vào = 20.000/19.400 = 1,0309 ⇒ 0,0309 > NGUONG_LECH/2 = 0,025 ⇒ A′
    tg.nen["AA0"] = {V2: (19400, 19300, 19500), R2: (20500, 20000, 21000)}
    th = tg.tong_hop()
    assert th["max_lech_sach"] == pytest.approx(0.0309, abs=1e-4)
    assert th["ket_cuc"] == "A′"


def test_A_phay_khi_nhom_bien_RONG():
    tg = TheGioi()
    tg.trades = [t for t in tg.trades if not t.symbol.startswith("AA")]
    th = tg.tong_hop()
    assert th["nhom_sach"] == [] and th["max_lech_sach"] is None
    assert th["ket_cuc"] == "A′"


def test_nhom_NOI_BIEN_dung_CONG_cua_nhan_dang_nhan_bien_dung_5_phan_tram():
    tg = TheGioi()
    # BIE: vào 21.000, nguồn mở 20.000 ⇒ |21.000 − 20.000| = 1.000, KHÔNG > 0,05 × 20.000
    # ⇒ nhãn coi là trong ngưỡng (SACH ngay). Dạng cộng 21.000/20.000 − 1 = 0,05000000000000004
    # > 0,05 sẽ đưa nhầm nó vào nhóm qua cổng.
    tg.trades.append(_trade(400, "BIE", V2, 21000, R2, 21000))
    tg.nen["BIE"] = {V2: (20000, 19900, 20100), R2: (20500, 20000, 21000)}
    tg.lich["BIE"] = []
    th = tg.tong_hop()
    assert 400 not in {d.id for d in th["nhom_noi_bien"]}
    assert len(th["nhom_noi_bien"]) == 12


def test_nhom_sach_dung_khoang_vao_den_NGAY_KEO_khong_phai_den_ngay_ra():
    tg = TheGioi()
    # AA0 có cổ tức tiền SAU ngày ra (12/09 ∈ (01/09, 14/10]) ⇒ rời nhóm sạch
    tg.lich["AA0"] = [_sk("AA0", "DIV", "tiền mặt", "2026-09-12", v=300)]
    th = tg.tong_hop()
    assert sorted(d.id for d in th["nhom_sach"]) == [31, 32]


# ───────────────────────── 5. Đối chứng của máy đo -> K0 ─────────────────────────

def test_K0_khi_ca_duong_HDB_mat_lich(capsys):
    tg = TheGioi()
    tg.lich["HDB"] = []
    assert not tg.tong_hop()["dc1"]
    ma, ra = tg.chay(capsys)
    assert ma == 3 and "KẾT CỤC (ký trước): K0" in ra


def test_K0_khi_doi_chung_ii_nhom_duoi_10():
    tg = TheGioi()
    tg.trades = [t for t in tg.trades if not (t.symbol == "SSX" and t.id >= 14)]
    th = tg.tong_hop()
    assert th["n2"] == 5 and not th["dc2"] and th["ket_cuc"] == "K0"


def test_K0_khi_doi_chung_ii_khop_duoi_80_phan_tram():
    tg = TheGioi()
    # Nguồn chỉ điều chỉnh 10% trong khi lịch nói 20% ⇒ SSX f_vào = 24.000/21.818 = 1,1 ≠ 1,2
    tg.nen["SSX"] = {V2: (24000 / 1.1, 21700, 21900), R2: (22500, 22000, 23000)}
    th = tg.tong_hop()
    assert th["khop"]["M_CK"] == 1 and not th["dc2"] and th["ket_cuc"] == "K0"


def test_K0_khi_doi_chung_iii_tap_loai_khac_tap_cua_dung_cu(capsys):
    tg = TheGioi()
    tg.hong_tai_lan["HDB"] = 2          # lượt tải thứ hai của HDB (trong tap_loai) hỏng
    ma, ra = tg.chay(capsys)
    assert ma == 3 and "(iii) cùng tập loại: dụng cụ [122] · tap_loai []" in ra


def test_ma_khong_tai_duoc_lich_khong_vao_doi_chieu(capsys):
    tg = TheGioi()
    del tg.lich["AA2"]
    ma, ra = tg.chay(capsys)
    assert "thiếu lịch" in ra and "AA2" in ra
    assert ma == 0


# ───────────────────────── 6. Lật trang lịch VCI ─────────────────────────

def _gia_vnstock(monkeypatch, so_dong):
    goi = []

    class Company:
        def __init__(self, ma):
            self.ma = ma

        def _fetch_events(self, event_codes, from_date, page, size):
            goi.append((self.ma, event_codes, from_date, page, size))
            con = so_dong - page * size
            return [{"ticker": self.ma}] * max(0, min(size, con))

    mod = types.ModuleType("vnstock.explorer.vci.company")
    mod.Company = Company
    for ten in ("vnstock", "vnstock.explorer", "vnstock.explorer.vci"):
        monkeypatch.setitem(sys.modules, ten, types.ModuleType(ten))
    monkeypatch.setitem(sys.modules, "vnstock.explorer.vci.company", mod)
    return goi


def test_tai_lich_lat_HET_trang(monkeypatch):
    goi = _gia_vnstock(monkeypatch, 120)
    rows = do26.tai_lich_that("HDB", "2026-08-22")
    assert len(rows) == 120
    assert [g[3] for g in goi] == [0, 1, 2]
    assert {(g[1], g[2], g[4]) for g in goi} == {("DIV,ISS", "20260822", 50)}


def test_tai_lich_NEM_khi_cham_tran_trang(monkeypatch):
    _gia_vnstock(monkeypatch, 10_000)
    with pytest.raises(RuntimeError):
        do26.tai_lich_that("HDB", "2026-08-22")


# ───────────────────────── 7. AST: chỉ đọc, đúng hàm của sản phẩm ─────────────────────────

def _cay():
    return ast.parse((GOC / "tools/do26_nguong_su_kien_quyen.py").read_text(encoding="utf-8"))


def _ten_goi(n):
    f = n.func
    return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")


def test_ast_khong_goi_ham_ghi_so_chi_mot_write_text_cho_json():
    goi = [_ten_goi(n) for n in ast.walk(_cay()) if isinstance(n, ast.Call)]
    cam = {"push", "write_all", "append_rows", "pull", "record_trade", "update_trade",
           "record_decision", "commit", "executemany", "executescript", "execute",
           "open", "write_bytes", "unlink", "to_csv", "mkdir"}
    assert not (cam & set(goi)), sorted(cam & set(goi))
    assert goi.count("write_text") == 1


def test_ast_nhan_lay_bang_soi_so_va_nguong_doc_tu_su_kien_quyen():
    cay = _cay()
    goi = {(n.func.value.id, n.func.attr) for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and isinstance(n.func.value, ast.Name)}
    assert ("skq", "soi_so") in goi and ("nsk", "tap_loai") in goi
    doc = {(n.value.id, n.attr) for n in ast.walk(cay)
           if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    assert {("skq", "NGUONG_LECH"), ("skq", "NOI_BIEN")} <= doc
    # Thân hàm PHÁN (`tong_hop`, `cham`) không gõ lại ngưỡng nào; 0,05 ở `CA_DUONG` là tỷ
    # lệ thưởng 5% của ca HDB đã biết, không phải ngưỡng, nên không quét cả file.
    for ham in (n for n in cay.body if isinstance(n, ast.FunctionDef)
                and n.name in ("tong_hop", "cham")):
        so = {n.value for n in ast.walk(ham) if isinstance(n, ast.Constant)}
        assert not ({0.05, 0.02, 0.01, 0.025} & so), (ham.name, so)
