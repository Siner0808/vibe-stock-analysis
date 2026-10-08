"""Bảng chấm bóng công khai trên app — BƯỚC 148 (P3b-2).
(Tên HIỂN THỊ từ BƯỚC 157: "Kiểm định chiến lược"; "chấm bóng" là tên nội bộ.)

Ba điều bảng phải giữ:
  1. MỌI ứng viên đều hiện, kể cả rớt sàng — ngưỡng 0,05/K chia cho TỔNG,
     giấu ứng viên rớt là giấu mẫu số;
  2. không có kết quả thì ghi `CHUA CHAM`, không suy ra trạng thái nào;
  3. app CHỈ ĐỌC sổ đăng ký — không gọi phép so nào trên dữ liệu thật
     (BƯỚC 144: tính trước khi khai là tiêu mất phần "chưa nhìn").
"""
import ast
import copy
import hashlib
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
    b = cb.bang_cong_khai(SO, ket={"B": (KET_QUA, cb.MOC_DOC, 55),
                                   "C": (dict(KET_QUA, p=0.02), cb.MOC_DOC, 55),
                                   "A": (KET_QUA, cb.MOC_DOC, 55)})
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
    b = cb.bang_cong_khai(so, ket={"D": (KET_QUA, cb.MOC_DOC, 55)})
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
    b2 = cb.bang_cong_khai(so, ket={"E": (KET_QUA, cb.MOC_DOC, 55),
                                    "D": (KET_QUA, cb.MOC_DOC, 55)})
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
    assert {"doc_so_ung_vien", "tom_tat_so", "bang_cong_khai", "bang_hien_thi"} <= goi, goi
    cam = goi & {"so_cap", "ma_tran_cap", "doc_quyet_dinh", "diem_ung_vien"}
    assert not cam, f"app tinh tren du lieu that: {cam}"
    print(f"PASS  app goi cham_bong: {sorted(goi)}")


# ── tên HIỂN THỊ — BƯỚC 157 ──────────────────────────────────────────────

def _app_chuoi() -> list[str]:
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    return [n.value for n in ast.walk(cay)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def test_TEN_NOI_BO_giu_nguyen_chi_TANG_HIEN_THI_doi():
    """Khoá nội bộ không đổi (gác git và test lịch sử đọc chúng); chỉ `bang_hien_thi`
    đổi chữ — và không đổi `bang_cong_khai`."""
    assert cb.COT_BANG == ("Ứng viên", "Khai ngày", "Mô tả", "Trọng số", "Lý do",
                           "Sàng", "Trạng thái")
    b = cb.bang_cong_khai(SO)
    truoc = b.copy()
    cb.bang_hien_thi(b)
    assert b.equals(truoc), "bang_hien_thi khong duoc doi bang vao"
    assert list(b.columns) == list(cb.COT_BANG)


def test_BANG_HIEN_THI_dung_bang_ten_da_chot_va_giu_so_hang_thu_tu():
    b = cb.bang_hien_thi(cb.bang_cong_khai(SO))
    assert list(b.columns) == ["Phương án", "Ngày đăng ký", "Mô tả", "Trọng số",
                               "Lý do", "Vòng sàng (cũ)", "Trạng thái"]
    assert list(b["Phương án"]) == ["C", "A", "B"]          # thứ tự khai, như bảng gốc
    assert list(b["Trạng thái"]) == ["Chưa đủ dữ liệu", "Rớt sàng (quy trình cũ)",
                                     "Chưa đủ dữ liệu"]
    assert list(b["Vòng sàng (cũ)"]) == ["qua sàng", "rớt sàng", "qua sàng"]


def test_TRANG_THAI_HIEN_ghim_literal_tung_cap():
    """Bảng người dùng chốt 02/10/2026. Ghim literal: đột biến một chữ phải đỏ."""
    assert cb.TRANG_THAI_HIEN == {
        "CHUA CHAM": "Chưa đủ dữ liệu",
        "CHUA DU DU LIEU": "Chưa đủ dữ liệu",
        "CHUA TOI MOC": "Chưa tới mốc đọc",
        "DANG CHAM": "Đang theo dõi",
        "QUA": "Đạt — đủ điều kiện nâng cấp",
        "THUA": "Kém hơn bản đang chạy",
        "ROT SANG": "Rớt sàng (quy trình cũ)",
        "CHUA SANG": "Chưa sàng (quy trình cũ)",
    }
    assert cb.SANG_HIEN == {"chua": "chưa sàng", "qua": "qua sàng", "rot": "rớt sàng",
                            "bo": "đã bỏ"}
    assert cb.TEN_COT_HIEN == {"Ứng viên": "Phương án", "Khai ngày": "Ngày đăng ký",
                               "Sàng": "Vòng sàng (cũ)"}


def test_MOI_trang_thai_ma_mat_may_co_the_sinh_ra_deu_co_ten_hien_thi():
    """Không trạng thái nội bộ nào lọt ra giao diện: thử MỌI nhánh sinh trạng thái."""
    so = copy.deepcopy(SO)
    so["ung_vien"]["D"] = _uv("2026-09-17", None)           # CHUA SANG (dòng cũ)
    so["ung_vien"]["E"] = _uv("2026-10-02", None)           # dòng một vòng
    thay = {"QUA": (dict(KET_QUA), cb.MOC_DOC, 55),
            "THUA": (dict(KET_QUA, delta=-0.08), cb.MOC_DOC, 55),
            "DANG CHAM": (dict(KET_QUA, p=0.9), cb.MOC_DOC, 55),
            "CHUA DU DU LIEU": (KET_QUA, cb.MOC_DOC, cb.MIN_MA - 1),
            "CHUA TOI MOC": (None, cb.MOC_DOC - 1, 55)}
    thay_ra = set()
    for ten, ket in thay.items():
        b = cb.bang_cong_khai(so, ket={"E": ket})
        thay_ra.add(dict(zip(b["Ứng viên"], b["Trạng thái"]))["E"])
        cb.bang_hien_thi(b)                                  # không được nổ
    assert thay_ra == set(thay), thay_ra
    b = cb.bang_cong_khai(so)
    assert set(b["Trạng thái"]) >= {"CHUA SANG", "ROT SANG", "CHUA CHAM"}
    h = cb.bang_hien_thi(b)
    for v in h["Trạng thái"]:
        assert v == v.capitalize() or v[0].isupper(), v
        assert not v.isupper() and v not in cb.TRANG_THAI_HIEN, v   # không phải mã nội bộ


def test_TRANG_THAI_la_chu_tieng_Viet_co_dau_khong_phai_ma_chu_hoa():
    for ma, hien in cb.TRANG_THAI_HIEN.items():
        assert any(ord(c) > 127 for c in hien), (ma, hien)
        assert hien != ma and not hien.isupper(), (ma, hien)


def test_GIA_TRI_la_thi_NO_khong_lot_chuoi_noi_bo_ra_giao_dien():
    b = cb.bang_cong_khai(SO)
    xau = b.copy()
    xau.loc[0, "Trạng thái"] = "TRANG THAI LA"
    with pytest.raises(ValueError, match="Trạng thái"):
        cb.bang_hien_thi(xau)
    xau = b.copy()
    xau.loc[0, "Sàng"] = "lạ"
    with pytest.raises(ValueError, match="Sàng"):
        cb.bang_hien_thi(xau)


def test_APP_ten_tab_tieu_de_va_nhan_dung_ten_moi_va_KHONG_con_cham_bong():
    chuoi = _app_chuoi()
    assert "🔬 Kiểm định chiến lược" in chuoi
    assert "##### 🔬 Kiểm định chiến lược trên phiên mới (forward test)" in chuoi
    for nhan in ("Số phương án đã đăng ký (K)", "Đăng ký trong tháng"):
        assert nhan in chuoi, nhan
    cu = [s for s in chuoi if "chấm bóng" in s.lower() or "cham bong" in s.lower()]
    assert not cu, f"ten noi bo lot ra giao dien: {cu}"
    for s in ("Đã khai (K)", "Khai trong tháng", "🧪 Chấm bóng", "Sổ ứng viên"):
        assert s not in chuoi, s


def test_APP_cau_giai_thich_khong_dung_thuat_ngu_noi_bo():
    cau = [s for s in _app_chuoi() if s.startswith("Mỗi phương án là một cách chấm điểm")]
    assert len(cau) == 1, cau
    c = cau[0]
    for cam in ("chấm bóng", "ứng viên", "K ", "π", "Bonferroni", "IC "):
        assert cam not in c, (cam, c)
    assert "SAU ngày đăng ký" in c and "hiếm" in c


def test_APP_goi_bang_hien_thi_bao_ngoai_bang_cong_khai():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    dung = [n for n in ast.walk(cay) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr == "bang_hien_thi"]
    assert len(dung) == 1
    arg = dung[0].args[0]
    assert (isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "bang_cong_khai"), "bang hien phai di qua bang_hien_thi"


# ── dịch mã nội bộ trong văn bản tự do `ly_do` — BƯỚC 157 ────────────────

def test_LY_DO_chua_ma_noi_bo_thi_HIEN_nhan_tieng_Viet():
    so = {"ung_vien": {"X": dict(_uv("2026-10-02", None), ly_do="Kỳ vọng hợp lý là DANG CHAM, "
                                                                  "không phải QUA (BƯỚC 155, BƯỚC 156).")}}
    b = cb.bang_hien_thi(cb.bang_cong_khai(so))
    assert b.loc[0, "Lý do"] == ("Kỳ vọng hợp lý là Đang theo dõi, không phải "
                                 "Đạt — đủ điều kiện nâng cấp (BƯỚC 155, BƯỚC 156).")
    # bảng gốc KHÔNG đổi: mã nội bộ vẫn còn ở `bang_cong_khai`
    assert "DANG CHAM" in cb.bang_cong_khai(so).loc[0, "Lý do"]


@pytest.mark.parametrize("ma", sorted(cb.TRANG_THAI_HIEN))
def test_MOI_ma_noi_bo_dung_rieng_deu_duoc_dich_dung_nhan(ma):
    assert cb.dich_ma_noi_bo(f"a {ma} b") == f"a {cb.TRANG_THAI_HIEN[ma]} b"
    assert cb.dich_ma_noi_bo(ma) == cb.TRANG_THAI_HIEN[ma]
    assert cb.dich_ma_noi_bo(f"({ma}).") == f"({cb.TRANG_THAI_HIEN[ma]})."


@pytest.mark.parametrize("van_ban", [
    "QUANG", "QUA_X", "xQUA", "THUAN", "ROT SANGX", "CHUAN", "qua", "Qua", "dang cham",
    "Dang Cham", "QUA1", "1QUA", "ĐQUA", "DANG CHAMS", "CHUA", "ROT",
])
def test_CHU_KHAC_khong_bi_dung_toi(van_ban):
    """Chỉ TỪ NGUYÊN VẸN, chữ hoa đúng: `QUANG`, `QUA_X`, `qua`… giữ nguyên."""
    assert cb.dich_ma_noi_bo(van_ban) == van_ban


def test_DICH_mot_luot_nhan_thay_vao_khong_bi_dich_lai():
    assert cb.dich_ma_noi_bo("CHUA DU DU LIEU") == "Chưa đủ dữ liệu"
    assert cb.dich_ma_noi_bo("QUA THUA") == "Đạt — đủ điều kiện nâng cấp Kém hơn bản đang chạy"
    xong = cb.dich_ma_noi_bo("DANG CHAM")
    assert cb.dich_ma_noi_bo(xong) == xong


def test_DICH_khong_chuoi_thi_tra_nguyen():
    assert cb.dich_ma_noi_bo(None) is None
    assert cb.dich_ma_noi_bo(3) == 3


def test_SO_THAT_UV_001_hien_Dang_theo_doi_va_FILE_SO_khong_doi_mot_byte():
    duong = GOC / "docs" / "ung-vien.json"
    truoc = hashlib.sha256(duong.read_bytes()).hexdigest()
    so = cb.doc_so_ung_vien()
    b = cb.bang_hien_thi(cb.bang_cong_khai(so))
    ly_do = b.set_index("Phương án").loc["UV-001", "Lý do"]
    assert "Đang theo dõi" in ly_do and "DANG CHAM" not in ly_do
    assert "BƯỚC 155, BƯỚC 156" in ly_do                     # chỉ dẫn tài liệu, giữ nguyên
    assert so["ung_vien"]["UV-001"]["ly_do"].count("DANG CHAM") == 1   # sổ trong bộ nhớ không đổi
    assert hashlib.sha256(duong.read_bytes()).hexdigest() == truoc
