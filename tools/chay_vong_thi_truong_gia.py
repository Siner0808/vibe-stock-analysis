"""`chay-vong` — chạy vòng học khép kín trên MỘT thị trường giả và in từng bước (C4 Lát 3, BƯỚC 290).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 5, 7, 8 ("Lát 3") và 17. Đặc tả là nguồn duy nhất.

MỘT thị trường, từ đầu tới cuối: sinh (Tầng 1) → bộ đề xuất cơ sở → khai (mỗi tháng một) → xác nhận bằng
`cham_xac_nhan.cham` THẬT → nâng cấp (một đời) → huỷ ứng viên đang chờ → kiểm tiến-về-trước. SAU KHI vòng đã quyết,
dụng cụ chấm đọc oracle (bảng sự thật) để in ΔIC_true của từng spec — vòng không bao giờ thấy nó (gác G4).

KHÔNG CÓ TỶ LỆ, KHÔNG CÓ PHÁN ĐẠT/TRƯỢT: một thị trường là một biên bản minh hoạ, không phải kết quả (đó là Lát 5).

DÒNG HẠT. Chỉ 1 và 9001 (dòng thử của test, ngoài năm dòng chính của mục 4.8). Dòng 2, 3, 4 dành cho lượt chạy chính
của Lát 5 và dòng 5 cho chẩn đoán SAU khi đã nhìn kết quả (bất biến 7): mọi đường vào bộ sinh đi qua `kiem_luong`,
nổ với mọi dòng khác — không sinh, không chạy, không đọc thị trường nào của chúng.

CHẠY
    ./.venv/Scripts/python.exe -X utf8 tools/chay_vong_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2
    ./.venv/Scripts/python.exe -X utf8 tools/chay_vong_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2 --ghi

`--muc` lấy κ của bốn mức 0× · 0,5× · 1× · 2× MDE₈₀ từ `docs/thi-truong-gia-hieu-chuan.json` (Lát 2); `--kappa` đặt thẳng.
`--ghi` ghi biên bản vào đúng MỘT file (`docs/vong-hoc-thi-truong-gia-mau.md`, trong khối mã) bằng `va_an_toan.ghi`.
Mã thoát: 0 chạy xong · 2 lỗi cấu hình (dòng hạt cấm, đối số sai). Không chạm Sheets, `*.db`, sổ ứng viên thật.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

for _luong_ra in (sys.stdout, sys.stderr):   # BƯỚC 129
    try:
        _luong_ra.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import cham_bong as cb  # noqa: E402
import cham_xac_nhan as cx  # noqa: E402
import thi_truong_gia as T  # noqa: E402
import vong_hoc_gia as V  # noqa: E402

DUONG_CONG_CU = Path(__file__).resolve().parent
DUONG_HIEU_CHUAN = GOC / "docs" / "thi-truong-gia-hieu-chuan.json"
DUONG_BIEN_BAN = GOC / "docs" / "vong-hoc-thi-truong-gia-mau.md"

# ── hạt: CHỈ dòng 1 và dòng thử 9001 ─────────────────────────────────────────
LUONG_TEST = 9001
LUONG_DUOC_PHEP = (1, 9001)
#: Dòng của mục 4.8 mà dụng cụ này KHÔNG được đụng: 2, 3, 4 (lượt chính, Lát 5) và 5 (chẩn đoán sau khi nhìn kết quả).
LUONG_BI_CHAN = (2, 3, 4, 5)


def kiem_luong(luong) -> None:
    """Cửa DUY NHẤT tới bộ sinh: chỉ dòng hạt 1 và 9001. Nổ với 2, 3, 4, 5, 6… và với kiểu lạ."""
    if isinstance(luong, bool) or not isinstance(luong, (int, np.integer)) or int(luong) not in LUONG_DUOC_PHEP:
        raise ValueError(
            f"chay-vong chi dung dong hat {LUONG_DUOC_PHEP}; nhan {luong!r}. Dong 2, 3, 4 danh cho luot chay chinh "
            f"cua Lat 5 va dong 5 cho chan doan sau khi nhin ket qua (bat bien 7) — khong sinh, khong chay, khong doc.")


# ── một thị trường ───────────────────────────────────────────────────────────

def doc_kappa_muc(he_so: float, duong: Path = DUONG_HIEU_CHUAN) -> float:
    """κ của mức `he_so` × MDE₈₀ đọc từ file hiệu chuẩn của Lát 2 (đọc, không ghi)."""
    muc = json.loads(Path(duong).read_text(encoding="utf-8"))["muc"]
    kp = [m["kappa"] for m in muc if abs(m["he_so"] - he_so) < 1e-9]
    if len(kp) != 1:
        raise ValueError(f"file hieu chuan khong co dung mot muc he_so={he_so}: {[m['he_so'] for m in muc]}")
    return float(kp[0])


def chay_mot_thi_truong(luong: int, chi_so: int, kappa: float, co_oracle: bool = True,
                        so_hoan_vi: int = cx.SO_HOAN_VI) -> dict:
    """Sinh MỘT thị trường (qua `kiem_luong`), chạy vòng, RỒI mới (nếu `co_oracle`) đọc oracle.
    Trả `{"thi_truong": {...}, "vong": biên bản của vòng, "su_that": bảng sự thật hoặc None}`."""
    kiem_luong(luong)
    tt = T.sinh_thi_truong(luong, chi_so, float(kappa), co_su_that=False)
    vong = V.chay_vong(tt.dong_quyet_dinh(), tt.gia, so_hoan_vi=so_hoan_vi)       # vòng chỉ nhận dòng + giá
    su_that = T.tinh_su_that(luong, chi_so, float(kappa)) if co_oracle else None  # oracle: SAU khi vòng đã quyết
    return {"thi_truong": {"luong": int(luong), "chi_so": int(chi_so), "kappa": float(kappa),
                           "so_ma": len(tt.ma), "ma_dau": tt.ma[0], "ma_cuoi": tt.ma[-1]},
            "vong": vong, "su_that": su_that}


# ── biên bản ─────────────────────────────────────────────────────────────────

def _so(x, nd=4) -> str:
    return "—" if x is None else f"{x:+.{nd}f}"


def bien_ban(kq: dict) -> list[str]:
    """Biên bản đọc được của MỘT thị trường, từng bước. Chỉ in số đã tính; không phán đạt/trượt."""
    tt, v, st = kq["thi_truong"], kq["vong"], kq["su_that"]
    ra = [f"THỊ TRƯỜNG GIẢ — dòng hạt {tt['luong']}, chỉ số {tt['chi_so']}, κ = {tt['kappa']:.6f}  "
          f"({tt['so_ma']} mã {tt['ma_dau']}…{tt['ma_cuoi']}, {v['so_phien']} phiên {v['ngay_dau']} → {v['ngay_cuoi']})",
          "(Một thị trường là một biên bản minh hoạ. KHÔNG có tỷ lệ nào ở đây; đó là Lát 5.)", ""]
    xep = v["de_xuat"]["xep"]
    chon = v["de_xuat"]["da_chon"]
    ra += [f"BƯỚC 1 — BỘ ĐỀ XUẤT CƠ SỞ (chỉ thấy phiên 0…{v['cua_so_nhin'] - 1}; "
           f"{xep[0].get('n_phien', '?')} phiên có nhãn, {xep[0].get('n_ma', '?')} mã). Δ = IC(spec) − IC(điểm đã ghi):"]
    for h, x in enumerate(xep, 1):       # bộ đề xuất cắm vào (C3) có thể không khai IC: in "—" thay vì nổ
        ra.append(f"   {h:>2}. {x['ten']:<20} Δ = {_so(x['delta'])}  (IC spec {_so(x.get('ic_spec'))}, "
                  f"IC đã ghi {_so(x.get('ic_da_ghi'))}){'   ← khai' if x['ten'] in chon else ''}")
    ra += [f"   khai {len(chon)} spec đầu có Δ > 0, mỗi spec một tháng: {', '.join(chon) or '(không có)'}", ""]
    ra.append(f"BƯỚC 2 — KHAI (sổ ứng viên giả trong bộ nhớ; K = {v['K']} ứng viên đã khai)")
    for m in v["lich"]:
        doc = f"phiên {m['doc_phien']} ({m['doc_ngay']})" if m["doc_ngay"] else f"phiên {m['doc_phien']} (ngoài dữ liệu)"
        ra.append(f"   {m['ma']} = {m['ten']:<20} khai phiên {m['khai_phien']} ({m['khai_ngay']}), đọc {doc}")
    ra.append("")
    ra.append(f"BƯỚC 3 — XÁC NHẬN (`cham_xac_nhan.cham`: đọc ở đúng {cb.MOC_DOC} phiên có nhãn, "
              f"ngưỡng 0,05/K, null hoán vị mã)")
    if not v["doc"]:
        ra.append("   (chưa có ứng viên nào tới phiên đọc)")
    for d in v["doc"]:
        ra.append(f"   {d['ma']} đọc phiên {d['phien_doc']} ({d['ngay_doc']}): K = {d['K']}, ngưỡng {d['nguong']:.5f}, "
                  f"{d['n_phien']} phiên × {d['n_ma']} mã → {d['trang_thai']}  "
                  f"(Δ = {_so(d['delta'])}, p = {'—' if d['p'] is None else format(d['p'], '.3g')})")
    ra.append("")
    pb = v["so_phien_ban"]["phien_ban"]
    ra.append("BƯỚC 4 — NÂNG CẤP (chỉ trong thị trường giả; một đời)")
    if len(pb) > 1:
        b = pb[-1]
        ra += [f"   phiên bản {b['so']} từ {b['ma_ung_vien']}: spec {json.dumps(b['spec']['trong_so'], ensure_ascii=False)}",
               f"   đọc ở phiên {b['phien_doc']}, HIỆU LỰC TỪ PHIÊN SAU: phiên {b['hieu_luc_tu_phien']} ({v['hieu_luc_ngay']})",
               f"   bằng chứng: p = {b['bang_chung']['p']:.3g}, Δ = {_so(b['bang_chung']['delta'])}, "
               f"{b['bang_chung']['n_phien']} phiên, K = {b['bang_chung']['K']}, hạt {b['bang_chung']['hat']}"]
    else:
        ra.append("   không có nâng cấp (không ứng viên nào đọc ra QUA)")
    ra.append(f"   huỷ vì nâng cấp (K vẫn đếm = {v['K']}): {', '.join(v['huy']) or '(không)'}")
    ra.append("   trạng thái cuối: " + ", ".join(f"{m} = {s}" for m, s in v["trang_thai"].items()))
    ra.append("")
    tv = v["tien_ve_truoc"]
    ra.append("BƯỚC 5 — KIỂM TIẾN-VỀ-TRƯỚC (chỉ phiên từ phiên hiệu lực trở đi)")
    if tv is None:
        ra.append("   không có nâng cấp nên không có gì để kiểm")
    else:
        ra.append(f"   từ {tv['tu_ngay']}: {tv['n_phien']}/{tv['so_phien']} phiên có nhãn × {tv['n_ma']} mã"
                  f"{'' if tv['du_cua_so'] else '  (CỬA SỔ CHƯA ĐỦ)'}")
        ra.append(f"   IC điểm đã ghi {_so(tv['ic_da_ghi'])}, IC phiên bản mới {_so(tv['ic_phien_ban_moi'])}, "
                  f"ΔIC thực hiện = {_so(tv['delta_ic'])}  (một thị trường, không có KTC)")
    ra.append("")
    ra.append("BƯỚC 6 — SỰ THẬT (oracle, đọc SAU khi vòng đã quyết; vòng không thấy nó)")
    if st is None:
        ra.append("   (bỏ qua: --khong-oracle)")
    else:
        ten = list(dict.fromkeys([*chon, T.TEN_SPEC_G, T.TEN_SPEC_Z, T.TEN_SPEC_H]))
        for t in ten:
            s = st["spec"][t]
            ra.append(f"   {t:<20} ΔIC_true = {_so(s['delta_ic'])} ± {s['se_mc']:.4f}"
                      f"{'   (đã khai)' if t in chon else ''}")
        ra.append(f"   (mẫu oracle {st['so_phien']} phiên, hạt {st['hat']}; ± là sai số Monte Carlo ước lượng)")
    return ra


# ── ghi (MỘT file) ───────────────────────────────────────────────────────────

def _nap_va_an_toan():
    s = importlib.util.spec_from_file_location("va_an_toan_chay_vong", DUONG_CONG_CU / "va_an_toan.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def noi_dung_tep(dong: list[str]) -> str:
    """Biên bản trong một khối mã Markdown (`*.txt` bị `.gitignore` của repo)."""
    return ("# Biên bản mẫu của vòng học trên thị trường giả (BƯỚC 290)\n\n"
            "Do `tools/chay_vong_thi_truong_gia.py --ghi` sinh; một thị trường, không phải kết quả.\n\n"
            "```text\n" + "\n".join(dong) + "\n```\n")


def ghi_bien_ban(dong: list[str], duong: Path = DUONG_BIEN_BAN) -> None:
    _nap_va_an_toan().ghi(duong, noi_dung_tep(dong))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--luong", type=int, default=LUONG_TEST, help="dòng hạt: chỉ 1 hoặc 9001")
    ap.add_argument("--chi-so", type=int, default=1)
    nhom = ap.add_mutually_exclusive_group()
    nhom.add_argument("--muc", type=float, default=None, help="hệ số MDE₈₀ của file hiệu chuẩn: 0 · 0.5 · 1 · 2")
    nhom.add_argument("--kappa", type=float, default=None)
    ap.add_argument("--khong-oracle", action="store_true")
    ap.add_argument("--ghi", action="store_true", help="ghi biên bản vào docs/vong-hoc-thi-truong-gia-mau.md")
    a = ap.parse_args(argv)
    try:
        kiem_luong(a.luong)
        if a.kappa is not None:
            kappa = a.kappa
        else:
            kappa = doc_kappa_muc(2.0 if a.muc is None else a.muc)
        kq = chay_mot_thi_truong(a.luong, a.chi_so, kappa, co_oracle=not a.khong_oracle)
    except ValueError as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 2
    dong = bien_ban(kq)
    print("\n".join(dong))
    if a.ghi:
        ghi_bien_ban(dong)
        print(f"đã ghi {DUONG_BIEN_BAN.relative_to(GOC).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
