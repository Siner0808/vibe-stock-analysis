# Tiêu chí đọc — khai TRƯỚC khi chạy

> **Vì sao có file này.** Bất biến 7 và 8 cấm chọn quy tắc sau khi đã nhìn
> số. Cách duy nhất thi hành được điều đó là **viết tiêu chí ra, commit,
> rồi mới chạy** — để nó không thể sửa sau. File này là hợp đồng, không
> phải ghi chú.
>
> Mỗi mục dưới đây phải được người dùng chốt trước khi lượt chạy tương ứng
> bắt đầu. Khai ngày nào thì ghi ngày ấy.

---

## Đính chính trước tiên: "~2,5 giờ mỗi lượt" là con số CHƯA AI ĐO

Ngày 08/09/2026 tôi nhắc con số ấy nhiều lần như một sự thật. Đo lại:

```
grep -rn "2,5 giờ|2,5h|150 phút" --include=*.md .   ->  KHONG CO trong repo
walkforward.py:167  # `che_do_hoc="tat"` đi từ 8,1 lên 27,7 phút.
```

Số đo **duy nhất** có trong mã là **8,1–27,7 phút** cho một lượt (khác nhau
tuỳ cache phân tích được dùng lại hay không). Con số 2,5 giờ đến từ một
dòng bàn giao, không từ một lượt chạy.

Đây đúng là `references/loi-da-mac.md` **lỗi 16** — chép một kết luận rồi
phát ra như phép đo của mình — và nó lặp lại **trong cùng ngày** tôi viết
lỗi 16 vào skill.

**Hệ quả cho quyết định:** chi phí thật của các lượt đo dưới đây chưa biết.
Lượt đầu tiên phải **đo và ghi thời gian chạy thật của chính nó**, và con
số ấy mới được dùng để lập kế hoạch cho các lượt sau.

---

## ĐO 1 — Bảng "CHI PHÍ THỰC THI" ở cấu hình hiện hành

### Vì sao cần

`CLAUDE.md` mục CHI PHÍ THỰC THI có một bảng số đã được đánh dấu **lạc
hậu**: dòng BẬT ghi `alpha −0,927%`, `KTC [−1,689; −0,076] LOẠI 0` — kết
quả có ý nghĩa thống kê duy nhất dự án từng có. Nó đo trên mã ngày 31/08,
ở **vốn cam kết trung bình 138,66%**, tức đòn bẩy 1,39 lần — đúng thứ bất
biến 7b bắt phải chia ra rồi đo lại.

Đo lại 04/09 trên HEAD ở chế độ mặc định: **379 lệnh · alpha −0,676% · KTC
[−1,470; +0,211] — CHỨA 0.** Nên hiện dự án **không có kết quả nào loại
được số 0**, và bảng trong tài liệu vẫn là bảng cũ.

### Chạy gì

Bốn lượt: hai công tắc × hai chế độ mô phỏng.

| # | `MO_PHONG_TRUOT_GIA` | chế độ | lệnh |
|---|---|---|---|
| 1 | `True` (hiện hành) | theo mã (mặc định) | `walkforward.py` |
| 2 | `True` | theo ngày | `walkforward.py --theo-ngay` |
| 3 | `False` | theo mã | qua script đặt cờ trước khi gọi `chay()` |
| 4 | `False` | theo ngày | như trên, kèm `theo_ngay=True` |

`stride` và `min_history` giữ **nguyên mặc định** (2 và 60) ở cả bốn lượt —
đổi chúng là đổi câu hỏi, xem ĐO 2.

Công tắc ở `paper_trading.py:329`, không có biến môi trường ghi đè, nên
lượt 3–4 đặt cờ trong một **script chạy** chứ **không sửa mã nguồn**.

### Đại lượng chính, và nó là DUY NHẤT

**`alpha` cùng `alpha_ktc` trên vùng OOS**, ở ngưỡng do chính lượt chạy
chọn trên IS. Không phải `ky_vong`, không phải `net_pct`, không phải
`win_rate` — bất biến 6.

### Ba kết cục, và hành động cho từng cái

| Kết cục | Nghĩa | Hành động đã cam kết |
|---|---|---|
| **A · cận TRÊN của KTC < 0** | alpha âm một cách đo được | Cổng C5 **giữ đóng**. Thay bảng số trong `CLAUDE.md` bằng số mới. Ngừng dò ngưỡng — dò thêm là đo độ may của phép tìm kiếm (bất biến 7). |
| **B · KTC chứa 0** | không phân biệt được với rổ chuẩn | Cổng C5 **giữ đóng**, theo đúng tinh thần "đảo gánh nặng" đã nằm sẵn trong `paper_metrics.dieu_kien_dong_lai()`. Thay bảng số. **Không đổi một tham số nào.** |
| **C · cận DƯỚI của KTC > 0** | alpha dương đo được | **KHÔNG mở cổng.** Đây là chiều đáng ngờ nhất — quy tắc số 1. Bắt buộc bốn phép kiểm ở mục dưới TRƯỚC khi tin con số. |

Kết cục C là chỗ file này tồn tại. Dự án đã **năm lần** cho ra số đẹp rồi
hoá ra vô nghĩa, và cả năm lần đều nghiêng về phía đẹp lên.

### Bốn phép kiểm bắt buộc khi gặp kết cục C

1. **`von_tb` ≤ 100%.** Vượt là đòn bẩy trá hình (bất biến 7b) — chia tỷ
   trọng cho đúng bội số rồi đo lại, con số cũ **không đọc được**.
2. **Chạy lại lần thứ hai, cùng lệnh, phải ra số y hệt** (bất biến 2).
   Lệch một chữ số là có trạng thái rò rỉ giữa hai lượt.
3. **`alpha_bo_qua` so với `so_lenh`.** Bao nhiêu lệnh bị loại vì không
   khớp được cặp ngày với rổ chuẩn. Bỏ qua nhiều thì alpha nói về một tập
   con, không nói về chiến lược.
4. **`so_ma_oos`.** Vùng OOS có bao nhiêu mã. Bản đo 07/08/2026 chỉ có
   22/50 mã trong vùng kiểm định — kết quả khi ấy nói về 22 mã đó.

### Phải báo cáo KÈM, không được tách rời

Mỗi dòng kết quả đi kèm: `so_lenh` · `von_tb` · `von_dinh` ·
`alpha_so_lenh` · `alpha_bo_qua` · `so_ma_is` · `so_ma_oos` · **thời gian
chạy thật**.

Trong dải kết quả, **dòng đáng tin nhất là dòng có nhiều lệnh nhất**,
không phải dòng alpha cao nhất (bất biến 7).

### Điều KHÔNG được làm sau khi thấy số

- Đổi ngưỡng, đổi `stride`, đổi `min_history`, đổi rổ mã, rồi chạy lại tới
  khi số đẹp hơn. Đó là bất biến 7 và 8.
- Chọn dòng có alpha cao nhất trong dải IS rồi gọi nó là kết quả.
- Mở cổng C5 vì một kết quả backtest. Cổng C5 đóng/mở theo
  `dieu_kien_dong_lai()` trên **lệnh tiến-về-trước đã đóng** (nay n = 1),
  không theo walk-forward.

---

## ĐO 2 — `stride=1`: câu hỏi hiện tại KHÔNG trả lời được

### Vì sao nó được nêu ra

`CLAUDE.md` ghi: backtest khớp ở **T+2**, đường chạy thật khớp ở **T+1**.
Đo trên sổ thật: 43/43 lệnh mô phỏng đúng T+2, 4/4 lệnh tiến-về-trước đúng
T+1. Chưa ai đo việc lệch ấy đổi kết quả bao nhiêu.

### Vì sao chạy `--stride 1` KHÔNG trả lời được câu đó

`stride` chỉ xuất hiện ở hai vòng lịch:

```python
# walkforward.py:193 va :295
for t in range(min_history, len(df), stride)
```

Nó quyết định **phiên nào được ghé**, và lệnh khớp ở phiên **được ghé kế
tiếp**. Nên `stride=2 → 1` đổi **cùng lúc hai thứ**:

- **số điểm quyết định** — gấp đôi, nên tập lệnh khác hẳn, không phải cùng
  tập lệnh với giá vào khác;
- **độ trễ khớp** — T+2 thành T+1.

Một khác biệt quan sát được **không quy được cho vế nào**. Đó là biến gây
nhiễu, không phải chi tiết kỹ thuật.

### Ba lựa chọn, cần người dùng chốt

| | Làm gì | Trả lời được câu gì |
|---|---|---|
| **1** | Không chạy | — |
| **2** | Chạy `--stride 1`, đọc có giới hạn | *"Gộp của điểm quyết định dày gấp đôi VÀ khớp sớm một phiên thì đổi bao nhiêu"* — **không** phải câu hỏi gốc |
| **3** | Tách độ trễ khớp khỏi `stride` bằng một tham số riêng, có test, rồi mới đo | Đúng câu hỏi gốc |

**Đề xuất: 3, hoặc 1.** Lựa chọn 2 tốn cùng chừng ấy máy mà cho một con số
không diễn giải được — và một con số không diễn giải được, đặt cạnh một
bảng đang lạc hậu, là đúng cách dự án này đã năm lần tự lừa mình.

### Nếu chọn 3 — tiêu chí đọc, khai trước

Đại lượng chính vẫn là **alpha OOS cùng KTC**, so giữa hai cấu hình chỉ
khác độ trễ khớp.

**Hướng dự kiến phải nêu TRƯỚC.** `CLAUDE.md` đã nêu: *"vào muộn một phiên
đáng lẽ làm kết quả xấu đi"*, nên chuyển từ T+2 (muộn) sang T+1 (sớm hơn,
khớp đường chạy thật) **được dự kiến làm alpha ĐẸP LÊN**.

Vì thế:

| Kết cục | Đọc thế nào |
|---|---|
| alpha đẹp lên, và mức đẹp lên **nhỏ hơn** bề rộng KTC | phù hợp dự kiến, không có gì bất thường |
| alpha **xấu đi** | ngược dự kiến → có thể sai ở hướng suy luận, hoặc ở phép cài đặt. Đi tìm trước khi tin. |
| alpha đẹp lên **hơn một nửa bề rộng KTC** | quy tắc số 1: giả định đầu tiên là **có lỗi**. Kiểm bốn thứ ở ĐO 1 trước khi ghi vào tài liệu. |

---

## Ghi chép

| Ngày | Mục | Người chốt | Ghi chú |
|---|---|---|---|
| 08/09/2026 | soạn lần đầu, chưa chạy lượt nào | — | chờ chốt ĐO 1 và lựa chọn 1/2/3 của ĐO 2 |
