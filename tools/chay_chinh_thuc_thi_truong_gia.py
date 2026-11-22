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
Chỉ ghi MỘT file chính thức (`docs/thi-truong-gia-ket-qua.json`) bằng `va_an_toan.ghi`. Không Sheets, không `*.db`, không mạng ngoài git.
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
        return self.luong in LUONG_CHINH_THUC and self.tem == _tem(self.luong, self.sha_do, self.head, self.goc_main)


def kiem_luong_chinh_thuc(luong, phep=None) -> None:
    """Cửa DUY NHẤT tới bộ sinh của dụng cụ này. 9001 qua tự do (dòng thử); 2 · 3 · 4 chỉ khi có `PhepChay` đúng dòng; MỌI dòng khác
    (kể cả 1 và 5, và kiểu lạ) nổ. Mọi hàm gọi bộ sinh phải gọi cửa này TRƯỚC (gác AST ở test)."""
    if isinstance(luong, bool) or not isinstance(luong, (int, np.integer)):
        raise ValueError(f"dong hat phai la so nguyen, nhan {luong!r}")
    luong = int(luong)
    if luong == LUONG_THU:
        return
    if luong in LUONG_KHONG_BAO_GIO:
        raise ValueError(f"dong hat {luong} bi chan vinh vien o dung cu nay (chan doan SAU khi da nhin ket qua, bat bien 7)")
    if luong not in LUONG_CHINH_THUC:
        raise ValueError(f"dong hat {luong} khong thuoc {LUONG_CHINH_THUC} va khong phai dong thu {LUONG_THU}")
    if not isinstance(phep, PhepChay) or phep.luong != luong or not phep.hop_le():
        raise CongTu([f"dong hat {luong} chi mo duoc qua kiem_cong (can giay phep dung dong hat, con nguyen ven)"])


def lenh_chuan(luong: int) -> str:
    """Phần lệnh CỐ ĐỊNH (không gồm `--so-tien-trinh`/`--tiep-tuc`, vốn không đổi kết quả) mà ĐO 37 phải NÊU nguyên văn."""
    return f"{TEN_DUNG_CU} --luong {int(luong)}"


def dong_ke_hoach(luong: int) -> str:
    """Dòng kế hoạch của dòng hạt, sinh từ `KE_HOACH` (không gõ tay): ĐO 37 phải NÊU nguyên văn dòng này."""
    k = KE_HOACH[int(luong)]
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
              van_ban_cay: str | None = None) -> PhepChay:
    """Cửa. Trả `PhepChay` nếu TẤT CẢ điều ở docstring đầu file đúng; ngược lại nổ `CongTu` với MỌI điều thiếu.
    `git(*đối số) -> (mã thoát, stdout)` và `van_ban_cay` (thân `docs/TIEU-CHI-DOC-TRUOC.md` ở cây làm việc) tiêm được để thử."""
    if isinstance(luong, bool) or not isinstance(luong, (int, np.integer)) or int(luong) not in LUONG_CHINH_THUC:
        raise CongTu([f"dong hat {luong!r} khong phai mot trong {LUONG_CHINH_THUC} (dong 5 va moi dong khac bi chan)"])
    luong = int(luong)
    thieu: list[str] = []
    rc, _ = git("fetch", "origin", "main", "--quiet")
    if rc != 0:
        thieu.append("git fetch origin main that bai (khong kiem duoc ĐO 37 o origin/main)")
    rc, van_main = git("show", f"origin/main:{DUONG_TIEU_CHI}")
    do_main = cat_muc_do(van_main) if rc == 0 else None
    if do_main is None:
        thieu.append(f"origin/main:{DUONG_TIEU_CHI} khong co muc '## ĐO {SO_DO} —'")
    else:
        if chuan_hoa(lenh_chuan(luong)) not in chuan_hoa(do_main):
            thieu.append(f"ĐO {SO_DO} o origin/main khong neu nguyen van lenh: {lenh_chuan(luong)}")
        if chuan_hoa(dong_ke_hoach(luong)) not in chuan_hoa(do_main):
            thieu.append(f"ĐO {SO_DO} o origin/main khong neu nguyen van dong ke hoach: {dong_ke_hoach(luong)}")
        if van_ban_cay is None:
            van_ban_cay = (GOC / DUONG_TIEU_CHI).read_text(encoding="utf-8") if (GOC / DUONG_TIEU_CHI).is_file() else ""
        do_cay = cat_muc_do(van_ban_cay)
        if do_cay is None or chuan_hoa(do_cay) != chuan_hoa(do_main):
            thieu.append(f"ĐO {SO_DO} o cay lam viec khac origin/main (khong ai duoc sua tieu chi sau khi ky)")
    rc, _ = git("merge-base", "--is-ancestor", "origin/main", "HEAD")
    if rc != 0:
        thieu.append("origin/main khong phai to tien cua HEAD")
    for f in FILE_GHIM:
        rc, _ = git("diff", "--quiet", "origin/main", "--", f)
        if rc != 0:
            thieu.append(f"{f} o cay lam viec khac origin/main (hoac khong kiem duoc)")
    hien_co = ket_qua_hien_co if ket_qua_hien_co is not None else doc_ket_qua_hien_co()
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


def tong_hop(ket: dict, hieu_chuan: dict, g_phay: dict) -> dict:
    """Đọc kết cục từ bản ghi ba dòng hạt, theo ĐÚNG bảng mục 6. Hàm thuần của `ket` + hai bản ghi dòng 1. Thiếu dòng nào thì
    `thieu` khác rỗng và kết cục là KHÔNG ĐỌC ĐƯỢC (chưa đủ dữ liệu). Trả `{"tieu_chi": {...}, "ket_cuc": ..., "truot": [...], "khong_doc": [...]}`."""
    cac = ket.get("cac_luong", {})
    thieu = [str(l) for l in LUONG_CHINH_THUC if str(l) not in cac or cac[str(l)].get("trang_thai") != "XONG"]
    out: dict = {"thieu": thieu, "tieu_chi": {}, "bao_cao": {}}
    truot: list[str] = []
    khong_doc: list[str] = []
    if thieu:
        out.update({"ket_cuc": "KHONG_DOC_DUOC", "truot": truot, "khong_doc": [f"chua du dong hat: {', '.join(thieu)}"]})
        return out
    o2, o3, o4 = cac["2"]["o"], cac["3"]["o"], cac["4"]["o"]
    tc = out["tieu_chi"]

    def dem(lst, f):
        return int(sum(1 for m in lst if f(m)))

    def chot(ma, gia_tri, nguong, dat, **them):
        tc[ma] = {"gia_tri": gia_tri, "nguong": nguong, "dat": bool(dat), **them}
        if not dat:
            truot.append(ma)

    x2, x1, x05, null3 = o2["2x"]["thi_truong"], o2["1x"]["thi_truong"], o2["0.5x"]["thi_truong"], o3["NULL"]["thi_truong"]
    chot("A", dem(x2, lambda m: m["oracle"]["top_f"] in m["chuoi"]["khai"]), f">= {NGUONG['A']}", dem(x2, lambda m: m["oracle"]["top_f"] in m["chuoi"]["khai"]) >= NGUONG["A"], R=len(x2))
    chot("A0", dem(null3, lambda m: T.TEN_SPEC_G in m["chuoi"]["khai"]), f"<= {NGUONG['A0']}", dem(null3, lambda m: T.TEN_SPEC_G in m["chuoi"]["khai"]) <= NGUONG["A0"], R=len(null3))
    b1 = dem(null3, lambda m: any(_bao_dong(m["bo_ba"][t], m["nguong"]) for t in ("G", "Z", "H")))
    chot("B1", b1, f"<= {NGUONG['B1']}", b1 <= NGUONG["B1"], R=len(null3))
    b2 = dem(x2, lambda m: m["bo_ba"]["G"]["tt"] == "QUA")
    chot("B2", b2, f">= {NGUONG['B2']}", b2 >= NGUONG["B2"], R=len(x2))
    b3 = dem(x2, lambda m: _bao_dong(m["bo_ba"]["Z"], m["nguong"]))
    chot("B3", b3, f"<= {NGUONG['B3']}", b3 <= NGUONG["B3"], R=len(x2))
    b4 = sum(dem(l, lambda m: m["bo_ba"]["H"]["tt"] == "QUA") for l in (x05, x1, x2))
    chot("B4", b4, "== 0", b4 == 0, R=len(x05) + len(x1) + len(x2))
    tat_ca = [m for l in (x05, x1, x2, null3, o4["NULL"]["thi_truong"], o4["2x"]["thi_truong"]) for m in l]
    c1 = sum(len(m["chuoi"]["c1"]) for m in tat_ca)
    chot("C1", c1, "== 0", c1 == 0, R=len(tat_ca))
    c2 = bootstrap_c2([m["chuoi"]["tien"]["delta_ic"] for m in x2
                       if m["chuoi"]["ket_cuc"] == V.KET_CUC_NANG_CAP and m["chuoi"]["tien"] is not None and m["chuoi"]["tien"]["du_cua_so"]])
    chot("C2", c2["can_duoi"], "can duoi KTC 95% > 0", c2["can_duoi"] is not None and c2["can_duoi"] > 0, **{k: c2[k] for k in ("n", "trung_binh")})
    c3 = dem(null3, lambda m: m["chuoi"]["ket_cuc"] == V.KET_CUC_NANG_CAP)
    chot("C3", c3, f"<= {NGUONG['C3']}", c3 <= NGUONG["C3"], R=len(null3))
    n4, x4 = o4["NULL"]["thi_truong"], o4["2x"]["thi_truong"]
    p1 = sum(m["p1"]["so_vi_pham"] for m in n4 + x4)
    chot("P1", p1, "== 0", p1 == 0, R=len(n4) + len(x4))
    p2 = None if any(m["p2"] is None for m in n4 + x4) else sum(m["p2"]["so_khac"] + m["p2"]["so_diem_lech"] for m in n4 + x4)
    chot("P2", p2, "== 0", p2 == 0, R=len(n4) + len(x4))
    p3 = dem(x4, lambda m: m["p3"]["ic_volume"] > 0)
    chot("P3", p3, f">= {NGUONG['P3']}", p3 >= NGUONG["P3"], R=len(x4))
    p4 = cac["4"].get("p4")
    chot("P4", None if p4 is None else p4["ma_thoat"], "gac G1-G5 xanh (ma thoat 0)", p4 is not None and p4["ma_thoat"] == 0)
    pt_null = dem(n4, lambda m: any(_bao_dong(m["bo_ba"][t], m["nguong"]) for t in ("Gp", "Z", "H")))
    pt_g = dem(x4, lambda m: m["bo_ba"]["Gp"]["tt"] == "QUA")
    thap, cao = g_phay["dai_thap"], g_phay["dai_cao"]
    chot("PT", {"bao_dong_NULL": pt_null, "Gp_QUA_2x": pt_g}, f"NULL <= {NGUONG['PT_NULL']} va Gp QUA trong [{thap} ; {cao}]",
         pt_null <= NGUONG["PT_NULL"] and thap <= pt_g <= cao, R=len(n4))
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
    for l, ten in ((2, "0.5x"), (2, "1x"), (2, "2x"), (3, "NULL"), (4, "NULL"), (4, "2x")):
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
           "tests/test_chay_chinh_thuc_thi_truong_gia.py"]
    lenh = [lenh_py, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-k", "test_G1_ or test_G2_ or test_G3_ or test_G4_ or test_G5_", *cac]
    r = subprocess.run(lenh, cwd=str(GOC), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    dong = [s for s in r.stdout.strip().splitlines() if s.strip()]
    return {"lenh": " ".join(lenh[3:]), "ma_thoat": int(r.returncode), "dong_cuoi": dong[-1] if dong else ""}


def danh_sach_viec(luong: int, phep, so_hoan_vi: int, co_p2: bool, da_co: dict | None = None, ke_hoach=None) -> list[tuple]:
    kh = KE_HOACH[luong] if ke_hoach is None else ke_hoach
    viec = []
    for ten, muc, dau, so in kh["o"]:
        xong = set() if da_co is None else {m["chi_so"] for m in da_co.get(ten, {}).get("thi_truong", [])}
        for chi_so in range(dau, dau + so):
            if chi_so not in xong:
                viec.append((luong, phep, kh["tang"], ten, muc, chi_so, so_hoan_vi, co_p2))
    return viec


def chay_luong(luong: int, phep, so_tien_trinh: int = 1, tiep_tuc: bool = False, luu_moi: int = 25, ra: Path = DUONG_KET_QUA,
               ke_hoach=None, so_hoan_vi: int = cx.SO_HOAN_VI, co_p2: bool = True, chay_p4_fn=chay_p4, lenh_text: str = "",
               in_tien_do: bool = True, ghi_fn=ghi_ket_qua) -> dict:
    """Chạy MỘT dòng hạt (đủ mọi ô), ghi từng đợt `luu_moi` thị trường vào `ra` (trạng thái DANG CHAY), xong thì XONG. Mỗi thị trường là
    hàm THUẦN của (dòng hạt, chỉ số, mức) nên chạy tiếp sau khi gián đoạn không chọn lại thứ gì."""
    kiem_luong_chinh_thuc(luong, phep)
    kh = KE_HOACH[luong] if ke_hoach is None else ke_hoach
    ket = doc_ket_qua_hien_co(ra)             # LUÔN đọc bản đang có: ghi một dòng hạt không được đè mất dòng hạt khác
    if ket is None:
        ket = {"buoc": 295, "do": f"ĐO {SO_DO}", "cac_luong": {}}
    cu = ket["cac_luong"].get(str(luong))
    if cu is not None and (cu["trang_thai"] == "XONG" or not tiep_tuc):
        raise CongTu([f"dong hat {luong} da co trong {Path(ra).name} (trang thai {cu['trang_thai']}): khong ghi de"])
    if cu is None:
        cu = {"trang_thai": "DANG CHAY", "lenh": lenh_text, "tang": kh["tang"], "o": {}, "giay": 0.0,
              "git": {"head": getattr(phep, "head", ""), "origin_main": getattr(phep, "goc_main", ""), "sha_do": getattr(phep, "sha_do", "")},
              "moi_truong": {"python": platform.python_version(), "so_tien_trinh": so_tien_trinh}}
        for ten, muc, dau, so in kh["o"]:
            cu["o"][ten] = {"muc": muc, "kappa": doc_kappa_muc(muc), "chi_so_dau": dau, "so": so, "thi_truong": []}
        ket["cac_luong"][str(luong)] = cu
    if luong == 4 and cu.get("p4") is None:
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
        moi = tai_lap_sinh(luong, phep, kh["tang"], muc, dau)
        ban_ghi = next(m for m in o["thi_truong"] if m["chi_so"] == dau)
        goc = ban_ghi["dg"] if kh["tang"] == 1 else ban_ghi["dg_sinh"]
        o["tai_lap"] = "KHOP" if moi == goc else "LECH"
    luu(True)
    return ket


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--luong", type=int, default=None, help="dòng hạt: 2 · 3 · 4 (chính thức, qua cửa) hoặc 9001 (dòng thử)")
    ap.add_argument("--ket-cuc", action="store_true", help="đọc kết cục từ docs/thi-truong-gia-ket-qua.json; không sinh thị trường nào")
    ap.add_argument("--so-tien-trinh", type=int, default=1)
    ap.add_argument("--tiep-tuc", action="store_true", help="chạy tiếp một dòng hạt đang dở")
    ap.add_argument("--tang", type=int, choices=(1, 2), default=None, help="CHỈ dòng thử 9001")
    ap.add_argument("--so-moi-o", type=int, default=1, help="CHỈ dòng thử 9001: số thị trường mỗi ô")
    ap.add_argument("--ra", default=None, help="CHỈ dòng thử 9001: file kết quả (không được là file chính thức)")
    ap.add_argument("--khong-p2", action="store_true", help="CHỈ dòng thử 9001 Tầng 2: bỏ P2 (đo chi phí riêng)")
    ap.add_argument("--so-hoan-vi", type=int, default=cx.SO_HOAN_VI, help="CHỈ dòng thử 9001")
    a = ap.parse_args(argv)
    if a.ket_cuc:
        ket = doc_ket_qua_hien_co()
        if ket is None:
            print("chua co docs/thi-truong-gia-ket-qua.json", file=sys.stderr)
            return 2
        kc = tong_hop(ket, json.loads(DUONG_HIEU_CHUAN.read_text(encoding="utf-8")), json.loads(DUONG_G_PHAY.read_text(encoding="utf-8")))
        print("\n".join(in_ket_cuc(kc)))
        return 0 if kc["ket_cuc"] == "DAT" else 1 if kc["ket_cuc"] == "TRUOT" else 2
    if a.luong is None:
        ap.error("can --luong hoac --ket-cuc")
    if a.luong == LUONG_THU:
        if a.tang is None or not a.ra:
            ap.error("dong thu 9001 can --tang va --ra <file>")
        ra = Path(a.ra).resolve()
        if ra == DUONG_KET_QUA.resolve():
            ap.error("dong thu khong duoc ghi ra file chinh thuc")
        o_mau = KE_HOACH[2]["o"] + KE_HOACH[3]["o"] if a.tang == 1 else KE_HOACH[4]["o"]
        ke_hoach = {"tang": a.tang, "o": tuple((ten, muc, dau, a.so_moi_o) for ten, muc, dau, _so in o_mau)}
        t0 = _t()
        ket = chay_luong(LUONG_THU, None, a.so_tien_trinh, False, 1000, ra, ke_hoach, a.so_hoan_vi, not a.khong_p2,
                         lambda: {"lenh": "(dong thu)", "ma_thoat": 0, "dong_cuoi": ""}, lenh_text="dong thu 9001")
        giay = _t() - t0
        cu = ket["cac_luong"][str(LUONG_THU)]
        print(f"dòng thử 9001, Tầng {a.tang}, {a.so_moi_o} thị trường mỗi ô, {a.so_tien_trinh} tiến trình: {giay:.1f} s tường")
        for ten, o in cu["o"].items():
            for m in o["thi_truong"]:
                print(f"  ô {ten} chỉ số {m['chi_so']}: " + ", ".join(f"{k} {v:.1f}s" for k, v in m["giay"].items()))
        return 0
    if a.luong not in LUONG_CHINH_THUC:
        print(f"dong hat {a.luong} khong chay duoc o dung cu nay (chinh thuc: {LUONG_CHINH_THUC}; thu: {LUONG_THU})", file=sys.stderr)
        return 2
    try:
        phep = kiem_cong(a.luong, git=git_that, tiep_tuc=a.tiep_tuc)
    except CongTu as e:
        print("CỬA TỪ CHỐI — không sinh thị trường nào:", file=sys.stderr)
        for s in e.ly_do:
            print("  - " + s, file=sys.stderr)
        return 3
    chay_luong(a.luong, phep, a.so_tien_trinh, a.tiep_tuc, lenh_text=f"./.venv/Scripts/python.exe -X utf8 {lenh_chuan(a.luong)} --so-tien-trinh {a.so_tien_trinh}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
