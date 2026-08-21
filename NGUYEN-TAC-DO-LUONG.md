# Nguyên tắc đo lường — đọc trước khi sửa bất cứ thứ gì liên quan tới kết quả

> Dành cho mọi agent (Antigravity, Claude, Cursor…) và cho chính bạn sau này.
> `AGENTS.md` do vnstock tự đồng bộ nên sẽ bị ghi đè — các quy tắc dưới đây
> nằm ở file này.

Dự án này đã **bốn** lần cho ra những con số rất đẹp mà sau đó hoá ra vô
nghĩa: +22,42% từ backtest có nhìn trộm, +14,88% "OOS" trên vùng đã tối ưu,
+14,24% là cực đại của 20 lần thử trên cùng dữ liệu, và **+636,11% từ một sổ
lệnh dùng đòn bẩy 2,2 lần** (xem dưới). Không lần nào có ai cố ý gian lận —
mỗi lần đều là một lỗi kỹ thuật nhỏ, âm thầm, và luôn nghiêng về phía làm
kết quả đẹp lên.

Đó là quy luật: **lỗi đo lường gần như không bao giờ làm kết quả xấu đi.**
Nếu một thay đổi làm con số đẹp lên đáng kể, giả định đầu tiên phải là có lỗi.

---

## Tám bất biến

### 1. Không nhìn trộm tương lai
Điểm số của phiên T chỉ được tính từ dữ liệu tới hết phiên T. Vào lệnh ở
giá **mở cửa phiên T+1**, không phải đóng cửa phiên T.

Mọi cơ chế "học hỏi" phải nhận mốc thời gian và chỉ đọc dữ liệu trước mốc đó.
Xem `post_mortem_learning.get_penalty_for_pattern(bd, as_of=...)`: thiếu
`as_of` thì trả 0 chứ không âm thầm dùng cả bộ nhớ.

### 2. Trạng thái phải tái lập
Chấm cùng một gói dữ liệu hai lần phải ra cùng một điểm. File trạng thái
(`sl_pattern_memory.json`) bị ghi trong lúc chạy đã từng làm cùng một input
cho ra 47 và 59.

Khoá bởi `tests/test_post_mortem.py::test_cham_diem_khong_doi_khi_chay_lai`.

### 3. Giả định bất lợi khi nến không phân định được
Nến ngày không cho biết đỉnh hay đáy tới trước. SL và TP cùng chạm → lấy SL.
Dời stop về hoà vốn → **chỉ có hiệu lực từ phiên sau**, vì lệnh dời stop chỉ
đặt được sau khi đã thấy giá chạm mốc.

### 4. Đường vốn theo thời gian, không theo id
Sổ trả lệnh theo thứ tự chèn (hết mã A rồi tới mã B). Dựng drawdown từ thứ tự
đó cho ra một chuỗi chưa từng tồn tại. Đo được 23,0% so với 30,7% trên cùng
tập lệnh.

Khoá bởi `test_duong_von_khong_phu_thuoc_thu_tu_ban_ghi`.

### 5. Mọi con số phải kèm khoảng tin cậy
Kỳ vọng +2% với 30 lệnh không nói lên gì. Với σ ≈ 7%/lệnh, cần vài trăm lệnh
để khoảng tin cậy loại được số 0. Dùng `paper_metrics.expectancy_significant()`.

**R:R cao làm σ tăng, tức càng cần NHIỀU mẫu hơn** — tỷ lệ lãi/lỗ đẹp không
thay thế được số lượng lệnh.

### 6. Đối chiếu chuẩn là phép đo quyết định
"Lãi hơn 0" khác "giỏi hơn ngồi yên". Trong thị trường đi lên, mua ngẫu nhiên
cũng cho kỳ vọng dương.

Phép so đúng là **alpha khớp từng lệnh**: mỗi lệnh so với việc cầm đều cả rổ
trong đúng khoảng thời gian lệnh đó nắm giữ (`paper_metrics.vs_benchmark`).
So mức danh mục là sai, vì bên trên là một vị thế giữ suốt còn bên dưới là
hàng trăm lệnh cộng dồn không kiểm tra tổng vốn.

### 7. Không chọn cực đại của N lần thử rồi gọi đó là kết quả
Quét 20 ngưỡng trên cùng một bộ dữ liệu rồi lấy vòng lãi cao nhất là đo độ
may của phép tìm kiếm, không đo lợi thế của chiến lược.

Kết quả chỉ có giá trị khi tham số được chọn trên một khoảng và đo trên một
khoảng **khác**.

> ✅ **Đã dựng lại: `walkforward.py`** (20/08/2026). Nó chia IS/OOS theo
> **dữ liệu nào đã tồn tại khi các vòng tối ưu chạy** — xem
> `docs/moc_du_lieu_sach.json` — chứ không theo ngày lịch, nên vùng kiểm
> định là vùng **không thể đã bị nhìn**, không phải vùng *giả định* chưa
> nhìn. Đo được: 25.219/80.939 phiên = 31,2%, trên 33/71 mã.
>
> ⚠️ Bản cũ `walkforward_vn100.py` (nay là `.broken`) **không làm việc đó**. Nó
> chạy `run_simulation` một lần trên toàn khoảng rồi lọc `exit_date` để gọi
> là OOS, ngưỡng 50,0 nhập sẵn thay vì chọn trên in-sample, và mốc chia là
> `datetime.now() - 182 ngày` nên OOS luôn rơi vào giai đoạn gần nhất —
> đúng thứ mục 8 cấm. Bản làm đúng nằm ở `git show 025507c`. Cho tới khi
> dựng lại, **dự án không có công cụ nào hiện thực hoá bất biến 7 và 8.**

Trong dải kết quả, **dòng đáng tin nhất là dòng có nhiều lệnh nhất**, không
phải dòng lãi cao nhất.

### 7b. Cộng dồn lệnh chồng lấn là đòn bẩy trá hình
Đường vốn nhân dồn từng lệnh vào **toàn bộ** vốn hiện có, lần lượt theo ngày
đóng. Phép nhân đó chỉ đúng khi mỗi thời điểm có một lệnh mở. Nhiều lệnh
chồng lên nhau thì tổng vốn cam kết vượt 100% — con số cộng dồn khi đó là
lợi nhuận của một tài khoản vay được, không phải tài khoản thật.

Luôn đọc `Performance.avg_capital_deployed_pct` kèm `total_net_pct`. Vượt
100% thì chia tỷ trọng cho đúng bội số rồi đo lại.

### 8. Vùng kiểm định nằm ở QUÁ KHỨ
Trực giác nói tối ưu trên quá khứ, kiểm định trên hiện tại. Ở đây ngược lại:
hàng trăm vòng loop đã chạy trên toàn bộ cache kéo tới hôm nay, nên giai đoạn
gần nhất là giai đoạn **đã bị nhìn nhiều nhất**.

Đổi mốc chia rồi chạy lại nhiều lần cho tới khi ra số đẹp là quay về đúng
lỗi ở mục 7.

---

## Những chỗ hỏng âm thầm — kiểm tra định kỳ

| Thứ | Hỏng thế nào | Cách phát hiện |
|---|---|---|
| Bộ lọc VN-INDEX | Không có cache VNINDEX → trả True cho mọi ngày, lọc không hoạt động | `market_filter.status()` |
| Độ phủ dữ liệu | Nửa rổ chỉ có dữ liệu năm gần nhất → kết quả nói về năm đó, không phải cả giai đoạn | `python extend_history.py --check` |
| `download()` | Bỏ qua mọi mã đã có cache → mã tải lần đầu với 13 tháng sẽ mãi mãi 13 tháng | dùng `extend_history()` thay vì `download()` |
| Đơn vị giá | vnstock trả nghìn đồng, agent trả VNĐ → `low <= stop_loss` luôn đúng | `data_quality.price_multiplier()` |
| Thiên lệch sống sót | Rổ là ảnh chụp hiện tại; mã đã rớt khỏi rổ không có mặt | chưa xử lý — mọi kết quả vẫn lạc quan hơn thực tế |

---

## Ranh giới không vượt qua

- **Không đặt lệnh thật.** Agent chuẩn bị → người xác nhận → người đặt lệnh.
- **Không ghi API key vào file trong repo.** Key nằm ở `.streamlit/secrets.toml`
  (đã gitignore) hoặc biến môi trường.
- **Không commit trạng thái chạy.** `*.db`, `sl_pattern_memory.json`,
  `backtest/cache/` đều đã gitignore. Ghi đè `paper_trades.db` bằng kết quả
  in-sample là xoá mất bằng chứng duy nhất chưa bị tối ưu chạm vào.

---

## Lần thứ tư: +636,11% (12/08/2026)

`brain/…/20loop_custom71_18m_optimization_report.md` công bố ngưỡng 50,0 là
"QUÁN QUÂN TỐI ƯU" với +636,11% trên 71 mã, 18 tháng. Con số **tái lập được
chính xác** từ `paper_custom20loop_18m_loop_11.db` — nó không bịa. Nhưng:

```
Vốn cam kết cùng lúc : 224% trung bình · 1.160% đỉnh điểm  → đòn bẩy 2,2x
Quy về 100% vốn      : +155,66%
VN-INDEX cùng kỳ     : +39,56%
```

Bốn bất biến bị vi phạm cùng lúc: cực đại của 20 lần thử trên cùng dữ liệu
(mục 7), cộng dồn lệnh chồng lấn (mục 7b), không có khoảng tin cậy (mục 5),
không có alpha khớp từng lệnh (mục 6). Đo trên 18 tháng gần nhất — giai đoạn
đã bị nhìn nhiều nhất (mục 8).

23 phút sau, ngưỡng 50,0 được nạp đè vào `paper_trades.db` (commit
`e2f98b4`): 96/113 lệnh thật biến mất, vị thế ACB đang mở bị xoá.

Ba việc đã làm sau sự cố: `guard_not_real_ledger()` chặn script tối ưu ghi
vào sổ thật; `Performance.avg_capital_deployed_pct` bắt đòn bẩy ẩn; app và
`paper_metrics.report()` cảnh báo khi vốn vượt 100%.

Bài học riêng của lần này: **báo cáo nằm ngoài repo thì nằm ngoài mọi bất
biến.** Thư mục `brain/` không được git theo dõi, không ai review, và là nơi
con số được diễn giải thành kết luận.

## Kết quả ngoài mẫu gần nhất (07/08/2026)

Rổ 50 mã, tối ưu trên tín hiệu từ 2025-07-17, kiểm định trên tín hiệu trước đó:

```
Trong mẫu (ngưỡng 62) : 240 lệnh · kỳ vọng −0,70%
Ngoài mẫu (ngưỡng 62) : 108 lệnh · kỳ vọng +2,17%  KTC [+0,50; +3,90]
Trung vị mỗi lệnh     : −0,40%   (phần lớn lệnh lỗ)
alpha khớp từng lệnh  : −0,63%   KTC [−2,09; +0,84]  → không khác chuẩn
```

Đọc đúng: kỳ vọng dương đến từ việc agent có mặt trong thị trường lúc thị
trường tăng, **không** từ kỹ năng chọn mã hay chọn thời điểm. Cầm đều cả rổ
cùng khoảng đó cho kết quả ngang bằng.

Chỉ 22/50 mã có dữ liệu trong vùng kiểm định. Chạy `extend_history.py` để kéo
cả rổ về 2022 rồi đo lại — đó là việc tiếp theo cần làm.
