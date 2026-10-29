"""BƯỚC 241 — ĐO dấu chân của hai lỗi bộ máy sổ thật trên sổ THẬT. CHỈ ĐỌC.

    ./.venv/Scripts/python.exe tools/do_dau_chan_241.py cat-lo   <DB tạm>   # lỗi 196
    ./.venv/Scripts/python.exe tools/do_dau_chan_241.py cong-vni <DB tạm>   # lỗi 195

`<DB tạm>` là bản sao của DB do `tools/doc_so_that.py` (`keo_ve_so_tam`) kéo từ Google Sheets về thư mục tạm;
dụng cụ này mở nó `mode=ro` và KHÔNG ghi Sheets, không ghi cache giá. Giá tải thẳng bằng
`backtest.data.fetch_one` (cần mạng). Chạy từ repo CHÍNH (có `.venv` và `vnstock`).

`cat-lo` — mỗi lệnh STOP_LOSS từ 28/09: cắt lỗ cuối có bằng 0,93 × đóng cửa của CHÍNH nến thoát (hay bằng giá vào
khi cao ≥ 1,05 × vào) không? `paper_trading.evaluate_open` xét cắt lỗ TRƯỚC bước nâng trong cùng một lượt, nên
một cắt lỗ được nâng trên nến thoát chỉ cắt được lệnh ở một lượt SAU của nến ấy (vi phạm bất biến 3).

`cong-vni` — mỗi ngày tín hiệu từ 25/09: cổng VN-INDEX cho phán quyết gì với (a) nguồn mạng kèm giờ như Actions
(hành vi cũ, so chuỗi), (b) cùng nguồn cắt 10 ký tự (sau sửa), (c) cache CSV; so với dòng THẬT trong sổ.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

TU_NGAY_CAT_LO = "2026-09-28"
TU_NGAY_CONG = "2026-09-25"
DEN_NGAY = "2026-12-31"


def _mo(duong) -> sqlite3.Connection:
    db = sqlite3.connect(f"file:{Path(duong).as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def cat_lo(duong_db: str) -> int:
    from backtest import data as btd
    from data_quality import price_multiplier

    db = _mo(duong_db)
    rows = db.execute(
        "SELECT * FROM trades WHERE status='CLOSED' AND exit_reason='STOP_LOSS'"
        " AND substr(exit_date,1,10) >= ? ORDER BY substr(exit_date,1,10), id", (TU_NGAY_CAT_LO,)).fetchall()
    print(f"lenh STOP_LOSS dong tu {TU_NGAY_CAT_LO}: {len(rows)}")
    nap: dict = {}

    def bars(ma):
        if ma not in nap:
            df = btd.fetch_one(ma, "2026-08-15", DEN_NGAY).copy()
            df["d"] = df["time"].astype(str).str[:10]
            nap[ma] = df.drop_duplicates("d", keep="last").set_index("d")
        return nap[ma]

    tong = {"nang_tren_chinh_nen_thoat": 0, "stop_cu": 0, "khong_ro": 0}
    for r in rows:
        ma, x = r["symbol"], str(r["exit_date"])[:10]
        b = bars(ma)
        if x not in b.index:
            print(f"#{r['id']} {ma}: THIEU nen {x}")
            tong["khong_ro"] += 1
            continue
        m = price_multiplier(b.reset_index())
        n = b.loc[x]
        ix = list(b.index).index(x)
        close, high, low, op = (float(n[k]) * m for k in ("close", "high", "low", "open"))
        trail, sl, vao = close * 0.93, float(r["stop_loss"]), float(r["entry_price"])
        nang_close = abs(sl - trail) <= 1e-6 * max(1.0, sl)
        nang_hoavon = high >= vao * 1.05 and abs(sl - vao) <= 1e-6 * max(1.0, sl)
        uoc_truoc = float(b.iloc[ix - 1]["close"]) * m * 0.93
        luot = db.execute("SELECT seq, at, score, acted, skip_reason FROM decisions WHERE symbol=?"
                          " AND substr(signal_date,1,10)=? ORDER BY seq", (ma, x)).fetchall()
        nang = nang_close or nang_hoavon
        tong["nang_tren_chinh_nen_thoat" if nang else "stop_cu"] += 1
        print(f"\n#{r['id']} {ma} vao {str(r['entry_date'])[:10]} @ {vao:,.0f} -> ra {x} @ {float(r['exit_price']):,.0f}"
              f"  stop cuoi {sl:,.1f}")
        print(f"   nen {x}: mo {op:,.0f} cao {high:,.0f} thap {low:,.0f} dong {close:,.0f} | 0,93*dong = {trail:,.1f}"
              f" | 0,93*dong nen truoc ({b.index[ix - 1]}) = {uoc_truoc:,.1f}")
        print(f"   stop cuoi == 0,93*dong(nen thoat): {nang_close} | == gia vao & cao>=1,05*vao: {nang_hoavon}"
              f" | thap {'<=' if low <= sl else '>'} stop cuoi")
        print(f"   => {'NANG-TREN-CHINH-NEN-THOAT' if nang else 'stop-cu(dat-tu-nen-truoc)'};"
              f" so dong quyet dinh cua ma ngay {x}: {len(luot)}")
        for q in luot:
            gio = pd.Timestamp(q["at"], unit="s", tz="UTC").tz_convert("Asia/Ho_Chi_Minh")
            print(f"      seq {q['seq']} at {gio:%d/%m %H:%M} diem {q['score']} acted {q['acted']} {q['skip_reason']}")
    print("\nTONG:", tong)
    return 0


def _chuan(df: pd.DataFrame, cat: bool) -> pd.DataFrame:
    d = df.copy()
    d["time"] = d["time"].astype(str)
    if cat:
        d["time"] = d["time"].str[:10]
    d = d.sort_values("time").reset_index(drop=True)
    d["ma50"] = d["close"].rolling(50).mean()
    return d


def _qua(d: pd.DataFrame, ngay: str):
    sub = d[d["time"] <= ngay]          # CHU Y: so chuoi nguyen, DUNG hanh vi cu cua market_filter
    if sub.empty:
        return None, None
    n = sub.iloc[-1]
    return (float(n["close"]) >= float(n["ma50"])) if pd.notna(n["ma50"]) else True, str(n["time"])[:10]


def cong_vni(duong_db: str) -> int:
    from backtest import data as btd

    db = _mo(duong_db)
    mang = btd.fetch_one("VNINDEX", "2020-01-01", DEN_NGAY)
    cache = btd.load("VNINDEX")
    d_mang, d_cat, d_cache = _chuan(mang, False), _chuan(mang, True), _chuan(cache, False)
    cuoi_cache = str(d_cache["time"].iloc[-1])[:10]
    print("mang: dong", len(mang), "mau time:", list(mang["time"].astype(str).tail(2)))
    print("cache: dong", len(cache), "mau time:", list(cache["time"].astype(str).tail(2)), "ngay cuoi:", cuoi_cache)
    ngay = [r[0] for r in db.execute("SELECT DISTINCT substr(signal_date,1,10) FROM decisions"
                                     " WHERE substr(signal_date,1,10)>=? ORDER BY 1", (TU_NGAY_CONG,))]
    print(f"\nngay tin hieu tu {TU_NGAY_CONG}: {len(ngay)}\n")
    f = lambda v: "-" if v is None else ("QUA" if v else "CHAN")  # noqa: E731
    lat = []
    for n in ngay:
        a, nen_a = _qua(d_mang, n)
        b, nen_b = _qua(d_cat, n)
        c = _qua(d_cache, n)[0] if n <= cuoi_cache else None
        vn = db.execute("SELECT COUNT(*) FROM decisions WHERE substr(signal_date,1,10)=? AND skip_reason LIKE 'VN-INDEX%'",
                        (n,)).fetchone()[0]
        khong_giu = db.execute("SELECT COUNT(*) FROM decisions WHERE substr(signal_date,1,10)=?"
                               " AND skip_reason<>'đã có vị thế đang mở'", (n,)).fetchone()[0]
        vao = db.execute("SELECT id,symbol FROM trades WHERE substr(signal_date,1,10)=? ORDER BY id", (n,)).fetchall()
        that = "CHAN" if vn > 0 else "QUA"
        print(f"{n}  {f(a):<4}(nen {nen_a})  {f(b):<4}(nen {nen_b})  {f(c):<4}  | THAT {that} {vn}/{khong_giu} | "
              + (",".join(f"#{r['id']}{r['symbol']}" for r in vao) or "-") + ("   <== LAT" if a != b else ""))
        if a != b:
            lat.append((n, a, b, vao))
        if c is not None and c != b:
            print("      !! cache khac sau-sua:", f(c), f(b))
        if khong_giu and that != f(a):
            print(f"      !! so that ({that}) khac mo phong hien-hanh ({f(a)})")
    print(f"\nSo ngay lat phan quyet: {len(lat)}/{len(ngay)}")
    for n, a, b, vao in lat:
        print(f"\n{n}: hien-hanh {f(a)} -> sau-sua {f(b)}")
        ds = db.execute("SELECT symbol, score, acted, skip_reason FROM decisions WHERE substr(signal_date,1,10)=?"
                        " AND score>=62 AND skip_reason<>'đã có vị thế đang mở' GROUP BY symbol ORDER BY symbol",
                        (n,)).fetchall()
        print("   dong quyet dinh diem>=62 (khong giu), nhom theo ma:", len(ds))
        for q in ds:
            print(f"      {q['symbol']:<5} diem {q['score']} acted {q['acted']} {str(q['skip_reason'])[:70]}")
        for r in vao:
            t = db.execute("SELECT * FROM trades WHERE id=?", (r["id"],)).fetchone()
            print(f"   LENH THAT #{t['id']} {t['symbol']} tin hieu {str(t['signal_date'])[:10]} khop {t['entry_date']}"
                  f" -> {t['status']} {t['exit_date']} {t['exit_reason']}")
    return 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 2 or argv[0] not in ("cat-lo", "cong-vni"):
        print(__doc__)
        return 2
    return cat_lo(argv[1]) if argv[0] == "cat-lo" else cong_vni(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
