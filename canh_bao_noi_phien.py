"""Cảnh báo chạm stop-loss / take-profit TRONG PHIÊN.

VÌ SAO CẦN
──────────
`evaluate_open()` chấm trên nến NGÀY, nên nó chỉ biết một vị thế đã chạm
stop-loss sau khi phiên đóng cửa. Nến 30 phút cho biết điều đó ngay trong
phiên — chạm lúc 10:05 thì không phải đợi tới 15:30 mới hay.

RANH GIỚI: BÁO, KHÔNG ĐỘNG VÀO SỔ
─────────────────────────────────
Module này **không đổi trạng thái lệnh nào**. Đây không phải sự thận trọng
thừa mà là điều kiện để mọi con số của dự án còn so sánh được với nhau:

  · Toàn bộ backtest và walk-forward đóng lệnh trên nến NGÀY.
  · Nếu sổ lệnh THẬT đóng lệnh theo nến 30 phút, nó sẽ được đo bằng một
    thước khác với thước đã dùng cho mọi kết quả ngoài mẫu. Hai bên không
    còn đối chiếu được, mà đối chiếu chính là thứ dự án này sống bằng.

Nên vai trò của nó đúng như ranh giới đã ghi ở CLAUDE.md: **agent chuẩn bị,
người xác nhận, người đặt lệnh.** Nó nói "ACB chạm stop-loss lúc 10:30" và
dừng ở đó.

GIẢ ĐỊNH BẤT LỢI VẪN GIỮ NGUYÊN
───────────────────────────────
Bất biến 3 nói nến ngày chạm cả SL lẫn TP thì lấy SL. Nến nội phiên biết
cái nào tới trước, nhưng module này KHÔNG dùng nó để sửa kết quả — nó chỉ
báo. Muốn dùng nến nội phiên để đo lại giả định đó thì là một phép đo
riêng, có vùng dữ liệu riêng, không phải việc của một cái chuông.

ĐƠN VỊ GIÁ
──────────
Sổ lệnh lưu VNĐ (`stop_loss = 21158.0`); `intraday_data.tai()` cũng trả
VNĐ. Hai bên khớp — nhưng module này KIỂM chứ không tin: lệch 1.000 lần là
đúng cái bẫy đã ghi ở NGUYEN-TAC-DO-LUONG.md, và `low <= stop_loss` khi đó
luôn đúng, tức báo động giả cho mọi mã. Lệch thì NỔ.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Giá nến so với mốc SL/TP phải cùng bậc. Ngoài dải này là lệch hệ đơn vị.
TY_LE_HOP_LE = (0.1, 10.0)

MUI_GIO_VN = timezone(timedelta(hours=7))


class DonViLechError(RuntimeError):
    """Giá nến và mốc SL/TP không cùng một hệ đơn vị."""


@dataclass(frozen=True)
class CanhBao:
    symbol: str
    loai: str          # "SL" hoặc "TP"
    muc: float         # mức stop-loss / take-profit
    gia_cham: float    # giá của nến đã chạm
    luc_nen: str       # thời điểm cây nến chạm
    tre_phut: float    # từ lúc nến đóng tới lúc phát hiện

    def dong_log(self) -> str:
        ten = "stop-loss" if self.loai == "SL" else "take-profit"
        return (f"{self.symbol}: chạm {ten} {self.muc:,.0f} lúc {self.luc_nen} "
                f"(giá {self.gia_cham:,.0f}) — phát hiện trễ "
                f"{self.tre_phut:.0f} phút")


def vi_the_dang_mo(db_path: str) -> list[dict]:
    """Các lệnh còn OPEN, kèm mốc SL/TP. Chỉ ĐỌC, không mở journal."""
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    try:
        rows = c.execute(
            "SELECT symbol, entry_date, entry_price, stop_loss, take_profit "
            "FROM trades WHERE status = 'OPEN'").fetchall()
    finally:
        c.close()
    return [dict(r) for r in rows]


def _kiem_don_vi(symbol: str, nen, muc: float) -> None:
    """Nổ nếu giá nến và mốc lệch bậc.

    Fail-closed có chủ đích: thà không báo gì còn hơn báo cho mọi mã mỗi
    phiên. Một cái chuông kêu oan vài lần là một cái chuông bị tắt.
    """
    if muc is None or muc <= 0 or nen is None or len(nen) == 0:
        return
    giua = float(nen["close"].median())
    if giua <= 0:
        return
    ty = giua / float(muc)
    if not (TY_LE_HOP_LE[0] <= ty <= TY_LE_HOP_LE[1]):
        raise DonViLechError(
            f"{symbol}: giá nến trung vị {giua:,.0f} so với mốc {muc:,.0f} "
            f"lệch {ty:.4g} lần — hai hệ đơn vị khác nhau. Không so được.")


def kiem_mot(lenh: dict, nen, bay_gio: datetime) -> CanhBao | None:
    """Cây nến ĐẦU TIÊN trong ngày chạm SL hoặc TP, hoặc None.

    Lấy cây ĐẦU TIÊN chứ không phải cây gần nhất: câu hỏi là "chạm lúc
    nào", và biết sớm nhất mới tính được độ trễ thật của cảnh báo.

    Chạm cả hai trong cùng một cây nến thì lấy SL — bất biến 3. Trong một
    cây nến 30 phút vẫn không biết bên nào tới trước.
    """
    if nen is None or len(nen) == 0:
        return None

    sl = lenh.get("stop_loss")
    tp = lenh.get("take_profit")
    _kiem_don_vi(lenh["symbol"], nen, sl or tp)

    dau_tien = None
    for _, hang in nen.iterrows():
        cham_sl = sl and float(hang["low"]) <= float(sl)
        cham_tp = tp and float(hang["high"]) >= float(tp)
        if cham_sl or cham_tp:
            # Cùng một nến chạm cả hai -> SL (bất biến 3).
            loai = "SL" if cham_sl else "TP"
            dau_tien = (hang, loai)
            break

    if dau_tien is None:
        return None

    hang, loai = dau_tien
    luc = hang["time"]
    luc_dt = luc.to_pydatetime() if hasattr(luc, "to_pydatetime") else luc
    if luc_dt.tzinfo is None:
        luc_dt = luc_dt.replace(tzinfo=MUI_GIO_VN)
    tre = (bay_gio - luc_dt).total_seconds() / 60.0

    return CanhBao(
        symbol=lenh["symbol"], loai=loai,
        muc=float(sl if loai == "SL" else tp),
        gia_cham=float(hang["low"] if loai == "SL" else hang["high"]),
        luc_nen=luc_dt.strftime("%Y-%m-%d %H:%M"),
        tre_phut=max(tre, 0.0))


def loc_dung_ngay(nen, ngay: str):
    """Chỉ giữ nến của ĐÚNG ngày `ngay`.

    KHÔNG tin phạm vi ngày của nguồn. Đo 21/08/2026: gọi
    `idd.tai("ACB", "2026-08-21", "2026-08-21", "30m")` trả về 12 nến, trong
    đó có cả 2026-08-20 14:00 — mà một phiên HOSE chỉ có 9 nến 30 phút.

    Không lọc thì một lệnh chạm stop-loss HÔM QUA — vốn đã được nến ngày xử
    lý xong — sẽ bị báo lại mỗi ngày, và độ trễ in ra là 1.604 phút thay vì
    vài chục phút. Chuông kêu oan mỗi phiên là chuông sắp bị tắt.
    """
    if nen is None or len(nen) == 0:
        return nen
    t = nen["time"]
    if not hasattr(t, "dt"):
        import pandas as pd
        t = pd.to_datetime(t)
    return nen[t.dt.strftime("%Y-%m-%d") == str(ngay)[:10]].reset_index(drop=True)


def quet(db_path: str, ngay: str, bay_gio: datetime, tai_nen) -> dict:
    """Quét mọi vị thế đang mở. Trả về báo cáo, KHÔNG đổi gì trong sổ.

    `tai_nen(symbol, ngay)` tách ra làm tham số để test chạy offline.
    """
    mo = vi_the_dang_mo(db_path)
    canh_bao: list[CanhBao] = []
    loi: list[str] = []

    for lenh in mo:
        try:
            nen = tai_nen(lenh["symbol"], ngay)
        except Exception as e:
            # Một mã hỏng không được làm im cả cái chuông.
            loi.append(f"{lenh['symbol']}: {type(e).__name__}: {str(e)[:120]}")
            continue
        try:
            cb = kiem_mot(lenh, loc_dung_ngay(nen, ngay), bay_gio)
        except DonViLechError as e:
            loi.append(str(e))
            continue
        if cb is not None:
            canh_bao.append(cb)

    return {"so_vi_the": len(mo), "canh_bao": canh_bao, "loi": loi}


# ═════════════════════════════════════════════════════════════════════
# CANH GÁC ĐƯỜNG DỮ LIỆU
#
# VÌ SAO CẦN
# ──────────
# `quet()` chỉ gọi `tai_nen` khi CÓ vị thế đang mở. Sổ rỗng thì vòng lặp
# không chạy lần nào, nên toàn bộ đường dữ liệu — gọi mạng, khoá API, lọc
# lưới 24/7, quy đơn vị — KHÔNG hề được thực thi.
#
# Đo trên lượt chạy 22/08/2026: 113 lệnh, tất cả đã đóng, 0 đang mở. Bước
# cảnh báo hết 0,35 giây và in "không vị thế nào chạm SL/TP" — đúng, nhưng
# nó không chứng minh được gì ngoài việc `vi_the_dang_mo()` chạy được.
#
# Và 0 vị thế không phải chuyện tạm thời: ngưỡng mua đang để trống (ô C5)
# VÀ VN-INDEX nằm dưới MA50. Đường mã đó sẽ nằm im cho tới đúng ngày đầu
# tiên có lệnh mở — tức nó chạy lần đầu vào đúng lúc nó buộc phải đúng.
#
# Canh gác nạp thử MỘT mã khi sổ rỗng. Có vị thế thì các lần nạp thật đã
# tự chứng minh rồi, nên điều kiện này phủ đúng chỗ trống, không phủ chồng.
#
# KHÔNG ĐƯỢC KÊU OAN
# ──────────────────
# Nhịp 09:00 chạy trước khi nến 30 phút đầu tiên kịp đóng, nên "hôm nay 0
# nến" là BÌNH THƯỜNG chứ không phải hỏng. Vì thế canh gác hỏi một KHOẢNG
# ngày chứ không hỏi riêng hôm nay: nguồn trả được nến của tuần trước là
# nguồn còn sống, bất kể chạy lúc mấy giờ. Chỉ khi nguồn NÉM hoặc trả rỗng
# cả khoảng mới tính là hỏng.
# ═════════════════════════════════════════════════════════════════════

# Mã canh gác phải là vốn hoá lớn, thanh khoản cao, và có giá VNĐ cao hơn
# hẳn NGUONG_VND — xem `_kiem_thang_gia`.
MA_CANH_GAC = "ACB"

# Đủ trùm một kỳ nghỉ lễ dài. Ngắn hơn thì nghỉ Tết hoá thành "nguồn hỏng".
SO_NGAY_CANH_GAC = 10

# Giá VNĐ của một mã vốn hoá lớn không bao giờ xuống dưới mức này; giá theo
# NGHÌN ĐỒNG thì không bao giờ lên trên. Ranh giới tách hai hệ đơn vị.
NGUONG_VND = 1_000.0


@dataclass(frozen=True)
class CanhGac:
    ma: str
    song: bool              # nguồn trả về được dữ liệu
    so_ngay: int
    so_nen_tong: int
    so_nen_hom_nay: int
    gia_giua: float | None
    loi: str | None

    @property
    def dat(self) -> bool:
        """Đường dữ liệu vừa sống vừa đúng thang đo."""
        return self.song and self.loi is None

    def dong_log(self) -> str:
        if not self.song:
            return f"canh gác {self.ma}: ĐƯỜNG DỮ LIỆU HỎNG — {self.loi}"
        if self.loi is not None:
            return f"canh gác {self.ma}: dữ liệu bất thường — {self.loi}"
        return (f"canh gác {self.ma}: nguồn sống — {self.so_nen_tong} nến "
                f"trong {self.so_ngay} ngày gần nhất, {self.so_nen_hom_nay} "
                f"nến hôm nay, giá trung vị {self.gia_giua:,.0f} VNĐ")


def _kiem_thang_gia(ma: str, giua: float) -> str | None:
    """None nếu giá đúng thang VNĐ, ngược lại trả câu giải thích.

    Đây là cái bẫy đã ghi ở NGUYEN-TAC-DO-LUONG.md: nguồn trả nghìn đồng
    thì `low <= stop_loss` đúng với MỌI vị thế, tức báo động giả toàn bộ.
    `_kiem_don_vi()` bắt được nó — nhưng chỉ khi có vị thế để so. Sổ rỗng
    thì không có mốc nào, nên ở đây so với một hằng số thay cho mốc.
    """
    if giua >= NGUONG_VND:
        return None
    return (f"giá trung vị {giua:,.2f} < {NGUONG_VND:,.0f} — {ma} là mã vốn "
            f"hoá lớn nên giá VNĐ phải cao hơn nhiều. Nhiều khả năng nguồn "
            f"đã chuyển sang nghìn đồng.")


def canh_gac(ngay: str, tai_khoang, ma: str = MA_CANH_GAC,
             so_ngay: int = SO_NGAY_CANH_GAC) -> CanhGac:
    """Nạp thử nến của một mã để chứng minh đường dữ liệu còn dùng được.

    `tai_khoang(ma, tu_ngay, den_ngay)` tách ra làm tham số để test chạy
    offline, y như `tai_nen` của `quet()`.
    """
    den = str(ngay)[:10]
    tu = (datetime.strptime(den, "%Y-%m-%d")
          - timedelta(days=so_ngay)).strftime("%Y-%m-%d")

    def _hong(ly_do: str) -> CanhGac:
        return CanhGac(ma=ma, song=False, so_ngay=so_ngay, so_nen_tong=0,
                       so_nen_hom_nay=0, gia_giua=None, loi=ly_do)

    try:
        nen = tai_khoang(ma, tu, den)
    except Exception as e:
        return _hong(f"{type(e).__name__}: {str(e)[:140]}")

    if nen is None or len(nen) == 0:
        return _hong(f"nguồn trả bảng rỗng cho {tu}..{den}")

    giua = float(nen["close"].median())
    return CanhGac(ma=ma, song=True, so_ngay=so_ngay, so_nen_tong=len(nen),
                   so_nen_hom_nay=len(loc_dung_ngay(nen, den)),
                   gia_giua=giua, loi=_kiem_thang_gia(ma, giua))


def quet_va_canh_gac(db_path: str, ngay: str, bay_gio: datetime,
                     tai_nen, tai_khoang, ma: str = MA_CANH_GAC) -> dict:
    """`quet()`, cộng canh gác khi sổ KHÔNG có vị thế nào đang mở.

    Điều kiện nằm ở đây chứ không nằm trong YAML là có chủ đích: "khi nào
    cần canh gác" là logic, mà logic trong heredoc thì không test được —
    bài học đã lặp lại nhiều lần ở dự án này.
    """
    r = quet(db_path, ngay, bay_gio, tai_nen)
    r["canh_gac"] = (canh_gac(ngay, tai_khoang, ma)
                     if r["so_vi_the"] == 0 else None)
    return r
