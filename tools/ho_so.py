"""Hồ sơ một file: dự án ĐÃ NÓI GÌ về nó, gom từ bốn nguồn đã đo.

VÌ SAO TỒN TẠI
──────────────
`SKILL.md` Bước 1 điều 1 bảo *"tìm xem đã có lời giải chưa"* bằng
`grep -rn`. Hai lần trong ba ngày (05/09 và 07/09) lời giải nằm sẵn trong
một file test kèm docstring nói thẳng lý do, và vẫn bị viết lại từ đầu.
Công cụ này là bản cơ giới hoá đúng bước ấy: hỏi một cái tên file, trả về
mọi chỗ dự án đã nói về nó.

NÓ KHÔNG TÓM TẮT GÌ CẢ
──────────────────────
Mọi dòng nó in ra là một địa chỉ có thật — tên test, số hiệu BƯỚC, số
hiệu ĐO, số hiệu lỗi — để người đọc `grep` lại. Không có tầng nén, không
gọi mô hình. Quy tắc số 2 của dự án giữ nguyên hiệu lực: **công cụ này
chỉ ra CHỖ đáng nhìn, nó không phán cái gì đúng.**

BỐN NGUỒN, VÀ SỨC NẶNG ĐO ĐƯỢC CỦA TỪNG NGUỒN (15/09/2026)
──────────────────────────────────────────────────────────
    test IMPORT file  ·  BƯỚC trong STATE.md  ·  ĐO trong TIÊU-CHÍ  ·  bảng lỗi

Trên 52 file `.py` ở gốc repo: **23 file có ≥3 tham chiếu**, trung vị 2,
13 file không có gì. Ba file nặng nhất — `paper_trading.py` 28,
`walkforward.py` 18, `paper_metrics.py` 18 — đúng là ba file mà
`cua_doc_bat_buoc` đang canh vì chúng ảnh hưởng kết quả.

Bảng lỗi là nguồn **phụ**, và điều đó là kết quả đo chứ không phải dự
đoán: tách cột ra thì chỉ **8/66 dòng** (12%) lặp lại một file ở CHỖ
HỎNG, lớp `chua-do` là 6/27. Bản chưa tách cột cho 29/48 = 60% — đọc
rộng gấp đôi, vì cột "cách chặn" chứa tên GÁC chứ không phải chỗ hỏng.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

BANG_LOI = GOC / ".claude/skills/quy-trinh-lam-viec/references/loi-da-mac.md"
PHAN_LOP = GOC / "docs/loi-phan-lop.json"
STATE = GOC / "docs/STATE.md"
TIEU_CHI = GOC / "docs/TIEU-CHI-DOC-TRUOC.md"
THU_MUC_TEST = GOC / "tests"

#: Trần của `additionalContext` theo đặc tả hook của Claude Code. Vượt thì
#: Claude Code ghi ra file rồi đưa đường dẫn kèm bản xem trước — tức hồ sơ
#: biến thành một cái tên file, đúng thứ công cụ này sinh ra để tránh.
TRAN_KY_TU = 10_000

#: Ngưỡng để một file được coi là "có hồ sơ đáng bơm". Đo 15/09/2026:
#: 23/52 file ở gốc repo đạt, trung vị của cả rổ là 2.
TOI_THIEU_THAM_CHIEU = 3

#: Đệm nằm ở THƯ MỤC TẠM, không nằm trong repo — `CLAUDE.md` mục "Ranh giới
#: không vượt qua": *không commit trạng thái chạy*. Một file đệm trong cây
#: repo sẽ vào diff, vào PR, và trôi khỏi máy khác.
TEN_DEM = "vibe_ho_so_chi_muc.json"

#: Số hiệu lược đồ của đệm. Đổi hình dạng bốn chỉ mục mà quên đổi số này
#: thì một bản đệm cũ sẽ được nạp vào một bản mã mới — đúng lớp lỗi "hai
#: đời dữ liệu trộn nhau". Vân tay chỉ canh ĐẦU VÀO; số này canh MÃ.
LUOC_DO_DEM = 1


@dataclass
class HoSo:
    ten: str
    test: list[str] = field(default_factory=list)
    buoc: list[str] = field(default_factory=list)
    do: list[str] = field(default_factory=list)
    loi_cho_hong: list[tuple[int, str]] = field(default_factory=list)
    loi_gac: list[tuple[int, str]] = field(default_factory=list)

    @property
    def so_tham_chieu(self) -> int:
        return len(self.test) + len(self.buoc) + len(self.do)

    @property
    def dang_ke(self) -> bool:
        return self.so_tham_chieu >= TOI_THIEU_THAM_CHIEU or bool(
            self.loi_cho_hong)


# ── đọc từng nguồn ──────────────────────────────────────────────────────

def _ten_co_so(o: str) -> str | None:
    """`walkforward.py:569` · `paper_metrics.Performance.x` -> tên file."""
    loi = re.split(r"::|:", o)[0].strip()
    t = Path(loi).name
    if t.endswith((".py", ".md", ".json", ".yml", ".toml")):
        return t
    dau = loi.split(".")[0].split("/")[-1]
    return f"{dau}.py" if dau and dau.isidentifier() else None


def test_nhap(thu_muc: Path = THU_MUC_TEST) -> dict[str, list[str]]:
    """{tên file: [test import nó]} — đọc AST, KHÔNG đọc `in`.

    `CLAUDE.md` mục "Gác phải đọc AST, không đọc `in`": ngày 22/08/2026
    hai gác viết bằng `"tên" in src` vẫn xanh sau khi xoá hẳn lời gọi,
    vì cái tên còn nằm trong khối chú thích.
    """
    ra: dict[str, list[str]] = defaultdict(list)
    for t in sorted(thu_muc.glob("test_*.py")):
        try:
            cay = ast.parse(t.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(cay):
            if isinstance(n, ast.Import):
                for a in n.names:
                    ra[a.name.split(".")[0] + ".py"].append(t.name)
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                ra[n.module.split(".")[0] + ".py"].append(t.name)
    return {k: sorted(set(v)) for k, v in ra.items()}


def _muc_nhac_ten(duong_dan: Path, mau_tieu_de: str) -> dict[str, list[str]]:
    """{tên file: [tiêu đề mục nhắc tới nó]} trong một tài liệu chia mục."""
    if not duong_dan.exists():
        return {}
    van = duong_dan.read_text(encoding="utf-8", errors="replace")
    phan = re.split(mau_tieu_de, van, flags=re.M)
    ra: dict[str, list[str]] = defaultdict(list)
    for i in range(1, len(phan) - 1, 2):
        tieu_de, than = phan[i].strip(), phan[i + 1]
        for ten in set(re.findall(r"[A-Za-z0-9_]+\.py", than)):
            ra[ten].append(tieu_de.split("—")[0].strip())
    return {k: v for k, v in ra.items()}


def buoc_nhac_ten(duong_dan: Path = STATE) -> dict[str, list[str]]:
    return _muc_nhac_ten(duong_dan, r"^## (BƯỚC \d+[^\n]*)$")


def do_nhac_ten(duong_dan: Path = TIEU_CHI) -> dict[str, list[str]]:
    return _muc_nhac_ten(duong_dan, r"^## (ĐO \d+[^\n]*)$")


def bang_loi(duong_dan: Path = BANG_LOI,
             phan_lop: Path = PHAN_LOP) -> dict[str, dict]:
    """{tên file: {cho_hong: [(số, lớp)], gac: [(số, lớp)]}}.

    TÁCH CỘT, và đó là cả điểm của hàm này. Cột "cách chặn" chứa tên
    **gác**; gộp nó vào chỗ hỏng thì tỷ lệ lặp file nhảy từ 12% lên 60%
    — đo 15/09/2026.
    """
    lop = {}
    if phan_lop.exists():
        lop = json.loads(phan_lop.read_text(encoding="utf-8")).get("loi", {})
    ra: dict[str, dict] = defaultdict(lambda: {"cho_hong": [], "gac": []})
    if not duong_dan.exists():
        return {}
    for dong in duong_dan.read_text(encoding="utf-8",
                                    errors="replace").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|", dong)
        if not m:
            continue
        so = int(m.group(1))
        l = lop.get(str(so), {}).get("lop", "?")
        cot = dong.split("|")
        for chi_so, khoa in ((2, "cho_hong"), (5, "gac")):
            if len(cot) <= chi_so:
                continue
            for o in re.findall(r"`([^`]+)`", cot[chi_so]):
                ten = _ten_co_so(o)
                if ten:
                    ra[ten][khoa].append((so, l))
    return {k: {a: sorted(set(b)) for a, b in v.items()} for k, v in ra.items()}


# ── đệm ─────────────────────────────────────────────────────────────────

def duong_dan_dem() -> Path:
    return Path(tempfile.gettempdir()) / TEN_DEM


def _dau_vao_chi_muc() -> list[Path]:
    """MỌI file bốn chỉ mục đọc. Thiếu một cái là đệm ôi mà không ai biết.

    Danh sách test SUY RA từ đĩa chứ không gõ: thêm một file test mới là
    thêm một mục vào vân tay, nên đệm tự hỏng đúng lúc cần hỏng.
    """
    return sorted(THU_MUC_TEST.glob("test_*.py")) + [
        STATE, TIEU_CHI, BANG_LOI, PHAN_LOP]


def van_tay() -> str:
    """Dấu vân tay của mọi đầu vào — tên · mtime · cỡ, cộng số hiệu lược đồ.

    VÌ SAO KHÔNG BĂM NỘI DUNG. Băm 94 file test cộng `STATE.md` là đọc
    đúng lượng byte mà việc dựng chỉ mục đang đọc, tức đệm không tiết
    kiệm gì. `stat()` đọc siêu dữ liệu, rẻ hơn hai bậc.

    VÌ SAO CÓ CẢ CỠ FILE, khi đã có `mtime_ns`. Trên vài hệ tệp `mtime`
    có thể trùng cho hai lượt ghi rất sát nhau; cỡ file bắt được phần lớn
    những ca ấy. Hai dấu hiệu rẻ vẫn rẻ hơn một phép băm.

    VÌ SAO CÓ CẢ ĐƯỜNG DẪN ĐẦY ĐỦ VÀ `GOC`. Đệm nằm ở thư mục tạm CHUNG
    của máy, nên hai bản sao repo — hay một `git worktree` — dùng chung
    một file đệm. Không có `GOC` trong vân tay thì bản sao thứ hai có thể
    nhận chỉ mục của bản thứ nhất.

    Một file VẮNG cũng phải đổi vân tay — xoá `loi-phan-lop.json` làm bảng
    lỗi mất cột lớp, và đó là một chỉ mục khác.
    """
    m = hashlib.sha256()
    m.update(f"luoc_do={LUOC_DO_DEM}\0goc={GOC}\0".encode())
    for p in _dau_vao_chi_muc():
        try:
            st = p.stat()
            m.update(f"{p}\0{st.st_mtime_ns}\0{st.st_size}\0".encode())
        except OSError:
            m.update(f"{p}\0VANG\0".encode())
    return m.hexdigest()


def _dung_chi_muc() -> dict:
    """Bốn chỉ mục, dựng từ đầu. Đây là NGUỒN SỰ THẬT; đệm chỉ chép lại."""
    return {
        "test": test_nhap(),
        "buoc": buoc_nhac_ten(),
        "do": do_nhac_ten(),
        "loi": bang_loi(),
    }


def _chuan_hoa(d: dict) -> dict:
    """JSON không có tuple. Trả bảng lỗi về đúng hình dạng `_dung_chi_muc`.

    Không có bước này thì đệm ĐỌC RA một thứ khác thứ nó GHI VÀO — và
    khác ở chỗ im lặng nhất: `[68, "chua-do"]` so với `(68, "chua-do")`.
    """
    d["loi"] = {ten: {khoa: [tuple(x) for x in ds]
                      for khoa, ds in v.items()}
                for ten, v in d.get("loi", {}).items()}
    return d


def chi_muc(dung_dem: bool = True) -> dict:
    """Bốn chỉ mục, lấy từ đệm nếu vân tay khớp.

    KHÔNG BAO GIỜ NỔ VÌ ĐỆM. Mọi lỗi đọc/ghi đều rơi xuống đường dựng lại
    — cùng nguyên tắc với `cua_ho_so.py`: một cái đệm làm hỏng lượt Read
    thì tệ hơn không có đệm.

    Đo 17/09/2026 trước khi có nó: một lượt hồ sơ đầu tiên cho mỗi file
    tốn **410 ms** (trung vị, 6 file), trong đó **237 ms** là `test_nhap`
    nạp AST của 94 file test — một chỉ mục TOÀN REPO, không phụ thuộc file
    đang hỏi, mà vẫn dựng lại từ đầu mỗi lượt.
    """
    if not dung_dem:
        return _dung_chi_muc()
    vt = van_tay()
    p = duong_dan_dem()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("van_tay") == vt:
            return _chuan_hoa(d["chi_muc"])
    except Exception:
        pass

    ci = _dung_chi_muc()
    try:
        tam = p.with_suffix(f".{os.getpid()}.tam")
        tam.write_text(json.dumps({"van_tay": vt, "chi_muc": ci},
                                  ensure_ascii=False),
                       encoding="utf-8")
        os.replace(tam, p)
    except Exception:
        pass
    return ci


# ── gom lại ─────────────────────────────────────────────────────────────

def doc_ho_so(ten_file: str, dung_dem: bool = True) -> HoSo:
    """Hồ sơ của MỘT file. Nhận đường dẫn bất kỳ, quy về tên cơ sở."""
    ten = Path(ten_file).name
    ci = chi_muc(dung_dem)
    bl = ci["loi"].get(ten, {"cho_hong": [], "gac": []})
    return HoSo(
        ten=ten,
        test=ci["test"].get(ten, []),
        buoc=ci["buoc"].get(ten, []),
        do=ci["do"].get(ten, []),
        loi_cho_hong=[(s, l) for s, l in bl.get("cho_hong", [])],
        loi_gac=[(s, l) for s, l in bl.get("gac", [])],
    )


def dong_ho_so(hs: HoSo, tran: int = TRAN_KY_TU) -> list[str]:
    """Dựng các dòng, KHÔNG in. Cắt theo thứ tự ưu tiên khi chạm trần.

    Thứ tự ưu tiên là kết quả đo, không phải sở thích: bảng lỗi đứng
    TRƯỚC vì nó hiếm (8/66 dòng) nên khi có thì nó đắt; test đứng sau vì
    nó dày nhất và cũng dễ tìm lại nhất bằng `grep`.
    """
    if not hs.dang_ke:
        return []
    # HAI con số, cố ý KHÔNG cộng làm một: `so_tham_chieu` đếm ba nguồn
    # chính, bảng lỗi là nguồn phụ (8/66 dòng, đo 15/09/2026). Nhưng đầu
    # đề phải khai ĐỦ thứ nó đứng trên — bản trước in `(0 tham chiếu)`
    # ngay trên ba dòng bảng lỗi của `HANDOFF.md`, và một số 0 như thế
    # mời người đọc bỏ qua cả khối. Lỗi 68, lôi ra bởi chính lượt bơm
    # thật đầu tiên của cửa (16/09/2026).
    dem = f"{hs.so_tham_chieu} tham chiếu"
    if hs.loi_cho_hong:
        dem += f" · {len(hs.loi_cho_hong)} dòng bảng lỗi"
    d = [f"HỒ SƠ {hs.ten} — dự án đã nói gì về file này ({dem})"]

    if hs.loi_cho_hong:
        d.append("  BẢNG LỖI · file này TỪNG LÀ CHỖ HỎNG:")
        for so, lop in hs.loi_cho_hong:
            d.append(f"      lỗi {so} [{lop}]")
    if hs.loi_gac:
        d.append("  BẢNG LỖI · file này là GÁC của: "
                 + ", ".join(f"lỗi {s}" for s, _ in hs.loi_gac))
    if hs.buoc:
        d.append(f"  STATE.md  ({len(hs.buoc)}): " + " · ".join(hs.buoc))
    if hs.do:
        d.append(f"  TIÊU CHÍ  ({len(hs.do)}): " + " · ".join(hs.do))
    if hs.test:
        d.append(f"  TEST KHOÁ ({len(hs.test)}): " + " · ".join(hs.test))

    d.append("  — đây là ĐỊA CHỈ để tra, không phải kết luận. "
             "Không tóm tắt, không nén.")

    van = "\n".join(d)
    while len(van) > tran and len(d) > 2:
        d.pop(-2)
        van = "\n".join(d)
    return d


def ten_dang_bom(toi_thieu: int = TOI_THIEU_THAM_CHIEU) -> list[str]:
    """Các file `.py` ở gốc repo đủ dày để đáng bơm.

    SUY RA, ĐỪNG GÕ. Gõ tay 23 cái tên thì danh sách trôi khỏi repo ngay
    lần thêm file tiếp theo.

    **CỬA KHÔNG GỌI HÀM NÀY** (đo 16/09/2026). `cua_ho_so.quyet_dinh()`
    hỏi thẳng `dong_ho_so()` cho từng file, nên quần thể thật của cửa
    rộng hơn quần thể ở đây: nó bơm cả `.md`, mà hàm này chỉ duyệt
    `*.py`. Bản trước ghi *"dùng sinh danh sách lọc của cửa"* — một lời
    hứa về đường nối chưa tồn tại, đúng lớp lỗi tài liệu thứ nhất ở
    `docs/HANDOFF.md` mục 4.

    Hàm này là MÁY ĐO, và là nguồn dự kiến cho trường `if` của hook nếu
    có ngày cần cắt chi phí sinh tiến trình mỗi lượt Read.
    """
    ci = chi_muc()
    tn, bn, dn, bl = ci["test"], ci["buoc"], ci["do"], ci["loi"]
    ra = []
    for p in sorted(GOC.glob("*.py")):
        n = (len(tn.get(p.name, [])) + len(bn.get(p.name, []))
             + len(dn.get(p.name, [])))
        if n >= toi_thieu or bl.get(p.name, {}).get("cho_hong"):
            ra.append(p.name)
    return ra


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="tên file cần tra hồ sơ")
    ap.add_argument("--danh-sach", action="store_true", dest="danh_sach",
                    help="in các file đủ dày để đáng bơm")
    ap.add_argument("--khong-dem", action="store_true", dest="khong_dem",
                    help="bỏ qua đệm, dựng lại bốn chỉ mục từ đầu")
    a = ap.parse_args()

    if a.danh_sach:
        ten = ten_dang_bom()
        for t in ten:
            print(t)
        print(f"\n{len(ten)} file trên {len(list(GOC.glob('*.py')))} file "
              f".py ở gốc repo")
        return 0

    if not a.file:
        ap.error("cần một tên file, hoặc --danh-sach")

    hs = doc_ho_so(a.file, dung_dem=not a.khong_dem)
    dong = dong_ho_so(hs)
    if not dong:
        print(f"{hs.ten}: chưa có hồ sơ "
              f"({hs.so_tham_chieu} tham chiếu, cần ≥{TOI_THIEU_THAM_CHIEU})")
        return 0
    print("\n".join(dong))
    return 0


if __name__ == "__main__":
    sys.exit(main())
