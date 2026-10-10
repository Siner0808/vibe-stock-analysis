"""Bản tin cuối ngày — MỘT trang cho MỘT ngày phiên của agent (BƯỚC 174, mốc B2).

Lõi dự án (`docs/STATE.md` BƯỚC 122): agent tự đặt lệnh ảo, tự học; người dùng
học theo sổ. Hôm nay muốn biết một ngày của agent, người dùng phải tự ghép nhiều
tab. Bản tin gom lại thành MỘT trang: thị trường · agent đã làm gì · vì sao ·
học được gì.

CHỈ ĐỌC. Module THUẦN: nhận các dòng `decisions` / `trades` / `nhat_ky` đúng
như sổ lưu và một bảng VN-INDEX, trả một `BanTin` đóng băng. Không mạng, không
đồng hồ, không đĩa, không ghi sổ, không tải giá, không gọi `so_bai_hoc` (hàm đó
cần giá). Không đổi điểm, ngưỡng, cổng hay cách khớp của sổ — chỉ app và
`tools/ban_tin.py` nhập module này (gác AST: `tests/test_ban_tin.py`).

BỐN LUẬT ĐỌC (mỗi cái từ một sự cố hoặc một bất biến)
─────────────────────────────────────────────────────
1. **Khử trùng lặp trước khi đếm** (`docs/STATE.md`, mục *"Đọc đúng con số
   16.183 quyết định"*): mỗi ngày có 2–3 lượt quét nên một cặp (mã, ngày tín
   hiệu) có nhiều dòng `decisions`. Một cặp = MỘT mã trong bản tin:
     · `acted`   = CÓ dòng nào acted (lượt 1 mở lệnh, lượt 2 ghi "đã có vị thế
                   đang mở" thì mã ấy ĐÃ MỞ — lấy dòng cuối sẽ nói ngược);
     · điểm      = điểm của dòng `seq` LỚN nhất (lượt quét cuối ngày, nến sát
                   nến đóng nhất);
     · lý do bỏ  = lý do của dòng `seq` lớn nhất, khi không dòng nào acted.
2. **Đạt ngưỡng = điểm >= ngưỡng** (như `paper_trading.consider_entry`: bỏ khi
   `score < threshold`), HOẶC đã mở lệnh ở một lượt nào đó trong ngày. Vế sau
   để mã mở lệnh ở lượt 1 rồi tụt điểm ở lượt 2 không biến mất khỏi phép đếm.
   `nguong` BẮT BUỘC, không mặc định: người gọi truyền `BUY_THRESHOLD`.
3. **Nhóm lý do gom theo HẰNG SỐ `paper_trading.LY_DO_*`**, so khớp chuỗi đầu như
   sổ ghi (lý do trần vốn mang số, nên gom theo tiền tố). Lý do không có hằng số
   (cổng VN-INDEX, chất lượng dữ liệu, thiếu SL/TP, điểm dưới ngưỡng) in
   NGUYÊN VĂN như sổ ghi — module không gõ lại chữ nào của sổ.
4. **Thiếu gì nói đó, không điền số thay thế.** D không phải phiên · lịch không
   phủ D · không có nến VN-INDEX của D · không có quyết định ngày D · nhật ký
   chưa điền nửa ĐÓNG: mỗi trường hợp là một câu nói rõ lý do.

GIỚI HẠN (khai thẳng)
─────────────────────
· Số vị thế "cuối ngày D" dựng lại từ trạng thái HIỆN TẠI của `trades` (ngày
  khớp, ngày thoát, trạng thái). Đúng với mọi lệnh chỉ đổi ngày MỘT lần; không
  đúng nếu sổ sửa ngày sau này.
· "Đóng ngày D" = `status == CLOSED` và `exit_date == D`. Lệnh `CLOSING` mang sẵn
  `exit_date` = ngày tín hiệu thoát (chưa khớp) và lệnh `HUY` mang `exit_date` =
  ngày bị huỷ: cả hai KHÔNG phải lệnh đã đóng, nên có dòng riêng.
· Bảng VN-INDEX có thể trùng ngày ở cuối chuỗi (`docs/STATE.md`, "Bẫy dữ liệu
  mới"): module bỏ trùng giữ dòng cuối trước khi so phiên.
· Bản tin KHÔNG đo lợi thế nào. Một ngày không phải bằng chứng (bất biến 5).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import lich_giao_dich
import paper_trading
from nhat_ky_vi_sao import vni_so_voi_ma50
from paper_trading import Status

CAU_RANH_GIOI = "Bản tin đọc từ sổ lệnh ẢO. Không phải khuyến nghị đặt lệnh thật."
CAU_KHONG_BAI_HOC = "Hôm nay không có lệnh đóng — chưa có bài học mới."
CAU_TRO_SO_BAI_HOC = ("Phân rã nguyên nhân từng lệnh (thị trường · ngành · riêng "
                      "mã/tín hiệu · chi phí): mục «Sổ bài học» trong tab "
                      "«📜 Lịch sử giao dịch» (B3).")

CONG_MO = "MỞ"
CONG_DONG = "ĐÓNG"

SO_TOP = 5

#: Hằng số lý do của sổ mà bản tin gom nhóm. So khớp theo CHUỖI ĐẦU: lý do trần
#: vốn mang số đứng sau tiền tố. Lấy TÊN từ `paper_trading`, không gõ lại chữ.
NHOM_LY_DO: tuple[str, ...] = (
    paper_trading.LY_DO_DANG_GIU,
    paper_trading.LY_DO_TRAN_VON,
    paper_trading.LY_DO_C5,
)
NHAN_KHONG_LY_DO = "(sổ không ghi lý do)"


@dataclass(frozen=True)
class ThiTruong:
    phien: Optional[bool]             # True có phiên · False nghỉ · None lịch không phủ
    dong_cua: Optional[float]
    pct_doi: Optional[float]          # % so với phiên liền trước
    ma50: Optional[float]
    pct_tren_ma50: Optional[float]
    cong: Optional[str]               # CONG_MO · CONG_DONG · None = chưa kiểm được
    ghi_chu: tuple[str, ...]          # mỗi mục thiếu một câu nói rõ vì sao


@dataclass(frozen=True)
class MaChamDiem:
    """Một mã SAU khi khử trùng lặp (mã, ngày tín hiệu)."""
    ma: str
    diem: Optional[int]               # điểm của dòng seq LỚN nhất
    da_mo: bool                       # có dòng nào acted
    ly_do_bo: str                     # lý do dòng seq lớn nhất ("" nếu da_mo)
    nhom: str                         # nhóm lý do ("" nếu da_mo)
    dat_nguong: bool
    so_luot: int


@dataclass(frozen=True)
class LenhTrongNgay:
    id: Optional[int]
    ma: str
    ngay_tin_hieu: str
    gia_vao: Optional[float]
    gia_ra: Optional[float]
    ty_trong_pct: Optional[float]
    ly_do_ra: Optional[str]
    loi_nhuan_rong_pct: Optional[float]   # chỉ từ nhật ký; None = nhật ký chưa có


@dataclass(frozen=True)
class BaiHocLenh:
    """Nửa ĐÓNG của nhật ký cho một lệnh đóng ngày D."""
    id: Optional[int]
    ma: str
    co_nua_dong: bool
    ghi_chu: Optional[str]            # vì sao không có nửa ĐÓNG
    ly_do_ra: Optional[str]
    loi_nhuan_rong_pct: Optional[float]
    ket_qua_R: Optional[float]
    alpha_pct: Optional[float]
    hau_kiem_may: Optional[str]


@dataclass(frozen=True)
class BanTin:
    ngay: str
    nguong: float
    thi_truong: ThiTruong
    co_quyet_dinh: bool
    so_cham: int
    so_dat: int
    mo_moi: tuple[MaChamDiem, ...]
    khop: tuple[LenhTrongNgay, ...]
    dong: tuple[LenhTrongNgay, ...]
    huy: tuple[LenhTrongNgay, ...]
    cho_thoat: tuple[LenhTrongNgay, ...]
    dang_mo: int
    dang_cho: int
    nhom_bo: tuple[tuple[str, tuple[str, ...]], ...]   # (nhóm lý do, các mã) đạt mà không mở
    top: tuple[MaChamDiem, ...]
    hoc: tuple[BaiHocLenh, ...]
    cau_ranh_gioi: str


# ─────────────────────────────────────────────────────────────────────
# Đọc ô
# ─────────────────────────────────────────────────────────────────────
def _ngay(x: Any) -> str:
    """10 ký tự đầu của một ngày; rỗng/None -> ''."""
    if x is None:
        return ""
    return str(x).strip()[:10]


def _co(v: Any) -> bool:
    """Cột `acted` (0/1, có thể là chuỗi từ ô sheet). None -> False."""
    if v is None or v == "":
        return False
    return int(v) != 0


def _seq(r: dict) -> int:
    s = r.get("seq")
    if s is None or s == "":
        raise ValueError(f"dòng quyết định thiếu seq (mã {r.get('symbol')!r}): "
                         "không biết lượt nào sau lượt nào nên không khử trùng được")
    return int(s)


def _nhom_ly_do(ly_do: str) -> str:
    if not ly_do:
        return NHAN_KHONG_LY_DO
    for tien_to in NHOM_LY_DO:
        if ly_do.startswith(tien_to):
            return tien_to
    return ly_do


def ngay_gan_nhat(quyet_dinh: list[dict]) -> Optional[str]:
    """Ngày tín hiệu LỚN nhất trong các dòng quyết định; None nếu không có."""
    ds = [_ngay(r.get("signal_date")) for r in quyet_dinh]
    ds = [d for d in ds if d]
    return max(ds) if ds else None


# ─────────────────────────────────────────────────────────────────────
# 1. Thị trường
# ─────────────────────────────────────────────────────────────────────
def _thi_truong(vni_df: Any, ngay: str) -> ThiTruong:
    phien = lich_giao_dich.co_phien(ngay)
    ghi_chu: list[str] = []
    if phien is False:
        return ThiTruong(False, None, None, None, None, None,
                         (f"{ngay} không phải ngày giao dịch (cuối tuần hoặc ngày nghỉ "
                          f"của Sở) — không có phiên để tóm tắt.",))
    if phien is None:
        ghi_chu.append(f"Chưa kiểm được {ngay} có phiên hay không: lịch giao dịch chỉ "
                       f"phủ {lich_giao_dich.PHU_TU} → {lich_giao_dich.PHU_TOI}.")
    if vni_df is None or len(vni_df) == 0:
        ghi_chu.append("VN-INDEX: không đọc được bảng giá (chưa nạp dữ liệu).")
        return ThiTruong(phien, None, None, None, None, None, tuple(ghi_chu))

    d = vni_df.copy()
    d["time"] = d["time"].astype(str).str[:10]
    d = d.sort_values("time").drop_duplicates(subset="time", keep="last")
    d = d.reset_index(drop=True)
    sub = d[d["time"] <= ngay]
    if sub.empty:
        ghi_chu.append(f"VN-INDEX: bảng giá không có nến nào tới hết {ngay}.")
        return ThiTruong(phien, None, None, None, None, None, tuple(ghi_chu))
    nen_cuoi = str(sub["time"].iloc[-1])
    if nen_cuoi != ngay:
        ghi_chu.append(f"VN-INDEX: chưa có nến ngày {ngay} (nến gần nhất {nen_cuoi}) — "
                       f"không nói số của {ngay}.")
        return ThiTruong(phien, None, None, None, None, None, tuple(ghi_chu))

    v = vni_so_voi_ma50(d, ngay)
    dong_cua, ma50, pct = v["vni_close"], v["vni_ma50"], v["vni_pct_tren_ma50"]
    pct_doi = None
    if len(sub) >= 2:
        truoc = float(sub["close"].iloc[-2])
        if truoc != 0:
            pct_doi = (dong_cua / truoc - 1.0) * 100.0
        else:
            ghi_chu.append("VN-INDEX: giá đóng phiên liền trước bằng 0 — không tính % đổi.")
    else:
        ghi_chu.append("VN-INDEX: không có phiên liền trước trong bảng — không tính % đổi.")
    cong = None
    if ma50 is None:
        ghi_chu.append("VN-INDEX: thiếu MA50 tại ngày này (chưa đủ phiên) — chưa kiểm được cổng.")
    else:
        cong = CONG_MO if dong_cua >= ma50 else CONG_DONG
    return ThiTruong(phien, dong_cua, pct_doi, ma50, pct, cong, tuple(ghi_chu))


# ─────────────────────────────────────────────────────────────────────
# 2–3. Agent đã làm gì · vì sao (khử trùng lặp)
# ─────────────────────────────────────────────────────────────────────
def _khu_trung(quyet_dinh: list[dict], ngay: str, nguong: float) -> list[MaChamDiem]:
    theo_ma: dict[str, list[dict]] = {}
    for r in quyet_dinh:
        if _ngay(r.get("signal_date")) != ngay:
            continue
        ma = str(r.get("symbol") if r.get("symbol") is not None else "").strip()
        if ma:
            theo_ma.setdefault(ma, []).append(r)
    ra = []
    for ma, ds in theo_ma.items():
        cuoi = max(ds, key=_seq)
        da_mo = any(_co(r.get("acted")) for r in ds)
        diem = cuoi.get("score")
        diem = None if diem is None or diem == "" else int(diem)
        ly_do = "" if da_mo else str(cuoi.get("skip_reason") or "")
        dat = da_mo or (diem is not None and diem >= nguong)
        ra.append(MaChamDiem(ma=ma, diem=diem, da_mo=da_mo, ly_do_bo=ly_do,
                             nhom="" if da_mo else _nhom_ly_do(ly_do),
                             dat_nguong=dat, so_luot=len(ds)))
    return ra


def _khoa_diem(m: MaChamDiem):
    return (m.diem is None, -(m.diem if m.diem is not None else 0), m.ma)


# ─────────────────────────────────────────────────────────────────────
# Lệnh
# ─────────────────────────────────────────────────────────────────────
def _so_thuc(x: Any) -> Optional[float]:
    return None if x is None or x == "" else float(x)


def _lenh(l: dict, nk_theo_id: dict[int, dict]) -> LenhTrongNgay:
    lid = None if l.get("id") in (None, "") else int(l["id"])
    nk = nk_theo_id.get(lid) if lid is not None else None
    return LenhTrongNgay(
        id=lid, ma=str(l.get("symbol")), ngay_tin_hieu=_ngay(l.get("signal_date")),
        gia_vao=_so_thuc(l.get("entry_price")), gia_ra=_so_thuc(l.get("exit_price")),
        ty_trong_pct=_so_thuc(l.get("size_pct")),
        ly_do_ra=(None if l.get("exit_reason") in (None, "") else str(l["exit_reason"])),
        loi_nhuan_rong_pct=(None if nk is None else _so_thuc(nk.get("loi_nhuan_rong_pct"))))


def _vi_the_cuoi_ngay(lenh: list[dict], ngay: str) -> tuple[int, int]:
    """(đang mở, đang chờ khớp) cuối ngày `ngay`, dựng từ ngày trong từng lệnh."""
    mo = cho = 0
    for l in lenh:
        tin_hieu = _ngay(l.get("signal_date"))
        if not tin_hieu or tin_hieu > ngay:
            continue
        vao, ra = _ngay(l.get("entry_date")), _ngay(l.get("exit_date"))
        if l.get("status") in (Status.CLOSED, Status.HUY) and ra and ra <= ngay:
            continue
        if vao and vao <= ngay:
            mo += 1
        else:
            cho += 1
    return mo, cho


def _bai_hoc(l: dict, nk_theo_id: dict[int, dict]) -> BaiHocLenh:
    lid = None if l.get("id") in (None, "") else int(l["id"])
    ma = str(l.get("symbol"))
    ly_do_ra = None if l.get("exit_reason") in (None, "") else str(l["exit_reason"])
    nk = nk_theo_id.get(lid) if lid is not None else None
    if nk is None:
        return BaiHocLenh(lid, ma, False, "sổ không có dòng nhật ký cho lệnh này",
                          ly_do_ra, None, None, None, None)
    if _ngay(nk.get("exit_date")) == "":
        return BaiHocLenh(lid, ma, False,
                          "nhật ký chưa điền nửa ĐÓNG (điền ở lượt quét kế tiếp)",
                          ly_do_ra, None, None, None, None)
    return BaiHocLenh(
        lid, ma, True, None, ly_do_ra,
        _so_thuc(nk.get("loi_nhuan_rong_pct")), _so_thuc(nk.get("ket_qua_R")),
        _so_thuc(nk.get("alpha_pct")),
        None if nk.get("hau_kiem_may") in (None, "") else str(nk["hau_kiem_may"]))


# ─────────────────────────────────────────────────────────────────────
# Lập bản tin
# ─────────────────────────────────────────────────────────────────────
def lap_ban_tin(quyet_dinh: list[dict], lenh: list[dict], nhat_ky: list[dict],
                vni_df: Any, ngay: str, nguong: float) -> BanTin:
    """Bản tin của `ngay` từ các dòng sổ. HÀM THUẦN — xem docstring module.

    `nguong` bắt buộc (người gọi truyền `paper_trading.BUY_THRESHOLD`). Dòng
    quyết định thiếu `seq` thì NỔ (`ValueError`): không biết lượt nào sau lượt
    nào thì không khử trùng được, và đoán là điền số thay thế.
    """
    if nguong is None:
        raise TypeError("lap_ban_tin: nguong bắt buộc (truyền BUY_THRESHOLD)")
    ngay = _ngay(ngay)
    nk_theo_id = {int(d["trade_id"]): d for d in nhat_ky
                  if d.get("trade_id") not in (None, "")}

    ma_cham = _khu_trung(quyet_dinh, ngay, nguong)
    mo_moi = sorted((m for m in ma_cham if m.da_mo), key=_khoa_diem)

    bo: dict[str, list[str]] = {}
    for m in ma_cham:
        if m.dat_nguong and not m.da_mo:
            bo.setdefault(m.nhom, []).append(m.ma)
    nhom_bo = tuple((k, tuple(sorted(v)))
                    for k, v in sorted(bo.items(), key=lambda kv: (-len(kv[1]), kv[0])))

    khop = tuple(_lenh(l, nk_theo_id) for l in lenh if _ngay(l.get("entry_date")) == ngay)
    dong_ds = [l for l in lenh
               if l.get("status") == Status.CLOSED and _ngay(l.get("exit_date")) == ngay]
    huy = tuple(_lenh(l, nk_theo_id) for l in lenh
                if l.get("status") == Status.HUY and _ngay(l.get("exit_date")) == ngay)
    cho_thoat = tuple(_lenh(l, nk_theo_id) for l in lenh
                      if l.get("status") == Status.CLOSING and _ngay(l.get("exit_date")) == ngay)
    dang_mo, dang_cho = _vi_the_cuoi_ngay(lenh, ngay)

    return BanTin(
        ngay=ngay, nguong=nguong, thi_truong=_thi_truong(vni_df, ngay),
        co_quyet_dinh=bool(ma_cham), so_cham=len(ma_cham),
        so_dat=sum(1 for m in ma_cham if m.dat_nguong),
        mo_moi=tuple(mo_moi), khop=khop,
        dong=tuple(_lenh(l, nk_theo_id) for l in dong_ds),
        huy=huy, cho_thoat=cho_thoat, dang_mo=dang_mo, dang_cho=dang_cho,
        nhom_bo=nhom_bo, top=tuple(sorted(ma_cham, key=_khoa_diem)[:SO_TOP]),
        hoc=tuple(_bai_hoc(l, nk_theo_id) for l in dong_ds),
        cau_ranh_gioi=CAU_RANH_GIOI)


# ─────────────────────────────────────────────────────────────────────
# Markdown (app và CLI dùng chung)
# ─────────────────────────────────────────────────────────────────────
def _so(x: Optional[float], dang: str, thieu: str = "chưa có") -> str:
    return thieu if x is None else format(x, dang)


def _ds_lenh(ds: tuple[LenhTrongNgay, ...], voi_ket_qua: bool) -> list[str]:
    ra = []
    for l in ds:
        s = f"- **{l.ma}** (tín hiệu {l.ngay_tin_hieu}"
        if l.gia_vao is not None:
            s += f", giá vào {l.gia_vao:,.0f}"
        if l.ty_trong_pct is not None:
            s += f", cỡ {l.ty_trong_pct:.1f}%"
        s += ")"
        if voi_ket_qua:
            s += (f" — thoát vì {l.ly_do_ra or 'chưa ghi lý do'}; lợi nhuận ròng "
                  + (f"{l.loi_nhuan_rong_pct:+.2f}%" if l.loi_nhuan_rong_pct is not None
                     else "chưa có (nhật ký chưa ghi)"))
        ra.append(s)
    return ra


def _mo_ta_ma(m: MaChamDiem) -> str:
    diem = "điểm không đọc được" if m.diem is None else f"điểm {m.diem}"
    return f"{m.ma} ({diem})"


def ban_tin_markdown(bt: BanTin) -> str:
    t = bt.thi_truong
    d = [f"## 📰 Bản tin cuối ngày {bt.ngay}", ""]

    d += ["### 1. Thị trường", ""]
    if t.dong_cua is not None:
        d.append(f"- VN-INDEX đóng cửa **{t.dong_cua:,.2f}**"
                 + ("" if t.pct_doi is None else f", {t.pct_doi:+.2f}% so với phiên trước"))
        if t.ma50 is not None:
            d.append(f"- So với MA50 ({t.ma50:,.2f}): {t.pct_tren_ma50:+.2f}%")
    if t.cong is not None:
        d.append(f"- Cổng VN-INDEX của sổ: **{t.cong}**")
    d += [f"- {g}" for g in t.ghi_chu]
    d.append("")

    d += ["### 2. Agent đã làm gì", ""]
    if not bt.co_quyet_dinh:
        d.append(f"- Không có quyết định nào ghi cho ngày tín hiệu {bt.ngay} — không nói "
                 f"được agent đã chấm mã nào (chưa quét, hoặc sổ chưa được kéo về).")
    else:
        d.append(f"- Đã chấm **{bt.so_cham}** mã; **{bt.so_dat}** mã đạt ngưỡng "
                 f"{bt.nguong:g} (đếm sau khi khử trùng lặp theo mã và ngày tín hiệu).")
    d.append("- Lệnh MỞ mới: " + (", ".join(_mo_ta_ma(m) for m in bt.mo_moi)
                                  if bt.mo_moi else "không có"))
    d.append(f"- Lệnh chờ KHỚP ngày {bt.ngay}:" + ("" if bt.khop else " không có"))
    d += _ds_lenh(bt.khop, False)
    d.append(f"- Lệnh ĐÓNG ngày {bt.ngay}:" + ("" if bt.dong else " không có"))
    d += _ds_lenh(bt.dong, True)
    if bt.huy:
        d.append("- Lệnh chờ bị HUỶ (không khớp được): "
                 + ", ".join(l.ma for l in bt.huy))
    if bt.cho_thoat:
        d.append("- Lệnh có tín hiệu THOÁT ngày này, chờ khớp thoát phiên sau: "
                 + ", ".join(l.ma for l in bt.cho_thoat))
    d.append(f"- Cuối ngày: **{bt.dang_mo}** vị thế đang mở, **{bt.dang_cho}** lệnh chờ khớp.")
    d.append("")

    d += ["### 3. Vì sao", ""]
    if not bt.co_quyet_dinh:
        d.append("- Không có quyết định ngày này nên không có lý do để kể.")
    else:
        if bt.nhom_bo:
            d.append("Mã ĐẠT ngưỡng mà không mở lệnh, theo lý do sổ ghi:")
            for nhom, ma in bt.nhom_bo:
                d.append(f"- **{len(ma)} mã** ({', '.join(ma)}) — {nhom}")
        else:
            d.append("- Không có mã nào đạt ngưỡng mà không mở lệnh.")
        d += ["", f"Top {SO_TOP} điểm cao nhất:", ""]
        for m in bt.top:
            ket = "MỞ LỆNH" if m.da_mo else (m.ly_do_bo or NHAN_KHONG_LY_DO)
            d.append(f"- {_mo_ta_ma(m)} — {ket}")
    d.append("")

    d += ["### 4. Học được gì", ""]
    if not bt.hoc:
        d.append(f"- {CAU_KHONG_BAI_HOC}")
    for b in bt.hoc:
        if not b.co_nua_dong:
            d.append(f"- **{b.ma}**: {b.ghi_chu}.")
            continue
        d.append(f"- **{b.ma}** — thoát vì {b.ly_do_ra or 'chưa ghi lý do'}; "
                 f"lãi ròng {_so(b.loi_nhuan_rong_pct, '+.2f')}"
                 f"{'' if b.loi_nhuan_rong_pct is None else '%'} · "
                 f"R {_so(b.ket_qua_R, '+.2f')} · alpha {_so(b.alpha_pct, '+.2f')}")
        d.append(f"  - Hậu kiểm máy: {b.hau_kiem_may or 'chưa có'}")
    d += ["", f"_{CAU_TRO_SO_BAI_HOC}_", ""]

    d += ["---", f"_{bt.cau_ranh_gioi}_"]
    return "\n".join(d)
