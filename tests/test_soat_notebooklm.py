"""Mỗi phép đo có tiêu chí ký trước phải KHAI đã soát chéo hay chưa.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 10/09/2026 người dùng chốt: dùng NotebookLM thường xuyên như một luồng
thông tin **độc lập**. Chỉ dẫn ấy nằm trong `SKILL.md`, trong
`~/.claude/rules/`, và trong bộ nhớ phiên.

Ngày 12/09/2026 người dùng phải nhắc **lần thứ hai** rằng nó không được
dùng. Cùng ngày, **một câu hỏi duy nhất** gửi công cụ ấy lôi ra rằng ĐO 5
là bản TRÙNG của `docs/STATE.md` BƯỚC 25 (04/09/2026) — 88,8 phút máy để
dựng lại một kết quả đã nằm trong sổ tám ngày.

**Một chỉ dẫn thường trực không có cơ chế thì nó chỉ là một lời nhắc.**
File này là cơ chế: nó không ép phải soát, nó ép phải **khai** đã soát hay
chưa — cùng đúng cách `# bia-ok:` không cấm mà buộc nói ra lý do.

Gác này KHÔNG thay được việc soát. Nó chỉ làm việc bỏ sót **không im lặng
được nữa**.
"""
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SO = GOC / "docs" / "soat-notebooklm.json"
TIEU_CHI = GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md"

sys.path.insert(0, str(GOC))


def _so() -> dict:
    return json.loads(SO.read_text(encoding="utf-8"))


def ten_phep_do(van: str) -> list[str]:
    """Mọi mục `## ĐO <n>` trong bản khai tiêu chí, giữ nguyên thứ tự.

    Đọc bằng biểu thức neo vào ĐẦU DÒNG và cấp tiêu đề, không bằng `in`:
    chữ "ĐO 5" xuất hiện hàng chục lần trong văn xuôi của chính file ấy.
    """
    thay, da_co = [], set()
    for d in van.splitlines():
        m = re.match(r"^##\s+(ĐO\s+\d+[a-z]?)\s*—", d)
        if m:
            ten = re.sub(r"\s+", " ", m.group(1))
            if ten not in da_co:
                da_co.add(ten)
                thay.append(ten)
    return thay


def test_MOI_PHEP_DO_da_ky_deu_co_mot_dong_trong_so():
    """Thêm một ĐO mà quên khai soát → đỏ. Đó là toàn bộ việc của gác này."""
    co = _so()["soat"]
    thieu = [t for t in ten_phep_do(TIEU_CHI.read_text(encoding="utf-8"))
             if t not in co]
    assert not thieu, (
        f"Cac phep do sau chua khai da soat cheo hay chua: {thieu}\n"
        f"Them mot dong vao {SO.name} — hoac `phat_hien`, hoac "
        f"`khong_soat_vi` kem ly do that.")
    print(f"PASS  {len(co)} phep do deu co dong khai")


def test_MOI_DONG_phai_khai_MOT_trong_HAI_the_khong_duoc_ca_hai():
    """`phat_hien` XOR `khong_soat_vi`. Có cả hai là nói nước đôi."""
    for ten, d in _so()["soat"].items():
        co_pd = "phat_hien" in d
        co_ks = "khong_soat_vi" in d
        assert co_pd or co_ks, f"{ten}: khong khai gi ca"
        assert not (co_pd and co_ks), (
            f"{ten}: khai CA HAI `phat_hien` lan `khong_soat_vi`")
    print("PASS  moi dong khai dung mot the")


def test_LY_DO_KHONG_SOAT_khong_duoc_rong_va_khong_duoc_chung_chung():
    """`khong_soat_vi: ""` hay `"khong can"` bị từ chối — cùng cơ chế `# bia-ok:`.

    Một ô thoát không đòi lý do thật thì nó là một ô thoát tự do, và gác
    này thành trang trí (lỗi 31).
    """
    MO_HO = ("khong can", "không cần", "khong quan trong", "n/a", "-", "sau")
    for ten, d in _so()["soat"].items():
        ly_do = d.get("khong_soat_vi")
        if ly_do is None:
            continue
        assert len(ly_do.strip()) >= 25, (
            f"{ten}: ly do khong soat qua ngan ({len(ly_do.strip())} ky tu) — "
            f"{ly_do!r}")
        assert ly_do.strip().lower() not in MO_HO, f"{ten}: ly do chung chung"
    print("PASS  moi ly do khong-soat deu cu the")


def test_MOI_PHAT_HIEN_phai_kem_LENH_tu_kiem_va_mot_PHAN_QUYET():
    """Giới hạn của công cụ: nó chỉ ra CHỖ đáng nhìn, nó không phán được.

    `SKILL.md`: *"Mọi phát hiện của nó phải tự kiểm lại, bằng `grep` hoặc
    bằng cách đọc mã."* Nên mỗi phát hiện phải mang theo một LỆNH đã chạy và
    một phán quyết THẬT/SAI — không được để trống một bên.
    """
    HOP_LE = {"THẬT", "SAI"}
    for ten, d in _so()["soat"].items():
        for i, pd in enumerate(d.get("phat_hien", [])):
            dau = f"{ten}[{i}]"
            assert pd.get("noi_dung", "").strip(), f"{dau}: thieu noi_dung"
            tk = pd.get("tu_kiem", "").strip()
            assert tk, f"{dau}: thieu `tu_kiem` — phat hien chua duoc kiem lai"
            assert len(tk) >= 15, f"{dau}: `tu_kiem` qua ngan: {tk!r}"
            pq = pd.get("phan_quyet", "").strip()
            assert pq, f"{dau}: thieu `phan_quyet`"
            assert any(pq.upper().startswith(k) for k in HOP_LE), (
                f"{dau}: `phan_quyet` phai mo dau bang THAT hoac SAI, "
                f"nhan {pq[:40]!r}")
    print("PASS  moi phat hien deu co lenh tu kiem va phan quyet")


def test_SO_nay_phai_ghi_GIOI_HAN_cua_cong_cu():
    """Công cụ chỉ thấy TÀI LIỆU. Quên điều đó là mượn thẩm quyền nó không có.

    Loại lỗi nặng nhất của dự án — tài liệu lệch MÃ — nó không bắt được cái
    nào. Sổ này phải tự mang câu ấy, vì người đọc sổ có thể không đọc skill.
    """
    van = SO.read_text(encoding="utf-8")
    assert "_gioi_han_cua_cong_cu" in van, "so thieu muc gioi han"
    gh = _so()["_gioi_han_cua_cong_cu"]
    assert "TÀI LIỆU" in gh and "MÃ" in gh, (
        "muc gioi han phai noi ro no chi thay TAI LIEU, khong thay MA")
    print("PASS  so tu mang gioi han cua cong cu")


def test_DOC_TEN_PHEP_DO_bang_TIEU_DE_chu_khong_bang_chu_xuat_hien():
    """Chữ "ĐO 5" nằm đầy trong văn xuôi; chỉ tiêu đề `## ĐO 5 —` mới tính.

    Đây là lỗi 30/35/36 của dự án — đọc sự XUẤT HIỆN của một chữ thay vì
    VAI TRÒ của nó. Khoá nó bằng một mẫu dựng tay, không bằng file thật.
    """
    mau = (
        "# Tieu chi\n"
        "Doan van xuoi nhac ĐO 5 va ĐO 6 nhieu lan, ĐO 5 nua.\n"
        "## ĐO 7 — mot phep do that\n"
        "Trong than muc nay lai nhac ĐO 7 va ĐO 8.\n"
        "### ĐO 9 — tieu de CAP BA, khong phai muc\n"
        "## ĐO 10 — mot phep do nua\n"
    )
    assert ten_phep_do(mau) == ["ĐO 7", "ĐO 10"], ten_phep_do(mau)
    print("PASS  chi tieu de cap hai moi tinh, van xuoi thi khong")
