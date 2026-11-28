"""Vong dot bien BUOC 307 (50 phat: 29 tren chuoi_chi_so.py, 21 tren cau_truc_gia.py).

Chay tu goc repo:  ./.venv/Scripts/python.exe -X utf8 docs/do-307/dot_bien_307.py <chuoi|cau_truc>
Ma thoat 1 neu con phat SONG (rong la du do). Moi phat chay pytest tren file gac cua no, roi HOAN TRA tung byte.
"""
from __future__ import annotations

import os
import pathlib
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
WT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WT / "tools"))
os.chdir(WT)
from va_an_toan import dot_bien_bo  # noqa: E402

CHUOI = [
    ("1000 -> 1 (he so thang)", '{("iboard", "VNMIDCAP"): 1000}', '{("iboard", "VNMIDCAP"): 1}'),
    ("bo cong do lon o lay_chuoi", "        if tham_chieu is not None:\n            ly = kiem_do_lon(",
     "        if False:\n            ly = kiem_do_lon("),
    ("kiem_do_lon luon qua", "    if thap <= ty <= cao:\n        return None", "    if True:\n        return None"),
    ("bien duoi mo (<)", "    if thap <= ty <= cao:", "    if thap < ty <= cao:"),
    ("bien tren mo (<)", "    if thap <= ty <= cao:", "    if thap <= ty < cao:"),
    ("dai 0.2 -> 0.1", "DAI_DO_LON = (0.2, 5.0)", "DAI_DO_LON = (0.1, 5.0)"),
    ("dai 5.0 -> 50", "DAI_DO_LON = (0.2, 5.0)", "DAI_DO_LON = (0.2, 50.0)"),
    ("trung vi -> trung binh", "ty = float((a.loc[chung] / b.loc[chung]).median())",
     "ty = float((a.loc[chung] / b.loc[chung]).mean())"),
    ("lay_ba_chuoi khong truyen tham chieu", "lay_chuoi(ten, den, bay_gio, tham_chieu=tham_chieu, **kw)",
     "lay_chuoi(ten, den, bay_gio, tham_chieu=None, **kw)"),
    ("hoan VNMIDCAP iboard -> VNMID", '("VNMidcap", "iboard"): "VNMIDCAP"', '("VNMidcap", "iboard"): "VNMID"'),
    ("hoan VNMID vps -> VNMIDCAP", '("VNMidcap", "vps"): "VNMID"', '("VNMidcap", "vps"): "VNMIDCAP"'),
    ("hoan VNMID vndirect -> VNMIDCAP", '("VNMidcap", "vndirect"): "VNMID"', '("VNMidcap", "vndirect"): "VNMIDCAP"'),
    ("can bang HOP thay GIAO", 'pd.Index(a.df["time"]).intersection(pd.Index(b.df["time"]))',
     'pd.Index(a.df["time"]).union(pd.Index(b.df["time"]))'),
    ("giu nen cuoi do", 'bo_cuoi = bool(len(df)) and nen_cuoi_dang_do(df["time"].iloc[-1], bay_gio)', "bo_cuoi = False"),
    ("giu cot volume", "        df = df[list(CAC_COT)].reset_index(drop=True)", "        df = df.reset_index(drop=True)"),
    ("nguong nen mot gia bi lo", "    if ty > NGUONG_NEN_MOT_GIA:", "    if False:"),
    ("nguong > thanh >=", "    if ty > NGUONG_NEN_MOT_GIA:", "    if ty >= NGUONG_NEN_MOT_GIA:"),
    ("nguong 0.005 -> 0.05", "NGUONG_NEN_MOT_GIA = 0.005", "NGUONG_NEN_MOT_GIA = 0.05"),
    ("nguong 0.005 -> 0.001", "NGUONG_NEN_MOT_GIA = 0.005", "NGUONG_NEN_MOT_GIA = 0.001"),
    ("ty le nen mot gia chi dem high==low", '    return float(((df["high"] == df["low"]) & (df["low"] == df["close"])).mean())',
     '    return float((df["high"] == df["low"]).mean())'),
    ("ty le nen mot gia chi dem low==close", '    return float(((df["high"] == df["low"]) & (df["low"] == df["close"])).mean())',
     '    return float((df["low"] == df["close"]).mean())'),
    ("TU_NGAY doi", "TU_NGAY = date(2017, 8, 24)", "TU_NGAY = date(2018, 1, 2)"),
    ("lich su ngan > -> <", 'ngan = df["time"].iloc[0].date() > TU_NGAY + timedelta(days=DUNG_SAI_NGAY_DAU)',
     'ngan = df["time"].iloc[0].date() < TU_NGAY + timedelta(days=DUNG_SAI_NGAY_DAU)'),
    ("ngay cuoi chung = min", "    cuoi = chung.max()", "    cuoi = chung.min()"),
    ("thua dem >= ", 'int((r.df["time"] > cuoi).sum())', 'int((r.df["time"] >= cuoi).sum())'),
    ("scale ap cho moi iboard", "        if (nguon.ten, ma) in HE_SO_THANG:", '        if nguon.ten == "iboard" and ma == "VN30":'),
    ("loai nguon khong ghi ly do", "            da_thu.append((nguon.ten, e.da_thu[0][1]))", "            da_thu.append((nguon.ten, ''))"),
    ("thong bao bo ten nguon", 'f"{TEN_HIEN[n] if n in TEN_HIEN else n} ({ly})"', 'f"{n} ({ly})"'),
    ("dong du kien lam tron", ':.4f}".replace(".", ",")', ':.2f}".replace(".", ",")'),
]

CAU_TRUC = [
    ("la_chi_so bi lo (dung sai 5 diem)", "    if la_chi_so:\n        return NUA_BUOC_CHI_SO", "    if False:\n        return NUA_BUOC_CHI_SO"),
    ("NUA 0.005 -> 5.0", "NUA_BUOC_CHI_SO = 0.005", "NUA_BUOC_CHI_SO = 5.0"),
    ("NUA 0.005 -> 0.5", "NUA_BUOC_CHI_SO = 0.005", "NUA_BUOC_CHI_SO = 0.5"),
    ("NUA 0.005 -> 0.05", "NUA_BUOC_CHI_SO = 0.005", "NUA_BUOC_CHI_SO = 0.05"),
    ("NUA 0.005 -> 0.001", "NUA_BUOC_CHI_SO = 0.005", "NUA_BUOC_CHI_SO = 0.001"),
    ("NUA 0.005 -> 0", "NUA_BUOC_CHI_SO = 0.005", "NUA_BUOC_CHI_SO = 0.0"),
    ("_nhan khong truyen la_chi_so", "abs(d) <= _nua(gia, he_so_gia, san, la_chi_so)", "abs(d) <= _nua(gia, he_so_gia, san, False)"),
    ("_cuc_tri khong truyen la_chi_so", "nua = _nua(tot.dong, he_so_gia, san, la_chi_so)", "nua = _nua(tot.dong, he_so_gia, san, False)"),
    ("_buoc_may khong truyen cho _cuc_tri", "c = _cuc_tri(dong, loai, tt.he_so_gia, tt.san, tt.la_chi_so)",
     "c = _cuc_tri(dong, loai, tt.he_so_gia, tt.san)"),
    ("_pivot khong truyen cho _nhan", "nhan=_nhan(loai, c.dong, truoc, tt.he_so_gia, tt.san, tt.la_chi_so),",
     "nhan=_nhan(loai, c.dong, truoc, tt.he_so_gia, tt.san),"),
    ("_buoc_fractal khong truyen", "nua = _nua(tam.dong, tt.he_so_gia, tt.san, tt.la_chi_so)", "nua = _nua(tam.dong, tt.he_so_gia, tt.san, False)"),
    ("_vuot_moc khong truyen", "nua = _nua(gia, tsk.he_so_gia, tsk.san, tsk.la_chi_so)", "nua = _nua(gia, tsk.he_so_gia, tsk.san, False)"),
    ("khoi_tao_su_kien bo co", "caps=(_CapSK(), _CapSK()), la_chi_so=tt.la_chi_so)", "caps=(_CapSK(), _CapSK()), la_chi_so=False)"),
    ("khoi_tao bo co", "caps=(_Cap(), _Cap()), la_chi_so=bool(la_chi_so))", "caps=(_Cap(), _Cap()), la_chi_so=False)"),
    ("doc_cau_truc khong truyen cho chuan_bi_nen", "nens = chuan_bi_nen(df, san, la_chi_so)", "nens = chuan_bi_nen(df, san)"),
    ("doc_cau_truc khong truyen cho khoi_tao", "tt = khoi_tao(ho, tham_so, san, he_so_gia, la_chi_so)", "tt = khoi_tao(ho, tham_so, san, he_so_gia)"),
    ("mac dinh la_chi_so True", "tham_so: tuple | None = None, la_chi_so: bool = False) -> CauTruc:",
     "tham_so: tuple | None = None, la_chi_so: bool = True) -> CauTruc:"),
    ("chi so van co khoa_bien", "kb = None if la_chi_so else _khoa_bien(", "kb = _khoa_bien("),
    ("chi so van co khong_giao_dich", 'if "volume" in df.columns and not la_chi_so:', 'if "volume" in df.columns:'),
    ("co phieu mat khoa_bien", "kb = None if la_chi_so else _khoa_bien(", "kb = None if True else _khoa_bien("),
    ("co phieu doi nua buoc", "    return nua_buoc(gia, he_so_gia, san)\n\n\ndef _nhan", "    return nua_buoc(gia, he_so_gia, san) * 2\n\n\ndef _nhan"),
]

if __name__ == "__main__":
    che_do = sys.argv[1] if len(sys.argv) > 1 else ""
    if che_do == "chuoi":
        song = dot_bien_bo(str(WT / "chuoi_chi_so.py"), CHUOI,
                           ["-m", "pytest", "tests/test_chuoi_chi_so.py", "-q", "-x", "-p", "no:cacheprovider"])
    elif che_do == "cau_truc":
        song = dot_bien_bo(str(WT / "cau_truc_gia.py"), CAU_TRUC,
                           ["-m", "pytest", "tests/test_cau_truc_gia.py", "-q", "-x", "-p", "no:cacheprovider"])
    else:
        sys.exit("dung: dot_bien_307.py <chuoi|cau_truc>")
    sys.exit(1 if song else 0)
