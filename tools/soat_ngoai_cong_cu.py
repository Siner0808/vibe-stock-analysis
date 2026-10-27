"""Ba phép quét NGOÀI tầm `tools/soat_loi_khai_cu.py` cho lượt soát định kỳ — bản trong repo.

VÌ SAO CÓ FILE NÀY (BƯỚC 232, lỗi 191)
─────────────────────────────────────
`tools/soat_loi_khai_cu.py` cố ý hẹp: chín tài liệu, bỏ hàng bảng, bỏ `docs/STATE.md`.
Mỗi lượt soát vì thế quét thêm phần ngoài tầm — và lượt 13 (BƯỚC 213, 21/10/2026) ghi
*"63 câu ứng viên, 52 chưa dấu"* cho STATE BƯỚC 186–208 bằng một script nằm ở scratchpad
của phiên con. Script mất; lượt 14 dựng lại trên CÙNG cây `efa6a58` ra 64 · 53 và không
truy ra câu lệch. Quy tắc 2 đòi lệnh tái lập được — một lệnh nằm ngoài repo thì không.

Ba lệnh dưới là bản trong repo của ba script lượt 14 (BƯỚC 230). Chúng đọc cây bằng
`git show <cây>:<tệp>`, nên chạy lại được trên một commit cũ và cho cùng con số:

    diff <A> <B>               dòng THÊM vào *.md giữa hai cây, qua bộ lọc
    state <a> <b> [--cay C]    câu trong `docs/STATE.md` thuộc BƯỚC a..b
    hang-bang [--cay C]        hàng bảng trong TAI_LIEU mà công cụ chính cố ý bỏ

Bộ lọc là CHÍNH bộ lọc của `soat_loi_khai_cu` (`PHU_DINH`, `CO_TEN`, `DA_CO_DAU`,
`cau_nhieu_dong`) — nhập, không chép, nên hai công cụ không trôi khỏi nhau. Đổi bộ lọc
thì con số của lượt cũ đổi theo; test ghim con số lượt 14 để việc ấy lộ ra.

NÓ KHÔNG PHÁN — mỗi dòng in ra là một địa chỉ để mở, không phải kết luận rằng câu sai.
Lượt soát ghi vào `docs/soat-dinh-ky.json` LỆNH đã chạy (kèm cây), không ghi đường script.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
import soat_loi_khai_cu as s  # noqa: E402

TIEU_DE_BUOC = re.compile(r"^## BƯỚC (\d+)\b")
HUNK = re.compile(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", re.M)


class ChuaKiemDuoc(Exception):
    """Không đọc được cây (git lỗi, commit không có) — mã thoát 2, không phải 'sạch'."""


def _git(*tham_so: str) -> str:
    r = subprocess.run(["git", "-C", str(GOC), *tham_so], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise ChuaKiemDuoc(f"git {' '.join(tham_so)}: {r.stderr.strip()[:200]}")
    return r.stdout


def doc_dong(tep: str, cay: str | None) -> list[str]:
    """Các dòng của `tep` ở cây `cay` (None = thư mục làm việc)."""
    if cay is None:
        return (GOC / tep).read_text(encoding="utf-8", errors="replace").split("\n")
    return _git("show", f"{cay}:{tep}").split("\n")


def dong_them(diff_u0: str) -> set[int]:
    """Số dòng (ở cây MỚI) được thêm/sửa trong một `git diff -U0`. HÀM THUẦN."""
    ra: set[int] = set()
    for m in HUNK.finditer(diff_u0):
        dau = int(m.group(1))
        dai = int(m.group(2)) if m.group(2) is not None else 1
        ra.update(range(dau, dau + dai))
    return ra


def ung_vien(dong: list[str], chon: set[int] | None = None) -> dict[int, str]:
    """{số dòng: nguyên văn} — dòng có cụm phủ định VÀ một tên, cộng câu nhiều dòng
    (`cau_nhieu_dong`). `chon` giới hạn vào một tập dòng. Hàng bảng ĐƯỢC tính. HÀM THUẦN."""
    ra = {i: d for i, d in enumerate(dong, 1)
          if (chon is None or i in chon) and s.PHU_DINH.search(d) and s.CO_TEN.search(d)}
    for i, d in s.cau_nhieu_dong(dong):
        if chon is None or i in chon:
            ra[i] = d
    return ra


def chua_dau(ung: dict[int, str]) -> dict[int, str]:
    return {i: d for i, d in ung.items() if not any(x in d for x in s.DA_CO_DAU)}


def cong_cu_chinh_thay(tep: str, noi_dung: str) -> bool:
    """Dòng này có nằm trong tầm `soat_loi_khai_cu` không: tệp thuộc TAI_LIEU và không phải
    hàng bảng. (Câu nhiều dòng của bản lưu `docs/lich-su/` công cụ chính bỏ — tính là ngoài.)"""
    return tep in s.TAI_LIEU and not noi_dung.lstrip().startswith("|")


def buoc_cua_dong(dong: list[str]) -> list[int | None]:
    """BƯỚC chứa từng dòng (theo tiêu đề `## BƯỚC n` gần nhất phía trên). HÀM THUẦN."""
    ra: list[int | None] = []
    hien = None
    for d in dong:
        m = TIEU_DE_BUOC.match(d)
        if m:
            hien = int(m.group(1))
        ra.append(hien)
    return ra


def quet_state(dong: list[str], tu: int, den: int) -> tuple[int, dict[int, tuple[int, str]]]:
    """(số ứng viên, {số dòng: (BƯỚC, nguyên văn)} của ứng viên CHƯA DẤU) thuộc BƯỚC
    tu..den, bao gồm hai đầu. HÀM THUẦN."""
    buoc = buoc_cua_dong(dong)
    chon = {i for i, b in enumerate(buoc, 1) if b is not None and tu <= b <= den}
    ung = ung_vien(dong, chon)
    return len(ung), {i: (buoc[i - 1], d) for i, d in chua_dau(ung).items()}


def hang_bang(dong: list[str]) -> tuple[int, int]:
    """(hàng bảng khớp bộ lọc, trong đó chưa dấu). HÀM THUẦN."""
    hang = [d for d in dong if d.lstrip().startswith("|")
            and s.PHU_DINH.search(d) and s.CO_TEN.search(d)]
    return len(hang), sum(1 for d in hang if not any(x in d for x in s.DA_CO_DAU))


def quet_diff(a: str, b: str) -> dict[str, dict]:
    """Mỗi tệp .md đổi giữa hai cây: số dòng thêm, ứng viên, chưa dấu (chia trong/ngoài tầm)."""
    ra: dict[str, dict] = {}
    for tep in [t for t in _git("diff", "--name-only", a, b, "--", "*.md").split("\n") if t]:
        them = dong_them(_git("diff", "-U0", a, b, "--", tep))
        dong = doc_dong(tep, b)
        ung = ung_vien(dong, them)
        chua = chua_dau(ung)
        ra[tep] = {"them": len(them), "ung_vien": len(ung), "chua_dau": chua,
                   "ngoai": {i: d for i, d in chua.items() if not cong_cu_chinh_thay(tep, d)}}
    return ra


def main(tham_so: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    con = ap.add_subparsers(dest="lenh", required=True)
    p = con.add_parser("diff", help="dòng thêm vào *.md giữa hai cây")
    p.add_argument("a")
    p.add_argument("b")
    p = con.add_parser("state", help="câu ứng viên của STATE trong khoảng BƯỚC")
    p.add_argument("tu", type=int)
    p.add_argument("den", type=int)
    p.add_argument("--cay", default=None, help="commit (mặc định: thư mục làm việc)")
    p = con.add_parser("hang-bang", help="hàng bảng mà công cụ chính bỏ")
    p.add_argument("--cay", default=None)
    a = ap.parse_args(tham_so)

    try:
        if a.lenh == "diff":
            ra = quet_diff(a.a, a.b)
            for tep, v in ra.items():
                print(f"{tep}: +{v['them']} dòng · ứng viên {v['ung_vien']} · chưa dấu "
                      f"{len(v['chua_dau'])} · ngoài tầm công cụ chính {len(v['ngoai'])}")
            print(f"TỔNG ngoài tầm: {sum(len(v['ngoai']) for v in ra.values())} câu chưa dấu")
            for tep, v in ra.items():
                for i, d in sorted(v["ngoai"].items()):
                    print(f"  {tep}:{i}  {d.strip()[:200]}")
        elif a.lenh == "state":
            n_ung, ra = quet_state(doc_dong("docs/STATE.md", a.cay), a.tu, a.den)
            dem: dict[int, int] = {}
            for b, _ in ra.values():
                dem[b] = dem.get(b, 0) + 1
            print(f"STATE BƯỚC {a.tu}–{a.den} @ {a.cay or 'thư mục làm việc'}: {n_ung} câu ứng viên, "
                  f"{len(ra)} chưa dấu")
            print("  theo BƯỚC: " + " · ".join(f"{b}: {n}" for b, n in sorted(dem.items())))
            for i, (b, d) in sorted(ra.items()):
                print(f"  {b}  :{i}  {d.strip()[:200]}")
        else:
            tong = chua = 0
            for tep in s.TAI_LIEU:
                try:
                    n, m = hang_bang(doc_dong(tep, a.cay))
                except (ChuaKiemDuoc, FileNotFoundError):
                    continue
                if n:
                    print(f"{tep}: {n} hàng bảng khớp bộ lọc, {m} chưa dấu")
                tong, chua = tong + n, chua + m
            print(f"TỔNG {tong} hàng · {chua} chưa dấu @ {a.cay or 'thư mục làm việc'}")
    except ChuaKiemDuoc as e:
        print(f"CHƯA KIỂM ĐƯỢC — {e}", file=sys.stderr)
        return 2
    print("\nMỗi dòng là một ĐỊA CHỈ để mở, không phải phán quyết. Ghi LỆNH này (kèm cây) "
          "vào docs/soat-dinh-ky.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
