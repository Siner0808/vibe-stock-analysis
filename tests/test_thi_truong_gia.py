"""Thị trường giả có lợi thế cài sẵn — Tầng 1 (C4 Lát 1, BƯỚC 261; `thi_truong_gia.py`).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4 và mục 7. Một bộ sinh chỉ đáng tin
khi nó được thử trên thứ nó sinh ra để bắt, nên phần lớn file này là phép thử MÁY ĐO:
oracle phải thấy lợi thế khi có (G dương, H âm) và im lặng khi không có (NULL), và sai
số Monte Carlo của chính nó phải được hiệu chuẩn (một ước lượng sai số sai làm mọi
"≈ 0" thành lời hứa suông — lỗi 61).

Dòng hạt thử: `LUONG_TEST` = 9001, NGOÀI năm dòng chính 1…5 của mục 4.8 và ngoài dãy
6, 7… dành cho bản đặc tả đã sửa, để không test nào đọc một thị trường của lượt chạy chính.

Gác AST (G1, G3, G5 của mục 7) theo khuôn `tests/test_san_dau.py`, kèm phép thử bắt đúng
mẫu xấu/tốt của chính chúng.
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import cham_bong as cb  # noqa: E402
import data_quality as dq  # noqa: E402
import experiment_tran_dac_trung as E  # noqa: E402
import lich_giao_dich as lich  # noqa: E402
import thi_truong_gia as T  # noqa: E402

DUONG = GOC / "thi_truong_gia.py"
LUONG_TEST = 9001
KAPPA_CO = 0.01          # núm lợi thế thử; Lát 2 mới hiệu chuẩn κ theo MDE₈₀
DUNG_SAI_TUONG_QUAN = 0.05   # dung sai khai: |Spearman sinh − bảng MO-XE| ≤ 0,05 ở mọi cặp


@pytest.fixture(scope="module")
def tt():
    """Một thị trường CÓ lợi thế, chưa dựng oracle (nhanh)."""
    return T.sinh_thi_truong(LUONG_TEST, 1, KAPPA_CO, co_su_that=False)


@pytest.fixture(scope="module")
def tt_oracle():
    return T.sinh_thi_truong(LUONG_TEST, 2, KAPPA_CO, co_su_that=True)


# ── dòng thời gian (mục 4.6): SUY RA từ lịch, kiểm bằng máy đo thật ─────────

def _chi_so_dau_thang(lich_ngay) -> list[int]:
    """Chỉ số phiên đầu tiên của mỗi tháng dương lịch, theo thứ tự — viết lại ĐỘC LẬP bằng pandas."""
    thang = pd.to_datetime(pd.Series(list(lich_ngay))).dt.to_period("M")
    return [int(i) for i in thang.drop_duplicates().index]


def test_dong_thoi_gian_cong_cac_doan_khong_go_tay():
    d = T.dong_thoi_gian()
    ngay = [x.strftime("%Y-%m-%d") for x in pd.bdate_range(T.NGAY_DAU, periods=800)]
    dau_thang = _chi_so_dau_thang(ngay)
    thang_cua_so = pd.Timestamp(ngay[T.SO_PHIEN_DA_NHIN - 1]).to_period("M")
    ky_vong_khai = [i for i in dau_thang if pd.Timestamp(ngay[i]).to_period("M") > thang_cua_so][:3]
    assert d["khai"] == ky_vong_khai and d["khai_ngay"] == [ngay[i] for i in ky_vong_khai]
    assert all(g > T.SO_PHIEN_DA_NHIN - 1 for g in d["khai"])
    # mỗi ứng viên đọc ở phiên có nhãn thứ 252 CÙNG với 22 phiên giá để nhãn ấy có thật
    assert d["doc"] == [k + (cb.MOC_DOC - 1) + 22 for k in d["khai"]]
    assert d["tong"] == d["doc"][-1] + T.SO_PHIEN_TIEN_VE_TRUOC + 23
    assert (d["S"], d["F"]) == (126, 126)


def test_dong_thoi_gian_khop_nhan_THAT_cua_may_do():
    """Kiểm bằng `E.nhan_vuot_ro` (không bằng công thức tự viết lại): cắt thị trường ở phiên đọc thì
    ứng viên i có ĐÚNG `cb.MOC_DOC` phiên có nhãn từ ngày khai; và ở độ dài tổng, F phiên sau phiên
    đọc CUỐI đều có nhãn, không phiên nào thừa."""
    d = T.dong_thoi_gian()
    gia = T.sinh_thi_truong(LUONG_TEST, 3, 0.0, so_phien=d["tong"], co_su_that=False).gia
    kh = {m: pd.DataFrame({"close": gia[m].to_numpy()}) for m in gia.columns}
    for k, doc in zip(d["khai"], d["doc"]):
        nhan = E.nhan_vuot_ro({m: v.iloc[:doc + 1] for m, v in kh.items()}, cb.NHIP)
        co = nhan.notna().all(axis=1).to_numpy()
        assert int(co[k:].sum()) == cb.MOC_DOC, (k, doc)
        assert not co[doc], "phiên đọc chưa có nhãn của chính nó: nhãn cần giá tới t + 22"
    nhan = E.nhan_vuot_ro(kh, cb.NHIP)
    co = nhan.notna().all(axis=1).to_numpy()
    cuoi = d["doc"][-1] + T.SO_PHIEN_TIEN_VE_TRUOC
    assert co[:cuoi + 1].all() and not co[cuoi + 1:].any(), "cửa sổ tiến-về-trước phải vừa khít, không thừa"
    assert len(gia) == d["tong"]


def test_ba_ngay_khai_khac_thang_duong_lich_lien_tiep():
    """Trần `cb.TRAN_MOI_THANG` đọc theo THÁNG DƯƠNG LỊCH của `khai_ngay`: cách 21 phiên không đủ."""
    ngay = T.dong_thoi_gian()["khai_ngay"]
    thang = [(int(x[:4]), int(x[5:7])) for x in ngay]
    assert len(set(thang)) == 3
    assert [(b[0] * 12 + b[1]) - (a[0] * 12 + a[1]) for a, b in zip(thang, thang[1:])] == [1, 1]
    spec = T.ho_spec_f()["mono_volume_score"]
    uv = {f"X{i}": {"khai_ngay": g, "mo_ta": "x", "ly_do": "x", "qua_sang": None, "spec": spec}
          for i, g in enumerate(ngay)}
    cb.kiem_so_ung_vien({"ung_vien": uv})          # sổ giả đúng khuôn, qua trần 1 ứng viên mỗi tháng
    uv["X9"] = {**uv["X0"], "khai_ngay": ngay[0][:8] + "28"}
    with pytest.raises(ValueError):                # đối chứng: hai ứng viên cùng tháng thì trần chặn
        cb.kiem_so_ung_vien({"ung_vien": uv})


# ── G5: ngày giả ───────────────────────────────────────────────────────────

def test_G5_moi_ngay_gia_tu_2100_01_04_va_ngoai_lich_cong_bo(tt):
    assert tt.ngay[0] == "2100-01-04" and min(tt.ngay) >= "2100-01-04"
    ts = pd.to_datetime(list(tt.ngay))
    assert (ts.weekday < 5).all() and ts.is_monotonic_increasing and ts.is_unique
    assert all(lich.co_phien(d) is None for d in tt.ngay), "ngày giả lọt vào lịch công bố"
    assert list(tt.gia.index) == list(tt.ngay)
    assert min(r["signal_date"] for r in tt.dong_quyet_dinh()[:600]) >= "2100-01-04"


def test_G5_AST_moi_hang_chuoi_ngay_trong_module_la_ngay_gia():
    cay = ast.parse(DUONG.read_text(encoding="utf-8"))
    ngay = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and len(n.value) == 10 and n.value[4] == "-" and n.value[7] == "-" and n.value[:4].isdigit()]
    assert ngay, "gác canh quần thể rỗng: module phải khai ngày đầu bằng một hằng chuỗi"
    assert all(g >= "2100-01-04" for g in ngay), ngay


def test_OHLCV_nam_2100_qua_validate_ohlcv_muc_OK(tt):
    """Mục 4.1 khoản 2: OHLC nhất quán ở năm 2100 cho `validate_ohlcv` mức OK."""
    c = tt.gia["GIA01"]
    o = c.shift(1).fillna(c.iloc[0])
    df = pd.DataFrame({"time": list(tt.ngay), "open": o.to_numpy(),
                       "high": np.maximum(o, c).to_numpy() * 1.002,
                       "low": np.minimum(o, c).to_numpy() * 0.998,
                       "close": c.to_numpy(), "volume": 1_000_000.0})
    rep = dq.validate_ohlcv(df, "GIA01", as_of=tt.ngay[-1])
    assert rep.level == dq.Severity.OK, [(i.code, i.message) for i in rep.issues]
    assert rep.last_date == tt.ngay[-1] and rep.rows == len(tt.ngay)


def test_OHLCV_phep_thu_bat_duoc_OHLC_bat_nhat(tt):
    """Phép thử của chính phép thử trên: bẻ một phiên (high < low) thì mức phải lên BLOCK."""
    c = tt.gia["GIA01"]
    df = pd.DataFrame({"time": list(tt.ngay), "open": c.to_numpy(), "high": c.to_numpy() * 1.002,
                       "low": c.to_numpy() * 0.998, "close": c.to_numpy(), "volume": 1e6})
    df.loc[10, "high"] = df.loc[10, "low"] * 0.9
    assert dq.validate_ohlcv(df, "GIA01", as_of=tt.ngay[-1]).level >= dq.Severity.WARN


# ── tái lập bit theo hạt (mục 4.8) ─────────────────────────────────────────

def test_tai_lap_BIT_cung_hat_cung_thi_truong():
    a = T.sinh_thi_truong(LUONG_TEST, 7, KAPPA_CO, so_phien=300, co_su_that=False)
    b = T.sinh_thi_truong(LUONG_TEST, 7, KAPPA_CO, so_phien=300, co_su_that=False)
    assert np.array_equal(a.diem, b.diem)
    assert all(np.array_equal(a.thanh_phan[k], b.thanh_phan[k]) for k in cb.THANH_PHAN)
    assert np.array_equal(a.gia.to_numpy(), b.gia.to_numpy())
    assert a.dong_quyet_dinh() == b.dong_quyet_dinh()


def test_tai_lap_BIT_cua_oracle(tt_oracle):
    lai = T.sinh_thi_truong(LUONG_TEST, 2, KAPPA_CO, co_su_that=True)
    assert tt_oracle.su_that == lai.su_that and tt_oracle.su_that is not None


def test_hat_la_DUNG_default_rng_luong_chi_so_va_oracle_dung_hat_rieng(tt):
    """Mục 4.8: `default_rng([luong, chi_so])`. Dựng lại bằng tay, so từng bit."""
    n = len(tt.ngay)
    mau = T._sinh_loi(np.random.default_rng([LUONG_TEST, 1]), n, KAPPA_CO)
    assert np.array_equal(mau["diem"], tt.diem)
    assert np.array_equal(mau["close"], tt.gia.to_numpy())
    khac = T._sinh_loi(np.random.default_rng(LUONG_TEST), n, KAPPA_CO)
    assert not np.array_equal(khac["diem"], tt.diem)
    sh = T.tinh_su_that(LUONG_TEST, 1, KAPPA_CO, so_phien=1200)
    assert sh["hat"] == [LUONG_TEST, 1, T.HAT_SU_THAT], "oracle phải dùng hạt RIÊNG [luong, chi_so, HAT_SU_THAT]"
    # hạt riêng thật: oracle KHÔNG dùng lại chuỗi số của chính thị trường (cùng tham số, cùng độ dài)
    chinh = T._sinh_loi(np.random.default_rng([LUONG_TEST, 1]), 1200, KAPPA_CO)
    rieng = T._sinh_loi(np.random.default_rng([LUONG_TEST, 1, T.HAT_SU_THAT]), 1200, KAPPA_CO)
    assert not np.array_equal(chinh["diem"], rieng["diem"])


def test_hat_khac_luong_hay_chi_so_cho_thi_truong_khac(tt):
    n = len(tt.ngay)
    a = T.sinh_thi_truong(LUONG_TEST, 2, KAPPA_CO, so_phien=n, co_su_that=False)
    b = T.sinh_thi_truong(LUONG_TEST + 1, 1, KAPPA_CO, so_phien=n, co_su_that=False)
    assert not np.array_equal(a.diem, tt.diem), "chỉ số thị trường không đi vào hạt"
    assert not np.array_equal(b.diem, tt.diem), "dòng hạt không đi vào hạt"
    assert not np.array_equal(a.diem, b.diem)


@pytest.mark.parametrize("xau", [0, -1, True, 1.5, "2"])
def test_hat_xau_bi_tu_choi(xau):
    with pytest.raises(ValueError):
        T.sinh_thi_truong(xau, 1, KAPPA_CO, so_phien=50, co_su_that=False)
    with pytest.raises(ValueError):
        T.sinh_thi_truong(LUONG_TEST, xau, KAPPA_CO, so_phien=50, co_su_that=False)


def test_kappa_chi_di_vao_so_hang_ky_vong_NULL_cung_hat_cung_quyet_dinh_khac_gia():
    """Bất biến đối chứng: κ CHỈ đổi giá. Thị trường NULL cùng hạt có đúng dòng quyết định của thị trường
    có lợi thế — nên NULL là đối chứng thật, không phải một thị trường khác."""
    nul = T.sinh_null(LUONG_TEST, 5, so_phien=400, co_su_that=False)
    co = T.sinh_thi_truong(LUONG_TEST, 5, 0.05, so_phien=400, co_su_that=False)
    assert nul.kappa == 0.0 and co.kappa == 0.05
    assert np.array_equal(nul.diem, co.diem)
    assert all(np.array_equal(nul.thanh_phan[k], co.thanh_phan[k]) for k in cb.THANH_PHAN)
    assert nul.dong_quyet_dinh() == co.dong_quyet_dinh()
    assert not np.array_equal(nul.gia.to_numpy(), co.gia.to_numpy())


def test_kappa_am_bi_tu_choi():
    with pytest.raises(ValueError):
        T.sinh_thi_truong(LUONG_TEST, 1, -0.01, so_phien=50, co_su_that=False)


# ── số nấc, tương quan, int() (mục 4.2) ────────────────────────────────────

def test_so_nac_va_bien_khop_bang_MO_XE_chinh_xac(tt):
    mong = {"momentum_score": (17, 4.2, 95.8), "trend_score": (10, 0.0, 100.0), "sr_score": (7, 6.2, 100.0),
            "risk_score": (8, 10.0, 45.0), "volume_score": (13, 25.0, 100.0)}
    for ten, (so, lo, hi) in mong.items():
        v = np.unique(tt.thanh_phan[ten])
        assert (len(v), float(v.min()), float(v.max())) == (so, lo, hi), ten
    assert tuple(T.TRONG_SO_MAC_DINH) == cb.THANH_PHAN == tuple(T.NAC), "ba nơi khai chung MỘT thứ tự"


def test_tuong_quan_hang_giua_cac_thanh_phan_khop_bang_MO_XE(tt):
    M = pd.DataFrame({k: tt.thanh_phan[k].ravel() for k in cb.THANH_PHAN}).corr(method="spearman").to_numpy()
    mong = np.array([[1, .76, .44, .09, .00], [.76, 1, .49, .34, .02], [.44, .49, 1, .09, .07],
                     [.09, .34, .09, 1, -.08], [.00, .02, .07, -.08, 1]])
    assert np.array_equal(mong, T.TUONG_QUAN_HANG), "bảng trong mã lệch bảng MO-XE-KIEN-TRUC.md"
    lech = np.abs(M - mong).max()
    assert lech <= DUNG_SAI_TUONG_QUAN, f"lệch {lech:.3f} > dung sai {DUNG_SAI_TUONG_QUAN}\n{np.round(M, 2)}"


def test_diem_la_so_nguyen_cat_cut_nen_co_hoa_hang(tt):
    d = tt.diem
    assert d.dtype.kind == "i"
    tho = np.zeros(d.shape)
    for k in cb.THANH_PHAN:
        tho = tho + T.TRONG_SO_MAC_DINH[k] * tt.thanh_phan[k]
    ben = (tho + T.DIEM_SAN > 0) & (tho < T.DIEM_TRAN - T.TRAN_TRANH_LUAN) & (tho > T.DIEM_SAN + T.TRAN_TRANH_LUAN)
    sai = (d - tho)[ben]
    # `int()` CẮT: điểm ≤ tổ hợp + nhiễu ≤ tổ hợp + 0,9 và > tổ hợp − 0,9 − 1. Làm tròn thay cho cắt
    # sẽ vượt cận trên ở khoảng một nửa số ô.
    assert sai.max() <= T.TRAN_TRANH_LUAN + 1e-9 and sai.min() > -T.TRAN_TRANH_LUAN - 1.0
    assert float(np.mean(sai > T.TRAN_TRANH_LUAN - 0.05)) < 0.1
    tru = float(np.mean([len(set(r)) < len(r) for r in d]))
    assert tru > 0.99, f"chỉ {tru:.0%} phiên có hoà hạng — điểm không rời rạc như bản thật"
    assert 5 <= d.min() and d.max() <= 95
    # hoà hạng nhiều thì số giá trị khác nhau ít hơn xa số ô
    assert len(np.unique(d)) < d.size / 100


def test_dong_quyet_dinh_dung_khuon_tab_decisions_va_doc_lai_qua_cham_bong(tt):
    tt_ = tt
    rows = tt_.dong_quyet_dinh()
    n, m = len(tt_.ngay), len(tt_.ma)
    assert len(rows) == n * m
    assert all(set(r) == {"symbol", "signal_date", "score", "components", "at", "seq"} for r in rows[:50])
    assert all(isinstance(r["score"], int) and isinstance(r["seq"], int) and isinstance(r["at"], float)
               for r in rows[:500])
    assert [r["seq"] for r in rows] == list(range(1, n * m + 1))
    assert set(json.loads(rows[0]["components"])) == set(cb.THANH_PHAN)
    bang = cb.doc_quyet_dinh(rows, "")
    assert bang.attrs["bo"] == 0 and len(bang) == n * m
    chuan = bang.pivot(index="ngay", columns="symbol", values="score")
    assert np.array_equal(chuan.to_numpy(), tt_.diem.astype(float)), "đọc lại qua cham_bong khác ma trận điểm"
    for k in cb.THANH_PHAN:
        assert np.array_equal(bang.pivot(index="ngay", columns="symbol", values=k).to_numpy(),
                              tt_.thanh_phan[k]), k
    at = [r["at"] for r in rows]
    assert at == sorted(at), "thứ tự `at` phải theo phiên"


def test_nhan_that_chi_co_o_thanh_phan_mang():
    """Lợi thế đi qua ĐÚNG thành phần mang: với κ lớn, IC của `volume_score` với nhãn phải dương rõ, còn bốn
    thành phần kia (độc lập với z — chỉ tương quan với NHIỄU của volume, không với z) quanh 0."""
    t = T.sinh_thi_truong(LUONG_TEST, 4, 0.04, so_phien=1200, co_su_that=False)
    kh = {m: pd.DataFrame({"close": t.gia[m].to_numpy()}) for m in t.gia.columns}
    nhan = E.nhan_vuot_ro(kh, cb.NHIP).to_numpy()
    co = ~np.isnan(nhan).any(axis=1)
    ic = {k: E.rho_hang(t.thanh_phan[k][co].ravel(), nhan[co].ravel()) for k in cb.THANH_PHAN}
    assert ic["volume_score"] > 0.08, ic
    for k in cb.THANH_PHAN:
        if k != "volume_score":
            assert abs(ic[k]) < ic["volume_score"] / 2, (k, ic)


# ── oracle (mục 4.5) ───────────────────────────────────────────────────────

def test_oracle_G_duong_H_am_Z_gan_0_o_muc_co_loi_the(tt_oracle):
    s = tt_oracle.su_that["spec"]
    g, h, z = s[T.TEN_SPEC_G], s[T.TEN_SPEC_H], s[T.TEN_SPEC_Z]
    assert g["delta_ic"] > 4 * g["se_mc"] and g["delta_ic"] > 0.01, g
    assert h["delta_ic"] < -4 * h["se_mc"] and h["delta_ic"] < 0, h
    assert abs(z["delta_ic"]) < 3 * z["se_mc"] and abs(z["delta_ic"]) < 0.1 * g["delta_ic"], (z, g)
    assert set(s) == set(T.ho_spec_oracle()) and len(T.ho_spec_f()) == 11 and len(s) == 12
    assert tt_oracle.su_that["so_phien"] == 5000 and tt_oracle.su_that["so_phien_co_nhan"] == 5000 - 22


def test_oracle_co_the_nhin_ra_loi_the_phep_thu_DUONG_cho_phep_do_cua_NULL(tt_oracle):
    """Trước khi tin kết quả ÂM của NULL: mẫu có KHẢ NĂNG cho kết quả DƯƠNG không? Có — ở κ > 0 máy đo
    đưa ít nhất G và H ra ngoài hai sai số (nếu không thì "NULL im lặng" chẳng nói gì)."""
    ngoai = T.spec_ngoai_hai_se(tt_oracle.su_that)
    assert T.TEN_SPEC_G in ngoai and T.TEN_SPEC_H in ngoai, ngoai


def test_oracle_NULL_sai_so_MC_duoc_hieu_chuan():
    """NULL: ΔIC_true của mọi spec là 0, nên Δ/sai số MC phải xấp xỉ chuẩn tắc. Đọc từng ô (spec × thị
    trường) chứ không đọc "mọi spec trong 2 sai số ở MỘT thị trường": 12 spec cùng lúc thì có thể
    đạt hay trượt tuỳ thị trường (đo 10/11/2026 trên 30 thị trường dòng thử: 13/30 thị trường có ≥ 1 spec
    ngoài 2 sai số, trong khi 93% số ô nằm trong). Tham số hiệu chuẩn là TỶ LỆ, không phải một lượt rút."""
    z = []
    for i in range(1, 5):
        sh = T.tinh_su_that(LUONG_TEST, 100 + i, 0.0)
        z += [v["delta_ic"] / v["se_mc"] for v in sh["spec"].values()]
    z = np.array(z)
    assert 0.7 < z.std() < 1.5, f"sai số MC ước lượng lệch: sd(Δ/se) = {z.std():.2f}"
    assert float(np.mean(np.abs(z) < 2)) >= 0.85
    assert abs(float(z.mean())) < 0.5, "thiên lệch hệ thống ở NULL"


def test_oracle_spec_ngoai_hai_se_do_dung_hai_chieu():
    gia = {"spec": {"a": {"delta_ic": 0.003, "se_mc": 0.002}, "b": {"delta_ic": -0.005, "se_mc": 0.002},
                    "c": {"delta_ic": 0.0039, "se_mc": 0.002}}}
    assert T.spec_ngoai_hai_se(gia) == ["b"]
    assert T.spec_ngoai_hai_se(gia, he_so=1.0) == ["a", "b", "c"]


def test_ho_spec_f_hop_le_va_dung_hinh_dang():
    f = T.ho_spec_f()
    assert len(f) == 11 and sorted(f) == sorted(set(f))
    for ten, s in f.items():
        cb.kiem_spec(s)
    assert [k for k, s in f.items() if len(s["trong_so"]) == 1] == [f"mono_{c}" for c in cb.THANH_PHAN]
    assert f["mono_volume_score"]["trong_so"] == {"volume_score": 1.0}
    assert "volume_score" not in f["bo_volume_score"]["trong_so"]
    for c in cb.THANH_PHAN:
        w = f[f"bo_{c}"]["trong_so"]
        assert set(w) == set(cb.THANH_PHAN) - {c}
        goc = {k: T.TRONG_SO_MAC_DINH[k] for k in w}
        assert all(abs(w[k] / goc[k] - 1.0 / sum(goc.values())) < 1e-12 for k in w), "phải là bộ mặc định chuẩn hoá"
    assert f["deu"]["trong_so"] == {c: 0.2 for c in cb.THANH_PHAN}
    z = T.spec_z()["trong_so"]
    assert z == {"trend_score": 0.15, "momentum_score": 0.25, "volume_score": 0.20, "sr_score": 0.25,
                 "risk_score": 0.15}
    assert z["volume_score"] == T.TRONG_SO_MAC_DINH["volume_score"], "Z không được đụng thành phần mang"
    assert z != T.TRONG_SO_MAC_DINH, "Z suy biến thành bộ mặc định (đổi chỗ hai trọng số bằng nhau)"


def test_diem_spec_cung_so_voi_cham_bong_tung_o(tt):
    """`diem_spec` (vectơ hoá) phải cho cùng điểm với `cb.diem_ung_vien` ở từng ô, sai ≤ 1e-9.

    KHÔNG đòi trùng bit: `sum()` của Python từ 3.12 cộng số thực có bù Neumaier (máy 3.13) còn 3.11 (CI) thì
    không, nên `cb.diem_ung_vien` tự nó lệch bit giữa hai bản; đòi trùng bit là đòi một thứ đổi theo máy.
    Hệ quả đã biết cho oracle: hoà hạng của spec chỉ có thể lệch ở những cặp ô mà hai tổng bằng nhau về
    TOÁN HỌC nhưng khác ở bit cuối — hiếm, và cùng chiều với cả hai điểm B và C."""
    for spec in T.ho_spec_oracle().values():
        c = T.diem_spec(spec, tt.thanh_phan)
        for t, j in ((0, 0), (17, 33), (len(tt.ngay) - 1, 59), (300, 7)):
            tp = {k: float(tt.thanh_phan[k][t, j]) for k in cb.THANH_PHAN}
            assert abs(c[t, j] - cb.diem_ung_vien(spec, tp)) <= 1e-9, (spec, t, j)


def test_oracle_tinh_lai_bang_tay_G_tu_hat_rieng_cung_nhan_THAT_cua_may_do():
    """Dựng lại ΔIC_true của G và sai số MC của nó TỪNG BƯỚC, ngoài `tinh_su_that`: hạt riêng, nhãn
    `E.nhan_vuot_ro` ở `cb.NHIP`, IC bằng `E.rho_hang`, khối liền nhau, độ lệch chuẩn mẫu (ddof = 1)."""
    n = 1500
    mau = T._sinh_loi(np.random.default_rng([LUONG_TEST, 3, T.HAT_SU_THAT]), n, KAPPA_CO)
    kh = {m: pd.DataFrame({"close": mau["close"][:, i]}) for i, m in enumerate(T._ma_gia())}
    nhan = E.nhan_vuot_ro(kh, cb.NHIP).to_numpy()[:n - 22]
    assert not np.isnan(nhan).any()
    b, c = mau["diem"][:n - 22].astype(float), mau["thanh_phan"]["volume_score"][:n - 22]
    khoi = np.array_split(np.arange(n - 22), 10)
    d_khoi = [E.rho_hang(c[i].ravel(), nhan[i].ravel()) - E.rho_hang(b[i].ravel(), nhan[i].ravel()) for i in khoi]
    mong = {"delta_ic": E.rho_hang(c.ravel(), nhan.ravel()) - E.rho_hang(b.ravel(), nhan.ravel()),
            "se_mc": float(np.std(d_khoi, ddof=1) / np.sqrt(10))}
    thuc = T.tinh_su_that(LUONG_TEST, 3, KAPPA_CO, so_phien=n)["spec"][T.TEN_SPEC_G]
    assert thuc["delta_ic"] == pytest.approx(mong["delta_ic"], abs=1e-12), (thuc, mong)
    assert thuc["se_mc"] == pytest.approx(mong["se_mc"], abs=1e-12), (thuc, mong)


def _khong_nhieu(monkeypatch):
    for ten in ("SIGMA_THI_TRUONG", "SIGMA_NGANH", "SIGMA_RIENG"):
        monkeypatch.setattr(T, ten, 0.0)


def test_ky_vong_cai_san_la_kappa_nhan_trung_binh_z_tu_T_den_T_20(monkeypatch):
    """Tắt mọi nhiễu: lợi nhuận phiên s chỉ còn κ·z(s−2)/21, nên nhãn của phiên T (log lợi nhuận T+2…T+22
    vượt rổ, ×100) phải bằng 100·κ·TB(z[T…T+20]) trừ trung bình mã — kiểm CẢ độ lớn (chia 21) lẫn độ trễ
    hai phiên (mục 4.2), bằng nhãn THẬT của máy đo."""
    _khong_nhieu(monkeypatch)
    n, kappa = 260, 0.02
    mau = T._sinh_loi(np.random.default_rng([LUONG_TEST, 6]), n, kappa)
    kh = {m: pd.DataFrame({"close": mau["close"][:, i]}) for i, m in enumerate(T._ma_gia())}
    nhan = E.nhan_vuot_ro(kh, cb.NHIP).to_numpy()
    z = mau["z"]
    co = ~np.isnan(nhan).any(axis=1)
    assert co.sum() == n - 22 and co[:n - 22].all()
    mong = np.array([100.0 * kappa * z[t:t + 21].mean(axis=0) for t in range(n - 22)])
    mong = mong - mong.mean(axis=1, keepdims=True)
    lech = np.abs(nhan[:n - 22] - mong).max()
    assert lech < 0.02, lech
    assert np.abs(mong).max() > 1.0, "tín hiệu cài sẵn phải đủ lớn để phép so có nghĩa"


def test_phan_rieng_ma_la_GARCH_t_cum_bien_dong_va_duoi_day(monkeypatch):
    """Phần riêng mã là `san_dau._nhieu_garch` (đã đo ở BƯỚC 248), không phải nhiễu chuẩn độc lập: bình
    phương lợi nhuận tự tương quan dương và đuôi dày. Tắt thị trường, ngành và κ để chỉ còn phần riêng."""
    for ten in ("SIGMA_THI_TRUONG", "SIGMA_NGANH"):
        monkeypatch.setattr(T, ten, 0.0)
    mau = T._sinh_loi(np.random.default_rng([LUONG_TEST, 8]), 3000, 0.0)
    r = np.diff(mau["close"], axis=0) / mau["close"][:-1]
    assert r.std() == pytest.approx(T.SIGMA_RIENG, rel=0.1)
    r2 = r ** 2 - (r ** 2).mean()
    acf1 = float((r2[1:] * r2[:-1]).mean() / (r2 * r2).mean())
    kurt = float(((r - r.mean()) ** 4).mean() / r.var() ** 2 - 3.0)
    assert acf1 > 0.08, f"không có cụm biến động: acf1(r²) = {acf1:.3f}"
    assert kurt > 1.0, f"không có đuôi dày: kurtosis dư = {kurt:.2f}"


def test_z_la_AR1_dung_he_so_ngay_va_phuong_sai_1(tt):
    t = T._sinh_loi(np.random.default_rng([LUONG_TEST, 10]), 2000, 0.0)["z"]
    assert float(t.std()) == pytest.approx(1.0, abs=0.05) and abs(float(t.mean())) < 0.05
    acf1 = float((t[1:] * t[:-1]).mean() / (t * t).mean())
    assert acf1 == pytest.approx(T.PHI_Z, abs=0.02)


def test_cac_hang_KHAI_ghim_dung_gia_tri_da_ghi_o_ghi_chu_thi_cong():
    """Giá trị KHAI trước (mục 4.2/6; ghi chú thi công của Lát 1). Đổi một số là sửa đặc tả và đổi dòng hạt
    (mục 4.8), nên test ghim để một lần sửa lặng lẽ không qua được."""
    khai = {"SO_MA": 60, "SO_NGANH": 6, "BIEN_NGAY": 0.07, "SIGMA_THI_TRUONG": 0.010, "SIGMA_NGANH": 0.007,
            "SIGMA_RIENG": 0.015, "PHI_Z": 0.97, "PHI_THANH_PHAN": 0.90, "HE_SO_Z": 0.5,
            "SIGMA_TRANH_LUAN": 0.45, "TRAN_TRANH_LUAN": 0.9, "SO_PHIEN_DA_NHIN": 126,
            "SO_PHIEN_TIEN_VE_TRUOC": 126, "SO_UNG_VIEN_KHAI": 3, "SO_PHIEN_SU_THAT": 5000,
            "SO_KHOI_SU_THAT": 10, "THANH_PHAN_MANG": "volume_score", "GIA_DAU": (10.0, 50.0)}
    for ten, v in khai.items():
        assert getattr(T, ten) == v, ten
    assert T.NU_BUOC_T == 7.5 and T.NU_BUOC_T == T.sd.GARCH_NU, "ν phải là hằng ĐÃ ĐO ở BƯỚC 248, dùng lại"
    assert (T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H) == ("mono_volume_score", "doi_cho_trend_sr", "bo_volume_score")


def test_trong_so_mac_dinh_khop_nhanh_else_cua_master_agent():
    """Bản sao phải khớp thật: bộ trọng số mặc định nằm gõ cứng ở `master_agent.py` (nhánh `else`)."""
    nguon = (GOC / "master_agent.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    kq = None
    for n in ast.walk(cay):
        if isinstance(n, ast.If) and n.orelse and not isinstance(n.orelse[0], ast.If):
            for s in n.orelse:
                if (isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name)
                        and s.targets[0].id == "weights" and isinstance(s.value, ast.Dict)):
                    kq = {k.value: v.value for k, v in zip(s.value.keys, s.value.values)}
    assert kq is not None, "không tìm thấy nhánh else gán weights trong master_agent.py — gác canh quần thể rỗng"
    assert {f"{k}_score": v for k, v in kq.items()} == T.TRONG_SO_MAC_DINH


def test_at_tang_theo_phien_va_khac_nhau_giua_cac_phien(tt):
    rows = tt.dong_quyet_dinh()
    m = len(tt.ma)
    theo_phien = [rows[i * m]["at"] for i in range(len(tt.ngay))]
    assert all(b > a for a, b in zip(theo_phien, theo_phien[1:])), "`at` phải tăng ngặt theo phiên"
    assert all(len({r["at"] for r in rows[i * m:(i + 1) * m]}) == 1 for i in (0, 5, 100))


# ── giá ────────────────────────────────────────────────────────────────────

def test_gia_duong_va_loi_nhuan_ngay_trong_bien_do(tt):
    assert (tt.gia.to_numpy() > 0).all() and tt.gia.shape == (len(tt.ngay), T.SO_MA) >= (1, 40)
    r = tt.gia.pct_change().abs().to_numpy()[1:]
    assert float(np.nanmax(r)) <= T.BIEN_NGAY + 1e-9
    assert float(np.nanmax(r)) == pytest.approx(0.07, abs=1e-9), "kẹp ±7% phải CÓ chạm (đuôi t) — không phải ngưỡng thừa"
    assert T.SO_MA >= cb.MIN_MA
    assert len(tt.ma) == T.SO_MA == len(set(tt.ma)) and all(m.startswith("GIA") for m in tt.ma)


# ── gác AST G1 · G3 (khuôn tests/test_san_dau.py) ───────────────────────────

TEN_GHI = {"push", "write_all", "append_rows", "ghi_ke_hoach", "record_trade", "update_trade",
           "write_text", "write_bytes", "to_csv", "to_json", "dump", "to_parquet", "to_pickle",
           "savetxt", "save", "savez", "executemany", "commit"}
CAM_TEN_THAT = {"SO_UNG_VIEN", "doc_so_ung_vien", "sheets_store", "keo_bang_gia", "doc_so_that"}
CAM_CHUOI = ("ung-vien", "phuong-an-bong", "UV-", "backtest", "cache")
NHAP_DUOC = {"__future__", "datetime", "json", "dataclasses", "statistics", "numpy", "pandas",
             "cham_bong", "experiment_tran_dac_trung", "san_dau"}


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
            if isinstance(n, ast.ImportFrom) and n.module:
                ra.add(n.module.split(".")[-1])
    return ra


def _chuoi(cay) -> list:
    return [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


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


def _nhap_muc_module(cay) -> set:
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            ra.add((n.module or "").split(".")[0])
    return ra


def _cay_module():
    return ast.parse(DUONG.read_text(encoding="utf-8"))


def test_G1_khong_ghi_khong_mo_file_ghi_khong_so_nhat_ky_ngoai_bo_nho():
    cay = _cay_module()
    assert not (_goi(cay) & TEN_GHI), sorted(_goi(cay) & TEN_GHI)
    assert not _mo_ghi(cay), "mở file ở chế độ ghi"
    assert not _so_nhat_ky_sai(cay), _so_nhat_ky_sai(cay)
    assert "open" not in _goi(cay), "bộ sinh không cần mở file nào"


def test_G1_mau_xau_va_tot_cua_chinh_phep_do():
    # Mỗi mẫu xấu phải bị ĐÚNG bộ dò dành cho nó bắt (một `or` chung làm bộ dò này che bộ dò kia).
    ten_ghi = ["gs.push(db, be)", "df.to_csv('x.csv')", "p.write_text('x')", "j.ghi_ke_hoach(d)",
               "json.dump(x, f)", "np.save('x', a)", "con.commit()", "np.savez('x', a=a)"]
    mo_ghi = ["open('f', 'w')", "open('f', mode='a+')", "open('f', 'x')", "open('f', m)", "open('f', 'r+')",
              "open('f', 'a')", "open('f', mode='ab')", "open('f', 'wb')"]
    so_sai = ["PaperTradingJournal('paper_trades.db')", "PaperTradingJournal(DB)", "PaperTradingJournal()"]
    for m in ten_ghi:
        assert _goi(ast.parse(m)) & TEN_GHI, f"TEN_GHI không bắt được: {m}"
    for m in mo_ghi:
        assert _mo_ghi(ast.parse(m)), f"_mo_ghi không bắt được: {m}"
    for m in so_sai:
        assert _so_nhat_ky_sai(ast.parse(m)), f"_so_nhat_ky_sai không bắt được: {m}"
    for m in ("open('f')", "open('f', 'r')"):
        assert "open" in _goi(ast.parse(m)), f"không thấy lời gọi open: {m}"
    tot = ["open('f')", "open('f', 'r')", "PaperTradingJournal(':memory:')", "x = json.dumps(d)",
           "'''push() chỉ nằm trong chú thích'''\n# push(x)\nx = 1"]
    for m in tot:
        c = ast.parse(m)
        assert not ((_goi(c) & TEN_GHI) or _mo_ghi(c) or _so_nhat_ky_sai(c)), f"bắt nhầm: {m}"


def test_G1_chay_that_khong_de_lai_dau_vet_tren_dia(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    t = T.sinh_thi_truong(LUONG_TEST, 9, KAPPA_CO, so_phien=120, co_su_that=True)
    t.dong_quyet_dinh()
    assert list(tmp_path.iterdir()) == []


def test_G3_khong_thay_the_gioi_that_AST():
    cay = _cay_module()
    chuoi = _chuoi(cay)
    sai = [s for s in chuoi if any(c in s for c in CAM_CHUOI)]
    assert not sai, f"chuỗi chạm thế giới thật: {sai}"
    assert not (_ten_dung(cay) & CAM_TEN_THAT), sorted(_ten_dung(cay) & CAM_TEN_THAT)
    assert _nhap_muc_module(cay) <= NHAP_DUOC, sorted(_nhap_muc_module(cay) - NHAP_DUOC)


def test_G3_mau_xau_va_tot_cua_chinh_phep_do():
    chuoi_xau = ["x = 'docs/ung-vien.json'", "p = 'docs/phuong-an-bong.json'", "x = 'UV-001'",
                 "p = 'backtest/cache/FPT.csv'", "p = 'cache_gia'", "'''ung-vien trong docstring'''"]
    ten_xau = ["from cham_bong import SO_UNG_VIEN", "cb.doc_so_ung_vien()", "import sheets_store",
               "from keo_bang_gia import x", "import doc_so_that", "from sheets_store import push"]
    nhap_la = ["import os", "import requests", "from paper_trading import x", "import gspread"]
    for m in chuoi_xau:
        assert any(k in s for s in _chuoi(ast.parse(m)) for k in CAM_CHUOI), f"CAM_CHUOI không bắt được: {m}"
    for m in ten_xau:
        assert _ten_dung(ast.parse(m)) & CAM_TEN_THAT, f"CAM_TEN_THAT không bắt được: {m}"
    for m in nhap_la:
        assert _nhap_muc_module(ast.parse(m)) - NHAP_DUOC, f"NHAP_DUOC không bắt được: {m}"
    for m in ("x = cb.THANH_PHAN", "import numpy as np", "from cham_bong import THANH_PHAN", "import statistics"):
        c = ast.parse(m)
        assert not (_ten_dung(c) & CAM_TEN_THAT) and not (_nhap_muc_module(c) - NHAP_DUOC), f"bắt nhầm: {m}"


def test_G3_nap_module_khong_keo_theo_gioi_that():
    """Đọc theo ĐƯỜNG NHẬP gián tiếp, không chỉ chữ trong file: nạp trong một tiến trình sạch rồi xem
    `sys.modules`. Sổ thật, Google Sheets, bộ kéo bảng giá không được lên."""
    ma = ("import sys, json; sys.path.insert(0, %r); import thi_truong_gia; "
          "cam = ['sheets_store', 'keo_bang_gia', 'doc_so_that', 'gspread', 'google_sheets_sync', "
          "'paper_trading', 'paper_runner', 'run_daily', 'vnstock', 'vnstock_data']; "
          "print(json.dumps([m for m in cam if m in sys.modules]))" % str(GOC))
    r = subprocess.run([sys.executable, "-I", "-c", ma], capture_output=True, text=True, cwd=str(GOC),
                       timeout=120, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    assert json.loads(r.stdout.strip().splitlines()[-1]) == [], r.stdout
