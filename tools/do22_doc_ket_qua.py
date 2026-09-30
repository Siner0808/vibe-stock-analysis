"""ĐO 22 — dụng cụ đọc: ba phép kiểm cơ học + chênh giá vào, giữa hai sổ OOS.

Tiêu chí: `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 22. Alpha và KTC đọc ở log của
walk-forward; `tools/do20_ghep_tung_lenh.py` ghép từng lệnh. Dụng cụ này trả lời
ba câu mà tiêu chí đã ký đòi trước khi được đọc alpha:

  P4  Mọi giá VÀO của lệnh HNX/UPCoM ở luồng ĐÃ SỬA chia hết cho 100 (bước giá
      thật). Cùng phép đếm ở luồng ĐỐI CHỨNG được in để so — đối chứng KHÔNG
      được đạt 100% (nếu đạt thì phép kiểm này không phân biệt được gì).
  P5  (chỉ chế độ `--che-do ma`) Mọi lệnh của mã HOSE giống hệt từng lệnh giữa
      hai luồng: ở chế độ theo mã, mỗi mã chạy độc lập và bước giá HOSE không
      đổi, nên một lệnh HOSE khác đi là có dây chuyền không lường trước.
  P6  Giá VÀO ĐÃ SỬA >= giá vào ĐỐI CHỨNG ở mọi lệnh HNX/UPCoM cùng khoá (mã,
      ngày tín hiệu) VÀ cùng ngày vào: lưới 100đ thô hơn lưới 50đ và 10đ, mua
      làm tròn LÊN thì không thể thấp hơn.

Đọc kèm, không quyết định gì: chênh giá vào trung bình theo dải giá của các
lệnh chung khoá (`docs/STATE.md` BƯỚC 143 dựng lại +23,8đ / +26,3đ).

    ./.venv/Scripts/python.exe tools/do22_doc_ket_qua.py \
        --doi-chung <wf_oos.db> --sua <wf_oos.db> --che-do ma|ngay

CHỈ ĐỌC (`mode=ro`). Mã thoát 0 mọi phép kiểm đạt · 1 có phép kiểm hỏng ·
2 chưa kiểm được (thiếu file).
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

from san_giao_dich import tra_san  # noqa: E402
import do20_ghep_tung_lenh as g20  # noqa: E402


def _chia_het(x: float, b: int) -> bool:
    return abs(round(x / b) * b - x) < 1e-6


def _khac_san(ma: str) -> bool:
    return tra_san(ma) in ("HNX", "UPCOM")


def dai_gia(gia: float) -> str:
    return "<10k" if gia < 10_000 else ("10-50k" if gia < 50_000 else ">=50k")


def kiem(doi_chung: dict, sua: dict, che_do: str) -> dict:
    """Hàm THUẦN trên hai dict {(mã, ngày tín hiệu): dòng lệnh}."""
    def dem_luoi(so: dict) -> tuple[int, int]:
        v = [float(r["entry_price"]) for (m, _), r in so.items()
             if _khac_san(m) and r["entry_price"]]
        return sum(_chia_het(x, 100) for x in v), len(v)

    p4 = {"sua": dem_luoi(sua), "doi_chung": dem_luoi(doi_chung)}

    p5_khac: list = []
    if che_do == "ma":
        ma_hose = {k for k in set(doi_chung) | set(sua) if not _khac_san(k[0])}
        for k in sorted(ma_hose):
            a, b = doi_chung.get(k), sua.get(k)
            if a is None or b is None or g20._gia(a) != g20._gia(b) \
                    or a["status"] != b["status"]:
                p5_khac.append(k)

    chung = [k for k in sorted(set(doi_chung) & set(sua)) if _khac_san(k[0])
             and doi_chung[k]["entry_price"] and sua[k]["entry_price"]
             and str(doi_chung[k]["entry_date"])[:10] == str(sua[k]["entry_date"])[:10]]
    p6_thap = [k for k in chung
               if float(sua[k]["entry_price"]) < float(doi_chung[k]["entry_price"]) - 1e-6]
    chenh = [(float(sua[k]["entry_price"]) - float(doi_chung[k]["entry_price"]),
              dai_gia(float(doi_chung[k]["entry_price"]))) for k in chung]
    return {"p4": p4, "p5_khac": p5_khac, "p6_thap": p6_thap,
            "n_chung_HNX_UPCOM": len(chung), "chenh": chenh,
            "n_HNX_UPCOM": {"doi_chung": sum(_khac_san(m) for m, _ in doi_chung),
                            "sua": sum(_khac_san(m) for m, _ in sua)}}


def main(tham_so: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--doi-chung", required=True, type=Path)
    ap.add_argument("--sua", required=True, type=Path)
    ap.add_argument("--che-do", required=True, choices=("ma", "ngay"))
    a = ap.parse_args(tham_so)
    thieu = [p for p in (a.doi_chung, a.sua) if not p.exists()]
    if thieu:
        print(f"CHƯA KIỂM ĐƯỢC — thiếu: {[str(p) for p in thieu]}")
        return 2
    kq = kiem(g20.doc_so(a.doi_chung), g20.doc_so(a.sua), a.che_do)
    dat = True

    n_ok, n = kq["p4"]["sua"]
    n_ok0, n0 = kq["p4"]["doi_chung"]
    ok4 = n > 0 and n_ok == n and not (n0 > 0 and n_ok0 == n0)
    dat &= ok4
    print(f"P4 giá VÀO HNX/UPCoM chia hết 100 · ĐÃ SỬA {n_ok}/{n} · đối chứng {n_ok0}/{n0} "
          f"→ {'ĐẠT' if ok4 else 'HỎNG'}")

    if a.che_do == "ma":
        ok5 = not kq["p5_khac"]
        dat &= ok5
        print(f"P5 lệnh HOSE giống hệt giữa hai luồng · khác: {len(kq['p5_khac'])} "
              f"{kq['p5_khac'][:5] or ''} → {'ĐẠT' if ok5 else 'HỎNG'}")
    else:
        print("P5 chỉ áp cho chế độ theo mã — bỏ qua ở chế độ theo ngày (trần vốn nối các mã)")

    ok6 = not kq["p6_thap"]
    dat &= ok6
    print(f"P6 giá vào ĐÃ SỬA >= đối chứng · {kq['n_chung_HNX_UPCOM']} lệnh HNX/UPCoM chung "
          f"khoá cùng ngày vào · thấp hơn: {len(kq['p6_thap'])} {kq['p6_thap'][:5] or ''} "
          f"→ {'ĐẠT' if ok6 else 'HỎNG'}")

    print(f"lệnh HNX/UPCoM: đối chứng {kq['n_HNX_UPCOM']['doi_chung']} · "
          f"đã sửa {kq['n_HNX_UPCOM']['sua']}")
    if kq["chenh"]:
        tat = [d for d, _ in kq["chenh"]]
        print(f"chênh giá vào (đã sửa − đối chứng): TB {statistics.mean(tat):+.1f}đ · "
              f"trung vị {statistics.median(tat):+.0f}đ · đổi {sum(1 for d in tat if d)}/{len(tat)}")
        for dai in ("<10k", "10-50k", ">=50k"):
            v = [d for d, k in kq["chenh"] if k == dai]
            if v:
                print(f"  {dai:7s} n={len(v):3d}  TB {statistics.mean(v):+.1f}đ")
    return 0 if dat else 1


if __name__ == "__main__":
    raise SystemExit(main())
