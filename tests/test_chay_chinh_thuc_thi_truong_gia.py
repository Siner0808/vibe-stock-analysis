"""Dụng cụ lượt chạy CHÍNH THỨC của C4 (BƯỚC 295): `tools/chay_chinh_thuc_thi_truong_gia.py` và ĐO 37.

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 6 và 8 ("Lát 5"); bảng đã ký ở `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 37.

Bốn nhóm phép thử:

* CỬA — dòng hạt 2, 3, 4 chỉ mở qua `kiem_cong`; thiếu MỘT điều thì không sinh thị trường nào và in HẾT các điều thiếu. Cửa nhận git
  TIÊM VÀO nên mọi ca (ĐO 37 chưa có ở `origin/main`, lệnh không được nêu, tiêu chí bị sửa sau khi ký, file ghim lệch, đã chạy xong…)
  được dựng bằng văn bản giả, KHÔNG phụ thuộc trạng thái git thật (nếu không, test sẽ đổi màu ngay khi PR này merge).
  Không test nào sinh dòng hạt 2, 3, 4, 5: bộ sinh bị buộc nổ khi test gọi `main` qua cửa.
* ĐỌC KẾT CỤC — từng tiêu chí của mục 6 ở ĐÚNG hai bên ngưỡng (ĐẠT một đơn vị trước biên, TRƯỢT một đơn vị sau), KHÔNG ĐỌC ĐƯỢC
  thắng TRƯỢT, bootstrap C2 tất định, kiểm C1 bắt đúng từng khoản 1–4 trên một chuỗi THẬT (dòng thử 9001).
* LUỒNG CHẠY — `chay_luong` ghi từng đợt, chạy tiếp không chọn lại, tái lập bit, P4 một lần; một lượt thử thật (Tầng 1, dòng 9001).
* GÁC — AST: mọi hàm gọi bộ sinh gọi cửa TRƯỚC, `PhepChay` chỉ dựng ở `kiem_cong`, một chỗ ghi file, không chuỗi của thế giới thật,
  và các dụng cụ KHÁC vẫn chặn dòng 2–5.

Tests pin giá trị của ĐO 37 đọc chúng từ bản ghi JSON của dòng 1, không gõ số.
"""
import ast
import copy
import importlib.util
import json
import os
import pickle
import re
import subprocess
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import cham_xac_nhan as cx  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402
import vong_hoc_gia as V  # noqa: E402

DUONG_TOOL = GOC / "tools" / "chay_chinh_thuc_thi_truong_gia.py"
_spec = importlib.util.spec_from_file_location("chay_chinh_thuc_thi_truong_gia", DUONG_TOOL)
CT = importlib.util.module_from_spec(_spec)
sys.modules["chay_chinh_thuc_thi_truong_gia"] = CT
_spec.loader.exec_module(CT)

HIEU_CHUAN = json.loads((GOC / "docs" / "thi-truong-gia-hieu-chuan.json").read_text(encoding="utf-8"))
G_PHAY = json.loads((GOC / "docs" / "thi-truong-gia-g-phay.json").read_text(encoding="utf-8"))
LUONG_TEST = 9001
TEN_F = sorted(T.ho_spec_f())
TEN_12 = sorted(T.ho_spec_oracle())
KAPPA_2X = CT.doc_kappa_muc(2.0)


# ══ CỬA ═══════════════════════════════════════════════════════════════════════════════════════════════════

def _van_ban_do37(luong=(2, 3, 4), lenh=True, ke_hoach=True, sau="## ĐO 38 — mục sau\n\nthân sau\n") -> str:
    """Văn bản `docs/TIEU-CHI-DOC-TRUOC.md` giả, có ĐO 36, ĐO 37 và (tuỳ) ĐO 38."""
    than = "## ĐO 37 — ký bảng\n\n"
    for l in luong:
        if lenh:   # lệnh nằm trong khối mã, xuống dòng giữa chừng: chuẩn hoá khoảng trắng phải xử lý được
            than += f"```\n./.venv/Scripts/python.exe -X utf8 {CT.lenh_chuan(l).replace(' --luong', chr(10) + '  --luong')} --so-tien-trinh 12\n```\n"
        if ke_hoach:
            than += CT.dong_ke_hoach(l) + "\n\n"
    return "# Tiêu chí\n\n## ĐO 36 — cũ\n\nthân cũ " + CT.lenh_chuan(2) + "\n\n" + than + sau


def _git_gia(van_main, *, fetch=0, ancestor=0, diff=0, head="a" * 40, goc="b" * 40):
    """`git` giả. `diff` là mã thoát chung hay hàm (đường → mã)."""
    nhat_ky = []

    def git(*a):
        nhat_ky.append(a)
        if a[0] == "fetch":
            return fetch, ""
        if a[0] == "show":
            return (0, van_main) if van_main is not None else (128, "")
        if a[0] == "merge-base":
            return ancestor, ""
        if a[0] == "diff":
            return (diff(a[-1]) if callable(diff) else diff), ""
        if a[0] == "rev-parse":
            return 0, (head if a[1] == "HEAD" else goc) + "\n"
        raise AssertionError(a)
    git.nhat_ky = nhat_ky
    return git


def _cong_ok(luong=2, **kw):
    van = _van_ban_do37()
    return CT.kiem_cong(luong, git=_git_gia(van), ket_qua_hien_co=kw.pop("ket_qua_hien_co", None), van_ban_cay=kw.pop("van_ban_cay", van), **kw)


def test_cua_cho_qua_khi_do37_o_origin_main_neu_lenh_va_ke_hoach_cay_bang_main_va_khong_file_ghim_lech():
    for l in CT.LUONG_CHINH_THUC:
        phep = _cong_ok(l)
        assert isinstance(phep, CT.PhepChay) and phep.luong == l and phep.hop_le()
        assert phep.head == "a" * 40 and phep.goc_main == "b" * 40
        CT.kiem_luong_chinh_thuc(l, phep)


def test_cua_TU_CHOI_khi_origin_main_chua_co_do37_va_khong_sinh_gi():
    """Đúng tình huống của nhánh này TRƯỚC khi ĐO 37 vào `main`: ĐO 36 là mục cuối."""
    van = "# T\n\n## ĐO 36 — cũ\n\nthân " + CT.lenh_chuan(2) + "\n"
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van)
    assert any("khong co muc '## ĐO 37" in s for s in e.value.ly_do)


GOC_NHANH = "64ec66b"     # `origin/main` lúc BƯỚC 295 bắt đầu (PR #340 đã merge); mục ĐO cuối của file lúc ấy là ĐO 36


def test_cua_TU_CHOI_voi_VAN_BAN_THAT_cua_origin_main_luc_nhanh_nay_bat_dau_ca_ba_dong_hat():
    """Cùng ca với test trên nhưng văn bản KHÔNG dựng tay: là `docs/TIEU-CHI-DOC-TRUOC.md` thật ở cây `64ec66b`. Bất biến theo thời gian
    (một commit không đổi), nên không đổi màu khi PR này merge. Clone nông không có commit ấy thì bỏ qua, không đỏ."""
    r = subprocess.run(["git", "show", f"{GOC_NHANH}:docs/TIEU-CHI-DOC-TRUOC.md"], cwd=str(GOC), capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        pytest.skip(f"khong co commit {GOC_NHANH} (clone nong)")
    assert CT.cat_muc_do(r.stdout) is None and CT.cat_muc_do(r.stdout, 36) is not None
    for l in CT.LUONG_CHINH_THUC:
        with pytest.raises(CT.CongTu) as e:
            CT.kiem_cong(l, git=_git_gia(r.stdout), ket_qua_hien_co=None, van_ban_cay=r.stdout)
        assert any("khong co muc '## ĐO 37" in s for s in e.value.ly_do)


def test_cua_khong_nham_ĐO_370_hay_37b_la_ĐO_37():
    for tieu in ("## ĐO 370 — x", "## ĐO 37b — x", "## ĐO 3 — x", "### ĐO 37 — x"):
        assert CT.cat_muc_do(f"# T\n\n{tieu}\n\nthân\n") is None, tieu
    assert CT.cat_muc_do("## ĐO 37 — a\n\nb\n\n## ĐO 38 — c\n\nd\n") == "## ĐO 37 — a\n\nb\n\n"


def test_cua_TU_CHOI_khi_do37_khong_neu_lenh_hay_dong_ke_hoach_cua_chinh_dong_hat_do():
    with pytest.raises(CT.CongTu) as e:
        van = _van_ban_do37(luong=(3, 4))          # nêu dòng 3, 4 nhưng KHÔNG nêu dòng 2
        CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van)
    assert len(e.value.ly_do) == 2                  # thiếu lệnh VÀ thiếu dòng kế hoạch: nêu hết cả hai
    for ten, kw in (("lệnh", {"lenh": False}), ("kế hoạch", {"ke_hoach": False})):
        van = _van_ban_do37(**kw)
        with pytest.raises(CT.CongTu) as e:
            CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van)
        assert len(e.value.ly_do) == 1, (ten, e.value.ly_do)


def test_cua_lenh_chi_nhan_trong_do37_khong_nhan_o_do_khac():
    """ĐO 36 nêu lệnh dòng 2 (do `_van_ban_do37` cố ý đặt) mà ĐO 37 không nêu → vẫn từ chối."""
    van = _van_ban_do37(luong=(3, 4))
    assert CT.chuan_hoa(CT.lenh_chuan(2)) in CT.chuan_hoa(van)
    with pytest.raises(CT.CongTu):
        CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van)


def test_cua_TU_CHOI_khi_do37_o_cay_lam_viec_khac_ban_o_origin_main():
    van = _van_ban_do37()
    sua = van.replace("ký bảng", "ký bảng (đã sửa)")
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=sua)
    assert any("cay lam viec khac" in s for s in e.value.ly_do)
    # đổi khoảng trắng thì KHÔNG phải là đổi tiêu chí
    CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=None, van_ban_cay=van.replace("\n\n", "\n\n\n"))


def test_cua_TU_CHOI_khi_fetch_hong_khong_phai_to_tien_hay_file_ghim_lech():
    van = _van_ban_do37()
    for ten, git, khoa in (("fetch", _git_gia(van, fetch=1), "git fetch"),
                           ("to tien", _git_gia(van, ancestor=1), "to tien"),
                           ("ghim", _git_gia(van, diff=lambda f: 1 if f == "thi_truong_gia.py" else 0), "thi_truong_gia.py")):
        with pytest.raises(CT.CongTu) as e:
            CT.kiem_cong(4, git=git, ket_qua_hien_co=None, van_ban_cay=van)
        assert any(khoa in s for s in e.value.ly_do), (ten, e.value.ly_do)


def test_cua_in_HET_cac_dieu_thieu_khong_dung_o_dieu_dau():
    git = _git_gia(None, fetch=1, ancestor=1, diff=1)
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(3, git=git, ket_qua_hien_co=None, van_ban_cay="")
    assert len(e.value.ly_do) >= 3 + len(CT.FILE_GHIM) - 0 and len(e.value.ly_do) == 2 + len(CT.FILE_GHIM) + 1


def test_cua_moi_dong_ghim_phai_la_file_git_biet():
    biet = set(subprocess.run(["git", "ls-files"], cwd=str(GOC), capture_output=True, text=True).stdout.split())
    assert [f for f in CT.FILE_GHIM if f not in biet] == []
    assert CT.TEN_DUNG_CU in CT.FILE_GHIM and "thi_truong_gia.py" in CT.FILE_GHIM


def test_cua_mot_lan_xong_thi_chan_dang_do_thi_can_tiep_tuc():
    van = _van_ban_do37()
    xong = {"cac_luong": {"2": {"trang_thai": "XONG"}}}
    do = {"cac_luong": {"2": {"trang_thai": "DANG CHAY"}}}
    for _ in range(2):   # --tiep-tuc không cứu được dòng đã XONG
        with pytest.raises(CT.CongTu) as e:
            CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=xong, van_ban_cay=van, tiep_tuc=True)
        assert any("DA chay xong" in s for s in e.value.ly_do)
    with pytest.raises(CT.CongTu) as e:
        CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=do, van_ban_cay=van)
    assert any("--tiep-tuc" in s for s in e.value.ly_do)
    assert CT.kiem_cong(2, git=_git_gia(van), ket_qua_hien_co=do, van_ban_cay=van, tiep_tuc=True).hop_le()
    # dòng 3 chưa có bản ghi thì dòng 2 xong không chặn nó
    assert CT.kiem_cong(3, git=_git_gia(van), ket_qua_hien_co=xong, van_ban_cay=van).hop_le()


@pytest.mark.parametrize("luong", [1, 5, 6, 0, -2, 9000, 22, "2", 2.0, None, True, False])
def test_kiem_cong_nổ_voi_moi_dong_ngoai_2_3_4_ke_ca_5(luong):
    with pytest.raises(CT.CongTu):
        CT.kiem_cong(luong, git=_git_gia(_van_ban_do37()), ket_qua_hien_co=None)


@pytest.mark.parametrize("luong", [1, 5, 6, 0, -2, 9000, "2", 2.0, None, True, False])
def test_kiem_luong_chinh_thuc_nổ_voi_moi_dong_la_va_dong_5_khong_bao_gio_mo(luong):
    phep = _cong_ok(2)
    with pytest.raises((ValueError, CT.CongTu)):
        CT.kiem_luong_chinh_thuc(luong, phep)
    with pytest.raises(ValueError):
        CT.kiem_luong_chinh_thuc(5, phep)              # dòng 5 nổ ngay cả khi có giấy phép hợp lệ của dòng khác


def test_kiem_luong_chinh_thuc_nhan_9001_tu_do_va_nhan_kieu_numpy():
    CT.kiem_luong_chinh_thuc(9001)
    CT.kiem_luong_chinh_thuc(np.int64(9001))
    phep = _cong_ok(3)
    CT.kiem_luong_chinh_thuc(np.int64(3), phep)


def test_dong_2_3_4_nổ_khong_giay_phep_hay_giay_phep_sai_dong_hay_gia_mao():
    ph2, ph3 = _cong_ok(2), _cong_ok(3)
    for l in CT.LUONG_CHINH_THUC:
        with pytest.raises(CT.CongTu):
            CT.kiem_luong_chinh_thuc(l)
        with pytest.raises(CT.CongTu):
            CT.kiem_luong_chinh_thuc(l, "co")
    with pytest.raises(CT.CongTu):
        CT.kiem_luong_chinh_thuc(2, ph3)                                        # phép của dòng khác
    gia = CT.PhepChay(2, ph2.sha_do, ph2.head, ph2.goc_main, "0" * 64)          # tem sai
    with pytest.raises(CT.CongTu):
        CT.kiem_luong_chinh_thuc(2, gia)
    doi = dict(ph2.__dict__, head="c" * 40)                                      # đổi một trường, giữ tem
    with pytest.raises(CT.CongTu):
        CT.kiem_luong_chinh_thuc(2, CT.PhepChay(**doi))
    gia5 = CT.PhepChay(5, "x", "y", "z", CT._tem(5, "x", "y", "z"))              # tem ĐÚNG nhưng dòng 5
    assert not gia5.hop_le()
    with pytest.raises(ValueError):
        CT.kiem_luong_chinh_thuc(5, gia5)


def test_giay_phep_di_qua_pickle_sang_tien_trinh_con_va_van_hop_le():
    ph = _cong_ok(4)
    ph2 = pickle.loads(pickle.dumps(ph))
    assert ph2 == ph and ph2.hop_le()
    CT.kiem_luong_chinh_thuc(4, ph2)


def _bo_sinh_phai_no(monkeypatch):
    """Mọi cửa vào bộ sinh và vòng NỔ: test nào lọt tới đây là test đã sinh một thị trường."""
    def no(*a, **k):
        raise AssertionError("MOT THI TRUONG DA DUOC SINH")
    for mod, ten in ((T, "sinh_thi_truong"), (T, "sinh_null"), (T, "tinh_su_that"), (T, "_sinh_loi"), (G, "sinh_thi_truong_2"),
                     (G, "_sinh_ohlcv_loi"), (G, "cham_diem_theo_ma"), (V, "chay_vong"), (cx, "cham")):
        monkeypatch.setattr(mod, ten, no)
    monkeypatch.setattr(CT, "ghi_ket_qua", no)


def test_main_dong_2_3_4_BI_TU_CHOI_o_trang_thai_cua_nhanh_nay_va_KHONG_sinh_thi_truong_nao(monkeypatch, capsys, tmp_path):
    """`origin/main` chưa có ĐO 37 (như nhánh này lúc làm việc): mã thoát 3, in lý do, không bộ sinh, không file."""
    _bo_sinh_phai_no(monkeypatch)
    van = "# T\n\n## ĐO 36 — cũ\n\nthân\n"
    monkeypatch.setattr(CT, "git_that", _git_gia(van))
    monkeypatch.setattr(CT, "DUONG_KET_QUA", tmp_path / "ket-qua.json")
    monkeypatch.setattr(CT, "doc_ket_qua_hien_co", lambda duong=None: None)
    for l in ("2", "3", "4"):
        assert CT.main(["--luong", l, "--so-tien-trinh", "12"]) == 3
        err = capsys.readouterr().err
        assert "CỬA TỪ CHỐI" in err and "ĐO 37" in err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("luong", ["1", "5", "6", "9000"])
def test_main_tu_choi_dong_ngoai_2_3_4_va_9001(luong, monkeypatch):
    _bo_sinh_phai_no(monkeypatch)
    assert CT.main(["--luong", luong]) == 2


def test_main_dong_thu_phai_co_tang_va_ra_va_khong_duoc_ghi_ra_file_chinh_thuc(monkeypatch):
    _bo_sinh_phai_no(monkeypatch)
    for tham in (["--luong", "9001"], ["--luong", "9001", "--tang", "1"], ["--luong", "9001", "--ra", "x.json"],
                 ["--luong", "9001", "--tang", "1", "--ra", str(CT.DUONG_KET_QUA)]):
        with pytest.raises(SystemExit):
            CT.main(tham)


def test_main_ket_cuc_khong_co_file_tra_2_va_khong_sinh_gi(monkeypatch):
    _bo_sinh_phai_no(monkeypatch)
    monkeypatch.setattr(CT, "doc_ket_qua_hien_co", lambda duong=None: None)
    assert CT.main(["--ket-cuc"]) == 2


def test_cac_dung_cu_khac_van_chan_dong_2_3_4_5_va_khong_dung_cu_nao_nhap_dung_cu_chinh_thuc():
    cu = {"chay_vong_thi_truong_gia", "hieu_chuan_thi_truong_gia", "oracle_tang2_thi_truong_gia", "chay_tang2_thi_truong_gia",
          "chay_vong_tang2_thi_truong_gia"}
    for ten in sorted(cu):
        duong = GOC / "tools" / f"{ten}.py"
        s = importlib.util.spec_from_file_location(ten + "_cua", duong)
        m = importlib.util.module_from_spec(s)
        sys.modules.setdefault(ten, m)
        s.loader.exec_module(m)
        for l in (2, 3, 4, 5):
            with pytest.raises(ValueError):
                m.kiem_luong(l)
        assert "chay_chinh_thuc" not in duong.read_text(encoding="utf-8")
    for duong in list(GOC.glob("*.py")) + list((GOC / "tools").glob("*.py")) + list((GOC / "tests").glob("*.py")):
        if duong.name in ("chay_chinh_thuc_thi_truong_gia.py", "test_chay_chinh_thuc_thi_truong_gia.py"):
            continue
        cay = ast.parse(duong.read_text(encoding="utf-8"))
        nhap = {a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names} | \
               {(n.module or "").split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
        assert "chay_chinh_thuc_thi_truong_gia" not in nhap, duong.name


# ══ KẾ HOẠCH ══════════════════════════════════════════════════════════════════════════════════════════════

def test_ke_hoach_khop_muc_6_ba_dong_hat_chi_so_roi_nhau_va_tranh_thi_truong_da_bi_oracle_nhin_o_lat_1():
    kh = CT.KE_HOACH
    assert sorted(kh) == [2, 3, 4] and tuple(sorted(kh)) == CT.LUONG_CHINH_THUC
    assert [(t, m, s) for t, m, _, s in kh[2]["o"]] == [("0.5x", 0.5, 400), ("1x", 1.0, 400), ("2x", 2.0, 400)] and kh[2]["tang"] == 1
    assert [(t, m, s) for t, m, _, s in kh[3]["o"]] == [("NULL", 0.0, 1000)] and kh[3]["tang"] == 1
    assert [(t, m, s) for t, m, _, s in kh[4]["o"]] == [("NULL", 0.0, 100), ("2x", 2.0, 100)] and kh[4]["tang"] == 2
    for l, k in kh.items():
        chi_so = [c for _, _, dau, so in k["o"] for c in range(dau, dau + so)]
        assert len(chi_so) == len(set(chi_so)), f"dong {l}: hai o dung chung chi so (chung so ngau nhien giua cac kappa)"
        assert min(chi_so) >= 1
    # mục 15 khoản 12: oracle đã nhìn dòng 2 chỉ số 1 (và dòng 5) ở Lát 1 → dòng 2 không dùng chỉ số 1
    assert 1 not in {c for _, _, dau, so in kh[2]["o"] for c in range(dau, dau + so)}
    assert all(muc in [m["he_so"] for m in HIEU_CHUAN["muc"]] for k in kh.values() for _, muc, _, _ in k["o"])


def test_lenh_chuan_va_dong_ke_hoach_sinh_tu_ke_hoach_khong_goi_tay():
    for l in CT.LUONG_CHINH_THUC:
        assert CT.lenh_chuan(l) == f"tools/chay_chinh_thuc_thi_truong_gia.py --luong {l}"
        d = CT.dong_ke_hoach(l)
        for ten, muc, dau, so in CT.KE_HOACH[l]["o"]:
            assert f"ô {ten} (mức {muc:g}× MDE80) chỉ số {dau}–{dau + so - 1}" in d
        assert f"Tầng {CT.KE_HOACH[l]['tang']}" in d
    assert "--so-tien-trinh" not in CT.lenh_chuan(2) and "--tiep-tuc" not in CT.lenh_chuan(2)


def test_danh_sach_viec_bo_qua_chi_so_da_co_va_khong_chon_lai():
    kh = {"tang": 1, "o": (("2x", 2.0, 10, 5), ("NULL", 0.0, 100, 3))}
    tat_ca = CT.danh_sach_viec(9001, None, 7, True, None, kh)
    assert [(v[3], v[5]) for v in tat_ca] == [("2x", c) for c in range(10, 15)] + [("NULL", c) for c in range(100, 103)]
    da = {"2x": {"thi_truong": [{"chi_so": 10}, {"chi_so": 12}]}}
    con = CT.danh_sach_viec(9001, None, 7, True, da, kh)
    assert [(v[3], v[5]) for v in con] == [("2x", 11), ("2x", 13), ("2x", 14)] + [("NULL", c) for c in range(100, 103)]
    assert all(v[6] == 7 and v[7] is True for v in con)


# ══ ĐỌC KẾT CỤC ═══════════════════════════════════════════════════════════════════════════════════════════

PHI = 0.6180339887498949


def _z_tat_dinh(k: int) -> float:
    """Chuẩn tất định (thứ tự thấp-lệch quanh phân vị): ra sd ≈ 1, trung bình ≈ 0, 95,4% trong 2."""
    u = ((k + 0.5) * PHI) % 1.0
    return NormalDist().inv_cdf(min(max(u, 1e-4), 1 - 1e-4))


def _oracle(i: int, *, z_he_so=1.0, g_delta=None, se=0.004):
    spec = {}
    for j, ten in enumerate(TEN_12):
        spec[ten] = [z_he_so * _z_tat_dinh(i * len(TEN_12) + j) * se, se]
    if g_delta is not None:
        spec[T.TEN_SPEC_G] = [g_delta, se]
    return {"top_f": T.TEN_SPEC_G, "spec": spec}


def _tt(p_alarm=False, qua=False):
    return {"tt": "QUA" if qua else ("THUA" if p_alarm else "DANG CHAM"), "p": 1e-4 if (qua or p_alarm) else 0.4, "delta": 0.1, "n_phien": 252, "n_ma": 60}


def _chuoi(khai=(), nang=False, tien=0.05, du=True, c1=()):
    return {"khai": list(khai), "ket_cuc": V.KET_CUC_NANG_CAP if nang else V.KET_CUC_KHONG_NANG_CAP, "trang_thai": {},
            "doc": [], "tien": {"delta_ic": tien, "du_cua_so": du, "n_phien": 126} if nang else None, "c1": list(c1)}


NG = 0.05 / 3


def _o1(n, *, tim_ra=0, g_qua=0, z_alarm=0, h_qua=0, g_khai=0, b1=0, nang=0, c1=0, g_delta=None, z_he_so=1.0, tien=0.05):
    """`n` thị trường Tầng 1. Mỗi chỉ tiêu là SỐ thị trường (các nhóm lấy từ đầu danh sách, nên chồng nhau theo ý muốn)."""
    ra = []
    for i in range(n):
        gd = (0.001 if i % 2 == 0 else -0.001) if g_delta == "luan_phien" else g_delta      # trung bình đúng 0 mà vẫn có phương sai
        orc = _oracle(i, z_he_so=z_he_so, g_delta=gd)
        if i < tim_ra:
            orc["top_f"], khai = T.TEN_SPEC_G, [T.TEN_SPEC_G]
        else:
            orc["top_f"], khai = "bo_risk_score", ([T.TEN_SPEC_G] if i < g_khai else ["mono_trend_score"])
        ra.append({"chi_so": i + 1, "dg": "x", "nguong": NG,
                   "bo_ba": {"G": _tt(qua=i < g_qua), "Z": _tt(p_alarm=i < z_alarm), "H": _tt(qua=i < h_qua) if h_qua else _tt()},
                   "chuoi": _chuoi(khai, nang=i < nang, tien=tien, c1=["khoan 1"] if i < c1 else ()), "oracle": orc})
    for i in range(b1):                         # b1: số thị trường có báo động bằng G THUA (không QUA), để tách khỏi g_qua
        ra[-1 - i]["bo_ba"]["G"] = _tt(p_alarm=True)
    return ra


def _o2(n, *, g_qua=0, null_alarm=0, p3=None, c1=0, p1=0, p2=0, dq=0, z_alarm=0, h_qua=0):
    ra = []
    for i in range(n):
        ra.append({"chi_so": i + 1, "dg_sinh": "x", "dg": "x", "nguong": NG,
                   "bo_ba": {"Gp": _tt(qua=i < g_qua), "Z": _tt(p_alarm=i < z_alarm), "H": _tt(qua=i < h_qua)},
                   "p1": {"so_vi_pham": 1 if i < p1 else 0, "vi_pham_dau": [], "dq_khong_ok": dq if i == 0 else 0, "so_dong": 36300},
                   "p2": {"so_khac": 1 if i < p2 else 0, "so_diem_lech": 0, "so_lenh_that": 5, "so_lenh_phat": 5, "bi_chan_vni": 1, "so_diem_so_duoc": 36300},
                   "p3": {"ic_volume": 0.1 if (p3 is None or i < p3) else -0.01, "so_cap": 1},
                   "chuoi": _chuoi(c1=["khoan 2"] if i < c1 else ())})
    for i in range(null_alarm):
        ra[-1 - i]["bo_ba"]["Z"] = _tt(p_alarm=True)
    return ra


def _ket_dat(**ghi_de):
    """Bản ghi ba dòng hạt thoả MỌI tiêu chí (một đơn vị trong ngưỡng) và mọi kiểm máy đo."""
    muc = {m["he_so"]: m["muc_tieu_delta_ic"] for m in HIEU_CHUAN["muc"]}
    n = CT.NGUONG
    lo, hi = HIEU_CHUAN["kiem_1x_trong_dai_99"]["dai_99_quanh_80"]
    o = {
        "x05": _o1(400, g_delta=muc[0.5]), "x1": _o1(400, g_qua=lo + 1, g_delta=muc[1.0]),
        "x2": _o1(400, tim_ra=n["A"], g_qua=n["B2"], z_alarm=n["B3"], g_delta=muc[2.0], nang=300),
        "n3": _o1(1000, g_khai=n["A0"], nang=n["C3"], g_delta="luan_phien"),
        "n4": _o2(100, null_alarm=n["PT_NULL"]), "x4": _o2(100, g_qua=G_PHAY["dai_thap"], p3=n["P3"]),
    }
    for i in range(n["B1"]):
        o["n3"][-1 - i]["bo_ba"]["Z"] = _tt(p_alarm=True)
    o.update(ghi_de)

    def cell(l):
        return {"thi_truong": o[l], "tai_lap": "KHOP"}
    return {"cac_luong": {
        "2": {"trang_thai": "XONG", "o": {"0.5x": cell("x05"), "1x": cell("x1"), "2x": cell("x2")}},
        "3": {"trang_thai": "XONG", "o": {"NULL": cell("n3")}},
        "4": {"trang_thai": "XONG", "o": {"NULL": cell("n4"), "2x": cell("x4")},
              "p4": {"lenh": "pytest", "ma_thoat": 0, "dong_cuoi": "ok"}}}}


def _doc(ket):
    return CT.tong_hop(ket, HIEU_CHUAN, G_PHAY)


def test_nen_DAT_du_moi_tieu_chi_o_sat_bien_dung_phia_va_khong_KHONG_DOC_DUOC():
    kc = _doc(_ket_dat())
    assert kc["khong_doc"] == [] and kc["truot"] == [] and kc["ket_cuc"] == "DAT", (kc["truot"], kc["khong_doc"])
    assert sorted(kc["tieu_chi"]) == sorted(["A", "A0", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "P1", "P2", "P3", "P4", "PT"])
    n = CT.NGUONG
    tc = kc["tieu_chi"]
    assert (tc["A"]["gia_tri"], tc["A0"]["gia_tri"], tc["B1"]["gia_tri"], tc["B2"]["gia_tri"], tc["B3"]["gia_tri"]) == \
           (n["A"], n["A0"], n["B1"], n["B2"], n["B3"])
    assert tc["C3"]["gia_tri"] == n["C3"] and tc["P3"]["gia_tri"] == n["P3"] and tc["PT"]["gia_tri"]["bao_dong_NULL"] == n["PT_NULL"]
    assert tc["PT"]["gia_tri"]["Gp_QUA_2x"] == G_PHAY["dai_thap"]
    assert tc["C2"]["dat"] and tc["C2"]["n"] == 300


def test_NGUONG_khop_bang_muc_6_cua_dac_ta_tung_dong():
    van = (GOC / "docs" / "thiet-ke-c4-thi-truong-gia.md").read_text(encoding="utf-8")
    hang = {m.group(1): m.group(0) for m in re.finditer(r"^\| \*\*([A-Z0-9]+)\*\* \|.*$", van, re.M)}
    n = CT.NGUONG
    assert f"≥ {n['A']} (80%)" in hang["A"] and f"≤ {n['A0']} (31,7%)" in hang["A0"] and f"≤ {n['B1']} (7,5%)" in hang["B1"]
    assert f"≥ {n['B2']} (90%)" in hang["B2"] and f"≤ {n['B3']} (5%)" in hang["B3"] and f"≤ {n['C3']} (5%)" in hang["C3"]
    assert f"≥ {n['P3']}/100" in hang["P"] and f"≤ {n['PT_NULL']}/100" in hang["PT"]
    assert f"[{G_PHAY['dai_thap']} ; {G_PHAY['dai_cao']}]" in hang["PT"]
    assert "400" in hang["A"] and "1.000" in hang["A0"] and "100" in hang["P"]


def _p2_none(ra, i):
    """Một thị trường chưa chạy P2 (`p2` = None): P2 không được đọc là 0 vi phạm (đột biến `p2 in (0, None)` sống sót ở BƯỚC 295)."""
    ra[i]["p2"] = None
    return ra


# (tên, tham số `_ket_dat`/ghi đè, tiêu chí phải TRƯỢT) — đều là MỘT đơn vị qua biên
def _truot_mot_don_vi():
    n = CT.NGUONG
    muc = {m["he_so"]: m["muc_tieu_delta_ic"] for m in HIEU_CHUAN["muc"]}
    lo, hi = HIEU_CHUAN["kiem_1x_trong_dai_99"]["dai_99_quanh_80"]
    x2 = dict(g_delta=muc[2.0], nang=300)
    return [
        ("A", {"x2": _o1(400, tim_ra=n["A"] - 1, g_qua=n["B2"], z_alarm=n["B3"], **x2)}, "A"),
        ("B2", {"x2": _o1(400, tim_ra=n["A"], g_qua=n["B2"] - 1, z_alarm=n["B3"], **x2)}, "B2"),
        ("B3", {"x2": _o1(400, tim_ra=n["A"], g_qua=n["B2"], z_alarm=n["B3"] + 1, **x2)}, "B3"),
        ("B4", {"x05": _o1(400, g_delta=muc[0.5], h_qua=1)}, "B4"),
        ("C1", {"x05": _o1(400, g_delta=muc[0.5], c1=1)}, "C1"),
        ("PT_null", {"n4": _o2(100, null_alarm=n["PT_NULL"] + 1)}, "PT"),
        ("PT_thap", {"x4": _o2(100, g_qua=G_PHAY["dai_thap"] - 1, p3=n["P3"])}, "PT"),
        ("PT_cao", {"x4": _o2(100, g_qua=G_PHAY["dai_cao"] + 1, p3=n["P3"])}, "PT"),
        ("P3", {"x4": _o2(100, g_qua=G_PHAY["dai_thap"], p3=n["P3"] - 1)}, "P3"),
        ("P1", {"n4": _o2(100, null_alarm=n["PT_NULL"], p1=1)}, "P1"),
        ("P2", {"n4": _o2(100, null_alarm=n["PT_NULL"], p2=1)}, "P2"),
        ("P2_chua_chay", {"n4": _p2_none(_o2(100, null_alarm=n["PT_NULL"]), 7)}, "P2"),
        ("C1_tang2", {"x4": _o2(100, g_qua=G_PHAY["dai_thap"], p3=n["P3"], c1=1)}, "C1"),
    ]


@pytest.mark.parametrize("ten,ghi_de,phai_truot", _truot_mot_don_vi(), ids=[t[0] for t in _truot_mot_don_vi()])
def test_moi_tieu_chi_TRUOT_dung_mot_don_vi_qua_bien_va_chi_no_truot(ten, ghi_de, phai_truot):
    ket = _ket_dat()
    cc = ket["cac_luong"]
    gan = {"x05": ("2", "0.5x"), "x1": ("2", "1x"), "x2": ("2", "2x"), "n3": ("3", "NULL"), "n4": ("4", "NULL"), "x4": ("4", "2x")}
    for k, v in ghi_de.items():
        cc[gan[k][0]]["o"][gan[k][1]]["thi_truong"] = v
    kc = _doc(ket)
    assert kc["khong_doc"] == [], kc["khong_doc"]
    assert kc["truot"] == [phai_truot] and kc["ket_cuc"] == "TRUOT", (kc["truot"], kc["tieu_chi"][phai_truot])


def test_A0_B1_C3_qua_bien_mot_don_vi_o_NULL_dong_3():
    n = CT.NGUONG
    for ten, kw in (("A0", {"g_khai": n["A0"] + 1, "nang": n["C3"]}), ("C3", {"g_khai": n["A0"], "nang": n["C3"] + 1})):
        ket = _ket_dat()
        ket["cac_luong"]["3"]["o"]["NULL"]["thi_truong"] = _o1(1000, g_delta="luan_phien", **kw)
        for i in range(n["B1"]):
            ket["cac_luong"]["3"]["o"]["NULL"]["thi_truong"][-1 - i]["bo_ba"]["Z"] = _tt(p_alarm=True)
        kc = _doc(ket)
        assert kc["truot"] == [ten] and kc["khong_doc"] == [], (ten, kc["truot"], kc["khong_doc"])
    ket = _ket_dat()
    for i in range(n["B1"] + 1):
        ket["cac_luong"]["3"]["o"]["NULL"]["thi_truong"][-1 - i]["bo_ba"]["Z"] = _tt(p_alarm=True)
    kc = _doc(ket)
    assert kc["truot"] == ["B1"] and kc["khong_doc"] == []


def test_C2_truot_khi_nang_cap_cho_delta_am_hay_cua_so_khong_du_hay_it_hon_hai():
    ket = _ket_dat()
    x2 = ket["cac_luong"]["2"]["o"]["2x"]["thi_truong"]
    for m in x2:
        if m["chuoi"]["tien"]:
            m["chuoi"]["tien"]["delta_ic"] = -0.05
    kc = _doc(ket)
    assert kc["truot"] == ["C2"] and kc["tieu_chi"]["C2"]["dat"] is False
    ket = _ket_dat()
    for m in ket["cac_luong"]["2"]["o"]["2x"]["thi_truong"]:
        if m["chuoi"]["tien"]:
            m["chuoi"]["tien"]["du_cua_so"] = False
    assert _doc(ket)["tieu_chi"]["C2"]["n"] == 0 and "C2" in _doc(ket)["truot"]


def test_bootstrap_C2_tat_dinh_hat_0_5000_lan_can_duoi_phan_vi_2_5():
    d = [0.05, 0.02, 0.08, -0.01, 0.04, 0.06, 0.0, 0.03]
    a, b = CT.bootstrap_c2(d), CT.bootstrap_c2(list(d))
    assert a == b and a["n"] == 8 and abs(a["trung_binh"] - float(np.mean(d))) < 1e-15
    rng = np.random.default_rng(0)
    ky_vong = float(np.percentile(np.asarray(d)[rng.integers(0, 8, size=(5000, 8))].mean(axis=1), 2.5))
    assert a["can_duoi"] == ky_vong and CT.SO_BOOTSTRAP_C2 == 5000 and CT.HAT_BOOTSTRAP_C2 == 0
    assert CT.bootstrap_c2([0.01] * 20)["can_duoi"] == pytest.approx(0.01)
    assert CT.bootstrap_c2([0.01]) == {"n": 1, "trung_binh": 0.01, "can_duoi": None}
    assert CT.bootstrap_c2([]) == {"n": 0, "trung_binh": None, "can_duoi": None}
    assert CT.bootstrap_c2([-0.02, 0.01, -0.03, 0.02, -0.01, 0.0])["can_duoi"] < 0


def test_KHONG_DOC_DUOC_thang_TRUOT_va_moi_kiem_may_do_bat_dung_cho():
    muc = {m["he_so"]: m["muc_tieu_delta_ic"] for m in HIEU_CHUAN["muc"]}
    lo, hi = HIEU_CHUAN["kiem_1x_trong_dai_99"]["dai_99_quanh_80"]

    def doc_va_khong_doc(ket):
        kc = _doc(ket)
        return kc["ket_cuc"], kc["khong_doc"], kc["truot"]
    # 1. oracle ở NULL lệch tỷ lệ: z phóng 1,6 lần → sd > 1,5 và tỷ lệ trong 2 sai số < 0,85
    ket = _ket_dat()
    n3 = ket["cac_luong"]["3"]["o"]["NULL"]["thi_truong"]
    for i, m in enumerate(n3):
        m["oracle"] = _oracle(i, z_he_so=1.7, g_delta=0.001 if i % 2 == 0 else -0.001)
    kc, kd, tr = doc_va_khong_doc(ket)
    assert kc == "KHONG_DOC_DUOC" and any("NULL ngoai tieu chi ty le" in s for s in kd)
    # 2. ΔIC_true(G) lệch 11% ở một mức, 9% thì không
    for lech, co in ((-0.11, True), (-0.09, False), (0.11, True)):
        ket = _ket_dat()
        for m in ket["cac_luong"]["2"]["o"]["1x"]["thi_truong"]:
            m["oracle"]["spec"][T.TEN_SPEC_G][0] = muc[1.0] * (1 + lech)
        kc, kd, tr = doc_va_khong_doc(ket)
        assert (kc == "KHONG_DOC_DUOC") is co, (lech, kd)
    # 3. tái lập hạt không bằng bit
    ket = _ket_dat()
    ket["cac_luong"]["4"]["o"]["2x"]["tai_lap"] = "LECH"
    kc, kd, _ = doc_va_khong_doc(ket)
    assert kc == "KHONG_DOC_DUOC" and any("4/2x" in s for s in kd)
    # 4. bộ sinh Tầng 2 có dòng data_quality ≠ OK
    ket = _ket_dat(x4=_o2(100, g_qua=G_PHAY["dai_thap"], p3=CT.NGUONG["P3"], dq=1))
    assert doc_va_khong_doc(ket)[0] == "KHONG_DOC_DUOC"
    # 5. bắt G ở 1× ngoài dải 99%: lo − 1 và hi + 1 đều ngoài, lo và hi đều trong
    for n_qua, co in ((lo - 1, True), (lo, False), (hi, False), (hi + 1, True)):
        ket = _ket_dat()
        ket["cac_luong"]["2"]["o"]["1x"]["thi_truong"] = _o1(400, g_qua=n_qua, g_delta=muc[1.0])
        assert (doc_va_khong_doc(ket)[0] == "KHONG_DOC_DUOC") is co, n_qua
    # KHÔNG ĐỌC ĐƯỢC thắng TRƯỢT: cùng lúc trượt B3 và tái lập LECH
    ket = _ket_dat()
    ket["cac_luong"]["2"]["o"]["2x"]["thi_truong"] = _o1(400, tim_ra=CT.NGUONG["A"], g_qua=CT.NGUONG["B2"], z_alarm=CT.NGUONG["B3"] + 1,
                                                       g_delta=muc[2.0], nang=300)
    ket["cac_luong"]["3"]["o"]["NULL"]["tai_lap"] = "LECH"
    kc, kd, tr = doc_va_khong_doc(ket)
    assert kc == "KHONG_DOC_DUOC" and tr == ["B3"] and kd


def test_thieu_dong_hat_hay_dang_do_thi_KHONG_DOC_DUOC_khong_the_doc_ra_DAT():
    ket = _ket_dat()
    del ket["cac_luong"]["4"]
    kc = _doc(ket)
    assert kc["ket_cuc"] == "KHONG_DOC_DUOC" and kc["thieu"] == ["4"] and kc["tieu_chi"] == {}
    ket = _ket_dat()
    ket["cac_luong"]["3"]["trang_thai"] = "DANG CHAY"
    assert _doc(ket)["thieu"] == ["3"]
    assert _doc({"cac_luong": {}})["thieu"] == ["2", "3", "4"]


def test_P4_chua_chay_hay_do_thi_TRUOT_P4():
    ket = _ket_dat()
    ket["cac_luong"]["4"]["p4"]["ma_thoat"] = 1
    kc = _doc(ket)
    assert kc["truot"] == ["P4"]
    del ket["cac_luong"]["4"]["p4"]
    assert _doc(ket)["truot"] == ["P4"]


def test_bao_cao_khong_phan_duong_cong_B1_Z_H_tang2_va_delta_thuc_hien_NULL():
    ket = _ket_dat(x4=_o2(100, g_qua=G_PHAY["dai_thap"], p3=CT.NGUONG["P3"], z_alarm=60, h_qua=3))
    kc = _doc(ket)
    br = kc["bao_cao"]
    assert br["tang2_Z_H_2x"] == {"Z_bao_dong": 60, "H_QUA": 3, "H_bao_dong": 3, "R": 100}          # Z, H tầng 2: BÁO CÁO, không phán
    assert kc["ket_cuc"] == "DAT" and kc["truot"] == []
    assert br["duong_cong_2x"]["G_QUA"] == CT.NGUONG["B2"] and br["duong_cong_0.5x"]["R"] == 400
    assert br["B1_ty_le"] == CT.NGUONG["B1"] / 1000 and br["B1_thieu_nhay"] is False
    assert br["bat_G_1x"]["dai_99"] == HIEU_CHUAN["kiem_1x_trong_dai_99"]["dai_99_quanh_80"]
    assert br["delta_ic_thuc_hien_NULL"]["n"] == CT.NGUONG["C3"]


def test_thong_ke_may_do_null_tinh_dung_ty_le_sd_va_trung_binh():
    tm = [{"oracle": {"spec": {"a": [0.0, 1.0], "b": [1.0, 1.0], "c": [-3.0, 1.0], "d": [2.0, 1.0]}}}]
    s = CT.thong_ke_may_do_null(tm)
    assert s["so_o"] == 4 and s["ty_le_trong_2se"] == 0.5 and s["trung_binh_z"] == 0.0
    assert s["sd_z"] == pytest.approx(float(np.std([0, 1, -3, 2], ddof=1)))


def test_in_ket_cuc_noi_het_ket_cuc_tung_tieu_chi_va_ly_do():
    ket = _ket_dat(n4=_o2(100, null_alarm=CT.NGUONG["PT_NULL"] + 1))
    van = "\n".join(CT.in_ket_cuc(_doc(ket)))
    assert "KẾT CỤC: TRUOT" in van and "PT  TRƯỢT" in van and "TRƯỢT ở: PT" in van and "A   ĐẠT" in van


# ══ KIỂM C1 TRÊN MỘT CHUỖI THẬT ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def chuoi_that():
    """Thị trường 2× thật của dòng thử 9001 (chỉ số 2001): chuỗi này nâng cấp (đã đo ở dòng thử: `NANG_CAP`)."""
    tt = T.sinh_thi_truong(LUONG_TEST, 2001, KAPPA_2X, co_su_that=False)
    dong = tt.dong_quyet_dinh()
    vong = V.chay_vong(dong, tt.gia)
    return dong, list(tt.ngay), vong


def test_kiem_c1_cho_ra_rong_tren_chuoi_that_co_nang_cap(chuoi_that):
    dong, ngay, vong = chuoi_that
    assert vong["ket_cuc"] == V.KET_CUC_NANG_CAP, "mẫu thử phải là một chuỗi CÓ nâng cấp, không thì C1 không có gì để bắt"
    assert CT.kiem_c1(vong, dong, ngay) == []


def test_kiem_c1_bat_dung_tung_khoan_1_den_4_va_khong_bat_nham(chuoi_that):
    dong, ngay, vong = chuoi_that

    def sai(sua, dong_moi=None):
        v = copy.deepcopy(vong)
        sua(v)
        return CT.kiem_c1(v, dong if dong_moi is None else dong_moi, ngay)
    # khoản 1: nâng cấp khi trạng thái KHÔNG phải QUA
    def k1(v):
        v["doc"][-1]["trang_thai"] = "DANG CHAM"
    assert any("khoan 1" in s for s in sai(k1))
    # khoản 1 (chiều ngược): QUA mà không có phiên bản mới
    def k1b(v):
        v["so_phien_ban"]["phien_ban"] = v["so_phien_ban"]["phien_ban"][:1]
        v["doc"][-1]["nang_cap"] = False
    assert any("khoan 1" in s for s in sai(k1b))
    # khoản 2: spec phiên bản mới khác spec đã khai
    def k2(v):
        v["so_phien_ban"]["phien_ban"][-1]["spec"] = {"loai": "trong_so", "trong_so": {"trend_score": 1.0}}   # spec HỢP LỆ nhưng không phải spec đã khai
    assert any("khoan 2" in s for s in sai(k2))
    # khoản 3: hiệu lực tại phiên đọc (không phải phiên sau), và phiên đọc không khớp lần đọc
    def k3(v):
        v["so_phien_ban"]["phien_ban"][-1]["hieu_luc_tu_phien"] -= 1
    assert any("khoan 3" in s for s in sai(k3))
    def k3b(v):
        v["so_phien_ban"]["phien_ban"][-1]["phien_doc"] += 1
        v["so_phien_ban"]["phien_ban"][-1]["hieu_luc_tu_phien"] += 1
    assert any("khoan 3" in s for s in sai(k3b))
    # khoản 4: điểm ghi sau phiên hiệu lực khác int(tổ hợp) — dòng đầu vào bị đổi một điểm; và dòng TRƯỚC hiệu lực bị coi là phải giữ nguyên
    ban = vong["so_phien_ban"]["phien_ban"][-1]
    chi_so = {n[:10]: i for i, n in enumerate(ngay)}
    sau = next(i for i, r in enumerate(dong) if chi_so[r["signal_date"][:10]] >= ban["hieu_luc_tu_phien"])
    d2 = [dict(r) for r in dong]
    # đổi MỘT thành phần của một dòng sau hiệu lực: `ap_phien_ban` đọc thành phần mới, kiểm độc lập đọc cùng thành phần → vẫn đúng...
    # ... nên khoản 4 bị bắt bằng cách đổi KẾT QUẢ của ap_phien_ban: dựng một V.ap_phien_ban hỏng.
    goc = V.ap_phien_ban
    try:
        def hong(dong_, so_pb, ngay_):
            ra = [dict(r) for r in goc(dong_, so_pb, ngay_)]
            ra[sau]["score"] += 3
            return ra
        V.ap_phien_ban = hong
        assert any("khoan 4" in s for s in CT.kiem_c1(copy.deepcopy(vong), dong, ngay))
        def hong_truoc(dong_, so_pb, ngay_):
            ra = [dict(r) for r in goc(dong_, so_pb, ngay_)]
            ra[0]["score"] += 1                      # dòng 0 nằm TRƯỚC phiên hiệu lực: phải giữ nguyên
            return ra
        V.ap_phien_ban = hong_truoc
        assert any("khoan 4" in s for s in CT.kiem_c1(copy.deepcopy(vong), dong, ngay))
    finally:
        V.ap_phien_ban = goc
    assert CT.kiem_c1(vong, d2, ngay) == []          # bản gốc vẫn sạch sau mọi thử


def test_kiem_c1_cho_ra_rong_khi_khong_co_nang_cap_va_bat_phien_ban_ma_khong_lan_doc_nao(chuoi_that):
    dong, ngay, vong = chuoi_that
    v = copy.deepcopy(vong)
    v["so_phien_ban"] = V.so_phien_ban_dau()
    v["doc"] = []
    assert CT.kiem_c1(v, dong, ngay) == []
    v2 = copy.deepcopy(vong)
    v2["doc"] = []
    assert any("so phien ban moi" in s for s in CT.kiem_c1(v2, dong, ngay))


# ══ LUỒNG CHẠY ════════════════════════════════════════════════════════════════════════════════════════════

def _ban_ghi_gia(chi_so, tang=1):
    b = {"chi_so": chi_so, "dg": f"d{chi_so}", "dg_sinh": f"d{chi_so}", "giay": {"sinh": 0.1}}
    return b


def test_chay_luong_ghi_tung_dot_DANG_CHAY_roi_XONG_tai_lap_khop_va_chay_tiep_khong_chon_lai(monkeypatch, tmp_path):
    goi = []
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang1", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0: goi.append((ten, chi_so)) or _ban_ghi_gia(chi_so))
    monkeypatch.setattr(CT, "tai_lap_sinh", lambda luong, phep, tang, muc, chi_so: f"d{chi_so}")
    luu = []
    kh = {"tang": 1, "o": (("2x", 2.0, 10, 5), ("NULL", 0.0, 100, 3))}
    ra = tmp_path / "ket.json"

    def ghi(ket, duong):
        luu.append((ket["cac_luong"][str(LUONG_TEST)]["trang_thai"], sum(len(o["thi_truong"]) for o in ket["cac_luong"][str(LUONG_TEST)]["o"].values())))
        ra.write_text(json.dumps(ket), encoding="utf-8")
    ket = CT.chay_luong(LUONG_TEST, None, 1, False, 3, ra, kh, 50, True, lambda: None, "x", False, ghi)
    assert luu == [("DANG CHAY", 3), ("DANG CHAY", 6), ("XONG", 8)]
    cu = ket["cac_luong"][str(LUONG_TEST)]
    assert [m["chi_so"] for m in cu["o"]["2x"]["thi_truong"]] == [10, 11, 12, 13, 14] and cu["o"]["2x"]["tai_lap"] == "KHOP" and cu["o"]["NULL"]["tai_lap"] == "KHOP"
    assert sorted(goi) == sorted([("2x", c) for c in range(10, 15)] + [("NULL", c) for c in range(100, 103)])
    assert cu["o"]["2x"]["kappa"] == KAPPA_2X and cu["o"]["NULL"]["kappa"] == 0.0
    # chạy tiếp từ bản dở: chỉ làm phần còn thiếu
    do = json.loads(ra.read_text(encoding="utf-8"))
    do["cac_luong"][str(LUONG_TEST)]["trang_thai"] = "DANG CHAY"
    do["cac_luong"][str(LUONG_TEST)]["o"]["2x"]["thi_truong"] = do["cac_luong"][str(LUONG_TEST)]["o"]["2x"]["thi_truong"][:2]
    do["cac_luong"][str(LUONG_TEST)]["o"]["NULL"]["thi_truong"] = []
    ra.write_text(json.dumps(do), encoding="utf-8")
    goi.clear()
    ket2 = CT.chay_luong(LUONG_TEST, None, 1, True, 100, ra, kh, 50, True, lambda: None, "x", False, ghi)
    assert sorted(goi) == sorted([("2x", c) for c in (12, 13, 14)] + [("NULL", c) for c in (100, 101, 102)])
    assert [m["chi_so"] for m in ket2["cac_luong"][str(LUONG_TEST)]["o"]["2x"]["thi_truong"]] == [10, 11, 12, 13, 14]


def test_chay_luong_khong_de_mat_dong_hat_khac_trong_file_va_khong_ghi_de_dong_da_co(monkeypatch, tmp_path):
    """Lỗi tự bắt ở BƯỚC 295: bản đầu chỉ đọc file khi `--tiep-tuc`, nên chạy dòng 3 sau dòng 2 sẽ GHI ĐÈ mất kết quả dòng 2."""
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang1", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0: _ban_ghi_gia(chi_so))
    monkeypatch.setattr(CT, "tai_lap_sinh", lambda luong, phep, tang, muc, chi_so: f"d{chi_so}")
    ra = tmp_path / "k.json"
    ra.write_text(json.dumps({"cac_luong": {"2": {"trang_thai": "XONG", "o": {"x": 1}}}}), encoding="utf-8")
    kh = {"tang": 1, "o": (("2x", 2.0, 10, 2),)}
    ghi = lambda k, d: Path(d).write_text(json.dumps(k), encoding="utf-8")
    ket = CT.chay_luong(LUONG_TEST, None, 1, False, 100, ra, kh, 50, True, lambda: None, "x", False, ghi)
    assert ket["cac_luong"]["2"] == {"trang_thai": "XONG", "o": {"x": 1}} and str(LUONG_TEST) in ket["cac_luong"]
    assert sorted(json.loads(ra.read_text(encoding="utf-8"))["cac_luong"]) == sorted(["2", str(LUONG_TEST)])
    with pytest.raises(CT.CongTu):                       # đã XONG: không ghi đè, kể cả --tiep-tuc
        CT.chay_luong(LUONG_TEST, None, 1, True, 100, ra, kh, 50, True, lambda: None, "x", False, ghi)
    with pytest.raises(CT.CongTu):                       # đang dở mà không --tiep-tuc: không ghi đè
        d = json.loads(ra.read_text(encoding="utf-8"))
        d["cac_luong"][str(LUONG_TEST)]["trang_thai"] = "DANG CHAY"
        ra.write_text(json.dumps(d), encoding="utf-8")
        CT.chay_luong(LUONG_TEST, None, 1, False, 100, ra, kh, 50, True, lambda: None, "x", False, ghi)


def test_chay_luong_tai_lap_LECH_khi_sinh_lai_ra_bam_khac(monkeypatch, tmp_path):
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang1", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0: _ban_ghi_gia(chi_so))
    monkeypatch.setattr(CT, "tai_lap_sinh", lambda luong, phep, tang, muc, chi_so: "khac")
    kh = {"tang": 1, "o": (("2x", 2.0, 10, 2),)}
    ket = CT.chay_luong(LUONG_TEST, None, 1, False, 100, tmp_path / "k.json", kh, 50, True, lambda: None, "x", False, lambda k, d: None)
    assert ket["cac_luong"][str(LUONG_TEST)]["o"]["2x"]["tai_lap"] == "LECH"
    # Tầng 2 so với `dg_sinh` (băm khung), Tầng 1 so với `dg` (băm dòng)
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang2", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0, co_p2=True: {"chi_so": chi_so, "dg": "dong", "dg_sinh": "khung", "giay": {}})
    monkeypatch.setattr(CT, "tai_lap_sinh", lambda luong, phep, tang, muc, chi_so: "khung")
    kh2 = {"tang": 2, "o": (("2x", 2.0, 10, 2),)}
    ket = CT.chay_luong(LUONG_TEST, None, 1, False, 100, tmp_path / "k.json", kh2, 50, True, lambda: None, "x", False, lambda k, d: None)
    assert ket["cac_luong"][str(LUONG_TEST)]["o"]["2x"]["tai_lap"] == "KHOP"


def test_chay_luong_dong_4_chay_P4_dung_mot_lan_ke_ca_khi_chay_tiep(monkeypatch, tmp_path):
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang2", lambda luong, phep, ten, muc, chi_so, so_hoan_vi=0, co_p2=True: {"chi_so": chi_so, "dg": "d", "dg_sinh": "d", "giay": {}})
    monkeypatch.setattr(CT, "tai_lap_sinh", lambda luong, phep, tang, muc, chi_so: "d")
    dem = []
    p4 = lambda: dem.append(1) or {"lenh": "x", "ma_thoat": 0, "dong_cuoi": "ok"}
    kh = {"tang": 2, "o": (("2x", 2.0, 10, 2),)}
    ph4 = _cong_ok(4)
    monkeypatch.setattr(CT, "kiem_luong_chinh_thuc", lambda luong, phep=None: None)
    ra = tmp_path / "k.json"
    CT.chay_luong(4, ph4, 1, False, 1, ra, kh, 50, True, p4, "x", False, lambda k, d: Path(d).write_text(json.dumps(k), encoding="utf-8"))
    assert dem == [1]
    do = json.loads(ra.read_text(encoding="utf-8"))
    do["cac_luong"]["4"]["trang_thai"] = "DANG CHAY"
    ra.write_text(json.dumps(do), encoding="utf-8")
    CT.chay_luong(4, ph4, 1, True, 1, ra, kh, 50, True, p4, "x", False, lambda k, d: None)
    assert dem == [1]                                   # P4 đã ghi ở bản dở: không chạy lại


def test_viec_kiem_cua_va_goi_dung_ham_tang_theo_tang(monkeypatch):
    goi = []
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang1", lambda *a, **k: goi.append(("t1", a)) or {"chi_so": a[4]})
    monkeypatch.setattr(CT, "chay_mot_thi_truong_tang2", lambda *a, **k: goi.append(("t2", a)) or {"chi_so": a[4]})
    assert CT._viec((LUONG_TEST, None, 1, "2x", 2.0, 7, 50, True)) == ("2x", {"chi_so": 7})
    assert CT._viec((LUONG_TEST, None, 2, "2x", 2.0, 8, 50, False)) == ("2x", {"chi_so": 8})
    assert [g[0] for g in goi] == ["t1", "t2"]
    with pytest.raises(CT.CongTu):
        CT._viec((2, None, 1, "2x", 2.0, 7, 50, True))          # dòng 2 không giấy phép: nổ TRƯỚC khi gọi gì
    assert len(goi) == 2


def test_chay_p4_goi_pytest_voi_test_G1_den_G5_tren_cac_file_co_that_va_tra_ma_thoat_va_dong_cuoi(monkeypatch):
    bat = {}

    class KQ:
        returncode, stdout = 0, "...\n12 passed in 3s\n"
    monkeypatch.setattr(CT.subprocess, "run", lambda lenh, **k: bat.update(lenh=lenh, k=k) or KQ())
    r = CT.chay_p4("py")
    lenh = bat["lenh"]
    ds = [x for x in lenh if x.startswith("tests/")]
    assert lenh[:5] == ["py", "-X", "utf8", "-m", "pytest"] and lenh[lenh.index("-k") + 1] == "test_G1_ or test_G2_ or test_G3_ or test_G4_ or test_G5_"
    assert r == {"lenh": " ".join(lenh[3:]), "ma_thoat": 0, "dong_cuoi": "12 passed in 3s"}
    assert ds and lenh[-len(ds):] == ds
    for f in ds:
        assert (GOC / f).is_file(), f
    assert "tests/test_vong_hoc_thi_truong_gia.py" in bat["lenh"] and "tests/test_tang2_thi_truong_gia.py" in bat["lenh"]
    assert bat["k"]["cwd"] == str(GOC)


def test_ket_qua_khong_phu_thuoc_so_tien_trinh_ke_ca_qua_pickle_sang_tien_trinh_con(tmp_path):
    """Một thị trường là hàm THUẦN của (dòng hạt, chỉ số, mức): 1 tiến trình và 2 tiến trình ra CÙNG bản ghi (trừ giây)."""
    kh = {"tang": 1, "o": (("2x", 2.0, 2001, 2), ("NULL", 0.0, 3001, 1))}

    def chay(n):
        ket = CT.chay_luong(LUONG_TEST, None, n, False, 100, tmp_path / f"k{n}.json", kh, 200, True, lambda: None, "x", False, lambda k, d: None)
        cu = ket["cac_luong"][str(LUONG_TEST)]
        return {ten: [{k: v for k, v in m.items() if k != "giay"} for m in o["thi_truong"]] for ten, o in cu["o"].items()}
    assert chay(1) == chay(2)


def test_luot_thu_that_Tang1_dong_9001_ghi_ra_file_chi_dinh_khong_phai_file_chinh_thuc(tmp_path):
    """Một thị trường 2× thật, qua CẢ pipeline (bộ ba, chuỗi + C1, oracle sau cùng, tái lập bit, ghi bằng `va_an_toan.ghi`)."""
    ra = tmp_path / "thu.json"
    kh = {"tang": 1, "o": (("2x", 2.0, 2001, 1),)}
    ket = CT.chay_luong(LUONG_TEST, None, 1, False, 100, ra, kh, cx.SO_HOAN_VI, True, lambda: None, "thu", False)
    m = ket["cac_luong"][str(LUONG_TEST)]["o"]["2x"]["thi_truong"][0]
    assert ket["cac_luong"][str(LUONG_TEST)]["trang_thai"] == "XONG" and ket["cac_luong"][str(LUONG_TEST)]["o"]["2x"]["tai_lap"] == "KHOP"
    assert set(m) == {"chi_so", "dg", "nguong", "bo_ba", "chuoi", "oracle", "giay"} and set(m["bo_ba"]) == {"G", "Z", "H"}
    assert abs(m["nguong"] - 0.05 / 3) < 1e-15 and m["chuoi"]["c1"] == [] and set(m["oracle"]["spec"]) == set(TEN_12)
    assert m["oracle"]["top_f"] in TEN_F and set(m["giay"]) == {"sinh", "bo_ba", "chuoi", "oracle"}
    assert json.loads(ra.read_text(encoding="utf-8")) == json.loads(json.dumps(ket))      # bản ghi trên đĩa = bản trả về
    assert not CT.DUONG_KET_QUA.exists() or CT.DUONG_KET_QUA.read_text(encoding="utf-8") != ra.read_text(encoding="utf-8")


def test_thi_truong_tang1_cho_ket_qua_giong_hieu_chuan_Lat_2_o_bo_ba_cung_mot_thi_truong():
    """Bộ ba của dụng cụ này đi ĐÚNG đường của `hieu_chuan_thi_truong_gia.cham_mot_thi_truong` (cùng `cham`, cùng sổ, cùng hạt hoán vị)."""
    import hieu_chuan_thi_truong_gia as H
    h = H.cham_mot_thi_truong(2001, KAPPA_2X, luong=1, so_hoan_vi=200)      # dòng 1 (dụng cụ Lát 2 chỉ nhận dòng 1)
    tt = T.sinh_thi_truong(1, 2001, KAPPA_2X, co_su_that=False)
    bang = {"gia": tt.gia, "keo_luc": H.keo_luc_gia(tt.ngay[-1]), "nguon": {m: "vci" for m in tt.ma}}
    r = cx.cham(tt.dong_quyet_dinh(), H.so_ung_vien_bo_ba(), bang, cx.HAT_RNG, 200)
    mine = CT.bo_ba_tang1_ket_qua(r)
    for ten in ("G", "Z", "H"):
        assert mine[ten]["tt"] == h[ten]["trang_thai"] and mine[ten]["p"] == h[ten]["p"] and mine[ten]["delta"] == h[ten]["delta"]


# ══ TẦNG 2 (dữ liệu và `_analyze` GIẢ — đường thật nằm ở dụng cụ, không ở pytest) ═════════════════════════

def _analyze_gia(monkeypatch):
    import zlib

    import paper_runner as pr

    def gia_lap(ma, df, san, ngay):
        r = np.random.default_rng(zlib.crc32(f"{ma}|{ngay}".encode()))
        tp = {k: float(r.integers(0, 101)) for k in ("trend_score", "momentum_score", "volume_score", "sr_score", "risk_score")}
        return {"final_score": int(r.integers(20, 80)), "recommendation": "x", "key_reasons": [], "data_quality": "OK", "score_breakdown": tp}
    monkeypatch.setattr(pr, "_analyze", gia_lap)


def test_so_ung_vien_bo_ba_tang2_la_Gp_Z_H_khai_o_ba_thang_cua_dong_thoi_gian_2():
    so = CT.so_ung_vien_bo_ba_tang2()["ung_vien"]
    ho = T.ho_spec_oracle()
    assert sorted(so) == ["Gp", "H", "Z"]
    assert so["Gp"]["spec"] == ho["bo_momentum_score"] and so["Z"]["spec"] == ho["doi_cho_trend_sr"] and so["H"]["spec"] == ho["bo_volume_score"]
    assert [so[t]["khai_ngay"] for t in ("Gp", "Z", "H")] == G.dong_thoi_gian_2()["khai_ngay"]
    assert CT.TEN_SPEC_GP == G_PHAY["g_phay"] == "bo_momentum_score"
    assert so["Z"]["spec"] == T.spec_z() and so["H"]["spec"] == T.ho_spec_f()[T.TEN_SPEC_H]


def test_thi_truong_tang2_chay_nguyen_pipeline_voi_analyze_gia_dung_khuon_ban_ghi(monkeypatch):
    _analyze_gia(monkeypatch)
    monkeypatch.setattr(G, "chay_that_va_phat_lai", lambda tt, dong_quyet_dinh_san=None: {
        "khac": [], "diem_lech": [], "thuc": [1, 2, 3], "phat": [1, 2, 3], "bi_chan_vni": 4, "so_diem_so_duoc": len(dong_quyet_dinh_san)})
    m = CT.chay_mot_thi_truong_tang2(LUONG_TEST, None, "2x", 2.0, 5)
    assert set(m) == {"chi_so", "dg_sinh", "dg", "nguong", "bo_ba", "p1", "p2", "p3", "chuoi", "giay"}
    assert set(m["bo_ba"]) == {"Gp", "Z", "H"} and abs(m["nguong"] - 0.05 / 3) < 1e-15
    assert m["p1"]["so_vi_pham"] == 0 and m["p1"]["dq_khong_ok"] == 0 and m["p1"]["so_dong"] == 60 * G.dong_thoi_gian_2()["tong"]
    assert m["p2"] == {"so_khac": 0, "so_diem_lech": 0, "so_lenh_that": 3, "so_lenh_phat": 3, "bi_chan_vni": 4, "so_diem_so_duoc": m["p1"]["so_dong"]}
    assert -1 <= m["p3"]["ic_volume"] <= 1 and m["chuoi"]["c1"] == [] and {"sinh", "cham", "bo_ba", "chuoi", "p2"} == set(m["giay"])
    for t in ("Gp", "Z", "H"):
        assert m["bo_ba"][t]["n_ma"] == 60 and m["bo_ba"][t]["n_phien"] == cx.cb.MOC_DOC


def test_thi_truong_tang2_co_p2_False_khong_goi_phat_lai_va_ghi_p2_None(monkeypatch):
    _analyze_gia(monkeypatch)

    def no(*a, **k):
        raise AssertionError("P2 khong duoc chay")
    monkeypatch.setattr(G, "chay_that_va_phat_lai", no)
    m = CT.chay_mot_thi_truong_tang2(LUONG_TEST, None, "NULL", 0.0, 6, co_p2=False)
    assert m["p2"] is None and "p2" not in m["giay"]
    # P2 lệch (khác ô hay lệch điểm) phải đi vào bản ghi
    monkeypatch.setattr(G, "chay_that_va_phat_lai", lambda tt, dong_quyet_dinh_san=None: {
        "khac": ["x", "y"], "diem_lech": ["z"], "thuc": [], "phat": [], "bi_chan_vni": 0, "so_diem_so_duoc": 0})
    m = CT.chay_mot_thi_truong_tang2(LUONG_TEST, None, "NULL", 0.0, 6)
    assert m["p2"]["so_khac"] == 2 and m["p2"]["so_diem_lech"] == 1


def test_tai_lap_sinh_Tang1_va_Tang2_bang_bit_va_nho_hat_va_nho_muc():
    a, b = CT.tai_lap_sinh(LUONG_TEST, None, 1, 2.0, 5), CT.tai_lap_sinh(LUONG_TEST, None, 1, 2.0, 5)
    assert a == b and a != CT.tai_lap_sinh(LUONG_TEST, None, 1, 2.0, 6) and a != CT.tai_lap_sinh(LUONG_TEST, None, 1, 1.0, 5)
    c, d = CT.tai_lap_sinh(LUONG_TEST, None, 2, 2.0, 5), CT.tai_lap_sinh(LUONG_TEST, None, 2, 2.0, 5)
    assert c == d and c != CT.tai_lap_sinh(LUONG_TEST, None, 2, 2.0, 6) and c != CT.tai_lap_sinh(LUONG_TEST, None, 2, 0.0, 5)


# ══ GÁC (AST) ═════════════════════════════════════════════════════════════════════════════════════════════

def _cay():
    return ast.parse(DUONG_TOOL.read_text(encoding="utf-8"))


def _ham(cay):
    return {n.name: n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}


def _goi(cay):
    ra = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            ra.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return ra


VAO_BO_SINH = {"sinh_thi_truong", "sinh_thi_truong_2", "sinh_null", "tinh_su_that", "_sinh_loi", "_sinh_ohlcv_loi", "chay_vong", "cham_diem_theo_ma"}


def _ham_goi_bo_sinh_thieu_cua(nguon: str) -> list[str]:
    sai = []
    for ten, f in _ham(ast.parse(nguon)).items():
        dong_sinh = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call)
                     and ((isinstance(n.func, ast.Attribute) and n.func.attr in VAO_BO_SINH) or (isinstance(n.func, ast.Name) and n.func.id in VAO_BO_SINH))]
        if not dong_sinh:
            continue
        dong_cua = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "kiem_luong_chinh_thuc"]
        if not dong_cua or min(dong_cua) > min(dong_sinh):
            sai.append(ten)
    return sai


def test_G4_AST_moi_ham_goi_bo_sinh_hay_vong_phai_goi_cua_TRUOC_va_do_bat_duoc_mau_xau():
    nguon = DUONG_TOOL.read_text(encoding="utf-8")
    assert _ham_goi_bo_sinh_thieu_cua(nguon) == []
    chạm = {t for t, f in _ham(_cay()).items() if _goi(f) & VAO_BO_SINH}
    assert {"chay_mot_thi_truong_tang1", "chay_mot_thi_truong_tang2", "tai_lap_sinh"} <= chạm
    assert _ham_goi_bo_sinh_thieu_cua("def f(l):\n    return T.sinh_thi_truong(l, 1, 0.0)\n") == ["f"]
    assert _ham_goi_bo_sinh_thieu_cua("def f(l):\n    x = G.sinh_thi_truong_2(l, 1, 0.0)\n    kiem_luong_chinh_thuc(l)\n") == ["f"]
    assert _ham_goi_bo_sinh_thieu_cua("def f(l):\n    return V.chay_vong(l, 1)\n") == ["f"]
    assert _ham_goi_bo_sinh_thieu_cua("def f(l):\n    kiem_luong_chinh_thuc(l)\n    return T.sinh_thi_truong(l, 1, 0.0)\n") == []
    assert _ham_goi_bo_sinh_thieu_cua("def f(l):\n    kiem_luong(l)\n    return T.sinh_thi_truong(l, 1, 0.0)\n") == ["f"]   # cửa cũ KHÔNG đủ


def test_G4_AST_oracle_chi_doc_SAU_loi_goi_vong_va_bo_ba_trong_ham_tang1():
    f = _ham(_cay())["chay_mot_thi_truong_tang1"]
    dong = lambda ten: [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == ten]
    assert dong("tinh_su_that") and max(dong("chay_vong") + dong("cham")) < min(dong("tinh_su_that"))
    for ten in ("chay_mot_thi_truong_tang2",):           # Tầng 2 không có oracle từng thị trường
        assert "tinh_su_that" not in _goi(_ham(_cay())[ten])


def test_AST_PhepChay_chi_duoc_dung_trong_kiem_cong():
    cay = _cay()
    cho = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "PhepChay"]
    kc = _ham(cay)["kiem_cong"]
    assert len(cho) == 1 and cho[0] in list(ast.walk(kc))


TEN_GHI = {"push", "write_all", "append_rows", "ghi_ke_hoach", "record_trade", "write_text", "write_bytes", "to_csv", "to_json", "dump",
           "to_parquet", "to_pickle", "savetxt", "save", "savez", "executemany", "commit", "open"}
CAM_TEN_THAT = {"SO_UNG_VIEN", "doc_so_ung_vien", "sheets_store", "keo_bang_gia", "doc_so_that", "PaperTradingJournal"}
CAM_CHUOI = ("ung-vien", "phuong-an-bong", "UV-", "backtest")
#: Chuỗi `cache` DUY NHẤT được phép: tuỳ chọn của pytest mà `chay_p4` truyền để lượt P4 không để thư mục nháp ở gốc repo. Mọi chuỗi
#: khác có chữ `cache` (đường `backtest/cache*` của G3) vẫn bị cấm.
CHUOI_CACHE_DUOC_PHEP = {"no:cacheprovider"}


def _chuoi_ngoai_docstring(cay):
    doc = {id(n.body[0].value) for n in ast.walk(cay) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
           and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str)}
    return [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc]


def test_G1_G3_AST_dung_cu_khong_ghi_gi_ngoai_mot_lan_ghi_va_an_toan_ghi_va_khong_nhac_the_gioi_that():
    cay = _cay()
    assert not (_goi(cay) & TEN_GHI), sorted(_goi(cay) & TEN_GHI)
    gi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "ghi"]
    assert len(gi) == 1 and gi[0] in list(ast.walk(_ham(cay)["ghi_ket_qua"]))
    chuoi = _chuoi_ngoai_docstring(cay)
    assert not [s for s in chuoi if any(c in s for c in CAM_CHUOI)]
    assert {s for s in chuoi if "cache" in s.lower()} == CHUOI_CACHE_DUOC_PHEP
    ten = {n.id for n in ast.walk(cay) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
    assert not (ten & CAM_TEN_THAT)
    duong = sorted(s for s in chuoi if (s.endswith(".md") or s.endswith(".json")) and " " not in s)
    assert duong == sorted(["docs/TIEU-CHI-DOC-TRUOC.md", "docs/thi-truong-gia-g-phay.json", "docs/thi-truong-gia-hieu-chuan.json",
                            "thi-truong-gia-g-phay.json", "thi-truong-gia-hieu-chuan.json", "thi-truong-gia-ket-qua.json"]), duong
    assert CT.DUONG_KET_QUA == GOC / "docs" / "thi-truong-gia-ket-qua.json"   # file ghi DUY NHẤT của dụng cụ
    ngay = [s for s in chuoi if len(s) == 10 and s[4] == "-" and s[7] == "-" and s[:4].isdigit()]
    assert all(s >= "2100-01-04" for s in ngay)


def test_AST_dung_cu_chi_nhap_nhung_thu_cho_phep_va_nap_khong_keo_theo_the_gioi_that():
    cay = _cay()
    nhap = {a.name.split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.Import) for a in n.names} | \
           {(n.module or "").split(".")[0] for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)}
    assert nhap <= {"__future__", "argparse", "dataclasses", "hashlib", "importlib", "json", "math", "platform", "re", "subprocess", "sys", "time",
                    "concurrent", "pathlib", "numpy", "cham_bong", "cham_xac_nhan", "thi_truong_gia", "thi_truong_gia_tang2", "vong_hoc_gia",
                    "chay_vong_tang2_thi_truong_gia", "hieu_chuan_thi_truong_gia"}, sorted(nhap)
    ma = ("import sys, json, importlib.util; sys.path.insert(0, %r); s = importlib.util.spec_from_file_location('ct', %r); "
          "m = importlib.util.module_from_spec(s); sys.modules['ct'] = m; s.loader.exec_module(m); "
          "cam = ['sheets_store', 'keo_bang_gia', 'doc_so_that', 'gspread', 'google_sheets_sync', 'paper_trading', 'paper_runner', "
          "'run_daily', 'vnstock', 'vnstock_data']; print(json.dumps([x for x in cam if x in sys.modules]))" % (str(GOC), str(DUONG_TOOL)))
    r = subprocess.run([sys.executable, "-I", "-c", ma], capture_output=True, text=True, cwd=str(GOC), timeout=180,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    assert json.loads(r.stdout.strip().splitlines()[-1]) == [], r.stdout


def test_AST_so_2_3_4_5_chi_xuat_hien_o_ke_hoach_va_ba_hang_dong_hat_khong_o_loi_goi_nao():
    cay = _cay()
    tu_khoa = [(k.arg, k.value.value) for n in ast.walk(cay) if isinstance(n, ast.Call) for k in n.keywords
               if k.arg == "luong" and isinstance(k.value, ast.Constant)]
    assert tu_khoa == []
    gan = {t.id: n.value for n in ast.walk(cay) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)
           and t.id in ("LUONG_THU", "LUONG_CHINH_THUC", "LUONG_KHONG_BAO_GIO")}
    assert ast.literal_eval(gan["LUONG_THU"]) == 9001 and ast.literal_eval(gan["LUONG_CHINH_THUC"]) == (2, 3, 4) \
        and ast.literal_eval(gan["LUONG_KHONG_BAO_GIO"]) == (5,)


def test_dung_cu_khong_co_doi_so_nao_chon_dong_hat_ngoai_luong_va_khong_co_doi_so_ghi_ra_file_chinh_thuc():
    co = [n.args[0].value for n in ast.walk(_cay()) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "add_argument" and n.args and isinstance(n.args[0], ast.Constant)]
    assert "--luong" in co and "--ket-cuc" in co and "--ra" in co and not [c for c in co if "hat" in c or "stream" in c]


# ══ ĐO 37 TRONG docs/TIEU-CHI-DOC-TRUOC.md ════════════════════════════════════════════════════════════════

TIEU_CHI = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
DAC_TA = (GOC / "docs" / "thiet-ke-c4-thi-truong-gia.md").read_text(encoding="utf-8")
DO37 = CT.cat_muc_do(TIEU_CHI)


def test_ĐO_37_co_trong_tieu_chi_la_muc_ke_tiep_va_duy_nhat():
    assert DO37 is not None
    assert len(re.findall(r"^##\s+ĐO\s+37\s*—", TIEU_CHI, re.M)) == 1
    so = [int(m.group(1)) for m in re.finditer(r"^##\s+ĐO\s+(\d+)[a-z]?\s*—", TIEU_CHI, re.M)]
    assert max(so) == 37 and "**Đã tra trùng:** BƯỚC" in DO37 and f"`{CT.TEN_DUNG_CU}`" in DO37


def test_ĐO_37_nêu_nguyen_van_lenh_va_dong_ke_hoach_cua_ca_ba_dong_hat_va_lenh_doc_ket_cuc():
    chuan = CT.chuan_hoa(DO37)
    for l in CT.LUONG_CHINH_THUC:
        assert CT.chuan_hoa(CT.lenh_chuan(l)) in chuan and CT.chuan_hoa(CT.dong_ke_hoach(l)) in chuan
        assert f"./.venv/Scripts/python.exe -X utf8 {CT.lenh_chuan(l)} --so-tien-trinh 12" in DO37
    assert f"./.venv/Scripts/python.exe -X utf8 {CT.TEN_DUNG_CU} --ket-cuc" in DO37
    assert "docs/thi-truong-gia-ket-qua.json" in DO37


def test_ĐO_37_chep_NGUYEN_VAN_cac_dong_cua_bang_muc_6_cua_dac_ta():
    """Mọi dòng của bảng (`| **A** |` … `| **PT** |`), dòng định nghĩa, ghi chú hàng PT, 'Báo cáo, không phán' và ba kết cục."""
    muc6 = DAC_TA[DAC_TA.index("## 6. Tiêu chí đạt/trượt"): DAC_TA.index("## 7. Gác")]
    cac = [s for s in muc6.splitlines() if s.startswith("| **") or s.startswith("**Định nghĩa.**") or s.startswith("> **Hàng PT, vế G")
           or s.startswith("**Báo cáo, không phán:**") or s.startswith("- **ĐẠT**") or s.startswith("- **TRƯỢT ở tiêu chí X**")
           or s.startswith("- **KHÔNG ĐỌC ĐƯỢC**") or s.startswith("Số thị trường (R)")]
    assert len(cac) == 11 + 1 + 1 + 1 + 3 + 1    # 11 hàng (A · A0 · B1–B4 · C1–C3 · P · PT) + định nghĩa + ghi chú PT + báo cáo + 3 kết cục + R
    chuan = DO37.replace("\r\n", "\n")
    thieu = [s[:60] for s in cac if s not in chuan and CT.chuan_hoa(s) not in CT.chuan_hoa(re.sub(r"^> ", "", chuan, flags=re.M))]
    assert thieu == [], thieu


def test_ĐO_37_nêu_so_do_chi_so_va_ngưỡng_tu_bản_ghi_dong_1_khong_go_tay():
    for m in HIEU_CHUAN["muc"]:
        if m["he_so"] > 0:
            assert f"{m['kappa']:.6f}" in DO37 and f"{m['muc_tieu_delta_ic']:.4f}" in DO37
    lo, hi = HIEU_CHUAN["kiem_1x_trong_dai_99"]["dai_99_quanh_80"]
    assert f"[{lo} ; {hi}]" in DO37
    assert f"[{G_PHAY['dai_thap']} ; {G_PHAY['dai_cao']}]" in DO37 and G_PHAY["g_phay"] in DO37
    assert re.search(r"thi-truong-gia-hieu-chuan\.json[^\n]*`[0-9a-f]{7,40}`", DO37) and re.search(r"thi-truong-gia-g-phay\.json[^\n]*`[0-9a-f]{7,40}`", DO37)
    for k, v in CT.NGUONG.items():
        assert str(v) in DO37, k
    assert str(CT.SO_BOOTSTRAP_C2) in DO37 and "hạt 0" in DO37


def test_ĐO_37_khai_bo_ba_tang_2_la_quyet_dinh_cua_leader_va_Z_H_chi_bao_cao():
    assert "quyết định của leader" in DO37 and "KHÔNG phải quyết định của người dùng" in DO37
    for ten in ("bo_momentum_score", "doi_cho_trend_sr", "bo_volume_score"):
        assert ten in DO37
    assert "BÁO CÁO, KHÔNG PHÁN" in DO37


def test_ĐO_37_tieu_chi_may_do_NULL_theo_ty_le_da_ky_voi_loi_NGUOI_DUNG_nguyen_van_va_ba_nguong_cua_dung_cu():
    """BƯỚC 295 pha 2: mục từng ghi CHỜ NGƯỜI DÙNG DUYỆT nay đã ký; lời người dùng (23/11/2026) và câu hỏi nguyên văn nằm trong ĐO."""
    for k, v in (("ty_le_o_trong_2se_toi_thieu", CT.MAY_DO_NULL["ty_le_o_trong_2se_toi_thieu"]), ("trung_binh_z_toi_da", CT.MAY_DO_NULL["trung_binh_z_toi_da"])):
        assert str(v).replace(".", ",") in DO37, k
    lo, hi = CT.MAY_DO_NULL["sd_z"]
    assert f"{lo}".replace(".", ",") in DO37 and f"{hi}".replace(".", ",") in DO37
    assert "mục 15 khoản 8" in DO37
    assert 'NGƯỜI DÙNG ĐÃ DUYỆT 23/11/2026, nguyên văn *"đồng ý"*' in DO37
    assert ("*\"BƯỚC 295: đồng ý đọc gộp phép kiểm máy đo ở thị trường NULL không? Ngưỡng: ít nhất 85% số ô trong 2 lần sai số, "
            "độ lệch chuẩn z trong 0,7–1,5, trị tuyệt đối trung bình z dưới 0,5.\"*") in DO37
    assert "CHỜ NGƯỜI DÙNG" not in DO37 and "KHÔNG được coi là đã ký" not in DO37
    assert DO37.count("MỌI ô (thị trường NULL của dòng 3 × 12 spec)") == 2     # ở mục Gốc và ở khoản 1 của Đ9
    assert "MỌI ô (thị trường NULL của dòng 3 × 12 spec), z = ΔIC_true / sai số MC" in DO37
    # ba ngưỡng ĐÚNG CHỖ chữ đậm của khoản 1 của Đ9 (sinh từ hằng số của dụng cụ, không gõ số), không chỉ "số có đâu đó trong ĐO"
    v = lambda x: str(x).replace(".", ",")   # noqa: E731
    for cau in (f"**tỷ lệ ô có |z| < 2 ≥ {v(CT.MAY_DO_NULL['ty_le_o_trong_2se_toi_thieu'])}**",
                f"**{v(lo)} < sd(z) < {v(hi)}**",
                f"**|trung bình z| < {v(CT.MAY_DO_NULL['trung_binh_z_toi_da'])}**"):
        assert cau in DO37, cau


def test_ba_nguong_may_do_NULL_la_ba_nguong_da_khoa_o_test_cua_Lat_1_truoc_khi_chay():
    nguon = (GOC / "tests" / "test_thi_truong_gia.py").read_text(encoding="utf-8")
    for dong in ("assert 0.7 < z.std() < 1.5", "assert float(np.mean(np.abs(z) < 2)) >= 0.85", "assert abs(float(z.mean())) < 0.5"):
        assert dong in nguon, dong
    assert CT.MAY_DO_NULL == {"ty_le_o_trong_2se_toi_thieu": 0.85, "sd_z": (0.7, 1.5), "trung_binh_z_toi_da": 0.5}
