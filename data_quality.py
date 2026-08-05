"""
data_quality.py
──────────────────────────────────────────────────────────────────────
Tầng kiểm định đặt GIỮA nguồn dữ liệu và pipeline phân tích.

Vấn đề nó giải: dữ liệu sai đi qua hệ thống mà không để lại dấu vết.
Chỉ báo kỹ thuật vẫn tính ra số, biểu đồ vẫn vẽ đẹp, khuyến nghị vẫn được
sinh ra — chỉ có điều tất cả đều sai. Không ai biết.

Bốn nhóm vấn đề được xử lý ở đây:
  1. Múi giờ  — mọi mốc thời gian phải là giờ Việt Nam, không phải giờ server.
  2. Đơn vị   — quyết định nghìn đồng/đồng MỘT LẦN cho cả chuỗi, không phải
                mỗi nơi tự đoán từ giá trị cuối cùng.
  3. Tính hợp lệ — high≥low, giá dương, không trùng ngày, cột đủ.
  4. Độ mới   — dữ liệu cũ phải bị phát hiện, không hiển thị như giá hiện tại.

Nguyên tắc xử lý: chặn theo mức độ.
    BLOCK → dữ liệu hỏng về mặt cấu trúc, tuyệt đối không dùng.
    WARN  → đáng ngờ nhưng có thể hợp lệ, vẫn dùng nhưng phải gắn nhãn.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import IntEnum

import pandas as pd

# ─────────────────────────── Múi giờ Việt Nam ────────────────────────
try:
    from zoneinfo import ZoneInfo
    VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:                                  # thiếu tzdata (hay gặp trên Windows)
    VN_TZ = timezone(timedelta(hours=7), name="ICT")


def now_vn() -> datetime:
    """Thời điểm hiện tại theo giờ Việt Nam.

    Dùng hàm này thay cho datetime.now(). Streamlit Cloud chạy UTC, nên
    datetime.now() sớm hơn giờ VN 7 tiếng — vừa hiển thị sai, vừa khiến
    mốc `end` khi lấy dữ liệu bỏ sót phiên gần nhất.
    """
    return datetime.now(VN_TZ)


def today_vn() -> datetime:
    return now_vn().replace(hour=0, minute=0, second=0, microsecond=0)


# ─────────────────────────── Mức độ & báo cáo ────────────────────────
class Severity(IntEnum):
    OK = 0
    WARN = 1
    BLOCK = 2


@dataclass
class Issue:
    code: str
    severity: Severity
    message: str


@dataclass
class QualityReport:
    symbol: str
    issues: list[Issue] = field(default_factory=list)
    unit_multiplier: float = 1.0        # nhân với giá thô để ra VNĐ
    rows: int = 0
    last_date: str = ""

    @property
    def level(self) -> Severity:
        return max((i.severity for i in self.issues), default=Severity.OK)

    @property
    def blocked(self) -> bool:
        return self.level >= Severity.BLOCK

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARN]

    @property
    def blockers(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.BLOCK]

    def summary(self) -> str:
        if self.blocked:
            return "🔴 " + " · ".join(i.message for i in self.blockers)
        if self.warnings:
            return "🟡 " + " · ".join(i.message for i in self.warnings)
        return "🟢 Dữ liệu hợp lệ"


# ─────────────────────────── Quy đổi đơn vị ──────────────────────────
# Một số nguồn trả giá theo nghìn đồng (FPT = 71.2), số khác theo đồng
# (FPT = 71200). Quyết định dựa trên TRUNG VỊ của cả chuỗi, không phải
# giá trị cuối — trung vị ổn định, không nhảy giữa hai phiên liền kề.
UNIT_THRESHOLD = 1000.0


def period_span_days(df: pd.DataFrame | None) -> int:
    """Số ngày dữ liệu thực sự có, tính từ cột `time`."""
    if df is None or not isinstance(df, pd.DataFrame) or "time" not in df:
        return 0
    t = pd.to_datetime(df["time"], errors="coerce").dropna()
    if len(t) < 2:
        return 0
    return int((t.max() - t.min()).days)


def period_label(days: int) -> str:
    """Nhãn mô tả khoảng thời gian, suy ra từ DỮ LIỆU THẬT.

    Lý do tồn tại: nhãn cứng trong giao diện sẽ lệch khỏi dữ liệu ngay khi
    ai đó đổi cửa sổ lấy dữ liệu. Ứng dụng từng hiển thị "52T Thấp - Cao"
    trong khi chỉ có 180 ngày — số liệu đúng, nhãn sai.
    """
    if days <= 0:
        return "không rõ kỳ"
    if days < 45:
        return f"{max(1, round(days / 7))} tuần"
    months = round(days / 30.44)
    if months < 12:
        return f"{months} tháng"
    years = days / 365.25
    return f"{years:.0f} năm" if abs(years - round(years)) < 0.15 \
        else f"{round(days / 30.44)} tháng"


def price_multiplier(df: pd.DataFrame | None) -> float:
    """Hệ số quy đổi giá thô sang VNĐ cho một bảng OHLCV.

    Điểm vào duy nhất cho mọi nơi trong ứng dụng. Trước đây bốn chỗ tự tính
    `1000 if close.iloc[-1] < 1000 else 1` — vừa giòn vừa có thể lệch nhau.
    """
    if df is None or not isinstance(df, pd.DataFrame) or "close" not in df:
        return 1.0
    return detect_unit_multiplier(df["close"])[0]


def detect_unit_multiplier(close: pd.Series) -> tuple[float, str | None]:
    """Trả (hệ số nhân, cảnh báo nếu chuỗi không nhất quán).

    Cách cũ `1000 if close.iloc[-1] < 1000 else 1` rất giòn: một mã giao
    dịch quanh mốc 1.000đ sẽ nhảy hệ số 1000× giữa hai phiên liền kề.
    """
    valid = pd.to_numeric(close, errors="coerce").dropna()
    valid = valid[valid > 0]
    if valid.empty:
        return 1.0, "không có giá hợp lệ để xác định đơn vị"

    median = float(valid.median())
    mult = 1000.0 if median < UNIT_THRESHOLD else 1.0

    # Nếu chuỗi có cả giá trị hai bên ngưỡng một cách đáng kể -> nghi ngờ
    below = float((valid < UNIT_THRESHOLD).mean())
    if 0.05 < below < 0.95:
        return mult, (f"đơn vị giá không nhất quán: {below:.0%} số phiên "
                      f"dưới {UNIT_THRESHOLD:,.0f}, phần còn lại trên")
    return mult, None


# ─────────────────────────── Biên độ dao động ────────────────────────
# Biên độ giá trong phiên theo sàn. Vượt biên độ thường là dấu hiệu của
# sự kiện doanh nghiệp (chia tách, cổ tức) mà nguồn chưa điều chỉnh giá —
# nên CẢNH BÁO chứ không chặn, vì cũng có thể do ngày giao dịch không liền.
EXCHANGE_LIMITS = {"HOSE": 0.07, "HNX": 0.10, "UPCOM": 0.15}

REQUIRED_COLUMNS = ("time", "open", "high", "low", "close", "volume")
STALE_WARN_DAYS = 4       # cuối tuần + 1 ngày lễ
STALE_BLOCK_DAYS = 10


def validate_ohlcv(df: pd.DataFrame | None, symbol: str = "",
                   exchange: str = "HOSE") -> QualityReport:
    """Kiểm định một bảng OHLCV. Không sửa dữ liệu, chỉ báo cáo."""
    rep = QualityReport(symbol=symbol)
    add = lambda c, s, m: rep.issues.append(Issue(c, s, m))

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        add("EMPTY", Severity.BLOCK, "không có dữ liệu")
        return rep

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        add("MISSING_COLS", Severity.BLOCK, f"thiếu cột: {', '.join(missing)}")
        return rep

    rep.rows = len(df)
    if rep.rows < 20:
        add("TOO_SHORT", Severity.BLOCK,
            f"chỉ có {rep.rows} phiên, không đủ để tính chỉ báo")
        return rep

    o, h, l, c = (pd.to_numeric(df[k], errors="coerce")
                  for k in ("open", "high", "low", "close"))
    vol = pd.to_numeric(df["volume"], errors="coerce")

    # ── Cấu trúc giá ──────────────────────────────────────────────────
    if c.isna().all():
        add("ALL_NAN", Severity.BLOCK, "toàn bộ giá đóng cửa không đọc được")
        return rep
    n_nan = int(c.isna().sum())
    if n_nan:
        sev = Severity.BLOCK if n_nan > rep.rows * 0.1 else Severity.WARN
        add("NAN_CLOSE", sev, f"{n_nan}/{rep.rows} phiên thiếu giá đóng cửa")

    if bool((c <= 0).any()):
        add("NON_POSITIVE", Severity.BLOCK,
            f"{int((c <= 0).sum())} phiên có giá ≤ 0")

    bad_hl = int((h < l).sum())
    if bad_hl:
        add("HIGH_LT_LOW", Severity.BLOCK, f"{bad_hl} phiên có giá cao < giá thấp")

    outside = int(((c > h) | (c < l) | (o > h) | (o < l)).sum())
    if outside:
        sev = Severity.BLOCK if outside > rep.rows * 0.02 else Severity.WARN
        add("OHLC_INCONSISTENT", sev,
            f"{outside} phiên có giá mở/đóng nằm ngoài khoảng cao-thấp")

    if bool((vol < 0).any()):
        add("NEGATIVE_VOLUME", Severity.BLOCK, "có khối lượng âm")
    elif bool((vol.fillna(0) == 0).all()):
        add("ZERO_VOLUME", Severity.WARN, "toàn bộ khối lượng bằng 0")

    # ── Trục thời gian ────────────────────────────────────────────────
    times = pd.to_datetime(df["time"], errors="coerce")
    if times.isna().all():
        add("BAD_TIME", Severity.BLOCK, "không đọc được cột thời gian")
        return rep

    n_dup = int(times.duplicated().sum())
    if n_dup:
        add("DUPLICATE_DATES", Severity.BLOCK, f"{n_dup} ngày bị lặp")

    if not times.dropna().is_monotonic_increasing:
        add("UNSORTED", Severity.WARN, "dữ liệu chưa sắp xếp theo thời gian")

    last = times.dropna().max()
    rep.last_date = last.strftime("%Y-%m-%d")
    age = (today_vn().date() - last.date()).days
    if age >= STALE_BLOCK_DAYS:
        add("STALE", Severity.BLOCK,
            f"dữ liệu cũ {age} ngày (phiên gần nhất {rep.last_date})")
    elif age >= STALE_WARN_DAYS:
        add("STALE", Severity.WARN,
            f"dữ liệu cũ {age} ngày (phiên gần nhất {rep.last_date})")

    # ── Đơn vị giá ────────────────────────────────────────────────────
    rep.unit_multiplier, unit_warn = detect_unit_multiplier(c)
    if unit_warn:
        add("UNIT_INCONSISTENT", Severity.WARN, unit_warn)

    # ── Biến động vượt biên độ ────────────────────────────────────────
    limit = EXCHANGE_LIMITS.get(str(exchange).upper(), 0.15)
    ret = c.pct_change().abs()
    # bỏ qua phiên có khoảng cách ngày lớn (nghỉ lễ dài) để tránh báo nhầm
    gap_days = times.diff().dt.days.fillna(1)
    suspicious = int(((ret > limit * 1.5) & (gap_days <= 4)).sum())
    if suspicious:
        add("PRICE_JUMP", Severity.WARN,
            f"{suspicious} phiên biến động vượt biên độ {limit:.0%} sàn "
            f"{exchange} — có thể do chia tách/cổ tức chưa điều chỉnh giá")

    return rep


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hoá: ép kiểu số, bỏ ngày trùng, sắp xếp tăng dần.

    Không lấp giá trị thiếu và không sửa giá — chỉ dọn những thứ chắc chắn
    an toàn. Việc lấp dữ liệu sẽ tạo ra số không có thật.
    """
    out = df.copy()
    for col in ("open", "high", "low", "close", "volume"):
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "time" in out:
        out["_t"] = pd.to_datetime(out["time"], errors="coerce")
        out = (out.dropna(subset=["_t"])
                  .drop_duplicates(subset=["_t"], keep="last")
                  .sort_values("_t")
                  .drop(columns=["_t"])
                  .reset_index(drop=True))
    return out
