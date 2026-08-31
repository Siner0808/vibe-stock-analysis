# Backtest hệ thống chấm điểm Vn-Stock

Trả lời một câu hỏi: **hệ thống chấm điểm này có giá trị dự báo không, hay chỉ là số đẹp?**

Trước khi có câu trả lời, mọi việc tinh chỉnh trọng số/ngưỡng đều là đoán.

## Chạy

```bash
# Bước 1 — tải dữ liệu (cần mạng, chạy một lần, ~2 phút cho VN30)
python3 backtest/run.py fetch --start 2024-01-01 --end 2026-08-01

# Bước 2 — chạy backtest (offline, tất định, lặp lại được)
python3 backtest/run.py test --stride 5
```

Kết quả ghi vào `backtest/results/`: `observations.csv` (chi tiết từng quan sát)
và `report.txt` (báo cáo).

## Cách đọc kết quả — quan trọng hơn cách chạy

Báo cáo có ba lớp, khắt khe dần:

| Lớp | Câu hỏi | Cạm bẫy |
|---|---|---|
| Lợi nhuận thô | Nhóm MUA có lãi không? | **Vô nghĩa nếu đứng một mình.** Thị trường tăng thì mọi tín hiệu mua đều lãi |
| Lợi nhuận vượt thị trường | Sau khi trừ trung bình toàn rổ cùng ngày, còn gì không? | Đây mới là kỹ năng chọn mã |
| Tương quan hạng (rho) | Điểm cao có đi kèm lợi nhuận cao không? | Không phụ thuộc ngưỡng — dùng được cả khi ngưỡng không kích hoạt |

**Quy tắc quyết định:** nếu khoảng tin cậy 95% chứa 0 → **chưa có bằng chứng**.
Đừng tinh chỉnh trọng số dựa trên kết quả đó. Đó là tối ưu vào nhiễu.

## Hạn chế đã biết — đọc trước khi tin kết quả

1. **Không có TradingView lịch sử.** Mọi phiên chạy với `tv_bonus = 0`.
   Hệ quả lớn: thang điểm co lại quanh 50 và **gần như không bao giờ chạm
   ngưỡng MUA (62)**. Nói cách khác, `tv_bonus ±8` đang là yếu tố quyết định
   việc hệ thống có phát tín hiệu MUA hay không. Đây là phát hiện về chính
   thiết kế, không phải lỗi backtest.
2. **Không có tin tức lịch sử.** `news_packet=None`. Backtest đo phần lõi kỹ
   thuật: trend, momentum, volume, S/R, risk, debate council, safety harness.
3. **Survivorship bias.** Chạy trên rổ VN30 *hiện tại* → lạc quan hơn thực tế,
   vì các mã bị loại khỏi rổ không có mặt.
4. **Chưa tính chi phí.** Không có phí giao dịch, thuế, trượt giá. Kết quả
   thực tế sẽ thấp hơn.
5. **Mẫu chồng lấn.** Các ngày gần nhau có lợi nhuận tương quan, làm khoảng
   tin cậy hẹp hơn thực tế. Tăng `--stride` để giảm.

## Vì sao tin được backtest này không rò rỉ tương lai

Look-ahead bias là lỗi khiến backtest cho kết quả tuyệt vời và hoàn toàn
vô nghĩa — và **không phát hiện được bằng mắt**. Ba hàng rào:

- `engine.run_symbol()` cắt `df.iloc[:t+1]` **trước** khi dựng packet.
- `test_khong_co_look_ahead`: chạy hai lần trên cùng lịch sử nhưng tương lai
  khác hẳn (một bản sụp 50%), khẳng định điểm tại mọi ngày T ≤ 120 giống hệt.
  Đã kiểm chứng test này *fail* khi cố tình bỏ dòng cắt.
- `test_khong_tim_ra_tin_hieu_trong_nhieu_thuan_tuy`: chạy trên random walk,
  khẳng định rho **không** có ý nghĩa. Nếu hệ thống "tìm ra" tín hiệu trong
  nhiễu thì chắc chắn có lỗi.

## Sau khi có kết quả thì làm gì

- **rho có ý nghĩa và excess return dương** → hệ thống có giá trị. Lúc này mới
  đáng tinh chỉnh trọng số, và mới đáng bàn tới agent nghiên cứu đa nguồn.
- **rho không có ý nghĩa** → thang điểm hiện tại chưa dự báo được gì. Việc cần
  làm là xem lại từng thành phần (thành phần nào có rho > 0 riêng lẻ?),
  không phải chỉnh trọng số tổng.
- **Chỉ lợi nhuận thô dương, excess return ≈ 0** → hệ thống đang đi theo thị
  trường, không chọn được mã. Đây là kết quả phổ biến nhất và dễ bị nhầm
  thành thành công.
