"""Cửa chặn: chưa đọc tài liệu bắt buộc thì không được sửa file ảnh hưởng kết quả.

VÌ SAO CÓ FILE NÀY

`CLAUDE.md` ghi rõ: *"Đọc `NGUYEN-TAC-DO-LUONG.md` và `MO-XE-KIEN-TRUC.md`
TRƯỚC KHI sửa bất cứ thứ gì liên quan tới kết quả."*

Ngày 20/08/2026, agent (Claude) đã sửa `paper_metrics.py`, `paper_runner.py`,
`market_filter.py`, `paper_trading.py` và nhiều file khác **trước khi đọc
hai tài liệu đó**, và chỉ đọc khi người dùng hỏi. Hậu quả cụ thể: nó lặp
lại một phân tích đã có sẵn trong tài liệu (đòn bẩy 2,2× của +636,11%), và
trình bày +14,24% như "con số thật" trong khi chính tài liệu đã liệt con số
đó vào danh sách vô nghĩa.

Nguyên nhân giống hệt mọi thứ khác trong dự án này: **một luật không phải
là cửa thì chỉ là gợi ý.** `.claude/settings.json` trước đó chỉ có
`PostToolUse` — chạy SAU khi ghi. Chuông báo cháy, không phải cửa chống cháy.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
HOOK = GOC / "tools" / "cua_doc_bat_buoc.py"


def _goi(tool: str, file_path: str, phien: str) -> subprocess.CompletedProcess:
    vao = json.dumps({
        "session_id": phien,
        "tool_name": tool,
        "tool_input": {"file_path": file_path},
    })
    # encoding="utf-8" là BẮT BUỘC, không phải trang trí. Không có nó,
    # tiến trình cha giải mã stderr của hook bằng codec locale Windows
    # (cp1258) và ném UnicodeDecodeError trong luồng đọc — `r.stderr` khi đó
    # thành None, và test đo nhầm rằng hook không nói gì.
    return subprocess.run([sys.executable, str(HOOK)], input=vao,
                          capture_output=True, text=True, timeout=30,
                          encoding="utf-8", errors="replace")


def test_chua_doc_thi_KHONG_duoc_sua_file_anh_huong_ket_qua():
    phien = "test-chua-doc"
    r = _goi("Edit", str(GOC / "paper_metrics.py"), phien)
    assert r.returncode == 2, f"không chặn (exit {r.returncode})"
    assert "NGUYEN-TAC-DO-LUONG" in r.stderr, f"không nói phải đọc gì: {r.stderr!r}"
    print("PASS  chưa đọc -> chặn sửa paper_metrics.py")


def test_doc_du_hai_tai_lieu_roi_thi_duoc_sua():
    phien = "test-da-doc"
    for ten in ("NGUYEN-TAC-DO-LUONG.md", "MO-XE-KIEN-TRUC.md"):
        r = _goi("Read", str(GOC / ten), phien)
        assert r.returncode == 0, f"đọc tài liệu mà bị chặn: {r.stderr!r}"
    r = _goi("Edit", str(GOC / "paper_metrics.py"), phien)
    assert r.returncode == 0, f"đọc đủ rồi mà vẫn chặn: {r.stderr!r}"
    print("PASS  đọc đủ hai tài liệu -> cho sửa")


def test_doc_MOT_tai_lieu_van_bi_chan():
    phien = "test-doc-mot"
    _goi("Read", str(GOC / "NGUYEN-TAC-DO-LUONG.md"), phien)
    r = _goi("Edit", str(GOC / "paper_trading.py"), phien)
    assert r.returncode == 2, "đọc một nửa mà vẫn cho qua"
    assert "MO-XE-KIEN-TRUC" in r.stderr
    print("PASS  đọc thiếu một tài liệu -> vẫn chặn")


def test_file_KHONG_anh_huong_ket_qua_thi_khong_chan():
    """Cửa hẹp có chủ đích: chặn quá rộng thì người ta tắt nó đi."""
    phien = "test-file-thuong"
    for ten in ("README.md", "docs/STATE.md", "tools/kiem_ban_sach.py"):
        r = _goi("Edit", str(GOC / ten), phien)
        assert r.returncode == 0, f"chặn nhầm {ten}: {r.stderr!r}"
    print("PASS  file không ảnh hưởng kết quả -> không chặn")


def test_phien_khac_thi_khong_ke_thua_quyen():
    """Đọc ở phiên trước không tính cho phiên này."""
    _goi("Read", str(GOC / "NGUYEN-TAC-DO-LUONG.md"), "phien-A")
    _goi("Read", str(GOC / "MO-XE-KIEN-TRUC.md"), "phien-A")
    r = _goi("Edit", str(GOC / "master_agent.py"), "phien-B")
    assert r.returncode == 2, "phiên B thừa hưởng quyền của phiên A"
    print("PASS  quyền không rò giữa các phiên")


def test_hook_hong_thi_KHONG_chan_cong_viec():
    """Đầu vào rác không được làm kẹt mọi thao tác."""
    r = subprocess.run([sys.executable, str(HOOK)], input="khong-phai-json",
                       capture_output=True, text=True, timeout=30,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, "đầu vào hỏng mà chặn cả công việc"
    print("PASS  đầu vào hỏng -> không chặn")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()
