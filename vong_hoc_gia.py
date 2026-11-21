"""Vòng học khép kín trên thị trường giả — Tầng 1 (C4, Lát 3, BƯỚC 290).

Đề bài: `docs/thiet-ke-c4-thi-truong-gia.md` mục 5 (vòng học), 7 (gác), 8 ("Lát 3") và mục 17
(ghi chú thi công của lát này). Đặc tả là nguồn duy nhất; đừng chép nó vào đây.

BỐN BỘ PHẬN, và cái nào là cái nào
  * `de_xuat`  — bộ đề xuất cơ sở (5.1). Hàm thuần: nhận dòng quyết định + bảng giá của CỬA SỔ ĐÃ NHÌN,
                 xếp 11 spec của họ F theo Δ = IC(spec) − IC(điểm đã ghi). CHƯA PHẢI đường thật, chưa phải C3.
  * khai       — sổ ứng viên giả là MỘT dict trong bộ nhớ, mỗi lần khai đi qua `cham_bong.kiem_so_ung_vien`.
  * xác nhận   — `cham_xac_nhan.cham` THẬT (không bản sao): chỉ phán ở đúng `cham_bong.MOC_DOC` phiên có nhãn.
  * `nang_cap` — sổ phiên bản trong bộ nhớ (5.4). KHÔNG đường thật nào nhập module này (gác G2).

MODULE NÀY CHỈ NHẬN DỮ LIỆU, KHÔNG SINH THỊ TRƯỜNG. Nó nhận `dong` (dòng đúng khuôn tab `decisions`) và
`gia` (ngày × mã) — không nhận `ThiTruongGia` (đối tượng ấy mang theo bảng sự thật của oracle) và không
gọi bộ sinh, nên không có đường nào từ đây tới một dòng hạt hay tới oracle (gác G4). Việc chọn dòng hạt nằm ở
dụng cụ `tools/chay_vong_thi_truong_gia.py`, nơi cửa `kiem_luong` chặn dòng 2, 3, 4, 5. Ngày không phải ngày giả
(trước `thi_truong_gia.NGAY_DAU`) bị từ chối: module không thể bị chĩa vào sổ thật.

KHÔNG CÓ TỶ LỆ NÀO Ở ĐÂY (đó là Lát 5). Một lượt chạy là MỘT thị trường; số in ra là biên bản, không phải kết quả.
"""
from __future__ import annotations

import copy
import datetime as _dt
import json

import pandas as pd

import cham_bong as cb
import cham_xac_nhan as cx
import experiment_tran_dac_trung as E
import thi_truong_gia as T

#: Tên có tiền tố khác `UV-` (gác G3 cấm chuỗi ấy): "DX" = đề xuất.
TIEN_TO_MA = "DX"
TRANG_THAI_QUA = "QUA"
#: Dấu của ứng viên đang chờ đọc khi có nâng cấp (mục 5.4 khoản 5, Q4). K VẪN đếm nó.
DAU_BI_HUY = "bi_huy_vi_nang_cap"
CHUA_DOC = "CHUA DOC"
KET_CUC_NANG_CAP = "NANG_CAP"
KET_CUC_KHONG_NANG_CAP = "KHONG_NANG_CAP"


# ── ngày giả, bảng giá giả ───────────────────────────────────────────────────

def kiem_ngay_gia(ngay) -> None:
    """Mọi ngày phải ≥ `thi_truong_gia.NGAY_DAU`: module không đọc được dòng của sổ thật (năm 2026)."""
    ngay = [str(n)[:10] for n in ngay]
    if not ngay:
        raise ValueError("khong co ngay nao")
    som = [n for n in ngay if n < T.NGAY_DAU]
    if som:
        raise ValueError(f"ngay {som[0]} truoc ngay gia dau tien {T.NGAY_DAU}: day khong phai thi truong gia")


def keo_luc_gia(ngay_cuoi: str) -> str:
    """Giờ kéo của bảng giả: nửa đêm giờ VN của NGÀY SAU nến cuối (nến cuối không còn dở; giờ kéo không sớm hơn
    nến cuối). Cùng quy tắc với dụng cụ hiệu chuẩn của Lát 2 — suy từ nến cuối, không gõ một hằng ngày."""
    return (_dt.date.fromisoformat(ngay_cuoi) + _dt.timedelta(days=1)).isoformat() + "T00:00:00+07:00"


def bang_gia_gia(gia: pd.DataFrame) -> dict:
    """Bảng giá giả đúng khuôn `cham_xac_nhan.cham` nhận (đi thẳng bằng dict, như Lát 2)."""
    return {"gia": gia, "keo_luc": keo_luc_gia(str(gia.index[-1])), "nguon": {m: "vci" for m in gia.columns}}


def cat_den_phien(dong: list[dict], gia: pd.DataFrame, phien_cuoi: int) -> tuple[list[dict], pd.DataFrame]:
    """Chỉ giữ dữ liệu tới phiên `phien_cuoi` (chỉ số, TÍNH CẢ phiên ấy): dòng quyết định và bảng giá.
    Đây là chỗ DUY NHẤT vòng học cắt thời gian; mọi lượt đọc của bộ đề xuất và của bước xác nhận đi qua nó."""
    ngay = list(gia.index)
    if isinstance(phien_cuoi, bool) or not isinstance(phien_cuoi, int) or not 0 <= phien_cuoi < len(ngay):
        raise ValueError(f"phien_cuoi phai la so nguyen trong [0, {len(ngay) - 1}], nhan {phien_cuoi!r}")
    han = str(ngay[phien_cuoi])
    return [r for r in dong if str(r.get("signal_date", ""))[:10] <= han], gia.iloc[:phien_cuoi + 1]


# ── bộ đề xuất cơ sở (5.1) ───────────────────────────────────────────────────

def _khoa_xep(x: dict) -> tuple:
    """Xếp Δ giảm dần; hoà thì theo THỨ TỰ TÊN spec (mục 5.1: "ràng buộc hoà bằng thứ tự đặt tên spec")."""
    return (-x["delta"], x["ten"])


def de_xuat(dong: list[dict], gia: pd.DataFrame) -> list[dict]:
    """Xếp 11 spec của họ F theo Δ = IC(spec) − IC(điểm đã ghi) trên MỌI phiên có nhãn của dữ liệu đưa vào.

    Dùng đúng `cham_bong.ma_tran_cap` và `E.rho_hang` (không bản sao); KHÔNG chạy `cham_bong.so_cap`: dữ liệu
    đã nhìn không có "phán". Hàm này tin đầu vào: việc cắt theo thời gian là của bên gọi (`cat_den_phien`).
    Trả danh sách dict `{ten, spec, delta, ic_spec, ic_da_ghi, n_phien, n_ma}` đã xếp; KHÔNG lọc Δ > 0
    (việc ấy là của `chon_khai`) để biên bản thấy cả phần đã quét mà không khai."""
    bang = cb.doc_quyet_dinh(dong, "")
    nhan = E.nhan_vuot_ro({m: pd.DataFrame({"close": gia[m]}) for m in gia.columns}, cb.NHIP)
    ra = []
    for ten, spec in T.ho_spec_f().items():
        B, C, Y, phien, cot = cb.ma_tran_cap(bang, spec, nhan)
        if not len(phien) or not len(cot):
            raise ValueError("cua so da nhin khong co phien co nhan nao: khong de xuat duoc")
        ic_cu = E.rho_hang(B.ravel(), Y.ravel())
        ic_moi = E.rho_hang(C.ravel(), Y.ravel())
        ra.append({"ten": ten, "spec": spec, "delta": float(ic_moi - ic_cu), "ic_spec": float(ic_moi),
                   "ic_da_ghi": float(ic_cu), "n_phien": len(phien), "n_ma": len(cot)})
    return sorted(ra, key=_khoa_xep)


def chon_khai(xep: list[dict], so: int = T.SO_UNG_VIEN_KHAI) -> list[dict]:
    """`so` spec đầu theo thứ hạng, CHỈ spec có Δ > 0 (ít hơn `so` spec dương thì khai ít hơn, không ép đủ)."""
    return [x for x in sorted(xep, key=_khoa_xep) if x["delta"] > 0][:so]


# ── lịch ─────────────────────────────────────────────────────────────────────

def phien_khai(ngay: list[str], so: int, so_phien_nhin: int = T.SO_PHIEN_DA_NHIN) -> list[int]:
    """Chỉ số phiên khai của `so` ứng viên: phiên ĐẦU TIÊN của tháng dương lịch thứ i kể từ tháng chứa phiên
    cuối của cửa sổ đã nhìn (`TRAN_MOI_THANG` = 1 đọc theo THÁNG DƯƠNG LỊCH). Suy từ lịch của dữ liệu."""
    if so_phien_nhin < 1 or so_phien_nhin > len(ngay):
        raise ValueError("cua so da nhin dai hon du lieu")
    nam, thang = int(ngay[so_phien_nhin - 1][:4]), int(ngay[so_phien_nhin - 1][5:7])
    ra = []
    for i in range(1, so + 1):
        m0 = thang - 1 + i
        muc = f"{nam + m0 // 12:04d}-{m0 % 12 + 1:02d}"
        dau = next((j for j, n in enumerate(ngay) if str(n)[:7] == muc), None)
        if dau is None:
            raise ValueError(f"du lieu khong phu thang {muc} cua ung vien thu {i}")
        ra.append(dau)
    return ra


def phien_doc(phien_khai_i: int) -> int:
    """Phiên đọc: `MOC_DOC`-th phiên CÓ NHÃN kể từ phiên khai là `khai + MOC_DOC − 1`, nhãn của nó cần giá tới
    +`NHIP`+1 phiên nữa. `chay_vong` kiểm lại bằng chính trạng thái của máy đo (nổ nếu còn `CHUA TOI MOC`)."""
    return phien_khai_i + cb.MOC_DOC - 1 + T.DO_TRE_NHAN


# ── sổ ứng viên giả (5.2) ────────────────────────────────────────────────────

def khai_ung_vien(so_uv: dict, ma: str, khai_ngay: str, spec: dict, mo_ta: str, ly_do: str) -> dict:
    """Trả sổ MỚI có thêm một ứng viên; mỗi lần khai đi qua `cham_bong.kiem_so_ung_vien` (trần 1/tháng và
    `qua_sang: null` tự áp). Sổ không ghi ra đĩa."""
    if ma in so_uv["ung_vien"]:
        raise ValueError(f"ung vien {ma} da khai")
    moi = copy.deepcopy(so_uv)
    moi["ung_vien"][ma] = {"khai_ngay": khai_ngay, "mo_ta": mo_ta, "ly_do": ly_do, "qua_sang": None,
                           "spec": copy.deepcopy(spec)}
    cb.kiem_so_ung_vien(moi)
    return moi


def huy_ung_vien_cho_doc(so_uv: dict, ma_da_doc) -> dict:
    """Mục 5.4 khoản 5 (Q4): mọi ứng viên CHƯA đọc bị HUỶ — đánh dấu `bi_huy_vi_nang_cap`. Sổ MỚI giữ NGUYÊN
    số dòng, nên K (`cham_bong.so_da_sang`) và ngưỡng 0,05/K không đổi: "K vẫn đếm"."""
    moi = copy.deepcopy(so_uv)
    for ma, d in moi["ung_vien"].items():
        if ma not in set(ma_da_doc):
            d[DAU_BI_HUY] = True
    cb.kiem_so_ung_vien(moi)
    return moi


# ── nâng cấp (5.4) ───────────────────────────────────────────────────────────

def so_phien_ban_dau() -> dict:
    """Sổ phiên bản: một dict trong bộ nhớ, MỘT phiên bản 0 = điểm đã ghi (`spec` None), hiệu lực từ phiên 0."""
    return {"phien_ban": [{"so": 0, "spec": None, "ma_ung_vien": None, "hieu_luc_tu_phien": 0,
                           "phien_doc": None, "bang_chung": None}]}


def nang_cap(so_phien_ban: dict, ket_qua_xac_nhan: dict, ma_ung_vien: str, phien_doc: int,
             so_ung_vien: dict) -> dict:
    """Hàm thuần: sổ phiên bản MỚI (hoặc chính sổ cũ khi không nâng cấp). Luật mục 5.4:

    1. CHỈ `trang_thai == "QUA"` tạo phiên bản mới; `THUA`, `DANG CHAM`, `CHUA TOI MOC`, `CHUA DU DU LIEU` không.
    2. Phiên bản mới có `spec` BẰNG đúng spec đã khai (so bằng, không làm tròn), kèm bằng chứng.
    3. Hiệu lực từ phiên SAU phiên đọc: `phien_doc + 1` (bất biến 1).
    6. MỘT ĐỜI (Q7): đã có phiên bản 1 thì không có phiên bản 2.

    `ket_qua_xac_nhan` là kết quả của `cham_xac_nhan.cham`; `phien_doc` là CHỈ SỐ phiên. Khoản 4 (điểm ghi từ phiên
    hiệu lực) nằm ở `ap_phien_ban`. Tham số `so_ung_vien` là chỗ LỆCH với chữ ký ở mục 5.4 (không có nó thì
    hàm không biết spec đã khai): xem mục 17 của đặc tả."""
    if isinstance(phien_doc, bool) or not isinstance(phien_doc, int) or phien_doc < 0:
        raise ValueError(f"phien_doc phai la so nguyen >= 0, nhan {phien_doc!r}")
    ct = ket_qua_xac_nhan["chi_tiet"][ma_ung_vien]
    if ct["trang_thai"] != TRANG_THAI_QUA:
        return so_phien_ban
    if len(so_phien_ban["phien_ban"]) > 1:
        return so_phien_ban
    spec = copy.deepcopy(so_ung_vien["ung_vien"][ma_ung_vien]["spec"])
    cb.kiem_spec(spec)
    ban = {"so": len(so_phien_ban["phien_ban"]), "spec": spec, "ma_ung_vien": ma_ung_vien,
           "hieu_luc_tu_phien": phien_doc + 1, "phien_doc": phien_doc,
           "bang_chung": {"p": float(ct["p"]), "delta": float(ct["delta"]), "n_phien": int(ct["n_phien"]),
                          "n_ma": int(ct["n_ma"]), "K": int(ket_qua_xac_nhan["K"]),
                          "nguong": float(ct["nguong"]), "hat": int(ct["hat"]), "so_hoan_vi": int(ct["so_hoan_vi"])}}
    return {"phien_ban": [*copy.deepcopy(so_phien_ban["phien_ban"]), ban]}


def phien_ban_hieu_luc(so_phien_ban: dict, t: int) -> dict:
    """Phiên bản đang chạy ở phiên `t` (chỉ số): phiên bản cuối có `hieu_luc_tu_phien` ≤ t."""
    dang = [b for b in so_phien_ban["phien_ban"] if b["hieu_luc_tu_phien"] <= t]
    return dang[-1]


def ap_phien_ban(dong: list[dict], so_phien_ban: dict, ngay: list[str]) -> list[dict]:
    """Dòng quyết định của thế giới SAU nâng cấp (mục 5.4 khoản 4): từ phiên hiệu lực, `score` =
    `int(diem_ung_vien(spec, components))` — phiên bản mới là tổ hợp tuyến tính của thành phần. Trước đó,
    và khi phiên bản đang chạy là 0, dòng giữ NGUYÊN. Trả bản sao; không sửa `dong`."""
    chi_so = {str(n)[:10]: i for i, n in enumerate(ngay)}
    ra = []
    for r in dong:
        t = chi_so[str(r["signal_date"])[:10]]
        ban = phien_ban_hieu_luc(so_phien_ban, t)
        if ban["spec"] is None:
            ra.append(r)
            continue
        tp = json.loads(r["components"])
        moi = dict(r)
        moi["score"] = int(cb.diem_ung_vien(ban["spec"], {k: tp[k] for k in cb.THANH_PHAN}))
        ra.append(moi)
    return ra


def kiem_tien_ve_truoc(dong: list[dict], gia: pd.DataFrame, so_phien_ban: dict,
                       so_phien: int = T.SO_PHIEN_TIEN_VE_TRUOC) -> dict | None:
    """Kiểm TIẾN-VỀ-TRƯỚC (mục 4.6 cửa sổ F, tiêu chí C2): ΔIC thực hiện của phiên bản mới so với điểm đã ghi
    trên `so_phien` phiên ĐẦU TIÊN kể từ phiên hiệu lực. CHỈ dùng dòng và giá từ phiên hiệu lực trở đi — không
    một dòng hay một giá nào ở phiên đọc hoặc trước đó (có test). Nhãn của phiên t dùng giá t+1…t+22, nên
    chỉ phiên có đủ giá phía sau mới có nhãn; `du_cua_so` nói cửa sổ có đủ `so_phien` phiên có nhãn không.
    Một thị trường, một con số: KHÔNG có phán, KHÔNG có tỷ lệ. Không nâng cấp thì trả None."""
    if len(so_phien_ban["phien_ban"]) < 2:
        return None
    ban = so_phien_ban["phien_ban"][-1]
    hl = ban["hieu_luc_tu_phien"]
    ngay = [str(n) for n in gia.index]
    if hl >= len(ngay):
        return {"tu_phien": hl, "n_phien": 0, "n_ma": 0, "ic_da_ghi": None, "ic_phien_ban_moi": None,
                "delta_ic": None, "du_cua_so": False, "so_phien": so_phien}
    cuoi = min(hl + so_phien - 1, len(ngay) - 1)
    gia_sau = gia.iloc[hl:]                                # từ phiên hiệu lực: KHÔNG có gì ở phiên đọc hay trước đó
    dong_cua_so = [r for r in dong if ngay[hl] <= str(r["signal_date"])[:10] <= ngay[cuoi]]
    nhan = E.nhan_vuot_ro({m: pd.DataFrame({"close": gia_sau[m]}) for m in gia_sau.columns}, cb.NHIP)
    cu = cb.doc_quyet_dinh(dong_cua_so, "")
    moi = cb.doc_quyet_dinh(ap_phien_ban(dong_cua_so, so_phien_ban, ngay), "")
    B_cu, _, Y, phien, cot = cb.ma_tran_cap(cu, ban["spec"], nhan)
    B_moi, _, Y2, phien2, cot2 = cb.ma_tran_cap(moi, ban["spec"], nhan)
    if phien != phien2 or cot != cot2:
        raise ValueError("hai ma tran cua so tien-ve-truoc khong cung phien/ma")
    if not len(phien) or not len(cot):
        return {"tu_phien": hl, "n_phien": 0, "n_ma": 0, "ic_da_ghi": None, "ic_phien_ban_moi": None,
                "delta_ic": None, "du_cua_so": False, "so_phien": so_phien}
    ic_cu, ic_moi = E.rho_hang(B_cu.ravel(), Y.ravel()), E.rho_hang(B_moi.ravel(), Y.ravel())
    return {"tu_phien": hl, "tu_ngay": ngay[hl], "den_ngay_cua_so": ngay[cuoi], "n_phien": len(phien),
            "n_ma": len(cot), "ic_da_ghi": float(ic_cu), "ic_phien_ban_moi": float(ic_moi),
            "delta_ic": float(ic_moi - ic_cu), "du_cua_so": len(phien) == so_phien, "so_phien": so_phien}


# ── vòng khép kín (một thị trường) ───────────────────────────────────────────

def chay_vong(dong: list[dict], gia: pd.DataFrame, de_xuat_fn=None, so_hoan_vi: int = cx.SO_HOAN_VI,
              so_phien_nhin: int = T.SO_PHIEN_DA_NHIN) -> dict:
    """MỘT thị trường, từ đầu tới cuối: đề xuất → khai (mỗi tháng một) → xác nhận bằng `cham_xac_nhan.cham` ở
    phiên đọc của từng ứng viên → nâng cấp (một đời) → huỷ ứng viên đang chờ → kiểm tiến-về-trước.

    `de_xuat_fn` mặc định là `de_xuat`; nó là CHỖ CẮM (một hàm `(dong, gia) -> [{ten, spec, delta}]`) để C3 chạy
    lại cùng tiêu chí, và để test dựng ca (G, Z, H) mà không phụ thuộc vào cái bộ đề xuất chọn.
    Mọi lượt đọc chỉ thấy dữ liệu tới phiên của nó (`cat_den_phien`); bộ đề xuất chỉ thấy tới
    min(cửa sổ đã nhìn, ngày khai đầu − 1). Trả biên bản (dict thuần) — không in, không ghi."""
    de_xuat_fn = de_xuat if de_xuat_fn is None else de_xuat_fn
    ngay = [str(n) for n in gia.index]
    kiem_ngay_gia(ngay)
    kiem_ngay_gia([str(r["signal_date"])[:10] for r in dong])

    khai0 = phien_khai(ngay, 1, so_phien_nhin)[0]
    cuoi_nhin = min(so_phien_nhin - 1, khai0 - 1)
    dong_nhin, gia_nhin = cat_den_phien(dong, gia, cuoi_nhin)
    xep = de_xuat_fn(dong_nhin, gia_nhin)
    chon = chon_khai(xep)

    khai_idx = phien_khai(ngay, len(chon), so_phien_nhin) if chon else []
    doc_idx = [phien_doc(k) for k in khai_idx]
    if doc_idx and max(khai_idx) >= min(doc_idx):
        raise ValueError("co ung vien khai SAU phien doc dau tien: vong nay gia dinh khai xong truoc khi doc")
    so_uv = {"ung_vien": {}}
    lich = []
    for i, x in enumerate(chon):
        ma = f"{TIEN_TO_MA}{i + 1}"
        so_uv = khai_ung_vien(so_uv, ma, ngay[khai_idx[i]], x["spec"], f"bo de xuat co so: {x['ten']}",
                              f"delta = {x['delta']:+.4f} tren cua so da nhin")
        lich.append({"ma": ma, "ten": x["ten"], "khai_phien": khai_idx[i], "khai_ngay": ngay[khai_idx[i]],
                     "doc_phien": doc_idx[i], "doc_ngay": ngay[doc_idx[i]] if doc_idx[i] < len(ngay) else None})

    so_pb = so_phien_ban_dau()
    lan_doc, da_doc = [], []
    for i, ma in enumerate(so_uv["ung_vien"]):
        if doc_idx[i] >= len(ngay):
            break                                           # thị trường chưa dài tới phiên đọc: chưa đọc
        dong_cat, gia_cat = cat_den_phien(dong, gia, doc_idx[i])
        kq = cx.cham(dong_cat, so_uv, bang_gia_gia(gia_cat), cx.HAT_RNG, so_hoan_vi)
        ct = kq["chi_tiet"][ma]
        if ct["trang_thai"] == cb.CHUA_TOI_MOC:
            raise ValueError(f"{ma}: phien doc {doc_idx[i]} tinh sai (may do con CHUA TOI MOC, "
                             f"{ct['n_phien_co_nhan']}/{cb.MOC_DOC} phien co nhan)")
        da_doc.append(ma)
        moi = nang_cap(so_pb, kq, ma, doc_idx[i], so_uv)
        nang = len(moi["phien_ban"]) > len(so_pb["phien_ban"])
        lan_doc.append({"ma": ma, "phien_doc": doc_idx[i], "ngay_doc": ngay[doc_idx[i]], "K": kq["K"],
                        "nguong": kq["nguong"], "trang_thai": ct["trang_thai"], "n_phien": ct["n_phien"],
                        "n_ma": ct["n_ma"], "delta": ct.get("delta"), "p": ct.get("p"), "z": ct.get("z"),
                        "nang_cap": nang})
        so_pb = moi
        if nang:
            so_uv = huy_ung_vien_cho_doc(so_uv, da_doc)
            break

    huy = [ma for ma, d in so_uv["ung_vien"].items() if d.get(DAU_BI_HUY)]
    trang_thai = {ma: next((r["trang_thai"] for r in lan_doc if r["ma"] == ma),
                           DAU_BI_HUY if ma in huy else CHUA_DOC) for ma in so_uv["ung_vien"]}
    nang_len = len(so_pb["phien_ban"]) > 1
    hl = so_pb["phien_ban"][-1]["hieu_luc_tu_phien"] if nang_len else None
    return {"so_phien": len(ngay), "ngay_dau": ngay[0], "ngay_cuoi": ngay[-1], "cua_so_nhin": cuoi_nhin + 1,
            "de_xuat": {"xep": xep, "da_chon": [x["ten"] for x in chon]},
            "lich": lich, "so_ung_vien": so_uv, "doc": lan_doc, "huy": huy, "trang_thai": trang_thai,
            "so_phien_ban": so_pb, "K": cb.so_da_sang(so_uv),
            "hieu_luc_ngay": (ngay[hl] if hl is not None and hl < len(ngay) else None),
            "tien_ve_truoc": kiem_tien_ve_truoc(dong, gia, so_pb) if nang_len else None,
            "ket_cuc": KET_CUC_NANG_CAP if nang_len else KET_CUC_KHONG_NANG_CAP}
