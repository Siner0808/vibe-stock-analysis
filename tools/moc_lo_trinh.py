"""Gác "MỖI BƯỚC PHỤC VỤ MỘT MỐC" — đọc `docs/LO-TRINH.md` và `docs/STATE.md`.

VÌ SAO CÓ FILE NÀY (BƯỚC 164, 08/10/2026)
──────────────────────────────────────────
Lộ trình `docs/LO-TRINH.md` được người dùng duyệt ngày 08/10/2026 (câu trả lời
nguyên văn: *"duyệt"*). Chẩn đoán đi kèm: 30 ngày trước đó chỉ 6,3% số dòng
thêm vào repo là mã sản phẩm (lệnh đo ở LO-TRINH.md) — việc quy trình lấy phần
của sản phẩm mà không ai nói ra nó đang làm vậy. Cơ chế "khai ra" chống nó:
từ `TU_BUOC` trở đi, mục `## BƯỚC n` trong `docs/STATE.md` phải mang MỘT dòng

    **Mốc:** A3                      (mã có thật trong docs/LO-TRINH.md)
    **Mốc:** quy-trinh — <lý do>     (việc quy trình thuần; lý do cụ thể)

Cùng triết lý `# bia-ok:` và `khong_soat_vi`: không cấm quy trình, buộc NÓI RA.
Máy đọc được: dòng có mặt, mã có thật. Máy KHÔNG đọc được: mã khai có đúng với
việc đã làm không — phần ấy là kỷ luật, và lượt soát định kỳ nhìn vào.

Hai bên gọi cùng MỘT bản cài đặt: `tests/test_moc_lo_trinh.py` (gác) và bất kỳ
công cụ nào sau này. Đọc bằng TIÊU ĐỀ cấp hai (`^## BƯỚC n —`), không bằng chữ
"BƯỚC" xuất hiện trong văn xuôi — cùng quy ước `tools/soat_loi_khai_cu.py`.

Giai đoạn A4 của lộ trình dự định TÁCH `docs/STATE.md` theo tháng: khi ấy
`TEP_STATE` (và `tools/buoc_cham_luat.py`) phải đổi theo, nếu không gác này đọc
một tệp không còn chứa BƯỚC mới — và `tests/test_moc_lo_trinh.py` có một ca
đòi quần thể KHÁC RỖNG nên nó sẽ đỏ, không im.
"""
from __future__ import annotations

import re
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
LO_TRINH = GOC / "docs" / "LO-TRINH.md"
TEP_STATE = ("docs/STATE.md",)

#: BƯỚC đầu tiên phải mang dòng Mốc. Người dùng chốt 08/10/2026 (khung lộ
#: trình *"duyệt"*, *"Bắt đầu giai đoạn A: Làm ngay"*); BƯỚC 164 là BƯỚC đầu.
#: Mọi BƯỚC trước đó là bản ghi của việc đã xảy ra — sửa chúng là viết lại lịch sử.
TU_BUOC = 164

#: Mã mốc được ĐỊNH NGHĨA bằng một mục danh sách mở đầu `- **A1**` trong
#: LO-TRINH.md. Một mã chỉ được nhắc trong văn xuôi KHÔNG phải mã định nghĩa.
RE_MA_DINH_NGHIA = re.compile(r"^- \*\*([A-Z]\d{1,2})\*\*", re.M)
RE_TIEU_DE_BUOC = re.compile(r"^##\s+BƯỚC\s+(\d+)\s*—")
RE_DONG_MOC = re.compile(r"^\*\*Mốc:\*\*\s*(.*?)\s*$")
RE_MA = re.compile(r"[A-Z]\d{1,2}")
QUY_TRINH = "quy-trinh"
#: Lý do dưới ngần này ký tự hay nằm trong danh sách này là câu thần chú —
#: cùng ngưỡng `test_LY_DO_KHONG_SOAT_khong_duoc_rong_va_khong_duoc_chung_chung`.
LY_DO_TOI_THIEU = 25
LY_DO_MO_HO = ("khong can", "không cần", "khong quan trong", "n/a", "-",
               "quy trinh", "quy trình", "viec quy trinh", "việc quy trình")


def ma_hop_le(van_lo_trinh: str) -> set[str]:
    """Mọi mã mốc LO-TRINH.md định nghĩa. HÀM THUẦN."""
    return set(RE_MA_DINH_NGHIA.findall(van_lo_trinh))


def tach_muc_buoc(van_state: str, tu: int = TU_BUOC) -> dict[int, list[str]]:
    """{n: các dòng của mục `## BƯỚC n`} với n >= `tu`. HÀM THUẦN.

    Mục kết thúc ở tiêu đề cấp hai kế tiếp BẤT KỲ (`## ĐO …` cũng cắt). Dòng
    trong khối rào ``` bị bỏ — một ví dụ `**Mốc:**` dán trong khối mã không
    phải lời khai của BƯỚC.
    """
    ra: dict[int, list[str]] = {}
    hien: int | None = None
    rao = False
    for d in van_state.splitlines():
        if d.lstrip().startswith("```"):
            rao = not rao
            continue
        if rao:
            continue
        if d.startswith("## "):
            m = RE_TIEU_DE_BUOC.match(d)
            hien = int(m.group(1)) if m and int(m.group(1)) >= tu else None
            if hien is not None:
                ra.setdefault(hien, [])
            continue
        if hien is not None:
            ra[hien].append(d)
    return ra


def loi_moc(dong_muc: list[str], hop_le: set[str]) -> list[str]:
    """Lỗi của MỘT mục BƯỚC (rỗng = sạch). HÀM THUẦN — chỗ phán duy nhất."""
    cac = [m.group(1) for d in dong_muc if (m := RE_DONG_MOC.match(d))]
    if not cac:
        return ["thieu dong `**Mốc:** <ma>` (hoac `**Mốc:** quy-trinh — <ly do>`)"]
    if len(cac) > 1:
        return [f"co {len(cac)} dong `**Mốc:**`, phai dung MOT"]
    noi = cac[0]
    if not noi:
        return ["dong `**Mốc:**` rong"]
    dau, _, duoi = noi.partition(" — ")
    if dau.strip().lower() == QUY_TRINH:
        ly_do = duoi.strip()
        if len(ly_do) < LY_DO_TOI_THIEU or ly_do.lower() in LY_DO_MO_HO:
            return [f"`**Mốc:** quy-trinh` thieu ly do cu the (>= {LY_DO_TOI_THIEU} "
                    f"ky tu, khong phai cau chung chung): {ly_do!r}"]
        return []
    ma = [t for t in re.split(r"[\s,;·+/]+", dau.strip()) if t]
    if not ma:
        return ["dong `**Mốc:**` khong co ma nao"]
    la = [t for t in ma if not RE_MA.fullmatch(t)]
    if la:
        return [f"khong phai ma moc: {la} (mong doi dang A1, B2, H1…, hoac quy-trinh)"]
    chua_co = sorted(t for t in ma if t not in hop_le)
    if chua_co:
        return [f"ma moc {chua_co} KHONG co trong docs/LO-TRINH.md "
                f"(ma hop le: {sorted(hop_le)})"]
    return []


def vi_pham(van_state: str, van_lo_trinh: str, tu: int = TU_BUOC) -> list[str]:
    """Mọi lỗi Mốc của các mục BƯỚC n >= `tu`: 'BƯỚC n: <lỗi>'. HÀM THUẦN."""
    hop_le = ma_hop_le(van_lo_trinh)
    ra: list[str] = []
    for n, dong in sorted(tach_muc_buoc(van_state, tu).items()):
        ra += [f"BƯỚC {n}: {e}" for e in loi_moc(dong, hop_le)]
    return ra


def doc_van_state(goc: Path = GOC) -> str:
    return "\n".join((goc / t).read_text(encoding="utf-8") for t in TEP_STATE)
