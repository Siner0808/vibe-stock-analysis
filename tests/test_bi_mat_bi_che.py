"""Gác: mọi file bí mật trong `.streamlit` phải bị che ĐÍCH DANH.

Trước 03/09/2026 `.streamlit/secrets_cloud_paste.txt` — credential thật của
kho ngoài — chỉ được che nhờ dòng `*.txt` nằm ở mục "Kết quả và log chạy
thử nghiệm", tức một luật không hề nói về bí mật. Repo này là public.

Luật ấy không sai vào ngày nó ra đời. Nó sai vào ngày ai đó lưu cùng nội
dung thành `.json`, `.md`, hoặc không đuôi — và không có gì báo.

Gác hỏi `git check-ignore`, tức hỏi chính git chứ không đọc lại
`.gitignore` rồi tự diễn giải: dựng lại luật của git trong test là kiểm
công thức của test, không kiểm hành vi của git.
"""
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

#: Mọi đuôi mà cùng một nội dung bí mật có thể bị lưu nhầm thành.
DUOI = [".toml", ".txt", ".json", ".md", ".bak", ".yaml", ".ini", ""]


def _bi_che(duong_dan: str) -> bool:
    """`--no-index` là BẮT BUỘC, không phải tuỳ chọn.

    Thiếu nó, `git check-ignore` **bỏ qua hoàn toàn file đang được theo
    dõi** và trả "không bị che" bất kể luật viết gì. Câu hỏi "bản mẫu có
    bị che quá tay không" vì thế chưa bao giờ được trả lời: đột biến xoá
    dòng phủ định `!...secrets.toml.example` vẫn XANH, vì file ấy đang
    được theo dõi nên git từ chối xét nó.

    Một cổng xanh không kiểm gì — đúng thứ dự án đã gặp ở
    `tools/kiem_ban_sach.py` (22/08) và ở ba gác dạng `in` (31/08). Tìm
    ra bằng đột biến, không phải bằng đọc lại.
    """
    r = subprocess.run(["git", "check-ignore", "-q", "--no-index", duong_dan],
                       cwd=GOC, capture_output=True)
    if r.returncode not in (0, 1):
        pytest.skip(f"git check-ignore không chạy được: {r.returncode}")
    return r.returncode == 0


@pytest.mark.parametrize("duoi", DUOI)
def test_moi_duoi_cua_file_secrets_deu_bi_che(duoi):
    assert _bi_che(f".streamlit/secrets{duoi}"), (
        f"secrets{duoi} KHÔNG bị che — đổi đuôi file là lộ credential")
    assert _bi_che(f".streamlit/secrets_cloud_paste{duoi}")


def test_ban_MAU_van_commit_duoc():
    """Che quá tay cũng là hỏng: `secrets.toml.example` là tài liệu."""
    assert not _bi_che(".streamlit/secrets.toml.example"), (
        "bản mẫu bị che -> người mới không có gì để chép")


def test_file_bi_mat_that_KHONG_bi_git_theo_doi():
    """Hỏi sổ của git, không hỏi thư mục: file đã lỡ commit thì .gitignore
    không cứu được nữa — luật chỉ áp cho file chưa theo dõi."""
    r = subprocess.run(["git", "ls-files", ".streamlit/"],
                       cwd=GOC, capture_output=True, text=True)
    theo_doi = {d.strip() for d in r.stdout.splitlines() if d.strip()}
    lo = {d for d in theo_doi
          if "secret" in d.lower() and not d.endswith(".example")}
    assert not lo, f"file bí mật đang bị git theo dõi: {sorted(lo)}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_bi_mat_bi_che.py -q")
