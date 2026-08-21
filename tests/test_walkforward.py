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
