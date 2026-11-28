"""BUOC 307 - tinh lai dau van tay co phieu (`DAU_VAN_TAY_CO_PHIEU` o tests/test_cau_truc_gia.py).

Dau van tay phai tinh tren `cau_truc_gia.py` CHUA SUA (main @ 9dc7672). Cach tai lap:
  git worktree add <thu_muc> 9dc7672
  chep tests/test_cau_truc_gia.py va docs/do-307/van_tay_co_phieu.py cua nhanh BUOC 307 vao <thu_muc> (cung duong dan)
  trong <thu_muc>:  python -X utf8 docs/do-307/van_tay_co_phieu.py   ->  ('85ac9f41...0f69', 27)
Tren nhanh BUOC 307 lenh nay in CUNG gia tri (cho thay `la_chi_so=False` khong doi mot byte).
Chi dung bang tay dung tay (khong du lieu that cua ba chi so; buc tuong DO 39).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
GOC = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))
spec = importlib.util.spec_from_file_location("test_cau_truc_gia_307", GOC / "tests" / "test_cau_truc_gia.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print(m._dau_van_tay(m._bang_vang()))
