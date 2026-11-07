"""Phần THUẦN của đường giao bản tin cuối ngày qua Telegram (BƯỚC 258, mốc B2 / tiêu chí T3).

Repo CÔNG KHAI nên một GitHub Issue không phải kênh riêng tư; người dùng chọn Telegram
(06/11/2026, *"Telegram (Recommended)"*). Module này chỉ chứa hàm thuần — không mạng, không
đĩa, không đồng hồ, không nhập `ban_tin` hay bất cứ thứ gì chạm sổ. Phần đọc sổ, gọi HTTP và ghi
dấu nằm ở `tools/gui_ban_tin_telegram.py`.

BỐN VIỆC
────────
1. `markdown_sang_van_ban` — bản tin là markdown (app dùng chung); gửi Telegram KHÔNG đặt
   `parse_mode`, nên ký tự `*` `_` trong lý do của sổ không bao giờ làm API từ chối cả tin.
2. `chia_tin` — mỗi tin ≤ `GIOI_HAN_KY_TU` (4096), cắt ở RANH GIỚI DÒNG, đo bằng đơn vị UTF-16
   (emoji ngoài BMP chiếm 2; cùng bài học "nút Gửi khoá từ 3.901" của sổ tay).
3. `chon_ngay` — NGÀY của bản tin lấy từ SỔ (ngày tín hiệu lớn nhất), không từ đồng hồ: lượt quét
   bị GitHub trễ 4–10 giờ có thể chạy qua nửa đêm giờ VN. Chặn ngày không phải phiên (lịch công
   bố), ngày ở tương lai, và ngày quá cũ (sổ không thêm gì mới).
4. `khoa_da_gui` — khoá chống gửi lặp: MỘT bản tin mỗi ngày phiên, bất kể bao nhiêu lượt quét.
"""
from __future__ import annotations

import datetime as _dt
import re
from typing import NamedTuple, Optional

import lich_giao_dich

#: Giới hạn của `sendMessage` (đơn vị UTF-16 sau khi phân tích thực thể; ta không dùng thực thể).
GIOI_HAN_KY_TU = 4096

#: Chỗ chừa cho tiền tố "(i/n) " khi bản tin phải tách thành nhiều tin.
CHO_CHUA_TIEN_TO = 16

#: Ngày bản tin cũ hơn hôm nay quá số ngày lịch này thì KHÔNG gửi: sổ không có gì mới, gửi là
#: gửi lại một ngày cũ. 3 = thứ Sáu → sáng thứ Hai vẫn còn hạn (cuối tuần 2 ngày + lượt quét
#: trễ qua nửa đêm), thứ Ba thì hết.
TOI_DA_TUOI_NGAY = 3

BIEN_TOKEN = "TELEGRAM_BOT_TOKEN"
BIEN_CHAT_ID = "TELEGRAM_CHAT_ID"

TIEN_TO_KHOA = "ban-tin-telegram-da-gui-"

_RE_TIEU_DE = re.compile(r"^\s{0,3}#{1,6}\s+")
_RE_GACH_DAU = re.compile(r"^(\s*)[-*]\s+")
_RE_NGANG = re.compile(r"^\s*-{3,}\s*$")
# `_nghiêng_` chỉ khi hai đầu KHÔNG dính chữ: "DA_CO_VI_THE" không bị cạo.
_RE_NGHIENG = re.compile(r"(?<![\w])_([^_\n]+?)_(?![\w])")
DONG_NGANG = "──────────"


class QuyetNgay(NamedTuple):
    """Kết quả `chon_ngay`. `ngay` là None khi KHÔNG gửi; `ly_do` luôn có chữ."""
    ngay: Optional[str]
    ly_do: str
    canh_bao: Optional[str] = None


def do_dai(s: str) -> int:
    """Độ dài theo đơn vị UTF-16 — thước của Telegram."""
    return len(s.encode("utf-16-le")) // 2


def markdown_sang_van_ban(md: str) -> str:
    """Markdown của `ban_tin.ban_tin_markdown` -> văn bản thuần, giữ nguyên chữ."""
    ra = []
    for dong in md.split("\n"):
        if _RE_NGANG.match(dong):
            ra.append(DONG_NGANG)
            continue
        dong = _RE_TIEU_DE.sub("", dong)
        dong = _RE_GACH_DAU.sub(lambda m: m.group(1) + "• ", dong)
        dong = dong.replace("**", "").replace("`", "")
        dong = _RE_NGHIENG.sub(r"\1", dong)
        ra.append(dong.rstrip())
    return "\n".join(ra).strip("\n")


def _cat_dong_dai(dong: str, gioi_han: int) -> list[str]:
    """Một dòng dài hơn giới hạn: cắt ở dấu cách gần cuối nhất, không có thì cắt cứng."""
    manh, hien = [], dong
    while do_dai(hien) > gioi_han:
        dau = 0
        for i, ch in enumerate(hien):
            if do_dai(hien[:i + 1]) > gioi_han:
                break
            dau = i + 1
        cat = hien.rfind(" ", 0, dau)
        cat = dau if cat <= 0 else cat
        manh.append(hien[:cat].rstrip())
        hien = hien[cat:].lstrip()
    manh.append(hien)
    return manh


def chia_tin(van_ban: str, gioi_han: int = GIOI_HAN_KY_TU) -> list[str]:
    """Tách thành các tin ≤ `gioi_han`, cắt ở ranh giới dòng. Nhiều hơn một tin thì mỗi tin
    mang tiền tố "(i/n) ". Rỗng -> danh sách rỗng (người gọi phải coi đó là lỗi, không gửi)."""
    van_ban = van_ban.strip("\n")
    if not van_ban.strip():
        return []
    if do_dai(van_ban) <= gioi_han:
        return [van_ban]
    tran = gioi_han - CHO_CHUA_TIEN_TO
    cum: list[list[str]] = [[]]
    dai = 0
    for dong in van_ban.split("\n"):
        for manh in _cat_dong_dai(dong, tran):
            them = do_dai(manh) + (1 if cum[-1] else 0)
            if cum[-1] and dai + them > tran:
                cum.append([])
                dai = 0
                them = do_dai(manh)
            cum[-1].append(manh)
            dai += them
    tin = ["\n".join(c).strip("\n") for c in cum]
    tin = [t for t in tin if t.strip()]
    n = len(tin)
    return [f"({i}/{n}) {t}" for i, t in enumerate(tin, 1)]


def chon_ngay(ngay_gan_nhat: Optional[str], hom_nay: str) -> QuyetNgay:
    """Ngày bản tin nên gửi, hoặc lý do KHÔNG gửi. `hom_nay` là ngày giờ VN do người gọi đưa.

    Có quyết định cho ngày D trong sổ nghĩa là lượt quét đã sinh dữ liệu ngày D. Lịch ngoài phạm
    vi bảng (`co_phien` = None) thì vẫn gửi nhưng kèm cảnh báo — có quyết định thì chắc chắn có
    nến; chặn là im lặng cả năm sau khi bảng lịch hết hạn.
    """
    if not ngay_gan_nhat:
        return QuyetNgay(None, "sổ không có quyết định nào — chưa quét, hoặc chưa kéo được sổ")
    d = str(ngay_gan_nhat)[:10]
    try:
        ngay_d = _dt.date.fromisoformat(d)
        ngay_nay = _dt.date.fromisoformat(str(hom_nay)[:10])
    except ValueError:
        return QuyetNgay(None, f"ngày không đọc được: {ngay_gan_nhat!r} / {hom_nay!r}")
    co = lich_giao_dich.co_phien(d)
    if co is False:
        return QuyetNgay(None, f"{d} không phải phiên giao dịch theo lịch công bố")
    tuoi = (ngay_nay - ngay_d).days
    if tuoi < 0:
        return QuyetNgay(None, f"ngày bản tin {d} nằm SAU hôm nay {ngay_nay.isoformat()}")
    if tuoi > TOI_DA_TUOI_NGAY:
        return QuyetNgay(None, f"ngày mới nhất trong sổ là {d}, cũ {tuoi} ngày so với "
                               f"{ngay_nay.isoformat()} (hạn {TOI_DA_TUOI_NGAY}): chưa có phiên mới")
    canh_bao = None
    if co is None:
        canh_bao = (f"lịch giao dịch chỉ phủ {lich_giao_dich.PHU_TU} → {lich_giao_dich.PHU_TOI}; "
                    f"{d} nằm ngoài nên chưa kiểm được đây có phải phiên — vẫn gửi vì sổ có "
                    f"quyết định ngày ấy. Cập nhật `lich_giao_dich.NGAY_NGHI`.")
    return QuyetNgay(d, "", canh_bao)


def khoa_da_gui(ngay: str) -> str:
    """Khoá dấu "đã gửi" của ngày `ngay` (workflow dùng làm khoá cache)."""
    _dt.date.fromisoformat(str(ngay)[:10])
    return f"{TIEN_TO_KHOA}{str(ngay)[:10]}"


def thieu_secret(env: dict) -> list[str]:
    """Tên biến môi trường Telegram còn thiếu hoặc rỗng (chỉ khoảng trắng cũng là rỗng)."""
    return [ten for ten in (BIEN_TOKEN, BIEN_CHAT_ID) if not (env.get(ten) or "").strip()]


def che_bi_mat(chuoi: str, *bi_mat: str) -> str:
    """Thay mọi lần xuất hiện của các chuỗi bí mật bằng `***` — dùng trước khi in lỗi."""
    for b in bi_mat:
        if b and b.strip():
            chuoi = chuoi.replace(b.strip(), "***")
    return chuoi
