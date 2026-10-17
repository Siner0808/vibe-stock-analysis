"""Phần CHẠY của B1 — viết hậu kiểm bằng lời cho lệnh ảo đã đóng (BƯỚC 204).

    python tools/hau_kiem_loi.py          # gọi API, THÊM dòng vào tab `hau_kiem`
    python tools/hau_kiem_loi.py --thu    # in lời dặn + dữ kiện từng lệnh, KHÔNG gọi API

Phần thuần (luật viết, máy kiểm, dữ kiện, tiền, tham số lời gọi) ở module gốc
`hau_kiem_loi.py`; đặc tả `docs/thiet-ke-b1-hau-kiem-loi.md`. File này là chỗ DUY NHẤT
nhập `anthropic`, và nhập TRONG hàm (gác `tests/test_requirements.py`). Workflow
`hau-kiem-loi.yml` chạy nó; khoá `ANTHROPIC_API_KEY` chỉ có ở job ấy.

MÃ THOÁT — ba nấc
  0  xong — kể cả khi có lệnh hỏng (đã `::warning::`, lượt sau làm lại) hay chạm trần
  1  lỗi cấu hình hoặc yêu cầu sai hình dạng (401 · 403 · 400): mọi lệnh sẽ hỏng như
     nhau, nên job phải ĐỎ để người dùng nhận email
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


def _loi_cau_hinh(mod) -> tuple:
    """Lỗi mà lượt sau KHÔNG tự hết: khoá sai, không có quyền, yêu cầu sai hình dạng."""
    return (mod.AuthenticationError, mod.PermissionDeniedError, mod.BadRequestError)


def _loi_tam(mod) -> tuple:
    """Lỗi tạm sau khi SDK đã tự thử lại (429 · 5xx · mạng): bỏ lệnh này, lượt sau làm."""
    return (mod.APIStatusError, mod.APIConnectionError)


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


def main(argv=None, *, backend=None, client=None, anthropic_mod=None, tai_gia=None,
         bay_gio=None) -> int:
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
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("::error::Hậu kiểm lời: thiếu ANTHROPIC_API_KEY — người dùng tự đặt "
                  "secret (Q9, docs/QUYET-DINH-CHO.md).")
            return MA_KHONG_CHAY
        import anthropic

        anthropic_mod = anthropic
        client = anthropic.Anthropic()

    moi: list[dict] = []
    dem: Counter = Counter()
    for i, d in enumerate(luot):
        dk = hk.du_kien(d, bai_hoc[d["trade_id"]])
        nd = hk.noi_dung_gui(dk)
        if hk.vuot_tran(hk.da_tieu_thang(hkd + moi, thang), hk.tran_mot_loi_goi(nd)):
            print(f"::warning::Hậu kiểm lời: chạm trần {hk.TRAN_USD_THANG} USD tháng {thang} "
                  f"— dừng lượt, còn {len(luot) - i} lệnh chưa viết.")
            break
        try:
            resp = client.beta.messages.create(**hk.tham_so_goi(nd))
        except _loi_cau_hinh(anthropic_mod) as e:
            print(f"::error::Hậu kiểm lời: lỗi cấu hình hoặc yêu cầu — {type(e).__name__}: {e}")
            _tom_tat(dem, hk.da_tieu_thang(hkd + moi, thang), thang)
            return MA_CAU_HINH
        except _loi_tam(anthropic_mod) as e:
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
