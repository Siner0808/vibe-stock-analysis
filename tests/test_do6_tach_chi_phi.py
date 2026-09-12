"""Bảng bốn kết cục của ĐO 6 KHÔNG phủ kín — và mã phải nói ra chỗ hở.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 12/09/2026 tôi ký một bảng bốn kết cục cho ĐO 6, rồi viết một dụng cụ
đọc nó bằng chuỗi `if / elif / else`. Rà lưới 101×101 sau khi đã công bố
kết quả:

    1.250 / 10.201 diem KHONG ung voi mo ta nao trong bang da ky
    — vung "mot ve nam trong [25%, 50%), ve kia duoi 25%" —
    va ca 1.250 diem bi nhanh `else` don IM LANG vao ket cuc 4.

Kết luận đã công bố **không** bị ảnh hưởng: điểm thật (74,6% · 45,6%) rơi
vào ô 3 và khớp đúng mô tả ô 3. Nhưng cái bảng thì hở, và mã thì tự bịa một
nghĩa cho chỗ bảng không nói.

**Không được đổi ngưỡng** — tiêu chí cấm thẳng điều đó sau khi thấy số.
Đường đúng là thêm một trạng thái `NGOAI_BANG`, cùng lý do
`kiem_cu_phap_311.py` phải có mã thoát 2 *"chưa kiểm được"*: **"không biết"
là một câu trả lời, và nó không được giả dạng một câu trả lời khác.**
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import do6_tach_chi_phi as d6  # noqa: E402

L, N = d6.NGUONG_GIAI_THICH, d6.NGUONG_NHO


def _luoi(buoc: int = 101):
    b = [i / (buoc - 1) for i in range(buoc)]
    return [(x, y) for x in b for y in b]


def test_NAM_TRANG_THAI_deu_DAT_TOI_DUOC():
    """Bốn ô đã ký CỘNG trạng thái thứ năm. Thiếu một cái là có chỗ chết."""
    bang = [
        ((0.05, 0.90), d6.THANH_KHOAN),   # tác động lớn, bước giá nhỏ
        ((0.90, 0.05), d6.GIA_VAO),       # bước giá lớn, tác động nhỏ
        ((0.75, 0.46), d6.CHUA_TACH),     # ĐÚNG số thật của ĐO 6
        ((0.05, 0.05), d6.CHO_KHAC),      # cả hai nhỏ
        ((0.30, 0.10), d6.NGOAI_BANG),    # chỗ HỞ của bảng
    ]
    for (b, t), mong_doi in bang:
        ma, ly_do = d6.quyet_dinh(b, t)
        assert ma == mong_doi, f"({b}, {t}) -> {ma}, doi {mong_doi}"
        assert ly_do.strip(), "moi trang thai phai noi ra LY DO"
    assert len({m for _, m in bang}) == 5, "phai co dung nam trang thai"
    print("PASS  nam trang thai deu dat toi duoc")


def test_MOI_O_phai_KHOP_mo_ta_da_ky_tren_TOAN_LUOI():
    """Không ô nào được nhận một điểm mà mô tả của nó không phủ.

    Đây là phép kiểm mà bản đầu KHÔNG có, và là lý do 1.250 điểm bị dồn im
    lặng. Mô tả viết lại thẳng ở đây từ bản khai, không đọc lại từ mã — đọc
    lại từ mã thì đột biến làm mù cả hai vế.
    """
    def khop(o, b, t):
        return {
            d6.THANH_KHOAN: t >= L and b < N,
            d6.GIA_VAO: b >= L and t < N,
            d6.CHUA_TACH: b >= N and t >= N,
            d6.CHO_KHAC: b < N and t < N,
        }.get(o)

    lech = []
    for b, t in _luoi():
        o = d6.quyet_dinh(b, t)[0]
        if o == d6.NGOAI_BANG:
            continue
        if not khop(o, b, t):
            lech.append((round(b, 2), round(t, 2), o))
    assert not lech, (
        f"{len(lech)} diem duoc xep vao mot o ma MO TA cua o do khong phu. "
        f"Vi du: {lech[:5]}")
    print("PASS  moi o chi nhan diem mo ta cua no phu")


def test_VUNG_HO_dung_la_vung_da_khai_va_KHONG_bi_don_vao_o_nao():
    """Chỗ hở phải đúng bằng vùng đã ghi, không rộng hơn, không hẹp hơn."""
    ho = [(b, t) for b, t in _luoi()
          if d6.quyet_dinh(b, t)[0] == d6.NGOAI_BANG]
    assert ho, "khong con vung ho -> nguong da bi doi, dieu tieu chi CAM"

    for b, t in ho:
        mot_ve_giua = (N <= b < L) or (N <= t < L)
        ve_kia_nho = (b < N) or (t < N)
        assert mot_ve_giua and ve_kia_nho, (
            f"({b:.2f}, {t:.2f}) nam ngoai vung ho da khai")

    # dung con so da ghi trong docstring cua dung cu
    assert len(ho) == 1250, f"vung ho co {len(ho)} diem, da ghi 1.250"
    print(f"PASS  vung ho dung {len(ho)}/{len(_luoi())} diem, dung vi tri")


def test_BON_NGUONG_khop_BAN_KHAI_trong_TIEU_CHI():
    """Cùng họ `N_DAY_DU` 596/451: mã và tài liệu nói hai con số khác nhau."""
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    dau = van.index("## ĐO 6 — khoảng cách chi phí thực thi IS/OOS")
    khoi = van[dau:dau + 6000]
    # van-ban-ok: ban khai la MARKDOWN — AST khong doc duoc mot bang van xuoi
    assert ">= 50%" in khoi and "< 25%" in khoi, "ban khai thieu hai nguong"
    assert "0,24" in khoi, "ban khai thieu khoang cach phai giai thich"
    assert d6.NGUONG_GIAI_THICH == 0.50, d6.NGUONG_GIAI_THICH
    assert d6.NGUONG_NHO == 0.25, d6.NGUONG_NHO
    assert d6.KHOANG_CACH == 0.24, d6.KHOANG_CACH
    print(f"PASS  nguong khop ban khai: {L:.0%} / {N:.0%} · "
          f"khoang cach {d6.KHOANG_CACH}")


def test_BIEN_doc_theo_dung_dau_da_ky():
    """`>= 50%` chứ không `> 50%`; `< 25%` chứ không `<= 25%`."""
    assert d6.quyet_dinh(0.10, 0.50)[0] == d6.THANH_KHOAN
    assert d6.quyet_dinh(0.10, 0.4999)[0] == d6.NGOAI_BANG
    assert d6.quyet_dinh(0.60, 0.25)[0] == d6.CHUA_TACH
    assert d6.quyet_dinh(0.60, 0.2499)[0] == d6.GIA_VAO
    assert d6.quyet_dinh(0.2499, 0.2499)[0] == d6.CHO_KHAC
    assert d6.quyet_dinh(0.25, 0.25)[0] == d6.CHUA_TACH
    print("PASS  bien >=50% va <25% doc dung dau da ky")


def test_SO_THAT_cua_DO_6_van_ra_ket_cuc_3():
    """Neo con số đã công bố. Đổi luật mà quên nó là đổi một kết luận."""
    ma, _ = d6.quyet_dinh(0.746, 0.456)
    assert ma == d6.CHUA_TACH, (
        f"so that cua DO 6 nay doc ra {ma}, trong khi BUOC 56 cong bo "
        f"'ket cuc 3 — chua tach duoc'")
    print("PASS  so that (74,6% · 45,6%) van ra KET CUC 3")
