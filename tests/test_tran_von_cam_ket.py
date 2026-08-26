"""Gác cho trần vốn cam kết — bất biến 7b, lần đầu được CHẶN chứ không chỉ báo.

Trước 24/08/2026 không có gì ngăn sổ mở thêm vị thế khi vốn cam kết đã
vượt 100%. `Performance.avg_capital_deployed_pct` chỉ BÁO CÁO sau khi việc
đã rồi — chuông báo cháy, không phải cửa chống cháy. Đo được:

    so lenh that      29% trung binh · 208% DINH
    walk-forward OOS 145% trung binh · 524% dinh

Đường vốn nhân dồn từng lệnh vào TOÀN BỘ vốn hiện có, nên khi tổng vốn cam
kết vượt 100% thì con số cộng dồn là lợi nhuận của một tài khoản VAY ĐƯỢC.
Đó đúng là cơ chế sinh ra +636,11% ngày 12/08/2026.

Hai loại lỗi phải chặn:
  • trần không chặn được  → đòn bẩy ẩn quay lại
  • **trần chặn nhầm**    → mất lệnh mà không ai biết vì sao
"""
import paper_trading as pt
import pytest
from paper_trading import Status

pytest.importorskip("pandas")


def _ket_qua(diem=70, entry=100.0, sl=95.0, tp=130.0):
    """Kết quả chấm điểm đủ để `consider_entry` mở lệnh."""
    return {
        "final_score": diem,
        "recommendation": "MUA",
        "data_quality": "OK",
        "score_breakdown": {},
        "key_reasons": [],
        "analyses": {"risk": {"recommendations": {
            "entry_price": entry, "stop_loss_price": sl,
            "take_profit_price": tp}}},
    }


@pytest.fixture
def so_lenh(tmp_path, monkeypatch):
    """Sổ scratch, cổng C5 mở, bộ lọc VN-INDEX luôn cho qua."""
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *_a, **_k: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    return pt.PaperTradingJournal(str(tmp_path / "wf_test.db"))


def _mo(so, ma, ngay="2026-03-02", **kw):
    return so.consider_entry(ma, ngay, _ket_qua(**kw), buy_threshold=50.0)


# ─────────────────────────────────────────────────────────────────────
# 1. Trần chặn được
# ─────────────────────────────────────────────────────────────────────

def test_khong_bao_gio_vuot_tran(so_lenh):
    """Mở liên tục 30 mã: tổng vốn cam kết không được vượt 100% lần nào."""
    dinh = 0.0
    for i in range(30):
        _mo(so_lenh, f"M{i:02d}")
        dinh = max(dinh, so_lenh.von_dang_cam_ket())
    assert dinh <= pt.TRAN_VON_CAM_KET_PCT, (
        f"vốn cam kết chạm {dinh:.1f}% — trần không chặn được")
    print(f"PASS  30 lệnh liên tiếp, đỉnh vốn cam kết {dinh:.1f}%")


def test_lenh_bi_tu_choi_phai_GHI_LY_DO_vao_so(so_lenh):
    """Bị chặn mà không ghi lý do thì trần thành một lỗ rò im lặng."""
    for i in range(30):
        _mo(so_lenh, f"M{i:02d}")
    ly_do = [d["skip_reason"] for d in so_lenh.decisions()
             if pt.LY_DO_TRAN_VON in (d["skip_reason"] or "")]
    assert ly_do, "không quyết định nào ghi lý do trần vốn"
    assert "%" in ly_do[0], f"lý do phải kèm con số, nhận {ly_do[0]!r}"
    print(f"PASS  {len(ly_do)} lệnh bị trần chặn, ví dụ: {ly_do[0][:70]}")


def test_dong_bot_vi_the_thi_mo_duoc_tiep(so_lenh):
    """Trần là ràng buộc theo THỜI ĐIỂM, không phải hạn ngạch cả đời."""
    for i in range(30):
        _mo(so_lenh, f"M{i:02d}")
    day = so_lenh.von_dang_cam_ket()
    so_lenh.db.execute("UPDATE trades SET status=? WHERE id=1",
                       (Status.CLOSED,))
    so_lenh.db.commit()
    assert so_lenh.von_dang_cam_ket() < day
    assert _mo(so_lenh, "MOI") is not None, (
        "đóng bớt vị thế rồi mà vẫn không mở được -> trần đang đếm cả lệnh "
        "đã đóng")
    print("PASS  đóng một vị thế -> mở được lệnh mới")


# ─────────────────────────────────────────────────────────────────────
# 2. Lệnh CHỜ KHỚP cũng phải tính — ô dễ sót nhất
# ─────────────────────────────────────────────────────────────────────

def test_lenh_PENDING_cung_tinh_vao_von_cam_ket(so_lenh):
    """Bỏ PENDING ra thì xếp bao nhiêu lệnh chờ cũng lọt.

    Rồi sáng hôm sau tất cả cùng khớp một lượt — trần vô hiệu đúng vào
    phiên nó cần chặn nhất. `consider_entry` tạo lệnh ở trạng thái
    PENDING, nên nếu hàm chỉ đếm OPEN thì nó luôn thấy 0%.
    """
    _mo(so_lenh, "AAA")
    dang = so_lenh.von_dang_cam_ket()
    assert dang > 0, (
        "lệnh vừa mở đang ở trạng thái PENDING mà vốn cam kết = 0 -> "
        "hàm chỉ đếm OPEN, trần sẽ không bao giờ chặn được gì")
    print(f"PASS  một lệnh PENDING -> vốn cam kết {dang:.1f}%")


# ─────────────────────────────────────────────────────────────────────
# 3. KHÔNG chặn nhầm
# ─────────────────────────────────────────────────────────────────────

def test_lenh_dau_tien_khong_bao_gio_bi_tran_chan(so_lenh):
    assert _mo(so_lenh, "AAA") is not None
    print("PASS  sổ rỗng -> lệnh đầu tiên qua")


def test_tran_dat_SAU_moi_cong_khac(so_lenh):
    """Điểm dưới ngưỡng phải ghi lý do ĐIỂM, không phải lý do trần.

    Đặt trần lên trước thì các cổng kia không còn thống kê được nữa —
    cùng lý do mà chốt C5 được đặt sau cùng.
    """
    assert _mo(so_lenh, "AAA", diem=10) is None
    ly_do = [d["skip_reason"] for d in so_lenh.decisions()]
    assert any("dưới ngưỡng" in (r or "") for r in ly_do), ly_do
    assert not any(pt.LY_DO_TRAN_VON in (r or "") for r in ly_do)
    print("PASS  điểm thấp -> ghi lý do điểm, không phải lý do trần")


# ─────────────────────────────────────────────────────────────────────
# 4. Hằng số phải giữ nguyên nghĩa
# ─────────────────────────────────────────────────────────────────────

def test_tran_mac_dinh_la_100_phan_tram():
    """Nâng trần lên trên 100% là bật lại đòn bẩy, không phải nới cấu hình.

    Bất biến 7b nói phép nhân dồn chỉ đúng khi vốn cam kết ≤ 100%.
    """
    assert pt.TRAN_VON_CAM_KET_PCT == 100.0
    print("PASS  trần = 100%")
