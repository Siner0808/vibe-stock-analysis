"""Bộ nhớ phải có HAI trục thời gian, không phải một.

VÌ SAO
`get_penalty_for_pattern` chỉ có một hàng rào: `signal_date < as_of`. Nó
chống nhìn trộm tương lai, và nó làm đúng việc đó.

Nhưng nó KHÔNG đủ để `save_memory()` bật lại an toàn. Xét một lệnh có tín
hiệu ngày 2026-01-05 và đóng bằng cắt lỗ ngày 2026-08-20:

    signal_date = 2026-01-05   → nhỏ hơn as_of 2026-08-20 → LỌT hàng rào
    nhưng mẫu này chỉ TỒN TẠI từ 2026-08-20

Nên trong chính phiên quét 20/08, mã A đóng bằng cắt lỗ sẽ làm lệch điểm
của mã B — cùng input, hai lần chạy khác thứ tự cho hai kết quả. Đó đúng là
sự cố 47-vs-59, và đó là lý do `save_memory()` không được gọi ở đâu cả:
bất biến 2 đang được giữ NHỜ TAI NẠN.

TRỤC THỨ HAI
Mỗi mẫu mang thêm `phien_hoc` — phiên mà nó trở nên biết được (ngày lệnh
đóng). Chấm điểm chỉ dùng mẫu có `phien_hoc` NHỎ HƠN phiên đang chấm.

Cùng hình dạng với bất biến 3: "dời stop về hoà vốn chỉ có hiệu lực từ
phiên sau, vì lệnh dời stop chỉ đặt được sau khi đã thấy giá chạm mốc."
"""
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import post_mortem_learning as pml

BD = {"trend_score": 65, "momentum_score": 60, "volume_score": 55}


def _may(mau):
    d = tempfile.mkdtemp()
    e = pml.PostMortemLearningEngine(str(Path(d) / "m.json"), enabled=True)
    e.sl_patterns = mau
    return e


def _mau(signal_date, phien_hoc):
    return {"symbol": "AAA", "signal_date": signal_date, "entry_score": 60,
            "trend_score": 65, "momentum_score": 60, "volume_score": 55,
            "nguon": "test", "trade_id": 1, "phien_hoc": phien_hoc}


def test_mau_hoc_TRONG_phien_KHONG_duoc_anh_huong_chinh_phien_do():
    """Đây là cơ chế 47-vs-59, viết ra thành một test."""
    e = _may([_mau(signal_date="2026-01-05", phien_hoc="2026-08-20")])
    phat = e.get_penalty_for_pattern(BD, as_of="2026-08-20",
                                     phien_hien_tai="2026-08-20")
    assert phat == 0.0, (
        f"mẫu vừa học trong phiên 2026-08-20 đã trừ {phat} điểm của chính "
        f"phiên đó — cùng input sẽ ra hai kết quả tuỳ thứ tự quét")
    print("PASS  mẫu học trong phiên không ảnh hưởng chính phiên đó")


def test_mau_do_CO_hieu_luc_tu_phien_sau():
    e = _may([_mau(signal_date="2026-01-05", phien_hoc="2026-08-20")])
    phat = e.get_penalty_for_pattern(BD, as_of="2026-08-21",
                                     phien_hien_tai="2026-08-21")
    assert phat == pml.PENALTY, f"phiên sau vẫn không áp dụng: {phat}"
    print("PASS  mẫu đó có hiệu lực từ phiên sau")


def test_hang_rao_nhin_trom_VAN_con_nguyen():
    """Trục thứ hai là THÊM, không phải thay. Bất biến 1 không được lỏng đi."""
    e = _may([_mau(signal_date="2026-09-01", phien_hoc="2020-01-01")])
    phat = e.get_penalty_for_pattern(BD, as_of="2026-08-20",
                                     phien_hien_tai="2026-08-20")
    assert phat == 0.0, "mẫu có tín hiệu ở TƯƠNG LAI vẫn được dùng"
    print("PASS  hàng rào chống nhìn trộm còn nguyên")


def test_khong_truyen_phien_hien_tai_thi_van_chay_nhu_cu():
    """Giữ hành vi cũ cho những chỗ gọi chưa cập nhật."""
    e = _may([_mau(signal_date="2026-01-05", phien_hoc="2026-08-20")])
    assert e.get_penalty_for_pattern(BD, as_of="2026-08-20") == pml.PENALTY
    print("PASS  không truyền phien_hien_tai -> hành vi cũ")


def test_mau_thieu_phien_hoc_bi_BO_khi_co_truc_thu_hai():
    """Không biết học lúc nào thì không dùng được — fail-closed."""
    m = _mau(signal_date="2026-01-05", phien_hoc="2026-08-20")
    del m["phien_hoc"]
    e = _may([m])
    phat = e.get_penalty_for_pattern(BD, as_of="2026-08-21",
                                     phien_hien_tai="2026-08-21")
    assert phat == 0.0, "mẫu không rõ học lúc nào mà vẫn trừ điểm"
    print("PASS  mẫu thiếu phien_hoc bị bỏ khi có trục thứ hai")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()


# ── Bật save_memory: chỉ SỔ THẬT mới được ghi vào bộ nhớ ─────────────
def _dung_so(thu_muc, ten_file, bd):
    """Dựng một sổ có sẵn một lệnh sắp chạm cắt lỗ."""
    import json as _json
    import os

    import paper_trading as pt
    pt.CHO_PHEP_MO_LENH_MOI = True
    duong = os.path.join(thu_muc, ten_file)
    that = os.path.basename(duong) == os.path.basename(pt.DB_PATH)
    j = pt.PaperTradingJournal(duong, cho_phep_so_that=that)
    j.db.execute(
        "INSERT INTO trades (symbol, signal_date, entry_date, entry_price,"
        " exit_date, exit_price, exit_reason, status, stop_loss, take_profit,"
        " size_pct, entry_score, components, reasons)"
        " VALUES ('AAA','2026-01-05','2026-01-06',100,NULL,NULL,NULL,'OPEN',"
        " 95,120,10,70,?,'[]')", (_json.dumps(bd),))
    j.db.commit()
    return j


def _dong_lenh_va_dem(ten_file):
    """Đóng lệnh bằng cắt lỗ, trả về số mẫu ĐƯỢC GHI RA ĐĨA."""
    import json as _json
    import os

    import post_mortem_learning as _pml

    with tempfile.TemporaryDirectory() as d:
        bo_nho = os.path.join(d, "bo_nho.json")
        may = _pml.PostMortemLearningEngine(bo_nho, enabled=True)
        may.sl_patterns = []
        # Ghim thang HAM, khong ghim bien.
        # `def get_learning_engine(memory_file=MEMORY_FILE, ...)` gan gia tri
        # mac dinh LUC DINH NGHIA HAM, nen gan lai _pml.MEMORY_FILE sau do
        # khong co tac dung — ham van hoi dung file that, thay khac voi engine
        # trong cache, roi dung lai mot engine moi tro vao file that.
        cu_ham = _pml.get_learning_engine
        _pml.get_learning_engine = lambda *a, **k: may
        os.environ["POST_MORTEM_ENABLED"] = "1"
        try:
            j = _dung_so(d, ten_file, BD)
            j.evaluate_open("AAA", "2026-02-01",
                            {"open": 99.0, "high": 99.0, "low": 90.0,
                             "close": 91.0}, current_score=40)
            j.db.close()
        finally:
            _pml.get_learning_engine = cu_ham
            os.environ.pop("POST_MORTEM_ENABLED", None)

        tren_dia = _json.loads(open(bo_nho, encoding="utf-8").read()) \
            if os.path.exists(bo_nho) else []
        return len(may.sl_patterns), len(tren_dia)


def test_backtest_KHONG_duoc_ghi_vao_bo_nho_that():
    """Ba script optimize đặt POST_MORTEM_ENABLED=1. Nếu save_memory chạy cho
    cả sổ scratch thì backtest ghi thẳng vào bộ nhớ thật — đúng cơ chế đã đẻ
    ra khối 6.327 mẫu, trong đó 99,1% không ứng với lệnh thật nào."""
    trong_ram, tren_dia = _dong_lenh_va_dem("paper_scratch_backtest.db")
    assert trong_ram == 1, "không ghi nhận mẫu nào trong RAM"
    assert tren_dia == 0, (
        f"sổ scratch đã ghi {tren_dia} mẫu XUỐNG ĐĨA — backtest đang bồi "
        f"vào bộ nhớ thật")
    print("PASS  sổ scratch: ghi nhận trong RAM, KHÔNG ghi xuống đĩa")


def test_so_that_thi_bo_nho_duoc_luu_lai():
    trong_ram, tren_dia = _dong_lenh_va_dem("paper_trades.db")
    assert trong_ram == 1 and tren_dia == 1, (
        f"sổ thật mà không lưu bộ nhớ: RAM={trong_ram} đĩa={tren_dia}")
    print("PASS  sổ thật: mẫu được lưu xuống đĩa -> cơ chế học thật sự chạy")
