"""Tầng 3 — VÒNG SÀNG (P3c-2, BƯỚC 154).

**ĐÃ NGỪNG DÙNG từ BƯỚC 155 (02/10/2026).** Người dùng chọn *"Bỏ vòng sàng"*: tầng 3
chỉ còn MỘT vòng (xác nhận), ứng viên khai thẳng, `cham_bong.MOC_MOT_VONG`. Lý do đo
được: ĐO 21 (K lớn → xác nhận gần như bất khả) và ĐO 23 (phép đối chiếu KHÔNG ĐẠT,
`docs/sang-doi-chieu.json`). File này được GIỮ NGUYÊN — không xoá — để ĐO 23 tái
lập được (`hinh-dang`, `doi-chieu`, `chan-doan`, `so-cache`). `sang` và `bang-day`
vẫn từ chối chạy vì kết quả đối chiếu chưa ĐẠT.

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 23 (commit riêng, đẩy
TRƯỚC khi file này tồn tại).

VIỆC CỦA FILE NÀY
Sàng các ứng viên `qua_sang: null` của `docs/ung-vien.json` trên dữ liệu ĐÃ
nhìn (phiên < `MOC_DA_NHIN`), bằng `cham_bong.so_cap`, rồi IN kết quả. Nó KHÔNG
ghi sổ ứng viên: điền `qua_sang` là việc TAY ở một commit riêng (P3c-3, luật (c)
của cổng tiền đăng ký, BƯỚC 153).

VÌ SAO KHÔNG SÀNG TRÊN DÒNG QUYẾT ĐỊNH ĐÃ GHI
Đếm trên bản lưu seeded (ĐO 23): 13.818 dòng, mật độ ô 17,1%, `ma_tran_cap` cho
0 mã đầy đủ — `cmd_seed` chạy `stride=2` và mã đang giữ vị thế không có dòng.
Nên vòng sàng chạy trên bảng điểm DÀY tính lại bằng đúng pipeline đang chạy
(`paper_runner._analyze`, bộ nhớ hậu kiểm TẮT) — NGOẠI LỆ CÓ TÊN của quy ước 1
của `cham_bong` (bản đang chạy là điểm ĐÃ GHI). Vòng XÁC NHẬN không đi qua file
này và vẫn giữ quy ước 1.

BA CHỖ MỘT MÁY SÀNG CÓ THỂ TỰ KHEN MÌNH
1. **Rò dữ liệu ≥ mốc.** Loại ngay lúc nạp (`cat_quyet_dinh`, `cat_gia`), và phần
   lõi (`kiem_khong_ro`) NÉM LỖI nếu còn thấy một dòng/nến ≥ mốc — cắt lúc nạp
   mà lõi không kiểm thì một đường nạp thứ hai làm rò mà không ai biết.
2. **Nền tính lại không phải hệ thống thật.** Phép đối chiếu (`doi_chieu`) so
   điểm tính lại với điểm ĐÃ GHI trên các ô seeded; kết cục ĐẠT/KHÔNG ĐẠT/
   KHÔNG ĐỌC do `ket_cuc_doi_chieu` phán theo ngưỡng đã ký. Sàng và bảng điểm
   dày CHỈ chạy khi file kết quả đối chiếu mang ĐẠT (`doc_ket_qua_doi_chieu`).
3. **Cửa sổ chọn theo kết quả.** Cửa sổ sàng suy từ ngày lên sàn của mã
   (`cua_so_sang`), không từ điểm hay nhãn.

CHẠY
    ./.venv/Scripts/python.exe tools/sang_ung_vien.py hinh-dang --db <seeded.db>
    ./.venv/Scripts/python.exe tools/sang_ung_vien.py doi-chieu --db <seeded.db> [--ghi]
    ./.venv/Scripts/python.exe tools/sang_ung_vien.py chan-doan --db <seeded.db>
    ./.venv/Scripts/python.exe tools/sang_ung_vien.py so-cache --cache-khac <cache_2018>
    ./.venv/Scripts/python.exe tools/sang_ung_vien.py bang-day
    ./.venv/Scripts/python.exe tools/sang_ung_vien.py sang

Mã thoát: 0 đọc được · 1 kết cục KHÔNG ĐẠT/lỗi dữ liệu · 2 chưa kiểm được.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

for _luong in (sys.stdout, sys.stderr):   # stderr: BƯỚC 129
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import cham_bong as CB  # noqa: E402
import experiment_tran_dac_trung as E  # noqa: E402

#: Mốc dữ liệu ĐÃ nhìn. Mọi dòng quyết định có `signal_date` ≥ mốc và mọi nến
#: có ngày ≥ mốc thuộc về vòng XÁC NHẬN. Ký ở ĐO 23.
MOC_DA_NHIN = "2026-08-10"
#: Giá cho đối chiếu và bảng điểm dày: CÙNG khung với bản seeded (ĐO 23).
CACHE_GIA = GOC / "backtest" / "cache"
CACHE_BANG_DAY = GOC / "backtest" / "cache_diem_sang"
FILE_DOI_CHIEU = GOC / "docs" / "sang-doi-chieu.json"
HAT = 20261002
SO_HOAN_VI = 2000
#: Qua sàng = Δ > 0 VÀ p hai phía < ngưỡng này (0,05 một phía). KHÔNG chia K.
NGUONG_P_SANG = 0.10
N_DOI_CHIEU_TOI_THIEU = 10_000
RHO_DOI_CHIEU_TOI_THIEU = 0.95
#: Sai lệch tối đa để một thành phần coi là KHỚP (chỉ để ĐỌC, không quyết định).
DUNG_SAI_THANH_PHAN = 0.1

_RE_NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}")


# ── chặn rò: loại lúc nạp, và lõi NÉM LỖI nếu còn sót ────────────────────

def _ngay(s) -> str:
    return str(s)[:10]


def cat_quyet_dinh(rows: list[dict], moc: str = MOC_DA_NHIN) -> tuple[list[dict], int]:
    """Giữ dòng có `signal_date` hợp lệ VÀ < mốc. Trả (dòng giữ, số dòng loại).

    Ngày thiếu/sai khuôn bị LOẠI và đếm chung — không có đường nào để một dòng
    không đọc được ngày lọt qua mốc.
    """
    giu, loai = [], 0
    for r in rows:
        d = str(r.get("signal_date", ""))
        if _RE_NGAY.match(d) and d[:10] < moc:
            giu.append(r)
        else:
            loai += 1
    return giu, loai


def cat_gia(kh: dict, moc: str = MOC_DA_NHIN) -> dict:
    """{mã: DataFrame} chỉ còn nến có ngày < mốc; mã hết nến thì bỏ."""
    ra = {}
    for ma, d in kh.items():
        con = d[d.index.astype(str).str.slice(0, 10) < moc]
        if len(con):
            ra[ma] = con
    return ra


def kiem_khong_ro(bang: pd.DataFrame | None = None, gia: dict | None = None,
                  moc: str = MOC_DA_NHIN) -> None:
    """NÉM `ValueError` nếu bảng điểm hay giá còn một dòng/nến ngày ≥ mốc."""
    xau = []
    if bang is not None and len(bang):
        n = int((bang["ngay"].astype(str).str.slice(0, 10) >= moc).sum())
        if n:
            xau.append(f"bang diem con {n} dong ngay >= {moc}")
    if gia is not None:
        for ma, d in gia.items():
            n = int((d.index.astype(str).str.slice(0, 10) >= moc).sum())
            if n:
                xau.append(f"gia {ma} con {n} nen ngay >= {moc}")
    if xau:
        raise ValueError("RO du lieu >= moc da nhin: " + "; ".join(xau))


def nhan_sach(gia: dict) -> pd.DataFrame:
    """Nhãn vượt rổ h = `NHIP` trên giá ĐÃ cắt. Nhãn nào chạm ≥ mốc thì NaN."""
    kiem_khong_ro(gia=gia)
    nhan = E.nhan_vuot_ro(gia, CB.NHIP)
    nhan.index = nhan.index.astype(str).str.slice(0, 10)
    return nhan


# ── bảng điểm DÀY ────────────────────────────────────────────────────────

def phan_tich_that():
    """Máy chấm THẬT: `paper_runner._analyze`, bộ nhớ hậu kiểm TẮT.

    Bộ nhớ tắt thì điểm là hàm thuần của lát cắt giá (đường quét CI chạy 0 mẫu,
    BƯỚC 140). Trả hàm `(mã, lịch sử, ngày) -> (thành phần, điểm cuối)`.
    """
    import paper_runner
    import walkforward
    walkforward._dung_bo_nho("tat", None)
    paper_runner._xoa_cache_phan_tich()

    def chay(ma, lich_su, ngay):
        kq = paper_runner._analyze(ma, lich_su, "HOSE", _ngay(ngay))
        return kq["score_breakdown"], float(kq["final_score"])
    return chay


def _lich_su(d: pd.DataFrame, t: int) -> pd.DataFrame:
    """Lịch sử tới hết hàng `t`, dạng cmd_seed đã đưa vào `_analyze`."""
    return d.iloc[: t + 1].reset_index(drop=True)


def diem_day(gia: dict, nhan: pd.DataFrame, phan_tich, tien_do=None,
             bat_dau_hang: int = E.MIN_HIST) -> pd.DataFrame:
    """Điểm tính lại cho mọi (mã, phiên) từ hàng `bat_dau_hang` mà nhãn có.

    Chỉ chấm ô có nhãn: phiên mà nhãn chạm ≥ mốc đã là NaN nên không được chấm —
    không có phép số học ngày nào để sai. Cột giống `cham_bong.doc_quyet_dinh`
    nên `ma_tran_cap` dùng thẳng.
    """
    kiem_khong_ro(gia=gia)
    ra = []
    for i, (ma, d) in enumerate(sorted(gia.items()), 1):
        nh = nhan[ma] if ma in nhan.columns else None
        if nh is None:
            continue
        for t in range(bat_dau_hang, len(d)):
            ngay = _ngay(d.index[t])
            v = nh.get(ngay)
            if v is None or not np.isfinite(v):
                continue
            tp, diem = phan_tich(ma, _lich_su(d, t), ngay)
            ra.append({"symbol": ma, "ngay": ngay, "score": diem,
                       **{k: float(tp[k]) for k in CB.THANH_PHAN}})
        if tien_do:
            tien_do(i, len(gia), ma)
    cot = ["symbol", "ngay", "score", *CB.THANH_PHAN]
    return pd.DataFrame(ra, columns=cot)


# ── đối chiếu điểm tính lại ↔ điểm đã ghi ────────────────────────────────

def ket_cuc_doi_chieu(n: int, rho_cuoi: float, rho_tp_min: float) -> str:
    """ĐẠT · KHÔNG ĐẠT · KHÔNG ĐỌC — đúng bảng ĐO 23, ngưỡng ghim ở đầu file."""
    if n < N_DOI_CHIEU_TOI_THIEU:
        return "KHONG DOC"
    if rho_cuoi >= RHO_DOI_CHIEU_TOI_THIEU and rho_tp_min >= RHO_DOI_CHIEU_TOI_THIEU:
        return "DAT"
    return "KHONG DAT"


def doi_chieu(rows: list[dict], gia: dict, phan_tich, tien_do=None) -> dict:
    """Chấm lại ĐÚNG các ô seeded rồi đo độ khớp với điểm đã ghi.

    `rows` là dòng thô của bảng `decisions`; dòng ≥ mốc bị loại và đếm. Ô khớp =
    mã nằm trong `gia` và ngày nằm trong lịch nến. Không tính IC với nhãn.
    """
    kiem_khong_ro(gia=gia)
    rows, loai = cat_quyet_dinh(rows)
    bang = CB.doc_quyet_dinh(rows, "0000-00-00")
    pos = {ma: {_ngay(x): k for k, x in enumerate(d.index)} for ma, d in gia.items()}
    cu, moi = [], []
    for i, r in enumerate(bang.itertuples(index=False), 1):
        k = pos.get(r.symbol, {}).get(r.ngay)
        if k is None:
            continue
        tp, diem = phan_tich(r.symbol, _lich_su(gia[r.symbol], k), r.ngay)
        cu.append([r.score, *(getattr(r, c) for c in CB.THANH_PHAN)])
        moi.append([diem, *(float(tp[c]) for c in CB.THANH_PHAN)])
        if tien_do and i % 1000 == 0:
            tien_do(i, len(bang), r.symbol)
    n = len(cu)
    ten = ("final_score", *CB.THANH_PHAN)
    if n == 0:
        return {"n": 0, "n_dong_loai_ge_moc": loai, "ket_cuc": "KHONG DOC",
                "rho_cuoi": None, "rho_tp": {}, "ty_le_khop": None}
    cu, moi = np.array(cu, float), np.array(moi, float)
    rho = {t: E.rho_hang(moi[:, j], cu[:, j]) for j, t in enumerate(ten)}
    rho_tp = {t: rho[t] for t in CB.THANH_PHAN}
    khop = np.all(np.abs(moi[:, 1:] - cu[:, 1:]) <= DUNG_SAI_THANH_PHAN + 1e-9, axis=1)
    return {"n": n, "n_dong_loai_ge_moc": loai, "rho_cuoi": rho["final_score"],
            "rho_tp": rho_tp, "ty_le_khop": float(khop.mean()),
            "ket_cuc": ket_cuc_doi_chieu(n, rho["final_score"], min(rho_tp.values()))}


def chan_doan(rows: list[dict], gia: dict, phan_tich, mau: int = 600,
              hat: int = 7) -> pd.DataFrame:
    """Chẩn đoán SAU một kết cục KHÔNG ĐẠT: mẫu ô seeded, ghi cạnh tính lại.

    Không đổi kết cục đã ký — chỉ trả lời vì sao các thành phần lệch, theo năm
    và theo độ dài lịch sử (`hang`). Mẫu cố định theo `hat`. Không IC.
    """
    kiem_khong_ro(gia=gia)
    rows, _ = cat_quyet_dinh(rows)
    bang = CB.doc_quyet_dinh(rows, "0000-00-00")
    pos = {ma: {_ngay(x): k for k, x in enumerate(d.index)} for ma, d in gia.items()}
    chon = np.random.default_rng(hat).choice(len(bang), min(mau, len(bang)),
                                             replace=False)
    ra = []
    for i in chon:
        r = bang.iloc[i]
        k = pos.get(r["symbol"], {}).get(r["ngay"])
        if k is None:
            continue
        tp, diem = phan_tich(r["symbol"], _lich_su(gia[r["symbol"]], k), r["ngay"])
        dong = {"ma": r["symbol"], "ngay": r["ngay"], "nam": r["ngay"][:4], "hang": k,
                "ghi_cuoi": float(r["score"]), "lai_cuoi": diem}
        for c in CB.THANH_PHAN:
            dong[f"ghi_{c}"], dong[f"lai_{c}"] = float(r[c]), float(tp[c])
        ra.append(dong)
    return pd.DataFrame(ra)


#: Biên độ dài lịch sử (số hàng) để chia nhóm khi chẩn đoán.
BIEN_HANG = (0, 100, 250, 500, 800, 5000)


def khop_theo_nhom(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Tỷ lệ ô khớp (|lệch| ≤ dung sai) của từng thành phần, theo năm và theo hàng."""
    ra = {}
    nhom = {"nam": d["nam"], "hang": pd.cut(d["hang"], list(BIEN_HANG))}
    for ten, khoa in nhom.items():
        cot = {}
        for c in CB.THANH_PHAN:
            ok = (d[f"lai_{c}"] - d[f"ghi_{c}"]).abs() <= DUNG_SAI_THANH_PHAN + 1e-9
            cot[c] = ok.groupby(khoa, observed=True).mean()
        cot["n"] = d.groupby(khoa, observed=True).size()
        ra[ten] = pd.DataFrame(cot)
    return ra


def so_hai_cache(a: dict, b: dict, dung_sai: float = 1e-6) -> dict:
    """Số nến chung mà `close` khác nhau giữa hai lần kéo giá, tính theo mã.

    Dùng để hỏi: cache hôm nay có phải cache lúc chạy `cmd_seed` không. Hai cache
    còn đó chỉ cho biết giá có ổn định giữa các lần kéo hay không.
    """
    chung = lech = 0
    ma_lech = {}
    for ma in sorted(set(a) & set(b)):
        x, y = a[ma]["close"].astype(float), b[ma]["close"].astype(float)
        j = x.index.intersection(y.index)
        khac = (x[j] - y[j]).abs() > dung_sai
        chung, lech = chung + len(j), lech + int(khac.sum())
        if khac.any():
            ma_lech[ma] = int(khac.sum())
    return {"n_ma_chung": len(set(a) & set(b)), "n_nen_chung": chung,
            "n_nen_khac": lech, "n_ma_co_nen_khac": len(ma_lech),
            "ty_le_nen_khac": lech / chung if chung else None}


def ghi_ket_qua_doi_chieu(duong: Path, kq: dict, nguon: str, ngay: str) -> None:
    """Ghi kết quả đối chiếu — file DUY NHẤT mà dụng cụ này ghi cho sổ sàng."""
    ban = {"ngay": ngay, "nguon_seeded": nguon, "moc_da_nhin": MOC_DA_NHIN,
           "che_do_bo_nho": "tat", "cache_gia": "backtest/cache", **kq}
    Path(duong).write_text(json.dumps(ban, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")


def doc_ket_qua_doi_chieu(duong: Path | None = None) -> dict | None:
    """Kết quả đối chiếu đã ghi, hoặc None nếu chưa có / hỏng khuôn.

    `duong` mặc định đọc LÚC GỌI: tham số mặc định buộc lúc định nghĩa thì test
    và dụng cụ khác không thay được đường.
    """
    try:
        d = json.loads(Path(duong or FILE_DOI_CHIEU).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) and "ket_cuc" in d else None


def da_doi_chieu_dat(duong: Path | None = None) -> bool:
    d = doc_ket_qua_doi_chieu(duong)
    return bool(d) and d["ket_cuc"] == "DAT"


# ── cửa sổ và phép sàng ──────────────────────────────────────────────────

def cua_so_sang(B: pd.DataFrame, Y: pd.DataFrame,
                min_ma: int = CB.MIN_MA) -> tuple[str, list[str]] | None:
    """Phiên đầu `s` mà ≥ `min_ma` mã có điểm VÀ nhãn ở MỌI phiên từ `s` tới cuối.

    Chỉ phụ thuộc chỗ trống của điểm/nhãn (ngày lên sàn), không phụ thuộc giá trị
    nào của chúng. Trả (s, các mã đủ từ `s`) hoặc None nếu không đủ `min_ma` mã.
    """
    Y = Y.reindex(index=B.index, columns=B.columns)
    co = Y.notna().any(axis=1) & B.notna().any(axis=1)
    B, Y = B[co], Y[co]
    ok = B.notna() & Y.notna()
    if ok.empty:
        return None
    bat_dau = {}
    for ma in ok.columns:
        thieu = np.flatnonzero(~ok[ma].to_numpy())
        if len(thieu) == len(ok):
            continue
        bat_dau[ma] = int(thieu[-1]) + 1 if len(thieu) else 0
        if bat_dau[ma] >= len(ok):
            del bat_dau[ma]
    if len(bat_dau) < min_ma:
        return None
    thu_tu = sorted(bat_dau.values())
    s = thu_tu[min_ma - 1]
    return str(ok.index[s]), sorted(m for m, v in bat_dau.items() if v <= s)


def chon_ung_vien_chua_sang(so: dict) -> list[str]:
    """Tên các dòng `qua_sang: null` — chỉ chúng được sàng."""
    return [ten for ten, d in so["ung_vien"].items() if d["qua_sang"] is None]


def sang_mot(bang: pd.DataFrame, nhan: pd.DataFrame, spec: dict,
             so_hoan_vi: int = SO_HOAN_VI, hat: int = HAT) -> dict:
    """Một ứng viên → {ket_cuc, delta, p, n_ma, n_phien, cua_so_tu}.

    QUA = Δ > 0 và p hai phía < `NGUONG_P_SANG`. KHÔNG ĐỌC khi không đủ
    `MIN_MA` mã đầy đủ hoặc `NHIP` phiên có nhãn (mỗi lượt một `rng` mới từ `hat`
    nên kết quả của một ứng viên không phụ thuộc thứ tự).
    """
    CB.kiem_spec(spec)
    B = bang.pivot(index="ngay", columns="symbol", values="score")
    Y = nhan.reindex(index=B.index, columns=B.columns)
    cs = cua_so_sang(B, Y)
    khong = {"ket_cuc": "KHONG DOC", "delta": None, "p": None,
             "n_ma": 0, "n_phien": 0, "cua_so_tu": None}
    if cs is None:
        return khong
    tu, cot = cs
    cat = bang[(bang["ngay"] >= tu) & bang["symbol"].isin(cot)]
    Bm, Cm, Ym, phien, ma = CB.ma_tran_cap(cat, spec, nhan)
    if len(ma) < CB.MIN_MA or len(phien) < CB.NHIP:
        return {**khong, "n_ma": len(ma), "n_phien": len(phien), "cua_so_tu": tu}
    ket = CB.so_cap(Bm, Cm, Ym, np.random.default_rng(hat), so_hoan_vi)
    qua = ket["delta"] > 0 and ket["p"] < NGUONG_P_SANG
    return {"ket_cuc": "QUA" if qua else "ROT", "delta": float(ket["delta"]),
            "p": float(ket["p"]), "n_ma": len(ma), "n_phien": len(phien),
            "cua_so_tu": tu}


def sang(so: dict, bang: pd.DataFrame, gia: dict,
         so_hoan_vi: int = SO_HOAN_VI, hat: int = HAT) -> dict[str, dict]:
    """Sàng mọi dòng `qua_sang: null`. KHÔNG ghi sổ. Ném lỗi nếu dữ liệu rò."""
    CB.kiem_so_ung_vien(so)
    kiem_khong_ro(bang=bang, gia=gia)
    nhan = nhan_sach(gia)
    return {ten: sang_mot(bang, nhan, so["ung_vien"][ten]["spec"], so_hoan_vi, hat)
            for ten in chon_ung_vien_chua_sang(so)}


# ── hình dạng dòng seeded (đếm, không IC) ────────────────────────────────

def hinh_dang(rows: list[dict], gia: dict) -> dict:
    """Đếm dòng/mã/phiên/mật độ của dòng seeded và số mã mà `ma_tran_cap` giữ.

    Dựng lại các con số đã khai ở ĐO 23. Chỉ ĐẾM: không IC, không điểm nào được
    so với nhãn.
    """
    kiem_khong_ro(gia=gia)
    rows, loai = cat_quyet_dinh(rows)
    bang = CB.doc_quyet_dinh(rows, "0000-00-00")
    nhan = nhan_sach(gia)
    co = {(r.symbol, r.ngay) for r in bang.itertuples(index=False)}
    lich = [d for d in nhan.index if bang["ngay"].min() <= d <= bang["ngay"].max()]
    ma_ds = sorted(bang["symbol"].unique())
    hien = pd.DataFrame(False, index=lich, columns=ma_ds)
    for ma, d in co:
        if d in hien.index:
            hien.loc[d, ma] = True
    moi_phien = hien.sum(axis=1)
    _, _, _, phien, ma_day_du = CB.ma_tran_cap(
        bang, {"loai": "trong_so", "trong_so": {"trend_score": 1.0}}, nhan)
    cua_so = {}
    for w in (2, 5, 10, 22):
        du = (hien.astype(int).rolling(w).sum() == w).sum(axis=1)
        cua_so[w] = int(du.max())
    return {"n_dong": len(bang), "n_dong_loai_ge_moc": loai,
            "n_bo": int(bang.attrs.get("bo", 0)),
            "n_ma": int(bang["symbol"].nunique()), "n_phien": int(bang["ngay"].nunique()),
            "n_phien_lich": len(lich), "n_o": len(lich) * len(ma_ds),
            "mat_do": len(co) / max(1, len(lich) * len(ma_ds)),
            "ma_moi_phien_trung_vi": int(moi_phien.median()),
            "ma_moi_phien_max": int(moi_phien.max()),
            "phien_du_40_ma": int((moi_phien >= CB.MIN_MA).sum()),
            "ma_tran_phien": len(phien), "ma_tran_ma_day_du": len(ma_day_du),
            "cua_so_ma_du_moi_phien": cua_so}


# ── nạp / ghi / dòng lệnh ────────────────────────────────────────────────

def doc_db_seeded(duong: Path, moc: str = MOC_DA_NHIN) -> tuple[list[dict], int]:
    """Dòng `decisions` < mốc từ một DB chỉ-đọc; đếm riêng số dòng ≥ mốc."""
    con = sqlite3.connect(f"file:{Path(duong).as_posix()}?mode=ro", uri=True)
    try:
        cur = con.execute(
            "SELECT seq, at, symbol, signal_date, score, components FROM decisions"
            " WHERE substr(signal_date,1,10) < ?", (moc,))
        cot = [c[0] for c in cur.description]
        rows = [dict(zip(cot, r)) for r in cur]
        n_ge = con.execute("SELECT COUNT(*) FROM decisions WHERE"
                           " substr(signal_date,1,10) >= ?", (moc,)).fetchone()[0]
    finally:
        con.close()
    return rows, int(n_ge)


def nap_gia(thu_muc: Path = CACHE_GIA) -> dict:
    """Giá từ cache, ĐÃ cắt < mốc ngay lúc nạp."""
    return cat_gia(E.nap_gia(thu_muc))


def ghi_bang_day(duong: Path, bang: pd.DataFrame) -> None:
    Path(duong).parent.mkdir(parents=True, exist_ok=True)
    bang.to_csv(duong, index=False)


def doc_bang_day(duong: Path) -> pd.DataFrame:
    return pd.read_csv(duong, dtype={"symbol": str, "ngay": str})


def _in_tien_do(i, n, ma):
    print(f"  [{i}/{n}] {ma}", flush=True)


def _lenh_hinh_dang(a) -> int:
    rows, n_ge = doc_db_seeded(Path(a.db))
    gia = nap_gia(Path(a.cache))
    h = hinh_dang(rows, gia)
    print(f"nguon {a.db} · cache {a.cache} · moc {MOC_DA_NHIN} "
          f"(dong >= moc chi DEM: {n_ge})")
    for k, v in h.items():
        print(f"  {k}: {v}")
    return 0


def _lenh_doi_chieu(a) -> int:
    rows, n_ge = doc_db_seeded(Path(a.db))
    gia = nap_gia(Path(a.cache))
    kq = doi_chieu(rows, gia, phan_tich_that(), _in_tien_do)
    kq["n_dong_loai_ge_moc"] = max(kq["n_dong_loai_ge_moc"], 0) + n_ge
    print(json.dumps(kq, ensure_ascii=False, indent=2))
    if a.ghi:
        ghi_ket_qua_doi_chieu(FILE_DOI_CHIEU, kq, Path(a.db).name,
                              datetime.date.today().isoformat())
        print(f"da ghi {FILE_DOI_CHIEU}")
    if kq["ket_cuc"] == "DAT":
        return 0
    return 1 if kq["ket_cuc"] == "KHONG DAT" else 2


def _lenh_chan_doan(a) -> int:
    rows, _ = doc_db_seeded(Path(a.db))
    d = chan_doan(rows, nap_gia(Path(a.cache)), phan_tich_that(), a.mau, a.hat)
    print(f"mau {len(d)} o (hat {a.hat}); ty le o khop moi thanh phan, theo nam va theo hang")
    for ten, bang in khop_theo_nhom(d).items():
        print(f"\n[theo {ten}]\n{bang.round(3).to_string()}")
    return 0


def _lenh_so_cache(a) -> int:
    r = so_hai_cache(nap_gia(Path(a.cache)), nap_gia(Path(a.cache_khac)))
    for k, v in r.items():
        print(f"  {k}: {v}")
    return 0


def _cho_phep_chay() -> bool:
    if da_doi_chieu_dat():
        return True
    print("TU CHOI: chua co ket qua doi chieu DAT (docs/sang-doi-chieu.json).")
    return False


def _lenh_bang_day(a) -> int:
    if not _cho_phep_chay():
        return 2
    gia = nap_gia(Path(a.cache))
    bang = diem_day(gia, nhan_sach(gia), phan_tich_that(), _in_tien_do)
    ghi_bang_day(Path(a.ra), bang)
    print(f"bang diem day: {len(bang)} dong · {bang['symbol'].nunique()} ma · "
          f"{bang['ngay'].nunique()} phien -> {a.ra}")
    return 0


def _lenh_sang(a) -> int:
    if not _cho_phep_chay():
        return 2
    so = CB.doc_so_ung_vien()
    bang = doc_bang_day(Path(a.bang))
    kq = sang(so, bang, nap_gia(Path(a.cache)))
    if not kq:
        print("khong co ung vien qua_sang null.")
    for ten, k in kq.items():
        print(f"{ten}: {k}")
    print("KHONG ghi so. Dien qua_sang bang tay o mot commit rieng (P3c-3).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="lenh", required=True)
    for ten in ("hinh-dang", "doi-chieu"):
        p = sp.add_parser(ten)
        p.add_argument("--db", required=True, help="DB seeded, mo chi-doc")
        p.add_argument("--cache", default=str(CACHE_GIA))
    sp.choices["doi-chieu"].add_argument("--ghi", action="store_true")
    p = sp.add_parser("so-cache")
    p.add_argument("--cache", default=str(CACHE_GIA))
    p.add_argument("--cache-khac", required=True)
    p = sp.add_parser("chan-doan")
    p.add_argument("--db", required=True, help="DB seeded, mo chi-doc")
    p.add_argument("--cache", default=str(CACHE_GIA))
    p.add_argument("--mau", type=int, default=600)
    p.add_argument("--hat", type=int, default=7)
    p = sp.add_parser("bang-day")
    p.add_argument("--cache", default=str(CACHE_GIA))
    p.add_argument("--ra", default=str(CACHE_BANG_DAY / "diem_day.csv"))
    p = sp.add_parser("sang")
    p.add_argument("--cache", default=str(CACHE_GIA))
    p.add_argument("--bang", default=str(CACHE_BANG_DAY / "diem_day.csv"))
    a = ap.parse_args(argv)
    return {"hinh-dang": _lenh_hinh_dang, "doi-chieu": _lenh_doi_chieu,
            "bang-day": _lenh_bang_day, "sang": _lenh_sang,
            "chan-doan": _lenh_chan_doan, "so-cache": _lenh_so_cache}[a.lenh](a)


if __name__ == "__main__":
    raise SystemExit(main())
