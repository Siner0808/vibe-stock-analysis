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


sys.path.insert(0, str(GOC / "tools"))
import cua_doc_bat_buoc as cua  # noqa: E402


def test_MOI_nhanh_deu_co_nhan_rieng_trong_nhat_ky():
    """Bảy nhánh, bảy nhãn khác nhau. Không nhánh nào im lặng.

    VÌ SAO — mất cả buổi sáng 09/09/2026 cho một câu hỏi đáng lẽ là một
    phép đọc file: "cửa này có chạy không?"

    Cửa nhường đường ở năm nhánh khác nhau và **không nhánh nào để lại dấu
    vết**. Từ bên ngoài, ba khả năng trông giống hệt nhau: cửa không chạy ·
    cửa chạy rồi nhường đường · cửa chạy và mã thoát bị bỏ qua.

    Một cửa không ghi lại việc mình đã chạy thì không phân biệt được với
    cửa chết. Test này khoá việc MỖI nhánh mang một nhãn RIÊNG — nhãn
    chung cho hai nhánh thì nhật ký lại mất đúng thứ nó sinh ra để nói.
    """
    ma_kq = str(GOC / "paper_metrics.py")
    truong_hop = [
        ({"tool_name": "Edit", "tool_input": {}}, 0, "BO-QUA-khong-co-file_path"),
        ({"tool_name": "Read", "tool_input": {"file_path": str(GOC / "README.md")}},
         0, "BO-QUA-doc-file-khac"),
        ({"tool_name": "Bash", "tool_input": {"file_path": ma_kq}},
         0, "BO-QUA-tool-khac"),
        ({"tool_name": "Edit", "tool_input": {"file_path": str(GOC / "app.py")}},
         0, "BO-QUA-file-khong-anh-huong-ket-qua"),
        ({"session_id": "test-nhan-chua-doc", "tool_name": "Edit",
          "tool_input": {"file_path": ma_kq}}, 2, "CHAN"),
    ]
    nhan_thay = set()
    for d, ma_cho, nhan_cho in truong_hop:
        ma, nhan, _ = cua.quyet_dinh(d)
        assert ma == ma_cho, f"{nhan_cho}: mã thoát {ma}, chờ {ma_cho}"
        assert nhan == nhan_cho, f"chờ nhãn {nhan_cho!r}, nhận {nhan!r}"
        nhan_thay.add(nhan)

    phien = "test-nhan-da-doc"
    for ten in cua.TAI_LIEU_BAT_BUOC:
        ma, nhan, _ = cua.quyet_dinh(
            {"session_id": phien, "tool_name": "Read",
             "tool_input": {"file_path": str(GOC / ten)}})
        assert (ma, nhan) == (0, "GHI-da-doc"), f"đọc tài liệu -> {nhan!r}"
        nhan_thay.add(nhan)

    ma, nhan, _ = cua.quyet_dinh(
        {"session_id": phien, "tool_name": "Edit",
         "tool_input": {"file_path": ma_kq}})
    assert (ma, nhan) == (0, "CHO-QUA-da-doc-du"), f"đọc đủ rồi -> {nhan!r}"
    nhan_thay.add(nhan)

    assert len(nhan_thay) == 7, (
        f"bảy nhánh phải cho bảy nhãn khác nhau, thấy {len(nhan_thay)}: "
        f"{sorted(nhan_thay)}. Hai nhánh dùng chung một nhãn thì nhật ký "
        f"mất đúng thứ nó sinh ra để nói.")
    print(f"PASS  bảy nhánh, bảy nhãn: {len(nhan_thay)}")


def test_nhanh_NHUONG_DUONG_cung_ghi_nhat_ky():
    """Nhánh im lặng nhất — không đọc nổi stdin — vẫn phải để lại dấu.

    Đây là nhánh "hỏng thì KHÔNG chặn" ở đầu file. Nó đúng về hành vi
    (cửa hỏng không được làm kẹt việc), nhưng nếu nó im luôn thì không ai
    biết cửa đã chạy hay chưa — và đó chính là chỗ mất một buổi sáng.
    """
    truoc = _so_dong_nhat_ky()
    r = subprocess.run([sys.executable, str(HOOK)], input="{ khong phai json",
                       capture_output=True, text=True, timeout=30,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, "stdin hỏng mà lại chặn — sai hướng fail"
    sau = _so_dong_nhat_ky()
    assert sau == truoc + 1, (
        f"nhánh nhường đường không ghi nhật ký ({truoc} -> {sau}). "
        f"Cửa im lặng ở nhánh này thì không phân biệt được với cửa chết.")
    assert "HONG-khong-doc-duoc-stdin" in _doc_nhat_ky()[-1]
    print("PASS  nhánh nhường đường vẫn ghi nhật ký")


def test_nhat_ky_HONG_thi_cua_van_chay():
    """Ghi nhật ký hỏng KHÔNG được làm kẹt cửa.

    Nhật ký là dụng cụ quan sát, không phải một phần của phép kiểm. Nếu nó
    ném thì mọi thao tác Read/Edit của phiên đứng lại — tệ hơn hẳn cái nó
    sửa. Đục thẳng đường dẫn thành một chỗ không ghi được.
    """
    goc = cua.duong_dan_nhat_ky
    cua.duong_dan_nhat_ky = lambda: Path(GOC / "khong-co-thu-muc-nay"
                                         / "sau-nua" / "x.log")
    try:
        cua.ghi_nhat_ky("THU", "khong-duoc-nem")          # không được ném
        ma, nhan, _ = cua.quyet_dinh(
            {"session_id": "test-nk-hong", "tool_name": "Edit",
             "tool_input": {"file_path": str(GOC / "paper_metrics.py")}})
        assert (ma, nhan) == (2, "CHAN"), "nhật ký hỏng làm hỏng quyết định"
    finally:
        cua.duong_dan_nhat_ky = goc
    print("PASS  nhật ký hỏng -> cửa vẫn quyết định đúng")


def _doc_nhat_ky() -> list:
    f = cua.duong_dan_nhat_ky()
    if not f.exists():
        return []
    return f.read_text(encoding="utf-8").splitlines()


def _so_dong_nhat_ky() -> int:
    return len(_doc_nhat_ky())


def test_duong_CHINH_cung_ghi_nhat_ky_moi_lan_chay():
    """Lần chạy BÌNH THƯỜNG cũng phải để lại một dòng.

    Test này ra đời vì một đột biến sống sót: xoá lời gọi ghi nhật ký ở
    đường chính của `main()` mà cả bộ test vẫn xanh.

    `test_nhanh_NHUONG_DUONG_cung_ghi_nhat_ky` chỉ đi qua đường stdin
    hỏng, nên nó khoá đúng một dòng `ghi_nhat_ky` — và để hở dòng kia,
    đúng cái dòng ghi lại MỌI lần chạy bình thường. Tức là gác cho việc
    quan sát lại có một chỗ không quan sát được.

    Gọi qua subprocess chứ không gọi `quyet_dinh` trực tiếp: `quyet_dinh`
    không ghi nhật ký, `main()` mới ghi. Kiểm ở tầng nào thì phải chạy ở
    tầng ấy.
    """
    truoc = _so_dong_nhat_ky()
    r = _goi("Edit", str(GOC / "app.py"), "test-duong-chinh")
    assert r.returncode == 0, f"app.py không ảnh hưởng kết quả mà bị chặn"
    sau = _so_dong_nhat_ky()
    assert sau == truoc + 1, (
        f"đường chính không ghi nhật ký ({truoc} -> {sau}). Cửa chạy mà "
        f"không để lại dấu thì không phân biệt được với cửa chết — đó "
        f"đúng là thứ nhật ký này sinh ra để chấm dứt.")
    assert "BO-QUA-file-khong-anh-huong-ket-qua" in _doc_nhat_ky()[-1], (
        f"ghi nhầm nhãn: {_doc_nhat_ky()[-1]!r}")
    print("PASS  đường chính ghi nhật ký mỗi lần chạy")
