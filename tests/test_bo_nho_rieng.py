"""Test bộ nhớ post-mortem RIÊNG cho mỗi lượt backtest.

VÌ SAO CÓ FILE NÀY
──────────────────
`_ENGINE_CACHE` là MỘT engine cho cả tiến trình. `record_sl_trade()` nối
thêm vào `sl_patterns` của engine đó. Nên trong `walkforward.chay()`, bảy
lượt dò ngưỡng và lượt OOS đều dùng chung một bộ nhớ đang lớn dần: lượt
ngưỡng 62 khởi động với bộ nhớ to hơn lượt ngưỡng 45.

Đo được 21/08/2026: ba lệnh cắt lỗ liên tiếp đưa bộ nhớ từ 44 lên 47 mẫu,
dù không mẫu nào được ghi ra đĩa. Bảy lượt KHÔNG độc lập — mà chọn lượt
tốt nhất trong một dải không độc lập chính là bất biến 7.

BA THỨ PHẢI ĐÚNG
────────────────
  1. Đổi engine thì thật sự đổi, kể cả khi đường dẫn không đổi.
  2. Dấu vân bộ nhớ phân biệt được hai bộ nhớ KHÁC NHAU nhưng CÙNG ĐỘ DÀI.
     Dấu vân cũ là `(enabled, len(sl_patterns))` nên không phân biệt được —
     hai lượt đều có 3 mẫu sẽ dùng chung điểm đã ghi nhớ, trong khi điểm
     thật thì khác nhau. Test `test_dau_van_phan_biet_hai_bo_nho_cung_dai`
     đỏ trên bản cũ.
  3. `co_san` KHÔNG được đụng vào `sl_pattern_memory.json` thật.

Chạy offline.
"""
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paper_runner as pr
import post_mortem_learning as pml
import walkforward as wf


def _mau(signal_date: str = "2026-01-05", trend: float = 70.0) -> dict:
    """Một mẫu hợp lệ — có đủ trường nguồn gốc nên load_memory() không bỏ."""
    return {
        "symbol": "FPT", "signal_date": signal_date, "entry_score": 70,
        "trend_score": trend, "momentum_score": 65.0, "volume_score": 60.0,
        "reasons": [], "nguon": "test.db", "trade_id": 1,
        "ghi_luc": "2026-01-05T00:00:00+07:00", "phien_hoc": "2026-01-20",
    }


def _ghi_bo_nho(duong: str, mau: list) -> None:
    with io.open(duong, "w", encoding="utf-8") as f:
        json.dump(mau, f, ensure_ascii=False)


def _file_tam(duoi: str = ".json") -> str:
    fd, p = tempfile.mkstemp(suffix=duoi)
    os.close(fd)
    os.remove(p)
    return p


def _don(*duong: str) -> None:
    for p in duong:
        if p and os.path.exists(p):
            os.remove(p)


def _tra_engine_ve_mac_dinh() -> None:
    """Đừng để engine của test rò sang file test chạy sau.

    `_ENGINE_CACHE` là biến toàn tiến trình. Vá nó mà không trả lại đúng là
    kiểu rò đã làm mất một buổi ở `tests/test_sheets_store.py`.
    """
    pml.dat_lai_engine(pml.MEMORY_FILE)
    pr._xoa_cache_phan_tich()


# ─────────────────────────────────────────────────────────────────────
# 1. Đổi engine thì thật sự đổi
# ─────────────────────────────────────────────────────────────────────

def test_get_learning_engine_dung_lai_engine_cu():
    """Ghi lại hành vi CŨ — đây là nguyên nhân, không phải lỗi cần sửa.

    Dùng lại engine là đúng cho app và cho phiên quét hằng ngày. Nó chỉ sai
    cho backtest nhiều lượt, và đó là lý do có `dat_lai_engine()`.
    """
    try:
        a = pml.get_learning_engine(pml.MEMORY_FILE)
        b = pml.get_learning_engine(pml.MEMORY_FILE)
        assert a is b, "cùng đường dẫn mà ra hai engine — hành vi đã đổi"
        print("PASS  get_learning_engine dùng lại engine cũ (như thiết kế)")
    finally:
        _tra_engine_ve_mac_dinh()


def test_dat_lai_engine_ep_dung_moi():
    try:
        a = pml.get_learning_engine(pml.MEMORY_FILE)
        b = pml.dat_lai_engine(pml.MEMORY_FILE)
        assert a is not b, "dat_lai_engine trả về đúng engine cũ"
        assert b.the_engine != a.the_engine, "hai engine trùng định danh"
        assert pml.get_learning_engine(pml.MEMORY_FILE) is b, (
            "engine mới không được đặt làm engine hiện hành")
        print("PASS  dat_lai_engine ép dựng engine mới, kể cả trùng đường dẫn")
    finally:
        _tra_engine_ve_mac_dinh()


# ─────────────────────────────────────────────────────────────────────
# 2. Dấu vân bộ nhớ  (đây là test then chốt)
# ─────────────────────────────────────────────────────────────────────

def test_dau_van_phan_biet_hai_bo_nho_cung_dai():
    """Hai bộ nhớ NỘI DUNG KHÁC NHAU nhưng CÙNG ĐỘ DÀI.

    Dấu vân cũ `(enabled, len(sl_patterns))` cho ra cùng một giá trị ở đây,
    nên hai lượt backtest dùng chung điểm đã ghi nhớ trong khi điểm thật
    khác nhau. Test này đỏ trên bản cũ — đó là lý do nó tồn tại.
    """
    a = _file_tam()
    b = _file_tam()
    try:
        _ghi_bo_nho(a, [_mau("2026-01-05", 70.0)])
        _ghi_bo_nho(b, [_mau("2026-03-09", 31.0)])   # cùng 1 mẫu, khác nội dung

        pml.dat_lai_engine(a, enabled=True)
        van_a = pr._dau_van_bo_nho()
        pml.dat_lai_engine(b, enabled=True)
        van_b = pr._dau_van_bo_nho()

        assert len(pml.get_learning_engine(b).sl_patterns) == 1
        assert van_a != van_b, (
            f"hai bộ nhớ khác nhau cho cùng dấu vân {van_a} — khoá cache sẽ "
            f"trùng trong khi điểm thì khác")
        print("PASS  dấu vân phân biệt hai bộ nhớ cùng độ dài")
    finally:
        _tra_engine_ve_mac_dinh()
        _don(a, b)


def test_dau_van_doi_khi_ghi_them_mau():
    p = _file_tam()
    try:
        may = pml.dat_lai_engine(p, enabled=True)
        truoc = pr._dau_van_bo_nho()
        assert may.record_sl_trade(
            "FPT", 70, {"trend_score": 70, "momentum_score": 65,
                        "volume_score": 60},
            [], signal_date="2026-01-05", trade_id=7, nguon="test.db",
            phien_hoc="2026-01-20") is True
        assert pr._dau_van_bo_nho() != truoc, (
            "ghi thêm mẫu mà dấu vân không đổi — điểm cũ sẽ được dùng lại")
        print("PASS  dấu vân đổi khi bộ nhớ đổi")
    finally:
        _tra_engine_ve_mac_dinh()
        _don(p)


def test_dau_van_bat_duoc_sua_tai_cho():
    """Sửa danh sách TẠI CHỖ, không qua engine.

    Đây là thứ giữ `len` lại trong dấu vân: nối thẳng vào danh sách không
    đi qua engine, nên chỉ độ dài phản ánh được.
    """
    p = _file_tam()
    try:
        may = pml.dat_lai_engine(p, enabled=True)
        truoc = pr._dau_van_bo_nho()

        may.sl_patterns.append(_mau())          # nối thẳng, không qua setter

        assert pr._dau_van_bo_nho() != truoc, (
            "sửa tại chỗ mà dấu vân không đổi — cache sẽ trả điểm cũ")
        print("PASS  dấu vân bắt được sửa tại chỗ (nhờ len)")
    finally:
        _tra_engine_ve_mac_dinh()
        _don(p)


def test_dau_van_giu_nguyen_khi_bo_nho_khong_doi():
    """Đọc hai lần liên tiếp phải ra cùng dấu vân — nếu không thì cache
    không bao giờ trúng và mọi lát cắt bị chấm lại."""
    p = _file_tam()
    try:
        pml.dat_lai_engine(p, enabled=True)
        assert pr._dau_van_bo_nho() == pr._dau_van_bo_nho()
        print("PASS  bộ nhớ không đổi -> dấu vân không đổi")
    finally:
        _tra_engine_ve_mac_dinh()
        _don(p)


# ─────────────────────────────────────────────────────────────────────
# 3. Ba chế độ học
# ─────────────────────────────────────────────────────────────────────

def test_che_do_tat_thi_engine_tat():
    try:
        may = wf._dung_bo_nho("tat", None)
        assert may.enabled is False
        print("PASS  chế độ tat -> engine tắt")
    finally:
        _tra_engine_ve_mac_dinh()


def test_che_do_tich_luy_bat_dau_rong():
    p = _file_tam()
    try:
        _ghi_bo_nho(p, [_mau(), _mau(), _mau()])     # rác từ lượt trước
        may = wf._dung_bo_nho("tich_luy", p)
        assert may.enabled is True
        assert may.sl_patterns == [], (
            f"tich_luy phải bắt đầu từ số không, đang có "
            f"{len(may.sl_patterns)} mẫu")
        print("PASS  chế độ tich_luy bắt đầu rỗng, xoá dấu vết lượt trước")
    finally:
        _tra_engine_ve_mac_dinh()
        _don(p)


def test_hai_luot_tich_luy_khong_dinh_nhau():
    """Đúng cái lỗi cần sửa: lượt sau không được thừa hưởng bộ nhớ lượt trước."""
    a, b = _file_tam(), _file_tam()
    try:
        may1 = wf._dung_bo_nho("tich_luy", a)
        may1.record_sl_trade(
            "FPT", 70, {"trend_score": 70, "momentum_score": 65,
                        "volume_score": 60},
            [], signal_date="2026-01-05", trade_id=1, nguon="a.db",
            phien_hoc="2026-01-20")
        assert len(may1.sl_patterns) == 1

        may2 = wf._dung_bo_nho("tich_luy", b)
        assert may2 is not may1
        assert may2.sl_patterns == [], (
            f"lượt sau thừa hưởng {len(may2.sl_patterns)} mẫu của lượt trước")
        print("PASS  hai lượt tich_luy độc lập")
    finally:
        _tra_engine_ve_mac_dinh()
        _don(a, b)


def test_che_do_co_san_nap_bo_nho_va_khong_dung_file_that():
    that = _file_tam()
    try:
        _ghi_bo_nho(that, [_mau("2026-01-05"), _mau("2026-02-06")])
        goc = pml.MEMORY_FILE
        pml.MEMORY_FILE = that
        try:
            may = wf._dung_bo_nho("co_san", None)
            assert may.enabled is True
            assert len(may.sl_patterns) == 2, len(may.sl_patterns)
            assert os.path.abspath(may.memory_file) != os.path.abspath(that), (
                "co_san đang trỏ THẲNG vào file bộ nhớ thật")

            # Ghi thêm rồi lưu — file thật phải không suy suyển.
            may.record_sl_trade(
                "AAA", 70, {"trend_score": 70, "momentum_score": 65,
                            "volume_score": 60},
                [], signal_date="2026-03-07", trade_id=9, nguon="x.db",
                phien_hoc="2026-03-20")
            may.save_memory(force=True)

            with io.open(that, encoding="utf-8") as f:
                assert len(json.load(f)) == 2, "file bộ nhớ thật bị ghi đè"
            print("PASS  co_san nạp bộ nhớ nhưng chạy trên bản sao")
        finally:
            _don(may.memory_file)
            pml.MEMORY_FILE = goc
    finally:
        _tra_engine_ve_mac_dinh()
        _don(that)


def test_co_san_dung_bo_nho_nhung_khong_ghi_them():
    """CHỈ ĐỌC phải là chỉ đọc.

    Bản đầu để `co_san` vừa nạp 44 mẫu vừa tích luỹ tiếp — chạy thử trên 5
    mã thấy nó học thêm 52 mẫu trong một lượt. Khi đó nó đo hiệu ứng GỘP
    của "có sẵn" và "tích luỹ", không quy được cho bên nào, tức không trả
    lời được câu hỏi nó sinh ra để trả lời.
    """
    that = _file_tam()
    try:
        _ghi_bo_nho(that, [_mau("2026-01-05"), _mau("2026-02-06")])
        goc = pml.MEMORY_FILE
        pml.MEMORY_FILE = that
        try:
            may = wf._dung_bo_nho("co_san", None)
            assert may.enabled is True, "co_san phải BẬT để còn chấm điểm"
            assert may.chi_doc is True, "co_san phải ở chế độ chỉ đọc"
            assert len(may.sl_patterns) == 2

            ghi_duoc = may.record_sl_trade(
                "AAA", 70, {"trend_score": 70, "momentum_score": 65,
                            "volume_score": 60},
                [], signal_date="2026-03-07", trade_id=9, nguon="x.db",
                phien_hoc="2026-03-20")
            assert ghi_duoc is False, "co_san vẫn ghi được mẫu mới"
            assert len(may.sl_patterns) == 2, (
                f"bộ nhớ phình từ 2 lên {len(may.sl_patterns)} trong chế độ "
                f"chỉ đọc")
            print("PASS  co_san dùng bộ nhớ nhưng không ghi thêm mẫu nào")
        finally:
            _don(may.memory_file)
            pml.MEMORY_FILE = goc
    finally:
        _tra_engine_ve_mac_dinh()
        _don(that)


def test_che_do_tat_thi_bo_nho_rong_han():
    """`tat` không được chỉ là "tắt công tắc" — bộ nhớ phải rỗng thật.

    Engine tắt mà vẫn ôm 44 mẫu thì chúng vô hại nhờ MỘT công tắc đang
    tắt. Không có gì để dùng thì mạnh hơn hẳn.
    """
    try:
        may = wf._dung_bo_nho("tat", None)
        assert may.enabled is False
        assert may.sl_patterns == [], (
            f"chế độ tat vẫn nạp {len(may.sl_patterns)} mẫu")
        print("PASS  chế độ tat -> engine tắt VÀ bộ nhớ rỗng")
    finally:
        _tra_engine_ve_mac_dinh()


def test_che_do_la_thi_no():
    try:
        for xau in ("bat", "TICH_LUY", "", None):
            try:
                wf._dung_bo_nho(xau, "x.json")
            except ValueError:
                pass
            else:
                raise AssertionError(f"chế độ {xau!r} được nhận")
        print("PASS  chế độ lạ bị từ chối, không âm thầm chạy như 'tat'")
    finally:
        _tra_engine_ve_mac_dinh()


def test_tich_luy_thieu_duong_dan_thi_no():
    try:
        try:
            wf._dung_bo_nho("tich_luy", None)
        except ValueError:
            pass
        else:
            raise AssertionError("tich_luy không có đường dẫn mà vẫn chạy")
        print("PASS  tich_luy thiếu đường dẫn -> nổ, không ghi bừa vào đâu")
    finally:
        _tra_engine_ve_mac_dinh()


if __name__ == "__main__":
    for ten, ham in sorted(list(globals().items())):
        if ten.startswith("test_"):
            ham()
    print("\nTẤT CẢ ĐỀU QUA")
