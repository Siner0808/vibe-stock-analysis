"""BƯỚC 280, phần B — đường đọc dùng chung của app lấy tab `decisions` chỉ 8 CỘT ĐẦU, mọi dòng, mọi con số y hệt.

Vì sao không phải "chỉ phần gần đây" (xem `docs/STATE.md` BƯỚC 280, mục B): cả ba nơi app dùng `quyet_dinh`
(ô "Sổ ảo" của tab kế hoạch cho MỌI ngày nến, `ngay_gan_nhat`, bản tin của ngày bất kỳ người dùng chọn — ô
ngày không có mốc dưới) đều cần lịch sử đủ, và thứ tự dòng theo `seq` KHÔNG phải thứ tự ngày (76 bước lùi
ngày đo 16/11/2026). Cái nặng là ba cột JSON ở cuối (`components`, `reasons`, `data_quality`), mà bản tin
không đọc: bỏ cột, giữ dòng.

Khoá năm điều:

1. **Cùng dict**: `doc_so_ban_tin` trên đường hẹp cho đúng thứ đường đầy đủ cho (kiểu, NULL ≠ chuỗi rỗng).
2. **Không hỏi cột nặng**: vùng hỏi là `1:1` (tiêu đề đủ cột) và `A2:H`; không có vùng nào phủ cột I..K.
3. **Tiêu đề vẫn kiểm ĐỦ 11 cột** dù dữ liệu chỉ 8: đổi tên một cột nặng thì vẫn nổ.
4. **Không đọc cột ngoài vùng một cách lặng lẽ**: bộ đọc cần cột nặng (sân đấu) hỏi đường hẹp thì NỔ.
5. **N suy từ danh sách cột**, không gõ số; `COT_QUYET_DINH_BAN_TIN` là tiền tố của `DECISION_COLS`.
"""
import re

import pytest

import google_sheets_sync as gss
import sheets_store as ss


def _dong(cols, **kv):
    return [str(kv.get(c, "")) for c in cols]


def _luoi() -> dict:
    nang = '{"momentum": 61.2, "x": "' + "y" * 400 + '"}'
    dec = [list(ss.DECISION_COLS)]
    for seq, (ma, ngay, diem, acted, ly_do) in enumerate([
            ("HPG", "2026-10-01", "70", "1", ""),
            ("FPT", "2026-11-02", "", "0", "điểm dưới ngưỡng"),
            ("VNM", "2026-11-02", "40", "0", ""),
            ("ACB", "2023-12-25", "55", "0", "đã có lệnh")], start=1):      # ngày CŨ nằm SAU trong sổ (backfill)
        dec.append(_dong(ss.DECISION_COLS, seq=seq, at="1.7e9", symbol=ma, signal_date=ngay, score=diem,
                         recommendation="BUY", acted=acted, skip_reason=ly_do,
                         components=nang, reasons=nang, data_quality=nang))
    return {
        ss.TAB_TRADES: [list(ss.TRADE_COLS), _dong(ss.TRADE_COLS, id=1, symbol="HPG", status="OPEN")],
        ss.TAB_NHAT_KY: [list(ss.NHAT_KY_COLS), _dong(ss.NHAT_KY_COLS, trade_id=1)],
        ss.TAB_DECISIONS: dec,
        ss.TAB_HAU_KIEM: [list(ss.HAU_KIEM_COLS)],
        ss.TAB_KE_HOACH: [list(ss.KE_HOACH_COLS), _dong(ss.KE_HOACH_COLS, seq=5, symbol="HPG", signal_date="2026-11-02")],
    }


def _cat(rows):
    ra = []
    for r in rows:
        r = list(r)
        while r and r[-1] == "":
            r.pop()
        ra.append(r)
    while ra and not ra[-1]:
        ra.pop()
    return ra


def _chu_so_cot(chu):
    return ord(chu) - 64


class _Sh:
    """Spreadsheet giả hiểu ba kiểu vùng: `'tab'`, `'tab'!1:1`, `'tab'!A2:H` (đúng thứ app hỏi)."""

    def __init__(self, luoi):
        self.luoi, self.nhat = luoi, []

    def values_batch_get(self, ranges, params=None):
        self.nhat.append(list(ranges))
        ra = []
        for r in ranges:
            m = re.fullmatch(r"'(.+)'(?:!(.+))?", r)
            ten, vung = m.group(1).replace("''", "'"), m.group(2)
            rows = self.luoi[ten]
            if vung == "1:1":
                rows = rows[:1]
            elif vung is not None:
                mm = re.fullmatch(r"A(\d+):([A-Z])", vung)
                dau, cuoi = int(mm.group(1)), _chu_so_cot(mm.group(2))
                rows = [r_[:cuoi] for r_ in rows[dau - 1:]]
            v = _cat(rows)
            ra.append({"range": r, **({"values": v} if v else {})})
        return {"valueRanges": ra}

    def worksheets(self):
        raise AssertionError("đường hẹp không được rơi về từng tab khi mọi tab đều có")


def _google(luoi) -> ss.GoogleSheet:
    g = object.__new__(ss.GoogleSheet)
    g._sh = _Sh(luoi)
    return g


def _ban_tin_qua(backend):
    return ss.doc_so_ban_tin(backend)


def _ref(luoi) -> ss.InMemorySheet:
    s = ss.InMemorySheet()
    s.tabs = {t: [list(r) for r in v] for t, v in luoi.items()}
    return s


# ── 1. cùng dict ────────────────────────────────────────────────────────────
def test_ban_tin_duong_hep_bang_duong_day_du_tung_dict():
    luoi = _luoi()
    hep = gss.BackendDocChung(_google(luoi), hep=gss.COT_HEP_APP)
    assert _ban_tin_qua(hep) == _ban_tin_qua(_ref(luoi))
    qd = _ban_tin_qua(hep)["quyet_dinh"]
    assert [d["seq"] for d in qd] == [1, 2, 3, 4] and qd[1]["score"] is None and qd[2]["skip_reason"] == ""
    assert qd[3]["signal_date"] == "2023-12-25"            # ngày cũ nằm sau trong sổ vẫn còn: không có "đuôi" nào bị cắt
    assert set(qd[0]) == set(ss.COT_QUYET_DINH_BAN_TIN)


def test_ba_bo_doc_con_lai_giong_nhau_tren_duong_hep():
    luoi = _luoi()
    hep = gss.BackendDocChung(_google(luoi), hep=gss.COT_HEP_APP)
    ref = _ref(luoi)
    assert ss.doc_nhat_ky(hep) == ss.doc_nhat_ky(ref)
    assert ss.doc_ke_hoach(hep) == ss.doc_ke_hoach(ref)
    assert ss.doc_hau_kiem(hep) == ss.doc_hau_kiem(ref)


def test_tab_decisions_chi_tieu_de_hoac_rong_ra_danh_sach_rong():
    luoi = _luoi()
    luoi[ss.TAB_DECISIONS] = [list(ss.DECISION_COLS)]
    assert _ban_tin_qua(gss.BackendDocChung(_google(luoi), hep=gss.COT_HEP_APP))["quyet_dinh"] == []
    luoi[ss.TAB_DECISIONS] = []
    assert _ban_tin_qua(gss.BackendDocChung(_google(luoi), hep=gss.COT_HEP_APP))["quyet_dinh"] == []


# ── 2. không hỏi cột nặng ───────────────────────────────────────────────────
def test_vung_hoi_la_tieu_de_day_du_va_A2_H_khong_vung_nao_phu_cot_nang():
    g = _google(_luoi())
    ra = g.read_rows_nhieu(gss.TAB_APP_DOC, hep=gss.COT_HEP_APP)
    (lan_hoi,) = g._sh.nhat                                   # MỘT lệnh gọi
    assert f"'{ss.TAB_DECISIONS}'!1:1" in lan_hoi and f"'{ss.TAB_DECISIONS}'!A2:H" in lan_hoi
    assert f"'{ss.TAB_DECISIONS}'" not in lan_hoi              # không có vùng "cả tab"
    assert ra[ss.TAB_DECISIONS][0] == list(ss.DECISION_COLS)   # tiêu đề ĐỦ 11 cột
    assert all(len(r) <= 8 for r in ra[ss.TAB_DECISIONS][1:])  # dữ liệu: không cột nặng nào về tới máy
    assert all("y" * 50 not in c for r in ra[ss.TAB_DECISIONS][1:] for c in r)


def test_tab_khac_van_doc_ca_tab():
    g = _google(_luoi())
    g.read_rows_nhieu(gss.TAB_APP_DOC, hep=gss.COT_HEP_APP)
    lan_hoi = g._sh.nhat[0]
    for t in gss.TAB_APP_DOC:
        if t != ss.TAB_DECISIONS:
            assert f"'{t}'" in lan_hoi


# ── 3. tiêu đề vẫn kiểm đủ ──────────────────────────────────────────────────
def test_doi_ten_cot_nang_o_tieu_de_van_NO_du_du_lieu_chi_doc_8_cot():
    luoi = _luoi()
    luoi[ss.TAB_DECISIONS][0][ss.DECISION_COLS.index("components")] = "thanh_phan"
    with pytest.raises(ss.SheetSchemaError):
        _ban_tin_qua(gss.BackendDocChung(_google(luoi), hep=gss.COT_HEP_APP))


def test_doi_ten_cot_dau_van_NO():
    luoi = _luoi()
    luoi[ss.TAB_DECISIONS][0][0] = "so_thu_tu"
    with pytest.raises(ss.SheetSchemaError):
        _ban_tin_qua(gss.BackendDocChung(_google(luoi), hep=gss.COT_HEP_APP))


# ── 4. không đọc cột ngoài vùng một cách lặng lẽ ───────────────────────────
def test_san_dau_can_cot_nang_ma_hoi_duong_hep_thi_NO():
    hep = gss.BackendDocChung(_google(_luoi()), hep=gss.COT_HEP_APP)
    with pytest.raises(ss.SheetError, match="cột đầu"):
        ss.doc_quyet_dinh_san_dau(hep)
    day_du = ss.doc_quyet_dinh_san_dau(_ref(_luoi()))
    assert day_du[0]["components"].startswith("{")


def test_ranh_gioi_cot_hep_cot_thu_8_con_duoc_cot_thu_9_thi_no():
    """Cột `seq`..`skip_reason` (chỉ số 0..7) được hỏi; `components` (chỉ số 8, cột I) là cột ĐẦU TIÊN ngoài vùng."""
    hep = gss.BackendDocChung(_google(_luoi()), hep=gss.COT_HEP_APP)
    assert len(ss._doc_tab(hep, ss.TAB_DECISIONS, ss.DECISION_COLS, ss.DECISION_COLS[:8])) == 4
    with pytest.raises(ss.SheetError):
        ss._doc_tab(hep, ss.TAB_DECISIONS, ss.DECISION_COLS, ("components",))


def test_backend_khong_khai_hep_thi_san_dau_van_doc_duoc():
    assert len(ss.doc_quyet_dinh_san_dau(gss.BackendDocChung(_ref(_luoi())))) == 4


# ── 5. N suy từ danh sách cột ───────────────────────────────────────────────
def test_N_suy_tu_cot_ban_tin_va_la_tien_to_cua_luoc_do():
    n = gss.COT_HEP_APP[ss.TAB_DECISIONS]
    assert ss.DECISION_COLS[:n] == ss.COT_QUYET_DINH_BAN_TIN
    assert ss._chu_cot(n) == "H"


def test_chu_cot_ngoai_A_Z_thi_no():
    with pytest.raises(ValueError):
        ss._chu_cot(0)
    with pytest.raises(ValueError):
        ss._chu_cot(27)


def test_backend_doc_chung_cua_ung_dung_khai_hep(monkeypatch):
    got = {}
    monkeypatch.setattr(gss, "get_backend", lambda backend=None: got.setdefault("b", _ref(_luoi())))
    monkeypatch.setattr(gss, "_DUNG_CHUNG", None)
    d = gss.backend_doc_chung()
    assert d.cot_hep == gss.COT_HEP_APP and gss.COT_HEP_APP == {ss.TAB_DECISIONS: 8}


def test_400_roi_ve_duong_cu_doc_day_du_van_ra_dung_ban_tin():
    class Loi400(Exception):
        code = 400
    luoi = _luoi()
    g = _google(luoi)
    g._sh.values_batch_get = lambda ranges, params=None: (_ for _ in ()).throw(Loi400())

    class Ws:
        def __init__(self, t):
            self.title, self._v = t, luoi[t]

        def get_all_values(self):
            n = max(len(r) for r in self._v)
            return [list(r) + [""] * (n - len(r)) for r in self._v]
    g._sh.worksheets = lambda: [Ws(t) for t in luoi]
    assert _ban_tin_qua(gss.BackendDocChung(g, hep=gss.COT_HEP_APP)) == _ban_tin_qua(_ref(luoi))
