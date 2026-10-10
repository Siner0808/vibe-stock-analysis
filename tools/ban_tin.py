"""In bản tin cuối ngày của sổ lệnh ẢO ra màn hình — CHỈ ĐỌC (BƯỚC 174, mốc B2).

    ./.venv/Scripts/python.exe tools/ban_tin.py [--ngay YYYY-MM-DD]

Không có `--ngay` thì lấy ngày tín hiệu lớn nhất trong sổ. Kéo sổ THẬT từ Google
Sheets vào một DB TẠM (`tools/doc_so_that.keo_ve_so_tam`, cùng đường với
`tools/doc_so_that.py` và `tools/canh_cong_c5.py`), chỉ chạy lệnh SELECT, rồi in
markdown của `ban_tin.ban_tin_markdown`. Không chạm sổ ở gốc repo, không ghi,
không đẩy (gác AST: `tests/test_ban_tin.py`).

VN-INDEX lấy từ `market_filter.get_vni_df()` (cache trên đĩa trước, mạng khi
cache rỗng). Cache có thể đứng sau ngày hỏi — khi đó bản tin ghi "chưa có nến
ngày D" thay vì dùng nến cũ.

Mã thoát: 0 đã in bản tin · 2 không đọc được sổ (kho ngoài chưa cấu hình, kéo
hỏng, hoặc sổ không có quyết định nào mà không chỉ định `--ngay`) hoặc dùng sai lệnh.
"""
from __future__ import annotations

import argparse
import datetime
import sqlite3
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
# `tools/` có file cùng tên với module gốc `ban_tin.py` (như `keo_bang_gia`): đặt
# GOC SAU CÙNG để nó đứng TRƯỚC `tools/` và `import ban_tin` ra module thuần.
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import ban_tin  # noqa: E402
import doc_so_that  # noqa: E402
from paper_trading import BUY_THRESHOLD  # noqa: E402


def doc_ba_bang(db: sqlite3.Connection) -> dict[str, list[dict]]:
    """Ba bảng của sổ tạm -> list dict. Chỉ SELECT."""
    db.row_factory = sqlite3.Row
    return {
        "quyet_dinh": [dict(r) for r in db.execute("SELECT * FROM decisions")],
        "lenh": [dict(r) for r in db.execute("SELECT * FROM trades")],
        "nhat_ky": [dict(r) for r in db.execute("SELECT * FROM nhat_ky")],
    }


def _vni_mac_dinh():
    import market_filter
    return market_filter.get_vni_df()


def main(argv=None, keo=None, vni=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ngay", help="ngày tín hiệu YYYY-MM-DD (mặc định: ngày gần nhất trong sổ)")
    a = ap.parse_args(argv)
    if a.ngay:
        try:
            datetime.date.fromisoformat(a.ngay)
        except ValueError:
            ap.error(f"--ngay phải là YYYY-MM-DD, nhận {a.ngay!r}")

    try:
        ra = (keo or doc_so_that.keo_ve_so_tam)()
    except Exception as e:
        print(f"CHUA DOC DUOC SO — {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if ra is None:
        print("CHUA DOC DUOC SO — kho ngoai chua cau hinh. Khong doan gi ca.",
              file=sys.stderr)
        return 2
    so, _bao_cao = ra
    bang = doc_ba_bang(so.db)

    ngay = a.ngay or ban_tin.ngay_gan_nhat(bang["quyet_dinh"])
    if ngay is None:
        print("CHUA CO BAN TIN — so khong co quyet dinh nao, khong co ngay de lap.",
              file=sys.stderr)
        return 2

    try:
        vni_df = (vni or _vni_mac_dinh)()
    except Exception as e:
        print(f"[canh bao] khong doc duoc VN-INDEX — {type(e).__name__}: {e}",
              file=sys.stderr)
        vni_df = None

    bt = ban_tin.lap_ban_tin(bang["quyet_dinh"], bang["lenh"], bang["nhat_ky"],
                             vni_df, ngay, BUY_THRESHOLD)
    print(ban_tin.ban_tin_markdown(bt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
