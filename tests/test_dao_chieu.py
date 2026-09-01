"""Phép kiểm đảo chiều phải giữ được KỶ LUẬT của một bản khai trước.

Một phép kiểm khai trước chỉ có giá trị nếu ba thứ không trôi được sau khi
người ta đã thấy con số:

  1. DẤU. Giả thuyết nói "âm". Một rho dương có ý nghĩa phải BÁC BỎ giả
     thuyết, không được đọc thành "tìm thấy tín hiệu". Đây là chỗ dễ trôi
     nhất, và nó trôi mà không để lại dấu vết nào trong kết quả.
  2. Ô CHÍNH. Nó được chọn theo LỰC PHÁT HIỆN. BƯỚC 7 đã chọn theo ý nghĩa
     kinh tế và tự ghi lại đó là lỗi.
  3. Ô THIẾU LỰC phải THẬT SỰ ĐƯỢC CHẠY. Khai một ô là không đọc được rồi
     không chạy nó thì lời khai ấy chỉ là trang trí.

Và một điều nữa, tìm ra ngày 01/09/2026 khi chạy lượt đầu: ô duy nhất
"ĐẠT" là ô đã khai trước là thiếu lực. Thứ chặn nó thành một phát hiện là
BẢN KHAI TRƯỚC cộng hiệu chỉnh năm ô (Bonferroni đòi p < 0,01; nó cho
0,019) — KHÔNG phải chứng cứ âm. Chứng cứ âm hôm ấy báo sàn nhiễu hỏng,
và chính nó mới là cái sai; xem `docs/STATE.md`, BƯỚC 9.
"""
import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import experiment_dao_chieu as D          # noqa: E402

NGUON = GOC / "experiment_dao_chieu.py"
CAY = ast.parse(NGUON.read_text(encoding="utf-8"))


def _ham(ten: str) -> ast.FunctionDef:
    for n in ast.walk(CAY):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"không có hàm {ten}")


def _gan(ten: str) -> ast.AST:
    for n in ast.walk(CAY):
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == ten for t in n.targets):
            return n.value
    raise AssertionError(f"không có gán {ten}")


def _goi_trong(nut: ast.AST) -> set:
    ra = set()
    for n in ast.walk(nut):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                ra.add(f.id)
            elif isinstance(f, ast.Attribute):
                ra.add(f.attr)
    return ra


def test_dau_am_la_gia_thuyet_va_dau_duong_la_BAC_BO():
    """Luật quyết định, kiểm bằng HÀNH VI của chính hàm.

    Bốn kết cục phải là bốn câu khác nhau. Nếu "ngược dấu" bị gộp vào
    "không đạt" thì phép kiểm mất đúng phần đắt nhất của việc khai dấu
    trước: khả năng BÁC BỎ giả thuyết chứ không chỉ không xác nhận nó.
    """
    p5, p95, rao = -0.02, 0.02, 0.04

    assert "BÁC BỎ" in D.phan_xu(0.05, p5, p95, rao), (
        "rho DƯƠNG có ý nghĩa phải BÁC BỎ giả thuyết đảo chiều — "
        "đọc nó thành 'tìm thấy tín hiệu' là lật dấu sau khi thấy số")
    assert "ĐẠT" not in D.phan_xu(0.05, p5, p95, rao)

    assert D.phan_xu(0.0, p5, p95, rao) == "không vượt sàn nhiễu"
    assert "DƯỚI rào" in D.phan_xu(-0.03, p5, p95, rao), (
        "âm có ý nghĩa nhưng dưới rào hoà vốn KHÔNG phải là đạt")
    assert D.phan_xu(-0.05, p5, p95, rao).startswith("ĐẠT")
    print("PASS  bốn kết cục là bốn câu; dương có ý nghĩa = BÁC BỎ")


def test_o_chinh_KHONG_nam_trong_nhom_thieu_luc():
    """Chọn ô chính theo ý nghĩa kinh tế là đúng lỗi BƯỚC 7 đã ghi lại."""
    assert (D.J_CHINH, D.H_CHINH) not in D.O_THIEU_LUC, (
        f"ô chính ({D.J_CHINH},{D.H_CHINH}) nằm trong nhóm đã khai là "
        f"thiếu lực — kết luận chính khi đó không đọc được")
    print(f"PASS  ô chính J={D.J_CHINH} h={D.H_CHINH} không thiếu lực")


def test_moi_o_khai_la_thieu_luc_deu_THAT_SU_duoc_chay():
    """Khai một ô rồi không chạy nó thì lời khai chỉ là trang trí.

    Chạy chúng mới là chỗ đắt: lượt đầu (01/09/2026) đúng một ô thiếu lực
    cho ra "ĐẠT", và chính việc nó ĐƯỢC chạy kèm nhãn "không đọc được" đã
    chặn một phát hiện giả.
    """
    duoc_chay = set(D.O_THU_CAP) | {(D.J_CHINH, D.H_CHINH)}
    thieu = [o for o in D.O_THIEU_LUC if o not in duoc_chay]
    assert not thieu, f"ô khai thiếu lực nhưng không có trong lượt chạy: {thieu}"
    print(f"PASS  {len(D.O_THIEU_LUC)} ô thiếu lực đều được chạy kèm nhãn")


def test_nguong_bao_gia_SUY_RA_tu_ALPHA_chu_khong_go_tay():
    """Kiểm HÌNH DẠNG biểu thức, không kiểm giá trị.

    `2 * ALPHA` bằng 0,10. Mọi đột biến cho ra 0,10 tại điểm này — `ALPHA
    + 0.05`, hằng số 0.10 — đều lọt qua một phép so giá trị. Đây đúng bài
    học của `TRAN * N / 225` ngày 31/08/2026.
    """
    v = _gan("TY_LE_BAO_GIA_TOI_DA")
    assert isinstance(v, ast.BinOp), (
        "TY_LE_BAO_GIA_TOI_DA phải là biểu thức SUY RA từ ALPHA, "
        "không phải một con số gõ tay")
    ten = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}
    assert "ALPHA" in ten, f"biểu thức không nhắc ALPHA: {ten}"
    print("PASS  ngưỡng báo giả suy ra từ ALPHA (kiểm bằng AST)")


def test_chung_cu_am_dung_DAC_TRUNG_THAT_dich_vong_khong_dung_nhieu_trang():
    """Nhiễu trắng cho một câu trả lời dễ dãi.

    Đặc trưng giả phải giữ TỰ TƯƠNG QUAN của đặc trưng thật. Thay bằng
    `standard_normal` là bỏ mất đúng tính chất đang cần kiểm, và cả
    `chung_cu_am` lẫn `nguong_hieu_chuan` sẽ cho một câu trả lời dễ dãi.
    """
    goi = _goi_trong(_ham("chung_cu_am"))
    assert "_dac_trung_gia" in goi, (
        "chung_cu_am không dựng đặc trưng giả qua _dac_trung_gia")
    assert "bang" in goi, "chung_cu_am không lấy đặc trưng thật qua bang()"

    # Và NGƯỠNG hiệu chuẩn phải dùng đúng cỗ máy đó, không phải một bản
    # dựng riêng — hai bản sao sẽ trôi ra khỏi nhau.
    assert "_dac_trung_gia" in _goi_trong(_ham("nguong_hieu_chuan")), (
        "nguong_hieu_chuan dựng đặc trưng giả bằng đường khác")

    gia = _goi_trong(_ham("_dac_trung_gia"))
    assert "roll" in gia, (
        "_dac_trung_gia không dịch vòng đặc trưng thật — dựng bằng nhiễu "
        "thì tự tương quan biến mất và phép hiệu chuẩn luôn xanh")
    assert "standard_normal" not in gia, (
        "_dac_trung_gia dùng nhiễu trắng làm đặc trưng giả")
    print("PASS  đặc trưng giả = dịch vòng đặc trưng THẬT, một đường duy nhất")


def test_nhanh_CLI_that_su_GOI_chung_cu_am():
    """"Hàm tồn tại" khác "nhánh có gọi hàm".

    Đột biến biến nhánh thành no-op sống sót ngày 31/08/2026 đúng vì test
    kiểm hàm như một hàm thuần mà không kiểm chỗ nối.
    """
    main = _ham("main")
    nhanh = [n for n in ast.walk(main)
             if isinstance(n, ast.If)
             and "chung_cu_am" in {a.attr for a in ast.walk(n.test)
                                   if isinstance(a, ast.Attribute)}]
    assert nhanh, "không có nhánh `if a.chung_cu_am:` trong main()"
    assert "chung_cu_am" in _goi_trong(nhanh[0]), (
        "nhánh --chung-cu-am không gọi chung_cu_am — cờ có mặt trên CLI "
        "nhưng không nối vào đâu")
    print("PASS  nhánh --chung-cu-am thật sự gọi chung_cu_am")


def test_dac_trung_KHONG_nhin_trom_tuong_lai():
    """x[t] chỉ được phụ thuộc close[0..t]. Đổi giá tương lai -> x[t] y nguyên."""
    n = 60
    gia = pd.DataFrame({"close": np.linspace(10.0, 20.0, n)})
    x1 = D.loi_nhuan_qua_khu(gia, 21)
    gia2 = gia.copy()
    gia2.loc[40:, "close"] = 999.0
    x2 = D.loi_nhuan_qua_khu(gia2, 21)
    np.testing.assert_allclose(x1[21:40], x2[21:40], rtol=0, atol=0)
    assert not np.allclose(x1[45], x2[45]), "phép thử không đổi được gì"
    print("PASS  đặc trưng không nhìn trộm (bất biến 1)")


def test_hang_thanh_khoan_KHONG_nhin_trom_tuong_lai():
    """Xếp hạng bằng trung vị TOÀN MẪU là nhìn trộm — mã lên hạng sau sẽ
    được gán 'lớn' cho cả giai đoạn nó còn nhỏ."""
    n = D.CUA_SO_THANH_KHOAN + 40
    ngay = [f"2020-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)]

    def _kho(cuoi_A: float) -> dict:
        ra = {}
        for ma, muc in (("A", 1.0), ("B", 2.0)):
            v = np.full(n, muc)
            if ma == "A":
                v[D.CUA_SO_THANH_KHOAN + 20:] = cuoi_A
            ra[ma] = pd.DataFrame({"close": np.ones(n), "volume": v},
                                  index=ngay)
        return ra

    h1 = D.hang_thanh_khoan(_kho(1.0))
    h2 = D.hang_thanh_khoan(_kho(500.0))
    t = D.CUA_SO_THANH_KHOAN + 5
    assert h1["A"].iloc[t] == h2["A"].iloc[t], (
        "thanh khoản TƯƠNG LAI của A đổi hạng của A ở hiện tại — "
        "xếp hạng đang dùng thông tin chưa tồn tại")
    print("PASS  hạng thanh khoản nhân quả")


def test_rao_hoa_von_LAY_TU_so_lenh_chu_khong_go_tay():
    """Phí phải chảy từ `paper_metrics.ROUND_TRIP_COST_PCT` vào tận đây.

    Hai bản sao của một hằng số phí sẽ trôi ra khỏi nhau, và lần trôi đó
    không làm test nào đỏ.
    """
    nhap = {n.module for n in ast.walk(CAY) if isinstance(n, ast.ImportFrom)
            and n.module}
    assert "experiment_tran_dac_trung" in nhap
    assert "rao_hoa_von" in _goi_trong(_ham("kiem_o")), (
        "kiem_o không gọi rao_hoa_von — rào đang được lấy từ đâu?")
    from paper_metrics import ROUND_TRIP_COST_PCT
    from experiment_tran_dac_trung import TRUOT_GIA_DPT, chi_phi_vong
    assert abs(chi_phi_vong() - (ROUND_TRIP_COST_PCT + TRUOT_GIA_DPT)) < 1e-12
    print(f"PASS  rào suy từ phí sổ lệnh · chi phí vòng {chi_phi_vong():.2f}%")


def test_so_luot_chung_cu_am_phai_TU_BIEN_MINH_DUOC():
    """Số lượt phải đủ để CHỨNG MINH một ô là hiệu chuẩn, không chỉ để gợi ý.

    Đây là lỗi đã xảy ra ngày 01/09/2026. Bản đầu chạy 40 lượt và in
    "5,0%" như một con số; lượt sau khác hạt giống cho 10,0%. Ở 40 lượt,
    một tỷ lệ thật 5% có KTC [1,4% ; 16,5%] — cận trên VƯỢT ngưỡng 10%,
    tức phép đo không thể chứng minh nổi điều nó vừa khẳng định.

    Gác này bắt số lượt phải lớn tới mức: nếu ô ĐÚNG là hiệu chuẩn ở mức
    ALPHA thì cận trên của khoảng nằm dưới ngưỡng. Không đủ thì mọi ô đều
    "chưa chứng minh được" và cờ `--chung-cu-am` thành vô dụng.
    """
    n = D.SO_LAN_CHUNG_CU_AM
    k = round(D.ALPHA * n)
    _, tren = D.khoang_wilson(k, n)
    assert tren <= D.TY_LE_BAO_GIA_TOI_DA, (
        f"{n} lượt là quá ít: một ô hiệu chuẩn hoàn hảo ({k}/{n} = "
        f"{k / n:.1%}) vẫn cho cận trên {tren:.1%} > ngưỡng "
        f"{D.TY_LE_BAO_GIA_TOI_DA:.1%}. Phép đo không kết luận được gì.")
    print(f"PASS  {n} lượt đủ để chứng minh: {k}/{n} -> cận trên {tren:.1%}")


def test_khoang_la_WILSON_chu_khong_phai_khoang_chuan():
    """Khoảng chuẩn trả [0 ; 0] khi k=0 — nó biến "chưa thấy lần nào" thành
    "chắc chắn bằng không", và có thể trả cận dưới ÂM ở k nhỏ."""
    duoi, tren = D.khoang_wilson(0, 200)
    assert tren > 0.0, (
        "k=0 mà cận trên bằng 0 — đây là khoảng chuẩn, không phải Wilson; "
        "nó khẳng định một điều mà 200 lượt không thể khẳng định")
    assert duoi >= 0.0, "cận dưới âm cho một tỷ lệ"
    duoi1, _ = D.khoang_wilson(1, 40)
    assert duoi1 >= 0.0
    print(f"PASS  Wilson: 0/200 -> [{duoi:.1%} ; {tren:.1%}]")


def test_phan_xu_hieu_chuan_la_FAIL_CLOSED_dung_CAN_TREN():
    """Đọc được chỉ khi CHỨNG MINH ĐƯỢC, tức cận TRÊN dưới ngưỡng.

    Lấy điểm ước lượng — hoặc tệ hơn, cận dưới — cho phép một phép đo quá
    ít lượt tự xưng là sạch. Cùng hình dạng với `vnstock_goi.kiem_goi()`
    phải có trạng thái thứ ba: mất mạng mà trả "khớp" là cổng xanh giả.
    """
    main = _ham("main")
    nhanh = [n for n in ast.walk(main)
             if isinstance(n, ast.If)
             and "chung_cu_am" in {a.attr for a in ast.walk(n.test)
                                   if isinstance(a, ast.Attribute)}]
    assert nhanh, "không có nhánh `if a.chung_cu_am:`"

    gan_ktc = [n for n in ast.walk(nhanh[0]) if isinstance(n, ast.Assign)
               and isinstance(n.value, ast.Call)
               and getattr(n.value.func, "id", "") == "khoang_wilson"]
    assert gan_ktc, "nhánh không dựng khoảng tin cậy"
    ten = [e.id for e in gan_ktc[0].targets[0].elts]
    can_tren = ten[1]

    gan_ok = [n for n in ast.walk(nhanh[0]) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "ok"
                      for t in n.targets)]
    assert gan_ok, "nhánh không quyết định `ok`"
    ss = gan_ok[0].value
    assert isinstance(ss, ast.Compare), "phán xử hiệu chuẩn không phải phép so"
    assert isinstance(ss.left, ast.Name) and ss.left.id == can_tren, (
        f"phán xử dùng {getattr(ss.left, 'id', ss.left)!r} chứ không phải "
        f"cận trên {can_tren!r} — đây là fail-OPEN")
    print(f"PASS  phán xử hiệu chuẩn dùng cận trên ({can_tren}), fail-closed")


def test_san_nhieu_TU_KHAI_o_nhip_CHUA_AI_DOI_CHIEU(capsys):
    """Im lặng ở nhịp đã kiểm, tự khai ở nhịp chưa ai kiểm.

    Đây là hàm BƯỚC 7 cũng dùng. Một dòng trong tài liệu thì phiên sau
    không đọc; một dòng ra `stderr` ngay lúc chạy thì có.

    Kiểm CẢ HAI chiều. Chỉ kiểm chiều "có kêu" thì một đột biến bắt kêu ở
    mọi nhịp vẫn xanh — mà cảnh báo kêu cả ở chỗ đã kiểm thì bị tắt trong
    một tuần, và một cảnh báo bị tắt bằng không có.
    """
    import experiment_tran_dac_trung as E

    y = np.arange(300, dtype=float)
    chi_so = {"A": np.arange(300)}
    rng = np.random.default_rng(0)

    assert 63 in E.NHIP_DA_DOI_CHIEU, (
        "h=63 ĐÃ được đối chiếu ngày 01/09/2026 — bỏ nó khỏi danh sách là "
        "vứt đi một phép đo đã trả tiền")

    for h in E.NHIP_DA_DOI_CHIEU:
        E._DA_CANH_BAO.clear()
        E.san_nhieu(lambda v: float(v[0]), y, chi_so, h, rng, 3)
        assert capsys.readouterr().err == "", (
            f"cảnh báo ở nhịp h={h} ĐÃ đối chiếu — kêu sai chỗ thì bị tắt")

    chua = next(h for h in range(5, 200) if h not in E.NHIP_DA_DOI_CHIEU)
    E._DA_CANH_BAO.clear()
    E.san_nhieu(lambda v: float(v[0]), y, chi_so, chua, rng, 3)
    err = capsys.readouterr().err
    assert "san_nhieu" in err and str(chua) in err, (
        f"nhịp h={chua} chưa ai đối chiếu mà không có cảnh báo: {err!r}")

    E.san_nhieu(lambda v: float(v[0]), y, chi_so, chua, rng, 3)
    assert capsys.readouterr().err == "", (
        "cảnh báo lặp — san_nhieu bị gọi hàng trăm lần liên tiếp, "
        "lặp 200 dòng là 200 dòng bị bỏ qua")
    print(f"PASS  im ở {len(E.NHIP_DA_DOI_CHIEU)} nhịp đã kiểm, "
          f"kêu một lần ở h={chua}")


def test_experiment_tran_dac_trung_reconfigure_CA_stderr():
    """Cảnh báo đi bằng stderr, và nó có dấu tiếng Việt.

    Thiếu dòng này thì cảnh báo ra dạng `\u1ec7...` — không nổ, nhưng
    không ai đọc nổi. Cùng họ với `UnicodeEncodeError` đã tái diễn ba lần
    (22, 23, 24/08/2026), chỉ khác là lần này nó im chứ không nổ.
    """
    src = (GOC / "experiment_tran_dac_trung.py").read_text(encoding="utf-8")
    cay = ast.parse(src)
    luong = {n.func.value.attr for n in ast.walk(cay)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == "reconfigure"
             and isinstance(n.func.value, ast.Attribute)}
    assert "stderr" in luong, (
        "experiment_tran_dac_trung không reconfigure stderr — cảnh báo "
        "hiệu chuẩn sẽ ra dạng thoát unicode")
    assert "stdout" in luong
    print("PASS  cả stdout lẫn stderr được reconfigure")


def _kho_gia_lap(so_ma: int = 4, so_phien: int = 420) -> dict:
    """Bộ giá tổng hợp đủ để chạy `bang()` — không đụng cache thật."""
    rng = np.random.default_rng(3)
    ngay = pd.bdate_range("2020-01-01", periods=so_phien).strftime("%Y-%m-%d")
    kh = {}
    for i in range(so_ma):
        b = np.cumsum(rng.standard_normal(so_phien)) * 0.01
        kh[f"M{i}"] = pd.DataFrame(
            {"close": 20.0 * np.exp(b),
             "volume": rng.integers(1_000, 50_000, so_phien).astype(float)},
            index=ngay)
    return kh


def test_nguong_hieu_chuan_lay_DUNG_DUOI_cua_phan_phoi():
    """Giả thuyết là ÂM, nên ngưỡng phải nằm ở đuôi DƯỚI.

    Đột biến lấy `1 − ALPHA` cho một ngưỡng DƯƠNG lớn, và khi đó
    `rho < ngưỡng` gần như luôn đúng — phép kiểm biến thành cỗ máy sinh
    phát hiện. Giá trị tuyệt đối thì trông vẫn "hợp lý", nên chỉ một tính
    chất về VỊ TRÍ mới bắt được.
    """
    kq = D.nguong_hieu_chuan(_kho_gia_lap(), 21, 21,
                             np.random.default_rng(0), so_lan=60)
    assert kq["nguong"] < kq["tb"], (
        f"ngưỡng {kq['nguong']:.4f} không nằm dưới trung bình "
        f"{kq['tb']:.4f} — đang lấy nhầm đuôi")
    assert kq["sd"] > 0.0
    print(f"PASS  ngưỡng ở đuôi dưới: {kq['nguong']:.4f} < TB {kq['tb']:.4f}")


def test_nhanh_CLI_that_su_GOI_nguong_hieu_chuan():
    """Lại là chỗ nối, không phải sự tồn tại."""
    main = _ham("main")
    nhanh = [n for n in ast.walk(main)
             if isinstance(n, ast.If)
             and "nguong_hieu_chuan" in {a.attr for a in ast.walk(n.test)
                                         if isinstance(a, ast.Attribute)}]
    assert nhanh, "không có nhánh `if a.nguong_hieu_chuan:`"
    assert "nguong_hieu_chuan" in _goi_trong(nhanh[0]), (
        "nhánh --nguong-hieu-chuan không gọi nguong_hieu_chuan")
    assert "kiem_o" in _goi_trong(nhanh[0]), (
        "nhánh không đối chiếu với phán xử theo sàn nhiễu cũ — không có "
        "đối chiếu thì không thấy được ngưỡng mới đổi gì")
    print("PASS  nhánh --nguong-hieu-chuan gọi cả ngưỡng mới lẫn kiem_o")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
