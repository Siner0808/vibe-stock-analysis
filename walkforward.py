"""Walk-forward THẬT — chọn tham số trên một khoảng, đo trên khoảng KHÁC.

VÌ SAO CÓ FILE NÀY
──────────────────
`walkforward_vn100.py` không còn làm walk-forward (đo 19/08/2026): nó chạy
`run_simulation` MỘT lần trên toàn khoảng rồi lọc `exit_date` để gọi là OOS,
ngưỡng 50,0 nhập sẵn thay vì chọn trên in-sample, và mốc chia là
`datetime.now() - 182 ngày`.

Bản ở `git show 025507c` có cấu trúc đúng — chọn trên IS, đo trên OOS —
nhưng vẫn lấy **6 tháng gần nhất** làm OOS. Đó là trái bất biến 8: hàng
trăm vòng loop đã chạy trên toàn bộ cache kéo tới hôm nay, nên giai đoạn
gần nhất là giai đoạn **đã bị nhìn nhiều nhất**.

CÁCH CHIA Ở ĐÂY
───────────────
Không chia theo ngày lịch. Chia theo **dữ liệu nào đã tồn tại khi các vòng
tối ưu chạy**.

`docs/moc_du_lieu_sach.json` ghi, với mỗi mã, ngày bắt đầu của cache TRƯỚC
khi `extend_history` chạy ngày 20/08/2026. Mọi phiên trước mốc đó là dữ
liệu **không tồn tại** lúc ấy — nên không vòng tối ưu nào *có thể* đã nhìn
thấy nó.

    OOS (đo)          = phiên <  mốc     ← chưa thể đã nhìn
    IS  (chọn ngưỡng) = phiên >= mốc     ← vùng đã bị nhìn

Đây là vùng kiểm định duy nhất trong dự án mà tính "chưa nhìn" **chứng minh
được**, thay vì giả định. Đo được: 25.219/80.939 phiên = 31,2%, trên 33/71
mã — 34 mã còn lại đã có dữ liệu từ 2021-10 nên không đóng góp gì.

LUẬT CHỌN NGƯỠNG — NÊU TRƯỚC, KHÔNG CHỌN SAU
Chỉ ngưỡng đạt tối thiểu `TOI_THIEU_LENH` lệnh trên IS mới đủ tư cách;
trong số đó lấy kỳ vọng cao nhất. Không có luật nêu trước thì "chọn trên
in-sample" chỉ là cực đại của N lần thử dưới một cái tên khác (bất biến 7).

CÁI NÀY KHÔNG LÀM
Nó không hứa tìm ra lợi thế. Nó chỉ làm cho câu trả lời — dù là "không có
lợi thế" — trở thành một câu trả lời đo được.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent
FILE_MOC = GOC / "docs" / "moc_du_lieu_sach.json"

#: Số lệnh tối thiểu trên IS để một ngưỡng đủ tư cách được chọn.
#: Với σ ≈ 7%/lệnh, dưới ngưỡng này thì kỳ vọng chỉ là nhiễu.
TOI_THIEU_LENH = 30

#: Dải ngưỡng quét trên IS.
DAI_NGUONG = [45.0, 48.0, 50.0, 52.0, 55.0, 58.0, 62.0]


def nap_moc_sach(duong_dan: Path | str = FILE_MOC) -> dict[str, str]:
    """{mã: ngày} — mọi phiên TRƯỚC ngày này là dữ liệu chưa thể đã nhìn."""
    d = json.loads(Path(duong_dan).read_text(encoding="utf-8"))
    return dict(d.get("moc_theo_ma", {}))


def chia_vung(df: pd.DataFrame, moc: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cắt một mã thành (OOS, IS). Hai vùng KHÔNG giao nhau, hợp lại đủ.

    So trên 10 ký tự đầu vì `backtest/cache/` từng có hai định dạng cột
    `time` trong cùng một thư mục.
    """
    if df is None or "time" not in getattr(df, "columns", []):
        rong = pd.DataFrame(columns=getattr(df, "columns", []))
        return rong, df
    ngay = df["time"].astype(str).str.slice(0, 10)
    truoc = ngay < str(moc)[:10]
    return df[truoc], df[~truoc]


def chon_nguong(ket_qua_is: list[dict],
                toi_thieu_lenh: int = TOI_THIEU_LENH) -> float | None:
    """Chọn ngưỡng trên kết quả IS theo luật đã nêu trước.

    Trả None khi không ngưỡng nào đủ mẫu — im lặng chọn đại một dòng 4 lệnh
    lãi 9,9% là đúng thứ bất biến 7 cấm.
    """
    du_tu_cach = [r for r in ket_qua_is
                  if int(r.get("so_lenh", 0)) >= toi_thieu_lenh]
    if not du_tu_cach:
        return None
    tot = max(du_tu_cach, key=lambda r: float(r.get("ky_vong", float("-inf"))))
    return float(tot["nguong"])


# ── Chạy mô phỏng ────────────────────────────────────────────────────
def _mo_phong(du_lieu: dict, nguong: float, db: str,
              stride: int = 2, min_history: int = 60) -> dict:
    """Chạy một lượt trên `du_lieu` với `nguong`, trả về chỉ số đo được.

    `du_lieu` là {mã: DataFrame} ĐÃ CẮT sẵn về đúng vùng cần chạy — hàm này
    không tự cắt, để không có đường nào lẫn IS sang OOS.
    """
    import os

    from paper_metrics import compute
    from paper_runner import _cho_phep_mo_lenh, run_session
    from paper_trading import PaperTradingJournal

    if os.path.exists(db):
        os.remove(db)
    so = PaperTradingJournal(db)
    with _cho_phep_mo_lenh():
        for sym, df in sorted(du_lieu.items()):
            n = len(df)
            for t in range(min_history, n, stride):
                hang = df.iloc[t]
                run_session(so, sym, df.iloc[: t + 1],
                            {"open": float(hang["open"]), "high": float(hang["high"]),
                             "low": float(hang["low"]), "close": float(hang["close"])},
                            str(hang["time"]), buy_threshold=nguong)
    lenh = so.all_trades()
    so.db.close()
    dong = [x for x in lenh if x.status == "CLOSED"]
    m = compute(dong)
    return {
        "nguong": nguong,
        "so_lenh": m.n_trades,
        "ky_vong": m.expectancy,
        "net_pct": m.total_net_pct,
        "win_rate": m.win_rate * 100,
        "von_tb": m.avg_capital_deployed_pct,
        "von_dinh": m.peak_capital_deployed_pct,
        "_lenh": dong,
    }


def chay(symbols: list[str] | None = None, dai_nguong: list[float] | None = None,
         stride: int = 2, min_history: int = 60, tien_to_db: str = "wf_",
         post_mortem: bool = False) -> dict:
    """Walk-forward đầy đủ. Trả về {is: [...], nguong_chon, oos: {...}}.

    Post-mortem bị TẮT trong suốt lượt chạy. Bộ nhớ hiện tại dựng từ 44 lệnh
    có tín hiệu 2024-01 → 2026-06, tức nằm trong vùng IS; vùng OOS thì nằm
    TRƯỚC đó. Hàng rào `as_of` đã chặn việc mẫu tương lai áp vào quá khứ,
    nhưng tắt hẳn thì phép đo không phải dựa vào một hàng rào nào cả.
    """
    import os

    from backtest.data import load_all
    from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS

    dai_nguong = dai_nguong or DAI_NGUONG
    symbols = symbols or CUSTOM_WATCHLIST_SYMBOLS
    moc = nap_moc_sach()
    tat_ca = load_all(symbols)

    vung_oos, vung_is = {}, {}
    for sym, df in tat_ca.items():
        if sym not in moc:
            continue
        o, i = chia_vung(df, moc[sym])
        if len(o) > min_history:
            vung_oos[sym] = o.reset_index(drop=True)
        if len(i) > min_history:
            vung_is[sym] = i.reset_index(drop=True)

    # `post_mortem=False` la mac dinh CO CHU DICH. Bat len chi de DO xem co
    # che hoc co giup gi khong -- va phai do bang cach chay ca hai chieu roi
    # so, khong phai bang cach nhin mot con so.
    #
    # Luu y: cac so tam (`wf_*.db`) khong phai so that, nen save_memory()
    # khong chay -- bo nho GIU NGUYEN 44 mau goc suot luot chay. Nghia la
    # phep do nay tra loi "bo nho hien co giup gi khong", KHONG phai "viec
    # tich luy them giup gi khong". Cau hoi thu hai can bo nho rieng cho moi
    # luot backtest, va do la viec khac.
    cu = os.environ.get("POST_MORTEM_ENABLED")
    os.environ["POST_MORTEM_ENABLED"] = "1" if post_mortem else "0"
    try:
        ket_qua_is = []
        for ng in dai_nguong:
            r = _mo_phong(vung_is, ng, f"{tien_to_db}is_{ng:g}.db",
                          stride, min_history)
            r.pop("_lenh", None)
            ket_qua_is.append(r)

        chon = chon_nguong(ket_qua_is)
        oos = None
        if chon is not None and vung_oos:
            oos = _mo_phong(vung_oos, chon, f"{tien_to_db}oos.db",
                            stride, min_history)
    finally:
        os.environ.pop("POST_MORTEM_ENABLED", None)
        if cu is not None:
            os.environ["POST_MORTEM_ENABLED"] = cu

    return {"is": ket_qua_is, "nguong_chon": chon, "oos": oos,
            "so_ma_is": len(vung_is), "so_ma_oos": len(vung_oos)}


def main() -> int:
    import argparse
    import sys

    from dai_ket_qua import CANH_BAO, in_toan_dai

    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", help="danh sách mã, cách nhau bằng dấu phẩy")
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--min-history", type=int, default=60, dest="min_history")
    a = ap.parse_args()

    ma = a.symbols.split(",") if a.symbols else None
    kq = chay(symbols=ma, stride=a.stride, min_history=a.min_history)

    print("=" * 72)
    print("WALK-FORWARD — chọn trên IS, đo trên OOS, hai vùng KHÔNG giao nhau")
    print("=" * 72)
    print(f"mã có vùng IS : {kq['so_ma_is']}")
    print(f"mã có vùng OOS: {kq['so_ma_oos']}"
          f"   (vùng chưa thể đã nhìn — xem docs/moc_du_lieu_sach.json)")
    print()
    print("── DẢI KẾT QUẢ TRÊN IN-SAMPLE ─────────────────────────────────")
    print(in_toan_dai(kq["is"], khoa_nhan="nguong", khoa_so_lenh="so_lenh",
                     khoa_pnl="net_pct", cot_them=["ky_vong", "win_rate",
                                                   "von_dinh"]))

    if kq["nguong_chon"] is None:
        print(f"⛔ KHÔNG ngưỡng nào đạt tối thiểu {TOI_THIEU_LENH} lệnh trên IS.")
        print("   Không chọn bừa một dòng ít mẫu — đó là bất biến 7.")
        print("   Chưa đo được OOS.")
        return 1

    print(f"→ Ngưỡng chọn trên IS: {kq['nguong_chon']:g}"
          f"  (luật nêu trước: ≥{TOI_THIEU_LENH} lệnh, rồi kỳ vọng cao nhất)")
    print()
    o = kq["oos"]
    if not o:
        print("⛔ Không có vùng OOS đủ lớn để đo.")
        return 1

    print("── ĐO TRÊN OUT-OF-SAMPLE ──────────────────────────────────────")
    print(f"  số lệnh          : {o['so_lenh']}")
    print(f"  kỳ vọng mỗi lệnh : {o['ky_vong']:+.2f}%")
    print(f"  win rate         : {o['win_rate']:.1f}%")
    print(f"  lợi nhuận cộng dồn: {o['net_pct']:+.2f}%")
    print(f"  vốn triển khai   : {o['von_tb']:.0f}% trung bình"
          f" · {o['von_dinh']:.0f}% đỉnh")
    if o["von_dinh"] > 100:
        print("  ⚠️  Vốn đỉnh vượt 100% — con số cộng dồn ở trên là lợi nhuận")
        print("     của một tài khoản VAY ĐƯỢC (bất biến 7b). Chia tỷ trọng")
        print("     cho đúng bội số rồi đo lại trước khi kết luận.")
    print()
    print("Con số dùng được là con số OOS ở trên, KHÔNG phải dòng nào trong")
    print("dải IS. Dải IS chỉ để chọn tham số.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
