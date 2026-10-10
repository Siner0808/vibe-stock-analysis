"""Gác BẢN TIN CUỐI NGÀY — `ban_tin.py`, `tools/ban_tin.py`, tab «📰 Bản tin» (BƯỚC 174, B2).

VÌ SAO FILE NÀY TỒN TẠI
───────────────────────
Bản tin chỉ ĐỌC sổ rồi kể lại, nên lỗi của nó không làm kết quả xấu đi — nó làm
người đọc TIN một câu chuyện sai. Hai chỗ dễ sai nhất:

  · đếm sai vì bảng `decisions` có 2–3 lượt quét mỗi ngày cho cùng một (mã,
    ngày tín hiệu) (`docs/STATE.md`, "Đọc đúng con số 16.183 quyết định");
  · kể một ngày không có phiên như thể nó có phiên.

Các gác ở đây:
  · SỐ TÍNH TAY — sổ giả dựng tay (13 dòng quyết định của 9 mã trong một ngày),
    đáp số viết bằng SỐ, phép tính ở chú thích. Không dựng lại công thức.
  · TÍNH CHẤT — hàm thuần (không đổi đầu vào, gọi hai lần cho cùng kết quả),
    đối tượng đóng băng, thiếu dữ liệu thì NÓI chứ không điền.
  · AST — ai được nhập, không hàm ghi, ngưỡng là TÊN `BUY_THRESHOLD`, nhóm lý
    do lấy từ TÊN `LY_DO_*` (không chuỗi gõ lại), CLI chỉ SELECT.

Mọi test offline, dữ liệu giả. Không cần vnstock.

Ngày dùng trong sổ giả (2026): thứ Tư 07/10 · thứ Năm 08/10 · thứ Sáu 09/10 là
phiên; thứ Bảy 10/10 và Quốc khánh 01/09 là ngày nghỉ; 05/01/2027 ngoài lịch.
"""
from __future__ import annotations

import ast
import dataclasses
import importlib.util
import pathlib
import sys

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
# `tools/` có file cùng tên module (`tools/ban_tin.py`): GOC phải đứng TRƯỚC.
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import ban_tin as bt  # noqa: E402
import duyet_repo  # noqa: E402
import paper_trading as pt  # noqa: E402
import sheets_store as ss  # noqa: E402
from paper_trading import Status  # noqa: E402

NGUONG = 62.0
D = "2026-10-09"
# Lý do của cổng VN-INDEX: KHÔNG có hằng số trong paper_trading (sổ ghi chuỗi
# viết thẳng trong `consider_entry`), nên bản tin in nguyên văn.
LY_DO_VNI = "VN-INDEX nằm dưới MA50 (Downtrend/Điều chỉnh - Giữ 100% tiền mặt)"


# ─────────────────────────────────────────────────────────────────────
# Dựng sổ giả
# ─────────────────────────────────────────────────────────────────────
def _qd(seq, ma, diem, acted=0, ly_do="", ngay=D):
    return {"seq": seq, "symbol": ma, "signal_date": ngay, "score": diem,
            "acted": acted, "skip_reason": ly_do}


def _tr(id, ma, tin_hieu, vao=None, ra=None, tt=Status.OPEN, ly_do=None,
        gia_vao=None, size=None, gia_ra=None):
    return {"id": id, "symbol": ma, "signal_date": tin_hieu, "entry_date": vao,
            "exit_date": ra, "status": tt, "exit_reason": ly_do,
            "entry_price": gia_vao, "size_pct": size, "exit_price": gia_ra}


def _nk(id, ma, ra=None, lnr=None, R=None, alpha=None, hk=None):
    return {"trade_id": id, "symbol": ma, "exit_date": ra,
            "loi_nhuan_rong_pct": lnr, "ket_qua_R": R, "alpha_pct": alpha,
            "hau_kiem_may": hk}


def _vni(*cap, ma50=None):
    """`cap` = (ngày, đóng cửa[, MA50])."""
    ra = []
    for c in cap:
        ra.append({"time": c[0], "close": float(c[1]),
                   "vni_ma50": float(c[2]) if len(c) > 2 else ma50})
    return pd.DataFrame(ra)


# 13 dòng quyết định ngày D của 9 mã (sau khử trùng còn 9). Cột phải: dòng seq LỚN nhất.
#   AAA  seq 1 điểm 70 MỞ     · seq 5 điểm 68 "đã có vị thế đang mở"  -> acted, điểm 68
#   BBB  seq 2 điểm 65 bỏ     · seq 6 điểm 66 bỏ (cổng VN-INDEX)      -> điểm 66
#   CCC  seq 3 điểm 80 bỏ     · seq 7 điểm 75 bỏ (trần vốn 95%)       -> điểm 75
#   III  seq 4 điểm 70 bỏ     · seq 8 điểm 50 bỏ (dưới ngưỡng)        -> điểm 50 (KHÔNG đạt)
#   BB2  seq 9 điểm 64 bỏ (cổng VN-INDEX; signal_date có hậu tố giờ)  -> điểm 64
#   DDD  seq 10 điểm 62 bỏ (ô C5)  <- ĐÚNG bằng ngưỡng 62: tính là ĐẠT
#   EEE  seq 11 điểm 61 · FFF seq 12 điểm 55 · GGG seq 13 điểm 30 (dữ liệu BLOCK)
QD = [
    _qd(1, "AAA", 70, acted=1),
    _qd(2, "BBB", 65, ly_do=LY_DO_VNI),
    _qd(3, "CCC", 80, ly_do=pt.LY_DO_TRAN_VON + ": đang cam kết 90.0% + 20.0% > 100%"),
    _qd(4, "III", 70, ly_do=pt.LY_DO_DANG_GIU),
    _qd(5, "AAA", 68, ly_do=pt.LY_DO_DANG_GIU),
    _qd(6, "BBB", 66, ly_do=LY_DO_VNI),
    _qd(7, "CCC", 75, ly_do=pt.LY_DO_TRAN_VON + ": đang cam kết 95.0% + 20.0% > 100%"),
    _qd(8, "III", 50, ly_do="điểm 50 dưới ngưỡng 62"),
    _qd(9, "BB2", 64, ly_do=LY_DO_VNI, ngay=D + " 00:00:00"),
    _qd(10, "DDD", 62, ly_do=pt.LY_DO_C5),
    _qd(11, "EEE", 61, ly_do="điểm 61 dưới ngưỡng 62"),
    _qd(12, "FFF", 55, ly_do="điểm 55 dưới ngưỡng 62"),
    _qd(13, "GGG", 30, ly_do="chất lượng dữ liệu 'BLOCK' — không dùng được"),
    # ngày khác: không được lẫn vào bản tin ngày D (seq LỚN hơn mọi dòng của D)
    _qd(20, "HHH", 90, acted=1, ngay="2026-10-08"),
]

# Sổ lệnh. Cuối ngày D=09/10 (dựng lại từ ngày trong từng lệnh):
#   id 1 AAA tín hiệu 09/10, chưa khớp ............ CHỜ KHỚP   -> cho 1
#   id 2 XXX khớp 09/10 ........................... ĐANG MỞ    -> mở (và là lệnh KHỚP ngày D)
#   id 3 YYY khớp 02/10, ĐÓNG 09/10 ............... đã xong    -> không đếm (và là lệnh ĐÓNG ngày D)
#   id 4 ZZZ HUỶ 09/10 ............................ đã xong    -> không đếm (HUỶ, không phải đóng)
#   id 5 WWW khớp 08/10, CLOSING exit_date 09/10 .. còn giữ    -> mở (và là lệnh CHỜ THOÁT)
#   id 6 VVV đóng 30/09 ........................... đã xong
#   id 8 TTT tín hiệu 12/10 (SAU D) ............... chưa tồn tại
#   id 9 SSS khớp 06/10, đóng 12/10 (SAU D) ....... còn giữ    -> mở
#   => đang mở = 3 (id 2, 5, 9) · đang chờ = 1 (id 1)
LENH = [
    _tr(1, "AAA", D, tt=Status.PENDING),
    _tr(2, "XXX", "2026-10-07", vao=D, tt=Status.OPEN, gia_vao=100000.0, size=12.5),
    _tr(3, "YYY", "2026-10-01", vao="2026-10-02", ra=D, tt=Status.CLOSED,
        ly_do="STOP_LOSS", gia_vao=50000.0, gia_ra=48000.0),
    _tr(4, "ZZZ", "2026-10-08", ra=D, tt=Status.HUY, ly_do=pt.LY_DO_TU_CHOI_LENH),
    _tr(5, "WWW", "2026-10-07", vao="2026-10-08", ra=D, tt=Status.CLOSING),
    _tr(6, "VVV", "2026-09-20", vao="2026-09-21", ra="2026-09-30", tt=Status.CLOSED,
        ly_do="TAKE_PROFIT"),
    _tr(8, "TTT", "2026-10-12", tt=Status.PENDING),
    _tr(9, "SSS", "2026-10-05", vao="2026-10-06", ra="2026-10-12", tt=Status.CLOSED,
        ly_do="MAX_HOLD"),
]
NK = [
    _nk(2, "XXX"),                                   # mới VÀO: nửa ĐÓNG chưa có
    _nk(3, "YYY", ra=D, lnr=-3.25, R=-1.1, alpha=-2.5, hk="cắt lỗ chạm 1R"),
]
# VN-INDEX: 08/10 đóng 1700,00; 09/10 đóng 1717,00; MA50 tại 09/10 = 1700,00
VNI = _vni(("2026-10-06", 1690), ("2026-10-07", 1695),
           ("2026-10-08", 1700), ("2026-10-09", 1717, 1700))


def _lap(ngay=D, qd=None, lenh=None, nk=None, vni=None, nguong=NGUONG):
    return bt.lap_ban_tin(QD if qd is None else qd, LENH if lenh is None else lenh,
                          NK if nk is None else nk, VNI if vni is None else vni,
                          ngay, nguong)


# ─────────────────────────────────────────────────────────────────────
# 1. Khử trùng lặp — số tính tay
# ─────────────────────────────────────────────────────────────────────
def test_khu_trung_13_dong_con_9_ma_va_5_ma_dat_nguong():
    """13 dòng của 9 mã. Đạt ngưỡng 62 (điểm của dòng seq LỚN nhất): AAA 68 (và đã mở),
    BBB 66, CCC 75, BB2 64, DDD 62 = 5. III cuối cùng 50 (dòng đầu 70 KHÔNG tính), EEE
    61 thiếu 1 điểm."""
    b = _lap()
    assert b.so_cham == 9
    assert b.so_dat == 5


def test_diem_lay_dong_seq_LON_nhat_khong_lay_dong_dau_hay_cao_nhat():
    top = {m.ma: m for m in _lap().top}
    assert top["CCC"].diem == 75          # không phải 80 (dòng seq 3) hay trung bình
    assert top["BBB"].diem == 66          # không phải 65
    assert top["AAA"].diem == 68          # không phải 70


def test_acted_la_CO_dong_nao_acted_khong_phai_dong_cuoi():
    """AAA: seq 1 mở lệnh, seq 5 "đã có vị thế đang mở". Mã ĐÃ MỞ; lấy dòng cuối sẽ
    nói ngược (mã đạt ngưỡng mà bỏ vì đang giữ)."""
    b = _lap()
    assert [m.ma for m in b.mo_moi] == ["AAA"]
    aaa = b.mo_moi[0]
    assert aaa.da_mo and aaa.ly_do_bo == "" and aaa.nhom == "" and aaa.so_luot == 2
    assert all(ma != "AAA" for _, ds in b.nhom_bo for ma in ds)


def test_diem_bang_ngung_la_DAT_diem_thieu_mot_la_khong():
    ma = {m.ma: m for m in _lap().top}
    assert ma["DDD"].diem == 62 and ma["DDD"].dat_nguong     # == ngưỡng
    tat_ca = _lap(qd=[_qd(1, "EEE", 61, ly_do="x")])
    assert tat_ca.so_dat == 0                                # 61 < 62


def test_nguong_la_tham_so_doi_nguong_doi_ket_qua():
    """Ngưỡng 66: BBB 66 và CCC 75 và AAA (đã mở) đạt; BB2 64, DDD 62 thì không."""
    b = _lap(nguong=66.0)
    assert b.so_dat == 3
    assert {m.ma for m in b.top if m.dat_nguong} == {"AAA", "BBB", "CCC"}
    assert b.nguong == 66.0


def test_dong_ngay_khac_va_hau_to_gio_cua_signal_date():
    b = _lap()
    assert all(m.ma != "HHH" for m in b.top)                # HHH ngày 08/10
    assert any(m.ma == "BB2" for m in b.top)                # "2026-10-09 00:00:00" vẫn là D
    assert _lap(ngay="2026-10-08").so_cham == 1             # chỉ HHH


# ─────────────────────────────────────────────────────────────────────
# 2. Nhóm lý do · top 5
# ─────────────────────────────────────────────────────────────────────
def test_nhom_ly_do_dem_dung_va_xep_theo_so_ma_giam_dan():
    """Đạt mà không mở: BB2 + BBB (cổng VN-INDEX, 2 mã) · CCC (trần vốn, lý do mang số
    nên gom theo tiền tố, hai lượt 90%/95% -> 1 mã) · DDD (ô C5). Cùng 1 mã: xếp theo
    chữ — "vốn…" (U+0076) đứng trước "ô C5" (U+00F4)."""
    assert _lap().nhom_bo == (
        (LY_DO_VNI, ("BB2", "BBB")),
        (pt.LY_DO_TRAN_VON, ("CCC",)),
        (pt.LY_DO_C5, ("DDD",)),
    )


def test_ly_do_khong_co_hang_so_in_nguyen_van():
    b = _lap(qd=[_qd(1, "ABC", 70, ly_do="thiếu stop-loss/take-profit")])
    assert b.nhom_bo == (("thiếu stop-loss/take-profit", ("ABC",)),)


def test_dat_nguong_ma_so_khong_ghi_ly_do_thi_noi_khong_ghi():
    b = _lap(qd=[_qd(1, "ABC", 70, ly_do="")])
    assert b.nhom_bo == ((bt.NHAN_KHONG_LY_DO, ("ABC",)),)


def test_top5_la_5_diem_cao_nhat_hoa_xep_theo_ma():
    """CCC 75 · AAA 68 · BBB 66 · BB2 64 · DDD 62. EEE 61 là thứ sáu, bị cắt."""
    b = _lap()
    assert [(m.ma, m.diem) for m in b.top] == [
        ("CCC", 75), ("AAA", 68), ("BBB", 66), ("BB2", 64), ("DDD", 62)]
    hoa = _lap(qd=[_qd(1, "ZZ2", 70), _qd(2, "AA2", 70), _qd(3, "MM2", 70)])
    assert [m.ma for m in hoa.top] == ["AA2", "MM2", "ZZ2"]


def test_top_noi_mo_hay_ly_do_bo():
    md = bt.ban_tin_markdown(_lap())
    assert "- AAA (điểm 68) — MỞ LỆNH" in md
    assert f"- BBB (điểm 66) — {LY_DO_VNI}" in md
    assert "- CCC (điểm 75) — " + pt.LY_DO_TRAN_VON + ": đang cam kết 95.0%" in md


def test_ma_khong_co_diem_xep_cuoi_va_khong_dat():
    b = _lap(qd=[_qd(1, "NIL", None, ly_do="x"), _qd(2, "OKA", 63)])
    assert [m.ma for m in b.top] == ["OKA", "NIL"]
    assert b.so_dat == 1


# ─────────────────────────────────────────────────────────────────────
# 3. Lệnh khớp · đóng · huỷ · chờ thoát · vị thế cuối ngày
# ─────────────────────────────────────────────────────────────────────
def test_lenh_khop_dong_huy_cho_thoat_ngay_D():
    b = _lap()
    assert [l.ma for l in b.khop] == ["XXX"]
    assert b.khop[0].gia_vao == 100000.0 and b.khop[0].ty_trong_pct == 12.5
    assert [l.ma for l in b.dong] == ["YYY"]          # id 3, CLOSED exit 09/10
    assert b.dong[0].ly_do_ra == "STOP_LOSS"
    assert b.dong[0].loi_nhuan_rong_pct == -3.25      # từ NHẬT KÝ, không tính lại
    assert [l.ma for l in b.huy] == ["ZZZ"]
    assert [l.ma for l in b.cho_thoat] == ["WWW"]


def test_lenh_CLOSING_va_HUY_khong_bi_dem_la_lenh_dong():
    """exit_date của CLOSING là ngày tín hiệu thoát, của HUY là ngày huỷ — cả hai KHÔNG
    phải lệnh đã đóng."""
    assert [l.ma for l in _lap().dong] == ["YYY"]


def test_vi_the_cuoi_ngay_D():
    """Xem chú thích LENH: đang mở = id 2, 5, 9 (id 9 đóng SAU D) = 3; chờ = id 1."""
    b = _lap()
    assert (b.dang_mo, b.dang_cho) == (3, 1)


def test_vi_the_cuoi_ngay_dung_lai_cho_ngay_qua_khu():
    """D = 07/10. Mở: id 3 (khớp 02/10, đóng 09/10 > D) và id 9 (khớp 06/10) = 2. Chờ:
    id 2 (khớp 09/10 > D), id 5 (khớp 08/10 > D) = 2. id 1, 4 (tín hiệu 08/10 và 09/10)
    chưa tồn tại; id 6 đã đóng 30/09."""
    b = _lap(ngay="2026-10-07")
    assert (b.dang_mo, b.dang_cho) == (2, 2)
    assert b.khop == () and b.dong == () and b.huy == () and b.cho_thoat == ()


def test_lenh_ngay_khac_khong_lan_vao():
    b = _lap(ngay="2026-10-08")
    assert [l.ma for l in b.khop] == ["WWW"]          # khớp 08/10


# ─────────────────────────────────────────────────────────────────────
# 4. Học được gì
# ─────────────────────────────────────────────────────────────────────
def test_hoc_duoc_gi_lay_nua_DONG_cua_nhat_ky():
    h = _lap().hoc
    assert len(h) == 1
    assert (h[0].ma, h[0].co_nua_dong, h[0].ket_qua_R, h[0].alpha_pct,
            h[0].hau_kiem_may, h[0].loi_nhuan_rong_pct, h[0].ly_do_ra) == (
        "YYY", True, -1.1, -2.5, "cắt lỗ chạm 1R", -3.25, "STOP_LOSS")
    md = bt.ban_tin_markdown(_lap())
    assert "Hậu kiểm máy: cắt lỗ chạm 1R" in md
    assert "R -1.10" in md and "alpha -2.50" in md


def test_khong_co_lenh_dong_thi_noi_dung_cau_chu_dinh():
    md = bt.ban_tin_markdown(_lap(ngay="2026-10-07"))
    assert "Hôm nay không có lệnh đóng — chưa có bài học mới." in md
    assert _lap(ngay="2026-10-07").hoc == ()


def test_lenh_dong_ma_nhat_ky_thieu_hoac_chua_dien_nua_DONG_thi_noi_ro():
    lenh = [_tr(3, "YYY", "2026-10-01", vao="2026-10-02", ra=D, tt=Status.CLOSED,
                ly_do="MAX_HOLD"),
            _tr(7, "RRR", "2026-10-01", vao="2026-10-02", ra=D, tt=Status.CLOSED,
                ly_do="TAKE_PROFIT")]
    nk = [_nk(7, "RRR")]                        # có dòng nhưng nửa ĐÓNG chưa điền
    b = _lap(lenh=lenh, nk=nk)
    por = {h.ma: h for h in b.hoc}
    assert not por["YYY"].co_nua_dong and "không có dòng nhật ký" in por["YYY"].ghi_chu
    assert not por["RRR"].co_nua_dong and "chưa điền nửa ĐÓNG" in por["RRR"].ghi_chu
    assert por["YYY"].ket_qua_R is None and por["RRR"].loi_nhuan_rong_pct is None
    assert all(l.loi_nhuan_rong_pct is None for l in b.dong)       # không tính thay
    md = bt.ban_tin_markdown(b)
    assert "chưa có (nhật ký chưa ghi)" in md
    assert "-0.00" not in md and "nan" not in md.lower()


def test_ban_tin_co_cau_tro_sang_so_bai_hoc():
    assert "Sổ bài học" in bt.ban_tin_markdown(_lap())


# ─────────────────────────────────────────────────────────────────────
# 5. Thị trường
# ─────────────────────────────────────────────────────────────────────
def test_thi_truong_ngay_co_phien():
    """1717/1700 − 1 = +1,00%; (1717 − 1700)/1700 = +1,00% so MA50; 1717 ≥ 1700 -> MỞ."""
    t = _lap().thi_truong
    assert t.phien is True
    assert t.dong_cua == 1717.0
    assert t.pct_doi == pytest.approx(1.0)
    assert t.ma50 == 1700.0
    assert t.pct_tren_ma50 == pytest.approx(1.0)
    assert t.cong == bt.CONG_MO and t.ghi_chu == ()
    md = bt.ban_tin_markdown(_lap())
    assert "VN-INDEX đóng cửa **1,717.00**, +1.00% so với phiên trước" in md
    assert "Cổng VN-INDEX của sổ: **MỞ**" in md


def test_cong_dong_khi_duoi_MA50_va_bang_MA50_thi_MO():
    duoi = _vni(("2026-10-08", 1700), ("2026-10-09", 1690, 1700))
    t = _lap(vni=duoi).thi_truong
    assert t.cong == bt.CONG_DONG
    assert t.pct_tren_ma50 == pytest.approx(-10 / 1700 * 100)
    assert t.pct_doi == pytest.approx(-10 / 1700 * 100)
    bang = _vni(("2026-10-08", 1690), ("2026-10-09", 1700, 1700))
    assert _lap(vni=bang).thi_truong.cong == bt.CONG_MO       # cổng dùng >=, như is_vni_bullish


def test_ngay_khong_phien_khong_ke_nhu_ngay_co_phien():
    """Thứ Bảy 10/10 và Quốc khánh 01/09, KỂ CẢ khi bảng có (giả) một nến cho ngày ấy."""
    for ngay in ("2026-10-10", "2026-09-01"):
        vni = _vni(("2026-09-01", 1500, 1400), ("2026-10-09", 1717, 1700),
                   ("2026-10-10", 1800, 1700))
        b = _lap(ngay=ngay, vni=vni)
        t = b.thi_truong
        assert t.phien is False
        assert (t.dong_cua, t.pct_doi, t.ma50, t.cong) == (None, None, None, None)
        assert "không phải ngày giao dịch" in t.ghi_chu[0]
        md = bt.ban_tin_markdown(b)
        assert f"{ngay} không phải ngày giao dịch" in md
        assert "đóng cửa" not in md and "Cổng VN-INDEX của sổ" not in md


def test_ngay_ngoai_lich_noi_chua_kiem_duoc_nhung_van_ke_neu_co_nen():
    vni = _vni(("2027-01-04", 1800, 1700), ("2027-01-05", 1818, 1700))
    t = _lap(ngay="2027-01-05", vni=vni).thi_truong
    assert t.phien is None
    assert "Chưa kiểm được 2027-01-05 có phiên hay không" in t.ghi_chu[0]
    assert t.dong_cua == 1818.0 and t.pct_doi == pytest.approx(1.0)


def test_vni_thieu_thi_noi_ly_do_khong_dien_so():
    # không có bảng
    for thieu in (None, pd.DataFrame(columns=["time", "close", "vni_ma50"])):
        t = _lap(vni=thieu).thi_truong if thieu is not None else bt.lap_ban_tin(
            QD, LENH, NK, None, D, NGUONG).thi_truong
        assert t.dong_cua is None and t.cong is None
        assert "không đọc được bảng giá" in t.ghi_chu[0]
    # bảng dừng ở 08/10: không được lấy nến 08/10 làm nến của 09/10
    cu = _vni(("2026-10-07", 1695, 1650), ("2026-10-08", 1700, 1650))
    t = _lap(vni=cu).thi_truong
    assert t.dong_cua is None and t.pct_doi is None and t.cong is None
    assert "chưa có nến ngày 2026-10-09 (nến gần nhất 2026-10-08)" in t.ghi_chu[0]
    # bảng chỉ có nến SAU D
    sau = _vni(("2026-10-12", 1700, 1650))
    assert "không có nến nào tới hết" in _lap(vni=sau).thi_truong.ghi_chu[0]


def test_vni_thieu_MA50_thi_chua_kiem_duoc_cong():
    nan = _vni(("2026-10-08", 1700), ("2026-10-09", 1717, float("nan")))
    t = _lap(vni=nan).thi_truong
    assert t.dong_cua == 1717.0 and t.pct_doi == pytest.approx(1.0)
    assert t.ma50 is None and t.pct_tren_ma50 is None and t.cong is None
    assert "thiếu MA50" in t.ghi_chu[0]
    khong_cot = pd.DataFrame({"time": ["2026-10-08", "2026-10-09"], "close": [1700.0, 1717.0]})
    assert _lap(vni=khong_cot).thi_truong.cong is None


def test_vni_khong_co_phien_truoc_thi_khong_tinh_phan_tram_doi():
    mot = _vni(("2026-10-09", 1717, 1700))
    t = _lap(vni=mot).thi_truong
    assert t.dong_cua == 1717.0 and t.pct_doi is None
    assert "không có phiên liền trước" in t.ghi_chu[0]


def test_vni_trung_ngay_o_cuoi_chuoi_khong_lam_phan_tram_doi_thanh_0():
    """Bẫy đã ghi ở STATE: chuỗi VN-INDEX trả cùng một ngày HAI lần ở cuối."""
    trung = _vni(("2026-10-07", 1695), ("2026-10-08", 1700),
                 ("2026-10-09", 1717, 1700), ("2026-10-09", 1717, 1700))
    t = _lap(vni=trung).thi_truong
    assert t.pct_doi == pytest.approx(1.0)


def test_vni_thoi_gian_co_hau_to_gio_van_khop_ngay():
    gio = _vni(("2026-10-08 00:00:00", 1700), ("2026-10-09 00:00:00", 1717, 1700))
    t = _lap(vni=gio).thi_truong
    assert t.dong_cua == 1717.0 and t.cong == bt.CONG_MO


def test_vni_khong_bi_sua_va_hai_lan_goi_cho_cung_ket_qua():
    vni = _vni(("2026-10-08 00:00:00", 1700), ("2026-10-09 00:00:00", 1717, 1700))
    truoc = vni.copy(deep=True)
    qd, lenh, nk = [dict(r) for r in QD], [dict(r) for r in LENH], [dict(r) for r in NK]
    a = bt.lap_ban_tin(qd, lenh, nk, vni, D, NGUONG)
    b = bt.lap_ban_tin(qd, lenh, nk, vni, D, NGUONG)
    assert a == b
    pd.testing.assert_frame_equal(vni, truoc)
    assert qd == QD and lenh == LENH and nk == NK


# ─────────────────────────────────────────────────────────────────────
# 6. Thiếu dữ liệu · lỗi
# ─────────────────────────────────────────────────────────────────────
def test_khong_co_quyet_dinh_ngay_D_noi_ro_va_van_ke_lenh():
    b = _lap(ngay="2026-10-07")
    assert not b.co_quyet_dinh and b.so_cham == 0 and b.so_dat == 0
    assert b.mo_moi == () and b.nhom_bo == () and b.top == ()
    md = bt.ban_tin_markdown(b)
    assert "Không có quyết định nào ghi cho ngày tín hiệu 2026-10-07" in md
    assert "Không có quyết định ngày này nên không có lý do để kể" in md
    assert "Đã chấm" not in md
    assert b.thi_truong.dong_cua == 1695.0       # thị trường vẫn kể


def test_so_rong_khong_no_va_khong_ve_ban_tin_nhu_that():
    b = bt.lap_ban_tin([], [], [], None, D, NGUONG)
    assert not b.co_quyet_dinh and (b.dang_mo, b.dang_cho) == (0, 0)
    md = bt.ban_tin_markdown(b)
    assert "Không có quyết định nào" in md and "không đọc được bảng giá" in md


def test_nguong_bat_buoc_va_dong_thieu_seq_thi_no():
    with pytest.raises(TypeError):
        bt.lap_ban_tin(QD, LENH, NK, VNI, D, None)
    with pytest.raises(TypeError):
        bt.lap_ban_tin(QD, LENH, NK, VNI, D)                 # không có giá trị mặc định
    # ngày không có quyết định nào để so: nếu không có chốt rõ thì None lọt qua im lặng
    with pytest.raises(TypeError, match="nguong bắt buộc"):
        bt.lap_ban_tin([], [], [], None, D, None)
    xau = [_qd(1, "AAA", 70), {**_qd(2, "AAA", 60), "seq": None}]
    with pytest.raises(ValueError, match="thiếu seq"):
        bt.lap_ban_tin(xau, LENH, NK, VNI, D, NGUONG)


def test_acted_dang_chuoi_tu_o_sheet_van_doc_dung():
    qd = [_qd(1, "AAA", 70, acted="1"), _qd(2, "BBB", 70, acted="0"),
          _qd(3, "CCC", 70, acted="")]
    assert [m.ma for m in _lap(qd=qd).mo_moi] == ["AAA"]


def test_ban_tin_dong_bang_va_cau_ranh_gioi():
    b = _lap()
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.ngay = "x"                                     # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.thi_truong.cong = "x"                          # type: ignore[misc]
    assert b.cau_ranh_gioi == "Bản tin đọc từ sổ lệnh ẢO. Không phải khuyến nghị đặt lệnh thật."
    assert bt.ban_tin_markdown(b).rstrip().endswith(f"_{b.cau_ranh_gioi}_")


def test_ngay_gan_nhat():
    assert bt.ngay_gan_nhat([]) is None
    assert bt.ngay_gan_nhat([{"signal_date": None}, {"signal_date": ""}]) is None
    assert bt.ngay_gan_nhat(QD) == D
    assert bt.ngay_gan_nhat([_qd(1, "A", 1, ngay="2026-10-08 07:00:00"),
                             _qd(2, "B", 1, ngay="2026-10-07")]) == "2026-10-08"


def test_ban_tin_markdown_ghi_nguyen_van_ly_do_va_so_tay():
    md = bt.ban_tin_markdown(_lap())
    assert "Đã chấm **9** mã; **5** mã đạt ngưỡng 62" in md
    assert "Lệnh MỞ mới: AAA (điểm 68)" in md
    assert "**2 mã** (BB2, BBB) — " + LY_DO_VNI in md
    assert "**1 mã** (CCC) — " + pt.LY_DO_TRAN_VON in md
    assert "Cuối ngày: **3** vị thế đang mở, **1** lệnh chờ khớp." in md
    assert "**XXX** (tín hiệu 2026-10-07, giá vào 100,000, cỡ 12.5%)" in md
    assert "thoát vì STOP_LOSS; lợi nhuận ròng -3.25%" in md
    assert "Lệnh chờ bị HUỶ (không khớp được): ZZZ" in md
    assert "chờ khớp thoát phiên sau: WWW" in md


# ─────────────────────────────────────────────────────────────────────
# 7. Đọc sổ từ Google Sheets (chỉ đọc) · CLI
# ─────────────────────────────────────────────────────────────────────
class _SoChiDoc(ss.InMemorySheet):
    """Sheet giả MÀ GHI LÀ NỔ: bản tin không được chạm lệnh ghi nào."""

    def write_all(self, tab, rows):
        raise AssertionError("bản tin ghi vào sổ (write_all)")

    def append_rows(self, tab, rows):
        raise AssertionError("bản tin ghi vào sổ (append_rows)")


def _sheet_day_du():
    s = _SoChiDoc()
    s.tabs[ss.TAB_DECISIONS] = [list(ss.DECISION_COLS)] + [
        [str(1), "1.7e9", "AAA", D, "70", "BUY", "1", "", "{}", "[]", "OK"],
        [str(2), "1.7e9", "BBB", D, "66", "HOLD", "0", LY_DO_VNI, "{}", "[]", "OK"],
    ]
    t = [list(ss.TRADE_COLS)]
    for l in (_tr(2, "XXX", "2026-10-07", vao=D, tt=Status.OPEN, gia_vao=100000.0, size=12.5),
              _tr(1, "AAA", D, tt=Status.PENDING)):
        t.append([ss._to_cell(c, l.get(c)) for c in ss.TRADE_COLS])
    s.tabs[ss.TAB_TRADES] = t
    n = _nk(2, "XXX")
    s.tabs[ss.TAB_NHAT_KY] = [list(ss.NHAT_KY_COLS),
                              [ss._to_cell(c, n.get(c)) for c in ss.NHAT_KY_COLS]]
    return s


def test_doc_so_ban_tin_doc_dung_kieu_va_chi_giu_cot_can():
    so = ss.doc_so_ban_tin(_sheet_day_du())
    qd = so["quyet_dinh"]
    assert [r["seq"] for r in qd] == [1, 2]
    assert qd[0]["score"] == 70 and qd[0]["acted"] == 1 and qd[1]["skip_reason"] == LY_DO_VNI
    assert set(qd[0]) == set(ss.COT_QUYET_DINH_BAN_TIN)      # không mang cột JSON nặng
    assert so["lenh"][0]["id"] == 2 and so["lenh"][0]["exit_date"] is None
    assert so["lenh"][0]["size_pct"] == 12.5
    assert so["nhat_ky"][0]["trade_id"] == 2 and so["nhat_ky"][0]["exit_date"] is None
    b = bt.lap_ban_tin(qd, so["lenh"], so["nhat_ky"], None, D, NGUONG)
    assert (b.so_cham, b.so_dat) == (2, 2) and [l.ma for l in b.khop] == ["XXX"]


def test_doc_so_ban_tin_tab_rong_la_danh_sach_rong_va_header_lech_thi_no():
    s = _SoChiDoc()
    assert ss.doc_so_ban_tin(s) == {"quyet_dinh": [], "lenh": [], "nhat_ky": []}
    s.tabs[ss.TAB_DECISIONS] = [[]]                          # gspread trả [[]] cho tab rỗng
    assert ss.doc_so_ban_tin(s)["quyet_dinh"] == []
    xau = _sheet_day_du()
    xau.tabs[ss.TAB_TRADES][0] = list(reversed(ss.TRADE_COLS))
    with pytest.raises(ss.SheetSchemaError):
        ss.doc_so_ban_tin(xau)


def _cli():
    spec = importlib.util.spec_from_file_location("ban_tin_cli", GOC / "tools" / "ban_tin.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _so_tam(tmp_path, sheet):
    """Sổ SQLite tạm dựng từ sheet giả, đúng đường `keo_ve_so_tam` đi (`pull`)."""
    j = pt.PaperTradingJournal(str(tmp_path / "tam.db"), cho_phep_so_that=True)
    ss.pull(j.db, sheet)
    return j, {"trades": 0, "decisions": 0}


def test_CLI_in_ban_tin_tu_so_tam_va_ma_thoat_0(tmp_path, capsys):
    j, bc = _so_tam(tmp_path, _sheet_day_du())
    code = _cli().main(["--ngay", D], keo=lambda: (j, bc),
                       vni=lambda: _vni(("2026-10-08", 1700), ("2026-10-09", 1717, 1700)))
    out = capsys.readouterr().out
    assert code == 0
    assert "## 📰 Bản tin cuối ngày 2026-10-09" in out
    assert "Đã chấm **2** mã; **2** mã đạt ngưỡng 62" in out
    assert "VN-INDEX đóng cửa **1,717.00**" in out
    assert "Bản tin đọc từ sổ lệnh ẢO." in out


def test_CLI_khong_co_ngay_thi_lay_ngay_gan_nhat_va_vni_hong_van_ra_ban_tin(tmp_path, capsys):
    j, bc = _so_tam(tmp_path, _sheet_day_du())

    def hong():
        raise RuntimeError("mất mạng")
    code = _cli().main([], keo=lambda: (j, bc), vni=hong)
    cap = capsys.readouterr()
    assert code == 0 and "Bản tin cuối ngày 2026-10-09" in cap.out
    assert "không đọc được bảng giá" in cap.out and "mất mạng" in cap.err


def test_CLI_ma_thoat_2_khi_khong_doc_duoc_so(tmp_path, capsys):
    cli = _cli()
    assert cli.main([], keo=lambda: None) == 2
    assert "kho ngoai chua cau hinh" in capsys.readouterr().err

    def no():
        raise OSError("hết hạn mức")
    assert cli.main(["--ngay", D], keo=no) == 2
    assert "hết hạn mức" in capsys.readouterr().err

    rong, bc = _so_tam(tmp_path, _SoChiDoc())
    assert cli.main([], keo=lambda: (rong, bc)) == 2         # sổ rỗng, không chỉ định ngày
    assert "khong co quyet dinh nao" in capsys.readouterr().err
    assert cli.main(["--ngay", D], keo=lambda: (rong, bc), vni=lambda: None) == 0


def test_CLI_ngay_sai_dinh_dang_thi_thoat_2():
    with pytest.raises(SystemExit) as e:
        _cli().main(["--ngay", "09/10/2026"], keo=lambda: None)
    assert e.value.code == 2


# ─────────────────────────────────────────────────────────────────────
# 8. AST
# ─────────────────────────────────────────────────────────────────────
TEN_GHI = {"push", "write_all", "append_rows", "pull", "record_trade", "update_trade",
           "record_decision", "commit", "executemany", "executescript",
           "open", "write_text", "write_bytes", "unlink", "to_csv", "mkdir",
           "now", "today", "now_vn", "utcnow", "read_csv", "urlopen", "request",
           "sleep"}


def _cay(duong):
    return ast.parse((GOC / duong).read_text(encoding="utf-8"))


def _nhap_va_goi(duong):
    nhap, goi = set(), set()
    for n in ast.walk(duong if isinstance(duong, ast.AST) else _cay(duong)):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                goi.add(f.id)
            elif isinstance(f, ast.Attribute):
                goi.add(f.attr)
    return nhap, goi


def _file_ma_nguon():
    bo = {"tests", ".venv", ".git", "node_modules", "__pycache__"}
    return [p for p in duyet_repo.duyet(GOC, "*.py")
            if not (set(p.relative_to(GOC).parts) & bo)]


def test_CHI_app_py_va_cong_cu_CLI_duoc_nhap_ban_tin():
    nguoi_nhap = set()
    for p in _file_ma_nguon():
        nhap, _ = _nhap_va_goi(ast.parse(p.read_text(encoding="utf-8")))
        if "ban_tin" in nhap:
            nguoi_nhap.add(p.relative_to(GOC).as_posix())
    assert nguoi_nhap == {"app.py", "tools/ban_tin.py"}, (
        f"ban_tin CHỈ ĐỂ ĐỌC, chỉ app và CLI được nhập; đang có: {sorted(nguoi_nhap)}")


@pytest.mark.parametrize("ten", [
    "run_daily.py", "paper_trading.py", "paper_runner.py", "paper_metrics.py",
    "master_agent.py", "analysis_agents.py", "debate_agents.py",
    "news_sentiment_agent.py", "fundamental_agent.py", "data_collectors.py",
    "walkforward.py", "sheets_store.py", "google_sheets_sync.py", "nhat_ky_vi_sao.py",
    "so_bai_hoc.py", "ke_hoach_vao_lenh.py"])
def test_duong_giao_dich_cham_diem_va_du_lieu_KHONG_nhap_ban_tin(ten):
    duong = GOC / ten
    if duong.exists():
        assert "ban_tin" not in _nhap_va_goi(ten)[0], ten
    assert not [p for p in duyet_repo.duyet(GOC / "backtest", "*.py")
                if "ban_tin" in _nhap_va_goi(ast.parse(p.read_text(encoding="utf-8")))[0]]


def test_module_chi_nhap_thu_trung_tinh_va_khong_goi_ham_ghi_mang_dong_ho():
    nhap, goi = _nhap_va_goi("ban_tin.py")
    assert nhap <= {"__future__", "dataclasses", "typing", "lich_giao_dich",
                    "paper_trading", "nhat_ky_vi_sao"}, nhap
    assert not (TEN_GHI & goi), sorted(TEN_GHI & goi)
    # không nhập đường tải giá / sổ bài học (cần giá) / kho ngoài
    assert not ({"market_filter", "so_bai_hoc", "sheets_store", "google_sheets_sync",
                 "data_quality", "vnstock", "requests", "pandas"} & nhap)


def test_nhom_ly_do_la_TEN_LY_DO_cua_paper_trading_khong_chuoi_go_lai():
    cay = _cay("ban_tin.py")
    gan = [n for n in cay.body if isinstance(n, ast.AnnAssign)
           and isinstance(n.target, ast.Name) and n.target.id == "NHOM_LY_DO"]
    assert len(gan) == 1 and isinstance(gan[0].value, ast.Tuple)
    ten = {(e.value.id, e.attr) for e in gan[0].value.elts
           if isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name)}
    assert len(ten) == len(gan[0].value.elts)                # mọi phần tử là `mô-đun.TÊN`
    assert ten == {("paper_trading", "LY_DO_DANG_GIU"), ("paper_trading", "LY_DO_TRAN_VON"),
                   ("paper_trading", "LY_DO_C5")}
    # và module không mang chữ nào của ba lý do ấy (trừ docstring)
    doc = {id(n.body[0].value) for n in ast.walk(cay)
           if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
           and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant)
             and isinstance(n.value, str) and id(n) not in doc]
    for v in (pt.LY_DO_DANG_GIU, pt.LY_DO_TRAN_VON, pt.LY_DO_C5):
        # 12 ký tự ĐẦU của lý do (sổ so khớp theo chuỗi đầu) hoặc cả lý do: bắt việc
        # gõ lại, không vu oan chuỗi ngắn trùng ngẫu nhiên ("ĐÓNG" nằm trong lý do C5,
        # "vị thế đang mở" là chữ của bản tin)
        trung = [s for s in chuoi if v[:12] in s or s == v]
        assert not trung, f"chuỗi gõ lại lý do của sổ: {trung}"
    # _nhom_ly_do thật sự đọc NHOM_LY_DO
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_nhom_ly_do")
    assert "NHOM_LY_DO" in {x.id for x in ast.walk(ham) if isinstance(x, ast.Name)}


def test_ly_do_cong_VN_INDEX_trong_test_van_la_chuoi_ma_paper_trading_ghi():
    """Giữ chuỗi gõ tay của TEST khớp nguồn: nếu `consider_entry` đổi chữ, test này đỏ
    trước khi nhóm lý do trong bản tin âm thầm tách làm hai."""
    assert LY_DO_VNI in (GOC / "paper_trading.py").read_text(encoding="utf-8")


def _lenh_goi(cay, ten):
    return [n for n in ast.walk(cay) if isinstance(n, ast.Call)
            and ((isinstance(n.func, ast.Attribute) and n.func.attr == ten)
                 or (isinstance(n.func, ast.Name) and n.func.id == ten))]


@pytest.mark.parametrize("duong", ["app.py", "tools/ban_tin.py"])
def test_nguoi_goi_truyen_nguong_la_TEN_BUY_THRESHOLD(duong):
    goi = _lenh_goi(_cay(duong), "lap_ban_tin")
    assert len(goi) == 1, f"{duong}: phải lập bản tin ĐÚNG MỘT chỗ"
    ten = ("quyet_dinh", "lenh", "nhat_ky", "vni_df", "ngay", "nguong")
    doi = dict(zip(ten, goi[0].args))
    doi.update({k.arg: k.value for k in goi[0].keywords})
    assert set(doi) == set(ten)
    assert isinstance(doi["nguong"], ast.Name) and doi["nguong"].id == "BUY_THRESHOLD"


def test_app_nhap_BUY_THRESHOLD_tu_paper_trading_khong_khai_lai():
    cay = _cay("app.py")
    assert any(isinstance(n, ast.ImportFrom) and n.module == "paper_trading"
               and "BUY_THRESHOLD" in {a.name for a in n.names} for n in cay.body)
    khai = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "BUY_THRESHOLD" for t in n.targets)]
    assert not khai


def test_app_doc_ban_tin_qua_ham_chi_doc_va_co_dem():
    cay = _cay("app.py")
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_doc_so_ban_tin")
    dec = [ast.unparse(d) for d in ham.decorator_list]
    assert any("st.cache_data" in d for d in dec), "đọc Sheets mỗi lượt vẽ là hết hạn mức"
    _, goi = _nhap_va_goi(ham)
    assert "load_so_ban_tin_from_google_sheets" in goi
    assert not (TEN_GHI & goi), sorted(TEN_GHI & goi)
    # app không mở paper_trades.db cho tab này: khối `with t_tin` không nhắc tới sổ ở máy
    khoi = next(n for n in cay.body if isinstance(n, ast.With)
                and any(isinstance(i.context_expr, ast.Name) and i.context_expr.id == "t_tin"
                        for i in n.items))
    _, goi_khoi = _nhap_va_goi(khoi)
    assert not ({"PaperTradingJournal", "all_trades", "sync_trades_to_google_sheets",
                 "restore_journal_from_google_sheets"} & goi_khoi)
    # kể cả chỉ NHẮC tên (Name/Attribute/chuỗi), không cần gọi: sổ ở máy đứng yên từ 20/08
    cam = {"PaperTradingJournal", "all_trades", "DB_PATH", "paper_trades"}
    for goc in (ham, khoi):
        nhac = {n.id for n in ast.walk(goc) if isinstance(n, ast.Name)} \
            | {n.attr for n in ast.walk(goc) if isinstance(n, ast.Attribute)} \
            | {n.value for n in ast.walk(goc) if isinstance(n, ast.Constant)
               and isinstance(n.value, str)}
        assert not [x for x in nhac if any(c in x for c in cam)], sorted(nhac)
    assert not (TEN_GHI & goi_khoi), sorted(TEN_GHI & goi_khoi)
    assert {"lap_ban_tin", "ban_tin_markdown", "ngay_gan_nhat"} <= goi_khoi


def test_app_co_tab_Ban_tin_va_noi_dung_tab_ten_dung():
    src = (GOC / "app.py").read_text(encoding="utf-8")
    assert '"📰 Bản tin"' in src
    cay = _cay("app.py")
    tabs = next(n for n in ast.walk(cay) if isinstance(n, ast.Assign)
                and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == "st.tabs")
    ten_bien = [e.id for e in tabs.targets[0].elts]
    nhan = [ast.unparse(e) for e in tabs.value.args[0].elts]
    assert len(ten_bien) == len(nhan)                         # mỗi tab đúng một nhãn
    assert ten_bien.index("t_tin") == [i for i, s in enumerate(nhan) if "Bản tin" in s][0]


def test_cong_cu_CLI_chi_SELECT_va_di_qua_duong_keo_an_toan():
    cay = _cay("tools/ban_tin.py")
    _, goi = _nhap_va_goi(cay)
    assert not (TEN_GHI & goi), sorted(TEN_GHI & goi)
    # mọi `.execute(...)` chỉ nhận chuỗi SELECT viết thẳng
    for n in ast.walk(cay):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "execute":
            a = n.args[0]
            assert isinstance(a, ast.Constant) and a.value.lstrip().upper().startswith("SELECT"), \
                ast.unparse(n)
    tham_chieu = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
    assert "keo_ve_so_tam" in tham_chieu, "phải đi qua đường kéo vào DB TẠM đã có"
    nhap, _ = _nhap_va_goi(cay)
    assert not ({"sheets_store", "google_sheets_sync"} & nhap)
    assert "sys.stdout" in ast.unparse(cay) and "reconfigure" in ast.unparse(cay)


def test_doc_so_ban_tin_chi_goi_read_rows():
    cay = _cay("sheets_store.py")
    for ten in ("doc_so_ban_tin", "_doc_tab"):
        ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)
        _, goi = _nhap_va_goi(ham)
        assert not (TEN_GHI & goi), (ten, sorted(TEN_GHI & goi))
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_doc_tab")
    assert "read_rows" in _nhap_va_goi(ham)[1]


def test_PHEP_THU_gac_AST_bat_dung_mau_vi_pham():
    XAU = ["import sheets_store\nsheets_store.push(db, be)\n",
           "be.write_all('trades', rows)\n",
           "open('x.db', 'w')\n",
           "x = datetime.now()\n"]
    TOT = ["be.read_rows('trades')\n",
           "# push(db, be) bị chú thích\nx = 1\n",
           "'''Không gọi write_all() ở đây.'''\nx = 1\n"]
    for m in XAU:
        assert TEN_GHI & _nhap_va_goi(ast.parse(m))[1], m
    for m in TOT:
        assert not (TEN_GHI & _nhap_va_goi(ast.parse(m))[1]), m
