"""BƯỚC 285 — khung tranh luận trên app hiện ĐÚNG TỪNG VÒNG; gác đọc AST của `app.py` và chạy biểu thức dựng ô.

Chỉ HIỂN THỊ. Lỗi (BƯỚC 284 tìm bằng đọc mã, BƯỚC 285 xác nhận bằng chạy `DebateModerator` trên dữ liệu dựng):
app gom phát biểu vào ba biến `bull_msg` · `bear_msg` · `bull2_msg` rồi dán ba ô cố định. Vòng 3 ghi đè vòng 2,
nên ô "🐂 Bull — Vòng 2" hiện lời của vòng 3, ô Bear hiện lời vòng 3 dưới nhãn không số vòng, và lời vòng 2 của
Bear không hiện ở đâu cả.

Ba gác:

1. HIỆN: chạy ĐÚNG biểu thức dựng ô của `app.py` (lấy từ cây AST, không dựng lại công thức) trên kết quả
   tranh luận thật (hình dạng như `master_agent`) và trên kết quả dựng; lời của mỗi vòng nằm dưới đúng nhãn
   "Vòng n" của nó, cho cả Bull và Bear.
2. NHÃN KHÔNG GÕ TAY: không chuỗi nào trong `app.py` mang "Vòng <số>"; số vòng điền từ chỉ số của
   `enumerate(rounds, start=1)`.
3. Ô Master Strategy còn nguyên và các biến gom cũ đã gỡ.

Gác dạng `"x" in src` khớp cả chú thích nên không dùng (CLAUDE.md, "Gác phải đọc AST").
"""
import ast
import html as _html_chuan
import pathlib
import re
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
APP = GOC / "app.py"

_O = re.compile(r'<span class="mn (bull|bear)">(.*?)</span></div>\s*<div class="mb-b">(.*?)</div>', re.S)


def _cay():
    return ast.parse(APP.read_text(encoding="utf-8"))


def _chuoi_hang(nut):
    return [n.value for n in ast.walk(nut) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _gan(cay, ten):
    kq = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
          and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]
    assert len(kq) == 1, f"mong đúng một phép gán `{ten}` trong app.py, thấy {len(kq)}"
    return kq[0]


def _dung_o(rounds, symbol="FPT"):
    """Chạy biểu thức `o_vong_tranh_luan` CỦA app.py (biên dịch từ chính nút AST) trên `rounds`."""
    cay = _cay()
    phe = eval(compile(ast.Expression(_gan(cay, "_PHE_TRANH_LUAN").value), "app.py", "eval"), {})
    env = {"rounds": rounds, "_PHE_TRANH_LUAN": phe, "symbol": symbol, "_chua": "CHUA-CO-LOI", "_html": _html_chuan}
    return eval(compile(ast.Expression(_gan(cay, "o_vong_tranh_luan").value), "app.py", "eval"), env)


def _doc_o(html):
    # BƯỚC 287: lời trong ô đã qua `html.escape` (`&` -> `&amp;`); gác này kiểm LỜI hiện ra nên bỏ thoát trước khi so.
    return [(m.group(1), " ".join(m.group(2).split()), _html_chuan.unescape(m.group(3).strip())) for m in _O.finditer(html)]


def _kq_tranh_luan_that():
    """Kết quả của `DebateModerator` trên dữ liệu dựng, cùng hình dạng `master_agent` (dict agent/stance/statement/impact)."""
    from debate_agents import DebateModerator
    a = {
        "trend": {"trend": "STRONG_UPTREND", "trend_strength": "MẠNH"},
        "momentum": {"momentum_signal": "STRONG_BUY", "indicators_summary": {"RSI": 75.0}},
        "volume": {"volume_signal": "CONFIRM", "stats": {"vol_ratio_vs_ma20": 1.6}},
        "support_resistance": {"position": "Gần vùng HỖ TRỢ", "levels": {"support_1": 20000.0}},
        "risk": {"risk_score": 80, "metrics": {"max_drawdown": 30.0, "sharpe_ratio": 1.2,
                                                "volatility_annual": 40.0}, "recommendations": {}},
        "news": {"overall_sentiment": "POSITIVE"},
    }
    v = DebateModerator().run_debate(a, 60.0)
    return [[{"agent": x.agent_name, "stance": x.stance, "statement": x.statement, "impact": x.score_impact}
             for x in rnd] for rnd in v.rounds]


# ── 1. mỗi vòng một ô, đúng lời, đúng số vòng ─────────────────────────────
def test_1a_ket_qua_that_moi_vong_mot_o_dung_loi_dung_nhan():
    rounds = _kq_tranh_luan_that()
    o = _doc_o(_dung_o(rounds))
    mong = [(("bull" if x["stance"] == "BULL" else "bear"), v, x["statement"])
            for v, rnd in enumerate(rounds, start=1) for x in rnd if x["stance"] in ("BULL", "BEAR")]
    assert len(mong) == 6, "dữ liệu dựng phải cho ba vòng, mỗi vòng một Bull và một Bear"
    assert [(c, int(re.search(r"Vòng (\d+)", n).group(1)), t) for c, n, t in o] == mong


def test_1b_ba_vong_cho_ba_loi_khac_nhau_khong_vong_nao_bi_de():
    rounds = [[{"stance": "BULL", "statement": f"BULL-V{v}"}, {"stance": "BEAR", "statement": f"BEAR-V{v}"}]
              for v in (1, 2, 3)]
    rounds[1].append({"stance": "NEUTRAL", "statement": "DEVIL-V2"})
    html = _dung_o(rounds)
    o = _doc_o(html)
    assert [(c, n.split("—")[-1].strip(), t) for c, n, t in o] == [
        ("bull", "Vòng 1", "BULL-V1"), ("bear", "Vòng 1", "BEAR-V1"),
        ("bull", "Vòng 2", "BULL-V2"), ("bear", "Vòng 2", "BEAR-V2"),
        ("bull", "Vòng 3", "BULL-V3"), ("bear", "Vòng 3", "BEAR-V3")]
    assert "DEVIL-V2" not in html, "phát biểu của Devil's Advocate không có ô ở khung này"


def test_1c_so_vong_theo_ket_qua_hai_vong_thi_hai_nhan_bon_vong_thi_bon_nhan():
    for n in (1, 2, 4):
        rounds = [[{"stance": "BULL", "statement": f"b{v}"}, {"stance": "BEAR", "statement": f"r{v}"}]
                  for v in range(1, n + 1)]
        nhan = [int(re.search(r"Vòng (\d+)", x[1]).group(1)) for x in _doc_o(_dung_o(rounds))]
        assert nhan == [v for v in range(1, n + 1) for _ in (0, 1)]


def test_1d_vong_thieu_mot_phe_chi_mat_dung_o_do_va_khong_vay_so_vong():
    rounds = [[{"stance": "BULL", "statement": "b1"}, {"stance": "BEAR", "statement": "r1"}],
              [{"stance": "BEAR", "statement": "r2"}],
              [{"stance": "BULL", "statement": "b3"}, {"stance": "BEAR", "statement": "r3"}]]
    o = _doc_o(_dung_o(rounds))
    assert [(c, int(re.search(r"Vòng (\d+)", n).group(1)), t) for c, n, t in o] == [
        ("bull", 1, "b1"), ("bear", 1, "r1"), ("bear", 2, "r2"), ("bull", 3, "b3"), ("bear", 3, "r3")]


def test_1e_khong_co_vong_nao_thi_hien_cau_bao_loi_va_khong_so_vong():
    for rong in ([], [[]]):
        html = _dung_o(rong)
        assert "CHUA-CO-LOI" in html and "Vòng" not in html


# ── 2. nhãn không gõ tay ───────────────────────────────────────────────────
def test_2a_khong_chuoi_nao_trong_app_mang_Vong_kem_so():
    for c in _chuoi_hang(_cay()):
        assert not re.search(r"Vòng\s*\d", c), f"nhãn vòng gõ tay còn trong app: {c[:60]!r}"


def test_2b_so_vong_dien_tu_enumerate_rounds_bat_dau_tu_1():
    cay = _cay()
    bieu = _gan(cay, "o_vong_tranh_luan").value
    # `"".join(<genexp>) or <ô báo lỗi>`: hình dạng gác từ ngoài vào trong.
    assert isinstance(bieu, ast.BoolOp) and isinstance(bieu.op, ast.Or)
    goi = bieu.values[0]
    assert isinstance(goi, ast.Call) and isinstance(goi.func, ast.Attribute) and goi.func.attr == "join"
    gen = goi.args[0]
    assert isinstance(gen, ast.GeneratorExp) and len(gen.generators) == 2
    g1, g2 = gen.generators
    assert isinstance(g1.target, ast.Tuple) and [t.id for t in g1.target.elts] == ["so_vong", "rnd"]
    it = g1.iter
    assert isinstance(it, ast.Call) and isinstance(it.func, ast.Name) and it.func.id == "enumerate"
    assert len(it.args) == 1 and isinstance(it.args[0], ast.Name) and it.args[0].id == "rounds"
    ks = {k.arg: k.value for k in it.keywords}
    assert isinstance(ks.get("start"), ast.Constant) and ks["start"].value == 1
    # Vòng trong đi qua TỪNG phát biểu của chính vòng ấy (không phải `rounds[-1]` hay một vòng cố định).
    assert isinstance(g2.iter, ast.Name) and g2.iter.id == "rnd" and isinstance(g2.target, ast.Name) \
        and g2.target.id == "arg"
    # Số vòng được điền ở ô nhãn: có một `{so_vong}` nằm cạnh chữ "Vòng", lời lấy từ `arg`.
    f = gen.elt
    assert isinstance(f, ast.JoinedStr)
    ten = {x.id for n in ast.walk(f) if isinstance(n, ast.FormattedValue) for x in ast.walk(n.value)
           if isinstance(x, ast.Name)}
    assert {"so_vong", "arg"} <= ten
    cho = [i for i, v in enumerate(f.values) if isinstance(v, ast.FormattedValue)
           and isinstance(v.value, ast.Name) and v.value.id == "so_vong"]
    assert len(cho) == 1 and isinstance(f.values[cho[0] - 1], ast.Constant) \
        and f.values[cho[0] - 1].value.rstrip().endswith("Vòng")
    # Lọc theo phe: chỉ BULL và BEAR có ô (khoá của bảng phe), không rẽ nhánh theo chỉ số vòng.
    assert len(g2.ifs) == 1 and isinstance(g2.ifs[0], ast.Compare) and isinstance(g2.ifs[0].ops[0], ast.In)
    assert not any(isinstance(n, ast.Name) and n.id == "so_vong" for c in g2.ifs for n in ast.walk(c))


def test_2c_bang_phe_chi_co_Bull_va_Bear_va_moi_phe_mot_mau_rieng():
    phe = eval(compile(ast.Expression(_gan(_cay(), "_PHE_TRANH_LUAN").value), "app.py", "eval"), {})
    assert set(phe) == {"BULL", "BEAR"}
    assert phe["BULL"][0] == "bull" and phe["BEAR"][0] == "bear"
    assert "Bull" in phe["BULL"][1] and "Bear" in phe["BEAR"][1]


# ── 3. ô Master giữ nguyên, biến gom cũ đã gỡ ──────────────────────────────
def test_3_o_Master_con_nguyen_va_ba_bien_gom_cu_da_go():
    cay = _cay()
    ten = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)}
    for cu in ("bull_msg", "bear_msg", "bull2_msg"):
        assert cu not in ten, f"biến gom cũ `{cu}` còn trong app: lời vòng sau sẽ ghi đè vòng trước"
    khung = [n for n in ast.walk(cay) if isinstance(n, ast.JoinedStr)
             and any("Debate Council" in c for c in _chuoi_hang(n))]
    assert len(khung) == 1
    cac = _chuoi_hang(khung[0])
    assert sum("Master Strategy" in c for c in cac) == 1
    dien = {x.id for n in ast.walk(khung[0]) if isinstance(n, ast.FormattedValue)
            for x in ast.walk(n.value) if isinstance(x, ast.Name)}
    assert {"master_msg", "dyn_rec", "o_vong_tranh_luan"} <= dien
    # Khung không còn ô Bull/Bear gõ tay: chỉ còn nhãn Master trong phần chữ cố định.
    assert not any("Bull" in c and "Vòng" in c for c in cac)
    # Số vòng ở tiêu đề (BƯỚC 284) vẫn đó.
    assert any(isinstance(m, ast.Call) and isinstance(m.func, ast.Name) and m.func.id == "len"
               for n in ast.walk(cay) if isinstance(n, ast.JoinedStr)
               and any("Bull vs Bear" in c for c in _chuoi_hang(n)) for m in ast.walk(n))
