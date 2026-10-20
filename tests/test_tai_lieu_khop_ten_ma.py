"""Gác: mọi `module.tên` tài liệu trỏ tới phải TỒN TẠI trong mã.

Canh `CLAUDE.md` và `docs/HANDOFF.md` — xem `CAC_TAI_LIEU`.

Ngày 05/09/2026 một lượt soát bằng máy tìm ra **hai con trỏ chết** sống
trong tài liệu không biết bao lâu:

    CLAUDE.md ghi                       ma that
    ----------------------------------  ------------------------------
    `sheets_store._COLS`                sheets_store.TRADE_COLS
    `fundamental_agent._doc()`          fundamental_agent.doc_chi_so()

Cả hai đều **đúng nội dung, sai địa chỉ**: `created_at` thật sự nằm trong
bảng cột, và cơ chế chấm-nhầm-thước-ngân-hàng thật sự tồn tại. Chỉ có cái
tên là dẫn người đọc tới hư không.

VÌ SAO LOẠI NÀY ĐÁNG MỘT BỘ GÁC RIÊNG
─────────────────────────────────────
Nó khác hai bộ gác tài liệu đã có, và khác ở chỗ dễ:

* `test_tai_lieu_khop_hang_so.py` canh **giá trị** hằng số. Giá trị thì
  có lịch sử, nên gác ấy buộc phải chấp nhận số cũ nằm cạnh số mới.
* `test_lich_cron_chuong.py` canh **giờ** cron. Cũng là giá trị.
* Bộ này canh **sự tồn tại của một cái tên**. Một cái tên thì hoặc có
  hoặc không — không có "tên cũ giữ lại để đối chiếu" nào cả. Nên gác
  này được phép nghiêm khắc, và không cần bán kính hay quy ước gì.

Cũng là loại mà **Gemini Notebook không bao giờ bắt được** (đã thử ngày
04 và 05/09): nó đọc văn bản, còn đây là tài liệu lệch MÃ.

MIỄN TRỪ PHẢI CÓ LÝ DO
──────────────────────
`MIEN_TRU` giữ những cặp cố ý trỏ tới thứ không còn/chưa bao giờ nằm
trong mã — cùng quy ước với cửa thoát `# bia-ok:` của
`tools/chan_bia_so_lieu.py`: không cấm, nhưng buộc nói ra vì sao.
"""
import ast
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

#: Các tài liệu bị canh. `docs/HANDOFF.md` vào đây ngày 05/09/2026 vì nó
#: đứng ĐẦU thứ tự ưu tiên (`HANDOFF` → `STATE` → `CLAUDE.md`) mà lại là
#: file cũ nhất — bản trước sống 16 ngày với mọi khẳng định sự kiện đã
#: sai, gồm cả câu bảo người đọc dừng lại nếu số test khác 218.
#:
#: `docs/STATE.md` CỐ Ý không nằm ở đây: nó là nhật ký, nên một cái tên
#: đúng-tại-thời-điểm-viết trong một mục có ngày tháng không phải lỗi.
CAC_TAI_LIEU = ("CLAUDE.md", "docs/HANDOFF.md")

#: Thư mục có mã nguồn được coi là "module của dự án".
THU_MUC = ("", "tools", "backtest")

#: Số ký tự tối thiểu của tài liệu. Một file đọc hụt làm mọi phép kiểm
#: bên dưới thành vô nghĩa mà vẫn XANH — cùng lý do có `SAN_KY_TU` ở
#: `tests/test_tai_lieu_khop_hang_so.py`.
SAN_KY_TU = {"CLAUDE.md": 20_000, "docs/HANDOFF.md": 5_000}

#: `module.tên` — module viết thường (theo PEP 8), tên là định danh.
#: Cố ý KHÔNG bắt `Class.thuộc_tính`: thuộc tính dataclass và thuộc tính
#: gán trong `__init__` không nằm ở cấp module, và một gác nửa vời trên
#: chúng sẽ đỏ giả.
RE_CAP = re.compile(r"`([a-z_][a-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)")

#: Đuôi file — `run_daily.py` khớp RE_CAP nhưng "py" không phải một tên.
DUOI = {"py", "yml", "yaml", "json", "md", "csv", "toml", "html", "db",
        "txt", "broken", "example", "lock", "cfg", "ini"}

#: Cặp CỐ Ý trỏ ra ngoài mã. Thêm vào đây phải kèm lý do.
MIEN_TRU = {
    # `vnai` là thư viện ngoài, không nằm trong repo.
    ("vnai", "load_skill"),
    ("vnai", "setup_agent_environment"),
}


def _ten_cap_module(p: Path) -> set[str]:
    """Tên định nghĩa ở CẤP MODULE, cộng tên phương thức của các lớp."""
    try:
        cay = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    ra: set[str] = set()
    for n in cay.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ra.add(n.name)
        elif isinstance(n, ast.ClassDef):
            ra.add(n.name)
            for c in n.body:
                if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    ra.add(c.name)
                elif isinstance(c, ast.AnnAssign) and isinstance(c.target, ast.Name):
                    ra.add(c.target.id)
                elif isinstance(c, ast.Assign):
                    for t in c.targets:
                        if isinstance(t, ast.Name):
                            ra.add(t.id)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    ra.add(t.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            ra.add(n.target.id)
    return ra


def _cac_module(goc: Path = GOC) -> dict[str, set[str]]:
    """Tên tệp -> tập tên cấp module, HỢP qua mọi thư mục của `THU_MUC`.

    Tài liệu viết `module.tên`, không viết thư mục, nên hai tệp cùng tên ở gốc và
    `tools/` là MỘT khoá. Bản cũ gán đè (`ra[p.stem] = …`): tệp đọc sau xoá tập tên
    của tệp đọc trước, và ngày 17/10/2026 hằng số có thật của `hau_kiem_loi.py` ở gốc
    bị báo chết (BƯỚC 205, lỗi 183). Gom HỢP: một tên sống khi CÓ trong ít nhất một
    tệp cùng tên.
    """
    ra: dict[str, set[str]] = {}
    for tm in THU_MUC:
        thu_muc = goc / tm if tm else goc
        for p in sorted(thu_muc.glob("*.py")):
            ra.setdefault(p.stem, set()).update(_ten_cap_module(p))
    return ra


def _doc(ten: str = "CLAUDE.md") -> str:
    p = GOC / ten
    src = p.read_text(encoding="utf-8")
    san = SAN_KY_TU[ten]
    assert len(src) >= san, (
        f"{ten} chỉ đọc được {len(src)} ký tự (sàn {san}) — gác này đang "
        f"canh một file rỗng hoặc đọc hụt")
    return src


def _cap_can_kiem(src: str, mods: dict[str, set[str]]) -> list[tuple[str, str]]:
    """Các cặp `module.tên` mà module CÓ THẬT trong dự án."""
    ra = []
    for mod, ten in RE_CAP.findall(src):
        if ten in DUOI or mod not in mods or (mod, ten) in MIEN_TRU:
            continue
        if (mod, ten) not in ra:
            ra.append((mod, ten))
    return ra


def _con_tro_chet(src: str, mods: dict[str, set[str]]) -> list[str]:
    """Các cặp trỏ tới tên KHÔNG tồn tại.

    Tách thành hàm riêng CÓ CHỦ ĐÍCH: để phép phán này nằm thẳng trong
    thân test thì đột biến `chet = []` sống sót, vì `test_MAY_DO…` đi qua
    hàm TRÍCH chứ không qua hàm PHÁN. Đúng cái bẫy đã sống sót nhiều lượt
    đục trong hai ngày 04–05/09/2026.
    """
    return [f"{m}.{t}" for m, t in _cap_can_kiem(src, mods)
            if t not in mods[m]]


@pytest.mark.parametrize("ten", CAC_TAI_LIEU)
def test_moi_ten_tai_lieu_tro_toi_deu_ton_tai(ten):
    """Đổi tên hàm/hằng mà quên tài liệu → đỏ."""
    mods = _cac_module()
    src = _doc(ten)
    assert _cap_can_kiem(src, mods), (
        f"không trích được cặp `module.tên` nào từ {ten} — biểu thức "
        f"trích đã hỏng, và một gác không trích được gì thì luôn xanh")

    chet = _con_tro_chet(src, mods)
    assert not chet, (
        f"{ten} trỏ tới những tên KHÔNG TỒN TẠI trong mã: "
        + ", ".join(sorted(chet))
        + ". Sửa tài liệu cho khớp mã, hoặc — nếu cố ý trỏ ra ngoài repo "
          "— thêm vào MIEN_TRU KÈM LÝ DO.")


def test_DANH_SACH_tai_lieu_khong_duoc_thu_hep_am_tham():
    """Rút danh sách xuống một file là bỏ gác cho file kia."""
    assert CAC_TAI_LIEU == ("CLAUDE.md", "docs/HANDOFF.md"), (
        "bỏ bớt tài liệu bị canh — sửa CÓ CHỦ ĐÍCH kèm lý do. "
        "`docs/HANDOFF.md` đứng ĐẦU thứ tự ưu tiên nên là file nguy hiểm "
        "nhất khi cũ.")


def test_MAY_DO_tu_chung_minh_no_bat_duoc():
    """Mã thật đang khớp, nên máy dò hỏng trả cùng đáp án với máy dò tốt.

    Đúng cái bẫy đã sống sót nhiều lượt đục trong hai ngày 04–05/09/2026.
    Cách duy nhất tách hai trường hợp là cho nó ăn mẫu đã biết là xấu.
    """
    mods = {"vi_du": {"co_that", "HANG_SO"}}

    # ĐI QUA `_con_tro_chet`, không đi vòng qua nó.
    xau = "`vi_du.khong_he_co` và `vi_du.cung_khong_co`"
    assert _con_tro_chet(xau, mods) == ["vi_du.khong_he_co",
                                        "vi_du.cung_khong_co"], (
        "máy dò không báo hai tên ĐÃ BIẾT là chết — nó đang trả rỗng cho "
        "mọi thứ, tức không kiểm gì cả")

    tot = "`vi_du.co_that` và `vi_du.HANG_SO`"
    assert _con_tro_chet(tot, mods) == [], (
        "máy dò báo chết cho tên ĐANG ĐÚNG — nó sẽ đỏ giả khắp nơi")

    # Đuôi file KHÔNG được coi là tên: `run_daily.py` phải bị bỏ qua,
    # nếu không gác đỏ giả ở mọi chỗ nhắc tên file.
    assert _cap_can_kiem("`vi_du.py`", mods) == [], \
        "đuôi file bị coi là tên — gác sẽ đỏ giả khắp nơi"

    # Module không thuộc dự án thì không phải việc của gác này.
    assert _cap_can_kiem("`khong_phai_module_du_an.gi_do`", mods) == [], \
        "gác đang phán về module không có trong dự án"


def test_CA_THAT_17_10_ten_cua_module_GOC_trung_ten_voi_TOOLS_van_SONG():
    """Dựng lại nguyên văn ca 17/10/2026 (BƯỚC 205, lỗi 183).

    `docs/HANDOFF.md` ghi `hau_kiem_loi.NGAY_HAU_KIEM_LOI_BAT_DAU` — hằng số CÓ THẬT
    trong `hau_kiem_loi.py` ở gốc — mà gác báo con trỏ chết: bản gom theo tên tệp để
    `tools/hau_kiem_loi.py` (cùng tên) ĐÈ tập tên của module gốc. BƯỚC 205 lách bằng
    cách viết lại câu trong HANDOFF; đây là chỗ sửa gác.
    """
    mods = _cac_module()
    for tm in ("", "tools"):
        assert (GOC / tm / "hau_kiem_loi.py").is_file(), (
            "ca thật cần CẢ HAI tệp `hau_kiem_loi.py` (gốc và tools/) — đổi tên "
            "một bên thì sửa test này CÓ CHỦ ĐÍCH")
    assert _con_tro_chet("`hau_kiem_loi.NGAY_HAU_KIEM_LOI_BAT_DAU`", mods) == [], (
        "tên của module GỐC bị coi là chết vì module cùng tên ở tools/ đè lên")
    assert _con_tro_chet("`hau_kiem_loi.main`", mods) == [], (
        "tên của module ở tools/ bị coi là chết — gom phải là HỢP, không phải đè "
        "theo chiều ngược lại")


def test_MODULE_TRUNG_TEN_o_BA_thu_muc_gom_HOP_khong_DE(tmp_path):
    """Ba tệp cùng tên ở gốc, `tools/`, `backtest/`: tên của CẢ BA phải sống, và tên
    không có ở tệp nào vẫn chết. Đi qua `_cac_module` thật (thư mục giả) rồi qua
    `_con_tro_chet` — hàm PHÁN, không phải hàm trích."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "backtest").mkdir()
    (tmp_path / "x_trung.py").write_text("HANG_GOC = 1\n", encoding="utf-8")
    (tmp_path / "tools" / "x_trung.py").write_text(
        "def ham_tools():\n    return 1\n", encoding="utf-8")
    (tmp_path / "backtest" / "x_trung.py").write_text(
        "class LopBacktest:\n    pass\n", encoding="utf-8")
    (tmp_path / "x_rieng.py").write_text("RIENG = 1\n", encoding="utf-8")

    mods = _cac_module(tmp_path)
    assert mods["x_rieng"] == {"RIENG"}
    src = ("`x_trung.HANG_GOC` `x_trung.ham_tools` `x_trung.LopBacktest` "
           "`x_trung.khong_co_o_dau` `x_rieng.RIENG`")
    assert _con_tro_chet(src, mods) == ["x_trung.khong_co_o_dau"], (
        "gom theo tên tệp phải là HỢP: tên của mọi tệp cùng tên đều sống, tên "
        "không tệp nào có thì vẫn chết")


def test_HAI_CON_TRO_CHET_cua_05_09_khong_duoc_quay_lai():
    """Ghim đúng hai tên đã hỏng, để lần sửa ngược lại thì đỏ ngay."""
    mods = _cac_module()
    assert "_COLS" not in mods["sheets_store"], (
        "nếu `_COLS` được tạo lại thì sửa test này CÓ CHỦ ĐÍCH")
    assert "TRADE_COLS" in mods["sheets_store"]
    assert "_doc" not in mods["fundamental_agent"]
    assert "doc_chi_so" in mods["fundamental_agent"]

    src = _doc()
    # Chinh van ban la thu can kiem, khong phai loi goi.
    # van-ban-ok: quy uoc du an — TEN DA CHET khong duoc co mat trong tai lieu
    assert "sheets_store._COLS" not in src
    assert "fundamental_agent._doc(" not in src


def test_MIEN_TRU_khong_duoc_phinh_am_tham():
    """Nhét cặp hỏng vào MIEN_TRU là vô hiệu hoá gác mà test vẫn xanh."""
    assert MIEN_TRU == {("vnai", "load_skill"),
                        ("vnai", "setup_agent_environment")}, (
        "danh sách miễn trừ đã đổi — mỗi cặp phải kèm lý do vì sao nó cố "
        "ý trỏ ra ngoài mã dự án")
    assert SAN_KY_TU == {"CLAUDE.md": 20_000, "docs/HANDOFF.md": 5_000}
    assert set(SAN_KY_TU) == set(CAC_TAI_LIEU), (
        "mỗi tài liệu bị canh phải có sàn ký tự riêng — thiếu một cái "
        "thì `_doc` nổ KeyError chứ không phải đỏ có thông báo")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_tai_lieu_khop_ten_ma.py -q")
