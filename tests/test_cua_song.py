"""Cửa nào đang sống — phải ĐỌC được, không được suy ra.

Nguyên nhân chính xác tìm ra 10/09/2026: hai hook (`cua_bash_an_toan.py`,
`cua_mo_phien.py`) chỉ được khai trong `<repo>/.claude/settings.json`, mà
file ấy chỉ nạp khi thư mục dự án LÀ repo — điều chưa xảy ra lần nào. Bốn
hook còn lại đã được chép sang `~/.claude/settings.json` bằng đường dẫn
tuyệt đối hôm 08/09 và chạy bình thường suốt từ đó.

Phép kiểm ĐẦU TIÊN dựng lại đúng cấu hình ấy — 6 hook repo, 4 hook toàn
cục — theo Bước 3 của skill.
"""
import ast
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import kiem_cua_song as ks  # noqa: E402

DUONG_REPO = "${CLAUDE_PROJECT_DIR:-.}"
TUYET_DOI = "C:/Users/cuong/.gemini/antigravity/scratch/vibe_preview"


def _hook(su_kien: str, matcher: str | None, *lenh: str) -> dict:
    m: dict = {"hooks": [{"type": "command", "command": c} for c in lenh]}
    if matcher is not None:
        m["matcher"] = matcher
    return {"hooks": {su_kien: [m]}}


def _gop(*ds: dict) -> dict:
    ra: dict = {"hooks": {}}
    for d in ds:
        for su_kien, nhom in d["hooks"].items():
            ra["hooks"].setdefault(su_kien, []).extend(nhom)
    return ra


def _repo_sau_hook() -> dict:
    """Đúng sáu hook mà settings của repo khai, tới 10/09/2026."""
    return _gop(
        _hook("PostToolUse", "Write|Edit",
              f'python "{DUONG_REPO}/tools/chan_bia_so_lieu.py"',
              f'python "{DUONG_REPO}/tools/cua_ghi_an_toan.py"'),
        _hook("PreToolUse", "Read|Write|Edit|NotebookEdit",
              f'python "{DUONG_REPO}/tools/cua_doc_bat_buoc.py"'),
        _hook("PreToolUse", "Bash",
              f'python "{DUONG_REPO}/tools/cua_bash_an_toan.py"'),
        _hook("SessionStart", None,
              f'python "{DUONG_REPO}/tools/cua_mo_phien.py"'),
        _hook("Stop", None,
              f'python "{DUONG_REPO}/tools/chan_bia_so_lieu.py"'
              ' --quet-thay-doi'),
    )


def _toan_cuc_bon_hook() -> dict:
    """Đúng bốn hook toàn cục có từ 08/09 — THIẾU Bash và SessionStart."""
    return _gop(
        _hook("PostToolUse", "Write|Edit",
              f'python "{TUYET_DOI}/tools/chan_bia_so_lieu.py"',
              f'python "{TUYET_DOI}/tools/cua_ghi_an_toan.py"'),
        _hook("PreToolUse", "Read|Write|Edit|NotebookEdit",
              f'python "{TUYET_DOI}/tools/cua_doc_bat_buoc.py"'),
        _hook("Stop", None,
              f'python "{TUYET_DOI}/tools/chan_bia_so_lieu.py"'
              ' --quet-thay-doi'),
    )


# ══ 1. Dựng lại nguyên văn tình trạng 08/09 → 10/09 ════════════════════

def test_DUNG_LAI_hai_cua_chua_dang_ky_toan_cuc():
    """Nếu phép kiểm này xanh thì công cụ vô dụng: nó phải chỉ đúng HAI
    cửa, và phải gọi tên chúng ra."""
    ma, thieu, tong = ks.so_sanh(_repo_sau_hook(), _toan_cuc_bon_hook())
    assert ma == 1, "sau/bon hook ma KHONG bao thieu"
    assert tong == 6
    ten = {v.split()[0] for _, _, v in thieu}
    assert ten == {"cua_bash_an_toan.py", "cua_mo_phien.py"}, (
        f"chi ra sai cua: {ten}")
    print(f"PASS  chi dung 2/6: {sorted(ten)}")


def test_khi_da_chep_du_thi_QUA():
    ma, thieu, tong = ks.so_sanh(_repo_sau_hook(), _repo_sau_hook())
    assert (ma, thieu, tong) == (0, [], 6)


# ══ 2. Chỗ dễ sai nhất: hai file dùng HAI KIỂU đường dẫn ═══════════════

def test_duong_dan_REPO_va_TUYET_DOI_phai_coi_la_MOT():
    """`${CLAUDE_PROJECT_DIR:-.}/tools/x.py` và `C:/.../tools/x.py` là
    cùng một cửa. So nguyên chuỗi thì mọi hook đều báo thiếu và công cụ
    thành một cái chuông kêu suốt — tệ ngang việc im."""
    a = _hook("PreToolUse", "Bash", f'python "{DUONG_REPO}/tools/x.py"')
    b = _hook("PreToolUse", "Bash", f'python "{TUYET_DOI}/tools/x.py"')
    assert ks.so_sanh(a, b)[0] == 0
    print("PASS  hai kieu duong dan quy ve mot")


@pytest.mark.parametrize("lenh,mong", [
    ('python "${CLAUDE_PROJECT_DIR:-.}/tools/x.py"', "x.py"),
    ('python "C:/a/b/tools/x.py"', "x.py"),
    ('python "C:/a/b/tools/x.py" --quet-thay-doi', "x.py --quet-thay-doi"),
    ('python "C:/a/b/tools/x.py"   --im   ', "x.py --im"),
    ("khong-co-duoi-py", None),
])
def test_dau_van_tay(lenh, mong):
    assert ks.dau_van_tay(lenh) == mong


def test_THAM_SO_khac_nhau_la_HAI_cua_khac_nhau():
    """`chan_bia_so_lieu.py` (PostToolUse) và `--quet-thay-doi` (Stop) là
    hai việc khác nhau. Gộp chúng thì gỡ mất một cái vẫn xanh."""
    a = _hook("Stop", None, 'python "t/x.py" --quet-thay-doi')
    b = _hook("Stop", None, 'python "t/x.py"')
    assert ks.so_sanh(a, b)[0] == 1


def test_MATCHER_khac_nhau_la_HAI_cua_khac_nhau():
    """Đột biến số 3 của lỗi 31/08: matcher đổi thì hook tồn tại nhưng
    không nối vào đâu. So mà bỏ matcher là mù đúng chỗ đó."""
    a = _hook("PreToolUse", "Bash", 'python "t/x.py"')
    b = _hook("PreToolUse", "Write|Edit", 'python "t/x.py"')
    assert ks.so_sanh(a, b)[0] == 1


def test_SU_KIEN_khac_nhau_la_HAI_cua_khac_nhau():
    a = _hook("PreToolUse", None, 'python "t/x.py"')
    b = _hook("PostToolUse", None, 'python "t/x.py"')
    assert ks.so_sanh(a, b)[0] == 1


# ══ 3. Trạng thái thứ ba ═══════════════════════════════════════════════

@pytest.mark.parametrize("repo,toan_cuc", [
    (None, {"hooks": {}}),
    ({"hooks": {}}, None),
    (None, None),
])
def test_KHONG_DOC_DUOC_tra_2_chu_KHONG_tra_0(repo, toan_cuc):
    """Không đọc được một trong hai file mà trả 0 thì chính công cụ này
    là cổng xanh giả — đúng thứ nó sinh ra để chặn."""
    assert ks.so_sanh(repo, toan_cuc)[0] == 2


def test_settings_RONG_khong_phai_loi_doc():
    """`{}` nghĩa là đọc được và không có hook nào — khác hẳn `None`."""
    assert ks.so_sanh({"hooks": {}}, {"hooks": {}})[0] == 0


# ══ 4. Cửa mở phiên phải THẬT SỰ gọi nó ═══════════════════════════════

def test_cua_mo_phien_CO_GOI_kiem_cua_song():
    """Đọc bằng AST, không bằng `in`: khối chú thích của chính hàm ấy đã
    chứa tên file kia."""
    cay = ast.parse((GOC / "tools/cua_mo_phien.py").read_text(encoding="utf-8"))
    h = [n for n in ast.walk(cay)
         if isinstance(n, ast.FunctionDef) and n.name == "trang_thai_cua"]
    assert h, "cua_mo_phien.py khong co ham trang_thai_cua"
    nhap = {a.name for n in ast.walk(h[0])
            if isinstance(n, ast.ImportFrom) for a in n.names}
    assert "bao_cao" in nhap, "trang_thai_cua khong nhap bao_cao"
    goi = {n.func.id for n in ast.walk(h[0])
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "bao_cao" in goi, "co nhap ma KHONG goi"
    print("PASS  cua_mo_phien goi that")


def test_ban_tin_CO_dong_trang_thai_cua():
    sys.path.insert(0, str(GOC / "tools"))
    import cua_mo_phien
    assert "CUA:" in cua_mo_phien.ban_tin(), "ban tin thieu dong trang thai"


def test_trang_thai_cua_KHONG_BAO_GIO_nem():
    """Mở phiên hỏng vì một dòng trang trí là cái giá không đáng trả."""
    sys.path.insert(0, str(GOC / "tools"))
    import cua_mo_phien
    that = ks.bao_cao
    try:
        ks.bao_cao = lambda **_: 1 / 0
        assert isinstance(cua_mo_phien.trang_thai_cua(), str)
    finally:
        ks.bao_cao = that


# ══ 5. File settings THẬT của repo phải đọc được ══════════════════════

def test_settings_cua_repo_doc_duoc_va_CO_hook():
    d = ks._doc(ks.SETTINGS_REPO)
    assert d is not None, "khong doc duoc .claude/settings.json cua repo"
    assert ks.doc_hook(d), "settings cua repo khong khai hook nao"
    print(f"PASS  settings repo khai {len(ks.doc_hook(d))} hook")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_") and not hasattr(ham, "pytestmark"):
            ham()
