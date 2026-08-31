# Mổ xẻ 5 tầng kiến trúc

> Đo trên 564–573 phiên thật của 10 mã (ACB, FPT, HPG, VNM, SSI, MWG, VCB,
> STB, GAS, POW), dữ liệu 2021-10 → 2026-08. Mọi con số dưới đây tái lập
> được bằng cách chạy lại pipeline trên cùng cache.
>
> ⚠️ **ĐO LẠI 31/08/2026 — phần "số nấc" bên dưới đã SAI, phần kết luận thì
> KHÔNG.** Chấm lại 63.389 phiên trên 69 mã với cửa sổ mở rộng
> (`df.iloc[:t+1]`, `min_history` 250): bốn agent giàu hơn hẳn bảng cũ.
> Nguyên nhân đã được chính dự án đo ngày 29/08: dưới 50 phiên thì
> `_compute_local_indicators()` trả `None` cho SMA50/SMA200 nên phần lớn
> luật bị bỏ qua. **"Công tắc 3 nấc" là tính chất của CỬA SỔ, chưa bao giờ
> là tính chất của mã nguồn.**
>
> Điều này KHÔNG cứu được kết luận của tài liệu — xem cuối file. Đặc trưng
> giàu hơn mà tương quan với lợi nhuận vẫn ở sàn nhiễu thì kết luận còn
> mạnh hơn, không yếu đi.

---

## Tóm tắt một dòng

Kiến trúc mô tả 5 tầng, 6 agent. Khi chạy thật thì **1 agent là hằng số
(`news`), 5 agent còn lại có biến thiên thật trên cửa sổ dài, và 2 tầng
cuối gần như không tồn tại**.

Nhưng điều quan trọng hơn: **cả 5 agent có biến thiên đó cộng lại vẫn
không dự báo được lợi nhuận.** Đo 31/08/2026, cách gộp tuyến tính TỐI ƯU
TRONG MẪU của 5 điểm agent cho rho = 0,0115 ở nhịp 5 phiên — dưới sàn
nhiễu 0,0404. Đó là cận trên: không cách gộp nào tốt hơn tồn tại.

> Bản đầu của tài liệu này viết "2 agent là hằng số, 2 agent chỉ có 3
> trạng thái". Điều đó đúng với **cửa sổ ngắn** nó đo, và sai với cấu hình
> đang chạy. Kết luận thì không đổi — chỉ có lý do là khác.

---

## Tầng 1 — Thu thập dữ liệu

| Nguồn | Trạng thái khi backtest/paper trading |
|---|---|
| OHLCV (vnstock) | ✅ hoạt động |
| TradingView (`tv_indicators`) | ❌ **rỗng `{}`** — không có dữ liệu lịch sử |
| Tin tức (`news_packet`) | ❌ **`None`** — không có kho tin lịch sử |

Đây là gốc rễ của mọi thứ bên dưới. `paper_runner._analyze()` tạo packet với
`tv_recommendation="NEUTRAL"`, không có `tv_indicators`, `news_packet=None`.
Không phải lỗi — không tồn tại nguồn TradingView và tin tức theo thời gian
lịch sử để backtest. Nhưng hệ quả thì rất lớn.

---

## Tầng 2 — Sáu agent phân tích

Đo phân bố thực tế của từng thành phần điểm:

| Agent | Khoảng | Số giá trị khác nhau | Nguồn dữ liệu | Đánh giá |
|---|---|---|---|---|
| Agent | Cửa sổ NGẮN (bản đầu) | **Cửa sổ DÀI (31/08/2026)** | Nguồn dữ liệu |
|---|---|---|---|
| **news** | 1 nấc · 50–50 | **1 nấc · 50–50** | tin tức — ❌ vẫn là hằng số |
| **momentum** | 2 nấc · 50–65 | **17 nấc · 4,2–95,8** | RSI, MACD, Stoch — `_compute_local_indicators` tự tính |
| **trend** | 3 nấc · 35–65 | **10 nấc · 0–100** | 5 luật; SMA50/SMA200 sống lại nên chạm được cả hai biên |
| **sr** | 3 nấc · 31–75 | **7 nấc · 6,2–100** | Bollinger tự tính, `pct_from_low` |
| **risk** | 9 nấc · 10–65 | **8 nấc · 10–45** | biến động, drawdown, Sharpe |
| **volume** | 12 nấc · 25–100 | **13 nấc · 25–100** | khối lượng, OBV |
| **điểm cuối** | — | **61 nấc · 23–83** | tổng có trọng số |

Cột thứ hai đo trên 63.389 phiên / 69 mã, cửa sổ mở rộng, `min_history`
250. Cột thứ nhất giữ lại để thấy **cùng một mã nguồn cho hai bảng khác
hẳn nhau khi cửa sổ đổi** — đó là bài học chính của lần đo lại này.

### Điều này nghĩa là gì

`MomentumAgent` đọc **duy nhất** từ `packet.tv_indicators`. Nhưng
`packet.tv_indicators` KHÔNG rỗng khi thiếu TradingView:
`DataOrchestrator._compute_local_indicators()` tự tính RSI, MACD, Stoch,
Bollinger, ATR từ OHLCV rồi đổ vào đúng khoá đó.

Cái quyết định vì thế là **độ dài cửa sổ**, không phải có TradingView hay
không. Dưới 50 phiên thì `SMA50`/`SMA200` là `None` và phần lớn luật bị bỏ
qua — đó là lý do bản đầu đo ra 2 nấc. Trên cửa sổ dài, agent này ra **17
nấc trải 4,2–95,8**.

Dòng ghi đè dưới đây vẫn tồn tại và vẫn đáng ngờ, nhưng nó không còn là
nguồn DUY NHẤT của biến thiên:

```python
momentum_norm = max(momentum_norm, 65.0)   # khi trend>=60 và volume>=55
```

Tức là điểm momentum thực chất là một hàm của trend và volume.

`TrendAnalysisAgent` có 5 luật chấm điểm, 4 luật dùng EMA20/SMA50/SMA200/ADX
từ TradingView. Chỉ luật thứ 5 (Giá > MA10 > MA20) chạy được. Thang ±5 điểm
thu về còn ±1,5 → chỉ ra được 35, 50, hoặc 65.

Tương tự với `SupportResistanceAgent`: mất Bollinger Bands, chỉ còn
`pct_from_low`.

### Sáu agent có nhìn ra sáu thứ khác nhau không

Tương quan hạng giữa các cặp:

```
              trend  momentum  volume    sr   risk
trend          1.00    0.76     0.44   0.09  -0.00
momentum       0.76    1.00     0.49   0.34   0.02
volume         0.44    0.49     1.00   0.09   0.07
sr             0.09    0.34     0.09   1.00  -0.08
risk          -0.00    0.02     0.07  -0.08   1.00
```

`trend` và `momentum` tương quan **0,76** — gần như cùng một biến, đúng như
dự đoán vì momentum là hàm của trend. `volume` tương quan 0,44–0,49 với cả
hai. Chỉ `risk` và `sr` là độc lập, và cả hai đóng góp rất ít vào điểm cuối
(+0,13 và +0,19).

Cộng sáu con số phụ thuộc lẫn nhau lại không tạo ra thông tin mới — nó chỉ
đếm cùng một tín hiệu nhiều lần với các trọng số khác nhau.

---

## Tầng 3 — Tổng hợp

Trọng số động ba chế độ (breakout / tích luỹ / mặc định). Vì `momentum` và
`news` là hằng số, hai nhánh trong công thức chỉ cộng thêm một số cố định.
Điểm cuối dao động 34–72, trung bình 49,9 — **thang 0–100 thực tế chỉ dùng
khoảng 38 điểm ở giữa**.

> **Đo lại 31/08/2026 trên cửa sổ dài: 23–83, trung bình 51,3, 61 nấc.**
> Dải rộng hơn (60 điểm thay vì 38) nhưng nhận xét bên dưới về ngưỡng 62
> vẫn đứng — 62 nằm ở phân vị rất cao của phân phối này.

Đây là lý do mọi lần chỉnh ngưỡng mua chỉ dịch qua lại trong một dải rất hẹp,
và vì sao ngưỡng 62 gần như là trần.

---

## Tầng 4 — Tranh luận · Tầng 4b — Safety Harness

| Tầng | Trung bình | Nhỏ nhất | Lớn nhất | Độ lệch | % phiên khác 0 |
|---|---|---|---|---|---|
| L4 Tranh luận | −0,00 | −0,8 | +0,9 | 0,42 | 100% |
| L4b Safety Harness | −0,02 | −10,0 | 0,0 | 0,42 | **0%** |

Tầng tranh luận chạy mọi phiên nhưng biên độ điều chỉnh là **±0,9 điểm** trên
thang 100. Trung bình đúng bằng 0 — nó không nghiêng về phía nào cả.

Safety Harness kích hoạt ở **0%** số phiên trong mẫu này. Nó có khả năng trừ
tới 10 điểm nhưng chưa lần nào dùng đến.

**Bỏ hẳn cả hai tầng: 572/573 phiên (99%) cho ra cùng một quyết định
mua/không mua.** Đúng 1 phiên bị lật.

Hai tầng này chiếm 470 dòng mã (`debate_agents.py`) và toàn bộ phần "tranh
luận đa chiều" trong sơ đồ kiến trúc. Về mặt chức năng, chúng gần như không
tồn tại.

Điều này **không** có nghĩa là ý tưởng sai. Safety Harness là chốt chặn —
nó nên hiếm khi kích hoạt. Nhưng "hiếm" khác "chưa bao giờ": nếu 0% thì
chưa có bằng chứng nó hoạt động, và cũng chưa có bằng chứng nó không.

---

## Tầng 5 — Phán quyết cuối

```
NẮM GIỮ  55%
BÁN      33%
MUA      10%
```

### Điểm số có dự báo được lợi nhuận không

Tương quan hạng giữa điểm tại phiên T và lợi nhuận 20 phiên sau đó:

```
Điểm cuối        rho = −0,019   KTC 95% [−0,100 ; +0,064]
  trend          rho = −0,028   [−0,104 ; +0,064]
  momentum       rho = −0,031   [−0,096 ; +0,072]
  volume         rho = +0,014   [−0,067 ; +0,097]
  sr             rho = −0,024   [−0,079 ; +0,094]
  risk           rho = −0,094   [−0,158 ; +0,009]
```

**Không thành phần nào có tương quan khác 0 một cách có ý nghĩa.** Khoảng tin
cậy của điểm cuối là [−0,10 ; +0,06] — đủ hẹp để nói rằng nếu có tương quan
thì nó rất nhỏ, và dấu thì thiên về âm.

Một chi tiết đáng chú ý theo hướng ngược lại: 60 phiên có điểm ≥62 cho lợi
nhuận trung bình +1,64%, so với +0,77% của toàn mẫu. Nhưng 60 phiên là quá
ít, và tương quan trên toàn dải thì bằng 0 — nên đây nhiều khả năng là nhiễu
chứ không phải tín hiệu. Nó khớp với kết quả walk-forward: alpha −0,36%,
KTC [−0,83 ; +0,10].

---

## Kết luận

**Thứ đang chạy khác hẳn thứ được vẽ** — nhưng không theo cách bản đầu của
tài liệu này mô tả. Sơ đồ có 6 agent độc lập, tranh luận đa chiều, chốt
chặn an toàn. Thực tế (đo 31/08/2026, cửa sổ dài): **5 agent có biến thiên
thật, 1 hằng số (`news`), tầng tranh luận bị VỨT BỎ** (`post_debate_score =
pre_debate_score`), và Safety Harness kích hoạt 0%.

**Đặc trưng giàu, mà vẫn không có tín hiệu.** Đây là kết quả nặng nhất của
lần đo lại. Cách gộp tuyến tính tối ưu trong mẫu — cận trên tuyệt đối —
cho rho dưới sàn nhiễu ở cả ba nhịp 5/10/20:

```
                         h=5      h=10     h=20
5 điểm agent           0,0115   0,0093   0,0071
8 chỉ báo thô          0,0234   0,0443   0,0640
sàn nhiễu (hoán vị)    0,0446   0,0609   0,0839
```

Ở h=5 phép đo có chứng cứ dương: tiêm tín hiệu giả bằng **nửa mức rào hoà
vốn** thì nó bắt được. Nên kết quả null ở đó là bằng chứng vắng mặt thật.
Ở h=20 phép đo thiếu lực — không đọc được. Chi tiết: `docs/STATE.md`, mục
**"BƯỚC 7"**.

**Nguyên nhân không phải mã kém, mà là thiếu dữ liệu.** Bốn agent phụ thuộc
TradingView và tin tức — hai nguồn không có lịch sử để backtest. Trên ứng
dụng chạy trực tiếp (có TradingView thật), 4 agent đó sẽ sống dậy. Nhưng khi
đó lại **không đo được** chúng có ích hay không, vì không backtest được.

Đây là mâu thuẫn cốt lõi của dự án: *phần đo được thì không có tín hiệu,
phần có thể có tín hiệu thì không đo được.*

### Ba việc cụ thể

**Cắt phần trang trí.** `news_score` là hằng số 50 — bỏ khỏi công thức trọng
số, hoặc ghi rõ "chưa hoạt động" trên giao diện thay vì hiển thị 50/100 như
một kết quả phân tích. Tương tự với momentum khi không có TradingView.

**Nói đúng về Safety Harness.** 0% kích hoạt trong 573 phiên. Hoặc viết test
dựng đúng tình huống nó phải chặn để chứng minh nó hoạt động, hoặc gỡ khỏi
sơ đồ.

**Nếu muốn có tín hiệu thật, phải thêm dữ liệu mà giá chưa phản ánh.** Sáu
agent hiện tại đều tính từ cùng một chuỗi giá — về mặt lý thuyết chúng không
thể tạo ra thông tin ngoài thứ đã có trong chuỗi đó. Báo cáo tài chính theo
quý, giao dịch nội bộ, khối ngoại mua ròng là những nguồn độc lập và
`financial_collector.py` đã có sẵn đường lấy dữ liệu.
