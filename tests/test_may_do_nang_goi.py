"""MÁY ĐO cũng phải bị nghi ngờ như GÁC — và ba máy đo nâng gói chưa có cái nào.

VÌ SAO CÓ FILE NÀY (17/09/2026)
──────────────────────────────
`SKILL.md` Bước 3 điều 4 nói thẳng:

    MAY DO cung phai bi nghi ngo nhu GAC -- va no NGUY HIEM HON, vi mot
    gac sai thi DO, con mot may do sai thi chi IN RA MOT CON SO.

Tới hôm nay dự án có **ba** dụng cụ `tools/do*_nang_*.py` — ĐO 10
(`vnstock`), ĐO 11 (`streamlit`), ĐO 12 (`plotly`) — và **không cái nào có
một dòng test**. Mỗi cái mang một hàm `phan_xu()` thuần, tức phần quyết
định *"nâng được hay không"*, và phần ấy chưa bao giờ bị đục.

Một `phan_xu()` hỏng không làm cổng nào đỏ. Nó chỉ in ra `NANG DUOC`.

QUẦN THỂ SUY RA, KHÔNG GÕ TAY — bài học lỗi 80, áp ngay tại đây
───────────────────────────────────────────────────────────────
`test_MOI_may_do_nang_goi_deu_duoc_phu` **tự tìm** các file
`tools/do*_nang_*.py` rồi đối chiếu với tập đã phủ ở dưới. Thêm ĐO 13 mà
không thêm test thì nó đỏ — không ai phải nhớ.
"""
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import do10_nang_vnstock as d10  # noqa: E402
import do11_nang_streamlit as d11  # noqa: E402
import do12_nang_plotly as d12  # noqa: E402

DA_PHU = {"do10_nang_vnstock", "do11_nang_streamlit", "do12_nang_plotly"}


# ══ quần thể ═══════════════════════════════════════════════════════════
def test_MOI_may_do_nang_goi_deu_duoc_phu():
    """Suy danh sách từ đĩa. Thêm một máy đo mà quên test thì đỏ ở đây."""
    thay = {p.stem for p in (GOC / "tools").glob("do*_nang_*.py")}
    assert thay, "khong tim thay may do nao — phep kiem nay dang mu"
    assert thay == DA_PHU, (
        f"may do chua duoc phu: {sorted(thay - DA_PHU)} · "
        f"da phu nhung khong con tren dia: {sorted(DA_PHU - thay)}")


@pytest.mark.parametrize("mo_dun", (d10, d11, d12))
def test_MOI_may_do_deu_co_phan_xu_va_BA_MA_khac_nhau(mo_dun):
    """Ba ô phải là ba chuỗi khác nhau — trùng nhau là gộp mất một ô."""
    assert callable(mo_dun.phan_xu)
    ba = {mo_dun.KHONG_NANG, mo_dun.CHUA_KET_LUAN}
    ba.add(getattr(mo_dun, "NANG_DUOC", None) or mo_dun.CO_TAC_DUNG)
    assert len(ba) == 3, f"ba o khong phan biet duoc: {ba}"


# ══ ĐO 10 — vnstock ════════════════════════════════════════════════════
def _anh10(bam: str = "aaa", cot=("time", "close"), goi: str = "KHOP",
           cot_b=None, cot_c=None) -> dict:
    """`cot_b` / `cot_c` đổi RIÊNG một ô.

    Bản đầu của hàm này dùng chung một `cot` cho cả A, B và C — nên khi
    đục ô B, ô A bắt hộ và phát đục **sống sót**. Một phép kiểm đổi ba
    biến cùng lúc không nói được gì về biến nào.
    """
    return {
        "vnstock": "4.0.7",
        "A": {m: {"dong": 65, "cot": list(cot), "bam": bam} for m in d10.MA},
        "B": {"cot": list(cot_b if cot_b is not None else cot)},
        "C": {m: {"ky": 54, "cot": list(cot_c if cot_c is not None else cot)}
              for m in d10.MA},
        "D": goi,
    }


def test_DO10_ba_o_deu_dat_toi_duoc():
    assert d10.phan_xu(_anh10(), _anh10())[0] == d10.CO_TAC_DUNG
    assert d10.phan_xu(_anh10(), _anh10(bam="bbb"))[0] == d10.KHONG_NANG
    hong = _anh10()
    hong["A"][d10.MA[0]] = {"loi": "ConnectionError"}
    assert d10.phan_xu(hong, _anh10())[0] == d10.CHUA_KET_LUAN
    assert d10.phan_xu(_anh10(), hong)[0] == d10.CHUA_KET_LUAN


def test_DO10_MOI_O_CHAN_deu_dat_toi_duoc_rieng():
    """A, B, C, D phải chặn được ĐỘC LẬP — một ô không bao giờ chặn là ô chết."""
    assert d10.phan_xu(_anh10(), _anh10(bam="x"))[0] == d10.KHONG_NANG
    assert d10.phan_xu(_anh10(), _anh10(cot_b=("time",)))[0] == d10.KHONG_NANG
    assert d10.phan_xu(_anh10(), _anh10(cot_c=("time",)))[0] == d10.KHONG_NANG
    assert d10.phan_xu(_anh10(), _anh10(goi="LECH"))[0] == d10.KHONG_NANG


# ══ ĐO 11 — streamlit ══════════════════════════════════════════════════
def _anh11(a=d11.CO, b="NHAN", ma_nap: int = 0,
           suc_khoe: str = "ok", tb: bool = False) -> dict:
    return {
        "ban": "1.60.0", "quet_file": 186,
        "A": {"markdown": a},
        "B": {"markdown(unsafe_allow_html)": b},
        "C": {"sheets_store": {"ma": ma_nap, "loi": [""]}},
        "D": {"suc_khoe": suc_khoe, "traceback": tb, "giay": 1.0},
    }


def test_DO11_ba_o_deu_dat_toi_duoc():
    assert d11.phan_xu(_anh11(), _anh11())[0] == d11.NANG_DUOC
    assert d11.phan_xu(_anh11(), _anh11(a=d11.THIEU))[0] == d11.KHONG_NANG
    assert d11.phan_xu(None, _anh11())[0] == d11.CHUA_KET_LUAN
    assert d11.phan_xu(_anh11(suc_khoe=None), _anh11(suc_khoe=None))[0] \
        == d11.CHUA_KET_LUAN


def test_DO11_MOI_O_CHAN_deu_dat_toi_duoc_rieng():
    for sau in (_anh11(a=d11.THIEU), _anh11(b="CHOI"), _anh11(ma_nap=1),
                _anh11(suc_khoe=None), _anh11(tb=True)):
        assert d11.phan_xu(_anh11(), sau)[0] == d11.KHONG_NANG, sau


def test_DO11_CHUA_KIEM_khong_duoc_doc_thanh_THIEU():
    """Ô thứ ba của từng tên: *chưa tra được* khác *không có* (lỗi 66)."""
    kq = d11.phan_xu(_anh11(a=d11.CHUA_KIEM), _anh11(a=d11.CHUA_KIEM))
    assert kq[0] == d11.NANG_DUOC, kq


# ══ ĐO 12 — plotly ═════════════════════════════════════════════════════
def _anh12(a=d12.CO, b="NHAN", ma_nap: int = 0,
           d1="h1", d2="h2", e="h3") -> dict:
    return {
        "ban": "6.9.0", "quet_file": 187,
        "A": {"graph_objects.Candlestick": a},
        "B": {"graph_objects.Candlestick(x)": b},
        "C": {"trade_review": {"ma": ma_nap, "loi": [""]}},
        "D": {"so_trace": 3, "so_hinh": 4, "so_chu_thich": 3,
              "D1": d1, "D2": d2, "E": e,
              "D1_tom": [], "D2_tom": {}, "E_noi_dung": {"template": e}},
    }


def test_DO12_ba_o_deu_dat_toi_duoc():
    assert d12.phan_xu(_anh12(), _anh12())[0] == d12.NANG_DUOC
    assert d12.phan_xu(_anh12(), _anh12(d1="khac"))[0] == d12.KHONG_NANG
    assert d12.phan_xu(None, _anh12())[0] == d12.CHUA_KET_LUAN
    khong_figure = _anh12()
    khong_figure["D"] = {}
    assert d12.phan_xu(_anh12(), khong_figure)[0] == d12.CHUA_KET_LUAN


def test_DO12_MOI_O_CHAN_deu_dat_toi_duoc_rieng():
    for sau in (_anh12(a=d12.THIEU), _anh12(b="CHOI"), _anh12(ma_nap=1),
                _anh12(d1="khac"), _anh12(d2="khac")):
        assert d12.phan_xu(_anh12(), sau)[0] == d12.KHONG_NANG, sau


def test_DO12_o_E_KHONG_duoc_chan_nhung_PHAI_noi_ra():
    """Điểm thiết kế của bảng ĐO 12, và nó phải đỏ được cả hai chiều.

    E chặn → bảng tự định sẵn `KHONG NANG` cho mọi bản CHÍNH.
    E im    → một khác biệt trình bày biến mất khỏi tầm mắt.
    """
    ma, xau, ghi_chu = d12.phan_xu(_anh12(), _anh12(e="khac"))
    assert ma == d12.NANG_DUOC, f"{ma} — o E dang CHAN, no khong duoc chan"
    assert not xau
    assert any("E" in g for g in ghi_chu), "o E doi ma khong ai noi gi"


def test_DO12_ghi_chu_cua_E_phai_CHI_DUOC_CHO_chu_khong_chi_bao_CO_DOI():
    """Lỗi 78: một cảnh báo không chỉ được chỗ nào là cảnh báo không dùng được."""
    _, _, ghi_chu = d12.phan_xu(
        _anh12(), _anh12(e="khac"))
    assert any("template" in g for g in ghi_chu), (
        f"ghi chu khong neu ten khoa nao doi: {ghi_chu}")


def test_DO12_khac_khoa_CAT_gia_tri_dai_nhung_van_neu_TEN():
    dai = "x" * 5000
    ra = d12.khac_khoa({"template": dai}, {"template": "y"})
    assert len(ra) == 1
    assert ra[0].startswith("template:")
    assert len(ra[0]) < 400, "khong cat — mot bang mau se nuot ca ban in"


def test_DO12_bang_gia_CO_DINH_phai_tai_lap_duoc():
    """Bất biến 2: cùng đầu vào, hai lượt, cùng số — nếu không thì phép so
    của ĐO 12 quy được cho hai vế chứ không một."""
    a = d12.bang_gia_co_dinh()
    b = d12.bang_gia_co_dinh()
    assert a.equals(b), "bang gia dau vao khong tai lap duoc"
    assert len(a) == d12.SO_PHIEN
