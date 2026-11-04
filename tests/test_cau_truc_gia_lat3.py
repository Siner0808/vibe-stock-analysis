"""Test `cau_truc_gia` Lát 3 — hai ô và khối chi tiết trên app (BƯỚC 250, Dow Lát 3, mốc B5 mượn).
Đặc tả: `docs/thiet-ke-dow-cau-truc.md` mục 7.1–7.3, 8.3, 8.4 (đột biến 16), 11 (Lát 3).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Lát 1–2 gác phần ĐỌC (không nhìn trộm). Lát 3 là phần NÓI: ô trên app là chỗ duy nhất một người đọc
thấy kết quả, nên lỗi ở đây có hai hình dạng khác với Lát 1–2:
  * LỜI hứa dự báo (đặc tả 7.2) lọt vào một chuỗi hiển thị — gác lời đọc MỌI chuỗi bằng AST (đột biến 16);
  * kết quả của mô-đun RÒ sang đường chấm điểm / sổ lệnh — gác nhập ở `tests/test_cau_truc_gia.py` đã cấm
    file chấm điểm nhập nó; ở đây thêm gác YẾU HƠN cho chính `app.py` (biến nhận kết quả chỉ nằm trong
    khối đánh dấu `DOW-BAT-DAU` … `DOW-KET-THUC`; đặc tả 8.3 nói thẳng nó không chứng minh được "không rò").

Đáp số TÍNH TAY: chuỗi `_BOS` (cùng chuỗi của Lát 2, bước ±500 đồng): thủy triều chưa đủ ở 30 nến đầu
(1 đỉnh swing, 0 đáy); `tăng` từ nến 54, cảnh báo từ nến 69 (STATE BƯỚC 249); `lẫn` từ nến 79.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
# `tools/` vào CUỐI đường tìm (có hai `cham_xac_nhan.py`; xem chú thích ở test_cau_truc_gia.py).
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cau_truc_gia as C  # noqa: E402
import pha_wyckoff as W  # noqa: E402

NGUON = GOC / "cau_truc_gia.py"
APP = GOC / "app.py"
NGAY = pd.bdate_range("2024-01-01", periods=600).strftime("%Y-%m-%d").tolist()

_BOS = ([20000 + 500 * i for i in range(21)] + [30000 - 500 * j for j in range(1, 9)]
        + [26000 + 500 * j for j in range(1, 15)] + [33000 - 500 * j for j in range(1, 9)]
        + [29000 + 500 * j for j in range(1, 10)] + [33500 - 500 * j for j in range(1, 17)]
        + [25500 + 500 * j for j in range(1, 5)])


def _df(dong, vol=1000):
    dong = [float(x) for x in dong]
    return pd.DataFrame({"time": pd.bdate_range("2024-01-01", periods=len(dong)),
                         "high": dong, "low": dong, "close": dong, "volume": vol})


def _guong(gia):
    return [50000.0 - (g - 20000.0) for g in gia]


def _pha(pha, cau_truc, su_kien=None, nhan="x"):
    """Một `PhaWyckoff` dựng bằng hàm tạo; `tests/test_cau_truc_gia_lat2.py` đã đối chiếu các chuỗi này với `doc_pha` thật."""
    return W.PhaWyckoff(pha=pha, cau_truc=cau_truc, su_kien=su_kien, do_tin="x", nhan_ngan=nhan, nhan_day=nhan,
                        huong="trung_tinh", san=1.0, tran=2.0, so_phien_nen=10, bang_chung=(), phan_bien=(),
                        phu_dinh="x")


KHONG_KET_LUAN = W.doc_pha(None)


def _doc(dong, pha=KHONG_KET_LUAN, **kw):
    return C.doc_hien_thi(_df(dong), 1.0, "HOSE", pha, **kw)


# ── 1. cửa sổ ghim (đặc tả 7.3) ───────────────────────────────────────────────────────────
def test_cua_so_ghim_784_va_ngay_lich_khop_run_daily():
    """784 phiên là kết luận của bảng đếm ở `docs/STATE.md` BƯỚC 250 (14,1% · 88,7% · 97,2% số mã đủ hai đỉnh + hai
    đáy swing ở 124 · 285 · 784 phiên). Số ngày lịch phải hỏi nguồn bằng ĐÚNG hằng số mà đường quét dùng để nhận 784
    phiên (`run_daily.NGAY_LICH_SU`, đọc bằng AST: nhập `run_daily` kéo cả hệ chấm điểm vào test)."""
    assert C.CUA_SO_PHIEN == 784
    cay = ast.parse((GOC / "run_daily.py").read_text(encoding="utf-8"))
    gia_tri = [n.value.value for n in cay.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
               and any(isinstance(t, ast.Name) and t.id == "NGAY_LICH_SU" for t in n.targets)]
    assert gia_tri == [1095], gia_tri
    assert C.NGAY_LICH_CUA_SO == gia_tri[0]


def test_doc_hien_thi_chi_doc_dung_cua_so_cuoi():
    df = _df(_BOS)
    a = C.doc_hien_thi(df, 1.0, "HOSE", KHONG_KET_LUAN, cua_so=80)
    b = C.doc_hien_thi(pd.concat([_df([20000.0] * 40).assign(time=pd.bdate_range("2020-01-01", periods=40)), df],
                                 ignore_index=True), 1.0, "HOSE", KHONG_KET_LUAN, cua_so=80)
    assert a == b                       # 40 nến cũ hơn cửa sổ không đổi một chữ nào
    assert b.so_nen == 80 and C.doc_hien_thi(df, 1.0, "HOSE", KHONG_KET_LUAN).so_nen == 80   # mặc định 784 > 80
    ngan = C.doc_hien_thi(df, 1.0, "HOSE", KHONG_KET_LUAN, cua_so=30)
    assert ngan.so_nen == 30 and ngan != a   # cửa sổ NGẮN hơn thì đọc khác (quần thể không tầm thường)
    assert any("nguồn chỉ trả 80/784 phiên" in d for d in a.chi_tiet) is False
    assert any("nguồn chỉ trả 80/784 phiên" in d for d in C.doc_hien_thi(df, 1.0, "HOSE", KHONG_KET_LUAN).chi_tiet)


def test_pha_wyckoff_chi_doc_120_phien_cuoi_nen_ba_cua_so_cho_cung_mot_pha():
    """`app.py` truyền `wy` (đọc trên bảng biểu đồ ~131 phiên) cho `doc_hien_thi` thay vì đọc lại trên 784 phiên.
    Điều đó chỉ đúng khi `doc_pha` chỉ nhìn 120 phiên cuối; nếu `pha_wyckoff` đổi, test này đỏ."""
    truoc = [140 - 40 * i / 699 for i in range(700)]
    zone = ([100 - 20 * i / 49 for i in range(50)] + [78, 75, 72] + [73 + i for i in range(6)]
            + [76, 75, 74, 76, 77, 75, 74, 76, 77, 76] * 3)
    zone = (zone + [75] * 20)[:100]
    closes = truoc + zone
    vols = [1000] * 700 + [1000] * 50 + [4000] * 3 + [1500] * 6 + [800] * 41
    n = len(closes)
    df = pd.DataFrame({"time": pd.date_range("2022-01-03", periods=n, freq="B").strftime("%Y-%m-%d"),
                       "open": closes, "close": closes, "high": [c * 1.005 for c in closes],
                       "low": [c * 0.995 for c in closes], "volume": vols})
    dai = W.doc_pha(df, 1000.0)
    assert dai.ket_luan_duoc, "quần thể: ca này phải là một pha CÓ kết luận, nếu không so sánh là tầm thường"
    for w in (131, 124, 300):
        assert W.doc_pha(df.tail(w), 1000.0) == dai, w


# ── 2. nội dung hai ô: đáp số tính tay ────────────────────────────────────────────────────
def test_o_thuy_trieu_chua_du_bang_chung_neu_so_dinh_day_thay_vi_ha_nguong():
    h = _doc(_BOS[:30])
    o = h.o_thuy_trieu
    assert (o.nhan, o.sac_thai, o.phu) == ("Chưa đủ bằng chứng", C.SAC_TRUNG_TINH, ("cấp swing: 1 đỉnh, 0 đáy",))
    assert (h.so_dinh_swing, h.so_day_swing) == (1, 0)
    assert h.o_chu_ky.nhan == "Chưa đủ bằng chứng" and h.o_chu_ky.sac_thai == C.SAC_TRUNG_TINH


def test_o_thuy_trieu_tang_kem_biet_tu_va_canh_bao_tu_nen_69():
    # 60 nến: tăng, biết từ nến 54, chưa cảnh báo. 70 nến: cùng thủy triều, thêm cảnh báo (CHoCH swing nến 69).
    a, b = _doc(_BOS[:60]), _doc(_BOS[:70])
    assert (a.o_thuy_trieu.nhan, a.o_thuy_trieu.sac_thai) == ("Tăng", C.SAC_TANG)
    assert a.o_thuy_trieu.phu == (f"biết từ {NGAY[54]}",)
    assert b.o_thuy_trieu.phu == (f"biết từ {NGAY[54]}", "cảnh báo cấu trúc: CHoCH swing ngược thủy triều")
    assert any("Cảnh báo cấu trúc: thiên hướng swing là xuống, ngược thủy triều tăng" in d for d in b.chi_tiet)
    assert not any("Cảnh báo cấu trúc: thiên hướng" in d for d in a.chi_tiet)


def test_o_thuy_trieu_lan_mau_trung_tinh_biet_tu_nen_79():
    h = _doc(_BOS)
    assert (h.o_thuy_trieu.nhan, h.o_thuy_trieu.sac_thai, h.o_thuy_trieu.phu) == ("Lẫn", C.SAC_TRUNG_TINH,
                                                                                (f"biết từ {NGAY[79]}",))


def test_o_thuy_trieu_giam_la_anh_guong_cua_tang():
    a, b = _doc(_BOS[:60]), _doc(_guong(_BOS[:60]))
    assert (b.o_thuy_trieu.nhan, b.o_thuy_trieu.sac_thai, b.o_thuy_trieu.phu) == ("Giảm", C.SAC_GIAM, a.o_thuy_trieu.phu)


def test_cac_o_khop_trang_thai_dow_tung_nhan():
    """Ô là hàm của `trang_thai_dow`, không tính lại: nhãn, ngày biết, số đỉnh/đáy khớp trên mọi tiền tố 25..80."""
    for n in range(25, 81):
        h = _doc(_BOS[:n])
        tt = C.trang_thai_dow(C.doc_cau_truc(_df(_BOS[:n])))
        assert h.trang_thai == tt
        ten = C.TEN_THUY_TRIEU[tt.thuy_trieu]
        assert h.o_thuy_trieu.nhan == ten[:1].upper() + ten[1:]
        if tt.thuy_trieu != C.CHUA_DU:
            assert h.o_thuy_trieu.phu[0] == f"biết từ {tt.ngay_biet_thuy_trieu}"


def test_o_chu_ky_nguon_thuy_trieu_khi_wyckoff_khong_ket_luan():
    markup, markdown = _doc(_BOS[:60]), _doc(_guong(_BOS[:60]))
    assert (markup.o_chu_ky.nhan, markup.o_chu_ky.sac_thai) == ("Markup", C.SAC_TANG)
    assert markup.o_chu_ky.phu == ("nguồn: thủy triều swing", f"biết từ {NGAY[54]}")
    assert (markdown.o_chu_ky.nhan, markdown.o_chu_ky.sac_thai) == ("Markdown", C.SAC_GIAM)
    assert any(C.GHI_CHU_KHONG_CO_VUNG in d for d in markup.chi_tiet)


def test_o_chu_ky_nguon_wyckoff_ghi_dung_ngay_du_lieu():
    h = _doc(_BOS[:60], pha=_pha("C", "TÍCH LUỸ", nhan="Pha C — Spring"))
    assert h.o_chu_ky.nhan == "Tích luỹ" and h.o_chu_ky.sac_thai == C.SAC_TRUNG_TINH
    assert h.o_chu_ky.phu == ("nguồn: pha Wyckoff", f"dữ liệu tới {NGAY[59]}")
    assert h.ngay_cuoi == NGAY[59]


def test_o_chu_ky_mau_thuan_hien_ca_hai_khong_ghi_de():
    """Pha E `Markup` mà thủy triều `giảm`: nhãn vẫn Markup (nguồn Wyckoff), thủy triều vẫn Giảm, cờ mâu thuẫn hiện ở
    ô VÀ ở khối chi tiết (đặc tả 6 khoản 4)."""
    h = _doc(_guong(_BOS[:60]), pha=_pha("E", "TÍCH LUỸ", su_kien="Markup", nhan="Pha E — Markup"))
    assert h.o_thuy_trieu.nhan == "Giảm"
    assert h.o_chu_ky.nhan == "Markup" and h.o_chu_ky.sac_thai == C.SAC_TRUNG_TINH
    assert "mâu thuẫn với thủy triều: xem chi tiết" in h.o_chu_ky.phu
    assert h.chu_ky.mau_thuan is True
    assert any("thủy triều swing chưa xác nhận" in d for d in h.chi_tiet)
    cung_chieu = _doc(_BOS[:60], pha=_pha("E", "TÍCH LUỸ", su_kien="Markup", nhan="Pha E — Markup"))
    assert cung_chieu.o_chu_ky.sac_thai == C.SAC_TANG and "mâu thuẫn với thủy triều: xem chi tiết" not in cung_chieu.o_chu_ky.phu


def test_nen_cuoi_dang_do_chi_ghi_nhan_khong_doi_nhan():
    a, b = _doc(_BOS[:60]), _doc(_BOS[:60], nen_cuoi_dang_do=True)
    assert b.o_thuy_trieu.phu == a.o_thuy_trieu.phu + (C.PHU_NEN_DANG_DO,)
    assert b.o_chu_ky.phu == a.o_chu_ky.phu + (C.PHU_NEN_DANG_DO,)
    assert (b.o_thuy_trieu.nhan, b.o_chu_ky.nhan, b.trang_thai) == (a.o_thuy_trieu.nhan, a.o_chu_ky.nhan, a.trang_thai)
    assert any("chưa đóng cửa" in d for d in b.chi_tiet) and not any("chưa đóng cửa" in d for d in a.chi_tiet)


# ── 3. khối chi tiết (đặc tả 7.1) ─────────────────────────────────────────────────────────
def test_khoi_chi_tiet_co_pivot_hai_cap_moc_phu_dinh_su_kien_con_song_va_chan_khoi():
    h = _doc(_BOS[:60])
    nd = "\n".join(h.chi_tiet)
    for muc in ("Đỉnh swing gần nhất", "Đáy swing gần nhất", "Đỉnh nội bộ gần nhất", "Đáy nội bộ gần nhất",
                "Mốc phủ định (đáy swing", "Cảnh báo cấu trúc gần nhất, cấp swing", "Cảnh báo cấu trúc gần nhất, cấp nội bộ",
                "Nhịp ngược (con sóng) hoàn tất gần nhất", "Chu kỳ 4 giai đoạn:", "xấp xỉ"):
        assert muc in nd, muc
    # đỉnh swing gần nhất đã biết tại nến 59: 33.000 (xảy ra 42, biết 46) — mỗi pivot kèm CẢ HAI ngày
    assert f"Đỉnh swing gần nhất: 33,000 (HH), xảy ra {NGAY[42]}, biết từ {NGAY[46]}." in h.chi_tiet
    assert f"Đáy swing gần nhất: 29,000 (HL), xảy ra {NGAY[50]}, biết từ {NGAY[54]}." in h.chi_tiet
    assert (f"Mốc phủ định (đáy swing; đóng cửa vượt qua nó quá nửa bước giá là CHoCH swing, một cảnh báo cấu trúc): "
            f"29,000 (HL), xảy ra {NGAY[50]}, biết từ {NGAY[54]}.") in h.chi_tiet
    assert h.chi_tiet[-1] == C.CHAN_KHOI == h.chan


def test_chan_khoi_mang_so_DO_ket_cuc_va_dung_chu_cua_van_ban_DO_34_da_sua():
    """Chân khối (BƯỚC 253): số ĐO + kết cục A + câu "không phân biệt được lợi thế ≥ MDE₈₀ với 0" của S2; KHÔNG được nói
    "Dow không có lợi thế" / "bằng rổ". Số MDE và nhãn đọc từ bản ghi thô của lượt chạy duy nhất, không gõ lại bằng tay."""
    import json
    from pathlib import Path
    ban_ghi = json.loads((Path(__file__).resolve().parent.parent / "docs" / "do34-lat4b-ket-qua.json").read_text(encoding="utf-8"))
    nhan = ban_ghi["ket_cuc_cuoi"]["ket_cuc"]
    mde = ban_ghi["doi_chung"]["iii"]["mde_80"]["diem_pt_dang_dau_tu_moi_nam"]
    assert nhan == "A"
    chan = C.CHAN_KHOI
    assert chan.startswith("Đọc cấu trúc giá, không dự báo.")
    assert "ĐO 34" in chan and f"kết cục {nhan}:" in chan
    assert "không phân biệt được lợi thế ≥ MDE₈₀ với 0" in chan
    assert f"{mde:.1f}".replace(".", ",") + " điểm phần trăm mỗi năm trên vốn đang đầu tư" in chan
    assert "không phải bằng chứng cấu trúc này không có lợi thế" in chan
    assert "Dow không có lợi thế" not in chan and "bằng rổ" not in chan and "Chưa có phép đo" not in chan
    assert "docs/STATE.md BƯỚC 253" in chan


def test_gia_hien_thi_theo_he_so_gia_va_co_khoa_bien_hien_ra():
    # bảng theo nghìn đồng (he_so_gia=1000): 20,0 → 20.000đ
    df = _df([x / 1000 for x in _BOS[:60]])
    h = C.doc_hien_thi(df, 1000.0, "HOSE", KHONG_KET_LUAN)
    assert f"Đỉnh swing gần nhất: 33,000 (HH), xảy ra {NGAY[42]}, biết từ {NGAY[46]}." in h.chi_tiet
    assert C._co_nen("KICH_SAN", False) == " (nến kịch sàn)"
    assert C._co_nen("KICH_TRAN", True) == " (nến kịch trần, phiên không giao dịch)"
    assert C._co_nen(None, False) == ""


def test_khong_doc_duoc_noi_ra_khong_doan_nhan():
    h = C.khong_doc_duoc("lý do thử")
    assert not h.doc_duoc and h.o_thuy_trieu.nhan == C.KHONG_DOC_DUOC == h.o_chu_ky.nhan
    assert h.chi_tiet[-1] == C.CHAN_KHOI and "lý do thử" in h.chi_tiet[0]
    with pytest.raises(ValueError):
        C.doc_hien_thi(_df(_BOS), 1.0, "SGX", KHONG_KET_LUAN)        # sàn lạ: nổ, không đoán


def test_bang_rong_khong_no_va_noi_chua_du():
    h = C.doc_hien_thi(_df(_BOS).iloc[0:0], 1.0, "HOSE", KHONG_KET_LUAN)
    assert h.so_nen == 0 and h.ngay_cuoi is None and h.o_thuy_trieu.nhan == "Chưa đủ bằng chứng"


# ── 4. GÁC LỜI (đặc tả 7.2, 8.3; đột biến 16) ─────────────────────────────────────────────
CAM_LOI = ("sẽ", "dự báo", "tín hiệu mua", "tín hiệu bán", "khuyến nghị", "đáng mua", "đảo chiều chắc chắn",
           "xác nhận xu hướng chính")


def _vi_pham(chuoi) -> list:
    """Các (từ cấm, chuỗi) có mặt. "dự báo" chỉ được phép đứng sau chữ "không" (chân khối cố định 7.2 khoản 3
    nói thẳng *"không dự báo"*); mọi từ cấm khác không có ngoại lệ."""
    ra = []
    for s in chuoi:
        for tu in CAM_LOI:
            mau = rf"(?<!\w){re.escape(tu)}(?!\w)"
            if tu == "dự báo":
                mau = rf"(?<!không )" + mau
            if re.search(mau, s, flags=re.I):
                ra.append((tu, s))
    return ra


def _la_docstring(nut, cha_cua) -> bool:
    """Hằng chuỗi là câu lệnh ĐẦU của Module / hàm / lớp (docstring): cha của nó là `Expr`, ông của nó là vật chứa."""
    expr = cha_cua.get(id(nut))
    chua = cha_cua.get(id(expr)) if isinstance(expr, ast.Expr) else None
    return (isinstance(chua, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))
            and bool(chua.body) and chua.body[0] is expr)


def _chuoi_trong_cay(cay, khoang=None) -> list:
    """Mọi hằng chuỗi (kể cả mảnh của f-string) KHÔNG phải docstring; `khoang` = các (dòng đầu, dòng cuối) được xét."""
    cha_cua = {id(c): p for p in ast.walk(cay) for c in ast.iter_child_nodes(p)}
    ra = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if _la_docstring(n, cha_cua):
                continue
            if khoang is not None and not any(a <= n.lineno <= b for a, b in khoang):
                continue
            ra.append(n.value)
    return ra


def _khoang_dow(src: str) -> list:
    """Các khối `# DOW-BAT-DAU` … `# DOW-KET-THUC` của app.py (số dòng 1-based, gồm cả hai dòng đánh dấu)."""
    mo, ket = [], []
    for i, d in enumerate(src.splitlines(), 1):
        t = d.strip()
        if t == "# DOW-BAT-DAU":
            mo.append(i)
        elif t == "# DOW-KET-THUC":
            ket.append(i)
    assert len(mo) == len(ket) >= 2, (mo, ket)
    assert all(a < b for a, b in zip(mo, ket)) and all(b < a for b, a in zip(ket, mo[1:]))
    return list(zip(mo, ket))


def test_cong_cu_gac_loi_bat_dung_va_khong_bat_nham():
    xau = ["Mã này sẽ tăng", "Dự báo xu hướng", "tín hiệu mua rõ", "Tín hiệu bán", "khuyến nghị giữ", "đáng mua",
           "đảo chiều chắc chắn", "xác nhận xu hướng chính", "Cấu trúc này dự báo giá"]
    lanh = ["Đọc cấu trúc giá, không dự báo.", "sẽ" + "m", "phiên", "dữ liệu tới 2026-11-02", "Chưa đủ bằng chứng"]
    assert [v[1] for v in _vi_pham(xau)] == xau
    assert _vi_pham(lanh) == []


def test_loi_mo_dun_khong_hua_du_bao__dot_bien_16():
    chuoi = _chuoi_trong_cay(ast.parse(NGUON.read_text(encoding="utf-8")))
    assert len(chuoi) > 100, "quần thể phải khác rỗng (lỗi 66)"
    assert any("không dự báo" in s for s in chuoi), "chân khối phải có mặt — nếu không gác không thấy ngoại lệ nào"
    assert _vi_pham(chuoi) == []


def test_loi_app_trong_khoi_dow_khong_hua_du_bao__dot_bien_16():
    src = APP.read_text(encoding="utf-8")
    chuoi = _chuoi_trong_cay(ast.parse(src), _khoang_dow(src))
    assert len(chuoi) > 10, "quần thể phải khác rỗng"
    assert _vi_pham(chuoi) == []
    assert _ro_dinh_danh(chuoi) == []


def test_loi_cac_chuoi_sinh_ra_o_moi_nhanh_khong_hua_du_bao():
    """Cả những chuỗi mà gác AST không thấy vì chúng được ghép lúc chạy (ngày, giá, tên nhãn)."""
    chuoi = []
    for n in (30, 60, 70, 80):
        for g in (_BOS[:n], _guong(_BOS[:n])):
            for pha in (KHONG_KET_LUAN, _pha("C", "TÍCH LUỸ"), _pha("C", "PHÂN PHỐI"), _pha("B", "CHƯA PHÂN ĐỊNH"),
                        _pha("E", "TÍCH LUỸ", "Markup"), _pha("E", "PHÂN PHỐI", "Markdown")):
                for dang_do in (False, True):
                    h = _doc(g, pha=pha, nen_cuoi_dang_do=dang_do)
                    for o in (h.o_thuy_trieu, h.o_chu_ky):
                        chuoi += [o.nhan, o.goi_y, *o.phu]
                    chuoi += list(h.chi_tiet)
    assert len(chuoi) > 1000
    assert _vi_pham(chuoi) == []
    assert _ro_dinh_danh(chuoi) == []


#: Định danh nội bộ (snake_case: `pha_wyckoff`, `thuy_trieu`, `noi_bo`, …) không được hiện ra cho người đọc. Cố ý chỉ
#: bắt dạng có gạch dưới: tên file trong chân khối (`docs/thiet-ke-dow-cau-truc.md`) dùng gạch ngang.
def _ro_dinh_danh(chuoi) -> list:
    return [s for s in chuoi if re.search(r"(?<![\w-])[a-z][a-z0-9]*_[a-z0-9_]+(?![\w-])", s)]


def test_cong_cu_gac_dinh_danh_bat_dung_va_khong_bat_nham():
    xau = ["nguồn pha_wyckoff; x", "nguồn thuy_trieu", "cấp noi_bo", "chu_ky"]
    assert _ro_dinh_danh(xau) == xau
    assert _ro_dinh_danh(["nguồn pha Wyckoff", "xem docs/thiet-ke-dow-cau-truc.md.", "thủy triều swing", "KICH_SAN"]) == []


def test_dong_chu_ky_va_o_dung_ten_nguoi_doc_cua_nguon_khong_lo_dinh_danh():
    kq = []
    for g, pha in ((_BOS[:60], KHONG_KET_LUAN), (_guong(_BOS[:60]), KHONG_KET_LUAN),
                   (_BOS[:60], _pha("C", "TÍCH LUỸ")), (_guong(_BOS[:60]), _pha("E", "TÍCH LUỸ", "Markup"))):
        h = _doc(g, pha=pha)
        kq.append((h.o_chu_ky.phu[0], next(d for d in h.chi_tiet if d.startswith("Chu kỳ 4 giai đoạn:"))))
    assert kq[0][0] == "nguồn: thủy triều swing" and "; nguồn thủy triều swing;" in kq[0][1]
    assert kq[2][0] == "nguồn: pha Wyckoff" and "; nguồn pha Wyckoff;" in kq[2][1]
    assert set(C.TEN_NGUON) == {C.NGUON_WYCKOFF, C.NGUON_THUY_TRIEU}
    mau_thuan = _doc(_guong(_BOS[:60]), pha=_pha("E", "TÍCH LUỸ", "Markup")).chi_tiet
    assert any("trong khi pha Wyckoff đọc Markup" in d for d in mau_thuan)


# ── 5. gác nhập cho app.py (đặc tả 8.3; yếu hơn các gác nhập khác và nói thẳng điều đó) ────
def _cha(cay) -> dict:
    return {id(c): p for p in ast.walk(cay) for c in ast.iter_child_nodes(p)}


def _ten_dow_trong_khoi(cay, khoang) -> set:
    """Tên GÁN hoặc ĐỊNH NGHĨA trong khối (biến của vòng lặp con như `d` trong `for d in …` không tính: chúng là
    biến cục bộ của biểu thức sinh, không giữ kết quả của mô-đun)."""
    cha = _cha(cay)
    ra = {"_ctg"}
    for n in ast.walk(cay):
        if not (hasattr(n, "lineno") and any(a <= n.lineno <= b for a, b in khoang)):
            continue
        p, trong_bieu_thuc_sinh = cha.get(id(n)), False
        while p is not None:
            trong_bieu_thuc_sinh |= isinstance(p, (ast.comprehension, ast.GeneratorExp, ast.ListComp, ast.Lambda,
                                                   ast.FunctionDef))
            p = cha.get(id(p))
        if trong_bieu_thuc_sinh:
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            ra.add(n.id)
        elif isinstance(n, ast.FunctionDef):
            ra.add(n.name)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            ra.add(n.name)
    return ra


def test_bien_ket_qua_chi_nam_trong_khoi_dow_va_hai_o_html_chi_trong_f_string():
    src = APP.read_text(encoding="utf-8")
    cay = ast.parse(src)
    khoang = _khoang_dow(src)
    ten = _ten_dow_trong_khoi(cay, khoang)
    assert {"_ctg", "cau_truc", "_ct_df", "o_thuy_trieu_html", "o_chu_ky_html", "_o_cau_truc_html"} <= ten, ten
    cha = _cha(cay)
    so_ngoai = 0
    for n in ast.walk(cay):
        if isinstance(n, ast.Name) and n.id in ten and not any(a <= n.lineno <= b for a, b in khoang):
            so_ngoai += 1
            if n.id in ("o_thuy_trieu_html", "o_chu_ky_html"):
                p = cha[id(n)]
                while p is not None and not isinstance(p, ast.JoinedStr):
                    p = cha.get(id(p))
                assert p is not None, f"{n.id} ngoài khối DOW phải chỉ nằm trong f-string của lưới ô (dòng {n.lineno})"
            else:
                pytest.fail(f"`{n.id}` (kết quả của cau_truc_gia) xuất hiện NGOÀI khối DOW, dòng {n.lineno}")
    assert so_ngoai == 2, "đúng hai chỗ ngoài khối: hai ô trong lưới tín hiệu nhanh"


def test_app_goi_ten_that_cua_mo_dun_va_truyen_dung_wy_cho_chu_ky():
    cay = ast.parse(APP.read_text(encoding="utf-8"))
    thuoc = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
             and n.value.id == "_ctg"}
    assert {"doc_hien_thi", "khong_doc_duoc", "NGAY_LICH_CUA_SO", "TEN_O_THUY_TRIEU", "TEN_O_CHU_KY"} <= thuoc
    for t in thuoc:
        assert hasattr(C, t), f"app.py gọi `_ctg.{t}` mà mô-đun không có"
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and n.func.attr == "doc_hien_thi"]
    assert len(goi) == 1
    assert [type(a).__name__ for a in goi[0].args[:4]] == ["Name", "Call", "Name", "Name"]
    assert goi[0].args[3].id == "wy", "chu kỳ phải ghép với CHÍNH lần đọc `doc_pha` của ô Pha Wyckoff"
    gan_wy = [n for n in ast.walk(cay) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "wy"
              for t in n.targets)]
    assert len(gan_wy) == 1 and gan_wy[0].value.func.id == "doc_pha"


def test_app_hoi_nguon_dung_so_ngay_cua_mo_dun_cho_cua_so_ghim():
    src = APP.read_text(encoding="utf-8")
    assert "timedelta(days=_ctg.NGAY_LICH_CUA_SO)" in src


def test_hai_o_nam_sat_sau_pha_wyckoff_theo_thu_tu_dac_ta_7_1():
    src = APP.read_text(encoding="utf-8")
    mau = (r'<span class="sig-lbl">Pha Wyckoff</span>\s*<span class="sig-val \{phase_cls\}">\{dyn_phase_short\}</span>\s*'
           r'</div>\s*\{o_thuy_trieu_html\}\s*\{o_chu_ky_html\}\s*<div class="sig-item">\s*<span class="sig-lbl">RSI')
    assert len(re.findall(mau, src)) == 1


def test_html_o_la_mot_dong_va_thoat_ky_tu():
    """Khối Markdown thụt lề bốn khoảng trắng: một ô nhiều dòng sẽ thành khối mã. Ô phải một dòng và thoát ký tự."""
    src = APP.read_text(encoding="utf-8")
    cay = ast.parse(src)
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "_o_cau_truc_html")
    mot = "\n".join(src.splitlines()[ham.lineno - 1:ham.end_lineno])
    assert "_html.escape" in mot and mot.count("_html.escape") >= 4
    ns = {"_html": __import__("html")}
    exec(compile(ast.Module([ham], []), "app_ham", "exec"), ns)    # chạy đúng hàm của app, không sao chép
    o = C.OHienThi(nhan="A<b>", sac_thai="tang", phu=("x & y", 'z"'), goi_y='g"<')
    s = ns["_o_cau_truc_html"]("Nhãn", o)
    assert "\n" not in s and "<b>" not in s and "&amp;" in s and 'title="g&quot;&lt;"' in s
    assert 'class="sig-val pos"' in s
    assert 'class="sig-val neu"' in ns["_o_cau_truc_html"]("N", C.OHienThi("a", C.SAC_TRUNG_TINH, (), ""))
    assert 'class="sig-val neg"' in ns["_o_cau_truc_html"]("N", C.OHienThi("a", C.SAC_GIAM, (), ""))


# ── 6. dụng cụ `cua-so` (máy đo bị nghi như gác) ──────────────────────────────────────────
def test_dung_cu_cua_so_dem_dung_tren_ca_dung_tay(tmp_path):
    """Ba mã: ACB = `_BOS` (80 nến: 3 đỉnh + 3 đáy swing, thủy triều lẫn), HPG = 30 nến đầu (1 đỉnh + 0 đáy, chưa
    đủ), VNM = 47 nến đầu (2 đỉnh + 1 đáy: đủ đỉnh mà thiếu đáy, nên `và` khác `hoặc`; đáy duy nhất chưa có nhãn nên
    thủy triều chưa đủ). Đáp số đếm tay: đỉnh swing biết ở nến 24 và 46, đáy biết ở nến 32 (STATE BƯỚC 249)."""
    import mo_ta_cau_truc_gia as M
    for ma, dong in (("ACB", _BOS), ("HPG", _BOS[:30]), ("VNM", _BOS[:47])):
        d = _df(dong)
        d["time"] = d["time"].dt.strftime("%Y-%m-%d")
        d.to_csv(tmp_path / f"{ma}.csv", index=False)
    kq = M.mo_ta_cua_so(tmp_path, ["ACB", "HPG", "VNM"], cac_cua_so=(80, 30))
    k80 = kq["cua_so"][80]
    assert k80["ma_du_hai_dinh_hai_day"] == 1 and k80["ty_le_du"] == round(1 / 3, 4)
    # số đỉnh swing mỗi mã {3, 1, 2}: np.percentile tuyến tính cho p10 = 1,2 và p90 = 2,8
    assert k80["dinh_swing"] == {"min": 1, "p10": pytest.approx(1.2), "trung_vi": 2.0, "p90": pytest.approx(2.8),
                                 "max": 3}
    assert k80["day_swing"]["max"] == 3 and k80["day_swing"]["min"] == 0
    assert k80["thuy_trieu_nen_cuoi"] == {"chua_du_bang_chung": 2, "lan": 1} and k80["ty_le_chua_du"] == round(2 / 3, 4)
    assert kq["do_nhay"]["30_so_voi_80"]["tren"] == 3
    assert kq["do_nhay"]["30_so_voi_80"]["khac_thuy_trieu"] >= 1      # ACB: cửa sổ 30 nến đọc khác cửa sổ 80
