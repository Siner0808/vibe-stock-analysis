"""Cỡ vị thế phải SUY RA từ số vị thế mục tiêu, không gõ tay.

VÌ SAO CÓ FILE NÀY
Trước 31/08/2026, `consider_entry` gõ thẳng `account_risk_pct = 1.0` và
chốt `max(5.0, min(33.3, size))`. Ba con số rời rạc, không nối với nhau và
không nối với `TRAN_VON_CAM_KET_PCT`. Hệ quả: số vị thế đồng thời là một
KẾT QUẢ PHỤ của ba hằng số, chứ không phải một lựa chọn ai đó đã ra.

Đo được ngày 31/08 (chế độ theo ngày, vùng IS, 71 mã): **4,2 vị thế trung
bình, đỉnh 7**. Chú thích ở `paper_trading.py` đoán 5,3 — gần, nhưng nó là
một phép suy chứ không phải phép đo, và không ai kiểm lại suốt nhiều tháng.

CÁI BẪY FILE NÀY CANH
`CLAUDE.md`: *"Khoá cấu hình không ai đọc nguy hiểm hơn code không ai
chạy. Code chết thì im lặng; núm vặn giả thì mời người ta vặn."* Thêm
`SO_VI_THE_MUC_TIEU` mà `consider_entry` vẫn dùng hằng số cũ thì đúng là
một núm vặn giả — và nó tệ hơn tình trạng trước, vì bây giờ trông như đã
sửa rồi.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import paper_trading as pt


def test_moi_con_so_deu_SUY_RA_tu_so_vi_the_muc_tieu():
    """Một lựa chọn (15) + một phép đo (stop trung vị) -> bốn con số."""
    assert pt.CO_MUC_TIEU_PCT == pt.TRAN_VON_CAM_KET_PCT / pt.SO_VI_THE_MUC_TIEU
    assert pt.RUI_RO_MOI_LENH_PCT == pt.CO_MUC_TIEU_PCT * pt.SL_TRUNG_VI
    assert pt.CO_TOI_THIEU_PCT == round(pt.CO_MUC_TIEU_PCT / 2, 1)
    assert pt.CO_TOI_DA_PCT == round(pt.CO_MUC_TIEU_PCT * 2, 1)
    print(f"PASS  {pt.SO_VI_THE_MUC_TIEU} vị thế -> cỡ TB "
          f"{pt.CO_MUC_TIEU_PCT:.2f}% · rủi ro {pt.RUI_RO_MOI_LENH_PCT:.4f}% "
          f"· chốt [{pt.CO_TOI_THIEU_PCT} ; {pt.CO_TOI_DA_PCT}]")


def _co(sl_pct_dist: float, so_vi_the: int | None = None) -> float:
    """Dựng lại đúng phép tính của `consider_entry`, cho `so_vi_the` bất kỳ."""
    n = so_vi_the or pt.SO_VI_THE_MUC_TIEU
    co_muc_tieu = pt.TRAN_VON_CAM_KET_PCT / n
    rui_ro = co_muc_tieu * pt.SL_TRUNG_VI
    size = rui_ro / max(0.03, sl_pct_dist)
    return round(max(round(co_muc_tieu / 2, 1),
                     min(round(co_muc_tieu * 2, 1), size)), 1)


def test_stop_TRUNG_VI_cho_ra_dung_co_muc_tieu():
    """Nếu không thì `SL_TRUNG_VI` đang là một con số của luật stop KHÁC."""
    co = _co(pt.SL_TRUNG_VI)
    assert abs(co - pt.CO_MUC_TIEU_PCT) < 0.1, (
        f"stop trung vị cho {co}%, mục tiêu {pt.CO_MUC_TIEU_PCT:.2f}%")
    print(f"PASS  stop trung vị {pt.SL_TRUNG_VI} -> {co}% "
          f"(mục tiêu {pt.CO_MUC_TIEU_PCT:.2f}%)")


def test_van_giu_RISK_PARITY_chu_khong_phai_co_co_dinh():
    """Stop rộng hơn thì vị thế PHẢI nhỏ hơn. Mất tính chất này thì đây chỉ
    là cỡ cố định đội lốt, và rủi ro mỗi lệnh thôi bằng nhau."""
    hep, giua, rong = _co(0.04), _co(0.0515), _co(0.065)
    assert hep > giua > rong, f"không đơn điệu: {hep} · {giua} · {rong}"
    assert hep / rong > 1.4, f"dải quá hẹp ({hep} vs {rong}) — gần như cố định"
    print(f"PASS  stop 4,0% -> {hep}% · 5,15% -> {giua}% · 6,5% -> {rong}%")


def test_VAN_num_KHONG_phai_num_gia():
    """Vặn `SO_VI_THE_MUC_TIEU` thì cỡ vị thế phải đổi THẬT.

    Đây là bất biến đắt nhất của file. Một núm vặn không nối vào đâu còn
    tệ hơn không có núm: nó mời người ta tin rằng đã sửa.
    """
    for n in (5, 10, 15, 30):
        co = _co(pt.SL_TRUNG_VI, n)
        muc_tieu = pt.TRAN_VON_CAM_KET_PCT / n
        assert abs(co - muc_tieu) < 0.1, f"{n} vị thế -> {co}%, cần {muc_tieu:.2f}%"
    assert _co(pt.SL_TRUNG_VI, 5) > _co(pt.SL_TRUNG_VI, 30), "núm vặn ngược"
    print("PASS  5 · 10 · 15 · 30 vị thế đều ra đúng cỡ tương ứng")


# ══ GÁC AST — khẳng định "consider_entry CÓ DÙNG" phải chứng minh trên cây

def _ham_consider_entry() -> ast.FunctionDef:
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    return [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)
            and n.name == "consider_entry"][0]


def _gan(ten: str) -> ast.AST:
    """Vế phải của phép gán ở mức module cho `ten`."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    for n in cay.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) \
                and n.targets[0].id == ten:
            return n.value
    raise AssertionError(f"không tìm thấy phép gán {ten}")


def test_cong_thuc_suy_dung_HINH_DANG_chu_khong_chi_dung_GIA_TRI():
    """Đột biến `TRAN * N / 225` cho ĐÚNG 6,667 tại N=15 — mọi phép so giá
    trị đều mù với nó, kể cả `CO_MUC_TIEU × N == TRAN`. Nhưng núm vặn khi
    đó chạy NGƯỢC: nhiều vị thế hơn lại cho cỡ TO hơn.

    Đây là lý do `CLAUDE.md` bắt mọi khẳng định về hành vi phải đi qua AST.
    Bản đầu của file này dựng lại công thức trong chính test (`_co`) nên nó
    kiểm công thức của test, không kiểm công thức của mã.
    """
    v = _gan("CO_MUC_TIEU_PCT")
    assert isinstance(v, ast.BinOp) and isinstance(v.op, ast.Div), (
        "CO_MUC_TIEU_PCT phải là một phép CHIA — nhân là núm vặn ngược")
    assert isinstance(v.left, ast.Name) and v.left.id == "TRAN_VON_CAM_KET_PCT"
    assert isinstance(v.right, ast.Name) and v.right.id == "SO_VI_THE_MUC_TIEU"

    r = _gan("RUI_RO_MOI_LENH_PCT")
    assert isinstance(r, ast.BinOp) and isinstance(r.op, ast.Mult)
    assert {x.id for x in (r.left, r.right) if isinstance(x, ast.Name)} == \
        {"CO_MUC_TIEU_PCT", "SL_TRUNG_VI"}
    print("PASS  CO_MUC_TIEU = TRẦN / SỐ_VỊ_THẾ · RỦI_RO = CỠ × STOP_TRUNG_VỊ")


def test_consider_entry_THAT_SU_doc_ba_hang_so_moi():
    """Gác dạng `"RUI_RO" in src` vô dụng: chuỗi đó nằm sẵn trong chú thích
    của chính `paper_trading.py`."""
    h = _ham_consider_entry()
    ten = {n.id for n in ast.walk(h) if isinstance(n, ast.Name)}
    for c in ("RUI_RO_MOI_LENH_PCT", "CO_TOI_THIEU_PCT", "CO_TOI_DA_PCT"):
        assert c in ten, f"consider_entry KHÔNG đọc {c} — núm vặn giả"
    print("PASS  consider_entry đọc cả ba hằng số suy ra")


def test_KHONG_con_hang_so_co_ghim_trong_consider_entry():
    """1.0 / 5.0 / 33.3 còn sót lại là bản sao — nó không sai vào ngày ra
    đời, nó sai vào ngày bản gốc đổi và nó thì không."""
    h = _ham_consider_entry()
    so = {n.value for n in ast.walk(h)
          if isinstance(n, ast.Constant) and isinstance(n.value, float)}
    for xau in (5.0, 33.3):
        assert xau not in so, f"còn hằng số cỡ vị thế cũ {xau} trong hàm"
    print(f"PASS  không còn 5.0 / 33.3 ghim trong consider_entry "
          f"(còn lại: {sorted(so)})")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
