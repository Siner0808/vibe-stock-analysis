"""Gác cho khối `recommendations` của `analysis_agents.RiskManagementAgent`.

VÌ SAO FILE NÀY RA ĐỜI (16/09/2026)
───────────────────────────────────
`analysis_agents.py` tính cắt lỗ và chốt lời hiện ra cho NGƯỜI đọc rồi tự
quyết định. Tra `tools/ho_so.py` sáng 16/09: **0 tham chiếu** — không test
nào import nó, không BƯỚC nào nhắc nó, không dòng bảng lỗi nào chạm nó.
File dày nhất repo có 27; file này có 0.

Và chỗ tối ấy giấu một thứ: hai khoá tên `*_pct` mang CÂU CHỮ, trong khi
năm nơi tiêu thụ in chúng kèm hậu tố `%`. Chạy thật đường ấy in ra:

    chatbot_agent.py:202   TP1: 10,299 VND (+Không giới hạn%)
    master_agent.py:291    TP1=10,299 VND (+Không giới hạn%)
    master_agent.py:287    TP2 Trailing=11,157 VND (+Vô cực%)
    debate_agents.py:84    Stop-loss chi -4.0%, tiem nang upside +Không giới hạn%.

Dòng cuối nặng nhất: tầng tranh luận dựng một luận điểm Risk:Reward đặt
một rủi ro ĐÃ ĐỊNH LƯỢNG cạnh một lợi nhuận KHÔNG GIỚI HẠN — trong khi
giá đi kèm là **đúng +20,0%**. Lỗi 69.

MỘT KHOÁ CỐ Ý KHÔNG NẰM TRONG GÁC NÀY
─────────────────────────────────────
`risk_reward_ratio` cũng là chuỗi (*"Fat-Tail (Trailing Stop 7% từ
đỉnh)"*). Nó **không** bị gác ở đây vì không nơi nào in nó kèm `%` — nó
hiện nguyên câu, và câu ấy đọc được. Sửa nó đòi chốt *"tỷ lệ tính tới
mục tiêu nào"*, một quyết định thuộc về người dùng chứ không thuộc về
một lượt dọn dẹp. Ghi ra để nó là ngoại lệ ĐƯỢC KHAI, không phải một
lớp bị quét hụt.
"""
import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

from analysis_agents import RiskManagementAgent  # noqa: E402
from data_collectors import MarketDataPacket  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BO_QUA = {".venv", "backtest", "scratch", ".git", "__pycache__"}
DUNG_SAI_DIEM = 0.15


def _khuyen_nghi() -> dict:
    """Chạy thật agent trên một chuỗi giá tất định.

    `docs/HANDOFF.md` ràng buộc 3: *claim về HÀNH VI của một hàm phải
    chứng minh bằng CHẠY hàm đó.* Đọc thấy `tp1_fraction = 0.20` ở dòng
    khởi tạo không chứng minh được khối `recommendations` nói gì.
    """
    rng = np.random.default_rng(7)
    n = 300
    gia = 16.0 * np.cumprod(1 + rng.normal(0, 0.015, n))
    df = pd.DataFrame({
        "time": pd.bdate_range("2025-01-01", periods=n),
        "open": gia, "high": gia * 1.01, "low": gia * 0.99,
        "close": gia, "volume": rng.integers(1e5, 1e6, n),
    })
    goi = MarketDataPacket(symbol="TEST", exchange="HOSE", ohlcv_df=df)
    return RiskManagementAgent().analyze(goi)["recommendations"]


def _quet_pct_chuoi(goc: Path) -> list[tuple[str, int, str, str]]:
    """Mọi khoá `*_pct` trong một dict literal mà giá trị là CHUỖI.

    Đọc AST, không đọc `in` — `CLAUDE.md` mục *"Gác phải đọc AST"*.
    """
    ra = []
    for p in sorted(goc.rglob("*.py")):
        # TƯƠNG ĐỐI với `goc`, không tuyệt đối. Repo thật nằm dưới một thư
        # mục tên `scratch`, mà `scratch` có trong BO_QUA — lọc theo đường
        # tuyệt đối thì lượt quét tự loại hết và in ra `0 chỗ`, nghe y hệt
        # "repo sạch". Bản đầu của máy quét ngày 16/09 sai đúng thế, và
        # phép kiểm dụng cụ ngay dưới là thứ bắt được.
        if any(x in p.relative_to(goc).parts for x in BO_QUA):
            continue
        try:
            cay = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(cay):
            if not isinstance(n, ast.Dict):
                continue
            for k, v in zip(n.keys, n.values):
                if (isinstance(k, ast.Constant) and isinstance(k.value, str)
                        and k.value.endswith("_pct")
                        and isinstance(v, ast.Constant)
                        and isinstance(v.value, str)):
                    ra.append((str(p.relative_to(goc)).replace("\\", "/"),
                               k.lineno, k.value, v.value))
    return ra


def test_MAY_QUET_bat_duoc_hinh_dang_da_biet(tmp_path):
    """PHÉP KIỂM DỤNG CỤ, và nó phải sống LÂU HƠN lần sửa.

    Gác dưới khẳng định *"repo không còn chỗ nào"* — một kết quả ÂM. Sau
    khi lỗi 69 được vá thì quần thể thật rỗng, nên lượt quét ấy không còn
    chứng minh được nó có khả năng thấy gì. Test này dựng lại hình dạng
    trong một thư mục tạm để câu hỏi *"máy quét có thấy được không"* luôn
    có câu trả lời ĐO ĐƯỢC.

    Đúng điều bắt buộc sinh ra từ lỗi 66: trước khi tin một kết quả âm,
    hỏi mẫu này CÓ KHẢ NĂNG cho kết quả dương không.
    """
    (tmp_path / "gia_dinh.py").write_text(
        'D = {"take_profit_pct": "Khong gioi han", "stop_loss_pct": 6.5}\n',
        encoding="utf-8")
    ra = _quet_pct_chuoi(tmp_path)
    assert [(k, v) for _, _, k, v in ra] == [
        ("take_profit_pct", "Khong gioi han")], (
        f"máy quét không thấy hình dạng đã biết, hoặc bắt nhầm số: {ra}")
    print("PASS  máy quét thấy được hình dạng đã biết")


def test_KHONG_con_khoa_pct_nao_mang_CHUOI_trong_repo():
    """Quét cả lớp, không chỉ hai ca — `docs/HANDOFF.md` ràng buộc 5.

    *"Sửa một chỗ là sửa một chỗ, không phải sửa một lớp."* Đo 16/09/2026
    trên 175 file: đúng 3 chỗ, cả ba trong `analysis_agents.py`, và chỉ
    hai chỗ tên `*_pct` là hỏng thật.
    """
    con = _quet_pct_chuoi(GOC)
    assert not con, "khoá phần trăm mang câu chữ:\n" + "\n".join(
        f"  {f}:{d}  {k} = {v!r}" for f, d, k, v in con)
    print("PASS  không khoá `*_pct` nào mang chuỗi")


def test_PCT_khop_voi_GIA_cung_cap():
    """Hai vế do agent tự sinh phải nói cùng một chuyện.

    Đây KHÔNG phải "test kiểm lại chính nó": nó không dựng lại công thức
    của mã, nó đối chiếu HAI ĐẦU RA độc lập của cùng một lượt chạy — giá
    và phần trăm. Một đột biến chỉ chạm một vế thì đỏ.
    """
    r = _khuyen_nghi()
    vao = float(r["entry_price"])
    assert vao > 0, "giá vào phải dương"

    for khoa_gia, khoa_pct, chieu in (
            ("take_profit_price", "take_profit_pct", +1),
            ("tp2_price", "tp2_pct", +1),
            ("stop_loss_price", "stop_loss_pct", -1)):
        pct = r[khoa_pct]
        assert isinstance(pct, (int, float)) and not isinstance(pct, bool), (
            f"{khoa_pct} = {pct!r} — phải là SỐ. Năm nơi in nó kèm hậu tố "
            f"`%`, nên một câu chữ ở đây ra thành `+{pct}%`.")
        suy_ra = (float(r[khoa_gia]) / vao - 1.0) * 100.0 * chieu
        assert abs(suy_ra - float(pct)) <= DUNG_SAI_DIEM, (
            f"{khoa_pct} khai {pct} nhưng {khoa_gia} suy ra {suy_ra:.2f}")

    print(f"PASS  TP1 +{r['take_profit_pct']}% · TP2 +{r['tp2_pct']}% · "
          f"SL -{r['stop_loss_pct']}%, cả ba khớp giá cùng cặp")


if __name__ == "__main__":
    import tempfile
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_") and callable(ham):
            if "tmp_path" in ham.__code__.co_varnames[:ham.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as t:
                    ham(Path(t))
            else:
                ham()
    print("\nTAT CA XANH")
