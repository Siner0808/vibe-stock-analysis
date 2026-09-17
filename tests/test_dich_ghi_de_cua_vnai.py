"""Bốn đích mà `vnai` ghi đè — tài liệu phải khai ĐỦ, và khai đúng cái nào.

VÌ SAO CÓ FILE NÀY
──────────────────
`CLAUDE.md` và `NGUYEN-TAC-DO-LUONG.md` cùng ghi *"`AGENTS.md` do vnstock
tự đồng bộ nên sẽ bị ghi đè"*. Đo 17/09/2026 thì câu ấy nêu **một trên
bốn** đích — và là đích **DUY NHẤT không bị ghi**:

    import vnstock        ->  khong file nao doi
    import vnstock_data   ->  ~/.claude/CLAUDE.md   ] ba file
                              ~/.gemini/GEMINI.md   ] TOAN CUC
                              ~/.codex/AGENTS.md    ]
                              <repo>/AGENTS.md  KHONG doi (mtime 03/08/2026)

Đây là lớp lỗi tài liệu thứ nhất ở `docs/HANDOFF.md` mục 4 ở dạng nguy
hiểm nhất: **một cảnh báo ĐÚNG về nguy cơ nhưng CHỈ SAI địa chỉ**. Người
đọc tin là mình đã được cảnh báo, rồi viết luật vào đúng file đang bị ghi.

BA PHÉP KIỂM, VÀ MỘT TRONG BA LÀ PHÉP KIỂM HÀNH VI
───────────────────────────────────────────────────
1. Tài liệu phải nêu **đủ** bốn đích, và danh sách ấy **suy ra từ `vnai`**
   chứ không gõ lại.
2. `AGENTS.md` của repo phải **giữ dấu mốc đời cũ**. Nó an toàn KHÔNG phải
   vì ai bảo vệ nó, mà vì nó CŨ: `setup_agent_environment` gặp
   `# Vnstock Vibe Onboarding` mà không có khối kết thúc thì bỏ qua. Ai
   "cập nhật" file ấy là gỡ mất chính cái khiên ấy.
3. Ba cái tên đường dẫn toàn cục phải có mặt trong `CLAUDE.md`.

BA TRẠNG THÁI, KHÔNG PHẢI HAI
─────────────────────────────
`vnai` có trong `requirements.txt` nên CI có nó. Nhưng nếu một ngày API
của nó đổi, phép kiểm này **không được im lặng**: nó lùi về danh sách ĐÃ
ĐO ngày 17/09/2026 và vẫn kiểm tài liệu. Một gác không đọc được nguồn thì
phải nói ra, chứ không phải bỏ qua.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

CLAUDE = GOC / "CLAUDE.md"
NGUYEN_TAC = GOC / "NGUYEN-TAC-DO-LUONG.md"
AGENTS = GOC / "AGENTS.md"

#: Đo 17/09/2026 bằng `vnai.beam.agents.AGENT_TARGET_ORDER` (vnai 2.6.0).
#: Chỉ dùng khi KHÔNG đọc được từ `vnai` — xem docstring, ba trạng thái.
DICH_DA_DO = ["project", "antigravity", "claude", "codex"]

#: Dấu mốc đời cũ đang che `AGENTS.md` của repo. `_BOOTSTRAP_START_MARKERS`
#: của vnai có nó, nhưng `_BOOTSTRAP_BLOCK_PATTERN` đòi thêm câu kết
#: `(End of Bootstrap...)` — thiếu câu ấy thì vnai xếp file vào "phiên bản
#: cũ" và BỎ QUA.
MOC_DOI_CU = "# Vnstock Vibe Onboarding"
CAU_KET_KHOI = "End of Bootstrap"


def _lui_ve_ban_da_do() -> tuple[list[str], str]:
    """Đường lùi khi không đọc được `vnai`.

    TÁCH RA THÀNH HÀM RIÊNG, cùng lý do với `kiem_hoan_tra`: nằm trong
    `except` thì đột biến *"trả rỗng thay vì lùi"* **không đục tới được**
    trên máy có `vnai`, và nó sống sót mà không ai biết. Đo 17/09/2026:
    đúng phát ấy sống sót ở lượt đầu.
    """
    return list(DICH_DA_DO), "ĐÃ ĐO 17/09/2026"


def _dich_tu_vnai() -> tuple[list[str], str]:
    """(danh sách đích, nguồn). Nguồn là 'vnai' hoặc 'ĐÃ ĐO 17/09'."""
    try:
        from vnai.beam import agents
        return list(agents.AGENT_TARGET_ORDER), "vnai"
    except Exception:
        return _lui_ve_ban_da_do()


def test_TAI_LIEU_phai_neu_DU_BON_DICH_chu_khong_phai_mot():
    dich, nguon = _dich_tu_vnai()
    assert len(dich) >= 4, f"doc duoc {len(dich)} dich tu {nguon} — qua it"

    van = CLAUDE.read_text(encoding="utf-8")
    thieu = [d for d in dich if f"`{d}`" not in van]
    assert not thieu, (
        f"CLAUDE.md khong neu ten {thieu} — vnai ghi vao {len(dich)} dich, "
        f"tai lieu chi ke mot phan (nguon: {nguon})")
    print(f"PASS  {len(dich)} dich tu {nguon}, CLAUDE.md neu du")


def test_TEN_DICH_va_DUONG_DAN_phai_nam_CUNG_MOT_DONG():
    """Tên đích thì trừu tượng; ĐƯỜNG DẪN mới là thứ người đọc tìm được.

    Và phải **cùng một dòng**. Bản trước của phép kiểm này chỉ hỏi *"chuỗi
    ấy có xuất hiện đâu đó trong file không"* — mà `~/.claude/CLAUDE.md`
    xuất hiện cả chục lần ở mục hook, nên một đột biến xoá đúng ô trong
    bảng vẫn **sống sót**. Một phép so trên cả file thì không nói được gì
    về chỗ đang cần nói.
    """
    dong = CLAUDE.read_text(encoding="utf-8").replace("\\", "/").splitlines()
    for ten, duong in (("antigravity", "~/.gemini/GEMINI.md"),
                       ("claude", "~/.claude/CLAUDE.md"),
                       ("codex", "~/.codex/AGENTS.md"),
                       ("project", "<repo>/AGENTS.md")):
        khop = [d for d in dong if f"`{ten}`" in d and f"`{duong}`" in d]
        assert khop, (
            f"CLAUDE.md khong co dong nao mang CA `{ten}` LAN `{duong}` — "
            f"mot cai ten dich khong giup ai tim ra file that")
    print("PASS  bon dich, moi dich mot dong mang ca ten lan duong dan")


def test_CAU_CU_neu_MOT_DICH_khong_duoc_de_TRAN():
    """Câu cũ được ở lại, nhưng phải mang dấu — quy ước giữ-số-cũ.

    `docs/HANDOFF.md` mục 4: một GIÁ TRỊ cũ để trần thì phải đánh dấu.
    Ở đây thứ cũ không phải một con số mà là một PHẠM VI, và cùng luật.
    """
    for p in (CLAUDE, NGUYEN_TAC):
        van = p.read_text(encoding="utf-8")
        i = van.find("do vnstock tự đồng bộ")
        if i == -1:
            continue
        quanh = van[max(0, i - 400):i + 900]
        assert ("⚠️" in quanh or "🔴" in quanh), (
            f"{p.name}: cau 'do vnstock tu dong bo' con de TRAN — no neu "
            f"MOT tren bon dich, va la dich duy nhat KHONG bi ghi")


def test_AGENTS_md_cua_repo_phai_GIU_DAU_MOC_DOI_CU():
    """Nó an toàn vì nó CŨ. Cập nhật nó là gỡ mất cái khiên.

    Đo 17/09/2026, ba ca chạy thật trong thư mục tạm:

        file chi co noi dung nguoi dung   -> vnai NOI them khoi cua no
        file co khoi hien hanh            -> don khoi, noi lai o CUOI
        file mang dau moc DOI CU          -> BO QUA hoan toan (87 -> 87)

    `AGENTS.md` của repo rơi vào ca thứ ba, và mtime của nó đứng yên từ
    commit đầu tiên 03/08/2026 — 45 ngày.
    """
    van = AGENTS.read_text(encoding="utf-8")
    assert MOC_DOI_CU in van, (
        f"AGENTS.md mat dau moc `{MOC_DOI_CU}` — day la thu duy nhat lam "
        f"vnai BO QUA file nay. Mat no thi file vao dien bi ghi lai.")
    assert CAU_KET_KHOI not in van, (
        f"AGENTS.md nay CO cau ket `{CAU_KET_KHOI}` — tuc no thanh mot "
        f"KHOI hop le, va vnai se don roi noi lai moi lan `import "
        f"vnstock_data`.")
    print("PASS  AGENTS.md van mang dau moc doi cu, vnai van bo qua no")


def test_DUONG_LUI_phai_TRA_DU_BON_DICH_chu_khong_RONG():
    """Vế còn lại: một đường lùi trả rỗng biến gác thành gác câm.

    `test_TAI_LIEU_phai_neu_DU_BON_DICH` đòi `len(dich) >= 4`, nên một
    đường lùi rỗng sẽ làm nó đỏ — NHƯNG chỉ trên máy KHÔNG có `vnai`. Trên
    máy có `vnai` thì nhánh ấy không bao giờ chạy. Gọi thẳng nó là cách
    duy nhất để đục thử tới được.
    """
    dich, nguon = _lui_ve_ban_da_do()
    assert len(dich) >= 4, f"duong lui chi tra {len(dich)} dich: {dich}"
    assert nguon != "vnai", "duong lui phai NOI RA rang no khong doc vnai"


def test_DANH_SACH_DA_DO_khop_vnai_khi_doc_duoc():
    """Bản dự phòng không được trôi khỏi bản thật.

    Nếu `vnai` đọc được mà danh sách đã đo lệch khỏi nó, thì đúng hình
    dạng `N_DAY_DU` 596/451: một bản sao gõ tay sống lâu hơn bản gốc.
    """
    dich, nguon = _dich_tu_vnai()
    if nguon != "vnai":
        print(f"CHUA KIEM DUOC: khong doc duoc vnai, dung ban {nguon}")
        return
    assert dich == DICH_DA_DO, (
        f"vnai nay bao {dich}, ban da do ghi {DICH_DA_DO} — cap nhat "
        f"DICH_DA_DO va doc lai CLAUDE.md")
