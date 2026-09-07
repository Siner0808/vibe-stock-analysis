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


# ─────────────────────────────────────────────────────────────────────
# Lệnh mồ côi khi hết dữ liệu — chỗ trần vốn bị rò
# ─────────────────────────────────────────────────────────────────────
#
# `walkforward._mo_phong` chạy THEO MÃ: xong toàn bộ lịch sử của FPT rồi
# mới sang ACB. Lệnh còn mở lúc hết dữ liệu của FPT không bao giờ được
# đóng — nó nằm lại trong DB suốt phần còn lại của lượt chạy.
#
# Trước khi có trần vốn điều đó vô hại: `[x for x in lenh if x.status ==
# CLOSED]` lặng lẽ bỏ chúng ra. Có trần rồi thì chúng ĂN VÀO HẠN MỨC của
# mọi mã sau. Đo 24/08/2026 trên vùng OOS: 4 lệnh mồ côi của 4 mã khác
# nhau chiếm 93,8% hạn mức, và số lệnh tụt 386 → 142. Con số đó là chỗ bị
# chiếm, KHÔNG phải giá của trần.


def test_dong_so_sach_dong_lenh_OPEN_va_XOA_lenh_PENDING(so_lenh):
    """Hai trạng thái, hai cách xử lý khác nhau — và khác nhau là cố ý."""
    _mo(so_lenh, "AAA")
    so_lenh.fill_pending("AAA", "2026-03-03", 100.0)
    _mo(so_lenh, "BBB")                       # để nguyên PENDING

    n = so_lenh.dong_so_sach("AAA", "2026-03-10", 108.0)
    assert n == 1
    t = [x for x in so_lenh.all_trades() if x.symbol == "AAA"][0]
    assert t.status == "CLOSED"
    assert t.exit_reason == pt.ExitReason.HET_DU_LIEU
    assert t.exit_price == 108.0

    m = so_lenh.dong_so_sach("BBB", "2026-03-10", 100.0)
    assert m == 1
    assert [x for x in so_lenh.all_trades() if x.symbol == "BBB"] == [], (
        "lệnh PENDING chưa bao giờ khớp — ghi lãi/lỗ cho nó là bịa ra một "
        "giao dịch")
    print("PASS  OPEN -> đóng ở giá cuối · PENDING -> xoá")


def test_dong_so_sach_GIAI_PHONG_han_muc(so_lenh):
    """Đây là lý do hàm này tồn tại."""
    for i in range(30):
        _mo(so_lenh, f"M{i:02d}")
    day = so_lenh.von_dang_cam_ket()
    assert day > 0
    for i in range(30):
        so_lenh.dong_so_sach(f"M{i:02d}", "2026-03-10", 100.0)
    assert so_lenh.von_dang_cam_ket() == 0.0, (
        "đóng sổ sách xong mà hạn mức vẫn bị chiếm -> mã sau vẫn bị chặn "
        "bởi lệnh của mã trước")
    print(f"PASS  {day:.1f}% hạn mức -> 0% sau khi đóng sổ sách")


def test_dong_so_sach_KHONG_dung_toi_ma_khac(so_lenh):
    """Mã kia phải ở trạng thái OPEN, không phải PENDING.

    Bản đầu của test này để BBB ở PENDING, nên đột biến "đóng sạch MỌI mã"
    (chỉ đụng OPEN) vẫn xanh. Một gác không đặt đúng trạng thái cần bảo vệ
    thì không bảo vệ được gì.
    """
    _mo(so_lenh, "AAA")
    _mo(so_lenh, "BBB")
    so_lenh.fill_pending("AAA", "2026-03-03", 100.0)
    so_lenh.fill_pending("BBB", "2026-03-03", 100.0)
    assert {x.symbol: x.status for x in so_lenh.all_trades()}["BBB"] == "OPEN"

    so_lenh.dong_so_sach("AAA", "2026-03-10", 100.0)
    sau = {x.symbol: x.status for x in so_lenh.all_trades()}
    assert sau["AAA"] == "CLOSED"
    assert sau["BBB"] == "OPEN", (
        "đóng sổ sách của AAA lại đụng tới BBB — mọi mã sau sẽ mất vị thế "
        "đang mở của chúng")
    print("PASS  đóng sổ sách AAA -> BBB vẫn OPEN")


def test_dong_so_sach_tren_so_rong_khong_no(so_lenh):
    assert so_lenh.dong_so_sach("XXX", "2026-03-10", 100.0) == 0
    print("PASS  sổ rỗng -> 0, không nổ")


def test_walkforward_PHAI_goi_dong_so_sach():
    """Gác đọc AST: `"dong_so_sach" in src` sẽ khớp phải chú thích ở trên.

    Không có lời gọi này thì trần vốn trong mọi lượt walk-forward bị lệnh
    mồ côi ăn mất hạn mức, và kết quả trông như "trần đắt" trong khi thật
    ra là đo nhầm.
    """
    import ast
    import os
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cay = ast.parse(open(os.path.join(goc, "walkforward.py"),
                         encoding="utf-8").read())
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    goi |= {n.func.id for n in ast.walk(cay)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "dong_so_sach" in goi, (
        "walkforward.py không gọi dong_so_sach — lệnh mồ côi sẽ ăn vào "
        "trần vốn của mọi mã phía sau")
    # Và phải nhân hệ số giá. vnstock trả nghìn đồng, sổ lệnh ghi VNĐ;
    # truyền giá thô vào `dong_so_sach` cho ra −99,90% cho MỌI lệnh. Đã
    # xảy ra thật ngày 24/08/2026 — bốn lệnh kéo kỳ vọng OOS từ +0,616%
    # xuống −0,419%, và không có gì đỏ cho tới khi đọc từng dòng lệnh.
    assert "price_multiplier" in goi, (
        "walkforward.py gọi dong_so_sach mà không gọi price_multiplier — "
        "giá thô theo nghìn đồng sẽ đóng mọi lệnh mồ côi ở −99,90%")
    print("PASS  walkforward có gọi dong_so_sach (xác nhận bằng AST)")


def test_dong_so_sach_NEM_khi_sai_don_vi(so_lenh):
    """Nghìn đồng gặp VNĐ — bẫy trong bảng "hỏng âm thầm" của
    NGUYEN-TAC-DO-LUONG.md, và nó đã xảy ra thật ngày 24/08/2026 ngay khi
    `dong_so_sach` vừa ra đời.

    Bốn lệnh HET_DU_LIEU trong lượt OOS đều đúng −99,90% — không phải bốn
    mã cùng sập, mà là giá thô 23,27 đứng cạnh giá vào 23.440. Bốn lệnh đó
    kéo kỳ vọng OOS từ +0,616% xuống −0,419%.

    Nổ chứ không tự sửa: tự nhân 1000 nghĩa là đoán xem người gọi ĐỊNH nói
    gì, và đoán sai thì không ai biết.
    """
    _mo(so_lenh, "AAA")
    so_lenh.fill_pending("AAA", "2026-03-03", 23_440.0)
    with pytest.raises(ValueError, match="DON VI"):
        so_lenh.dong_so_sach("AAA", "2026-03-10", 23.27)
    print("PASS  giá thô nghìn đồng -> nổ, không ghi -99,9%")


def test_dong_so_sach_KHONG_nem_voi_bien_dong_that(so_lenh):
    """Chốt phải rộng hơn mọi biến động giá có thể có.

    Biên độ sàn 7–15% một phiên; kể cả một lệnh giữ lâu rồi rơi 60% vẫn
    phải đi qua. Chốt bắt ở mức lệch 10 LẦN, không phải 10 phần trăm.
    """
    _mo(so_lenh, "AAA")
    so_lenh.fill_pending("AAA", "2026-03-03", 23_440.0)
    so_lenh.dong_so_sach("AAA", "2026-03-10", 9_000.0)      # -61,6%
    t = [x for x in so_lenh.all_trades() if x.symbol == "AAA"][0]
    assert t.status == "CLOSED" and t.exit_price == 9_000.0
    print("PASS  rơi 61,6% vẫn đóng bình thường")


def test_dong_so_sach_khong_nem_khi_chua_co_gia_vao(so_lenh):
    """Lệnh PENDING chưa có `entry_price` — không có gì để đối chiếu."""
    _mo(so_lenh, "AAA")
    assert so_lenh.dong_so_sach("AAA", "2026-03-10", 0.001) == 1
    print("PASS  PENDING không entry_price -> xoá, không nổ")


def _co_C5_trong_ma_nguon() -> bool:
    """Giá trị `CHO_PHEP_MO_LENH_MOI` ĐỌC TỪ NGUỒN `paper_trading.py`.

    **Không** đọc `pt.CHO_PHEP_MO_LENH_MOI`. Ba file test gán cờ đó ở mức
    MODULE (`test_google_sheets_sync`, `test_paper_trading`,
    `test_sheets_store`) và pytest nạp mọi module lúc collect, nên giá trị
    lúc chạy do THỨ TỰ COLLECT quyết định chứ không do mã nguồn.

    Đo 07/09/2026, cùng một test, khác mỗi danh sách file truyền vào:

        pytest tests/test_tran_von_cam_ket.py -k cong_MO
            -> re nhanh SKIP  (cong DONG, dung voi ma nguon)

        pytest tests/test_paper_trading.py tests/test_tran_von_cam_ket.py
               -k cong_MO
            -> "PASS  cong MO · tran 100% ..."   trong khi cong dang DONG

    `test_c5_noi_that.py::test_cong_C5_dang_DONG_trong_ma_nguon` đã giải
    xong việc này từ trước và docstring của nó nói thẳng lý do; file này
    không đọc nó nên lặp lại đúng lỗi ấy.
    """
    import ast
    import os

    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cay = ast.parse(open(os.path.join(goc, "paper_trading.py"),
                         encoding="utf-8").read())
    gan = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "CHO_PHEP_MO_LENH_MOI"
                   for t in n.targets)]
    assert len(gan) == 1, f"gán CHO_PHEP_MO_LENH_MOI {len(gan)} lần"
    assert isinstance(gan[0].value, ast.Constant), ast.dump(gan[0].value)
    return bool(gan[0].value.value)


def test_cong_MO_thi_ba_thu_bao_ve_phai_CO_MAT():
    """Cổng C5 mở thì trần vốn và điều kiện đóng lại phải tồn tại.

    Buộc ba thứ đi cùng nhau. Mở cổng mà không có trần là mời lại đúng cơ
    chế sinh ra +636,11% (sổ thật từng chạm 208% vốn cam kết). Mở cổng mà
    không có điều kiện đóng lại nêu trước thì ngày phải đóng, điều kiện sẽ
    được chế ra sau khi đã nhìn số.

    Điều kiện rẽ nhánh đọc từ NGUỒN — xem `_co_C5_trong_ma_nguon`.
    """
    if not _co_C5_trong_ma_nguon():
        print("SKIP  cổng đang đóng")
        return
    import paper_metrics as pm
    assert pt.TRAN_VON_CAM_KET_PCT <= 100.0, (
        f"cổng MỞ mà trần vốn {pt.TRAN_VON_CAM_KET_PCT}% > 100% — đòn bẩy ẩn")
    assert hasattr(pm, "dieu_kien_dong_lai"), (
        "cổng MỞ mà không có điều kiện đóng lại nêu trước")
    import run_daily
    assert run_daily.BUY_THRESHOLD == pt.BUY_THRESHOLD, (
        f"cổng MỞ mà đường chạy thật dùng ngưỡng {run_daily.BUY_THRESHOLD} "
        f"trong khi mọi phép đo ngoài mẫu đo ở {pt.BUY_THRESHOLD}")
    print(f"PASS  cổng MỞ · trần {pt.TRAN_VON_CAM_KET_PCT:.0f}% · "
          f"ngưỡng {pt.BUY_THRESHOLD} · có điều kiện đóng lại")
