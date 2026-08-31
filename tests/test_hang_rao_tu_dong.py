"""Hàng rào tự động phải THẬT SỰ được nối vào, không chỉ tồn tại.

BA LỖ HỔNG ĐÃ ĐÓNG NGÀY 31/08/2026 — file này canh để chúng không mở lại.

1. HOOK KHÔNG THẤY GÌ ĐI QUA BASH
   `PostToolUse` khớp `Write|Edit`. Mà chính quy ước của dự án — *"vá lớn
   thì viết một file `.py` rồi chạy nó"* — đi qua Bash. Quy ước tự vô hiệu
   hoá cái gác của chính nó. Đo được: một phiên làm việc sửa 6 file mà hook
   không chạy lần nào; `--quet-repo` chỉ được gọi vì người nhớ ra.
   → Thêm hook `Stop` chạy `--quet-thay-doi`.

2. `kiem_cu_phap_311.py` CHỈ CHẠY BẰNG TAY
   `CLAUDE.md` ghi *"CHẠY TRƯỚC KHI PUSH"* — một hàng rào dựa vào trí nhớ.
   Nó là thứ DUY NHẤT kiểm python nhúng trong heredoc của workflow YAML,
   mà `quet-so-lenh.yml` có hơn 70 dòng như thế. Hỏng thì chỉ lộ ra khi
   cron nổ giữa phiên giao dịch.
   → Thêm bước vào `kiem-dinh.yml`.

3. CÔNG CỤ ĐÓ KHÔNG TỰ TÌM RA MÌNH
   `DUONG_DOAN` không có `sys.executable`. Trên Linux CI nó phải trông vào
   `python3.11` có nằm trên PATH hay không — không bảo đảm. Trả mã 2 ("chưa
   kiểm được") trên CI chính là một cổng xanh giả.
   → Thêm `sys.executable` vào danh sách, và CI coi mã 2 là ĐỎ.
"""
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

SETTINGS = GOC / ".claude" / "settings.json"
KIEM_DINH = GOC / ".github" / "workflows" / "kiem-dinh.yml"


def _khoi_hook(su_kien: str) -> list[tuple[str, list[str]]]:
    """[(matcher, [lệnh])] — matcher là thứ quyết định hook CÓ CHẠY hay không.

    Chỉ đọc lệnh mà bỏ qua matcher là kiểm hook TỒN TẠI chứ không kiểm nó
    được NỐI VÀO ĐÂU. Đột biến đổi matcher thành `NotebookEdit` sống sót
    đúng vì bản đầu của helper này chỉ trả lệnh.
    """
    d = json.loads(SETTINGS.read_text(encoding="utf-8"))
    return [(khoi.get("matcher", ""),
             [h.get("command", "") for h in khoi.get("hooks", [])])
            for khoi in d.get("hooks", {}).get(su_kien, [])]


def _lenh_cua_hook(su_kien: str) -> list[str]:
    return [c for _, ls in _khoi_hook(su_kien) for c in ls]


def test_hook_Stop_soat_lai_file_da_doi():
    """Lỗ hổng 1. Không có nó thì mọi thay đổi qua Bash im lặng tới lúc push."""
    lenh = _lenh_cua_hook("Stop")
    assert lenh, "KHÔNG có hook Stop — thay đổi qua Bash không ai soát"
    assert any("chan_bia_so_lieu" in c and "--quet-thay-doi" in c
               for c in lenh), f"hook Stop không chạy --quet-thay-doi: {lenh}"
    print("PASS  hook Stop soát file đã đổi")


def test_hai_hook_cu_van_con_VA_van_noi_dung_cho():
    """Thêm hook mới mà làm rơi hook cũ thì đây là một bước lùi.

    Kiểm cả MATCHER, không chỉ lệnh: một hook nối vào matcher không bao giờ
    khớp thì y hệt không có hook, mà nhìn vào file lại tưởng là có.
    """
    for su_kien, cong_cu, phai_khop in (
            ("PostToolUse", "chan_bia_so_lieu", ("Write", "Edit")),
            ("PreToolUse", "cua_doc_bat_buoc", ("Read", "Write", "Edit"))):
        khop = [(m, ls) for m, ls in _khoi_hook(su_kien)
                if any(cong_cu in c for c in ls)]
        assert khop, f"{su_kien}: mất hook {cong_cu}"
        matcher = khop[0][0]
        for t in phai_khop:
            assert t in matcher, (
                f"{su_kien}: matcher {matcher!r} không bắt {t} — "
                f"hook có mặt nhưng không nối vào đâu")
    print("PASS  hai hook cũ còn nguyên VÀ matcher vẫn bắt đúng công cụ")


def test_CI_chay_kiem_cu_phap_311():
    """Lỗ hổng 2. Đây là thứ DUY NHẤT canh python nhúng trong YAML."""
    src = KIEM_DINH.read_text(encoding="utf-8")
    assert "tools/kiem_cu_phap_311.py" in src, (
        "kiem-dinh.yml KHÔNG chạy kiem_cu_phap_311 — python nhúng trong "
        "workflow YAML không ai kiểm")
    print("PASS  kiem-dinh.yml chạy kiem_cu_phap_311")


def test_CI_coi_ma_2_la_DO_chu_khong_bo_qua():
    """Mã 2 = "chưa kiểm được". Trên runner 3.11 đó là lỗi, không phải xanh.

    Đây đúng là hình dạng cổng xanh giả mà `vnstock_goi.kiem_goi()` đã phải
    dựng trạng thái thứ ba để tránh: mất mạng mà trả "khớp".
    """
    src = KIEM_DINH.read_text(encoding="utf-8")
    i = src.find("tools/kiem_cu_phap_311.py")
    khoi = src[i:i + 700]
    assert '"$ma" -eq 2' in khoi or "$ma\" -eq 2" in khoi, (
        "CI không phân biệt mã 2 — 'chưa kiểm được' đang được tính là xanh")
    print("PASS  CI coi mã 2 (chưa kiểm được) là đỏ")


def test_cong_cu_311_tu_tim_ra_chinh_no():
    """Lỗ hổng 3. `sys.executable` là ứng viên hiển nhiên và nó đang thiếu."""
    import kiem_cu_phap_311 as k
    assert sys.executable in k.DUONG_DOAN, (
        "DUONG_DOAN không có sys.executable — trên CI công cụ phải trông "
        "vào `python3.11` có trên PATH hay không")
    # Và nó phải đứng SAU biến môi trường: người đặt PYTHON311 là cố ý.
    assert k.DUONG_DOAN.index(sys.executable) > 0
    print("PASS  DUONG_DOAN có sys.executable, và sau PYTHON311")


def test_quet_thay_doi_LUI_VE_quet_repo_khi_khong_hoi_duoc_git():
    """Rỗng có HAI nghĩa: không đổi gì, hoặc không hỏi được git.

    Không phân biệt được thì phải quét cả repo. Coi rỗng là "sạch" biến
    một thư mục không có git thành một cổng xanh vĩnh viễn.
    """
    import ast
    import chan_bia_so_lieu as c

    cay = ast.parse((GOC / "tools" / "chan_bia_so_lieu.py")
                    .read_text(encoding="utf-8"))
    h = [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)
         and n.name == "quet_thay_doi"][0]
    goi = {n.func.id for n in ast.walk(h)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "quet_repo" in goi, (
        "quet_thay_doi không có đường lui về quet_repo — danh sách rỗng "
        "sẽ được đọc là 'sạch'")
    assert callable(c.file_da_doi)
    print("PASS  không hỏi được git -> lùi về quét cả repo")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
