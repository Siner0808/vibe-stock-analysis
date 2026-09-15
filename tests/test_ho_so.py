"""Gác cho `tools/ho_so.py` và cửa `tools/cua_ho_so.py`.

Công cụ này bơm văn bản vào ngữ cảnh của chính tôi, nên nó nằm ở một chỗ
nguy hiểm: một hồ sơ SAI không đỏ ở đâu cả, nó chỉ làm tôi tin nhầm — đúng
hình dạng lỗi 61 (*"một gác sai thì ĐỎ, một máy đo sai thì chỉ in ra một
con số"*). Vì thế phần lớn test ở đây canh **cái nó KHÔNG được làm**.

Ba bất biến lớn nhất:
  1. cửa KHÔNG BAO GIỜ chặn, và không bao giờ thoát khác 0
  2. hồ sơ không vượt trần 10.000 ký tự của `additionalContext`
  3. cột "cách chặn" của bảng lỗi KHÔNG được lẫn sang "chỗ hỏng"
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import cua_ho_so  # noqa: E402
import ho_so  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

#: Ca THẬT đã biết trước: đo 15/09/2026, `paper_trading.py` là file dày
#: nhất ở gốc repo. Nếu phép tra ra 0 tham chiếu cho nó thì máy đo hỏng,
#: không phải repo đổi.
CA_THAT = "paper_trading.py"


def test_ca_that_co_ho_so_day():
    hs = ho_so.doc_ho_so(CA_THAT)
    assert hs.so_tham_chieu >= 10, (
        f"{CA_THAT} đo được {hs.so_tham_chieu} tham chiếu — 15/09/2026 nó "
        f"có 26. Dưới 10 nghĩa là phép tra hỏng, không phải repo gọn lại.")
    assert hs.test and hs.buoc, "thiếu hẳn một nguồn"
    print(f"PASS  {CA_THAT}: {hs.so_tham_chieu} tham chiếu "
          f"({len(hs.test)} test · {len(hs.buoc)} BƯỚC · {len(hs.do)} ĐO)")


def test_HO_SO_khong_vuot_tran_10k():
    """Trần của `additionalContext`. Vượt thì Claude Code thay hồ sơ bằng
    một đường dẫn file — tức công cụ tự vô hiệu hoá chính nó.
    """
    hs = ho_so.HoSo(
        ten="gia.py",
        test=[f"test_gia_{i}.py" for i in range(600)],
        buoc=[f"BƯỚC {i}" for i in range(400)],
        do=[f"ĐO {i}" for i in range(80)],
        loi_cho_hong=[(1, "chua-do")],
    )
    # So với con số của ĐẶC TẢ, KHÔNG so với `ho_so.TRAN_KY_TU`. Dùng
    # hằng số của module làm kỳ vọng thì nới hằng số là nới luôn phép
    # kiểm — đột biến "trần lên 10 triệu" sống sót đúng vì thế ở lượt
    # chạy đầu. `CLAUDE.md` gọi mẫu này là "test kiểm lại chính nó".
    TRAN_DAC_TA = 10_000       # bia-ok: tran cua additionalContext do
    assert ho_so.TRAN_KY_TU <= TRAN_DAC_TA, (   # dac ta hook Claude Code
        f"TRAN_KY_TU = {ho_so.TRAN_KY_TU} vượt trần đặc tả {TRAN_DAC_TA}")
    van = "\n".join(ho_so.dong_ho_so(hs))
    assert len(van) <= TRAN_DAC_TA, f"hồ sơ dài {len(van)} > {TRAN_DAC_TA}"
    assert "lỗi 1" in van, "cắt mất dòng bảng lỗi — nguồn hiếm nhất"
    print(f"PASS  hồ sơ khổng lồ bị cắt còn {len(van)} ký tự, giữ bảng lỗi")


def test_BANG_LOI_tach_cot_gac_khoi_cho_hong():
    """Ca thật: lỗi 65. `test_tran_von_khong_bao_nham.py` là GÁC, nên nó
    KHÔNG được xuất hiện ở chỗ hỏng; `walkforward.py` thì ngược lại.

    Gộp hai cột làm tỷ lệ lặp file nhảy 12% -> 60% (đo 15/09/2026).
    """
    bl = ho_so.bang_loi()
    gac = bl.get("test_tran_von_khong_bao_nham.py", {})
    assert any(s == 65 for s, _ in gac.get("gac", [])), "mất vế GÁC"
    assert not gac.get("cho_hong"), (
        "file GÁC lọt sang cột CHỖ HỎNG — đây là lỗi đọc rộng đã đo")
    wf = bl.get("walkforward.py", {})
    assert any(s == 65 for s, _ in wf.get("cho_hong", [])), (
        "walkforward.py phải nằm ở chỗ hỏng của lỗi 65")
    print("PASS  bảng lỗi tách đúng hai cột")


def test_TEST_NHAP_doc_AST_chu_khong_doc_van_ban(tmp_path):
    """Tên module nằm trong CHÚ THÍCH thì không tính là import.

    `CLAUDE.md`: hai gác viết bằng `"tên" in src` vẫn xanh sau khi xoá
    hẳn lời gọi, vì cái tên còn trong khối chú thích ngay phía trên.
    """
    d = tmp_path / "tests"
    d.mkdir()
    (d / "test_chi_nhac_trong_chu_thich.py").write_text(
        "# file nay chi NHAC toi walkforward trong chu thich\n"
        "# import walkforward\n"
        '"""walkforward cung xuat hien trong docstring."""\n'
        "x = 1\n", encoding="utf-8")
    (d / "test_nhap_that.py").write_text(
        "import walkforward\nY = 2\n", encoding="utf-8")

    ra = ho_so.test_nhap(d)
    assert ra.get("walkforward.py") == ["test_nhap_that.py"], (
        f"đọc văn bản chứ không đọc AST: {ra.get('walkforward.py')}")
    print("PASS  chú thích và docstring không bị tính là import")


def _xoa_dau_vet(*phien: str) -> None:
    """Xoá dấu vết "đã bơm" của các phiên thử.

    KHÔNG phải dọn dẹp cho gọn. File dấu vết nằm ở TEMP và **sống qua
    từng lượt chạy pytest**, nên lượt thứ hai trở đi cửa im — và test
    `khong_bao_gio_chan` lặng lẽ không kiểm gì nữa. Đột biến
    `allow -> deny` SỐNG SÓT đúng vì thế ở lượt đục thử đầu tiên.
    """
    for p in phien:
        f = cua_ho_so._dau_vet(p)
        if f.exists():
            f.unlink()


def _goi_cua(payload: dict) -> tuple[int, str]:
    """Gọi cửa như Claude Code gọi: JSON qua stdin, đọc stdout."""
    kq = subprocess.run(
        [sys.executable, str(GOC / "tools" / "cua_ho_so.py")],
        input=json.dumps(payload), capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=str(GOC.parent))
    return kq.returncode, kq.stdout


def test_CUA_khong_bao_gio_chan_va_khong_bao_gio_thoat_khac_0():
    """Bất biến số một. Cửa chặn của dự án là `cua_doc_bat_buoc`; cửa này
    chỉ bơm. Một `deny` lọt ra đây là chặn một lượt Read hợp lệ của người.
    """
    _xoa_dau_vet("t-chan-1", "t-chan-2", "t-chan-3")
    payloads = [
        {"session_id": "t-chan-1", "tool_input":
            {"file_path": str(GOC / CA_THAT)}},
        {"session_id": "t-chan-2", "tool_input": {"file_path": "/khong/co.py"}},
        {"session_id": "t-chan-3"},
        {},
    ]
    so_lan_kiem = 0
    for p in payloads:
        ma, ra = _goi_cua(p)
        assert ma == 0, f"thoát {ma} với payload {p}"
        if ra.strip():
            d = json.loads(ra)
            quyet = d["hookSpecificOutput"]["permissionDecision"]
            assert quyet == "allow", f"cửa trả {quyet!r}"
            so_lan_kiem += 1
    # Không có lần nào bơm thì chẳng có `permissionDecision` nào được
    # kiểm, và test này thành một vòng lặp rỗng nói "PASS".
    assert so_lan_kiem >= 1, (
        "không payload nào làm cửa bơm — phép kiểm permissionDecision "
        "không chạy lần nào. Dấu vết phiên còn sót?")
    print(f"PASS  {len(payloads)} payload, {so_lan_kiem} lần thật sự kiểm "
          f"quyết định: mã thoát 0, không có deny")


def test_CUA_song_khi_stdin_HONG():
    kq = subprocess.run(
        [sys.executable, str(GOC / "tools" / "cua_ho_so.py")],
        input="{{{ khong phai json", capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=str(GOC.parent))
    assert kq.returncode == 0, "stdin hỏng mà cửa không nhường đường"
    assert not kq.stdout.strip()
    print("PASS  stdin hỏng -> im, thoát 0")


def test_CUA_im_voi_subagent():
    van, nhan, _ = cua_ho_so.quyet_dinh({
        "session_id": "t-sub", "agent_id": "abc", "agent_type": "Explore",
        "tool_input": {"file_path": str(GOC / CA_THAT)}})
    assert van is None and nhan == "IM-subagent"
    print("PASS  subagent -> im")


def test_QUYET_DINH_la_ham_THUAN_khong_ghi_dau_vet():
    """Đánh dấu "đã bơm" phải xảy ra SAU khi in xong, không phải trong
    lúc quyết định.

    Phép thử 15/09/2026 rơi đúng vào đây: `print` nổ `UnicodeEncodeError`
    nhưng dấu vết đã ghi, nên lượt sau im — suất bơm bị đốt lặng lẽ.
    """
    phien = "t-thuan"
    dau_vet = cua_ho_so._dau_vet(phien)
    if dau_vet.exists():
        dau_vet.unlink()
    van, nhan, _ = cua_ho_so.quyet_dinh(
        {"session_id": phien, "tool_input": {"file_path": str(GOC / CA_THAT)}})
    assert van and nhan == "BOM"
    assert not dau_vet.exists(), (
        "quyet_dinh() đã ghi dấu vết — nó phải THUẦN, việc ghi thuộc về "
        "main() sau khi in thành công")
    print("PASS  quyet_dinh() thuần, không đốt suất bơm khi in hỏng")


def test_CUA_khu_trung_trong_cung_mot_phien():
    phien = "t-khu-trung"
    dau_vet = cua_ho_so._dau_vet(phien)
    if dau_vet.exists():
        dau_vet.unlink()
    p = {"session_id": phien, "tool_input": {"file_path": str(GOC / CA_THAT)}}
    ma1, ra1 = _goi_cua(p)
    ma2, ra2 = _goi_cua(p)
    assert ma1 == 0 and ra1.strip(), "lần đầu phải bơm"
    assert ma2 == 0 and not ra2.strip(), "lần hai cùng phiên vẫn bơm"
    print("PASS  bơm một lần mỗi file mỗi phiên")


def test_DANH_SACH_LOC_duoc_SUY_RA_chu_khong_GO_TAY():
    """`ten_dang_bom()` phải tính từ repo. Một danh sách gõ tay sẽ trôi
    khỏi repo ngay lần thêm file tiếp theo — `SKILL.md` Bước 2:
    *"Suy ra, đừng gõ."*
    """
    src = (GOC / "tools" / "ho_so.py").read_text(encoding="utf-8")
    cay = ast.parse(src)
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "ten_dang_bom")
    # `*.py` là MẪU GLOB, không phải một cái tên — loại nó ra, nếu không
    # gác này báo nhầm ngay chính lời giải đúng. Lượt chạy đầu tiên đỏ ở
    # đúng chỗ đó.
    hang_chuoi = [n.value for n in ast.walk(ham)
                  if isinstance(n, ast.Constant) and isinstance(n.value, str)
                  and n.value.endswith(".py")
                  and not any(k in n.value for k in "*?[")]
    assert not hang_chuoi, f"có tên file gõ thẳng trong hàm: {hang_chuoi}"
    ten = ho_so.ten_dang_bom()
    assert CA_THAT in ten, f"{CA_THAT} phải nằm trong danh sách lọc"
    assert 5 <= len(ten) <= 45, (
        f"danh sách lọc {len(ten)} file — 15/09/2026 đo được 23/52. "
        f"Ngoài dải này thì ngưỡng hoặc phép tra đã trôi.")
    print(f"PASS  danh sách lọc suy ra được: {len(ten)} file")


if __name__ == "__main__":
    import tempfile
    for ten_ham, ham in sorted(globals().items()):
        if ten_ham.startswith("test_") and callable(ham):
            if "tmp_path" in ham.__code__.co_varnames[:ham.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as t:
                    ham(Path(t))
            else:
                ham()
    print("\nTAT CA XANH")
