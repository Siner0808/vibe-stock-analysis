"""Bảng sức khoẻ hệ thống — gom các phép kiểm RỜI RẠC thành MỘT bảng, CHỈ ĐỌC (BƯỚC 177, mốc B4).

VÌ SAO CÓ FILE NÀY
──────────────────
Sức khoẻ hệ thống nằm rải ở mười công cụ, mỗi cái một mã thoát riêng, và người
phải NHỚ mà chạy từng cái: chuông quét, chuông nguồn đứng, chuông cổng C5, chuông
bài học, lệch bản gói, hạng gói, bộ lọc VN-INDEX, cửa tự động, đường ngoài repo,
soát tuần. `docs/LO-TRINH.md` mốc B4: *"Bảng sức khoẻ hệ thống thay cho phần lớn
soát tay."* Module này chạy chúng TUẦN TỰ và đưa về một khuôn: bốn trạng thái.

BỐN TRẠNG THÁI, VÀ MỘT LUẬT CỨNG
────────────────────────────────
    XANH            công cụ chạy được và tự khai "ổn"
    VANG            công cụ chạy được và TỰ KHAI một mức cảnh báo
    DO              công cụ chạy được và tự khai có việc phải làm
    CHUA_KIEM_DUOC  không chạy được / hết giờ / thiếu thứ cần / mã thoát lạ

**CHUA_KIEM_DUOC không bao giờ là XANH** — cùng tinh thần `vnstock_goi.kiem_goi`
("mất mạng không được trả khớp"). Một bảng toàn xanh vì không phép nào chạy được
là đúng thứ dự án này tồn tại để chống. VANG chỉ có khi công cụ TỰ khai cảnh báo
(mỗi phép mang `chung_vang` — chữ của chính công cụ — và gác đòi nó có thật).

MÃ THOÁT 1 CỦA BA CHUÔNG LÀ MỘT-CHO-HAI-CHUYỆN
──────────────────────────────────────────────
`chuong_bao_quet`, `chuong_nguon_dung`, `canh_cong_c5` đều thoát 1 cho CẢ "đã
kêu thật" LẪN "không nhìn thấy gì nên kêu" (kéo hỏng, kho chưa cấu hình, lịch hết
hạn). Đọc mã thoát trần là biến "không kiểm được" thành "đỏ" — hoặc tệ hơn, một
ngoại lệ chưa bắt của Python (cũng thoát 1) thành "đỏ". Nên với mã thoát nằm trong
`ma_can_dau_hieu`, trạng thái chỉ thành DO khi đầu ra mang CÂU CỦA CHÍNH CÔNG CỤ
báo kêu (`dau_hieu`); không thấy câu nào → CHUA_KIEM_DUOC. Mọi tiến trình thoát
khác 0 mà đầu ra có `Traceback` → CHUA_KIEM_DUOC, bất kể bảng nói gì.

CHỈ ĐỌC
───────
Không phép nào được ghi. Tiến trình con chạy với `GITHUB_STEP_SUMMARY` bị GỠ
(vài chuông nối Markdown vào đó), `PYTHONDONTWRITEBYTECODE=1` (không rải
`__pycache__` vào repo) và stdin đóng. Hai phép có đường GHI ngầm nếu thiếu cache
VN-INDEX (`get_vni_df()` tải mạng rồi ghi `backtest/cache/`): chúng mang điều kiện
`cache_vnindex` và trả CHUA_KIEM_DUOC khi cache chưa có, thay vì tự đi ghi.
Chuông kéo sổ Sheets về FILE TẠM; không phép nào đẩy gì lên Sheets.

NGOÀI DANH MỤC (khai thẳng)
───────────────────────────
`data_quality.price_multiplier()` và `mau_bang_gia.doc_bang_gia("SSI")` (cũng ở
mục "Kiểm định kỳ" của `CLAUDE.md`): cần tham số do người chọn và gọi mạng giá;
chưa có ngưỡng nào để khai XANH/ĐỎ. Không đoán — để ngoài.

TUẦN TỰ, KHÔNG SONG SONG
────────────────────────
Nhiều phép đọc cùng sổ Sheets / cùng cache và ghi file tạm cùng tên; chạy song song
cho đỏ giả (cùng lý do năm cổng). Gác AST cấm `threading` / `concurrent` / `asyncio`
/ `multiprocessing` trong file này.

Module này KHÔNG được nhập bởi đường giao dịch / chấm điểm / dữ liệu (`run_daily`,
`paper_trading`, `master_agent`, `backtest/`): nó là bảng để NGƯỜI đọc, không là đầu
vào của quyết định nào.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Sequence

GOC = Path(__file__).resolve().parent

XANH = "XANH"
VANG = "VANG"
DO = "DO"
CHUA_KIEM_DUOC = "CHUA_KIEM_DUOC"
TRANG_THAI = (XANH, VANG, DO, CHUA_KIEM_DUOC)

#: Tiến trình con nổ ngoại lệ chưa bắt -> Python thoát 1, lẫn với "đã kêu".
DAU_NO = "Traceback (most recent call last)"

#: Số dòng tối đa của `chi_tiet`, và độ dài tối đa một dòng.
SO_DONG_TOI_DA = 3
DO_DAI_DONG = 200

#: Biến môi trường ép "đang ở máy phát triển" (1) hoặc "không" (0).
BIEN_MAY = "VIBE_SUC_KHOE_MAY"


# ─────────────────────────────────────────────────────────────────────
# Kiểu dữ liệu
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PhepKiem:
    """Một phép kiểm trong danh mục.

    Đúng MỘT trong hai: `tep` (công cụ dòng lệnh, đường dẫn tương đối từ gốc
    repo, chạy bằng subprocess) hoặc `ham` (cặp `(module, tên hàm)`, gọi trực tiếp
    trong `try`).

    `ma_thoat`: (mã, trạng thái) đọc từ docstring/mã của công cụ.
    `ma_can_dau_hieu`: mã thoát mà bảng KHÔNG đủ phân biệt (một mã cho nhiều
    chuyện) — phải có `dau_hieu` khớp mới ra trạng thái, không thì CHUA_KIEM_DUOC.
    `dau_hieu`: (mã, chuỗi con của đầu ra, trạng thái), khớp theo THỨ TỰ.
    `bang_chung`: (mã hoặc nhãn, chuỗi con PHẢI có trong file công cụ) — chữ của
    chính công cụ nói về mã/nhãn ấy; gác đòi nó có thật.
    `chung_vang`: chữ của công cụ tự khai mức cảnh báo; bắt buộc nếu VANG với tới được.
    `dieu_kien`: tên các điều kiện (xem `DIEU_KIEN`); không đạt -> CHUA_KIEM_DUOC.
    """

    ten: str
    mo_ta: str
    tep: str | None = None
    doi_so: tuple[str, ...] = ()
    ham: tuple[str, str] | None = None
    ma_thoat: tuple[tuple[int, str], ...] = ()
    ma_can_dau_hieu: tuple[int, ...] = ()
    dau_hieu: tuple[tuple[int, str, str], ...] = ()
    bang_chung: tuple[tuple[object, str], ...] = ()
    chung_vang: str = ""
    dieu_kien: tuple[str, ...] = ()
    timeout_giay: int = 60

    def __post_init__(self) -> None:
        if (self.tep is None) == (self.ham is None):
            raise ValueError(f"{self.ten}: phải có ĐÚNG MỘT trong `tep` và `ham`")
        for _, tt in self.ma_thoat:
            if tt not in TRANG_THAI:
                raise ValueError(f"{self.ten}: trạng thái lạ {tt!r}")
        for _, _, tt in self.dau_hieu:
            if tt not in TRANG_THAI:
                raise ValueError(f"{self.ten}: trạng thái lạ {tt!r}")
        for ten_dk in self.dieu_kien:
            if ten_dk not in DIEU_KIEN:
                raise ValueError(f"{self.ten}: điều kiện lạ {ten_dk!r}")
        # VANG với tới được mà không có lời công cụ tự khai = tự bịa mức cảnh báo.
        co_vang = (any(tt == VANG for _, tt in self.ma_thoat)
                   or any(tt == VANG for _, _, tt in self.dau_hieu))
        if co_vang and not self.chung_vang:
            raise ValueError(f"{self.ten}: VANG mà không có `chung_vang` "
                             f"(công cụ phải TỰ khai mức cảnh báo)")

    @property
    def lenh_tai_lap(self) -> str:
        """Lệnh để người chạy lại đúng phép này bằng tay."""
        if self.tep is not None:
            return " ".join(["python", self.tep, *self.doi_so])
        return _LENH_HAM[self.ten]


@dataclass(frozen=True)
class KetQua:
    """Kết quả một phép kiểm. `chi_tiet` tối đa `SO_DONG_TOI_DA` dòng."""

    ten: str
    trang_thai: str
    chi_tiet: tuple[str, ...]
    lenh_tai_lap: str
    thoi_gian_giay: float
    ly_do: str = ""


# ─────────────────────────────────────────────────────────────────────
# Điều kiện tiên quyết — trả None nếu đạt, hoặc LÝ DO không đạt
# ─────────────────────────────────────────────────────────────────────

def dk_may_phat_trien() -> str | None:
    """Phép kiểm chỉ có nghĩa ở MÁY của người dùng (đọc `~/.claude`, thư mục nhà).

    Nhận biết bằng `.venv` ở gốc repo (mọi lệnh trong `CLAUDE.md` dùng
    `./.venv/Scripts/python.exe`; Streamlit Cloud, Actions và phiên đám mây không có).
    Đây là SUY RA, có thể sai — `VIBE_SUC_KHOE_MAY=1` ép chạy, `=0` ép bỏ qua.
    """
    ep = os.environ.get(BIEN_MAY, "").strip()
    if ep == "1":
        return None
    if ep == "0":
        return f"{BIEN_MAY}=0: người dùng chọn bỏ qua phép kiểm chỉ-có-nghĩa-ở-máy"
    if (GOC / ".venv").is_dir():
        return None
    return ("chỉ có nghĩa ở máy phát triển (không thấy .venv ở gốc repo — "
            "Streamlit Cloud / Actions / phiên đám mây không phải máy ấy); "
            f"đặt {BIEN_MAY}=1 để ép chạy")


def dk_co_gh() -> str | None:
    if shutil.which("gh") is None:
        return "không có lệnh `gh` (cần `gh` đã đăng nhập để hỏi lượt CI)"
    return None


def dk_cache_vnindex() -> str | None:
    """Cache VN-INDEX phải ĐỌC ĐƯỢC sẵn: không thì `get_vni_df()` tải mạng rồi GHI cache."""
    try:
        from backtest import data as btd
        df = btd.load("VNINDEX")
    except Exception as e:
        return f"không đọc được cache VN-INDEX ({type(e).__name__}: {str(e)[:80]})"
    if df is None or len(df) == 0:
        return ("cache VN-INDEX chưa có — phép kiểm này sẽ tải mạng và GHI "
                "backtest/cache/, mà bảng sức khoẻ không được ghi gì")
    return None


DIEU_KIEN: dict[str, Callable[[], str | None]] = {
    "may_phat_trien": dk_may_phat_trien,
    "gh": dk_co_gh,
    "cache_vnindex": dk_cache_vnindex,
}


# ─────────────────────────────────────────────────────────────────────
# Phần THUẦN — không tiến trình, không mạng. Đây là phần được đục thử.
# ─────────────────────────────────────────────────────────────────────

def rut_gon(dau_ra: str, toi_da: int = SO_DONG_TOI_DA) -> tuple[str, ...]:
    """Tối đa `toi_da` dòng không rỗng: các dòng ĐẦU và dòng CUỐI.

    Dòng cuối giữ lại vì với một ngoại lệ chưa bắt đó là dòng nêu tên lỗi.
    """
    dong = [d.strip()[:DO_DAI_DONG] for d in str(dau_ra).splitlines() if d.strip()]
    if len(dong) <= toi_da:
        return tuple(dong)
    return tuple(dong[:toi_da - 1] + dong[-1:])


def danh_gia_ma_thoat(phep: PhepKiem, ma: int, dau_ra: str) -> tuple[str, str]:
    """(trạng thái, lý do) từ mã thoát + đầu ra của một công cụ dòng lệnh.

    Thứ tự CỨNG: (1) nổ ngoại lệ -> CHUA; (2) dấu hiệu của công cụ; (3) mã mơ hồ
    không có dấu hiệu -> CHUA; (4) bảng; (5) mã lạ -> CHUA. Không nhánh nào cho
    XANH trừ bảng của công cụ tự khai XANH.
    """
    if ma != 0 and DAU_NO in dau_ra:
        return CHUA_KIEM_DUOC, f"công cụ nổ ngoại lệ chưa bắt (mã thoát {ma})"
    for m, chuoi, tt in phep.dau_hieu:
        if m == ma and chuoi in dau_ra:
            return tt, f"đầu ra mang «{chuoi}»"
    if ma in phep.ma_can_dau_hieu:
        return CHUA_KIEM_DUOC, (f"mã thoát {ma} gộp nhiều chuyện và đầu ra không "
                                f"mang câu nào của công cụ để phân biệt")
    bang = dict(phep.ma_thoat)
    if ma not in bang:
        return CHUA_KIEM_DUOC, f"mã thoát lạ {ma} (công cụ không khai mã này)"
    tt = bang[ma]
    if tt == CHUA_KIEM_DUOC:
        return CHUA_KIEM_DUOC, f"công cụ tự khai chưa kiểm được (mã thoát {ma})"
    return tt, ""


def danh_gia_kiem_goi(tt) -> tuple[str, str]:
    """`vnstock_goi.TrangThaiGoi` -> (trạng thái, lý do). Ba nhãn của chính module ấy."""
    import vnstock_goi as vg
    tinh_trang = getattr(tt, "tinh_trang", None)
    if tinh_trang == vg.KHOP:
        return XANH, ""
    if tinh_trang == vg.LECH:
        return DO, "hạng thư viện cục bộ lệch hạng máy chủ"
    if tinh_trang == vg.CHUA_KIEM_DUOC:
        return CHUA_KIEM_DUOC, str(getattr(tt, "ly_do", ""))
    return CHUA_KIEM_DUOC, f"trạng thái lạ {tinh_trang!r}"


def danh_gia_status(st) -> tuple[str, str]:
    """`market_filter.status()` -> (trạng thái, lý do).

    `active` True -> XANH. `active` False MÀ có `ngay_cuoi` (đọc được dữ liệu và
    đo được độ cũ) -> DO: bộ lọc quá hạn. `active` False không có `ngay_cuoi`
    (không có dữ liệu / lỗi nạp) -> CHUA_KIEM_DUOC: không đo được độ cũ.
    """
    if not isinstance(st, dict):
        return CHUA_KIEM_DUOC, "status() không trả dict"
    if st.get("active") is True:
        return XANH, ""
    if st.get("ngay_cuoi"):
        return DO, "bộ lọc VN-INDEX không dùng được: dữ liệu quá hạn"
    return CHUA_KIEM_DUOC, "không đo được độ cũ của VN-INDEX (không có dữ liệu hoặc lỗi nạp)"


def ma_thoat_tong(ket_qua: Sequence[KetQua]) -> int:
    """Mã thoát của CLI: 1 có DO · 2 không DO nhưng có CHUA_KIEM_DUOC · 0 còn lại.

    Bảng RỖNG trả 2, không 0: không phép nào chạy thì không có gì để gọi là xanh.
    VANG một mình trả 0 — nó là cảnh báo của công cụ, không phải việc phải làm
    (cùng luật chuông của dự án: cảnh báo đi bằng chữ, không bằng mã thoát).
    """
    if not ket_qua:
        return 2
    if any(k.trang_thai == DO for k in ket_qua):
        return 1
    if any(k.trang_thai == CHUA_KIEM_DUOC for k in ket_qua):
        return 2
    return 0


def dong_hien_thi(ket_qua: Sequence[KetQua]) -> list[dict]:
    """Mỗi kết quả MỘT dòng cho giao diện — KHÔNG lọc, KHÔNG gộp (CHUA_KIEM_DUOC cũng hiện).

    `chi_tiet` luôn có ít nhất lý do khi chưa kiểm được: một ô trắng ở dòng đó sẽ
    đọc như "không có gì để nói".
    """
    return [{"ten": k.ten, "trang_thai": k.trang_thai,
             "chi_tiet": list(k.chi_tiet),
             "ly_do": k.ly_do,
             "lenh_tai_lap": k.lenh_tai_lap,
             "thoi_gian_giay": k.thoi_gian_giay} for k in ket_qua]


# ─────────────────────────────────────────────────────────────────────
# Chạy
# ─────────────────────────────────────────────────────────────────────

def _moi_truong_con() -> dict[str, str]:
    """Môi trường tiến trình con: không chỗ ghi ngầm (summary, bytecode)."""
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_STEP_SUMMARY"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _chay_tep(phep: PhepKiem) -> tuple[str, str, tuple[str, ...]]:
    """Chạy công cụ dòng lệnh -> (trạng thái, lý do, chi tiết)."""
    duong = GOC / str(phep.tep)
    if not duong.is_file():
        return CHUA_KIEM_DUOC, f"không thấy công cụ {phep.tep}", ()
    try:
        ra = subprocess.run(
            [sys.executable, str(duong), *phep.doi_so],
            cwd=str(GOC), env=_moi_truong_con(), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            timeout=phep.timeout_giay, check=False)
    except subprocess.TimeoutExpired:
        return CHUA_KIEM_DUOC, f"hết giờ sau {phep.timeout_giay}s", ()
    except Exception as e:
        return CHUA_KIEM_DUOC, f"không chạy được: {type(e).__name__}: {str(e)[:100]}", ()
    dau_ra = ra.stdout if isinstance(ra.stdout, str) else ""
    tt, ly_do = danh_gia_ma_thoat(phep, ra.returncode, dau_ra)
    return tt, ly_do, rut_gon(dau_ra)


def _chay_kiem_goi() -> tuple[str, str, tuple[str, ...]]:
    import vnstock_goi as vg
    tt = vg.kiem_goi(dung_cache=False)
    trang_thai, ly_do = danh_gia_kiem_goi(tt)
    return trang_thai, ly_do, rut_gon(tt.dong_log())


def _chay_market_status() -> tuple[str, str, tuple[str, ...]]:
    import market_filter as mf
    # Cache trong tiến trình (lru_cache) giữ bản nạp cũ: xoá để ĐỌC LẠI file cache
    # trên đĩa. Chỉ bộ nhớ; điều kiện `cache_vnindex` đã bảo đảm không đi mạng/ghi.
    mf.get_vni_df.cache_clear()
    st = mf.status()
    trang_thai, ly_do = danh_gia_status(st)
    note = str(st.get("note", "")) if isinstance(st, dict) else ""
    return trang_thai, ly_do, rut_gon(note)


_CHAY_HAM: dict[str, Callable[[], tuple[str, str, tuple[str, ...]]]] = {
    "kiem_goi": _chay_kiem_goi,
    "market_status": _chay_market_status,
}

_LENH_HAM = {
    "kiem_goi": ('python -c "import vnstock_goi as g; '
                 'print(g.kiem_goi(dung_cache=False).dong_log())"'),
    "market_status": 'python -c "import market_filter as m; print(m.status())"',
}


def kiem_mot(phep: PhepKiem) -> KetQua:
    """Chạy MỘT phép. KHÔNG BAO GIỜ ném: mọi ngoại lệ thành CHUA_KIEM_DUOC."""
    bat_dau = time.monotonic()
    try:
        chua_dat = next((ly for ly in (DIEU_KIEN[ten]() for ten in phep.dieu_kien)
                         if ly), None)
        if chua_dat is not None:
            tt, ly_do, chi_tiet = CHUA_KIEM_DUOC, chua_dat, ()
        elif phep.tep is not None:
            tt, ly_do, chi_tiet = _chay_tep(phep)
        else:
            tt, ly_do, chi_tiet = _CHAY_HAM[phep.ten]()
    except Exception as e:
        tt, ly_do, chi_tiet = (CHUA_KIEM_DUOC,
                               f"không chạy được: {type(e).__name__}: {str(e)[:100]}", ())
    if tt not in TRANG_THAI:                       # hàng rào cuối: không có trạng thái thứ năm
        tt, ly_do = CHUA_KIEM_DUOC, f"trạng thái lạ {tt!r}"
    if tt == CHUA_KIEM_DUOC and ly_do and not chi_tiet:
        chi_tiet = (ly_do,)
    return KetQua(ten=phep.ten, trang_thai=tt, chi_tiet=tuple(chi_tiet),
                  lenh_tai_lap=phep.lenh_tai_lap,
                  thoi_gian_giay=round(time.monotonic() - bat_dau, 2), ly_do=ly_do)


def _chon_phep(chon: Sequence[str] | None) -> list[PhepKiem]:
    if chon is None:
        return list(DANH_MUC)
    ten_chon = list(chon)
    if not ten_chon:
        raise ValueError("`chon` rỗng: chọn ít nhất một phép (hoặc None để chạy hết)")
    hop_le = {p.ten for p in DANH_MUC}
    la = sorted(set(ten_chon) - hop_le)
    if la:
        raise ValueError(f"phép kiểm không có trong danh mục: {', '.join(la)}")
    return [p for p in DANH_MUC if p.ten in set(ten_chon)]


def kiem_lan_luot(chon: Sequence[str] | None = None) -> Iterator[KetQua]:
    """Từng kết quả MỘT, theo thứ tự danh mục, TUẦN TỰ (cho app vẽ tiến độ)."""
    for phep in _chon_phep(chon):
        yield kiem_mot(phep)


def kiem_tat_ca(chon: Sequence[str] | None = None) -> list[KetQua]:
    """Chạy các phép (mặc định: cả danh mục) TUẦN TỰ. `chon` = tên phép."""
    return list(kiem_lan_luot(chon))


# ─────────────────────────────────────────────────────────────────────
# Danh mục — mỗi phép khai mã thoát ĐÃ ĐỌC từ công cụ, kèm câu của công cụ
# ─────────────────────────────────────────────────────────────────────

DANH_MUC: tuple[PhepKiem, ...] = (
    PhepKiem(
        ten="chuong_bao_quet",
        mo_ta="Ngày làm việc nào (3 ngày gần nhất) không có lượt quét thành công",
        tep="tools/chuong_bao_quet.py",
        ma_thoat=((0, XANH), (1, DO)),
        ma_can_dau_hieu=(1,),
        dau_hieu=((1, "Không đọc được danh sách lượt chạy", CHUA_KIEM_DUOC),
                  (1, "Không có lượt quét nào thành công", DO)),
        bang_chung=((0, "Mọi ngày trong khoảng soát đều có lượt quét thành công."),
                    (1, "Không có lượt quét nào thành công trong ngày")),
        timeout_giay=60),
    PhepKiem(
        ten="chuong_nguon_dung",
        mo_ta="Có phiên theo lịch mà không có nến VN-INDEX mới (nguồn dữ liệu đứng)",
        tep="tools/chuong_nguon_dung.py",
        ma_thoat=((0, XANH), (1, DO)),
        ma_can_dau_hieu=(1,),
        dau_hieu=((1, "Không kéo được VN-INDEX", CHUA_KIEM_DUOC),
                  (1, "Chuỗi VN-INDEX rỗng", CHUA_KIEM_DUOC),
                  (1, "[CHUA_BIET]", CHUA_KIEM_DUOC),
                  (1, "[NGUON_DUNG]", DO),
                  (1, "[BANG_SAI]", DO)),
        bang_chung=((0, "0 nếu yên, 1 nếu phải kêu."),
                    (1, "0 nếu yên, 1 nếu phải kêu.")),
        timeout_giay=90),
    PhepKiem(
        ten="canh_cong_c5",
        mo_ta="Điều kiện dừng đã đạt mà cổng C5 còn mở / cổng đóng mà vẫn rò lệnh",
        tep="tools/canh_cong_c5.py",
        ma_thoat=((0, XANH), (1, DO)),
        ma_can_dau_hieu=(1,),
        dau_hieu=((1, "ĐIỀU KIỆN DỪNG ĐÃ ĐẠT NHƯNG CỔNG C5 VẪN MỞ", DO),
                  (1, "CỔNG C5 RÒ RỈ", DO),
                  (1, "KHÔNG ĐO ĐƯỢC", CHUA_KIEM_DUOC),
                  (1, "không kéo được sổ lệnh", CHUA_KIEM_DUOC),
                  (1, "kho ngoài chưa cấu hình", CHUA_KIEM_DUOC)),
        bang_chung=((0, "0 = không phải làm gì, 1 = phải kêu."),
                    (1, "0 = không phải làm gì, 1 = phải kêu.")),
        dieu_kien=("cache_vnindex",),
        timeout_giay=120),
    PhepKiem(
        ten="chuong_bai_hoc",
        mo_ta="Lệnh đóng quá hạn một phiên mà chưa có bài học (tiêu chí ra giai đoạn B)",
        tep="tools/chuong_bai_hoc.py",
        ma_thoat=((0, XANH), (1, DO), (2, CHUA_KIEM_DUOC)),
        bang_chung=((0, "xanh: không lệnh nào quá hạn"),
                    (1, "VI PHẠM: có lệnh đóng quá hạn một phiên mà chưa có bài học"),
                    (2, "CHƯA KIỂM ĐƯỢC: Sheets không đọc được")),
        timeout_giay=120),
    PhepKiem(
        ten="so_ban_goi",
        mo_ta="Bản thư viện ở CI lệch bản ở máy này (gói quyết định số / giao diện)",
        tep="tools/so_ban_goi.py",
        ma_thoat=((0, XANH), (1, VANG), (2, CHUA_KIEM_DUOC)),
        bang_chung=((0, "KHỚP — hai nơi cùng bản trên mọi gói so được."),
                    (1, "CÓ chạm chỗ quyết định."),
                    (2, "CHƯA KIỂM ĐƯỢC: không hỏi được `gh`")),
        chung_vang="Đây KHÔNG phải lỗi",
        dieu_kien=("gh",),
        timeout_giay=180),
    PhepKiem(
        ten="kiem_goi",
        mo_ta="Hạng gói vnstock cục bộ có khớp hạng máy chủ không",
        ham=("vnstock_goi", "kiem_goi"),
        bang_chung=(("KHOP", "`KHOP` / `LECH` / `CHUA_KIEM_DUOC`"),
                    ("CHUA_KIEM_DUOC", 'mà trả về "khớp" thì phép kiểm này lại trở thành đúng thứ nó sinh ra để bắt.')),
        timeout_giay=30),
    PhepKiem(
        ten="market_status",
        mo_ta="Bộ lọc VN-INDEX có thật sự đang hoạt động (không quá hạn) không",
        ham=("market_filter", "status"),
        bang_chung=(("active", "Bộ lọc có thật sự đang hoạt động không."),),
        dieu_kien=("cache_vnindex",),
        timeout_giay=30),
    PhepKiem(
        ten="kiem_cua_song",
        mo_ta="Cửa tự động khai ở docs/cua-du-an.json đã đăng ký toàn cục chưa",
        tep="tools/kiem_cua_song.py",
        ma_thoat=((0, XANH), (1, DO), (2, CHUA_KIEM_DUOC)),
        bang_chung=((0, "0 = mọi hook trong bản khai đều có bản toàn cục"),
                    (1, "1 = có hook CHƯA đăng ký toàn cục"),
                    (2, "2 = CHƯA KIỂM ĐƯỢC (không đọc được một trong hai file)")),
        dieu_kien=("may_phat_trien",),
        timeout_giay=30),
    PhepKiem(
        ten="kiem_duong_ngoai_repo",
        mo_ta="Đường dẫn ngoài repo mà tài liệu sống nêu tên: còn hay trỏ vào chỗ trống",
        tep="tools/kiem_duong_ngoai_repo.py",
        ma_thoat=((0, XANH), (1, DO), (2, CHUA_KIEM_DUOC)),
        bang_chung=((0, "0 sạch · 1 có con trỏ chết · 2 CHƯA KIỂM ĐƯỢC."),
                    (1, "0 sạch · 1 có con trỏ chết · 2 CHƯA KIỂM ĐƯỢC."),
                    (2, "0 sạch · 1 có con trỏ chết · 2 CHƯA KIỂM ĐƯỢC.")),
        dieu_kien=("may_phat_trien",),
        timeout_giay=30),
    PhepKiem(
        ten="soat_tuan",
        mo_ta="Phần máy của soát định kỳ: lời khai chưa ai mở, quá nhịp, BƯỚC chưa khai sổ tay",
        tep="tools/soat_tuan.py",
        ma_thoat=((0, XANH), (2, CHUA_KIEM_DUOC)),
        dau_hieu=((0, "::warning", VANG),),
        bang_chung=((0, "Nó KHÔNG làm đỏ job chỉ vì có lời khai cần phán"),
                    (2, "Job chỉ đỏ khi MÁY hỏng")),
        chung_vang="::warning title=Soát tuần",
        timeout_giay=60),
)

#: Tên phép -> phép. Tên là khoá của `--chi`.
THEO_TEN: dict[str, PhepKiem] = {p.ten: p for p in DANH_MUC}
