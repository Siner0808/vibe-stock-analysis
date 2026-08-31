"""
experiment_tran_dac_trung.py
──────────────────────────────────────────────────────────────────────
TRẦN của tập đặc trưng: cách gộp TỐT NHẤT CÓ THỂ có dự báo được không.

Câu hỏi khác hẳn "điểm hiện tại có dự báo được không". Điểm hiện tại dùng
một bộ trọng số gõ tay; nếu nó cho rho ≈ 0 thì vẫn còn ngỏ khả năng bộ
trọng số đang gộp sai. Script này đóng khả năng đó lại.

CÁCH ĐO — VÌ SAO KHỚP TRONG MẪU LÀ ĐÚNG Ở ĐÂY
Khớp mô hình tuyến tính trên TOÀN BỘ dữ liệu, không giữ lại phần nào.
Nghe như phạm luật, nhưng đây chính là điều cần: **không quy trình trung
thực nào vượt được điểm tối ưu trong mẫu.** Nếu cả cận trên cũng không nhô
lên khỏi nhiễu thì câu hỏi đóng lại, và đóng lại mà KHÔNG tiêu một phiên
sạch nào (bất biến 8 — vùng sạch là tài nguyên tiêu hao).

SÀN NHIỄU DỰNG BẰNG HOÁN VỊ, KHÔNG BẰNG CÔNG THỨC
Khớp trong mẫu tự làm rho phồng lên, và mức phồng phụ thuộc số tham số,
tự tương quan của nhãn, và cấu trúc chéo. Không công thức nào tôi tin được
cho cả ba cùng lúc. Hoán vị DỊCH VÒNG THEO MÃ — dịch chuỗi nhãn của mỗi mã
đi một khoảng ngẫu nhiên ≫ h — giữ nguyên tự tương quan trong mã VÀ cấu
trúc chéo, chỉ phá liên kết đặc trưng↔nhãn. Nó tự nuốt luôn phần phồng.

⚠️ CHỨNG CỨ DƯƠNG LÀ BƯỚC QUYẾT ĐỊNH, KHÔNG PHẢI KẾT QUẢ NULL
Không có `--chung-cu-duong` thì *"không tìm thấy gì"* và *"máy đo hỏng"*
trông y hệt nhau. Nó tiêm một đặc trưng giả có mức tương quan BIẾT TRƯỚC,
hiệu chuẩn quanh rào hoà vốn. Đo ngày 31/08/2026:

      nhịp   tiêm 0   nửa rào   đúng rào   1,5× rào
      h=5      im       KÊU       KÊU        KÊU     -> ĐỌC ĐƯỢC
      h=20     im        im        im        KÊU     -> KHÔNG đọc được

Nghĩa là kết quả null ở h=5 là **bằng chứng vắng mặt**; ở h=20 nó chỉ là
**thiếu lực**. Đừng báo cáo hai thứ đó bằng cùng một câu.

NHÃN PHẢI LÀ LỢI NHUẬN VƯỢT RỔ (bất biến 6)
Đo 31/08/2026, tương quan chéo trung bình giữa các mã cùng ngày:
      nhãn thô     +0,368  ->  68 mã sụp còn 2,6 mã ĐỘC LẬP
      nhãn vượt rổ −0,012  ->  giữ nguyên 68
Dùng nhãn thô là tự vứt 96% cỡ mẫu cho beta thị trường.

RÀO HOÀ VỐN ĐƯỢC SUY RA, KHÔNG GÕ TAY
Phí lấy thẳng từ `paper_metrics.ROUND_TRIP_COST_PCT` nên mọi thay đổi hằng
số phí tự lan vào đây. Trượt giá là số ĐO ĐƯỢC (24/08/2026), khai riêng
bên dưới vì nó không phải hằng số trong mã.

KẾT QUẢ ĐÃ CHẠY: `docs/STATE.md`, mục "BƯỚC 7".
"""
import argparse
import json
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent
CACHE = GOC / "backtest" / "cache"
FILE_MOC = GOC / "docs" / "moc_du_lieu_sach.json"

#: Dưới mốc này `SMA50`/`SMA200` trả None nên đặc trưng NGHÈO. Trộn hai chế
#: độ vào một mẫu là trộn hai phân phối khác nhau — xem `docs/STATE.md`,
#: mục "BƯỚC 2 — ĐO CHỖ TỐI" (29/08/2026).
MIN_HIST = 250

#: Trượt giá MỖI VÒNG, đo ngày 24/08/2026 bằng hai lượt walk-forward khác
#: nhau đúng công tắc `MO_PHONG_TRUOT_GIA`. Không phải hằng số trong mã —
#: nó là kết quả của mô hình `truot_gia.py` trên lưới giá thật.
TRUOT_GIA_DPT = 0.43

#: Tám đặc trưng khai TRƯỚC. Thêm bớt sau khi thấy số là bất biến 7.
TEN_DAC_TRUNG = ("rsi", "macd_hist", "bb_pctb", "stoch_kd",
                 "atr_pct", "px_sma50", "px_sma200", "vol_rel")

HORIZONS = (5, 10, 20)
SO_HOAN_VI = 1000
_ND = NormalDist()


def chi_phi_vong() -> float:
    """Chi phí mỗi vòng, tính %. Phí lấy từ sổ lệnh, trượt giá khai ở trên."""
    from paper_metrics import ROUND_TRIP_COST_PCT
    return ROUND_TRIP_COST_PCT + TRUOT_GIA_DPT


def e_z_tren(p: float) -> float:
    """E[Z | Z > ngưỡng] cho chuẩn tắc, khi chọn `p` phần trăm trên cùng."""
    a = _ND.inv_cdf(1 - p)
    return _ND.pdf(a) / p


def rao_hoa_von(sigma: float, p: float = 0.05) -> float:
    """Tương quan tối thiểu để nhóm được chọn bù nổi chi phí thực thi.

    Chọn CÀNG ÍT mã thì rào CÀNG THẤP (E[z] lớn hơn), nhưng số lệnh mỗi năm
    cũng ít đi — tức lực đo giảm. Hai chiều ngược nhau, phải nêu cả hai.
    """
    return chi_phi_vong() / (sigma * e_z_tren(p))


def dac_trung(df: pd.DataFrame) -> pd.DataFrame:
    """Tám chỉ báo, VECTOR HOÁ — mỗi hàng chỉ dùng dữ liệu tới hết hàng đó.

    Cùng công thức với `data_collectors._compute_local_indicators`, khác
    duy nhất chỗ cắt: ở đó lấy `.iloc[-1]`, ở đây lấy cả chuỗi. Tính lại
    từng phiên là O(n²) và cho ra đúng cùng con số.
    """
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
    out = pd.DataFrame(index=df.index)

    d = c.diff()
    up = d.clip(lower=0).ewm(com=13, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(com=13, adjust=False).mean()
    out["rsi"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))

    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    out["macd_hist"] = (macd - macd.ewm(span=9, adjust=False).mean()) / c

    s20, sd20 = c.rolling(20).mean(), c.rolling(20).std()
    out["bb_pctb"] = (c - (s20 - 2 * sd20)) / (4 * sd20).replace(0, np.nan)

    lo14, hi14 = l.rolling(14).min(), h.rolling(14).max()
    k = 100 * (c - lo14) / (hi14 - lo14).replace(0, np.nan)
    out["stoch_kd"] = k - k.rolling(3).mean()

    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()],
                   axis=1).max(axis=1)
    out["atr_pct"] = tr.rolling(14).mean() / c

    out["px_sma50"] = c / c.rolling(50).mean() - 1
    out["px_sma200"] = c / c.rolling(200).mean() - 1
    out["vol_rel"] = np.log((v + 1) / (v.rolling(50).mean() + 1))
    return out


def nap_gia() -> dict:
    """{mã: DataFrame} từ `backtest/cache/`, chỉ mã có trong sổ tay mốc sạch."""
    moc = json.loads(FILE_MOC.read_text(encoding="utf-8"))["moc_theo_ma"]
    kh = {}
    for ma in moc:
        f = CACHE / f"{ma}.csv"
        if not f.exists():
            continue
        df = pd.read_csv(f)
        if "time" not in df.columns or len(df) < MIN_HIST + 60:
            continue
        ngay = df["time"].astype(str).str.slice(0, 10)
        kh[ma] = (df.assign(ngay=ngay).drop_duplicates("ngay")
                    .sort_values("ngay").set_index("ngay"))
    return kh


def nhan_vuot_ro(kh: dict, h: int) -> pd.DataFrame:
    """Log lợi nhuận `h` phiên VƯỢT RỔ ĐỀU, vào ở giá mở cửa T+1.

    `shift(-1)` là bất biến 1: điểm của phiên T chỉ dùng dữ liệu tới hết T,
    còn lệnh vào ở phiên SAU. Bỏ nó là nhìn trộm đúng một phiên.
    """
    gia = pd.DataFrame({m: d["close"] for m, d in kh.items()}).sort_index()
    ln = np.log(gia)
    fwd = (ln.shift(-h - 1) - ln.shift(-1)) * 100
    return fwd.sub(fwd.mean(axis=1), axis=0)


def rho_hang(x: np.ndarray, y: np.ndarray) -> float:
    """Tương quan hạng — cùng thước đo `backtest/report.py` dùng."""
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    mau = np.sqrt((rx @ rx) * (ry @ ry))
    return float(rx @ ry / mau) if mau else 0.0


def khop_va_rho(X: np.ndarray, y: np.ndarray) -> float:
    """OLS TRONG MẪU rồi đo tương quan hạng của giá trị khớp với nhãn.

    Đây là CẬN TRÊN: không cách gộp tuyến tính nào cho rho cao hơn.
    """
    A = np.column_stack([np.ones(len(X)), X])
    beta = np.linalg.lstsq(A, y, rcond=None)[0]
    return rho_hang(A @ beta, y)


def _bang(kh: dict, h: int):
    """Gộp mọi mã thành (X chuẩn hoá, y, chỉ số theo mã)."""
    nhan = nhan_vuot_ro(kh, h)
    Xs, ys, mas = [], [], []
    for ma, d in kh.items():
        dt = dac_trung(d).iloc[MIN_HIST:]
        y = nhan[ma].reindex(dt.index)
        ok = dt.notna().all(axis=1) & y.notna()
        if int(ok.sum()) < 60:
            continue
        Xs.append(dt.loc[ok, list(TEN_DAC_TRUNG)].to_numpy(float))
        ys.append(y[ok].to_numpy(float))
        mas.append(np.full(int(ok.sum()), ma))
    X = np.vstack(Xs)
    y = np.concatenate(ys)
    ma_arr = np.concatenate(mas)
    X = (X - X.mean(0)) / X.std(0)
    chi_so = {m: np.flatnonzero(ma_arr == m) for m in np.unique(ma_arr)}
    return X, y, chi_so


def san_nhieu(ham, y: np.ndarray, chi_so: dict, h: int,
              rng, so: int = SO_HOAN_VI) -> np.ndarray:
    """Phân phối null bằng hoán vị DỊCH VÒNG theo mã.

    Dịch ≫ h để không quan sát nào giữ lại nhãn cũ của nó qua phần chồng
    lấn. Mã quá ngắn thì để nguyên — dịch một chuỗi 30 phiên với h=20
    không phá được gì mà còn làm null hẹp lại một cách giả tạo.
    """
    out = np.empty(so)
    for i in range(so):
        yp = y.copy()
        for _, idx in chi_so.items():
            n = len(idx)
            if n > 2 * (h + 1):
                k = int(rng.integers(h + 1, n - h - 1))
                yp[idx] = np.roll(y[idx], k)
        out[i] = ham(yp)
    out.sort()
    return out


def chung_cu_duong(kh: dict, h: int, rng, so_vong: int = 400) -> None:
    """Tiêm tín hiệu có mức BIẾT TRƯỚC, xem phép đo có bắt được không."""
    X, y, chi_so = _bang(kh, h)
    sigma = float(y.std())
    rao = rao_hoa_von(sigma)
    p95 = san_nhieu(lambda yp: khop_va_rho(X, yp), y, chi_so, h, rng,
                    so_vong)[int(0.95 * so_vong)]

    print(f"\n── CHỨNG CỨ DƯƠNG · h = {h} ──")
    print(f"  {len(y):,} quan sát · rào hoà vốn {rao:.3f} · sàn nhiễu {p95:.4f}")
    print(f"  {'tiêm vào':>14} {'rho tiêm':>9} {'rho đo được':>12} {'bắt?':>7}")
    for he_so, ten in ((0.0, "không có gì"), (0.5, "nửa rào"),
                       (1.0, "đúng bằng rào"), (1.5, "1,5× rào")):
        muc = rao * he_so
        gia_dt = muc * (y / sigma) + np.sqrt(max(1 - muc ** 2, 0.0)) * \
            rng.standard_normal(len(y))
        Xg = np.column_stack([X, (gia_dt - gia_dt.mean()) / gia_dt.std()])
        r = khop_va_rho(Xg, y)
        bat = "CÓ" if r > p95 else "không"
        print(f"  {ten:>14} {muc:>9.4f} {r:>12.4f} {bat:>7}")
    print("  Đọc: 'không có gì' phải KHÔNG bắt và 'đúng bằng rào' phải BẮT")
    print("  thì kết quả null ở nhịp này mới là bằng chứng vắng mặt.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[2])
    ap.add_argument("--hoan-vi", type=int, default=SO_HOAN_VI,
                    help="số lần hoán vị dựng sàn nhiễu")
    ap.add_argument("--chung-cu-duong", action="store_true",
                    help="chạy phép tiêm tín hiệu — ĐỌC TRƯỚC KHI TIN KẾT QUẢ NULL")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    if not CACHE.exists():
        print("❌ Chưa có `backtest/cache/`. Chạy `backtest/run.py fetch` trước.")
        return 1

    rng = np.random.default_rng(a.seed)
    kh = nap_gia()
    if not kh:
        print("❌ Không đọc được mã nào từ cache.")
        return 1

    print("=" * 78)
    print("TRẦN CỦA TẬP ĐẶC TRƯNG — cận trên trong mẫu")
    print(f"  {len(kh)} mã · min_history {MIN_HIST} · {len(TEN_DAC_TRUNG)} đặc trưng")
    print(f"  chi phí mỗi vòng {chi_phi_vong():.2f}% "
          f"(phí sổ lệnh + trượt giá {TRUOT_GIA_DPT} đpt)")
    print(f"  hoán vị {a.hoan_vi} lần · seed {a.seed}")
    print("=" * 78)

    print(f"\n  {'h':>3} {'quan sát':>10} {'rho cận trên':>13} {'sàn nhiễu':>11}"
          f" {'rào @top5%':>11}  kết luận")
    for h in HORIZONS:
        X, y, chi_so = _bang(kh, h)
        rho = khop_va_rho(X, y)
        null = san_nhieu(lambda yp: khop_va_rho(X, yp), y, chi_so, h, rng,
                         a.hoan_vi)
        p95 = null[int(0.95 * a.hoan_vi)]
        rao = rao_hoa_von(float(y.std()))
        if rho <= p95:
            kl = "DƯỚI sàn nhiễu"
        elif rho < rao:
            kl = "vượt nhiễu, DƯỚI rào"
        else:
            kl = "VƯỢT CẢ HAI"
        print(f"  {h:>3} {len(y):>10,} {rho:>13.4f} {p95:>11.4f}"
              f" {rao:>11.3f}  {kl}")

    if a.chung_cu_duong:
        for h in (5, 20):
            chung_cu_duong(kh, h, rng)
    else:
        print("\n⚠️  CHƯA chạy chứng cứ dương. Một kết quả 'DƯỚI sàn nhiễu' ở")
        print("   trên CHƯA đọc được — nó có thể là không có tín hiệu, mà cũng")
        print("   có thể là phép đo thiếu lực. Chạy lại với --chung-cu-duong.")

    print("\n" + "=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
