"""Cửa sổ dữ liệu của máy quét phải đủ dài để agent xu hướng sống.

VÌ SAO CÓ FILE NÀY
──────────────────
`run_daily.py` từng lấy `now - 60 ngày` = **44 phiên**. Đo ngày 29/08/2026
trên cả 71 mã (xem `docs/STATE.md` — "BƯỚC 2 — ĐO CHỖ TỐI"):

  • gói vnstock miễn phí ↔ tài trợ : |lệch| 0,46 điểm · đổi quyết định 0/67
  • TradingView thật ↔ không có    : |lệch| 0,59 điểm · đổi quyết định 0/71
  • cửa sổ 44 phiên ↔ 301 phiên    : |lệch| 5,86 điểm · **đổi 6/71**

Cơ chế: `_compute_local_indicators()` trả `None` cho `SMA50` dưới 50 phiên
và `SMA200` dưới 200 phiên. Thiếu chúng thì các luật của agent xu hướng
dùng chúng bị bỏ qua, và `trend_score` kẹt trong 35/50/65 — không bao giờ
chạm 100 hay 15.

Vì sao đó là lỗi chứ không phải lựa chọn: ngưỡng 62 do Phase 5D chọn bằng
walk-forward, mà `walkforward.py:213` truyền `df.iloc[: t + 1]` — cửa sổ
MỞ RỘNG, hàng trăm phiên. **Ngưỡng được hiệu chuẩn trên một phân phối điểm
khác với phân phối nó đang được áp lên.** Ba trong bốn lệnh tiến-về-trước
đầu tiên (NAF, TCB, HUT) chỉ tồn tại vì cửa sổ ngắn.

File này khoá ba thứ:
  1. cửa sổ đủ dài để `SMA200` tính được — sàn suy từ CƠ CHẾ, không từ ý thích;
  2. cửa sổ là một HẰNG SỐ CÓ TÊN, không phải con số nằm giữa thân hàm;
  3. máy quét không bao giờ nhìn ít hơn giao diện — hai nơi lệch nhau thì
     người dùng thấy một điểm và máy vào lệnh theo một điểm khác.
"""
import ast
import sys
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import run_daily as rd  # noqa: E402
from data_collectors import DataOrchestrator  # noqa: E402

#: Phiên / ngày lịch, đo thật: 44/60 = 0,733 · 301/420 = 0,717.
#: Lấy 0,66 cho chắc — sàn phải là sàn kể cả năm nhiều ngày nghỉ.
PHIEN_MOI_NGAY = 0.66

#: `_compute_local_indicators` cần đúng ngần này phiên cho SMA200.
PHIEN_CAN_CHO_SMA200 = 200


def _hang_so(ten_file: str, ten: str):
    """Đọc hằng số mức module bằng AST — `app.py` là script Streamlit,
    import nó sẽ chạy cả giao diện."""
    cay = ast.parse((GOC / ten_file).read_text(encoding="utf-8"))
    for n in cay.body:
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == ten for t in n.targets):
            return ast.literal_eval(n.value)
    raise AssertionError(f"{ten_file} không có hằng số {ten}")


def test_cua_so_du_dai_de_SMA200_tinh_duoc():
    phien = rd.NGAY_LICH_SU * PHIEN_MOI_NGAY
    assert phien >= PHIEN_CAN_CHO_SMA200, (
        f"{rd.NGAY_LICH_SU} ngày lịch ≈ {phien:.0f} phiên < "
        f"{PHIEN_CAN_CHO_SMA200}. SMA200 sẽ là None, agent xu hướng mất "
        f"luật dài hạn, và trend_score kẹt trong 35/50/65 — đúng lỗi đo "
        f"được ngày 29/08/2026.")
    print(f"PASS  {rd.NGAY_LICH_SU} ngày ≈ {phien:.0f} phiên ≥ "
          f"{PHIEN_CAN_CHO_SMA200}")


def test_cua_so_KHONG_phai_con_so_nam_giua_than_ham():
    """Một con số nằm giữa hàm 300 dòng thì không ai thấy nó là một lựa chọn."""
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef)
               and n.name == "execute_daily_scan")
    gan = [n for n in ast.walk(ham) if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "start_date"
                   for t in n.targets)]
    assert len(gan) == 1, f"gán start_date {len(gan)} lần"
    ten = {x.id for x in ast.walk(gan[0].value) if isinstance(x, ast.Name)}
    assert "NGAY_LICH_SU" in ten, (
        f"start_date không dùng hằng số NGAY_LICH_SU (thấy: {sorted(ten)})")
    print("PASS  cửa sổ đi qua hằng số có tên")


def test_may_quet_khong_nhin_it_hon_giao_dien():
    app = _hang_so("app.py", "NGAY_LICH_SU_PHAN_TICH")
    assert rd.NGAY_LICH_SU >= app, (
        f"máy quét {rd.NGAY_LICH_SU} ngày < giao diện {app} ngày. Người "
        f"dùng sẽ thấy một điểm, máy vào lệnh theo một điểm khác.")
    print(f"PASS  máy quét {rd.NGAY_LICH_SU} ≥ giao diện {app} ngày")


def _khung(n: int) -> pd.DataFrame:
    """Chuỗi giá tăng đều — chỉ cần ĐỦ DÀI, không cần giống thật."""
    return pd.DataFrame({
        "time": pd.date_range("2020-01-01", periods=n, freq="D"),
        "open": [100.0 + i * 0.1 for i in range(n)],
        "high": [101.0 + i * 0.1 for i in range(n)],
        "low": [99.0 + i * 0.1 for i in range(n)],
        "close": [100.0 + i * 0.1 for i in range(n)],
        "volume": [1_000_000.0] * n,
    })


def test_co_che_SMA_bien_mat_duoi_nguong():
    """Chứng minh bằng CHẠY: đây là lý do cửa sổ ngắn làm liệt agent xu hướng."""
    o = DataOrchestrator("FPT", "", "")
    for n, co_sma50, co_sma200 in ((44, False, False),
                                   (60, True, False),
                                   (250, True, True)):
        ind = o._compute_local_indicators(_khung(n))
        assert (ind.get("SMA50") is not None) is co_sma50, (n, ind.get("SMA50"))
        assert (ind.get("SMA200") is not None) is co_sma200, (n, ind.get("SMA200"))
    print("PASS  44 phiên: mất cả SMA50 lẫn SMA200 · 60: mất SMA200 · 250: đủ")


def test_cua_so_dai_thi_workflow_phai_duoc_noi_thoi_gian():
    """Cửa sổ dài mà không nới thời gian = một phiên quét chết giữa chừng.

    Đo thật 29/08/2026: 420 ngày → 2,35 s/mã (71 mã ≈ 4,0 phút);
    1095 ngày → 8,88 s/mã (71 mã ≈ 11,7 phút). Job có SÁU bước, nên
    25 phút cho cửa sổ 1095 là quá sát.
    """
    import yaml
    d = yaml.safe_load(
        (GOC / ".github" / "workflows" / "quet-so-lenh.yml").read_text(
            encoding="utf-8"))
    tm = d["jobs"]["quet"]["timeout-minutes"]
    can = 40 if rd.NGAY_LICH_SU >= 1000 else 25
    assert tm >= can, (
        f"cửa sổ {rd.NGAY_LICH_SU} ngày cần timeout-minutes ≥ {can}, "
        f"workflow đang để {tm}")
    print(f"PASS  cửa sổ {rd.NGAY_LICH_SU} ngày · timeout {tm} phút ≥ {can}")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
