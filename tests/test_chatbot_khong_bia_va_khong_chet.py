"""`chatbot_agent.py`: khối rủi ro phải CHẠY ĐƯỢC, và không con số nào được bịa.

VÌ SAO CÓ FILE NÀY (17/09/2026, lỗi 78)
───────────────────────────────────────
Đi tìm việc treo *"TP1 là mục tiêu chỉ-để-hiện"* thì gặp một thứ khác hẳn.

**Một.** `_fallback_answer` có ba nhánh trên giấy, và nhánh QUẢN TRỊ RỦI RO
nằm **sau một `return`** trong cùng khối `if`. Đo bằng AST: **11 dòng trên
37 dòng** của hàm là mã chết. Và nó sẽ **nổ** nếu chạy — `risk_recs` lẫn
`entry_str` chưa bao giờ được gán ở đâu. Đo bằng cách CHẠY: bốn câu hỏi
rủi ro đều rơi xuống nhánh trả lời chung.

**Hai.** File này mang **18 trên 28** cảnh báo `chan_bia_so_lieu` của cả
repo — nhiều hơn mọi file khác cộng lại. Mỗi cảnh báo là một
`.get(khoa, <số>)`: thiếu dữ liệu thì người đọc nhận `Trend 50/100`,
`SL -5.0%`, `TP +10.0%`. Ba con số ấy còn **lệch khỏi chính máy**: TP1 của
`analysis_agents` là **+20%**, TP2 là **+30%**.

**Ba.** Khối chết ấy hứa *"Take-Profit TP1 (Chốt 50% vốn)"* và *"Trailing
Stop (Gồng 50% còn lại)"* — mô tả một cơ chế **thoát một phần** mà dự án
không có ở bất kỳ đường nào.

Cảnh báo `chan_bia_so_lieu` đã kêu đúng chỗ này suốt nhiều tuần. Nó không
được đọc vì bản tin chỉ in một con số tổng — và `docs/HANDOFF.md` mục 1
còn dặn *"số cảnh báo thì đổi, không phải tiêu chí"*. Nên với RIÊNG file
này, cảnh báo nay là một bức tường.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import chan_bia_so_lieu as cb  # noqa: E402
import chatbot_agent as ca  # noqa: E402

NGUON = GOC / "chatbot_agent.py"

#: Bộ khuyến nghị THẬT, hình dạng đúng như `analysis_agents.py` trả về.
RISK_THAT = {
    "entry_price": 66000.0,
    "entry_range": "65.670 - 66.330",
    "stop_loss_price": 62300.0,
    "stop_loss_pct": 5.6,
    "take_profit_price": 79200.0,
    "take_profit_pct": 20.0,
    "tp2_price": 85800.0,
    "tp2_pct": 30.0,
    "suggested_position_size_pct": 12.5,
}

DUNG = (ast.Return, ast.Raise, ast.Continue, ast.Break)


def _cau_lenh_chet(than) -> list:
    """Câu lệnh nằm SAU một `return`/`raise`/`continue`/`break` cùng khối."""
    ra, da_dung = [], False
    for c in than:
        if da_dung:
            ra.append(c)
        if isinstance(c, DUNG):
            da_dung = True
        for khoi in ("body", "orelse", "finalbody"):
            if hasattr(c, khoi):
                ra += _cau_lenh_chet(getattr(c, khoi))
    return ra


def _chet_trong_file(p: Path) -> list[tuple[int, str]]:
    cay = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    chet = _cau_lenh_chet(cay.body)
    for n in ast.walk(cay):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            chet += _cau_lenh_chet(n.body)
    return sorted({(c.lineno, type(c).__name__) for c in chet})


# ══ 1. Không mã chết — và luật này TOÀN REPO ═══════════════════════════
#: Lọc theo đường dẫn TƯƠNG ĐỐI với gốc repo, KHÔNG theo `p.parts` tuyệt
#: đối. Repo này nằm trong một thư mục tên `scratch`, nên một phép lọc
#: tuyệt đối loại sạch mọi file và máy đo im lặng báo "0 dòng chết" cho
#: một lượt quét 0 file. Đã mắc đúng thế ngày 16/09/2026, và mắc lại hôm
#: nay — thứ bắt được cả hai lần là phép tự kiểm `quet > 100`.
BO_QUA = {".venv", "__pycache__", "backtest", "brain", "scratch"}


def test_KHONG_FILE_NAO_trong_repo_co_CAU_LENH_CHET():
    """Đo 17/09/2026 sau khi sửa: **0 file · 0 dòng** trên cả repo.

    Nên đây là một tính chất ĐANG CÓ, không phải một mong muốn — cùng lối
    với `test_MOI_HINH_DANG_XAU_thuoc_ve_DUNG_MOT_LUAT`.

    Một câu lệnh sau `return` không đỏ ở đâu cả: nó nạp được, cú pháp
    đúng, và mọi test đi qua nhánh khác vẫn xanh. Thứ duy nhất nhìn thấy
    nó là AST.
    """
    xau = []
    quet = 0
    for p in sorted(GOC.rglob("*.py")):
        if any(x in p.relative_to(GOC).parts for x in BO_QUA):
            continue
        quet += 1
        try:
            chet = _chet_trong_file(p)
        except SyntaxError:
            continue
        if chet:
            xau.append(f"{p.relative_to(GOC).as_posix()}: {chet}")
    assert quet > 100, f"chi quet duoc {quet} file — phep kiem nay mu"
    assert not xau, "có câu lệnh KHÔNG BAO GIỜ CHẠY:\n  " + "\n  ".join(xau)
    print(f"PASS  {quet} file .py · 0 câu lệnh chết")


# ══ 2. Không con số bịa trong chính file này ═══════════════════════════
def test_chatbot_agent_KHONG_CON_mot_canh_bao_BIA_SO_nao():
    """Với RIÊNG file này, cảnh báo là một BỨC TƯỜNG chứ không phải ghi chú.

    Đo 17/09/2026: **18 → 0**. Cả repo đi từ 28 xuống 10.
    """
    pt = cb.kiem_tra(NGUON)
    assert not pt, (
        f"{len(pt)} cảnh báo bịa số trong chatbot_agent.py:\n  "
        + "\n  ".join(f"dòng {x.dong}: {x.thong_diep}" for x in pt))
    print("PASS  chatbot_agent.py: 0 cảnh báo bịa số")


# ══ 3. Nhánh rủi ro phải TỚI ĐƯỢC ═════════════════════════════════════
def _tra_loi(hoi: str, risk=None, breakdown=None) -> str:
    bot = ca.StockChatbotAgent()
    return bot._fallback_answer(
        hoi, "FPT", "HOSE", 71, "MUA", breakdown or {}, ["lý do 1"],
        {"risk": {"recommendations": risk if risk is not None else RISK_THAT}})


def test_MOI_TU_KHOA_RUI_RO_deu_TOI_DUOC_khoi_rui_ro():
    """Nhánh này nằm sau một `return` từ khi file ra đời tới 17/09/2026.

    Gọi thẳng `_tra_loi_rui_ro` KHÔNG chứng minh được gì — lượt sửa đầu
    tiên làm đúng thế và bỏ sót một `NameError` ở chính nhánh điều kiện.
    Phải đi qua `_fallback_answer`, tức đúng đường người dùng đi.
    """
    assert ca.TU_KHOA_RUI_RO, "danh sach tu khoa RONG — nhanh nay khong the toi"
    for tu in ca.TU_KHOA_RUI_RO:
        ra = _tra_loi(f"cho tôi biết {tu} thế nào")
        assert "Quản trị rủi ro" in ra, (
            f"từ khoá {tu!r} KHÔNG tới được khối rủi ro:\n{ra[:200]}")
    print(f"PASS  {len(ca.TU_KHOA_RUI_RO)} từ khoá, tất cả tới được")


def test_CAU_HOI_KHAC_khong_bi_keo_vao_khoi_rui_ro():
    """Vế còn lại của cặp — một nhánh nuốt mọi câu hỏi cũng là một lỗi."""
    for hoi in ("hôm nay thế nào", "mã này là gì", "so với VNINDEX"):
        ra = _tra_loi(hoi)
        assert "Quản trị rủi ro" not in ra, f"{hoi!r} bị kéo vào khối rủi ro"


def test_KHOI_RUI_RO_in_dung_SO_THAT_va_du_nam_muc():
    ra = _tra_loi("cắt lỗ ở đâu")
    for mong in ("66,000", "62,300", "5.6", "79,200", "20.0",
                 "85,800", "30.0", "12.5"):
        assert mong in ra, f"thiếu số thật {mong!r} trong khối rủi ro"
    assert "5. " in ra, "thiếu mục thứ năm"


# ══ 4. Thiếu dữ liệu thì NÓI LÀ THIẾU ═════════════════════════════════
def test_THIEU_DU_LIEU_thi_KHONG_BAO_GIO_thanh_mot_CON_SO():
    """Ba con số bịa cũ — 5.0 · 10.0 · 20.0 · 15.0 — không được quay lại.

    Và chúng còn lệch khỏi máy: TP1 thật là +20%, TP2 thật là +30%.
    """
    ra = _tra_loi("cắt lỗ ở đâu", risk={"entry_price": 66000.0})
    assert "chưa đo được" in ra
    # `0 VNĐ` phải viết kèm dấu nháy ngược mở: nó là CHUỖI CON của
    # `66,000 VNĐ`, nên bản đầu của phép kiểm này đỏ trên một đầu ra ĐÚNG.
    for bia in ("-5.0%", "+10.0%", "+20.0%", "15.0%", "`0 VNĐ`"):
        assert bia not in ra, f"con số bịa {bia!r} quay lại khi thiếu dữ liệu"


def test_KHONG_CO_DU_LIEU_thi_noi_thang_chu_khong_dung_bang_rong():
    ra = _tra_loi("cắt lỗ ở đâu", risk={})
    assert "Chưa có dữ liệu" in ra
    assert "1." not in ra, "vẫn dựng bảng dù không có gì để điền"


def test_DIEM_AGENT_thieu_thi_KHONG_thanh_50():
    """50 là điểm TRUNG TÍNH — in nó khi thiếu là phát ra một phán quyết."""
    ra = _tra_loi("tại sao khuyến nghị vậy", breakdown={})
    assert "chưa đo được" in ra
    assert "`50/100`" not in ra, "điểm thiếu vẫn in ra 50"


def test_FINAL_SCORE_thieu_thi_KHONG_thanh_50_o_duong_THAT():
    """Đi qua `answer_question` — đường người dùng đi, không phải hàm con.

    `final_score` thiếu mà in `50/100` là in ra đúng điểm trung tính: một
    phán quyết *"không nghiêng về đâu"* mà không phép đo nào đứng sau. Và
    nó đi thẳng vào ngữ cảnh nạp cho Gemini, tức được một mô hình đọc rồi
    diễn giải tiếp — con số bịa được rửa qua một tầng nữa.
    """
    bot = ca.StockChatbotAgent()
    bot.api_key = None
    ra = bot.answer_question(
        "hôm nay thế nào",
        {"symbol": "FPT", "score_breakdown": {}, "key_reasons": [],
         "analyses": {"risk": {"recommendations": RISK_THAT}}})
    assert "50/100" not in ra, "final_score thiếu vẫn in ra 50"
    assert "chưa đo được" in ra


# ══ 5. Không hứa một cơ chế KHÔNG TỒN TẠI ═════════════════════════════
def test_KHONG_HUA_thoat_MOT_PHAN_vi_du_an_KHONG_CO_co_che_do():
    """*"Chốt 50% vốn"* · *"Gồng 50% còn lại"* mô tả một thành phần không có.

    Cùng lớp với hai ô bị gỡ khỏi giao diện ngày 21/08/2026 — nhãn
    `Pha C — Wyckoff Spring` và ô `Fundamental Agent · BCTC Q2`.
    """
    ra = _tra_loi("chốt lời ở đâu")
    for hua in ("50% vốn", "50% còn lại", "Chốt lời 2 Tầng", "Chốt 50%"):
        assert hua not in ra, (
            f"câu trả lời còn hứa `{hua}` — dự án không có cơ chế thoát "
            f"một phần")
    assert "thoát MỘT PHẦN nào" in ra, "không nói ra rằng cơ chế ấy không có"

    # Và lời văn KHÔNG được tự trích lại câu đã gỡ: bản đầu của khối này
    # giải thích mình bằng cách nhắc nguyên văn *"Chốt 50% vốn"*, nên
    # chính nó lại chứa câu ấy — và phép kiểm trên đỏ trên một đầu ra
    # đúng ý. Người đọc không cần biết một khối mã chết từng viết gì.
    van = NGUON.read_text(encoding="utf-8")
    assert "Chốt lời 2 Tầng" not in van, "tiêu đề cũ còn trong nguồn"


def test_KHOI_RUI_RO_phai_NOI_RA_rang_TP_khong_phai_loi_thoat_cua_may():
    """Việc treo gốc: *"TP1 là mục tiêu chỉ-để-hiện"*.

    `analysis_agents.py` đã ghi điều đó trong chú thích từ 16/09/2026.
    Nhưng chú thích thì người dùng không đọc — câu trả lời thì có.
    """
    ra = _tra_loi("chốt lời ở đâu")
    assert "THAM CHIẾU" in ra
    assert "CHOT_LOI_CUNG" in ra, "không nêu tên cờ để người đọc tra lại"
    for loi_thoat in ("STOP_LOSS", "SIGNAL_REVERSED", "HET_DU_LIEU"):
        assert loi_thoat in ra, f"không kể lối thoát THẬT {loi_thoat}"
