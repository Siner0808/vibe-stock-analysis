"""Đọc cấu trúc giá — đỉnh/đáy xoay chiều theo hai cấp (BƯỚC 247, Dow Lát 1, mốc B5 mượn).

CHỈ ĐỂ ĐỌC, KHÔNG CHẤM ĐIỂM. Đặc tả: `docs/thiet-ke-dow-cau-truc.md` mục 5.1–5.6, 5.9.
Lát 1 chỉ có LÕI PIVOT: chưa có BOS/CHoCH, trạng thái Dow, chu kỳ, ô trên app (Lát 2–3).

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
    nhat_ky = []
    for nen in nens:
        tt, moi = cap_nhat(tt, nen)
        nhat_ky.extend(moi)
    return CauTruc(nhat_ky=tuple(nhat_ky), so_nen=len(nens), ho=tt.ho, tham_so=tt.tham_so,
                   san=tt.san, he_so_gia=tt.he_so_gia, trang_thai=tt)


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
