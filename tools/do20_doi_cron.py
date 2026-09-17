"""Đọc tiêu chí BƯỚC 20 — *"dời cron ba chuông có tác dụng không"*, tới hạn 17/09/2026.

VÌ SAO CÓ FILE NÀY
──────────────────
`docs/STATE.md` BƯỚC 20 ký một bảng đọc ngày **03/09/2026**, trước khi mười
ngày làm việc kế tiếp tồn tại:

    Dai luong : tre TRUNG VI cua chuong-bao-quet, cac luot event=schedule
    Nen       : 247 phut (n = 9), do 03/09/2026 tren lich cu `0 9`
    Co mau    : 10 ngay lam viec ke tiep, toi het 17/09/2026 (n ~ 10)

      <=  60 phut  ->  DOI CO TAC DUNG
      >  120 phut  ->  DOI KHONG CO TAC DUNG
      60-120 phut  ->  CHUA KET LUAN DUOC, do tiep

Quy tắc số 2 của dự án: *không có lệnh thì không có số*. Một bảng mà người
phải tự trừ giờ rồi tự xếp ô thì con số của nó chưa có lệnh đứng sau. File
này là cái lệnh ấy.

MỘT BẢN CÀI ĐẶT, KHÔNG PHẢI HAI
───────────────────────────────
Phép đo trễ — khe đã hẹn, mốc TẠO, quy về khe gần nhất phía trước — đã có ở
`tools/do_roi_nhip.py` và đã được một phép đo khác dùng (BƯỚC 54). File này
**nhập** chúng, không chép lại.

Đó là bài học ngày 16/09/2026 trả giá để học: bản cài đặt thứ hai của một
phép lọc trôi ra khỏi bản thứ nhất và làm hai đột biến sống sót ngay trong
cái gác viết để chống trôi (lỗi 73). Phép sửa không phải viết gác tốt hơn
mà là **bỏ bản cài đặt thứ hai**.

Thứ file này thêm vào là đúng một thứ: **bảng phán xử của BƯỚC 20**, khác
hẳn bảng hai-đại-lượng của BƯỚC 54.

VÌ SAO CÓ PHÉP CHẶN TRÊN–DƯỚI
─────────────────────────────
Nhịp chuông nổ lúc 09:23 UTC, tức **16:23 giờ VN**. Một phiên làm việc buổi
sáng ngày 17/09 đọc được đúng **9** ngày, không phải 10 — mẫu chưa đầy.

Trả lời bằng cách đoán ngày thứ mười là bịa. Trả lời bằng cách chờ tới chiều
là bỏ phí cả buổi. Đường thứ ba: **chặn hai đầu**. Cho ngày còn thiếu nhận
giá trị NHỎ NHẤT có thể (0 phút — GitHub không tạo lượt trước khe) rồi lớn
nhất có thể, xem phán quyết có đổi không. Hai đầu cùng một ô thì con số còn
thiếu **không mang thông tin phán xử**, và điều đó tự nó đọc được.

Một phán quyết chỉ đọc được khi nó không phụ thuộc thứ chưa đo.
"""
import argparse
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from do_roi_nhip import (  # noqa: E402
    NHIP, hoi_github, khe_da_hen, khe_gan_nhat_truoc, ngay_lam_viec, tre_phut,
)

# ── Bảng đã ký BƯỚC 20. Đổi một con số ở đây là đổi tiêu chí SAU khi thấy số ──
CHUONG = "chuong-bao-quet.yml"
NEN_PHUT = 247.0                                  # lịch cũ `0 9`, n = 9
NGUONG_TOT = 60.0                                 # ≤ : dời CÓ tác dụng
NGUONG_XAU = 120.0                                # > : dời KHÔNG có tác dụng
CUA_SO = (date(2026, 9, 4), date(2026, 9, 17))    # 10 ngày làm việc, đã ký

CO_TAC_DUNG = "DOI CO TAC DUNG"
KHONG_TAC_DUNG = "DOI KHONG CO TAC DUNG"
CHUA_KET_LUAN = "CHUA KET LUAN DUOC"

#: Trần dùng cho phép chặn trên. KHÔNG phải một phép đo — nó chỉ cần lớn hơn
#: mọi trễ có thể quan sát, và một nhịp cron không sống quá 24 giờ vì nhịp
#: hôm sau sẽ thay chỗ nó.
TRAN_GIA_DINH_PHUT = 24 * 60.0


def phan_xu(trung_vi: float | None) -> tuple[str, str]:
    """Xếp trung vị trễ vào đúng một ô của bảng ĐÃ KÝ. Trả (mã, lý do).

    BA trạng thái chứ không hai — cùng quy ước với `lich_giao_dich.chan_doan`
    và `vnstock_goi.kiem_goi`. Ô giữa là ô bắt buộc: thiếu nó thì mọi số đều
    bị ép về một trong hai phán quyết mạnh.
    """
    if trung_vi is None:
        return CHUA_KET_LUAN, "khong do duoc luot nao trong cua so"
    if trung_vi <= NGUONG_TOT:
        return CO_TAC_DUNG, f"trung vi {trung_vi:.2f} <= {NGUONG_TOT:g} phut"
    if trung_vi > NGUONG_XAU:
        return (KHONG_TAC_DUNG,
                f"trung vi {trung_vi:.2f} > {NGUONG_XAU:g} phut")
    return (CHUA_KET_LUAN,
            f"trung vi {trung_vi:.2f} nam giua {NGUONG_TOT:g} va {NGUONG_XAU:g}")


def chan_hai_dau(tre_da_co: list[float],
                 so_ngay_thieu: int) -> tuple[float, float]:
    """Trung vị NHỎ NHẤT và LỚN NHẤT mà mẫu đầy có thể nhận.

    Ngày còn thiếu nhận 0 phút cho cận dưới (GitHub không tạo lượt chạy
    trước khe đã hẹn) và `TRAN_GIA_DINH_PHUT` cho cận trên.
    """
    if not tre_da_co and so_ngay_thieu <= 0:
        raise ValueError("khong co du lieu nao de chan")
    duoi = statistics.median(sorted(tre_da_co + [0.0] * so_ngay_thieu))
    tren = statistics.median(
        sorted(tre_da_co + [TRAN_GIA_DINH_PHUT] * so_ngay_thieu))
    return duoi, tren


def doc_duoc_chua(tre_da_co: list[float],
                  so_ngay_thieu: int) -> tuple[bool, str, str]:
    """Phán quyết có PHỤ THUỘC ngày còn thiếu không. Trả (đọc được, ô, lý do).

    `True` nghĩa là hai cận cho **cùng một ô** — con số chưa đo không mang
    thông tin phán xử, nên đọc bây giờ và đọc chiều nay ra cùng kết luận.
    """
    if so_ngay_thieu <= 0:
        ma, ly_do = phan_xu(statistics.median(tre_da_co) if tre_da_co else None)
        return True, ma, "mau da day, khong con ngay nao thieu"
    duoi, tren = chan_hai_dau(tre_da_co, so_ngay_thieu)
    ma_duoi, _ = phan_xu(duoi)
    ma_tren, _ = phan_xu(tren)
    if ma_duoi == ma_tren:
        return True, ma_duoi, (
            f"{so_ngay_thieu} ngay con thieu khong lat duoc phan quyet: "
            f"can duoi {duoi:.2f} va can tren {tren:.2f} phut cung mot o")
    return False, CHUA_KET_LUAN, (
        f"{so_ngay_thieu} ngay con thieu LAT duoc phan quyet: "
        f"can duoi {duoi:.2f} -> {ma_duoi}, can tren {tren:.2f} -> {ma_tren}")


def chua_toi_gio(ngay: date, bay_gio: datetime) -> bool:
    """Khe của ngày ấy còn ở phía trước — KHÔNG phải một nhịp bị rơi.

    Tách riêng vì hai thứ trông giống hệt nhau trong dữ liệu (ngày không có
    lượt nào) mà nghĩa thì ngược nhau. Gộp chúng lại là đếm một ngày chưa
    tới giờ thành một ngày hỏng — đúng chiều làm hệ thống trông tệ hơn thực
    tế, và cũng đúng chiều làm cỡ mẫu trông đầy hơn thực tế.
    """
    gio, phut = NHIP[CHUONG][0]
    return bay_gio < khe_da_hen(ngay, gio, phut)


def do(mocs: list[datetime], cua_so: tuple[date, date],
       bay_gio: datetime) -> dict:
    """Trễ từng lượt trong cửa sổ, tách ba loại ngày không có lượt nào."""
    khe = NHIP[CHUONG]
    trong = sorted(m for m in mocs if cua_so[0] <= m.date() <= cua_so[1])
    tre = [tre_phut(m, khe_gan_nhat_truoc(m, khe)) for m in trong]
    co_luot = {m.date() for m in trong}

    cho_toi = [d for d in ngay_lam_viec(cua_so)
               if d not in co_luot and chua_toi_gio(d, bay_gio)]
    roi = [d for d in ngay_lam_viec(cua_so)
           if d not in co_luot and not chua_toi_gio(d, bay_gio)]
    return {
        "moc": trong,
        "tre": tre,
        "trung_vi": statistics.median(tre) if tre else None,
        "ngay_lam_viec": ngay_lam_viec(cua_so),
        "ngay_chua_toi_gio": cho_toi,
        "ngay_roi": roi,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Doc tieu chi BUOC 20.")
    ap.add_argument("--tu", default=CUA_SO[0].isoformat())
    ap.add_argument("--den", default=CUA_SO[1].isoformat())
    tham_so = ap.parse_args()
    cua_so = (date.fromisoformat(tham_so.tu), date.fromisoformat(tham_so.den))
    if cua_so != CUA_SO:
        print(f"CANH BAO: cua so {cua_so[0]} -> {cua_so[1]} KHAC cua so da ky "
              f"{CUA_SO[0]} -> {CUA_SO[1]}. So ra KHONG doc duoc bang bang "
              f"da ky cua BUOC 20.")

    bay_gio = datetime.now(timezone.utc)
    gio, phut = NHIP[CHUONG][0]
    print("TIEU CHI BUOC 20 — khai 03/09/2026, toi han 17/09/2026")
    print(f"CUA SO  {cua_so[0]} -> {cua_so[1]}   khe {gio:02d}:{phut:02d}Z "
          f"({(gio + 7) % 24:02d}:{phut:02d} gio VN)")
    print(f"BAY GIO {bay_gio.strftime('%Y-%m-%d %H:%M:%SZ')}\n")

    ket = do(hoi_github(CHUONG), cua_so, bay_gio)
    for m, t in zip(ket["moc"], ket["tre"]):
        print(f"  {m.strftime('%Y-%m-%d %H:%M:%SZ')}   tre {t:8.2f} phut")
    if ket["ngay_roi"]:
        print("  ROI NHIP : " + ", ".join(d.isoformat() for d in ket["ngay_roi"]))
    else:
        print("  ROI NHIP : khong ngay nao")
    if ket["ngay_chua_toi_gio"]:
        print("  CHUA TOI GIO: "
              + ", ".join(d.isoformat() for d in ket["ngay_chua_toi_gio"]))

    n_co = len(ket["tre"])
    n_thieu = len(ket["ngay_chua_toi_gio"])
    print(f"\n  n = {n_co} da do  ·  {n_thieu} ngay chua toi gio  ·  "
          f"{len(ket['ngay_lam_viec'])} ngay lam viec trong cua so")

    tv = ket["trung_vi"]
    print(f"\nNEN (lich cu `0 9`, 03/09) : {NEN_PHUT:.2f} phut")
    print(f"TRUNG VI (lich moi)        : "
          + (f"{tv:.2f} phut" if tv is not None else "khong do duoc"))
    if tv is not None:
        print(f"CHENH                      : {tv - NEN_PHUT:+.2f} phut")

    doc_duoc, ma, ly_do = doc_duoc_chua(ket["tre"], n_thieu)
    print(f"\nDOC DUOC CHUA: {'CO' if doc_duoc else 'CHUA'}  —  {ly_do}")
    print(f"\nPHAN QUYET: {ma}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
