"""`tools/doc_so_that.py` phải CHỈ ĐỌC — và điều đó kiểm bằng AST.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 12/08/2026 một lượt ghi đè xoá **96/113 lệnh thật**. Từ đó dự án có
một ranh giới: *sổ thật nằm trên Google Sheets; không ghi đè, không đẩy,
và KHÔNG đọc `paper_trades.db` ở máy vì nó là một bản sao chết.*

Một dụng cụ mới đọc sổ là đúng chỗ ranh giới ấy dễ bị vượt nhất. Nên nó
không được **hứa** là chỉ đọc — nó phải **chứng minh** được.

Đọc bằng **AST**, không bằng `in`: một cái tên như `push` còn nằm trong
khối chú thích giải thích *vì sao không gọi push* sẽ làm phép kiểm dạng
văn bản vô hiệu — đúng lỗi 38 của chính ngày hôm nay.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
DUNG_CU = GOC / "tools" / "doc_so_that.py"

sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import doc_so_that as dst  # noqa: E402

# Tên hàm/phương thức GHI. `unlink` KHÔNG nằm đây: dụng cụ có xoá một file
# DB TẠM trong thư mục tạm, và đó là việc đúng.
TEN_GHI = {"push", "write_all", "append_rows", "pull", "record_trade",
           "update_trade", "record_decision", "commit", "executemany"}


def _loi_goi(cay: ast.AST) -> set[str]:
    """Mọi TÊN được GỌI — `f()` và `x.f()`. Không tính tên chỉ nhắc tới."""
    ra: set[str] = set()
    for n in ast.walk(cay):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Name):
            ra.add(f.id)
        elif isinstance(f, ast.Attribute):
            ra.add(f.attr)
    return ra


def test_DUNG_CU_khong_goi_mot_ham_GHI_nao():
    """Phép kiểm chính. Thêm một lời gọi ghi vào đó → đỏ."""
    goi = _loi_goi(ast.parse(DUNG_CU.read_text(encoding="utf-8")))
    pham = sorted(goi & TEN_GHI)
    assert not pham, (
        f"tools/doc_so_that.py goi ham GHI: {pham}\n"
        f"No la dung cu CHI DOC. Su co 12/08/2026 xoa 96/113 lenh that bat "
        f"dau tu dung mot duong ghi khong ai de y.")
    print(f"PASS  khong goi mot trong {len(TEN_GHI)} ten ghi nao")


def test_DB_dung_cu_TAO_RA_nam_trong_THU_MUC_TAM():
    """Kiểm CƠ CHẾ, không kiểm chữ.

    Hai bản trước của phép kiểm này quét chuỗi tìm `paper_trades` và **cả
    hai đều đỏ oan** — lần đầu vì docstring giải thích *vì sao không đọc sổ
    ở máy*, lần sau vì một banner in ra màn hình nói đúng câu ấy. Đó là lỗi
    38 mắc lần thứ ba và thứ tư trong ngày 12/09/2026.

    **Nhắc một cái tên KHÁC với mở nó.** Thứ bảo đảm sổ thật an toàn không
    phải việc văn bản có chứa chữ gì, mà là: dụng cụ chỉ tạo DB trong thư
    mục TẠM, và không gọi một hàm ghi nào (phép kiểm ở trên).
    """
    goi = _loi_goi(ast.parse(DUNG_CU.read_text(encoding="utf-8")))
    assert "gettempdir" in goi, (
        "dung cu khong dung tempfile.gettempdir() — khong chung minh duoc "
        "DB no tao ra nam ngoai repo")
    assert "keo_so_co_thu_lai" in goi, (
        "phai di qua duong keo an toan da co (tools/canh_cong_c5.py dung), "
        "khong tu che mot duong keo moi")
    print("PASS  DB tao ra nam trong thu muc tam, qua duong keo an toan")


def test_PHEP_THU_bat_dung_cai_no_sinh_ra_de_bat():
    """Dựng lại nguyên văn một dụng cụ VI PHẠM. Gác phải thấy.

    Mẫu dựng tay, không đọc file thật: một gác chỉ chạy trên đầu vào sạch
    thì mọi phép nới đều sống sót (lỗi 34).
    """
    import tempfile

    XAU = [
        'import sheets_store\nsheets_store.push(db, be)\n',
        'be.write_all("trades", rows)\n',
        'so.record_trade(t)\n',
        'gs.pull(db, be)\n',
    ]
    TOT = [
        'be.read_rows("trades")\n',
        'gs.keo_so_co_thu_lai(str(tam))\n',
        '# khong duoc goi push() hay write_all() o day\nx = 1\n',
    ]
    with tempfile.TemporaryDirectory() as t:
        for i, mau in enumerate(XAU):
            f = Path(t) / f"x{i}.py"
            f.write_text(mau, encoding="utf-8")
            goi = _loi_goi(ast.parse(f.read_text(encoding="utf-8")))
            assert goi & TEN_GHI, f"KHONG bat duoc mau phai bat:\n{mau}"
        for i, mau in enumerate(TOT):
            f = Path(t) / f"t{i}.py"
            f.write_text(mau, encoding="utf-8")
            goi = _loi_goi(ast.parse(f.read_text(encoding="utf-8")))
            assert not (goi & TEN_GHI), f"bat NHAM mau hop le:\n{mau}"
    print(f"PASS  bat {len(XAU)}/{len(XAU)} mau ghi · "
          f"bo qua {len(TOT)}/{len(TOT)} mau chi doc")


def test_TEN_TRONG_CHU_THICH_khong_lam_gac_vo_hieu():
    """Chính docstring của dụng cụ nhắc `push()`. AST phải bỏ qua nó.

    Đây là lỗi 38, mắc sáng cùng ngày: một phép kiểm dạng `in` bị chính
    lời giải thích của nó làm hỏng.
    """
    mau = ('"""Khong bao gio goi push() hay write_all()."""\n'
           '# push(db, be) — dong nay bi chu thich\n'
           'x = read_rows("trades")\n')
    goi = _loi_goi(ast.parse(mau))
    assert not (goi & TEN_GHI), f"AST dem ca ten trong chu thich: {goi}"
    assert "push" in mau, "mau phai THAT SU chua chu `push`"
    print("PASS  ten trong docstring/chu thich khong lam gac vo hieu")


def test_HAI_HAM_THONG_KE_la_ham_THUAN():
    """`tom_tat` và `tien_ve_truoc` phải chạy được không cần mạng.

    Tách phần tính khỏi phần lấy dữ liệu để thử được bằng mẫu dựng tay —
    một dụng cụ chỉ kiểm được khi có mạng là một dụng cụ không kiểm được.
    """
    class L:
        def __init__(self, ma, tt, ngay):
            self.symbol, self.status, self.signal_date = ma, tt, ngay

    ds = [L("AAA", "CLOSED", "2026-08-28"), L("BBB", "OPEN", "2026-08-28"),
          L("CCC", "CLOSED", "2026-01-02"), L("DDD", "PENDING", "2026-08-29")]

    t = dst.tom_tat(ds)
    assert t["tong"] == 4
    assert t["theo_trang_thai"] == {"CLOSED": 2, "OPEN": 1, "PENDING": 1}
    assert {x.symbol for x in t["chua_dong"]} == {"BBB", "DDD"}

    v = dst.tien_ve_truoc(ds, "2026-08-28")
    assert v["tong"] == 3, "loc theo signal_date >= moc"
    assert {x.symbol for x in v["da_dong"]} == {"AAA"}
    assert {x.symbol for x in v["con_mo"]} == {"BBB", "DDD"}

    # bien: moc DUNG bang ngay tin hieu thi van tinh (>=, khong phai >)
    assert dst.tien_ve_truoc(ds, "2026-08-29")["tong"] == 1
    print("PASS  hai ham thong ke chay duoc khong can mang")
