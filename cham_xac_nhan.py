"""Tầng 3 — MÁY CHẤM XÁC NHẬN (P3d phần MÃ, BƯỚC 161).

Ghép dòng quyết định (`decisions`) + MỘT bảng giá thành `ket` cho từng ứng viên,
đúng dạng `cham_bong.bang_cong_khai` nhận. Không đổi nhãn (`nhan_vuot_ro`), không
đổi `NHIP`/`ALPHA`/`MIN_MA`/cách tính K — chỉ là BÊN GỌI mà `cham_bong` còn thiếu.

MODULE THUẦN về mạng và về ghi: không gọi mạng, không ghi file, không đọc Sheets,
không đọc `backtest/cache*`. Hai hàm `doc_bang_gia` · `doc_dong_quyet_dinh` chỉ ĐỌC
một file local do bên gọi chỉ ra. Phần KÉO giá thật làm sau, trên máy người dùng.

BẢNG GIÁ MỘT LƯỢT (người dùng chốt 06/10/2026, "Một bảng tải một lần"; BƯỚC 159,
ĐO 24). Mỗi lần chấm dùng MỘT bảng kéo trong MỘT lượt, phủ trọn [T+1, T+22] của mọi
phiên được chấm, cùng họ nguồn với agent sống (`data_collectors.py`: `vci` rồi
`kbs`). Không nối nhiều lượt kéo (hệ số điều chỉnh đổi giữa hai lượt: `close` lệch
thật ở 21,6% nến chung), không đọc cache backtest.

ĐỊNH DẠNG: CSV dài, một dòng mỗi (mã, phiên), đúng năm cột `COT_BANG_GIA`
(`symbol,date,close,nguon,keo_luc`). `nguon` và `keo_luc` nằm Ở MỖI DÒNG chứ không ở
một dòng đầu file: ghép hai file CSV bằng `cat` giữ nguyên giá trị từng dòng, nên
bảng ghép từ hai lượt kéo MANG HAI `keo_luc` và bị từ chối; một dòng tiêu đề chung
thì bị ghép mà không để dấu vết.

KHÔNG BAO GIỜ điền giá. Giá thiếu thì NÓI mã nào, phiên nào, rồi từ chối cả bảng;
một giá điền (`ffill`, giá mặc định, nội suy) là một nhãn tính trên số không có.

BIÊN `khai_ngay` (BƯỚC 161): phiên `khai_ngay` CÓ TÍNH — xem `BIEN_KHAI_NGAY`.

MỐC ĐỌC (BƯỚC 162): phán quyết chỉ có ở `cham_bong.MOC_DOC` phiên CÓ NHÃN, trên đúng
chừng ấy phiên ĐẦU TIÊN kể từ phiên đầu của dữ liệu chấm; trước mốc `cham_mot` không
chạy phép so nào và không trả `delta`/`p`/`z`. Mốc nằm ở `cham_bong` (`phan_quyet`,
`trang_thai`) chứ không ở đây, để MỌI bên gọi — không riêng module này — đi qua nó.
`tien_do_theo_lich` là phép ƯỚC theo lịch công bố cho app (không giá, không Sheets).
"""
from __future__ import annotations

import csv
import datetime
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

import cham_bong as cb
import data_quality as dq
import experiment_tran_dac_trung as E
import lich_giao_dich as lich

#: Phiên `khai_ngay` của một ứng viên có được tính làm dữ liệu chấm của nó không.
#: `">="` = CÓ (khớp `cham_bong.doc_quyet_dinh`, lọc `ngay >= tu_ngay`); `">"` = KHÔNG,
#: dữ liệu chấm bắt đầu từ ngày kế. KÝ TRƯỚC khi nối kết quả vào app (BƯỚC 156 để
#: ngỏ; BƯỚC 161 ký) — chọn biên sau khi thấy số là chọn theo kết quả.
#: Lý do: nhãn của phiên T dùng giá T+1 .. T+22, nên nhãn đầu tiên có thể có của
#: phiên `khai_ngay` luôn nằm SAU ngày khai; không có đường nào để kết quả của nó
#: được biết trước khi khai. Bỏ phiên ấy chỉ mất một phiên trong ~43 và không bảo vệ gì.
BIEN_KHAI_NGAY = ">="
_LECH_NGAY = {">=": 0, ">": 1}

#: Hạt RNG cố định cho phép hoán vị (BƯỚC 161). Mỗi ứng viên dựng một
#: `default_rng(hat)` MỚI, nên kết quả của một ứng viên không phụ thuộc thứ tự chấm.
HAT_RNG = 20261007
#: Số lượt hoán vị mỗi ứng viên — bằng mặc định của `cham_bong.so_cap`, ghi ra để
#: bản chạy nói được mình dùng bao nhiêu.
SO_HOAN_VI = 2000

#: Cột bảng giá, đúng và đủ (thứ tự không quan trọng).
COT_BANG_GIA = ("symbol", "date", "close", "nguon", "keo_luc")
#: Họ nguồn của agent sống: `VNStockCollectorAgent` thử `vci` rồi `kbs`.
NGUON_HOP_LE = ("vci", "kbs")
_RE_NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: Danh sách (mã, phiên) thiếu in tối đa chừng này mục; tổng số luôn in đủ.
TOI_DA_IN = 12


class BangGiaLoi(ValueError):
    """Bảng giá không đạt: sai khuôn, trộn lượt kéo, hoặc thiếu giá cho nhãn."""


def _gom(muc, toi_da: int = TOI_DA_IN) -> str:
    muc = list(muc)
    hien = ", ".join(str(m) for m in muc[:toi_da])
    return hien + (f", … (+{len(muc) - toi_da})" if len(muc) > toi_da else "")


# ── định dạng và đọc bảng giá ────────────────────────────────────────────

def dinh_dang_bang_gia(gia: pd.DataFrame, keo_luc: str, nguon: dict) -> str:
    """Bảng ngày × mã (NaN = thiếu) → văn bản CSV dài đúng khuôn.

    Chỉ để bên kéo giá thật và test dùng CHUNG một định dạng. Ô NaN bị BỎ khỏi
    file — không viết dòng rỗng, không điền; `phan_tich_bang_gia` + `kiem_phu` sẽ
    nói thiếu ở đâu khi chấm.
    """
    dong = [",".join(COT_BANG_GIA)]
    for ma in gia.columns:
        for ngay, v in gia[ma].items():
            if pd.notna(v):
                dong.append(f"{ma},{ngay},{repr(float(v))},{nguon[ma]},{keo_luc}")
    return "\n".join(dong) + "\n"


def phan_tich_bang_gia(van_ban: str) -> dict:
    """Văn bản CSV → `{"gia": ngày × mã (float; NaN = KHÔNG có dòng), "keo_luc",
    "nguon": {mã: nguồn}}`. Ném `BangGiaLoi` khi sai khuôn hay mang hai lượt kéo."""
    try:
        df = pd.read_csv(io.StringIO(van_ban), dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
        raise BangGiaLoi(f"khong doc duoc CSV: {e}") from e
    if set(df.columns) != set(COT_BANG_GIA) or len(df.columns) != len(COT_BANG_GIA):
        raise BangGiaLoi(f"cot phai la dung {list(COT_BANG_GIA)}, co {list(df.columns)}")
    if df.empty:
        raise BangGiaLoi("bang gia rong")
    rong = df.index[(df == "").any(axis=1)]
    if len(rong):
        ct = [f"{df.at[i, 'symbol'] or '?'}@{df.at[i, 'date'] or '?'}" for i in rong]
        raise BangGiaLoi(f"{len(rong)} dong co o RONG (khong dien gia): {_gom(ct)}")

    keo = sorted(set(df["keo_luc"]))
    if len(keo) != 1:
        raise BangGiaLoi(f"bang gia mang {len(keo)} keo_luc khac nhau (khong noi nhieu "
                         f"luot keo): {_gom(keo)}")
    try:
        keo_dt = datetime.datetime.fromisoformat(keo[0])
    except ValueError as e:
        raise BangGiaLoi(f"keo_luc khong phai ISO 8601: {keo[0]!r}") from e
    if keo_dt.tzinfo is None:
        raise BangGiaLoi(f"keo_luc thieu mui gio: {keo[0]!r}")

    la = sorted(set(df["nguon"]) - set(NGUON_HOP_LE))
    if la:
        raise BangGiaLoi(f"nguon ngoai {list(NGUON_HOP_LE)}: {la}")
    nhieu = sorted(m for m, g in df.groupby("symbol")["nguon"] if g.nunique() != 1)
    if nhieu:
        raise BangGiaLoi(f"ma tron nhieu nguon trong mot chuoi: {_gom(nhieu)}")

    xau = sorted(set(df.loc[~df["date"].str.match(_RE_NGAY), "date"]))
    if xau:
        raise BangGiaLoi(f"date phai la YYYY-MM-DD: {_gom(xau)}")
    try:
        for d in set(df["date"]):
            datetime.date.fromisoformat(d)
    except ValueError as e:
        raise BangGiaLoi(f"date khong ton tai: {e}") from e
    gia = pd.to_numeric(df["close"], errors="coerce")
    sai = df.index[~np.isfinite(gia) | (gia <= 0)]
    if len(sai):
        ct = [f"{df.at[i, 'symbol']}@{df.at[i, 'date']}={df.at[i, 'close']}" for i in sai]
        raise BangGiaLoi(f"{len(sai)} gia khong phai so duong huu han: {_gom(ct)}")
    trung = df[df.duplicated(["symbol", "date"], keep=False)]
    if len(trung):
        ct = sorted({f"{r.symbol}@{r.date}" for r in trung.itertuples()})
        raise BangGiaLoi(f"{len(ct)} cap (ma, phien) trung: {_gom(ct)}")

    cuoi = max(df["date"])
    keo_vn = keo_dt.astimezone(dq.VN_TZ)
    if keo_vn.date().isoformat() < cuoi:
        raise BangGiaLoi(f"keo_luc {keo[0]} (gio VN {keo_vn.date()}) som hon nen cuoi "
                         f"{cuoi}: gia tu tuong lai cua luot keo")
    if dq.nen_cuoi_dang_do(cuoi, keo_vn):
        raise BangGiaLoi(f"nen cuoi {cuoi} co the con DO luc keo ({keo[0]}, truoc gio dong "
                         f"{dq.GIO_NEN_DA_DONG}): nhan T+22 khong duoc tinh tren nen do")

    pv = df.assign(close=gia).pivot(index="date", columns="symbol", values="close")
    return {"gia": pv.sort_index().astype(float), "keo_luc": keo[0],
            "nguon": dict(df.drop_duplicates("symbol").set_index("symbol")["nguon"])}


def doc_bang_gia(duong) -> dict:
    """ĐỌC một file bảng giá (UTF-8) rồi `phan_tich_bang_gia`. Không ghi gì."""
    return phan_tich_bang_gia(Path(duong).read_text(encoding="utf-8"))


def kiem_lich(gia: pd.DataFrame) -> dict:
    """Đối chiếu lịch phiên của bảng với `lich_giao_dich` (công bố trước, chỉ 2026).

    Một ngày CÓ phiên theo lịch mà mọi mã đều thiếu làm `shift` của nhãn trượt một
    phiên mà không dòng nào báo; ngày lịch nói NGHỈ mà bảng có là bảng sai. Ngoài
    phạm vi lịch thì KHÔNG kiểm được — nói ra, không coi là sạch.
    Trả `{"kiem_duoc": số ngày đã đối chiếu, "ngoai_lich": số ngày chưa kiểm được}`.
    """
    cal = set(gia.index)
    d, het = datetime.date.fromisoformat(min(cal)), datetime.date.fromisoformat(max(cal))
    thieu, thua, kiem, ngoai = [], [], 0, 0
    while d <= het:
        s = d.isoformat()
        co = lich.co_phien(s)
        if co is None:
            ngoai += 1
        else:
            kiem += 1
            if co and s not in cal:
                thieu.append(s)
            if not co and s in cal:
                thua.append(s)
        d += datetime.timedelta(days=1)
    if thieu or thua:
        raise BangGiaLoi(f"lich phien cua bang khop sai lich cong bo: thieu phien "
                         f"{_gom(thieu)}; co ngay nghi {_gom(thua)}")
    return {"kiem_duoc": kiem, "ngoai_lich": ngoai}


# ── phủ giá cho nhãn ─────────────────────────────────────────────────────

def kiem_phu(gia: pd.DataFrame, phien_qd, ma_qd, nhip: int = cb.NHIP) -> dict:
    """Bảng giá có phủ trọn [T+1, T+nhip+1] cho MỌI phiên chấm được không.

    Phiên T chấm được khi bảng còn đủ `nhip + 1` phiên sau nó (nhãn dùng giá T+1
    và T+22). Phiên quyết định SAU phiên cuối của bảng thì chưa có nhãn — hợp lệ,
    được liệt kê, không phải lỗi. Mọi mã của bảng phải có `close` ở MỌI phiên
    trong các cửa sổ ấy: rổ chuẩn của nhãn là trung bình các mã CỦA BẢNG, một giá
    thiếu làm rổ co lại lặng lẽ. Ném `BangGiaLoi` gọi tên (mã, phiên) thiếu.

    Trả `{"cham_duoc": [phiên], "chua_co_nhan": [phiên]}`.
    """
    cal = list(gia.index)
    pos = {s: i for i, s in enumerate(cal)}
    ma_thieu = sorted(set(ma_qd) - set(gia.columns))
    if ma_thieu:
        raise BangGiaLoi(f"ma co dong quyet dinh nhung khong co trong bang gia: "
                         f"{_gom(ma_thieu)}")
    cham_duoc, chua, lac = [], [], []
    for t in sorted(set(phien_qd)):
        if t > cal[-1]:
            chua.append(t)
        elif t not in pos:
            lac.append(t)          # trước phiên đầu của bảng, hoặc rơi vào lỗ hổng lịch
        elif pos[t] + nhip + 1 <= len(cal) - 1:
            cham_duoc.append(t)
        else:
            chua.append(t)
    if lac:
        raise BangGiaLoi(f"phien quyet dinh khong nam trong lich cua bang gia "
                         f"({cal[0]} .. {cal[-1]}): {_gom(lac)}")
    can = sorted({cal[j] for t in cham_duoc
                  for j in range(pos[t] + 1, pos[t] + nhip + 2)})
    if can:
        o_thieu = gia.loc[can].isna()
        cap = [(m, s) for m in gia.columns for s in can if o_thieu.at[s, m]]
        if cap:
            raise BangGiaLoi(f"thieu gia trong cua so [T+1, T+{nhip + 1}] cua phien cham "
                             f"duoc: {len(cap)} o (ma@phien) tren "
                             f"{len({m for m, _ in cap})} ma: "
                             f"{_gom(f'{m}@{s}' for m, s in cap)}")
    return {"cham_duoc": cham_duoc, "chua_co_nhan": chua}


# ── dòng quyết định ──────────────────────────────────────────────────────

def doc_dong_quyet_dinh(duong) -> list[dict]:
    """ĐỌC dòng tab `decisions` đã xuất ra file local: `.json` (danh sách dict)
    hoặc `.csv` (có dòng tiêu đề, mọi ô là chuỗi). Không ghi, không gọi Sheets."""
    p = Path(duong)
    if p.suffix.lower() == ".json":
        rows = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            raise ValueError(f"{p.name}: phai la danh sach dict")
        return rows
    if p.suffix.lower() == ".csv":
        with p.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    raise ValueError(f"{p.name}: chi nhan .json hoac .csv")


def tu_ngay_doc(khai_ngay: str) -> str:
    """Ngày đầu tiên của dữ liệu chấm, theo `BIEN_KHAI_NGAY` — tham số `tu_ngay`
    của `cham_bong.doc_quyet_dinh` (nó giữ `ngay >= tu_ngay`)."""
    d = datetime.date.fromisoformat(khai_ngay)
    return (d + datetime.timedelta(days=_LECH_NGAY[BIEN_KHAI_NGAY])).isoformat()


# ── tiến độ tới mốc đọc, ƯỚC theo lịch (BƯỚC 162) ─────────────────────────

def tien_do_theo_lich(khai_ngay: str, hom_nay: str) -> dict:
    """Số phiên có nhãn CÓ THỂ có theo lịch công bố, từ phiên đầu của dữ liệu chấm.

    Đếm phiên giao dịch (theo `lich_giao_dich`) trong [`tu_ngay_doc(khai_ngay)`,
    `hom_nay`] rồi trừ `NHIP + 1` phiên cuối chưa có nhãn (nhãn của phiên T cần giá
    T+22). Đây là CẬN TRÊN: không đọc giá, không đọc dòng quyết định, nên không biết
    phiên nào thiếu dòng hay nến hôm nay đã đóng chưa; con số thật chỉ có khi chạy
    `tools/cham_xac_nhan.py`. Ngoài phạm vi lịch công bố (chỉ 2026) thì
    `tinh_duoc` là False và `n_co_nhan` là `None` — không đoán.
    """
    tu = tu_ngay_doc(khai_ngay)
    dau = lich.co_phien(tu)
    if dau is None or lich.co_phien(hom_nay) is None:
        return {"tinh_duoc": False, "n_phien_lich": None, "n_co_nhan": None,
                "moc": cb.MOC_DOC}
    n_lich = 0 if str(hom_nay)[:10] < tu else len(lich.cac_phien(tu, hom_nay)) + (1 if dau else 0)
    return {"tinh_duoc": True, "n_phien_lich": n_lich,
            "n_co_nhan": max(0, n_lich - (cb.NHIP + 1)), "moc": cb.MOC_DOC}


def nhan_tien_do(td: dict) -> str:
    """Câu hiện cho người dùng từ `tien_do_theo_lich` — một nơi, để app và test chung."""
    if not td["tinh_duoc"]:
        return (f"chưa tính được (lịch công bố chỉ phủ {lich.PHU_TU} → {lich.PHU_TOI})")
    n, moc = td["n_co_nhan"], td["moc"]
    s = f"≈ {min(n, moc)}/{moc} phiên có nhãn (theo lịch)"
    return s + (" — theo lịch đã tới mốc đọc" if n >= moc else "")


def bang_tien_do(so_uv: dict, hom_nay: str) -> dict:
    """{mã: câu tiến độ} cho từng phương án của sổ. Phương án của quy trình cũ không
    vào vòng xác nhận (rớt sàng hoặc chưa sàng) thì không có tiến độ để hiện."""
    cb.kiem_so_ung_vien(so_uv)
    return {ma: (nhan_tien_do(tien_do_theo_lich(d["khai_ngay"], hom_nay))
                 if cb.sau_moc(d) or d["qua_sang"] is True else "không áp dụng")
            for ma, d in so_uv["ung_vien"].items()}


# ── chấm ─────────────────────────────────────────────────────────────────

def _nhan(gia: pd.DataFrame) -> pd.DataFrame:
    kh = {m: pd.DataFrame({"close": gia[m]}) for m in gia.columns}
    return E.nhan_vuot_ro(kh, cb.NHIP)


def cham_mot(rows: list[dict], ma: str, d: dict, gia: pd.DataFrame, a: float,
             hat: int = HAT_RNG, so: int = SO_HOAN_VI) -> dict:
    """Chấm MỘT ứng viên trên dòng quyết định từ `khai_ngay` của CHÍNH nó.

    Phép so là `cham_bong.so_cap` (cặp, cùng hoán vị MÃ cho hai điểm) trên nhãn
    `E.nhan_vuot_ro`; `a` = ngưỡng 0,05/K của cả sổ. Đi qua `cham_bong.phan_quyet`
    nên chỉ phán ở mốc `MOC_DOC`, trên đúng `MOC_DOC` phiên có nhãn đầu tiên. Chưa tới
    mốc (hoặc tới mốc mà dưới `MIN_MA` mã) thì `so_cap` KHÔNG chạy, `ket` là `None` và
    kết quả KHÔNG có khoá `delta`/`p`/`z` — không phải NaN đã tính, không số mặc định.
    `n_phien` là số phiên dùng cho phép so (≤ `MOC_DOC`); `n_phien_co_nhan` là số phiên
    có nhãn đang có trong dữ liệu (tiến độ thật, có thể vượt mốc).
    """
    tu = tu_ngay_doc(d["khai_ngay"])
    bang = cb.doc_quyet_dinh(rows, tu)
    phu = kiem_phu(gia, bang["ngay"], bang["symbol"])
    q = cb.phan_quyet(bang, d["spec"], _nhan(gia), a, hat, so=so)
    c = {"ket": q["ket"], "n_phien": q["n_phien"], "n_ma": q["n_ma"],
         "trang_thai": q["trang_thai"], "moc_doc": cb.MOC_DOC,
         "n_phien_co_nhan": len(phu["cham_duoc"]),
         "nguong": a, "khai_ngay": d["khai_ngay"], "tu_ngay": tu,
         "bien": BIEN_KHAI_NGAY, "n_dong": len(bang), "n_dong_bo": bang.attrs["bo"],
         "n_phien_quyet_dinh": len(set(bang["ngay"])),
         "phien_chua_co_nhan": phu["chua_co_nhan"], "hat": hat, "so_hoan_vi": so}
    if q["ket"] is not None:
        c.update(delta=q["ket"]["delta"], p=q["ket"]["p"], z=q["ket"]["z"])
    return c


def cham(rows: list[dict], so_uv: dict, bang_gia: dict, hat: int = HAT_RNG,
         so: int = SO_HOAN_VI) -> dict:
    """Chấm MỌI ứng viên của sổ trên MỘT bảng giá đã `phan_tich_bang_gia`.

    Trả `{"ket": {mã: (ket, n_phien, n_ma)}, "chi_tiet": {mã: {...}}, ...}` —
    khoá `ket` đúng dạng `cham_bong.bang_cong_khai(so_uv, ket)` nhận.
    """
    cb.kiem_so_ung_vien(so_uv)
    gia = bang_gia["gia"]
    cal = kiem_lich(gia)
    a = cb.nguong(so_uv)
    ct = {ma: cham_mot(rows, ma, d, gia, a, hat, so)
          for ma, d in sorted(so_uv["ung_vien"].items())}
    return {"ket": {ma: (c["ket"], c["n_phien"], c["n_ma"]) for ma, c in ct.items()},
            "chi_tiet": ct, "K": cb.so_da_sang(so_uv), "nguong": a, "hat": hat,
            "so_hoan_vi": so, "keo_luc": bang_gia["keo_luc"],
            "nguon": sorted(set(bang_gia["nguon"].values())),
            "n_ma_bang_gia": gia.shape[1], "phien_dau": gia.index[0],
            "phien_cuoi": gia.index[-1], "lich": cal}
