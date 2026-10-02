"""Gác dụng cụ vòng SÀNG của tầng 3 — `tools/sang_ung_vien.py` (BƯỚC 154, ĐO 23).

Chạy trên dữ liệu TỔNG HỢP: không chạm cache giá, không chạm sổ thật, không gọi
`paper_runner._analyze` (máy chấm thật được thay bằng hàm giả). Tiêu chí ký
trước: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 23.

Bốn thứ phải đúng, vì cả bốn là chỗ một máy sàng có thể tự khen mình:
1. **Không rò ≥ mốc**: loại lúc nạp, và lõi NÉM LỖI nếu còn sót — kể cả nhãn.
2. **Phép đối chiếu đo đúng thứ nó khai**: chỉ ô khớp, chấm lại trên đúng lịch
   sử `iloc[:t+1]`, không nhìn trước, và kết cục theo ngưỡng đã ký.
3. **Tỉ lệ qua/rớt đúng ngưỡng**: tín hiệu cấy vào phải QUA; nhiễu phải QUA với
   tỉ lệ nằm trong khoảng nhị thức của 5% (một phía) — không hơn, không kém.
4. **Không ghi sổ ứng viên**: điền `qua_sang` là việc tay ở commit riêng.
"""
import ast
import hashlib
import importlib.util
import math
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "sang_ung_vien", GOC / "tools" / "sang_ung_vien.py")
S = importlib.util.module_from_spec(_spec)
sys.modules["sang_ung_vien"] = S
_spec.loader.exec_module(S)

import cham_bong as CB  # noqa: E402
import experiment_khoi_ngoai_nhip_dai as D  # noqa: E402

TIEU_CHI = GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md"
FILE_TOOL = GOC / "tools" / "sang_ung_vien.py"


# ── dữ liệu tổng hợp ─────────────────────────────────────────────────────

def _ar1(rng, n, rho=0.9):
    """Chuỗi AR(1) phương sai 1 — điểm thật bền theo thời gian, không phải ồn trắng."""
    e = rng.standard_normal(n) * math.sqrt(1 - rho * rho)
    x = np.empty(n)
    x[0] = rng.standard_normal()
    for t in range(1, n):
        x[t] = rho * x[t - 1] + e[t]
    return x


def _gia(hat, n_ma=45, n_ph=200, dau="2024-01-01"):
    """{mã: DataFrame} dạng `E.nap_gia`: chỉ số `ngay`, cột `time` + OHLCV."""
    rng = np.random.default_rng(hat)
    ngay = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(dau, periods=n_ph)]
    kh = {}
    for j in range(n_ma):
        c = 50 * np.exp(np.cumsum(rng.normal(0, 0.02, n_ph)))
        kh[f"M{j:02d}"] = pd.DataFrame(
            {"time": ngay, "open": c, "high": c * 1.01, "low": c * 0.99,
             "close": c, "volume": 1e6}, index=pd.Index(ngay, name="ngay"))
    return kh


def _bang(gia, hat, tin_hieu=0.0, spec_nen=None):
    """Bảng điểm dày giả. `score` (nền) là ồn; `trend_score` mang `tin_hieu`·nhãn."""
    rng = np.random.default_rng(hat + 10_000)
    nhan = S.nhan_sach(gia)
    z = (nhan - np.nanmean(nhan.to_numpy())) / np.nanstd(nhan.to_numpy())
    rows = []
    for ma, d in gia.items():
        n = len(d)
        tp = {k: 50 + 10 * _ar1(rng, n) for k in CB.THANH_PHAN}
        if tin_hieu:
            tp["trend_score"] = tp["trend_score"] + 10 * tin_hieu * z[ma].reindex(
                d.index).fillna(0.0).to_numpy()
        diem = 50 + 10 * _ar1(rng, n)
        if spec_nen:
            diem = sum(w * tp[k] for k, w in spec_nen.items())
        for t in range(n):
            rows.append({"symbol": ma, "ngay": d.index[t], "score": float(diem[t]),
                         **{k: float(tp[k][t]) for k in CB.THANH_PHAN}})
    return pd.DataFrame(rows)


SPEC_TREND = {"loai": "trong_so", "trong_so": {"trend_score": 1.0}}


# ── 1. chặn rò ───────────────────────────────────────────────────────────

def test_CAT_QUYET_DINH_loai_dong_tu_moc_tro_di_va_dem():
    rows = [{"signal_date": "2026-08-09"}, {"signal_date": "2026-08-10"},
            {"signal_date": "2026-08-10 15:00:00"}, {"signal_date": "2027-01-01"},
            {"signal_date": "2026-08-07"}]
    giu, loai = S.cat_quyet_dinh(rows)
    assert [r["signal_date"] for r in giu] == ["2026-08-09", "2026-08-07"]
    assert loai == 3


def test_CAT_QUYET_DINH_ngay_thieu_hay_sai_khuon_bi_LOAI_khong_lot_qua():
    rows = [{}, {"signal_date": ""}, {"signal_date": None}, {"signal_date": "abc"},
            {"signal_date": "2026-8-1"}, {"signal_date": "2026-01-02"}]
    giu, loai = S.cat_quyet_dinh(rows)
    assert [r.get("signal_date") for r in giu] == ["2026-01-02"]
    assert loai == 5


def test_CAT_QUYET_DINH_dung_nguong_mot_ngay_truoc_va_sau_moc():
    giu, loai = S.cat_quyet_dinh([{"signal_date": "2026-08-09"},
                                  {"signal_date": "2026-08-10"}], moc="2026-08-10")
    assert len(giu) == 1 and loai == 1
    giu, loai = S.cat_quyet_dinh([{"signal_date": "2026-08-09"},
                                  {"signal_date": "2026-08-10"}], moc="2026-08-11")
    assert len(giu) == 2 and loai == 0


def test_CAT_GIA_bo_nen_tu_moc_tro_di_va_bo_ma_het_nen():
    ngay = ["2026-08-07", "2026-08-10", "2026-08-11"]
    muon = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=pd.Index(ngay, name="ngay"))
    toan_sau = pd.DataFrame({"close": [1.0]}, index=pd.Index(["2026-09-01"], name="ngay"))
    ra = S.cat_gia({"A": muon, "B": toan_sau})
    assert list(ra) == ["A"]
    assert list(ra["A"].index) == ["2026-08-07"]


def test_KIEM_KHONG_RO_ne_loi_khi_bang_con_dong_tu_moc():
    bang = pd.DataFrame({"ngay": ["2026-08-07", "2026-08-10"]})
    with pytest.raises(ValueError, match="RO"):
        S.kiem_khong_ro(bang=bang)
    S.kiem_khong_ro(bang=bang.iloc[:1])


def test_KIEM_KHONG_RO_ne_loi_khi_gia_con_nen_tu_moc():
    d = pd.DataFrame({"close": [1.0, 2.0]},
                     index=pd.Index(["2026-08-07", "2026-08-10"], name="ngay"))
    with pytest.raises(ValueError, match="RO"):
        S.kiem_khong_ro(gia={"A": d})
    S.kiem_khong_ro(gia={"A": d.iloc[:1]})


def test_SANG_ne_loi_khi_cay_mot_dong_diem_tu_moc():
    gia = _gia(1)
    bang = _bang(gia, 1)
    them = pd.DataFrame([{"symbol": "M00", "ngay": "2026-08-10", "score": 50.0,
                          **{k: 50.0 for k in CB.THANH_PHAN}}])
    so = {"ung_vien": {}}
    with pytest.raises(ValueError, match="RO"):
        S.sang(so, pd.concat([bang, them], ignore_index=True), gia)


def test_SANG_ne_loi_khi_cay_mot_nen_gia_tu_moc():
    gia = _gia(2)
    bang = _bang(gia, 2)
    d = gia["M00"]
    gia["M00"] = pd.concat([d, pd.DataFrame(
        {"time": ["2026-08-10"], "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
         "volume": 1.0}, index=pd.Index(["2026-08-10"], name="ngay"))])
    with pytest.raises(ValueError, match="RO"):
        S.sang({"ung_vien": {}}, bang, gia)
    with pytest.raises(ValueError, match="RO"):
        S.nhan_sach(gia)


def test_DIEM_DAY_va_DOI_CHIEU_va_HINH_DANG_deu_ne_loi_khi_gia_ro():
    gia = _gia(3, n_ma=2, n_ph=40)
    d = gia["M00"]
    gia["M00"] = pd.concat([d, pd.DataFrame(
        {"time": ["2026-09-01"], "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
         "volume": 1.0}, index=pd.Index(["2026-09-01"], name="ngay"))])
    gia_sach = _gia(3, n_ma=2, n_ph=40)
    nhan = S.nhan_sach(gia_sach)
    with pytest.raises(ValueError, match="RO"):
        S.diem_day(gia, nhan, lambda *a: ({}, 0.0))
    with pytest.raises(ValueError, match="RO"):
        S.doi_chieu([], gia, lambda *a: ({}, 0.0))
    with pytest.raises(ValueError, match="RO"):
        S.hinh_dang([], gia)


def test_NHAN_chi_co_o_phien_ma_T_cong_22_van_nam_trong_gia_da_cat():
    """Phiên T có nhãn chỉ khi hàng T + NHIP + 1 nằm trong giá đã cắt — nhãn
    không bao giờ chạm một nến ≥ mốc, kể cả khi cache còn nến sau mốc."""
    ngay = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(end="2026-09-10", periods=90)]
    kh = {}
    rng = np.random.default_rng(4)
    for j in range(3):
        c = 50 * np.exp(np.cumsum(rng.normal(0, 0.02, len(ngay))))
        kh[f"A{j}"] = pd.DataFrame({"time": ngay, "close": c},
                                   index=pd.Index(ngay, name="ngay"))
    gia = S.cat_gia(kh)
    n = len(next(iter(gia.values())))
    assert max(gia["A0"].index) < S.MOC_DA_NHIN
    nhan = S.nhan_sach(gia)
    co = np.flatnonzero(nhan.notna().any(axis=1).to_numpy())
    assert co.max() == n - CB.NHIP - 2          # T + h + 1 <= n - 1
    lich = list(gia["A0"].index)
    assert all(lich[t + CB.NHIP + 1] < S.MOC_DA_NHIN for t in co)


def test_DIEM_DAY_chi_cham_o_co_nhan_va_khong_nhin_truoc():
    gia = _gia(5, n_ma=2, n_ph=60)
    nhan = S.nhan_sach(gia)
    goi = []

    def gia_phan_tich(ma, lich_su, ngay):
        # lịch sử phải KẾT THÚC đúng ở phiên đang chấm
        assert str(lich_su["time"].iloc[-1])[:10] == ngay
        assert list(lich_su.index) == list(range(len(lich_su)))
        goi.append((ma, ngay, len(lich_su)))
        return {k: 50.0 for k in CB.THANH_PHAN}, 50.0

    b = S.diem_day(gia, nhan, gia_phan_tich, bat_dau_hang=10)
    co_nhan = {(ma, d) for ma in gia for d in nhan.index
               if np.isfinite(nhan.at[d, ma]) and gia[ma].index.get_loc(d) >= 10}
    assert {(m, d) for m, d, _ in goi} == co_nhan
    assert len(b) == len(co_nhan)
    assert list(b.columns) == ["symbol", "ngay", "score", *CB.THANH_PHAN]
    for ma, d, n_ls in goi:
        assert n_ls == gia[ma].index.get_loc(d) + 1


# ── 2. phép đối chiếu ────────────────────────────────────────────────────

def _may_gia(ma, lich_su, ngay):
    """Máy chấm GIẢ, hàm thuần của lát cắt — cho điểm biến thiên theo ô."""
    c = float(lich_su["close"].iloc[-1])
    n = len(lich_su)
    tp = {k: round((c * (j + 3) + n * (j + 1)) % 97, 1)
          for j, k in enumerate(CB.THANH_PHAN)}
    return tp, float(int(sum(tp.values()) / 5))


def _rows_da_ghi(gia, buoc=2, them=(), pha=False):
    """Dòng đã ghi giả. `pha=True`: mỗi mã một pha riêng, như `cmd_seed` stride 2."""
    import json
    rows = []
    for j, (ma, d) in enumerate(gia.items()):
        for t in range(10 + (j % buoc if pha else 0), len(d), buoc):
            ngay = d.index[t]
            tp, diem = _may_gia(ma, d.iloc[: t + 1].reset_index(drop=True), ngay)
            rows.append({"seq": len(rows), "at": float(len(rows)), "symbol": ma,
                         "signal_date": ngay, "score": diem,
                         "components": json.dumps(tp)})
    return rows + list(them)


def test_DOI_CHIEU_may_giong_het_cho_rho_1_va_khop_moi_o(monkeypatch):
    monkeypatch.setattr(S, "N_DOI_CHIEU_TOI_THIEU", 50)
    gia = _gia(6, n_ma=4, n_ph=60)
    rows = _rows_da_ghi(gia)
    kq = S.doi_chieu(rows, gia, _may_gia)
    assert kq["n"] == len(rows)
    assert kq["rho_cuoi"] == pytest.approx(1.0)
    assert all(v == pytest.approx(1.0) for v in kq["rho_tp"].values())
    assert set(kq["rho_tp"]) == set(CB.THANH_PHAN)
    assert kq["ty_le_khop"] == 1.0
    assert kq["ket_cuc"] == "DAT"


def test_DOI_CHIEU_may_cho_diem_khac_HAN_thi_KHONG_DAT(monkeypatch):
    monkeypatch.setattr(S, "N_DOI_CHIEU_TOI_THIEU", 50)
    gia = _gia(7, n_ma=4, n_ph=60)
    rows = _rows_da_ghi(gia)
    rng = np.random.default_rng(0)

    def may_ngau_nhien(ma, ls, ngay):
        return ({k: float(rng.uniform(0, 100)) for k in CB.THANH_PHAN},
                float(rng.uniform(0, 100)))

    kq = S.doi_chieu(rows, gia, may_ngau_nhien)
    assert kq["rho_cuoi"] < 0.5
    assert kq["ket_cuc"] == "KHONG DAT"


def test_DOI_CHIEU_mot_thanh_phan_lech_la_du_de_KHONG_DAT(monkeypatch):
    """Điểm cuối khớp mà một thành phần lệch → vẫn KHÔNG ĐẠT (hai vế, cả hai)."""
    monkeypatch.setattr(S, "N_DOI_CHIEU_TOI_THIEU", 50)
    gia = _gia(8, n_ma=4, n_ph=60)
    rows = _rows_da_ghi(gia)
    rng = np.random.default_rng(1)

    def may(ma, ls, ngay):
        tp, diem = _may_gia(ma, ls, ngay)
        tp["sr_score"] = float(rng.uniform(0, 100))
        return tp, diem

    kq = S.doi_chieu(rows, gia, may)
    assert kq["rho_cuoi"] == pytest.approx(1.0)
    assert kq["rho_tp"]["sr_score"] < 0.5
    assert kq["ket_cuc"] == "KHONG DAT"


@pytest.mark.parametrize("lech, ty_le", [(0.05, 1.0), (0.1, 1.0), (0.5, 0.0)])
def test_DOI_CHIEU_ty_le_khop_dung_sai_0_1_cho_moi_thanh_phan(monkeypatch, lech, ty_le):
    """Chỉ để ĐỌC, nhưng phải đo đúng: một thành phần lệch quá 0,1 là ô không khớp."""
    gia = _gia(22, n_ma=3, n_ph=40)
    rows = _rows_da_ghi(gia)

    def may(ma, ls, ngay):
        tp, diem = _may_gia(ma, ls, ngay)
        tp["risk_score"] = round(tp["risk_score"] + lech, 6)
        return tp, diem

    assert S.doi_chieu(rows, gia, may)["ty_le_khop"] == ty_le


def test_PHAN_TICH_THAT_dat_bo_nho_TAT_truoc_khi_cham_va_goi_pipeline_that(monkeypatch):
    import paper_runner
    import walkforward
    nhat_ky = []
    monkeypatch.setattr(walkforward, "_dung_bo_nho",
                        lambda che_do, duong: nhat_ky.append(("bo_nho", che_do, duong)))
    monkeypatch.setattr(paper_runner, "_xoa_cache_phan_tich",
                        lambda: nhat_ky.append(("xoa_cache",)))

    def gia_analyze(ma, ls, san, ngay):
        nhat_ky.append(("analyze", ma, san, ngay))
        return {"final_score": 61, "score_breakdown": {"trend_score": 1.5}}
    monkeypatch.setattr(paper_runner, "_analyze", gia_analyze)

    chay = S.phan_tich_that()
    assert nhat_ky[:2] == [("bo_nho", "tat", None), ("xoa_cache",)]
    tp, diem = chay("FPT", pd.DataFrame({"x": [1]}), "2026-01-02 00:00:00")
    assert (tp, diem) == ({"trend_score": 1.5}, 61.0) and isinstance(diem, float)
    assert nhat_ky[2] == ("analyze", "FPT", "HOSE", "2026-01-02")


def test_DOI_CHIEU_va_BANG_DAY_deu_di_qua_phan_tich_that_khi_chay_lenh(monkeypatch, tmp_path):
    """Lệnh CLI dùng máy chấm THẬT (bộ nhớ tắt) — không có đường nào đi vòng qua nó."""
    f = tmp_path / "dc.json"
    S.ghi_ket_qua_doi_chieu(f, {"ket_cuc": "DAT"}, "x.db", "2026-10-02")
    monkeypatch.setattr(S, "FILE_DOI_CHIEU", f)
    dung = []
    gia = _gia(23, n_ma=2, n_ph=60)
    monkeypatch.setattr(S, "nap_gia", lambda *a, **k: gia)
    monkeypatch.setattr(S, "phan_tich_that", lambda: dung.append(1) or _may_gia)
    assert S.main(["bang-day", "--ra", str(tmp_path / "b.csv")]) == 0
    assert dung == [1]


def test_HINH_DANG_dung_bien_40_ma_la_DU_40_ma():
    gia = _gia(24, n_ma=40, n_ph=80)
    h = S.hinh_dang(_rows_da_ghi(gia, buoc=1), gia)
    assert h["ma_moi_phien_trung_vi"] == 40 and h["phien_du_40_ma"] == 70


def test_DOI_CHIEU_chi_dem_o_khop_va_dem_dong_tu_moc():
    gia = _gia(9, n_ma=3, n_ph=60)
    xa = {"seq": 9998, "at": 1.0, "symbol": "ZZZ", "signal_date": gia["M00"].index[30],
          "score": 50.0, "components": '{"trend_score":1}'}
    lech = {"seq": 9999, "at": 2.0, "symbol": "M00", "signal_date": "2020-01-01",
            "score": 50.0, "components": '{"trend_score":1}'}
    ro = {"seq": 10000, "at": 3.0, "symbol": "M00", "signal_date": "2026-08-10",
          "score": 50.0, "components": "{}"}
    rows = _rows_da_ghi(gia)
    kq = S.doi_chieu(rows + [xa, lech, ro], gia, _may_gia)
    assert kq["n"] == len(rows)                # mã lạ, ngày ngoài lịch, ô ≥ mốc: không tính
    assert kq["n_dong_loai_ge_moc"] == 1


def test_DOI_CHIEU_chay_lai_tren_dung_lich_su_cmd_seed_da_dua_vao():
    gia = _gia(10, n_ma=2, n_ph=40)
    rows = _rows_da_ghi(gia, buoc=1)
    thay = []

    def may(ma, ls, ngay):
        k = gia[ma].index.get_loc(ngay)
        thay.append(len(ls) == k + 1 and str(ls["time"].iloc[-1])[:10] == ngay
                    and list(ls.index) == list(range(len(ls))))
        return _may_gia(ma, ls, ngay)

    S.doi_chieu(rows, gia, may)
    assert thay and all(thay)


def test_DOI_CHIEU_khong_o_nao_khop_thi_KHONG_DOC():
    gia = _gia(11, n_ma=2, n_ph=40)
    kq = S.doi_chieu([{"seq": 1, "at": 1.0, "symbol": "ZZZ",
                       "signal_date": "2024-02-01", "score": 50.0,
                       "components": '{"trend_score":1}'}], gia, _may_gia)
    assert kq["ket_cuc"] == "KHONG DOC" and kq["n"] == 0


@pytest.mark.parametrize("n, rc, rt, ky_vong", [
    (10_000, 0.95, 0.95, "DAT"),
    (9_999, 0.99, 0.99, "KHONG DOC"),
    (10_000, 0.9499, 0.99, "KHONG DAT"),
    (10_000, 0.99, 0.9499, "KHONG DAT"),
    (13_818, 1.0, 1.0, "DAT"),
    (0, 1.0, 1.0, "KHONG DOC"),
])
def test_KET_CUC_DOI_CHIEU_dung_bang_da_ky(n, rc, rt, ky_vong):
    """Ngưỡng ghim bằng LITERAL: đột biến hằng số không làm mù cả gác lẫn máy."""
    assert S.ket_cuc_doi_chieu(n, rc, rt) == ky_vong


# ── file kết quả đối chiếu và cổng chạy ──────────────────────────────────

def test_FILE_DOI_CHIEU_khong_co_hay_hong_hay_KHONG_DAT_thi_khong_cho_chay(tmp_path):
    f = tmp_path / "doi_chieu.json"
    assert S.da_doi_chieu_dat(f) is False             # chưa có
    f.write_text("không phải json", encoding="utf-8")
    assert S.da_doi_chieu_dat(f) is False             # hỏng
    f.write_text('{"x": 1}', encoding="utf-8")
    assert S.da_doi_chieu_dat(f) is False             # thiếu khoá
    S.ghi_ket_qua_doi_chieu(f, {"ket_cuc": "KHONG DAT", "n": 20000}, "x.db", "2026-10-02")
    assert S.da_doi_chieu_dat(f) is False
    S.ghi_ket_qua_doi_chieu(f, {"ket_cuc": "DAT", "n": 20000}, "x.db", "2026-10-02")
    assert S.da_doi_chieu_dat(f) is True
    d = S.doc_ket_qua_doi_chieu(f)
    assert d["moc_da_nhin"] == "2026-08-10" and d["che_do_bo_nho"] == "tat"


@pytest.mark.parametrize("lenh", ["bang-day", "sang"])
def test_LENH_CHAY_TU_CHOI_khi_chua_DAT_va_khong_nap_gia(lenh, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(S, "FILE_DOI_CHIEU", tmp_path / "khong_co.json")

    def ne(*a, **k):
        raise AssertionError("không được nạp giá khi chưa ĐẠT")
    monkeypatch.setattr(S, "nap_gia", ne)
    assert S.main([lenh]) == 2
    assert "TU CHOI" in capsys.readouterr().out


# ── cửa sổ ───────────────────────────────────────────────────────────────

def _luoi(bat_dau_theo_ma, n=50):
    ngay = [f"2025-01-{i + 1:02d}" for i in range(n)]
    B = pd.DataFrame(np.nan, index=ngay, columns=list(bat_dau_theo_ma))
    for ma, s in bat_dau_theo_ma.items():
        B.loc[ngay[s]:, ma] = 1.0
    return B, B.copy()


def test_CUA_SO_la_phien_dau_ma_du_MIN_MA_ma_co_diem_den_cuoi():
    bat = {f"A{j}": 0 for j in range(30)}
    bat.update({f"B{j}": 10 for j in range(10)})       # 40 mã đủ từ phiên 10
    bat.update({f"C{j}": 30 for j in range(5)})        # lên sàn muộn: không kéo cửa sổ
    B, Y = _luoi(bat)
    s, cot = S.cua_so_sang(B, Y)
    assert s == B.index[10]
    assert len(cot) == 40 and not any(m.startswith("C") for m in cot)


def test_CUA_SO_bo_phien_cuoi_chua_co_nhan():
    B, Y = _luoi({f"A{j}": 0 for j in range(45)})
    Y.iloc[-22:] = np.nan                               # đuôi chưa có nhãn
    s, cot = S.cua_so_sang(B, Y)
    assert s == B.index[0] and len(cot) == 45


def test_CUA_SO_khong_du_MIN_MA_ma_thi_None():
    B, Y = _luoi({f"A{j}": 0 for j in range(39)})
    assert S.cua_so_sang(B, Y) is None


def test_CUA_SO_ma_co_lo_giua_chuoi_phai_bat_dau_sau_lo():
    bat = {f"A{j}": 0 for j in range(40)}
    B, Y = _luoi(bat)
    B.iloc[20, 0] = np.nan                              # A0 thủng ở phiên 20
    s, cot = S.cua_so_sang(B, Y)
    assert s == B.index[21] and len(cot) == 40         # 40 mã đủ chỉ từ phiên 21


def test_CUA_SO_khong_phu_thuoc_gia_tri_diem_hay_nhan():
    B, Y = _luoi({f"A{j}": 0 for j in range(30)} | {f"B{j}": 7 for j in range(15)})
    a = S.cua_so_sang(B, Y)
    rng = np.random.default_rng(0)
    B2 = pd.DataFrame(np.where(B.notna(), rng.standard_normal(B.shape), np.nan),
                      index=B.index, columns=B.columns)
    Y2 = pd.DataFrame(np.where(Y.notna(), rng.standard_normal(Y.shape), np.nan),
                      index=Y.index, columns=Y.columns)
    assert S.cua_so_sang(B2, Y2) == a


# ── 3. tỉ lệ qua / rớt đúng ngưỡng ───────────────────────────────────────

def test_TIN_HIEU_cay_vao_QUA_o_it_nhat_95_phan_tram_luot():
    qua = 0
    r = 20
    for hat in range(r):
        gia = _gia(100 + hat)
        bang = _bang(gia, 100 + hat, tin_hieu=1.0)
        k = S.sang_mot(bang, S.nhan_sach(gia), SPEC_TREND, so_hoan_vi=300)
        qua += k["ket_cuc"] == "QUA"
    print(f"tin hieu cay vao: {qua}/{r} luot QUA")
    assert qua >= math.ceil(0.95 * r), f"chi {qua}/{r} luot QUA"


def test_NHIEU_QUA_voi_ti_le_trong_khoang_nhi_thuc_cua_nguong_5_phan_tram():
    """Ứng viên thuần nhiễu: QUA khi Δ > 0 và p < 0,10 ⇒ xác suất 5% một phía.
    200 lượt; khoảng nhị thức 99,9% hai phía của B(200; 0,05)."""
    r, alpha = 200, 0.05
    qua = 0
    for hat in range(r):
        gia = _gia(1000 + hat, n_ma=40, n_ph=150)
        bang = _bang(gia, 1000 + hat)
        k = S.sang_mot(bang, S.nhan_sach(gia), SPEC_TREND, so_hoan_vi=300)
        assert k["ket_cuc"] in ("QUA", "ROT"), k
        qua += k["ket_cuc"] == "QUA"
    tren = D.nguong_im(r, alpha, muc=0.001)
    duoi, tich = 0, 0.0
    for m in range(r + 1):
        tich += math.comb(r, m) * alpha ** m * (1 - alpha) ** (r - m)
        if tich >= 0.001:
            duoi = m
            break
    print(f"nhieu: {qua}/{r} luot QUA, khoang nhi thuc {duoi}..{tren}")
    assert duoi <= qua <= tren, f"{qua}/{r} QUA, khoang {duoi}..{tren}"


def test_UNG_VIEN_giong_het_ban_dang_chay_thi_ROT_vi_delta_bang_0():
    gia = _gia(12)
    nen = {"trend_score": 0.5, "volume_score": 0.5}
    bang = _bang(gia, 12, spec_nen=nen)
    k = S.sang_mot(bang, S.nhan_sach(gia),
                   {"loai": "trong_so", "trong_so": nen}, so_hoan_vi=200)
    assert k["delta"] == 0.0 and k["ket_cuc"] == "ROT"


def test_UNG_VIEN_THUA_ban_dang_chay_ro_rang_thi_ROT_khong_QUA():
    """Nền mang tín hiệu, ứng viên là ồn: Δ < 0 và p nhỏ — vẫn ROT, không QUA."""
    gia = _gia(13)
    bang = _bang(gia, 13, tin_hieu=1.0)
    nhan = S.nhan_sach(gia)
    bang["score"] = bang["trend_score"]                  # nền = có tín hiệu
    k = S.sang_mot(bang, nhan, {"loai": "trong_so", "trong_so": {"sr_score": 1.0}},
                   so_hoan_vi=300)
    assert k["delta"] < 0 and k["ket_cuc"] == "ROT"


def test_KHONG_DOC_khi_it_hon_MIN_MA_ma_hoac_it_hon_NHIP_phien():
    gia = _gia(14, n_ma=30)
    k = S.sang_mot(_bang(gia, 14), S.nhan_sach(gia), SPEC_TREND, so_hoan_vi=100)
    assert k["ket_cuc"] == "KHONG DOC" and k["delta"] is None and k["p"] is None
    gia = _gia(15, n_ph=40)                              # chỉ 17-18 phiên có nhãn
    k = S.sang_mot(_bang(gia, 15), S.nhan_sach(gia), SPEC_TREND, so_hoan_vi=100)
    assert k["ket_cuc"] == "KHONG DOC"


def test_KET_QUA_mot_ung_vien_khong_phu_thuoc_thu_tu_sang():
    gia = _gia(16)
    bang = _bang(gia, 16, tin_hieu=0.4)
    nhan = S.nhan_sach(gia)
    ts = {"loai": "trong_so", "trong_so": {"trend_score": 0.6, "momentum_score": 0.4}}
    a = S.sang_mot(bang, nhan, SPEC_TREND, so_hoan_vi=200)
    S.sang_mot(bang, nhan, ts, so_hoan_vi=200)
    b = S.sang_mot(bang, nhan, SPEC_TREND, so_hoan_vi=200)
    assert a == b


def test_SANG_chi_nhan_dong_qua_sang_null_va_khong_sua_so():
    gia = _gia(17)
    bang = _bang(gia, 17, tin_hieu=1.0)
    uv = lambda qs, ten: {"khai_ngay": "2026-09-01", "mo_ta": ten, "ly_do": "x",
                          "qua_sang": qs, "spec": SPEC_TREND}
    so = {"ung_vien": {"moi": uv(None, "moi"), "da_qua": uv(True, "q"),
                       "da_rot": uv(False, "r"), "moi2": uv(None, "moi2")}}
    ban_sao = repr(so)
    kq = S.sang(so, bang, gia, so_hoan_vi=200)
    assert set(kq) == {"moi", "moi2"}
    assert repr(so) == ban_sao and so["ung_vien"]["moi"]["qua_sang"] is None
    assert S.chon_ung_vien_chua_sang(so) == ["moi", "moi2"]


def test_SANG_nhan_so_khong_hop_le_thi_ne_loi():
    gia = _gia(18)
    bang = _bang(gia, 18)
    bad = {"ung_vien": {"x": {"khai_ngay": "2026-09-01", "mo_ta": "", "ly_do": "",
                              "qua_sang": 1, "spec": SPEC_TREND}}}
    with pytest.raises(ValueError):
        S.sang(bad, bang, gia)


# ── 4. không ghi sổ ứng viên ─────────────────────────────────────────────

_GHI = {"write_text", "write_bytes", "to_csv", "write", "mkdir", "unlink", "replace",
        "rename", "touch", "writelines", "open"}
_CHO_PHEP_GHI = {"ghi_ket_qua_doi_chieu", "ghi_bang_day"}


def _ham_va_loi_goi():
    cay = ast.parse(FILE_TOOL.read_text(encoding="utf-8"))
    ra = []
    for fn in [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)]:
        for c in ast.walk(fn):
            if isinstance(c, ast.Call):
                f = c.func
                ten = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                ra.append((fn.name, ten))
    return ra


def test_CHI_HAI_ham_ghi_file_va_khong_ham_nao_chua_ten_ung_vien_json():
    ghi = {(fn, t) for fn, t in _ham_va_loi_goi() if t in _GHI}
    ngoai = {fn for fn, _ in ghi} - _CHO_PHEP_GHI
    assert not ngoai, f"ham ghi file ngoai danh sach cho phep: {sorted(ngoai)}"
    # hàm ghi nhận ĐƯỜNG làm tham số — không tự đụng `SO_UNG_VIEN`
    cay = ast.parse(FILE_TOOL.read_text(encoding="utf-8"))
    for fn in [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)
               and n.name in _CHO_PHEP_GHI]:
        ten = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name)}
        thuoc = {x.attr for x in ast.walk(fn) if isinstance(x, ast.Attribute)}
        assert not ({"SO_UNG_VIEN"} & (ten | thuoc)), fn.name


def test_DB_seeded_mo_CHI_DOC_va_khong_doi_mot_byte(tmp_path):
    f = tmp_path / "seeded.db"
    con = sqlite3.connect(f)
    con.execute("CREATE TABLE decisions (seq INTEGER PRIMARY KEY, at REAL, symbol TEXT,"
                " signal_date TEXT, score INT, components TEXT)")
    con.executemany("INSERT INTO decisions VALUES (?,?,?,?,?,?)", [
        (1, 1.0, "AAA", "2026-08-07", 50, "{}"),
        (2, 2.0, "AAA", "2026-08-10", 50, "{}"),
        (3, 3.0, "BBB", "2026-08-10 09:00:00", 50, "{}"),
        (4, 4.0, "BBB", "2026-01-02", 51, "{}")])
    con.commit()
    con.close()
    truoc = hashlib.sha256(f.read_bytes()).hexdigest()
    rows, n_ge = S.doc_db_seeded(f)
    assert sorted(r["seq"] for r in rows) == [1, 4] and n_ge == 2
    assert all(r["signal_date"][:10] < "2026-08-10" for r in rows)
    assert hashlib.sha256(f.read_bytes()).hexdigest() == truoc
    ct = ast.parse(FILE_TOOL.read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(ct) if isinstance(n, ast.FunctionDef)
               and n.name == "doc_db_seeded")
    chuoi = [c.value for c in ast.walk(ham) if isinstance(c, ast.Constant)
             and isinstance(c.value, str)]
    assert any("mode=ro" in s for s in chuoi)


def test_LENH_SANG_in_ket_qua_khong_ghi_so_that(monkeypatch, tmp_path, capsys):
    f = tmp_path / "dc.json"
    S.ghi_ket_qua_doi_chieu(f, {"ket_cuc": "DAT", "n": 20000}, "x.db", "2026-10-02")
    monkeypatch.setattr(S, "FILE_DOI_CHIEU", f)
    gia = _gia(19)
    S.ghi_bang_day(tmp_path / "bang.csv", _bang(gia, 19, tin_hieu=1.0))
    monkeypatch.setattr(S, "nap_gia", lambda *a, **k: gia)
    uv = {"khai_ngay": "2026-09-01", "mo_ta": "t", "ly_do": "t", "qua_sang": None,
          "spec": SPEC_TREND}
    monkeypatch.setattr(CB, "doc_so_ung_vien", lambda *a, **k: {"ung_vien": {"u1": uv}})
    that = GOC / "docs" / "ung-vien.json"
    h0 = hashlib.sha256(that.read_bytes()).hexdigest()
    assert S.main(["sang", "--bang", str(tmp_path / "bang.csv")]) == 0
    ra = capsys.readouterr().out
    assert "u1:" in ra and "KHONG ghi so" in ra
    assert hashlib.sha256(that.read_bytes()).hexdigest() == h0


# ── chẩn đoán sau KHÔNG ĐẠT ──────────────────────────────────────────────

def test_CHAN_DOAN_mau_co_dinh_theo_hat_va_chi_lech_o_thanh_phan_bi_lam_lech():
    """Máy lệch ĐÚNG một thành phần (`risk_score`) ở các ô có lịch sử dài: bảng
    chẩn đoán phải chỉ đúng thành phần ấy, đúng nhóm ấy, và chỉ ở đó."""
    gia = _gia(25, n_ma=4, n_ph=120)
    rows = _rows_da_ghi(gia, buoc=1)

    def may(ma, ls, ngay):
        tp, diem = _may_gia(ma, ls, ngay)
        if len(ls) > 101:                     # hàng >= 101: nhóm (100, 250]
            tp["risk_score"] = round(tp["risk_score"] + 5.0, 6)
        return tp, diem

    d = S.chan_doan(rows, gia, may, mau=150, hat=3)
    d2 = S.chan_doan(rows, gia, may, mau=150, hat=3)
    assert d.equals(d2) and len(d) == 150
    assert not d.duplicated(["ma", "ngay"]).any()          # mẫu KHÔNG lặp ô
    dai_ls = d[d["hang"] > 101]
    assert len(dai_ls) > 0
    assert np.allclose(dai_ls["lai_risk_score"] - dai_ls["ghi_risk_score"], 5.0)
    assert not d.equals(S.chan_doan(rows, gia, may, mau=150, hat=4))
    t = S.khop_theo_nhom(d)["hang"]
    ngan, dai = t.index[t.index.map(lambda x: x.right <= 100)], t.index[t.index.map(lambda x: x.left >= 100)]
    assert len(ngan) >= 1 and len(dai) >= 1                  # có NHIỀU nhóm hàng
    assert (t.loc[ngan, "risk_score"] == 1.0).all()
    assert (t.loc[dai, "risk_score"] == 0.0).all()
    for c in ("trend_score", "momentum_score", "volume_score", "sr_score"):
        assert (t[c] == 1.0).all()
    assert int(t["n"].sum()) == 150


def test_CHAN_DOAN_dung_sai_0_1_la_KHOP_con_hon_0_1_la_LECH():
    gia = _gia(28, n_ma=3, n_ph=60)
    rows = _rows_da_ghi(gia, buoc=1)

    def may(do_lech):
        def f(ma, ls, ngay):
            tp, diem = _may_gia(ma, ls, ngay)
            tp["trend_score"] = round(tp["trend_score"] + do_lech, 6)
            return tp, diem
        return f
    for do_lech, ky_vong in ((0.1, 1.0), (0.11, 0.0)):
        d = S.chan_doan(rows, gia, may(do_lech), mau=60, hat=1)
        t = S.khop_theo_nhom(d)["nam"]
        assert (t["trend_score"] == ky_vong).all(), (do_lech, t)


def test_CHAN_DOAN_cung_ne_loi_khi_gia_ro():
    gia = _gia(26, n_ma=2, n_ph=40)
    gia["M00"] = pd.concat([gia["M00"], pd.DataFrame(
        {"time": ["2026-09-01"], "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
         "volume": 1.0}, index=pd.Index(["2026-09-01"], name="ngay"))])
    with pytest.raises(ValueError, match="RO"):
        S.chan_doan([], gia, _may_gia)


def test_SO_HAI_CACHE_dem_dung_nen_chung_nen_khac_va_ma_khac():
    a, b = _gia(27, n_ma=3, n_ph=30), _gia(27, n_ma=3, n_ph=30)
    assert S.so_hai_cache(a, b) == {"n_ma_chung": 3, "n_nen_chung": 90, "n_nen_khac": 0,
                                    "n_ma_co_nen_khac": 0, "ty_le_nen_khac": 0.0}
    b["M01"] = b["M01"].assign(close=b["M01"]["close"] * 1.01)
    b["M02"] = b["M02"].iloc[5:].copy()
    b["M02"].iloc[:3, b["M02"].columns.get_loc("close")] += 1.0
    b["ZZ"] = b["M00"]
    r = S.so_hai_cache(a, b)
    assert r["n_ma_chung"] == 3 and r["n_nen_chung"] == 30 + 25 + 30
    assert r["n_nen_khac"] == 30 + 3 and r["n_ma_co_nen_khac"] == 2
    assert r["ty_le_nen_khac"] == pytest.approx(33 / 85)
    assert S.so_hai_cache({}, {})["ty_le_nen_khac"] is None


# ── file kết quả đối chiếu đã COMMIT ─────────────────────────────────────

def test_FILE_DOI_CHIEU_da_commit_TU_NHAT_QUAN_khong_sua_tay_thanh_DAT():
    """Kết cục trong file phải suy ra được từ chính các số trong file, bằng đúng
    `ket_cuc_doi_chieu`. Sửa tay `ket_cuc` thành DAT (hay sửa số mà không sửa
    kết cục) làm gác đỏ — công cụ chỉ chạy sàng khi file nói ĐẠT."""
    d = S.doc_ket_qua_doi_chieu()
    if d is None:
        pytest.skip("chua co docs/sang-doi-chieu.json")
    assert d["moc_da_nhin"] == S.MOC_DA_NHIN and d["che_do_bo_nho"] == "tat"
    assert set(d["rho_tp"]) == set(CB.THANH_PHAN)
    suy_ra = S.ket_cuc_doi_chieu(d["n"], d["rho_cuoi"], min(d["rho_tp"].values()))
    assert d["ket_cuc"] == suy_ra


# ── hình dạng (đếm) ──────────────────────────────────────────────────────

def test_HINH_DANG_dem_dung_tren_du_lieu_tong_hop_va_khong_ma_day_du_khi_stride_2():
    gia = _gia(20, n_ma=45, n_ph=80)
    rows = _rows_da_ghi(gia, buoc=2, pha=True)
    h = S.hinh_dang(rows, gia)
    assert h["n_dong"] == len(rows) and h["n_ma"] == 45
    assert h["n_dong_loai_ge_moc"] == 0
    # stride 2, mỗi mã một pha: không mã nào có dòng ở hai phiên liền nhau
    assert h["cua_so_ma_du_moi_phien"][2] == 0
    assert h["ma_tran_ma_day_du"] == 0
    assert h["mat_do"] == pytest.approx(0.5, abs=0.02)      # stride 2 → nửa số ô
    assert 22 <= h["ma_moi_phien_max"] <= 23 and 22 <= h["ma_moi_phien_trung_vi"] <= 23
    assert h["phien_du_40_ma"] == 0


def test_HINH_DANG_buoc_1_thi_ma_tran_giu_du_ma():
    gia = _gia(21, n_ma=45, n_ph=80)
    h = S.hinh_dang(_rows_da_ghi(gia, buoc=1), gia)
    assert h["ma_tran_ma_day_du"] == 45
    assert h["mat_do"] == pytest.approx(1.0)
    assert h["ma_moi_phien_trung_vi"] == 45 and h["ma_moi_phien_max"] == 45
    assert h["n_phien"] == h["n_phien_lich"] == 70 and h["phien_du_40_ma"] == 70
    assert h["n_o"] == 70 * 45
    assert h["cua_so_ma_du_moi_phien"] == {2: 45, 5: 45, 10: 45, 22: 45}


def test_DUNG_CU_khai_NGUNG_DUNG_tu_BUOC_155_nhung_van_con_de_tai_lap_DO_23():
    assert "ĐÃ NGỪNG DÙNG từ BƯỚC 155" in S.__doc__
    assert "GIỮ NGUYÊN" in S.__doc__
    for ten in ("hinh_dang", "doi_chieu", "chan_doan", "so_hai_cache"):
        assert callable(getattr(S, ten))                 # ĐO 23 còn tái lập được
    assert CB.MOC_MOT_VONG == "2026-10-02"


# ── ngưỡng đã ký khớp mã ─────────────────────────────────────────────────

def _muc_do23():
    van = TIEU_CHI.read_text(encoding="utf-8")
    dau = van.index("## ĐO 23")
    sau = re.search(r"\n## ", van[dau + 5:])
    return van[dau: dau + 5 + sau.start()] if sau else van[dau:]


def test_HANG_SO_ghim_bang_LITERAL_va_khop_tieu_chi_da_ky():
    assert S.MOC_DA_NHIN == "2026-08-10"
    assert S.HAT == 20261002
    assert S.SO_HOAN_VI == 2000
    assert S.NGUONG_P_SANG == 0.10
    assert S.N_DOI_CHIEU_TOI_THIEU == 10_000
    assert S.RHO_DOI_CHIEU_TOI_THIEU == 0.95
    assert S.CACHE_GIA.name == "cache" and S.CACHE_GIA.parent.name == "backtest"
    muc = _muc_do23()
    for chuoi in ("2026-08-10", "20261002", "2.000 hoán vị", "< **0,10**",
                  "≥ 10.000", "≥ 0,95", "`MIN_MA` = 40", "`che_do_hoc=\"tat\"`"):
        assert chuoi in muc, chuoi
    assert CB.MIN_MA == 40 and CB.NHIP == 21
