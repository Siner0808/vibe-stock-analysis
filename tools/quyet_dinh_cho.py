"""Bộ đọc và bộ phán KHUÔN của `docs/QUYET-DINH-CHO.md` — hàng đợi quyết định chờ người dùng.

VÌ SAO CÓ FILE NÀY (BƯỚC 165, 08/10/2026, mốc A5 của `docs/LO-TRINH.md`)
────────────────────────────────────────────────────────────────────────
Các câu "chờ người dùng / cần người quyết" nằm rải rác ở `docs/HANDOFF.md`,
`docs/STATE.md` và `CLAUDE.md`, và có câu sống 15 ngày mà không ai kiểm xem nó
còn mở không (đo 08/10/2026: thư mục `luu_do18` mà HANDOFF còn hỏi "giữ hay xoá"
đã không còn trên đĩa). Sổ này gom chúng vào MỘT nơi để leader trình người dùng
trong một phiên quyết định.

Khuôn là thứ máy kiểm được; NỘI DUNG (câu hỏi có đúng không, đề xuất có hay
không) là việc của người đọc. Khuôn đòi:

  * mục `## Qn — <câu hỏi>`, mã liền nhau từ Q1;
  * `**Trạng thái:**` là MỘT trong `chờ` · `đã quyết` · `hết hiệu lực`;
  * mục `chờ`: NGUỒN (mỗi `tệp:dòng` kèm một trích `«…»` còn nguyên văn trong
    tệp), ít nhất hai LỰA CHỌN `- (a) …`, một ĐỀ XUẤT, dữ kiện kèm lệnh và ngày;
  * mục `đã quyết`: câu trả lời NGUYÊN VĂN `*"…"*` kèm ngày;
  * mục `hết hiệu lực`: BẰNG CHỨNG gồm lệnh (trong dấu huyền) và ngày.

Nó không phán được gì về việc trích có ĐÚNG NGHĨA hay không: một trích còn
nguyên văn vẫn có thể bị hiểu sai. Đó là kỷ luật của người viết sổ.

Dùng:  ./.venv/Scripts/python.exe tools/quyet_dinh_cho.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
TEP = GOC / "docs" / "QUYET-DINH-CHO.md"
HANDOFF = GOC / "docs" / "HANDOFF.md"

TRANG_THAI = ("chờ", "đã quyết", "hết hiệu lực")
CHO, DA_QUYET, HET_HIEU_LUC = TRANG_THAI

#: Không đòi dấu `—`: `## Q10 - tên` (gạch nối thường) cũng là một mục, và một
#: bộ đọc chỉ nhận `—` sẽ để nó lọt khỏi khuôn (cùng bài học đột biến M14 của
#: `tools/moc_lo_trinh.py`).
RE_TIEU_DE = re.compile(r"^## (Q\d+)\s+[—–-]\s+(.*?)\s*$")
RE_TRUONG = re.compile(r"^\*\*([^*]+?):\*\*\s*(.*)$")
RE_LUA_CHON = re.compile(r"^\s*- \(([a-z])\)\s+\S", re.M)
RE_TEP_DONG = re.compile(r"([\w./-]+\.(?:md|py|json|yml|toml)):(\d+)")
RE_NGAY = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
RE_LENH = re.compile(r"`[^`\n]+`")
RE_TRA_LOI = re.compile(r'\*"([^"]{2,})"\*')

#: Nhãn trường (đúng như viết trong sổ) -> khoá nội bộ.
NHAN_TRANG_THAI = "Trạng thái"
NHAN_NGUON = "Nguồn"
NHAN_ANH_HUONG = "Ảnh hưởng"
NHAN_LUA_CHON = "Lựa chọn"
NHAN_DE_XUAT = "Đề xuất của leader"
NHAN_DU_KIEN = "Dữ kiện đã kiểm"
NHAN_TRA_LOI = "Trả lời nguyên văn"
NHAN_BANG_CHUNG = "Bằng chứng"

#: Trần để "câu hỏi một dòng" không phình thành đoạn văn.
TIEU_DE_TOI_DA = 220
TIEU_DE_TOI_THIEU = 20


class Muc:
    """Một mục Q của sổ. Dữ liệu thuần, không logic."""

    def __init__(self, ma: str, tieu_de: str):
        self.ma = ma
        self.tieu_de = tieu_de
        self.truong: dict[str, str] = {}   # nhãn (bỏ phần trong ngoặc) -> nội dung

    def _khoa(self, nhan: str) -> str:
        """Nhãn ĐẦY ĐỦ của trường: đúng nhãn, hoặc nhãn + ` (ghi chú / ngày)`.

        Không khớp tiền tố trần: `Nguồn gốc` không được đọc là `Nguồn`.
        """
        for k in self.truong:
            if k == nhan or k.startswith(nhan + " ("):
                return k
        return ""

    def lay(self, nhan: str) -> str:
        """Nội dung trường theo nhãn, khớp theo TIỀN TỐ (nhãn có thể kèm ngoặc)."""
        return self.truong.get(self._khoa(nhan), "")

    def truong_nhan(self, nhan: str) -> str:
        """Chính nhãn đầy ĐỦ — để đọc phần trong ngoặc (ngày, chữ ĐỀ XUẤT)."""
        return self._khoa(nhan)

    @property
    def trang_thai(self) -> str:
        return self.lay(NHAN_TRANG_THAI).strip()


def doc_muc(van: str) -> list[Muc]:
    """Tách sổ thành các mục Q. HÀM THUẦN.

    Một trường là dòng `**Nhãn:** nội dung`; các dòng sau (kể cả `- (a) …`) thuộc
    trường ấy cho tới trường kế hoặc tiêu đề kế. Dòng trong khối rào ``` bị bỏ.
    Mục kết thúc ở tiêu đề cấp hai BẤT KỲ (nên mục "Đã quét và loại" không dính Q9).
    """
    ra: list[Muc] = []
    hien: Muc | None = None
    nhan: str | None = None
    rao = False
    for d in van.splitlines():
        if d.lstrip().startswith("```"):
            rao = not rao
            continue
        if rao:
            continue
        if d.startswith("## "):
            m = RE_TIEU_DE.match(d)
            hien = Muc(m.group(1), m.group(2)) if m else None
            nhan = None
            if hien is not None:
                ra.append(hien)
            continue
        if hien is None:
            continue
        t = RE_TRUONG.match(d)
        if t:
            nhan = t.group(1).strip()
            hien.truong[nhan] = t.group(2)
        elif nhan is not None and d.strip():
            hien.truong[nhan] += "\n" + d
    return ra


def _doc_tep(goc: Path, duong: str) -> list[str] | None:
    p = goc / duong
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8").splitlines()


def loi_nguon(nguon: str, goc: Path = GOC) -> list[str]:
    """Mỗi `tệp:dòng` phải có tệp, dòng trong độ dài tệp, và một trích `«…»`
    ngay sau còn NGUYÊN VĂN ở đâu đó trong tệp. HÀM THUẦN theo (nguon, goc).

    Trích phải còn trong tệp chứ không cần ở đúng dòng: số dòng trôi khi tệp bị
    thêm dòng phía trên, còn trích đổi nghĩa thì không trôi.
    """
    loi: list[str] = []
    cac = list(RE_TEP_DONG.finditer(nguon))
    if not cac and not re.search(r"BƯỚC\s+\d+", nguon):
        return ["NGUỒN rỗng: cần `tệp:dòng «trích»` hoặc một BƯỚC cụ thể"]
    for m in cac:
        duong, dong = m.group(1), int(m.group(2))
        dong_tep = _doc_tep(goc, duong)
        if dong_tep is None:
            loi.append(f"nguồn trỏ tệp không tồn tại: {duong}")
            continue
        if not 1 <= dong <= len(dong_tep):
            loi.append(f"{duong}:{dong} vượt độ dài tệp ({len(dong_tep)} dòng)")
            continue
        sau = nguon[m.end():].lstrip()
        t = re.match(r"«([^»]+)»", sau)
        if not t:
            loi.append(f"{duong}:{dong} thiếu trích «…» ngay sau")
            continue
        if t.group(1) not in "\n".join(dong_tep):
            loi.append(f"{duong}:{dong} trích «{t.group(1)}» KHÔNG còn nguyên văn trong tệp")
    return loi


def loi_muc(m: Muc, goc: Path = GOC) -> list[str]:
    """Lỗi khuôn của MỘT mục (rỗng = sạch). HÀM THUẦN — chỗ phán duy nhất."""
    loi: list[str] = []
    tt = m.trang_thai
    if not TIEU_DE_TOI_THIEU <= len(m.tieu_de) <= TIEU_DE_TOI_DA:
        loi.append(f"câu hỏi dài {len(m.tieu_de)} ký tự, ngoài [{TIEU_DE_TOI_THIEU}; {TIEU_DE_TOI_DA}]")
    if tt not in TRANG_THAI:
        return loi + [f"trạng thái {tt!r} không thuộc {list(TRANG_THAI)}"]

    du_kien = m.lay(NHAN_DU_KIEN)
    if not RE_LENH.search(du_kien):
        loi.append("`Dữ kiện đã kiểm` không có lệnh nào trong dấu huyền (Quy tắc 2)")
    if not RE_NGAY.search(m.truong_nhan(NHAN_DU_KIEN) + " " + du_kien
                          + " " + m.lay(NHAN_BANG_CHUNG)):
        loi.append("`Dữ kiện đã kiểm` không ghi ngày kiểm dạng dd/mm/yyyy")
    if len(m.lay(NHAN_ANH_HUONG).strip()) < 30:
        loi.append("`Ảnh hưởng` rỗng hoặc quá ngắn (<30 ký tự)")

    if tt == CHO:
        loi += loi_nguon(m.lay(NHAN_NGUON), goc)
        cac_chon = RE_LUA_CHON.findall(m.lay(NHAN_LUA_CHON))
        if len(cac_chon) < 2:
            loi.append(f"mục `chờ` cần >= 2 lựa chọn `- (a) …`, có {len(cac_chon)}")
        elif cac_chon != [chr(ord("a") + i) for i in range(len(cac_chon))]:
            loi.append(f"lựa chọn phải là a, b, c… liền nhau, có {cac_chon}")
        de_xuat = m.lay(NHAN_DE_XUAT)
        if "ĐỀ XUẤT" not in m.truong_nhan(NHAN_DE_XUAT) or len(de_xuat.strip()) < 20:
            loi.append("mục `chờ` cần `Đề xuất của leader (ĐỀ XUẤT …)` có nội dung")
    elif tt == DA_QUYET:
        tl = m.lay(NHAN_TRA_LOI)
        if not RE_TRA_LOI.search(tl):
            loi.append('mục `đã quyết` cần `Trả lời nguyên văn` dạng *"…"* (>= 2 ký tự)')
        if not RE_NGAY.search(m.truong_nhan(NHAN_TRA_LOI) + " " + tl):
            loi.append("mục `đã quyết` cần ngày dd/mm/yyyy của câu trả lời")
        loi += loi_nguon(m.lay(NHAN_NGUON), goc)
    else:  # hết hiệu lực
        bc = m.lay(NHAN_BANG_CHUNG)
        if not RE_LENH.search(bc):
            loi.append("mục `hết hiệu lực` cần `Bằng chứng` có lệnh trong dấu huyền")
        if not RE_NGAY.search(m.truong_nhan(NHAN_BANG_CHUNG) + " " + bc):
            loi.append("mục `hết hiệu lực` cần ngày chạy lệnh dạng dd/mm/yyyy")
        loi += loi_nguon(m.lay(NHAN_NGUON), goc)
    return loi


def loi_so(muc: list[Muc], goc: Path = GOC) -> list[str]:
    """Lỗi của CẢ sổ: quần thể khác rỗng, mã liền nhau không trùng, rồi từng mục."""
    if not muc:
        return ["sổ không có mục Q nào (quần thể rỗng — đọc hụt hoặc tiêu đề sai)"]
    loi: list[str] = []
    so = [int(m.ma[1:]) for m in muc]
    if len(set(so)) != len(so):
        loi.append(f"mã Q trùng: {[m.ma for m in muc]}")
    if sorted(so) != list(range(1, len(so) + 1)):
        loi.append(f"mã Q phải liền nhau từ Q1 (mục không bị xoá), có {[m.ma for m in muc]}")
    for m in muc:
        loi += [f"{m.ma}: {x}" for x in loi_muc(m, goc)]
    return loi


def loi_con_tro_handoff(van_handoff: str, duong: str = "docs/QUYET-DINH-CHO.md",
                        nhan: str = "**Cần người quyết:**", cua_so: int = 3) -> list[str]:
    """HANDOFF phải trỏ tới sổ ngay dưới mục "Cần người quyết". HÀM THUẦN."""
    dong = van_handoff.splitlines()
    chi = [i for i, d in enumerate(dong) if d.strip() == nhan]
    if len(chi) != 1:
        return [f"tìm thấy {len(chi)} dòng {nhan!r} trong HANDOFF (cần đúng 1)"]
    kho = "\n".join(dong[chi[0] + 1: chi[0] + 1 + cua_so])
    if duong not in kho:
        return [f"{duong} không được nhắc trong {cua_so} dòng ngay dưới {nhan}"]
    return []


def tom_tat(muc: list[Muc]) -> dict[str, int]:
    dem = {t: 0 for t in TRANG_THAI}
    for m in muc:
        dem[m.trang_thai] = dem.get(m.trang_thai, 0) + 1
    return dem


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    van = TEP.read_text(encoding="utf-8")
    muc = doc_muc(van)
    for m in muc:
        print(f"{m.ma:<4} [{m.trang_thai:<12}] {m.tieu_de}")
    print()
    print("tổng:", tom_tat(muc))
    loi = loi_so(muc) + loi_con_tro_handoff(HANDOFF.read_text(encoding="utf-8"))
    for x in loi:
        print("LỖI:", x)
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
