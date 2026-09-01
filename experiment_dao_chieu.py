"""
experiment_dao_chieu.py
──────────────────────────────────────────────────────────────────────
KIỂM GIẢ THUYẾT ĐẢO CHIỀU — bản KHAI TRƯỚC, một lần, không lặp lại.

GIẢ THUYẾT ĐẾN TỪ ĐÂU (quan trọng hơn nội dung của nó)
Tài liệu ngoài về HOSE: danh mục "kẻ thua" vượt "kẻ thắng" 1,80% và 2,17%
ở tháng thứ hai và thứ ba; momentum VN yếu và chỉ tồn tại ở nhịp rất dài.
Giả thuyết vì thế **cố định TRƯỚC khi nhìn dữ liệu dự án** — đó là điều
duy nhất làm nó hợp lệ với bất biến 7 và 8. Lật dấu SAU khi thấy số âm
thì không hợp lệ, và file này không có đường nào để làm việc đó.

DẤU ĐƯỢC KHAI TRƯỚC, NÊN PHÉP KIỂM MỘT PHÍA
Đảo chiều nghĩa là rho(lợi nhuận quá khứ, lợi nhuận vượt rổ tương lai)
**ÂM**. Một rho DƯƠNG có ý nghĩa KHÔNG phải "tìm thấy tín hiệu" — nó là
momentum, tức **bác bỏ** giả thuyết này. Hai kết luận đó được in bằng hai
câu khác nhau, cố ý.

Ô CHÍNH CHỌN THEO LỰC PHÁT HIỆN, KHÔNG THEO Ý NGHĨA KINH TẾ
Đây là chỗ BƯỚC 7 đã sai và ghi lại lỗi của chính nó: test chính hồi đó
khai là h=20 vì nó khớp nhịp nắm giữ thật, trong khi bảng lực — viết
trước — đã ghi h=20 là sát biên. Bảng lực cho phép kiểm này, tính TRƯỚC
khi đo bất kỳ tương quan nào (ba đại lượng dùng để tính nó — cỡ mẫu, n
hiệu dụng, độ lệch chuẩn của nhãn — đều không phụ thuộc liên kết đặc
trưng↔nhãn):

      J    h   quan sát   n hiệu dụng   phát hiện 80%   rào @5%   đủ lực?
     21   21     73.584         3.345           0,043     0,044      CÓ
     10   10     74.343         6.758           0,030     0,066      CÓ
      5    5     74.693        12.449           0,022     0,095      CÓ
     21   42     72.135         1.678           0,061     0,031     không
     21   63     70.686         1.104           0,075     0,025     không

**Phát hiện của tài liệu nằm ở tháng 2–3, tức h=42 — và ô đó KHÔNG đủ
lực.** Nó vẫn được chạy, nhưng kết luận ở đó đã được khai TRƯỚC là không
đọc được, bất kể con số ra sao. Ô chính là (21, 21) — đảo chiều một tháng
cổ điển, ô duy nhất vừa được tài liệu đỡ vừa đủ lực.

Cỡ hiệu ứng tài liệu ngụ ý: chênh 2%/tháng trên σ ≈ 9% là 0,22 độ lệch;
quy về tương quan hạng qua chênh thập phân vị (2×E[z|top10%] = 3,51) cho
**rho ≈ 0,063**. Trên rào 0,044 và trên mức phát hiện 0,043 — nên phép
kiểm này CÓ lực với đúng cỡ hiệu ứng mà tài liệu công bố.

MIN_HIST 80, KHÔNG PHẢI 250
250 tồn tại trong `experiment_tran_dac_trung.py` vì SMA50/SMA200 trả None
dưới mốc đó. Đặc trưng ở đây là lợi nhuận quá khứ thuần — không có SMA
nào — nên ràng buộc ấy không áp dụng, và 80 phiên (gần 4× cửa sổ hình
thành dài nhất) cho thêm lực. Đây là lựa chọn thiết kế, không phải kết
quả: nó được chốt trước lượt chạy.

HAI CHẶNG, KHAI TRƯỚC CẢ HAI
  Chặng 1 — toàn cache. Không tiêu một phiên sạch nào.
  Chặng 2 — CHỈ chạy nếu chặng 1 ĐẠT ở ô chính: xác nhận trên vùng sạch
            `docs/moc_du_lieu_sach.json`. Khai ở đây để nó không thể được
            phát minh ra sau khi thấy số.

PHÂN TẦNG THANH KHOẢN LÀ THỨ CẤP, VÀ THIẾU LỰC — NÓI TRƯỚC
Tài liệu nói đảo chiều **chết vì chi phí ở vốn hoá nhỏ**, chỉ sống ở vốn
hoá lớn. Cắt còn một phần ba làm n hiệu dụng chia ba (phát hiện ×1,73)
TRONG KHI rào lại CAO HƠN ở nhóm lớn vì σ nhỏ hơn. Hai chiều cùng xấu.
Nên phân tầng chỉ được báo cáo như quan sát, không phải kết luận.

Xếp hạng thanh khoản dựng NHÂN QUẢ: trung vị 250 phiên gần nhất tính tới
hết phiên T, rồi xếp hạng chéo trong đúng ngày T. Xếp hạng bằng trung vị
toàn mẫu là nhìn trộm — mã thanh khoản lên sau sẽ được gán "lớn" cho cả
giai đoạn nó còn nhỏ.

CHỨNG CỨ DƯƠNG VẪN BẮT BUỘC
Cùng lý do như script anh em: không có nó thì "không có tín hiệu" và
"máy đo hỏng" trông y hệt nhau. Ở đây tín hiệu tiêm vào mang dấu ÂM.

KẾT QUẢ ĐÃ CHẠY: `docs/STATE.md`, mục "BƯỚC 9".
"""
import argparse
import sys

import numpy as np
import pandas as pd

from experiment_tran_dac_trung import (chi_phi_vong, nap_gia, nhan_vuot_ro,
                                       rao_hoa_von, rho_hang, san_nhieu)

sys.stdout.reconfigure(encoding="utf-8")

#: Ô CHÍNH — khai trước, chọn theo bảng lực ở đầu file.
J_CHINH, H_CHINH = 21, 21

#: Ô thứ cấp. Có mặt trong bản khai trước nên chúng không phải "chạy thêm
#: cho tới khi ra số đẹp"; nhưng chúng không được đọc như kết luận chính.
O_THU_CAP = ((10, 10), (5, 5), (21, 42), (21, 63))

#: Khai TRƯỚC là thiếu lực. Kết luận ở các ô này KHÔNG đọc được, dù số ra
#: sao. Ghi ở đây để không ai đọc chúng như kết quả sau khi thấy con số.
O_THIEU_LUC = ((21, 42), (21, 63))

#: Không có SMA nào trong đặc trưng này nên mốc 250 của script anh em
#: không áp dụng. 80 phiên ≈ 4× cửa sổ hình thành dài nhất.
MIN_HIST = 80

#: Cửa sổ tính trung vị thanh khoản, tính tới hết phiên T (nhân quả).
CUA_SO_THANH_KHOAN = 250

SO_HOAN_VI = 1000
ALPHA = 0.05


def loi_nhuan_qua_khu(df: pd.DataFrame, J: int) -> np.ndarray:
    """Log lợi nhuận J phiên tính TỚI HẾT phiên T. Không nhìn trộm.

    Nhãn đã lo phần vào lệnh ở T+1 (`nhan_vuot_ro` có `shift(-1)`), nên ở
    đây không được dịch thêm lần nữa — dịch hai lần là bỏ mất một phiên.
    """
    c = np.log(df["close"].to_numpy(float))
    x = np.full(len(c), np.nan)
    x[J:] = c[J:] - c[:-J]
    return x


def hang_thanh_khoan(kh: dict) -> pd.DataFrame:
    """Hạng chéo của thanh khoản, mỗi ngày một hạng, hoàn toàn nhân quả."""
    gtgd = pd.DataFrame({m: d["close"] * d["volume"] for m, d in kh.items()})
    gtgd = gtgd.sort_index()
    tr = gtgd.rolling(CUA_SO_THANH_KHOAN,
                      min_periods=CUA_SO_THANH_KHOAN).median()
    return tr.rank(axis=1, pct=True)


def bang(kh: dict, J: int, h: int, tang: str = "tat_ca") -> tuple:
    """(x, y, chỉ số theo mã) — một đặc trưng duy nhất, không tham số nào."""
    nhan = nhan_vuot_ro(kh, h)
    hang = hang_thanh_khoan(kh) if tang != "tat_ca" else None
    xs, ys, mas = [], [], []
    for ma, d in kh.items():
        x = loi_nhuan_qua_khu(d, J)
        y = nhan[ma].reindex(d.index).to_numpy(float)
        ok = ~np.isnan(x) & ~np.isnan(y)
        ok[:MIN_HIST] = False
        if tang != "tat_ca":
            r = hang[ma].reindex(d.index).to_numpy(float)
            gioi_han = r >= 2 / 3 if tang == "lon" else r <= 1 / 3
            ok = ok & ~np.isnan(r) & gioi_han
        if int(ok.sum()) < 60:
            continue
        xs.append(x[ok])
        ys.append(y[ok])
        mas.append(np.full(int(ok.sum()), ma))
    x_all = np.concatenate(xs)
    y_all = np.concatenate(ys)
    ma_arr = np.concatenate(mas)
    chi_so = {m: np.flatnonzero(ma_arr == m) for m in np.unique(ma_arr)}
    return x_all, y_all, chi_so


def phan_xu(rho: float, p5: float, p95: float, rao: float) -> str:
    """LUẬT QUYẾT ĐỊNH — viết trong mã, chốt trước khi chạy.

    Ba kết cục khác nhau, ba câu khác nhau. Gộp "không đạt" với "ngược
    dấu" là đánh mất đúng phần thông tin đắt nhất của một phép kiểm có
    khai dấu trước.
    """
    if rho > p95:
        return "NGƯỢC DẤU — momentum, BÁC BỎ giả thuyết đảo chiều"
    if rho >= p5:
        return "không vượt sàn nhiễu"
    if abs(rho) < rao:
        return "vượt nhiễu, DƯỚI rào hoà vốn"
    return "ĐẠT — âm có ý nghĩa VÀ trên rào"


def kiem_o(kh: dict, J: int, h: int, rng, so_hoan_vi: int,
           tang: str = "tat_ca") -> dict:
    x, y, chi_so = bang(kh, J, h, tang)
    rho = rho_hang(x, y)
    null = san_nhieu(lambda yp: rho_hang(x, yp), y, chi_so, h, rng, so_hoan_vi)
    p5 = float(null[int(ALPHA * so_hoan_vi)])
    p95 = float(null[int((1 - ALPHA) * so_hoan_vi)])
    rao = rao_hoa_von(float(y.std()))
    return {"J": J, "h": h, "n": len(y), "n_eff": len(y) / (h + 1),
            "rho": rho, "p5": p5, "p95": p95, "rao": rao,
            "null_sd": float(null.std()),
            "phan_xu": phan_xu(rho, p5, p95, rao)}


def chung_cu_duong(kh: dict, J: int, h: int, rng, so_vong: int = 400) -> bool:
    """Tiêm tín hiệu ÂM có mức biết trước. Trả về: ô này có ĐỌC ĐƯỢC không."""
    x, y, chi_so = bang(kh, J, h)
    sigma = float(y.std())
    rao = rao_hoa_von(sigma)
    null = san_nhieu(lambda yp: rho_hang(x, yp), y, chi_so, h, rng, so_vong)
    p5 = float(null[int(ALPHA * so_vong)])

    print(f"\n── CHỨNG CỨ DƯƠNG · J={J} h={h} ──")
    print(f"  {len(y):,} quan sát · rào {rao:.3f} · sàn nhiễu(5%) {p5:.4f}")
    print(f"  {'tiêm vào':>14} {'rho tiêm':>10} {'rho đo được':>12} {'kêu?':>7}")
    bat = {}
    for he_so, ten in ((0.0, "không có gì"), (0.5, "nửa rào"),
                       (1.0, "đúng bằng rào"), (1.5, "1,5× rào")):
        muc = rao * he_so
        gia = -muc * (y / sigma) + np.sqrt(1 - muc ** 2) * \
            rng.standard_normal(len(y))
        r = rho_hang(gia, y)
        keu = r < p5
        bat[ten] = keu
        print(f"  {ten:>14} {-muc:>10.4f} {r:>12.4f} "
              f"{'CÓ' if keu else 'không':>7}")
    doc_duoc = (not bat["không có gì"]) and bat["đúng bằng rào"]
    print(f"  -> ô này {'ĐỌC ĐƯỢC' if doc_duoc else 'KHÔNG đọc được'}: "
          f"'không có gì' phải im VÀ 'đúng bằng rào' phải kêu")
    return doc_duoc


def _in_dong(k: dict, nhan_o: str = "") -> None:
    print(f"  {k['J']:>3} {k['h']:>4} {k['n']:>9,} {k['n_eff']:>8.0f}"
          f" {k['rho']:>9.4f} {k['p5']:>9.4f} {k['rao']:>8.3f}"
          f"  {k['phan_xu']}{nhan_o}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Kiem gia thuyet dao chieu")
    ap.add_argument("--hoan-vi", type=int, default=SO_HOAN_VI)
    ap.add_argument("--chung-cu-duong", action="store_true",
                    help="BAT BUOC de doc duoc ket qua null")
    ap.add_argument("--phan-tang", action="store_true",
                    help="chay them phan tang thanh khoan (THU CAP, thieu luc)")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    kh = nap_gia()
    if not kh:
        print("❌ Không đọc được mã nào từ cache.")
        return 1

    print("=" * 78)
    print("GIẢ THUYẾT ĐẢO CHIỀU — phép kiểm KHAI TRƯỚC, một phía, dấu ÂM")
    print(f"  {len(kh)} mã · min_history {MIN_HIST} · chi phí vòng "
          f"{chi_phi_vong():.2f}% · hoán vị {a.hoan_vi} · seed {a.seed}")
    print(f"  Ô CHÍNH: J={J_CHINH} h={H_CHINH}. Mọi ô khác là THỨ CẤP.")
    print("=" * 78)

    print(f"\n  {'J':>3} {'h':>4} {'quan sát':>9} {'n_eff':>8} {'rho':>9}"
          f" {'nhiễu5%':>9} {'rào':>8}  phán xử")
    chinh = kiem_o(kh, J_CHINH, H_CHINH, rng, a.hoan_vi)
    _in_dong(chinh, "   <<< Ô CHÍNH")
    for J, h in O_THU_CAP:
        k = kiem_o(kh, J, h, rng, a.hoan_vi)
        _in_dong(k, "   (thiếu lực — không đọc được)"
                 if (J, h) in O_THIEU_LUC else "   (thứ cấp)")

    print(f"\n  Sàn nhiễu hoán vị so với lý thuyết: sd đo được "
          f"{chinh['null_sd']:.4f} · lý thuyết 1/√n_eff = "
          f"{1 / np.sqrt(chinh['n_eff']):.4f}")
    print("  Hai số lệch nhau nhiều nghĩa là giả định n hiệu dụng sai —"
          " đọc lại bảng lực trước khi đọc phán xử.")

    if a.phan_tang:
        print("\n── PHÂN TẦNG THANH KHOẢN (THỨ CẤP, khai trước là thiếu lực) ──")
        print(f"  {'tầng':>10} {'quan sát':>9} {'n_eff':>8} {'rho':>9}"
              f" {'nhiễu5%':>9} {'rào':>8}")
        for tang, ten in (("lon", "lớn"), ("nho", "nhỏ")):
            k = kiem_o(kh, J_CHINH, H_CHINH, rng, a.hoan_vi, tang)
            print(f"  {ten:>10} {k['n']:>9,} {k['n_eff']:>8.0f}"
                  f" {k['rho']:>9.4f} {k['p5']:>9.4f} {k['rao']:>8.3f}")

    if a.chung_cu_duong:
        doc_duoc = chung_cu_duong(kh, J_CHINH, H_CHINH, rng)
        print(f"\n  KẾT LUẬN Ô CHÍNH: {chinh['phan_xu']}")
        if not doc_duoc:
            print("  ⚠️  Nhưng chứng cứ dương KHÔNG qua — câu trên không đọc được.")
    else:
        print("\n⚠️  CHƯA chạy chứng cứ dương. Một kết quả 'không vượt sàn")
        print("   nhiễu' ở trên CHƯA đọc được — có thể là không có tín hiệu,")
        print("   mà cũng có thể là phép đo thiếu lực. Chạy lại với")
        print("   --chung-cu-duong.")

    print("\n" + "=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
