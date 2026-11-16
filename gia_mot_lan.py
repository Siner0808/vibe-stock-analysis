"""Một lần tải giá cho MỘT mã, rồi cắt khung (BƯỚC 280, phần C) — CHỈ cho app, không đổi một con số.

VÌ SAO. Trang app xin giá của cùng một mã dưới ba cửa sổ ngày (180 · 1.095 · 1.583 ngày lịch: biểu
đồ, ô cấu trúc Dow, nến tuần/tháng) và VN-INDEX dưới cửa sổ thứ ba; mỗi cửa sổ là một lượt gọi mạng
riêng (đo 16/11/2026: 0,29 + 0,69 + một phần của 2,38 giây lúc mở lần đầu, và cùng ba lượt lúc đổi mã).

GIỚI HẠN ĐO ĐƯỢC (16/11/2026, `dbg_C3`: 10 mã + VN-INDEX × 5 cửa sổ). Chuỗi nguồn là Entrade → VNDirect →
VPS; Entrade BỊ BỎ ở cửa sổ 1.583 ngày (hai nến cùng một ngày phiên trong lịch sử cũ) nên cửa sổ ấy do VNDirect
phục vụ, còn 180 · 420 · 800 · 1.095 ngày do Entrade. Hai nguồn cho giá LÀM TRÒN KHÁC (chênh tới 0,005 trên
giá nghìn đồng, khối lượng lệch tới 56.194 ở PVS), nên cửa sổ 1.583 ngày KHÔNG cắt thành các cửa sổ ngắn được:
số trên biểu đồ sẽ đổi. Vì vậy chỉ gộp các cửa sổ cùng do NGUỒN ĐẦU CỦA CHUỖI phục vụ (`tai_mot_lan` kiểm
tên nguồn của lượt tải rộng), và app chỉ gộp biểu đồ ngày (180) với ô cấu trúc Dow (1.095).

CÁCH CẮT ĐÚNG. `VNStockCollectorAgent.collect(mã, start, end)` luôn trả `n` nến CUỐI của chuỗi
đã chuẩn hoá, `n` suy từ cặp (start, end) bởi `nguon_gia_cong_khai.cua_so_vci_cu` — nó KHÔNG đọc
`start` theo nghĩa "từ ngày ấy" (`CLAUDE.md`, mục Dữ liệu: đừng "sửa" về tôn trọng `start`). Hai cửa
sổ cùng `end` vì thế là hai ĐUÔI của cùng một chuỗi: cửa sổ hẹp = `n_hẹp` dòng cuối của cửa sổ rộng.
Hàm này làm đúng phép ấy rồi chạy lại `validate_ohlcv` trên phần cắt để lấy cùng danh sách cảnh báo.

KHÔNG sửa `collect` và không chạm thứ `run_daily` dùng. Chỗ nào không chắc cắt được (bảng rộng ngắn
hơn cửa sổ hẹp, kiểm định chặn phần cắt) thì trả `None` và người gọi tải theo đường cũ.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd


def so_nen_cua_so(start: str, end: str) -> int:
    """Số nến cuối mà `collect(…, start, end)` giữ lại — đúng hàm của đường tải, không gõ lại công thức."""
    import nguon_gia_cong_khai as ngk
    return ngk.cua_so_vci_cu(start, end)[1]


def cat_tu_khung_rong(df_rong: Optional[pd.DataFrame], start: str, end: str, *,
                      symbol: str, exchange: str) -> Optional[tuple]:
    """`(df, "OK", cảnh_báo)` — ĐÚNG ba thứ mà `load_stock_data(symbol, start, end, exchange)` trả — hay `None`.

    `df_rong` là kết quả `collect` của một cửa sổ RỘNG HƠN (cùng `end`, cùng mã). `None` khi không
    chắc cắt được: bảng rộng rỗng hoặc ngắn hơn `n` nến của cửa sổ hẹp (mã niêm yết muộn: cửa sổ hẹp có
    thể thấy ít nến hơn phần suy ra), hoặc kiểm định chặn phần cắt.
    """
    from data_quality import validate_ohlcv
    if df_rong is None or not isinstance(df_rong, pd.DataFrame) or df_rong.empty:
        return None
    n = so_nen_cua_so(start, end)
    if n <= 0 or n > len(df_rong):
        return None
    df = df_rong.tail(n).reset_index(drop=True)
    bao_cao = validate_ohlcv(df, symbol=symbol, exchange=exchange)
    if bao_cao.blocked:
        return None
    return df, "OK", [i.message for i in bao_cao.warnings]


def nguon_dau_chuoi(ticker: str) -> str:
    """Tên nguồn ĐỨNG ĐẦU chuỗi giá của `ticker` (Entrade cho cổ phiếu, VNDirect cho VN-Index)."""
    import nguon_gia_cong_khai as ngk
    return ngk.chuoi_nguon(str(ticker).strip().upper())[0].ten


def tai_mot_lan(tai_nguon, tai, ticker: str, start: str, end: str, exch: str, ngay_rong: int) -> tuple:
    """Giá của `ticker` cho cửa sổ (start, end): cắt từ MỘT lượt tải cửa sổ rộng `ngay_rong` ngày lịch.

    `tai_nguon(ticker, start, end, exch)` trả `(df, trạng_thái, cảnh_báo, tên_nguồn)` (`app.load_stock_data_nguon`,
    có đệm); `tai(ticker, start, end, exch)` là đường tải cũ `(df, trạng_thái, cảnh_báo)`. Hai cửa sổ của app
    cùng `end` nên cùng gọi `tai_nguon` với CÙNG đối số rộng và chỉ lượt đầu đi qua mạng.

    CHỈ cắt khi lượt tải rộng do NGUỒN ĐẦU CHUỖI phục vụ: khi đó mọi cửa sổ hẹp hơn cũng do nguồn ấy phục vụ
    (khoảng của chúng nằm trong khoảng rộng) và cho đúng các nến cuối. Nguồn khác (đã bỏ nguồn đầu) cho giá làm
    tròn khác — xem docstring module. Không cắt được (tải rộng hỏng, trạng thái khác OK, sai nguồn,
    `cat_tu_khung_rong` trả `None`) thì trả đúng thứ `tai(ticker, start, end, exch)` trả.
    """
    tu_rong = min(pd.Timestamp(start), pd.Timestamp(end) - pd.Timedelta(days=ngay_rong))
    df_rong, trang_thai, _, nguon = tai_nguon(ticker, tu_rong.strftime("%Y-%m-%d"), end, exch)
    if trang_thai == "OK" and nguon == nguon_dau_chuoi(ticker):
        cat = cat_tu_khung_rong(df_rong, start, end, symbol=ticker, exchange=exch)
        if cat is not None:
            return cat
    return tai(ticker, start, end, exch)
