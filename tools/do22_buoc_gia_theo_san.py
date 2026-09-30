"""BƯỚC 143 — đo trước: bước giá của mã HNX/UPCoM bị tính theo thang HOSE.

Trả lời bốn câu, mỗi câu một mục in ra, không gộp thành một con số:

  1. SÀN THẬT của từng mã trong rổ — `Listing(source=…).symbols_by_exchange()`
     ở HAI nguồn (vci, kbs), so từng mã SAU KHI chuẩn hoá nhãn (VCI ghi `HSX`,
     KBS ghi `HOSE`). Không suy từ biên độ. Cần mạng: mất mạng thì mục này
     báo CHƯA KIỂM ĐƯỢC, không báo khớp.
  2. Bao nhiêu lệnh trong sổ OOS của một lượt walk-forward thuộc mã HNX/UPCoM,
     ở dải giá vào nào (thang HOSE khác thang HNX ở dưới 50.000đ).
  3. Giá vào/ra của các lệnh ấy có nằm trên lưới 100đ của sàn thật không — kèm
     ĐỐI CHỨNG DƯƠNG: mã HOSE giá >= 50.000đ (thang HOSE cũng 100đ) phải cho
     ~100%. Một phép kiểm không có ca chắc chắn dương thì không biết nó có mù không.
  4. Dựng lại GIÁ VÀO bằng hàm thuần `truot_gia.truot_gia` ở hai thang (HOSE
     và sàn thật), trên đúng nến đã lưu. Đối chứng: thang HOSE phải TÁI LẬP giá
     vào đã ghi; lệnh nào không tái lập được thì bị loại khỏi phép đo và được
     đếm ra. Phía RA không dựng lại được (giá gốc trước trượt không lưu), nên
     KHÔNG có con số đo cho phía RA.

    ./.venv/Scripts/python.exe tools/do22_buoc_gia_theo_san.py \
        --oos <wf_oos.db> [--oos <wf_oos.db> ...] --cache <thư mục CSV>

CHỈ ĐỌC: mở DB ở `mode=ro`, không ghi gì, không đổi mã repo (truyền `san=` tường
minh vào hàm thuần). Mã thoát 0 đọc được · 2 chưa kiểm được (thiếu file, mất
mạng ở mục 1).
"""
from __future__ import annotations

import argparse
import sqlite3
import statistics
import sys
from collections import Counter
from pathlib import Path

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

from san_giao_dich import chuan_hoa_nhan as chuan_hoa_san  # noqa: E402  một nơi duy nhất

VON_VND = 1_000_000_000          # như paper_trading.VON_DANH_MUC_VND


def san_theo_nguon() -> dict[str, dict[str, str | None]]:
    """{nguồn: {mã: sàn đã chuẩn hoá}} — nổ nếu thiếu mạng hay thiếu thư viện."""
    from vnstock import Listing
    ra: dict[str, dict[str, str | None]] = {}
    for nguon in ("vci", "kbs"):
        d = Listing(source=nguon).symbols_by_exchange()
        ra[nguon] = {str(s).upper(): chuan_hoa_san(e)
                     for s, e in zip(d["symbol"], d["exchange"])}
    return ra


def dai_gia(gia: float) -> str:
    return "<10k" if gia < 10_000 else ("10-50k" if gia < 50_000 else ">=50k")


def chia_het(x: float, b: int) -> bool:
    return abs(round(x / b) * b - x) < 1e-6


def doc_lenh(duong: Path) -> list[dict]:
    db = sqlite3.connect(f"file:{duong}?mode=ro", uri=True)
    try:
        cot = ("symbol", "entry_date", "entry_price", "exit_price", "size_pct")
        return [dict(zip(cot, r)) for r in db.execute(
            f"SELECT {', '.join(cot)} FROM trades")]
    finally:
        db.close()


def muc_1(ro: list[str]) -> dict[str, str]:
    """In sàn của rổ ở hai nguồn; trả {mã: sàn} của các mã KHÔNG phải HOSE."""
    nguon = san_theo_nguon()
    vci, kbs = nguon["vci"], nguon["kbs"]
    lech = [s for s in ro if vci.get(s) != kbs.get(s)]
    thieu = [s for s in ro if vci.get(s) is None or kbs.get(s) is None]
    print(f"[1] sàn thật · rổ {len(ro)} mã · phân bố (vci): "
          f"{dict(Counter(vci.get(s) for s in ro))}")
    print(f"    lệch giữa hai nguồn sau chuẩn hoá: {lech or 'không'} · "
          f"mã không có nhãn HOSE/HNX/UPCOM ở một nguồn: {thieu or 'không'}")
    khac = {s: vci[s] for s in ro if vci.get(s) in ("HNX", "UPCOM")}
    for san in ("HNX", "UPCOM"):
        print(f"    {san}: {[s for s, v in khac.items() if v == san]}")
    return khac


def muc_2_3_4(duong: Path, cache: Path, khac: dict[str, str]) -> None:
    import pandas as pd
    from truot_gia import MUA, khoi_luong_hop_le, truot_gia

    lenh = doc_lenh(duong)
    ch = [r for r in lenh if r["symbol"] in khac and r["entry_price"]]
    print(f"\n{duong.parent.name}/{duong.name}: {len(lenh)} lệnh · "
          f"HNX/UPCoM: {len(ch)} ({100.0 * len(ch) / max(len(lenh), 1):.1f}%)")
    print(f"[2] theo mã: {dict(Counter(r['symbol'] for r in ch))}")
    print(f"    theo dải giá vào: "
          f"{dict(Counter(dai_gia(float(r['entry_price'])) for r in ch))}")

    nho = [r for r in ch if float(r["entry_price"]) < 50_000]
    dc = [r for r in lenh if r["symbol"] not in khac and r["entry_price"]
          and float(r["entry_price"]) >= 50_000]
    print(f"[3] giá VÀO chia hết 100 — HNX/UPCoM vào <50k: "
          f"{sum(chia_het(float(r['entry_price']), 100) for r in nho)}/{len(nho)} · "
          f"ĐỐI CHỨNG HOSE >=50k: "
          f"{sum(chia_het(float(r['entry_price']), 100) for r in dc)}/{len(dc)}")

    chenh, theo_dai, khong_dung_lai, du_lieu = [], {}, 0, {}
    for r in ch:
        s = r["symbol"]
        if s not in du_lieu:
            df = pd.read_csv(cache / f"{s}.csv")
            df["time"] = df["time"].astype(str).str[:10]
            du_lieu[s] = df
        df = du_lieu[s]
        i = df.index[df["time"] == str(r["entry_date"])[:10]]
        if len(i) != 1 or i[0] < 1:
            khong_dung_lai += 1
            continue
        row = df.loc[i[0]]
        gia_mo = float(row["open"]) * 1000            # cache: nghìn đồng
        nen = {"high": float(row["high"]) * 1000, "low": float(row["low"]) * 1000,
               "volume": float(row["volume"])}         # khối lượng KHÔNG nhân
        so_cp = khoi_luong_hop_le(int(VON_VND * float(r["size_pct"]) / 100.0 / gia_mo))
        if so_cp <= 0:
            khong_dung_lai += 1
            continue
        g_hose = truot_gia(gia_mo, MUA, nen, so_cp, "HOSE")["gia_khop"]
        if abs(g_hose - float(r["entry_price"])) > 1e-6:
            khong_dung_lai += 1                        # loại: máy đo không tái lập được
            continue
        g_dung = truot_gia(gia_mo, MUA, nen, so_cp, khac[s])["gia_khop"]
        chenh.append(g_dung - g_hose)
        theo_dai.setdefault(dai_gia(gia_mo), []).append(100.0 * (g_dung - g_hose) / g_hose)
    print(f"[4] dựng lại giá vào bằng thang HOSE tái lập đúng giá đã ghi: "
          f"{len(chenh)}/{len(ch)} (loại: {khong_dung_lai})")
    if chenh:
        print(f"    đổi giá vào: {sum(1 for d in chenh if d):d}/{len(chenh)} · "
              f"TB {statistics.mean(chenh):+.1f}đ · trung vị {statistics.median(chenh):+.0f}đ · "
              f"max {max(chenh):+.0f}đ")
        for k in ("<10k", "10-50k", ">=50k"):
            v = theo_dai.get(k, [])
            print(f"    {k:7s} n={len(v):3d}  TB {statistics.mean(v) if v else float('nan'):+.3f}% giá vào")
        print("    (chỉ phía VÀO. Phía RA không dựng lại được — xem đầu file.)")


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--oos", action="append", default=[], type=Path,
                    help="wf_oos.db của một lượt walk-forward (lặp được)")
    ap.add_argument("--cache", type=Path, help="thư mục CSV nến (nghìn đồng)")
    a = ap.parse_args(tham_so)
    thieu = [p for p in a.oos if not p.exists()] + \
        ([a.cache] if a.cache and not a.cache.exists() else [])
    if thieu:
        print(f"CHƯA KIỂM ĐƯỢC — thiếu: {[str(p) for p in thieu]}")
        return 2
    from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS as RO
    try:
        khac = muc_1(list(RO))
    except Exception as e:                         # mất mạng / thiếu thư viện
        print(f"CHƯA KIỂM ĐƯỢC mục [1] — {type(e).__name__}: {str(e)[:120]}")
        return 2
    if a.oos and not a.cache:
        print("CHƯA KIỂM ĐƯỢC — mục [2–4] cần --cache")
        return 2
    for duong in a.oos:
        muc_2_3_4(duong, a.cache, khac)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
