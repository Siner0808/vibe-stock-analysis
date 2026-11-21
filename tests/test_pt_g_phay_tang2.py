"""PT ở Tầng 2 sau quyết định 21/11/2026 (C4, BƯỚC 294): hàng PT của mục 6 phải khớp bản ghi đo ở dòng hạt 1.

Số trong đặc tả được đọc từ `docs/thi-truong-gia-g-phay.json` (bản ghi của lượt đo), không gõ tay ở đây. Test canh ba thứ:
(1) bản ghi tự nhất quán với công thức đã khai TRƯỚC ở mục 19.8 (dải tính lại từ ΔIC_true bằng dụng cụ đã commit trước lượt đo);
(2) các điều kiện DỪNG khai trước đều không bị chạm (nếu bị chạm thì bản ghi không được nằm trong repo);
(3) hàng PT trong đặc tả nói đúng G′, đúng dải, giữ vế NULL và R, và quyết định nguyên văn của người dùng có mặt.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import dai_pt_tang2_thi_truong_gia as D  # noqa: E402

BAN_GHI = json.loads((GOC / "docs" / "thi-truong-gia-g-phay.json").read_text(encoding="utf-8"))
DAC_TA = (GOC / "docs" / "thiet-ke-c4-thi-truong-gia.md").read_text(encoding="utf-8")
HIEU_CHUAN = json.loads((GOC / "docs" / "thi-truong-gia-hieu-chuan.json").read_text(encoding="utf-8"))
CAU_NGUOI_DUNG = "làm theo đề xuất của bạn đi, phương án nào tốt nhất thì làm"


def _hang_PT() -> str:
    dong = [d for d in DAC_TA.splitlines() if d.startswith("| **PT** |")]
    assert len(dong) == 1, "mục 6 phải có đúng MỘT hàng PT"
    return dong[0]


def test_ban_ghi_o_dong_hat_1_hat_thu_ba_2_va_chi_so_ngoai_cac_khoi_cua_Lat_2():
    assert BAN_GHI["luong"] == 1 and BAN_GHI["hat_thu_ba"] == 2 and BAN_GHI["g_phay"] == "bo_momentum_score"
    from hieu_chuan_thi_truong_gia import CHI_SO_GOC, BUOC_DIEM
    khoi = [(g, g + 10 * BUOC_DIEM) for g in CHI_SO_GOC.values()]
    for c in BAN_GHI["chi_so_2x"] + BAN_GHI["chi_so_null"]:
        assert not any(lo <= c < hi for lo, hi in khoi), f"chi_so {c} chạm khối của Lát 2"
        assert str(c) in DAC_TA, f"chi_so {c} phải được khai trong đặc tả (mục 19.8)"
    assert len(set(BAN_GHI["chi_so_2x"] + BAN_GHI["chi_so_null"])) == len(BAN_GHI["chi_so_2x"] + BAN_GHI["chi_so_null"])


def test_probit_cua_ban_ghi_la_probit_Tang_1_trong_file_hieu_chuan():
    p = HIEU_CHUAN["mde80"]["probit"]
    assert (BAN_GHI["probit"]["a"], BAN_GHI["probit"]["b"]) == (p["a"], p["b"])


def test_dai_trong_ban_ghi_tinh_lai_duoc_tu_delta_bang_dung_cu_khai_truoc():
    r = D.dai_tu_delta(BAN_GHI["x2"]["delta_ic"], BAN_GHI["probit"]["a"], BAN_GHI["probit"]["b"], BAN_GHI["R"])
    assert (r["dai_thap"], r["dai_cao"]) == (BAN_GHI["dai_thap"], BAN_GHI["dai_cao"])
    assert r["p_qua"] == pytest.approx(BAN_GHI["p_qua"], abs=1e-12)
    assert BAN_GHI["R"] == 100


def test_khong_dieu_kien_DUNG_nao_bi_cham():
    x = BAN_GHI["x2"]
    assert x["delta_ic"] / x["se"] > 2                                    # S1
    assert abs(BAN_GHI["lech_so_voi_9001"]["so_se_gop"]) <= 3             # S2
    se_gop = (x["se"] ** 2 + BAN_GHI["tham_chieu_9001"]["se"] ** 2) ** 0.5
    assert BAN_GHI["lech_so_voi_9001"]["se_gop"] == pytest.approx(se_gop, abs=1e-12)
    assert BAN_GHI["lech_so_voi_9001"]["hieu"] == pytest.approx(x["delta_ic"] - BAN_GHI["tham_chieu_9001"]["delta_ic"], abs=1e-12)
    assert BAN_GHI["dai_thap"] > 0                                        # S3
    nl = BAN_GHI["null"]
    assert nl["spec_ngoai_hai_se"] == [] and nl["khong_ok"] == 0          # S4
    assert all(abs(v["delta_ic"]) < 2 * v["se"] for v in nl["spec"].values())
    assert len(nl["spec"]) == 12


def test_hang_PT_noi_G_phay_dung_dai_va_giu_ve_NULL_va_R():
    pt = _hang_PT()
    thap, cao = BAN_GHI["dai_thap"], BAN_GHI["dai_cao"]
    assert "`bo_momentum_score`" in pt
    assert f"[{thap} ; {cao}]/100" in pt
    assert "báo động ở NULL ≤ 12/100" in pt
    assert "≥ 85/100" not in pt                                           # vế G cũ đã được viết lại
    assert pt.count("| NULL, 2× | 100 |") == 1                           # thị trường và R = 100 không đổi


def test_quyet_dinh_nguyen_van_cua_nguoi_dung_o_muc_19_va_dong_trich_duoi_bang_muc_6():
    muc_19_8 = DAC_TA.split("### 19.8", 1)[1].split("### 19.9", 1)[0]
    assert f"*\"{CAU_NGUOI_DUNG}\"*" in muc_19_8                         # quyết định nguyên văn nằm Ở mục 19.8
    duoi_bang = DAC_TA.split("| **PT** |", 1)[1].split("**Báo cáo, không phán:**", 1)[0]
    assert CAU_NGUOI_DUNG in duoi_bang and "mục 19" in duoi_bang


def test_ma_lenh_khai_truoc_co_mat_trong_dac_ta():
    assert re.fullmatch(r"[0-9a-f]{40}", BAN_GHI["ma_lenh_khai_truoc"])
    assert BAN_GHI["ma_lenh_khai_truoc"][:7] in DAC_TA
