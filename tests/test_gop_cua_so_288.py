"""BƯỚC 288 — MỘT lượt tải 1.583 ngày cho biểu đồ ngày, ô Dow và nến tuần/tháng (phương án C, người dùng chọn
*"C: một lượt Entrade (Recommended)"*). Nến ngày/Dow/180 của app GIỐNG HỆT nến `run_daily` chấm; `run_daily`, `collect`
mặc định, `fetch_one` và backtest KHÔNG đổi một byte.

Năm điều được khoá (đột biến ở `docs/STATE.md` BƯỚC 288):

1. **Chuỗi mặc định bất biến**: `CHUOI_CO_PHIEU` / `CHUOI_CHI_SO` đúng bản trên `main` (đọc bằng AST, không đọc giá
   trị lúc chạy), và nguồn khử trùng KHÔNG nằm trong chúng.
2. **Nguồn khử trùng chỉ vào được từ đường biểu đồ của app**: tên mới chỉ xuất hiện ở `nguon_gia_cong_khai.py`,
   `app.py` (chỉ `chuoi_cho_app`) và công cụ đối chiếu; `collect` có tham số `chuoi=None`; `run_daily` · `paper_runner` ·
   `keo_bang_gia` · `nen_su_kien_quyen` · mọi `collect` của app trừ MỘT chỗ KHÔNG truyền `chuoi`.
3. **Phép khử trùng**: giữ nến khối lượng lớn hơn, bằng nhau lấy nến muộn; không trùng thì trả nguyên đối tượng; ngày
   trùng muộn hơn `NGAY_TRUNG_CUOI_DA_BIET` thì nổ (nến trong cửa sổ quét không bao giờ đi qua phép khử).
4. **Golden ngoại tuyến** (JSON thô THẬT chụp 20/11/2026, `tests/du_lieu/entrade_khu_trung_288.json.gz`): chạy CHÍNH
   `tools/doi_chieu_gop_cua_so_288.doi_chieu_mot_ma` — nến Dow (785) và nến biểu đồ (180) của app bằng nến `collect`
   mặc định TỪNG BYTE; cả khi nguồn đầu hỏng (khử trùng nổ) thì vẫn bằng. Lượt mạng thật: xem STATE BƯỚC 288.
5. **App nối đúng và nói thẳng**: một nguồn ghi chú dưới chart tuần/tháng của cổ phiếu (nêu Entrade, ba cặp khử sai);
   nến tuần/tháng KHÔNG vào điểm, khuyến nghị hay sổ (tên chỉ nằm ở `app.py` và `khung_thoi_gian.py`).
"""
import ast
import gzip
import json
import pathlib
import sys

import pandas as pd
import pytest

import nguon_gia_cong_khai as ngk

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(GOC / "tools"))        # append: tools/ không được che mặt các module cùng tên ở gốc repo
import doi_chieu_gop_cua_so_288 as dc288  # noqa: E402
import duyet_repo  # noqa: E402

TEN_MOI = {"NGUON_ENTRADE_KHU_TRUNG", "chuoi_cho_app", "khu_trung_entrade", "_doc_entrade_khu_trung",
           "NGAY_TRUNG_CUOI_DA_BIET"}


def _cay(p):
    return ast.parse((GOC / p).read_text(encoding="utf-8"))


def _file_mot_ma():
    """Mọi file .py của repo (không .venv, không thư mục ẩn, không tests)."""
    for p in sorted(duyet_repo.duyet(GOC, "*.py")):
        r = p.relative_to(GOC)
        if any(x.startswith(".") or x in ("tests", "__pycache__", "node_modules") for x in r.parts):
            continue
        yield r


# ── 1. chuỗi mặc định bất biến ───────────────────────────────────────────────
def _gan(cay, ten):
    for n in cay.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets):
            return n.value
    raise AssertionError(f"khong thay {ten}")


def test_chuoi_mac_dinh_dung_ban_tren_main_theo_AST():
    cay = _cay("nguon_gia_cong_khai.py")
    assert ast.dump(_gan(cay, "CHUOI_CO_PHIEU")) == ast.dump(
        ast.parse("(NGUON_ENTRADE, NGUON_VNDIRECT, NGUON_VPS)", mode="eval").body)
    assert ast.dump(_gan(cay, "CHUOI_CHI_SO")) == ast.dump(
        ast.parse("(NGUON_VNDIRECT, NGUON_IBOARD, NGUON_VPS)", mode="eval").body)


def test_chuoi_nguon_va_ten_cac_nguon_khong_doi_va_khong_co_nguon_khu_trung():
    assert ngk.ten_cac_nguon("ACB") == ("entrade", "vndirect", "vps")
    assert ngk.ten_cac_nguon("VNINDEX") == ("vndirect", "iboard", "vps")
    for ma in ("ACB", "SHS", "VNINDEX"):
        assert ngk.NGUON_ENTRADE_KHU_TRUNG not in ngk.chuoi_nguon(ma)
    assert ngk.CHUOI_CO_PHIEU[0] is ngk.NGUON_ENTRADE
    assert ngk.NGUON_ENTRADE_KHU_TRUNG is not ngk.NGUON_ENTRADE


def test_chuoi_cho_app_thay_dung_mot_nguon_dau_cho_co_phieu_con_chi_so_giu_nguyen():
    cp = ngk.chuoi_cho_app("ACB")
    assert cp[0] is ngk.NGUON_ENTRADE_KHU_TRUNG and cp[1:] == ngk.CHUOI_CO_PHIEU[1:]
    assert [n.ten for n in cp] == ["entrade", "vndirect", "vps"]
    assert ngk.chuoi_cho_app("VNINDEX") is ngk.CHUOI_CHI_SO
    assert ngk.chuoi_cho_app("vnindex") is ngk.CHUOI_CHI_SO


# ── 2. nguồn khử trùng chỉ vào được từ đường biểu đồ của app ─────────────────
def _ten_trong(cay):
    ra = []
    for n in ast.walk(cay):
        ten = (n.attr if isinstance(n, ast.Attribute) else n.id if isinstance(n, ast.Name)
               else n.name if isinstance(n, (ast.alias, ast.FunctionDef)) else None)
        if ten in TEN_MOI:
            ra.append((ten, getattr(n, "lineno", 0)))
    return ra


def test_ten_moi_chi_xuat_hien_o_ba_noi_cho_phep():
    thay = {}
    for r in _file_mot_ma():
        for ten, dong in _ten_trong(ast.parse((GOC / r).read_text(encoding="utf-8"))):
            thay.setdefault(r.as_posix(), set()).add(ten)
    assert set(thay) == {"nguon_gia_cong_khai.py", "app.py", "tools/doi_chieu_gop_cua_so_288.py"}, thay
    assert thay["app.py"] == {"chuoi_cho_app"}
    assert thay["tools/doi_chieu_gop_cua_so_288.py"] == {"chuoi_cho_app"}


def _goi_collect(cay):
    return [n for n in ast.walk(cay) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "collect"
            and isinstance(getattr(n.func, "value", None), ast.Call)
            and getattr(n.func.value.func, "id", "") == "VNStockCollectorAgent"]


def test_collect_co_tham_so_chuoi_mac_dinh_None_va_chuyen_tiep_cho_lay_ohlcv():
    cay = _cay("data_collectors.py")
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "collect"
               and n.args.args[0].arg == "self" and n.args.args[1].arg == "symbol")
    ten = [a.arg for a in ham.args.args]
    mac = {a.arg: d for a, d in zip(ham.args.args[-len(ham.args.defaults):], ham.args.defaults)}
    assert "chuoi" in ten and isinstance(mac["chuoi"], ast.Constant) and mac["chuoi"].value is None
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "lay_ohlcv"]
    assert len(goi) == 1
    kw = {k.arg: ast.unparse(k.value) for k in goi[0].keywords}
    assert kw.get("chuoi") == "chuoi"


@pytest.mark.parametrize("tep", ["run_daily.py", "paper_runner.py", "keo_bang_gia.py", "nen_su_kien_quyen.py"])
def test_duong_quet_va_cac_noi_khac_goi_collect_KHONG_truyen_chuoi(tep):
    for g in _goi_collect(_cay(tep)):
        assert "chuoi" not in {k.arg for k in g.keywords}, f"{tep}:{g.lineno}"
    # run_daily gọi `collector.collect` (một biến), nên kiểm riêng mọi lời gọi `.collect(` có từ khoá `chuoi`
    for n in ast.walk(_cay(tep)):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "collect":
            assert "chuoi" not in {k.arg for k in n.keywords}, f"{tep}:{n.lineno}"


def test_app_chi_MOT_loi_goi_collect_truyen_chuoi_va_no_nam_trong_load_stock_data_nguon():
    cay = _cay("app.py")
    co = [(h.name, k) for h in ast.walk(cay) if isinstance(h, ast.FunctionDef)
          for n in ast.walk(h) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "collect"
          for k in n.keywords if k.arg == "chuoi"]
    ten_ham = [h for h, _ in co]
    assert ten_ham == ["load_stock_data_nguon"], ten_ham
    assert ast.unparse(co[0][1].value) == "_ngk_app.chuoi_cho_app(ticker)"
    # `load_stock_data` (đường cũ, VN-INDEX và mọi nơi khác) không truyền
    ham = next(h for h in ast.walk(cay) if isinstance(h, ast.FunctionDef) and h.name == "load_stock_data")
    assert all("chuoi" not in {k.arg for k in n.keywords} for n in ast.walk(ham)
               if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "collect")


def test_fetch_one_va_backtest_khong_nhac_ten_moi_va_van_dung_chuoi_mac_dinh():
    cay = _cay("backtest/data.py")
    assert not _ten_trong(cay)
    src = (GOC / "backtest" / "data.py").read_text(encoding="utf-8")
    assert "theo_ten = {n.ten: n for n in (ngk.NGUON_ENTRADE, ngk.NGUON_VNDIRECT," in src


# ── 3. phép khử trùng ────────────────────────────────────────────────────────
def _ts(ngay, gio_utc=2):
    return int((pd.Timestamp(ngay) + pd.Timedelta(hours=gio_utc) - pd.Timestamp("1970-01-01")).total_seconds())


def _cot(rows):
    """rows = [(ngay, gio_utc, khoi)] -> (t,o,h,l,c,v)."""
    return ([_ts(n, g) for n, g, _ in rows], [1.0 + i for i in range(len(rows))], [2.0 + i for i in range(len(rows))],
            [0.5 + i for i in range(len(rows))], [1.5 + i for i in range(len(rows))], [k for _, _, k in rows])


def test_khong_trung_thi_tra_nguyen_doi_tuong():
    cot = _cot([("2022-12-26", 2, 10), ("2022-12-27", 2, 20)])
    assert ngk.khu_trung_entrade(cot) is cot


def test_trung_thi_giu_nen_khoi_luong_lon_hon_va_giu_thu_tu_va_cac_nen_khac():
    cot = _cot([("2022-12-26", 2, 10), ("2022-12-27", 0, 418_000), ("2022-12-27", 2, 2_040_100),
                ("2022-12-28", 2, 30)])
    t, o, h, l, c, v = ngk.khu_trung_entrade(cot)
    assert v == [10, 2_040_100, 30]
    assert o == [1.0, 3.0, 4.0] and c == [1.5, 3.5, 4.5]              # nến giữ mang đúng giá của CHÍNH nó
    assert t == [cot[0][0], cot[0][2], cot[0][3]]
    # nến giữ là nến SAU: đảo vị trí hai nến thì vẫn giữ nến khối lượng lớn
    cot2 = _cot([("2022-12-27", 2, 2_040_100), ("2022-12-27", 0, 418_000)])
    assert ngk.khu_trung_entrade(cot2)[5] == [2_040_100]


def test_khoi_luong_bang_nhau_thi_giu_nen_muon_hon():
    cot = _cot([("2022-12-27", 0, 500), ("2022-12-27", 2, 500)])
    t, o, *_ = ngk.khu_trung_entrade(cot)
    assert t == [cot[0][1]] and o == [2.0]


def test_ngay_trung_muon_hon_moc_da_biet_thi_NO():
    cot = _cot([("2023-04-11", 0, 10), ("2023-04-11", 2, 20)])
    with pytest.raises(ngk.NguonGiaLoi, match="cùng một ngày phiên"):
        ngk.khu_trung_entrade(cot)
    # đúng ngày mốc thì được khử
    assert ngk.khu_trung_entrade(_cot([("2023-04-10", 0, 10), ("2023-04-10", 2, 20)]))[5] == [20]


def test_moc_ngay_trung_cuoi_la_10_04_2023():
    import datetime
    assert ngk.NGAY_TRUNG_CUOI_DA_BIET == datetime.date(2023, 4, 10)


def test_khoi_luong_khong_doc_duoc_o_nen_trung_thi_NO_va_mang_lech_do_dai_thi_NO():
    cot = _cot([("2022-12-27", 0, None), ("2022-12-27", 2, 5)])
    with pytest.raises(ngk.NguonGiaLoi):
        ngk.khu_trung_entrade(cot)
    t, o, h, l, c, v = _cot([("2022-12-26", 2, 1)])
    with pytest.raises(ngk.NguonGiaLoi, match="khác độ dài"):
        ngk.khu_trung_entrade((t, o, h, l, c, []))
    assert ngk.khu_trung_entrade(([], [], [], [], [], [])) == ([], [], [], [], [], [])


def test_dung_khung_van_chan_chuoi_trung_con_nguon_khu_trung_thi_qua():
    cot = _cot([("2022-12-26", 2, 10), ("2022-12-27", 0, 5), ("2022-12-27", 2, 20)])
    d1, d2 = pd.Timestamp("2022-12-01").date(), pd.Timestamp("2023-01-31").date()
    with pytest.raises(ngk.NguonGiaLoi, match="cùng một ngày phiên"):
        ngk.dung_khung(cot, d1, d2)                                  # nguồn Entrade mặc định: lỗi cũ còn nguyên
    df = ngk.dung_khung(ngk.khu_trung_entrade(cot), d1, d2)
    assert list(df["volume"]) == [10, 20] and not df["time"].duplicated().any()


def test_doc_entrade_khu_trung_nhan_no_data_va_loi_nhu_doc_phang():
    assert ngk.NGUON_ENTRADE_KHU_TRUNG.doc({"s": "no_data"}) == ([], [], [], [], [], [])
    with pytest.raises(ngk.NguonGiaLoi):
        ngk.NGUON_ENTRADE_KHU_TRUNG.doc({"s": "error"})
    assert ngk.NGUON_ENTRADE_KHU_TRUNG.ten == "entrade" and ngk.NGUON_ENTRADE_KHU_TRUNG.url is ngk._url_entrade


# ── 4. golden ngoại tuyến trên JSON thô thật ─────────────────────────────────
@pytest.fixture(scope="module")
def chup():
    with gzip.open(pathlib.Path(__file__).resolve().parent / "du_lieu" / "entrade_khu_trung_288.json.gz", "rt",
                   encoding="utf-8") as f:
        return json.load(f)


def _phat_lai(monkeypatch, chup, them_trung_muon=None):
    """Thay `ngk._http_json` bằng máy chủ GIẢ phát lại JSON thô, lọc theo `from`/`to` của URL như máy chủ thật
    (không lọc thì kiểm 'trùng ngày' của `dung_khung` chạy trên cả lịch sử cũ ở mọi cửa sổ — kết quả sai do máy đo)."""
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    dem = []

    def http(url, accept="*/*"):
        nguon = "entrade" if "entrade" in url else "vndirect" if "vndirect" in url else "vps"
        ma = url.split("symbol=")[1].split("&")[0]
        dem.append((nguon, ma, url))
        j = chup.get(nguon, {}).get(ma)
        if j is None:
            raise ngk.NguonGiaLoi("HTTP 404")
        a, b = int(url.split("from=")[1].split("&")[0]), int(url.split("to=")[1].split("&")[0])
        giu = [i for i, x in enumerate(j["t"]) if a <= x <= b]
        ra = {k: ([v[i] for i in giu] if isinstance(v, list) else v) for k, v in j.items()}
        if them_trung_muon and nguon == "entrade" and ma in them_trung_muon:
            i = len(ra["t"]) - 30                                   # nhân đôi một nến NẰM TRONG cửa sổ quét
            for k, v in ra.items():
                if isinstance(v, list):
                    v.insert(i + 1, v[i] + 7200 if k == "t" else v[i])
        return ra
    monkeypatch.setattr(ngk, "_http_json", http)
    return dem


@pytest.mark.parametrize("ma", ["ACB", "DHG", "AAA", "SHS"])
def test_GOLDEN_nen_Dow_va_bieu_do_cua_app_bang_nen_quet_tung_byte(monkeypatch, chup, ma):
    _phat_lai(monkeypatch, chup)
    r = dc288.doi_chieu_mot_ma(ma, chup["den"])
    assert r.ghi_chu == [] and r.nguon_cua_so_rong == "entrade"
    assert r.quet_giong and r.so_hang_lech_quet == 0 and r.so_nen_quet >= 780
    assert r.bieu_do_giong and r.so_nen_bieu_do >= 120


def test_GOLDEN_cua_so_1583_co_ngay_trung_that_va_phep_khu_xuong_dung_mot_nen_moi_ngay(monkeypatch, chup):
    import data_collectors as dc
    for ma, ngay_trung in (("DHG", ["2022-12-27", "2023-04-07"]), ("AAA", ["2022-12-27", "2023-04-10"]),
                           ("ACB", ["2022-12-27"])):
        _phat_lai(monkeypatch, chup)
        tu = (pd.Timestamp(chup["den"]) - pd.Timedelta(days=1583)).strftime("%Y-%m-%d")
        r = dc.VNStockCollectorAgent().collect(ma, tu, chup["den"], exchange="HOSE", chuoi=ngk.chuoi_cho_app(ma))
        assert r["status"] == "OK" and r["source"] == "entrade", r["note"]
        t = pd.to_datetime(r["df"]["time"])
        assert not t.duplicated().any() and len(r["df"]) == ngk.cua_so_vci_cu(tu, chup["den"])[1]
        for ng in ngay_trung:                                         # ngày trùng có đúng MỘT nến
            assert (t == pd.Timestamp(ng)).sum() == 1
        # nến GIỮ là nến khối lượng lớn hơn (JSON thô: ACB 27/12/2022 418.000 | 2.040.100; DHG 07/04/2023 1.000 | 500 —
        # nến ĐẦU thắng, không phải nến muộn; AAA 10/04/2023 270.500 | 2.844.900)
        khoi = {(m, ng): v for m, ng, v in (("ACB", "2022-12-27", 2_040_100), ("DHG", "2023-04-07", 1_000),
                                            ("AAA", "2023-04-10", 2_844_900))}
        for (m, ng), v in khoi.items():
            if m == ma:
                assert int(r["df"].loc[t == pd.Timestamp(ng), "volume"].iloc[0]) == v
        # chuỗi MẶC ĐỊNH vẫn thấy lỗi cũ: Entrade bị bỏ ở cửa sổ này (điều BƯỚC 288 giữ nguyên cho đường quét)
        if ma == "DHG":
            m = dc.VNStockCollectorAgent().collect(ma, tu, chup["den"], exchange="HOSE")
            assert m["source"] == "vndirect" and m["note"].count("đã bỏ: entrade") == 1


def test_GOLDEN_nguon_dau_hong_vi_trung_muon_thi_app_roi_sang_duong_cu_va_VAN_bang_nen_quet(monkeypatch, chup):
    """Entrade sinh một ngày trùng NẰM TRONG cửa sổ quét (muộn hơn mốc đã biết): phép khử nổ, `tai_mot_lan` về đường
    cũ; `collect` mặc định cũng bỏ Entrade ở cửa sổ quét -> cả hai cùng đi VNDirect -> vẫn giống từng byte."""
    _phat_lai(monkeypatch, chup, them_trung_muon={"DHG"})
    r = dc288.doi_chieu_mot_ma("DHG", chup["den"])
    assert r.ghi_chu == []
    assert r.nguon_cua_so_rong == "vndirect"                       # nguồn đầu (Entrade khử trùng) bị bỏ -> VNDirect
    assert r.quet_giong and r.bieu_do_giong


def test_GOLDEN_may_do_bat_duoc_khac_biet_that(monkeypatch, chup):
    """Máy đo phải CÓ KHẢ NĂNG báo LỆCH: thay phép khử bằng nguồn đầu Entrade KHÔNG khử + chuỗi VNDirect ở cửa sổ rộng
    (thiết kế B bị bác) thì nến Dow lệch nến quét."""
    import gia_mot_lan as g1l
    _phat_lai(monkeypatch, chup)
    monkeypatch.setattr(ngk, "chuoi_cho_app", lambda ma: (ngk.NGUON_VNDIRECT, ngk.NGUON_VPS))
    monkeypatch.setattr(g1l, "nguon_dau_chuoi", lambda tk: "vndirect")   # cho phép cắt từ lượt VNDirect
    r = dc288.doi_chieu_mot_ma("DHG", chup["den"])
    assert r.nguon_cua_so_rong == "vndirect"
    assert not r.quet_giong                                          # nến Dow làm tròn khác nến quét (hoặc lệch cả hình dạng)
    assert not r.bieu_do_giong


def test_hang_so_cua_cong_cu_doi_chieu_bang_hang_so_that_cua_run_daily_va_app():
    import khung_thoi_gian as kt         # tool KHÔNG nhập module này (gác "chỉ app.py nhập"), nên khoá số ở đây
    assert dc288.NGAY_RONG == kt.NGAY_LICH_CHO_KHUNG_THANG
    rd = next(n for n in _cay("run_daily.py").body if isinstance(n, ast.Assign)
              and any(getattr(t, "id", "") == "NGAY_LICH_SU" for t in n.targets))
    assert ast.literal_eval(rd.value) == dc288.NGAY_QUET
    ap = next(n for n in ast.walk(_cay("app.py")) if isinstance(n, ast.Assign)
              and any(getattr(t, "id", "") == "days_back" for t in n.targets))
    assert ast.literal_eval(ap.value) == dc288.NGAY_BIEU_DO


# ── 5. app nối đúng và nói thẳng ─────────────────────────────────────────────
def test_chu_thich_nguon_nen_tuan_thang_nay_Entrade_va_ba_cap_khu_sai():
    cay = _cay("app.py")
    ghi = ast.literal_eval(_gan(cay, "_GHI_CHU_NGUON_KHUNG_GOP"))
    for can in ("Entrade", "VNDirect", "26%", "5 đồng", "1.300 đồng", "AAA 10/04/2023", "DHG và MSR 07/04/2023",
                "khối lượng lớn hơn"):
        assert can in ghi, can
    # cổ phiếu truyền ghi chú; VN-INDEX (vẫn VNDirect) thì KHÔNG
    goi = {g.args[0].id if isinstance(g.args[0], ast.Name) else "": g for g in ast.walk(cay)
           if isinstance(g, ast.Call) and getattr(g.func, "id", "") == "_ve_khung_gop"}
    assert len(goi["_nen_ck"].args) == 5 and ast.unparse(goi["_nen_ck"].args[4]) == "_GHI_CHU_NGUON_KHUNG_GOP"
    assert len(goi["nen_vn"].args) == 4
    ham = next(h for h in ast.walk(cay) if isinstance(h, ast.FunctionDef) and h.name == "_ve_khung_gop")
    assert any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_chu_thich_khung"
               and len(n.args) == 2 for n in ast.walk(ham))


def test_nen_tuan_thang_khong_vao_diem_khuyen_nghi_hay_so_ten_chi_o_app_va_khung_thoi_gian():
    """Lệnh tái lập (đã chạy 20/11/2026, in ở STATE BƯỚC 288): AST mọi file .py ngoài tests tìm `khung_thoi_gian`,
    `NGAY_LICH_CHO_KHUNG_THANG`, `gop_nen`, `nen_ngay_da_dong` — chỉ `app.py` và chính module."""
    ten = {"khung_thoi_gian", "NGAY_LICH_CHO_KHUNG_THANG", "gop_nen", "nen_ngay_da_dong", "_nen_ba_khung"}
    thay = {}
    for r in _file_mot_ma():
        for n in ast.walk(ast.parse((GOC / r).read_text(encoding="utf-8"))):
            t = (n.attr if isinstance(n, ast.Attribute) else n.id if isinstance(n, ast.Name)
                 else n.name if isinstance(n, ast.alias) else n.name if isinstance(n, ast.FunctionDef) else None)
            if t in ten:
                thay.setdefault(r.as_posix(), set()).add(t)
    assert set(thay) <= {"app.py", "khung_thoi_gian.py"}, thay
    # trong app.py, kết quả `_nen_ba_khung` chỉ đi vào hai hàm VẼ/CHÚ THÍCH, không vào `master`/`ke_hoach`/sổ
    cay = _cay("app.py")
    dung = {ast.unparse(g.func) for g in ast.walk(cay) if isinstance(g, ast.Call) and any(
        isinstance(a, ast.Name) and a.id in ("_nen_ck", "nen_vn") for a in g.args)}
    assert dung == {"_hien_dong_pha", "_ve_khung_gop"}, dung
