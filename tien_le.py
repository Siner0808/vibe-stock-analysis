"""Tra tiền lệ — CHỈ ĐỂ HIỆN (ý 5, BƯỚC 215; thiết kế `docs/thiet-ke-y5-tien-le.md`).

Với một lệnh trong nhật ký, gom những lệnh CŨ cùng bối cảnh đã kết thúc ra sao, để
người dùng HỌC — không để dự báo. Điểm không dự báo được lợi nhuận (`CLAUDE.md`,
rho ≈ 0), nên tỷ lệ thắng của một nhóm gần như là tỷ lệ nền cộng nhiễu: `tom_tat`
luôn trả tỷ lệ nền và khoảng tin cậy Wilson cạnh số của nhóm, và nhóm dưới
`N_TOI_THIEU_TIEN_LE` không có tỷ lệ.

"Giống" = cùng khoá (dải điểm vào, nấc VN-Index cao hơn MA50 ngày tín hiệu) —
người dùng chốt 20/10/2026, *"Dải điểm × độ cao VNI (Recommended)"*. Biên nấc chọn
theo số lệnh mỗi nấc, TRƯỚC khi ai nhìn kết cục; đổi biên sau khi nhìn = bất biến 7.

Chống nhìn tương lai: tiền lệ chỉ gồm lệnh có NGÀY RA < NGÀY VÀO của lệnh đang xem.

Module THUẦN: không đọc mạng, đĩa hay Sheets. Kho mô phỏng là tệp JSON dựng bằng
`tools/dung_kho_tien_le.py`; bên gọi đọc tệp rồi đưa dict vào `doc_kho`.
Đường giao dịch, chấm điểm và đo KHÔNG nhập module này (gác AST, `tests/test_tien_le.py`).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from paper_trading import BUY_THRESHOLD
from so_bai_hoc import KET_QUA_HOA, KET_QUA_THANG, KET_QUA_THUA, ket_qua_lenh

#: Biên trên của dải điểm thấp: [BUY_THRESHOLD, 70) · [70, ∞).
DIEM_DAI_CAO = 70.0
#: Biên các nấc VN-Index cao hơn MA50 (%): [0, 2) · [2, 5) · [5, ∞).
BIEN_NAC_VNI = (2.0, 5.0)
#: Nhóm ít tiền lệ hơn số này thì không in tỷ lệ (thiết kế mục 6).
N_TOI_THIEU_TIEN_LE = 10
#: Z của KTC 95% hai phía.
Z_95 = 1.96

#: Tệp kho phần mô phỏng, tính từ gốc repo (`tools/dung_kho_tien_le.py` ghi, app đọc).
DUONG_KHO = "docs/kho-tien-le.json"
#: Câu cố định của khối trên app — đọc tỷ lệ của nhóm như một lát cắt, không như dự báo.
NHAN_HIEN = ("Để HỌC, không để dự báo: điểm không dự báo được lợi nhuận, nên tỷ lệ thắng của "
             "một nhóm gần như là tỷ lệ nền cộng nhiễu — luôn đọc nó cạnh tỷ lệ nền.")

MO_PHONG = "mô phỏng"
THAT = "thật"
#: Khoá của lệnh thiếu điểm/VN-Index, điểm dưới ngưỡng mua, hoặc VN-Index dưới MA50
#: (cổng mở lệnh lẽ ra đã chặn) — nhóm riêng, không gộp vào nhóm nào.
KHONG_XEP_DUOC = "không xếp được"


def _so(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def dai_diem(diem: Any) -> Optional[str]:
    v = _so(diem)
    if v is None or v < BUY_THRESHOLD:
        return None
    return f"≥{DIEM_DAI_CAO:g}" if v >= DIEM_DAI_CAO else f"{BUY_THRESHOLD:g}–{DIEM_DAI_CAO - 1:g}"


def nac_vni(pct_tren_ma50: Any) -> Optional[str]:
    v = _so(pct_tren_ma50)
    if v is None or v < 0:
        return None
    thap, cao = BIEN_NAC_VNI
    if v < thap:
        return f"0–{thap:g}%"
    if v < cao:
        return f"{thap:g}–{cao:g}%"
    return f"≥{cao:g}%"


def khoa_nhom(diem: Any, pct_tren_ma50: Any):
    """(dải điểm, nấc VN-Index), hoặc `KHONG_XEP_DUOC`."""
    d, n = dai_diem(diem), nac_vni(pct_tren_ma50)
    return KHONG_XEP_DUOC if d is None or n is None else (d, n)


@dataclass(frozen=True)
class TienLe:
    nguon: str                      # MO_PHONG | THAT
    ma: str
    ngay_vao: str                   # YYYY-MM-DD
    ngay_ra: str
    diem_vao: Optional[float]
    vni_pct_tren_ma50: Optional[float]
    loi_nhuan_rong_pct: float
    ly_do_thoat: str = ""


def doc_kho(du_lieu: Mapping[str, Any]) -> list[TienLe]:
    """Phần mô phỏng: dict đã đọc từ tệp JSON của `tools/dung_kho_tien_le.py`."""
    ra = []
    for d in du_lieu.get("lenh", []):
        lnr = _so(d.get("loi_nhuan_rong_pct"))
        if lnr is None or not d.get("ngay_ra") or not d.get("ngay_vao"):
            continue
        ra.append(TienLe(MO_PHONG, str(d["ma"]), str(d["ngay_vao"])[:10], str(d["ngay_ra"])[:10],
                         _so(d.get("diem_vao")), _so(d.get("vni_pct_tren_ma50")), lnr,
                         str(d.get("ly_do_thoat") or "")))
    return ra


def tu_dong_nhat_ky(dong: Mapping[str, Any]) -> Optional[TienLe]:
    """Một dòng nhật ký (`nhat_ky_vi_sao.COT_NHAT_KY`) đã có nửa ĐÓNG → tiền lệ "thật"."""
    lnr = _so(dong.get("loi_nhuan_rong_pct"))
    if lnr is None or not dong.get("exit_date") or not dong.get("entry_date"):
        return None
    return TienLe(THAT, str(dong.get("symbol") or ""), str(dong["entry_date"])[:10],
                  str(dong["exit_date"])[:10], _so(dong.get("entry_score")),
                  vni_cua_dong(dong), lnr, str(dong.get("exit_reason") or ""))


def vni_cua_dong(dong: Mapping[str, Any]) -> Optional[float]:
    """`vni_pct_tren_ma50` trong ô `boi_canh` (JSON) của một dòng nhật ký."""
    bc = dong.get("boi_canh")
    if isinstance(bc, str):
        try:
            bc = json.loads(bc) if bc.strip() else {}
        except ValueError:
            return None
    return _so(bc.get("vni_pct_tren_ma50")) if isinstance(bc, Mapping) else None


def chon_tien_le(kho: Iterable[TienLe], ngay_vao: str) -> list[TienLe]:
    """Chỉ lệnh có ngày RA < ngày VÀO của lệnh đang xem — cùng ngày cũng bị loại."""
    moc = str(ngay_vao)[:10]
    return [t for t in kho if t.ngay_ra < moc]


def wilson(k: int, n: int, z: float = Z_95) -> Optional[tuple[float, float]]:
    """KTC Wilson của tỷ lệ k/n (0..1); None khi n = 0."""
    if n <= 0:
        return None
    p = k / n
    mau = 1 + z * z / n
    tam = (p + z * z / (2 * n)) / mau
    nua = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / mau
    return max(0.0, tam - nua), min(1.0, tam + nua)


def _dem(lenh: list[TienLe]) -> dict:
    kq = [ket_qua_lenh(t.loi_nhuan_rong_pct) for t in lenh]
    thang = kq.count(KET_QUA_THANG)
    n = len(lenh)
    return {"n": n, "thang": thang, "thua": kq.count(KET_QUA_THUA), "hoa": kq.count(KET_QUA_HOA),
            "n_mo_phong": sum(1 for t in lenh if t.nguon == MO_PHONG),
            "n_that": sum(1 for t in lenh if t.nguon == THAT),
            "ty_le": thang / n if n else None, "ktc": wilson(thang, n)}


def tom_tat(kho: Iterable[TienLe], diem: Any, pct_tren_ma50: Any, ngay_vao: str,
            so_ca_gan: int = 3) -> dict:
    """Khối tiền lệ của MỘT lệnh: nhóm cùng khoá, nền, và ca gần nhất.

    `du` False → nhóm dưới `N_TOI_THIEU_TIEN_LE`: bên hiện in "chưa đủ tiền lệ (n = …)"
    và KHÔNG in tỷ lệ. `khong_phan_biet` True → KTC của nhóm chứa tỷ lệ nền.
    """
    truoc = chon_tien_le(kho, ngay_vao)
    khoa = khoa_nhom(diem, pct_tren_ma50)
    nhom = ([] if khoa == KHONG_XEP_DUOC
            else [t for t in truoc if khoa_nhom(t.diem_vao, t.vni_pct_tren_ma50) == khoa])
    g, nen = _dem(nhom), _dem(truoc)
    du = g["n"] >= N_TOI_THIEU_TIEN_LE
    khong_pb = (du and g["ktc"] is not None and nen["ty_le"] is not None
                and g["ktc"][0] <= nen["ty_le"] <= g["ktc"][1])
    gan = sorted(nhom, key=lambda t: (t.ngay_ra, t.ma), reverse=True)[:so_ca_gan]
    return {"khoa": khoa, "nhom": g, "nen": nen, "du": du,
            "khong_phan_biet": khong_pb, "gan_nhat": gan}


def _pt(x: float) -> str:
    return f"{x * 100:.0f}%"


def _ty_le(d: dict) -> str:
    lo, hi = d["ktc"]
    return f"thắng {_pt(d['ty_le'])} [KTC 95%: {_pt(lo)} ; {_pt(hi)}]"


def dong_hien(kq: Mapping[str, Any]) -> list[str]:
    """Các dòng chữ của khối \"Tiền lệ\" (thiết kế mục 6). Bên hiện in nguyên, không tính gì.

    Nhóm dưới `N_TOI_THIEU_TIEN_LE`: KHÔNG có tỷ lệ. Tỷ lệ nền luôn đi cạnh tỷ lệ nhóm.
    """
    g, nen, khoa = kq["nhom"], kq["nen"], kq["khoa"]
    if khoa == KHONG_XEP_DUOC:
        ra = ["Không xếp được nhóm: thiếu điểm vào hoặc độ cao VN-Index so MA50, điểm dưới "
              "ngưỡng mua, hoặc VN-Index dưới MA50."]
    else:
        ra = [f"Tiền lệ lúc vào lệnh — điểm {khoa[0]} · VN-Index cao hơn MA50 {khoa[1]}"]
        if not kq["du"]:
            ra.append(f"Chưa đủ tiền lệ (n = {g['n']}; cần ≥ {N_TOI_THIEU_TIEN_LE}) — không in tỷ lệ.")
        else:
            ra.append(f"{g['n']} tiền lệ ({g['n_mo_phong']} {MO_PHONG}, {g['n_that']} {THAT}): "
                      f"{g['thang']} thắng · {g['thua']} thua · {g['hoa']} hoà — {_ty_le(g)}")
    if nen["n"]:
        ra.append(f"Nền (mọi tiền lệ có trước ngày vào, n = {nen['n']}): {_ty_le(nen)}")
    else:
        ra.append("Nền: chưa có tiền lệ nào đóng trước ngày vào.")
    if kq["du"]:
        ra.append("→ Không phân biệt được với nền." if kq["khong_phan_biet"] else
                  "→ Khác nền ở lát cắt này; điểm vẫn không dự báo được lợi nhuận — đọc như "
                  "một lát cắt, không như tín hiệu.")
    for t in kq["gan_nhat"]:
        ra.append(f"{t.ma} · {t.ngay_vao} → {t.ngay_ra} · {t.loi_nhuan_rong_pct:+.2f}% · {t.nguon}")
    return ra
