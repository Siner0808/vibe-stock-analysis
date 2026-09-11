"""Cache BCTC — số kỳ phải khai theo ĐÚNG BẢNG, không khai gộp.

VÌ SAO CÓ FILE NÀY
──────────────────
`CLAUDE.md` ghi từ 23/08/2026: *"Cache BCTC nay là 71 mã × 34 kỳ (hạng
silver), nhưng cache GIÁ chỉ lùi tới 2021-10 nên còn 19 kỳ dùng được"*, và
đặt điều kiện xem lại agent cơ bản là *"cache giá lùi được về 2018"*.

Ngày 11/09/2026 vế ấy **đạt** — giá lùi tới 2018-09-13. Điều kiện vẫn
**không thoả**, vì đếm lại thì ràng buộc đã đổi chỗ:

    ratio    15 ky khac nhau · MOI MA chi 2-4 ky   <- agent DOC bang nay
    balance  34 ky
    income   34 ky

Câu *"34 kỳ"* đúng cho `balance`/`income` và **sai cho `ratio`**. Nó sống
19 ngày vì không gác nào đối chiếu con số ấy với **bảng cụ thể** mà
`fundamental_agent` đọc.

Cùng hình dạng `N_DAY_DU` 596/451 và cờ C5 `True`/`False`: một câu đúng
về **thứ này** được đọc thành đúng về **thứ kia**.

HAI CHIỀU, LUÔN LUÔN
────────────────────
Bản đầu của file này chỉ chạy phép phán trên `CLAUDE.md` thật — tức chỉ
trên đầu vào SẠCH. Đục thử lôi ra ngay: mọi đột biến **nới lỏng** gác đều
SỐNG, vì nới một phép kiểm ra thì nó vẫn xanh trên dữ liệu sạch.

Nên phần phán được tách thành hàm thuần, và mỗi hàm được thử bằng CẢ đầu
vào phải-qua LẪN đầu vào phải-chặn.
"""
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

KHO = GOC / "backtest" / "fundamentals"
RE_KY = re.compile(r"^\d{4}-Q[1-4]$")

# Tên bảng phải nằm trong CÙNG MỆNH ĐỀ, không phải "đâu đó gần".
#
# Bản đầu cho 400 ký tự, và đục thử lôi ra ngay: trả câu 23/08 về dạng
# không nói bảng nào thì gác VẪN XANH, vì một ghi chú cách đó vài dòng có
# nhắc chữ `ratio`. Phép kiểm khi ấy đo "có chữ ấy ở gần không", không đo
# "con số này có được giải thích không".
#
# Đo trên bản ngày 11/09/2026: mọi chỗ khai ĐÚNG đều có tên bảng trong
# vòng **30 ký tự**. Lấy 60 là rộng gấp đôi chỗ cần, vẫn chặt hơn một
# đoạn văn.
CUA_SO = 60

# `ratio` 4 kỳ so với `balance` 34 — chênh 8,5 lần. Đòi gấp đôi là một
# ngưỡng rộng rãi, chỉ để bắt lúc hai bảng thật sự xích lại gần nhau.
BOI = 2


def cho_qua_tai_lieu(src: str) -> list[str]:
    """PHÉP PHÁN. Trả các chỗ nhắc '34 kỳ' mà KHÔNG nói rõ bảng nào."""
    thieu = []
    for m in re.finditer(r"34\s*kỳ", src):
        quanh = src[max(0, m.start() - CUA_SO):m.end() + CUA_SO]
        if not re.search(r"`?(ratio|balance|income)`?", quanh):
            thieu.append(src[max(0, m.start() - 60):m.end() + 60])
    return thieu


def hai_bang_con_chenh_xa(ratio: dict[str, int],
                          balance: dict[str, int]) -> bool:
    """PHÉP PHÁN. `ratio` còn ít kỳ hơn `balance` nhiều lần không?"""
    chung = sorted(set(ratio) & set(balance))
    if not chung:
        return False
    tv_r = sorted(ratio[m] for m in chung)[len(chung) // 2]
    tv_b = sorted(balance[m] for m in chung)[len(chung) // 2]
    return tv_r * BOI < tv_b


def _so_ky(bang: str) -> dict[str, int]:
    """{mã: số kỳ} cho một bảng. Rỗng nếu kho chưa có."""
    import pandas as pd
    ra = {}
    for f in sorted(KHO.glob(f"*_{bang}.csv")):
        try:
            cols = pd.read_csv(f, nrows=0).columns
        except Exception:
            continue
        ra[f.stem.rsplit("_", 1)[0]] = sum(1 for c in cols if RE_KY.match(c))
    return ra


# ─────────────── phép phán tự chứng minh, HAI CHIỀU ───────────────

def test_MAY_DO_phep_phan_tai_lieu_bat_duoc_ca_hai_chieu():
    """Không có phép thử này thì mọi đột biến NỚI LỎNG đều sống sót."""
    XAU = [
        ("nguyên văn câu 23/08",
         "Cache BCTC nay là 71 mã × 34 kỳ (hạng silver), nhưng cache GIÁ "
         "chỉ lùi tới 2021-10 nên còn 19 kỳ dùng được."),
        ("tên bảng ở XA, ngoài mệnh đề",
         "Cache BCTC nay là 71 mã × 34 kỳ (hạng silver)." + " x" * 60 +
         " Bảng `ratio` thì khác."),
        ("bảng bất đối xứng không nói bảng",
         "| Máy local | silver | không giới hạn (đo được 34 kỳ) | 300/phút |"),
    ]
    TOT = [
        ("nói rõ ngay sau con số",
         "Cache BCTC nay là 71 mã × 34 kỳ **ở bảng `balance` và `income`**."),
        ("nói rõ ngay trước con số",
         "Bảng `balance` và `income` đo được 34 kỳ."),
        ("không nhắc con số thì không phán",
         "Bảng nào cũng có ít kỳ hơn mong đợi."),
    ]
    for ten, src in XAU:
        assert cho_qua_tai_lieu(src), f"BỎ SÓT: {ten}\n  {src[:90]!r}"
    for ten, src in TOT:
        assert not cho_qua_tai_lieu(src), f"KÊU OAN: {ten}\n  {src[:90]!r}"
    print(f"PASS  phép phán tài liệu: chặn {len(XAU)}/{len(XAU)} xấu, "
          f"tha {len(TOT)}/{len(TOT)} tốt")


def test_MAY_DO_phep_phan_so_ky_bat_duoc_ca_hai_chieu():
    """Cùng lý do: một phép so chỉ chạy trên dữ liệu thật là phép so mù."""
    # con chenh xa -> True
    assert hai_bang_con_chenh_xa({"A": 4, "B": 4}, {"A": 34, "B": 34})
    assert hai_bang_con_chenh_xa({"A": 2, "B": 4, "C": 3}, {"A": 34, "B": 33, "C": 34})
    # da xich lai gan -> False, va do la luc tai lieu phai doc lai
    assert not hai_bang_con_chenh_xa({"A": 17, "B": 18}, {"A": 34, "B": 34})
    assert not hai_bang_con_chenh_xa({"A": 34, "B": 34}, {"A": 34, "B": 34})
    assert not hai_bang_con_chenh_xa({}, {})
    print("PASS  phép phán số kỳ: bắt được cả 'còn chênh xa' lẫn 'đã gần'")


# ───────────────────── áp lên dữ liệu THẬT ─────────────────────

def test_bang_RATIO_va_BALANCE_khong_duoc_gop_lam_mot():
    """Hai bảng có số kỳ khác hẳn nhau — đó là SỰ THẬT, không phải lỗi.

    Ngày nào hai bên xích lại gần nhau thì câu chuyện đổi, và tài liệu
    phải được đọc lại — nên test đỏ khi ấy là đúng việc nó phải làm.
    """
    if not KHO.is_dir():
        pytest.skip("chưa có cache BCTC trên máy này (CI không tải)")
    r, b = _so_ky("ratio"), _so_ky("balance")
    if not r or not b:
        pytest.skip("cache BCTC rỗng")
    assert hai_bang_con_chenh_xa(r, b), (
        "`ratio` và `balance` nay KHÔNG còn chênh nhau quá "
        f"{BOI} lần theo trung vị.\n"
        "Đó có thể là tin tốt (cache `ratio` đã đầy hơn), nhưng khi đó ghi "
        "chú trong CLAUDE.md về điều kiện xem lại agent cơ bản đã LẠC HẬU. "
        "Đọc `docs/STATE.md` BƯỚC 52 rồi cập nhật nó trước khi đụng vào "
        "phép kiểm này.")
    chung = sorted(set(r) & set(b))
    tv_r = sorted(r[m] for m in chung)[len(chung) // 2]
    tv_b = sorted(b[m] for m in chung)[len(chung) // 2]
    print(f"PASS  `ratio` trung vị {tv_r} kỳ · `balance` trung vị {tv_b} kỳ "
          f"trên {len(chung)} mã")


def test_CLAUDE_md_khong_duoc_noi_34_ky_ma_KHONG_NOI_BANG_NAO():
    """Con số kỳ BCTC phải đi kèm tên bảng. Đây là gác TÀI LIỆU.

    Gác dạng văn bản hợp lệ ở đây: `CLAUDE.md` là văn bản, và điều cần
    khoá là **một con số có nói rõ nó nói về cái gì hay không**.
    """
    thieu = cho_qua_tai_lieu((GOC / "CLAUDE.md").read_text(encoding="utf-8"))
    assert not thieu, (
        "CLAUDE.md nhắc '34 kỳ' mà không nói rõ BẢNG NÀO trong cùng mệnh "
        "đề:\n" + "\n".join(f"  …{t}…" for t in thieu) +
        "\n`ratio` có 2–4 kỳ mỗi mã, `balance`/`income` có 34. Một con số "
        "không nói rõ nó nói về bảng nào sẽ bị đọc thành bảng kia — đúng "
        "hình dạng N_DAY_DU 596/451.")
    print("PASS  mọi chỗ nhắc '34 kỳ' đều nói rõ bảng nào")
