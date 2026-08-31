"""
paper_metrics.py
──────────────────────────────────────────────────────────────────────
Chấm điểm sổ lệnh giấy.

Câu hỏi phải trả lời, theo thứ tự khắt khe dần:
  1. Kỳ vọng mỗi lệnh có dương không? (sau phí)
  2. Con số đó có vượt được ngẫu nhiên không?
  3. Có hơn việc chỉ cầm đều cả rổ không?

Câu 3 là câu quyết định. Lãi 8% khi VN-INDEX tăng 12% là THUA — và đây
đúng là cái bẫy đã gặp ở backtest: thị trường tăng làm mọi thứ trông đẹp.
"""
from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime

from paper_trading import (BROKER_FEE_PCT, EXCHANGE_FEE_PCT, SELL_TAX_PCT,
                           ExitReason, Trade)

#: PHẢI khớp từng số hạng với `Trade.net_return_pct()`. Hai công thức song
#: song là chỗ trôi ra khỏi nhau âm thầm — cùng cơ chế đã làm `run_daily`
#: cầm `50.0` trong khi `paper_trading` cầm `62`.
ROUND_TRIP_COST_PCT = ((BROKER_FEE_PCT + EXCHANGE_FEE_PCT) * 2
                       + SELL_TAX_PCT) * 100


@dataclass
class Performance:
    n_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    expectancy: float          # kỳ vọng mỗi lệnh, sau phí (%)
    profit_factor: float
    total_net_pct: float       # tổng lợi nhuận cộng dồn theo tỷ trọng
    max_drawdown_pct: float
    by_exit_reason: dict[str, int]
    # Vốn đã cam kết cùng lúc, tính theo % tài khoản. Vượt 100% nghĩa là
    # `total_net_pct` ở trên là lợi nhuận của một tài khoản dùng đòn bẩy.
    avg_capital_deployed_pct: float = 0.0
    peak_capital_deployed_pct: float = 0.0

    @property
    def is_leveraged(self) -> bool:
        return self.avg_capital_deployed_pct > 100.0

    def summary(self) -> str:
        s = (f"{self.n_trades} lệnh · thắng {self.win_rate:.0%} · "
             f"kỳ vọng {self.expectancy:+.2f}%/lệnh · "
             f"PF {self.profit_factor:.2f} · DD tối đa {self.max_drawdown_pct:.1f}%")
        if self.is_leveraged:
            s += (f" · ⚠️ ĐÒN BẨY {self.avg_capital_deployed_pct / 100:.1f}x "
                  f"({self.avg_capital_deployed_pct:.0f}% vốn)")
        return s


def _returns(trades: list[Trade]) -> list[float]:
    return [t.net_return_pct() for t in trades
            if t.status == "CLOSED" and t.net_return_pct() is not None]


def _capital_deployment(closed: list[Trade]) -> tuple[float, float]:
    """Vốn cam kết cùng lúc: trung bình theo thời gian, và đỉnh điểm.

    Đường vốn ở compute() nhân dồn từng lệnh vào TOÀN BỘ vốn hiện có, lần
    lượt theo ngày đóng. Phép nhân đó chỉ đúng khi mỗi thời điểm chỉ có một
    lệnh mở. Khi nhiều lệnh chồng lên nhau, tổng vốn cam kết vượt 100% và
    con số lợi nhuận cộng dồn trở thành lợi nhuận của một tài khoản dùng
    đòn bẩy — không tài khoản thật nào chạy được như vậy.

    Đây chính là chỗ báo cáo 20 vòng (12/08/2026) trượt: +636,11% ở ngưỡng
    50,0 tái lập được, nhưng bộ lệnh đó giữ trung bình 224% vốn (đỉnh
    1.160%) — đòn bẩy 2,2 lần.

    Trả về (trung_bình, đỉnh) tính theo % tài khoản.
    """
    deltas: dict[date, float] = defaultdict(float)
    for t in closed:
        if not t.entry_date or not t.exit_date:
            continue
        try:
            d_in = date.fromisoformat(str(t.entry_date)[:10])
            d_out = date.fromisoformat(str(t.exit_date)[:10])
        except ValueError:
            continue
        if d_out < d_in:
            continue
        size = float(t.size_pct or 0.0)
        deltas[d_in] += size
        deltas[d_out] -= size

    if not deltas:
        return 0.0, 0.0

    moc = sorted(deltas)
    level = peak = weighted = 0.0
    total_days = 0
    for i, d in enumerate(moc):
        level += deltas[d]
        peak = max(peak, level)
        if i + 1 < len(moc):
            span = (moc[i + 1] - d).days
            weighted += level * span
            total_days += span

    avg = weighted / total_days if total_days else peak
    return avg, peak


def compute(trades: list[Trade]) -> Performance | None:
    rets = _returns(trades)
    if not rets:
        return None

    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))

    # Đường vốn: mỗi lệnh đóng góp theo tỷ trọng vốn của nó.
    #
    # PHẢI sắp theo NGÀY ĐÓNG LỆNH. Danh sách lấy từ sổ mặc định xếp theo id,
    # tức thứ tự chèn: hết toàn bộ lệnh của mã A rồi mới tới mã B. Dựng đường
    # vốn theo thứ tự đó cho ra một chuỗi lãi/lỗ chưa từng tồn tại, và
    # drawdown tính từ nó không phải mức sụt giảm tài khoản thật sự chịu.
    # Đo trên rổ 50 mã: 23,0% theo id so với 30,7% theo thời gian.
    closed = [t for t in trades if t.status == "CLOSED"
              and t.net_return_pct() is not None]
    
    # Sắp xếp lệnh theo thời điểm ĐÓNG LỆNH để tính chính xác MaxDD theo thời gian
    closed.sort(key=lambda x: x.exit_date or "")
    
    equity, peak, max_dd = 100.0, 100.0, 0.0
    for t in closed:
        equity *= 1 + (t.net_return_pct() / 100) * (t.size_pct / 100)
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak * 100)

    reasons: dict[str, int] = {}
    for t in closed:
        reasons[t.exit_reason or "?"] = reasons.get(t.exit_reason or "?", 0) + 1

    avg_deployed, peak_deployed = _capital_deployment(closed)

    return Performance(
        n_trades=len(rets),
        win_rate=len(wins) / len(rets),
        avg_win=statistics.mean(wins) if wins else 0.0,
        avg_loss=statistics.mean(losses) if losses else 0.0,
        expectancy=statistics.mean(rets),
        profit_factor=(gross_win / gross_loss) if gross_loss else float("inf"),
        total_net_pct=equity - 100.0,
        max_drawdown_pct=max_dd,
        by_exit_reason=reasons,
        avg_capital_deployed_pct=avg_deployed,
        peak_capital_deployed_pct=peak_deployed,
    )


def expectancy_significant(trades: list[Trade], iters: int = 5000,
                           seed: int = 0) -> dict:
    """Kỳ vọng dương có phải may rủi không? Bootstrap khoảng tin cậy.

    Khoảng chứa 0 => chưa đủ bằng chứng. Với 20-30 lệnh thì gần như chắc
    chắn sẽ chứa 0 — đó là lý do cần vài trăm lệnh trước khi kết luận.
    """
    rets = _returns(trades)
    if len(rets) < 10:
        return {"expectancy": None, "ci": (None, None), "significant": False,
                "verdict": f"mới {len(rets)} lệnh, chưa đủ để kết luận"}
    rng = random.Random(seed)
    means = []
    for _ in range(iters):
        sample = [rets[rng.randrange(len(rets))] for _ in range(len(rets))]
        means.append(statistics.mean(sample))
    means.sort()
    lo, hi = means[int(0.025 * iters)], means[int(0.975 * iters)]
    sig = lo > 0
    return {
        "expectancy": statistics.mean(rets),
        "ci": (lo, hi),
        "significant": sig,
        "verdict": ("kỳ vọng dương có ý nghĩa thống kê" if sig else
                    "CHƯA đủ bằng chứng kỳ vọng dương (khoảng tin cậy chứa 0)"),
    }


def _ngay(gia_tri) -> str:
    """Cắt về YYYY-MM-DD. `backtest/cache/` có hai định dạng cột `time`
    trong cùng một thư mục; sổ lệnh thì sạch. Chuẩn hoá ở ĐIỂM DÙNG rẻ hơn
    và an toàn hơn sửa 125 file dữ liệu gốc."""
    return str(gia_tri or "")[:10]


def ro_chuan_tu_chuoi_gia(trades: list[Trade],
                          gia_theo_ngay: dict) -> dict:
    """Dựng {(ngày vào, ngày ra): % thay đổi của chuẩn} cho từng lệnh đã đóng.

    Chuẩn hoá ngày ở CẢ HAI phía — chuỗi giá và sổ lệnh — nên rổ chạy được
    với cache dạng nào cũng được.

    Thiếu một trong hai đầu ngày thì KHÔNG dựng khoá. Đoán bằng ngày gần
    nhất sẽ làm phép đo trông đầy đủ hơn thực tế; để trống thì
    `vs_benchmark` đếm nó vào `bo_qua` và báo cáo nói ra con số đó.
    """
    gia = {_ngay(k): v for k, v in gia_theo_ngay.items()}
    ro: dict = {}
    for t in trades:
        if t.status != "CLOSED":
            continue
        vao, ra = _ngay(t.entry_date), _ngay(t.exit_date)
        p_vao, p_ra = gia.get(vao), gia.get(ra)
        if not vao or not ra or not p_vao or not p_ra:
            continue
        ro[(vao, ra)] = (p_ra - p_vao) / p_vao * 100.0
    return ro


def vs_benchmark(trades: list[Trade],
                 benchmark_return_by_period: dict[tuple[str, str], float],
                 z: float = 1.959964) -> dict:
    """So từng lệnh với việc cầm CHUẨN trong CÙNG khoảng thời gian.

    benchmark_return_by_period: {(ngày_vào, ngày_ra): % thay đổi của chuẩn}

    Đây là phép đo quyết định. Không có nó, một thị trường tăng sẽ khiến
    mọi hệ thống trông như thiên tài.
    """
    diffs = []
    bo_qua = 0
    for t in trades:
        if t.status != "CLOSED" or t.net_return_pct() is None:
            continue
        key = (t.entry_date or "", t.exit_date or "")
        bench = benchmark_return_by_period.get(key)
        if bench is None:
            # Đếm, không nuốt. Một lệnh đã đóng mà không tìm được cặp ngày
            # trong rổ chuẩn là MẪU BỊ BỎ, không phải mẫu không tồn tại.
            # `backtest/cache/` có hai định dạng cột `time` (40/125 file
            # mang hậu tố ' 07:00:00', 85/125 chỉ có ngày) trong khi
            # 113/113 lệnh trong sổ đều sạch, nên rổ dựng từ nhóm file kia
            # không khớp một lệnh nào. Bản cũ `continue` im lặng và trả về
            # "mới 0 lệnh có đối chiếu, chưa đủ" — đọc như thiếu dữ liệu,
            # thật ra là lỗi định dạng.
            bo_qua += 1
            continue
        diffs.append(t.net_return_pct() - bench)

    if len(diffs) < 10:
        return {"n": len(diffs), "alpha": None, "bo_qua": bo_qua,
                "verdict": f"mới {len(diffs)} lệnh có đối chiếu, chưa đủ"
                           + (f" ({bo_qua} lệnh bị BỎ vì không tìm được cặp "
                              f"ngày trong rổ chuẩn)" if bo_qua else "")}

    # `z` cho phép người gọi chọn độ rộng khoảng. Mặc định 1,959964 giữ
    # nguyên KTC 95% và ra ĐÚNG hai chỉ số cũ (125 và 4874), nên mọi chỗ
    # gọi sẵn có không đổi một chữ số.
    #
    # `dieu_kien_dong_lai` cần z rộng hơn vì nó được đánh giá LIÊN TỤC —
    # mỗi lượt quét, 12 lượt một ngày. Nhìn nhiều lần ở cùng một mức thì
    # xác suất chạm biên do nhiễu cộng dồn lên.
    rng = random.Random(0)
    VONG = 5000
    means = []
    for _ in range(VONG):
        s = [diffs[rng.randrange(len(diffs))] for _ in range(len(diffs))]
        means.append(statistics.mean(s))
    means.sort()
    _duoi = int(statistics.NormalDist().cdf(-z) * VONG)
    lo, hi = means[_duoi], means[VONG - 1 - _duoi]
    return {
        "n": len(diffs),
        "bo_qua": bo_qua,
        "alpha": statistics.mean(diffs),
        "ci": (lo, hi),
        "significant": not (lo <= 0 <= hi),
        "verdict": ("VƯỢT chuẩn có ý nghĩa" if lo > 0 else
                    "THUA chuẩn có ý nghĩa" if hi < 0 else
                    "không khác chuẩn một cách có ý nghĩa"),
    }



# ── Sổ này được tích luỹ, hay được sinh ra trong một lượt? ───────────
#
# Đo ngày 23/08/2026 trên `paper_trades.db`: cả 113 lệnh có `created_at`
# nằm trong khoảng 258 giây ngày 07/08/2026, trong khi `signal_date` của
# chúng trải từ 2024-01-05 đến 2026-06-26 — hơn hai năm rưỡi. Sổ ấy chưa
# bao giờ tích luỹ một lệnh nào từ việc quét tiến về phía trước.
#
# Không có gì SAI khi sổ sinh ra như vậy; sai là đọc nó như bằng chứng
# tích luỹ. Bốn phép đo dưới đây — kỳ vọng, KTC, alpha, drawdown — đều
# mang nghĩa khác hẳn giữa hai trường hợp.

#: Hai lần ghi cách nhau quá ngưỡng này thì thuộc hai lô khác nhau.
#: 60 giây: một lượt quét thật ghi từng lệnh sau khi tải nến và chấm
#: điểm, không thể nhanh hơn thế trên cả một rổ.
KHE_TOI_DA_GIAY = 60.0

#: Dưới ngưỡng này thì không đủ để nói gì — một phiên thật có thể mở vài
#: lệnh liền nhau.
TOI_THIEU_LENH_LO = 10

#: Và điều kiện phân biệt thật sự: lô phải trải trên một khoảng
#: `signal_date` DÀI. Một phiên bận rộn mở 15 lệnh trong 30 giây, nhưng
#: cả 15 lệnh cùng một ngày tín hiệu. Chỉ mô phỏng mới ghi lệnh của
#: 2024 và lệnh của 2026 cách nhau vài giây.
TOI_THIEU_NGAY_TRAI = 90


def lo_ghi_hang_loat(trades: list[Trade]) -> list[dict]:
    """Các lô lệnh được ghi vào đĩa hàng loạt. Rỗng nghĩa là không thấy.

    Trả `[]` cả khi KHÔNG KẾT LUẬN ĐƯỢC (sổ cũ không có `created_at`) —
    người gọi phải hiểu rỗng là "không thấy", không phải "đã chứng minh
    là không có". `so_lenh_khong_ro` trong `tom_tat_lo_ghi()` nói ra
    phần chưa biết đó.
    """
    co = [t for t in trades if t.created_at is not None]
    if len(co) < TOI_THIEU_LENH_LO:
        return []
    co.sort(key=lambda t: float(t.created_at))

    lo: list[list[Trade]] = [[co[0]]]
    for t in co[1:]:
        if float(t.created_at) - float(lo[-1][-1].created_at) <= KHE_TOI_DA_GIAY:
            lo[-1].append(t)
        else:
            lo.append([t])

    ra = []
    for nhom in lo:
        if len(nhom) < TOI_THIEU_LENH_LO:
            continue
        ngay = sorted(str(t.signal_date)[:10] for t in nhom if t.signal_date)
        if not ngay:
            continue
        try:
            trai = (date.fromisoformat(ngay[-1])
                    - date.fromisoformat(ngay[0])).days
        except ValueError:
            continue
        if trai < TOI_THIEU_NGAY_TRAI:
            continue
        ra.append({
            "so_lenh": len(nhom),
            "ids": {t.id for t in nhom},
            "ghi_tu": float(nhom[0].created_at),
            "ghi_den": float(nhom[-1].created_at),
            "giay": float(nhom[-1].created_at) - float(nhom[0].created_at),
            "tin_hieu_tu": ngay[0],
            "tin_hieu_den": ngay[-1],
            "ngay_trai": trai,
        })
    return ra


def tom_tat_lo_ghi(trades: list[Trade]) -> dict:
    """{so_lo, so_lenh_trong_lo, so_lenh_khong_ro, lo: [...]}"""
    lo = lo_ghi_hang_loat(trades)
    return {
        "so_lo": len(lo),
        "so_lenh_trong_lo": sum(x["so_lenh"] for x in lo),
        "so_lenh_khong_ro": sum(1 for t in trades if t.created_at is None),
        "lo": lo,
    }


# ── Điều kiện ĐÓNG LẠI cổng C5 — nêu TRƯỚC, không chế sau ────────────
#
# Ngày 24/08/2026 cổng `CHO_PHEP_MO_LENH_MOI` được mở ở ngưỡng 62. Lý do
# mở KHÔNG phải vì đã tìm thấy lợi thế — mọi phép đo alpha đều chứa số 0.
# Lý do là: cấu hình chạy trực tiếp (sáu agent đầy đủ, có TradingView và
# tin tức) CHƯA BAO GIỜ được đo, và nó chỉ đo được tiến về phía trước.
#
# Điều kiện đóng lại phải viết ra TRƯỚC khi có dữ liệu. Viết sau là chọn
# ngưỡng theo kết quả — cùng một lỗi với bất biến 7, chỉ đổi hướng.

# ── BẢN 2, viết ngày 29/08/2026 — vì sao bản 1 bị thay ──────────────
#
# BẢN 1 (26/08/2026, commit `0f67047`), ghi lại nguyên văn để đối chiếu:
#
#     TOI_THIEU_LENH_DE_DONG = 60
#     đóng ⟺ ≥60 lệnh tiến-về-trước ĐÃ ĐÓNG **và** cận trên KTC 95% của
#     KỲ VỌNG < 0
#
# Bốn lý do thay, đo và ghi ở `docs/STATE.md` — "GỐC RỄ CỦA CỔNG C5":
#
#   1. Đo sai ĐẠI LƯỢNG. Kỳ vọng trả lời "hệ thống có lãi không"; câu cần
#      hỏi là "hệ thống có hơn cầm cả rổ không" — alpha khớp từng lệnh
#      (bất biến 6).
#   2. Hiệu chuẩn để bắt THẢM HOẠ (−2,5%/lệnh) trong khi mức bất lợi đo
#      được là −0,927% alpha. Lệch 8 lần độ lớn: kỳ vọng cần 11,4 năm để
#      đạt 80% lực phát hiện, alpha cần 13 tháng.
#   3. Chỉ định giá sai lầm loại I (đóng nhầm vì nhiễu). Loại II — để mở
#      trong khi đang lỗ — không được nhắc một lần, nên bản 1 KHÔNG BAO
#      GIỜ đóng một hệ thống chỉ đơn giản là không có lợi thế.
#   4. Đếm mù lệnh chưa đóng. Ngày 29/08/2026 sổ có 4 lệnh PENDING mà bản
#      1 báo "0/60" — vô hình với chính phép kiểm sinh ra để canh chúng.
#
# Điều khoản sửa đổi (`docs/STATE.md`) cho phép viết lại khi cả ba đúng:
# tiền đề bị bác bỏ bằng một phép ĐO MỚI (không phải vì kết quả ra xấu);
# chưa có điểm dữ liệu kết quả nào thuộc loại quy tắc đang chờ; và bản
# cũ, bản mới, lý do đổi đều được ghi. Ngày 29/08/2026 cả ba thoả —
# 4 lệnh tiến-về-trước còn PENDING, chưa lệnh nào đóng.

#: Độ lệch chuẩn của alpha MỖI LỆNH. Nêu TRƯỚC, suy từ phép đo ngoài mẫu
#: n=385 (docs/STATE.md): alpha −0,927%, KTC 95% [−1,689 ; −0,076]
#:   nửa độ rộng 0,8065  →  SE 0,4115  →  σ = 0,4115·√385 = 8,075%
SIGMA_ALPHA = 8.075

#: Mức bất lợi ĐO ĐƯỢC ngoài mẫu khi bật chi phí thực thi. Ngưỡng phải có
#: lực phát hiện ở ĐÂY, không phải ở mức thảm hoạ.
MUC_BAT_LOI = -0.927

#: Cỡ mẫu cho 80% lực phát hiện ở `MUC_BAT_LOI`, hai phía 5%:
#:     n = ((1,95996 + 0,84162)·σ/|μ|)² = (2,80158·8,075/0,927)² = 595,31
#: làm tròn LÊN → 596. `docs/STATE.md` ghi 595 vì làm tròn xuống; chênh
#: một lệnh, không đổi đặc tính, nhưng mã phải khớp chính công thức của nó.
#: KHÔNG viết tay con số này — `co_mau_cho_luc()` tính ra nó, và
#: `tests/test_dieu_kien_dung_alpha.py` bắt hai bên phải khớp.
N_DAY_DU = 596

#: Dưới mốc này thì chưa đánh giá. 150 ≈ 25% thông tin của `N_DAY_DU`.
N_TOI_THIEU = 150

#: Biên HẠI được đánh giá LIÊN TỤC (mỗi lượt quét), nên phải nới rộng hơn
#: 1,96. Mô phỏng 40.000 lần với σ trên, đánh giá ở MỌI n từ 150:
#:     z=1,96 → sai lầm loại I 11,7%    z=2,30 → 5,8%    z=2,50 → 3,7%
#: Chọn 2,30 để giữ loại I ở mức ~5%.
Z_BIEN_HAI = 2.30

#: Mốc `N_DAY_DU` là MỘT phép kiểm tại một điểm, không nhìn lặp, nên giữ
#: 1,96.
Z_LOI_THE = 1.959964


def co_mau_cho_luc(muc: float = MUC_BAT_LOI, sigma: float = SIGMA_ALPHA,
                   luc: float = 0.80) -> int:
    """Cỡ mẫu để đạt `luc` lực phát hiện cho hiệu ứng `muc`, hai phía 5%.

    Tồn tại để `N_DAY_DU` KHÔNG phải một con số chọn bằng trực giác. Mọi
    ngưỡng dừng trong dự án này phải suy được từ lực phát hiện ở mức hiệu
    ứng THỰC TẾ — đó chính là chỗ bản 1 sai.
    """
    z_b = {0.80: 0.841621, 0.90: 1.281552}[luc]
    return math.ceil(((1.959964 + z_b) * sigma / abs(muc)) ** 2)


def lenh_tien_ve_truoc(trades: list[Trade]) -> list[Trade]:
    """Lệnh KHÔNG thuộc lô ghi hàng loạt nào và có dấu thời gian ghi.

    Lệnh thiếu `created_at` bị loại — không phải vì chúng xấu, mà vì
    không chứng minh được chúng tích luỹ tiến về phía trước. Bằng chứng
    chưa rõ nguồn gốc thì không được tính là bằng chứng.
    """
    trong_lo: set = set()
    for x in lo_ghi_hang_loat(trades):
        trong_lo |= x.get("ids", set())
    return [t for t in trades
            if t.created_at is not None and t.id not in trong_lo]


def dieu_kien_dong_lai(trades: list[Trade],
                       benchmark: dict | None = None) -> dict:
    """Cổng C5 có nên đóng lại không. `dat=True` nghĩa là NÊN ĐÓNG.

    Đo bằng ALPHA KHỚP TỪNG LỆNH (bất biến 6), trên nhóm lệnh
    tiến-về-trước ĐÃ ĐÓNG và khớp được cặp ngày với rổ chuẩn.

        n < N_TOI_THIEU        chưa đủ để kết luận
        N_TOI_THIEU ≤ n < N_DAY_DU
                               ĐÓNG nếu cận TRÊN của KTC (z=2,30) < 0
                               → alpha âm một cách đo được   [biên HẠI]
        n ≥ N_DAY_DU           ĐÓNG TRỪ KHI cận DƯỚI của KTC (z=1,96) > 0
                               → đã đủ cỡ mẫu nêu trước mà vẫn chưa chứng
                                 minh được lợi thế             [đảo gánh nặng]

    Vế thứ ba là chỗ bản 1 không có, và là chỗ định giá sai lầm loại II:
    một hệ thống chỉ đơn giản KHÔNG có lợi thế sẽ bị đóng, chứ không được
    chạy vô hạn vì chưa ai chứng minh được nó có hại.

    Đặc tính đo bằng mô phỏng 40.000 lần (σ = 8,075%/lệnh, chạy tại n=595):

        μ thật     ĐÓNG    vì hại  chưa chứng minh   n trung bình
        −2,000%   100,0%   100,0%          0,0%          161
        −0,927%   100,0%    81,1%         18,9%          335
        −0,500%   100,0%    39,1%         60,9%          482
         0,000%    99,6%     5,8%         93,8%          580
        +0,500%    79,7%     0,4%         79,3%          686
        +0,927%    27,6%     0,0%         27,6%          890
        +2,000%     0,0%     0,0%          0,0%          995

    Đọc đúng hai dòng khó chịu nhất:
      • μ=0 → đóng 99,6%. ĐÚNG Ý ĐỒ: không lợi thế thì dừng.
      • μ=+0,5% → đóng 79,7%. Một lợi thế thật nhưng NHỎ HƠN mức thiết kế
        (±0,927%) cần ~2.050 lệnh mới phân biệt được với 0. Dự án không
        chạy đủ dài cho mức đó, nên nó chọn dừng thay vì chạy tiếp bằng
        hy vọng. Đây là một lựa chọn được nêu ra, không phải một điểm mù.

    `benchmark` THIẾU thì KHÔNG kết luận, và nói ra lý do. Không được lặng
    lẽ quay về kỳ vọng — đó đúng là lỗi đang sửa.
    """
    tien = lenh_tien_ve_truoc(trades)
    dong = [t for t in tien if t.status == "CLOSED"]
    cam_ket = [t for t in tien if t.status in ("OPEN", "PENDING", "CLOSING")]
    #: `do_duoc=False` nghĩa là phép kiểm KHÔNG chạy được, khác hẳn
    #: `dat=False` nghĩa là đã chạy và chưa tới ngưỡng. Người gọi phải
    #: phân biệt được hai thứ đó mà không phải so chuỗi lý do.
    khung = {"so_lenh": 0, "n_cam_ket": len(cam_ket), "alpha": None,
             "ci": (None, None), "bo_qua": 0, "do_duoc": False}

    if benchmark is None:
        return {**khung, "dat": False,
                "ly_do": ("KHÔNG đo được — thiếu rổ đối chiếu VN-INDEX. "
                          "Điều kiện này đo ALPHA, không đo kỳ vọng; không "
                          "có rổ chuẩn thì nó không kết luận gì cả")}

    b = vs_benchmark(dong, benchmark, z=Z_BIEN_HAI)
    n = b["n"]
    duoi_ke = (f" · {len(cam_ket)} lệnh đã cam kết chưa đóng"
               if cam_ket else "")
    bo_ke = (f" · {b['bo_qua']} lệnh BỊ BỎ vì không khớp cặp ngày trong rổ"
             if b.get("bo_qua") else "")
    khung.update(so_lenh=n, bo_qua=b.get("bo_qua", 0), do_duoc=True)

    if n < N_TOI_THIEU:
        return {**khung, "dat": False,
                "ly_do": (f"mới {n}/{N_TOI_THIEU} lệnh tiến-về-trước có đối "
                          f"chiếu — chưa đủ để kết luận{duoi_ke}{bo_ke}")}

    lo, hi = b["ci"]
    alpha = b["alpha"]
    khung.update(alpha=alpha, ci=(lo, hi))

    if hi < 0:
        return {**khung, "dat": True,
                "ly_do": (f"{n} lệnh, alpha {alpha:+.3f}%/lệnh, KTC 97,9% "
                          f"[{lo:+.3f}; {hi:+.3f}] — cận trên dưới 0, hệ "
                          f"thống THUA rổ chuẩn một cách đo được{duoi_ke}")}

    if n >= N_DAY_DU:
        b95 = vs_benchmark(dong, benchmark, z=Z_LOI_THE)
        lo95, hi95 = b95["ci"]
        if not lo95 > 0:
            return {**khung, "ci": (lo95, hi95), "dat": True,
                    "ly_do": (f"{n} lệnh — đã đủ cỡ mẫu nêu trước "
                              f"({N_DAY_DU}) mà alpha {alpha:+.3f}%/lệnh vẫn "
                              f"chưa chứng minh được lợi thế: KTC 95% "
                              f"[{lo95:+.3f}; {hi95:+.3f}] không loại được "
                              f"số 0{duoi_ke}")}
        return {**khung, "ci": (lo95, hi95), "dat": False,
                "ly_do": (f"{n} lệnh, alpha {alpha:+.3f}%/lệnh, KTC 95% "
                          f"[{lo95:+.3f}; {hi95:+.3f}] — VƯỢT rổ chuẩn có ý "
                          f"nghĩa{duoi_ke}")}

    return {**khung, "dat": False,
            "ly_do": (f"{n}/{N_DAY_DU} lệnh, alpha {alpha:+.3f}%/lệnh, KTC "
                      f"97,9% [{lo:+.3f}; {hi:+.3f}] — chưa chạm biên hại"
                      f"{duoi_ke}{bo_ke}")}


def report(trades: list[Trade],
           benchmark: dict[tuple[str, str], float] | None = None) -> str:
    out: list[str] = []
    add = out.append
    add("=" * 64)
    add("SỔ LỆNH GIẤY CỦA AGENT")
    add("=" * 64)

    perf = compute(trades)
    n_open = sum(1 for t in trades if t.status in ("OPEN", "PENDING"))
    if perf is None:
        add(f"Chưa có lệnh nào đóng. Đang mở/chờ: {n_open}")
        return "\n".join(out)

    add(f"Đã đóng   : {perf.n_trades} lệnh   |  Đang mở/chờ: {n_open}")
    add(f"Tỷ lệ thắng: {perf.win_rate:.1%}")

    # Bổ sung danh sách chi tiết các vị thế ĐANG MỞ / CHỜ KHỚP
    active_trades = [t for t in trades if t.status in ("OPEN", "PENDING")]
    if active_trades:
        add("")
        add("─" * 64)
        add("📌 DANH SÁCH LỆNH ĐANG MỞ & CHỜ KHỚP (ACTIVE POSITIONS):")
        add("─" * 64)
        add(f"{'MÃ':<6} | {'TRẠNG THÁI':<9} | {'NGÀY VÀO':<10} | {'GIÁ VÀO (VNĐ)':<13} | {'STOP LOSS':<10} | {'VỐN':<5}")
        add("─" * 64)
        for t in active_trades:
            entry_p = f"{t.entry_price:,.0f}" if t.entry_price else "Chờ mở cửa"
            sl_p = f"{t.stop_loss:,.0f}" if t.stop_loss else "N/A"
            add(f"{t.symbol:<6} | {t.status:<9} | {str(t.entry_date or t.signal_date):<10} | {entry_p:<13} | {sl_p:<10} | {t.size_pct:.0f}%")
        add("─" * 64)
    add(f"Lãi TB    : {perf.avg_win:+.2f}%   |  Lỗ TB: {perf.avg_loss:+.2f}%")
    add(f"Kỳ vọng   : {perf.expectancy:+.2f}% mỗi lệnh (đã trừ "
        f"{ROUND_TRIP_COST_PCT:.2f}% phí)")
    add(f"Profit factor: {perf.profit_factor:.2f}")
    add(f"Lợi nhuận cộng dồn: {perf.total_net_pct:+.2f}%")
    add(f"Sụt giảm tối đa   : {perf.max_drawdown_pct:.1f}%")
    add(f"Vốn triển khai    : {perf.avg_capital_deployed_pct:.0f}% trung bình "
        f"| {perf.peak_capital_deployed_pct:.0f}% đỉnh điểm")

    if perf.is_leveraged:
        don_bay = perf.avg_capital_deployed_pct / 100
        add("")
        add("🚨 CẢNH BÁO ĐÒN BẨY — con số lợi nhuận ở trên KHÔNG có thật")
        add(f"   Sổ này giữ trung bình {perf.avg_capital_deployed_pct:.0f}% vốn "
            f"cùng lúc, tức đòn bẩy {don_bay:.1f} lần.")
        add(f"   'Lợi nhuận cộng dồn {perf.total_net_pct:+.2f}%' là của một tài "
            f"khoản vay được")
        add(f"   {don_bay:.1f}x vốn. Tài khoản thật không chạy được như vậy.")
        add(f"   Chia tỷ trọng cho {don_bay:.1f} rồi đo lại mới ra con số dùng được.")

    lo = tom_tat_lo_ghi(trades)
    if lo["so_lo"]:
        add("")
        add("⚠️ SỔ NÀY KHÔNG PHẢI BẢN GHI TÍCH LUỸ")
        for x in lo["lo"]:
            t1 = datetime.fromtimestamp(x["ghi_tu"]).strftime("%d/%m/%Y %H:%M")
            add(f"   {x['so_lenh']} lệnh được ghi trong {x['giay']:.0f} giây "
                f"({t1}),")
            add(f"   nhưng tín hiệu của chúng trải {x['tin_hieu_tu']} → "
                f"{x['tin_hieu_den']} ({x['ngay_trai']} ngày).")
        add("   Đó là dấu vết của MỘT lượt mô phỏng, không phải nhiều phiên")
        add("   quét tiến về phía trước. Kỳ vọng, KTC và alpha ở trên vẫn")
        add("   đúng như phép tính, nhưng chúng nói về lượt mô phỏng ấy.")
    _dk = dieu_kien_dong_lai(trades, benchmark)
    add("")
    add(f"Cổng C5 (mở vị thế mới): {_dk['ly_do']}")
    if _dk["dat"]:
        add("   🔴 ĐIỀU KIỆN ĐÓNG LẠI ĐÃ ĐẠT — bản 2, nêu 29/08/2026.")
        add("   Đặt CHO_PHEP_MO_LENH_MOI = False rồi báo người dùng.")
    if lo["so_lenh_khong_ro"]:
        add(f"   ({lo['so_lenh_khong_ro']} lệnh không có dấu thời gian ghi — "
            f"không kết luận được)")

    add("")
    add("Lý do đóng lệnh:")
    labels = {ExitReason.STOP_LOSS: "Chạm cắt lỗ",
              ExitReason.TAKE_PROFIT: "Chạm chốt lời",
              ExitReason.SIGNAL_REVERSED: "Tín hiệu đảo chiều",
              ExitReason.MAX_HOLD: "Hết hạn nắm giữ"}
    for k, v in sorted(perf.by_exit_reason.items(), key=lambda x: -x[1]):
        add(f"  {labels.get(k, k):<22} {v:>4}  ({v / perf.n_trades:.0%})")

    add("")
    sig = expectancy_significant(trades)
    add("─" * 64)
    if sig["expectancy"] is not None:
        add(f"Kỳ vọng {sig['expectancy']:+.2f}%  "
            f"[KTC 95%: {sig['ci'][0]:+.2f}%, {sig['ci'][1]:+.2f}%]")
    add(f"  → {sig['verdict']}")

    if benchmark:
        b = vs_benchmark(trades, benchmark)
        add("")
        if b.get("alpha") is not None:
            add(f"So với cầm đều cả rổ cùng kỳ: {b['alpha']:+.2f}%/lệnh  "
                f"[{b['ci'][0]:+.2f}%, {b['ci'][1]:+.2f}%]")
        add(f"  → {b['verdict']}")
        if b.get("bo_qua"):
            add(f"  ⚠️ ĐÃ BỎ {b['bo_qua']} lệnh vì không tìm được cặp ngày "
                f"trong rổ chuẩn — phép đo này chỉ nói về "
                f"{b['n']}/{b['n'] + b['bo_qua']} lệnh.")
    else:
        add("")
        add("⚠️ Chưa có đối chiếu chuẩn. Con số ở trên KHÔNG nói lên được gì")
        add("   cho tới khi biết thị trường chung đi thế nào trong cùng kỳ.")

    add("")
    add("=" * 64)
    add("CÁCH ĐỌC")
    add("=" * 64)
    add("• Dưới ~100 lệnh, mọi kết luận đều mong manh. Kiên nhẫn.")
    add("• Kỳ vọng dương mà khoảng tin cậy chứa 0 = chưa biết gì.")
    add("• Chỉ so với chuẩn mới tách được kỹ năng chọn mã khỏi xu hướng chung.")
    add("• Sổ này chỉ đo TÍN HIỆU. Giao dịch thật còn có trượt giá, khớp")
    add("  một phần và tâm lý — kết quả thực tế sẽ thấp hơn.")
    return "\n".join(out)
