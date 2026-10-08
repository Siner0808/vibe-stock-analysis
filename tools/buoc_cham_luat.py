"""Một BƯỚC có đổi LUẬT hay không — máy phán bằng LỊCH SỬ GIT, không bằng lời khai.

VÌ SAO CÓ FILE NÀY (BƯỚC 164, 08/10/2026)
──────────────────────────────────────────
Quy tắc 3 cũ: MỖI BƯỚC đều phải hỏi sổ tay NotebookLM (người dùng chốt
18/09/2026). Quy tắc 3 mới, người dùng đồng ý ngày 08/10/2026 (nguyên văn trả
lời: *"Đồng ý"* cho câu *"Giảm phần việc quy trình: soát tự động mỗi tuần, chỉ
hỏi NotebookLM cho những BƯỚC đổi kết luận đo hoặc đổi luật"*):

    một BƯỚC PHẢI hỏi thật khi nó ĐỔI MỘT LUẬT hoặc ĐỔI MỘT KẾT LUẬN ĐO;
    BƯỚC khác không bắt buộc, nhưng phải KHAI vì sao không hỏi.

Nếu chỉ tin lời khai thì "không đổi luật" thành ô thoát mới — đúng hình dạng
lỗi 86 (sáu lượt liên tiếp viện lý do thật mà vẫn bỏ qua). Nên máy phải TỰ PHÁN
được vế "có đổi luật không", từ thứ không nằm trong tay người khai: lịch sử git.

CÁCH PHÁN
─────────
1. Tìm commit ĐƯA `## BƯỚC n` vào `docs/STATE.md`, đi theo CHA ĐẦU
   (`git log --first-parent -G…`): squash cho commit gộp; `--merge` cho commit
   gộp mà diff so với cha đầu chính là cả PR.
2. Danh sách file đổi của commit ấy mà chạm `FILE_LUAT` → BẮT BUỘC hỏi thật.
3. BƯỚC CHƯA VÀO nhánh gốc (còn trên nhánh PR, hoặc chưa commit): file đổi =
   cây làm việc so với điểm tách khỏi nhánh gốc, cộng file chưa theo dõi. Cùng
   câu trả lời ở máy lẫn CI (CI checkout merge-ref: điểm tách chính là `main`).

REPO NÔNG THÌ ĐỎ, không xanh im — cùng `tests/test_tien_dang_ky_git.py`:
`actions/checkout` mặc định `fetch-depth: 1` không có lịch sử; CI đặt `0`.

NÓ KHÔNG PHÁN ĐƯỢC GÌ — khai thẳng
──────────────────────────────────
Chỉ thấy FILE, không thấy NGHĨA. Một BƯỚC chỉ sửa `docs/STATE.md` mà viết một
kết luận đo MỚI (không có file luật nào đổi theo) thì máy khai nó "không chạm
luật". Hai tầng đỡ: (1) mọi ĐO ký trước đều thêm mục vào
`docs/TIEU-CHI-DOC-TRUOC.md` (một file luật); (2) mọi ngưỡng gác bằng test phải
xuất hiện kề tên trong `CLAUDE.md` (`tests/test_tai_lieu_khop_hang_so.py`). Phần
còn lại là kỷ luật, và lượt soát định kỳ đọc các ô `khong_bat_buoc_vi`.

Dùng:

    ./.venv/Scripts/python.exe tools/buoc_cham_luat.py 164
    ./.venv/Scripts/python.exe tools/buoc_cham_luat.py --tu 130 --den 163
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

from moc_lo_trinh import TEP_STATE, TU_BUOC  # noqa: E402

#: File mà đổi một dòng trong đó là đổi LUẬT hoặc KẾT LUẬN ĐO của dự án.
#: Danh sách do leader đề xuất 08/10/2026 và được ghi ở docs/LO-TRINH.md; thêm
#: vào đây là siết, bớt đi là nới — nên một test ghim đúng tập này.
FILE_LUAT: tuple[str, ...] = (
    "CLAUDE.md",
    "NGUYEN-TAC-DO-LUONG.md",
    "MO-XE-KIEN-TRUC.md",
    ".claude/skills/quy-trinh-lam-viec/SKILL.md",
    "docs/TIEU-CHI-DOC-TRUOC.md",
    "docs/LO-TRINH.md",
)

#: Nhánh gốc, theo thứ tự thử. Không thấy cái nào thì NỔ — không đoán.
NHANH_GOC: tuple[str, ...] = ("origin/main", "main")

#: Neo lịch sử: `main` lúc giao BƯỚC 164 (PR #209, hợp nhất BƯỚC 163). Mọi BƯỚC
#: >= `moc_lo_trinh.TU_BUOC` được đưa vào SAU commit này, nên tìm tiêu đề chỉ
#: cần đi `NEO_LICH_SU..HEAD`. Đo 08/10/2026: tìm không neo tốn ~2 giây một
#: BƯỚC (pickaxe trên `docs/STATE.md` 1,2 MB qua cả lịch sử) — nhân với số BƯỚC
#: sau 164 thì bộ test chậm dần vô hạn; có neo thì chỉ trả tiền cho phần mới.
NEO_LICH_SU = "0a991e1"


class LoiLichSu(RuntimeError):
    """Không đọc được lịch sử git đủ để phán — phải ĐỎ, không phải xanh."""


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "log.showSignature=false", "-c",
                        "core.quotepath=false", *args], cwd=str(repo),
                       capture_output=True)
    if r.returncode != 0:
        raise LoiLichSu(f"git {' '.join(args)}: "
                        f"{r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "replace")


def kiem_khong_nong(repo: Path) -> None:
    if _git(repo, "rev-parse", "--is-shallow-repository").strip() != "false":
        raise LoiLichSu("repo NONG (shallow): lich su bi cat, may khong phan duoc "
                        "BUOC nao doi luat — CI phai checkout voi fetch-depth: 0")


def nhanh_goc(repo: Path, ung_vien: tuple[str, ...] = NHANH_GOC) -> str:
    for ref in ung_vien:
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                            f"{ref}^{{commit}}"], cwd=str(repo), capture_output=True)
        if r.returncode == 0:
            return ref
    raise LoiLichSu(f"khong thay nhanh goc nao trong {ung_vien} — khong co moc de "
                    f"phan BUOC da vao nhanh chinh hay chua")


def commit_dua_buoc_vao(repo: Path, n: int,
                        tep_state: tuple[str, ...] = TEP_STATE,
                        neo: str | None = None) -> str | None:
    """Commit CŨ NHẤT trên đường cha-đầu của HEAD mà diff (so với cha đầu) đụng
    dòng tiêu đề `## BƯỚC n `. None nếu chưa commit nào chứa nó.

    `-G` (diff có dòng khớp) chứ không `-S` (đếm số lần): `-S` với chuỗi
    `## BƯỚC 16` khớp cả tiêu đề cấp ba `### BƯỚC 16`. Dấu cách cuối mẫu để
    `BƯỚC 16` không khớp `BƯỚC 164`. Lấy cái CŨ NHẤT vì một lần sửa tiêu đề về
    sau cũng khớp `-G`.

    `neo` (xem `NEO_LICH_SU`) giới hạn khoảng tìm `neo..HEAD`. Neo không phải
    tổ tiên của HEAD (repo nông, nhánh lạ) thì NỔ chứ không tìm tay không.
    """
    khoang = []
    if neo is not None:
        if not _la_to_tien(repo, neo, "HEAD"):
            raise LoiLichSu(f"neo {neo} khong phai to tien cua HEAD — khong "
                            f"gioi han duoc khoang tim")
        khoang = [f"{neo}..HEAD"]
    ra = _git(repo, "log", "--first-parent", "--format=%H",
              f"-G^## BƯỚC {n} ", *khoang, "--", *tep_state).split()
    return ra[-1] if ra else None


def _la_to_tien(repo: Path, a: str, b: str) -> bool:
    r = subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                       cwd=str(repo), capture_output=True)
    if r.returncode not in (0, 1):
        raise LoiLichSu(f"git merge-base --is-ancestor {a} {b}: "
                        f"{r.stderr.decode('utf-8', 'replace').strip()}")
    return r.returncode == 0


def _tach_nul(s: str) -> list[str]:
    return [x for x in s.split("\0") if x]


def file_cua_buoc(repo: Path, n: int, goc: str | None = None,
                  tep_state: tuple[str, ...] = TEP_STATE,
                  neo: str | None = None) -> tuple[list[str], str]:
    """(file đổi của BƯỚC n, mô tả NGUỒN của câu trả lời)."""
    kiem_khong_nong(repo)
    goc = goc or nhanh_goc(repo)
    c = commit_dua_buoc_vao(repo, n, tep_state, neo)
    if c is not None and _la_to_tien(repo, c, goc):
        cha = _git(repo, "rev-list", "--parents", "-n", "1", c).split()[1:]
        if cha:
            files = _tach_nul(_git(repo, "diff", "--name-only", "-z", cha[0], c))
        else:
            files = _tach_nul(_git(repo, "show", "--name-only", "-z",
                                   "--format=", c))
        return sorted(files), f"da vao {goc}: commit {c[:7]} so voi cha dau"
    diem_tach = _git(repo, "merge-base", "HEAD", goc).strip()
    da_theo_doi = _tach_nul(_git(repo, "diff", "--name-only", "-z", diem_tach))
    chua_theo_doi = _tach_nul(_git(repo, "ls-files", "--others",
                                   "--exclude-standard", "-z"))
    return (sorted(set(da_theo_doi) | set(chua_theo_doi)),
            f"CHUA vao {goc}: cay lam viec so voi diem tach {diem_tach[:7]}")


def file_luat_bi_cham(files) -> list[str]:
    """Phần giao của `files` với `FILE_LUAT`. HÀM THUẦN — chỗ phán duy nhất."""
    luat = set(FILE_LUAT)
    return sorted(f for f in files if f in luat)


def buoc_cham_luat(repo: Path, n: int, goc: str | None = None,
                   neo: str | None = None) -> tuple[bool, list[str], str]:
    """(có chạm luật?, các file luật bị chạm, nguồn câu trả lời)."""
    files, nguon = file_cua_buoc(repo, n, goc, neo=neo)
    cham = file_luat_bi_cham(files)
    return bool(cham), cham, nguon


#: Lý do `khong_bat_buoc_vi` ngắn hơn ngần này ký tự là câu thần chú — cùng ngưỡng
#: với `khong_soat_vi` (`tests/test_soat_notebooklm.py::test_LY_DO_KHONG_SOAT_…`).
#: Bản đầu còn một danh sách "lý do mơ hồ" (`khong can`, `n/a`, `-`…) kiểm RIÊNG;
#: đột biến (BƯỚC 164, phát P14) cho thấy nó là mã CHẾT: mọi phần tử đều ngắn hơn
#: 25 ký tự nên phép kiểm độ dài đã bắt hết, bỏ nó đi không ca nào đổi. Gỡ thay
#: vì thêm một ca giả (`tests/test_buoc_cham_luat.py::test_LY_DO_mo_ho_ngan_…`).
LY_DO_TOI_THIEU = 25
#: Ba ô còn lại mà một mục `khong_bat_buoc_vi` KHÔNG được mang cùng: nói "không
#: hỏi" và "đã hỏi" trong một dòng là nói nước đôi.
O_XUNG_DOT = ("cau_hoi", "phat_hien", "khong_tim_thay_gi", "khong_soat_vi")


def loi_khong_bat_buoc(ten: str, muc: dict, cham: list[str]) -> list[str]:
    """Lỗi của MỘT mục khai `khong_bat_buoc_vi` (rỗng = hợp lệ). HÀM THUẦN.

    `cham` = các file luật mà BƯỚC ấy đã chạm (từ `file_luat_bi_cham`). Đây là
    chỗ phán DUY NHẤT của luật "ô mới chỉ hợp lệ khi máy xác nhận BƯỚC không chạm
    file luật" — test và `tools/so_tay.py ghi` cùng gọi nó.
    """
    ly_do = muc.get("khong_bat_buoc_vi")
    if not isinstance(ly_do, str):
        return [f"{ten}: `khong_bat_buoc_vi` phai la chuoi"]
    ra: list[str] = []
    if cham:
        ra.append(f"{ten}: BUOC nay CHAM file luat {cham} — phai HOI THAT so tay; "
                  f"o `khong_bat_buoc_vi` khong duoc nhan")
    ly = ly_do.strip()
    if len(ly) < LY_DO_TOI_THIEU:
        ra.append(f"{ten}: ly do khong-bat-buoc qua ngan ({len(ly)} ky tu) — {ly!r}")
    dung = [k for k in O_XUNG_DOT if k in muc]
    if dung:
        ra.append(f"{ten}: vua khai `khong_bat_buoc_vi` vua mang {dung} — noi nuoc doi")
    return ra


def ly_do_trung(so: dict) -> list[str]:
    """Các `khong_bat_buoc_vi` dùng CHUNG một lý do (chuẩn hoá khoảng trắng, hoa/thường).

    Một lý do dán lại cho nhiều BƯỚC là câu thần chú (lỗi 86). Máy không đọc
    được lý do có thật không; nó đọc được lý do có bị DÁN LẠI không.
    """
    thay: dict[str, str] = {}
    ra: list[str] = []
    for ten, d in so.items():
        if not isinstance(d, dict) or not isinstance(d.get("khong_bat_buoc_vi"), str):
            continue
        k = " ".join(d["khong_bat_buoc_vi"].split()).lower()
        if k in thay:
            ra.append(f"{ten} dung lai ly do cua {thay[k]}")
        else:
            thay[k] = ten
    return ra


def so_buoc(ten: str) -> int | None:
    """`BƯỚC 164` -> 164; `BƯỚC 70-73` (mục gộp) -> 70, số ĐẦU; tên khác (`ĐO 5`) -> None."""
    m = re.fullmatch(r"BƯỚC (\d+)(?:-\d+)?", ten.strip())
    return int(m.group(1)) if m else None


def loi_o_khong_bat_buoc(soat: dict, moc: int, file_cua) -> list[str]:
    """Lỗi của MỌI mục `khong_bat_buoc_vi` trong `soat` (rỗng = sạch). HÀM THUẦN.

    `file_cua(n) -> [file đổi của BƯỚC n]` được TIÊM vào: gác thật truyền máy đọc
    git, test truyền bản giả. Mục có ô này ở BƯỚC < `moc` (hoặc không phải BƯỚC)
    là lỗi: luật thu hẹp chỉ có hiệu lực từ `moc`, và lùi nó về BƯỚC cũ là viết
    lại lịch sử.
    """
    ra: list[str] = []
    for ten, d in soat.items():
        if not isinstance(d, dict) or "khong_bat_buoc_vi" not in d:
            continue
        n = so_buoc(ten)
        if n is None or n < moc:
            ra.append(f"{ten}: o `khong_bat_buoc_vi` chi hop le cho BUOC >= {moc}")
            continue
        ra += loi_khong_bat_buoc(ten, d, file_luat_bi_cham(file_cua(n)))
    return ra + ly_do_trung(soat)


def co_phan_quyet_that(muc: dict) -> bool:
    """Mục sổ tay có ít nhất một phát hiện mà `phan_quyet` mở đầu bằng THẬT."""
    return any(str(p.get("phan_quyet", "")).strip().upper().startswith("THẬT")
               for p in muc.get("phat_hien") or [])


def bang_doi_chieu(cham: dict[int, bool], so: dict) -> dict[str, list[int]]:
    """Chéo hai thứ máy đọc được: BƯỚC có chạm luật không × sổ tay có tìm ra
    điều THẬT không. HÀM THUẦN. Dùng để ĐO một luật nới trước khi nhận nó.

    Khoá trả về là bốn ô của bảng 2×2; chỉ tính BƯỚC có trong `cham` VÀ có
    `cau_hoi` trong sổ (BƯỚC đã HỎI THẬT — chưa hỏi thì không có kết quả để chéo).
    """
    ra: dict[str, list[int]] = {"cham_that": [], "cham_khong_that": [],
                                "khong_cham_that": [], "khong_cham_khong_that": []}
    for n, c in sorted(cham.items()):
        d = so.get(f"BƯỚC {n}")
        if not isinstance(d, dict) or not str(d.get("cau_hoi") or "").strip():
            continue
        ra[("cham" if c else "khong_cham") + ("_that" if co_phan_quyet_that(d)
                                              else "_khong_that")].append(n)
    return ra


def main(argv: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("buoc", nargs="*", type=int)
    ap.add_argument("--tu", type=int)
    ap.add_argument("--den", type=int)
    ap.add_argument("--doi-chieu", action="store_true",
                    help="in bang 2x2: BUOC cham luat x so tay co tim ra dieu THAT")
    a = ap.parse_args(argv)
    ds = list(a.buoc)
    if a.tu is not None:
        den = a.den if a.den is not None else a.tu
        ds += list(range(a.tu, den + 1))
    if not ds:
        ap.print_usage(sys.stderr)
        return 2
    ket_qua: dict[int, bool] = {}
    try:
        for n in ds:
            # BƯỚC trước TU_BUOC nằm TRƯỚC neo: tìm từ đầu lịch sử (chậm, đúng).
            neo = NEO_LICH_SU if n >= TU_BUOC else None
            if commit_dua_buoc_vao(GOC, n, neo=neo) is None and not any(
                    f"## BƯỚC {n} " in (GOC / t).read_text(encoding="utf-8")
                    for t in TEP_STATE):
                print(f"BƯỚC {n}: khong co tieu de trong {TEP_STATE}")
                continue
            cham, files, nguon = buoc_cham_luat(GOC, n, neo=neo)
            ket_qua[n] = cham
            print(f"BƯỚC {n}: {'CHAM LUAT' if cham else 'khong cham luat'}"
                  f" {files if cham else ''} [{nguon}]")
    except LoiLichSu as e:
        print(f"CHUA PHAN DUOC: {e}", file=sys.stderr)
        return 2
    if a.doi_chieu:
        import json
        so = json.loads((GOC / "docs" / "soat-notebooklm.json")
                        .read_text(encoding="utf-8"))["soat"]
        b = bang_doi_chieu(ket_qua, so)
        print(f"\nDOI CHIEU ({len(ket_qua)} BUOC phan duoc; chi tinh BUOC da HOI THAT):")
        for khoa, ds_n in b.items():
            print(f"  {khoa:24} {len(ds_n):3}  {ds_n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
