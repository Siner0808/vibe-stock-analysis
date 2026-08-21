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
CHE_DO_HOC = ("tat", "co_san", "tich_luy")


def _dung_bo_nho(che_do: str, duong_bo_nho: str | None):
    """Dựng bộ nhớ post-mortem RIÊNG cho một lượt. Trả về engine.

    Ba chế độ, ba câu hỏi khác nhau:

    `tat`      — không bộ nhớ, engine RỖNG hẳn. Mặc định, và là mốc để so.
    `co_san`   — nạp bộ nhớ hiện có (44 mẫu từ lệnh thật), CHỈ ĐỌC: dùng để
                 chấm điểm nhưng không ghi thêm mẫu nào. Trả lời "bộ nhớ
                 ĐANG CÓ giúp gì không".
    `tich_luy` — bắt đầu RỖNG, lớn dần trong chính lượt này. Trả lời "việc
                 TÍCH LUỸ giúp gì không" — câu trước đây không đo được.

    Hai chế độ sau phải TÁCH BẠCH. Bản đầu của hàm này để `co_san` vừa nạp
    44 mẫu vừa tích luỹ tiếp — chạy thử thấy nó học thêm 52 mẫu trong một
    lượt. Khi đó nó đo một hiệu ứng GỘP và không quy được cho bên nào.

    Mỗi lượt một engine mới. Không làm thế thì bảy lượt dò ngưỡng dùng chung
    `_ENGINE_CACHE` và lượt sau khởi động với bộ nhớ do lượt trước bồi vào —
    bảy lượt không độc lập, mà chọn lượt tốt nhất trong đó là bất biến 7.

    `co_san` chạy trên BẢN SAO chứ không trỏ thẳng vào `sl_pattern_memory.json`.
    Hôm nay không có đường nào ghi ngược vào file thật, nhưng dự án này đã một
    lần ghi đè sổ thật bằng kết quả backtest — bản sao là một dòng lệnh, còn
    hậu quả của lần sau thì không.
    """
    import os
    import shutil
    import tempfile

    from paper_runner import _xoa_cache_phan_tich
    from post_mortem_learning import MEMORY_FILE, dat_lai_engine

    if che_do not in CHE_DO_HOC:
        raise ValueError(f"che_do_hoc phải là một trong {CHE_DO_HOC}, "
                         f"nhận {che_do!r}")

    if che_do == "tat":
        # Trỏ vào một đường dẫn KHÔNG tồn tại để engine rỗng thật, thay vì
        # nạp 44 mẫu rồi để đó. Engine tắt thì các mẫu đó vô hại, nhưng
        # "vô hại vì có một công tắc đang tắt" yếu hơn "không có gì để dùng".
        fd, trong = tempfile.mkstemp(suffix=".json", prefix="wf_bo_nho_tat_")
        os.close(fd)
        os.remove(trong)
        may = dat_lai_engine(trong, enabled=False)
    elif che_do == "co_san":
        # Bản sao + chi_doc là hai lớp cho cùng một việc. `chi_doc` chặn ghi
        # ở engine; bản sao chặn ở tầng file, phòng khi có đường ghi khác
        # xuất hiện sau này. Dự án này đã một lần ghi đè sổ thật bằng kết
        # quả backtest — hai lớp cho một file 44 dòng là rẻ.
        fd, ban_sao = tempfile.mkstemp(suffix=".json", prefix="wf_bo_nho_")
        os.close(fd)
        if os.path.exists(MEMORY_FILE):
            shutil.copyfile(MEMORY_FILE, ban_sao)
        else:
            os.remove(ban_sao)
        may = dat_lai_engine(ban_sao, enabled=True, chi_doc=True)
    else:
        if not duong_bo_nho:
            raise ValueError("che_do_hoc='tich_luy' cần duong_bo_nho")
        if os.path.exists(duong_bo_nho):
            os.remove(duong_bo_nho)          # lượt này bắt đầu từ số không
        may = dat_lai_engine(duong_bo_nho, enabled=True)

    # Xoá cache CHỈ khi bộ nhớ bật. Bật thì mỗi lượt một engine riêng nên
    # các mục cũ không bao giờ dùng lại được — giữ chúng chỉ tốn RAM.
    #
    # Tắt thì NGƯỢC LẠI: điểm là hàm thuần của lát cắt, bảy lượt dò ngưỡng
    # chấm đúng những lát cắt giống nhau, và dùng chung cache là đúng chứ
    # không phải may. Xoá vô điều kiện làm mỗi lượt chấm lại từ đầu —
    # `che_do_hoc="tat"` đi từ 8,1 lên 27,7 phút.
    #
    # Tính đúng đắn không dựa vào việc xoá: dấu vân đã phân biệt các engine.
    # Xoá chỉ là dọn RAM.
    if may.enabled:
        _xoa_cache_phan_tich()
    return may


def _mo_phong(du_lieu: dict, nguong: float, db: str,
              stride: int = 2, min_history: int = 60,
              che_do_hoc: str = "tat",
              duong_bo_nho: str | None = None) -> dict:
    """Chạy một lượt trên `du_lieu` với `nguong`, trả về chỉ số đo được.

    `du_lieu` là {mã: DataFrame} ĐÃ CẮT sẵn về đúng vùng cần chạy — hàm này
    không tự cắt, để không có đường nào lẫn IS sang OOS.
    """
    import os

    from paper_metrics import compute, vs_benchmark
    from paper_runner import _cho_phep_mo_lenh, build_benchmark, run_session
    from paper_trading import PaperTradingJournal

    may = _dung_bo_nho(che_do_hoc, duong_bo_nho)
    mau_dau = len(may.sl_patterns)

    if os.path.exists(db):
        os.remove(db)
    so = PaperTradingJournal(db)
    # try/finally: bản cũ gọi `so.db.close()` sau vòng lặp, nên một ngoại lệ
    # giữa chừng để kết nối SQLite mở vĩnh viễn. Trên Windows điều đó khoá
    # luôn file — dọn dẹp sau đó nhận PermissionError WinError 32, và lỗi
    # thứ hai đó che mất lỗi thứ nhất.
    try:
        with _cho_phep_mo_lenh():
            for sym, df in sorted(du_lieu.items()):
                n = len(df)
                for t in range(min_history, n, stride):
                    hang = df.iloc[t]
                    run_session(so, sym, df.iloc[: t + 1],
                                {"open": float(hang["open"]),
                                 "high": float(hang["high"]),
                                 "low": float(hang["low"]),
                                 "close": float(hang["close"])},
                                str(hang["time"]), buy_threshold=nguong)
        lenh = so.all_trades()
    finally:
        so.db.close()

    # Ghi lại bộ nhớ của lượt này để soi được nó đã học gì. Chỉ chế độ
    # tich_luy mới ghi: `co_san` chạy trên bản sao tạm, ghi ra là ghi vào
    # rác; `tat` thì không có gì để ghi.
    mau_cuoi = len(may.sl_patterns)
    if che_do_hoc == "tich_luy":
        may.save_memory(force=True)

    dong = [x for x in lenh if x.status == "CLOSED"]
    m = compute(dong)

    # Alpha khớp từng lệnh — bất biến 6, và là phép đo QUYẾT ĐỊNH. Trước
    # 21/08/2026 hàm này không tính nó: nó in kỳ vọng và lợi nhuận cộng
    # dồn, tức là "lãi hơn 0 không", trong khi câu cần trả lời là "giỏi hơn
    # cầm đều cả rổ không". Trong một thị trường đi lên, hai câu đó cho hai
    # câu trả lời rất khác nhau.
    chuan = build_benchmark(dong, du_lieu)
    a = vs_benchmark(dong, chuan) if chuan else {"n": 0, "alpha": None,
                                                 "verdict": "chưa có đối chiếu"}

    # `compute()` trả None khi KHÔNG có lệnh đóng nào, và bản cũ đọc thẳng
    # `m.n_trades` nên nổ AttributeError. Một ngưỡng cao không mở lệnh nào
    # là kết quả HỢP LỆ và là thông tin quan trọng — "ngưỡng này không giao
    # dịch" khác hẳn "lượt chạy hỏng". Nổ ở đây làm sập cả walk-forward vì
    # một dòng đáng lẽ chỉ ghi 0 lệnh.
    if m is None:
        return {
            "nguong": nguong, "che_do_hoc": che_do_hoc,
            "mau_dau": mau_dau, "mau_hoc_them": mau_cuoi - mau_dau,
            "so_lenh": 0, "ky_vong": None, "net_pct": None,
            "win_rate": None, "von_tb": None, "von_dinh": None,
            "alpha": None, "alpha_ktc": None, "alpha_so_lenh": 0,
            "alpha_bo_qua": 0,
            "alpha_ket_luan": "không lệnh nào đóng — chưa có gì để đo",
            "_lenh": [],
        }

    return {
        "nguong": nguong,
        "alpha": a.get("alpha"),
        "alpha_ktc": a.get("ci"),
        "alpha_so_lenh": a.get("n"),
        "alpha_bo_qua": a.get("bo_qua"),
        "alpha_ket_luan": a.get("verdict"),
        "che_do_hoc": che_do_hoc,
        "mau_dau": mau_dau,
        "mau_hoc_them": mau_cuoi - mau_dau,
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
         che_do_hoc: str = "tat") -> dict:
    """Walk-forward đầy đủ. Trả về {is: [...], nguong_chon, oos: {...}}.

    `che_do_hoc` — xem `_dung_bo_nho()`. Mặc định `tat`, và đó là chủ đích:
    bộ nhớ hiện có dựng từ 44 lệnh có tín hiệu 2024-01 → 2026-06, tức nằm
    trong vùng IS, trong khi vùng OOS nằm TRƯỚC đó. Hàng rào `as_of` chặn
    việc mẫu tương lai áp vào quá khứ, nhưng tắt hẳn thì phép đo không phải
    dựa vào hàng rào nào cả.

    Mỗi lượt có bộ nhớ RIÊNG, dựng lại từ đầu. Trước 21/08/2026 thì không:
    cả bảy lượt dò ngưỡng và lượt OOS dùng chung một `_ENGINE_CACHE`, và
    `record_sl_trade()` nối thêm vào danh sách dùng chung đó — đo được là
    ba lệnh cắt lỗ đủ đưa bộ nhớ từ 44 lên 47 mẫu dù không mẫu nào ghi ra
    đĩa. Nghĩa là lượt ngưỡng 62 khởi động với bộ nhớ to hơn lượt ngưỡng 45.
    Mọi con số `post_mortem=True` đo trước ngày đó đều dính lỗi này.
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

    # Chế độ học được đặt qua `enabled=` của từng engine chứ không qua biến
    # môi trường, nhưng POST_MORTEM_ENABLED vẫn phải khớp: `paper_runner`
    # đọc nó ở vài chỗ khác, và hai nguồn sự thật lệch nhau thì sớm muộn
    # cũng có chỗ đọc nhầm nguồn.
    cu = os.environ.get("POST_MORTEM_ENABLED")
    os.environ["POST_MORTEM_ENABLED"] = "0" if che_do_hoc == "tat" else "1"
    try:
        ket_qua_is = []
        for ng in dai_nguong:
            r = _mo_phong(vung_is, ng, f"{tien_to_db}is_{ng:g}.db",
                          stride, min_history, che_do_hoc,
                          f"{tien_to_db}bo_nho_is_{ng:g}.json")
            r.pop("_lenh", None)
            ket_qua_is.append(r)

        chon = chon_nguong(ket_qua_is)
        oos = None
        if chon is not None and vung_oos:
            oos = _mo_phong(vung_oos, chon, f"{tien_to_db}oos.db",
                            stride, min_history, che_do_hoc,
                            f"{tien_to_db}bo_nho_oos.json")
    finally:
        os.environ.pop("POST_MORTEM_ENABLED", None)
        if cu is not None:
            os.environ["POST_MORTEM_ENABLED"] = cu
        # Trả engine về mặc định: hàm này đã thay `_ENGINE_CACHE` toàn tiến
        # trình, để nguyên là mọi thứ chạy sau đó thừa hưởng bộ nhớ backtest.
        from paper_runner import _xoa_cache_phan_tich
        from post_mortem_learning import MEMORY_FILE, dat_lai_engine
        dat_lai_engine(MEMORY_FILE)
        _xoa_cache_phan_tich()

    return {"is": ket_qua_is, "nguong_chon": chon, "oos": oos,
            "che_do_hoc": che_do_hoc,
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
    ap.add_argument("--che-do-hoc", choices=CHE_DO_HOC, default="tat",
                    dest="che_do_hoc",
                    help="tat: khong co bo nho (mac dinh) | "
                         "co_san: nap bo nho hien co, chi doc | "
                         "tich_luy: bat dau rong, lon dan trong luot nay")
    a = ap.parse_args()

    ma = a.symbols.split(",") if a.symbols else None
    kq = chay(symbols=ma, stride=a.stride, min_history=a.min_history,
              che_do_hoc=a.che_do_hoc)

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
    if o.get("alpha") is not None:
        print(f"  alpha khớp từng lệnh: {o['alpha']:+.2f}%/lệnh"
              f"   KTC 95% [{o['alpha_ktc'][0]:+.2f} ; {o['alpha_ktc'][1]:+.2f}]")
        print(f"    → {o['alpha_ket_luan']}")
    else:
        print(f"  alpha khớp từng lệnh: chưa đo được"
              f"   ({o.get('alpha_ket_luan')})")
    if o.get("alpha_bo_qua"):
        print(f"    ⚠️ bỏ {o['alpha_bo_qua']} lệnh vì không dựng được cặp "
              f"ngày trong rổ chuẩn")
    print(f"  bộ nhớ học: đầu {o['mau_dau']} mẫu, học thêm "
          f"{o['mau_hoc_them']}   (chế độ {o['che_do_hoc']})")
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
