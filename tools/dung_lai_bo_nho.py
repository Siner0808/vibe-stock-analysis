"""Dựng lại `sl_pattern_memory.json` CHỈ từ những lệnh cắt lỗ THẬT — phương án C.

BỐI CẢNH — đo ngày 20/08/2026 trên file cũ:

    6.327 mẫu · 100 mã · tín hiệu 2021-11 → 2026-07
    trường nói vòng nào / dữ liệu nào sinh ra :  KHÔNG CÓ
    khớp một lệnh THẬT trong sổ               :  56/6.327 =  0,89%
    không ứng với lệnh thật nào               :  6.271    = 99,1%

Rổ thật 71 mã, sổ thật 113 lệnh. Không cách nào sinh ra 6.327 mẫu từ 100
mã — toàn bộ là dư lượng của các vòng seed/tối ưu in-sample.

Hệ quả đo được: với dung sai ±5 trên 3 chiều, bộ nhớ cũ phủ 49,4% không
gian giá trị mà agent thật sự sinh ra, và **92,5%** số mã trong một phiên
thật bị trừ 12 điểm trên thang 100. Đó là đòn bẩy lớn nhất đang tác động
lên hành vi hệ thống — lớn hơn cả tầng tranh luận (±0,9 điểm).

VÌ SAO KHÔNG PHẢI PHƯƠNG ÁN B (giữ file, bổ sung provenance)
Thông tin để truy nguồn không tồn tại: các vòng sinh ra file đã bị
`os.remove()` xoá, chỉ 8/20 sổ sót lại và chỉ vì lần chạy đó bị gián đoạn.

VÌ SAO KHÔNG PHẢI PHƯƠNG ÁN A (xoá sạch, tắt hẳn)
A để lại một hệ thống sạch nhưng KHÔNG CÒN ĐƯỜNG ỐNG. Ngày muốn học thật
vẫn phải dựng lại từ đầu. C giữ đường ống và làm nó đúng ngay từ đầu: bộ
nhớ chỉ sinh từ lệnh đã đóng thật, và lớn lên trung thực khi sổ dày lên.

NÓI THẲNG VỀ KỲ VỌNG
Với 44 lệnh cắt lỗ hiện có, bộ nhớ mới phủ **0,9%** không gian — tức cơ chế
gần như vô hiệu. Đó là câu trả lời trung thực, không phải thất bại.

CHẠY
    python tools/dung_lai_bo_nho.py --xem        # chỉ xem, không ghi
    python tools/dung_lai_bo_nho.py --ghi        # ghi đè sl_pattern_memory.json
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SO_MAC_DINH = str(GOC / "paper_trades.db")
FILE_BO_NHO = str(GOC / "sl_pattern_memory.json")


def dung_lai(db_path: str = SO_MAC_DINH) -> list[dict]:
    """Đọc sổ lệnh, trả về danh sách mẫu hình từ các lệnh CẮT LỖ thật."""
    now = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT id, symbol, signal_date, entry_date, exit_date, entry_score,"
        " components, reasons FROM trades"
        " WHERE status = 'CLOSED' AND exit_reason LIKE '%STOP%'"
        " ORDER BY id").fetchall()
    c.close()

    mau = []
    for r in rows:
        try:
            bd = json.loads(r["components"]) if r["components"] else {}
            ly_do = json.loads(r["reasons"]) if r["reasons"] else []
        except Exception:
            bd, ly_do = {}, []
        # Thiếu breakdown thì BỎ, không điền mặc định: một mẫu dựng từ số
        # bịa còn tệ hơn không có mẫu.
        if not all(k in bd for k in
                   ("trend_score", "momentum_score", "volume_score")):
            continue
        mau.append({
            "symbol": r["symbol"],
            "signal_date": str(r["signal_date"])[:10],
            "entry_score": int(r["entry_score"] or 0),
            "trend_score": int(bd["trend_score"]),
            "momentum_score": int(bd["momentum_score"]),
            "volume_score": int(bd["volume_score"]),
            "reasons": ly_do[:3] if isinstance(ly_do, list) else [],
            "nguon": db_path,
            "trade_id": int(r["id"]),
            "entry_date": str(r["entry_date"] or "")[:10],
            "exit_date": str(r["exit_date"] or "")[:10],
            # Truc thoi gian thu hai: mau nay tro nen biet duoc vao dung
            # phien lenh dong, khong phai phien sinh tin hieu.
            "phien_hoc": str(r["exit_date"] or "")[:10],
            "ghi_luc": now,
        })
    return mau


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=SO_MAC_DINH)
    ap.add_argument("--ghi", action="store_true",
                    help="ghi đè sl_pattern_memory.json")
    ap.add_argument("--xem", action="store_true", help="chỉ xem")
    a = ap.parse_args()

    mau = dung_lai(a.db)
    cu = []
    if Path(FILE_BO_NHO).exists():
        try:
            cu = json.loads(Path(FILE_BO_NHO).read_text(encoding="utf-8"))
        except Exception:
            cu = []

    print(f"sổ lệnh          : {a.db}")
    print(f"bộ nhớ CŨ        : {len(cu)} mẫu")
    print(f"bộ nhớ MỚI       : {len(mau)} mẫu (chỉ từ lệnh cắt lỗ đã đóng)")
    if mau:
        print(f"khoảng tín hiệu  : {min(m['signal_date'] for m in mau)}"
              f" → {max(m['signal_date'] for m in mau)}")
        print(f"số mã            : {len({m['symbol'] for m in mau})}")

    if not a.ghi:
        print("\n(chưa ghi gì — thêm --ghi để ghi đè)")
        return 0

    Path(FILE_BO_NHO).write_text(
        json.dumps(mau, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Đã ghi {len(mau)} mẫu vào {FILE_BO_NHO}")
    print("   Mọi mẫu đều mang nguồn: trade_id + đường dẫn sổ + thời điểm ghi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
