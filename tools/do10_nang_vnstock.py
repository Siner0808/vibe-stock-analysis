"""Đọc bảng ĐO 10 — `vnstock` 4.0.7 → 4.0.8 có đổi CON SỐ không.

VÌ SAO CÓ FILE NÀY
──────────────────
`vnai` 2.6.0 đóng lại được bằng phép so mã nguồn, vì hai file quyết định
dữ liệu giống hệt từng byte. Với `vnstock` 4.0.8 thì **mọi file trên
đường dữ liệu đều đổi** — `api/quote.py`, `explorer/vci/quote.py`,
`explorer/kbs/*`, và `core/utils/parser.py` co lại 16%. Nên câu hỏi *"nó
có đổi số không"* **không trả lời được bằng cách đọc mã**.

Quy tắc số 2 của dự án: *không có lệnh thì không có số*. File này là cái
lệnh ấy, và nó chạy HAI LƯỢT — trước khi nâng và sau khi nâng — trên
CÙNG tham số.

BẢNG ĐỌC nằm ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 10, khai **trước** khi
con số đầu tiên tồn tại. File này không được mang một bảng đọc thứ hai.

    A khac DU MOT O                            ->  KHONG NANG
    B hoac C doi TAP COT                       ->  KHONG NANG
    A giong het + B,C tap cot giong + D giong  ->  NANG DUOC
    khong keo duoc du lieu                     ->  CHUA KET LUAN DUOC

BA Ô, KHÔNG PHẢI HAI
────────────────────
Ô thứ ba bắt buộc. Một lượt kéo hỏng — mất mạng, hết hạn mức — mà bị đọc
thành *"không đổi gì"* là đúng lỗi 66: một kết quả âm từ một mẫu không
thể cho kết quả dương thì nói về MẪU, không nói về giả thuyết.

VÌ SAO A ĐO TRÊN KHOẢNG ĐÃ ĐÓNG
───────────────────────────────
Dữ liệu đã đóng thì **phải** bất biến. Nếu nó đổi giữa hai lượt thì đó là
THƯ VIỆN đổi, không phải thị trường đổi. Đo trên khoảng đang mở thì hai
lượt chạy cách nhau vài phút đã khác nhau, và phép so không quy được cho
vế nào — đúng hình dạng `stride` ở BƯỚC 21.
"""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.stdout.reconfigure(encoding="utf-8")

#: Ký trong `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 10. Đổi một giá trị ở đây là
#: đổi tiêu chí sau khi thấy số.
MA = ("FPT", "VCB", "SSI")
DAU, CUOI = "2024-01-02", "2024-03-29"      # khoảng ĐÃ ĐÓNG
NGUON_GIA = "VCI"

CO_TAC_DUNG = "NANG DUOC"
KHONG_NANG = "KHONG NANG"
CHUA_KET_LUAN = "CHUA KET LUAN DUOC"

TEN_ANH = "vibe_do10_vnstock.json"


def duong_anh() -> Path:
    return Path(tempfile.gettempdir()) / TEN_ANH


def _bam_bang(df) -> dict:
    """Vân tay một bảng: hình dạng · cột · băm nội dung · hai đầu.

    Băm trên CSV chứ không trên `repr`: `repr` cắt bớt khi bảng dài, nên
    hai bảng khác nhau ở giữa sẽ cho cùng một chuỗi. Đúng lớp lỗi "máy đo
    hẹp hơn thứ nó đo".
    """
    if df is None:
        return {"loi": "None"}
    try:
        csv = df.to_csv(index=False)
    except Exception as e:                    # bia-ok: khong doc duoc bang
        return {"loi": f"{type(e).__name__}: {e}"}
    return {
        "dong": int(len(df)),
        "cot": [str(c) for c in df.columns],
        "bam": hashlib.sha256(csv.encode("utf-8")).hexdigest(),
        "dau": csv.splitlines()[1] if len(csv.splitlines()) > 1 else "",
        "cuoi": csv.splitlines()[-1] if len(csv.splitlines()) > 1 else "",
    }


def do_A() -> dict:
    """OHLCV ngày, khoảng ĐÃ ĐÓNG. Đọc được TỪNG Ô."""
    from vnstock import Quote
    ra = {}
    for ma in MA:
        try:
            df = Quote(symbol=ma, source=NGUON_GIA).history(
                start=DAU, end=CUOI, interval="1D")
            ra[ma] = _bam_bang(df)
        except Exception as e:                # bia-ok: ghi LOI, khong thay so
            ra[ma] = {"loi": f"{type(e).__name__}: {e}"}
    return ra


def do_B() -> dict:
    """Bảng giá. CHỈ đọc TẬP CỘT — giá đổi theo từng phiên."""
    from vnstock import Trading
    try:
        df = Trading(source="vci").price_board(list(MA))
        return {"cot": sorted(str(c) for c in df.columns),
                "dong": int(len(df))}
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return {"loi": f"{type(e).__name__}: {e}"}


def do_C() -> dict:
    """Chỉ số tài chính. Đọc SỐ KỲ + TẬP CỘT, không đọc giá trị."""
    from vnstock import Finance
    ra = {}
    for ma in MA:
        try:
            df = Finance(source="VCI", symbol=ma, period="year",
                         show_log=False).ratio()
            ra[ma] = {"dong": int(len(df)),
                      "cot": sorted(str(c) for c in df.columns)}
        except Exception as e:                # bia-ok: ghi LOI, khong thay so
            ra[ma] = {"loi": f"{type(e).__name__}: {e}"}
    return ra


def do_D() -> str:
    import vnstock_goi
    try:
        return str(vnstock_goi.kiem_goi())
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return f"LOI {type(e).__name__}: {e}"


def phien_ban() -> str:
    import importlib.metadata as md
    return md.version("vnstock")


def chup() -> dict:
    return {"vnstock": phien_ban(), "A": do_A(), "B": do_B(),
            "C": do_C(), "D": do_D()}


def _co_loi(x) -> bool:
    if isinstance(x, dict):
        return "loi" in x or any(_co_loi(v) for v in x.values())
    return False


def phan_xu(truoc: dict, sau: dict) -> tuple[str, list[str]]:
    """Xếp hai ảnh chụp vào đúng MỘT ô của bảng ĐÃ KÝ. Trả (mã, lý do)."""
    ly_do = []
    if _co_loi(truoc) or _co_loi(sau):
        return CHUA_KET_LUAN, ["co it nhat mot luot keo HONG — xem truong `loi`"]

    for ma in MA:
        a, b = truoc["A"].get(ma, {}), sau["A"].get(ma, {})
        if a != b:
            khac = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
            ly_do.append(f"A[{ma}] KHAC o: {khac}")
    if ly_do:
        return KHONG_NANG, ly_do

    if truoc["B"].get("cot") != sau["B"].get("cot"):
        return KHONG_NANG, ["B doi TAP COT"]
    for ma in MA:
        if truoc["C"].get(ma, {}).get("cot") != sau["C"].get(ma, {}).get("cot"):
            ly_do.append(f"C[{ma}] doi TAP COT")
    if ly_do:
        return KHONG_NANG, ly_do

    if truoc["D"] != sau["D"]:
        return KHONG_NANG, ["D (kiem_goi) doi"]
    return CO_TAC_DUNG, ["A giong het tung o · B,C giu tap cot · D giu nguyen"]


def _in(nhan: str, d: dict) -> None:
    print(f"\n{nhan}  (vnstock {d['vnstock']})")
    for ma in MA:
        a = d["A"].get(ma, {})
        if "loi" in a:
            print(f"  A {ma}: LOI {a['loi'][:70]}")
        else:
            print(f"  A {ma}: {a['dong']:3d} dong · {len(a['cot'])} cot · "
                  f"bam {a['bam'][:16]}")
    b = d["B"]
    print(f"  B    : " + (b["loi"][:70] if "loi" in b
                          else f"{len(b['cot'])} cot · {b['dong']} dong"))
    for ma in MA:
        c = d["C"].get(ma, {})
        if "loi" in c:
            print(f"  C {ma}: LOI {c['loi'][:70]}")
        else:
            print(f"  C {ma}: {c['dong']} ky · {len(c['cot'])} cot")
    print(f"  D    : {d['D'][:100]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Doc bang DO 10.")
    ap.add_argument("che_do", choices=["truoc", "sau"],
                    help="`truoc` chup va luu; `sau` chup roi SO")
    a = ap.parse_args()

    d = chup()
    if a.che_do == "truoc":
        duong_anh().write_text(json.dumps(d, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        _in("ANH CHUP TRUOC", d)
        print(f"\nda luu: {duong_anh()}")
        return 0

    try:
        truoc = json.loads(duong_anh().read_text(encoding="utf-8"))
    except OSError:
        print(f"CHUA CO anh chup truoc o {duong_anh()} — chay `truoc` da.")
        return 2

    _in("TRUOC", truoc)
    _in("SAU", d)
    if truoc["vnstock"] == d["vnstock"]:
        print(f"\nCANH BAO: hai luot cung mot phien ban {d['vnstock']} — "
              f"phep so nay khong noi gi ve phep nang.")
    ma, ly_do = phan_xu(truoc, d)
    print("\nLY DO:")
    for x in ly_do:
        print(f"  - {x}")
    print(f"\nPHAN QUYET: {ma}")
    return 0 if ma == CO_TAC_DUNG else 1


if __name__ == "__main__":
    raise SystemExit(main())
