"""ĐO 13 — `urllib3` 1.26.20 → 2.8.0: dữ liệu về có đổi một ô nào không?

Tiêu chí đã ký TRƯỚC lượt chạy đầu tiên: `docs/TIEU-CHI-DOC-TRUOC.md`,
mục **ĐO 13**. Bảng đọc ở đó, không ở đây — và không sửa sau khi thấy số.

    ./.venv/Scripts/python.exe tools/do13_nang_urllib3.py truoc
    pip install urllib3==2.8.0
    ./.venv/Scripts/python.exe tools/do13_nang_urllib3.py sau

CHIỀU CỦA PHÉP NÂNG NÀY NGƯỢC VỚI BA PHÉP TRƯỚC
───────────────────────────────────────────────
`requirements.txt` không ghim `urllib3` — nó là phụ thuộc gián tiếp của
`requests` — nên CI **và Streamlit Cloud** đều lấy bản mới nhất, tức 2.8.0.
Máy local 1.26.20 là **kẻ duy nhất còn ở 1.x**. Nếu dữ liệu đổi thì kết
luận không phải *"đừng nâng máy"* mà là *"mọi con số đo ở máy này đo trên
một tầng HTTP khác tầng đang phục vụ"*, và việc phải làm là ghim
`urllib3<2` để kéo SẢN XUẤT về đúng bản đã đo.

VÌ SAO CÓ Ô D0, VÀ VÌ SAO NÓ CHẠY TRƯỚC
───────────────────────────────────────
ĐO 12 so hai `go.Figure` dựng từ một bảng giá sinh bằng công thức đóng,
nên hai lượt chắc chắn cùng đầu vào. Ở đây phải **gọi mạng**, và endpoint
có thể trả khác nhau vì lý do chẳng liên quan tới urllib3 — dự án đã gặp
đúng chuyện ấy (HT1 · TCH, một lượt kéo hỏng tạm thời).

Nên **D0 kéo hai lượt trên CÙNG một bản**. Hai lượt ấy khác nhau thì D1
không nói được gì về urllib3 — nó nói về endpoint. Bỏ D0 đi thì một khác
biệt ngẫu nhiên sẽ bị đọc thành một phán quyết về thư viện.

PHÉP BĂM DÙNG LẠI CỦA ĐO 10, KHÔNG VIẾT BẢN THỨ HAI
───────────────────────────────────────────────────
`do10_nang_vnstock._bam_bang()` đã băm trên CSV (không trên `repr`, thứ
cắt bớt khi bảng dài). Viết một phép băm thứ hai là dựng hai thước cho
cùng một đại lượng, và chúng sẽ trôi ra khỏi nhau.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))
sys.stdout.reconfigure(encoding="utf-8")

TEN_ANH = "vibe_do13_urllib3.json"

#: Khoảng ĐÃ ĐÓNG — dữ liệu quý I/2024 không còn đổi. Cùng lý do ĐO 10.
DAU, CUOI = "2024-01-02", "2024-03-29"
MA = ("VCB", "FPT", "HPG")
NGUON_GIA = "VCI"

#: Hai chỗ DUY NHẤT repo gọi `requests`, đọc bằng AST ngày 18/09/2026.
#: Gõ ra đây để ô B có thứ đối chiếu; quần thể thật thì `do_B` tự quét.
BE_MAT = (("get", ("params", "timeout")),
          ("post", ("headers", "json", "timeout")))

KHONG_NANG = "KHONG NANG"
NANG_DUOC = "NANG DUOC"
CHUA_KET_LUAN = "CHUA KET LUAN DUOC"


def duong_anh() -> Path:
    return Path(tempfile.gettempdir()) / TEN_ANH


# ══ A — nạp được không, và nạp bản nào ═════════════════════════════════
def do_A() -> dict:
    """Tiến trình RIÊNG: `import requests`, rồi hỏi urllib3 bản nào.

    Tiến trình riêng vì `import` trong chính tiến trình này đã xảy ra từ
    trước — hỏi lại chỉ đọc cache của `sys.modules`, không đo được việc
    nạp có nổ hay không.
    """
    ma = ("import requests, urllib3, json; "
          "print('KQ' + json.dumps({'urllib3': urllib3.__version__, "
          "'requests': requests.__version__}))")
    try:
        kq = subprocess.run([sys.executable, "-c", ma], capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=120)
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return {"loi": f"{type(e).__name__}: {e}"}
    if kq.returncode != 0:
        return {"nap": False, "ma_thoat": kq.returncode,
                "loi": kq.stderr.strip()[-400:]}
    for d in kq.stdout.splitlines():
        if d.startswith("KQ"):
            return {"nap": True, **json.loads(d[2:])}
    return {"nap": False, "loi": "khong doc duoc dong KQ"}


# ══ B — bề mặt repo còn nhận không ═════════════════════════════════════
def do_B() -> dict:
    """Mọi cặp (hàm, từ khoá) repo gọi, so với `inspect.signature`."""
    import requests
    ra = {}
    for ten, tu_khoa in BE_MAT:
        ham = getattr(requests, ten, None)
        if ham is None:
            ra[ten] = {"co_ham": False}
            continue
        try:
            ts = inspect.signature(ham).parameters
        except (TypeError, ValueError) as e:  # bia-ok: ghi LOI, khong thay so
            ra[ten] = {"loi": f"{type(e).__name__}: {e}"}
            continue
        co_kwargs = any(p.kind is p.VAR_KEYWORD for p in ts.values())
        ra[ten] = {
            "co_ham": True,
            "nhan": sorted(k for k in tu_khoa if k in ts or co_kwargs),
            "choi": sorted(k for k in tu_khoa if k not in ts and not co_kwargs),
        }
    return ra


# ══ C — nút thắt dữ liệu của vnstock ═══════════════════════════════════
def do_C() -> dict:
    """`send_request` là chỗ MỌI dòng OHLCV đi qua. Chữ ký còn nguyên không?"""
    try:
        from vnstock.core.utils.client import send_request
        ts = inspect.signature(send_request).parameters
        return {"co": True, "tham_so": sorted(ts)}
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return {"co": False, "loi": f"{type(e).__name__}: {e}"}


# ══ D — dữ liệu thật, khoảng đã đóng ═══════════════════════════════════
def _keo_mot_luot() -> dict:
    """Một lượt kéo OHLCV cho cả rổ. Băm bằng phép băm của ĐO 10."""
    from do10_nang_vnstock import _bam_bang
    from vnstock import Quote
    ra = {}
    for ma in MA:
        try:
            df = Quote(symbol=ma, source=NGUON_GIA).history(
                start=DAU, end=CUOI, interval="1D")
            ra[ma] = _bam_bang(df)
        except Exception as e:                # bia-ok: ghi LOI, khong thay so
            ra[ma] = {"loi": f"{type(e).__name__}: {e}"}
    return ra


def do_D() -> dict:
    """D0 (đối chứng, hai lượt cùng bản) rồi D1 (ảnh để so chéo bản)."""
    t0 = time.monotonic()
    luot1 = _keo_mot_luot()
    t1 = time.monotonic()
    luot2 = _keo_mot_luot()
    t2 = time.monotonic()
    return {
        "luot1": luot1,
        "luot2": luot2,
        "D0_dat": luot1 == luot2,
        "giay_luot1": round(t1 - t0, 2),
        "giay_luot2": round(t2 - t1, 2),
    }


# ══ phán xử — HÀM THUẦN ════════════════════════════════════════════════
def phan_xu(truoc: dict, sau: dict) -> tuple[str, list[str]]:
    """Đọc theo đúng bảng đã ký ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 13.

    HÀM THUẦN trên hai ảnh — không chạm mạng, không đọc đĩa — nên đục thử
    được từng ô mà không cần đổi gói.
    """
    ly_do: list[str] = []

    for nhan, anh in (("truoc", truoc), ("sau", sau)):
        if not anh.get("A", {}).get("nap"):
            return CHUA_KET_LUAN, [f"A: `import requests` NO o luot {nhan}"]

    for nhan, anh in (("truoc", truoc), ("sau", sau)):
        for ten, d in anh.get("B", {}).items():
            if not d.get("co_ham"):
                ly_do.append(f"B: mat ham requests.{ten} o luot {nhan}")
            elif d.get("choi"):
                ly_do.append(f"B: requests.{ten} CHOI {d['choi']} o luot {nhan}")

    if truoc.get("C", {}).get("tham_so") != sau.get("C", {}).get("tham_so"):
        ly_do.append("C: chu ky send_request DOI")
    if not sau.get("C", {}).get("co"):
        ly_do.append("C: khong nap duoc send_request o luot sau")

    # D0 quyết định D1 có đọc được không — chạy TRƯỚC mọi phép so chéo bản
    for nhan, anh in (("truoc", truoc), ("sau", sau)):
        d = anh.get("D", {})
        if not d:
            return CHUA_KET_LUAN, [f"D: khong co so lieu o luot {nhan}"]
        if not d.get("D0_dat"):
            return CHUA_KET_LUAN, [
                f"D0 KHONG DAT o luot {nhan}: hai luot keo CUNG BAN khac "
                f"nhau, nen D1 khong noi duoc gi ve urllib3"]

    if truoc["D"]["luot1"] != sau["D"]["luot1"]:
        khac = [m for m in MA
                if truoc["D"]["luot1"].get(m) != sau["D"]["luot1"].get(m)]
        ly_do.append(f"D1: bam DU LIEU doi o {khac} — ghim urllib3<2")

    if ly_do:
        return KHONG_NANG, ly_do
    return NANG_DUOC, []


def _in_anh(nhan: str, a: dict) -> None:
    A = a.get("A", {})
    print(f"\n  [{nhan}]  urllib3 {A.get('urllib3', '?')} · "
          f"requests {A.get('requests', '?')} · nap={A.get('nap')}")
    for ten, d in sorted(a.get("B", {}).items()):
        print(f"      B  requests.{ten:<5} nhan={d.get('nhan')} "
              f"choi={d.get('choi')}")
    print(f"      C  send_request tham so: {len(a.get('C', {}).get('tham_so') or [])}")
    d = a.get("D", {})
    print(f"      D0 dat={d.get('D0_dat')}  ·  E  "
          f"{d.get('giay_luot1')}s / {d.get('giay_luot2')}s")
    for ma in MA:
        o = (d.get("luot1") or {}).get(ma, {})
        print(f"      D1 {ma:<5} {o.get('dong', '-')} dong · "
              f"{str(o.get('bam'))[:16]}{'  LOI: ' + o['loi'] if o.get('loi') else ''}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("luot", choices=("truoc", "sau"))
    a = ap.parse_args()

    anh = {"A": do_A(), "B": do_B(), "C": do_C(), "D": do_D()}

    p = duong_anh()
    cu = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    cu[a.luot] = anh
    p.write_text(json.dumps(cu, ensure_ascii=False, indent=2), encoding="utf-8")

    _in_anh(a.luot, anh)

    if a.luot == "truoc":
        print(f"\n  da ghi anh `truoc` vao {p}")
        print("  buoc tiep: pip install urllib3==2.8.0  roi chay lai voi `sau`")
        return 0

    if "truoc" not in cu:
        print("\n  CHUA KET LUAN DUOC: khong co anh `truoc` de so.")
        return 2

    ma, ly_do = phan_xu(cu["truoc"], cu["sau"])
    print("\n" + "=" * 66)
    print(f"  PHAN QUYET: {ma}")
    for d in ly_do:
        print(f"      {d}")
    print("  Bang doc: docs/TIEU-CHI-DOC-TRUOC.md muc DO 13 — ky truoc luot chay.")
    return {NANG_DUOC: 0, KHONG_NANG: 1, CHUA_KET_LUAN: 2}[ma]


if __name__ == "__main__":
    raise SystemExit(main())
