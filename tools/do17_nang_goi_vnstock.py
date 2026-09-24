"""Đọc bảng ĐO 17 — nâng ba gói `vnai` · `vnii` · `vnstock_data`, MỘT GÓI MỘT CHẶNG.

VÌ SAO CÓ FILE NÀY
──────────────────
Người dùng giao 24/09/2026: *cài đầy đủ các gói vnstock, lấy bản mới thay
bản cũ*. Hỏi máy chủ thì ba gói có bản mới:

    vnai          2.6.0 -> 2.6.1   (PyPI; CI da chay 2.6.1 tu sang 24/09)
    vnii          0.2.5 -> 0.2.6   (/api/packages cong khai)
    vnstock_data  3.3.0 -> 3.3.1   (/api/vnstock/packages/list, co xac thuc)

Ba gói này KHÔNG giống ĐO 10–13 ở một chỗ: ngày **29/09/2026** có một
phép kiểm point-in-time đã ký (ĐO 14 ô D) — kéo lại khối ngoại FPT qua
chính `vnstock_data` rồi so băm với bản chụp 22/09. Bản chụp ấy chụp trên
3.3.0. Nếu 3.3.1 đổi cách XUẤT dữ liệu thì băm 29/09 sẽ khác vì THƯ VIỆN
đổi, không vì NGUỒN sửa lại — và bảng đọc của ô D không có ô cho khả năng
ấy. Nên phép nâng này phải trả lời hai câu, không phải một:

    1. con so du an dang dung co doi khong           (o A B C D, muon ĐO 10)
    2. o D ngay 29/09 con doc duoc tren ban moi khong (o E)
    va mot cau thu ba rieng cua vnai:
    3. hai cong tac nguoi dung tat 18/09 con giu khong (o F)

BA CHẶNG, KHÔNG PHẢI MỘT LƯỢT
─────────────────────────────
Bản nháp đầu nâng cả ba trong một lượt. `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 13
điều 5 đã cấm đúng hình dạng ấy: *"gộp hai phép nâng vào một lượt là đúng
cái lỗi `--stride 1`"* — một khác biệt quan sát được không quy được cho gói
nào. Nên:

    truoc  --nang vnai-->          sau_vnai  --nang vnii-->  sau_vnii
           --nang vnstock_data-->  sau_vnstock_data

Mỗi chặng so với chặng NGAY TRƯỚC, và freeze phải đổi ĐÚNG MỘT dòng — dòng
của gói chặng ấy. Chặng nào không ra `NANG DUOC` thì lùi gói ấy và DỪNG.

BẢNG ĐỌC nằm ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 17, khai **trước** khi
con số đầu tiên tồn tại. File này không được mang một bảng đọc thứ hai.

    CHUA KET LUAN DUOC  keo HONG · freeze doi KHAC dung goi cua chang ·
                        nen F truoc hong
    KHONG NANG          A khac mot o · B doi tap cot · C doi so ky/tap cot ·
                        D doi · F sau khong dat
    HOAN                o E: mot phia khong tu khop, hoac cu != moi
                        -> lui goi nay, nang lai sau khi doc xong o D 29/09
    NANG DUOC           con lai

Ô E KHÔNG đọc sớm ô D: nó kéo **các mã NGOÀI rổ khối ngoại** (không mã nào
có trong bản chụp 22/09), cùng cửa sổ, cùng lời gọi `goi_thu` của ĐO 14,
và chỉ so bản CŨ với bản MỚI trong cùng một buổi — không so với gì của
ngày 22/09.
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

import do10_nang_vnstock as d10  # noqa: E402
import do14_kha_thi_khoi_ngoai as d14  # noqa: E402

#: Ký trong `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 17. Đổi một giá trị ở đây là
#: đổi tiêu chí sau khi thấy số.
GOI_NANG = ("vnai", "vnii", "vnstock_data")
TU, DEN = "2025-01-02", "2025-06-30"          # dung cua so o D cua ĐO 14
UNG_VIEN = ("HAH", "GMD", "VHC", "REE", "DGC", "DGW")   # NGOAI ro khoi ngoai
SO_MA_E = 3
SO_LUOT_E = 2
DONG_TOI_THIEU = 100
SO_DICH_AGENT = 4

#: Chung một lời gọi với ô D — lấy thẳng từ ĐO 14, không viết lại.
goi_thu = d14.goi_thu

NANG_DUOC = "NANG DUOC"
KHONG_NANG = "KHONG NANG"
CHUA_KET_LUAN = "CHUA KET LUAN DUOC"
HOAN = "HOAN — lui goi nay toi khi doc xong o D 29/09"

MOC_F = "@@F@@"


def chang_truoc(goi: str) -> str:
    """Nhãn ảnh chụp mà chặng `goi` so với: chặng NGAY TRƯỚC nó."""
    i = GOI_NANG.index(goi)
    return "truoc" if i == 0 else f"sau_{GOI_NANG[i - 1]}"


def duong_anh(nhan: str) -> Path:
    return Path(tempfile.gettempdir()) / f"vibe_do17_{nhan}.json"


def dich_toan_cuc() -> tuple[Path, ...]:
    """Ba đích toàn cục vnai từng ghi đè (BƯỚC 91)."""
    h = Path.home()
    return (h / ".claude" / "CLAUDE.md", h / ".gemini" / "GEMINI.md",
            h / ".codex" / "AGENTS.md")


# ══ phần THUẦN — thứ phan_xu đứng trên ═════════════════════════════════
def _ten_goi(dong: str) -> str:
    """Tên chuẩn hoá của một dòng `pip freeze` — cả hai dạng `==` và ` @ `."""
    ten = dong.split(" @ ")[0].split("==")[0].strip()
    return ten.lower().replace("-", "_")


def goi_doi(truoc: list[str], sau: list[str]) -> set[str]:
    """Tên mọi gói có dòng freeze khác nhau, kể cả thêm hoặc mất."""
    a = {_ten_goi(x): x.strip() for x in truoc if x.strip()}
    b = {_ten_goi(x): x.strip() for x in sau if x.strip()}
    return {k for k in set(a) | set(b) if a.get(k) != b.get(k)}


def f_dat(f: dict) -> tuple[bool, str]:
    """Ô F: hai công tắc người dùng tắt 18/09 còn giữ, và không đích nào bị ghi."""
    if not isinstance(f, dict) or "loi" in f:
        return False, f"F doc HONG: {f.get('loi') if isinstance(f, dict) else f}"
    if f.get("import_ma_thoat") != 0:
        return False, f"`import vnstock_data` ma thoat {f.get('import_ma_thoat')}"
    if f.get("tong") != SO_DICH_AGENT:
        return False, f"so dich agent {f.get('tong')} != {SO_DICH_AGENT}"
    if f.get("bat") != 0:
        return False, f"{f.get('bat')}/{f.get('tong')} dich agent dang BAT"
    if f.get("rieng_tu") != "minimal":
        return False, f"muc rieng tu {f.get('rieng_tu')!r} != 'minimal'"
    if f.get("bam_truoc") != f.get("bam_sau"):
        return False, "mot dich toan cuc DOI sau `import vnstock_data`"
    return True, "0/4 dich bat · rieng tu minimal · 3 dich toan cuc dung yen"


def _e_thieu(e: dict) -> str:
    """Rỗng nếu ô E đủ để đọc; không thì nói vì sao."""
    if not isinstance(e, dict) or "loi" in e:
        return f"E doc HONG: {e.get('loi') if isinstance(e, dict) else e}"
    ma = e.get("ma") or []
    if len(ma) < SO_MA_E:
        return f"E chi co {len(ma)}/{SO_MA_E} ma keo duoc"
    luot = e.get("luot") or []
    if len(luot) < SO_LUOT_E:
        return f"E chi co {len(luot)}/{SO_LUOT_E} luot"
    for i, l in enumerate(luot, 1):
        for m in ma:
            o = l.get(m) or {}
            if "loi" in o or not o.get("bam"):
                return f"E luot {i} {m}: keo HONG"
            if (o.get("dong") or 0) < DONG_TOI_THIEU:
                return f"E luot {i} {m}: {o.get('dong')} dong < {DONG_TOI_THIEU}"
    return ""


def _van_tay_e(e: dict, m: str) -> set[tuple]:
    return {(l[m].get("hinh"), l[m].get("bam")) for l in e["luot"]}


def phan_xu(truoc: dict, sau: dict, goi: str) -> tuple[str, list[str]]:
    """Xếp hai ảnh chụp của MỘT chặng vào đúng MỘT ô của bảng ĐÃ KÝ.

    `goi` là gói của chặng ấy. Trả (mã, lý do)."""
    # 1. keo hong -> chua ket luan
    if d10._co_loi(truoc["do10"]) or d10._co_loi(sau["do10"]):
        return CHUA_KET_LUAN, ["o A-D co it nhat mot luot keo HONG — xem `loi`"]
    for nhan, anh in (("truoc", truoc), ("sau", sau)):
        thieu = _e_thieu(anh["E"])
        if thieu:
            return CHUA_KET_LUAN, [f"{nhan}: {thieu}"]
    if truoc["E"]["ma"] != sau["E"]["ma"]:
        return CHUA_KET_LUAN, [f"E hai luot keo KHAC ma: {truoc['E']['ma']} / {sau['E']['ma']}"]

    # 2. chang nay phai cham DUNG MOT goi — goi cua chang (ĐO 13 dieu 5)
    doi = goi_doi(truoc["freeze"], sau["freeze"])
    if goi not in GOI_NANG or doi != {goi}:
        return CHUA_KET_LUAN, [f"freeze doi {sorted(doi)}, khong phai dung ['{goi}']"]

    # 3. nen F truoc phai dat, khong thi F sau khong doc duoc
    ok, cau = f_dat(truoc["F"])
    if not ok:
        return CHUA_KET_LUAN, [f"nen F TRUOC khong dat: {cau}"]
    ok, cau = f_dat(sau["F"])
    if not ok:
        return KHONG_NANG, [f"F SAU: {cau}"]

    # 4. con so du an dang dung — A B C D
    a, b = truoc["do10"], sau["do10"]
    ly_do = []
    for m in d10.MA:
        x, y = a["A"].get(m, {}), b["A"].get(m, {})
        if x != y:
            ly_do.append(f"A[{m}] KHAC o: {sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))}")
    if a["B"].get("cot") != b["B"].get("cot"):
        ly_do.append("B doi TAP COT")
    for m in d10.MA:
        x, y = a["C"].get(m, {}), b["C"].get(m, {})
        if x.get("dong") != y.get("dong"):
            ly_do.append(f"C[{m}] doi SO KY {x.get('dong')} -> {y.get('dong')}")
        if x.get("cot") != y.get("cot"):
            ly_do.append(f"C[{m}] doi TAP COT")
    if a["D"] != b["D"]:
        ly_do.append("D (kiem_goi) doi")
    if ly_do:
        return KHONG_NANG, ly_do

    # 5. o E — o D 29/09 con doc duoc khong
    ma = truoc["E"]["ma"]
    for nhan, anh in (("truoc", truoc), ("sau", sau)):
        for m in ma:
            if len(_van_tay_e(anh["E"], m)) != 1:
                ly_do.append(f"E {nhan} {m}: {SO_LUOT_E} luot CUNG ban cho ket qua KHAC nhau")
    if ly_do:
        return HOAN, ly_do
    for m in ma:
        if _van_tay_e(truoc["E"], m) != _van_tay_e(sau["E"], m):
            ly_do.append(f"E {m}: ban cu va ban moi cho bang KHAC nhau")
    if ly_do:
        return HOAN, ly_do

    return NANG_DUOC, [f"freeze doi dung {goi} · F giu · A giong het · B,C giu so ky va "
                       "tap cot · D giu · E giong het tung byte, cu == moi"]


# ══ phần CHẠM MẠNG / MÁY ═══════════════════════════════════════════════
def _freeze() -> list[str]:
    r = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                       capture_output=True, text=True, encoding="utf-8")
    return [x for x in r.stdout.splitlines() if x.strip()]


def _ban() -> dict:
    ra = {}
    for g in GOI_NANG + ("vnstock",):
        try:
            ra[g] = md.version(g)
        except md.PackageNotFoundError:
            ra[g] = None
    return ra


def _keo_e(mkt, m: str) -> dict:
    import pandas as pd
    try:
        hinh, kq, nhat_ky = goi_thu(mkt.equity(m).foreign_flow, TU, DEN)
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return {"loi": f"{type(e).__name__}: {e}"}
    if not hinh or not isinstance(kq, pd.DataFrame) or kq.empty:
        return {"loi": "khong keo duoc", "nhat_ky": nhat_ky}
    csv = kq.to_csv(index=False)             # dung cach bam cua o D
    dong = csv.splitlines()
    return {"hinh": hinh, "dong": int(len(kq)), "cot": [str(c) for c in kq.columns],
            "bam": hashlib.sha256(csv.encode("utf-8")).hexdigest(),
            "tho": dong[:3] + dong[-1:]}


def do_E(ma_co_dinh: list[str] | None) -> dict:
    """`truoc`: chọn SO_MA_E mã đầu tiên của UNG_VIEN kéo được. `sau`: dùng lại đúng các mã ấy."""
    try:
        import vnstock_data as vd
        mkt = vd.Market()
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return {"loi": f"import vnstock_data: {type(e).__name__}: {e}"}
    luot1, chon = {}, []
    ung = ma_co_dinh if ma_co_dinh else UNG_VIEN
    for m in ung:
        o = _keo_e(mkt, m)
        luot1[m] = o
        if ma_co_dinh or ("loi" not in o and o["dong"] >= DONG_TOI_THIEU):
            chon.append(m)
        if len(chon) >= SO_MA_E:
            break
    luot = [luot1] + [{m: _keo_e(mkt, m) for m in chon} for _ in range(SO_LUOT_E - 1)]
    return {"ma": chon, "da_thu": list(luot1), "luot": luot}


_MA_F = f"""
import json, sys
import vnai
from vnai.beam import agents
a = agents.agent_status()
t = vnai.telemetry_status()
bat = sum(1 for v in a.get("targets", {{}}).values() if v.get("enabled"))
print("{MOC_F}" + json.dumps({{"bat": bat, "tong": len(a.get("targets", {{}})),
      "cong_tac_chung": a.get("enabled"), "rieng_tu": t.get("privacy_level")}}))
"""


def _bam_dich() -> dict:
    ra = {}
    for p in dich_toan_cuc():
        ra[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "VANG"
    return ra


def do_F() -> dict:
    """Mỗi phép đọc là một TIẾN TRÌNH MỚI — tiến trình gọi hàm không phân biệt được
    *đã ghi đĩa* với *chỉ đổi trong bộ nhớ* (BƯỚC 104)."""
    try:
        bam_truoc = _bam_dich()
        r1 = subprocess.run([sys.executable, "-c", "import vnstock_data"],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", cwd=str(GOC), timeout=300)
        bam_sau = _bam_dich()
        r2 = subprocess.run([sys.executable, "-c", _MA_F], capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            cwd=str(GOC), timeout=300)
        dong = [x for x in r2.stdout.splitlines() if x.startswith(MOC_F)]
        if not dong:
            return {"loi": f"khong doc duoc trang thai: {r2.stderr[-300:]}"}
        ra = json.loads(dong[-1][len(MOC_F):])
    except Exception as e:                    # bia-ok: ghi LOI, khong thay so
        return {"loi": f"{type(e).__name__}: {e}"}
    ra.update({"import_ma_thoat": r1.returncode, "import_loi": r1.stderr[-300:],
               "bam_truoc": bam_truoc, "bam_sau": bam_sau})
    return ra


def chup(ma_e: list[str] | None) -> dict:
    return {"ban": _ban(), "freeze": _freeze(), "F": do_F(),
            "do10": d10.chup(), "E": do_E(ma_e)}


def _in(nhan: str, d: dict) -> None:
    print(f"\n{'=' * 64}\n{nhan}  {d['ban']}\n{'=' * 64}")
    d10._in("  A-D", d["do10"])
    f = d["F"]
    if "loi" in f:
        print(f"  F    : LOI {f['loi'][:120]}")
    else:
        doi = sum(f["bam_truoc"][k] != f["bam_sau"][k] for k in f["bam_truoc"])
        print(f"  F    : import ma thoat {f['import_ma_thoat']} · {f['bat']}/{f['tong']} dich bat"
              f" · rieng tu {f['rieng_tu']} · dich toan cuc doi {doi}/3")
    e = d["E"]
    if "loi" in e:
        print(f"  E    : LOI {e['loi'][:120]}")
        return
    print(f"  E    : da thu {e['da_thu']} · chon {e['ma']}")
    for i, l in enumerate(e["luot"], 1):
        for m in e["ma"]:
            o = l.get(m, {})
            if "loi" in o:
                print(f"  E l{i} {m}: LOI {o['loi'][:100]}")
                continue
            print(f"  E l{i} {m}: {o['hinh']} · {o['dong']} dong · {len(o['cot'])} cot · bam {o['bam'][:16]}")
            if i == 1:
                for x in o["tho"]:
                    print(f"        | {x[:110]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Doc bang DO 17 — mot goi mot chang.")
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
