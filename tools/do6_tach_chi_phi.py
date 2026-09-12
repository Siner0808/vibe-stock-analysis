"""ĐO 6 — tách chi phí trượt giá thành BƯỚC GIÁ và TÁC ĐỘNG, so hai vùng.

Đọc theo đúng bốn kết cục đã ký trong `docs/TIEU-CHI-DOC-TRUOC.md` mục
**ĐO 6** (12/09/2026), và **không** đổi một ngưỡng nào.

VÌ SAO FILE NÀY NẰM TRONG REPO
──────────────────────────────
Quy tắc số 2: *không có lệnh thì không có số*. Bản đầu của dụng cụ này nằm
ở scratchpad, nên những con số đã vào `docs/STATE.md` BƯỚC 56 không có lệnh
nào trong repo đứng sau. Chép vào đây để chúng tái lập được.

TRẠNG THÁI THỨ NĂM — VÀ VÌ SAO NÓ BẮT BUỘC
──────────────────────────────────────────
Bảng đã ký mô tả **bốn** vùng:

    1  TAC DONG >= 50%  VA  BUOC GIA < 25%
    2  BUOC GIA >= 50%  VA  TAC DONG < 25%
    3  ca hai >= 25%
    4  ca hai < 25%

Bốn mô tả ấy **không phủ kín** mặt phẳng. Rà lưới 101×101 ngày 12/09/2026:
**1.250/10.201 điểm** không ứng với mô tả nào — vùng *một vế nằm trong
[25%, 50%), vế kia dưới 25%*.

Bản đầu có một nhánh `else` và **dồn im lặng** cả vùng ấy vào kết cục 4.
Đó là bịa một nghĩa cho chỗ bảng không nói. Nay nó trả `NGOAI_BANG`.

Cùng lý do `kiem_cu_phap_311.py` phải có mã thoát 2 *"chưa kiểm được"*, và
`vnstock_goi.kiem_goi()` phải có trạng thái `CHƯA KIỂM ĐƯỢC`: **"không
biết" là một câu trả lời, và nó không được giả dạng một câu trả lời khác.**

Đổi ngưỡng cho hết vùng hở là điều tiêu chí cấm thẳng. Nói ra chỗ hở thì
không.
"""
import argparse
import sqlite3
import statistics
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

VON = 1_000_000_000          # paper_trading.VON_DANH_MUC_VND
HE_SO_GIA = 1000.0           # cache nghìn đồng -> VNĐ; KHỐI LƯỢNG không nhân
KHOANG_CACH = 0.24           # 0,63 - 0,39 điểm mỗi lệnh — đã ký
NGUONG_GIAI_THICH = 0.50     # >= 50% -> vế đó là lời giải — đã ký
NGUONG_NHO = 0.25            # < 25%  -> vế đó không đáng kể — đã ký

THANH_KHOAN = "THANH KHOAN"      # kết cục 1
GIA_VAO = "GIA VAO"              # kết cục 2
CHUA_TACH = "CHUA TACH DUOC"     # kết cục 3
CHO_KHAC = "NAM O CHO KHAC"      # kết cục 4
NGOAI_BANG = "NGOAI BANG DA KY"  # trạng thái thứ năm


def quyet_dinh(p_buoc: float, p_tac: float) -> tuple[str, str]:
    """Xếp (phần bước giá, phần tác động) vào đúng MỘT ô của bảng đã ký.

    Hai tham số là **tỷ lệ** phần khoảng cách 0,24 điểm mà mỗi vế giải
    thích được, không phải điểm phần trăm.

    Mỗi ô kiểm ĐẦY ĐỦ mô tả của nó, không dựa vào thứ tự `elif` — nhánh
    `else` của bản đầu chính là chỗ 1.250 điểm lưới bị dồn vào im lặng.
    """
    lon_buoc, lon_tac = p_buoc >= NGUONG_GIAI_THICH, p_tac >= NGUONG_GIAI_THICH
    nho_buoc, nho_tac = p_buoc < NGUONG_NHO, p_tac < NGUONG_NHO

    if lon_tac and nho_buoc:
        return THANH_KHOAN, "tac dong giai thich >= 50%, buoc gia < 25%"
    if lon_buoc and nho_tac:
        return GIA_VAO, "buoc gia giai thich >= 50%, tac dong < 25%"
    if not nho_buoc and not nho_tac:
        return CHUA_TACH, "ca hai ve deu gop >= 25% — khong duoc chon ve to hon"
    if nho_buoc and nho_tac:
        return CHO_KHAC, ("ca hai ve deu < 25% — chi phi nam o lo chan / khop "
                          "mot phan / vong doi lenh")
    return NGOAI_BANG, (
        f"buoc gia {p_buoc:.1%} · tac dong {p_tac:.1%} KHONG ung voi mo ta "
        f"nao trong bang da ky. Mot ve nam trong [25%, 50%) con ve kia duoi "
        f"25%. Bang khong noi gi ve vung nay — KHONG duoc doc thanh mot o.")


# ── Lớp lấy dữ liệu ───────────────────────────────────────────────────
_nen: dict[str, pd.DataFrame | None] = {}


def _bang(ma: str, cache: Path) -> pd.DataFrame | None:
    if ma not in _nen:
        p = cache / f"{ma}.csv"
        if not p.exists():
            _nen[ma] = None
        else:
            df = pd.read_csv(p)
            df["ngay"] = df["time"].astype(str).str.slice(0, 10)
            _nen[ma] = df.set_index("ngay")
    return _nen[ma]


def nen_tai(ma: str, ngay: str, cache: Path) -> dict | None:
    df = _bang(ma, cache)
    if df is None or ngay not in df.index:
        return None
    r = df.loc[ngay]
    # `df.loc[<nhan>]` tra Series khi nhan duy nhat, DataFrame khi nhan bi
    # lap. Hoi thang KIEU. KHONG duoc hoi bang mot mac dinh BANG SO — do la
    # dung mau R1 cua chan_bia_so_lieu, va cua ay da chan that o ban dau.
    if isinstance(r, pd.DataFrame):
        r = r.iloc[0]
    return {"high": float(r["high"]) * HE_SO_GIA,
            "low": float(r["low"]) * HE_SO_GIA,
            "volume": float(r["volume"])}


def tach(db: Path, cache: Path) -> dict:
    """Bảng tách khoản cho một dân số lệnh, cộng CẢ HAI chiều mỗi lệnh."""
    from truot_gia import BAN, MUA, khoi_luong_hop_le, truot_gia

    con = sqlite3.connect(str(db))
    try:
        rows = con.execute(
            "SELECT symbol, entry_date, entry_price, exit_date, exit_price, "
            "size_pct FROM trades WHERE entry_date IS NOT NULL "
            "AND entry_price > 0 AND exit_date IS NOT NULL AND exit_price > 0"
        ).fetchall()
    finally:
        con.close()

    buoc, tac_dong, ty_trong, gia_vao = [], [], [], []
    bo_qua = 0
    for ma, nv, gv, nr, gr, sp in rows:
        bv = nen_tai(ma, str(nv)[:10], cache)
        br = nen_tai(ma, str(nr)[:10], cache)
        if bv is None or br is None:
            bo_qua += 1
            continue
        b_ma = t_ma = 0.0
        ok = True
        for gia, huong, nen in ((float(gv), MUA, bv), (float(gr), BAN, br)):
            so_cp = khoi_luong_hop_le(int(VON * (float(sp or 0) / 100.0) / gia))
            if so_cp <= 0:
                ok = False
                break
            t = truot_gia(gia, huong, nen, so_cp)
            b_ma += 100.0 * t["buoc_gia"] / gia
            t_ma += 100.0 * t["phan_tac_dong"] / gia
            ty_trong.append(t["ty_trong_kl"])
        if not ok:
            bo_qua += 1
            continue
        buoc.append(b_ma)
        tac_dong.append(t_ma)
        gia_vao.append(float(gv))

    tv = statistics.median
    return {"n": len(buoc), "bo_qua": bo_qua,
            "buoc": tv(buoc) if buoc else None,
            "tac_dong": tv(tac_dong) if tac_dong else None,
            "ty_trong": tv(ty_trong) if ty_trong else None,
            "gia_vao": tv(gia_vao) if gia_vao else None}


def main() -> int:
    ap = argparse.ArgumentParser(description="ĐO 6 — tách chi phí IS/OOS")
    ap.add_argument("--is-db", default="wf_is_62.db")
    ap.add_argument("--oos-db", default="wf_oos.db")
    ap.add_argument("--cache", default=str(GOC / "backtest" / "cache"))
    ts = ap.parse_args()
    cache = Path(ts.cache)

    print("=" * 70)
    print("DO 6 — chi phi IS/OOS: THANH KHOAN hay GIA VAO")
    print("=" * 70)

    ket = {}
    for ten, f in (("TRONG MAU (nguong 62)", ts.is_db), ("NGOAI MAU", ts.oos_db)):
        d = Path(f)
        if not d.is_absolute():
            d = GOC / f
        if not d.exists():
            print(f"\nKhong thay {d} — chay walkforward.py truoc.")
            return 2
        k = tach(d, cache)
        ket[ten] = k
        print(f"\n{ten}   [{d.name}]")
        print(f"  so lenh doc duoc : {k['n']}   (bo qua {k['bo_qua']})")
        if k["n"]:
            print(f"  BUOC GIA  hai chieu : {k['buoc']:.4f} %")
            print(f"  TAC DONG  hai chieu : {k['tac_dong']:.4f} %")
            print(f"  ty trong KL/nen     : {k['ty_trong']:.6f}")
            print(f"  gia vao trung vi    : {k['gia_vao']:,.0f} d")

    a, b = ket["TRONG MAU (nguong 62)"], ket["NGOAI MAU"]
    if not a["n"] or not b["n"]:
        print("\nMot vung rong -> KHONG doc duoc. Dung.")
        return 2

    p_buoc = (b["buoc"] - a["buoc"]) / KHOANG_CACH
    p_tac = (b["tac_dong"] - a["tac_dong"]) / KHOANG_CACH
    print(f"\n{'=' * 70}")
    print(f"CHENH OOS - IS, so voi khoang cach {KHOANG_CACH} diem")
    print(f"  BUOC GIA : {b['buoc'] - a['buoc']:+.4f} diem -> {p_buoc:+6.1%}")
    print(f"  TAC DONG : {b['tac_dong'] - a['tac_dong']:+.4f} diem -> {p_tac:+6.1%}")

    ma, ly_do = quyet_dinh(p_buoc, p_tac)
    print(f"\nKET CUC: {ma}\n  {ly_do}")
    return 1 if ma == NGOAI_BANG else 0


if __name__ == "__main__":
    raise SystemExit(main())
