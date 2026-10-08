"""Gác MỐC ĐỌC của vòng xác nhận — BƯỚC 162.

Người dùng chọn 07/10/2026 *"Một mốc cố định"*: vòng xác nhận chỉ phán MỘT lần, khi đủ
252 phiên CÓ NHÃN, trên ĐÚNG 252 phiên có nhãn đầu tiên. Trước mốc app và CLI chỉ hiện
tiến độ n/252; Δ/p/z không được tính hay trả ra.

File này chạy với mốc THẬT (252) — KHÔNG thu nhỏ — và dữ liệu GIẢ dựng trong test (không
đọc dữ liệu thật, không mạng, không `backtest/cache*`). `tests/test_cham_xac_nhan.py` chạy
với mốc thu nhỏ để nhanh; hằng số thật chỉ được ghim ở đây.

Ca QUAN TRỌNG NHẤT: thêm phiên SAU mốc không đổi kết quả (`test_THEM_PHIEN_SAU_MOC_...`).
Đột biến đầu tiên của file này: đổi "252 phiên ĐẦU" thành "mọi phiên tới nay" (bỏ lệnh cắt
trong `cham_bong.ma_tran_cap`) — gác phải đỏ.

LỆNH TÁI LẬP các số hiệu chuẩn trên dữ liệu GIẢ (cwd là gốc repo; 20 hạt dữ liệu 0–19,
400 lượt hoán vị, 252 phiên × 45 mã, ứng viên chỉ gồm `volume_score`; tín hiệu tiêm vào
NHÃN với hệ số `gamma` trên log-lợi-nhuận 21 phiên):

    ./.venv/Scripts/python.exe -c "import sys; sys.path[:0]=['.','tests']; import test_moc_doc as t; print(t._tron252(gamma=0.012), t._tron252(gamma=0.0), t._tron252(gamma=0.002), t._tron252(gamma=0.012, ghi_tiem=True, spec=t._spec(trend_score=1.0)))"

Các NGƯỠNG trong test (≥ 9/10 · ≤ 4/20 · 5–19 · ≥ 9/10 với QUA = 0) được chọn SAU khi thấy
các số ấy — đây là gác về DỤNG CỤ trên dữ liệu giả, không phải tiêu chí ký trước về thị
trường.
"""
import ast
import copy
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tests"))

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402
import lich_giao_dich as lich  # noqa: E402
from test_cham_xac_nhan import _cli, _so_uv, _spec, dung  # noqa: E402

KEO_DAI = "2030-01-01T16:30:00+07:00"      # sau phiên cuối của mọi bảng ở file này
MOC = 252


def _dung(W, M=45, hat=0, gamma=0.0, **kw):
    return dung(W=W, M=M, hat=hat, gamma=gamma, keo=KEO_DAI, **kw)


def _cham(rows, uv, bg, so=200, ma="UV-T"):
    return cx.cham(rows, uv, bg, so=so)["chi_tiet"][ma]


def _uv_dau(cal, spec=None, i=0):
    return _so_uv(cal[i], spec or _spec(volume_score=1.0))


def _cat(rows, bg, cal, ma, n_qd):
    """Bản CẮT của cùng dữ liệu: chỉ `n_qd` phiên quyết định đầu và bảng giá đúng tới
    T+22 của phiên cuối. Cắt (slice), không dựng lại — hạt ngẫu nhiên đổi theo kích thước."""
    giu = set(cal[:n_qd])
    r2 = [r for r in rows if r["signal_date"] in giu]
    g2 = bg["gia"].iloc[:n_qd + cb.NHIP + 1]
    bg2 = cx.phan_tich_bang_gia(cx.dinh_dang_bang_gia(g2, KEO_DAI, bg["nguon"]))
    return r2, bg2


# ── 1. hằng số ghim literal ──────────────────────────────────────────────

def test_HANG_SO_moc_doc_va_cac_hang_so_KHONG_doi_ghim_literal():
    assert cb.MOC_DOC == 252
    assert cb.CHUA_TOI_MOC == "CHUA TOI MOC"
    assert (cb.NHIP, cb.ALPHA, cb.MIN_MA) == (21, 0.05, 40)     # BƯỚC 162 không đổi ba hằng số này
    assert cb.MOC_DOC >= cb.NHIP
    assert cb.TRANG_THAI_HIEN["CHUA TOI MOC"] == "Chưa tới mốc đọc"
    assert cx.BIEN_KHAI_NGAY == ">=" and cx.HAT_RNG == 20261007 and cx.SO_HOAN_VI == 2000


# ── 2. TRƯỚC mốc: không chạy so_cap, không có Δ/p/z ───────────────────────

def _spy_so_cap(monkeypatch):
    goi = []
    that = cb.so_cap

    def spy(B, C, Y, rng, so=2000):
        goi.append(B.shape)
        return that(B, C, Y, rng, so=so)
    monkeypatch.setattr(cb, "so_cap", spy)
    return goi


def test_TRUOC_MOC_so_cap_KHONG_chay_va_KHONG_co_delta_p_z(monkeypatch):
    goi = _spy_so_cap(monkeypatch)
    rows, bg, cal, ma = _dung(W=MOC - 1, gamma=0.012)
    c = _cham(rows, _uv_dau(cal), bg)
    assert goi == []                                            # phép so KHÔNG được gọi
    assert c["trang_thai"] == "CHUA TOI MOC" and c["ket"] is None
    assert not {"delta", "p", "z"} & set(c), sorted(c)          # không phải NaN-nhưng-đã-tính
    assert (c["n_phien"], c["n_phien_co_nhan"], c["moc_doc"]) == (MOC - 1, MOC - 1, MOC)


def test_DUNG_toi_moc_so_cap_chay_DUNG_MOT_lan_tren_252_phien(monkeypatch):
    goi = _spy_so_cap(monkeypatch)
    rows, bg, cal, ma = _dung(W=MOC, gamma=0.012)
    c = _cham(rows, _uv_dau(cal), bg)
    assert goi == [(MOC, 45)]
    assert c["trang_thai"] == "QUA" and set(c) >= {"delta", "p", "z"} and c["ket"] is not None


def test_MOC_dem_phien_CO_NHAN_khong_phai_phien_co_dong_quyet_dinh():
    """252 phiên quyết định nhưng bảng giá thiếu T+22 của phiên cuối → chỉ 251 có nhãn →
    CHUA TOI MOC. Đủ T+22 → tới mốc."""
    rows, bg, cal, ma = _dung(W=MOC, N=MOC + cb.NHIP)          # thiếu đúng một phiên giá
    c = _cham(rows, _uv_dau(cal), bg)
    assert (c["n_phien"], c["n_phien_quyet_dinh"]) == (MOC - 1, MOC)
    assert c["trang_thai"] == "CHUA TOI MOC" and c["phien_chua_co_nhan"] == cal[MOC - 1:MOC]
    rows, bg, cal, ma = _dung(W=MOC, N=MOC + cb.NHIP + 1)
    c = _cham(rows, _uv_dau(cal), bg)
    assert (c["n_phien"], c["trang_thai"] != "CHUA TOI MOC") == (MOC, True)


# ── 3. ĐÚNG 252 phiên ĐẦU: thêm phiên sau mốc KHÔNG đổi kết quả ───────────

def _so_sanh_hai_ket_qua(a, b):
    ka, kb = a["ket"], b["ket"]
    assert a["n_phien"] == b["n_phien"] == MOC
    assert a["n_ma"] == b["n_ma"] and a["trang_thai"] == b["trang_thai"]
    assert (a["delta"], a["p"], a["z"]) == (b["delta"], b["p"], b["z"])
    assert np.array_equal(ka["null"], kb["null"])               # CÙNG hạt → cùng từng giá trị null


@pytest.mark.parametrize("W_tong", [MOC + 1, MOC + 48])
def test_THEM_PHIEN_SAU_MOC_khong_doi_ket_qua(W_tong):
    """Ca quan trọng nhất. Dữ liệu dài hơn chứa NGUYÊN các phiên đầu; ket quả phải
    giống hệt từng chữ số — không phải 'gần giống'."""
    rows, bg, cal, ma = _dung(W=W_tong, gamma=0.004)
    uv = _uv_dau(cal)
    r_cat, bg_cat = _cat(rows, bg, cal, ma, MOC)
    ngan = _cham(r_cat, uv, bg_cat)
    dai = _cham(rows, uv, bg)
    _so_sanh_hai_ket_qua(ngan, dai)
    assert dai["n_phien_co_nhan"] == W_tong and ngan["n_phien_co_nhan"] == MOC
    assert dai["n_phien_quyet_dinh"] == W_tong                  # dữ liệu dài thật sự dài hơn


def test_phien_SAU_moc_thieu_mot_ma_khong_lam_roi_ma_ay_khoi_252_phien_dau():
    """Cắt phải xảy ra TRƯỚC khi chọn mã đầy đủ. Cắt sau thì một mã vắng ở phiên 260
    bị loại khỏi `du` và ĐỔI kết quả của chính 252 phiên đã đọc."""
    rows, bg, cal, ma = _dung(W=MOC + 30, gamma=0.004)
    uv = _uv_dau(cal)
    r_cat, bg_cat = _cat(rows, bg, cal, ma, MOC)
    ngan = _cham(r_cat, uv, bg_cat)
    sau = set(cal[MOC + 8:])
    thieu = [r for r in rows if not (r["symbol"] == "M05" and r["signal_date"] in sau)]
    assert len(thieu) == len(rows) - 22
    dai = _cham(thieu, uv, bg)
    assert dai["n_ma"] == 45                                    # M05 còn đủ trong 252 phiên đầu
    _so_sanh_hai_ket_qua(ngan, dai)


def test_phien_SAU_moc_dong_hong_hay_gia_la_khong_doi_ket_qua_252_phien_dau():
    rows, bg, cal, ma = _dung(W=MOC + 30, gamma=0.004)
    uv = _uv_dau(cal)
    r_cat, bg_cat = _cat(rows, bg, cal, ma, MOC)
    ngan = _cham(r_cat, uv, bg_cat)
    hong = copy.deepcopy(rows)
    sau = set(cal[MOC + 3:])
    for r in hong:
        if r["signal_date"] in sau and r["symbol"] in ("M01", "M02"):
            r["components"] = "khong phai JSON"                 # dòng hỏng SAU mốc
    gia = bg["gia"].copy()
    gia.iloc[MOC + cb.NHIP + 1:] *= 3.0                         # giá SAU T+22 của phiên mốc đổi hẳn
    bg3 = cx.phan_tich_bang_gia(cx.dinh_dang_bang_gia(gia, KEO_DAI, bg["nguon"]))
    dai = _cham(hong, uv, bg3)
    assert dai["n_dong_bo"] == 2 * 27 and ngan["n_dong_bo"] == 0
    _so_sanh_hai_ket_qua(ngan, dai)


def test_THU_TU_dong_quyet_dinh_trong_tep_khong_doi_ket_qua():
    rows, bg, cal, ma = _dung(W=MOC + 5, gamma=0.004)
    uv = _uv_dau(cal)
    a = _cham(rows, uv, bg)
    xao = list(rows)
    np.random.default_rng(3).shuffle(xao)
    assert xao != rows
    _so_sanh_hai_ket_qua(a, _cham(xao, uv, bg))


def test_DOC_LAI_ve_sau_cho_cung_ket_qua_hat_co_dinh_va_hat_khac_doi_null_khong_doi_delta():
    rows, bg, cal, ma = _dung(W=MOC + 5, gamma=0.004)
    uv = _uv_dau(cal)
    a, b = _cham(rows, uv, bg), _cham(rows, uv, bg)
    _so_sanh_hai_ket_qua(a, b)
    c = cx.cham(rows, uv, bg, hat=cx.HAT_RNG + 1, so=200)["chi_tiet"]["UV-T"]
    assert c["delta"] == a["delta"] and not np.array_equal(c["ket"]["null"], a["ket"]["null"])


def test_252_phien_DAU_tinh_tu_phien_dau_cua_du_lieu_cham_theo_BIEN_khai_ngay(monkeypatch):
    """Phiên đầu của dữ liệu chấm là `tu_ngay_doc(khai_ngay)` (biên `>=`: phiên khai_ngay
    CÓ tính). Khai ở phiên thứ 10 thì 252 phiên là [10, 262); biên `>` đẩy sang [11, 263)."""
    rows, bg, cal, ma = _dung(W=MOC + 40, gamma=0.004)
    uv = _uv_dau(cal, i=10)

    def doan(lo):
        giu = set(cal[lo:lo + MOC])
        r2 = [r for r in rows if r["signal_date"] in giu]
        g2 = bg["gia"].iloc[lo:lo + MOC + cb.NHIP + 1]
        return r2, cx.phan_tich_bang_gia(cx.dinh_dang_bang_gia(g2, KEO_DAI, bg["nguon"]))
    a = _cham(rows, uv, bg)
    assert a["tu_ngay"] == cal[10]
    r2, bg2 = doan(10)
    _so_sanh_hai_ket_qua(a, _cham(r2, uv, bg2))
    monkeypatch.setattr(cx, "BIEN_KHAI_NGAY", ">")
    b = _cham(rows, uv, bg)
    assert cal[10] < b["tu_ngay"] <= cal[11]                    # ngày kế khai_ngay (có thể là cuối tuần)
    r3, bg3 = doan(11)
    _so_sanh_hai_ket_qua(b, _cham(r3, uv, bg3))                 # cùng `uv` (khai cal[10]), biên `>`
    assert a["delta"] != b["delta"]                             # hai biên là hai tập phiên khác nhau


# ── 4. ma_tran_cap(phien_toi_da) và phan_quyet ───────────────────────────

def _bang_nho(sessions, ma, vang=()):
    """Bảng quyết định giả: mọi (mã, phiên), trừ các cặp trong `vang`."""
    rng = np.random.default_rng(0)
    ra = []
    for s in sessions:
        for m in ma:
            if (m, s) in vang:
                continue
            tp = {k: float(rng.uniform(0, 100)) for k in cb.THANH_PHAN}
            ra.append({"symbol": m, "ngay": s, "score": float(rng.uniform(0, 100)), **tp})
    return pd.DataFrame(ra)


def _nhan_nho(sessions, ma, nan_phien=()):
    rng = np.random.default_rng(1)
    y = pd.DataFrame(rng.standard_normal((len(sessions), len(ma))), index=sessions, columns=ma)
    for s in nan_phien:
        y.loc[s] = np.nan
    return y


SP = {"loai": "trong_so", "trong_so": {"volume_score": 1.0}}
PH = [f"2026-11-{d:02d}" for d in range(2, 12)]                  # 10 phiên liên tiếp (không phải lịch thật)
MA = ["A", "B", "C", "D"]


def test_ma_tran_cap_phien_toi_da_giu_N_phien_co_nhan_DAU_TIEN():
    b, y = _bang_nho(PH, MA), _nhan_nho(PH, MA)
    B, C, Y, phien, ma = cb.ma_tran_cap(b, SP, y, phien_toi_da=4)
    assert phien == PH[:4] and B.shape == C.shape == Y.shape == (4, 4) and ma == MA
    assert cb.ma_tran_cap(b, SP, y)[3] == PH                     # không tham số: không cắt (vòng sàng cũ)


def test_ma_tran_cap_cat_SAU_khi_bo_phien_chua_co_nhan_va_TRUOC_khi_chon_ma():
    # phiên đầu không có nhãn: không được đếm vào N phiên
    b, y = _bang_nho(PH, MA), _nhan_nho(PH, MA, nan_phien=[PH[0]])
    assert cb.ma_tran_cap(b, SP, y, phien_toi_da=3)[3] == PH[1:4]
    # mã D vắng ở phiên thứ 6: cắt ở 4 thì D còn; không cắt thì D bị loại
    b = _bang_nho(PH, MA, vang={("D", PH[5])})
    y = _nhan_nho(PH, MA)
    assert cb.ma_tran_cap(b, SP, y, phien_toi_da=4)[4] == MA
    assert cb.ma_tran_cap(b, SP, y)[4] == ["A", "B", "C"]


def test_phan_quyet_chi_chay_so_cap_o_DUNG_moc_va_du_ma(monkeypatch):
    monkeypatch.setattr(cb, "MOC_DOC", 6)
    goi = _spy_so_cap(monkeypatch)
    ma40 = [f"M{i:02d}" for i in range(cb.MIN_MA)]
    y = _nhan_nho(PH, ma40)
    q = cb.phan_quyet(_bang_nho(PH[:5], ma40), SP, y, 0.05, hat=1, so=20)
    assert goi == [] and q["trang_thai"] == "CHUA TOI MOC" and q["ket"] is None
    assert (q["n_phien"], q["n_ma"]) == (5, cb.MIN_MA)
    q = cb.phan_quyet(_bang_nho(PH, ma40), SP, y, 0.05, hat=1, so=20)           # 10 phiên > mốc 6
    assert goi == [(6, cb.MIN_MA)] and q["n_phien"] == 6 and q["ket"] is not None
    goi.clear()
    ma39 = ma40[:-1]
    q = cb.phan_quyet(_bang_nho(PH, ma39), SP, _nhan_nho(PH, ma39), 0.05, hat=1, so=20)
    assert goi == [] and q["trang_thai"] == "CHUA DU DU LIEU" and q["ket"] is None


def test_phan_quyet_dung_RNG_moi_moi_lan_nen_chay_lai_cho_cung_null(monkeypatch):
    monkeypatch.setattr(cb, "MOC_DOC", 6)
    ma40 = [f"M{i:02d}" for i in range(cb.MIN_MA)]
    b, y = _bang_nho(PH, ma40), _nhan_nho(PH, ma40)
    a = cb.phan_quyet(b, SP, y, 0.05, hat=9, so=30)["ket"]
    c = cb.phan_quyet(b, SP, y, 0.05, hat=9, so=30)["ket"]
    d = cb.phan_quyet(b, SP, y, 0.05, hat=10, so=30)["ket"]
    assert np.array_equal(a["null"], c["null"]) and not np.array_equal(a["null"], d["null"])
    # hạt THẬT sự là `hat` (không lệch một đơn vị, không bỏ): dựng lại phép so bằng tay
    B, C, Y, _, _ = cb.ma_tran_cap(b, SP, y, phien_toi_da=6)
    tay = cb.so_cap(B, C, Y, np.random.default_rng(9), so=30)
    assert np.array_equal(a["null"], tay["null"]) and a["delta"] == tay["delta"] and a["p"] == tay["p"]


# ── 5. trang_thai: hai đầu của mốc ───────────────────────────────────────

def test_trang_thai_TU_CHOI_phan_quyet_tinh_tren_so_phien_khac_moc():
    ket = {"delta": 0.05, "p": 0.0001}
    assert cb.trang_thai(ket, 0.01, cb.MOC_DOC, 60) == "QUA"
    with pytest.raises(ValueError, match=str(cb.MOC_DOC)):
        cb.trang_thai(ket, 0.01, cb.MOC_DOC + 1, 60)             # cửa sổ lớn dần là lần nhìn mới
    assert cb.trang_thai(ket, 0.01, cb.MOC_DOC - 1, 60) == "CHUA TOI MOC"
    assert cb.trang_thai(ket, 0.01, 0, 0) == "CHUA TOI MOC"


def test_trang_thai_truoc_moc_KHONG_doc_ket_va_toi_moc_thieu_ket_thi_NO():
    assert cb.trang_thai(None, 0.01, cb.MOC_DOC - 1, 60) == "CHUA TOI MOC"
    assert cb.trang_thai({}, 0.01, 10, 60) == "CHUA TOI MOC"      # `{}["p"]` sẽ KeyError nếu bị đọc
    assert cb.trang_thai(None, 0.01, cb.MOC_DOC, cb.MIN_MA - 1) == "CHUA DU DU LIEU"
    with pytest.raises(ValueError, match="khong co ket qua"):
        cb.trang_thai(None, 0.01, cb.MOC_DOC, cb.MIN_MA)


def test_trang_thai_ranh_gioi_ma_o_dung_MIN_MA():
    ket = {"delta": 0.05, "p": 0.0001}
    assert cb.trang_thai(ket, 0.01, cb.MOC_DOC, cb.MIN_MA - 1) == "CHUA DU DU LIEU"
    assert cb.trang_thai(ket, 0.01, cb.MOC_DOC, cb.MIN_MA) == "QUA"


# ── 6. bảng công khai ────────────────────────────────────────────────────

def test_bang_cong_khai_hien_CHUA_TOI_MOC_roi_dich_tieng_Viet_va_tu_choi_n_phien_qua_moc():
    so = {"ung_vien": {"E": {"khai_ngay": "2026-10-02", "mo_ta": "m", "ly_do": "l",
                             "qua_sang": None, "spec": SP}}}
    b = cb.bang_cong_khai(so, ket={"E": (None, 100, 50)})
    assert b.loc[0, "Trạng thái"] == "CHUA TOI MOC"
    assert cb.bang_hien_thi(b).loc[0, "Trạng thái"] == "Chưa tới mốc đọc"
    with pytest.raises(ValueError, match="phien"):
        cb.bang_cong_khai(so, ket={"E": ({"delta": 0.1, "p": 0.0}, cb.MOC_DOC + 1, 50)})


# ── 7. gác AST: MỌI đường tới phán quyết đi qua mốc ───────────────────────

def _file_ma_nguon():
    """Mã nguồn sản phẩm: gốc repo + tools, KHÔNG gồm tests."""
    return sorted(GOC.glob("*.py")) + sorted((GOC / "tools").glob("*.py"))


def _goi(ten):
    """(file tương đối, tên hàm bao ngoài, node) của mọi lời gọi `ten` ở mã sản phẩm."""
    ra = []
    for f in _file_ma_nguon():
        cay = ast.parse(f.read_text(encoding="utf-8"))
        cha = {}
        for n in ast.walk(cay):
            for c in ast.iter_child_nodes(n):
                cha[c] = n

        def ham(n):
            while n in cha:
                n = cha[n]
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return n.name
            return None
        for n in ast.walk(cay):
            if isinstance(n, ast.Call):
                t = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                if t == ten:
                    ra.append((str(f.relative_to(GOC)).replace("\\", "/"), ham(n), n))
    return ra


def test_phan_quyet_la_DUONG_DUY_NHAT_toi_so_cap_cua_vong_xac_nhan():
    """`so_cap` chỉ được gọi trong `cham_bong.phan_quyet` — trừ vòng SÀNG đã ngừng dùng
    (`tools/sang_ung_vien.py`, giữ để ĐO 23 tái lập; nó không phán xác nhận)."""
    vi_tri = {(f, h) for f, h, _ in _goi("so_cap")}
    assert ("cham_bong.py", "phan_quyet") in vi_tri, vi_tri       # không rỗng: gác có thật
    la = {(f, h) for f, h in vi_tri if f not in ("cham_bong.py", "tools/sang_ung_vien.py")}
    assert not la, f"duong tat toi so_cap ngoai phan_quyet: {sorted(la)}"
    assert {h for f, h in vi_tri if f == "cham_bong.py"} == {"phan_quyet"}


def test_ma_tran_cap_chi_goi_voi_phien_toi_da_bang_MOC_DOC_ngoai_vong_sang_cu():
    goi = _goi("ma_tran_cap")
    trong = [(f, h, n) for f, h, n in goi if f != "tools/sang_ung_vien.py"]
    assert [(f, h) for f, h, _ in trong] == [("cham_bong.py", "phan_quyet")], trong
    kw = {k.arg: k.value for k in trong[0][2].keywords}
    assert isinstance(kw.get("phien_toi_da"), ast.Name) and kw["phien_toi_da"].id == "MOC_DOC"


def test_cham_xac_nhan_khong_tu_goi_so_cap_ma_tran_cap_hay_trang_thai():
    cay = ast.parse((GOC / "cham_xac_nhan.py").read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and isinstance(n.func.value, ast.Name) and n.func.value.id == "cb"}
    assert "phan_quyet" in goi
    assert not goi & {"so_cap", "ma_tran_cap", "trang_thai"}, sorted(goi)


def test_KHONG_con_hang_so_252_nao_khac_ngoai_MOC_DOC_trong_ma_san_pham():
    """Một `252` gõ tay ở chỗ khác sẽ trôi ra khỏi `MOC_DOC`. Chỉ một chỗ được có."""
    co = []
    # Chỉ các file của tính năng này: nơi khác (hệ số năm hoá `sqrt(252)`…) có 252 riêng.
    for f in (GOC / "cham_bong.py", GOC / "cham_xac_nhan.py", GOC / "keo_bang_gia.py",
              GOC / "app.py", GOC / "tools" / "cham_xac_nhan.py",
              GOC / "tools" / "keo_bang_gia.py"):
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if (isinstance(n, ast.Constant) and not isinstance(n.value, bool)
                    and n.value == 252 and isinstance(n.value, (int, float))):
                co.append(f.name)
    assert co == ["cham_bong.py"], co


# ── 8. tiến độ theo lịch (app) ───────────────────────────────────────────

def test_TIEN_DO_ranh_gioi_phien_dau_va_22_phien_cuoi_chua_co_nhan():
    # 02/10/2026 (thứ Sáu) là phiên đầu; tháng 10 và 11/2026 không có ngày nghỉ.
    # Phiên: 02/10 (1) + 4 tuần × 5 (05–30/10) = 21 phiên tới hết 30/10; 02/11 là phiên 22.
    cac = {"2026-10-02": 1, "2026-10-05": 2, "2026-10-30": 21, "2026-11-02": 22,
           "2026-11-03": 23, "2026-11-04": 24}
    mong = {"2026-10-02": 0, "2026-10-05": 0, "2026-10-30": 0, "2026-11-02": 0,
            "2026-11-03": 1, "2026-11-04": 2}                  # trừ 22 phiên cuối chưa có nhãn
    for hn, n in cac.items():
        td = cx.tien_do_theo_lich("2026-10-02", hn)
        assert td["tinh_duoc"] and td["n_phien_lich"] == n, (hn, td)
        assert td["n_co_nhan"] == mong[hn] and td["moc"] == cb.MOC_DOC, (hn, td)


def test_TIEN_DO_khai_ngay_roi_vao_ngay_nghi_hoac_cuoi_tuan_va_hom_nay_truoc_khai_ngay():
    td = cx.tien_do_theo_lich("2026-10-03", "2026-10-09")          # thứ Bảy: phiên đầu là 05/10
    assert td["n_phien_lich"] == 5 and td["tinh_duoc"]
    td = cx.tien_do_theo_lich("2026-10-05", "2026-10-02")          # hôm nay TRƯỚC ngày đầu dữ liệu
    assert td["tinh_duoc"] and td["n_phien_lich"] == 0 and td["n_co_nhan"] == 0


def test_TIEN_DO_ngoai_pham_vi_lich_cong_bo_la_CHUA_TINH_DUOC_khong_doan():
    for kn, hn in (("2026-10-02", "2027-01-01"), ("2026-10-02", "2027-06-30"),
                   ("2025-12-31", "2026-03-02")):
        td = cx.tien_do_theo_lich(kn, hn)
        assert td == {"tinh_duoc": False, "n_phien_lich": None, "n_co_nhan": None,
                      "moc": cb.MOC_DOC}, (kn, hn)
        assert "chưa tính được" in cx.nhan_tien_do(td)
    assert cx.tien_do_theo_lich("2026-10-02", "2026-12-31")["tinh_duoc"]     # biên cuối của lịch
    assert cx.tien_do_theo_lich("2026-01-02", "2026-03-02")["tinh_duoc"]     # biên đầu của lịch
    assert "2026-12-31" in cx.nhan_tien_do(cx.tien_do_theo_lich("2026-10-02", "2027-01-01"))


def test_TIEN_DO_so_voi_dem_doc_lap_tung_ngay_lich():
    """Đối chứng độc lập: đếm bằng vòng lặp ngày + `co_phien`, không qua `cac_phien`."""
    kn, hn = "2026-03-02", "2026-12-18"
    d, dem = datetime.date.fromisoformat(kn), 0
    while d <= datetime.date.fromisoformat(hn):
        dem += bool(lich.co_phien(d.isoformat()))
        d += datetime.timedelta(days=1)
    td = cx.tien_do_theo_lich(kn, hn)
    assert td["n_phien_lich"] == dem and td["n_co_nhan"] == dem - (cb.NHIP + 1)


def test_NHAN_tien_do_cat_o_moc_va_noi_ro_theo_lich():
    s = cx.nhan_tien_do({"tinh_duoc": True, "n_phien_lich": 40, "n_co_nhan": 18, "moc": 252})
    assert s == "≈ 18/252 phiên có nhãn (theo lịch)"
    s = cx.nhan_tien_do({"tinh_duoc": True, "n_phien_lich": 300, "n_co_nhan": 278, "moc": 252})
    assert s.startswith("≈ 252/252 phiên có nhãn (theo lịch)") and "đã tới mốc" in s
    assert "đã tới mốc" not in cx.nhan_tien_do(
        {"tinh_duoc": True, "n_phien_lich": 273, "n_co_nhan": 251, "moc": 252})
    assert "đã tới mốc" in cx.nhan_tien_do(
        {"tinh_duoc": True, "n_phien_lich": 274, "n_co_nhan": 252, "moc": 252})


def _uv_so(ngay, qua):
    return {"khai_ngay": ngay, "mo_ta": "m", "ly_do": "l", "qua_sang": qua, "spec": SP}


def test_BANG_TIEN_DO_chi_phuong_an_o_vong_xac_nhan_co_tien_do():
    so = {"ung_vien": {"A": _uv_so("2026-10-02", None),              # từ mốc một vòng
                       "B": _uv_so("2026-09-14", True),              # qua sàng cũ → trong xác nhận
                       "C": _uv_so("2026-09-14", False),             # rớt sàng
                       "D": _uv_so("2026-09-14", None)}}             # chưa sàng
    t = cx.bang_tien_do(so, "2026-10-07")
    assert t["A"] == "≈ 0/252 phiên có nhãn (theo lịch)" and t["B"].startswith("≈ 0/252")
    assert t["C"] == t["D"] == "không áp dụng"
    with pytest.raises(ValueError):
        cx.bang_tien_do({"ung_vien": {"A": {"khai_ngay": "2026-10-02"}}}, "2026-10-07")


def test_BANG_TIEN_DO_cho_so_THAT_moi_phuong_an_co_mot_cau_va_so_khong_doi():
    duong = GOC / "docs" / "ung-vien.json"
    truoc = duong.read_bytes()
    so = cb.doc_so_ung_vien()
    t = cx.bang_tien_do(so, "2026-10-07")
    assert set(t) == set(so["ung_vien"]) and all(isinstance(v, str) and v for v in t.values())
    assert duong.read_bytes() == truoc


def test_TIEN_DO_khong_doc_gia_khong_doc_sheets_AST():
    cay = ast.parse((GOC / "cham_xac_nhan.py").read_text(encoding="utf-8"))
    ham = {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}
    for ten in ("tien_do_theo_lich", "nhan_tien_do", "bang_tien_do"):
        goi = {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(ham[ten])
               if isinstance(n, ast.Call)}
        assert not goi & {"doc_bang_gia", "phan_tich_bang_gia", "doc_dong_quyet_dinh", "cham",
                          "cham_mot", "open", "read_text", "read_csv"}, (ten, goi)


# ── 9. app: chỉ hiện tiến độ, ẩn Δ/p ─────────────────────────────────────

def _app_cay():
    return ast.parse((GOC / "app.py").read_text(encoding="utf-8"))


def test_APP_chi_goi_bang_tien_do_cua_cham_xac_nhan_va_khong_tinh_gi_tren_du_lieu():
    cay = _app_cay()
    ten = {a.asname or a.name for n in ast.walk(cay) if isinstance(n, ast.Import)
           for a in n.names if a.name == "cham_xac_nhan"}
    assert ten, "app phai nhap cham_xac_nhan de hien tien do"
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and isinstance(n.func.value, ast.Name) and n.func.value.id in ten}
    assert goi == {"bang_tien_do"}, goi
    chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert "Tiến độ tới mốc đọc" in chuoi
    cam = [s for s in chuoi if "chấm bóng" in s.lower() or "cham bong" in s.lower()]
    assert not cam, cam


def test_APP_hom_nay_cua_tien_do_la_ngay_VN_hien_tai_khong_gan_tay():
    """Tiến độ tính tới HÔM NAY: đối số thứ hai của `bang_tien_do` phải là
    `now_vn().date().isoformat()` — một ngày gõ tay sẽ đóng băng tiến độ."""
    goi = [n for n in ast.walk(_app_cay()) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == "bang_tien_do"]
    assert len(goi) == 1 and len(goi[0].args) == 2
    a = goi[0].args[1]
    chuoi = []
    while isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute):
        chuoi.append(a.func.attr)
        a = a.func.value
    assert chuoi == ["isoformat", "date"] and isinstance(a, ast.Call) and a.func.id == "now_vn"


def test_APP_cau_chu_thich_noi_mot_lan_o_moc_theo_lich_va_khong_ghi_so_252_gan_tay():
    cay = _app_cay()
    cau = []
    for n in ast.walk(cay):                                  # f-string: ghép phần chữ cố định
        if isinstance(n, ast.JoinedStr):
            cau.append("".join(v.value for v in n.values if isinstance(v, ast.Constant)))
    dung_cau = [c for c in cau if "chỉ được đọc MỘT lần" in c]
    assert len(dung_cau) == 1, cau
    c = dung_cau[0]
    for can in ("chưa được tính", "ƯỚC", "theo lịch", "lệnh chấm trên máy", "chưa tính được"):
        assert can in c, can
    for cam in ("ứng viên", "Bonferroni", "π", "IC "):
        assert cam not in c, cam
    nap = [n for n in ast.walk(cay) if isinstance(n, ast.FormattedValue)
           and isinstance(n.value, ast.Name) and n.value.id == "_moc_uv"]
    assert nap, "so mốc phai di tu cb.MOC_DOC qua bien, khong go tay"


def test_APP_bang_hien_ra_khong_co_cot_delta_hay_p():
    b = cb.bang_hien_thi(cb.bang_cong_khai(cb.doc_so_ung_vien()))
    ten = [str(c).lower() for c in b.columns]
    assert not [c for c in ten if c in ("delta", "δ", "p", "z") or "p-value" in c or "p =" in c]


# ── 10. CLI chấm: tôn trọng mốc ──────────────────────────────────────────

def _tep_dai(tmp_path, rows, bg, uv):
    (tmp_path / "bg.csv").write_text(cx.dinh_dang_bang_gia(bg["gia"], KEO_DAI, bg["nguon"]),
                                     encoding="utf-8")
    (tmp_path / "qd.json").write_text(json.dumps(rows), encoding="utf-8")
    (tmp_path / "uv.json").write_text(json.dumps(uv), encoding="utf-8")
    return ["--bang-gia", str(tmp_path / "bg.csv"), "--quyet-dinh", str(tmp_path / "qd.json"),
            "--ung-vien", str(tmp_path / "uv.json"), "--so-hoan-vi", "50"]


def test_CLI_truoc_moc_in_tien_do_va_KHONG_in_delta_p_z(tmp_path, capsys):
    rows, bg, cal, ma = _dung(W=100, gamma=0.012)
    assert _cli().main(_tep_dai(tmp_path, rows, bg, _uv_dau(cal))) == 0
    ra = capsys.readouterr().out
    assert "tien do    : 100/252 phien co nhan" in ra
    assert "CHUA TOI MOC" in ra
    assert "delta/p/z  : khong tinh" in ra
    for cam in ("  delta      :", "  p          :", "NaN"):
        assert cam not in ra, cam


def test_CLI_toi_moc_in_delta_va_p_va_chi_252_phien_dau(tmp_path, capsys):
    rows, bg, cal, ma = _dung(W=MOC + 30, gamma=0.012)
    assert _cli().main(_tep_dai(tmp_path, rows, bg, _uv_dau(cal))) == 0
    ra = capsys.readouterr().out
    assert "tien do    : 282/252 phien co nhan" in ra and "ma tran    : 252 phien co nhan x 45" in ra
    assert "  delta      : +" in ra and "  p          : " in ra and "delta/p/z  : khong tinh" not in ra
    assert "QUA" in ra


# ── 11. LỰC ở mốc THẬT là một TỶ LỆ trên nhiều lượt rút (lỗi 99, lỗi 94) ──

def _tron252(gamma, n_hat=20, spec=None, ghi_tiem=False, so=400):
    dem = {}
    for hat in range(n_hat):
        rows, bg, cal, _ = _dung(W=MOC, hat=hat, gamma=gamma, ghi_tiem=ghi_tiem)
        t = cx.cham(rows, _uv_dau(cal, spec), bg, so=so)["chi_tiet"]["UV-T"]["trang_thai"]
        dem[t] = dem.get(t, 0) + 1
    return dem


def test_LUC_o_moc_that_tiem_vao_UNG_VIEN_cho_QUA_gan_nhu_moi_luot():
    assert _tron252(0.012, n_hat=10).get("QUA", 0) >= 9


def test_LUC_o_moc_that_KHONG_TIEM_GI_chi_dong_gia_tri_nho():
    dem = _tron252(0.0)
    assert dem.get("QUA", 0) + dem.get("THUA", 0) <= 4, dem


def test_LUC_o_moc_that_nhip_bien_cho_ty_le_o_GIUA_khong_phai_0_hoac_100():
    assert 5 <= _tron252(0.002).get("QUA", 0) <= 19


def test_LUC_o_moc_that_tiem_vao_BAN_DANG_CHAY_cho_THUA_khong_cho_QUA():
    dem = _tron252(0.012, n_hat=10, ghi_tiem=True, spec=_spec(trend_score=1.0))
    assert dem.get("THUA", 0) >= 9 and dem.get("QUA", 0) == 0, dem
