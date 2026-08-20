"""Cửa chặn: chưa đọc tài liệu bắt buộc thì không được sửa file ảnh hưởng kết quả.

Chạy như `PreToolUse` hook của Claude Code. Đọc JSON từ stdin.

VÌ SAO CÓ FILE NÀY
──────────────────
`CLAUDE.md` ghi rõ: "Đọc `NGUYEN-TAC-DO-LUONG.md` và `MO-XE-KIEN-TRUC.md`
TRƯỚC KHI sửa bất cứ thứ gì liên quan tới kết quả."

Ngày 20/08/2026 agent đã sửa `paper_metrics.py`, `paper_runner.py`,
`market_filter.py`, `paper_trading.py` và hàng chục file khác **trước khi
đọc hai tài liệu đó** — và chỉ đọc khi người dùng hỏi. Hậu quả cụ thể:

  • lặp lại một phân tích đã có sẵn trong tài liệu (đòn bẩy 2,2× của
    +636,11%, kèm cả tên file `paper_custom20loop_18m_loop_11.db`);
  • trình bày +14,24% như "con số thật", trong khi chính tài liệu đã liệt
    con số đó vào danh sách bốn con số vô nghĩa;
  • khẳng định "bằng chứng ngoài mẫu hiện có là 0 lệnh", trong khi tài liệu
    ghi sẵn một phép đo 108 lệnh ngoài mẫu ngày 07/08.

Nguyên nhân giống hệt mọi thứ khác trong dự án này: **một luật không phải
là cửa thì chỉ là gợi ý.** Bản trước của `.claude/settings.json` chỉ có
`PostToolUse` — chạy SAU khi ghi. Chuông báo cháy, không phải cửa chống cháy.

NGUYÊN TẮC THIẾT KẾ
───────────────────
1. **Hẹp có chủ đích.** Chỉ chặn file thật sự ảnh hưởng kết quả. Một cửa
   chặn quá rộng sẽ bị tắt, mà cửa bị tắt thì bằng không có.
2. **Hỏng thì KHÔNG chặn.** Hook lỗi mà làm kẹt mọi thao tác là tệ hơn
   không có hook. Ngược hướng với `chan_bia_so_lieu.py` — file đó chặn
   theo hướng nghi-ngờ-thì-dừng vì nó bảo vệ *số liệu*; file này bảo vệ
   *quy trình*, nên nó nhường đường khi chính nó không chắc.
3. **Không rò giữa phiên.** Đọc ở phiên trước không tính cho phiên này.

BA GIỚI HẠN, PHẢI BIẾT
──────────────────────
1. **Chỉ có hiệu lực từ PHIÊN SAU.** Claude Code nạp cấu hình hook lúc khởi
   tạo phiên. Thêm hook giữa phiên thì phiên đó vẫn chạy như cũ — đã kiểm
   ngày 20/08: đăng ký xong, thử `Edit` một file được bảo vệ, và nó KHÔNG
   bị chặn.
2. **Không thấy được thao tác qua Bash.** Matcher chỉ bắt `Read|Write|Edit`
   của Claude Code. Một agent ghi file bằng `python - <<PY ... write_text()`
   qua Bash sẽ đi vòng qua cửa này hoàn toàn. Cùng loại giới hạn mà
   `chan_bia_so_lieu.py` đã ghi cho chính nó — và ở đó nó được bù bằng
   `--quet-repo` chạy trong CI. Ở đây CHƯA có gì bù: không có cách nào để
   CI biết agent đã đọc tài liệu hay chưa.
3. **Đo "đã đọc", không đo "đã hiểu".** Một agent gọi `Read` rồi bỏ qua nội
   dung vẫn qua được cửa. Cửa này chỉ loại bỏ trường hợp *chưa hề đọc* —
   đó đúng là trường hợp đã xảy ra ngày 20/08, nhưng nó không phải mọi
   trường hợp.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Phải đọc HẾT những file này trong phiên hiện tại.
TAI_LIEU_BAT_BUOC = ("NGUYEN-TAC-DO-LUONG.md", "MO-XE-KIEN-TRUC.md")

#: File mà một thay đổi có thể làm sai CON SỐ, không chỉ làm sai giao diện.
FILE_ANH_HUONG_KET_QUA = {
    "paper_metrics.py", "paper_trading.py", "paper_runner.py",
    "master_agent.py", "analysis_agents.py", "debate_agents.py",
    "post_mortem_learning.py", "market_filter.py", "data_quality.py",
    "data_collectors.py", "run_daily.py", "sheets_store.py",
    "google_sheets_sync.py",
}

#: Cả thư mục backtest/ và mọi script tối ưu.
def _anh_huong_ket_qua(p: Path) -> bool:
    if p.name in FILE_ANH_HUONG_KET_QUA:
        return True
    if p.suffix != ".py":
        return False
    if p.name.startswith(("optimize_", "walkforward", "run_oos")):
        return True
    try:
        return "backtest" in p.relative_to(GOC).parts
    except ValueError:
        return False


def _duong_dan_dau_vet(phien: str) -> Path:
    an_toan = "".join(c if c.isalnum() or c in "-_" else "_" for c in phien)[:64]
    return Path(tempfile.gettempdir()) / f"vibe_da_doc_{an_toan}.json"


def _da_doc(phien: str) -> set:
    f = _duong_dan_dau_vet(phien)
    if not f.exists():
        return set()
    try:
        return set(json.loads(f.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _ghi_da_doc(phien: str, ten: str) -> None:
    da = _da_doc(phien) | {ten}
    try:
        _duong_dan_dau_vet(phien).write_text(
            json.dumps(sorted(da)), encoding="utf-8")
    except Exception:
        pass


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0                      # hỏng thì nhường đường

    phien = str(d.get("session_id") or "khong-ro")
    tool = str(d.get("tool_name") or "")
    tho = (d.get("tool_input") or {}).get("file_path")
    if not tho:
        return 0

    p = Path(str(tho))
    if tool == "Read":
        if p.name in TAI_LIEU_BAT_BUOC:
            _ghi_da_doc(phien, p.name)
        return 0

    if tool not in ("Write", "Edit", "NotebookEdit"):
        return 0
    if not _anh_huong_ket_qua(p):
        return 0

    thieu = [t for t in TAI_LIEU_BAT_BUOC if t not in _da_doc(phien)]
    if not thieu:
        return 0

    print(
        f"CHẶN: chưa đọc tài liệu bắt buộc trong phiên này.\n"
        f"\n"
        f"  Định sửa : {p.name}  (ảnh hưởng tới CON SỐ, không chỉ giao diện)\n"
        f"  Còn thiếu: {', '.join(thieu)}\n"
        f"\n"
        f"CLAUDE.md: \"Đọc hai file này TRƯỚC KHI sửa bất cứ thứ gì liên quan\n"
        f"tới kết quả.\" Ngày 20/08/2026 luật đó bị bỏ qua và hậu quả là lặp\n"
        f"lại phân tích đã có sẵn, cộng với việc trình bày một con số mà chính\n"
        f"tài liệu đã tuyên bố vô nghĩa như thể nó là số thật.\n"
        f"\n"
        f"Đọc xong hai file rồi thao tác lại.",
        file=sys.stderr)
    return 2                          # exit 2 = chặn, stderr trả về cho agent


if __name__ == "__main__":
    sys.exit(main())
