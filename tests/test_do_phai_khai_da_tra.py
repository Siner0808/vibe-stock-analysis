"""Mỗi phép đo phải KHAI đã tra trùng hay chưa — lỗ hổng của lỗi 41 và 53.

VÌ SAO CÓ FILE NÀY
──────────────────
Hai lần dự án thiết kế một phép đo mà không tra xem **nó đã được đo chưa**:

```
loi 41  12/09/2026  DO 5 la ban TRUNG cua BUOC 25 — 88,8 phut lang phi
loi 53  14/09/2026  DO 8 khong tra BUOC 8, von da dinh luong meo mo don bay
                    tu 31/08. Lan nay THOAT — DO 8 hoa ra khong trung —
                    nhung no thoat VI MAY, khong vi da tra.
```

Cả hai lần, thứ tìm ra chỗ trùng đều là **NotebookLM, sau khi việc đã
xong**. Không cơ chế nào của repo hỏi câu ấy.

KIỂM VAI TRÒ, KHÔNG KIỂM SỰ XUẤT HIỆN
─────────────────────────────────────
Một gác chấp nhận *"thân mục có nhắc chữ `BƯỚC n` nào đó"* sẽ **cho ĐO 8
lọt** — mục ấy nhắc `BƯỚC 60` trong phần giới hạn, và vẫn là mục đã bỏ
qua `BƯỚC 8`. Đếm được 14/09/2026: 5/11 mục có nhắc một số BƯỚC, và ít
nhất một trong năm là nhắc vì lý do khác hẳn.

Nên gác này đòi một **dòng khai riêng**, không đòi một chữ xuất hiện —
cùng bài học lỗi 30/35/36/38/44.

KHÔNG CẤM, BUỘC NÓI RA
──────────────────────
Hai hình dạng hợp lệ, và **cả hai đều là lời khai**:

```
**Đã tra trùng:** BƯỚC 8 · BƯỚC 25 — <tra ra gì>
**Không khai được là đã tra vì:** <sự thật>
```

Hình thứ hai không phải cửa sau: nó biến *"không ai biết có tra hay
không"* thành một con số **đếm được**. Cùng cơ chế `# bia-ok:` ·
`# lenh-xau-ok:` · `khong_soat_vi`.

ĐIỀU GÁC NÀY KHÔNG LÀM — nói thẳng, bài học lỗi 44
──────────────────────────────────────────────────
Nó **không** biết lời khai có đúng không. Khai `BƯỚC 8` mà chưa đọc BƯỚC 8
thì nó vẫn xanh. Thứ duy nhất nó chặn: **một phép đo đã ký mà không ai nói
được đã tra trùng hay chưa.**

Vế mà nó kiểm được bằng máy: mỗi `BƯỚC n` được khai phải **CÓ THẬT** trong
`docs/STATE.md`. Một số hiệu bịa không lọt.
"""
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tests"))

# Dùng lại máy cắt mục đã có thay vì chép 10 dòng sang đây: hai bản sao
# của một phép cắt sẽ trôi ra khỏi nhau, và bảng lỗi có sẵn một dòng cho
# đúng hình dạng đó (lỗi 41 — không tìm lời giải sẵn có).
from test_phep_do_neu_dung_cu import cac_muc  # noqa: E402

TIEU_CHI = GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md"
STATE = GOC / "docs" / "STATE.md"

DAI_TOI_THIEU = 30

RE_DA_TRA = re.compile(r"\*\*Đã tra trùng:\*\*(.+)")
RE_CHUA_TRA = re.compile(r"\*\*Không khai được là đã tra vì:\*\*(.+)")
RE_SO_BUOC = re.compile(r"BƯỚC\s+(\d+)")

# KHÔNG có danh sách "từ chung chung" ở đây, và việc đó là CÓ CHỦ ĐÍCH.
# Bản đầu có một danh sách như thế; vòng đục thử chỉ ra nó là MÃ CHẾT:
# phần tử dài nhất 10 ký tự, ngưỡng độ dài 30, và phép đo độ dài chạy
# TRƯỚC — nên nhánh ấy không bao giờ quyết định được gì.
#
# Đó là khuyết tật đã tìm ra và sửa SÁNG CÙNG NGÀY ở
# `tools/soat_lenh_tai_lieu.py`, rồi chép lại y nguyên buổi chiều.
# Ngưỡng 30 ký tự tự nó đã buộc phải cụ thể.


def ly_do_hop_le(ly_do: str) -> bool:
    """Một lời khai có đủ tư cách là lời khai không. Hàm THUẦN.

    Ngưỡng ghim bằng LITERAL, không đọc từ module này: một đột biến hằng
    số đọc-từ-chính-mình làm mù CẢ HAI vế, và dự án đã trả giá hai lần
    trong một ngày cho đúng hình dạng ấy (BƯỚC 58 và BƯỚC 60).
    """
    s = " ".join(ly_do.split()).strip().rstrip(".")
    return len(s) >= 30


def buoc_co_that(van_state: str) -> set[str]:
    """Số hiệu mọi BƯỚC có thật, đọc từ TIÊU ĐỀ của `docs/STATE.md`.

    Đọc tiêu đề chứ không đọc mọi chỗ chữ `BƯỚC` xuất hiện: thân các mục
    nhắc chéo nhau liên tục, nên quét cả file thì mọi số đều "có thật".
    """
    return set(re.findall(r"^##\s*BƯỚC\s+(\d+)", van_state, re.M))


def loi_cua_khai(loai: str, noi: str, buoc_that: set[str]) -> str | None:
    """Lời khai này hỏng ở đâu? `None` là đạt. Hàm THUẦN.

    Tách ra khỏi phần duyệt file vì hai phép kiểm dựa vào nó đều SỐNG SÓT
    đột biến khi chỉ chạy trên file thật: mọi mục trong `docs/` đều hợp
    lệ, nên bỏ hẳn phép phán đi cũng không có gì đỏ. Đúng lỗi 34 — một
    gác chỉ thấy đầu vào sạch là một gác chưa được thử.
    """
    if loai == "thieu":
        return "khong khai gi"
    if not ly_do_hop_le(noi):
        return f"noi dung qua ngan: {noi[:40]!r}"
    if loai == "da_tra":
        so = set(RE_SO_BUOC.findall(noi))
        if not so:
            return "khai 'da tra' ma khong neu BUOC nao"
        la = sorted(so - buoc_that, key=int)
        if la:
            return f"khai BUOC khong co trong docs/STATE.md: {la}"
    return None


def khai_cua_muc(than: str) -> tuple[str, str]:
    """(loại, nội dung) — `da_tra` · `chua_tra` · `thieu`. Hàm THUẦN."""
    m = RE_DA_TRA.search(than)
    if m:
        return "da_tra", m.group(1).strip()
    m = RE_CHUA_TRA.search(than)
    if m:
        return "chua_tra", m.group(1).strip()
    return "thieu", ""


# ───────────────────────── phép phán, HAI CHIỀU ─────────────────────────

def test_MAY_DO_tu_chung_minh_no_PHAN_BIET_duoc_ba_hinh_dang():
    """Mẫu dựng tay. Một gác chỉ chạy trên đầu vào sạch thì mọi phép nới
    đều sống sót (lỗi 34)."""
    assert khai_cua_muc("**Đã tra trùng:** BƯỚC 8 — khong trung")[0] == "da_tra"
    assert khai_cua_muc("**Không khai được là đã tra vì:** x")[0] == "chua_tra"
    assert khai_cua_muc("mot muc nhac BƯỚC 60 trong phan gioi han")[0] == "thieu"
    # Day la ca DO 8 that: nhac mot so BUOC ma KHONG phai loi khai.
    assert khai_cua_muc("bai hoc BƯỚC 60: mot phep do chi chay duoc mot lan"
                        )[0] == "thieu"
    print("PASS  phan biet duoc loi KHAI voi chu BUOC xuat hien trong van xuoi")


def test_LY_DO_hop_le_tu_chung_minh_HAI_CHIEU():
    # Hai ve ghim bang LITERAL o HAI cho khac nhau: hang so o dau file
    # va con so trong `ly_do_hop_le`. Doi mot ben ma khong doi ben kia
    # -> do. Do la cach duy nhat vua tranh duoc "mu ca hai ve" (BUOC 58,
    # BUOC 60) vua khong de hang so tro thanh do trang tri.
    assert DAI_TOI_THIEU == 30, "hang so khai va nguong that da troi"
    assert not ly_do_hop_le("")
    assert not ly_do_hop_le("x" * 29)
    assert ly_do_hop_le("x" * 30)
    assert ly_do_hop_le("luot do chay truoc khi co quy uoc nay, va khong "
                        "truy lai duoc bang git")
    print(f"PASS  nguong {DAI_TOI_THIEU} ky tu + tu vung chung chung, hai chieu")


def test_BUOC_CO_THAT_chi_doc_TIEU_DE_chu_khong_doc_ca_file():
    """Thân các mục nhắc chéo nhau liên tục. Quét cả file thì MỌI số đều
    "có thật", và vế máy-kiểm-được của gác này tan ra.

    Mẫu dựng tay, không đọc file thật (lỗi 34).
    """
    mau = ("## BƯỚC 7 — mot muc that\n"
           "than muc nay nhac BƯỚC 999 va BƯỚC 8 trong van xuoi\n"
           "## BƯỚC 8 — mot muc that nua\n")
    that = buoc_co_that(mau)
    assert that == {"7", "8"}, f"doc ra {sorted(that)}, phai la 7 va 8"
    assert "999" not in that, "quet ca file nen mot so BIA cung 'co that'"
    print("PASS  chi doc tieu de — so nhac trong van xuoi khong thanh 'co that'")


def test_MOI_MUC_DO_deu_KHAI_da_tra_trung_hay_chua():
    """Phép kiểm chính. Thêm một mục ĐO mà không khai → đỏ."""
    muc = cac_muc(TIEU_CHI.read_text(encoding="utf-8"))
    assert muc, "khong cat duoc muc DO nao — may cat hong"
    thieu = [ten for ten, than in muc if khai_cua_muc(than)[0] == "thieu"]
    assert not thieu, (
        f"Cac muc sau khong khai da tra trung hay chua: {thieu}\n\n"
        f"Loi 41 (DO 5 trung BUOC 25, mat 88,8 phut) va loi 53 (DO 8 bo qua "
        f"BUOC 8, thoat vi may). Viet MOT trong hai dong:\n"
        f"  **Da tra trung:** BUOC n - <tra ra gi>\n"
        f"  **Khong khai duoc la da tra vi:** <su that>")
    print(f"PASS  {len(muc)} muc DO deu khai da tra trung hay chua")


def test_MOI_SO_BUOC_duoc_khai_deu_CO_THAT_trong_STATE():
    """Vế máy kiểm được: một số hiệu bịa không lọt.

    Gác này KHONG biet loi khai co dung khong — xem docstring dau file.
    Nhung no biet `BƯỚC 999` la khong co that.
    """
    that = buoc_co_that(STATE.read_text(encoding="utf-8"))
    assert that, "khong doc duoc BUOC nao tu STATE — may doc hong"
    la = {}
    for ten, than in cac_muc(TIEU_CHI.read_text(encoding="utf-8")):
        loai, noi = khai_cua_muc(than)
        if loai != "da_tra":
            continue
        xau = sorted(set(RE_SO_BUOC.findall(noi)) - that, key=int)
        if xau:
            la[ten] = xau
    assert not la, (
        f"khai BUOC khong co trong docs/STATE.md: {la}\n"
        f"BUOC co that: {len(that)} muc, lon nhat {max(that, key=int)}")
    print(f"PASS  moi so BUOC duoc khai deu co that ({len(that)} BUOC trong STATE)")


def test_PHEP_PHAN_tu_chung_minh_no_bat_duoc_BON_hinh_dang_hong():
    """Mẫu dựng tay, HAI CHIỀU. Đây là phép kiểm mà bốn đột biến sống sót
    ở lượt đục đầu tiên đã đòi — file thật không có mục nào hỏng, nên bỏ
    hẳn phép phán đi cũng chẳng có gì đỏ (lỗi 34).
    """
    that = {"8", "25"}
    dai = "x" * 40

    XAU = [
        ("thieu", "", "khong khai gi"),
        ("da_tra", "BƯỚC 8 ngan", "noi dung qua ngan"),
        ("da_tra", dai, "khong neu BUOC nao"),
        ("da_tra", "BƯỚC 999 " + dai, "BUOC khong co"),
        ("chua_tra", "ngan", "noi dung qua ngan"),
    ]
    for loai, noi, mong in XAU:
        loi = loi_cua_khai(loai, noi, that)
        assert loi is not None, f"BO SOT mau xau: {(loai, noi[:30])}"
        assert mong.split()[0] in loi, (
            f"bat duoc nhung ly do sai: cho {mong!r}, nhan {loi!r}")

    TOT = [
        ("da_tra", "BƯỚC 8 · BƯỚC 25 — " + dai),
        ("chua_tra", dai),
    ]
    for loai, noi in TOT:
        assert loi_cua_khai(loai, noi, that) is None, \
            f"bat NHAM mau hop le: {(loai, noi[:30])}"
    print(f"PASS  bat {len(XAU)}/{len(XAU)} mau hong · "
          f"bo qua {len(TOT)}/{len(TOT)} mau dat")


def test_MOI_LOI_KHAI_TRONG_FILE_THAT_deu_dat():
    """Cùng phép phán, lần này chạy lên file thật."""
    that = buoc_co_that(STATE.read_text(encoding="utf-8"))
    hong = {}
    for ten, than in cac_muc(TIEU_CHI.read_text(encoding="utf-8")):
        loai, noi = khai_cua_muc(than)
        loi = loi_cua_khai(loai, noi, that)
        if loi:
            hong[ten] = loi
    assert not hong, f"loi khai khong dat: {hong}"
    print("PASS  moi loi khai trong file that deu dat")


def test_DEM_duoc_bao_nhieu_muc_KHONG_khai_duoc_la_da_tra():
    """Không phải phép chặn — phép ĐẾM.

    Hình dạng "không khai được" là cửa thoát, nên nó phải **đếm được**,
    nếu không cửa thoát thành chỗ trốn. Con số này là thước: nó phải đi
    xuống theo thời gian, và một phép đo MỚI rơi vào đó là đáng hỏi.
    """
    muc = cac_muc(TIEU_CHI.read_text(encoding="utf-8"))
    chua = [ten for ten, than in muc if khai_cua_muc(than)[0] == "chua_tra"]
    da = [ten for ten, than in muc if khai_cua_muc(than)[0] == "da_tra"]
    print(f"PASS  {len(da)}/{len(muc)} muc khai DA TRA · "
          f"{len(chua)} muc khong khai duoc: {chua}")
    assert len(da) + len(chua) == len(muc)
