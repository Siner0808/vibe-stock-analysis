"""Gác B1 — hậu kiểm BẰNG LỜI cho lệnh ảo đã đóng (`hau_kiem_loi.py`, BƯỚC 203).

Đặc tả: `docs/thiet-ke-b1-hau-kiem-loi.md`. File này canh phần THUẦN: lược đồ tab,
luật viết và máy kiểm, dữ kiện gửi đi, tiền, chọn lệnh cần viết, tách phản hồi API
(phản hồi GIẢ, đúng hình dạng Opus 5.5: khối `thinking` đứng TRƯỚC khối `text`),
và phép đo vế "có lời" của tiêu chí B. Không gọi mạng, không cần khoá.
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import pathlib
from types import SimpleNamespace as NS

import pytest

import hau_kiem_loi as hk
import so_bai_hoc

GOC = pathlib.Path(__file__).resolve().parent.parent
NGUON = (GOC / "hau_kiem_loi.py").read_text(encoding="utf-8")
CAY = ast.parse(NGUON)


def _ham(ten: str) -> ast.FunctionDef:
    for n in CAY.body:
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"không thấy hàm {ten}")


def _dong(**doi) -> dict:
    """Một dòng nhật ký ĐÃ ĐÓNG, đúng các cột `nhat_ky_vi_sao.COT_NHAT_KY`."""
    d = {
        "trade_id": 125, "symbol": "HPG", "signal_date": "2026-10-01",
        "entry_date": "2026-10-02", "entry_price": 27450.0,
        "stop_loss_ban_dau": 26100.0, "rui_ro_pct": 4.92, "entry_score": 64,
        "diem_agent": json.dumps({"trend_score": 70.0, "momentum_score": 65.5}),
        "ly_do": json.dumps(["RSI 71.3 trên ngưỡng"]),
        "boi_canh": json.dumps({"vni_pct_tren_ma50": 2.4}),
        "exit_date": "2026-10-09", "exit_price": 26020.0, "exit_reason": "STOP_LOSS",
        "loi_nhuan_rong_pct": -5.2134, "ket_qua_R": -1.06, "ro_chuan_pct": -1.1,
        "alpha_pct": -4.1134, "hau_kiem_may": "THUA | gap dưới cắt lỗ",
        "hau_kiem_loi": None,
    }
    d.update(doi)
    return d


def _du_kien(**doi) -> dict:
    d = _dong(**doi)
    return hk.du_kien(d, so_bai_hoc.lap_bai_hoc(d))


def _van(**doi) -> dict:
    v = {"ke_lai": "Lệnh HPG lỗ 5,21% và thoát vì cắt lỗ ngày 09/10/2026.",
         "khong_chung_minh": "Một lệnh chưa chứng minh được tín hiệu tốt hay xấu.",
         "theo_doi": "Chưa kiểm: lệnh cắt lỗ có hay bị gap dưới cắt lỗ không.",
         "kien_thuc": "Gap là khi giá mở cửa nhảy qua mức cắt lỗ."}
    v.update(doi)
    return v


def _luat_vi_pham(van: dict, dk: dict | None = None) -> set[str]:
    return {v.split(":", 1)[0] for v in hk.kiem_dau_ra(van, _du_kien() if dk is None else dk)}


# ── Lược đồ, schema, hằng số ─────────────────────────────────────────────

def test_LUOC_DO_tab_dung_thu_tu_dac_ta():
    assert hk.COT_HAU_KIEM == (
        "trade_id", "lan", "symbol", "exit_date", "trang_thai", "ly_do_bac",
        "ke_lai", "khong_chung_minh", "theo_doi", "kien_thuc", "model_yeu_cau",
        "model_phuc_vu", "effort", "bam_loi_dan", "bam_du_kien", "token_vao",
        "token_ra", "chi_phi_usd_uoc", "stop_reason", "viet_luc")
    assert hk.COT_SO_NGUYEN == {"trade_id", "lan", "token_vao", "token_ra"}
    assert hk.COT_SO_THUC == {"chi_phi_usd_uoc"}
    assert hk.COT_CHU_RONG_DUOC <= set(hk.COT_HAU_KIEM)


def test_SCHEMA_bon_truong_bat_buoc_khong_truong_la():
    s = hk.SCHEMA_BON_TRUONG
    assert s["required"] == list(hk.TRUONG)
    assert s["additionalProperties"] is False
    assert s["properties"] == {t: {"type": "string"} for t in hk.TRUONG}
    assert hk.TRUONG == ("ke_lai", "khong_chung_minh", "theo_doi", "kien_thuc")


def test_MODEL_EFFORT_va_tran_dung_quyet_dinh_nguoi_dung():
    assert hk.MODEL == "claude-opus-5-5"
    assert hk.EFFORT == "medium"
    assert hk.TRAN_USD_THANG == 5.0
    assert hk.SO_LENH_MOI_LUOT == 10
    assert hk.SO_LAN_TOI_DA == 2


def test_LUAT_VIET_sau_ma_va_moi_cau_dan_nam_NGUYEN_VAN_trong_LOI_DAN():
    assert [l.ma for l in hk.LUAT_VIET] == [
        "so-co-nguon", "mot-lenh", "khong-khuyen-nghi", "ma-co-nguon",
        "gia-thuyet-dan-nhan", "do-dai"]
    for l in hk.LUAT_VIET:
        assert l.dan and l.dan in hk.LOI_DAN, l.ma


def test_LOI_DAN_DUNG_TU_LUAT_VIET_khong_go_tay():
    """Luật nói với model và luật máy kiểm là MỘT bảng: `LOI_DAN` phải là một
    biểu thức đọc `LUAT_VIET`, không phải chuỗi gõ lại."""
    gan = [n for n in CAY.body
           if (isinstance(n, ast.Assign) and any(
               isinstance(t, ast.Name) and t.id == "LOI_DAN" for t in n.targets))
           or (isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
               and n.target.id == "LOI_DAN")]
    assert len(gan) == 1
    ten = {n.id for n in ast.walk(gan[0].value) if isinstance(n, ast.Name)}
    assert "LUAT_VIET" in ten


def test_DO_DAI_trong_LOI_DAN_suy_tu_GIOI_HAN_TU():
    dan = next(l.dan for l in hk.LUAT_VIET if l.ma == "do-dai")
    for t, n in hk.GIOI_HAN_TU.items():
        assert f"{t}" in dan and f"{n}" in dan


def test_MODULE_khong_nhap_anthropic_va_muc_module_chi_thu_vien_chuan():
    """`sheets_store` nhập file này để lấy lược đồ — mức module chỉ được thư viện
    chuẩn (nhập `so_bai_hoc` ở mức module sẽ kéo cả `paper_trading`). Và module
    thuần không bao giờ nhập `anthropic`: chỉ phần chạy làm việc ấy."""
    import sys
    for n in ast.walk(CAY):
        if isinstance(n, ast.Import):
            assert all(a.name.split(".")[0] != "anthropic" for a in n.names)
        if isinstance(n, ast.ImportFrom):
            assert (n.module or "").split(".")[0] != "anthropic"
    for n in CAY.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                assert a.name.split(".")[0] in sys.stdlib_module_names, a.name
        if isinstance(n, ast.ImportFrom) and n.module != "__future__":
            assert n.module.split(".")[0] in sys.stdlib_module_names, n.module


def test_THAM_SO_GOI_dung_hop_dong_Opus_5_5():
    t = hk.tham_so_goi("nội dung")
    assert set(t) == {"model", "max_tokens", "system", "messages", "output_config",
                      "betas", "fallbacks"}
    assert t["model"] == "claude-opus-5-5" and t["max_tokens"] == hk.MAX_TOKENS
    assert t["system"] == hk.LOI_DAN
    assert t["messages"] == [{"role": "user", "content": "nội dung"}]
    assert t["output_config"] == {"effort": "medium", "format": {
        "type": "json_schema", "schema": hk.SCHEMA_BON_TRUONG}}
    assert t["betas"] == ["server-side-fallback-2026-07-01"] and t["fallbacks"] == "default"


# ── Máy kiểm: mẫu đạt ─────────────────────────────────────────────────────

def test_VAN_MAU_dat_moi_luat():
    assert hk.kiem_dau_ra(_van(), _du_kien()) == []


# ── so-co-nguon ───────────────────────────────────────────────────────────

def test_SO_BIA_nghe_hop_ly_bi_bac():
    """Lỗi thật mà luật này sinh ra để bắt: một con số bịa nghe hợp lý."""
    assert "so-co-nguon" in _luat_vi_pham(_van(ke_lai="Lệnh HPG lỗ 4,8% rồi thoát."))


def test_SO_lam_tron_dung_duoc_nhan_lam_tron_sai_bi_bac():
    for van in ("lỗ 5,2%", "lỗ 5%", "lỗ 5,213%", "kém rổ 4,11 điểm"):
        assert _luat_vi_pham(_van(ke_lai=f"Lệnh HPG {van}.")) == set(), van
    assert "so-co-nguon" in _luat_vi_pham(_van(ke_lai="Lệnh HPG lỗ 5,22%."))


def test_NGAY_khop_theo_gia_tri_khong_theo_dinh_dang():
    for van in ("thoát ngày 2026-10-09", "thoát ngày 09/10/2026", "thoát ngày 9/10/2026"):
        assert _luat_vi_pham(_van(ke_lai=f"Lệnh HPG {van}.")) == set(), van
    assert "so-co-nguon" in _luat_vi_pham(_van(ke_lai="Lệnh HPG thoát ngày 10/10/2026."))


def test_SO_LIEN_CHU_khong_doc_la_so():
    assert _luat_vi_pham(_van(
        ke_lai="Lệnh HPG thoát vì STOP_LOSS, giá dưới MA20.")) == set()


def test_DOC_SO_kieu_viet_nghin_va_thap_phan():
    assert hk._doc_so("1.234,5") == (1234.5, 1)
    assert hk._doc_so("23.450") == (23450.0, 0)
    assert hk._doc_so("3.46") == (3.46, 2)
    assert hk._doc_so("−5,21") == (5.21, 2)
    assert hk._doc_so("+7") == (7.0, 0)


def test_SO_TRONG_CHUOI_du_kien_la_nguon_hop_le():
    assert _luat_vi_pham(_van(ke_lai="Lệnh HPG vào khi RSI 71,3.")) == set()


def test_SO_PHAY_NGHIN_KIEU_ANH_trong_du_kien_doc_ca_hai_cach():
    """Sổ thật ghi lý do vào kiểu Anh: "Vào lệnh=53,500 VNĐ | SL=50,022 VNĐ" (đo trên
    `--thu` với Sheets thật, 17/10/2026). Văn viết kiểu Việt "53.500" phải khớp; cách đọc
    thập phân (53,5) vẫn giữ vì chuỗi nguồn có thể là thập phân thật."""
    dk = _du_kien(ly_do=json.dumps(["🎯 Vào lệnh=53,500 VNĐ | SL=50,022 VNĐ (-6.5%)"]))
    for van in ("giá vào dự kiến 53.500 đồng", "cắt lỗ dự kiến 50.022 đồng", "lệch 53,5"):
        assert _luat_vi_pham(_van(ke_lai=f"Lệnh HPG có {van}."), dk) == set(), van
    assert "so-co-nguon" in _luat_vi_pham(_van(ke_lai="Lệnh HPG có giá 53.600 đồng."), dk)


def test_SO_TRONG_VAN_doc_ca_ngay_va_so():
    ngay, so = hk.so_trong_van("ngày 09/10/2026 lỗ 5,21% và giá 26.020")
    assert ngay == {"2026-10-09"}
    assert so == [(5.21, 2), (26020.0, 0)]


# ── mot-lenh ──────────────────────────────────────────────────────────────

def test_MOT_LENH_cam_ket_luan_tru_khi_phu_dinh():
    bac = ("Lệnh này chứng minh tín hiệu tốt.", "Chắc chắn agent đúng.",
           "Rõ ràng agent sai ở lệnh HPG.",
           # "không" ở CÂU TRƯỚC không phủ định câu sau
           "Không có gap. Lệnh này chứng minh tín hiệu tốt.",
           # "không" cùng câu nhưng quá xa (> 25 ký tự) không phủ định cụm này
           "Lệnh không có gap dưới cắt lỗ và kết quả này chứng minh tín hiệu tốt.")
    dat = ("Lệnh này chưa chứng minh được gì.", "Không chắc chắn về nguyên nhân.")
    for v in bac:
        assert "mot-lenh" in _luat_vi_pham(_van(khong_chung_minh=v)), v
    for v in dat:
        assert _luat_vi_pham(_van(khong_chung_minh=v)) == set(), v


def test_TIN_HIEU_SAI_chi_khi_du_kien_co_cach_goi():
    dk = _du_kien()
    assert dk["bai_hoc"]["cach_goi"]
    van = _van(khong_chung_minh="Cách gọi tín hiệu sai chỉ là tên của phần riêng mã.")
    assert _luat_vi_pham(van, dk) == set()
    dk["bai_hoc"]["cach_goi"] = None
    assert "mot-lenh" in _luat_vi_pham(van, dk)


# ── khong-khuyen-nghi ─────────────────────────────────────────────────────

def test_KHONG_KHUYEN_NGHI_cam_loi_khuyen_mua_ban():
    for v in ("Nên mua lại HPG khi giá hồi.", "Hãy bán sớm hơn.", "Khuyến nghị giữ."):
        assert "khong-khuyen-nghi" in _luat_vi_pham(_van(kien_thuc=v)), v
    for v in ("Đây không phải khuyến nghị.", "Giá mua vào ngày 02/10/2026."):
        assert _luat_vi_pham(_van(kien_thuc=v)) == set(), v


# ── ma-co-nguon ───────────────────────────────────────────────────────────

def test_MA_LA_bi_bac_ma_cung_nganh_va_viet_tat_duoc_nhan():
    assert "HSG" in so_bai_hoc.ma_cung_nganh("HPG")
    assert "VCB" not in so_bai_hoc.ma_cung_nganh("HPG")
    assert _luat_vi_pham(_van(ke_lai="HPG kém HSG; VN-INDEX, RSI, ATR, HOSE.")) == set()
    assert "ma-co-nguon" in _luat_vi_pham(_van(ke_lai="HPG kém VCB trong cùng kỳ."))


# ── gia-thuyet-dan-nhan, do-dai ──────────────────────────────────────────

def test_GIA_THUYET_phai_mo_dau_CHUA_KIEM():
    assert "gia-thuyet-dan-nhan" in _luat_vi_pham(
        _van(theo_doi="Lệnh cắt lỗ hay bị gap dưới cắt lỗ."))


def test_DO_DAI_dung_bien_va_truong_rong_bi_bac():
    tu = "HPG " * hk.GIOI_HAN_TU["ke_lai"]
    assert _luat_vi_pham(_van(ke_lai=tu)) == set()
    assert "do-dai" in _luat_vi_pham(_van(ke_lai=tu + "HPG"))
    assert "do-dai" in _luat_vi_pham(_van(kien_thuc="  "))
    van = _van()
    del van["kien_thuc"]
    assert "do-dai" in _luat_vi_pham(van)


# ── Dữ kiện ───────────────────────────────────────────────────────────────

def test_DU_KIEN_chi_tu_nhat_ky_va_bai_hoc_khong_tu_tinh():
    dk = _du_kien()
    assert dk["lenh"]["loi_nhuan_rong_pct"] == -5.2134
    assert dk["chi_tiet"]["ly_do"] == ["RSI 71.3 trên ngưỡng"]
    assert dk["ma_cung_nganh"] == so_bai_hoc.ma_cung_nganh("HPG")
    assert dk["hang_so"]["n_phien_sau_thoat"] == so_bai_hoc.N_PHIEN_SAU_THOAT
    f = _ham("du_kien")
    goi = {n.func.attr for n in ast.walk(f)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert {"chi_tiet", "ma_cung_nganh"} <= goi
    assert not [n for n in ast.walk(f) if isinstance(n, ast.BinOp)]


def test_NOI_DUNG_GUI_la_JSON_doc_lai_duoc_va_on_dinh():
    dk = _du_kien()
    s = hk.noi_dung_gui(dk)
    assert s == hk.noi_dung_gui(json.loads(json.dumps(dk)))
    dau = s.index("{")
    assert json.loads(s[dau:s.rindex("}") + 1]) == json.loads(json.dumps(dk, default=str))


# ── Tiền ─────────────────────────────────────────────────────────────────

def test_TIEN_uoc_DU_theo_gia_CAO_NHAT_cua_bang():
    assert hk.chi_phi_uoc(1_000_000, 0) == 5.0
    assert hk.chi_phi_uoc(0, 1_000_000) == 25.0
    assert hk.gia_cao_nhat() == (5.0, 25.0)


def test_TRAN_THANG_dung_bien():
    assert hk.vuot_tran(4.80, 0.25) is True
    assert hk.vuot_tran(4.75, 0.25) is False      # đúng 5,00: chưa vượt


def test_TRAN_MOT_LOI_GOI_dem_BYTE_va_cong_MAX_TOKENS():
    vao, ra = hk.gia_cao_nhat()
    assert hk.tran_mot_loi_goi("ạ") - hk.tran_mot_loi_goi("a") == pytest.approx(2 * vao / 1e6)
    assert hk.tran_mot_loi_goi("") >= hk.MAX_TOKENS * ra / 1e6


def test_DA_TIEU_THANG_chi_cong_dung_thang():
    dong = [{"chi_phi_usd_uoc": 0.1, "viet_luc": "2026-10-26T18:20:00+07:00"},
            {"chi_phi_usd_uoc": 0.2, "viet_luc": "2026-10-31T18:20:00+07:00"},
            {"chi_phi_usd_uoc": 0.4, "viet_luc": "2026-11-02T18:20:00+07:00"}]
    assert hk.da_tieu_thang(dong, "2026-10") == pytest.approx(0.3)


# ── Chọn lệnh cần viết ────────────────────────────────────────────────────

def test_CAN_VIET_bo_lenh_co_DAT_dua_lenh_het_luot_ra_rieng():
    nk = [_dong(trade_id=1, exit_date="2026-10-09"), _dong(trade_id=2, exit_date="2026-10-05"),
          _dong(trade_id=3), _dong(trade_id=4), _dong(trade_id=5, exit_date=None),
          _dong(trade_id=6, ro_chuan_pct=None)]
    hkd = [{"trade_id": 3, "lan": 1, "trang_thai": hk.TT_BI_BAC},
           {"trade_id": 3, "lan": 2, "trang_thai": hk.TT_DAT},
           {"trade_id": 4, "lan": 1, "trang_thai": hk.TT_BI_BAC},
           {"trade_id": 4, "lan": 2, "trang_thai": hk.TT_TU_CHOI},
           {"trade_id": 1, "lan": 1, "trang_thai": hk.TT_CAT_CUT}]
    can, het = hk.can_viet(nk, hkd)
    assert [d["trade_id"] for d in can] == [2, 1]          # ngày ra tăng dần
    assert [d["trade_id"] for d in het] == [4]
    assert hk.lan_ke(hkd, 1) == 2 and hk.lan_ke(hkd, 2) == 1


# ── Tách phản hồi (giả, đúng hình dạng Opus 5.5) ─────────────────────────

def _phan_hoi(text="{}", stop="end_turn", model="claude-opus-5-5", danh_muc=None,
              iterations=None, vao=1200, ra=900):
    return NS(content=[NS(type="thinking", thinking=""), NS(type="text", text=text)],
              stop_reason=stop, model=model,
              stop_details=NS(category=danh_muc) if stop == "refusal" else None,
              usage=NS(input_tokens=vao, output_tokens=ra, cache_creation_input_tokens=None,
                       cache_read_input_tokens=None, iterations=iterations))


def test_TACH_PHAN_HOI_doc_khoi_TEXT_khong_doc_content_0():
    t = hk.tach_phan_hoi(_phan_hoi(text='{"a": 1}'))
    assert t["text"] == '{"a": 1}'
    assert (t["token_vao"], t["token_ra"]) == (1200, 900)
    assert t["danh_muc"] is None


def test_TACH_PHAN_HOI_tu_choi_mang_danh_muc_va_iterations_lay_phan_lon_hon():
    t = hk.tach_phan_hoi(_phan_hoi(stop="refusal", danh_muc="cyber"))
    assert t["danh_muc"] == "cyber"
    hai_buoc = [NS(type="message", input_tokens=1200, output_tokens=50),
                NS(type="fallback_message", input_tokens=1300, output_tokens=880)]
    t = hk.tach_phan_hoi(_phan_hoi(iterations=hai_buoc, vao=1300, ra=880))
    assert (t["token_vao"], t["token_ra"]) == (2500, 930)


# ── Kết quả một lệnh ─────────────────────────────────────────────────────

def _ket(resp, lan=1):
    d = _dong()
    return hk.ket_qua_mot_lenh(d, lan, resp, _du_kien(), "2026-10-26T18:20:00+07:00")


def test_KET_QUA_DAT_dung_luoc_do_va_mang_bam():
    k = _ket(_phan_hoi(text=json.dumps(_van(), ensure_ascii=False)))
    assert tuple(k) == hk.COT_HAU_KIEM
    assert k["trang_thai"] == hk.TT_DAT and k["ly_do_bac"] is None
    assert k["ke_lai"] == _van()["ke_lai"]
    assert k["bam_loi_dan"] == hk.bam(hk.LOI_DAN)
    assert k["bam_du_kien"] == hk.bam(_du_kien())
    assert k["chi_phi_usd_uoc"] == pytest.approx(hk.chi_phi_uoc(1200, 900))
    assert (k["model_yeu_cau"], k["model_phuc_vu"], k["effort"]) == (
        "claude-opus-5-5", "claude-opus-5-5", "medium")


def test_KET_QUA_BI_BAC_khi_JSON_hong_hoac_vi_pham_TU_CHOI_CAT_CUT():
    assert _ket(_phan_hoi(text="không phải JSON"))["trang_thai"] == hk.TT_BI_BAC
    assert _ket(_phan_hoi(text='{"ke_lai": "x"}'))["trang_thai"] == hk.TT_BI_BAC
    k = _ket(_phan_hoi(text=json.dumps(_van(ke_lai="Lệnh HPG lỗ 4,8%."), ensure_ascii=False)))
    assert k["trang_thai"] == hk.TT_BI_BAC and "so-co-nguon" in k["ly_do_bac"]
    k = _ket(_phan_hoi(stop="refusal", danh_muc="cyber", text=""))
    assert k["trang_thai"] == hk.TT_TU_CHOI and "cyber" in k["ly_do_bac"]
    assert _ket(_phan_hoi(stop="max_tokens"))["trang_thai"] == hk.TT_CAT_CUT
    thua = json.dumps({**_van(), "ghi_chu": "trường lạ"}, ensure_ascii=False)
    assert _ket(_phan_hoi(text=thua))["trang_thai"] == hk.TT_BI_BAC


# ── Bản hiện và phép đo vế "có lời" ───────────────────────────────────────

def test_BAN_MOI_NHAT_chi_lay_DAT_lan_lon_nhat():
    hkd = [{"trade_id": 7, "lan": 1, "trang_thai": hk.TT_DAT, "ke_lai": "a"},
           {"trade_id": 7, "lan": 2, "trang_thai": hk.TT_DAT, "ke_lai": "b"},
           {"trade_id": 7, "lan": 3, "trang_thai": hk.TT_BI_BAC, "ke_lai": "c"},
           {"trade_id": 8, "lan": 1, "trang_thai": hk.TT_BI_BAC, "ke_lai": "d"}]
    assert hk.ban_moi_nhat(hkd, 7)["ke_lai"] == "b"
    assert hk.ban_moi_nhat(hkd, 8) is None


class _LichThuHaiToiThuSau:
    def trong_pham_vi(self, ngay: str) -> bool:
        return ngay < "2027-01-01"

    def co_phien(self, ngay: str) -> bool:
        return dt.date.fromisoformat(ngay).weekday() < 5


def test_DO_PHU_LOI_chua_bat_thi_khong_do():
    lenh = [{"trade_id": 1, "symbol": "HPG", "entry_date": "2026-10-02",
             "exit_date": "2026-10-09"}]
    kq = hk.do_phu_hau_kiem_loi(lenh, [], "2026-10-20", bat_dau=None,
                                lich=_LichThuHaiToiThuSau())
    assert kq["trang_thai"] == hk.TT_CHUA_BAT
    assert kq["n_vi_pham"] == 0


def test_DO_PHU_LOI_da_bat_xep_dung_nhom_va_han_mot_phien():
    lenh = [{"trade_id": 1, "symbol": "A", "entry_date": "2026-10-20", "exit_date": "2026-10-23"},
            {"trade_id": 2, "symbol": "B", "entry_date": "2026-10-27", "exit_date": "2026-10-28"},
            {"trade_id": 3, "symbol": "C", "entry_date": "2026-10-27", "exit_date": "2026-10-29"},
            {"trade_id": 4, "symbol": "D", "entry_date": "2026-10-27", "exit_date": "2026-10-30"},
            {"trade_id": 5, "symbol": "E", "entry_date": "2026-10-21", "exit_date": "2026-10-26"}]
    hkd = [{"trade_id": 2, "lan": 1, "trang_thai": hk.TT_DAT},
           {"trade_id": 5, "lan": 1, "trang_thai": hk.TT_DAT}]
    kq = hk.do_phu_hau_kiem_loi(lenh, hkd, "2026-11-02", bat_dau="2026-10-26",
                                lich=_LichThuHaiToiThuSau())
    assert [m["trade_id"] for m in kq["truoc_b1"]] == [1]
    assert [m["trade_id"] for m in kq["co"]] == [5, 2]       # đóng ĐÚNG ngày bật: có tính
    assert [m["trade_id"] for m in kq["vi_pham"]] == [3]        # hạn hết 30/10
    assert [m["trade_id"] for m in kq["trong_han"]] == [4]      # hạn hết 02/11
    assert kq["trang_thai"] == so_bai_hoc.TT_VI_PHAM


# ── CHỈ ĐỂ HIỆN (B1, BƯỚC 205) ────────────────────────────────────────────

#: Nơi DUY NHẤT được đọc tab `hau_kiem`: đường đọc chung, phần chạy, chuông, app.
DUOC_DOC_TAB_HAU_KIEM = frozenset({
    "google_sheets_sync.py", "tools/hau_kiem_loi.py", "tools/chuong_bai_hoc.py", "app.py"})


def test_CHI_DE_HIEN_khong_noi_nao_khac_doc_tab_hau_kiem():
    """Đặc tả mục 2: đoạn văn không vào đường sinh lệnh, điểm, ngưỡng, điều kiện dừng,
    backtest hay tầng 3. Gác theo LỜI GỌI hàm đọc tab (AST), quét gốc + tools/ + backtest/."""
    import duyet_repo

    doc = set()
    tep = (list(GOC.glob("*.py")) + list((GOC / "tools").glob("*.py"))
           + list(duyet_repo.duyet(GOC / "backtest", "*.py")))
    for p in tep:
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call):
                ten = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                if ten in ("doc_hau_kiem", "load_hau_kiem_from_google_sheets"):
                    doc.add(p.relative_to(GOC).as_posix())
    assert doc <= DUOC_DOC_TAB_HAU_KIEM, sorted(doc - DUOC_DOC_TAB_HAU_KIEM)
    assert {"tools/hau_kiem_loi.py", "tools/chuong_bai_hoc.py"} <= doc


@pytest.mark.parametrize("ten", [
    "run_daily.py", "paper_trading.py", "paper_runner.py", "paper_metrics.py",
    "master_agent.py", "analysis_agents.py", "debate_agents.py", "data_collectors.py",
    "walkforward.py", "ke_hoach_vao_lenh.py", "cham_bong.py", "cham_xac_nhan.py"])
def test_CHI_DE_HIEN_duong_giao_dich_va_do_khong_nhap_module(ten):
    p = GOC / ten
    if not p.exists():
        return
    nhap = set()
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
    assert "hau_kiem_loi" not in nhap, ten
