"""Gác của `tools/so_tay.py` — dựng câu hỏi và ghi sổ soát chéo (BƯỚC 130).

Phép kiểm đáng tin nhất ở đây là phép đi qua CA THẬT đã biết trước: khuôn
câu hỏi phải dựng lại được BYTE-CHO-BYTE câu hỏi BƯỚC 129 đã gửi thật, đọc
từ chính sổ. Một khuôn "trông giống" mà không tái lập được câu thật là một
khuôn khác.
"""
import importlib.util
import json
import re
import shutil
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
    p = tmp_path / "soat-notebooklm.json"
    shutil.copyfile(GOC / "docs" / "soat-notebooklm.json", p)
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
