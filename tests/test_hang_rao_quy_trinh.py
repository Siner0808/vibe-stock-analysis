"""Hàng rào QUY TRÌNH cho mọi điều kiện an toàn — không chỉ cho cổng C5.

VÌ SAO CÓ FILE NÀY
──────────────────
Cổng C5 hỏng vì bốn lý do (`docs/STATE.md` — "GỐC RỄ CỦA CỔNG C5"). Sửa
riêng cổng C5 thì lần sau một điều kiện khác sẽ hỏng y hệt, vì hai điểm
mù sinh ra nó chưa được rào:

  • **Ngưỡng chọn bằng trực giác.** Bản 1 hiệu chuẩn để bắt −2,5%/lệnh
    trong khi mức bất lợi thật là −0,927%. Lệch 8 lần độ lớn — nó cần
    11,4 năm để đạt 80% lực phát hiện.
  • **Điều kiện không có nơi hành động.** Bản 1 chỉ được gọi trong
    `report()`, một hàm nối chuỗi. Kể cả khi đạt, nó thêm một CÂU VĂN.

Hai điểm mù đó là điểm mù của QUY TRÌNH, không của một hàm. File này rào
chúng bằng một sổ đăng ký: mọi điều kiện an toàn phải khai ở đây, và mỗi
khai báo phải chứng minh được hai điều — ngưỡng SUY TỪ lực phát hiện, và
điều kiện đạt thì có thứ gì đó ĐỔI TRẠNG THÁI.

Thêm một điều kiện mới mà quên khai -> test đỏ. Đó là cách một luật trở
thành một cửa thay vì một gợi ý.
"""
import ast
import math
import random
import statistics as st
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import paper_metrics as pm  # noqa: E402
import paper_trading as pt  # noqa: E402
import run_daily as rd  # noqa: E402

#: SỔ ĐĂNG KÝ điều kiện an toàn.
#:
#:   dieu_kien   — hàm trả {"dat": bool}
#:   thi_hanh    — hàm ĐỔI TRẠNG THÁI khi điều kiện đạt
#:   co          — (module, tên) lá cờ mà thi_hanh phải đổi
#:   nguong      — hằng số quyết định, phải suy từ lực phát hiện
#:   luc         — (mức hiệu ứng, σ) mà `nguong` được hiệu chuẩn cho
DIEU_KIEN_AN_TOAN = {
    "dieu_kien_dong_lai": {
        "module": pm,
        "thi_hanh": rd.thi_hanh_dieu_kien_dung,
        "co": (pt, "CHO_PHEP_MO_LENH_MOI"),
        "nguong": "N_DAY_DU",
        "luc": (pm.MUC_BAT_LOI, pm.SIGMA_ALPHA),
    },
}

#: File có điều kiện an toàn. Hẹp có chủ đích: một cửa quá rộng sẽ bị tắt,
#: mà cửa bị tắt thì bằng không có.
FILE_CO_DIEU_KIEN = ("paper_metrics.py", "paper_trading.py", "run_daily.py")


def _ham_dieu_kien(ten_file: str) -> set:
    cay = ast.parse((GOC / ten_file).read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(cay)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("dieu_kien_")}


# ── 1. Không được có điều kiện an toàn nào nằm ngoài sổ ──────────────

def test_moi_dieu_kien_an_toan_deu_phai_khai():
    thay = set()
    for f in FILE_CO_DIEU_KIEN:
        thay |= _ham_dieu_kien(f)
    thieu = thay - set(DIEU_KIEN_AN_TOAN)
    assert not thieu, (
        f"điều kiện an toàn chưa khai trong DIEU_KIEN_AN_TOAN: {sorted(thieu)}. "
        f"Khai nó, kèm nơi thi hành và ngưỡng — hoặc nó sẽ lặp lại đúng lỗi "
        f"của cổng C5: một điều kiện không ai thi hành.")
    thua = set(DIEU_KIEN_AN_TOAN) - thay
    assert not thua, f"khai trong sổ nhưng không còn tồn tại: {sorted(thua)}"
    print(f"PASS  {len(thay)} điều kiện an toàn, đều đã khai")


# ── 2. Ngưỡng phải SUY TỪ lực phát hiện, không gõ tay ────────────────

def test_moi_nguong_deu_suy_tu_luc_phat_hien():
    for ten, k in DIEU_KIEN_AN_TOAN.items():
        n = getattr(k["module"], k["nguong"])
        muc, sigma = k["luc"]
        can = pm.co_mau_cho_luc(muc, sigma)
        assert n == can, (
            f"{ten}: {k['nguong']}={n} nhưng lực phát hiện 80% ở mức "
            f"{muc}%/lệnh với σ={sigma}% cần {can}. Ngưỡng phải suy ra, "
            f"không gõ tay — đó chính là chỗ bản 1 của cổng C5 sai.")
        print(f"PASS  {ten}: {k['nguong']}={n} khớp lực phát hiện ở {muc}%")


def test_muc_hieu_ung_phai_la_muc_THUC_TE_khong_phai_muc_tham_hoa():
    """Bản 1 hiệu chuẩn cho −2,5% trong khi mức thật là −0,927%.

    Không có cách nào để test biết "mức thật" là bao nhiêu — nhưng có cách
    bắt nó phải là một hằng số CÓ TÊN, đọc được, thay vì một con số nằm
    trong công thức. Đặt tên cho một giả định là bước đầu để ai đó cãi nó.
    """
    for ten, k in DIEU_KIEN_AN_TOAN.items():
        muc, sigma = k["luc"]
        assert isinstance(muc, float) and muc != 0, (ten, muc)
        assert isinstance(sigma, float) and sigma > 0, (ten, sigma)
        # Hằng số phải nằm ở mức module, không phải số rời trong hàm.
        ten_hang = [t for t in dir(k["module"])
                    if not t.startswith("_")
                    and getattr(k["module"], t, None) is muc]
        assert ten_hang, (
            f"{ten}: mức hiệu ứng {muc} không có tên ở mức module")
        print(f"PASS  {ten}: mức hiệu ứng có tên `{ten_hang[0]}` = {muc}")


# ── 3. Điều kiện đạt thì phải có thứ gì đó ĐỔI TRẠNG THÁI ────────────

def _so_dat_dieu_kien():
    """Sổ lệnh + rổ chuẩn khiến `dieu_kien_dong_lai` chắc chắn ĐẠT."""
    import datetime as dt

    from paper_trading import Trade

    moc = dt.datetime(2026, 8, 7, 14, 41).timestamp()
    ts = []
    for i in range(200):
        vao = (dt.date(2024, 1, 5) + dt.timedelta(days=i * 3)).isoformat()
        ra = (dt.date(2024, 1, 5) + dt.timedelta(days=i * 3 + 1)).isoformat()
        ts.append(Trade(
            id=i, symbol="FPT", signal_date=vao, entry_date=vao,
            entry_price=100.0, exit_date=ra, exit_price=97.0,
            exit_reason="STOP_LOSS", stop_loss=93.0, take_profit=110.0,
            size_pct=10.0, entry_score=62, status="CLOSED",
            created_at=moc + 86400 * (i + 1)))
    ro = {(t.entry_date, t.exit_date): t.net_return_pct() + 3.0 for t in ts}
    return ts, ro


def test_dieu_kien_dat_thi_TRANG_THAI_doi_that():
    """Chạy thật, không đọc mã: cờ phải đổi giá trị.

    Đây là phép kiểm mà cổng C5 thiếu suốt từ 24/08 tới 28/08/2026. Bản 1
    "đạt" chỉ có nghĩa là báo cáo thêm một dòng chữ.
    """
    ts, ro = _so_dat_dieu_kien()
    assert pm.dieu_kien_dong_lai(ts, ro)["dat"] is True, "sổ mẫu phải ĐẠT"
    for ten, k in DIEU_KIEN_AN_TOAN.items():
        mod, co = k["co"]
        cu = getattr(mod, co)
        try:
            setattr(mod, co, True)
            k["thi_hanh"](ts, lambda v: setattr(mod, co, v), ro)
            assert getattr(mod, co) is False, (
                f"{ten}: điều kiện ĐẠT nhưng `{mod.__name__}.{co}` không "
                f"đổi. Một điều kiện chỉ in ra thì không bảo vệ được gì.")
        finally:
            setattr(mod, co, cu)
        print(f"PASS  {ten}: đạt -> {mod.__name__}.{co} True → False")


def test_chua_dat_thi_KHONG_duoc_dung_vao_trang_thai():
    """Một hàng rào tự sập khi chưa cần thì sớm muộn bị gỡ."""
    for ten, k in DIEU_KIEN_AN_TOAN.items():
        ghi = []
        k["thi_hanh"]([], ghi.append, {})
        assert ghi == [], f"{ten}: chưa đạt mà đã đụng vào cờ: {ghi}"
        print(f"PASS  {ten}: chưa đạt -> không đụng trạng thái")


def test_noi_thi_hanh_KHONG_duoc_la_ham_noi_chuoi():
    """`report()` là hàm nối chuỗi — nó KHÔNG được là nơi thi hành duy nhất."""
    cay = ast.parse((GOC / "paper_metrics.py").read_text(encoding="utf-8"))
    rep = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "report")
    trong_report = {n.func.id for n in ast.walk(rep)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    for ten, k in DIEU_KIEN_AN_TOAN.items():
        assert ten in trong_report, (
            f"{ten} không còn được in ra trong report() — một điều kiện "
            f"không ai nhìn thấy cũng là một vấn đề")
        # ...nhưng phải có nơi khác THI HÀNH nó.
        nguon = (GOC / "run_daily.py").read_text(encoding="utf-8")
        assert f"{ten}(" in nguon, (
            f"{ten} chỉ được gọi trong report() — đúng lỗi nguyên nhân 4")
        print(f"PASS  {ten}: vừa được IN, vừa có nơi THI HÀNH ngoài report()")


# ── 4. Ngưỡng phải THẬT SỰ có lực phát hiện ở mức đã công bố ─────────

def _mo_phong(mu: float, sigma: float, n_toi_thieu: int, n_day_du: int,
              z: float, so_lan: int = 3000, seed: int = 20260829) -> float:
    """Tỷ lệ chạm biên HẠI, mô phỏng đúng cách mã đánh giá: LIÊN TỤC."""
    rng = random.Random(seed)
    dung = 0
    for _ in range(so_lan):
        tong = 0.0
        for n in range(1, n_day_du + 1):
            tong += rng.gauss(mu, sigma)
            if n < n_toi_thieu:
                continue
            if tong / n + z * sigma / math.sqrt(n) < 0:
                dung += 1
                break
    return dung / so_lan


def test_nguong_co_luc_phat_hien_that_o_muc_da_cong_bo():
    """Công bố lực phát hiện là chưa đủ — phải ĐO nó.

    Mô phỏng đúng cách mã đánh giá (liên tục, mỗi lượt quét), bằng chính
    các hằng số mã đang dùng. Đổi `Z_BIEN_HAI`, `N_DAY_DU` hay
    `N_TOI_THIEU` mà làm hỏng đặc tính thì test này đỏ.
    """
    luc = _mo_phong(pm.MUC_BAT_LOI, pm.SIGMA_ALPHA,
                    pm.N_TOI_THIEU, pm.N_DAY_DU, pm.Z_BIEN_HAI)
    loai_i = _mo_phong(0.0, pm.SIGMA_ALPHA,
                       pm.N_TOI_THIEU, pm.N_DAY_DU, pm.Z_BIEN_HAI)
    assert luc >= 0.70, (
        f"biên HẠI chỉ có lực {luc:.1%} ở mức {pm.MUC_BAT_LOI}%/lệnh — "
        f"dưới 70%. Ngưỡng phải bắt được mức bất lợi THỰC TẾ.")
    assert loai_i <= 0.10, (
        f"sai lầm loại I {loai_i:.1%} — trên 10%. Biên bị nhìn LIÊN TỤC "
        f"nên z phải nới rộng hơn 1,96; hiện z={pm.Z_BIEN_HAI}.")
    print(f"PASS  lực {luc:.1%} ở {pm.MUC_BAT_LOI}% · loại I {loai_i:.1%}")


def _mo_phong_ca_hai(mu: float, so_lan: int = 3000, tran: int = 1000,
                     seed: int = 20260901) -> float:
    """Tỷ lệ ĐÓNG qua CẢ HAI nhánh, đúng như `dieu_kien_dong_lai` đánh giá.

    `_mo_phong` ở trên chỉ chạy nhánh biên HẠI. Nhưng `N_DAY_DU` điều
    khiển nhánh ĐẢO GÁNH NẶNG, và đó chính là nhánh mà một thay đổi hằng
    số làm hỏng mà không nhánh kia hé ra điều gì.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    n = np.arange(1, tran + 1)
    tb = np.cumsum(rng.normal(mu, pm.SIGMA_ALPHA, size=(so_lan, tran)),
                   axis=1) / n
    se = pm.SIGMA_ALPHA / np.sqrt(n)
    hai = tb + pm.Z_BIEN_HAI * se < 0
    hai[:, :pm.N_TOI_THIEU - 1] = False
    ganh = ~(tb - pm.Z_LOI_THE * se > 0)
    ganh[:, :max(pm.N_TOI_THIEU, pm.N_DAY_DU) - 1] = False
    return float((hai | ganh).any(axis=1).mean())


def test_he_thong_THAT_SU_TOT_khong_bao_gio_bi_dong():
    """Một hệ thống +2%/lệnh phải KHÔNG BAO GIỜ bị đóng.

    Đây là đặc tính đắt nhất của điều kiện này, và là đặc tính mà một bản
    cập nhật nghe rất hợp lý phá mất. Ngày 01/09/2026 phép đo mới cho
    alpha −1,99%; đặt thẳng `MUC_BAT_LOI = −1.99` thì `N_DAY_DU` tụt còn
    130, nhánh đảo gánh nặng nổ khi mẫu còn quá nhỏ để chứng minh bất cứ
    điều gì, và mô phỏng cho **25,9%** — cứ bốn hệ thống xuất sắc thì một
    bị tắt.

    Không test nào cũ đỏ trước thay đổi đó: `_mo_phong` chỉ soi nhánh biên
    HẠI, mà nhánh hỏng là nhánh kia. Gác này đóng đúng lỗ đó.

    ĐIỂM MÙ, nói ra vì nó có thật: `_mo_phong_ca_hai` DỰNG LẠI logic chứ
    không gọi `dieu_kien_dong_lai`. Nó vì thế bắt được đột biến ở HẰNG SỐ
    mà không bắt được đột biến ở THÂN HÀM. Phần thân hàm do các test mục 3
    canh — chúng gọi hàm thật và kiểm cờ có đổi. Hai gác bù nhau, và không
    gác nào một mình đủ.
    """
    xau = _mo_phong_ca_hai(+2.0)
    assert xau <= 0.02, (
        f"hệ thống +2,0%/lệnh bị đóng {xau:.1%} số lần — trên 2%. "
        f"Bộ hằng số hiện tại (μ={pm.MUC_BAT_LOI} σ={pm.SIGMA_ALPHA} "
        f"N_DAY_DU={pm.N_DAY_DU} N_TOI_THIEU={pm.N_TOI_THIEU}) đang tắt "
        f"những hệ thống đáng lẽ phải được chạy tiếp.")

    khong_loi_the = _mo_phong_ca_hai(0.0)
    assert khong_loi_the >= 0.90, (
        f"μ=0 chỉ bị đóng {khong_loi_the:.1%} — dưới 90%. Vế đảo gánh nặng "
        f"tồn tại để một hệ thống KHÔNG có lợi thế bị dừng, chứ không được "
        f"chạy vô hạn vì chưa ai chứng minh được nó có hại.")
    print(f"PASS  +2,0% bị đóng {xau:.1%} · μ=0 bị đóng {khong_loi_the:.1%}")


def test_N_TOI_THIEU_phai_SUY_RA_tu_N_DAY_DU():
    """Kiểm HÌNH DẠNG, không kiểm giá trị.

    Bản cũ gõ tay `150` trong khi 596/4 = 149 — một con số làm tròn cho
    đẹp mắt lọt vào đúng chỗ đáng lẽ phải suy ra, và không gì kêu. Mọi đột
    biến trả về đúng 113 tại điểm này đều lọt qua một phép so giá trị.
    """
    cay = ast.parse((GOC / "paper_metrics.py").read_text(encoding="utf-8"))
    v = next(n.value for n in ast.walk(cay) if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "N_TOI_THIEU"
                     for t in n.targets))
    ten = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}
    assert "N_DAY_DU" in ten, (
        f"N_TOI_THIEU không suy ra từ N_DAY_DU — biểu thức chỉ nhắc {ten}")
    assert not isinstance(v, ast.Constant), "N_TOI_THIEU là hằng số gõ tay"
    print(f"PASS  N_TOI_THIEU suy từ N_DAY_DU (= {pm.N_TOI_THIEU})")


def test_nhin_lien_tuc_thi_z_phai_rong_hon_1_96():
    """Chứng minh vì sao z=2,30: đo loại I của chính z=1,96."""
    hep = _mo_phong(0.0, pm.SIGMA_ALPHA, pm.N_TOI_THIEU, pm.N_DAY_DU, 1.959964)
    rong = _mo_phong(0.0, pm.SIGMA_ALPHA, pm.N_TOI_THIEU, pm.N_DAY_DU,
                     pm.Z_BIEN_HAI)
    assert hep > rong, (hep, rong)
    assert hep > 0.09, (
        f"z=1,96 chỉ cho loại I {hep:.1%} — nếu thật thế thì lý do nới z "
        f"lên {pm.Z_BIEN_HAI} không còn đứng vững, phải viết lại chú thích")
    print(f"PASS  z=1,96 -> loại I {hep:.1%} · z={pm.Z_BIEN_HAI} -> {rong:.1%}")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
