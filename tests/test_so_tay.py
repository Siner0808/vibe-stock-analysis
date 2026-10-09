"""Gác của `tools/so_tay.py` — dựng câu hỏi và ghi sổ soát chéo (BƯỚC 130).

Phép kiểm đáng tin nhất ở đây là phép đi qua CA THẬT đã biết trước: khuôn
câu hỏi phải dựng lại được BYTE-CHO-BYTE câu hỏi BƯỚC 129 đã gửi thật, đọc
từ chính sổ. Một khuôn "trông giống" mà không tái lập được câu thật là một
khuôn khác.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
import so_tay as st  # noqa: E402


def _so_that() -> dict:
    return json.loads((GOC / "docs" / "soat-notebooklm.json").read_text(encoding="utf-8"))


def _muc_tot(**thay) -> dict:
    m = {"buoc": "BƯỚC 9999",
         "cau_hoi": st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["a statement that y"]),
         "phat_hien": [{"noi_dung": "CLAUDE.md: mot cau",
                        "tu_kiem": "grep -n 'mot cau' CLAUDE.md -> dong 1",
                        "phan_quyet": "THẬT."}]}
    m.update(thay)
    return m


# ── dựng câu hỏi ─────────────────────────────────────────────────────────

def test_DUNG_LAI_NGUYEN_VAN_cau_hoi_THAT_cua_BUOC_129():
    cau = _so_that()["soat"]["BƯỚC 129"]["cau_hoi"]
    dau = "I am about to write BƯỚC 129 into docs/STATE.md: "
    giua = " Is there ANY place in your sources that CONTRADICTS"
    assert cau.startswith(dau)
    ket_luan = cau[len(dau):cau.index(giua)]
    vi_du = cau[cau.index("For example: ") + len("For example: "):
                cau.index(". Quote each such sentence")]
    assert st.dung_cau_hoi("BƯỚC 129", ket_luan, [vi_du]) == cau


def test_CAU_HOI_luon_MOT_DONG_ke_ca_khi_ket_luan_xuong_dong():
    cau = st.dung_cau_hoi("BƯỚC 1", "dong mot\ndong hai\r\n  dong ba " * 5,
                          ["vi du\nhai dong"])
    assert "\n" not in cau and "\r" not in cau


def test_CAU_HOI_mang_LOI_THOAT_mien_tru_va_doi_TIENG_VIET():
    cau = st.dung_cau_hoi("BƯỚC 1", "y" * 60, ["z"])
    assert st.O_THOAT in cau
    assert st.MIEN_TRU_DA_DANH_DAU in cau
    assert cau.endswith(st.DOI_TRA_LOI_VIET)


def test_O_THOAT_la_NGUYEN_VAN_loi_thoat_cac_luot_that_da_dung():
    so = _so_that()["soat"]
    for b in ("BƯỚC 127", "BƯỚC 128", "BƯỚC 129"):
        assert so[b]["o_thoat"] == st.O_THOAT, b


@pytest.mark.parametrize("ket_luan, vi_du", [
    ("ngan qua", ["x"]),            # hỏi RỘNG
    ("y" * 60, []),                 # không có ví dụ câu nghi ngờ
    ("y" * 60, ["   "]),            # ví dụ rỗng
])
def test_CAU_HOI_tu_choi_hoi_RONG(ket_luan, vi_du):
    with pytest.raises(st.TuChoi):
        st.dung_cau_hoi("BƯỚC 1", ket_luan, vi_du)


# ── ghi sổ ───────────────────────────────────────────────────────────────

@pytest.fixture
def so_tam(tmp_path):
    """Bản sao sổ thật, BỎ mọi mục `khong_bat_buoc_vi` thật.

    Các ca dưới đây đếm chính xác những BƯỚC mà `ghi` đưa cho máy phán và đặt
    `_moc_chi_hoi_khi_doi_luat` lên 9990; một mục `khong_bat_buoc_vi` thật của sổ
    (từ BƯỚC 165) lọt vào sẽ bị phán lại và làm hai ca đỏ giả (đo 08/10/2026:
    `[165, 9999] != [9999]`). Test phải độc lập với sổ thật, không phụ thuộc việc
    sổ thật có mục nào.
    """
    p = tmp_path / "soat-notebooklm.json"
    d = json.loads((GOC / "docs" / "soat-notebooklm.json").read_text(encoding="utf-8"))
    d["soat"] = {k: v for k, v in d["soat"].items()
                 if not (isinstance(v, dict) and "khong_bat_buoc_vi" in v)}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def test_GHI_them_DUNG_MOT_khoa_va_khong_cham_khoa_nao_khac(so_tam):
    truoc = json.loads(so_tam.read_text(encoding="utf-8"))
    st.ghi(_muc_tot(), so=so_tam, ngay="2026-09-27")
    sau = json.loads(so_tam.read_text(encoding="utf-8"))
    assert set(sau["soat"]) - set(truoc["soat"]) == {"BƯỚC 9999"}
    del sau["soat"]["BƯỚC 9999"]
    assert sau == truoc
    assert so_tam.read_text(encoding="utf-8").endswith("}\n")


def test_GHI_ra_dong_ma_GAC_SO_nhan(so_tam):
    """Dòng ghi ra phải qua đúng các luật của gác sổ thật."""
    spec = importlib.util.spec_from_file_location(
        "gac_so", GOC / "tests" / "test_soat_notebooklm.py")
    gac = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gac)
    assert set(gac.HOP_LE) == set(st.HOP_LE)
    assert gac.DOI_TRA_LOI_VIET == st.DOI_TRA_LOI_VIET.lower().rstrip(".")
    dong = st.ghi(_muc_tot(), so=so_tam, ngay="2026-09-27")
    assert dong["o_thoat"] in dong["cau_hoi"]
    assert gac.DOI_TRA_LOI_VIET in dong["cau_hoi"].lower()


@pytest.mark.parametrize("ten, thay", [
    ("thieu loi thoat", {"cau_hoi": "I am about to write BƯỚC 9999. Answer in Vietnamese."}),
    ("xuong dong", {"cau_hoi": _muc_tot()["cau_hoi"].replace(" Is there", "\nIs there")}),
    ("khong doi tieng Viet", {"cau_hoi": _muc_tot()["cau_hoi"].replace(st.DOI_TRA_LOI_VIET, "")}),
    ("khong the nao", {"phat_hien": []}),
    ("ca hai the", {"khong_tim_thay_gi": True, "_tu_kiem_cau_am": "grep x" * 10}),
    ("cau AM thieu tu kiem", {"phat_hien": [], "khong_tim_thay_gi": True}),
    ("phan quyet DUNG thay THAT", {"phat_hien": [{"noi_dung": "n", "tu_kiem": "grep -n x CLAUDE.md -> 1", "phan_quyet": "ĐÚNG."}]}),
    ("tu kiem qua ngan", {"phat_hien": [{"noi_dung": "n", "tu_kiem": "grep", "phan_quyet": "THẬT."}]}),
    ("buoc sai", {"buoc": "buoc 9999"}),
    ("trung BUOC da co", {"buoc": "BƯỚC 129"}),
])
def test_GHI_tu_choi_va_KHONG_cham_file(so_tam, ten, thay):
    truoc = so_tam.read_bytes()
    with pytest.raises(st.TuChoi):
        st.ghi(_muc_tot(**thay), so=so_tam, ngay="2026-09-27")
    assert so_tam.read_bytes() == truoc, ten


def test_GHI_cau_AM_co_tu_kiem_thi_nhan(so_tam):
    dong = st.ghi(_muc_tot(phat_hien=[], khong_tim_thay_gi=True,
                           _tu_kiem_cau_am="grep -n 'mau' CLAUDE.md docs/HANDOFF.md -> 0 dong noi nguoc"),
                  so=so_tam, ngay="2026-09-27")
    assert dong["khong_tim_thay_gi"] is True and dong["phat_hien"] == []


# ── dòng lệnh ────────────────────────────────────────────────────────────

def test_CLI_HOI_in_MOT_DONG_va_TU_CHOI_ra_stderr_doc_duoc_UTF8():
    ok = subprocess.run(
        [sys.executable, str(GOC / "tools" / "so_tay.py"), "hoi",
         "--buoc", "BƯỚC 1", "--ket-luan", "k" * 60, "--vi-du", "một câu tiếng Việt"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    assert ok.returncode == 0, ok.stderr
    assert ok.stdout.count("\n") == 1 and "một câu tiếng Việt" in ok.stdout
    hong = subprocess.run(
        [sys.executable, str(GOC / "tools" / "so_tay.py"), "hoi",
         "--buoc", "BƯỚC 1", "--ket-luan", "ngắn"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    assert hong.returncode == 1
    assert "TU CHOI" in (hong.stderr or "")


def test_LENH_GUI_chon_O_CHAT_theo_nhan_KHONG_lay_textarea_dau_tien():
    """Lỗi 113: `textarea` ĐẦU TIÊN của trang là ô *"Tìm nguồn mới trên web"*.
    Ngày 29/09 câu hỏi BƯỚC 142 đi vào đó, bấm Gửi là đi tìm nguồn trên web."""
    cau = st.dung_cau_hoi("BƯỚC 1", "k" * 60, ["câu có 'nháy đơn' và \"nháy kép\""])
    js = st.lenh_gui(cau)
    assert 'textarea[aria-label="Hộp truy vấn"]' in js
    assert "querySelector('textarea')" not in js and 'querySelector("textarea")' not in js
    assert json.dumps(cau, ensure_ascii=False) in js      # câu nhúng NGUYÊN VĂN
    # nút Gửi còn khoá ngay sau `input` — đo 29/09 bấm lúc ấy không gửi gì:
    # phải có một VÒNG CHỜ trên `disabled`, đứng TRƯỚC lệnh bấm
    cho = re.search(r"for \([^)]*b\.disabled[^)]*\)\s*await", js)
    assert cho and cho.start() < js.index("b.click()")


def test_CLI_HOI_JS_in_lenh_gui_cua_DUNG_cau_hoi():
    arg = ["--buoc", "BƯỚC 1", "--ket-luan", "k" * 60, "--vi-du", "một câu"]
    chay = [sys.executable, str(GOC / "tools" / "so_tay.py"), "hoi"]
    cau = subprocess.run(chay + arg, capture_output=True, text=True,
                         encoding="utf-8", cwd=str(GOC)).stdout.strip()
    js = subprocess.run(chay + arg + ["--js"], capture_output=True, text=True,
                        encoding="utf-8", cwd=str(GOC))
    assert js.returncode == 0, js.stderr
    assert js.stdout.strip() == st.lenh_gui(cau)


def test_CLI_GHI_tep_khong_doc_duoc_la_MA_2_khong_phai_traceback(tmp_path):
    for tep, noi_dung in (("vang.json", None), ("hong.json", "{khong phai json")):
        p = tmp_path / tep
        if noi_dung is not None:
            p.write_text(noi_dung, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(GOC / "tools" / "so_tay.py"), "ghi", str(p)],
            capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
        assert r.returncode == 2, (tep, r.returncode, r.stderr)
        assert "CHUA DOC DUOC" in (r.stderr or "") and "Traceback" not in (r.stderr or ""), tep


# ── BƯỚC 164: đường ghi `khong_bat_buoc_vi` và lệnh `dem` ────────────────────
#
# Gác của phần mới thêm ở BƯỚC 164 (người dùng "Đồng ý" thu hẹp Quy tắc 3, 08/10/2026).
# Đột biến lô B phát hiện phần này chưa có gác nào trong file này.

LY_DO = "BUOC chi ghi ket qua luot soat dinh ky, khong doi luat hay ket luan do"


def _khong_cham(n):
    return ["docs/STATE.md", "tools/x.py"]


def test_GHI_khong_bat_buoc_them_DUNG_MOT_dong_chi_co_ngay_va_ly_do(so_tam):
    truoc = json.loads(so_tam.read_text(encoding="utf-8"))
    dong = st.ghi({"buoc": "BƯỚC 9999", "khong_bat_buoc_vi": LY_DO}, so=so_tam,
                  ngay="2026-10-09", cham_luat=_khong_cham)
    assert dong == {"ngay": "2026-10-09", "khong_bat_buoc_vi": LY_DO}
    sau = json.loads(so_tam.read_text(encoding="utf-8"))
    assert sau["soat"]["BƯỚC 9999"] == dong
    del sau["soat"]["BƯỚC 9999"]
    assert sau == truoc
    assert so_tam.read_text(encoding="utf-8").endswith("}\n")


def test_GHI_khong_bat_buoc_hoi_MAY_voi_DUNG_so_BUOC(so_tam):
    thay = []
    st.ghi({"buoc": "BƯỚC 9999", "khong_bat_buoc_vi": LY_DO}, so=so_tam,
           ngay="2026-10-09", cham_luat=lambda n: thay.append(n) or [])
    assert thay == [9999], thay


@pytest.mark.parametrize("ten, muc, cham", [
    ("cham file luat", {"buoc": "BƯỚC 9999", "khong_bat_buoc_vi": LY_DO},
     ["CLAUDE.md"]),
    ("truoc moc thu hep", {"buoc": "BƯỚC 163", "khong_bat_buoc_vi": LY_DO}, []),
    ("ten khong phai BUOC", {"buoc": "ĐO 5", "khong_bat_buoc_vi": LY_DO}, []),
    ("da co trong so", {"buoc": "BƯỚC 164", "khong_bat_buoc_vi": LY_DO}, []),
    ("ly do ngan", {"buoc": "BƯỚC 9999", "khong_bat_buoc_vi": "ngan"}, []),
    ("kem cau_hoi (nuoc doi)", {"buoc": "BƯỚC 9999", "khong_bat_buoc_vi": LY_DO,
                                "cau_hoi": "x"}, []),
])
def test_GHI_khong_bat_buoc_tu_choi_va_KHONG_cham_file(so_tam, ten, muc, cham):
    truoc = so_tam.read_bytes()
    with pytest.raises(st.TuChoi):
        st.ghi(muc, so=so_tam, ngay="2026-10-09", cham_luat=lambda n: cham)
    assert so_tam.read_bytes() == truoc, ten


def test_GHI_khong_bat_buoc_tu_choi_ly_do_dan_lai_tu_BUOC_khac(so_tam):
    st.ghi({"buoc": "BƯỚC 9998", "khong_bat_buoc_vi": LY_DO}, so=so_tam,
           ngay="2026-10-09", cham_luat=_khong_cham)
    truoc = so_tam.read_bytes()
    with pytest.raises(st.TuChoi, match="9998"):
        st.ghi({"buoc": "BƯỚC 9999", "khong_bat_buoc_vi": LY_DO.upper()}, so=so_tam,
               ngay="2026-10-09", cham_luat=_khong_cham)
    assert so_tam.read_bytes() == truoc


def test_GHI_khong_bat_buoc_tu_choi_khi_so_thieu_moc_thu_hep(so_tam):
    d = json.loads(so_tam.read_text(encoding="utf-8"))
    del d["_moc_chi_hoi_khi_doi_luat"]
    so_tam.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(st.TuChoi, match="moc"):
        st.ghi({"buoc": "BƯỚC 9999", "khong_bat_buoc_vi": LY_DO}, so=so_tam,
               ngay="2026-10-09", cham_luat=_khong_cham)


def test_GHI_khong_bat_buoc_BUOC_dung_bang_moc_thi_NHAN_BUOC_ngay_duoi_moc_thi_TU_CHOI(so_tam):
    """Biên của mốc: `n < moc` chứ không `n <= moc` (đột biến T1, lô B). Dời mốc của
    sổ tạm lên 9990 để BƯỚC bằng mốc chưa có sẵn trong sổ."""
    d = json.loads(so_tam.read_text(encoding="utf-8"))
    d["_moc_chi_hoi_khi_doi_luat"] = 9990
    so_tam.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(st.TuChoi, match="moc"):
        st.ghi({"buoc": "BƯỚC 9989", "khong_bat_buoc_vi": LY_DO}, so=so_tam,
               ngay="2026-10-09", cham_luat=_khong_cham)
    dong = st.ghi({"buoc": "BƯỚC 9990", "khong_bat_buoc_vi": LY_DO}, so=so_tam,
                  ngay="2026-10-09", cham_luat=_khong_cham)
    assert dong["khong_bat_buoc_vi"] == LY_DO


def test_GHI_dung_duong_hoi_that_khi_khong_co_o_khong_bat_buoc(so_tam):
    """Hai đường tách bạch: mục có `phat_hien` không bị nhánh mới nuốt."""
    dong = st.ghi(_muc_tot(), so=so_tam, ngay="2026-10-09",
                  cham_luat=lambda n: pytest.fail("duong hoi that khong duoc hoi may git"))
    assert "khong_bat_buoc_vi" not in dong and dong["phat_hien"]


def _the(phan_quyet):
    return {"cau_hoi": "c", "phat_hien": [{"phan_quyet": phan_quyet}]}


def test_DEM_hoi_that_dem_MUC_khong_dem_phat_hien_va_bo_o_khong_hoi():
    so = {"BƯỚC 10": _the("THẬT. ok"),
          "BƯỚC 11": {"cau_hoi": "c", "phat_hien": [{"phan_quyet": "THẬT. a"},
                                                    {"phan_quyet": "THẬT. b"}]},
          "BƯỚC 12": _the("SAI. x"),
          "BƯỚC 13": {"cau_hoi": "c", "phat_hien": [], "khong_tim_thay_gi": True},
          "BƯỚC 14": {"khong_bat_buoc_vi": "ly do"},
          "BƯỚC 15": {"khong_soat_vi": "ly do cu"},
          "BƯỚC 16": {"cau_hoi": "   ", "phat_hien": [{"phan_quyet": "THẬT."}]},
          "ĐO 5": _the("THẬT."),
          "BƯỚC 70-73": _the("THẬT.")}
    assert st.dem_hoi_that(so, 10, 16) == (4, 2)         # 10, 11, 12, 13 đã hỏi; THẬT: 10, 11
    assert st.dem_hoi_that(so, 70, 70) == (1, 1)         # mục gộp tính theo số ĐẦU


def test_DEM_hoi_that_bien_hai_dau_la_BAO_GOM():
    so = {f"BƯỚC {n}": _the("THẬT.") for n in (9, 10, 11, 12, 13)}
    assert st.dem_hoi_that(so, 10, 12) == (3, 3)
    assert st.dem_hoi_that(so, 10, 10) == (1, 1)
    assert st.dem_hoi_that(so, 14, 20) == (0, 0)


def test_DEM_CLI_so_that_cua_BUOC_1_den_129_la_25_tren_30():
    """Số đã dùng làm lý do nới Quy tắc 3 (LO-TRINH.md). Sổ chỉ-thêm nên số này đứng yên."""
    r = subprocess.run(
        [sys.executable, str(GOC / "tools" / "so_tay.py"), "dem", "--tu", "1", "--den", "129"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    assert r.returncode == 0, r.stderr
    assert "30 muc da HOI THAT" in r.stdout and "25 muc co phan quyet THẬT" in r.stdout, r.stdout
    assert "(25/30)" in r.stdout and "BƯỚC 1-129" in r.stdout, r.stdout
