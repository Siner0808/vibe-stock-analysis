"""Phần CHẠY của B1 — viết hậu kiểm bằng lời cho lệnh ảo đã đóng (BƯỚC 204).

    python tools/hau_kiem_loi.py          # gọi API, THÊM dòng vào tab `hau_kiem`
    python tools/hau_kiem_loi.py --thu    # in lời dặn + dữ kiện từng lệnh, KHÔNG gọi API

Phần thuần (luật viết, máy kiểm, dữ kiện, tiền, tham số lời gọi) ở module gốc
`hau_kiem_loi.py`; đặc tả `docs/thiet-ke-b1-hau-kiem-loi.md`. File này là chỗ DUY NHẤT
nhập SDK của model (`google.genai`, từ BƯỚC 229; trước đó `anthropic`), và nhập TRONG hàm
(gác `tests/test_requirements.py`). Workflow `hau-kiem-loi.yml` chạy nó; khoá
`GEMINI_API_KEY` chỉ có ở job ấy.

MÃ THOÁT — ba nấc
  0  xong — kể cả khi có lệnh hỏng (đã `::warning::`, lượt sau làm lại), chạm trần tiền
     hay hết hạn mức của Gemini (429: dừng lượt, lượt sau làm)
  1  lỗi cấu hình hoặc yêu cầu sai hình dạng (400 · 401 · 403 · 404): mọi lệnh sẽ hỏng
     như nhau, nên job phải ĐỎ để người dùng nhận email
  2  không chạy được: thiếu khoá, kho ngoài chưa cấu hình, không đọc/ghi được Sheets

CHỈ THÊM vào tab `hau_kiem`; không đọc hay ghi sổ SQLite nào, không đổi tab khác. Mọi
phản hồi có `usage` thành một dòng (kể cả bị bác) để tổng tiền cộng từ tab luôn đủ; ghi
tab hỏng SAU khi đã gọi API thì dừng ngay (tiền đã tiêu mà sổ không thấy).
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
# `tools/` có file cùng tên với module gốc `hau_kiem_loi.py` (như `ban_tin`): đặt GOC
# SAU CÙNG để nó đứng TRƯỚC `tools/` và `import hau_kiem_loi` ra module thuần.
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import hau_kiem_loi as hk  # noqa: E402

MA_XONG = 0
MA_CAU_HINH = 1
MA_KHONG_CHAY = 2

#: Mốc đầu tải giá lùi ít nhất ngần này ngày lịch: cổng kiểm định dữ liệu chặn bảng
#: ngắn hơn `data_quality.SO_PHIEN_TOI_THIEU` phiên — đúng bẫy BƯỚC 168 của nút app.
NGAY_GIA_LUI = 120


#: Mã HTTP mà lượt sau KHÔNG tự hết: yêu cầu sai hình dạng, khoá sai, không có quyền,
#: không có model ấy.
MA_HTTP_CAU_HINH = frozenset({400, 401, 403, 404})
#: Hết hạn mức (kể cả hạn mức NGÀY của bậc miễn phí): các lệnh sau cũng sẽ 429 -> dừng lượt.
MA_HTTP_HET_HAN_MUC = 429
#: SDK `google-genai` mặc định KHÔNG thử lại (`retry_args(None)`, đọc mã 2.33.0) — đặt
#: tường minh, gồm cả lần đầu; nó thử lại 408 · 429 · 5xx. MỖI lần thử ăn một request của
#: hạn mức ngày (bậc miễn phí: 20 request/ngày/model — lỗi 429 thật của lượt đo 2) nên chỉ
#: thử lại MỘT lần: lượt đo 2 mất 3 request mỗi lệnh hỏng vì 503/504 khi model quá tải.
SO_LAN_THU = 2
#: Hạn chờ MỖI request (mili giây, đơn vị của `HttpOptions.timeout`). Không đặt thì một lời
#: gọi treo giữ job tới trần của workflow: lượt đo 1 (run 40256929934, 26/10/2026) viết 4
#: lệnh rồi treo ~18 phút và bị GitHub huỷ ở `timeout-minutes`. 90 giây thì quá ngắn: lượt
#: đo 2 (run 40258909497) nhận 504 DEADLINE_EXCEEDED ở hai lệnh khi model quá tải.
THOI_GIAN_CHO_MS = 180_000
#: Hạn của cả lượt gọi (giây): quá thì KHÔNG mở lời gọi mới, dừng xanh, lượt sau làm. Cộng
#: một lời gọi tệ nhất (`SO_LAN_THU` × `THOI_GIAN_CHO_MS`) vẫn phải nằm trong `timeout-minutes`
#: của job (gác `tests/test_tools_hau_kiem_loi.py`).
HAN_LUOT_GIAY = 10 * 60
#: SDK gọi HTTP bằng `httpx`: lỗi mạng còn lại sau các lần thử mang module ấy. Nhận ra bằng
#: TÊN module để phần chạy không phải nhập `httpx` (gói không khai trong requirements).
GOI_LOI_MANG = frozenset({"httpx", "httpcore"})

LOI_CAU_HINH = "cau_hinh"
LOI_HET_HAN_MUC = "het_han_muc"
LOI_TAM = "tam"


def _loai_loi(e: BaseException, loi_mod) -> str | None:
    """Phân loại một lỗi khi gọi model; None = lỗi lạ (lỗi mã), để nó nổ ra ngoài."""
    if isinstance(e, loi_mod.APIError):
        ma = getattr(e, "code", None)
        if ma in MA_HTTP_CAU_HINH:
            return LOI_CAU_HINH
        return LOI_HET_HAN_MUC if ma == MA_HTTP_HET_HAN_MUC else LOI_TAM
    if type(e).__module__.split(".")[0] in GOI_LOI_MANG:
        return LOI_TAM
    return None


def _tai_gia_that(tu: str, den: str):
    """Bộ tải giá của phần chạy: cùng bộ thu `VNStockCollectorAgent` (kèm kiểm định) mà
    app dùng; vòng lặp gom giá là `so_bai_hoc.gia_tu_bo_tai`, dùng chung với app."""
    import san_giao_dich
    from data_collectors import VNStockCollectorAgent

    agent = VNStockCollectorAgent()

    def tai(ma: str):
        try:
            res = agent.collect(ma, tu, den, exchange=san_giao_dich.san_cua(ma))
        except Exception:
            return None, "FAILED"
        return res.get("df"), res.get("status")

    return tai


def _tom_tat(dem: Counter, da_tieu: float, thang: str, ghi=print) -> None:
    dong = (f"Hậu kiểm lời: {sum(dem.values())} lời gọi · "
            + " · ".join(f"{k} {v}" for k, v in sorted(dem.items()))
            + f" · đã tiêu (ước dư) tháng {thang}: {da_tieu:.4f} / {hk.TRAN_USD_THANG} USD")
    ghi(dong)
    tep = os.environ.get("GITHUB_STEP_SUMMARY")
    if tep:
        with open(tep, "a", encoding="utf-8") as f:
            print(f"### Hậu kiểm bằng lời (B1)\n\n{dong}", file=f)


def _doi_so(argv) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--thu", action="store_true",
                   help="in lời dặn + dữ kiện từng lệnh, không gọi API, không ghi gì")
    return p.parse_args(argv)


def main(argv=None, *, backend=None, client=None, loi_mod=None, tai_gia=None,
         bay_gio=None, dong_ho=time.monotonic) -> int:
    a = _doi_so(argv)
    import sheets_store
    import so_bai_hoc
    from data_quality import now_vn

    bay_gio = now_vn() if bay_gio is None else bay_gio
    hom_nay = bay_gio.strftime("%Y-%m-%d")
    thang = hom_nay[:7]
    try:
        if backend is None:
            backend = sheets_store.open_from_secrets()
        if backend is None:
            print("::error::Hậu kiểm lời: kho ngoài (Google Sheets) chưa cấu hình — "
                  "không đọc được sổ.")
            return MA_KHONG_CHAY
        nk = sheets_store.doc_nhat_ky(backend)
        hkd = sheets_store.doc_hau_kiem(backend)
    except Exception as e:
        print(f"::error::Hậu kiểm lời: không đọc được Sheets — {type(e).__name__}: {e}")
        return MA_KHONG_CHAY

    can, het = hk.can_viet(nk, hkd)
    for d in het:
        print(f"::warning::Hậu kiểm lời: lệnh #{d['trade_id']} {d['symbol']} đã hỏng "
              f"{hk.SO_LAN_TOI_DA} lần — dừng, chờ người xem tab hau_kiem.")
    luot = can[:hk.SO_LENH_MOI_LUOT]
    if len(can) > len(luot):
        print(f"::notice::Hậu kiểm lời: {len(can) - len(luot)} lệnh để lượt sau "
              f"(trần {hk.SO_LENH_MOI_LUOT} lệnh mỗi lượt).")
    if not luot:
        print("Hậu kiểm lời: không có lệnh nào cần viết.")
        _tom_tat(Counter(), hk.da_tieu_thang(hkd, thang), thang)
        return MA_XONG

    tu_lui = (bay_gio - datetime.timedelta(days=NGAY_GIA_LUI)).strftime("%Y-%m-%d")
    tu = so_bai_hoc.tu_ngay_tai_gia(luot, tu_lui)
    tai = _tai_gia_that(tu, hom_nay) if tai_gia is None else tai_gia
    gia, thieu = so_bai_hoc.gia_tu_bo_tai(so_bai_hoc.ma_can_gia(luot), tai)
    if thieu:
        print(f"⚠️ Không tải được giá {len(thieu)} mã ({', '.join(thieu)}): phần ngành và "
              "cắt lỗ sát của bài học nói \"chưa đủ dữ liệu\".")
    bai_hoc = {b["trade_id"]: b for b in so_bai_hoc.bai_hoc_cho_so(luot, gia)["bai_hoc"]}

    if a.thu:
        print("=== LỜI DẶN (system) ===")
        print(hk.LOI_DAN)
        for d in luot:
            print(f"=== Lệnh #{d['trade_id']} {d['symbol']} · ra {d['exit_date']} ===")
            print(hk.noi_dung_gui(hk.du_kien(d, bai_hoc[d["trade_id"]])))
        return MA_XONG

    if client is None:
        khoa = os.environ.get("GEMINI_API_KEY")
        if not khoa:
            print("::error::Hậu kiểm lời: thiếu GEMINI_API_KEY — người dùng tự đặt secret "
                  "(BƯỚC 229).")
            return MA_KHONG_CHAY
        from google import genai
        from google.genai import errors, types

        loi_mod = errors
        client = genai.Client(api_key=khoa, http_options=types.HttpOptions(
            timeout=THOI_GIAN_CHO_MS,
            retry_options=types.HttpRetryOptions(attempts=SO_LAN_THU)))

    moi: list[dict] = []
    dem: Counter = Counter()
    bat_dau = dong_ho()
    for i, d in enumerate(luot):
        if dong_ho() - bat_dau > HAN_LUOT_GIAY:
            print(f"::warning::Hậu kiểm lời: hết {HAN_LUOT_GIAY // 60} phút của lượt — dừng, "
                  f"còn {len(luot) - i} lệnh chưa viết; lượt sau làm.")
            break
        dk = hk.du_kien(d, bai_hoc[d["trade_id"]])
        nd = hk.noi_dung_gui(dk)
        if hk.vuot_tran(hk.da_tieu_thang(hkd + moi, thang), hk.tran_mot_loi_goi(nd)):
            print(f"::warning::Hậu kiểm lời: chạm trần {hk.TRAN_USD_THANG} USD tháng {thang} "
                  f"— dừng lượt, còn {len(luot) - i} lệnh chưa viết.")
            break
        try:
            resp = client.models.generate_content(**hk.tham_so_goi(nd))
        except Exception as e:
            loai = _loai_loi(e, loi_mod)
            if loai is None:
                raise
            if loai == LOI_CAU_HINH:
                print(f"::error::Hậu kiểm lời: lỗi cấu hình hoặc yêu cầu — "
                      f"{type(e).__name__}: {e}")
                _tom_tat(dem, hk.da_tieu_thang(hkd + moi, thang), thang)
                return MA_CAU_HINH
            if loai == LOI_HET_HAN_MUC:
                print(f"::warning::Hậu kiểm lời: hết hạn mức của Gemini — dừng lượt, còn "
                      f"{len(luot) - i} lệnh chưa viết; lượt sau làm. {type(e).__name__}: {e}")
                break
            print(f"::warning::Hậu kiểm lời: lệnh #{d['trade_id']} {d['symbol']} — "
                  f"{type(e).__name__}: {e}; lượt sau làm lại.")
            continue
        dong = hk.ket_qua_mot_lenh(d, hk.lan_ke(hkd + moi, d["trade_id"]), resp, dk,
                                   bay_gio.isoformat(timespec="seconds"))
        try:
            sheets_store.them_hau_kiem(backend, [dong])
        except Exception as e:
            print(f"::error::Hậu kiểm lời: đã gọi API cho lệnh #{d['trade_id']} nhưng KHÔNG "
                  f"ghi được tab hau_kiem — {type(e).__name__}: {e}. Dừng: tiền đã tiêu mà "
                  "sổ không thấy.")
            return MA_KHONG_CHAY
        moi.append(dong)
        dem[dong["trang_thai"]] += 1
        if dong["trang_thai"] != hk.TT_DAT:
            print(f"::warning::Hậu kiểm lời: lệnh #{d['trade_id']} {d['symbol']} lần "
                  f"{dong['lan']} — {dong['trang_thai']}: {dong['ly_do_bac']}")
    _tom_tat(dem, hk.da_tieu_thang(hkd + moi, thang), thang)
    return MA_XONG


if __name__ == "__main__":
    sys.exit(main())
