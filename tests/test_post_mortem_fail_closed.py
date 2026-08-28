"""Thiếu thành phần điểm thì post-mortem KHÔNG được đoán.

Bản trước thay mọi thành phần thiếu bằng `50`:

    c_trend = current_breakdown.get("trend_score", 50)

Với dung sai ±5 trên ba chiều, một toạ độ bịa (50, 50, 50) vẫn khớp được
một mẫu nào đó trong bộ nhớ và trừ **12 điểm** trên thang 100 — trong khi
ngưỡng mua là 62. Cùng cơ chế ở `record_sl_trade`: mẫu mang 50 bịa nằm lẫn
giữa mẫu thật và bẩn vĩnh viễn.

Đo 24/08/2026: 44/44 mẫu hiện có là (65,65,100) hoặc (65,65,93), KHÔNG mẫu
nào chứa 50. Nên chốt này không đổi hành vi hôm nay — nó chặn đường.

Từ 21/08/2026 `save_memory()` đã bật cho sổ thật và từ 24/08 cổng C5 đã mở,
nên đường này đang chấm điểm thật.
"""
import post_mortem_learning as pml


def _may(tmp_path, mau=None):
    m = pml.PostMortemLearningEngine(memory_file=str(tmp_path / "m.json"))
    m.enabled = True
    m.chi_doc = False
    m.sl_patterns = list(mau or [])
    return m


DU = {"trend_score": 65, "momentum_score": 65, "volume_score": 100}
MAU = [{"symbol": "FPT", "signal_date": "2026-01-05", "entry_score": 70,
        "trend_score": 65, "momentum_score": 65, "volume_score": 100,
        "reasons": [], "nguon": "paper_trades.db", "trade_id": 1,
        "phien_hoc": "2026-01-20"}]


def test_du_thanh_phan_thi_van_phat(tmp_path):
    """Chốt mới không được làm cơ chế cũ chết — nếu không, test dưới vô nghĩa."""
    m = _may(tmp_path, MAU)
    p = m.get_penalty_for_pattern(DU, as_of="2026-03-01",
                                  phien_hien_tai="2026-03-01")
    assert p != 0.0, "khớp đúng mẫu mà không phạt -> cơ chế đã chết"
    print(f"PASS  đủ ba thành phần, khớp mẫu -> phạt {p}")


def test_THIEU_thanh_phan_thi_KHONG_phat(tmp_path):
    """Mẫu phải nằm GẦN 50 trên trục bị thiếu, nếu không test vô nghĩa.

    Bản đầu của test này dùng mẫu (65,65,100) và bỏ `trend_score`. Bản cũ
    bịa ra 50, nhưng |50−65| = 15 > dung sai 5 nên nó cũng không khớp —
    test xanh cả hai bên, và đột biến "quay lại .get(...,50)" sống sót.

    Con số bịa chỉ cắn khi bộ nhớ có mẫu ở gần nó. Đó đúng là điều sẽ xảy
    ra khi bộ nhớ lớn dần: 44 mẫu hôm nay phủ 3,2% không gian, và mọi mẫu
    mới đều kéo vùng phủ rộng ra.
    """
    for truc, gia_tri in (("trend_score", 50), ("momentum_score", 50),
                          ("volume_score", 52)):
        mau = dict(MAU[0])
        mau[truc] = gia_tri              # mẫu nằm trong dung sai ±5 của 50
        m = _may(tmp_path, [mau])

        du = dict(DU)
        du[truc] = gia_tri
        assert m.get_penalty_for_pattern(
            du, as_of="2026-03-01", phien_hien_tai="2026-03-01") != 0.0, (
            f"mẫu gần 50 trên trục {truc} mà đủ thành phần lại không phạt "
            f"-> tình huống dựng sai, test không chứng minh được gì")

        thieu = {k: v for k, v in du.items() if k != truc}
        assert m.get_penalty_for_pattern(
            thieu, as_of="2026-03-01", phien_hien_tai="2026-03-01") == 0.0, (
            f"thiếu {truc} mà vẫn phạt -> điểm bị trừ dựa trên toạ độ 50 "
            f"bịa ra, và ở đây nó KHỚP một mẫu thật")
    print("PASS  thiếu thành phần -> không phạt, kể cả khi mẫu nằm cạnh 50")


def test_THIEU_thanh_phan_thi_KHONG_ghi_mau(tmp_path):
    m = _may(tmp_path)
    ok = m.record_sl_trade("FPT", 70, {"trend_score": 65, "volume_score": 100},
                           [], signal_date="2026-01-05", trade_id=9,
                           nguon="paper_trades.db", phien_hoc="2026-01-20")
    assert ok is False and m.sl_patterns == [], (
        "ghi một mẫu mang 50 bịa -> bộ nhớ bẩn vĩnh viễn, và mẫu đó khớp "
        "cả một vùng không lệnh thật nào từng đi qua")
    print("PASS  thiếu thành phần -> không ghi mẫu")


def test_DU_thanh_phan_thi_VAN_ghi_mau(tmp_path):
    m = _may(tmp_path)
    ok = m.record_sl_trade("FPT", 70, dict(DU), [], signal_date="2026-01-05",
                           trade_id=9, nguon="paper_trades.db",
                           phien_hoc="2026-01-20")
    assert ok is True and len(m.sl_patterns) == 1
    assert m.sl_patterns[0]["trend_score"] == 65
    print("PASS  đủ thành phần -> vẫn ghi bình thường")


def test_gia_tri_0_KHONG_bi_coi_la_thieu(tmp_path):
    """`0` là một điểm số hợp lệ. Dùng `not x` thay `x is None` sẽ nuốt nó.

    `momentum` đo được là luôn trả 0 (MO-XE-KIEN-TRUC.md), nên đây không
    phải trường hợp giả định.
    """
    m = _may(tmp_path)
    ok = m.record_sl_trade(
        "FPT", 70, {"trend_score": 0, "momentum_score": 0, "volume_score": 0},
        [], signal_date="2026-01-05", trade_id=9, nguon="paper_trades.db",
        phien_hoc="2026-01-20")
    assert ok is True, "điểm 0 bị coi là thiếu -> mất mẫu thật"
    print("PASS  điểm 0 là giá trị hợp lệ, không phải 'thiếu'")
