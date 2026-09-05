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


# ---------------------------------------------------------------------
# CLAUDE.md CŨNG PHẢI THEO KỊP CRON        (thêm 05/09/2026)
#
# Bốn test trên canh chú thích BÊN TRONG các file `.yml`. Không cái nào
# nhìn ra ngoài — nên khi `57dad6a` dời cron ngày 03/09, câu trong
# `CLAUDE.md` "chạy 09:00 UTC (16:00 ICT)" ở lại nguyên vẹn và **cả bảy
# test vẫn xanh**. Nó sống hai ngày.
#
# Cùng hình dạng với `tests/test_tai_lieu_khop_hang_so.py` (04/09): tài
# liệu lệch MÃ nguy hiểm hơn tài liệu lệch tài liệu, vì đọc chéo tài
# liệu thì thấy, còn cái này chỉ lộ khi mở mã ra so.
#
# HỢP ĐỒNG, và giới hạn của nó: đòi giờ HIỆN HÀNH có mặt ở CHỖ nhắc tên
# workflow, trong bán kính `BAN_KINH_CLAUDE` ký tự. KHÔNG đòi "mọi chỗ
# đều đúng" — dự án cố ý giữ giờ cũ kèm ghi chú (đoạn ⚠️ ngay dưới câu
# ấy nêu lại `09:00`), và một gác cấm điều đó sẽ ép xoá lịch sử đo.
# ---------------------------------------------------------------------

TAI_LIEU = GOC / "CLAUDE.md"

#: Bao nhiêu ký tự quanh tên workflow thì còn tính là "nói về nó".
#: Hỏi "giờ đúng có xuất hiện đâu đó trong file 60 KB không" là câu hỏi
#: quá yếu — phải hỏi KỀ TÊN.
BAN_KINH_CLAUDE = 400

#: Hai dạng giờ PHẢI cùng được kiểm. Bỏ một dạng là vô hiệu hoá nửa gác
#: mà không sửa một dòng logic nào — và vì tài liệu hiện ĐÚNG cả hai
#: dạng, đột biến ấy trả về đúng cùng đáp án với bản lành. Nó đã sống
#: sót một lượt đục ngày 05/09/2026 trước khi có dòng ghim này.
DANG_GIO_PHAI_KIEM = ("UTC", "ICT")


def _co_gio_ke_ten(src: str, ten: str, gio: str) -> bool:
    """Có chỗ nào nhắc `ten` mà `gio` nằm trong bán kính không."""
    i = src.find(ten)
    while i != -1:
        if gio in src[max(0, i - BAN_KINH_CLAUDE): i + BAN_KINH_CLAUDE]:
            return True
        i = src.find(ten, i + 1)
    return False


def _gio_ict(ten: str) -> tuple[str, str]:
    """(chuỗi UTC, chuỗi ICT) suy TỪ CRON, không gõ tay."""
    phut, gio = _cron(ten)
    return f"{gio:02d}:{phut:02d} UTC", f"{(gio + 7) % 24:02d}:{phut:02d} ICT"


def test_CLAUDE_md_ghi_dung_gio_chuong_bao_quet():
    """Dời cron mà quên `CLAUDE.md` → đỏ. Đúng lỗi đã sống 03→05/09."""
    src = TAI_LIEU.read_text(encoding="utf-8")
    assert len(src) >= 20_000, (
        f"CLAUDE.md chỉ đọc được {len(src)} ký tự — gác này đang canh một "
        f"file rỗng hoặc đọc hụt")
    ten = "chuong-bao-quet.yml"
    assert ten in src, (
        f"CLAUDE.md không nhắc `{ten}` lần nào — nếu cố ý bỏ thì sửa cả "
        f"test này, có lý do")
    utc, ict = _gio_ict(ten)
    kiem = {dang: (gio, _co_gio_ke_ten(src, ten, gio))
            for gio, dang in zip((utc, ict), DANG_GIO_PHAI_KIEM)}
    assert set(kiem) == set(DANG_GIO_PHAI_KIEM), (
        f"gác chỉ kiểm {sorted(kiem)} thay vì "
        f"{sorted(DANG_GIO_PHAI_KIEM)} — nửa gác đã bị bỏ")
    for dang, (gio, co) in kiem.items():
        assert co, (
            f"cron của {ten} là {utc} ({ict}) nhưng CLAUDE.md không viết "
            f"'{gio}' ({dang}) ở chỗ nào nhắc tên workflow (bán kính "
            f"{BAN_KINH_CLAUDE} ký tự). Dời cron thì phải sửa CLAUDE.md — "
            f"và theo quy ước dự án thì ĐÁNH DẤU tại chỗ, đừng xoá giờ cũ.")


def test_MAY_DO_CLAUDE_md_tu_chung_minh_no_bat_duoc():
    """Mã thật đang KHỚP, nên máy dò hỏng trả cùng đáp án với máy dò tốt.

    Đúng đột biến đã sống sót 03/09, 04/09 và 05/09. Cách duy nhất tách
    hai trường hợp là bắt nó chạy trên dữ liệu đã biết là sai.
    """
    src = TAI_LIEU.read_text(encoding="utf-8")
    ten = "chuong-bao-quet.yml"

    assert not _co_gio_ke_ten(src, ten, "04:44 UTC"), (
        "máy dò báo có một giờ bịa nằm kề tên workflow — nó đang trả True "
        "cho mọi thứ, tức không kiểm gì cả")
    assert not _co_gio_ke_ten(src, "workflow-khong-ton-tai.yml", "09:23 UTC"), (
        "máy dò tìm thấy một tên workflow không tồn tại trong tài liệu")

    utc, _ = _gio_ict(ten)
    assert _co_gio_ke_ten(src, ten, utc), (
        "máy dò không thấy cả trường hợp ĐANG ĐÚNG — nó đang hỏng")

    # Bán kính phải THẬT SỰ chặn: giờ đúng có mặt trong file nhưng ở xa
    # tên workflow thì KHÔNG được tính. Không có vế này thì đột biến nới
    # bán kính lên vô hạn sống sót.
    xa = "x" * (BAN_KINH_CLAUDE * 3)
    assert not _co_gio_ke_ten(f"{ten}{xa}{utc}", ten, utc), (
        f"bán kính không có tác dụng — {utc} cách tên workflow "
        f"{len(xa)} ký tự mà vẫn được tính là kề")


def test_BAN_KINH_va_DANG_GIO_khong_duoc_thu_hep_am_tham():
    """Hai cách vô hiệu hoá gác này mà không sửa một dòng logic nào."""
    assert BAN_KINH_CLAUDE == 400
    assert DANG_GIO_PHAI_KIEM == ("UTC", "ICT"), (
        "bỏ bớt dạng giờ phải kiểm — sửa CÓ CHỦ ĐÍCH kèm lý do, chứ "
        "đừng rút gọn cho test xanh")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Chạy bằng: pytest tests/test_lich_cron_chuong.py -q")
