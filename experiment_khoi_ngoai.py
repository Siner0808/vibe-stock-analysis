"""ĐO 15 — khối ngoại có DỰ BÁO được lợi nhuận không?

Tiêu chí ký trước: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 15.

BỘ MÁY ĐƯỢC NHẬP LẠI, KHÔNG DỰNG LẠI
`experiment_tran_dac_trung.py` đã có đủ năm thứ đắt tiền, và tất cả đều đã
được đối chiếu ở BƯỚC 7 và BƯỚC 9:

    nhan_vuot_ro()   nhan la loi nhuan VUOT RO (bat bien 6). Nhan tho co
                     tuong quan cheo +0,368, tuc 68 ma sup con 2,6 ma doc
                     lap -- dung nhan tho la tu vut 96% co mau.
    san_nhieu()      hoan vi DICH VONG theo ma: giu tu tuong quan trong ma
                     VA cau truc cheo, chi pha lien ket dac trung-nhan. Da
                     doi chieu bang duong thu hai o nam nhip.
    chung_cu_duong() tiem tin hieu co muc BIET TRUOC. Khong co no thi
                     "khong tim thay gi" va "may do hong" trong y het nhau.
    rao_hoa_von()    suy tu ROUND_TRIP_COST_PCT, khong go tay.
    MIN_HIST = 250   duoi moc nay dac trung gia NGHEO (BUOC 2).

Lỗi 41 tính đúng cái này: hai lần trong ba ngày lời giải nằm sẵn trong
repo và vẫn bị viết lại từ đầu. Ở đây chỉ **tập đặc trưng** là mới.

ĐÂY LÀ MỘT CẬN TRÊN
Cửa sổ 2021-10-14 → 2026-09-03 là vùng đã bị nhìn nhiều nhất (bất biến 8).
Nên đo TRONG MẪU là cố ý: dưới sàn nhiễu thì câu hỏi đóng lại mà không
tiêu một phiên sạch nào; trên sàn nhiễu thì **chưa** là tín hiệu, nó chỉ
nói rằng một phép đo ngoài mẫu là đáng làm.

CHẠY
    ./.venv/Scripts/python.exe fetch_khoi_ngoai.py
    ./.venv/Scripts/python.exe experiment_khoi_ngoai.py
    ./.venv/Scripts/python.exe experiment_khoi_ngoai.py --chung-cu-duong
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

import experiment_tran_dac_trung as E  # noqa: E402

CACHE_KN = GOC / "backtest" / "cache_khoi_ngoai"

#: Năm đặc trưng khai TRƯỚC trong `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 15.
#: Thêm bớt sau khi thấy số là bất biến 7.
TEN_DAC_TRUNG = ("kn_ty_trong_5", "kn_ty_trong_20", "kn_ap_luc_5",
                 "kn_z_20", "kn_cuong_do_20")

#: Ô KHÔNG HƯỚNG. Nó đo mức tham gia, không đo mua hay bán — nên một IC
#: khác 0 ở đây là dấu hiệu RÒ RỈ, không phải tín hiệu.
O_DOI_CHUNG = "kn_cuong_do_20"

#: Hai nhịp, cả hai nằm trong `E.NHIP_DA_DOI_CHIEU`.
HORIZONS = (5, 21)

#: Năm đặc trưng cùng lúc.
ALPHA_BONFERRONI = 0.05 / len(TEN_DAC_TRUNG)


def nap_khoi_ngoai() -> dict:
    """{mã: DataFrame chỉ số theo ngày} từ cache đĩa. KHÔNG chạm mạng."""
    kn = {}
    if not CACHE_KN.exists():
        return kn
    for f in sorted(CACHE_KN.glob("*.csv")):
        df = pd.read_csv(f)
        if "time" not in df.columns:
            continue
        ngay = df["time"].astype(str).str.slice(0, 10)
        kn[f.stem] = (df.assign(ngay=ngay).drop_duplicates("ngay")
                        .sort_values("ngay").set_index("ngay"))
    return kn


def dac_trung_kn(gia: pd.DataFrame, kn: pd.DataFrame) -> pd.DataFrame:
    """Năm đặc trưng khối ngoại, VECTOR HOÁ, chỉ dùng dữ liệu tới hết hàng.

    Ghép theo NGÀY của bảng giá: mọi đặc trưng nằm trên đúng lịch mà nhãn
    nằm trên. Phiên có giá mà thiếu khối ngoại thành `NaN` và bị loại ở
    `_bang_kn` — nó KHÔNG được điền 0, vì 0 là một giá trị có nghĩa thật
    trong chuỗi này (16–36% số phiên các năm đầu).
    """
    k = kn.reindex(gia.index)
    out = pd.DataFrame(index=gia.index)

    vol = gia["volume"].astype(float)
    nv = pd.to_numeric(k.get("net_vol"), errors="coerce")
    bv = pd.to_numeric(k.get("buy_val"), errors="coerce")
    sv = pd.to_numeric(k.get("sell_val"), errors="coerce")
    nval = pd.to_numeric(k.get("net_val"), errors="coerce")

    def _r(s, n):
        return s.rolling(n, min_periods=n).sum()

    out["kn_ty_trong_5"] = _r(nv, 5) / _r(vol, 5).replace(0, np.nan)
    out["kn_ty_trong_20"] = _r(nv, 20) / _r(vol, 20).replace(0, np.nan)

    mau5 = _r(bv, 5) + _r(sv, 5)
    out["kn_ap_luc_5"] = (_r(bv, 5) - _r(sv, 5)) / mau5.replace(0, np.nan)

    s20 = _r(nval, 20)
    tb = s20.rolling(250, min_periods=250).mean()
    sd = s20.rolling(250, min_periods=250).std()
    out["kn_z_20"] = (s20 - tb) / sd.replace(0, np.nan)

    gtgd20 = _r(gia["close"].astype(float) * vol, 20)
    out["kn_cuong_do_20"] = (_r(bv, 20) + _r(sv, 20)) / gtgd20.replace(0, np.nan)
    return out


def do_phu_ghep(kh: dict, kn: dict) -> dict:
    """Bao nhiêu phiên CÓ GIÁ mà thiếu khối ngoại — điều 2 của tiêu chí."""
    co_gia = thieu_kn = 0
    ma_thieu_han = []
    for ma, g in kh.items():
        if ma not in kn:
            ma_thieu_han.append(ma)
            co_gia += len(g)
            thieu_kn += len(g)
            continue
        chung = g.index.intersection(kn[ma].index)
        co_gia += len(g)
        thieu_kn += len(g) - len(chung)
    return {"co_gia": co_gia, "thieu_kn": thieu_kn,
            "ma_thieu_han": ma_thieu_han}


def _bang_kn(kh: dict, kn: dict, h: int):
    """Gộp mọi mã thành (X, y, chỉ số theo mã). Song song `E._bang`."""
    nhan = E.nhan_vuot_ro(kh, h)
    Xs, ys, mas = [], [], []
    for ma, g in kh.items():
        if ma not in kn:
            continue
        dt = dac_trung_kn(g, kn[ma]).iloc[E.MIN_HIST:]
        y = nhan[ma].reindex(dt.index)
        ok = dt.notna().all(axis=1) & y.notna()
        if int(ok.sum()) < 60:
            continue
        Xs.append(dt.loc[ok, list(TEN_DAC_TRUNG)].to_numpy(float))
        ys.append(y[ok].to_numpy(float))
        mas.append(np.full(int(ok.sum()), ma))
    if not Xs:
        return None, None, None
    X = np.vstack(Xs)
    y = np.concatenate(ys)
    ma_arr = np.concatenate(mas)
    chi_so = {m: np.flatnonzero(ma_arr == m) for m in np.unique(ma_arr)}
    return X, y, chi_so


def tri_so_p(ic: float, null: np.ndarray) -> float:
    """Trị số p hai phía, thực nghiệm. Dùng CẢ phân phối null.

    VÌ SAO KHÔNG DÙNG PHÂN VỊ
    Quy tắc Bonferroni ở đây đòi ngưỡng 0,5% mỗi phía. Một phân vị 0,5%
    ước lượng từ `n` hoán vị chỉ tựa vào vài thống kê thứ tự ở đuôi — với
    n = 40 nó chính là CỰC TRỊ của 40 mẫu, tức một cái sàn hẹp hơn sàn
    thật, tức "vượt sàn" quá dễ. Trị số p đếm trên toàn bộ phân phối nên
    không có chỗ đó.

    Công thức `(1 + k) / (1 + n)` là dạng có hiệu chỉnh: nó không bao giờ
    trả 0, vì một phép đo với n hoán vị không thể khẳng định p < 1/(n+1).

    KHAI RA CHO ĐÚNG: phép sửa này làm SAU một lượt dò 40 hoán vị đã cho
    thấy một ô `VUOT`. Chiều của nó là chiều CHẶT hơn — một sàn rộng hơn,
    khó vượt hơn — chứ không phải chiều làm kết quả đẹp lên. Ghi ở đây để
    người đọc sau tự phán, thay vì phải tin.
    """
    k = int(np.sum(np.abs(null) >= abs(ic)))
    return (1.0 + k) / (1.0 + len(null))


def bien_thien_sau_ghep(X: np.ndarray) -> dict:
    """Điều 1 của tiêu chí — BƯỚC 112.

    Một chuỗi giàu trên lịch có thể sụp thành vài giá trị ở đúng tập quan
    sát được dùng. `sl_pattern_memory.json` trông 6.327 mẫu mà chỉ có 2
    bộ ba khác nhau, và con số 6.327 không hề báo điều đó.
    """
    return {t: int(len(np.unique(X[:, i])))
            for i, t in enumerate(TEN_DAC_TRUNG)}


def doc_duoc_khong(bat_gi: dict) -> bool:
    """Phán quyết của chứng cứ dương, tách ra thành HÀM THUẦN.

    Hai vế, và cả hai bắt buộc — đúng câu của bản gốc: *"không có gì" phải
    KHÔNG bắt và "đúng bằng rào" phải BẮT*. Bỏ vế đầu là bỏ phép kiểm xem
    máy đo có tự kêu trên hư không hay không, mà đó chính là ca đã xảy ra
    thật ngày 22/09/2026.

    Tách ra vì một phán quyết nằm chìm trong một hàm dài có gọi sàn nhiễu
    thì không ai đục thử được — và hai phát đục đã SỐNG SÓT vì đúng lý do
    đó. Thiếu khoá thì trả False: fail closed.
    """
    return (not bat_gi.get("khong co gi", True)) and bool(
        bat_gi.get("dung bang rao", False))


def chung_cu_duong_kn(X, y, chi_so, h: int, rng, so_vong: int = 400) -> bool:
    """Tiêm một đặc trưng có mức tương quan BIẾT TRƯỚC, xem phép đo có kêu.

    KHÔNG dùng `E.chung_cu_duong` được, và lý do nằm trong chính tiêu chí
    ĐO 15: nó tiêm vào **tám đặc trưng giá** và đo bằng `khop_va_rho`
    (cận trên tuyến tính), còn ĐO 15 đo **IC một đặc trưng**. Tập đặc
    trưng khác thì lực khác, nên chép kết quả 31/08 sang là đọc một phép
    đo về thứ khác.

    Phán quyết theo đúng câu của bản gốc: *"không có gì" phải KHÔNG bắt và
    "đúng bằng rào" phải BẮT*. Trả `True` chỉ khi cả hai vế đạt — fail
    closed, vì lấy điểm giữa cho phép một phép đo yếu tự xưng là sạch.

    ĐẶC TRƯNG TIÊM PHẢI TỰ TƯƠNG QUAN NHƯ ĐẶC TRƯNG THẬT — VÀ PHẢI RỜI NHÃN
    Hàm này hỏng HAI lần trước khi đúng, và cả hai lần đều đáng ghi.

    Bản 1 tiêm **nhiễu trắng**. Sai vì `E.san_nhieu` hoán vị NHÃN với đặc
    trưng GIỮ NGUYÊN, nên bề rộng null phụ thuộc thẳng vào tự tương quan
    của đặc trưng: chuỗi trơn cho null RỘNG, nhiễu trắng cho null HẸP.
    Hiệu chuẩn bằng nhiễu trắng là hiệu chuẩn một phép đo DỄ HƠN phép đo
    thật rồi tuyên bố phép đo khó là đọc được.

    Bản 2 lấy nền từ **chính cột `kn_z_20` thật**. Nó chữa được tự tương
    quan và hỏng ở chỗ khác, nặng hơn: ô *"không tiêm gì"* trở thành **đo
    lại chính `kn_z_20`**, tức phép hiệu chuẩn tự kiểm chính thứ nó đi
    kiểm. Bằng chứng là chính bản in — ở h=21 ô "không tiêm gì" cho
    p = 0,0075 và **KÊU**, trong khi nó buộc phải im.

    Bản 3, đang chạy: nền là cột thật ấy **dịch vòng trong từng mã** một
    khoảng ≫ h. Dịch vòng giữ NGUYÊN VẸN tự tương quan và phá liên kết
    với nhãn — đúng cơ chế `E.san_nhieu` dùng, chỉ đổi vế áp dụng. Và nó
    KHÔNG phải cái bẫy `references/bay.md` mục 4 cảnh báo: ở đó phép hiệu
    chuẩn dịch đặc trưng RỒI LẠI hoán vị nhãn trong cùng một vòng null
    nên độ dịch hiệu dụng bị quấn; ở đây nền được dịch MỘT LẦN để dựng
    ra, còn null vẫn dựng bằng cách hoán vị nhãn với nền giữ nguyên.
    """
    sigma = float(np.std(y))
    rao = E.rao_hoa_von(sigma)
    i_nen = TEN_DAC_TRUNG.index("kn_z_20")
    nen = X[:, i_nen].copy()
    for _, idx in chi_so.items():
        n = len(idx)
        if n > 2 * (h + 1):
            k = int(rng.integers(h + 1, n - h - 1))
            nen[idx] = np.roll(nen[idx], k)
    nen = (nen - nen.mean()) / (nen.std() or 1.0)

    print(f"\n-- CHUNG CU DUONG · h = {h} --")
    print(f"  {len(y):,} quan sat · rao hoa von {rao:.4f}")
    print(f"  nen nhieu: cot THAT `kn_z_20` DICH VONG trong tung ma"
          f" (giu tu tuong quan, roi nhan)")
    print(f"  {'tiem vao':>16} {'rho tiem':>9} {'IC do duoc':>12} {'tri so p':>10} {'bat?':>7}")
    bat_gi = {}
    for he_so, ten in ((0.0, "khong co gi"), (0.5, "nua rao"),
                       (1.0, "dung bang rao"), (1.5, "1,5x rao")):
        muc = rao * he_so
        gia_dt = muc * (y / sigma) + np.sqrt(max(1 - muc ** 2, 0.0)) * nen
        r = E.rho_hang(gia_dt, y)
        null = E.san_nhieu(lambda yp, _x=gia_dt: E.rho_hang(_x, yp),
                           y, chi_so, h, rng, so=so_vong)
        p = tri_so_p(r, null)
        bat = p < ALPHA_BONFERRONI
        bat_gi[ten] = bat
        print(f"  {ten:>16} {muc:>9.4f} {r:>+12.4f} {p:>10.4f}"
              f" {'CO' if bat else 'khong':>7}")

    doc_duoc = doc_duoc_khong(bat_gi)
    print(f"  -> nhip nay {'DOC DUOC' if doc_duoc else 'KHONG doc duoc'}:"
          f" ket qua null o day la"
          f" {'bang chung vang mat' if doc_duoc else 'THIEU LUC'}")
    return doc_duoc


def phan_dinh(ket: dict, chung_cu_keu: bool | None,
              can_tren: dict | None = None) -> tuple[int, str]:
    """Đọc theo ĐÚNG bảng bốn kết cục đã ký.

    `can_tren` thêm 22/09/2026 sau một lượt hỏi sổ tay: dự án đóng câu hỏi
    bằng **cách gộp tuyến tính tối ưu trong mẫu**, không bằng IC từng đặc
    trưng. Một IC đơn lẻ dưới sàn nhiễu KHÔNG cho phép nói *"không cách
    gộp nào tốt hơn tồn tại"* — đó là hai khẳng định khác nhau, và chỉ
    khẳng định thứ hai mới đóng được câu hỏi.
    """
    if chung_cu_keu is None:
        return 2, "CHUA KIEM DUOC — chung cu duong chua chay"
    o = dict(ket)
    if can_tren is not None:
        o["CAN TREN"] = can_tren
    vuot = [t for t, v in o.items() if v.get("vuot_san")]
    if not vuot:
        if chung_cu_keu:
            return 0, ("KET CUC 3 — BANG CHUNG VANG MAT: khong dac trung nao"
                       " (ke ca CAN TREN) vuot san nhieu, va chung cu duong KEU")
        return 2, ("KET CUC 4 — THIEU LUC: chung cu duong IM,"
                   " ket qua null KHONG doc duoc")
    if not chung_cu_keu:
        return 2, (f"KET CUC 4 — THIEU LUC: chung cu duong IM, nen con so"
                   f" cua {vuot} KHONG doc duoc du no vuot san nhieu")
    vuot_rao = [t for t in vuot if o[t].get("vuot_rao")]
    if vuot_rao:
        return 1, f"KET CUC 1 — {vuot_rao} vuot ca san nhieu lan rao hoa von"
    return 1, f"KET CUC 2 — {vuot} vuot san nhieu nhung DUOI rao hoa von"


def chay_mot_nhip(kh: dict, kn: dict, h: int, rng, so_hoan_vi: int) -> dict:
    print(f"\n{'=' * 66}\nNHIP h = {h}\n{'=' * 66}")
    X, y, chi_so = _bang_kn(kh, kn, h)
    if X is None:
        print("  khong gop duoc bang nao")
        return {}
    print(f"  {X.shape[0]} quan sat · {len(chi_so)} ma · {X.shape[1]} dac trung")

    bt = bien_thien_sau_ghep(X)
    print("\n  BIEN THIEN SAU KHI GHEP (dieu 1 — BUOC 112):")
    for t, n in bt.items():
        print(f"    {t:<16} {n:>7} gia tri khac nhau tren {X.shape[0]}")

    sigma = float(np.std(y))
    rao = E.rao_hoa_von(sigma)
    print(f"\n  sigma nhan {sigma:.3f}%  ·  rao hoa von {rao:.4f}")

    ket = {}
    for i, ten in enumerate(TEN_DAC_TRUNG):
        x = X[:, i]
        ic = E.rho_hang(x, y)
        null = E.san_nhieu(lambda yp, _x=x: E.rho_hang(_x, yp),
                           y, chi_so, h, rng, so=so_hoan_vi)
        p = tri_so_p(ic, null)
        lo = float(np.quantile(null, ALPHA_BONFERRONI / 2))
        hi = float(np.quantile(null, 1 - ALPHA_BONFERRONI / 2))
        vuot_san = p < ALPHA_BONFERRONI
        ket[ten] = {"ic": ic, "p": p, "san_lo": lo, "san_hi": hi,
                    "vuot_san": bool(vuot_san),
                    "vuot_rao": bool(abs(ic) > rao)}
        dau = "VUOT" if vuot_san else "trong"
        print(f"    {ten:<16} IC {ic:+.4f}   p {p:.4f}"
              f"   san [{lo:+.4f} ; {hi:+.4f}]   {dau}"
              + ("   | vuot rao" if abs(ic) > rao else ""))

    # ── CAN TREN: cach gop tuyen tinh TOI UU trong mau ────────────────
    # Mot IC don le KHONG phai can tren -- cach gop co the cao hon bat ky
    # dac trung rieng le nao. Ma "cau hoi dong lai" chi noi duoc khi CAN
    # TREN cung nam duoi san nhieu. Day dung khuon BUOC 7: khop tren TOAN
    # BO du lieu, khong giu lai phan nao, vi "khong quy trinh trung thuc
    # nao vuot duoc diem toi uu trong mau".
    Xc = (X - X.mean(0)) / np.where(X.std(0) == 0, 1.0, X.std(0))
    ic_tran = E.khop_va_rho(Xc, y)
    null_tran = E.san_nhieu(lambda yp: E.khop_va_rho(Xc, yp),
                            y, chi_so, h, rng, so=so_hoan_vi)
    p_tran = tri_so_p(ic_tran, null_tran)
    vuot_tran = p_tran < ALPHA_BONFERRONI
    print(f"\n  CAN TREN (gop tuyen tinh toi uu trong mau):")
    print(f"    rho {ic_tran:+.4f}   p {p_tran:.4f}"
          f"   {'VUOT' if vuot_tran else 'trong'} san nhieu"
          + ("   | vuot rao" if abs(ic_tran) > rao else ""))
    if not vuot_tran:
        print(f"    -> khong cach gop tuyen tinh nao cua nam dac trung nay"
              f" vuot duoc nhieu o nhip {h}")

    if ket.get(O_DOI_CHUNG, {}).get("vuot_san"):
        print(f"\n  ⚠️  O KHONG HUONG `{O_DOI_CHUNG}` CUNG VUOT SAN NHIEU."
              f"\n      Dieu 3 cua tieu chi: thu do duoc nhieu kha nang la RO RI,"
              f"\n      khong phai huong cua dong tien.")
    return {"h": h, "n": int(X.shape[0]), "so_ma": len(chi_so),
            "sigma": sigma, "rao": rao, "bien_thien": bt, "dac_trung": ket,
            "can_tren": {"rho": ic_tran, "p": p_tran,
                         "vuot_san": bool(vuot_tran),
                         "vuot_rao": bool(abs(ic_tran) > rao)},
            "_bang": (X, y, chi_so)}


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DO 15 — IC cua khoi ngoai")
    ap.add_argument("--chung-cu-duong", action="store_true",
                    help="tiem tin hieu co muc BIET TRUOC roi xem phep do co keu")
    ap.add_argument("--hoan-vi", type=int, default=E.SO_HOAN_VI)
    ap.add_argument("--hat-giong", type=int, default=20260922)
    ap.add_argument("--ra", default="")
    a = ap.parse_args(tham_so)

    kh = E.nap_gia()
    kn = nap_khoi_ngoai()
    print(f"gia: {len(kh)} ma  ·  khoi ngoai: {len(kn)} ma")
    if not kn:
        print("CHUA KIEM DUOC — chua co cache khoi ngoai."
              " Chay `fetch_khoi_ngoai.py` truoc.")
        return 2

    dp = do_phu_ghep(kh, kn)
    print(f"\nDO PHU GHEP (dieu 2): {dp['co_gia']} phien co gia,"
          f" thieu khoi ngoai {dp['thieu_kn']}"
          f" ({100 * dp['thieu_kn'] / max(1, dp['co_gia']):.2f}%)")
    if dp["ma_thieu_han"]:
        print(f"  ma khong co file khoi ngoai: {dp['ma_thieu_han']}")

    rng = np.random.default_rng(a.hat_giong)
    ra = {"ngay_chay": pd.Timestamp.today().strftime("%Y-%m-%d"),
          "do_phu_ghep": dp, "nhip": {}}
    for h in HORIZONS:
        ra["nhip"][str(h)] = chay_mot_nhip(kh, kn, h, rng, a.hoan_vi)

    keu = {}
    if a.chung_cu_duong:
        print(f"\n{'=' * 66}\nCHUNG CU DUONG\n{'=' * 66}")
        for h in HORIZONS:
            d = ra["nhip"].get(str(h), {})
            if not d:
                continue
            X, y, chi_so = d["_bang"]
            keu[h] = chung_cu_duong_kn(X, y, chi_so, h, rng)
            ra["nhip"][str(h)]["chung_cu_duong_keu"] = keu[h]

    print(f"\n{'=' * 66}\nPHAN DINH THEO BANG DA KY\n{'=' * 66}")
    ma_thoat = 0
    for h in HORIZONS:
        d = ra["nhip"].get(str(h), {})
        if not d:
            continue
        m, cau = phan_dinh(d["dac_trung"], keu.get(h), d.get("can_tren"))
        print(f"  h={h:<3} {cau}")
        ma_thoat = max(ma_thoat, m)

    if a.ra:
        goi = {k: v for k, v in ra.items() if k != "nhip"}
        goi["nhip"] = {k: {kk: vv for kk, vv in v.items() if kk != "_bang"}
                       for k, v in ra["nhip"].items()}
        Path(a.ra).write_text(json.dumps(goi, ensure_ascii=False, indent=2,
                                         default=float), encoding="utf-8")
        print(f"\n  ghi: {a.ra}")
    return ma_thoat


if __name__ == "__main__":
    sys.exit(main())
