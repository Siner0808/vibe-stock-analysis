"""Nhật ký "VÌ SAO" của từng lệnh ảo — P2 của kế hoạch 25/09/2026.

Người dùng chốt (`docs/STATE.md` BƯỚC 122): agent tự đặt lệnh ảo, học sau
mỗi lệnh, và người dùng học theo từ sổ. Sổ lệnh (`trades`) trả lời *lệnh nào,
lãi lỗ bao nhiêu*; nhật ký này trả lời *VÌ SAO vào, và lệnh ấy dạy được gì*:

    lúc VÀO   điểm từng agent · lý do · bối cảnh · cắt lỗ BAN ĐẦU · rủi ro
    lúc ĐÓNG  lợi nhuận ròng · kết quả theo R · so với rổ · hậu kiểm máy
              · (hậu kiểm lời — Claude, khoá API người dùng tự đặt; P2c)

File này là phần THUẦN (P2a): nhận dữ liệu, trả dòng; không đọc sổ, không
ghi đĩa, không gọi mạng. Nối vào `paper_trading` và tab Sheets là P2b.

Ba quyết định, mỗi cái có lý do đo được:

1. **Cắt lỗ BAN ĐẦU phải ghi lúc khớp, không suy lại về sau.**
   `paper_trading.py` nâng `stop_loss` bằng `UPDATE trades SET stop_loss`
   (trailing), nên sau khi đóng lệnh sổ chỉ còn cắt lỗ CUỐI. Không có cắt lỗ
   ban đầu thì không có R. `dong_vao_lenh` đọc `trade.stop_loss` tại lúc khớp
   — trước mọi lần nâng — và giữ nó trong nhật ký.

2. **Không có công thức phí thứ hai.** Lợi nhuận ròng là
   `Trade.net_return_pct()` — docstring của nó: *"con số duy nhất đáng tin"*.
   So với rổ là đúng hình dạng `paper_metrics.vs_benchmark`: ròng trừ % đổi
   của rổ trên cùng cặp ngày (bất biến 6). Gác AST khoá cả hai.

3. **Hậu kiểm máy chỉ NÓI điều đo được trên chính lệnh ấy.** Không suy ra
   "agent X sai" từ một lệnh — một lệnh không phải bằng chứng (bất biến 5).
   Nó gắn nhãn: kết cục, so rổ, gap dưới cắt lỗ, trailing đã nâng, lỗ vượt 1R,
   và agent cao/thấp nhất lúc vào. Việc học từ NHIỀU lệnh là tầng 3.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from paper_trading import ExitReason, Status, Trade

#: Thứ tự cột LÀ hợp đồng với tab Google Sheets (P2b) — cùng quy ước
#: `sheets_store.TRADE_COLS`: đổi thứ tự hay tên là đổi lược đồ.
COT_NHAT_KY: tuple[str, ...] = (
    "trade_id", "symbol", "signal_date", "entry_date", "entry_price",
    "stop_loss_ban_dau", "rui_ro_pct", "entry_score", "diem_agent", "ly_do",
    "boi_canh",
    "exit_date", "exit_price", "exit_reason", "loi_nhuan_rong_pct",
    "ket_qua_R", "ro_chuan_pct", "alpha_pct", "hau_kiem_may", "hau_kiem_loi",
)

#: Khoá điểm KHÔNG đem ra nói "agent cao/thấp nhất", mỗi khoá một lý do đo được.
KHOA_KHONG_XEP_HANG: dict[str, str] = {
    "news_score": "hằng số 50 trên đường giao dịch (MO-XE-KIEN-TRUC.md, Tầng 2)",
    "fundamental_score": "trọng số 0 — không vào điểm (master_agent.TRONG_SO_CO_BAN)",
}


def rui_ro_pct(gia_vao: Optional[float], sl_ban_dau: Optional[float]) -> Optional[float]:
    """Khoảng cách từ giá vào tới cắt lỗ ban đầu, % giá vào.

    ÂM khi giá khớp đã nằm DƯỚI cắt lỗ (gap xuống lúc mở cửa phiên khớp) —
    giữ nguyên dấu để người đọc thấy, không kẹp về 0.
    """
    if not gia_vao or sl_ban_dau is None:
        return None
    return (gia_vao - sl_ban_dau) / gia_vao * 100.0


def ket_qua_R(loi_nhuan_rong_pct: Optional[float],
              rui_ro: Optional[float]) -> Optional[float]:
    """Lợi nhuận ròng chia rủi ro ban đầu. Không có rủi ro dương thì KHÔNG có R.

    Trả None thay vì một con số khi rủi ro ≤ 0: chia cho một khoảng cách âm
    đảo dấu kết quả, và một R bịa ra đọc y hệt một R thật.
    """
    if loi_nhuan_rong_pct is None or rui_ro is None or rui_ro <= 0:
        return None
    return loi_nhuan_rong_pct / rui_ro


def _diem(components: Any) -> dict[str, float]:
    if isinstance(components, str):
        components = json.loads(components) if components.strip() else {}
    return {k: float(v) for k, v in (components or {}).items()
            if k.endswith("_score") and isinstance(v, (int, float))
            and not isinstance(v, bool)}


def _xep_hang_agent(diem: dict[str, float]) -> Optional[str]:
    d = {k: v for k, v in diem.items() if k not in KHOA_KHONG_XEP_HANG}
    if len(d) < 2:
        return None
    cao = max(d, key=lambda k: (d[k], k))
    thap = min(d, key=lambda k: (d[k], k))
    ten = lambda k: k[:-len("_score")]  # noqa: E731
    return (f"agent cao nhất lúc vào: {ten(cao)} {d[cao]:g} · "
            f"thấp nhất: {ten(thap)} {d[thap]:g}")


def hau_kiem_may(*, sl_ban_dau: float, exit_price: float, exit_reason: str,
                 loi_nhuan_rong_pct: float, R: Optional[float],
                 alpha: Optional[float], diem: dict[str, float]) -> list[str]:
    """Nhãn máy cho MỘT lệnh đã đóng. Tất định: cùng đầu vào, cùng nhãn."""
    nhan = []
    lnr = loi_nhuan_rong_pct
    nhan.append("THẮNG" if lnr > 0 else "THUA" if lnr < 0 else "HOÀ")
    if alpha is None:
        nhan.append("chưa có rổ chuẩn cho cặp ngày này — không nói được vượt hay thua rổ")
    else:
        nhan.append(f"{'vượt' if alpha > 0 else 'thua'} rổ {alpha:+.2f} điểm")
    if exit_price < sl_ban_dau:
        duoi = (sl_ban_dau - exit_price) / sl_ban_dau * 100.0
        nhan.append(f"thoát DƯỚI cắt lỗ ban đầu {duoi:.2f}% — gap/trượt giá "
                    "(bất biến 3: gap qua SL khớp ở giá mở cửa)")
    elif exit_reason == ExitReason.STOP_LOSS and exit_price > sl_ban_dau:
        nhan.append("thoát bằng cắt lỗ ĐÃ NÂNG (trailing) — cao hơn cắt lỗ ban đầu")
    if R is not None and R < -1.0:
        nhan.append(f"lỗ {R:.2f}R — vượt mức rủi ro dự kiến 1R")
    xh = _xep_hang_agent(diem)
    if xh:
        nhan.append(xh)
    return nhan


def dong_vao_lenh(trade: Trade, components: Any, reasons: Any,
                  boi_canh: dict) -> dict:
    """Dòng nhật ký lúc VÀO. Gọi đúng lúc khớp — TRƯỚC mọi lần nâng stop."""
    if trade.entry_price is None or not trade.entry_date:
        raise ValueError(f"lệnh {trade.id} chưa khớp — chưa có giá vào để ghi nhật ký")
    if trade.status not in (Status.OPEN,):
        raise ValueError(f"lệnh {trade.id} ở trạng thái {trade.status}, nhật ký VÀO "
                         "chỉ ghi lúc vừa khớp (OPEN) — sau đó stop_loss có thể đã bị nâng")
    ly_do = reasons if isinstance(reasons, str) else json.dumps(reasons, ensure_ascii=False)
    dong = {c: None for c in COT_NHAT_KY}
    dong.update({
        "trade_id": trade.id, "symbol": trade.symbol,
        "signal_date": str(trade.signal_date)[:10],
        "entry_date": str(trade.entry_date)[:10],
        "entry_price": trade.entry_price,
        "stop_loss_ban_dau": trade.stop_loss,
        "rui_ro_pct": rui_ro_pct(trade.entry_price, trade.stop_loss),
        "entry_score": trade.entry_score,
        "diem_agent": json.dumps(_diem(components), ensure_ascii=False, sort_keys=True),
        "ly_do": ly_do,
        "boi_canh": json.dumps(boi_canh, ensure_ascii=False, sort_keys=True),
    })
    return dong


def dong_dong_lenh(dong: dict, trade: Trade,
                   ro_chuan_pct: Optional[float]) -> dict:
    """Điền nửa ĐÓNG vào một dòng VÀO. Không đổi nửa VÀO."""
    if trade.id != dong["trade_id"]:
        raise ValueError(f"dòng nhật ký của lệnh {dong['trade_id']}, lệnh đưa vào là {trade.id}")
    if trade.status != Status.CLOSED or trade.exit_price is None:
        raise ValueError(f"lệnh {trade.id} chưa đóng")
    lnr = trade.net_return_pct()
    R = ket_qua_R(lnr, dong["rui_ro_pct"])
    alpha = None if ro_chuan_pct is None else lnr - ro_chuan_pct
    moi = dict(dong)
    moi.update({
        "exit_date": str(trade.exit_date)[:10],
        "exit_price": trade.exit_price,
        "exit_reason": trade.exit_reason,
        "loi_nhuan_rong_pct": lnr,
        "ket_qua_R": R,
        "ro_chuan_pct": ro_chuan_pct,
        "alpha_pct": alpha,
        "hau_kiem_may": " | ".join(hau_kiem_may(
            sl_ban_dau=dong["stop_loss_ban_dau"], exit_price=trade.exit_price,
            exit_reason=trade.exit_reason or "", loi_nhuan_rong_pct=lnr, R=R,
            alpha=alpha, diem=json.loads(dong["diem_agent"] or "{}"))),
    })
    return moi
