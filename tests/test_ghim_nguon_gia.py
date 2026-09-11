"""`fetch_one` phải GHIM được nguồn — hai nguồn là hai hệ số điều chỉnh.

VÌ SAO CÓ FILE NÀY
──────────────────
`fetch_one` thử lần lượt `kbs → tcbs → vci → dnse` và lấy cái đầu tiên
có dữ liệu. Nó **không ghi lại nguồn nào đã trả lời**.

Lượt kéo `backtest/cache_2018/` ngày 11/09/2026: 123 mã từ `kbs`, **2 mã
từ `vci`** (HT1, TCH). Không vì `kbs` thiếu — hỏi lại sau đó, `kbs` trả
đủ 1.995 phiên cho cả hai. Một lần hỏng tạm thời, im lặng.

Và giá hai nguồn **không bằng nhau**:

    TCH  1988/1995 dong lech · ty le vci/kbs TB 0,9971
    HT1   116/1995 dong lech · TB 0,99998
    FPT  1499/1995 dong lech · TB 0,99966

Phần lớn là một hệ số gần đều nên triệt tiêu trong lợi nhuận, nhưng
không đều tuyệt đối. **Một rổ trộn hai nguồn là một rổ trộn hai hệ số**,
và không ai biết vì hàm im lặng.

Cùng họ lỗi 30: thứ gây hại không phải việc rơi nguồn, mà việc rơi nguồn
KHÔNG ĐƯỢC HỎI.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

from backtest import data as bt_data  # noqa: E402


class _QuoteGia:
    """Quote giả, ghi lại MỌI nguồn được hỏi. Không chạm mạng."""

    da_hoi: list[str] = []
    co_du_lieu: set[str] = set()

    def __init__(self, symbol: str, source: str):
        self.source = source
        _QuoteGia.da_hoi.append(source)

    def history(self, start: str, end: str):
        import pandas as pd
        if self.source not in _QuoteGia.co_du_lieu:
            return pd.DataFrame()
        return pd.DataFrame({"time": ["2020-01-02"], "close": [10.0]})


def _dung_quote_gia(monkeypatch, co_du_lieu: set[str]):
    import types
    _QuoteGia.da_hoi = []
    _QuoteGia.co_du_lieu = co_du_lieu
    gia = types.ModuleType("vnstock")
    gia.Quote = _QuoteGia
    monkeypatch.setitem(sys.modules, "vnstock", gia)
    monkeypatch.setattr(bt_data.time, "sleep", lambda *_: None)


def test_MAC_DINH_giu_nguyen_hanh_vi_cu(monkeypatch):
    """Không truyền `nguon` thì thử đúng thứ tự cũ, lấy cái đầu có dữ liệu."""
    _dung_quote_gia(monkeypatch, {"vci"})
    df = bt_data.fetch_one("TCH", "2018-01-01", "2026-09-11")
    assert df is not None and not df.empty
    assert _QuoteGia.da_hoi == ["kbs", "tcbs", "vci"], _QuoteGia.da_hoi
    print(f"PASS  mặc định: hỏi {_QuoteGia.da_hoi} rồi dừng ở nguồn có dữ liệu")


def test_GHIM_mot_nguon_thi_KHONG_roi_sang_nguon_khac(monkeypatch):
    """Ghim `kbs` mà `kbs` hỏng thì phải trả None, KHÔNG âm thầm lấy `vci`.

    Đây là cả lý do tham số này tồn tại: thà không có dữ liệu còn hơn có
    dữ liệu từ một hệ số khác mà không ai biết.
    """
    _dung_quote_gia(monkeypatch, {"vci"})
    df = bt_data.fetch_one("TCH", "2018-01-01", "2026-09-11", nguon="kbs")
    assert df is None, "ghim kbs mà vẫn rơi sang nguồn khác"
    assert _QuoteGia.da_hoi == ["kbs"], _QuoteGia.da_hoi
    print("PASS  ghim một nguồn: chỉ hỏi nguồn ấy, hỏng thì trả None")


def test_GHIM_nguon_CO_du_lieu_thi_lay_duoc(monkeypatch):
    _dung_quote_gia(monkeypatch, {"kbs", "vci"})
    df = bt_data.fetch_one("FPT", "2018-01-01", "2026-09-11", nguon="vci")
    assert df is not None and not df.empty
    assert _QuoteGia.da_hoi == ["vci"], _QuoteGia.da_hoi
    print("PASS  ghim nguồn có dữ liệu: lấy đúng nguồn ấy, không hỏi nguồn nào khác")


def test_GHIM_mot_DANH_SACH_nguon(monkeypatch):
    """Cho phép một danh sách hẹp, vẫn chặn hơn mặc định bốn nguồn."""
    _dung_quote_gia(monkeypatch, {"dnse"})
    df = bt_data.fetch_one("X", "2018-01-01", "2026-09-11",
                           nguon=("kbs", "vci"))
    assert df is None
    assert _QuoteGia.da_hoi == ["kbs", "vci"], _QuoteGia.da_hoi
    print("PASS  ghim danh sách: chỉ hỏi trong danh sách ấy")


def test_DANH_SACH_MAC_DINH_van_la_bon_nguon_quen_thuoc():
    """Đổi thứ tự nguồn là đổi hệ số điều chỉnh của cả rổ — phải cố ý."""
    assert bt_data.NGUON_MAC_DINH == ("kbs", "tcbs", "vci", "dnse"), (
        f"thứ tự nguồn mặc định đã đổi: {bt_data.NGUON_MAC_DINH}\n"
        "Đổi thứ tự là đổi nguồn trả lời cho những mã mà nguồn đầu hỏng, "
        "tức đổi hệ số điều chỉnh của chúng. Đọc `docs/STATE.md` BƯỚC 53.")
    print(f"PASS  thứ tự nguồn mặc định: {bt_data.NGUON_MAC_DINH}")
