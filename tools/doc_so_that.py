"""Đọc trạng thái sổ lệnh THẬT — chỉ đọc, không ghi, không đẩy.

VÌ SAO CÓ FILE NÀY
──────────────────
`CLAUDE.md` mục *"HỆ THỐNG ĐANG Ở TRẠNG THÁI NÀO"* có một bảng
*"muốn biết … hỏi bằng …"*, và dòng **"sổ lệnh thật có gì"** chỉ ghi
*"kéo từ Google Sheets — KHÔNG đọc `paper_trades.db` ở máy"*.

Đó là một **cách làm**, không phải một **lệnh**. Nên trên thực tế không ai
chạy nó, và ngày 12/09/2026 hai con số về sổ trong `CLAUDE.md` đã trôi mà
không gác nào thấy:

```
"CON 3 (05/09/2026) ... NAF · STB · TCB van mo"   ->  that ra con 2
"bo dem ket qua da dong nay la 1"                 ->  that ra la 2
```

**Số về SỔ không gác được bằng test.** `tests/test_tai_lieu_khop_hang_so.py`
đối chiếu tài liệu với **hằng số trong mã** — nhưng sổ nằm trên mạng và tự
đổi khi thị trường chạy, không có hằng số nào để đối chiếu. Phòng thủ duy
nhất là **một lệnh đọc nó**, chạy đều.

CHỈ ĐỌC — VÀ ĐIỀU ĐÓ ĐƯỢC KHOÁ BẰNG TEST
────────────────────────────────────────
Kéo vào một DB **tạm**, đúng đường `tools/canh_cong_c5.py` đã dùng. Không
chạm `paper_trades.db`, không gọi `push()`. Ngày 12/08/2026 một lượt ghi đè
đã xoá 96/113 lệnh thật; `tests/test_doc_so_that.py` đọc bằng **AST** rằng
file này không gọi một hàm ghi nào.
"""
import argparse
import collections
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def keo_ve_so_tam(ghi=print) -> tuple[object, dict] | None:
    """Kéo sổ thật vào một DB TẠM rồi mở nó. Không chạm sổ ở gốc repo."""
    import google_sheets_sync as gs
    from paper_trading import PaperTradingJournal

    tam = Path(tempfile.gettempdir()) / "doc_so_that.db"
    if tam.exists():
        tam.unlink()
    bao_cao = gs.keo_so_co_thu_lai(str(tam), ghi=ghi)
    if bao_cao is None:
        return None
    return PaperTradingJournal(str(tam)), bao_cao


def tom_tat(trades: list) -> dict:
    """Thống kê thuần trên một danh sách lệnh. Không gọi mạng, không I/O."""
    theo_tt = collections.Counter(getattr(t, "status", "") for t in trades)
    chua_dong = [t for t in trades
                 if getattr(t, "status", "") in ("OPEN", "PENDING")]
    return {"tong": len(trades),
            "theo_trang_thai": dict(theo_tt),
            "chua_dong": chua_dong}


def tien_ve_truoc(trades: list, moc_tin_hieu: str) -> dict:
    """Lệnh có `signal_date` >= mốc — tức sinh ra SAU khi bắt đầu quét tiến.

    Mốc truyền vào chứ không gõ trong này: nó là một QUYẾT ĐỊNH về cách
    đọc, và để nó ở đây thì nó sẽ trôi mà không ai thấy.
    """
    def ngay(t):
        return str(getattr(t, "signal_date", ""))[:10]

    trong = [t for t in trades if ngay(t) and ngay(t) >= moc_tin_hieu]
    da_dong = [t for t in trong if getattr(t, "status", "") == "CLOSED"]
    return {"tong": len(trong), "da_dong": da_dong,
            "con_mo": [t for t in trong if t not in da_dong]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--moc-tin-hieu", default="2026-08-28",
                    help="ngày tín hiệu đầu tiên của giai đoạn tiến-về-trước")
    ts = ap.parse_args()

    import paper_metrics as pm
    import paper_trading as pt

    ra = keo_ve_so_tam()
    if ra is None:
        print("CHUA DOC DUOC — kho ngoai chua cau hinh. Khong doan gi ca.",
              file=sys.stderr)
        return 2
    so, bao_cao = ra
    trades = so.all_trades()

    print("=" * 66)
    print("SO LENH THAT — doc tu Google Sheets, KHONG doc paper_trades.db")
    print("=" * 66)
    print(f"\n{bao_cao['trades']} lenh · {bao_cao['decisions']} quyet dinh")

    t = tom_tat(trades)
    print(f"\nTRANG THAI: {t['theo_trang_thai']}")
    print(f"\nVI THE CHUA DONG: {len(t['chua_dong'])}")
    for x in sorted(t["chua_dong"], key=lambda y: getattr(y, "symbol", "")):
        print(f"  {getattr(x, 'symbol', '?'):6s} {getattr(x, 'status', '?'):8s}"
              f"  tin hieu {str(getattr(x, 'signal_date', ''))[:10]:12s}"
              f"  khop {str(getattr(x, 'entry_date', '') or '—')[:10]:12s}")

    tvt = tien_ve_truoc(trades, ts.moc_tin_hieu)
    print(f"\nTIEN-VE-TRUOC (tin hieu >= {ts.moc_tin_hieu})")
    print(f"  tong        : {tvt['tong']}")
    print(f"  DA DONG     : {len(tvt['da_dong'])}   <- bo dem cua dieu kien dung")
    for x in sorted(tvt["da_dong"], key=lambda y: str(getattr(y, "exit_date", ""))):
        print(f"    {getattr(x, 'symbol', '?'):6s} ra "
              f"{str(getattr(x, 'exit_date', ''))[:10]:12s} "
              f"{getattr(x, 'exit_reason', '') or '—'}")

    print(f"\nCO C5 trong ma nguon : "
          f"CHO_PHEP_MO_LENH_MOI = {pt.CHO_PHEP_MO_LENH_MOI}")
    print(f"N_TOI_THIEU          : {pm.N_TOI_THIEU}")
    print(f"\n  {len(tvt['da_dong'])} / {pm.N_TOI_THIEU} — "
          f"{'CHUA du de ket luan gi' if len(tvt['da_dong']) < pm.N_TOI_THIEU else 'DA du co mau toi thieu'}")
    print("\nKHONG doc lai/lo cua nhung lenh nay, va KHONG duoc dung chung de")
    print("noi hay siet bat ky nguong nao — do la bat bien 7 doi huong.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
