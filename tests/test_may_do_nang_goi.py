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
import do13_nang_urllib3 as d13  # noqa: E402
import do14_kha_thi_khoi_ngoai as d14  # noqa: E402
import do17_nang_goi_vnstock as d17  # noqa: E402

DA_PHU = {"do10_nang_vnstock", "do11_nang_streamlit", "do12_nang_plotly",
          "do13_nang_urllib3", "do17_nang_goi_vnstock"}


# ══ quần thể ═══════════════════════════════════════════════════════════
def test_MOI_may_do_nang_goi_deu_duoc_phu():
    """Suy danh sách từ đĩa. Thêm một máy đo mà quên test thì đỏ ở đây."""
    thay = {p.stem for p in (GOC / "tools").glob("do*_nang_*.py")}
    assert thay, "khong tim thay may do nao — phep kiem nay dang mu"
    assert thay == DA_PHU, (
        f"may do chua duoc phu: {sorted(thay - DA_PHU)} · "
        f"da phu nhung khong con tren dia: {sorted(DA_PHU - thay)}")


@pytest.mark.parametrize("mo_dun", (d10, d11, d12, d13, d17))
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

# ══ ĐO 13 — urllib3 ════════════════════════════════════════════════════
#
# Ô D0 là thứ ĐO 13 có mà ba máy đo trước không có: nó phải GỌI MẠNG, nên
# endpoint có thể trả khác nhau vì lý do chẳng liên quan tới urllib3. D0
# kéo hai lượt trên CÙNG một bản; hai lượt ấy khác nhau thì D1 nói về
# endpoint chứ không nói về thư viện.


def _anh13(*, urllib3="1.26.20", nap=True, choi=None, tham_so=None,
           D0=True, bam="aaa"):
    """Một ảnh ĐO 13 dựng tay. Mỗi ô đổi được RIÊNG, nên đục thử được
    từng ô mà không kéo theo ô khác — đúng phép sửa của ĐO 10 ô B."""
    return {
        "A": {"nap": nap, "urllib3": urllib3, "requests": "2.34.2"},
        "B": {"get": {"co_ham": True, "nhan": ["params", "timeout"],
                      "choi": choi or []},
              "post": {"co_ham": True, "nhan": ["headers", "json", "timeout"],
                       "choi": []}},
        "C": {"co": True, "tham_so": tham_so or ["a", "b"]},
        "D": {"luot1": {m: {"bam": bam} for m in d13.MA},
              "luot2": {m: {"bam": bam} for m in d13.MA},
              "D0_dat": D0, "giay_luot1": 1.0, "giay_luot2": 1.0},
    }


def test_DO13_hai_anh_giong_het_thi_NANG_DUOC():
    ma, ly_do = d13.phan_xu(_anh13(), _anh13(urllib3="2.8.0"))
    assert ma == d13.NANG_DUOC, (ma, ly_do)


def test_DO13_bam_DU_LIEU_doi_thi_KHONG_NANG():
    """Ô quyết định. Nó phải nêu tên mã lệch, không chỉ kêu chung chung."""
    ma, ly_do = d13.phan_xu(_anh13(bam="aaa"),
                            _anh13(urllib3="2.8.0", bam="bbb"))
    assert ma == d13.KHONG_NANG, (ma, ly_do)
    assert any("D1" in d for d in ly_do), ly_do
    assert any(m in " ".join(ly_do) for m in d13.MA), (
        "khong neu ten ma nao lech — mot con so tong lai (loi 78)")


def test_DO13_D0_KHONG_DAT_thi_CHUA_KET_LUAN_chu_khong_phai_KHONG_NANG():
    """Chỗ dễ sai nhất của cả bảng: endpoint không tất định KHÔNG phải một
    phán quyết về urllib3. Gộp hai ô ấy là đúng lỗi 66."""
    ma, ly_do = d13.phan_xu(_anh13(D0=False),
                            _anh13(urllib3="2.8.0", D0=False))
    assert ma == d13.CHUA_KET_LUAN, (ma, ly_do)
    assert any("D0" in d for d in ly_do), ly_do


def test_DO13_D0_hong_o_MOT_luot_thoi_cung_du_de_CHUA_KET_LUAN():
    ma, _ = d13.phan_xu(_anh13(), _anh13(urllib3="2.8.0", D0=False))
    assert ma == d13.CHUA_KET_LUAN, ma


def test_DO13_import_NO_thi_CHUA_KET_LUAN():
    ma, ly_do = d13.phan_xu(_anh13(), _anh13(urllib3="2.8.0", nap=False))
    assert ma == d13.CHUA_KET_LUAN, (ma, ly_do)


def test_DO13_tu_khoa_bi_CHOI_thi_KHONG_NANG():
    ma, ly_do = d13.phan_xu(_anh13(),
                            _anh13(urllib3="2.8.0", choi=["timeout"]))
    assert ma == d13.KHONG_NANG, (ma, ly_do)
    assert any("timeout" in d for d in ly_do), ly_do


def test_DO13_chu_ky_send_request_DOI_thi_KHONG_NANG():
    """`send_request` là nút thắt MỌI dòng OHLCV đi qua."""
    ma, ly_do = d13.phan_xu(_anh13(tham_so=["a", "b"]),
                            _anh13(urllib3="2.8.0", tham_so=["a"]))
    assert ma == d13.KHONG_NANG, (ma, ly_do)
    assert any("send_request" in d for d in ly_do), ly_do


def test_DO13_khoang_do_phai_la_khoang_DA_DONG():
    """Khoảng chưa đóng thì hai lượt kéo khác nhau vì THỊ TRƯỜNG, không vì
    urllib3 — và khi ấy D0 sẽ đỏ mãi. Neo bằng một mốc quá khứ xa."""
    import datetime as dt
    cuoi = dt.date.fromisoformat(d13.CUOI)
    assert cuoi < dt.date.today() - dt.timedelta(days=180), (
        f"CUOI = {d13.CUOI} qua gan hom nay — khoang chua chac da dong")
    assert dt.date.fromisoformat(d13.DAU) < cuoi


# ══ ĐO 17 — vnai · vnii · vnstock_data, MỘT GÓI MỘT CHẶNG ══════════════
#
# Khác ĐO 10–13 ở ô E: ngày 29/09 có một phép kiểm point-in-time đã ký
# (ĐO 14 ô D) kéo khối ngoại qua chính `vnstock_data`. Nâng gói mà đổi
# cách XUẤT dữ liệu thì băm 29/09 khác vì THƯ VIỆN, không vì NGUỒN — nên
# ô E có một phán quyết riêng, HOAN, không gộp vào KHONG NANG.
#
# Và khác bản nháp đầu của chính nó: ba gói, BA CHẶNG. ĐO 13 điều 5 cấm
# gộp hai phép nâng vào một lượt — khác biệt không quy được cho gói nào.

_CU = {"vnai": "vnai==2.6.0", "vnii": "vnii @ https://x/vnii-0.2.5.tar.gz",
       "vnstock_data": "vnstock_data @ file:///x/vnstock_data-3.3.0.tar.gz"}
_MOI = {"vnai": "vnai==2.6.1", "vnii": "vnii @ file:///x/vnii-0.2.6.tar.gz",
        "vnstock_data": "vnstock_data @ file:///x/vnstock_data-3.3.1.tar.gz"}


def _freeze(*da_nang: str) -> list[str]:
    """Freeze với các gói trong `da_nang` ở bản mới, còn lại ở bản cũ."""
    return ["pandas==3.0.0", "vnstock==4.0.8"] + [
        (_MOI if g in da_nang else _CU)[g] for g in d17.GOI_NANG]


def _f17(*, ma_thoat=0, bat=0, tong=4, rieng_tu="minimal", dich_doi=False):
    bam = {"a": "1", "b": "2", "c": "3"}
    return {"import_ma_thoat": ma_thoat, "bat": bat, "tong": tong,
            "rieng_tu": rieng_tu, "bam_truoc": dict(bam),
            "bam_sau": {**bam, "a": "9"} if dich_doi else dict(bam)}


def _e17(bam=("x", "x"), hinh="start/end", dong=119, ma=("HAH", "GMD", "VHC"),
         bam_rieng=None):
    """`bam` là băm của TỪNG LƯỢT; `bam_rieng` đổi riêng một mã."""
    luot = []
    for b in bam:
        l = {}
        for m in ma:
            bb = (bam_rieng or {}).get(m, b)
            l[m] = {"hinh": hinh, "dong": dong, "cot": ["time"], "bam": bb, "tho": []}
        luot.append(l)
    return {"ma": list(ma), "da_thu": list(ma), "luot": luot}


def _anh17(*, freeze=None, bam_a="aaa", cot_b=None, ky_c=54, cot_c=None,
           goi="KHOP", F=None, E=None):
    do10 = _anh10(bam=bam_a, goi=goi, cot_b=cot_b, cot_c=cot_c)
    for m in d10.MA:
        do10["C"][m]["dong"] = ky_c
    return {"ban": {}, "freeze": freeze if freeze is not None else _freeze(),
            "F": F if F is not None else _f17(), "do10": do10,
            "E": E if E is not None else _e17()}


def _xu17(truoc=None, chang="vnai", **sau):
    """Chặng `chang` so với nền; `sau` mặc định là nền với ĐÚNG gói ấy nâng."""
    sau.setdefault("freeze", _freeze(chang))
    return d17.phan_xu(truoc or _anh17(), _anh17(**sau), chang)


def test_DO17_BON_o_deu_dat_toi_duoc():
    assert _xu17()[0] == d17.NANG_DUOC
    assert _xu17(bam_a="bbb")[0] == d17.KHONG_NANG
    assert _xu17(E=_e17(bam=("y", "y")))[0] == d17.HOAN
    assert _xu17(E=_e17(dong=5))[0] == d17.CHUA_KET_LUAN


def test_DO17_BON_ma_khac_nhau():
    assert len({d17.NANG_DUOC, d17.KHONG_NANG, d17.CHUA_KET_LUAN, d17.HOAN}) == 4


def test_DO17_BA_CHANG_theo_THU_TU_moi_chang_so_voi_chang_NGAY_TRUOC():
    """vnai -> vnii -> vnstock_data. Thứ tự là phần của tiêu chí đã ký."""
    assert d17.GOI_NANG == ("vnai", "vnii", "vnstock_data")
    assert [d17.chang_truoc(g) for g in d17.GOI_NANG] == [
        "truoc", "sau_vnai", "sau_vnii"]


def test_DO17_moi_chang_NANG_DUOC_khi_freeze_doi_DUNG_goi_cua_no():
    da = []
    for g in d17.GOI_NANG:
        nen = _anh17(freeze=_freeze(*da))
        da.append(g)
        ma, ly_do = d17.phan_xu(nen, _anh17(freeze=_freeze(*da)), g)
        assert ma == d17.NANG_DUOC, (g, ma, ly_do)


@pytest.mark.parametrize("chang,sau", [
    ("vnai", ("vnai", "vnii")),              # GOP hai goi vao mot chang
    ("vnai", ("vnai", "vnii", "vnstock_data")),   # ban nhap dau: ca ba mot luot
    ("vnii", ("vnai",)),                     # nang NHAM goi so voi chang
    ("vnai", ()),                            # chua nang gi
    ("pandas", ()),                          # goi ngoai danh sach
])
def test_DO17_chang_doi_KHAC_dung_MOT_goi_cua_no_thi_CHUA_KET_LUAN(chang, sau):
    """Đúng lỗi ĐO 13 điều 5 cấm: gộp phép nâng thì khác biệt không quy được."""
    ma, ly_do = d17.phan_xu(_anh17(), _anh17(freeze=_freeze(*sau)), chang)
    assert ma == d17.CHUA_KET_LUAN, (ma, ly_do)
    assert any("freeze" in x for x in ly_do), ly_do


def test_DO17_freeze_keo_theo_goi_LA_thi_CHUA_KET_LUAN():
    keo_la = _freeze("vnai") + ["squarify==0.4.4"]
    doi_la = [x.replace("pandas==3.0.0", "pandas==3.0.1") for x in _freeze("vnai")]
    for fz in (keo_la, doi_la):
        ma, ly_do = _xu17(freeze=fz)
        assert ma == d17.CHUA_KET_LUAN, (ma, ly_do)


def test_DO17_MOI_O_CON_SO_chan_duoc_RIENG():
    """A, B, C (số kỳ VÀ tập cột), D — mỗi ô một mình phải chặn được.

    Số kỳ của C là vế ĐO 10 không so. Ở đây nó là vế chính: `vnai` giữ
    `PERIOD_LIMITS`, và hạng nhận sai thì BCTC bị cắt còn 8 kỳ mà không
    lỗi, không cảnh báo — đúng sự cố 22/08/2026."""
    assert _xu17(bam_a="x")[0] == d17.KHONG_NANG
    assert _xu17(cot_b=("time",))[0] == d17.KHONG_NANG
    assert _xu17(ky_c=8)[0] == d17.KHONG_NANG
    assert _xu17(cot_c=("time",))[0] == d17.KHONG_NANG
    assert _xu17(goi="LECH")[0] == d17.KHONG_NANG


@pytest.mark.parametrize("f", [
    _f17(bat=1), _f17(rieng_tu="standard"), _f17(ma_thoat=1),
    _f17(dich_doi=True), _f17(tong=3), {"loi": "x"}])
def test_DO17_F_SAU_hong_thi_KHONG_NANG(f):
    """Hai công tắc người dùng tắt 18/09. Bản mới làm mất một cái là lùi."""
    ma, ly_do = _xu17(F=f)
    assert ma == d17.KHONG_NANG, (ma, ly_do)
    assert any("F SAU" in x for x in ly_do), ly_do


def test_DO17_nen_F_TRUOC_hong_thi_CHUA_KET_LUAN():
    """Nền hỏng thì F sau đạt hay không đều không nói gì về bản mới."""
    ma, _ = _xu17(truoc=_anh17(F=_f17(bat=4)))
    assert ma == d17.CHUA_KET_LUAN


def test_DO17_goi_doi_doc_ca_HAI_dang_dong_freeze():
    assert d17.goi_doi(_freeze(), _freeze(*d17.GOI_NANG)) == set(d17.GOI_NANG)
    assert d17.goi_doi(["A-B==1"], ["a_b==2"]) == {"a_b"}
    assert d17.goi_doi(["x==1"], ["x==1"]) == set()


@pytest.mark.parametrize("e_truoc,e_sau", [
    (_e17(bam=("x", "z")), _e17()),                  # truoc tu khong khop
    (_e17(), _e17(bam=("x", "z"))),                  # sau tu khong khop
    (_e17(), _e17(bam_rieng={"GMD": "k"})),          # mot ma cu != moi
    (_e17(), _e17(hinh="start_date/end_date")),      # doi hinh dang loi goi
])
def test_DO17_o_E_lech_thi_HOAN_chu_khong_phai_KHONG_NANG(e_truoc, e_sau):
    """Ô E lệch KHÔNG nói bản mới làm hỏng số — nó nói ô D 29/09 không
    còn đọc được trên bản mới. Hai câu khác nhau, hai hành động khác nhau."""
    ma, ly_do = _xu17(truoc=_anh17(E=e_truoc), E=e_sau)
    assert ma == d17.HOAN, (ma, ly_do)
    assert any("E" in x for x in ly_do), ly_do


@pytest.mark.parametrize("phia", ["truoc", "sau"])
def test_DO17_mot_phia_TU_KHONG_KHOP_phai_NEU_TEN_phia_ay(phia):
    """Hai lượt CÙNG bản cho hai bảng khác nhau nói về NGUỒN, không về thư
    viện. Lý do phải gọi tên phía lệch — một lý do chung chung thì người đọc
    quy nó cho phép nâng (lỗi 78)."""
    lech = _e17(bam=("x", "z"))
    e_truoc, e_sau = (lech, _e17()) if phia == "truoc" else (_e17(), lech)
    ma, ly_do = _xu17(truoc=_anh17(E=e_truoc), E=e_sau)
    assert ma == d17.HOAN, (ma, ly_do)
    assert any(f"E {phia}" in x and "KHAC nhau" in x for x in ly_do), ly_do


def test_DO17_HAI_phia_cung_lech_Y_HET_nhau_van_HOAN():
    """Ca phép so cũ↔mới KHÔNG bắt được: hai tập vân tay bằng nhau vì cả
    hai phía cùng nhảy giữa đúng hai bảng. Ô D so MỘT lượt với MỘT lượt,
    nên một nguồn nhảy như thế làm ô D không đọc được — dù thư viện nào."""
    lech = _e17(bam=("x", "z"))
    ma, ly_do = _xu17(truoc=_anh17(E=lech), E=lech)
    assert ma == d17.HOAN, (ma, ly_do)


@pytest.mark.parametrize("e", [
    _e17(dong=d17.DONG_TOI_THIEU - 1), _e17(ma=("HAH", "GMD")),
    _e17(bam=("x",)), {"loi": "import"},
    _e17(bam_rieng={"VHC": ""}),
])
def test_DO17_o_E_THIEU_thi_CHUA_KET_LUAN(e):
    """Kéo hỏng mà đọc thành 'không đổi gì' là đúng lỗi 66."""
    assert _xu17(E=e)[0] == d17.CHUA_KET_LUAN
    assert _xu17(truoc=_anh17(E=e))[0] == d17.CHUA_KET_LUAN
    # hai phia CUNG thieu mot kieu — phep so ma giua hai phia khong con bat ho
    assert _xu17(truoc=_anh17(E=e), E=e)[0] == d17.CHUA_KET_LUAN


def test_DO17_hai_luot_keo_KHAC_ma_thi_CHUA_KET_LUAN():
    ma, _ = _xu17(E=_e17(ma=("HAH", "GMD", "REE")))
    assert ma == d17.CHUA_KET_LUAN


def test_DO17_A_D_keo_hong_thi_CHUA_KET_LUAN():
    hong = _anh17(freeze=_freeze("vnai"))
    hong["do10"]["A"][d10.MA[0]] = {"loi": "ConnectionError"}
    assert d17.phan_xu(_anh17(), hong, "vnai")[0] == d17.CHUA_KET_LUAN


def test_DO17_o_E_dung_CHUNG_loi_goi_va_CUA_SO_voi_o_D():
    """Ô E chỉ bảo vệ được ô D nếu nó đi đúng đường ô D đi.

    Cửa sổ của ô D là một phép gán cục bộ trong `o_D_bam` — đọc bằng AST,
    không đọc bằng `in` (chú thích cũng chứa hai chuỗi ngày ấy)."""
    import ast
    assert d17.goi_thu is d14.goi_thu
    cay = ast.parse((GOC / "tools" / "do14_kha_thi_khoi_ngoai.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "o_D_bam")
    gan = next(n for n in ast.walk(ham) if isinstance(n, ast.Assign)
               and isinstance(n.targets[0], ast.Tuple)
               and [e.id for e in n.targets[0].elts] == ["tu", "den"])
    assert (d17.TU, d17.DEN) == tuple(ast.literal_eval(gan.value))


def test_DO17_ung_vien_E_NGOAI_ro_khoi_ngoai():
    """Kéo một mã TRONG rổ trước 29/09 là đọc sớm phép kiểm đã hẹn."""
    sys.path.insert(0, str(GOC))
    from vn100_symbols import VN100_SYMBOLS
    trung = set(d17.UNG_VIEN) & set(VN100_SYMBOLS)
    assert not trung, f"ung vien E nam TRONG ro: {sorted(trung)}"
    assert len(d17.UNG_VIEN) >= d17.SO_MA_E


def test_DO17_khoang_E_la_khoang_DA_DONG():
    import datetime as dt
    assert dt.date.fromisoformat(d17.DEN) < dt.date.today() - dt.timedelta(days=180)


def test_DO17_chang_mang_ten_goi_NGOAI_danh_sach_thi_CHUA_KET_LUAN():
    """Kể cả khi freeze đổi đúng một dòng của chính gói ấy."""
    doi_la = [x.replace("pandas==3.0.0", "pandas==3.0.1") for x in _freeze()]
    ma, _ = d17.phan_xu(_anh17(), _anh17(freeze=doi_la), "pandas")
    assert ma == d17.CHUA_KET_LUAN
