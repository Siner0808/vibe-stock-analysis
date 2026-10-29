"""Sinh BẢNG VÀNG của một phiên giao dịch giấy (BƯỚC 239, Lát 1 của C1).

Mục đích: chứng minh một lần tái cấu trúc `paper_trading` / `paper_runner.run_session`
KHÔNG đổi hành vi. Bảng vàng được sinh bằng mã TRƯỚC khi sửa; sau khi sửa, test
`tests/test_bang_vang_phien.py` chạy lại đúng kịch bản và đòi từng ô khớp.

LỆNH SINH (đã chạy trên `main` `09f7980`, trước mọi dòng sửa bộ máy):

    ./.venv/Scripts/python.exe tools/sinh_bang_vang_phien.py --ghi tests/du_lieu/bang_vang_phien.json

Chạy lại lệnh trên sau tái cấu trúc phải cho ra file GIỐNG HỆT (test dùng cùng hàm).
Đừng sinh lại bảng vàng để "làm test xanh": một ô đổi là hành vi đổi.

KỊCH BẢN. Mười mã, 95 phiên, giá và điểm viết tay (xác định, không ngẫu nhiên). `_analyze`
được thay bằng bảng điểm của kịch bản — bộ máy THẬT (`run_session` → `fill_pending` →
`fill_closing` → `evaluate_open`/`xet_lenh_dat_san` → `consider_entry`, trượt giá, bước giá,
lô chẵn, khoá biên, trần vốn, cắt lỗ, trailing) chạy nguyên văn. Các nguồn ngoài được thay
bằng hàm xác định: VN-INDEX (`market_filter.is_vni_bullish`), độ rộng (`do_rong`), IMOM
(`imom`), lịch phiên và máy đóng băng (`chot_sut_giam`), bộ nhớ hậu nghiệm (tắt).

MƯỜI BỐN KỊCH BẢN. Mỗi kịch bản cờ đặt một (hoặc vài) cờ của bộ máy rồi chạy cả 95 phiên. Cờ
đặt bằng GÁN BIẾN MODULE (`paper_trading.<CỜ> = giá trị`) — đúng cách các dụng cụ ĐO 30–33
đang làm — nên bảng này cũng khoá việc ĐỌC CỜ LÚC GỌI. Mặc định phải bằng nguồn: kịch bản
`mac_dinh` không đặt gì, và `co_mac_dinh` ghi các cờ đọc từ module lúc sinh.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd

GOC = Path(__file__).resolve().parent.parent
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

#: Mười mã của kịch bản, theo thứ tự xử lý trong một phiên (trần vốn phụ thuộc thứ tự).
MA = ["FPT", "HPG", "VNM", "SSI", "SHS", "ACB", "MWG", "VCB", "STB", "GAS"]
SO_PHIEN = 95
PHIEN = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-04-01", periods=SO_PHIEN)]

#: Cờ của bộ máy mà bảng vàng khoá mặc định (đọc từ module lúc sinh, ghi vào file).
CO = ["CHO_PHEP_MO_LENH_MOI", "BUY_THRESHOLD", "TRAN_VON_CAM_KET_PCT", "CONG_VNI_BAT",
      "DO_RONG_NGUONG", "NGHI_SAU_LO_NGAY", "LOC_IMOM_PHAN_VI", "CHOT_SUT_GIAM_NGUONG",
      "CHOT_SUT_GIAM_PHIEN", "EXIT_SIGNAL_THRESHOLD", "MAX_HOLD_SESSIONS", "CHOT_LOI_CUNG"]

#: tên kịch bản -> {"co": {CỜ: giá trị}, "that": máy đóng băng THẬT?, "chi_khop_xen_ke": bool,
#:                  "buy_threshold": tham số truyền thẳng vào run_session}
KICH_BAN = {
    "mac_dinh": {},
    "nghi_sau_lo_7": {"co": {"NGHI_SAU_LO_NGAY": 7}},
    "do_rong_050": {"co": {"CONG_VNI_BAT": False, "DO_RONG_NGUONG": 0.50}},
    "do_rong_050_giu_vni": {"co": {"DO_RONG_NGUONG": 0.50}},
    "imom_020": {"co": {"LOC_IMOM_PHAN_VI": 0.20}},
    "chot_sut_giam_gia": {"co": {"CHOT_SUT_GIAM_NGUONG": 0.15}},
    "chot_sut_giam_that": {"co": {"CHOT_SUT_GIAM_NGUONG": 0.002, "CHOT_SUT_GIAM_PHIEN": 5},
                           "that": True},
    "chot_loi_cung": {"co": {"CHOT_LOI_CUNG": True}},
    "tran_von_40": {"co": {"TRAN_VON_CAM_KET_PCT": 40.0}},
    "nguong_mua_55": {"co": {"BUY_THRESHOLD": 55}},
    "thoat_50_giu_30": {"co": {"EXIT_SIGNAL_THRESHOLD": 50, "MAX_HOLD_SESSIONS": 30}},
    "dong_cong_c5": {"co": {"CHO_PHEP_MO_LENH_MOI": False}},
    "tham_so_nguong_58": {"buy_threshold": 58.0},
    "chi_khop_xen_ke": {"chi_khop_xen_ke": True},
}

# ── giá (nghìn đồng, như cache) ──────────────────────────────────────
_NEN = {  # mã: (giá gốc, trôi mỗi phiên, tần số sóng, pha)
    "FPT": (60.0, 0.0030, 0.31, 0.2), "HPG": (55.0, 0.0010, 0.27, 1.1),
    "VNM": (70.0, 0.0006, 0.23, 2.0), "SSI": (52.0, -0.0010, 0.37, 0.5),
    "SHS": (58.0, 0.0012, 0.29, 3.0), "ACB": (64.0, 0.0018, 0.33, 1.7),
    "MWG": (72.0, 0.0016, 0.21, 0.9), "VCB": (90.0, 0.0010, 0.19, 2.4),
    "STB": (56.0, 0.0014, 0.41, 0.3), "GAS": (80.0, 0.0012, 0.25, 1.4),
}
#: Khoảng cách cắt lỗ (tỉ lệ) của khuyến nghị rủi ro, mỗi mã một số: đổi cỡ vị thế.
_SL = {"FPT": 0.05, "HPG": 0.05, "VNM": 0.04, "SSI": 0.05, "SHS": 0.06, "ACB": 0.045,
       "MWG": 0.05, "VCB": 0.04, "STB": 0.055, "GAS": 0.05}
#: Biên chốt lời của khuyến nghị (tỉ lệ trên giá vào).
_TP = {m: 1.20 for m in MA}
_TP["GAS"] = 1.10

#: Ngày bị đảo giá lẻ: {(mã, i): {"ret": ..., "gap": ..., "cao": ..., "thap": ..., "khoa": bool}}.
#: `ret` = lợi suất đóng cửa so phiên trước; `gap` = mở cửa lệch so đóng cửa phiên trước;
#: `cao`/`thap` = nhân lên max/min(mở, đóng); `khoa` = nến MỘT GIÁ (kịch trần/sàn).
_SOC = {
    ("HPG", 17): {"ret": -0.09, "thap": 0.99},                     # thủng SL
    ("SSI", 31): {"ret": -0.012},                                   # nằm dưới giá vào
    ("SHS", 50): {"gap": -0.10, "ret": -0.09, "thap": 0.99},        # gap dưới SL lúc mở cửa
    ("GAS", 60): {"ret": 0.04, "cao": 1.25},                        # đâm qua chốt lời
    ("VCB", 62): {"ret": -0.069, "khoa": True},                     # kịch sàn một giá
    ("VCB", 63): {"gap": -0.01, "ret": -0.01},                      # phiên mở khoá, vẫn dưới SL
    ("ACB", 56): {"ret": 0.069, "khoa": True},                      # kịch trần một giá
    ("MWG", 75): {"ret": -0.08, "thap": 0.99},
}

# ── điểm: {mã: [(i0, i1, điểm), ...]}, mặc định 50 ───────────────────
_DIEM = {
    "FPT": [(8, 89, 70)],                                  # vào sớm, giữ tới trần thời gian
    "HPG": [(14, 14, 72), (17, 17, 72), (19, 21, 72), (26, 26, 72)],  # cắt lỗ i=17 CÙNG phiên tín hiệu 72
    "VNM": [(24, 28, 70), (33, 33, 61), (34, 34, 62), (36, 60, 40)],  # VN-INDEX giảm; 61 / 62
    "SSI": [(30, 30, 70), (32, 38, 47), (39, 39, 44)],     # thoát theo tín hiệu ở 44, không 47
    "SHS": [(40, 40, 80), (53, 54, 80)],
    "ACB": [(55, 55, 75)],                                 # 56 kịch trần -> lệnh chờ bị HUỶ
    "MWG": [(44, 49, 75), (70, 70, 75)],                   # 44 thiếu SL -> bỏ; 45 vào
    "VCB": [(44, 44, 78)],
    "STB": [(44, 48, 74), (52, 52, 74)],                   # 44 BLOCK -> bỏ; 45 vào
    "GAS": [(46, 52, 76)],                                 # 46 WARN vẫn vào
}
#: (mã, i) -> chất lượng dữ liệu khác "OK".
_CHAT_LUONG = {("STB", 44): "BLOCK", ("GAS", 46): "WARN"}
#: (mã, i) mà khuyến nghị rủi ro thiếu cắt lỗ.
_THIEU_SL = {("MWG", 44)}

#: VN-INDEX dưới MA50 ở các phiên này.
_VNI_XAU = set(PHIEN[24:29]) | set(PHIEN[52:54])
#: Độ rộng thị trường: thấp ở các phiên này, thiếu ở đầu chuỗi.
_DO_RONG_THAP = set(PHIEN[44:47]) | set(PHIEN[26:28])
_DO_RONG_THIEU = set(PHIEN[:5])
#: Phân vị IMOM của mã (cố định theo mã).
_IMOM = {"HPG": 0.10, "MWG": 0.30, "VNM": 0.18}
#: Sổ đóng băng "giả" (kịch bản không dùng máy thật): cửa sổ đóng băng theo phiên.
_DONG_BANG_GIA = (set(PHIEN[56:59]), 0.2, PHIEN[55])


def dung_gia() -> dict:
    """{mã: DataFrame OHLCV nghìn đồng, làm tròn 0,1 (= 100đ, hợp bước giá mọi sàn)}."""
    ra = {}
    for ma in MA:
        goc, troi, w, pha = _NEN[ma]
        dong = [goc]
        ret = [0.0]
        for i in range(1, SO_PHIEN):
            r = troi + 0.004 * math.sin(w * i + pha)
            soc = _SOC.get((ma, i), {})
            if "ret" in soc:
                r = soc["ret"]
            ret.append(r)
            dong.append(round(dong[-1] * (1 + r), 1))
        mo, cao, thap = [dong[0]], [dong[0] * 1.003], [dong[0] * 0.997]
        for i in range(1, SO_PHIEN):
            soc = _SOC.get((ma, i), {})
            o = round(dong[i - 1] * (1 + soc["gap"]), 1) if "gap" in soc else dong[i - 1]
            c = dong[i]
            h = max(o, c) * 1.003 * soc.get("cao", 1.0)
            t = min(o, c) * 0.997 * soc.get("thap", 1.0)
            if soc.get("khoa"):
                o = h = t = c
            mo.append(o)
            cao.append(round(h, 1) if not soc.get("khoa") else c)
            thap.append(round(t, 1) if not soc.get("khoa") else c)
        ra[ma] = pd.DataFrame({
            "time": PHIEN, "open": mo, "high": cao, "low": thap, "close": dong,
            "volume": [2_500_000.0 + 20_000.0 * (i % 7) for i in range(SO_PHIEN)]})
    return ra


def diem_cua(ma: str, i: int) -> int:
    for a, b, d in _DIEM.get(ma, []):
        if a <= i <= b:
            return d
    return 50


def ket_qua_cham(ma: str, i: int, gia: dict) -> dict:
    """Kết quả `_analyze` của (mã, phiên i): điểm viết tay + khuyến nghị rủi ro dựng từ giá."""
    d = diem_cua(ma, i)
    vao = float(gia[ma]["close"].iloc[i]) * 1000.0
    rec = {"entry_price": vao, "stop_loss_price": vao * (1 - _SL[ma]),
           "take_profit_price": vao * _TP[ma]}
    if (ma, i) in _THIEU_SL:
        rec["stop_loss_price"] = None
    return {"final_score": d, "recommendation": "MUA" if d >= 62 else "NẮM GIỮ",
            # bia-ok: kịch bản TỔNG HỢP viết tay — "OK" là mức chất lượng của dữ liệu giả, không phải số đo
            "data_quality": _CHAT_LUONG.get((ma, i), "OK"),
            "score_breakdown": {"tong": d}, "key_reasons": [f"điểm {d}"],
            "analyses": {"risk": {"recommendations": rec}}}


@contextlib.contextmanager
def _gan(doi_tuong, ten: str, gia_tri):
    cu = getattr(doi_tuong, ten)
    setattr(doi_tuong, ten, gia_tri)
    try:
        yield
    finally:
        setattr(doi_tuong, ten, cu)


@contextlib.contextmanager
def ngu_canh(gia: dict, that: bool = False):
    """Thay mọi nguồn ngoài bằng hàm xác định; trả lại nguyên trạng ở cuối."""
    import chot_sut_giam
    import do_rong
    import imom
    import market_filter
    import paper_runner
    import post_mortem_learning

    class _TatHoc:
        enabled = False

    chi_so = {d: i for i, d in enumerate(PHIEN)}

    def _phan_tich(symbol, history, exchange="HOSE", session_date=None):
        return ket_qua_cham(symbol, chi_so[str(session_date)[:10]], gia)

    def _may_gia(phien, he_so, t, nguong, so_phien):
        cua_so, sut, bat_dau = _DONG_BANG_GIA
        return (sut, bat_dau) if str(t)[:10] in cua_so else None

    def _do_rong(ngay):
        n = str(ngay)[:10]
        return None if n in _DO_RONG_THIEU else (0.30 if n in _DO_RONG_THAP else 0.70)

    with contextlib.ExitStack() as st:
        st.enter_context(_gan(paper_runner, "_analyze", _phan_tich))
        st.enter_context(_gan(market_filter, "is_vni_bullish",
                              lambda d, *a, **k: str(d)[:10] not in _VNI_XAU))
        st.enter_context(_gan(do_rong, "do_rong_mac_dinh", _do_rong))
        st.enter_context(_gan(imom, "phan_vi_mac_dinh", lambda ma, ngay: _IMOM.get(ma)))
        st.enter_context(_gan(chot_sut_giam, "lich_phien_mac_dinh", lambda: list(PHIEN)))
        if not that:
            st.enter_context(_gan(chot_sut_giam, "may_trang_thai", _may_gia))
        st.enter_context(_gan(post_mortem_learning, "get_learning_engine", lambda *a, **k: _TatHoc()))
        yield


def _lam_tron(x):
    return round(x, 6) if isinstance(x, float) else x


COT_LENH = ["symbol", "signal_date", "entry_date", "entry_price", "exit_date", "exit_price",
            "exit_reason", "stop_loss", "take_profit", "size_pct", "entry_score", "status"]
COT_QD = ["symbol", "signal_date", "score", "acted", "skip_reason", "data_quality"]


def chay_kich_ban(ten: str, cach: str = "module", gia: dict | None = None) -> dict:
    """Chạy MỘT kịch bản, trả bảng kết quả (dict thuần JSON).

    `cach` = "module": cờ đặt bằng GÁN BIẾN MODULE (đường hiện hành, và là đường bảng vàng sinh
    ra). `cach` = "cau_hinh": module giữ nguyên MẶC ĐỊNH, cờ đi qua `CauHinhVao` truyền vào
    `run_session(cau_hinh=...)` — chỉ chạy được SAU tái cấu trúc.
    """
    import paper_runner
    import paper_trading as pt

    kb = KICH_BAN[ten]
    gia = gia or dung_gia()
    co = dict(kb.get("co") or {})
    with contextlib.ExitStack() as st:
        st.enter_context(ngu_canh(gia, that=bool(kb.get("that"))))
        thamso = {}
        if cach == "module":
            for k, v in co.items():
                st.enter_context(_gan(pt, k, v))
        else:
            import dataclasses
            thamso["cau_hinh"] = dataclasses.replace(
                pt.CauHinhVao.tu_module(), **{k.lower(): v for k, v in co.items()})
        if "buy_threshold" in kb:
            thamso["buy_threshold"] = kb["buy_threshold"]
        so = pt.PaperTradingJournal(":memory:")
        nhat_ky_buoc = []
        for i in range(SO_PHIEN):
            chi_khop = bool(kb.get("chi_khop_xen_ke")) and i % 2 == 1 and i > 0
            for ma in MA:
                lich_su = gia[ma].iloc[: i + 1]
                nen = {k: float(gia[ma][k].iloc[i]) for k in ("open", "high", "low", "close", "volume")}
                s = paper_runner.run_session(so, ma, lich_su, nen, PHIEN[i], "HOSE",
                                             chi_khop=chi_khop, **thamso)
                if any(s[k] for k in ("filled_in", "filled_out", "closed", "opened")):
                    nhat_ky_buoc.append([i, ma, s["filled_in"], s["filled_out"], s["closed"],
                                         s["opened"]])
        lenh = [[_lam_tron(r[c]) for c in COT_LENH] for r in so.db.execute(
            f"SELECT {', '.join(COT_LENH)} FROM trades ORDER BY id").fetchall()]
        qd_tat_ca = [[_lam_tron(r[c]) for c in COT_QD] for r in so.db.execute(
            f"SELECT {', '.join(COT_QD)} FROM decisions ORDER BY seq").fetchall()]
        so.db.close()
    bam = hashlib.sha256(json.dumps(qd_tat_ca, ensure_ascii=False).encode("utf-8")).hexdigest()
    qd_khac_diem = [r for r in qd_tat_ca if not str(r[4]).startswith("điểm ")]
    return {"cot_lenh": COT_LENH, "lenh": lenh, "cot_quyet_dinh": COT_QD,
            "so_quyet_dinh": len(qd_tat_ca), "bam_quyet_dinh": bam,
            "quyet_dinh_khac_diem_thap": qd_khac_diem, "buoc": nhat_ky_buoc}


def phu(bang: dict) -> dict:
    """Đếm những gì bảng vàng THẬT SỰ chạm: lý do bỏ, lý do ra, trạng thái — để biết kịch bản
    không rỗng ở chỗ nó định canh."""
    dem: dict = {"ly_do_bo": {}, "ly_do_ra": {}, "trang_thai": {}}
    for ten, b in bang.items():
        for r in b["quyet_dinh_khac_diem_thap"]:
            k = str(r[4]).split(":")[0].split(" ")[0:3]
            k = " ".join(k)
            dem["ly_do_bo"][k] = dem["ly_do_bo"].get(k, 0) + 1
        for r in b["lenh"]:
            dem["ly_do_ra"][str(r[6])] = dem["ly_do_ra"].get(str(r[6]), 0) + 1
            dem["trang_thai"][r[11]] = dem["trang_thai"].get(r[11], 0) + 1
    return dem


def sinh() -> dict:
    import paper_trading as pt
    gia = dung_gia()
    co_mac_dinh = {c: getattr(pt, c) for c in CO}
    bang = {ten: chay_kich_ban(ten, "module", gia) for ten in KICH_BAN}
    return {"_ghi_chu": ("Bảng vàng BƯỚC 239. Sinh bằng tools/sinh_bang_vang_phien.py trên main "
                         "09f7980 TRƯỚC khi sửa bộ máy. Đừng sinh lại để làm test xanh."),
            "co_mac_dinh": co_mac_dinh, "kich_ban": bang}


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ghi", help="đường file JSON sẽ ghi")
    ap.add_argument("--phu", action="store_true", help="in số liệu độ phủ của kịch bản")
    a = ap.parse_args(argv)
    kq = sinh()
    van = json.dumps(kq, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if a.ghi:
        p = Path(a.ghi)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(van, encoding="utf-8", newline="\n")
        print(f"đã ghi {p} ({len(van):,} ký tự, {len(kq['kich_ban'])} kịch bản)")
    if a.phu or not a.ghi:
        print(json.dumps(phu(kq["kich_ban"]), ensure_ascii=False, indent=1, sort_keys=True))
        for ten, b in kq["kich_ban"].items():
            print(f"{ten}: {len(b['lenh'])} lệnh, {b['so_quyet_dinh']} quyết định")
    return 0


if __name__ == "__main__":
    sys.exit(main())
