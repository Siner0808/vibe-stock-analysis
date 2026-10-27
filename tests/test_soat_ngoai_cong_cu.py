"""Gác của `tools/soat_ngoai_cong_cu.py` — ba phép quét ngoài tầm công cụ soát chính (BƯỚC 232, lỗi 191).

Phép kiểm đáng tin nhất là CA THẬT đã biết trước: lượt soát 14 (BƯỚC 230) ghi số của ba
phép quét bằng script ở scratchpad; công cụ trong repo phải tái lập ĐÚNG những con số ấy
trên đúng các cây đã ghi (`61221db`, `efa6a58`). CI lấy đủ lịch sử (`fetch-depth: 0`).
"""
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
import soat_loi_khai_cu as s  # noqa: E402
import soat_ngoai_cong_cu as n  # noqa: E402


# ── hàm thuần ────────────────────────────────────────────────────────────

def test_DONG_THEM_doc_hunk_co_va_khong_co_do_dai_va_bo_hunk_chi_xoa():
    diff = ("@@ -10,0 +11,3 @@\n+a\n+b\n+c\n"
            "@@ -5 +6 @@\n-x\n+y\n"
            "@@ -20,2 +22,0 @@\n-p\n-q\n")
    assert n.dong_them(diff) == {6, 11, 12, 13}


def test_UNG_VIEN_tinh_dong_va_cau_nhieu_dong_CHUA_DAU_bo_dong_co_dau():
    dong = ["Công cụ `tools/x.py` chưa có test.",           # 1: dòng
            "| 9 | `a.py` không nhập `b` | x |",               # 2: hàng bảng (được tính)
            "⚠️ HẾT ĐÚNG: `c.py` chưa có gác.",               # 3: có dấu
            "Câu này nói `d.py` ở dòng trên và",               # 4..5: câu nhiều dòng,
            "chưa ai mở nó.",                                  #   cụm phủ định ở dòng 5
            "Văn xuôi chưa có tên nào."]                       # 6: không tên
    ung = n.ung_vien(dong)
    assert set(ung) == {1, 2, 3, 5}
    assert set(n.chua_dau(ung)) == {1, 2, 5}
    assert set(n.ung_vien(dong, chon={1, 5})) == {1, 5}


def test_QUET_STATE_lay_DUNG_khoang_BUOC_bao_gom_hai_dau():
    dong = ["## BƯỚC 1 — a", "`x.py` chưa có test.",
            "## BƯỚC 2 — b", "`y.py` chưa có test.",
            "Nhắc `## BƯỚC 9` giữa dòng: `u.py` chưa có test.",   # không phải tiêu đề
            "## BƯỚC 3 — c", "`z.py` chưa có test.", "⚠️ `w.py` chưa có test.",
            "## BƯỚC 4 — d", "`v.py` chưa có test."]
    n_ung, ra = n.quet_state(dong, 2, 3)
    assert n_ung == 4
    assert {i: b for i, (b, _) in ra.items()} == {4: 2, 5: 2, 7: 3}


def test_HANG_BANG_chi_dem_hang_bang_khop_bo_loc():
    dong = ["| 1 | `a.py` chưa có gác | x |", "| 2 | 🔴 `b.py` chưa có gác | x |",
            "| 3 | không tên, chưa có gác | x |", "`c.py` chưa có gác, không phải hàng bảng."]
    assert n.hang_bang(dong) == (2, 1)


def test_TAM_cong_cu_chinh_la_TAI_LIEU_tru_hang_bang():
    assert n.cong_cu_chinh_thay("CLAUDE.md", "`a.py` chưa có gác.")
    assert not n.cong_cu_chinh_thay("CLAUDE.md", "| 1 | `a.py` chưa có gác |")
    assert not n.cong_cu_chinh_thay("docs/STATE.md", "`a.py` chưa có gác.")
    assert "docs/STATE.md" not in s.TAI_LIEU


# ── ca thật: số của lượt soát 14 (docs/STATE.md BƯỚC 230) ──────────────

def test_CA_THAT_STATE_209_229_o_61221db_la_49_ung_vien_44_chua_dau_dung_tung_BUOC():
    n_ung, ra = n.quet_state(n.doc_dong("docs/STATE.md", "61221db"), 209, 229)
    dem: dict[int, int] = {}
    for b, _ in ra.values():
        dem[b] = dem.get(b, 0) + 1
    assert (n_ung, len(ra)) == (49, 44)
    assert dem == {209: 2, 210: 2, 211: 4, 212: 1, 213: 7, 214: 3, 215: 3, 216: 2, 217: 3,
                   218: 4, 219: 1, 220: 2, 222: 3, 224: 2, 225: 1, 227: 1, 228: 1, 229: 2}


def test_CA_THAT_STATE_186_208_o_efa6a58_la_64_53_lot_14_dung_lai():
    """Lượt 13 ghi 63 · 52 bằng script đã mất; lượt 14 dựng lại ra 64 · 53 (lỗi 191)."""
    n_ung, ra = n.quet_state(n.doc_dong("docs/STATE.md", "efa6a58"), 186, 208)
    assert (n_ung, len(ra)) == (64, 53)


def test_CA_THAT_HANG_BANG_o_61221db_la_67_hang_46_chua_dau():
    ra = {t: n.hang_bang(n.doc_dong(t, "61221db")) for t in s.TAI_LIEU}
    assert sum(a for a, _ in ra.values()) == 67
    assert sum(b for _, b in ra.values()) == 46
    assert ra[".claude/skills/quy-trinh-lam-viec/references/loi-da-mac.md"] == (59, 38)


def test_CA_THAT_DIFF_efa6a58_61221db_khop_tung_tep_cua_luot_14():
    ra = n.quet_diff("efa6a58", "61221db")
    gon = {t: (v["them"], v["ung_vien"], len(v["chua_dau"]), len(v["ngoai"])) for t, v in ra.items()}
    assert gon["docs/STATE.md"] == (674, 49, 44, 44)
    assert gon["docs/TIEU-CHI-DOC-TRUOC.md"] == (483, 6, 5, 5)
    assert gon[".claude/skills/quy-trinh-lam-viec/references/loi-da-mac.md"] == (11, 3, 2, 2)
    assert gon["CLAUDE.md"] == (10, 2, 2, 0)
    assert gon["docs/thiet-ke-y5-tien-le.md"] == (127, 2, 2, 2)
    assert sum(v[3] for v in gon.values()) == 53


# ── dòng lệnh ────────────────────────────────────────────────────────────

def test_CLI_cay_khong_ton_tai_la_MA_2_khong_phai_sach(capsys):
    assert n.main(["state", "1", "2", "--cay", "khong-co-commit-nay"]) == 2
    assert "CHƯA KIỂM ĐƯỢC" in capsys.readouterr().err


def test_CLI_state_in_so_ung_vien_va_chua_dau(capsys):
    assert n.main(["state", "209", "229", "--cay", "61221db"]) == 0
    assert "49 câu ứng viên, 44 chưa dấu" in capsys.readouterr().out


def test_CONG_CU_CHINH_tro_sang_cong_cu_nay(capsys):
    """Lượt soát chạy `soat_loi_khai_cu` trước tiên — con trỏ phải nằm trong bản in ấy."""
    assert s.main([]) == 0
    assert "tools/soat_ngoai_cong_cu.py" in capsys.readouterr().out
