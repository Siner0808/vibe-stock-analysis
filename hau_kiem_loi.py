"""Hậu kiểm BẰNG LỜI cho mỗi lệnh ảo đã đóng — B1 (BƯỚC 203), phần THUẦN.

Đặc tả người dùng duyệt 17/10/2026: `docs/thiet-ke-b1-hau-kiem-loi.md`. Mỗi lệnh ảo đã
đóng có MỘT đoạn văn bốn phần do model ngôn ngữ viết (Gemini 3.8 Flash từ BƯỚC 229; trước
đó Claude Opus 5.5) từ số máy ĐÃ tính (nhật ký "vì sao" +
sổ bài học B3), để NGƯỜI DÙNG đọc và học. CHỈ ĐỂ HIỆN (khuôn B6): không module nào
trên đường sinh lệnh, điểm, ngưỡng, điều kiện dừng, backtest hay tầng 3 đọc nó.

File này KHÔNG gọi mạng, KHÔNG ghi đĩa, KHÔNG nhập SDK của model (`google.genai`) — phần chạy
`tools/hau_kiem_loi.py` làm những việc ấy. Mức module chỉ nhập thư viện chuẩn vì
`sheets_store` nhập file này để lấy lược đồ tab `hau_kiem`; các hàm cần `so_bai_hoc`,
`nhat_ky_vi_sao`, `paper_metrics` nhập chúng TRONG hàm (nhập ở mức module sẽ kéo cả
chuỗi `paper_trading` vào `sheets_store`).

MỘT BẢNG LUẬT (`LUAT_VIET`): lời dặn gửi model (`LOI_DAN`) DỰNG TỪ bảng này, và máy
kiểm (`kiem_dau_ra`) kiểm theo chính bảng này — luật nói với model và luật máy kiểm
không thể trôi khỏi nhau. Máy bắt số bịa, câu cấm và mã lạ; nó KHÔNG bắt được một lập
luận sai dùng toàn số đúng, nên app luôn đặt bảng phân rã của máy cạnh đoạn văn.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

#: Người dùng chọn 17/10/2026 "Opus 5.5 (Recommended)"; đổi 26/10/2026 (BƯỚC 229) vì API của
#: Anthropic cần nạp tín dụng: "Đổi sang Gemini 3.8 Flash (Recommended)", bậc miễn phí.
MODEL = "gemini-3.8-flash"
#: Model dự phòng (BƯỚC 233). Ba trên bốn lượt chạy bằng Gemini 26–27/10/2026 viết 0 lệnh:
#: 3.8 Flash bậc miễn phí trả 503 UNAVAILABLE ("high demand") hoặc 504 DEADLINE_EXCEEDED.
#: Lời gọi chính hỏng vì lỗi TẠM thì phần chạy gọi model này MỘT lần cho cùng lệnh, cùng mọi
#: tham số khác; hạn mức ngày của bậc miễn phí tính riêng từng model (429 thật ghi
#: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, BƯỚC 229). Người dùng chọn
#: 27/10/2026: "A. Lui model + rút hạn chờ (Recommended)".
MODEL_DU_PHONG = "gemini-3.5-flash-lite"
#: `thinking_level` — mặc định của Gemini 3.8 Flash là `medium` (tài liệu Google, đọc
#: 26/10/2026); đặt TƯỜNG MINH. Lượt chạy thật đầu tiên là phép đo; đổi hay giữ là quyết
#: định của người dùng sau khi đọc (đặc tả mục 9). Tên cột `effort` của tab giữ nguyên.
EFFORT = "medium"
#: `max_output_tokens`; cũng là trần tiền ra của một lời gọi. CHƯA KIỂM: tài liệu SDK không
#: nói nó có gồm token suy nghĩ hay không — lượt đo đầu đọc `thoughts_token_count`.
MAX_TOKENS = 8000
#: Người dùng chọn 17/10/2026: "5 $ mỗi tháng (Recommended)". Bậc miễn phí không tính tiền,
#: nhưng máy không biết khoá đang ở bậc nào, nên vẫn cộng theo giá bậc trả phí: lớp thứ hai.
TRAN_USD_THANG = 5.0
SO_LENH_MOI_LUOT = 10
#: Một lệnh hỏng (bị bác, từ chối, bị cắt) tới số lần này thì dừng, chờ người xem.
SO_LAN_TOI_DA = 2
#: USD mỗi một triệu token (vào, ra) ở bậc TRẢ PHÍ — trang giá của Google đọc 26/10/2026:
#: 0,75/3,75 tới 31/12/2026, 1,50/7,50 từ 01/01/2027; giá ra gồm token suy nghĩ. Lấy mức
#: CAO (`gia_cao_nhat`): ước dư, không bao giờ thiếu. Bậc miễn phí thật ra là 0.
#: `gemini-3.5-flash-lite` (BƯỚC 233, cùng trang đọc 27/10/2026): 0,30/2,50, giá ra gồm
#: token suy nghĩ — thấp hơn nên mức cao của bảng không đổi. Mọi model phần chạy gọi phải
#: có mặt ở đây (gác `tests/test_tools_hau_kiem_loi.py`).
GIA_USD_MOI_TRIEU: dict[str, tuple[float, float]] = {
    "gemini-3.8-flash": (1.50, 7.50),
    "gemini-3.5-flash-lite": (0.30, 2.50),
}

TT_DAT = "DAT"
TT_BI_BAC = "BI_BAC"
TT_TU_CHOI = "TU_CHOI"
TT_CAT_CUT = "CAT_CUT"
#: Trạng thái của phép đo vế "có lời" khi B1 chưa bật (`NGAY_HAU_KIEM_LOI_BAT_DAU`).
TT_CHUA_BAT = "chua_bat"

#: Bốn phần người dùng chọn 17/10/2026 (cả bốn).
TRUONG: tuple[str, ...] = ("ke_lai", "khong_chung_minh", "theo_doi", "kien_thuc")
GIOI_HAN_TU: dict[str, int] = {"ke_lai": 180, "khong_chung_minh": 80, "theo_doi": 80,
                               "kien_thuc": 80}
NHAN_GIA_THUYET = "Chưa kiểm:"

#: Thứ tự cột = hợp đồng với tab `hau_kiem` trên Google Sheets (đặc tả mục 7).
COT_HAU_KIEM: tuple[str, ...] = (
    "trade_id", "lan", "symbol", "exit_date", "trang_thai", "ly_do_bac", *TRUONG,
    "model_yeu_cau", "model_phuc_vu", "effort", "bam_loi_dan", "bam_du_kien",
    "token_vao", "token_ra", "chi_phi_usd_uoc", "stop_reason", "viet_luc",
)
COT_SO_NGUYEN: frozenset[str] = frozenset({"trade_id", "lan", "token_vao", "token_ra"})
COT_SO_THUC: frozenset[str] = frozenset({"chi_phi_usd_uoc"})
#: Cột chữ được rỗng: dòng bị từ chối không có văn, dòng đạt không có lý do bác.
COT_CHU_RONG_DUOC: frozenset[str] = frozenset(
    {"ly_do_bac", *TRUONG, "model_phuc_vu", "stop_reason"})

SCHEMA_BON_TRUONG: dict = {
    "type": "object",
    "properties": {t: {"type": "string"} for t in TRUONG},
    "required": list(TRUONG),
    "additionalProperties": False,
}

#: Ngày bật B1 (khoá API có, workflow bật). None = CHƯA BẬT: vế "có lời" của chuông
#: chưa đo. Lệnh đóng trước ngày ấy không tính và không điền bù (khuôn Q13). Đặt 26/10/2026
#: ở BƯỚC 229, cùng ngày khoá Gemini có và lượt đo thật đầu tiên viết được lệnh.
NGAY_HAU_KIEM_LOI_BAT_DAU: Optional[str] = "2026-10-26"

NHAN_HIEN = "Gemini viết · chỉ để đọc · máy chỉ kiểm số và câu chữ"
#: Nhãn hiện của bốn trường — app và bản tin dùng chung (BƯỚC 205).
NHAN_TRUONG: dict[str, str] = {
    "ke_lai": "Kể lại", "khong_chung_minh": "Điều một lệnh không chứng minh",
    "theo_doi": "Nên theo dõi", "kien_thuc": "Kiến thức"}

#: `finish_reason` của Gemini (tên trong `google.genai.types.FinishReason`, bản 2.33.0).
KET_THUC_XONG = "STOP"
KET_THUC_CAT = "MAX_TOKENS"
#: Bị chặn vì an toàn hay nội dung -> TU_CHOI. Lời nhắc bị chặn TRƯỚC khi có ứng viên
#: (`prompt_feedback.block_reason`) cũng là từ chối, `stop_reason` ghi "BLOCKED:<lý do>".
KET_THUC_TU_CHOI: frozenset[str] = frozenset(
    {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"})


# ── Đọc số và ngày trong văn ─────────────────────────────────────────────

_NGAY_ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
_NGAY_VN = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")
#: Số đứng riêng: không dính chữ phía trước (`MA20`), dấu `−` Unicode như `-`.
_SO = re.compile(r"(?<![\w.,])[+\-−]?\d+(?:[.,]\d+)*(?!\d)")
_NGHIN_CHAM = re.compile(r"\d{1,3}(?:\.\d{3})+")
#: Số kiểu Anh `53,500` — chỉ xét trong chuỗi NGUỒN (lý do vào lệnh của sổ thật ghi
#: "Vào lệnh=53,500 VNĐ", đo 17/10/2026); văn của model vẫn đọc dấu phẩy là thập phân.
_NGHIN_PHAY = re.compile(r"\d{1,3}(?:,\d{3})+")


def _doc_so(tok: str) -> tuple[float, int]:
    """Một số viết kiểu Việt Nam -> (giá trị TUYỆT ĐỐI, số chữ số thập phân đã viết).

    Có cả `.` và `,` thì `.` ngăn nghìn; chỉ `,` thì `,` là dấu thập phân; chỉ `.` thì
    là ngăn nghìn khi khớp `1.234.567`, ngược lại là dấu thập phân (chuỗi Python).
    Dấu đặt ngoài: "lỗ 5,21%" và −5,21 là cùng một số.
    """
    t = tok.lstrip("+-−")
    if "." in t and "," in t:
        nguyen, _, le = t.replace(".", "").partition(",")
    elif "," in t:
        nguyen, _, le = t.partition(",")
    elif _NGHIN_CHAM.fullmatch(t):
        nguyen, le = t.replace(".", ""), ""
    else:
        nguyen, _, le = t.partition(".")
    return float(f"{nguyen}.{le}" if le else nguyen), len(le)


def _ngay_iso(s: str) -> tuple[set[str], str]:
    """(các ngày ISO trong chuỗi, chuỗi đã xoá ngày)."""
    ngay = {f"{a}-{b}-{c}" for a, b, c in _NGAY_ISO.findall(s)}
    ngay |= {f"{c}-{int(b):02d}-{int(a):02d}" for a, b, c in _NGAY_VN.findall(s)}
    return ngay, _NGAY_VN.sub(" ", _NGAY_ISO.sub(" ", s))


def so_trong_van(s: str) -> tuple[set[str], list[tuple[float, int]]]:
    """(ngày ISO, [(giá trị tuyệt đối, số chữ số thập phân)]) có trong một đoạn văn."""
    ngay, con = _ngay_iso(s)
    return ngay, [_doc_so(m.group(0)) for m in _SO.finditer(con)]


def _la(o: Any):
    """Mọi lá (số, chuỗi) của một cấu trúc JSON-được."""
    if isinstance(o, Mapping):
        for v in o.values():
            yield from _la(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _la(v)
    else:
        yield o


def so_nguon(du_kien: Mapping) -> tuple[set[str], list[float]]:
    """Mọi ngày và số mà đoạn văn ĐƯỢC dùng: lá số của dữ kiện, cộng ngày và số nằm
    trong lá chuỗi (lý do vào lệnh ghi "RSI 71.3…" là một nguồn hợp lệ)."""
    ngay: set[str] = set()
    so: list[float] = []
    for v in _la(du_kien):
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            so.append(abs(float(v)))
        elif isinstance(v, str):
            n, con = _ngay_iso(v)
            ngay |= n
            for m in _SO.finditer(con):
                tok = m.group(0)
                so.append(_doc_so(tok)[0])
                if _NGHIN_PHAY.fullmatch(tok.lstrip("+-−")):
                    so.append(float(tok.lstrip("+-−").replace(",", "")))
    return ngay, so


def _khop(x: float, so_le: int, nguon: Sequence[float]) -> bool:
    """`x` viết với `so_le` chữ số thập phân là một cách làm tròn của một số nguồn."""
    nua = 0.5 * 10 ** (-so_le) + 1e-9
    return any(abs(s - x) <= nua for s in nguon)


# ── Sáu luật ─────────────────────────────────────────────────────────────

def _cac_doan(van: Mapping[str, Any]) -> list[tuple[str, str]]:
    return [(t, van[t]) for t in TRUONG if isinstance(van.get(t), str)]


def _kiem_so(van: Mapping, dk: Mapping) -> list[str]:
    ngay_nguon, so_ng = so_nguon(dk)
    loi = []
    for t, s in _cac_doan(van):
        ngay, so = so_trong_van(s)
        loi += [f"{t}: ngày {n} không có trong dữ kiện" for n in sorted(ngay - ngay_nguon)]
        loi += [f"{t}: số {x:g} không có trong dữ kiện" for x, d in so
                if not _khop(x, d, so_ng)]
    return loi


_PHU_DINH = re.compile(r"\b(không|chưa)\b", re.IGNORECASE)
_HET_CAU = re.compile(r"[.!?\n]")


def _bi_phu_dinh(s: str, dau: int) -> bool:
    """Cụm ở vị trí `dau` đứng sau "không"/"chưa" trong cùng câu, cách ≤ 25 ký tự."""
    truoc = s[max(0, dau - 25):dau]
    truoc = _HET_CAU.split(truoc)[-1]
    return bool(_PHU_DINH.search(truoc))


def _tim_cum(van: Mapping, cum: Sequence[str]) -> list[str]:
    loi = []
    for t, s in _cac_doan(van):
        for c in cum:
            for m in re.finditer(re.escape(c), s, re.IGNORECASE):
                if not _bi_phu_dinh(s, m.start()):
                    loi.append(f"{t}: \"{m.group(0)}\"")
    return loi


_CAM_MOT_LENH: tuple[str, ...] = ("chứng minh", "chắc chắn", "luôn luôn", "agent sai",
                                  "agent đã sai")
_TIN_HIEU_SAI = "tín hiệu sai"


def _kiem_mot_lenh(van: Mapping, dk: Mapping) -> list[str]:
    loi = _tim_cum(van, _CAM_MOT_LENH)
    if not (dk.get("bai_hoc") or {}).get("cach_goi"):
        loi += [f"{v} — dữ kiện không có cach_goi" for v in _tim_cum(van, (_TIN_HIEU_SAI,))]
    return loi


_CAM_KHUYEN_NGHI: tuple[str, ...] = ("nên mua", "nên bán", "hãy mua", "hãy bán",
                                     "khuyến nghị")


def _kiem_khuyen_nghi(van: Mapping, dk: Mapping) -> list[str]:
    return _tim_cum(van, _CAM_KHUYEN_NGHI)


#: Chữ viết tắt ba ký tự in hoa hợp lệ, không phải mã cổ phiếu.
VIET_TAT: frozenset[str] = frozenset({
    "HOSE", "HNX", "UPCOM", "ATC", "ATO", "RSI", "MACD", "ATR", "SMA", "EMA", "OBV",
    "ADX", "VND", "USD", "ROE", "EPS"})
_MA = re.compile(r"(?<![\w-])[A-Z][A-Z0-9]{2}(?![\w-])")


def _kiem_ma(van: Mapping, dk: Mapping) -> list[str]:
    # Mã hợp lệ = chữ viết tắt + mọi mã nằm trong một lá chuỗi của dữ kiện: mã của
    # lệnh (`lenh.symbol`) và mã cùng ngành (`ma_cung_nganh`) đều là lá chuỗi.
    duoc = set(VIET_TAT) | {m for v in _la(dk) if isinstance(v, str) for m in _MA.findall(v)}
    return [f"{t}: mã {m} không phải mã của lệnh hay mã cùng ngành"
            for t, s in _cac_doan(van) for m in _MA.findall(s) if m not in duoc]


def _kiem_gia_thuyet(van: Mapping, dk: Mapping) -> list[str]:
    s = van.get("theo_doi")
    if isinstance(s, str) and s.strip().startswith(NHAN_GIA_THUYET):
        return []
    return [f"theo_doi không mở đầu bằng \"{NHAN_GIA_THUYET}\""]


def _kiem_do_dai(van: Mapping, dk: Mapping) -> list[str]:
    loi = []
    for t in TRUONG:
        s = van.get(t)
        if not isinstance(s, str) or not s.strip():
            loi.append(f"{t} thiếu hoặc rỗng")
            continue
        n = len(s.split())
        if n > GIOI_HAN_TU[t]:
            loi.append(f"{t} dài {n} từ, trần {GIOI_HAN_TU[t]}")
    return loi


@dataclass(frozen=True)
class Luat:
    ma: str
    dan: str
    kiem: Callable[[Mapping, Mapping], list[str]]


LUAT_VIET: tuple[Luat, ...] = (
    Luat("so-co-nguon",
         "Mọi con số và mọi ngày phải lấy từ dữ kiện (được làm tròn); không tự tính số mới, "
         "không dùng số ví dụ, kể cả trong phần kiến thức. Viết ngày dạng dd/mm/yyyy.",
         _kiem_so),
    Luat("mot-lenh",
         "Một lệnh không chứng minh được gì về agent hay tín hiệu: không viết "
         "\"chứng minh\", \"chắc chắn\", \"luôn luôn\", \"agent sai\" trừ khi đứng sau "
         "\"không\" hoặc \"chưa\"; cụm \"tín hiệu sai\" chỉ dùng khi dữ kiện có cach_goi.",
         _kiem_mot_lenh),
    Luat("khong-khuyen-nghi",
         "Không khuyên mua hay bán: không viết \"nên mua\", \"nên bán\", \"hãy mua\", "
         "\"hãy bán\", \"khuyến nghị\" trừ khi đứng sau \"không\" hoặc \"chưa\".",
         _kiem_khuyen_nghi),
    Luat("ma-co-nguon",
         "Chỉ nhắc mã cổ phiếu của lệnh này và các mã cùng ngành có trong dữ kiện.",
         _kiem_ma),
    Luat("gia-thuyet-dan-nhan",
         f"Trường theo_doi mở đầu đúng bằng \"{NHAN_GIA_THUYET}\".",
         _kiem_gia_thuyet),
    Luat("do-dai",
         "Độ dài: " + "; ".join(f"{t} tối đa {n} từ" for t, n in GIOI_HAN_TU.items())
         + "; không trường nào để trống.",
         _kiem_do_dai),
)


def kiem_dau_ra(van: Mapping[str, Any], du_kien: Mapping) -> list[str]:
    """Mọi vi phạm `"<mã luật>: <chi tiết>"` của bốn trường; rỗng = ĐẠT."""
    return [f"{l.ma}: {v}" for l in LUAT_VIET for v in l.kiem(van, du_kien)]


_DAU_LOI_DAN = (
    "Bạn viết hậu kiểm cho MỘT lệnh ảo đã đóng của một hệ thống giao dịch giấy trên cổ "
    "phiếu Việt Nam. Người đọc là một nhà đầu tư cá nhân đang học từ sổ lệnh. Đoạn văn chỉ "
    "để đọc: không có lệnh thật nào, và đây không phải lời khuyên đầu tư.\n"
    "Dữ kiện là JSON đi kèm, do máy tính sẵn từ nhật ký \"vì sao\" và sổ bài học. Chỉ dùng "
    "dữ kiện ấy. Viết tiếng Việt, giọng giải thích, không tô vẽ.\n\n"
    "Trả về đúng bốn trường:\n"
    "- ke_lai: vì sao vào lệnh (điểm từng agent, lý do, bối cảnh VN-INDEX), vì sao thoát, "
    "lãi/lỗ đến từ phần nào (thị trường, ngành, riêng mã, chi phí), và các cờ gap, cắt lỗ "
    "sát (cờ nào \"chưa đủ dữ liệu\" thì nói đúng như vậy).\n"
    "- khong_chung_minh: điều MỘT lệnh này không chứng minh được.\n"
    "- theo_doi: một giả thuyết đáng theo dõi ở các lệnh sau.\n"
    "- kien_thuc: giải thích ngắn một khái niệm gắn với lệnh này.\n\n"
    "Luật viết — máy kiểm từng luật, vi phạm thì đoạn văn bị bác:\n"
)


def _dung_loi_dan(luat: Sequence[Luat]) -> str:
    return _DAU_LOI_DAN + "".join(f"- {l.dan}\n" for l in luat)


LOI_DAN: str = _dung_loi_dan(LUAT_VIET)


def bam(obj: Any) -> str:
    """sha256 rút gọn của một đối tượng JSON-được — để biết đoạn văn viết theo lời dặn
    nào, từ dữ kiện nào."""
    s = obj if isinstance(obj, str) else json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                                     default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


# ── Dữ kiện gửi đi ───────────────────────────────────────────────────────

_COT_LENH: tuple[str, ...] = (
    "trade_id", "symbol", "signal_date", "entry_date", "entry_price", "stop_loss_ban_dau",
    "rui_ro_pct", "entry_score", "exit_date", "exit_price", "exit_reason",
    "loi_nhuan_rong_pct", "ket_qua_R", "ro_chuan_pct", "alpha_pct", "hau_kiem_may",
)
_KHOA_BAI_HOC: tuple[str, ...] = (
    "ket_qua", "phan", "nguyen_nhan", "cach_goi", "gap", "cat_lo_sat", "nganh",
    "n_ma_nganh", "thieu",
)


def du_kien(dong_nk: Mapping[str, Any], bai_hoc: Mapping[str, Any]) -> dict:
    """Bộ dữ kiện của MỘT lệnh: chỉ số ĐÃ tính bởi nhật ký và sổ bài học, không công
    thức thứ hai (gác AST: hàm này không có phép tính nào)."""
    import nhat_ky_vi_sao
    import paper_metrics
    import so_bai_hoc

    sym = dong_nk.get("symbol")
    return {
        "lenh": {c: dong_nk.get(c) for c in _COT_LENH},
        "chi_tiet": nhat_ky_vi_sao.chi_tiet(dict(dong_nk)),
        "bai_hoc": {k: bai_hoc.get(k) for k in _KHOA_BAI_HOC},
        "ma_cung_nganh": so_bai_hoc.ma_cung_nganh(sym) if sym else [],
        "hang_so": {"n_phien_sau_thoat": so_bai_hoc.N_PHIEN_SAU_THOAT,
                    "chi_phi_vong_pct": paper_metrics.ROUND_TRIP_COST_PCT},
    }


def tham_so_goi(noi_dung: str, model: str = MODEL) -> dict:
    """Toàn bộ tham số của `client.models.generate_content` — MỘT chỗ. JSON đúng bốn
    trường bằng `response_json_schema` (Gemini nhận `additionalProperties`); độ sâu chỉnh
    bằng `thinking_level`; không `temperature` / `top_p` / `top_k`. `model`: `MODEL` hoặc
    `MODEL_DU_PHONG` (BƯỚC 233) — mọi tham số khác giống hệt."""
    return {
        "model": model,
        "contents": noi_dung,
        "config": {
            "system_instruction": LOI_DAN,
            "max_output_tokens": MAX_TOKENS,
            "response_mime_type": "application/json",
            "response_json_schema": SCHEMA_BON_TRUONG,
            "thinking_config": {"thinking_level": EFFORT},
        },
    }


def noi_dung_gui(du_kien: Mapping) -> str:
    """Lượt `user` của lời gọi: dữ kiện JSON (ổn định: `sort_keys`) + một câu yêu cầu."""
    return ("Dữ kiện của lệnh:\n"
            + json.dumps(du_kien, sort_keys=True, ensure_ascii=False, indent=1, default=str)
            + "\n\nViết bốn trường theo lời dặn.")


# ── Tiền ─────────────────────────────────────────────────────────────────

def gia_cao_nhat() -> tuple[float, float]:
    return (max(v for v, _ in GIA_USD_MOI_TRIEU.values()),
            max(r for _, r in GIA_USD_MOI_TRIEU.values()))


def chi_phi_uoc(token_vao: int, token_ra: int) -> float:
    """USD, theo giá CAO NHẤT của bảng: ước dư, không bao giờ ước thiếu."""
    vao, ra = gia_cao_nhat()
    return (token_vao * vao + token_ra * ra) / 1e6


def tran_mot_loi_goi(noi_dung: str) -> float:
    """Trần tiền của một lời gọi, TRƯỚC khi gọi: mỗi token chứa ít nhất một byte, nên số
    byte UTF-8 của lời dặn + nội dung là cận TRÊN của token vào; cộng `MAX_TOKENS` ra."""
    return chi_phi_uoc(len((LOI_DAN + noi_dung).encode("utf-8")), MAX_TOKENS)


def da_tieu_thang(dong_hk: Sequence[Mapping[str, Any]], thang: str) -> float:
    """Tổng `chi_phi_usd_uoc` của các dòng viết trong tháng `thang` ("YYYY-MM", giờ VN)."""
    tong = 0.0
    for d in dong_hk:
        v = d.get("chi_phi_usd_uoc")
        if v is not None and str(d.get("viet_luc"))[:7] == thang:
            tong += float(v)
    return tong


def vuot_tran(da_tieu: float, tran_loi_goi: float) -> bool:
    """Gọi thêm một lời có thể vượt trần tháng không. Đúng bằng trần thì chưa vượt."""
    return da_tieu + tran_loi_goi > TRAN_USD_THANG


# ── Chọn lệnh cần viết ───────────────────────────────────────────────────

def _theo_lenh(dong_hk: Sequence[Mapping[str, Any]]) -> dict[Any, list[Mapping]]:
    ra: dict[Any, list[Mapping]] = {}
    for h in dong_hk:
        ra.setdefault(h.get("trade_id"), []).append(h)
    return ra


def lan_ke(dong_hk: Sequence[Mapping[str, Any]], trade_id: Any) -> int:
    """Số `lan` của lần viết kế tiếp cho lệnh — khoá (`trade_id`, `lan`) không trùng."""
    cu = [int(h["lan"]) for h in _theo_lenh(dong_hk).get(trade_id, []) if h.get("lan")]
    return max(cu, default=0) + 1


def can_viet(dong_nk: Sequence[Mapping[str, Any]],
             dong_hk: Sequence[Mapping[str, Any]]) -> tuple[list[Mapping], list[Mapping]]:
    """(lệnh cần viết, lệnh đã hỏng đủ `SO_LAN_TOI_DA` lần) — theo ngày ra tăng dần.

    Lệnh cần viết = ĐÃ CÓ bài học (`so_bai_hoc.ly_do_thieu_bai_hoc` là None: nửa ĐÓNG
    và rổ chuẩn — đúng tiêu chí "có bài học" của chuông) và chưa có dòng `DAT`.
    """
    import so_bai_hoc

    theo = _theo_lenh(dong_hk)
    can, het = [], []
    for d in dong_nk:
        if d.get("trade_id") is None or so_bai_hoc.ly_do_thieu_bai_hoc(d) is not None:
            continue
        hs = theo.get(d["trade_id"], [])
        if any(h.get("trang_thai") == TT_DAT for h in hs):
            continue
        (het if len(hs) >= SO_LAN_TOI_DA else can).append(d)

    def khoa(d):
        return str(d.get("exit_date"))[:10], d.get("trade_id")

    return sorted(can, key=khoa), sorted(het, key=khoa)


# ── Phản hồi API -> một dòng của tab ────────────────────────────────────

def _so_nguyen(o: Any, ten: str) -> int:
    v = getattr(o, ten, None)
    return int(v) if v else 0


def _ten(x: Any) -> Optional[str]:
    """Enum của SDK (`FinishReason.STOP`) hay chuỗi -> tên trần ("STOP")."""
    return None if x is None else str(getattr(x, "value", x))


def tach_phan_hoi(resp: Any) -> dict:
    """Phản hồi `generate_content` -> dict thuần. Chữ = các phần `text` của ứng viên đầu,
    BỎ phần suy nghĩ (`thought` True). Token ra = token trả lời + token suy nghĩ (giá ra
    của Google gồm cả suy nghĩ). Lời nhắc bị chặn (không có ứng viên, có
    `prompt_feedback.block_reason`) -> `stop_reason` "BLOCKED:<lý do>"."""
    ung = (getattr(resp, "candidates", None) or [None])[0]
    phan = getattr(getattr(ung, "content", None), "parts", None) or []
    text = "".join(getattr(p, "text", None) or "" for p in phan if not getattr(p, "thought", None))
    u = getattr(resp, "usage_metadata", None)
    ra = _so_nguyen(u, "candidates_token_count") + _so_nguyen(u, "thoughts_token_count")
    stop, danh_muc = _ten(getattr(ung, "finish_reason", None)), None
    chan = _ten(getattr(getattr(resp, "prompt_feedback", None), "block_reason", None))
    if ung is None and chan:
        stop, danh_muc = f"BLOCKED:{chan}", chan
    elif stop in KET_THUC_TU_CHOI:
        danh_muc = stop
    return {"stop_reason": stop, "model": getattr(resp, "model_version", None), "text": text,
            "token_vao": _so_nguyen(u, "prompt_token_count"), "token_ra": ra,
            "danh_muc": danh_muc}


def doc_json(text: str) -> Optional[dict]:
    """Chữ phản hồi -> dict bốn trường, hoặc None nếu không phải JSON đúng hình dạng."""
    try:
        o = json.loads(text)
    except (TypeError, ValueError):
        return None
    if not isinstance(o, dict) or set(o) != set(TRUONG):
        return None
    return o


def ket_qua_mot_lenh(dong_nk: Mapping[str, Any], lan: int, resp: Any,
                     du_kien_lenh: Mapping, viet_luc: str, model: str = MODEL) -> dict:
    """Một phản hồi API -> MỘT dòng tab `hau_kiem` (theo `COT_HAU_KIEM`).

    Bị chặn (`KET_THUC_TU_CHOI`, lời nhắc bị chặn) -> TU_CHOI · `MAX_TOKENS` -> CAT_CUT ·
    JSON hỏng, kết thúc khác `STOP` hoặc vi phạm luật -> BI_BAC (văn vẫn giữ làm bằng
    chứng; app không hiện) · còn lại -> DAT. Mọi phản hồi đều thành một dòng, để tổng
    tiền cộng từ tab luôn đủ. `model`: model ĐÃ GỌI (chính hoặc dự phòng) -> `model_yeu_cau`.
    """
    t = tach_phan_hoi(resp)
    van = doc_json(t["text"]) if t["stop_reason"] == KET_THUC_XONG else None
    vi_pham = kiem_dau_ra(van, du_kien_lenh) if van is not None else []
    if t["danh_muc"] is not None:
        tt, ly_do = TT_TU_CHOI, f"bị từ chối (danh mục: {t['danh_muc']})"
    elif t["stop_reason"] == KET_THUC_CAT:
        tt, ly_do = TT_CAT_CUT, f"chạm max_output_tokens {MAX_TOKENS}"
    elif van is None:
        tt, ly_do = TT_BI_BAC, (f"stop_reason {t['stop_reason']}: phản hồi không phải "
                                "JSON đúng bốn trường")
    elif vi_pham:
        tt, ly_do = TT_BI_BAC, " · ".join(vi_pham)
    else:
        tt, ly_do = TT_DAT, None
    dong = {
        "trade_id": dong_nk.get("trade_id"), "lan": lan, "symbol": dong_nk.get("symbol"),
        "exit_date": str(dong_nk.get("exit_date"))[:10], "trang_thai": tt,
        "ly_do_bac": ly_do, **{f: (van or {}).get(f) for f in TRUONG},
        "model_yeu_cau": model, "model_phuc_vu": t["model"], "effort": EFFORT,
        "bam_loi_dan": bam(LOI_DAN), "bam_du_kien": bam(du_kien_lenh),
        "token_vao": t["token_vao"], "token_ra": t["token_ra"],
        "chi_phi_usd_uoc": round(chi_phi_uoc(t["token_vao"], t["token_ra"]), 6),
        "stop_reason": t["stop_reason"], "viet_luc": viet_luc,
    }
    return {c: dong[c] for c in COT_HAU_KIEM}


# ── Hiện và đo ───────────────────────────────────────────────────────────

def ban_moi_nhat(dong_hk: Sequence[Mapping[str, Any]], trade_id: Any) -> Optional[Mapping]:
    """Dòng `DAT` có `lan` lớn nhất của một lệnh — thứ app và bản tin hiện. Dòng bị bác,
    bị từ chối hay bị cắt không bao giờ được hiện."""
    dat = [h for h in _theo_lenh(dong_hk).get(trade_id, []) if h.get("trang_thai") == TT_DAT]
    return max(dat, key=lambda h: int(h.get("lan") or 0), default=None)


def do_phu_hau_kiem_loi(lenh_dong: Sequence[Mapping[str, Any]],
                        dong_hk: Sequence[Mapping[str, Any]], hom_nay: Any, *,
                        bat_dau: Optional[str], lich: Any = None) -> dict:
    """Vế "có lời" của tiêu chí B: lệnh đóng có dòng `DAT` trong vòng một phiên.

    Cùng hình dạng `so_bai_hoc.do_phu_bai_hoc`, cùng hạn (HẾT `phien_ke_tiep` sau ngày
    đóng). `bat_dau` None -> `TT_CHUA_BAT`: B1 chưa bật, chưa đo gì. Lệnh đóng TRƯỚC
    `bat_dau` vào nhóm `truoc_b1`: không tính, không điền bù.
    """
    import so_bai_hoc

    hom = str(hom_nay)[:10]
    nhom: dict[str, list[dict]] = {k: [] for k in (
        "co", "trong_han", "vi_pham", "truoc_b1", "khong_kiem_duoc")}
    theo = _theo_lenh(dong_hk)
    for lenh in lenh_dong:
        ra = str(lenh.get("exit_date") or "")[:10]
        mot = {"trade_id": lenh.get("trade_id"), "symbol": lenh.get("symbol"),
               "exit_date": ra or None}
        if bat_dau is None or (ra and ra < bat_dau):
            nhom["truoc_b1"].append(mot)
            continue
        if any(h.get("trang_thai") == TT_DAT for h in theo.get(lenh.get("trade_id"), [])):
            nhom["co"].append(mot)
            continue
        if not ra:
            nhom["khong_kiem_duoc"].append({**mot, "ly_do": "sổ lệnh thiếu ngày đóng"})
            continue
        han = so_bai_hoc.phien_ke_tiep(ra, lich)
        if han is None:
            nhom["khong_kiem_duoc"].append(
                {**mot, "ly_do": f"lịch phiên không phủ tới hạn của lệnh đóng {ra}"})
        elif hom <= han:
            nhom["trong_han"].append({**mot, "han": han})
        else:
            nhom["vi_pham"].append({**mot, "han": han})
    for ds in nhom.values():
        ds.sort(key=lambda m: (str(m.get("exit_date") or ""), str(m.get("trade_id"))))
    n = {k: len(v) for k, v in nhom.items()}
    if bat_dau is None:
        tt = TT_CHUA_BAT
    else:
        tt = (so_bai_hoc.TT_VI_PHAM if n["vi_pham"] else
              so_bai_hoc.TT_CHUA_KIEM_DUOC if n["khong_kiem_duoc"] else so_bai_hoc.TT_XANH)
    return {**nhom, "trang_thai": tt, "bat_dau": bat_dau, "hom_nay": hom,
            **{f"n_{k}": v for k, v in n.items()}}
