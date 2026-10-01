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

Hai luật:
  1. mọi thứ dưới `.claude/worktrees/` — KỂ CẢ khi đã mất `.git`: gỡ worktree
     trên Windows để lại thư mục khi có file đang bị khoá, và bản sao mồ côi
     ấy vẫn làm cổng đỏ giả.
  2. mọi thư mục CON của gốc có mục `.git` — tệp `gitdir:` (worktree) hay
     thư mục (bản clone lồng): đó là một cây làm việc KHÁC, không phải repo
     này. Gốc thì không xét — gốc nào cũng có `.git`.

Mỗi máy quét giữ bộ lọc riêng của nó (`.venv`, `scratch`…); file này chỉ
thêm đúng một điều. Gác: `tests/test_duyet_repo.py`, gồm một sổ đăng ký bắt
mọi lượt duyệt đệ quy mới không đi qua đây. `docs/STATE.md` BƯỚC 147.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

THU_MUC_WORKTREE_APP = (".claude", "worktrees")


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
    """`goc.rglob(mau)` trừ mọi thứ nằm trong worktree lồng."""
    goc = Path(goc)
    nho: dict = {}
    for p in goc.rglob(mau):
        if not la_worktree_long(goc, p, nho):
            yield p
