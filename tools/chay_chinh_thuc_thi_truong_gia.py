"""`chay-chinh-thuc` — LƯỢT CHẠY CHÍNH THỨC của C4 (T6): dòng hạt 2, 3, 4, và đọc kết cục theo bảng đã ký (BƯỚC 295; chạy ở BƯỚC 296).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 4.8 (hạt), 6 (tiêu chí), 8 ("Lát 5") và `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 37 (bảng đã ký).
Đặc tả là nguồn duy nhất; đừng chép nó vào đây.

ĐÂY LÀ NƠI DUY NHẤT dòng hạt 2, 3, 4 được mở (bất biến 7). Mọi dụng cụ khác (`chay_vong_thi_truong_gia` · `hieu_chuan_thi_truong_gia`
· `oracle_tang2_thi_truong_gia` · `chay_tang2_thi_truong_gia` · `chay_vong_tang2_thi_truong_gia`) giữ cửa `kiem_luong` cũ: chỉ 1 và 9001.
Dòng 5 (chẩn đoán SAU khi đã nhìn kết quả) không bao giờ mở ở đây.

CỬA (`kiem_cong`) — một dòng 2/3/4 chỉ chạy được khi TẤT CẢ đúng, đọc bằng git lúc chạy:
  1. `git fetch origin main` thành công (không kiểm được = không chạy);
  2. `docs/TIEU-CHI-DOC-TRUOC.md` ở `origin/main` CÓ mục `## ĐO 37 —`;
  3. thân ĐO 37 ở `origin/main` NÊU nguyên văn lệnh sắp chạy (`lenh_chuan`) và dòng kế hoạch của dòng hạt (`dong_ke_hoach`: chỉ số thị trường);
  4. thân ĐO 37 ở cây làm việc BẰNG thân ở `origin/main` (không ai sửa tiêu chí sau khi ký), và mọi file của `FILE_GHIM`
     (chính dụng cụ này, bộ sinh, vòng học, máy đo, hai bản ghi hiệu chuẩn) ở cây làm việc BẰNG `origin/main`;
  5. `origin/main` là tổ tiên của `HEAD`;
  6. dòng hạt ấy CHƯA có bản ghi XONG trong `docs/thi-truong-gia-ket-qua.json` (một lần); đang dở thì chỉ chạy với `--tiep-tuc`.
Thiếu một điều là KHÔNG sinh thị trường nào, không đọc một dòng hạt nào, mã thoát 3 và in HẾT các điều thiếu.
Dòng 9001 là dòng thử (kích thước nhỏ, kết quả ra file người gọi chỉ định, KHÔNG BAO GIỜ ra file chính thức).

MỖI THỊ TRƯỜNG chạy HAI thủ tục trên CÙNG dữ liệu (mục 6): (i) bộ ba, K = 3; (ii) chuỗi đề xuất → xác nhận → nâng cấp (+ kiểm bất biến
5.4 khoản 1–4 = tiêu chí C1). Oracle chỉ đọc SAU khi cả hai đã xong (gác G4). Tầng 2: thêm P1 · P2 · P3 và bộ ba của Tầng 2 (G′ · Z · H).

CHẠY (BƯỚC 296 — các lệnh này nằm nguyên văn trong ĐO 37):
    ./.venv/Scripts/python.exe -X utf8 tools/chay_chinh_thuc_thi_truong_gia.py --luong 2 --so-tien-trinh 12
    ./.venv/Scripts/python.exe -X utf8 tools/chay_chinh_thuc_thi_truong_gia.py --luong 3 --so-tien-trinh 12
    ./.venv/Scripts/python.exe -X utf8 tools/chay_chinh_thuc_thi_truong_gia.py --luong 4 --so-tien-trinh 12
    ./.venv/Scripts/python.exe -X utf8 tools/chay_chinh_thuc_thi_truong_gia.py --ket-cuc
THỬ (BƯỚC 295, dòng thử 9001, nhỏ):
    ./.venv/Scripts/python.exe -X utf8 tools/chay_chinh_thuc_thi_truong_gia.py --luong 9001 --tang 1 --so-moi-o 1 --ra <file>

Mã thoát: 0 xong · 2 lỗi đối số · 3 cửa từ chối. `--ket-cuc`: 0 ĐẠT · 1 TRƯỢT · 2 KHÔNG ĐỌC ĐƯỢC hay chưa đủ dòng hạt.
Chỉ ghi MỘT file chính thức MỖI ĐO (ĐO 37: `docs/thi-truong-gia-ket-qua.json`; ĐO 38: file `-do38` cạnh nó) bằng `va_an_toan.ghi`. Không Sheets, không `*.db`, không mạng ngoài git.

TỔNG QUÁT HOÁ CHO ĐO 38 (BƯỚC 303; lượt chạy là BƯỚC 304). Dụng cụ nay phục vụ HAI ĐO bằng hai bản ghi cấu hình `KeHoachDo` (`DO_37` mặc định, `DO_38`) và bảng
`DO_THEO_LUONG` (dòng hạt → ĐO). Mọi hàm nhận `do=None` (suy từ dòng hạt, không có thì ĐO 37) nên MỌI phép thử của ĐO 37 chạy không đổi; kết quả của hai ĐO ghi ở hai
file khác nhau, không đè nhau. ĐO 38: dòng hạt 6 · 7 · 8 · 9 chỉ mở khi ĐO 38 đã ở `origin/main` (cửa như trên, thêm: bản ghi hiệu chuẩn của BƯỚC 301 phải
XONG, không báo DỪNG, và MỘT câu `A0 ≤ … · PT dải 99% […] · κ_d = …` ở ĐO 38 phải khớp bản ghi); dòng 1 · 5 · 10 LUÔN chặn. A0 và dải PT của ĐO 38 ĐỌC từ bản ghi hiệu chuẩn,
không gõ ở đây. Dòng 9 là thị trường NULL có nhớ (`thi_truong_gia.sinh_thi_truong_m`, oracle `tinh_su_that_m`); tiêu chí M1 (≤ 50/1.000 xác nhận nhầm) và M2 (sd gộp của z′ ∈
[0,8 ; 1,25]) đọc ở `tong_hop`. Lệnh ĐO 38 mang `--do 38` (ĐO 37 giữ nguyên): `--luong 6 --do 38`, không suy ngầm, để lệnh của ĐO 37 `--luong 6` vẫn là lỗi đối số.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import math
import platform
import re
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
import vong_hoc_gia as V  # noqa: E402
from chay_vong_tang2_thi_truong_gia import noi_dong_va_gia  # noqa: E402
from hieu_chuan_thi_truong_gia import keo_luc_gia, so_ung_vien_bo_ba  # noqa: E402

DUONG_KET_QUA = GOC / "docs" / "thi-truong-gia-ket-qua.json"
DUONG_HIEU_CHUAN = GOC / "docs" / "thi-truong-gia-hieu-chuan.json"
DUONG_G_PHAY = GOC / "docs" / "thi-truong-gia-g-phay.json"
#: Hai file của ĐO 38 dựng từ tên file của ĐO 37 (cùng thư mục, thêm hậu tố `-do38`): bản ghi hiệu chuẩn của BƯỚC 301 và file kết quả của lượt chạy (BƯỚC 304).
DUONG_HC38 = DUONG_HIEU_CHUAN.with_name(f"{DUONG_HIEU_CHUAN.stem}-do38{DUONG_HIEU_CHUAN.suffix}")
DUONG_KET_QUA_38 = DUONG_KET_QUA.with_name(f"{DUONG_KET_QUA.stem}-do38{DUONG_KET_QUA.suffix}")
DUONG_TIEU_CHI = "docs/TIEU-CHI-DOC-TRUOC.md"
TEN_DUNG_CU = "tools/chay_chinh_thuc_thi_truong_gia.py"

# ── dòng hạt ─────────────────────────────────────────────────────────────────
LUONG_THU = 9001
LUONG_CHINH_THUC = (2, 3, 4)
LUONG_KHONG_BAO_GIO = (5,)   # chẩn đoán SAU khi đã nhìn kết quả: không bao giờ mở ở dụng cụ này
SO_DO = 37                   # số của ĐO ký bảng mục 6

#: Kế hoạch KHAI: ô (muc = hệ số MDE₈₀ của file hiệu chuẩn; chỉ số thị trường liền nhau từ `chi_so_dau`). Mỗi thị trường dùng ĐÚNG MỘT hạt
#: `[luong, chi_so]`; ba mức của dòng 2 và hai ô của dòng 4 ở KHỐI chỉ số riêng (không chung số ngẫu nhiên giữa các κ — Lát 2, mục 16 khoản 2).
KE_HOACH = {
    2: {"tang": 1, "o": (("0.5x", 0.5, 1001, 400), ("1x", 1.0, 2001, 400), ("2x", 2.0, 3001, 400))},   # không dùng chỉ số 1: mục 15 khoản 12
    3: {"tang": 1, "o": (("NULL", 0.0, 1, 1000),)},
    4: {"tang": 2, "o": (("NULL", 0.0, 1, 100), ("2x", 2.0, 1001, 100))},
}

# ── ngưỡng của mục 6 (KHAI; chép từ bảng mục 6, kiểm bằng test so với ĐO 37) ──
NGUONG = {"A": 320, "A0": 317, "B1": 75, "B2": 360, "B3": 20, "P3": 90, "PT_NULL": 12, "C3": 50}
SO_BOOTSTRAP_C2 = 5000
HAT_BOOTSTRAP_C2 = 0
DUNG_SAI_MUC = 0.10
#: Tiêu chí MÁY ĐO ở NULL, đọc theo TỶ LỆ (mục 15 khoản 8). Ba con số này là ba ngưỡng đã khoá ở test của Lát 1
#: (`tests/test_thi_truong_gia.py`), chọn TRƯỚC mọi lượt chạy; ĐO 37 xin người dùng duyệt chúng làm tiêu chí KHÔNG ĐỌC ĐƯỢC.
MAY_DO_NULL = {"ty_le_o_trong_2se_toi_thieu": 0.85, "sd_z": (0.7, 1.5), "trung_binh_z_toi_da": 0.5}

# ── ĐO 38 (BƯỚC 303): ngưỡng MỚI và kế hoạch ──────────────────────────────────
TEN_O_NULL_M = "NULL-M"   # ô của dòng 9: thị trường NULL có nhớ (nhân tố ngành bền); bộ sinh `thi_truong_gia.sinh_thi_truong_m`
K_BO_BA = 3               # G · Z · H
#: M1: số thị trường NULL-M có ≥ 1 xác nhận nhầm tối đa (R = 1.000). M2: độ lệch chuẩn GỘP của z′ nằm trong `M2_dai` (đóng hai đầu). `ty_le_loai_toi_da`: số cặp
#: (thị trường × ứng viên) bị loại khỏi phép gộp vì σ_hoán-vị = 0 hay chưa phán, tối đa bao nhiêu phần của 3 × R cặp; quá thì M2 là KHÔNG ĐỌC ĐƯỢC.
#: A0 và dải PT của ĐO 38 KHÔNG nằm ở đây: chúng đọc từ bản ghi hiệu chuẩn (`doc_hieu_chuan_do38`).
NGUONG_M = {"M1": 50, "M2_dai": (0.8, 1.25), "ty_le_loai_toi_da": 0.01}
#: Kế hoạch KHAI của ĐO 38 (đặc tả mục 5 và 21.5): cùng cỡ ô và cùng khối chỉ số như ĐO 37 nhưng khoá `luong` KHÁC nên hạt khác; dòng 9 là NULL-M.
KE_HOACH_38 = {
    6: {"tang": 1, "o": (("0.5x", 0.5, 1001, 400), ("1x", 1.0, 2001, 400), ("2x", 2.0, 3001, 400))},
    7: {"tang": 1, "o": (("NULL", 0.0, 1, 1000),)},
    8: {"tang": 2, "o": (("NULL", 0.0, 1, 100), ("2x", 2.0, 1001, 100))},
    9: {"tang": 1, "o": ((TEN_O_NULL_M, 0.0, 1, 1000),)},
}
LUU_MOI_MAC_DINH = 25


# ═════════════════════════════════════════════════════════════════════════════
# CỬA
# ═════════════════════════════════════════════════════════════════════════════

class CongTu(Exception):
    """Cửa từ chối. `ly_do` là DANH SÁCH mọi điều thiếu (không dừng ở điều đầu)."""

    def __init__(self, ly_do: list[str]):
        super().__init__("; ".join(ly_do))
        self.ly_do = list(ly_do)


def _tem(luong: int, sha_do: str, head: str, goc_main: str) -> str:
    return hashlib.sha256(f"chay-chinh-thuc-295|{luong}|{sha_do}|{head}|{goc_main}".encode()).hexdigest()


@dataclasses.dataclass(frozen=True)
class PhepChay:
    """Giấy phép mở MỘT dòng hạt chính thức. Chỉ `kiem_cong` dựng nó (tem băm); tiến trình con nhận lại qua pickle và kiểm tem."""
    luong: int
    sha_do: str
    head: str
    goc_main: str
    tem: str

    def hop_le(self) -> bool:
        return self.luong in DO_THEO_LUONG and self.tem == _tem(self.luong, self.sha_do, self.head, self.goc_main)


def kiem_luong_chinh_thuc(luong, phep=None) -> None:
    """Cửa DUY NHẤT tới bộ sinh của dụng cụ này. 9001 qua tự do (dòng thử); 2 · 3 · 4 (ĐO 37) và 6 · 7 · 8 · 9 (ĐO 38) chỉ khi có `PhepChay` đúng dòng; MỌI dòng khác
    (kể cả 1 · 5 · 10 và kiểu lạ) nổ. Mọi hàm gọi bộ sinh phải gọi cửa này TRƯỚC (gác AST ở test)."""
    if isinstance(luong, bool) or not isinstance(luong, (int, np.integer)):
        raise ValueError(f"dong hat phai la so nguyen, nhan {luong!r}")
    luong = int(luong)
    if luong == LUONG_THU:
        return
    if luong in LUONG_CHAN_TAT_CA:
        raise ValueError(f"dong hat {luong} bi chan vinh vien o dung cu nay (chan doan SAU khi da nhin ket qua, hay dong hieu chuan; bat bien 7)")
    if luong not in DO_THEO_LUONG:
        raise ValueError(f"dong hat {luong} khong thuoc {tuple(DO_THEO_LUONG)} va khong phai dong thu {LUONG_THU}")
    if not isinstance(phep, PhepChay) or phep.luong != luong or not phep.hop_le():
        raise CongTu([f"dong hat {luong} chi mo duoc qua kiem_cong (can giay phep dung dong hat, con nguyen ven)"])


def lenh_chuan(luong: int, do: int | None = None) -> str:
    """Phần lệnh CỐ ĐỊNH (không gồm `--so-tien-trinh`/`--tiep-tuc`, vốn không đổi kết quả) mà ĐO tương ứng phải NÊU nguyên văn. ĐO 37 giữ
    dạng cũ (`--luong N`); ĐO khác thêm `--do <số>` trước `--luong` (để `--luong 6` KHÔNG mở được dòng 6 khi quên `--do`)."""
    cfg = cau_hinh_do(do, luong)
    if cfg.so_do == SO_DO:
        return f"{TEN_DUNG_CU} --luong {int(luong)}"
    return f"{TEN_DUNG_CU} --do {cfg.so_do} --luong {int(luong)}"


def lenh_ket_cuc(do: int | None = None) -> str:
    """Lệnh đọc kết cục (không sinh thị trường nào) của một ĐO: ĐO 37 `--ket-cuc`; ĐO khác thêm `--do <số>`."""
    cfg = cau_hinh_do(do)
    return f"{TEN_DUNG_CU} --ket-cuc" if cfg.so_do == SO_DO else f"{TEN_DUNG_CU} --ket-cuc --do {cfg.so_do}"


def dong_ke_hoach(luong: int, do: int | None = None) -> str:
    """Dòng kế hoạch của dòng hạt, sinh từ kế hoạch của ĐO (không gõ tay): ĐO ấy phải NÊU nguyên văn dòng này."""
    k = cau_hinh_do(do, luong).ke_hoach[int(luong)]
    o = "; ".join(f"ô {ten} (mức {muc:g}× MDE80) chỉ số {dau}–{dau + so - 1}" for ten, muc, dau, so in k["o"])
    return f"dòng {int(luong)} · Tầng {k['tang']}: {o}"


def chuan_hoa(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def cat_muc_do(van: str, so: int = SO_DO) -> str | None:
    """Thân của mục `## ĐO <so> —` (tới tiêu đề `## ĐO` kế hay hết file); None nếu không có."""
    m = re.search(rf"^##\s+ĐO\s+{so}\s*—.*$", van, re.M)
    if not m:
        return None
    tiep = re.search(r"^##\s+ĐO\s", van[m.end():], re.M)
    return van[m.start(): m.end() + tiep.start()] if tiep else van[m.start():]


#: File mà lượt chạy ĐỌC hay CHẠY: ở cây làm việc phải bằng `origin/main` (không sửa sau khi ký).
FILE_GHIM = (TEN_DUNG_CU, "thi_truong_gia.py", "thi_truong_gia_tang2.py", "vong_hoc_gia.py", "cham_bong.py", "cham_xac_nhan.py",
             "tools/hieu_chuan_thi_truong_gia.py", "tools/chay_vong_tang2_thi_truong_gia.py", "tools/chay_vong_thi_truong_gia.py",
             "docs/thi-truong-gia-hieu-chuan.json", "docs/thi-truong-gia-g-phay.json")


@dataclasses.dataclass(frozen=True)
class KeHoachDo:
    """Cấu hình MỘT ĐO của dụng cụ: số ĐO, dòng hạt được mở (qua cửa), dòng hạt chặn vĩnh viễn, kế hoạch (ô · mức · chỉ số đầu · số), file kết quả, file ghim,
    thứ tự dòng hạt cho `tong_hop` (có lợi thế · NULL · Tầng 2 [· NULL-M]), BƯỚC của lượt chạy, `luu_moi` riêng từng dòng, và cờ "cần bản ghi hiệu chuẩn"."""
    so_do: int
    luong: tuple
    luong_chan: tuple
    ke_hoach: dict
    duong_ket_qua: Path
    file_ghim: tuple
    luong_tong_hop: tuple
    buoc_chay: int
    luu_moi: dict
    can_hieu_chuan: bool

    def luu_moi_cua(self, luong: int) -> int:
        if int(luong) in self.luu_moi:
            return self.luu_moi[int(luong)]
        return LUU_MOI_MAC_DINH


#: ĐO 37 là MẶC ĐỊNH của mọi hàm: `KE_HOACH` và `FILE_GHIM` là đúng các đối tượng cũ nên mọi phép thử ĐO 37 chạy không đổi.
DO_37 = KeHoachDo(so_do=SO_DO, luong=LUONG_CHINH_THUC, luong_chan=LUONG_KHONG_BAO_GIO, ke_hoach=KE_HOACH, duong_ket_qua=DUONG_KET_QUA,
                  file_ghim=FILE_GHIM, luong_tong_hop=(2, 3, 4), buoc_chay=295, luu_moi={}, can_hieu_chuan=False)
#: ĐO 38: dòng 6 · 7 · 8 · 9 mở qua cửa; 1 (chỉ hiệu chuẩn) · 5 · 10 (chẩn đoán SAU khi nhìn) chặn vĩnh viễn; dòng 8 ghi mỗi 12 thị trường (≤ một đợt ≈ 21 phút mất).
DO_38 = KeHoachDo(so_do=38, luong=(6, 7, 8, 9), luong_chan=(1, 5, 10), ke_hoach=KE_HOACH_38, duong_ket_qua=DUONG_KET_QUA_38,
                  file_ghim=FILE_GHIM + (f"docs/{DUONG_HC38.name}",), luong_tong_hop=(6, 7, 8, 9), buoc_chay=304, luu_moi={8: 12}, can_hieu_chuan=True)
CAU_HINH = {37: DO_37, 38: DO_38}
DO_THEO_LUONG = {2: 37, 3: 37, 4: 37, 6: 38, 7: 38, 8: 38, 9: 38}
LUONG_CHAN_TAT_CA = tuple(sorted({x for c in CAU_HINH.values() for x in c.luong_chan}))   # 1 · 5 · 10: không bao giờ mở ở dụng cụ này


def cau_hinh_do(do: int | None = None, luong=None) -> KeHoachDo:
    """Cấu hình của ĐO `do`; không nêu thì suy từ dòng hạt (`DO_THEO_LUONG`), không suy được (dòng thử, dòng lạ, kiểu lạ) thì ĐO 37 — MẶC ĐỊNH."""
    if do is None:
        do = SO_DO
        if isinstance(luong, (int, np.integer)) and not isinstance(luong, bool) and int(luong) in DO_THEO_LUONG:
            do = DO_THEO_LUONG[int(luong)]
    if do not in CAU_HINH:
        raise ValueError(f"khong co ĐO {do!r} o dung cu nay (co: {tuple(CAU_HINH)})")
    return CAU_HINH[do]


# ── bản ghi hiệu chuẩn của ĐO 38 (BƯỚC 301) ─────────────────────────────────

def _vi(x) -> str:
    return str(x).replace(".", ",")


def doc_ban_ghi_hieu_chuan(duong: Path | None = None) -> dict | None:
    """Bản ghi hiệu chuẩn của ĐO 38 ở cây làm việc (đọc, không ghi); None nếu không có hay không đọc được."""
    duong = DUONG_HC38 if duong is None else Path(duong)
    if not duong.is_file():
        return None
    try:
        ban = json.loads(duong.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return ban if isinstance(ban, dict) else None


def kiem_hieu_chuan_do38(ban) -> tuple[dict | None, list[str]]:
    """Kiểm bản ghi hiệu chuẩn: đủ bốn việc `kd · a0 · t1 · pt` XONG, KHÔNG việc nào báo DỪNG hay THẤT BẠI, và ba số có đúng kiểu. Trả `(hc, lỗi)`; có lỗi thì
    `hc` là None. `hc` = `{"kappa_d", "nguong_A0", "dai_pt"}` — đúng ba số mà ĐO 38 ký (không số nào gõ ở dụng cụ này)."""
    if not isinstance(ban, dict) or not isinstance(ban.get("cac_viec"), dict):
        return None, ["khong doc duoc ban ghi (thieu cac_viec)"]
    loi: list[str] = []
    kq_viec: dict = {}
    for viec in ("kd", "a0", "t1", "pt"):
        v = ban["cac_viec"].get(viec)
        if not isinstance(v, dict):
            loi.append(f"viec {viec} vang")
            continue
        if v.get("trang_thai") != "XONG":
            loi.append(f"viec {viec} chua XONG (trang thai {v.get('trang_thai')!r})")
        kq = v.get("ket_qua")
        if not isinstance(kq, dict):
            loi.append(f"viec {viec} khong co ket_qua")
            continue
        kq_viec[viec] = kq
        if kq.get("dung"):
            loi.append(f"viec {viec}: luat DUNG da bao ({kq.get('ly_do_dung')})")
        if viec == "kd" and kq.get("that_bai"):
            loi.append(f"viec kd THAT BAI ({kq.get('ly_do')})")
    if loi:
        return None, loi
    kd, nguong, dai = kq_viec["kd"].get("kappa_d"), kq_viec["a0"].get("nguong"), kq_viec["pt"].get("dai_99")
    if isinstance(kd, bool) or not isinstance(kd, (int, float)) or not kd > 0:
        loi.append(f"kappa_d khong hop le: {kd!r}")
    if isinstance(nguong, bool) or not isinstance(nguong, int):
        loi.append(f"nguong A0 phai la so nguyen, nhan {nguong!r}")
    if not (isinstance(dai, (list, tuple)) and len(dai) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in dai) and dai[0] <= dai[1]):
        loi.append(f"dai 99% cua PT khong hop le: {dai!r}")
    if loi:
        return None, loi
    return {"kappa_d": float(kd), "nguong_A0": int(nguong), "dai_pt": (int(dai[0]), int(dai[1]))}, []


def doc_hieu_chuan_do38(duong: Path | None = None) -> dict | None:
    """`kiem_hieu_chuan_do38` trên bản ghi ở `duong` (mặc định `DUONG_HC38`); None nếu không có hay có điều kiện xấu."""
    hc, loi = kiem_hieu_chuan_do38(doc_ban_ghi_hieu_chuan(duong))
    return hc if not loi else None


def doc_kappa_d(duong: Path | None = None) -> float:
    """κ_d của thị trường NULL-M, đọc từ bản ghi hiệu chuẩn của ĐO 38 (đọc, không ghi, không gõ tay). Không có hay chưa đạt thì NỔ."""
    hc = doc_hieu_chuan_do38(duong)
    if hc is None:
        raise ValueError("ban ghi hieu chuan ĐO 38 vang hay chua dat: khong co kappa_d")
    return float(hc["kappa_d"])


def cau_da_ky_do38(hc: dict) -> str:
    """MỘT câu mà ĐO 38 phải NÊU nguyên văn: ba số rút từ bản ghi hiệu chuẩn (A0 · dải PT · κ_d). Cửa so câu này với văn bản ĐO 38 ở `origin/main`, nên một
    bản ghi mang số khác số đã ký làm cửa đóng (không tính lại rồi chạy tiếp)."""
    lo, hi = hc["dai_pt"]
    return f"A0 ≤ {hc['nguong_A0']} · PT dải 99% [{lo} ; {hi}] · κ_d = {_vi(hc['kappa_d'])}"


def git_that(*doi) -> tuple[int, str]:
    """Chạy `git` ở gốc repo, trả (mã thoát, stdout). Không có git thì (127, '')."""
    try:
        r = subprocess.run(["git", *doi], cwd=str(GOC), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return r.returncode, r.stdout


def doc_ket_qua_hien_co(duong: Path = DUONG_KET_QUA) -> dict | None:
    return json.loads(Path(duong).read_text(encoding="utf-8")) if Path(duong).is_file() else None


def kiem_cong(luong: int, git=git_that, ket_qua_hien_co: dict | None = None, tiep_tuc: bool = False,
              van_ban_cay: str | None = None, do: int | None = None, ban_ghi_hc: dict | None = None) -> PhepChay:
    """Cửa. Trả `PhepChay` nếu TẤT CẢ điều ở docstring đầu file đúng; ngược lại nổ `CongTu` với MỌI điều thiếu.
    `git(*đối số) -> (mã thoát, stdout)`, `van_ban_cay` (thân `docs/TIEU-CHI-DOC-TRUOC.md` ở cây làm việc) và `ban_ghi_hc` (bản ghi hiệu chuẩn của ĐO 38,
    đã parse) tiêm được để thử. `do` = số ĐO; không nêu thì suy từ dòng hạt (`DO_THEO_LUONG`), không suy được thì ĐO 37."""
    cfg = cau_hinh_do(do, luong)
    if isinstance(luong, bool) or not isinstance(luong, (int, np.integer)) or int(luong) not in cfg.luong:
        raise CongTu([f"dong hat {luong!r} khong phai mot trong {cfg.luong} cua ĐO {cfg.so_do} (dong {LUONG_CHAN_TAT_CA} va moi dong khac bi chan)"])
    luong, so = int(luong), cfg.so_do
    thieu: list[str] = []
    rc, _ = git("fetch", "origin", "main", "--quiet")
    if rc != 0:
        thieu.append(f"git fetch origin main that bai (khong kiem duoc ĐO {so} o origin/main)")
    rc, van_main = git("show", f"origin/main:{DUONG_TIEU_CHI}")
    do_main = cat_muc_do(van_main, so) if rc == 0 else None
    hc = None
    if cfg.can_hieu_chuan:
        ban = ban_ghi_hc if ban_ghi_hc is not None else doc_ban_ghi_hieu_chuan()
        hc, loi_hc = kiem_hieu_chuan_do38(ban)
        thieu += [f"ban ghi hieu chuan ĐO {so}: {s}" for s in loi_hc]
    if do_main is None:
        thieu.append(f"origin/main:{DUONG_TIEU_CHI} khong co muc '## ĐO {so} —'")
    else:
        if chuan_hoa(lenh_chuan(luong, so)) not in chuan_hoa(do_main):
            thieu.append(f"ĐO {so} o origin/main khong neu nguyen van lenh: {lenh_chuan(luong, so)}")
        if chuan_hoa(dong_ke_hoach(luong, so)) not in chuan_hoa(do_main):
            thieu.append(f"ĐO {so} o origin/main khong neu nguyen van dong ke hoach: {dong_ke_hoach(luong, so)}")
        if hc is not None and chuan_hoa(cau_da_ky_do38(hc)) not in chuan_hoa(do_main):
            thieu.append(f"ĐO {so} o origin/main khong neu nguyen van cau so da ky khop ban ghi hieu chuan: {cau_da_ky_do38(hc)}")
        if van_ban_cay is None:
            van_ban_cay = (GOC / DUONG_TIEU_CHI).read_text(encoding="utf-8") if (GOC / DUONG_TIEU_CHI).is_file() else ""
        do_cay = cat_muc_do(van_ban_cay, so)
        if do_cay is None or chuan_hoa(do_cay) != chuan_hoa(do_main):
            thieu.append(f"ĐO {so} o cay lam viec khac origin/main (khong ai duoc sua tieu chi sau khi ky)")
    rc, _ = git("merge-base", "--is-ancestor", "origin/main", "HEAD")
    if rc != 0:
        thieu.append("origin/main khong phai to tien cua HEAD")
    for f in cfg.file_ghim:
        rc, _ = git("diff", "--quiet", "origin/main", "--", f)
        if rc != 0:
            thieu.append(f"{f} o cay lam viec khac origin/main (hoac khong kiem duoc)")
    if ket_qua_hien_co is not None:
        hien_co = ket_qua_hien_co
    else:   # ĐO 37 gọi hàm KHÔNG đối số (đường mặc định, như trước); ĐO khác đọc ĐÚNG file của mình
        hien_co = doc_ket_qua_hien_co() if cfg is DO_37 else doc_ket_qua_hien_co(cfg.duong_ket_qua)
    if hien_co is not None:
        cu = hien_co["cac_luong"].get(str(luong)) if isinstance(hien_co.get("cac_luong"), dict) else None
        if cu is not None and cu.get("trang_thai") == "XONG":
            thieu.append(f"dong hat {luong} DA chay xong (mot lan, khong chay lai)")
        elif cu is not None and not tiep_tuc:
            thieu.append(f"dong hat {luong} dang do: chi chay tiep voi --tiep-tuc")
    if thieu:
        raise CongTu(thieu)
    rc, head = git("rev-parse", "HEAD")
    rc2, goc_main = git("rev-parse", "origin/main")
    if rc != 0 or rc2 != 0:
        raise CongTu(["khong doc duoc HEAD hay origin/main"])
    sha_do = hashlib.sha256(chuan_hoa(do_main).encode("utf-8")).hexdigest()
    return PhepChay(luong, sha_do, head.strip(), goc_main.strip(), _tem(luong, sha_do, head.strip(), goc_main.strip()))


# ═════════════════════════════════════════════════════════════════════════════
# MỘT THỊ TRƯỜNG
# ═════════════════════════════════════════════════════════════════════════════

def doc_kappa_muc(he_so: float, duong: Path = DUONG_HIEU_CHUAN) -> float:
    """κ của mức `he_so` × MDE₈₀ đọc từ file hiệu chuẩn của Lát 2 (đọc, không ghi)."""
    muc = json.loads(Path(duong).read_text(encoding="utf-8"))["muc"]
    kp = [m["kappa"] for m in muc if abs(m["he_so"] - he_so) < 1e-9]
    if len(kp) != 1:
        raise ValueError(f"file hieu chuan khong co dung mot muc he_so={he_so}")
    return float(kp[0])


def _bam(dong: list[dict], gia=None) -> str:
    """Băm dòng quyết định và, nếu có, ma trận giá. Ở Tầng 1 `κ` chỉ đổi GIÁ chứ không đổi dòng quyết định, nên băm riêng dòng
    sẽ bỏ lọt đúng thứ `κ` đổi (test dựng lại phát hiện này ở BƯỚC 295)."""
    h = hashlib.sha256()
    for r in dong:
        h.update(f"{r['symbol']}|{r['signal_date']}|{r['score']}|{r['components']}\n".encode("utf-8"))
    if gia is not None:
        h.update(np.ascontiguousarray(gia.to_numpy(dtype=float)).tobytes())
    return h.hexdigest()[:24]


def _bam_khung(tt) -> str:
    h = hashlib.sha256()
    for m in tt.ma:
        for c in G.COT_OHLCV[1:]:
            h.update(np.ascontiguousarray(tt.gia[m][c].to_numpy(dtype=float)).tobytes())
    return h.hexdigest()[:24]


def bo_ba_tang1_ket_qua(r: dict) -> dict:
    ra = {}
    for ten in ("G", "Z", "H"):
        c = r["chi_tiet"][ten]
        ra[ten] = {"tt": c["trang_thai"], "p": float(c["p"]), "delta": float(c["delta"]), "n_phien": int(c["n_phien"]), "n_ma": int(c["n_ma"])}
    return ra


def kiem_c1(vong: dict, dong: list[dict], ngay: list[str]) -> list[str]:
    """Tiêu chí C1: bất biến 5.4 khoản 1–4 trên MỘT thị trường (tất định; một vi phạm là lỗi mã). Rỗng = đạt.
    (1) chỉ `QUA` tạo phiên bản; (2) spec phiên bản mới BẰNG spec đã khai; (3) hiệu lực từ phiên SAU phiên đọc;
    (4) từ phiên hiệu lực, `score` = `int` của tổ hợp tuyến tính thành phần theo spec (cộng bằng `math.fsum`, độc lập với `sum()`
    của `cham_bong.diem_ung_vien`; ô đúng trên biên nguyên được phép lệch 1 đơn vị — mục 15 khoản 9), trước đó giữ nguyên."""
    sai: list[str] = []
    pb = vong["so_phien_ban"]["phien_ban"]
    so_uv = vong["so_ung_vien"]["ung_vien"]
    nang = [d for d in vong["doc"] if d["nang_cap"]]
    if len(pb) - 1 != len(nang):
        sai.append(f"so phien ban moi {len(pb) - 1} != so lan nang cap {len(nang)}")
    for d in nang:
        if d["trang_thai"] != "QUA":
            sai.append(f"khoan 1: {d['ma']} nang cap khi trang thai {d['trang_thai']}")
    for d in vong["doc"]:
        if d["trang_thai"] == "QUA" and not d["nang_cap"] and len(pb) < 2:
            sai.append(f"khoan 1: {d['ma']} QUA ma khong co phien ban moi")
    for ban in pb[1:]:
        ma = ban["ma_ung_vien"]
        if ma not in so_uv or ban["spec"] != so_uv[ma]["spec"]:
            sai.append(f"khoan 2: spec phien ban {ban['so']} khac spec da khai cua {ma}")
        doc_ma = [d for d in vong["doc"] if d["ma"] == ma]
        if len(doc_ma) != 1 or ban["phien_doc"] != doc_ma[0]["phien_doc"]:
            sai.append(f"khoan 3: phien doc cua phien ban {ban['so']} khong khop lan doc cua {ma}")
        if ban["hieu_luc_tu_phien"] != ban["phien_doc"] + 1:
            sai.append(f"khoan 3: hieu luc {ban['hieu_luc_tu_phien']} != phien doc {ban['phien_doc']} + 1")
    if len(pb) > 1:
        ban = pb[-1]
        chi_so = {str(n)[:10]: i for i, n in enumerate(ngay)}
        try:
            moi = V.ap_phien_ban(dong, vong["so_phien_ban"], ngay)
        except (ValueError, KeyError) as e:     # một phiên bản không áp được là vi phạm khoản 4, không phải lý do làm sập cả lượt chạy
            return [*sai, f"khoan 4: ap_phien_ban no: {e}"]
        lech = 0
        for r0, r1 in zip(dong, moi):
            t = chi_so[str(r0["signal_date"])[:10]]
            if t < ban["hieu_luc_tu_phien"]:
                lech += r1["score"] != r0["score"]
                continue
            tp = json.loads(r0["components"])
            x = math.fsum(float(w) * float(tp[k]) for k, w in ban["spec"]["trong_so"].items())
            ky_vong = int(x)
            gan_bien = abs(x - round(x)) < 1e-9
            if r1["score"] != ky_vong and not (gan_bien and abs(r1["score"] - ky_vong) == 1):
                lech += 1
        if lech:
            sai.append(f"khoan 4: {lech} dong co diem khong dung")
    return sai


def _t():
    return time.perf_counter()


def chay_mot_thi_truong_tang1(luong: int, phep, ten_o: str, muc: float, chi_so: int, so_hoan_vi: int = cx.SO_HOAN_VI) -> dict:
    """MỘT thị trường Tầng 1: sinh → bộ ba (K = 3) → chuỗi (+ C1) → RỒI oracle. Trả bản ghi JSON được."""
    kiem_luong_chinh_thuc(luong, phep)
    kappa = doc_kappa_muc(muc)
    t0 = _t()
    tt = T.sinh_thi_truong(luong, chi_so, kappa, co_su_that=False)
    dong = tt.dong_quyet_dinh()
    ngay = list(tt.ngay)
    giay = {"sinh": _t() - t0}
    t1 = _t()
    bang_gia = {"gia": tt.gia, "keo_luc": keo_luc_gia(tt.ngay[-1]), "nguon": {m: "vci" for m in tt.ma}}
    r = cx.cham(dong, so_ung_vien_bo_ba(), bang_gia, cx.HAT_RNG, so_hoan_vi)
    bo_ba = bo_ba_tang1_ket_qua(r)
    giay["bo_ba"] = _t() - t1
    t2 = _t()
    vong = V.chay_vong(dong, tt.gia, so_hoan_vi=so_hoan_vi)
    c1 = kiem_c1(vong, dong, ngay)
    giay["chuoi"] = _t() - t2
    t3 = _t()
    su_that = T.tinh_su_that(luong, chi_so, kappa)       # oracle: SAU khi cả hai thủ tục đã quyết
    giay["oracle"] = _t() - t3
    ten_f = sorted(T.ho_spec_f())
    top_f = sorted(ten_f, key=lambda t: (-su_that["spec"][t]["delta_ic"], t))[0]
    tv = vong["tien_ve_truoc"]
    return {"chi_so": int(chi_so), "dg": _bam(dong, tt.gia), "nguong": float(r["nguong"]), "bo_ba": bo_ba,
            "chuoi": {"khai": list(vong["de_xuat"]["da_chon"]), "ket_cuc": vong["ket_cuc"], "trang_thai": vong["trang_thai"],
                      "doc": [{"ma": d["ma"], "phien_doc": d["phien_doc"], "tt": d["trang_thai"],
                               "p": d["p"], "delta": d["delta"]} for d in vong["doc"]],
                      "tien": None if tv is None else {"delta_ic": tv["delta_ic"], "du_cua_so": tv["du_cua_so"], "n_phien": tv["n_phien"]},
                      "c1": c1},
            "oracle": {"top_f": top_f, "spec": {t: [v["delta_ic"], v["se_mc"]] for t, v in su_that["spec"].items()}},
            "giay": {k: round(v, 3) for k, v in giay.items()}}


def tai_lap_sinh(luong: int, phep, tang: int, muc: float, chi_so: int) -> str:
    """Sinh lại dữ liệu của một thị trường và trả băm (chỉ để so bit với bản ghi: tiêu chí máy đo 'tái lập hạt')."""
    kiem_luong_chinh_thuc(luong, phep)
    kappa = doc_kappa_muc(muc)
    if tang == 1:
        tt = T.sinh_thi_truong(luong, chi_so, kappa, co_su_that=False)
        return _bam(tt.dong_quyet_dinh(), tt.gia)
    return _bam_khung(G.sinh_thi_truong_2(luong, chi_so, kappa))


def so_ung_vien_bo_ba_tang2() -> dict:
    """Sổ GIẢ của bộ ba Tầng 2: G′ = `bo_momentum_score`, Z = `doi_cho_trend_sr`, H = `bo_volume_score`, khai ở ba tháng liên tiếp
    của `dong_thoi_gian_2()`. Tên khoá G′ → `G'`-không-dấu `Gp` để không lẫn với G của Tầng 1."""
    ngay = G.dong_thoi_gian_2()["khai_ngay"]
    ho = T.ho_spec_oracle()
    ten_spec = {"Gp": TEN_SPEC_GP, "Z": T.TEN_SPEC_Z, "H": T.TEN_SPEC_H}
    so = {"ung_vien": {ten: {"khai_ngay": ngay[i], "mo_ta": f"bo ba tang 2 {ten}", "ly_do": f"bo ba tang 2 {ten}",
                             "qua_sang": None, "spec": ho[ten_spec[ten]]} for i, ten in enumerate(("Gp", "Z", "H"))}}
    cb.kiem_so_ung_vien(so)
    return so


TEN_SPEC_GP = "bo_momentum_score"   # G′ của Tầng 2 (mục 19.8 khoản 1): cố định, KHÔNG đổi sau khi nhìn số


def chay_mot_thi_truong_tang2(luong: int, phep, ten_o: str, muc: float, chi_so: int, so_hoan_vi: int = cx.SO_HOAN_VI,
                              co_p2: bool = True) -> dict:
    """MỘT thị trường Tầng 2: sinh khung OHLCV → chấm 60 mã bằng `_analyze` THẬT (một tiến trình) → P1 → bộ ba (G′ · Z · H, K = 3) →
    chuỗi (+ C1) → P3 → P2 (chạy đường thật và phát lại; tuỳ chọn chỉ ở dòng thử)."""
    kiem_luong_chinh_thuc(luong, phep)
    kappa = doc_kappa_muc(muc)
    giay: dict = {}
    t0 = _t()
    tt = G.sinh_thi_truong_2(luong, chi_so, kappa)
    dg = _bam_khung(tt)
    giay["sinh"] = _t() - t0
    t1 = _t()
    theo_ma = {m: G.cham_diem_theo_ma(tt, m) for m in tt.ma}
    dong, gia = noi_dong_va_gia(tt, theo_ma)
    giay["cham"] = _t() - t1
    p1 = G.kiem_p1(tt, dong, len(tt.ma), tt.so_phien)
    dq_khong_ok = sum(1 for d in dong if d["data_quality"] != "OK")
    p1_khac = [s for s in p1 if not s.startswith("data_quality")]
    t2 = _t()
    ngay = [str(n) for n in gia.index]
    r = cx.cham(dong, so_ung_vien_bo_ba_tang2(), V.bang_gia_gia(gia), cx.HAT_RNG, so_hoan_vi)
    bo_ba = {}
    for ten in ("Gp", "Z", "H"):
        c = r["chi_tiet"][ten]
        bo_ba[ten] = {"tt": c["trang_thai"], "p": float(c["p"]), "delta": float(c["delta"]), "n_phien": int(c["n_phien"]), "n_ma": int(c["n_ma"])}
    giay["bo_ba"] = _t() - t2
    t3 = _t()
    vong = V.chay_vong(dong, gia, so_hoan_vi=so_hoan_vi)
    c1 = kiem_c1(vong, dong, ngay)
    giay["chuoi"] = _t() - t3
    ic = G.ic_thanh_phan(tt, dong)
    p2 = None
    if co_p2:
        t4 = _t()
        kq = G.chay_that_va_phat_lai(tt, dong_quyet_dinh_san=dong)
        p2 = {"so_khac": len(kq["khac"]), "so_diem_lech": len(kq["diem_lech"]), "so_lenh_that": len(kq["thuc"]),
              "so_lenh_phat": len(kq["phat"]), "bi_chan_vni": int(kq["bi_chan_vni"]), "so_diem_so_duoc": int(kq["so_diem_so_duoc"])}
        giay["p2"] = _t() - t4
    tv = vong["tien_ve_truoc"]
    return {"chi_so": int(chi_so), "dg_sinh": dg, "dg": _bam(dong), "nguong": float(r["nguong"]), "bo_ba": bo_ba,
            "p1": {"so_vi_pham": len(p1_khac), "vi_pham_dau": p1_khac[:3], "dq_khong_ok": int(dq_khong_ok), "so_dong": len(dong)},
            "p2": p2, "p3": {"ic_volume": float(ic["ic"]["volume_score"]), "so_cap": int(ic["so_cap"])},
            "chuoi": {"khai": list(vong["de_xuat"]["da_chon"]), "ket_cuc": vong["ket_cuc"], "trang_thai": vong["trang_thai"],
                      "tien": None if tv is None else {"delta_ic": tv["delta_ic"], "du_cua_so": tv["du_cua_so"], "n_phien": tv["n_phien"]},
                      "c1": c1},
            "giay": {k: round(v, 3) for k, v in giay.items()}}


# ═════════════════════════════════════════════════════════════════════════════
# THỊ TRƯỜNG NULL CÓ NHỚ (ĐO 38, dòng 9): sinh · bộ ba · chuỗi · RỒI oracle `tinh_su_that_m`
# ═════════════════════════════════════════════════════════════════════════════

def bo_ba_nho_ket_qua(r: dict) -> dict:
    """Như `bo_ba_tang1_ket_qua` nhưng giữ thêm `z` và `sd_null` (= độ lệch chuẩn của chính 2.000 giá trị hoán vị mã mà `z` chia cho): hai thứ cần để tính z′
    SAU khi oracle đã nói. Cặp chưa phán (không có `ket`) thì không có hai khoá ấy."""
    ra = {}
    for ten in ("G", "Z", "H"):
        c = r["chi_tiet"][ten]
        d = {"tt": c["trang_thai"], "p": float(c["p"]), "delta": float(c["delta"]), "n_phien": int(c["n_phien"]), "n_ma": int(c["n_ma"])}
        ket = c["ket"]
        if ket is not None:
            d["z"] = float(ket["z"])
            d["sd_null"] = float(np.std(ket["null"]))
        ra[ten] = d
    return ra


def chay_mot_thi_truong_m(luong: int, phep, ten_o: str, muc: float, chi_so: int, so_hoan_vi: int = cx.SO_HOAN_VI) -> dict:
    """MỘT thị trường NULL-M (dòng 9, Tầng 1): sinh bằng `sinh_thi_truong_m` với κ_d của bản ghi hiệu chuẩn → bộ ba (K = 3) → chuỗi (+ C1) → RỒI oracle
    `tinh_su_that_m` của CHÍNH thị trường ấy (oracle cũ rút mẫu dài không có nhân tố ngành, không dùng được). `muc` không dùng (NULL-M không có mức MDE)."""
    kiem_luong_chinh_thuc(luong, phep)
    kappa_d = doc_kappa_d()
    t0 = _t()
    tt = T.sinh_thi_truong_m(luong, chi_so, kappa_d, co_su_that=False)
    dong = tt.dong_quyet_dinh()
    ngay = list(tt.ngay)
    giay = {"sinh": _t() - t0}
    t1 = _t()
    bang_gia = {"gia": tt.gia, "keo_luc": keo_luc_gia(tt.ngay[-1]), "nguon": {m: "vci" for m in tt.ma}}
    r = cx.cham(dong, so_ung_vien_bo_ba(), bang_gia, cx.HAT_RNG, so_hoan_vi)
    bo_ba = bo_ba_nho_ket_qua(r)
    giay["bo_ba"] = _t() - t1
    t2 = _t()
    vong = V.chay_vong(dong, tt.gia, so_hoan_vi=so_hoan_vi)
    c1 = kiem_c1(vong, dong, ngay)
    giay["chuoi"] = _t() - t2
    t3 = _t()
    su_that = T.tinh_su_that_m(luong, chi_so, kappa_d)       # oracle: SAU khi cả hai thủ tục đã quyết
    giay["oracle"] = _t() - t3
    ten_f = sorted(T.ho_spec_f())
    top_f = sorted(ten_f, key=lambda t: (-su_that["spec"][t]["delta_ic"], t))[0]
    tv = vong["tien_ve_truoc"]
    return {"chi_so": int(chi_so), "dg": _bam(dong, tt.gia), "nguong": float(r["nguong"]), "bo_ba": bo_ba,
            "chuoi": {"khai": list(vong["de_xuat"]["da_chon"]), "ket_cuc": vong["ket_cuc"], "trang_thai": vong["trang_thai"],
                      "doc": [{"ma": d["ma"], "phien_doc": d["phien_doc"], "tt": d["trang_thai"],
                               "p": d["p"], "delta": d["delta"]} for d in vong["doc"]],
                      "tien": None if tv is None else {"delta_ic": tv["delta_ic"], "du_cua_so": tv["du_cua_so"], "n_phien": tv["n_phien"]},
                      "c1": c1},
            "oracle": {"top_f": top_f, "ic_da_ghi": float(su_that["ic_da_ghi"]), "spec": {t: [v["delta_ic"], v["se_mc"]] for t, v in su_that["spec"].items()}},
            "giay": {k: round(v, 3) for k, v in giay.items()}}


def tai_lap_sinh_m(luong: int, phep, chi_so: int) -> str:
    """Sinh lại dữ liệu của một thị trường NULL-M và trả băm (so bit với bản ghi: tiêu chí máy đo 'tái lập hạt')."""
    kiem_luong_chinh_thuc(luong, phep)
    tt = T.sinh_thi_truong_m(luong, chi_so, doc_kappa_d(), co_su_that=False)
    return _bam(tt.dong_quyet_dinh(), tt.gia)


def phi_nghich(p: float) -> float:
    """Φ⁻¹(p) của chuẩn tắc, bằng chia đôi trên `math.erf` (chính xác tới ~1e-12; dụng cụ này không nhập thư viện thống kê)."""
    if not 0.0 < p < 1.0:
        raise ValueError(f"p phai trong (0, 1), nhan {p!r}")
    lo, hi = -12.0, 12.0
    for _ in range(200):
        giua = 0.5 * (lo + hi)
        if 0.5 * (1.0 + math.erf(giua / math.sqrt(2.0))) < p:
            lo = giua
        else:
            hi = giua
    return 0.5 * (lo + hi)


def z_phay(delta, delta_that, sd_null):
    """z′ = (Δ − ΔIC_true) / σ_hoán-vị (mục 21.7 của đặc tả): Δ quan sát, ΔIC_true của oracle CHÍNH thị trường ấy, σ_hoán-vị = `sd_null`. Không tính được
    (thiếu một thành phần, hay σ không dương) thì None."""
    if delta is None or delta_that is None or sd_null is None or not sd_null > 0.0:
        return None
    return (delta - delta_that) / sd_null


def _tom_tat(x: list[float]) -> dict:
    a = np.asarray(x, float)
    return {"n": int(a.size), "trung_binh": float(a.mean()) if a.size else None, "sd": float(a.std(ddof=1)) if a.size > 1 else None}


def danh_gia_nho(thi_truong: list[dict]) -> dict:
    """Đọc dòng 9 (NULL-M, R thị trường): M1 và M2 cùng ba khối BÁO KÈM của M1 và đuôi z′. Hàm thuần của bản ghi.
    M1: số thị trường có ≥ 1 *xác nhận nhầm* = ứng viên G · Z · H bị `QUA` mà ΔIC_true (oracle của CHÍNH thị trường) ≤ 0.
    M2: độ lệch chuẩn GỘP (`ddof=1`) của z′ trên mọi cặp (thị trường × ứng viên); cặp σ = 0 hay chưa phán bị loại và đếm."""
    ten = {"G": T.TEN_SPEC_G, "Z": T.TEN_SPEC_Z, "H": T.TEN_SPEC_H}
    nham = hai_phia = nang_cap = c1 = 0
    z_phay_cap: list[float] = []
    z_ca = {k: [] for k in ten}
    delta_that = {k: [] for k in ten}
    loai = 0
    for m in thi_truong:
        bo_ba, spec = m["bo_ba"], m["oracle"]["spec"]
        if any(bo_ba[k]["tt"] == "QUA" and spec[ten[k]][0] <= 0.0 for k in ten):
            nham += 1
        if any(_bao_dong(bo_ba[k], m["nguong"]) for k in ten):
            hai_phia += 1
        if m["chuoi"]["ket_cuc"] == V.KET_CUC_NANG_CAP:
            nang_cap += 1
        c1 += len(m["chuoi"]["c1"])
        for k in ten:
            c, dt = bo_ba[k], spec[ten[k]][0]
            delta_that[k].append(dt)
            if "z" in c:
                z_ca[k].append(c["z"])
            zp = z_phay(c["delta"], dt, c["sd_null"] if "sd_null" in c else None)
            if zp is None:
                loai += 1
            else:
                z_phay_cap.append(zp)
    R = len(thi_truong)
    z_c = phi_nghich(1.0 - 0.05 / (2 * K_BO_BA))
    cap = np.asarray(z_phay_cap, float)
    tren = int((cap > z_c).sum())
    sd_gop = float(cap.std(ddof=1)) if cap.size > 1 else None
    return {"R": R, "M1": nham, "M2": sd_gop, "M2_n": int(cap.size), "so_cap_loai": loai, "so_cap": K_BO_BA * R, "C1_dong_9": c1,
            "bao_cao": {"M1_bao_dong_hai_phia": {"so_thi_truong": hai_phia, "R": R, "ty_le": hai_phia / R if R else None},
                        "M1_nang_cap_ma": {"so_thi_truong": nang_cap, "R": R, "ty_le": nang_cap / R if R else None},
                        "M1_z": {"gop": _tom_tat([z for k in ten for z in z_ca[k]]), **{k: _tom_tat(z_ca[k]) for k in ten}},
                        "M2_duoi": {"z_c": z_c, "n": int(cap.size), "so_cap_tren": tren, "ty_le": tren / cap.size if cap.size else None},
                        "M2_loai": {"so_cap_loai": loai, "so_cap": K_BO_BA * R, "ty_le": loai / (K_BO_BA * R) if R else None},
                        "M_delta_that_tb": {k: float(np.mean(delta_that[k])) if delta_that[k] else None for k in ten}}}


# ═════════════════════════════════════════════════════════════════════════════
# TỔNG HỢP VÀ ĐỌC KẾT CỤC (mục 6)
# ═════════════════════════════════════════════════════════════════════════════

def _bao_dong(tc: dict, nguong: float) -> bool:
    return tc["p"] < nguong


def thong_ke_may_do_null(thi_truong: list[dict]) -> dict:
    """z = ΔIC_true / sai số MC của MỌI (thị trường NULL × 12 spec): tỷ lệ ô trong 2 sai số, sd(z), trung bình(z)."""
    z = []
    for m in thi_truong:
        for d, se in m["oracle"]["spec"].values():
            z.append(d / se)
    z = np.asarray(z, float)
    return {"so_o": int(z.size), "ty_le_trong_2se": float((np.abs(z) < 2.0).mean()), "sd_z": float(z.std(ddof=1)),
            "trung_binh_z": float(z.mean())}


def bootstrap_c2(delta: list[float]) -> dict:
    """C2: cận dưới KTC 95% (bootstrap qua thị trường, `SO_BOOTSTRAP_C2` lần, hạt `HAT_BOOTSTRAP_C2`) của ΔIC thực hiện trung bình."""
    d = np.asarray(delta, float)
    if d.size < 2:
        return {"n": int(d.size), "trung_binh": float(d.mean()) if d.size else None, "can_duoi": None}
    rng = np.random.default_rng(HAT_BOOTSTRAP_C2)
    tb = d[rng.integers(0, d.size, size=(SO_BOOTSTRAP_C2, d.size))].mean(axis=1)
    return {"n": int(d.size), "trung_binh": float(d.mean()), "can_duoi": float(np.percentile(tb, 2.5))}


def tong_hop(ket: dict, hieu_chuan: dict, g_phay: dict | None, do: int | None = None, hc38: dict | None = None) -> dict:
    """Đọc kết cục từ bản ghi các dòng hạt của MỘT ĐO, theo ĐÚNG bảng đã ký. Hàm thuần của `ket` + các bản ghi dòng 1. Thiếu dòng nào thì
    `thieu` khác rỗng và kết cục là KHÔNG ĐỌC ĐƯỢC (chưa đủ dữ liệu). Trả `{"tieu_chi": {...}, "ket_cuc": ..., "truot": [...], "khong_doc": [...]}`.

    ĐO 37 (mặc định): dòng 2 · 3 · 4; A0 ≤ `NGUONG["A0"]` và dải PT từ `g_phay`. ĐO 38 (`do=38`): dòng 6 · 7 · 8 · 9; A0 và dải PT từ `hc38` (kết quả của
    `kiem_hieu_chuan_do38`, đọc từ bản ghi hiệu chuẩn, không gõ tay), thêm M1 · M2 trên dòng 9; `g_phay` không dùng."""
    cfg = cau_hinh_do(do)
    nguong = dict(NGUONG)
    if cfg.can_hieu_chuan:
        if hc38 is None:
            raise ValueError(f"ĐO {cfg.so_do} can ban ghi hieu chuan (hc38): A0 va dai PT doc tu do, khong tu hang so")
        nguong["A0"] = int(hc38["nguong_A0"])
        thap, cao = hc38["dai_pt"]
    else:
        thap, cao = g_phay["dai_thap"], g_phay["dai_cao"]
    l_loi, l_null, l_t2 = cfg.luong_tong_hop[:3]
    l_nho = cfg.luong_tong_hop[3] if len(cfg.luong_tong_hop) > 3 else None
    cac = ket.get("cac_luong", {})
    thieu = [str(l) for l in cfg.luong_tong_hop if str(l) not in cac or cac[str(l)].get("trang_thai") != "XONG"]
    out: dict = {"thieu": thieu, "tieu_chi": {}, "bao_cao": {}}
    truot: list[str] = []
    khong_doc: list[str] = []
    if thieu:
        out.update({"ket_cuc": "KHONG_DOC_DUOC", "truot": truot, "khong_doc": [f"chua du dong hat: {', '.join(thieu)}"]})
        return out
    o2, o3, o4 = cac[str(l_loi)]["o"], cac[str(l_null)]["o"], cac[str(l_t2)]["o"]
    tc = out["tieu_chi"]

    def dem(lst, f):
        return int(sum(1 for m in lst if f(m)))

    def chot(ma, gia_tri, nguong, dat, **them):
        tc[ma] = {"gia_tri": gia_tri, "nguong": nguong, "dat": bool(dat), **them}
        if not dat:
            truot.append(ma)

    x2, x1, x05, null3 = o2["2x"]["thi_truong"], o2["1x"]["thi_truong"], o2["0.5x"]["thi_truong"], o3["NULL"]["thi_truong"]
    ngv = nguong   # `chot` có tham số tên `nguong` (chuỗi mô tả); `ngv` là dict ngưỡng của ĐO này
    chot("A", dem(x2, lambda m: m["oracle"]["top_f"] in m["chuoi"]["khai"]), f">= {ngv['A']}", dem(x2, lambda m: m["oracle"]["top_f"] in m["chuoi"]["khai"]) >= ngv["A"], R=len(x2))
    chot("A0", dem(null3, lambda m: T.TEN_SPEC_G in m["chuoi"]["khai"]), f"<= {ngv['A0']}", dem(null3, lambda m: T.TEN_SPEC_G in m["chuoi"]["khai"]) <= ngv["A0"], R=len(null3))
    b1 = dem(null3, lambda m: any(_bao_dong(m["bo_ba"][t], m["nguong"]) for t in ("G", "Z", "H")))
    chot("B1", b1, f"<= {ngv['B1']}", b1 <= ngv["B1"], R=len(null3))
    b2 = dem(x2, lambda m: m["bo_ba"]["G"]["tt"] == "QUA")
    chot("B2", b2, f">= {ngv['B2']}", b2 >= ngv["B2"], R=len(x2))
    b3 = dem(x2, lambda m: _bao_dong(m["bo_ba"]["Z"], m["nguong"]))
    chot("B3", b3, f"<= {ngv['B3']}", b3 <= ngv["B3"], R=len(x2))
    b4 = sum(dem(l, lambda m: m["bo_ba"]["H"]["tt"] == "QUA") for l in (x05, x1, x2))
    chot("B4", b4, "== 0", b4 == 0, R=len(x05) + len(x1) + len(x2))
    tat_ca = [m for l in (x05, x1, x2, null3, o4["NULL"]["thi_truong"], o4["2x"]["thi_truong"]) for m in l]
    c1 = sum(len(m["chuoi"]["c1"]) for m in tat_ca)
    chot("C1", c1, "== 0", c1 == 0, R=len(tat_ca))
    c2 = bootstrap_c2([m["chuoi"]["tien"]["delta_ic"] for m in x2
                       if m["chuoi"]["ket_cuc"] == V.KET_CUC_NANG_CAP and m["chuoi"]["tien"] is not None and m["chuoi"]["tien"]["du_cua_so"]])
    chot("C2", c2["can_duoi"], "can duoi KTC 95% > 0", c2["can_duoi"] is not None and c2["can_duoi"] > 0, **{k: c2[k] for k in ("n", "trung_binh")})
    c3 = dem(null3, lambda m: m["chuoi"]["ket_cuc"] == V.KET_CUC_NANG_CAP)
    chot("C3", c3, f"<= {ngv['C3']}", c3 <= ngv["C3"], R=len(null3))
    n4, x4 = o4["NULL"]["thi_truong"], o4["2x"]["thi_truong"]
    p1 = sum(m["p1"]["so_vi_pham"] for m in n4 + x4)
    chot("P1", p1, "== 0", p1 == 0, R=len(n4) + len(x4))
    p2 = None if any(m["p2"] is None for m in n4 + x4) else sum(m["p2"]["so_khac"] + m["p2"]["so_diem_lech"] for m in n4 + x4)
    chot("P2", p2, "== 0", p2 == 0, R=len(n4) + len(x4))
    p3 = dem(x4, lambda m: m["p3"]["ic_volume"] > 0)
    chot("P3", p3, f">= {ngv['P3']}", p3 >= ngv["P3"], R=len(x4))
    p4 = cac[str(l_t2)].get("p4")
    chot("P4", None if p4 is None else p4["ma_thoat"], "gac G1-G5 xanh (ma thoat 0)", p4 is not None and p4["ma_thoat"] == 0)
    pt_null = dem(n4, lambda m: any(_bao_dong(m["bo_ba"][t], m["nguong"]) for t in ("Gp", "Z", "H")))
    pt_g = dem(x4, lambda m: m["bo_ba"]["Gp"]["tt"] == "QUA")
    chot("PT", {"bao_dong_NULL": pt_null, "Gp_QUA_2x": pt_g}, f"NULL <= {ngv['PT_NULL']} va Gp QUA trong [{thap} ; {cao}]",
         pt_null <= ngv["PT_NULL"] and thap <= pt_g <= cao, R=len(n4))
    nho = None
    if l_nho is not None:     # ĐO 38: M1 · M2 trên dòng 9 (NULL-M)
        nho = danh_gia_nho(cac[str(l_nho)]["o"][TEN_O_NULL_M]["thi_truong"])
        chot("M1", nho["M1"], f"<= {NGUONG_M['M1']}", nho["M1"] <= NGUONG_M["M1"], R=nho["R"])
        m2_lo, m2_hi = NGUONG_M["M2_dai"]
        chot("M2", nho["M2"], f"sd z' gop trong [{m2_lo} ; {m2_hi}]", nho["M2"] is not None and m2_lo <= nho["M2"] <= m2_hi, R=nho["M2_n"])
        out["bao_cao"].update(nho["bao_cao"])
        out["bao_cao"]["C1_dong_9"] = nho["C1_dong_9"]
        if nho["R"] == 0 or nho["so_cap_loai"] > NGUONG_M["ty_le_loai_toi_da"] * nho["so_cap"]:
            khong_doc.append(f"M2: {nho['so_cap_loai']}/{nho['so_cap']} cap (thi truong x ung vien) bi loai vi sigma hoan vi = 0 hay chua phan (> {NGUONG_M['ty_le_loai_toi_da']:.0%})")
    # ── máy đo: KHÔNG ĐỌC ĐƯỢC ──
    st = thong_ke_may_do_null(null3)
    tiu = MAY_DO_NULL
    if not (st["ty_le_trong_2se"] >= tiu["ty_le_o_trong_2se_toi_thieu"] and tiu["sd_z"][0] <= st["sd_z"] <= tiu["sd_z"][1]
            and abs(st["trung_binh_z"]) < tiu["trung_binh_z_toi_da"]):
        khong_doc.append("oracle o NULL ngoai tieu chi ty le (muc 15 khoan 8)")
    out["bao_cao"]["may_do_null"] = st
    for ten_o, lst, muc in (("0.5x", x05, 0.5), ("1x", x1, 1.0), ("2x", x2, 2.0)):
        m = next(m for m in hieu_chuan["muc"] if abs(m["he_so"] - muc) < 1e-9)
        tb = float(np.mean([a["oracle"]["spec"][T.TEN_SPEC_G][0] for a in lst]))
        lech = (tb - m["muc_tieu_delta_ic"]) / m["muc_tieu_delta_ic"]
        out["bao_cao"][f"delta_G_{ten_o}"] = {"trung_binh": tb, "muc_tieu": m["muc_tieu_delta_ic"], "lech": lech}
        if abs(lech) > DUNG_SAI_MUC:
            khong_doc.append(f"delta_ic_true(G) o muc {ten_o} lech {lech:+.1%} so voi muc tieu (> {DUNG_SAI_MUC:.0%})")
    g_null = [a["oracle"]["spec"][T.TEN_SPEC_G][0] for a in null3]
    se_tb = float(np.std(g_null, ddof=1) / math.sqrt(len(g_null)))
    out["bao_cao"]["delta_G_NULL"] = {"trung_binh": float(np.mean(g_null)), "se_tb": se_tb}
    if abs(float(np.mean(g_null))) >= 2.0 * se_tb:
        khong_doc.append("delta_ic_true(G) o NULL ngoai hai sai so cua trung binh")
    tai = []
    cac_o = [(l_loi, "0.5x"), (l_loi, "1x"), (l_loi, "2x"), (l_null, "NULL"), (l_t2, "NULL"), (l_t2, "2x")]
    if l_nho is not None:
        cac_o.append((l_nho, TEN_O_NULL_M))
    for l, ten in cac_o:
        o = cac[str(l)]["o"][ten]
        if o.get("tai_lap") != "KHOP":
            tai.append(f"{l}/{ten}")
    if tai:
        khong_doc.append(f"tai lap hat khong bang bit o: {', '.join(tai)}")
    dq = sum(m["p1"]["dq_khong_ok"] for m in n4 + x4)
    if dq:
        khong_doc.append(f"bo sinh Tang 2: {dq} dong data_quality khac OK")
    k1 = hieu_chuan["kiem_1x_trong_dai_99"]["dai_99_quanh_80"]
    n1 = dem(x1, lambda m: m["bo_ba"]["G"]["tt"] == "QUA")
    out["bao_cao"]["bat_G_1x"] = {"n_QUA": n1, "R": len(x1), "dai_99": k1}
    if not (k1[0] <= n1 <= k1[1]):
        khong_doc.append(f"1x: bat G {n1}/{len(x1)} ngoai dai 99% {k1}")
    for ten, lst in (("0.5x", x05), ("1x", x1), ("2x", x2)):
        out["bao_cao"][f"duong_cong_{ten}"] = {"G_QUA": dem(lst, lambda m: m["bo_ba"]["G"]["tt"] == "QUA"),
                                               "tim_ra": dem(lst, lambda m: m["oracle"]["top_f"] in m["chuoi"]["khai"]),
                                               "nang_cap": dem(lst, lambda m: m["chuoi"]["ket_cuc"] == V.KET_CUC_NANG_CAP), "R": len(lst)}
    out["bao_cao"]["B1_ty_le"] = b1 / len(null3)
    out["bao_cao"]["B1_thieu_nhay"] = bool(b1 / len(null3) < 0.025)
    nc_null = [m["chuoi"]["tien"]["delta_ic"] for m in null3 if m["chuoi"]["ket_cuc"] == V.KET_CUC_NANG_CAP and m["chuoi"]["tien"] is not None]
    out["bao_cao"]["delta_ic_thuc_hien_NULL"] = {"n": len(nc_null), "trung_binh": float(np.mean(nc_null)) if nc_null else None}
    out["bao_cao"]["tang2_Z_H_2x"] = {"Z_bao_dong": dem(x4, lambda m: _bao_dong(m["bo_ba"]["Z"], m["nguong"])),
                                      "H_QUA": dem(x4, lambda m: m["bo_ba"]["H"]["tt"] == "QUA"),
                                      "H_bao_dong": dem(x4, lambda m: _bao_dong(m["bo_ba"]["H"], m["nguong"])), "R": len(x4)}
    if khong_doc:
        out["ket_cuc"] = "KHONG_DOC_DUOC"
    elif truot:
        out["ket_cuc"] = "TRUOT"
    else:
        out["ket_cuc"] = "DAT"
    out["truot"], out["khong_doc"] = truot, khong_doc
    return out


def in_ket_cuc(kc: dict) -> list[str]:
    ra = [f"KẾT CỤC: {kc['ket_cuc']}"]
    if kc["thieu"]:
        ra.append(f"  chưa đủ dòng hạt: {', '.join(kc['thieu'])}")
    for ma, v in kc["tieu_chi"].items():
        ra.append(f"  {ma:<3} {'ĐẠT' if v['dat'] else 'TRƯỢT':<6} giá trị {v['gia_tri']} (ngưỡng {v['nguong']})")
    for s in kc["khong_doc"]:
        ra.append(f"  KHÔNG ĐỌC ĐƯỢC: {s}")
    if kc["truot"]:
        ra.append(f"  TRƯỢT ở: {', '.join(kc['truot'])}")
    if kc["bao_cao"]:
        ra.append("  BÁO CÁO (không phán):")
        for k, v in kc["bao_cao"].items():
            ra.append(f"    {k}: {json.dumps(v, ensure_ascii=False)}")
    return ra


# ═════════════════════════════════════════════════════════════════════════════
# CHẠY
# ═════════════════════════════════════════════════════════════════════════════

def _viec(a):
    """Việc của MỘT tiến trình: một thị trường. Kiểm cửa ngay trong `chay_mot_thi_truong_*` (giấy phép đi theo pickle)."""
    luong, phep, tang, ten_o, muc, chi_so, so_hoan_vi, co_p2 = a
    kiem_luong_chinh_thuc(luong, phep)
    if tang == 1:
        if ten_o == TEN_O_NULL_M:
            return ten_o, chay_mot_thi_truong_m(luong, phep, ten_o, muc, chi_so, so_hoan_vi)
        return ten_o, chay_mot_thi_truong_tang1(luong, phep, ten_o, muc, chi_so, so_hoan_vi)
    return ten_o, chay_mot_thi_truong_tang2(luong, phep, ten_o, muc, chi_so, so_hoan_vi, co_p2)


def _nap_va_an_toan():
    s = importlib.util.spec_from_file_location("va_an_toan_chay_chinh_thuc", DUONG_CONG_CU / "va_an_toan.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def ghi_ket_qua(ket: dict, duong: Path = DUONG_KET_QUA) -> None:
    _nap_va_an_toan().ghi(duong, json.dumps(ket, ensure_ascii=False, separators=(",", ":")) + "\n")


def chay_p4(lenh_py: str = sys.executable) -> dict:
    """P4: các gác G1–G5 của mục 7 xanh. Chạy các test mang tên `test_G1_` … `test_G5_` bằng pytest; trả mã thoát và dòng cuối."""
    cac = ["tests/test_vong_hoc_thi_truong_gia.py", "tests/test_tang2_thi_truong_gia.py", "tests/test_thi_truong_gia.py",
           "tests/test_san_dau.py", "tests/test_hieu_chuan_thi_truong_gia.py", "tests/test_chuan_bi_lat5_thi_truong_gia.py",
           "tests/test_chay_chinh_thuc_thi_truong_gia.py", "tests/test_chay_chinh_thuc_do38.py"]
    lenh = [lenh_py, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-k", "test_G1_ or test_G2_ or test_G3_ or test_G4_ or test_G5_", *cac]
    r = subprocess.run(lenh, cwd=str(GOC), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    dong = [s for s in r.stdout.strip().splitlines() if s.strip()]
    return {"lenh": " ".join(lenh[3:]), "ma_thoat": int(r.returncode), "dong_cuoi": dong[-1] if dong else ""}


def danh_sach_viec(luong: int, phep, so_hoan_vi: int, co_p2: bool, da_co: dict | None = None, ke_hoach=None) -> list[tuple]:
    kh = cau_hinh_do(None, luong).ke_hoach[luong] if ke_hoach is None else ke_hoach
    viec = []
    for ten, muc, dau, so in kh["o"]:
        xong = set() if da_co is None else {m["chi_so"] for m in da_co.get(ten, {}).get("thi_truong", [])}
        for chi_so in range(dau, dau + so):
            if chi_so not in xong:
                viec.append((luong, phep, kh["tang"], ten, muc, chi_so, so_hoan_vi, co_p2))
    return viec


def chay_luong(luong: int, phep, so_tien_trinh: int = 1, tiep_tuc: bool = False, luu_moi: int = 25, ra: Path = DUONG_KET_QUA,
               ke_hoach=None, so_hoan_vi: int = cx.SO_HOAN_VI, co_p2: bool = True, chay_p4_fn=chay_p4, lenh_text: str = "",
               in_tien_do: bool = True, ghi_fn=ghi_ket_qua, do: int | None = None) -> dict:
    """Chạy MỘT dòng hạt (đủ mọi ô), ghi từng đợt `luu_moi` thị trường vào `ra` (trạng thái DANG CHAY), xong thì XONG. Mỗi thị trường là
    hàm THUẦN của (dòng hạt, chỉ số, mức) nên chạy tiếp sau khi gián đoạn không chọn lại thứ gì. `do` = số ĐO (kế hoạch, BƯỚC ghi vào bản ghi đầu);
    không nêu thì suy từ dòng hạt, không suy được (dòng thử) thì ĐO 37."""
    kiem_luong_chinh_thuc(luong, phep)
    cfg = cau_hinh_do(do, luong)
    kh = cfg.ke_hoach[luong] if ke_hoach is None else ke_hoach
    ket = doc_ket_qua_hien_co(ra)             # LUÔN đọc bản đang có: ghi một dòng hạt không được đè mất dòng hạt khác
    if ket is None:
        ket = {"buoc": cfg.buoc_chay, "do": f"ĐO {cfg.so_do}", "cac_luong": {}}
    cu = ket["cac_luong"].get(str(luong))
    if cu is not None and (cu["trang_thai"] == "XONG" or not tiep_tuc):
        raise CongTu([f"dong hat {luong} da co trong {Path(ra).name} (trang thai {cu['trang_thai']}): khong ghi de"])
    if cu is None:
        cu = {"trang_thai": "DANG CHAY", "lenh": lenh_text, "tang": kh["tang"], "o": {}, "giay": 0.0,
              "git": {"head": getattr(phep, "head", ""), "origin_main": getattr(phep, "goc_main", ""), "sha_do": getattr(phep, "sha_do", "")},
              "moi_truong": {"python": platform.python_version(), "so_tien_trinh": so_tien_trinh}}
        for ten, muc, dau, so in kh["o"]:
            cu["o"][ten] = {"muc": muc, "kappa": doc_kappa_d() if ten == TEN_O_NULL_M else doc_kappa_muc(muc), "chi_so_dau": dau, "so": so, "thi_truong": []}
        ket["cac_luong"][str(luong)] = cu
    if luong == cfg.luong_tong_hop[2] and cu.get("p4") is None:   # dòng Tầng 2 (ĐO 37: 4; ĐO 38: 8) chạy P4 đúng MỘT lần
        cu["p4"] = chay_p4_fn()
    t0 = _t()
    viec = danh_sach_viec(luong, phep, so_hoan_vi, co_p2, cu["o"], kh)
    giay_truoc = float(cu["giay"])

    def luu(xong: bool):
        cu["giay"] = giay_truoc + (_t() - t0)
        for o in cu["o"].values():
            o["thi_truong"].sort(key=lambda m: m["chi_so"])
        cu["trang_thai"] = "XONG" if xong else "DANG CHAY"
        ghi_fn(ket, ra)

    def nhan(kq):
        ten, rec = kq
        cu["o"][ten]["thi_truong"].append(rec)

    xong_so = 0
    if so_tien_trinh > 1:
        with ProcessPoolExecutor(max_workers=so_tien_trinh) as pool:
            for kq in pool.map(_viec, viec, chunksize=1):
                nhan(kq)
                xong_so += 1
                if xong_so % luu_moi == 0:
                    luu(False)
                    if in_tien_do:
                        print(f"[{_t() - t0:8.1f}s] {xong_so}/{len(viec)}", flush=True)
    else:
        for a in viec:
            nhan(_viec(a))
            xong_so += 1
            if xong_so % luu_moi == 0:
                luu(False)
                if in_tien_do:
                    print(f"[{_t() - t0:8.1f}s] {xong_so}/{len(viec)}", flush=True)
    # tái lập hạt BẰNG BIT: sinh lại thị trường ĐẦU của mỗi ô và so băm
    for ten, muc, dau, so in kh["o"]:
        o = cu["o"][ten]
        moi = tai_lap_sinh_m(luong, phep, dau) if ten == TEN_O_NULL_M else tai_lap_sinh(luong, phep, kh["tang"], muc, dau)
        ban_ghi = next(m for m in o["thi_truong"] if m["chi_so"] == dau)
        goc = ban_ghi["dg"] if kh["tang"] == 1 else ban_ghi["dg_sinh"]
        o["tai_lap"] = "KHOP" if moi == goc else "LECH"
    luu(True)
    return ket


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--luong", type=int, default=None, help="dòng hạt của ĐO đã chọn (37: 2 · 3 · 4; 38: 6 · 7 · 8 · 9; qua cửa) hoặc 9001 (dòng thử)")
    ap.add_argument("--do", type=int, default=37, help="số ĐO: 37 (mặc định) hay 38; `--luong` phải thuộc ĐO này")
    ap.add_argument("--nho", action="store_true", help="CHỈ dòng thử 9001 và --do 38: chạy ô NULL-M (thị trường NULL có nhớ) thay cho các ô Tầng 1 thường")
    ap.add_argument("--ket-cuc", action="store_true", help="đọc kết cục từ file kết quả của ĐO đã chọn; không sinh thị trường nào")
    ap.add_argument("--so-tien-trinh", type=int, default=1)
    ap.add_argument("--tiep-tuc", action="store_true", help="chạy tiếp một dòng hạt đang dở")
    ap.add_argument("--tang", type=int, choices=(1, 2), default=None, help="CHỈ dòng thử 9001")
    ap.add_argument("--so-moi-o", type=int, default=1, help="CHỈ dòng thử 9001: số thị trường mỗi ô")
    ap.add_argument("--ra", default=None, help="CHỈ dòng thử 9001: file kết quả (không được là file chính thức)")
    ap.add_argument("--khong-p2", action="store_true", help="CHỈ dòng thử 9001 Tầng 2: bỏ P2 (đo chi phí riêng)")
    ap.add_argument("--so-hoan-vi", type=int, default=cx.SO_HOAN_VI, help="CHỈ dòng thử 9001")
    a = ap.parse_args(argv)
    if a.do not in CAU_HINH:
        ap.error(f"--do phai la mot trong {tuple(CAU_HINH)}, nhan {a.do}")
    cfg = CAU_HINH[a.do]
    if a.ket_cuc:
        ket = doc_ket_qua_hien_co() if cfg is DO_37 else doc_ket_qua_hien_co(cfg.duong_ket_qua)
        if ket is None:
            print(f"chua co {cfg.duong_ket_qua.relative_to(GOC).as_posix()}", file=sys.stderr)
            return 2
        hc_json = json.loads(DUONG_HIEU_CHUAN.read_text(encoding="utf-8"))
        if cfg.can_hieu_chuan:
            hc38 = doc_hieu_chuan_do38()
            if hc38 is None:
                print(f"ban ghi hieu chuan cua ĐO {cfg.so_do} vang hay chua dat: khong doc duoc A0 va dai PT", file=sys.stderr)
                return 2
            kc = tong_hop(ket, hc_json, None, do=cfg.so_do, hc38=hc38)
        else:
            kc = tong_hop(ket, hc_json, json.loads(DUONG_G_PHAY.read_text(encoding="utf-8")))
        print("\n".join(in_ket_cuc(kc)))
        return 0 if kc["ket_cuc"] == "DAT" else 1 if kc["ket_cuc"] == "TRUOT" else 2
    if a.luong is None:
        ap.error("can --luong hoac --ket-cuc")
    if a.luong == LUONG_THU:
        if a.tang is None or not a.ra:
            ap.error("dong thu 9001 can --tang va --ra <file>")
        ra = Path(a.ra).resolve()
        if ra in {c.duong_ket_qua.resolve() for c in CAU_HINH.values()}:
            ap.error("dong thu khong duoc ghi ra file chinh thuc")
        if a.nho:
            if not cfg.can_hieu_chuan or a.tang != 1:
                ap.error("--nho chi di voi --do 38 va --tang 1")
            o_mau = cfg.ke_hoach[cfg.luong_tong_hop[3]]["o"]
        else:
            o_mau = cfg.ke_hoach[cfg.luong_tong_hop[0]]["o"] + cfg.ke_hoach[cfg.luong_tong_hop[1]]["o"] if a.tang == 1 else cfg.ke_hoach[cfg.luong_tong_hop[2]]["o"]
        ke_hoach = {"tang": a.tang, "o": tuple((ten, muc, dau, a.so_moi_o) for ten, muc, dau, _so in o_mau)}
        t0 = _t()
        ket = chay_luong(LUONG_THU, None, a.so_tien_trinh, False, 1000, ra, ke_hoach, a.so_hoan_vi, not a.khong_p2,
                         lambda: {"lenh": "(dong thu)", "ma_thoat": 0, "dong_cuoi": ""}, lenh_text="dong thu 9001", do=cfg.so_do)
        giay = _t() - t0
        cu = ket["cac_luong"][str(LUONG_THU)]
        print(f"dòng thử 9001, Tầng {a.tang}, {a.so_moi_o} thị trường mỗi ô, {a.so_tien_trinh} tiến trình: {giay:.1f} s tường")
        for ten, o in cu["o"].items():
            for m in o["thi_truong"]:
                print(f"  ô {ten} chỉ số {m['chi_so']}: " + ", ".join(f"{k} {v:.1f}s" for k, v in m["giay"].items()))
        return 0
    if a.luong not in cfg.luong:
        print(f"dong hat {a.luong} khong chay duoc o ĐO {cfg.so_do} (chinh thuc: {cfg.luong}; thu: {LUONG_THU}; mot dong cua ĐO khac can --do cua no)", file=sys.stderr)
        return 2
    try:
        phep = kiem_cong(a.luong, git=git_that, tiep_tuc=a.tiep_tuc, do=cfg.so_do)
    except CongTu as e:
        print(f"CỬA TỪ CHỐI (ĐO {cfg.so_do}) — không sinh thị trường nào:", file=sys.stderr)
        for s in e.ly_do:
            print("  - " + s, file=sys.stderr)
        return 3
    chay_luong(a.luong, phep, a.so_tien_trinh, a.tiep_tuc, luu_moi=cfg.luu_moi_cua(a.luong), ra=cfg.duong_ket_qua, do=cfg.so_do,
               lenh_text=f"./.venv/Scripts/python.exe -X utf8 {lenh_chuan(a.luong, cfg.so_do)} --so-tien-trinh {a.so_tien_trinh}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
