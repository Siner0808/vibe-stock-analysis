"""BƯỚC 297 — app: ô Devil's Advocate trong khung tranh luận, và `html.escape` cho hai chữ từ ngoài mã (`_loi_np`, `symbol`).

Chỉ HIỂN THỊ. Không đổi `debate_agents.py`, điểm hay logic tranh luận. Quyết định của leader dưới lời người dùng
22/11/2026 (*"tiếp đi. việc nào có thể quyết thay tôi thì làm nốt luôn đi"*), không phải lựa chọn riêng của người dùng.

1. DEVIL. `DebateModerator.run_debate` đặt phát biểu của `DevilsAdvocateAgent` (stance NEUTRAL) vào vòng 2, sau Bull và
   Bear của vòng ấy. Trước BƯỚC 297 app lọc nó đi (`o_vong_tranh_luan` chỉ cho BULL/BEAR). Nay `_PHE_TRANH_LUAN` có khoá
   thứ ba và mỗi phát biểu NEUTRAL có MỘT ô, đúng vòng của nó, qua `html.escape`.
2. ESCAPE lớp E1 (`_loi_np`: chữ lỗi mạng/thư viện ở ô "Trong phiên") và E2 (`symbol`: mã người dùng gõ vào
   `st.text_input("Mã CK")`). Lớp E3 (nhãn đóng của chính mã: `dyn_rec`, `dyn_phase_full`...) KHÔNG đổi ở BƯỚC này.
3. GÁC AST: mọi lần dán `symbol` / `_loi_np` vào một f-string phải đi qua `html.escape`, trừ khi f-string ấy là đối số của
   một lời gọi Streamlit KHÔNG bật `unsafe_allow_html` (markdown thường, không sinh thẻ HTML).

Như BƯỚC 285/287: chạy ĐÚNG biểu thức của `app.py` (biên dịch từ cây AST), không bật Streamlit, không mạng.
So thứ tự bằng `sorted` hoặc tập, không so theo thứ tự đi cây (lỗi 206).
"""
import ast
import html as _html_chuan
import pathlib
import re
import sys
from html.parser import HTMLParser

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
APP = GOC / "app.py"

TEN_NGOAI = ("symbol", "_loi_np")      # hai lớp chữ có thể mang ký tự từ ngoài mã (E1, E2)
NHIEM = '<b>BOOM</b> & "so" <script>x()</script> \'q\' A&B'


# ── dụng cụ AST ────────────────────────────────────────────────────────────
def _cay(src=None):
    return ast.parse(APP.read_text(encoding="utf-8") if src is None else src)


def _gan(cay, ten):
    kq = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
          and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]
    assert len(kq) == 1, f"mong đúng một phép gán `{ten}`, thấy {len(kq)}"
    return kq[0]


def _chay(nut_bieu_thuc, env):
    return eval(compile(ast.Expression(nut_bieu_thuc), "app.py", "eval"), env)


def _dung_o(rounds, symbol="FPT"):
    """Chạy ĐÚNG biểu thức `o_vong_tranh_luan` của app.py trên `rounds`."""
    cay = _cay()
    phe = _chay(_gan(cay, "_PHE_TRANH_LUAN").value, {})
    env = {"rounds": rounds, "_PHE_TRANH_LUAN": phe, "symbol": symbol, "_chua": "CHUA-CO-LOI", "_html": _html_chuan}
    return _chay(_gan(cay, "o_vong_tranh_luan").value, env)


def _ten_trong(nut):
    return {x.id for x in ast.walk(nut) if isinstance(x, ast.Name)}


def _bam_html(cay):
    """Tên các biến trỏ vào module `html` chuẩn (`import html` hoặc `import html as _html`)."""
    return {(a.asname or a.name) for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names if a.name == "html"}


def _la_escape(nut, bam):
    return (isinstance(nut, ast.Call) and isinstance(nut.func, ast.Attribute) and nut.func.attr == "escape"
            and isinstance(nut.func.value, ast.Name) and nut.func.value.id in bam)


def _bat_html(goi):
    """Lời gọi có `unsafe_allow_html=True` (hoặc giá trị không phải hằng `False`, nghi ngờ thì coi là bật)."""
    for k in goi.keywords:
        if k.arg == "unsafe_allow_html":
            return not (isinstance(k.value, ast.Constant) and k.value.value is False)
    return False


# Chỗ nhận MARKDOWN THƯỜNG (Streamlit thoát thẻ HTML khi không bật `unsafe_allow_html`): không phải ngữ cảnh HTML.
_CHO_MARKDOWN = {"error", "warning", "spinner", "caption", "markdown", "info", "success"}


def _vi_pham(src):
    """Danh sách (dòng, biểu thức) mà `symbol`/`_loi_np` được dán vào f-string KHÔNG qua `html.escape`
    và f-string ấy không phải đối số của chỗ nhận markdown thường. Trả về đã `sorted` (lỗi 206)."""
    cay = _cay(src)
    bam = _bam_html(cay)
    cha = {c: n for n in ast.walk(cay) for c in ast.iter_child_nodes(n)}
    kq = []

    def goi_gan_nhat(nut):
        while nut in cha:
            nut = cha[nut]
            if isinstance(nut, ast.Call):
                return nut
        return None

    for n in ast.walk(cay):
        if isinstance(n, ast.FormattedValue) and _ten_trong(n.value) & set(TEN_NGOAI):
            if _la_escape(n.value, bam):
                continue
            # nằm trong một `html.escape(...)` ở tầng sâu hơn (vd `{html.escape(x)[:5]}`) cũng đã thoát
            if any(_la_escape(x, bam) and _ten_trong(x) & set(TEN_NGOAI) for x in ast.walk(n.value)):
                continue
            g = goi_gan_nhat(n)
            f = g.func if g is not None else None
            la_markdown = (g is not None and not _bat_html(g) and (
                (isinstance(f, ast.Attribute) and f.attr in _CHO_MARKDOWN and isinstance(f.value, ast.Name) and f.value.id == "st")
                or (isinstance(f, ast.Name) and f.id == "_hien_dong_pha")))
            if not la_markdown:
                kq.append((n.lineno, ast.unparse(n.value)))
        # tên trần ở chỗ KHÔNG phải f-string: nối chuỗi, `%`, `.format`, hoặc gán bí danh
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)):
            for toan in (n.left, n.right):
                if isinstance(toan, ast.Name) and toan.id in TEN_NGOAI:
                    kq.append((n.lineno, f"{ast.unparse(n)}  [nối chuỗi]"))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "format":
            for a in list(n.args) + [k.value for k in n.keywords]:
                if isinstance(a, ast.Name) and a.id in TEN_NGOAI:
                    kq.append((n.lineno, f"{ast.unparse(n)}  [.format]"))
        # bí danh: `m = symbol` (đích là TÊN trần); `st.session_state[k] = symbol` là kho trạng thái, không phải HTML
        if (isinstance(n, (ast.Assign, ast.NamedExpr, ast.AnnAssign)) and isinstance(n.value, ast.Name)
                and n.value.id in TEN_NGOAI
                and all(isinstance(t, ast.Name) for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))):
            kq.append((n.lineno, f"{ast.unparse(n)}  [bí danh]"))
    return sorted(kq)


class _Thu(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.the, self.chu = [], []

    def handle_starttag(self, tag, attrs):
        self.the.append((tag, tuple(sorted(attrs))))

    def handle_data(self, d):
        self.chu.append(d)


def _doc(html_ra):
    p = _Thu()
    p.feed(html_ra)
    return p


_O = re.compile(r'<div class="mb (\w+)">\s*<div class="mh"><span class="mn \1">(.*?)</span></div>\s*<div class="mb-b">(.*?)</div>', re.S)


def _doc_o(html_ra):
    """[(lớp, nhãn, lời)] theo thứ tự xuất hiện trong HTML (lời đã bỏ thoát)."""
    return [(m.group(1), " ".join(m.group(2).split()), _html_chuan.unescape(m.group(3).strip())) for m in _O.finditer(html_ra)]


def _kq_tranh_luan_that():
    """Kết quả của `DebateModerator` thật trên dữ liệu dựng (cùng hình dạng `master_agent`)."""
    from debate_agents import DebateModerator
    a = {
        "trend": {"trend": "STRONG_UPTREND", "trend_strength": "MẠNH"},
        "momentum": {"momentum_signal": "STRONG_BUY", "indicators_summary": {"RSI": 75.0}},
        "volume": {"volume_signal": "CONFIRM", "stats": {"vol_ratio_vs_ma20": 1.6}},
        "support_resistance": {"position": "Gần vùng HỖ TRỢ", "levels": {"support_1": 20000.0}},
        "risk": {"risk_score": 80, "metrics": {"max_drawdown": 30.0, "sharpe_ratio": 1.2, "volatility_annual": 40.0},
                 "recommendations": {}},
        "news": {"overall_sentiment": "POSITIVE", "total_articles": 3},
    }
    v = DebateModerator().run_debate(a, 60.0)
    return [[{"agent": x.agent_name, "stance": x.stance, "statement": x.statement, "impact": x.score_impact}
             for x in rnd] for rnd in v.rounds]


# ── 1. Devil's Advocate ────────────────────────────────────────────────────
def test_1a_khoa_NEUTRAL_cua_bang_phe_lay_tu_stance_cua_agent_trong_ma():
    from debate_agents import BearAdvocateAgent, BullAdvocateAgent, DevilsAdvocateAgent
    phe = _chay(_gan(_cay(), "_PHE_TRANH_LUAN").value, {})
    assert set(phe) == {BullAdvocateAgent.STANCE, BearAdvocateAgent.STANCE, DevilsAdvocateAgent.STANCE}
    assert phe[DevilsAdvocateAgent.STANCE][0] == "devil" and "Devil" in phe[DevilsAdvocateAgent.STANCE][1]
    # mỗi phe một lớp CSS riêng, và lớp ấy có kiểu trong CSS của app
    assert len({v[0] for v in phe.values()}) == 3
    css = APP.read_text(encoding="utf-8")
    assert ".mb.devil" in css and ".mn.devil" in css


def test_1b_ket_qua_that_devil_nam_o_vong_2_sau_bull_va_bear_cua_vong_ay():
    rounds = _kq_tranh_luan_that()
    o = _doc_o(_dung_o(rounds))
    devil_that = [x for rnd in rounds for x in rnd if x["stance"] == "NEUTRAL"]
    assert len(devil_that) == 1, "dữ liệu dựng phải cho đúng một phát biểu NEUTRAL"
    mong = []
    for v, rnd in enumerate(rounds, start=1):
        for x in rnd:
            mong.append(({"BULL": "bull", "BEAR": "bear", "NEUTRAL": "devil"}[x["stance"]], v, x["statement"]))
    got = [(c, int(re.search(r"Vòng (\d+)", n).group(1)), t) for c, n, t in o]
    assert got == mong
    # đúng vị trí: ngay sau Bull và Bear của vòng 2, trước Bull của vòng 3
    assert [(c, v) for c, v, _ in got] == [("bull", 1), ("bear", 1), ("bull", 2), ("bear", 2), ("devil", 2), ("bull", 3), ("bear", 3)]
    assert got[4][2] == devil_that[0]["statement"], "lời Devil hiện nguyên văn như văn bản"


def test_1c_devil_qua_html_escape_hien_ra_la_chu_khong_thanh_the():
    rounds = [[{"stance": "BULL", "statement": "b"}, {"stance": "BEAR", "statement": "r"}],
              [{"stance": "BULL", "statement": "b2"}, {"stance": "BEAR", "statement": "r2"},
               {"stance": "NEUTRAL", "statement": NHIEM}]]
    html_ra = _dung_o(rounds)
    p = _doc(html_ra)
    assert {t for t, _ in p.the} == {"div", "span"}, f"phát biểu sinh thẻ lạ: {sorted({t for t, _ in p.the})}"
    assert NHIEM in "".join(p.chu)
    assert "<script>" not in html_ra and "<b>BOOM" not in html_ra


def test_1d_khong_co_devil_thi_khong_co_o_devil_va_khong_in_None():
    rounds = [[{"stance": "BULL", "statement": "b1"}, {"stance": "BEAR", "statement": "r1"}],
              [{"stance": "BULL", "statement": "b2"}, {"stance": "BEAR", "statement": "r2"}]]
    html_ra = _dung_o(rounds)
    assert "devil" not in html_ra and "Devil" not in html_ra and "None" not in html_ra
    assert len(_doc_o(html_ra)) == 4


def test_1e_devil_o_vong_khac_nam_dung_vong_do_va_nhieu_devil_moi_phat_bieu_mot_o():
    rounds = [[{"stance": "BULL", "statement": "b1"}, {"stance": "NEUTRAL", "statement": "d1"}],
              [{"stance": "BEAR", "statement": "r2"}],
              [{"stance": "BULL", "statement": "b3"}, {"stance": "NEUTRAL", "statement": "d3a"},
               {"stance": "NEUTRAL", "statement": "d3b"}]]
    got = [(c, int(re.search(r"Vòng (\d+)", n).group(1)), t) for c, n, t in _doc_o(_dung_o(rounds))]
    assert got == [("bull", 1, "b1"), ("devil", 1, "d1"), ("bear", 2, "r2"),
                   ("bull", 3, "b3"), ("devil", 3, "d3a"), ("devil", 3, "d3b")]


def test_1f_phat_bieu_Devil_thieu_hoac_None_thi_o_rong_khong_in_None():
    html_ra = _dung_o([[{"stance": "BULL", "statement": "b"}, {"stance": "NEUTRAL"}, {"stance": "NEUTRAL", "statement": None}]])
    assert "None" not in html_ra


def test_1g_chi_co_devil_khong_bull_bear_van_hien_o_devil_khong_roi_ve_cau_bao_loi():
    html_ra = _dung_o([[{"stance": "NEUTRAL", "statement": "d"}]])
    assert [c for c, _, _ in _doc_o(html_ra)] == ["devil"] and "CHUA-CO-LOI" not in html_ra


# ── 2. E1: `_loi_np` ───────────────────────────────────────────────────────
def _np_phu_loi():
    """Phép gán `_np_phu` của nhánh lỗi (chuỗi mang "nến nội phiên:"), lấy từ cây AST của app."""
    kq = [n for n in ast.walk(_cay()) if isinstance(n, ast.Assign)
          and any(isinstance(t, ast.Name) and t.id == "_np_phu" for t in n.targets)
          and any(isinstance(c, ast.Constant) and "nến nội phiên:" in str(c.value) for c in ast.walk(n.value))]
    assert len(kq) == 1
    return kq[0].value


def test_2a_loi_np_thu_la_chu_khong_thanh_the_trong_o_Trong_phien():
    ra = _chay(_np_phu_loi(), {"_loi_np": NHIEM, "_html": _html_chuan})
    p = _doc(f'<div style="x">{ra}</div>')
    assert [t for t, _ in p.the] == ["div"], f"lỗi ngoài sinh thẻ lạ: {p.the}"
    assert "".join(p.chu) == f"nến nội phiên: {NHIEM}"
    assert "<script>" not in ra and "<b>" not in ra


def test_2b_loi_np_binh_thuong_hien_giong_het_truoc_khi_thoat():
    for bt in ("Không có nguồn: nến 30 phút", "timeout sau 10 giây", "KeyError close"):
        assert _chay(_np_phu_loi(), {"_loi_np": bt, "_html": _html_chuan}) == f"nến nội phiên: {bt}"
    # dấu nháy đơn thành `&#x27;`: khác byte nhưng trình duyệt hiện lại đúng dấu nháy
    ra = _chay(_np_phu_loi(), {"_loi_np": "KeyError 'close'", "_html": _html_chuan})
    assert _html_chuan.unescape(ra) == "nến nội phiên: KeyError 'close'"


def test_2c_loi_np_la_ngoai_le_hay_so_thi_van_hien_nhu_str():
    assert _chay(_np_phu_loi(), {"_loi_np": ValueError("a<b"), "_html": _html_chuan}) == "nến nội phiên: a&lt;b"


# ── 3. E2: `symbol` ────────────────────────────────────────────────────────
def _cho_dan_symbol_vao_html():
    """Các FormattedValue của app mang `symbol` và nằm trong ngữ cảnh HTML (đối số `unsafe_allow_html=True`, hoặc
    f-string gán vào biến rồi dán vào HTML). Mỗi phần tử: (dòng, nút biểu thức)."""
    cay = _cay()
    cha = {c: n for n in ast.walk(cay) for c in ast.iter_child_nodes(n)}
    kq = []
    for n in ast.walk(cay):
        if not (isinstance(n, ast.FormattedValue) and "symbol" in _ten_trong(n.value)):
            continue
        x, goi = n, None
        while x in cha:
            x = cha[x]
            if isinstance(x, ast.Call):
                goi = x
                break
        if goi is not None and _bat_html(goi):
            kq.append((n.lineno, n.value))
    return sorted(kq, key=lambda t: t[0])


def test_3a_biet_truoc_so_cho_dan_symbol_vao_html_va_moi_cho_qua_escape():
    cho = _cho_dan_symbol_vao_html()
    dong = [d for d, _ in cho]
    # danh sách chốt 22/11/2026 (đếm bằng AST, lệnh trong docs/STATE.md BƯỚC 297); thêm chỗ mới thì sửa số này CÓ CHỦ ĐÍCH
    assert len(dong) == 7, f"số chỗ dán `symbol` vào st.markdown(unsafe_allow_html=True) đổi: {dong}"
    bam = _bam_html(_cay())
    chua_thoat = [d for d, nut in cho if not _la_escape(nut, bam)]
    assert chua_thoat == [], f"còn chỗ dán `symbol` thô vào HTML ở dòng {chua_thoat}"


def test_3b_moi_bieu_thuc_symbol_o_app_chay_voi_chuoi_doc_ra_la_chu_va_ma_thuong_giu_nguyen_byte():
    cay = _cay()
    cho = [nut for _, nut in _cho_dan_symbol_vao_html()]
    # thêm hai chỗ mà `symbol` đi vào HTML qua biến (`_vt_phu`) và qua ô dự phòng của khung tranh luận
    cho += [n.value for n in ast.walk(cay) if isinstance(n, ast.FormattedValue) and "symbol" in _ten_trong(n.value)
            and n.lineno in {m.lineno for m in ast.walk(cay) if isinstance(m, ast.Assign)
                             and any(isinstance(t, ast.Name) and t.id == "_vt_phu" for t in m.targets)}]
    assert cho
    for nut in cho:
        for ma in ("FPT", "ACB", "VN30F1M", "E1VFVN30", "BSR"):
            assert _chay(nut, {"symbol": ma, "_html": _html_chuan}) == ma, f"mã thường đổi hình: {ast.unparse(nut)} · {ma}"
        ra = _chay(nut, {"symbol": NHIEM, "_html": _html_chuan})
        assert "<" not in ra and ">" not in ra and '"' not in ra
        assert _html_chuan.unescape(ra) == NHIEM


def test_3c_o_du_phong_cua_khung_tranh_luan_thoat_symbol_ma_thuong_giong_het_ban_cu():
    nhiem = _dung_o([], symbol=NHIEM)
    p = _doc(nhiem)
    assert {t for t, _ in p.the} == {"div", "span"} and NHIEM in "".join(p.chu)
    # mã thường hiện y như bản dán thô
    assert "Bull Agent (FPT)" in _dung_o([], symbol="FPT")


# ── 4. gác AST: dán `symbol` / `_loi_np` vào HTML phải đi qua html.escape ─────
def test_4a_app_hien_tai_khong_co_cho_dan_thô():
    assert _vi_pham(APP.read_text(encoding="utf-8")) == []


MAU_THO = [
    ("f\"nến nội phiên: {_html.escape(str(_loi_np))}\"", "f\"nến nội phiên: {_loi_np}\""),
    ("{_html.escape(symbol)}.VN</span>", "{symbol}.VN</span>"),
    ("🐂 Bull Agent ({_html.escape(symbol)})", "🐂 Bull Agent ({symbol})"),
    ("Vị thế {_html.escape(symbol)}</div>", "Vị thế {symbol}</div>"),
    ("<b style=\"color:var(--c-acc);\">{_html.escape(symbol)} ({exchange})", "<b style=\"color:var(--c-acc);\">{symbol} ({exchange})"),
]


@pytest.mark.parametrize("co_escape,tho", MAU_THO)
def test_4b_dung_lai_nguyen_van_dang_tho_thi_gac_do(co_escape, tho):
    src = APP.read_text(encoding="utf-8")
    assert src.count(co_escape) == 1, f"neo không khớp đúng một lần: {co_escape!r}"
    vi = _vi_pham(src.replace(co_escape, tho))
    assert len(vi) == 1, f"gác phải bắt đúng một chỗ, thấy {vi}"


def test_4c_gac_bat_ca_nhom_ke_nhau_nhung_khong_bat_markdown_thuong():
    mau_do = ["import html as _h\nsymbol = 'A'\nst.markdown(f'<b>{symbol}</b>', unsafe_allow_html=True)\n",
              "import html as _h\nsymbol = 'A'\nx = f'<b>{symbol}</b>'\n",
              "import html as _h\nsymbol = 'A'\nx = '<b>' + symbol + '</b>'\n",
              "import html as _h\nsymbol = 'A'\nx = '<b>{}</b>'.format(symbol)\n",
              "import html as _h\nsymbol = 'A'\nm = symbol\n",
              "import html as _h\nsymbol = 'A'\nx = f'<b>{_h.escape(\"z\")}{symbol}</b>'\n",
              "import html as _h\nclass K:\n    def escape(s): return s\nsymbol = 'A'\nx = f'{K.escape(symbol)}'\n",
              "symbol = 'A'\nx = f'{html.escape(symbol)}'\n"]    # `html` không được import trong mẫu: không chứng minh là module chuẩn
    mau_xanh = ["import html as _h\nsymbol = 'A'\nst.markdown(f'<b>{_h.escape(symbol)}</b>', unsafe_allow_html=True)\n",
                "import html as _h\nsymbol = 'A'\nst.error(f'lỗi mã {symbol}')\n",
                "import html as _h\nsymbol = 'A'\nst.markdown(f'##### {symbol}')\n",
                "import html as _h\nsymbol = 'A'\n_hien_dong_pha(1, 2, f'{symbol}.VN')\n",
                "import html as _h\nsymbol = 'A'\nx = f'{_h.escape(symbol)[:3]}'\n"]
    for m in mau_do:
        assert _vi_pham(m), f"phải đỏ: {m!r}"
    for m in mau_xanh:
        assert _vi_pham(m) == [], f"phải xanh: {m!r}"


def test_4d_st_markdown_bat_unsafe_allow_html_False_la_markdown_thuong_con_True_hoac_bien_la_html():
    assert _vi_pham("import html as _h\nsymbol='A'\nst.markdown(f'{symbol}', unsafe_allow_html=False)\n") == []
    assert _vi_pham("import html as _h\nsymbol='A'\nst.markdown(f'{symbol}', unsafe_allow_html=bat)\n") != []
