"""Gác phần CHẠY của B1 (`tools/hau_kiem_loi.py`, BƯỚC 204).

Client GIẢ (ghi lại tham số mỗi lời gọi, trả phản hồi đúng hình dạng Gemini: phần suy
nghĩ `thought=True` đứng TRƯỚC phần chữ) + `sheets_store.InMemorySheet` + bộ tải giá giả:
không mạng, không khoá, không tiền. Hai test dùng gói `google-genai` THẬT (BƯỚC 229) để
khoá lớp lỗi mà phần chạy phân loại và hình dạng `config` mà SDK nhận.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
from types import SimpleNamespace as NS

import pytest

import hau_kiem_loi as hk
import sheets_store as ss

GOC = pathlib.Path(__file__).resolve().parent.parent
BAY_GIO = dt.datetime(2026, 10, 26, 18, 20)


def _nap_cli():
    spec = importlib.util.spec_from_file_location(
        "tools_hau_kiem_loi", GOC / "tools" / "hau_kiem_loi.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CLI = _nap_cli()


def _dong(**doi) -> dict:
    d = {
        "trade_id": 125, "symbol": "HPG", "signal_date": "2026-10-01",
        "entry_date": "2026-10-02", "entry_price": 27450.0,
        "stop_loss_ban_dau": 26100.0, "rui_ro_pct": 4.92, "entry_score": 64,
        "diem_agent": json.dumps({"trend_score": 70.0}), "ly_do": json.dumps(["RSI 71.3"]),
        "boi_canh": json.dumps({"vni_pct_tren_ma50": 2.4}),
        "exit_date": "2026-10-09", "exit_price": 26020.0, "exit_reason": "STOP_LOSS",
        "loi_nhuan_rong_pct": -5.2134, "ket_qua_R": -1.06, "ro_chuan_pct": -1.1,
        "alpha_pct": -4.1134, "hau_kiem_may": "THUA", "hau_kiem_loi": None,
    }
    d.update(doi)
    return d


VAN = {"ke_lai": "Lệnh HPG lỗ 5,21% và thoát vì cắt lỗ ngày 09/10/2026.",
       "khong_chung_minh": "Một lệnh chưa chứng minh được tín hiệu tốt hay xấu.",
       "theo_doi": "Chưa kiểm: lệnh cắt lỗ có hay bị gap dưới cắt lỗ không.",
       "kien_thuc": "Gap là khi giá mở cửa nhảy qua mức cắt lỗ."}


def _phan_hoi(text=None, stop="STOP"):
    text = json.dumps(VAN, ensure_ascii=False) if text is None else text
    return NS(candidates=[NS(content=NS(parts=[NS(text="nghĩ thầm", thought=True),
                                               NS(text=text, thought=None)]),
                             finish_reason=stop)],
              prompt_feedback=None, model_version="gemini-3.8-flash",
              usage_metadata=NS(prompt_token_count=2000, candidates_token_count=1200,
                                thoughts_token_count=300))


def _so(dong_nk, dong_hk=()):
    b = ss.InMemorySheet()
    b.write_all(ss.TAB_NHAT_KY, [list(ss.NHAT_KY_COLS)] + [
        [ss._to_cell(c, d.get(c)) for c in ss.NHAT_KY_COLS] for d in dong_nk])
    if dong_hk:
        ss.them_hau_kiem(b, list(dong_hk))
    return b


class _Client:
    def __init__(self, *tra):
        self.goi: list[dict] = []
        self._tra = list(tra)
        self.models = NS(generate_content=self._create)

    def _create(self, **kw):
        self.goi.append(kw)
        x = self._tra.pop(0)
        if isinstance(x, BaseException):
            raise x
        return x


class _APIError(Exception):
    """Giả `google.genai.errors.APIError`: mang mã HTTP ở `code`."""

    def __init__(self, code):
        super().__init__(f"HTTP {code}")
        self.code = code


#: Lỗi mạng giả mang module `httpx`, như lỗi thật của SDK sau các lần thử lại.
_LoiMang = type("ConnectError", (Exception,), {"__module__": "httpx"})

MOD = NS(APIError=_APIError)


def _tai_hong(ma):
    return None, "FAILED"


def _chay(b, client, *argv):
    return CLI.main(list(argv), backend=b, client=client, loi_mod=MOD,
                    tai_gia=_tai_hong, bay_gio=BAY_GIO)


def _dong_hk(**doi) -> dict:
    d = {c: None for c in hk.COT_HAU_KIEM}
    d.update({"trade_id": 125, "lan": 1, "symbol": "HPG", "exit_date": "2026-10-09",
              "trang_thai": hk.TT_BI_BAC, "model_yeu_cau": hk.MODEL, "effort": hk.EFFORT,
              "bam_loi_dan": "x", "bam_du_kien": "y", "token_vao": 1, "token_ra": 1,
              "chi_phi_usd_uoc": 0.01, "viet_luc": "2026-10-26T10:00:00"})
    d.update(doi)
    return d


# ── Đường chính ──────────────────────────────────────────────────────────

def test_DAT_goi_DUNG_tham_so_va_THEM_mot_dong():
    b, c = _so([_dong()]), _Client(_phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == 1
    nd = hk.noi_dung_gui(hk.du_kien(_dong(), {}))
    assert set(c.goi[0]) == set(hk.tham_so_goi(nd))
    assert c.goi[0]["model"] == hk.MODEL
    assert c.goi[0]["config"] == hk.tham_so_goi(nd)["config"]
    for cam in ("temperature", "top_p", "top_k"):
        assert cam not in c.goi[0]["config"]
    dong = ss.doc_hau_kiem(b)
    assert [(d["trade_id"], d["lan"], d["trang_thai"]) for d in dong] == [(125, 1, hk.TT_DAT)]
    assert dong[0]["ke_lai"] == VAN["ke_lai"]
    assert dong[0]["viet_luc"] == "2026-10-26T18:20:00"
    assert dong[0]["model_yeu_cau"] == hk.MODEL


def test_THU_khong_goi_khong_ghi_khong_can_khoa(monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    b = _so([_dong()])
    assert CLI.main(["--thu"], backend=b, tai_gia=_tai_hong, bay_gio=BAY_GIO) == CLI.MA_XONG
    ra = capsys.readouterr().out
    assert hk.LOI_DAN in ra and "Dữ kiện của lệnh" in ra
    assert ss.doc_hau_kiem(b) == []


def test_TU_CHOI_ghi_dong_co_danh_muc_va_lan_ke_tang():
    b, c = _so([_dong()], [_dong_hk(lan=1)]), _Client(_phan_hoi(stop="SAFETY", text=""))
    assert _chay(b, c) == CLI.MA_XONG
    moi = [d for d in ss.doc_hau_kiem(b) if d["lan"] == 2]
    assert len(moi) == 1 and moi[0]["trang_thai"] == hk.TT_TU_CHOI
    assert "SAFETY" in moi[0]["ly_do_bac"]


def test_LENH_CO_DAT_va_LENH_HET_LUOT_khong_goi(capsys):
    b = _so([_dong(trade_id=1), _dong(trade_id=2)],
            [_dong_hk(trade_id=1, lan=1, trang_thai=hk.TT_DAT),
             _dong_hk(trade_id=2, lan=1), _dong_hk(trade_id=2, lan=2)])
    c = _Client()
    assert _chay(b, c) == CLI.MA_XONG
    assert c.goi == []
    assert "#2" in capsys.readouterr().out


def _bac_nhung_van_dat(**doi) -> dict:
    """Dòng BI_BAC mà văn của nó QUA máy kiểm hiện hành (bị bác vì luật cũ hơn)."""
    return _dong_hk(**{"trang_thai": hk.TT_BI_BAC, "stop_reason": "STOP", **VAN, **doi})


def test_HET_LUOT_chi_tinh_LAN_HONG_THAT_hai_dong_bac_nham_thi_viet_lai(capsys):
    """BƯỚC 234: cron 27/10 — 5 lệnh bị bác ở `lan` 1 (hai lần bác nhầm) đứng ở trần 2 dù văn
    của chúng qua máy kiểm hiện hành. Nay không tính: viết lại ở lần 3, tab giữ nguyên."""
    b = _so([_dong()], [_bac_nhung_van_dat(lan=1), _bac_nhung_van_dat(lan=2)])
    truoc = [dict(d) for d in ss.doc_hau_kiem(b)]
    c = _Client(_phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == 1
    ra = capsys.readouterr().out
    assert "::notice::" in ra and "#125" in ra and "HPG" in ra
    assert "2 dòng không còn tính" in ra and "lần 3" in ra
    assert "dừng" not in ra
    sau = ss.doc_hau_kiem(b)
    assert sau[:2] == truoc and len(sau) == 3          # không sửa, không xoá dòng nào
    assert (sau[2]["lan"], sau[2]["trang_thai"]) == (3, hk.TT_DAT)


def test_HET_LUOT_mot_dong_hong_that_va_mot_dong_bac_nham_thi_van_con_mot_lan(capsys):
    b = _so([_dong()], [_dong_hk(lan=1, stop_reason="STOP", **{**VAN, "kien_thuc": ""}),
                        _bac_nhung_van_dat(lan=2)])
    c = _Client(_phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == 1
    ra = capsys.readouterr().out
    assert "1 dòng không còn tính" in ra and "hỏng thật 1/2" in ra


def test_HET_LUOT_van_dung_khi_hai_lan_hong_THAT(capsys):
    """Bác thật (văn VẪN trượt), từ chối, cắt cụt: mỗi dòng là một lần hỏng thật."""
    for hs in ([_dong_hk(lan=1, stop_reason="STOP", **{**VAN, "ke_lai": "Lệnh HPG lỗ 4,8%."}),
                _dong_hk(lan=2, stop_reason="STOP", **{**VAN, "ke_lai": "Lệnh HPG lỗ 4,6%."})],
               [_dong_hk(lan=1, trang_thai=hk.TT_TU_CHOI, stop_reason="SAFETY"),
                _bac_nhung_van_dat(lan=2, trang_thai=hk.TT_CAT_CUT, stop_reason="MAX_TOKENS")],
               [_dong_hk(lan=1), _dong_hk(lan=2)]):          # stop_reason rỗng: không văn
        b, c = _so([_dong()], hs), _Client()
        assert _chay(b, c) == CLI.MA_XONG
        assert c.goi == []
        ra = capsys.readouterr().out
        assert "::warning::" in ra and "#125" in ra and "hỏng thật 2 lần" in ra
        assert "::notice::" not in ra


def test_HET_LUOT_chi_dem_dong_cua_CHINH_lenh_do_khong_dem_dong_lenh_khac(capsys):
    """Lệnh 1: hai dòng bác nhầm (hồi sinh). Lệnh 2: hai lần hỏng thật (dừng). Dòng của lệnh 2
    không được cộng vào lệnh 1."""
    hang = {"trang_thai": hk.TT_TU_CHOI, "stop_reason": "SAFETY"}
    b = _so([_dong(trade_id=1), _dong(trade_id=2)],
            [_bac_nhung_van_dat(trade_id=1, lan=1), _bac_nhung_van_dat(trade_id=1, lan=2),
             _dong_hk(trade_id=2, lan=1, **hang), _dong_hk(trade_id=2, lan=2, **hang)])
    c = _Client(_phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == 1
    ra = capsys.readouterr().out
    assert "#1 HPG có 2 dòng không đạt, 2 dòng không còn tính" in ra
    assert "#2 HPG đã hỏng thật 2 lần" in ra
    assert [(d["trade_id"], d["lan"]) for d in ss.doc_hau_kiem(b)][-1] == (1, 3)


def test_HET_LUOT_duoc_hoi_sinh_vao_DUNG_cho_theo_ngay_ra_TRUOC_tran_luot(capsys):
    """Lệnh ra SỚM NHẤT được hồi sinh phải nằm trong lượt 10 lệnh (đẩy lệnh ra muộn nhất
    sang lượt sau), và là lệnh được gọi ĐẦU TIÊN."""
    n = hk.SO_LENH_MOI_LUOT
    muon = [_dong(trade_id=100 + i, exit_date=f"2026-10-{10 + i:02d}") for i in range(n)]
    som = _dong(trade_id=7)                                   # ra 2026-10-09: sớm hơn cả n lệnh
    b = _so(muon + [som], [_bac_nhung_van_dat(trade_id=7, lan=1),
                           _bac_nhung_van_dat(trade_id=7, lan=2)])
    c = _Client(*[_phan_hoi() for _ in range(n + 1)])
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == n
    moi = ss.doc_hau_kiem(b)[2:]                              # theo thứ tự ghi = thứ tự gọi
    assert (moi[0]["trade_id"], moi[0]["lan"]) == (7, 3)
    assert len(moi) == n and 100 + n - 1 not in [d["trade_id"] for d in moi]
    assert "1 lệnh để lượt sau" in capsys.readouterr().out


def test_THU_in_ca_lenh_duoc_hoi_sinh(capsys):
    b = _so([_dong()], [_bac_nhung_van_dat(lan=1), _bac_nhung_van_dat(lan=2)])
    assert CLI.main(["--thu"], backend=b, tai_gia=_tai_hong, bay_gio=BAY_GIO) == CLI.MA_XONG
    ra = capsys.readouterr().out
    assert "=== Lệnh #125 HPG" in ra
    assert len(ss.doc_hau_kiem(b)) == 2


def test_CHAM_TRAN_THANG_dung_TRUOC_loi_goi(capsys):
    b = _so([_dong(trade_id=1)], [_dong_hk(trade_id=9, chi_phi_usd_uoc=4.95)])
    c = _Client(_phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert c.goi == []
    assert "chạm trần" in capsys.readouterr().out


def test_TRAN_THANG_cong_CA_tien_vua_tieu_trong_luot():
    """Đã tiêu 4,91 USD trước lượt; mỗi lời gọi giả tốn `chi_phi_uoc(2000, 1500)` ≈ 0,014
    USD, trần một lời gọi ≈ 0,07 USD (giá Gemini bậc trả phí): lời 1 và 2 còn dưới 5 USD,
    lời 3 thì vượt — nếu phần chạy chỉ cộng tiền các lượt TRƯỚC thì nó gọi cả ba."""
    b = _so([_dong(trade_id=i) for i in (1, 2, 3)], [_dong_hk(trade_id=9, chi_phi_usd_uoc=4.91)])
    c = _Client(*[_phan_hoi() for _ in range(3)])
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == 2


def test_TRAN_LUOT_chi_goi_SO_LENH_MOI_LUOT():
    n = hk.SO_LENH_MOI_LUOT + 2
    b = _so([_dong(trade_id=i) for i in range(1, n + 1)])
    c = _Client(*[_phan_hoi() for _ in range(n)])
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == hk.SO_LENH_MOI_LUOT


# ── Lỗi ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ma", [400, 401, 403, 404])
def test_LOI_CAU_HINH_thoat_1_va_khong_ghi(ma):
    b, c = _so([_dong(trade_id=1), _dong(trade_id=2)]), _Client(_APIError(ma), _phan_hoi())
    assert _chay(b, c) == CLI.MA_CAU_HINH
    assert len(c.goi) == 1 and ss.doc_hau_kiem(b) == []


@pytest.mark.parametrize("loi", [_APIError(500), _APIError(503), _APIError(408), _LoiMang("x")])
def test_LOI_TAM_canh_bao_roi_sang_lenh_ke(loi, capsys):
    """Cả model chính lẫn model dự phòng hỏng vì lỗi tạm: cảnh báo, sang lệnh kế."""
    b = _so([_dong(trade_id=1, exit_date="2026-10-08"), _dong(trade_id=2)])
    c = _Client(loi, loi, _phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert [g["model"] for g in c.goi] == [hk.MODEL, hk.MODEL_DU_PHONG, hk.MODEL]
    assert [(d["trade_id"], d["trang_thai"]) for d in ss.doc_hau_kiem(b)] == [(2, hk.TT_DAT)]
    ra = capsys.readouterr().out
    assert "::warning::" in ra and "lượt sau làm lại" in ra


@pytest.mark.parametrize("loi", [_APIError(503), _APIError(504), _LoiMang("x")])
def test_LOI_TAM_o_model_CHINH_thi_model_DU_PHONG_viet_CUNG_lenh(loi):
    """BƯỚC 233: lời gọi chính hỏng vì lỗi tạm (503/504 khi 3.8 Flash quá tải — run
    40472660912) thì gọi `MODEL_DU_PHONG` MỘT lần cho CÙNG lệnh, mọi tham số khác giống
    hệt; dòng ghi model đã gọi thật ở `model_yeu_cau`."""
    b, c = _so([_dong()]), _Client(loi, _phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert [g["model"] for g in c.goi] == [hk.MODEL, hk.MODEL_DU_PHONG]
    khac = [{k: v for k, v in g.items() if k != "model"} for g in c.goi]
    assert khac[0] == khac[1]
    dong = ss.doc_hau_kiem(b)
    assert [(d["trade_id"], d["trang_thai"], d["model_yeu_cau"]) for d in dong] == [
        (125, hk.TT_DAT, hk.MODEL_DU_PHONG)]


def test_HET_HAN_MUC_o_model_DU_PHONG_cung_dung_LUOT(capsys):
    b = _so([_dong(trade_id=1, exit_date="2026-10-08"), _dong(trade_id=2)])
    c = _Client(_APIError(503), _APIError(429), _phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == 2 and ss.doc_hau_kiem(b) == []
    assert "hết hạn mức" in capsys.readouterr().out


def test_LOI_CAU_HINH_o_model_DU_PHONG_thoat_1():
    """Model dự phòng sai tên hay không nhận tham số (400 · 404) là lỗi cấu hình: job ĐỎ
    để người dùng nhận email, như với model chính."""
    b = _so([_dong(trade_id=1), _dong(trade_id=2)])
    c = _Client(_APIError(503), _APIError(404), _phan_hoi())
    assert _chay(b, c) == CLI.MA_CAU_HINH
    assert len(c.goi) == 2 and ss.doc_hau_kiem(b) == []


def test_MOI_MODEL_phan_chay_goi_DEU_CO_GIA():
    """Trần tiền tháng cộng theo giá CAO NHẤT của bảng; model nào phần chạy gọi mà vắng
    bảng thì mức ấy không còn phủ nó — ước dư thành có thể ước thiếu."""
    assert CLI.CHUOI_MODEL[0] == hk.MODEL
    assert len(set(CLI.CHUOI_MODEL)) == len(CLI.CHUOI_MODEL) >= 2
    assert set(CLI.CHUOI_MODEL) <= set(hk.GIA_USD_MOI_TRIEU)


def test_SDK_KHONG_thu_lai_MOI_lenh_toi_da_MOT_request_MOI_model():
    """Bậc miễn phí: 20 request/ngày/model (429 thật, BƯỚC 229), mỗi lần SDK thử lại là
    một request. Từ BƯỚC 233 model dự phòng thay chỗ lần thử lại: mỗi lệnh ăn tối đa MỘT
    request của mỗi model."""
    assert CLI.SO_LAN_THU == 1


def test_MOT_LENH_te_nhat_NGAN_HON_lenh_504_cua_run_40472660912():
    """Run 40472660912 (27/10/2026): mỗi lệnh 504 ăn 358–359 s của lượt 10 phút — cấu hình
    BƯỚC 229 là 2 lần thử × 180 s. Gác vừa-job ở trên KHÔNG bắt việc quay lại 180 s (vẫn
    vừa 20 phút): một lệnh tệ nhất (mọi model, mọi lần thử) phải NGẮN HƠN cấu hình ấy."""
    te_nhat_229 = 2 * 180
    assert len(CLI.CHUOI_MODEL) * CLI.SO_LAN_THU * CLI.THOI_GIAN_CHO_MS / 1000 < te_nhat_229


def test_HET_HAN_MUC_429_dung_LUOT_khong_goi_lenh_ke(capsys):
    """Hạn mức NGÀY của bậc miễn phí hết thì mọi lệnh sau cũng 429 — gọi tiếp chỉ đốt thời
    gian của job (mỗi lời còn được SDK thử lại). Dừng lượt, xanh, lượt sau làm."""
    b = _so([_dong(trade_id=1, exit_date="2026-10-08"), _dong(trade_id=2)])
    c = _Client(_APIError(429), _phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert len(c.goi) == 1 and ss.doc_hau_kiem(b) == []
    assert "hết hạn mức" in capsys.readouterr().out


def test_LOI_LA_khong_bi_nuot_ma_no_ra_ngoai():
    """Lỗi không phải lỗi gọi model (lỗi mã) không được biến thành một cảnh báo xanh."""
    b, c = _so([_dong()]), _Client(TypeError("tham số sai"), _phan_hoi())
    with pytest.raises(TypeError):
        _chay(b, c)


def test_THIEU_KHOA_thoat_2(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    b = _so([_dong()])
    assert CLI.main([], backend=b, tai_gia=_tai_hong, bay_gio=BAY_GIO) == CLI.MA_KHONG_CHAY


def test_TEN_KHOA_phan_chay_doc_DUNG_ten_workflow_dua_vao():
    """Phần chạy đọc khoá bằng `os.environ.get(<tên>)`; workflow phải đưa ĐÚNG tên ấy từ
    secret cùng tên. Lệch một bên thì lượt chạy thật thoát 2 "thiếu khoá" dù secret có
    (phép thiếu-khoá ở trên không bắt được: nó xoá biến nào thì cũng ra thiếu)."""
    import ast
    import re

    cay = ast.parse((GOC / "tools" / "hau_kiem_loi.py").read_text(encoding="utf-8"))
    ten = {n.args[0].value for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and n.func.attr == "get" and isinstance(n.func.value, ast.Attribute)
           and n.func.value.attr == "environ" and n.args
           and isinstance(n.args[0], ast.Constant) and n.args[0].value.endswith("_API_KEY")}
    assert ten == {"GEMINI_API_KEY"}, ten
    wf = (GOC / ".github" / "workflows" / "hau-kiem-loi.yml").read_text(encoding="utf-8")
    dua = re.findall(r"^\s*([A-Z_]+_API_KEY):\s*\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}", wf, re.M)
    assert dua == [("GEMINI_API_KEY", "GEMINI_API_KEY")], dua


def test_HAN_LUOT_qua_gio_thi_KHONG_mo_loi_goi_moi(capsys):
    """Lượt đo 1 (26/10/2026) treo tới trần của job: quá `HAN_LUOT_GIAY` thì dừng xanh."""
    gio = iter([0.0, 0.0, CLI.HAN_LUOT_GIAY + 1.0, CLI.HAN_LUOT_GIAY + 2.0])
    b = _so([_dong(trade_id=1, exit_date="2026-10-08"), _dong(trade_id=2)])
    c = _Client(_phan_hoi(), _phan_hoi())
    assert CLI.main([], backend=b, client=c, loi_mod=MOD, tai_gia=_tai_hong, bay_gio=BAY_GIO,
                    dong_ho=lambda: next(gio)) == CLI.MA_XONG
    assert len(c.goi) == 1
    assert "phút của lượt" in capsys.readouterr().out


def test_HAN_GIO_vua_trong_TIMEOUT_cua_job():
    """Hạn lượt + một LỆNH tệ nhất (mọi model, mọi lần thử đều chờ hết hạn) + 3 phút dựng job
    (đo lượt 1: ~1 phút cài, ~40 giây đọc Sheets và giá) phải nằm trong `timeout-minutes`."""
    import re

    wf = (GOC / ".github" / "workflows" / "hau-kiem-loi.yml").read_text(encoding="utf-8")
    phut = int(re.search(r"^\s*timeout-minutes:\s*(\d+)", wf, re.M).group(1))
    te_nhat = len(CLI.CHUOI_MODEL) * CLI.SO_LAN_THU * CLI.THOI_GIAN_CHO_MS / 1000
    assert CLI.HAN_LUOT_GIAY + te_nhat + 180 <= phut * 60
    assert re.search(r'^\s*PYTHONUNBUFFERED:\s*"1"', wf, re.M)


def test_CLIENT_THAT_dung_HAN_CHO_va_SO_LAN_THU(monkeypatch):
    """Đường không truyền `client`: phần chạy tự dựng `genai.Client` — thay lớp ấy bằng
    bản giả ghi tham số, để khoá `timeout` và `attempts` mà không gọi mạng."""
    from google import genai
    from google.genai import errors

    dung = {}

    class _Gia:
        def __init__(self, **kw):
            dung.update(kw)
            self.models = NS(generate_content=lambda **k: _phan_hoi())

    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.setattr(genai, "Client", _Gia)
    b = _so([_dong()])
    assert CLI.main([], backend=b, tai_gia=_tai_hong, bay_gio=BAY_GIO) == CLI.MA_XONG
    assert dung["api_key"] == "khoa-gia"
    h = dung["http_options"]
    assert h.timeout == CLI.THOI_GIAN_CHO_MS
    assert h.retry_options.attempts == CLI.SO_LAN_THU
    assert [d["trang_thai"] for d in ss.doc_hau_kiem(b)] == [hk.TT_DAT]
    assert errors.APIError  # đường thật dùng đúng module lỗi của SDK


def test_KHONG_DOC_DUOC_SHEETS_thoat_2():
    class _Hong(ss.InMemorySheet):
        def read_rows(self, tab):
            raise OSError("mất mạng")

    assert _chay(_Hong(), _Client()) == CLI.MA_KHONG_CHAY


def test_GHI_TAB_HONG_sau_khi_goi_thi_DUNG_ngay():
    class _GhiHong(ss.InMemorySheet):
        def append_rows(self, tab, rows):
            raise OSError("mất mạng")

    b = _GhiHong()
    b.write_all(ss.TAB_NHAT_KY, [list(ss.NHAT_KY_COLS)] + [
        [ss._to_cell(c, d.get(c)) for c in ss.NHAT_KY_COLS]
        for d in (_dong(trade_id=1), _dong(trade_id=2))])
    c = _Client(_phan_hoi(), _phan_hoi())
    assert _chay(b, c) == CLI.MA_KHONG_CHAY
    assert len(c.goi) == 1


def test_GENAI_THAT_loi_mang_ma_HTTP_va_phan_loai_dung():
    """Phần chạy phân loại theo `APIError.code`: khoá bằng gói thật — lỗi 4xx/5xx thật là
    con của `APIError` và mang đúng mã ở `code` — không bằng bản giả."""
    from google.genai import errors

    def loi(lop, ma):
        return lop(ma, {"error": {"code": ma, "message": "x", "status": "S"}})

    assert issubclass(errors.ClientError, errors.APIError)
    assert issubclass(errors.ServerError, errors.APIError)
    for ma in (400, 401, 403, 404):
        assert CLI._loai_loi(loi(errors.ClientError, ma), errors) == CLI.LOI_CAU_HINH, ma
    assert CLI._loai_loi(loi(errors.ClientError, 429), errors) == CLI.LOI_HET_HAN_MUC
    assert CLI._loai_loi(loi(errors.ServerError, 503), errors) == CLI.LOI_TAM
    assert CLI._loai_loi(_LoiMang("x"), errors) == CLI.LOI_TAM
    assert CLI._loai_loi(ValueError("x"), errors) is None


def test_GENAI_THAT_nhan_DUNG_config_cua_tham_so_goi():
    """`tham_so_goi` là dict thuần; SDK thật phải dựng được `GenerateContentConfig` từ nó
    (sai tên trường thì pydantic nổ) và giữ nguyên lược đồ + mức suy nghĩ."""
    from google.genai import types

    cfg = types.GenerateContentConfig.model_validate(hk.tham_so_goi("x")["config"])
    assert cfg.response_json_schema == hk.SCHEMA_BON_TRUONG
    assert cfg.response_mime_type == "application/json"
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.MEDIUM
    assert cfg.max_output_tokens == hk.MAX_TOKENS and cfg.system_instruction == hk.LOI_DAN
    assert cfg.temperature is None
