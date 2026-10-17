"""Gác phần CHẠY của B1 (`tools/hau_kiem_loi.py`, BƯỚC 204).

Client GIẢ (ghi lại tham số mỗi lời gọi, trả phản hồi đúng hình dạng Opus 5.5) +
`sheets_store.InMemorySheet` + bộ tải giá giả: không mạng, không khoá, không tiền.
Một test dùng gói `anthropic` THẬT để khoá tên và thứ bậc các lớp lỗi mà phần chạy bắt.
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


def _phan_hoi(text=None, stop="end_turn", danh_muc=None):
    text = json.dumps(VAN, ensure_ascii=False) if text is None else text
    return NS(content=[NS(type="thinking", thinking=""), NS(type="text", text=text)],
              stop_reason=stop, model="claude-opus-5-5",
              stop_details=NS(category=danh_muc) if stop == "refusal" else None,
              usage=NS(input_tokens=2000, output_tokens=1500, cache_creation_input_tokens=None,
                       cache_read_input_tokens=None, iterations=None))


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
        self.beta = NS(messages=NS(create=self._create))

    def _create(self, **kw):
        self.goi.append(kw)
        x = self._tra.pop(0)
        if isinstance(x, BaseException):
            raise x
        return x


class _APIStatusError(Exception):
    pass


class _BadRequestError(_APIStatusError):
    pass


class _AuthenticationError(_APIStatusError):
    pass


class _PermissionDeniedError(_APIStatusError):
    pass


class _RateLimitError(_APIStatusError):
    pass


class _APIConnectionError(Exception):
    pass


MOD = NS(APIStatusError=_APIStatusError, BadRequestError=_BadRequestError,
         AuthenticationError=_AuthenticationError, PermissionDeniedError=_PermissionDeniedError,
         RateLimitError=_RateLimitError, APIConnectionError=_APIConnectionError)


def _tai_hong(ma):
    return None, "FAILED"


def _chay(b, client, *argv):
    return CLI.main(list(argv), backend=b, client=client, anthropic_mod=MOD,
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
    for cam in ("thinking", "temperature", "top_p", "top_k"):
        assert cam not in c.goi[0]
    dong = ss.doc_hau_kiem(b)
    assert [(d["trade_id"], d["lan"], d["trang_thai"]) for d in dong] == [(125, 1, hk.TT_DAT)]
    assert dong[0]["ke_lai"] == VAN["ke_lai"]
    assert dong[0]["viet_luc"] == "2026-10-26T18:20:00"


def test_THU_khong_goi_khong_ghi_khong_can_khoa(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    b = _so([_dong()])
    assert CLI.main(["--thu"], backend=b, tai_gia=_tai_hong, bay_gio=BAY_GIO) == CLI.MA_XONG
    ra = capsys.readouterr().out
    assert hk.LOI_DAN in ra and "Dữ kiện của lệnh" in ra
    assert ss.doc_hau_kiem(b) == []


def test_TU_CHOI_ghi_dong_co_danh_muc_va_lan_ke_tang():
    b, c = _so([_dong()], [_dong_hk(lan=1)]), _Client(_phan_hoi(stop="refusal", danh_muc="cyber", text=""))
    assert _chay(b, c) == CLI.MA_XONG
    moi = [d for d in ss.doc_hau_kiem(b) if d["lan"] == 2]
    assert len(moi) == 1 and moi[0]["trang_thai"] == hk.TT_TU_CHOI
    assert "cyber" in moi[0]["ly_do_bac"]


def test_LENH_CO_DAT_va_LENH_HET_LUOT_khong_goi(capsys):
    b = _so([_dong(trade_id=1), _dong(trade_id=2)],
            [_dong_hk(trade_id=1, lan=1, trang_thai=hk.TT_DAT),
             _dong_hk(trade_id=2, lan=1), _dong_hk(trade_id=2, lan=2)])
    c = _Client()
    assert _chay(b, c) == CLI.MA_XONG
    assert c.goi == []
    assert "#2" in capsys.readouterr().out


def test_CHAM_TRAN_THANG_dung_TRUOC_loi_goi(capsys):
    b = _so([_dong(trade_id=1)], [_dong_hk(trade_id=9, chi_phi_usd_uoc=4.95)])
    c = _Client(_phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert c.goi == []
    assert "chạm trần" in capsys.readouterr().out


def test_TRAN_THANG_cong_CA_tien_vua_tieu_trong_luot():
    """Đã tiêu 4,70 USD trước lượt; mỗi lời gọi giả tốn `chi_phi_uoc(2000, 1500)`, trần
    một lời gọi ~0,23 USD: lời 1 và 2 còn dưới 5 USD, lời 3 thì vượt — nếu phần chạy chỉ
    cộng tiền các lượt TRƯỚC thì nó gọi cả ba."""
    b = _so([_dong(trade_id=i) for i in (1, 2, 3)], [_dong_hk(trade_id=9, chi_phi_usd_uoc=4.70)])
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

@pytest.mark.parametrize("loi", [_BadRequestError, _AuthenticationError, _PermissionDeniedError])
def test_LOI_CAU_HINH_thoat_1_va_khong_ghi(loi):
    b, c = _so([_dong(trade_id=1), _dong(trade_id=2)]), _Client(loi("x"), _phan_hoi())
    assert _chay(b, c) == CLI.MA_CAU_HINH
    assert len(c.goi) == 1 and ss.doc_hau_kiem(b) == []


@pytest.mark.parametrize("loi", [_RateLimitError, _APIStatusError, _APIConnectionError])
def test_LOI_TAM_canh_bao_roi_sang_lenh_ke(loi, capsys):
    b = _so([_dong(trade_id=1, exit_date="2026-10-08"), _dong(trade_id=2)])
    c = _Client(loi("x"), _phan_hoi())
    assert _chay(b, c) == CLI.MA_XONG
    assert [(d["trade_id"], d["trang_thai"]) for d in ss.doc_hau_kiem(b)] == [(2, hk.TT_DAT)]
    assert "::warning::" in capsys.readouterr().out


def test_THIEU_KHOA_thoat_2(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    b = _so([_dong()])
    assert CLI.main([], backend=b, tai_gia=_tai_hong, bay_gio=BAY_GIO) == CLI.MA_KHONG_CHAY


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


def test_ANTHROPIC_THAT_co_du_lop_loi_va_lop_hep_dung_duoi_lop_rong():
    """Phần chạy bắt lớp HẸP (cấu hình) trước lớp RỘNG (tạm): thứ tự ấy chỉ đúng khi
    lớp hẹp là con của `APIStatusError`. Khoá bằng gói thật, không bằng bản giả."""
    import anthropic

    for ten in ("AuthenticationError", "PermissionDeniedError", "BadRequestError",
                "RateLimitError", "APIStatusError", "APIConnectionError"):
        assert hasattr(anthropic, ten), ten
    for ten in ("AuthenticationError", "PermissionDeniedError", "BadRequestError",
                "RateLimitError"):
        assert issubclass(getattr(anthropic, ten), anthropic.APIStatusError), ten
    assert set(CLI._loi_cau_hinh(anthropic)) == {
        anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.BadRequestError}
