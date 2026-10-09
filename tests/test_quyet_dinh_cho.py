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
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import quyet_dinh_cho as q  # noqa: E402

BA_NGUON_THAT = GOC / "docs" / "QUYET-DINH-CHO.md"


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
    assert dem[q.CHO] >= 1 and dem[q.DA_QUYET] >= 1 and dem[q.HET_HIEU_LUC] >= 1, (
        f"thiếu một trạng thái trong sổ thật: {dem} — gác sẽ không bao giờ chạy "
        "nhánh đó trên dữ liệu thật")


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
    van = _bien(_van(), "`docs/HANDOFF.md:387 «xoá hẳn»`", "`docs/HANDOFF_XOA.md:387 «xoá hẳn»`")
    assert any("không tồn tại" in x for x in _loi(van))


def test_PHAT_3_trich_khong_con_nguyen_van_thi_DO():
    van = _bien(_van(), "«Bộ nhớ hậu nghiệm trên đường quét thật»", "«câu đã bị sửa mất»")
    assert any("KHÔNG còn nguyên văn" in x for x in _loi(van))


def test_PHAT_4_dong_vuot_do_dai_tep_thi_DO():
    van = _bien(_van(), "`docs/HANDOFF.md:563 ", "`docs/HANDOFF.md:9999999 ")
    assert any("vượt độ dài" in x for x in _loi(van))


def test_PHAT_5_nguon_thieu_trich_thi_DO():
    van = _bien(_van(), "`CLAUDE.md:164 «quyết định của người dùng, chưa có»`", "`CLAUDE.md:164`")
    assert any("thiếu trích" in x for x in _loi(van))


def test_PHAT_6_nguon_rong_thi_DO():
    """Mục Q3 mất hết nguồn."""
    van = _thay_dong(_van(), "**Nguồn:** `docs/HANDOFF.md:384 ", "**Nguồn:** chưa rõ")
    assert any("Q3" in x and "NGUỒN rỗng" in x for x in _loi(van))


def test_PHAT_7_chi_con_mot_lua_chon_thi_DO():
    van = _bien(_van(), "- (b) Người dùng tự mở app", "(b) Người dùng tự mở app")
    van = _bien(van, "- (c) Bỏ việc kiểm.", "(c) Bỏ việc kiểm.")
    assert any("Q3" in x and "lựa chọn" in x for x in _loi(van))


def test_PHAT_8_lua_chon_nhay_chu_thi_DO():
    van = _bien(_van(), "- (b) Người dùng tự mở app", "- (c) Người dùng tự mở app")
    van = _bien(van, "- (c) Bỏ việc kiểm.", "- (e) Bỏ việc kiểm.")
    assert any("liền nhau" in x for x in _loi(van))


def test_PHAT_9_bo_chu_DE_XUAT_thi_DO():
    van = _bien(_van(),
                "**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), vì kiểm",
                "**Đề xuất của leader:** (a), vì kiểm")
    assert any("Q3" in x and "ĐỀ XUẤT" in x for x in _loi(van))


def test_PHAT_10_trang_thai_la_thi_DO():
    van = _bien(_van(), "## Q3 — Địa chỉ (URL) app Streamlit Cloud là gì, để kiểm việc treo từ BƯỚC 127?\n\n**Trạng thái:** chờ",
                "## Q3 — Địa chỉ (URL) app Streamlit Cloud là gì, để kiểm việc treo từ BƯỚC 127?\n\n**Trạng thái:** tạm gác")
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
    van = _bien(_van(), "**Dữ kiện đã kiểm (08/10/2026):**\n- `grep -rIl", "**Dữ kiện đã kiểm:**\n- `grep -rIl")
    assert any("Q3" in x and "ngày" in x for x in _loi(van))


def test_PHAT_16_anh_huong_rong_thi_DO():
    van = _thay_dong(_van(), "**Ảnh hưởng:** chỉ kiểm vận hành", "**Ảnh hưởng:** ngắn")
    assert any("Q3" in x and "Ảnh hưởng" in x for x in _loi(van))


def test_PHAT_17_het_hieu_luc_khong_co_bang_chung_thi_DO():
    van = _thay_dong(_van(), "**Bằng chứng (lệnh + ngày):**",
                     "**Bằng chứng (lệnh + ngày):** ngày 08/10/2026, đã xem bằng mắt")
    assert any("Q5" in x and "Bằng chứng" in x for x in _loi(van))


def test_PHAT_18_het_hieu_luc_khong_ngay_thi_DO():
    van = _thay_dong(_van(), "**Bằng chứng (lệnh + ngày):**",
                     "**Bằng chứng (lệnh + ngày):** `ls -d x` báo không có")
    assert any("Q5" in x and "ngày chạy lệnh" in x for x in _loi(van))


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
    van = _bien(_van(), "`docs/LO-TRINH.md:169 «giữ hay xoá»`", "`docs/LO-TRINH.md:169 «câu đã mất»`")
    assert any("Q5" in x and "KHÔNG còn nguyên văn" in x for x in _loi(van))


def test_PHAT_27_de_xuat_qua_ngan_thi_DO():
    """Nhãn đủ chữ ĐỀ XUẤT nhưng nội dung rỗng ruột."""
    van = _thay_dong(_van(), "**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), vì kiểm",
                     "**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a).")
    assert any("Q3" in x and "ĐỀ XUẤT" in x for x in _loi(van))


def test_PHAT_28_tra_loi_mot_ky_tu_thi_DO():
    van = _bien(_van(), '*"Để tới giai đoạn B (Recommended)"*', '*"x"*')
    assert any("Q9" in x and "nguyên văn" in x for x in _loi(van))


def test_PHAT_29_nguon_chi_co_BUOC_van_hop_le_nhung_thieu_ca_hai_thi_DO():
    """Nguồn chỉ có chữ chung chung, không BƯỚC nào, không tệp:dòng."""
    van = _thay_dong(_van(), "**Nguồn:** `docs/HANDOFF.md:384 ", "**Nguồn:** theo trí nhớ của leader")
    assert any("Q3" in x and "NGUỒN rỗng" in x for x in _loi(van))
    van2 = _thay_dong(_van(), "**Nguồn:** `docs/HANDOFF.md:384 ", "**Nguồn:** xem BƯỚC 127 và BƯỚC 141")
    assert not any("Q3" in x and "NGUỒN" in x for x in _loi(van2))


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
