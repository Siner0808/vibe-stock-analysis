"""Gác: ĐƯỜNG GIAO DỊCH không được đọc TradingView thật.

VÌ SAO CÓ FILE NÀY
──────────────────
`tv_recommendation` **không tái lập** — bất biến 2. Đo gốc (`docs/STATE.md`
BƯỚC 8, mục *"Chưa đo"*): hai lượt chạy cách nhau chưa tới một giờ, thị
trường ĐÃ ĐÓNG, MSR đổi `STRONG_BUY` → `NEUTRAL`, điểm B **75 → 67**.

Tám điểm. Trên thang 0–100 với ngưỡng mua **62**. Nếu đại lượng ấy vào
được đường giao dịch thì cùng một phiên, cùng một gói dữ liệu, chấm hai
lần cho ra hai tập lệnh khác nhau — và không ai biết, vì cả hai đều trông
hợp lệ.

LỜI KHAI CŨ YẾU HƠN SỰ THẬT
───────────────────────────
Tài liệu ghi *"hiện vô hại vì bonus không đổi quyết định mã nào"*. Đó là
một câu **thực nghiệm, n=1** — nó đúng hôm ấy và có thể sai ngày mai.

Sự thật mạnh hơn, đọc được bằng AST (15/09/2026): **đường giao dịch không
thể chạm tới TradingView thật.**

    paper_runner._analyze   tv_recommendation="NEUTRAL"  ghim cung
    backtest/engine.py      tv_recommendation="NEUTRAL"  ghim cung
    collect_and_handoff()   chi duoc goi tu master_agent.run_full_analysis

`paper_runner` CÓ khởi tạo `DataOrchestrator`, nhưng chỉ để gọi
`_compute_local_indicators` — hàm thuần trên dataframe, không chạm mạng.

CÁI GÁC NÀY CANH MỘT THAY ĐỔI TƯƠNG LAI, KHÔNG CANH MỘT LỖI HÔM NAY
───────────────────────────────────────────────────────────────────
Hôm nay nó bắt **0 ca** — đúng như gác INDEX ở BƯỚC 72. Thứ nó canh là một
thay đổi nghe rất hợp lý: *"dùng TradingView thật trong lượt quét đi, dữ
liệu tốt hơn mà"*. Thay đổi ấy sẽ **không** làm test nào đỏ, **không** làm
số xấu đi ngay, và sẽ lặng lẽ đưa một đại lượng không tái lập vào đúng chỗ
sinh ra lệnh.

Chỗ nó VẪN sống: `master_agent.run_full_analysis()` — đường phân tích một
mã trên app, thứ người đọc rồi tự quyết. Ở đó bất biến 2 vẫn bị vi phạm và
gác này KHÔNG đụng tới, có chủ đích: đó là đường không sinh lệnh.
"""
import ast
import subprocess
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Những module nằm trên đường SINH RA LỆNH. Ghim tập này lại: thu nó xuống
#: là bỏ gác mà không sửa một dòng logic nào.
DUONG_GIAO_DICH = (
    "paper_runner.py",
    "backtest/engine.py",
    "run_daily.py",
    "walkforward.py",
)

#: Lời gọi mở đường mạng tới TradingView.
CUA_MANG = "collect_and_handoff"


def _cay(duong: str) -> ast.Module:
    f = GOC / duong
    assert f.exists(), f"{duong} khong con ton tai — sua DUONG_GIAO_DICH"
    return ast.parse(f.read_text(encoding="utf-8"))


def gan_tv(cay: ast.Module) -> list[ast.keyword]:
    """Mọi `tv_recommendation=<gì đó>` truyền theo TÊN.

    Đọc bằng AST chứ không bằng `in`: chuỗi `tv_recommendation` nằm đầy
    trong chú thích của chính các file này (lỗi 38).
    """
    return [n for n in ast.walk(cay)
            if isinstance(n, ast.keyword) and n.arg == "tv_recommendation"]


def goi_cua_mang(cay: ast.Module) -> list[int]:
    return [n.lineno for n in ast.walk(cay)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == CUA_MANG]


# ───────────────────────────── phép kiểm ─────────────────────────────

def test_DUONG_GIAO_DICH_khong_goi_cua_mang_TradingView():
    """`collect_and_handoff()` là lời gọi mạng. Nó không được xuất hiện
    trên bất kỳ module nào sinh ra lệnh."""
    lot = {d: goi_cua_mang(_cay(d)) for d in DUONG_GIAO_DICH}
    lot = {d: v for d, v in lot.items() if v}
    assert not lot, (
        f"duong giao dich goi {CUA_MANG}(): {lot}\n"
        f"Do la loi goi mang toi TradingView, va tv_recommendation KHONG "
        f"TAI LAP (bat bien 2): mot buoc doi = 8 diem tren thang co nguong "
        f"62. Cung mot phien, cham hai lan, ra hai tap lenh khac nhau.")
    print(f"PASS  {len(DUONG_GIAO_DICH)} module deu khong goi {CUA_MANG}()")


def test_moi_lan_TRUYEN_tv_recommendation_deu_la_HANG_SO():
    """Ghim cứng `"NEUTRAL"` là thứ giữ đường giao dịch tất định.

    Đổi nó thành một biến hay một lời gọi là mở đúng cánh cửa trên, chỉ
    khác hình dạng.
    """
    xau = []
    for d in DUONG_GIAO_DICH:
        for kw in gan_tv(_cay(d)):
            if not isinstance(kw.value, ast.Constant):
                xau.append(f"{d}:{kw.lineno} -> {type(kw.value).__name__}")
    assert not xau, (
        f"tv_recommendation duoc truyen bang thu KHONG phai hang so: {xau}\n"
        f"Duong giao dich phai tat dinh; mot gia tri lay luc chay thi khong.")
    print("PASS  moi lan truyen tv_recommendation deu la hang so")


def test_MAY_DO_tu_chung_minh_no_DOC_DUOC__khong_kiem_mot_tap_rong():
    """Không có phép kiểm này thì hai phép trên xanh cả khi AST đọc hụt.

    Một lỗi gõ trong tên keyword cho ra danh sách rỗng, và rỗng thì mọi
    `assert not` đều qua. Đục thử đi qua ĐÚNG hàm đang phán.
    """
    co = {d: len(gan_tv(_cay(d))) for d in DUONG_GIAO_DICH}
    assert sum(co.values()) >= 2, (
        f"chi doc duoc {co} — may do dang hong hoac hai cho ghim cung da bi "
        f"go. Ca hai kha nang deu phai DO.")
    assert co["paper_runner.py"] >= 1 and co["backtest/engine.py"] >= 1, co
    print(f"PASS  doc duoc {sum(co.values())} cho truyen tv_recommendation")


def test_HAI_CHIEU__may_do_phai_TU_CHOI_mot_gia_tri_lay_luc_chay():
    """Bài học lỗi 34: gác chỉ chạy trên dữ liệu SẠCH thì mọi phép nới nó
    đều sống sót. Thử trên nguồn dựng tay, cả hai chiều."""
    sach = ast.parse('P(tv_recommendation="NEUTRAL")')
    ban = ast.parse("P(tv_recommendation=tv['recommendation'])")
    assert all(isinstance(k.value, ast.Constant) for k in gan_tv(sach))
    assert not any(isinstance(k.value, ast.Constant) for k in gan_tv(ban))

    assert goi_cua_mang(ast.parse("x = o.collect_and_handoff()")) == [1]
    assert goi_cua_mang(ast.parse("x = o._compute_local_indicators(df)")) == []
    print("PASS  may do phan biet hang so voi gia tri lay luc chay")


def test_TAP_DUONG_GIAO_DICH_khong_duoc_thu_hep_am_tham():
    """Rút danh sách xuống còn một file là bỏ gác mà không sửa logic.

    Mọi tên trong đó phải là file GIT BIẾT — một cái tên git không biết là
    một lời hứa về thành phần không có.
    """
    assert set(DUONG_GIAO_DICH) == {
        "paper_runner.py", "backtest/engine.py",
        "run_daily.py", "walkforward.py",
    }, "tap duong giao dich bi doi — go mot muc phai CO CHU DICH"

    r = subprocess.run(["git", "ls-files"], cwd=str(GOC),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    biet = set(r.stdout.split())
    thieu = [d for d in DUONG_GIAO_DICH if d not in biet]
    assert not thieu, f"git khong biet: {thieu}"
    print("PASS  tap duong giao dich nguyen ven va git deu biet")
