"""Bất đối xứng local/CI có **ba** vế, không phải hai — và phép phán phải ĐỎ được.

VÌ SAO CÓ FILE NÀY (17/09/2026, lỗi 79)
──────────────────────────────────────
`CLAUDE.md` có một bảng tên *"Bất đối xứng local / CI — VĨNH VIỄN, và là
chủ ý"*, kết bằng một câu khai ĐỦ:

    "Bat doi xung CHI nam o BCTC va han muc; lich su gia thi khong."

Thiếu một vế, và vế thiếu là vế đổi **thường xuyên nhất**: số hiệu bản thư
viện. `requirements.txt` khai bằng **SÀN**, nên CI luôn lấy bản mới nhất
còn máy local cài một lần rồi đứng yên.

Đo bằng cách đọc thẳng nhật ký CI: lượt `2026-09-16T01:26:10Z` đã chạy
`vnai-2.6.0` **sáu tiếng rưỡi trước** khi PR #130 nâng vnai ở máy local.
Và `vnstock` 4.0.8 phát hành 15/09, nên mọi cổng xanh từ hôm ấy đều xanh
trên 4.0.8 — trong khi `docs/STATE.md` BƯỚC 87 viết *"mọi con số hiện hành
đã đo trên 4.0.7"*.

Câu ấy đúng về các lượt **ĐO**, sai về các lượt **CỔNG**.

HAI PHÉP KIỂM, HAI LOẠI
───────────────────────
1. **Tài liệu** phải nêu vế thứ ba, và phải nêu LỆNH đọc trạng thái. Một
   bảng khai ĐỦ mà thiếu một vế thì tệ hơn một bảng không khai gì.
2. **Phép phán** `so_ban_goi.so_sanh()` phải đạt tới được **cả ba** ô.
   Nó không chạy được trên CI (cần `gh`), nên phần phán tách khỏi phần
   đọc mạng — đúng lối `cua_bash_an_toan.kiem()`.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import so_ban_goi as sb  # noqa: E402

CLAUDE = GOC / "CLAUDE.md"
REQ = GOC / "requirements.txt"


# ══ 1. Tài liệu phải nêu VẾ THỨ BA ═════════════════════════════════════
def _khoi_bat_doi_xung() -> str:
    van = CLAUDE.read_text(encoding="utf-8")
    dau = van.find("Bất đối xứng local / CI")
    assert dau != -1, "khong tim thay muc bat doi xung trong CLAUDE.md"
    cuoi = van.find("\n## ", dau)
    return van[dau:cuoi if cuoi != -1 else len(van)]


def test_MUC_BAT_DOI_XUNG_phai_neu_VE_BAN_THU_VIEN():
    """Vế thiếu là vế đổi thường xuyên nhất, nên nó phải có tên trong bảng."""
    khoi = _khoi_bat_doi_xung().lower()
    for phai_co in ("bản thư viện", "requirements.txt", "sàn"):
        assert phai_co in khoi, (
            f"muc bat doi xung khong neu {phai_co!r} — bang van dang khai "
            f"DU trong khi no thieu mot ve")
    print("PASS  muc bat doi xung neu ca ve ban thu vien")


def test_CAU_CHI_NAM_O_BCTC_VA_HAN_MUC_phai_mang_DAU():
    """Quy ước giữ-số-cũ ở `docs/HANDOFF.md` mục 4, áp cho một PHẠM VI."""
    khoi = _khoi_bat_doi_xung()
    i = khoi.find("CHỈ nằm ở BCTC")
    assert i != -1, "cau cu bien mat — neu co y go thi sua ca phep kiem nay"
    quanh = khoi[i:i + 700]
    assert "⚠️" in quanh, (
        "cau 'CHI nam o BCTC va han muc' con de TRAN — no khai DU trong "
        "khi thieu ve ban thu vien")


def test_MUC_BAT_DOI_XUNG_phai_neu_LENH_doc_trang_thai():
    """*Đọc trạng thái, đừng suy ra nó* — lỗi 25, và luật ấy cần một lệnh."""
    khoi = _khoi_bat_doi_xung()
    assert "tools/so_ban_goi.py" in khoi, (
        "khong neu lenh nao de doc trang thai — nguoi doc lai phai suy")
    assert (GOC / "tools" / "so_ban_goi.py").exists()


def test_REQUIREMENTS_van_khai_bang_SAN_chu_khong_phai_GHIM():
    """Nếu một ngày nó thành `==` thì cả mục bất đối xứng phải viết lại.

    Không đòi nó PHẢI là sàn — đó là quyết định. Đòi nó **khớp với thứ
    tài liệu đang mô tả**: cùng họ `N_DAY_DU` 596/451.
    """
    van = REQ.read_text(encoding="utf-8")
    dong = [d.strip() for d in van.splitlines()
            if d.strip().startswith(("vnstock", "vnai"))
            and not d.strip().startswith("#")]
    assert dong, "khong tim thay dong vnstock/vnai trong requirements.txt"
    for d in dong:
        assert ">=" in d, (
            f"`{d}` khong con la SAN — muc bat doi xung o CLAUDE.md dang "
            f"mo ta mot co che khong con dung")


# ══ 2. Phép phán phải đạt tới CẢ BA ô ══════════════════════════════════
LOC = {g: "1.0.0" for g in sb.CONG_KHAI}


def test_BA_O_cua_phep_phan_deu_DAT_TOI_DUOC():
    """Ô thứ ba bắt buộc: im lặng ở đó bị đọc thành *"hai nơi giống nhau"*."""
    ma, lech = sb.so_sanh(LOC, dict.fromkeys(
        (sb._chuan(g) for g in sb.CONG_KHAI), "1.0.0"))
    assert ma == sb.KHOP and not lech

    ci = dict.fromkeys((sb._chuan(g) for g in sb.CONG_KHAI), "1.0.0")
    ci[sb._chuan("vnstock")] = "9.9.9"
    ma, lech = sb.so_sanh(LOC, ci)
    assert ma == sb.LECH
    assert lech == [("vnstock", "1.0.0", "9.9.9")], lech

    for rong in (None, {}):
        ma, lech = sb.so_sanh(LOC, rong)
        assert ma == sb.CHUA_KIEM, f"{rong!r} phai ra CHUA KIEM DUOC"
        assert not lech
    print("PASS  ba o deu dat toi duoc")


def test_GOI_KHONG_THAY_trong_nhat_ky_thi_KHONG_duoc_phan_la_LECH():
    """*Không thấy* khác *thấy và khác*. Gộp hai cái là chế ra báo động giả.

    Nhật ký CI chỉ in các gói lượt ấy THẬT SỰ cài; một gói đã có sẵn trong
    ảnh máy chạy sẽ không xuất hiện.
    """
    ma, lech = sb.so_sanh(LOC, {sb._chuan("vnstock"): "1.0.0"})
    assert ma == sb.KHOP, f"{ma} — goi vang mat bi doc thanh lech"
    assert not lech


def test_DAU_GACH_NGANG_trong_ten_goi_duoc_quy_ve_MOT_dang():
    """`tradingview-ta` trong `pip freeze`, `tradingview_ta` trong nhật ký."""
    assert sb._chuan("tradingview-ta") == sb._chuan("tradingview_ta")
    ma, _ = sb.so_sanh({"tradingview-ta": "3.3.0"},
                       {"tradingview_ta": "3.3.0"})
    assert ma == sb.KHOP


def test_MAU_DOC_NHAT_KY_bat_dung_dong_pip_that():
    """Dựng lại nguyên văn một dòng `Successfully installed` của CI."""
    dong = ("kiem-dinh\tCài thư viện\t2026-09-16T01:27:00Z Successfully "
            "installed numpy-2.2.6 pandas-2.3.3 streamlit-1.64.0 "
            "vnai-2.6.0 vnstock-4.0.8 vnstock_ezchart-1.0.2 zipp-4.1.0")
    thay = dict(sb.RE_GOI.findall(dong))
    for ten, ban in (("vnstock", "4.0.8"), ("vnai", "2.6.0"),
                     ("streamlit", "1.64.0"), ("pandas", "2.3.3")):
        assert thay.get(ten) == ban, f"{ten}: doc ra {thay.get(ten)!r}"
    print("PASS  mau doc dung dong `Successfully installed` that cua CI")
