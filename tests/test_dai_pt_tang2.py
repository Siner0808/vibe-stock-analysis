"""Dải 99% của PT ở Tầng 2 (C4, BƯỚC 294): công thức khai TRƯỚC ở `docs/thiet-ke-c4-thi-truong-gia.md` mục 19.8.

Ba điểm dưới đây là ba số của mục 19.5 (BƯỚC 293) tính bằng một script tạm; test này đòi dụng cụ của BƯỚC 294 cho
cùng số, nên công thức khai trước KHÔNG đổi giữa hai BƯỚC. Probit đọc từ file hiệu chuẩn của Lát 2, không gõ tay.
"""
from __future__ import annotations

import json
import sys
from math import comb
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import dai_pt_tang2_thi_truong_gia as D  # noqa: E402


def test_probit_doc_tu_file_hieu_chuan_Lat_2():
    j = json.loads((GOC / "docs" / "thi-truong-gia-hieu-chuan.json").read_text(encoding="utf-8"))["mde80"]["probit"]
    assert D.doc_probit() == (float(j["a"]), float(j["b"]))


@pytest.mark.parametrize("delta, thap, cao, p_lam_tron", [
    (0.0304, 5, 23, 0.134),    # `bo_momentum_score` ở 2×, dòng hạt 9001 (mục 19.5: P ≈ 13,4%, dải 5–23)
    (0.0281, 4, 20, 0.113),    # `bo_sr_score` ở 2× (mục 19.5: 11,3%, 4–20)
    (0.0066, 0, 6, 0.016),     # `mono_volume_score` = G ở 2× (mục 19.4 điều 2: 1,6%, 0–6)
])
def test_dai_khop_ba_so_cua_muc_19_5(delta, thap, cao, p_lam_tron):
    a, b = D.doc_probit()
    r = D.dai_tu_delta(delta, a, b)
    assert (r["dai_thap"], r["dai_cao"]) == (thap, cao)
    assert round(r["p_qua"], 3) == p_lam_tron
    assert r["R"] == 100


def test_dai_la_hai_phia_0_5_phan_tram_moi_duoi_tinh_lai_doc_lap():
    """Dải phải BAO ĐÚNG ≥ 99%, và bỏ bớt một phía ở mỗi đầu thì tụt xuống dưới 99%: kiểm cả hai phía và độ khít."""
    p, n = 0.1337, 100
    thap, cao = D.dai_99(p, n)
    pmf = [comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n + 1)]
    assert sum(pmf[thap:cao + 1]) >= 0.99
    assert sum(pmf[:thap]) <= 0.005 + 1e-12            # đuôi dưới bị cắt không vượt 0,5%
    assert sum(pmf[:thap + 1]) >= 0.005                 # thấp là k NHỎ NHẤT có CDF ≥ 0,005
    assert sum(pmf[:cao]) < 0.995 <= sum(pmf[:cao + 1])  # cao là k NHỎ NHẤT có CDF ≥ 0,995


def test_bien_p_bang_0_va_1():
    assert D.dai_99(0.0, 100) == (0, 0)
    assert D.dai_99(1.0, 100) == (100, 100)
    with pytest.raises(ValueError):
        D.dai_99(1.2, 100)
