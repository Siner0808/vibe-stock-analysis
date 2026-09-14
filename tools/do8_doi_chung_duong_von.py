"""ĐO 8 — số học đường vốn của ta so với một cài đặt ĐỘC LẬP.

Tiêu chí đọc khai TRƯỚC: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 8, commit
`207da19` lúc 11:11:03 ngày 14/09/2026, sửa ở `6d2c45f`.

CÂU HỎI
───────
`paper_metrics.compute()` dựng đường vốn bằng **cộng dồn tuần tự theo ngày
đóng**. Hai lệnh CHỒNG LẤN theo thời gian vẫn bị nhân nối tiếp, tức vốn
của lệnh sau hưởng lãi của lệnh trước — điều chưa từng xảy ra.

Bất biến 7b gọi đó là *đòn bẩy trá hình*, và dự án tới nay chỉ **cảnh báo**
bằng `avg_capital_deployed_pct`, chưa bao giờ **định lượng**.

HAI PHẦN CỦA MÉO MÓ — đừng gộp chúng
────────────────────────────────────
```
Pi(1 + w_i r_i) = 1 + Sigma w_i r_i + Sigma_{i<j} w_i w_j r_i r_j
```

| phần | là gì | bậc |
|---|---|---|
| số hạng chéo | tích thay vì tổng, với lệnh ĐỒNG THỜI | bậc hai, **dấu đi hai chiều** |
| cấp vốn | cam kết vượt 100% — tài khoản thật không cấp nổi | bậc nhất, **luôn** thổi lên |

Bản khai đầu viết *"cộng dồn luôn cho số lớn hơn"*. Số học tính tay bác
điều đó **trước khi chạy** — xem `6d2c45f`.

VÌ SAO VẾ KIA PHẢI LÀ MÃ CỦA NGƯỜI KHÁC
───────────────────────────────────────
Viết bản thứ hai của chính mình rồi so hai bên là đúng cái bẫy
*"test KIỂM LẠI CHÍNH NÓ"* trong `CLAUDE.md`: nó kiểm công thức của test,
không kiểm công thức của mã. Nên vế đối chứng là `vectorbt`, chạy trong
**một venv riêng** — xem `tools/doi_chung/ve_vectorbt.py` để biết vì sao
nó không được vào `requirements.txt`.

CHI PHÍ: KHÔNG "tắt", mà **GIỐNG HỆT hai bên**
──────────────────────────────────────────────
Đầu vào truyền sang vế kia là `Trade.net_return_pct()` — đã trừ phí sẵn.
Nên phí nằm y hệt ở cả hai vế, còn **mô hình chi phí của vectorbt thì tắt
hẳn** (`fees=0`, `slippage=0`). Đó là điều bản khai muốn: so SỐ HỌC, không
so hai mô hình chi phí khác nhau.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VE_DOI_CHUNG = GOC / "tools" / "doi_chung" / "ve_vectorbt.py"
BIEN_MOI_TRUONG = "VIBE_VENV_DOI_CHUNG"
DUNG_SAI_DUNG_CU = 1e-6      # ca 1 va 2a: so hoc thuan
DUNG_SAI_DOC = 0.5           # ca 3: diem phan tram, khai TRUOC


def _phien(i: int) -> str:
    """Ngày phiên giả, cách nhau một ngày. Chỉ dùng để sắp thứ tự."""
    return f"2026-01-{i + 1:02d}"


def dung_lenh(mau: list[tuple]) -> list:
    """Dựng `Trade` thật từ `(vao, ra, size_pct, gross_pct)`.

    Dùng `Trade` thật chứ không dựng một lớp giả: thứ đang được đo là
    `paper_metrics.compute()`, và nó đọc `net_return_pct()` của `Trade`.
    """
    from paper_trading import Trade

    ra = []
    for i, (vao, ket, size, gross) in enumerate(mau):
        gia_vao = 100.0
        ra.append(Trade(
            id=i + 1, symbol=f"L{i}", signal_date=_phien(vao),
            entry_date=_phien(vao), entry_price=gia_vao,
            exit_date=_phien(ket), exit_price=gia_vao * (1 + gross / 100),
            exit_reason="ĐO 8", stop_loss=0.0, take_profit=0.0,
            size_pct=size, entry_score=0, status="CLOSED"))
    return ra


def ve_ta(trades: list) -> float:
    """A — lợi nhuận cộng dồn theo cài đặt của DỰ ÁN."""
    import paper_metrics as pm

    p = pm.compute(trades)
    if p is None:
        raise RuntimeError("compute() tra None")
    return p.total_net_pct


def von_trien_khai(trades: list) -> tuple[float, float]:
    """C và D — vốn cam kết trung bình và đỉnh, theo cài đặt của dự án."""
    import paper_metrics as pm

    p = pm.compute(trades)
    return p.avg_capital_deployed_pct, p.peak_capital_deployed_pct


def ve_kia(trades: list, python_venv: str) -> dict:
    """B — do `vectorbt` tính, trong MỘT tiến trình và MỘT venv khác."""
    ngay = sorted({t.entry_date for t in trades} | {t.exit_date for t in trades})
    chi_so = {d: i for i, d in enumerate(ngay)}
    lenh = [{"vao": chi_so[t.entry_date], "ra": chi_so[t.exit_date],
             "size_pct": t.size_pct, "ret_pct": t.net_return_pct()}
            for t in trades]

    r = subprocess.run([python_venv, str(VE_DOI_CHUNG)],
                       input=json.dumps({"lenh": lenh}),
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"ve doi chung that bai (ma {r.returncode}): "
                           f"{r.stdout.strip() or r.stderr.strip()[:300]}")
    ra = json.loads(r.stdout)
    if "loi" in ra:
        raise RuntimeError(f"ve doi chung bao loi: {ra['loi']}")
    return ra


def so_hang_cheo(trades: list) -> float:
    """Σ_{i<j} w_i w_j r_i r_j — chênh lệch DỰ ĐOÁN được cho lệnh đồng thời.

    Hàm THUẦN, và nó là phần "tính tay" của phép kiểm dụng cụ: nó nói
    TRƯỚC khoảng cách phải bằng bao nhiêu, thay vì chỉ nói hai số khác
    nhau. Chỉ đúng khi MỌI lệnh chồng lấn hoàn toàn.
    """
    w = [t.size_pct / 100 for t in trades]
    r = [t.net_return_pct() / 100 for t in trades]
    tong = 0.0
    for i in range(len(w)):
        for j in range(i + 1, len(w)):
            tong += w[i] * w[j] * r[i] * r[j]
    return tong * 100


def doc_ket_cuc(A: float, B: float, D: float) -> list[str]:
    """Đọc theo bảng đã ký — và NÓI RA khi bảng ấy chồng điều kiện.

    Bảng ký ngày 14/09/2026 có hai ô cùng khớp khi `B > A` và `D > 100%`:

      ô 2  `|A − B| > 0,5` VÀ `D > 100%`  -> khoảng cách LÀ đòn bẩy trá hình
      ô 4  `B > A` khi `D > 100%`          -> bất ngờ, PHẢI TRUY, không nhận

    Bản đầu của hàm này kiểm ô 2 trước rồi `elif`, nên nó in ra một kết
    quả ở đúng tình huống bảng bảo **đừng nhận một kết quả**. Đó là thứ
    tự viết quyết định cách đọc, không phải điều khoản quyết định.

    Nay: in **MỌI** ô khớp, và khi có xung đột thì theo ô **thận trọng
    hơn** — ô không cho phép kết luận. Hàm THUẦN.
    """
    khop = []
    if abs(A - B) <= DUNG_SAI_DOC and D <= 100.0:
        khop.append(("1", "so hoc hai ben khop, tap lenh khong don bay"))
    if abs(A - B) > DUNG_SAI_DOC and D > 100.0:
        khop.append(("2", "khoang cach LA don bay tra hinh, nay DO DUOC"))
    if abs(A - B) > DUNG_SAI_DOC and D <= 100.0:
        khop.append(("3", "cam ket <= 100% ma van lech — TRUY, gia dinh dau "
                          "tien la LOI CUA TA"))
    if B > A and D > 100.0:
        khop.append(("4", "BAT NGO: phan cap von le ra LUON thoi A len. "
                          "PHAI TRUY, khong duoc nhan"))

    ra = ["\n   doc theo bang da ky:"]
    if not khop:
        ra.append("   -> KHONG o nao khop. Bang da ky co lo — noi ra, dung "
                  "chon bua mot o.")
        return ra
    for so, mo_ta in khop:
        ra.append(f"   -> KET CUC {so}: {mo_ta}")
    if len(khop) > 1:
        than_trong = "4" if any(s == "4" for s, _ in khop) else khop[-1][0]
        ra.append(f"   !! BANG DA KY CHONG DIEU KIEN: {len(khop)} o cung "
                  f"khop. Theo o THAN TRONG hon -> KET CUC {than_trong}.")
        ra.append("      Mot bang ket cuc chong nhau la mot lo cua ban khai, "
                  "khong phai cho de chon.")
    return ra


def _bao(ten: str, A: float, B: float, C: float, D: float) -> None:
    print(f"\n── {ten} " + "─" * max(0, 58 - len(ten)))
    print(f"   A (ta, cong don tuan tu) : {A:+9.5f}%")
    print(f"   B (vectorbt, mot ket tien): {B:+9.5f}%")
    print(f"   A - B                     : {A - B:+9.5f} diem")
    print(f"   von cam ket  TB {C:6.1f}%  ·  dinh {D:6.1f}%")


def main() -> int:
    ap = argparse.ArgumentParser(description="DO 8 — doi chung duong von")
    ap.add_argument("--python-venv", default=os.environ.get(BIEN_MOI_TRUONG),
                    help=f"python.exe cua venv co vectorbt (hoac {BIEN_MOI_TRUONG})")
    ap.add_argument("--so-that", action="store_true",
                    help="chay CA 3 tren so lenh THAT (can mang). CHI DOC.")
    ts = ap.parse_args()

    if not ts.python_venv or not Path(ts.python_venv).exists():
        print(f"CHUA KIEM DUOC — chua co venv doi chung.\n"
              f"  Dung {BIEN_MOI_TRUONG} hoac --python-venv.\n"
              f"  Cach dung: xem docstring tools/doi_chung/ve_vectorbt.py",
              file=sys.stderr)
        return 2

    print("=" * 66)
    print("DO 8 — so hoc duong von: cai dat cua ta so voi mot cai dat DOC LAP")
    print("=" * 66)

    # ── PHEP KIEM DUNG CU — doc TRUOC moi con so khac ─────────────────
    hong = []

    # CA 1: hai lenh KHONG chong lan, moi lenh 100% von.
    # Cong don tuan tu LA dung o day, nen A phai bang B.
    c1 = dung_lenh([(0, 1, 100.0, 10.0), (2, 3, 100.0, -5.0)])
    A1, B1 = ve_ta(c1), ve_kia(c1, ts.python_venv)["loi_nhuan_pct"]
    C1, D1 = von_trien_khai(c1)
    _bao("CA 1 · khong chong lan · 100% moi lenh", A1, B1, C1, D1)
    lech1 = abs(A1 - B1)
    print(f"   doi hoi: |A-B| <= {DUNG_SAI_DUNG_CU}   -> "
          f"{'DAT' if lech1 <= DUNG_SAI_DUNG_CU else 'HONG'}  ({lech1:.2e})")
    if lech1 > DUNG_SAI_DUNG_CU:
        hong.append("CA 1")

    # CA 2a: hai lenh CHONG LAN HOAN TOAN, moi lenh 50%.
    # Khoang cach phai bang DUNG so hang cheo — mot du doan dong kin,
    # manh hon "hai so khac nhau".
    c2 = dung_lenh([(0, 5, 50.0, 10.0), (0, 5, 50.0, -5.0)])
    A2, B2 = ve_ta(c2), ve_kia(c2, ts.python_venv)["loi_nhuan_pct"]
    C2, D2 = von_trien_khai(c2)
    cheo = so_hang_cheo(c2)
    _bao("CA 2a · chong lan hoan toan · 50% moi lenh", A2, B2, C2, D2)
    print(f"   so hang cheo tinh TAY      : {cheo:+9.5f} diem")
    lech2 = abs((A2 - B2) - cheo)
    print(f"   doi hoi: |(A-B) - cheo| <= {DUNG_SAI_DUNG_CU}   -> "
          f"{'DAT' if lech2 <= DUNG_SAI_DUNG_CU else 'HONG'}  ({lech2:.2e})")
    if lech2 > DUNG_SAI_DUNG_CU:
        hong.append("CA 2a")

    if hong:
        print(f"\nDUNG CU HONG o {', '.join(hong)}. "
              f"KHONG doc ca nao khac — ban khai cam dung dieu do.",
              file=sys.stderr)
        return 1
    print("\n>> DUNG CU SACH. Doc tiep duoc.")

    # ── CA 2b: cam ket 150%, tach phan CAP VON ────────────────────────
    c3 = dung_lenh([(0, 5, 50.0, 10.0), (0, 5, 50.0, 10.0),
                    (0, 5, 50.0, 10.0)])
    A3, B3 = ve_ta(c3), ve_kia(c3, ts.python_venv)["loi_nhuan_pct"]
    C3, D3 = von_trien_khai(c3)
    _bao("CA 2b · ba lenh chong lan · cam ket 150%", A3, B3, C3, D3)
    cheo3 = so_hang_cheo(c3)
    print(f"   so hang cheo tinh TAY      : {cheo3:+9.5f} diem")
    print(f"   phan CAP VON (con lai)     : {(A3 - B3) - cheo3:+9.5f} diem"
          f"   ({((A3 - B3) - cheo3) / (A3 - B3) * 100:.0f}% khoang cach)")
    print("   tai khoan that khong cap noi lenh thu ba")

    # ── CA 3: SỔ LỆNH THẬT ────────────────────────────────────────────
    if not ts.so_that:
        print("\n── CA 3 · so lenh that " + "─" * 40)
        print("   BO QUA (them --so-that de chay). Can mang + credential.")
        return 0

    print("\n── CA 3 · so lenh that " + "─" * 40)
    try:
        import doc_so_that
        ra = doc_so_that.keo_ve_so_tam(ghi=lambda *a, **k: None)
    except Exception as e:
        print(f"   CHUA KIEM DUOC — khong keo duoc so: {e}", file=sys.stderr)
        return 2
    if ra is None:
        print("   CHUA KIEM DUOC — kho ngoai chua cau hinh.", file=sys.stderr)
        return 2

    so, _ = ra
    kin = [t for t in so.all_trades()
           if t.status == "CLOSED" and t.entry_date and t.exit_date
           and t.net_return_pct() is not None]
    if not kin:
        print("   CHUA KIEM DUOC — so khong co lenh da dong nao.",
              file=sys.stderr)
        return 2

    A4 = ve_ta(kin)
    B4 = ve_kia(kin, ts.python_venv)["loi_nhuan_pct"]
    C4, D4 = von_trien_khai(kin)
    _bao(f"CA 3 · so that · {len(kin)} lenh da dong", A4, B4, C4, D4)
    print(f"   so hang cheo tinh TAY      : {so_hang_cheo(kin):+9.5f} diem"
          f"   (CHI dung khi moi lenh chong lan — o day la MOC, khong phai dap so)")
    for d in doc_ket_cuc(A4, B4, D4):
        print(d)

    # ── PHEP THU PHAN BIET: cung tap lenh, HA TY TRONG cho cam ket <= 100%
    #
    # Neu khoang cach den tu CAP VON thi ha ty trong xuong duoi tran se
    # lam no biet mat. Neu no con nguyen thi do la bat dong SO HOC, va
    # gia dinh dau tien phai la LOI CUA TA (quy tac so 1).
    if D4 > 100.0:
        he_so = 100.0 / D4
        nho = _ha_ty_trong(kin, he_so)
        A5 = ve_ta(nho)
        B5 = ve_kia(nho, ts.python_venv)["loi_nhuan_pct"]
        C5, D5 = von_trien_khai(nho)
        _bao(f"CA 3b · CUNG tap lenh, ty trong x{he_so:.4f}", A5, B5, C5, D5)
        print(f"\n   phep thu phan biet:")
        if abs(A5 - B5) <= DUNG_SAI_DOC:
            print("   -> khoang cach BIEN MAT khi cam ket <= 100%")
            print("      => no den tu CAP VON, khong phai bat dong so hoc")
        else:
            print(f"   -> khoang cach CON NGUYEN ({A5 - B5:+.5f} diem) du cam "
                  f"ket chi {D5:.1f}%")
            print("      => BAT DONG SO HOC. Gia dinh dau tien: LOI CUA TA.")
    return 0


def _ha_ty_trong(trades: list, he_so: float) -> list:
    """Cùng tập lệnh, cùng lãi/lỗ, chỉ HẠ tỷ trọng. Không đụng bản gốc."""
    import copy

    ra = []
    for t in trades:
        b = copy.copy(t)
        b.size_pct = t.size_pct * he_so
        ra.append(b)
    return ra


if __name__ == "__main__":
    raise SystemExit(main())
