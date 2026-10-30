"""Gác BẢN GHI cấu hình KTC đã khoá ở BƯỚC 248 (`docs/thiet-ke-c1-san-dau.md` mục 8.4b; `docs/san-dau-do-phu.json`,
khoá `cau_hinh_khoa`). ĐO 34 (Dow), Lát 4, in cấu hình KTC của nó và phải KHỚP bản ghi này, lệch là K0
(`khop_cau_hinh_khoa`); nên ở đây:
  1. mặc định trong MÃ (chữ ký của `ktc_khoi_co_cap`, hằng số) BẰNG bản ghi trong file;
  2. bản ghi là ứng viên ĐẦU TIÊN đạt (mọi ứng viên trước nó KHÔNG đạt, nó đạt cả 9 ô, đúng thứ tự khai) — kiểm cả
     chuỗi lẫn máy kiểm (`vi_pham_cau_hinh_khoa`) bằng bảng tổng hợp xấu;
  3. `khop_cau_hinh_khoa` báo từng chỗ lệch;
  4. nhãn mà `bang` in nói đúng cấu hình khoá và độ phủ lấy từ chính file.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.append(str(GOC / "tools"))

import san_dau as sd  # noqa: E402
from test_san_dau import _sach_cache_phan_tich  # noqa: E402

assert _sach_cache_phan_tich  # fixture autouse nhập từ test_san_dau, giữ trong module này

DUONG_DO_PHU = GOC / "docs" / "san-dau-do-phu.json"
THU_TU_KHAI = ["L42", "L63", "L21", "PW", "L10", "N13", "L5"]      # đặc tả 8.4b khoản 4 (chép tay: đổi thứ tự là đổi đặc tả)


def _bang() -> dict:
    return json.loads(DUONG_DO_PHU.read_text(encoding="utf-8"))


# ── 1. mã = bản ghi ───────────────────────────────────────────────────────────────────────────
def test_cau_hinh_khoa_trong_file_bang_cau_hinh_suy_ra_tu_ma():
    assert _bang()["cau_hinh_khoa"] == sd.cau_hinh_khoa()


def test_mac_dinh_cua_ktc_khoi_co_cap_bang_ban_ghi_trong_file():
    kh = _bang()["cau_hinh_khoa"]
    mac_dinh = {k: p.default for k, p in inspect.signature(sd.ktc_khoi_co_cap).parameters.items()}
    assert mac_dinh["do_dai"] == kh["do_dai_khoi"] == "PW"
    assert mac_dinh["vong"] == kh["vong"] == 5000
    assert mac_dinh["hat"] == kh["hat_bootstrap"] == 0
    assert list(sd.PHAN_VI_KTC) == kh["phan_vi"] == [2.5, 97.5]
    assert kh["nhan"] == sd.nhan_do_dai(mac_dinh["do_dai"]) == "PW"


def test_ktc_khong_tham_so_dung_cau_hinh_khoa_va_khop_ban_ghi():
    rng = __import__("numpy").random.default_rng(3)
    a, b = rng.standard_normal(120), rng.standard_normal(120)
    for k in (sd.ktc_khoi_co_cap(a), sd.ktc_khoi_co_cap(a, b)):
        assert (k["do_dai_yeu_cau"], k["vong"], k["hat"], k["phan_vi"]) == ("PW", 5000, 0, [2.5, 97.5])
        assert sd.khop_cau_hinh_khoa(k, _bang()["cau_hinh_khoa"]) == []


def test_ktc_co_nhan_va_bang_dung_mac_dinh_khoa():
    import numpy as np
    a = np.random.default_rng(4).standard_normal(90)
    kq = sd.ktc_co_nhan(a, None, "tho", _bang())
    assert sd.khop_cau_hinh_khoa(kq["ktc"], _bang()["cau_hinh_khoa"]) == []
    assert "khối=PW" in kq["dong"] and "độ phủ đo được" in kq["dong"]


# ── 2. ứng viên đầu tiên đạt ──────────────────────────────────────────────────────────────────
def test_file_la_ung_vien_dau_tien_dat_dung_thu_tu_khai():
    bang = _bang()
    assert sd.vi_pham_cau_hinh_khoa(bang) == []
    assert [m["nhan"] for m in bang["ung_vien_da_thu"]] == THU_TU_KHAI[:4]               # dừng ở PW
    assert [nhan for nhan in map(sd.nhan_do_dai, sd.UNG_VIEN_KTC)] == THU_TU_KHAI
    *truoc, khoa = bang["ung_vien_da_thu"]
    assert [m["dat"] for m in truoc] == [False] * 3 and khoa["dat"] is True
    for m in truoc:
        assert any(not sd.o_dat(p) for t in m["do_phu"].values() for p in t.values()), m["nhan"]
    cac_o = [p for t in khoa["do_phu"].values() for p in t.values()]
    assert len(cac_o) == 9 and all(p >= 0.90 for p in cac_o), cac_o
    assert bang["do_phu"] == {"PW": khoa["do_phu"]}


def test_ung_vien_thu_nhat_va_hai_la_khong_xac_dinh_o_n_40_vi_khoi_dai_hon_chuoi():
    bang = _bang()
    for m in bang["ung_vien_da_thu"][:2]:
        assert m["do_phu"]["40"] == {"cap": None, "mot_chuoi": None, "tho": None}, m["nhan"]


def test_kiem_lai_hai_hat_va_can_thang_duoc_ghi_va_co_the_dung_duoi_90_ma_khong_doi_cau_hinh():
    bang = _bang()
    assert set(bang["kiem_lai"]) == {"hat1", "hat2"} and bang["cang_thang"]["phi"] == sd.PHI_CANG_THANG
    for ten, t in bang["kiem_lai"].items():
        assert set(t) == {"40", "113", "252"}, ten
    assert set(bang["cang_thang"]["do_phu"]) == {"PW"}
    # chúng chỉ để BÁO CÁO: cấu hình khoá vẫn là PW dù ô căng thẳng dưới 90%
    assert bang["cau_hinh_khoa"]["nhan"] == "PW"


# ── máy kiểm bị đột biến bằng bảng tổng hợp ───────────────────────────────────────────────────
def _o(p: float) -> dict:
    return {str(n): {d: p for d in sd.DANG_KTC} for n in sd.LUOI_N}


def _bang_tong_hop(truoc_dat: bool = False, khoa_dat: bool = True, thu_tu=("L42", "L63", "L21", "PW"),
                   p_rieng: dict | None = None) -> dict:
    uv = []
    for nhan in thu_tu:
        la_khoa = nhan == "PW"
        p = 0.95 if (khoa_dat if la_khoa else truoc_dat) else 0.5
        p = (p_rieng or {}).get(nhan, p)
        uv.append({"nhan": nhan, "do_phu": _o(p), "dat": ung_dat(p)})
    khoa = next((m for m in uv if m["nhan"] == "PW"), uv[-1])
    b = sd.dung_bang_do_phu({"PW": khoa["do_phu"]}, ung_vien_da_thu=[(m["nhan"], m["do_phu"]) for m in uv])
    return json.loads(json.dumps(b))        # như file thật: không dùng chung đối tượng giữa `do_phu` và ứng viên cuối


def ung_dat(p: float) -> bool:
    return p >= 0.90


def test_vi_pham_cau_hinh_khoa_chap_nhan_chuoi_dung_va_bat_tung_loi():
    assert sd.vi_pham_cau_hinh_khoa(_bang_tong_hop()) == []
    assert sd.vi_pham_cau_hinh_khoa(_bang_tong_hop(truoc_dat=True)), "ứng viên trước đã đạt mà không chốt nó"
    assert sd.vi_pham_cau_hinh_khoa(_bang_tong_hop(khoa_dat=False)), "cấu hình khoá không đạt"
    assert sd.vi_pham_cau_hinh_khoa(_bang_tong_hop(thu_tu=("L63", "L42", "L21", "PW"))), "sai thứ tự khai"
    assert sd.vi_pham_cau_hinh_khoa(_bang_tong_hop(thu_tu=("L42", "L63", "L21"))), "chưa tới cấu hình khoá"
    assert sd.vi_pham_cau_hinh_khoa(_bang_tong_hop(thu_tu=("L42", "L63", "L21", "PW", "L10"))), "thử thêm ứng viên SAU khi chốt"
    b = _bang_tong_hop()
    b["ung_vien_da_thu"][0]["dat"] = True
    assert sd.vi_pham_cau_hinh_khoa(b), "cờ 'dat' không khớp bảng"
    b = _bang_tong_hop()
    b["do_phu"]["PW"]["40"]["cap"] = 0.99
    assert sd.vi_pham_cau_hinh_khoa(b), "do_phu khác bảng của ứng viên cuối"
    b = _bang_tong_hop()
    b["ung_vien_da_thu"][-1]["do_phu"]["40"]["cap"] = None
    assert sd.vi_pham_cau_hinh_khoa(b), "ô None không đạt"
    # ứng viên cuối ĐẠT và đứng sau chuỗi không-đạt, nhưng KHÔNG phải cấu hình mà mã khoá: chỉ luật "cuối = khoá" bắt
    b = _bang_tong_hop(thu_tu=("L42", "L63", "L21"), p_rieng={"L21": 0.95})
    assert [s for s in sd.vi_pham_cau_hinh_khoa(b)] == ["ung vien cuoi cung duoc thu L21 khong phai cau hinh khoa PW"]
    # bảng hợp lệ nhưng THIẾU chuỗi ứng viên đã thử (rỗng hay vắng) thì không tin được
    for thieu in ([], None):
        b = _bang_tong_hop()
        if thieu is None:
            b.pop("ung_vien_da_thu")
        else:
            b["ung_vien_da_thu"] = thieu
        assert sd.vi_pham_cau_hinh_khoa(b) == ["thieu ung_vien_da_thu"]
    assert sd.vi_pham_cau_hinh_khoa({}) and sd.vi_pham_cau_hinh_khoa(None)


# ── 3. khớp bản ghi ───────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("sua, trung", [({"do_dai": 10}, "do_dai_khoi"), ({"do_dai": "N13"}, "do_dai_khoi"),
                                        ({"vong": 1000}, "vong"), ({"hat": 1}, "hat_bootstrap")])
def test_khop_cau_hinh_khoa_bao_tung_cho_lech(sua, trung):
    import numpy as np
    a = np.random.default_rng(8).standard_normal(100)
    k = sd.ktc_khoi_co_cap(a, **sua)
    loi = sd.khop_cau_hinh_khoa(k, _bang()["cau_hinh_khoa"])
    assert len(loi) == 1 and loi[0].startswith(trung), loi


def test_khop_cau_hinh_khoa_bao_lech_phan_vi_va_thieu_khoa():
    import numpy as np
    k = sd.ktc_khoi_co_cap(np.random.default_rng(9).standard_normal(100))
    ban_ghi = dict(_bang()["cau_hinh_khoa"])
    assert sd.khop_cau_hinh_khoa(k, ban_ghi) == []
    k2 = dict(k, phan_vi=[5.0, 95.0])
    assert [s.split(":")[0] for s in sd.khop_cau_hinh_khoa(k2, ban_ghi)] == ["phan_vi"]
    assert sd.khop_cau_hinh_khoa({}, ban_ghi), "ktc thiếu mọi khoá thì không khớp"
    ban_ghi.pop("vong")
    assert any(s.startswith("vong") for s in sd.khop_cau_hinh_khoa(k, ban_ghi))


def test_khop_doi_khi_yeu_cau_la_so_nhung_ban_ghi_la_quy_tac():
    """Dù quy tắc PW giải ra đúng số, cái được SO là cái YÊU CẦU: gọi với `do_dai` = số thì không khớp bản ghi 'PW'."""
    import numpy as np
    a = np.random.default_rng(10).standard_normal(100)
    giai = sd.ktc_khoi_co_cap(a)["do_dai"]
    k = sd.ktc_khoi_co_cap(a, do_dai=giai)
    assert k["do_dai"] == giai and sd.khop_cau_hinh_khoa(k, _bang()["cau_hinh_khoa"])
