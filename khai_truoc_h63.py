"""
khai_truoc_h63.py
BẢN KHAI TRƯỚC cho phép kiểm đảo chiều tại ô J=21, h=63.

FILE NÀY KHÔNG CHỨA KẾT QUẢ, VÀ ĐÓ LÀ ĐIỂM CHÍNH
────────────────────────────────────────────────
Nó được commit MỘT MÌNH, trước khi có thêm dữ liệu. Kết quả sẽ nằm ở một
commit sau. Lịch sử git vì thế chứng minh được thứ tự — không ai phải tin
lời hứa. Cùng cách làm đã dùng ở BƯỚC 9 (`51adc88`).

VÌ SAO Ô NÀY CẦN MỘT BẢN KHAI RIÊNG
───────────────────────────────────
BƯỚC 9 chạy năm ô cùng lúc. Ô duy nhất cho ra "ĐẠT" là h=63 — và nó đã
được khai trước là KHÔNG ĐỌC ĐƯỢC vì thiếu lực. Con số:

    rho quan sát   −0,0349
    sàn nhiễu 5%   −0,0265        (hoán vị)
    ngưỡng trực tiếp −0,0275      (hiệu chuẩn 2.000 lần)
    rào hoà vốn      0,025
    Bonferroni 5 ô (2 phía, α=0,01): cần vượt −0,0430  ->  KHÔNG vượt

Bản khai trước của BƯỚC 9 là thứ duy nhất chặn con số ấy thành "một phát
hiện". Muốn đọc được ô này thì phải kiểm nó **một mình**, trên dữ liệu
chưa dùng, theo luật viết ra TRƯỚC.

════════════════════════════════════════════════════════════════════════
ĐIỂM THIẾT KẾ KHÔNG PHẢI LÀ GIÁ TRỊ ĐÃ QUAN SÁT — đây là chỗ dễ sai nhất
════════════════════════════════════════════════════════════════════════
Ngày 02/09/2026, `docs/STATE.md` ghi ô này "cần ~1,3× dữ liệu". Con số đó
tính lực so với **−0,0349**, tức so với chính giá trị quan sát được. Mà
giá trị ấy là **cực đại của năm ô** — nó mang sẵn phần thắng của phép tìm
kiếm (winner's curse) và gần như chắc chắn lớn hơn hiệu ứng thật.

Neo lực vào nó là tự cho mình một phép kiểm dễ: chọn cỡ mẫu vừa đủ để bắt
đúng con số đã nhìn thấy thì kiểu gì cũng "vừa đủ".

Đây đúng là lỗi mà `paper_metrics.MUC_BAT_LOI` đã tránh ngày 01/09: ở đó
ước lượng điểm là −1,99 nhưng điểm thiết kế lấy cận trên −0,92, vì **điểm
thiết kế phải là hiệu ứng NHỎ NHẤT còn đáng quan tâm**, không phải hiệu
ứng đã đo.

Ở đây, hiệu ứng nhỏ nhất còn đáng quan tâm là **rào hoà vốn**: dưới mức
ấy thì dù tương quan có thật cũng không bù nổi chi phí thực thi, nên biết
hay không biết đều không đổi hành động nào.

    điểm thiết kế = −(rào hoà vốn tại h=63) = −0,025

Giá phải trả, và nêu ra chứ không giấu: cần **3,73×** dữ liệu thay vì
1,83×. Phép kiểm khó hơn hẳn. Đó là phép kiểm đúng.

════════════════════════════════════════════════════════════════════════
HAI PHÍA, KHÔNG PHẢI MỘT PHÍA
════════════════════════════════════════════════════════════════════════
Giả thuyết có hướng (đảo chiều ⇒ rho âm), và hướng ấy đã được khai trong
`experiment_dao_chieu.phan_xu` TRƯỚC khi thấy bất kỳ kết quả h=63 nào. Về
lý thuyết, một phía là hợp lệ.

Vẫn chọn hai phía. Lý do: **dữ liệu này đã bị nhìn một lần rồi**, và nhìn
đúng theo chiều đó. Một phía sau khi đã nhìn là thứ không cãi được với
người đọc hoài nghi, kể cả khi nó đúng về hình thức. Mất lực (2,94× →
3,73×) là giá của việc không phải tranh cãi.

Luật dấu của BƯỚC 9 giữ nguyên và vẫn nằm trong `phan_xu`: **rho DƯƠNG có
ý nghĩa là BÁC BỎ giả thuyết đảo chiều**, không phải "tìm thấy tín hiệu".

════════════════════════════════════════════════════════════════════════
ĐIỀU KIỆN CHẠY — phép kiểm này CHƯA ĐƯỢC PHÉP CHẠY
════════════════════════════════════════════════════════════════════════
`du_dieu_kien_chay()` là cổng. Chừng nào sd của phân phối null chưa co
xuống mức khai dưới đây thì lượt chạy phải DỪNG, không phải chạy rồi ghi
chú "thiếu lực" — BƯỚC 7 đã làm đúng thế và chính nhãn ấy về sau bị nghi
ngờ khi phát hiện công thức `n/(h+1)` hụt 3,5 lần.

ĐO SD NULL, ĐỪNG SUY TỪ CÔNG THỨC. `n_eff = n/(h+1)` cho 1.104 ở h=63
trong khi đo trực tiếp ra 3.906 — hụt 3,5×. Mọi con số lực ở đây tính từ
sd null **đo được** (2.000 lượt hiệu chuẩn), không từ công thức.

ĐƯỜNG LẤY THÊM DỮ LIỆU: mở rộng SỐ MÃ, không phải chờ thêm thời gian.
Chuỗi hiện tại trải ~5 năm; nhân 3,73 lần theo trục thời gian là chờ tới
những năm 2040. Trục cắt ngang thì mở được ngay — rổ hiện là 68 mã sau
lọc, và sàn Việt Nam có hàng trăm mã đủ thanh khoản.

CẢNH BÁO ĐI KÈM, phải đọc trước khi mở rộng rổ: thêm mã làm tăng n nhưng
cũng đổi TỔNG THỂ đang đo. Rổ mới phải được khai trước bằng một luật máy
móc (ví dụ: mọi mã HOSE có trung vị GTGD 250 phiên trên một ngưỡng nêu
trước), KHÔNG phải chọn tay. Chọn tay rồi đo là mở lại đúng cánh cửa mà
bất biến 7 đóng.
"""
from __future__ import annotations

from statistics import NormalDist

#: Ô DUY NHẤT được kiểm. Một ô, nên không có hiệu chỉnh đa phép so.
J_KIEM, H_KIEM = 21, 63

#: Hai phía — xem phần đầu file. Không đổi thành một phía để "đủ lực".
HAI_PHIA = True
ALPHA = 0.05
LUC_MUC_TIEU = 0.80

#: Rào hoà vốn tại h=63, đo BƯỚC 9. Lượt chạy thật phải tính lại bằng
#: `experiment_tran_dac_trung.rao_hoa_von()` trên chính dữ liệu của nó và
#: DỪNG nếu lệch quá 20% so với con số này — rào đổi nghĩa là chi phí hoặc
#: phân phối nhãn đã đổi, và khi đó bản khai này nói về một bài toán khác.
RAO_HOA_VON_H63 = 0.025
LECH_RAO_TOI_DA = 0.20

#: ĐIỂM THIẾT KẾ. Hiệu ứng NHỎ NHẤT còn đáng quan tâm, KHÔNG phải hiệu
#: ứng đã đo (−0,0349). Suy ra từ rào, không gõ tay.
DIEM_THIET_KE = -RAO_HOA_VON_H63

#: Phân phối null ĐO ĐƯỢC ở BƯỚC 9 (2.000 lượt hiệu chuẩn trực tiếp).
#: KHÔNG suy từ `n/(h+1)` — công thức đó hụt 3,5× ở nhịp này.
NULL_TB = -0.0018
NULL_SD_HIEN = 0.0160

#: Giá trị quan sát ở BƯỚC 9. Ghi lại để đối chiếu, và CỐ Ý không dùng vào
#: bất kỳ phép tính lực nào — xem phần đầu file.
RHO_DA_QUAN_SAT = -0.0349

_Z = NormalDist()


def _z_toi_han() -> float:
    return _Z.inv_cdf(1 - ALPHA / 2) if HAI_PHIA else _Z.inv_cdf(1 - ALPHA)


def nguong_bac_bo(null_sd: float = NULL_SD_HIEN) -> float:
    """Ngưỡng phía ÂM. rho phải nhỏ hơn giá trị này mới có ý nghĩa."""
    return NULL_TB - _z_toi_han() * null_sd


def sd_null_can() -> float:
    """sd null tối đa còn cho `LUC_MUC_TIEU` tại `DIEM_THIET_KE`."""
    return abs(DIEM_THIET_KE - NULL_TB) / (
        _z_toi_han() + _Z.inv_cdf(LUC_MUC_TIEU))


def boi_du_lieu_can() -> float:
    """Phải nhân cỡ mẫu hiệu dụng lên bao nhiêu lần. SUY RA, không gõ."""
    return (NULL_SD_HIEN / sd_null_can()) ** 2


def luc_tai(mu: float, null_sd: float = NULL_SD_HIEN) -> float:
    """Xác suất bác bỏ được null nếu hiệu ứng thật đúng bằng `mu`."""
    return _Z.cdf((nguong_bac_bo(null_sd) - mu) / null_sd)


def du_dieu_kien_chay(null_sd_moi: float, rao_moi: float) -> tuple[bool, str]:
    """CỔNG. Phép kiểm chỉ được chạy khi cả hai điều kiện thoả.

    Trả `(được_chạy, lý_do)`. Không đủ lực thì DỪNG — không chạy rồi dán
    nhãn "thiếu lực". BƯỚC 7 đã làm đúng thế, và về sau chính cái nhãn ấy
    hoá ra dựa trên một công thức hụt 3,5 lần, nên không ai còn biết ô nào
    thật sự thiếu lực. Một phép kiểm đã chạy thì con số của nó tồn tại và
    sẽ được đọc, dù có dán nhãn gì lên.
    """
    if rao_moi <= 0:
        return False, "rào hoà vốn không dương — dữ liệu hoặc chi phí sai."
    lech = abs(rao_moi - RAO_HOA_VON_H63) / RAO_HOA_VON_H63
    if lech > LECH_RAO_TOI_DA:
        return False, (
            f"Rào hoà vốn nay {rao_moi:.4f}, lệch {lech:.0%} so với "
            f"{RAO_HOA_VON_H63:.4f} lúc khai (trần {LECH_RAO_TOI_DA:.0%}). "
            f"Chi phí hoặc phân phối nhãn đã đổi — bản khai này nói về một "
            f"bài toán khác. Viết bản khai mới.")
    can = sd_null_can()
    if null_sd_moi > can:
        return False, (
            f"sd null {null_sd_moi:.5f} còn lớn hơn mức cần {can:.5f}. "
            f"Lực tại điểm thiết kế {DIEM_THIET_KE:+.4f} mới đạt "
            f"{luc_tai(DIEM_THIET_KE, null_sd_moi):.1%}, cần "
            f"{LUC_MUC_TIEU:.0%}. Cần nhân cỡ mẫu hiệu dụng "
            f"{(null_sd_moi / can) ** 2:.2f}× nữa. CHƯA ĐƯỢC CHẠY.")
    return True, (f"Đủ lực: sd null {null_sd_moi:.5f} ≤ {can:.5f}, "
                  f"lực {luc_tai(DIEM_THIET_KE, null_sd_moi):.1%} tại "
                  f"{DIEM_THIET_KE:+.4f}.")


def phan_xu(rho: float, null_sd: float = NULL_SD_HIEN) -> str:
    """Luật phán xử, viết TRƯỚC để nó không trôi theo con số nhìn thấy.

    Bốn kết cục, và kết cục thứ hai là kết cục thường gặp nhất. Không có ô
    nào cho "gần có ý nghĩa" — đó là chỗ mọi kết luận mềm chui vào.

    ĐIỀU KHOẢN RÀO HOÀ VỐN HÔM NAY LÀ CHỮ CHẾT, CÓ CHỦ ĐÍCH. Ở sd hiện
    nay (0,0160) ngưỡng bác bỏ là −0,0332, đã nằm ngoài rào 0,025 — nên
    mọi kết quả có ý nghĩa đều tự động trên rào và nhánh ấy không chạm
    tới được. Ở sd lúc đủ lực (0,00828) ngưỡng thành −0,0180 và khoảng
    (0,0180 ; 0,025) mở ra: có ý nghĩa thống kê mà không bù nổi chi phí.
    Điều khoản sống dậy đúng vào ngày phép kiểm được phép đọc, và phải
    được viết TỪ BÂY GIỜ chứ không phải lúc đó.
    """
    nguong = nguong_bac_bo(null_sd)
    if rho > -NULL_TB + _z_toi_han() * null_sd:
        return "NGƯỢC DẤU — động lượng, BÁC BỎ giả thuyết đảo chiều"
    if rho >= nguong:
        return "KHÔNG bác bỏ được null — không có đảo chiều đọc được"
    if abs(rho) < RAO_HOA_VON_H63:
        return "có ý nghĩa nhưng DƯỚI rào hoà vốn — không hành động được"
    return "ĐẠT — âm có ý nghĩa VÀ trên rào hoà vốn"
