"""Chỉnh THANG GIÁ của lệnh CHỜ KHỚP (`PENDING`) khi sự kiện quyền rơi giữa lúc có tín hiệu và lúc khớp (BƯỚC 282).

VÌ SAO CÓ FILE NÀY
──────────────────
`chinh_thang_gia.py` (BƯỚC 272/276) chỉnh lệnh ĐANG MỞ bằng hệ số f = `entry_price` ÷ giá MỞ của nguồn ở nến
vào. Lệnh `PENDING` chưa có `entry_price` nên bộ ấy bỏ qua nó (`chinh_thang_gia.TRANG_THAI_CHINH`; ĐO 35 khai
PENDING ngoài phạm vi). Nhưng `fill_pending` chạy BÊN TRONG `run_session`, SAU lời gọi bộ chỉnh, và khớp lệnh
chờ ở giá MỞ của nến đầu tiên sau ngày tín hiệu. Nếu nến ấy là ngày giao dịch không hưởng quyền (nguồn điều
chỉnh lùi cả lịch sử): giá khớp đúng (thang mới) nhưng `stop_loss` · `take_profit` của lệnh còn ở thang CŨ lúc
quét ngày T, cao hơn giá mới. Phiên kế tiếp `low <= stop_loss` đúng ngay: một cú cắt lỗ GIẢ sau một phiên. Nhãn
`su_kien_quyen` KHÔNG thấy nó (f_vào ≈ 1 nên `SACH`), nên lệnh ở lại mẫu của điều kiện dừng C5 và bộ nhớ học.
Trường hợp mẫu: `vibe_logs_282/vi_du_hong_282.py`.

PHÉP ĐO
───────
Lệnh chờ không có giá vào, nhưng kế hoạch vào lệnh (`ke_hoach`, BƯỚC 195) ghi `gia_dong` = giá đóng cửa ngày
tín hiệu ở THANG LÚC QUÉT (VNĐ). Hệ số: f = `ke_hoach.gia_dong(mã, ngày tín hiệu)` ÷ (giá đóng cửa ngày ấy trong
khung giá HÔM NAY × `price_multiplier`). Cùng một phiên đóng cửa đo ở hai thang nên không có chuyện "khớp giữa
phiên" như ở f của lệnh mở: chỉ cần ngưỡng `NGUONG_LECH` (DÙNG LẠI từ `chinh_thang_gia`, không khai lại).

KHI f > 1 + `NGUONG_LECH` (so `>` chặt): chia `stop_loss` · `take_profit` của lệnh cho f, ghi một mục vào
`nhat_ky.boi_canh` (cùng khoá `dieu_chinh_thang` với lệnh mở, mục mang `loai = "lenh_cho"`), trong MỘT
`SAVEPOINT` cùng dòng nhật ký. Mục ấy vừa là nhật ký vừa là DẤU chống chia hai lần: `ke_hoach.gia_dong` còn ở
thang cũ nên lượt quét kế vẫn đo ra f cũ; thấy dấu của cùng ngày tín hiệu thì im lặng bỏ qua. Lệnh chờ KHÔNG có
dòng nhật ký (hoặc `boi_canh` hỏng) thì KHÔNG chỉnh — không có chỗ ghi dấu thì không được chỉnh.

KHÔNG LÀM (mọi thứ dưới đây giữ nguyên hành vi cũ)
 · không có dòng `ke_hoach` / thiếu giá / khung giá không có nến ngày tín hiệu / nguồn CAO hơn sổ
   (f < 1/(1+`NGUONG_LECH`)): để NGUYÊN lệnh, in dòng `##[warning]` (không mã thoát);
 · không HUỶ lệnh và không đổi lệnh theo "giá mở gap xuống" hay "cắt lỗ ≥ giá khớp": hai thứ ấy bắt cả cú gap
   THẬT, huỷ chúng làm số đẹp lên (Quy tắc 1);
 · không chạm lệnh OPEN · CLOSING · đã đóng (đó là việc của `chinh_thang_gia`), `entry_price`, `size_pct`,
   `decisions`, `ke_hoach`, điểm, ngưỡng mua, mô hình khớp.
Hạn chế khai thẳng: nguồn CHƯA điều chỉnh sau sự kiện thì f = 1 và lệnh vẫn bị cắt lỗ giả (cùng lỗ hổng với lệnh
mở: `chinh_thang_gia.may_do_chua_dieu_chinh` chỉ BÁO). Cổ tức tiền dưới 5% sót có chủ ý.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from chinh_thang_gia import KHOA_NHAT_KY, NGUONG_LECH, _chia, _la_so, _ngay
from data_quality import price_multiplier
from paper_trading import Status

#: Giá trị của `loai` trong mục nhật ký (lệnh mở không có khoá này).
LOAI_LENH_CHO = "lenh_cho"

#: Bốn trạng thái của phép đo f ở MỘT lệnh chờ (tên khớp `chinh_thang_gia` ở chỗ cùng nghĩa).
CHINH = "CHINH"
BINH_THUONG = "BINH_THUONG"
NGUON_CAO_HON = "NGUON_CAO_HON"
KHONG_DO_DUOC = "KHONG_DO_DUOC"
#: Đã chỉnh ở một lượt trước (dấu trong `boi_canh`): im lặng bỏ qua.
DA_CHINH = "DA_CHINH"


def gia_dong_ngay(df: Any, ngay: str, he_so: float) -> Optional[float]:
    """Giá đóng cửa ngày `ngay` của khung giá (VNĐ), hoặc None. Ngày trùng giữ dòng cuối."""
    if df is None or len(df) == 0 or not ngay:
        return None
    ra = None
    for d, c in zip(df["time"], df["close"]):
        if _ngay(d) == ngay and _la_so(c):
            ra = float(c) * he_so
    return ra


def do_he_so_lenh_cho(gia_dong_tin_hieu: Any, ngay_tin_hieu: Any, df: Any,
                      he_so_gia: float) -> dict:
    """Đo f cho MỘT lệnh chờ. HÀM THUẦN. Trả {"trang_thai", "f", "ly_do"}.

    `gia_dong_tin_hieu` = `ke_hoach.gia_dong` (VNĐ, thang lúc quét); `df` = khung giá của lượt quét hôm nay
    (nghìn đồng, đã bỏ nến dở); `he_so_gia` = `price_multiplier(df)`.
    """
    ngay = _ngay(ngay_tin_hieu)
    if not _la_so(gia_dong_tin_hieu) or not ngay:
        return {"trang_thai": KHONG_DO_DUOC, "f": None,
                "ly_do": "không có giá đóng cửa ngày tín hiệu trong kế hoạch vào lệnh (ke_hoach.gia_dong)"}
    nay = gia_dong_ngay(df, ngay, he_so_gia)
    if nay is None:
        return {"trang_thai": KHONG_DO_DUOC, "f": None,
                "ly_do": f"khung giá hôm nay không có nến hợp lệ ngày tín hiệu {ngay}"}
    f = float(gia_dong_tin_hieu) / nay
    if float(gia_dong_tin_hieu) * (1 + NGUONG_LECH) < nay:
        return {"trang_thai": NGUON_CAO_HON, "f": f,
                "ly_do": (f"f = {f:.4f} < 1/(1+{NGUONG_LECH:.0%}): nguồn CAO hơn sổ — "
                          "không phải dạng sự kiện quyền")}
    if not float(gia_dong_tin_hieu) > (1 + NGUONG_LECH) * nay:
        return {"trang_thai": BINH_THUONG, "f": f, "ly_do": ""}
    return {"trang_thai": CHINH, "f": f, "ly_do": ""}


def _doc_boi_canh(db, trade_id: Any) -> tuple[bool, dict]:
    """(có dòng nhật ký, boi_canh dạng dict). Dòng không có -> (False, {}). `boi_canh` hỏng thì NỔ."""
    r = db.execute("SELECT boi_canh FROM nhat_ky WHERE trade_id=?", (trade_id,)).fetchone()
    if r is None:
        return False, {}
    tho = r["boi_canh"]
    if tho is None or (isinstance(tho, str) and not tho.strip()):
        return True, {}
    bc = json.loads(tho)
    if not isinstance(bc, dict):
        raise ValueError(f"nhat_ky.boi_canh của lệnh {trade_id} không phải JSON object")
    lan = bc.get(KHOA_NHAT_KY)
    if lan is not None and not isinstance(lan, list):
        raise ValueError(f"nhat_ky.boi_canh.{KHOA_NHAT_KY} của lệnh {trade_id} không phải danh sách")
    return True, bc


def _da_chinh(bc: dict, ngay_tin_hieu: str) -> bool:
    return any(isinstance(m, dict) and m.get("loai") == LOAI_LENH_CHO
               and m.get("ngay_tin_hieu") == ngay_tin_hieu for m in (bc.get(KHOA_NHAT_KY) or []))


def _ap_dung(db, row: Any, bc: dict, f: float, ngay_quet: str, ngay_tin_hieu: str, nguon: str) -> dict:
    """Ghi `trades` (stop_loss, take_profit) + `nhat_ky.boi_canh` trong MỘT giao dịch (SAVEPOINT): lỗi giữa
    chừng thì lệnh giữ NGUYÊN thang cũ. Ném lại lỗi sau khi hoàn tác."""
    moi = {"stop_loss": _chia(row["stop_loss"], f), "take_profit": _chia(row["take_profit"], f)}
    lan = list(bc.get(KHOA_NHAT_KY) or [])
    lan.append({"loai": LOAI_LENH_CHO, "ngay_quet": ngay_quet, "f": f,
                "ngay_tin_hieu": ngay_tin_hieu, "nguon": nguon})
    bc = dict(bc, **{KHOA_NHAT_KY: lan})
    db.execute("SAVEPOINT chinh_lenh_cho")
    try:
        db.execute("UPDATE trades SET stop_loss=?, take_profit=? WHERE id=? AND status=?",
                   (moi["stop_loss"], moi["take_profit"], row["id"], Status.PENDING))
        db.execute("UPDATE nhat_ky SET boi_canh=? WHERE trade_id=?",
                   (json.dumps(bc, ensure_ascii=False, sort_keys=True), row["id"]))
    except BaseException:
        db.execute("ROLLBACK TO chinh_lenh_cho")
        db.execute("RELEASE chinh_lenh_cho")
        raise
    db.execute("RELEASE chinh_lenh_cho")
    db.commit()
    return moi


def chinh_lenh_cho_mot_ma(journal, ma: str, df: Any, ngay_quet: str, *,
                          nguon: str = "?", ghi: Callable[[str], None] = print) -> list[dict]:
    """Chỉnh thang cho các lệnh CHỜ KHỚP của MỘT mã, trên khung giá `df` (thô, nghìn đồng) mà lượt quét vừa
    tải. Trả danh sách sự kiện (mỗi lệnh một dict). Gọi SAU `chinh_thang_mot_ma` và TRƯỚC `run_session`.

    Mọi trường hợp không chỉnh được: lệnh GIỮ NGUYÊN, in `##[warning]`, KHÔNG ném lỗi vì thiếu dữ liệu.
    """
    db = journal.db
    rows = db.execute("SELECT * FROM trades WHERE symbol=? AND status=? ORDER BY id",
                      (ma, Status.PENDING)).fetchall()
    if not rows:
        return []
    he_so = price_multiplier(df) if df is not None and len(df) else 1
    ra: list[dict] = []
    for r in rows:
        ngay_tin = _ngay(r["signal_date"])
        kh = db.execute("SELECT gia_dong FROM ke_hoach WHERE symbol=? AND substr(signal_date, 1, 10)=?"
                        " ORDER BY seq DESC LIMIT 1", (ma, ngay_tin)).fetchone()
        kq = do_he_so_lenh_cho(None if kh is None else kh["gia_dong"], ngay_tin, df, he_so)
        sk = {"id": r["id"], "ma": ma, "trang_thai": kq["trang_thai"], "f": kq["f"],
              "ngay_tin_hieu": ngay_tin, "ly_do": kq["ly_do"], "canh_bao": [], "loi": ""}
        if kq["trang_thai"] in (KHONG_DO_DUOC, NGUON_CAO_HON):
            msg = f"##[warning]chỉnh lệnh chờ {ma} #{r['id']}: không chỉnh — {kq['ly_do']}"
            sk["canh_bao"].append(msg)
            ghi(msg)
        elif kq["trang_thai"] == CHINH:
            try:
                co_dong, bc = _doc_boi_canh(db, r["id"])
                if not co_dong:
                    sk["trang_thai"] = KHONG_DO_DUOC
                    sk["ly_do"] = "lệnh chờ không có dòng nhật ký để ghi dấu chỉnh (chống chia hai lần)"
                    msg = f"##[warning]chỉnh lệnh chờ {ma} #{r['id']}: không chỉnh — {sk['ly_do']}"
                    sk["canh_bao"].append(msg)
                    ghi(msg)
                elif _da_chinh(bc, ngay_tin):
                    sk["trang_thai"] = DA_CHINH
                else:
                    moi = _ap_dung(db, r, bc, kq["f"], _ngay(ngay_quet), ngay_tin, nguon)
                    sk["gia_cu"] = {"stop_loss": r["stop_loss"], "take_profit": r["take_profit"]}
                    sk["gia_moi"] = moi
                    ghi(f"🔧 chỉnh lệnh chờ {ma} #{r['id']}: f = {kq['f']:.4f} (tín hiệu {ngay_tin}, "
                        f"nguồn {nguon}) · cắt lỗ {r['stop_loss']:,.1f} → {moi['stop_loss']:,.1f}")
            except Exception as e:
                sk["loi"] = f"{type(e).__name__}: {e}"
                msg = (f"##[warning]chỉnh lệnh chờ {ma} #{r['id']}: GHI HỎNG, đã hoàn tác, "
                       f"lệnh giữ thang cũ — {sk['loi']}")
                sk["canh_bao"].append(msg)
                ghi(msg)
        ra.append(sk)
    return ra
