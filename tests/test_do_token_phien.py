"""Gác cho `tools/do_token_phien.py` và cho NGÂN SÁCH ngữ cảnh (BƯỚC 145).

Hai thứ, cùng một lý do: hạn mức 5 giờ bị đốt bởi **kích thước ngữ cảnh ×
số lượt gọi API** (đo 30/09/2026: ~465k token gửi lại ở mỗi lượt, 98,5–98,7%
là đọc lại cache, output chưa tới 1%), và hai file nạp tự động — `CLAUDE.md`,
`SKILL.md` — từng chiếm 108k + 45k ký tự.

MÁY ĐO cũng bị nghi ngờ như gác (`SKILL.md` Bước 3, điều 4). Lỗi có thật đã
cắn ngay lượt đo đầu: mỗi khối trả lời ghi NHIỀU dòng cùng `message.id` và cùng
`usage`; cộng theo dòng ra 1.244 lượt, số thật là 517. Nên phép đo đầu tiên ở
đây là đối chứng dương: ba dòng cùng id phải ra MỘT lượt.
"""
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import do_token_phien as D  # noqa: E402


def _dong(id_, ngay="2026-09-30", doc=0, ghi=0, vao=1, ra=0, lap=1):
    """`lap` dòng cùng id — đúng cách Claude Code ghi một câu trả lời nhiều khối."""
    o = {"type": "assistant", "timestamp": f"{ngay}T06:00:00.000Z",
         "message": {"id": id_, "usage": {
             "input_tokens": vao, "cache_read_input_tokens": doc,
             "cache_creation_input_tokens": ghi, "output_tokens": ra}}}
    return [json.dumps(o)] * lap


# ── 1. gộp theo id ──────────────────────────────────────────────────────

def test_ba_dong_cung_id_la_MOT_luot():
    r = D.tong_hop(_dong("m1", doc=1000, ra=10, lap=3))
    assert r["luot"] == 1
    assert r["doc_cache"] == 1000 and r["output"] == 10
    assert r["ngu_canh"] == 1001


def test_id_khac_nhau_thi_cong_don():
    r = D.tong_hop(_dong("m1", doc=1000, ra=10) + _dong("m2", doc=2000, ra=5, lap=2))
    assert r["luot"] == 2
    assert r["doc_cache"] == 3000 and r["output"] == 15
    assert r["ngu_canh"] == 3002
    assert r["trung_vi_ngu_canh"] == 1501


def test_trung_vi_khong_phai_trung_binh():
    """Ba lượt 1.001 · 1.001 · 10.001: trung vị 1.001, trung bình 4.001."""
    r = D.tong_hop(_dong("a", doc=1000) + _dong("b", doc=1000) + _dong("c", doc=10_000))
    assert r["trung_vi_ngu_canh"] == 1001


def test_cung_id_thi_dong_SAU_thang():
    """Khi stream, dòng sau mang `output_tokens` cuối cùng; giữ dòng đầu là đo hụt."""
    r = D.tong_hop(_dong("m1", doc=100, ra=5) + _dong("m1", doc=100, ra=50))
    assert r["luot"] == 1 and r["output"] == 50


def test_dong_khong_co_usage_va_dong_hong_khong_lam_hong_so():
    dong = _dong("m1", doc=10) + [json.dumps({"type": "user"}), "{khong phai json"]
    r = D.tong_hop(dong)
    assert r["luot"] == 1
    assert r["dong_bo_qua"] == 1        # dòng hỏng được ĐẾM, không im lặng


def test_rong_thi_khong_no():
    r = D.tong_hop([])
    assert r["luot"] == 0 and r["trung_vi_ngu_canh"] == 0


# ── 2. ghi lại cả cache ─────────────────────────────────────────────────

def test_NGUONG_ghi_lai_ghim_o_200k():
    assert D.NGUONG_GHI_LAI == 200_000


def test_ghi_lai_chi_dem_luot_VUOT_nguong():
    n = D.NGUONG_GHI_LAI
    dong = (_dong("a", ghi=n) + _dong("b", ghi=n + 1) + _dong("c", ghi=n + 500))
    r = D.tong_hop(dong)
    assert r["ghi_lai_ca_cache"] == 2                      # đúng bằng ngưỡng: KHÔNG
    assert r["token_ghi_lai"] == (n + 1) + (n + 500)
    assert r["ghi_cache"] == 3 * n + 501


def test_theo_ngay():
    r = D.tong_hop(_dong("a", ngay="2026-09-28", doc=5)
                   + _dong("b", ngay="2026-09-29", doc=7, lap=2))
    assert list(r["theo_ngay"]) == ["2026-09-28", "2026-09-29"]
    assert r["theo_ngay"]["2026-09-29"]["doc_cache"] == 7


# ── 3. ước lượng token ──────────────────────────────────────────────────

def test_uoc_token_khop_hai_lan_hieu_chuan():
    """116.978 ký tự → 39.004 token; 15.666 → 5.223 (`get_usage`, 30/09/2026)."""
    for ky_tu, that in ((116_978, 39_004), (15_666, 5_223)):
        assert abs(D.uoc_token(ky_tu) - that) / that < 0.01


def test_kich_co_tai_lieu_doc_dung_file_that():
    ds = dict(D.kich_co_tai_lieu())
    assert ds["CLAUDE.md"] == len((GOC / "CLAUDE.md").read_text(encoding="utf-8"))
    assert "docs/HANDOFF.md" in ds


# ── 4. NGÂN SÁCH ngữ cảnh ───────────────────────────────────────────────

#: Trần ký tự của hai file nạp tự động. Đặt ở mức người dùng duyệt 30/09/2026
#: (CLAUDE.md 20–25k, SKILL.md dưới 18k) cộng một khoảng thở nhỏ cho CLAUDE.md.
#: Chạm trần = chuyển phần lịch sử sang `docs/lich-su/`, KHÔNG nâng trần.
TRAN_CLAUDE_MD = 26_000
TRAN_SKILL_MD = 18_000


def test_TRAN_khong_bi_nang_am_tham():
    assert (TRAN_CLAUDE_MD, TRAN_SKILL_MD) == (26_000, 18_000)


def test_CLAUDE_md_va_SKILL_md_nam_trong_ngan_sach():
    for p, tran in ((GOC / "CLAUDE.md", TRAN_CLAUDE_MD),
                    (GOC / ".claude" / "skills" / "quy-trinh-lam-viec" / "SKILL.md",
                     TRAN_SKILL_MD)):
        n = len(p.read_text(encoding="utf-8"))
        assert n <= tran, (
            f"{p.name} dài {n:,} ký tự, trần {tran:,}. File này nạp vào MỌI lượt "
            f"gọi công cụ — chuyển phần lịch sử sang docs/lich-su/ (chép nguyên "
            f"văn), đừng nâng trần.")


def test_ban_luu_ton_tai_va_khong_rong():
    """Rút gọn không được làm mất thông tin: bản nguyên văn phải còn đó."""
    for ten, toi_thieu in (("CLAUDE-md-2026-09-30.md", 100_000),
                           ("SKILL-md-2026-09-30.md", 40_000)):
        p = GOC / "docs" / "lich-su" / ten
        assert p.exists(), f"mất bản lưu {ten}"
        assert len(p.read_text(encoding="utf-8")) >= toi_thieu


# ── 5. xếp hạng token-lượt (BƯỚC 150) ───────────────────────────────────

def _goi(id_):
    """Một lượt gọi API (dòng assistant có usage)."""
    return [json.dumps({"type": "assistant", "message": {
        "id": id_, "usage": {"input_tokens": 1, "output_tokens": 1}}})]


def _att(loai, n_ky_tu):
    return [json.dumps({"type": "attachment", "attachment": {
        "type": loai, "noi_dung": "x" * n_ky_tu}})]


def _chi_phi(r, nhan):
    return r["theo_nguon"].get(nhan, 0)


def test_chi_phi_la_ky_tu_chia_3_nhan_so_luot_CON_LAI():
    """Một mục vào trước 3 lượt: cùng một mục, gấp 3 lần cái vào trước 1 lượt."""
    dong = _att("a", 300) + _goi("m1") + _goi("m2") + _goi("m3")
    r = D.xep_hang(dong)
    dai = len(json.dumps({"type": "a", "noi_dung": "x" * 300}, ensure_ascii=False))
    assert r["luot"] == 3
    assert _chi_phi(r, "att:a") == dai / D.KY_TU_MOI_TOKEN * 3


def test_vao_SOM_dat_hon_vao_MUON_cung_kich_co():
    dong = (_att("aaa", 600) + _goi("m1") + _att("bbb", 600) + _goi("m2") + _goi("m3"))
    r = D.xep_hang(dong)
    assert _chi_phi(r, "att:aaa") == 3 * _chi_phi(r, "att:bbb") / 2


def test_muc_vao_SAU_luot_cuoi_khong_ton_gi():
    r = D.xep_hang(_goi("m1") + _att("tre", 900))
    assert _chi_phi(r, "att:tre") == 0


def test_compact_RESET_noi_dung_truoc_do_khong_con_bi_tinh():
    """Mục trước ranh giới compact chỉ trả cho các lượt TRƯỚC ranh giới."""
    ranh = [json.dumps({"type": "system", "subtype": "compact_boundary"})]
    dong = _att("cu", 600) + _goi("m1") + ranh + _goi("m2") + _goi("m3")
    r = D.xep_hang(dong)
    dai = len(json.dumps({"type": "cu", "noi_dung": "x" * 600}, ensure_ascii=False))
    assert _chi_phi(r, "att:cu") == dai / D.KY_TU_MOI_TOKEN * 1    # chỉ m1
    assert r["luot"] == 3


def test_nhieu_dong_cung_message_id_la_MOT_luot():
    dong = _att("a", 300) + _goi("m1") + _goi("m1") + _goi("m1")
    assert D.xep_hang(dong)["luot"] == 1


def test_prompt_snapshot_bi_loai():
    assert "att:prompt_snapshot" in D.LOAI_TRU
    r = D.xep_hang(_att("prompt_snapshot", 90_000) + _goi("m1"))
    assert "att:prompt_snapshot" not in r["theo_nguon"] and r["tong"] == 0


def test_ket_qua_cong_cu_mang_TEN_cong_cu_cua_no():
    dong = [
        json.dumps({"type": "assistant", "message": {"id": "m0", "usage": {"input_tokens": 1}, "content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}},
            {"type": "tool_use", "id": "t2", "name": "mcp__Claude_Browser__computer", "input": {}}]}}),
        json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "a" * 300},
            {"type": "tool_result", "tool_use_id": "t2", "content": [
                {"type": "text", "text": "b" * 30}, {"type": "image", "source": {}}]}]}}),
    ] + _goi("m1")
    r = D.xep_hang(dong)
    assert _chi_phi(r, "result:Bash") == 300 / D.KY_TU_MOI_TOKEN
    assert _chi_phi(r, "result:computer") == (30 + D.KY_TU_MOI_ANH) / D.KY_TU_MOI_TOKEN


def test_dau_vao_tool_use_tren_CUNG_dong_voi_luot_goi_khong_tinh_chinh_no():
    """Dòng assistant vừa là lượt gọi vừa mang tool_use: ngữ cảnh của lượt ấy
    chưa chứa đầu vào của nó, nên chỉ trả cho các lượt SAU."""
    dong = [json.dumps({"type": "assistant", "message": {
        "id": "m1", "usage": {"input_tokens": 1}, "content": [
            {"type": "tool_use", "id": "t1", "name": "Bash",
             "input": {"command": "x" * 300}}]}})] + _goi("m2") + _goi("m3")
    r = D.xep_hang(dong)
    dai = len(json.dumps({"command": "x" * 300}, ensure_ascii=False))
    assert _chi_phi(r, "tool_use_input") == dai / D.KY_TU_MOI_TOKEN * 2
