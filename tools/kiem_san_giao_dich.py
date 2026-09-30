"""So bảng sàn trong repo (`san_giao_dich.BANG_SAN`) với `Listing` ở hai nguồn.

Bảng là một BẢN CHỤP nên nó có thể cũ đi khi một mã chuyển sàn hay bị huỷ
niêm yết. Công cụ này hỏi lại `Listing(source=...).symbols_by_exchange()` ở VCI
và KBS, chuẩn hoá nhãn (VCI ghi `HSX`, KBS ghi `HOSE`) rồi nói ra TỪNG mã lệch —
không nén thành một con số.

    ./.venv/Scripts/python.exe tools/kiem_san_giao_dich.py

Mã thoát: 0 bảng khớp cả hai nguồn ở mọi mã · 1 có mã lệch, hai nguồn bất đồng,
hoặc mã không xác định được sàn · 2 CHƯA KIỂM ĐƯỢC (mất mạng, thiếu thư viện).
Mất mạng mà trả "khớp" thì phép kiểm này thành đúng thứ nó sinh ra để bắt.

Chạy bằng tay khi rổ đổi hoặc định kỳ; KHÔNG nằm trong đường quét hay CI —
mạng ở đó làm phép đo mất tái lập (bất biến 2).
"""
from __future__ import annotations

import sys

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from san_giao_dich import BANG_SAN, chuan_hoa_nhan  # noqa: E402

NGUON = ("vci", "kbs")


def so_sanh(bang: dict[str, str],
            theo_nguon: dict[str, dict[str, object]]) -> dict[str, list]:
    """Hàm THUẦN. `theo_nguon` = {nguồn: {mã: NHÃN THÔ của nguồn}}.

    Trả:
      lech            [(mã, bảng, {nguồn: sàn})]  nguồn nói sàn khác bảng
      bat_dong        [(mã, {nguồn: sàn})]        hai nguồn nói khác nhau
      khong_xac_dinh  [(mã, {nguồn: nhãn thô})]   nhãn lạ hoặc mã vắng ở nguồn
    Một mã vừa lệch vừa bất đồng hiện ở CẢ hai danh sách.
    """
    lech, bat_dong, khong_xac_dinh = [], [], []
    for ma in sorted(bang):
        tho = {n: theo_nguon.get(n, {}).get(ma) for n in theo_nguon}
        san = {n: chuan_hoa_nhan(v) if v is not None else None
               for n, v in tho.items()}
        if any(v is None for v in san.values()):
            khong_xac_dinh.append((ma, tho))
            continue
        if len(set(san.values())) > 1:
            bat_dong.append((ma, san))
        if any(v != bang[ma] for v in san.values()):
            lech.append((ma, bang[ma], san))
    return {"lech": lech, "bat_dong": bat_dong,
            "khong_xac_dinh": khong_xac_dinh}


def _tai_nguon() -> dict[str, dict[str, object]]:
    from vnstock import Listing
    ra: dict[str, dict[str, object]] = {}
    for nguon in NGUON:
        d = Listing(source=nguon).symbols_by_exchange()
        ra[nguon] = {str(s).upper(): e for s, e in zip(d["symbol"], d["exchange"])}
    return ra


def main() -> int:
    try:
        theo_nguon = _tai_nguon()
    except Exception as e:                       # mất mạng / thiếu thư viện
        print(f"CHƯA KIỂM ĐƯỢC — {type(e).__name__}: {str(e)[:150]}")
        return 2
    kq = so_sanh(BANG_SAN, theo_nguon)
    from san_giao_dich import NGAY_CHUP
    print(f"bảng chụp {NGAY_CHUP} · {len(BANG_SAN)} mã · nguồn: {', '.join(NGUON)}")
    for ma, bang, san in kq["lech"]:
        print(f"  LỆCH        {ma}: bảng {bang} · nguồn {san}")
    for ma, san in kq["bat_dong"]:
        print(f"  BẤT ĐỒNG    {ma}: {san}")
    for ma, tho in kq["khong_xac_dinh"]:
        print(f"  KHÔNG XĐ    {ma}: nhãn thô {tho}")
    n = sum(len(v) for v in kq.values())
    if n:
        print(f"{n} dòng cần xem — sửa `BANG_SAN` (và ngày chụp) rồi chạy lại.")
        return 1
    print("KHỚP — mọi mã của bảng có cùng sàn ở cả hai nguồn.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
