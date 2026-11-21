"""Thị trường giả Tầng 2 — bộ sinh OHLCV mang `z` bằng khối lượng, và chấm điểm qua `paper_runner._analyze` THẬT
(C4 Lát 4, BƯỚC 292; `thi_truong_gia_tang2.py`, `tools/chay_tang2_thi_truong_gia.py`).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4.1–4.2, 4.6, 4.8, 4.9, 6 (hàng P: P1), 7 và 8 ("Lát 4"). Ba loại phép thử:

* BỘ SINH — khung OHLCV nhất quán (qua `validate_ohlcv`, biên ±7%), tái lập bit theo hạt, NULL và 2× CÙNG khối lượng,
  khối lượng mang `z` (tương quan đo được, có đối chứng âm), ngày giả (G5), hằng KHAI ghim.
* CHẤM ĐIỂM — mỗi dòng là một lần `_analyze` THẬT (so với lời gọi trực tiếp), lịch sử cắt tới phiên (không nhìn trộm),
  P1 xanh trên thị trường nhỏ và ĐỎ trên từng mẫu hỏng, hai bẫy đã đo (va chạm khoá cache, engine bộ nhớ hậu nghiệm).
* CÁCH LY — không mạng (tạo socket nổ), không file chung (`backtest/cache*`, `sl_pattern_memory.json`, `paper_trades.db`,
  `~/.vnstock`), G1/G3 theo AST, G2 (đường thật không nhập module này; ở `tests/test_vong_hoc_thi_truong_gia.py`).

Dòng hạt thử: 9001 (dòng thử, ngoài năm dòng chính của mục 4.8). KHÔNG test nào sinh dòng 2, 3, 4, 5. Thị trường NHỎ
(60 mã sinh, chỉ chấm vài mã × vài phiên): lượt chạy cả 60 mã × 594 phiên nằm ở dụng cụ, không ở pytest.
"""
import ast
import builtins
import importlib.util
import json
import os
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cham_bong as cb  # noqa: E402
import data_quality as dq  # noqa: E402
import lich_giao_dich as lich  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402

DUONG = GOC / "thi_truong_gia_tang2.py"
DUONG_TOOL = GOC / "tools" / "chay_tang2_thi_truong_gia.py"
_spec = importlib.util.spec_from_file_location("chay_tang2_thi_truong_gia", DUONG_TOOL)
CT = importlib.util.module_from_spec(_spec)
sys.modules["chay_tang2_thi_truong_gia"] = CT
_spec.loader.exec_module(CT)

LUONG_TEST = 9001
KAPPA_2X = 0.04458670117751986   # κ của mức 2× MDE₈₀ trong docs/thi-truong-gia-hieu-chuan.json (Lát 2)
N_KD, N_QD = 60, 12              # thị trường nhỏ: 60 phiên khởi động + 12 phiên có quyết định


@pytest.fixture(scope="module")
def tt():
    return G.sinh_thi_truong_2(LUONG_TEST, 1, KAPPA_2X, so_phien=N_QD, so_khoi_dong=N_KD)


@pytest.fixture(scope="module")
def loi_dai():
    """Mẫu dài để đo tương quan khối lượng–z: 600 phiên × 60 mã, cả mảng z (chỉ test thấy z)."""
    return G._sinh_ohlcv_loi(np.random.default_rng([LUONG_TEST, 3]), 600, KAPPA_2X)


# ══ BỘ SINH ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_khung_dung_cot_dung_cuoc_so_phien_va_ngay_giai_doan_G5(tt):
    assert tuple(tt.gia["GIA01"].columns) == G.COT_OHLCV == dq.REQUIRED_COLUMNS
    assert len(tt.ma) == T.SO_MA and set(tt.gia) == set(tt.ma)
    assert len(tt.ngay) == N_KD + N_QD and tt.so_khoi_dong == N_KD and tt.so_phien == N_QD
    assert all(len(df) == N_KD + N_QD for df in tt.gia.values())
    ngay = list(tt.gia["GIA01"]["time"])
    assert ngay == list(tt.ngay) == list(T.lich_phien(N_KD + N_QD))
    ts = pd.to_datetime(ngay)
    assert (ts.weekday < 5).all() and ts.is_monotonic_increasing and ts.is_unique
    assert min(ngay) >= T.NGAY_DAU == "2100-01-04"
    assert all(lich.co_phien(d) is None for d in ngay), "ngày giả lọt vào lịch công bố (G5)"
    # phiên CÓ quyết định đầu tiên là ngày thứ N_KD + 1 của lịch, không phải NGAY_DAU
    assert tt.ngay_quyet_dinh == tt.ngay[N_KD:] and tt.ngay_quyet_dinh[0] == T.lich_phien(N_KD + 1)[-1]


def test_so_phien_mac_dinh_la_dong_thoi_gian_cua_dac_ta_cong_250_khoi_dong():
    t = G.sinh_thi_truong_2(LUONG_TEST, 2, 0.0)
    assert G.SO_PHIEN_KHOI_DONG == 250
    assert t.so_phien == T.dong_thoi_gian()["tong"] == 594 and len(t.ngay) == 250 + 594


def test_OHLC_nhat_quan_trong_bien_7_phan_tram_va_validate_ohlcv_muc_OK(tt):
    for ma, df in tt.gia.items():
        o, h, l, c, v = (df[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
        assert (l <= np.minimum(o, c)).all() and (np.maximum(o, c) <= h).all(), ma     # CHẶT, không dung sai (BƯỚC 292)
        assert (l > 0).all() and (v > 0).all()
        ref = np.concatenate([[c[0]], c[:-1]])
        assert (np.abs(c / ref - 1) <= T.BIEN_NGAY + 1e-9).all(), ma
        assert (h <= ref * (1 + T.BIEN_NGAY) + 1e-9).all() and (l >= ref * (1 - T.BIEN_NGAY) - 1e-9).all(), ma
        assert (np.abs(o / ref - 1) <= G.TRAN_GAP + 1e-9).all(), ma
        bao = dq.validate_ohlcv(df, ma, G.SAN_GIAO_DICH, as_of=str(df["time"].iloc[-1]))
        assert bao.level == dq.Severity.OK, (ma, [i.message for i in bao.issues])
        assert dq.price_multiplier(df) == 1000.0, "giá nghìn đồng như nguồn thật: price_multiplier phải ra 1000"


def test_OHLC_chat_khong_dung_sai_ca_o_phien_cham_bien_7_phan_tram_mau_dai(loi_dai):
    """Lỗi đã bị P1 bắt ở lượt chạy đầu tiên (BƯỚC 292): lợi nhuận kẹp ở đúng biên nên `close/ref` có thể vượt biên
    1e-16, và nến thành `đóng cửa > cao` ở bậc làm tròn — `validate_ohlcv` (so chặt) báo WARN. Mẫu nhỏ KHÔNG có ca nào
    chạm biên (kết quả âm của nó vô nghĩa: lỗi 66), nên ca này đo trên mẫu dài VÀ đòi mẫu có ca chạm biên."""
    o, h, l, c = (loi_dai[k] for k in ("open", "high", "low", "close"))
    ref = np.vstack([c[:1], c[:-1]])
    cham_bien = np.abs(c / ref - 1) >= T.BIEN_NGAY - 1e-12
    assert cham_bien.sum() >= 1, "mẫu không có phiên nào chạm biên: phép thử không có khả năng cho kết quả dương"
    assert (l <= np.minimum(o, c)).all() and (np.maximum(o, c) <= h).all()
    assert not ((c > h) | (c < l) | (o > h) | (o < l)).any()


def test_validate_ohlcv_bat_duoc_khung_hong_cua_chinh_bo_sinh(tt):
    """Phép thử NGƯỢC (máy đo cũng bị nghi ngờ): bẻ một phiên thì mức phải lên cao hơn OK."""
    df = tt.gia["GIA01"].copy()
    df.loc[40, "high"] = float(df.loc[40, "low"]) - 1.0
    assert dq.validate_ohlcv(df, "GIA01", "HOSE", as_of=str(df["time"].iloc[-1])).level > dq.Severity.OK


def test_khoi_luong_nguyen_duong_boi_cua_lo_100(tt):
    for df in tt.gia.values():
        v = df["volume"]
        assert v.dtype == np.int64 and (v > 0).all() and (v % G.BUOC_KHOI_LUONG == 0).all()


def test_tai_lap_bit_theo_hat_va_hat_khac_cho_khung_khac():
    a = G.sinh_thi_truong_2(LUONG_TEST, 5, KAPPA_2X, so_phien=6, so_khoi_dong=30)
    b = G.sinh_thi_truong_2(LUONG_TEST, 5, KAPPA_2X, so_phien=6, so_khoi_dong=30)
    c = G.sinh_thi_truong_2(LUONG_TEST, 6, KAPPA_2X, so_phien=6, so_khoi_dong=30)
    for m in a.ma:
        pd.testing.assert_frame_equal(a.gia[m], b.gia[m], check_exact=True)
    assert not np.array_equal(a.gia["GIA01"]["close"], c.gia["GIA01"]["close"])
    assert not np.array_equal(a.gia["GIA01"]["volume"], c.gia["GIA01"]["volume"])


def test_NULL_va_co_loi_the_CUNG_hat_cung_khoi_luong_chi_khac_gia():
    """`kappa` chỉ đi vào kỳ vọng lợi nhuận: mọi số ngẫu nhiên thêm rút SAU `_sinh_loi` và KHÔNG phụ thuộc nó."""
    null = G.sinh_thi_truong_2(LUONG_TEST, 7, 0.0, so_phien=40, so_khoi_dong=60)
    co = G.sinh_thi_truong_2(LUONG_TEST, 7, KAPPA_2X, so_phien=40, so_khoi_dong=60)
    for m in null.ma:
        assert np.array_equal(null.gia[m]["volume"], co.gia[m]["volume"]), m
    assert not np.array_equal(null.gia["GIA01"]["close"], co.gia["GIA01"]["close"])
    # và ĐÚNG phần giá của Tầng 1: cùng `_sinh_loi` nên `close` của Tầng 2 bằng `close` của lõi Tầng 1 cùng hạt
    lo = T._sinh_loi(np.random.default_rng([LUONG_TEST, 7]), 100, KAPPA_2X)
    assert np.array_equal(co.gia["GIA05"]["close"].to_numpy(), lo["close"][:, 4])


def test_khoi_luong_mang_z_tuong_quan_do_duoc_va_doi_chung_am(loi_dai):
    """Mục 4.2: z đi qua khối lượng. log khối lượng bỏ cỡ riêng của từng mã tương quan với z cỡ C_Z/√(C_Z²+σ²);
    đối chứng: với z của một thị trường KHÁC tương quan phải ≈ 0 (máy đo có thể cho kết quả âm)."""
    lv = np.log(loi_dai["volume"].astype(float))
    lv = lv - lv.mean(axis=0, keepdims=True)
    z = loi_dai["z"] - loi_dai["z"].mean(axis=0, keepdims=True)
    ly_thuyet = G.HE_SO_Z_KHOI_LUONG / np.hypot(G.HE_SO_Z_KHOI_LUONG, G.SIGMA_KHOI_LUONG)
    r = np.corrcoef(lv.ravel(), z.ravel())[0, 1]
    assert abs(r - ly_thuyet) < 0.03, (r, ly_thuyet)
    z_khac = G._sinh_ohlcv_loi(np.random.default_rng([LUONG_TEST, 4]), 600, KAPPA_2X)["z"]
    assert abs(np.corrcoef(lv.ravel(), z_khac.ravel())[0, 1]) < 0.05
    # chỉ KHỐI LƯỢNG đọc z trực tiếp: biên trong ngày và nhảy mở cửa không mang z
    gap = loi_dai["open"][1:] / loi_dai["close"][:-1] - 1
    rau = loi_dai["high"] / np.maximum(loi_dai["open"], loi_dai["close"]) - 1
    assert abs(np.corrcoef(gap.ravel(), z[1:].ravel())[0, 1]) < 0.05
    assert abs(np.corrcoef(rau.ravel(), z.ravel())[0, 1]) < 0.05


def test_khoi_luong_mang_z_ca_o_NULL_kappa_chi_la_nut_cua_gia():
    lo = G._sinh_ohlcv_loi(np.random.default_rng([LUONG_TEST, 3]), 600, 0.0)
    lv = np.log(lo["volume"].astype(float))
    lv = lv - lv.mean(axis=0, keepdims=True)
    assert np.corrcoef(lv.ravel(), lo["z"].ravel())[0, 1] > 0.7


def test_cac_hang_KHAI_ghim_dung_gia_tri_da_khai():
    assert (G.HE_SO_Z_KHOI_LUONG, G.SIGMA_KHOI_LUONG, G.KHOI_LUONG_TRUNG_VI, G.SIGMA_CO_MA, G.BUOC_KHOI_LUONG,
            G.SIGMA_GAP, G.TRAN_GAP, G.SIGMA_BIEN_TRONG_NGAY, G.SO_PHIEN_KHOI_DONG, G.SAN_GIAO_DICH) == (
        0.4, 0.3, 1_000_000, 0.7, 100, 0.003, 0.02, 0.006, 250, "HOSE")


def test_tu_choi_dau_vao_sai():
    with pytest.raises(ValueError):
        G.sinh_thi_truong_2(LUONG_TEST, 1, -0.1, so_phien=5, so_khoi_dong=30)
    with pytest.raises(ValueError):
        G.sinh_thi_truong_2(LUONG_TEST, 0, 0.0, so_phien=5, so_khoi_dong=30)
    with pytest.raises(ValueError):
        G.sinh_thi_truong_2(LUONG_TEST, 1, 0.0, so_phien=5, so_khoi_dong=-1)


# ══ CHẤM ĐIỂM QUA ĐƯỜNG ỐNG THẬT ══════════════════════════════════════════════════════════════════════════

MA_NHO, PHIEN_NHO = ("GIA01", "GIA02", "GIA03"), (0, 5, 11)


@pytest.fixture(scope="module")
def dong_nho(tt):
    return G.cham_diem(tt, ma=MA_NHO, phien=PHIEN_NHO)


def test_moi_dong_la_MOT_lan_analyze_that_khong_ban_sao(tt, dong_nho):
    import paper_runner as pr
    assert len(dong_nho) == len(MA_NHO) * len(PHIEN_NHO)
    with G.moi_truong_cham():
        for d in dong_nho:
            t = N_KD + int(np.flatnonzero(np.array(tt.ngay_quyet_dinh) == d["signal_date"])[0])
            res = pr._analyze(d["symbol"], tt.gia[d["symbol"]].iloc[: t + 1], "HOSE", tt.ngay[t])
            assert d["score"] == int(res["final_score"]) and d["recommendation"] == res["recommendation"]
            assert json.loads(d["components"]) == json.loads(json.dumps(res["score_breakdown"]))
            assert d["data_quality"] == res["data_quality"] == "OK"


def test_dong_quyet_dinh_dung_khuon_decisions_va_P1_xanh(tt, dong_nho):
    assert G.kiem_p1(tt, dong_nho, len(MA_NHO), len(PHIEN_NHO)) == []
    assert set(dong_nho[0]) == set(G.cot_bang_decisions())
    assert [d["seq"] for d in dong_nho] == list(range(1, len(dong_nho) + 1))
    # thứ tự: phiên trước, trong phiên theo thứ tự mã
    assert [(d["signal_date"], d["symbol"]) for d in dong_nho] == [
        (tt.ngay[N_KD + k], m) for k in PHIEN_NHO for m in MA_NHO]
    b = cb.doc_quyet_dinh(dong_nho, tu_ngay=tt.ngay_quyet_dinh[0])
    assert len(b) == len(dong_nho) and b.attrs["bo"] == 0


def test_chi_so_phien_ngoai_khoang_bi_tu_choi_va_phien_dau_khong_thuoc_khoi_dong(tt):
    assert G.kiem_p1(tt, G.cham_diem(tt, ma=("GIA01",), phien=(0,)), 1, 1) == []
    with pytest.raises(ValueError):
        G.cham_diem_theo_ma(tt, "GIA01", [-1])
    with pytest.raises(ValueError):
        G.cham_diem_theo_ma(tt, "GIA01", [N_QD])


def test_lich_su_cat_toi_phien_khong_nhin_trom_tuong_lai(tt):
    """Bất biến 1: thay TOÀN BỘ nến sau phiên k bằng nhiễu thì điểm ở phiên ≤ k không đổi (giữ nguyên giá trị tới k)."""
    k, t = 6, N_KD + 6
    bien = {m: df.copy() for m, df in tt.gia.items()}
    rng = np.random.default_rng(LUONG_TEST)
    for m in ("GIA01", "GIA02"):
        for c in ("open", "high", "low", "close"):
            bien[m].loc[t + 1:, c] = bien[m].loc[t + 1:, c].to_numpy() * rng.uniform(0.5, 1.5, size=len(bien[m]) - t - 1)
        bien[m].loc[t + 1:, "volume"] = 1_000
    tt2 = G.ThiTruongGia2(luong=tt.luong, chi_so=tt.chi_so, kappa=tt.kappa, so_khoi_dong=tt.so_khoi_dong,
                          so_phien=tt.so_phien, ngay=tt.ngay, ma=tt.ma, gia=bien)
    for m in ("GIA01", "GIA02"):
        a = G.cham_diem_theo_ma(tt, m, [k])
        b = G.cham_diem_theo_ma(tt2, m, [k])
        assert a == b
        c = G.cham_diem_theo_ma(tt2, m, [N_QD - 1])
        assert c != G.cham_diem_theo_ma(tt, m, [N_QD - 1]), "phép thử mồi phải đổi được điểm ở phiên SAU"


# ── P1: phép đo bắt được từng mẫu hỏng (máy đo cũng bị nghi ngờ) ─────────────────────────────────────────

def _hong(dong, i, **sua):
    ra = [dict(d) for d in dong]
    ra[i].update(sua)
    return ra


@pytest.mark.parametrize("ten,sua", [
    ("cot_thua", {"them": 1}), ("score_float", {"score": 61.5}), ("score_bool", {"score": True}),
    ("score_duoi_5", {"score": 4}), ("score_tren_95", {"score": 96}), ("at_int", {"at": 5}),
    ("seq_float", {"seq": 1.0}), ("components_hong", {"components": "{khong phai json"}),
    ("thieu_thanh_phan", {"components": json.dumps({"trend_score": 50.0})}),
    ("thanh_phan_ngoai_khoang", {"components": json.dumps({k: 101.0 for k in cb.THANH_PHAN})}),
    ("thanh_phan_nan", {"components": json.dumps({k: float("nan") for k in cb.THANH_PHAN})}),
    ("chat_luong_WARN", {"data_quality": "WARN"}), ("chat_luong_rong", {"data_quality": ""}),
    ("ngay_khoi_dong", {"signal_date": "2100-01-04"}),
])
def test_P1_do_duoc_mau_hong(tt, dong_nho, ten, sua):
    assert G.kiem_p1(tt, _hong(dong_nho, 0, **sua), len(MA_NHO), len(PHIEN_NHO)), f"P1 bỏ lọt mẫu hỏng: {ten}"


def test_P1_do_duoc_thieu_thua_dong_va_trung_khoa(tt, dong_nho):
    assert G.kiem_p1(tt, dong_nho[:-1], len(MA_NHO), len(PHIEN_NHO))                 # thiếu một dòng
    assert G.kiem_p1(tt, dong_nho + [dict(dong_nho[0], seq=999)], len(MA_NHO), len(PHIEN_NHO))   # thừa + trùng khoá
    bo_cot = [{k: v for k, v in d.items() if k != "skip_reason"} for d in dong_nho]
    assert G.kiem_p1(tt, bo_cot, len(MA_NHO), len(PHIEN_NHO))                          # thiếu cột


def test_cot_bang_decisions_doc_tu_so_that_khong_go_tay():
    assert set(G.cot_bang_decisions()) == {"seq", "at", "symbol", "signal_date", "score", "recommendation", "acted",
                                           "skip_reason", "components", "reasons", "data_quality"}


# ── hai bẫy đã đo ────────────────────────────────────────────────────────────────────────────────────────

def test_BAY_khoa_cache_khong_chua_noi_dung_gia_hai_thi_truong_dung_khoa(tt):
    """`_ANALYZE_CACHE` khoá bằng (mã, số dòng, ngày cuối, ngày phiên): hai thị trường giả cùng tên mã và lịch, khác
    hạt, VA CHẠM — thị trường thứ hai nhận NGUYÊN kết quả của thị trường thứ nhất. Lượt chấm của module này xoá cache
    nên không trúng. (Nếu `paper_runner` đổi khoá và phép thử đầu của ca này đỏ, bẫy đã được chữa: bỏ phần xoá cache.)"""
    import paper_runner as pr
    tt2 = G.sinh_thi_truong_2(LUONG_TEST, 2, KAPPA_2X, so_phien=N_QD, so_khoi_dong=N_KD)
    t, ma = N_KD + 8, "GIA01"
    cat = lambda x: x.gia[ma].iloc[: t + 1]
    with G.moi_truong_cham():
        a = pr._analyze(ma, cat(tt), "HOSE", tt.ngay[t])
        b = pr._analyze(ma, cat(tt2), "HOSE", tt2.ngay[t])      # KHÔNG xoá cache giữa hai thị trường
        assert b is a, "khoá cache không còn va chạm giữa hai thị trường: bẫy đã chữa"
        pr._xoa_cache_phan_tich()
        b_that = pr._analyze(ma, cat(tt2), "HOSE", tt2.ngay[t])
    assert b_that is not a and b_that["score_breakdown"] != a["score_breakdown"], "hai thị trường phải cho điểm khác"
    dong = G.cham_diem_theo_ma(tt2, ma, [8])[0]
    assert dong["score_breakdown"] == b_that["score_breakdown"] != a["score_breakdown"]
    # và hai lượt chấm liên tiếp TRONG CÙNG tiến trình (cùng mã, cùng ngày) không dính nhau
    assert G.cham_diem_theo_ma(tt, ma, [8])[0]["score_breakdown"] == a["score_breakdown"]


def test_moi_truong_cham_tat_engine_hau_nghiem_va_tra_lai_ca_hai(tt, tmp_path, monkeypatch):
    import paper_runner as pr
    import post_mortem_learning as pml
    monkeypatch.chdir(tmp_path)
    (tmp_path / pml.MEMORY_FILE).write_text("{khong phai json", encoding="utf-8")    # mồi: engine mặc định sẽ đọc nó
    goc = pml._ENGINE_CACHE
    engine_cu = pml.dat_lai_engine(str(tmp_path / "bo_nho_cu.json"), enabled=True)
    pr._ANALYZE_CACHE[("do-vat-cu",)] = {"x": 1}
    try:
        with G.moi_truong_cham():
            e = pml.get_learning_engine()
            assert e is not engine_cu and e.enabled is False and e.sl_patterns == []
            assert not os.path.exists(e.memory_file), "engine tắt phải trỏ vào đường KHÔNG có file"
            assert pr._ANALYZE_CACHE == {}
            assert pr._dau_van_bo_nho() == (False,)
        assert pml._ENGINE_CACHE is engine_cu and engine_cu.enabled is True
        assert pr._ANALYZE_CACHE == {("do-vat-cu",): {"x": 1}}
        # và khi nổ giữa chừng vẫn trả lại
        with pytest.raises(RuntimeError):
            with G.moi_truong_cham():
                raise RuntimeError("nổ")
        assert pml._ENGINE_CACHE is engine_cu and ("do-vat-cu",) in pr._ANALYZE_CACHE
    finally:
        pr._ANALYZE_CACHE.pop(("do-vat-cu",), None)
        pml._ENGINE_CACHE = goc


# ══ CÁCH LY: không mạng, không file chung ═════════════════════════════════════════════════════════════════

def test_khong_mang_tao_socket_la_no_trong_luc_cham_diem_mot_thi_truong(tt, monkeypatch):
    G.cham_diem(tt, ma=("GIA01",), phien=(0,))          # khởi động: nạp mọi module (urllib3 thăm dò IPv6 lúc nhập)
    goi = []

    class NoSocket(socket.socket):
        def __init__(self, *a, **k):
            goi.append("socket")
            raise AssertionError("tạo socket trong lúc chấm điểm")

    def cam(ten):
        def f(*a, **k):
            goi.append(ten)
            raise AssertionError(f"{ten} trong lúc chấm điểm")
        return f

    monkeypatch.setattr(socket, "socket", NoSocket)
    for ten in ("create_connection", "getaddrinfo", "gethostbyname", "socketpair"):
        monkeypatch.setattr(socket, ten, cam(ten))
    dong = G.cham_diem(tt, ma=MA_NHO, phien=PHIEN_NHO)
    assert len(dong) == 9 and G.kiem_p1(tt, dong, 3, 3) == [] and goi == []
    with pytest.raises(AssertionError):                      # máy đo cũng bị nghi ngờ: chốt chặn có thật
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_khong_file_chung_khong_mo_cache_bo_nho_so_hay_vnstock(tt, monkeypatch, tmp_path):
    G.cham_diem(tt, ma=("GIA01",), phien=(0,))          # nạp module trước: chỉ đo phần CHẤM ĐIỂM
    monkeypatch.chdir(tmp_path)
    cam = ("backtest", "cache", "sl_pattern_memory", "paper_trades", ".vnstock", ".db", "sheets", "google")
    mo = []
    goc_open = builtins.open
    goc_sqlite = sqlite3.connect

    def open_do(f, *a, **k):
        mo.append(str(f))
        return goc_open(f, *a, **k)

    def sqlite_do(f, *a, **k):
        mo.append("sqlite:" + str(f))
        return goc_sqlite(f, *a, **k)

    monkeypatch.setattr(builtins, "open", open_do)
    monkeypatch.setattr(sqlite3, "connect", sqlite_do)
    goc_exists = os.path.exists
    hoi = []
    monkeypatch.setattr(os.path, "exists", lambda p: (hoi.append(str(p)), goc_exists(p))[1])
    dong = G.cham_diem(tt, ma=MA_NHO, phien=PHIEN_NHO)
    assert len(dong) == 9
    cham = [p for p in mo + hoi if any(c in p.lower() for c in cam)]
    assert cham == [], f"đụng file chung: {cham}"
    assert [p for p in mo if p.startswith("sqlite:") and p != "sqlite::memory:"] == []
    assert list(tmp_path.iterdir()) == [], "lượt chấm để lại dấu vết trên đĩa"


# ══ DỤNG CỤ ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_dung_cu_dung_lai_cua_kiem_luong_cua_chay_vong():
    import chay_vong_thi_truong_gia as CV
    assert CT.kiem_luong is CV.kiem_luong and CT.LUONG_TEST == LUONG_TEST


@pytest.mark.parametrize("luong", [2, 3, 4, 5, 6, 0, -1, True, 1.0, "1"])
def test_dung_cu_no_voi_dong_hat_bi_chan_va_main_tra_2(luong):
    with pytest.raises(ValueError):
        CT.chay_mot_thi_truong(luong, 1, 0.01, so_ma_cham=1, so_phien=3, so_khoi_dong=30)
    if isinstance(luong, int) and not isinstance(luong, bool):
        assert CT.main(["--luong", str(luong), "--chi-so", "1", "--kappa", "0.01"]) == 2


def test_dung_cu_chay_xong_thi_truong_nho_ma_thoat_0_va_in_chi_phi_va_P1(capsys):
    assert CT.main(["--luong", "9001", "--chi-so", "1", "--muc", "2", "--so-ma-cham", "2", "--so-phien", "4",
                    "--so-khoi-dong", "40"]) == 0
    ra = capsys.readouterr().out
    assert "CHI PHÍ" in ra and "ms một lần" in ra and "ĐẠT, 0 vi phạm" in ra and "PHÂN PHỐI" in ra


def test_dung_cu_tra_1_khi_P1_co_vi_pham(monkeypatch, capsys):
    monkeypatch.setattr(G, "kiem_p1", lambda *a, **k: ["vi pham gia"])
    assert CT.main(["--luong", "9001", "--chi-so", "1", "--kappa", "0.01", "--so-ma-cham", "1", "--so-phien", "3",
                    "--so-khoi-dong", "30"]) == 1
    assert "VI PHẠM" in capsys.readouterr().out


def test_dung_cu_khong_co_doi_so_dong_hat_ngoai_luong():
    cay = ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))
    co = [n.args[0].value for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "add_argument" and n.args and isinstance(n.args[0], ast.Constant)]
    assert "--luong" in co and "--chi-so" in co


# ══ GÁC AST ═══════════════════════════════════════════════════════════════════════════════════════════════

TEN_GHI = {"push", "write_all", "append_rows", "ghi_ke_hoach", "record_trade", "update_trade", "record_decision",
           "write_text", "write_bytes", "to_csv", "to_json", "dump", "to_parquet", "to_pickle", "savetxt", "save",
           "savez", "executemany", "commit"}
CAM_TEN_THAT = {"SO_UNG_VIEN", "doc_so_ung_vien", "sheets_store", "keo_bang_gia", "doc_so_that", "oracle",
                "tinh_su_that", "su_that", "ho_spec_oracle"}
CAM_CHUOI = ("ung-vien", "phuong-an-bong", "UV-", "backtest", "cache", "vnstock", "paper_trades")
TEN_DONG_HO_MANG = {"now", "today", "now_vn", "today_vn", "sleep", "perf_counter", "monotonic", "time", "urlopen",
                    "request", "connect", "create_connection", "read_csv"}
NHAP_DUOC = {"__future__", "contextlib", "json", "dataclasses", "datetime", "numpy", "pandas", "cham_bong",
             "thi_truong_gia", "paper_runner", "post_mortem_learning", "paper_trading"}


def _cay(duong):
    return ast.parse(duong.read_text(encoding="utf-8"))


def _goi(cay) -> set:
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            ra.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return ra


def _ten_dung(cay) -> set:
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Name):
            ra.add(n.id)
        elif isinstance(n, ast.Attribute):
            ra.add(n.attr)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                ra.add(a.name.split(".")[-1])
                if a.asname:
                    ra.add(a.asname)
    return ra


def _chuoi_ma(cay) -> list:
    """Hằng chuỗi KHÔNG phải docstring (docstring là lời giải thích, được nhắc tên thứ bị cấm)."""
    doc = set()
    for n in ast.walk(cay):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
            doc.add(id(n.body[0].value))
    return [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in doc]


def _mo_ghi(cay) -> list:
    ra = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
            mode = n.args[1] if len(n.args) > 1 else next((k.value for k in n.keywords if k.arg == "mode"), None)
            if isinstance(mode, ast.Constant) and any(c in str(mode.value) for c in "wax+"):
                ra.append(n)
            elif mode is not None and not isinstance(mode, ast.Constant):
                ra.append(n)
    return ra


def _so_nhat_ky_sai(cay) -> list:
    sai = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            ten = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if ten != "PaperTradingJournal":
                continue
            doi = n.args[0] if n.args else next((k.value for k in n.keywords if k.arg == "path"), None)
            if not (isinstance(doi, ast.Constant) and doi.value == ":memory:"):
                sai.append(ast.dump(n)[:90])
    return sai


def _nhap(cay) -> set:
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            ra.add((n.module or "").split(".")[0])
    return ra


def test_G1_module_khong_ghi_khong_mo_file_chi_so_nhat_ky_memory():
    cay = _cay(DUONG)
    assert not (_goi(cay) & TEN_GHI), sorted(_goi(cay) & TEN_GHI)
    assert not _mo_ghi(cay) and "open" not in _goi(cay)
    assert not _so_nhat_ky_sai(cay), _so_nhat_ky_sai(cay)
    assert "PaperTradingJournal" in _goi(cay), "gác canh quần thể rỗng: P1 đọc cột bảng từ sổ :memory:"


def test_G1_mau_xau_va_tot_cua_chinh_phep_do():
    for m in ("df.to_csv('x')", "p.write_text('x')", "con.commit()", "journal.record_decision(a)", "con.executemany(q, r)"):
        assert _goi(ast.parse(m)) & TEN_GHI, m
    for m in ("PaperTradingJournal('paper_trades.db')", "PaperTradingJournal(DB)"):
        assert _so_nhat_ky_sai(ast.parse(m)), m
    for m in ("PaperTradingJournal(':memory:')", "x = json.dumps(d)"):
        c = ast.parse(m)
        assert not (_goi(c) & TEN_GHI) and not _so_nhat_ky_sai(c), m


def test_G3_module_khong_cham_the_gioi_that_khong_dong_ho_khong_mang_khong_oracle():
    cay = _cay(DUONG)
    sai = [s for s in _chuoi_ma(cay) if any(c in s for c in CAM_CHUOI)]
    assert not sai, f"chuỗi chạm thế giới thật: {sai}"
    assert not (_ten_dung(cay) & CAM_TEN_THAT), sorted(_ten_dung(cay) & CAM_TEN_THAT)
    assert not (_goi(cay) & TEN_DONG_HO_MANG), sorted(_goi(cay) & TEN_DONG_HO_MANG)
    assert _nhap(cay) <= NHAP_DUOC, sorted(_nhap(cay) - NHAP_DUOC)
    assert not ({"socket", "requests", "urllib", "time", "os", "sys", "san_dau"} & _nhap(cay))


def test_G3_mau_xau_va_tot_cua_chinh_phep_do():
    for m in ("x = 'backtest/cache/FPT.csv'", "x = 'docs/ung-vien.json'", "x = 'UV-001'", "x = 'paper_trades.db'"):
        assert any(c in s for s in _chuoi_ma(ast.parse(m)) for c in CAM_CHUOI), m
    assert not _chuoi_ma(ast.parse('"""backtest cache ung-vien trong docstring"""\nx = 1'))
    for m in ("from cham_bong import SO_UNG_VIEN", "T.tinh_su_that(1)", "import sheets_store", "x = tt.su_that"):
        assert _ten_dung(ast.parse(m)) & CAM_TEN_THAT, m
    for m in ("datetime.now()", "time.sleep(1)", "urllib.request.urlopen(u)", "pd.read_csv(p)", "s.connect(a)"):
        assert _goi(ast.parse(m)) & TEN_DONG_HO_MANG, m
    for m in ("import socket", "import requests"):
        assert _nhap(ast.parse(m)) - NHAP_DUOC, m


def test_G3_nap_module_khong_keo_theo_the_gioi_that():
    """Theo ĐƯỜNG NHẬP gián tiếp: nạp trong một tiến trình sạch rồi chấm MỘT điểm, xem `sys.modules`. Sổ thật, Google
    Sheets, bộ kéo bảng giá, vnstock không được lên (đường chấm thật nhập `paper_trading`, `paper_runner` — chủ ý)."""
    ma = ("import sys, json; sys.path.insert(0, %r); import thi_truong_gia_tang2 as G; "
          "t = G.sinh_thi_truong_2(9001, 1, 0.0, so_phien=2, so_khoi_dong=30); G.cham_diem(t, ma=('GIA01',), phien=(0,)); "
          "cam = ['sheets_store', 'keo_bang_gia', 'doc_so_that', 'gspread', 'google_sheets_sync', 'run_daily', "
          "'vnstock', 'vnstock_data']; "
          "print(json.dumps([m for m in cam if m in sys.modules]))" % str(GOC))
    r = subprocess.run([sys.executable, "-I", "-c", ma], capture_output=True, text=True, cwd=str(GOC),
                       timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    assert json.loads(r.stdout.strip().splitlines()[-1]) == [], r.stdout


def test_G5_AST_moi_hang_chuoi_ngay_trong_module_la_ngay_gia():
    cay = _cay(DUONG)
    ngay = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and len(n.value) == 10 and n.value[4] == "-" and n.value[7] == "-" and n.value[:4].isdigit()]
    assert all(g >= "2100-01-04" for g in ngay), ngay      # module không khai ngày nào: ngày đến từ `T.lich_phien`
    assert G.SO_PHIEN_KHOI_DONG == 250 and "T.lich_phien" in ast.unparse(cay)


def _ham(cay) -> dict:
    return {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}


def _ham_goi_bo_sinh_thieu_cua(nguon: str) -> list[str]:
    vao = {"sinh_thi_truong_2", "_sinh_ohlcv_loi", "sinh_thi_truong", "sinh_null", "tinh_su_that", "_sinh_loi"}
    sai = []
    for ten, f in _ham(ast.parse(nguon)).items():
        dong_sinh = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call)
                     and ((isinstance(n.func, ast.Attribute) and n.func.attr in vao)
                          or (isinstance(n.func, ast.Name) and n.func.id in vao))]
        if not dong_sinh:
            continue
        dong_cua = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "kiem_luong"]
        if not dong_cua or min(dong_cua) > min(dong_sinh):
            sai.append(ten)
    return sai


def test_AST_moi_ham_cua_dung_cu_goi_bo_sinh_phai_goi_kiem_luong_truoc():
    nguon = DUONG_TOOL.read_text(encoding="utf-8")
    assert _ham_goi_bo_sinh_thieu_cua(nguon) == []
    assert "chay_mot_thi_truong" in {t for t, f in _ham(ast.parse(nguon)).items() if _goi(f) & {"sinh_thi_truong_2"}}


def test_AST_phep_do_bat_dung_mau_xau_cua_cua_kiem_luong():
    xau = "def f(l):\n    return G.sinh_thi_truong_2(l, 1, 0.0)\n"
    xau2 = "def f(l):\n    x = G.sinh_thi_truong_2(l, 1, 0.0)\n    kiem_luong(l)\n"
    xau3 = "def f(l):\n    return G._sinh_ohlcv_loi(r, 5, 0.0)\n"
    tot = "def f(l):\n    kiem_luong(l)\n    return G.sinh_thi_truong_2(l, 1, 0.0)\n"
    assert _ham_goi_bo_sinh_thieu_cua(xau) == ["f"] and _ham_goi_bo_sinh_thieu_cua(xau2) == ["f"]
    assert _ham_goi_bo_sinh_thieu_cua(xau3) == ["f"] and _ham_goi_bo_sinh_thieu_cua(tot) == []
    assert _ham_goi_bo_sinh_thieu_cua("def f(l):\n    return 1\n") == []
