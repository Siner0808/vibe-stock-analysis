"""Cửa và máy đọc kết cục của ĐO 38 (BƯỚC 303): `tools/chay_chinh_thuc_thi_truong_gia.py` tổng quát hoá cho HAI ĐO.

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 21 (đặc tả sửa C4), `vibe_logs_c4sua/DAC-TA-SUA-C4.md` mục 5 ("Tổng quát hoá cửa"),
và `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 38 (bảng đã ký). Lượt chạy chính thức là BƯỚC 304; BƯỚC 303 chỉ KÝ và dựng cửa.

KHÔNG MỘT THỊ TRƯỜNG nào của dòng hạt 6–10 được sinh ở file này, cũng không ở nơi nào khác của BƯỚC 303: fixture tự động
`_khong_sinh_dong_6_den_10` bọc mọi hàm sinh/oracle của bộ sinh và NỔ nếu đối số `luong` thuộc 6…10. Các phép thử chạy thật
dùng dòng 9001 (dòng thử) hoặc bản giả.

Bốn nhóm:

* CẤU HÌNH — `DO_THEO_LUONG`, hai bản ghi `KeHoachDo`, `DO_37` là mặc định, hai ĐO không đè file kết quả của nhau;
* CỬA ĐO 38 — dòng 6–9 chỉ mở khi ĐO 38 đã ở `origin/main` và nêu nguyên văn lệnh + dòng kế hoạch + MỘT câu số đã ký khớp bản ghi
  hiệu chuẩn; dòng 1 · 5 · 10 luôn chặn; cửa ĐO 37 không đổi;
* ĐỌC KẾT CỤC — A0 và dải PT đọc từ BẢN GHI (không gõ tay), M1 ≤ 50/1.000, M2 sd z′ gộp ∈ [0,8 ; 1,25], hai bên biên;
* NỘI DUNG ĐO 38 trong `docs/TIEU-CHI-DOC-TRUOC.md` khớp dụng cụ.
"""
import ast
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tests"))
sys.path.append(str(GOC / "tools"))

import cham_xac_nhan as cx  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402
import vong_hoc_gia as V  # noqa: E402
# Dùng lại bản nạp dụng cụ và các hàm dựng bản ghi giả của file ĐO 37 (cùng MỘT thể hiện của module, không nạp hai lần).
from test_chay_chinh_thuc_thi_truong_gia import (  # noqa: E402
    CT, DUONG_TOOL, G_PHAY, HIEU_CHUAN, NG, _chuoi, _git_gia, _o1, _o2, _oracle, _tt)

LUONG_TEST = 9001
TIEU_CHI = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
DUONG_HC38 = GOC / "docs" / "thi-truong-gia-hieu-chuan-do38.json"
TEN = {"G": T.TEN_SPEC_G, "Z": T.TEN_SPEC_Z, "H": T.TEN_SPEC_H}


# ══ CÁCH LY ═══════════════════════════════════════════════════════════════════════════════════════════════

def _bao_ve(ham, vi_tri_luong=0):
    def vo(*a, **k):
        luong = k["luong"] if "luong" in k else a[vi_tri_luong]
        if isinstance(luong, (int, np.integer)) and not isinstance(luong, bool) and 6 <= int(luong) <= 10:
            raise AssertionError(f"MOT THI TRUONG CUA DONG HAT {luong} DA DUOC SINH trong test (BUOC 303 cam)")
        return ham(*a, **k)
    return vo


@pytest.fixture(autouse=True)
def _khong_sinh_dong_6_den_10(monkeypatch):
    for mod, ten in ((T, "sinh_thi_truong"), (T, "sinh_null"), (T, "tinh_su_that"), (T, "sinh_thi_truong_m"), (T, "tinh_su_that_m"),
                     (T, "ic_da_ghi_m"), (G, "sinh_thi_truong_2")):
        monkeypatch.setattr(mod, ten, _bao_ve(getattr(mod, ten)))
    for ten in ("_sinh_loi",):
        # `_sinh_loi(rng, ...)` không nhận luong: bọc ở tầng `default_rng` là quá rộng; các cửa trên đã phủ đường vào
        pass


@pytest.fixture(autouse=True)
def _khong_doc_ket_qua_do38_that(monkeypatch):
    """Phép thử mô tả trạng thái TRƯỚC lượt chạy: không đọc file kết quả chính thức (cả hai ĐO) THẬT (lỗi 208)."""
    goc = CT.doc_ket_qua_hien_co
    cam = {CT.DO_37.duong_ket_qua.resolve(), CT.DO_38.duong_ket_qua.resolve()}

    def doc(duong=None):
        if duong is None or Path(duong).resolve() in cam:
            return None
        return goc(duong)
    monkeypatch.setattr(CT, "doc_ket_qua_hien_co", doc)


# ══ BẢN GHI HIỆU CHUẨN GIẢ (số CỐ Ý khác số thật để bắt hằng số gõ tay) ═══════════════════════════════════

def _hc(a0=307, lo=31, hi=62, kd=0.018, **sua):
    """Bản ghi `docs/thi-truong-gia-hieu-chuan-do38.json` giả, đủ bốn việc XONG, không báo DỪNG."""
    b = {"buoc": 301, "do": "ĐO 38", "cac_viec": {
        "kd": {"trang_thai": "XONG", "ket_qua": {"kappa_d": kd, "that_bai": False, "ly_do": [], "dung": False, "ly_do_dung": []}},
        "a0": {"trang_thai": "XONG", "ket_qua": {"N": 20000, "k_G": 5263, "p_hat": 0.26315, "nguong": a0, "dung": False, "ly_do_dung": []}},
        "t1": {"trang_thai": "XONG", "ket_qua": {"n": 1000, "dung": False, "ly_do_dung": []}},
        "pt": {"trang_thai": "XONG", "ket_qua": {"n_cal": 200, "k": 92, "dai_99": [lo, hi], "dung": False, "ly_do_dung": []}}}}
    for k, v in sua.items():
        b["cac_viec"][k.split("__")[0]][k.split("__")[1]] = v
    return b


def _hc_doc(**kw):
    hc, loi = CT.kiem_hieu_chuan_do38(_hc(**kw))
    assert loi == [], loi
    return hc


# ══ CẤU HÌNH ══════════════════════════════════════════════════════════════════════════════════════════════

def test_DO_THEO_LUONG_va_hai_ban_ghi_cau_hinh():
    assert CT.DO_THEO_LUONG == {2: 37, 3: 37, 4: 37, 6: 38, 7: 38, 8: 38, 9: 38}
    assert CT.CAU_HINH == {37: CT.DO_37, 38: CT.DO_38}
    assert CT.cau_hinh_do() is CT.DO_37 and CT.cau_hinh_do(None, 9001) is CT.DO_37        # mặc định ĐO 37 (cả dòng thử)
    assert CT.cau_hinh_do(None, 6) is CT.DO_38 and CT.cau_hinh_do(37, 6) is CT.DO_37 and CT.cau_hinh_do(38, 2) is CT.DO_38
    assert CT.DO_37.so_do == 37 and CT.DO_38.so_do == 38
    assert CT.DO_37.luong == CT.LUONG_CHINH_THUC == (2, 3, 4) and CT.DO_37.ke_hoach is CT.KE_HOACH
    assert CT.DO_38.luong == (6, 7, 8, 9)
    assert set(CT.DO_38.luong_chan) == {1, 5, 10} and 5 in CT.DO_37.luong_chan
    assert CT.DO_37.duong_ket_qua == CT.DUONG_KET_QUA
    assert CT.DO_38.duong_ket_qua == GOC / "docs" / "thi-truong-gia-ket-qua-do38.json" and CT.DO_38.duong_ket_qua != CT.DO_37.duong_ket_qua
    with pytest.raises(ValueError):
        CT.cau_hinh_do(39)
    for luong, do in CT.DO_THEO_LUONG.items():
        assert luong in CT.CAU_HINH[do].luong and luong in CT.CAU_HINH[do].ke_hoach, luong
    assert not (set(CT.DO_37.luong) & set(CT.DO_38.luong)) and not (set(CT.DO_38.luong) & set(CT.DO_38.luong_chan))
    assert not ({1, 5, 10} & set(CT.DO_THEO_LUONG))


def test_ke_hoach_do38_khop_dac_ta_muc_5_va_21_5_chi_so_roi_nhau_P2_ca_200():
    kh = CT.DO_38.ke_hoach
    assert [(t, m, d, s) for t, m, d, s in kh[6]["o"]] == [("0.5x", 0.5, 1001, 400), ("1x", 1.0, 2001, 400), ("2x", 2.0, 3001, 400)] and kh[6]["tang"] == 1
    assert [(t, m, d, s) for t, m, d, s in kh[7]["o"]] == [("NULL", 0.0, 1, 1000)] and kh[7]["tang"] == 1
    assert [(t, m, d, s) for t, m, d, s in kh[8]["o"]] == [("NULL", 0.0, 1, 100), ("2x", 2.0, 1001, 100)] and kh[8]["tang"] == 2
    assert [(t, m, d, s) for t, m, d, s in kh[9]["o"]] == [(CT.TEN_O_NULL_M, 0.0, 1, 1000)] and kh[9]["tang"] == 1
    for l, k in kh.items():
        chi_so = [c for _, _, dau, so in k["o"] for c in range(dau, dau + so)]
        assert len(chi_so) == len(set(chi_so)) and min(chi_so) >= 1, l
    assert all(muc in [m["he_so"] for m in HIEU_CHUAN["muc"]] for l in (6, 7, 8) for _, muc, _, _ in kh[l]["o"])
    assert CT.DO_38.luu_moi_cua(8) == 12 and CT.DO_38.luu_moi_cua(6) == 25 and CT.DO_38.luu_moi_cua(9) == 25
    assert [CT.DO_37.luu_moi_cua(l) for l in (2, 3, 4)] == [25, 25, 25]
    assert CT.DO_38.luong_tong_hop == (6, 7, 8, 9) and CT.DO_37.luong_tong_hop == (2, 3, 4)


def test_lenh_chuan_va_dong_ke_hoach_cua_do38_sinh_tu_ke_hoach_va_do37_khong_doi():
    for l in (2, 3, 4):
        assert CT.lenh_chuan(l) == f"tools/chay_chinh_thuc_thi_truong_gia.py --luong {l}" == CT.lenh_chuan(l, 37)
    assert CT.lenh_ket_cuc() == "tools/chay_chinh_thuc_thi_truong_gia.py --ket-cuc"
    for l in (6, 7, 8, 9):
        assert CT.lenh_chuan(l) == f"tools/chay_chinh_thuc_thi_truong_gia.py --do 38 --luong {l}" == CT.lenh_chuan(l, 38)
        d = CT.dong_ke_hoach(l)
        for ten, muc, dau, so in CT.DO_38.ke_hoach[l]["o"]:
            assert f"ô {ten} (mức {muc:g}× MDE80) chỉ số {dau}–{dau + so - 1}" in d
        assert d.startswith(f"dòng {l} · Tầng {CT.DO_38.ke_hoach[l]['tang']}")
    assert CT.lenh_ket_cuc(38) == "tools/chay_chinh_thuc_thi_truong_gia.py --ket-cuc --do 38"
    assert CT.dong_ke_hoach(2) == CT.dong_ke_hoach(2, 37) and "dòng 2 · Tầng 1" in CT.dong_ke_hoach(2)


# ══ BẢN GHI HIỆU CHUẨN: đọc và câu đã ký ══════════════════════════════════════════════════════════════════

def test_kiem_hieu_chuan_do38_doc_dung_ba_so_va_bat_tung_loi():
    hc = _hc_doc(a0=300, lo=20, hi=40, kd=0.02)
    assert hc["nguong_A0"] == 300 and hc["dai_pt"] == (20, 40) and hc["kappa_d"] == 0.02
    assert CT.cau_da_ky_do38(hc) == "A0 ≤ 300 · PT dải 99% [20 ; 40] · κ_d = 0,02"
    assert CT.cau_da_ky_do38(_hc_doc()) == "A0 ≤ 307 · PT dải 99% [31 ; 62] · κ_d = 0,018"
    tt = {"kd": "XONG", "a0": "XONG", "t1": "XONG", "pt": "XONG"}
    for viec in tt:                                              # mỗi việc phải XONG
        loi = CT.kiem_hieu_chuan_do38(_hc(**{f"{viec}__trang_thai": "DANG CHAY"}))[1]
        assert loi and viec in " ".join(loi), viec
    for viec in tt:                                              # luật DỪNG báo ở bất kỳ việc nào → từ chối
        loi = CT.kiem_hieu_chuan_do38(_hc(**{f"{viec}__ket_qua": {**_hc()["cac_viec"][viec]["ket_qua"], "dung": True}}))[1]
        assert loi and viec in " ".join(loi), viec
    assert CT.kiem_hieu_chuan_do38(_hc(kd__ket_qua={"kappa_d": 0.018, "that_bai": True, "dung": False}))[1]
    assert CT.kiem_hieu_chuan_do38({"cac_viec": {}})[1] and CT.kiem_hieu_chuan_do38(None)[1]
    bi_mat = _hc()
    del bi_mat["cac_viec"]["pt"]["ket_qua"]["dai_99"]
    assert CT.kiem_hieu_chuan_do38(bi_mat)[1]
    assert CT.kiem_hieu_chuan_do38(_hc(a0=307.5))[1]              # ngưỡng không nguyên → lỗi, không làm tròn lặng lẽ


def test_ban_ghi_hieu_chuan_THAT_neu_co_thi_doc_duoc_va_cho_307_31_62_0_018():
    """Số rút từ bản ghi THẬT của BƯỚC 301 (tái lập từng số: `docs/STATE.md` BƯỚC 303)."""
    ban = json.loads(DUONG_HC38.read_text(encoding="utf-8"))
    hc, loi = CT.kiem_hieu_chuan_do38(ban)
    assert loi == [] and hc is not None
    assert (hc["nguong_A0"], tuple(hc["dai_pt"]), hc["kappa_d"]) == (307, (31, 62), 0.018)
    assert CT.doc_hieu_chuan_do38(DUONG_HC38) == hc


# ══ CỬA ĐO 38 ═════════════════════════════════════════════════════════════════════════════════════════════

def _than_do(so, luong, hc=None, de_so=None, tieu_de=True):
    """Thân một mục ĐO giả. `de_so` = số ĐO mà lệnh/kế hoạch được sinh theo (khác `so` để dựng văn bản ĐO 37 NÊU NHẦM dòng của ĐO 38)."""
    de_so = so if de_so is None else de_so
    t = f"## ĐO {so} — ký\n\n" if tieu_de else ""
    for l in luong:
        t += f"```\n./.venv/Scripts/python.exe -X utf8 {CT.lenh_chuan(l, de_so).replace(' --', chr(10) + '  --', 1)} --so-tien-trinh 12\n```\n"
        t += CT.dong_ke_hoach(l, de_so) + "\n\n"
    if hc is not None:
        t += "**Số đã ký từ bản ghi hiệu chuẩn:** " + CT.cau_da_ky_do38(hc) + "\n\n"
    return t


def _van_ban(*, do37=(2, 3, 4), do37_gia_6_9=True, do38=(6, 7, 8, 9), hc=None, cau=True):
    """`docs/TIEU-CHI-DOC-TRUOC.md` giả: ĐO 36, ĐO 37 (kể cả dòng 6–9 bị nêu NHẦM ở ĐO 37 để bắt `DO_THEO_LUONG` sai) và ĐO 38."""
    hc = _hc_doc() if hc is None else hc
    v = "# T\n\n## ĐO 36 — cũ\n\nthân cũ\n\n"
    if do37 is not None:
        v += _than_do(37, tuple(do37))
        if do37_gia_6_9:
            v += _than_do(37, (6, 7, 8, 9), de_so=38, tieu_de=False)
    if do38 is not None:
        v += _than_do(38, do38, hc if cau else None)
    return v


KIEM_CONG_THAT = CT.kiem_cong      # bắt trước mọi monkeypatch


def _cong(luong, van=None, **kw):
    van = _van_ban() if van is None else van
    return KIEM_CONG_THAT(luong, git=kw.pop("git", _git_gia(van)), ket_qua_hien_co=kw.pop("ket_qua_hien_co", None),
                        van_ban_cay=kw.pop("van_ban_cay", van), do=kw.pop("do", None), ban_ghi_hc=kw.pop("ban_ghi_hc", _hc()), **kw)


def test_cua_do38_cho_qua_dong_6_7_8_9_khi_ky_o_origin_main_va_ban_ghi_khop():
    for l in (6, 7, 8, 9):
        phep = _cong(l)
        assert isinstance(phep, CT.PhepChay) and phep.luong == l and phep.hop_le()
        CT.kiem_luong_chinh_thuc(l, phep)
        assert _cong(l, do=38).luong == l                               # nêu `do` tường minh cũng được
    # cửa ĐO 37 không đổi: dòng 2 vẫn qua với ĐO 37, và KHÔNG cần ĐO 38
    van = _van_ban(do38=None)
    assert CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van).luong == 2


def test_cua_do38_TU_CHOI_khi_origin_main_chua_co_do38_du_ĐO_37_nhac_nham_dong_6_9():
    """Bắt `DO_THEO_LUONG` trỏ sai ĐO: ĐO 37 trong văn bản này nêu cả lệnh và dòng kế hoạch của dòng 6–9, nên một cửa trỏ dòng 6 vào ĐO 37 sẽ cho qua."""
    van = _van_ban(do38=None)
    for l in (6, 7, 8, 9):
        with pytest.raises(CT.CongTu) as e:
            _cong(l, van)
        assert any("khong co muc '## ĐO 38 —'" in s for s in e.value.ly_do), e.value.ly_do
    van2 = _van_ban(do38=None, do37_gia_6_9=False)
    with pytest.raises(CT.CongTu):
        _cong(6, van2)
    van3 = _van_ban(do37=None)                                         # ĐO 38 có nhưng ĐO 37 vắng: dòng 2 từ chối
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(2, git=_git_gia(van3), ket_qua_hien_co=None, van_ban_cay=van3)
    assert any("khong co muc '## ĐO 37 —'" in s for s in e.value.ly_do)


def test_cua_do38_TU_CHOI_khi_ĐO_38_khong_neu_lenh_hay_dong_ke_hoach_hay_cau_da_ky():
    with pytest.raises(CT.CongTu) as e:
        van = _van_ban(do38=(7, 8, 9))
        _cong(6, van)
    assert len(e.value.ly_do) == 2                                     # thiếu lệnh VÀ dòng kế hoạch của dòng 6
    van = _van_ban(cau=False)
    with pytest.raises(CT.CongTu) as e:
        _cong(6, van)
    assert len(e.value.ly_do) == 1 and "cau so da ky" in e.value.ly_do[0]


@pytest.mark.parametrize("sua,khoa", [
    (dict(a0=317), "cau so da ky"), (dict(a0=306), "cau so da ky"), (dict(lo=30), "cau so da ky"), (dict(hi=63), "cau so da ky"),
    (dict(kd=0.02), "cau so da ky")])
def test_cua_do38_TU_CHOI_khi_ban_ghi_hieu_chuan_khac_so_da_ky_trong_ĐO_38(sua, khoa):
    """Văn bản ĐO 38 ký A0 ≤ 307 · [31 ; 62] · κ_d = 0,018; bản ghi (cây làm việc) mang số khác → KHÔNG chạy (không tính lại mà chạy tiếp)."""
    van = _van_ban()
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(6, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van, ban_ghi_hc=_hc(**sua))
    assert any(khoa in s for s in e.value.ly_do), e.value.ly_do


def test_cua_do38_TU_CHOI_khi_ban_ghi_hieu_chuan_vang_hay_do_hay_bao_DUNG():
    van = _van_ban()
    for ten, ban in (("vang", None), ("do", _hc(a0__trang_thai="DANG CHAY")), ("dung", _hc(pt__ket_qua={**_hc()["cac_viec"]["pt"]["ket_qua"], "dung": True}))):
        with pytest.raises(CT.CongTu) as e:
            CT.kiem_cong(6, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van, ban_ghi_hc=ban if ban is not None else {})
        assert any("hieu chuan" in s for s in e.value.ly_do), (ten, e.value.ly_do)


def test_cua_do38_khong_doc_ban_ghi_thuc_khi_khong_tiem_va_doc_duong_ban_ghi_cua_ĐO_38(monkeypatch, tmp_path):
    """Không tiêm `ban_ghi_hc` thì cửa đọc `DUONG_HC38` ở cây làm việc: đổi đường sang file giả có số khác → từ chối; số khớp → qua."""
    van = _van_ban()
    f = tmp_path / "hc.json"
    monkeypatch.setattr(CT, "DUONG_HC38", f)
    f.write_text(json.dumps(_hc(a0=317)), encoding="utf-8")
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(7, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van)
    assert any("cau so da ky" in s for s in e.value.ly_do)
    f.write_text(json.dumps(_hc()), encoding="utf-8")
    assert CT.kiem_cong(7, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van).luong == 7
    f.unlink()
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(7, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van)
    assert any("hieu chuan" in s for s in e.value.ly_do)


def test_cua_do38_TU_CHOI_khi_ĐO_38_o_cay_khac_origin_main_hay_file_ghim_lech_hay_khong_to_tien():
    van = _van_ban()
    with pytest.raises(CT.CongTu) as e:
        _cong(6, van, van_ban_cay=van.replace("## ĐO 38 — ký", "## ĐO 38 — ký (sửa)"))
    assert any("ĐO 38 o cay lam viec khac origin/main" in s for s in e.value.ly_do)
    _cong(6, van, van_ban_cay=van.replace("\n\n", "\n\n\n"))          # đổi khoảng trắng không phải sửa tiêu chí
    ban = "docs/thi-truong-gia-hieu-chuan-do38.json"
    assert ban in CT.DO_38.file_ghim and set(CT.FILE_GHIM) <= set(CT.DO_38.file_ghim) and CT.TEN_DUNG_CU in CT.DO_38.file_ghim
    for ten, git, khoa in (("fetch", _git_gia(van, fetch=1), "git fetch"), ("to tien", _git_gia(van, ancestor=1), "to tien"),
                           ("ghim", _git_gia(van, diff=lambda f: 1 if f == ban else 0), ban)):
        with pytest.raises(CT.CongTu) as e:
            _cong(8, van, git=git)
        assert any(khoa in s for s in e.value.ly_do), (ten, e.value.ly_do)


def test_cua_do38_in_HET_cac_dieu_thieu():
    git = _git_gia(None, fetch=1, ancestor=1, diff=1)
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(9, git=git, ket_qua_hien_co=None, van_ban_cay="", ban_ghi_hc={})
    assert len(e.value.ly_do) >= 2 + len(CT.DO_38.file_ghim) + 1


def test_cua_do38_mot_lan_XONG_chan_DANG_DO_can_tiep_tuc_va_hai_ĐO_khong_chan_nhau(monkeypatch):
    van = _van_ban()
    xong, do = {"cac_luong": {"6": {"trang_thai": "XONG"}}}, {"cac_luong": {"6": {"trang_thai": "DANG CHAY"}}}
    for _ in range(2):
        with pytest.raises(CT.CongTu) as e:
            _cong(6, van, ket_qua_hien_co=xong, tiep_tuc=True)
        assert any("DA chay xong" in s for s in e.value.ly_do)
    with pytest.raises(CT.CongTu) as e:
        _cong(6, van, ket_qua_hien_co=do)
    assert any("--tiep-tuc" in s for s in e.value.ly_do)
    assert _cong(6, van, ket_qua_hien_co=do, tiep_tuc=True).hop_le()
    assert _cong(7, van, ket_qua_hien_co=xong).hop_le()                # dòng 7 chưa có bản ghi
    # không tiêm bản ghi → cửa đọc ĐÚNG file của ĐO của dòng đó, không đọc file của ĐO kia
    da_doc = []
    monkeypatch.setattr(CT, "doc_ket_qua_hien_co", lambda duong=None: da_doc.append(None if duong is None else Path(duong)) or None)
    _cong(6, van)
    CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van)
    assert da_doc == [CT.DO_38.duong_ket_qua, None]                    # ĐO 37: đường mặc định (hàm tự biết file của mình)


@pytest.mark.parametrize("luong", [1, 5, 10])
def test_cua_chan_vinh_vien_dong_1_5_10_du_ĐO_38_nhac_den_chung_va_cua_nao(luong):
    van = _van_ban() + (f"\n### thêm\n./.venv/Scripts/python.exe -X utf8 {CT.lenh_chuan(luong, 38)} --so-tien-trinh 12\n"
                        f"dòng {luong} · Tầng 1: ô NULL (mức 0× MDE80) chỉ số 1–10\n")   # ĐO 38 (giả) nêu cả lệnh và kế hoạch của dòng bị chặn
    with pytest.raises(CT.CongTu):
        CT.kiem_cong(luong, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van, ban_ghi_hc=_hc())
    with pytest.raises(CT.CongTu):
        CT.kiem_cong(luong, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van, do=38, ban_ghi_hc=_hc())
    with pytest.raises(CT.CongTu):
        CT.kiem_cong(luong, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van, do=37, ban_ghi_hc=_hc())
    phep = _cong(6)
    with pytest.raises(ValueError, match="bi chan vinh vien"):
        CT.kiem_luong_chinh_thuc(luong, phep)                          # nổ ngay cả khi có giấy phép hợp lệ của dòng khác
    gia = CT.PhepChay(luong, "x", "y", "z", CT._tem(luong, "x", "y", "z"))   # tem ĐÚNG nhưng dòng bị chặn
    assert not gia.hop_le()
    with pytest.raises(ValueError):
        CT.kiem_luong_chinh_thuc(luong, gia)


def test_kiem_luong_chinh_thuc_dong_6_9_nổ_khong_giay_phep_sai_dong_hay_gia_mao_va_dong_la_van_no():
    ph = {l: _cong(l) for l in (6, 7, 8, 9)}
    for l in (6, 7, 8, 9):
        with pytest.raises(CT.CongTu):
            CT.kiem_luong_chinh_thuc(l)
        with pytest.raises(CT.CongTu):
            CT.kiem_luong_chinh_thuc(l, ph[6 if l != 6 else 7])        # phép của dòng khác
        with pytest.raises(CT.CongTu):
            CT.kiem_luong_chinh_thuc(l, CT.PhepChay(l, ph[l].sha_do, ph[l].head, ph[l].goc_main, "0" * 64))
    for l in (0, -2, 11, 9000, "6", 6.0, None, True, False, 12):
        with pytest.raises((ValueError, CT.CongTu)):
            CT.kiem_luong_chinh_thuc(l, ph[6])
    CT.kiem_luong_chinh_thuc(np.int64(9), ph[9])
    CT.kiem_luong_chinh_thuc(9001)


def test_main_do_38_BI_TU_CHOI_o_trang_thai_cua_nhanh_nay_va_KHONG_sinh_gi(monkeypatch, capsys, tmp_path):
    def no(*a, **k):
        raise AssertionError("MOT THI TRUONG DA DUOC SINH")
    for mod, ten in ((T, "sinh_thi_truong"), (T, "sinh_thi_truong_m"), (T, "tinh_su_that"), (T, "tinh_su_that_m"), (G, "sinh_thi_truong_2"),
                     (V, "chay_vong"), (cx, "cham"), (CT, "ghi_ket_qua")):
        monkeypatch.setattr(mod, ten, no)
    van = "# T\n\n## ĐO 37 — cũ\n\nthân\n"
    monkeypatch.setattr(CT, "git_that", _git_gia(van))
    for l in ("6", "7", "8", "9"):
        assert CT.main(["--do", "38", "--luong", l, "--so-tien-trinh", "12"]) == 3
        err = capsys.readouterr().err
        assert "CỬA TỪ CHỐI" in err and "ĐO 38" in err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("tham", [["--luong", "6"], ["--do", "37", "--luong", "6"], ["--do", "38", "--luong", "2"], ["--do", "38", "--luong", "5"],
                                  ["--do", "38", "--luong", "10"], ["--do", "38", "--luong", "1"], ["--do", "38", "--luong", "9000"],
                                  ["--do", "37", "--luong", "9"]])
def test_main_tu_choi_dong_khong_thuoc_do_da_chon_ma_thoat_2_va_khong_sinh_gi(tham, monkeypatch):
    def no(*a, **k):
        raise AssertionError("MOT THI TRUONG DA DUOC SINH")
    for mod, ten in ((T, "sinh_thi_truong"), (T, "sinh_thi_truong_m"), (G, "sinh_thi_truong_2"), (CT, "ghi_ket_qua"), (CT, "kiem_cong")):
        monkeypatch.setattr(mod, ten, no)
    assert CT.main(tham) == 2


def test_main_do_la_doi_so_hop_le_chi_37_hay_38_va_mac_dinh_37():
    cay = ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))
    ar = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"
          and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "--do"]
    assert len(ar) == 1
    kw = {k.arg: k.value for k in ar[0].keywords}
    assert ast.literal_eval(kw["default"]) == 37 and kw["type"].id == "int"
    with pytest.raises(SystemExit):
        CT.main(["--ket-cuc", "--do", "39"])


def test_main_ket_cuc_doc_dung_file_cua_tung_ĐO_va_mac_dinh_la_ĐO_37(monkeypatch, capsys):
    da_doc = []
    monkeypatch.setattr(CT, "doc_ket_qua_hien_co", lambda duong=None: da_doc.append(duong) or None)
    assert CT.main(["--ket-cuc"]) == 2
    assert CT.main(["--ket-cuc", "--do", "37"]) == 2
    assert CT.main(["--ket-cuc", "--do", "38"]) == 2
    assert da_doc[0] is None and da_doc[1] is None                      # ĐO 37: đường mặc định
    assert Path(da_doc[2]) == CT.DO_38.duong_ket_qua


def test_main_ket_cuc_do38_thieu_ban_ghi_hieu_chuan_hay_dang_dong_hat_tra_2(monkeypatch):
    monkeypatch.setattr(CT, "doc_ket_qua_hien_co", lambda duong=None: {"cac_luong": {}})
    monkeypatch.setattr(CT, "doc_hieu_chuan_do38", lambda duong=None: None)
    assert CT.main(["--ket-cuc", "--do", "38"]) == 2


def test_main_do38_chay_luong_nhan_dung_cau_hinh_luu_moi_ra_va_P2_ca_200(monkeypatch):
    goi = []
    monkeypatch.setattr(CT, "kiem_cong", lambda luong, **k: goi.append(("cong", luong, k)) or _cong(luong))
    monkeypatch.setattr(CT, "chay_luong", lambda luong, phep, so_tien_trinh=1, tiep_tuc=False, luu_moi=25, ra=None, ke_hoach=None, so_hoan_vi=0,
                        co_p2=True, chay_p4_fn=None, lenh_text="", in_tien_do=True, ghi_fn=None, do=None:
                        goi.append(("chay", luong, dict(luu_moi=luu_moi, ra=ra, ke_hoach=ke_hoach, co_p2=co_p2, do=do, lenh=lenh_text, tt=so_tien_trinh))) or {})
    for l, luu in ((6, 25), (7, 25), (8, 12), (9, 25)):
        goi.clear()
        assert CT.main(["--do", "38", "--luong", str(l), "--so-tien-trinh", "12"]) == 0
        assert goi[0][2]["do"] == 38
        chay = goi[1][2]
        assert chay["luu_moi"] == luu and chay["ra"] == CT.DO_38.duong_ket_qua and chay["co_p2"] is True and chay["do"] in (38, CT.DO_38)
        assert chay["lenh"] == f"./.venv/Scripts/python.exe -X utf8 {CT.lenh_chuan(l, 38)} --so-tien-trinh 12"
    goi.clear()
    assert CT.main(["--luong", "3", "--so-tien-trinh", "12"]) == 0
    assert goi[1][2]["ra"] == CT.DO_37.duong_ket_qua and goi[1][2]["luu_moi"] == 25
    assert goi[1][2]["lenh"] == f"./.venv/Scripts/python.exe -X utf8 {CT.lenh_chuan(3)} --so-tien-trinh 12"


def test_main_dong_thu_do38_khong_duoc_ghi_ra_file_chinh_thuc_cua_hai_ĐO(monkeypatch):
    def no(*a, **k):
        raise AssertionError("MOT THI TRUONG DA DUOC SINH")
    monkeypatch.setattr(CT, "chay_luong", no)
    for chinh in (CT.DO_37.duong_ket_qua, CT.DO_38.duong_ket_qua):
        for do in ("37", "38"):
            with pytest.raises(SystemExit):
                CT.main(["--do", do, "--luong", "9001", "--tang", "1", "--ra", str(chinh)])


# ══ ĐỌC KẾT CỤC ĐO 38 ═════════════════════════════════════════════════════════════════════════════════════

def _z_pair(sd_muc_tieu, n_cap, sigma=0.01):
    """`n_cap` giá trị z′ tất định, trung bình 0, độ lệch chuẩn (ddof=1) đúng `sd_muc_tieu`: ±a luân phiên (n_cap chẵn)."""
    a = sd_muc_tieu * math.sqrt((n_cap - 1) / n_cap)
    return [a if i % 2 == 0 else -a for i in range(n_cap)]


def _o_nho(n=1000, sd=1.0, xac_nhan_nham=0, loai=0, nang=0, bao_dong=0, delta_that=(-0.02, 0.003, -0.002)):
    """`n` thị trường NULL-M: z′ của (thị trường, ứng viên) lấy tuần tự từ `_z_pair`; `xac_nhan_nham` thị trường có G `QUA` mà ΔIC_true ≤ 0."""
    zs = _z_pair(sd, 3 * n)
    sigma = 0.01
    ra = []
    for i in range(n):
        bo_ba, spec = {}, {}
        for j, k in enumerate(("G", "Z", "H")):
            zp = zs[3 * i + j]
            dt = delta_that[j]
            c = _tt(qua=False)
            c.update({"delta": dt + zp * sigma, "z": zp, "sd_null": sigma})
            bo_ba[k] = c
            spec[TEN[k]] = [dt, 0.004]
        ra.append({"chi_so": i + 1, "dg": "x", "nguong": NG, "bo_ba": bo_ba, "oracle": {"top_f": T.TEN_SPEC_G, "spec": spec,
                                                                                      "ic_da_ghi": 0.1}, "chuoi": _chuoi(nang=i < nang)})
    for i in range(xac_nhan_nham):                              # G `QUA` mà ΔIC_true(G) = −0,02 ≤ 0
        ra[i]["bo_ba"]["G"]["tt"] = "QUA"
    for i in range(loai):                                       # σ = 0 → cặp bị loại khỏi phép gộp
        ra[-1 - i]["bo_ba"]["Z"]["sd_null"] = 0.0
    for i in range(bao_dong):
        ra[-1 - i]["bo_ba"]["H"]["p"] = 1e-4
    return ra


def _ket_dat38(**ghi_de):
    """Bản ghi bốn dòng hạt 6–9 thoả MỌI tiêu chí một đơn vị trong ngưỡng (A0 ≤ 300, dải PT [20 ; 40]: SỐ KHÁC số thật để bắt hằng số gõ tay)."""
    muc = {m["he_so"]: m["muc_tieu_delta_ic"] for m in HIEU_CHUAN["muc"]}
    n = {**CT.NGUONG, "A0": 300}
    lo, hi = HIEU_CHUAN["kiem_1x_trong_dai_99"]["dai_99_quanh_80"]
    o = {
        "x05": _o1(400, g_delta=muc[0.5]), "x1": _o1(400, g_qua=lo + 1, g_delta=muc[1.0]),
        "x2": _o1(400, tim_ra=n["A"], g_qua=n["B2"], z_alarm=n["B3"], g_delta=muc[2.0], nang=300),
        "n7": _o1(1000, g_khai=n["A0"], nang=n["C3"], g_delta="luan_phien"),
        "n8": _o2(100, null_alarm=n["PT_NULL"]), "x8": _o2(100, g_qua=20, p3=n["P3"]),
        "m9": _o_nho(xac_nhan_nham=50),     # M1 = 50 LITERAL (ĐO 38 ký ≤ 50/1.000): không đọc từ hằng số của dụng cụ
    }
    for i in range(n["B1"]):
        o["n7"][-1 - i]["bo_ba"]["Z"] = _tt(p_alarm=True)
    o.update(ghi_de)

    def cell(l):
        return {"thi_truong": o[l], "tai_lap": "KHOP"}
    return {"cac_luong": {
        "6": {"trang_thai": "XONG", "o": {"0.5x": cell("x05"), "1x": cell("x1"), "2x": cell("x2")}},
        "7": {"trang_thai": "XONG", "o": {"NULL": cell("n7")}},
        "8": {"trang_thai": "XONG", "o": {"NULL": cell("n8"), "2x": cell("x8")}, "p4": {"lenh": "pytest", "ma_thoat": 0, "dong_cuoi": "ok"}},
        "9": {"trang_thai": "XONG", "o": {CT.TEN_O_NULL_M: cell("m9")}}}}


def _doc38(ket, hc=None):
    return CT.tong_hop(ket, HIEU_CHUAN, None, do=38, hc38=_hc_doc(a0=300, lo=20, hi=40) if hc is None else hc)


def test_do38_nen_DAT_du_moi_tieu_chi_o_sat_bien_A0_va_dai_PT_doc_tu_ban_ghi_khong_tu_hang_so():
    kc = _doc38(_ket_dat38())
    assert kc["khong_doc"] == [] and kc["truot"] == [] and kc["ket_cuc"] == "DAT", (kc["truot"], kc["khong_doc"])
    assert sorted(kc["tieu_chi"]) == sorted(["A", "A0", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "P1", "P2", "P3", "P4", "PT", "M1", "M2"])
    tc = kc["tieu_chi"]
    assert tc["A0"]["gia_tri"] == 300 and tc["A0"]["nguong"] == "<= 300"
    assert tc["PT"]["gia_tri"]["Gp_QUA_2x"] == 20 and tc["PT"]["nguong"].endswith("[20 ; 40]") and "[20 ; 40]" in tc["PT"]["nguong"]
    assert tc["M1"]["gia_tri"] == CT.NGUONG_M["M1"] == 50 and tc["M1"]["R"] == 1000
    assert tc["M2"]["dat"] is True and kc["thieu"] == []
    # hằng số trong tay KHÔNG được thay bản ghi: cùng dữ liệu, A0 = 299 thì A0 = 300 trượt; dải [21 ; 40] thì 20 trượt
    ket = _ket_dat38()
    assert _doc38(ket, _hc_doc(a0=299, lo=20, hi=40))["truot"] == ["A0"]
    assert _doc38(ket, _hc_doc(a0=300, lo=21, hi=40))["truot"] == ["PT"]
    assert _doc38(ket, _hc_doc(a0=300, lo=10, hi=19))["truot"] == ["PT"]
    assert _doc38(ket, _hc_doc(a0=317, lo=20, hi=40))["truot"] == []   # ngưỡng ĐO 37 (317) hay 307 không phải thứ cửa đọc: số ở BẢN GHI


def test_do38_dung_ham_hc38_bat_buoc_va_tong_hop_do37_khong_doi():
    with pytest.raises(ValueError):
        CT.tong_hop(_ket_dat38(), HIEU_CHUAN, None, do=38)
    assert CT.tong_hop({"cac_luong": {}}, HIEU_CHUAN, G_PHAY)["thieu"] == ["2", "3", "4"] == CT.tong_hop({"cac_luong": {}}, HIEU_CHUAN, G_PHAY, do=37)["thieu"]
    assert _doc38({"cac_luong": {}})["thieu"] == ["6", "7", "8", "9"]
    ket = _ket_dat38()
    del ket["cac_luong"]["9"]
    kc = _doc38(ket)
    assert kc["ket_cuc"] == "KHONG_DOC_DUOC" and kc["thieu"] == ["9"] and kc["tieu_chi"] == {}
    ket = _ket_dat38()
    ket["cac_luong"]["7"]["trang_thai"] = "DANG CHAY"
    assert _doc38(ket)["thieu"] == ["7"]


def _truot38():
    n = {**CT.NGUONG, "A0": 300}
    return [
        ("A0", {"n7": _o1(1000, g_khai=n["A0"] + 1, nang=n["C3"], g_delta="luan_phien")}, "A0"),
        ("PT_thap", {"x8": _o2(100, g_qua=19, p3=n["P3"])}, "PT"),
        ("PT_cao", {"x8": _o2(100, g_qua=41, p3=n["P3"])}, "PT"),
        ("PT_null", {"n8": _o2(100, null_alarm=n["PT_NULL"] + 1)}, "PT"),
        ("M1_51", {"m9": _o_nho(xac_nhan_nham=51)}, "M1"),
        ("M2_cao", {"m9": _o_nho(sd=1.25 + 1e-6, xac_nhan_nham=50)}, "M2"),
        ("M2_thap", {"m9": _o_nho(sd=0.8 - 1e-6, xac_nhan_nham=50)}, "M2"),
    ]


@pytest.mark.parametrize("ten,ghi_de,phai_truot", _truot38(), ids=[t[0] for t in _truot38()])
def test_do38_moi_tieu_chi_moi_va_doi_TRUOT_dung_mot_don_vi_qua_bien_va_chi_no_truot(ten, ghi_de, phai_truot):
    ket = _ket_dat38()
    gan = {"x05": ("6", "0.5x"), "x1": ("6", "1x"), "x2": ("6", "2x"), "n7": ("7", "NULL"), "n8": ("8", "NULL"), "x8": ("8", "2x"), "m9": ("9", CT.TEN_O_NULL_M)}
    for k, v in ghi_de.items():
        ket["cac_luong"][gan[k][0]]["o"][gan[k][1]]["thi_truong"] = v
    kc = _doc38(ket)
    assert kc["khong_doc"] == [], kc["khong_doc"]
    assert kc["truot"] == [phai_truot] and kc["ket_cuc"] == "TRUOT", (kc["truot"], kc["tieu_chi"][phai_truot])


def test_do38_cac_tieu_chi_cua_ĐO_37_doc_tren_dong_6_7_8_khong_tren_dong_2_3_4():
    """Mỗi tiêu chí ĐO 37 trượt một đơn vị ở ĐÚNG ô của dòng 6/7/8 → đúng tiêu chí ấy trượt (cùng ngưỡng, khác dòng)."""
    n = CT.NGUONG
    muc = {m["he_so"]: m["muc_tieu_delta_ic"] for m in HIEU_CHUAN["muc"]}
    x2 = dict(g_delta=muc[2.0], nang=300)
    ca = [("A", "x2", _o1(400, tim_ra=n["A"] - 1, g_qua=n["B2"], z_alarm=n["B3"], **x2), "6", "2x"),
          ("B2", "x2", _o1(400, tim_ra=n["A"], g_qua=n["B2"] - 1, z_alarm=n["B3"], **x2), "6", "2x"),
          ("B3", "x2", _o1(400, tim_ra=n["A"], g_qua=n["B2"], z_alarm=n["B3"] + 1, **x2), "6", "2x"),
          ("B4", "x05", _o1(400, g_delta=muc[0.5], h_qua=1), "6", "0.5x"),
          ("C1", "x05", _o1(400, g_delta=muc[0.5], c1=1), "6", "0.5x"),
          ("P3", "x8", _o2(100, g_qua=20, p3=n["P3"] - 1), "8", "2x"),
          ("P1", "n8", _o2(100, null_alarm=n["PT_NULL"], p1=1), "8", "NULL"),
          ("P2", "n8", _o2(100, null_alarm=n["PT_NULL"], p2=1), "8", "NULL")]
    for ma, _k, thi_truong, luong, o in ca:
        ket = _ket_dat38()
        ket["cac_luong"][luong]["o"][o]["thi_truong"] = thi_truong
        kc = _doc38(ket)
        assert kc["khong_doc"] == [] and kc["truot"] == [ma], (ma, kc["truot"], kc["khong_doc"])
    ket = _ket_dat38()
    ket["cac_luong"]["7"]["o"]["NULL"]["thi_truong"][-1 - n["B1"]]["bo_ba"]["Z"] = _tt(p_alarm=True)
    assert _doc38(ket)["truot"] == ["B1"]
    ket = _ket_dat38()
    ket["cac_luong"]["7"]["o"]["NULL"]["thi_truong"] = _o1(1000, g_khai=300, nang=n["C3"] + 1, g_delta="luan_phien")
    for i in range(n["B1"]):
        ket["cac_luong"]["7"]["o"]["NULL"]["thi_truong"][-1 - i]["bo_ba"]["Z"] = _tt(p_alarm=True)
    assert _doc38(ket)["truot"] == ["C3"]


def test_do38_M1_dem_thi_truong_co_it_nhat_mot_xac_nhan_nham_theo_oracle_cua_CHINH_thi_truong():
    def m1(thi_truong):
        ket = _ket_dat38(m9=thi_truong)
        return _doc38(ket)["tieu_chi"]["M1"]["gia_tri"]
    assert m1(_o_nho(xac_nhan_nham=0)) == 0 and m1(_o_nho(xac_nhan_nham=7)) == 7
    ra = _o_nho(xac_nhan_nham=3)
    for i in range(3):                                           # thêm QUA ở Z và H: cùng thị trường vẫn đếm MỘT lần
        ra[i]["bo_ba"]["Z"]["tt"] = "QUA"
        ra[i]["bo_ba"]["H"]["tt"] = "QUA"
    assert m1(ra) == 3
    ra = _o_nho(xac_nhan_nham=5)
    ra[0]["oracle"]["spec"][T.TEN_SPEC_G][0] = 0.001             # ΔIC_true(G) > 0 → QUA là ĐÚNG, không phải nhầm
    ra[1]["oracle"]["spec"][T.TEN_SPEC_G][0] = 0.0               # = 0 → nhầm (một phía: ΔIC_true ≤ 0)
    assert m1(ra) == 4
    ra = _o_nho(xac_nhan_nham=0)
    ra[0]["bo_ba"]["G"]["tt"] = "THUA"                           # THUA (báo động hai phía) không phải xác nhận
    ra[1]["bo_ba"]["G"]["tt"] = "DANG CHAM"
    assert m1(ra) == 0
    ra = _o_nho(xac_nhan_nham=0)
    ra[0]["bo_ba"]["Z"]["tt"] = "QUA"                            # Z có ΔIC_true = +0,003 > 0 ở mẫu giả: QUA đúng; H = −0,002: QUA nhầm
    ra[1]["bo_ba"]["H"]["tt"] = "QUA"
    assert m1(ra) == 1


def test_do38_M2_sd_z_phay_gop_G_Z_H_hai_dau_dong_va_bao_cao_khong_phan():
    lo, hi = 0.8, 1.25                       # LITERAL: [0,8 ; 1,25] đã ký, không đọc từ hằng số của dụng cụ
    assert CT.NGUONG_M["M2_dai"] == (lo, hi) and CT.NGUONG_M["M1"] == 50 and CT.NGUONG_M["ty_le_loai_toi_da"] == 0.01
    for sd, dat in ((lo - 1e-6, False), (lo + 1e-6, True), (1.0, True), (hi - 1e-6, True), (hi + 1e-6, False), (0.5, False), (2.0, False)):
        kc = _doc38(_ket_dat38(m9=_o_nho(sd=sd, xac_nhan_nham=0)))
        assert kc["tieu_chi"]["M2"]["dat"] is dat, sd
        assert kc["tieu_chi"]["M2"]["gia_tri"] == pytest.approx(sd, abs=1e-9)
        assert kc["truot"] == ([] if dat else ["M2"]) and kc["ket_cuc"] == ("DAT" if dat else "TRUOT"), sd
    # sd GỘP: z′ của Z lệch 1,5 mà G và H sd 1,0 → pooled giữa hai (không phán từng ứng viên)
    ra = _o_nho(sd=1.0)
    for m in ra:
        m["bo_ba"]["Z"]["delta"] *= 1.3
    kc = _doc38(_ket_dat38(m9=ra))
    assert kc["tieu_chi"]["M2"]["gia_tri"] > 1.0 and kc["tieu_chi"]["M2"]["dat"] is True
    # z′ dùng ΔIC_true của CHÍNH thị trường: đổi nó thì z′ đổi
    ra = _o_nho(sd=1.0)
    for m in ra:
        m["oracle"]["spec"][T.TEN_SPEC_G][0] += 0.05             # (Δ − ΔIC_true)/σ lệch ~ −5 ở G
    assert _doc38(_ket_dat38(m9=ra))["tieu_chi"]["M2"]["dat"] is False


def test_do38_M2_cap_sigma_0_hay_chua_phan_bi_loai_va_qua_1_phan_tram_la_KHONG_DOC_DUOC():
    kc = _doc38(_ket_dat38(m9=_o_nho(loai=10)))
    assert kc["khong_doc"] == [] and kc["bao_cao"]["M2_loai"] == {"so_cap_loai": 10, "so_cap": 3000, "ty_le": 10 / 3000}
    assert kc["tieu_chi"]["M2"]["R"] == 2990
    kc = _doc38(_ket_dat38(m9=_o_nho(loai=31)))                  # 31/3000 > 1%
    assert kc["ket_cuc"] == "KHONG_DOC_DUOC" and any("M2" in s for s in kc["khong_doc"])
    ra = _o_nho()
    del ra[0]["bo_ba"]["G"]["sd_null"]                           # thiếu sd_null (cặp chưa phán) cũng bị loại
    assert _doc38(_ket_dat38(m9=ra))["bao_cao"]["M2_loai"]["so_cap_loai"] == 1


def test_do38_bao_cao_Bao_kem_ba_khoi_M1_duoi_z_phay_va_khong_vao_ket_cuc():
    ra = _o_nho(bao_dong=60, nang=7, xac_nhan_nham=0)
    kc = _doc38(_ket_dat38(m9=ra))
    br = kc["bao_cao"]
    assert br["M1_bao_dong_hai_phia"] == {"so_thi_truong": 60, "R": 1000, "ty_le": 0.06}          # (a) so B1 ≤ 75
    assert br["M1_nang_cap_ma"] == {"so_thi_truong": 7, "R": 1000, "ty_le": 0.007}                # (c) so C3
    z = br["M1_z"]                                                                                # (b) sd, trung bình của z
    assert set(z) == {"gop", "G", "Z", "H"} and z["G"]["n"] == 1000 and z["gop"]["n"] == 3000 and z["gop"]["sd"] == pytest.approx(1.0, abs=1e-9)
    zc = NormalDist().inv_cdf(1 - 0.05 / (2 * 3))
    d = br["M2_duoi"]
    assert d["z_c"] == pytest.approx(zc, abs=1e-9) and abs(d["z_c"] - 2.3940) < 5e-5
    assert d["n"] == 3000 and d["ty_le"] == pytest.approx(0.0)            # ±1 luân phiên: không cặp nào > 2,394
    d3 = _doc38(_ket_dat38(m9=_o_nho(sd=3.0)))["bao_cao"]["M2_duoi"]
    assert d3["ty_le"] == pytest.approx(0.5) and d3["so_cap_tren"] == 1500
    assert set(br["M_delta_that_tb"]) == {"G", "Z", "H"} and br["M_delta_that_tb"]["G"] == pytest.approx(-0.02)
    assert kc["tieu_chi"]["M1"]["dat"] and kc["ket_cuc"] == "DAT" and "M1_z" not in kc["tieu_chi"]


def test_do38_tai_lap_hat_o_NULL_M_la_dieu_kien_KHONG_DOC_DUOC_va_C1_dong_9_chi_BAO_CAO():
    ket = _ket_dat38()
    ket["cac_luong"]["9"]["o"][CT.TEN_O_NULL_M]["tai_lap"] = "LECH"
    kc = _doc38(ket)
    assert kc["ket_cuc"] == "KHONG_DOC_DUOC" and any(f"9/{CT.TEN_O_NULL_M}" in s for s in kc["khong_doc"])
    ket = _ket_dat38()
    ket["cac_luong"]["6"]["o"]["2x"]["tai_lap"] = "LECH"
    assert _doc38(ket)["ket_cuc"] == "KHONG_DOC_DUOC"
    ra = _o_nho()
    ra[0]["chuoi"]["c1"] = ["khoan 1"]
    kc = _doc38(_ket_dat38(m9=ra))
    assert kc["tieu_chi"]["C1"]["gia_tri"] == 0 and kc["bao_cao"]["C1_dong_9"] == 1 and kc["ket_cuc"] == "DAT"


def test_do38_KHONG_DOC_DUOC_thang_TRUOT_va_may_do_NULL_o_dong_7():
    ket = _ket_dat38()
    for i, m in enumerate(ket["cac_luong"]["7"]["o"]["NULL"]["thi_truong"]):
        m["oracle"] = _oracle(i, z_he_so=1.7, g_delta=0.001 if i % 2 == 0 else -0.001)
    kc = _doc38(ket)
    assert kc["ket_cuc"] == "KHONG_DOC_DUOC" and any("NULL ngoai tieu chi ty le" in s for s in kc["khong_doc"])
    ket = _ket_dat38(m9=_o_nho(xac_nhan_nham=51))
    ket["cac_luong"]["8"]["o"]["2x"]["tai_lap"] = "LECH"
    kc = _doc38(ket)
    assert kc["ket_cuc"] == "KHONG_DOC_DUOC" and kc["truot"] == ["M1"] and any("8/2x" in s for s in kc["khong_doc"])


def test_in_ket_cuc_do38_noi_M1_M2():
    kc = _doc38(_ket_dat38(m9=_o_nho(xac_nhan_nham=51)))
    van = "\n".join(CT.in_ket_cuc(kc))
    assert "KẾT CỤC: TRUOT" in van and "M1" in van and "M2" in van and "TRƯỢT ở: M1" in van


def test_phi_nghich_khop_NormalDist_va_z_c_la_2_3940():
    for p in (0.5, 0.9, 1 - 0.05 / 6, 0.975, 0.999, 0.1):
        assert CT.phi_nghich(p) == pytest.approx(NormalDist().inv_cdf(p), abs=1e-9)
    assert round(CT.phi_nghich(1 - 0.05 / (2 * 3)), 4) == 2.3940


def test_z_phay_la_Delta_tru_DeltaICtrue_chia_sigma_hoan_vi():
    assert CT.z_phay(0.05, 0.02, 0.01) == pytest.approx(3.0)
    assert CT.z_phay(-0.01, 0.02, 0.01) == pytest.approx(-3.0)
    assert CT.z_phay(0.05, 0.02, 0.0) is None and CT.z_phay(None, 0.02, 0.01) is None and CT.z_phay(0.05, 0.02, None) is None


# ══ MỘT THỊ TRƯỜNG NULL-M (dòng thử 9001, đường thật) ═════════════════════════════════════════════════════

@pytest.fixture
def kappa_d_thu(monkeypatch):
    monkeypatch.setattr(CT, "doc_kappa_d", lambda duong=None: 0.018)
    return 0.018


def test_thi_truong_NULL_M_dong_thu_di_het_pipeline_va_khop_cham_truc_tiep(kappa_d_thu):
    m = CT.chay_mot_thi_truong_m(LUONG_TEST, None, CT.TEN_O_NULL_M, 0.0, 3, so_hoan_vi=200)
    assert set(m) == {"chi_so", "dg", "nguong", "bo_ba", "chuoi", "oracle", "giay"} and set(m["bo_ba"]) == {"G", "Z", "H"}
    assert abs(m["nguong"] - 0.05 / 3) < 1e-15 and m["chuoi"]["c1"] == [] and set(m["giay"]) == {"sinh", "bo_ba", "chuoi", "oracle"}
    assert set(m["oracle"]["spec"]) == set(T.ho_spec_oracle()) and "ic_da_ghi" in m["oracle"]
    tt = T.sinh_thi_truong_m(LUONG_TEST, 3, kappa_d_thu, co_su_that=False)
    assert m["dg"] == CT._bam(tt.dong_quyet_dinh(), tt.gia)
    import hieu_chuan_thi_truong_gia as H
    bang = {"gia": tt.gia, "keo_luc": H.keo_luc_gia(tt.ngay[-1]), "nguon": {x: "vci" for x in tt.ma}}
    r = cx.cham(tt.dong_quyet_dinh(), H.so_ung_vien_bo_ba(), bang, cx.HAT_RNG, 200)
    for ten in ("G", "Z", "H"):
        c = r["chi_tiet"][ten]
        assert m["bo_ba"][ten]["tt"] == c["trang_thai"] and m["bo_ba"][ten]["p"] == c["p"] and m["bo_ba"][ten]["delta"] == c["delta"]
        assert m["bo_ba"][ten]["z"] == c["ket"]["z"] and m["bo_ba"][ten]["sd_null"] == float(np.std(c["ket"]["null"]))
    su = T.tinh_su_that_m(LUONG_TEST, 3, kappa_d_thu)       # oracle của CHÍNH thị trường (κ_d thật của nó, không phải κ = 0)
    assert m["oracle"]["spec"] == {t: [v["delta_ic"], v["se_mc"]] for t, v in su["spec"].items()} and m["oracle"]["ic_da_ghi"] == su["ic_da_ghi"]
    # κ_d vào thị trường: đổi κ_d thì dữ liệu đổi (không bị bỏ qua)
    tt0 = T.sinh_thi_truong_m(LUONG_TEST, 3, 0.0, co_su_that=False)
    assert CT._bam(tt0.dong_quyet_dinh(), tt0.gia) != m["dg"]


def test_tai_lap_sinh_m_bang_bit_va_nho_hat_va_nho_kappa_d(monkeypatch):
    monkeypatch.setattr(CT, "doc_kappa_d", lambda duong=None: 0.018)
    a, b = CT.tai_lap_sinh_m(LUONG_TEST, None, 5), CT.tai_lap_sinh_m(LUONG_TEST, None, 5)
    assert a == b and a != CT.tai_lap_sinh_m(LUONG_TEST, None, 6)
    monkeypatch.setattr(CT, "doc_kappa_d", lambda duong=None: 0.02)
    assert a != CT.tai_lap_sinh_m(LUONG_TEST, None, 5)
    tt = T.sinh_thi_truong_m(LUONG_TEST, 5, 0.018, co_su_that=False)
    assert a == CT._bam(tt.dong_quyet_dinh(), tt.gia)


def test_doc_kappa_d_doc_tu_ban_ghi_va_no_khi_thieu(tmp_path):
    f = tmp_path / "hc.json"
    f.write_text(json.dumps(_hc(kd=0.024)), encoding="utf-8")
    assert CT.doc_kappa_d(f) == 0.024
    f.write_text(json.dumps(_hc(a0__trang_thai="DANG CHAY")), encoding="utf-8")
    with pytest.raises(ValueError):
        CT.doc_kappa_d(f)
    with pytest.raises(ValueError):
        CT.doc_kappa_d(tmp_path / "khong_co.json")


def test_viec_dua_o_NULL_M_den_ham_NULL_M_va_chay_luong_ghi_kappa_d_va_tai_lap_NULL_M(monkeypatch, tmp_path):
    goi = []
    monkeypatch.setattr(CT, "doc_kappa_d", lambda duong=None: 0.018)
    monkeypatch.setattr(CT, "chay_mot_thi_truong_m", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0: goi.append(("m", ten, chi_so)) or {"chi_so": chi_so, "dg": f"d{chi_so}", "giay": {}})
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang1", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0: goi.append(("t1", ten, chi_so)) or {"chi_so": chi_so, "dg": f"d{chi_so}", "giay": {}})
    monkeypatch.setattr(CT, "tai_lap_sinh_m", lambda luong, phep, chi_so: f"d{chi_so}")
    monkeypatch.setattr(CT, "tai_lap_sinh", lambda luong, phep, tang, muc, chi_so: f"d{chi_so}")
    assert CT._viec((LUONG_TEST, None, 1, CT.TEN_O_NULL_M, 0.0, 4, 50, True)) == (CT.TEN_O_NULL_M, {"chi_so": 4, "dg": "d4", "giay": {}})
    assert CT._viec((LUONG_TEST, None, 1, "NULL", 0.0, 4, 50, True))[0] == "NULL" and [g[0] for g in goi] == ["m", "t1"]
    kh = {"tang": 1, "o": ((CT.TEN_O_NULL_M, 0.0, 10, 3), ("NULL", 0.0, 100, 2))}
    ket = CT.chay_luong(LUONG_TEST, None, 1, False, 100, tmp_path / "k.json", kh, 50, True, lambda: None, "x", False, lambda k, d: None, do=38)
    cu = ket["cac_luong"][str(LUONG_TEST)]
    assert cu["o"][CT.TEN_O_NULL_M]["kappa"] == 0.018 and cu["o"]["NULL"]["kappa"] == 0.0
    assert cu["o"][CT.TEN_O_NULL_M]["tai_lap"] == "KHOP" and ket["do"] == "ĐO 38" and ket["buoc"] == 304
    assert sorted(g[2] for g in goi if g[0] == "m") == [4, 10, 11, 12]


def test_chay_luong_do37_giu_nguyen_buoc_295_va_do_37_cua_ban_ghi_dau(monkeypatch, tmp_path):
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang1", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0: {"chi_so": chi_so, "dg": f"d{chi_so}", "giay": {}})
    monkeypatch.setattr(CT, "tai_lap_sinh", lambda luong, phep, tang, muc, chi_so: f"d{chi_so}")
    kh = {"tang": 1, "o": (("2x", 2.0, 10, 2),)}
    ket = CT.chay_luong(LUONG_TEST, None, 1, False, 100, tmp_path / "k.json", kh, 50, True, lambda: None, "x", False, lambda k, d: None)
    assert ket["do"] == "ĐO 37" and ket["buoc"] == 295


# ══ GÁC (AST) ═════════════════════════════════════════════════════════════════════════════════════════════

def _cay():
    return ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))


def _ham(cay):
    return {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}


def _ten_goi(f):
    return [n for n in ast.walk(f) if isinstance(n, ast.Call)]


VAO_BO_SINH_38 = {"sinh_thi_truong_m", "tinh_su_that_m", "_sinh_loi_m", "ic_da_ghi_m", "sinh_thi_truong", "sinh_thi_truong_2", "tinh_su_that",
                  "chay_vong", "cham_diem_theo_ma"}


def _ten(n):
    return n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id if isinstance(n.func, ast.Name) else ""


def test_G4_AST_ham_NULL_M_goi_cua_TRUOC_bo_sinh_va_oracle_SAU_bo_ba_va_chuoi():
    ham = _ham(_cay())
    for ten in ("chay_mot_thi_truong_m", "tai_lap_sinh_m"):
        f = ham[ten]
        dong_cua = [n.lineno for n in _ten_goi(f) if _ten(n) == "kiem_luong_chinh_thuc"]
        dong_sinh = [n.lineno for n in _ten_goi(f) if _ten(n) in VAO_BO_SINH_38]
        assert dong_cua and dong_sinh and min(dong_cua) < min(dong_sinh), ten
    f = ham["chay_mot_thi_truong_m"]
    dong = lambda t: [n.lineno for n in _ten_goi(f) if _ten(n) == t]  # noqa: E731
    assert dong("tinh_su_that_m") and max(dong("chay_vong") + dong("cham")) < min(dong("tinh_su_that_m"))
    assert "tinh_su_that" not in {_ten(n) for n in _ten_goi(f)}       # KHÔNG dùng oracle cũ (rút mẫu dài không có nhân tố ngành)
    assert {n.lineno for n in _ten_goi(ham["kiem_cong"]) if _ten(n) in VAO_BO_SINH_38} == set()


def test_AST_so_6_den_10_khong_xuat_hien_nhu_doi_so_goi_nao_va_ba_hang_dong_hat_cu_khong_doi():
    cay = _cay()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            for k in n.keywords:
                assert not (k.arg == "luong" and isinstance(k.value, ast.Constant)), "dong hat viet tran trong loi goi"
            if _ten(n) in VAO_BO_SINH_38 | {"chay_luong", "kiem_luong_chinh_thuc", "kiem_cong"}:
                assert not any(isinstance(a, ast.Constant) and isinstance(a.value, int) and 1 <= a.value <= 10 for a in n.args[:1]), ast.dump(n)[:80]
    gan = {t.id: n.value for n in ast.walk(cay) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)
           and t.id in ("LUONG_THU", "LUONG_CHINH_THUC", "LUONG_KHONG_BAO_GIO")}
    assert ast.literal_eval(gan["LUONG_THU"]) == 9001 and ast.literal_eval(gan["LUONG_CHINH_THUC"]) == (2, 3, 4) \
        and ast.literal_eval(gan["LUONG_KHONG_BAO_GIO"]) == (5,)
    dg = [n.value for n in ast.walk(cay) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name) and t.id == "DO_THEO_LUONG"]
    assert len(dg) == 1 and ast.literal_eval(dg[0]) == {2: 37, 3: 37, 4: 37, 6: 38, 7: 38, 8: 38, 9: 38}


def test_AST_PhepChay_van_chi_dung_o_kiem_cong_va_chi_mot_ham_cua():
    cay = _cay()
    cho = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "PhepChay"]
    assert len(cho) == 1 and cho[0] in list(ast.walk(_ham(cay)["kiem_cong"]))


def test_cac_dung_cu_khac_chan_dong_6_7_8_9_10_nhu_2_3_4_5():
    import importlib.util
    for ten in ("chay_vong_thi_truong_gia", "hieu_chuan_thi_truong_gia", "oracle_tang2_thi_truong_gia", "chay_tang2_thi_truong_gia",
                "chay_vong_tang2_thi_truong_gia", "hieu_chuan_sua_c4"):
        duong = GOC / "tools" / f"{ten}.py"
        s = importlib.util.spec_from_file_location(ten + "_cua38", duong)
        m = importlib.util.module_from_spec(s)
        sys.modules.setdefault(ten, m)
        s.loader.exec_module(m)
        for l in (6, 7, 8, 9, 10):
            with pytest.raises(ValueError):
                m.kiem_luong(l)
        assert "chay_chinh_thuc" not in duong.read_text(encoding="utf-8")


def test_bo_sinh_cong_khai_khong_goi_tu_dung_cu_nao_khac_voi_dong_6_den_10():
    """Không file nguồn nào ngoài dụng cụ này và hai file test ĐO 37/38 chứa lời gọi bộ sinh với dòng hạt viết trần 6…10."""
    import duyet_repo
    sai = []
    for duong in list(GOC.glob("*.py")) + list((GOC / "tools").glob("*.py")):
        cay = ast.parse(duong.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and _ten(n) in {"sinh_thi_truong", "sinh_thi_truong_m", "sinh_thi_truong_2", "tinh_su_that", "tinh_su_that_m"} \
                    and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value in (6, 7, 8, 9, 10):
                sai.append(f"{duong.name}:{n.lineno}")
    assert sai == []
    for duong in duyet_repo.liet_ke(GOC, "tests", "*.py"):
        cay = ast.parse(duong.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and _ten(n) in {"sinh_thi_truong", "sinh_thi_truong_m", "sinh_thi_truong_2", "tinh_su_that", "tinh_su_that_m", "sinh_null"} \
                    and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value in (6, 7, 8, 9, 10):
                sai.append(f"{duong.name}:{n.lineno}")
    assert sai == [], sai


# ══ ĐO 38 TRONG docs/TIEU-CHI-DOC-TRUOC.md ════════════════════════════════════════════════════════════════

DO37 = CT.cat_muc_do(TIEU_CHI, 37)
DO38 = CT.cat_muc_do(TIEU_CHI, 38)


def test_ĐO_38_co_trong_tieu_chi_ngay_sau_ĐO_37_la_muc_cuoi_va_duy_nhat_va_ĐO_37_khong_bi_sua():
    assert DO38 is not None and DO37 is not None
    assert len(re.findall(r"^##\s+ĐO\s+38\s*—", TIEU_CHI, re.M)) == 1
    so = [int(m.group(1)) for m in re.finditer(r"^##\s+ĐO\s+(\d+)[a-z]?\s*—", TIEU_CHI, re.M)]
    assert so[-2:] == [37, 38] and so.count(37) == 1
    assert TIEU_CHI.index("## ĐO 37 —") < TIEU_CHI.index("## ĐO 38 —")
    assert "**Đã tra trùng:** BƯỚC" in DO38 and f"`{CT.TEN_DUNG_CU}`" in DO38
    # thân ĐO 37 không đổi một chữ so với lúc chạy (BƯỚC 296 ghi băm vào bản ghi thật)
    ban = json.loads((GOC / "docs" / "thi-truong-gia-ket-qua.json").read_text(encoding="utf-8"))
    mong = hashlib.sha256(CT.chuan_hoa(DO37).encode("utf-8")).hexdigest()
    assert all(ban["cac_luong"][str(l)]["git"]["sha_do"] == mong for l in (2, 3, 4))


def test_ĐO_38_neu_nguyen_van_lenh_dong_ke_hoach_va_lenh_doc_ket_cuc_cua_ca_bon_dong_hat():
    chuan = CT.chuan_hoa(DO38)
    for l in (6, 7, 8, 9):
        assert CT.chuan_hoa(CT.lenh_chuan(l, 38)) in chuan and CT.chuan_hoa(CT.dong_ke_hoach(l, 38)) in chuan
        assert f"./.venv/Scripts/python.exe -X utf8 {CT.lenh_chuan(l, 38)} --so-tien-trinh 12" in DO38
    assert f"./.venv/Scripts/python.exe -X utf8 {CT.lenh_ket_cuc(38)}" in DO38 and "docs/thi-truong-gia-ket-qua-do38.json" in DO38
    assert "docs/thi-truong-gia-hieu-chuan-do38.json" in DO38
    # thứ tự lệnh của BƯỚC 304: dòng 6 · 7 · 9 rồi 8
    vt = [DO38.index(f"{CT.lenh_chuan(l, 38)} --so-tien-trinh 12") for l in (6, 7, 9, 8)]
    assert vt == sorted(vt)
    assert "`luu_moi = 12`" in DO38 and "P2" in DO38 and "cả 200" in DO38


def test_ĐO_38_cau_so_da_ky_la_dung_cau_cua_ban_ghi_hieu_chuan_THAT():
    hc = CT.doc_hieu_chuan_do38(DUONG_HC38)
    assert CT.chuan_hoa(CT.cau_da_ky_do38(hc)) in CT.chuan_hoa(DO38)
    assert hc["nguong_A0"] == 307 and tuple(hc["dai_pt"]) == (31, 62) and hc["kappa_d"] == 0.018
    # kiểm_cong thật (git tiêm) chấp nhận chính văn bản thật này ở cây làm việc
    for l in (6, 7, 8, 9):
        p = CT.kiem_cong(l, git=_git_gia(TIEU_CHI), ket_qua_hien_co=None, van_ban_cay=TIEU_CHI, ban_ghi_hc=json.loads(DUONG_HC38.read_text(encoding="utf-8")))
        assert p.hop_le() and p.sha_do == hashlib.sha256(CT.chuan_hoa(DO38).encode("utf-8")).hexdigest()


def test_ĐO_38_chep_nguyen_van_cac_hang_ĐO_37_con_giu_va_chi_A0_va_PT_doi():
    hang37 = {m.group(1): m.group(0) for m in re.finditer(r"^\| \*\*([A-Z0-9]+)\*\* \|.*$", DO37, re.M)}
    hang38 = {m.group(1): m.group(0) for m in re.finditer(r"^\| \*\*([A-Z0-9]+)\*\* \|.*$", DO38, re.M)}
    assert set(hang37) == {"A", "A0", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "P", "PT"}
    assert set(hang38) == set(hang37) | {"M1", "M2"}
    for ma in set(hang37) - {"A0", "PT"}:
        assert hang38[ma] == hang37[ma], ma
    assert "≤ 307" in hang38["A0"] and "[31 ; 62]" in hang38["PT"] and "≤ 12/100" in hang38["PT"] and "≤ 317" not in hang38["A0"]
    assert "≤ 50 (5%)" in hang38["M1"] and "1.000" in hang38["M1"] and "[0,8 ; 1,25]" in hang38["M2"] and "z′" in hang38["M2"]
    assert f"≤ {CT.NGUONG_M['M1']}" in hang38["M1"] and all(str(x).replace(".", ",") in hang38["M2"] for x in CT.NGUONG_M["M2_dai"])
    chuan37, chuan38 = CT.chuan_hoa(DO37), CT.chuan_hoa(DO38)
    for k, v in CT.NGUONG.items():
        if k not in ("A0",):
            assert str(v) in DO38, k
    for cau in ("Định nghĩa.", "Báo cáo, không phán:", "KHÔNG ĐỌC ĐƯỢC", "ĐẠT", "TRƯỢT ở tiêu chí X"):
        assert cau in DO38


def test_ĐO_38_nhan_BUOC_299_streams_luat_rang_buoc_va_loi_nguoi_dung_nguyen_van():
    for chuoi in ("Đã khai", "Báo kèm", "Sau khi nhìn"):
        assert chuoi in DO38
    assert "*\"Giữ M1 + phán thêm z′ (Recommended)\"*" in DO38 and "*\"ok tiếp tục làm theo đề xuất của bạn\"*" in DO38 and "*\"duyệt cả 4\"*" in DO38
    assert "không hạ ngưỡng" in DO38.lower() or "KHÔNG hạ ngưỡng" in DO38
    assert "dòng hạt MỚI" in DO38 or "dòng hạt mới" in DO38 or "NEW" in DO38 or "dòng MỚI" in DO38
    for s in ("6 · 7 · 8 · 9", "10", "9001", "1.100.001"):
        assert s in DO38, s
    for dong in ("chặn vĩnh viễn",):
        assert dong in DO38
    assert re.search(r"\*\*Đã tra trùng:\*\* BƯỚC", DO38)


def test_ĐO_38_thoa_gac_cau_truc_nhan_cua_BUOC_299():
    import test_ket_qua_do_co_nhan as K
    assert K.kiem_tieu_chi(TIEU_CHI) == []
    muc, _ = K.doc_tieu_chi(TIEU_CHI)
    ten = [t for t, n, h, _ in muc if n == 38 and not h]
    assert ten == ["ĐO 38"]
    ky = K.ma_phan_ky(next(than for t, n, h, than in muc if n == 38))
    assert {"M1", "M2", "M3", "M4"} <= ky[0]
