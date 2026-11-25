"""Hiệu chuẩn của bản SỬA C4 sau ĐO 37 (BƯỚC 301, ĐO 38): `kd` · `a0` · `pt` · `t1`.

Đặc tả: vibe_logs_c4sua/DAC-TA-SUA-C4.md mục 2 (A0), 3 (PT), 4 (NULL có nhớ), 5 (dòng hạt) và 7 (lát L2); khai của cả
bản sửa ở `docs/thiet-ke-c4-thi-truong-gia.md` mục 21–22. Đặc tả là nguồn duy nhất; đừng chép nó vào đây. Người dùng duyệt
đặc tả 25/11/2026: *"duyệt cả 4"*. Số ĐO của bản sửa là **38** (leader chốt; đặc tả ghi 39).

CHỈ DÒNG HẠT 1 (thật) và 9001 (thử). Mọi đường vào bộ sinh đi qua `kiem_luong` (nổ với 2…10 và mọi dòng khác). Các dòng 2–10
KHÔNG được sinh, chạy hay đọc ở đây.

BỐN VIỆC (`--viec`), mỗi việc MỘT khối trong `docs/thi-truong-gia-hieu-chuan-do38.json`, đọc MỘT lần:

  kd  đặt κ_d của NULL-M (xem THỦ TỤC KHAI dưới).
  a0  mức ngẫu nhiên của A0: N = 20.000 thị trường NULL Tầng 1, chỉ số 1.100.001–1.120.000; đếm bộ đề xuất THẬT
      (`vong_hoc_gia.de_xuat` + `chon_khai`, cửa sổ đã nhìn như `chay_vong`) khai G = `mono_volume_score` ở bao nhiêu thị
      trường. In p̂, SE, ngưỡng `binom.ppf(0,999 ; 1000 ; p̂)` (tính bằng `nhi_thuc_ppf`, không scipy) và luật DỪNG
      p̂ + 3·SE ≥ 0,3. TỪ CHỐI chạy nếu đầu ra bộ đề xuất thiếu `z` (tức trước BƯỚC 300).
  pt  dải PT: n_cal = 200 thị trường Tầng 2 mức 2×, chỉ số 1.200.001–1.200.200; chỉ chấm điểm (`G.cham_diem_theo_ma`) và
      `cx.cham` (không P2, không vòng). k = số thị trường mà G′ = `bo_momentum_score` có `trang_thai` == `QUA`; dải 99% của
      số QUA của R = 100 thị trường chính thức là Beta-nhị thức(100 ; k + ½ ; n_cal − k + ½): [k nhỏ nhất có P(X ≤ k) ≥ 0,005 ;
      k nhỏ nhất có P(X ≤ k) ≥ 0,995]. DỪNG nếu k/n_cal ngoài [0,2 ; 0,7] hoặc có dòng `data_quality` ≠ OK. Ghi thêm Δ, p
      (và z, σ hoán vị) của G = `mono_volume_score` và của cả bộ ba cho bảng 2×2.
  t1  1.000 thị trường Tầng 1 mức 2×, chỉ số 1.300.001–1.301.000, cho G và G′ (bảng 2×2 {G, G′} × {Tầng 1, Tầng 2}).

THỦ TỤC KHAI của `kd` (viết TRƯỚC mọi lượt chạy thật; chỉ thăm dò trên dòng thử 9001):
  * NULL-M = `thi_truong_gia._sinh_loi_m`: nhân tố ngành d AR(1) φ_d = 0,97; vào lợi nhuận qua κ_d · d(s−2)/21 và vào CẢ NĂM
    thành phần cùng hệ số b_d; z có κ = 0 (vẫn nằm trong volume_score như cũ).
  * b_d = `HE_SO_D` = 0,5 CỐ ĐỊNH: đúng hệ số `HE_SO_Z` đã khai cho z, KHÔNG một số mới để chọn theo kết quả.
  * Đại lượng đo: IC(điểm đã ghi) = `thi_truong_gia.ic_da_ghi_m`: hạng, gộp mọi phiên có nhãn × 60 mã, trên mẫu dài 5.000 phiên
    (`SO_PHIEN_SU_THAT`), hạt `[1, chỉ số, 301]`. Mục tiêu 0,10 (cỡ đo ở Tầng 2 mức 2×, 0,098–0,104; `thiet-ke` 19.3/19.9).
  * Lưới κ_d CỐ ĐỊNH (9 điểm): 0,012 · 0,014 · … · 0,028 (bước 0,002; thăm dò 9001 cho IC ≈ 0,10 quanh κ_d = 0,02, bước 0,002
    đổi IC cỡ 0,01). Lưới KHÔNG đổi sau khi chạy.
  * Khối chỉ số (dòng 1, chưa ai dùng — `git grep` rỗng): `1.400.001 + j·1.000 + t`, j = thứ tự điểm lưới (0–8), t = 0…49
    (khối TÌM, 50 mẫu mỗi điểm lưới); khối KIỂM ở j = 9: 100 mẫu tại κ_d đã chọn. Cao nhất 1.409.100.
  * Luật chọn: IC_j = trung bình 50 mẫu ở điểm j; chọn κ_d có |IC_j − 0,10| nhỏ nhất (hoà → κ_d nhỏ hơn). KHÔNG làm tròn,
    không nội suy.
  * THẤT BẠI (DỪNG, báo, KHÔNG chọn lại, KHÔNG đổi lưới): (a) lưới không kẹp 0,10 (min IC > 0,10 hoặc max IC < 0,10);
    (b) IC giảm theo κ_d quá 2 sai số chuẩn giữa hai điểm liền; (c) điểm gần nhất nằm ở RÌA lưới; (d) |IC_chọn − 0,10| > 0,010
    (±10% mục tiêu, như `DUNG_SAI_MUC` của Lát 2); (e) khối KIỂM: trung bình IC của 100 mẫu ngoài [0,090 ; 0,110].
  * Chỉ khi KHÔNG thất bại thì κ_d (đọc từ khối `kd`) được dùng cho thị trường NULL-M của dòng 9 (BƯỚC 302/303).

CHẠY (lệnh thật; từng việc MỘT lần, theo thứ tự kd → a0 → t1 → pt):
    ./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec kd --luong 1 --so-tien-trinh 12
    ./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec a0 --luong 1 --so-tien-trinh 12
    ./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec t1 --luong 1 --so-tien-trinh 12
    ./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec pt --luong 1 --so-tien-trinh 12
Chạy tiếp sau khi gián đoạn: ĐÚNG lệnh ấy thêm `--tiep-tuc` (chỉ khi cùng mã băm git). Đọc kết quả: `--doc`.
THỬ (dòng 9001, `--ra` bắt buộc, không bao giờ ra file chính thức): `--viec kd --luong 9001 --so 3 --ra <file>`.
Ghi log RA NGOÀI repo (cây không được bẩn khi chạy dòng 1).

Dòng 1 chỉ chạy khi: cây git SẠCH (ngoại trừ chính file kết quả); khối chưa XONG (đọc MỘT lần; dở thì chỉ `--tiep-tuc`);
`--so`/`--dau` là giá trị đã khai. Mã thoát: 0 xong · 2 lỗi đối số · 3 cửa từ chối · 4 xong nhưng LUẬT DỪNG báo (kd thất bại,
a0 p̂ + 3·SE ≥ 0,3, pt k/n_cal ngoài [0,2 ; 0,7] hay data_quality ≠ OK). Không Sheets, không `*.db`, không mạng ngoài git.
Chỉ ghi `docs/thi-truong-gia-hieu-chuan-do38.json` bằng `va_an_toan.ghi` (nguyên tử, mỗi `LUU_MOI` đơn vị).
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

for _luong_ra in (sys.stdout, sys.stderr):   # BƯỚC 129
    try:
        _luong_ra.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
DUONG_CONG_CU = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))
sys.path.append(str(DUONG_CONG_CU))

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import thi_truong_gia_tang2 as G  # noqa: E402
import va_an_toan  # noqa: E402
import vong_hoc_gia as V  # noqa: E402
from chay_vong_tang2_thi_truong_gia import noi_dong_va_gia  # noqa: E402
from hieu_chuan_thi_truong_gia import nhi_thuc_ppf  # noqa: E402

SO_DO = 38
TEN_FILE = "docs/thi-truong-gia-hieu-chuan-do38.json"
DUONG_KET_QUA = GOC / "docs" / "thi-truong-gia-hieu-chuan-do38.json"
DUONG_HIEU_CHUAN = GOC / "docs" / "thi-truong-gia-hieu-chuan.json"

# ── dòng hạt: CHỈ 1 và 9001 ──────────────────────────────────────────────────
LUONG_THAT = 1
LUONG_THU = 9001
LUONG_DUOC_PHEP = (LUONG_THAT, LUONG_THU)
TEN_VIEC = ("kd", "a0", "pt", "t1")

#: Chỉ số thị trường ĐÃ KHAI cho dòng 1 (mỗi việc một khối; không khối nào chạm khối của `hieu_chuan_thi_truong_gia.CHI_SO_GOC`,
#: dừng ở 990.000). `git grep` ở BƯỚC 301: không số nào trong 1.100.001–1.409.100 từng xuất hiện trong mã hay tài liệu.
KHAI = {"kd": {"dau": 1_400_001}, "a0": {"dau": 1_100_001, "so": 20_000},
        "pt": {"dau": 1_200_001, "so": 200}, "t1": {"dau": 1_300_001, "so": 1000}}
LUU_MOI = 12          # ghi file kết quả mỗi 12 đơn vị (một thị trường, hay một mẫu IC ở `kd`)

# ── kd ────────────────────────────────────────────────────────────────────────
KD_LUOI = (0.012, 0.014, 0.016, 0.018, 0.020, 0.022, 0.024, 0.026, 0.028)
KD_SO_TIM, KD_SO_KIEM = 50, 100
KD_BUOC_LUOI = 1000                   # chỉ số = dau + j·KD_BUOC_LUOI + t; khối KIỂM ở j = len(KD_LUOI)
KD_MUC_TIEU = 0.10
KD_DUNG_SAI = 0.10                    # tương đối: |IC − mục tiêu| ≤ 10% · mục tiêu (như DUNG_SAI_MUC của Lát 2)
KD_HE_SO_SE_DON_DIEU = 2.0
KD_SO_PHIEN = T.SO_PHIEN_SU_THAT

# ── a0 ────────────────────────────────────────────────────────────────────────
A0_R = 1000                           # R của tiêu chí A0 (số thị trường NULL chính thức)
A0_PHAN_VI = 0.999
A0_HE_SO_SE_DUNG = 3.0
A0_P_DUNG = 0.3                       # p̂ + 3·SE ≥ 0,3 → dừng: bộ sinh hay luật khai đã lệch, không phải chỉnh ngưỡng

# ── pt ────────────────────────────────────────────────────────────────────────
PT_R = 100                            # số thị trường 2× chính thức của dòng 8
PT_DAI_Q = 0.005                      # dải 99% = [phân vị 0,005 ; phân vị 0,995]
PT_TI_LE_DUNG = (0.2, 0.7)
TEN_SPEC_GP = "bo_momentum_score"     # G′ của Tầng 2 (mục 19.8 khoản 1): cố định


class CongTu(Exception):
    """Cửa từ chối. `ly_do` là DANH SÁCH mọi điều thiếu (không dừng ở điều đầu)."""

    def __init__(self, ly_do: list[str]):
        super().__init__("; ".join(ly_do))
        self.ly_do = list(ly_do)


def kiem_luong(luong) -> None:
    """Cửa DUY NHẤT tới bộ sinh: chỉ dòng hạt 1 (thật) và 9001 (thử). Nổ với 2…10, 0, âm, bool và kiểu lạ."""
    if isinstance(luong, bool) or not isinstance(luong, (int, np.integer)) or int(luong) not in LUONG_DUOC_PHEP:
        raise ValueError(
            f"hieu chuan sua C4 chi dung dong hat {LUONG_DUOC_PHEP}; nhan {luong!r}. Cac dong 2-10 danh cho lat chay "
            f"chinh thuc va chan doan — khong sinh, khong chay, khong doc o day.")


# ═════════════════════════════════════════════════════════════════════════════
# THỐNG KÊ THUẦN (không scipy: `scipy` không có trong requirements.txt)
# ═════════════════════════════════════════════════════════════════════════════

def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def betabinom_pmf(x: int, n: int, a: float, b: float) -> float:
    """P(X = x), X ~ Beta-nhị thức(n ; a ; b). Khớp `scipy.stats.betabinom.pmf(x, n, a, b)` (có test)."""
    if x < 0 or x > n:
        return 0.0
    return math.exp(math.lgamma(n + 1) - math.lgamma(x + 1) - math.lgamma(n - x + 1)
                    + _log_beta(x + a, n - x + b) - _log_beta(a, b))


def betabinom_cdf(k: int, n: int, a: float, b: float) -> float:
    if k < 0:
        return 0.0
    return min(1.0, math.fsum(betabinom_pmf(x, n, a, b) for x in range(0, min(k, n) + 1)))


def betabinom_ppf(q: float, n: int, a: float, b: float) -> int:
    """k nhỏ nhất có P(X ≤ k) ≥ q (như `scipy.stats.betabinom.ppf`)."""
    t = 0.0
    for k in range(n + 1):
        t += betabinom_pmf(k, n, a, b)
        if t >= q - 1e-12:
            return k
    return n


def dai_betabinom(k: int, n_cal: int, so_chinh_thuc: int = PT_R, q: float = PT_DAI_Q) -> dict:
    """Dải 99% của số QUA ở `so_chinh_thuc` thị trường chính thức, từ k QUA trên n_cal thị trường hiệu chuẩn:
    p ~ Beta(k + ½, n_cal − k + ½); X ~ Beta-nhị thức(so_chinh_thuc ; k + ½ ; n_cal − k + ½);
    dải = [k nhỏ nhất có P(X ≤ k) ≥ q ; k nhỏ nhất có P(X ≤ k) ≥ 1 − q]."""
    if not (0 <= k <= n_cal) or n_cal < 1:
        raise ValueError(f"k={k}, n_cal={n_cal}")
    a, b = k + 0.5, n_cal - k + 0.5
    return {"a": a, "b": b, "thap": betabinom_ppf(q, so_chinh_thuc, a, b), "cao": betabinom_ppf(1.0 - q, so_chinh_thuc, a, b)}


# ═════════════════════════════════════════════════════════════════════════════
# CỬA (git)
# ═════════════════════════════════════════════════════════════════════════════

def git_that(*doi) -> tuple[int, str]:
    """Chạy `git` ở gốc repo, trả (mã thoát, stdout). Không có git thì (127, '')."""
    try:
        r = subprocess.run(["git", *doi], cwd=str(GOC), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return r.returncode, r.stdout


def cay_ban(git=git_that) -> list[str] | None:
    """Các dòng `git status --porcelain` TRỪ file kết quả của chính dụng cụ này; `None` nếu không đọc được git."""
    rc, ra = git("status", "--porcelain")
    if rc != 0:
        return None
    ra_dong = [d for d in ra.splitlines() if d.strip()]
    return [d for d in ra_dong if d[3:].strip().strip('"').replace("\\", "/") != TEN_FILE]


def doc_ket_qua_hien_co(duong: Path = DUONG_KET_QUA) -> dict | None:
    return json.loads(Path(duong).read_text(encoding="utf-8")) if Path(duong).is_file() else None


def kiem_cong(viec: str, luong: int, dau: int, so: int | None, ra: Path, tiep_tuc: bool = False, git=git_that,
              ket_hien_co: dict | None = None) -> dict:
    """Cửa. Trả `{"sha": ..., "sach": bool}` nếu mọi điều đúng; ngược lại nổ `CongTu` với MỌI điều thiếu.

    * Dòng 1: cây git SẠCH; `--dau`/`--so` đúng giá trị đã khai (`KHAI`); file kết quả là file chính thức.
    * Dòng 9001: cây bẩn chỉ được GHI NHẬN (`sach: False`), không từ chối; `--ra` KHÔNG được là file chính thức.
    * Khối đã XONG: không bao giờ chạy lại (đọc MỘT lần). Khối đang dở: chỉ `--tiep-tuc`, và chỉ cùng mã băm git."""
    kiem_luong(luong)
    if viec not in TEN_VIEC:
        raise ValueError(f"viec phai la mot trong {TEN_VIEC}, nhan {viec!r}")
    thieu: list[str] = []
    la_chinh_thuc = Path(ra).resolve() == DUONG_KET_QUA.resolve()
    rc, head = git("rev-parse", "HEAD")
    sha = head.strip() if rc == 0 else ""
    if not sha:
        thieu.append("khong doc duoc git HEAD (khong ghi duoc ma bam cua lan chay)")
    ban = cay_ban(git)
    sach = ban == []
    if ban is None:
        thieu.append("khong doc duoc git status")
    if luong == LUONG_THAT:
        if ban:
            thieu.append(f"cay lam viec ban ({len(ban)} muc, vi du {ban[0]!r}): commit hay don truoc khi chay dong 1")
        if not la_chinh_thuc:
            thieu.append("dong 1 chi ghi ra file chinh thuc " + TEN_FILE)
        khai = KHAI[viec]
        if dau != khai["dau"] or (viec != "kd" and so != khai["so"]):
            thieu.append(f"dong 1 chay dung gia tri da khai cho '{viec}': --dau {khai['dau']}"
                         + ("" if viec == "kd" else f" --so {khai['so']}"))
    elif la_chinh_thuc:
        thieu.append("dong thu 9001 KHONG duoc ghi ra file chinh thuc")
    hien_co = ket_hien_co if ket_hien_co is not None else doc_ket_qua_hien_co(ra)
    cu = None if hien_co is None else hien_co.get("cac_viec", {}).get(viec)
    if cu is not None:
        if cu.get("trang_thai") == "XONG":
            thieu.append(f"viec '{viec}' DA xong (doc MOT lan, khong chay lai, khong ghi de)")
        elif not tiep_tuc:
            thieu.append(f"viec '{viec}' dang do: chi chay tiep voi --tiep-tuc")
        elif cu.get("luong") != luong:
            thieu.append(f"viec '{viec}' dang do o dong {cu.get('luong')}, khong phai {luong}")
        elif cu.get("git", {}).get("sha") != sha:
            thieu.append(f"viec '{viec}' dang do o ma bam {cu.get('git', {}).get('sha')} khac HEAD hien tai {sha}")
    elif tiep_tuc:
        thieu.append(f"khong co viec '{viec}' dang do de chay tiep")
    if thieu:
        raise CongTu(thieu)
    return {"sha": sha, "sach": bool(sach)}


# ═════════════════════════════════════════════════════════════════════════════
# SỔ ỨNG VIÊN GIẢ VÀ CHẤM
# ═════════════════════════════════════════════════════════════════════════════

def so_ung_vien_bo_ba_gp(khai_ngay: list[str]) -> dict:
    """Sổ GIẢ (bộ nhớ): G′ = `bo_momentum_score` · Z · H khai ở ba ngày liên tiếp `khai_ngay`; đi qua `kiem_so_ung_vien`."""
    ho = T.ho_spec_oracle()
    ten_spec = (TEN_SPEC_GP, T.TEN_SPEC_Z, T.TEN_SPEC_H)
    so = {"ung_vien": {ten: {"khai_ngay": khai_ngay[i], "mo_ta": f"hieu chuan sua C4 {ten}", "ly_do": f"hieu chuan sua C4 {ten}",
                             "qua_sang": None, "spec": ho[ten_spec[i]]} for i, ten in enumerate(("Gp", "Z", "H"))}}
    cb.kiem_so_ung_vien(so)
    return so


def tom_tat_cham(c: dict) -> dict:
    """Δ, p, z, σ hoán vị (độ lệch chuẩn của null) và trạng thái của MỘT ứng viên, từ kết quả `cx.cham_mot`."""
    ket = c.get("ket")
    if ket is None or "delta" not in c:
        raise ValueError(f"ung vien chua toi moc doc (trang thai {c.get('trang_thai')!r}): khong co delta/p")
    return {"tt": c["trang_thai"], "delta": float(c["delta"]), "p": float(c["p"]), "z": float(c["z"]),
            "sd_null": float(np.std(ket["null"])), "n_phien": int(c["n_phien"]), "n_ma": int(c["n_ma"])}


def cham_g_va_gp(dong: list[dict], gia, khai_ngay: list[str], so_hoan_vi: int = cx.SO_HOAN_VI) -> dict:
    """Chấm bộ ba (G′, Z, H) bằng `cx.cham` (K = 3, ngưỡng 0,05/3) VÀ G = `mono_volume_score` ở CHÍNH khe của G′ (cùng ngày khai,
    cùng ngưỡng K = 3) bằng `cx.cham_mot` — Z và H của hai bộ ba là một nên không chấm lại. Trả `{G, Gp, Z, H}` (`tom_tat_cham`)."""
    so = so_ung_vien_bo_ba_gp(khai_ngay)
    r = cx.cham(dong, so, V.bang_gia_gia(gia), cx.HAT_RNG, so_hoan_vi)
    a = r["nguong"]
    cg = cx.cham_mot(dong, "G", {"khai_ngay": khai_ngay[0], "spec": T.ho_spec_oracle()[T.TEN_SPEC_G]}, gia, a, cx.HAT_RNG, so_hoan_vi)
    ra = {ten: tom_tat_cham(r["chi_tiet"][ten]) for ten in ("Gp", "Z", "H")}
    ra["G"] = tom_tat_cham(cg)
    ra["nguong"] = float(a)
    return ra


def doc_kappa_2x(duong: Path = DUONG_HIEU_CHUAN) -> float:
    """κ của mức 2× MDE₈₀ đọc từ file hiệu chuẩn của Lát 2 (đọc, không ghi) — cùng κ mà ĐO 37 dùng ở cả hai tầng."""
    muc = json.loads(Path(duong).read_text(encoding="utf-8"))["muc"]
    kp = [m["kappa"] for m in muc if abs(m["he_so"] - 2.0) < 1e-9]
    if len(kp) != 1:
        raise ValueError("file hieu chuan khong co dung mot muc he_so=2.0")
    return float(kp[0])


# ═════════════════════════════════════════════════════════════════════════════
# a0: bộ đề xuất THẬT
# ═════════════════════════════════════════════════════════════════════════════

class DeXuatThieuZ(Exception):
    """Đầu ra `vong_hoc_gia.de_xuat` thiếu `z`: bộ đề xuất chuẩn hoá (BƯỚC 300) chưa nằm trong cây."""


def kiem_co_z(xep: list[dict]) -> None:
    if not xep or any(("z" not in x) or not isinstance(x["z"], (int, float)) or not math.isfinite(x["z"]) for x in xep):
        raise DeXuatThieuZ("dau ra vong_hoc_gia.de_xuat thieu 'z' (hoac khong huu han): bo de xuat chuan hoa (BUOC 300) chua co "
                           "trong cay — a0 khong chay")


def de_xuat_va_chon(dong: list[dict], gia) -> tuple[list[dict], list[dict]]:
    """Đúng cách `vong_hoc_gia.chay_vong` gọi bộ đề xuất: cửa sổ đã nhìn `min(S − 1, khai0 − 1)` cắt bằng `cat_den_phien`,
    rồi `de_xuat` và `chon_khai` THẬT (gọi qua mô-đun lúc chạy)."""
    ngay = [str(n) for n in gia.index]
    V.kiem_ngay_gia(ngay)
    khai0 = V.phien_khai(ngay, 1, T.SO_PHIEN_DA_NHIN)[0]
    cuoi_nhin = T.SO_PHIEN_DA_NHIN
    dong_nhin, gia_nhin = V.cat_den_phien(dong, gia, cuoi_nhin)
    xep = V.de_xuat(dong_nhin, gia_nhin)
    return xep, V.chon_khai(xep)


def kiem_de_xuat_co_z_truoc_khi_chay() -> None:
    """Chạy bộ đề xuất THẬT MỘT lần trên một thị trường NULL của dòng thử 9001 và nổ `DeXuatThieuZ` nếu thiếu `z`."""
    tt = T.sinh_null(LUONG_THU, 1, co_su_that=False)
    xep, _ = de_xuat_va_chon(tt.dong_quyet_dinh(), tt.gia)
    kiem_co_z(xep)


def ten_spec_f() -> list[str]:
    return sorted(T.ho_spec_f())


def don_a0(luong: int, chi_so: int) -> dict:
    kiem_luong(luong)
    tt = T.sinh_null(luong, chi_so, co_su_that=False)
    xep, chon = de_xuat_va_chon(tt.dong_quyet_dinh(), tt.gia)
    kiem_co_z(xep)
    ten = ten_spec_f()
    return {"khoa": int(chi_so), "chon": [ten.index(x["ten"]) for x in chon]}


def tong_hop_a0(ban_ghi: list[dict], ten: list[str] | None = None) -> dict:
    """p̂ = tỷ lệ thị trường mà bộ đề xuất khai G; SE = √(p̂(1−p̂)/N); ngưỡng = `binom.ppf(0,999 ; 1000 ; p̂)`.
    DỪNG (không ngưỡng) nếu p̂ + 3·SE ≥ 0,3."""
    ten = ten_spec_f() if ten is None else ten
    ig = ten.index(T.TEN_SPEC_G)
    n = len(ban_ghi)
    if n < 1:
        raise ValueError("a0: khong co thi truong nao")
    k = sum(1 for r in ban_ghi if ig in r["chon"])
    p = k / n
    se = math.sqrt(p * (1.0 - p) / n)
    dung = p + A0_HE_SO_SE_DUNG * se >= A0_P_DUNG
    dem = {t: sum(1 for r in ban_ghi if i in r["chon"]) / n for i, t in enumerate(ten)}
    return {"N": n, "k_G": k, "p_hat": p, "se": se, "R": A0_R,
            "nguong": None if dung else int(nhi_thuc_ppf(A0_PHAN_VI, A0_R, p)),
            "dung": bool(dung), "ly_do_dung": [f"p_hat + 3*SE = {p + A0_HE_SO_SE_DUNG * se:.4f} >= {A0_P_DUNG}"] if dung else [],
            "ty_le_theo_spec": dem, "so_spec_trung_binh": float(np.mean([len(r["chon"]) for r in ban_ghi]))}


# ═════════════════════════════════════════════════════════════════════════════
# pt, t1: hai tầng
# ═════════════════════════════════════════════════════════════════════════════

def don_pt(luong: int, chi_so: int, kappa: float) -> dict:
    """MỘT thị trường Tầng 2 mức 2×: sinh khung → chấm 60 mã bằng `_analyze` THẬT → G′ · Z · H và G. Không P2, không vòng."""
    kiem_luong(luong)
    tt = G.sinh_thi_truong_2(luong, chi_so, kappa)
    theo_ma = {m: G.cham_diem_theo_ma(tt, m) for m in tt.ma}
    dong, gia = noi_dong_va_gia(tt, theo_ma)
    dq = sum(1 for d in dong if d["data_quality"] != "OK")
    ra = cham_g_va_gp(dong, gia, G.dong_thoi_gian_2()["khai_ngay"])
    ra.update({"khoa": int(chi_so), "dq_khong_ok": int(dq), "so_dong": len(dong)})
    return ra


def don_t1(luong: int, chi_so: int, kappa: float) -> dict:
    """MỘT thị trường Tầng 1 mức 2×: sinh → G′ · Z · H và G."""
    kiem_luong(luong)
    tt = T.sinh_thi_truong(luong, chi_so, kappa, co_su_that=False)
    ra = cham_g_va_gp(tt.dong_quyet_dinh(), tt.gia, T.dong_thoi_gian()["khai_ngay"])
    ra.update({"khoa": int(chi_so)})
    return ra


def o_2x2(ban_ghi: list[dict], ten: str) -> dict:
    """Một ô của bảng 2×2: m = trung bình Δ, s = độ lệch chuẩn Δ (ddof = 1), σ̄ = trung bình σ hoán vị, P = tỷ lệ `QUA`."""
    d = np.asarray([r[ten]["delta"] for r in ban_ghi], float)
    sd = np.asarray([r[ten]["sd_null"] for r in ban_ghi], float)
    qua = sum(1 for r in ban_ghi if r[ten]["tt"] == "QUA")
    return {"n": int(d.size), "m": float(d.mean()), "s": float(d.std(ddof=1)) if d.size > 1 else None,
            "sigma_bar": float(sd.mean()), "QUA": int(qua), "P": qua / d.size,
            "bao_dong": int(sum(1 for r in ban_ghi if r[ten]["p"] < r["nguong"]))}


def tong_hop_pt(ban_ghi: list[dict]) -> dict:
    n = len(ban_ghi)
    k = sum(1 for r in ban_ghi if r["Gp"]["tt"] == "QUA")
    dai = dai_betabinom(k, n)
    dq = sum(r["dq_khong_ok"] for r in ban_ghi)
    ly_do = []
    if not (PT_TI_LE_DUNG[0] <= k / n <= PT_TI_LE_DUNG[1]):
        ly_do.append(f"k/n_cal = {k}/{n} = {k / n:.3f} ngoai [{PT_TI_LE_DUNG[0]} ; {PT_TI_LE_DUNG[1]}]")
    if dq:
        ly_do.append(f"{dq} dong data_quality khac OK")
    return {"n_cal": n, "k": k, "dai_99": [dai["thap"], dai["cao"]], "beta": [dai["a"], dai["b"]], "R": PT_R,
            "dung": bool(ly_do), "ly_do_dung": ly_do, "o": {t: o_2x2(ban_ghi, t) for t in ("Gp", "G", "Z", "H")}}


def tong_hop_t1(ban_ghi: list[dict]) -> dict:
    return {"n": len(ban_ghi), "dung": False, "ly_do_dung": [], "o": {t: o_2x2(ban_ghi, t) for t in ("Gp", "G", "Z", "H")}}


# ═════════════════════════════════════════════════════════════════════════════
# kd: κ_d của NULL-M
# ═════════════════════════════════════════════════════════════════════════════

def chi_so_kd(dau: int, j: int, t: int) -> int:
    if not (0 <= j <= len(KD_LUOI)) or not (0 <= t < KD_BUOC_LUOI):
        raise ValueError(f"j={j}, t={t} ngoai khoi kd")
    return dau + j * KD_BUOC_LUOI + t


def don_kd(luong: int, khoa: str, kappa_d: float, chi_so: int) -> dict:
    kiem_luong(luong)
    return {"khoa": khoa, "kappa_d": float(kappa_d), "chi_so": int(chi_so),
            "ic": float(T.ic_da_ghi_m(luong, chi_so, float(kappa_d), KD_SO_PHIEN))}


def chon_kappa_d(ic_theo_diem: dict[float, list[float]]) -> dict:
    """Luật chọn κ_d của THỦ TỤC KHAI (docstring đầu file). Hàm thuần; KHÔNG làm tròn, không nội suy."""
    luoi = sorted(ic_theo_diem)
    tb = {k: float(np.mean(ic_theo_diem[k])) for k in luoi}
    se = {k: float(np.std(ic_theo_diem[k], ddof=1) / math.sqrt(len(ic_theo_diem[k]))) if len(ic_theo_diem[k]) > 1 else float("inf")
          for k in luoi}
    ly_do: list[str] = []
    if min(tb.values()) > KD_MUC_TIEU or max(tb.values()) < KD_MUC_TIEU:
        ly_do.append(f"luoi khong kep {KD_MUC_TIEU}: IC trong [{min(tb.values()):.4f} ; {max(tb.values()):.4f}]")
    for a, b in zip(luoi, luoi[1:]):
        if tb[b] < tb[a] - KD_HE_SO_SE_DON_DIEU * math.hypot(se[a], se[b]):
            ly_do.append(f"IC giam theo kappa_d: {a} -> {b} ({tb[a]:.4f} -> {tb[b]:.4f}) qua {KD_HE_SO_SE_DON_DIEU:g} SE")
    chon = min(luoi, key=lambda k: (abs(tb[k] - KD_MUC_TIEU), k))
    if chon in (luoi[0], luoi[-1]):
        ly_do.append(f"diem gan muc tieu nhat ({chon}) nam o RIA luoi")
    if abs(tb[chon] - KD_MUC_TIEU) > KD_DUNG_SAI * KD_MUC_TIEU:
        ly_do.append(f"|IC({chon}) - {KD_MUC_TIEU}| = {abs(tb[chon] - KD_MUC_TIEU):.4f} > {KD_DUNG_SAI * KD_MUC_TIEU:.4f}")
    return {"kappa_d": None if ly_do else chon, "gan_nhat": chon, "ic_tb": {str(k): tb[k] for k in luoi},
            "ic_se": {str(k): se[k] for k in luoi}, "that_bai": bool(ly_do), "ly_do": ly_do}


def kiem_kd(ic_kiem: list[float]) -> dict:
    tb = float(np.mean(ic_kiem))
    lo, hi = KD_MUC_TIEU * (1 - KD_DUNG_SAI), KD_MUC_TIEU * (1 + KD_DUNG_SAI)
    return {"n": len(ic_kiem), "ic_tb": tb,
            "ic_se": float(np.std(ic_kiem, ddof=1) / math.sqrt(len(ic_kiem))) if len(ic_kiem) > 1 else None,
            "dai": [lo, hi], "dat": bool(lo <= tb <= hi)}


# ═════════════════════════════════════════════════════════════════════════════
# CHẠY (resumable, nguyên tử)
# ═════════════════════════════════════════════════════════════════════════════

def _t() -> float:
    return time.perf_counter()


def _viec_don_vi(a):
    """Việc của MỘT tiến trình. `a = (viec, luong, *tham_so)`; kiểm cửa dòng hạt NGAY trong tiến trình con."""
    viec, luong, *tham = a
    kiem_luong(luong)
    return {"kd": don_kd, "a0": don_a0, "pt": don_pt, "t1": don_t1}[viec](luong, *tham)


def ghi_khoi(ra: Path, viec: str, khoi: dict, doc_fn=doc_ket_qua_hien_co) -> None:
    """Đọc lại file, thay ĐÚNG khối `viec`, ghi nguyên tử: hai việc chạy song song không đè khối của nhau."""
    ket = doc_fn(ra) or {"buoc": 301, "do": f"ĐO {SO_DO}", "cac_viec": {}}
    ket.setdefault("cac_viec", {})[viec] = khoi
    va_an_toan.ghi(ra, json.dumps(ket, ensure_ascii=False, separators=(",", ":")) + "\n")


def chay_dot(viec: str, luong: int, don_vi: list[tuple], khoi: dict, luu, so_tien_trinh: int = 1,
             luu_moi: int = LUU_MOI, in_tien_do: bool = True) -> None:
    """Chạy các đơn vị CHƯA có trong `khoi["ban_ghi"]` (khoá `khoa`), nối kết quả, gọi `luu()` mỗi `luu_moi` đơn vị. Đơn vị là
    hàm THUẦN của (dòng hạt, chỉ số, mức) nên chạy tiếp không chọn lại gì."""
    xong = {json.dumps(r["khoa"]) for r in khoi["ban_ghi"]}
    con = [(viec, luong, *u[1:]) for u in don_vi if json.dumps(u[0]) not in xong]
    t0 = _t()
    dem = 0

    def nhan(rec):
        nonlocal dem
        khoi["ban_ghi"].append(rec)
        dem += 1
        if dem % luu_moi == 0:
            luu()
            if in_tien_do:
                print(f"[{_t() - t0:8.1f}s] {dem}/{len(con)}", flush=True)

    if so_tien_trinh > 1 and len(con) > 1:
        with ProcessPoolExecutor(max_workers=so_tien_trinh) as pool:
            for rec in pool.map(_viec_don_vi, con, chunksize=1):
                nhan(rec)
    else:
        for u in con:
            nhan(_viec_don_vi(u))


def don_vi_theo_viec(viec: str, dau: int, so: int | None) -> list[tuple]:
    """Danh sách đơn vị `(khoa, *tham_so)` của a0 · pt · t1 (kd có hai giai đoạn, xem `chay_kd`)."""
    if viec == "a0":
        return [(c, c) for c in range(dau, dau + so)]
    kappa = doc_kappa_2x()
    return [(c, c, kappa) for c in range(dau, dau + so)]


def _khoi_moi(viec: str, luong: int, dau: int, so: int | None, cong: dict, so_tien_trinh: int) -> dict:
    return {"trang_thai": "DANG CHAY", "luong": int(luong), "do": SO_DO,
            "cau_hinh": {"dau": int(dau), "so": so, "luu_moi": LUU_MOI, "so_hoan_vi": cx.SO_HOAN_VI,
                         **({"kappa_2x": doc_kappa_2x()} if viec in ("pt", "t1") else {}),
                         **({"ten_spec_f": ten_spec_f(), "R": A0_R, "phan_vi": A0_PHAN_VI} if viec == "a0" else {}),
                         **({"luoi": list(KD_LUOI), "so_tim": KD_SO_TIM, "so_kiem": KD_SO_KIEM, "muc_tieu": KD_MUC_TIEU,
                             "so_phien": KD_SO_PHIEN, "he_so_d": T.HE_SO_D, "phi_d": T.PHI_D, "hat_ic": T.HAT_IC_DA_GHI}
                            if viec == "kd" else {})},
            "git": dict(cong), "moi_truong": {"python": platform.python_version(), "so_tien_trinh": so_tien_trinh},
            "giay": 0.0, "ban_ghi": [], "ket_qua": None}


def chay_kd(luong: int, khoi: dict, dau: int, so_tim: int, so_kiem: int, luu, so_tien_trinh: int, luu_moi: int,
            in_tien_do: bool = True) -> None:
    """Hai giai đoạn: TÌM trên lưới → chọn κ_d (hoặc thất bại) → KIỂM ở κ_d đã chọn."""
    tim = [(f"tim|{j}|{t}", f"tim|{j}|{t}", k, chi_so_kd(dau, j, t)) for j, k in enumerate(KD_LUOI) for t in range(so_tim)]
    chay_dot("kd", luong, tim, khoi, luu, so_tien_trinh, luu_moi, in_tien_do)
    theo = {}
    for r in khoi["ban_ghi"]:
        if r["khoa"].startswith("tim|"):
            theo.setdefault(r["kappa_d"], []).append(r["ic"])
    chon = khoi.get("chon") or chon_kappa_d(theo)
    khoi["chon"] = chon
    luu()
    if chon["that_bai"]:
        khoi["ket_qua"] = {"kappa_d": None, "that_bai": True, "ly_do": chon["ly_do"], "dung": True, "ly_do_dung": chon["ly_do"]}
        return
    kiem = [(f"kiem|{t}", f"kiem|{t}", chon["kappa_d"], chi_so_kd(dau, len(KD_LUOI), t)) for t in range(so_kiem)]
    chay_dot("kd", luong, kiem, khoi, luu, so_tien_trinh, luu_moi, in_tien_do)
    ic_kiem = [r["ic"] for r in khoi["ban_ghi"] if r["khoa"].startswith("kiem|")]
    k = kiem_kd(ic_kiem)
    khoi["kiem"] = k
    ly_do = [] if k["dat"] else [f"KIEM: IC trung binh {k['ic_tb']:.4f} ngoai {k['dai']}"]
    khoi["ket_qua"] = {"kappa_d": None if ly_do else chon["kappa_d"], "that_bai": bool(ly_do), "ly_do": ly_do,
                       "dung": bool(ly_do), "ly_do_dung": ly_do, "ic_tb": chon["ic_tb"], "ic_kiem": k["ic_tb"],
                       "he_so_d": T.HE_SO_D, "phi_d": T.PHI_D}


def chay_viec(viec: str, luong: int, dau: int, so: int | None, ra: Path, cong: dict, so_tien_trinh: int = 1,
              tiep_tuc: bool = False, luu_moi: int = LUU_MOI, in_tien_do: bool = True, so_kiem: int | None = None) -> dict:
    """Chạy MỘT việc (đủ mọi đơn vị), ghi từng đợt vào `ra` (DANG CHAY), xong thì XONG. Trả khối."""
    kiem_luong(luong)
    cu = (doc_ket_qua_hien_co(ra) or {}).get("cac_viec", {}).get(viec)
    khoi = cu if (cu is not None and tiep_tuc) else _khoi_moi(viec, luong, dau, so, cong, so_tien_trinh)
    giay_truoc = float(khoi["giay"])
    t0 = _t()

    def luu(trang_thai: str = "DANG CHAY"):
        khoi["giay"] = giay_truoc + (_t() - t0)
        khoi["trang_thai"] = trang_thai
        ghi_khoi(ra, viec, khoi)

    luu()
    if viec == "kd":
        chay_kd(luong, khoi, dau, so if luong == LUONG_THU else KD_SO_TIM, (so_kiem if luong == LUONG_THU else KD_SO_KIEM),
                luu, so_tien_trinh, luu_moi, in_tien_do)
    else:
        chay_dot(viec, luong, don_vi_theo_viec(viec, dau, so), khoi, luu, so_tien_trinh, luu_moi, in_tien_do)
        ban = sorted(khoi["ban_ghi"], key=lambda r: r["khoa"])
        khoi["ban_ghi"] = ban
        khoi["ket_qua"] = {"a0": tong_hop_a0, "pt": tong_hop_pt, "t1": tong_hop_t1}[viec](ban)
    khoi["ban_ghi"].sort(key=lambda r: json.dumps(r["khoa"]))
    luu("XONG")
    return khoi


def in_khoi(viec: str, khoi: dict) -> list[str]:
    kq = khoi.get("ket_qua")
    ra = [f"== {viec} · dòng {khoi['luong']} · {khoi['trang_thai']} · git {khoi['git'].get('sha', '')[:10]}"
          f"{'' if khoi['git'].get('sach', True) else ' (CÂY BẨN)'} · {khoi['giay']:.0f} s"]
    if kq is None:
        return ra + ["  (chưa có kết quả)"]
    if viec == "kd":
        ra.append(f"  κ_d = {kq['kappa_d']} · thất bại {kq['that_bai']} · IC(điểm đã ghi) lưới: {json.dumps(khoi['chon']['ic_tb'])}")
        if "kiem" in khoi:
            se = khoi["kiem"]["ic_se"]
            ra.append(f"  KIỂM: n {khoi['kiem']['n']} · IC {khoi['kiem']['ic_tb']:.4f} ± {'?' if se is None else f'{se:.4f}'} · dải {khoi['kiem']['dai']}")
    elif viec == "a0":
        ra.append(f"  p̂ = {kq['k_G']}/{kq['N']} = {kq['p_hat']:.4f} · SE {kq['se']:.4f} · ngưỡng binom.ppf(0,999;1000;p̂) = {kq['nguong']}")
        ra.append(f"  trung bình {kq['so_spec_trung_binh']:.3f} spec khai/thị trường")
    else:
        ra.append(f"  {json.dumps({k: v for k, v in kq.items() if k != 'o'}, ensure_ascii=False)}")
        for t, o in kq["o"].items():
            s = "?" if o["s"] is None else f"{o['s']:.4f}"          # n = 1 (dòng thử): chưa có độ lệch chuẩn
            ra.append(f"  {t:<2} m {o['m']:+.4f} s {s} σ̄ {o['sigma_bar']:.4f} QUA {o['QUA']}/{o['n']} (P {o['P']:.3f}) báo động {o['bao_dong']}")
    if kq.get("dung"):
        ra.append("  DỪNG: " + "; ".join(kq["ly_do_dung"]))
    return ra


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--viec", choices=TEN_VIEC, default=None)
    ap.add_argument("--luong", type=int, default=None, help="dòng hạt: 1 (thật) hoặc 9001 (thử)")
    ap.add_argument("--so", type=int, default=None, help="số thị trường (dòng 1: giá trị đã khai); kd 9001: số mẫu mỗi điểm lưới")
    ap.add_argument("--dau", type=int, default=None, help="chỉ số thị trường đầu (dòng 1: giá trị đã khai)")
    ap.add_argument("--so-tien-trinh", type=int, default=1)
    ap.add_argument("--tiep-tuc", action="store_true")
    ap.add_argument("--ra", default=None, help="CHỈ dòng thử 9001: file kết quả (không được là file chính thức)")
    ap.add_argument("--doc", action="store_true", help="in kết quả đã ghi; không sinh thị trường nào")
    a = ap.parse_args(argv)
    if a.doc:
        ket = doc_ket_qua_hien_co(Path(a.ra).resolve() if a.ra else DUONG_KET_QUA)
        if ket is None:
            print("chua co file ket qua", file=sys.stderr)
            return 2
        for v, k in ket.get("cac_viec", {}).items():
            print("\n".join(in_khoi(v, k)))
        return 0
    if a.viec is None or a.luong is None:
        ap.error("can --viec va --luong (hoac --doc)")
    try:
        kiem_luong(a.luong)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    luong = int(a.luong)
    if luong == LUONG_THU and not a.ra:
        ap.error("dong thu 9001 can --ra <file>")
    ra = Path(a.ra).resolve() if (luong == LUONG_THU and a.ra) else DUONG_KET_QUA
    khai = KHAI[a.viec]
    dau = a.dau if a.dau is not None else (khai["dau"] if luong == LUONG_THAT else 1)
    so = a.so if a.so is not None else (khai.get("so") if luong == LUONG_THAT else 2)
    try:
        cong = kiem_cong(a.viec, luong, dau, so, ra, a.tiep_tuc)
        if a.viec == "a0":
            kiem_de_xuat_co_z_truoc_khi_chay()
    except CongTu as e:
        print("CỬA TỪ CHỐI — không sinh thị trường nào của dòng này:", file=sys.stderr)
        for s in e.ly_do:
            print("  - " + s, file=sys.stderr)
        return 3
    except DeXuatThieuZ as e:
        print(f"CỬA TỪ CHỐI — {e}", file=sys.stderr)
        return 3
    khoi = chay_viec(a.viec, luong, dau, so, ra, cong, a.so_tien_trinh, a.tiep_tuc,
                     so_kiem=(2 * so if a.viec == "kd" and so else None))
    print("\n".join(in_khoi(a.viec, khoi)))
    return 4 if (khoi.get("ket_qua") or {}).get("dung") else 0


if __name__ == "__main__":
    sys.exit(main())
