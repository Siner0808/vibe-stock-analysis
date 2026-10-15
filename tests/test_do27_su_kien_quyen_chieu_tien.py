"""BƯỚC 194 (mốc D2) — dụng cụ ĐO 27: chiều tiến, quần thể = lệnh tiến-về-trước đóng
SAU ngày ký, khoảng sự kiện từ max(ngày vào, ngày ghi sổ).

Bản ký: `docs/TIEU-CHI-DOC-TRUOC.md`, `## ĐO 27` (commit 19a7950, trước dụng cụ).
Thế giới giả, đáp án tính tay:

  HDB #122 (tiến, ghi 28/09, vào 28/09 giá 27.950, nguồn mở 21.500 ⇒ f_vào 1,3; ra
      09/10 giá 21.000, nến [20.800; 22.000]) — đóng TRƯỚC ngày ký ⇒ chỉ là đối chứng (i).
  SSX ×12 (mô phỏng, GHI 07/08/2026): vào 01/03 giá 24.000, nguồn mở 20.000 ⇒ f 1,2;
      ra 10/03. Lịch: CK 10% ngày 01/05 (TRƯỚC ngày ghi ⇒ đã nằm trong giá sổ, BỎ),
      CK 20% ngày 20/09 (sau ngày ghi) ⇒ F = 1,2 khớp. Đếm từ ngày VÀO thì F = 1,32,
      |1,2/1,32 − 1| = 0,091 ⇒ trượt — đó là đúng chỗ ĐO 26 hỏng.
  ⇒ đối chứng (ii): N = 13 (HDB + 12 SSX), khớp 13/13; (iii) {122} = {122}.
  Quần thể rỗng (không lệnh tiến nào đóng sau 15/10) ⇒ CHƯA ĐỦ, mã thoát 0.

Đột biến: `docs/STATE.md` BƯỚC 194.
"""
from __future__ import annotations

import ast
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do27_su_kien_quyen_chieu_tien as do27  # noqa: E402
import paper_trading as pt  # noqa: E402
from paper_trading import Status  # noqa: E402

KEO = "2026-11-30"
VN = dt.timezone(dt.timedelta(hours=7))
CK_THUONG = "Phát hành cổ phiếu - Cổ phiếu thưởng tỉ lệ 5.0%"
CK_CO_TUC = "Phát hành cổ phiếu - Trả Cổ tức bằng Cổ phiếu tỉ lệ 25.0%"


def _ts(ngay: str, gio: int = 15) -> float:
    y, m, d = map(int, ngay.split("-"))
    return dt.datetime(y, m, d, gio, 0, tzinfo=VN).timestamp()


def _trade(id, ma, vao, gia_vao, ra, gia_ra, ghi):
    return pt.Trade(id=id, symbol=ma, signal_date=vao, entry_date=vao,
                    entry_price=gia_vao, exit_date=ra, exit_price=gia_ra,
                    exit_reason="STOP_LOSS", stop_loss=1.0, take_profit=2.0,
                    size_pct=10.0, entry_score=70, status=Status.CLOSED,
                    created_at=ghi)


def _sk(ma, td, ngay, r=None, v=None, ma_sk="ISS"):
    return {"ticker": ma, "eventCode": ma_sk, "eventTitleVi": td,
            "exrightDate": f"{ngay}T00:00:00", "exerciseRatio": r, "valuePerShare": v}


class _So:
    def __init__(self, t):
        self._t = t

    def all_trades(self):
        return list(self._t)


class TheGioi:
    def __init__(self):
        # Lô mô phỏng: 12 lệnh ghi CÙNG một lúc (lô ghi hàng loạt ⇒ không phải tiến-về-trước)
        lo = _ts("2026-08-07", 14)
        self.trades = [_trade(122, "HDB", "2026-09-28", 27950, "2026-10-09", 21000,
                              _ts("2026-09-28"))]
        self.nen = {"HDB": {"2026-09-28": (21500, 21000, 22000),
                            "2026-10-09": (20800, 20800, 22000)}}
        self.lich = {"HDB": [_sk("HDB", CK_THUONG, "2026-10-09", r=0.05),
                             _sk("HDB", CK_CO_TUC, "2026-10-09", r=0.25)]}
        for i in range(12):
            self.trades.append(_trade(10 + i, "SSX", "2026-03-01", 24000, "2026-03-10",
                                      24600, lo + i))
        self.nen["SSX"] = {"2026-03-01": (20000, 19900, 20100),
                           "2026-03-10": (20500, 20000, 21000)}
        self.lich["SSX"] = [_sk("SSX", CK_THUONG, "2026-05-01", r=0.10),
                            _sk("SSX", CK_THUONG, "2026-09-20", r=0.20)]
        self.so_id = 500

    # ── lệnh tiến-về-trước đóng SAU ngày ký ─────────────────────────────
    def them_tien(self, ma, vao, gia_vao, ra, gia_ra, nen, lich=()):
        self.so_id += 1
        self.trades.append(_trade(self.so_id, ma, vao, gia_vao, ra, gia_ra,
                                  _ts(vao, 9) - 86400))     # ghi hôm trước ngày vào
        self.nen.setdefault(ma, {}).update(nen)
        self.lich.setdefault(ma, []).extend(lich)
        return self.so_id

    def them_sach(self, n, ma_dau="S"):
        """n lệnh sạch: vào 20.000 = mở nguồn (f 1), ra 30/10, không sự kiện."""
        for i in range(n):
            self.them_tien(f"{ma_dau}{i:02d}", "2026-10-20", 20000, "2026-10-30", 20500,
                           {"2026-10-20": (20000, 19900, 20100),
                            "2026-10-30": (20500, 20000, 21000)})

    def them_duong_that(self, ma):
        """Dựng như HDB: f_vào 1,3; CK 5% + 25% ngày 25/10 ∈ (20/10, 30/10] ⇒ dương thật."""
        return self.them_tien(ma, "2026-10-20", 27950, "2026-10-30", 21000,
                              {"2026-10-20": (21500, 21000, 22000),
                               "2026-10-30": (20800, 20800, 22000)},
                              [_sk(ma, CK_THUONG, "2026-10-25", r=0.05),
                               _sk(ma, CK_CO_TUC, "2026-10-25", r=0.25)])

    def them_su_kien_sau_ra(self, ma):
        """Sự kiện SAU ngày ra (05/11): f 1,2, giá ra 24.600 ÷ 1,2 = 20.500 trong biên ⇒
        SACH, qua cổng, e = 0 ⇒ nhóm biên NOI_BIEN có phần tử."""
        return self.them_tien(ma, "2026-10-20", 24000, "2026-10-30", 24600,
                              {"2026-10-20": (20000, 19900, 20100),
                               "2026-10-30": (20500, 20000, 21000)},
                              [_sk(ma, CK_THUONG, "2026-11-05", r=0.20)])

    def tai(self, ma, tu, den):
        if ma not in self.nen:
            return "FAILED", None, 1.0
        ngay = sorted(self.nen[ma])
        b = self.nen[ma]
        return "OK", pd.DataFrame({
            "time": ngay, "open": [b[d][0] / 1000 for d in ngay],
            "low": [b[d][1] / 1000 for d in ngay], "high": [b[d][2] / 1000 for d in ngay],
            "close": [b[d][0] / 1000 for d in ngay]}), 1000.0

    def tai_lich(self, ma, tu):
        return list(self.lich.get(ma, []))

    def chay(self, capsys):
        ma = do27.main([], keo=lambda: (_So(self.trades), {}), tai=self.tai,
                       tai_lich=self.tai_lich, hom_nay=KEO)
        return ma, capsys.readouterr().out


# ───────────────────────── 1. Ngày ghi sổ và quần thể ─────────────────────────

def test_ngay_ghi_theo_GIO_VN():
    # 23:30 giờ VN ngày 07/08 = 16:30 UTC cùng ngày; 00:30 giờ VN ngày 08/08 = 17:30 UTC 07/08
    assert do27.ngay_ghi(dt.datetime(2026, 8, 7, 23, 30, tzinfo=VN).timestamp()) == "2026-08-07"
    assert do27.ngay_ghi(dt.datetime(2026, 8, 8, 0, 30, tzinfo=VN).timestamp()) == "2026-08-08"
    assert do27.ngay_ghi(None) is None


def test_quan_the_chi_lenh_TIEN_dong_SAU_ngay_ky():
    tg = TheGioi()
    a = tg.them_tien("AAA", "2026-10-01", 20000, "2026-10-15", 20500, {})   # đóng ĐÚNG ngày ký
    b = tg.them_tien("BBB", "2026-10-01", 20000, "2026-10-16", 20500, {})   # đóng sau
    qt = do27.quan_the(tg.trades)
    assert b in qt and a not in qt
    assert not ({10, 11, 122} & qt)          # mô phỏng và lệnh đóng trước ngày ký


# ───────────────────────── 2. Khoảng sự kiện từ ngày ghi sổ ─────────────────────────

def test_khoang_tu_NGAY_GHI_bo_su_kien_truoc_ngay_ghi_va_doi_chung_ii_qua():
    th = _th(TheGioi())
    assert th["doi_chung"]["n2"] == 13
    assert th["doi_chung"]["khop"] == {"M_CK": 13, "M_CKTM": 13}
    assert th["doi_chung"]["dc2"]


def test_lenh_ghi_SAU_ngay_ra_khong_co_su_kien_trong_luc_giu():
    tg = TheGioi()
    nen = {m: {d: v for d, v in b.items()} for m, b in tg.nen.items()}
    import su_kien_quyen as skq
    nen_vnd = {m: skq.dung_nen(sorted(b), [b[d][0] for d in sorted(b)],
                               [b[d][1] for d in sorted(b)], [b[d][2] for d in sorted(b)], 1.0)
               for m, b in nen.items()}
    lich = {m: do27.do26.chuan_hoa(m, r) for m, r in tg.lich.items()}
    dong = {d.id: d for d in do27.cham(tg.trades, nen_vnd, lich, KEO)}
    # SSX: ghi 07/08 > ra 10/03 ⇒ khoảng giữ (07/08, 10/03] rỗng; CK 10% ngày 01/05 KHÔNG giữ
    assert dong[10].giu == [] and dong[10].F_giu == 1.0
    assert [s.ngay for s in dong[10].sau_vao] == ["2026-09-20"]
    # HDB: ghi 28/09 = ngày vào ⇒ khoảng như ĐO 26
    assert [s.ty_le for s in dong[122].giu] == [0.05, 0.25]


# ───────────────────────── 3. Kết cục ─────────────────────────

def _th(tg):
    import su_kien_quyen as skq
    import nen_su_kien_quyen as nsk
    nen = {m: skq.dung_nen(sorted(b), [b[d][0] for d in sorted(b)],
                           [b[d][1] for d in sorted(b)], [b[d][2] for d in sorted(b)], 1.0)
           for m, b in tg.nen.items()}
    lich = {m: do27.do26.chuan_hoa(m, r) for m, r in tg.lich.items()}
    dong = do27.cham(tg.trades, nen, lich, KEO)
    return do27.tong_hop(dong, set(nsk.loai_tu_nen(tg.trades, nen)), do27.quan_the(tg.trades))


def test_quan_the_rong_la_CHUA_DU():
    th = _th(TheGioi())
    assert th["n_quan_the"] == 0 and th["ket_cuc"] == "CHƯA ĐỦ"


def test_A_khi_du_30_lenh_va_3_duong_that_va_hai_bien_qua():
    tg = TheGioi()
    tg.them_sach(26)
    for m in ("DT1", "DT2", "DT3"):
        tg.them_duong_that(m)
    tg.them_su_kien_sau_ra("SR1")
    th = _th(tg)
    assert th["n_quan_the"] == 30 and len(th["duong_that"]) == 3
    assert th["quan_the"]["duong_tinh_gia"] == [] and th["quan_the"]["am_tinh_gia_lon"] == []
    assert len(th["quan_the"]["nhom_noi_bien"]) == 1 and th["quan_the"]["max_e"] == 0.0
    assert th["ket_cuc"] == "A"


def test_CHUA_DU_khi_29_lenh_du_3_duong_that():
    tg = TheGioi()
    tg.them_sach(25)
    for m in ("DT1", "DT2", "DT3"):
        tg.them_duong_that(m)
    tg.them_su_kien_sau_ra("SR1")
    th = _th(tg)
    assert th["n_quan_the"] == 29 and th["ket_cuc"] == "CHƯA ĐỦ"


def test_CHUA_DU_khi_30_lenh_chi_2_duong_that():
    tg = TheGioi()
    tg.them_sach(27)
    for m in ("DT1", "DT2"):
        tg.them_duong_that(m)
    tg.them_su_kien_sau_ra("SR1")
    th = _th(tg)
    assert th["n_quan_the"] == 30 and len(th["duong_that"]) == 2
    assert th["ket_cuc"] == "CHƯA ĐỦ"


def test_A_phay_khi_nhom_bien_NOI_BIEN_rong():
    tg = TheGioi()
    tg.them_sach(27)
    for m in ("DT1", "DT2", "DT3"):
        tg.them_duong_that(m)
    th = _th(tg)
    assert th["quan_the"]["nhom_noi_bien"] == [] and th["ket_cuc"] == "A′"


def test_B_duong_tinh_gia_trong_quan_the_ma_thoat_1(capsys):
    tg = TheGioi()
    # FPX: dựng như dương thật nhưng lịch RỖNG ⇒ nhãn SU_KIEN mà không sự kiện
    i = tg.them_tien("FPX", "2026-10-20", 27950, "2026-10-30", 21000,
                     {"2026-10-20": (21500, 21000, 22000),
                      "2026-10-30": (20800, 20800, 22000)})
    th = _th(tg)
    assert [d.id for d in th["quan_the"]["duong_tinh_gia"]] == [i]
    assert th["ket_cuc"] == "B"
    ma, ra = tg.chay(capsys)
    assert ma == 1 and "DƯƠNG TÍNH GIẢ: 1" in ra


def test_duong_tinh_gia_NGOAI_quan_the_khong_tinh():
    tg = TheGioi()
    # Lệnh mô phỏng dạng FPX (không created_at) đóng sau ngày ký: KHÔNG thuộc quần thể
    tg.trades.append(pt.Trade(id=900, symbol="FPX", signal_date="2026-10-20",
                              entry_date="2026-10-20", entry_price=27950,
                              exit_date="2026-10-30", exit_price=21000, exit_reason="SL",
                              stop_loss=1.0, take_profit=2.0, size_pct=10.0,
                              entry_score=70, status=Status.CLOSED, created_at=None))
    tg.nen["FPX"] = {"2026-10-20": (21500, 21000, 22000), "2026-10-30": (20800, 20800, 22000)}
    tg.lich["FPX"] = []
    assert _th(tg)["ket_cuc"] == "CHƯA ĐỦ"


def test_K0_khi_dem_tu_NGAY_VAO_thi_doi_chung_ii_truot(monkeypatch):
    tg = TheGioi()
    # Bỏ ngày ghi sổ ⇒ khoảng về (ngày vào, …] ⇒ SSX F = 1,32 ≠ 1,2 ⇒ (ii) trượt ⇒ K0
    monkeypatch.setattr(do27, "ngay_ghi", lambda _ts: None)
    assert _th(tg)["ket_cuc"] == "K0"


def test_CLI_ma_thoat_2_khi_khong_doc_duoc_so(capsys):
    assert do27.main([], keo=lambda: None) == 2
    assert "CHUA DOC DUOC SO" in capsys.readouterr().err


def test_CLI_the_gioi_chuan(capsys):
    ma, ra = TheGioi().chay(capsys)
    assert ma == 0
    assert "(ii)  giá ↔ lịch: N=13 · M_CK 13 (100.0%)" in ra
    assert "(iii) cùng tập loại: dụng cụ [122] · tap_loai [122] → QUA" in ra
    assert "QUẦN THỂ: 0 lệnh có lịch" in ra
    assert "KẾT CỤC LƯỢT ĐỌC (ký trước): CHƯA ĐỦ" in ra


# ───────────────────────── 4. AST ─────────────────────────

def _cay():
    return ast.parse((GOC / "tools/do27_su_kien_quyen_chieu_tien.py").read_text(encoding="utf-8"))


def test_ast_dung_lai_dinh_nghia_cua_DO_26_va_khong_ghi_so():
    cay = _cay()
    goi = {(n.func.value.id, n.func.attr) for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and isinstance(n.func.value, ast.Name)}
    assert {("do26", "cham"), ("do26", "tong_hop"), ("nsk", "tap_loai"),
            ("nsk", "lenh_dong_tien_ve_truoc")} <= goi
    ten = [n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
           for n in ast.walk(cay) if isinstance(n, ast.Call)]
    cam = {"push", "write_all", "append_rows", "pull", "record_trade", "update_trade",
           "record_decision", "commit", "execute", "open", "unlink", "to_csv"}
    assert not (cam & set(ten)) and ten.count("write_text") == 1


def test_NGAY_KY_la_ngay_cua_ban_ky():
    assert do27.NGAY_KY == "2026-10-15"
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    assert "## ĐO 27" in van and "(khai 15/10/2026)" in van.split("## ĐO 27", 1)[1].split("\n", 1)[0]
