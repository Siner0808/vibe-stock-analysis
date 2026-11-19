"""BƯỚC 284 — sáu chỗ app HIỆN sai điều nó đang làm; gác đọc AST của `app.py` và `news_collectors.py`.

Chỉ HIỂN THỊ: không điểm, không phân tích, không sổ, không lượt quét. Sáu gác, mỗi gác một lỗi:

1. Ô chọn "Chế độ phân bổ vốn" không ai đọc (`capital_mode`): gỡ.
2. Giờ cố định `10:45` · `10:46` · `10:47` · `14:05` trong khung tranh luận, chữ "3 Vong" gõ tay, và
   "Khung D1 — 15:00 ICT" (hằng số thật là `data_quality.GIO_NEN_DA_DONG` = 15:30).
3. "KL Trung Binh / 20 phien gan nhat" hiện trung bình cả khung ~180 phiên.
4. Chú thích "làm mới mỗi 5 phút" khi hạn đệm thật là `google_sheets_sync.TTL_DOC_APP` (30 phút).
5. Chú thích HTML `<!-- … -->` ở chân trang bị gửi tới trình duyệt.
6. Địa chỉ tin tức tiếng Anh không mã hoá mã (`A&B` cắt câu hỏi); hai địa chỉ anh em đã dùng `quote_plus`.

Gác dạng `"x" in src` khớp cả chú thích nên không dùng; mọi khẳng định đi qua cây AST (CLAUDE.md,
"Gác phải đọc AST").
"""
import ast
import io
import pathlib
import tokenize
from urllib.parse import parse_qs, urlparse

import pandas as pd

GOC = pathlib.Path(__file__).resolve().parent.parent
APP = GOC / "app.py"
TIN = GOC / "news_collectors.py"


def _cay(duong):
    return ast.parse(pathlib.Path(duong).read_text(encoding="utf-8"))


def _chuoi_hang(nut):
    """Mọi hằng chuỗi nằm dưới `nut` (kể cả các đoạn chữ của f-string)."""
    return [n.value for n in ast.walk(nut) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _ten_trong_cho_dien(nut):
    """Tên (Name) xuất hiện trong các ô `{…}` của f-string `nut`."""
    ten = set()
    for n in ast.walk(nut):
        if isinstance(n, ast.FormattedValue):
            ten |= {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name)}
    return ten


def _f_string_chua(cay, mau):
    kq = [n for n in ast.walk(cay) if isinstance(n, ast.JoinedStr)
          and any(mau in c for c in _chuoi_hang(n))]
    return kq


def _goi_ham(cay, ten_thuoc_tinh):
    return [n for n in ast.walk(cay) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr == ten_thuoc_tinh]


def _ten_ham(call):
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


# ── 1. ô chọn không ai đọc ───────────────────────────────────────────────
def test_1_o_chon_che_do_phan_bo_von_da_go():
    cay = _cay(APP)
    ten = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)}
    assert "capital_mode" not in ten, "biến của ô chọn vốn còn trong app"
    for call in _goi_ham(cay, "radio"):
        chu = " ".join(_chuoi_hang(call))
        assert "phân bổ vốn" not in chu and "Kelly Dynamic" not in chu, (
            "ô chọn chế độ phân bổ vốn còn trên thanh bên mà không điều gì đọc nó")


# ── 2. giờ và số vòng giả ở khung tranh luận / tiêu đề biểu đồ ─────────────
def test_2a_khong_con_gio_go_tay_o_khung_tranh_luan():
    cay = _cay(APP)
    for chu in _chuoi_hang(cay):
        for gio in ("10:45", "10:46", "10:47", "14:05"):
            assert gio not in chu, f"giờ gõ tay {gio} còn trong chuỗi giao diện"
    for f in _f_string_chua(cay, "Debate Council"):
        for c in _chuoi_hang(f):
            assert 'class="mt"' not in c, "ô giờ (mt) của khung tranh luận còn đó"


def test_2b_so_vong_cua_tranh_luan_lay_tu_ket_qua_khong_go_tay():
    cay = _cay(APP)
    for c in _chuoi_hang(cay):
        assert "3 Vong" not in c and "3 vòng" not in c, "số vòng gõ tay còn trong app"
    # Tiêu đề phải có ô điền là `len(<danh sách vòng của kết quả>)`; không có vòng thì không hiện số.
    kn = [n for n in ast.walk(cay) if isinstance(n, ast.JoinedStr)
          and any("Bull vs Bear" in c for c in _chuoi_hang(n))
          and any(isinstance(m, ast.FormattedValue) for m in ast.walk(n))]
    assert kn, "tiêu đề 'Bull vs Bear' không còn điền số vòng từ kết quả"
    assert any(isinstance(m, ast.Call) and _ten_ham(m) == "len" and
               any(isinstance(a, ast.Name) and a.id == "rounds" for a in m.args)
               for f in kn for m in ast.walk(f)), "số vòng không lấy từ len(rounds)"


def test_2c_tieu_de_bieu_do_lay_gio_tu_hang_so_GIO_NEN_DA_DONG():
    cay = _cay(APP)
    for c in _chuoi_hang(cay):
        assert "15:00" not in c, "giờ 15:00 gõ tay (hằng số thật là 15:30) còn trong app"
    nhap = [a for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and n.module == "data_quality"
            for a in n.names]
    assert "GIO_NEN_DA_DONG" in {a.name for a in nhap}, "app không nhập GIO_NEN_DA_DONG"
    f = _f_string_chua(cay, "Khung D1")
    assert len(f) == 1
    # Tiêu đề điền giờ từ một biến; biến ấy phải được gán từ chính hằng số.
    ten = _ten_trong_cho_dien(f[0])
    assert ten, "tiêu đề Khung D1 không có ô điền nào (giờ vẫn gõ tay)"
    gan = {t.id: n.value for n in ast.walk(cay) if isinstance(n, ast.Assign)
           for t in n.targets if isinstance(t, ast.Name)}
    assert any("GIO_NEN_DA_DONG" in {x.id for x in ast.walk(gan[t]) if isinstance(x, ast.Name)}
               for t in ten if t in gan), "giờ ở tiêu đề không suy ra từ GIO_NEN_DA_DONG"


# ── 3. KL trung bình: nhãn và giá trị cùng MỘT cửa sổ ─────────────────────
def _gan_o_goc(cay, ten):
    kq = [n for n in cay.body if isinstance(n, ast.Assign)
          and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]
    return kq


def test_3_kl_trung_binh_nhan_va_gia_tri_dung_chung_mot_cua_so_20_phien():
    cay = _cay(APP)
    hang = _gan_o_goc(cay, "SO_PHIEN_KL_TB")
    assert len(hang) == 1 and isinstance(hang[0].value, ast.Constant) and hang[0].value.value == 20
    gan = _gan_o_goc(cay, "avg_vol_20")
    assert len(gan) == 1, "không có đúng một phép gán avg_vol_20 ở gốc tệp"
    # Hình dạng: int( <cột volume>.tail(SO_PHIEN_KL_TB).mean() )
    v = gan[0].value
    assert isinstance(v, ast.Call) and _ten_ham(v) == "int" and len(v.args) == 1
    mean = v.args[0]
    assert isinstance(mean, ast.Call) and _ten_ham(mean) == "mean"
    tail = mean.func.value
    assert isinstance(tail, ast.Call) and _ten_ham(tail) == "tail"
    assert len(tail.args) == 1 and isinstance(tail.args[0], ast.Name) and tail.args[0].id == "SO_PHIEN_KL_TB"
    # Giá trị: chạy đúng biểu thức của app trên một khung dựng sẵn (160 phiên đầu 1000, 20 phiên cuối 5).
    df = pd.DataFrame({"volume": [1000] * 160 + [5] * 20})
    env = {"df": df, "SO_PHIEN_KL_TB": hang[0].value.value}
    assert eval(compile(ast.Expression(v), "app.py", "eval"), env) == 5

    # `avg_vol` (cả khung) vẫn là mẫu số của ô "Dòng tiền lớn": BƯỚC này không đổi ô ấy.
    luong = _gan_o_goc(cay, "vol_flow_ratio")
    assert len(luong) == 1
    ten_luong = {x.id for x in ast.walk(luong[0].value) if isinstance(x, ast.Name)}
    assert "avg_vol" in ten_luong and "avg_vol_20" not in ten_luong

    # Ô hiển thị: giá trị lấy avg_vol_20 (không phải avg_vol), nhãn lấy SO_PHIEN_KL_TB (không gõ "20 phien").
    o = _f_string_chua(cay, "KL Trung Binh")
    assert len(o) == 1
    ten = _ten_trong_cho_dien(o[0])
    assert "avg_vol_20" in ten and "avg_vol" not in ten
    assert "SO_PHIEN_KL_TB" in ten
    assert not any("20 phien" in c for c in _chuoi_hang(o[0])), "nhãn còn gõ tay 20 phiên"


# ── 4. chú thích làm mới đọc hạn đệm từ hằng số ───────────────────────────
def test_4_chu_thich_lam_moi_doc_TTL_DOC_APP_khong_go_tay_so_phut():
    cay = _cay(APP)
    for c in _chuoi_hang(cay):
        assert "mỗi 5 phút" not in c, "chữ 'mỗi 5 phút' gõ tay còn trong app"
    ca = [call for call in _goi_ham(cay, "caption")
          if any("làm mới mỗi" in c for c in _chuoi_hang(call))]
    assert len(ca) == 3, f"mong 3 chú thích làm mới, thấy {len(ca)}"
    for call in ca:
        dien = [n for n in ast.walk(call) if isinstance(n, ast.FormattedValue)]
        thuoc = {x.attr for d in dien for x in ast.walk(d.value) if isinstance(x, ast.Attribute)}
        assert "TTL_DOC_APP" in thuoc, "chú thích làm mới không đọc TTL_DOC_APP"
        # Hình dạng của phép suy ra: giây → phút là `TTL_DOC_APP // 60` (không chia nhầm, không nhân thêm).
        ps = [x for d in dien for x in ast.walk(d.value) if isinstance(x, ast.BinOp)]
        assert any(isinstance(p.op, ast.FloorDiv) and isinstance(p.left, ast.Attribute)
                   and p.left.attr == "TTL_DOC_APP" and isinstance(p.right, ast.Constant)
                   and p.right.value == 60 for p in ps), "phép đổi giây sang phút không phải TTL_DOC_APP // 60"


# ── 5. không chú thích HTML nào tới trình duyệt ───────────────────────────
def test_5_khong_chuoi_nao_trong_app_mang_chu_thich_HTML_va_lich_su_nam_o_chu_thich_python():
    cay = _cay(APP)
    for c in _chuoi_hang(cay):
        assert "<!--" not in c, "chú thích HTML còn trong chuỗi gửi ra trình duyệt"
    cmt = [t.string for t in tokenize.generate_tokens(io.StringIO(APP.read_text(encoding="utf-8")).readline)
           if t.type == tokenize.COMMENT]
    assert any("Gemini" in c for c in cmt), "lịch sử về 'Gemini' ở chân trang không còn trong chú thích Python"


# ── 6. địa chỉ tin tức mã hoá mã cổ phiếu ──────────────────────────────────
def test_6a_moi_dia_chi_google_news_dien_ma_qua_quote_plus():
    cay = _cay(TIN)
    f = _f_string_chua(cay, "news.google.com/rss/search?q=")
    assert len(f) >= 2
    for j in f:
        goi = [n for n in ast.walk(j) if isinstance(n, ast.FormattedValue) and isinstance(n.value, ast.Call)
               and _ten_ham(n.value) == "quote_plus"]
        assert goi, "địa chỉ Google News điền câu hỏi mà không qua quote_plus"
        ngoai = [n for n in ast.walk(j) if isinstance(n, ast.FormattedValue)
                 and not (isinstance(n.value, ast.Call) and _ten_ham(n.value) == "quote_plus")]
        assert not any(isinstance(x, ast.Name) and x.id == "symbol" for n in ngoai for x in ast.walk(n.value))


def _lay_dia_chi(monkeypatch, ma):
    import news_collectors as nc
    chup = []
    monkeypatch.setattr(nc, "_gom_song_song", lambda viec, *a, **k: chup.append([v[1] for v in viec]) or [])
    nc.CompanyNewsAgent().collect(ma)
    return chup[0]


def test_6b_goi_tin_cua_ma_thuong_giong_dia_chi_cu_va_ma_co_ky_tu_dac_biet_khong_bi_cat(monkeypatch):
    for ma in ("FPT", "VNM", "HPG"):
        _, _, en = _lay_dia_chi(monkeypatch, ma)
        assert en == f"https://news.google.com/rss/search?q={ma}+Vietnam+stock&hl=en&gl=VN&ceid=VN:en"
    _, _, en = _lay_dia_chi(monkeypatch, "A&B")
    q = parse_qs(urlparse(en).query)
    assert q["q"] == ["A&B Vietnam stock"] and q["hl"] == ["en"], "dấu & của mã cắt câu hỏi"
