"""Sổ bài học — nhãn NGUYÊN NHÂN cho mỗi lệnh ảo đã đóng (BƯỚC 167, mốc B3 phần 1).

Nhật ký "vì sao" (`nhat_ky_vi_sao`) đã cho biết MỖI LỆNH lãi lỗ bao nhiêu và
hơn thua rổ bao nhiêu. Sổ này hỏi tiếp: lãi/lỗ ấy ĐẾN TỪ ĐÂU — thị trường
chung, ngành, riêng mã/tín hiệu, hay phí? Cộng hai cờ trên cùng lệnh: GAP và
CẮT LỖ SÁT.

File này là phần THUẦN: nhận dòng nhật ký (dict theo `COT_NHAT_KY`) và chuỗi
giá do người gọi đưa vào; không đọc sổ, không ghi đĩa, không gọi mạng. Nó
CHỈ HIỆN: không đổi `COT_NHAT_KY`, không thêm cột vào tab Sheets, không đổi
điểm, ngưỡng hay luật giao dịch. Cùng đầu vào, cùng kết quả.

══ ĐỀ XUẤT ĐỊNH NGHĨA — CHƯA ĐO ══════════════════════════════════════════
Mọi định nghĩa dưới đây là ĐỀ XUẤT của leader (B3, lộ trình 08/10/2026) cộng
một sửa đổi có lý do; chưa chạy trên sổ thật nên chưa biết nhãn nào hay xảy
ra, và chưa ai kiểm nhãn nào "hữu ích".

1. PHÂN RÃ không ngưỡng, bốn phần cộng đúng bằng lãi ròng của lệnh:

       lãi ròng = thị trường + ngành + riêng mã + chi phí

       thị trường = rổ chuẩn (% đổi VN-INDEX, cùng cặp ngày — số nhật ký ĐÃ GHI)
       ngành      = lợi nhuận TB các mã cùng ngành − thị trường
       riêng mã   = lãi ròng + chi phí − lợi nhuận TB ngành
       chi phí    = −`paper_metrics.ROUND_TRIP_COST_PCT`

   Thiếu số liệu ngành thì `ngành` = None và `riêng mã` = lãi ròng + chi phí
   − thị trường (ngành NẰM TRONG riêng mã, bản ghi nói rõ). Thiếu rổ chuẩn
   thì KHÔNG phân rã (không đoán).

   SỬA ĐỔI SO VỚI ĐỀ XUẤT BA PHẦN: tách `chi phí` ra khỏi `riêng mã`. Lãi
   ròng đã trừ phí (`Trade.net_return_pct`), rổ chuẩn thì không; để phí nằm
   trong `riêng mã` thì một lệnh hoà vốn giá mà mất đúng phí bị gọi là
   "tín hiệu sai" — một nhãn sai ngay ở lệnh đầu tiên. `chi phí` là cận DƯỚI
   (mô hình trượt giá nằm trong giá vào/ra, tức vẫn ở `riêng mã`). Hằng đẳng
   thức vẫn đúng theo cấu trúc: phần cuối là phần dư.

2. NGUYÊN NHÂN CHÍNH: lệnh THUA → phần ÂM nhất; lệnh THẮNG → phần DƯƠNG nhất;
   hoà → không có. Hoà giữa hai phần thì lấy phần đứng trước trong `PHAN`
   (tất định).

3. `tín hiệu sai` KHÔNG phải nhãn đo được từ một lệnh (bất biến 5). Nó chỉ là
   cách GỌI phần `riêng mã` khi phần ấy là nguyên nhân chính của một lệnh
   THUA. Bản ghi mang `cach_goi`, không mang nhãn riêng.

4. GAP: `nhat_ky_vi_sao.thoat_duoi_cat_lo` — đúng hàm mà `hau_kiem_may` gọi,
   không có công thức thứ hai.

5. CẮT LỖ SÁT: lệnh thoát bằng cắt lỗ VÀ trong `N_PHIEN_SAU_THOAT` phiên sau
   ngày ra, giá đóng cửa cao nhất ≥ giá vào. Không có chuỗi giá sau thoát →
   "chưa đủ dữ liệu", không đoán. Chuỗi ngắn hơn cửa sổ mà chưa chạm giá
   vào → cũng "chưa đủ dữ liệu" (cửa sổ chưa khép), không phải "không".

6. NGÀNH: `vn100_symbols.SECTOR_WATCHLIST`, không bảng thứ hai. Mã thuộc 0
   hoặc ≥ 2 ngành (PLX có ở "Dầu khí" và "Điện, Nước & Khí đốt") KHÔNG gán
   ngành; bản ghi nói lý do. Lợi nhuận ngành = TB các mã CÙNG ngành (không
   gồm chính mã) từ đóng cửa ngày vào tới đóng cửa ngày ra — đúng cặp ngày và
   đúng loại giá mà rổ chuẩn của nhật ký dùng, để `ngành` là hiệu hai thứ
   cùng loại.

══ ĐIỀU SỔ NÀY KHÔNG NÓI ═════════════════════════════════════════════════
Không xếp hạng agent, không suy ra "agent X sai" từ một lệnh. Dưới
`N_TOI_THIEU_TONG_HOP` lệnh, bảng tổng hợp kèm câu "chưa đủ lệnh để kết luận".
`N_PHIEN_SAU_THOAT` cũng là ĐỀ XUẤT CHƯA ĐO.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Sequence

import paper_metrics
from nhat_ky_vi_sao import thoat_duoi_cat_lo
from paper_trading import ExitReason, Status
from vn100_symbols import SECTOR_WATCHLIST

#: ĐỀ XUẤT, CHƯA ĐO: số phiên sau ngày ra mà ta nhìn xem giá có quay lại
#: giá vào không. Một hằng số, một chỗ.
N_PHIEN_SAU_THOAT = 5

#: Dưới ngần này lệnh có bài học thì bảng tổng hợp chưa nói được gì. SUY RA từ
#: ngưỡng của điều kiện dừng, không gõ số.
N_TOI_THIEU_TONG_HOP = paper_metrics.N_TOI_THIEU

#: Thứ tự CỐ ĐỊNH của bốn phần — cũng là thứ tự phá hoà.
PHAN: tuple[str, ...] = ("thi_truong", "nganh", "rieng_ma", "chi_phi")

#: Nhãn hiện của từng phần. Viết thành CẶP rồi dựng dict (cùng lý do
#: `nhat_ky_vi_sao.NHAN_BOI_CANH`: gác toàn repo đọc hình dạng dict literal).
NHAN_PHAN: dict[str, str] = dict((
    ("thi_truong", "Thị trường chung"), ("nganh", "Ngành"),
    ("rieng_ma", "Riêng mã/tín hiệu"), ("chi_phi", "Chi phí"),
))

# Trạng thái của cờ CẮT LỖ SÁT.
CLS_CO = "co"
CLS_KHONG = "khong"
CLS_KHONG_AP_DUNG = "khong_ap_dung"
CLS_CHUA_DU = "chua_du_du_lieu"

KET_QUA_THANG = "THẮNG"
KET_QUA_THUA = "THUA"
KET_QUA_HOA = "HOÀ"


def _ngay(gia_tri: Any) -> str:
    return str(gia_tri or "")[:10]


def _la_so(x: Any) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and not math.isnan(x))


# ── Ngành ────────────────────────────────────────────────────────────────

def nganh_cua(ma: str) -> tuple[Optional[str], Optional[str]]:
    """(tên ngành, None) hoặc (None, lý do không gán được). Từ `SECTOR_WATCHLIST`."""
    cac = [ten for ten, ds in SECTOR_WATCHLIST.items() if ma in ds]
    if len(cac) == 1:
        return cac[0], None
    if not cac:
        return None, f"{ma} không thuộc ngành nào trong SECTOR_WATCHLIST"
    return None, (f"{ma} nằm trong {len(cac)} ngành ({', '.join(cac)}) — "
                  "không gán một ngành")


def ma_cung_nganh(ma: str) -> list[str]:
    """Các mã CÙNG ngành với `ma`, không gồm chính nó; rỗng nếu không gán được ngành."""
    ten, _ = nganh_cua(ma)
    if ten is None:
        return []
    return [m for m in dict.fromkeys(SECTOR_WATCHLIST[ten]) if m != ma]


def chuoi_dong_cua(df: Any, he_so: float) -> dict[str, float]:
    """Bảng OHLCV -> {ngày[:10]: đóng cửa × hệ số}. Bỏ phiên không có giá.

    `he_so` là `data_quality.price_multiplier(df)` của chính bảng này: sổ lệnh
    ghi VNĐ, vnstock trả nghìn đồng — quên nhân thì cờ cắt lỗ sát so hai đơn
    vị khác nhau.
    """
    if df is None or len(df) == 0:
        return {}
    ra: dict[str, float] = {}
    for t, c in zip(df["time"], df["close"]):
        if _la_so(c) and c > 0:
            ra[_ngay(t)] = float(c) * he_so
    return ra


def loi_nhuan_nganh(ma: str, ngay_vao: Any, ngay_ra: Any,
                    gia_theo_ma: Optional[Mapping[str, Mapping[str, float]]]) -> dict:
    """Lợi nhuận TB (%) các mã cùng ngành, đóng cửa ngày vào -> đóng cửa ngày ra.

    Mã thiếu giá ở MỘT trong hai đầu thì loại khỏi trung bình (không đoán bằng
    ngày gần nhất). Trả `{"gia_tri", "n_ma", "nganh", "ly_do"}`; `gia_tri` None
    kèm `ly_do` khi không tính được.
    """
    ten, ly_do_nganh = nganh_cua(ma)
    ra = {"gia_tri": None, "n_ma": 0, "nganh": ten, "ly_do": None}
    if ten is None:
        ra["ly_do"] = ly_do_nganh
        return ra
    vao, thoat = _ngay(ngay_vao), _ngay(ngay_ra)
    if not vao or not thoat:
        ra["ly_do"] = "thiếu ngày vào hoặc ngày ra"
        return ra
    if not gia_theo_ma:
        ra["ly_do"] = "chưa có giá các mã cùng ngành"
        return ra
    loi = []
    for m in ma_cung_nganh(ma):
        chuoi = gia_theo_ma.get(m)
        if not chuoi:
            continue
        p_vao, p_ra = chuoi.get(vao), chuoi.get(thoat)
        if _la_so(p_vao) and _la_so(p_ra) and p_vao > 0:
            loi.append((p_ra - p_vao) / p_vao * 100.0)
    if not loi:
        ra["ly_do"] = (f"không mã cùng ngành ({ten}) nào có giá cả ngày vào "
                       "lẫn ngày ra")
        return ra
    ra["gia_tri"] = sum(loi) / len(loi)
    ra["n_ma"] = len(loi)
    return ra


def gia_sau_thoat(chuoi: Optional[Mapping[str, float]], ngay_ra: Any
                  ) -> Optional[list[float]]:
    """`N_PHIEN_SAU_THOAT` giá đóng cửa đầu tiên SAU (nghiêm ngặt) ngày ra.

    None nếu không có chuỗi hoặc ngày ra. Ngày ra không tính: giá thoát đã nằm
    trong lệnh, ta hỏi giá có QUAY LẠI sau đó không.
    """
    if not chuoi:
        return None
    ra = _ngay(ngay_ra)
    if not ra:
        return None
    sau = sorted(k for k in chuoi if k > ra)
    return [chuoi[k] for k in sau[:N_PHIEN_SAU_THOAT]]


# ── Ba thứ đo trên MỘT lệnh ──────────────────────────────────────────────

def phan_ra(loi_nhuan_rong_pct: Optional[float], ro_chuan_pct: Optional[float],
            loi_nhuan_nganh_pct: Optional[float] = None) -> Optional[dict]:
    """Bốn phần cộng đúng bằng lãi ròng; None nếu thiếu lãi ròng hoặc rổ chuẩn."""
    if not _la_so(loi_nhuan_rong_pct) or not _la_so(ro_chuan_pct):
        return None
    phi = paper_metrics.ROUND_TRIP_COST_PCT
    if _la_so(loi_nhuan_nganh_pct):
        nganh = loi_nhuan_nganh_pct - ro_chuan_pct
        rieng = loi_nhuan_rong_pct + phi - loi_nhuan_nganh_pct
    else:
        nganh = None
        rieng = loi_nhuan_rong_pct + phi - ro_chuan_pct
    return {"thi_truong": ro_chuan_pct, "nganh": nganh,
            "rieng_ma": rieng, "chi_phi": -phi}


def ket_qua_lenh(loi_nhuan_rong_pct: float) -> str:
    return (KET_QUA_THANG if loi_nhuan_rong_pct > 0
            else KET_QUA_THUA if loi_nhuan_rong_pct < 0 else KET_QUA_HOA)


def nguyen_nhan_chinh(ket_qua: str, phan: Optional[Mapping[str, Optional[float]]]
                      ) -> Optional[str]:
    """THUA → phần ÂM nhất; THẮNG → phần DƯƠNG nhất; HOÀ hoặc không phân rã → None."""
    if not phan or ket_qua == KET_QUA_HOA:
        return None
    co = {k: v for k, v in phan.items() if v is not None}
    if not co:
        return None
    if ket_qua == KET_QUA_THUA:
        return min(co, key=lambda k: (co[k], PHAN.index(k)))
    return max(co, key=lambda k: (co[k], -PHAN.index(k)))


def cat_lo_sat(exit_reason: Optional[str], entry_price: Optional[float],
               gia_dong_sau_thoat: Optional[Sequence[float]]) -> dict:
    """Cờ CẮT LỖ SÁT: thoát bằng cắt lỗ rồi giá quay lại ≥ giá vào trong cửa sổ.

    Trả `{"trang_thai", "gia_cao_nhat"}`; trạng thái là một trong `CLS_*`.
    """
    if exit_reason != ExitReason.STOP_LOSS:
        return {"trang_thai": CLS_KHONG_AP_DUNG, "gia_cao_nhat": None}
    gia = [g for g in (gia_dong_sau_thoat or []) if _la_so(g)][:N_PHIEN_SAU_THOAT]
    if not _la_so(entry_price) or not gia:
        return {"trang_thai": CLS_CHUA_DU, "gia_cao_nhat": None}
    cao = max(gia)
    if cao >= entry_price:
        return {"trang_thai": CLS_CO, "gia_cao_nhat": cao}
    if len(gia) < N_PHIEN_SAU_THOAT:
        return {"trang_thai": CLS_CHUA_DU, "gia_cao_nhat": cao}
    return {"trang_thai": CLS_KHONG, "gia_cao_nhat": cao}


# ── Một lệnh -> một bài học ──────────────────────────────────────────────

def lenh_da_dong(dong: Mapping[str, Any]) -> bool:
    """Nửa ĐÓNG của dòng nhật ký đã điền (có ngày ra và lãi ròng)."""
    return bool(dong.get("exit_date")) and _la_so(dong.get("loi_nhuan_rong_pct"))


def lap_bai_hoc(dong: Mapping[str, Any], *,
                loi_nhuan_nganh_pct: Optional[float] = None,
                ly_do_thieu_nganh: Optional[str] = None,
                ten_nganh: Optional[str] = None,
                n_ma_nganh: Optional[int] = None,
                gia_dong_sau_thoat: Optional[Sequence[float]] = None) -> dict:
    """Một dòng nhật ký ĐÃ ĐÓNG -> bản ghi bài học. TẤT ĐỊNH.

    Chỉ ĐỌC dòng nhật ký (lãi ròng, rổ chuẩn, giá, lý do thoát đều là số nhật
    ký đã ghi). `loi_nhuan_nganh_pct` và `gia_dong_sau_thoat` là thứ nhật ký
    KHÔNG có nên người gọi đưa vào; thiếu thì phần tương ứng nói "chưa đủ dữ
    liệu" chứ không đoán.
    """
    if not lenh_da_dong(dong):
        raise ValueError(f"lệnh {dong.get('trade_id')} chưa có nửa ĐÓNG — chưa có bài học")
    lnr = float(dong["loi_nhuan_rong_pct"])
    ket_qua = ket_qua_lenh(lnr)
    thieu: list[str] = []

    phan = phan_ra(lnr, dong.get("ro_chuan_pct"), loi_nhuan_nganh_pct)
    if phan is None:
        thieu.append("chưa có rổ chuẩn cho cặp ngày này — không phân rã được")
    elif phan["nganh"] is None:
        thieu.append(ly_do_thieu_nganh or "chưa có số liệu ngành — ngành nằm trong "
                     "phần riêng mã/tín hiệu")

    nguyen_nhan = nguyen_nhan_chinh(ket_qua, phan)
    cach_goi = None
    if nguyen_nhan == "rieng_ma" and ket_qua == KET_QUA_THUA:
        cach_goi = ("tín hiệu sai — chỉ là cách GỌI phần riêng mã/tín hiệu khi nó "
                    "là nguyên nhân chính của lệnh thua; một lệnh không chứng "
                    "minh được tín hiệu sai (bất biến 5)")

    gap = None
    sl, gia_ra = dong.get("stop_loss_ban_dau"), dong.get("exit_price")
    if _la_so(sl) and _la_so(gia_ra):
        gap = thoat_duoi_cat_lo(sl, gia_ra)
    else:
        thieu.append("thiếu cắt lỗ ban đầu hoặc giá thoát — không xét được gap")

    cls = cat_lo_sat(dong.get("exit_reason"), dong.get("entry_price"), gia_dong_sau_thoat)
    if cls["trang_thai"] == CLS_CHUA_DU:
        thieu.append(f"chưa đủ giá {N_PHIEN_SAU_THOAT} phiên sau ngày ra — "
                     "chưa xét được cắt lỗ sát")

    return {
        "trade_id": dong.get("trade_id"), "symbol": dong.get("symbol"),
        "exit_date": _ngay(dong.get("exit_date")),
        "exit_reason": dong.get("exit_reason"),
        "ket_qua": ket_qua, "loi_nhuan_rong_pct": lnr,
        "phan": phan, "co_nganh": bool(phan and phan["nganh"] is not None),
        "nganh": ten_nganh, "n_ma_nganh": n_ma_nganh,
        "nguyen_nhan": nguyen_nhan, "cach_goi": cach_goi,
        "gap": gap, "cat_lo_sat": cls, "thieu": thieu,
    }


# ── Nhiều lệnh ───────────────────────────────────────────────────────────

def _ktc_trung_binh(xs: Sequence[float]) -> dict:
    n = len(xs)
    tb = sum(xs) / n
    if n < 2:
        return {"tb": tb, "n": n, "ktc": None}
    sd = math.sqrt(sum((x - tb) ** 2 for x in xs) / (n - 1))
    nua = paper_metrics.Z_LOI_THE * sd / math.sqrt(n)
    return {"tb": tb, "n": n, "ktc": (tb - nua, tb + nua)}


def _nganh_va_rieng_ma(p: Mapping[str, Optional[float]]) -> float:
    """Ngành + riêng mã: phần KHÔNG phụ thuộc có tách được ngành hay không."""
    return p["rieng_ma"] + (p["nganh"] if p["nganh"] is not None else 0.0)


def _trung_binh_phan(cac: Sequence[dict]) -> dict:
    """TB mỗi phần trên các lệnh phân rã được. Cùng loại với nhau:
    `riêng mã` chỉ lấy lệnh CÓ ngành (ở lệnh không có ngành, ngành nằm trong
    nó); `ngành + riêng mã` thì lấy mọi lệnh phân rã được."""
    pr = [b["phan"] for b in cac if b["phan"]]
    co_nganh = [p for p in pr if p["nganh"] is not None]
    ra: dict[str, Optional[dict]] = {}
    for k in ("thi_truong", "chi_phi"):
        ra[k] = _ktc_trung_binh([p[k] for p in pr]) if pr else None
    for k in ("nganh", "rieng_ma"):
        ra[k] = _ktc_trung_binh([p[k] for p in co_nganh]) if co_nganh else None
    ra["nganh_va_rieng_ma"] = (
        _ktc_trung_binh([_nganh_va_rieng_ma(p) for p in pr]) if pr else None)
    return ra


def tong_hop(cac_bai_hoc: Sequence[dict]) -> dict:
    """Gộp nhiều bài học: đếm nguyên nhân chính (tách THẮNG/THUA) và TB đóng góp.

    Không xếp hạng agent. Dưới `N_TOI_THIEU_TONG_HOP` lệnh thì `cau_luu_y` nói
    thẳng là chưa đủ lệnh để kết luận.
    """
    n = len(cac_bai_hoc)
    dem = {KET_QUA_THANG: {k: 0 for k in PHAN}, KET_QUA_THUA: {k: 0 for k in PHAN}}
    khong_phan_ra = 0
    for b in cac_bai_hoc:
        if b["nguyen_nhan"] in PHAN:
            dem[b["ket_qua"]][b["nguyen_nhan"]] += 1
        elif b["ket_qua"] != KET_QUA_HOA:
            khong_phan_ra += 1
    gap_xet = [b for b in cac_bai_hoc if b["gap"] is not None]
    cls_xet = [b for b in cac_bai_hoc
               if b["cat_lo_sat"]["trang_thai"] in (CLS_CO, CLS_KHONG)]
    cau = None
    if n < N_TOI_THIEU_TONG_HOP:
        cau = (f"Mới {n} lệnh có bài học, dưới {N_TOI_THIEU_TONG_HOP} — chưa đủ lệnh "
               "để kết luận: một vài lệnh không phải bằng chứng (bất biến 5). "
               "Bảng này kể NGUYÊN NHÂN từng lệnh, không xếp hạng agent.")
    return {
        "n": n,
        "n_thang": sum(b["ket_qua"] == KET_QUA_THANG for b in cac_bai_hoc),
        "n_thua": sum(b["ket_qua"] == KET_QUA_THUA for b in cac_bai_hoc),
        "n_hoa": sum(b["ket_qua"] == KET_QUA_HOA for b in cac_bai_hoc),
        "nguyen_nhan": dem, "n_khong_phan_ra": khong_phan_ra,
        "n_co_nganh": sum(b["co_nganh"] for b in cac_bai_hoc),
        "tb_phan": _trung_binh_phan(cac_bai_hoc),
        "tb_phan_thua": _trung_binh_phan(
            [b for b in cac_bai_hoc if b["ket_qua"] == KET_QUA_THUA]),
        "n_gap": sum(b["gap"] is True for b in gap_xet), "n_gap_xet": len(gap_xet),
        "n_cat_lo_sat": sum(b["cat_lo_sat"]["trang_thai"] == CLS_CO for b in cls_xet),
        "n_cat_lo_sat_xet": len(cls_xet),
        "du_lenh": n >= N_TOI_THIEU_TONG_HOP, "cau_luu_y": cau,
    }


def ma_can_gia(dong_nk: Sequence[Mapping[str, Any]]) -> list[str]:
    """Các mã cần giá để xét ngành và cắt lỗ sát: mỗi mã của lệnh đã đóng + mã cùng ngành."""
    can: dict[str, None] = {}
    for d in dong_nk:
        if not lenh_da_dong(d) or not d.get("symbol"):
            continue
        can[d["symbol"]] = None
        for m in ma_cung_nganh(d["symbol"]):
            can[m] = None
    return sorted(can)


def tu_ngay_can_gia(dong_nk: Sequence[Mapping[str, Any]]) -> Optional[str]:
    """Ngày vào sớm nhất của các lệnh đã đóng — mốc đầu khi tải giá; None nếu không có."""
    ngay = [_ngay(d.get("entry_date")) for d in dong_nk
            if lenh_da_dong(d) and d.get("entry_date")]
    return min(ngay) if ngay else None


def bai_hoc_cho_so(dong_nk: Sequence[Mapping[str, Any]],
                   gia_theo_ma: Optional[Mapping[str, Mapping[str, float]]] = None) -> dict:
    """Mọi dòng nhật ký -> bài học cho lệnh đã đóng + bảng tổng hợp.

    `gia_theo_ma` {mã: {ngày: đóng cửa VNĐ}} có hoặc không; không có thì ngành
    và cắt lỗ sát nói "chưa đủ dữ liệu" còn phần còn lại vẫn chạy.
    `n_dong_cho_nua_dong` đếm lệnh sổ đã đóng mà nhật ký chưa điền nửa ĐÓNG
    (điền ở lượt `hoan_tat_nhat_ky` kế tiếp) — tiêu chí ra khỏi giai đoạn B
    là 0 ở đây trong vòng một phiên.
    """
    cac: list[dict] = []
    cho = 0
    for d in dong_nk:
        if not lenh_da_dong(d):
            if d.get("trang_thai_lenh") == Status.CLOSED:
                cho += 1
            continue
        sym = d.get("symbol")
        ng = loi_nhuan_nganh(sym, d.get("entry_date"), d.get("exit_date"), gia_theo_ma)
        sau = gia_sau_thoat((gia_theo_ma or {}).get(sym), d.get("exit_date"))
        cac.append(lap_bai_hoc(
            d, loi_nhuan_nganh_pct=ng["gia_tri"], ly_do_thieu_nganh=ng["ly_do"],
            ten_nganh=ng["nganh"], n_ma_nganh=ng["n_ma"], gia_dong_sau_thoat=sau))
    return {"bai_hoc": cac, "n_dong_cho_nua_dong": cho, "tong_hop": tong_hop(cac)}


# ── Dựng hàng để HIỆN (app chỉ định dạng, không tính) ────────────────────

#: Nhãn hiện của cờ cắt lỗ sát. Viết thành CẶP rồi dựng dict, như `NHAN_PHAN`.
NHAN_CAT_LO_SAT: dict[str, str] = dict((
    (CLS_CO, "có"), (CLS_KHONG, "không"),
    (CLS_KHONG_AP_DUNG, "— (không thoát bằng cắt lỗ)"),
    (CLS_CHUA_DU, "chưa đủ dữ liệu"),
))


def nhan_nguyen_nhan(b: Mapping[str, Any]) -> str:
    """Nguyên nhân chính của một bài học, để hiện. Lệnh hoà hoặc chưa phân rã được: gạch."""
    if b["nguyen_nhan"] is None:
        return "— (hoà)" if b["ket_qua"] == KET_QUA_HOA else "— (chưa phân rã được)"
    nhan = NHAN_PHAN[b["nguyen_nhan"]]
    return f"{nhan} (gọi: tín hiệu sai?)" if b["cach_goi"] else nhan


def dong_bang(b: Mapping[str, Any]) -> dict:
    """Một bài học -> một hàng bảng, số THÔ (None = thiếu). Không tính lại số nào."""
    p = b["phan"] or {}
    return {
        "Mã": b["symbol"], "Ra": b["exit_date"], "Kết quả": b["ket_qua"],
        "Lãi ròng %": b["loi_nhuan_rong_pct"],
        "Nguyên nhân chính": nhan_nguyen_nhan(b),
        "Thị trường %": p.get("thi_truong"), "Ngành %": p.get("nganh"),
        "Riêng mã/tín hiệu %": p.get("rieng_ma"), "Chi phí %": p.get("chi_phi"),
        "Gap": None if b["gap"] is None else ("có" if b["gap"] else "không"),
        "Cắt lỗ sát": NHAN_CAT_LO_SAT[b["cat_lo_sat"]["trang_thai"]],
        "Còn thiếu": " | ".join(b["thieu"]) or None,
    }


def bang_nguyen_nhan(th: Mapping[str, Any]) -> list[dict]:
    """Đếm nguyên nhân chính, tách THẮNG/THUA — mỗi phần một hàng."""
    dem = th["nguyen_nhan"]
    return [{"Nguyên nhân chính": NHAN_PHAN[k],
             "Lệnh THẮNG": dem[KET_QUA_THANG][k], "Lệnh THUA": dem[KET_QUA_THUA][k]}
            for k in PHAN]


def bang_dong_gop(th: Mapping[str, Any]) -> list[dict]:
    """Đóng góp trung bình mỗi phần (điểm %/lệnh), kèm KTC 95% và số lệnh."""
    nhan = [("thi_truong", NHAN_PHAN["thi_truong"]), ("nganh", NHAN_PHAN["nganh"]),
            ("rieng_ma", NHAN_PHAN["rieng_ma"]), ("chi_phi", NHAN_PHAN["chi_phi"]),
            ("nganh_va_rieng_ma", "Ngành + riêng mã (không phụ thuộc tách được ngành)")]
    hang = []
    for k, ten in nhan:
        tat_ca, thua = th["tb_phan"][k], th["tb_phan_thua"][k]
        hang.append({
            "Phần": ten,
            "TB mọi lệnh": None if tat_ca is None else tat_ca["tb"],
            "KTC 95%": None if tat_ca is None else tat_ca["ktc"],
            "Số lệnh": None if tat_ca is None else tat_ca["n"],
            "TB lệnh THUA": None if thua is None else thua["tb"],
            "Số lệnh THUA": None if thua is None else thua["n"],
        })
    return hang
