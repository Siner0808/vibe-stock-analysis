"""Nhật ký cửa Bash — ghi ở CẢ BA ngả, và không bao giờ giết cửa.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 14/09/2026 câu *"nới luật này có bắt nhầm không"* cắn hai lần (lỗi
49, rồi BƯỚC 65), và cả hai lần chỉ đo được trên **proxy** — 69 dòng lệnh
trong tài liệu, 20 lệnh `TOT`. Quần thể đúng là **lệnh thật sự được gõ**,
mà cửa Bash tới hôm ấy **không ghi gì**.

HAI ĐIỀU PHẢI KHOÁ, VÀ CÁI THỨ NHẤT KHÔNG HIỂN NHIÊN
────────────────────────────────────────────────────
1. **Ghi ở CẢ BA ngả** — `CHO-QUA` · `CHAN` · `THOAT`. Một nhật ký chỉ
   có mẫu XẤU thì vẫn **không** trả lời được câu *"nới ra thì bắt NHẦM
   cái gì"*, tức vẫn để nguyên cái lỗ đã sinh ra lỗi 49.
2. **Ghi hỏng thì cửa vẫn phán đúng.** Nhật ký là thứ phụ. Một cửa an
   toàn chết vì cái nhật ký của nó là một cửa tệ hơn cửa không có nhật ký.

Và điều thứ nhất phải kiểm bằng **AST ở CHỖ NỐI**, không bằng "hàm có tồn
tại": bài học lỗi 20 và `bay.md` mục 1 — *"hàm X có tồn tại" khác "nhánh Y
có gọi X"*.
"""
import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import cua_bash_an_toan as cb  # noqa: E402
import soat_nhat_ky_cua as sn  # noqa: E402

PY = sys.executable
CUA = GOC / "tools" / "cua_bash_an_toan.py"
DOC = GOC / "tools" / "soat_nhat_ky_cua.py"


def _chay_cua(lenh: str, temp: Path) -> int:
    """Bơm payload giả vào cửa, với TEMP trỏ sang thư mục riêng."""
    import os

    moi = dict(os.environ, TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp))
    r = subprocess.run(
        [PY, str(CUA)],
        input=json.dumps({"tool_name": "Bash",
                          "tool_input": {"command": lenh}}),
        capture_output=True, text=True, encoding="utf-8", env=moi)
    return r.returncode


def test_GHI_o_CA_BA_NGA_khong_chi_nga_CHAN(tmp_path):
    """Phép kiểm chính. Chỉ ghi ngả CHẶN là để nguyên lỗ của lỗi 49."""
    for lenh in ("git status --short",                       # CHO-QUA
                 "sed -i 's/a/b/' CLAUDE.md",                # CHAN
                 "sed -i 's/a/b/' x.md # cua-ok: thu nhat ky"):  # THOAT
        _chay_cua(lenh, tmp_path)

    log = tmp_path / cb.TEN_NHAT_KY
    assert log.exists(), "cua khong ghi gi ca"
    bg = [json.loads(d) for d in log.read_text(encoding="utf-8").splitlines()
          if d.strip()]
    phan = [b["phan"] for b in bg]
    assert phan == ["CHO-QUA", "CHAN", "THOAT"], (
        f"thieu nga: {phan}. Mot nhat ky chi co mau XAU khong tra loi duoc "
        f"cau 'noi ra thi bat NHAM cai gi'.")
    assert bg[1]["luat"] == ["sed-i-file-repo"]
    assert bg[0]["lenh"] == "git status --short"
    print("PASS  ghi du ba nga CHO-QUA · CHAN · THOAT")


def test_MAIN_goi_ghi_nhat_ky_TRUOC_khi_re_nhanh__doc_bang_AST():
    """"Hàm có tồn tại" khác "nhánh có gọi nó" — lỗi 20, `bay.md` mục 1.

    Lời gọi phải nằm **trước** `if not pham: return 0`. Đặt sau đó thì
    ngả CHO-QUA không bao giờ được ghi, và test ở trên là thứ duy nhất
    biết — nhưng nó chạy tiến trình con, nên một phép đọc tĩnh ở đây là
    lưới thứ hai, rẻ và không phụ thuộc môi trường.
    """
    cay = ast.parse(CUA.read_text(encoding="utf-8"))
    main = next(n for n in ast.walk(cay)
                if isinstance(n, ast.FunctionDef) and n.name == "main")

    goi = [i for i, n in enumerate(main.body)
           if any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                  and c.func.id == "ghi_nhat_ky" for c in ast.walk(n))]
    assert goi, "main() khong goi ghi_nhat_ky — nhat ky ton tai nhung khong noi"

    ve = [i for i, n in enumerate(main.body)
          if isinstance(n, ast.If) and any(isinstance(c, ast.Return)
                                           for c in ast.walk(n))]
    sau_cung = [i for i in ve if i > goi[0]]
    assert sau_cung, (
        "ghi_nhat_ky duoc goi SAU moi nhanh `return` — nga CHO-QUA khong "
        "bao gio duoc ghi")
    print("PASS  ghi_nhat_ky duoc goi TRUOC nhanh re dau tien")


def test_GHI_HONG_thi_CUA_VAN_PHAN_DUNG(monkeypatch, tmp_path):
    """Nhật ký là thứ PHỤ. Cửa chết vì nó là cửa tệ hơn cửa không có nó."""
    def no(*a, **k):
        raise OSError("o dia day")

    monkeypatch.setattr(cb, "duong_nhat_ky", no)
    # Khong duoc nem ra ngoai.
    cb.ghi_nhat_ky("git status", [], False)

    # Va phep phan khong doi.
    assert [t for t, _ in cb.kiem("sed -i 's/a/b/' CLAUDE.md")] == \
        ["sed-i-file-repo"]
    print("PASS  ghi hong -> nhuong duong, phep phan khong doi")


def test_NHAT_KY_nam_trong_THU_MUC_TAM_khong_trong_repo():
    """Nội dung là đúng thứ đã gõ vào Bash — nó không bao giờ được commit."""
    d = cb.duong_nhat_ky()
    assert str(d).startswith(tempfile.gettempdir()), \
        f"nhat ky khong nam trong TEMP: {d}"
    assert GOC not in d.parents, "nhat ky nam TRONG repo — se bi commit"
    print(f"PASS  nhat ky nam trong TEMP, ngoai repo")


# ───────────────────────── dụng cụ đọc ─────────────────────────

def test_THU_MAU_di_qua_kiem__khong_dung_lai_phep_phan():
    """Dựng lại phép phán trong dụng cụ đọc là bẫy "test KIỂM LẠI CHÍNH NÓ".

    Nó phải **thay mẫu vào `LUAT` rồi gọi `kiem()`**, để đi qua đúng phạm
    vi đọc mà luật ấy khai (`DOC_THO` · `DOC_GIU_NHAY` · `DOC_BOC`).
    """
    cay = ast.parse(DOC.read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "thu_mau")
    goi = {c.func.attr for c in ast.walk(ham)
           if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
    assert "kiem" in goi, "thu_mau khong goi kiem() — no tu dung lai phep phan"
    print("PASS  thu_mau di qua kiem(), khong dung lai phep phan")


def test_THU_MAU_HOAN_TRA_LUAT_du_co_no_giua_chung():
    """Để `LUAT` bị đổi sau một lượt thử là làm hỏng mọi phép phán sau."""
    goc = cb.LUAT
    ra = sn.thu_mau("sed-i-file-repo", r"KHONG-KHOP-GI-CA", "sed -i x")
    assert cb.LUAT is goc, "LUAT khong tro ve ban goc"
    assert "sed-i-file-repo" not in ra

    try:
        sn.thu_mau("sed-i-file-repo", r"(", "sed -i x")   # regex hong
    except Exception:
        pass
    assert cb.LUAT is goc, "LUAT khong tro ve khi co ngoai le"
    print("PASS  thu_mau hoan tra LUAT, ke ca khi no")


def test_DOC_NHAT_KY_bo_qua_dong_hong_va_DEM_no(tmp_path, capsys):
    """Dòng hỏng bị bỏ qua trong im lặng thì con số phía sau là số dối."""
    f = tmp_path / "x.log"
    f.write_text('{"phan":"CHAN","lenh":"a","luat":[]}\nKHONG-PHAI-JSON\n\n'
                 '{"phan":"CHO-QUA","lenh":"b","luat":[]}\n',
                 encoding="utf-8")
    bg = sn.doc_nhat_ky(f)
    assert len(bg) == 2
    assert "1 dong hong" in capsys.readouterr().err
    assert sn.doc_nhat_ky(tmp_path / "khong-co.log") == []
    print("PASS  dong hong bi bo qua VA duoc dem")


def test_DUNG_CU_DOC_chay_duoc_va_THOAT_2_khi_luat_khong_co():
    """Tên luật không có phải là CHƯA KIỂM ĐƯỢC, không phải 'sach'."""
    r = subprocess.run([PY, str(DOC), "--thu-luat", "khong-ton-tai",
                        "--mau", "x"],
                       capture_output=True, text=True, encoding="utf-8",
                       cwd=str(GOC))
    assert r.returncode == 2, f"ma thoat {r.returncode}, phai la 2"
    assert "CHUA KIEM DUOC" in r.stderr
    print("PASS  luat khong co -> ma thoat 2")
