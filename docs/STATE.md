# STATE.md — trạng thái dự án qua từng phiên sửa chữa

> File này để phiên sau đọc là hiểu ngay đang ở đâu. Đọc trước
> `NGUYEN-TAC-DO-LUONG.md` và `MO-XE-KIEN-TRUC.md`.

---

## Phiên 1 — 19/08/2026 · PHASE 0: MỐC GỐC

### Cấu hình đã chốt

- Làm việc trên nhánh **`sua-chua/phase-0`**, không phải `main`.
  `main` là nhánh Streamlit Cloud tự deploy theo mỗi push.
- Kế hoạch 7 Phase: `ke-hoach-sua-vibe-preview.md`.
  Thứ tự đã chốt: **số liệu trung thực trước → mở khoá giao dịch sau**.
- Năm ô cấu hình C1–C5 trong kế hoạch **chưa được trả lời** — chúng chặn
  thiết kế của Phase 2, 3 và 5.

### Đã xong (Gate 0 — 4/4 điều kiện xanh)

| Điều kiện Gate 0 | Kết quả |
|---|---|
| `pytest` chạy tới cùng, có con số thật | ✅ **204 passed / 0 failed** · 52,87s |
| Có bản sao bằng chứng ngoài thư mục dự án | ✅ `_phase0_snapshot.tar.gz` (2,9 MB · 406 file) |
| Đang đứng ở nhánh KHÁC `main` | ✅ `sua-chua/phase-0` |
| `docs/STATE.md` tồn tại với ảnh chụp trước | ✅ chính file này |

**Không có test nào đang đỏ âm thầm.** Đây là tin tốt và là mốc đo cho mọi
Phase sau: bất kỳ Phase nào làm số này khác 204 đều phải giải thích được.

Bộ test còn **sạch về trạng thái**: chạy xong 204 test, `paper_trades.db` và
`sl_pattern_memory.json` giữ nguyên md5, không sinh file rác nào.

### Ảnh chụp TRƯỚC — mọi con số lấy từ `paper_metrics.compute()`

> Không tự chế phép tính. Con số dưới đây là đầu ra của chính module đo
> lường của dự án, chạy trên bản sao sổ lệnh.

```
n_trades                  = 112 (đã đóng)   ·  tổng 113, 1 OPEN
win_rate                  = 0,25
avg_win                   = +12,49%
avg_loss                  =  −3,11%
expectancy                = +0,79%
profit_factor             = 1,3396
total_net_pct             = +14,2449%
max_drawdown_pct          = 9,9117%
avg_capital_deployed_pct  = 28,94%
peak_capital_deployed_pct = 208,30%      ← đòn bẩy ẩn ở đỉnh
is_leveraged              = False        ← chỉ đọc TRUNG BÌNH, mù với đỉnh

expectancy_significant → ci = (−0,688 ; +2,323) · significant = False
   "CHƯA đủ bằng chứng kỳ vọng dương (khoảng tin cậy chứa 0)"

by_exit_reason = SIGNAL_REVERSED 48 · STOP_LOSS 44 · TAKE_PROFIT 19 · MAX_HOLD 1
```

**Sổ lệnh**

```
trades            113  (112 CLOSED · 1 OPEN)
decisions      12.564  ·  max(seq) = 12.564  → liên tục, không lỗ, không trùng
quyết định mới nhất   2026-08-19 07:00:00
data_quality  'OK' × 12.564  ·  KHÔNG một giá trị nào khác  ← cổng chất lượng là code chết
acted = 1 kể từ 10/08 :  0
sl_pattern_memory.json : 6.327 mẫu hình
reports/               : 34 file
```

**Độ phủ cache (125 file)**

```
Ngày CUỐI:  2025-10-08 →  1 mã (BCG)      ← cũ 10 THÁNG
            2026-07-31 →  2 mã (BVH, SSB)
            2026-08-06 →  1 mã (VCF)
            2026-08-07 → 99 mã            ← gồm cả VNINDEX
            2026-08-11 → 22 mã

Định dạng cột `time`:  85 file `YYYY-MM-DD`  ·  40 file `YYYY-MM-DD HH:MM:SS`
Bắt đầu từ:  49 mã 2021-10 · 37 mã 2025-02 · 31 mã 2025-01 · còn lại rải rác
Ít phiên nhất:   GEL 125 phiên (2026-02 → 2026-08)
Nhiều nhất  :   VNINDEX 1.724 phiên (2019-09 → 2026-08-07)
```

### Phát hiện mới trong Phase 0

**BCG dừng ở 2025-10-08 — cũ 10 tháng.** Không có chốt độ tươi nào áp cho
cache backtest (`backtest/data.load()` không gọi `validate_ohlcv`), nên một mã
ngừng cập nhật 10 tháng vẫn được chấm điểm và vẫn vào rổ đối chiếu như bình
thường. Không log, không cảnh báo. Đây là bản mở rộng của cùng cơ chế đã làm
đóng băng VNINDEX, chỉ khác là nó âm thầm hơn vì không ai theo dõi BCG.

**Bộ test hoàn toàn xanh nhưng không bắt được bất kỳ CRITICAL nào trong audit.**
204 test, 0 đỏ — trong khi cổng VN-INDEX đóng băng 13 ngày, điểm báo cáo là
hằng số 50,0, và giao diện công bố +636,11%. Đây chính là mẫu *"test đúng
nhưng dây chưa cắm"*: từng thành phần được test kỹ khi đứng riêng, không ai
kiểm nó có được **gọi đúng** trong luồng vận hành hay không. Mọi Phase sau
phải thêm test loại "thành phần X thực sự được gọi", không chỉ test đơn vị.

### Chặn ở đâu

1. **Năm ô C1–C5 chưa trả lời.** Không thiết kế được Phase 2 (fail-open hay
   fail-closed khi cache quá hạn), Phase 3 (một nơi ghi hay hai), Phase 5
   (dựng lại walk-forward hay bỏ bất biến 7 & 8).
2. **Ngưỡng mua production vẫn là 50,0** — con số mà `NGUYEN-TAC-DO-LUONG.md`
   mục 7 đã tuyên bố vô hiệu. Chưa quyết (ô C5).

### Việc đầu tiên trên máy người dùng

1. **Chuyển `_phase0_snapshot.tar.gz` ra khỏi thư mục dự án.** Nó đang nằm ở
   gốc repo. Bản sao trong khung chat là bản dự phòng, nhưng nên có một bản
   trên ổ đĩa ở nơi git và script không với tới.
2. **Xoá `.git/index.lock`** (0 byte, kẹt từ 05:09 ngày 19/08). Nó không chặn
   `git checkout -b` nhưng sẽ chặn các thao tác ghi index khác.
3. Cây làm việc có **85 file "modified"** — gần như toàn bộ chỉ là đổi
   line-ending (số dòng thêm = số dòng xoá). Thay đổi thật duy nhất:
   `ui_prototype.html` 1 dòng. Hai file chưa track: `test_syntax.js` và
   `ui_redesign_prototype.html` (md5 **giống hệt** `ui_prototype.html`).

### Bước tiếp theo

Trả lời C1–C5 → duyệt Phase 1 → sửa `run_daily.py:108` (điểm hằng số 50,0) và
khối số cứng trong `app.py`.

**Không** đụng vào cổng VN-INDEX (Phase 2) trước khi Phase 1 xong: ngay giây
phút cổng mở, `consider_entry` sẽ chạy tới dòng so ngưỡng, gặp `50,0`, và mở
lệnh ở lượt quét kế tiếp — trong khi báo cáo bạn đọc vẫn hiện 50,0/100 cho cả
71 mã.

### Ghi chú phương pháp

`pytest` được chạy trên **bản sao** dự án trong môi trường Linux/Python 3.11
(khớp `.python-version`), không phải trên máy Windows của người dùng. Lý do:
môi trường cầu nối tới máy chỉ có Python 3.10 và không có `pytest`,
`vnstock`, `streamlit`, `gspread`. Chạy trên bản sao còn có lợi thế là mọi
tác dụng phụ (nếu có) không chạm tới sổ lệnh thật.

**Chưa kiểm được, và tôi không chạy:** `run_daily.py` một lượt thật ·
`market_filter.status()` trên máy người dùng (gọi nó có thể tải mạng và ghi
cache) · nội dung Google Sheet thật · log GitHub Actions · Task Scheduler
`VibeStock_QuetPhien` (chuỗi này chỉ xuất hiện trong `CLAUDE.md`, không có
`.bat`/`.ps1` nào trong repo).

---

## Phiên 1 (tiếp) — 19/08/2026 · PHASE 1A: ĐIỂM TRONG BÁO CÁO PHIÊN

### Phạm vi

Chỉ 1A (điểm trong báo cáo `.md`). **Không** đụng `app.py` — 1B chờ ô C3.
1A độc lập với cả năm ô C1–C5.

### Cách làm: test đỏ trước, rồi mới sửa

| Bước | Verify | Kết quả |
|---|---|---|
| 1. Viết 2 test | phải ĐỎ trước khi sửa | ✅ 2 failed — test tĩnh chỉ đúng `dòng 108: .get('score', 50.0)` |
| 2. Sửa 2 dòng | 2 test chuyển XANH | ✅ 2 passed |
| 3. Toàn bộ bộ test | không đỏ thêm so với mốc 204 | ✅ **206 passed** (204 + 2 mới), 0 failed |
| 4. Đối chiếu chéo | điểm trả ra == điểm ghi vào `decisions` | ✅ 5/5 mã khớp |

Bước 4 chạy pipeline chấm điểm **thật** (không stub) trên cache thật:

```
MÃ      run_session trả   decisions ghi   khớp?
FPT                41.0              41     ✓
HPG                39.0              39     ✓
VNM                64.0              64     ✓
SSI                32.0              32     ✓
MWG                40.0              40     ✓
```

Điểm biến thiên thật (32–64), không còn hằng số 50,0. VNM = 64 vượt cả
ngưỡng 62 lẫn 50 — trước đây con số này không bao giờ tới được mắt người đọc.

### Thay đổi mã nguồn — đúng 2 dòng

```diff
--- paper_runner.py   (run_session, cuối hàm)
+    # Điểm THẬT của phiên này. Bên dựng báo cáo cần nó; trước đây nó được
+    # tính ở đây rồi vứt đi, nên báo cáo phải bịa một hằng số thay thế.
+    stats["final_score"] = float(result["final_score"])
     return stats

--- run_daily.py:108
-    last_score = s.get("score", 50.0)
+    last_score = s["final_score"]
```

Khoá đặt tên `final_score` (không phải `score`) — `score` chính là cái tên đã
tạo ra lỗi R2 lần đầu. `result` luôn được gán trước `return` trong cả ba
nhánh của `run_session`, nên không cần xử lý `None`.

### Hai test mới

| Test | File | Bắt điều gì |
|---|---|---|
| `test_run_session_tra_ve_diem_that_khong_phai_hang_so` | `tests/test_paper_trading.py` | phía **sản xuất**: khoá tồn tại, mang đúng điểm của mã đó, và hai mã điểm khác nhau thì giá trị khác nhau |
| `test_bao_cao_phien_khong_doc_diem_bang_mac_dinh_so` | `tests/test_no_fabricated_data.py` | phía **tiêu thụ**: quét AST `run_daily.py`, cấm `.get(<khoá chứa "score">, <số>)` |

Test thứ hai là luật R4 của `tools/chan_bia_so_lieu.py` áp cho đúng chỗ đã
hỏng — cần thiết vì hook đó là PostToolUse và chỉ bắt `Write|Edit` của Claude
Code, nên sửa từ IDE, Antigravity hay tay người đều lọt.

### Cố ý KHÔNG sửa

`run_daily.py:136` có `x["score"] >= 50.0` — hằng số viết cứng trùng lặp với
`BUY_THRESHOLD`. Hôm nay hai giá trị bằng nhau nên sửa không đổi hành vi gì;
đó là suy đoán tương lai. Thuộc Phase 2 nếu ô C5 quyết đổi ngưỡng.

### Chưa kiểm được

Chưa chạy `run_daily.py` một lượt thật (cần mạng + ghi vào sổ thật). Bằng
chứng gần nhất là bước 4: cùng pipeline, cùng dữ liệu, hai nguồn khớp. Báo
cáo phiên đầu tiên sau khi bạn chạy lại sẽ là xác nhận cuối cùng — mục "TOP
10" và "Xếp hạng ngành" phải có nhiều hơn một giá trị điểm.

### Trạng thái git

Nhánh `sua-chua/phase-0`, **chưa commit**. 4 file đổi: +94 dòng, −1 dòng.

### Bước tiếp theo

Trả lời **C1–C5**. Ô gấp nhất vẫn là C5 — Phase 2 gỡ cổng VN-INDEX xong là
`consider_entry` chạy tới dòng so ngưỡng và mở lệnh ở lượt quét kế tiếp.

---

## Phiên 1 (tiếp) — 19/08/2026 · PHASE 1B: SỐ CỨNG TRONG `app.py`

### Ô C3 — quyết theo phương án khuyến nghị

Bạn nói "tiếp tục làm tiếp" mà chưa chốt C1–C5, nên 1B chạy theo phương án
đã khuyến nghị trong kế hoạch: **không đọc được sổ thì nói "chưa có dữ
liệu"**, chưa nối Google Sheets. Sổ lệnh vẫn đọc trực tiếp từ
`paper_trades.db` khi file có mặt (tức là trên máy local thì có số thật,
trên Streamlit Cloud thì hiện trạng thái trống + lý do).

### Cách làm: vẫn test đỏ trước

| Bước | Verify | Kết quả |
|---|---|---|
| 1. Viết 2 test tĩnh | phải ĐỎ | ✅ liệt kê đúng 16 hằng số bịa |
| 2. Sửa `app.py` | 2 test xanh | ✅ |
| 3. Toàn bộ bộ test | ≥ 206 | ✅ **208 passed**, 0 failed |
| 4. `py_compile` | không lỗi cú pháp | ✅ |
| 5. **Smoke test trình duyệt** | app chạy thật, không traceback | ✅ HTTP 200, 0 traceback |
| 6. Quét lại text đã render | không còn số bịa trên màn hình | ✅ sạch |

Bước 5–6 chạy bằng Streamlit headless + Playwright, với một harness đặt
NGOÀI dự án (`PYTHONPATH=/tmp/stub`) thay nguồn vnstock bằng
`backtest/cache/` — vì môi trường kiểm thử không có API key. **Không file
nào của dự án bị sửa để phục vụ kiểm thử.**

### Phát hiện mà CẢ HAI bản audit đều bỏ sót

Thẻ **"Trạng thái hệ thống AI"** ở sidebar dán cứng toàn bộ:

```
📈 Technical Agent    12ms      ● ONLINE
📑 Fundamental Agent  Q2/2026   ● ONLINE
⚔️ Debate Council     3 Vòng    ● ACTIVE
🧠 Post-Mortem Mem    39 Mẫu    ● SYNCED     ← file thật có 6.327 mẫu (lệch 162×)
📡 TradingView MCP    Live      ● READY
```

Không dòng nào đọc từ đâu. `39 Mẫu` là con số sai nghiêm trọng nhất còn
lại trên giao diện sau khi gỡ +636,11%. Cả bản audit lẫn bản kiểm chứng đều
không bắt được — **chỉ smoke test bằng trình duyệt mới lộ ra**, vì nó nằm
trong một chuỗi HTML tĩnh không khớp mẫu grep nào của hai bản đó.

Bài học cho các Phase sau: kiểm tĩnh (grep/AST) chỉ bắt được thứ mình đã
biết tên. Muốn tìm cái chưa biết thì phải **render rồi đọc màn hình**.

### Đã thay

| Chỗ | Trước | Sau |
|---|---|---|
| Topbar | `VN-Index 1,245.80 ▲ +0.85%` · `20-Loop Return +636.11%` | `VN-Index —` · `Sổ lệnh (net) +14.24%` (từ `compute()`) |
| Tab "Tài khoản Giả lập" | HTML tĩnh: 7.361 Tỷ · +636,11% · 1.787 lệnh · PF 1,43 · WR 61,2% · DD 19,4% · +7,77% | 4 ô thật từ `paper_metrics.compute()` + **KTC 95%** + **cảnh báo đòn bẩy khi peak > 100%** |
| Tab "Lịch sử giao dịch (1,787)" | 1.787 | `112` — số lệnh đã đóng thật |
| Bảng vị thế | `entry_price or 22750.0` · `entry_date or "2026-05-29"` · `"60.0"` · `pos_capital = 30_000_000` | thiếu trường nào thì `—`, bỏ cột PnL VNĐ (không biết vốn tài khoản thì không tính được) |
| Nhánh `else` dựng vị thế ACB giả | `+7.77%` · `+2,330,649 VNĐ` · SL 21.158 · TP 26.052 | thông báo trạng thái trống, kèm **lý do** vì sao không đọc được sổ |
| `calculate_rsi` | thiếu dữ liệu → `50.0` | → `None`, hiển thị `—` |
| `est_stop_loss` / `est_tp` | thiếu khuyến nghị → `close×0,93` / `close×1,15` | → `None`, hiển thị `—`; đường SL trên chart chỉ vẽ khi có số |
| Nhãn SL/TP | `(-7.0%)` / `(+15.0%)` cứng | phần trăm tính thật từ giá hiện tại |
| Tỷ trọng vốn trong kế hoạch vào lệnh | `"30%"` | `safety.safe_position_size` thật |
| "Pha Wyckoff" | `Pha C — Wyckoff Spring` … | `Vùng điểm ≥ 60 (điểm cuối, không phải pha Wyckoff)` … |
| Thẻ trạng thái hệ thống | 5 dòng dán cứng | Post-Mortem đọc thật (`6.327 mẫu · ● TẮT`), 4 dòng còn lại `— · ● chưa đo` |

Ba gác dựng sau sự cố thứ tư giờ đã chạm tới mặt người đọc: cảnh báo đòn
bẩy hiện **"🔴 ĐÒN BẨY ẨN: vốn cam kết cùng lúc chạm 208% (trung bình 29%)"**,
và cảnh báo KTC hiện **"CHƯA đủ bằng chứng kỳ vọng dương"**.

### Cố ý KHÔNG sửa (ngoài phạm vi 1B)

| Chỗ | Vì sao |
|---|---|
| `Threshold 50.0 pts` ở topbar | đúng với `BUY_THRESHOLD` thật — là cấu hình, không phải phép đo. Thuộc ô C5 |
| Pill `● Sheets Synced` | khẳng định trạng thái **không** kiểm chứng, nhưng không phải con số. Cùng họ với `market_filter.status()` → Phase 2 |
| Tab "Pipeline v2": `LIVE DATA`, `LIVE SYNC` | như trên |
| Tab "Báo cáo 3 phiên" | in cùng một điểm cho cả ba khung giờ như thể ba phiên khác nhau; `Doi SL Breakeven` dán cứng. Là mô tả sai, không phải số bịa |

### Trạng thái git

Nhánh `sua-chua/phase-0`, **chưa commit**. Tổng Phase 1A + 1B:
`app.py` +190/−119 · `paper_runner.py` +4 · `run_daily.py` ±1 ·
2 file test +4 test mới. Bộ test: **204 → 208**, không test cũ nào đỏ.

### Chưa kiểm được

- Chưa chạy `run_daily.py` một lượt thật.
- Smoke test dùng dữ liệu từ `backtest/cache/` (qua harness ngoài dự án),
  không phải vnstock trực tiếp — nên chưa xác nhận đường lấy dữ liệu live.
- Nhánh "không đọc được sổ" (Streamlit Cloud) chỉ được kiểm bằng test tĩnh,
  chưa render thật với `paper_trades.db` vắng mặt.
