"""Gác lịch cron của ba chuông — và của chú thích nói về lịch ấy.

Ngày 03/09/2026 đo được: nhịp ở 09:00 và 09:30 UTC trễ **trung vị 4–4,7
giờ**, trong khi tài liệu dự án ghi "5 → 90 phút". Ba nhịp được dời lệch
khỏi mốc `:00` và `:30` theo đúng khuyến nghị của tài liệu GitHub.

Bộ gác này canh ba thứ, và thứ ba mới là thứ hay hỏng nhất:

1. Không nhịp nào quay về mốc `:00`/`:30` — mốc nghẽn.
2. Không nhịp nào được dời SỚM HƠN bản cũ. `chuong_bao_quet.kiem_tra()`
   soát cả ngày hôm nay và báo đỏ khi ngày đó chưa có lượt quét nào; chạy
   sớm là tự chế báo động giả trong đúng cái chuông canh việc quét.
3. Chú thích trong file phải KHỚP với cron của chính file đó. Hôm nay đã
   sửa ba chú thích nêu sai giờ sau khi cron đổi — cùng hình dạng với
   `extend_history.py` trỏ tới một file `.broken`: văn bản hướng dẫn
   không được ai kiểm.

Gác 3 là gác VĂN BẢN, và ở đây văn bản mới là thứ cần kiểm — xem
CLAUDE.md, "Gác phải đọc AST, không đọc `in`".
"""
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
WF = GOC / ".github" / "workflows"

#: workflow -> (phút, giờ) UTC đang khai báo, và nhịp CŨ để so chiều dời.
NHIP = {
    "chuong-bao-quet.yml": ((23, 9), (0, 9)),
    "canh-cong-c5.yml": ((43, 9), (30, 9)),
    "chuong-nguon-dung.yml": ((17, 10), (0, 10)),
}

RE_CRON = re.compile(r"^\s*-\s*cron:\s*'(\d+)\s+(\d+)\s+\*\s+\*\s+1-5'\s*$",
                     re.MULTILINE)
#: Dòng chú thích TỰ KHAI giờ của chính file đó.
RE_TU_KHAI = re.compile(r"#\s*(\d{2}):(\d{2}) UTC = (\d{2}):(\d{2}) ICT")


def _doc(ten: str) -> str:
    return (WF / ten).read_text(encoding="utf-8")


def _cron(ten: str) -> tuple[int, int]:
    m = RE_CRON.findall(_doc(ten))
    assert len(m) == 1, f"{ten}: thấy {len(m)} dòng cron, phải đúng 1"
    return int(m[0][0]), int(m[0][1])


@pytest.mark.parametrize("ten", sorted(NHIP))
def test_cron_dung_nhu_da_khai(ten):
    assert _cron(ten) == NHIP[ten][0]


@pytest.mark.parametrize("ten", sorted(NHIP))
def test_KHONG_quay_ve_moc_nghen(ten):
    """`:00` và `:30` là lúc nhiều workflow nhất cùng xin chạy."""
    phut, _ = _cron(ten)
    assert phut not in (0, 30), (
        f"{ten} quay về mốc nghẽn :{phut:02d} — xem docs/STATE.md, BƯỚC 19")


@pytest.mark.parametrize("ten", sorted(NHIP))
def test_KHONG_duoc_doi_som_hon_ban_cu(ten):
    """Dời muộn thì an toàn; dời sớm thì `chuong_bao_quet` báo động giả."""
    (pm, gm), (pc, gc) = NHIP[ten]
    assert (gm * 60 + pm) >= (gc * 60 + pc), (
        f"{ten} dời SỚM hơn bản cũ — soát cả ngày hôm nay thì chưa có "
        f"lượt quét nào và chuông kêu oan")
    assert _cron(ten) == (pm, gm)


@pytest.mark.parametrize("ten", sorted(NHIP))
def test_CHU_THICH_khop_voi_cron_cua_chinh_no(ten):
    """Chú thích nêu sai giờ là thứ đã hỏng ba lần trong ngày 03/09."""
    m = RE_TU_KHAI.findall(_doc(ten))
    assert len(m) == 1, f"{ten}: thấy {len(m)} dòng tự khai giờ, phải đúng 1"
    gio_utc, phut_utc, gio_ict, phut_ict = map(int, m[0])
    assert (phut_utc, gio_utc) == _cron(ten), (
        f"{ten}: chú thích ghi {gio_utc:02d}:{phut_utc:02d} UTC nhưng cron "
        f"là {_cron(ten)[1]:02d}:{_cron(ten)[0]:02d}")
    assert (gio_ict, phut_ict) == ((gio_utc + 7) % 24, phut_utc), (
        f"{ten}: giờ ICT không phải UTC+7")


def test_THU_TU_ba_chuong_giu_nguyen():
    """Ba chuông cách nhau để không lẫn trong hộp thư — lý do có từ đầu."""
    thu_tu = ["chuong-bao-quet.yml", "canh-cong-c5.yml",
              "chuong-nguon-dung.yml"]
    moc = [_cron(t)[1] * 60 + _cron(t)[0] for t in thu_tu]
    assert moc == sorted(moc), f"thứ tự ba chuông đã đảo: {moc}"
    assert all(b - a >= 10 for a, b in zip(moc, moc[1:])), (
        f"hai chuông cách nhau dưới 10 phút: {moc}")


def test_CHEO_chuong_nguon_dung_nhac_dung_gio_hai_chuong_kia():
    """File nhắc giờ của file khác — chỗ chú thích trôi mà không ai thấy."""
    src = _doc("chuong-nguon-dung.yml")
    m = re.search(r"báo quét (\d{2}):(\d{2}), cổng C5 (\d{2}):(\d{2})", src)
    assert m, "không còn dòng nhắc chéo — nếu cố ý bỏ thì sửa cả test này"
    bq_g, bq_p, c5_g, c5_p = map(int, m.groups())
    assert (bq_p, bq_g) == _cron("chuong-bao-quet.yml")
    assert (c5_p, c5_g) == _cron("canh-cong-c5.yml")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_lich_cron_chuong.py -q")
