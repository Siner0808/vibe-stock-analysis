"""`tools/do20_doi_cron.py` phải đọc được bảng BƯỚC 20 — và phải ĐỎ được.

VÌ SAO CÓ FILE NÀY
──────────────────
Lỗi 31 của dự án: *một tiêu chí không thể đỏ là trang trí*. Bảng BƯỚC 20 có
**ba** ô, và ô đáng sợ nhất không phải ô "không có tác dụng" — ô ấy là kết
quả thật của hôm nay. Ô đáng sợ là `DOI CO TAC DUNG`: nếu không đầu vào nào
chạm tới được nó thì bảng ấy chưa bao giờ là một phép kiểm.

Phép kiểm thứ hai, cùng họ `N_DAY_DU` 596/451: **ba con số trong mã phải
khớp ba con số trong bản khai** ở `docs/STATE.md`. Sửa ngưỡng sau khi thấy
số là điều bản khai cấm thẳng, và một bản sao gõ tay thì trôi.

Phép kiểm thứ ba là bài học đắt nhất của ngày 16/09/2026 (lỗi 73): **không
được có bản cài đặt THỨ HAI** của phép đo trễ. `tools/do_roi_nhip.py` đã có
nó và đã dùng nó cho BƯỚC 54; file mới phải NHẬP, không chép. Gác này đọc
AST — một bản chép nằm trong chú thích thì `in` không phân biệt được.
"""
import ast
import re
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import do20_doi_cron as d20  # noqa: E402

UTC = timezone.utc
NGUON = GOC / "tools" / "do20_doi_cron.py"
STATE = GOC / "docs" / "STATE.md"

#: Mốc TẠO thật của `chuong-bao-quet.yml`, các lượt `event=schedule`, đọc
#: ngày 17/09/2026 bằng:
#:
#:     gh run list --workflow=chuong-bao-quet.yml --event=schedule \
#:        --limit=20 --json createdAt
#:
#: Ghi lại ở đây để bộ test chạy được KHÔNG CẦN MẠNG — cổng 4 của dự án đòi
#: mọi file test xanh khi chạy một mình, và CI thì không có `gh` đã đăng nhập.
MOC_THAT = [
    "2026-09-04T13:34:55Z",
    "2026-09-07T15:05:56Z",
    "2026-09-08T13:41:03Z",
    "2026-09-09T13:46:08Z",
    "2026-09-10T13:39:44Z",
    "2026-09-11T13:38:01Z",
    "2026-09-14T15:55:13Z",
    "2026-09-15T14:21:32Z",
    "2026-09-16T14:13:53Z",
]

#: Con số BƯỚC 54 đã ghi vào `docs/STATE.md` ngày 12/09/2026 cho cửa sổ
#: 07→11/09, đo bằng một dụng cụ KHÁC (`tools/do_roi_nhip.py`). Đây là "ca
#: THẬT đã biết trước" mà Bước 3 điều 4 của skill đòi mọi máy đo phải đi qua.
A_BUOC_54 = 258.05


def _moc(chuoi: str) -> datetime:
    return datetime.fromisoformat(chuoi.replace("Z", "+00:00"))


def _mocs() -> list[datetime]:
    return [_moc(s) for s in MOC_THAT]


def _sau_khe(ngay: str) -> datetime:
    """Một mốc NẰM SAU khe của ngày ấy — để `chua_toi_gio` trả False."""
    return datetime.fromisoformat(f"{ngay}T23:59:00+00:00")


# ══ Ô của bảng đã ký ═══════════════════════════════════════════════════
def test_BA_O_cua_bang_da_ky_deu_DAT_TOI_DUOC():
    """Mỗi ô một đầu vào. Ô nào không đạt tới được là ô trang trí."""
    bang = [
        (12.0, d20.CO_TAC_DUNG),
        (60.0, d20.CO_TAC_DUNG),        # BIÊN: `<=` chứ không phải `<`
        (90.0, d20.CHUA_KET_LUAN),
        (120.0, d20.CHUA_KET_LUAN),     # BIÊN: `>` chứ không phải `>=`
        (263.13, d20.KHONG_TAC_DUNG),
        (None, d20.CHUA_KET_LUAN),
    ]
    for tv, mong_doi in bang:
        ma, ly_do = d20.phan_xu(tv)
        assert ma == mong_doi, f"trung vi {tv} -> {ma}, doi {mong_doi}"
        assert ly_do, "moi o phai noi ra LY DO"
    da_bat = {d20.phan_xu(tv)[0] for tv, _ in bang}
    assert da_bat == {d20.CO_TAC_DUNG, d20.CHUA_KET_LUAN, d20.KHONG_TAC_DUNG}
    print("PASS  ba o cua bang deu dat toi duoc, ca hai bien deu dung chieu")


def test_HAI_LY_DO_CHUA_KET_LUAN_khong_duoc_tron_lam_mot():
    """*Không đo được gì* và *nằm giữa hai ngưỡng* là hai chuyện khác nhau."""
    _, vi_rong = d20.phan_xu(None)
    _, vi_giua = d20.phan_xu(90.0)
    assert vi_rong != vi_giua, "hai ly do dang noi cung mot cau"


# ══ Ba con số phải khớp bản khai, không được gõ hai lần ════════════════
def test_BA_NGUONG_trong_ma_khop_BAN_KHAI_o_STATE():
    """Cùng họ `N_DAY_DU` 596/451: bản sao gõ tay thì trôi khỏi bản gốc."""
    src = STATE.read_text(encoding="utf-8")
    khoi = re.search(r"## BƯỚC 20 —.*?(?=\n## BƯỚC )", src, re.S)
    assert khoi, "khong tim thay BUOC 20 trong docs/STATE.md"
    van = khoi.group(0)

    nen = re.search(r"Nền\s*:\s*(\d+)\s*phút", van)
    tot = re.search(r"≤\s*(\d+)\s*phút\s*->", van)
    xau = re.search(r">\s*(\d+)\s*phút\s*->", van)
    assert nen and tot and xau, "ban khai BUOC 20 thieu mot trong ba con so"

    assert d20.NEN_PHUT == float(nen.group(1)), (
        f"NEN_PHUT = {d20.NEN_PHUT} nhung ban khai ghi {nen.group(1)}")
    assert d20.NGUONG_TOT == float(tot.group(1)), (
        f"NGUONG_TOT = {d20.NGUONG_TOT} nhung ban khai ghi {tot.group(1)}")
    assert d20.NGUONG_XAU == float(xau.group(1)), (
        f"NGUONG_XAU = {d20.NGUONG_XAU} nhung ban khai ghi {xau.group(1)}")
    print(f"PASS  nen {d20.NEN_PHUT:g} · nguong {d20.NGUONG_TOT:g}"
          f"/{d20.NGUONG_XAU:g} khop ban khai")


# ══ Máy đo phải đi qua một CA THẬT đã biết trước ═══════════════════════
def test_MAY_DO_dung_lai_dung_con_so_BUOC_54_da_ghi():
    """Dụng cụ KHÁC, ngày KHÁC, cùng cửa sổ — phải ra cùng một con số.

    Đây là phát đầu tiên theo Bước 3 điều 2: *dựng lại nguyên văn ca thật*.
    Một máy đo tự nhất quán mà lệch khỏi con số đã ghi thì nó đang đo một
    thứ khác với thứ BƯỚC 54 đo, và mọi phép so sau đó là so hai thang.
    """
    ket = d20.do(_mocs(), (date(2026, 9, 7), date(2026, 9, 11)),
                 _sau_khe("2026-09-11"))
    assert ket["trung_vi"] is not None
    assert round(ket["trung_vi"], 2) == A_BUOC_54, (
        f"cua so 07->11/09 ra {ket['trung_vi']:.2f}, BUOC 54 ghi {A_BUOC_54}")
    assert ket["ngay_roi"] == [], "5 ngay lam viec deu co luot, khong ngay nao roi"
    print(f"PASS  may do dung lai {A_BUOC_54} phut cua BUOC 54")


def test_CUA_SO_DA_KY_ra_dung_PHAN_QUYET_va_KHONG_ngay_nao_ROI():
    ket = d20.do(_mocs(), d20.CUA_SO, _moc("2026-09-17T01:08:45Z"))
    assert len(ket["tre"]) == 9
    assert ket["ngay_roi"] == []
    assert ket["ngay_chua_toi_gio"] == [date(2026, 9, 17)]
    ma, _ = d20.phan_xu(ket["trung_vi"])
    assert ma == d20.KHONG_TAC_DUNG
    assert ket["trung_vi"] > d20.NEN_PHUT, (
        "tre TANG so voi nen — neu no GIAM thi quy tac so 1 doi mot luot dieu tra")


# ══ CHƯA TỚI GIỜ ≠ RƠI NHỊP ════════════════════════════════════════════
def test_NGAY_CHUA_TOI_GIO_khong_bi_dem_thanh_ROI_NHIP():
    """Hai thứ giống hệt nhau trong dữ liệu, ngược nhau về nghĩa.

    Gộp chúng lại đẩy cỡ mẫu trông đầy hơn thực tế (10 thay vì 9) VÀ đẩy
    số nhịp rơi lên — hai cái sai cùng lúc, ngược chiều nhau, nên không
    cái nào tự lộ ra.
    """
    truoc_khe = _moc("2026-09-17T01:08:45Z")
    sau_khe = _moc("2026-09-17T23:00:00Z")
    assert d20.chua_toi_gio(date(2026, 9, 17), truoc_khe) is True
    assert d20.chua_toi_gio(date(2026, 9, 17), sau_khe) is False

    som = d20.do(_mocs(), d20.CUA_SO, truoc_khe)
    muon = d20.do(_mocs(), d20.CUA_SO, sau_khe)
    assert som["ngay_chua_toi_gio"] == [date(2026, 9, 17)]
    assert som["ngay_roi"] == []
    assert muon["ngay_chua_toi_gio"] == []
    assert muon["ngay_roi"] == [date(2026, 9, 17)], (
        "qua khe ma van khong co luot nao thi do LA mot nhip roi")


def test_NGAY_CUOI_TUAN_khong_bao_gio_la_ngay_lam_viec():
    """12–13/09 là thứ Bảy và Chủ nhật; đếm chúng là chế ra hai nhịp rơi."""
    lv = d20.do(_mocs(), d20.CUA_SO, _sau_khe("2026-09-17"))["ngay_lam_viec"]
    assert date(2026, 9, 12) not in lv and date(2026, 9, 13) not in lv
    assert len(lv) == 10, f"cua so da ky phai co dung 10 ngay lam viec, co {len(lv)}"


# ══ Phép chặn hai đầu — và nó phải NÓI ĐƯỢC "chưa đọc được" ════════════
def test_CHAN_HAI_DAU_om_tron_trung_vi_that():
    """Cận dưới ≤ trung vị thật ≤ cận trên, với chính mẫu của hôm nay."""
    tre = d20.do(_mocs(), d20.CUA_SO, _moc("2026-09-17T01:08:45Z"))["tre"]
    duoi, tren = d20.chan_hai_dau(tre, 1)
    that = statistics.median(tre)
    assert duoi <= that <= tren, f"{duoi} <= {that} <= {tren} khong thoa"


def test_HAI_CAN_phai_RA_DUNG_SO_khi_tinh_tay_duoc():
    """Ngày còn thiếu phải THẬT SỰ vào mẫu, không chỉ vào lời hứa.

    Một `chan_hai_dau` bỏ qua `so_ngay_thieu` vẫn cho cận dưới ≤ trung vị
    thật và vẫn xếp đúng ô trên số của hôm nay — nó **sống sót** lượt đột
    biến đầu tiên. Thứ nó không làm được là ra đúng con số khi tính tay:

        biet = [10, 20, 30] · thieu 1
        can duoi = trung vi [0, 10, 20, 30]       = 15
        can tren = trung vi [10, 20, 30, TRAN]    = 25
    """
    duoi, tren = d20.chan_hai_dau([10.0, 20.0, 30.0], 1)
    assert duoi == 15.0, f"can duoi ra {duoi}, tinh tay la 15.0"
    assert tren == 25.0, f"can tren ra {tren}, tinh tay la 25.0"


def test_HAI_CAN_cua_MAU_HOM_NAY_dung_bang_con_so_da_cong_bo():
    """Chính hai con số `docs/STATE.md` BƯỚC 89 viết ra, khoá tại đây.

    Một cận dưới bỏ qua ngày còn thiếu vẫn ≤ trung vị thật và vẫn xếp đúng
    ô — nó **sống sót** lượt đột biến đầu. Thứ nó không làm được là ra đúng
    `260.59`: bỏ ngày thiếu thì cận dưới sập về chính trung vị `263.13`,
    tức một khoảng chặn HẸP HƠN sự thật. Một khoảng chặn hẹp hơn sự thật
    là thứ nói "đọc được" khi chưa đọc được.
    """
    tre = d20.do(_mocs(), d20.CUA_SO, _moc("2026-09-17T01:08:45Z"))["tre"]
    duoi, tren = d20.chan_hai_dau(tre, 1)
    assert round(duoi, 2) == 260.59, f"can duoi ra {duoi:.2f}, da cong bo 260.59"
    assert round(tren, 2) == 277.01, f"can tren ra {tren:.2f}, da cong bo 277.01"
    assert round(statistics.median(tre), 2) == 263.13
    print("PASS  hai can 260.59 - 277.01 dung nhu so da cong bo")


def test_TRANG_THAI_CHUA_DOC_DUOC_phai_DAT_TOI_DUOC():
    """Ô quan trọng nhất của phép chặn: khi ngày còn thiếu LẬT được phán quyết.

    Một `doc_duoc_chua()` luôn trả True sẽ qua mọi phép so trên số thật của
    hôm nay — đúng hình dạng lỗi 66: một mẫu không thể cho kết quả dương
    thì kết quả âm của nó không nói gì về giả thuyết.
    """
    # Một mẫu mỏng nằm sát ngưỡng: ngày còn thiếu quyết định tất cả.
    doc_duoc, ma, ly_do = d20.doc_duoc_chua([50.0], 1)
    assert doc_duoc is False, "mau sat nguong ma van bao doc duoc"
    assert ma == d20.CHUA_KET_LUAN
    assert "LAT" in ly_do

    doc_duoc, ma, _ = d20.doc_duoc_chua([263.13] * 9, 1)
    assert doc_duoc is True and ma == d20.KHONG_TAC_DUNG
    print("PASS  ca hai trang thai cua phep chan deu dat toi duoc")


def test_MAU_DAY_thi_khong_con_phep_CHAN():
    doc_duoc, ma, ly_do = d20.doc_duoc_chua([263.13] * 10, 0)
    assert doc_duoc is True and ma == d20.KHONG_TAC_DUNG
    assert "day" in ly_do


# ══ MỘT bản cài đặt, không phải hai — lỗi 73 ═══════════════════════════
def _ten_ham_dinh_nghia(cay: ast.Module) -> set[str]:
    return {n.name for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}


def _ten_da_nhap(cay: ast.Module) -> set[str]:
    ra: set[str] = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.ImportFrom):
            ra |= {a.asname or a.name for a in n.names}
    return ra


def test_PHEP_DO_TRE_phai_NHAP_chu_khong_duoc_DINH_NGHIA_LAI():
    """Đọc AST, không đọc `in`: một bản chép trong chú thích lọt `in` hết.

    Ba cái tên này là phép đo trễ. Chúng đã có ở `tools/do_roi_nhip.py` và
    BƯỚC 54 đã đọc số qua chúng. Định nghĩa lại ở đây là dựng bản thứ hai —
    thứ đã làm hai đột biến sống sót ngày 16/09 (lỗi 73).
    """
    cay = ast.parse(NGUON.read_text(encoding="utf-8"))
    dinh_nghia = _ten_ham_dinh_nghia(cay)
    da_nhap = _ten_da_nhap(cay)
    for ten in ("tre_phut", "khe_gan_nhat_truoc", "khe_da_hen", "ngay_lam_viec"):
        assert ten not in dinh_nghia, (
            f"`{ten}` bi DINH NGHIA LAI trong do20_doi_cron.py — "
            f"do_roi_nhip.py da co no, nhap di dung chep")
        assert ten in da_nhap, f"`{ten}` phai duoc NHAP tu do_roi_nhip"
    print("PASS  phep do tre chi co MOT ban cai dat, do20 nhap lai no")


def test_NHIP_phai_doc_tu_do_roi_nhip_chu_khong_go_lai():
    """Khe 09:23 gõ lại ở đây là chỗ lệch thứ hai khi cron đổi lần nữa."""
    import do_roi_nhip as drn
    assert d20.NHIP is drn.NHIP, "NHIP phai la CHINH doi tuong cua do_roi_nhip"
    assert d20.CHUONG in d20.NHIP
