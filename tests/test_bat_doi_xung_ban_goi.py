"""Bất đối xứng local/CI có **ba** vế, không phải hai — và phép phán phải ĐỎ được.

VÌ SAO CÓ FILE NÀY (17/09/2026, lỗi 79)
──────────────────────────────────────
`CLAUDE.md` có một bảng tên *"Bất đối xứng local / CI — VĨNH VIỄN, và là
chủ ý"*, kết bằng một câu khai ĐỦ:

    "Bat doi xung CHI nam o BCTC va han muc; lich su gia thi khong."

Thiếu một vế, và vế thiếu là vế đổi **thường xuyên nhất**: số hiệu bản thư
viện. `requirements.txt` khai bằng **SÀN**, nên CI luôn lấy bản mới nhất
còn máy local cài một lần rồi đứng yên.

VÀ MỘT TẦNG THỨ HAI, CÙNG NGÀY (lỗi 80)
───────────────────────────────────────
Dụng cụ dựng ra để chữa lỗi 79 **mắc lại đúng hình dạng ấy**: nó khai một
hằng số bảy tên gõ tay rồi chỉ so bảy tên. Đo lại trên toàn bộ quần thể
chiều 17/09:

    92 goi co o CA HAI noi  ->  LECH 32
    bay ten go tay bat duoc ->  1
    lot qua                 ->  31   (urllib3 1.26.20 / 2.8.0,
                                      plotly 6.9.0 / 7.1.0, ...)

Nên file này khoá **ba** thứ, không phải hai:

1. **Tài liệu** phải nêu vế thứ ba, và phải nêu LỆNH đọc trạng thái.
2. **Phép phán** `so_ban_goi.so_sanh()` phải đạt tới được **cả ba** ô.
3. **Quần thể phải SUY RA**, và hạng chỉ được quyết định MỨC ĐỘ — một
   dòng ngoài mọi hạng vẫn phải có mặt trong danh sách lệch.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import so_ban_goi as sb  # noqa: E402

CLAUDE = GOC / "CLAUDE.md"
REQ = GOC / "requirements.txt"


# ══ 1. Tài liệu phải nêu VẾ THỨ BA ═════════════════════════════════════
def _khoi_bat_doi_xung() -> str:
    van = CLAUDE.read_text(encoding="utf-8")
    dau = van.find("Bất đối xứng local / CI")
    assert dau != -1, "khong tim thay muc bat doi xung trong CLAUDE.md"
    cuoi = van.find("\n## ", dau)
    return van[dau:cuoi if cuoi != -1 else len(van)]


def test_MUC_BAT_DOI_XUNG_phai_neu_VE_BAN_THU_VIEN():
    """Vế thiếu là vế đổi thường xuyên nhất, nên nó phải có tên trong bảng."""
    khoi = _khoi_bat_doi_xung().lower()
    for phai_co in ("bản thư viện", "requirements.txt", "sàn"):
        assert phai_co in khoi, (
            f"muc bat doi xung khong neu {phai_co!r} — bang van dang khai "
            f"DU trong khi no thieu mot ve")
    print("PASS  muc bat doi xung neu ca ve ban thu vien")


def test_CAU_CHI_NAM_O_BCTC_VA_HAN_MUC_phai_mang_DAU():
    """Quy ước giữ-số-cũ ở `docs/HANDOFF.md` mục 4, áp cho một PHẠM VI."""
    khoi = _khoi_bat_doi_xung()
    i = khoi.find("CHỈ nằm ở BCTC")
    assert i != -1, "cau cu bien mat — neu co y go thi sua ca phep kiem nay"
    quanh = khoi[i:i + 700]
    assert "⚠️" in quanh, (
        "cau 'CHI nam o BCTC va han muc' con de TRAN — no khai DU trong "
        "khi thieu ve ban thu vien")


def test_CAU_CON_MOT_VE_LECH_phai_mang_DAU():
    """Lỗi 80: *"còn một vế lệch"* là câu về CỬA SỔ DỤNG CỤ, không về thế giới.

    Nó đúng với bảy tên dụng cụ nhìn, và sai với 92 gói so được. Một câu
    đếm mà không có dấu thì bị đọc là câu về thế giới — đúng hình dạng
    `N_DAY_DU` 596/451.
    """
    khoi = _khoi_bat_doi_xung()
    i = khoi.find("một vế lệch")
    if i == -1:
        return                      # câu đã gỡ hẳn — không còn gì để đánh dấu
    quanh = khoi[i:i + 900]
    assert "lỗi 80" in quanh or "LỖI 80" in quanh, (
        "cau 'con mot ve lech' con de TRAN — no dem tren bay ten go tay, "
        "khong phai tren 92 goi so duoc")


def test_MUC_BAT_DOI_XUNG_phai_neu_LENH_doc_trang_thai():
    """*Đọc trạng thái, đừng suy ra nó* — lỗi 25, và luật ấy cần một lệnh."""
    khoi = _khoi_bat_doi_xung()
    assert "tools/so_ban_goi.py" in khoi, (
        "khong neu lenh nao de doc trang thai — nguoi doc lai phai suy")
    assert (GOC / "tools" / "so_ban_goi.py").exists()


def test_REQUIREMENTS_van_khai_bang_SAN_chu_khong_phai_GHIM():
    """Nếu một ngày nó thành `==` thì cả mục bất đối xứng phải viết lại.

    Không đòi nó PHẢI là sàn — đó là quyết định. Đòi nó **khớp với thứ
    tài liệu đang mô tả**: cùng họ `N_DAY_DU` 596/451.
    """
    van = REQ.read_text(encoding="utf-8")
    dong = [d.strip() for d in van.splitlines()
            if d.strip().startswith(("vnstock", "vnai"))
            and not d.strip().startswith("#")]
    assert dong, "khong tim thay dong vnstock/vnai trong requirements.txt"
    for d in dong:
        assert ">=" in d, (
            f"`{d}` khong con la SAN — muc bat doi xung o CLAUDE.md dang "
            f"mo ta mot co che khong con dung")


# ══ 2. Phép phán phải đạt tới CẢ BA ô ══════════════════════════════════
def test_BA_O_cua_phep_phan_deu_DAT_TOI_DUOC():
    """Ô thứ ba bắt buộc: im lặng ở đó bị đọc thành *"hai nơi giống nhau"*."""
    loc = {"vnstock": "1.0.0", "pandas": "1.0.0"}
    ma, lech = sb.so_sanh(loc, dict(loc))
    assert ma == sb.KHOP and not lech

    ma, lech = sb.so_sanh(loc, {"vnstock": "9.9.9", "pandas": "1.0.0"})
    assert ma == sb.LECH
    assert lech == [("vnstock", "1.0.0", "9.9.9", sb.SO)], lech

    for rong in (None, {}):
        ma, lech = sb.so_sanh(loc, rong)
        assert ma == sb.CHUA_KIEM, f"{rong!r} phai ra CHUA KIEM DUOC"
        assert not lech
    print("PASS  ba o deu dat toi duoc")


def test_GOI_KHONG_THAY_trong_nhat_ky_thi_KHONG_duoc_phan_la_LECH():
    """*Không thấy* khác *thấy và khác*. Gộp hai cái là chế ra báo động giả.

    Nhật ký CI chỉ in các gói lượt ấy THẬT SỰ cài; một gói đã có sẵn trong
    ảnh máy chạy sẽ không xuất hiện.
    """
    ma, lech = sb.so_sanh({"vnstock": "1.0.0", "chi_o_may": "2.0.0"},
                          {"vnstock": "1.0.0"})
    assert ma == sb.KHOP, f"{ma} — goi vang mat bi doc thanh lech"
    assert not lech


def test_DAU_GACH_NGANG_trong_ten_goi_duoc_quy_ve_MOT_dang():
    """`tradingview-ta` trong `pip freeze`, `tradingview_ta` trong nhật ký."""
    assert sb._chuan("tradingview-ta") == sb._chuan("tradingview_ta")
    assert sb._chuan("zope.interface") == sb._chuan("zope-interface")
    ma, _ = sb.so_sanh({sb._chuan("tradingview-ta"): "3.3.0"},
                       {sb._chuan("tradingview_ta"): "3.3.0"})
    assert ma == sb.KHOP


def test_MAU_DOC_NHAT_KY_bat_dung_dong_pip_that():
    """Dựng lại nguyên văn một dòng `Successfully installed` của CI."""
    dong = ("kiem-dinh\tCài thư viện\t2026-09-16T01:27:00Z Successfully "
            "installed numpy-2.2.6 pandas-2.3.3 streamlit-1.64.0 "
            "vnai-2.6.0 vnstock-4.0.8 vnstock_ezchart-1.0.2 zipp-4.1.0")
    thay = sb.doc_nhat_ky(dong)
    for ten, ban in (("vnstock", "4.0.8"), ("vnai", "2.6.0"),
                     ("streamlit", "1.64.0"), ("pandas", "2.3.3")):
        assert thay.get(sb._chuan(ten)) == ban, f"{ten}: doc ra {thay.get(ten)!r}"
    assert thay.get("zipp") == "4.1.0", (
        "`zipp` bi bo qua — quan the dang bi loc bang mot danh sach go tay")
    print("PASS  mau doc dung dong `Successfully installed` that cua CI")


# ══ 3. Quần thể SUY RA, hạng chỉ quyết định MỨC ĐỘ (lỗi 80) ════════════
_GO_TAY = frozenset(sb._chuan(g) for g in sb.HANG_SO + sb.HANG_GIAO_DIEN)


def test_QUAN_THE_la_GIAO_cua_hai_ben_chu_khong_phai_DANH_SACH_GO_TAY():
    """Phát đục dựng lại ĐÚNG ca thật: một gói ngoài mọi hạng vẫn phải lệch.

    Bản đầu lọc theo bảy tên gõ tay, nên `urllib3` 1.26.20 so với 2.8.0 —
    một khoảng cách bản CHÍNH — không bao giờ tới được danh sách.
    """
    ten = "urllib3"
    assert sb._chuan(ten) not in _GO_TAY, (
        "chon lai mot ten NGOAI moi hang, khong thi phep kiem nay mu")
    ma, lech = sb.so_sanh({ten: "1.26.20"}, {ten: "2.8.0"})
    assert ma == sb.LECH, f"{ma} — goi ngoai hang bi loc khoi quan the"
    assert lech == [(ten, "1.26.20", "2.8.0", sb.KHAC)], lech
    print("PASS  quan the suy ra — goi ngoai moi hang van toi duoc danh sach")


def test_DUNG_LAI_CA_THAT_ngay_17_09_ba_goi_ba_hang():
    """Ba dòng thật của lượt CI 35180072169, mỗi dòng một hạng."""
    loc = {"pandas": "2.3.3", "plotly": "6.9.0", "urllib3": "1.26.20"}
    ci = {"pandas": "2.3.3", "plotly": "7.1.0", "urllib3": "2.8.0"}
    ma, lech = sb.so_sanh(loc, ci)
    assert ma == sb.LECH
    assert {g for g, _, _, _ in lech} == {"plotly", "urllib3"}, lech
    hang = {g: h for g, _, _, h in lech}
    assert hang["plotly"] == sb.GIAO_DIEN
    assert hang["urllib3"] == sb.KHAC
    assert sb.cham_cho_quyet_dinh(lech) is True


def test_HANG_chi_quyet_dinh_MUC_DO_chu_khong_LOC_dong_nao():
    """Hai câu hỏi tách bạch: *có lệch không* và *lệch có chạm chỗ quyết định*."""
    chi_khac = [("urllib3", "1.26.20", "2.8.0", sb.KHAC)]
    assert sb.cham_cho_quyet_dinh(chi_khac) is False, (
        "mot dong ngoai hang lam ma thoat do — hang dang LOC chu khong "
        "chi bao muc do")
    for h in (sb.SO, sb.GIAO_DIEN):
        assert sb.cham_cho_quyet_dinh([("x", "1", "2", h)]) is True
    assert sb.cham_cho_quyet_dinh([]) is False


def test_MOI_HANG_deu_GAN_DUOC_cho_mot_ten_that():
    """Ba hạng đều đạt tới được — một hạng không ai rơi vào là hạng chết."""
    assert sb.hang_cua("vnstock") == sb.SO
    assert sb.hang_cua("streamlit") == sb.GIAO_DIEN
    assert sb.hang_cua("urllib3") == sb.KHAC
    assert sb.hang_cua("tradingview_ta") == sb.SO, "chuan hoa ten bi bo qua"


def test_BAN_LOCAL_doc_MOI_goi_chu_khong_phai_mot_danh_sach():
    """Quần thể ở phía máy cũng phải suy ra — đây là nửa còn lại của lỗi 80."""
    loc = sb.ban_local()
    assert len(loc) > 50, (
        f"chi doc duoc {len(loc)} goi — `ban_local` dang bi mot danh sach "
        f"go tay bop lai")
    assert "pytest" in loc, "goi khong nam trong hang nao van phai co mat"


# ─────────────────────────────────────────────────────────────────────────
# CỘT SUY RA: "repo có NHẬP gói này không" — thêm 18/09/2026
#
# Hạng quyết định *"lệch này có quan trọng không"*, và hạng đến từ hai
# tuple GÕ TAY. Đo 18/09: **3 trên 10** tên ở hạng ồn ào mà repo không nhập
# lần nào — `vnstock_ezchart`, `altair`, `matplotlib`. App vẽ toàn bộ bằng
# plotly; 0 lời gọi `st.line_chart` hay `st.pyplot`.
#
# Cột này KHÔNG đổi hạng. Suy hạng từ "repo có nhập không" là dựng một cửa
# sổ HẸP HƠN thứ nó đo — một gói repo không nhập vẫn chạm người dùng được
# qua thư viện khác. Đó là lỗi 80 đảo chiều.
# ─────────────────────────────────────────────────────────────────────────


def test_GOI_REPO_NHAP_doc_bang_AST_chu_khong_bang_CHU():
    """Ca thật, không phải đồ giả: `tools/so_ban_goi.py` CHỨA chữ "altair".

    Hằng số `HANG_GIAO_DIEN` mang đúng chuỗi ấy, nên một lượt quét theo VĂN
    BẢN sẽ đếm `altair` là "repo có dùng" — và cột này thành vô nghĩa đúng
    ở chỗ nó sinh ra để soi. `CLAUDE.md`, mục *"Dọn code chết"*: *"Dùng
    AST, đừng dùng grep."*
    """
    van = (GOC / "tools" / "so_ban_goi.py").read_text(encoding="utf-8")
    # van-ban-ok: TIEN DE cua phep kiem chu khong phai ket luan — phai chung minh chu ay CO trong file thi cau sau moi co nghia
    assert "altair" in van, "ca thu nay dua tren viec chu 'altair' CO trong file"
    # van-ban-ok: cung mot tien de, cho ten goi thu hai trong hang gõ tay
    assert "matplotlib" in van
    nhap = sb.goi_repo_nhap()
    assert "altair" not in nhap, "doc bang CHU roi — chu 'altair' chi la hang so"
    assert "matplotlib" not in nhap
    print("PASS  chu co trong file ma KHONG bi dem la nhap")


def test_GOI_REPO_NHAP_van_thay_goi_THAT_SU_duoc_nhap():
    """Đối chứng DƯƠNG. Không có nó, một hàm trả rỗng cũng qua phép kiểm trên."""
    nhap = sb.goi_repo_nhap()
    for g in ("pandas", "streamlit", "plotly"):
        assert g in nhap, f"{g} duoc nhap that ma khong thay -> phep do MU"
    print(f"PASS  doi chung duong dat — {len(nhap)} goi")


def test_GOI_REPO_NHAP_quet_ca_THU_MUC_CON_chu_khong_chi_GOC():
    """Ba gói ở phép kiểm trên đều được nhập từ file Ở GỐC repo, nên một
    lượt quét KHÔNG đệ quy vẫn qua được chúng — đục thử đã chứng minh: phát
    `rglob` -> `glob` **sống sót**.

    Đo ra ca phân biệt được: `pytest` là một trong HAI gói duy nhất chỉ
    được nhập từ thư mục con (`tests/`). Nó không bao giờ rời repo này.
    """
    assert "pytest" in sb.goi_repo_nhap(), (
        "khong thay `pytest` — luot quet dang bo qua thu muc con")
    print("PASS  quet toi ca tests/")


def test_HANG_ON_MA_KHONG_NHAP_goi_dung_ten():
    """HÀM THUẦN trên tập `nhap`, nên đục thử được mà không chạm đĩa."""
    gia = frozenset({sb._chuan(t) for t in sb.HANG_SO} |
                    {sb._chuan(t) for t in sb.HANG_GIAO_DIEN})
    assert sb.hang_on_ma_khong_nhap(gia) == [], "nhap DU ma van keu"
    thieu = gia - {sb._chuan("altair")}
    assert sb.hang_on_ma_khong_nhap(thieu) == [("altair", sb.GIAO_DIEN)]
    assert sb.hang_on_ma_khong_nhap(frozenset()) != [], "nhap RONG ma im lang"
    print("PASS  goi dung ten, va khong keu khi du")


def test_COT_SUY_RA_KHONG_duoc_doi_HANG_cua_bat_ky_goi_nao():
    """Ranh giới của cả thiết kế: cột này NÓI, nó không PHÁN.

    Nếu một ngày ai đó nối `goi_repo_nhap()` vào `hang_cua()`, phép kiểm
    này đỏ — và nó phải đỏ, vì khi ấy một gói như `altair` sẽ tụt xuống
    "con lai" và **im lặng** thay vì được nhìn thấy.
    """
    import ast
    nguon = (GOC / "tools" / "so_ban_goi.py").read_text(encoding="utf-8")
    cay = ast.parse(nguon)
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "hang_cua")
    goi = {n.func.id for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "goi_repo_nhap" not in goi, (
        "hang_cua() dang doc cot SUY RA — hang phai giu nguyen la GO TAY")
    assert sb.hang_cua("altair") == sb.GIAO_DIEN, (
        "altair phai VAN o hang on ao du repo khong nhap")
    print("PASS  cot suy ra khong dong vao hang")


def test_BAN_DO_MODULE_GOI_suy_tu_METADATA_chu_khong_go_tay():
    """Bảng phải SUY từ metadata đang cài, không gõ.

    LỜI KHAI ĐƯỢC SUY RA, KHÔNG NÊU TÊN GÓI NÀO — lỗi 84, 18/09/2026.
    Bản đầu neo vào `ban_do.get("yaml") == "pyyaml"`. `pyyaml` CÓ ở máy
    này và **KHÔNG** có trên CI, nên năm cổng xanh tại máy rồi CI đỏ ngay:
    `assert None == 'pyyaml'`. Tôi gõ tay một tên gói vào đúng phép kiểm
    dựng ra để chứng minh *"đừng gõ tay"*.

    Thứ cần khẳng định không phải MỘT cặp cụ thể, mà là **bảng có phân
    biệt được module với gói**. Đếm số cặp khác nhau kiểm được điều ấy mà
    không nêu tên nào — nên nó đúng ở mọi môi trường, và nó vẫn giết đột
    biến "gõ tay một dict nhỏ" (mọi cặp gõ tay đều có module trùng gói).
    """
    ban_do = sb.ban_do_module_goi()
    assert len(ban_do) > 50, f"ban do qua nho ({len(ban_do)}) — co go tay khong?"
    khac = {m: g for m, g in ban_do.items() if sb._chuan(m) != g}
    assert khac, (
        "khong cap nao co ten module KHAC ten goi — bang nay hoac go tay, "
        "hoac dang lay ten goi lam ten module")
    print(f"PASS  ban do {len(ban_do)} module · {len(khac)} cap module != goi")
