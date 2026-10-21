"""Duyệt đệ quy cây repo mà KHÔNG đi xuống worktree lồng bên trong nó.

VÌ SAO CÓ FILE NÀY
──────────────────
Ứng dụng Claude desktop tạo worktree cho mỗi phiên ở
`<repo>/.claude/worktrees/<tên>/` — NẰM TRONG thư mục repo. Ngày 30/09/2026,
khi `.claude/worktrees/angry-keller-8c2bd9` tồn tại, năm cổng chạy từ bản
checkout chính cho ĐỎ GIẢ ở bốn cổng:

    cổng 1  test_repo_hien_tai_sach_o_muc_chan đỏ
    cổng 2  kiem_cu_phap_311 thoát 2: WinError 206 (dòng lệnh quá dài)
    cổng 3  chan_bia_so_lieu --quet-repo: 5 CHẶN, cả năm trong bản sao lồng
    cổng 4  test_chan_bia_so_lieu.py vượt 300 giây

git KHÔNG thấy thư mục ấy — ứng dụng ghi `.claude/worktrees/` vào
`.git/info/exclude` — nên mọi phép dựa trên `git ls-files` vẫn đúng. Nhưng
`Path.rglob` không hỏi git.

Ba luật:
  1. mọi thứ dưới `.claude/worktrees/` — KỂ CẢ khi đã mất `.git`: gỡ worktree
     trên Windows để lại thư mục khi có file đang bị khoá, và bản sao mồ côi
     ấy vẫn làm cổng đỏ giả.
  2. mọi thư mục CON của gốc có mục `.git` — tệp `gitdir:` (worktree) hay
     thư mục (bản clone lồng): đó là một cây làm việc KHÁC, không phải repo
     này. Gốc thì không xét — gốc nào cũng có `.git`.
  3. thư mục `.tam_test/` ở GỐC (BƯỚC 201): chỗ DUY NHẤT test được đặt file
     tạm TRONG repo (bộ dò bịa số chỉ chấm file thuộc một worktree của repo).
     Năm cổng chạy song song thì một test quét repo ở tiến trình này bắt gặp
     `tmpXXXX/thu.py` của tiến trình kia đúng lúc nó bị xoá → `FileNotFoundError`
     — đỏ giả, đo 16/10/2026: 3/158 file mỗi vòng, hai vòng, cùng một nguồn.
  4. tệp hay thư mục có tiền tố `__tam_` NGAY dưới `tests/` của gốc (BƯỚC 211):
     tệp tạm mà một test BUỘC phải đặt trong `tests/` — bộ dò bịa số chỉ miễn trừ
     đường bắt đầu bằng `tests/`, nên luật 3 không dời được nó (BƯỚC 206). Đặt bằng
     `tep_tam_trong_tests` (tên duy nhất mỗi lượt). Đỏ giả 20/10/2026 (PR #255, CI
     cổng 4): `duyet` trả `tests/__tam_kiem_tra_mien_tru.py`, tiến trình kia xoá nó,
     `test_KHONG_FILE_NAO_trong_repo_co_CAU_LENH_CHET` đọc → `FileNotFoundError`.
     `liet_ke` là bản MỘT TẦNG của `duyet` cho cùng luật này.

Mỗi máy quét giữ bộ lọc riêng của nó (`.venv`, `scratch`…); file này chỉ
thêm đúng một điều. Gác: `tests/test_duyet_repo.py`, gồm một sổ đăng ký bắt
mọi lượt duyệt đệ quy mới không đi qua đây. `docs/STATE.md` BƯỚC 147.
"""
from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Iterator

THU_MUC_WORKTREE_APP = (".claude", "worktrees")

#: Thư mục ở gốc repo dành cho file tạm của test (gitignore). Luật 3.
THU_MUC_TAM_TEST = ".tam_test"

#: Luật 4: tệp tạm của test đặt THẲNG trong `tests/` mang tiền tố này.
THU_MUC_TESTS = "tests"
TIEN_TO_TAM = "__tam_"


def la_tep_tam_cua_test(goc: Path, duong_dan: Path) -> bool:
    """`duong_dan` (dưới `goc`) có phải tệp tạm luật 4 không: phần đường THỨ HAI mang
    tiền tố `__tam_` và phần đầu là `tests`. So theo PHẦN, không theo chuỗi con."""
    phan = Path(duong_dan).relative_to(goc).parts
    return (len(phan) >= 2 and phan[0] == THU_MUC_TESTS
            and phan[1].startswith(TIEN_TO_TAM))


@contextlib.contextmanager
def tep_tam_trong_tests(goc: Path, ten: str) -> Iterator[Path]:
    """Một tệp `.py` RỖNG, tên duy nhất `tests/__tam_<ten>_<ngẫu nhiên>.py`; xoá khi ra.

    Tên cố định thì hai tiến trình chạy cùng một test (cổng 1 và cổng 4) xoá tệp của
    nhau: đo 21/10/2026, 6/1600 lượt đỏ `PermissionError`/`FileNotFoundError`.
    """
    fd, ten_tep = tempfile.mkstemp(prefix=f"{TIEN_TO_TAM}{ten}_", suffix=".py",
                                   dir=str(Path(goc) / THU_MUC_TESTS))
    os.close(fd)
    p = Path(ten_tep)
    try:
        yield p
    finally:
        p.unlink(missing_ok=True)


def la_worktree_long(goc: Path, duong_dan: Path, _nho: dict | None = None) -> bool:
    """`duong_dan` (một FILE dưới `goc`) có nằm trong worktree lồng không.

    `_nho` là bộ nhớ `{thư mục: có .git}` cho MỘT lượt duyệt — truyền từ
    `duyet()`. Không giữ nó ở mức module: một bộ nhớ sống qua lượt sẽ trả
    lời cũ khi worktree được tạo hay gỡ giữa chừng (lỗi 75).
    """
    phan = duong_dan.relative_to(goc).parts
    if phan[:len(THU_MUC_WORKTREE_APP)] == THU_MUC_WORKTREE_APP:
        return True
    if _nho is None:
        _nho = {}
    d = goc
    for p in phan[:-1]:
        d = d / p
        co = _nho.get(d)
        if co is None:
            co = _nho[d] = (d / ".git").exists()
        if co:
            return True
    return False


def duyet(goc: Path, mau: str) -> Iterator[Path]:
    """`goc.rglob(mau)` trừ worktree lồng, `.tam_test/` và tệp tạm `tests/__tam_*`."""
    goc = Path(goc)
    nho: dict = {}
    for p in goc.rglob(mau):
        if p.relative_to(goc).parts[:1] == (THU_MUC_TAM_TEST,):
            continue
        if la_tep_tam_cua_test(goc, p):
            continue
        if not la_worktree_long(goc, p, nho):
            yield p


def liet_ke(goc: Path, thu_muc, mau: str) -> list[Path]:
    """`(goc / thu_muc).glob(mau)` MỘT TẦNG, trừ tệp tạm luật 4. Đã sắp xếp."""
    goc = Path(goc)
    return sorted(p for p in (goc / thu_muc).glob(mau)
                  if not la_tep_tam_cua_test(goc, p))
