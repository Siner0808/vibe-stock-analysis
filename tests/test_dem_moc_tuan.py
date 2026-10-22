"""BƯỚC 218 — dụng cụ đếm tiêu chí ra khỏi giai đoạn A (`tools/dem_moc_tuan.py`).

Tiêu chí ở `docs/LO-TRINH.md`: ít nhất 2/3 số BƯỚC mỗi tuần phục vụ một mốc sản
phẩm (mọi mã trừ nhóm A và `quy-trinh`). Lượt đếm đầu (22/10/2026) cho W41 đạt vừa
sát (10/15), W42 và W43 không — nên biên 2/3 phải được kiểm ĐÚNG ở điểm bằng.
"""
from __future__ import annotations

import ast
import re
import sys
from datetime import date
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import dem_moc_tuan as d  # noqa: E402
import moc_lo_trinh as mlt  # noqa: E402

STATE_GIA = """\
## BƯỚC 163 — CŨ, TRƯỚC MỐC (01/10/2026)

**Mốc:** B3

## BƯỚC 300 — SẢN PHẨM (12/10/2026)

**Mốc:** B3

## BƯỚC 301 — NHÓM A, MÃ TRONG LÝ DO KHÔNG ĐẾM (13/10/2026)

**Mốc:** A5 — liên quan B1 và Q14

## BƯỚC 302 — QUY TRÌNH NHẮC MÃ (14/10/2026)

**Mốc:** quy-trinh — sửa gác B3 đỏ giả khi máy tải nặng

```
**Mốc:** B4
```

## BƯỚC 303 — KHÔNG NGÀY

**Mốc:** B2

## BƯỚC 304 — TUẦN SAU (19/10/2026)

**Mốc:** A1 · B2
"""


def test_loai_moc_tung_dang():
    assert d.loai_moc("B3") == d.SAN_PHAM
    assert d.loai_moc("D2 — dữ liệu giá ở máy đổi theo BƯỚC 180") == d.SAN_PHAM
    assert d.loai_moc("A1, A2, A3") == d.NHOM_A
    assert d.loai_moc("A5 — liên quan B1 và Q14") == d.NHOM_A, "mã trong LÝ DO không được đếm"
    assert d.loai_moc("A1 · B2") == d.SAN_PHAM, "có MỘT mã ngoài nhóm A là mốc sản phẩm"
    assert d.loai_moc("quy-trinh — sửa gác B3 đỏ giả khi máy tải nặng") == d.QUY_TRINH
    assert d.loai_moc(None) == d.THIEU
    assert d.loai_moc("") == d.THIEU


def test_doc_buoc_tu_164_bo_khoi_rao_va_neu_ten_buoc_khong_ngay():
    buoc, khong_ngay = d.doc_buoc(STATE_GIA)
    assert [b["n"] for b in buoc] == [300, 301, 302, 304], "BƯỚC < 164 không vào quần thể"
    assert khong_ngay == [303], "tiêu đề không ngày phải được NÊU TÊN, không lặng lẽ rơi"
    loai = {b["n"]: b["loai"] for b in buoc}
    assert loai == {300: d.SAN_PHAM, 301: d.NHOM_A, 302: d.QUY_TRINH, 304: d.SAN_PHAM}
    assert next(b for b in buoc if b["n"] == 300)["ngay"] == date(2026, 10, 12)


def test_dem_theo_tuan_ISO_va_tuan_chua_het():
    buoc, _ = d.doc_buoc(STATE_GIA)
    tuan = d.dem_theo_tuan(buoc, hom_nay=date(2026, 10, 20))
    assert [(t["tuan"], t["so_buoc"], t["san_pham"]) for t in tuan] == [
        ("2026-W42", 3, 1), ("2026-W43", 1, 1)]
    assert [t["dat"] for t in tuan] == [False, True]
    assert [t["da_het"] for t in tuan] == [True, False], "tuần chứa hôm nay là tuần CHƯA HẾT"


def _buoc(loai_ds):
    return [{"n": i, "ngay": date(2026, 10, 12), "loai": x, "moc": ""}
            for i, x in enumerate(loai_ds)]


def test_bien_2_phan_3_dung_o_DIEM_BANG():
    sp, qt = d.SAN_PHAM, d.QUY_TRINH
    hn = date(2026, 12, 1)
    assert d.dem_theo_tuan(_buoc([sp, sp, qt]), hn)[0]["dat"] is True, "2/3 đúng bằng ngưỡng là ĐẠT"
    assert d.dem_theo_tuan(_buoc([sp] * 10 + [qt] * 5), hn)[0]["dat"] is True, "W41 thật: 10/15"
    assert d.dem_theo_tuan(_buoc([sp] * 3 + [qt] * 2), hn)[0]["dat"] is False, "3/5 = 60%"
    assert d.dem_theo_tuan(_buoc([sp] * 18 + [qt] * 11), hn)[0]["dat"] is False, "W42 thật: 18/29"


def test_nguong_KHOP_cau_cua_LO_TRINH():
    van = (GOC / "docs" / "LO-TRINH.md").read_text(encoding="utf-8")
    k = re.search(r"\*\*Ra khỏi giai đoạn khi:\*\*\s*ít nhất (\d+)/(\d+) số BƯỚC mỗi\s+tuần", van)
    assert k, "câu tiêu chí ra khỏi giai đoạn A trong docs/LO-TRINH.md đã đổi dạng"
    assert (int(k.group(1)), int(k.group(2))) == (d.TU_SO, d.MAU_SO)


def test_STATE_that_moi_BUOC_tu_164_deu_doc_duoc_ngay():
    buoc, khong_ngay = d.doc_buoc(mlt.doc_van_state())
    assert not khong_ngay, f"tiêu đề BƯỚC không mang ngày (dd/mm/yyyy) ở cuối: {khong_ngay}"
    assert len(buoc) == len(mlt.tach_muc_buoc(mlt.doc_van_state())) > 50
    assert all(b["loai"] != d.THIEU for b in buoc), "gác Mốc đã bắt BƯỚC thiếu dòng Mốc"


def _goi(cay):
    return {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None)
            for n in ast.walk(cay) if isinstance(n, ast.Call)}


def test_MOT_bo_tach_dong_Moc_cho_gac_va_dung_cu():
    cay_cu = ast.parse((GOC / "tools" / "dem_moc_tuan.py").read_text(encoding="utf-8"))
    assert {"tach_muc_buoc", "tach_dau_ly_do", "cac_ma"} <= _goi(cay_cu)
    tu_dung = [n.lineno for n in ast.walk(cay_cu)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr in {"compile", "match", "search", "findall", "split"}
               and n.args and isinstance(n.args[0], ast.Constant)
               and isinstance(n.args[0].value, str) and "Mốc" in n.args[0].value]
    assert not tu_dung, f"dụng cụ tự dựng regex dòng Mốc (dòng {tu_dung}) — dùng của moc_lo_trinh"
    cay_gac = ast.parse((GOC / "tools" / "moc_lo_trinh.py").read_text(encoding="utf-8"))
    loi_moc = next(n for n in ast.walk(cay_gac)
                   if isinstance(n, ast.FunctionDef) and n.name == "loi_moc")
    assert {"tach_dau_ly_do", "cac_ma"} <= _goi(loi_moc), "gác phải đi qua CÙNG hai hàm tách"


def test_main_in_bang(capsys):
    assert d.main([]) == 0
    ra = capsys.readouterr().out
    assert "Tuần ISO" in ra and "2026-W41" in ra
