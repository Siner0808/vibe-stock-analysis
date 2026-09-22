"""ĐO 14 — dữ liệu khối ngoại có BACKTEST được không?

Tiêu chí đọc ký trước khi chạy: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 14.

VÌ SAO CÓ PHÉP ĐO NÀY
─────────────────────
`MO-XE-KIEN-TRUC.md` kết luận: sáu agent đều tính từ **cùng một chuỗi
giá**, nên về lý thuyết chúng không tạo được thông tin ngoài thứ đã có
trong chuỗi đó. Nó nêu tên ba nguồn độc lập: BCTC theo quý · giao dịch
nội bộ · **khối ngoại mua ròng**.

Nguồn thứ nhất đã đo — `docs/STATE.md` BƯỚC 53, IC không phân biệt được
với 0 trên 2.099 quan sát. Nguồn thứ ba thì tới hôm nay **chưa ai kéo
một dòng nào**.

ĐO GÌ, VÀ KHÔNG ĐO GÌ
─────────────────────
Đây là phép đo **TÍNH KHẢ THI**, không phải phép đo **TÍN HIỆU**. Một ô
ĐẠT ở đây KHÔNG nói gì về việc khối ngoại có dự báo được lợi nhuận hay
không; nó chỉ nói chuỗi ấy có tồn tại đủ dài và đủ rộng để đem ra đo hay
không. BƯỚC 53 là lời nhắc đắt giá: lần trước một nguồn độc lập được kéo
về đủ cỡ mẫu, và IC vẫn nằm trọn quanh 0.

ĐỐI CHỨNG DƯƠNG — phần quan trọng nhất của dụng cụ này
──────────────────────────────────────────────────────
Một chuỗi khối ngoại NGẮN có hai cách giải thích, và chúng ngược nhau:

    a) nguon that su chi phuc vu tung ay ngay
    b) tham so ngay CUA TOI bi bo qua, ham tra ve mac dinh

Không phân biệt được hai cái đó thì con số đọc ra nói về **dụng cụ**, chứ
không nói về **nguồn** — đúng lỗi 66. Nên mỗi lượt chạy kéo thêm `ohlcv`
qua **đúng cùng một đối tượng**, **đúng cùng khoảng ngày**, bằng **đúng
tên tham số vừa dùng được**. OHLCV là ca đã biết trước là dương: cache
trong repo có dữ liệu giá từ 2018-09.

    ohlcv DAI  +  foreign_flow NGAN   ->  (a), noi ve NGUON
    ohlcv NGAN +  foreign_flow NGAN   ->  (b), CHUA KIEM DUOC

BA TRẠNG THÁI
─────────────
    0  doc duoc, va ca hai o A/B deu DAT
    1  doc duoc, co o KHONG DAT
    2  CHUA KIEM DUOC — API no, bi khoa hang, hoac doi chung am
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

#: Ngày xin đủ sớm để chạm trần thật của nguồn, không phải trần của câu hỏi.
XIN_TU = "2015-01-01"

#: Mốc của ô A. Cache giá mặc định lùi tới 2021-10; cache rộng tới 2018-09-13.
MOC_PHU_CACHE_MAC_DINH = "2021-10-01"
MOC_PHU_CACHE_RONG = "2018-09-13"

#: Ô B. Ngưỡng ký trước, KHÔNG được sửa sau khi thấy số.
NGUONG_PHU_DAT = 60
NGUONG_PHU_HONG = 36

#: Mã dùng cho ô A và ô C. Có mặt trong cache, thanh khoản cao.
MA_MOC = "FPT"

#: Các hình dạng lời gọi sẽ thử, theo thứ tự. Chữ ký thật bị lớp bọc
#: `_dispatch(**B)` che, nên tên tham số chỉ lộ ra khi gọi — thử rồi KHAI
#: đường nào chạy được, đừng đoán rồi im lặng.
HINH_DANG = (
    ("start/end", lambda f, t, d: f(start=t, end=d)),
    ("start_date/end_date", lambda f, t, d: f(start_date=t, end_date=d)),
    ("from_date/to_date", lambda f, t, d: f(from_date=t, to_date=d)),
    ("vi tri", lambda f, t, d: f(t, d)),
    ("khong tham so", lambda f, t, d: f()),
)


def _hom_nay() -> str:
    return time.strftime("%Y-%m-%d")


def goi_thu(ham, tu: str, den: str) -> tuple[str, object, list[str]]:
    """Thử từng hình dạng cho tới khi một cái trả về bảng không rỗng.

    Trả `(ten_hinh_dang, ket_qua, nhat_ky)`. Không tìm được thì
    `ten_hinh_dang` là chuỗi rỗng — và `nhat_ky` giữ nguyên văn từng lỗi,
    vì một câu "không gọi được" mà không nêu ĐƯỜNG đã thử sẽ sai ngay khi
    có đường thứ hai (lỗi 16).
    """
    nhat_ky: list[str] = []
    for ten, goi in HINH_DANG:
        try:
            kq = goi(ham, tu, den)
        except Exception as e:  # noqa: BLE001
            nhat_ky.append(f"{ten:<22} -> {type(e).__name__}: {str(e)[:110]}")
            continue
        n = _so_dong(kq)
        nhat_ky.append(f"{ten:<22} -> OK, {n if n is not None else 'khong dem duoc'} dong")
        if n:
            return ten, kq, nhat_ky
    return "", None, nhat_ky


def _so_dong(kq) -> int | None:
    """Số dòng, hoặc None khi KHÔNG ĐẾM ĐƯỢC.

    Trả 0 ở nhánh hỏng thì phía sau không phân biệt được *"nguồn trả về
    rỗng"* với *"tôi không đọc nổi thứ nguồn trả về"* — hai kết luận
    ngược nhau về cùng một mã. Đây đúng luật R3 của `chan_bia_so_lieu`,
    và cửa ấy đã chặn bản đầu của chính hàm này.
    """
    if kq is None:
        return None
    try:
        return int(len(kq))
    except TypeError:
        return None


def _cot_ngay(df):
    """Tên cột ngày, suy từ bảng nhận được — đừng ghim tên."""
    for c in df.columns:
        if str(c).lower() in ("date", "time", "trading_date", "ngay", "tradingdate"):
            return c
    return None


def in_tho(df, nhan: str, so_dong: int = 5) -> None:
    """In DỮ LIỆU THÔ ngay dưới con số — bài học lỗi 61."""
    print(f"\n  --- {nhan}: {len(df)} dong x {len(df.columns)} cot")
    print(f"      cot: {list(df.columns)}")
    with_pd = df.head(so_dong).to_string(max_colwidth=18)
    for d in with_pd.splitlines():
        print(f"      | {d}")


def o_A_va_C(eq, in_du_lieu: bool) -> dict:
    """Ô A (độ sâu) và ô C (đọc được không), kèm ĐỐI CHỨNG DƯƠNG."""
    import pandas as pd

    den = _hom_nay()
    print(f"\n{'=' * 62}\nO A · DO SAU — xin tu {XIN_TU}, ma {MA_MOC}\n{'=' * 62}")

    ten, kq, nhat_ky = goi_thu(eq.foreign_flow, XIN_TU, den)
    print("  duong da thu:")
    for d in nhat_ky:
        print(f"    {d}")
    if not ten or not isinstance(kq, pd.DataFrame):
        return {"doc_duoc": False, "vi_sao": "khong hinh dang nao tra ve bang"}

    print(f"  hinh dang dung duoc: {ten}")
    if in_du_lieu:
        in_tho(kq, "foreign_flow tho")

    cot = _cot_ngay(kq)
    if cot is None:
        return {"doc_duoc": False, "vi_sao": f"khong tim thay cot ngay trong {list(kq.columns)}"}

    ngay = pd.to_datetime(kq[cot], errors="coerce").dropna()
    if ngay.empty:
        return {"doc_duoc": False, "vi_sao": f"cot `{cot}` khong doi duoc sang ngay"}
    som, muon = str(ngay.min())[:10], str(ngay.max())[:10]

    # --- DOI CHUNG DUONG: cung doi tuong, cung khoang, cung hinh dang goi
    print(f"\n  DOI CHUNG DUONG — ohlcv cung khoang, cung hinh dang `{ten}`")
    _, kq2, nk2 = goi_thu(eq.ohlcv, XIN_TU, den)
    for d in nk2:
        print(f"    {d}")
    som_gia = ""
    if isinstance(kq2, pd.DataFrame) and len(kq2):
        c2 = _cot_ngay(kq2)
        if c2 is not None:
            n2 = pd.to_datetime(kq2[c2], errors="coerce").dropna()
            if not n2.empty:
                som_gia = str(n2.min())[:10]
    print(f"    ohlcv som nhat      : {som_gia or '(khong doc duoc)'}")
    print(f"    foreign_flow som nhat: {som}")

    return {"doc_duoc": True, "hinh_dang": ten, "cot_ngay": str(cot),
            "som": som, "muon": muon, "so_dong": int(len(kq)),
            "cot": [str(c) for c in kq.columns], "doi_chung_som": som_gia}


def o_B(mkt, ma_list: list[str], nghi: float) -> dict:
    """Ô B — bao nhiêu mã trong rổ chuẩn có dữ liệu."""
    import pandas as pd

    den = _hom_nay()
    print(f"\n{'=' * 62}\nO B · DO PHU — {len(ma_list)} ma cua ro chuan\n{'=' * 62}")
    co: list[str] = []
    khong: list[str] = []
    for i, ma in enumerate(ma_list, 1):
        try:
            _, kq, _ = goi_thu(mkt.equity(ma).foreign_flow, XIN_TU, den)
        except Exception:  # noqa: BLE001
            kq = None
        n = _so_dong(kq) if isinstance(kq, pd.DataFrame) else None
        (co if n else khong).append(ma)
        if i % 10 == 0 or i == len(ma_list):
            print(f"  {i:>3}/{len(ma_list)}  co {len(co)} · khong {len(khong)}")
        time.sleep(nghi)
    print(f"\n  CO du lieu  : {len(co)}/{len(ma_list)}")
    print(f"  KHONG co    : {len(khong)}/{len(ma_list)}  {khong[:20]}")
    return {"co": len(co), "tong": len(ma_list), "thieu": khong}


def o_D_bam(eq, ra: Path) -> dict:
    """Ô D — băm một CỬA SỔ CỐ ĐỊNH để lần đọc sau so được.

    Point-in-time KHÔNG kiểm được trong một phiên: một chuỗi bị sửa lại
    (restate) trông y hệt một chuỗi không bị sửa, nếu chỉ đọc một lần.
    Nên lượt này chỉ CHỤP; phép so nằm ở mốc ngày khai trong tiêu chí.
    """
    import pandas as pd

    tu, den = "2025-01-02", "2025-06-30"
    print(f"\n{'=' * 62}\nO D · CHUP CUA SO CO DINH {tu} -> {den}\n{'=' * 62}")
    ten, kq, _ = goi_thu(eq.foreign_flow, tu, den)
    if not ten or not isinstance(kq, pd.DataFrame) or kq.empty:
        print("  khong chup duoc")
        return {"chup_duoc": False}
    csv = kq.to_csv(index=False)
    bam = hashlib.sha256(csv.encode("utf-8")).hexdigest()
    print(f"  {len(kq)} dong · sha256 {bam}")
    ra.write_text(csv, encoding="utf-8")
    print(f"  luu: {ra}")
    return {"chup_duoc": True, "bam": bam, "so_dong": int(len(kq)),
            "tu": tu, "den": den}


def so_khop_lich(ngay_a, ngay_b) -> tuple[int, int, int]:
    """(chung, chỉ có ở A, chỉ có ở B) trên phần GIAO của hai khoảng.

    HÀM THUẦN. Cắt về phần giao trước khi so, vì hai chuỗi dài khác nhau
    thì phần thừa ở đầu không phải "thiếu" — nó nằm ngoài câu hỏi.
    """
    a, b = set(map(str, ngay_a)), set(map(str, ngay_b))
    if not a or not b:
        return 0, len(a), len(b)
    tu, den = max(min(a), min(b)), min(max(a), max(b))
    a = {x for x in a if tu <= x <= den}
    b = {x for x in b if tu <= x <= den}
    return len(a & b), len(a - b), len(b - a)


def soi_ky(mkt, ma_a: str, ma_b: str) -> dict:
    """Ba phép soi mà một CON SỐ TỔNG không nói được.

    Tiêu chí ĐO 14 ký sẵn: *"một ô ĐẠT phải kiểm bằng mắt trên dữ liệu
    thô, không tin con số tổng"* — vì mọi ô đạt là chiều dễ chịu, và đó
    đúng là chiều quy tắc số 1 bảo phải nghi ngờ.

    1. MÃ CÓ THẬT SỰ ĐỔI KẾT QUẢ KHÔNG. Một API bỏ qua tham số `symbol`
       cho ra **71/71 mã có dữ liệu** y hệt một API phục vụ đủ cả rổ.
    2. CHUỖI CÓ KHỚP LỊCH PHIÊN KHÔNG. Thiếu một phần các phiên thì phép
       ghép vào giá tạo lỗ hổng IM LẶNG, không báo gì.
    3. GIÁ TRỊ CÓ BIẾN THIÊN KHÔNG. Agent `news` là hằng số 50 suốt nhiều
       tháng mà không ai thấy — một cột hằng số vẫn "có dữ liệu".
    """
    import hashlib

    import pandas as pd

    den = _hom_nay()
    print(f"\n{'=' * 62}\nSOI KY — ba cau mot con so tong khong tra loi duoc\n{'=' * 62}")
    ra: dict = {}

    _, fa, _ = goi_thu(mkt.equity(ma_a).foreign_flow, XIN_TU, den)
    _, fb, _ = goi_thu(mkt.equity(ma_b).foreign_flow, XIN_TU, den)
    if not isinstance(fa, pd.DataFrame) or not isinstance(fb, pd.DataFrame):
        print("  khong keo du hai ma -> CHUA KIEM DUOC")
        return {"doc_duoc": False}

    # --- 1. ma co doi ket qua khong
    ba = hashlib.sha256(fa.to_csv(index=False).encode()).hexdigest()[:16]
    bb = hashlib.sha256(fb.to_csv(index=False).encode()).hexdigest()[:16]
    khac = ba != bb
    print(f"\n  1. MA CO DOI KET QUA KHONG")
    print(f"     {ma_a}: {len(fa)} dong · bam {ba}")
    print(f"     {ma_b}: {len(fb)} dong · bam {bb}")
    print(f"     -> {'KHAC NHAU, ma CO duoc doc' if khac else 'GIONG HET — API BO QUA tham so ma'}")
    ra["ma_doi_ket_qua"] = khac

    # --- 2. khop lich phien
    ca = _cot_ngay(fa)
    _, ga, _ = goi_thu(mkt.equity(ma_a).ohlcv, XIN_TU, den)
    print(f"\n  2. KHOP LICH PHIEN ({ma_a}, tren phan GIAO cua hai khoang)")
    if isinstance(ga, pd.DataFrame) and ca is not None and _cot_ngay(ga) is not None:
        n_a = [str(x)[:10] for x in fa[ca]]
        n_g = [str(x)[:10] for x in ga[_cot_ngay(ga)]]
        chung, chi_kn, chi_gia = so_khop_lich(n_a, n_g)
        tong = chung + chi_kn + chi_gia
        print(f"     chung          : {chung}")
        print(f"     chi co khoi ngoai: {chi_kn}")
        print(f"     chi co gia       : {chi_gia}")
        print(f"     -> phu {chung}/{chung + chi_gia} phien co gia"
              f" ({100 * chung / max(1, chung + chi_gia):.1f}%)")
        ra["khop_lich"] = {"chung": chung, "chi_khoi_ngoai": chi_kn,
                           "chi_gia": chi_gia, "tong": tong}
    else:
        print("     khong doc duoc -> CHUA KIEM DUOC")

    # --- 3. bien thien
    print(f"\n  3. GIA TRI CO BIEN THIEN KHONG ({ma_a})")
    for cot in ("net_val", "net_vol", "buy_val"):
        if cot not in fa.columns:
            continue
        s = pd.to_numeric(fa[cot], errors="coerce")
        nac = int(s.nunique())
        print(f"     {cot:<9} {nac} gia tri khac nhau · {int((s == 0).sum())} so 0"
              f" · {int(s.isna().sum())} rong · min {s.min():.3g} max {s.max():.3g}")
        ra.setdefault("bien_thien", {})[cot] = nac
    # --- 4. ty le so 0 co DUNG YEN theo thoi gian khong
    print(f"\n  4. TY LE SO 0 THEO NAM ({ma_a})")
    print("     Mot cot 'co bien thien' van co the doi BAN CHAT giua cac nam.")
    print("     Neu ty le nay troi, moi dac trung dem theo thoi gian — 'bao nhieu")
    print("     phien ke tu lan mua rong gan nhat' — se troi theo NO chu khong")
    print("     theo thi truong.")
    if ca is not None and "net_val" in fa.columns:
        tam = pd.DataFrame({
            "nam": pd.to_datetime(fa[ca], errors="coerce").dt.year,
            "v": pd.to_numeric(fa["net_val"], errors="coerce"),
        }).dropna(subset=["nam"])
        bang = tam.groupby("nam").agg(dong=("v", "size"),
                                      so_0=("v", lambda s: int((s == 0).sum())))
        bang["ty_le_0"] = (100 * bang.so_0 / bang.dong).round(1)
        for d in bang.to_string().splitlines():
            print(f"     | {d}")
        ra["ty_le_0_theo_nam"] = {int(k): float(v)
                                  for k, v in bang["ty_le_0"].items()}

    ra["doc_duoc"] = True
    return ra


def phan_dinh(a: dict, b: dict) -> tuple[int, str]:
    """Đọc theo ĐÚNG bảng đã ký, không nới.

    Vế ĐỐI CHỨNG đứng TRƯỚC mọi phán quyết, vì không có nó thì một chuỗi
    ngắn không tách được thành hai nguyên nhân ngược nhau. Bản đầu của
    hàm này có một nhánh `pass` rơi thẳng xuống KẾT CỤC 3 — tức đọc ca
    *"tham số ngày bị bỏ qua ở CẢ HAI lời gọi"* thành *"nguồn không đủ
    sâu"*. Đó đúng là lỗi 66, mắc ngay trong dụng cụ dựng ra để tránh nó.
    """
    if not a.get("doc_duoc"):
        return 2, f"CHUA KIEM DUOC — {a.get('vi_sao', '')}"
    som = a["som"]
    doi_chung = a.get("doi_chung_som")
    if not doi_chung:
        return 2, "CHUA KIEM DUOC — doi chung duong khong doc duoc"
    dat_a = som <= MOC_PHU_CACHE_MAC_DINH
    if not dat_a and doi_chung > MOC_PHU_CACHE_MAC_DINH:
        return 2, ("CHUA KIEM DUOC — doi chung CUNG ngan: khong tach duoc"
                   " 'nguon chi phuc vu tung ay ngay' voi 'tham so ngay bi bo qua'")
    co = b.get("co")
    if co is None:
        return 2, ("CHUA KIEM DUOC — o B bi BO QUA, chua do do phu."
                   " Mot o bo qua KHONG duoc doc thanh mot o do duoc 0.")
    dat_b = co >= NGUONG_PHU_DAT
    hong_b = co < NGUONG_PHU_HONG
    if dat_a and dat_b:
        return 0, "KET CUC 1 — dung duoc: du sau VA du rong"
    if dat_a and not dat_b:
        return 1, ("KET CUC 2 — du sau, KHONG du rong"
                   + (" (duoi nua ro)" if hong_b else ""))
    return 1, "KET CUC 3 — KHONG du sau: khong dung lam vung kiem dinh duoc"


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DO 14 — kha thi du lieu khoi ngoai")
    ap.add_argument("--so-ma", type=int, default=0,
                    help="chi do N ma dau cua ro (0 = ca ro)")
    ap.add_argument("--bo-o-b", action="store_true", help="bo qua o B")
    ap.add_argument("--nghi", type=float, default=0.25, help="giay nghi giua hai loi goi")
    ap.add_argument("--soi-ky", action="store_true",
                    help="ba phep soi tren du lieu THO (xem soi_ky)")
    ap.add_argument("--ma-doi-chung", default="VCB",
                    help="ma thu hai dung cho phep soi 1")
    ap.add_argument("--ra", default="", help="noi ghi ket qua JSON")
    a = ap.parse_args(tham_so)

    try:
        import vnstock_data as vd
    except Exception as e:  # noqa: BLE001
        print(f"CHUA KIEM DUOC — import vnstock_data no: {type(e).__name__}: {e}")
        return 2

    from vn100_symbols import VN100_SYMBOLS

    mkt = vd.Market()
    eq = mkt.equity(MA_MOC)

    ket_a = o_A_va_C(eq, in_du_lieu=True)
    ma_list = VN100_SYMBOLS[:a.so_ma] if a.so_ma else list(VN100_SYMBOLS)
    ket_b = {"co": None, "tong": 0, "thieu": []} if a.bo_o_b else o_B(mkt, ma_list, a.nghi)

    thu_muc = Path(a.ra).parent if a.ra else GOC
    ket_d = o_D_bam(eq, thu_muc / "do14_cua_so_2025H1.csv") if ket_a.get("doc_duoc") else {}
    ket_soi = soi_ky(mkt, MA_MOC, a.ma_doi_chung) if a.soi_ky else {}

    ma_thoat, cau = phan_dinh(ket_a, ket_b)
    print(f"\n{'=' * 62}\nPHAN DINH: {cau}\n{'=' * 62}")
    print(f"  o A som nhat : {ket_a.get('som', '?')}   (moc ky truoc {MOC_PHU_CACHE_MAC_DINH}"
          f" · rong {MOC_PHU_CACHE_RONG})")
    print(f"  o B do phu   : {ket_b.get('co', '?')}/{ket_b.get('tong', '?')}"
          f"   (moc ky truoc {NGUONG_PHU_DAT})")

    if a.ra:
        Path(a.ra).write_text(json.dumps(
            {"o_A": ket_a, "o_B": ket_b, "o_D": ket_d, "soi_ky": ket_soi,
             "phan_dinh": cau, "ma_thoat": ma_thoat, "ngay": _hom_nay()},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ghi: {a.ra}")
    return ma_thoat


if __name__ == "__main__":
    sys.exit(main())
