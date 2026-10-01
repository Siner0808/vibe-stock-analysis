"""Bảng chấm bóng công khai trên app — BƯỚC 148 (P3b-2).

Ba điều bảng phải giữ:
  1. MỌI ứng viên đều hiện, kể cả rớt sàng — ngưỡng 0,05/K chia cho TỔNG,
     giấu ứng viên rớt là giấu mẫu số;
  2. không có kết quả thì ghi `CHUA CHAM`, không suy ra trạng thái nào;
  3. app CHỈ ĐỌC sổ đăng ký — không gọi phép so nào trên dữ liệu thật
     (BƯỚC 144: tính trước khi khai là tiêu mất phần "chưa nhìn").
"""
import ast
import copy
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pytest

import cham_bong as cb


def _uv(ngay, qua, ts=None):
    return {"khai_ngay": ngay, "mo_ta": f"thu {ngay}", "ly_do": "test",
            "qua_sang": qua,
            "spec": {"loai": "trong_so",
                     "trong_so": ts or {"trend_score": 0.25, "volume_score": 0.75}}}


SO = {"ung_vien": {
    "B": _uv("2026-10-06", True),
    "A": _uv("2026-10-05", False),
    "C": _uv("2026-09-28", True, {"risk_score": 1.0}),
}}
KET_QUA = {"delta": 0.08, "null": [], "z": 3.5, "p": 0.0002}


def test_SO_RONG_bang_rong_dung_cot_va_nguong_la_ALPHA():
    so = {"ung_vien": {}}
    b = cb.bang_cong_khai(so)
    assert b.empty and list(b.columns) == list(cb.COT_BANG)
    t = cb.tom_tat_so(so, "2026-10-07")
    assert (t["K"], t["nguong"], t["qua_sang"], t["tuan_nay"]) == (0, cb.ALPHA, 0, 0)
    print("PASS  so rong: bang rong, K=0, nguong=ALPHA")


def test_MOI_ung_vien_deu_hien_KE_CA_rot_sang_theo_thu_tu_khai():
    b = cb.bang_cong_khai(SO)
    assert list(b["Ứng viên"]) == ["C", "A", "B"], "phai xep theo ngay khai"
    tt = dict(zip(b["Ứng viên"], b["Trạng thái"]))
    assert tt == {"C": "CHUA CHAM", "A": "ROT SANG", "B": "CHUA CHAM"}, tt
    assert dict(zip(b["Ứng viên"], b["Trọng số"]))["B"] == "volume 0.75 · trend 0.25"
    print("PASS  ca ung vien rot sang van hien; khong ket qua -> CHUA CHAM")


def test_CO_ket_qua_thi_trang_thai_qua_trang_thai_voi_NGUONG_chia_TONG():
    b = cb.bang_cong_khai(SO, ket={"B": (KET_QUA, 60, 55),
                                   "C": (dict(KET_QUA, p=0.02), 60, 55),
                                   "A": (KET_QUA, 60, 55)})
    tt = dict(zip(b["Ứng viên"], b["Trạng thái"]))
    # p = 0,02 nằm GIỮA 0,05/3 và 0,05/2: chia TỔNG (3) thì chưa qua; chia số
    # qua sàng (2) thì qua. p = 0,03 ở bản đầu không phân biệt được hai phép chia.
    assert tt == {"B": "QUA", "C": "DANG CHAM", "A": "ROT SANG"}, tt
    print("PASS  co ket qua -> trang_thai, nguong 0,05/K voi K = tong")


def test_TOM_TAT_dem_K_la_TONG_va_tuan_ISO_cua_hom_nay():
    t = cb.tom_tat_so(SO, "2026-10-07")          # tuần ISO 2026-W41: A, B
    assert (t["K"], t["qua_sang"], t["tuan_nay"]) == (3, 2, 2), t
    assert t["nguong"] == pytest.approx(cb.ALPHA / 3)
    assert t["tran_tuan"] == cb.TRAN_SANG_MOI_TUAN
    print(f"PASS  tom tat: {t}")


def test_SO_SAI_KHUON_thi_NO_khong_hien_nua_voi():
    hong = copy.deepcopy(SO)
    hong["ung_vien"]["A"]["spec"]["trong_so"] = {"news_score": 1.0}
    for ham in (cb.bang_cong_khai, lambda s: cb.tom_tat_so(s, "2026-10-07")):
        with pytest.raises(ValueError):
            ham(hong)
    print("PASS  so sai khuon -> ValueError, khong hien bang")


def _goi_cham_bong_trong_app() -> set:
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    ten = {a.asname or a.name for n in ast.walk(cay) if isinstance(n, ast.Import)
           for a in n.names if a.name == "cham_bong"}
    return {n.func.attr for n in ast.walk(cay)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name) and n.func.value.id in ten}


def test_APP_chi_DOC_so_dang_ky_khong_so_tren_du_lieu_that():
    goi = _goi_cham_bong_trong_app()
    assert {"doc_so_ung_vien", "tom_tat_so", "bang_cong_khai"} <= goi, goi
    cam = goi & {"so_cap", "ma_tran_cap", "doc_quyet_dinh", "diem_ung_vien"}
    assert not cam, f"app tinh tren du lieu that: {cam}"
    print(f"PASS  app goi cham_bong: {sorted(goi)}")
