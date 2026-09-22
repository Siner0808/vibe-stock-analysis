"""Đường lấy GIAO DỊCH NỘI BỘ có trả dữ liệu không?

`MO-XE-KIEN-TRUC.md` nêu ba nguồn độc lập: BCTC theo quý · **giao dịch nội
bộ** · khối ngoại mua ròng. Hai nguồn đầu và cuối đã đo — `docs/STATE.md`
BƯỚC 53 và BƯỚC 113. Đây là nguồn còn lại.

ĐÂY LÀ PHÉP DÒ ĐƯỜNG, KHÔNG PHẢI PHÉP ĐO TÍN HIỆU
Không có bảng tiêu chí ký trước, và đó là chủ ý: câu hỏi ở đây là *"đường
này có trả dữ liệu không"*, trả lời được bằng chính lượt gọi. Dựng một
bảng tiêu chí cho một câu hỏi đã có đáp án là diễn kịch theo chiều ngược
với ô `pyarrow` — cùng một lỗi, khác dấu.

BA TRẠNG THÁI PHẢI TÁCH ĐƯỢC, VÀ CHÚNG TRÔNG Y HỆT NHAU
    a) nguon THAT SU khong co du lieu nay
    b) duong bi KHOA o hang tai khoan
    c) duong HONG
`vnstock_pipeline` đã từng bị khoá ở hạng silver **trong khi**
`license/verify` vẫn liệt kê nó — nên (b) là khả năng có thật, không phải
lo hão.

ĐỐI CHỨNG DƯƠNG tách được (a) khỏi (b) và (c): gọi thêm những endpoint
KHÁC của **cùng một nguồn, cùng một mã**. Nếu chúng trả dữ liệu thì nguồn
sống và tài khoản có quyền, nên con số 0 nói về **dữ liệu**, không nói về
**quyền truy cập**.

BA TRẠNG THÁI MÃ THOÁT
    0  duong CO tra du lieu
    1  duong KHONG tra du lieu, va doi chung DUONG dat -> doc duoc
    2  CHUA KIEM DUOC — doi chung am, hoac import no
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

#: Bốn nguồn `Company` nhận. Hỏi HẾT thay vì đoán nguồn nào có.
NGUON = ("VCI", "KBS", "ASEAN", "CAFEF")

#: Endpoint đang hỏi.
DICH = "insider_trading"

#: Endpoint dùng làm ĐỐI CHỨNG DƯƠNG — cùng lớp, cùng nguồn, cùng mã.
DOI_CHUNG = ("officers", "shareholders", "news", "overview")


def _so_dong(df) -> int | None:
    """Số dòng, hoặc None khi KHÔNG ĐẾM ĐƯỢC.

    Trả 0 ở nhánh hỏng thì phía sau không phân biệt được *"nguồn trả về
    rỗng"* với *"tôi không đọc nổi thứ nguồn trả về"* — hai kết luận
    ngược nhau. Luật R3 của `chan_bia_so_lieu`.
    """
    if df is None:
        return None
    try:
        return int(len(df))
    except TypeError:
        return None


def goi(nguon: str, ma: str, ten: str):
    """(số dòng | None, mô tả lỗi). KHÔNG nuốt lỗi thành số."""
    import vnstock_data as vd

    try:
        co = vd.Company(nguon, ma)
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:70]}"
    if not hasattr(co, ten):
        return None, "khong co ten nay"
    try:
        return _so_dong(getattr(co, ten)()), ""
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:70]}"


def do_nguon(ma: str) -> dict:
    """Nguồn nào nhận `insider_trading`, và nguồn ấy trả gì."""
    print(f"\n{'=' * 64}\nBON NGUON, ma {ma}\n{'=' * 64}")
    ra = {}
    for ng in NGUON:
        n, loi = goi(ng, ma, DICH)
        ra[ng] = {"so_dong": n, "loi": loi}
        mo_ta = loi if loi else f"{n} dong"
        print(f"  {ng:<7} {DICH} -> {mo_ta}")
    return ra


def doi_chung_duong(nguon: str, ma: str) -> dict:
    """Cùng nguồn, cùng mã, endpoint KHÁC — nguồn có sống không."""
    print(f"\n{'=' * 64}\nDOI CHUNG DUONG — {nguon}, ma {ma}\n{'=' * 64}")
    ra = {}
    for ten in DOI_CHUNG:
        n, loi = goi(nguon, ma, ten)
        ra[ten] = {"so_dong": n, "loi": loi}
        print(f"  {ten:<14} -> {loi if loi else f'{n} dong'}")
    co = [t for t, d in ra.items() if (d["so_dong"] or 0) > 0]
    print(f"  -> {len(co)}/{len(DOI_CHUNG)} endpoint KHAC co du lieu: {co}")
    return ra


def quet_ro(nguon: str, ma_list: list[str], nghi: float) -> dict:
    """Cả rổ — để lời khai nói về RỔ, không nói về vài mã."""
    print(f"\n{'=' * 64}\nQUET RO — {len(ma_list)} ma tren nguon {nguon}\n{'=' * 64}")
    co, rong, hong = [], [], []
    for i, ma in enumerate(ma_list, 1):
        n, loi = goi(nguon, ma, DICH)
        if n is None:
            hong.append(ma)
        elif n > 0:
            co.append(f"{ma}({n})")
        else:
            rong.append(ma)
        if i % 20 == 0 or i == len(ma_list):
            print(f"  {i:>3}/{len(ma_list)}  co {len(co)} · rong {len(rong)}"
                  f" · hong {len(hong)}")
        time.sleep(nghi)
    print(f"\n  CO du lieu : {len(co)}/{len(ma_list)}  {co[:10]}")
    print(f"  RONG       : {len(rong)}/{len(ma_list)}")
    print(f"  HONG       : {len(hong)}/{len(ma_list)}  {hong[:10]}")
    return {"co": len(co), "rong": len(rong), "hong": len(hong),
            "tong": len(ma_list), "ma_co": co}


def phan_dinh(ro: dict, dc: dict) -> tuple[int, str]:
    """Đọc ba trạng thái, KHÔNG gộp hai cái cuối."""
    dc_co = sum(1 for d in dc.values() if (d["so_dong"] or 0) > 0)
    if ro.get("co", 0) > 0:
        return 0, f"DUONG CO TRA DU LIEU — {ro['co']}/{ro['tong']} ma"
    if dc_co == 0:
        return 2, ("CHUA KIEM DUOC — doi chung AM: khong endpoint nao khac"
                   " cua cung nguon tra du lieu, nen con so 0 noi ve QUYEN"
                   " TRUY CAP chu khong noi ve DU LIEU")
    return 1, (f"DUONG KHONG TRA DU LIEU — 0/{ro['tong']} ma, va doi chung"
               f" DUONG dat ({dc_co}/{len(DOI_CHUNG)} endpoint khac CO du"
               f" lieu). Con so 0 nay DOC DUOC.")


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Duong giao dich noi bo co tra du lieu khong")
    ap.add_argument("--ma-moc", default="FPT")
    ap.add_argument("--nguon-quet", default="KBS",
                    help="nguon dem di quet ca ro")
    ap.add_argument("--so-ma", type=int, default=0)
    ap.add_argument("--nghi", type=float, default=0.2)
    ap.add_argument("--ra", default="")
    a = ap.parse_args(tham_so)

    try:
        import vnstock_data  # noqa: F401
    except Exception as e:  # noqa: BLE001
        print(f"CHUA KIEM DUOC — import vnstock_data no: {type(e).__name__}: {e}")
        return 2

    from vn100_symbols import VN100_SYMBOLS

    ket_nguon = do_nguon(a.ma_moc)
    dc = doi_chung_duong(a.nguon_quet, a.ma_moc)
    ma_list = VN100_SYMBOLS[:a.so_ma] if a.so_ma else list(VN100_SYMBOLS)
    ro = quet_ro(a.nguon_quet, ma_list, a.nghi)

    ma_thoat, cau = phan_dinh(ro, dc)
    print(f"\n{'=' * 64}\nPHAN DINH: {cau}\n{'=' * 64}")

    if a.ra:
        Path(a.ra).write_text(json.dumps(
            {"nguon": ket_nguon, "doi_chung": dc, "ro": ro,
             "phan_dinh": cau, "ma_thoat": ma_thoat,
             "ngay": time.strftime("%Y-%m-%d")},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ghi: {a.ra}")
    return ma_thoat


if __name__ == "__main__":
    sys.exit(main())
