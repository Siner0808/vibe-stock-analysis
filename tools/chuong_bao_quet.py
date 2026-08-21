"""Chuông báo: ngày làm việc mà không có lượt quét nào thành công.

VÌ SAO CÓ FILE NÀY
──────────────────
Từ 20/08/2026 Task Scheduler đã tắt, chỉ còn GitHub Actions quét sổ lệnh.
Trước đó máy cục bộ vô tình làm lưới dự phòng; giờ không còn. Một ngày mà
mọi lượt Actions đều hỏng thì ngày đó không được quét, sổ lệnh không cập
nhật, và **không ai biết** — đúng kiểu hỏng âm thầm mà dự án này đã dính
nhiều lần.

SOÁT NHIỀU NGÀY, KHÔNG CHỈ HÔM NAY
──────────────────────────────────
Chuông chạy bằng chính cron GitHub — thứ đã đo được là rơi mất khoảng một
nửa số nhịp (xem CLAUDE.md, mục "Quét tự động"). Chuông không kêu thì im
lặng, đúng thứ nó sinh ra để chống.

Nên mỗi lượt chuông soát SO_NGAY_SOAT ngày làm việc gần nhất chứ không chỉ
hôm nay. Một nhịp chuông bị rơi thì nhịp hôm sau vẫn bắt được ngày đó. Nó
không xoá được rủi ro — nhiều nhịp liên tiếp cùng rơi thì vẫn im — nhưng
thu hẹp cửa sổ im lặng từ "một nhịp" xuống "SO_NGAY_SOAT nhịp liên tiếp".

ĐO CÁI GÌ
─────────
Đếm **lượt chạy thành công của workflow quét**, không phải đếm bản ghi mới
trong sổ. Hai lý do:

  - Cái cần canh là "máy quét có chạy không", và đó đúng là thứ lượt chạy
    nói. Sổ không có bản ghi mới còn có thể vì thị trường nghỉ lễ.
  - Đọc sổ đòi credential Google; đọc lượt chạy chỉ cần GITHUB_TOKEN mà
    Actions tự cấp. Ít bộ phận hơn thì ít chỗ hỏng hơn.

Hệ quả phải biết: một lượt chạy "thành công" nhưng quét ra 0 mã vẫn được
tính là có quét. Chuông này canh sự VẮNG MẶT của phép quét, không canh
chất lượng của nó.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import urllib.error
import urllib.request

# Ngày workflow quét bắt đầu tồn tại. Không soát trước mốc này — trước đó
# vắng lượt chạy là chuyện đương nhiên, báo động sẽ là báo động giả.
NGAY_BAT_DAU = "2026-08-13"

# Số ngày làm việc soát mỗi lượt. 3 để một nhịp chuông rơi vẫn được nhịp
# sau phủ, mà không lôi lại quá xa quá khứ.
SO_NGAY_SOAT = 3

TEN_WORKFLOW_QUET = "quet-so-lenh.yml"


# ─────────────────────────────────────────────────────────────────────
# Phần thuần — không mạng, không đồng hồ. Đây là phần được test.
# ─────────────────────────────────────────────────────────────────────

def cac_ngay_lam_viec(den_ngay: _dt.date, so_ngay: int = SO_NGAY_SOAT,
                      tu_ngay: str = NGAY_BAT_DAU) -> list[str]:
    """SO_NGAY ngày làm việc gần nhất tính ngược từ `den_ngay`, gồm cả nó.

    Bỏ thứ Bảy và Chủ nhật (cron quét chỉ chạy T2–T6). Cắt ở `tu_ngay` để
    không soát giai đoạn workflow chưa tồn tại.
    """
    if so_ngay < 1:
        raise ValueError(f"so_ngay phải >= 1, nhận {so_ngay}")

    moc = _dt.date.fromisoformat(tu_ngay)
    ra: list[str] = []
    ngay = den_ngay
    while len(ra) < so_ngay and ngay >= moc:
        if ngay.weekday() < 5:          # 0=T2 … 4=T6
            ra.append(ngay.isoformat())
        ngay -= _dt.timedelta(days=1)
    return sorted(ra)


def dem_luot_thanh_cong(runs: list[dict]) -> dict[str, int]:
    """Đếm lượt chạy THÀNH CÔNG theo ngày (UTC).

    Dùng ngày UTC là đúng chứ không phải tiện: nhịp quét nằm trong
    02:00–08:30 UTC, tức 09:00–15:30 giờ VN cùng một ngày dương lịch. Hai
    múi giờ không lệch ngày ở khung giờ này.
    """
    theo_ngay: dict[str, int] = {}
    for r in runs:
        if r.get("conclusion") != "success":
            continue
        ngay = str(r.get("created_at", ""))[:10]
        if not ngay:
            continue
        theo_ngay[ngay] = theo_ngay.get(ngay, 0) + 1
    return theo_ngay


def kiem_tra(runs: list[dict], den_ngay: _dt.date,
             so_ngay: int = SO_NGAY_SOAT,
             tu_ngay: str = NGAY_BAT_DAU) -> dict:
    """Ngày làm việc nào trong khoảng soát không có lượt quét thành công.

    Trả về {"ngay_trong": [...], "chi_tiet": {ngày: số lượt}}.
    `ngay_trong` rỗng nghĩa là mọi ngày đều được quét.
    """
    can_soat = cac_ngay_lam_viec(den_ngay, so_ngay, tu_ngay)
    dem = dem_luot_thanh_cong(runs)
    chi_tiet = {ngay: dem.get(ngay, 0) for ngay in can_soat}
    return {
        "ngay_trong": [ngay for ngay, n in chi_tiet.items() if n == 0],
        "chi_tiet": chi_tiet,
    }


# ─────────────────────────────────────────────────────────────────────
# Phần có mạng
# ─────────────────────────────────────────────────────────────────────

def _tai_cac_luot(repo: str, token: str | None,
                  workflow: str = TEN_WORKFLOW_QUET) -> list[dict]:
    url = (f"https://api.github.com/repos/{repo}/actions/workflows/"
           f"{workflow}/runs?per_page=100")
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "vibe-chuong-bao",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as f:
        return json.loads(f.read().decode("utf-8")).get("workflow_runs", [])


def _ep_stdout_utf8() -> None:
    """Console Windows mặc định cp1258, in tiếng Việt là nổ UnicodeEncodeError.

    Nổ ở đây biến thành BÁO ĐỘNG GIẢ: tiến trình chết với mã thoát 1 vì
    lý do chẳng liên quan gì tới việc có quét hay không. Chuông kêu oan
    vài lần là người ta thôi nghe.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def main() -> int:
    _ep_stdout_utf8()
    repo = os.environ.get("GITHUB_REPOSITORY", "Siner0808/vibe-stock-analysis")
    token = os.environ.get("GITHUB_TOKEN")

    try:
        runs = _tai_cac_luot(repo, token)
    except (urllib.error.URLError, OSError, ValueError) as e:
        # Không đọc được danh sách lượt chạy thì KHÔNG kết luận là "không
        # có lượt nào" — đó là suy diễn từ sự thiếu thông tin, và nó sẽ
        # đẻ ra báo động giả. Nói rõ là chưa kiểm được.
        print(f"::error::Không đọc được danh sách lượt chạy: "
              f"{type(e).__name__}: {e}")
        return 1

    kq = kiem_tra(runs, _dt.datetime.now(_dt.timezone.utc).date())

    print(f"Soát {len(kq['chi_tiet'])} ngày làm việc gần nhất:")
    for ngay, n in sorted(kq["chi_tiet"].items()):
        print(f"  {ngay}  {n} lượt quét thành công"
              f"{'   <-- TRỐNG' if n == 0 else ''}")

    if kq["ngay_trong"]:
        print(f"::error::Không có lượt quét nào thành công trong ngày "
              f"{', '.join(kq['ngay_trong'])}. Sổ lệnh có thể chưa được "
              f"cập nhật cho (các) phiên đó — kiểm tab Actions và chạy tay "
              f"workflow 'Quét sổ lệnh' nếu cần.")
        return 1

    print("Mọi ngày trong khoảng soát đều có lượt quét thành công.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
