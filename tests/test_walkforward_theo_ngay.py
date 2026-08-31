"""Backtest chạy theo NGÀY thay vì theo MÃ — điều kiện để trần vốn có nghĩa.

VÌ SAO CẦN CHẾ ĐỘ NÀY
`_mo_phong` bản gốc chạy `for sym ... for t`: xong toàn bộ lịch sử FPT rồi
mới sang ACB. Cộng với chốt `elif self.open_position(symbol) is not None`
trong `consider_entry` (một mã chỉ giữ một vị thế), số vị thế đồng thời
THẬT ở chế độ đó luôn bằng **1**.

Hệ quả, và nó lớn hơn vẻ ngoài:

  • `TRAN_VON_CAM_KET_PCT` KHÔNG BAO GIỜ chạm. Các con số đòn bẩy 145% /
    524% / 1372% trong mọi báo cáo walk-forward do
    `paper_metrics._capital_deployment` dựng lại từ chồng lấn LỊCH sau khi
    việc đã rồi — chúng mô tả một danh mục máy chưa bao giờ nắm.
  • Mọi thay đổi về CỠ VỊ THẾ đều vô hình. Giảm `size_pct` để giữ 15 vị thế
    thay vì 5 chỉ co đường vốn lại, không sinh thêm một lệnh nào.

BẤT BIẾN CHÍNH CỦA FILE NÀY
Đổi chế độ chỉ được đổi **THỨ TỰ**, không được đổi **TẬP** phiên được chấm.
Đổi tập phiên là đổi dữ liệu đầu vào chứ không phải đổi cách chạy — và hai
chế độ khi đó không còn so được với nhau, nên phép đo "15 vị thế so với 5"
sẽ đo cả sự khác biệt lẫn cái lỗi.

Mặc định là THEO MÃ. Không con số walk-forward nào đã công bố được đổi âm
thầm; muốn chế độ mới thì phải nói ra.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pandas as pd

import walkforward as wf

MIN_HIST, STRIDE = 3, 1


def _df(tu: str, so_phien: int) -> pd.DataFrame:
    ngay = pd.bdate_range(tu, periods=so_phien).strftime("%Y-%m-%d")
    n = len(ngay)
    return pd.DataFrame({"time": ngay, "open": [10.0] * n, "high": [10.4] * n,
                         "low": [9.7] * n, "close": [10.1] * n,
                         "volume": [1_000_000] * n})


def _bo_du_lieu() -> dict:
    """Ba mã có khoảng ngày LỆCH nhau — nếu trùng khít thì phép kiểm xen kẽ
    thành hiển nhiên và không bắt được gì."""
    return {"ACB": _df("2024-01-02", 12),
            "FPT": _df("2024-01-08", 12),
            "HPG": _df("2024-01-15", 12)}


def _tap_phien_theo_ma(du_lieu: dict) -> set:
    """Tập (mã, chỉ số hàng) mà vòng lặp THEO MÃ sẽ chấm."""
    return {(sym, t) for sym, df in du_lieu.items()
            for t in range(MIN_HIST, len(df), STRIDE)}


def test_lich_xep_theo_NGAY_khong_theo_ma():
    """Khoá đầu tiên phải là ngày. Xếp theo mã thì chế độ này vô nghĩa."""
    lich = wf.lich_theo_ngay(_bo_du_lieu(), MIN_HIST, STRIDE)
    ngay = [x[0] for x in lich]
    assert ngay == sorted(ngay), "lịch không xếp theo ngày"
    assert len(lich) > 0
    print(f"PASS  {len(lich)} phiên xếp theo ngày, {ngay[0]} → {ngay[-1]}")


def test_doi_che_do_KHONG_doi_TAP_phien():
    """BẤT BIẾN CHÍNH. Chỉ đổi thứ tự, không đổi tập.

    Mất hoặc thêm một phiên thì hai chế độ đo hai bộ dữ liệu khác nhau, và
    phép so giữa chúng không còn nói lên điều gì.
    """
    du_lieu = _bo_du_lieu()
    theo_ngay = {(sym, t) for _, sym, t in
                 wf.lich_theo_ngay(du_lieu, MIN_HIST, STRIDE)}
    theo_ma = _tap_phien_theo_ma(du_lieu)
    assert theo_ngay == theo_ma, (
        f"lệch {len(theo_ngay ^ theo_ma)} phiên giữa hai chế độ")
    print(f"PASS  hai chế độ chấm ĐÚNG cùng {len(theo_ma)} phiên")


def test_lich_TAT_DINH_du_thu_tu_dict_khac():
    """Bất biến 2: cùng gói dữ liệu phải cho cùng kết quả.

    Không có khoá phụ là mã thì thứ tự trong một ngày phụ thuộc thứ tự
    duyệt dict — và hai lượt chạy ra hai kết quả khác nhau đúng vào ngày
    trần vốn chạm.
    """
    a = _bo_du_lieu()
    b = {k: a[k] for k in reversed(list(a))}
    assert wf.lich_theo_ngay(a, MIN_HIST, STRIDE) == \
        wf.lich_theo_ngay(b, MIN_HIST, STRIDE)
    print("PASS  đảo thứ tự dict -> lịch không đổi")


def test_che_do_theo_ngay_THAT_SU_xen_ke_cac_ma():
    """Chứng minh chế độ này KHÔNG phải vòng theo mã đội lốt.

    Phải có ngày mà nhiều mã cùng được chấm — đó chính là điều kiện để
    nhiều vị thế cùng mở, tức để trần vốn có gì mà chặn.
    """
    lich = wf.lich_theo_ngay(_bo_du_lieu(), MIN_HIST, STRIDE)
    theo_ngay: dict = {}
    for ngay, sym, _ in lich:
        theo_ngay.setdefault(ngay, set()).add(sym)
    nhieu_ma = [n for n, s in theo_ngay.items() if len(s) > 1]
    assert nhieu_ma, "không ngày nào có quá một mã — các mã không hề xen kẽ"

    # Và thứ tự thật phải khác vòng theo mã, nếu không đây là no-op.
    tu_lich = [(sym, t) for _, sym, t in lich]
    tuan_tu = [(sym, t) for sym in sorted(_bo_du_lieu())
               for t in range(MIN_HIST, 12, STRIDE)]
    assert tu_lich != tuan_tu, "thứ tự y hệt vòng theo mã"
    print(f"PASS  {len(nhieu_ma)} ngày có nhiều mã cùng chấm · thứ tự khác hẳn")


# ══ BA GÁC ĐỌC AST — khẳng định về HÀNH VI phải chứng minh trên cây ═════
#
# Gác dạng `"theo_ngay" in src` vô dụng ở đây: chính khối chú thích đầu
# file này đã chứa chuỗi đó.

def _ham(ten: str) -> ast.FunctionDef:
    cay = ast.parse((GOC / "walkforward.py").read_text(encoding="utf-8"))
    return [n for n in ast.walk(cay)
            if isinstance(n, ast.FunctionDef) and n.name == ten][0]


def _ten_goi(node) -> set:
    return {n.func.id for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def test_mac_dinh_la_THEO_MA():
    """Bật mặc định là đổi âm thầm mọi con số walk-forward đã công bố."""
    for ten in ("_mo_phong", "chay"):
        h = _ham(ten)
        vt = [a.arg for a in h.args.args].index("theo_ngay")
        mac_dinh = h.args.defaults[vt - (len(h.args.args) - len(h.args.defaults))]
        assert mac_dinh.value is False, f"{ten}: theo_ngay mặc định KHÔNG phải False"
    print("PASS  cả _mo_phong lẫn chay đều mặc định theo MÃ")


def test_hai_che_do_dung_CHUNG_mot_lenh_cham_phien():
    """Hai bản sao của lời gọi `run_session` là chỗ hai chế độ trôi ra khỏi
    nhau — và khi đó phép so giữa chúng đo cả sự khác biệt lẫn cái lỗi."""
    h = _ham("_mo_phong")
    assert "run_session" not in _ten_goi(h), (
        "_mo_phong gọi thẳng run_session — hai chế độ sẽ có hai bản sao")
    nhanh = [n for n in ast.walk(h) if isinstance(n, ast.If)
             and isinstance(n.test, ast.Name) and n.test.id == "theo_ngay"][0]
    for than, ten in ((nhanh.body, "theo ngày"), (nhanh.orelse, "theo mã")):
        goi = set().union(*(_ten_goi(x) for x in than))
        assert "_chay_mot_phien" in goi, f"nhánh {ten} không dùng bản dùng chung"
    print("PASS  hai nhánh dùng chung `_chay_mot_phien`, không có bản sao")


def test_nhanh_theo_ngay_THAT_SU_dung_lich_theo_ngay():
    """Nếu không có gác này, nhánh `theo_ngay` chạy y hệt vòng theo mã mà
    MỌI test khác vẫn xanh — đột biến số 7 đã sống sót đúng như vậy.

    Lý do lọt: các test kia kiểm `lich_theo_ngay` như một hàm THUẦN, còn
    hai gác AST chỉ đòi nhánh gọi `_chay_mot_phien` — điều mà bản no-op
    vẫn làm. Khoảng trống nằm ở chỗ nối hai thứ đó lại.
    """
    h = _ham("_mo_phong")
    nhanh = [n for n in ast.walk(h) if isinstance(n, ast.If)
             and isinstance(n.test, ast.Name) and n.test.id == "theo_ngay"][0]
    trong_nhanh = set().union(*(_ten_goi(x) for x in nhanh.body))
    assert "lich_theo_ngay" in trong_nhanh, (
        "nhánh theo_ngay KHÔNG gọi lich_theo_ngay — nó đang chạy theo mã")
    trong_else = set().union(*(_ten_goi(x) for x in nhanh.orelse))
    assert "lich_theo_ngay" not in trong_else, (
        "nhánh theo MÃ lại dùng lịch theo ngày — hai chế độ đã lẫn vào nhau")
    print("PASS  nhánh theo ngày dùng lịch theo ngày, nhánh theo mã thì không")


def test_che_do_theo_ngay_dong_so_SAU_toan_bo_vong():
    """Đóng sổ giữa chừng thì lệnh của mã sau bị đóng oan bởi mã trước.

    Ở chế độ theo mã, "hết dữ liệu của một mã" nghĩa là tới lượt mã sau nên
    đóng ngay là đúng. Ở chế độ theo ngày thì không — các mã chạy xen kẽ.
    """
    h = _ham("_mo_phong")
    nhanh = [n for n in ast.walk(h) if isinstance(n, ast.If)
             and isinstance(n.test, ast.Name) and n.test.id == "theo_ngay"][0]
    vong_cham = [n for n in ast.walk(ast.Module(body=nhanh.body, type_ignores=[]))
                 if isinstance(n, ast.For)
                 and "_chay_mot_phien" in _ten_goi(n)]
    assert vong_cham, "nhánh theo ngày không có vòng chấm phiên nào"
    for v in vong_cham:
        assert "_dong_so_cuoi" not in _ten_goi(v), (
            "đóng sổ nằm TRONG vòng chấm phiên — mã sau bị đóng oan")
    goi_nhanh = set().union(*(_ten_goi(x) for x in nhanh.body))
    assert "_dong_so_cuoi" in goi_nhanh, "nhánh theo ngày không đóng sổ lần nào"
    print("PASS  theo ngày: đóng sổ nằm ngoài vòng chấm phiên")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
