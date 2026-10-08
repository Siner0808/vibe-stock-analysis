"""Gác "MỖI BƯỚC PHỤC VỤ MỘT MỐC" — BƯỚC 164 (giai đoạn A1 của `docs/LO-TRINH.md`).

Người dùng duyệt khung lộ trình ngày 08/10/2026 (*"duyệt"*) và bảo bắt đầu giai
đoạn A (*"Làm ngay"*). Từ BƯỚC 164, mục BƯỚC của `docs/STATE.md` phải có một dòng
`**Mốc:** <mã>` với mã CÓ THẬT trong `docs/LO-TRINH.md`, hoặc `**Mốc:**
quy-trinh — <lý do>`. Máy đọc bằng TIÊU ĐỀ cấp hai, như các gác sổ khác.

Phát đục đầu tiên dựng lại đúng ca thật: lấy NGUYÊN mục BƯỚC 164 của sổ và bỏ
dòng Mốc khỏi nó — gác phải ĐỎ. Quần thể bị đòi phải KHÁC RỖNG, nếu không mọi ca
xanh trên hai tập rỗng (lỗi 66).
"""
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import moc_lo_trinh as m  # noqa: E402

LO_TRINH = (GOC / "docs" / "LO-TRINH.md")
HOP_LE = {"A1", "A2", "B1", "H1"}


def _lo_trinh() -> str:
    return LO_TRINH.read_text(encoding="utf-8")


def _state() -> str:
    return m.doc_van_state(GOC)


# ── quần thể THẬT ────────────────────────────────────────────────────────────

def test_MOC_BAT_DAU_la_quyet_dinh_164_khong_bi_nang_len():
    """164 là BƯỚC đầu tiên người dùng bắt đầu giai đoạn A. Nâng nó là bỏ gác
    cho các BƯỚC bị đẩy ra ngoài; hạ nó là đòi khai bù cho lịch sử."""
    assert m.TU_BUOC == 164


def test_QUAN_THE_khong_rong_va_co_BUOC_164():
    muc = m.tach_muc_buoc(_state())
    assert 164 in muc, (
        "mục `## BƯỚC 164 —` không thấy trong docs/STATE.md — gác đang canh một "
        "quần thể rỗng, hoặc TEP_STATE trỏ nhầm tệp (giai đoạn A4 tách STATE?)")
    assert len(muc[164]) > 20, "mục BƯỚC 164 gần như rỗng — đọc hụt?"


def test_MOI_BUOC_tu_164_trong_STATE_that_deu_co_dong_Moc_hop_le():
    loi = m.vi_pham(_state(), _lo_trinh())
    assert not loi, "BƯỚC thiếu/sai dòng Mốc:\n  " + "\n  ".join(loi)


def test_PHAT_DAU_bo_dong_Moc_khoi_BUOC_164_that_thi_DO():
    """Dựng lại NGUYÊN VĂN lỗi: BƯỚC 164 viết xong mà quên dòng Mốc."""
    van = _state()
    goc = m.vi_pham(van, _lo_trinh())
    assert goc == [], goc
    bo = "\n".join(d for d in van.split("\n") if not d.startswith("**Mốc:**"))
    loi = m.vi_pham(bo, _lo_trinh())
    assert any(l.startswith("BƯỚC 164:") and "thieu" in l for l in loi), loi


def test_MA_MOC_that_co_du_cac_ma_cua_lo_trinh():
    ma = m.ma_hop_le(_lo_trinh())
    can = ({f"A{i}" for i in range(1, 6)} | {f"B{i}" for i in range(1, 5)}
           | {f"C{i}" for i in range(1, 5)} | {f"D{i}" for i in range(1, 5)}
           | {f"E{i}" for i in range(1, 4)} | {"H1", "H2"}
           | {f"T{i}" for i in range(1, 8)})
    assert can <= ma, f"LO-TRINH.md thieu ma: {sorted(can - ma)}"
    assert "C5" not in ma, (
        "`C5` da la ten cong/dieu kien dung C5 cua du an — dat lam ma moc la "
        "tu tao nham lan (BUOC 164 co y bo qua C5)")


def test_LO_TRINH_chep_dung_bon_cau_tra_loi_cua_nguoi_dung():
    van = _lo_trinh()
    for cau in ("*\"duyệt\"*", "*\"Đồng ý\"*",
                "*\"Để tới giai đoạn B (Recommended)\"*", "*\"Làm ngay\"*"):
        assert cau in van, f"LO-TRINH.md thieu cau tra loi nguyen van {cau}"
    assert "08/10/2026" in van


def test_LO_TRINH_goi_dung_ten_uoc_luong_cua_ngay_phan_quyet():
    """Ngày phán quyết là ƯỚC LƯỢNG (lịch nghỉ 2027 chưa công bố) và phải nói cách
    tính lại bằng `lich_giao_dich`. Không được ghim nó như một ngày chắc chắn."""
    van = _lo_trinh()
    i = van.index("### Đích 2")
    dau = van[i:i + 400]
    assert "ƯỚC LƯỢNG" in dau
    assert "lich_giao_dich" in van and "NGAY_NGHI" in van


def test_CON_SO_65_va_274_trong_LO_TRINH_khop_lenh_tai_lap_NGAY_BI_KHOA():
    """Quy tắc 2: văn bản nói lệnh in `65 274`; chạy chính nó và so. Lịch 2026
    đã công bố (không trôi), còn `MOC_DOC`/`NHIP` đổi thì tài liệu phải đổi theo."""
    import cham_bong as cb
    import lich_giao_dich as lich
    van = _lo_trinh()
    ra = (len(lich.cac_phien("2026-10-01", "2026-12-31")),
          cb.MOC_DOC + cb.NHIP + 1)
    assert ra == (65, 274), ra
    assert "In **65 274**" in van, "LO-TRINH.md khong con khop ket qua lenh"
    assert f"{ra[1]} − {ra[0]} = **209" in van


# ── phép phán `loi_moc` ──────────────────────────────────────────────────────

def _loi(*dong, hop_le=HOP_LE):
    return m.loi_moc(list(dong), hop_le)


@pytest.mark.parametrize("dong", [
    "**Mốc:** A1",
    "**Mốc:** A1, B1",
    "**Mốc:** A1 · H1",
    "**Mốc:** A1 + A2",
    "**Mốc:** A1 — doi luat Quy tac 3 theo quyet dinh nguoi dung",
    "**Mốc:** quy-trinh — soat dinh ky luot 12, khong phuc vu moc san pham",
    "**Mốc:** Quy-Trinh — soat dinh ky luot 12, khong phuc vu moc san pham",
])
def test_dong_Moc_HOP_LE(dong):
    assert _loi("# tieu de", dong, "than bai") == [], dong


@pytest.mark.parametrize("dong, tu_khoa", [
    ("**Mốc:** ", "rong"),
    ("**Mốc:** Z9", "KHONG co trong"),               # mã không định nghĩa
    ("**Mốc:** A1, Z9", "KHONG co trong"),           # một mã lạ trong hai
    ("**Mốc:** hoan thien", "khong phai ma"),
    ("**Mốc:** A", "khong phai ma"),
    ("**Mốc:** quy-trinh", "thieu ly do"),
    ("**Mốc:** quy-trinh — ", "thieu ly do"),
    ("**Mốc:** quy-trinh — viec quy trinh", "thieu ly do"),   # chung chung
    ("**Mốc:** quy-trinh — ngan qua", "thieu ly do"),         # dưới 25 ký tự
])
def test_dong_Moc_SAI_phai_DO(dong, tu_khoa):
    loi = _loi(dong)
    assert len(loi) == 1 and tu_khoa in loi[0], loi


@pytest.mark.parametrize("tieu_de", [
    "## BƯỚC 170 - gach noi thuong, khong phai em dash",
    "## BƯỚC 170: hai cham",
    "## BƯỚC  170  nhieu dau cach",
    "## BƯỚC 170"])
def test_tieu_de_BUOC_khong_co_em_dash_van_la_mot_muc_thieu_Moc(tieu_de):
    """Đột biến M14 (lô B): đòi `—` sau số làm một tiêu đề viết khác dấu thoát khỏi luật."""
    van = f"{tieu_de}\nnoi dung khong co dong moc\n"
    loi = m.vi_pham(van, "- **A1** — x\n")
    assert len(loi) == 1 and loi[0].startswith("BƯỚC 170: thieu"), loi


def test_so_BUOC_dai_hon_khong_bi_cat_thanh_so_ngan():
    """`BƯỚC 1700` là BƯỚC 1700, không phải BƯỚC 170 theo sau chữ số 0."""
    assert set(m.tach_muc_buoc("## BƯỚC 1700 — x\n", 164)) == {1700}
    assert m.tach_muc_buoc("## BƯỚC 16 — x\n", 164) == {}


def test_ly_do_quy_trinh_dung_BIEN_25_ky_tu():
    """24 ký tự đỏ, 25 xanh (`<` chứ không `<=`). Cũng khoá lý do gỡ danh sách "lý do
    mơ hồ" riêng (phát đục lô B của BƯỚC 164): nó là mã chết — mọi phần tử đều < 25 ký
    tự nên phép kiểm độ dài đã bắt hết."""
    assert _loi("**Mốc:** quy-trinh — " + "x" * 24) != []
    assert _loi("**Mốc:** quy-trinh — " + "x" * 25) == []
    assert not hasattr(m, "LY_DO_MO_HO"), "danh sach chet duoc them lai"


def test_THIEU_va_THUA_dong_Moc():
    assert "thieu" in _loi("khong co gi")[0]
    assert "2 dong" in _loi("**Mốc:** A1", "**Mốc:** B1")[0]


def test_quy_trinh_khong_di_kem_ma_san_pham_duoc_hieu_la_ma_la():
    """`quy-trinh, A1` không phải 'việc quy trình có mã': phần trước ` — ` là một
    mã, và `quy-trinh` không phải mã. Phải ĐỎ, không lặng lẽ nhận."""
    assert _loi("**Mốc:** quy-trinh, A1 — mot ly do du dai de qua duoc") != []


# ── máy đọc tiêu đề ──────────────────────────────────────────────────────────

MAU = (
    "# So\n"
    "Van xuoi nhac BƯỚC 170 va **Mốc:** A1 nhieu lan.\n"
    "## BƯỚC 163 — truoc moc, KHONG duoc doi\n"
    "khong co moc o day\n"
    "## BƯỚC 164 — dung moc\n"
    "**Mốc:** A1\n"
    "### BƯỚC 165 — tieu de CAP BA, khong phai muc\n"
    "## BƯỚC 166 — sau moc, thieu Mốc\n"
    "van xuoi: moc **Mốc:** A1 giua dong\n"
    "```\n"
    "**Mốc:** A1\n"
    "```\n"
    "## ĐO 30 — mot ĐO cat muc BƯỚC 166\n"
    "**Mốc:** B1\n"
)


def test_tach_muc_chi_lay_TIEU_DE_cap_hai_tu_moc_tro_di():
    muc = m.tach_muc_buoc(MAU, 164)
    assert sorted(muc) == [164, 166], sorted(muc)
    assert m.tach_muc_buoc(MAU, 1).keys() >= {163, 164, 166}


def test_Moc_trong_van_xuoi_va_khoi_rao_va_muc_khac_KHONG_tinh_cho_BUOC():
    loi = m.vi_pham(MAU, "- **A1** — a\n- **B1** — b\n", 164)
    assert loi == ["BƯỚC 166: thieu dong `**Mốc:** <ma>` (hoac `**Mốc:** "
                   "quy-trinh — <ly do>`)"], loi


def test_MA_chi_dinh_nghia_bang_muc_danh_sach_dau_dong():
    van = "Van xuoi nhac **A1** va `B2`.\n- **C3** — dinh nghia that\n  - **D4** — long nhau\n"
    assert m.ma_hop_le(van) == {"C3"}
