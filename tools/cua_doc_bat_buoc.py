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
import sys
import tempfile
from datetime import datetime
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


#: Nhật ký "cửa này đã chạy". Nằm ở TEMP, một dòng mỗi lần được gọi.
TEN_NHAT_KY = "vibe_cua_doc_chay.log"


def duong_dan_nhat_ky() -> Path:
    return Path(tempfile.gettempdir()) / TEN_NHAT_KY


def ghi_nhat_ky(nhan: str, chi_tiet: str = "") -> None:
    """Ghi MỘT dòng vào nhật ký chạy. Không bao giờ ném.

    VÌ SAO CẦN — cả một buổi sáng 09/09/2026 để trả lời một câu hỏi
    đáng lẽ là một phép đọc file
    ────────────────────────────────────────────────────────────────
    Sáng hôm ấy tôi kết luận **hai lần** rằng cửa này không cưỡng chế
    được, dựa trên hai thứ, và cả hai đều không đứng được:

    1. File dấu vết `vibe_da_doc_<phiên>.json` trong TEMP. Nó do
       `_ghi_da_doc()` tạo — mà một lượt chạy TAY kịch bản này với id
       phiên thật sinh ra file **y hệt**. Không phân biệt được "cửa nổ"
       với "tôi gõ tay".
    2. Một phép thử: `Edit` lên file được bảo vệ → không bị chặn. Nhưng
       phép thử ấy dùng `old_string` **không tồn tại trong file**. Thao
       tác hỏng ở khâu kiểm tra và hook không bao giờ được gọi.

       **Một thao tác HỎNG không kiểm được một cái cửa chạy TRƯỚC thao
       tác.** Phép thử không đo cái nó tưởng nó đo.

    Làm lại bằng một `Edit` HỢP LỆ, có nhật ký này: cửa nổ, ghi
    `CHO-QUA-da-doc-du` — nó cho qua vì phiên ấy **đã đọc đủ** hai tài
    liệu, đúng thiết kế. Cửa vẫn luôn hoạt động.

    Cái làm mất cả buổi sáng không phải cửa hỏng, mà là cửa **im lặng ở
    mọi nhánh nhường đường**. Ba khả năng — không chạy · chạy rồi nhường
    đường · chạy rồi mã thoát bị bỏ qua — trông giống hệt nhau từ bên
    ngoài.

    **Một cửa không ghi lại việc mình đã chạy thì không phân biệt được
    với cửa chết.** Nhật ký này biến câu hỏi ấy thành một phép đọc file.

    Ghi ở MỌI nhánh, kể cả nhánh nhường đường, và kể cả khi không đọc nổi
    stdin. Nhánh im lặng chính là nhánh cần nhìn thấy nhất.
    """
    try:
        with open(duong_dan_nhat_ky(), "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{nhan}\t"
                    f"{chi_tiet}\n")
    except Exception:
        pass                          # nhật ký hỏng KHÔNG được làm kẹt cửa


def quyet_dinh(d: dict) -> tuple[int, str, str]:
    """Quyết định từ payload hook. Trả `(mã thoát, nhãn, chi tiết)`.

    Tách khỏi `main()` để kiểm được bằng máy: `main()` đọc stdin và in ra
    stderr, còn hàm này chỉ nhận một dict và trả một bộ ba. Nhãn là thứ đi
    vào nhật ký, nên nó phải nói ra **nhánh nào đã chạy**, không chỉ nói
    chặn hay không.
    """
    phien = str(d.get("session_id") or "khong-ro")
    tool = str(d.get("tool_name") or "")
    tho = (d.get("tool_input") or {}).get("file_path")
    if not tho:
        return 0, "BO-QUA-khong-co-file_path", tool

    p = Path(str(tho))
    if tool == "Read":
        if p.name in TAI_LIEU_BAT_BUOC:
            _ghi_da_doc(phien, p.name)
            return 0, "GHI-da-doc", p.name
        return 0, "BO-QUA-doc-file-khac", p.name

    if tool not in ("Write", "Edit", "NotebookEdit"):
        return 0, "BO-QUA-tool-khac", tool
    if not _anh_huong_ket_qua(p):
        return 0, "BO-QUA-file-khong-anh-huong-ket-qua", p.name

    thieu = [t for t in TAI_LIEU_BAT_BUOC if t not in _da_doc(phien)]
    if not thieu:
        return 0, "CHO-QUA-da-doc-du", p.name
    return 2, "CHAN", f"{p.name} · thiếu: {','.join(thieu)}"


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    try:
        d = json.load(sys.stdin)
    except Exception:
        ghi_nhat_ky("HONG-khong-doc-duoc-stdin")
        return 0                      # hỏng thì nhường đường

    ma, nhan, chi_tiet = quyet_dinh(d)
    ghi_nhat_ky(nhan, chi_tiet)
    if ma == 0:
        return 0

    p = Path(str((d.get("tool_input") or {}).get("file_path")))
    thieu = [t for t in TAI_LIEU_BAT_BUOC
             if t not in _da_doc(str(d.get("session_id") or "khong-ro"))]
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
