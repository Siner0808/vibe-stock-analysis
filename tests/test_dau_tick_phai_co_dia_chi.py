"""Gác: một dấu ✅ trong bảng lỗi phải CHỈ ĐƯỢC một cơ chế CÓ THẬT.

VÌ SAO CÓ FILE NÀY
──────────────────
Bảng lỗi tự ghi **hai lần** một dấu ✅ hứa rộng hơn thứ nó giao — lỗi 44
và 47 — và `tools/doc_bang_loi.py` in kèm một cảnh báo cùng ý:
*"cột ✅ nói CÓ MỘT CÁI GÁC, không nói gác ấy BẮT ĐƯỢC"*.

Câu *"gác ấy có bắt được không"* **không đọc được từ văn bản**, và gác này
không giả vờ đọc được. Nó hỏi câu yếu hơn nhiều, nhưng trả lời được:

    mot dau ✅ co DIA CHI khong?

Địa chỉ = một đường dẫn git biết, một tên module, hoặc một tên `def`/
`class` có thật trong repo. Một dấu ✅ không trỏ vào đâu cả là một **lời
hứa**, không phải một cơ chế — và lời hứa thì không ai kiểm được.

ĐO TRƯỚC KHI DỰNG (15/09/2026)
──────────────────────────────
33 dòng mang ✅ · **3 dòng không có địa chỉ** — dòng 34 (không trỏ đâu
cả), 35 (*"chính công cụ ấy"*) và 42 (*"gác trên"*). Cả ba đã được viết
lại địa chỉ tường minh trong cùng PR, nên tỷ lệ bắt nhầm của luật này là
**0/33** tại lúc dựng. Đó là điều kiện để nó được dựng, không phải một
ghi chú thêm.

CÁI GÁC NÀY KHÔNG CANH GÌ
─────────────────────────
Nó **không** biết gác được trỏ tới có chạy không, có bắt được không, hay
có còn đúng không. Ba câu ấy vẫn chưa ai đóng. Nó chỉ làm một việc: **một
lời hứa không có địa chỉ thì không im lặng được nữa.**
"""
import ast
import functools
import re
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
BANG = GOC / ".claude/skills/quy-trinh-lam-viec/references/loi-da-mac.md"

#: Tên ngắn hơn ngưỡng này khớp bừa vào văn xuôi — `chay`, `doc`, `main`.
DAI_TOI_THIEU = 6


def _git(*t: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *t], cwd=str(GOC),
                          capture_output=True, text=True)


@functools.lru_cache(maxsize=1)
def dia_chi_co_that() -> frozenset[str]:
    """Mọi thứ trong repo mà một dòng bảng có thể TRỎ TỚI.

    Ba dạng, và dạng thứ ba là dạng hay bị bỏ sót nhất: tài liệu viết
    `va_an_toan.thay()` hay `test_moi_luat_deu_khai_NGUON` — một HÀM, chứ
    không phải một file. Bản đầu của phép đo này chỉ nhận đường dẫn đầy
    đủ và đọc 15/33 dòng thành "không có địa chỉ"; 12 trong số đó có địa
    chỉ thật. Lỗi 61.
    """
    r = _git("ls-files")
    assert r.returncode == 0, f"`git ls-files` that bai: {r.stderr.strip()}"
    duong = set(r.stdout.split())

    ra = set(duong)
    ra |= {p.rsplit("/", 1)[-1] for p in duong}
    ra |= {p.rsplit("/", 1)[-1][:-3] for p in duong if p.endswith(".py")}
    for p in duong:
        if not p.endswith(".py"):
            continue
        try:
            cay = ast.parse((GOC / p).read_text(encoding="utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for n in ast.walk(cay):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
                ra.add(n.name)

    sys.path.insert(0, str(GOC / "tools"))
    import cua_bash_an_toan as cb
    ra |= {t for t, _, _ in cb.LUAT}

    return frozenset(t for t in ra if len(t) >= DAI_TOI_THIEU)


def dong_bang(van: str) -> list[tuple[str, str]]:
    """`(số hiệu, cột "đã chặn bằng")` cho mỗi dòng MANG DẤU ✅.

    Đọc theo CỘT, không theo chữ ✅ xuất hiện ở đâu đó trong dòng: ký hiệu
    ấy nằm trong văn xuôi của nhiều ô khác.

    **Hàm THUẦN trên NỘI DUNG**, không tự đọc đĩa — nhờ vậy phép kiểm hai
    chiều ở dưới thử được bằng một bảng dựng tay mà không phải ghi đè file
    thật. Bản đầu của file này làm đúng điều đó và đã sửa: một test ghi vào
    file trong repo là đúng hình dạng đã gây đỏ giả nhiều lần.
    """
    ra = []
    for m in re.finditer(r"^\| (\d+) \|.*$", van, re.M):
        cot = [c.strip() for c in m.group(0).split(" | ")]
        if len(cot) >= 5 and cot[3] == "✅":
            ra.append((m.group(1), cot[4].rstrip("|").strip()))
    return ra


def co_dia_chi(chan_bang: str, dia_chi: frozenset[str]) -> bool:
    return any(t in chan_bang for t in dia_chi)


# ───────────────────────────── phép kiểm ─────────────────────────────

def test_MOI_dau_TICH_deu_tro_toi_mot_thu_CO_THAT():
    """Đo 15/09/2026: 33 dòng ✅, 0 dòng không địa chỉ sau lượt dọn."""
    dc = dia_chi_co_that()
    xanh = dong_bang(BANG.read_text(encoding="utf-8"))
    assert xanh, "khong doc duoc dong ✅ nao — may do hong, xem phep kiem duoi"

    treo = [(n, c[:120]) for n, c in xanh if not co_dia_chi(c, dc)]
    assert not treo, (
        "dau ✅ khong tro toi thu gi co that:\n  "
        + "\n  ".join(f"dong {n} | {c}" for n, c in treo)
        + "\nMot dau ✅ khong co dia chi la mot LOI HUA, khong phai co che. "
          "Neu ten cua no khong con ton tai thi do la mot dia chi CHET.")
    print(f"PASS  {len(xanh)} dong ✅, moi dong deu co dia chi")


def test_MAY_DO_tu_chung_minh_no_BAT_DUOC__hai_chieu():
    """Bài học **lỗi 34**, và nó vừa cắn chính phép đo này.

    Một gác chỉ chạy trên dữ liệu SẠCH thì mọi phép nới nó đều sống sót.
    Nên thử cả hai chiều trên đầu vào dựng tay.
    """
    dc = dia_chi_co_that()
    assert len(dc) > 500, (
        f"chi thu duoc {len(dc)} dia chi — tap qua nho, gac tren dang "
        f"kiem tren mot tap rong va se xanh voi moi dau vao")
    assert "va_an_toan" in dc and "doc_bang_loi" in dc, (
        "tap dia chi thieu ten module — dang chi nhan duong dan day du, "
        "dung loi 61")

    assert "thay" not in dc, (
        "ten 4 ky tu lot vao tap dia chi. `thay` khop ca cum 'thay vi' trong "
        "van xuoi, nen moi dau ✅ se co mot 'dia chi' GIA va gac tren thanh "
        "trang tri. Day la vai tro cua DAI_TOI_THIEU — ha no xuong la bo gac.")

    assert co_dia_chi("`va_an_toan.thay()`", dc)
    assert co_dia_chi("`tests/test_c5_noi_that.py`", dc)
    assert not co_dia_chi("tách phép phán thành hàm thuần rồi thử", dc), (
        "mot cau ta thuan tuy KHONG duoc tinh la dia chi")
    assert not co_dia_chi("chính công cụ ấy", dc)
    print(f"PASS  tap {len(dc)} dia chi, hai chieu deu dung")


def test_DOC_THEO_COT_chu_khong_theo_chu_TICH_xuat_hien():
    """Ký hiệu ✅ nằm đầy trong văn xuôi của các ô khác — đọc bừa là đếm
    nhầm. Hàm THUẦN nên thử được bằng một bảng dựng tay."""
    van = (
        "| # | Lỗi | Bắt bởi | Máy chặn? | Đã chặn bằng |\n"
        "|---|---|---|---|---|\n"
        "| 1 | co chu ✅ trong mo ta | x | ⚠️ | chua co |\n"
        "| 2 | binh thuong | x | ✅ | `tools/va_an_toan.py` |\n"
    )
    assert dong_bang(van) == [("2", "`tools/va_an_toan.py`")], dong_bang(van)
    # Va bang THAT phai doc ra khac rong — mot ham thuan van co the mu.
    assert len(dong_bang(BANG.read_text(encoding="utf-8"))) > 20
    print("PASS  chi dem dong co COT thu tu la ✅")
