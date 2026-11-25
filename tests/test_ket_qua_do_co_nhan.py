"""Gác CẤU TRÚC của nhãn con số — BƯỚC 299, từ ĐO 38 trở đi.

VÌ SAO CÓ FILE NÀY
──────────────────
Luật đã nằm ở phần mở đầu của `docs/TIEU-CHI-DOC-TRUOC.md` (mục "Nhãn của
con số"): mọi con số một ĐO báo ra mang đúng MỘT nhãn — `Đã khai M#` ·
`Báo kèm` · `Sau khi nhìn`. Chẩn đoán trước đó: luật CÓ, nhưng máy không canh
phần KẾT QUẢ, và không có nhãn chung để tách "đã khai" khỏi "sau khi nhìn".

Gác này canh HÌNH DẠNG của luật ấy, bằng hai bộ đọc:

  1. `docs/TIEU-CHI-DOC-TRUOC.md`, mục `## ĐO n —` với n >= 38 (phần KÝ):
     dòng `- **M1** … (người dùng|leader)`, mã không trùng, khối `### SỬA ĐO`
     đủ trường, mục hậu tố chữ phải là `Sau khi nhìn`, thăng nhãn đúng khuôn;
  2. `docs/STATE.md`, mục mở bằng `**Kết quả ĐO k:**` với k >= 38: ba khối
     đúng thứ tự, mã ở khối ⊂ mã phần ký, mọi M# có mặt hay có lời "không báo
     được vì", hai dòng sha, và `git merge-base --is-ancestor`.

HIỆN KHÔNG CÓ MỤC NÀO >= 38. Một gác chỉ chạy trên file thật hôm nay đọc
0 mục và xanh mãi — nên mỗi luật được thử trên VĂN BẢN DỰNG TAY (một mẫu tốt,
một mẫu xấu cho mỗi luật), và bộ đột biến (`references/bay.md`) đục từng luật.

ĐIỀU GÁC NÀY KHÔNG LÀM — nói thẳng, bài học lỗi 86 và 44
────────────────────────────────────────────────────────
- Nó không biết con số thật có thuộc mã đã nêu không: nhãn có thể thành câu
  thần chú. Giảm nhẹ: mã ở khối phải có ở phần ký, và M# nào không báo thì
  phải khai lý do ≥ 30 ký tự.
- Nó không biết "dữ liệu mới" của một lần thăng nhãn có thật mới không: nó chỉ
  kiểm HÌNH DẠNG (mã tồn tại ở ĐO nguồn, câu `dữ liệu mới:` có mặt). Việc
  phán là của người duyệt.
- Giờ commit không phải bằng chứng. Bằng chứng là tổ tiên trong `origin/main`
  ghi lúc chạy; lối thoát "commit cục bộ" được phép nhưng mang nhãn yếu.

QUÉT: bỏ khối mã (rào ``` / ~~~) và dòng `> ` TRƯỚC khi đọc — STATE có 1.166
dòng rào và chính luật trích mẫu nhãn. Tên `M0`–`M9` của ĐO 24 vô hại: neo là
`- **M<số>**` và n >= 38. Mọi so sánh danh sách ở đây đều SẮP XẾP trước (lỗi
206: thứ tự duyệt cây khác nhau giữa NTFS và Linux).

REPO NÔNG THÌ ĐỎ, không xanh im (cùng luật `tests/test_tien_dang_ky_git.py`):
ở bản nông `--is-ancestor` có thể ra 1 oan hoặc 128, nên `la_to_tien` nổ
`ChuaKiemDuoc`. CI đặt `fetch-depth: 0` (`.github/workflows/kiem-dinh.yml`).
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tests"))

# Dùng lại máy cắt mục đã có (không chép): hai bản sao của một phép cắt trôi
# ra khỏi nhau.
from test_phep_do_neu_dung_cu import cac_muc  # noqa: E402

TIEU_CHI = GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md"
STATE = GOC / "docs" / "STATE.md"

TU_DO = 38
DAI_LY_DO = 30        # lý do ≥ 30 ký tự: cùng ngưỡng `test_do_phai_khai_da_tra.py`
DAI_DIEM_SO_SANH = 20  # `- **M1** (người dùng)` không phải một điểm so sánh
HUONG = ("nới", "siết", "trung tính")
CAU_NOI = "đạt-sau-khi-đổi-luật không phải bằng chứng máy đo tốt hơn"
CAU_KET_CUC = "dưới văn bản đã sửa"
BA_KHOI = ["Đã khai", "Báo kèm", "Sau khi nhìn"]


class ChuaKiemDuoc(RuntimeError):
    """Không phán được tổ tiên (repo nông, sha lạ): KHÔNG được coi là sạch."""


# ── quét ─────────────────────────────────────────────────────────────────

RE_RAO = re.compile(r"^\s*(`{3,}|~{3,})")


def bo_khoi_ma_va_trich(van: str) -> str:
    """Thay khối mã và dòng `> ` bằng dòng RỖNG (giữ nguyên số dòng).

    Xuống dòng CRLF quy về LF (lỗi 93). Rào không đóng thì NỔ: nếu nuốt im
    phần còn lại của file thì gác xanh trên thứ nó chưa đọc.
    """
    ra: list[str] = []
    rao = None
    for dong in van.replace("\r\n", "\n").split("\n"):
        m = RE_RAO.match(dong)
        if rao is None:
            if m:
                rao = m.group(1)
                ra.append("")
            elif re.match(r"^ {0,3}>", dong):
                ra.append("")
            else:
                ra.append(dong)
        else:
            ra.append("")
            gon = dong.strip()
            if m and set(gon) == {rao[0]} and len(gon) >= len(rao):
                rao = None
    if rao is not None:
        raise ValueError("khối mã không đóng: gác sẽ nuốt im phần còn lại")
    return "\n".join(ra)


RE_TEN_MUC = re.compile(r"ĐO\s+(\d+)([a-z]?)$")
RE_DONG_M = re.compile(r"^\s*-\s+\*\*M(\d+)\*\*(.*)$", re.M)
RE_DONG_B = re.compile(r"^\s*-\s+\*\*B(\d+)\*\*(.*)$", re.M)
# Quyết định của leader 25/11/2026: `(leader)` TRƠ TRỤI không hợp lệ; chỉ `(leader — người dùng giao:
# *"<lời người dùng, >= 10 ký tự>"*)`. Dòng 8 đầu tệp (người dùng chốt mọi mục) vẫn là luật.
RE_NGUOI_CHOT = re.compile(r'\((người dùng|leader — người dùng giao: \*"[^"]{10,}"\*)\)\s*$')
RE_NHAN_YEU = re.compile(r"^\s*\*\*Nhãn:\*\*\s*Sau khi nhìn\s*$", re.M)
RE_THANG = re.compile(
    r"\(thăng từ ĐO\s+(\d+)\s+(B\d+|Báo kèm|Sau khi nhìn);\s*"
    r"dữ liệu mới:\s*([^)]{10,})\)")
RE_TIEU_DE_SUA = re.compile(r"^###\s+SỬA ĐO\s+(\d+)\b.*$", re.M)
RE_TIEU_DE_BAT_KY = re.compile(r"^#{1,6}\s", re.M)


def _cat_den_tieu_de_khac(than: str) -> str:
    """`cac_muc` cắt tới `## ĐO` kế; ở đây cắt sớm hơn, tới BẤT KỲ `## `."""
    return re.split(r"\n## ", than, maxsplit=1)[0]


def doc_tieu_chi(van: str) -> tuple[list[tuple[str, int, str, str]], list[str]]:
    """((tên, n, hậu tố, thân) của mục n >= 38, tên các mục n <= 37 SẮP XẾP)."""
    muc, bo_qua = [], []
    for ten, than in cac_muc(bo_khoi_ma_va_trich(van)):
        m = RE_TEN_MUC.match(ten)
        n, hau_to = int(m.group(1)), m.group(2)
        if n >= TU_DO:
            muc.append((ten, n, hau_to, _cat_den_tieu_de_khac(than)))
        else:
            bo_qua.append(ten)
    return muc, sorted(bo_qua)


def ma_phan_ky(than: str) -> tuple[set[str], set[str]]:
    """(tập M#, tập B#) khai ở phần ký của một mục."""
    return ({"M" + x for x, _ in RE_DONG_M.findall(than)},
            {"B" + x for x, _ in RE_DONG_B.findall(than)})


# ── luật 1: phần KÝ của mục ĐO >= 38 ─────────────────────────────────────

def kiem_sua(n: int, khoi: str) -> list[str]:
    """Khối `### SỬA ĐO n`: mỗi điều một dòng `cũ → mới — **Hướng:** …`, và
    bốn trường còn lại. Điều "nới" kèm hai câu bắt buộc."""
    loi = []
    dong_dieu = [d for d in khoi.split("\n") if re.match(r"^\s*-\s+.*→", d)]
    if not dong_dieu:
        loi.append(f"SỬA ĐO {n}: không có dòng điều khoản dạng `- <điều>: <cũ> → <mới>`")
    co_noi = False
    for d in dong_dieu:
        h = re.search(r"\*\*Hướng:\*\*\s*(nới|siết|trung tính)\b", d)
        if not h:
            loi.append(f"SỬA ĐO {n}: dòng thiếu `**Hướng:** nới | siết | trung tính`: {d.strip()[:60]}")
        elif h.group(1) == "nới":
            co_noi = True
    for truong in ("Người chốt", "Đã thấy", "Chưa đọc gì", "Commit tới origin/main"):
        if not re.search(rf"\*\*{re.escape(truong)}:\*\*\s*\S", khoi):
            loi.append(f"SỬA ĐO {n}: thiếu trường `**{truong}:**`")
    if co_noi:
        thap = khoi.casefold()
        for cau in (CAU_NOI, CAU_KET_CUC):
            if cau.casefold() not in thap:
                loi.append(f"SỬA ĐO {n}: có điều \"nới\" nhưng thiếu câu \"{cau}\"")
    return loi


def kiem_muc(ten: str, n: int, hau_to: str, than: str) -> list[str]:
    """Luật của MỘT mục ĐO >= 38 (không đụng tới mục khác)."""
    loi = []
    dong_m = RE_DONG_M.findall(than)
    if hau_to:  # `ĐO 38b`: chẩn đoán SAU, không quyết kết cục
        if not RE_NHAN_YEU.search(than):
            loi.append(f"{ten}: mục hậu tố chữ thiếu dòng `**Nhãn:** Sau khi nhìn`")
        if dong_m:
            loi.append(f"{ten}: mục hậu tố chữ không được có dòng `- **M#**`")
    else:
        if not dong_m:
            loi.append(f"{ten}: phần ký không có dòng `- **M1** … (người dùng|leader)`")
        for so, phan_con in dong_m:
            if not RE_NGUOI_CHOT.search(phan_con):
                loi.append(f"{ten}: dòng M{so} thiếu `(người dùng)` hay `(leader — người dùng giao: *\"…\"*)` ở cuối")
            elif len(RE_NGUOI_CHOT.sub("", phan_con).strip()) < DAI_DIEM_SO_SANH:
                loi.append(f"{ten}: dòng M{so} không nêu điểm so sánh (< {DAI_DIEM_SO_SANH} ký tự)")
        ma = [so for so, _ in dong_m]
        if len(ma) != len(set(ma)):
            loi.append(f"{ten}: mã M# trùng nhau {sorted(ma)}")
    ma_b = [so for so, _ in RE_DONG_B.findall(than)]
    if len(ma_b) != len(set(ma_b)):
        loi.append(f"{ten}: mã B# trùng nhau {sorted(ma_b)}")
    for m in RE_TIEU_DE_SUA.finditer(than):
        sau = RE_TIEU_DE_BAT_KY.search(than, m.end())
        khoi = than[m.start(): sau.start() if sau else len(than)]
        if int(m.group(1)) != n:
            loi.append(f"{ten}: tiêu đề `### SỬA ĐO {m.group(1)}` nằm trong mục ĐO {n}")
        loi += [f"{ten}: {x}" for x in kiem_sua(int(m.group(1)), khoi)]
    return loi


def kiem_tieu_chi(van: str) -> list[str]:
    """Mọi lỗi cấu trúc của các mục ĐO >= 38 (rỗng = sạch)."""
    muc, _ = doc_tieu_chi(van)
    loi = []
    ten_muc = [t for t, _, _, _ in muc]
    for ten in sorted({t for t in ten_muc if ten_muc.count(t) > 1}):
        loi.append(f"{ten}: tiêu đề `## {ten} —` xuất hiện {ten_muc.count(ten)} lần (phải duy nhất)")
    ky = {}
    for ten, n, hau_to, than in muc:
        loi += kiem_muc(ten, n, hau_to, than)
        if not hau_to:
            ky[n] = ma_phan_ky(than)
    for ten, n, hau_to, than in muc:
        for so_dong in than.split("\n"):
            if "thăng từ" not in so_dong:
                continue
            m = RE_THANG.search(so_dong)
            if not m:
                loi.append(f"{ten}: dòng thăng nhãn sai khuôn `(thăng từ ĐO <n> B1; dữ liệu mới: <…>)`")
                continue
            nguon, the = int(m.group(1)), m.group(2)
            if nguon >= n:
                loi.append(f"{ten}: thăng nhãn từ ĐO {nguon} — chỉ được từ một ĐO TRƯỚC")
            elif re.fullmatch(r"B\d+", the) and nguon < TU_DO:
                loi.append(f"{ten}: ĐO {nguon} chưa có mã B# để thăng ({the})")
            elif re.fullmatch(r"B\d+", the) and the not in ky.get(nguon, (set(), set()))[1]:
                loi.append(f"{ten}: {the} không có ở phần ký của ĐO {nguon}")
    return loi


# ── luật 2: mục KẾT QUẢ ở STATE ──────────────────────────────────────────

RE_MO_KET_QUA = re.compile(r"^\*\*Kết quả ĐO\s+(\d+):\*\*", re.M)
RE_TIEU_DE_KHOI = re.compile(r"^###\s+(Đã khai|Báo kèm|Sau khi nhìn)\b(.*)$", re.M)
RE_SHA = r"`?([0-9a-f]{7,40})`?"
RE_KHAI = re.compile(r"\*\*Khai ở commit:\*\*\s*" + RE_SHA)
RE_CHAY = re.compile(r"\*\*Chạy trên origin/main:\*\*\s*" + RE_SHA)
RE_YEU = re.compile(r"\*\*Khai trước bằng:\*\*\s*commit cục bộ — vì\s+(\S.*)$", re.M)
RE_KHONG_BAO = re.compile(r"\*{0,2}M(\d+)\*{0,2}\s+—\s+không báo được vì\s+(\S.*)$", re.M)


def doc_ket_qua(van: str) -> tuple[list[tuple[int, str]], list[int]]:
    """((k, thân) của mục `**Kết quả ĐO k:**` với k >= 38, các k <= 37 SẮP XẾP)."""
    sach = bo_khoi_ma_va_trich(van)
    vt = list(RE_MO_KET_QUA.finditer(sach))
    muc, bo_qua = [], []
    for i, m in enumerate(vt):
        diem = [len(sach)]
        if i + 1 < len(vt):
            diem.append(vt[i + 1].start())
        sau = re.search(r"^## ", sach[m.end():], re.M)
        if sau:
            diem.append(m.end() + sau.start())
        k = int(m.group(1))
        if k >= TU_DO:
            muc.append((k, sach[m.start(): min(diem)]))
        else:
            bo_qua.append(k)
    return muc, sorted(bo_qua)


def git_that(*doi, cwd=GOC) -> tuple[int, str]:
    """`git` ở `cwd`; `(mã thoát, stdout)`. Không có git thì `(127, '')`."""
    try:
        r = subprocess.run(["git", *doi], cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return r.returncode, r.stdout


def la_to_tien(khai: str, chay: str, git=git_that) -> bool:
    """`git merge-base --is-ancestor <khai> <chay>`: True (0) · False (1).

    Mọi thứ khác — repo NÔNG, sha lạ, không có git — là `ChuaKiemDuoc`, không
    phải False và không phải True: ở bản nông, thiếu lịch sử có thể làm lệnh
    ra 1 oan, còn "yếu" thì phải là một lời khai chứ không phải một tai nạn.
    `git(*đối số) -> (mã thoát, stdout)` tiêm được như `kiem_cong`.
    """
    for sha in (khai, chay):
        if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
            raise ChuaKiemDuoc(f"sha không đúng dạng: {sha!r}")
    rc, ra = git("rev-parse", "--is-shallow-repository")
    if rc != 0 or ra.strip() != "false":
        raise ChuaKiemDuoc("repo NÔNG (shallow) hoặc không đọc được: không phán được tổ tiên")
    rc, _ = git("merge-base", "--is-ancestor", khai, chay)
    if rc == 0:
        return True
    if rc == 1:
        return False
    raise ChuaKiemDuoc(f"git merge-base --is-ancestor ra mã {rc} (sha không có trong kho?)")


def _ma_tieu_de(phan_con: str, chu: str) -> set[str]:
    return set(re.findall(rf"{chu}\d+", phan_con))


def kiem_ket_qua(k: int, than: str, ky: tuple[set[str], set[str]] | None,
                 git=git_that) -> list[str]:
    """Luật của MỘT mục kết quả. `ky` = (M#, B#) của mục ĐO k ở TIEU-CHI."""
    nhan = f"Kết quả ĐO {k}"
    if ky is None:
        return [f"{nhan}: không có mục `## ĐO {k} —` (phần ký) ở docs/TIEU-CHI-DOC-TRUOC.md"]
    ky_m, ky_b = ky
    loi = []
    td = list(RE_TIEU_DE_KHOI.finditer(than))
    if [m.group(1) for m in td] != BA_KHOI:
        return [f"{nhan}: ba khối phải đúng thứ tự {' · '.join(BA_KHOI)}, thấy "
                f"{[m.group(1) for m in td]}"]
    khoi = {}
    for i, m in enumerate(td):
        sau = RE_TIEU_DE_BAT_KY.search(than, m.end())
        khoi[m.group(1)] = than[m.end(): sau.start() if sau else len(than)].strip()
        if not khoi[m.group(1)]:
            loi.append(f"{nhan}: khối `{m.group(1)}` rỗng (khối trống ghi *Không có*)")
    dau = {m.group(1): m.group(2) for m in td}
    # mã ở tiêu đề khối và ở dòng khối ⊂ mã phần ký
    co_o_khoi_khai = {"M" + x for x, _ in RE_DONG_M.findall(khoi["Đã khai"])} | \
        set(re.findall(r"^\s*(?:-\s+)?\*\*(M\d+)\*\*", khoi["Đã khai"], re.M))
    for ma in sorted((_ma_tieu_de(dau["Đã khai"], "M") | co_o_khoi_khai) - ky_m):
        loi.append(f"{nhan}: {ma} ở khối Đã khai không có ở phần ký")
    co_o_khoi_kem = set(re.findall(r"^\s*(?:-\s+)?\*\*(B\d+)\*\*", khoi["Báo kèm"], re.M))
    for ma in sorted((_ma_tieu_de(dau["Báo kèm"], "B") | co_o_khoi_kem) - ky_b):
        loi.append(f"{nhan}: {ma} ở khối Báo kèm không có ở phần ký")
    # mọi M# của phần ký phải có mặt, hoặc có lời "không báo được vì"
    khong_bao = {"M" + so: ly_do for so, ly_do in RE_KHONG_BAO.findall(than)}
    for ma in sorted(ky_m):
        if ma in co_o_khoi_khai:
            continue
        if ma not in khong_bao:
            loi.append(f"{nhan}: {ma} của phần ký không có ở khối Đã khai và không có dòng "
                       f"`{ma} — không báo được vì <lý do>`")
        elif len(khong_bao[ma].strip()) < DAI_LY_DO:
            loi.append(f"{nhan}: lý do `{ma} — không báo được vì` ngắn hơn {DAI_LY_DO} ký tự")
    # khối Sau khi nhìn không là kết cục
    skn = khoi["Sau khi nhìn"]
    if re.search(r"^\s*(?:-\s+)?\*\*[MB]\d", skn, re.M):
        loi.append(f"{nhan}: khối Sau khi nhìn có dòng bắt đầu bằng mã M#/B# (số đã khai không đứng ở đây)")
    if "KẾT CỤC" in skn:
        loi.append(f"{nhan}: khối Sau khi nhìn có chữ KẾT CỤC (nó là đầu mối, không là kết cục)")
    # hai dòng sha và bằng chứng khai trước
    khai, chay = RE_KHAI.search(than), RE_CHAY.search(than)
    if not khai:
        loi.append(f"{nhan}: thiếu dòng `**Khai ở commit:** <sha>`")
    if not chay:
        loi.append(f"{nhan}: thiếu dòng `**Chạy trên origin/main:** <sha>`")
    yeu = RE_YEU.search(than)
    if "**Khai trước bằng:**" in than and not yeu:
        loi.append(f"{nhan}: dòng `**Khai trước bằng:**` sai khuôn `commit cục bộ — vì <lý do>`")
    if yeu and len(yeu.group(1).strip()) < DAI_LY_DO:
        loi.append(f"{nhan}: lý do của `Khai trước bằng` ngắn hơn {DAI_LY_DO} ký tự")
    ghi_yeu = "bằng chứng yếu" in dau["Đã khai"]
    if ghi_yeu != bool(yeu):
        loi.append(f"{nhan}: tiêu đề khối Đã khai phải ghi *(bằng chứng yếu)* khi và chỉ khi có dòng "
                   f"`**Khai trước bằng:** commit cục bộ`")
    if khai and chay and not yeu:
        try:
            if not la_to_tien(khai.group(1), chay.group(1), git):
                loi.append(f"{nhan}: commit khai {khai.group(1)} KHÔNG là tổ tiên của {chay.group(1)} "
                           f"(bằng chứng yếu: khai `Khai trước bằng` hoặc khai lại ở commit đã tới origin/main)")
        except ChuaKiemDuoc as e:
            loi.append(f"{nhan}: chưa kiểm được tổ tiên — {e}")
    return loi


def kiem_state(van_state: str, van_tieu_chi: str, git=git_that) -> list[str]:
    muc, _ = doc_ket_qua(van_state)
    ky = {n: ma_phan_ky(than) for _, n, hau_to, than in doc_tieu_chi(van_tieu_chi)[0] if not hau_to}
    loi = []
    dem = [k for k, _ in muc]
    for k in sorted({x for x in dem if dem.count(x) > 1}):
        loi.append(f"Kết quả ĐO {k}: mở {dem.count(k)} lần ở STATE (phải một lần)")
    for k, than in muc:
        loi += kiem_ket_qua(k, than, ky.get(k), git)
    return loi


# ═══ MẪU DỰNG TAY ════════════════════════════════════════════════════════

DIEM = "IC của điểm tổng so với lô ngẫu nhiên, 200 thị trường 2×, ngưỡng đọc ≥ 0,05"


def muc_do(n="38", hau_to="", m=("M1",), b=("B1",), them="", ten="thử một câu hỏi"):
    d = [f"## ĐO {n}{hau_to} — {ten} (khai 25/11/2026)", "", "Câu hỏi: …", ""]
    d += [f"- **{x}** {DIEM} (người dùng)" for x in m]
    d += [f"- **{x}** báo kèm một bảng phụ, không quyết kết cục" for x in b]
    return "\n".join(d) + "\n" + them + "\n"


def sua(noi=True, bo="", huong="nới"):
    t = ["### SỬA ĐO 38", "",
         f"- Điều K0: `nửa rào` → `20× rào` — **Hướng:** {huong}",
         "- Điều H: `H` → `2H` — **Hướng:** siết",
         "**Người chốt:** leader",
         "**Đã thấy:** các số đối chứng (ii) và (iii)",
         "**Chưa đọc gì:** số chính",
         "**Commit tới origin/main:** 0123abc"]
    if noi:
        t.append(f"*{CAU_NOI}*; kết cục ghi *{CAU_KET_CUC}*.")
    return "\n".join(x for x in t if not (bo and bo in x)) + "\n"


def tieu_chi(*muc, truoc="# Tiêu chí\n\nlời mở\n\n"):
    return truoc + "\n".join(muc)


def ket_qua(k="38", ma_khai=("M1",), ma_kem=("B1",), skn="*Không có*", khai="abc1234",
            chay="def5678", yeu=False, them="", sau_khai_dong="", dau_khai=None,
            thu_tu=None):
    th = ["Đã khai", "Báo kèm", "Sau khi nhìn"] if thu_tu is None else thu_tu
    dau = dau_khai if dau_khai is not None else (
        f"Đã khai ({', '.join(ma_khai)})" + (" (bằng chứng yếu)" if yeu else ""))
    khoi = {
        "Đã khai": f"### {dau}\n" + ("\n".join(f"- **{x}** IC = 0,07 (khai)" for x in ma_khai) or "*Không có*"),
        "Báo kèm": f"### Báo kèm ({', '.join(ma_kem)})\n" + ("\n".join(f"- **{x}** bảng phụ" for x in ma_kem) or "*Không có*"),
        "Sau khi nhìn": f"### Sau khi nhìn\n{skn}",
    }
    cuoi = [f"**Kết quả ĐO {k}:**", "", f"**Khai ở commit:** {khai}",
            f"**Chạy trên origin/main:** {chay}"]
    if yeu:
        cuoi.append("**Khai trước bằng:** commit cục bộ — vì khai trước lượt chạy nhưng PR chưa gộp được")
    cuoi.append(sau_khai_dong)
    return "\n".join(cuoi) + "\n\n" + "\n\n".join(khoi[t] for t in th) + "\n" + them + "\n"


def state(*phan):
    return "# STATE\n\n## BƯỚC 300 — thử\n\n" + "\n".join(phan)


def git_gia(rc=0, nong="false"):
    def g(*doi):
        if doi[:2] == ("rev-parse", "--is-shallow-repository"):
            return 0, nong + "\n"
        return rc, ""
    return g


def loi_cua(van, **kw):
    return kiem_tieu_chi(van, **kw)


# ═══ A. PHẦN KÝ (TIEU-CHI) ═══════════════════════════════════════════════

def test_mau_tot_tieu_chi_khong_loi():
    assert kiem_tieu_chi(tieu_chi(muc_do())) == []
    assert kiem_tieu_chi(tieu_chi(muc_do(them=sua()))) == []


def test_ba_nhan_B_la_tuy_chon_va_nhieu_M_ok():
    assert kiem_tieu_chi(tieu_chi(muc_do(m=("M1", "M2"), b=()))) == []


def test_xau_khong_co_dong_M():
    assert any("không có dòng" in x for x in kiem_tieu_chi(tieu_chi(muc_do(m=()))))


def test_xau_M_thieu_nguoi_chot():
    van = tieu_chi(muc_do().replace("(người dùng)", ""))
    assert any("thiếu `(người dùng)`" in x for x in kiem_tieu_chi(van))
    van = tieu_chi(muc_do().replace("(người dùng)", "(trợ lý)"))
    assert any("thiếu `(người dùng)`" in x for x in kiem_tieu_chi(van))
    # (leader) chỉ hợp lệ khi người dùng giao, kèm lời họ (xem test kế)
    assert kiem_tieu_chi(tieu_chi(muc_do().replace("(người dùng)", GIAO))) == []


GIAO = '(leader — người dùng giao: *"cứ chọn ngưỡng theo bạn"*)'


def test_leader_phai_mang_loi_nguoi_dung_giao_khong_duoc_tran_trui():
    """Quyết định của leader 25/11/2026 (thu hẹp, không phải câu hỏi mới): dòng 8 đầu tệp
    vẫn là luật — mọi M# là `(người dùng)`; `(leader)` chỉ ở chỗ người dùng đã giao quyết
    định ấy và dòng phải mang lời họ."""
    tran = tieu_chi(muc_do().replace("(người dùng)", "(leader)"))
    assert any("người dùng giao" in x for x in kiem_tieu_chi(tran)), kiem_tieu_chi(tran)
    for xau in ('(leader — người dùng giao: *""*)', '(leader — người dùng giao: *"ok"*)',
                '(leader — người dùng giao)', '(leader — người dùng giao: cứ chọn ngưỡng theo bạn)'):
        van = tieu_chi(muc_do().replace("(người dùng)", xau))
        assert any("thiếu" in x for x in kiem_tieu_chi(van)), xau
    assert kiem_tieu_chi(tieu_chi(muc_do().replace("(người dùng)", GIAO))) == []


def test_xau_M_khong_neu_diem_so_sanh():
    van = tieu_chi("## ĐO 38 — x\n\n- **M1** (người dùng)\n")
    assert any("không nêu điểm so sánh" in x for x in kiem_tieu_chi(van))


def test_xau_ma_M_trung_va_ma_B_trung():
    van = tieu_chi(muc_do(m=("M1", "M1")))
    assert any("M# trùng" in x for x in kiem_tieu_chi(van))
    van = tieu_chi(muc_do(b=("B1", "B1")))
    assert any("B# trùng" in x for x in kiem_tieu_chi(van))


def test_xau_tieu_de_trung():
    van = tieu_chi(muc_do(), muc_do(ten="bản bổ sung"))
    assert any("xuất hiện 2 lần" in x for x in kiem_tieu_chi(van))
    # hậu tố chữ là TÊN KHÁC, không phải tiêu đề trùng
    van = tieu_chi(muc_do(), muc_do(hau_to="b", m=(), b=(), them="**Nhãn:** Sau khi nhìn\n"))
    assert kiem_tieu_chi(van) == []


def test_hau_to_chu_phai_la_Sau_khi_nhin_va_khong_M():
    ok = muc_do(hau_to="b", m=(), b=(), them="**Nhãn:** Sau khi nhìn\n")
    assert kiem_tieu_chi(tieu_chi(ok)) == []
    thieu = muc_do(hau_to="b", m=(), b=())
    assert any("thiếu dòng `**Nhãn:** Sau khi nhìn`" in x for x in kiem_tieu_chi(tieu_chi(thieu)))
    co_m = muc_do(hau_to="b", m=("M1",), b=(), them="**Nhãn:** Sau khi nhìn\n")
    assert any("không được có dòng" in x for x in kiem_tieu_chi(tieu_chi(co_m)))


def test_sua_tot_va_moi_truong_thieu_deu_do():
    assert kiem_tieu_chi(tieu_chi(muc_do(them=sua()))) == []
    for truong in ("Người chốt", "Đã thấy", "Chưa đọc gì", "Commit tới origin/main"):
        loi = kiem_tieu_chi(tieu_chi(muc_do(them=sua(bo=f"**{truong}:**"))))
        assert any(f"`**{truong}:**`" in x for x in loi), (truong, loi)


def test_sua_huong_sai_hoac_thieu_va_noi_thieu_cau():
    loi = kiem_tieu_chi(tieu_chi(muc_do(them=sua(huong="tuỳ ý"))))
    assert any("thiếu `**Hướng:**" in x for x in loi), loi
    loi = kiem_tieu_chi(tieu_chi(muc_do(them=sua(noi=False))))
    assert any("thiếu câu" in x and CAU_NOI in x for x in loi), loi
    assert any("thiếu câu" in x and CAU_KET_CUC in x for x in loi), loi
    # không có điều "nới" thì không đòi hai câu
    khong_noi = sua(noi=False, huong="siết")
    assert kiem_tieu_chi(tieu_chi(muc_do(them=khong_noi))) == []


def test_sua_khong_co_dieu_khoan_va_sai_so():
    loi = kiem_tieu_chi(tieu_chi(muc_do(them="### SỬA ĐO 38\n\n**Người chốt:** leader\n")))
    assert any("không có dòng điều khoản" in x for x in loi)
    loi = kiem_tieu_chi(tieu_chi(muc_do(them=sua().replace("SỬA ĐO 38", "SỬA ĐO 39"))))
    assert any("nằm trong mục ĐO 38" in x for x in loi)


def test_thang_nhan_tot_va_xau():
    goc = muc_do("38")
    m2 = ("## ĐO 39 — x\n\n- **M1** " + DIEM + " (thăng từ ĐO 38 B1; dữ liệu mới: dòng hạt 7 chưa dùng) " + GIAO + "\n")
    assert kiem_tieu_chi(tieu_chi(goc, m2)) == []
    # trong CHÍNH ĐO sinh ra con số
    cung = ("## ĐO 38 — x\n\n- **M1** " + DIEM + " (thăng từ ĐO 38 B1; dữ liệu mới: dòng hạt 7 chưa dùng) (người dùng)\n"
            "- **B1** phụ\n")
    assert any("chỉ được từ một ĐO TRƯỚC" in x for x in kiem_tieu_chi(tieu_chi(cung)))
    # thiếu `dữ liệu mới`
    thieu = m2.replace("; dữ liệu mới: dòng hạt 7 chưa dùng", "")
    assert any("sai khuôn" in x for x in kiem_tieu_chi(tieu_chi(goc, thieu)))
    # `dữ liệu mới:` có chữ nhưng rỗng ruột (< 10 ký tự)
    ngan = m2.replace("dòng hạt 7 chưa dùng", "có")
    assert any("sai khuôn" in x for x in kiem_tieu_chi(tieu_chi(goc, ngan)))
    # mã B# không có ở ĐO nguồn
    la =m2.replace("38 B1", "38 B9")
    assert any("B9 không có ở phần ký" in x for x in kiem_tieu_chi(tieu_chi(goc, la)))
    # nguồn ≤ 37 không có mã B#: chỉ nhận chữ
    cu = m2.replace("ĐO 38 B1", "ĐO 34 B1")
    assert any("chưa có mã B#" in x for x in kiem_tieu_chi(tieu_chi(goc, cu)))
    chu = m2.replace("ĐO 38 B1", "ĐO 34 Báo kèm")
    assert kiem_tieu_chi(tieu_chi(goc, chu)) == []


# ═══ B. PHẠM VI: CHỈ ĐO >= 38 ═══════════════════════════════════════════

def test_ĐO_le_37_bi_bo_qua_ke_ca_khi_xau():
    xau37 = "## ĐO 37 — tệ\n\n- **M1** (x)\n- **M1** (x)\n### SỬA ĐO 37\n"
    van = tieu_chi(xau37, muc_do())
    muc, bo = doc_tieu_chi(van)
    assert [t for t, *_ in muc] == ["ĐO 38"]
    assert bo == ["ĐO 37"]
    assert kiem_tieu_chi(van) == []


def test_ngưỡng_la_38_dung_ranh_gioi():
    # 37 bỏ, 38 quét (mẫu 38 XẤU phải lộ), 38b quét như ĐO 38
    xau38 = "## ĐO 38 — x\n\nkhông có dòng M nào\n"
    assert kiem_tieu_chi(tieu_chi("## ĐO 37 — x\n\nkhông có dòng M\n")) == []
    assert kiem_tieu_chi(tieu_chi(xau38)) != []


def test_ten_M0_den_M9_cua_ĐO_24_va_tieu_de_M_khong_lam_do():
    do24 = "## ĐO 24 — cũ\n\n- **M0a.** gì đó\n### M0 — x\n### M9 — y\n- **M1** hai lần\n- **M1** hai lần\n"
    them = "### M0 — tiêu đề có tên M0 ở ĐO mới\n"
    van = tieu_chi(do24, muc_do(them=them))
    assert kiem_tieu_chi(van) == []
    muc, bo = doc_tieu_chi(van)
    assert bo == ["ĐO 24"] and ma_phan_ky(muc[0][3])[0] == {"M1"}


def test_khoi_ma_va_dong_trich_khong_tinh():
    # ĐO 38 chỉ có dòng M trong khối mã hoặc dòng `> `: không có phần ký
    trong_rao = "## ĐO 38 — x\n\n```markdown\n- **M1** " + DIEM + " (người dùng)\n```\n"
    assert any("không có dòng" in x for x in kiem_tieu_chi(tieu_chi(trong_rao)))
    trong_trich = "## ĐO 38 — x\n\n> - **M1** " + DIEM + " (người dùng)\n"
    assert any("không có dòng" in x for x in kiem_tieu_chi(tieu_chi(trong_trich)))
    # tiêu đề ĐO 38 nằm TRONG khối mã không là mục
    van = tieu_chi("```\n## ĐO 38 — mẫu trong rào\n```\n")
    assert doc_tieu_chi(van)[0] == []
    # rào 4 dấu bọc rào 3 dấu: rào ngắn bên trong không đóng nhầm
    long = "````markdown\n```\n## ĐO 38 — mẫu\n```\n````\n"
    assert doc_tieu_chi(tieu_chi(long))[0] == []
    # CRLF
    assert kiem_tieu_chi(tieu_chi(muc_do()).replace("\n", "\r\n")) == []


def test_bo_khoi_ma_va_trich_giu_so_dong_va_chi_bo_dung_thu():
    """Gọi thẳng hàm quét: các neo `^` của bộ đọc đã tự loại dòng `> `, nên chỉ
    phép thử TRỰC TIẾP mới giữ được việc bỏ dòng trích (đột biến bỏ nó sống sót
    nếu chỉ thử qua bộ đọc — phát hiện khi đục, 25/11/2026)."""
    van = ("a\n> trích\n```x\nrào\n```\n  > trích thụt\nb\n"
           "    > bốn dấu cách là mã thụt\n~~~\nrào\n~~~\nc")
    ra = bo_khoi_ma_va_trich(van).split("\n")
    assert len(ra) == len(van.split("\n"))
    assert [x for x in ra if x] == ["a", "b", "    > bốn dấu cách là mã thụt", "c"]
    assert bo_khoi_ma_va_trich("a\r\n> b\r\nc") == "a\n\nc"


def test_rao_khong_dong_thi_NO_khong_nuot_im():
    with pytest.raises(ValueError, match="không đóng"):
        doc_tieu_chi("# a\n```\n## ĐO 38 — x\n")


# ═══ C. MỤC KẾT QUẢ (STATE) ═════════════════════════════════════════════

def kq_loi(muc_ky=None, kq=None, git=None):
    return kiem_state(state(kq if kq is not None else ket_qua()),
                      tieu_chi(muc_ky if muc_ky is not None else muc_do()),
                      git or git_gia(0))


def test_ket_qua_tot_khong_loi():
    assert kq_loi() == []


def test_thu_tu_ba_khoi():
    loi = kq_loi(kq=ket_qua(thu_tu=["Báo kèm", "Đã khai", "Sau khi nhìn"]))
    assert any("đúng thứ tự" in x for x in loi), loi
    loi = kq_loi(kq=ket_qua(thu_tu=["Đã khai", "Sau khi nhìn"]))
    assert any("đúng thứ tự" in x for x in loi), loi


def test_khoi_rong_phai_ghi_Khong_co():
    loi = kq_loi(kq=ket_qua(skn=""))
    assert any("rỗng" in x for x in loi), loi
    assert kq_loi(kq=ket_qua(ma_kem=())) == []   # `*Không có*`


def test_ma_o_khoi_phai_thuoc_phan_ky():
    loi = kq_loi(kq=ket_qua(ma_khai=("M1", "M7")))
    assert any("M7 ở khối Đã khai không có ở phần ký" in x for x in loi), loi
    loi = kq_loi(kq=ket_qua(ma_kem=("B1", "B7")))
    assert any("B7 ở khối Báo kèm không có ở phần ký" in x for x in loi), loi
    # mã chỉ ở TIÊU ĐỀ khối (không có dòng trong khối)
    k = ket_qua().replace("### Đã khai (M1)", "### Đã khai (M1, M7)")
    assert any("M7" in x for x in kq_loi(kq=k))


def test_moi_M_cua_phan_ky_phai_co_mat_hay_khai_ly_do():
    ky = muc_do(m=("M1", "M2"))
    loi = kq_loi(ky, ket_qua(ma_khai=("M1",)))
    assert any("M2 của phần ký không có" in x for x in loi), loi
    ly_do = "M2 — không báo được vì dòng hạt chưa chạy xong trong lượt này"
    assert kq_loi(ky, ket_qua(ma_khai=("M1",), sau_khai_dong=ly_do)) == []
    ngan = "M2 — không báo được vì hỏng"
    loi = kq_loi(ky, ket_qua(ma_khai=("M1",), sau_khai_dong=ngan))
    assert any("ngắn hơn 30" in x for x in loi), loi


def test_khoi_Sau_khi_nhin_khong_co_ma_hay_KET_CUC():
    for mau in ("- **M1** lén vào đây", "**B1** cũng không", "**M2** trần"):
        assert any("mã M#/B#" in x for x in kq_loi(kq=ket_qua(skn=mau))), mau
    loi = kq_loi(kq=ket_qua(skn="đầu mối; KẾT CỤC: ĐẠT"))
    assert any("KẾT CỤC" in x for x in loi), loi
    # nói về kết cục bằng chữ thường thì không sao
    assert kq_loi(kq=ket_qua(skn="đầu mối cho một ĐO sau; không quyết định kết cục")) == []


def test_thieu_dong_sha():
    k = ket_qua().replace("**Khai ở commit:** abc1234\n", "")
    assert any("thiếu dòng `**Khai ở commit:**" in x for x in kq_loi(kq=k))
    k = ket_qua().replace("**Chạy trên origin/main:** def5678\n", "")
    assert any("thiếu dòng `**Chạy trên origin/main:**" in x for x in kq_loi(kq=k))


def test_to_tien_phai_ra_0_neu_khong_do():
    loi = kq_loi(git=git_gia(rc=1))
    assert any("KHÔNG là tổ tiên" in x for x in loi), loi
    loi = kq_loi(git=git_gia(rc=128))
    assert any("chưa kiểm được" in x for x in loi), loi
    loi = kq_loi(git=git_gia(nong="true"))
    assert any("chưa kiểm được" in x and "NÔNG" in x for x in loi), loi


def test_loi_thoat_bang_chung_yeu_phai_nhan_va_co_ly_do():
    # đúng khuôn: không đòi tổ tiên (git ra 1 vẫn xanh), tiêu đề mang nhãn
    assert kq_loi(kq=ket_qua(yeu=True), git=git_gia(rc=1)) == []
    # có dòng yếu mà tiêu đề không mang nhãn
    k = ket_qua(yeu=True).replace(" (bằng chứng yếu)", "")
    assert any("khi và chỉ khi" in x for x in kq_loi(kq=k, git=git_gia(rc=1)))
    # tiêu đề mang nhãn mà không có dòng khai
    k = ket_qua(dau_khai="Đã khai (M1) (bằng chứng yếu)")
    assert any("khi và chỉ khi" in x for x in kq_loi(kq=k, git=git_gia(rc=1)))
    # lý do ngắn
    k = ket_qua(yeu=True).replace("vì khai trước lượt chạy nhưng PR chưa gộp được", "vì lười")
    assert any("ngắn hơn 30" in x for x in kq_loi(kq=k, git=git_gia(rc=1)))
    # sai khuôn
    k = ket_qua(yeu=True).replace("commit cục bộ — vì", "giờ commit —")
    assert any("sai khuôn" in x for x in kq_loi(kq=k, git=git_gia(rc=1)))


def test_ket_qua_khong_co_phan_ky_va_mo_hai_lan():
    loi = kiem_state(state(ket_qua(k="39")), tieu_chi(muc_do()), git_gia(0))
    assert any("không có mục `## ĐO 39 —`" in x for x in loi), loi
    loi = kiem_state(state(ket_qua(), ket_qua()), tieu_chi(muc_do()), git_gia(0))
    assert any("mở 2 lần" in x for x in loi), loi


def test_ket_qua_le_37_va_khoi_trong_rao_bi_bo_qua():
    xau37 = "**Kết quả ĐO 37:**\n\nlung tung, không có ba khối\n"
    muc, bo = doc_ket_qua(state(xau37, ket_qua()))
    assert [k for k, _ in muc] == [38] and bo == [37]
    assert kiem_state(state(xau37), tieu_chi(muc_do()), git_gia(0)) == []
    mau_trong_rao = "```markdown\n**Kết quả ĐO 38:**\nlung tung\n```\n"
    assert doc_ket_qua(state(mau_trong_rao))[0] == []
    mau_trich = "> **Kết quả ĐO 38:**\n> lung tung\n"
    assert doc_ket_qua(state(mau_trich))[0] == []


def test_mau_nhan_nam_trong_so_ky_HON_CHUC_khoi_STATE_khong_phai_ket_qua():
    # mục mở bằng chữ khác (vd `## Kết quả ĐO 38` cũ) không được đọc
    cu = "## Kết quả ĐO 38\n\nlung tung\n"
    assert doc_ket_qua(state(cu))[0] == []


# ═══ D. TỔ TIÊN: repo tạm, và lịch sử THẬT ═════════════════════════════

def _g(repo, *a):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *a], cwd=str(repo),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"git {' '.join(a)}: {r.stderr}"
    return r.stdout.strip()


def _commit(repo, ten, noi_dung):
    (repo / ten).write_text(noi_dung, encoding="utf-8")
    _g(repo, "add", "-A")
    _g(repo, "commit", "-q", "-m", noi_dung)
    return _g(repo, "rev-parse", "HEAD")


@pytest.fixture
def kho(tmp_path):
    """main: c1 ← c2 ; nhánh khai: c1 ← f1 ; gộp --no-ff = m ; squash = s (nhánh phụ)."""
    r = tmp_path / "kho"
    r.mkdir()
    _g(r, "init", "-q", "-b", "main")
    c1 = _commit(r, "a.txt", "c1")
    _g(r, "checkout", "-q", "-b", "khai")
    f1 = _commit(r, "khai.txt", "f1")
    _g(r, "checkout", "-q", "main")
    c2 = _commit(r, "a.txt", "c2")
    _g(r, "branch", "squash", c2)
    _g(r, "merge", "-q", "--no-ff", "-m", "gop", "khai")
    m = _g(r, "rev-parse", "HEAD")
    _g(r, "checkout", "-q", "squash")
    _g(r, "merge", "-q", "--squash", "khai")
    _g(r, "commit", "-q", "-m", "squash")
    s = _g(r, "rev-parse", "HEAD")
    return {"r": r, "c1": c1, "f1": f1, "c2": c2, "m": m, "s": s}


def _gr(repo):
    return lambda *a: git_that(*a, cwd=repo)


def test_to_tien_tren_repo_tam_gop_merge(kho):
    g = _gr(kho["r"])
    # khai ở f1, chạy ở c2 (main TRƯỚC khi PR gộp): f1 chưa tới main → yếu
    assert la_to_tien(kho["f1"], kho["c2"], g) is False
    # chạy ở m (SAU gộp --no-ff): f1 là tổ tiên
    assert la_to_tien(kho["f1"], kho["m"], g) is True
    # c1 là tổ tiên của mọi thứ; chiều ngược lại thì không
    assert la_to_tien(kho["c1"], kho["m"], g) is True
    assert la_to_tien(kho["m"], kho["c1"], g) is False


def test_to_tien_squash_ra_1_oan_va_luat_giu_merge(kho):
    """Squash KHÔNG giữ f1 làm tổ tiên: lý do luật đòi `--merge` (SKILL.md Bước 5)."""
    assert la_to_tien(kho["f1"], kho["s"], _gr(kho["r"])) is False


def test_to_tien_sha_la_hay_sai_dang_thi_NO(kho):
    g = _gr(kho["r"])
    with pytest.raises(ChuaKiemDuoc, match="mã 128"):
        la_to_tien("deadbee", kho["m"], g)
    for xau in ("--all", "HEAD", "zzzzzzz", "abc12", ""):
        with pytest.raises(ChuaKiemDuoc, match="dạng"):
            la_to_tien(xau, kho["m"], g)


def test_to_tien_repo_nong_thi_NO_khong_xanh_im(kho, tmp_path):
    nong = tmp_path / "nong"
    _g(tmp_path, "clone", "-q", "--depth", "1", kho["r"].resolve().as_uri(), str(nong))
    assert _g(nong, "rev-parse", "--is-shallow-repository") == "true"
    with pytest.raises(ChuaKiemDuoc, match="NÔNG"):
        la_to_tien(kho["c1"], kho["m"], _gr(nong))


def test_to_tien_khong_co_git_thi_NO():
    with pytest.raises(ChuaKiemDuoc):
        la_to_tien("abc1234", "def5678", lambda *a: (127, ""))


# Ca THẬT, bất biến theo thời gian (đo 25/11/2026): `981aa25` là khai trước của
# BƯỚC 294, `64ec66b` là merge của PR của nó; `64ec66b^1` = `19ec8b3` là `main`
# NGAY TRƯỚC khi PR gộp. Giờ commit cục bộ của `981aa25` TRƯỚC lượt chạy, mà nó
# tới `main` SAU — tổ tiên nói đúng điều giờ commit không nói được.
SHA = {
    "khai_294": "981aa25311fdb757906a694568482916a34bb949",
    "main_truoc_294": "19ec8b34290d24977ff96ca96cacda5864f8fefc",
    "merge_294": "64ec66bdc4456311cce7e3d77916b7ea063c279f",
    "khai_37": "0f6424d34fdb021d5adec88530b90a974f8287a0",
    "main_truoc_37": "58c1d2ff416ecf056e5beac1231767e1bc9ac3b7",
    "merge_37": "86d43d1b06f99ea3f7d807d61f0f67c6b3e29b61",
}


def test_to_tien_tren_LICH_SU_THAT():
    """Repo thật. ĐỎ ở repo nông (CI thiếu `fetch-depth: 0`) — chủ ý."""
    assert la_to_tien(SHA["khai_294"], SHA["main_truoc_294"]) is False
    assert la_to_tien(SHA["khai_294"], SHA["merge_294"]) is True
    assert la_to_tien(SHA["khai_37"], SHA["main_truoc_37"]) is False
    assert la_to_tien(SHA["khai_37"], SHA["merge_37"]) is True


# ═══ E. FILE THẬT ═══════════════════════════════════════════════════════

def test_file_that_hom_nay_khong_co_muc_nao_ge_38_va_ĐO_le_37_duoc_dem():
    """Ghim số mục bị bỏ qua. Số ĐO ≤ 37 KHÔNG tăng nữa (đo 25/11/2026, lệnh:
    `grep -cE "^## ĐO [0-9]+[a-z]? —" docs/TIEU-CHI-DOC-TRUOC.md` ra 42)."""
    muc, bo = doc_tieu_chi(TIEU_CHI.read_text(encoding="utf-8"))
    ten = sorted({t for t in bo}, key=lambda t: (int(re.search(r"\d+", t).group()), t))
    assert [t for t, *_ in muc] == [], "đã có ĐO >= 38: gác phải canh nó (xem test mẫu)"
    assert len(bo) == 42 and len(ten) == 40, (len(bo), len(ten))
    assert bo == sorted(bo)


def test_file_that_sach_theo_luat():
    van = TIEU_CHI.read_text(encoding="utf-8")
    assert kiem_tieu_chi(van) == []
    assert kiem_state(STATE.read_text(encoding="utf-8"), van) == []


def test_khoi_luat_nam_o_phan_mo_dau_va_cung_chu_voi_gac():
    """Luật ở TIEU-CHI và gác ở đây không được trôi ra khỏi nhau: mọi chữ
    gác đòi phải CÓ trong khối luật. Khối nằm sau `---` đầu, TRƯỚC `## Đính
    chính` và `## ĐO 1` — thêm vào cuối là chữ nối vào thân ĐO 37."""
    van = TIEU_CHI.read_text(encoding="utf-8").replace("\r\n", "\n")
    tieu_de = "## Nhãn của con số — áp dụng từ ĐO 38"
    assert van.count(tieu_de) == 1
    vt = van.index(tieu_de)
    assert van.index("\n---\n") < vt < van.index("## Đính chính trước tiên") < van.index("## ĐO 1 —")
    khoi = van[vt: van.index("## Đính chính trước tiên")]
    cua_gac = [
        "Đã khai M#", "Báo kèm", "Sau khi nhìn", "`- **M1** <điểm so sánh> (người dùng)`",
        "`(leader)`", "`(leader — người dùng giao: *\"…\"*)`", "`(leader)` trơ trụi bị gác từ chối",
        "con đường DUY NHẤT được phép sửa", "chỉ có một ĐO mới", "`- **B1** …`", "git merge-base --is-ancestor", "bằng chứng yếu",
        "**Kết quả ĐO <n>:**", "### Đã khai (M1, …)", "### Báo kèm (B1, …)", "### Sau khi nhìn",
        "**Khai ở commit:**", "**Chạy trên origin/main:**",
        "**Khai trước bằng:** commit cục bộ — vì <lý do ≥ 30 ký tự>",
        "M# — không báo được vì <lý do ≥ 30 ký tự>", "thăng từ ĐO <n> B1; dữ liệu mới:", "### SỬA ĐO <n>",
        "**Hướng:**", "**Người chốt:**", "**Đã thấy:**", "**Chưa đọc gì:**",
        "**Commit tới origin/main:**", CAU_NOI, CAU_KET_CUC, "**Nhãn:** Sau khi nhìn",
        "`--merge`", "tests/test_ket_qua_do_co_nhan.py",
    ]
    thieu = [x for x in cua_gac if x not in khoi]
    assert thieu == [], thieu
    for lien_quan in ("nới | siết | trung tính", "KHÔNG phải bằng chứng"):
        assert lien_quan in khoi, lien_quan
