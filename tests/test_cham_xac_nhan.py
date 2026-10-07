"""Gác P3d — MÁY CHẤM XÁC NHẬN của tầng 3 (BƯỚC 161).

`cham_xac_nhan` ghép dòng quyết định + MỘT bảng giá thành `ket` cho từng ứng viên.
Mọi dữ liệu ở đây là GIẢ, dựng trong test (không đọc dữ liệu thật, không mạng,
không `backtest/cache*`).

Ba điều gác chính:
1. Bảng giá là MỘT lượt kéo: hai `keo_luc` bị từ chối; giá thiếu bị từ chối và gọi
   tên (mã, phiên); KHÔNG BAO GIỜ điền giá.
2. Dữ liệu chấm của mỗi ứng viên là dòng quyết định từ `khai_ngay` của CHÍNH nó;
   biên `BIEN_KHAI_NGAY` đã ký (phiên `khai_ngay` CÓ tính).
3. Phán quyết về LỰC là một TỶ LỆ trên nhiều lượt rút (lỗi 99), kèm ô "không tiêm
   gì" (lỗi 94) và ô tiêm vào BẢN ĐANG CHẠY (chiều của Δ).

MỐC ĐỌC (BƯỚC 162): file này chạy với `cham_bong.MOC_DOC` THU NHỎ về 70 (fixture
`_moc_nho`, tự trả lại sau mỗi test) để dữ liệu giả 70 phiên đủ tới mốc và bộ test chạy
nhanh; mọi khẳng định về mốc THẬT (252) và về việc cắt phiên đầu nằm ở
`tests/test_moc_doc.py`. Hằng số thật được ghim literal ở đó.
"""
import ast
import datetime
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import cham_bong as cb
import cham_xac_nhan as cx
import lich_giao_dich as lich

KEO = "2027-03-01T16:30:00+07:00"        # sau phiên cuối của mọi bảng dưới đây
THIEU = "2026-10-05"
MOC_NHO = 70                              # = số phiên quyết định mặc định của `dung`


@pytest.fixture(autouse=True)
def _moc_nho(monkeypatch):
    """Thu nhỏ mốc đọc cho file này. Mốc THẬT: `tests/test_moc_doc.py`."""
    monkeypatch.setattr(cb, "MOC_DOC", MOC_NHO)


# ── dựng dữ liệu giả ─────────────────────────────────────────────────────

def _lich(n: int, dau: str = "2026-10-05") -> list[str]:
    """`n` ngày trong tuần liên tiếp; ngày nghỉ lễ 2026 (nếu có) bị bỏ."""
    d, ra = datetime.date.fromisoformat(dau), []
    while len(ra) < n:
        if d.weekday() < 5 and lich.co_phien(d.isoformat()) is not False:
            ra.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return ra


def _spec(**w) -> dict:
    return {"loai": "trong_so", "trong_so": w}


def _so_uv(khai: str, spec: dict, ma: str = "UV-T") -> dict:
    return {"ung_vien": {ma: {"khai_ngay": khai, "mo_ta": "giả", "ly_do": "giả",
                              "qua_sang": None, "spec": spec}}}


def dung(W=70, M=45, hat=0, gamma=0.0, tiem="volume_score", ghi_tiem=False, N=None,
         keo=KEO):
    """(rows, bảng giá đã phân tích, lịch, mã).

    `W` phiên quyết định × `M` mã; bảng giá dài `N` phiên (mặc định đủ T+22 cho phiên
    quyết định cuối). `gamma` tiêm tín hiệu vào NHÃN theo thành phần `tiem` (hệ số
    đúng `gamma` trên log-lợi-nhuận 21 phiên); `ghi_tiem` đưa cùng tín hiệu ấy vào
    ĐIỂM ĐÃ GHI (bản đang chạy) thay vì để nó là nhiễu độc lập. `keo` = `keo_luc` của
    bảng (phải sau phiên cuối; mặc định đủ cho ~85 phiên, dữ liệu dài hơn đưa `keo` muộn hơn).
    """
    rng = np.random.default_rng(hat)
    N = N or W + cb.NHIP + 1
    cal = _lich(N)
    ma = [f"M{i:02d}" for i in range(M)]
    comp = {k: 50 + 10 * rng.standard_normal((W, M)) for k in cb.THANH_PHAN}
    z = (comp[tiem] - 50) / 10
    r = 0.015 * rng.standard_normal((N, M))
    for t in range(W):                       # s = t+2 .. t+22: 21 số hạng × gamma/21
        r[t + 2: min(t + 22, N - 1) + 1] += gamma / 21 * z[t]
    gia = pd.DataFrame(100 * np.exp(np.cumsum(r, axis=0)), index=cal, columns=ma)
    diem = 50 + 10 * (z if ghi_tiem else rng.standard_normal((W, M)))
    rows, seq = [], 0
    for t in range(W):
        for j, m in enumerate(ma):
            tp = {k: float(comp[k][t, j]) for k in cb.THANH_PHAN}
            rows.append({"seq": seq, "at": 1e9 + seq, "symbol": m, "signal_date": cal[t],
                         "score": float(diem[t, j]), "components": json.dumps(tp)})
            seq += 1
    bg = cx.phan_tich_bang_gia(cx.dinh_dang_bang_gia(gia, keo, {m: "vci" for m in ma}))
    return rows, bg, cal, ma


def _chay(W=70, M=45, hat=0, spec=None, so=400, khai=None, **kw):
    rows, bg, cal, _ = dung(W=W, M=M, hat=hat, **kw)
    sp = spec or _spec(volume_score=1.0)
    uv = _so_uv(khai or cal[0], sp)
    return cx.cham(rows, uv, bg, so=so)["chi_tiet"]["UV-T"]


# ── 1. định dạng và đọc bảng giá ─────────────────────────────────────────

def test_ban_tho_bang_gia_vong_di_vong_ve_giu_nguyen_tung_o():
    _, bg, cal, ma = dung(W=30, M=5)
    van = cx.dinh_dang_bang_gia(bg["gia"], KEO, bg["nguon"])
    bg2 = cx.phan_tich_bang_gia(van)
    pd.testing.assert_frame_equal(bg["gia"], bg2["gia"])
    assert bg2["keo_luc"] == KEO and set(bg2["nguon"].values()) == {"vci"}
    assert van.splitlines()[0] == "symbol,date,close,nguon,keo_luc"


def _van(W=30, M=5, keo=KEO):
    _, bg, _, ma = dung(W=W, M=M)
    return cx.dinh_dang_bang_gia(bg["gia"], keo, {m: "vci" for m in ma})


def _sua(van: str, ma: str, ngay: str, **thay) -> str:
    """Sửa các trường của dòng (mã, phiên) trong văn bản bảng giá."""
    cot, ra, thay_duoc = cx.COT_BANG_GIA, [], 0
    for dong in van.splitlines():
        f = dong.split(",")
        if f[0] == ma and f[1] == ngay:
            f = [thay.get(c, v) for c, v in zip(cot, f)]
            thay_duoc += 1
        ra.append(",".join(f))
    assert thay_duoc == 1, (ma, ngay)
    return "\n".join(ra) + "\n"


def _bo_dong(van: str, ma: str, ngay: str) -> str:
    dong = [d for d in van.splitlines() if not d.startswith(f"{ma},{ngay},")]
    assert len(dong) == len(van.splitlines()) - 1
    return "\n".join(dong) + "\n"


def _tu_choi(van: str, *mong):
    with pytest.raises(cx.BangGiaLoi) as e:
        cx.phan_tich_bang_gia(van)
    for m in mong:
        assert m in str(e.value), (m, str(e.value))


def test_BANG_hai_keo_luc_BI_TU_CHOI_va_noi_ten_ca_hai():
    van = _van().replace(KEO, "2027-03-02T16:30:00+07:00", 20)
    _tu_choi(van, "2 keo_luc", KEO, "2027-03-02T16:30:00+07:00")


def test_BANG_ghep_hai_file_bang_CAT_van_mang_hai_keo_luc():
    """Ghép hai lượt kéo bằng `cat` giữ nguyên `keo_luc` từng dòng — đó là lý do
    `keo_luc` nằm ở MỖI dòng chứ không ở dòng đầu file."""
    a, b = _van(keo=KEO), _van(keo="2027-03-02T16:30:00+07:00")
    _tu_choi(a + b.split("\n", 1)[1], "2 keo_luc")


def test_BANG_keo_luc_phai_ISO_va_CO_mui_gio():
    _tu_choi(_van(keo="2027-03-01T16:30:00"), "thieu mui gio")
    _tu_choi(_van(keo="mot gio chieu"), "khong phai ISO")


def test_BANG_keo_luc_khong_som_hon_nen_cuoi_va_nen_cuoi_khong_DO():
    cuoi = max(_van().split("\n")[1:-1], key=lambda d: d.split(",")[1]).split(",")[1]
    truoc = (datetime.date.fromisoformat(cuoi) - datetime.timedelta(days=1)).isoformat()
    _tu_choi(_van(keo=f"{truoc}T16:30:00+07:00"), "tuong lai")
    _tu_choi(_van(keo=f"{cuoi}T14:00:00+07:00"), "con DO")
    # 08:00 UTC = 15:00 giờ VN, trước giờ đóng 15:30 → vẫn dở: múi giờ được đổi đúng
    _tu_choi(_van(keo=f"{cuoi}T08:00:00+00:00"), "con DO")
    cx.phan_tich_bang_gia(_van(keo=f"{cuoi}T16:00:00+07:00"))      # cùng ngày, sau giờ đóng
    cx.phan_tich_bang_gia(_van(keo=f"{cuoi}T09:00:00+00:00"))      # 16:00 giờ VN


def test_BANG_nguon_phai_thuoc_ho_vci_kbs_va_moi_ma_MOT_nguon():
    ma = _van().split("\n")[1].split(",")[0]
    ngay = _van().split("\n")[1].split(",")[1]
    _tu_choi(_sua(_van(), ma, ngay, nguon="tcbs"), "tcbs")
    _tu_choi(_sua(_van(), ma, ngay, nguon="kbs"), "tron nhieu nguon", ma)
    van = "\n".join(d if not d.startswith(f"{ma},") else d.replace(",vci,", ",kbs,")
                    for d in _van().splitlines()) + "\n"
    bg = cx.phan_tich_bang_gia(van)                       # mã này toàn kbs, mã khác toàn vci
    assert set(bg["nguon"].values()) == {"vci", "kbs"}


def test_BANG_sai_khuon_bi_tu_choi():
    van = _van()
    cot = van.split("\n")[0]
    _tu_choi(van.replace(cot, "symbol,date,close,nguon", 1).replace(f",{KEO}", ""), "cot phai la")
    _tu_choi(van.replace(cot, cot + ",extra", 1), "cot phai la")
    _tu_choi("symbol,date,close,nguon,keo_luc\n", "rong")
    _tu_choi("", "doc duoc CSV")
    d1 = van.split("\n")[1].split(",")
    _tu_choi(_sua(van, d1[0], d1[1], date="05/10/2026"), "YYYY-MM-DD")
    _tu_choi(_sua(van, d1[0], d1[1], date="2026-02-30"), "khong ton tai")
    _tu_choi(_sua(van, d1[0], d1[1], date=d1[1] + "x"), "YYYY-MM-DD")
    _tu_choi(_sua(van, d1[0], d1[1], nguon=""), "o RONG", f"{d1[0]}@{d1[1]}")


@pytest.mark.parametrize("gia", ["", "0", "-5", "abc", "nan", "inf"])
def test_BANG_gia_rong_hoac_khong_phai_so_duong_BI_TU_CHOI_va_goi_ten(gia):
    van = _van()
    d1 = van.split("\n")[1].split(",")
    _tu_choi(_sua(van, d1[0], d1[1], close=gia), f"{d1[0]}@{d1[1]}")


def test_BANG_trung_cap_ma_phien_BI_TU_CHOI():
    van = _van()
    d1 = van.split("\n")[1]
    _tu_choi(van + d1 + "\n", "trung", d1.split(",")[0])


def test_LICH_bang_thieu_phien_hoac_co_ngay_nghi_so_voi_lich_cong_bo_BI_TU_CHOI():
    _, bg, cal, ma = dung(W=30, M=5)
    gia = bg["gia"]
    assert cx.kiem_lich(gia)["kiem_duoc"] > 0
    with pytest.raises(cx.BangGiaLoi, match=cal[7]):
        cx.kiem_lich(gia.drop(index=cal[7]))                 # mọi mã thiếu một phiên
    nghi = pd.DataFrame({"A": [1.0, 1.0, 1.0]}, index=["2026-08-28", "2026-09-01", "2026-09-03"])
    with pytest.raises(cx.BangGiaLoi, match="2026-09-01"):  # Quốc khánh: lịch nói nghỉ
        cx.kiem_lich(nghi)


def test_LICH_ngoai_pham_vi_lich_cong_bo_la_CHUA_KIEM_DUOC_chu_khong_phai_sach():
    gia = pd.DataFrame({"A": [1.0, 1.0]}, index=["2027-03-01", "2027-03-02"])
    r = cx.kiem_lich(gia)
    assert r == {"kiem_duoc": 0, "ngoai_lich": 2}
    assert cx.kiem_lich(dung(W=70, M=5)[1]["gia"])["ngoai_lich"] > 0     # bảng vắt sang 2027


# ── 2. phủ giá cho nhãn ──────────────────────────────────────────────────

def _phu(gia, rows_or_phien, ma):
    return cx.kiem_phu(gia, rows_or_phien, ma)


def _bg_thieu(W=70, M=45, **o_thieu):
    """(gia đã đục một ô, lịch, mã): `o_thieu` = {mã: chỉ số phiên}."""
    _, bg, cal, ma = dung(W=W, M=M)
    gia = bg["gia"].copy()
    for m, i in o_thieu.items():
        gia.loc[cal[i], m] = np.nan
    return gia, cal, ma


def test_PHU_du_thi_chay_va_chia_phien_cham_duoc_voi_chua_co_nhan():
    _, bg, cal, ma = dung(W=70, M=45)
    r = cx.kiem_phu(bg["gia"], cal[:70], ma)
    assert r["cham_duoc"] == cal[:70] and r["chua_co_nhan"] == []
    r = cx.kiem_phu(bg["gia"].iloc[:60], cal[:70], ma)       # bảng cắt ở cal[59]
    assert r["cham_duoc"] == cal[:38]                         # 38 + 22 = 60: phiên 37 còn T+22
    assert r["chua_co_nhan"] == cal[38:70]                    # gồm cả phiên SAU phiên cuối bảng


def test_PHU_ranh_gioi_chinh_xac_cua_phien_cham_duoc():
    _, bg, cal, ma = dung(W=70, M=45)
    gia = bg["gia"]
    for n, mong in ((70 + 22, 70), (70 + 21, 69)):            # đúng T+22 có / thiếu một phiên
        r = cx.kiem_phu(gia.iloc[:n], cal[:70], ma)
        assert len(r["cham_duoc"]) == mong, n


@pytest.mark.parametrize("i, ten", [(1, "T+1 cua phien dau"), (-1, "T+22 cua phien cuoi")])
def test_PHU_thieu_gia_o_BIEN_cua_so_BI_TU_CHOI_va_goi_ten_ma_va_phien(i, ten):
    _, bg, cal, ma = dung(W=70, M=45)
    gia = bg["gia"].copy()
    gia.iloc[i, gia.columns.get_loc("M03")] = np.nan
    with pytest.raises(cx.BangGiaLoi) as e:
        cx.kiem_phu(gia, cal[:70], ma)
    assert f"M03@{gia.index[i]}" in str(e.value), ten


def test_PHU_gia_cua_chinh_phien_T_khong_can_cho_nhan():
    """Nhãn dùng close T+1 và T+22; close của T không vào nhãn (`shift(-1)` trở đi)."""
    _, bg, cal, ma = dung(W=70, M=45)
    gia = bg["gia"].copy()
    gia.loc[cal[0], "M03"] = np.nan
    assert cx.kiem_phu(gia, cal[:70], ma)["cham_duoc"] == cal[:70]


def test_PHU_ma_co_quyet_dinh_ma_khong_co_trong_bang_gia_BI_TU_CHOI():
    _, bg, cal, ma = dung(W=70, M=45)
    with pytest.raises(cx.BangGiaLoi, match="ZZZ"):
        cx.kiem_phu(bg["gia"], cal[:70], [*ma, "ZZZ"])


def test_PHU_phien_quyet_dinh_truoc_phien_dau_cua_bang_hoac_roi_vao_lo_hong_BI_TU_CHOI():
    _, bg, cal, ma = dung(W=70, M=45)
    with pytest.raises(cx.BangGiaLoi, match="2026-09-01"):
        cx.kiem_phu(bg["gia"], ["2026-09-01", cal[3]], ma)
    with pytest.raises(cx.BangGiaLoi, match=cal[5]):
        cx.kiem_phu(bg["gia"].drop(index=cal[5]), cal[:10], ma)


def test_PHU_KHONG_BAO_GIO_dien_gia_gia_thieu_van_la_NaN_hoac_bi_tu_choi():
    gia, cal, ma = _bg_thieu(M03=20)
    assert np.isnan(gia.loc[cal[20], "M03"])
    with pytest.raises(cx.BangGiaLoi, match=f"M03@{cal[20]}"):
        cx.kiem_phu(gia, cal[:70], ma)


def test_GAC_AST_module_khong_goi_ham_dien_gia_khong_ghi_file_khong_mang():
    src = Path(inspect.getsourcefile(cx)).read_text(encoding="utf-8")
    cay = ast.parse(src)
    cam_ham = {"fillna", "ffill", "bfill", "pad", "backfill", "interpolate", "replace",
               "write_text", "write_bytes", "to_csv", "to_json", "to_parquet", "mkdir",
               "unlink", "rename", "touch"}
    goi = {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
           for n in ast.walk(cay) if isinstance(n, ast.Call)}
    assert not (goi & cam_ham), sorted(goi & cam_ham)
    kw = {k.arg for n in ast.walk(cay) if isinstance(n, ast.Call) for k in n.keywords}
    assert not (kw & {"fill_value", "method", "limit"}), kw
    for n in ast.walk(cay):                    # mọi `open(...)` chỉ để ĐỌC
        if (isinstance(n, ast.Call) and (getattr(n.func, "attr", "") == "open"
                                         or getattr(n.func, "id", "") == "open")):
            assert len(n.args) <= 1 and not {k.arg for k in n.keywords} & {"mode"}
    goc = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            goc |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            goc.add((n.module or "").split(".")[0])
    mang = {"requests", "urllib", "urllib3", "http", "socket", "gspread", "sheets_store",
            "google_sheets_sync", "vnstock", "vnstock_data", "vnai", "data_collectors",
            "yfinance", "aiohttp", "httpx"}
    assert not (goc & mang), sorted(goc & mang)


# ── 3. biên `khai_ngay` và dữ liệu chấm của TỪNG ứng viên ─────────────────

def test_HANG_SO_bien_hat_so_luot_nguon_va_cot_ghim_bang_LITERAL():
    assert cx.BIEN_KHAI_NGAY == ">="
    assert cx._LECH_NGAY == {">=": 0, ">": 1}
    assert cx.HAT_RNG == 20261007
    assert cx.SO_HOAN_VI == 2000
    assert cx.NGUON_HOP_LE == ("vci", "kbs")
    assert cx.COT_BANG_GIA == ("symbol", "date", "close", "nguon", "keo_luc")


def test_tu_ngay_doc_theo_bien_da_ky_va_bien_kia_la_ngay_ke(monkeypatch):
    assert cx.tu_ngay_doc("2026-10-02") == "2026-10-02"         # `>=`: phiên khai_ngay CÓ tính
    monkeypatch.setattr(cx, "BIEN_KHAI_NGAY", ">")
    assert cx.tu_ngay_doc("2026-10-02") == "2026-10-03"         # `>`: bắt đầu ngày kế
    assert cx.tu_ngay_doc("2026-10-31") == "2026-11-01"         # qua tháng
    monkeypatch.setattr(cx, "BIEN_KHAI_NGAY", "<")
    with pytest.raises(KeyError):                                # biên lạ nổ, không có mặc định
        cx.tu_ngay_doc("2026-10-02")


def test_BIEN_khai_ngay_phien_khai_ngay_CO_tinh_va_phien_truoc_do_KHONG(monkeypatch):
    W, M = 70, 45
    rows, bg, cal, _ = dung(W=W, M=M)
    uv = _so_uv(cal[10], _spec(volume_score=1.0))
    c = cx.cham(rows, uv, bg, so=50)["chi_tiet"]["UV-T"]
    assert c["n_phien_quyet_dinh"] == W - 10 and c["n_dong"] == (W - 10) * M
    assert c["tu_ngay"] == cal[10] and c["bien"] == ">="
    monkeypatch.setattr(cx, "BIEN_KHAI_NGAY", ">")
    c = cx.cham(rows, uv, bg, so=50)["chi_tiet"]["UV-T"]
    assert c["n_phien_quyet_dinh"] == W - 11 and c["tu_ngay"] == cal[11]


def test_MOI_ung_vien_chi_cham_tren_dong_tu_khai_ngay_CUA_CHINH_NO():
    rows, bg, cal, _ = dung(W=70, M=45)
    thang_11 = next(s for s in cal if s >= "2026-11-02")
    so = {"ung_vien": {
        "UV-A": {"khai_ngay": "2026-10-05", "mo_ta": "a", "ly_do": "a", "qua_sang": None,
                 "spec": _spec(volume_score=1.0)},
        "UV-B": {"khai_ngay": "2026-11-02", "mo_ta": "b", "ly_do": "b", "qua_sang": None,
                 "spec": _spec(volume_score=1.0)}}}
    r = cx.cham(rows, so, bg, so=50)
    a, b = r["chi_tiet"]["UV-A"], r["chi_tiet"]["UV-B"]
    assert a["n_phien_quyet_dinh"] == 70 and a["tu_ngay"] == "2026-10-05"
    assert b["n_phien_quyet_dinh"] == 70 - cal.index(thang_11) and b["tu_ngay"] == "2026-11-02"
    assert r["K"] == 2 and a["nguong"] == b["nguong"] == pytest.approx(0.025)


def test_ket_tung_ung_vien_DOC_LAP_voi_ung_vien_khac_va_voi_thu_tu(monkeypatch):
    rows, bg, cal, _ = dung(W=70, M=45, gamma=0.012)
    mot = {"ung_vien": {"UV-A": {"khai_ngay": "2026-10-05", "mo_ta": "a", "ly_do": "a",
                                 "qua_sang": None, "spec": _spec(volume_score=1.0)}}}
    hai = {"ung_vien": {**mot["ung_vien"], "UV-B": {
        "khai_ngay": "2026-11-02", "mo_ta": "b", "ly_do": "b", "qua_sang": None,
        "spec": _spec(trend_score=1.0)}}}
    a1 = cx.cham(rows, mot, bg, so=200)["chi_tiet"]["UV-A"]
    a2 = cx.cham(rows, hai, bg, so=200)["chi_tiet"]["UV-A"]
    assert (a1["delta"], a1["p"], a1["z"]) == (a2["delta"], a2["p"], a2["z"])
    assert a1["nguong"] == 0.05 and a2["nguong"] == pytest.approx(0.025)


def test_NGUONG_0_05_chia_K_di_het_duong_toi_TRANG_THAI_cung_mot_p_khac_K_khac_phan_quyet():
    """p = 0,0364 (hạt dữ liệu 9, gamma 0,004, 400 lượt): dưới 0,05 nên K = 1 phán `QUA`,
    trên 0,05/2 nên K = 2 chỉ `DANG CHAM`. Ngưỡng `a` phải ĐI QUA tới `phan_quyet`, không
    được thay bằng một hằng số — bằng 0,05 thì mọi ca K = 1 vẫn xanh."""
    rows, bg, cal, _ = dung(W=70, M=45, hat=9, gamma=0.004)
    mot = _so_uv(cal[0], _spec(volume_score=1.0))
    hai = {"ung_vien": {**mot["ung_vien"], "UV-B": {
        "khai_ngay": "2026-11-02", "mo_ta": "b", "ly_do": "b", "qua_sang": None,
        "spec": _spec(trend_score=1.0)}}}
    a = cx.cham(rows, mot, bg, so=400)["chi_tiet"]["UV-T"]
    b = cx.cham(rows, hai, bg, so=400)["chi_tiet"]["UV-T"]
    assert 0.025 < a["p"] < 0.05 and a["p"] == b["p"] and a["delta"] > 0
    assert (a["nguong"], b["nguong"]) == (0.05, 0.025)
    assert (a["trang_thai"], b["trang_thai"]) == ("QUA", "DANG CHAM")


def test_cham_TU_CHOI_so_ung_vien_sai_khuon():
    rows, bg, cal, _ = dung(W=30, M=5)
    xau = _so_uv("2026-10-05", _spec(volume_score=1.0))
    xau["ung_vien"]["UV-T"]["qua_sang"] = True            # từ 02/10 không có vòng sàng
    with pytest.raises(ValueError, match="qua_sang phai null"):
        cx.cham(rows, xau, bg)


# ── 4. chưa đủ dữ liệu · trùng bản đang chạy · LỰC là một TỶ LỆ ───────────

def test_CHUA_DU_DU_LIEU_o_ranh_gioi_phien_va_ma_va_delta_KHONG_CO_khong_phai_NaN():
    """Biên phiên là MỐC (thu nhỏ 70): dưới mốc `CHUA TOI MOC`; tới mốc mà dưới
    `MIN_MA` mã thì `CHUA DU DU LIEU`. Cả hai: không có khoá `delta`/`p`/`z`."""
    for W, M, mong in ((MOC_NHO - 1, 45, "CHUA TOI MOC"), (MOC_NHO, 39, "CHUA DU DU LIEU"),
                       (MOC_NHO, 40, None)):
        c = _chay(W=W, M=M, so=50, gamma=0.012)
        assert c["n_phien"] == W and c["n_ma"] == M, (W, M)
        if mong is None:
            assert c["trang_thai"] not in ("CHUA TOI MOC", "CHUA DU DU LIEU"), (W, M)
            assert np.isfinite(c["delta"]) and c["ket"] is not None, (W, M)
        else:
            assert c["trang_thai"] == mong, (W, M)
            assert c["ket"] is None, (W, M)
            assert not {"delta", "p", "z"} & set(c), (W, M, sorted(c))


def test_CHUA_DU_DU_LIEU_khi_chua_phien_nao_co_nhan_hoac_khong_co_dong_nao_tu_khai_ngay():
    rows, bg, cal, ma = dung(W=70, M=45)
    cat = cx.phan_tich_bang_gia(cx.dinh_dang_bang_gia(bg["gia"].iloc[:15], KEO,
                                                      {m: "vci" for m in ma}))
    c = cx.cham(rows[:15 * 45], _so_uv(cal[0], _spec(volume_score=1.0)), cat)["chi_tiet"]["UV-T"]
    assert c["n_phien"] == 0 and c["trang_thai"] == "CHUA TOI MOC"
    assert c["phien_chua_co_nhan"] == cal[:15] and not {"delta", "p", "z"} & set(c)
    c = cx.cham(rows, _so_uv("2027-06-30", _spec(volume_score=1.0)), bg)["chi_tiet"]["UV-T"]
    assert c["n_dong"] == 0 and c["n_phien"] == 0 and c["trang_thai"] == "CHUA TOI MOC"


def test_UNG_VIEN_trung_ban_dang_chay_thi_DELTA_bang_0_va_khong_qua():
    rows, bg, cal, _ = dung(W=70, M=45, gamma=0.012)
    spec = _spec(trend_score=0.5, volume_score=0.5)
    for r in rows:                    # điểm ĐÃ GHI = đúng điểm ứng viên sẽ cho
        r["score"] = cb.diem_ung_vien(spec, json.loads(r["components"]))
    c = cx.cham(rows, _so_uv(cal[0], spec), bg, so=200)["chi_tiet"]["UV-T"]
    assert c["delta"] == 0.0 and c["p"] == 1.0
    assert c["trang_thai"] == "DANG CHAM"


def _tron(**kw):
    dem = {}
    for hat in range(20):
        t = _chay(hat=hat, **kw)["trang_thai"]
        dem[t] = dem.get(t, 0) + 1
    return dem


def test_LUC_la_mot_TY_LE_tiem_vao_UNG_VIEN_cho_QUA_gan_nhu_moi_luot():
    dem = _tron(gamma=0.012)                                   # 20 lượt rút dữ liệu khác nhau
    assert dem.get("QUA", 0) >= 18, dem


def test_LUC_o_KHONG_TIEM_GI_chi_dong_gia_tri_nho_va_khong_QUA_nguoc_chieu():
    dem = _tron(gamma=0.0)
    assert dem.get("QUA", 0) + dem.get("THUA", 0) <= 4, dem


def test_LUC_tiem_vao_BAN_DANG_CHAY_cho_THUA_khong_cho_QUA():
    dem = _tron(gamma=0.012, ghi_tiem=True, spec=_spec(trend_score=1.0))
    assert dem.get("THUA", 0) >= 18 and dem.get("QUA", 0) == 0, dem


def test_nhip_bien_tiem_nho_cho_ty_le_o_GIUA_khong_phai_0_hoac_100():
    """Một lượt rút ở nhịp biên là đồng xu (lỗi 99): chỉ TỶ LỆ mới kể được lực."""
    dem = _tron(gamma=0.006)
    assert 5 <= dem.get("QUA", 0) <= 19, dem


# ── 5. hạt RNG cố định và ghi ra · khớp `bang_cong_khai` ──────────────────

def test_HAT_co_dinh_cung_dau_vao_cung_ket_qua_va_hat_duoc_GHI_RA_va_THAT_su_dung():
    rows, bg, cal, _ = dung(W=70, M=45, gamma=0.012)
    uv = _so_uv(cal[0], _spec(volume_score=1.0))
    a = cx.cham(rows, uv, bg, so=300)
    b = cx.cham(rows, uv, bg, so=300)
    assert a["hat"] == cx.HAT_RNG and a["chi_tiet"]["UV-T"]["hat"] == cx.HAT_RNG
    assert a["so_hoan_vi"] == 300 and a["chi_tiet"]["UV-T"]["so_hoan_vi"] == 300
    ka, kb = a["chi_tiet"]["UV-T"]["ket"], b["chi_tiet"]["UV-T"]["ket"]
    assert np.array_equal(ka["null"], kb["null"]) and ka["p"] == kb["p"]
    c = cx.cham(rows, uv, bg, hat=cx.HAT_RNG + 1, so=300)
    assert c["hat"] == cx.HAT_RNG + 1
    kc = c["chi_tiet"]["UV-T"]["ket"]
    assert not np.array_equal(ka["null"], kc["null"])          # hạt có tác dụng
    assert ka["delta"] == kc["delta"]                          # Δ thật không phụ thuộc hạt
    assert len(ka["null"]) == 300                              # số lượt hoán vị có tác dụng


def test_ket_dung_dang_bang_cong_khai_nhan_va_khop_trang_thai():
    rows, bg, cal, _ = dung(W=70, M=45, gamma=0.012)
    uv = _so_uv(cal[0], _spec(volume_score=1.0))
    r = cx.cham(rows, uv, bg, so=300)
    ket, n_phien, n_ma = r["ket"]["UV-T"]
    assert set(ket) >= {"delta", "p", "z"} and (n_phien, n_ma) == (70, 45)
    b = cb.bang_cong_khai(uv, r["ket"])
    assert b.loc[0, "Trạng thái"] == r["chi_tiet"]["UV-T"]["trang_thai"] == "QUA"
    assert b.loc[0, "Trạng thái"] != "CHUA CHAM"
    assert r["keo_luc"] == KEO and r["nguon"] == ["vci"] and r["n_ma_bang_gia"] == 45


def test_cham_goi_kiem_lich_bang_thieu_mot_phien_BI_TU_CHOI_ca_lan_chay():
    rows, bg, cal, ma = dung(W=70, M=45)
    # bỏ một phiên (12/2026, trong phạm vi lịch) KHÔNG có dòng quyết định — chỉ 40 phiên đầu
    # có quyết định: `kiem_phu` không
    # thấy gì, nhưng nhãn của các phiên trước nó sẽ trượt một phiên — chỉ kiểm lịch bắt được
    gia = bg["gia"].drop(index=cal[50])
    thieu = cx.phan_tich_bang_gia(cx.dinh_dang_bang_gia(gia, KEO, {m: "vci" for m in ma}))
    assert cal[50] < "2027" and cal[39] < cal[50]
    cx.kiem_phu(thieu["gia"], cal[:40], ma)
    with pytest.raises(cx.BangGiaLoi, match=f"lich phien.*{cal[50]}"):
        cx.cham(rows[:40 * 45], _so_uv(cal[0], _spec(volume_score=1.0)), thieu)


def test_dong_thieu_thanh_phan_BI_BO_va_DEM_ra_khong_dien():
    rows, bg, cal, _ = dung(W=70, M=45)
    tp = json.loads(rows[0]["components"])
    del tp["volume_score"]
    rows[0]["components"] = json.dumps(tp)
    c = cx.cham(rows, _so_uv(cal[0], _spec(volume_score=1.0)), bg, so=50)["chi_tiet"]["UV-T"]
    assert c["n_dong_bo"] == 1 and c["n_dong"] == 70 * 45 - 1


# ── 6. đọc dòng quyết định từ file · CLI ─────────────────────────────────

def _tep(tmp_path, rows, bg, uv=None):
    (tmp_path / "bg.csv").write_text(cx.dinh_dang_bang_gia(bg["gia"], KEO, bg["nguon"]),
                                     encoding="utf-8")
    (tmp_path / "qd.json").write_text(json.dumps(rows), encoding="utf-8")
    if uv is not None:
        (tmp_path / "uv.json").write_text(json.dumps(uv), encoding="utf-8")
    return (["--bang-gia", str(tmp_path / "bg.csv"), "--quyet-dinh", str(tmp_path / "qd.json")]
            + (["--ung-vien", str(tmp_path / "uv.json")] if uv is not None else []))


def test_doc_dong_quyet_dinh_json_va_csv_cho_cung_ket_qua_cham(tmp_path):
    import csv
    rows, bg, cal, _ = dung(W=70, M=45, gamma=0.012)
    (tmp_path / "qd.json").write_text(json.dumps(rows), encoding="utf-8")
    with (tmp_path / "qd.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    j = cx.doc_dong_quyet_dinh(tmp_path / "qd.json")
    s = cx.doc_dong_quyet_dinh(tmp_path / "qd.csv")
    uv = _so_uv(cal[0], _spec(volume_score=1.0))
    a = cx.cham(j, uv, bg, so=100)["chi_tiet"]["UV-T"]
    b = cx.cham(s, uv, bg, so=100)["chi_tiet"]["UV-T"]
    assert (a["delta"], a["p"], a["n_phien"]) == (b["delta"], b["p"], b["n_phien"])
    (tmp_path / "qd.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="json hoac .csv"):
        cx.doc_dong_quyet_dinh(tmp_path / "qd.txt")


def _cli():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cham_xac_nhan_cli", Path(cx.__file__).parent / "tools" / "cham_xac_nhan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_CLI_in_ket_qua_ra_man_hinh_va_KHONG_ghi_gi(tmp_path, capsys):
    rows, bg, cal, _ = dung(W=70, M=45, gamma=0.012)
    uv = _so_uv(cal[0], _spec(volume_score=1.0))
    args = _tep(tmp_path, rows, bg, uv) + ["--so-hoan-vi", "100"]
    truoc = sorted(p.name for p in tmp_path.iterdir())
    so_that = Path(cx.__file__).parent / "docs" / "ung-vien.json"
    bam = so_that.read_bytes()
    assert _cli().main(args) == 0
    ra = capsys.readouterr().out
    for can in ("UV-T", "QUA", f"hat {cx.HAT_RNG}", "100 luot hoan vi", KEO, "vci", "delta", "p  "):
        assert can in ra, can
    assert sorted(p.name for p in tmp_path.iterdir()) == truoc       # không ghi file nào
    assert so_that.read_bytes() == bam                               # sổ ứng viên thật không đổi


def test_CLI_tham_so_hat_di_het_duong_toi_ket_qua(tmp_path, capsys):
    rows, bg, cal, _ = dung(W=70, M=45, gamma=0.012)
    args = _tep(tmp_path, rows, bg, _so_uv(cal[0], _spec(volume_score=1.0)))
    assert _cli().main(args + ["--so-hoan-vi", "50", "--hat", "7"]) == 0
    ra = capsys.readouterr().out
    assert "hat 7 " in ra and f"hat {cx.HAT_RNG}" not in ra and "50 luot hoan vi" in ra


def test_CLI_tu_choi_bang_hai_keo_luc_voi_ma_thoat_1(tmp_path, capsys):
    rows, bg, cal, _ = dung(W=70, M=45)
    args = _tep(tmp_path, rows, bg, _so_uv(cal[0], _spec(volume_score=1.0)))
    van = (tmp_path / "bg.csv").read_text(encoding="utf-8")
    (tmp_path / "bg.csv").write_text(van.replace(KEO, "2027-03-02T16:30:00+07:00", 100),
                                     encoding="utf-8")
    assert _cli().main(args) == 1
    ra = capsys.readouterr().out
    assert ra.startswith("TU CHOI") and "2 keo_luc" in ra


def test_CLI_tu_choi_bang_thieu_gia_va_noi_ma_phien_voi_ma_thoat_1(tmp_path, capsys):
    rows, bg, cal, ma = dung(W=70, M=45)
    thieu = bg["gia"].copy()
    thieu.loc[cal[20], "M07"] = np.nan
    args = _tep(tmp_path, rows, {"gia": thieu, "nguon": bg["nguon"]},
                _so_uv(cal[0], _spec(volume_score=1.0)))
    assert _cli().main(args) == 1
    assert f"M07@{cal[20]}" in capsys.readouterr().out


def test_CLI_la_script_chay_duoc_va_chi_nhap_module_thuan():
    src = (Path(cx.__file__).parent / "tools" / "cham_xac_nhan.py").read_text(encoding="utf-8")
    cay = ast.parse(src)
    goc = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            goc |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            goc.add((n.module or "").split(".")[0])
    assert goc >= {"cham_bong", "cham_xac_nhan"}
    assert not goc & {"requests", "gspread", "sheets_store", "google_sheets_sync",
                      "vnstock", "vnstock_data", "vnai", "app", "streamlit"}
    ghi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not ghi & {"write_text", "write_bytes", "to_csv", "to_json", "push", "mkdir"}
