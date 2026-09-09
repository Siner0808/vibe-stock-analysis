"""Walk-forward thật — bất biến 7 và 8.

VÌ SAO DỰNG LẠI
`walkforward_vn100.py` không còn làm walk-forward: nó chạy `run_simulation`
MỘT lần trên toàn khoảng rồi lọc `exit_date` để gọi là OOS, ngưỡng 50,0
nhập sẵn thay vì chọn trên in-sample, và mốc chia là `datetime.now() - 182
ngày` nên OOS luôn rơi vào giai đoạn gần nhất.

Bản ở `git show 025507c` có cấu trúc đúng (chọn trên IS, đo trên OOS) nhưng
vẫn lấy 6 tháng GẦN NHẤT làm OOS — trái bất biến 8: hàng trăm vòng loop đã
chạy trên toàn bộ cache kéo tới hôm nay, nên giai đoạn gần nhất là giai đoạn
ĐÃ BỊ NHÌN NHIỀU NHẤT.

CÁCH CHIA Ở ĐÂY KHÁC HẲN
Không chia theo ngày lịch. Chia theo **dữ liệu nào đã tồn tại khi các vòng
tối ưu chạy**: `docs/moc_du_lieu_sach.json` ghi, với mỗi mã, ngày bắt đầu
của cache TRƯỚC khi extend_history chạy ngày 20/08/2026. Mọi phiên trước mốc
đó là dữ liệu KHÔNG TỒN TẠI lúc ấy — nên không vòng nào *có thể* đã nhìn.

Đó là vùng kiểm định duy nhất trong dự án mà tính "chưa nhìn" **chứng minh
được**, thay vì giả định. Đo được: 25.219/80.939 phiên = 31,2%, trên 33/71 mã.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pandas as pd

import walkforward as wf


def _df(tu: str, den: str) -> pd.DataFrame:
    ngay = pd.bdate_range(tu, den).strftime("%Y-%m-%d")
    n = len(ngay)
    return pd.DataFrame({"time": ngay, "open": [10.0] * n, "high": [10.4] * n,
                         "low": [9.7] * n, "close": [10.1] * n,
                         "volume": [1_000_000] * n})


def test_hai_vung_KHONG_GIAO_NHAU_va_phu_het():
    """Gate 5D: A ∩ B = ∅. Đây là điều kiện nghiệm thu, không phải chi tiết."""
    df = _df("2022-01-03", "2026-08-20")
    oos, insample = wf.chia_vung(df, "2025-01-08")

    t_oos = set(oos["time"].astype(str))
    t_is = set(insample["time"].astype(str))
    assert t_oos & t_is == set(), f"{len(t_oos & t_is)} phiên nằm ở CẢ HAI vùng"
    assert t_oos | t_is == set(df["time"].astype(str)), "mất phiên khi chia"
    assert max(t_oos) < min(t_is), "vùng kiểm định KHÔNG nằm hoàn toàn ở quá khứ"
    print(f"PASS  OOS {len(t_oos)} phiên · IS {len(t_is)} phiên · giao = ∅")


def test_ma_khong_co_vung_sach_thi_OOS_rong():
    """34/71 mã đã có dữ liệu từ 2021-10 nên không đóng góp vùng sạch nào."""
    df = _df("2025-06-02", "2026-08-20")
    oos, insample = wf.chia_vung(df, "2025-01-08")
    assert len(oos) == 0 and len(insample) == len(df)
    print("PASS  mã không có vùng sạch -> OOS rỗng, không bịa ra mẫu")


def test_chon_nguong_KHONG_lay_dong_it_lenh_du_lai_cao_nhat():
    """Bất biến 7: dòng đáng tin nhất là dòng NHIỀU LỆNH nhất.

    Luật chọn phải nêu TRƯỚC: chỉ ngưỡng đạt tối thiểu số lệnh mới đủ tư
    cách. Không có luật đó thì "chọn trên in-sample" chỉ là cực đại của N
    lần thử dưới một cái tên khác.
    """
    ket_qua = [
        {"nguong": 45.0, "so_lenh": 120, "ky_vong": 0.8},
        {"nguong": 50.0, "so_lenh": 90, "ky_vong": 1.1},
        {"nguong": 62.0, "so_lenh": 4, "ky_vong": 9.9},   # bẫy
    ]
    chon = wf.chon_nguong(ket_qua, toi_thieu_lenh=30)
    assert chon == 50.0, f"chọn {chon} — dòng 4 lệnh lãi 9,9% là nhiễu"
    print("PASS  ngưỡng ít lệnh bị loại dù kỳ vọng cao nhất")


def test_khong_du_lenh_o_dau_thi_TRA_None_chu_khong_doan():
    ket_qua = [{"nguong": 50.0, "so_lenh": 5, "ky_vong": 3.0}]
    assert wf.chon_nguong(ket_qua, toi_thieu_lenh=30) is None
    print("PASS  không ngưỡng nào đủ mẫu -> trả None, không đoán bừa")


def test_moc_sach_doc_duoc_va_co_provenance():
    moc = wf.nap_moc_sach()
    assert len(moc) >= 60, f"chỉ đọc được {len(moc)} mã"
    assert all(isinstance(v, str) and len(v) == 10 for v in moc.values())
    print(f"PASS  đọc được mốc sạch cho {len(moc)} mã")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()


def test_mo_phong_bao_alpha_va_trang_thai_bo_nho():
    """`_mo_phong` phải trả về ALPHA và tình trạng bộ nhớ, không chỉ lãi/lỗ.

    Trước 21/08/2026 nó chỉ trả kỳ vọng, win rate và lợi nhuận cộng dồn —
    tức trả lời "lãi hơn 0 không". Câu cần trả lời là "giỏi hơn cầm đều cả
    rổ không" (bất biến 6). Trong thị trường đi lên, hai câu đó cho hai câu
    trả lời rất khác nhau, và công cụ đo ngoài mẫu mà không in ra cái quyết
    định thì người đọc sẽ đọc cái còn lại.

    Test này KHÔNG khẳng định alpha bằng bao nhiêu — dữ liệu giả, giá phẳng,
    nên số nào cũng vô nghĩa. Nó chỉ khoá việc các trường đó CÓ MẶT và mang
    nhãn tự nói ra khi chưa đo được.
    """
    import os

    du_lieu = {"AAA": _df("2024-01-01", "2024-05-01"),
               "BBB": _df("2024-01-01", "2024-05-01")}
    db = "test_mo_phong_tam.db"
    bo_nho = "wf_bo_nho_test_tam.json"
    try:
        r = wf._mo_phong(du_lieu, 50.0, db, stride=20, min_history=60,
                         che_do_hoc="tich_luy", duong_bo_nho=bo_nho)

        for khoa in ("alpha", "alpha_ktc", "alpha_so_lenh", "alpha_bo_qua",
                     "alpha_ket_luan", "che_do_hoc", "mau_dau",
                     "mau_hoc_them"):
            assert khoa in r, f"thiếu trường {khoa!r} trong kết quả"

        assert r["che_do_hoc"] == "tich_luy"
        assert r["mau_dau"] == 0, "tich_luy phải bắt đầu từ bộ nhớ rỗng"
        assert r["alpha"] is not None or r["alpha_ket_luan"], (
            "alpha None mà không nói lý do — đọc như 'không có alpha' thay "
            "vì 'chưa đủ mẫu'")
        print("PASS  _mo_phong báo alpha và tình trạng bộ nhớ")
    finally:
        from paper_runner import _xoa_cache_phan_tich
        from post_mortem_learning import MEMORY_FILE, dat_lai_engine
        dat_lai_engine(MEMORY_FILE)
        _xoa_cache_phan_tich()
        for f in (db, bo_nho):
            if os.path.exists(f):
                os.remove(f)


def test_bao_cao_OOS_in_DU_moi_truong_hop_dong_BAT_bao_cao():
    """Điều khoản "Phải báo cáo KÈM" của `docs/TIEU-CHI-DOC-TRUOC.md`.

    VÌ SAO TEST NÀY TỒN TẠI, và vì sao nó KHÁC
    `test_mo_phong_bao_alpha_va_trang_thai_bo_nho` ở trên:

    Test kia khoá các trường CÓ MẶT trong dict `_mo_phong` trả về. Ngày
    09/09/2026 nó vẫn xanh trong khi `alpha_so_lenh` **chưa bao giờ được
    in ra**. Bốn lượt của ĐO 1 chạy hết 157,7 phút rồi mới lộ ra rằng con
    số hợp đồng bắt báo cáo không có trong log.

    Một trường nằm trong dict mà không đi ra tới người đọc thì với người
    đọc nó không tồn tại. Nên phải khoá cả hai đầu: có trong kết quả, VÀ
    có trong báo cáo.

    Test kiểm GIÁ TRỊ chứ không kiểm nhãn. Nhãn còn nguyên mà in nhầm
    trường khác thì phép kiểm nhãn vẫn xanh — đúng hình dạng "test kiểm
    lại chính nó" đã cắn dự án ba lần ngày 31/08/2026.
    """
    o = {"so_lenh": 4111, "ky_vong": 1.11, "win_rate": 22.2, "net_pct": 3.33,
         "alpha": -0.44, "alpha_ktc": (-1.55, 0.66),
         "alpha_ket_luan": "khong khac chuan",
         "alpha_so_lenh": 3907, "alpha_bo_qua": 204,
         "mau_dau": 88, "mau_hoc_them": 0, "che_do_hoc": "co_san",
         "von_tb": 51.0, "von_dinh": 137.0}
    bao = "\n".join(wf.dong_bao_cao_oos(o))

    for nhan, gia_tri in (("so_lenh", "4111"), ("alpha_so_lenh", "3907"),
                          ("alpha_bo_qua", "204"), ("von_tb", "51%"),
                          ("von_dinh", "137%"), ("mau_dau", "88")):
        assert gia_tri in bao, (
            f"{nhan} = {gia_tri} không có trong báo cáo OOS. Hợp đồng "
            f"docs/TIEU-CHI-DOC-TRUOC.md bắt báo cáo KÈM trường này.")

    assert "137%" in bao and "vượt 100%" in bao, (
        "vốn đỉnh 137% mà không có cảnh báo đòn bẩy trá hình (bất biến 7b)")

    o0 = dict(o, alpha_bo_qua=0, von_dinh=99.0)
    bao0 = "\n".join(wf.dong_bao_cao_oos(o0))
    assert "cặp ngày: 0" in bao0, (
        "bỏ 0 lệnh vẫn phải in ra. Dòng vắng mặt làm người đọc không "
        "phân biệt được 'bằng 0' với 'không ai đo'.")
    assert "vượt 100%" not in bao0, "vốn đỉnh 99% mà vẫn cảnh báo đòn bẩy"
    print("PASS  báo cáo OOS in đủ mọi trường hợp đồng bắt báo cáo")
