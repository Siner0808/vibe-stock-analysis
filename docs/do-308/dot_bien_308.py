"""Vong dot bien BUOC 308 (Dow phan 2, Lat 2: dow_hai_chi_so.py) — chay tren BAN SAO cua cay lam viec.

Chay tu goc ban sao:  ./.venv/Scripts/python.exe -X utf8 docs/do-308/dot_bien_308.py <mo_dun|gac_nhap|tat_ca>
(`.venv` cua repo chinh; ban sao khong co .venv rieng, goi bang duong dan tuyet doi cua may dang chay.)
Ma thoat 1 neu con phat SONG (rong la du do). Moi phat chay pytest tren file gac cua no, roi HOAN TRA tung byte.

Nhom `mo_dun`: dot bien len `dow_hai_chi_so.py` voi hai file test cua no lam gac.
Nhom `gac_nhap`: dot bien len `tests/test_cau_truc_gia.py` (bo dong CHO_PHEP_NHAP), them mot file nhap la, them import
cam vao mo-dun: gac nhap va gac loi o `tests/test_dow_hai_chi_so_buc_tuong.py` va file kia phai do.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
WT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WT / "tools"))
os.chdir(WT)
from va_an_toan import dot_bien_bo  # noqa: E402

MD = str(WT / "dow_hai_chi_so.py")
LENH = ["-m", "pytest", "tests/test_dow_hai_chi_so.py", "tests/test_dow_hai_chi_so_buc_tuong.py", "-q", "-x",
        "-p", "no:cacheprovider"]
LENH_NHAP = ["-m", "pytest", "tests/test_dow_hai_chi_so_buc_tuong.py", "tests/test_cau_truc_gia.py", "-q", "-x",
             "-p", "no:cacheprovider"]

# (ten, neo cu, neo moi): neo phai khop DUNG MOT lan
MO_DUN = [
    # ── chin phat cua dac ta §6 hang 2 ──
    ("1. ngay_ket = ngay SOM hon (buoc 4)", "ngay_ket=ngay[k], tre=k - mo.k_mo, ly_do=ly_do, lat_kia=lat_kia)",
     "ngay_ket=mo.ngay_mo, tre=k - mo.k_mo, ly_do=ly_do, lat_kia=lat_kia)"),
    ("1b. ngay_ket = ngay som hon (xac nhan ngay o buoc 5)", "k_ket=k, ngay_ket=ngay[k], tre=k - cu.k,",
     "k_ket=k, ngay_ket=cu.ngay, tre=k - cu.k,"),
    ("2. buoc 4: <= w thanh < w", "elif w is None or k - mo.k_mo <= w:", "elif w is None or k - mo.k_mo < w:"),
    ("2b. buoc 5: <= w thanh < w", "if w is not None and k - x.k > w:", "if w is not None and k - x.k >= w:"),
    ("2c. buoc 1: > w thanh >= w", "if mo is not None and w is not None and k - mo.k_mo > w:",
     "if mo is not None and w is not None and k - mo.k_mo >= w:"),
    ("3. bo mot-doi-mot", "if x.chieu == chieu and (ten_kia, x.k) not in dung:", "if x.chieu == chieu:"),
    ("4. bo buoc 2 (lead lat lai)", "if hom_nay[lead] is not None and hom_nay[lead].chieu != mo.chieu:",
     "if False:"),
    ("5. KHOI_DAU tinh la lat", "if e.cap == C.CAP_SWING and e.loai == C.CHOCH)",
     "if e.cap == C.CAP_SWING and e.loai in (C.CHOCH, C.KHOI_DAU))"),
    ("5b. BOS tinh la lat", "if e.cap == C.CAP_SWING and e.loai == C.CHOCH)",
     "if e.cap == C.CAP_SWING and e.loai in (C.CHOCH, C.BOS))"),
    ("5c. cap noi bo tinh la lat", "if e.cap == C.CAP_SWING and e.loai == C.CHOCH)",
     "if e.cap in C.CAPS and e.loai == C.CHOCH)"),
    ("6. trang thai doc k_ket >= t", "if moi.k_ket is None or moi.k_ket > t:", "if moi.k_ket is None or moi.k_ket >= t:"),
    ("6b. trang thai dao dau k_ket <= t", "if moi.k_ket is None or moi.k_ket > t:",
     "if moi.k_ket is None or moi.k_ket <= t:"),
    ("6c. trang thai doc ket_qua bo qua k_ket", "if moi.k_ket is None or moi.k_ket > t:", "if moi.ket_qua == DANG_CHO:"),
    ("7. chi A duoc lam lead (buoc 2-4)", "lead, kia = mo.lead, _kia(mo.lead)", "lead, kia = LEAD_A, LEAD_B"),
    ("7b. chi A duoc MO doan (buoc 5)", "if mo is None and con:", "if mo is None and con and (LEAD_A in con or len(con) == 2):"),
    # ── bon phat leader dat them ──
    # L1 (U1 cho lat cua doan HET HAN) la phat TUONG DUONG: lat het han luon xa hon w moi lat sau nen khong bao gio duoc
    # chon o buoc 5; dong `dung.discard` tuong ung bi xoa khoi ma (lan dot bien dau: phat nay song sot).
    ("L1b. U1: lat lead_dao_chieu khong tra ranh", "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, LEAD_DAO_CHIEU))\n                dung.discard((lead, mo.lat_mo.k))\n",
     "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, LEAD_DAO_CHIEU))\n"),
    ("L1c. U1: lat ben_kia_nguoc khong tra ranh", "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, BEN_KIA_NGUOC))\n                    dung.discard((lead, mo.lat_mo.k))\n",
     "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, BEN_KIA_NGUOC))\n"),
    ("L2. Q2: trai chieu lay chieu cua A (thu tu A roi B)",
     "ra.append(_doan_cung_hang(None, k, ngay, w, fa, fb, KHONG_XAC_NHAN, BEN_KIA_NGUOC))",
     "ra.append(_doan_cung_hang(fa.chieu, k, ngay, w, fa, fb, KHONG_XAC_NHAN, BEN_KIA_NGUOC))"),
    ("L2b. Q2: trai chieu xu ly nhu cung chieu", "if fa.chieu == fb.chieu:", "if True:"),
    ("L2c. Q2: trai chieu danh dau hai lat da dung (khong ranh)",
     "ra.append(_doan_cung_hang(None, k, ngay, w, fa, fb, KHONG_XAC_NHAN, BEN_KIA_NGUOC))",
     "ra.append(_doan_cung_hang(None, k, ngay, w, fa, fb, KHONG_XAC_NHAN, BEN_KIA_NGUOC))\n"
     "                    dung |= {(LEAD_A, k), (LEAD_B, k)}"),
    ("L2d. Q2: trai chieu van mo doan cho",
     "ra.append(_doan_cung_hang(None, k, ngay, w, fa, fb, KHONG_XAC_NHAN, BEN_KIA_NGUOC))",
     "ra.append(_doan_cung_hang(None, k, ngay, w, fa, fb, KHONG_XAC_NHAN, BEN_KIA_NGUOC))\n"
     "                    mo = Doan(lead=LEAD_A, chieu=fa.chieu, k_mo=k, ngay_mo=fa.ngay, k_tao=k, ket_qua=DANG_CHO,\n"
     "                              k_ket=None, ngay_ket=None, tre=None, ly_do=None, w=w, lat_mo=fa, lat_kia=None)"),
    ("L3. doan con mo o cuoi bang ghi het_han", "    if mo is not None:\n        ra.append(mo)\n",
     "    if mo is not None:\n        ra.append(replace(mo, ket_qua=KHONG_XAC_NHAN, k_ket=mo.k_mo + (w or 0) + 1, ly_do=HET_HAN))\n"),
    ("L3b. doan con mo o cuoi bang ghi het_han (chi khi w huu han)", "    if mo is not None:\n        ra.append(mo)\n",
     "    if mo is not None:\n        ra.append(mo if w is None else replace(mo, ket_qua=KHONG_XAC_NHAN, k_ket=mo.k_mo + w + 1, ly_do=HET_HAN))\n"),
    ("L4. lat dong doan o buoc 3 bi danh dau da dung",
     "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, BEN_KIA_NGUOC))\n                    dung.discard((lead, mo.lat_mo.k))\n",
     "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, BEN_KIA_NGUOC))\n                    dung.discard((lead, mo.lat_mo.k))\n                    con.remove(kia)\n"),
    ("L4b. lat dong doan o buoc 2 bi danh dau da dung",
     "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, LEAD_DAO_CHIEU))\n                dung.discard((lead, mo.lat_mo.k))\n",
     "ra.append(_dong(mo, KHONG_XAC_NHAN, k, ngay, LEAD_DAO_CHIEU))\n                dung.discard((lead, mo.lat_mo.k))\n                con.remove(lead)\n"),
    # ── them cua phien con ──
    ("X1. doan moi nhat theo k_mo thay vi theo thu tu tao",
     "        if d.k_tao <= t:\n            moi = d\n",
     "        if d.k_mo <= t and (moi is None or d.k_mo >= moi.k_mo):\n            moi = d\n"),
    ("X1b. k_tao <= t thanh k_tao < t", "        if d.k_tao <= t:\n", "        if d.k_tao < t:\n"),
    ("X2. buoc 5 tim lat xa nhat thay vi gan nhat", "for x in reversed(lat_kia):", "for x in lat_kia:"),
    ("X3. buoc 5 bo cua cua so w", "if w is not None and k - x.k > w:", "if False:"),
    ("X3b. buoc 5 bo dieu kien cung chieu", "if x.chieu == chieu and (ten_kia, x.k) not in dung:",
     "if (ten_kia, x.k) not in dung:"),
    ("X4. tre cua xac nhan ngay lech 1", "tre=k - cu.k, ly_do=None", "tre=k - cu.k + 1, ly_do=None"),
    ("X4b. tre cua _dong lech 1", "ngay_ket=ngay[k], tre=k - mo.k_mo, ly_do=ly_do", "ngay_ket=ngay[k], tre=k - mo.k_mo + 1, ly_do=ly_do"),
    ("X4c. tre cung hang bang 1", "ngay_ket=ngay[k], tre=0, ly_do=ly_do, w=w, lat_mo=fa", "ngay_ket=ngay[k], tre=1, ly_do=ly_do, w=w, lat_mo=fa"),
    ("X5. bo kiem ngay lat", "if x.ngay != ngay[x.k]:", "if False:"),
    ("X5b. bo kiem k ngoai bang", "or not 0 <= x.k < len(ngay):", "or not 0 <= x.k <= len(ngay):"),
    ("X5c. bo kiem cung chieu lien nhau", "if x.chieu == truoc.chieu:", "if False:"),
    ("X5d. bo kiem cung hang", "if x.k <= truoc.k:", "if x.k < truoc.k:"),
    ("X5e. cho phep w am", "or w < 0):", "or w < -1):"),
    ("X6. con_lai lech 1", "con_lai = None if moi.w is None else moi.w - (t - moi.k_mo)",
     "con_lai = None if moi.w is None else moi.w - (t - moi.k_mo) + 1"),
    ("X6b. tre cua trang thai khong xac nhan lo ra", "moi.tre if moi.ket_qua == XAC_NHAN else None", "moi.tre"),
    ("X6c. trang thai chua_du -> dang_cho", "return TrangThaiCap(CHUA_DU, None, None, None, None, None, None, None, None, None, None)",
     "return TrangThaiCap(DANG_CHO, None, None, None, None, None, None, None, None, None, None)"),
    ("X7. lat dung ngay_xay_ra", "Lat(k=e.chi_so_biet, ngay=e.ngay_biet, chieu=e.chieu)", "Lat(k=e.chi_so_biet, ngay=e.ngay_xay_ra, chieu=e.chieu)"),
    ("X7b. lat dung chi_so_xay_ra", "Lat(k=e.chi_so_biet, ngay=e.ngay_biet, chieu=e.chieu)", "Lat(k=e.chi_so_xay_ra, ngay=e.ngay_biet, chieu=e.chieu)"),
    ("X8. buoc 3 bo (chuoi kia nguoc chieu coi nhu cung chieu)", "if f.chieu != mo.chieu:", "if False:"),
    ("X8b. buoc 4 xac nhan khong danh dau lat dung", "dung.add((kia, k))\n                    con.remove(kia)", "con.remove(kia)"),
    ("X8c. buoc 5 mo doan khong danh dau lat dung", "                    dung.add((ten, k))\n    if mo is not None:",
     "                    pass\n    if mo is not None:"),
    ("X8d. xac nhan ngay khong danh dau lat dung", "dung |= {(_kia(ten), cu.k), (ten, k)}", "dung |= {(ten, k)}"),
    ("X8e. cung hang cung chieu khong danh dau lat dung", "dung |= {(LEAD_A, k), (LEAD_B, k)}\n                else:",
     "pass\n                else:"),
    # hien thi
    ("H1. huong len/xuong dao", '_HUONG = {C.TANG: "lên", C.GIAM: "xuống"}', '_HUONG = {C.TANG: "xuống", C.GIAM: "lên"}'),
    ("H2. theo sau dao vai", "{ten[_kia(tt.lead)]} theo sau {ten[tt.lead]} {tt.tre} phiên",
     "{ten[tt.lead]} theo sau {ten[_kia(tt.lead)]} {tt.tre} phiên"),
    ("H3. ngay dao dd/mm", 'return f"{ngay_thang}/{thang}/{nam}"', 'return f"{thang}/{ngay_thang}/{nam}"'),
    ("H4. con lai khong gioi han", '"không giới hạn số phiên" if tt.con_lai is None else', '"còn 0 phiên" if tt.con_lai is None else'),
    ("H5. tieu de dang cho doi chieu", 'f"Đang chờ · {_TEN_CHIEU[tt.chieu]}"', 'f"Đang chờ · {_TEN_CHIEU[C.GIAM]}"'),
    # ── chin phat cuoi cua §6 hang 2 (nhap va loi) ──
    ("9. import paper_trading", "import cau_truc_gia as C\n", "import cau_truc_gia as C\nimport paper_trading  # noqa\n"),
    ("9b. import os (ngoai danh sach trang)", "import cau_truc_gia as C\n", "import cau_truc_gia as C\nimport os  # noqa\n"),
    ("9c. import tools.do_dow_cau_truc", "import cau_truc_gia as C\n", "import cau_truc_gia as C\nfrom tools import do_dow_cau_truc  # noqa\n"),
    ("9d. import backtest", "import cau_truc_gia as C\n", "import cau_truc_gia as C\nimport backtest  # noqa\n"),
    ("9e. bo import cau_truc_gia, tu go hang so", "import cau_truc_gia as C\n",
     "class C:  # noqa\n    TANG, GIAM, CAP_SWING, CHOCH = 'tang', 'giam', 'swing', 'CHOCH'\n"),
    ("10. chuoi hien thi chua 'du bao'", '"Chưa đủ bằng chứng"', '"Chưa đủ bằng chứng, dự báo"'),
    ("10b. chuoi hien thi chua tu 'se'", '"chưa có đảo chiều swing nào ở cả hai chuỗi"', '"chưa có đảo chiều swing nào, sẽ chờ"'),
    ("10c. chuoi hien thi chua 'khuyen nghi'", "không giới hạn số phiên", "không giới hạn số phiên, khuyến nghị chờ"),
    ("10d. xac nhan noi la xu huong chinh", 'tieu_de = f"Đã xác nhận · {_TEN_CHIEU[tt.chieu]}"',
     'tieu_de = f"Đã xác nhận xu hướng chính · {_TEN_CHIEU[tt.chieu]}"'),
    ("10e. dang cho noi tin hieu mua", '"Đang chờ · ', '"Đang chờ, tín hiệu mua · '),
]

CHO_PHEP = str(WT / "tests" / "test_cau_truc_gia.py")
GAC_NHAP = [
    ("N1. bo dong dow_hai_chi_so.py khoi CHO_PHEP_NHAP", 'tools/mo_ta_cau_truc_gia.py", "dow_hai_chi_so.py"}',
     'tools/mo_ta_cau_truc_gia.py"}'),
    ("N2. thay ten mo-dun trong CHO_PHEP_NHAP bang ten sai", '"tools/mo_ta_cau_truc_gia.py", "dow_hai_chi_so.py"}',
     '"tools/mo_ta_cau_truc_gia.py", "dow_hai_chi_so_x.py"}'),
]


def _file_la() -> bool:
    """Them mot file goc repo nhap mo-dun: gac nhap phai do. Hoan tra bang xoa; tra True neu gac do."""
    duong = WT / "ke_hoach_la.py"
    duong.write_text("import dow_hai_chi_so\n", encoding="utf-8")
    try:
        kq = subprocess.run([sys.executable, "-m", "pytest", "tests/test_dow_hai_chi_so_buc_tuong.py", "-q", "-x",
                             "-p", "no:cacheprovider"], cwd=str(WT), capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    finally:
        duong.unlink()
    return kq.returncode != 0


if __name__ == "__main__":
    che_do = sys.argv[1] if len(sys.argv) > 1 else "tat_ca"
    song: list[str] = []
    tong = 0
    if che_do in ("mo_dun", "tat_ca"):
        tong += len(MO_DUN)
        song += dot_bien_bo(MD, MO_DUN, LENH)
    if che_do in ("gac_nhap", "tat_ca"):
        tong += len(GAC_NHAP) + 1
        song += dot_bien_bo(CHO_PHEP, GAC_NHAP, LENH_NHAP)
        da_giet = _file_la()
        print(f"  {'DO  ' if da_giet else 'SONG'}  N3. file la nhap dow_hai_chi_so")
        if not da_giet:
            song.append("N3. file la nhap dow_hai_chi_so")
    print(f"\nTONG: {tong - len(song)}/{tong} do")
    if song:
        print("SONG SOT: " + ", ".join(song))
    sys.exit(1 if song else 0)
