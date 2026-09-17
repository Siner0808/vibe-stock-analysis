"""Đọc bảng ĐO 12 — `plotly` 6.9.0 → 7.1.0 có làm biểu đồ nói khác đi không.

VÌ SAO CÓ FILE NÀY
──────────────────
BƯỚC 95 đo trên toàn bộ quần thể gói và tìm ra `plotly` máy **6.9.0** ·
CI **7.1.0** — một khoảng cách bản **CHÍNH**, ở đúng thư viện vẽ mọi biểu
đồ. Streamlit Cloud cài từ `requirements.txt`, nên **người dùng đang xem
biểu đồ do 7.1.0 vẽ** trong khi mọi lượt kiểm ở máy này chạy trên 6.9.0.

BẢNG ĐỌC nằm ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 12, khai **trước** khi
con số so sánh đầu tiên tồn tại. File này không được mang bảng đọc thứ hai.

    A  mot ten BIEN MAT                      ->  KHONG NANG
    B  mot tu khoa bi CHOI THEM              ->  KHONG NANG
    C  trade_review NAP NO                   ->  KHONG NANG
    D1 bam DU LIEU cua trace DOI             ->  KHONG NANG
    D2 bam HINH + CHU THICH DOI              ->  KHONG NANG
    E  bam phan con lai cua layout DOI       ->  GHI RA, khong phan
       tat ca giong het                      ->  NANG DUOC
       khong dung duoc figure                ->  CHUA KET LUAN DUOC

DỮ LIỆU VÀ TRANG TRÍ LÀ HAI CÂU HỎI KHÁC NHAU
─────────────────────────────────────────────
Một phép nâng bản CHÍNH gần như chắc chắn đổi vài mặc định trình bày. Một
bảng đọc chỉ hỏi *"đặc tả có giống hệt không"* thì đã tự định sẵn câu trả
lời `KHÔNG NÂNG`, và một lời tiên tri không thể sai thì vô dụng.

Nhưng **D2 không phải trang trí**: đường cắt lỗ là một `add_hline` nằm
trong `layout.shapes`, và nó mang một con số người đọc hành động theo. Xếp
nó chung với màu nền là đúng cái lỗi `TP1 chỉ-để-hiện` (lỗi 78).

VÌ SAO ĐO `build_figure` CHỨ KHÔNG DỰNG LẠI BIỂU ĐỒ CỦA `app.py`
────────────────────────────────────────────────────────────────
`trade_review.build_figure()` là hàm **thuần** và là **mã đang giao**.
Biểu đồ thứ hai nằm trong thân script Streamlit của `app.py` nên không
gọi rời được — và dựng lại nó ở đây sẽ là *test kiểm lại chính nó*, lỗi
đã mắc ba lần ngày 31/08/2026. Với biểu đồ ấy, ĐO 12 chỉ đọc được ô A và
ô B: các tên và từ khoá nó dùng còn sống hay không.
"""
import argparse
import ast
import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.stdout.reconfigure(encoding="utf-8")

#: Ký trong `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 12.
SO_PHIEN = 90
GIA_GOC = 20.0                      # nghìn đồng, như vnstock trả
MODUN_NAP = ("trade_review",)
BO_QUA = {".venv", "scratch", "node_modules", ".git", "backtest"}

CO = "CO"
THIEU = "THIEU"
CHUA_KIEM = "CHUA KIEM"

NANG_DUOC = "NANG DUOC"
KHONG_NANG = "KHONG NANG"
CHUA_KET_LUAN = "CHUA KET LUAN DUOC"

TEN_ANH = "vibe_do12_plotly.json"


def duong_anh() -> Path:
    return Path(tempfile.gettempdir()) / TEN_ANH


# ── phần ĐỌC REPO: thuần ────────────────────────────────────────────────
def _trong_repo(p: Path) -> bool:
    """Lọc theo đường TƯƠNG ĐỐI — repo nằm dưới một thư mục tên `scratch`."""
    return not any(x in p.relative_to(GOC).parts for x in BO_QUA)


def _bi_danh(cay: ast.AST) -> tuple[str | None, set[str]]:
    """(bí danh của `plotly.graph_objects`, tên nhập thẳng từ plotly)."""
    bi = None
    thang: set[str] = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "plotly.graph_objects":
                    bi = a.asname or "plotly"
        elif isinstance(n, ast.ImportFrom) and (n.module or "").startswith("plotly"):
            for a in n.names:
                thang.add(a.asname or a.name)
    return bi, thang


def be_mat(goc: Path = GOC) -> tuple[dict, dict, int]:
    """Quét repo bằng AST. Trả (tên -> file, tên -> từ khoá, số file quét).

    Tên dạng `go.Candlestick` viết là `graph_objects.Candlestick`; tên nhập
    thẳng như `make_subplots` giữ nguyên.
    """
    ten: dict[str, set[str]] = {}
    khoa: dict[str, set[str]] = {}
    quet = 0
    for p in sorted(goc.rglob("*.py")):
        if not _trong_repo(p):
            continue
        quet += 1
        try:
            cay = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        bi, thang = _bi_danh(cay)
        if bi is None and not thang:
            continue
        for n in ast.walk(cay):
            goi = n.func if isinstance(n, ast.Call) else None
            if bi and isinstance(n, ast.Attribute) and \
                    isinstance(n.value, ast.Name) and n.value.id == bi:
                ten.setdefault(f"graph_objects.{n.attr}", set()).add(p.name)
            if isinstance(n, ast.Name) and n.id in thang:
                ten.setdefault(n.id, set()).add(p.name)
            if goi is None:
                continue
            duong = None
            if bi and isinstance(goi, ast.Attribute) and \
                    isinstance(goi.value, ast.Name) and goi.value.id == bi:
                duong = f"graph_objects.{goi.attr}"
            elif isinstance(goi, ast.Name) and goi.id in thang:
                duong = goi.id
            if duong is None:
                continue
            for kw in n.keywords:
                khoa.setdefault(duong, set()).add(kw.arg if kw.arg else "**")
    return ({k: sorted(v) for k, v in ten.items()},
            {k: sorted(v) for k, v in khoa.items()},
            quet)


# ── phần CHẠM plotly ────────────────────────────────────────────────────
def _tra(duong: str):
    """Đi theo đường. Trả (trạng thái, đối tượng hoặc lý do)."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    goc_ten = {"graph_objects": go, "make_subplots": make_subplots}
    phan = duong.split(".")
    o = goc_ten.get(phan[0])
    if o is None:
        return THIEU, f"khong co goc {phan[0]}"
    for k in phan[1:]:
        try:
            o = getattr(o, k)
        except AttributeError:
            return THIEU, f"khong co .{k}"
        except Exception as e:                # bia-ok: khong tra duoc, khong doan
            return CHUA_KIEM, f"{type(e).__name__}: {e}"
    return CO, o


def do_ten(ten: dict) -> dict:
    return {d: _tra(d)[0] for d in sorted(ten)}


def do_khoa(khoa: dict) -> dict:
    """Mỗi (tên, từ khoá) -> NHAN / CHOI / CHUA KIEM."""
    ra = {}
    for duong in sorted(khoa):
        tt, o = _tra(duong)
        if tt != CO or not callable(o):
            for k in khoa[duong]:
                ra[f"{duong}({k})"] = CHUA_KIEM
            continue
        try:
            sig = inspect.signature(o)
        except (ValueError, TypeError):        # bia-ok: khong doc duoc chu ky
            for k in khoa[duong]:
                ra[f"{duong}({k})"] = CHUA_KIEM
            continue
        co_var = any(t.kind is inspect.Parameter.VAR_KEYWORD
                     for t in sig.parameters.values())
        for k in khoa[duong]:
            if k == "**":
                ra[f"{duong}({k})"] = CHUA_KIEM
            elif co_var or k in sig.parameters:
                ra[f"{duong}({k})"] = "NHAN"
            else:
                ra[f"{duong}({k})"] = "CHOI"
    return ra


def do_nap() -> dict:
    ra = {}
    for m in MODUN_NAP:
        kq = subprocess.run([sys.executable, "-c", f"import {m}"],
                            cwd=str(GOC), capture_output=True, text=True,
                            timeout=180)
        ra[m] = {"ma": kq.returncode,
                 "loi": (kq.stderr or "").strip().splitlines()[-1:] or [""]}
    return ra


# ── đầu vào CỐ ĐỊNH: công thức đóng, không ngẫu nhiên, không cache ──────
@dataclass(frozen=True)
class LenhGia:
    """Đúng các trường `build_figure` đọc — không hơn, không kém."""
    signal_date: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float


def bang_gia_co_dinh():
    """Bảng giá sinh bằng công thức đóng — cùng đầu vào ở cả hai lượt."""
    import math
    import pandas as pd
    ngay = pd.bdate_range("2024-01-02", periods=SO_PHIEN).strftime("%Y-%m-%d")
    dong = []
    for i, d in enumerate(ngay):
        nen = GIA_GOC + 2.0 * math.sin(i / 7.0) + i * 0.01
        dong.append({
            "time": d,
            "open": round(nen, 2),
            "high": round(nen + 0.45, 2),
            "low": round(nen - 0.40, 2),
            "close": round(nen + 0.15 * math.cos(i / 5.0), 2),
            "volume": 100_000 + i * 137,
        })
    return pd.DataFrame(dong)


def lenh_co_dinh(df) -> LenhGia:
    t = df["time"].astype(str)
    return LenhGia(
        signal_date=t.iloc[60], entry_date=t.iloc[61], exit_date=t.iloc[75],
        entry_price=21_500.0, exit_price=22_300.0,
        stop_loss=20_100.0, take_profit=23_800.0)


def _bam(o) -> str:
    return hashlib.sha256(
        json.dumps(o, sort_keys=True, ensure_ascii=False,
                   default=str).encode("utf-8")).hexdigest()


DU_LIEU_TRACE = ("x", "y", "open", "high", "low", "close", "text")


def do_figure() -> dict:
    """D — dựng biểu đồ THẬT rồi tách DỮ LIỆU khỏi TRANG TRÍ."""
    import trade_review
    df = bang_gia_co_dinh()
    fig = trade_review.build_figure(df, lenh_co_dinh(df))

    trace = []
    for tr in fig.data:
        d = {"loai": tr.type, "ten": tr.name}
        for k in DU_LIEU_TRACE:
            v = getattr(tr, k, None)
            if v is not None:
                d[k] = [str(z) for z in v]
        trace.append(d)

    lay = fig.layout.to_plotly_json()
    hinh = {"shapes": lay.pop("shapes", ()), "annotations": lay.pop("annotations", ())}

    return {
        "so_trace": len(trace),
        "so_hinh": len(hinh["shapes"]),
        "so_chu_thich": len(hinh["annotations"]),
        "D1": _bam(trace),
        "D2": _bam(hinh),
        "E": _bam(lay),
    }


def chup() -> dict:
    import plotly
    ten, khoa, quet = be_mat()
    assert quet > 100, f"quet chi {quet} file — may do hep hon thu no do"
    assert ten, "quet ra 0 ten plotly — may do dang mu"
    return {
        "ban": plotly.__version__,
        "quet_file": quet,
        "A": do_ten(ten),
        "B": do_khoa(khoa),
        "C": do_nap(),
        "D": do_figure(),
    }


# ── phần PHÁN: thuần, đục thử được không cần plotly ─────────────────────
def phan_xu(truoc: dict | None, sau: dict | None) -> tuple[str, list[str], list[str]]:
    """So hai lượt chụp. Trả (phán quyết, lý do CHẶN, ghi chú KHÔNG chặn)."""
    if not truoc or not sau:
        return CHUA_KET_LUAN, ["thiếu một trong hai lượt chụp"], []
    if not truoc.get("D") or not sau.get("D"):
        return CHUA_KET_LUAN, ["một lượt không dựng được figure"], []

    xau: list[str] = []
    for k, v in truoc["A"].items():
        if v == CO and sau["A"].get(k) == THIEU:
            xau.append(f"A: {k} biến mất")
    for k, v in truoc["B"].items():
        if v == "NHAN" and sau["B"].get(k) == "CHOI":
            xau.append(f"B: {k} bị chối")
    for m, v in truoc["C"].items():
        if v["ma"] == 0 and sau["C"].get(m, {}).get("ma") != 0:
            xau.append(f"C: {m} nạp nổ")
    if truoc["D"]["D1"] != sau["D"]["D1"]:
        xau.append("D1: DỮ LIỆU của trace đổi")
    if truoc["D"]["D2"] != sau["D"]["D2"]:
        xau.append("D2: HÌNH và CHÚ THÍCH đổi")

    ghi_chu: list[str] = []
    if truoc["D"]["E"] != sau["D"]["E"]:
        ghi_chu.append("E: phần còn lại của layout đổi — ĐỌC, không chặn")

    if xau:
        return KHONG_NANG, xau, ghi_chu
    return NANG_DUOC, [], ghi_chu


def _dem(d: dict, gia_tri: str) -> int:
    return sum(1 for v in d.values() if v == gia_tri)


def _in_luot(nhan: str, a: dict) -> None:
    print(f"  {nhan:<6} plotly {a['ban']}  ·  quét {a['quet_file']} file")
    print(f"         A  {_dem(a['A'], CO)} có · {_dem(a['A'], THIEU)} thiếu"
          f" · {_dem(a['A'], CHUA_KIEM)} chưa kiểm")
    print(f"         B  {_dem(a['B'], 'NHAN')} nhận · {_dem(a['B'], 'CHOI')} chối"
          f" · {_dem(a['B'], CHUA_KIEM)} chưa kiểm")
    xanh = sum(1 for v in a["C"].values() if v["ma"] == 0)
    print(f"         C  {xanh}/{len(a['C'])} module nạp được")
    d = a["D"]
    print(f"         D  {d['so_trace']} trace · {d['so_hinh']} hình · "
          f"{d['so_chu_thich']} chú thích")
    print(f"            D1 {d['D1'][:16]}  D2 {d['D2'][:16]}  E {d['E'][:16]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--luot", choices=("truoc", "sau"))
    ap.add_argument("--so", action="store_true")
    ns = ap.parse_args()

    anh = duong_anh()
    kho = json.loads(anh.read_text(encoding="utf-8")) if anh.exists() else {}

    if ns.luot:
        kho[ns.luot] = chup()
        anh.write_text(json.dumps(kho, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"ĐO 12 — lượt {ns.luot}")
        _in_luot(ns.luot, kho[ns.luot])
        print(f"\nảnh: {anh}")
        return 0

    if not ns.so:
        ap.print_help()
        return 2

    print("ĐO 12 — plotly, so hai lượt\n")
    for nhan in ("truoc", "sau"):
        if nhan in kho:
            _in_luot(nhan, kho[nhan])
        else:
            print(f"  {nhan:<6} (chưa chụp)")
    tt, xau, ghi_chu = phan_xu(kho.get("truoc"), kho.get("sau"))
    print(f"\nPHAN QUYET: {tt}")
    for d in xau:
        print(f"  CHẶN  {d}")
    for d in ghi_chu:
        print(f"  đọc   {d}")
    return {NANG_DUOC: 0, KHONG_NANG: 1, CHUA_KET_LUAN: 2}[tt]


if __name__ == "__main__":
    raise SystemExit(main())
