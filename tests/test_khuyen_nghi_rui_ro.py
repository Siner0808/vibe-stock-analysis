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


def _phan_tich_day_du() -> dict:
    """Cả kết quả `analyze()`, không chỉ khối `recommendations`."""
    rng = np.random.default_rng(7)
    n = 300
    gia = 16.0 * np.cumprod(1 + rng.normal(0, 0.015, n))
    df = pd.DataFrame({
        "time": pd.bdate_range("2025-01-01", periods=n),
        "open": gia, "high": gia * 1.01, "low": gia * 0.99,
        "close": gia, "volume": rng.integers(1e5, 1e6, n),
    })
    goi = MarketDataPacket(symbol="TEST", exchange="HOSE", ohlcv_df=df)
    return RiskManagementAgent().analyze(goi)


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


def test_RR_la_SO_va_chia_dung_HAI_PHAN_TRAM_hien_ra():
    """`risk_reward_ratio` phải là SỐ, và phải bằng thương của đúng hai con
    số nằm cạnh nó trên màn hình.

    Vì sao chia hai con số ĐÃ LÀM TRÒN chứ không chia hai phân số gốc:
    người đọc thấy `+20.0%` và `-4.7%` rồi chia nhẩm. Tính từ phân số chưa
    làm tròn cho 4,23 trong khi mắt thấy 4,26 — một chênh lệch nhỏ mà
    không ai giải thích được, và đúng loại lệch mà lỗi 69 sinh ra từ đó.

    KHÔNG trừ chi phí vòng (`paper_metrics.ROUND_TRIP_COST_PCT` = 0,46%),
    cũng vì lý do ấy: một RR đã trừ chi phí sẽ không còn bằng thương của
    hai số hiện ra. Chi phí được nói ở chỗ khác, không nhét vào đây.
    """
    r = _khuyen_nghi()
    rr = r["risk_reward_ratio"]
    assert isinstance(rr, (int, float)) and not isinstance(rr, bool), (
        f"risk_reward_ratio = {rr!r} — phải là SỐ. Nó từng là câu chữ "
        f'"Fat-Tail (Trailing Stop 7% từ đỉnh)", và hai nơi in nó ra cho '
        f"người đọc như một tỷ lệ.")

    mong = r["take_profit_pct"] / r["stop_loss_pct"]
    assert abs(float(rr) - mong) <= 0.01, (
        f"RR khai {rr} nhưng hai con số hiện ra cho "
        f"{r['take_profit_pct']}/{r['stop_loss_pct']} = {mong:.4f}")

    # Biên suy từ chính hai cái kẹp trong mã: TP1 co dinh 20%, SL kep
    # trong 4,0-6,5% -> RR nam tron trong [3,08 ; 5,00].
    assert 3.0 <= float(rr) <= 5.01, (
        f"RR = {rr} nằm ngoài dải suy được từ hai cái kẹp của mã "
        f"(TP1 20% · SL 4,0–6,5%). Một trong hai cái kẹp đã đổi.")
    print(f"PASS  RR = {rr}:1 = {r['take_profit_pct']}/{r['stop_loss_pct']}")


def test_DUONG_GIAO_DICH_chi_doc_BA_khoa_GIA_tu_khoi_khuyen_nghi():
    """Gác AN TOÀN cho mọi lần sửa khối `recommendations` sau này.

    `paper_trading.consider_entry` ĐỌC khối này — nên sửa nó KHÔNG mặc
    nhiên là sửa hiển thị. Đo 16/09/2026 bằng AST: nó đọc đúng **ba** khoá,
    cả ba là GIÁ. Không khoá `*_pct` nào, không `risk_reward_ratio`.

    Vì thế lượt đổi lỗi 69 và lượt đổi RB này **không thể** chạm kết quả
    giao dịch. Gác này giữ cho câu ấy còn đúng: thêm một khoá hiển thị vào
    đường sinh lệnh thì đỏ ở đây, ngay lúc thêm.
    """
    import ast
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    doc_duoc = set()
    for n in ast.walk(cay):
        if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                and n.value.id == "risk"
                and isinstance(n.slice, ast.Constant)):
            doc_duoc.add(n.slice.value)
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get"
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "risk" and n.args
                and isinstance(n.args[0], ast.Constant)):
            doc_duoc.add(n.args[0].value)

    # PHEP KIEM DUNG CU: mot luot quet ra rong thi "khong khoa nao la" la
    # ket luan tu mot mau khong the cho ket qua duong -- dung dieu bat buoc
    # sinh ra tu loi 66.
    assert doc_duoc, ("lượt quét AST ra RỖNG — máy quét hỏng, không phải "
                      "đường giao dịch đã thôi đọc khối khuyến nghị")

    CHO_PHEP = {"entry_price", "stop_loss_price", "take_profit_price"}
    thua = doc_duoc - CHO_PHEP
    assert not thua, (
        f"đường sinh lệnh nay đọc thêm {sorted(thua)} từ khối khuyến nghị. "
        f"Khối ấy vốn là HIỂN THỊ; thêm một khoá vào đây là biến một lượt "
        f"sửa giao diện thành một lượt sửa kết quả.")
    print(f"PASS  đường giao dịch đọc đúng {sorted(doc_duoc)}")


def test_CHINH_SACH_TRAILING_khong_mat_khi_RR_thanh_so():
    """Cái chuỗi cũ mang một thông tin THẬT — đừng đánh rơi nó.

    `risk_reward_ratio` từng là *"Fat-Tail (Trailing Stop 7% từ đỉnh)"*.
    Trailing 7% có thật: `paper_trading.py` đặt `trail_sl = close_p * 0.93`
    và chỉ nâng lên. Đổi ô ấy thành số mà không nói lại chính sách ở đâu
    khác là xoá một thứ đo được.

    Nó chuyển sang `signals`, nơi hai luật Break-Even và Pyramiding đã nằm.
    """
    r = RiskManagementAgent()
    ra = _phan_tich_day_du()
    tin = " ".join(ra.get("signals", []))
    assert "Trailing" in tin and "7" in tin, (
        f"không tín hiệu nào còn nói tới chính sách trailing: "
        f"{ra.get('signals')}")
    assert "đỉnh" not in tin, (
        "nhãn vẫn ghi 'từ đỉnh'. Mã dùng `close_p * 0.93` — giá ĐÓNG CỬA, "
        "không phải `high`. Đo 16/09/2026.")
    print("PASS  chính sách trailing vẫn được nói ra, và nói đúng mã")


def _phan_tich_SL_TRONG_LONG() -> dict:
    """Một chuỗi giá mà stop-loss KHÔNG chạm hai cái kẹp 4,0 / 6,5.

    Mẫu mặc định (`sigma` 0,015) cho biến động năm 22% nên `sl_fraction`
    bị kẹp xuống đúng sàn **4,0%**, và khi ấy 20,0/4,0 = 5,0 dù tính bằng
    cách nào. Tức mẫu ấy **không phân biệt được** hai thiết kế — đúng cái
    bẫy lỗi 66: một kết quả âm rút từ mẫu nằm ngoài vùng phép thử phân
    biệt được thì nói về MẪU, không nói về giả thuyết.

    `sigma` 0,028 cho biến động ~44,5%, `sl_fraction` 0,0556 nằm trong
    lòng khoảng. Dò 16/09/2026: 54 tổ hợp (sigma, seed) phân biệt được.
    """
    rng = np.random.default_rng(6)
    n = 300
    gia = 16.0 * np.cumprod(1 + rng.normal(0, 0.028, n))
    df = pd.DataFrame({
        "time": pd.bdate_range("2025-01-01", periods=n),
        "open": gia, "high": gia * 1.01, "low": gia * 0.99,
        "close": gia, "volume": rng.integers(1e5, 1e6, n),
    })
    goi = MarketDataPacket(symbol="TEST2", exchange="HOSE", ohlcv_df=df)
    return RiskManagementAgent().analyze(goi)


def test_RR_chia_HAI_SO_HIEN_RA_chu_khong_chia_hai_phan_so_goc():
    """Trên mẫu KHÔNG chạm kẹp, hai thiết kế cho hai con số khác nhau.

    Đây là chỗ quyết định của cả lượt sửa, và nó chỉ đo được ở đây.
    """
    ra = _phan_tich_SL_TRONG_LONG()
    r = ra["recommendations"]
    sl_pct, tp_pct = r["stop_loss_pct"], r["take_profit_pct"]

    assert 4.0 < sl_pct < 6.5, (
        f"mẫu cho stop-loss {sl_pct}% — CHẠM cái kẹp, nên hai thiết kế ra "
        f"cùng một số và phép kiểm dưới không đo gì. Đổi mẫu.")

    tu_hien_ra = round(tp_pct / sl_pct, 2)
    sl_fraction = max(0.04, min(0.065,
                                ra["metrics"]["volatility_annual"] / 800.0))
    tu_phan_so = round((tp_pct / 100.0) / sl_fraction, 2)

    # PHEP KIEM DUNG CU: mau nay CO kha nang cho ket qua duong hay khong.
    assert abs(tu_hien_ra - tu_phan_so) >= 0.02, (
        f"hai thiết kế cùng cho {tu_hien_ra} trên mẫu này — mẫu KHÔNG phân "
        f"biệt được, phép kiểm dưới vô nghĩa dù xanh hay đỏ")

    assert abs(float(r["risk_reward_ratio"]) - tu_hien_ra) < 0.005, (
        f"RR = {r['risk_reward_ratio']} — nó đang chia hai PHÂN SỐ GỐC "
        f"({tu_phan_so}) chứ không chia hai con số HIỆN RA "
        f"({tp_pct}/{sl_pct} = {tu_hien_ra}). Người đọc chia nhẩm hai số "
        f"trên màn hình sẽ không ra con số này.")
    print(f"PASS  RR = {r['risk_reward_ratio']} = {tp_pct}/{sl_pct}, "
          f"không phải {tu_phan_so} (chia phân số gốc)")


def test_HAI_NOI_IN_RR_deu_kem_hau_to_MOT():
    """`RR=3.57` trần thì mơ hồ — 3,57 cái gì trên cái gì.

    Gác này đọc VĂN BẢN, và đó là hợp lệ ở đây vì thứ đang canh CHÍNH LÀ
    một chuỗi định dạng. `CLAUDE.md` mục *"Gác phải đọc AST"* chừa đúng
    ngoại lệ ấy: *"gác dạng văn bản chỉ còn dùng cho thứ thật sự là văn
    bản"*.
    """
    for ten in ("master_agent.py", "debate_agents.py"):
        for so, dong in enumerate(
                (GOC / ten).read_text(encoding="utf-8").splitlines(), 1):
            if "risk_reward_ratio" not in dong or dong.lstrip().startswith("#"):
                continue
            if "rec.get(" in dong or "rec[" in dong and "f\"" not in dong:
                continue
            assert ":1" in dong, (
                f"{ten}:{so} in RR mà không kèm ':1' — một con số trần "
                f"không nói được nó là tỷ lệ:\n  {dong.strip()}")
    print("PASS  cả hai nơi in RR đều kèm ':1'")


def _bull_phan_bac(khuyen_nghi: dict | None) -> str:
    """Chạy thật vòng 2 của Bull với một lời Bear có chữ "rủi ro"."""
    from debate_agents import BullAdvocateAgent, DebateArgument
    bear = [DebateArgument(agent_name="bear", stance="BEAR", round_num=1,
                           statement="Rủi ro quá lớn ở vùng giá này",
                           score_impact=-1.0)]
    risk = {} if khuyen_nghi is None else {"recommendations": khuyen_nghi}
    ra = BullAdvocateAgent().argue({"risk": risk}, 2, bear)
    return ra.statement


def test_LUAN_DIEM_RR_chi_phat_ra_khi_CO_SO():
    """Ba con số bịa sẵn 7 / 17 / "2.5:1" đã bị gỡ — và chỗ gỡ phải ĐO được.

    Bản trước dùng `rec.get("stop_loss_pct", 7)` v.v., nên khi khối khuyến
    nghị vắng mặt thì Bull vẫn phát ra *"Stop-loss chỉ -7%, upside +17%,
    RR 2.5:1"* — ba con số **không ai đo**, trong một câu tự giới thiệu là
    *"rủi ro đã được ĐỊNH LƯỢNG"*. Đó đúng luật R4 của
    `tools/chan_bia_so_lieu.py`.

    Nay không có số thì không có luận điểm. Bất biến 5 của
    `NGUYEN-TAC-DO-LUONG.md` đứng sau điều này: *"R:R cao làm σ tăng"* —
    một tỷ lệ không phải bằng chứng, nên một tỷ lệ BỊA lại càng không.
    """
    co_so = _bull_phan_bac(_khuyen_nghi())
    assert "Risk:Reward" in co_so and ":1" in co_so, (
        f"có đủ số mà luận điểm không phát ra: {co_so!r}")

    khong_so = _bull_phan_bac(None)
    assert "Risk:Reward" not in khong_so, (
        f"khối khuyến nghị VẮNG MẶT mà luận điểm định lượng vẫn phát ra — "
        f"nghĩa là nó đang in số bịa:\n  {khong_so!r}")
    for bia in ("-7%", "+17%", "2.5:1"):
        assert bia not in khong_so, f"con số bịa {bia} vẫn còn: {khong_so!r}"
    print("PASS  luận điểm Risk:Reward im khi không có số")


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
