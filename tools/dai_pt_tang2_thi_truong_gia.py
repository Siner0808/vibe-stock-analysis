"""Dải 99% của tiêu chí PT ở Tầng 2 (C4, BƯỚC 294): từ ΔIC_true của G′ tới P(`QUA`) tới dải nhị thức.

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 19.8 (khai TRƯỚC khi đo) và mục 6 hàng PT.
Công thức là phần của lời khai, nên nó nằm ở đây và được commit TRƯỚC lượt đo:

    p      = Φ(a + b · ΔIC_true(G′))       a, b = `mde80.probit` của `docs/thi-truong-gia-hieu-chuan.json` (Tầng 1)
    dải 99% của số thị trường `QUA` trên R = 100 thị trường, hai phía:
        thấp = k NHỎ NHẤT có P(X ≤ k) ≥ 0,005         cao = k NHỎ NHẤT có P(X ≤ k) ≥ 0,995      X ~ Nhị thức(R, p)

ΔIC_true là ĐIỂM ƯỚC của lượt oracle; sai số Monte Carlo của nó KHÔNG đi vào dải (đúng cách mục 19.5 tính
5–23 cho `bo_momentum_score` ở dòng hạt 9001). `--se` chỉ in thêm dải ở ΔIC ± 1 sai số để người đọc thấy
dải ấy hẹp hơn độ bất định thật; nó không phải tiêu chí.

CHẠY
    ./.venv/Scripts/python.exe tools/dai_pt_tang2_thi_truong_gia.py --delta 0.0304 [--se 0.0030] [--R 100]

Chỉ đọc `docs/thi-truong-gia-hieu-chuan.json`; không ghi file, không sinh thị trường, không mạng.
"""
from __future__ import annotations

import argparse
import json
import sys
from math import comb
from pathlib import Path
from statistics import NormalDist

for _luong_ra in (sys.stdout, sys.stderr):   # BƯỚC 129
    try:
        _luong_ra.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
DUONG_HIEU_CHUAN = GOC / "docs" / "thi-truong-gia-hieu-chuan.json"

SO_THI_TRUONG_PT = 100        # mục 6, hàng PT: R = 100
PHAN_VI_MOT_PHIA = 0.005      # dải 99% hai phía = 0,5% mỗi đuôi


def doc_probit(duong: Path = DUONG_HIEU_CHUAN) -> tuple[float, float]:
    """(a, b) của đường probit Tầng 1, đọc từ file hiệu chuẩn của Lát 2 (đọc, không ghi)."""
    p = json.loads(Path(duong).read_text(encoding="utf-8"))["mde80"]["probit"]
    return float(p["a"]), float(p["b"])


def p_qua(delta_ic: float, a: float, b: float) -> float:
    """P(`QUA`) = Φ(a + b · ΔIC_true)."""
    return NormalDist().cdf(a + b * float(delta_ic))


def dai_99(p: float, so_thi_truong: int = SO_THI_TRUONG_PT, phan_vi: float = PHAN_VI_MOT_PHIA) -> tuple[int, int]:
    """Dải 99% hai phía của Nhị thức(R, p): (thấp, cao) như docstring đầu file."""
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"p phai trong [0, 1]: {p!r}")
    cum, thap, cao = 0.0, None, None
    for k in range(so_thi_truong + 1):
        cum += comb(so_thi_truong, k) * p ** k * (1 - p) ** (so_thi_truong - k)
        if thap is None and cum >= phan_vi:
            thap = k
        if cao is None and cum >= 1 - phan_vi:
            cao = k
    return int(thap), int(so_thi_truong if cao is None else cao)


def dai_tu_delta(delta_ic: float, a: float, b: float, so_thi_truong: int = SO_THI_TRUONG_PT) -> dict:
    p = p_qua(delta_ic, a, b)
    thap, cao = dai_99(p, so_thi_truong)
    return {"delta_ic": float(delta_ic), "p_qua": p, "dai_thap": thap, "dai_cao": cao, "R": int(so_thi_truong)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--delta", type=float, required=True, help="ΔIC_true của G′ ở mức 2× (điểm ước)")
    ap.add_argument("--se", type=float, default=None, help="sai số Monte Carlo của ΔIC (chỉ để in dải ± 1 sai số)")
    ap.add_argument("--R", type=int, default=SO_THI_TRUONG_PT)
    a = ap.parse_args(argv)
    try:
        ca, cb_ = doc_probit()
        r = dai_tu_delta(a.delta, ca, cb_, a.R)
    except (ValueError, OSError, KeyError) as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 2
    print(f"probit Tầng 1: a = {ca:.6f}, b = {cb_:.6f}")
    print(f"ΔIC_true = {r['delta_ic']:+.6f}  →  P(QUA) = {r['p_qua']:.4f}  →  dải 99% của {r['R']} thị trường: {r['dai_thap']}–{r['dai_cao']}")
    if a.se is not None:
        for nhan, d in (("−1 sai số", a.delta - a.se), ("+1 sai số", a.delta + a.se)):
            x = dai_tu_delta(d, ca, cb_, a.R)
            print(f"  (chỉ để tham khảo, không phải tiêu chí) ΔIC {nhan} = {d:+.6f}: P = {x['p_qua']:.4f}, dải {x['dai_thap']}–{x['dai_cao']}")
    print("KET_QUA_JSON " + json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
