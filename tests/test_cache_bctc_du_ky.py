"""Ba bảng BCTC, ba đường đọc KHÁC NHAU — đừng suy đường này ra đường kia.

VÌ SAO CÓ FILE NÀY, VÀ VÌ SAO NÓ ĐÃ BỊ VIẾT LẠI
───────────────────────────────────────────────
Bản đầu (11/09/2026, sáng) khẳng định: *"bảng `ratio` chỉ có 2–4 kỳ, mà
`ratio` mới là bảng `fundamental_agent` thật sự đọc, nên điều kiện xem
lại agent cơ bản KHÔNG thoả."*

**Nửa sau của câu ấy SAI**, và nó đã bị đẩy lên `main`. Đo lại cùng ngày:

    backtest/fundamentals/*_ratio.csv   <- Finance(source="VCI", period="quarter")
    fundamental_agent                   <- Finance(source="KBS", period="year"), GỌI MẠNG
    experiment_fundamentals (phép đo IC) <- CHỈ đọc _income.csv + _balance.csv

Chữ `ratio` xuất hiện **0 lần** trong `experiment_fundamentals.py`. Ba
đường trùng **tên bảng** nhưng khác **nguồn**, khác **độ mịn**, và khác
cả chỗ lấy. Tôi suy đường này ra đường kia vì thấy cùng chữ `ratio` —
đúng lỗi 36.

Hệ quả thật, đo bằng chính dụng cụ định nghĩa nó: cache giá lùi về
2018-09 đưa số kỳ dùng được từ **19 lên 31**, tức **điều kiện xem lại ĐÃ
THOẢ** (ngưỡng 28). Tôi đã dừng sai lý do.

File này nay khoá những gì ĐÃ ĐO ĐƯỢC, không khoá một suy luận.
"""
import ast
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

KHO = GOC / "backtest" / "fundamentals"
RE_KY = re.compile(r"^\d{4}-Q[1-4]$")


def _chuoi_trong(duong: Path) -> set[str]:
    """Mọi hằng chuỗi trong một file .py, đọc bằng AST.

    AST chứ không `in`: chữ `ratio` nằm trong chú thích của
    `experiment_fundamentals.py` cả chục lần, mà chú thích không đọc
    file nào. `CLAUDE.md` 22/08/2026: *gác phải đọc AST, không đọc `in`*.
    """
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    return {n.value for n in ast.walk(cay)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def test_PHEP_DO_IC_khong_doc_bang_ratio():
    """Khoá đúng cái tôi đã suy sai.

    `experiment_fundamentals.py` dựng đặc trưng từ `_income.csv` và
    `_balance.csv`. Nó KHÔNG đọc `_ratio.csv`. Số kỳ dùng được của phép
    đo IC vì thế do hai bảng ấy quyết định — chúng có 34 kỳ, không phải
    2–4 như `ratio`.
    """
    f = GOC / "experiment_fundamentals.py"
    chuoi = _chuoi_trong(f)
    doc_ratio = [s for s in chuoi if "_ratio" in s or s == "ratio"]
    assert not doc_ratio, (
        f"`experiment_fundamentals.py` nay CÓ nhắc tới bảng ratio trong một "
        f"hằng chuỗi: {doc_ratio}\nNếu nó thật sự đọc bảng ấy thì số kỳ dùng "
        f"được đổi hẳn — đọc lại `docs/STATE.md` BƯỚC 53 trước khi sửa phép "
        f"kiểm này.")
    assert any("_income" in s for s in chuoi), "phải đọc _income.csv"
    assert any("_balance" in s for s in chuoi), "phải đọc _balance.csv"
    print("PASS  phép đo IC đọc income+balance, KHÔNG đọc ratio")


def test_AGENT_CO_BAN_va_CACHE_dung_hai_NGUON_khac_nhau():
    """Hai đường cùng tên bảng `ratio` mà khác nguồn và khác độ mịn.

    Trùng tên là chỗ suy sai. Khoá lại để lần sau không ai suy nữa.
    """
    agent = _chuoi_trong(GOC / "fundamental_agent.py")
    fetch = _chuoi_trong(GOC / "fetch_fundamentals.py")

    assert "KBS" in agent and "year" in agent, (
        f"`fundamental_agent` phải đọc KBS/year — nay thấy nguồn khác. "
        f"Nếu đổi thật thì nó bắt đầu dùng chung đường với cache, và "
        f"`docs/STATE.md` BƯỚC 53 phải được đọc lại.")
    assert "VCI" in fetch and "quarter" in fetch, (
        "`fetch_fundamentals` phải tải VCI/quarter — nay thấy khác.")
    print("PASS  agent đọc KBS/year · cache tải VCI/quarter — hai đường khác nhau")


def test_CACHE_ratio_it_ky_la_do_NGUON_cat_chu_khong_phai_cong_cu_hong():
    """Đo 11/09/2026: hỏi thẳng nguồn, `ratio` trả 4 kỳ còn hai bảng kia 34.

    Đây là phép kiểm trên ĐĨA, không gọi mạng. Nó khoá điều đã đo: cache
    khớp đúng thứ nguồn cho, nên `fetch_fundamentals.py` không hỏng.
    """
    if not KHO.is_dir():
        pytest.skip("chưa có cache BCTC trên máy này (CI không tải)")

    def so_ky(bang: str) -> list[int]:
        import pandas as pd
        ra = []
        for f in sorted(KHO.glob(f"*_{bang}.csv")):
            try:
                ra.append(sum(1 for c in pd.read_csv(f, nrows=0).columns
                              if RE_KY.match(c)))
            except Exception:
                pass
        return ra

    r, b = so_ky("ratio"), so_ky("balance")
    if not r or not b:
        pytest.skip("cache BCTC rỗng")
    tv_r = sorted(r)[len(r) // 2]
    tv_b = sorted(b)[len(b) // 2]
    assert tv_r * 2 < tv_b, (
        f"`ratio` trung vị {tv_r} kỳ, `balance` trung vị {tv_b} — hai bảng "
        f"nay KHÔNG còn chênh nhau quá hai lần.\nNguồn có thể đã mở rộng "
        f"`ratio`. Đọc `docs/STATE.md` BƯỚC 53 rồi cập nhật ghi chú trước "
        f"khi đụng phép kiểm này.")
    print(f"PASS  `ratio` trung vị {tv_r} kỳ · `balance` {tv_b} kỳ — "
          f"nguồn cắt, không phải công cụ hỏng")


def test_CLAUDE_md_khong_duoc_noi_34_ky_ma_KHONG_NOI_BANG_NAO():
    """Con số kỳ BCTC phải đi kèm tên bảng — phần ĐÚNG của lỗi 33.

    Nửa sai của lỗi 33 là hệ quả tôi suy ra; nửa đúng là chính con số:
    *"34 kỳ"* không nói nó đếm bảng nào, nên nó bị đọc thành bảng khác.
    Phần ấy giữ nguyên.
    """
    src = (GOC / "CLAUDE.md").read_text(encoding="utf-8")
    # Ten bang phai nam trong CUNG MENH DE. Do 11/09/2026: moi cho khai
    # dung deu co ten bang trong vong 30 ky tu. Lay 60 la rong gap doi.
    CUA_SO = 60
    thieu = [src[max(0, m.start() - 60):m.end() + 60]
             for m in re.finditer(r"34\s*kỳ", src)
             if not re.search(r"`?(ratio|balance|income)`?",
                              src[max(0, m.start() - CUA_SO):m.end() + CUA_SO])]
    assert not thieu, (
        "CLAUDE.md nhắc '34 kỳ' mà không nói rõ BẢNG NÀO trong cùng mệnh "
        "đề:\n" + "\n".join(f"  …{t}…" for t in thieu) +
        "\n`ratio` có 2–4 kỳ mỗi mã, `balance`/`income` có 34.")
    print("PASS  mọi chỗ nhắc '34 kỳ' đều nói rõ bảng nào")
