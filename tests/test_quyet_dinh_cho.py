"""Gác KHUÔN của `docs/QUYET-DINH-CHO.md` — BƯỚC 165 (mốc A5 của `docs/LO-TRINH.md`).

Sổ gom các câu đang chờ người dùng quyết để leader trình trong MỘT phiên. Gác
này không phán câu hỏi nào đúng hay sai (máy không biết); nó giữ ba điều máy biết:

  * mục `chờ` có NGUỒN còn thật, >= 2 LỰA CHỌN, một ĐỀ XUẤT, dữ kiện kèm lệnh và ngày;
  * mục `đã quyết` có câu trả lời NGUYÊN VĂN của người dùng và ngày;
  * mục không bị xoá lặng lẽ (mã liền từ Q1) và HANDOFF vẫn trỏ tới sổ.

Phát đục đầu tiên dựng lại đúng lỗi mà sổ sinh ra để chặn: một mục `đã quyết`
không có câu trả lời nguyên văn (dòng "đã quyết" sống mười lăm ngày ở HANDOFF
mà không ai kiểm xem câu trả lời đâu), và một mục trỏ vào đường đã chết
(`luu_do18` — thư mục HANDOFF còn hỏi "giữ hay xoá" đã không còn trên đĩa).
Quần thể bị đòi KHÁC RỖNG: một bộ đọc trỏ nhầm tệp sẽ xanh trên tập rỗng (lỗi 66).

BƯỚC 166 (09/10/2026) SỬA gác có chủ đích, không nới: người dùng trả lời Q1–Q6, Q8, Q10 nên
Q3 (từng là mục `chờ` mẫu của nhiều phát đục) thành `đã quyết`, và Q5 (mục `hết hiệu lực`
duy nhất) cũng thành `đã quyết` — người dùng đã quyết xoá chứ không phải câu hỏi hết đối
tượng. Các phát đục cần mục `chờ` chuyển sang Q7 / Q11; các phát cần mục `hết hiệu lực`
chạy trên MẪU dựng sẵn `MAU_HET_HIEU_LUC` (khuôn vẫn giữ trạng thái ấy, nên nhánh của nó
vẫn phải đỏ được). Quần thể thật không còn bị đòi có mục `hết hiệu lực`.

BƯỚC 172 (09/10/2026) làm điều tương tự lần thứ hai: người dùng trả lời nốt Q7 · Q11 · Q12 ·
Q13 nên sổ thật KHÔNG còn mục `chờ` nào. Các phát đục nhắm vào nhánh `chờ` (nguồn, lựa chọn,
ĐỀ XUẤT, dữ kiện, ảnh hưởng) chuyển sang MẪU dựng sẵn `MAU_CHO`; khuôn vẫn giữ trạng thái ấy
cho ngày có câu hỏi mới, nên nhánh của nó vẫn phải đỏ được và mẫu sạch phải sạch.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import quyet_dinh_cho as q  # noqa: E402

BA_NGUON_THAT = GOC / "docs" / "QUYET-DINH-CHO.md"


MAU_HET_HIEU_LUC = """# sổ mẫu

## Q1 — Một câu hỏi đã hết đối tượng vì thư mục của nó không còn nữa?

**Trạng thái:** hết hiệu lực

**Nguồn:** `docs/LO-TRINH.md:1 «LỘ TRÌNH — hai đích, năm giai đoạn»`

**Ảnh hưởng:** chỉ dọn dẹp, không đổi hành vi giao dịch hay số đo của dự án.

**Bằng chứng (lệnh + ngày):** ngày 09/10/2026, `ls -d thu-muc-mau` báo không có.

**Dữ kiện đã kiểm (09/10/2026):**
- `ls -d thu-muc-mau` báo không có.
"""


MAU_CHO = """# sổ mẫu

## Q1 — Một câu hỏi mẫu còn chờ người dùng, dựng sẵn để nhánh `chờ` vẫn bị đục được?

**Trạng thái:** chờ

**Nguồn:** `docs/LO-TRINH.md:1 «LỘ TRÌNH — hai đích, năm giai đoạn»`

**Ảnh hưởng:** chỉ là mẫu cho gác, không đổi hành vi giao dịch hay số đo của dự án.

**Lựa chọn:**
- (a) Phương án thứ nhất của mẫu. Hệ quả: không đổi gì.
- (b) Phương án thứ hai của mẫu. Hệ quả: đổi một thứ.
- (c) Phương án thứ ba của mẫu. Hệ quả: đổi hai thứ.

**Đề xuất của leader (ĐỀ XUẤT, mẫu dựng sẵn, chưa ai quyết):** chọn (a) vì rẻ nhất trong ba phương án của mẫu.

**Dữ kiện đã kiểm (09/10/2026):**
- `ls -d thu-muc-mau` báo không có.
"""


def _van() -> str:
    return BA_NGUON_THAT.read_text(encoding="utf-8")


def _loi(van: str) -> list[str]:
    return q.loi_so(q.doc_muc(van), GOC)


def _bien(van: str, cu: str, moi: str) -> str:
    """Đục MỘT chỗ; neo phải khớp đúng một lần, không thì test tự nổ."""
    assert van.count(cu) == 1, f"neo khớp {van.count(cu)} lần: {cu[:60]!r}"
    return van.replace(cu, moi, 1)


def _thay_dong(van: str, bat_dau: str, moi: str) -> str:
    """Thay NGUYÊN MỘT dòng bắt đầu bằng `bat_dau` (phải duy nhất)."""
    cac = [d for d in van.split("\n") if d.startswith(bat_dau)]
    assert len(cac) == 1, f"{len(cac)} dòng bắt đầu bằng {bat_dau!r}"
    return van.replace(cac[0], moi, 1)


# ── quần thể THẬT ────────────────────────────────────────────────────────────

def test_SO_THAT_sach_khuon():
    loi = _loi(_van())
    assert not loi, "sổ vi phạm khuôn:\n  " + "\n  ".join(loi)


def test_QUAN_THE_khong_rong_va_co_du_ba_trang_thai():
    muc = q.doc_muc(_van())
    dem = q.tom_tat(muc)
    assert len(muc) >= 5, f"sổ chỉ đọc ra {len(muc)} mục — bộ đọc hụt hoặc tệp sai"
    assert dem[q.DA_QUYET] >= 1, (
        f"sổ thật không có mục `đã quyết` nào: {dem} — gác sẽ không bao giờ chạy "
        "nhánh đó trên dữ liệu thật")
    # Sổ thật hết mục `chờ` từ BƯỚC 172 (hàng đợi rỗng). Nhánh `chờ` chạy trên mẫu.
    assert q.tom_tat(q.doc_muc(MAU_CHO))[q.CHO] == 1


def test_CHO_van_chay_duoc_tren_mau_dung_san():
    """Sổ thật hết mục `chờ` (BƯỚC 172) nhưng khuôn còn trạng thái ấy: mẫu sạch phải sạch."""
    muc = q.doc_muc(MAU_CHO)
    assert q.tom_tat(muc)[q.CHO] == 1
    assert q.loi_so(muc, GOC) == []


def test_HET_HIEU_LUC_van_chay_duoc_tren_mau_dung_san():
    """Sổ thật hết mục `hết hiệu lực` (09/10/2026) nhưng khuôn còn trạng thái ấy:
    mẫu sạch phải sạch, và nhánh phải đếm được một mục."""
    muc = q.doc_muc(MAU_HET_HIEU_LUC)
    assert q.tom_tat(muc)[q.HET_HIEU_LUC] == 1
    assert q.loi_so(muc, GOC) == []


def test_NAM_MUC_cua_leader_deu_co_mat():
    """Năm câu leader nêu ở LO-TRINH.md mục A5 (08/10/2026). Mục không bị xoá."""
    muc = q.doc_muc(_van())
    chu = {m.ma: (m.tieu_de + " " + m.lay(q.NHAN_NGUON)) for m in muc}
    can = ("44 mẫu", "Vế thứ ba", "Streamlit Cloud", "thiếu giá", "luu_do18")
    thieu = [k for k in can if not any(k in v for v in chu.values())]
    assert not thieu, f"mất mục của leader: {thieu}"


def test_HANDOFF_that_tro_toi_so():
    van = q.HANDOFF.read_text(encoding="utf-8")
    assert q.loi_con_tro_handoff(van) == []


# ── phát đục: dựng lại NGUYÊN VĂN lỗi ───────────────────────────────────────

def test_PHAT_DAU_da_quyet_ma_bo_cau_tra_loi_nguyen_van_thi_DO():
    """Lỗi thật: một dòng 'đã quyết' mà không ai biết người dùng đã nói gì."""
    van = _bien(_van(), '*"Để tới giai đoạn B (Recommended)"*', "(đã chốt)")
    loi = _loi(van)
    assert any("Q9" in x and "nguyên văn" in x for x in loi), loi


def test_PHAT_2_nguon_tro_duong_da_chet_thi_DO():
    """Lỗi thật: `luu_do18` — đường còn được trích trong khi thư mục đã mất."""
    van = _bien(_van(), "`docs/HANDOFF.md:398 «xoá hẳn»`", "`docs/HANDOFF_XOA.md:398 «xoá hẳn»`")
    assert any("không tồn tại" in x for x in _loi(van))


def test_PHAT_3_trich_khong_con_nguyen_van_thi_DO():
    van = _bien(_van(), "«Bộ nhớ hậu nghiệm trên đường quét thật»", "«câu đã bị sửa mất»")
    assert any("KHÔNG còn nguyên văn" in x for x in _loi(van))


def test_PHAT_4_dong_vuot_do_dai_tep_thi_DO():
    van = _bien(_van(), "`docs/HANDOFF.md:576 ", "`docs/HANDOFF.md:9999999 ")
    assert any("vượt độ dài" in x for x in _loi(van))


def test_PHAT_5_nguon_thieu_trich_thi_DO():
    van = _bien(_van(), "`CLAUDE.md:164 «đường thật **giữ 0 mẫu**»`", "`CLAUDE.md:164`")
    assert any("thiếu trích" in x for x in _loi(van))


def test_PHAT_6_nguon_rong_thi_DO():
    """Mục mẫu (`chờ`) mất hết nguồn."""
    van = _thay_dong(MAU_CHO, "**Nguồn:** `docs/LO-TRINH.md:1 ", "**Nguồn:** chưa rõ")
    assert any("Q1" in x and "NGUỒN rỗng" in x for x in _loi(van))


def test_PHAT_7_chi_con_mot_lua_chon_thi_DO():
    van = _bien(MAU_CHO, "- (b) Phương án thứ hai", "(b) Phương án thứ hai")
    van = _bien(van, "- (c) Phương án thứ ba", "(c) Phương án thứ ba")
    assert any("Q1" in x and "lựa chọn" in x for x in _loi(van))


def test_PHAT_8_lua_chon_nhay_chu_thi_DO():
    van = _bien(MAU_CHO, "- (b) Phương án thứ hai", "- (c) Phương án thứ hai")
    van = _bien(van, "- (c) Phương án thứ ba", "- (e) Phương án thứ ba")
    assert any("liền nhau" in x for x in _loi(van))


def test_PHAT_9_bo_chu_DE_XUAT_thi_DO():
    van = _bien(MAU_CHO,
                "**Đề xuất của leader (ĐỀ XUẤT, mẫu dựng sẵn, chưa ai quyết):** chọn (a)",
                "**Đề xuất của leader:** chọn (a)")
    assert any("Q1" in x and "ĐỀ XUẤT" in x for x in _loi(van))


def test_PHAT_10_trang_thai_la_thi_DO():
    van = _bien(MAU_CHO, "**Trạng thái:** chờ", "**Trạng thái:** tạm gác")
    assert any("trạng thái" in x for x in _loi(van))


def test_PHAT_11_xoa_mot_muc_giua_chung_thi_DO():
    """Mục KHÔNG bị xoá: bỏ Q3 làm mã đứt (Q1 Q2 Q4 ...)."""
    van = _van()
    a = van.index("## Q3 — ")
    b = van.index("## Q4 — ")
    assert any("liền nhau" in x for x in _loi(van[:a] + van[b:]))


def test_PHAT_12_trung_ma_thi_DO():
    van = _bien(_van(), "## Q4 — ", "## Q3 — ")
    assert any("trùng" in x for x in _loi(van))


def test_PHAT_13_tieu_de_gach_noi_thuong_van_la_muc():
    """Bài học M14 (BƯỚC 164): `## Q4 - …` không được lọt khỏi bộ đọc."""
    van = _bien(_van(), "## Q4 — ", "## Q4 - ")
    assert [m.ma for m in q.doc_muc(van)].count("Q4") == 1
    assert _loi(van) == []


def test_PHAT_14_du_kien_khong_co_lenh_thi_DO():
    van = _van()
    a = van.index("## Q4 — ")
    b = van.index("## Q5 — ")
    k = van.index("**Dữ kiện đã kiểm", a)
    van = van[:k] + van[k:b].replace("`", "") + van[b:]
    assert any("Q4" in x and "lệnh" in x for x in _loi(van))


def test_PHAT_15_du_kien_khong_co_ngay_thi_DO():
    van = _bien(MAU_CHO, "**Dữ kiện đã kiểm (09/10/2026):**", "**Dữ kiện đã kiểm:**")
    assert any("Q1" in x and "ngày" in x for x in _loi(van))


def test_PHAT_16_anh_huong_rong_thi_DO():
    van = _thay_dong(MAU_CHO, "**Ảnh hưởng:** chỉ là mẫu", "**Ảnh hưởng:** ngắn")
    assert any("Q1" in x and "Ảnh hưởng" in x for x in _loi(van))


def test_PHAT_17_het_hieu_luc_khong_co_bang_chung_thi_DO():
    van = _thay_dong(MAU_HET_HIEU_LUC, "**Bằng chứng (lệnh + ngày):**",
                     "**Bằng chứng (lệnh + ngày):** ngày 09/10/2026, đã xem bằng mắt")
    assert any("Q1" in x and "Bằng chứng" in x for x in _loi(van))


def test_PHAT_18_het_hieu_luc_khong_ngay_thi_DO():
    van = _thay_dong(MAU_HET_HIEU_LUC, "**Bằng chứng (lệnh + ngày):**",
                     "**Bằng chứng (lệnh + ngày):** `ls -d x` báo không có")
    assert any("Q1" in x and "ngày chạy lệnh" in x for x in _loi(van))


def test_PHAT_19_da_quyet_khong_ngay_thi_DO():
    van = _bien(_van(), "**Trả lời nguyên văn (08/10/2026):**", "**Trả lời nguyên văn:**")
    assert any("Q9" in x and "ngày" in x for x in _loi(van))


def test_PHAT_20_so_rong_thi_DO_khong_xanh_im():
    assert _loi("") != []
    assert _loi("# tiêu đề\n\nkhông có mục nào\n") != []


def test_PHAT_21_con_tro_HANDOFF_bi_go_thi_DO():
    van = q.HANDOFF.read_text(encoding="utf-8")
    assert q.loi_con_tro_handoff(van) == []
    bo = van.replace("docs/QUYET-DINH-CHO.md", "docs/KHAC.md")
    assert q.loi_con_tro_handoff(bo) != []


def test_PHAT_22_con_tro_HANDOFF_qua_xa_muc_Can_nguoi_quyet_thi_DO():
    dong = ["**Cần người quyết:**", "", "a", "b", "c", "docs/QUYET-DINH-CHO.md"]
    assert q.loi_con_tro_handoff("\n".join(dong)) != []
    dong2 = ["**Cần người quyết:**", "", "docs/QUYET-DINH-CHO.md"]
    assert q.loi_con_tro_handoff("\n".join(dong2)) == []


def test_PHAT_23_khong_co_hoac_hai_dong_Can_nguoi_quyet_thi_DO():
    assert q.loi_con_tro_handoff("khong co dong nao") != []
    hai = "**Cần người quyết:**\ndocs/QUYET-DINH-CHO.md\n**Cần người quyết:**\n"
    assert q.loi_con_tro_handoff(hai) != []


def test_PHAT_24_tieu_de_qua_ngan_hoac_qua_dai_thi_DO():
    ngan = _bien(_van(), "## Q3 — Địa chỉ (URL) app Streamlit Cloud là gì, để kiểm việc treo từ BƯỚC 127?", "## Q3 — Gì?")
    assert any("Q3" in x and "câu hỏi dài" in x for x in _loi(ngan))
    dai = _bien(_van(), "## Q3 — Địa chỉ (URL) app Streamlit Cloud là gì, để kiểm việc treo từ BƯỚC 127?",
                "## Q3 — " + "rất dài " * 40)
    assert any("Q3" in x and "câu hỏi dài" in x for x in _loi(dai))


def test_PHAT_25_da_quyet_nguon_chet_thi_DO():
    """Nguồn của mục `đã quyết` cũng phải còn thật (không chỉ mục `chờ`)."""
    van = _bien(_van(), "`docs/LO-TRINH.md:28 «Khoá Claude API»`", "`docs/LO-TRINH.md:28 «câu đã mất»`")
    assert any("Q9" in x and "KHÔNG còn nguyên văn" in x for x in _loi(van))


def test_PHAT_26_het_hieu_luc_nguon_chet_thi_DO():
    van = _bien(MAU_HET_HIEU_LUC, "«LỘ TRÌNH — hai đích, năm giai đoạn»", "«câu đã mất»")
    assert any("Q1" in x and "KHÔNG còn nguyên văn" in x for x in _loi(van))


def test_PHAT_27_de_xuat_qua_ngan_thi_DO():
    """Nhãn đủ chữ ĐỀ XUẤT nhưng nội dung rỗng ruột."""
    van = _thay_dong(MAU_CHO, "**Đề xuất của leader (ĐỀ XUẤT, mẫu dựng sẵn, chưa ai quyết):** chọn (a)",
                     "**Đề xuất của leader (ĐỀ XUẤT, mẫu dựng sẵn, chưa ai quyết):** (a).")
    assert any("Q1" in x and "ĐỀ XUẤT" in x for x in _loi(van))


def test_PHAT_28_tra_loi_mot_ky_tu_thi_DO():
    van = _bien(_van(), '*"Để tới giai đoạn B (Recommended)"*', '*"x"*')
    assert any("Q9" in x and "nguyên văn" in x for x in _loi(van))


def test_PHAT_29_nguon_chi_co_BUOC_van_hop_le_nhung_thieu_ca_hai_thi_DO():
    """Nguồn chỉ có chữ chung chung, không BƯỚC nào, không tệp:dòng."""
    van = _thay_dong(MAU_CHO, "**Nguồn:** `docs/LO-TRINH.md:1 ", "**Nguồn:** theo trí nhớ của leader")
    assert any("Q1" in x and "NGUỒN rỗng" in x for x in _loi(van))
    van2 = _thay_dong(MAU_CHO, "**Nguồn:** `docs/LO-TRINH.md:1 ", "**Nguồn:** xem BƯỚC 121 và BƯỚC 127")
    assert not any("Q1" in x and "NGUỒN" in x for x in _loi(van2))


def test_PHAT_30_ngay_sai_dang_thi_DO():
    """Ngày phải dạng dd/mm/yyyy: `2026-10-08` hay `8/10` không đủ để khai ngày trả lời."""
    van = _bien(_van(), "**Trả lời nguyên văn (08/10/2026):**", "**Trả lời nguyên văn (2026-10-08):**")
    assert any("Q9" in x and "ngày" in x for x in _loi(van))
    van = _bien(_van(), "**Trả lời nguyên văn (08/10/2026):**", "**Trả lời nguyên văn (8/10):**")
    assert any("Q9" in x and "ngày" in x for x in _loi(van))


def test_NGAY_khong_lay_mot_doan_giua_chuoi_so_dai_hon():
    """`108/10/20269` không phải một ngày; `08/10/2026` thì có."""
    assert q.RE_NGAY.search("108/10/20269") is None
    assert q.RE_NGAY.search("trả lời ngày 08/10/2026.") is not None


def test_NHAN_chi_khop_tron_tu_hoac_tien_to_cach_bang_dau_cach():
    """`Nguồn gốc` không được đọc là `Nguồn`; `Nguồn (ghi chú)` thì có."""
    m = q.Muc("Q1", "x" * 30)
    m.truong["Nguồn gốc"] = "sai"
    assert m.lay(q.NHAN_NGUON) == ""
    m.truong["Nguồn (ghi chú)"] = "đúng"
    assert m.lay(q.NHAN_NGUON) == "đúng"


def test_TRICH_DAN_nam_ngoai_khoi_rao_khong_bi_doc_la_muc():
    """Một ví dụ `## Q1 — …` dán trong khối ``` không phải mục thật."""
    van = _van() + "\n```\n## Q99 — ví dụ trong khối rào, không phải mục thật\n```\n"
    assert "Q99" not in [m.ma for m in q.doc_muc(van)]


# ── BƯỚC 166: quyết định 09/10/2026 ─────────────────────────────────────────

def _muc(ma: str):
    return next(m for m in q.doc_muc(_van()) if m.ma == ma)


def test_Q5_la_da_quyet_voi_CA_HAI_cau_tra_loi_nguyen_van():
    """Đính chính của leader (09/10): Q5 KHÔNG phải `hết hiệu lực`. Người dùng đã quyết xoá
    (02/10) và xác nhận lại (09/10); BƯỚC 165 từng ghi nhầm là "đã mất"."""
    m = _muc("Q5")
    assert m.trang_thai == q.DA_QUYET
    van = _van()
    assert '*"Xoá cả hai (Recommended)"*' in m.lay(q.NHAN_TRA_LOI)
    assert "02/10/2026" in m.truong_nhan(q.NHAN_TRA_LOI)
    assert '*"Đưa lại vào Thùng rác"*' in "\n".join(m.truong.values())
    # phát đầu: bỏ câu trả lời có hiệu lực thì ĐỎ
    bo = _bien(van, '**Trả lời nguyên văn (02/10/2026):** *"Xoá cả hai (Recommended)"*',
               "**Trả lời nguyên văn (02/10/2026):** (đã chốt)")
    assert any("Q5" in x and "nguyên văn" in x for x in _loi(bo))


def test_Q3_URL_app_KHONG_nam_trong_repo_cong_khai():
    """Người dùng đưa URL nhưng repo công khai và app dùng khoá API trả phí: URL không được vào repo."""
    import re
    import subprocess
    ds = subprocess.run(["git", "ls-files", "-z"], cwd=str(GOC), capture_output=True,
                        text=True, check=True).stdout.split("\0")
    mau = re.compile(r"[A-Za-z0-9-]+\.streamlit\.app")
    thay = []
    for rel in ds:
        p = GOC / rel
        if not rel or p.suffix not in (".md", ".py", ".yml", ".yaml", ".toml", ".json", ".txt", ".html"):
            continue
        if rel == "tests/test_quyet_dinh_cho.py" or not p.is_file():
            continue
        if mau.search(p.read_text(encoding="utf-8", errors="ignore")):
            thay.append(rel)
    assert thay == [], f"URL app Streamlit nằm trong repo công khai: {thay}"
    assert "cố ý không lưu trong repo công khai" in _muc("Q3").lay(q.NHAN_TRA_LOI)


def test_A4_da_bo_va_Q10_ghi_dung_cau_tra_loi():
    m = _muc("Q10")
    assert m.trang_thai == q.DA_QUYET
    assert '*"Không tách (Recommended)"*' in m.lay(q.NHAN_TRA_LOI)
    lo_trinh = (GOC / "docs" / "LO-TRINH.md").read_text(encoding="utf-8")
    dong = next(d for d in lo_trinh.splitlines() if d.startswith("- **A4**"))
    assert "ĐÃ BỎ 09/10/2026" in dong
    # gạch ngang phải bao đúng câu A4 (bỏ một đầu `~~` thì chỉ còn nửa câu bị gạch)
    assert "~~Tách `docs/STATE.md` theo tháng, giữ một mục lục.~~" in dong


# ── BƯỚC 172: người dùng đóng hàng đợi (09/10/2026) ────────────────────────

def test_BUOC_172_bon_muc_da_quyet_voi_cau_tra_loi_NGUYEN_VAN():
    """Q7 · Q11 · Q12 · Q13 `đã quyết`; câu trả lời chép nguyên văn, kể cả lỗi chính tả."""
    can = {
        "Q7": ['*"Gỡ khỏi repo (Recommended)"*', '*"làm đi"*', "KHÔNG phải ý kiến pháp lý",
               "không cấp quyền sử dụng dữ liệu của nguồn bên thứ ba",
               "xuất bản các nội dung của trang web dưới bất kỳ hình thức nào",
               "Lịch sử git cũ VẪN chứa các tệp"],
        "Q11": ['*"Tắt bằng mã ở cả hai (Recommended)"*', '*"tắt có ảnh hưởng gì không?"*',
                "đường `vnii` vẫn gửi tên hàm"],
        "Q12": ['*"trước đó bạn có đề xuất bỏ ngưỡng thanh trượt. Tôi đã xem xét và đống ý rằng '
                'thanh trượt trên app không có tác dụng gì nhiều. Hãy giao việc phán quyết cho Agent, '
                'không phải cứ điểm cao là mua (đôi khi đạt đủ điểm chưa chắc đã đúng điểm vào lệnh) '
                'bạn hãy tư duy sâu hơn để giải quyết bài toán đó nhé."*',
                '*"Duyệt cả lộ trình (Recommended)"*', "B6", "C7"],
        "Q13": ['*"đồng ý không tính"*'],
    }
    for ma, chuoi in can.items():
        m = _muc(ma)
        assert m.trang_thai == q.DA_QUYET, (ma, m.trang_thai)
        gop = "\n".join(m.truong.values())
        thieu = [c for c in chuoi if c not in gop]
        assert not thieu, f"{ma} mất câu nguyên văn/ý: {thieu}"
        assert "09/10/2026" in m.truong_nhan(q.NHAN_TRA_LOI), ma


def test_BUOC_172_bo_cau_tra_loi_thi_DO():
    """Phát đầu: bỏ câu trả lời nguyên văn của Q13 thì sổ phải đỏ đúng mục ấy."""
    van = _bien(_van(), '*"đồng ý không tính"*', "(đã chốt)")
    assert any("Q13" in x and "nguyên văn" in x for x in _loi(van))


def test_BUOC_172_so_that_khong_con_nguon_chet_o_Q12():
    """Q12 trích `app.py` cũ; app đã gỡ chúng nên Nguồn phải chỉ còn trích CÒN NGUYÊN VĂN."""
    assert _loi(_van()) == []
    assert "NGUONG_MUA_MAC_DINH = 50.0" not in (GOC / "app.py").read_text(encoding="utf-8")
