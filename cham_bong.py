"""Tầng 3 — CHẤM BÓNG ứng viên (P3a, BƯỚC 144).

Người dùng chọn 29/09/2026: *"chấm bóng công khai"*. Mỗi ứng viên là một cách
chấm điểm khác, chạy SONG SONG với bản đang chạy trên dữ liệu CHƯA nhìn —
những phiên đến SAU ngày nó được khai — và chỉ lên phiên bản khi qua ngưỡng
thống kê. ĐO 21 (BƯỚC 142) đo trước: ở nhịp giữ lệnh việc ấy HIẾM, có thể không
lần nào trong năm đầu. Module này không được làm nó dễ hơn thật.

MODULE THUẦN: không gọi mạng, không đọc Sheets, không ghi file. Bên gọi đưa vào
các dòng tab `decisions` và bảng giá; module trả số và trạng thái.

NĂM QUY ƯỚC, mỗi quy ước chặn một cách vòng xác nhận tự khen mình:
1. **Bản đang chạy là ĐIỂM ĐÃ GHI** (`score` của sổ quyết định), không tính
   lại từ thành phần — điểm ghi đã qua trọng số động, harness, bộ nhớ hậu
   kiểm; tính lại là so với một bản chưa từng chạy. **Áp cho vòng XÁC NHẬN**
   (và cho `doc_quyet_dinh`, đường nạp của nó). NGOẠI LỆ CÓ TÊN: vòng SÀNG
   (`tools/sang_ung_vien.py`, BƯỚC 154, `docs/TIEU-CHI-DOC-TRUOC.md` ĐO 23) dùng
   điểm TÍNH LẠI vì dòng đã ghi quá thưa để dựng ma trận (mật độ ô 17,1%, 0 mã
   đầy đủ) — và chỉ khi phép đối chiếu với điểm đã ghi mang kết cục ĐẠT.
2. **Mỗi (mã, phiên) một lần**, giữ dòng ghi sau cùng — sổ có dòng lặp vì mọi
   lượt quét trong ngày xử lý lại cùng phiên đã đóng (BƯỚC 125).
3. **So CẶP trên cùng nhãn**: Δ = IC(ứng viên) − IC(bản đang chạy); null hoán
   vị MÃ (BƯỚC 142) áp CÙNG một phép hoán vị cho cả hai điểm.
4. **Ngưỡng 0,05 / K, K = TỔNG số ứng viên đã KHAI** — kể cả ứng viên rớt
   sàng, vì sàng là chỗ đã nhìn nhiều lần (bất biến 7), và kể cả ứng viên
   chưa sàng hay vào thẳng xác nhận (`qua_sang: null`) — chiều chặt hơn, đừng đổi
   (BƯỚC 153, 155).
5. **MỘT MỐC ĐỌC, MỘT LẦN PHÁN** (BƯỚC 162; người dùng chọn 07/10/2026 *"Một mốc cố
   định"*). Vòng xác nhận chỉ phán khi đủ `MOC_DOC` = 252 phiên CÓ NHÃN, và phán trên
   ĐÚNG 252 phiên có nhãn ĐẦU TIÊN kể từ phiên đầu của dữ liệu chấm — không phải
   "≥ 252" trên một cửa sổ lớn dần. Lý do: phán `QUA` ngay khi p < 0,05/K mà không nói
   ĐỌC KHI NÀO là đọc mỗi ngày từ phiên có nhãn thứ 21, khoảng 230 lần nhìn, và sai
   lầm loại I phồng lên (cùng hiện tượng đã đo ở điều kiện dừng C5: z = 1,96 đánh giá
   liên tục cho 11,7% thay vì 5%, `docs/STATE.md` mục *"Vì sao hai giá trị z khác
   nhau"*; với tầng 3 điều đó CHƯA đo, chỉ là ước lượng hướng). ĐO 21 đo lực ở đúng một
   mốc W = 252. Trước mốc: `so_cap` KHÔNG chạy, Δ/p/z không được tính hay trả ra —
   trạng thái là `CHUA TOI MOC` kèm tiến độ n/252. Mọi đường tới phán quyết đi qua mốc
   ở hai đầu: `phan_quyet` là đường DUY NHẤT tới `so_cap` của vòng xác nhận, và
   `trang_thai` từ chối một phán quyết tính trên số phiên khác `MOC_DOC`. Việc cắt 252
   phiên đầu xảy ra TRƯỚC khi chọn mã đầy đủ (`ma_tran_cap(phien_toi_da=...)`): cắt
   sau thì một phiên về sau thiếu một mã sẽ làm rớt mã ấy khỏi phép so, tức đổi kết
   quả của chính 252 phiên đã đọc.

TIỀN ĐĂNG KÝ (P3c-1, BƯỚC 153): một ứng viên được khai TRƯỚC vòng sàng, trong
một commit, với `qua_sang: null`; commit sàng điền nó thành true/false đúng một
lần. `vi_pham_tien_dang_ky` phán một phiên bản sổ so với các phiên bản cha của
nó; bên đi qua lịch sử git là `tests/test_tien_dang_ky_git.py`.

MỘT VÒNG (P3c, BƯỚC 155): người dùng chọn 02/10/2026 **"Bỏ vòng sàng"** — khai thẳng
ứng viên vào vòng xác nhận, tối đa 1 mỗi THÁNG dương lịch, chọn bằng lập luận.
Lý do đo được: ĐO 21 (K lớn thì xác nhận gần như bất khả) và ĐO 23 (điểm tính lại
KHÔNG tái lập điểm đã ghi, dòng seeded quá thưa cho `ma_tran_cap`). Từ
`MOC_MOT_VONG` trở đi một dòng khai mang `qua_sang: null` NGHĨA LÀ *không qua vòng
sàng, vào thẳng xác nhận* và không bao giờ được điền; dòng khai trước mốc giữ luật
cũ (≤ 5 mỗi tuần ISO, `qua_sang` null → true/false một lần). K vẫn đếm MỌI dòng.
`tools/sang_ung_vien.py` đã NGỪNG DÙNG nhưng được giữ để ĐO 23 tái lập.

Nhãn: `experiment_tran_dac_trung.nhan_vuot_ro` — log lợi nhuận `NHIP` phiên
VƯỢT rổ đều, vào ở phiên T+1 (bất biến 1, bất biến 6). Không dựng nhãn thứ hai.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

import experiment_tran_dac_trung as E

GOC = Path(__file__).resolve().parent
SO_UNG_VIEN = GOC / "docs" / "ung-vien.json"

#: Năm số hạng của điểm trước tranh luận (`master_agent`). `news_score` chỉ để
#: hiện — MO-XE Tầng 2 — nên không được vào ứng viên.
THANH_PHAN = ("trend_score", "momentum_score", "volume_score", "sr_score",
              "risk_score")

#: Nhịp nhãn = thời gian giữ lệnh trung bình (20,3 phiên) — ô chuẩn của ĐO 21.
NHIP = 21
ALPHA = 0.05
#: Dưới chừng này mã đầy đủ thì chưa so — cùng `MIN_MA` của ĐO 21.
MIN_MA = 40
#: MỐC ĐỌC (BƯỚC 162, người dùng chọn 07/10/2026): vòng xác nhận phán MỘT lần, trên
#: đúng chừng này phiên CÓ NHÃN đầu tiên của dữ liệu chấm (≈ 1 năm; ô W = 252 của ĐO 21,
#: K = 1 bắt 23/30). Quy ước 5 của docstring đầu file. Đơn vị là phiên CÓ NHÃN — phiên
#: có dòng quyết định và đủ giá T+1..T+22 — không phải phiên lịch.
MOC_DOC = 252
#: Trạng thái trước mốc đọc: chưa phán, KHÔNG có Δ/p/z.
CHUA_TOI_MOC = "CHUA TOI MOC"
#: Trần sàng mỗi tuần ISO — kế hoạch 25/09 (BƯỚC 122). Chỉ còn áp cho dòng khai
#: TRƯỚC `MOC_MOT_VONG`.
TRAN_SANG_MOI_TUAN = 5
#: Ngày người dùng bỏ vòng sàng (BƯỚC 155). Dòng khai từ ngày này: không có vòng
#: sàng, `qua_sang` phải null, trần `TRAN_MOI_THANG` mỗi tháng dương lịch.
MOC_MOT_VONG = "2026-10-02"
TRAN_MOI_THANG = 1
LOAI_SPEC = ("trong_so",)
TRUONG_UNG_VIEN = ("khai_ngay", "mo_ta", "ly_do", "qua_sang", "spec")

_ND = NormalDist()


# ── sổ quyết định → bảng bóng ────────────────────────────────────────────

def doc_quyet_dinh(rows: list[dict], tu_ngay: str) -> pd.DataFrame:
    """Dòng tab `decisions` → một dòng mỗi (mã, phiên), từ `tu_ngay` trở đi.

    Dòng thiếu thành phần hay JSON hỏng bị BỎ và ĐẾM (`attrs["bo"]`) — không
    điền mặc định: một thành phần bịa là một ứng viên chấm trên số không có.
    """
    ra, bo = [], 0
    for r in rows:
        ngay = str(r.get("signal_date", ""))[:10]
        if ngay < tu_ngay:
            continue
        try:
            tp = json.loads(r.get("components") or "")
            vals = {k: float(tp[k]) for k in THANH_PHAN}
            diem = float(r["score"])
        except (ValueError, TypeError, KeyError):
            bo += 1
            continue
        ra.append({"symbol": str(r["symbol"]), "ngay": ngay, "score": diem,
                   "_thu_tu": (float(r.get("at") or 0), float(r.get("seq") or 0)),
                   **vals})
    b = pd.DataFrame(ra, columns=["symbol", "ngay", "score", "_thu_tu", *THANH_PHAN])
    b = (b.sort_values("_thu_tu").drop_duplicates(["symbol", "ngay"], keep="last")
          .drop(columns="_thu_tu").sort_values(["ngay", "symbol"])
          .reset_index(drop=True))
    b.attrs["bo"] = bo
    return b


# ── ứng viên ─────────────────────────────────────────────────────────────

def kiem_spec(spec: dict) -> None:
    """Chỉ nhận ứng viên KHAI BÁO được — không nhận mã tuỳ ý."""
    if not isinstance(spec, dict) or spec.get("loai") not in LOAI_SPEC:
        raise ValueError(f"loai ung vien khong nhan: {spec!r}")
    ts = spec.get("trong_so")
    if not isinstance(ts, dict) or not ts:
        raise ValueError("trong_so rong")
    la = set(ts) - set(THANH_PHAN)
    if la:
        raise ValueError(f"thanh phan ngoai tap: {sorted(la)}")
    if any(float(w) < 0 for w in ts.values()):
        raise ValueError("trong so am")
    if abs(sum(float(w) for w in ts.values()) - 1.0) > 1e-9:
        raise ValueError("tong trong so phai bang 1")


def diem_ung_vien(spec: dict, tp: dict) -> float:
    kiem_spec(spec)
    return float(sum(float(w) * float(tp[k]) for k, w in spec["trong_so"].items()))


# ── phép so cặp ──────────────────────────────────────────────────────────

def _hang_giua(A: np.ndarray) -> np.ndarray:
    r = pd.Series(A.ravel()).rank().to_numpy()
    return (r - r.mean()).reshape(A.shape)


def so_cap(B: np.ndarray, C: np.ndarray, Y: np.ndarray, rng,
           so: int = 2000) -> dict:
    """Δ = IC(C) − IC(B) trên cùng nhãn Y (ma trận phiên × mã, đầy đủ).

    Null: cột nhãn của mã j gán cho mã π(j), CÙNG π cho cả hai điểm — hoán vị
    đồng nhất cho lại đúng Δ thật (có test khoá). p hai phía theo xấp xỉ chuẩn
    của null, như ĐO 21.
    """
    RB, RC, RY = _hang_giua(B), _hang_giua(C), _hang_giua(Y)
    ny = float((RY * RY).sum())
    mb = float(np.sqrt((RB * RB).sum() * ny))
    mc = float(np.sqrt((RC * RC).sum() * ny))
    delta = E.rho_hang(C.ravel(), Y.ravel()) - E.rho_hang(B.ravel(), Y.ravel())
    if not mb or not mc:
        return {"delta": delta, "null": np.zeros(so), "p": 1.0, "z": 0.0}
    CB, CC = RB.T @ RY, RC.T @ RY
    M = CB.shape[0]
    hang = np.arange(M)
    null = np.empty(so)
    for i in range(so):
        pi = rng.permutation(M)
        null[i] = CC[hang, pi].sum() / mc - CB[hang, pi].sum() / mb
    sd = float(np.std(null))
    if sd == 0.0:
        return {"delta": delta, "null": null, "p": 1.0, "z": 0.0}
    z = (delta - float(np.mean(null))) / sd
    return {"delta": delta, "null": null, "z": z,
            "p": 2.0 * (1.0 - _ND.cdf(abs(z)))}


def ma_tran_cap(bang: pd.DataFrame, spec: dict, nhan: pd.DataFrame,
                phien_toi_da: int | None = None):
    """(B, C, Y, phiên, mã) — chỉ giữ mã ĐỦ cả ba ở MỌI phiên có nhãn.

    `nhan`: ngày × mã từ `E.nhan_vuot_ro`. Phiên chưa đủ `NHIP` phiên sau nó
    thì nhãn NaN và bị bỏ — không đoán nhãn của tương lai.

    `phien_toi_da`: chỉ giữ chừng ấy phiên có nhãn ĐẦU TIÊN (theo ngày), và việc cắt
    xảy ra TRƯỚC khi chọn mã đầy đủ — xem quy ước 5. `None` = không cắt: chỉ vòng
    SÀNG cũ (`tools/sang_ung_vien.py`, ngừng dùng) gọi như thế; vòng xác nhận đi qua
    `phan_quyet`, luôn cắt ở `MOC_DOC`.
    """
    kiem_spec(spec)
    b = bang.copy()
    b["uv"] = [diem_ung_vien(spec, r) for r in b[list(THANH_PHAN)].to_dict("records")]
    B = b.pivot(index="ngay", columns="symbol", values="score")
    C = b.pivot(index="ngay", columns="symbol", values="uv")
    Y = nhan.reindex(index=B.index, columns=B.columns)
    co_nhan = Y.notna().any(axis=1)
    B, C, Y = B[co_nhan], C[co_nhan], Y[co_nhan]
    if phien_toi_da is not None:
        B, C, Y = B.iloc[:phien_toi_da], C.iloc[:phien_toi_da], Y.iloc[:phien_toi_da]
    du = B.notna().all() & C.notna().all() & Y.notna().all()
    cot = du[du].index
    return (B[cot].to_numpy(float), C[cot].to_numpy(float), Y[cot].to_numpy(float),
            list(B.index), list(cot))


def phan_quyet(bang: pd.DataFrame, spec: dict, nhan: pd.DataFrame, alpha_k: float,
               hat: int, so: int = 2000) -> dict:
    """Phán MỘT ứng viên của vòng xác nhận — đường DUY NHẤT tới `so_cap` (quy ước 5).

    Dựng ma trận trên `MOC_DOC` phiên có nhãn đầu tiên. Chưa đủ `MOC_DOC` phiên thì
    `so_cap` KHÔNG chạy và kết quả KHÔNG có khoá `delta`/`p`/`z` — không phải NaN đã
    tính. Đủ phiên nhưng dưới `MIN_MA` mã đầy đủ cũng không chạy `so_cap`. Mỗi lần gọi
    dựng một `default_rng(hat)` MỚI, nên chạy lại về sau cho CÙNG kết quả.

    Trả `{"trang_thai", "n_phien", "n_ma", "ket"}`; `ket` là kết quả `so_cap` hoặc
    `None` khi chưa phán.
    """
    B, C, Y, phien, cot = ma_tran_cap(bang, spec, nhan, phien_toi_da=MOC_DOC)
    n_phien, n_ma = len(phien), len(cot)
    ket = None
    if n_phien == MOC_DOC and n_ma >= MIN_MA:
        ket = so_cap(B, C, Y, np.random.default_rng(hat), so=so)
    return {"trang_thai": trang_thai(ket, alpha_k, n_phien, n_ma),
            "n_phien": n_phien, "n_ma": n_ma, "ket": ket}


# ── ngưỡng, trạng thái, sổ đăng ký ───────────────────────────────────────

def so_da_sang(so: dict) -> int:
    """K: MỌI dòng đã khai, kể cả rớt sàng và chưa sàng (quy ước 4)."""
    return len(so.get("ung_vien", {}))


def nguong(so: dict) -> float:
    k = so_da_sang(so)
    return ALPHA / k if k else ALPHA


def trang_thai(ket: dict | None, alpha_k: float, n_phien: int, n_ma: int) -> str:
    """Trạng thái của MỘT ứng viên trong vòng xác nhận — quy ước 5.

    `n_phien` là số phiên CÓ NHÃN mà `ket` được tính trên. Dưới `MOC_DOC`: chưa phán
    (`ket` không được đọc, có thể `None`). Trên `MOC_DOC`: nổ — một phán quyết tính
    trên cửa sổ lớn dần là một lần nhìn mới, không phải lần đọc ở mốc.
    """
    if n_phien < MOC_DOC:
        return CHUA_TOI_MOC
    if n_phien > MOC_DOC:
        raise ValueError(f"phan quyet tinh tren {n_phien} phien; chi doc o dung "
                         f"{MOC_DOC} phien co nhan dau tien")
    if n_ma < MIN_MA:
        return "CHUA DU DU LIEU"
    if ket is None:
        raise ValueError("da toi moc doc ma khong co ket qua so_cap")
    if ket["p"] < alpha_k:
        return "QUA" if ket["delta"] > 0 else "THUA"
    return "DANG CHAM"


def doc_so_ung_vien(duong: Path = SO_UNG_VIEN) -> dict:
    return json.loads(duong.read_text(encoding="utf-8"))


def sau_moc(d: dict) -> bool:
    """Dòng khai từ `MOC_MOT_VONG`: không có vòng sàng."""
    return (datetime.date.fromisoformat(d["khai_ngay"])
            >= datetime.date.fromisoformat(MOC_MOT_VONG))


def kiem_so_ung_vien(so: dict) -> None:
    """Khuôn sổ + trần khai. Ném ValueError.

    Trước `MOC_MOT_VONG`: ≤ 5 mỗi tuần ISO. Từ mốc: `qua_sang` phải null (không
    có vòng sàng) và ≤ `TRAN_MOI_THANG` mỗi tháng dương lịch.
    """
    uv = so.get("ung_vien")
    if not isinstance(uv, dict):
        raise ValueError("thieu khoa ung_vien")
    tuan: dict = {}
    thang: dict = {}
    for ma, d in uv.items():
        thieu = [t for t in TRUONG_UNG_VIEN if t not in d]
        if thieu:
            raise ValueError(f"{ma}: thieu {thieu}")
        kiem_spec(d["spec"])
        if d["qua_sang"] is not None and not isinstance(d["qua_sang"], bool):
            raise ValueError(f"{ma}: qua_sang phai la null (chua sang / vao thang xac nhan) hoac true/false")
        ngay = datetime.date.fromisoformat(d["khai_ngay"])
        if sau_moc(d):
            if d["qua_sang"] is not None:
                raise ValueError(f"{ma}: khai tu {MOC_MOT_VONG} khong co vong sang, "
                                 f"qua_sang phai null")
            k = (ngay.year, ngay.month)
            thang[k] = thang.get(k, 0) + 1
            if thang[k] > TRAN_MOI_THANG:
                raise ValueError(f"qua {TRAN_MOI_THANG} ung vien trong thang "
                                 f"{k[0]}-{k[1]:02d}")
            continue
        y, w, _ = ngay.isocalendar()
        tuan[(y, w)] = tuan.get((y, w), 0) + 1
        if tuan[(y, w)] > TRAN_SANG_MOI_TUAN:
            raise ValueError(f"qua {TRAN_SANG_MOI_TUAN} ung vien trong tuan {y}-W{w}")


# ── bảng công khai (P3b-2, BƯỚC 148) ─────────────────────────────────────

COT_BANG = ("Ứng viên", "Khai ngày", "Mô tả", "Trọng số", "Lý do", "Sàng",
            "Trạng thái")
#: Cột "Sàng" theo `qua_sang` cho dòng khai TRƯỚC mốc: null = khai rồi, vòng sàng
#: chưa chạy. Dòng khai từ `MOC_MOT_VONG` hiện `SANG_BO`: vòng sàng đã bỏ.
SANG = {None: "chua", True: "qua", False: "rot"}
SANG_BO = "bo"


def tom_tat_so(so: dict, hom_nay: str) -> dict:
    """Đầu bảng: K, ngưỡng hiện hành, số đã khai trong tuần ISO (dòng TRƯỚC mốc)
    và trong tháng dương lịch (dòng TỪ mốc) của `hom_nay`."""
    kiem_so_ung_vien(so)
    uv = list(so["ung_vien"].values())
    hn = datetime.date.fromisoformat(hom_nay)
    ngay = [(datetime.date.fromisoformat(d["khai_ngay"]), sau_moc(d)) for d in uv]
    return {"K": so_da_sang(so), "nguong": nguong(so),
            "qua_sang": sum(1 for d in uv if d["qua_sang"] is True),
            "tuan_nay": sum(1 for g, sm in ngay
                            if not sm and g.isocalendar()[:2] == hn.isocalendar()[:2]),
            "tran_tuan": TRAN_SANG_MOI_TUAN,
            "thang_nay": sum(1 for g, sm in ngay
                             if sm and (g.year, g.month) == (hn.year, hn.month)),
            "tran_thang": TRAN_MOI_THANG}


def bang_cong_khai(so: dict, ket: dict | None = None) -> pd.DataFrame:
    """Sổ ứng viên → bảng hiện. KHÔNG tính gì trên dữ liệu thật.

    MỌI ứng viên đều hiện, kể cả rớt sàng và chưa sàng — ngưỡng chia cho TỔNG
    (quy ước 4), giấu ứng viên rớt là giấu mẫu số. `ket` = {mã: (kết quả
    `so_cap`, số phiên, số mã)} do bên gọi đưa vào; thiếu thì ứng viên qua sàng
    ghi `CHUA CHAM` — không suy trạng thái từ chỗ không có số. Kết quả `so_cap` là
    `None` khi chưa tới mốc đọc (`MOC_DOC`): trạng thái `CHUA TOI MOC`, và số phiên khác
    `MOC_DOC` khi đã quá mốc làm `trang_thai` nổ (quy ước 5). Dòng khai TRƯỚC
    mốc mà chưa sàng (`qua_sang: null`) thì `CHUA SANG`, kể cả khi `ket` có nó.
    Dòng khai TỪ `MOC_MOT_VONG` không có vòng sàng: cột Sàng hiện `SANG_BO` và
    trạng thái đi thẳng vào xác nhận (`CHUA CHAM` khi chưa có `ket`) — không bao
    giờ `CHUA SANG`.
    """
    kiem_so_ung_vien(so)
    ket = ket or {}
    a = nguong(so)
    hang = []
    for ma, d in sorted(so["ung_vien"].items(),
                        key=lambda kv: (kv[1]["khai_ngay"], kv[0])):
        mot_vong = sau_moc(d)
        sang = SANG_BO if mot_vong else SANG[d["qua_sang"]]
        if not mot_vong and d["qua_sang"] is None:
            tt = "CHUA SANG"
        elif not mot_vong and not d["qua_sang"]:
            tt = "ROT SANG"
        elif ma in ket:
            tt = trang_thai(ket[ma][0], a, ket[ma][1], ket[ma][2])
        else:
            tt = "CHUA CHAM"
        ts = " · ".join(f"{k.removesuffix('_score')} {float(w):.2f}" for k, w in
                        sorted(d["spec"]["trong_so"].items(), key=lambda kv: -float(kv[1])))
        hang.append(dict(zip(COT_BANG, (ma, d["khai_ngay"], d["mo_ta"], ts,
                                        d["ly_do"], sang, tt))))
    return pd.DataFrame(hang, columns=list(COT_BANG))


# ── tầng HIỂN THỊ (BƯỚC 157) ─────────────────────────────────────────────
# "Chấm bóng" là tên NỘI BỘ (module, sổ, khoá, test). Tên người dùng thấy trên
# app là "Kiểm định chiến lược" / "phương án chấm điểm". Ánh xạ nằm ở ĐÂY và chỉ
# ở đây: `bang_cong_khai` và mọi khoá nội bộ giữ nguyên để không gãy cổng git và
# test lịch sử. Ánh xạ CHẶT — một giá trị lạ nổ `ValueError`, không lọt chuỗi nội
# bộ ra giao diện.

#: Tên cột hiển thị. Cột không có trong bảng này giữ nguyên.
TEN_COT_HIEN = {"Ứng viên": "Phương án", "Khai ngày": "Ngày đăng ký",
                "Sàng": "Vòng sàng (cũ)"}
#: Trạng thái (`bang_cong_khai` + `trang_thai`) → câu tiếng Việt có dấu.
TRANG_THAI_HIEN = {
    "CHUA CHAM": "Chưa đủ dữ liệu",
    "CHUA DU DU LIEU": "Chưa đủ dữ liệu",
    "CHUA TOI MOC": "Chưa tới mốc đọc",
    "DANG CHAM": "Đang theo dõi",
    "QUA": "Đạt — đủ điều kiện nâng cấp",
    "THUA": "Kém hơn bản đang chạy",
    "ROT SANG": "Rớt sàng (quy trình cũ)",
    "CHUA SANG": "Chưa sàng (quy trình cũ)",
}
#: Cột "Sàng" (`SANG` + `SANG_BO`) → chữ hiển thị.
SANG_HIEN = {"chua": "chưa sàng", "qua": "qua sàng", "rot": "rớt sàng", "bo": "đã bỏ"}


#: Mã trạng thái nội bộ đứng thành TỪ NGUYÊN VẸN trong văn bản tự do (`ly_do`):
#: khớp đúng chữ hoa, `\w` ở hai biên nên `QUANG` hay `QUA_X` không bị đụng. Một
#: lượt `re.sub` duy nhất — nhãn thay vào không bị dịch lại.
_RE_MA_NOI_BO = re.compile(
    r"(?<!\w)(" + "|".join(re.escape(k) for k in TRANG_THAI_HIEN) + r")(?!\w)")


def dich_ma_noi_bo(van_ban):
    """Thay mã trạng thái nội bộ đứng riêng trong `van_ban` bằng nhãn tiếng Việt.

    Dòng sổ đã khai là BẤT BIẾN (cổng git, luật b) nên một `ly_do` viết trước khi có
    tầng hiển thị vẫn mang `DANG CHAM`; chỉ tầng hiển thị được dịch nó. Không phải
    chuỗi (NaN, None) thì trả nguyên.
    """
    if not isinstance(van_ban, str):
        return van_ban
    return _RE_MA_NOI_BO.sub(lambda m: TRANG_THAI_HIEN[m.group(1)], van_ban)


def bang_hien_thi(bang: pd.DataFrame) -> pd.DataFrame:
    """Bảng `bang_cong_khai` → bảng hiện cho người dùng. Hàm THUẦN, không đổi `bang`.

    Chỉ đổi CHỮ: tên cột, giá trị cột Sàng và cột Trạng thái, và mã trạng thái nội
    bộ đứng thành từ nguyên vẹn trong cột Lý do (`dich_ma_noi_bo`). Số hàng, thứ tự
    và mọi cột khác giữ nguyên. Giá trị chưa có trong ánh xạ → `ValueError`.
    """
    ra = bang.copy()
    ra["Lý do"] = ra["Lý do"].map(dich_ma_noi_bo)
    for cot, bangmap in (("Trạng thái", TRANG_THAI_HIEN), ("Sàng", SANG_HIEN)):
        la = sorted(set(ra[cot]) - set(bangmap))
        if la:
            raise ValueError(f"cot {cot}: gia tri chua co ten hien thi: {la}")
        ra[cot] = ra[cot].map(bangmap)
    return ra.rename(columns=TEN_COT_HIEN)


# ── tiền đăng ký: một phiên bản sổ so với các phiên bản CHA (P3c-1, BƯỚC 153) ──

#: Giờ VN (UTC+7, không giờ mùa hè) — luật (e) so ngày theo múi này.
GIO_VN = datetime.timezone(datetime.timedelta(hours=7))
#: Trường KHÔNG được đổi sau commit khai. `qua_sang` là trường duy nhất điền
#: sau — suy ra từ khuôn, đừng gõ lại danh sách.
TRUONG_BAT_BIEN = tuple(t for t in TRUONG_UNG_VIEN if t != "qua_sang")
_THIEU = object()


def ngay_vn(thoi_diem: str) -> str:
    """Thời điểm ISO 8601 CÓ múi giờ (`git log --format=%cI`) → ngày giờ VN."""
    return datetime.datetime.fromisoformat(thoi_diem).astimezone(GIO_VN).date().isoformat()


def vi_pham_tien_dang_ky(con: dict, cha: list[dict], ngay_commit: str) -> list[str]:
    """Phán một phiên bản sổ (`con`) so với MỌI phiên bản cha của nó trong git.

    `cha` rỗng = commit tạo file; commit gộp có hai cha — dòng có ở MỘT cha là
    dòng đã khai. `ngay_commit` = ngày commit `con` theo giờ VN. Trả các vi
    phạm; rỗng là sạch.

      (a) dòng MỚI (không cha nào có) phải mang `qua_sang: null`;
      (e) và `khai_ngay` = ngày commit khai — khai lùi ngày là nhận dữ liệu đã
          nhìn làm "chưa nhìn";
      (d) không dòng nào của một cha bị xoá — xoá là giấu mẫu số K;
      (b) `TRUONG_BAT_BIEN` không đổi;
      (c) `qua_sang` chỉ đi null → true/false, không bao giờ từ true/false
          sang giá trị khác — tức đổi đúng MỘT lần.
    """
    uv = con.get("ung_vien") if isinstance(con, dict) else None
    if not isinstance(uv, dict):
        return ["khong doc duoc khoa ung_vien"]
    uv_cha = [c["ung_vien"] for c in cha
              if isinstance(c, dict) and isinstance(c.get("ung_vien"), dict)]
    loi = []
    for ma, d in uv.items():
        if any(ma in u for u in uv_cha):
            continue
        if d.get("qua_sang", _THIEU) is not None:
            loi.append(f"{ma}: commit khai phai mang qua_sang null (a)")
        if d.get("khai_ngay") != ngay_commit:
            loi.append(f"{ma}: khai_ngay {d.get('khai_ngay')} khac ngay commit khai "
                       f"{ngay_commit} gio VN (e)")
    for u in uv_cha:
        for ma, p in u.items():
            if ma not in uv:
                loi.append(f"{ma}: dong da khai bi xoa (d)")
                continue
            d = uv[ma]
            doi = [t for t in TRUONG_BAT_BIEN if d.get(t, _THIEU) != p.get(t, _THIEU)]
            if doi:
                loi.append(f"{ma}: sua truong da khai {doi} (b)")
            q_p, q_c = p.get("qua_sang", _THIEU), d.get("qua_sang", _THIEU)
            hop_le = ((q_c is None or isinstance(q_c, bool)) if q_p is None
                      else isinstance(q_p, bool) and q_c is q_p)
            if not hop_le:
                loi.append(f"{ma}: qua_sang {q_p!r} -> {q_c!r}; chi duoc null -> "
                           f"true/false mot lan (c)")
    return loi
