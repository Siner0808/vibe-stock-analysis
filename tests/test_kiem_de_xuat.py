"""Gác BẢNG KIỂM xác định cho ứng viên do MÁY soạn — BƯỚC 305 (`kiem_de_xuat.py`, `tools/kiem_phieu_de_xuat.py`).

Đặc tả: `vibe_logs_y23/DAC-TA-Y2.md` (nháp 25/11/2026). Người dùng 23/11/2026: *"làm ý 1 và 2"*; 25/11/2026
*"Đồng ý ý 2 và 3A"* → *"duyệt"* (cả ba khuyến nghị mục 5: không lưu phiếu thành file; bảng ngưỡng giữ
nguyên, là ƯỚC LƯỢNG chọn trước khi nhìn ứng viên nào; chạy cả cho đề xuất tay, chỉ in).

Bảng kiểm CHỈ ĐỌC spec + sổ + hai trường khai (`dan_xuat`, `da_doc_ket_qua_som`) và trả chữ PASS · REVISE ·
REJECT kèm lý do. Nó không có số nào để ghi (không đổi điểm, trọng số, ngưỡng), không mở khoá ứng viên, không
chấm, không đọc kết quả. Các gác dưới đây ghim điều ấy bằng AST.

Mỗi mục được thử CẢ HAI chiều (qua và chặn) bằng mẫu dựng tay; đối chứng THẬT là UV-001 của sổ thật với băm
file trước = sau (khuôn `tests/test_bang_cham_bong.py::test_SO_THAT_UV_001_…`). Test CHỈ chạy trên dữ liệu
dựng trong test và `docs/ung-vien.json` đọc-thuần; không mạng, không `backtest/cache*`.
"""
import ast
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import cham_bong as cb  # noqa: E402
import duyet_repo  # noqa: E402
import kiem_de_xuat as K  # noqa: E402
import kiem_phieu_de_xuat as CLI  # noqa: E402
import thi_truong_gia as T  # noqa: E402

TT, MM, VV, SS, RR = cb.THANH_PHAN
SO_THAT = GOC / "docs" / "ung-vien.json"
DUONG_MODULE = GOC / "kiem_de_xuat.py"
DUONG_CLI = GOC / "tools" / "kiem_phieu_de_xuat.py"


def _spec(**w):
    """Spec trọng số từ khoá ngắn: t · m · v · s · r."""
    ten = {"t": TT, "m": MM, "v": VV, "s": SS, "r": RR}
    return {"loai": "trong_so", "trong_so": {ten[k]: x for k, x in w.items()}}


def _tay(spec, loai="tay", tham_so=(), doc=False, ma=None):
    p = {"spec": spec, "dan_xuat": {"loai": loai, "tham_so": list(tham_so)}, "da_doc_ket_qua_som": doc}
    if ma is not None:
        p["ma"] = ma
    return p


def _hang(ma, spec):
    return {"khai_ngay": "2026-10-02", "mo_ta": f"mau {ma}", "ly_do": "mau", "qua_sang": None, "spec": spec}


def _so(**uv):
    return {"ung_vien": {ma: _hang(ma, s) for ma, s in uv.items()}}


UV1_SPEC = _spec(t=0.2941, m=0.2941, v=0.2353, s=0.1765)
SO_UV1 = _so(**{"UV-001": UV1_SPEC})
PHIEU_UV1 = _tay(UV1_SPEC, "bo_mot", [RR], ma="UV-001")
SO_RONG = {"ung_vien": {}}


def _muc(kq, ten):
    (m,) = [x for x in kq["muc"] if x["ten"] == ten]
    return m


def _ket(kq, ten):
    return _muc(kq, ten)["ket_qua"]


# ── 1. nối với nguồn, hằng số, hình dạng kết quả ─────────────────────────────────────────────────────────

def test_THANH_PHAN_va_CO_SO_khop_nguon_vi_module_khong_duoc_nhap_ho():
    """Module không nhập `cham_bong` / `thi_truong_gia` (gác AST dưới), nên hai bản chép phải khớp nguồn."""
    assert K.THANH_PHAN == cb.THANH_PHAN
    assert K.CO_SO == T.TRONG_SO_MAC_DINH and tuple(K.CO_SO) == tuple(T.TRONG_SO_MAC_DINH)
    assert K.LOAI_SPEC == cb.LOAI_SPEC


def test_HANG_SO_ngưỡng_ghim_literal_dung_bang_da_duoc_duyet():
    assert (K.TU_DO_REVISE, K.TU_DO_REJECT) == (3, 4)
    assert K.BUOC_TRONG_SO == 0.05 and K.SAN_L1 == 0.10
    assert K.DUNG_SAI_DUNG_LAI == 1e-4 and K.DUNG_SAI_TRUNG == 1e-4
    assert K.SO_DONG_CUNG_HO == 2
    assert (K.PASS, K.REVISE, K.REJECT) == ("PASS", "REVISE", "REJECT")


def test_KET_QUA_co_nam_muc_dung_thu_tu_va_KHONG_co_diem_tong():
    kq = K.kiem_phieu(PHIEU_UV1, SO_UV1)
    assert [m["ten"] for m in kq["muc"]] == ["THAM_SO_TU_DO", "DO_CHINH_XAC", "QUA_GAN_BAN_CHAY",
                                             "TRUNG_LAP", "KHAI_BAT_BUOC"]
    assert [m["stt"] for m in kq["muc"]] == [1, 2, 3, 4, 5]
    assert set(kq) == {"ket_luan", "muc"}, "không điểm tổng, không trường nào ngoài hai khoá"
    for m in kq["muc"]:
        assert m["ket_qua"] in (K.PASS, K.REVISE, K.REJECT) and m["ly_do"] and "do" in m


def test_KIEM_SPEC_cua_module_chap_nhan_va_tu_choi_dung_nhu_cham_bong_kiem_spec():
    xau = [None, {"loai": "khac", "trong_so": {TT: 1.0}}, _spec(),
           {"loai": "trong_so", "trong_so": {"news_score": 1.0}}, _spec(t=1.5, m=-0.5), _spec(t=0.5, m=0.4)]
    tot = [_spec(t=1.0), _spec(t=0.5, r=0.5), UV1_SPEC]
    for s in xau:
        with pytest.raises(ValueError):
            cb.kiem_spec(s)
        with pytest.raises(ValueError):
            K.kiem_phieu({"spec": s, "dan_xuat": {"loai": "tay", "tham_so": []}, "da_doc_ket_qua_som": False},
                         SO_RONG)
    for s in tot:
        cb.kiem_spec(s)
        K.kiem_phieu(_tay(s), SO_RONG)


# ── 2. mục 1 THAM_SO_TU_DO ───────────────────────────────────────────────────────────────────────────────

def test_MUC1_moi_spec_cua_ho_F_va_Z_khai_dung_nhan_thi_tu_do_bang_0_va_PASS():
    ho = T.ho_spec_f()
    cac = {f"mono_{c}": (ho[f"mono_{c}"], "mono", [c]) for c in cb.THANH_PHAN}
    cac |= {f"bo_{c}": (ho[f"bo_{c}"], "bo_mot", [c]) for c in cb.THANH_PHAN}
    cac["deu"] = (ho["deu"], "deu", [])
    cac["z"] = (T.spec_z(), "doi_cho", [TT, SS])
    assert len(cac) == 12
    for ten, (s, loai, ts) in cac.items():
        kq = K.kiem_phieu(_tay(s, loai, ts), SO_RONG)
        m = _muc(kq, "THAM_SO_TU_DO")
        assert m["ket_qua"] == K.PASS and m["do"] == 0, ten
        assert _ket(kq, "DO_CHINH_XAC") == K.PASS, ten      # chỉ `tay` mới bị soát bội 0,05


def test_MUC1_UV_001_lam_tron_bon_chu_so_van_khop_bo_mot_risk():
    m = _muc(K.kiem_phieu(PHIEU_UV1, SO_UV1), "THAM_SO_TU_DO")
    assert m["ket_qua"] == K.PASS and m["do"] == 0


def test_MUC1_khai_SAI_nhan_la_REJECT():
    sai = _tay(UV1_SPEC, "bo_mot", [SS])                    # UV-001 bỏ risk, khai là bỏ sr
    m = _muc(K.kiem_phieu(sai, SO_RONG), "THAM_SO_TU_DO")
    assert m["ket_qua"] == K.REJECT and "nhãn" in m["ly_do"]
    mono_sai = _tay(T.ho_spec_f()["deu"], "mono", [TT])
    assert _ket(K.kiem_phieu(mono_sai, SO_RONG), "THAM_SO_TU_DO") == K.REJECT


def test_MUC1_dung_sai_dung_lai_5e5_qua_5e3_la_nhan_sai():
    """Đột biến `1e-4 → 1e-1` làm nhãn sai lọt: lệch 5e-3 phải REJECT; lệch 5e-5 vẫn là nhãn đúng."""
    gan = _spec(t=0.29415, m=0.29405, v=0.2353, s=0.1765)        # lệch 5e-5 mỗi trọng số
    xa = _spec(t=0.2991, m=0.2891, v=0.2353, s=0.1765)           # lệch 5e-3
    assert _ket(K.kiem_phieu(_tay(gan, "bo_mot", [RR]), SO_RONG), "THAM_SO_TU_DO") == K.PASS
    assert _ket(K.kiem_phieu(_tay(xa, "bo_mot", [RR]), SO_RONG), "THAM_SO_TU_DO") == K.REJECT


def test_MUC1_tay_dem_trong_so_duong_tru_1_ba_la_REVISE_bon_la_REJECT_hai_la_PASS():
    hai = _tay(_spec(t=0.5, m=0.3, v=0.2))
    ba = _tay(_spec(t=0.3127, m=0.1873, v=0.3412, s=0.1588, r=0.0))
    bon = _tay(_spec(t=0.22, m=0.24, v=0.21, s=0.17, r=0.16))
    mot = _tay(_spec(t=1.0))
    for p, ky, tu_do in [(mot, K.PASS, 0), (hai, K.PASS, 2), (ba, K.REVISE, 3), (bon, K.REJECT, 4)]:
        m = _muc(K.kiem_phieu(p, SO_RONG), "THAM_SO_TU_DO")
        assert (m["ket_qua"], m["do"]) == (ky, tu_do)


def test_MUC1_luat_tho_tay_dem_deu_la_bon_tu_do_dung_duong_la_khai_deu():
    deu = T.ho_spec_f()["deu"]
    assert _muc(K.kiem_phieu(_tay(deu, "tay"), SO_RONG), "THAM_SO_TU_DO")["ket_qua"] == K.REJECT
    assert _muc(K.kiem_phieu(_tay(deu, "deu"), SO_RONG), "THAM_SO_TU_DO")["ket_qua"] == K.PASS


@pytest.mark.parametrize("dan_xuat", [
    {"loai": "la", "tham_so": []}, {"loai": "mono", "tham_so": [TT, MM]}, {"loai": "mono", "tham_so": []},
    {"loai": "bo_mot", "tham_so": ["news_score"]}, {"loai": "deu", "tham_so": [TT]},
    {"loai": "doi_cho", "tham_so": [TT]}, {"loai": "doi_cho", "tham_so": [TT, TT]},
    {"loai": "tay", "tham_so": ["x"]}, {"loai": "tay"}, {"tham_so": []}, [], "tay"])
def test_MUC1_dan_xuat_hu_thi_NO_ValueError_khong_doan(dan_xuat):
    with pytest.raises(ValueError):
        K.kiem_phieu({"spec": UV1_SPEC, "dan_xuat": dan_xuat, "da_doc_ket_qua_som": False}, SO_RONG)


# ── 3. mục 2 DO_CHINH_XAC ────────────────────────────────────────────────────────────────────────────────

def test_MUC2_tay_trong_so_khong_boi_cua_0_05_la_REVISE_va_hai_chieu():
    khong = _tay(_spec(t=0.3127, m=0.1873, v=0.3412, s=0.1588))
    boi = _tay(_spec(t=0.5, m=0.35, v=0.15))                      # 0,15 · 0,35 phải tính là bội dù dấu phẩy động
    nhieu = _tay(_spec(t=0.7, m=0.3))
    assert _ket(K.kiem_phieu(khong, SO_RONG), "DO_CHINH_XAC") == K.REVISE
    assert _ket(K.kiem_phieu(boi, SO_RONG), "DO_CHINH_XAC") == K.PASS
    assert _ket(K.kiem_phieu(nhieu, SO_RONG), "DO_CHINH_XAC") == K.PASS
    m = _muc(K.kiem_phieu(khong, SO_RONG), "DO_CHINH_XAC")
    assert set(m["do"]) == {TT, MM, VV, SS}


def test_MUC2_mot_trong_so_le_cua_ca_hai_tu_do_PASS_nhung_ket_luan_van_REVISE():
    """Hai tự do (mục 1 PASS) mà 0,52/0,48 không bội 0,05: chỉ mục 2 đỏ → ket_luan REVISE."""
    kq = K.kiem_phieu(_tay(_spec(t=0.52, m=0.48)), SO_RONG)
    assert [m["ket_qua"] for m in kq["muc"]] == [K.PASS, K.REVISE, K.PASS, K.PASS, K.PASS]
    assert kq["ket_luan"] == K.REVISE


def test_MUC2_phieu_da_khai_nhan_dan_xuat_khong_bi_soat_boi_0_05():
    assert _ket(K.kiem_phieu(PHIEU_UV1, SO_UV1), "DO_CHINH_XAC") == K.PASS      # 0,2941… không bội 0,05 mà đúng nhãn


# ── 4. mục 3 QUA_GAN_BAN_CHAY ────────────────────────────────────────────────────────────────────────────

def test_MUC3_Z_nguyen_ban_doi_cho_trend_momentum_cung_0_25_L1_bang_0_la_REJECT():
    z = _spec(t=0.25, m=0.25, v=0.20, s=0.15, r=0.15)             # đổi chỗ hai trọng số bằng nhau = đúng bộ mặc định
    kq = K.kiem_phieu(_tay(z, "doi_cho", [TT, MM]), SO_RONG)
    assert _ket(kq, "THAM_SO_TU_DO") == K.PASS                    # khai đúng nhãn
    m = _muc(kq, "QUA_GAN_BAN_CHAY")
    assert m["ket_qua"] == K.REJECT and m["do"] == 0
    assert kq["ket_luan"] == K.REJECT


def test_MUC3_L1_duoi_0_10_REVISE_tu_0_10_tro_len_PASS_va_biên_dung_0_10_la_PASS():
    cac = [(_spec(t=0.29, m=0.21, v=0.20, s=0.15, r=0.15), K.REVISE, 0.08),
           (_spec(t=0.30, m=0.20, v=0.20, s=0.15, r=0.15), K.PASS, 0.10),   # biên: không `<`
           (T.spec_z(), K.PASS, 0.20), (UV1_SPEC, K.PASS, 0.30)]
    for s, ky, l1 in cac:
        m = _muc(K.kiem_phieu(_tay(s), SO_RONG), "QUA_GAN_BAN_CHAY")
        assert m["ket_qua"] == ky and m["do"] == pytest.approx(l1, abs=1e-9)


def test_MUC3_L1_tinh_tren_nam_thanh_phan_ke_ca_thanh_phan_vang():
    """Trọng số vắng = 0: UV-001 bỏ risk (0,15) góp vào L1; bỏ nó đi thì L1 sẽ thấp hơn 0,30."""
    m = _muc(K.kiem_phieu(_tay(UV1_SPEC), SO_RONG), "QUA_GAN_BAN_CHAY")
    assert m["do"] == pytest.approx(0.30, abs=1e-3)


# ── 5. mục 4 TRUNG_LAP ───────────────────────────────────────────────────────────────────────────────────

def test_MUC4_khai_lai_dung_spec_UV_001_thanh_UV_002_la_REJECT():
    kq = K.kiem_phieu(_tay(UV1_SPEC, "bo_mot", [RR], ma="UV-002"), SO_UV1)
    m = _muc(kq, "TRUNG_LAP")
    assert m["ket_qua"] == K.REJECT and "UV-001" in m["ly_do"] and kq["ket_luan"] == K.REJECT


def test_MUC4_lech_duoi_dung_sai_van_la_trung_lech_0_01_thi_khong():
    gan = _spec(t=0.29415, m=0.29405, v=0.2353, s=0.1765)          # |Δw| = 5e-5
    xa = _spec(t=0.3041, m=0.2841, v=0.2353, s=0.1765)             # |Δw| = 0,01, cùng tập thành phần
    assert _ket(K.kiem_phieu(_tay(gan, ma="UV-002"), SO_UV1), "TRUNG_LAP") == K.REJECT
    m = _muc(K.kiem_phieu(_tay(xa, ma="UV-002"), SO_UV1), "TRUNG_LAP")
    assert m["ket_qua"] == K.PASS, "một dòng cùng họ chưa đủ (cần ≥ 2); và 0,01 không phải trùng"


def test_MUC4_cung_tap_thanh_phan_duong_voi_tu_2_dong_la_REVISE_voi_1_dong_la_PASS():
    a = _spec(t=0.4, m=0.2, v=0.2, s=0.2)
    b = _spec(t=0.2, m=0.4, v=0.2, s=0.2)
    ung = _spec(t=0.3, m=0.3, v=0.2, s=0.2)
    m2 = _muc(K.kiem_phieu(_tay(ung, ma="UV-009"), _so(**{"UV-007": a, "UV-008": b})), "TRUNG_LAP")
    m1 = _muc(K.kiem_phieu(_tay(ung, ma="UV-009"), _so(**{"UV-007": a})), "TRUNG_LAP")
    assert m2["ket_qua"] == K.REVISE and sorted(m2["do"]["cung_ho"]) == ["UV-007", "UV-008"]
    assert m1["ket_qua"] == K.PASS
    assert m1["do"] == {"trung": [], "cung_ho": ["UV-007"]}


def test_MUC4_dong_KHAC_ho_hay_trong_so_0_khong_tinh_la_cung_ho():
    a = _spec(t=0.4, m=0.2, v=0.2, s=0.1, r=0.1)                   # có risk: tập khác
    b = _spec(t=0.3, m=0.3, v=0.2, s=0.2, r=0.0)                   # r = 0 KHÔNG dương: tập = {t m v s}
    c = _spec(t=0.2, m=0.4, v=0.2, s=0.1, r=0.1)
    ung = _spec(t=0.3, m=0.3, v=0.2, s=0.2)
    kq = K.kiem_phieu(_tay(ung, ma="UV-009"), _so(**{"UV-006": a, "UV-007": c, "UV-008": b}))
    m = _muc(kq, "TRUNG_LAP")
    assert m["ket_qua"] == K.REJECT and m["do"]["trung"] == ["UV-008"], "b trùng ung (r = 0 ≡ vắng)"
    ung2 = _spec(t=0.35, m=0.25, v=0.2, s=0.2)
    m = _muc(K.kiem_phieu(_tay(ung2, ma="UV-009"), _so(**{"UV-006": a, "UV-007": c, "UV-008": b})), "TRUNG_LAP")
    assert m["ket_qua"] == K.PASS and m["do"]["cung_ho"] == ["UV-008"]


def test_MUC4_so_voi_cac_dong_KHAC_tru_chinh_no_va_khong_co_ma_thi_so_voi_moi_dong():
    assert _ket(K.kiem_phieu(PHIEU_UV1, SO_UV1), "TRUNG_LAP") == K.PASS            # ma = UV-001: bỏ chính nó
    khong_ma = {k: v for k, v in PHIEU_UV1.items() if k != "ma"}
    assert _ket(K.kiem_phieu(khong_ma, SO_UV1), "TRUNG_LAP") == K.REJECT            # không khai mã: dòng ấy là "khác"
    assert _ket(K.kiem_phieu(khong_ma, SO_RONG), "TRUNG_LAP") == K.PASS


def test_MUC4_so_hu_thi_NO_ValueError():
    for so in [{}, {"ung_vien": []}, _so(**{"UV-001": UV1_SPEC}) | {"ung_vien": {"UV-001": {"spec": {}}}}]:
        with pytest.raises(ValueError):
            K.kiem_phieu(PHIEU_UV1, so)


# ── 6. mục 5 KHAI_BAT_BUOC ───────────────────────────────────────────────────────────────────────────────

def test_MUC5_da_doc_ket_qua_som_true_la_REJECT_du_cac_muc_khac_deu_PASS():
    p = dict(PHIEU_UV1, da_doc_ket_qua_som=True)
    kq = K.kiem_phieu(p, SO_UV1)
    assert [m["ket_qua"] for m in kq["muc"]] == [K.PASS, K.PASS, K.PASS, K.PASS, K.REJECT]
    assert kq["ket_luan"] == K.REJECT and "HANDOFF" in _muc(kq, "KHAI_BAT_BUOC")["ly_do"]


def test_MUC5_bo_ngo_mot_trong_hai_truong_khai_la_REVISE_khong_phai_PASS():
    khong_doc = {k: v for k, v in PHIEU_UV1.items() if k != "da_doc_ket_qua_som"}
    kq = K.kiem_phieu(khong_doc, SO_UV1)
    assert _ket(kq, "KHAI_BAT_BUOC") == K.REVISE and kq["ket_luan"] == K.REVISE
    khong_dx = {k: v for k, v in PHIEU_UV1.items() if k != "dan_xuat"}
    kq = K.kiem_phieu(khong_dx, SO_UV1)
    assert kq["ket_luan"] == K.REVISE and _ket(kq, "KHAI_BAT_BUOC") == K.REVISE
    # thiếu dan_xuat thì mục 1 và 2 KHÔNG thể kiểm: không được ghi PASS im lặng
    assert _ket(kq, "THAM_SO_TU_DO") == K.REVISE and _ket(kq, "DO_CHINH_XAC") == K.REVISE
    trang = {"spec": UV1_SPEC}
    assert K.kiem_phieu(trang, SO_RONG)["ket_luan"] == K.REVISE
    ca_hai = dict(trang, da_doc_ket_qua_som=True)
    assert K.kiem_phieu(ca_hai, SO_RONG)["ket_luan"] == K.REJECT, "thiếu dan_xuat + đã đọc sớm: nặng nhất thắng"


@pytest.mark.parametrize("gia_tri", ["false", "true", 0, 1, [], {}, "", "False"])
def test_MUC5_da_doc_ket_qua_som_khong_phai_bool_thi_NO_ValueError(gia_tri):
    """Chuỗi "false" là truthy: không được đoán nghĩa."""
    with pytest.raises(ValueError):
        K.kiem_phieu(dict(PHIEU_UV1, da_doc_ket_qua_som=gia_tri), SO_UV1)


def test_PHIEU_khong_phai_dict_hay_thieu_spec_thi_NO_ValueError():
    for p in [None, [], "x", {}, {"dan_xuat": {"loai": "tay", "tham_so": []}, "da_doc_ket_qua_som": False}]:
        with pytest.raises(ValueError):
            K.kiem_phieu(p, SO_RONG)


# ── 7. ket_luan = mục NẶNG NHẤT ──────────────────────────────────────────────────────────────────────────

def test_KET_LUAN_la_muc_nang_nhat_REJECT_hon_REVISE_hon_PASS():
    reject_va_revise = K.kiem_phieu(_tay(_spec(t=0.22, m=0.24, v=0.21, s=0.17, r=0.16)), SO_RONG)
    assert {m["ket_qua"] for m in reject_va_revise["muc"]} >= {K.REJECT, K.REVISE}
    assert reject_va_revise["ket_luan"] == K.REJECT                  # mục 1 REJECT, 2 REVISE, 3 REVISE
    chi_revise = K.kiem_phieu(_tay(_spec(t=0.52, m=0.48)), SO_RONG)
    assert {m["ket_qua"] for m in chi_revise["muc"]} == {K.PASS, K.REVISE} and chi_revise["ket_luan"] == K.REVISE
    chi_pass = K.kiem_phieu(PHIEU_UV1, SO_UV1)
    assert {m["ket_qua"] for m in chi_pass["muc"]} == {K.PASS} and chi_pass["ket_luan"] == K.PASS
    revise_o_cuoi = K.kiem_phieu(dict(PHIEU_UV1, da_doc_ket_qua_som=True), SO_UV1)    # REJECT ở mục CUỐI
    assert revise_o_cuoi["ket_luan"] == K.REJECT


def test_KET_QUA_khong_doi_phieu_cung_nhu_so_dau_vao_va_chay_hai_lan_cho_cung_chu():
    p, s = copy.deepcopy(PHIEU_UV1), copy.deepcopy(SO_UV1)
    a = K.kiem_phieu(p, s)
    assert p == PHIEU_UV1 and s == SO_UV1
    assert K.kiem_phieu(p, s) == a


# ── 8. đối chứng THẬT: UV-001 trên sổ thật, file không đổi một byte ───────────────────────────────────────

def _bam(duong):
    return hashlib.sha256(duong.read_bytes()).hexdigest()


def test_DOI_CHUNG_THAT_UV_001_tren_so_that_PASS_cac_muc_1_2_3_5_va_FILE_SO_khong_doi_mot_byte():
    """Nếu bảng kiểm đỏ ở UV-001 thì bảng kiểm sai, không phải UV-001 (đặc tả mục 2)."""
    truoc = _bam(SO_THAT)
    so = cb.doc_so_ung_vien()
    d = so["ung_vien"]["UV-001"]
    kq = K.kiem_phieu({"ma": "UV-001", "spec": d["spec"], "dan_xuat": {"loai": "bo_mot", "tham_so": [RR]},
                       "da_doc_ket_qua_som": False}, so)
    for ten in ("THAM_SO_TU_DO", "DO_CHINH_XAC", "QUA_GAN_BAN_CHAY", "KHAI_BAT_BUOC"):
        assert _ket(kq, ten) == K.PASS, ten
    assert _muc(kq, "THAM_SO_TU_DO")["do"] == 0
    assert _muc(kq, "QUA_GAN_BAN_CHAY")["do"] == pytest.approx(0.30, abs=1e-3)
    assert _bam(SO_THAT) == truoc
    assert so == cb.doc_so_ung_vien(), "sổ trong bộ nhớ cũng không đổi"


def test_DOI_CHUNG_THAT_dong_UV_001_cua_so_that_dung_mot_minh_cho_PASS_toan_bang():
    """Dòng THẬT của UV-001 đặt vào một sổ chỉ có nó: cả năm mục PASS (mục 4 không còn phụ thuộc dòng khai sau)."""
    thang = {"ung_vien": {"UV-001": cb.doc_so_ung_vien()["ung_vien"]["UV-001"]}}
    kq = K.kiem_phieu({"ma": "UV-001", "spec": thang["ung_vien"]["UV-001"]["spec"],
                       "dan_xuat": {"loai": "bo_mot", "tham_so": [RR]}, "da_doc_ket_qua_som": False}, thang)
    assert [m["ket_qua"] for m in kq["muc"]] == [K.PASS] * 5 and kq["ket_luan"] == K.PASS


def test_DOI_CHUNG_THAT_khai_lai_UV_001_thanh_UV_002_tren_so_that_la_REJECT():
    so = cb.doc_so_ung_vien()
    kq = K.kiem_phieu({"ma": "UV-DOI-CHUNG", "spec": so["ung_vien"]["UV-001"]["spec"],
                       "dan_xuat": {"loai": "bo_mot", "tham_so": [RR]}, "da_doc_ket_qua_som": False}, so)
    assert _ket(kq, "TRUNG_LAP") == K.REJECT and kq["ket_luan"] == K.REJECT


# ── 9. công cụ dòng lệnh ─────────────────────────────────────────────────────────────────────────────────

def _ghi(tmp_path, ten, doi_tuong):
    p = tmp_path / ten
    p.write_text(json.dumps(doi_tuong, ensure_ascii=False), encoding="utf-8")
    return p


def test_CLI_ma_thoat_0_PASS_1_REVISE_3_REJECT_va_in_tung_muc(tmp_path, capsys):
    so = _ghi(tmp_path, "so.json", SO_UV1)
    cac = [(_tay(T.spec_z(), "doi_cho", [TT, SS], ma="UV-002"), 0, "PASS"),
           (_tay(_spec(t=0.52, m=0.48), ma="UV-002"), 1, "REVISE"),
           (dict(PHIEU_UV1, ma="UV-002"), 3, "REJECT")]
    for phieu, ma, chu in cac:
        f = _ghi(tmp_path, "phieu.json", phieu)
        assert CLI.main([str(f), "--so", str(so)]) == ma
        ra = capsys.readouterr().out
        for ten in ("THAM_SO_TU_DO", "DO_CHINH_XAC", "QUA_GAN_BAN_CHAY", "TRUNG_LAP", "KHAI_BAT_BUOC"):
            assert ten in ra, ten
        assert f"KET LUAN: {chu}" in ra
        assert ra.count("số liệu thô:") == 5, "dữ liệu THÔ in ngay dưới từng mục (SKILL Bước 3, điều 4)"
        assert "chỉ in" in ra, "dòng nhắc: không chặn, không ghi sổ, không mở khoá"


def test_CLI_ma_thoat_2_khi_chua_kiem_duoc_va_KHONG_in_chu_ket_luan(tmp_path, capsys):
    so = _ghi(tmp_path, "so.json", SO_UV1)
    hu = tmp_path / "hu.json"
    hu.write_text("{khong phai json", encoding="utf-8")
    cac = [[str(tmp_path / "khong_co.json"), "--so", str(so)], [str(hu), "--so", str(so)],
           [str(_ghi(tmp_path, "ok.json", PHIEU_UV1)), "--so", str(tmp_path / "khong_co_so.json")],
           [str(_ghi(tmp_path, "dx.json", dict(PHIEU_UV1, dan_xuat={"loai": "la", "tham_so": []}))), "--so", str(so)],
           [str(_ghi(tmp_path, "bool.json", dict(PHIEU_UV1, da_doc_ket_qua_som="false"))), "--so", str(so)]]
    for lenh in cac:
        assert CLI.main(lenh) == 2, lenh
        ra = capsys.readouterr()
        assert "KET LUAN" not in ra.out and "CHUA KIEM DUOC" in ra.err


def test_CLI_mac_dinh_doc_so_that_va_khong_doi_mot_byte_cua_so_hay_phieu(tmp_path, capsys):
    f = _ghi(tmp_path, "phieu.json", PHIEU_UV1)
    truoc_so, truoc_phieu, truoc_thu_muc = _bam(SO_THAT), _bam(f), sorted(p.name for p in tmp_path.iterdir())
    ma = CLI.main([str(f)])
    ra = capsys.readouterr().out
    assert ma in (0, 1, 3) and "KET LUAN:" in ra
    assert CLI.SO_MAC_DINH == SO_THAT
    assert _bam(SO_THAT) == truoc_so and _bam(f) == truoc_phieu
    assert sorted(p.name for p in tmp_path.iterdir()) == truoc_thu_muc, "công cụ không ghi file nào"


def test_CLI_chay_duoc_nhu_script_va_ma_thoat_di_qua_tien_trinh(tmp_path):
    so = _ghi(tmp_path, "so.json", SO_UV1)
    f = _ghi(tmp_path, "phieu.json", dict(PHIEU_UV1, ma="UV-002"))
    r = subprocess.run([sys.executable, "-X", "utf8", str(DUONG_CLI), str(f), "--so", str(so)],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(tmp_path))
    assert r.returncode == 3 and "KET LUAN: REJECT" in r.stdout, (r.returncode, r.stdout, r.stderr)


# ── 10. gác AST: bảng kiểm không đọc kết quả, không ghi, không ai nhập nó ───────────────────────────────

#: Thứ DUY NHẤT module được nhập (đặc tả mục 3 khoản 4).
NHAP_CHO_PHEP = {"__future__", "json", "dataclasses", "pathlib", "typing"}
#: Lời gọi cấm: ghi đĩa, đồng hồ, mạng, tiến trình. Module chỉ tính trên dict nó nhận.
GOI_CAM = {"open", "write_text", "write_bytes", "dump", "mkdir", "unlink", "rename", "touch", "remove", "rmtree",
           "system", "Popen", "run", "check_output", "urlopen", "now", "today", "sleep"}
CAM_NHAP = {"cham_bong", "cham_xac_nhan", "vong_hoc_gia", "master_agent", "run_daily", "sheets_store",
            "experiment_tran_dac_trung", "thi_truong_gia", "paper_trading", "paper_runner", "paper_metrics"}


def _nhap_va_goi(nguon: str) -> tuple[set, set]:
    nhap, goi = set(), set()
    for n in ast.walk(ast.parse(nguon)):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
        elif isinstance(n, ast.Call):
            goi.add(n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", ""))
    return nhap, goi


def test_G1_PHEP_DO_bat_duoc_nhap_cam_va_loi_goi_ghi():
    for xau in ["import cham_xac_nhan", "from cham_bong import so_cap", "import paper_trading as p",
                "def f():\n    import sheets_store", "import experiment_tran_dac_trung"]:
        nhap, _ = _nhap_va_goi(xau)
        assert nhap - NHAP_CHO_PHEP, xau
    for xau in ['open("f", "w")', 'Path("x").write_text("y")', "json.dump(x, f)", "datetime.now()"]:
        _, goi = _nhap_va_goi(xau)
        assert goi & GOI_CAM, xau
    for tot in ["import json\nfrom pathlib import Path", 'x = json.dumps({})', "max(a, key=f)"]:
        nhap, goi = _nhap_va_goi(tot)
        assert not (nhap - NHAP_CHO_PHEP) and not (goi & GOI_CAM), tot


def test_G1_module_chi_nhap_thu_chuan_cho_phep_va_khong_ghi_khong_dong_ho_khong_mang():
    nhap, goi = _nhap_va_goi(DUONG_MODULE.read_text(encoding="utf-8"))
    assert nhap <= NHAP_CHO_PHEP, sorted(nhap - NHAP_CHO_PHEP)
    assert not (nhap & CAM_NHAP)
    assert not (goi & GOI_CAM), sorted(goi & GOI_CAM)


def test_G1_cong_cu_dong_lenh_cung_khong_ghi_va_khong_nhap_phep_cham():
    nhap, goi = _nhap_va_goi(DUONG_CLI.read_text(encoding="utf-8"))
    assert not (nhap & CAM_NHAP), sorted(nhap & CAM_NHAP)
    assert not (goi & GOI_CAM), sorted(goi & GOI_CAM)
    assert "kiem_de_xuat" in nhap


def test_G2_khong_module_nao_nhap_kiem_de_xuat_tru_cong_cu_dong_lenh_va_test_nay():
    """Đảo chiều: nó không đi vào `vong_hoc_gia` (đổi phép đo T6), `cham_bong` (phép chấm), `paper_*`, `run_daily`."""
    ra = set()
    for p in duyet_repo.duyet(GOC, "*.py"):
        rel = p.relative_to(GOC)
        if rel.parts[0] in {".venv", ".git"} or rel.as_posix() == "kiem_de_xuat.py":
            continue
        nhap, _ = _nhap_va_goi(p.read_text(encoding="utf-8"))
        if "kiem_de_xuat" in nhap:
            ra.add(rel.as_posix())
    assert ra == {"tools/kiem_phieu_de_xuat.py", "tests/test_kiem_de_xuat.py"}, sorted(ra)
    for ten in ["cham_bong.py", "cham_xac_nhan.py", "vong_hoc_gia.py", "master_agent.py", "run_daily.py",
                "sheets_store.py", *[p.name for p in GOC.glob("paper_*.py")]]:
        assert ten not in ra, ten


def test_G3_module_khong_la_cua_vao_ung_vien_khong_ghi_so_va_khong_tu_goi_phan_quyet():
    nguon = DUONG_MODULE.read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    ten_dung = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
    assert not (ten_dung & {"phan_quyet", "so_cap", "cham", "nguong", "MOC_DOC", "MIN_MA", "ma_tran_cap",
                            "khai_ung_vien", "qua_sang"}), sorted(ten_dung)
