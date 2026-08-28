"""Mọi khoá trong bộ trọng số phải THỰC SỰ được nhân vào điểm.

Cho tới 28/08/2026 cả ba bộ trọng số của `MasterConsensusAgent.run` đều
mang khoá `"news": 0.0`, mà biểu thức `pre_debate_score` không hề nhắc
tới `weights["news"]`. Hậu quả: đặt `"news": 0.25` vào đó thì KHÔNG có
gì thay đổi — một núm vặn giả. Đây đúng là kiểu lỗi "silent pass" mà
`NGUYEN-TAC-DO-LUONG.md` cảnh báo: sửa xong, chạy xong, số không đổi,
không ai biết mình vừa không làm gì.

Test này gác cả hai chiều:
  · khoá có trong dict mà không được nhân  -> núm vặn giả
  · khoá được nhân mà không có trong dict  -> KeyError lúc chạy

So bằng AST, không bằng chuỗi: `"news" in src` khớp cả chữ trong chú
thích, và file này có rất nhiều chú thích nói về news.
"""
import ast
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NGUON = pathlib.Path(__file__).resolve().parent.parent / "master_agent.py"


def _ham_run() -> ast.FunctionDef:
    cay = ast.parse(NGUON.read_text(encoding="utf-8"))
    for lop in ast.walk(cay):
        if isinstance(lop, ast.ClassDef) and lop.name == "MasterConsensusAgent":
            for n in lop.body:
                if isinstance(n, ast.FunctionDef) and n.name == "run":
                    return n
    raise AssertionError("Không tìm thấy MasterConsensusAgent.run")


def _cac_bo_trong_so(ham) -> list[tuple[int, set[str]]]:
    """(số dòng, tập khoá) của mỗi dict gán cho biến `weights`."""
    ra = []
    for n in ast.walk(ham):
        if not isinstance(n, ast.Assign) or not isinstance(n.value, ast.Dict):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "weights"
                   for t in n.targets):
            continue
        khoa = {k.value for k in n.value.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        ra.append((n.lineno, khoa))
    return ra


def _khoa_duoc_nhan(ham) -> set[str]:
    """Các khoá xuất hiện dưới dạng `weights["X"]` trong thân hàm."""
    ra = set()
    for n in ast.walk(ham):
        if (isinstance(n, ast.Subscript)
                and isinstance(n.value, ast.Name) and n.value.id == "weights"
                and isinstance(n.slice, ast.Constant)
                and isinstance(n.slice.value, str)):
            ra.add(n.slice.value)
    return ra


def test_tim_duoc_ba_bo_trong_so():
    """Nếu cấu trúc đổi thì hai test dưới thành vô nghĩa — chặn trước."""
    bo = _cac_bo_trong_so(_ham_run())
    assert len(bo) == 3, (
        f"Chờ 3 bộ trọng số động, thấy {len(bo)}. Cập nhật test này trước "
        f"khi tin vào hai test còn lại.")


def test_khong_co_num_van_gia():
    """Khoá nằm trong dict mà không được nhân = núm vặn không nối vào đâu."""
    ham = _ham_run()
    duoc_nhan = _khoa_duoc_nhan(ham)
    assert duoc_nhan, "Không thấy `weights[...]` nào — biểu thức điểm đã đổi?"
    for dong, khoa in _cac_bo_trong_so(ham):
        thua = khoa - duoc_nhan
        assert not thua, (
            f"master_agent.py dòng {dong}: khoá {sorted(thua)} có trong bộ "
            f"trọng số nhưng KHÔNG được nhân vào `pre_debate_score`. Đặt "
            f"số khác 0 vào đó sẽ không làm điểm dịch một ly — núm vặn giả.")


def test_khong_nhan_khoa_khong_ton_tai():
    """Khoá được nhân mà dict thiếu = KeyError ở đúng nhánh trọng số đó."""
    ham = _ham_run()
    duoc_nhan = _khoa_duoc_nhan(ham)
    for dong, khoa in _cac_bo_trong_so(ham):
        thieu = duoc_nhan - khoa
        assert not thieu, (
            f"master_agent.py dòng {dong}: biểu thức điểm đọc {sorted(thieu)} "
            f"nhưng bộ trọng số này không có — KeyError khi rơi vào nhánh đó.")
