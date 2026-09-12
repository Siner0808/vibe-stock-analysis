"""`tools/do_roi_nhip.py` phải đọc được bảng đã ký — CẢ HAI Ô BÁC BỎ.

VÌ SAO CÓ FILE NÀY
──────────────────
Lỗi 31 của dự án: *một tiêu chí không thể đỏ là trang trí*. Bảng khai ngày
05/09/2026 có hai ô **BÁC BỎ**, và chính khai báo ấy nói ra vì sao:

    "Hai ô BÁC BỎ mới là thứ làm khai báo này có giá trị. Chỉ có ô 'ủng hộ'
     và ô 'tương hợp' thì đây là một lời tiên tri không thể sai."

Nên phép kiểm quan trọng nhất ở đây KHÔNG phải "ô tương hợp ra đúng" — mà
là **hai ô bác bỏ có đạt tới được**. Một `quyet_dinh()` trả TUONG_HOP cho
mọi đầu vào sẽ qua được mọi phép so trên số thật của tuần này.

Và một phép kiểm thứ hai, cùng họ `N_DAY_DU` 596/451: **ba ngưỡng trong mã
phải khớp ba ngưỡng trong bản khai**. Sửa ngưỡng sau khi thấy số là điều
khai báo cấm thẳng.
"""
import ast
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import do_roi_nhip as drn  # noqa: E402

UTC = timezone.utc


def _moc(chuoi: str) -> datetime:
    return datetime.fromisoformat(chuoi).replace(tzinfo=UTC)


# ══ Bảng đã ký — NĂM ô, và hai ô đỏ phải đạt tới được ═══════════════════
def test_NAM_O_cua_bang_da_ky_deu_DAT_TOI_DUOC():
    """Mỗi ô một đầu vào. Thiếu một ô nào là bảng ấy có chỗ không dùng tới."""
    bang = [
        ((30.0, 6.0), drn.UNG_HO),        # trễ giảm VÀ nhịp hồi
        ((30.0, 2.0), drn.BAC_BO),        # trễ giảm mà nhịp KHÔNG hồi
        ((300.0, 6.0), drn.BAC_BO),       # nhịp hồi mà trễ KHÔNG giảm
        ((300.0, 2.0), drn.TUONG_HOP),    # cả hai đứng yên
        ((300.0, 4.0), drn.CHUA_KET_LUAN),
    ]
    for (a, b), mong_doi in bang:
        ma, ly_do = drn.quyet_dinh(a, b)
        assert ma == mong_doi, f"A={a} B={b} -> {ma}, doi {mong_doi}"
        assert ly_do, "moi o phai noi ra LY DO"
    da_bat = {drn.quyet_dinh(a, b)[0] for (a, b), _ in bang}
    assert da_bat == {drn.UNG_HO, drn.BAC_BO, drn.TUONG_HOP, drn.CHUA_KET_LUAN}
    print("PASS  nam o cua bang deu dat toi duoc, gom CA HAI o BAC BO")


def test_HAI_O_BAC_BO_khong_duoc_tra_cung_LY_DO():
    """Hai ô cùng mã nhưng khác cơ chế — trộn lời thì mất nửa thông tin."""
    _, ly_do_1 = drn.quyet_dinh(30.0, 2.0)
    _, ly_do_2 = drn.quyet_dinh(300.0, 6.0)
    assert ly_do_1 != ly_do_2, "hai o bac bo dang noi cung mot cau"
    print(f"PASS  hai o bac bo phan biet duoc: {ly_do_1!r} vs {ly_do_2!r}")


def test_BIEN_cua_nguong_doc_theo_dung_dau_da_ky():
    """`A <= 120` chứ không phải `A < 120`; `B >= 5` chứ không phải `B > 5`."""
    assert drn.quyet_dinh(120.0, 6.0)[0] == drn.UNG_HO
    assert drn.quyet_dinh(120.01, 6.0)[0] == drn.BAC_BO
    assert drn.quyet_dinh(30.0, 5.0)[0] == drn.UNG_HO
    assert drn.quyet_dinh(30.0, 3.0)[0] == drn.BAC_BO
    assert drn.quyet_dinh(30.0, 4.0)[0] == drn.CHUA_KET_LUAN
    print("PASS  bien <=120 va >=5 doc dung dau da ky")


def test_THIEU_DU_LIEU_khong_duoc_thanh_mot_phan_quyet():
    """Không đo được là trạng thái thứ ba, không phải 'tương hợp'."""
    assert drn.quyet_dinh(None, 2.0)[0] == drn.CHUA_KET_LUAN
    assert drn.quyet_dinh(300.0, None)[0] == drn.CHUA_KET_LUAN
    print("PASS  thieu du lieu -> CHUA KET LUAN, khong tu nhan mot o")


# ══ Ba ngưỡng trong mã phải khớp bản khai ══════════════════════════════
def test_BA_NGUONG_trong_ma_khop_BAN_KHAI_trong_STATE():
    """Cùng họ `N_DAY_DU` 596/451: tài liệu và mã nói hai con số khác nhau.

    Khai báo cấm thẳng: *"Điều KHÔNG được làm sau khi thấy số: đổi ngưỡng
    120 phút, đổi mốc 5/3, hay nới khoảng 07–11/09."* Nên ba con số ấy
    phải đọc được từ `docs/STATE.md` và phải bằng ba hằng số trong mã.
    """
    van = (GOC / "docs" / "STATE.md").read_text(encoding="utf-8")
    dau = van.index("KHAI TRƯỚC — CƠ CHẾ RƠI NHỊP")
    khoi = van[dau:dau + 3000]

    assert f"A <= {drn.NGUONG_TRE_PHUT} phut" in khoi, (
        f"NGUONG_TRE_PHUT = {drn.NGUONG_TRE_PHUT} khong co trong ban khai")
    assert f"B >= {drn.B_NHIEU}" in khoi, f"B_NHIEU = {drn.B_NHIEU} lech ban khai"
    assert f"B <= {drn.B_IT}" in khoi, f"B_IT = {drn.B_IT} lech ban khai"

    ngay = re.findall(r"(\d{2}) -> (\d{2})/09", khoi)
    assert ngay, "ban khai khong neu khoang ngay"
    assert (int(ngay[0][0]), int(ngay[0][1])) == (drn.CUA_SO[0].day,
                                                 drn.CUA_SO[1].day), (
        f"cua so trong ma {drn.CUA_SO} lech khoang da khai {ngay[0]}")
    print(f"PASS  ba nguong khop ban khai: {drn.NGUONG_TRE_PHUT} phut · "
          f"B>={drn.B_NHIEU}/B<={drn.B_IT} · {drn.CUA_SO[0]}->{drn.CUA_SO[1]}")


# ══ Phép quy một mốc về khe đã hẹn ═════════════════════════════════════
def test_TRE_QUA_NUA_DEM_thuoc_ve_khe_HOM_TRUOC():
    """Trễ 4 giờ thuộc khe cùng ngày; trễ qua nửa đêm thuộc khe hôm trước.

    Quy sai thì một nhịp trễ 15 giờ đọc ra trễ âm, và trung vị tụt xuống
    dưới ngưỡng — đúng chiều làm kết quả đẹp lên.
    """
    khe = drn.NHIP["chuong-bao-quet.yml"]
    cung_ngay = drn.khe_gan_nhat_truoc(_moc("2026-09-07T13:41:03"), khe)
    assert cung_ngay == _moc("2026-09-07T09:23:00")

    qua_dem = drn.khe_gan_nhat_truoc(_moc("2026-09-08T01:10:00"), khe)
    assert qua_dem == _moc("2026-09-07T09:23:00"), "khong lui ve khe hom truoc"
    assert drn.tre_phut(_moc("2026-09-08T01:10:00"), qua_dem) > 0
    print("PASS  moc tre qua nua dem quy ve khe HOM TRUOC, tre van duong")


def test_NGAY_KHONG_CO_LUOT_NAO_van_duoc_dem_la_0():
    """Bỏ ngày rỗng ra khỏi trung vị làm tuần hỏng trông như tuần vắng số."""
    cua_so = (date(2026, 9, 7), date(2026, 9, 11))
    mocs = [_moc("2026-09-07T07:00:00"), _moc("2026-09-07T07:30:00"),
            _moc("2026-09-11T07:00:00")]
    dem = drn.dem_moi_ngay_lam_viec(mocs, cua_so)
    assert dem == [2, 0, 0, 0, 1], dem
    assert len(dem) == 5, "cua so nam ngay lam viec phai cho nam so"
    print(f"PASS  ngay rong dem la 0: {dem}")


def test_CUOI_TUAN_khong_nam_trong_ngay_lam_viec():
    """Cron khai `1-5`. Đếm cả thứ Bảy là tự thêm một ngày rơi giả."""
    ngay = drn.ngay_lam_viec((date(2026, 9, 5), date(2026, 9, 13)))
    assert all(d.weekday() < 5 for d in ngay)
    assert date(2026, 9, 11) in ngay, "thu Sau 11/09 phai co"
    assert date(2026, 9, 12) not in ngay, "12/09/2026 la thu BAY"
    assert date(2026, 9, 5) not in ngay, "05/09/2026 la thu BAY"
    assert ngay == [date(2026, 9, d) for d in range(7, 12)], ngay
    print(f"PASS  chi ngay lam viec: {len(ngay)} ngay trong khoang 05->13/09")


def _chuoi_khong_phai_docstring(duong: Path) -> list[str]:
    """Mọi chuỗi hằng trong mã, TRỪ docstring.

    `CLAUDE.md` mục *"Gác phải đọc AST, không đọc `in`"*: một tên còn nằm
    trong khối chú thích thì phép kiểm dạng văn bản vô hiệu. Ở đây nó tự
    cắn ngay lượt chạy đầu — docstring giải thích *vì sao không đọc
    `conclusion`* chứa đúng chữ ấy.
    """
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    bo_qua = set()
    for nut in ast.walk(cay):
        if isinstance(nut, (ast.Module, ast.FunctionDef,
                            ast.AsyncFunctionDef, ast.ClassDef)):
            than = getattr(nut, "body", [])
            if (than and isinstance(than[0], ast.Expr)
                    and isinstance(than[0].value, ast.Constant)
                    and isinstance(than[0].value.value, str)):
                bo_qua.add(id(than[0].value))
    return [n.value for n in ast.walk(cay)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in bo_qua]


def test_DEM_moi_luot_duoc_TAO_khong_loc_theo_ket_cuc():
    """BƯỚC 28 đã trả giá để ghi ra phân biệt này — khoá nó bằng mã nguồn.

    `chuong_bao_quet.py` lọc `conclusion == "success"` vì nó hỏi *"ngày này
    có được quét không"*. Dụng cụ đo RƠI NHỊP hỏi *"GitHub có TẠO lượt chạy
    không"*, nên một lượt `failure` hay `queued` vĩnh viễn vẫn là nhịp KHÔNG
    rơi. Lọc `success` ở đây sẽ đếm nhầm hai kiểu hỏng thành rơi nhịp.
    """
    chuoi = _chuoi_khong_phai_docstring(GOC / "tools" / "do_roi_nhip.py")
    dinh_kem = [c for c in chuoi if "conclusion" in c]
    assert not dinh_kem, (
        f"do_roi_nhip.py dang DUNG `conclusion` trong ma: {dinh_kem}\n"
        "No dang dem KET CUC chu khong dem NHIP DUOC TAO. "
        "Xem docs/STATE.md BUOC 28.")
    assert any("createdAt" in c for c in chuoi), "phai doc moc TAO"
    print(f"PASS  {len(chuoi)} chuoi trong ma, khong chuoi nao loc ket cuc")
