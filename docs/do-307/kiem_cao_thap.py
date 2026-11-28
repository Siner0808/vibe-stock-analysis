"""BUOC 307 - kiem `high`/`low` THAT cua chuoi chi so (dac ta Dow phan 2 muc 6, hang 1; phat hien cua BUOC 306).

Chay tu goc repo:  ./.venv/Scripts/python.exe -X utf8 docs/do-307/kiem_cao_thap.py
Keo cac nguon cua `nguon_gia_cong_khai.CHUOI_CHI_SO` cho VN30 / VNMidcap / VN100 tu `chuoi_chi_so.TU_NGAY` va IN chi DU KIEN
DU LIEU: so hang, ngay dau/cuoi, ngay trung, ty le hang high == low == close, ty le open == close, so hang high/low nam
ngoai [open, close], trung vi (high - low). KHONG nap `cau_truc_gia`, khong dem swing hay lat (buc tuong DO 39).
"""
from __future__ import annotations

import pathlib
import sys
import time
from datetime import date, datetime, timezone

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import pandas as pd

import chuoi_chi_so as CC
import nguon_gia_cong_khai as ng

assert "cau_truc_gia" not in sys.modules, "buc tuong DO 39: cau_truc_gia khong duoc nap"
TU, DEN = CC.TU_NGAY, date.today()
TS_TU = int(datetime(TU.year, TU.month, TU.day, tzinfo=timezone.utc).timestamp()) - 86400
TS_DEN = int(datetime(DEN.year, DEN.month, DEN.day, tzinfo=timezone.utc).timestamp()) + 86400

print(f"cua so {TU} -> {DEN}; thu tu nguon = {[n.ten for n in ng.CHUOI_CHI_SO]}")
for chuoi in CC.CHUOI:
    for nguon in ng.CHUOI_CHI_SO:
        ma = CC.MA_THEO_NGUON[(chuoi, nguon.ten)]
        try:
            j = ng._goi_co_thu_lai(nguon.url("chi_so", ma, TS_TU, TS_DEN), nguon.accept, ng._http_json,
                                   time.sleep, time.monotonic, 1.0)
            t, o, h, l, c, v = nguon.doc(j)
        except ng.NguonGiaLoi as e:
            print(f"{chuoi:9s}|{nguon.ten:8s}|{ma:9s}| LOI: {e}")
            continue
        ts = pd.to_numeric(pd.Series(t), errors="coerce")
        ngay = (pd.to_datetime(ts.astype("int64"), unit="s") + pd.Timedelta(hours=7)).dt.normalize()
        df = pd.DataFrame({"ngay": ngay, "o": pd.to_numeric(pd.Series(o)), "h": pd.to_numeric(pd.Series(h)),
                           "l": pd.to_numeric(pd.Series(l)), "c": pd.to_numeric(pd.Series(c))})
        df = df[df["ngay"] >= pd.Timestamp(TU)]
        ngoai = int(((df.h < df[["o", "c"]].max(axis=1)) | (df.l > df[["o", "c"]].min(axis=1))).sum())
        print(f"{chuoi:9s}|{nguon.ten:8s}|{ma:9s}| hang={len(df)} trung_ngay={int(df['ngay'].duplicated().sum())} "
              f"dau={df.ngay.min().date()} cuoi={df.ngay.max().date()} | "
              f"h==l==c={CC.ty_le_nen_mot_gia(df.rename(columns={'h': 'high', 'l': 'low', 'c': 'close'})):.4f} "
              f"o==c={float((df.o == df.c).mean()):.4f} h/l_ngoai_o-c={ngoai} trung_vi(h-l)={float((df.h - df.l).median()):.3f}")
print("cau_truc_gia da nap:", "cau_truc_gia" in sys.modules)
