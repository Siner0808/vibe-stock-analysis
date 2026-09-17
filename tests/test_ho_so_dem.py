"""Đệm chỉ mục của `tools/ho_so.py`: nhanh hơn thì được, KHÁC đi thì không.

VÌ SAO CÓ FILE NÀY
──────────────────
Một cái đệm là một bản sao thứ hai của sự thật, và dự án này có cả một
bảng lỗi về bản sao thứ hai — `N_DAY_DU` 596/451, cờ C5 `True`/`False`,
lỗi 73 với hai bản cài đặt của một phép lọc. Đệm hồ sơ nguy hiểm hơn cả
ba, vì `ho_so.py` tự khai *"mọi dòng nó in ra là một địa chỉ có thật"*:
một bản đệm ôi in ra địa chỉ KHÔNG còn thật, mà vẫn đúng giọng.

Nên hai câu hỏi, và chỉ hai:

  1. Đệm có ra ĐÚNG thứ bản dựng-từ-đầu ra không?
  2. Vân tay có ĐỔI khi bất cứ đầu vào nào đổi không — kể cả đầu vào
     được thêm vào mai sau?

Câu 2 mới là câu khó, vì nó phải đúng cả với mã CHƯA VIẾT. `test_MOI_DAU_
VAO_cua_bon_chi_muc_deu_nam_trong_VAN_TAY` suy danh sách đầu vào ra từ
**chữ ký thật của bốn hàm chỉ mục**, chứ không gõ lại — thêm nguồn thứ
năm mà quên vân tay thì nó đỏ.
"""
import inspect
import json
import sys
from dataclasses import asdict
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import ho_so  # noqa: E402


# ══ 1. Đệm phải ra ĐÚNG thứ bản dựng-từ-đầu ra ═════════════════════════
def test_DEM_ra_DUNG_thu_ban_DUNG_TU_DAU_ra():
    """Trên một quần thể CÓ NỘI DUNG — quần thể rỗng thì mọi đệm đều đúng."""
    ten = ho_so.ten_dang_bom()
    assert len(ten) >= 10, (
        f"quan the chi co {len(ten)} file — qua mong de phan biet duoc gi")

    tong = 0
    for t in ten:
        moc = asdict(ho_so.doc_ho_so(t, dung_dem=False))
        dem = asdict(ho_so.doc_ho_so(t, dung_dem=True))
        assert moc == dem, f"{t}: dem KHAC ban dung tu dau\n{moc}\n{dem}"
        tong += (len(moc["test"]) + len(moc["buoc"]) + len(moc["do"])
                 + len(moc["loi_cho_hong"]) + len(moc["loi_gac"]))
    assert tong >= 100, (
        f"ca quan the chi co {tong} tham chieu — phep so nay khong phan "
        f"biet duoc mot dem RONG voi mot dem DUNG")
    print(f"PASS  {len(ten)} file · {tong} tham chieu · dem trung khop hoan toan")


def test_DEM_giu_TUPLE_chu_khong_tra_ve_LIST():
    """JSON không có tuple. Quên chuẩn hoá thì đệm đọc ra một kiểu khác.

    Chỗ này im lặng nhất trong cả phép đệm: `[68, "chua-do"]` in ra y hệt
    `(68, "chua-do")` ở mọi chỗ trừ một phép so `==`.
    """
    ci = ho_so.chi_muc(dung_dem=True)
    co_tuple = False
    for v in ci["loi"].values():
        for ds in v.values():
            for x in ds:
                assert isinstance(x, tuple), f"bang loi tra ve {type(x)}: {x!r}"
                co_tuple = True
    assert co_tuple, "bang loi RONG — phep kiem nay khong so gi ca"


# ══ 2. Vân tay phải đổi khi đầu vào đổi ════════════════════════════════
def _bo_dau_vao_gia(tmp: Path) -> dict:
    """Dựng một bộ đầu vào ĐẦY ĐỦ trong thư mục tạm, trả bản đồ để vá."""
    tests = tmp / "tests"
    tests.mkdir()
    (tests / "test_mot.py").write_text("import paper_trading\n", encoding="utf-8")
    state = tmp / "STATE.md"
    state.write_text("## BƯỚC 1 — x\n`paper_trading.py`\n", encoding="utf-8")
    tieu_chi = tmp / "TIEU-CHI.md"
    tieu_chi.write_text("## ĐO 1 — y\n`paper_trading.py`\n", encoding="utf-8")
    bang = tmp / "loi.md"
    bang.write_text("| 1 | `paper_trading.py` | a | b | c |\n", encoding="utf-8")
    phan_lop = tmp / "phan-lop.json"
    phan_lop.write_text('{"loi": {"1": {"lop": "x"}}}', encoding="utf-8")
    return {"THU_MUC_TEST": tests, "STATE": state, "TIEU_CHI": tieu_chi,
            "BANG_LOI": bang, "PHAN_LOP": phan_lop}


def _va(monkeypatch, bo: dict) -> None:
    for ten, p in bo.items():
        monkeypatch.setattr(ho_so, ten, p)


def test_VAN_TAY_doi_khi_MOT_FILE_TEST_doi_NOI_DUNG(tmp_path, monkeypatch):
    bo = _bo_dau_vao_gia(tmp_path)
    _va(monkeypatch, bo)
    truoc = ho_so.van_tay()
    (bo["THU_MUC_TEST"] / "test_mot.py").write_text(
        "import walkforward\n", encoding="utf-8")
    assert ho_so.van_tay() != truoc, "sua mot file test ma van tay dung yen"


def test_VAN_TAY_doi_khi_THEM_mot_file_test_MOI(tmp_path, monkeypatch):
    """Ca mà một vân tay 'chỉ băm các file đã biết' sẽ bỏ sót."""
    bo = _bo_dau_vao_gia(tmp_path)
    _va(monkeypatch, bo)
    truoc = ho_so.van_tay()
    (bo["THU_MUC_TEST"] / "test_hai.py").write_text(
        "import paper_metrics\n", encoding="utf-8")
    assert ho_so.van_tay() != truoc, "them mot file test ma van tay dung yen"


def test_VAN_TAY_doi_khi_MOT_FILE_TEST_bi_XOA(tmp_path, monkeypatch):
    bo = _bo_dau_vao_gia(tmp_path)
    _va(monkeypatch, bo)
    truoc = ho_so.van_tay()
    (bo["THU_MUC_TEST"] / "test_mot.py").unlink()
    assert ho_so.van_tay() != truoc, "xoa mot file test ma van tay dung yen"


def test_VAN_TAY_doi_khi_TUNG_TAI_LIEU_doi(tmp_path, monkeypatch):
    """Bốn tài liệu, mỗi cái một lượt — thiếu một cái là một chỉ mục ôi."""
    bo = _bo_dau_vao_gia(tmp_path)
    _va(monkeypatch, bo)
    for ten in ("STATE", "TIEU_CHI", "BANG_LOI", "PHAN_LOP"):
        truoc = ho_so.van_tay()
        p: Path = bo[ten]
        p.write_text(p.read_text(encoding="utf-8") + "\nthem\n",
                     encoding="utf-8")
        assert ho_so.van_tay() != truoc, f"sua {ten} ma van tay dung yen"


def test_VAN_TAY_doi_khi_MOT_DAU_VAO_BIEN_MAT(tmp_path, monkeypatch):
    """Xoá `loi-phan-lop.json` làm bảng lỗi mất cột lớp — đó là chỉ mục khác."""
    bo = _bo_dau_vao_gia(tmp_path)
    _va(monkeypatch, bo)
    truoc = ho_so.van_tay()
    bo["PHAN_LOP"].unlink()
    assert ho_so.van_tay() != truoc, "mot dau vao bien mat ma van tay dung yen"


def test_VAN_TAY_mang_theo_LUOC_DO_va_GOC(tmp_path, monkeypatch):
    """Vân tay canh ĐẦU VÀO; số hiệu lược đồ canh MÃ. Thiếu nó thì đổi
    hình dạng chỉ mục xong vẫn nạp được một bản đệm đời cũ."""
    bo = _bo_dau_vao_gia(tmp_path)
    _va(monkeypatch, bo)
    truoc = ho_so.van_tay()
    monkeypatch.setattr(ho_so, "LUOC_DO_DEM", ho_so.LUOC_DO_DEM + 1)
    assert ho_so.van_tay() != truoc, "doi LUOC_DO_DEM ma van tay dung yen"

    monkeypatch.setattr(ho_so, "LUOC_DO_DEM", ho_so.LUOC_DO_DEM - 1)
    monkeypatch.setattr(ho_so, "GOC", tmp_path / "mot-ban-sao-khac")
    assert ho_so.van_tay() != truoc, (
        "doi GOC ma van tay dung yen — hai ban sao repo tren cung mot may "
        "se dung chung mot file dem")


# ══ 3. Danh sách đầu vào phải SUY RA, không gõ ═════════════════════════
def test_MOI_DAU_VAO_cua_bon_chi_muc_deu_nam_trong_VAN_TAY():
    """Suy từ CHỮ KÝ THẬT của bốn hàm chỉ mục, không gõ lại danh sách.

    Đây là phép kiểm duy nhất trong file này còn đúng với mã CHƯA VIẾT.
    Thêm một nguồn thứ năm bằng cách thêm tham số mặc định kiểu `Path`
    vào một hàm chỉ mục, mà quên `_dau_vao_chi_muc()`, thì nó đỏ.
    """
    can = set()
    for ham in (ho_so.test_nhap, ho_so.buoc_nhac_ten, ho_so.do_nhac_ten,
                ho_so.bang_loi):
        for ts in inspect.signature(ham).parameters.values():
            if isinstance(ts.default, Path):
                can.add(ts.default.resolve())
    assert can, "khong doc duoc dau vao nao tu chu ky — phep kiem nay mu"

    co = {p.resolve() for p in ho_so._dau_vao_chi_muc()}
    thu_muc = {p.resolve() for p in co}
    for p in sorted(can):
        phu = p in co or any(p == q.parent for q in thu_muc)
        assert phu, (
            f"`{p.name}` la dau vao cua mot chi muc nhung KHONG nam trong "
            f"van tay — dem se oi ma khong ai biet")
    print(f"PASS  {len(can)} dau vao suy tu chu ky, deu nam trong van tay")


# ══ 4. Đệm hỏng thì LÙI, không nổ ══════════════════════════════════════
def test_DEM_HONG_thi_LUI_VE_duong_dung_lai(tmp_path, monkeypatch):
    """Một cái đệm làm hỏng lượt Read thì tệ hơn không có đệm."""
    gia = tmp_path / "dem.json"
    gia.write_text("{khong phai json", encoding="utf-8")
    monkeypatch.setattr(ho_so, "duong_dan_dem", lambda: gia)
    hs = ho_so.doc_ho_so("paper_trading.py", dung_dem=True)
    assert hs.so_tham_chieu > 0, "dem hong lam mat ca ho so"
    assert json.loads(gia.read_text(encoding="utf-8"))["van_tay"], (
        "dem hong ma khong duoc ghi de bang ban dung")


def test_DEM_KHONG_GHI_DUOC_thi_van_chay(tmp_path, monkeypatch):
    """Thư mục tạm chỉ-đọc là chuyện có thật trên máy công ty."""
    monkeypatch.setattr(ho_so, "duong_dan_dem",
                        lambda: tmp_path / "khong-co" / "dem.json")
    hs = ho_so.doc_ho_so("paper_trading.py", dung_dem=True)
    assert hs.so_tham_chieu > 0


def test_DEM_VAN_TAY_LECH_thi_KHONG_duoc_dung(tmp_path, monkeypatch):
    """Ca nguy hiểm nhất: đệm ĐỌC ĐƯỢC nhưng nói về một đời khác."""
    gia = tmp_path / "dem.json"
    gia.write_text(json.dumps({
        "van_tay": "khong-phai-van-tay-that",
        "chi_muc": {"test": {"paper_trading.py": ["test_BIA.py"]},
                    "buoc": {}, "do": {}, "loi": {}},
    }), encoding="utf-8")
    monkeypatch.setattr(ho_so, "duong_dan_dem", lambda: gia)
    hs = ho_so.doc_ho_so("paper_trading.py", dung_dem=True)
    assert "test_BIA.py" not in hs.test, (
        "dem co van tay LECH van duoc nap — day la duong sinh ra mot dia "
        "chi KHONG co that, dung thu ho_so.py sinh ra de tranh")


def test_KHONG_DEM_phai_THAT_SU_bo_qua_dem(tmp_path, monkeypatch):
    """`dung_dem=False` là đường thoát. Một đường thoát không thoát thì
    phép so ở `test_DEM_ra_DUNG_thu_ban_DUNG_TU_DAU_ra` đang so đệm với
    chính nó — và nó sẽ xanh mãi mãi."""
    gia = tmp_path / "dem.json"
    gia.write_text(json.dumps({
        "van_tay": ho_so.van_tay(),
        "chi_muc": {"test": {"paper_trading.py": ["test_BIA.py"]},
                    "buoc": {}, "do": {}, "loi": {}},
    }), encoding="utf-8")
    monkeypatch.setattr(ho_so, "duong_dan_dem", lambda: gia)

    voi = ho_so.doc_ho_so("paper_trading.py", dung_dem=True)
    assert voi.test == ["test_BIA.py"], (
        "dem co van tay DUNG ma khong duoc nap — phep kiem nay khong "
        "phan biet duoc gi")
    khong = ho_so.doc_ho_so("paper_trading.py", dung_dem=False)
    assert "test_BIA.py" not in khong.test, "dung_dem=False van doc dem"
    assert len(khong.test) > 5, "duong dung-tu-dau khong ra duoc gi"


def test_VAN_TAY_doi_khi_CO_FILE_doi_ma_MTIME_thi_khong(tmp_path, monkeypatch):
    """Vì sao vân tay mang cả CỠ chứ không chỉ `mtime_ns`.

    Dựng đúng ca ấy: ghi lại file với nội dung DÀI HƠN rồi ép `mtime` về
    đúng giá trị cũ. Không có cỡ file trong vân tay thì hai đời dữ liệu
    khác nhau mang cùng một vân tay.
    """
    import os
    bo = _bo_dau_vao_gia(tmp_path)
    _va(monkeypatch, bo)
    p: Path = bo["STATE"]
    st = p.stat()
    truoc = ho_so.van_tay()

    them = "## BƯỚC 2 — z\n`x.py`\n"
    p.write_text(p.read_text(encoding="utf-8") + them,
                 encoding="utf-8")
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert p.stat().st_mtime_ns == st.st_mtime_ns, (
        "khong ep duoc mtime — phep kiem nay khong dung duoc ca can dung")
    assert p.stat().st_size != st.st_size, "co file khong doi, ca nay rong"
    assert ho_so.van_tay() != truoc, (
        "cung mtime, khac co file, ma van tay dung yen")


# ══ 5. Ranh giới: không commit trạng thái chạy ═════════════════════════
def test_DEM_KHONG_duoc_nam_trong_CAY_REPO():
    """`CLAUDE.md`: *không commit trạng thái chạy*. Đệm là trạng thái chạy."""
    p = ho_so.duong_dan_dem().resolve()
    assert GOC.resolve() not in p.parents, (
        f"dem nam trong cay repo: {p} — no se vao diff va vao PR")
