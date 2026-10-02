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
    "B": _uv("2026-09-16", True),
    "A": _uv("2026-09-15", False),
    "C": _uv("2026-09-07", True, {"risk_score": 1.0}),
}}
KET_QUA = {"delta": 0.08, "null": [], "z": 3.5, "p": 0.0002}


def test_SO_RONG_bang_rong_dung_cot_va_nguong_la_ALPHA():
    so = {"ung_vien": {}}
    b = cb.bang_cong_khai(so)
    assert b.empty and list(b.columns) == list(cb.COT_BANG)
    t = cb.tom_tat_so(so, "2026-09-17")
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
    t = cb.tom_tat_so(SO, "2026-09-17")          # tuần ISO 2026-W38: A, B
    assert (t["K"], t["qua_sang"], t["tuan_nay"]) == (3, 2, 2), t
    assert t["nguong"] == pytest.approx(cb.ALPHA / 3)
    assert t["tran_tuan"] == cb.TRAN_SANG_MOI_TUAN
    print(f"PASS  tom tat: {t}")


def test_CHUA_SANG_hien_rieng_va_KHONG_dem_vao_qua_sang():
    """BƯỚC 153: `qua_sang: null` = khai rồi, vòng sàng chưa chạy. Không phải
    rớt sàng, không phải chờ chấm — và có `ket` cũng không được chấm nó."""
    so = copy.deepcopy(SO)
    so["ung_vien"]["D"] = _uv("2026-09-17", None)
    b = cb.bang_cong_khai(so, ket={"D": (KET_QUA, 60, 55)})
    dong = b.set_index("Ứng viên")
    assert (dong.loc["D", "Sàng"], dong.loc["D", "Trạng thái"]) == ("chua", "CHUA SANG")
    assert dict(zip(b["Ứng viên"], b["Sàng"])) == {"C": "qua", "A": "rot", "B": "qua",
                                                    "D": "chua"}
    t = cb.tom_tat_so(so, "2026-09-17")
    assert (t["K"], t["qua_sang"], t["tuan_nay"]) == (4, 2, 3), t
    assert t["nguong"] == pytest.approx(cb.ALPHA / 4)
    print(f"PASS  chua sang: {dict(dong.loc['D'])}; tom tat {t}")


def test_SAU_MOC_dong_khai_hien_bo_vao_thang_xac_nhan_khong_bao_gio_CHUA_SANG():
    """BƯỚC 155: từ `MOC_MOT_VONG` không còn vòng sàng — `qua_sang: null` hiện
    `bo` / `CHUA CHAM`, và có `ket` thì đi thẳng vào trạng thái xác nhận."""
    so = copy.deepcopy(SO)
    so["ung_vien"]["E"] = _uv("2026-10-02", None)
    so["ung_vien"]["D"] = _uv("2026-09-17", None)          # dòng CŨ chưa sàng
    b = cb.bang_cong_khai(so)
    dong = b.set_index("Ứng viên")
    assert (dong.loc["E", "Sàng"], dong.loc["E", "Trạng thái"]) == ("bo", "CHUA CHAM")
    assert (dong.loc["D", "Sàng"], dong.loc["D", "Trạng thái"]) == ("chua", "CHUA SANG")
    assert "CHUA SANG" not in (dong.loc["E", "Trạng thái"],)
    b2 = cb.bang_cong_khai(so, ket={"E": (KET_QUA, 60, 55), "D": (KET_QUA, 60, 55)})
    d2 = b2.set_index("Ứng viên")
    assert d2.loc["E", "Trạng thái"] == "QUA"               # 0,0002 < 0,05/5
    assert d2.loc["D", "Trạng thái"] == "CHUA SANG"         # dòng cũ vẫn không được chấm
    assert d2.loc["E", "Sàng"] == cb.SANG_BO == "bo"
    print("PASS  sau moc: bo / CHUA CHAM / vao thang xac nhan")


def test_TOM_TAT_dem_thang_nay_tu_dong_SAU_moc_va_tuan_nay_tu_dong_TRUOC_moc():
    so = copy.deepcopy(SO)
    so["ung_vien"]["E"] = _uv("2026-10-02", None)
    t = cb.tom_tat_so(so, "2026-10-20")
    assert (t["thang_nay"], t["tran_thang"]) == (1, 1)
    assert t["tuan_nay"] == 0                                # dòng mới không vào đếm tuần
    assert cb.tom_tat_so(so, "2026-10-02")["tuan_nay"] == 0  # kể cả cùng tuần ISO với E
    t = cb.tom_tat_so(so, "2026-11-03")
    assert t["thang_nay"] == 0
    assert cb.tom_tat_so(so, "2027-10-20")["thang_nay"] == 0   # cùng tháng, khác NĂM
    t = cb.tom_tat_so(so, "2026-09-17")
    assert (t["tuan_nay"], t["thang_nay"]) == (2, 0)         # E khai SAU hom_nay: tháng 9 trống
    assert t["K"] == 4 and t["nguong"] == pytest.approx(cb.ALPHA / 4)


def test_SO_SAI_KHUON_thi_NO_khong_hien_nua_voi():
    hong = copy.deepcopy(SO)
    hong["ung_vien"]["A"]["spec"]["trong_so"] = {"news_score": 1.0}
    for ham in (cb.bang_cong_khai, lambda s: cb.tom_tat_so(s, "2026-09-17")):
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
