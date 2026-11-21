"""Chuẩn bị Lát 5 của C4 (BƯỚC 293): (a) độ lệch lịch của Tầng 2 và (c) bảng sự thật (oracle) của Tầng 2.

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 18 khoản 12 (a)·(c) và mục 19. Hai nhóm phép thử:

* (a) `thi_truong_gia.dong_thoi_gian(lech)` — Tầng 1 (`lech = 0`) phải ra ĐÚNG BIT đầu ra cũ (bản cũ dán nguyên văn ở đây
  làm đối chứng, và các con số ghim); Tầng 2 (`lech = 250`) ra 139 · 160 · 183 / 412 · 433 · 456 / 605 đo ở mục 18 khoản 12a,
  viết lại ĐỘC LẬP bằng `pandas.bdate_range`, và khớp `vong_hoc_gia.phien_khai` đọc trên chính lịch Tầng 2.
* (c) `tools/oracle_tang2_thi_truong_gia.py` — phép tính ΔIC_true khớp `thi_truong_gia.tinh_su_that` từng số trên cùng một
  mẫu, đường chấm là CHÍNH `cham_diem` (không bản sao), hạt riêng và qua cửa `kiem_luong`, kết quả không phụ thuộc số tiến
  trình, cửa sổ trượt cắt đúng, gác AST của dụng cụ. Mẫu NHỎ; lượt chạy cỡ 5.000 phiên × 60 mã ở dụng cụ, không ở pytest.

Dòng hạt thử: 9001. KHÔNG test nào sinh dòng 2, 3, 4, 5.
"""
import ast
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cham_bong as cb  # noqa: E402
import experiment_tran_dac_trung as E  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402
import vong_hoc_gia as V  # noqa: E402

DUONG_TOOL = GOC / "tools" / "oracle_tang2_thi_truong_gia.py"
_spec = importlib.util.spec_from_file_location("oracle_tang2_thi_truong_gia", DUONG_TOOL)
OR = importlib.util.module_from_spec(_spec)
sys.modules["oracle_tang2_thi_truong_gia"] = OR
_spec.loader.exec_module(OR)

LUONG_TEST = 9001
KAPPA_2X = 0.04458670117751986   # κ của mức 2× MDE₈₀ trong docs/thi-truong-gia-hieu-chuan.json (Lát 2)


# ══ (a) ĐỘ LỆCH LỊCH ═════════════════════════════════════════════════════════════════════════════════════════

def _dong_thoi_gian_ban_cu() -> dict:
    """`thi_truong_gia.dong_thoi_gian()` NGUYÊN VĂN ở `origin/main` @ `62c36ea` (trước BƯỚC 293), chép ở đây làm đối chứng."""
    lich = T.lich_phien(12 * 21 + T.SO_PHIEN_DA_NHIN)
    thang = [(dt.date.fromisoformat(d).year, dt.date.fromisoformat(d).month) for d in lich]
    nam, th = thang[T.SO_PHIEN_DA_NHIN - 1]
    khai = []
    for i in range(1, T.SO_UNG_VIEN_KHAI + 1):
        m0 = th - 1 + i
        muc = (nam + m0 // 12, m0 % 12 + 1)
        khai.append(thang.index(muc))
    doc = [k + (cb.MOC_DOC - 1) + T.DO_TRE_NHAN for k in khai]
    tong = doc[-1] + T.SO_PHIEN_TIEN_VE_TRUOC + T.DO_TRE_NHAN + 1
    return {"S": T.SO_PHIEN_DA_NHIN, "F": T.SO_PHIEN_TIEN_VE_TRUOC, "khai": khai,
            "khai_ngay": [lich[k] for k in khai], "doc": doc, "tong": tong}


def test_Tang1_dong_thoi_gian_giu_NGUYEN_dau_ra_cu_va_cac_con_so_da_ghi():
    d = T.dong_thoi_gian()
    assert d == _dong_thoi_gian_ban_cu() and T.dong_thoi_gian(lech=0) == d and T.dong_thoi_gian(0) == d
    assert list(d) == ["S", "F", "khai", "khai_ngay", "doc", "tong"]            # không thêm khoá nào ở Tầng 1
    assert d == {"S": 126, "F": 126, "khai": [128, 150, 172],
                 "khai_ngay": ["2100-07-01", "2100-08-02", "2100-09-01"], "doc": [401, 423, 445], "tong": 594}


def test_lech_phai_la_so_nguyen_khong_am():
    for xau in (-1, 2.5, "250", None, True):
        with pytest.raises(ValueError):
            T.dong_thoi_gian(lech=xau)


def test_Tang2_dong_thoi_gian_2_la_139_160_183_doc_412_433_456_tong_605():
    d = G.dong_thoi_gian_2()
    assert d["khai"] == [139, 160, 183] and d["doc"] == [412, 433, 456] and d["tong"] == 605
    assert d["lech"] == G.SO_PHIEN_KHOI_DONG == 250 and (d["S"], d["F"]) == (126, 126)
    assert d["khai_ngay"] == ["2101-07-01", "2101-08-01", "2101-09-01"]
    assert {k: v for k, v in d.items() if k != "lech"} == T.dong_thoi_gian(lech=250)
    assert G.dong_thoi_gian_2(0) == {**T.dong_thoi_gian(), "lech": 0}           # lech 0 là Tầng 1


def _viet_lai_doc_lap(lech: int) -> dict:
    """Viết lại bằng pandas, không dùng `T.dong_thoi_gian`: lịch thứ Hai–Sáu liền từ `NGAY_DAU`; phiên có quyết định k nằm ở
    hàng `lech + k` của lịch; ứng viên i khai ở phiên có quyết định ĐẦU TIÊN của tháng thứ i sau tháng của phiên S − 1."""
    lich = [x.strftime("%Y-%m-%d") for x in pd.bdate_range(T.NGAY_DAU, periods=lech + 900)]
    qd = lich[lech:]
    thang_cua_so = pd.Timestamp(qd[T.SO_PHIEN_DA_NHIN - 1]).to_period("M")
    khai = []
    for i in range(1, 4):
        muc = thang_cua_so + i
        khai.append(next(k for k, n in enumerate(qd) if pd.Timestamp(n).to_period("M") == muc))
    doc = [k + 251 + 22 for k in khai]
    return {"khai": khai, "khai_ngay": [qd[k] for k in khai], "doc": doc, "tong": doc[-1] + 126 + 22 + 1}


@pytest.mark.parametrize("lech", [0, 250, 17, 400])
def test_dong_thoi_gian_khop_cach_viet_lai_doc_lap_o_nhieu_do_lech(lech):
    d = T.dong_thoi_gian(lech=lech)
    ky_vong = _viet_lai_doc_lap(lech)
    assert {k: d[k] for k in ky_vong} == ky_vong


def test_vong_doc_dung_ngay_Tang2_cho_ra_chinh_cac_phien_khai_cua_dong_thoi_gian_2():
    """Vòng KHÔNG gọi `dong_thoi_gian` (gác G4) mà suy phiên khai từ lịch của dữ liệu nó nhận. Đưa cho nó lịch của phiên có
    quyết định Tầng 2: phải ra ĐÚNG các phiên khai của `dong_thoi_gian_2` — chứng minh độ lệch là chỗ Tầng 2 cần, và
    rằng vòng đã sống đúng với lịch ấy (số phiên 605 mới là thứ phải sửa)."""
    d = G.dong_thoi_gian_2()
    ngay = [x.strftime("%Y-%m-%d") for x in pd.bdate_range(T.NGAY_DAU, periods=G.SO_PHIEN_KHOI_DONG + d["tong"])]
    qd = ngay[G.SO_PHIEN_KHOI_DONG:]
    assert V.phien_khai(qd, 3) == d["khai"] and [V.phien_doc(k) for k in d["khai"]] == d["doc"]
    assert V.phien_khai(list(T.lich_phien(594)), 3) == T.dong_thoi_gian()["khai"]        # Tầng 1 như cũ
    assert V.phien_khai(qd, 3) != T.dong_thoi_gian()["khai"]


def test_Tang2_sinh_mac_dinh_605_phien_va_cua_so_tien_ve_truoc_cua_ung_vien_cuoi_du():
    t = G.sinh_thi_truong_2(LUONG_TEST, 7, 0.0)
    d = G.dong_thoi_gian_2()
    assert t.so_phien == 605 and len(t.ngay) == 855
    # ứng viên khai sau cùng: phiên hiệu lực = doc + 1; F phiên có nhãn cần giá tới hiệu lực + F − 1 + 22, nên cần ĐÚNG
    # hiệu lực + F + 22 phiên — 605 vừa khít, còn 594 (số của Tầng 1) thiếu 11 phiên ở Tầng 2
    assert t.so_phien == d["doc"][-1] + 1 + T.SO_PHIEN_TIEN_VE_TRUOC + T.DO_TRE_NHAN - 1 + 1
    assert t.so_phien - 594 == 11


def test_Tang1_sinh_mac_dinh_van_594_phien_khong_doi():
    assert T.sinh_thi_truong(LUONG_TEST, 7, 0.0, co_su_that=False).gia.shape == (594, 60)


# ══ (c) BẢNG SỰ THẬT TẦNG 2 ════════════════════════════════════════════════════════════════════════════════

def test_bang_su_that_khop_tinh_su_that_Tang1_tung_so_tren_cung_mot_mau():
    """Phép tính ΔIC_true của dụng cụ Tầng 2 = phép tính của `T.tinh_su_that` (cùng 12 spec, cùng sai số khối), khi đưa cho nó
    đúng thành phần/điểm/nhãn của một mẫu Tầng 1. Đây là phép thử máy đo: tính thứ đã biết đáp án (Tầng 1) bằng đường mới."""
    so_phien = 500
    st = T.tinh_su_that(LUONG_TEST, 5, KAPPA_2X, so_phien=so_phien)
    mau = T._sinh_loi(np.random.default_rng([LUONG_TEST, 5, T.HAT_SU_THAT]), so_phien, KAPPA_2X)
    kh = {m: pd.DataFrame({"close": mau["close"][:, i]}) for i, m in enumerate(T._ma_gia())}
    nhan = E.nhan_vuot_ro(kh, cb.NHIP).to_numpy()
    moi = OR.bang_su_that(mau["thanh_phan"], mau["diem"], nhan)
    assert set(moi["spec"]) == set(st["spec"]) and len(moi["spec"]) == 12
    for ten, v in st["spec"].items():
        assert moi["spec"][ten]["delta_ic"] == pytest.approx(v["delta_ic"], abs=1e-12), ten
        assert moi["spec"][ten]["se_mc"] == pytest.approx(v["se_mc"], abs=1e-12), ten
    assert moi["so_phien_co_nhan"] == st["so_phien_co_nhan"]


def test_bang_su_that_do_duoc_dap_an_biet_truoc_diem_bang_nhan_va_diem_nguoc_nhan():
    rng = np.random.default_rng([LUONG_TEST, 11])
    n, m = 300, 20
    nhan = rng.standard_normal((n, m))
    nhan[-22:] = np.nan
    ngau = rng.standard_normal((n, m))
    tp = {k: ngau + 0.0 * i for i, k in enumerate(cb.THANH_PHAN)}
    tp["volume_score"] = nhan.copy()                      # thành phần BẰNG nhãn: IC = 1
    tp["volume_score"][-22:] = 0.0
    diem = np.rint(50 + 10 * ngau).astype(np.int64)
    r = OR.bang_su_that(tp, diem, nhan)
    assert r["ic_rieng"]["volume_score"]["ic"] == pytest.approx(1.0, abs=1e-12)
    assert abs(r["ic_rieng"]["trend_score"]["ic"]) < 0.1 and abs(r["ic_rieng"]["score"]["ic"]) < 0.1
    assert r["spec"][T.TEN_SPEC_G]["delta_ic"] > 0.85
    assert r["spec"][T.TEN_SPEC_H]["delta_ic"] < r["spec"][T.TEN_SPEC_G]["delta_ic"]
    nguoc = {**tp, "volume_score": -tp["volume_score"]}
    assert OR.bang_su_that(nguoc, diem, nhan)["spec"][T.TEN_SPEC_G]["delta_ic"] < -0.85


def test_nhan_thieu_o_giua_bi_no_vi_nhan_chi_duoc_thieu_o_duoi():
    nhan = np.ones((50, 4))
    nhan[10] = np.nan
    with pytest.raises(AssertionError):
        OR.bang_su_that({k: np.ones((50, 4)) for k in cb.THANH_PHAN}, np.ones((50, 4), dtype=np.int64), nhan)


def test_hat_rieng_thu_ba_la_2_khac_hat_oracle_Tang1_va_hat_thi_truong():
    assert OR.HAT_ORACLE_2 == 2 != T.HAT_SU_THAT == 1
    kd, qd = 20, 300
    a = OR.sinh_mau(LUONG_TEST, 5, KAPPA_2X, qd, kd)
    khac = G.sinh_thi_truong_2(LUONG_TEST, 5, KAPPA_2X, so_phien=qd, so_khoi_dong=kd)
    dung = G._sinh_ohlcv_loi(np.random.default_rng([LUONG_TEST, 5, 2]), kd + qd, KAPPA_2X)
    ma = a.ma[0]
    np.testing.assert_array_equal(a.gia[ma]["close"].to_numpy(), dung["close"][:, 0])
    np.testing.assert_array_equal(a.gia[ma]["volume"].to_numpy(), dung["volume"][:, 0])
    assert not np.allclose(a.gia[ma]["close"].to_numpy(), khac.gia[ma]["close"].to_numpy())
    tang1 = T._sinh_loi(np.random.default_rng([LUONG_TEST, 5, T.HAT_SU_THAT]), kd + qd, KAPPA_2X)
    assert not np.allclose(a.gia[ma]["close"].to_numpy(), tang1["close"][:, 0])
    again = OR.sinh_mau(LUONG_TEST, 5, KAPPA_2X, qd, kd)                          # tái lập bit
    np.testing.assert_array_equal(a.gia[ma]["close"].to_numpy(), again.gia[ma]["close"].to_numpy())


@pytest.mark.parametrize("luong", [2, 3, 4, 5, 6, 0, -1, True, 1.0, "1", None])
def test_dong_hat_bi_chan_o_moi_duong_vao_bo_sinh(luong):
    with pytest.raises(ValueError):
        OR.sinh_mau(luong, 1, 0.0, 100)
    if isinstance(luong, int) and not isinstance(luong, bool):
        assert OR.main(["--luong", str(luong), "--so-phien", "200"]) == 2


def test_dong_hat_cho_phep_chi_1_va_9001():
    OR.kiem_luong(1)
    OR.kiem_luong(9001)


def test_duong_cham_la_CHINH_cham_diem_diem_la_int_final_score_thanh_phan_la_score_breakdown():
    tt = OR.sinh_mau(LUONG_TEST, 3, KAPPA_2X, 6, 30)
    ma = tt.ma[:2]
    kq = OR.cham_mau(tt, ma=ma, cua_so=None)
    dong = G.cham_diem(tt, ma=ma)
    b = cb.doc_quyet_dinh(dong, tu_ngay=min(d["signal_date"] for d in dong))
    for j, m in enumerate(ma):
        con = b[b["symbol"] == m].sort_values("ngay")
        np.testing.assert_array_equal(kq["diem"][:, j], con["score"].to_numpy())
        for k in cb.THANH_PHAN:
            np.testing.assert_allclose(kq["thanh_phan"][k][:, j], con[k].to_numpy(float), rtol=0, atol=0)
    assert kq["diem"].dtype == np.int64 and kq["khong_ok"] == 0 and kq["diem"].shape == (6, 2)


def test_cua_so_truot_cat_dung_so_dong_lich_su_va_None_la_mo_rong(monkeypatch):
    import paper_runner as pr
    do_dai = []

    def gia_lap(ma, df, san, ngay):
        do_dai.append(len(df))
        return {"final_score": 50.0, "recommendation": "x", "score_breakdown": {}, "key_reasons": [], "data_quality": "OK"}
    monkeypatch.setattr(pr, "_analyze", gia_lap)
    tt = G.sinh_thi_truong_2(LUONG_TEST, 2, 0.0, so_phien=10, so_khoi_dong=40)
    G.cham_diem_theo_ma(tt, "GIA01")
    assert do_dai == [41 + k for k in range(10)]
    do_dai.clear()
    G.cham_diem_theo_ma(tt, "GIA01", cua_so=45)
    assert do_dai == [min(41 + k, 45) for k in range(10)] and max(do_dai) == 45
    do_dai.clear()
    G.cham_diem_theo_ma(tt, "GIA01", phien=[9], cua_so=5)
    assert do_dai == [5]


def test_cua_so_mac_dinh_la_khoi_dong_cong_dong_thoi_gian_2():
    assert OR.CUA_SO_CHAM == 250 + G.dong_thoi_gian_2()["tong"] == 855


def test_ket_qua_khong_phu_thuoc_so_tien_trinh_va_ghep_dung_thu_tu_ma():
    from concurrent.futures import ProcessPoolExecutor
    ma = ("GIA01", "GIA02")
    mot = OR.tinh_nhieu_mau(LUONG_TEST, [4], KAPPA_2X, 70, ma=ma, cua_so=None, pool=None, so_khoi=3)
    with ProcessPoolExecutor(max_workers=2) as pool:
        hai = OR.tinh_nhieu_mau(LUONG_TEST, [4], KAPPA_2X, 70, ma=ma, cua_so=None, pool=pool, so_khoi=3)
    for ten, v in mot[0]["spec"].items():
        assert hai[0]["spec"][ten]["delta_ic"] == v["delta_ic"] and hai[0]["spec"][ten]["se_mc"] == v["se_mc"]
    assert mot[0]["ic_rieng"] == hai[0]["ic_rieng"] and mot[0]["hat"] == [LUONG_TEST, 4, 2]


def test_nhieu_mau_dung_moi_chi_so_mot_hat_rieng_va_xep_dung_thu_tu():
    ma = ("GIA01",)
    ra = OR.tinh_nhieu_mau(LUONG_TEST, [4, 5], KAPPA_2X, 70, ma=ma, cua_so=None, pool=None, so_khoi=3)
    assert [r["hat"] for r in ra] == [[LUONG_TEST, 4, 2], [LUONG_TEST, 5, 2]]
    assert ra[0]["spec"][T.TEN_SPEC_G]["delta_ic"] != ra[1]["spec"][T.TEN_SPEC_G]["delta_ic"]
    don = OR.tinh_nhieu_mau(LUONG_TEST, [5], KAPPA_2X, 70, ma=ma, cua_so=None, pool=None, so_khoi=3)
    assert don[0]["spec"][T.TEN_SPEC_G]["delta_ic"] == ra[1]["spec"][T.TEN_SPEC_G]["delta_ic"]


def _mau_gia(delta, se, ic):
    ten = list(T.ho_spec_oracle())
    return {"spec": {t: {"delta_ic": d, "se_mc": s} for t, d, s in zip(ten, delta, se)},
            "ic_rieng": {"trend_score": {"ic": ic, "se_mc": 0.01}}}


def test_gop_mau_trung_binh_va_sai_so_can_tong_binh_phuong_chia_k():
    n = len(T.ho_spec_oracle())
    a, b = _mau_gia([0.10] * n, [0.03] * n, 0.2), _mau_gia([0.20] * n, [0.04] * n, 0.4)
    g = OR.gop_mau([a, b])
    v = g["spec"][T.TEN_SPEC_G]
    assert v["delta_ic"] == pytest.approx(0.15) and v["se"] == pytest.approx(np.sqrt(0.03 ** 2 + 0.04 ** 2) / 2)
    assert v["sd_giua_mau"] == pytest.approx(np.std([0.1, 0.2], ddof=1) / np.sqrt(2))
    assert g["ic_rieng"]["trend_score"]["ic"] == pytest.approx(0.3) and g["so_mau"] == 2
    assert OR.gop_mau([a])["spec"][T.TEN_SPEC_G]["sd_giua_mau"] is None


def test_kiem_NULL_hai_sai_so_bat_dung_spec_ngoai_va_bo_qua_spec_trong():
    n = len(T.ho_spec_oracle())
    ten = list(T.ho_spec_oracle())
    delta, se = [0.001] * n, [0.01] * n
    delta[3] = 0.02                                       # đúng 2 sai số: ngoài (≥)
    delta[5] = -0.0199                                    # trong
    g = OR.gop_mau([_mau_gia(delta, se, 0.0)])
    assert OR.spec_ngoai_hai_se_gop(g) == [ten[3]]
    assert OR.spec_ngoai_hai_se_gop(g, he_so=3.0) == []


# ── gác AST của dụng cụ ──────────────────────────────────────────────────────────────────────────────────

TEN_GHI = {"push", "write_all", "append_rows", "ghi_ke_hoach", "record_trade", "update_trade", "record_decision",
           "write_text", "write_bytes", "to_csv", "to_json", "dump", "to_parquet", "to_pickle", "savetxt", "save",
           "savez", "executemany", "commit", "open", "ghi"}
CAM_CHUOI = ("ung-vien", "phuong-an-bong", "UV-", "backtest", "cache", "vnstock", "paper_trades")


def _cay():
    return ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))


def _goi(cay) -> set:
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            ra.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return ra


def test_G1_dung_cu_khong_ghi_file_nao_khong_so_khong_mang():
    cay = _cay()
    assert not (_goi(cay) & TEN_GHI), sorted(_goi(cay) & TEN_GHI)
    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
    assert not (nhap & {"sheets_store", "keo_bang_gia", "doc_so_that", "socket", "requests", "urllib", "sqlite3",
                        "paper_trading", "paper_runner"}), nhap


def test_G3_G5_dung_cu_khong_nhac_the_gioi_that_va_moi_chuoi_ngay_la_ngay_gia():
    cay = _cay()
    doc = {id(n.body[0].value) for n in ast.walk(cay) if isinstance(n, (ast.Module, ast.FunctionDef)) and n.body
           and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)
           and isinstance(n.body[0].value.value, str)}
    chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc]
    assert not [s for s in chuoi if any(c in s for c in CAM_CHUOI)]
    ngay = [s for s in chuoi if len(s) == 10 and s[4] == "-" and s[7] == "-" and s[:4].isdigit()]
    assert all(s >= "2100-01-04" for s in ngay)


def _ham_goi_sinh_thieu_cua(nguon: str) -> list[str]:
    vao = {"sinh_thi_truong_2", "_sinh_ohlcv_loi", "sinh_thi_truong", "sinh_null", "tinh_su_that", "_sinh_loi"}
    sai = []
    for f in (n for n in ast.walk(ast.parse(nguon)) if isinstance(n, ast.FunctionDef)):
        sinh = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call)
                and ((isinstance(n.func, ast.Attribute) and n.func.attr in vao) or (isinstance(n.func, ast.Name) and n.func.id in vao))]
        if not sinh:
            continue
        cua = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "kiem_luong"]
        if not cua or min(cua) > min(sinh):
            sai.append(f.name)
    return sai


def test_AST_moi_ham_goi_bo_sinh_phai_goi_kiem_luong_truoc_va_do_bat_duoc_mau_xau():
    nguon = DUONG_TOOL.read_text(encoding="utf-8")
    assert _ham_goi_sinh_thieu_cua(nguon) == []
    assert "sinh_mau" in {f.name for f in ast.walk(ast.parse(nguon)) if isinstance(f, ast.FunctionDef)
                          and any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "sinh_thi_truong_2" for n in ast.walk(f))}
    assert _ham_goi_sinh_thieu_cua("def f(l):\n    return G.sinh_thi_truong_2(l, 1, 0.0)\n") == ["f"]
    assert _ham_goi_sinh_thieu_cua("def f(l):\n    x = G.sinh_thi_truong_2(l, 1, 0.0)\n    kiem_luong(l)\n") == ["f"]
    assert _ham_goi_sinh_thieu_cua("def f(l):\n    kiem_luong(l)\n    return G.sinh_thi_truong_2(l, 1, 0.0)\n") == []


def test_dung_cu_khong_co_doi_so_nao_ve_dong_hat_ngoai_luong_va_khong_ghi_ket_qua():
    cay = _cay()
    co = [n.args[0].value for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "add_argument" and n.args and isinstance(n.args[0], ast.Constant)]
    assert "--luong" in co and not [c for c in co if "ghi" in c or "luu" in c or "out" in c]


# ── điểm ghi và dòng lệnh ────────────────────────────────────────────────────────────────────────────────

def test_diem_ghi_la_int_cat_cut_khong_lam_tron_nhu_cot_score_cua_dong_quyet_dinh(monkeypatch):
    import paper_runner as pr
    gia_tri = iter([57.9, 57.1, 5.99, 95.0])

    def gia_lap(ma, df, san, ngay):
        return {"final_score": next(gia_tri), "recommendation": "x", "key_reasons": [], "data_quality": "OK",
                "score_breakdown": {k: 10.0 * (i + 1) for i, k in enumerate(cb.THANH_PHAN)}}
    monkeypatch.setattr(pr, "_analyze", gia_lap)
    tt = G.sinh_thi_truong_2(LUONG_TEST, 2, 0.0, so_phien=4, so_khoi_dong=30)
    _, diem, tp, khong_ok = OR._viec_cham_ma((tt, "GIA01", None))
    assert diem.tolist() == [57, 57, 5, 95] and khong_ok == 0
    assert tp["trend_score"].tolist() == [10.0] * 4 and tp["risk_score"].tolist() == [50.0] * 4


def test_main_chay_xong_mau_nho_in_json_voi_chi_so_tang_dan_va_ma_thoat_0(capsys):
    kq = OR.main(["--luong", "9001", "--kappa", "0.0446", "--so-phien", "100", "--so-mau", "2", "--chi-so-dau", "201",
                  "--so-ma-cham", "1", "--cua-so", "0", "--json"])
    ra = capsys.readouterr().out
    assert kq == 0 and "BẢNG SỰ THẬT TẦNG 2" in ra
    j = json.loads(next(d for d in ra.splitlines() if d.startswith("KET_QUA_JSON "))[len("KET_QUA_JSON "):])
    assert j["chi_so"] == [201, 202] and [m["hat"] for m in j["tung_mau"]] == [[9001, 201, 2], [9001, 202, 2]]
    assert j["so_ma"] == 1 and j["so_lan_cham"] == 200 and j["cua_so"] is None
