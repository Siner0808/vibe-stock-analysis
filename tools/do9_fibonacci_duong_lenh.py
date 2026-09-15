"""ĐO 9 — mức Fibonacci trong ĐƯỜNG SINH LỆNH. Một lượt mỗi lần gọi.

Tiêu chí đọc đã ký TRƯỚC khi có dòng mã nào của phép đo này:
`docs/TIEU-CHI-DOC-TRUOC.md`, mục **ĐO 9**. Đừng đọc alpha trước khi đọc
bảng kết cục ở đó — nó tồn tại đúng để không ai chọn cách đọc sau khi đã
thấy số.

BỐN LƯỢT, và chỉ BA phép so đọc được
────────────────────────────────────
    A   SL=ATR   TP=+20%        CHOT_LOI_CUNG=TAT   doi chung = hien hanh
    B   SL=FIBO  TP=+20%        CHOT_LOI_CUNG=TAT   chi doi SL
    C   SL=ATR   TP=+20%        CHOT_LOI_CUNG=BAT   chi doi cong tac
    D   SL=FIBO  TP=FIBO        CHOT_LOI_CUNG=BAT   doi ca ba

    doc duoc:  A<->B (SL)  ·  A<->C (cong tac)  ·  C<->D (muc TP)
    KHONG doc: A<->D — ba thu doi cung luc

Lượt **C là PHÉP KIỂM DỤNG CỤ**: nó phải dựng lại hình dạng đã biết của
`CHOT_LOI_CUNG=True` (phương sai giảm đáng kể, alpha không đổi trong phạm
vi KTC). C không tái lập được thì **dừng, không đọc B và D**.

MỖI LƯỢT MỘT TIẾN TRÌNH
───────────────────────
`_ANALYZE_CACHE` trong `paper_runner` sống theo tiến trình, và hai lượt
khác cờ mà dùng chung cache là hai lượt cùng đọc một kết quả đã chấm với
cờ của lượt trước. Chạy từng lượt một, mỗi lượt một lần gọi.
"""
import argparse
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

#: {tên lượt: (dùng mức Fibonacci, chốt lời cứng)}
LUOT = {
    "A": (False, False),
    "B": (True, False),
    "C": (False, True),
    "D": (True, True),
}

VAI_TRO = {
    "A": "đối chứng = hiện hành",
    "B": "chỉ đổi SL",
    "C": "chỉ đổi công tắc — PHÉP KIỂM DỤNG CỤ",
    "D": "đổi cả ba",
}


def chay_mot_luot(ten: str, symbols: str | None = None) -> int:
    """Chạy đúng một lượt TRONG tiến trình này.

    `symbols` CHỈ để thử đường ống trước khi giao cả rổ. Bảng ĐO 9 chạy
    KHÔNG truyền tham số này — đổi rổ mã là đổi câu hỏi.
    """
    dung_fibo, chot_cung = LUOT[ten]

    sys.path.insert(0, str(GOC))
    import paper_trading

    # Trượt giá: KHẲNG ĐỊNH cấu hình mặc định, không đặt nó.
    # Một kịch bản lặng lẽ đặt lại cờ là một kịch bản đo cấu hình của
    # chính nó, không đo cấu hình đang chạy.
    if paper_trading.MO_PHONG_TRUOT_GIA is not True:
        print(f"DỪNG: ĐO 9 phải đo ở trượt giá BẬT, mà "
              f"MO_PHONG_TRUOT_GIA đang là "
              f"{paper_trading.MO_PHONG_TRUOT_GIA!r}. Sửa tiêu chí trước.",
              file=sys.stderr)
        return 2

    paper_trading.DUNG_MUC_FIBONACCI = dung_fibo
    paper_trading.CHOT_LOI_CUNG = chot_cung

    import paper_runner
    import walkforward

    for k in paper_runner.DEM_MUC:
        paper_runner.DEM_MUC[k] = 0

    sys.argv = ["walkforward.py", "--theo-ngay"]
    if symbols:
        sys.argv += ["--symbols", symbols]

    print("=" * 72)
    print(f"ĐO 9 · LƯỢT {ten} — {VAI_TRO[ten]}")
    print(f"  DUNG_MUC_FIBONACCI = {paper_trading.DUNG_MUC_FIBONACCI}")
    print(f"  CHOT_LOI_CUNG      = {paper_trading.CHOT_LOI_CUNG}")
    print(f"  MO_PHONG_TRUOT_GIA = {paper_trading.MO_PHONG_TRUOT_GIA}")
    print(f"  chế độ             = theo ngày")
    print(f"  rổ mã              = {symbols or 'CẢ RỔ (mặc định)'}")
    print("=" * 72)

    ma = walkforward.main()

    d = paper_runner.DEM_MUC
    tong = sum(d.values())
    print()
    print("NGUỒN MỨC — con số này phải đọc TRƯỚC alpha")
    print("-" * 72)
    print(f"  dùng Fibonacci            : {d['fibonacci']}")
    print(f"  về ATR · thiếu cấu trúc   : {d['ve_atr_thieu_cau_truc']}")
    print(f"  về ATR · rủi ro quá biên  : {d['ve_atr_qua_rui_ro']}")
    if tong:
        print(f"  -> tỷ lệ áp được Fibonacci: {d['fibonacci'] / tong:.1%} "
              f"trên {tong} lượt chấm")
    if dung_fibo and d["fibonacci"] == 0:
        print("\n  ⚠️ CỜ BẬT MÀ KHÔNG LƯỢT NÀO DÙNG FIBONACCI. Lượt này KHÔNG "
              "đo cái nó định đo — đừng đọc alpha của nó.", file=sys.stderr)
    print()
    print("Đọc alpha SAU KHI đọc docs/TIEU-CHI-DOC-TRUOC.md mục ĐO 9.")
    return ma


def main() -> int:
    ap = argparse.ArgumentParser(description="ĐO 9 — Fibonacci vào đường lệnh")
    ap.add_argument("--luot", choices=sorted(LUOT), required=True,
                    help="A đối chứng · B chỉ SL · C kiểm dụng cụ · D cả ba")
    ap.add_argument("--symbols",
                    help="CHỈ để thử đường ống. Bảng thật không truyền.")
    a = ap.parse_args()
    return chay_mot_luot(a.luot, a.symbols)


if __name__ == "__main__":
    sys.exit(main())
