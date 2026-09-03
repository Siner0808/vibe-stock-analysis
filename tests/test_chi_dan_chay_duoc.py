"""Gác: một chỉ dẫn trỏ tới file không tồn tại là một cổng xanh giả.

Ngày 03/09/2026 `extend_history.py` kết thúc bằng dòng

    Bước tiếp theo:  <lệnh chạy> walkforward_vn100.py

trong khi file ấy đã đổi đuôi thành `.broken` từ 20/08/2026 và
`CLAUDE.md` cấm dùng nó. Người làm theo chỉ dẫn sẽ nhận `No such file`
— và đó là kịch bản MAY: kịch bản xấu là file còn tồn tại nhưng đã sai.

Nặng hơn, cùng ngày: `market_filter.CacheQuaHanError` bảo người dùng chạy
`extend_history.py` để sửa cache VN-INDEX quá hạn, mà script ấy lặp trên
`VN100_SYMBOLS` nên chưa bao giờ đụng tới VNINDEX. Đo sau một lượt chạy
đầy đủ: 71/71 mã trong rổ lên 03/09, VNINDEX vẫn ở 20/08, cổng C1 vẫn
TẮT. Một chỉ dẫn không sửa được thứ nó nói là sẽ sửa.

Hai lỗi cùng một hình dạng: **văn bản hướng dẫn không được ai kiểm.**
"""
import ast
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import extend_history as eh  # noqa: E402

BO_QUA = {".venv", "scratch", "__pycache__", ".git", "node_modules",
          "backtest", "brain"}
#: Khớp lệnh chạy một file .py. KHÔNG khớp `python -m` hay `python -c`,
#: vì hai dạng đó không nêu tên file nào để kiểm.
RE_CHI_DAN = re.compile(r"python[0-9.]*\s+((?!-)[A-Za-z_][\w./-]*\.py)")


#: Sàn số file phải quét được. Xem docstring của hàm quét bên dưới.
SAN_SO_FILE = 80


def _quet() -> tuple[list[str], int]:
    """Trả (lỗi, số file đã quét). LỌC THEO ĐƯỜNG TƯƠNG ĐỐI, bắt buộc.

    Repo này nằm ở `…\\antigravity\\scratch\\vibe_preview`, nên lọc
    "scratch" trên `f.parts` của đường TUYỆT ĐỐI sẽ khớp **mọi** file của
    dự án và máy quét bỏ qua sạch — xanh vì không kiểm gì.

    Bản đầu của chính hàm này mắc đúng lỗi đó, và chỉ đột biến tìm ra: trỏ
    ngược chỉ dẫn về `walkforward_vn100.py` mà test vẫn xanh. Dự án đã gặp
    bẫy này một lần và ghi lại ở `tools/kiem_cu_phap_311.py`, nhưng bài
    học nằm trong chú thích của một công cụ thì không bảo vệ công cụ sau.
    """
    loi, so_file = [], 0
    for duoi in ("*.py", "*.md", "*.yml", "*.yaml", "*.toml"):
        for f in GOC.rglob(duoi):
            if any(p in BO_QUA for p in f.relative_to(GOC).parts):
                continue
            try:
                src = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            so_file += 1
            for i, dong in enumerate(src.splitlines(), 1):
                for m in RE_CHI_DAN.finditer(dong):
                    if not (GOC / m.group(1)).exists():
                        loi.append(f"{f.relative_to(GOC)}:{i} -> {m.group(1)}")
    return loi, so_file


def test_SAN_SO_FILE_khong_duoc_ha_am_tham():
    """Hạ sàn về 0 là gỡ gác, và một phép đột biến đã chứng minh nó êm.

    Nên nới sàn phải sửa HAI chỗ: hằng số và dòng này. Cùng quy ước với
    cổng C5 — đóng bằng tay, khoá bởi test, mở lại thì có chủ đích.
    """
    assert SAN_SO_FILE >= 80, "sàn bị hạ — máy quét im lặng sẽ lọt"


def test_may_quet_THAT_SU_quet_duoc_file():
    """Một máy quét im lặng vì không thấy gì thì tệ hơn không có máy quét.

    Đây là chốt chặn chung cho mọi gác quét-toàn-repo, không riêng gác
    này: con số phải LỘ RA, để một số 0 nhìn thấy được.
    """
    _, so_file = _quet()
    assert so_file >= SAN_SO_FILE, (
        f"chỉ quét được {so_file} file — bộ lọc đang nuốt cả repo")


def test_moi_chi_dan_python_deu_tro_toi_file_CO_THAT():
    loi, _ = _quet()
    assert not loi, "chỉ dẫn trỏ tới file không tồn tại:\n  " + "\n  ".join(loi)


def test_extend_history_CO_keo_ca_chi_so_ngoai_ro():
    assert "VNINDEX" in eh.CHI_SO_NGOAI_RO


def test_LOI_GOI_that_su_nhan_chi_so_chu_khong_chi_khai_hang():
    """Gác HÌNH DẠNG chuỗi truyền: hằng số → biến → lời gọi.

    Khai một hằng số rồi quên truyền nó đi là cách hỏng êm nhất — module
    vẫn có `CHI_SO_NGOAI_RO`, test giá trị vẫn xanh, và VNINDEX vẫn không
    được tải. Nên phải lần theo đúng chuỗi ấy, không kiểm điểm đầu.
    """
    cay = ast.parse((GOC / "extend_history.py").read_text(encoding="utf-8"))
    ham = [n for n in ast.walk(cay)
           if isinstance(n, ast.FunctionDef) and n.name == "main"]
    assert len(ham) == 1

    goi = [n for n in ast.walk(ham[0]) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "extend_history"]
    assert len(goi) == 1, f"thấy {len(goi)} lời gọi extend_history()"
    dau = goi[0].args[0]
    assert isinstance(dau, ast.Name), ast.dump(dau)

    gan = [n for n in ast.walk(ham[0]) if isinstance(n, ast.Assign)
           and any(getattr(t, "id", None) == dau.id for t in n.targets)]
    assert len(gan) == 1, f"{dau.id} được gán {len(gan)} lần"
    ten = {n.id for n in ast.walk(gan[0].value) if isinstance(n, ast.Name)}
    assert "CHI_SO_NGOAI_RO" in ten, (
        f"{dau.id} không dựng từ CHI_SO_NGOAI_RO — chỉ số không được tải")


def test_thong_bao_C1_van_tro_dung_cong_cu():
    """Đây là gác VĂN BẢN, và ở đây văn bản mới là thứ cần kiểm.

    Thứ được kiểm chính là chuỗi thông báo lỗi mà người dùng đọc. Gác AST
    không nói được gì về nó; ngược lại gác `in` trên văn bản-là-văn-bản
    thì hợp lệ — xem CLAUDE.md, "Gác phải đọc AST, không đọc `in`".
    """
    src = (GOC / "market_filter.py").read_text(encoding="utf-8")
    assert "extend_history.py" in src, (
        "thông báo C1 không còn chỉ tới công cụ nào")
    assert (GOC / "extend_history.py").exists()
    assert "VNINDEX" in eh.CHI_SO_NGOAI_RO, (
        "thông báo chỉ tới extend_history.py nhưng script không kéo VNINDEX")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_chi_dan_chay_duoc.py -q")
