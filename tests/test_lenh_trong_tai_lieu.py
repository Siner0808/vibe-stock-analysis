"""Lệnh viết trong TÀI LIỆU phải là lệnh cửa gác Bash cho chạy.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 14/09/2026 đếm được **30 dòng lệnh** trong tài liệu của repo mà
`tools/cua_bash_an_toan.py` sẽ chặn nếu có ai gõ. 13 dòng là chỉ dẫn sống.

Nặng nhất: luật `python-he-thong` tự khai nguồn của nó là *"QUY UOC, chep
tu docs/HANDOFF.md muc 1"* — mà mục ấy vi phạm đúng luật đó **ba lần**.
Cái gác dẫn một tài liệu ra làm nguồn, và tài liệu ấy làm ngược lại điều
nó dạy. Không gác nào thấy, vì chưa có gì đối chiếu hai bên.

Gác này đối chiếu, bằng cách **gọi chính `kiem()`** của cửa Bash — không
chép luật sang, không quét chữ. Luật đổi thì phép soát đổi theo.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
DUNG_CU = GOC / "tools" / "soat_lenh_tai_lieu.py"

sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import cua_bash_an_toan as cb  # noqa: E402
import soat_lenh_tai_lieu as slt  # noqa: E402


def _md(*dong: str) -> str:
    return "\n".join(dong) + "\n"


def test_REPO_khong_con_dong_lenh_nao_bi_cua_Bash_chan():
    """Phép kiểm chính. Thêm một lệnh `python …` vào tài liệu → đỏ."""
    ma = slt.main([])          # [] chu khong None: dung nhai co cua pytest
    assert ma == 0, (
        "Con dong lenh trong tai lieu bi chinh cua gac Bash chan.\n"
        "Chay `./.venv/Scripts/python.exe tools/soat_lenh_tai_lieu.py` "
        "de xem tung dong.")


def test_PHEP_THU_bat_dung_NGUYEN_VAN_loi_that():
    """Dựng lại **nguyên văn** ba dòng của `docs/HANDOFF.md` mục 1.

    Đây là câu hỏi duy nhất đáng hỏi về một cái gác mới: nó có bắt được
    đúng thứ nó sinh ra để bắt không. Mẫu dựng tay, không đọc file thật —
    một gác chỉ chạy trên đầu vào sạch thì mọi phép nới đều sống sót
    (lỗi 34).
    """
    that = _md(
        "## 1. BON LENH DAU TIEN",
        "",
        "```bash",
        "pytest tests/ -q",
        "python tools/kiem_cu_phap_311.py",
        "python tools/chan_bia_so_lieu.py --quet-repo",
        "python tools/kiem_test_chay_rieng.py",
        "```",
    )
    vp = slt.soat_mot_file("docs/HANDOFF.md", that, cb.kiem)
    assert len(vp) == 3, f"phai bat DUNG 3 dong `python …`, bat duoc {len(vp)}"
    assert all("python-he-thong" in v[3] for v in vp)
    # `pytest tests/ -q` KHONG bi chan — no la lenh hop le.
    assert all("pytest tests/ -q" not in v[2] for v in vp)


def test_LENH_DUNG_thi_KHONG_bi_bat():
    """Bắt nhầm lệnh hợp lệ còn hại hơn bỏ sót: nó dạy người ta tắt gác."""
    tot = _md(
        "```bash",
        "./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py",
        "./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/kq.log 2>&1",
        "git -C <repo> status --short",
        "gh pr checks 104",
        "```",
    )
    assert slt.soat_mot_file("x.md", tot, cb.kiem) == []


def test_DAU_CHO_PHEP_can_mot_LY_DO_THAT():
    """Cửa thoát giống `# bia-ok:` — không cấm, buộc NÓI RA.

    Ba mức phải phân biệt được: không dấu · dấu rỗng · dấu có lý do thật.
    """
    xau = "cat > tests/test_x.py <<'PYEOF'"

    khong_dau = _md("```bash", xau, "```")
    assert len(slt.soat_mot_file("x.md", khong_dau, cb.kiem)) == 1

    dau_rong = _md("```bash", "# lenh-xau-ok:", xau, "```")
    assert len(slt.soat_mot_file("x.md", dau_rong, cb.kiem)) == 1, \
        "dau RONG phai bi tu choi"

    dau_ngan = _md("```bash", "# lenh-xau-ok: co y", xau, "```")
    assert len(slt.soat_mot_file("x.md", dau_ngan, cb.kiem)) == 1, \
        "ly do chung chung phai bi tu choi"

    dau_that = _md(
        "```bash",
        "# lenh-xau-ok: nguyen van lenh da xoa 40 phep kiem ngay 09/09/2026",
        xau, "```")
    assert slt.soat_mot_file("x.md", dau_that, cb.kiem) == []


def test_DAU_phai_DINH_vao_dong_lenh_chu_khong_troi_tu_do():
    """Một dấu ở đầu khối KHÔNG được che cho mọi dòng phía dưới.

    Nếu nó trôi được thì một lý do viết cho lệnh A sẽ lặng lẽ miễn cho
    lệnh B chẳng liên quan — đúng hình dạng `# bia-ok:` đặt sai chỗ.
    """
    ly_do = "# lenh-xau-ok: nguyen van lenh da gay loi 23 ngay 09/09/2026"
    troi = _md(
        "```bash",
        ly_do,
        "",                        # dong trong XOA dau
        "python run_daily.py",
        "```",
    )
    assert len(slt.soat_mot_file("x.md", troi, cb.kiem)) == 1, \
        "dau phai bi dong trong xoa, khong duoc che cho dong duoi"

    hai_dong = _md(
        "```bash",
        ly_do,
        "cat > tests/test_x.py <<'PYEOF'",
        "python run_daily.py",       # dong THU HAI khong con dau
        "```",
    )
    vp = slt.soat_mot_file("x.md", hai_dong, cb.kiem)
    assert len(vp) == 1 and "run_daily" in vp[0][2]


def test_CHU_THICH_va_KHOI_KHONG_PHAI_BASH_deu_bi_bo_qua():
    """Dòng chú thích không phải lệnh — nên chính cái dấu không tự kích
    hoạt phép soát. Và khối ```python là mã, không phải lệnh shell."""
    ma_python = _md(
        "```python",
        "python run_daily.py",     # chuoi trong khoi PYTHON, khong phai lenh
        "```",
        "```text",
        "python paper_runner.py",
        "```",
    )
    assert slt.soat_mot_file("x.md", ma_python, cb.kiem) == []

    chi_chu_thich = _md("```bash", "# python run_daily.py", "```")
    assert slt.soat_mot_file("x.md", chi_chu_thich, cb.kiem) == []


def test_ly_do_hop_le_la_ham_THUAN_va_NGUONG_ghim_bang_SO_VIET_THANG():
    """`DAI_TOI_THIEU` ghim bằng một SỐ VIẾT THẲNG, không đọc từ module.

    Đọc hằng số từ chính module đang thử làm mù cả hai vế — đột biến nó
    thì phép kiểm đi theo và vẫn xanh. Lỗi ấy mắc ở BƯỚC 58, sửa xong,
    rồi mắc LẠI y nguyên ở BƯỚC 60 chưa đầy một giờ sau.
    """
    assert slt.DAI_TOI_THIEU == 24

    assert not slt.ly_do_hop_le("")
    assert not slt.ly_do_hop_le("   ")
    assert not slt.ly_do_hop_le("ok")
    assert not slt.ly_do_hop_le("x" * 23), "23 ky tu phai NGAN qua"
    assert slt.ly_do_hop_le("x" * 24), "dung 24 ky tu phai DU"
    assert not slt.ly_do_hop_le("  " + "x" * 20 + "  "), "dem SAU khi cat"


def test_KHAI_MIEN_co_ly_do_doi_thi_bi_goi_TEN():
    """Miễn ở mức file là quyết định nặng nhất — soi kỹ nhất ở đây.

    `kiem_khai` trả **tên** chứ không trả `bool`: một danh sách rỗng đọc
    xuôi là lành, và khác rỗng thì luôn nghĩa là có việc phải làm. Cùng
    lý do `dot_bien_bo` trả phát sống sót thay vì đếm phát chết.
    """
    assert slt.kiem_khai({}) == []
    assert slt.kiem_khai({"a.md": "x" * 24}) == []
    assert slt.kiem_khai({"a.md": "ok", "b.md": "x" * 24, "c.md": ""}) \
        == ["a.md", "c.md"]


def test_CHI_file_DUOC_KHAI_moi_duoc_mien():
    """Một lỗi bỏ qua MỌI file cũng cho ra 0 vi phạm.

    Không có con số thứ hai thì hai trạng thái ấy không phân biệt được —
    nên `soat_nhieu` trả luôn danh sách đã soát. Vòng lặp đột biến tìm ra
    đúng chỗ này: phát *"miễn TẤT CẢ các file"* sống sót ở bản đầu, vì
    sau khi tài liệu đã sạch thì miễn hết cũng ra 0.
    """
    xau = _md("```bash", "python run_daily.py", "```")
    tot = _md("```bash", "./.venv/Scripts/python.exe run_daily.py", "```")
    kho = {"a.md": tot, "b.md": xau, "so-nhat-ky.md": xau}

    vp, da_soat = slt.soat_nhieu(sorted(kho), {}, kho.get, cb.kiem)
    assert da_soat == ["a.md", "b.md", "so-nhat-ky.md"]
    assert len(vp) == 2

    khai = {"so-nhat-ky.md": "so chi-them, moi dong la ban ghi lich su"}
    vp, da_soat = slt.soat_nhieu(sorted(kho), khai, kho.get, cb.kiem)
    assert da_soat == ["a.md", "b.md"], "CHI file duoc khai moi duoc bo qua"
    assert len(vp) == 1 and vp[0][0] == "b.md"


def test_SO_NHAT_KY_duoc_mien_nhung_phai_KHAI_kem_ly_do():
    """Miễn ở mức file là một quyết định — nó phải nằm trong diff.

    `docs/STATE.md` là sổ chỉ-thêm: mọi dòng lệnh trong đó là bản ghi của
    lệnh ĐÃ CHẠY ngày ấy. Sửa chúng là viết lại lịch sử đo lường.
    """
    khai = slt.doc_khai_nhat_ky(GOC)
    assert "docs/STATE.md" in khai, "so nhat ky phai duoc khai ra"
    for ten, ly_do in khai.items():
        assert slt.ly_do_hop_le(ly_do), f"ly do cho `{ten}` khong hop le"
        assert (GOC / ten).exists(), f"khai mot file khong ton tai: {ten}"


def test_DUNG_CU_goi_CHINH_ham_kiem_cua_cua_Bash():
    """Kiểm CƠ CHẾ, không kiểm chữ.

    Nếu công cụ chép danh sách luật sang thay vì gọi `kiem()`, hai bên sẽ
    trôi ra khỏi nhau và gác này thành một bản sao lạc hậu của cửa Bash.
    Đọc bằng AST vì docstring của chính công cụ có nhắc `kiem` (lỗi 38).
    """
    cay = ast.parse(DUNG_CU.read_text(encoding="utf-8"))
    nhap = {n.module for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    ten_nhap = {a.name for n in ast.walk(cay)
                if isinstance(n, ast.Import) for a in n.names}
    assert "cua_bash_an_toan" in (nhap | ten_nhap), \
        "cong cu phai NHAP cua_bash_an_toan, khong chep luat sang"

    # Và nó phải LẤY hàm `kiem` ra từ module ấy. Hình dạng cần tìm là
    # `<gì đó>.kiem` — một tham chiếu thuộc tính. KHÔNG phải `ast.Call`
    # có `func` là Attribute: công cụ truyền `cb.kiem` vào như một giá
    # trị rồi gọi nó dưới tên trần `kiem(...)`, nên tìm lời gọi thuộc
    # tính sẽ không thấy gì. Bản đầu của phép kiểm này tìm đúng như vậy
    # và đỏ oan — chính nó dạy lại rằng phải nhìn hình dạng THẬT.
    thuoc_tinh = {n.attr for n in ast.walk(cay)
                  if isinstance(n, ast.Attribute)}
    assert "kiem" in thuoc_tinh, \
        "phai lay ham kiem() cua cua Bash ra dung, khong tu phan"
