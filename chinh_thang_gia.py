"""Chỉnh THANG GIÁ của vị thế đang mở lúc xét (BƯỚC 272, ĐO 35 — `docs/TIEU-CHI-DOC-TRUOC.md`).

VÌ SAO CÓ FILE NÀY
──────────────────
Sổ lệnh lưu giá vào · cắt lỗ · chốt lời ở thang CHƯA điều chỉnh lúc khớp. Nguồn giá điều chỉnh
LÙI cả lịch sử sau một sự kiện quyền (thưởng · chia cổ phiếu · quyền mua), nên tới ngày giao
dịch không hưởng quyền, nến thang MỚI bị so với cắt lỗ thang CŨ và chạm cắt lỗ GIẢ
(`paper_trading._lenh_dat_san`: `low <= sl`). Ca đã thấy: #122 HDB (09/10/2026) và #128 TCB
(28/10/2026) — `docs/STATE.md` BƯỚC 269, 270.

MỖI LƯỢT QUÉT, với mỗi vị thế `OPEN`/`CLOSING` của mã vừa tải khung giá:

  f = `entry_price` ÷ giá MỞ của nguồn ở nến VÀO (`entry_date`) — nến DUY NHẤT sổ lưu một giá thật.

f vượt 1 quá `NGUONG_LECH` (5%, GHIM, dùng LẠI của `su_kien_quyen`, không dò) VÀ giá khớp nằm
NGOÀI thân nến vào (> giá CAO × (1 + `NOI_BIEN`): không thể là lệnh khớp giữa phiên) thì chia
`entry_price`, `stop_loss`, `take_profit` cho f, GHI NGƯỢC vào sổ trong MỘT giao dịch (kèm
`nhat_ky.entry_price`, `nhat_ky.stop_loss_ban_dau` và khoá `dieu_chinh_thang` của `boi_canh`).
Sau đó f' ≈ 1 ở lượt kế: không cần cờ nhớ, không chia hai lần (L5).

KHÔNG làm: dòng ĐÃ ĐÓNG (kể cả #122, #128) · `decisions` · `ke_hoach` · `hau_kiem` · lệnh `PENDING`
· cổ tức tiền dưới 5% (sót có chủ ý) · hoãn cắt lỗ khi nghi nguồn chưa điều chỉnh (chỉ BÁO) ·
đổi điểm, ngưỡng mua, mô hình khớp, logic cắt lỗ/trailing. Không dùng lịch sự kiện.

CHIỀU THIÊN LỆCH (Quy tắc 1): chỉnh thang chỉ có thể làm một lệnh LỖ GIẢ biến mất; nó không tạo
lệnh lãi mới. Mọi con số "đẹp lên" do phát lại là số của Quy tắc 1, không phải số đã sửa.

TRẠNG THÁI (BƯỚC 272): ĐƯỜNG THẬT TẮT. ĐO 35 kết cục K0 (đối chứng (i)/(ii) trượt) nên KHÔNG có nơi gọi nào
trong đường quét: chỉ `tools/do35_chinh_thang_gia.py` (phát lại) nhập file này. Bật đường thật (một lời gọi ở
`run_daily`, sau khi khung giá tải và TRƯỚC `run_session`) chỉ khi một ĐO kết cục A cho phép, và khi ấy sửa gác
`tests/test_chinh_thang_gia.py::test_duong_that_TAT_*` CÙNG LÚC, có chủ đích. Không có công tắc cờ: một cờ không
ai đọc là cấu hình chết; "tắt" ở đây là KHÔNG CÓ NGƯỜI GỌI, và gác AST canh đúng điều đó.
Walk-forward, backtest và `paper_trading`/`paper_runner` KHÔNG nhập file này.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Iterable, Mapping, Optional

import su_kien_quyen as skq
from data_quality import EXCHANGE_LIMITS, price_multiplier
from paper_trading import Status

#: GHIM — cùng hằng số với nhãn sự kiện quyền (BƯỚC 176), không dò lại.
NGUONG_LECH = skq.NGUONG_LECH
NOI_BIEN = skq.NOI_BIEN

#: Trạng thái được chỉnh. `PENDING` chưa có giá khớp để đo f (ngoài phạm vi, ĐO 35).
TRANG_THAI_CHINH = (Status.OPEN, Status.CLOSING)

#: Cột giá của bảng `trades` mà bộ chỉnh CHIA cho f.
COT_GIA_CHINH = ("entry_price", "stop_loss", "take_profit")
#: Cột giá chỉ được GHI lúc ra (lệnh đang mở chưa có): bộ chỉnh không cần chạm.
COT_GIA_CHI_GHI_LUC_RA = ("exit_price",)
#: Cột REAL không phải giá: tỷ trọng vốn không phụ thuộc thang; dấu thời gian.
COT_REAL_KHONG_PHAI_GIA = ("size_pct", "created_at")

#: Khoá của `nhat_ky.boi_canh`. Giá trị là DANH SÁCH các lần chỉnh (cộng dồn khi có sự kiện thứ hai).
KHOA_NHAT_KY = "dieu_chinh_thang"

#: Bốn trạng thái của phép đo f ở MỘT vị thế.
CHINH = "CHINH"                          # f vượt ngưỡng và giá khớp ngoài thân nến vào: chia
BINH_THUONG = "BINH_THUONG"              # 1/(1+N) ≤ f ≤ 1+N: im lặng
KHOP_GIUA_PHIEN = "KHOP_GIUA_PHIEN"      # f > 1+N nhưng giá khớp nằm trong thân nến (+NOI_BIEN): không chỉnh
NGUON_CAO_HON = "NGUON_CAO_HON"          # f < 1/(1+N): không phải dạng sự kiện quyền, báo
KHONG_DO_DUOC = "KHONG_DO_DUOC"          # thiếu nến vào / giá không hợp lệ: không làm gì, báo


def _la_so(x: Any) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and x == x and x > 0)


def _ngay(x: Any) -> str:
    return str(x or "")[:10]


def do_he_so(gia_vao: Any, ngay_vao: Any,
             nen: Mapping[str, skq.Nen]) -> dict:
    """Đo f ở nến VÀO. HÀM THUẦN. Trả {"trang_thai", "f", "ly_do"}.

    `nen` = {ngày: (mở, thấp, cao)} VNĐ của nguồn hôm nay (`su_kien_quyen.dung_nen`).
    Kích hoạt khi CẢ HAI cùng đúng (L2, viết dạng nhân, so `>` chặt — đúng 5,00% không kích hoạt):
      (a) `gia_vao` > (1 + NGUONG_LECH) × giá MỞ;
      (b) `gia_vao` > (1 + NOI_BIEN) × giá CAO.
    """
    ngay = _ngay(ngay_vao)
    if not _la_so(gia_vao) or not ngay:
        return {"trang_thai": KHONG_DO_DUOC, "f": None,
                "ly_do": "thiếu giá vào hoặc ngày vào của lệnh"}
    n = nen.get(ngay)
    if n is None or len(n) != 3 or not all(_la_so(v) for v in n):
        return {"trang_thai": KHONG_DO_DUOC, "f": None,
                "ly_do": f"khung giá không có nến hợp lệ ngày vào {ngay}"}
    mo, _thap, cao = n
    f = gia_vao / mo
    if gia_vao * (1 + NGUONG_LECH) < mo:
        return {"trang_thai": NGUON_CAO_HON, "f": f,
                "ly_do": (f"f = {f:.4f} < 1/(1+{NGUONG_LECH:.0%}): nguồn CAO hơn sổ — "
                          "không phải dạng sự kiện quyền")}
    if not gia_vao > (1 + NGUONG_LECH) * mo:
        return {"trang_thai": BINH_THUONG, "f": f, "ly_do": ""}
    if not gia_vao > (1 + NOI_BIEN) * cao:
        return {"trang_thai": KHOP_GIUA_PHIEN, "f": f,
                "ly_do": (f"f = {f:.4f} nhưng giá khớp không vượt giá CAO nến vào + "
                          f"{NOI_BIEN:.0%}: có thể là khớp giữa phiên, không chỉnh")}
    return {"trang_thai": CHINH, "f": f, "ly_do": ""}


def may_do_chua_dieu_chinh(df: Any, he_so: float, san: Any,
                           tu_ngay: str, den_ngay: Optional[str] = None
                           ) -> list[dict]:
    """Máy dò nguồn CHƯA điều chỉnh (L6) — CHỈ BÁO, không chỉnh, không hoãn cắt lỗ.

    Nến t (ngày ∈ [`tu_ngay`, `den_ngay`]) có `high` < đóng(t−1) × (1 − biên độ của sàn) ×
    (1 − NOI_BIEN): cú rơi không thể có nếu giá tham chiếu không bị điều chỉnh. Mù ở f ≲ 1,1
    (cú rơi nằm trong biên độ). `san` không có trong `EXCHANGE_LIMITS` thì không dò (không đoán).
    """
    bien = EXCHANGE_LIMITS.get(str(san).upper())
    if bien is None or df is None or len(df) < 2:
        return []
    thoi = [_ngay(x) for x in df["time"]]
    cao = list(df["high"])
    dong = list(df["close"])
    ra = []
    for i in range(1, len(df)):
        d = thoi[i]
        if d < tu_ngay or (den_ngay is not None and d > den_ngay):
            continue
        if not (_la_so(cao[i]) and _la_so(dong[i - 1])):
            continue
        nguong = float(dong[i - 1]) * he_so * (1 - bien) * (1 - NOI_BIEN)
        if float(cao[i]) * he_so < nguong:
            ra.append({"ngay": d, "cao": float(cao[i]) * he_so, "nguong": nguong,
                       "bien": bien})
    return ra


def _chia(x: Any, f: float) -> Any:
    return x / f if _la_so(x) else x


def _cap_nhat_trades(db, row: Mapping[str, Any], f: float) -> dict:
    moi = {c: _chia(row[c], f) for c in COT_GIA_CHINH}
    db.execute("UPDATE trades SET entry_price=?, stop_loss=?, take_profit=? WHERE id=?",
               (moi["entry_price"], moi["stop_loss"], moi["take_profit"], row["id"]))
    return moi


def _cap_nhat_nhat_ky(db, trade_id: Any, f: float, ngay_quet: str, ngay_vao: str,
                      nguon: str) -> bool:
    """Chia hai ô giá của dòng nhật ký (nếu có) và ghi khoá `dieu_chinh_thang` vào `boi_canh`.

    Dòng không có thì bỏ phần này (`trades` vẫn chỉnh). `boi_canh` không phải JSON object thì NỔ
    — bên gọi `rollback`, lệnh giữ thang cũ.
    """
    r = db.execute("SELECT entry_price, stop_loss_ban_dau, boi_canh FROM nhat_ky"
                   " WHERE trade_id=?", (trade_id,)).fetchone()
    if r is None:
        return False
    bc_tho = r["boi_canh"]
    if bc_tho is None or (isinstance(bc_tho, str) and not bc_tho.strip()):
        bc: dict = {}
    else:
        bc = json.loads(bc_tho)
        if not isinstance(bc, dict):
            raise ValueError(f"nhat_ky.boi_canh của lệnh {trade_id} không phải JSON object")
    lan = bc.get(KHOA_NHAT_KY)
    if lan is None:
        lan = []
    elif not isinstance(lan, list):
        raise ValueError(f"nhat_ky.boi_canh.{KHOA_NHAT_KY} của lệnh {trade_id} không phải danh sách")
    lan.append({"ngay_quet": ngay_quet, "f": f, "ngay_nen_vao": ngay_vao, "nguon": nguon})
    bc[KHOA_NHAT_KY] = lan
    db.execute("UPDATE nhat_ky SET entry_price=?, stop_loss_ban_dau=?, boi_canh=?"
               " WHERE trade_id=?",
               (_chia(r["entry_price"], f), _chia(r["stop_loss_ban_dau"], f),
                json.dumps(bc, ensure_ascii=False, sort_keys=True), trade_id))
    return True


def _ap_dung(db, row: Mapping[str, Any], f: float, ngay_quet: str, ngay_vao: str,
             nguon: str) -> dict:
    """Ghi `trades` + `nhat_ky` trong MỘT giao dịch (SAVEPOINT): lỗi giữa chừng thì lệnh giữ
    NGUYÊN thang cũ, không bao giờ nửa cũ nửa mới (L3). Ném lại lỗi sau khi hoàn tác."""
    db.execute("SAVEPOINT chinh_thang")
    try:
        moi = _cap_nhat_trades(db, row, f)
        co_nhat_ky = _cap_nhat_nhat_ky(db, row["id"], f, ngay_quet, ngay_vao, nguon)
    except BaseException:
        db.execute("ROLLBACK TO chinh_thang")
        db.execute("RELEASE chinh_thang")
        raise
    db.execute("RELEASE chinh_thang")
    db.commit()
    return {"gia_moi": moi, "co_nhat_ky": co_nhat_ky}


def chinh_thang_mot_ma(journal, ma: str, df: Any, ngay_quet: str, *,
                       nguon: str = "?", san: Any = None,
                       ghi: Callable[[str], None] = print,
                       nhan_f: float = 1.0) -> list[dict]:
    """Chỉnh thang cho các vị thế mở của MỘT mã, trên khung giá `df` (thô, nghìn đồng) mà lượt
    quét vừa tải. Trả danh sách sự kiện (mỗi vị thế một dict; vị thế BÌNH THƯỜNG cũng có dòng).

    Gọi SAU khi tải khung giá và TRƯỚC `evaluate_open`/`fill_closing` của mã ấy (L4).
    `nhan_f` CHỈ cho phép đo độ nhạy (C2: f × 0,98 · × 1,02); đường thật không truyền (gác AST).
    """
    db = journal.db
    cho = ",".join("?" * len(TRANG_THAI_CHINH))
    rows = db.execute(f"SELECT * FROM trades WHERE symbol=? AND status IN ({cho})"
                      " ORDER BY id", (ma, *TRANG_THAI_CHINH)).fetchall()
    if not rows:
        return []
    he_so = price_multiplier(df)
    nen = skq.dung_nen(df["time"], df["open"], df["low"], df["high"], he_so) \
        if df is not None and len(df) else {}
    ra: list[dict] = []
    for r in rows:
        ngay_vao = _ngay(r["entry_date"])
        kq = do_he_so(r["entry_price"], ngay_vao, nen)
        sk = {"id": r["id"], "ma": ma, "trang_thai": kq["trang_thai"], "f": kq["f"],
              "ngay_vao": ngay_vao, "ly_do": kq["ly_do"], "canh_bao": [], "loi": ""}
        if kq["trang_thai"] in (KHONG_DO_DUOC, NGUON_CAO_HON):
            msg = (f"##[warning]chỉnh thang giá {ma} #{r['id']}: không chỉnh — {kq['ly_do']}")
            sk["canh_bao"].append(msg)
            ghi(msg)
        elif kq["trang_thai"] == CHINH:
            f_dung = kq["f"] * nhan_f
            try:
                kqa = _ap_dung(db, r, f_dung, _ngay(ngay_quet), ngay_vao, nguon)
            except Exception as e:
                sk["loi"] = f"{type(e).__name__}: {e}"
                msg = (f"##[warning]chỉnh thang giá {ma} #{r['id']}: GHI HỎNG, đã hoàn tác, "
                       f"lệnh giữ thang cũ — {sk['loi']}")
                sk["canh_bao"].append(msg)
                ghi(msg)
            else:
                sk["gia_cu"] = {c: r[c] for c in COT_GIA_CHINH}
                sk["gia_moi"] = kqa["gia_moi"]
                sk["f_dung"] = f_dung
                ghi(f"🔧 chỉnh thang giá {ma} #{r['id']}: f = {kq['f']:.4f} (nến vào {ngay_vao}, "
                    f"nguồn {nguon}) · giá vào {r['entry_price']:,.1f} → "
                    f"{kqa['gia_moi']['entry_price']:,.1f} · cắt lỗ {r['stop_loss']:,.1f} → "
                    f"{kqa['gia_moi']['stop_loss']:,.1f}")
        ra.append(sk)
    if df is not None and len(df):
        ngay_cuoi = _ngay(df["time"].iloc[-1])
        for d in may_do_chua_dieu_chinh(df, he_so, san, ngay_cuoi):
            msg = (f"##[warning]{ma}: nghi nguồn chưa điều chỉnh sau sự kiện quyền — nến "
                   f"{d['ngay']} cao {d['cao']:,.0f} < đóng phiên trước × (1 − {d['bien']:.0%}) "
                   f"× (1 − {NOI_BIEN:.0%}) = {d['nguong']:,.0f}; không chỉnh, không hoãn cắt lỗ")
            ra[0]["canh_bao"].append(msg)
            ghi(msg)
    return ra


def cot_gia_chua_khai(cot_real: Iterable[str]) -> list[str]:
    """Cột REAL của DDL `trades` mà bộ chỉnh chưa khai là chia/chỉ-ghi-lúc-ra/không-phải-giá."""
    da_khai = set(COT_GIA_CHINH) | set(COT_GIA_CHI_GHI_LUC_RA) | set(COT_REAL_KHONG_PHAI_GIA)
    return sorted(c for c in cot_real if c not in da_khai)
