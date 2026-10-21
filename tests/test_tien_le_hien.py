"""Gác khối "Tiền lệ" trên app (ý 5 phần 2, BƯỚC 216; `docs/thiet-ke-y5-tien-le.md` mục 6).

Chữ dựng ở `tien_le.dong_hien` (thuần); app chỉ in. Ba luật của mục 6 canh ở đây:
nhóm dưới 10 KHÔNG có tỷ lệ; tỷ lệ nền LUÔN đi cạnh; KTC chứa nền → "không phân biệt
được với nền".
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import tien_le as tl  # noqa: E402
from tien_le import MO_PHONG, THAT, TienLe  # noqa: E402


def _t(ra: str, lnr: float, diem: float = 65, vni: float = 1.0, nguon: str = MO_PHONG,
       ma: str = "FPT") -> TienLe:
    return TienLe(nguon, ma, "2022-01-03", ra, diem, vni, lnr, "STOP_LOSS")


def _kho(n_nhom: int, thang_nhom: int, n_khac: int = 10, thang_khac: int = 5) -> list[TienLe]:
    return ([_t(f"2022-03-{i + 1:02d}", 1.0 if i < thang_nhom else -1.0) for i in range(n_nhom)]
            + [_t(f"2022-05-{i + 1:02d}", 1.0 if i < thang_khac else -1.0, diem=75)
               for i in range(n_khac)])


def test_CHUA_DU_tien_le_thi_KHONG_co_ty_le_nhom_nhung_VAN_co_nen():
    d = tl.dong_hien(tl.tom_tat(_kho(9, 5), 65, 1.0, "2026-01-05"))
    assert d[0] == f"Tiền lệ lúc vào lệnh — điểm {tl.dai_diem(65)} · VN-Index cao hơn MA50 0–2%"
    assert d[1].startswith("Chưa đủ tiền lệ (n = 9; cần ≥ 10)") and "%" not in d[1].replace("—", "")
    assert d[2].startswith("Nền (mọi tiền lệ có trước ngày vào, n = 19): thắng")
    assert not any(x.startswith("→") for x in d)


def test_DU_va_KTC_chua_nen_thi_KHONG_PHAN_BIET():
    d = tl.dong_hien(tl.tom_tat(_kho(10, 5), 65, 1.0, "2026-01-05"))
    assert d[1] == "10 tiền lệ (10 mô phỏng, 0 thật): 5 thắng · 5 thua · 0 hoà — thắng 50% [KTC 95%: 24% ; 76%]"
    assert d[2] == "Nền (mọi tiền lệ có trước ngày vào, n = 20): thắng 50% [KTC 95%: 30% ; 70%]"
    assert d[3] == "→ Không phân biệt được với nền."


def test_DU_va_KTC_KHONG_chua_nen_thi_van_nhac_khong_phai_tin_hieu():
    d = tl.dong_hien(tl.tom_tat(_kho(12, 12, n_khac=40, thang_khac=0), 65, 1.0, "2026-01-05"))
    assert d[3].startswith("→ Khác nền ở lát cắt này") and "không như tín hiệu" in d[3]


def test_KHONG_XEP_DUOC_thi_noi_ro_va_van_co_nen():
    d = tl.dong_hien(tl.tom_tat(_kho(10, 5), 61, 1.0, "2026-01-05"))
    assert d[0].startswith("Không xếp được nhóm") and d[1].startswith("Nền (")


def test_NEN_RONG_va_CA_GAN_NHAT_ghi_nguon():
    assert tl.dong_hien(tl.tom_tat([], 65, 1.0, "2026-01-05"))[-1] == \
        "Nền: chưa có tiền lệ nào đóng trước ngày vào."
    kho = [_t("2022-03-01", 2.5, ma="AAA"), _t("2022-03-02", -1.25, nguon=THAT, ma="BBB")]
    d = tl.dong_hien(tl.tom_tat(kho, 65, 1.0, "2026-01-05"))
    assert d[-2:] == ["BBB · 2022-01-03 → 2022-03-02 · -1.25% · thật",
                      "AAA · 2022-01-03 → 2022-03-01 · +2.50% · mô phỏng"]


def test_TEP_KHO_ma_app_doc_co_that():
    assert (GOC / tl.DUONG_KHO).is_file()


# ─────────────────────────── app: chỉ in, không tính ───────────────────────────

def _app():
    return ast.parse((GOC / "app.py").read_text(encoding="utf-8"))


def _ham(cay, ten):
    return next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten)


def _goi(nut) -> set[str]:
    return {(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
            for n in ast.walk(nut) if isinstance(n, ast.Call)}


def test_APP_khoi_tien_le_tinh_bang_tien_le_va_chi_in():
    goi = _goi(_ham(_app(), "_khoi_tien_le"))
    assert {"tom_tat", "dong_hien", "tu_dong_nhat_ky", "vni_cua_dong", "_doc_kho_tien_le"} <= goi
    assert not goi & {"wilson", "khoa_nhom", "chon_tien_le", "ket_qua_lenh"}, \
        "app tự tính — mọi phép tính phải ở tien_le"


def test_APP_goi_khoi_tien_le_trong_chi_tiet_nhat_ky():
    cay = _app()
    ngoai = [n for n in cay.body if not isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    assert any("_khoi_tien_le" in _goi(n) for n in ngoai), "khối tiền lệ không được gọi"
    kho = _ham(cay, "_doc_kho_tien_le")
    assert any(isinstance(n, ast.Attribute) and n.attr == "DUONG_KHO" for n in ast.walk(kho))
