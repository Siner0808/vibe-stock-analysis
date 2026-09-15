"""Cửa `PreToolUse` · Read|Edit — bơm HỒ SƠ của file sắp mở vào ngữ cảnh.

NÓ KHÔNG BAO GIỜ CHẶN
─────────────────────
Trả `permissionDecision: "allow"` và mã thoát 0 trong mọi nhánh, kể cả
khi hỏng. Cửa chặn của dự án là `tools/cua_doc_bat_buoc.py`; đặc tả ghi
*"When several hooks return additionalContext for the same event, Claude
receives all of the values"* và các hook cùng sự kiện chạy song song, nên
hai cửa này không giành nhau.

VÌ SAO Ở `PreToolUse` CHỨ KHÔNG Ở `UserPromptSubmit`
────────────────────────────────────────────────────
Đặc tả hook của Claude Code: *"Where the reminder appears depends on the
event: … **PreToolUse, PostToolUse, PostToolUseFailure, and PostToolBatch:
next to the tool result**."* Tức hồ sơ hiện **ngay cạnh nội dung file** —
đúng chỗ cần, vì câu hỏi *"file này đã có ai nói gì chưa"* chỉ đáng trả
lời vào đúng lúc đang nhìn nó.

Ngày 15/09/2026 tôi đã kết luận NGƯỢC LẠI điều này — rằng `PreToolUse`
không bơm được — từ một bản tóm tắt đặc tả do mô hình nhỏ đọc hộ. Bản
tóm tắt ấy bịa. Đọc nguyên văn trang đặc tả thì nó nằm ngay trong danh
sách. Lỗi 66, và nó xảy ra trong lúc đang thiết kế đúng công cụ để chặn
việc tin bản nén.

BA ĐIỀU KIỆN IM LẶNG, cả ba để cửa không thành tiếng ồn
───────────────────────────────────────────────────────
  1. đang ở trong subagent  -> im
  2. file chưa đủ hồ sơ     -> im  (ngưỡng ở `ho_so.TOI_THIEU_THAM_CHIEU`)
  3. đã bơm file này trong phiên này -> im
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

TEN_NHAT_KY = "vibe_cua_ho_so_chay.log"


def duong_dan_nhat_ky() -> Path:
    return Path(tempfile.gettempdir()) / TEN_NHAT_KY


def ghi_nhat_ky(nhan: str, chi_tiet: str = "") -> None:
    """Một dòng mỗi lần được gọi, KỂ CẢ khi nhường đường.

    Cùng lý do với `tools/cua_doc_bat_buoc.py`: không có nhật ký thì câu
    hỏi *"cửa có chạy không"* trở thành một buổi sáng suy diễn. Phân biệt
    được "cửa không chạy" với "cửa chạy mà im".
    """
    try:
        from datetime import datetime
        with duong_dan_nhat_ky().open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {nhan}  "
                    f"{chi_tiet}\n")
    except Exception:
        pass


def _dau_vet(phien: str) -> Path:
    an_toan = "".join(c if c.isalnum() or c in "-_" else "_"
                      for c in phien)[:80]
    return Path(tempfile.gettempdir()) / f"vibe_ho_so_da_bom_{an_toan}.json"


def da_bom(phien: str) -> set[str]:
    f = _dau_vet(phien)
    if not f.exists():
        return set()
    try:
        return set(json.loads(f.read_text(encoding="utf-8")))
    except Exception:
        return set()


def ghi_da_bom(phien: str, ten: str) -> None:
    try:
        _dau_vet(phien).write_text(
            json.dumps(sorted(da_bom(phien) | {ten})), encoding="utf-8")
    except Exception:
        pass


def quyet_dinh(d: dict) -> tuple[str | None, str, str]:
    """(văn bản bơm | None, nhãn nhật ký, chi tiết). Hàm THUẦN.

    Tách khỏi `main()` để đục thử đi qua đúng hàm đang phán — `SKILL.md`
    Bước 3 điều 1.
    """
    if d.get("agent_id"):
        return None, "IM-subagent", str(d.get("agent_type") or "")

    duong = (d.get("tool_input") or {}).get("file_path")
    if not duong:
        return None, "IM-khong-co-file_path", ""

    ten = Path(str(duong)).name
    phien = str(d.get("session_id") or "khong-ro")
    if ten in da_bom(phien):
        return None, "IM-da-bom-trong-phien", ten

    import ho_so
    dong = ho_so.dong_ho_so(ho_so.doc_ho_so(ten))
    if not dong:
        return None, "IM-chua-du-ho-so", ten

    return "\n".join(dong), "BOM", f"{ten} ({len(dong)} dong)"


def main() -> int:
    # KHÔNG bỏ dòng này. Cửa chạy từ cwd BẤT KỲ, và console Windows ở
    # `cp1258` làm `print` một chuỗi tiếng Việt nổ `UnicodeEncodeError`.
    # Đo 15/09/2026 bằng cách bơm payload giả từ ngoài repo: cửa nổ ngay
    # phát đầu. Đây là lần thứ TƯ của dự án — `kiem_ban_sach` 22/08,
    # `experiment_fundamentals` 23/08, `extend_history` 24/08 — và lý do
    # `tests/test_script_chay_duoc_tren_windows.py` tồn tại.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        d = json.load(sys.stdin)
    except Exception:
        ghi_nhat_ky("HONG-khong-doc-duoc-stdin")
        return 0                       # hỏng thì nhường đường, luôn luôn

    try:
        van, nhan, chi_tiet = quyet_dinh(d)
    except Exception as e:             # bia-ok: cua nay KHONG duoc lam
        ghi_nhat_ky("HONG", repr(e)[:200])   # hong mot luot Read cua nguoi
        return 0                             # dung. Im la hanh vi dung.

    ghi_nhat_ky(nhan, chi_tiet)
    if van is None:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": van,
        }
    }, ensure_ascii=False))

    # Đánh dấu SAU KHI in xong, không phải trước. Một lượt in hỏng mà đã
    # ghi dấu thì suất bơm của file ấy bị đốt im lặng cho cả phiên — và
    # phép thử ngày 15/09/2026 rơi đúng vào đó: `print` nổ
    # `UnicodeEncodeError`, dấu vết đã ghi, lượt sau im.
    ghi_da_bom(str(d.get("session_id") or "khong-ro"),
               Path(str((d.get("tool_input") or {}).get("file_path"))).name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
