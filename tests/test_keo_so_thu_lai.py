"""Test bước kéo sổ lệnh có thử lại.

VÌ SAO CÓ FILE NÀY. 2/35 nhịp quét tự động (18/08 và 19/08/2026) chết ở
đúng bước kéo sổ, sau 2 giây, và hai bước sau bị "skipped" — nhịp đó
không quét gì cả. Thêm cơ chế thử lại thì phải chứng minh bốn điều, chứ
suy luận từ mã là chưa đủ:

  1. Một lần kéo HỎNG không để lại dấu vết trên sổ. Đây là điều kiện
     tiên quyết. Thiếu nó thì thử lại còn TỆ HƠN không thử: lần 1 xoá dở
     sổ, lần 2 gặp sổ đã có dữ liệu rồi bị chính gác chống ghi đè từ
     chối — lỗi nhất thời hoá lỗi vĩnh viễn.
  2. Thử lại thật sự cứu được lỗi nhất thời.
  3. KHÔNG thử lại khi kho ngoài chưa cấu hình — thử lại vô nghĩa, chỉ
     làm chậm nhịp quét.
  4. Thử hết vẫn hỏng thì NỔ, không trả None và không trả sổ rỗng. Quét
     tiếp trên sổ rỗng rồi đẩy lên là đúng cơ chế đã làm mất 96/113 lệnh
     ngày 12/08/2026.

Chạy offline, không cần mạng lẫn credential.

GHI CHÚ VỀ CÁCH DỰNG DỮ LIỆU. File này KHÔNG vá market_filter hay
paper_trading.CHO_PHEP_MO_LENH_MOI ở mức module như tests/test_sheets_store.py
làm. Vá mức module rò sang các file test chạy sau nó trong cùng phiên
pytest — đã mất một buổi vì đúng chuyện đó. Ở đây sheet được dựng thẳng
từ TRADE_COLS/DECISION_COLS nên không cần đụng tới hai module kia.
"""
import io
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google_sheets_sync as gs
import sheets_store as ss


# ─────────────────────────────────────────────────────────────────────
# Đồ dựng cảnh
# ─────────────────────────────────────────────────────────────────────

def _dong(cols: tuple, dat: dict) -> list:
    """Một dòng sheet: ô nào không nêu tên thì để rỗng (-> NULL)."""
    return [str(dat.get(c, "")) for c in cols]


def sheet_co_du_lieu() -> ss.InMemorySheet:
    """Sheet có đúng 1 lệnh và 1 quyết định — đủ để phân biệt với sổ rỗng."""
    sheet = ss.InMemorySheet()
    sheet.write_all(ss.TAB_TRADES, [
        list(ss.TRADE_COLS),
        _dong(ss.TRADE_COLS, {"id": 1, "symbol": "FPT", "status": "CLOSED",
                              "signal_date": "2026-01-05"}),
    ])
    sheet.write_all(ss.TAB_DECISIONS, [
        list(ss.DECISION_COLS),
        _dong(ss.DECISION_COLS, {"seq": 1, "symbol": "FPT",
                                 "signal_date": "2026-01-05"}),
    ])
    return sheet


class SheetChapChon:
    """Bọc ngoài một sheet thật, cho hỏng N lời gọi read_rows đầu tiên.

    `hong_o_tab` để dựng riêng tình huống đọc trades XONG rồi mới hỏng ở
    decisions — tình huống đó mới kiểm được rằng thứ tự trong pull()
    (đọc mạng trước, DELETE sau) đúng như đọc từ mã.
    """

    def __init__(self, that, so_lan_hong: int = 1, hong_o_tab=None):
        self.that = that
        self.con_hong = so_lan_hong
        self.hong_o_tab = hong_o_tab
        self.so_lan_doc = 0

    def read_rows(self, tab):
        self.so_lan_doc += 1
        dung_tab = self.hong_o_tab is None or tab == self.hong_o_tab
        if self.con_hong > 0 and dung_tab:
            self.con_hong -= 1
            raise ConnectionError("mạng chập")
        return self.that.read_rows(tab)

    def write_all(self, tab, rows):
        self.that.write_all(tab, rows)

    def append_rows(self, tab, rows):
        self.that.append_rows(tab, rows)


class NghiGia:
    """Thay time.sleep — ghi lại đã bị bảo ngủ bao lâu, không ngủ thật."""

    def __init__(self):
        self.cac_lan = []

    def __call__(self, giay):
        self.cac_lan.append(giay)


def _duong_dan_so_tam() -> str:
    fd, p = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(p)          # để PaperTradingJournal tự tạo từ đầu
    return p


def _dem_ban_ghi(db_path: str) -> tuple:
    if not os.path.exists(db_path):
        return (0, 0)
    c = sqlite3.connect(db_path)
    try:
        return (c.execute("SELECT COUNT(*) FROM trades").fetchone()[0],
                c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0])
    finally:
        c.close()


# ─────────────────────────────────────────────────────────────────────
# 1. Kéo hỏng không để lại dấu vết  (điều kiện tiên quyết của thử lại)
# ─────────────────────────────────────────────────────────────────────

def test_keo_hong_o_lenh_khong_de_lai_dau_vet():
    p = _duong_dan_so_tam()
    try:
        hong = SheetChapChon(sheet_co_du_lieu(), so_lan_hong=1)
        try:
            gs.restore_journal_from_google_sheets(p, backend=hong)
        except ConnectionError:
            pass
        else:
            raise AssertionError("lỗi mạng bị nuốt mất")

        assert _dem_ban_ghi(p) == (0, 0), (
            f"sổ bẩn sau lần kéo hỏng: {_dem_ban_ghi(p)}")

        # Lần thử sau phải kéo được — nếu lần hỏng để lại dấu vết thì
        # gác chống ghi đè trong pull() sẽ từ chối ở đây.
        bc = gs.restore_journal_from_google_sheets(p, backend=hong)
        assert bc == {"trades": 1, "decisions": 1}, bc
        print("PASS  kéo hỏng ở lệnh -> sổ vẫn sạch, lần sau kéo được")
    finally:
        if os.path.exists(p):
            os.remove(p)


def test_keo_hong_giua_chung_khong_lam_mat_so_dang_co():
    """Sổ ĐÃ CÓ dữ liệu, kéo lại, hỏng giữa chừng -> không mất bản ghi nào.

    PHẢI seed sổ trước. Kiểm trên sổ trống là test rỗng nghĩa: sổ trống
    thì hỏng kiểu gì nó cũng "vẫn trống", kể cả khi pull() xoá sạch rồi
    mới chết. Có dữ liệu sẵn mới phân biệt được GIỮ NGUYÊN với
    CHƯA-TỪNG-LÀM-GÌ.

    Tính chất được khoá ở đây là tính chất mà cơ chế thử lại dựa vào:
    "một lần pull() hỏng để lại sổ y như trước". Nó đứng vững nhờ hai lý
    do độc lập — hai lời gọi mạng nằm trước mọi lệnh DELETE, và
    connection đóng khi chưa commit thì SQLite rollback. Test không quan
    tâm lý do nào giữ nó, chỉ quan tâm nó còn đúng.
    """
    p = _duong_dan_so_tam()
    try:
        # Seed: kéo thành công một lần.
        bc = gs.restore_journal_from_google_sheets(
            p, backend=sheet_co_du_lieu())
        assert bc == {"trades": 1, "decisions": 1}, bc
        assert _dem_ban_ghi(p) == (1, 1), _dem_ban_ghi(p)

        # Kéo lại, cho phép ghi đè, nhưng hỏng ở lần đọc mạng THỨ HAI.
        hong = SheetChapChon(sheet_co_du_lieu(), so_lan_hong=1,
                             hong_o_tab=ss.TAB_DECISIONS)
        try:
            gs.restore_journal_from_google_sheets(
                p, allow_overwrite=True, backend=hong)
        except ConnectionError:
            pass
        else:
            raise AssertionError("lỗi mạng bị nuốt mất")

        assert _dem_ban_ghi(p) == (1, 1), (
            f"mất dữ liệu khi kéo hỏng giữa chừng: {_dem_ban_ghi(p)}")
        print("PASS  hỏng giữa chừng -> sổ đang có không mất bản ghi nào")
    finally:
        if os.path.exists(p):
            os.remove(p)


# ─────────────────────────────────────────────────────────────────────
# 2. Thử lại cứu được lỗi nhất thời
# ─────────────────────────────────────────────────────────────────────

def test_thu_lai_cuu_duoc_loi_nhat_thoi():
    p = _duong_dan_so_tam()
    try:
        hong = SheetChapChon(sheet_co_du_lieu(), so_lan_hong=1)
        nghi = NghiGia()
        bc = gs.keo_so_co_thu_lai(p, so_lan=3, cho=(5, 20), backend=hong,
                                  nghi=nghi, ghi=lambda _s: None)
        assert bc == {"trades": 1, "decisions": 1}, bc
        assert nghi.cac_lan == [5], f"chờ sai nhịp: {nghi.cac_lan}"
        print("PASS  hỏng lần 1 -> thử lại -> kéo được, chờ đúng 5s")
    finally:
        if os.path.exists(p):
            os.remove(p)


def test_gian_dan_thoi_gian_cho():
    p = _duong_dan_so_tam()
    try:
        hong = SheetChapChon(sheet_co_du_lieu(), so_lan_hong=2)
        nghi = NghiGia()
        bc = gs.keo_so_co_thu_lai(p, so_lan=3, cho=(5, 20), backend=hong,
                                  nghi=nghi, ghi=lambda _s: None)
        assert bc == {"trades": 1, "decisions": 1}, bc
        assert nghi.cac_lan == [5, 20], f"chờ sai nhịp: {nghi.cac_lan}"
        print("PASS  hỏng 2 lần -> chờ giãn dần 5s rồi 20s")
    finally:
        if os.path.exists(p):
            os.remove(p)


# ─────────────────────────────────────────────────────────────────────
# 3. Chưa cấu hình thì KHÔNG thử lại
# ─────────────────────────────────────────────────────────────────────

def test_chua_cau_hinh_thi_khong_thu_lai():
    goi = []
    that = gs.restore_journal_from_google_sheets

    def gia(*a, **k):
        goi.append(1)
        return None

    gs.restore_journal_from_google_sheets = gia
    try:
        nghi = NghiGia()
        bc = gs.keo_so_co_thu_lai("khong-dung-toi.db", so_lan=3,
                                  nghi=nghi, ghi=lambda _s: None)
    finally:
        gs.restore_journal_from_google_sheets = that

    assert bc is None, bc
    assert len(goi) == 1, f"gọi lại {len(goi)} lần cho việc chắc chắn vô ích"
    assert nghi.cac_lan == [], f"ngủ vô ích: {nghi.cac_lan}"
    print("PASS  chưa cấu hình -> trả None ngay, không thử lại")


# ─────────────────────────────────────────────────────────────────────
# 4. Hết số lần thì NỔ, không trả None, không trả sổ rỗng
# ─────────────────────────────────────────────────────────────────────

def test_het_so_lan_thi_no():
    p = _duong_dan_so_tam()
    try:
        hong = SheetChapChon(sheet_co_du_lieu(), so_lan_hong=99)
        nghi = NghiGia()
        try:
            gs.keo_so_co_thu_lai(p, so_lan=3, cho=(5, 20), backend=hong,
                                 nghi=nghi, ghi=lambda _s: None)
        except gs.KeoSoThatBai as e:
            loi = str(e)
        else:
            raise AssertionError("thử hết vẫn hỏng mà không nổ")

        assert "3 lần" in loi, loi
        assert "ConnectionError" in loi, (
            f"không nói ra lỗi gốc thì lần sau lại phải đoán: {loi}")
        assert nghi.cac_lan == [5, 20], nghi.cac_lan
        assert _dem_ban_ghi(p) == (0, 0)
        print("PASS  hỏng cả 3 lần -> nổ, nêu tên lỗi gốc, sổ vẫn sạch")
    finally:
        if os.path.exists(p):
            os.remove(p)


def test_so_lan_khong_hop_le_thi_no_ngay():
    for xau in (0, -1):
        try:
            gs.keo_so_co_thu_lai("khong-dung-toi.db", so_lan=xau)
        except ValueError:
            pass
        else:
            raise AssertionError(f"so_lan={xau} được nhận")
    print("PASS  so_lan < 1 bị từ chối")


# ─────────────────────────────────────────────────────────────────────
# 5. Workflow phải THẬT SỰ gọi hàm này
# ─────────────────────────────────────────────────────────────────────

def test_workflow_dung_ham_co_thu_lai():
    """Không có test này thì hàm trên có thể xanh mà nhịp quét vẫn gọi
    đường cũ — đúng kiểu hỏng âm thầm mà dự án đã dính nhiều lần."""
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(goc, ".github", "workflows", "quet-so-lenh.yml")
    s = io.open(p, encoding="utf-8").read()
    assert "keo_so_co_thu_lai" in s, "workflow chưa gọi hàm có thử lại"
    assert "KeoSoThatBai" in s, "workflow chưa bắt KeoSoThatBai"
    print("PASS  workflow gọi đúng đường có thử lại")


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            ham()
    print("\nTẤT CẢ ĐỀU QUA")
