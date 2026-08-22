"""fundamental_agent.py — agent đọc báo cáo tài chính.

VÌ SAO CÓ FILE NÀY
──────────────────
Sơ đồ kiến trúc của dự án vẽ một ô "Fundamental Agent · BCTC Q2" nằm giữa
luồng dữ liệu suốt nhiều tháng. Ngày 21/08/2026 ô đó bị gỡ, vì
`grep -rn "fundamental" master_agent.py analysis_agents.py` trả về rỗng:
không lớp nào tồn tại, không thành phần nào đọc báo cáo tài chính, và
`FinancialDataCollector` tuy có được import vào `app.py` nhưng chưa từng
được gọi. Vẽ một ô vào giữa luồng là khẳng định dữ liệu chảy qua đó.

File này làm phần việc mà cái ô kia đã hứa.

──────────────────────────────────────────────────────────────────────
BỐN CÁI BẪY CỦA DỮ LIỆU CƠ BẢN — CẢ BỐN ĐỀU ĐÃ CẮN Ở DỰ ÁN NÀY
──────────────────────────────────────────────────────────────────────

1. **Ba dòng trong bảng `ratio` là TĂNG TRƯỞNG, không phải mức.**
   `total_assets`, `owners_equity`, `profit_after_tax_...` nghe như số dư
   nhưng nhãn tiếng Việt của chúng là "Tăng trưởng tổng tài sản", "Tăng
   trưởng vốn chủ sở hữu", "Tăng trưởng lợi nhuận sau thuế". Đo trên FPT
   ngày 22/08/2026: `total_assets` = -3,81 cho năm 2022. Tổng tài sản âm
   là bất khả; đó là -3,81%. Đọc nhầm ba dòng này thì mọi chỉ số dẫn xuất
   đều sai mà không có gì kêu — đúng họ với cái bẫy nghìn đồng/VNĐ trong
   `NGUYEN-TAC-DO-LUONG.md`. Nên ở đây chúng mang hậu tố `_tang_pct`.

2. **Ngân hàng có bộ chỉ tiêu KHÁC.** ACB không có `net_margin`,
   `debt_to_equity`, `net_revenue`, `interest_coverage`; đổi lại có
   `net_interest_margin_nim`, `cost_income_ratio_cir`,
   `equity_total_assets`. Chấm ngân hàng bằng thước của doanh nghiệp sản
   xuất sẽ loại sạch nhóm ngân hàng — mà đó là nhóm nặng ký nhất rổ VN30.
   `experiment_fundamentals.py` đã vấp đúng chỗ này khi chọn trường.
   Đòn bẩy của ngân hàng cũng KHÔNG so được với đòn bẩy doanh nghiệp
   thường: vay là nghiệp vụ của họ, không phải dấu hiệu rủi ro.

3. **`roe_trailling` và `roa_trailling` bằng 0 ở mọi mã, mọi năm.** Nguồn
   trả về cột rỗng chứ không trả về thiếu. Dùng nó thì mọi doanh nghiệp
   đều có ROE = 0.

4. **Số liệu cũ trông y hệt số liệu hiện tại.** Bảng năm chốt sau vài
   tháng nên năm liền trước là bình thường; cách hai năm trở lên là nguồn
   đang trả dữ liệu hỏng. Ngưỡng dùng chung với `financial_collector`.

CHỖ CHƯA ĐÚNG MÀ ĐÃ BIẾT: NHÓM NGÀNH CHỈ CÓ HAI
───────────────────────────────────────────────
Module chia "ngân hàng" và "phi ngân hàng". Công ty chứng khoán rơi vào
nhóm sau, nên đòn bẩy từ cho vay ký quỹ bị chấm bằng thước doanh nghiệp
sản xuất: đo SSI ngày 22/08/2026 ra `Nợ vay/Vốn chủ 188%` kèm cảnh báo
"đòn bẩy cao", trong khi với công ty chứng khoán đó là mức bình thường.
Chưa tách nhóm thứ ba vì chưa có cách nhận diện nào đọc từ chính bảng số
liệu — thêm một danh sách mã dán cứng sẽ hỏng lặng lẽ khi rổ đổi. Câu
chữ của tín hiệu có in kèm con số nên người đọc tự trừ hao được.

──────────────────────────────────────────────────────────────────────
ẢNH HƯỞNG LÊN ĐIỂM GIAO DỊCH: BẰNG 0, CÓ CHỦ ĐÍCH
──────────────────────────────────────────────────────────────────────
Agent này chạy đủ, trả số thật, và hiện lên giao diện. Nhưng
`master_agent.TRONG_SO_CO_BAN` mặc định bằng 0, nên nó KHÔNG làm dịch
điểm giao dịch một ly nào.

Không phải vì làm dở, mà vì chưa ai đo được nó có ích không.
`experiment_fundamentals.py` đã tính sẵn lực thống kê: gói cộng đồng
vnstock chỉ trả 8 quý, mà yếu tố giá trị/chất lượng trong tài liệu học
thuật có IC ≈ 0,03–0,05. Ở mức đó, 8 quý phát hiện được tín hiệu với xác
suất ~10%. Ba thiên lệch còn lại (số liệu điều chỉnh hồi tố, thiên lệch
sống sót, cửa sổ nằm trong vùng đã tối ưu) đều đẩy kết quả ĐẸP lên.

Quy tắc số 1 của dự án: nếu một thay đổi làm con số đẹp lên đáng kể, giả
định đầu tiên phải là có lỗi. Bật trọng số lên rồi thấy lãi tăng chính là
kịch bản đó. Bật nó là một quyết định ĐO LƯỜNG, không phải một dòng code
— và dòng code cho quyết định ấy chỉ là một hằng số.
"""
from __future__ import annotations

import datetime as _dt
import time
from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

NGUON = "vnstock · KBS · bảng ratio, period=year"
NAM_TOI_DA_CU = 2          # giữ đồng bộ với financial_collector.NAM_TOI_DA_CU
_TTL_GIAY = 900

NGAN_HANG = "ngân hàng"
PHI_NGAN_HANG = "phi ngân hàng"

# Ngưỡng chấm. Đặt tên hết, và tách riêng hai nhóm ngành, vì cùng một con
# số ROE 17% nói hai chuyện khác nhau ở hai nhóm.
ROE_TOT, ROE_KHA, ROE_YEU = 20.0, 15.0, 10.0
BIEN_LN_TOT, BIEN_LN_YEU = 15.0, 5.0
NO_VAY_CAO, NO_VAY_THAP = 100.0, 50.0        # nợ vay / VCSH, %
TRA_LAI_AN_TOAN, TRA_LAI_NGUY = 5.0, 2.0     # lần
VCSH_TTS_MONG = 8.0                          # vốn chủ / tổng tài sản, % (ngân hàng)
NIM_TOT, NIM_YEU = 3.5, 2.5                  # %
PE_RE, PE_DAT = 10.0, 25.0
PB_RE, PB_DAT = 1.5, 4.0
TANG_TRUONG_TOT, TANG_TRUONG_XAU = 15.0, -15.0

DIEM_NEN = 50.0            # chưa biết gì thì đứng giữa
DIEM_MIN, DIEM_MAX = 0.0, 100.0

_CACHE: dict[str, tuple[float, Any]] = {}


def _cache(khoa: str, lam, ttl: int = _TTL_GIAY):
    """Cache TTL tối giản, không phụ thuộc Streamlit để test được offline."""
    gio = time.time()
    co = _CACHE.get(khoa)
    if co and gio - co[0] < ttl:
        return co[1]
    gia_tri = lam()
    _CACHE[khoa] = (gio, gia_tri)
    return gia_tri


def xoa_cache() -> None:
    """Dùng trong test — cache dính giữa các ca test là một nguồn nhiễu."""
    _CACHE.clear()


@dataclass(frozen=True)
class ChiSoCoBan:
    """Chỉ số đã chuẩn hoá. `None` nghĩa là KHÔNG có, không phải bằng 0."""

    ma: str
    co_du_lieu: bool
    ly_do: str
    nam: int | None
    nhom: str

    roe_pct: float | None = None
    roa_pct: float | None = None
    pe: float | None = None
    pb: float | None = None
    eps: float | None = None
    co_tuc_pct: float | None = None

    # Chỉ doanh nghiệp thường
    bien_ln_pct: float | None = None
    no_vay_tren_vcsh_pct: float | None = None
    kha_nang_tra_lai: float | None = None

    # Chỉ ngân hàng
    nim_pct: float | None = None
    vcsh_tren_tts_pct: float | None = None

    # Hậu tố `_tang_pct` là bắt buộc: nguồn đặt tên ba dòng này giống hệt
    # số dư, xem bẫy số 1 ở đầu file.
    ln_tang_pct: float | None = None
    vcsh_tang_pct: float | None = None
    tts_tang_pct: float | None = None


# ─────────────────────────────────────────────────────────────────────
# Đọc bảng
# ─────────────────────────────────────────────────────────────────────

#: Các dòng nguồn trả về nhưng KHÔNG được dùng, kèm lý do. Danh sách này
#: tồn tại để lần sau ai đó định dùng thì thấy ngay vì sao không nên.
KHONG_DUNG = {
    "roe_trailling": "nguồn trả 0.0 ở mọi mã, mọi năm",
    "roa_trailling": "nguồn trả 0.0 ở mọi mã, mọi năm",
}


def _nam_cot(df: pd.DataFrame) -> list[int]:
    ra = []
    for c in df.columns:
        s = str(c).strip()
        if s.isdigit() and 1990 < int(s) < 2100:
            ra.append(int(s))
    return sorted(ra, reverse=True)


def _lay(df: pd.DataFrame, ten: str, nam: int) -> float | None:
    """Giá trị của dòng `ten` ở cột năm `nam`, hoặc None.

    Cột năm được tra bằng tên cột chứ không qua `Series.get`: với khoá số
    nguyên, `get(2025)` bị hiểu là VỊ TRÍ 2025 chứ không phải nhãn.
    """
    if "item_id" not in df.columns:
        return None
    cot = str(nam) if str(nam) in df.columns else (
        nam if nam in df.columns else None)
    if cot is None:
        return None
    hang = df[df["item_id"].astype(str).str.strip() == ten]
    if hang.empty:
        return None
    v = pd.to_numeric(hang.iloc[0][cot], errors="coerce")
    return None if pd.isna(v) else float(v)


def _tai_bang_that(ma: str) -> pd.DataFrame | None:
    """Gọi vnstock. Tách riêng để test tiêm được hàm giả vào."""
    try:
        from vnstock_auth import ensure_api_key
        ensure_api_key()
        from vnstock.api.financial import Finance
    except Exception:
        return None
    try:
        df = Finance(source="KBS", symbol=ma, period="year",
                     show_log=False).ratio(lang="en", dropna=True)
    except Exception:
        return None
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None
    return df


def doc_chi_so(ma: str, tai_bang: Callable[[str], Any] | None = None) -> ChiSoCoBan:
    """Đọc bảng chỉ số của một mã và chuẩn hoá.

    `co_du_lieu=False` là một kết quả hợp lệ. Giao diện phải hiện "không
    có dữ liệu" chứ tuyệt đối không điền số thay thế — bản cũ của
    `financial_collector.py` từng sinh P/E từ `hash(symbol)`, và vì hash
    chuỗi được ngẫu nhiên hoá theo tiến trình, cùng một mã cho ra P/E khác
    nhau sau mỗi lần khởi động.
    """
    tai = tai_bang or _tai_bang_that
    df = _cache(f"fa:{ma}", lambda: tai(ma)) if tai_bang is None else tai(ma)

    def _trong(ly_do: str) -> ChiSoCoBan:
        return ChiSoCoBan(ma=ma, co_du_lieu=False, ly_do=ly_do, nam=None,
                          nhom=PHI_NGAN_HANG)

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return _trong(f"không lấy được bảng chỉ số từ {NGUON}")
    if "item_id" not in df.columns:
        return _trong("bảng nguồn không có cột item_id — cấu trúc đã đổi")

    nam_co = _nam_cot(df)
    if not nam_co:
        return _trong("bảng nguồn không có cột năm nào nhận ra được")

    nam = nam_co[0]
    nam_min = _dt.date.today().year - NAM_TOI_DA_CU
    if nam < nam_min:
        return _trong(f"năm mới nhất là {nam}, cũ hơn {nam_min} — đã BỎ thay "
                      f"vì hiển thị như số liệu hiện hành")

    ten = set(df["item_id"].astype(str).str.strip())
    la_ngan_hang = "net_interest_margin_nim" in ten or "net_margin" not in ten
    g = lambda k: _lay(df, k, nam)

    ra = ChiSoCoBan(
        ma=ma, co_du_lieu=True, ly_do="", nam=nam,
        nhom=NGAN_HANG if la_ngan_hang else PHI_NGAN_HANG,
        roe_pct=g("roe"), roa_pct=g("roa"),
        pe=g("pe_ratio"), pb=g("pb_ratio"),
        eps=g("trailing_eps"), co_tuc_pct=g("dividend_yield"),
        bien_ln_pct=None if la_ngan_hang else g("net_margin"),
        no_vay_tren_vcsh_pct=None if la_ngan_hang else g("debt_to_equity"),
        kha_nang_tra_lai=None if la_ngan_hang else g("interest_coverage"),
        nim_pct=g("net_interest_margin_nim") if la_ngan_hang else None,
        vcsh_tren_tts_pct=(g("equity_total_assets") if la_ngan_hang
                           else g("equity_to_assets")),
        ln_tang_pct=g("profit_after_tax_for_shareholders_of_the_parent_company"),
        vcsh_tang_pct=g("owners_equity"),
        tts_tang_pct=g("total_assets"),
    )
    if ra.roe_pct is None and ra.pe is None and ra.pb is None:
        return _trong(f"bảng {nam} có nhưng không nhận ra chỉ tiêu nào — "
                      f"tên dòng đã đổi")
    return ra


# ─────────────────────────────────────────────────────────────────────
# Chấm
# ─────────────────────────────────────────────────────────────────────

def _cham_sinh_loi(c: ChiSoCoBan, th: list, cb: list) -> float:
    d = 0.0
    if c.roe_pct is None:
        th.append("🟡 Không có ROE.")
        return d
    if c.roe_pct < 0:
        d -= 20
        th.append(f"🔴 ROE {c.roe_pct:.1f}% — doanh nghiệp đang lỗ trên vốn chủ.")
        cb.append("ROE âm")
    elif c.roe_pct >= ROE_TOT:
        d += 12
        th.append(f"✅ ROE {c.roe_pct:.1f}% — sinh lời trên vốn chủ cao.")
    elif c.roe_pct >= ROE_KHA:
        d += 6
        th.append(f"✅ ROE {c.roe_pct:.1f}% — khá.")
    elif c.roe_pct < ROE_YEU:
        d -= 6
        th.append(f"⚠️ ROE {c.roe_pct:.1f}% — thấp.")
    else:
        th.append(f"🟡 ROE {c.roe_pct:.1f}% — trung bình.")
    return d


def _cham_an_toan(c: ChiSoCoBan, th: list, cb: list) -> float:
    """Đòn bẩy và khả năng chịu đựng. Hai nhóm ngành, hai thước đo.

    Ngân hàng vay tiền là nghiệp vụ chứ không phải rủi ro, nên chấm họ
    bằng `debt_to_equity` là chấm sai bản chất. Với ngân hàng, thứ nói lên
    sức chịu đựng là tỷ lệ vốn chủ trên tổng tài sản.
    """
    d = 0.0
    if c.nhom == NGAN_HANG:
        if c.vcsh_tren_tts_pct is None:
            th.append("🟡 Không có tỷ lệ vốn chủ/tổng tài sản.")
        elif c.vcsh_tren_tts_pct < VCSH_TTS_MONG:
            d -= 8
            th.append(f"⚠️ Vốn chủ/Tổng tài sản {c.vcsh_tren_tts_pct:.1f}% — "
                      f"đệm vốn mỏng (dưới {VCSH_TTS_MONG:.0f}%).")
            cb.append("đệm vốn mỏng")
        else:
            d += 4
            th.append(f"✅ Vốn chủ/Tổng tài sản {c.vcsh_tren_tts_pct:.1f}%.")
        if c.nim_pct is not None:
            if c.nim_pct >= NIM_TOT:
                d += 6
                th.append(f"✅ NIM {c.nim_pct:.2f}% — biên lãi thuần tốt.")
            elif c.nim_pct < NIM_YEU:
                d -= 4
                th.append(f"⚠️ NIM {c.nim_pct:.2f}% — biên lãi thuần mỏng.")
            else:
                th.append(f"🟡 NIM {c.nim_pct:.2f}%.")
        return d

    if c.no_vay_tren_vcsh_pct is None:
        th.append("🟡 Không có tỷ lệ nợ vay/vốn chủ.")
    elif c.no_vay_tren_vcsh_pct > NO_VAY_CAO:
        d -= 8
        th.append(f"⚠️ Nợ vay/Vốn chủ {c.no_vay_tren_vcsh_pct:.0f}% — đòn bẩy cao.")
        cb.append("đòn bẩy cao")
    elif c.no_vay_tren_vcsh_pct < NO_VAY_THAP:
        d += 5
        th.append(f"✅ Nợ vay/Vốn chủ {c.no_vay_tren_vcsh_pct:.0f}% — đòn bẩy thấp.")
    else:
        th.append(f"🟡 Nợ vay/Vốn chủ {c.no_vay_tren_vcsh_pct:.0f}%.")

    if c.kha_nang_tra_lai is not None:
        if c.kha_nang_tra_lai < TRA_LAI_NGUY:
            d -= 12
            th.append(f"🔴 Khả năng trả lãi {c.kha_nang_tra_lai:.1f} lần — "
                      f"lợi nhuận không đủ gánh chi phí lãi vay.")
            cb.append("khả năng trả lãi dưới 2 lần")
        elif c.kha_nang_tra_lai >= TRA_LAI_AN_TOAN:
            d += 4
            th.append(f"✅ Khả năng trả lãi {c.kha_nang_tra_lai:.1f} lần.")
        else:
            th.append(f"🟡 Khả năng trả lãi {c.kha_nang_tra_lai:.1f} lần.")

    if c.bien_ln_pct is not None:
        if c.bien_ln_pct >= BIEN_LN_TOT:
            d += 6
            th.append(f"✅ Biên lợi nhuận {c.bien_ln_pct:.1f}%.")
        elif c.bien_ln_pct < BIEN_LN_YEU:
            d -= 5
            th.append(f"⚠️ Biên lợi nhuận {c.bien_ln_pct:.1f}% — mỏng.")
        else:
            th.append(f"🟡 Biên lợi nhuận {c.bien_ln_pct:.1f}%.")
    return d


def _cham_tang_truong(c: ChiSoCoBan, th: list, cb: list) -> float:
    d = 0.0
    if c.ln_tang_pct is None:
        th.append("🟡 Không có số tăng trưởng lợi nhuận.")
        return d
    if c.ln_tang_pct >= TANG_TRUONG_TOT:
        d += 10
        th.append(f"✅ Lợi nhuận sau thuế tăng {c.ln_tang_pct:+.1f}% so với năm trước.")
    elif c.ln_tang_pct <= TANG_TRUONG_XAU:
        d -= 10
        th.append(f"🔴 Lợi nhuận sau thuế {c.ln_tang_pct:+.1f}% so với năm trước.")
        cb.append("lợi nhuận suy giảm mạnh")
    else:
        th.append(f"🟡 Lợi nhuận sau thuế {c.ln_tang_pct:+.1f}% so với năm trước.")
    return d


def _cham_dinh_gia(c: ChiSoCoBan, th: list) -> float:
    """Định giá KHÔNG phải chất lượng.

    P/E thấp có thể là rẻ, mà cũng có thể là thị trường đang định giá đúng
    một doanh nghiệp đang xấu đi. Nên phần này có biên độ điểm nhỏ hơn hẳn
    ba phần trên, và câu chữ nói rõ đây là mức giá chứ không phải sức khoẻ.
    """
    d = 0.0
    if c.pe is not None and c.pe > 0:
        if c.pe <= PE_RE:
            d += 5
            th.append(f"✅ P/E {c.pe:.1f} — thị trường đang trả giá thấp.")
        elif c.pe >= PE_DAT:
            d -= 5
            th.append(f"⚠️ P/E {c.pe:.1f} — thị trường đang trả giá cao.")
        else:
            th.append(f"🟡 P/E {c.pe:.1f}.")
    elif c.pe is not None and c.pe <= 0:
        th.append(f"🔴 P/E {c.pe:.1f} — âm, doanh nghiệp đang lỗ.")
        d -= 5
    if c.pb is not None:
        if c.pb <= PB_RE:
            d += 3
            th.append(f"✅ P/B {c.pb:.2f}.")
        elif c.pb >= PB_DAT:
            d -= 3
            th.append(f"⚠️ P/B {c.pb:.2f} — cao so với giá trị sổ sách.")
        else:
            th.append(f"🟡 P/B {c.pb:.2f}.")
    return d


def _xep_hang(diem: float) -> str:
    if diem >= 70:
        return "TỐT"
    if diem >= 58:
        return "KHÁ"
    if diem >= 42:
        return "TRUNG BÌNH"
    if diem >= 30:
        return "YẾU"
    return "XẤU"


class FundamentalAgent:
    """Agent Cơ Bản — đánh giá sức khoẻ tài chính từ báo cáo năm.

    Trả về dict cùng họ với các agent ở `analysis_agents.py`, thêm khoá
    `available`. `available=False` nghĩa là không đọc được báo cáo; khi đó
    `diem` là None chứ không phải 50, để không ai lỡ cộng một con số trung
    tính vào công thức và tưởng đã tính tới yếu tố cơ bản.
    """

    NAME = "Fundamental Agent"

    def __init__(self, tai_bang: Callable[[str], Any] | None = None):
        self._tai_bang = tai_bang

    def analyze(self, ma: str) -> dict:
        c = doc_chi_so(ma, self._tai_bang)
        if not c.co_du_lieu:
            return {
                "agent": self.NAME, "symbol": ma, "available": False,
                "diem": None, "xep_hang": "KHÔNG CÓ DỮ LIỆU",
                "nhom": c.nhom, "nam": None, "nguon": NGUON,
                "signals": [f"⚠️ {c.ly_do}"],
                "canh_bao": [], "chi_so": c,
            }

        th: list[str] = []
        cb: list[str] = []
        diem = DIEM_NEN
        diem += _cham_sinh_loi(c, th, cb)
        diem += _cham_an_toan(c, th, cb)
        diem += _cham_tang_truong(c, th, cb)
        diem += _cham_dinh_gia(c, th)
        diem = max(DIEM_MIN, min(DIEM_MAX, diem))

        return {
            "agent": self.NAME, "symbol": ma, "available": True,
            "diem": round(diem, 1), "xep_hang": _xep_hang(diem),
            "nhom": c.nhom, "nam": c.nam, "nguon": NGUON,
            "signals": th, "canh_bao": cb, "chi_so": c,
        }
