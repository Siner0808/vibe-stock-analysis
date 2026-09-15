"""Mức Fibonacci: số học đúng, đơn vị đúng, và KHÔNG BỊA khi thiếu bằng chứng.

ĐƠN VỊ CỦA PHÉP KIỂM NÀY
────────────────────────
Thứ đang được kiểm là **số học Fibonacci**, không phải bộ dò cấu trúc
Wyckoff — cái đó đã có test và đột biến riêng. Nên phần lớn phép kiểm ở
đây thay `pha_wyckoff.doc_pha` bằng một kết quả DỰNG TAY với sàn/trần đã
biết, rồi soi từng con số đi ra.

Thay một hàm đi thì phải chứng minh đường nối vẫn đi qua nó thật — nếu
không, một ngày nào đó `doc_muc` tự dò đỉnh–đáy và mọi phép kiểm ở đây vẫn
xanh. Đó là việc của `test_KHONG_TU_DO_dinh_day…`, đọc bằng **AST**, vì
chữ `pha_wyckoff` nằm đầy trong docstring của chính module ấy (lỗi 38).
"""
import ast
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import muc_fibonacci as mf  # noqa: E402
import pha_wyckoff  # noqa: E402


def _df(n: int = 80, gia: float = 100.0) -> pd.DataFrame:
    """Bảng nến tối thiểu — đủ cột, đủ dòng. Nội dung không quan trọng ở
    những phép kiểm có thay `doc_pha`."""
    return pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=n, freq="D"),
        "open": [gia] * n, "high": [gia * 1.01] * n,
        "low": [gia * 0.99] * n, "close": [gia] * n,
        "volume": [1_000_000] * n,
    })


def _pha(san: float, tran: float, so_phien: int = 40) -> pha_wyckoff.PhaWyckoff:
    """Một kết quả Wyckoff KẾT LUẬN ĐƯỢC, sàn/trần đặt sẵn."""
    return pha_wyckoff.PhaWyckoff(
        pha="TÍCH LUỸ", cau_truc="TÍCH LUỸ", su_kien=None, do_tin="đã xác nhận",
        nhan_ngan="x", nhan_day="x", huong="TĂNG",
        san=san, tran=tran, so_phien_nen=so_phien,
        bang_chung=(), phan_bien=(), phu_dinh="")


def _dat(monkeypatch, san, tran):
    monkeypatch.setattr(mf.pha_wyckoff, "doc_pha",
                        lambda df, hs=1.0: _pha(san, tran))


# ───────────────────── không đủ bằng chứng thì KHÔNG bịa ─────────────

def test_KHONG_DU_BANG_CHUNG_thi_KHONG_BIA_vung():
    """Một vùng bịa nguy hiểm hơn một ô trống.

    Đi qua `doc_pha` THẬT với bảng quá ngắn — không thay gì cả, vì đây
    đúng là đường mà một nửa rổ VN100 đi vào.
    """
    ra = mf.doc_muc(_df(n=10))
    assert not ra.ket_luan_duoc
    assert ra.vung_mua is None and ra.sl is None
    assert ra.tp1 is None and ra.tp2 is None
    assert ra.ly_do.strip(), "tu choi ma khong noi vi sao"
    assert "Chưa đủ bằng chứng" in ra.nhan

    # LY DO phai la ly do THAT cua pha_wyckoff, khong phai mot cau chung.
    #
    # Chot thu hai (`san is None`) do duoc moi ca ma chot thu nhat do —
    # nen duc bo chot thu nhat SONG SOT o luot dau. No khong mat an toan,
    # no mat LY DO CU THE: nguoi doc nhan "thieu bien vung" thay vi "chi co
    # 10 phien, can it nhat 60". Trong mot du an lay "noi ro vi sao" lam
    # coc, do la mat mat that.
    assert "10 phiên" in ra.ly_do, (
        f"ly do khong mang theo ly do goc cua pha_wyckoff: {ra.ly_do!r}")
    print(f"PASS  tu choi va noi ly do THAT: {ra.ly_do[:60]}")


def test_BANG_RONG_hay_THIEU_COT_deu_tu_choi_chu_khong_no():
    for x in (None, pd.DataFrame(), _df(n=80).drop(columns=["low"])):
        ra = mf.doc_muc(x)
        assert not ra.ket_luan_duoc and ra.ly_do.strip()
    print("PASS  bang rong / thieu cot -> tu choi, khong no")


def test_BIEN_VUNG_khong_duong_thi_tu_choi(monkeypatch):
    """Trần ≤ sàn là dữ liệu vô nghĩa. Chia cho nó ra số vẫn 'chạy được'."""
    for san, tran in ((100.0, 100.0), (120.0, 100.0)):
        _dat(monkeypatch, san, tran)
        ra = mf.doc_muc(_df())
        assert not ra.ket_luan_duoc, (san, tran)
        assert "biên vùng không dương" in ra.ly_do
    print("PASS  bien vung <= 0 -> tu choi")


# ───────────────────────── số học ────────────────────────────────────

def test_VUNG_MUA_la_HAI_so_nam_giua_0_5_va_0_618_duoi_TRAN(monkeypatch):
    """Đây là toàn bộ lý do có module: một VÙNG, không phải một điểm."""
    _dat(monkeypatch, 100.0, 200.0)          # biên = 100
    ra = mf.doc_muc(_df())
    assert ra.ket_luan_duoc
    thap, cao = ra.vung_mua
    # 200 − 0,618·100 = 138,2   ·   200 − 0,500·100 = 150,0
    # So bằng `approx`: giá trị KHÔNG làm tròn nên mang nhiễu dấu phẩy động.
    assert thap == pytest.approx(138.2), ra.vung_mua
    assert cao == pytest.approx(150.0), ra.vung_mua
    assert thap < cao, "vung mua phai co be rong"
    assert cao < ra.tran and thap > ra.san
    print(f"PASS  vung mua {thap:,.0f}–{cao:,.0f} nam trong (san, tran)")


def test_TP_nam_TREN_TRAN_va_TP2_xa_hon_TP1(monkeypatch):
    """Mở rộng 1,272 và 1,618 đo TỪ SÀN, nên `1,0` chính là trần."""
    _dat(monkeypatch, 100.0, 200.0)
    ra = mf.doc_muc(_df())
    assert (ra.tp1, ra.tp2) == (227.2, 261.8), (ra.tp1, ra.tp2)
    assert ra.tp1 > ra.tran and ra.tp2 > ra.tp1
    print(f"PASS  TP1 {ra.tp1:,.0f} · TP2 {ra.tp2:,.0f}, ca hai tren tran")


@pytest.mark.parametrize("san,tran,vua", [
    (100.0, 200.0, False),        # nền rộng 100% — không thể vừa ngân sách
    (95.0, 100.0, True),          # nền hẹp 5%
    (10_000.0, 90_000.0, False),  # nền rất rộng
    (21.0, 21.5, True),           # giá thật kiểu VN, nền rất hẹp
])
def test_SL_luon_DUOI_day_vung__va_BAO_khi_vuot_ngan_sach(monkeypatch, san, tran, vua):
    """Hai điều kiện đánh nhau, và gác này canh chỗ chúng đánh nhau.

    *"SL dưới cấu trúc"* và *"rủi ro mỗi lệnh ≤ 6,5%"* không thể cùng đúng
    trên một nền rộng. Bản nháp đầu kẹp bừa cho ra một con số và SL rơi
    **vào giữa vùng mua** — chính phép kiểm tham số này bắt được, ở lượt
    chạy đầu tiên.

    Hợp đồng nay là: SL **luôn** dưới đáy vùng mua, và khi rủi ro vượt biên
    thì **nói ra**, không kẹp cho đẹp.
    """
    _dat(monkeypatch, san, tran)
    ra = mf.doc_muc(_df())
    assert ra.ket_luan_duoc
    thap, cao = ra.vung_mua
    assert ra.sl < thap, "SL phai nam DUOI day vung mua, khong duoc lot vao trong"
    assert ra.sl_pct == pytest.approx((cao - ra.sl) / cao * 100, abs=0.11), (
        "sl_pct phai do tu DINH vung mua — do la ca xau nhat")
    assert ra.vua_ngan_sach is vua, (san, tran, ra.sl_pct)
    if not vua:
        assert "KHÔNG vừa ngân sách rủi ro" in ra.nhan, (
            "vuot bien ma nhan khong noi gi — do la giau, khong phai bao")
    print(f"PASS  san {san} tran {tran} -> SL {ra.sl:,.1f} "
          f"({ra.sl_pct}%) · vua ngan sach: {vua}")


def test_VI_TRI_GIA_ba_trang_thai__hai_chieu(monkeypatch):
    """Hàm thuần, thử cả ba nhánh trên đầu vào dựng tay (bài học lỗi 34)."""
    assert mf._vi_tri(130.0, 138.0, 150.0) == "DƯỚI VÙNG"
    assert mf._vi_tri(145.0, 138.0, 150.0) == "TRONG VÙNG"
    assert mf._vi_tri(160.0, 138.0, 150.0) == "TRÊN VÙNG"

    _dat(monkeypatch, 100.0, 200.0)
    assert mf.doc_muc(_df(gia=145.0)).vi_tri_gia == "TRONG VÙNG"
    assert mf.doc_muc(_df(gia=999.0)).vi_tri_gia == "TRÊN VÙNG"
    print("PASS  ba trang thai vi tri gia, ca ham thuan lan duong that")


# ───────────────────── bất biến và đường nối ─────────────────────────

def test_HAM_THUAN__goi_hai_lan_ra_Y_HET(monkeypatch):
    """Bất biến 2. `tv_recommendation` vi phạm đúng điều này (lỗi 63)."""
    _dat(monkeypatch, 100.0, 200.0)
    d = _df()
    assert mf.doc_muc(d) == mf.doc_muc(d)
    print("PASS  cung dau vao -> cung ket qua")


def test_DON_VI_di_vao_bang_DON_VI_di_ra(monkeypatch):
    """Nghìn đồng gặp VNĐ là cái bẫy đã cắn dự án nhiều lần.

    `he_so_gia` chỉ truyền thẳng cho `doc_pha`; module này KHÔNG quy đổi
    thêm lần nào. Nên nhân hệ số lên 1.000 thì mọi mốc giá phải nhân đúng
    1.000, không hơn không kém.
    """
    monkeypatch.setattr(mf.pha_wyckoff, "doc_pha",
                        lambda df, hs=1.0: _pha(100.0 * hs, 200.0 * hs))
    mot = mf.doc_muc(_df(gia=145.0), he_so_gia=1.0)
    nghin = mf.doc_muc(_df(gia=145.0), he_so_gia=1000.0)
    for a, b in ((mot.san, nghin.san), (mot.tran, nghin.tran),
                 (mot.tp1, nghin.tp1), (mot.tp2, nghin.tp2)):
        assert b == pytest.approx(a * 1000, rel=1e-9), (a, b)
    assert mot.sl_pct == nghin.sl_pct, "phan tram KHONG duoc doi theo don vi"
    assert mot.vi_tri_gia == nghin.vi_tri_gia, (
        "vi tri gia phai BAT BIEN theo don vi. Quen nhan he_so_gia vao gia "
        "cuoi thi mot ma nghin-dong se luon doc ra 'DUOI VUNG' — sai am tham, "
        "vi no van la mot nhan hop le.")
    print("PASS  moi moc gia nhan dung 1.000, phan tram va vi tri giu nguyen")


def test_KHONG_TU_DO_dinh_day__phai_di_qua_pha_wyckoff():
    """"Hàm có tồn tại" khác "nhánh có gọi nó" — lỗi 20.

    Đọc AST: `doc_muc` phải gọi `pha_wyckoff.doc_pha`. Không có phép kiểm
    này thì một ngày nào đó nó tự dò đỉnh–đáy, và mọi phép kiểm có
    `monkeypatch` ở trên vẫn xanh.
    """
    cay = ast.parse((GOC / "muc_fibonacci.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "doc_muc")
    goi = {f"{c.func.value.id}.{c.func.attr}" for c in ast.walk(ham)
           if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
           and isinstance(c.func.value, ast.Name)}
    assert "pha_wyckoff.doc_pha" in goi, (
        f"doc_muc khong goi pha_wyckoff.doc_pha — no dang tu do dinh day. "
        f"Cac loi goi thay duoc: {sorted(goi)}")
    print("PASS  doc_muc di qua pha_wyckoff.doc_pha")


def test_O_VUNG_MUA_tren_APP_khong_duoc_quay_ve_GIA_DONG_CUA():
    """Chặn đúng ca người dùng chụp màn hình gửi tới, lỗi 64.

    Từ 18/08/2026 tới 15/09/2026 — **28 ngày** — ô *"Vùng giá mua đề xuất"*
    in ra `latest_close_fmt`, tức giá đóng cửa phiên gần nhất. Nhãn hứa một
    *vùng* và một *đề xuất*; giá trị là dữ liệu thô.

    Ngày 21/08/2026, ba ngày sau khi ô này ra đời, dự án gỡ **hai ô khác**
    vì đúng lý do ấy — lượt dọn đó sửa hai ca và không quét cả lớp
    (`docs/HANDOFF.md` ràng buộc 5).

    Phép kiểm này hẹp có chủ đích: nó không biết *"nhãn nào hứa quá"* nói
    chung — câu đó không đọc được từ văn bản. Nó chỉ chặn ca CỤ THỂ đã trả
    giá 28 ngày quay lại.
    """
    src = (GOC / "app.py").read_text(encoding="utf-8")
    xau = [d.strip() for d in src.splitlines()
           if "Vùng giá mua" in d and "latest_close_fmt" in d]
    assert not xau, (
        f"o 'Vung gia mua' lai bam vao gia dong cua: {xau}\n"
        f"Mot nhan hua VUNG ma in ra mot DIEM la loi 64, va no da song 28 ngay.")

    # Doc bang AST, khong bang `in`: chu `muc_fibonacci` nam ca trong chu
    # thich cua chinh app.py, nen mot phep so van ban se xanh ngay ca khi
    # loi `import` bi go. Luat o CLAUDE.md muc "Gac phai doc AST".
    nhap = {a.name for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Import) for a in n.names}
    nhap |= {n.module for n in ast.walk(ast.parse(src))
             if isinstance(n, ast.ImportFrom) and n.module}
    assert "muc_fibonacci" in nhap, (
        f"app.py khong NHAP `muc_fibonacci` — o vung mua dang lay so tu dau? "
        f"Cac module duoc nhap: {sorted(nhap)[:12]}...")
    print("PASS  o 'Vung gia mua' khong bam vao gia dong cua")


def test_BIEN_SL_phai_KHOP_nguong_ATR_trong_analysis_agents():
    """*Suy ra, đừng gõ* — luật Bước 2, áp cho một ngưỡng nằm ở HAI file.

    `analysis_agents.py` kẹp SL theo ATR bằng `max(0.04, min(0.065, …))`,
    hai con số TRẦN trong mã. `muc_fibonacci` phải dùng đúng biên ấy, nếu
    không thì hai chỗ cùng nói về "rủi ro mỗi lệnh" sẽ trôi khỏi nhau —
    đúng hình dạng `N_DAY_DU` 596/451.

    Đọc bằng regex trên NGUỒN chứ không import: hai số ấy là literal nằm
    trong một biểu thức, không phải hằng số có tên.
    """
    src = (GOC / "analysis_agents.py").read_text(encoding="utf-8")
    # NEO VAO `sl_fraction`, khong bat bieu thuc `max(x, min(y,` dau tien:
    # ban dau tien cua phep kiem nay tom nham mot bieu thuc khac va doc ra
    # bien [10.0, 90.0]. Mot regex qua rong la mot may do hep hon thu no do
    # o chieu nguoc lai — loi 61.
    m = re.search(r"sl_fraction\s*=\s*max\(\s*([\d.]+)\s*,\s*min\(\s*([\d.]+)\s*,",
                  src)
    assert m, ("khong con thay `sl_fraction = max(x, min(y, ...))` trong "
               "analysis_agents.py — doc lai roi sua phep kiem nay")
    hep, rong = float(m.group(1)), float(m.group(2))
    assert (hep, rong) == (mf.SL_HEP_NHAT, mf.SL_RONG_NHAT), (
        f"analysis_agents kep SL vao [{hep}, {rong}] con muc_fibonacci dung "
        f"[{mf.SL_HEP_NHAT}, {mf.SL_RONG_NHAT}] — hai cho noi ve cung mot thu "
        f"va da troi khoi nhau")
    print(f"PASS  hai file cung dung bien SL [{hep}, {rong}]")
