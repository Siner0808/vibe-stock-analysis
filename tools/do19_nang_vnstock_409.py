"""Đọc bảng ĐO 19 — `vnai` 2.6.1 → 2.6.2 rồi `vnstock` 4.0.8 → 4.0.9, MỘT GÓI MỘT CHẶNG.

VÌ SAO CÓ FILE NÀY
──────────────────
Tối 25/09/2026 PyPI cách ly `vnstock` và `vnai`, và người dùng chốt tạm ngừng
mọi mã nhập hai gói (`docs/STATE.md` BƯỚC 122). Chiều 26/09 hãng phát hành
`vnstock` 4.0.9 và `vnai` 2.6.2 trên kho riêng (`vnstocks.com/api/simple`);
CHANGELOG mục *Security* thừa nhận bản cũ ghi khối lệnh vào file luật toàn cục
của trợ lý AI mỗi lần `import vnstock`. PyPI vẫn cách ly. Người dùng chốt:
*"Nâng, qua một ĐO"*.

Phép nâng này hỏi đúng ba câu của ĐO 17 — con số có đổi không (A–D), ô D
ngày 29/09 còn đọc được không (E), hai công tắc 18/09 còn giữ không (F) — và
thêm MỘT câu riêng của bản vá bảo mật:

    G  mot tien trinh MOI chay `import vnstock` co GHI gi khong:
       ba dich toan cuc + AGENTS.md cua repo + cau hinh agent cua vnai

G chạy TRƯỚC mọi ô khác trong một ảnh chụp, để ô F (`import vnstock_data`)
không chạm đĩa trước nó.

HAI CHẶNG, KHÔNG PHẢI MỘT LƯỢT (ĐO 13 điều 5)
─────────────────────────────────────────────
    truoc  --nang vnai-->  sau_vnai  --nang vnstock-->  sau_vnstock

`vnai` đi trước: `vnstock` 4.0.9 chỉ gọi móc lúc import khi `vnai` đã là bản
không ghi (nó dò `vnai.beam.agent_bootstrap`), nên thứ tự ngược lại là một
tổ hợp không ai định chạy.

BẢNG ĐỌC nằm ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 19, khai **trước** khi con
số đầu tiên tồn tại. File này không mang bảng đọc thứ hai: phần A–F là
`do17_nang_goi_vnstock.phan_xu`, nguyên vẹn; file này chỉ thêm G và phép
kiểm bản đã cài.
"""
import argparse
import hashlib
import importlib.metadata as md
import json
import subprocess
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))
sys.stdout.reconfigure(encoding="utf-8")

import do17_nang_goi_vnstock as d17  # noqa: E402

#: Ký trong `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 19. Đổi một giá trị ở đây là đổi
#: tiêu chí sau khi thấy số.
GOI_NANG = ("vnai", "vnstock")
BAN_DICH = {"vnai": "2.6.2", "vnstock": "4.0.9"}

NANG_DUOC = d17.NANG_DUOC
KHONG_NANG = d17.KHONG_NANG
CHUA_KET_LUAN = d17.CHUA_KET_LUAN
HOAN = d17.HOAN


def chang_truoc(goi: str) -> str:
    """Nhãn ảnh chụp mà chặng `goi` so với: chặng NGAY TRƯỚC nó."""
    i = GOI_NANG.index(goi)
    return "truoc" if i == 0 else f"sau_{GOI_NANG[i - 1]}"


def duong_anh(nhan: str) -> Path:
    return Path(tempfile.gettempdir()) / f"vibe_do19_{nhan}.json"


def dich_g() -> tuple[Path, ...]:
    """Mọi file `import vnstock` từng ghi hoặc có thể ghi (BƯỚC 91 · 103)."""
    h = Path.home()
    return d17.dich_toan_cuc() + (GOC / "AGENTS.md",
                                  h / ".vnstock" / "config" / "agent.json")


# ══ phần THUẦN ══════════════════════════════════════════════════════════
def g_dat(g) -> tuple[bool, str]:
    """Ô G: một tiến trình mới `import vnstock` mã thoát 0 và KHÔNG đổi file nào."""
    if not isinstance(g, dict) or "loi" in g:
        return False, f"G doc HONG: {g.get('loi') if isinstance(g, dict) else g}"
    if g.get("import_ma_thoat") != 0:
        return False, f"`import vnstock` ma thoat {g.get('import_ma_thoat')}"
    truoc, sau = g.get("bam_truoc") or {}, g.get("bam_sau") or {}
    if len(truoc) != len(dich_g()) or set(truoc) != set(sau):
        return False, f"G bam {len(truoc)}/{len(dich_g())} dich"
    doi = sorted(k for k in truoc if truoc[k] != sau[k])
    if doi:
        return False, f"`import vnstock` DOI {doi}"
    return True, f"`import vnstock` ma thoat 0 · {len(truoc)} dich dung yen"


def phan_xu(truoc: dict, sau: dict, goi: str) -> tuple[str, list[str]]:
    """Bảng ĐO 17 cho A–F, rồi G, rồi bản đã cài phải đúng bản đã ký."""
    ma, ly_do = d17.phan_xu(truoc, sau, goi, goi_nang=GOI_NANG)
    if ma == CHUA_KET_LUAN:
        return ma, ly_do
    ban = (sau.get("ban") or {}).get(goi)
    if ban != BAN_DICH.get(goi):
        return CHUA_KET_LUAN, [f"ban da cai {goi}={ban}, khong phai {BAN_DICH.get(goi)} da ky"]
    ok, cau = g_dat(truoc.get("G"))
    if not ok:
        return CHUA_KET_LUAN, [f"nen G TRUOC khong dat: {cau}"]
    ok, cau = g_dat(sau.get("G"))
    if not ok:
        return KHONG_NANG, [f"G SAU: {cau}"] + ly_do
    return ma, ly_do + [cau]


# ══ phần CHẠM MÁY ═══════════════════════════════════════════════════════
def _bam_g() -> dict:
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "VANG"
            for p in dich_g()}


def do_G() -> dict:
    """Tiến trình MỚI — tiến trình gọi hàm không phân biệt được ghi đĩa với
    đổi trong bộ nhớ (BƯỚC 104)."""
    try:
        truoc = _bam_g()
        r = subprocess.run([sys.executable, "-c", "import vnstock"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=str(GOC), timeout=300)
        sau = _bam_g()
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return {"loi": f"{type(e).__name__}: {e}"}
    return {"import_ma_thoat": r.returncode, "bam_truoc": truoc, "bam_sau": sau,
            "stderr_cuoi": r.stderr[-600:]}


def _ban() -> dict:
    ra = {}
    for g in ("vnai", "vnii", "vnstock", "vnstock_data"):
        try:
            ra[g] = md.version(g)
        except md.PackageNotFoundError:
            ra[g] = None
    return ra


def chup(ma_e) -> dict:
    g = do_G()                                # TRUOC moi o khac
    d = d17.chup(ma_e)
    d["ban"] = _ban()
    d["G"] = g
    return d


def _in(nhan: str, d: dict) -> None:
    d17._in(nhan, d)
    g = d["G"]
    ok, cau = g_dat(g)
    print(f"  G    : {'DAT' if ok else 'KHONG DAT'} — {cau}")
    for p, h in (g.get("bam_truoc") or {}).items():
        h2 = (g.get("bam_sau") or {}).get(p)
        print(f"        {h[:12]} -> {str(h2)[:12]}  {p}")
    for dong in (g.get("stderr_cuoi") or "").strip().splitlines()[-6:]:
        print(f"        ! {dong[:110]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Doc bang DO 19 — mot goi mot chang.")
    ap.add_argument("che_do", choices=["truoc", "sau"],
                    help="`truoc` chup nen; `sau <goi>` chup sau khi nang goi ay roi SO")
    ap.add_argument("goi", nargs="?", choices=GOI_NANG)
    a = ap.parse_args()

    if a.che_do == "truoc":
        d = chup(None)
        duong_anh("truoc").write_text(json.dumps(d, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        _in("ANH CHUP TRUOC", d)
        print(f"\nda luu: {duong_anh('truoc')}")
        return 0

    if not a.goi:
        print("`sau` can ten goi cua chang: " + " -> ".join(GOI_NANG))
        return 2
    nhan_a = chang_truoc(a.goi)
    try:
        truoc = json.loads(duong_anh(nhan_a).read_text(encoding="utf-8"))
    except OSError:
        print(f"CHUA CO anh `{nhan_a}` o {duong_anh(nhan_a)} — chay chang truoc da.")
        return 2
    if nhan_a != "truoc" and truoc.get("phan_quyet") != NANG_DUOC:
        print(f"chang `{nhan_a}` ra {truoc.get('phan_quyet')!r}, khong phai NANG DUOC — DUNG.")
        return 2
    d = chup(truoc["E"].get("ma"))
    ma, ly_do = phan_xu(truoc, d, a.goi)
    d["phan_quyet"], d["ly_do"] = ma, ly_do
    duong_anh(f"sau_{a.goi}").write_text(json.dumps(d, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    _in(nhan_a.upper(), truoc)
    _in(f"SAU_{a.goi.upper()}", d)
    print(f"\nCHANG {a.goi}: {nhan_a} -> sau_{a.goi}\nLY DO:")
    for x in ly_do:
        print(f"  - {x}")
    print(f"\nPHAN QUYET: {ma}")
    print(f"luu: {duong_anh(f'sau_{a.goi}')}")
    return {NANG_DUOC: 0, CHUA_KET_LUAN: 2}.get(ma, 1)


if __name__ == "__main__":
    raise SystemExit(main())
