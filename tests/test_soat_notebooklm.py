"""Mỗi phép đo có tiêu chí ký trước phải KHAI đã soát chéo hay chưa.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 10/09/2026 người dùng chốt: dùng NotebookLM thường xuyên như một luồng
thông tin **độc lập**. Chỉ dẫn ấy nằm trong `SKILL.md`, trong
`~/.claude/rules/`, và trong bộ nhớ phiên.

Ngày 12/09/2026 người dùng phải nhắc **lần thứ hai** rằng nó không được
dùng. Cùng ngày, **một câu hỏi duy nhất** gửi công cụ ấy lôi ra rằng ĐO 5
là bản TRÙNG của `docs/STATE.md` BƯỚC 25 (04/09/2026) — 88,8 phút máy để
dựng lại một kết quả đã nằm trong sổ tám ngày.

**Một chỉ dẫn thường trực không có cơ chế thì nó chỉ là một lời nhắc.**
File này là cơ chế: nó không ép phải soát, nó ép phải **khai** đã soát hay
chưa — cùng đúng cách `# bia-ok:` không cấm mà buộc nói ra lý do.

Gác này KHÔNG thay được việc soát. Nó chỉ làm việc bỏ sót **không im lặng
được nữa**.
"""
import ast
import json
import re
import sys
from pathlib import Path

import pytest

GOC =Path(__file__).resolve().parent.parent
SO = GOC / "docs" / "soat-notebooklm.json"
SO_DINH_KY = GOC / "docs" / "soat-dinh-ky.json"
TIEU_CHI = GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md"
STATE = GOC / "docs" / "STATE.md"

#: Mốc đọc từ CHÍNH SỔ (`_moc_buoc`), không gõ ở đây — `tools/cua_mo_phien.py`
#: cũng đọc đúng con số ấy, và một ngưỡng gõ tay hai chỗ sẽ trôi khỏi nhau
#: (`SKILL.md` Bước 2: *"Suy ra, đừng gõ"*). Lý do có mốc nằm trong sổ, ở
#: khoá `_vi_sao_co_moc_buoc`.

sys.path.insert(0, str(GOC))


def _so() -> dict:
    return json.loads(SO.read_text(encoding="utf-8"))


def ten_phep_do(van: str) -> list[str]:
    """Mọi mục `## ĐO <n>` trong bản khai tiêu chí, giữ nguyên thứ tự.

    Đọc bằng biểu thức neo vào ĐẦU DÒNG và cấp tiêu đề, không bằng `in`:
    chữ "ĐO 5" xuất hiện hàng chục lần trong văn xuôi của chính file ấy.
    """
    thay, da_co = [], set()
    for d in van.splitlines():
        m = re.match(r"^##\s+(ĐO\s+\d+[a-z]?)\s*—", d)
        if m:
            ten = re.sub(r"\s+", " ", m.group(1))
            if ten not in da_co:
                da_co.add(ten)
                thay.append(ten)
    return thay


def ten_buoc(van: str, moc: int) -> list[str]:
    """Mọi mục `## BƯỚC <n>` có n >= `moc`. Gọi thẳng bản cài đặt DUY NHẤT.

    Hàm thật nằm ở `tools/soat_loi_khai_cu.buoc_chua_khai`, và
    `tools/cua_mo_phien.py` gọi đúng nó — nên gác này và bản tin mở phiên
    KHÔNG THỂ trôi khỏi nhau. Bản đầu 16/09/2026 viết hai lần rồi canh cho
    hai bản khớp; đục thử cho thấy phép canh ấy so hai tập rỗng và cả hai
    đột biến vào hook sống sót.
    """
    sys.path.insert(0, str(GOC / "tools"))
    from soat_loi_khai_cu import buoc_chua_khai
    return buoc_chua_khai(van, (), moc)


def test_MOI_BUOC_tu_MOC_deu_co_mot_dong_trong_so():
    """Thêm một BƯỚC mà quên khai soát → đỏ.

    Vì sao BƯỚC chứ không chỉ ĐO: `SKILL.md` bảo dùng công cụ ấy *"sau khi
    viết một kết luận, nhờ nó tìm chỗ trong tài liệu nói ngược lại"*. Một
    BƯỚC **là** một kết luận. Đo 16/09/2026 trên cả sổ: 10 trên 84 BƯỚC
    có nhắc tới nó, và lần gần nhất xảy ra vì người dùng viết thẳng yêu
    cầu ấy trong tin nhắn — tức cơ chế thật là trí nhớ của người dùng.
    """
    so = _so()
    co = so["soat"]
    thieu = [t for t in ten_buoc(STATE.read_text(encoding="utf-8"),
                                 so["_moc_buoc"])
             if t not in co]
    assert not thieu, (
        f"Cac BUOC sau chua khai da soat cheo hay chua: {thieu}\n"
        f"Them mot dong vao {SO.name}: hoi that (`phat_hien` hoac "
        f"`khong_tim_thay_gi`), hoac — chi tu BUOC {so['_moc_chi_hoi_khi_doi_luat']} "
        f"va chi khi khong cham file luat — `khong_bat_buoc_vi`.")
    print(f"PASS  moi BUOC tu {so['_moc_buoc']} deu co dong khai")


def _so_dinh_ky() -> dict:
    return json.loads(SO_DINH_KY.read_text(encoding="utf-8"))


def test_SO_DINH_KY_moi_luot_deu_khai_PHAM_VI_va_KET_QUA():
    """Nhịp soát 2 ngày, người dùng chốt 16/09/2026.

    Một lượt "đã soát" không nói ra SOÁT GÌ và RA GÌ thì nó là một dấu tích
    vào ô trống — đúng thứ `test_LY_DO_KHONG_SOAT_…` chặn cho sổ kia. Nên
    mỗi lượt phải mang phạm vi thật, và phải kết bằng MỘT trong hai: có
    phát hiện, hoặc khai thẳng là không tìm thấy gì.
    """
    ds = _so_dinh_ky()["lan_soat"]
    assert ds, "so rong — mot nhip khong co luot nao la mot nhip khong ton tai"
    for x in ds:
        n = x.get("ngay", "")
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", n), f"ngay sai dinh dang: {n!r}"
        pv = x.get("pham_vi", "").strip()
        assert len(pv) >= 40, f"{n}: pham vi qua ngan ({len(pv)}) — {pv!r}"
        co_pd = bool(x.get("phat_hien"))
        co_kh = x.get("khong_tim_thay_gi") is True
        assert co_pd or co_kh, (
            f"{n}: khong khai ket qua — phai co `phat_hien`, hoac "
            f"`khong_tim_thay_gi: true`")
        assert not (co_pd and co_kh), f"{n}: khai ca hai the"
    print(f"PASS  {len(ds)} luot soat dinh ky, moi luot co pham vi va ket qua")


def test_SO_DINH_KY_moi_PHAT_HIEN_kem_LENH_va_PHAN_QUYET():
    """Cùng hợp đồng với sổ soát chéo: chỉ ra chỗ thì phải tự kiểm lại.

    Và `phan_quyet` mở đầu bằng THẬT/SAI — một lượt soát kết luận *"vẫn
    đúng"* là một kết quả hợp lệ và phải ghi được, nếu không thì sổ chỉ
    chứa tin xấu và người đọc tưởng mọi lượt soát đều tìm ra lỗi.
    """
    for x in _so_dinh_ky()["lan_soat"]:
        for i, pd in enumerate(x.get("phat_hien", [])):
            dau = f"{x['ngay']}[{i}]"
            assert pd.get("noi_dung", "").strip(), f"{dau}: thieu noi_dung"
            tk = pd.get("tu_kiem", "").strip()
            assert len(tk) >= 15, f"{dau}: `tu_kiem` qua ngan: {tk!r}"
            pq = pd.get("phan_quyet", "").strip()
            assert any(pq.upper().startswith(k) for k in ("THẬT", "SAI")), (
                f"{dau}: `phan_quyet` phai mo dau bang THAT hoac SAI")
    print("PASS  moi phat hien dinh ky deu co lenh tu kiem va phan quyet")


def test_SO_DINH_KY_phai_khai_vi_sao_KHONG_phai_nhip_CAP_NHAT():
    """Con số đã đổi cái đích — sổ phải mang nó, không để trong đầu ai.

    Người dùng đề xuất nhịp cho việc *cập nhật*. Đo ra: SKILL và bảng lỗi
    có sửa **9 trên 14 ngày** gần nhất, tức việc ấy đã chạy theo sự kiện.
    Nhịp này nhắm nửa kia — soát lại thứ ĐÃ CÓ. Một người đọc sổ mà không
    biết điều đó sẽ tưởng nhịp 2 ngày là nhịp sửa tài liệu.
    """
    so = _so_dinh_ky()
    vs = so.get("_vi_sao_KHONG_phai_nhip_CAP_NHAT", "")
    assert len(vs) >= 150, "so thieu loi khai ve viec no KHONG phai nhip cap nhat"
    assert "9 trên 14" in vs or "9 tren 14" in vs, (
        "loi khai phai mang CON SO da do, khong chi mang lap luan")
    assert so.get("_gioi_han"), "so thieu muc gioi han cua cong cu sinh danh sach"
    print("PASS  so khai ro no nham nua nao, kem con so")


def test_MOI_PHEP_DO_da_ky_deu_co_mot_dong_trong_so():
    """Thêm một ĐO mà quên khai soát → đỏ. Đó là toàn bộ việc của gác này."""
    co = _so()["soat"]
    thieu = [t for t in ten_phep_do(TIEU_CHI.read_text(encoding="utf-8"))
             if t not in co]
    assert not thieu, (
        f"Cac phep do sau chua khai da soat cheo hay chua: {thieu}\n"
        f"Them mot dong vao {SO.name} — hoac `phat_hien`, hoac "
        f"`khong_soat_vi` kem ly do that.")
    print(f"PASS  {len(co)} phep do deu co dong khai")


def test_MOI_DONG_phai_khai_MOT_trong_BA_the_khong_duoc_hai_cai():
    """`phat_hien` XOR `khong_soat_vi` XOR `khong_bat_buoc_vi`. Hai cái là nói nước đôi.

    Thẻ thứ ba thêm ở BƯỚC 164 (08/10/2026). Người dùng đồng ý thu hẹp Quy tắc 3,
    trả lời nguyên văn: "Đồng ý" cho câu "Giảm phần việc quy trình: soát tự động
    mỗi tuần, chỉ hỏi NotebookLM cho những BƯỚC đổi kết luận đo hoặc đổi luật".
    Đây là nới CÓ CHỦ ĐÍCH: gác vẫn đòi đúng MỘT thẻ, và thẻ mới chỉ hợp lệ khi
    máy xác nhận BƯỚC không chạm file luật (`test_O_KHONG_BAT_BUOC_…` bên dưới).
    """
    cac_the = ("phat_hien", "khong_soat_vi", "khong_bat_buoc_vi")
    for ten, d in _so()["soat"].items():
        co = [k for k in cac_the if k in d]
        assert co, f"{ten}: khong khai gi ca"
        assert len(co) == 1, f"{ten}: khai nhieu hon mot the: {co}"
    print("PASS  moi dong khai dung mot the")


def test_LY_DO_KHONG_SOAT_khong_duoc_rong_va_khong_duoc_chung_chung():
    """`khong_soat_vi: ""` hay `"khong can"` bị từ chối — cùng cơ chế `# bia-ok:`.

    Một ô thoát không đòi lý do thật thì nó là một ô thoát tự do, và gác
    này thành trang trí (lỗi 31). Từ BƯỚC 164 gác này canh cả `khong_bat_buoc_vi`
    (người dùng "Đồng ý" 08/10/2026): ô mới cũng không được là câu thần chú.
    """
    MO_HO = ("khong can", "không cần", "khong quan trong", "n/a", "-", "sau")
    for ten, d in _so()["soat"].items():
        for o in ("khong_soat_vi", "khong_bat_buoc_vi"):
            ly_do = d.get(o)
            if ly_do is None:
                continue
            assert len(ly_do.strip()) >= 25, (
                f"{ten}: ly do {o} qua ngan ({len(ly_do.strip())} ky tu) — "
                f"{ly_do!r}")
            assert ly_do.strip().lower() not in MO_HO, f"{ten}: ly do chung chung"
    print("PASS  moi ly do khong-soat / khong-bat-buoc deu cu the")


#: BA ô, không phải hai — cùng quy ước với `vnstock_goi.kiem_goi`,
#: `lich_giao_dich.chan_doan` và mọi máy đo nâng gói.
#:
#: Ô thứ ba thêm 17/09/2026. Bản trước chỉ nhận THẬT/SAI, nên một lượt soát
#: ĐÃ HỎI mà không đọc được câu trả lời **không có chỗ để ghi** — và cách
#: duy nhất còn lại là bịa một phán quyết hoặc im lặng. Đúng lỗi 66 trong
#: một hình dạng mới: gộp *"chưa kiểm được"* vào *"không có gì"*.
HOP_LE = ("THẬT", "SAI", "CHƯA KIỂM ĐƯỢC")


def test_MOI_PHAT_HIEN_phai_kem_LENH_tu_kiem_va_mot_PHAN_QUYET():
    """Giới hạn của công cụ: nó chỉ ra CHỖ đáng nhìn, nó không phán được.

    `SKILL.md`: *"Mọi phát hiện của nó phải tự kiểm lại, bằng `grep` hoặc
    bằng cách đọc mã."* Nên mỗi phát hiện phải mang theo một LỆNH đã chạy và
    một phán quyết — không được để trống một bên.
    """
    for ten, d in _so()["soat"].items():
        for i, pd in enumerate(d.get("phat_hien", [])):
            dau = f"{ten}[{i}]"
            assert pd.get("noi_dung", "").strip(), f"{dau}: thieu noi_dung"
            tk = pd.get("tu_kiem", "").strip()
            assert tk, f"{dau}: thieu `tu_kiem` — phat hien chua duoc kiem lai"
            assert len(tk) >= 15, f"{dau}: `tu_kiem` qua ngan: {tk!r}"
            pq = pd.get("phan_quyet", "").strip()
            assert pq, f"{dau}: thieu `phan_quyet`"
            assert any(pq.upper().startswith(k) for k in HOP_LE), (
                f"{dau}: `phan_quyet` phai mo dau bang mot trong "
                f"{HOP_LE}, nhan {pq[:40]!r}")
    print("PASS  moi phat hien deu co lenh tu kiem va phan quyet")


#: Dòng bắt buộc trong mọi câu gửi sổ tay, từ `_moc_ngon_ngu` trở đi.
#: Người dùng chốt 17/09/2026: hỏi bằng tiếng Anh, đòi trả lời tiếng Việt.
DOI_TRA_LOI_VIET = "answer in vietnamese"


def test_CAU_HOI_tu_MOC_NGON_NGU_phai_DOI_TRA_LOI_TIENG_VIET():
    """Câu gửi sổ tay phải NÓI RA nó muốn câu trả lời bằng tiếng gì.

    GIỚI HẠN, khai thẳng: gác này chỉ kiểm câu hỏi **có mang** dòng ấy.
    Nó **không** kiểm được phần còn lại có thật sự là tiếng Anh không —
    một câu hỏi hợp lệ có quyền trích nguyên văn tài liệu tiếng Việt, và
    bắt nó sạch dấu sẽ đẩy người hỏi sang *kể lại* thay vì *dẫn lại*.
    Nửa ấy là kỷ luật, không phải cơ chế.

    Mốc đặt ở ngày SAU ngày chốt: các mục 17/09 đã hỏi xong trước khi có
    quyết định, và sửa lời khai của chúng cho hợp gác mới là viết lại
    lịch sử.
    """
    so = _so()
    moc = so.get("_moc_ngon_ngu")
    assert moc, "so thieu `_moc_ngon_ngu` — gac nay khong biet ap tu dau"
    thieu = []
    for ten, d in so["soat"].items():
        if not isinstance(d, dict) or d.get("ngay", "") < moc:
            continue
        ch = d.get("cau_hoi")
        if ch and DOI_TRA_LOI_VIET not in ch.lower():
            thieu.append(ten)
    assert not thieu, (
        f"tu moc {moc}, cau hoi phai mang dong doi tra loi tieng Viet "
        f"({DOI_TRA_LOI_VIET!r}) — thieu o: {thieu}")
    print(f"PASS  moi cau hoi tu {moc} deu doi tra loi tieng Viet")


def test_O_THU_BA_khong_duoc_thanh_CUA_THOAT():
    """`CHƯA KIỂM ĐƯỢC` cho MỘT phát hiện là trung thực; cho TẤT CẢ thì không.

    Một lượt soát mà mọi phát hiện đều *"chưa kiểm được"* là một lượt
    `khong_soat_vi` mặc áo khác — và nó lách đúng cái gác đòi nêu lý do cụ
    thể. Ô thứ ba sinh ra để khỏi phải bịa, không phải để khỏi phải soát.
    """
    for ten, d in _so()["soat"].items():
        ds = d.get("phat_hien") or []
        if not ds:
            continue
        chua = [p for p in ds
                if p.get("phan_quyet", "").strip().upper()
                .startswith("CHƯA KIỂM ĐƯỢC")]
        assert len(chua) < len(ds), (
            f"{ten}: {len(chua)}/{len(ds)} phat hien deu CHUA KIEM DUOC — "
            f"day la mot luot `khong_soat_vi` mac ao khac")
    print("PASS  o thu ba khong thanh cua thoat")


def test_SO_nay_phai_ghi_GIOI_HAN_cua_cong_cu():
    """Công cụ chỉ thấy TÀI LIỆU. Quên điều đó là mượn thẩm quyền nó không có.

    Loại lỗi nặng nhất của dự án — tài liệu lệch MÃ — nó không bắt được cái
    nào. Sổ này phải tự mang câu ấy, vì người đọc sổ có thể không đọc skill.
    """
    so = _so()
    assert "_gioi_han_cua_cong_cu" in so, "so thieu muc gioi han"
    gh = so["_gioi_han_cua_cong_cu"]
    assert "TÀI LIỆU" in gh and "MÃ" in gh, (
        "muc gioi han phai noi ro no chi thay TAI LIEU, khong thay MA")
    print("PASS  so tu mang gioi han cua cong cu")


def test_SO_nay_phai_ghi_CA_gioi_han_NGUON_LA_BAN_CHUP():
    """Khai MỘT giới hạn không phải khai ĐỦ — lỗi 60.

    Tới 14/09/2026 sổ khai đúng một giới hạn (*"chỉ thấy TÀI LIỆU"*) và
    gác trên vẫn xanh — trong khi nguồn `STATE.md` của sổ tay dừng ở
    **BƯỚC 41** còn repo đã tới **73**: 32 mục, 30% số ký tự, nằm ngoài
    tầm nhìn suốt **sáu ngày**. Ba lượt soát đã ghi vào sổ đều chạy trên
    bản thiếu ấy.

    Một bản chụp cũ đi trong im lặng, và im lặng thì không gác nào nghe
    được. Nên lời khai phải mang theo **CÁCH ĐO** độ tươi, không chỉ nêu
    rằng giới hạn ấy tồn tại — cùng cơ chế `# bia-ok:`: không cấm, buộc
    nói ra.
    """
    so = _so()
    assert "_gioi_han_NGUON_LA_BAN_CHUP" in so, (
        "so thieu muc `_gioi_han_NGUON_LA_BAN_CHUP` — xem loi 60")
    gh = so["_gioi_han_NGUON_LA_BAN_CHUP"]
    assert "bản chụp" in gh.lower(), (
        "muc nay phai noi ro NGUON LA BAN CHUP")
    assert "BƯỚC" in gh and "grep" in gh, (
        "loi khai phai kem CACH DO do tuoi (hoi so tay muc BUOC lon nhat, "
        "doi chieu bang `grep -c`) — neu ra rang gioi han ton tai thi "
        "khong ai do duoc no")
    print("PASS  so khai ca gioi han thu hai, kem cach do")


def test_DOC_TEN_PHEP_DO_bang_TIEU_DE_chu_khong_bang_chu_xuat_hien():
    """Chữ "ĐO 5" nằm đầy trong văn xuôi; chỉ tiêu đề `## ĐO 5 —` mới tính.

    Đây là lỗi 30/35/36 của dự án — đọc sự XUẤT HIỆN của một chữ thay vì
    VAI TRÒ của nó. Khoá nó bằng một mẫu dựng tay, không bằng file thật.
    """
    mau = (
        "# Tieu chi\n"
        "Doan van xuoi nhac ĐO 5 va ĐO 6 nhieu lan, ĐO 5 nua.\n"
        "## ĐO 7 — mot phep do that\n"
        "Trong than muc nay lai nhac ĐO 7 va ĐO 8.\n"
        "### ĐO 9 — tieu de CAP BA, khong phai muc\n"
        "## ĐO 10 — mot phep do nua\n"
    )
    assert ten_phep_do(mau) == ["ĐO 7", "ĐO 10"], ten_phep_do(mau)
    print("PASS  chi tieu de cap hai moi tinh, van xuoi thi khong")


def test_SO_nay_phai_mang_MOC_BUOC_va_ly_do_cua_no():
    """Mốc là MỘT con số quyết định phạm vi cả cái gác — nó phải ở trong sổ,
    kèm lý do, chứ không nằm rải trong mã của test và của hook.
    """
    so = _so()
    assert isinstance(so.get("_moc_buoc"), int), "so thieu `_moc_buoc`"
    vs = so.get("_vi_sao_co_moc_buoc", "")
    assert len(vs) >= 100, "moc khong kem ly do doc duoc"
    assert "ĐO" in vs and "BƯỚC" in vs, (
        "ly do phai noi ro vi sao quan the doi tu DO sang BUOC")
    print(f"PASS  moc BUOC = {so['_moc_buoc']}, kem ly do")


def test_MOC_BUOC_khong_duoc_NANG_cho_toi_khi_gac_thanh_RONG():
    """Nâng ngưỡng là nới luôn phép kiểm — lỗ hổng đã sống sót một lần.

    Ngày 15/09/2026 đột biến `TRAN_KY_TU` lên 10 triệu **sống sót**, vì
    test so với chính hằng số của module. Ở đây hình dạng ấy quay lại dưới
    dạng khác: đặt `_moc_buoc` = 9999 thì không BƯỚC nào bị đòi, và mọi
    gác phía trên vẫn xanh — một cái gác im lặng hoàn hảo.

    Không so với một con số ghim (nó sẽ trôi). So với HẬU QUẢ: quần thể bị
    đòi phải KHÁC RỖNG.
    """
    so = _so()
    bi_doi = ten_buoc(STATE.read_text(encoding="utf-8"), so["_moc_buoc"])
    assert bi_doi, (
        f"`_moc_buoc` = {so['_moc_buoc']} khong doi BUOC nao ca — gac nay "
        f"dang canh mot quan the RONG, tuc no khong the do gi. Ha moc "
        f"xuong, dung nang len cho toi khi no im.")
    print(f"PASS  moc {so['_moc_buoc']} doi {len(bi_doi)} BUOC, khong rong")


def test_PHEP_LOC_thu_tren_mot_MAU_KHAC_RONG():
    """Thử phép lọc trên một mẫu CÓ mục chưa khai — không thử trên sổ thật.

    Sổ thật hiện đã khai đủ, nên mọi phép so trên nó là phép so hai tập
    RỖNG: nó xanh với bản đúng và xanh với bản hỏng như nhau. Đục thử
    16/09/2026 chứng minh điều đó — hai đột biến vào hook sống sót một
    phép canh viết riêng để bắt chúng. Lỗi 66, lần thứ ba trong ngày.

    Mẫu dựng tay giữ cho câu hỏi *"phép lọc có chạy không"* luôn đo được.
    """
    sys.path.insert(0, str(GOC / "tools"))
    from soat_loi_khai_cu import buoc_chua_khai

    mau = (
        "# So tay\n"
        "Van xuoi nhac BƯỚC 90 va BƯỚC 91 nhieu lan.\n"
        "## BƯỚC 79 — truoc moc\n"
        "## BƯỚC 81 — da khai\n"
        "### BƯỚC 82 — tieu de cap ba\n"
        "## BƯỚC 83 — CHUA khai\n"
    )
    assert buoc_chua_khai(mau, {"BƯỚC 81"}, 81) == ["BƯỚC 83"], (
        buoc_chua_khai(mau, {"BƯỚC 81"}, 81))
    # va no phai thay CA HAI khi khong co gi duoc khai
    assert buoc_chua_khai(mau, (), 81) == ["BƯỚC 81", "BƯỚC 83"]
    print("PASS  phep loc chay dung tren mau co muc chua khai")


def test_HOOK_goi_dung_ban_cai_dat_DUY_NHAT():
    """Bản tin mở phiên phải đi qua `soat_loi_khai_cu.buoc_chua_khai`.

    Đọc AST, không đọc `in`: cái tên có thể nằm trong chú thích. Gác hình
    DẠNG thay vì gác giá trị, vì giá trị hiện là một danh sách rỗng và một
    danh sách rỗng không phân biệt được bản đúng với bản hỏng.
    """
    src = (GOC / "tools" / "cua_mo_phien.py").read_text(encoding="utf-8")
    cay = ast.parse(src)
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef)
               and n.name == "buoc_chua_khai_soat")
    goi = {n.func.id for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "buoc_chua_khai" in goi, (
        "cua_mo_phien.buoc_chua_khai_soat() khong con goi ban cai dat "
        "duy nhat — no dang tu dung lai phep loc, tuc mo lai cho de troi")
    print("PASS  hook goi ban cai dat duy nhat")


def test_DOC_TEN_BUOC_bang_TIEU_DE_va_TON_TRONG_MOC():
    """Hai điều cùng lúc: chỉ tiêu đề cấp hai mới tính, VÀ mốc phải chặn.

    Mẫu dựng tay chứ không dùng file thật — một gác khẳng định *"không
    thiếu mục nào"* mà chạy trên quần thể rỗng thì nó không đo gì.
    """
    mau = (
        "# So tay\n"
        "Doan van xuoi nhac BƯỚC 82 va BƯỚC 99 nhieu lan.\n"
        "## BƯỚC 79 — truoc moc, KHONG duoc doi\n"
        "## BƯỚC 81 — dung moc, phai doi\n"
        "### BƯỚC 83 — tieu de CAP BA, khong phai muc\n"
        "## BƯỚC 84 — sau moc, phai doi\n"
    )
    assert ten_buoc(mau, moc=81) == ["BƯỚC 81", "BƯỚC 84"], ten_buoc(mau, 81)
    # Va moc that su chan: ha moc xuong thi muc 79 phai hien ra.
    assert "BƯỚC 79" in ten_buoc(mau, moc=1), "moc khong thuc su loc gi"
    print("PASS  doc BUOC bang tieu de, va moc thuc su chan")
#: ─────────────────────────────────────────────────────────────────────
#: MỖI BƯỚC ĐỀU PHẢI ĐI QUA SỔ TAY — người dùng chốt 18/09/2026
#:
#: Ô thoát `khong_soat_vi` ra đời để khỏi phải BỊA; ngày 18/09 nó đã thành
#: chỗ để khỏi phải HỎI — sáu lượt liên tiếp, lỗi 86. Mốc đọc từ
#: `_moc_bat_buoc_hoi` trong chính sổ, KHÔNG gõ ở đây: `tools/cua_mo_phien.py`
#: đọc đúng con số ấy, và một ngưỡng gõ tay hai chỗ sẽ trôi khỏi nhau.


def _moc_bat_buoc() -> int:
    so = _so()
    m = so.get("_moc_bat_buoc_hoi")
    assert isinstance(m, int), (
        "so thieu `_moc_bat_buoc_hoi` — gac nay khong biet ap tu dau")
    return m


def buoc_tu_moc_bat_buoc() -> list[str]:
    """`## BƯỚC n` trong STATE.md có n >= `_moc_bat_buoc_hoi`. SUY RA từ đĩa."""
    return ten_buoc(STATE.read_text(encoding="utf-8"), _moc_bat_buoc())


def _moc_chi_hoi() -> int:
    """Mốc BƯỚC 164: từ đó BƯỚC không đổi luật được khai `khong_bat_buoc_vi`."""
    m = _so().get("_moc_chi_hoi_khi_doi_luat")
    assert isinstance(m, int) and not isinstance(m, bool), (
        "so thieu `_moc_chi_hoi_khi_doi_luat` — gac nay khong biet ap tu dau")
    return m


def _tools_so_buoc(ten: str):
    sys.path.insert(0, str(GOC / "tools"))
    from buoc_cham_luat import so_buoc
    return so_buoc(ten)


def test_TU_MOC_BAT_BUOC_moi_BUOC_deu_phai_HOI_THAT():
    """Một BƯỚC khai `khong_soat_vi` từ mốc này trở đi → ĐỎ.

    Đây là phép đục đầu tiên dựng lại NGUYÊN VĂN lỗi 86: hôm ấy sáu mục
    liên tiếp khai ô thoát, mỗi lượt một lý do thật sự khác nhau và thật sự
    cụ thể — nên mọi gác so CHỮ đều im. Thứ máy đọc được là **ô thoát có
    được dùng hay không**, và từ mốc này câu trả lời phải là không.

    Đo trước khi siết, từ mốc cũ 81: **8 hỏi thật / 19 bỏ qua trên 27
    BƯỚC**. Không phải một lượt trượt — là tỷ lệ nền 70%.

    PHẢI khai đủ BA thứ: `cau_hoi` nguyên văn, và MỘT trong hai kết quả.
    `phat_hien: []` KHÔNG phải kết quả — nó không phân biệt được *đã hỏi
    và không thấy gì* với *chưa hỏi*, mà phân biệt ấy là toàn bộ việc của
    gác này. Muốn khai "đã hỏi, không thấy gì" thì dùng
    `khong_tim_thay_gi: true`, cùng quy ước với `docs/soat-dinh-ky.json`.

    SỬA CÓ CHỦ ĐÍCH ở BƯỚC 164 (08/10/2026) — gác này KHÔNG bị gỡ, nó đổi đối
    tượng canh. Người dùng đồng ý thu hẹp Quy tắc 3 (nguyên văn: "Đồng ý" cho
    câu "Giảm phần việc quy trình: soát tự động mỗi tuần, chỉ hỏi NotebookLM cho
    những BƯỚC đổi kết luận đo hoặc đổi luật"). Từ `_moc_chi_hoi_khi_doi_luat`
    một BƯỚC được thay việc hỏi bằng ô `khong_bat_buoc_vi` — nhưng ô ấy KHÔNG
    được miễn kiểm ở đây một cách im lặng: nó được chuyển sang
    `test_O_KHONG_BAT_BUOC_chi_hop_le_khi_MAY_xac_nhan_BUOC_khong_cham_luat`,
    nơi máy đọc lịch sử git để phán. Mọi BƯỚC trước mốc ấy giữ luật cũ.
    """
    so = _so()
    moc = _moc_bat_buoc()
    moc_hep = _moc_chi_hoi()
    loi = []
    for ten in buoc_tu_moc_bat_buoc():
        d = so["soat"].get(ten)
        if not isinstance(d, dict):
            loi.append(f"{ten}: khong co dong khai nao")
            continue
        if "khong_soat_vi" in d:
            loi.append(f"{ten}: con khai `khong_soat_vi` — tu BUOC {moc} "
                       f"o thoat nay KHONG con duoc nhan")
            continue
        if "khong_bat_buoc_vi" in d:
            n = _tools_so_buoc(ten)
            if n is None or n < moc_hep:
                loi.append(f"{ten}: o `khong_bat_buoc_vi` chi duoc nhan tu BUOC "
                           f"{moc_hep} — truoc do MOI BUOC deu phai hoi that")
            continue                    # phan con lai do gac rieng phan xu
        if not (d.get("cau_hoi") or "").strip():
            loi.append(f"{ten}: thieu `cau_hoi` nguyen van")
        co_pd = bool(d.get("phat_hien"))
        co_kh = d.get("khong_tim_thay_gi") is True
        if not (co_pd or co_kh):
            loi.append(f"{ten}: khong khai KET QUA — `phat_hien` khac rong, "
                       f"hoac `khong_tim_thay_gi: true`")
        if co_pd and co_kh:
            loi.append(f"{ten}: khai CA HAI the ket qua")
    assert not loi, (
        "MOI BUOC deu phai di qua so tay (nguoi dung chot 18/09/2026):\n  "
        + "\n  ".join(loi))
    print(f"PASS  moi BUOC tu {moc} deu HOI THAT, khong con o thoat")


def test_CAU_HOI_tu_MOC_BAT_BUOC_phai_mang_MOT_LOI_THOAT():
    """Thiếu lối thoát thì sổ tay **bịa thay vì từ chối** — BƯỚC 107.

    Gác này KHÔNG gõ sẵn một câu lối thoát mẫu. Gõ sẵn thì nó thành khẩu
    hiệu dán vào, và một khẩu hiệu dán vào thì đo được sự có mặt của chữ
    chứ không đo được sự có mặt của lối thoát. Nó đòi mục **tự khai**
    `o_thoat`, rồi kiểm rằng chuỗi ấy THẬT SỰ là một phần của câu đã gửi —
    suy ra từ chính dữ liệu, đúng luật *"suy ra, đừng gõ"*.

    Sửa có chủ đích ở BƯỚC 164 (người dùng "Đồng ý" 08/10/2026): mục khai
    `khong_bat_buoc_vi` không có câu hỏi nên không có lối thoát để kiểm; gác chỉ
    bỏ qua mục ấy SAU KHI gác kia đã đòi máy xác nhận nó không chạm file luật.
    """
    so = _so()
    for ten in buoc_tu_moc_bat_buoc():
        d = so["soat"].get(ten) or {}
        if "khong_soat_vi" in d or "khong_bat_buoc_vi" in d:
            continue                  # phep kiem tren da goi ten muc nay roi
        ot = (d.get("o_thoat") or "").strip()
        assert len(ot) >= 20, (
            f"{ten}: thieu `o_thoat` hoac qua ngan ({len(ot)}) — xem BUOC 107")
        ch = d.get("cau_hoi") or ""
        assert ot in ch, (
            f"{ten}: `o_thoat` KHONG nam trong `cau_hoi` — mot loi thoat "
            f"khai ma khong gui di thi khong phai loi thoat")
    print("PASS  moi cau hoi tu moc bat buoc deu mang mot loi thoat that")


def test_MOC_BAT_BUOC_khong_duoc_NANG_cho_toi_khi_gac_thanh_RONG():
    """Nâng mốc là nới luôn phép kiểm — cùng lỗ hổng với `_moc_buoc`.

    Đặt `_moc_bat_buoc_hoi` = 9999 thì không BƯỚC nào bị đòi và cả hai gác
    trên vẫn xanh: một cái gác im lặng hoàn hảo. So với HẬU QUẢ, không so
    với một con số ghim — con số thì trôi, hậu quả thì không.
    """
    moc = _moc_bat_buoc()
    bi_doi = buoc_tu_moc_bat_buoc()
    assert bi_doi, (
        f"`_moc_bat_buoc_hoi` = {moc} khong doi BUOC nao ca — gac nay dang "
        f"canh mot quan the RONG. Ha moc xuong, dung nang len cho toi khi "
        f"no im.")
    print(f"PASS  moc bat buoc {moc} doi {len(bi_doi)} BUOC, khong rong")


def test_SO_phai_mang_MOC_BAT_BUOC_kem_LY_DO_va_CON_SO():
    """Một quyết định siết luật phải mang theo phép đo đã đứng sau nó.

    Cùng hợp đồng với `test_SO_DINH_KY_phai_khai_vi_sao_KHONG_phai_nhip_CAP_NHAT`:
    lời khai phải mang CON SỐ đã đo, không chỉ mang lập luận. Ở đây con số
    là tỷ lệ bỏ qua trên quần thể cũ — thứ làm cho việc siết có nghĩa.
    """
    vs = _so().get("_vi_sao_co_moc_bat_buoc_hoi", "")
    assert len(vs) >= 150, "moc bat buoc khong kem ly do doc duoc"
    assert "19/27" in vs, (
        "loi khai phai mang CON SO da do (8 hoi that / 19 bo qua tren 27 "
        "BUOC tu moc 81), khong chi mang lap luan")
    assert "BƯỚC" in vs and "ĐO" in vs, (
        "loi khai phai noi ro PHAM VI la BUOC chu khong phai DO")
    print("PASS  moc bat buoc kem ly do va con so")


def _ham_hook(ten: str) -> ast.FunctionDef:
    src = (GOC / "tools" / "cua_mo_phien.py").read_text(encoding="utf-8")
    return next(n for n in ast.walk(ast.parse(src))
                if isinstance(n, ast.FunctionDef) and n.name == ten)


def test_HOOK_doc_MOC_BAT_BUOC_tu_SO_chu_KHONG_go_con_so():
    """Bản tin mở phiên phải ĐỌC mốc từ sổ, không gõ lại nó.

    Hai chỗ cùng giữ một ngưỡng thì chúng sẽ trôi khỏi nhau — dự án đã trả
    giá cho đúng hình dạng đó ở `N_DAY_DU` 596/451 và ở cờ C5. Đọc AST chứ
    không đọc `in`: con số 108 có thể nằm trong chú thích.
    """
    ham = _ham_hook("moc_bat_buoc_hoi")
    doc_file = {n.func.attr for n in ast.walk(ham)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "read_text" in doc_file or "loads" in doc_file, (
        "moc_bat_buoc_hoi() khong doc so — no dang lay moc tu dau?")
    go_tay = [n.value for n in ast.walk(ham)
              if isinstance(n, ast.Constant) and isinstance(n.value, int)
              and not isinstance(n.value, bool) and n.value >= 100]
    assert not go_tay, (
        f"moc_bat_buoc_hoi() go SAN mot con so moc: {go_tay} — moc phai doc "
        f"tu `_moc_bat_buoc_hoi` trong so")
    print("PASS  hook doc moc tu so, khong go con so")


def test_BAN_TIN_phai_NOI_RA_moc_bat_buoc():
    """Luật chỉ có tác dụng ở chỗ còn quyền chọn: lúc MỞ PHIÊN.

    Ngày 16/09/2026 đo được rằng một gác chỉ đỏ lúc chạy test thì nó đỏ
    SAU khi việc đã làm xong. Dòng nợ soát chéo vì thế phải nói ra rằng ô
    thoát đã đóng — nếu không, người đọc bản tin vẫn tưởng mình còn hai
    lựa chọn như cũ.
    """
    ham = _ham_hook("ban_tin")
    goi = {n.func.id for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "moc_bat_buoc_hoi" in goi, (
        "ban_tin() khong goi moc_bat_buoc_hoi() — ban tin mo phien van moi "
        "nguoi khai `khong_soat_vi` nhu cu")
    assert "moc_chi_hoi_khi_doi_luat" in goi, (
        "ban_tin() khong goi moc_chi_hoi_khi_doi_luat() — ban tin van noi "
        "'moi BUOC phai HOI' sau khi Quy tac 3 da thu hep (BUOC 164)")
    print("PASS  ban tin mo phien noi ra moc bat buoc")


#: ─────────────────────────────────────────────────────────────────────
#: QUY TẮC 3 THU HẸP — BƯỚC 164, người dùng "Đồng ý" 08/10/2026
#:
#: Một BƯỚC PHẢI hỏi thật khi nó đổi luật hoặc kết luận đo; BƯỚC khác khai
#: `khong_bat_buoc_vi`, và ô ấy chỉ hợp lệ khi MÁY (lịch sử git) xác nhận BƯỚC
#: không chạm file luật. Các gác phía trên được SỬA để canh luật mới, không bị
#: gỡ; các gác dưới đây là nửa còn lại.


def _chay_gac_o_moi(soat: dict, file_cua, moc: int = 164) -> list[str]:
    sys.path.insert(0, str(GOC / "tools"))
    from buoc_cham_luat import loi_o_khong_bat_buoc
    return loi_o_khong_bat_buoc(soat, moc, file_cua)


LY_DO_MAU = "BUOC chi ghi ket qua luot soat dinh ky, khong doi luat hay ket luan do"


def test_O_KHONG_BAT_BUOC_chi_hop_le_khi_MAY_xac_nhan_BUOC_khong_cham_luat():
    """Gác THẬT: mọi mục `khong_bat_buoc_vi` của sổ đi qua máy đọc git.

    Sổ hiện CHƯA có mục nào (BƯỚC 164 tự nó đổi luật nên phải hỏi thật), nên phép
    này trên sổ thật là phép so tập rỗng — nó xanh với bản đúng lẫn bản hỏng.
    Thứ chứng minh máy chạy là các ca dựng tay bên dưới, đi qua đúng hàm này.
    """
    sys.path.insert(0, str(GOC / "tools"))
    from buoc_cham_luat import NEO_LICH_SU, file_cua_buoc
    loi = _chay_gac_o_moi(
        _so()["soat"],
        lambda n: file_cua_buoc(GOC, n, neo=NEO_LICH_SU)[0],
        _moc_chi_hoi())
    assert not loi, "\n".join(loi)
    print("PASS  moi o khong_bat_buoc_vi duoc may git xac nhan")


def test_PHAT_DAU_BUOC_cham_CLAUDE_md_ma_khai_o_moi_thi_DO():
    """Dựng lại NGUYÊN VĂN lỗi: BƯỚC sửa một luật nhưng khai 'không bắt buộc'."""
    soat = {"BƯỚC 170": {"ngay": "2026-10-20", "khong_bat_buoc_vi": LY_DO_MAU}}
    loi = _chay_gac_o_moi(soat, lambda n: ["CLAUDE.md", "docs/STATE.md"])
    assert len(loi) == 1 and "CHAM file luat" in loi[0] and "CLAUDE.md" in loi[0], loi
    # cung BUOC do, khong cham file luat nao -> hop le
    assert _chay_gac_o_moi(soat, lambda n: ["docs/STATE.md", "tools/x.py"]) == []


@pytest.mark.parametrize("file_luat", [
    "CLAUDE.md", "NGUYEN-TAC-DO-LUONG.md", "MO-XE-KIEN-TRUC.md",
    ".claude/skills/quy-trinh-lam-viec/SKILL.md",
    "docs/TIEU-CHI-DOC-TRUOC.md", "docs/LO-TRINH.md"])
def test_MOI_file_luat_deu_lam_o_moi_thanh_DO(file_luat):
    soat = {"BƯỚC 170": {"ngay": "2026-10-20", "khong_bat_buoc_vi": LY_DO_MAU}}
    loi = _chay_gac_o_moi(soat, lambda n: ["docs/STATE.md", file_luat])
    assert loi and file_luat in loi[0], loi


def test_O_moi_khong_di_kem_o_HOI_hay_o_THOAT_cu():
    for them in ({"cau_hoi": "x"}, {"phat_hien": []}, {"khong_tim_thay_gi": True},
                 {"khong_soat_vi": "mot ly do du dai de qua duoc cong"}):
        soat = {"BƯỚC 170": {"khong_bat_buoc_vi": LY_DO_MAU, **them}}
        loi = _chay_gac_o_moi(soat, lambda n: [])
        assert loi and "nuoc doi" in loi[0], (them, loi)


@pytest.mark.parametrize("ly_do", ["", "ngan", "khong can", "n/a", "-", "x" * 24])
def test_O_moi_ly_do_RONG_NGAN_hay_CHUNG_CHUNG_thi_DO(ly_do):
    loi = _chay_gac_o_moi({"BƯỚC 170": {"khong_bat_buoc_vi": ly_do}}, lambda n: [])
    assert loi, ly_do


def test_O_moi_ly_do_DAN_LAI_cho_BUOC_khac_thi_DO():
    """Lý do giống hệt ở hai BƯỚC là câu thần chú (lỗi 86); chuẩn hoá khoảng trắng và
    hoa/thường để không lách bằng một dấu cách."""
    soat = {"BƯỚC 170": {"khong_bat_buoc_vi": LY_DO_MAU},
            "BƯỚC 171": {"khong_bat_buoc_vi": "  " + LY_DO_MAU.upper().replace(" ", "  ")}}
    loi = _chay_gac_o_moi(soat, lambda n: [])
    assert len(loi) == 1 and "171" in loi[0] and "170" in loi[0], loi
    soat["BƯỚC 171"]["khong_bat_buoc_vi"] = LY_DO_MAU + " va con ghi them mot ve khac"
    assert _chay_gac_o_moi(soat, lambda n: []) == []


@pytest.mark.parametrize("ten", ["BƯỚC 163", "BƯỚC 108", "BƯỚC 70-73", "ĐO 5"])
def test_O_moi_khong_duoc_lui_ve_BUOC_cu_hay_ten_la(ten):
    """Mốc 164 chặn: dán ô mới vào BƯỚC cũ là viết lại lịch sử."""
    loi = _chay_gac_o_moi({ten: {"khong_bat_buoc_vi": LY_DO_MAU}}, lambda n: [])
    assert loi and "chi hop le cho BUOC >= 164" in loi[0], loi


def test_O_moi_nhan_dung_BUOC_164_la_BUOC_dau_tien_cua_luat_moi():
    """Biên: n == mốc phải được nhận (`n < moc` chứ không `n <= moc`)."""
    assert _chay_gac_o_moi({"BƯỚC 164": {"khong_bat_buoc_vi": LY_DO_MAU}},
                           lambda n: []) == []
    assert _chay_gac_o_moi({"BƯỚC 163": {"khong_bat_buoc_vi": LY_DO_MAU}},
                           lambda n: [])


def test_MAY_DOC_GIT_that_su_duoc_goi_voi_dung_so_BUOC():
    """Máy nhận `file_cua(n)` với n là số BƯỚC của chính mục — không phải số khác."""
    thay = []
    _chay_gac_o_moi({"BƯỚC 177": {"khong_bat_buoc_vi": LY_DO_MAU}},
                    lambda n: thay.append(n) or [])
    assert thay == [177], thay


def test_MOC_CHI_HOI_khong_duoc_NANG_cho_toi_khi_gac_thanh_RONG():
    """Nâng mốc là nới luôn phép kiểm — cùng lỗ hổng với hai mốc kia.

    Đặt `_moc_chi_hoi_khi_doi_luat` = 9999 thì không BƯỚC nào bị đưa vào luật mới
    và các gác xanh trên một quần thể RỖNG. So với HẬU QUẢ, không so một con số."""
    moc = _moc_chi_hoi()
    bi_doi = ten_buoc(STATE.read_text(encoding="utf-8"), moc)
    assert bi_doi, (
        f"`_moc_chi_hoi_khi_doi_luat` = {moc} khong doi BUOC nao ca — gac dang "
        f"canh mot quan the RONG. Ha moc xuong, dung nang len cho toi khi no im.")
    assert moc >= _moc_bat_buoc(), "mốc thu hẹp thấp hơn mốc 'mỗi BƯỚC phải hỏi'"


def test_SO_phai_mang_MOC_CHI_HOI_kem_LY_DO_va_CON_SO_DA_DO():
    """Một quyết định NỚI luật phải mang theo phép đo đứng sau nó và câu trả lời
    nguyên văn của người dùng — nới mà không có chúng là nới lặng lẽ."""
    vs = _so().get("_vi_sao_co_moc_chi_hoi_khi_doi_luat", "")
    assert len(vs) >= 600, "moc thu hep khong kem ly do doc duoc"
    for can in ("Đồng ý", "08/10/2026", "25/30", "6/33", "FILE_LUAT",
                "tools/buoc_cham_luat.py", "khong_soat_vi", "BƯỚC <= 163"):
        assert can in vs, f"loi khai thieu {can!r}"
    assert "MÁY MÙ" in vs, "loi khai phai noi ro cho may khong thay duoc"


def test_BUOC_164_tu_no_DOI_LUAT_nen_phai_HOI_THAT_khong_the_khai_o_moi():
    """Đề bài giao: BƯỚC 164 đổi chính Quy tắc 3, nên là ca đầu tiên của luật mới.

    Nếu ai đó chuyển nó sang `khong_bat_buoc_vi`, gác máy-đọc-git đã đỏ; ca này
    khoá thêm một lớp bằng đúng tên BƯỚC, để lỗi đọc ra từ test chứ không từ git."""
    d = _so()["soat"].get("BƯỚC 164")
    assert isinstance(d, dict), "BƯỚC 164 chua co dong nao trong so"
    assert "khong_bat_buoc_vi" not in d and "khong_soat_vi" not in d
    assert (d.get("cau_hoi") or "").strip(), "BƯỚC 164 doi LUAT nen phai hoi that"
