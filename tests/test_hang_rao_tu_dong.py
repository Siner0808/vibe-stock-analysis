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
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

#: Từ 10/09/2026 sáu hook KHÔNG còn đăng ký trong settings của
#: repo — giữ cả hai nơi làm mỗi hook chạy HAI LẦN khi phiên mở ở repo
#: (đo trực tiếp, `docs/STATE.md` BƯỚC 49). Nơi đăng ký thật là
#: `~/.claude/settings.json`, mà CI không thấy. Thứ CI kiểm được, và vẫn
#: đáng kiểm, là BẢN KHAI: đúng hook, đúng sự kiện, đúng matcher.
#: Việc "đã đăng ký thật chưa" do `tools/kiem_cua_song.py` trả lời.
SETTINGS = GOC / "docs" / "cua-du-an.json"
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


def test_khong_hoi_duoc_git_thi_file_da_doi_tra_None():
    """Chạy THẬT trên một thư mục không phải repo git.

    Đi qua đúng `subprocess` thật, không thay thế gì — nên nó canh chính
    thân hàm, chỗ mà test ngay dưới (thay `file_da_doi` bằng hàm giả)
    không với tới được.
    """
    import chan_bia_so_lieu as c

    that = c.GOC_DU_AN
    try:
        c.GOC_DU_AN = Path(tempfile.mkdtemp(prefix="khong-git-"))
        ket = c.file_da_doi()
        assert ket is None, (
            "git chay o thu muc khong phai repo -> CHUA HOI DUOC, phai la "
            f"None chu khong phai {ket!r} (rong se bi doc thanh sach)")
    finally:
        c.GOC_DU_AN = that
    print("PASS  khong hoi duoc git -> None, khong phai []")


def test_subprocess_no_thi_file_da_doi_cung_tra_None():
    """Nhánh `except Exception` — git không cài, hết giờ, cwd không tồn tại.

    Khác nhánh `returncode != 0` mà test ngay trên chạm tới. Một phát đột
    biến ngày 08/09/2026 sống sót đúng vì hai nhánh ấy bị coi là một.
    """
    import chan_bia_so_lieu as c

    that = c.GOC_DU_AN
    try:
        c.GOC_DU_AN = Path(tempfile.gettempdir()) / "khong-he-ton-tai-abc123"
        assert not c.GOC_DU_AN.exists()
        ket = c.file_da_doi()
        assert ket is None, (
            "cwd khong ton tai -> subprocess no -> CHUA HOI DUOC, phai la "
            f"None chu khong phai {ket!r}")
    finally:
        c.GOC_DU_AN = that
    print("PASS  subprocess no -> None")


def test_RONG_khac_CHUA_HOI_DUOC_git():
    """`[]` (git nói: không đổi gì) KHÔNG được đọc thành `None` (chưa hỏi được).

    Bản trước gộp hai thứ ấy vào một `[]`, và `quet_thay_doi()` lùi về quét
    TOÀN REPO cho cả hai. Vô hại suốt thời gian cửa `Stop` chỉ chạy trong
    repo. Ngày 08/09/2026 cửa ấy được đăng ký ở `~/.claude/settings.json`
    nên chạy ở MỌI dự án — mà **cây sạch là trạng thái bình thường lúc cuối
    phiên**, nên mỗi lần dừng phiên đều nổ một lượt quét toàn repo kèm 30
    dòng cảnh báo về một dự án người dùng không hề mở. Gác kêu sói thì bị tắt.

    Kiểm HÀNH VI, không kiểm cấu trúc. Test ngay trên chỉ hỏi
    `quet_thay_doi` có GỌI `quet_repo` không — và câu trả lời vẫn là "có"
    cả trước lẫn sau khi lỗi này ra đời, nên nó không thể bắt được.
    """
    import chan_bia_so_lieu as c

    dau_vet = []

    def gia_quet_repo():
        dau_vet.append("REPO")
        return 0

    def gia_quet(ds, nhan):
        dau_vet.append(("FILE", tuple(str(p) for p in ds)))
        return 0

    that = (c.quet_repo, c._quet, c.file_da_doi)
    try:
        c.quet_repo, c._quet = gia_quet_repo, gia_quet

        c.file_da_doi = lambda: None
        assert c.quet_thay_doi() == 0
        assert dau_vet == ["REPO"], (
            f"None = chua hoi duoc git -> phai quet ca repo, nhung: {dau_vet}")

        dau_vet.clear()
        c.file_da_doi = lambda: []
        assert c.quet_thay_doi() == 0
        assert dau_vet == [], (
            "[] = git DA tra loi va khong file .py nao doi -> khong duoc "
            f"quet gi ca, nhung: {dau_vet}")

        dau_vet.clear()
        c.file_da_doi = lambda: [GOC / "paper_metrics.py"]
        assert c.quet_thay_doi() == 0
        assert len(dau_vet) == 1 and dau_vet[0][0] == "FILE", (
            f"danh sach co file -> phai quet dung nhung file do: {dau_vet}")
    finally:
        c.quet_repo, c._quet, c.file_da_doi = that
    print("PASS  None -> quet repo · [] -> khong quet gi · [x] -> quet x")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
