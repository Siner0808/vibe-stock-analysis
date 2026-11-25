"""Vòng học khép kín trên thị trường giả — Tầng 1 (C4 Lát 3, BƯỚC 290; `vong_hoc_gia.py`,
`tools/chay_vong_thi_truong_gia.py`).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 5.1–5.5, 7 (gác G2, G4, G6, G7) và 8 ("Lát 3"). Ba loại phép thử:

* BẤT BIẾN 5.4 — mỗi khoản có ca dựng: QUA → nâng; THUA → không; DANG CHAM → không; ứng viên đang chờ → huỷ
  (K vẫn đếm); hiệu lực từ phiên sau; một đời. Ca thật chạy qua `cham_xac_nhan.cham` THẬT; ca phụ (năm trạng thái,
  spec không làm tròn) chạy trên hàm thuần `nang_cap`.
* GÁC — G2 (đường thật không nhập module thị trường giả), G4 (oracle cách ly khỏi vòng), G6 (không chấm lại: xác
  nhận đi qua `cham_bong.phan_quyet`), G7 (bất biến thời gian: mồi sau ngày khai, mồi sau phiên đọc, hiệu lực từ phiên
  sau). Kèm cửa `kiem_luong` của dụng cụ: chỉ dòng hạt 1 và 9001.
* MÁY ĐO — bộ đề xuất thử trên ca có đáp án biết trước (một chuỗi giá mà nhãn xếp đúng theo `volume_score`).

Dòng hạt thử: 9001 (dòng thử của test, ngoài năm dòng chính 1…5 của mục 4.8). KHÔNG test nào sinh dòng 2, 3, 4, 5.
Không số nào ở đây là tỷ lệ; mỗi ca là MỘT thị trường.
"""
import ast
import copy
import importlib.util
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
sys.path.append(str(GOC / "tools"))

import duyet_repo  # noqa: E402

DUONG_V = GOC / "vong_hoc_gia.py"
DUONG_TOOL = GOC / "tools" / "chay_vong_thi_truong_gia.py"
_spec = importlib.util.spec_from_file_location("chay_vong_thi_truong_gia", DUONG_TOOL)
CV = importlib.util.module_from_spec(_spec)
sys.modules["chay_vong_thi_truong_gia"] = CV
_spec.loader.exec_module(CV)

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402
import experiment_tran_dac_trung as E  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import vong_hoc_gia as V  # noqa: E402

LUONG_TEST = 9001
KAPPA_2X = 0.04458670117751986   # κ của mức 2× MDE₈₀ trong docs/thi-truong-gia-hieu-chuan.json (Lát 2)
HO = T.ho_spec_oracle()
S = T.SO_PHIEN_DA_NHIN


def de_xuat_gia(*ten):
    """Chỗ cắm: bộ đề xuất cho trước (test dựng ca G, Z, H mà không phụ thuộc cái bộ đề xuất cơ sở chọn)."""
    def f(dong, gia):
        return [{"ten": t, "spec": HO[t], "delta": 1.0 - 0.1 * i, "z": 5.0 - 0.5 * i} for i, t in enumerate(ten)]
    return f


_CACHE: dict = {}


def thi_truong(chi_so, kappa):
    k = (chi_so, kappa)
    if k not in _CACHE:
        tt = T.sinh_thi_truong(LUONG_TEST, chi_so, kappa, co_su_that=False)
        _CACHE[k] = (tt, tt.dong_quyet_dinh())
    return _CACHE[k]


def vong(chi_so, kappa, *ten):
    k = ("vong", chi_so, kappa, ten)
    if k not in _CACHE:
        tt, dong = thi_truong(chi_so, kappa)
        _CACHE[k] = V.chay_vong(dong, tt.gia, de_xuat_gia(*ten) if ten else None)
    return _CACHE[k]


@pytest.fixture(scope="module")
def vong_QUA_dau():          # G đứng đầu: đọc đầu tiên QUA → nâng cấp → hai ứng viên còn lại bị huỷ
    return vong(1, KAPPA_2X, T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H)


@pytest.fixture(scope="module")
def vong_chuoi_THUA_DANGCHAM_QUA():   # H (THUA) → Z (DANG CHAM) → G (QUA): chỉ lần đọc thứ ba nâng cấp
    return vong(1, KAPPA_2X, T.TEN_SPEC_H, T.TEN_SPEC_Z, T.TEN_SPEC_G)


@pytest.fixture(scope="module")
def vong_khong_nang():       # H (THUA) → Z (DANG CHAM) → mono_trend (THUA): không ai QUA
    return vong(1, KAPPA_2X, T.TEN_SPEC_H, T.TEN_SPEC_Z, "mono_trend_score")


# ══ bất biến 5.4 trên ca THẬT (cham_xac_nhan.cham) ═══════════════════════════════════════════════

def test_5_4_khoan1_QUA_tao_phien_ban_moi_va_cac_ung_vien_cho_bi_huy(vong_QUA_dau):
    v = vong_QUA_dau
    assert [d["trang_thai"] for d in v["doc"]] == ["QUA"] and v["doc"][0]["nang_cap"] is True
    assert len(v["so_phien_ban"]["phien_ban"]) == 2 and v["ket_cuc"] == V.KET_CUC_NANG_CAP
    assert v["so_phien_ban"]["phien_ban"][1]["ma_ung_vien"] == "DX1"
    assert v["trang_thai"] == {"DX1": "QUA", "DX2": V.DAU_BI_HUY, "DX3": V.DAU_BI_HUY}


def test_5_4_khoan1_THUA_khong_nang_cap_va_DANG_CHAM_khong_nang_cap(vong_khong_nang):
    v = vong_khong_nang
    assert [d["trang_thai"] for d in v["doc"]] == ["THUA", "DANG CHAM", "THUA"]
    assert [d["nang_cap"] for d in v["doc"]] == [False, False, False]
    assert len(v["so_phien_ban"]["phien_ban"]) == 1 and v["so_phien_ban"]["phien_ban"][0]["spec"] is None
    assert v["ket_cuc"] == V.KET_CUC_KHONG_NANG_CAP and v["tien_ve_truoc"] is None
    assert v["huy"] == [] and not [1 for d in v["so_ung_vien"]["ung_vien"].values() if V.DAU_BI_HUY in d]


def test_5_4_THUA_roi_DANG_CHAM_roi_QUA_chi_lan_doc_thu_ba_nang_cap_va_khong_con_ai_de_huy(
        vong_chuoi_THUA_DANGCHAM_QUA):
    v = vong_chuoi_THUA_DANGCHAM_QUA
    assert [(d["ma"], d["trang_thai"], d["nang_cap"]) for d in v["doc"]] == [
        ("DX1", "THUA", False), ("DX2", "DANG CHAM", False), ("DX3", "QUA", True)]
    assert v["huy"] == [] and v["so_phien_ban"]["phien_ban"][1]["ma_ung_vien"] == "DX3"
    # phiên bản 0 vẫn đang chạy tới tận phiên đọc thứ ba
    assert V.phien_ban_hieu_luc(v["so_phien_ban"], v["doc"][2]["phien_doc"])["so"] == 0


def test_5_4_khoan2_phien_ban_moi_co_spec_BANG_DUNG_spec_da_khai_kem_bang_chung(vong_QUA_dau):
    v = vong_QUA_dau
    ban = v["so_phien_ban"]["phien_ban"][1]
    assert ban["spec"] == HO[T.TEN_SPEC_G] == v["so_ung_vien"]["ung_vien"]["DX1"]["spec"]
    d = v["doc"][0]
    bc = ban["bang_chung"]
    assert bc == {"p": d["p"], "delta": d["delta"], "n_phien": cb.MOC_DOC, "n_ma": T.SO_MA, "K": 3,
                  "nguong": pytest.approx(0.05 / 3), "hat": cx.HAT_RNG, "so_hoan_vi": cx.SO_HOAN_VI}
    assert bc["p"] < bc["nguong"] and bc["delta"] > 0


def test_5_4_khoan3_hieu_luc_tu_phien_SAU_phien_doc(vong_QUA_dau):
    v = vong_QUA_dau
    t = v["doc"][0]["phien_doc"]
    ban = v["so_phien_ban"]["phien_ban"][1]
    assert ban["phien_doc"] == t and ban["hieu_luc_tu_phien"] == t + 1
    assert V.phien_ban_hieu_luc(v["so_phien_ban"], t)["so"] == 0          # ở CHÍNH phiên đọc: vẫn bản cũ
    assert V.phien_ban_hieu_luc(v["so_phien_ban"], t + 1)["so"] == 1      # từ phiên sau: bản mới
    assert V.phien_ban_hieu_luc(v["so_phien_ban"], 0)["so"] == 0
    assert v["hieu_luc_ngay"] == str(thi_truong(1, KAPPA_2X)[0].gia.index[t + 1])


def test_5_4_khoan4_diem_ghi_tu_phien_hieu_luc_la_int_cua_diem_ung_vien(vong_QUA_dau):
    v = vong_QUA_dau
    tt, dong = thi_truong(1, KAPPA_2X)
    ngay = [str(n) for n in tt.gia.index]
    truoc = copy.deepcopy(dong)
    ap = V.ap_phien_ban(dong, v["so_phien_ban"], ngay)
    hl = v["so_phien_ban"]["phien_ban"][1]["hieu_luc_tu_phien"]
    chi_so = {n: i for i, n in enumerate(ngay)}
    assert len(ap) == len(dong)
    doi = 0
    for cu, moi in zip(dong, ap):
        t = chi_so[cu["signal_date"]]
        if t < hl:
            assert moi == cu, "dòng TRƯỚC phiên hiệu lực phải giữ nguyên"
            continue
        tp = json.loads(cu["components"])
        assert moi["score"] == int(cb.diem_ung_vien(v["so_phien_ban"]["phien_ban"][1]["spec"], tp))
        assert {k: x for k, x in moi.items() if k != "score"} == {k: x for k, x in cu.items() if k != "score"}
        doi += moi["score"] != cu["score"]
    assert doi > 1000, "phiên bản mới (mono volume) phải đổi điểm ở rất nhiều dòng, không là phép thử rỗng"
    assert dong == truoc, "không được sửa dòng đầu vào"


def test_5_4_khoan4_int_la_cat_cut_khong_lam_tron():
    spec = {"loai": "trong_so", "trong_so": {"volume_score": 0.5, "trend_score": 0.5}}
    tp = {"trend_score": 51.0, "momentum_score": 0.0, "volume_score": 60.8, "sr_score": 0.0, "risk_score": 0.0}
    dong = [{"symbol": "A", "signal_date": "2100-01-04", "score": 9, "components": json.dumps(tp), "at": 1.0, "seq": 1},
            {"symbol": "A", "signal_date": "2100-01-05", "score": 9, "components": json.dumps(tp), "at": 2.0, "seq": 2}]
    pb = {"phien_ban": [{"so": 0, "spec": None, "hieu_luc_tu_phien": 0},
                        {"so": 1, "spec": spec, "hieu_luc_tu_phien": 1}]}
    ap = V.ap_phien_ban(dong, pb, ["2100-01-04", "2100-01-05"])
    assert ap[0]["score"] == 9 and ap[1]["score"] == 55          # 55,9 → 55 (cắt cụt, như paper_trading :731)


def test_5_4_khoan5_ung_vien_cho_bi_huy_nhung_K_va_nguong_VAN_DEM(vong_QUA_dau):
    v = vong_QUA_dau
    so = v["so_ung_vien"]
    assert v["huy"] == ["DX2", "DX3"] and so["ung_vien"]["DX2"][V.DAU_BI_HUY] is True
    assert V.DAU_BI_HUY not in so["ung_vien"]["DX1"]
    assert cb.so_da_sang(so) == 3 == v["K"]
    assert cb.nguong(so) == pytest.approx(0.05 / 3)
    cb.kiem_so_ung_vien(so)      # vẫn đúng khuôn sổ
    assert so["ung_vien"]["DX2"]["spec"] == HO[T.TEN_SPEC_Z] and so["ung_vien"]["DX2"]["qua_sang"] is None


def test_5_4_khoan5_huy_chi_cham_ung_vien_chua_doc_va_khong_sua_dau_vao():
    so = {"ung_vien": {}}
    ngay = ["2100-07-01", "2100-08-02", "2100-09-01"]
    for i, ten in enumerate((T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H)):
        so = V.khai_ung_vien(so, f"DX{i + 1}", ngay[i], HO[ten], "m", "l")
    truoc = copy.deepcopy(so)
    moi = V.huy_ung_vien_cho_doc(so, ["DX1", "DX2"])
    assert so == truoc, "không được sửa sổ đầu vào"
    assert [m for m, d in moi["ung_vien"].items() if d.get(V.DAU_BI_HUY)] == ["DX3"]
    assert cb.so_da_sang(moi) == 3 and cb.nguong(moi) == pytest.approx(0.05 / 3)
    assert [m for m, d in V.huy_ung_vien_cho_doc(so, [])["ung_vien"].items() if d.get(V.DAU_BI_HUY)] == [
        "DX1", "DX2", "DX3"]


def test_5_4_khoan6_mot_doi_khong_co_nang_cap_thu_hai_o_ca_vong_va_o_ham_thuan(vong_QUA_dau):
    # ở vòng: sau lần nâng cấp đầu không còn lượt đọc nào (cả hai ứng viên sau bị huỷ, không đọc)
    assert len(vong_QUA_dau["doc"]) == 1
    # ở hàm thuần: hai lần QUA liên tiếp chỉ cho MỘT phiên bản mới
    ket = _ket_gia("QUA")
    so_uv = _so_uv_gia()
    pb1 = V.nang_cap(V.so_phien_ban_dau(), ket, "DX1", 400, so_uv)
    pb2 = V.nang_cap(pb1, ket, "DX1", 500, so_uv)
    assert len(pb1["phien_ban"]) == 2 and pb2 == pb1 and pb2["phien_ban"][1]["hieu_luc_tu_phien"] == 401


# ══ nang_cap — hàm thuần, năm trạng thái ═══════════════════════════════════════════════════════

def _ket_gia(trang_thai, ma="DX1", delta=0.12, p=0.001):
    ct = {"trang_thai": trang_thai, "n_phien": cb.MOC_DOC, "n_ma": 60, "nguong": 0.05 / 3, "hat": cx.HAT_RNG,
          "so_hoan_vi": cx.SO_HOAN_VI}
    if trang_thai in ("QUA", "THUA", "DANG CHAM"):
        ct.update(delta=delta, p=p, z=3.0)
    return {"chi_tiet": {ma: ct}, "K": 3, "nguong": 0.05 / 3, "hat": cx.HAT_RNG, "so_hoan_vi": cx.SO_HOAN_VI}


def _so_uv_gia(spec=None):
    so = {"ung_vien": {"DX1": {"khai_ngay": "2100-07-01", "mo_ta": "m", "ly_do": "l", "qua_sang": None,
                               "spec": spec or HO[T.TEN_SPEC_G]}}}
    return so


@pytest.mark.parametrize("trang_thai", ["THUA", "DANG CHAM", cb.CHUA_TOI_MOC, "CHUA DU DU LIEU"])
def test_nang_cap_khong_tao_phien_ban_khi_khong_phai_QUA(trang_thai):
    pb = V.so_phien_ban_dau()
    truoc = copy.deepcopy(pb)
    moi = V.nang_cap(pb, _ket_gia(trang_thai), "DX1", 400, _so_uv_gia())
    assert moi == truoc and pb == truoc and len(moi["phien_ban"]) == 1


def test_nang_cap_QUA_tao_dung_mot_phien_ban_khong_sua_dau_vao():
    pb = V.so_phien_ban_dau()
    truoc = copy.deepcopy(pb)
    moi = V.nang_cap(pb, _ket_gia("QUA"), "DX1", 400, _so_uv_gia())
    assert pb == truoc, "không được sửa sổ phiên bản đầu vào"
    assert [b["so"] for b in moi["phien_ban"]] == [0, 1] and moi["phien_ban"][0] == truoc["phien_ban"][0]
    b = moi["phien_ban"][1]
    assert b["spec"] == HO[T.TEN_SPEC_G] and b["hieu_luc_tu_phien"] == 401 and b["phien_doc"] == 400
    assert b["bang_chung"] == {"p": 0.001, "delta": 0.12, "n_phien": cb.MOC_DOC, "n_ma": 60, "K": 3,
                               "nguong": pytest.approx(0.05 / 3), "hat": cx.HAT_RNG, "so_hoan_vi": cx.SO_HOAN_VI}


@pytest.mark.parametrize("phien_doc", [0, 1, 400, 593])
def test_nang_cap_hieu_luc_dung_phien_doc_cong_mot(phien_doc):
    moi = V.nang_cap(V.so_phien_ban_dau(), _ket_gia("QUA"), "DX1", phien_doc, _so_uv_gia())
    assert moi["phien_ban"][1]["hieu_luc_tu_phien"] == phien_doc + 1
    assert V.phien_ban_hieu_luc(moi, phien_doc)["so"] == 0 and V.phien_ban_hieu_luc(moi, phien_doc + 1)["so"] == 1


def test_nang_cap_spec_BANG_khong_lam_tron_va_la_ban_sao_khong_la_cung_doi_tuong():
    spec = {"loai": "trong_so", "trong_so": {"trend_score": 1 / 3, "momentum_score": 1 / 3, "volume_score": 1 / 3}}
    so_uv = _so_uv_gia(spec)
    moi = V.nang_cap(V.so_phien_ban_dau(), _ket_gia("QUA"), "DX1", 10, so_uv)
    b = moi["phien_ban"][1]["spec"]
    assert b == spec and b["trong_so"]["trend_score"] == 1 / 3     # đúng từng bit
    assert b is not spec and b["trong_so"] is not spec["trong_so"]
    b["trong_so"]["trend_score"] = 0.0
    assert so_uv["ung_vien"]["DX1"]["spec"]["trong_so"]["trend_score"] == 1 / 3


@pytest.mark.parametrize("xau", [-1, 1.0, "3", None, True])
def test_nang_cap_phien_doc_xau_bi_tu_choi(xau):
    with pytest.raises(ValueError, match="phien_doc"):
        V.nang_cap(V.so_phien_ban_dau(), _ket_gia("QUA"), "DX1", xau, _so_uv_gia())


def test_nang_cap_doc_dung_ung_vien_duoc_hoi_khong_doc_ung_vien_khac():
    ket = _ket_gia("QUA", "DX1")
    ket["chi_tiet"]["DX2"] = {**ket["chi_tiet"]["DX1"], "trang_thai": "THUA"}
    so_uv = _so_uv_gia()
    so_uv["ung_vien"]["DX2"] = {**so_uv["ung_vien"]["DX1"], "spec": HO[T.TEN_SPEC_H]}
    assert len(V.nang_cap(V.so_phien_ban_dau(), ket, "DX1", 5, so_uv)["phien_ban"]) == 2
    assert len(V.nang_cap(V.so_phien_ban_dau(), ket, "DX2", 5, so_uv)["phien_ban"]) == 1
    with pytest.raises(KeyError):
        V.nang_cap(V.so_phien_ban_dau(), ket, "DX9", 5, so_uv)


# ══ kiểm tiến-về-trước ════════════════════════════════════════════════════════════════════════════

def test_tien_ve_truoc_cua_so_F_phien_dau_tu_phien_hieu_luc_dung_phien_co_nhan(vong_QUA_dau):
    tv = vong_QUA_dau["tien_ve_truoc"]
    hl = vong_QUA_dau["so_phien_ban"]["phien_ban"][1]["hieu_luc_tu_phien"]
    tt = thi_truong(1, KAPPA_2X)[0]
    assert tv["tu_phien"] == hl and tv["tu_ngay"] == str(tt.gia.index[hl])
    assert tv["n_phien"] == T.SO_PHIEN_TIEN_VE_TRUOC and tv["du_cua_so"] is True and tv["n_ma"] == T.SO_MA
    assert tv["den_ngay_cua_so"] == str(tt.gia.index[hl + T.SO_PHIEN_TIEN_VE_TRUOC - 1])
    assert tv["delta_ic"] == pytest.approx(tv["ic_phien_ban_moi"] - tv["ic_da_ghi"])
    assert tv["delta_ic"] > 0, "ở lợi thế 2× phiên bản mới (mono volume) phải hơn điểm đã ghi trên cửa sổ tiến-về-trước"
    # cửa sổ F + 22 phiên giá phía sau nằm gọn trong thị trường; với ứng viên khai SAU CÙNG (đọc ở phiên 445)
    # thì vừa khít phiên cuối (mục 15 khoản 3: tổng 594)
    assert hl + T.SO_PHIEN_TIEN_VE_TRUOC - 1 + T.DO_TRE_NHAN < len(tt.gia)
    cuoi = T.dong_thoi_gian()["doc"][-1] + 1
    assert cuoi + T.SO_PHIEN_TIEN_VE_TRUOC - 1 + T.DO_TRE_NHAN == len(tt.gia) - 1


def test_tien_ve_truoc_chi_dung_du_lieu_tu_phien_hieu_luc_tro_di(vong_QUA_dau):
    tt, dong = thi_truong(1, KAPPA_2X)
    v = vong_QUA_dau
    hl = v["so_phien_ban"]["phien_ban"][1]["hieu_luc_tu_phien"]
    ngay = [str(n) for n in tt.gia.index]
    vi_tri = {n: i for i, n in enumerate(ngay)}
    goc = v["tien_ve_truoc"]
    rng = np.random.default_rng(777)

    def mo(gia, dong_, tu, den):
        g = gia.copy()
        g.iloc[tu:den] = g.iloc[tu:den].to_numpy() * rng.uniform(0.5, 2.0, size=g.iloc[tu:den].shape)
        d = []
        for r in dong_:
            r = dict(r)
            if tu <= vi_tri[r["signal_date"]] < den:
                tp = {k: float(x) for k, x in zip(cb.THANH_PHAN, rng.uniform(0, 100, size=5))}
                r["components"], r["score"] = json.dumps(tp), int(rng.integers(5, 95))
            d.append(r)
        return g, d
    # mồi ở phiên đọc và MỌI phiên trước đó: kết quả không được đổi
    g1, d1 = mo(tt.gia, dong, 0, hl)
    assert V.kiem_tien_ve_truoc(d1, g1, v["so_phien_ban"]) == goc
    # đối chứng: mồi ở CHÍNH phiên hiệu lực (trong cửa sổ) thì kết quả PHẢI đổi — phép thử không rỗng
    g2, d2 = mo(tt.gia, dong, hl, hl + 40)
    assert V.kiem_tien_ve_truoc(d2, g2, v["so_phien_ban"])["delta_ic"] != goc["delta_ic"]
    # mồi sau cửa sổ + nhãn (phiên > hl + F − 1 + 22): không còn phiên nào, nên không có gì để đổi
    g3, d3 = mo(tt.gia, dong, len(ngay) - 1, len(ngay))
    assert V.kiem_tien_ve_truoc(d3, g3, v["so_phien_ban"]) == goc


def test_tien_ve_truoc_bang_gia_dua_vao_may_do_nhan_bat_dau_dung_o_phien_hieu_luc(vong_QUA_dau, monkeypatch):
    """Ghim bằng máy ghi: nhãn của cửa sổ tiến-về-trước tính trên bảng giá KHÔNG chứa phiên đọc hay phiên trước nó."""
    tt, dong = thi_truong(1, KAPPA_2X)
    hl = vong_QUA_dau["so_phien_ban"]["phien_ban"][1]["hieu_luc_tu_phien"]
    thay = []
    that = E.nhan_vuot_ro

    def ghi(kh, h):
        thay.append((min(d.index[0] for d in kh.values()), len(next(iter(kh.values())))))
        return that(kh, h)
    monkeypatch.setattr(E, "nhan_vuot_ro", ghi)
    V.kiem_tien_ve_truoc(dong, tt.gia, vong_QUA_dau["so_phien_ban"])
    assert thay == [(str(tt.gia.index[hl]), len(tt.gia) - hl)]


def test_tien_ve_truoc_khong_nang_cap_thi_None_va_cua_so_thieu_thi_khai_thang(vong_QUA_dau, vong_khong_nang):
    tt, dong = thi_truong(1, KAPPA_2X)
    assert V.kiem_tien_ve_truoc(dong, tt.gia, vong_khong_nang["so_phien_ban"]) is None
    rong = V.kiem_tien_ve_truoc(dong, tt.gia, vong_QUA_dau["so_phien_ban"], so_phien=300)
    assert rong["du_cua_so"] is False and rong["so_phien"] == 300
    assert 0 < rong["n_phien"] < 300 and rong["n_phien"] == len(tt.gia) - 1 - T.DO_TRE_NHAN - rong["tu_phien"] + 1


def test_tien_ve_truoc_nang_cap_o_cuoi_du_lieu_khong_co_phien_nao_thi_khong_co_so():
    tt, dong = thi_truong(1, KAPPA_2X)
    pb = V.nang_cap(V.so_phien_ban_dau(), _ket_gia("QUA"), "DX1", len(tt.gia) - 1, _so_uv_gia())
    kq = V.kiem_tien_ve_truoc(dong, tt.gia, pb)
    assert kq["n_phien"] == 0 and kq["delta_ic"] is None and kq["du_cua_so"] is False
    pb = V.nang_cap(V.so_phien_ban_dau(), _ket_gia("QUA"), "DX1", len(tt.gia) - 5, _so_uv_gia())
    kq = V.kiem_tien_ve_truoc(dong, tt.gia, pb)       # có phiên nhưng chưa phiên nào có nhãn T+22
    assert kq["n_phien"] == 0 and kq["delta_ic"] is None


# ══ bộ đề xuất cơ sở ═════════════════════════════════════════════════════════════════════════════

def _thi_truong_nhan_biet_truoc(so_phien=60, so_ma=60):
    """Chuỗi giá mà nhãn xếp ĐÚNG theo `volume_score`: mã j có lợi nhuận ngày cố định r_j tăng theo j, nên nhãn
    (log lợi nhuận 21 phiên vượt rổ) xếp theo j ở MỌI phiên. volume_score = j (hoàn hảo); các thành phần khác và
    điểm đã ghi là nhiễu độc lập. Đáp án biết trước: spec mono_volume_score hơn hẳn và đứng đầu."""
    rng = np.random.default_rng(31)
    ngay = list(T.lich_phien(so_phien))
    ma = [f"GIA{j + 1:02d}" for j in range(so_ma)]
    r = np.linspace(-0.004, 0.004, so_ma)
    gia = pd.DataFrame(10.0 * np.cumprod(1.0 + np.tile(r, (so_phien, 1)), axis=0), index=ngay, columns=ma)
    dong, seq = [], 0
    for t, n in enumerate(ngay):
        for j, m in enumerate(ma):
            seq += 1
            tp = {k: float(rng.uniform(0, 100)) for k in cb.THANH_PHAN}
            tp["volume_score"] = float(j)
            dong.append({"symbol": m, "signal_date": n, "score": int(rng.integers(5, 95)),
                         "components": json.dumps(tp), "at": float(seq), "seq": seq})
    return dong, gia


def test_de_xuat_tim_dung_spec_tot_nhat_tren_ca_co_dap_an_biet_truoc():
    dong, gia = _thi_truong_nhan_biet_truoc()
    xep = V.de_xuat(dong, gia)
    assert sorted(x["ten"] for x in xep) == sorted(T.ho_spec_f()) and len(xep) == 11
    assert xep[0]["ten"] == "mono_volume_score" and xep[0]["delta"] > 0.8
    assert xep[0]["ic_spec"] == pytest.approx(1.0, abs=1e-2) and abs(xep[0]["ic_da_ghi"]) < 0.2
    assert [x["z"] for x in xep] == sorted((x["z"] for x in xep), reverse=True)     # BƯỚC 300: xếp theo z, không theo Δ
    assert all(x["n_phien"] == 60 - T.DO_TRE_NHAN and x["n_ma"] == 60 for x in xep)
    # spec chỉ gồm thành phần nhiễu thì không thể hơn một spec chứa volume
    assert all(x["delta"] < xep[0]["delta"] for x in xep[1:])
    for x in xep:
        assert x["delta"] == pytest.approx(x["ic_spec"] - x["ic_da_ghi"])
        assert x["spec"] == T.ho_spec_f()[x["ten"]]


def test_de_xuat_la_ham_thuan_cung_dau_vao_cung_ket_qua_va_khong_sua_dau_vao():
    dong, gia = _thi_truong_nhan_biet_truoc()
    truoc, g0 = copy.deepcopy(dong), gia.copy()
    a, b = V.de_xuat(dong, gia), V.de_xuat(dong, gia)
    assert a == b and dong == truoc and gia.equals(g0)


def test_de_xuat_cua_so_khong_co_phien_co_nhan_thi_no():
    dong, gia = _thi_truong_nhan_biet_truoc(so_phien=20)    # < NHIP + 1 phiên: chưa phiên nào có nhãn
    with pytest.raises(ValueError, match="khong co phien co nhan"):
        V.de_xuat(dong, gia)


def test_xep_hoa_theo_thu_tu_ten_spec_va_chon_khai_chi_lay_z_duong_va_delta_duong_toi_da_3():
    x = [{"ten": "b", "delta": 0.1, "z": 1.0}, {"ten": "a", "delta": 0.1, "z": 1.0},
         {"ten": "c", "delta": 0.3, "z": 3.0}, {"ten": "z", "delta": 0.0, "z": 0.0},
         {"ten": "y", "delta": -0.2, "z": -2.0}, {"ten": "d", "delta": 0.05, "z": 0.5}]
    assert [t["ten"] for t in sorted(x, key=V._khoa_xep)] == ["c", "a", "b", "d", "z", "y"]
    assert [t["ten"] for t in V.chon_khai(x)] == ["c", "a", "b"]                   # tối đa 3, hoà theo tên
    assert [t["ten"] for t in V.chon_khai(x, so=10)] == ["c", "a", "b", "d"]       # z = 0 và z < 0 không khai
    assert V.chon_khai([{"ten": "q", "delta": 0.0, "z": 0.0}, {"ten": "r", "delta": -1.0, "z": -1.0}]) == []
    assert [t["ten"] for t in V.chon_khai(list(reversed(x)))] == ["c", "a", "b"]   # không phụ thuộc thứ tự vào


def test_so_khai_toi_da_la_hang_SO_UNG_VIEN_KHAI():
    assert T.SO_UNG_VIEN_KHAI == 3
    x = [{"ten": f"s{i}", "delta": 1.0 - i / 100, "z": 5.0 - i / 10} for i in range(8)]
    assert len(V.chon_khai(x)) == T.SO_UNG_VIEN_KHAI


# ══ bộ đề xuất CHUẨN HOÁ (BƯỚC 300; `docs/thiet-ke-c4-thi-truong-gia.md` mục 21.1) ═══════════════════════════════

def _hang_giua_doc_lap(A):
    """Hạng giữa tính bằng `scipy.stats.rankdata`: KHÔNG đi qua `cham_bong._hang_giua` (test không kiểm mã bằng chính mã)."""
    from scipy.stats import rankdata
    r = rankdata(A.ravel())
    return (r - r.mean()).reshape(A.shape)


def _ma_tran_A_doc_lap(B, C, Y):
    RB, RC, RY = _hang_giua_doc_lap(B), _hang_giua_doc_lap(C), _hang_giua_doc_lap(Y)
    ny = float((RY * RY).sum())
    mb, mc = np.sqrt((RB * RB).sum() * ny), np.sqrt((RC * RC).sum() * ny)
    return (RC.T @ RY) / mc - (RB.T @ RY) / mb


def test_thong_ke_null_khop_LIET_KE_TAT_CA_hoan_vi_o_M_6_ca_mu_lan_sd():
    """M = 6 mã → 720 hoán vị: liệt kê hết, độ lệch chuẩn QUẦN THỂ (chia 720). Dạng đóng chia (M − 1) phải khớp
    đúng; chia M, bỏ μ, hay không căn giữa theo hàng/cột đều lệch xa hơn dung sai."""
    from itertools import permutations
    rng = np.random.default_rng(2026)
    for so_phien in (8, 11):
        B = rng.integers(0, 5, (so_phien, 6)).astype(float)       # có hoà: hạng trung bình
        C = rng.integers(0, 9, (so_phien, 6)).astype(float) + 0.5 * B
        Y = rng.normal(size=(so_phien, 6)) + 0.4 * C
        A = _ma_tran_A_doc_lap(B, C, Y)
        null = np.array([sum(A[j, p[j]] for j in range(6)) for p in permutations(range(6))])
        mu, sd = V.thong_ke_null(B, C, Y)
        assert len(null) == 720
        assert mu == pytest.approx(float(null.mean()), rel=1e-9, abs=1e-12)
        assert sd == pytest.approx(float(null.std()), rel=1e-9)
        assert abs(mu) > 1e-3 * sd, "ca dựng phải có μ ≠ 0 để phép thử bắt được 'bỏ trừ μ'"


def test_thong_ke_null_khop_so_cap_20000_hoan_vi_trong_2_phan_tram_o_mot_thi_truong():
    tt, dong = thi_truong(1, KAPPA_2X)
    dong_n, gia_n = V.cat_den_phien(dong, tt.gia, S - 1)
    bang = cb.doc_quyet_dinh(dong_n, "")
    nhan = E.nhan_vuot_ro({m: pd.DataFrame({"close": gia_n[m]}) for m in gia_n.columns}, cb.NHIP)
    for ten in (T.TEN_SPEC_G, "deu", "mono_momentum_score"):
        B, C, Y, _, _ = cb.ma_tran_cap(bang, T.ho_spec_f()[ten], nhan)
        mu, sd = V.thong_ke_null(B, C, Y)
        ket = cb.so_cap(B, C, Y, np.random.default_rng(11), so=20000)
        assert sd == pytest.approx(float(ket["null"].std()), rel=0.02), ten
        assert abs(mu - float(ket["null"].mean())) < 0.05 * sd, ten
        z = (ket["delta"] - mu) / sd
        assert z == pytest.approx(ket["z"], abs=0.03 * max(1.0, abs(z))), ten


def test_thong_ke_null_phuong_sai_0_tra_0_0_o_ba_ca():
    rng = np.random.default_rng(5)
    B = rng.normal(size=(9, 6))
    C = rng.normal(size=(9, 6))
    Y = rng.normal(size=(9, 6))
    assert V.thong_ke_null(B, np.full((9, 6), 3.0), Y) == (0.0, 0.0)           # C hằng: m_c = 0
    assert V.thong_ke_null(np.full((9, 6), 3.0), C, Y) == (0.0, 0.0)           # B hằng: m_b = 0
    assert V.thong_ke_null(B, C, np.full((9, 6), 1.0)) == (0.0, 0.0)           # Y hằng
    assert V.thong_ke_null(B[:, :1], C[:, :1], Y[:, :1]) == (0.0, 0.0)         # một mã: không có hoán vị
    # nhãn chỉ phụ thuộc phiên (mọi mã cùng nhãn): mọi hoán vị cho CÙNG tổng → σ = 0, dù m_b·m_c ≠ 0
    Yp = np.tile(rng.normal(size=(9, 1)), (1, 6))
    mu, sd = V.thong_ke_null(B, C, Yp)
    assert sd == 0.0 and np.isfinite(mu)


def _thi_truong_z_khac_delta(seed=38, so_phien=90, so_ma=30, risk_hang=False):
    """Mã j có xu hướng thật `troi[j]`. `volume_score` đo xu hướng ấy kèm nhiễu MỚI mỗi phiên (σ_null nhỏ); `trend_score`
    là hằng số riêng của mã (không liên quan xu hướng thật, σ_null lớn vì chỉ có `so_ma` giá trị khác nhau): IC của nó là
    may rủi. Hạt 38: Δ(trend) > Δ(volume) nhưng z(trend) << z(volume). `risk_hang`: `risk_score` = 50 ở MỌI dòng (spec
    mono_risk phương sai 0) và điểm đã ghi NGƯỢC nhãn, nên Δ(mono_risk) = −IC(B) > 0."""
    rng = np.random.default_rng(seed)
    ngay = list(T.lich_phien(so_phien))
    ma = [f"GIA{j + 1:02d}" for j in range(so_ma)]
    troi = rng.normal(0, 0.003, so_ma)
    loi = troi + rng.normal(0, 0.01, (so_phien, so_ma))
    gia = pd.DataFrame(10.0 * np.cumprod(1.0 + loi, axis=0), index=ngay, columns=ma)
    ben = rng.uniform(20, 80, so_ma)
    dong, seq = [], 0
    for n in ngay:
        for j, m in enumerate(ma):
            seq += 1
            tp = {k: float(rng.uniform(0, 100)) for k in cb.THANH_PHAN}
            if risk_hang:
                tp["risk_score"] = 50.0
                tp["volume_score"] = float(50 + 1500.0 * troi[j] + rng.normal(0, 12))
                diem = int(np.clip(50 - 1500.0 * troi[j] + rng.normal(0, 12), 5, 95))
            else:
                tp["trend_score"] = float(ben[j] + rng.normal(0, 3))
                tp["volume_score"] = float(50 + 1500.0 * troi[j] + rng.normal(0, 12))
                diem = int(rng.integers(5, 95))
            dong.append({"symbol": m, "signal_date": n, "score": diem,
                         "components": json.dumps(tp), "at": float(seq), "seq": seq})
    return dong, gia


def test_de_xuat_tra_them_z_va_sd_null_va_z_la_delta_tru_mu_chia_sd_cua_thong_ke_null():
    dong, gia = _thi_truong_z_khac_delta()
    xep = V.de_xuat(dong, gia)
    assert {"ten", "spec", "delta", "z", "sd_null", "ic_spec", "ic_da_ghi", "n_phien", "n_ma"} <= set(xep[0])
    bang = cb.doc_quyet_dinh(dong, "")
    nhan = E.nhan_vuot_ro({m: pd.DataFrame({"close": gia[m]}) for m in gia.columns}, cb.NHIP)
    lech_mu = []
    for x in xep:
        B, C, Y, _, _ = cb.ma_tran_cap(bang, x["spec"], nhan)
        mu, sd = V.thong_ke_null(B, C, Y)
        assert x["sd_null"] == sd and sd > 0
        assert x["z"] == pytest.approx((x["delta"] - mu) / sd, rel=1e-12, abs=1e-12)
        lech_mu.append(abs(mu) / sd)
    assert min(lech_mu) > 1e-4, "μ phải khác 0 ở MỌI spec, nếu không phép thử không bắt được 'bỏ trừ μ'"
    assert [x["z"] for x in xep] == sorted((x["z"] for x in xep), reverse=True)


def test_ca_dung_delta_lon_nhat_nhung_z_nho_hon_bo_cu_chon_sai_bo_moi_chon_dung():
    dong, gia = _thi_truong_z_khac_delta()
    xep = V.de_xuat(dong, gia)
    d = {x["ten"]: x for x in xep}
    cu = max(xep, key=lambda x: x["delta"])                       # bộ đề xuất cũ: Δ thô lớn nhất
    assert cu["ten"] == "mono_trend_score" and cu["delta"] > d["mono_volume_score"]["delta"] + 0.05
    assert d["mono_trend_score"]["z"] < d["mono_volume_score"]["z"] - 1.0           # nhưng z nhỏ hơn hẳn
    assert d["mono_trend_score"]["sd_null"] > 2 * d["mono_volume_score"]["sd_null"]
    assert xep[0]["ten"] == "mono_volume_score"                    # bộ mới: z lớn nhất = spec có tín hiệu THẬT
    assert V.chon_khai(xep)[0]["ten"] == "mono_volume_score"
    assert [x["ten"] for x in V.chon_khai(xep)] != [x["ten"] for x in sorted(xep, key=lambda y: -y["delta"])[:3]]


def test_spec_phuong_sai_0_khong_duoc_khai_du_delta_duong():
    dong, gia = _thi_truong_z_khac_delta(risk_hang=True)
    xep = V.de_xuat(dong, gia)
    r = next(x for x in xep if x["ten"] == "mono_risk_score")
    assert r["delta"] > 0.1 and r["ic_da_ghi"] < -0.1 and r["ic_spec"] == 0.0     # Δ = −IC(B) > 0 vì C hằng
    assert r["z"] == 0.0 and r["sd_null"] == 0.0
    khai = [x["ten"] for x in V.chon_khai(xep, so=11)]
    assert "mono_risk_score" not in khai and len(khai) == 10, khai
    assert all(x["z"] > 0 for x in xep if x["ten"] != "mono_risk_score")


def test_chon_khai_doi_hoi_ca_z_duong_va_delta_duong():
    x = [{"ten": "a", "delta": 0.2, "z": -0.3}, {"ten": "b", "delta": -0.05, "z": 2.0},
         {"ten": "c", "delta": 0.0, "z": 3.0}, {"ten": "d", "delta": 0.1, "z": 0.0},
         {"ten": "e", "delta": 0.01, "z": 0.01}]
    assert [t["ten"] for t in V.chon_khai(x, so=10)] == ["e"]


def test_xep_hoa_lam_tron_z_12_chu_so_khong_hon_khong_kem():
    """z hơn kém dưới 5e-13 là sai số dấu chấm động → HOÀ → theo tên; hơn kém 2e-12 thì z quyết định."""
    hoa = [{"ten": "b", "delta": 0.1, "z": 0.5 + 2e-13}, {"ten": "a", "delta": 0.1, "z": 0.5}]
    assert [t["ten"] for t in sorted(hoa, key=V._khoa_xep)] == ["a", "b"]
    khac = [{"ten": "a", "delta": 0.1, "z": 0.25}, {"ten": "b", "delta": 0.1, "z": 0.25 + 2e-12}]
    assert [t["ten"] for t in sorted(khac, key=V._khoa_xep)] == ["b", "a"]
    ro = [{"ten": "a", "delta": 0.1, "z": 0.25}, {"ten": "b", "delta": 0.1, "z": 0.75}]
    assert [t["ten"] for t in sorted(ro, key=V._khoa_xep)] == ["b", "a"]


def test_xep_hang_khong_dung_delta_tho_ca_khi_delta_trai_chieu_voi_z():
    x = [{"ten": "a", "delta": 0.9, "z": 1.0}, {"ten": "b", "delta": 0.1, "z": 5.0}]
    assert [t["ten"] for t in V.chon_khai(x)] == ["b", "a"]


def test_G7_z_va_sd_null_cung_khong_doi_khi_moi_sau_cua_so_con_moi_thi_THAY_doi_chung():
    tt, dong = thi_truong(1, KAPPA_2X)
    dong_m, gia_m = _mo_sau(dong, tt.gia, S)
    g0, g1 = _bat_dau_vao_de_xuat(dong, tt.gia), _bat_dau_vao_de_xuat(dong_m, gia_m)
    r0, r1 = V.de_xuat(g0["dong"], g0["gia"]), V.de_xuat(g1["dong"], g1["gia"])
    assert [(x["ten"], x["z"], x["sd_null"]) for x in r0] == [(x["ten"], x["z"], x["sd_null"]) for x in r1]
    thay = V.de_xuat(dong_m, gia_m)                                # đối chứng: nếu THẤY phần mồi thì z phải khác
    assert [x["z"] for x in thay] != [x["z"] for x in r0]


def test_G4_de_xuat_chay_tron_khi_oracle_va_bo_sinh_bi_buoc_day(monkeypatch):
    tt, dong = thi_truong(1, KAPPA_2X)
    dong_n, gia_n = V.cat_den_phien(dong, tt.gia, S - 1)
    truoc = V.de_xuat(dong_n, gia_n)

    def bay(*a, **k):
        raise AssertionError("bộ đề xuất đã chạm oracle hay bộ sinh")
    for ten in ("tinh_su_that", "sinh_thi_truong", "sinh_null", "_sinh_loi", "spec_ngoai_hai_se", "ho_spec_oracle",
                "dong_thoi_gian", "lich_phien"):
        monkeypatch.setattr(T, ten, bay)
    assert V.de_xuat(dong_n, gia_n) == truoc


# ══ lịch và sổ ═══════════════════════════════════════════════════════════════════════════════════

def test_lich_khai_va_doc_khop_dong_thoi_gian_cua_lat_1():
    dtg = T.dong_thoi_gian()
    ngay = list(T.lich_phien(dtg["tong"]))
    assert V.phien_khai(ngay, 3) == dtg["khai"]
    assert [V.phien_doc(k) for k in dtg["khai"]] == dtg["doc"]


def test_phien_doc_la_phien_dau_tien_ma_may_do_khong_con_CHUA_TOI_MOC():
    """Kiểm CÁC HAI PHÍA bằng chính máy đo (`cham_xac_nhan.cham_mot`), không bằng công thức: ở phiên đọc − 1 còn
    251 phiên có nhãn (CHUA TOI MOC), ở phiên đọc đủ 252 và phán."""
    tt, dong = thi_truong(1, KAPPA_2X)
    ngay = [str(n) for n in tt.gia.index]
    k = V.phien_khai(ngay, 1)[0]
    doc = V.phien_doc(k)
    d = {"khai_ngay": ngay[k], "mo_ta": "m", "ly_do": "l", "qua_sang": None, "spec": HO[T.TEN_SPEC_G]}
    for t, trang_thai, n in ((doc - 1, cb.CHUA_TOI_MOC, cb.MOC_DOC - 1), (doc, "QUA", cb.MOC_DOC)):
        dong_cat, gia_cat = V.cat_den_phien(dong, tt.gia, t)
        c = cx.cham_mot(dong_cat, "DX1", d, gia_cat, 0.05 / 3, so=200)
        assert c["n_phien_co_nhan"] == n and c["trang_thai"] == trang_thai


def test_phien_khai_loi_va_thang_thu_i_theo_lich_duong():
    ngay = [str(n) for n in T.lich_phien(594)]
    k = V.phien_khai(ngay, 3)
    assert [ngay[i][:7] for i in k] == ["2100-07", "2100-08", "2100-09"]
    assert all(ngay[i - 1][:7] != ngay[i][:7] for i in k), "phiên khai là phiên ĐẦU của tháng"
    assert ngay[S - 1][:7] == "2100-06"
    with pytest.raises(ValueError, match="khong phu thang"):
        V.phien_khai(ngay[:140], 3)
    with pytest.raises(ValueError, match="cua so da nhin"):
        V.phien_khai(ngay[:10], 1)


def test_khai_ung_vien_di_qua_kiem_so_ung_vien_tran_mot_moi_thang_va_khong_sua_so_goc():
    so = {"ung_vien": {}}
    so1 = V.khai_ung_vien(so, "DX1", "2100-07-01", HO[T.TEN_SPEC_G], "m", "l")
    assert so == {"ung_vien": {}} and cb.so_da_sang(so1) == 1
    with pytest.raises(ValueError, match="qua 1 ung vien"):
        V.khai_ung_vien(so1, "DX2", "2100-07-15", HO[T.TEN_SPEC_Z], "m", "l")      # cùng tháng dương lịch
    with pytest.raises(ValueError, match="da khai"):
        V.khai_ung_vien(so1, "DX1", "2100-08-02", HO[T.TEN_SPEC_Z], "m", "l")
    with pytest.raises(ValueError):
        V.khai_ung_vien(so1, "DX2", "2100-08-02", {"loai": "trong_so", "trong_so": {"trend_score": 0.5}}, "m", "l")
    so2 = V.khai_ung_vien(so1, "DX2", "2100-08-02", HO[T.TEN_SPEC_Z], "m", "l")
    assert cb.so_da_sang(so2) == 2 and cb.nguong(so2) == pytest.approx(0.025)
    assert so2["ung_vien"]["DX1"]["qua_sang"] is None


def test_lich_cua_vong_co_ba_ung_vien_moi_thang_mot_va_K_la_so_da_khai(vong_QUA_dau):
    v = vong_QUA_dau
    assert [m["ma"] for m in v["lich"]] == ["DX1", "DX2", "DX3"] and v["K"] == 3
    dtg = T.dong_thoi_gian()
    assert [m["khai_phien"] for m in v["lich"]] == dtg["khai"] and [m["doc_phien"] for m in v["lich"]] == dtg["doc"]
    assert [m["ten"] for m in v["lich"]] == [T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H]


def test_doc_o_phien_doc_va_K_la_so_da_khai_tai_luc_doc(vong_chuoi_THUA_DANGCHAM_QUA):
    v = vong_chuoi_THUA_DANGCHAM_QUA
    for d, m in zip(v["doc"], v["lich"]):
        assert d["phien_doc"] == m["doc_phien"] and d["K"] == 3 and d["nguong"] == pytest.approx(0.05 / 3)
        assert d["n_phien"] == cb.MOC_DOC and d["n_ma"] == T.SO_MA


def test_thi_truong_ngan_hon_phien_doc_thi_khai_roi_dung_khong_doc_khong_nang(monkeypatch):
    tt, dong = thi_truong(1, KAPPA_2X)
    ngan = 300
    dong_n, gia_n = V.cat_den_phien(dong, tt.gia, ngan - 1)
    goi = []
    monkeypatch.setattr(V.cx, "cham", lambda *a, **k: goi.append(1))
    v = V.chay_vong(dong_n, gia_n, de_xuat_gia(T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H))
    assert goi == [] and v["doc"] == [] and v["ket_cuc"] == V.KET_CUC_KHONG_NANG_CAP
    assert set(v["trang_thai"].values()) == {V.CHUA_DOC} and v["tien_ve_truoc"] is None
    assert [m["doc_ngay"] for m in v["lich"]] == [None, None, None]


def test_bo_de_xuat_khong_co_spec_duong_thi_khong_khai_gi():
    tt, dong = thi_truong(1, KAPPA_2X)
    v = V.chay_vong(dong, tt.gia, lambda d, g: [{"ten": "x", "spec": HO[T.TEN_SPEC_G], "delta": -0.1, "z": -0.1}])
    assert v["lich"] == [] and v["so_ung_vien"] == {"ung_vien": {}} and v["doc"] == [] and v["K"] == 0
    assert v["ket_cuc"] == V.KET_CUC_KHONG_NANG_CAP


def test_chay_vong_that_bo_de_xuat_co_so_tren_thi_truong_2x_khai_ba_va_nang_cap_dung_luat():
    tt, dong = thi_truong(1, KAPPA_2X)
    v = V.chay_vong(dong, tt.gia)
    xep = v["de_xuat"]["xep"]
    assert v["de_xuat"]["da_chon"] == [x["ten"] for x in xep if x["delta"] > 0][:3]
    assert xep[0]["ten"] == T.TEN_SPEC_G, "ở lợi thế 2× mono volume phải đứng đầu trên cửa sổ đã nhìn"
    assert v["ket_cuc"] == V.KET_CUC_NANG_CAP and v["doc"][0]["trang_thai"] == "QUA"
    assert v["huy"] == ["DX2", "DX3"] and v["K"] == 3
    assert v["cua_so_nhin"] == S and all(x["n_phien"] == S - T.DO_TRE_NHAN == 104 for x in xep)


# ══ G7 — bất biến thời gian ════════════════════════════════════════════════════════════════════════

class _Dung(Exception):
    pass


def _bat_dau_vao_de_xuat(dong, gia):
    """Chạy `chay_vong` với bộ đề xuất là một MÁY GHI rồi nổ: thấy chính xác thứ vòng đưa cho bộ đề xuất."""
    got = {}

    def ghi(d, g):
        got["dong"], got["gia"] = copy.deepcopy(d), g.copy()
        raise _Dung
    with pytest.raises(_Dung):
        V.chay_vong(dong, gia, ghi)
    return got


def _mo_sau(dong, gia, tu):
    """Mồi: từ phiên `tu` trở đi giá nhân ngẫu nhiên và dòng quyết định bị thay bằng nhiễu."""
    rng = np.random.default_rng(555)
    vi_tri = {str(n): i for i, n in enumerate(gia.index)}
    g = gia.copy()
    g.iloc[tu:] = g.iloc[tu:].to_numpy() * rng.uniform(0.4, 2.5, size=g.iloc[tu:].shape)
    d = []
    for r in dong:
        r = dict(r)
        if vi_tri[r["signal_date"]] >= tu:
            tp = {k: float(x) for k, x in zip(cb.THANH_PHAN, rng.uniform(0, 100, size=5))}
            r["components"], r["score"] = json.dumps(tp), int(rng.integers(5, 95))
        d.append(r)
    return d, g


def test_G7_bo_de_xuat_chi_thay_phien_0_toi_S_tru_1_ca_dong_lan_gia():
    tt, dong = thi_truong(1, KAPPA_2X)
    ngay = [str(n) for n in tt.gia.index]
    got = _bat_dau_vao_de_xuat(dong, tt.gia)
    khai0 = V.phien_khai(ngay, 1)[0]
    assert len(got["gia"]) == S == 126 and str(got["gia"].index[-1]) == ngay[S - 1]
    assert max(r["signal_date"] for r in got["dong"]) == ngay[S - 1] <= ngay[khai0 - 1]
    assert len(got["dong"]) == S * T.SO_MA and got["gia"].equals(tt.gia.iloc[:S])


def test_G7_moi_sau_cua_so_khong_doi_dau_ra_cua_bo_de_xuat_gia_tai_chi_so_S_tro_di():
    """Mồi: giá VÀ dòng từ phiên S trở đi bị thay bằng nhiễu. Hạng của 11 spec phải y hệt từng bit."""
    tt, dong = thi_truong(1, KAPPA_2X)
    dong_m, gia_m = _mo_sau(dong, tt.gia, S)
    assert not gia_m.equals(tt.gia) and dong_m != dong
    g0, g1 = _bat_dau_vao_de_xuat(dong, tt.gia), _bat_dau_vao_de_xuat(dong_m, gia_m)
    assert g0["dong"] == g1["dong"] and g0["gia"].equals(g1["gia"])
    r0 = V.de_xuat(g0["dong"], g0["gia"])
    r1 = V.de_xuat(g1["dong"], g1["gia"])
    assert r0 == r1 and len(r0) == 11
    # đối chứng: nếu bộ đề xuất THẤY phần mồi (không cắt) thì đầu ra PHẢI khác — mồi có tác dụng
    assert V.de_xuat(dong_m, gia_m) != V.de_xuat(dong, tt.gia)
    assert V.de_xuat(dong_m, gia_m)[0]["n_phien"] != S - T.DO_TRE_NHAN


def test_G7_xep_hang_that_cua_vong_khong_doi_khi_moi_sau_cua_so():
    tt, dong = thi_truong(1, KAPPA_2X)
    dong_m, gia_m = _mo_sau(dong, tt.gia, S)
    a = V.chay_vong(dong, tt.gia, so_hoan_vi=50)["de_xuat"]
    b = V.chay_vong(dong_m, gia_m, so_hoan_vi=50)["de_xuat"]
    assert a == b


def test_G7_cua_so_nhin_la_hang_S_khong_phai_ngay_khai_tru_mot():
    """Đọc (a) của mục 17 khoản 1: cửa sổ = S phiên (104 phiên có nhãn), KHÔNG kéo giá tới ngày khai − 1 (106)."""
    tt, dong = thi_truong(1, KAPPA_2X)
    ngay = [str(n) for n in tt.gia.index]
    assert V.phien_khai(ngay, 1)[0] - 1 > S - 1                    # ngày khai − 1 (phiên 127) nằm SAU cửa sổ
    got = _bat_dau_vao_de_xuat(dong, tt.gia)
    xep = V.de_xuat(got["dong"], got["gia"])
    assert {x["n_phien"] for x in xep} == {S - T.DO_TRE_NHAN} == {104}


def test_G7_moi_lan_doc_chi_thay_du_lieu_toi_phien_doc_cua_no(monkeypatch):
    tt, dong = thi_truong(1, KAPPA_2X)
    ngay = [str(n) for n in tt.gia.index]
    thay = []
    that = V.cx.cham

    def ghi(rows, so_uv, bang, hat, so):
        thay.append((max(str(r["signal_date"])[:10] for r in rows), str(bang["gia"].index[-1]), list(bang["gia"].index)[0]))
        return that(rows, so_uv, bang, hat, so)
    monkeypatch.setattr(V.cx, "cham", ghi)
    v = V.chay_vong(dong, tt.gia, de_xuat_gia(T.TEN_SPEC_H, T.TEN_SPEC_Z, T.TEN_SPEC_G), so_hoan_vi=50)
    assert len(thay) == len(v["doc"]) == 3
    for (ngay_dong, ngay_gia, dau), d in zip(thay, v["doc"]):
        assert ngay_dong == ngay_gia == ngay[d["phien_doc"]] and dau == ngay[0]


def test_G7_moi_sau_phien_doc_khong_doi_phan_quyet_cua_lan_doc_do():
    tt, dong = thi_truong(1, KAPPA_2X)
    goc = vong(1, KAPPA_2X, T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H)
    t = goc["doc"][0]["phien_doc"]
    dong_m, gia_m = _mo_sau(dong, tt.gia, t + 1)
    v = V.chay_vong(dong_m, gia_m, de_xuat_gia(T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H))
    assert v["doc"] == goc["doc"] and v["so_phien_ban"] == goc["so_phien_ban"]
    assert v["tien_ve_truoc"] != goc["tien_ve_truoc"], "đối chứng: phần mồi nằm trong cửa sổ tiến-về-trước"


def test_G7_hieu_luc_tu_phien_sau_o_dong_quyet_dinh_sau_nang_cap():
    """Phiên đọc t: điểm ghi ở t vẫn là bản cũ; chỉ từ t + 1 mới là `int(diem_ung_vien)`."""
    pb = V.nang_cap(V.so_phien_ban_dau(), _ket_gia("QUA"), "DX1", 1, _so_uv_gia())
    tp = {"trend_score": 0.0, "momentum_score": 0.0, "volume_score": 77.0, "sr_score": 0.0, "risk_score": 0.0}
    ngay = ["2100-01-04", "2100-01-05", "2100-01-06"]
    dong = [{"symbol": "A", "signal_date": n, "score": 11, "components": json.dumps(tp), "at": i, "seq": i}
            for i, n in enumerate(ngay)]
    ap = V.ap_phien_ban(dong, pb, ngay)
    assert [r["score"] for r in ap] == [11, 11, 77]            # t = 1 là phiên đọc: bản mới từ phiên 2


# ══ G6 — không chấm lại ══════════════════════════════════════════════════════════════════════════

CAM_TU_CHAM = {"so_cap", "phan_quyet", "cham_mot", "permutation", "permuted", "shuffle", "rank", "rankdata", "argsort",
               "corrcoef", "spearmanr", "default_rng", "RandomState"}
#: BƯỚC 300: bộ đề xuất chuẩn hoá cần hạng giữa của CHÍNH `so_cap` (không bản sao): `cb._hang_giua`, ba lần gọi,
#: đúng một hàm. Mọi chỗ khác trong `vong_hoc_gia.py` vẫn cấm nó.
HAM_DUOC_GOI_HANG_GIUA = "thong_ke_null"


def _cay(duong):
    return ast.parse(Path(duong).read_text(encoding="utf-8"))


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


def test_G6_vong_khong_goi_so_cap_phan_quyet_hay_viet_lai_IC_va_hoan_vi():
    cay = _cay(DUONG_V)
    sai = _goi(cay) & CAM_TU_CHAM
    assert not sai, sorted(sai)
    # không nhắc tên các hàm ấy dưới dạng chuỗi (getattr(cb, "so_cap")) hay thuộc tính
    assert not (set(_chuoi(cay)) & CAM_TU_CHAM) and not (_ten_dung(cay) & CAM_TU_CHAM)
    # bước xác nhận đi qua `cham_xac_nhan.cham`, đúng MỘT lời gọi, trong `chay_vong`
    cham = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "cham" and isinstance(n.func.value, ast.Name) and n.func.value.id == "cx"]
    assert len(cham) == 1
    ham = {f.name: f for f in ast.walk(cay) if isinstance(f, ast.FunctionDef)}
    assert cham[0] in list(ast.walk(ham["chay_vong"]))
    # IC chỉ tính bằng `E.rho_hang` của máy đo, ở đúng hai hàm
    rho = {f.name for f in ham.values() for n in ast.walk(f) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "rho_hang"}
    assert rho == {"de_xuat", "kiem_tien_ve_truoc"}


def test_G6_phep_do_AST_bat_duoc_mau_xau():
    for m in ("cb.so_cap(B, C, Y, rng)", "cb.phan_quyet(b, s, n, a, h)", "np.random.permutation(5)",
              "s.rank()", "rng = np.random.default_rng(1)", "x = getattr(cb, 'so_cap')", "cx.cham_mot(r, m, d, g, a)"):
        c = ast.parse(m)
        assert (_goi(c) & CAM_TU_CHAM) or (set(_chuoi(c)) & CAM_TU_CHAM), m
    for m in ("cx.cham(a, b, c)", "E.rho_hang(x, y)", "cb.ma_tran_cap(a, b, c)"):
        assert not (_goi(ast.parse(m)) & CAM_TU_CHAM), m


def _cho_hang_giua(cay) -> list[tuple[str, bool]]:
    """Mọi chỗ nhắc `_hang_giua` (tên trần, thuộc tính, hay chuỗi): (tên hàm bao ngoài, có phải `cb._hang_giua(...)`)."""
    ra = []
    for f in [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)]:
        goi = {id(n.func) for n in ast.walk(f) if isinstance(n, ast.Call)}
        for n in ast.walk(f):
            if isinstance(n, ast.Attribute) and n.attr == "_hang_giua":
                ra.append((f.name, id(n) in goi and isinstance(n.value, ast.Name) and n.value.id == "cb"))
            elif isinstance(n, ast.Name) and n.id == "_hang_giua":
                ra.append((f.name, False))
            elif isinstance(n, ast.Constant) and n.value == "_hang_giua":
                ra.append((f.name, False))
    return ra


def test_G6_hang_giua_chi_duoc_goi_ba_lan_o_dung_mot_ham_va_la_cua_cham_bong():
    cay = _cay(DUONG_V)
    cho = _cho_hang_giua(cay)
    assert cho == [(HAM_DUOC_GOI_HANG_GIUA, True)] * 3, cho
    # không nhắc nó ở mức module (import, gán, chuỗi) mà hàm nào cũng không bao ngoài
    mo_dau = [n for n in ast.walk(cay) if (isinstance(n, ast.Name) and n.id == "_hang_giua")
              or (isinstance(n, ast.Attribute) and n.attr == "_hang_giua")
              or (isinstance(n, ast.Constant) and n.value == "_hang_giua")]
    assert len(mo_dau) == 3
    mau_xau = {"mot_ham_khac": "def khac(a):\n    return cb._hang_giua(a)\n",
               "ban_sao": "def thong_ke_null(a):\n    return _hang_giua(a)\n",
               "chuoi": "def thong_ke_null(a):\n    return getattr(cb, '_hang_giua')(a)\n"}
    for ten, m in mau_xau.items():
        c = _cho_hang_giua(ast.parse(m))
        assert c != [(HAM_DUOC_GOI_HANG_GIUA, True)], ten


def test_G6_ca_so_cap_chi_duoc_goi_tu_ben_trong_phan_quyet_va_moi_lan_doc_di_qua_phan_quyet(monkeypatch):
    nguoi_goi, phan_quyet_goi = [], []
    so_cap, phan_quyet = cb.so_cap, cb.phan_quyet

    def spy_so_cap(*a, **k):
        nguoi_goi.append(sys._getframe(1).f_code.co_name)
        return so_cap(*a, **k)

    def spy_phan_quyet(*a, **k):
        phan_quyet_goi.append(1)
        return phan_quyet(*a, **k)
    monkeypatch.setattr(cb, "so_cap", spy_so_cap)
    monkeypatch.setattr(cb, "phan_quyet", spy_phan_quyet)
    tt, dong = thi_truong(1, KAPPA_2X)
    v = V.chay_vong(dong, tt.gia, de_xuat_gia(T.TEN_SPEC_H, T.TEN_SPEC_Z, "mono_trend_score"), so_hoan_vi=50)
    assert len(v["doc"]) == 3
    assert set(nguoi_goi) == {"phan_quyet"}
    # `cham` chấm MỌI ứng viên của sổ ở mỗi lần đọc: 3 ứng viên × 3 lần = 9 lần `phan_quyet`, nhưng `so_cap`
    # chỉ chạy ở ứng viên ĐÃ TỚI MỐC: 1 + 2 + 3 = 6
    assert len(phan_quyet_goi) == 9 and nguoi_goi == ["phan_quyet"] * 6


# ══ G2 — đường thật không nhập module thị trường giả ═════════════════════════════════════════════

MODULE_GIA = ("thi_truong_gia", "vong_hoc_gia", "thi_truong_gia_tang2")      # BƯỚC 292: thêm Tầng 2
DUOC_NHAP = {"vong_hoc_gia.py", "tools/hieu_chuan_thi_truong_gia.py", "tools/chay_vong_thi_truong_gia.py",
             "thi_truong_gia_tang2.py", "tools/chay_tang2_thi_truong_gia.py",
             "tools/oracle_tang2_thi_truong_gia.py",      # BƯỚC 293: bảng sự thật Tầng 2
             "tools/chay_vong_tang2_thi_truong_gia.py",   # BƯỚC 293: chi phí của vòng trên Tầng 2
             "tools/chay_chinh_thuc_thi_truong_gia.py"}   # BƯỚC 295: dụng cụ chạy chính thức dòng hạt 2 · 3 · 4
DUONG_THAT = ("paper_trading.py", "paper_runner.py", "paper_metrics.py", "run_daily.py", "master_agent.py",
              "analysis_agents.py", "walkforward.py", "sheets_store.py", "cham_bong.py", "cham_xac_nhan.py",
              "hau_kiem_loi.py", "ban_tin.py", "san_dau.py", "tools/san_dau.py")


def _nhap_hoac_nhac(cay) -> set:
    """Module giả bị nhập (câu lệnh import) HOẶC nhắc bằng chuỗi (`importlib.import_module("vong_hoc_gia")`)."""
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ra |= {a.name.split(".")[0] for a in n.names} & set(MODULE_GIA)
        elif isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] in MODULE_GIA:
                ra.add(n.module.split(".")[0])
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            ra |= {m for m in MODULE_GIA if n.value == m or n.value.startswith(m + ".")}
    return ra


def _nguoi_nhap_module_gia() -> dict:
    ra = {}
    for p in duyet_repo.duyet(GOC, "*.py"):
        rel = p.relative_to(GOC).as_posix()
        if rel.split("/")[0] in {"tests", ".venv", ".git"}:
            continue
        got = _nhap_hoac_nhac(ast.parse(p.read_text(encoding="utf-8")))
        if got:
            ra[rel] = got
    return ra


def test_G2_duong_that_KHONG_nhap_module_thi_truong_gia_hay_vong_hoc_gia():
    nguoi = _nguoi_nhap_module_gia()
    assert set(nguoi) <= DUOC_NHAP, f"chỉ {sorted(DUOC_NHAP)} được nhập: {nguoi}"
    assert {"vong_hoc_gia.py", "tools/chay_vong_thi_truong_gia.py", "tools/hieu_chuan_thi_truong_gia.py",
            "thi_truong_gia_tang2.py", "tools/chay_tang2_thi_truong_gia.py",
            "tools/oracle_tang2_thi_truong_gia.py", "tools/chay_vong_tang2_thi_truong_gia.py",
            "tools/chay_chinh_thuc_thi_truong_gia.py"} <= set(nguoi)
    for ten in DUONG_THAT:
        assert ten not in nguoi, ten
    assert not [x for x in nguoi if x.startswith("backtest/") or x == "app.py"]


def test_G2_phep_do_bat_duoc_importer_la_ca_dang_chuoi():
    for m in ("import vong_hoc_gia", "from thi_truong_gia import sinh_null", "import thi_truong_gia as T",
              "importlib.import_module('vong_hoc_gia')", "__import__('thi_truong_gia')"):
        assert _nhap_hoac_nhac(ast.parse(m)), m
    for m in ("import numpy", "x = 'vong_hoc_gia_khac'", "from cham_bong import so_cap"):
        assert not _nhap_hoac_nhac(ast.parse(m)), m


def test_G2_nap_duong_that_khong_keo_theo_module_thi_truong_gia():
    """Theo đường nhập GIÁN TIẾP: nạp cả đường thật trong một tiến trình sạch rồi xem `sys.modules`."""
    ma = ("import sys, json; sys.path.insert(0, %r); "
          "import paper_trading, paper_runner, paper_metrics, master_agent, analysis_agents, cham_bong, "
          "cham_xac_nhan, hau_kiem_loi, ban_tin, san_dau; "
          "print(json.dumps([m for m in ('thi_truong_gia', 'vong_hoc_gia', 'thi_truong_gia_tang2') if m in sys.modules]))" % str(GOC))
    r = subprocess.run([sys.executable, "-I", "-c", ma], capture_output=True, text=True, cwd=str(GOC),
                       timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    assert json.loads(r.stdout.strip().splitlines()[-1]) == [], r.stdout


# ══ G4 — oracle cách ly khỏi vòng ════════════════════════════════════════════════════════════════

TEN_ORACLE = {"tinh_su_that", "su_that", "spec_ngoai_hai_se", "ho_spec_oracle", "HAT_SU_THAT", "SO_PHIEN_SU_THAT",
              "SO_KHOI_SU_THAT", "se_mc", "TEN_SPEC_Z", "TEN_SPEC_H", "TEN_SPEC_G", "spec_z"}
TEN_BO_SINH = {"sinh_thi_truong", "sinh_null", "_sinh_loi", "ThiTruongGia", "kappa", "_ar1", "_roi_rac",
               "dong_quyet_dinh", "lich_phien", "dong_thoi_gian", "tinh_su_that"}
T_DUOC_DUNG = {"ho_spec_f", "NGAY_DAU", "DO_TRE_NHAN", "SO_PHIEN_DA_NHIN", "SO_PHIEN_TIEN_VE_TRUOC",
               "SO_UNG_VIEN_KHAI"}


def _thuoc_tinh_cua(cay, ten_goc: str) -> set:
    return {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
            and n.value.id == ten_goc}


def test_G4_vong_khong_nhac_ten_oracle_hay_bo_sinh_va_chi_dung_vai_hang_cua_T():
    cay = _cay(DUONG_V)
    cam = TEN_ORACLE | TEN_BO_SINH
    assert not (_ten_dung(cay) & cam), sorted(_ten_dung(cay) & cam)
    assert not (set(_chuoi(cay)) & cam), sorted(set(_chuoi(cay)) & cam)
    dung = _thuoc_tinh_cua(cay, "T")
    assert dung and dung <= T_DUOC_DUNG, sorted(dung - T_DUOC_DUNG)
    assert {"ho_spec_f", "SO_PHIEN_DA_NHIN", "DO_TRE_NHAN"} <= dung
    # nhập cả module (`import thi_truong_gia as T`), không `from thi_truong_gia import tên`
    nhap = [n for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and (n.module or "") == "thi_truong_gia"]
    assert nhap == []


def test_G4_phep_do_AST_bat_duoc_mau_xau():
    for m in ("T.tinh_su_that(1, 1, 0.0)", "x = tt.su_that", "from thi_truong_gia import tinh_su_that",
              "T.spec_ngoai_hai_se(s)", "k = 'su_that'", "T.sinh_thi_truong(9001, 1, 0.1)", "x = kappa"):
        c = ast.parse(m)
        assert ((_ten_dung(c) | set(_chuoi(c))) & (TEN_ORACLE | TEN_BO_SINH)), m
    assert _thuoc_tinh_cua(ast.parse("T.tinh_su_that(1)\nT.ho_spec_f()"), "T") - T_DUOC_DUNG == {"tinh_su_that"}
    assert not ((_ten_dung(ast.parse("T.ho_spec_f()\nx = T.NGAY_DAU")) | set()) & (TEN_ORACLE | TEN_BO_SINH))


def test_G4_chay_vong_chay_tron_khi_oracle_va_bo_sinh_bi_buoc_day(monkeypatch):
    tt, dong = thi_truong(1, KAPPA_2X)

    def bay(*a, **k):
        raise AssertionError("vòng đã chạm oracle hay bộ sinh")
    for ten in ("tinh_su_that", "sinh_thi_truong", "sinh_null", "_sinh_loi", "spec_ngoai_hai_se", "ho_spec_oracle",
                "dong_thoi_gian", "lich_phien"):
        monkeypatch.setattr(T, ten, bay)
    v = V.chay_vong(dong, tt.gia, so_hoan_vi=50)
    assert v["ket_cuc"] in (V.KET_CUC_NANG_CAP, V.KET_CUC_KHONG_NANG_CAP) and v["lich"]


def test_G4_vong_khong_nhan_ThiTruongGia_vi_no_mang_oracle_theo():
    tt = T.sinh_thi_truong(LUONG_TEST, 77, KAPPA_2X, so_phien=200, co_su_that=False)
    with pytest.raises((TypeError, AttributeError, KeyError)):
        V.chay_vong(tt, tt.gia)


def test_G4_dung_cu_doc_oracle_SAU_khi_vong_da_quyet(monkeypatch):
    thu_tu = []
    monkeypatch.setattr(CV.V, "chay_vong", lambda *a, **k: thu_tu.append("vong") or {"x": 1})
    monkeypatch.setattr(CV.T, "tinh_su_that", lambda *a, **k: thu_tu.append("oracle") or {"y": 1})
    monkeypatch.setattr(CV.T, "sinh_thi_truong", lambda *a, **k: thu_tu.append("sinh") or
                        type("X", (), {"dong_quyet_dinh": lambda s: [], "gia": None, "ma": ("A",)})())
    CV.chay_mot_thi_truong(LUONG_TEST, 1, 0.01)
    assert thu_tu == ["sinh", "vong", "oracle"]
    thu_tu.clear()
    CV.chay_mot_thi_truong(LUONG_TEST, 1, 0.01, co_oracle=False)
    assert thu_tu == ["sinh", "vong"]


def test_G4_AST_trong_dung_cu_loi_goi_vong_dung_TRUOC_loi_goi_oracle():
    ham = {f.name: f for f in ast.walk(_cay(DUONG_TOOL)) if isinstance(f, ast.FunctionDef)}["chay_mot_thi_truong"]
    dong = {}
    for n in ast.walk(ham):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            dong.setdefault(n.func.attr, n.lineno)
    assert dong["chay_vong"] < dong["tinh_su_that"], dong


# ══ cửa dòng hạt của dụng cụ `chay-vong` ═══════════════════════════════════════════════════════════

@pytest.mark.parametrize("luong", [0, 2, 3, 4, 5, 6, 7, 8, 9000, 9002, 10_000, -1, True, 1.0, "1", None, "9001"])
def test_kiem_luong_no_voi_moi_dong_ngoai_1_va_9001(luong):
    with pytest.raises(ValueError, match="dong hat"):
        CV.kiem_luong(luong)


def test_kiem_luong_nhan_dong_1_va_9001_ca_kieu_numpy_va_khong_chan_nham_dong_chan():
    for v in (1, 9001, np.int64(1), np.int32(9001)):
        CV.kiem_luong(v)
    assert CV.LUONG_DUOC_PHEP == (1, 9001) and CV.LUONG_TEST == 9001
    assert set(CV.LUONG_BI_CHAN) == {2, 3, 4, 5} and not set(CV.LUONG_BI_CHAN) & set(CV.LUONG_DUOC_PHEP)


@pytest.mark.parametrize("luong", [2, 3, 4, 5, 6])
def test_moi_duong_vao_chay_vong_no_voi_dong_bi_chan_va_khong_de_bo_sinh_chay(luong, monkeypatch):
    def bay(*a, **k):
        raise AssertionError("bo sinh da chay")
    monkeypatch.setattr(T, "sinh_thi_truong", bay)
    monkeypatch.setattr(T, "tinh_su_that", bay)
    monkeypatch.setattr(V, "chay_vong", bay)
    with pytest.raises(ValueError, match="dong hat"):
        CV.chay_mot_thi_truong(luong, 1, 0.01)
    with pytest.raises(ValueError, match="dong hat"):
        CV.chay_mot_thi_truong(luong, 1, 0.01, co_oracle=False)
    assert CV.main(["--luong", str(luong), "--kappa", "0.01"]) == 2


def test_main_tu_choi_dong_bi_chan_bang_ma_thoat_2_va_noi_ro_ly_do(capsys):
    assert CV.main(["--luong", "2", "--chi-so", "1", "--muc", "2"]) == 2
    err = capsys.readouterr().err
    assert "dong hat" in err and "Lat 5" in err


def _ham(cay) -> dict:
    return {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}


def _ham_goi_bo_sinh_thieu_cua(nguon: str) -> list[str]:
    vao = {"sinh_thi_truong", "sinh_null", "tinh_su_that", "_sinh_loi", "chay_vong"}
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


def test_AST_moi_ham_cua_dung_cu_goi_bo_sinh_hay_vong_phai_goi_kiem_luong_truoc():
    nguon = DUONG_TOOL.read_text(encoding="utf-8")
    assert _ham_goi_bo_sinh_thieu_cua(nguon) == []
    assert "chay_mot_thi_truong" in {t for t, f in _ham(ast.parse(nguon)).items()
                                     if _goi(f) & {"sinh_thi_truong", "chay_vong"}}


def test_AST_phep_do_bat_dung_mau_xau_cua_cua_kiem_luong():
    xau = "def f(l):\n    return T.sinh_thi_truong(l, 1, 0.0)\n"
    xau2 = "def f(l):\n    x = T.tinh_su_that(l, 1, 0.0)\n    kiem_luong(l)\n"
    xau3 = "def f(l):\n    return V.chay_vong(d, g)\n"
    tot = "def f(l):\n    kiem_luong(l)\n    return T.sinh_thi_truong(l, 1, 0.0)\n"
    assert _ham_goi_bo_sinh_thieu_cua(xau) == ["f"] and _ham_goi_bo_sinh_thieu_cua(xau2) == ["f"]
    assert _ham_goi_bo_sinh_thieu_cua(xau3) == ["f"] and _ham_goi_bo_sinh_thieu_cua(tot) == []
    assert _ham_goi_bo_sinh_thieu_cua("def f(l):\n    return 1\n") == []


def test_AST_dung_cu_khong_co_doi_so_dong_hat_ngoai_luong_va_hat_khong_viet_tay():
    cay = _cay(DUONG_TOOL)
    co = [n.args[0].value for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "add_argument" and n.args and isinstance(n.args[0], ast.Constant)]
    assert "--luong" in co and not [c for c in co if "hat" in c or "stream" in c], co
    tu_khoa = [(k.arg, k.value.value) for n in ast.walk(cay) if isinstance(n, ast.Call)
               for k in n.keywords if k.arg == "luong" and isinstance(k.value, ast.Constant)]
    assert tu_khoa == [], tu_khoa
    # chỉ `LUONG_TEST`, `LUONG_DUOC_PHEP`, `LUONG_BI_CHAN` khai số dòng hạt
    gan = {t.id: ast.literal_eval(n.value) for n in ast.walk(cay) if isinstance(n, ast.Assign)
           for t in n.targets if isinstance(t, ast.Name) and t.id.startswith("LUONG")
           and isinstance(n.value, (ast.Constant, ast.Tuple))}
    assert gan == {"LUONG_TEST": 9001, "LUONG_DUOC_PHEP": (1, 9001), "LUONG_BI_CHAN": (2, 3, 4, 5)}, gan


def test_vong_khong_co_cua_vao_bo_sinh_nen_khong_co_dong_hat_o_do():
    cay = _cay(DUONG_V)
    ten = _ten_dung(cay)
    assert not [t for t in ten if "luong" in t.lower() or "hat" == t.lower() or "seed" in t.lower()
                or "stream" in t.lower()], sorted(ten)


# ══ G5 — ngày giả ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ngay", [["2026-11-20"], ["2100-01-04", "2099-12-31"], ["2100-01-04", "2026-01-02"], []])
def test_G5_kiem_ngay_gia_tu_choi_ngay_that_hay_truoc_2100_01_04(ngay):
    with pytest.raises(ValueError):
        V.kiem_ngay_gia(ngay)


def test_G5_kiem_ngay_gia_nhan_ngay_gia_va_vong_tu_choi_dong_hay_bang_gia_that():
    V.kiem_ngay_gia([T.NGAY_DAU, "2102-04-13"])
    tt, dong = thi_truong(1, KAPPA_2X)
    that = [dict(r, signal_date="2026-11-20") for r in dong[:60]]
    with pytest.raises(ValueError, match="khong phai thi truong gia"):
        V.chay_vong(that, tt.gia)
    gia_that = tt.gia.copy()
    gia_that.index = [f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}" for i in range(len(gia_that))]
    with pytest.raises(ValueError, match="khong phai thi truong gia"):
        V.chay_vong(dong, gia_that)


def test_cat_den_phien_giu_dung_phien_cuoi_tinh_ca_phien_do_va_tu_choi_chi_so_xau():
    tt, dong = thi_truong(1, KAPPA_2X)
    d, g = V.cat_den_phien(dong, tt.gia, 10)
    ngay = [str(n) for n in tt.gia.index]
    assert len(g) == 11 and str(g.index[-1]) == ngay[10] and len(d) == 11 * T.SO_MA
    assert max(r["signal_date"] for r in d) == ngay[10] and min(r["signal_date"] for r in d) == ngay[0]
    for xau in (-1, len(ngay), 1.0, True, None):
        with pytest.raises(ValueError):
            V.cat_den_phien(dong, tt.gia, xau)


# ══ bảng giá giả, biên bản, gác ghi / thế giới thật ═════════════════════════════════════════════

def test_bang_gia_gia_qua_phan_tich_bang_gia_cua_buoc_xac_nhan_va_khong_ket_qua_loi():
    tt, dong = thi_truong(1, KAPPA_2X)
    b = V.bang_gia_gia(tt.gia.iloc[:500])
    assert b["keo_luc"].endswith("T00:00:00+07:00")
    assert set(b["nguon"].values()) == {"vci"} and set(b["nguon"]) == set(tt.ma)
    ngay_cuoi = str(tt.gia.index[499])
    import datetime as dt
    assert b["keo_luc"][:10] == (dt.date.fromisoformat(ngay_cuoi) + dt.timedelta(days=1)).isoformat()
    bg = cx.phan_tich_bang_gia(cx.dinh_dang_bang_gia(b["gia"], b["keo_luc"], b["nguon"]))
    assert bg["keo_luc"] == b["keo_luc"]


def test_bien_ban_co_du_sau_buoc_khong_co_ty_le_va_khong_phan_dat_truot(vong_QUA_dau):
    kq = {"thi_truong": {"luong": LUONG_TEST, "chi_so": 1, "kappa": KAPPA_2X, "so_ma": 60, "ma_dau": "GIA01",
                         "ma_cuoi": "GIA60"}, "vong": vong_QUA_dau, "su_that": None}
    dong = CV.bien_ban(kq)
    van = "\n".join(dong)
    for tieu_de in ("BƯỚC 1 — BỘ ĐỀ XUẤT", "BƯỚC 2 — KHAI", "BƯỚC 3 — XÁC NHẬN", "BƯỚC 4 — NÂNG CẤP",
                    "BƯỚC 5 — KIỂM TIẾN-VỀ-TRƯỚC", "BƯỚC 6 — SỰ THẬT"):
        assert tieu_de in van, tieu_de
    assert "%" not in van and "ĐẠT" not in van and "TRƯỢT" not in van and "tỷ lệ nào" in van
    assert "DX1 đọc phiên 401" in van and "HIỆU LỰC TỪ PHIÊN SAU: phiên 402" in van
    assert "huỷ vì nâng cấp (K vẫn đếm = 3): DX2, DX3" in van and "bỏ qua: --khong-oracle" in van
    assert van.count("← khai") == 3


def test_bien_ban_voi_bo_de_xuat_co_so_in_du_11_hang_va_chi_3_dong_danh_dau_khai():
    kq = {"thi_truong": {"luong": LUONG_TEST, "chi_so": 1, "kappa": KAPPA_2X, "so_ma": 60, "ma_dau": "A", "ma_cuoi": "B"},
          "vong": vong(1, KAPPA_2X), "su_that": None}
    hang = [d for d in CV.bien_ban(kq) if d.startswith("   ") and " Δ = " in d and "IC spec" in d]
    assert len(hang) == 11 and [d for d in hang if d.endswith("← khai")] == hang[:3]
    assert "mono_volume_score" in hang[0] and hang[0].startswith("    1. ")


def test_bien_ban_khong_nang_cap_noi_dung_va_thi_truong_chua_doc():
    kq = {"thi_truong": {"luong": LUONG_TEST, "chi_so": 1, "kappa": 0.0, "so_ma": 60, "ma_dau": "A", "ma_cuoi": "B"},
          "vong": vong(1, KAPPA_2X, T.TEN_SPEC_H, T.TEN_SPEC_Z, "mono_trend_score"), "su_that": None}
    van = "\n".join(CV.bien_ban(kq))
    assert "không có nâng cấp" in van and "không có gì để kiểm" in van and "(không)" in van
    assert "→ THUA" in van and "→ DANG CHAM" in van


def test_main_chay_that_ma_thoat_0_in_ra_va_ghi_dung_mot_file(monkeypatch, capsys, tmp_path):
    ghi = []
    monkeypatch.setattr(CV, "ghi_bien_ban", lambda dong: ghi.append(list(dong)))
    monkeypatch.chdir(tmp_path)
    assert CV.main(["--luong", "9001", "--chi-so", "1", "--muc", "2", "--khong-oracle", "--ghi"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("THỊ TRƯỜNG GIẢ — dòng hạt 9001, chỉ số 1") and "bỏ qua: --khong-oracle" in out
    assert len(ghi) == 1 and "\n".join(ghi[0]) in out and list(tmp_path.iterdir()) == []


def test_ghi_bien_ban_ghi_dung_file_duoc_chon_va_doc_lai_dung(tmp_path):
    p = tmp_path / "x.md"
    CV.ghi_bien_ban(["a", "b — c"], p)
    van = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert van == CV.noi_dung_tep(["a", "b — c"]) and "```text\na\nb — c\n```\n" in van
    assert CV.DUONG_BIEN_BAN == GOC / "docs" / "vong-hoc-thi-truong-gia-mau.md"


def test_doc_kappa_muc_khop_file_hieu_chuan_cua_lat_2_va_loi_khi_khong_co_muc(tmp_path):
    muc = json.loads((GOC / "docs" / "thi-truong-gia-hieu-chuan.json").read_text(encoding="utf-8"))["muc"]
    assert CV.doc_kappa_muc(2.0) == [m["kappa"] for m in muc if m["he_so"] == 2.0][0] == KAPPA_2X
    assert CV.doc_kappa_muc(0.0) == 0.0 and 0 < CV.doc_kappa_muc(0.5) < CV.doc_kappa_muc(1.0) < CV.doc_kappa_muc(2.0)
    with pytest.raises(ValueError, match="khong co dung mot muc"):
        CV.doc_kappa_muc(3.0)
    p = tmp_path / "h.json"
    p.write_text(json.dumps({"muc": [{"he_so": 2.0, "kappa": 0.1}, {"he_so": 2.0, "kappa": 0.2}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="khong co dung mot muc"):
        CV.doc_kappa_muc(2.0, p)


TEN_GHI = {"push", "write_all", "append_rows", "ghi_ke_hoach", "record_trade", "write_text", "write_bytes", "to_csv",
           "to_json", "dump", "to_parquet", "to_pickle", "savetxt", "save", "savez", "executemany", "commit", "open"}
CAM_TEN_THAT = {"SO_UNG_VIEN", "doc_so_ung_vien", "sheets_store", "keo_bang_gia", "doc_so_that", "PaperTradingJournal"}
CAM_CHUOI = ("ung-vien", "phuong-an-bong", "UV-", "backtest", "cache")


def test_G1_vong_khong_ghi_gi_va_dung_cu_chi_ghi_mot_file_bang_va_an_toan_ghi():
    assert not (_goi(_cay(DUONG_V)) & TEN_GHI), sorted(_goi(_cay(DUONG_V)) & TEN_GHI)
    cay = _cay(DUONG_TOOL)
    assert not (_goi(cay) & TEN_GHI), sorted(_goi(cay) & TEN_GHI)
    gi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "ghi"]
    assert len(gi) == 1 and gi[0] in list(ast.walk(_ham(cay)["ghi_bien_ban"]))
    duong = [s for s in _chuoi(cay) if (s.endswith(".md") or s.endswith(".json")) and " " not in s]
    assert sorted(duong) == ["thi-truong-gia-hieu-chuan.json", "vong-hoc-thi-truong-gia-mau.md"], duong


def test_G3_khong_thay_the_gioi_that_o_vong_va_dung_cu():
    for duong, nhap_duoc in ((DUONG_V, {"__future__", "copy", "datetime", "json", "numpy", "pandas", "cham_bong",
                                       "cham_xac_nhan", "experiment_tran_dac_trung", "thi_truong_gia"}),
                             (DUONG_TOOL, {"__future__", "argparse", "importlib", "json", "sys", "pathlib", "numpy",
                                           "cham_bong", "cham_xac_nhan", "thi_truong_gia", "vong_hoc_gia"})):
        cay = _cay(duong)
        sai = [s for s in _chuoi(cay) if any(c in s for c in CAM_CHUOI)]
        assert not sai, (duong.name, sai)
        assert not (_ten_dung(cay) & CAM_TEN_THAT), sorted(_ten_dung(cay) & CAM_TEN_THAT)
        nhap = set()
        for n in ast.walk(cay):
            if isinstance(n, ast.Import):
                nhap |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                nhap.add((n.module or "").split(".")[0])
        assert nhap <= nhap_duoc, (duong.name, sorted(nhap - nhap_duoc))


def test_G3_nap_vong_va_dung_cu_khong_keo_theo_gioi_that():
    ma = ("import sys, json, importlib.util; sys.path.insert(0, %r); import vong_hoc_gia; "
          "s = importlib.util.spec_from_file_location('cv', %r); m = importlib.util.module_from_spec(s); "
          "s.loader.exec_module(m); "
          "cam = ['sheets_store', 'keo_bang_gia', 'doc_so_that', 'gspread', 'google_sheets_sync', "
          "'paper_trading', 'paper_runner', 'run_daily', 'vnstock', 'vnstock_data']; "
          "print(json.dumps([x for x in cam if x in sys.modules]))" % (str(GOC), str(DUONG_TOOL)))
    r = subprocess.run([sys.executable, "-I", "-c", ma], capture_output=True, text=True, cwd=str(GOC),
                       timeout=180, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    assert json.loads(r.stdout.strip().splitlines()[-1]) == [], r.stdout


def test_G1_chay_that_mot_thi_truong_khong_de_lai_dau_vet_tren_dia(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    CV.chay_mot_thi_truong(LUONG_TEST, 3, KAPPA_2X, co_oracle=False, so_hoan_vi=50)
    assert list(tmp_path.iterdir()) == []


# ══ biên bản mẫu đã commit ═════════════════════════════════════════════════════════════════════════

def test_bien_ban_mau_da_commit_dung_dong_hat_thu_co_sau_buoc_va_khong_ty_le():
    p = CV.DUONG_BIEN_BAN
    assert p.is_file(), "chưa commit biên bản mẫu"
    van = p.read_text(encoding="utf-8")
    assert "```text\nTHỊ TRƯỜNG GIẢ — dòng hạt 9001, chỉ số 1, κ = 0.044587" in van
    for tieu_de in ("BƯỚC 1 — BỘ ĐỀ XUẤT", "BƯỚC 2 — KHAI", "BƯỚC 3 — XÁC NHẬN", "BƯỚC 4 — NÂNG CẤP",
                    "BƯỚC 5 — KIỂM TIẾN-VỀ-TRƯỚC", "BƯỚC 6 — SỰ THẬT"):
        assert tieu_de in van, tieu_de
    assert "%" not in van and "ĐẠT" not in van and "TRƯỢT" not in van
    assert "→ QUA" in van and "HIỆU LỰC TỪ PHIÊN SAU" in van


def test_bien_ban_mau_duoc_git_theo_doi_khong_bi_gitignore():
    """`*.txt` bị `.gitignore` của repo: một biên bản đặt tên ấy có mặt ở máy (test `is_file` xanh) và vắng ở CI."""
    r = subprocess.run(["git", "check-ignore", "-q", "--", str(CV.DUONG_BIEN_BAN.relative_to(GOC).as_posix())],
                       capture_output=True, text=True, cwd=str(GOC), timeout=60)
    assert r.returncode == 1, f"git check-ignore mã thoát {r.returncode}: biên bản mẫu bị bỏ qua hay git hỏng ({r.stderr})"
    r2 = subprocess.run(["git", "check-ignore", "-q", "--", "docs/khong-ai-nho-toi.txt"], capture_output=True,
                        text=True, cwd=str(GOC), timeout=60)
    assert r2.returncode == 0, "phép đo phải thấy được một file *.txt thật sự bị bỏ qua"


def test_bien_ban_mau_khop_lan_chay_lai_o_phan_cau_truc_khong_o_chu_so_cuoi():
    """Chạy lại MỘT thị trường mẫu (không oracle): cùng spec đã khai, cùng trạng thái, cùng phiên đọc và hiệu lực.
    Không so từng chữ số: `sum()` của Python 3.12+ cộng có bù, 3.11 thì không (mục 15 khoản 9)."""
    van = CV.DUONG_BIEN_BAN.read_text(encoding="utf-8")
    kq = CV.chay_mot_thi_truong(LUONG_TEST, 1, KAPPA_2X, co_oracle=False)
    v = kq["vong"]
    dong = [d for d in van.splitlines()]
    assert any(d.startswith("   khai 3 spec đầu có Δ > 0") and d.endswith(", ".join(v["de_xuat"]["da_chon"]))
               for d in dong)
    assert any(d == "   trạng thái cuối: " + ", ".join(f"{m} = {s}" for m, s in v["trang_thai"].items())
               for d in dong)
    ban = v["so_phien_ban"]["phien_ban"][1]
    assert any(f"đọc ở phiên {ban['phien_doc']}, HIỆU LỰC TỪ PHIÊN SAU: phiên {ban['hieu_luc_tu_phien']} "
               f"({v['hieu_luc_ngay']})" in d for d in dong)
