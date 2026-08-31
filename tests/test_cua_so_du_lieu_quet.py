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

File này khoá bốn thứ:
  1. cửa sổ đủ dài để `SMA200` tính được — sàn suy từ CƠ CHẾ, không từ ý thích;
  2. cửa sổ là một HẰNG SỐ CÓ TÊN, không phải con số nằm giữa thân hàm;
  3. máy quét không bao giờ nhìn ít hơn giao diện — hai nơi lệch nhau thì
     người dùng thấy một điểm và máy vào lệnh theo một điểm khác;
  4. và — thêm 31/08/2026 — cửa sổ THẬT SỰ NHẬN ĐƯỢC phải được đo mỗi lượt
     quét, vì ba thứ trên chỉ nói về cửa sổ mã nguồn XIN.
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


def _timeout_phut(ten_file: str, job: str) -> int:
    """`timeout-minutes` của một job, đọc bằng tay — KHÔNG dùng PyYAML.

    `kiem-dinh.yml` chỉ cài `requirements.txt` (cộng `pytest`), và PyYAML
    KHÔNG nằm trong đó. Bản đầu của test này `import yaml`: xanh ở máy vì
    streamlit kéo theo PyYAML, đỏ trên runner sạch —
    `ModuleNotFoundError: No module named 'yaml'`, chặn merge PR.

    Thêm một phụ thuộc vào `requirements.txt` chỉ để một test đọc được
    một con số là trả giá ở đường chạy sản xuất cho tiện lợi của test.
    File workflow là của chính dự án và đủ đơn giản để đọc bằng tay.
    """
    dong = (GOC / ".github" / "workflows" / ten_file).read_text(
        encoding="utf-8").splitlines()
    trong_job = False
    for d in dong:
        if d.strip().startswith("#"):
            continue
        if d.startswith(f"  {job}:"):
            trong_job = True
            continue
        if not trong_job:
            continue
        # Thụt lề đúng 2 dấu cách = sang job khác.
        if d.strip() and d.startswith("  ") and not d.startswith("   "):
            break
        if d.strip().startswith("timeout-minutes:"):
            return int(d.split(":", 1)[1].strip())
    raise AssertionError(f"{ten_file}: không thấy timeout-minutes của job {job}")


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
    tm = _timeout_phut("quet-so-lenh.yml", "quet")
    can = 40 if rd.NGAY_LICH_SU >= 1000 else 25
    assert tm >= can, (
        f"cửa sổ {rd.NGAY_LICH_SU} ngày cần timeout-minutes ≥ {can}, "
        f"workflow đang để {tm}")
    print(f"PASS  cửa sổ {rd.NGAY_LICH_SU} ngày · timeout {tm} phút ≥ {can}")


# ══ CỬA SỔ XIN ĐƯỢC ≠ CỬA SỔ NHẬN ĐƯỢC ══════════════════════════════════
#
# Năm phép kiểm trên đo cửa sổ mã nguồn **xin**. Không phép nào biết máy
# chủ thật sự **trả về** bao nhiêu. Hai lý do phải đo cả vế kia:
#
#   • Đo ngày 31/08/2026 tại máy local: xin từ 2023-09-01, nhận về từ
#     2023-07-10 — nguồn không trả đúng khoảng được hỏi.
#   • `CLAUDE.md` ghi thẳng rằng gói **miễn phí** trên runner chưa bao giờ
#     được đo ở đại lượng này ("Chưa đo: gói miễn phí có phục vụ nổi 420
#     ngày OHLCV cho cổ phiếu không").
#
# Một cửa sổ bị cắt âm thầm tái tạo ĐÚNG lỗi ngày 29/08: ngưỡng 62 hiệu
# chuẩn trên phân phối điểm của cửa sổ dài, đem áp lên điểm của cửa sổ
# ngắn. Nên mỗi lượt quét phải tự đo lấy, và phải nói ra được TỪ XA —
# nhật ký chạy đòi đăng nhập, annotation thì không.


def _ham(ten: str):
    """Hàm mức module của `run_daily.py`, đọc từ cây cú pháp."""
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"run_daily.py không có hàm {ten}")


def test_cua_so_bi_cat_thi_PHAI_keu():
    """44 phiên trên kỳ vọng 747 — đúng cấu hình đã lật 6/71 quyết định."""
    _, canh = rd.bao_cua_so_du_lieu([44] * 71, 747, "2026-08-28")
    assert canh, "cửa sổ 44/747 phiên mà không cảnh báo gì"
    assert "44" in canh and "747" in canh, canh
    assert str(rd.BUY_THRESHOLD) in canh, (
        "cảnh báo phải nói rõ ngưỡng nào đang bị áp lên một phân phối khác")
    print(f"PASS  44/747 phiên -> kêu")


def test_du_phien_thi_IM():
    """Kêu cả khi không có việc gì là dạy người ta bỏ qua chuông."""
    _, canh = rd.bao_cua_so_du_lieu([784] * 71, 747, "2026-08-28")
    assert canh == "", canh
    print("PASS  784/747 phiên -> im")


def test_khong_co_ky_vong_thi_KHONG_ket_luan():
    """Không dựng được kỳ vọng thì NÓI RA, không bịa một con số thay thế.

    Một kỳ vọng bịa ra đẻ ra cảnh báo giả hoặc im lặng giả — cả hai đều
    tệ hơn việc nói thẳng là chưa đo được.
    """
    dong, canh = rd.bao_cua_so_du_lieu([44] * 71, None, "không có chuỗi VN-INDEX")
    assert canh == "", "chưa có kỳ vọng mà đã kết luận bị cắt"
    assert "chưa so được" in dong, dong
    print("PASS  thiếu kỳ vọng -> nói ra, không kết luận")


def test_dong_do_luon_dem_ma_duoi_moc_SMA():
    """50 phiên là mốc CƠ CHẾ — phải đếm được, không chỉ suy từ trung vị."""
    dong, _ = rd.bao_cua_so_du_lieu([44, 44, 300, 784], 747, "2026-08-28")
    assert "2 mã dưới 50 phiên" in dong, dong
    print("PASS  đếm đúng 2 mã dưới mốc SMA50")


def test_nguong_ty_le_la_hang_so_co_ten():
    """Đặt tên cho một giả định là bước đầu để ai đó cãi nó."""
    assert isinstance(rd.TY_LE_PHIEN_TOI_THIEU, float)
    assert 0.5 <= rd.TY_LE_PHIEN_TOI_THIEU <= 0.9, rd.TY_LE_PHIEN_TOI_THIEU
    print(f"PASS  TY_LE_PHIEN_TOI_THIEU = {rd.TY_LE_PHIEN_TOI_THIEU}")


def test_ky_vong_hong_thi_tra_None_chu_khong_no(monkeypatch):
    """Phép đo hỏng không được làm chết lượt quét nó đang đo."""
    def no():
        raise RuntimeError("mất mạng")
    monkeypatch.setattr(rd.market_filter, "get_vni_df", no)
    ky_vong, ly_do = rd.phien_ky_vong("2023-09-01", "2026-08-31")
    assert ky_vong is None and "RuntimeError" in ly_do, (ky_vong, ly_do)
    print("PASS  nguồn hỏng -> (None, lý do), không ném")


def test_may_quet_THAT_SU_goi_phep_do():
    """Test đúng mà dây chưa cắm — đúng lỗi `vs_benchmark` đã mắc."""
    ham = _ham("execute_daily_scan")
    goi = {n.func.id for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "bao_cua_so_du_lieu" in goi, "execute_daily_scan không gọi phép đo"
    assert "phien_ky_vong" in goi, "execute_daily_scan không dựng kỳ vọng"
    print("PASS  execute_daily_scan gọi cả hai hàm đo")


def test_canh_bao_di_bang_warning_KHONG_phai_error():
    """Làm đỏ lượt quét ở đây là sinh ra một báo động giả che mất chuông.

    `tools/chuong_bao_quet.py` đếm `conclusion == "success"` của workflow
    "Quét sổ lệnh" để biết một ngày có được quét không. Một cảnh báo thật
    làm job đỏ sẽ khiến chuông kia báo "ngày này không có lượt quét nào".

    Đọc hằng chuỗi trong CÂY CÚ PHÁP chứ không grep: chú thích ngay trên
    khối này có nhắc cả `::warning::` lẫn `::error::`, nên một phép kiểm
    dạng `in src` sẽ xanh kể cả khi mã nguồn làm ngược lại.
    """
    ham = _ham("execute_daily_scan")
    khoi = [n for n in ast.walk(ham) if isinstance(n, ast.If)
            and isinstance(n.test, ast.Name) and n.test.id == "_dong_canh"]
    assert len(khoi) == 1, f"thấy {len(khoi)} khối cảnh báo cửa sổ, phải 1"
    chu = "".join(n.value for n in ast.walk(khoi[0])
                  if isinstance(n, ast.Constant) and isinstance(n.value, str))
    assert "::warning::" in chu, chu
    assert "::error::" not in chu, (
        "cảnh báo cửa sổ đi bằng ::error:: sẽ làm đỏ lượt quét")
    print("PASS  cảnh báo cửa sổ đi bằng ::warning::")


def test_phep_do_khong_no_voi_dau_vao_ky_quac():
    """Dụng cụ đo hỏng phải BÁO, không được làm sập thứ nó đang đo."""
    for phien, ky_vong in [([], 747), ([0], 747), ([44] * 71, 0),
                           ([44] * 71, -5), ([1], None), ([784], 1)]:
        dong, canh = rd.bao_cua_so_du_lieu(phien, ky_vong, "2026-08-28")
        assert isinstance(dong, str) and isinstance(canh, str), (phien, ky_vong)
    print("PASS  6 đầu vào kỳ quặc -> đều trả về hai chuỗi")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
