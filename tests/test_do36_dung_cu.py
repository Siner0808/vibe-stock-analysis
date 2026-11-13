"""BƯỚC 273 — gác của phần DỤNG CỤ mà ĐO 36 sửa (`tools/do35_chinh_thang_gia.py`): luật quần thể S2 (E1 · E2 · E3),
phán S1 của #122, K0 của (ii′), so blob mã đo, và việc `chay` KHÔNG in số nào của C1–C11 khi một đối chứng trượt.

Máy đo cũng phải bị nghi ngờ như gác (lỗi 61): mọi thứ ở đây chạy trên sổ và khung giá DỰNG TAY, không đọc sổ hay
nến thật. Mỗi phép thử biên đặt cả hai phía của biên (ngày vào/ngày ra/ngày cuối khung; 4/5 lệnh).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import pickle
import subprocess
import sys

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do35_chinh_thang_gia as d35  # noqa: E402
from nhat_ky_vi_sao import COT_NHAT_KY  # noqa: E402
from paper_trading import PaperTradingJournal  # noqa: E402

CK_50 = {"ticker": "HDB", "eventCode": "ISS", "eventTitleVi": "Trả cổ tức bằng cổ phiếu tỉ lệ 50%",
         "exrightDate": "2026-10-02T00:00:00", "exerciseRatio": 0.5}
NEN_MEMBER = [("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 19.8, 20.0, 19.0, 19.2),
              ("2026-10-05", 19.2, 19.6, 19.0, 19.4), ("2026-10-06", 19.4, 19.8, 19.2, 19.6)]
NEN_DA_DIEU_CHINH = [("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 20.2, 20.6, 20.0, 20.4),
                     ("2026-10-05", 20.4, 20.8, 20.2, 20.6), ("2026-10-06", 20.6, 21.0, 20.4, 20.8)]


@pytest.fixture(autouse=True)
def _khong_ghi_bo_nho_mau_hinh(monkeypatch):
    monkeypatch.setenv("POST_MORTEM_ENABLED", "0")


def _khung(nen) -> pd.DataFrame:
    df = pd.DataFrame({"time": pd.to_datetime([n[0] for n in nen]), "open": [n[1] for n in nen],
                       "high": [n[2] for n in nen], "low": [n[3] for n in nen], "close": [n[4] for n in nen],
                       "volume": [1_000_000.0] * len(nen)})
    df["ngay"] = df["time"].dt.strftime("%Y-%m-%d")
    return df


def _mot_ma(nen):
    df = _khung(nen)
    return {"df": df, "nguon": "test", "tu": "2026-09-26", "bam": d35.bam_khung(df)}


# ───────────────────────── blob ─────────────────────────
def test_blob_git_bang_git_hash_object_va_doi_CRLF_ve_LF(tmp_path):
    f = tmp_path / "a.py"
    f.write_bytes(b"x = 1\ny = 'd\xc3\xa2u'\n")
    assert d35.blob_git(f) == subprocess.run(["git", "hash-object", str(f)], capture_output=True, text=True,
                                             check=True).stdout.strip()
    g = tmp_path / "b.py"
    g.write_bytes(b"x = 1\r\ny = 'd\xc3\xa2u'\r\n")
    assert d35.blob_git(g) == d35.blob_git(f)


def test_blob_ma_do_tren_dia_khop_ban_da_ky_va_dung_chu_ky_trong_ban_ky():
    assert d35.BLOB_KY == "e8bdc1530593d98396fb7b79ca45c4109941fb65"
    ok, thuc = d35.kiem_blob()
    assert ok and thuc == d35.BLOB_KY


def test_kiem_blob_khac_ban_da_ky_thi_tra_sai(tmp_path):
    f = tmp_path / "chinh_thang_gia.py"
    f.write_text("print('khác')\n", encoding="utf-8")
    ok, thuc = d35.kiem_blob(f)
    assert ok is False and thuc != d35.BLOB_KY
    assert d35.kiem_blob(f, thuc)[0] is True


# ───────────────────────── luật quần thể S2 ─────────────────────────
def _so_luat(tmp_path, *, decisions, nhat_ky_sl0="ok", ngay_vao="2026-10-01", ngay_ra="2026-10-06",
             ma="XYZ", id_=127):
    """Dựng sổ có MỘT lệnh + dòng quyết định; trả (kết nối ro, qt, kho)."""
    duong = tmp_path / "so.db"
    j = PaperTradingJournal(str(duong))
    j.db.execute(
        "INSERT INTO trades (id, symbol, signal_date, entry_date, entry_price, exit_date, exit_price,"
        " exit_reason, stop_loss, take_profit, size_pct, status)"
        " VALUES (?,?,?,?,20000,?,19000,'STOP_LOSS',19500,24000,5,'CLOSED')",
        (id_, ma, ngay_vao, ngay_vao, ngay_ra))
    if nhat_ky_sl0 != "khong_co":
        d = {c: None for c in COT_NHAT_KY}
        d.update(trade_id=id_, symbol=ma, entry_date=ngay_vao, entry_price=20000.0,
                 stop_loss_ban_dau=None if nhat_ky_sl0 == "ok" else nhat_ky_sl0, rui_ro_pct=5.0,
                 diem_agent="{}", ly_do="[]", boi_canh="{}")
        if nhat_ky_sl0 == "ok":
            d["stop_loss_ban_dau"] = 19500.0
        j.db.execute(f"INSERT INTO nhat_ky ({','.join(COT_NHAT_KY)}) VALUES ({','.join('?' * len(COT_NHAT_KY))})",
                     [d[c] for c in COT_NHAT_KY])
    for ngay in decisions:
        j.record_decision(ma, ngay, {"final_score": 70, "recommendation": "GIU"}, False, "x")
    j.db.commit()
    j.db.close()
    c = d35.mo_so(duong)
    t = dict(c.execute("SELECT * FROM trades WHERE id=?", (id_,)).fetchone())
    nk = c.execute("SELECT * FROM nhat_ky WHERE trade_id=?", (id_,)).fetchone()
    t["nhat_ky"] = dict(nk) if nk else None
    return c, [t], {ma: _mot_ma(NEN_MEMBER)}


TAT_CA = ("2026-10-02", "2026-10-05", "2026-10-06")


def _thu_muc_con(tmp_path, ten):
    p = tmp_path / ten
    p.mkdir()
    return p


def test_luat_ca_ba_dieu_kien_dung_thi_vao_quan_the(tmp_path):
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA)
    x = d35.luat_quan_the(c, qt, kho, {"XYZ": []})[0]
    assert (x["e1"], x["e2"], x["e3"], x["vao_qt"], x["truot"]) == (True, True, True, True, [])
    assert x["e1_n_ngay"] == 3 and x["cuoi_khung"] == "2026-10-06"


def test_E1_thieu_mot_ngay_giao_dich_trong_vao_ra_thi_loai_va_goi_ten_ngay(tmp_path):
    c, qt, kho = _so_luat(tmp_path, decisions=("2026-10-02", "2026-10-06"))
    x = d35.luat_quan_the(c, qt, kho, {"XYZ": []})[0]
    assert x["e1"] is False and x["e1_thieu"] == ["2026-10-05"] and x["vao_qt"] is False
    assert x["truot"][0].startswith("E1") and "2026-10-05" in x["truot"][0]


def test_E1_bien_ngay_ra_phai_co_diem_con_ngay_vao_thi_khong_can(tmp_path):
    c, qt, kho = _so_luat(tmp_path, decisions=("2026-10-02", "2026-10-05"))          # thiếu đúng ngày RA 06/10
    assert d35.luat_quan_the(c, qt, kho, {"XYZ": []})[0]["e1_thieu"] == ["2026-10-06"]
    c, qt, kho = _so_luat(_thu_muc_con(tmp_path, "b"), decisions=("2026-10-01",) + TAT_CA)   # thêm điểm ở ngày vào
    assert d35.luat_quan_the(c, qt, kho, {"XYZ": []})[0]["e1"] is True


def test_E1_chi_tinh_dong_quyet_dinh_cua_dung_ma(tmp_path):
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA, ma="XYZ")
    qt[0]["symbol"] = "ABC"
    kho = {"ABC": kho["XYZ"]}
    assert d35.luat_quan_the(c, qt, kho, {"ABC": []})[0]["e1"] is False


@pytest.mark.parametrize("ngay_gd, dem", [("2026-10-01", False),       # đúng ngày vào: mua đã ở giá sau quyền
                                          ("2026-10-02", True),        # ngày đầu sau ngày vào
                                          ("2026-10-06", True),        # đúng ngày cuối của khung
                                          ("2026-10-07", False)])      # sau ngày cuối của khung
def test_E2_gdkhq_chi_tinh_trong_vao_cuoi_khung_loai_tru_vao_gom_cuoi(tmp_path, ngay_gd, dem):
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA)
    lich = {"XYZ": [{"eventCode": "DIV", "exrightDate": ngay_gd + "T00:00:00", "ticker": "XYZ"}]}
    x = d35.luat_quan_the(c, qt, kho, lich)[0]
    assert x["e2"] is (not dem) and x["vao_qt"] is (not dem)
    assert (x["e2_gdkhq"] == [(ngay_gd, "DIV")]) is dem or not dem


@pytest.mark.parametrize("ma_su_kien", ["DIV", "ISS"])
def test_E2_moi_dong_ke_ca_tien_mat_nho_va_ca_ISS_khong_phan_loai_deu_loai_lenh(tmp_path, ma_su_kien):
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA)
    lich = {"XYZ": [{"eventCode": ma_su_kien, "eventTitleVi": "tiêu đề không phân loại được",
                     "exrightDate": "2026-10-03T00:00:00"}]}
    assert d35.luat_quan_the(c, qt, kho, lich)[0]["e2"] is False


def test_E2_dong_khong_co_exrightDate_khong_tinh(tmp_path):
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA)
    lich = {"XYZ": [{"eventCode": "ISS", "exrightDate": None}, {"eventCode": "DIV"}]}
    assert d35.luat_quan_the(c, qt, kho, lich)[0]["e2"] is True


@pytest.mark.parametrize("lich", [{}, {"XYZ": None}])
def test_E2_lich_khong_doc_duoc_thi_loai_voi_ly_do_khong_kiem_duoc_E2(tmp_path, lich):
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA)
    x = d35.luat_quan_the(c, qt, kho, lich)[0]
    assert x["e2"] is False and x["vao_qt"] is False and "E2 (không kiểm được E2)" in x["truot"]


@pytest.mark.parametrize("x, dung", [(19500.0, True), (1, True), (None, False), (0, False), (0.0, False),
                                     (-5.0, False), (float("nan"), False), ("19500", False), (True, False),
                                     (float("inf"), False)])
def test_la_so_duong_chi_nhan_so_thuc_duong_huu_han_khong_nhan_chuoi_hay_bool(x, dung):
    assert d35._la_so_duong(x) is dung


@pytest.mark.parametrize("sl0, dung", [("ok", True), (None, False), (0, False), (0.0, False), (-5.0, False)])
def test_E3_stop_loss_ban_dau_phai_la_so_duong_huu_han(tmp_path, sl0, dung):
    arg = "khong_co" if sl0 is None else sl0
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA, nhat_ky_sl0=arg)
    x = d35.luat_quan_the(c, qt, kho, {"XYZ": []})[0]
    assert x["e3"] is dung and x["vao_qt"] is dung


def test_E3_dong_nhat_ky_co_nhung_o_stop_loss_ban_dau_rong_cung_loai(tmp_path):
    c, qt, kho = _so_luat(tmp_path, decisions=TAT_CA, nhat_ky_sl0=None)               # dòng có, ô NULL
    x = d35.luat_quan_the(c, qt, kho, {"XYZ": []})[0]
    assert x["e3"] is False and x["truot"] == ["E3 (stop_loss_ban_dau = None)"]


def test_hai_ca_duong_122_va_128_khong_bao_gio_vao_quan_the_du_ca_ba_dieu_kien_dung(tmp_path):
    for i in (122, 128):
        c, qt, kho = _so_luat(_thu_muc_con(tmp_path, f"d{i}"), decisions=TAT_CA, id_=i)
        x = d35.luat_quan_the(c, qt, kho, {"XYZ": []})[0]
        assert x["e1"] and x["e2"] and x["e3"] and x["ca_duong"] is True and x["vao_qt"] is False


def test_nhieu_dieu_kien_truot_cung_luc_deu_duoc_goi_ten(tmp_path):
    c, qt, kho = _so_luat(tmp_path, decisions=("2026-10-02",), nhat_ky_sl0="khong_co")
    x = d35.luat_quan_the(c, qt, kho, {"XYZ": [{"eventCode": "DIV", "exrightDate": "2026-10-05T00:00:00"}]})[0]
    assert [t.split(" ")[0] for t in x["truot"]] == ["E1", "E2", "E3"]


# ───────────────────────── S1 ─────────────────────────
def _hang_122(**ghi):
    r = {"exit_reason": "STOP_LOSS", "exit_date": "2026-10-02", "exit_price": 20000.0}
    r.update(ghi)
    return r


def _s1(row, diem=None, nen=NEN_DA_DIEU_CHINH):
    return d35.s1_ca_122(row, _khung(nen), {"2026-10-02": 70, "2026-10-05": 70} if diem is None else diem, "2026-10-01")


def test_S1_dat_khi_cat_lo_o_nen_dau_co_diem_gia_ra_le_mo_va_trong_nen():
    ok, ct_ = _s1(_hang_122(exit_price=20200.0))             # đúng bằng giá mở: ≤ (không chặt)
    assert ok is True and ct_["ngay_dau"] == "2026-10-02" and all(ct_["dieu_kien"].values())
    assert _s1(_hang_122(exit_price=20000.0))[0] is True


def test_S1_gia_ra_tren_gia_mo_cua_nen_thi_truot():
    ok, ct_ = _s1(_hang_122(exit_price=20200.01))
    assert ok is False and ct_["dieu_kien"]["gia_ra_le_mo"] is False


def test_S1_gia_ra_duoi_day_nen_noi_NOI_BIEN_thi_truot_va_bien_la_thap_nhan_0_98():
    # thấp 20000 → cận dưới = 20000 × 0,98 = 19600 (nhân: dạng của su_kien_quyen.kiem_lenh)
    assert _s1(_hang_122(exit_price=19600.0))[0] is True
    ok, ct_ = _s1(_hang_122(exit_price=19599.0))
    assert ok is False and ct_["dieu_kien"]["gia_ra_trong_nen"] is False
    assert ct_["khoang"][0] == pytest.approx(19600.0) and ct_["khoang"][1] == pytest.approx(20600.0 * 1.02)


def test_S1_khong_phai_STOP_LOSS_thi_truot():
    assert _s1(_hang_122(exit_reason="SIGNAL_REVERSED"))[0] is False


def test_S1_ngay_ra_khac_nen_dau_co_diem_thi_truot_ke_ca_khi_la_nen_sau():
    assert _s1(_hang_122(exit_date="2026-10-05"))[0] is False
    # nến 02/10 không có dòng quyết định → nến đầu có điểm là 05/10, ra ở 02/10 là sai nến
    ok, ct_ = _s1(_hang_122(exit_date="2026-10-02"), diem={"2026-10-05": 70})
    assert ok is False and ct_["ngay_dau"] == "2026-10-05"
    assert _s1(_hang_122(exit_date="2026-10-05", exit_price=20400.0), diem={"2026-10-05": 70})[0] is True


def test_S1_khong_co_nen_nao_co_diem_thi_truot_khong_no():
    ok, ct_ = _s1(_hang_122(), diem={})
    assert ok is False and ct_["ngay_dau"] is None


def test_S1_ngay_ra_gia_ra_khong_co_thi_khong_no():
    ok, _ = _s1(_hang_122(exit_price=None, exit_date=None))
    assert ok is False


# ───────────────────────── K0 ─────────────────────────
def _k0(**ghi):
    tham = dict(i_ket={122: (True, {}), 128: (True, {})}, thanh_vien=[1, 2, 3, 4, 5], ii_truot=[], iii=True,
                v_ok={122: True, 128: True}, iv_thieu=[], m0=True)
    tham.update(ghi)
    return d35.phan_k0(**tham)


def test_K0_khong_ly_do_nao_thi_rong():
    assert _k0() == []


def test_K0_quan_the_duoi_5_thi_K0_dung_5_thi_khong():
    assert _k0(thanh_vien=[1, 2, 3, 4]) and "4 < 5" in _k0(thanh_vien=[1, 2, 3, 4])[0]
    assert _k0(thanh_vien=[1, 2, 3, 4, 5]) == []
    assert d35.N_QUAN_THE_TOI_THIEU == 5


def test_K0_mot_lenh_cua_quan_the_khong_tai_lap_la_K0_dung_sai_0():
    assert "[3]" in _k0(ii_truot=[3])[0]


@pytest.mark.parametrize("ghi", [dict(iii=False), dict(m0=False), dict(iv_thieu=[7]),
                                 dict(v_ok={122: True, 128: False}),
                                 dict(i_ket={122: (False, {}), 128: (True, {})}),
                                 dict(i_ket={122: (True, {}), 128: (False, {})})])
def test_K0_moi_doi_chung_khac_truot_la_K0(ghi):
    assert len(_k0(**ghi)) == 1


# ───────────────────────── chay() trên thế giới dựng tay ─────────────────────────
def _the_gioi(tmp_path, monkeypatch, *, thanh_vien=5, ra_sai_o=None, lich_loi=(), them_lenh_ngoai=True,
              nen_122=NEN_DA_DIEU_CHINH, ngoai_kich_hoat=False, bo_nen_vao=None, f_lech=1.0):
    """Sổ có #122 HDB và #128 TCB (nguồn ĐÃ điều chỉnh ÷1,5, lệnh vào 30000 thang cũ), `thanh_vien` lệnh đạt E1–E3
    (mỗi mã một lệnh, cắt lỗ ở nến 02/10) và một lệnh NGOÀI quần thể (không nhật ký, ô ra bị làm sai)."""
    duong = tmp_path / d35.TEN_SO
    j = PaperTradingJournal(str(duong))
    lenh = [(122, "HDB", 30000.0), (128, "TCB", 30000.0)] + [(130 + k, f"A0{k}", 20000.0 * (f_lech if k == 0 else 1.0)) for k in range(thanh_vien)]
    if them_lenh_ngoai:
        lenh.append((150, "B01", 30000.0 if ngoai_kich_hoat else 20000.0))
    kho = {"HDB": _mot_ma(nen_122), "TCB": _mot_ma(NEN_DA_DIEU_CHINH)}
    for i, ma, gia in lenh:
        kho.setdefault(ma, _mot_ma(NEN_MEMBER))
        if ma == "B01" and ngoai_kich_hoat:                 # hình dạng #116: ngoài (ii′) mà bộ chỉnh PHẢI kích hoạt
            kho["B01"] = _mot_ma(NEN_DA_DIEU_CHINH)
        if ma == bo_nen_vao:                                  # thiếu nến VÀO: f không đo được
            kho[ma] = _mot_ma(NEN_MEMBER[1:])
        sl = 28500.0 if gia == 30000.0 else 19500.0
        j.db.execute(
            "INSERT INTO trades (id, symbol, signal_date, entry_date, entry_price, exit_date, exit_price,"
            " exit_reason, stop_loss, take_profit, size_pct, status, created_at)"
            " VALUES (?,?, '2026-10-01','2026-10-01',?, '2026-10-02', 1, 'STOP_LOSS', ?, ?, 5,'CLOSED', ?)",
            (i, ma, gia, sl, gia * 1.2, 1.7e9 + i * 1e6))
        if ma != "B01":
            d = {c: None for c in COT_NHAT_KY}
            d.update(trade_id=i, symbol=ma, entry_date="2026-10-01", entry_price=gia, stop_loss_ban_dau=sl,
                     rui_ro_pct=5.0, diem_agent="{}", ly_do="[]", boi_canh=json.dumps({"atr_pct": 2.0}))
            j.db.execute(f"INSERT INTO nhat_ky ({','.join(COT_NHAT_KY)}) VALUES ({','.join('?' * len(COT_NHAT_KY))})",
                         [d[c] for c in COT_NHAT_KY])
        for ngay in ("2026-10-02", "2026-10-05", "2026-10-06"):
            j.record_decision(ma, ngay, {"final_score": 70, "recommendation": "GIU"}, False, "x")
    j.db.commit()
    j.db.close()
    with open(tmp_path / "nen_do35.pkl", "wb") as f:
        pickle.dump(kho, f)
    # đặt ô ra của sổ = bản cơ sở (như thể sổ thật tái lập được), trừ lệnh bị làm sai
    c = d35.mo_so(duong)
    qt = d35.quan_the(c)
    diem = {t["symbol"]: d35.diem_theo_ngay(c, t["symbol"]) for t in qt}
    ghi = {}
    for t in qt:
        r = d35.phat_lai(duong, t, kho, diem[t["symbol"]], sua=False)["row"]
        ghi[t["id"]] = (r["exit_date"], r["exit_reason"], r["exit_price"])
    c.close()
    import sqlite3
    w = sqlite3.connect(duong)
    for i, (ngay, ly_do, gia) in ghi.items():
        if i == ra_sai_o:
            gia = gia + 1.0
        if i == 150:
            gia = gia + 7.0                     # lệnh NGOÀI quần thể không tái lập: không bao giờ làm K0
        w.execute("UPDATE trades SET exit_date=?, exit_reason=?, exit_price=? WHERE id=?", (ngay, ly_do, gia, i))
    w.commit()
    w.close()
    monkeypatch.setitem(d35.CA_DUONG[128], "ra", (ghi[128][1], d35.ngay10(ghi[128][0]), ghi[128][2]))
    for i in (122, 128):
        monkeypatch.setitem(d35.CA_DUONG[i], "cua_so_den", "2026-10-06")

    def lich_fn(ma):
        if ma in lich_loi:
            raise RuntimeError("hết giờ")
        return [dict(CK_50, ticker=ma)] if ma in ("HDB", "TCB") else []
    return lich_fn


def _chay(tmp_path, capsys, lich_fn, **kw):
    ma_thoat = d35.chay(tmp_path, False, lich_fn=lich_fn, **kw)
    return ma_thoat, capsys.readouterr().out


def test_chay_doi_chung_dat_thi_in_C1_toi_C11_va_C3_C4_doc_tren_quan_the(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert "K0 từ đối chứng: không" in out
    assert "Quần thể (ii′) tính lúc chạy: [130, 131, 132, 133, 134] (5 lệnh)" in out
    assert "#150 " in out and "loại vì E3" in out                       # lệnh NGOÀI được gọi tên, báo kèm
    assert "C3 · C4 đọc trên quần thể (ii′)" in out
    assert "C4: kích hoạt ở [122, 128] trong (ii′)" in out
    assert "(i) #122 theo S1: True" in out and "(i) #128 từng chữ số: True" in out
    assert "=== C1 · C2" in out and "=== PHÁN QUYẾT TỪNG TIÊU CHÍ" in out
    assert ">>> KẾT CỤC ĐO 36: CHƯA ĐỦ DỮ LIỆU ĐỂ PHÁN (thiếu pytest)" in out      # không có pytest thì KHÔNG phán A
    assert "C3: ĐẠT" in out and "C4: ĐẠT" in out and "C6: ĐẠT" in out
    assert (tmp_path / "ket_qua_do36.json").exists()
    d35_json = json.loads((tmp_path / "ket_qua_do36.json").read_text(encoding="utf-8"))
    assert d35_json["quan_the"] == [130, 131, 132, 133, 134]


def test_chay_lenh_ngoai_quan_the_khong_tai_lap_khong_lam_K0(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert "K0 từ đối chứng: không" in out and ">>> KẾT CỤC ĐO 36: K0" not in out
    assert "#150 " in out and "(ii′) lệnh của quần thể KHÔNG tái lập" in out and "[]" in out.split("KHÔNG tái lập")[1][:120]


def test_chay_quan_the_4_lenh_la_K0_va_KHONG_in_so_nao_cua_C(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch, thanh_vien=4)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert ma == 1 and ">>> KẾT CỤC ĐO 36: K0" in out and "quần thể 4 < 5" in out
    for dau in ("=== C1", "=== C3", "=== C6", "=== C8", "=== C9", "=== C11", "PHÁN QUYẾT", "f đo được của từng lệnh",
                "Quy tắc 1", "nhiễu f", "C4: kích hoạt"):
        assert dau not in out, dau
    kq = json.loads((tmp_path / "ket_qua_do36.json").read_text(encoding="utf-8"))
    assert kq["ketcuc"] == "K0" and "C" not in kq and "ket" not in kq


def test_chay_mot_lenh_cua_quan_the_khong_tai_lap_la_K0_khong_in_C(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch, ra_sai_o=132)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert ma == 1 and ">>> KẾT CỤC ĐO 36: K0" in out and "KHÔNG tái lập (dung sai 0): [132]" in out
    assert "=== C1" not in out and "PHÁN QUYẾT" not in out


def test_chay_lich_VCI_cua_ca_duong_khong_doc_duoc_la_K0_khong_in_C(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch, lich_loi=("TCB",))
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert ma == 1 and "(v) lịch VCI không đọc được cho [128]" in out and "=== C1" not in out


def test_chay_lich_cua_mot_ma_thanh_vien_hong_chi_loai_lenh_do_khong_K0_neu_con_du_5(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch, thanh_vien=6, lich_loi=("A01",))
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert "không kiểm được E2" in out and "Quần thể (ii′) tính lúc chạy: [130, 132, 133, 134, 135] (5 lệnh)" in out
    assert ">>> KẾT CỤC ĐO 36: K0" not in out


def test_chay_S1_truot_la_K0(tmp_path, monkeypatch, capsys):
    # nguồn KHÔNG điều chỉnh (giống nến cuối của lượt thật): bản cơ sở của #122 không cắt lỗ ở nến đầu
    nen_chua = [("2026-10-01", 30.0, 30.2, 29.8, 30.0), ("2026-10-02", 30.2, 30.6, 30.0, 30.4),
                ("2026-10-05", 30.4, 30.8, 30.2, 30.6), ("2026-10-06", 30.6, 31.0, 30.4, 30.8)]
    lich_fn = _the_gioi(tmp_path, monkeypatch, nen_122=nen_chua)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert ma == 1 and "(i) ca dương #122 không tái lập (S1)" in out and "=== C1" not in out


def test_chay_blob_lech_la_K0_ngay_tu_dau_khong_doc_so(tmp_path, capsys):
    lech = tmp_path / "chinh_thang_gia.py"
    lech.write_text("# đã sửa\n", encoding="utf-8")
    ma = d35.chay(tmp_path, False, lich_fn=lambda m: [], duong_blob=lech)       # không có sổ, không có nến
    out = capsys.readouterr().out
    assert ma == 1 and "LỆCH" in out and ">>> KẾT CỤC ĐO 36: K0 (blob" in out and "sổ " not in out


def test_chay_khong_ghi_de_so_va_khong_doi_khung(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    truoc = hashlib.sha256((tmp_path / d35.TEN_SO).read_bytes()).hexdigest()
    _chay(tmp_path, capsys, lich_fn)
    assert hashlib.sha256((tmp_path / d35.TEN_SO).read_bytes()).hexdigest() == truoc


class _Chay:
    def __init__(self, ma_thoat_theo_loc):
        self.ma_thoat_theo_loc = ma_thoat_theo_loc

    def __call__(self, lenh, **kw):
        loc = lenh[lenh.index("-k") + 1] if "-k" in lenh else "sheets"
        rc = self.ma_thoat_theo_loc.get(loc, 0)
        return subprocess.CompletedProcess(lenh, rc, stdout="1 passed in 0.1s\n", stderr="")


def test_chay_day_du_ket_cuc_A_khi_moi_tieu_chi_dat_va_chuong_quy_tac_1_keu_khi_tong_duong(
        tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    monkeypatch.setattr(d35.subprocess, "run", _Chay({}))
    ma = d35.chay(tmp_path, True, lich_fn=lich_fn)
    out = capsys.readouterr().out
    assert ma == 0 and ">>> KẾT CỤC ĐO 36: A" in out
    assert "Quy tắc 1: lợi nhuận gộp sau sửa (chưa trừ phí) #122+#128 = +8.00%" in out
    assert "!!! QUY TẮC 1" in out


def test_chay_C5_pytest_do_thi_ket_cuc_B_va_khong_keu_chuong_quy_tac_1(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    monkeypatch.setattr(d35.subprocess, "run", _Chay({"test_C5_": 1}))
    ma = d35.chay(tmp_path, True, lich_fn=lich_fn)
    out = capsys.readouterr().out
    assert ma == 1 and ">>> KẾT CỤC ĐO 36: B" in out and "C5: TRƯỢT" in out and "!!! QUY TẮC 1" not in out


def test_chay_C11_pytest_do_mot_minh_la_C_con_B_va_C_cung_xay_ra_thi_la_B_truoc(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    monkeypatch.setattr(d35.subprocess, "run", _Chay({"test_C11_": 1}))
    d35.chay(tmp_path, True, lich_fn=lich_fn)
    assert ">>> KẾT CỤC ĐO 36: C" in capsys.readouterr().out
    monkeypatch.setattr(d35.subprocess, "run", _Chay({"test_C11_": 1, "test_C7": 1}))
    d35.chay(tmp_path, True, lich_fn=lich_fn)
    assert ">>> KẾT CỤC ĐO 36: B (đồng thời C)" in capsys.readouterr().out


def test_C3_C4_chi_doc_tren_quan_the_lenh_ngoai_kich_hoat_dung_thiet_ke_khong_lam_B(tmp_path, monkeypatch, capsys):
    """Hình dạng #116: một lệnh NGOÀI (ii′) mà bộ chỉnh phải kích hoạt (nguồn đã điều chỉnh sau lệnh). Đọc C4 trên
    cả 20 lệnh như bản ký ĐO 35 thì đây là kích hoạt lệnh thứ ba (B); S3 đọc trên (ii′) thì là báo kèm."""
    lich_fn = _the_gioi(tmp_path, monkeypatch, ngoai_kich_hoat=True)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert "K0 từ đối chứng: không" in out
    assert "C4: kích hoạt ở [122, 128] trong (ii′)" in out and "C3: ĐẠT" in out and "C4: ĐẠT" in out
    bao_kem = out.split("Báo kèm: lệnh NGOÀI")[1].split("=== C6")[0]      # được in cạnh, như báo kèm
    assert "f = 1.5 · bộ chỉnh CHINH" in bao_kem and "số lần chỉnh 1" in bao_kem


def test_chay_mot_lenh_thieu_nen_vao_thi_iv_truot_la_K0_khong_in_C(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch, thanh_vien=6, bo_nen_vao="A02")
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert ma == 1 and "(iv) thiếu f cho [132]" in out and "=== C1" not in out


def test_chay_M0_cuoi_doi_thi_K0_va_bo_dem_C_khong_bao_gio_duoc_xa(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    that = d35.bam_tep
    dem = {"n": 0}

    def bam_tep_doi(p):
        dem["n"] += 1
        return that(p) if dem["n"] <= 2 else "doi-" + str(dem["n"])
    monkeypatch.setattr(d35, "bam_tep", bam_tep_doi)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert ma == 1 and "M0 cuối" in out and ">>> KẾT CỤC ĐO 36: K0" in out
    for dau in ("=== C1", "=== C3", "PHÁN QUYẾT", "Quy tắc 1", "f đo được của từng lệnh"):
        assert dau not in out, dau


@pytest.mark.parametrize("f_lech, dat", [(1.02, True), (1.03, False)])
def test_C4_nguong_la_NGUONG_LECH_chia_2_cua_quan_the_f_lech_1_03_khong_kich_hoat_nhung_van_truot(
        tmp_path, monkeypatch, capsys, f_lech, dat):
    lich_fn = _the_gioi(tmp_path, monkeypatch, f_lech=f_lech)
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert "K0 từ đối chứng: không" in out
    assert ("C4: ĐẠT" in out) is dat and ("C4: TRƯỢT" in out) is (not dat)
    assert "C3: ĐẠT" in out                                   # f dưới 5% thì bộ chỉnh KHÔNG đụng ô nào


def test_S1_nen_dau_la_nen_sau_ngay_vao_du_ngay_vao_cung_co_dong_quyet_dinh():
    ok, ct_ = _s1(_hang_122(exit_price=20150.0), diem={"2026-10-01": 70, "2026-10-02": 70})
    assert ok is True and ct_["ngay_dau"] == "2026-10-02"


def test_chay_128_gia_ra_lech_mot_don_vi_thi_doi_chung_i_truot_K0(tmp_path, monkeypatch, capsys):
    lich_fn = _the_gioi(tmp_path, monkeypatch)
    ra = d35.CA_DUONG[128]["ra"]
    monkeypatch.setitem(d35.CA_DUONG[128], "ra", (ra[0], ra[1], ra[2] + 0.5))
    ma, out = _chay(tmp_path, capsys, lich_fn)
    assert ma == 1 and "(i) ca dương #128 không tái lập" in out and "=== C1" not in out

