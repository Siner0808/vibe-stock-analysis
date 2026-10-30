"""Đọc cấu trúc giá — đỉnh/đáy xoay chiều theo hai cấp (BƯỚC 247, Dow Lát 1) cùng BOS / CHoCH,
trạng thái Dow và chu kỳ 4 giai đoạn (BƯỚC 249, Dow Lát 2). Mốc B5 mượn.

CHỈ ĐỂ ĐỌC, KHÔNG CHẤM ĐIỂM. Đặc tả: `docs/thiet-ke-dow-cau-truc.md` mục 5.1–5.9 và 6.
Lát 1 = LÕI PIVOT; Lát 2 (cuối file) = sự kiện phá mốc theo cấp, thủy triều · mốc phủ định · con sóng,
và `ghep_chu_ky`. Chưa có ô trên app (Lát 3). Mọi sự kiện/trạng thái mang `ngay_xay_ra` và `ngay_biet`
và là hàm của TIỀN TỐ nhật ký (bất biến khi cắt mở rộng: `tests/test_cau_truc_gia_lat2.py`).

Hợp đồng
────────
Module THUẦN: không mạng, không đĩa, không đồng hồ. Vào: bảng nến ngày tăng dần
(`time`, `high`, `low`, `close`, tuỳ chọn `volume`). Ra: MỘT nhật ký sự kiện CHỈ-THÊM
(`CauTruc.nhat_ky`). Mỗi dòng mang HAI thời điểm:

  * `ngay_xay_ra` / `chi_so_xay_ra` — nến mang cực trị;
  * `ngay_biet`  / `chi_so_biet`   — nến ĐẦU TIÊN mà việc đó tính ra được chỉ từ dữ liệu
    tới hết nến ấy; luôn `chi_so_biet > chi_so_xay_ra`.

Bất biến khi cắt (gác chính, `tests/test_cau_truc_gia.py`): nhật ký của `df[:t+1]` y hệt
các dòng có `chi_so_biet <= t` của nhật ký đủ. Mọi thứ ở đây vì vậy là hàm của TIỀN TỐ
dữ liệu: không cửa sổ căn giữa, không `shift` âm, không chỉ số `[t + k]` (gác AST).
Pivot CHỜ (cực trị đang theo dõi, chưa xác nhận) KHÔNG BAO GIỜ vào nhật ký.

Ba họ bộ dò, MỖI họ hai cấp (nội bộ, swing) là HAI bộ dò độc lập:
  * `atr` (mặc định (2, 4)): máy trạng thái trên giá ĐÓNG CỬA; đỉnh xác nhận ở nến đầu tiên
    có `close <= đỉnh_chờ - k × ATR14`, đáy đối xứng. ATR14 = trung bình đơn 14 phiên của
    true range (dùng cao/thấp/đóng), chỉ các nến <= t;
  * `zigzag`: cùng máy trạng thái, ngưỡng là tỷ lệ θ của chính cực trị chờ;
  * `fractal`: nến `i` có `close` lớn hơn NGHIÊM NGẶT `close` của `N` nến mỗi bên, xác nhận ở
    nến `i + N` (cửa sổ nhìn LUI từ nến `t`, không nhìn tới). Hai họ trên xen kẽ ngay trong
    cấu trúc máy; họ này cần luật xen kẽ (hai pivot cùng loại liền nhau thì giữ cái cực trị
    hơn, bằng một dòng `thay_the` chỉ-thêm).

Giá bằng nhau: giá đóng cửa VN nằm trên lưới bước giá. Hai giá `bằng` khi chênh nhau không
quá NỬA bước giá (tra theo `truot_gia.buoc_gia` ở mức giá đang xét, đổi về đơn vị của bảng
bằng `he_so_gia`); hơn kém chỉ tính khi vượt NGHIÊM NGẶT nửa bước. Cực trị chờ bị thay khi
và chỉ khi giá mới vượt nghiêm ngặt qua nửa bước (đỉnh bằng không thay đỉnh cũ).

Hai quy ước THÊM so với đặc tả (khai ở `docs/STATE.md` BƯỚC 247):
  * cực trị nằm ở NẾN ĐẦU của bảng không bao giờ là pivot (chưa biết nó là đỉnh/đáy hay chỉ
    là chỗ cửa sổ bắt đầu; `smartmoneyconcepts` ép nến đầu làm pivot, TR §5.5);
  * ATR bằng 0 (14 phiên đứng yên) thì không xác nhận gì: ngưỡng `k × 0` sẽ biến một lùi 1 tick
    thành "đảo chiều".

Hệ số giá `he_so_gia` và sàn `san` nhận NGOÀI (như `pha_wyckoff.doc_pha`). Cố ý KHÔNG tự gọi
`data_quality.price_multiplier(df)`: nó lấy trung vị CẢ chuỗi nên cùng một nến sẽ đổi hệ số khi
cắt đuôi — phá bất biến khi cắt. Người gọi tính MỘT lần rồi truyền cho mọi lượt cắt.

Cờ nến: `khoa_bien` (`KICH_TRAN`/`KICH_SAN` qua `vong_doi_lenh.khoa_bien`, không tự suy trần từ
phần trăm) và `khong_giao_dich` (`volume == 0`) gắn lên MỌI pivot, lấy từ nến mang cực trị.
Không bỏ nến, không sửa giá, không điều chỉnh giá.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

from data_quality import EXCHANGE_LIMITS
from truot_gia import buoc_gia
from vong_doi_lenh import khoa_bien as _khoa_bien

CHU_KY_ATR = 14
#: Lưới tham số (nội bộ, swing) — đặc tả mục 5.3. KHÔNG thu hẹp sau khi thấy kết quả.
LUOI = {
    "atr": ((2, 3), (2, 4), (3, 4)),
    "fractal": ((3, 8), (5, 13), (3, 13), (5, 50)),
    "zigzag": ((0.05, 0.10), (0.05, 0.15), (0.07, 0.15)),
}
#: Mặc định hiển thị, chốt TRƯỚC khi có số đo (đặc tả mục 5.3).
MAC_DINH = ("atr", (2, 4))

CAP_NOI_BO = "noi_bo"
CAP_SWING = "swing"
CAPS = (CAP_NOI_BO, CAP_SWING)
DINH = "dinh"
DAY = "day"
XAC_NHAN = "xac_nhan"
THAY_THE = "thay_the"
HH, HL, LH, LL, BANG, CHUA_CO = "HH", "HL", "LH", "LL", "bang", "chua_co"

_CHUA_CO_HUONG = "chua_co"
_TIM_DINH = "tim_dinh"
_TIM_DAY = "tim_day"


@dataclass(frozen=True)
class Nen:
    """Một nến đã chuẩn bị: mọi đặc trưng chỉ phụ thuộc các nến <= nó."""
    chi_so: int
    ngay: str
    cao: float
    thap: float
    dong: float
    atr: float | None
    khoa_bien: str | None
    khong_giao_dich: bool


@dataclass(frozen=True)
class Pivot:
    """Một dòng nhật ký (đặc tả 5.9). `chi_so_biet > chi_so_xay_ra` luôn đúng."""
    cap: str
    loai: str
    su_kien: str
    ngay_xay_ra: str
    chi_so_xay_ra: int
    ngay_biet: str
    chi_so_biet: int
    gia: float
    nhan: str
    khoa_bien: str | None
    khong_giao_dich: bool
    thay_the_chi_so: int | None = None


@dataclass(frozen=True)
class _Cap:
    chieu: str = _CHUA_CO_HUONG
    dong: tuple = ()      # Nen kể từ pivot hiệu lực cuối (loại trừ) — nơi cực trị CHỜ nằm
    cuoi: tuple = ()      # tối đa 3 pivot hiệu lực cuối (để gắn nhãn và xen kẽ)


@dataclass(frozen=True)
class TrangThai:
    ho: str
    tham_so: tuple
    san: str
    he_so_gia: float
    caps: tuple
    dem: tuple = ()       # bộ đệm các nến gần nhất, chỉ họ fractal dùng


@dataclass(frozen=True)
class CauTruc:
    nhat_ky: tuple
    so_nen: int
    ho: str
    tham_so: tuple
    san: str
    he_so_gia: float
    trang_thai: TrangThai
    su_kien: tuple = ()               # Lát 2: các `SuKienPha` (BOS / CHOCH / KHOI_DAU), theo thứ tự biết
    con_song: tuple = ()              # Lát 2: các `ConSong` đã hoàn tất, theo thứ tự biết
    trang_thai_su_kien: object = None  # Lát 2: `TrangThaiSuKien` sau nến cuối (để chạy tiếp từng nến)


# ── chuẩn bị nến ──────────────────────────────────────────────────────────────────────────
def chuan_bi_nen(df: pd.DataFrame, san: str = "HOSE") -> list[Nen]:
    """Bảng nến -> danh sách `Nen`. Nến thứ i chỉ dùng các hàng <= i (so `shift(1)`, trung
    bình lăn 14 phía sau), nên cắt đuôi bảng không đổi các nến còn lại."""
    san_u = str(san).upper()
    if san_u not in EXCHANGE_LIMITS:
        raise ValueError(f"sàn {san!r} không có trong EXCHANGE_LIMITS {sorted(EXCHANGE_LIMITS)}")
    bien_do = EXCHANGE_LIMITS[san_u]
    thieu = {"time", "high", "low", "close"} - set(df.columns)
    if thieu:
        raise ValueError(f"thiếu cột {sorted(thieu)}")
    if len(df) == 0:
        return []
    cao = pd.to_numeric(df["high"], errors="coerce").astype(float).reset_index(drop=True)
    thap = pd.to_numeric(df["low"], errors="coerce").astype(float).reset_index(drop=True)
    dong = pd.to_numeric(df["close"], errors="coerce").astype(float).reset_index(drop=True)
    if cao.isna().any() or thap.isna().any() or dong.isna().any():
        raise ValueError("cao/thấp/đóng có ô trống — không đoán giá thay")
    gio = pd.to_datetime(df["time"]).reset_index(drop=True)
    if not gio.is_monotonic_increasing or gio.duplicated().any():
        raise ValueError("`time` phải tăng nghiêm ngặt")
    if "volume" in df.columns:
        kl = pd.to_numeric(df["volume"], errors="coerce").reset_index(drop=True)
        khong_gd = (kl == 0)
    else:
        khong_gd = pd.Series(False, index=dong.index)
    tham_chieu = dong.shift(1)
    tr = pd.concat([cao - thap, (cao - tham_chieu).abs(), (thap - tham_chieu).abs()],
                   axis=1).max(axis=1)
    tr = tr.where(~khong_gd, 0.0)
    atr = tr.rolling(CHU_KY_ATR, min_periods=CHU_KY_ATR).mean()
    ngay = gio.dt.strftime("%Y-%m-%d")
    nen = []
    for i in range(len(dong)):
        kb = _khoa_bien({"high": cao[i], "low": thap[i], "tham_chieu": tham_chieu[i]}, bien_do)
        a = atr[i]
        nen.append(Nen(chi_so=i, ngay=str(ngay[i]), cao=float(cao[i]), thap=float(thap[i]),
                       dong=float(dong[i]), atr=None if pd.isna(a) else float(a),
                       khoa_bien=kb, khong_giao_dich=bool(khong_gd[i])))
    return nen


# ── giá bằng nhau trên lưới bước giá ──────────────────────────────────────────────────────
def nua_buoc(gia: float, he_so_gia: float, san: str) -> float:
    """Nửa bước giá ở mức `gia`, tính theo đơn vị của bảng (nghìn đồng hay đồng)."""
    return buoc_gia(gia * he_so_gia, san) / 2.0 / he_so_gia


def _nhan(loai: str, gia: float, truoc: Pivot | None, he_so_gia: float, san: str) -> str:
    if truoc is None:
        return CHUA_CO
    d = gia - truoc.gia
    if abs(d) <= nua_buoc(gia, he_so_gia, san):
        return BANG
    if loai == DINH:
        return HH if d > 0 else LH
    return HL if d > 0 else LL


def _cuc_tri(dong: tuple, loai: str, he_so_gia: float, san: str) -> Nen:
    """Cực trị CHỜ của một đoạn nến. Duyệt tuần tự: nến sau chỉ thay khi vượt NGHIÊM NGẶT qua
    nửa bước giá, nên cực trị bằng nhau giữ nến SỚM nhất."""
    tot = dong[0]
    for n in dong[1:]:
        nua = nua_buoc(tot.dong, he_so_gia, san)
        if loai == DINH:
            if n.dong - tot.dong > nua:
                tot = n
        elif tot.dong - n.dong > nua:
            tot = n
    return tot


def _pivot(cap: str, loai: str, c: Nen, nen: Nen, cuoi: tuple, tt: TrangThai,
           su_kien: str = XAC_NHAN, thay_the: int | None = None) -> Pivot:
    truoc = next((p for p in reversed(cuoi) if p.loai == loai), None)
    return Pivot(cap=cap, loai=loai, su_kien=su_kien, ngay_xay_ra=c.ngay, chi_so_xay_ra=c.chi_so,
                 ngay_biet=nen.ngay, chi_so_biet=nen.chi_so, gia=c.dong,
                 nhan=_nhan(loai, c.dong, truoc, tt.he_so_gia, tt.san),
                 khoa_bien=c.khoa_bien, khong_giao_dich=c.khong_giao_dich,
                 thay_the_chi_so=thay_the)


# ── động cơ chạy tăng dần ─────────────────────────────────────────────────────────────────
def khoi_tao(ho: str = MAC_DINH[0], tham_so: tuple | None = None, san: str = "HOSE",
             he_so_gia: float = 1.0) -> TrangThai:
    if ho not in LUOI:
        raise ValueError(f"họ {ho!r} không có trong {sorted(LUOI)}")
    if tham_so is None:
        tham_so = MAC_DINH[1] if ho == MAC_DINH[0] else LUOI[ho][0]
    tham_so = tuple(tham_so)
    if len(tham_so) != 2 or not all(x > 0 for x in tham_so) or tham_so[0] >= tham_so[1]:
        raise ValueError(f"tham_so phải là (nội bộ, swing) dương và nội bộ < swing, nhận {tham_so}")
    if ho == "fractal" and not all(float(x).is_integer() for x in tham_so):
        raise ValueError("fractal cần N nguyên")
    if not he_so_gia > 0:
        raise ValueError("he_so_gia phải dương")
    if str(san).upper() not in EXCHANGE_LIMITS:
        raise ValueError(f"sàn {san!r} không có trong EXCHANGE_LIMITS {sorted(EXCHANGE_LIMITS)}")
    return TrangThai(ho=ho, tham_so=tham_so, san=str(san).upper(), he_so_gia=float(he_so_gia),
                     caps=(_Cap(), _Cap()))


def _buoc_may(tt: TrangThai, cap_ten: str, k: float, cap: _Cap, nen: Nen):
    """Một nến qua máy trạng thái (họ `atr` và `zigzag`). Trả (cap mới, các dòng mới)."""
    dong, chieu, cuoi, moi = cap.dong + (nen,), cap.chieu, cap.cuoi, []
    for _ in range(len(dong) + 1):          # vòng hữu hạn: mỗi lượt bỏ ít nhất một nến khỏi `dong`
        ung = []
        for loai in (DINH, DAY):
            if (loai == DINH and chieu == _TIM_DAY) or (loai == DAY and chieu == _TIM_DINH):
                continue
            c = _cuc_tri(dong, loai, tt.he_so_gia, tt.san)
            if c.chi_so == 0 or c.chi_so >= nen.chi_so:
                continue                     # nến đầu bảng, hoặc cực trị chính là nến này
            if tt.ho == "atr":
                if nen.atr is None or not nen.atr > 0:
                    continue
                khoang = k * nen.atr
            else:
                khoang = k * c.dong
            if loai == DINH and nen.dong <= c.dong - khoang:
                ung.append((c, loai))
            elif loai == DAY and nen.dong >= c.dong + khoang:
                ung.append((c, loai))
        if not ung:
            break
        c, loai = min(ung, key=lambda x: x[0].chi_so)
        moi.append(_pivot(cap_ten, loai, c, nen, cuoi, tt))
        cuoi = (cuoi + (moi[-1],))[-3:]
        chieu = _TIM_DAY if loai == DINH else _TIM_DINH
        dong = tuple(n for n in dong if n.chi_so > c.chi_so)
    return _Cap(chieu=chieu, dong=dong, cuoi=cuoi), moi


def _buoc_fractal(tt: TrangThai, cap_ten: str, n_nen: int, cap: _Cap, nen: Nen):
    """Họ fractal: nến `t − N` là pivot nếu lớn/nhỏ hơn nghiêm ngặt cả `2N` nến quanh nó. Chỉ
    nhìn LUI từ nến t (bộ đệm), nên `ngay_biet` = nến t."""
    n_nen = int(n_nen)
    if len(tt.dem) < 2 * n_nen + 1:
        return cap, []
    cua_so = tt.dem[-(2 * n_nen + 1):]
    tam = cua_so[n_nen]
    nua = nua_buoc(tam.dong, tt.he_so_gia, tt.san)
    khac = cua_so[:n_nen] + cua_so[n_nen + 1:]
    if all(tam.dong - x.dong > nua for x in khac):
        loai = DINH
    elif all(x.dong - tam.dong > nua for x in khac):
        loai = DAY
    else:
        return cap, []
    cuoi = cap.cuoi
    if cuoi and cuoi[-1].loai == loai:       # xen kẽ: hai pivot cùng loại liền nhau
        cu = cuoi[-1]
        hon = (tam.dong - cu.gia > nua) if loai == DINH else (cu.gia - tam.dong > nua)
        if not hon:
            return cap, []                   # giữ cái cũ (bằng nhau thì giữ cái sớm hơn)
        p = _pivot(cap_ten, loai, tam, nen, cuoi[:-1], tt, THAY_THE, cu.chi_so_xay_ra)
        return replace(cap, cuoi=cuoi[:-1] + (p,)), [p]
    p = _pivot(cap_ten, loai, tam, nen, cuoi, tt)
    return replace(cap, cuoi=(cuoi + (p,))[-3:]), [p]


def cap_nhat(tt: TrangThai, nen: Nen) -> tuple[TrangThai, list[Pivot]]:
    """Một nến vào, trạng thái mới và các dòng nhật ký mới ra. Hai cấp chạy độc lập."""
    dem = tt.dem
    if tt.ho == "fractal":
        dem = (dem + (nen,))[-(2 * int(max(tt.tham_so)) + 1):]
        tt = replace(tt, dem=dem)
    caps, dong_moi = [], []
    for ten, k, cap in zip(CAPS, tt.tham_so, tt.caps):
        if tt.ho == "fractal":
            cap2, moi = _buoc_fractal(tt, ten, k, cap, nen)
        else:
            cap2, moi = _buoc_may(tt, ten, k, cap, nen)
        caps.append(cap2)
        dong_moi.extend(moi)
    return replace(tt, caps=tuple(caps)), dong_moi


def doc_cau_truc(df: pd.DataFrame, he_so_gia: float = 1.0, san: str = "HOSE",
                 ho: str = MAC_DINH[0], tham_so: tuple | None = None) -> CauTruc:
    """Đọc cả bảng: vòng lặp trên `cap_nhat`. Giống hệt chạy từng nến."""
    nens = chuan_bi_nen(df, san)
    tt = khoi_tao(ho, tham_so, san, he_so_gia)
    tsk = khoi_tao_su_kien(tt)
    nhat_ky, su_kien = [], []
    for nen in nens:
        tt, moi = cap_nhat(tt, nen)
        tsk, sk = cap_nhat_su_kien(tsk, nen, moi)
        nhat_ky.extend(moi)
        su_kien.extend(sk)
    return CauTruc(nhat_ky=tuple(nhat_ky), so_nen=len(nens), ho=tt.ho, tham_so=tt.tham_so,
                   san=tt.san, he_so_gia=tt.he_so_gia, trang_thai=tt, su_kien=tuple(su_kien),
                   con_song=con_song_tu_nhat_ky(nhat_ky), trang_thai_su_kien=tsk)


def nhat_ky_tai(nhat_ky, chi_so_t: int) -> list[Pivot]:
    """Các dòng ĐÃ BIẾT tại nến `chi_so_t`: chỉ dùng dòng có `chi_so_biet <= chi_so_t`."""
    return [p for p in nhat_ky if p.chi_so_biet <= chi_so_t]


def pivot_cuoi_tai(nhat_ky, chi_so_t: int, cap: str, loai: str) -> Pivot | None:
    """Pivot HIỆU LỰC gần nhất cùng cấp, cùng loại, đã biết tại `chi_so_t` (dòng `thay_the` đè
    dòng bị thay)."""
    kq = None
    for p in nhat_ky_tai(nhat_ky, chi_so_t):
        if p.cap == cap and p.loai == loai:
            kq = p
    return kq


# ══ LÁT 2 (BƯỚC 249) ═══════════════════════════════════════════════════════════════════════
# Sự kiện BOS / CHoCH theo cấp (đặc tả 5.7), trạng thái Dow (5.8), chu kỳ 4 giai đoạn (6).
BOS, CHOCH, KHOI_DAU = "BOS", "CHOCH", "KHOI_DAU"
TANG, GIAM = "tang", "giam"                 # chiều phá · thiên hướng · thủy triều
LAN, CHUA_DU = "lan", "chua_du_bang_chung"  # thủy triều không rõ · chưa có hai đỉnh + hai đáy

#: Con sóng (5.8). Mặc định hiển thị chốt TRƯỚC khi có số đo: 3/8 nhịp chính VÀ 10 phiên.
PHIEN_SONG = 10
BIEN_DO_SONG = ("nhip_chinh", 3 / 8)
KIEU_SONG = "va"
#: Lưới 18 ô CHỈ ĐỂ ĐẾM (ĐO 34): biên độ × thời gian × {VÀ, HOẶC}. KHÔNG thu hẹp sau khi thấy kết quả.
LUOI_SONG = {"bien_do": (("phan_tram", 0.03), ("nhip_chinh", 1 / 3), ("nhip_chinh", 3 / 8)),
             "phien": (8, 10, 15), "kieu": ("va", "hoac")}

#: Chu kỳ 4 giai đoạn (6).
TICH_LUY, MARKUP, PHAN_PHOI, MARKDOWN = "Tích luỹ", "Markup", "Phân phối", "Markdown"
CHUA_DU_BC = "chưa đủ bằng chứng"
NGUON_WYCKOFF, NGUON_THUY_TRIEU = "pha_wyckoff", "thuy_trieu"
TEN_THUY_TRIEU = {TANG: "tăng", GIAM: "giảm", LAN: "lẫn", CHUA_DU: "chưa đủ bằng chứng"}
#: Chuỗi của `pha_wyckoff.PhaWyckoff` mà phép ghép đọc (mô-đun đó không đổi; test đối chiếu với `doc_pha` thật).
_WY_TICH_LUY, _WY_PHAN_PHOI, _WY_CHUA_PHAN_DINH = "TÍCH LUỸ", "PHÂN PHỐI", "CHƯA PHÂN ĐỊNH"
_WY_PHA_RA_VUNG, _WY_MARKUP, _WY_MARKDOWN = "E", "Markup", "Markdown"


@dataclass(frozen=True)
class SuKienPha:
    """BOS / CHOCH / KHOI_DAU của một cấp (đặc tả 5.7 khoản 5). `ngay_xay_ra == ngay_biet`: đóng cửa vượt
    mốc là biết ngay khi nến đóng. `pivot_bi_pha.chi_so_biet < chi_so_xay_ra` luôn đúng."""
    cap: str
    loai: str
    chieu: str
    ngay_xay_ra: str
    chi_so_xay_ra: int
    ngay_biet: str
    chi_so_biet: int
    pivot_bi_pha: Pivot
    gia_dong: float
    khoa_bien: str | None
    khong_giao_dich: bool


@dataclass(frozen=True)
class _CapSK:
    huong: str = _CHUA_CO_HUONG
    chua_pha: tuple = ()      # các Pivot hiệu lực ĐÃ BIẾT mà CHƯA bị phá (cờ `da_pha` = vắng mặt ở đây)


@dataclass(frozen=True)
class TrangThaiSuKien:
    san: str
    he_so_gia: float
    caps: tuple


@dataclass(frozen=True)
class ConSong:
    """Một nhịp NGƯỢC chiều thủy triều, từ pivot nội bộ `diem_dau` tới pivot nội bộ đối loại `diem_cuoi`
    (5.8). Vào nhật ký KHI `diem_cuoi` được xác nhận (`ngay_biet = diem_cuoi.ngay_biet`); không sửa lại.
    `du_dieu_kien` theo mặc định 3/8 VÀ 10 phiên; ô khác của lưới: `du_dieu_kien_o`."""
    cap: str
    chieu: str                    # chiều của nhịp ngược: `giam` khi thủy triều `tang`, và ngược lại
    thuy_trieu: str
    diem_dau: Pivot
    diem_cuoi: Pivot
    moc_nhip_chinh: Pivot | None  # đáy (đỉnh) swing liền trước `diem_dau`, đã biết tại `chi_so_biet`
    bien_do: float                # |diem_dau.gia − diem_cuoi.gia|
    bien_do_nhip_chinh: float | None
    ty_le: float | None           # bien_do / bien_do_nhip_chinh
    ty_le_gia: float              # bien_do / diem_dau.gia
    so_phien: int                 # diem_cuoi.chi_so_xay_ra − diem_dau.chi_so_xay_ra
    du_dieu_kien: bool
    ngay_xay_ra: str
    chi_so_xay_ra: int
    ngay_biet: str
    chi_so_biet: int
    thay_the: bool = False        # `diem_cuoi` là dòng `thay_the` của họ fractal


@dataclass(frozen=True)
class TrangThaiDow:
    """Trạng thái Dow tại nến `chi_so_t` (5.8); mỗi thành phần mang `ngay_biet` = ngày của nến ĐẦU TIÊN mà giá
    trị HIỆN TẠI của nó tính ra được (bắt đầu của đoạn không đổi), không phải ngày đọc."""
    chi_so_t: int = -1
    thuy_trieu: str = CHUA_DU
    chi_so_biet_thuy_trieu: int | None = None
    ngay_biet_thuy_trieu: str | None = None
    moc_phu_dinh: Pivot | None = None
    ngay_biet_moc_phu_dinh: str | None = None
    canh_bao_dao_chieu: bool = False
    ngay_biet_canh_bao: str | None = None
    thien_huong_swing: str = _CHUA_CO_HUONG
    thien_huong_noi_bo: str = _CHUA_CO_HUONG
    su_kien_cuoi_swing: SuKienPha | None = None
    su_kien_cuoi_noi_bo: SuKienPha | None = None
    dinh_swing_cuoi: Pivot | None = None
    day_swing_cuoi: Pivot | None = None
    con_song_cuoi: ConSong | None = None


@dataclass(frozen=True)
class ChuKy4:
    giai_doan: str
    nguon: str
    ly_do: str
    ghi_chu: tuple
    mau_thuan: bool = False
    thuy_trieu: str = CHUA_DU
    ngay_biet_thuy_trieu: str | None = None


# ── sự kiện phá mốc theo cấp ──────────────────────────────────────────────────────────────
def khoi_tao_su_kien(tt: TrangThai) -> TrangThaiSuKien:
    return TrangThaiSuKien(san=tt.san, he_so_gia=tt.he_so_gia, caps=(_CapSK(), _CapSK()))


def _vuot_moc(tsk: TrangThaiSuKien, loai: str, dong: float, gia: float) -> bool:
    """Đóng cửa vượt mốc QUÁ nửa bước giá (nghiêm ngặt): đóng bằng mốc hay trong nửa bước là chưa phá."""
    nua = nua_buoc(gia, tsk.he_so_gia, tsk.san)
    if loai == DINH:
        return dong - gia > nua
    return gia - dong > nua


def _buoc_su_kien(tsk: TrangThaiSuKien, ten_cap: str, cap: _CapSK, nen: Nen):
    """Phá mốc tại nến `nen` với các pivot ĐÃ BIẾT trước nến này. Mỗi pivot bị phá tối đa MỘT lần.
    Phá một mốc thì mọi pivot cùng loại mà đóng cửa đã vượt quá nửa bước cũng thành đã phá (hai đỉnh
    gần-bằng-nhau chỉ cho MỘT sự kiện, không cho hai sự kiện ở hai nến liền nhau)."""
    huong, chua_pha, moi = cap.huong, cap.chua_pha, []
    for loai, chieu in ((DINH, TANG), (DAY, GIAM)):
        cung = [p for p in chua_pha if p.loai == loai]
        if not cung or not _vuot_moc(tsk, loai, nen.dong, cung[-1].gia):
            continue
        ten = KHOI_DAU if huong == _CHUA_CO_HUONG else (BOS if chieu == huong else CHOCH)
        moi.append(SuKienPha(cap=ten_cap, loai=ten, chieu=chieu, ngay_xay_ra=nen.ngay,
                             chi_so_xay_ra=nen.chi_so, ngay_biet=nen.ngay, chi_so_biet=nen.chi_so,
                             pivot_bi_pha=cung[-1], gia_dong=nen.dong, khoa_bien=nen.khoa_bien,
                             khong_giao_dich=nen.khong_giao_dich))
        huong = chieu
        chua_pha = tuple(p for p in chua_pha
                         if not (p.loai == loai and _vuot_moc(tsk, loai, nen.dong, p.gia)))
    return _CapSK(huong=huong, chua_pha=chua_pha), moi


def _them_pivot(cap: _CapSK, pivots) -> _CapSK:
    """Ghi các pivot được xác nhận ở nến này vào danh sách chưa phá. Dòng `thay_the` (fractal) gỡ pivot bị thay."""
    chua_pha = cap.chua_pha
    for p in pivots:
        if p.su_kien == THAY_THE:
            chua_pha = tuple(q for q in chua_pha
                             if not (q.loai == p.loai and q.chi_so_xay_ra == p.thay_the_chi_so))
        chua_pha = chua_pha + (p,)
    return _CapSK(huong=cap.huong, chua_pha=chua_pha)


def cap_nhat_su_kien(tsk: TrangThaiSuKien, nen: Nen, pivots_moi) -> tuple[TrangThaiSuKien, list[SuKienPha]]:
    """Một nến + các dòng pivot MỚI của chính nến ấy vào; trạng thái mới và sự kiện mới ra. THỨ TỰ là
    luật (5.7 khoản 1): trước hết xét phá mốc với pivot đã biết TRƯỚC nến, sau đó mới ghi pivot xác nhận
    ở chính nến này. Hai cấp độc lập, cấp nội bộ ghi trước."""
    caps, moi = [], []
    for ten, cap in zip(CAPS, tsk.caps):
        cap2, sk = _buoc_su_kien(tsk, ten, cap, nen)
        cap2 = _them_pivot(cap2, [p for p in pivots_moi if p.cap == ten])
        caps.append(cap2)
        moi.extend(sk)
    return replace(tsk, caps=tuple(caps)), moi


def su_kien_tai(su_kien, chi_so_t: int) -> list[SuKienPha]:
    """Các sự kiện ĐÃ BIẾT tại nến `chi_so_t`."""
    return [e for e in su_kien if e.chi_so_biet <= chi_so_t]


# ── trạng thái Dow: thủy triều, mốc phủ định (5.8) ────────────────────────────────────────
def _ap_dong(chuoi: list, p: Pivot) -> list:
    """Áp một dòng nhật ký lên chuỗi pivot HIỆU LỰC của một cấp."""
    if p.su_kien == THAY_THE:
        chuoi = [q for q in chuoi if not (q.loai == p.loai and q.chi_so_xay_ra == p.thay_the_chi_so)]
    return chuoi + [p]


def _thuy_trieu_tu_swing(sw: list):
    """(thủy triều, đỉnh swing cuối, đáy swing cuối). `tang` khi đỉnh cuối là HH VÀ đáy cuối là HL; `giam`
    khi LH VÀ LL; chưa có hai đỉnh + hai đáy thì `chua_du_bang_chung`; còn lại (kể cả `bang`) là `lan`."""
    dinh = next((p for p in reversed(sw) if p.loai == DINH), None)
    day = next((p for p in reversed(sw) if p.loai == DAY), None)
    if dinh is None or day is None or CHUA_CO in (dinh.nhan, day.nhan):
        return CHUA_DU, dinh, day
    if dinh.nhan == HH and day.nhan == HL:
        return TANG, dinh, day
    if dinh.nhan == LH and day.nhan == LL:
        return GIAM, dinh, day
    return LAN, dinh, day


def _ghi_chay(chay: dict, ten: str, gia_tri, chi_so: int, ngay: str) -> None:
    """Chỉ ghi khi giá trị ĐỔI: `chay[ten]` luôn là (giá trị hiện tại, nến bắt đầu đoạn, ngày)."""
    if chay[ten][0] != gia_tri:
        chay[ten] = (gia_tri, chi_so, ngay)


def trang_thai_tu_nhat_ky(nhat_ky, su_kien, con_song, chi_so_t: int) -> TrangThaiDow:
    """Trạng thái Dow tại `chi_so_t`, tính CHỈ từ các dòng có `chi_so_biet <= chi_so_t` (hàm của tiền tố)."""
    pv, ev = {}, {}
    for p in nhat_ky:
        if p.cap == CAP_SWING and p.chi_so_biet <= chi_so_t:
            pv.setdefault(p.chi_so_biet, []).append(p)
    for e in su_kien:
        if e.cap == CAP_SWING and e.chi_so_biet <= chi_so_t:
            ev.setdefault(e.chi_so_biet, []).append(e)
    chay = {"thuy_trieu": (CHUA_DU, None, None), "moc": (None, None, None),
            "canh_bao": (False, None, None)}
    sw, huong_sw, dinh, day = [], _CHUA_CO_HUONG, None, None
    moc = None
    for b in sorted(set(pv) | set(ev)):
        lines_p, lines_e = (pv[b] if b in pv else []), (ev[b] if b in ev else [])
        ngay = (lines_p + lines_e)[0].ngay_biet
        for p in lines_p:
            sw = _ap_dong(sw, p)
        for e in lines_e:
            huong_sw = e.chieu
        thuy_trieu, dinh, day = _thuy_trieu_tu_swing(sw)
        moc = day if thuy_trieu == TANG else (dinh if thuy_trieu == GIAM else None)
        canh_bao = (thuy_trieu, huong_sw) in ((TANG, GIAM), (GIAM, TANG))
        _ghi_chay(chay, "thuy_trieu", thuy_trieu, b, ngay)
        _ghi_chay(chay, "moc", None if moc is None else (moc.loai, moc.chi_so_xay_ra, moc.gia), b, ngay)
        _ghi_chay(chay, "canh_bao", canh_bao, b, ngay)
    sk_da_biet = su_kien_tai(su_kien, chi_so_t)
    cuoi = {c: next((e for e in reversed(sk_da_biet) if e.cap == c), None) for c in CAPS}
    song = [w for w in con_song if w.chi_so_biet <= chi_so_t]
    return TrangThaiDow(
        chi_so_t=chi_so_t, thuy_trieu=chay["thuy_trieu"][0], chi_so_biet_thuy_trieu=chay["thuy_trieu"][1],
        ngay_biet_thuy_trieu=chay["thuy_trieu"][2], moc_phu_dinh=moc,
        ngay_biet_moc_phu_dinh=chay["moc"][2], canh_bao_dao_chieu=chay["canh_bao"][0],
        ngay_biet_canh_bao=chay["canh_bao"][2], thien_huong_swing=huong_sw,
        thien_huong_noi_bo=cuoi[CAP_NOI_BO].chieu if cuoi[CAP_NOI_BO] else _CHUA_CO_HUONG,
        su_kien_cuoi_swing=cuoi[CAP_SWING], su_kien_cuoi_noi_bo=cuoi[CAP_NOI_BO],
        dinh_swing_cuoi=dinh, day_swing_cuoi=day, con_song_cuoi=song[-1] if song else None)


def trang_thai_dow(cs: CauTruc, chi_so_t: int | None = None) -> TrangThaiDow:
    """Trạng thái Dow của `cs` tại nến `chi_so_t` (mặc định nến cuối)."""
    t = cs.so_nen - 1 if chi_so_t is None else chi_so_t
    return trang_thai_tu_nhat_ky(cs.nhat_ky, cs.su_kien, cs.con_song, t)


# ── con sóng (5.8) ────────────────────────────────────────────────────────────────────────
def _dat_dieu_kien(ty_le, ty_le_gia: float, so_phien: int, bien_do: tuple, phien: int, kieu: str) -> bool:
    loai, nguong = bien_do
    if loai == "nhip_chinh":
        du_bien = ty_le is not None and ty_le >= nguong
    elif loai == "phan_tram":
        du_bien = ty_le_gia >= nguong
    else:
        raise ValueError(f"loại biên độ {loai!r} không có (nhip_chinh | phan_tram)")
    du_gian = so_phien >= phien
    if kieu == "va":
        return du_bien and du_gian
    if kieu == "hoac":
        return du_bien or du_gian
    raise ValueError(f"kiểu {kieu!r} không có (va | hoac)")


def du_dieu_kien_o(song: ConSong, bien_do: tuple = BIEN_DO_SONG, phien: int = PHIEN_SONG,
                   kieu: str = KIEU_SONG) -> bool:
    """`song` có đủ điều kiện ở MỘT ô của lưới (mặc định 3/8 nhịp chính VÀ 10 phiên) không."""
    return _dat_dieu_kien(song.ty_le, song.ty_le_gia, song.so_phien, bien_do, phien, kieu)


def con_song_tu_nhat_ky(nhat_ky, bien_do: tuple = BIEN_DO_SONG, phien: int = PHIEN_SONG,
                        kieu: str = KIEU_SONG) -> tuple:
    """Các nhịp ngược đã HOÀN TẤT, phát lại từ nhật ký pivot theo từng nến biết. Thủy triều tại nến `t` đọc từ
    các dòng swing có `chi_so_biet <= t` (kể cả dòng cùng nến). Nhịp ngược đang chạy chưa vào đây."""
    nhom = {}
    for p in nhat_ky:
        nhom.setdefault(p.chi_so_biet, []).append(p)
    sw, nb, kq = [], [], []
    for b in sorted(nhom):
        dong_b = nhom[b]
        for p in dong_b:
            if p.cap == CAP_SWING:
                sw = _ap_dong(sw, p)
        thuy_trieu = _thuy_trieu_tu_swing(sw)[0]
        for p in dong_b:
            if p.cap != CAP_NOI_BO:
                continue
            nb = _ap_dong(nb, p)
            if thuy_trieu not in (TANG, GIAM) or len(nb) < 2 or nb[-2].loai == p.loai:
                continue
            nguoc = (thuy_trieu == TANG and p.loai == DAY) or (thuy_trieu == GIAM and p.loai == DINH)
            if not nguoc:
                continue
            dau = nb[-2]
            loai_goc = DAY if thuy_trieu == TANG else DINH
            goc = next((q for q in reversed(sw)
                        if q.loai == loai_goc and q.chi_so_xay_ra < dau.chi_so_xay_ra), None)
            bd = abs(dau.gia - p.gia)
            chinh = None if goc is None else (dau.gia - goc.gia if thuy_trieu == TANG else goc.gia - dau.gia)
            chinh = chinh if chinh is not None and chinh > 0 else None
            ty_le = None if chinh is None else bd / chinh
            ty_gia = bd / dau.gia if dau.gia > 0 else 0.0
            so_phien = p.chi_so_xay_ra - dau.chi_so_xay_ra
            kq.append(ConSong(
                cap=CAP_NOI_BO, chieu=GIAM if thuy_trieu == TANG else TANG, thuy_trieu=thuy_trieu,
                diem_dau=dau, diem_cuoi=p, moc_nhip_chinh=goc, bien_do=bd, bien_do_nhip_chinh=chinh,
                ty_le=ty_le, ty_le_gia=ty_gia, so_phien=so_phien,
                du_dieu_kien=_dat_dieu_kien(ty_le, ty_gia, so_phien, bien_do, phien, kieu),
                ngay_xay_ra=p.ngay_xay_ra, chi_so_xay_ra=p.chi_so_xay_ra, ngay_biet=p.ngay_biet,
                chi_so_biet=p.chi_so_biet, thay_the=p.su_kien == THAY_THE))
    return tuple(kq)


# ── chu kỳ 4 giai đoạn (6) ────────────────────────────────────────────────────────────────
GHI_CHU_KHONG_CO_VUNG = ("không có vùng đi ngang nào được nhận ra; đây là xu hướng đọc từ cấu trúc, "
                         "không phải pha Wyckoff")


def _ghi_chu_thuy_trieu(trang_thai: TrangThaiDow) -> str:
    ten = TEN_THUY_TRIEU[trang_thai.thuy_trieu]
    if trang_thai.ngay_biet_thuy_trieu:
        return f"thủy triều swing: {ten} (biết từ {trang_thai.ngay_biet_thuy_trieu})"
    return f"thủy triều swing: {ten}"


def _chu_ky(trang_thai: TrangThaiDow, giai_doan: str, nguon: str, ly_do: str, ghi_chu,
            mau_thuan: bool = False) -> ChuKy4:
    return ChuKy4(giai_doan=giai_doan, nguon=nguon, ly_do=ly_do, ghi_chu=tuple(ghi_chu),
                  mau_thuan=mau_thuan, thuy_trieu=trang_thai.thuy_trieu,
                  ngay_biet_thuy_trieu=trang_thai.ngay_biet_thuy_trieu)


def ghep_chu_ky(trang_thai: TrangThaiDow, pha) -> ChuKy4:
    """Ghép thủy triều (`trang_thai`) với một `pha_wyckoff.PhaWyckoff` (chỉ ĐỌC) thành chu kỳ 4 giai đoạn.

    Trong vùng đi ngang: Wyckoff quyết (Tích luỹ / Phân phối; pha B là "chưa đủ bằng chứng"). Rời vùng
    (pha E): Markup / Markdown theo `pha.su_kien`. Ngoài vùng, Wyckoff không kết luận: thủy triều cho
    Markup / Markdown, và TỪ THỦY TRIỀU KHÔNG BAO GIỜ SUY RA Tích luỹ hay Phân phối (cần một vùng đi ngang
    do `pha_wyckoff` nhận ra). Mâu thuẫn Wyckoff ↔ thủy triều được HIỂN THỊ, không bao giờ ghi đè nhãn."""
    tt = trang_thai.thuy_trieu
    ten_tt = TEN_THUY_TRIEU[tt]
    dong_tt = _ghi_chu_thuy_trieu(trang_thai)
    if pha.ket_luan_duoc:
        if pha.pha == _WY_PHA_RA_VUNG:
            if pha.su_kien == _WY_MARKUP:
                gd, nguoc = MARKUP, GIAM
            elif pha.su_kien == _WY_MARKDOWN:
                gd, nguoc = MARKDOWN, TANG
            else:
                raise ValueError(f"pha E có sự kiện lạ {pha.su_kien!r}")
            if tt == nguoc:
                ghi = (f"thủy triều swing chưa xác nhận: đang {ten_tt} trong khi pha_wyckoff đọc {gd}; "
                       f"hai phép đọc được hiển thị cạnh nhau, không phép nào bị ghi đè", dong_tt)
                return _chu_ky(trang_thai, gd, NGUON_WYCKOFF, f"giá đã rời vùng đi ngang ({pha.nhan_ngan})",
                               ghi, mau_thuan=True)
            return _chu_ky(trang_thai, gd, NGUON_WYCKOFF, f"giá đã rời vùng đi ngang ({pha.nhan_ngan})",
                           (dong_tt,))
        if pha.cau_truc == _WY_TICH_LUY:
            gd, nguoc = TICH_LUY, GIAM
        elif pha.cau_truc == _WY_PHAN_PHOI:
            gd, nguoc = PHAN_PHOI, TANG
        elif pha.cau_truc == _WY_CHUA_PHAN_DINH:
            return _chu_ky(trang_thai, CHUA_DU_BC, NGUON_WYCKOFF,
                           "trong vùng đi ngang, chưa phân định tích luỹ hay phân phối", (dong_tt,))
        else:
            raise ValueError(f"cấu trúc Wyckoff lạ {pha.cau_truc!r}")
        ghi = [dong_tt]
        if tt == nguoc:
            ghi.append("ở pha A–D, thủy triều ngược hướng với vùng đi ngang là hình dạng thường gặp "
                       "(vùng nằm sau xu hướng ngược chiều)")
        return _chu_ky(trang_thai, gd, NGUON_WYCKOFF, f"trong vùng đi ngang ({pha.nhan_ngan})", ghi)
    # Wyckoff không kết luận: chỉ thủy triều, và chỉ cho Markup / Markdown.
    if tt == TANG:
        return _chu_ky(trang_thai, MARKUP, NGUON_THUY_TRIEU, "thủy triều swing tăng, không có vùng đi ngang",
                       (GHI_CHU_KHONG_CO_VUNG, dong_tt, pha.nhan_day))
    if tt == GIAM:
        return _chu_ky(trang_thai, MARKDOWN, NGUON_THUY_TRIEU, "thủy triều swing giảm, không có vùng đi ngang",
                       (GHI_CHU_KHONG_CO_VUNG, dong_tt, pha.nhan_day))
    return _chu_ky(trang_thai, CHUA_DU_BC, NGUON_THUY_TRIEU,
                   f"Wyckoff không kết luận và thủy triều swing {ten_tt}", (dong_tt, pha.nhan_day))
