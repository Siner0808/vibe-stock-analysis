"""Đọc tiêu chí "cơ chế rơi nhịp cron" đã khai 05/09/2026, tới hạn 12/09/2026.

VÌ SAO CÓ FILE NÀY
──────────────────
`docs/STATE.md` mục *"KHAI TRƯỚC — CƠ CHẾ RƠI NHỊP"* ký một bảng đọc TRƯỚC
khi tuần 07–11/09 tồn tại. Bảng ấy có **hai ô BÁC BỎ** — đó là thứ làm nó
thành phép kiểm chứ không phải lời tiên tri.

Quy tắc số 2 của dự án: *không có lệnh thì không có số*. Một bảng đọc mà
người phải tự trừ giờ rồi tự xếp ô thì con số của nó chưa có lệnh đứng sau,
và ô đã ký có thể bị đọc lệch mà không ai thấy. File này là cái lệnh ấy.

HAI ĐẠI LƯỢNG, ĐÚNG NHƯ ĐÃ KÝ
─────────────────────────────
    A = trung vị TRỄ của `chuong-bao-quet`, các lượt `schedule`, 07 → 11/09
    B = trung vị SỐ LƯỢT `schedule` của `quet-so-lenh` mỗi ngày làm việc

Trễ đo từ **khe nhịp đã hẹn** tới lúc GitHub **TẠO** lượt chạy — không phải
tới lúc nó chạy xong, và không lọc theo `conclusion`. Đó là phân biệt BƯỚC
28 đã trả giá để ghi ra: `chuong_bao_quet.py` đếm `success` vì nó hỏi *"ngày
này có được quét không"*; đo rơi nhịp phải đếm **mọi lượt được TẠO** vì nó
hỏi *"GitHub có tạo lượt chạy không"*. Một lượt `failure` hay `queued` vĩnh
viễn vẫn là một nhịp KHÔNG rơi.

Gom ngày theo **UTC**, vì nhịp cron khai bằng UTC. Gom theo giờ VN đẩy lượt
17:16Z của 27/08 sang ngày hôm sau và đẩy một lượt sang thứ Bảy — ngày cron
không hề có nhịp.
"""
import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, date, time, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

# ── Bảng đã ký. Đổi một con số ở đây là đổi tiêu chí SAU khi thấy số ──────
NGUONG_TRE_PHUT = 120     # lấy nguyên từ tiêu chí BƯỚC 20, không chọn mới
B_NHIEU = 5               # B >= 5 : nhịp đã hồi
B_IT = 3                  # B <= 3 : nhịp chưa hồi

UNG_HO = "UNG HO"
BAC_BO = "BAC BO"
TUONG_HOP = "TUONG HOP"
CHUA_KET_LUAN = "CHUA KET LUAN DUOC"

# ── Nhịp khai trong `.github/workflows/` (giờ UTC) ────────────────────────
NHIP = {
    "chuong-bao-quet.yml": [(9, 23)],
    "canh-cong-c5.yml": [(9, 43)],
    "chuong-nguon-dung.yml": [(10, 17)],
    "quet-so-lenh.yml": [(h, m) for h in (2, 3, 4, 6, 7, 8) for m in (0, 30)],
}

CUA_SO = (date(2026, 9, 7), date(2026, 9, 11))   # đã ký, KHÔNG được nới


def khe_da_hen(ngay: date, gio: int, phut: int) -> datetime:
    """Mốc UTC mà cron hẹn cho ngày ấy."""
    return datetime.combine(ngay, time(gio, phut), tzinfo=timezone.utc)


def tre_phut(thuc_te: datetime, hen: datetime) -> float:
    """Số phút từ khe đã hẹn tới lúc lượt chạy được TẠO."""
    return (thuc_te - hen).total_seconds() / 60.0


def khe_gan_nhat_truoc(moc: datetime, khe: list[tuple[int, int]]) -> datetime:
    """Khe đã hẹn gần nhất KHÔNG SAU `moc`, tìm ngược tối đa bảy ngày.

    Một nhịp trễ bốn giờ vẫn thuộc về khe của chính ngày ấy; một nhịp trễ
    qua nửa đêm thì thuộc về khe hôm trước. Quy về khe gần nhất phía trước
    là cách duy nhất không phải đoán.
    """
    for lui in range(8):
        ngay = (moc - timedelta(days=lui)).date()
        ung_vien = [khe_da_hen(ngay, g, p) for g, p in khe]
        truoc = [k for k in ung_vien if k <= moc]
        if truoc:
            return max(truoc)
    raise ValueError(f"khong tim duoc khe da hen nao truoc {moc.isoformat()}")


def trong_cua_so(moc: datetime, cua_so: tuple[date, date]) -> bool:
    return cua_so[0] <= moc.date() <= cua_so[1]


def gom_theo_ngay(mocs: list[datetime]) -> dict[date, int]:
    """Đếm lượt mỗi ngày UTC. Ngày không có lượt nào KHÔNG xuất hiện."""
    dem: dict[date, int] = {}
    for m in mocs:
        dem[m.date()] = dem.get(m.date(), 0) + 1
    return dem


def ngay_lam_viec(cua_so: tuple[date, date]) -> list[date]:
    dau, cuoi = cua_so
    ra, d = [], dau
    while d <= cuoi:
        if d.weekday() < 5:
            ra.append(d)
        d += timedelta(days=1)
    return ra


def dem_moi_ngay_lam_viec(mocs: list[datetime],
                          cua_so: tuple[date, date]) -> list[int]:
    """Số lượt mỗi ngày làm việc, KỂ CẢ ngày 0 lượt.

    Bỏ ngày 0 lượt ra khỏi trung vị sẽ làm một tuần hỏng hoàn toàn trông
    giống một tuần không có dữ liệu — đúng chiều làm kết quả đẹp lên.
    """
    dem = gom_theo_ngay(mocs)
    return [dem.get(d, 0) for d in ngay_lam_viec(cua_so)]


def quyet_dinh(a_phut: float | None, b_luot: float | None) -> tuple[str, str]:
    """Xếp (A, B) vào đúng một ô của bảng ĐÃ KÝ. Trả (mã, lý do).

    Bảng nguyên văn:

        A <= 120 VA B >= 5  -> UNG HO    hai dai luong di cung nhau
        A <= 120 VA B <= 3  -> BAC BO    tre giam ma nhip khong hoi
        A >  120 VA B >= 5  -> BAC BO    nhip hoi ma tre khong giam
        A >  120 VA B <= 3  -> TUONG HOP, chua phan biet duoc
        B = 4               -> CHUA KET LUAN DUOC
    """
    if a_phut is None or b_luot is None:
        return CHUA_KET_LUAN, "thieu du lieu cho it nhat mot dai luong"
    if B_IT < b_luot < B_NHIEU:
        return CHUA_KET_LUAN, f"B = {b_luot:g} nam giua {B_IT} va {B_NHIEU}"
    tre_giam = a_phut <= NGUONG_TRE_PHUT
    nhip_hoi = b_luot >= B_NHIEU
    if tre_giam and nhip_hoi:
        return UNG_HO, "hai dai luong di cung nhau"
    if tre_giam and not nhip_hoi:
        return BAC_BO, "tre giam ma nhip khong hoi"
    if not tre_giam and nhip_hoi:
        return BAC_BO, "nhip hoi ma tre khong giam"
    return TUONG_HOP, "chua phan biet duoc"


# ── Lớp lấy dữ liệu — mỏng có chủ đích, để phần phán ở trên kiểm được ────
def hoi_github(workflow: str, so_luot: int = 120) -> list[datetime]:
    """Mốc TẠO của mọi lượt `schedule`, mới nhất trước."""
    ra = subprocess.run(
        ["gh", "run", "list", f"--workflow={workflow}", "--event=schedule",
         f"--limit={so_luot}", "--json", "createdAt"],
        capture_output=True, text=True, encoding="utf-8")
    if ra.returncode != 0:
        raise RuntimeError(f"gh that bai cho {workflow}: {ra.stderr.strip()}")
    return [datetime.fromisoformat(d["createdAt"].replace("Z", "+00:00"))
            for d in json.loads(ra.stdout)]


def do_mot_chuong(workflow: str, mocs: list[datetime],
                  cua_so: tuple[date, date]) -> dict:
    """Trễ từng lượt trong cửa sổ, cho một workflow một-nhịp-mỗi-ngày."""
    khe = NHIP[workflow]
    trong = sorted(m for m in mocs if trong_cua_so(m, cua_so))
    tre = [tre_phut(m, khe_gan_nhat_truoc(m, khe)) for m in trong]
    ngay_co = {m.date() for m in trong}
    thieu = [d for d in ngay_lam_viec(cua_so) if d not in ngay_co]
    return {
        "workflow": workflow,
        "so_luot": len(trong),
        "tre": tre,
        "trung_vi_tre": statistics.median(tre) if tre else None,
        "ngay_roi": thieu,
        "moc": trong,
    }


def _in_bang(ket: dict) -> None:
    print(f"\n{ket['workflow']}  —  {ket['so_luot']} luot trong cua so")
    for m, t in zip(ket["moc"], ket["tre"]):
        print(f"  {m.strftime('%Y-%m-%d %H:%M:%SZ')}   tre {t:7.2f} phut")
    if ket["ngay_roi"]:
        print("  ROI NHIP: " + ", ".join(d.isoformat() for d in ket["ngay_roi"]))
    else:
        print("  ROI NHIP: khong ngay nao")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tu", default=CUA_SO[0].isoformat())
    ap.add_argument("--den", default=CUA_SO[1].isoformat())
    tham_so = ap.parse_args()
    cua_so = (date.fromisoformat(tham_so.tu), date.fromisoformat(tham_so.den))

    if cua_so != CUA_SO:
        print(f"CANH BAO: cua so {cua_so[0]} -> {cua_so[1]} KHAC cua so da ky "
              f"{CUA_SO[0]} -> {CUA_SO[1]}. So ra KHONG doc duoc bang bang da ky.")

    print(f"CUA SO  {cua_so[0]} -> {cua_so[1]}  (gio UTC, ngay lam viec)")

    # ── Đại lượng A ──────────────────────────────────────────────────────
    bao = do_mot_chuong("chuong-bao-quet.yml",
                        hoi_github("chuong-bao-quet.yml"), cua_so)
    _in_bang(bao)
    a = bao["trung_vi_tre"]

    # ── Đại lượng B ──────────────────────────────────────────────────────
    quet = [m for m in hoi_github("quet-so-lenh.yml") if trong_cua_so(m, cua_so)]
    moi_ngay = dem_moi_ngay_lam_viec(quet, cua_so)
    b = statistics.median(moi_ngay) if moi_ngay else None
    print(f"\nquet-so-lenh.yml  —  {len(quet)} luot / "
          f"{len(NHIP['quet-so-lenh.yml']) * len(ngay_lam_viec(cua_so))} nhip")
    for d, n in zip(ngay_lam_viec(cua_so), moi_ngay):
        print(f"  {d.isoformat()}   {n:2d}/12 luot")

    # ── Dự đoán thứ hai: ba chuông, 15 ngày-chuông ───────────────────────
    print("\nDU DOAN 2 — ba chuong, 15 ngay-chuong, du doan ROI 0")
    tong_roi = 0
    for wf in ("chuong-bao-quet.yml", "canh-cong-c5.yml",
               "chuong-nguon-dung.yml"):
        k = do_mot_chuong(wf, hoi_github(wf), cua_so)
        tong_roi += len(k["ngay_roi"])
        print(f"  {wf:24s} {k['so_luot']}/{len(ngay_lam_viec(cua_so))} no"
              + (f"  ROI: {k['ngay_roi']}" if k["ngay_roi"] else ""))
    print(f"  TONG: roi {tong_roi}/15 ngay-chuong")

    # ── Phán quyết ───────────────────────────────────────────────────────
    ma, ly_do = quyet_dinh(a, b)
    print(f"\nA = {a:.2f} phut" if a is not None else "\nA = khong do duoc")
    print(f"B = {b:g} luot/ngay" if b is not None else "B = khong do duoc")
    print(f"\nPHAN QUYET: {ma}  —  {ly_do}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
