"""Tầng 3 — CHẤM BÓNG ứng viên (P3a, BƯỚC 144).

Người dùng chọn 29/09/2026: *"chấm bóng công khai"*. Mỗi ứng viên là một cách
chấm điểm khác, chạy SONG SONG với bản đang chạy trên dữ liệu CHƯA nhìn —
những phiên đến SAU ngày nó được khai — và chỉ lên phiên bản khi qua ngưỡng
thống kê. ĐO 21 (BƯỚC 142) đo trước: ở nhịp giữ lệnh việc ấy HIẾM, có thể không
lần nào trong năm đầu. Module này không được làm nó dễ hơn thật.

MODULE THUẦN: không gọi mạng, không đọc Sheets, không ghi file. Bên gọi đưa vào
các dòng tab `decisions` và bảng giá; module trả số và trạng thái.

BỐN QUY ƯỚC, mỗi quy ước chặn một cách vòng xác nhận tự khen mình:
1. **Bản đang chạy là ĐIỂM ĐÃ GHI** (`score` của sổ quyết định), không tính
   lại từ thành phần — điểm ghi đã qua trọng số động, harness, bộ nhớ hậu
   kiểm; tính lại là so với một bản chưa từng chạy.
2. **Mỗi (mã, phiên) một lần**, giữ dòng ghi sau cùng — sổ có dòng lặp vì mọi
   lượt quét trong ngày xử lý lại cùng phiên đã đóng (BƯỚC 125).
3. **So CẶP trên cùng nhãn**: Δ = IC(ứng viên) − IC(bản đang chạy); null hoán
   vị MÃ (BƯỚC 142) áp CÙNG một phép hoán vị cho cả hai điểm.
4. **Ngưỡng 0,05 / K, K = TỔNG số ứng viên đã KHAI** — kể cả ứng viên rớt
   sàng, vì sàng là chỗ đã nhìn nhiều lần (bất biến 7), và kể cả ứng viên
   chưa sàng (`qua_sang: null`) — chiều chặt hơn, đừng đổi (BƯỚC 153).

TIỀN ĐĂNG KÝ (P3c-1, BƯỚC 153): một ứng viên được khai TRƯỚC vòng sàng, trong
một commit, với `qua_sang: null`; commit sàng điền nó thành true/false đúng một
lần. `vi_pham_tien_dang_ky` phán một phiên bản sổ so với các phiên bản cha của
nó; bên đi qua lịch sử git là `tests/test_tien_dang_ky_git.py`.

Nhãn: `experiment_tran_dac_trung.nhan_vuot_ro` — log lợi nhuận `NHIP` phiên
VƯỢT rổ đều, vào ở phiên T+1 (bất biến 1, bất biến 6). Không dựng nhãn thứ hai.
"""
from __future__ import annotations

import datetime
import json
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
#: Trần sàng mỗi tuần ISO — kế hoạch 25/09 (BƯỚC 122).
TRAN_SANG_MOI_TUAN = 5
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


def ma_tran_cap(bang: pd.DataFrame, spec: dict, nhan: pd.DataFrame):
    """(B, C, Y, phiên, mã) — chỉ giữ mã ĐỦ cả ba ở MỌI phiên có nhãn.

    `nhan`: ngày × mã từ `E.nhan_vuot_ro`. Phiên chưa đủ `NHIP` phiên sau nó
    thì nhãn NaN và bị bỏ — không đoán nhãn của tương lai.
    """
    kiem_spec(spec)
    b = bang.copy()
    b["uv"] = [diem_ung_vien(spec, r) for r in b[list(THANH_PHAN)].to_dict("records")]
    B = b.pivot(index="ngay", columns="symbol", values="score")
    C = b.pivot(index="ngay", columns="symbol", values="uv")
    Y = nhan.reindex(index=B.index, columns=B.columns)
    co_nhan = Y.notna().any(axis=1)
    B, C, Y = B[co_nhan], C[co_nhan], Y[co_nhan]
    du = B.notna().all() & C.notna().all() & Y.notna().all()
    cot = du[du].index
    return (B[cot].to_numpy(float), C[cot].to_numpy(float), Y[cot].to_numpy(float),
            list(B.index), list(cot))


# ── ngưỡng, trạng thái, sổ đăng ký ───────────────────────────────────────

def so_da_sang(so: dict) -> int:
    """K: MỌI dòng đã khai, kể cả rớt sàng và chưa sàng (quy ước 4)."""
    return len(so.get("ung_vien", {}))


def nguong(so: dict) -> float:
    k = so_da_sang(so)
    return ALPHA / k if k else ALPHA


def trang_thai(ket: dict, alpha_k: float, n_phien: int, n_ma: int) -> str:
    if n_phien < NHIP or n_ma < MIN_MA:
        return "CHUA DU DU LIEU"
    if ket["p"] < alpha_k:
        return "QUA" if ket["delta"] > 0 else "THUA"
    return "DANG CHAM"


def doc_so_ung_vien(duong: Path = SO_UNG_VIEN) -> dict:
    return json.loads(duong.read_text(encoding="utf-8"))


def kiem_so_ung_vien(so: dict) -> None:
    """Khuôn sổ + trần 5 ứng viên mỗi tuần ISO. Ném ValueError."""
    uv = so.get("ung_vien")
    if not isinstance(uv, dict):
        raise ValueError("thieu khoa ung_vien")
    tuan: dict = {}
    for ma, d in uv.items():
        thieu = [t for t in TRUONG_UNG_VIEN if t not in d]
        if thieu:
            raise ValueError(f"{ma}: thieu {thieu}")
        kiem_spec(d["spec"])
        if d["qua_sang"] is not None and not isinstance(d["qua_sang"], bool):
            raise ValueError(f"{ma}: qua_sang phai la null (chua sang) hoac true/false")
        y, w, _ = datetime.date.fromisoformat(d["khai_ngay"]).isocalendar()
        tuan[(y, w)] = tuan.get((y, w), 0) + 1
        if tuan[(y, w)] > TRAN_SANG_MOI_TUAN:
            raise ValueError(f"qua {TRAN_SANG_MOI_TUAN} ung vien trong tuan {y}-W{w}")


# ── bảng công khai (P3b-2, BƯỚC 148) ─────────────────────────────────────

COT_BANG = ("Ứng viên", "Khai ngày", "Mô tả", "Trọng số", "Lý do", "Sàng",
            "Trạng thái")
#: Cột "Sàng" theo `qua_sang`: null = khai rồi, vòng sàng chưa chạy.
SANG = {None: "chua", True: "qua", False: "rot"}


def tom_tat_so(so: dict, hom_nay: str) -> dict:
    """Đầu bảng: K, ngưỡng hiện hành, số đã khai trong tuần ISO của `hom_nay`."""
    kiem_so_ung_vien(so)
    uv = list(so["ung_vien"].values())
    tuan = datetime.date.fromisoformat(hom_nay).isocalendar()[:2]
    return {"K": so_da_sang(so), "nguong": nguong(so),
            "qua_sang": sum(1 for d in uv if d["qua_sang"] is True),
            "tuan_nay": sum(1 for d in uv if datetime.date.fromisoformat(
                d["khai_ngay"]).isocalendar()[:2] == tuan),
            "tran_tuan": TRAN_SANG_MOI_TUAN}


def bang_cong_khai(so: dict, ket: dict | None = None) -> pd.DataFrame:
    """Sổ ứng viên → bảng hiện. KHÔNG tính gì trên dữ liệu thật.

    MỌI ứng viên đều hiện, kể cả rớt sàng và chưa sàng — ngưỡng chia cho TỔNG
    (quy ước 4), giấu ứng viên rớt là giấu mẫu số. `ket` = {mã: (kết quả
    `so_cap`, số phiên, số mã)} do bên gọi đưa vào; thiếu thì ứng viên qua sàng
    ghi `CHUA CHAM` — không suy trạng thái từ chỗ không có số. Chưa sàng
    (`qua_sang: null`) thì `CHUA SANG`, kể cả khi `ket` có nó.
    """
    kiem_so_ung_vien(so)
    ket = ket or {}
    a = nguong(so)
    hang = []
    for ma, d in sorted(so["ung_vien"].items(),
                        key=lambda kv: (kv[1]["khai_ngay"], kv[0])):
        if d["qua_sang"] is None:
            tt = "CHUA SANG"
        elif not d["qua_sang"]:
            tt = "ROT SANG"
        elif ma in ket:
            tt = trang_thai(ket[ma][0], a, ket[ma][1], ket[ma][2])
        else:
            tt = "CHUA CHAM"
        ts = " · ".join(f"{k.removesuffix('_score')} {float(w):.2f}" for k, w in
                        sorted(d["spec"]["trong_so"].items(), key=lambda kv: -float(kv[1])))
        hang.append(dict(zip(COT_BANG, (ma, d["khai_ngay"], d["mo_ta"], ts,
                                        d["ly_do"], SANG[d["qua_sang"]], tt))))
    return pd.DataFrame(hang, columns=list(COT_BANG))


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
