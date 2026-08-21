> ⛔ **ĐÍNH CHÍNH (21/08/2026) — đọc trước khi trích bất cứ con số nào.**
>
> Hai chỗ trong tài liệu này không dùng được:
>
> 1. **alpha `+0,428%` là SAI.** Chạy lại trên đúng 408 lệnh đó, mọi cách
>    dựng rổ chuẩn đều cho alpha từ **−0,160%** đến **+0,247%**. Muốn có
>    +0,428% thì rổ chuẩn phải lãi ≈ 0,003%, tức gần như đứng yên — dữ liệu
>    không chống đỡ điều đó. Kỳ vọng `+0,431%` thì đúng và tái lập được.
>
> 2. **Phụ lục A/B về cơ chế học không dùng được.** Bảy lượt dò ngưỡng khi
>    đó dùng chung một bộ nhớ đang lớn dần (`_ENGINE_CACHE` là một engine
>    cho cả tiến trình), nên chúng không độc lập — đúng thứ bất biến 7 cấm.
>
> Cả hai đã đo lại trong **`ket-qua-bo-nho-rieng-20260821.md`**. Phần còn
> lại của tài liệu này — dải in-sample, cách chia vùng, số lệnh — vẫn đúng.

# Kết quả walk-forward — 20/08/2026

Phép đo đầu tiên của dự án trên vùng dữ liệu **chứng minh được là chưa từng
dùng để chọn tham số**. Chạy bằng `walkforward.py`, 8,1 phút.

## Cách chia vùng

Không chia theo ngày lịch. Chia theo **dữ liệu nào đã tồn tại khi các vòng
tối ưu chạy** — xem `docs/moc_du_lieu_sach.json`.

```
IS  (chọn ngưỡng) : 71 mã · phiên >= mốc  ← vùng đã bị nhìn
OOS (đo)          : 33 mã · phiên <  mốc  ← 25.219 phiên KHÔNG TỒN TẠI
                                             trong cache lúc tối ưu chạy
```

## Dải in-sample

| ngưỡng | lệnh | kỳ vọng | win rate | vốn đỉnh |
|---|---|---|---|---|
| 45 | 2200 | +0,30% | 26,8% | 1372,8% |
| 48 | 2008 | +0,38% | 27,7% | 1346,3% |
| 50 | 1841 | +0,52% | 28,3% | 1330,7% |
| 52 | 1683 | +0,56% | 28,7% | 1339,3% |
| 55 | 1418 | +0,82% | 29,5% | 1332,0% |
| 58 | 1188 | +1,00% | 30,1% | 1345,9% |
| **62** | **871** | **+1,52%** | **32,3%** | 1261,9% |

Ngưỡng chọn theo luật nêu trước (≥30 lệnh, rồi kỳ vọng cao nhất): **62,0**.

> **Đính chính một kết luận trước đó.** Ngày 20/08 tôi đo trên 8 sổ còn sót
> của lần chạy 20 vòng và kết luận *"win rate phẳng 28,2–30,7%, ngưỡng không
> cải thiện chất lượng chọn mã"*. Trên vùng IS này thì **không phẳng**: WR
> tăng đều 26,8% → 32,3% và kỳ vọng tăng đều +0,30% → +1,52% khi ngưỡng đi
> từ 45 lên 62. Kết luận đúng phải là: ngưỡng **có** cải thiện chất lượng
> **trong mẫu** — nhưng phần cải thiện đó **không sống sót ra ngoài mẫu**.

## Đo trên out-of-sample — ngưỡng 62

```
số lệnh                 408          (bỏ sót 0 lệnh khi đối chiếu)
kỳ vọng mỗi lệnh        +0,431%      KTC 95% [−0,469% ; +1,407%]  ← chứa 0
win rate                25,5%        (trong mẫu ở ngưỡng này: 32,3%)
alpha khớp từng lệnh    +0,428%      ← SAI, xem đính chính đầu file
vốn triển khai          151% trung bình · 542% đỉnh
lợi nhuận cộng dồn      +36,14%
quy về 100% vốn         +23,92%      (chia cho bội số 1,51×)
```

**Con số dùng được là alpha, không phải +36,14%.** Cộng dồn ở trên là lợi
nhuận của một tài khoản vay được — bất biến 7b.

## Kết luận

Kỳ vọng trong mẫu +1,52% rơi xuống **+0,43%** ngoài mẫu — mất 72%. Win rate
rơi từ 32,3% xuống 25,5%. Đó là dạng suy giảm kinh điển của tham số chọn
trên chính dữ liệu đo.

Và alpha khớp từng lệnh **chứa số 0**: chiến lược không phân biệt được với
việc cầm đều cả rổ trong cùng khoảng thời gian.

Đây là phép đo **thứ tư** cho cùng một câu trả lời, và là phép đo **chính
xác nhất** trong bốn:

| Phép đo | Mẫu | Kết quả | KTC |
|---|---|---|---|
| rho điểm ↔ lợi nhuận 20 phiên | 573 phiên | −0,019 | [−0,100 ; +0,064] |
| alpha in-sample (sổ 113 lệnh) | 112 lệnh | +0,090% | [−1,166 ; +1,391] |
| alpha OOS 07/08/2026 | 108 lệnh | −0,63% | [−2,09 ; +0,84] |
| **alpha OOS 20/08/2026** | **408 lệnh** | **+0,428%** | **[−0,375 ; +1,275]** |

Khoảng tin cậy lần này **hẹp nhất** (±0,82 so với ±1,5 và ±1,5) vì mẫu lớn
nhất. Hẹp hơn mà vẫn chứa 0 nghĩa là: nếu có lợi thế thì nó nhỏ hơn mức mà
408 lệnh phân biệt được.

## Hai hạn chế phải ghi kèm

1. **Vùng OOS không phải lát cắt ngẫu nhiên.** 33 mã đóng góp nó là những mã
   trước đây chỉ có dữ liệu từ 2025 — tức nhóm được thêm vào cache muộn.
   Chúng có thể khác hệ thống về quy mô hoặc thanh khoản.
2. **Thiên lệch sống sót vẫn còn.** Rổ 71 mã là ảnh chụp 08/2026; mã đã rớt
   khỏi rổ không có mặt. Đây là hạn chế `NGUYEN-TAC-DO-LUONG.md` đã ghi là
   **cố ý chưa xử lý** vì dự án chưa có dữ liệu lịch sử thành phần rổ.

## Điều này nói gì cho ô C5

Walk-forward **đã sinh ra được một ngưỡng chọn hợp lệ: 62**. Nhưng phép đo
ngoài mẫu của chính ngưỡng đó cho alpha chứa 0.

Nên câu trả lời cho C5 **không đổi**: để trống, dừng mở vị thế mới. Khác
biệt là bây giờ đó là kết luận **có bằng chứng**, không phải trạng thái chờ.

---

# Phụ lục — cơ chế học có giúp gì không?

Chạy lại **cùng một walk-forward**, chỉ khác một biến: post-mortem TẮT hay BẬT.

| | TẮT | BẬT |
|---|---|---|
| ngưỡng chọn trên IS | 62,0 | 55,0 |
| lệnh IS ở ngưỡng đó | 871 | 731 |
| **lệnh OOS** | **408** | **292** |
| win rate OOS | 25,5% | 28,1% |
| **alpha** | **+0,428%** | **+0,288%** |
| **KTC 95%** | **[−0,375 ; +1,275]** | **[−0,638 ; +1,278]** |
| kết luận | không khác chuẩn | không khác chuẩn |
| thời gian chạy | 8,1 phút | 31,2 phút |

## Đọc bảng này

**Không có bằng chứng cơ chế học giúp được gì.** Trên mọi chiều đo, bật nó
làm mọi thứ *hơi tệ hơn hoặc không đổi*:

- điểm ước lượng alpha **thấp hơn** (+0,288% so với +0,428%)
- khoảng tin cậy **rộng hơn** (±0,96 so với ±0,82), vì mẫu nhỏ hơn
- số lệnh OOS **giảm 28%** (408 → 292) — bộ nhớ chủ yếu làm việc *chặn bớt*
- chi phí tính toán **gấp gần 4 lần**

Nói cho công bằng: hai khoảng tin cậy chồng lấn gần như hoàn toàn, nên cũng
**không kết luận được rằng nó gây hại**. Kết luận đúng là: *không phân biệt
được với việc không có nó* — trong khi tốn gấp 4 lần thời gian.

## Một chi tiết đáng chú ý

Với post-mortem **TẮT**, kỳ vọng trên IS tăng **đơn điệu** theo ngưỡng:

```
+0,30 → +0,38 → +0,52 → +0,56 → +0,82 → +1,00 → +1,52
```

Với post-mortem **BẬT**, nó hết đơn điệu:

```
+0,59 → +0,83 → +0,88 → +0,70 → +0,91 → +0,88 → +0,59
```

Một quan hệ đơn điệu bị bẻ thành răng cưa là dấu hiệu **thêm nhiễu**, không
phải thêm tín hiệu.

## Hạn chế của chính phép đo này

Sổ tạm không phải sổ thật nên `save_memory()` không chạy — bộ nhớ **giữ
nguyên 44 mẫu** suốt lượt. Nên bảng trên trả lời *"bộ nhớ hiện có giúp gì
không"*, **không** phải *"việc tích luỹ thêm giúp gì không"*.

Câu hỏi thứ hai cần bộ nhớ riêng cho mỗi lượt backtest, và cần đủ lệnh để
tích luỹ có ý nghĩa. Với 44 mẫu sau ~2 năm, đó là câu hỏi của nhiều năm nữa,
không phải của tuần này.
