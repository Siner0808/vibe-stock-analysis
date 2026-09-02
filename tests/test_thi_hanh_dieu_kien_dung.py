"""Điều kiện dừng phải ĐỔI TRẠNG THÁI, không chỉ thêm một dòng chữ.

VÌ SAO CÓ FILE NÀY
──────────────────
Nguyên nhân nặng nhất của cổng C5 (xem `docs/STATE.md` — "GỐC RỄ CỦA
CỔNG C5") là điều kiện dừng **không có ai thi hành**:
`dieu_kien_dong_lai()` chỉ được gọi bên trong `paper_metrics.report()`,
một hàm nối chuỗi, và khi đạt nó thêm đúng một CÂU VĂN vào một tệp zip
lưu 14 ngày. Kể cả nếu điều kiện có lực phát hiện 100%, nó vẫn không
đóng được cổng.

File này khoá năm thứ, và thứ tự quan trọng:
  1. đạt điều kiện ⇒ cờ THẬT SỰ đổi giá trị (không phải trả về một chuỗi);
  2. chưa đạt ⇒ KHÔNG đụng vào cờ (một hàng rào hay tự sập thì bị gỡ);
  3. chỗ gọi nằm TRƯỚC vòng quét (sau vòng quét là muộn đúng một phiên);
  4. chuông C5 kêu đúng lúc — và KHÔNG kêu khi cổng đã đóng;
  5. và — thêm 31/08/2026 — cổng đã đóng phải CHỨNG MINH ĐƯỢC TỪ SỔ LỆNH
     rằng nó chặn. Bốn thứ trên đều đọc mã nguồn; thứ năm đọc dữ liệu, và
     đó là khác biệt giữa "đã khai là chặn" và "đã chặn".
"""
import ast
import datetime as dt
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import paper_trading as pt        # noqa: E402
import run_daily as rd            # noqa: E402
from paper_trading import Trade   # noqa: E402
import canh_cong_c5              # noqa: E402

MOC = dt.datetime(2026, 8, 7, 14, 41).timestamp()


def _ngay(n: int) -> str:
    return (dt.date(2024, 1, 5) + dt.timedelta(days=n)).isoformat()


def _lenh(i: int, loi_nhuan: float) -> Trade:
    """Lệnh tiến-về-trước đã đóng: ghi cách nhau một ngày, nên không thành lô."""
    ngay = _ngay(i * 3)
    return Trade(
        id=i, symbol="FPT", signal_date=ngay, entry_date=ngay,
        entry_price=100.0, exit_date=ngay,
        exit_price=100.0 * (1 + loi_nhuan / 100),
        exit_reason="STOP_LOSS", stop_loss=93.0, take_profit=110.0,
        size_pct=10.0, entry_score=62, status="CLOSED",
        created_at=MOC + 86400 * (i + 1))


def _ro(ts: list[Trade], alpha: float) -> dict:
    """Rổ chuẩn sao cho alpha mỗi lệnh đúng bằng `alpha`.

    Dựng từ chính `net_return_pct()` nên không phải tự viết phép tính lợi
    nhuận — thứ `NGUYEN-TAC-DO-LUONG.md` cấm.
    """
    return {(t.entry_date, t.exit_date): t.net_return_pct() - alpha
            for t in ts}


def _so_lo_nang() -> tuple[list[Trade], dict]:
    """200 lệnh, alpha −3%/lệnh: KTC loại được 0 ⇒ điều kiện ĐẠT.

    Từ bản 2 (29/08/2026) điều kiện đo ALPHA chứ không đo kỳ vọng, và mốc
    tối thiểu là `paper_metrics.N_TOI_THIEU` chứ không phải 60.
    """
    ts = [_lenh(i, -8.0 + (i % 5) * 0.4) for i in range(200)]
    return ts, _ro(ts, -3.0)


def _so_chua_du() -> tuple[list[Trade], dict]:
    """Ít hơn mốc tối thiểu, lỗ nặng ⇒ điều kiện KHÔNG đạt."""
    ts = [_lenh(i, -8.0) for i in range(30)]
    return ts, _ro(ts, -3.0)


# ── 1. Đạt điều kiện thì cờ THẬT SỰ đổi ──────────────────────────────

def test_dat_dieu_kien_thi_TAT_co():
    ghi = []
    da_dong, thong_diep = rd.thi_hanh_dieu_kien_dung(*_so_lo_nang()[:1], ghi.append,
                                                 _so_lo_nang()[1])
    assert da_dong is True, thong_diep
    assert ghi == [False], f"cờ được đặt thành {ghi}, phải là [False]"
    assert "ĐÃ ĐẠT" in thong_diep, thong_diep
    print(f"PASS  đạt -> đặt cờ {ghi} · {thong_diep[:48]}…")


def test_co_thuc_su_doi_gia_tri_tren_module():
    """Chứng minh bằng CHẠY, không bằng đọc: cờ thật đổi từ True sang False."""
    cu = pt.CHO_PHEP_MO_LENH_MOI
    try:
        pt.CHO_PHEP_MO_LENH_MOI = True
        _ts, _ro_c = _so_lo_nang()
        rd.thi_hanh_dieu_kien_dung(
            _ts, lambda v: setattr(pt, "CHO_PHEP_MO_LENH_MOI", v), _ro_c)
        assert pt.CHO_PHEP_MO_LENH_MOI is False
    finally:
        pt.CHO_PHEP_MO_LENH_MOI = cu
    print("PASS  cờ trên module đổi True -> False khi điều kiện đạt")


# ── 2. Chưa đạt thì KHÔNG đụng vào cờ ────────────────────────────────

def test_chua_du_mau_thi_KHONG_dung_vao_co():
    ghi = []
    da_dong, thong_diep = rd.thi_hanh_dieu_kien_dung(_so_chua_du()[0], ghi.append,
                                                 _so_chua_du()[1])
    assert da_dong is False and ghi == [], f"đã đụng vào cờ: {ghi}"
    print(f"PASS  chưa đủ mẫu -> không đụng cờ · {thong_diep[:48]}…")


def test_dang_lai_thi_KHONG_dung_vao_co():
    ghi = []
    _ts = [_lenh(i, +6.0) for i in range(200)]
    da_dong, _ = rd.thi_hanh_dieu_kien_dung(_ts, ghi.append, _ro(_ts, +3.0))
    assert da_dong is False and ghi == []
    print("PASS  đang lãi -> không đụng cờ")


def test_so_rong_thi_KHONG_dung_vao_co():
    ghi = []
    assert rd.thi_hanh_dieu_kien_dung([], ghi.append, {})[0] is False
    assert ghi == []
    print("PASS  sổ rỗng -> không đụng cờ")


# ── 3. Chỗ gọi nằm TRƯỚC vòng quét ───────────────────────────────────

def _ham(ten: str) -> ast.FunctionDef:
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"không tìm thấy hàm {ten}")


def test_goi_dung_mot_lan_va_TRUOC_vong_quet():
    """Thi hành sau vòng quét là muộn đúng một phiên — phiên không được có."""
    ham = _ham("execute_daily_scan")
    goi = [n for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "thi_hanh_dieu_kien_dung"]
    assert len(goi) == 1, f"gọi {len(goi)} lần, phải đúng 1"

    vong = [n for n in ast.walk(ham)
            if isinstance(n, ast.For) and isinstance(n.iter, ast.Call)
            and isinstance(n.iter.func, ast.Name)
            and n.iter.func.id == "enumerate"]
    assert vong, "không tìm thấy vòng quét rổ"
    assert goi[0].lineno < min(v.lineno for v in vong), (
        f"thi hành ở dòng {goi[0].lineno}, vòng quét bắt đầu ở dòng "
        f"{min(v.lineno for v in vong)} — thi hành phải đứng TRƯỚC")
    print(f"PASS  thi hành dòng {goi[0].lineno} < vòng quét dòng "
          f"{min(v.lineno for v in vong)}")


def test_ham_dat_co_that_su_gan_vao_co_C5():
    """Truyền vào một hàm đặt cờ rỗng thì test trên vẫn xanh mà đời vẫn hỏng."""
    ham = _ham("execute_daily_scan")
    goi = [n for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "thi_hanh_dieu_kien_dung"][0]
    nguon = ast.dump(goi.args[1])
    assert "setattr" in nguon, nguon
    assert "CHO_PHEP_MO_LENH_MOI" in nguon, nguon
    print("PASS  hàm đặt cờ gán thật vào CHO_PHEP_MO_LENH_MOI")


# ── 4. Chuông C5 kêu đúng lúc ────────────────────────────────────────

def test_chuong_kEU_khi_dat_ma_cong_van_MO():
    ma, td = canh_cong_c5.kiem(*_so_lo_nang()[:1], cong_dang_mo=True,
                               benchmark=_so_lo_nang()[1])
    assert ma == 1 and "VẪN MỞ" in td, td
    print(f"PASS  đạt + cổng mở -> kêu ({ma})")


def test_chuong_IM_khi_dat_nhung_cong_da_DONG():
    """Kêu khi đã đúng trạng thái là dạy người ta bỏ qua chuông."""
    ma, td = canh_cong_c5.kiem(_so_lo_nang()[0], cong_dang_mo=False,
                               benchmark=_so_lo_nang()[1])
    assert ma == 0 and "ĐÃ ĐÓNG" in td, td
    print(f"PASS  đạt + cổng đóng -> im ({ma})")


def test_chuong_IM_khi_chua_dat():
    for mo in (True, False):
        ma, td = canh_cong_c5.kiem(_so_chua_du()[0], cong_dang_mo=mo,
                                   benchmark=_so_chua_du()[1])
        assert ma == 0, (mo, td)
    print("PASS  chưa đạt -> im, dù cổng mở hay đóng")


# ── 5. Cổng đã đóng có CHẶN THẬT không ───────────────────────────────
#
# `kiem()` hỏi "điều kiện đạt chưa, cổng còn mở không" — cả hai vế đọc từ
# MÃ NGUỒN. `kiem_ro_ri()` hỏi một câu chỉ dữ liệu trả lời được: kể từ
# lúc đóng, đã có vị thế mới nào được mở chưa.
#
# Vì sao câu hỏi đó không thừa: ngày 31/08/2026 bốn lệnh chờ đầu tiên
# khớp trong khi cổng đang đóng. Đó là hành vi ĐÚNG (`fill_pending`
# không đọc cờ C5), nhưng nó cũng là ngày đầu tiên sổ lệnh động đậy dưới
# một cái cổng đóng — tức ngày đầu tiên câu "cổng có chặn không" có thể
# trả lời sai mà không ai thấy.

_MOC_DONG = canh_cong_c5.moc_dong_cong(pt.NGAY_DONG_CONG_C5)


def _qd(acted: int, at: float, symbol: str = "FPT") -> dict:
    """Một dòng `decisions` rút gọn — đúng ba trường mà `kiem_ro_ri` đọc."""
    return {"acted": acted, "at": at, "symbol": symbol}


def _ham_chuong(ten: str) -> ast.FunctionDef:
    cay = ast.parse((GOC / "tools" / "canh_cong_c5.py").read_text(
        encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"canh_cong_c5.py không có hàm {ten}")


def test_cong_dong_ma_van_vao_lenh_thi_KEU():
    ma, td = canh_cong_c5.kiem_ro_ri(
        [_qd(0, _MOC_DONG + 100), _qd(1, _MOC_DONG + 200, "STB")],
        cong_dang_mo=False, moc=_MOC_DONG, ngay_dong=pt.NGAY_DONG_CONG_C5)
    assert ma == 1, td
    assert "RÒ RỈ" in td and "STB" in td, td
    print("PASS  cổng đóng + 1 quyết định vào lệnh -> kêu, nêu tên mã")


def test_khong_ro_ri_thi_IM_va_NOI_RA_da_doi_chieu():
    """Im lặng phải phân biệt được với chưa kiểm — nên nó nói ra con số."""
    ma, td = canh_cong_c5.kiem_ro_ri(
        [_qd(0, _MOC_DONG + 100), _qd(0, _MOC_DONG + 200)],
        cong_dang_mo=False, moc=_MOC_DONG, ngay_dong=pt.NGAY_DONG_CONG_C5)
    assert ma == 0, td
    assert "0 quyết định vào lệnh" in td and "2 quyết định" in td, td
    print("PASS  không rò rỉ -> im, và nói rõ đã đối chiếu bao nhiêu dòng")


def test_lenh_mo_TRUOC_khi_dong_cong_KHONG_lam_keu_oan():
    """113 lệnh cũ mở hồi cổng còn mở — kêu vì chúng là dạy bỏ qua chuông."""
    ma, td = canh_cong_c5.kiem_ro_ri(
        [_qd(1, _MOC_DONG - 86400 * 30), _qd(1, _MOC_DONG - 1)],
        cong_dang_mo=False, moc=_MOC_DONG, ngay_dong=pt.NGAY_DONG_CONG_C5)
    assert ma == 0, td
    print("PASS  quyết định trước mốc đóng -> không kêu oan")


def test_cong_dang_MO_thi_khong_co_gi_de_doi_chieu():
    ma, td = canh_cong_c5.kiem_ro_ri(
        [_qd(1, _MOC_DONG + 500)], cong_dang_mo=True, moc=_MOC_DONG,
        ngay_dong=pt.NGAY_DONG_CONG_C5)
    assert ma == 0 and "đang MỞ" in td, td
    print("PASS  cổng mở -> không đối chiếu, không kêu")


def test_fill_pending_KHONG_ghi_quyet_dinh():
    """Nền móng của phép kiểm trên: lệnh chờ khớp không sinh `acted = 1`.

    Đọc từ cây cú pháp chứ không tin chú thích. Ngày nào `fill_pending`
    bắt đầu ghi quyết định thì lệnh chờ lúc khớp sẽ làm chuông kêu oan,
    và phép kiểm này đỏ TRƯỚC khi điều đó xảy ra trên sổ thật.

    Bản trước viết "bốn lệnh chờ khớp sáng 31/08" như một việc đã rồi.
    SAI — đo 02/09/2026 cả bốn vẫn `PENDING`, vì không có phiên nào sau
    28/08 (BƯỚC 11). Tính chất bị khoá ở đây vì thế CHƯA từng được thử
    trên sổ thật, và đó đúng là lý do phải khoá bằng AST: một tính chất
    chưa bao giờ được quan sát thì không có quan sát nào canh nó.
    """
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    ham = [n for n in ast.walk(cay)
           if isinstance(n, ast.FunctionDef) and n.name == "fill_pending"]
    assert len(ham) == 1, f"thấy {len(ham)} hàm fill_pending"
    goi = {n.func.attr for n in ast.walk(ham[0])
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "record_decision" not in goi, (
        "fill_pending nay CÓ ghi quyết định — kiem_ro_ri sẽ kêu oan mỗi "
        "lần một lệnh chờ khớp dưới cổng đóng")
    print("PASS  fill_pending không ghi quyết định")


def test_moc_dong_cong_dung_mui_gio_VN():
    """Lệch 7 tiếng đủ để một quyết định sáng sớm rơi sai phía của mốc.

    Việt Nam là UTC+7 quanh năm, không có giờ mùa hè — nên 00:00 ngày
    29/08 giờ VN phải là 17:00 ngày 28/08 giờ UTC. Kiểm bằng sự thật đó
    chứ không dựng lại cùng phép tính của mã nguồn.
    """
    moc = canh_cong_c5.moc_dong_cong("2026-08-29")
    utc = dt.datetime.fromtimestamp(moc, dt.timezone.utc)
    assert utc.strftime("%Y-%m-%d %H:%M") == "2026-08-28 17:00", utc
    print(f"PASS  mốc = {utc:%Y-%m-%d %H:%M} UTC = 00:00 ngày 29/08 giờ VN")


def test_ngay_dong_cong_la_hang_so_co_ten_khong_o_tuong_lai():
    ngay = dt.date.fromisoformat(pt.NGAY_DONG_CONG_C5)
    assert ngay <= dt.date.today(), (
        f"NGAY_DONG_CONG_C5 = {ngay} nằm ở tương lai — mốc đối chiếu như "
        f"vậy làm mọi rò rỉ lọt lưới")
    print(f"PASS  NGAY_DONG_CONG_C5 = {ngay}")


def test_chuong_THAT_SU_goi_kiem_ro_ri_va_dua_VAO_MA_THOAT():
    """Gọi mà không đưa vào mã thoát thì workflow vẫn xanh — chuông câm."""
    main = _ham_chuong("main")
    goi = {n.func.id for n in ast.walk(main)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "kiem_ro_ri" in goi, "main() không gọi kiem_ro_ri"
    assert "moc_dong_cong" in goi, "main() không dựng mốc đóng cổng"
    tra_ve = [n for n in ast.walk(main) if isinstance(n, ast.Return)]
    ten = {m.id for n in tra_ve for m in ast.walk(n)
           if isinstance(m, ast.Name)}
    assert "ma_rr" in ten, (
        "kết quả đối chiếu rò rỉ không đi vào mã thoát của main()")
    print("PASS  main() gọi kiem_ro_ri và đưa kết quả vào mã thoát")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
