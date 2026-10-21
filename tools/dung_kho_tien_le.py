"""Dựng phần MÔ PHỎNG của kho tiền lệ ý 5 (BƯỚC 215; `docs/thiet-ke-y5-tien-le.md` mục 3).

    ./.venv/Scripts/python.exe tools/dung_kho_tien_le.py --so <wf_oos.db> --cache <thư mục CSV> \\
        --ra docs/kho-tien-le.json --do "ĐO 29" --commit <commit của lượt chạy> --nguong-is 45

Lấy lệnh ĐÃ ĐÓNG có điểm vào ≥ `paper_trading.BUY_THRESHOLD` của một sổ OOS walk-forward.
Hai cột tính bằng ĐÚNG hàm sổ thật dùng, không công thức thứ hai:
- `loi_nhuan_rong_pct` = `Trade.net_return_pct()` (sổ mở bằng `PaperTradingJournal`, trên
  một BẢN CHÉP tạm — sổ nguồn không bị chạm);
- `vni_pct_tren_ma50` = `nhat_ky_vi_sao.vni_so_voi_ma50` trên `market_filter.get_vni_df()`
  nạp từ CHÍNH thư mục cache của lượt chạy (`VNINDEX.csv` phải có; thiếu thì dừng, không
  để `get_vni_df` kéo mạng).
Đầu tệp ghi băm cache (`tools/do25_ke_hoach_vao_lenh.py::bam_thu_muc`), băm sổ, số ĐO,
commit, ngưỡng IS và lệnh dựng. Chạy lại trên cùng đầu vào ra cùng tệp từng byte.

Mã thoát: 0 đã ghi · 2 thiếu đầu vào.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
for _p in (GOC, GOC / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

for _luong in (sys.stdout, sys.stderr):   # stderr: BƯỚC 129
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _bam_tep(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lenh_tu_so(duong_so: Path) -> list:
    """Mọi lệnh của sổ, đọc qua `PaperTradingJournal` trên một bản chép tạm."""
    from paper_trading import PaperTradingJournal
    with tempfile.TemporaryDirectory() as tam:
        chep = Path(tam) / "so.db"
        shutil.copyfile(duong_so, chep)
        so = PaperTradingJournal(str(chep))
        try:
            return so.all_trades()
        finally:
            so.db.close()


def vni_df_tu_cache(cache: Path):
    """`market_filter.get_vni_df()` với `backtest.data.CACHE_DIR` trỏ vào `cache`."""
    import backtest.data as bd
    import market_filter
    cu = bd.CACHE_DIR
    bd.CACHE_DIR = Path(cache)
    try:
        return market_filter.get_vni_df()
    finally:
        bd.CACHE_DIR = cu


def dong_kho(trades: list, vni_df) -> list[dict]:
    """Lệnh ĐÃ ĐÓNG, điểm ≥ ngưỡng mua → dòng kho, xếp theo (ngày ra, mã, ngày tín hiệu)."""
    from nhat_ky_vi_sao import vni_so_voi_ma50
    from paper_trading import BUY_THRESHOLD, Status
    ra = []
    for t in trades:
        lnr = t.net_return_pct()
        if t.status != Status.CLOSED or lnr is None or t.entry_score is None \
                or t.entry_score < BUY_THRESHOLD:
            continue
        ngay_tin_hieu = str(t.signal_date)[:10]
        pct = vni_so_voi_ma50(vni_df, ngay_tin_hieu)["vni_pct_tren_ma50"]
        ra.append({"ma": t.symbol, "ngay_tin_hieu": ngay_tin_hieu,
                   "ngay_vao": str(t.entry_date)[:10], "ngay_ra": str(t.exit_date)[:10],
                   "diem_vao": t.entry_score,
                   "vni_pct_tren_ma50": None if pct is None else round(pct, 4),
                   "loi_nhuan_rong_pct": round(lnr, 4),
                   "ly_do_thoat": t.exit_reason or ""})
    return sorted(ra, key=lambda d: (d["ngay_ra"], d["ma"], d["ngay_tin_hieu"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--so", required=True, type=Path, help="wf_oos.db của lượt walk-forward")
    ap.add_argument("--cache", required=True, type=Path, help="thư mục CSV của lượt ấy")
    ap.add_argument("--ra", required=True, type=Path, help="tệp JSON ghi ra")
    ap.add_argument("--do", required=True, help="số ĐO của lượt chạy, ví dụ 'ĐO 29'")
    ap.add_argument("--commit", required=True, help="commit của lượt chạy")
    ap.add_argument("--nguong-is", required=True, type=float, dest="nguong_is")
    a = ap.parse_args(argv)
    if not a.so.is_file():
        print(f"THIẾU sổ: {a.so}")
        return 2
    if not (a.cache / "VNINDEX.csv").is_file():
        print(f"THIẾU {a.cache / 'VNINDEX.csv'} — không nạp VN-Index từ mạng.")
        return 2
    from do25_ke_hoach_vao_lenh import bam_thu_muc
    from paper_trading import BUY_THRESHOLD

    trades = lenh_tu_so(a.so)
    vni = vni_df_tu_cache(a.cache)
    dong = dong_kho(trades, vni)
    bam = bam_thu_muc(a.cache)
    du_lieu = {
        "_ghi_chu": ("Kho tiền lệ ý 5, phần MÔ PHỎNG (BƯỚC 215). CHỈ ĐỂ HIỆN — không vào điểm, "
                     "ngưỡng hay lệnh. Dựng bằng tools/dung_kho_tien_le.py; đừng sửa tay."),
        "nguon": {"do": a.do, "commit_luot_chay": a.commit, "nguong_is": a.nguong_is,
                  "bam_cache": bam["sha256"], "so_tep_cache": bam["so_file"],
                  "bam_so": _bam_tep(a.so), "nguong_mua": BUY_THRESHOLD,
                  "lenh_dung": (f"tools/dung_kho_tien_le.py --so <{a.so.name}> --cache <cache> "
                                f"--ra {a.ra.as_posix()} --do \"{a.do}\" --commit {a.commit} "
                                f"--nguong-is {a.nguong_is:g}")},
        "so_lenh_so": len(trades),
        "lenh": dong,
    }
    a.ra.parent.mkdir(parents=True, exist_ok=True)
    with open(a.ra, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(du_lieu, ensure_ascii=False, indent=1) + "\n")
    thieu = sum(1 for d in dong if d["vni_pct_tren_ma50"] is None)
    print(f"sổ {len(trades)} lệnh · kho {len(dong)} lệnh (đóng, điểm ≥ {BUY_THRESHOLD:g}) · "
          f"thiếu VN-Index {thieu} · cache {bam['sha256'][:16]} · ghi {a.ra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
