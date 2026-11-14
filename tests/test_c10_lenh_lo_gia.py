"""BƯỚC 276 — C10 của ĐO 35 (việc đi kèm kết cục A): lệnh LỖ GIẢ do sự kiện quyền không được dạy bộ nhớ học
và không được đọc thành gap.

Bản ký (`docs/TIEU-CHI-DOC-TRUOC.md` ĐO 35, C10):
  (a) `tools/dung_lai_bo_nho.py` loại lệnh mang nhãn `SU_KIEN_TRONG_LUC_GIU` bằng ĐÚNG tập của
      `nen_su_kien_quyen.tap_loai`; không đọc được nến thì `--ghi` TỪ CHỐI, `--xem` cảnh báo (không đoán);
      bộ nhớ dựng từ bản sao sổ = số lệnh `STOP_LOSS` đã đóng − số lệnh bị loại.
  (b) cờ Gap của sổ bài học và dòng "gap/trượt giá" ở lớp HIỆN đọc nhãn: lệnh nhãn `SU_KIEN_TRONG_LUC_GIU`
      không bị đếm là gap, ghi "lệch thang giá do sự kiện quyền"; chuỗi `hau_kiem_may` đã ghi giữ nguyên.

Tên test mang khoá `test_C10…` để `-k test_C10` chọn được (BƯỚC 273 ghi `-k test_C10` chọn 0 test).
Nến giả là nghìn đồng như nguồn thật: ca "HDB" vào 27.950 trên nến mở 21.500 → f_vào = 27.950 / 21.500 =
1,3 > 1,05 và giá vào ngoài thân nến → `SU_KIEN_TRONG_LUC_GIU`; ca "AAA" vào 20.000 trên nến mở 20.000 → SẠCH.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import dung_lai_bo_nho as dl  # noqa: E402
import nen_su_kien_quyen as nsk  # noqa: E402
import nhat_ky_vi_sao as nkvs  # noqa: E402
import so_bai_hoc as sbh  # noqa: E402
from paper_trading import PaperTradingJournal  # noqa: E402

V, R = "2026-09-28", "2026-10-09"
BD = {"trend_score": 50, "momentum_score": 50, "volume_score": 50}


def _bang(mo, thap, cao):
    return pd.DataFrame({"time": [V, R], "open": [mo[0] / 1000, mo[1] / 1000],
                         "low": [thap[0] / 1000, thap[1] / 1000],
                         "high": [cao[0] / 1000, cao[1] / 1000],
                         "close": [mo[0] / 1000, mo[1] / 1000]})


BANG = {
    "HDB": _bang((21500, 20800), (21000, 20800), (22000, 22000)),   # f_vào 1,3 → SU_KIEN_TRONG_LUC_GIU
    "AAA": _bang((20000, 20500), (19600, 20500), (20400, 21500)),   # SẠCH
}


def _tai(hong=(), goi=None):
    def tai(ma, tu, den):
        if goi is not None:
            goi.append(ma)
        if ma in hong or ma not in BANG:
            return "FAILED", None, 1.0
        return "OK", BANG[ma], 1000.0
    return tai


def _them(j, ma, gia_vao, gia_ra, ly_do="STOP_LOSS", tien_ve_truoc=True, trang_thai="CLOSED"):
    cot = ("symbol, signal_date, entry_date, entry_price, exit_date, exit_price, exit_reason, status,"
           " stop_loss, take_profit, size_pct, entry_score, components, reasons, created_at")
    n = j.db.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    j.db.execute(f"INSERT INTO trades ({cot}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (ma, "2026-09-25", V, gia_vao, R, gia_ra, ly_do, trang_thai, 1.0, 2.0, 10.0, 70,
                  json.dumps(BD), "[]", (1.8e9 + 86400 * (n + 1)) if tien_ve_truoc else None))


def _so(tmp_path, dong):
    """Sổ tệp tạm với các lệnh `(ma, vao, ra, kwargs)`. Trả đường dẫn."""
    db = str(tmp_path / "so.db")
    j = PaperTradingJournal(db)
    for d in dong:
        _them(j, d[0], d[1], d[2], **(d[3] if len(d) > 3 else {}))
    j.db.commit()
    j.db.close()
    return db


def _bam(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


CA_THUONG = [("HDB", 27950.0, 21000.0), ("AAA", 20000.0, 19000.0)]


# ───────────────────────── (a) bộ nhớ học ─────────────────────────
def test_C10a_loai_dung_tap_cua_tap_loai_va_so_mau_bang_stop_loss_tru_so_loai(tmp_path):
    db = _so(tmp_path, CA_THUONG)
    ket = dl.tap_loai_tu_so(db, tai=_tai())
    # CÙNG tập với `nen_su_kien_quyen.tap_loai` chạy trên các lệnh của sổ (id HDB = 1)
    j = PaperTradingJournal(db)
    goc = nsk.tap_loai(j.all_trades(), tai=_tai())
    j.db.close()
    assert set(ket.loai) == set(goc.loai) == {1}
    chua_loai = dl.dung_lai(db)
    da_loai = dl.dung_lai(db, loai_tru=ket.loai)
    assert [m["symbol"] for m in chua_loai] == ["HDB", "AAA"]
    assert [m["symbol"] for m in da_loai] == ["AAA"]
    # số lệnh STOP_LOSS đã đóng − số lệnh loại = số mẫu (phép đếm bản ký, tính tay: 2 − 1 = 1)
    assert len(da_loai) == len(chua_loai) - len(ket.loai) == 1


def test_C10a_lenh_SACH_va_lenh_khong_phai_cat_lo_o_lai_nguyen_ven(tmp_path):
    db = _so(tmp_path, [("AAA", 20000.0, 19000.0), ("AAA", 20000.0, 21000.0, {"ly_do": "TAKE_PROFIT"})])
    ket = dl.tap_loai_tu_so(db, tai=_tai())
    assert ket.loai == {}
    assert [m["trade_id"] for m in dl.dung_lai(db, loai_tru=ket.loai)] == [1]


def test_C10a_ghi_TU_CHOI_khi_khong_doc_duoc_nen_va_khong_ghi_gi(tmp_path, monkeypatch, capsys):
    db = _so(tmp_path, CA_THUONG)
    dich = tmp_path / "bo_nho.json"
    monkeypatch.setattr(dl, "FILE_BO_NHO", str(dich))
    ma = dl.main(["--db", db, "--ghi"], tai=_tai(hong={"HDB", "AAA"}))
    ra = capsys.readouterr().out
    assert ma == 1 and not dich.exists()
    assert "TỪ CHỐI" in ra


def test_C10a_ghi_TU_CHOI_ca_khi_chi_MOT_ma_khong_tai_duoc(tmp_path, monkeypatch):
    db = _so(tmp_path, CA_THUONG)
    dich = tmp_path / "bo_nho.json"
    monkeypatch.setattr(dl, "FILE_BO_NHO", str(dich))
    assert dl.main(["--db", db, "--ghi"], tai=_tai(hong={"AAA"})) == 1
    assert not dich.exists()


def test_C10a_ghi_TU_CHOI_khi_tap_loai_bao_LOI_CHUNG_du_moi_ma_tai_duoc(tmp_path, monkeypatch, capsys):
    """`tap_loai` không ném lỗi mà trả `loi` (không tính được tập loại): mã nào cũng tải được nhưng việc gắn
    nhãn hỏng — `thieu` rỗng, chỉ `loi` có chữ. Không được nhầm đó là "không có lệnh nào cần loại"."""
    db = _so(tmp_path, CA_THUONG)
    dich = tmp_path / "bo_nho.json"
    monkeypatch.setattr(dl, "FILE_BO_NHO", str(dich))

    def hong(*a, **k):
        raise RuntimeError("gắn nhãn hỏng")
    monkeypatch.setattr(nsk.skq, "id_su_kien_trong_luc_giu", hong)
    ket = dl.tap_loai_tu_so(db, tai=_tai())
    assert ket.thieu == () and "gắn nhãn hỏng" in ket.loi and not dl.doc_duoc_nen(ket)
    assert dl.main(["--db", db, "--ghi"], tai=_tai()) == 1 and not dich.exists()
    assert "TỪ CHỐI" in capsys.readouterr().out


def test_C10a_xem_CANH_BAO_khi_khong_doc_duoc_nen_va_noi_mau_chua_loai(tmp_path, monkeypatch, capsys):
    db = _so(tmp_path, CA_THUONG)
    monkeypatch.setattr(dl, "FILE_BO_NHO", str(tmp_path / "bo_nho.json"))
    assert dl.main(["--db", db, "--xem"], tai=_tai(hong={"HDB", "AAA"})) == 0
    ra = capsys.readouterr().out
    assert "KHÔNG đọc được nến" in ra and "CHƯA chắc đã loại" in ra
    assert not (tmp_path / "bo_nho.json").exists()


def test_C10a_ghi_khi_doc_duoc_nen_ghi_mau_da_loai_va_in_so_lenh_loai(tmp_path, monkeypatch, capsys):
    db = _so(tmp_path, CA_THUONG)
    dich = tmp_path / "bo_nho.json"
    monkeypatch.setattr(dl, "FILE_BO_NHO", str(dich))
    assert dl.main(["--db", db, "--ghi"], tai=_tai()) == 0
    mau = json.loads(dich.read_text(encoding="utf-8"))
    assert [m["symbol"] for m in mau] == ["AAA"]
    assert "loại lỗ GIẢ      : 1 lệnh" in capsys.readouterr().out


def test_C10a_khong_co_lenh_tien_ve_truoc_thi_khong_tai_nen_va_ghi_duoc(tmp_path, monkeypatch):
    db = _so(tmp_path, [("HDB", 27950.0, 21000.0, {"tien_ve_truoc": False})])   # lệnh mô phỏng
    goi: list = []
    ket = dl.tap_loai_tu_so(db, tai=_tai(goi=goi))
    assert goi == [] and ket.loai == {} and dl.doc_duoc_nen(ket)
    monkeypatch.setattr(dl, "FILE_BO_NHO", str(tmp_path / "bo_nho.json"))
    assert dl.main(["--db", db, "--ghi"], tai=_tai(goi=goi)) == 0


def test_C10a_doc_so_CHI_DOC_khong_doi_mot_byte(tmp_path):
    db = _so(tmp_path, CA_THUONG)
    truoc = _bam(db)
    dl.tap_loai_tu_so(db, tai=_tai())
    dl.dung_lai(db, loai_tru={1})
    assert _bam(db) == truoc


def test_C10a_AST_dung_lai_goi_dung_tap_loai_va_khong_dinh_nghia_nhan_thu_hai():
    cay = ast.parse((GOC / "tools" / "dung_lai_bo_nho.py").read_text(encoding="utf-8"))
    goi = {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(cay) if isinstance(n, ast.Call)}
    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split(".")[0])
    assert "tap_loai" in goi and "nen_su_kien_quyen" in nhap
    assert "su_kien_quyen" not in nhap, "không nhập thẳng nhãn: chỉ đi qua đường nối"
    # `--ghi` đứng SAU phép kiểm `doc_duoc_nen`: lệnh `return 1` của nhánh từ chối nằm trước `write_text`
    main = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "main")
    dong_tu_choi = [n.lineno for n in ast.walk(main) if isinstance(n, ast.Return)
                    and isinstance(n.value, ast.Constant) and n.value.value == 1]
    dong_ghi = [n.lineno for n in ast.walk(main) if isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") == "write_text"]
    assert dong_tu_choi and dong_ghi and max(dong_tu_choi) < min(dong_ghi)


# ───────────────────────── (b) lớp HIỆN ─────────────────────────
def _dong_nk(trade_id, sl=100.0, gia_ra=90.0):
    return {"trade_id": trade_id, "symbol": "HDB", "entry_date": V, "exit_date": R, "entry_price": 110.0,
            "exit_price": gia_ra, "stop_loss_ban_dau": sl, "exit_reason": "STOP_LOSS",
            "loi_nhuan_rong_pct": -18.0, "ro_chuan_pct": 0.0, "trang_thai_lenh": "CLOSED"}


def test_C10b_co_gap_khong_dem_lenh_nhan_va_noi_ly_do():
    d = _dong_nk(122)
    thuong = sbh.lap_bai_hoc(d)
    assert thuong["gap"] is True                           # 90 < 100: gap như cũ, không nhãn
    nhan = sbh.lap_bai_hoc(d, su_kien_quyen="f_vào 1,300")
    assert nhan["gap"] is None
    assert any(nkvs.NHAN_LECH_THANG_QUYEN in t for t in nhan["thieu"])
    assert "lệch thang giá do sự kiện quyền" in " | ".join(nhan["thieu"])


def test_C10b_lap_bai_hoc_khong_sua_dong_nhat_ky_dau_vao():
    d = _dong_nk(122)
    goc = dict(d)
    sbh.lap_bai_hoc(d, su_kien_quyen="x")
    assert d == goc


def test_C10b_bai_hoc_cho_so_loai_lenh_nhan_khoi_tong_gap_khoa_so_theo_chuoi():
    nk = [_dong_nk(122), _dong_nk("5", sl=100.0, gia_ra=90.0), _dong_nk(7, sl=100.0, gia_ra=105.0)]
    khong = sbh.bai_hoc_cho_so(nk)["tong_hop"]
    assert (khong["n_gap"], khong["n_gap_xet"]) == (2, 3)          # tính tay: 90<100 ×2; 105<100 sai
    co = sbh.bai_hoc_cho_so(nk, nhan_su_kien={122: "lý do"})["tong_hop"]
    assert (co["n_gap"], co["n_gap_xet"]) == (1, 2)                # #122 ra khỏi cả tử lẫn mẫu
    chuoi = sbh.bai_hoc_cho_so(nk, nhan_su_kien={"5": "lý do"})["tong_hop"]
    assert (chuoi["n_gap"], chuoi["n_gap_xet"]) == (1, 2)          # khoá "5" khớp dòng nhật ký có trade_id "5"
    so = sbh.bai_hoc_cho_so([_dong_nk(5)], nhan_su_kien={"5": "x"})["tong_hop"]   # khoá chuỗi, id số
    assert (so["n_gap"], so["n_gap_xet"]) == (0, 0)
    hang = sbh.dong_bang(sbh.bai_hoc_cho_so(nk, nhan_su_kien={122: "x"})["bai_hoc"][0])
    assert hang["Gap"] is None


def test_C10b_dong_gap_cua_hau_kiem_may_doc_nhan_va_chuoi_da_ghi_khong_doi():
    chuoi = " | ".join(nkvs.hau_kiem_may(sl_ban_dau=100.0, exit_price=90.0, exit_reason="STOP_LOSS",
                                         loi_nhuan_rong_pct=-10.0, R=-1.0, alpha=None, diem={}))
    goc = chuoi
    # chữ ĐÃ GHI giữ từng byte (bản ghi ở Sheets không bị chạm)
    assert ("thoát DƯỚI cắt lỗ ban đầu 10.00% — gap/trượt giá "
            "(bất biến 3: gap qua SL khớp ở giá mở cửa)") in chuoi
    khong_nhan = nkvs.hau_kiem_may_hien(chuoi, False)
    assert " | ".join(khong_nhan) == chuoi
    co_nhan = nkvs.hau_kiem_may_hien(chuoi, True)
    assert not any(d.startswith("thoát DƯỚI cắt lỗ ban đầu") for d in co_nhan)
    assert sum(nkvs.NHAN_LECH_THANG_QUYEN in d for d in co_nhan) == 1
    assert len(co_nhan) == len(khong_nhan)                              # thay MỘT dòng, không thêm/bớt
    khac = [(a, b) for a, b in zip(khong_nhan, co_nhan) if a != b]
    assert len(khac) == 1 and khac[0][0].startswith("thoát DƯỚI")        # các dòng khác nguyên
    assert chuoi == goc                                                  # hàm không sửa đầu vào


def test_C10b_lenh_khong_co_dong_gap_thi_nhan_khong_doi_gi():
    chuoi = " | ".join(nkvs.hau_kiem_may(sl_ban_dau=100.0, exit_price=105.0, exit_reason="STOP_LOSS",
                                         loi_nhuan_rong_pct=5.0, R=0.5, alpha=1.0, diem={}))
    assert nkvs.hau_kiem_may_hien(chuoi, True) == nkvs.hau_kiem_may_hien(chuoi, False)
    assert nkvs.hau_kiem_may_hien(None, True) == [] and nkvs.hau_kiem_may_hien("", False) == []


def test_C10b_noi_that_o_app_AST_chi_doc_nhan_khi_da_bam_nut_va_truyen_vao_hai_cho_hien():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    ham = {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}
    goi = lambda nut: [n for n in ast.walk(nut) if isinstance(n, ast.Call)]          # noqa: E731
    ten = lambda n: getattr(n.func, "attr", getattr(n.func, "id", ""))                # noqa: E731
    # sổ bài học: nhãn tính TRƯỚC `bai_hoc_cho_so` và được TRUYỀN vào đó bằng đối số `nhan_su_kien`
    sbh_goi = goi(ham["_khoi_so_bai_hoc"])
    dong_nhan = [n.lineno for n in sbh_goi if ten(n) == "_nhan_quyen_cho_hien"]
    bh = [n for n in sbh_goi if ten(n) == "bai_hoc_cho_so"]
    assert len(dong_nhan) == 1 and len(bh) == 1 and dong_nhan[0] < bh[0].lineno
    assert "nhan_su_kien" in {k.arg for k in bh[0].keywords}
    # chi tiết một lệnh: dòng "Hậu kiểm máy" đi qua `hau_kiem_may_hien`
    hien = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and ten(n) == "hau_kiem_may_hien"]
    assert len(hien) == 1 and len(hien[0].args) == 2
    assert not isinstance(hien[0].args[1], ast.Constant), "cờ nhãn phải TÍNH từ lệnh, không phải hằng"
    # `_nhan_quyen_cho_hien` chỉ đọc nhãn SAU chốt "đã bấm nút" và không tự có nút
    f = ham["_nhan_quyen_cho_hien"]
    chot = [n for n in f.body if isinstance(n, ast.If) and "su_kien_quyen_co_gia" in ast.unparse(n.test)]
    assert chot and f.body[1] is chot[0]            # body[0] là docstring; chốt là câu lệnh đầu tiên
    tai = [n.lineno for n in goi(f) if ten(n) == "_nen_cho_su_kien_quyen"]
    assert tai and min(tai) > chot[0].lineno
    assert {"pham_vi_tai", "id_su_kien_trong_luc_giu"} <= {ten(n) for n in goi(f)}    # nhãn của MÁY, không tự dựng
    assert not [n for n in goi(f) if ten(n) in ("button", "write_all", "push")]


def test_C10b_lop_hien_khong_nhap_su_kien_quyen_va_khong_ghi_so():
    for ten in ("so_bai_hoc.py", "nhat_ky_vi_sao.py"):
        cay = ast.parse((GOC / ten).read_text(encoding="utf-8"))
        nhap = {(n.module or "").split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
        nhap |= {a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names}
        assert not ({"su_kien_quyen", "nen_su_kien_quyen", "gspread", "sheets_store"} & nhap), ten


def test_C10_tai_lieu_va_mot_dinh_nghia_DAU_NHAN_GAP_dung_o_ca_cho_sinh_lan_cho_hien():
    cay = ast.parse((GOC / "nhat_ky_vi_sao.py").read_text(encoding="utf-8"))
    ham = {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}
    for ten in ("hau_kiem_may", "hau_kiem_may_hien"):
        ten_dung = {n.id for n in ast.walk(ham[ten]) if isinstance(n, ast.Name)}
        assert "DAU_NHAN_GAP" in ten_dung, ten
