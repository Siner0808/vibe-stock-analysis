"""Gác dụng cụ đo độ trễ khớp lệnh — và gác cả ba chỗ hiển thị nó.

`docs/STATE.md` BƯỚC 17 ghi độ trễ khớp lệnh là "biến không ai đo": cả
`signal_date` lẫn `entry_date` đều được lưu, nên độ trễ suy ra được từ
lâu, nhưng không dụng cụ nào đọc nó và **hai bảng gộp hai cột thành một**
(`entry_date or signal_date`) — che đúng khoảng cách ấy.

Bộ gác này canh bốn thứ, và thứ tư là thứ dễ mục ruỗng nhất:

1. Năm trạng thái tách bạch. Ba trong số đó là "chưa kết luận được" và
   chúng KHÁC NHAU — gộp lại là mất thông tin cần để biết phải sửa gì.
2. Ngưỡng `TRE_CHUAN_PHIEN` không được nới. Nới lên 2 là hợp thức hoá
   đúng thứ dụng cụ sinh ra để bắt.
3. Cột gộp KHÔNG được quay lại. Kiểm bằng AST hình dạng biểu thức, không
   bằng `in` — xem CLAUDE.md, "Gác phải đọc AST, không đọc `in`".
4. Phép đo KHÔNG được lọc lệnh trễ ra. Viết lúc sổ mới có 4 lệnh
   tiến-về-trước và 0 kết quả đã đóng, tức TRƯỚC khi nhìn thấy lệnh trễ
   nào lãi hay lỗ. Lọc sau khi đã thấy số là bất biến 7 đổi hướng.
"""
import ast
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import do_tre_khop as dtk           # noqa: E402
import paper_metrics as pm          # noqa: E402
from paper_trading import Trade     # noqa: E402


def _lenh(i, ma, tin_hieu, khop, trang_thai="OPEN", gia=13250.0,
          ra=None, gia_ra=None):
    goc = gia or 13250.0
    return Trade(
        id=i, symbol=ma, signal_date=tin_hieu, entry_date=khop,
        entry_price=gia, exit_date=ra, exit_price=gia_ra, exit_reason=None,
        stop_loss=goc * 0.93, take_profit=goc * 1.10, size_pct=25.0,
        entry_score=64, status=trang_thai, created_at=1.0e9)


# ── 1. Năm trạng thái ────────────────────────────────────────────────

#: Mỗi hàng là một trường hợp CÓ THẬT hoặc dựng được từ lịch 2026.
#: 28/08 → 03/09 là bốn lệnh thật đầu tiên của dự án: 31/08, 01/09 và
#: 02/09 nghỉ Quốc khánh, nên T+1 theo lịch phiên là 03/09 — đếm bằng
#: ngày làm việc sẽ ra 4 và kết luận sai.
CAC_CA = [
    ("bốn lệnh thật", "2026-08-28", "2026-09-03", dtk.DUNG_HAN, 1),
    ("trượt một phiên", "2026-08-28", "2026-09-04", dtk.TRE, 2),
    ("trượt cả tuần", "2026-08-28", "2026-09-09", dtk.TRE, 5),
    ("chưa khớp", "2026-08-28", None, dtk.CHUA_KHOP, None),
    ("ngoài phạm vi lịch", "2025-06-01", "2025-06-02", dtk.NGOAI_LICH, None),
    ("khớp vào thứ Bảy", "2026-09-04", "2026-09-05", dtk.MAU_THUAN, 0),
    ("khớp mà không tín hiệu", None, "2026-09-03", dtk.MAU_THUAN, None),
]


@pytest.mark.parametrize("ten,tin,khop,cho_doi,so_cho_doi", CAC_CA)
def test_nam_trang_thai(ten, tin, khop, cho_doi, so_cho_doi):
    tt, n = dtk.trang_thai_khop(tin, khop)
    assert tt == cho_doi, f"{ten}: ra {tt}, mong {cho_doi}"
    assert n == so_cho_doi, f"{ten}: đếm {n}, mong {so_cho_doi}"


def test_NGOAI_LICH_khong_duoc_gop_vao_DUNG_HAN():
    """Lịch hết hạn mà báo "đúng hạn" thì tệ hơn không có dụng cụ.

    `lich_giao_dich` chỉ phủ 2026. Sang 2027 mà chưa ai cập nhật bảng thì
    MỌI lệnh rơi vào nhánh này — nếu nó trả `DUNG_HAN` thì cả năm sau im
    lặng, và im lặng ấy trông y hệt "mọi thứ đều ổn".
    """
    tt, n = dtk.trang_thai_khop("2027-03-01", "2027-03-02")
    assert tt == dtk.NGOAI_LICH
    assert tt != dtk.DUNG_HAN
    assert n is None, "không đếm được thì phải trả None, không được trả 0"


def test_khong_dem_duoc_thi_KHONG_bia_so():
    """`so_phien` là `None` ở mọi trạng thái không đếm được.

    Trả 0 thay cho "chưa biết" là bịa một con số, và con số ấy đi thẳng
    vào bảng thống kê rồi thành "0 lệnh trễ".
    """
    for tt_ten, tin, khop in [("chưa khớp", "2026-09-03", None),
                              ("ngoài lịch", "2024-01-05", "2024-01-08")]:
        tt, n = dtk.trang_thai_khop(tin, khop)
        assert n is None, f"{tt_ten}: trả {n} thay vì None (trạng thái {tt})"


# ── 2. Ngưỡng ────────────────────────────────────────────────────────

def test_TRE_CHUAN_PHIEN_khong_duoc_noi():
    """Bất biến 1: vào lệnh ở giá mở cửa phiên T+1. Con số là 1.

    Nới lên 2 làm mọi lệnh trượt một phiên thành "đúng hạn" — một cách
    lặng lẽ để dụng cụ này không bao giờ kêu nữa. Ghim cả HẰNG SỐ lẫn
    HÀNH VI: hằng số bắt kẻ sửa thẳng, hành vi bắt kẻ sửa đường vòng.
    """
    assert dtk.TRE_CHUAN_PHIEN == 1
    tt, n = dtk.trang_thai_khop("2026-08-28", "2026-09-04")
    assert (tt, n) == (dtk.TRE, 2), "T+2 phải là TRỄ, không phải đúng hạn"


def test_nhan_cua_ba_trang_thai_khong_dem_duoc_phai_KHAC_NHAU():
    """Ba dấu "—", "?", "!" là bản hiển thị của ba trạng thái khác nhau.

    Cho chúng dùng chung một ký tự là gộp ba trạng thái ở tầng mà người
    đọc thật sự nhìn — tức là gộp thật, dù mã bên dưới vẫn tách.
    """
    nhan = {tt: dtk.nhan_tre(tt, None)
            for tt in (dtk.CHUA_KHOP, dtk.NGOAI_LICH, dtk.MAU_THUAN)}
    assert len(set(nhan.values())) == 3, f"nhãn trùng nhau: {nhan}"


# ── 3. Tổng hợp và báo cáo ───────────────────────────────────────────

def _so_hon_hop():
    return [
        _lenh(1, "HUT", "2026-08-28", "2026-09-03"),
        _lenh(2, "NAF", "2026-08-28", "2026-09-03"),
        _lenh(3, "STB", "2026-08-28", "2026-09-04"),
        _lenh(4, "TCB", "2026-09-03", None, trang_thai="PENDING", gia=None),
        _lenh(5, "OLD", "2025-05-02", "2025-05-05", trang_thai="CLOSED",
              ra="2025-06-02", gia_ra=14000.0),
    ]


def test_tom_tat_dem_dung_tung_nhom():
    tt = dtk.tom_tat(_so_hon_hop())
    assert tt["dem"][dtk.DUNG_HAN] == 2
    assert tt["dem"][dtk.TRE] == 1
    assert tt["dem"][dtk.CHUA_KHOP] == 1
    assert tt["dem"][dtk.NGOAI_LICH] == 1
    assert tt["dem"][dtk.MAU_THUAN] == 0
    assert tt["so_lenh"] == 5, "tổng các nhóm phải bằng số lệnh đưa vào"
    assert tt["tre_lon_nhat"] == 2
    assert [d["symbol"] for d in tt["tre"]] == ["STB"]


def test_bao_cao_IM_LANG_khi_moi_lenh_dung_han():
    """Không có gì bất thường thì không được thêm chữ.

    Một cảnh báo kêu mọi phiên là một cảnh báo không ai đọc.
    """
    dung_han = [_lenh(1, "HUT", "2026-08-28", "2026-09-03"),
                _lenh(2, "NAF", "2026-08-28", "2026-09-03")]
    assert dtk.dong_bao_cao(dtk.tom_tat(dung_han)) == []


def test_bao_cao_NOI_RA_khi_co_lenh_tre():
    dong = "\n".join(dtk.dong_bao_cao(dtk.tom_tat(_so_hon_hop())))
    assert "STB" in dong, "lệnh trễ phải được gọi tên, không chỉ đếm"
    assert "T+2" in dong
    assert "2026-09-04" in dong


def test_bao_cao_NOI_RA_khi_so_mau_thuan():
    so = [_lenh(9, "XXX", "2026-09-04", "2026-09-05")]
    dong = "\n".join(dtk.dong_bao_cao(dtk.tom_tat(so)))
    assert dong, "sổ mâu thuẫn mà báo cáo im là mất đúng thứ cần biết"
    assert "XXX" in dong


def test_report_hien_ca_bang_tach_cot_lan_canh_bao():
    """Đo trên đầu ra THẬT của `paper_metrics.report`, không đọc mã."""
    ra = pm.report(_so_hon_hop())
    assert "TÍN HIỆU" in ra and "KHỚP" in ra, "bảng chưa tách hai cột ngày"
    assert "T+2" in ra, "cột trễ không hiện trong bảng vị thế"
    assert dtk.CHU_GIAI in ra, (
        "có ô '?' và '!' mà không có chú giải thì hai ký tự đó vô nghĩa")
    assert "STB" in ra
    # Ngày tín hiệu của lệnh còn chờ phải hiện Ở CỘT TÍN HIỆU, và cột
    # khớp phải để trống — chứ không mượn ngày tín hiệu làm ngày vào.
    assert "2026-09-03 | —" in ra, "lệnh PENDING vẫn đang mượn ngày tín hiệu"


def test_report_PHAT_RA_canh_bao_chu_khong_chi_in_bang():
    """Khối cảnh báo phải có mặt trong `report()`, không chỉ trong bảng.

    Bảng vị thế đã in "T+2" và "STB" rồi, nên một test tìm hai chuỗi ấy
    sẽ VẪN XANH sau khi khối cảnh báo bị gỡ khỏi `report()` — đúng hình
    dạng "test kiểm lại chính nó" ghi ở CLAUDE.md. Phải bắt bằng câu chỉ
    khối cảnh báo mới nói.
    """
    ra = pm.report(_so_hon_hop())
    assert "ĐỘ TRỄ KHỚP LỆNH" in ra, (
        "khối cảnh báo độ trễ không còn được gọi trong report()")
    rieng = [d for d in dtk.dong_bao_cao(dtk.tom_tat(_so_hon_hop()))
             if "MUỘN" in d]
    assert rieng and rieng[0] in ra, (
        "report() không phát ra đúng câu mà dong_bao_cao() dựng — hai nơi "
        "đang nói hai chuyện khác nhau về cùng một lệnh")


def test_report_KHONG_them_chu_khi_moi_lenh_dung_han():
    """Chiều ngược lại: không có gì trễ thì không được có khối cảnh báo."""
    ra = pm.report([_lenh(1, "HUT", "2026-08-28", "2026-09-03"),
                    _lenh(2, "NAF", "2026-08-28", "2026-09-03")])
    assert "ĐỘ TRỄ KHỚP LỆNH" not in ra


# ── 3b. Đồng đều hay rải rác — hai nguyên nhân, một bảng đếm ─────────

def _tre(ma, tin, khop):
    return _lenh(hash(ma) % 1000, ma, tin, khop)


def test_TOI_THIEU_DE_NOI_DONG_DEU_khong_duoc_ha():
    """Hạ xuống 1 thì mọi tập một phần tử đều "đồng đều" — vô nghĩa."""
    assert dtk.TOI_THIEU_DE_NOI_DONG_DEU == 3


def test_tre_DONG_DEU_thi_chi_dung_stride_chu_khong_do_loi_cron():
    """Hình dạng thật của sổ ngày 04/09/2026: 43 lệnh, tất cả T+2.

    Nhịp cron rơi ngẫu nhiên KHÔNG thể cho ra một hằng số. Bản đầu của
    dụng cụ này khẳng định thẳng nguyên nhân là cron, và số liệu thật
    bác sạch ngay lần chạy đầu tiên.
    """
    so = [_tre("AAA", "2026-01-07", "2026-01-09"),
          _tre("BBB", "2026-01-09", "2026-01-13"),
          _tre("CCC", "2026-01-13", "2026-01-15"),
          _tre("DDD", "2026-03-03", "2026-03-05")]
    tt = dtk.tom_tat(so)
    assert tt["tre_dong_deu"] is True
    assert tt["cac_muc_tre"] == [2]

    dong = "\n".join(dtk.dong_bao_cao(tt))
    assert "ĐỒNG ĐỀU" in dong
    assert "stride" in dong, "không chỉ ra chỗ phải đi xem thì báo để làm gì"
    assert "cron" not in dong.lower(), (
        "vẫn đổ cho cron trong khi độ trễ là hằng số — đúng câu sai mà "
        "số liệu thật đã bác ngày 04/09/2026")


def test_tre_RAI_RAC_thi_moi_hop_voi_nhip_quet_roi():
    so = [_tre("AAA", "2026-01-07", "2026-01-09"),      # T+2
          _tre("BBB", "2026-01-07", "2026-01-13"),      # T+4
          _tre("CCC", "2026-01-07", "2026-01-15")]      # T+6
    tt = dtk.tom_tat(so)
    assert tt["tre_dong_deu"] is False
    assert tt["cac_muc_tre"] == [2, 4, 6]
    dong = "\n".join(dtk.dong_bao_cao(tt))
    assert "RẢI RÁC" in dong
    assert "cron" in dong.lower()


def test_CHUA_DU_MAU_khong_duoc_gop_vao_ben_nao():
    """Trạng thái thứ ba, y như mọi phép đo khác của dự án.

    Hai lệnh trễ giống nhau là chuyện thường; gọi đó là "đồng đều" rồi
    chỉ tay sang `stride` là kết luận vượt quá dữ liệu.
    """
    so = [_tre("AAA", "2026-01-07", "2026-01-09"),
          _tre("BBB", "2026-01-09", "2026-01-13")]
    tt = dtk.tom_tat(so)
    assert tt["tre_dong_deu"] is None, "2 lệnh mà đã dám kết luận"
    dong = "\n".join(dtk.dong_bao_cao(tt))
    assert "Chưa đủ" in dong
    assert "ĐỒNG ĐỀU" not in dong and "RẢI RÁC" not in dong


def test_CO_CHE_sinh_ra_T2_la_buoc_nhay_chu_khong_phai_thu_tu_trong_phien():
    """Chứng minh cơ chế, không chỉ suy từ đọc mã.

    `run_session` gọi `fill_pending` TRƯỚC `consider_entry`, nên lệnh
    sinh ở phiên t khớp ở **phiên kế tiếp ĐƯỢC GHÉ**. Ghé từng phiên
    (stride=1) cho T+1; ghé cách phiên (stride=2) cho T+2 — cùng một mã,
    khác duy nhất tập phiên được mô phỏng.
    """
    import tempfile
    from paper_trading import PaperTradingJournal, Status

    phien = ["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08",
             "2026-01-09"]

    def khop_voi_buoc(buoc: int) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            so = PaperTradingJournal(str(Path(tmp) / "t.db"))
            try:
                so.db.execute(
                    "INSERT INTO trades (symbol, exchange, signal_date,"
                    " entry_date, entry_price, stop_loss, take_profit,"
                    " size_pct, entry_score, status)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?)",
                    ("AAA", "HOSE", phien[0], None, None, 9300.0, 11000.0,
                     25.0, 64, Status.PENDING))
                so.db.commit()
                for p in phien[buoc::buoc]:
                    so.fill_pending("AAA", p, 10000.0)
                r = so.db.execute(
                    "SELECT entry_date FROM trades").fetchone()
                return r["entry_date"]
            finally:
                so.db.close()

    khop1, khop2 = khop_voi_buoc(1), khop_voi_buoc(2)
    assert dtk.trang_thai_khop(phien[0], khop1) == (dtk.DUNG_HAN, 1), (
        f"ghé từng phiên phải cho T+1, ra {khop1}")
    assert dtk.trang_thai_khop(phien[0], khop2) == (dtk.TRE, 2), (
        f"ghé cách phiên phải cho T+2, ra {khop2}")


# ── 4. Cột gộp không được quay lại (AST) ─────────────────────────────

#: Ba nơi hiển thị. Sàn: phải quét đủ CẢ BA. Một máy quét không nói ra
#: nó quét được bao nhiêu file là một máy quét có thể đang quét 0 file —
#: bẫy đã sập ngày 03/09/2026 ở `tests/test_chi_dan_chay_duoc.py`.
NOI_HIEN_THI = ("paper_metrics.py", "run_daily.py", "app.py")

#: Hai tên trường mà việc đặt cạnh nhau bằng `or` chính là lỗi.
TEN_NGAY = {"entry_date", "signal_date"}


def test_NOI_HIEN_THI_khong_duoc_thu_hep_am_tham():
    """Bỏ bớt một file khỏi danh sách là gỡ gác cho file đó.

    Cả hai gác AST bên dưới đều lặp trên đúng bộ này, nên rút nó xuống
    còn một file làm hai gác cùng teo lại mà vẫn xanh — cùng hình dạng
    với `SAN_SO_FILE = 0` sống sót đột biến ngày 03/09/2026.
    """
    assert set(NOI_HIEN_THI) == {"paper_metrics.py", "run_daily.py",
                                 "app.py"}, (
        "ba nơi hiển thị vị thế đã đổi — sửa danh sách này CÓ CHỦ ĐÍCH, "
        "kèm lý do, chứ đừng rút gọn cho test xanh")


def _ten_ngay_trong(nut) -> set:
    """Tên trường ngày mà biểu thức này đọc — cả `t.x` lẫn `d["x"]`."""
    ra = set()
    for n in ast.walk(nut):
        if isinstance(n, ast.Attribute) and n.attr in TEN_NGAY:
            ra.add(n.attr)
        elif isinstance(n, ast.Subscript):
            s = n.slice
            if isinstance(s, ast.Constant) and s.value in TEN_NGAY:
                ra.add(s.value)
    return ra


def _cho_gop(cay) -> list[int]:
    """Dòng của mọi biểu thức lấy ngày này THAY CHO ngày kia.

    Bắt cả `a or b` lẫn `a if … else b`: hai cách viết, một lỗi. Chỉ kêu
    khi HAI NHÁNH KHÁC NHAU đọc hai trường khác nhau — nên
    `d["entry_date"] or "—"` (lùi về gạch ngang) không bị kêu, vì gạch
    ngang không giả làm một ngày.
    """
    ra = []
    for n in ast.walk(cay):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            nhanh = [_ten_ngay_trong(v) for v in n.values]
        elif isinstance(n, ast.IfExp):
            nhanh = [_ten_ngay_trong(n.body), _ten_ngay_trong(n.orelse)]
        else:
            continue
        if set().union(*nhanh) >= TEN_NGAY and not any(
                x >= TEN_NGAY for x in nhanh):
            ra.append(n.lineno)
    return ra


#: Ba cách viết CÙNG một lỗi, và một cách viết KHÔNG phải lỗi. Máy dò
#: phải phân biệt được cả bốn — nếu không thì câu "0 vi phạm" của nó
#: không mang thông tin gì.
MAU_XAU = [
    ("thuộc tính", "x = t.entry_date or t.signal_date"),
    ("khoá dict", "x = d['entry_date'] or d['signal_date']"),
    ("ba ngôi", "x = t.entry_date if t.entry_date else t.signal_date"),
    ("đảo thứ tự", "x = t.signal_date or t.entry_date"),
    ("lồng trong f-string", "x = f\"{t.entry_date or t.signal_date}\""),
]
MAU_TOT = [
    ("lùi về gạch ngang", "x = d['entry_date'] or '—'"),
    ("hai cột riêng", "x = (t.signal_date, t.entry_date)"),
    ("chờ mở cửa", "x = t.entry_price or 'Chờ mở cửa'"),
]


@pytest.mark.parametrize("ten,src", MAU_XAU)
def test_may_do_BAT_DUOC_mau_xau(ten, src):
    """Không có test này thì `_cho_gop` biến thành `return []` vẫn xanh.

    Mã thật hiện không vi phạm, nên một máy dò HỎNG trả về đúng cùng
    câu trả lời với một máy dò TỐT — cùng hình dạng với đột biến "đổi
    khai báo mà không đổi con số nào" ngày 03/09/2026. Cách duy nhất
    tách hai trường hợp là bắt máy dò làm việc trên một mẫu đã biết là
    xấu. Cùng cách `tools/kiem_cu_phap_311.py` tự kiểm mình bằng một
    đoạn cú pháp 3.12 trước khi kiểm repo.
    """
    assert _cho_gop(ast.parse(src)), f"máy dò bỏ lọt: {ten} — {src}"


@pytest.mark.parametrize("ten,src", MAU_TOT)
def test_may_do_KHONG_keu_oan(ten, src):
    """Một gác kêu oan sẽ bị vô hiệu bằng ngoại lệ, rồi mục ruỗng."""
    assert not _cho_gop(ast.parse(src)), f"kêu oan: {ten} — {src}"


def test_KHONG_noi_nao_gop_lai_hai_cot_ngay():
    quet = 0
    loi = []
    for ten in NOI_HIEN_THI:
        f = GOC / ten
        assert f.exists(), f"{ten} biến mất — gác này đang canh chỗ trống"
        src = f.read_text(encoding="utf-8")
        assert "entry_date" in src, (
            f"{ten} không còn nhắc entry_date; nếu bảng vị thế đã dời đi "
            f"thì sửa NOI_HIEN_THI, đừng để gác canh nhầm file")
        quet += 1
        for dong in _cho_gop(ast.parse(src)):
            loi.append(f"{ten}:{dong}")
    assert quet == len(NOI_HIEN_THI), f"chỉ quét được {quet} file"
    assert not loi, (
        "cột gộp đã quay lại ở " + ", ".join(loi) +
        " — `entry_date or signal_date` làm lệnh chờ hiện ngày TÍN HIỆU "
        "như thể đó là ngày vào. Xem docs/STATE.md, BƯỚC 17.")


def test_ba_noi_hien_thi_deu_GOI_dung_cu(monkeypatch):
    """Khai báo import chưa đủ — phải thấy LỜI GỌI trong cây cú pháp."""
    for ten in NOI_HIEN_THI:
        cay = ast.parse((GOC / ten).read_text(encoding="utf-8"))
        nhap, goi = set(), set()
        for n in ast.walk(cay):
            if isinstance(n, ast.Import):
                for a in n.names:
                    nhap.add(a.asname or a.name.split(".")[0])
            elif isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Attribute):
                    goi.add(f.attr)
                elif isinstance(f, ast.Name):
                    goi.add(f.id)
        assert "do_tre_khop" in nhap or "_dtk" in nhap, (
            f"{ten} hiện cột 'Trễ' mà không nhập do_tre_khop")
        assert "do_mot_lenh" in goi, (
            f"{ten} nhập do_tre_khop nhưng không gọi do_mot_lenh — "
            f"cột trễ đang được tính ở đâu?")


# ── 5. Quyết định khai TRƯỚC: không lọc lệnh trễ ─────────────────────

def test_phep_do_KHONG_duoc_loc_lenh_tre():
    """Lệnh khớp muộn VẪN được tính vào mọi con số.

    Khai lúc sổ có 4 lệnh tiến-về-trước và 0 kết quả đã đóng — tức trước
    khi biết lệnh trễ lãi hay lỗ. Loại chúng ra sau khi đã thấy số là
    chọn tập mẫu theo kết quả, tức bất biến 7 đổi hướng.

    Nguyên nhân trễ (cron GitHub rơi nhịp) độc lập với mã cổ phiếu, nên
    loại chúng KHÔNG sửa được thiên lệch nào — nó chỉ làm cỡ mẫu nhỏ đi
    ở đúng dự án mà cỡ mẫu là ràng buộc chặt nhất.
    """
    dung_han = [_lenh(1, "AAA", "2026-08-28", "2026-09-03",
                      trang_thai="CLOSED", ra="2026-10-01", gia_ra=14000.0)]
    tre = [_lenh(1, "AAA", "2026-08-28", "2026-09-09",
                 trang_thai="CLOSED", ra="2026-10-01", gia_ra=14000.0)]

    assert dtk.trang_thai_khop("2026-08-28", "2026-09-09")[0] == dtk.TRE
    a, b = pm.compute(dung_han), pm.compute(tre)
    assert a is not None and b is not None
    assert a.n_trades == b.n_trades == 1, (
        "lệnh trễ đã bị loại khỏi `compute` — dụng cụ đo được phép NÓI, "
        "không được phép LOẠI")
    assert (len(pm.lenh_tien_ve_truoc(dung_han))
            == len(pm.lenh_tien_ve_truoc(tre)) == 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_do_tre_khop.py -q")
