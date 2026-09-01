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
| "Pha Wyckoff" | `Pha C — Wyckoff Spring` … | `Vùng điểm ≥ 60 (điểm cuối, không phải pha Wyckoff)` … — **đã thay lần nữa ngày 22/08/2026 bằng phép đọc cấu trúc thật, xem mục cuối file** |
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

---

## Phiên 1 (tiếp) — 19/08/2026 · PHASE 4: HÀNG RÀO TỰ ĐỘNG

### Vì sao làm Phase 4 trước Phase 2

Phase 2 cần ô C1 + C5 (chưa có). Còn Phase 4 không cần ô nào, và không có
nó thì mọi thứ vừa sửa ở 1A/1B **không được gì bảo vệ**: `grep pytest
.github/workflows/` = 0, Streamlit Cloud deploy theo push, push không đi
qua test. Hai test chặn `+636,11%` quay lại chỉ chạy nếu ai đó nhớ gõ
`pytest`.

### Đã làm

**1. Chế độ `--quet-repo` cho `tools/chan_bia_so_lieu.py`**

Hook hiện tại là PostToolUse (chạy *sau* khi ghi) và matcher chỉ bắt
`Write|Edit` của Claude Code. Chế độ mới quét toàn bộ `.py` trong dự án,
trả exit 1 nếu có phát hiện mức CHẶN.

Hiện trạng đo được: **0 CHẶN · 35 cảnh báo**

| File | Cảnh báo | Mẫu |
|---|---|---|
| `chatbot_agent.py` | 18 | `.get("trend_score", 50)`, `.get("risk_score", 50)`… — cùng bệnh với `run_daily.py:108` vừa sửa |
| `post_mortem_learning.py` | 6 | `.get("trend_score", 50)` |
| `debate_agents.py` | 6 | `.get("stop_loss_pct", 7)`, `pos_size = min(pos_size, 10.0)` |
| `master_agent.py` | 1 | `momentum_norm = max(momentum_norm, 65.0)` — dòng đã biến momentum thành hàm của trend+volume |
| khác | 4 | |

Mức CHẶN sạch nên CI xanh được ngay. 35 cảnh báo là món nợ đã hiện rõ,
không thuộc phạm vi Phase 4.

**2. `.github/workflows/kiem-dinh.yml`** — chạy trên mọi push và PR:
quét bịa số liệu → `pytest tests/ -q` → chạy lại pytest **khi mạng bị chặn**.

**3. Hai test mới** khoá `--quet-repo`: bắt được mẫu R1/R2, và "repo hiện
tại sạch ở mức CHẶN" (bất biến — đỏ nghĩa là một mẫu cũ vừa quay lại).

Bộ test: **208 → 210 passed**.

### Một gác GIẢ tự tay bắt được

Bản đầu của bước "kiểm test chạy được khi không có mạng" viết:

```python
socket.socket.connect = chan
sys.exit(subprocess.call([sys.executable, "-m", "pytest", ...]))
```

Nó **chạy xanh** — và hoàn toàn vô nghĩa: `subprocess` sinh một tiến trình
Python mới, patch ở tiến trình cha không theo sang. Đã chứng minh bằng cách
cho tiến trình con `connect(("pypi.org", 443))` — nó ra mạng được.

Bản sửa chạy `pytest.main()` **in-process** sau khi patch, và tự kiểm chính
mình trước: nếu vẫn connect được thì thoát với thông báo "GÁC HỎNG". Kiểm
lại: chặn thành công, 210 passed offline.

Đây đúng mẫu mà chính Phase 0 đã cảnh báo — thành phần được test kỹ nhưng
dây chưa cắm, và mọi chỉ số vẫn xanh.

### GIỚI HẠN — không vá được bằng mã nguồn

**Streamlit Cloud không nghe lệnh GitHub Actions.** Workflow này chỉ báo
đỏ, không chặn được deploy. Muốn thật sự chặn, bạn phải làm trên GitHub:

1. `Settings → Branches → Add branch protection rule` cho `main`
2. Bật **Require status checks to pass before merging** → chọn `kiem-dinh`
3. Làm việc trên nhánh khác, chỉ merge vào `main` khi check xanh

Đây là thay đổi **thói quen**, và là chỗ dễ trượt nhất của cả kế hoạch.

### Việc bạn phải tự làm

`.github/workflows/kiem-dinh.yml` **không ghi được qua cầu nối** — file
workflow được bảo vệ (đúng: nó là file chạy code). Bản đầy đủ đã gửi trong
khung chat; bạn tự lưu vào `.github/workflows/` rồi `git add`.

### Trạng thái git

Nhánh `sua-chua/phase-0`, **3 commit**:

```
955a2ec feat(ci): che do --quet-repo cho bo do bia so lieu
e70b5f6 fix(app): go moi con so bia khoi giao dien, doc so lenh qua paper_metrics
6a54e90 fix(bao-cao): tra diem THAT ra bao cao phien, bo mac dinh 50.0
```

Chưa push. Chưa merge vào `main` — nên Streamlit Cloud vẫn đang chạy bản cũ
với `+636,11%`.

### Bước tiếp theo

1. **Chạy `python run_daily.py` một lượt** — điều kiện cuối của Gate 1A.
   Báo cáo sinh ra phải có > 1 giá trị điểm.
2. Đặt `kiem-dinh.yml` vào repo + bật branch protection.
3. Trả lời **C1–C5** để mở khoá Phase 2. Hoặc làm tiếp Phase 3A–3D /
   Phase 5A–5B (không cần ô nào).

---

## Phiên 1 (tiếp) — 19/08/2026 · PHASE 3A–3D: ĐÓNG ĐƯỜNG MẤT BẰNG CHỨNG

3E (hai nơi ghi song song) cần ô **C2**, chưa làm.

### Verify

| Bước | Kết quả |
|---|---|
| 7 test viết TRƯỚC | ✅ đều ĐỎ trước khi sửa |
| `pytest tests/ -q` | ✅ **217 passed** (mốc 210), 0 failed |
| `--quet-repo` | ✅ 0 CHẶN |
| Streamlit + Playwright sau khi đổi chữ ký `__init__` | ✅ HTTP 200, 0 traceback, topbar `+14.24%`, tab `Lịch sử giao dịch (112)` |

### 3A — gác chuyển từ phía người gọi vào `__init__`

Bản cũ gọi `guard_not_real_ledger(SCRATCH_DB, ...)` — truyền **hằng số tên
file scratch**, tức không bao giờ có thể kích hoạt — và chỉ gọi ở 3/7 script
tối ưu. Đó là lời tự khai, không phải cái cửa.

Nay: mở `paper_trades.db` phải khai báo `cho_phep_so_that=True`. Mặc định
**từ chối**, nên script viết sau này cũng phải đi qua.

| Được miễn (có lý do) | Không được miễn |
|---|---|
| `run_daily.py` · `cmd_daily` · `cmd_report` · `google_sheets_sync` · `app.py` (chỉ đọc) | **`cmd_seed`** · 7 script `optimize_*` · `walkforward_vn100` · `run_oos_test` · `run_vn100_18m_test` · `evaluate_custom71_results` |

`cmd_seed` mặc định trỏ vào `paper_trades.db` — đúng đường đã đi ngày
12/08/2026. Nay nó nổ.

### 3B — `push()` phát hiện dòng bị bỏ sót

Khoá nhận dạng là **`(seq, symbol, signal_date)`**, không phải một mình
`seq`. Đây là chi tiết quyết định: khi hai nơi cùng ghi, chúng sinh ra
**cùng dải seq cho nội dung khác nhau** — so một mình `seq` thì thấy "đủ"
trong khi thật ra là hai bản ghi khác nhau đội cùng một số. Bản đầu của tôi
so mình `seq` và **không bắt được cả sự cố 14/08 lẫn test của chính nó**.

### 3D — nâng stop commit ngay

Đo trên DB tạm: stop **108,81** trong phiên → **90,0** sau khi đóng kết nối.
Test tái lập đúng con số đó trước khi sửa.

### 3C — ĐỔI HÀNH VI, cần bạn duyệt

`open_from_secrets()` nay **nổ** khi cấu hình nửa vời (có key thiếu creds,
hoặc ngược lại, hoặc key rỗng). Trước đây trả `None`, tức gộp "cấu hình
HỎNG" vào "chưa cấu hình".

Căn cứ: **chính docstring của hàm đó** viết *"Không có credential thì tính
năng TẮT sạch… Nhưng cấu hình SAI thì phải nổ, vì 'tưởng đã sao lưu mà thật
ra không' là trạng thái tệ nhất."* Hành vi cũ trái với hợp đồng nó tự tuyên bố.

**Test cũ `test_bao_ro_khi_chua_cau_hinh` khoá lại hành vi cũ.** Tôi đã sửa
test đó và ghi rõ lý do ngay tại chỗ. Đây là lần duy nhất trong phiên tôi
sửa một test đang xanh — cần bạn xác nhận.

Ảnh hưởng thực tế: `secrets.toml` sai cú pháp, thiếu thư viện `toml` (không
có trong `requirements.txt`), hoặc key rỗng → `run_daily.py` **dừng phiên
quét** thay vì in "chưa cấu hình" rồi chạy tiếp trên sổ cũ.

### Trạng thái git

Nhánh `sua-chua/phase-0`, **4 commit**:

```
a679a8b fix(so-lenh): dong bon duong lam mat bang chung im lang
955a2ec feat(ci): che do --quet-repo cho bo do bia so lieu
e70b5f6 fix(app): go moi con so bia khoi giao dien...
6a54e90 fix(bao-cao): tra diem THAT ra bao cao phien...
```

Bộ test: 204 → **217**. Chưa push, chưa merge vào `main`.

### Còn treo

1. **`python run_daily.py` một lượt** — Gate 1A chưa đóng. Nay còn quan
   trọng hơn: 3C có thể làm phiên quét dừng nếu `secrets.toml` có vấn đề,
   và đó chính là thứ cần biết.
2. `.github/workflows/kiem-dinh.yml` + branch protection (chỉ bạn làm được).
3. **C1–C5** → Phase 2, 3E, 5D.

---

## Phiên 1 (tiếp) — 19/08/2026 · GATE 1A ĐÃ ĐÓNG

### Cách chạy được

`run_daily.py` **không chạy được trên máy người dùng qua cầu nối** — môi
trường đó có Python 3.10, thiếu `vnstock`/`streamlit`/`gspread`, và không có
mạng. Đã chạy trên **bản sao** trong container, nguồn dữ liệu thay bằng
`backtest/cache/` qua harness đặt NGOÀI dự án. Sổ lệnh của bản sao đã được
sao lưu trước khi chạy và **khôi phục nguyên trạng sau đó** (md5 khớp).

### Điều kiện cuối của Gate 1A: ĐẠT

```
Số giá trị điểm KHÁC NHAU trong báo cáo mới:  5
Các giá trị:  52,0 · 53,0 · 59,0 · 63,0 · 64,0
```

Trước khi sửa: **1 giá trị duy nhất** (50,0) trong suốt 21 báo cáo.

| Mục | Trước | Sau |
|---|---|---|
| "Số cổ phiếu đạt ngưỡng ≥ 50,0" | `71/71` (vì `50 >= 50` luôn đúng) | **`7/71`** |
| TOP 1–3 | BSR · PVD · PVS — 10 mã **đầu watchlist** | **HHP 64,0 · VHM 63,0 · BCM 59,0** |
| Điểm trung bình ngành | cả 16 ngành đúng `50,0đ` | **28,0đ → 41,6đ**, xếp hạng thật |
| Mã dẫn đầu ngành | mã **đầu danh sách** mỗi ngành | mã điểm cao nhất ngành |

Trong `decisions` vừa ghi: **49 giá trị điểm khác nhau, dải 16–71**.

### Những thứ khác cùng lúc được xác nhận

- **3A không chặn nhầm**: `run_daily` mở sổ thật với `cho_phep_so_that=True`,
  chạy trọn 71 mã, không nổ.
- **3C hoạt động đúng ở nhánh "chưa cấu hình"**: không có `secrets.toml` →
  in *"Kho ngoài chưa cấu hình"* → quét tiếp. Đúng ý.
- **Cổng VN-INDEX vẫn chặn 70/70**: mọi quyết định mang một lý do duy nhất
  *"VN-INDEX nằm dưới MA50"*. 0 lệnh mở, dù có mã đạt 64 và 71 điểm.
  Đây là Phase 2, chưa động tới.
- Sổ lệnh không hỏng: 113 lệnh trước và sau, `seq` liên tục.

### Bổ sung 3C — nửa quan trọng hơn mà bản sửa đầu bỏ sót

`except Exception: pass` bọc quanh **cả** `import toml` **lẫn**
`toml.load()`. Hai đường vào rất thật:

- `toml` **không có trong `requirements.txt`** — máy nào thiếu thư viện đó
  thì `secrets.toml` bị bỏ qua lặng lẽ;
- `secrets.toml` sai cú pháp sau một lần sửa tay.

Cả hai đều ra *"Kho ngoài chưa cấu hình"*, `run_daily` quét tiếp mà **không
kéo sổ về trước** — đúng tiền đề của sự cố mất 70 dòng ngày 14/08. Nay file
CÓ mặt thì mọi lỗi đọc nó đều là "cấu hình hỏng" → `SheetError`.

**Rủi ro cho 09:10 sáng mai:** nếu máy bạn thiếu `toml`, phiên quét sẽ
**dừng** thay vì âm thầm bỏ qua Sheets. Đó là hành vi đúng, nhưng bạn cần
biết trước. Kiểm bằng: `python -c "import toml; print(toml.__version__)"`.

### Trạng thái git

Nhánh `sua-chua/phase-0`, **5 commit**. Bộ test: 204 → **218**.

```
aceade1 fix(sheets): secrets.toml co mat ma khong doc duoc thi NO
a679a8b fix(so-lenh): dong bon duong lam mat bang chung im lang
955a2ec feat(ci): che do --quet-repo cho bo do bia so lieu
e70b5f6 fix(app): go moi con so bia khoi giao dien...
6a54e90 fix(bao-cao): tra diem THAT ra bao cao phien...
```

### Còn treo

1. **Chạy `python run_daily.py` trên MÁY BẠN** — bản chạy ở trên dùng cache
   (dữ liệu dừng 07–11/08) và không có Sheets. Lần chạy thật với vnstock
   live + `secrets.toml` thật vẫn chưa được kiểm.
2. Kiểm `toml` đã cài chưa (xem trên).
3. `.github/workflows/kiem-dinh.yml` + branch protection.
4. **C1–C5** → Phase 2, 3E, 5D.

---

## Phiên 2 — 20/08/2026 · CHẠY THẬT + DỌN NỢ TỒN ĐỌNG

Phiên Claude Code trên máy người dùng. Ba lệnh mục 0 của `HANDOFF.md` đã
chạy; toàn bộ nợ **không bị C1–C5 chặn** đã đóng.

### Ba lệnh khởi động — kết quả thật

| Lệnh | Kết quả |
|---|---|
| `pytest tests/ -q` | **218 collected · 217 passed · 1 failed** |
| `import toml` | ✅ 0.10.2 có sẵn |
| `python run_daily.py` | ✅ **exit 0**, lượt chạy live đầu tiên |

**Test đỏ KHÔNG phải hồi quy.** `test_secrets_toml_ton_tai_nhung_khong_doc_duoc_thi_NO`
xanh khi chạy riêng, đỏ khi chạy cả bộ. `open_from_secrets()` đọc `st.secrets`
trước file, và streamlit **cache** secrets sau lần chạm đầu; một test chạy
trước đã nạp bản hợp lệ vào cache, nên nhánh đọc-file không bao giờ chạy tới.
Mốc 218 đo trên bản sao Linux **không có `secrets.toml` thật** — máy có file
thật thì đổi màu mà mã không đổi. Kèm theo: lượt chạy cả bộ đã dựng
`GoogleSheet` bằng credential thật và gọi mạng tới Sheet production.

**`run_daily.py` — gate của HANDOFF ĐẠT.** Kéo sổ trước khi quét chạy đúng
(113 lệnh, 12.634 quyết định), ghi 70 quyết định mới, đẩy Sheets thành công.
Điểm **không còn là hằng 50,0**: 27 giá trị phân biệt trong 70 dòng mới
(min 21 · max 55). Kiểm chéo báo cáo ↔ bảng `decisions`: **6/6 mã khớp**.

**Chẩn đoán cốt lõi được xác nhận bằng chạy hàm:**
```
market_filter.status()        = {'active': True, ... → 2026-08-07}
is_vni_bullish('2026-08-20')  = False
is_vni_bullish('2030-01-01')  = False
```
6/71 mã vượt ngưỡng hôm nay, **0 lệnh mở**. Không phải thiếu tín hiệu — là cổng.
`data_quality = 'OK'` × **12.704/12.704**: cổng chất lượng vẫn là code chết.

### Đã đóng trong phiên này

| Việc | Gate liên quan |
|---|---|
| Cách ly `st.secrets` trong test 3C | mốc test về 218 xanh |
| **`toml` vào `requirements.txt`** + test chặn tái phạm | — |
| Xoá 12 file rác 0 byte trong `.git/` | STATE.md mục "việc đầu tiên" |
| `_phase0_snapshot.tar.gz` ra ngoài repo | **Gate 0 điều kiện 2** |
| Smoke test app với sổ lệnh vắng mặt | **Gate 1 điều kiện 3** |
| Luật **R6** `X or <số>` cho bộ dò | Phase 4 bước 4 |
| **`.github/workflows/kiem-dinh.yml`** | Phase 4 bước 1+2 |
| Ba pill khẳng định trạng thái không kiểm | cùng họ Phase 1 |
| Ngưỡng mua về một nguồn duy nhất | dọn đường cho C5 |

**`toml` vào `requirements.txt` — ĐÍNH CHÍNH mức độ.** Bản đầu của mục này
(và commit `9a6050f`) khẳng định "mọi lượt quét trên GitHub Actions đều chết
ở bước kéo sổ". **Sai.** `toml` là phụ thuộc của `streamlit`
(`pip show toml` → `Required-by: streamlit`), mà `streamlit` có trong
`requirements.txt`, nên runner vẫn cài được nó. Đã kiểm trên trang Actions:
10/12 lượt `Quét sổ lệnh` gần nhất XANH, chạy đủ 8–9 phút.

Việc khai báo `toml` vẫn đúng, nhưng lý do khác: nó là phụ thuộc **ngầm**.
Streamlit đã và đang chuyển dần sang `tomli`/`tomllib`; ngày nó bỏ `toml`
khỏi danh sách phụ thuộc, `open_from_secrets()` sẽ bắt đầu ném `SheetError`
và phiên quét dừng — không phải vì cấu hình hỏng mà vì một thư viện biến mất
sau một lần nâng cấp không liên quan. Đây là **nguy cơ tiềm ẩn**, không phải
sự cố đang xảy ra. `tests/test_requirements.py` khoá đúng nguy cơ đó.

**Hai lượt quét ĐỎ** (45s và 38s, trong 12 lượt gần nhất) chưa truy nguyên —
không phải do `toml` vì các lượt khác cùng dependency vẫn xanh.

### Phát hiện mới, CHƯA sửa — cố ý

- **R6 bắt ngay 2 chỗ đang sống**, cả hai là con số 50:
  `debate_agents.py:159` `risk.get("risk_score") or 50` và
  `debate_agents.py:347` `(...).get("RSI") or 50.0`. Chỗ thứ hai nằm **đúng
  trong danh sách Phase 1B** ("RSI bịa 50,0 khi thiếu phiên") — Phase 1B gỡ
  nó khỏi `app.py`, bản sao trong `debate_agents.py` sống sót.
  Không sửa vì chúng nằm trên đường tính điểm: sửa là đổi điểm, mà chưa có
  **Gate 5A** thì không đo được thay đổi ấy đúng hay sai.
- **`paper_trading.py:77` khai báo `BUY_THRESHOLD = 62`** trong khi
  `run_daily.py:23` là `50.0`. Cùng tên, khác giá trị, cùng dự án. Hôm nay
  62 không chạy (chỉ là mặc định dự phòng; `run_daily` luôn truyền 50.0).
  Hợp nhất là chọn giữa 50 và 62 — **đúng là ô C5**.
- Chuỗi lời khuyên của R1/R3/R4 in `{v}` nguyên văn vì thiếu tiền tố `f`.

### Trạng thái git

Nhánh `sua-chua/phase-0`, **12 commit**, chưa push. Bộ test: 204 → 218 → **226**.

### Còn treo — chỉ người dùng làm được

1. **Push nhánh** để `kiem-dinh.yml` chạy lần đầu.
2. **Branch protection**: Settings → Branches → Require status checks →
   `kiem-dinh`. Streamlit Cloud không nghe Actions; đây là thay đổi thói quen.
3. **C1–C5** → chặn Phase 2, 3E, 5D.

### Còn treo — làm được, chưa làm

Phase 5A (test tái lập 2 tiến trình, post-mortem BẬT) và Phase 5B
(`vs_benchmark` vào đường tự động — `grep benchmark run_daily.py` = 0).
Kế hoạch ghi rõ hai mục này **không cần ô C nào**. Phase 6 cần Gate 5A trước.

---

## Phiên 2 (tiếp) — PHASE 5A + 5B

### Gate 5A — bất biến 2: trạng thái phải tái lập ✅

Test mới `test_tai_lap_qua_HAI_TIEN_TRINH_voi_post_mortem_BAT` khẳng định
**hai** điều; điều thứ hai quan trọng ngang điều thứ nhất:

```
post-mortem BẬT, tiến trình 1 : 48
post-mortem BẬT, tiến trình 2 : 48    ← tái lập
post-mortem TẮT               : 60    ← bộ nhớ CÓ cắn, đúng -12 = PENALTY
```

Thiếu vế thứ hai thì test vẫn xanh khi post-mortem âm thầm không chạy.
Cách ly bằng `cwd` (vì `MEMORY_FILE` là đường dẫn tương đối) nên
`sl_pattern_memory.json` thật giữ nguyên md5.

### Đo được cho Phase 6 — lớn hơn dự đoán của kế hoạch

`run_daily.py:12` đặt `POST_MORTEM_ENABLED = "1"` → **post-mortem ĐANG BẬT
trong mọi phiên quét production.**

Trên 280 lượt chấm của các phiên hôm nay:

```
Số mã khớp mẫu hình cắt lỗ → bị trừ 12 điểm:  259/280 = 92,5%
```

Hệ quả cụ thể, ngưỡng mua là 50,0:

| Mã | Điểm ghi vào sổ | Nếu không có bộ nhớ |
|---|---|---|
| PLX | 48 | **60** ← vượt ngưỡng |
| BSR | 42 | **54** ← vượt ngưỡng |
| PVD | 39 | **51** ← vượt ngưỡng |

Kế hoạch ước "gần như 1"; đo trên không gian giá trị đều thì chỉ 49,4%,
nhưng theo **tần suất thật** là 92,5% — kế hoạch đúng. Đây là đòn bẩy lớn
nhất đang tác động lên hành vi hệ thống, và nó dựng hoàn toàn từ dư lượng
in-sample. **Gate 6 điều kiện 1 coi như đã có số đo.**

### Gate 5B — bất biến 6: alpha khớp từng lệnh ✅

Hai lỗi riêng biệt, cùng một họ: `vs_benchmark` **chưa bao giờ được gọi**
trên đường tự động, và nó **bỏ mẫu im lặng** khi lệch định dạng ngày.

Đã vá lệch định dạng ở **điểm dùng** (`ro_chuan_tu_chuoi_gia` chuẩn hoá cả
hai phía) thay vì sửa 125 file cache gốc.

**Phép đo bất biến 6 đầu tiên của dự án:**

```
lệnh đã đóng                        112
lệnh bị bỏ vì thiếu cặp ngày          0
TB lợi nhuận mỗi lệnh của hệ thống  +0,792%
TB VN-INDEX trong CÙNG khoảng đó    +0,702%
alpha                               +0,090%
KTC 95%                             [−1,166% ; +1,391%]   ← chứa 0
kết luận            không khác chuẩn một cách có ý nghĩa
số lệnh thắng chuẩn                  35/112  (31%)
```

**Gần như toàn bộ +14,24% cộng dồn là beta thị trường.** Con số này độc
lập với rho = −0,019 của `MO-XE-KIEN-TRUC.md` và đi cùng hướng.

### Còn treo sau 5A/5B

- **Quyết định thiết kế chưa chốt (mục 5A của kế hoạch):** `run_daily` ghi
  `stop_loss` lại ở mỗi nhịp quét, tính trên nến **chưa đóng**. Mức stop
  cuối phụ thuộc giờ nào máy được bật. Hoặc chỉ ghi trailing stop ở ATC,
  hoặc chấp nhận và ghi rõ rằng sổ này không tái lập được. **Cần người dùng.**
- **5C** (cấm in "quán quân", mỗi vòng một tiến trình) và **5D** (dựng lại
  walk-forward — chặn bởi C4) chưa làm.
- **Phase 6** giờ đã có số đo để quyết, nhưng ba phương án A/B/C vẫn cần
  người dùng chọn.

---

## Phiên 2 (tiếp) — PHASE 5C

Bất biến 7. Làm được **3/4 phần**; phần thứ tư cần người dùng quyết.

### Đã xong

**1. Khoá `_ANALYZE_CACHE` phải mang trạng thái bộ nhớ post-mortem.**
Kế hoạch mô tả vấn đề là "20 vòng không độc lập". Đọc mã thì cơ chế cụ thể
hơn: `_analyze()` ghi nhớ một giá trị **không phải hàm thuần của khoá** —
`master_agent.run()` cộng `sl_penalty` lấy từ bộ nhớ đang phình ra. Đo được:
bộ nhớ đổi 0 → 1.331 mẫu, cùng lát cắt, điểm vẫn y nguyên 61. Sau khi sửa:
61 → 49, đúng −12 = `PENALTY`.

**2. Gỡ 7 khối "quán quân"** khỏi `evaluate_custom71_results`,
`optimize_20_loops`, `optimize_20loops_custom71_18m`, `optimize_agent`,
`optimize_custom_71stocks_18m`, `optimize_vn100_18m`, `optimize_vn50`.
Thêm `dai_ket_qua.py` (bảng dải sắp theo **số lệnh**, đánh dấu dòng nhiều
mẫu nhất) và cổng chặn tái phạm quét chuỗi bằng AST.

> **Phát hiện nặng hơn việc in:** 3 script không chỉ *in* quán quân, chúng
> **dùng** tham số của nó — chạy lại `cmd_seed` với ngưỡng vòng thắng rồi in
> *"✅ Đã cập nhật Sổ lệnh chính thức với tham số tối ưu 20 Vòng thành công!"*
> Chúng ghi vào `SCRATCH_DB` chứ không phải `paper_trades.db` — gác chống
> ghi đè hoạt động đúng. Chỉ **lời thông báo** là sai. Đây đúng hình dạng sự
> cố 12/08, khác mỗi đích đến. Đã sửa thông báo thành nội dung thật.

**3. Nhãn "18 tháng" là bịa — đã sửa.** Subcommand `seed` **không có**
`--start`/`--end` trong argparse, và `cmd_seed` không đọc hai trường đó.
Tham số được đặt, được truyền, và bị bỏ qua. Nay `cmd_seed` tôn trọng
start/end (so trên 10 ký tự đầu để chịu được cả hai định dạng cache) và
**luôn in ĐỘ PHỦ THẬT** trước khi chạy.

**Ngừng xoá bằng chứng.** Hai script kết thúc bằng `os.remove()` xoá sạch
các `.db` mỗi vòng. Đó là lý do chỉ còn 8/20 sổ của lần chạy sinh ra
+636,11% — và chính 8 sổ còn sót mới cho phép đo lại hôm nay rằng **win
rate cả dải 48–59 chỉ trải 28,2%–30,7%**, tức ngưỡng không hề cải thiện
chất lượng chọn mã.

### 4. Gác đa luồng + tiến trình riêng ✅

Người dùng chọn **B rồi A**.

**B — gác.** Bản sửa khoá cache làm ô nhiễm *lộ ra* nhưng không gỡ nó:
`_ENGINE_CACHE` vẫn giữ MỘT engine, `sl_patterns` vẫn dùng chung. Luồng
không sửa được — đặt lại cache giữa vòng sẽ đè lên các vòng chạy song song,
thread-local thì rò rỉ vì 20 vòng dùng chung 8 luồng. Nên cấu hình này nay
**nổ**: `_gac_da_luong()` chặn khi post-mortem BẬT và `_analyze` bị gọi từ
hơn một luồng trong cùng tiến trình.

Thông báo lỗi nêu **hai** lối đi hợp lệ: một tiến trình mỗi vòng, hoặc
`POST_MORTEM_ENABLED=0` — khi tắt, `sl_penalty` luôn 0 nên `_analyze` trở
lại là hàm thuần và đa luồng hợp lệ. **Không có cửa thoát bằng biến môi
trường:** cấu hình bị chặn ở đây không cho ra kết quả dùng được.

**A — dựng lại script.** Chỉ đổi executor thì hỏng: `download()` nằm ở mức
module, spawn khiến 8 worker tải lại 71 mã. Đã dời phần dựng dữ liệu vào
`main()`; `run_single_loop()` nhận tham số qua `item` thay vì biến toàn cục.

Kiểm chứng bằng chạy:

```
nạp module            0,47s, không tải gì     (trước: tải 71 mã)
run_single_loop       pickle được
POST_MORTEM_ENABLED   có mặt trong worker = 1
biến toàn cục symbols đã biến mất
mức module            không còn lời gọi có tác dụng phụ nào
```

**Gate 5C vẫn CHƯA nghiệm thu** — "chạy 2 lần cùng một script → ra cùng
bảng" cần chạy script thật, hàng giờ, không làm được trong phiên. Nhưng cấu
hình sai nay không còn chạy im lặng được nữa.

---

## NĂM Ô C1–C5 — ĐÃ TRẢ LỜI (20/08/2026)

Người dùng uỷ quyền cho phiên này chọn. Mỗi ô kèm bằng chứng đo được trong
phiên, không phải kèm khuyến nghị sẵn của kế hoạch.

### C1 — Cache VN-INDEX quá hạn → **DỪNG PHIÊN QUÉT** (ngưỡng 3 phiên)

Chạy hàm thật hôm nay:
```
market_filter.status()        = {'active': True, ... → 2026-08-07}
is_vni_bullish('2026-08-20')  = False
is_vni_bullish('2030-01-01')  = False
```
Cổng báo **BẬT** trong khi từ chối **mọi ngày tương lai vĩnh viễn**. 14 ngày,
0 lệnh, không ai biết. Chỗ nguy hiểm không phải *mất* dữ liệu — mà là **dữ
liệu cũ trông giống dữ liệu mới**. Mất dữ liệu thì fail-open còn nhìn thấy
được; cũ mà im lặng thì fail-closed âm thầm, đúng chiều tệ nhất.

Kèm theo, bắt buộc: bỏ `except Exception: vni_ok = True`
(`paper_trading.py:208`) — lỗi khi hỏi cổng không được im lặng thành "cho qua".

### C2 — **MỘT NƠI: GitHub Actions.** Tắt Task Scheduler.

Đo trên trang Actions hôm nay: **27/29 lượt xanh**, mỗi lượt 8–9 phút, chạy
bất kể máy có bật hay không, và mọi lượt hỏng đều để lại log + artifact.

Máy cục bộ thì phủ sóng phụ thuộc máy có thức: 18/08 chỉ 5 lượt (máy tắt
phần lớn ngày), 19/08 được 14 lượt. Và lượt hỏng **không để lại gì**.

Bằng chứng trực tiếp cho rủi ro hai nơi: ngay trong phiên này, Task
Scheduler chạy lúc 09:10 và ghi 70 quyết định **trong lúc tôi đang sửa
`run_daily.py`**.

> **Điều kiện trước khi tắt máy cục bộ:** thêm retry cho bước "Kéo sổ lệnh".
> Cả 2/29 lượt đỏ đều chết ở đúng bước đó, sau 2 giây, và bước quét bị
> skipped — nhịp đó không quét gì cả.

#### 21/08/2026 — điều kiện đã đủ, và một phép đo làm đổi cách hiểu C2

Retry đã có: `google_sheets_sync.keo_so_co_thu_lai()`, workflow gọi nó,
8 test khoá ở `tests/test_keo_so_thu_lai.py`. Test then chốt nhất là điều
kiện tiên quyết của mọi cơ chế thử lại — *một lần `pull()` hỏng để lại sổ
y như trước*. Thiếu tính chất đó thì thử lại còn tệ hơn không thử. Test
đó được kiểm bằng đột biến: sửa `pull()` thành DELETE+commit trước lời
gọi mạng thứ hai thì test đỏ `(0,1) != (1,1)`.

Task Scheduler **đã ở trạng thái Disabled** khi kiểm (chạy lần cuối 20/08
lúc 10:40), tức C2 đã xảy ra trên thực tế trước khi điều kiện của nó đủ.

Đo lại độ tin cậy của lịch GitHub trên 35 nhịp thay vì 1 ngày:

```
Ngày làm việc đủ (17→20/08) : 6/12 nhịp mỗi ngày = 50%
Nổ đúng phút đã hẹn         : 1/32 lần
Trễ điển hình               : 5 → 90 phút
Lượt sau giờ đóng cửa       : 4/4 ngày, 15:29→15:33 giờ VN
```

Cách hiểu cũ ("Actions chạy đều, máy thì phụ thuộc máy có thức") không
sai nhưng thiếu. Đúng hơn là: **Actions rơi mất khoảng một nửa số nhịp
trong phiên, nhưng chưa ngày nào lỡ lượt sau đóng cửa** — và vì
`evaluate_open()` chấm trên nến ngày, lượt đó mới là lượt quyết định.

Hai điều C2 chưa xử lý, ghi ra để không quên:

1. **Không có lưới dự phòng và không có chuông.** Một ngày mà mọi lượt
   Actions đều hỏng thì ngày đó không được quét, và không ai biết. Trước
   đây máy cục bộ vô tình làm lưới; giờ không còn.
2. **Việc né giờ nghỉ trưa trong cron không còn hiệu lực.** Nhịp 04:30
   UTC bị trễ đã rơi vào 05:03 → 05:56 UTC, tức 12:03 → 12:56 giờ VN.
   Không gây hại (giá đứng yên) nhưng ý định trong mã không khớp thực tế.

### C3 — App cloud: **GIỮ "chưa có dữ liệu"**

Đã smoke test hôm nay với `paper_trades.db` đổi tên: tab Tài khoản chỉ còn
một dòng cảnh báo, không hàng ACB bịa nào. Nó hoạt động.

Cho app đọc Sheets sẽ thêm một lời gọi mạng và một hộ tiêu thụ quota vào
**mỗi lần tải trang**, đồng thời thêm một bên tham gia vào kho ngoài đúng
lúc C2 đang rút bớt. Chỉ xem lại nếu có người thật sự cần xem sổ trên cloud.

### C4 — **DỰNG LẠI** walk-forward từ `025507c`

Phase 5C làm cho **phép tìm kiếm** trung thực, nhưng không sinh ra được một
ngưỡng dùng được. Không có 5D thì **không có cơ chế nào** sinh ra nó —
`NGUYEN-TAC-DO-LUONG.md` nói thẳng: *"cho tới khi dựng lại, dự án không có
công cụ nào hiện thực hoá bất biến 7 và 8"*.

Dự án **đã từng** làm được: phép đo 07/08 cho 108 lệnh ngoài mẫu, alpha
−0,63% KTC [−2,09; +0,84]. Công cụ bị mất, không phải năng lực bị mất.

Việc đầu tiên: đổi tên `walkforward_vn100.py` → `.broken` — nó vẫn
`os.remove(sl_pattern_memory.json)` ở dòng 36.

### C5 — **ĐỂ TRỐNG + DỪNG MỞ LỆNH MỚI** cho tới khi 5D sinh ra ngưỡng hợp lệ

Đo được hôm nay trên 8/20 sổ còn sót của chính lần chạy sinh ra +636,11%:

```
win rate toàn dải ngưỡng 48→59      28,2% → 30,7%   (chênh 2,5 điểm)
tương quan ngưỡng ↔ số lệnh         −0,999
tương quan số lệnh ↔ vốn đỉnh       +0,990
ngưỡng 50 hơn ngưỡng 48             1,57/636 = 0,25%
```

**Ngưỡng không cải thiện chất lượng chọn mã** — win rate phẳng chứng minh
điều đó, và nó còn *cao hơn* ở ngưỡng 58–59. Thứ ngưỡng điều khiển là **số
lệnh**, và số lệnh điều khiển **đòn bẩy**. "Quán quân" chỉ là vòng ôm nhiều
vị thế cùng lúc nhất.

Cộng thêm: alpha in-sample +0,090% KTC [−1,166; +1,391] chứa 0; alpha ngoài
mẫu 07/08 là −0,63% cũng chứa 0. Và post-mortem đang trừ 12 điểm cho 92,5%
tín hiệu, nên rào thực tế đã là ~62 chứ không phải 50.

Hệ thống **đã ở đúng trạng thái này 14 ngày** — nhưng do tai nạn. Chọn C5
như thế này không tốn gì, và ngăn tai nạn đó im lặng kết thúc vào đúng lúc
Phase 2 gỡ cổng VN-INDEX.

---

## PHASE 2 — CỔNG CHẶN PHẢI LỘ RA (20/08/2026)

Làm được vì **C5 đã khoá việc mở vị thế mới trước**. Không có C5 thì giây
phút cổng được gỡ là lệnh mở ở lượt quét kế tiếp, bằng ngưỡng 50,0.

### C5 — dừng mở vị thế mới ✅

`paper_trading.CHO_PHEP_MO_LENH_MOI = False`. Hệ thống vẫn quét, vẫn chấm,
vẫn ghi quyết định, vẫn đóng vị thế đang mở — chỉ không mở mới. Chốt đặt
**sau** mọi cổng khác có chủ đích, để lý do ghi vào sổ cho biết lệnh đó *lẽ
ra* đã mở, và để 2B vẫn thống kê được từng cổng.

Ngoại lệ hẹp: `cmd_seed` bọc trong `_cho_phep_mo_lenh()` — backtest tồn tại
để **đo** chính logic vào lệnh.

> **Bắt được một hỏng học im lặng do chính thay đổi này gây ra.** Ba file
> test dựng fixture *bằng* `consider_entry()`. Với công tắc tắt chúng trả
> sổ **rỗng**, và mọi assert kiểu "không có giá trị 30 trong sổ" đều đúng
> vô nghĩa — 246 test vẫn xanh. Đã bật công tắc trong cả ba, **và** thêm
> `assert j.all_trades()` ngay trong hàm dựng fixture. Đã kiểm chốt đó bằng
> cách tắt công tắc rồi chạy lại: nó nổ đúng như mong đợi.

### 2A — cổng lộ ra khi nó tự tắt ✅

`status()` nay trả về **tuổi dữ liệu** (`ngay_cuoi`, `tuoi_phien`) và đặt
`active=False` khi quá hạn. Quá hạn (>3 phiên, ô C1) thì `is_vni_bullish`
**ném `CacheQuaHanError`** chứ không trả `False` lặng lẽ.

Độ cũ đo so với **ngày đang chấm**, không so với hôm nay — cache chạy tới
2026 mà chấm phiên 2024 thì không hề quá hạn. Đo sai chiều là mọi backtest
nổ oan.

Đã gỡ `except Exception: vni_ok = True` trong `consider_entry`, và cho
`CacheQuaHanError` **xuyên qua** bộ bắt lỗi theo từng mã trong `run_daily`.

### 2B — báo cáo nói về cổng ✅

Trước: `grep "market_filter|status()" run_daily.py` = **0**. Nay mỗi báo cáo
có khối "CỔNG CHẶN — TRẠNG THÁI THẬT". Nghiệm thu bằng lượt chạy thật:

```
Cổng VN-INDEX: BẬT · dữ liệu tới 2026-08-20 · trễ 0 phiên (ngưỡng 3)
Quyết định KHÔNG vào lệnh: 70 — VN-INDEX nằm dưới MA50
```

Lần đầu tiên báo cáo nói ra **vì sao** không có lệnh nào. Và cache VNINDEX
đã được làm mới trong ngày (07/08 → 20/08), nên cổng đang chặn vì thị
trường **thật sự** dưới MA50, không phải vì cache đóng băng.

### 2C — ĐÃ ĐO, CHƯA BẬT

Điều kiện 5 của Gate 2. Chạy `validate_ohlcv` trên cả hai đường:

| Đường | OK | WARN | BLOCK |
|---|---|---|---|
| **cache backtest** (71 mã) | **0%** | 31% | **69%** |
| **quét live** (mẫu 10 mã) | **100%** | 0% | 0% |

Nguyên nhân gần như hoàn toàn là `STALE`: 49 mã dữ liệu cũ 13 ngày (tới
2026-08-07), 22 mã cũ 9 ngày (tới 2026-08-11), thêm 3 mã `PRICE_JUMP`.

**Kết luận, và nó khác một chút so với dự đoán của kế hoạch.** Kế hoạch đoán
bật cổng sẽ chặn nhiều hơn — đúng, nhưng chỉ với **backtest**. Đường quét
live có dữ liệu tươi và 10/10 mã sạch. Nghĩa là:

- bật cổng chất lượng **không** chặn phiên quét production
- nó **sẽ** phơi ra ngay rằng cache backtest cũ 13 ngày
- và việc tiếp theo đúng là **sửa dữ liệu** (`extend_history()`, không phải
  `download()` — `download()` bỏ qua mọi mã đã có cache), không phải nới cổng

### Gate 2 — 4/5

```
✓ test: cache VNINDEX cũ → status() báo KHÔNG hoạt động
✓ test: cache quá ngưỡng → phiên quét dừng có thông báo
✓ báo cáo phiên có dòng về cổng VN-INDEX (nghiệm thu bằng lượt chạy thật)
✗ test: packet có WARN → decision ghi đúng mức đó, KHÔNG phải 'OK'
✓ đã có con số đo
```

Điều kiện 4 là việc **bật** cổng — chưa làm vì nó chặn 69% backtest và đó
là thay đổi hành vi đủ lớn để cần người dùng quyết.

---

## PHASE 2 HOÀN TẤT — Gate 2 đủ 5/5 (20/08/2026)

### Phát hiện lớn nhất: không có công cụ nào làm mới được cache

Truy từ phép đo 2C (69% rổ BLOCK vì `STALE`):

```
download(force=False)   bỏ qua MỌI mã đã có cache      → không làm mới
download(force=True)    ghi đè trọn khoảng             → MẤT lịch sử
extend_history()        bỏ qua nếu lịch sử đủ xa       → chỉ nối về quá khứ
```

Đường duy nhất còn lại là `download(force=True)`, và nó đã gây hậu quả thật
**ngay trong ngày**: `backtest/cache/VNINDEX.csv` đi từ 1.724 phiên
(2019-09-13 → 2026-08-07) xuống **1.655 phiên** (2020-01-02 → 2026-08-20).
Tươi lên và **mất 4 tháng lịch sử** — đúng thứ bất biến 8 cần.

`extend_history()` đã biết hợp nhất giữ bản ghi cũ (2/3 test mới xanh ngay
từ đầu). Nó chỉ thiếu một điều kiện: cũ ở **đuôi** thì cũng phải nối.
Ngưỡng độ tươi lấy trực tiếp từ `data_quality.STALE_WARN_DAYS` để hai bên
không thể lệch nhau.

**Kết quả chạy thật trên 71 mã:**

```
độ phủ     49 mã @08-07 + 22 mã @08-11   →   71/71 @2026-08-20
lịch sử    0 mã mất phần đầu (đối chiếu bản sao lưu trước khi chạy)
chất lượng OK 0% / WARN 31% / BLOCK 69%  →  OK 88,7% / WARN 11,3% / BLOCK 0%
```

### 2C — cổng chất lượng đã cắm ✅

Cắm vào gặp **đúng cùng lỗi khái niệm với 2A**: `validate_ohlcv` đo độ cũ so
với *hôm nay*, nên backtest replay phiên 2024 thì mọi lát cắt "cũ 2 năm" và
bị BLOCK sạch. Đã thêm `as_of` — đo so với **ngày đang chấm**.

Luật chặn qua **ba** lần lặp, mỗi lần do một test bắt được:

| Bản | Luật | Vì sao sai |
|---|---|---|
| gốc | `!= "OK"` | code chết — packet luôn mang `"OK"` cứng |
| thứ hai | `== "BLOCK"` | quá hẹp — chuỗi `'SYNTHETIC'` (dữ liệu bịa) lọt qua |
| cuối | `not in {"OK","WARN"}` | fail-closed với mọi mức lạ |

WARN không còn bị chặn như BLOCK: gộp hai mức là mất thông tin.

> **Một lượt quét thật ghi 70/70 dòng `OK` — trông y hệt hành vi dán cứng.**
> Dữ liệu tươi thì OK là đúng, nhưng *"đúng vì tính ra"* và *"đúng vì dán
> cứng"* không phân biệt được từ kết quả. Đã thêm test ép một trường hợp
> KHÔNG-OK đi qua trọn đường `run_session → _analyze → consider_entry →
> record_decision`.

### Gate 2 — 5/5 ✅

```
✓ cache VNINDEX cũ → status() báo KHÔNG hoạt động
✓ quá ngưỡng → phiên quét dừng có thông báo
✓ báo cáo phiên có dòng về cổng (nghiệm thu bằng lượt chạy thật)
✓ packet có WARN → decision ghi đúng mức đó, KHÔNG phải 'OK'
✓ đã có con số đo
```

### Công cụ mới: `tools/kiem_ban_sach.py`

Clone HEAD ra thư mục tạm rồi chạy pytest ở đó — tái hiện runner CI. Riêng
phiên 20/08 đã gặp **bốn** lỗi phụ thuộc môi trường, nên *"xanh ở máy tôi"*
không còn là bằng chứng đủ.

Chính công cụ này cho tôi một kết quả sai lệch khi mới dùng: nó clone HEAD
chứ không phải cây làm việc, nên báo "xanh" trong khi thay đổi chưa commit.
Nay nó cảnh báo rõ khi cây làm việc bẩn.

---

## CI — bốn lỗi phụ thuộc môi trường trong một phiên

`kiem-dinh` đỏ trên runner trong khi mọi thứ xanh ở máy. Ba bậc tái hiện,
mỗi bậc loại trừ một biến:

| Môi trường | Kết quả |
|---|---|
| máy phát triển (Win, 3.13, đủ file) | xanh |
| clone sạch (Win, 3.13, thiếu file) | bắt được lỗi #3 |
| clone sạch + Python 3.11 | xanh → không phải phiên bản Python |
| runner Ubuntu | vẫn đỏ → còn lại là **thời gian chạy** |

Bốn lỗi, cùng một họ — *test đo môi trường chứ không đo hành vi*:

1. **`st.secrets` bị cache** — nhánh đọc-file không bao giờ chạy tới.
2. **`is_vni_bullish` bị ghim ở mức module** trong `test_paper_trading.py`,
   rò sang `test_market_filter.py`.
3. **`test_thieu_key_van_chay_binh_thuong`** không cách ly `st.secrets`; máy
   có key thì xanh, runner không có thì đi tiếp tới `import vnstock` và nổ
   `ImportError` vì module `vnai` giả của test thiếu `optimize_execution`.
4. **`test_gac_no_khi_post_mortem_bat_va_chay_da_luong`** —
   `threading.get_ident()` chỉ duy nhất giữa các luồng **còn sống**. Thân
   hàm quá ngắn nên trên máy nhanh luồng 1 xong trước khi luồng 2 bắt đầu,
   cả hai nhận **cùng id**, gác không nổ.

Lỗi #4 đáng chú ý vì nó cho thấy **gác đúng còn test sai**: chạy tuần tự thì
an toàn thật — không bao giờ có hai vòng đọc cùng `sl_patterns` một lúc.
Thứ cần chặn là chạy **đồng thời**, và khi đó các id đều còn sống nên phân
biệt được. Đã thêm `threading.Barrier` để ép hai luồng chồng nhau.

### Làm cho lỗi CI đọc được mà không cần đăng nhập

Log Actions cần đăng nhập; **annotation thì công khai qua API**. Trước khi
sửa, một lượt CI đỏ chỉ để lại đúng dòng `Process completed with exit code 1`
— không đủ để sửa bất cứ gì. Nay bước test in tên test đỏ thành `::error::`,
và câu trả lời hiện ra ngay ở lần chạy kế tiếp.

---

## PHASE 6 — phương án C (20/08/2026)

Người dùng hỏi thẳng: *"tại sao phải xoá đi xây lại?"* Câu hỏi đúng. Đo lại
thì không cần xoá — cần **thay dữ liệu bẩn bằng dữ liệu thật**.

```
file cũ: 6.327 mẫu · 100 mã · tín hiệu 2021-11 → 2026-07
         trường nói vòng nào/dữ liệu nào sinh ra : KHÔNG CÓ
         khớp một lệnh THẬT trong sổ            : 56/6.327 = 0,89%
```

Rổ thật 71 mã, sổ thật 113 lệnh — không cách nào sinh ra 6.327 mẫu từ 100 mã.

**Không chọn B** (giữ file, bổ sung provenance): thông tin để truy nguồn
**không tồn tại** — các vòng sinh ra nó đã bị `os.remove()` xoá.
**Không chọn A** (xoá sạch): A để lại hệ thống sạch nhưng **không còn đường
ống**; ngày muốn học thật vẫn phải dựng lại từ đầu.

### Gate 6 — 3/3 ✅

```
1. đo trước–sau trên 280 lượt chấm gần nhất
     TRƯỚC (6.327 mẫu): 255/280 = 91,1% bị trừ 12 điểm
     SAU   (   44 mẫu):   7/280 =  2,5%
     → 248/280 mã (88,6%) được TRẢ LẠI 12 điểm
2. Gate 5A vẫn xanh sau khi đổi
3. không còn khẳng định "Self-Improving" — có test khoá
```

### Ba chốt giữ cho C không thoái hoá

1. `record_sl_trade` **từ chối** mẫu không khai `trade_id` + `nguon`
2. `load_memory` **bỏ** mẫu không có provenance và **nói ra** bao nhiêu
3. `tools/dung_lai_bo_nho.py` dựng lại từ lệnh cắt lỗ đã đóng; thiếu
   breakdown thì **bỏ**, không điền mặc định

### Nói thẳng về kỳ vọng

44 mẫu phủ **0,9%** không gian giá trị agent sinh ra — cơ chế gần như vô
hiệu. Đó là câu trả lời trung thực với 113 lệnh, không phải thất bại. Giá
trị của C là **đường ống đúng đang chạy và tích luỹ trung thực**.

### Chưa làm, có chủ đích: không bật `save_memory()`

Bật ngây thơ sẽ quay lại lỗi 47-vs-59 — trong một phiên quét, mã A đóng
bằng cắt lỗ sẽ làm lệch điểm mã B. Sửa đúng cần **một trục thời gian thứ
hai**: chỉ dùng mẫu đã học *trước khi phiên bắt đầu*, giống bất biến 3
("dời stop chỉ có hiệu lực từ phiên sau"). Việc riêng.

---

## PHASE 5D — dựng lại walk-forward (20/08/2026)

Ô C4 đã chọn "dựng lại". Bản ở `git show 025507c` có cấu trúc đúng (chọn
trên IS, đo trên OOS) nhưng vẫn lấy **6 tháng gần nhất** làm OOS — trái bất
biến 8, vì giai đoạn gần nhất là giai đoạn *đã bị nhìn nhiều nhất*.

### Cách chia khác hẳn: theo **dữ liệu nào đã tồn tại**

Khi nối cache về 2022-01-01 hôm nay, **33/71 mã được kéo về thêm 25.219
phiên** — dữ liệu **không tồn tại** trong cache lúc các vòng tối ưu chạy,
nên không vòng nào *có thể* đã nhìn thấy.

Đó là vùng kiểm định duy nhất trong dự án mà tính "chưa nhìn" **chứng minh
được**, thay vì giả định.

Ranh giới đó chỉ tồn tại trong bản sao lưu tạm, nên đã ghi lại ngay:
`docs/moc_du_lieu_sach.json` — 71 mã, kèm provenance.

```
vùng sạch : 25.219/80.939 phiên = 31,2%, trên 33/71 mã
OOS (đo)          = phiên <  mốc     ← chưa thể đã nhìn
IS  (chọn ngưỡng) = phiên >= mốc     ← vùng đã bị nhìn
```

### Luật chọn ngưỡng nêu TRƯỚC

Chỉ ngưỡng đạt **≥30 lệnh** trên IS mới đủ tư cách; trong số đó lấy kỳ vọng
cao nhất. Không có luật nêu trước thì "chọn trên in-sample" chỉ là cực đại
của N lần thử dưới một cái tên khác.

### Nghiệm thu end-to-end (3 mã · 2 ngưỡng · stride 25)

```
ngưỡng 48 :  8 lệnh · kỳ vọng +11,02%
ngưỡng 55 :  4 lệnh · kỳ vọng  +8,10%
ngưỡng chọn: None  →  TỪ CHỐI dòng 8 lệnh, không chạy OOS
```

Máy chạy đúng, **và gác hoạt động**.

### Hai file bị vô hiệu hoá

| File | Vì sao |
|---|---|
| `walkforward_vn100.py.broken` | ba lỗi đã ghi ở đầu file. Lợi ích phụ: nó là script **duy nhất** gọi `os.remove(sl_pattern_memory.json)` — nay `grep` toàn repo trả về **0** |
| `experiment_signal_source.py.broken` | import `_slim`/`bootstrap_ci` từ `walkforward_vn100`. Hai tên đó **chưa bao giờ tồn tại** — `git log -S"def bootstrap_ci" --all` trả về 0 commit. File chưa bao giờ nạp được, và không ai tham chiếu. **Không phải hậu quả của lần đổi tên hôm nay** |

Chốt `test_requirements` là thứ bắt được file thứ hai. Đã tách thông báo của
nó thành hai trường hợp — *"thư viện ngoài chưa khai báo"* và *"import
HỎNG — module không tồn tại ở đâu cả"* — vì gộp chung làm thông báo nói sai
bản chất vấn đề.

---

## KẾT QUẢ WALK-FORWARD — 20/08/2026

Chi tiết đầy đủ: `docs/ket-qua-walkforward-20260820.md`. Tóm tắt:

```
IS  : 71 mã, ngưỡng chọn = 62,0 (luật nêu trước: ≥30 lệnh, rồi kỳ vọng cao nhất)
OOS : 33 mã, 408 lệnh, trên 25.219 phiên CHƯA THỂ đã bị nhìn

kỳ vọng   +0,431%   KTC [−0,469 ; +1,407]   ← chứa 0
alpha     −0,160%   KTC [−0,903 ; +0,646]   ← chứa 0
          → không khác chuẩn một cách có ý nghĩa

(alpha sửa 21/08/2026. Con số cũ +0,428% SAI — nó so với một rổ chuẩn
 lãi ≈ 0%, thứ dữ liệu không chống đỡ. Chi tiết và độ nhạy của alpha
 theo cách dựng rổ: docs/ket-qua-bo-nho-rieng-20260821.md)
vốn đỉnh  542%  ·  net +36,14%  →  quy về 100% vốn: +23,92%
```

Kỳ vọng trong mẫu +1,52% → ngoài mẫu **+0,43%** (mất 72%). WR 32,3% → 25,5%.

**Phép đo thứ tư cho cùng một câu trả lời, và là phép đo chính xác nhất**
(KTC ±0,82 so với ±1,5 của hai lần trước, vì mẫu 408 lệnh lớn nhất).

**Đính chính:** kết luận trước đó của tôi — *"win rate phẳng 28,2–30,7%,
ngưỡng không cải thiện chất lượng chọn mã"* — đo trên 8 sổ còn sót và **sai
với vùng IS này**: WR tăng đều 26,8% → 32,3%. Kết luận đúng: ngưỡng **có**
cải thiện **trong mẫu**, nhưng phần cải thiện đó **không sống sót ra ngoài
mẫu**.

**C5 không đổi**, nhưng lý do đổi: từ "chờ vì chưa có cách chọn" thành
"đã chọn được bằng cách hợp lệ, và phép đo nói ngưỡng đó không có lợi thế
phân biệt được với cầm đều cả rổ".

---

## CẢNH BÁO NỘI PHIÊN — ĐÃ TỰ LÀM CHỨNG, VÀ ĐÃ CÓ CANH GÁC (22/08/2026)

### Lượt chạy tay 22/08 trả lời được câu hỏi bỏ ngỏ hôm 21/08

Lượt `88216494021`, 08:18 ICT thứ Bảy. Bốn dòng mốc hiện ra trong nhật ký:

```
[noi-phien] bắt đầu lúc 2026-08-22 08:18:04 ICT
[noi-phien] vị thế đang mở: 0
[noi-phien] không vị thế nào chạm SL/TP.
[noi-phien] xong.
```

Lượt 21/08 để lại **0 dòng**, và khi đó không phân biệt được "chạy rồi,
không có gì" với "chết ngay từ dòng đầu". Nay phân biệt được. Dòng `xong.`
in ra *sau* khối ghi `$GITHUB_STEP_SUMMARY`, nên nó cũng chứng minh khối đó
chạy trót lọt — không phải suy đoán.

Thứ tự bước xác nhận đúng trên runner thật, và đây là thứ tự bắt buộc:

```
5. Kéo sổ lệnh từ Google Sheets   → 113 lệnh, 14.085 quyết định
6. Cảnh báo chạm SL/TP trong phiên
7. Quét thị trường và cập nhật sổ lệnh
8. Đối chiếu sổ local với kho ngoài → local 113 · sheet 113
```

Không có annotation thật nào phát ra. Mọi chuỗi `::warning::` tìm thấy
trong nhật ký đều là dòng mã được echo lại, không phải output.

### Nhưng phần quan trọng vẫn chưa chạy lần nào

`vi_the_dang_mo()` trả về danh sách **rỗng**, nên vòng lặp trong `quet()`
không chạy. Nghĩa là `intraday_data.tai()` — gọi mạng, `ensure_api_key()`,
lọc lưới 24/7, quy đơn vị, `_kiem_don_vi()` — **chưa từng thực thi trên
runner**. Cái chuông đã chứng minh nó biết nói "không có gì"; nó chưa chứng
minh được nó biết kêu.

Và 0 vị thế không phải chuyện tạm thời. Hai cổng cùng chặn:

```
Ngưỡng mua        : ĐỂ TRỐNG (ô C5)
Cổng VN-INDEX     : BẬT · VN-INDEX dưới MA50
71/71 quyết định  : KHÔNG vào lệnh
Sổ lệnh           : 113 đã đóng · 0 đang mở
```

Nên đường mã đó sẽ nằm im cho tới đúng ngày đầu tiên có lệnh mở — tức nó
chạy lần đầu vào đúng lúc nó buộc phải đúng. Đó là lúc tệ nhất để phát hiện
vnstock không gọi được từ IP của runner.

### Canh gác — nạp thử một mã khi sổ rỗng

`canh_bao_noi_phien.canh_gac()` + `quet_va_canh_gac()`. Khi `so_vi_the == 0`
thì nạp nến 30 phút của một mã (mặc định ACB) để chứng minh đường dữ liệu
còn dùng được. Có vị thế thì các lần nạp thật đã tự chứng minh rồi, nên điều
kiện này phủ **đúng** chỗ trống chứ không phủ chồng.

Ba điểm thiết kế, đều là để nó không kêu oan:

| Điểm | Vì sao |
|---|---|
| Hỏi một **khoảng** 10 ngày, không hỏi riêng hôm nay | Nhịp 09:00 chạy trước khi nến 30 phút đầu tiên kịp đóng. Hỏi riêng hôm nay thì mỗi phiên có đúng 1 báo động giả, và vài ngày là người ta thôi đọc. |
| Nguồn **ném** hoặc **rỗng cả khoảng** mới tính là hỏng | "Chưa có nến hôm nay" là bình thường, không phải sự cố. |
| So giá trung vị với hằng số 1.000 VNĐ | Sổ rỗng thì không có mốc SL/TP nào để `_kiem_don_vi()` so. Nguồn lặng lẽ đổi sang nghìn đồng làm `low <= stop_loss` đúng với **mọi** vị thế — chính cái bẫy ở `NGUYEN-TAC-DO-LUONG.md`. |

Điều kiện "khi nào cần canh gác" nằm trong module, **không** nằm trong YAML.
Logic trong heredoc thì không test được — bài học đã lặp lại nhiều lần ở dự
án này.

Khoá bởi `tests/test_canh_gac_du_lieu.py` (14 test, chạy offline). Ba đột
biến đã thử, cả ba đều làm test đỏ:

```
đòi phải có nến HÔM NAY mới coi là đạt  -> 1 đỏ  (kêu oan lúc 09:00)
canh gác LUÔN LUÔN, kể cả khi có vị thế -> 1 đỏ  (gọi mạng thừa mỗi nhịp)
bỏ phép kiểm thang giá                  -> 2 đỏ
```

### Chỗ mù thứ hai: python nhúng trong YAML chưa từng được kiểm cú pháp

Bước cảnh báo có hơn 70 dòng python nằm trong heredoc. Đoạn đó chạy trên
runner y hệt một file `.py`, nhưng `rglob("*.py")` không thấy nó và không
test nào import nó. Sau bản vá hôm nay nó còn dài thêm.

Đây đúng là lớp lỗi đã làm CI đỏ hôm 21/08 (PEP 701, f-string 3.12-mới).
Lần đó nó nằm trong một file `.py` nên `tools/kiem_cu_phap_311.py` bắt được.
Nằm trong heredoc thì không có gì bắt.

`kiem_cu_phap_311.doan_nhung()` nay trích mọi heredoc **có trích dẫn**
(`<<'X'`) từ `.github/workflows/*.yml`, ghi ra file tạm và kiểm cùng một
lượt với các file `.py`. Heredoc **không** trích dẫn thì bỏ qua có chủ đích:
shell nội suy `$…` trước khi python thấy, nên thứ trên đĩa không phải thứ
chạy thật, và kiểm nhầm còn tệ hơn không kiểm.

Số đoạn nhúng được in ra cùng số file, để một số 0 ở đó **nhìn thấy được**:

```
Đã kiểm 89 file .py + 3 đoạn nhúng trong workflow, bằng Python 3.11.
```

Đã kiểm chứng bằng cách nhét một biểu thức 3.12-mới vào đúng heredoc đó:

```
⛔ quet-so-lenh.yml:136 (PYCB):76  —  unterminated string literal
1 chỗ KHÔNG nạp được bằng 3.11. CI sẽ đỏ.      (mã thoát 1)
```

Khoá bởi `tests/test_doan_nhung_workflow.py` (7 test). Test cuối neo vào
**file thật**, không phải file giả — một bộ trích trả rỗng vẫn in
"✅ Mọi file nạp được bằng 3.11", y hệt khi mọi thứ đều sạch. Đột biến
`doan_nhung` luôn trả rỗng làm 4 test đỏ.

### Trạng thái sau bản vá

```
360 test xanh (339 + 14 canh gác + 7 trích đoạn nhúng)
0 CHẶN · 37 cảnh báo (không đổi)
89 file .py + 3 đoạn nhúng — nạp được bằng 3.11
```

**Còn chưa biết:** canh gác chưa chạy trên runner lần nào. Nhịp theo lịch
gần nhất (thứ Hai 09:00 ICT) sẽ là câu trả lời — và câu trả lời đó đọc được
ngay trên trang lượt chạy, không cần tải nhật ký về.

---

## PHA WYCKOFF THẬT, VÀ AGENT CƠ BẢN THẬT (22/08/2026)

Hai ô trên giao diện từng bị gỡ ngày 21/08/2026 vì cùng một lý do: chúng
hứa một thứ không tồn tại. Hôm nay chúng được trả lại, lần này có mã nguồn
đứng sau.

### 1. `pha_wyckoff.py` — ô "Vùng điểm AI" trở lại thành "Pha Wyckoff"

Ô này từng hiện `Pha C — Wyckoff Spring` cho **mọi** mã có điểm ≥ 60. Nó
là điểm số chia thành bốn khoảng, đội lốt một kết luận về hành vi dòng
tiền lớn. Bản vá 21/08 đổi nhãn thành `Vùng điểm ≥ 60 (điểm cuối, không
phải pha Wyckoff)` — đúng nhưng vô dụng.

`doc_pha(df, he_so_gia)` nay đọc tương quan giá–khối lượng: tìm cụm cao
trào 3 phiên, kiểm nhịp AR, dựng sàn/trần, rồi tìm Spring / UTAD / SOS /
SOW / Markup / Markdown trong 10 phiên gần nhất.

**Ba quyết định thiết kế, cả ba đều để nó không kết luận bừa:**

| Quyết định | Vì sao |
|---|---|
| Biên vùng dựng từ phần **nền**, sự kiện tìm ở phần **sau** — hai phần không giao nhau | Lấy min/max trên cả đoạn thì chính cây thủng sâu nhất định nghĩa ra cái sàn, nên `low < san` không bao giờ đúng và bộ nhận dạng **không bao giờ kêu**. Cùng họ với những phép kiểm báo xanh trên 0 mẫu ở dự án này. |
| Cửa sổ tìm cao trào bị chặn **cả hai đầu** | Cụm khối lượng lớn nhất trong 120 phiên có thể thuộc một cấu trúc đã kết thúc. Bỏ chặn trái, đo trên dữ liệu thật: "vùng dao động" rộng **96%** ở VHM, **61%** ở SSI. Con số đó tự nó nói phép đọc sai. |
| Pha B trả về `CHƯA PHÂN ĐỊNH`, không đoán hướng | Pha B của tích luỹ và pha B của phân phối trông giống hệt nhau. Khác biệt chỉ lộ ra ở pha C. |

Đo trên 40 mã VN100, dữ liệu tới 20/08: 11 pha B · 3 Spring · 2 SOS ·
2 pha A · 1 UTAD · 1 Markdown · 20 "chưa đủ bằng chứng" (7 thiếu AR,
13 biên độ nền quá rộng). Tỷ lệ không kết luận cao là **đúng kỷ luật của
phương pháp**, không phải lỗi ngưỡng. Đừng nới ngưỡng cho ra nhãn đẹp hơn
— đó đúng là cách cái nhãn cũ ra đời.

**Một lỗi logic do smoke test trình duyệt lôi ra, không phải do test bắt.**
Lượt quét ACB hiện `Pha C — Spring · TÍCH LUỸ · đã xác nhận` trong khi
dòng bằng chứng ngay bên dưới ghi **"cao trào MUA"**. Nhánh sự kiện tự ghi
đè cấu trúc mà không ai đối chiếu lại với điểm neo. Nay `_doi_chieu_boi_canh()`
chạy trên cấu trúc ĐÃ KẾT LUẬN: mâu thuẫn thì nói thẳng ("nhiều khả năng
là tái tích luỹ") và **hạ độ tin**. ACB sau vá: `nhiều khả năng`.

Đây là lần thứ hai một lỗi mặt-người-đọc chỉ lộ ra qua trình duyệt chứ
không qua test — lần trước là thẻ "Trạng thái hệ thống AI" hôm 21/08.

### 2. `fundamental_agent.py` — Agent Cơ Bản

Ô "Fundamental Agent · BCTC Q2" bị gỡ khỏi cả bảng trạng thái lẫn sơ đồ
pipeline ngày 21/08, vì `grep -rn "fundamental" master_agent.py
analysis_agents.py` trả về rỗng.

Nay có thật: đọc bảng `ratio` theo năm từ vnstock/KBS, chấm sinh lời — an
toàn — tăng trưởng — định giá, trả `diem` 0-100 kèm xếp hạng và danh sách
cảnh báo. Đo thật ngày 22/08: FPT `TỐT 87`, VNM `TỐT 71`, ACB `KHÁ 68`,
HPG `KHÁ 64`, SSI `KHÁ 58` (kèm cảnh báo đòn bẩy cao).

**Bốn cái bẫy phát hiện khi dò dữ liệu thật, cả bốn đều có test riêng:**

```
1. `total_assets` / `owners_equity` / `profit_after_tax_...` trong bảng
   ratio là TĂNG TRƯỞNG %, không phải số dư. FPT 2022: total_assets =
   -3,81. Tổng tài sản âm là bất khả — đó là -3,81%.
2. Ngân hàng KHÔNG có net_margin / debt_to_equity / interest_coverage.
   Chấm ACB bằng thước doanh nghiệp sản xuất là loại sạch nhóm nặng ký
   nhất rổ VN30.
3. `roe_trailling` và `roa_trailling` bằng 0,0 ở mọi mã, mọi năm.
4. Số liệu cũ hơn 2 năm trông y hệt số liệu hiện hành trên giao diện.
```

### 3. Ảnh hưởng lên điểm giao dịch: **0** — và đó là một quyết định

`master_agent.TRONG_SO_CO_BAN = 0.0`. Điểm cơ bản tham gia theo dạng cộng
lệch `(điểm − 50) × trọng số`, nên trọng số 0 cho ra **đúng** con số như
trước khi có agent này — kiểm được bằng mắt, không cần chạy lại cả sổ lệnh.

Vì sao chưa bật: `experiment_fundamentals.py` đã tính sẵn lực thống kê —
gói cộng đồng vnstock chỉ trả 8 quý, mà yếu tố cơ bản có IC ≈ 0,03–0,05,
nên thiết kế này phát hiện tín hiệu với xác suất ~10%. Ba thiên lệch còn
lại đều đẩy kết quả ĐẸP lên. Quy tắc số 1: một thay đổi làm con số đẹp lên
thì giả định đầu tiên phải là có lỗi.

**Và một rào chắn quan trọng hơn trọng số:** `MasterConsensusAgent(doc_co_ban=False)`
là mặc định. Bảng chỉ số theo năm là trạng thái HIỆN TẠI, đã gồm mọi điều
chỉnh hồi tố, và **không kèm ngày công bố**. Đưa nó vào một phiên năm 2022
là chấm phiên đó bằng số liệu 2025 — nhìn trộm tương lai ở dạng thô nhất.
`backtest/engine.py` và `paper_runner.py` dựng agent bằng constructor rỗng
nên giữ nguyên hành vi cũ và không phát sinh lời gọi mạng nào. Chỉ
`run_full_analysis()` bật nó lên.

### Khoá bằng gì

```
tests/test_pha_wyckoff.py            26 test
tests/test_fundamental_agent.py      22 test  (offline, tiêm hàm tải giả)
tests/test_co_ban_trong_pipeline.py  10 test
tests/test_no_fabricated_data.py     +2 test  (nhãn phải có module đứng sau)
```

`"Pha Wyckoff"` đã **rời** danh sách cấm trong `test_no_fabricated_data.py`.
Nó nằm đó vì cái nhãn từng là tên gọi mỹ miều cho bốn khoảng điểm, không
phải vì hai chữ "Wyckoff" tự nó là điều cấm. Thay chỗ nó là hai test có
điều kiện: nhãn được phép hiện, VỚI ĐIỀU KIỆN app.py gọi `pha_wyckoff.doc_pha`
và `master_agent.py` gọi `FundamentalAgent`.

Mười đột biến đã thử, **cả mười đều làm test đỏ**:

```
biên vùng lấy từ CẢ ĐOẠN (vòng lặp logic)   -> đỏ
bỏ chặn trái khi tìm cao trào               -> đỏ
pha B đoán bừa là TÍCH LUỸ                  -> đỏ
bỏ đối chiếu bối cảnh                       -> đỏ
Spring không cần Test vẫn "đã xác nhận"     -> đỏ
ngân hàng bị chấm bằng thước doanh nghiệp   -> đỏ
thiếu dữ liệu -> điểm 50 "trung tính"       -> đỏ
bỏ chốt độ tươi số liệu                     -> đỏ
bật trọng số cơ bản lên 0,3                 -> đỏ
backtest cũng đọc dữ liệu cơ bản            -> đỏ
```

Lần chạy đột biến ĐẦU TIÊN có một mục xanh: "bỏ chặn trái khi tìm cao
trào". Test khẳng định `so_phien_nen <= 60`, mà nhánh "chưa đủ bằng chứng"
trả `so_phien_nen = 0` nên cũng thoả — test xanh trên 0 phép kiểm. Đã thêm
`assert r.ket_luan_duoc` trước cận trên đó.

### Trạng thái sau bản vá

```
420 test xanh (394 + 26 Wyckoff, trong đó có 22 cơ bản + 10 pipeline)
0 CHẶN · 37 cảnh báo (không đổi)
94 file .py + 3 đoạn nhúng — nạp được bằng 3.11
Smoke test trình duyệt: 0 traceback, 0 stException, 2 dataframe render
```

**Còn chưa biết:** trọng số cơ bản có nên khác 0 hay không. Câu trả lời
cần ≥40 quý; gói dữ liệu hiện tại cho 8. Đó là giới hạn gói dữ liệu, không
phải giới hạn của mã nguồn.

---

## GÓI SILVER ĐÃ MUA NHƯNG APP CHẠY NHƯ GÓI MIỄN PHÍ (22/08/2026)

### Đo được gì

Tài khoản nâng lên Silver, còn hạn tới 22/11/2026. Máy chủ vnstocks.com tự
xác nhận qua `GET /api/vnstock/license/verify`:

```json
{"deviceRegistered": true, "userType": "paid", "hasActiveSubscription": true,
 "subscription": {"tier": "silver", "endDate": "2026-11-22", "isActive": true},
 "availablePackages": ["vnstock_data","vnstock_ta","vnstock_pipeline","vnstock_news"]}
```

Nhưng thư viện cục bộ nói khác:

```
vnai.get_user_tier() -> {"tier": "free", "limits": {"per_minute": 60}}
```

### Gốc: một ImportError bị nuốt

`vnai/beam/auth.py`:

```python
def _detect_tier(self):
    tier_from_vnii = self._check_vnii_tier()   # import vnii -> ImportError
    if tier_from_vnii: return tier_from_vnii
    if self._has_api_key(): return "free"      # rơi vào đây, không kêu
```

Package `vnii` chưa cài. `_check_vnii_tier()` bắt `ImportError`, log ở mức
debug, trả `None`. Hàm gọi nó rơi xuống `"free"`. **Không lỗi, không cảnh
báo, không dấu vết trên giao diện.**

Chính tài liệu bootstrap của vnstock cũng cảnh báo đúng chỗ này: *"Do not
rely exclusively on local `vnii` logs as it might not be installed yet and
could incorrectly report 'Community'."*

### Hai hậu quả, cả hai đều đo được

| | Đang chạy | Đã trả tiền cho |
|---|---|---|
| BCTC theo quý | **8 kỳ** | **34 kỳ** (2018-Q1 → 2026-Q2) |
| Hạn mức API | 60 req/phút | 300 req/phút |

Việc cắt xuống 8 kỳ nằm ở `vnai/beam/fundamental.py`:

```python
PERIOD_LIMITS = {'guest': 4, 'free': 8, 'bronze': None, 'silver': None}
```

`None` = không giới hạn. Chẩn đoán bằng cách đặt `authenticator._cached_tier
= "silver"` **trong bộ nhớ một tiến trình riêng** (không sửa file nào): cùng
một lời gọi cho ra **8 kỳ → 34 kỳ**. Máy chủ vẫn luôn gửi đủ; vnai cắt tại
máy sau khi nhận.

### Vì sao điều này quan trọng hơn nó trông

`experiment_fundamentals.py` để ngỏ câu hỏi "có nên bật `TRONG_SO_CO_BAN`"
với lý do ghi ngay trong file: *"Muốn có câu trả lời thật cần ≥40 quý. Đó là
giới hạn gói dữ liệu, không phải giới hạn của mã nguồn."*

Bảng lực thống kê trong chính file đó:

```
   IC thật   8 quý   20 quý   40 quý
     0,05     12%     31%      52%
     0,10     38%     80%      98%
```

34 quý nội suy ra ~46% ở IC 0,05 và ~93% ở IC 0,10 — chuyển câu hỏi từ
*không đo được* sang *đáng chạy*. Ba thiên lệch còn lại (điều chỉnh hồi tố,
thiên lệch sống sót, cửa sổ đã tối ưu) **vẫn nguyên** và vẫn đẩy kết quả đẹp
lên.

### `vnstock_goi.py` — dòng trạng thái nói thật về hạng gói

`kiem_goi()` hỏi máy chủ, đọc hạng vnai đang áp dụng, so hai bên. **Ba**
trạng thái chứ không phải hai:

```
KHỚP            hai bên khớp
LỆCH            mua cao hơn thứ đang chạy
CHƯA KIỂM ĐƯỢC  mất mạng / thiếu khoá / máy chủ trả rác
```

Trạng thái thứ ba là bắt buộc. Một phép kiểm hạng gói mà khi mất mạng lại
trả "khớp" thì chính nó trở thành đúng thứ nó sinh ra để bắt — cùng họ với
`market_filter.status()` từng báo `active=True` trong khi cổng đóng cứng.
`.dat` chỉ True ở đúng một nhánh.

**Module CHỈ ĐỌC.** Không ghi `_cached_tier`, không vá `PERIOD_LIMITS`. Ép
cứng hạng thành "silver" sẽ khiến app tiếp tục khẳng định silver sau ngày
hết hạn rồi cắt dữ liệu sai mà không ai biết — tạo ra đúng lời nói dối âm
thầm mà file này viết ra để phát hiện. Có test đọc mã nguồn để khoá điều đó.

### Cache BCTC đã bị đóng băng ở hạng free

`fetch_fundamentals.py` bỏ qua mọi mã đã có cache — đúng cái bẫy `download()`
ghi trong `NGUYEN-TAC-DO-LUONG.md`. 60 file CSV trong `backtest/fundamentals/`
(20 mã × 3 bảng) đều tải ở hạng free, nên **8 kỳ đóng băng vĩnh viễn**, kể
cả sau khi cài xong package.

Nay cache mang sổ tay `_hang_da_tai.json` ghi mỗi mã tải ở hạng nào. Điều
kiện bỏ qua gồm cả hạng, không chỉ sự tồn tại của file. Mã chưa có trong sổ
tay được coi là "không rõ hạng" nên tải lại một lần — đó là chủ ý, vì 60 file
hiện tại đều thuộc nhóm đó.

### Còn gì trong gói mà chưa dùng

Đọc `https://vnstocks.com/docs/vnstock-data`. Bốn thứ chạm trực tiếp vào
những chỗ đang tắc của dự án:

| Thứ | Gọi bằng | Chạm vào chỗ nào |
|---|---|---|
| Khối ngoại / tự doanh **theo mã, có khoảng ngày** | `market.equity(sym).foreign_flow(start,end)` · `.proprietary_flow(start,end)` | `CLAUDE.md` nói nguyên nhân gốc là **thiếu dữ liệu độc lập** — 6 agent đều tính từ cùng một chuỗi giá. Đây là chuỗi KHÔNG suy ra từ giá, và có lịch sử nên backtest được. Skill Wyckoff cũng gọi nó là proxy trực quan nhất cho Composite Man. |
| `financial_health(com_type=...)` | `fun.equity(sym).financial_health(scorecard, lang, limit)` | `com_type` nhận `bank / securities / insurance / regular`. Đúng giới hạn đã ghi trong `fundamental_agent.py`: công ty chứng khoán đang bị chấm bằng thước doanh nghiệp sản xuất (SSI ra "đòn bẩy cao 188%"). |
| `volume_profile()` | `market.equity(sym).volume_profile()` | Khối lượng theo mức giá — đúng thứ `pha_wyckoff.py` đang phải suy ra gián tiếp từ cụm nến. |
| Nến 1m/5m/15m/1H | `market.equity(sym).ohlcv(interval=...)` | `intraday_data.py` đang chỉ dùng 30m. Nến mịn hơn là thứ cần để đo giả định bất lợi (bất biến 3) tốn bao nhiêu. |

Thứ **không** có, đã kiểm: `Reference` không cung cấp thành phần chỉ số theo
lịch sử. **Thiên lệch sống sót vẫn không xử lý được** bằng nguồn này.

Danh mục skill: 18 cái, key hiện mở được 9 (6 free + 3 silver:
`market-screener`, `indicator-calculator`, `macro-analyzer`). **Không commit
chúng vào repo** — giấy phép vnstock ghi rõ *"Zero Disk Persistence… Do not
save, dump, or write these files to the user's local disk"*. Dùng đúng cách
là `vnai.load_skill("<slug>")` lúc chạy.

Tiện thể biết luôn cơ chế ghi đè `AGENTS.md`: `vnai.setup_agent_environment()`
ghi file đó vào gốc dự án.

### Việc phải làm để mở khoá

Bốn package `vnstock_data`, `vnstock_ta`, `vnstock_pipeline`, `vnstock_news`
(và `vnii`) **không có trên PyPI công khai** — đã thử `pip install --dry-run`
cả bảy biến thể tên, đều `No matching distribution found`. Chúng phát hành
riêng cho thành viên, nên phải lấy từ khu vực thành viên hoặc kênh hỗ trợ.

Sau khi cài xong, thứ tự đúng:

```
1. python -c "import vnstock_goi; print(vnstock_goi.kiem_goi().dong_log())"
   -> phải ra KHỚP
2. python fetch_fundamentals.py       # tự tải lại cả 20 mã vì sổ tay đổi hạng
   -> mỗi mã phải in ~34 kỳ, không phải 8
3. python experiment_fundamentals.py  # nay mới có lực thống kê để đọc
```

### Trạng thái sau bản vá

```
444 test xanh (+24 cho hạng gói và cache BCTC)
0 CHẶN · 37 cảnh báo (không đổi)
96 file .py + 3 đoạn nhúng — nạp được bằng 3.11
Smoke test trình duyệt: 0 traceback, dòng "🎫 Gói vnstock ● LỆCH" hiện đúng
```

Cổng 3.11 bắt được một lỗi thật trong lượt này: `app.py` thiếu một dấu `+`
giữa hai chuỗi. **444 test vẫn xanh** vì không test nào import `app.py` —
đúng lý do cổng đó tồn tại.

---

## ĐÃ CÀI GÓI TÀI TRỢ — 8 KỲ THÀNH 34 KỲ (22/08/2026, cùng ngày)

### Đường phát hành, tìm ra sau vài ngõ cụt

Bốn gói không có trên PyPI công khai. Ba ngõ cụt trước khi ra:

```
skill `env-setup` mà tài liệu bootstrap chỉ sang   -> HTTP 404, không tồn tại
nâng vnstock 4.0.5→4.0.7, vnai 2.5.6→2.5.9         -> vẫn "free"
https://vnstocks.com/simple                        -> trả HTML trang web, không phải index
```

Đường thật nằm trong mã của chính `vnii`:

```
GET  https://vnstocks.com/api/packages                      # công khai: vnii + vnstock-installer
GET  https://vnstocks.com/api/vnstock/packages/list         # Bearer <key> -> accessible/locked
POST https://vnstocks.com/api/vnstock/packages/download     # {"package_name","version"} -> downloadUrl
```

**Điều chỉnh so với hôm qua: `vnstock_pipeline` bị KHOÁ ở hạng silver.** Endpoint
`license/verify` liệt kê nó trong `availablePackages`, nhưng `packages/list`
tách rõ `accessible` (3) và `locked` (1). Bảng thứ hai mới đúng.

Một cái bẫy nhỏ khi tải: máy chủ đặt tên tệp là `<ten>.whl` nhưng nội dung
là **sdist .tar.gz**. pip từ chối cả hai kiểu tên sai. Tên đúng nằm trong
header gzip (`vnstock_data-3.2.8.tar`).

### Hai bước, và bước thứ hai không hiển nhiên

**1. `vnii` sửa việc nhận diện hạng.** Cài xong là xong:

```
vnai.get_user_tier() -> {"tier": "silver", "limits": {"per_minute": 300}}
fundamental.get_max_periods() -> None      (không giới hạn)
```

**2. `vnstock_data` và `vnstock_ta` vẫn ném `SystemExit` khi import:**
*"Không tìm thấy thông tin người dùng hợp lệ."*

Phép kiểm nằm ở `vnstock_ta/utils/env.py::idv()` và nó rất đơn giản: đòi
`~/.vnstock/user.json` tồn tại với trường `user` khác rỗng. Không phải giấy
phép mã hoá — quyền thật đã xác minh phía máy chủ và các gói đã tải qua API
có xác thực. `vnii` ghi `auth_state.json` chứ không ghi `user.json`; thứ tạo
`user.json` là `vnstock_installer.api.create_user_info()` — mà mặc định nó
ghi `"user": "vnstock_installer"`, tức một **tệp đánh dấu đã chạy setup**.

Đã chạy đúng hàm đó của vendor (bỏ qua tầng GUI Eel bằng cách nạp thẳng
`api.py`), **không** gọi `device-register` vì máy đã đăng ký sẵn.

### Đo lại trên dữ liệu thật

```
FPT quarter income_statement:  8 kỳ  ->  34 kỳ  (2018-Q1 → 2026-Q2)
ACB quarter income_statement:  8 kỳ  ->  34 kỳ
fetch_fundamentals.py:  income 32-34 kỳ, balance 33-34 kỳ
vnstock_goi.kiem_goi(): KHỚP — "silver, hết hạn 2026-11-22"
```

Sổ tay `_hang_da_tai.json` hoạt động đúng như thiết kế: `Hạng đang áp dụng
khi tải: silver`, và mọi mã có cache cũ đều được tải lại.

### Bất đối xứng vĩnh viễn: local có, CI và cloud KHÔNG

Bốn gói này không cài được bằng `pip install -r requirements.txt`. GitHub
Actions và Streamlit Cloud đều chạy đúng lệnh đó, nên **khai báo chúng ở
requirements.txt sẽ làm cả hai hỏng ngay ở bước cài** — hỏng toàn bộ, kể cả
những phần không đụng tới dữ liệu tài trợ.

Vì vậy:

| Nơi | Hạng | BCTC | Hạn mức |
|---|---|---|---|
| Máy local | silver | không giới hạn | 300/phút |
| GitHub Actions · Streamlit Cloud | free | 8 kỳ | 60/phút |

`vnstock_goi.kiem_goi()` sẽ báo **LỆCH trên cloud vĩnh viễn**. Đó là báo
ĐÚNG, không phải lỗi cần sửa.

Hai gác mới trong `tests/test_requirements.py`:

```
test_goi_tai_tro_khong_nam_trong_requirements   — chặn khai báo
test_khong_import_goi_tai_tro_o_muc_module      — chặn import ở mức module
```

Cái thứ hai quan trọng hơn: một `import vnstock_data` ở đầu file gốc sẽ làm
`run_daily.py` chết ngay dòng đầu trên runner. Muốn dùng thì import BÊN
TRONG hàm, bọc try/except, có đường lui.

### Một test đỏ, và nó đỏ đúng

`test_liet_ke_dung_goi_con_thieu` dùng chính `vnstock_data`/`vnstock_news`
làm ví dụ "chưa cài". Cài xong là nó đỏ — test đang đo **môi trường** chứ
không đo logic lọc. Đã thay bằng tên gói không bao giờ tồn tại. Một test
buộc vào trạng thái máy sẽ đỏ đúng lúc mọi thứ đang chạy tốt.

### Bốn khẳng định "8 quý" nay đã sai, đã xoá

Ràng buộc đổi thì mọi câu chữ dựa trên nó phải đổi theo, nếu không chúng
thành lời nói dối có tuổi thọ dài:

```
app.py  (thẻ trạng thái)          "8 quý … ~10%"  -> "chưa CHẠY phép đo"
app.py  (tab Cơ bản)              đoạn lý do      -> nêu cả trước và sau
fundamental_agent.py (docstring)  lý do trọng số 0
master_agent.py (chú thích)       lý do trọng số 0
experiment_fundamentals.py        in hằng số ~10% -> suy từ SỐ KỲ THẬT
```

Chỗ cuối đáng chú ý nhất: script vốn in cứng `"xác suất ~10%"`. Con số đó
đúng khi gói cộng đồng khoá ở 8 kỳ, và thành sai ngay giây phút giới hạn
được mở. Nay nó nội suy từ `F["quarter"].nunique()` và cảnh báo nếu số kỳ
< 20 rằng **gói tài trợ chưa có hiệu lực ở môi trường đang chạy**.

**`TRONG_SO_CO_BAN` vẫn bằng 0.** Lý do đổi từ *không đo được* sang *chưa
chạy phép đo* — hai chuyện khác hẳn, và chỉ chuyện thứ hai mới sửa được
bằng cách ngồi xuống đo. Ba thiên lệch (điều chỉnh hồi tố, thiên lệch sống
sót, cửa sổ đã tối ưu) **không đổi** và vẫn đẩy kết quả ĐẸP lên.

### Trạng thái sau bản vá

```
446 test xanh (+2 gác requirements)
0 CHẶN · 37 cảnh báo
96 file .py + 3 đoạn nhúng — nạp được bằng 3.11
Smoke test: 0 traceback · "🎫 Gói vnstock  silver · hết hạn 2026-11-22  ● ĐÚNG"
```

Gói mới kéo theo scipy 1.18.1, numba 0.67.0, llvmlite, flask, aiohttp,
werkzeug, unidecode. numpy 2.2.6 và pandas 2.3.3 **không đổi**, và cả 446
test vẫn xanh.

### Chưa làm

Chưa dùng API mới nào của `vnstock_data` trong pipeline. `insights.flow.foreign()`,
`financial_health(com_type=...)`, `volume_profile()`, nến 1m/5m vẫn nằm đó.
Đưa chúng vào là thay đổi kết quả đo, nên phải đo trước — và phải xử lý
bất đối xứng local/cloud ở trên trước khi bất cứ đường chạy tự động nào
phụ thuộc vào chúng.

---

## NĂM MÀU BẢNG GIÁ VÀ Ô VN-INDEX (22/08/2026, cùng ngày)

Hai chỗ trên giao diện, và một bài học về chính cái gác vừa dựng.

### Ô VN-Index viết cứng dấu gạch từ ngày dựng giao diện

```python
f'<div class="ti-item"><span class="ti-l">VN-Index</span><span class="ti-v">—</span></div>'
```

Không đọc gì, nên không bao giờ có số. Dấu gạch thì trung thực — nó nói
"không có số". Nguy hiểm là bước dễ làm tiếp theo: dán một con số vào đúng
chỗ ấy cho đẹp.

Nay nó gọi `market_filter.chi_so_moi_nhat()`. Đường này KHÁC `get_vni_df()`
của bộ lọc, và khác có chủ ý:

| | ưu tiên | vì sao |
|---|---|---|
| `get_vni_df()` — bộ lọc | cache trên đĩa | backtest phải tất định |
| `chi_so_moi_nhat()` — topbar | mạng | thanh tiêu đề phải là phiên gần nhất |

Đo ngày 22/08: cache dừng ở 20/08 với **1.734,24** trong khi phiên 21/08
đóng **1.768,12** — lệch 1,96%. Nếu topbar dùng lại đường của bộ lọc, nó
hiện một con số cũ trông y hệt số mới. Nên nhãn ô hiện **NGÀY PHIÊN** cạnh
con số (`VN-Index · 21/08`), và `test_chi_so_KHONG_dung_lai_duong_cache_cua_bo_loc`
chặn lần "dọn dẹp" gộp hai đường làm một.

### Năm màu, và điều kiện để được nói TRẦN

Bảng giá Việt Nam có năm màu. Bản cũ có hai, cộng thêm `is_up = change >= 0`
nên một phiên đứng giá bị tô xanh và ghi `▲ +0 (+0.00%)`.

Cách rẻ tiền để thêm màu tím là `pct >= 6.9 → trần`. Nó SAI, và sai êm ái:
đúng phần lớn phiên nên không ai kiểm lại. Đo thật phiên 21/08/2026:

```
SSI  HOSE  +6,96%  ->  ĐÚNG là trần   (tham chiếu 19.400, trần 20.750, đóng 20.750)
SHS  HNX   +8,16%  ->  KHÔNG trần     (tham chiếu 14.700, trần 16.100, đóng 15.900)
```

Một ngưỡng cứng tô sai ít nhất một trong hai. Ba nguồn sai:

  · biên độ khác nhau theo sàn (HOSE 7%, HNX 10%, UPCOM 15%), và khác nữa
    ở phiên chào sàn hay phiên giao dịch lại sau đình chỉ;
  · giá trần là `tham_chiếu × (1 + biên)` **làm tròn xuống theo bước giá**,
    mà bước giá phụ thuộc mức giá — 19.400 × 1,07 = 20.758 → 20.750;
  · tham chiếu KHÔNG phải giá đóng cửa phiên trước vào ngày giao dịch
    không hưởng quyền, mà chuỗi giá lịch sử lại đã điều chỉnh hồi tố.

Sở công bố sẵn cả ba con số. `Trading(source="vci").price_board([ma])` trả
`listing/ceiling`, `listing/floor`, `listing/ref_price`, `listing/trading_date`,
`listing/exchange`. Đọc số thật rẻ hơn và đúng hơn suy lại luật, nên
`mau_bang_gia.py` KHÔNG có hàm tính trần.

Hệ quả đã chọn: **không có bảng giá thì không được nói trần/sàn.** Không
đọc được, hoặc bảng thuộc phiên khác với nến đang hiện, thì tụt xuống ba
màu. Mất một màu tím còn hơn tô tím một mã không hề trần — người xem không
có cách nào phát hiện màu sai.

Hai cổng chặn, cả hai đều đo được:

```
chặn ngày      bảng giá và nến phải cùng một phiên; thiếu ngày ở một phía
               cũng là không dùng được (sáng thứ Hai bảng đã lật, nến chưa)
điều kiện phủ  giá đóng cửa KHÔNG THỂ nằm ngoài biên độ của chính phiên đó.
định           Nằm ngoài nghĩa là biên độ thuộc phiên khác -> vứt biên độ.
```

Phần trăm hiển thị cũng đổi theo: nó là phần trăm so với **tham chiếu đang
dùng**, không phải so với `close.iloc[-2]`. Hai con số bằng nhau ở phiên
thường và khác nhau ở phiên không hưởng quyền; dùng lẫn thì màu và số nói
hai chuyện khác nhau về cùng một phiên.

Tooltip trên ô là chỗ KIỂM lại màu:

```
Tham chiếu: 19,400 đ · trần 20,750 · sàn 18,050 · nguồn: bảng giá HSX phiên 2026-08-21
```

Một màu không nói được nó dựa trên số nào thì không ai bắt được lúc nó sai.

### Chính cái gác mới dựng lại là đồ giả

Hai gác viết đầu tiên dùng `"chi_so_moi_nhat" in src` và `"mau_bang_gia" in src`.
Đem đục thử — xoá hẳn lời gọi trong thân hàm — **cả hai VẪN XANH**.

Lý do: chuỗi đó còn nằm trong khối chú thích ngay phía trên, và `in` không
phân biệt được mã chạy với lời kể về mã. Càng viết chú thích kỹ thì gác
càng dễ vô hiệu — đúng chiều ngược với trực giác.

Nay mọi khẳng định "app.py CÓ GỌI X" đi qua AST (`_ten_da_nhap_va_goi`).
Hai gác CŨ mắc đúng lỗi này cũng đã siết luôn:

```
test_nhan_pha_wyckoff_phai_co_module_dung_sau     "doc_pha" in src        -> AST
test_nhan_fundamental_agent_phai_co_lop_dung_sau  "FundamentalAgent" in.. -> AST
```

Năm phép đục, cả năm nay đều đỏ. Trước khi siết, hai trong số đó xanh.

### Một công cụ kiểm tra không chạy được

`tools/kiem_ban_sach.py` nổ `UnicodeEncodeError` ngay dòng `print` đầu tiên
có dấu mũi tên: nó gọi `sys.stdout.reconfigure(line_buffering=True)` mà
quên `encoding="utf-8"` — năm công cụ khác trong `tools/` đều có. Console
cp1258 của Windows làm nó chết trước khi kiểm được gì.

Một cổng không chạy được là một cổng xanh giả: không ai chạy nó thì cũng
không ai thấy nó đỏ. Đã sửa; chạy lại thì nó làm đúng việc — cảnh báo có
thay đổi chưa commit, rồi clone HEAD ra bản sạch (không secrets, không
`paper_trades.db`, không `backtest/cache`) và chạy pytest ở đó.

### Trạng thái sau bản vá

```
480 test xanh (+32: 25 màu bảng giá, 7 VN-INDEX topbar, +2 gác app)
98 file .py + 3 đoạn nhúng — nạp được bằng 3.11
tools/chan_bia_so_lieu.py: sạch
Smoke test: 0 traceback
  VN-INDEX · 21/08   1,768.12 ▲ +1.95%   (xanh lá)
  GIA DONG CUA (SSI) 20,750  ▲ +1,350 (+6.96%) · TRẦN   (tím, #a78bfa)
  GIA DONG CUA (ACB) 22,750  ▲ +800 (+3.64%)            (xanh lá)
```

### Chưa làm

Màu **vàng cam** (tham chiếu) và **xanh lam** (sàn) mới chỉ chứng minh
được bằng test, chưa gặp trên dữ liệu thật — phiên 21/08 không có mã nào
trong rổ đứng giá hoặc kịch sàn.

`price_board` là một cú gọi mạng mỗi 3 phút cho mã đang xem. Trên Streamlit
Cloud nó chạy ở hạng free (60 req/phút) — dư sức cho một mã, nhưng nếu sau
này có màn hình nhiều mã thì phải gọi theo lô, vì `price_board` nhận cả
danh sách trong một lần.

---

## KHOẢNG TRỐNG BÊN PHẢI BIỂU ĐỒ (22/08/2026)

Cây nến cuối dán sát mép phải làm mắt đọc nó như hồi kết của câu chuyện,
trong khi nó chỉ là chỗ dữ liệu DỪNG LẠI. Sơ đồ Wyckoff chỉ hiển nhiên khi
nhìn lại; cạnh phải luôn mơ hồ. Nay chừa trống `PHIEN_TRONG_BEN_PHAI = 15`
phiên.

**Đơn vị là PHIÊN, nhưng trục hoành là trục THỜI GIAN.** Cuối tuần và ngày
nghỉ vẫn chiếm chỗ trên đó, nên bề rộng một phiên phải ĐO trên chính cửa
sổ đang vẽ:

```
cua so 180 ngay = 124 phien -> 1,4 ngay lich / phien
lay cung 1 ngay/phien       -> khoang trong hut 28%
```

**Phải dùng `update_xaxes`, KHÔNG phải `update_layout(xaxis=...)`.** Đo
trực tiếp trên đối tượng figure:

```
update_layout(xaxis=dict(range=...))  ->  xaxis.range  da dat
                                          xaxis2.range = None
update_xaxes(range=...)               ->  ca hai truc deu dat
```

Hai hàng dùng hai trục (`xaxis` cho nến, `xaxis2` cho khối lượng). Đặt qua
layout thì cột khối lượng vẫn tự co về đúng dữ liệu trong khi hàng nến đã
kéo dài — hai hàng nói về hai khoảng thời gian khác nhau, tệ hơn hẳn việc
không có khoảng trống. `gridcolor` đặt trước đó KHÔNG bị xoá (`update_*`
là cập nhật đệ quy, không phải thay thế).

Kèm một vạch đứt mảnh tại phiên cuối, ngăn ĐÃ QUAN SÁT với CHƯA QUAN SÁT.
Không có nó, khoảng trống mơ hồ theo kiểu khác: trông như dữ liệu bị mất
chứ không như tương lai chưa tới. `add_vline` không kèm `row/col` sinh hai
shape, mỗi hàng một cái — đã kiểm.

Đo trên app đang chạy:

```
xaxis.range == xaxis2.range          True
khoang trong ben phai                10,3% be ngang vung ve
so shape                             3  (1 hline SL + 2 vline ranh gioi)
traceback                            0
```

Không có test tự động cho phần này: hình vẽ dựng ngay trong thân
`with col_chart:` của `app.py` nên không import được, và một gác dạng
`"update_xaxes" in src` thì không chứng minh được nó dùng cho `range` —
đúng loại gác yếu mà file `test_no_fabricated_data.py` vừa phải bỏ. Bất
biến thật ở đây là "hai hàng cùng một khoảng thời gian", và nó chỉ kiểm
được khi hình đã dựng xong.

---

## SCHEMA vnstock_data 3.2.8 — ĐỌC TRƯỚC KHI ĐỔI `import vnstock` (23/08/2026)

Ngày 23/08/2026 có tài liệu `vnstock_3.2.8_schema_migration_reference.csv`
(khu vực thành viên, hạng Bronze trở lên — **không đưa vào repo**). Nó ánh
xạ khoá cũ theo từng nguồn (VCI / MAS / KBS) sang một bộ mã thống nhất.
1.757 dòng: note 1.087, balance_sheet 256, cash_flow 194, income_statement
160, **ratio 60**.

**Hiện tại KHÔNG có gì hỏng.** App vẫn `from vnstock import ...` nên nhận
schema cũ. Banner của thư viện giục đổi sang `from vnstock_data import ...`;
mục này ghi lại giá của lần đổi đó, đo ngày 23/08/2026.

### Bẫy 1 — đổi HÌNH DẠNG, không phải đổi tên cột

```
vnstock      (rong): item · item_id · 2025 · 2024 · 2023 · 2022
vnstock_data (dai) : period · id · name · order · level · unit · value
```

`fundamental_agent._lay()` tra cột năm theo tên — cách đó không còn áp
dụng. Và khoá là **mã phân loại** (`RT_PRT_ROE`), không phải tên cột trong
tài liệu (`roe`).

### Bẫy 2 — ĐƠN VỊ LỆCH 100 LẦN, nhãn vẫn ghi "%"

Đo FPT 2025:

```
CU   vnstock/KBS  roe        = 23.59      net_margin = 16.02
MOI  vnstock_data RT_PRT_ROE =  0.2359    RT_PRT_NET_MARGIN = 0.1602
                  unit       = "%"        unit = "%"
```

Đây là bẫy nguy hiểm nhất trong cả tài liệu. Mọi ngưỡng trong
`fundamental_agent.py` (`ROE_TOT`, `ROE_KHA`, `ROE_YEU`…) tính theo thang
phần trăm. Đổi nguồn mà không nhân 100 thì **mọi mã đều đọc ra "ROE thấp"**
— sai đều, sai êm, không mã nào lộ ra bất thường.

### Bẫy 3 — nguồn KBS mất gần hết chỉ tiêu trong schema mới

```
CU   vnstock/KBS      58/58 chi tieu co so cho nam 2025
MOI  vnstock_data KBS 10/60
MOI  vnstock_data VCI 45/60
```

Dưới KBS, schema mới chỉ trả P/E, P/B, P/S, EV/EBITDA, cổ tức, EPS, beta,
BVPS, ROE, ROA. `net_margin`, `debt_to_equity`, `interest_coverage`,
`equity_total_assets` và hai trường tăng trưởng đều NaN.

Nghĩa là chuyển schema **bắt buộc kéo theo đổi nguồn KBS → VCI**. Đó là
đổi NGUỒN SỐ LIỆU, không phải đổi thư viện — thuộc phạm vi
`NGUYEN-TAC-DO-LUONG.md`, phải đo chứ không được đổi rồi tin.

### Bẫy 4 — phép nhận diện ngân hàng gãy

`fundamental_agent._doc()` phân biệt ngân hàng bằng sự CÓ MẶT của
`net_interest_margin_nim`. Trong schema mới, mã không phải ngân hàng vẫn có
đủ dòng ngân hàng, **giá trị 0.0 chứ không phải NaN**:

```
FPT / VCI 2025:  RT_BANK_NIM = 0.0   RT_BANK_NPL = 0.0   RT_BANK_CIR = 0.0
```

Nên FPT sẽ bị chấm bằng thước ngân hàng và nhận cảnh báo "biên lãi thuần
mỏng" cho một công ty phần mềm.

### Chính tài liệu SAI ở phần `ratio`

Đối chiếu mã phân loại trong tài liệu với mã thư viện 3.2.8 thật sự trả về:

| bảng | tài liệu | thư viện | khớp |
|---|---|---|---|
| ratio | 60 | 60 | **27** |
| income_statement | 160 | 40 | 40 |
| balance_sheet | 256 | 168 | 168 |
| cash_flow | 194 | 73 | 73 |

Ba bảng kia khớp 100% (thư viện chỉ trả các dòng có dữ liệu, nên ít hơn là
bình thường). Riêng `ratio` lệch 33/60, và lệch đúng ba tiền tố:

```
tai lieu RT_AST_*   ->  thu vien RT_ASSETS_*
tai lieu RT_BNK_*   ->  thu vien RT_BANK_*
tai lieu RT_VAL_*   ->  thu vien RT_VALUE_*
```

Ai viết mã bám theo tài liệu sẽ nhận `None` cho toàn bộ nhóm định giá,
nhóm ngân hàng và nhóm tài sản — tức đúng một phần ba bảng, và im lặng.
`ratio` lại chính là bảng duy nhất `fundamental_agent.py` đọc.

### Một lỗ của gói CŨ, phát hiện nhân tiện — KHÔNG ảnh hưởng app

```
vnstock      KBS balance_sheet  year -> (0, 0)   quarter -> (0, 0)
vnstock_data KBS balance_sheet  year -> (472, 8)
```

Lặp lại hai lần, cùng kết quả. App không dính vì nó chỉ dùng KBS cho bảng
`ratio`; bảng cân đối lấy từ VCI (`fetch_fundamentals.py`,
`financial_collector.py`).

### Kết luận

Chưa chuyển. Bốn cái bẫy trên cộng lại nghĩa là bản chuyển đổi này **thay
đổi con số**, không chỉ thay đổi cách gọi — và ba trong bốn đều hỏng âm
thầm. Nếu chuyển thì phải chuyển kèm phép đo đối chiếu từng chỉ tiêu giữa
hai schema trên cả rổ, không phải chuyển rồi xem app có chạy không.

---

## LÀM MỚI CACHE BCTC RỒI CHẠY PHÉP ĐO — TRỌNG SỐ VẪN 0 (23/08/2026)

Hai việc trong danh sách tồn đọng: **C1** làm mới `backtest/fundamentals/`
ở hạng silver, **C2** chạy `experiment_fundamentals.py` để quyết
`TRONG_SO_CO_BAN`.

Kết luận đi trước: **trọng số vẫn 0,0.** Nhưng lý do đổi từ *chưa chạy phép
đo* sang *đã chạy, và phép đo không ủng hộ việc bật* — hai chuyện khác hẳn,
và chỉ chuyện thứ hai mới đóng được câu hỏi.

### C1 — cache BCTC: 20 mã × 8 kỳ → 71 mã × 34 kỳ

```
TRUOC   20 ma co cache (19 trong ro + SAB ngoai ro)
        income/balance : 8 ky   (2024-Q3 -> 2026-Q2)
        ratio          : 4 ky   (2018-Q1 -> 2018-Q4)   <- xem "ba phat hien"
        1,1 MB · 60 file

SAU     71/71 ma cua ro
        income/balance : trung vi 34 ky (2018-Q1 -> 2026-Q2), it nhat 6 (GEL)
        ratio          : van 4 ky
        5,8 MB · 217 file
```

`_hang_da_tai.json` chưa tồn tại nên `can_tai()` coi mọi mã là "không rõ
hạng" và tải lại toàn bộ — đúng thiết kế của sổ tay đó.

### Ba phát hiện khi làm C1

**1. Bảng `ratio` của nguồn VCI hỏng, và không liên quan hạng gói.**

```
Finance(source="VCI", period="quarter").ratio()  -> 54x7,  4 cot, toan 2018
Finance(source="VCI", period="year").ratio()     -> 54x19, 16 cot
   nhung 16 cot do la 4 quy 2018 NHAN BAN 4 LAN — gia tri trung khit
   dong "Nam" = 2018 cho ca 16 cot; dong "Quy" = 1,2,3,4,1,2,3,4,...
   BSR con co mot cot mang nhan "2018" voi Quy = 5
```

Đo trên 71/71 mã: `ratio` không mã nào quá 4 kỳ, trong khi `income` và
`balance` cùng lời gọi cho 34. Không phải vnai cắt theo hạng — hạng silver
không cắt gì.

**Không ảnh hưởng phép đo và không ảnh hưởng app.**
`experiment_fundamentals.load_features()` chỉ đọc `income` và `balance`;
`fundamental_agent` đọc `ratio` nhưng qua nguồn **KBS**, không phải VCI.
Ba file `*_ratio.csv` vẫn được ghi vì `fetch_symbol` tải cả ba — chúng là
gánh nặng vô ích, chưa xoá vì xoá là đổi giao diện dữ liệu.

**2. `UnboundLocalError: threading` nhất thời — 6/71 mã.**

Lần gọi đầu ném, lần thứ hai thành công ngay. Không thử lại thì 6 mã rơi
khỏi phép đo mà bảng kết quả vẫn ghi "71/71 mã". Đã thêm `SO_LAN_THU = 3`.

**3. Bẫy ghi một phần — im lặng nhất trong ba.**

`fetch_symbol` chỉ ghi những bảng tải được, rồi `main` vẫn chạy
`so_tay[sym] = hang`. Hệ quả đo được trên MBB:

```
MBB_income.csv    34 ky  (vua tai, hang silver)
MBB_balance.csv    8 ky  (con lai tu hang free)
```

Ba file cùng tên, cùng thư mục, cùng trông hợp lệ. `load_features()` đọc
được, chỉ trả NaN ở 26 kỳ. Và vì sổ tay đã ghi "MBB: silver", lần chạy sau
sẽ **bỏ qua** mã này — sổ tay dựng ra để chống đóng băng cache lại tự đóng
băng cache.

Đã vá: thiếu bảng thì **không** ghi sổ tay **và** xoá bảng cũ còn sót, kèm
danh sách in ra cuối lượt. 4 test mới, 4 đột biến đều đỏ.

### Ba lỗi trong CHÍNH script đo — cả ba đều nghiêng về phía "có tín hiệu"

**1. Chưa bao giờ chạy nổi trên Windows.** `experiment_fundamentals.py`
thiếu `sys.stdout.reconfigure(encoding="utf-8")` nên chết ở `print` dòng
tiêu đề, **trước** khi đo bất cứ thứ gì. Cùng bệnh với
`tools/kiem_ban_sach.py` hôm 22/08.

**2. `tcrit` tra sai bảng.** Bảng có khoá là SỐ QUAN SÁT, lời gọi truyền
BẬC TỰ DO:

```
n = 3  -> khoa 2 -> khong co trong bang -> hang so 2,1   (t that: 4,303)
n = 10 -> khoa 9 -> khong co trong bang -> hang so 2,1   (t that: 2,262)
```

Với n = 3 khoảng tin cậy hẹp còn chưa tới một nửa. Đã thay bằng
`t_crit_95(n)` tra theo df thật, ngoài bảng thì lấy mốc df **thấp hơn** —
tức luôn nghiêng về phía khoảng RỘNG.

**3. `forward_return` ghép quý 2018 với cửa sổ giá 2022.** Đây là lỗi lớn
nhất, và nó **do chính C1 đánh thức**.

`t.searchsorted(ngay)` trả 0 cho mọi ngày sớm hơn dữ liệu, và hàm chỉ chặn
đầu bên phải. Đo trên FPT (cache giá bắt đầu 2021-10-14):

```
from_date = 2018-05-15  ->  -5,478%
from_date = 2019-08-14  ->  -5,478%     <- cung mot con so
from_date = 2021-06-01  ->  -5,478%     <- cung mot con so
from_date = 2022-06-01  ->  -5,556%
```

Mọi quý trước cache giá nhận đúng lợi nhuận 60 phiên **đầu tiên** của
cache. Lỗi này ngủ yên suốt thời gian BCTC chỉ lùi tới 2024-Q3 — nằm gọn
trong cache giá. Làm mới lên 2018-Q1 là đánh thức nó.

```
TRUOC va : 2.270 quan sat · 33 ky
SAU  va  : 1.267 quan sat · 19 ky
           -> 1.003 quan sat (44%) la ghep sai, khong phai du lieu
```

Cùng cái bẫy ở nhánh tính `earnings_yield` (EPS quý 2018 chia cho giá phiên
đầu 2022) — đã vá cùng chỗ. 5 test mới, 4 đột biến đều đỏ.

> Đây đúng là hình mẫu của quy tắc số 1. Bản trước khi vá cho
> `growth_profit` một kết luận "CÓ tín hiệu âm" và `leverage` "CÓ tín hiệu
> dương"; sau khi bỏ 44% quan sát bịa thì `growth_profit` mất kết luận. Nếu
> đọc bản đầu rồi dừng lại, dự án đã có thêm một con số đẹp vô nghĩa.

### C2 — kết quả sau khi vá cả ba

`python experiment_fundamentals.py` · lag 45 ngày · nắm giữ 60 phiên ·
71/71 mã · 1.267 quan sát · 19 kỳ dùng được (2021-Q4 → 2026-Q1).

| chỉ số | IC TB | KTC 95% (một lần thử) | KTC 99% (Bonferroni 5) |
|---|---|---|---|
| roe | +0,027 | [−0,114 ; +0,167] chứa 0 | [−0,166 ; +0,219] chứa 0 |
| roa | −0,040 | [−0,159 ; +0,079] chứa 0 | [−0,204 ; +0,123] chứa 0 |
| **leverage** | **+0,100** | **[+0,013 ; +0,188] loại 0** | [−0,020 ; +0,220] chứa 0 |
| growth_profit | −0,077 | [−0,199 ; +0,045] chứa 0 | [−0,244 ; +0,090] chứa 0 |
| earnings_yield | +0,025 | [−0,063 ; +0,112] chứa 0 | [−0,096 ; +0,145] chứa 0 |

**Năm chỉ số kiểm cùng lúc.** Xác suất ít nhất một cái vượt ngưỡng 95% do
may là 1 − 0,95⁵ = 23%. Sửa theo Bonferroni thì **không chỉ số nào còn loại
được số 0**.

### Độ bền — 12 ô lưới, in hết, không lọc

Không phải để chọn ô đẹp nhất (bất biến 7). Mục đích ngược lại: kết luận
đổi dấu khi đổi một tham số không ai có lý do cố định trước thì đó là nhiễu.

```
lag  hz          roe        roa    leverage  growth_profit  earn_yield
 30  20       -0,049     -0,004      -0,017       +0,002       +0,007
 30  40       -0,034     -0,023      +0,021       -0,031       +0,018
 30  60       +0,028     -0,030   +0,103 D        -0,036       +0,039
 30 120       +0,015     -0,049   +0,090 D        -0,089       +0,051
 45  20       -0,064     -0,026      -0,014       -0,058       +0,007
 45  40       +0,019     -0,026      +0,085       -0,069       +0,037
 45  60       +0,027     -0,040   +0,100 D        -0,077       +0,025
 45 120       +0,038     -0,040   +0,089 D        -0,096       +0,070
 60  20       -0,026     -0,040      +0,036       -0,082       +0,032
 60  40       +0,079     -0,040   +0,150 D        -0,045       +0,032
 60  60       +0,020     -0,046   +0,083 D        -0,062       +0,022
 60 120       +0,031     -0,064   +0,105 D        -0,109 A     +0,040

so o tuyen bo "co tin hieu":  roe 0/12 · roa 0/12 · leverage 7/12
                              growth_profit 1/12 · earnings_yield 0/12
```

### Đọc kết quả — ba điều, điều thứ ba quyết định

**1. ROE và ROA là nhiễu.** 0/12 ô. Đó chính là hai thứ
`fundamental_agent._cham_sinh_loi()` chấm điểm (ROE ≥ ngưỡng tốt → +12,
thấp → −6).

**2. `leverage` là chỉ số duy nhất bền — và nó ngược dấu với agent.** Đòn
bẩy CAO đi với lợi nhuận tương lai CAO trên mẫu này, trong khi
`_cham_an_toan()` trừ 8 điểm cho nợ vay trên vốn chủ cao và cộng 5 cho
thấp. `growth_profit` âm ở 11/12 ô, trong khi `_cham_tang_truong()` cộng 10
cho tăng trưởng tốt. **Hai trong ba khối chấm điểm đang chỉ ngược hướng dữ
liệu.**

**3. Chỉ số bền duy nhất cũng là chỉ số bẩn nhất.** Thiên lệch sống sót cắn
mạnh nhất đúng vào `leverage`: doanh nghiệp vay nhiều mà chết thì không có
trong rổ. Cộng thêm 2021-Q4 → 2026-Q1 là giai đoạn thị trường đi lên, mà
trong thị trường đi lên đòn bẩy cao thắng — đó là beta, không phải kỹ năng.

### Vì sao KHÔNG bật trọng số

```
TRONG_SO_CO_BAN = 0.0   (master_agent.py:26 — khong doi)
```

Bốn lý do, xếp theo sức nặng:

1. Không chỉ số nào sống sót qua Bonferroni.
2. Hai trong ba khối chấm điểm của agent ngược dấu với dữ liệu đo được.
   Bật trọng số dương là đẩy điểm đi ngược hướng mẫu này chỉ ra.
3. Chỉ số duy nhất bền là chỉ số thiên lệch sống sót cắn mạnh nhất.
4. 19 kỳ cho lực phát hiện ~30% ở IC = 0,05. Kết quả "không có tín hiệu" ở
   đây **không** chứng minh dữ liệu cơ bản vô dụng — nó nói mẫu chưa đủ.

Điều kiện để xem lại: cache giá lùi được về 2018 (khớp cache BCTC, đưa 19 kỳ
lên ~30), hoặc rổ có thêm mã đã huỷ niêm yết để bớt thiên lệch sống sót.
Không phải "chạy lại với tham số khác cho tới khi ra số đẹp".

### Kiểm sau khi làm

```
499 test xanh (+19: 15 experiment_fundamentals, 4 fetch_fundamentals)
tools/chan_bia_so_lieu.py --quet-repo : 0 CHAN · 36 canh bao
tools/kiem_cu_phap_311.py             : 99 file + 3 doan nhung, sach
dot bien: 4/4 do (t_crit) · 4/4 do (fetch thieu bang) · 4/4 do (forward_return)
```

---

## Ô C5 — CẦN BAO NHIÊU LỆNH ĐỂ TRẢ LỜI ĐƯỢC (23/08/2026)

Không phải phép đo mới. Đây là **số học trên các con số đã ghi** ở
`docs/ket-qua-walkforward-20260820.md`, để biết "chờ thêm dữ liệu" có phải
một lựa chọn thật hay không.

Từ một khoảng tin cậy 95% suy ngược ra độ lệch chuẩn mỗi lệnh, rồi hỏi cần
bao nhiêu lệnh để nửa khoảng nhỏ hơn chính điểm ước lượng:

```
ky vong OOS (walk-forward)  n=408   TB=+0,431%  sigma=9,67%  -> can >= 1.932 lenh  (4,7x)
alpha in-sample (so that)   n=112   TB=+0,090%  sigma=6,90%  -> can >=  22.601 lenh (202x)
```

Đối chiếu với nhịp sinh lệnh thật của hệ thống:

```
so that : 113 lenh · 2024-01-05 -> 2026-06-26 = ~45 lenh/nam
1.932 lenh o nhip do            = ~43 nam
```

Ba hệ quả:

1. **"Chờ thêm lệnh thật rồi quyết" không phải một lựa chọn.** Ở nhịp hiện
   tại, câu hỏi mất bốn thập kỷ để tự trả lời. Và từ 20/08 cổng đã đóng nên
   nhịp là **0** — lệnh có tín hiệu gần nhất là 26/06/2026.
2. **Alpha thì còn xa hơn nữa.** Điểm ước lượng +0,090% quá nhỏ so với σ =
   6,90%; muốn khoảng tin cậy loại được số 0 cần hơn hai vạn lệnh. Nói cách
   khác: với thiết kế này, alpha **không thể** được chứng minh bằng sổ lệnh
   thật, dù chờ bao lâu.
3. Muốn rút ngắn thì phải **giảm σ hoặc tăng điểm ước lượng**, không phải
   tăng n. Giảm σ nghĩa là vào lệnh nhất quán hơn (bớt phụ thuộc phiên nào
   máy được bật, bớt biên độ R:R). Tăng điểm ước lượng nghĩa là tìm nguồn
   tín hiệu độc lập — mà nguồn ứng viên gần nhất, dữ liệu cơ bản, vừa đo
   xong và **không có** (mục 23/08/2026 ở trên).

Trạng thái sổ lúc ghi: 113 lệnh (112 đóng, **1 đang mở**), 13.589 quyết
định, quyết định gần nhất 20/08/2026 — hệ thống vẫn quét và vẫn ghi, chỉ
không mở vị thế mới.

---

## SỔ LỆNH "THẬT" ĐƯỢC GHI TRONG 258 GIÂY (23/08/2026)

Đi tìm giá của giả định bất lợi (bất biến 3) thì đụng phải hai thứ khác,
cái thứ hai đổi cách đọc gần như mọi con số nói về sổ lệnh.

### Một, chốt lời cứng đã bị gỡ — nhưng docstring vẫn hứa nó

`PaperTradingJournal.evaluate_open()` mở đầu bằng:

> *"Thứ tự ưu tiên khi cả SL và TP cùng chạm trong một phiên: LẤY SL."*

Ngay bên dưới, trong thân hàm:

```python
# SL là lệnh chờ đặt sẵn ở sàn -> khớp NGAY trong phiên.
# BỎ CHỐT LỜI CỨNG (Hard TP) - Fat-Tail Exploitation
if low <= sl:
    reason, price = ExitReason.STOP_LOSS, sl
```

Không còn nhánh nào so `high` với `take_profit`. `grep -rn ExitReason.TAKE_PROFIT`
toàn repo trả về **0 chỗ gán** — chỉ còn định nghĩa hằng số và hai chỗ tra
nhãn hiển thị. Cột `take_profit` vẫn được tính và vẫn được ghi vào DB, và
vẫn không có gì đọc nó để ra quyết định.

**Hệ quả cho mục "đo giá của giả định bất lợi" trong danh sách tồn đọng:
tình huống ấy không còn đường chạy.** SL và TP không thể "cùng chạm" khi TP
không được kiểm. Giả định bất lợi còn sống ở chỗ khác và ở đó nó ĐANG đúng:
trailing stop và dời-về-hoà-vốn chỉ có hiệu lực **từ phiên sau**.

### Hai, 19/112 lệnh đã đóng mang một lý do mà mã hiện tại không sinh ra được

```
ly do dong        n    thang        TB       min       max
TAKE_PROFIT      19    19 (100%)  +17,23%   +4,92%   +23,81%
STOP_LOSS        44     0 (  0%)   -3,02%  -10,12%    -0,40%
SIGNAL_REVERSED  48     8 ( 17%)   -2,46%   -8,44%    +4,76%
MAX_HOLD          1     1 (100%)  +12,39%
                        ---------
tong             112   28 ( 25%)   +0,792%
```

Toàn bộ kỳ vọng dương của sổ nằm ở 19 dòng ấy: +17,23% × 19 = +327 điểm,
93 dòng còn lại = −239 điểm, chia 112 ra +0,79%.

**Đừng đọc thành "luật mới tệ hơn".** Bỏ 19 dòng ra rồi tính lại cho
−2,567% (KTC [−3,192 ; −1,941]) là một con số **sai**: dưới luật hiện hành,
những lệnh từng chạm chốt lời sẽ chạy tiếp và thoát bằng trailing stop hoặc
đảo tín hiệu, chứ không biến mất. Xoá dòng không mô phỏng được luật mới.

Điều đọc được là: **sổ này trộn hai chế độ thoát lệnh, nên không đọc được
như một chiến lược.** Trong đó có `alpha in-sample +0,090%` — một trong
những con số đang được dùng để biện minh cho việc giữ cổng đóng.

Riêng walk-forward thì KHÔNG dính: `walkforward._mo_phong` gọi
`paper_runner.run_session` + `PaperTradingJournal`, tức đúng luật hiện
hành. 408 lệnh OOS đều là chế độ hiện tại.

### Ba, và đây là cái lớn: cả 113 lệnh được ghi trong 258 giây

```
trades.created_at   min 2026-08-07 14:41:16
                    max 2026-08-07 14:45:35     -> 258 giay
so dong ghi sau 08/08/2026:  0
```

113 lệnh trải từ tín hiệu 2024-01-05 đến 2026-06-26 — hơn hai năm rưỡi —
được viết vào đĩa trong hơn bốn phút.

`created_at` **có** trong `sheets_store._COLS` nên nó đi qua vòng đẩy–kéo
mà không bị ghi lại. Nghĩa là lần khôi phục sau sự cố 12/08 giữ nguyên dấu
thời gian gốc, chứ không đóng dấu mới. Con số 07/08 là lần ghi thật.

**Sổ này chưa bao giờ tích luỹ một lệnh nào từ việc quét tiến về phía
trước.** Nó là kết quả của MỘT lượt mô phỏng chạy ngày 07/08/2026, bốn ngày
trước sự cố ghi đè.

Bảng `decisions` thì ngược lại — vẫn chạy thật, 5.071 quyết định riêng
tháng 08/2026. Máy vẫn quét, vẫn chấm, vẫn ghi. Nó chỉ chưa bao giờ mở một
vị thế nào ngoài lượt mô phỏng đó.

### Vì sao điều này đổi ô C5

`CLAUDE.md` gọi `paper_trades.db` là *"bằng chứng duy nhất chưa bị tối ưu
chạm vào"*. Câu ấy đúng theo nghĩa hẹp — không vòng tối ưu nào ghi đè nó
nữa — nhưng nó **không phải** một bản ghi tích luỹ tiến về phía trước, và
đó là thứ mà cách gọi "sổ lệnh thật" gợi ra.

Hệ quả cho quyết định mở/đóng cổng:

- Giữ đóng thì bằng chứng tiến-về-phía-trước **vẫn là 0 lệnh**, không phải
  "113 lệnh và chờ thêm". Nhịp không chậm — nó bằng không, và đã bằng
  không từ đầu.
- Mở cổng là con đường duy nhất sinh ra loại bằng chứng đó. Ở sổ giấy,
  không có tiền thật nào bị đặt vào.
- Cái mất khi mở không phải tiền mà là **tính thuần nhất**: sổ sẽ có thêm
  một chế độ thứ ba (lệnh sinh tiến-về-trước) cạnh hai chế độ đang trộn.
  Muốn tránh thì phải tách sổ, hoặc ít nhất đánh dấu được dòng nào thuộc
  lượt mô phỏng 07/08.

Chưa đụng gì vào cổng. Đây là ghi chép, không phải thay đổi.

---

## `lo_ghi_hang_loat()` — sổ tự khai nó được sinh ra thế nào (23/08/2026)

Việc 1 của hai việc chốt sau khi phát hiện 113 lệnh được ghi trong 258 giây.

### Không thêm cột — dấu vết đã nằm sẵn trong dữ liệu

Cách hiển nhiên là thêm một cột `nguon` vào bảng `trades` rồi điền tay cho
113 dòng. Không làm, vì ba lý do:

1. `sheets_store` soi gương toàn phần và **nổ khi lệch cấu trúc cột** —
   thêm cột là kéo theo một lần di trú trên cả kho ngoài.
2. Nhãn điền tay chỉ đúng cho 113 dòng đã biết. Lô hàng loạt tiếp theo sẽ
   lại lọt.
3. Dấu vết đã có sẵn: `created_at` là lúc GHI VÀO ĐĨA, `signal_date` là
   ngày mô phỏng. Một sổ tích luỹ tiến về phía trước ghi mỗi lần một lệnh,
   cách nhau hàng giờ; một lượt mô phỏng ghi hàng trăm lệnh trong vài giây.

Nên đây là một **phép đo**, không phải một nhãn.

### Ba ngưỡng, và cái thứ ba mới là cái phân biệt

```python
KHE_TOI_DA_GIAY   = 60.0   # cach nhau hon the -> hai lo khac nhau
TOI_THIEU_LENH_LO = 10     # it hon thi khong noi duoc gi
TOI_THIEU_NGAY_TRAI = 90   # signal_date cua lo phai TRAI dai
```

Hai ngưỡng đầu là hiển nhiên. Ngưỡng thứ ba là thứ giữ cho cảnh báo không
kêu bậy: **một phiên bận rộn mở 20 lệnh trong 30 giây trông y hệt một lượt
mô phỏng nếu chỉ nhìn `created_at`** — khác nhau ở chỗ 20 lệnh ấy cùng một
ngày tín hiệu, còn mô phỏng ghi lệnh của 2024 cạnh lệnh của 2026.

Đo trên sổ thật:

```
so_lo 1 · so_lenh_trong_lo 113 · so_lenh_khong_ro 0
   ghi   07/08/2026 14:41:16 -> 14:45:35   (258 giay)
   tin hieu  2024-01-05 -> 2026-06-26      (903 ngay)
```

`paper_metrics.report()` in cảnh báo ngay trên mục "Lý do đóng lệnh", cùng
chỗ và cùng giọng với cảnh báo đòn bẩy.

### Rỗng nghĩa là "không thấy", không phải "không có"

`Trade.created_at` mặc định `None`, và `_lay_cot()` trả `None` khi hàng
thiếu cột — sổ cũ hơn schema hiện tại thì thiếu thật, `sqlite3.Row` ném
`IndexError` chứ không trả `None`. `tom_tat_lo_ghi()` báo riêng
`so_lenh_khong_ro` để phần chưa biết không lẫn vào phần đã kết luận.

### 10 test, 5 đột biến đỏ — và một đột biến từng SỐNG

Đột biến "bỏ ngưỡng số lệnh tối thiểu của một lô" ban đầu vẫn **xanh**: mọi
trường hợp ít lệnh trong bộ test đều bị chặn sớm ở lối vào hàm
(`len(co) < TOI_THIEU_LENH_LO`), nên phép kiểm bên trong vòng lặp chưa bao
giờ được chạm tới. Thêm
`test_lo_NHO_nam_canh_lo_lon_van_phai_bi_bo_qua` (30 lệnh cạnh 4 lệnh) thì
5/5 đỏ.

---

## Công tắc `CHOT_LOI_CUNG` — dựng để ĐO, không phải để bật

Việc 2 cần chạy walk-forward hai lần trên đúng cùng dữ liệu, nên cần một
đường bật lại chốt lời cứng mà **không đổi hành vi mặc định**.

```python
CHOT_LOI_CUNG = False        # tat = hanh vi dang chay tu truoc
...
if low <= sl:
    reason, price = ExitReason.STOP_LOSS, sl
elif CHOT_LOI_CUNG and high >= tp:
    reason, price = ExitReason.TAKE_PROFIT, tp
```

`elif` chứ không phải `if` thứ hai — đó là thứ giữ bất biến 3 khi công tắc
bật: cả hai cùng chạm trong một phiên thì vẫn LẤY SL. Đổi sang hai `if` rời
là để TP ghi đè SL, đúng cái giả định có lợi bị cấm. Đột biến đó đỏ.

Docstring của `evaluate_open()` cũng được sửa: bản trước hứa một nhánh TP
mà thân hàm đã gỡ từ lâu — đọc nó rồi tin là hiểu sai hệ thống đang chạy.

512 test xanh · 0 CHẶN · 3.11 sạch.

---

## GỠ CHỐT LỜI CỨNG LÀ ĐÚNG HAY SAI — ĐÃ ĐO (23/08/2026)

Việc 2. Chạy `walkforward.chay()` **hai lần**, cùng dữ liệu, cùng stride,
cùng chế độ bộ nhớ, cùng luật chọn ngưỡng nêu trước. Khác duy nhất một
thứ: `paper_trading.CHOT_LOI_CUNG`. Mỗi lượt ~24 phút.

### In-sample (71 mã) — TẮT thắng ở mọi ngưỡng

```
nguong    TAT      BAT     chenh      (ky vong moi lenh)
   45   +0,302   +0,036   +0,266
   48   +0,389   +0,147   +0,242
   50   +0,548   +0,223   +0,325
   52   +0,545   +0,152   +0,393
   55   +0,721   +0,277   +0,444
   58   +0,883   +0,400   +0,483
   62   +1,310   +0,648   +0,662
```

Khoảng cách **rộng dần theo ngưỡng**. Cả hai bên đều chọn 62 theo luật nêu
trước (≥30 lệnh, rồi kỳ vọng cao nhất).

### Ngoài mẫu (33 mã, vùng chưa thể đã nhìn)

```
          lenh   ky vong    WR     nam giu   sigma   von_tb  von_dinh
TAT        386   +0,616%   26,7%   20,3 ng   10,18%   145%     524%
BAT        430   +0,426%   28,8%   17,4 ng    7,72%   137%     533%

alpha khop tung lenh
TAT     -0,008%   KTC [-0,797 ; +0,845]   chua 0
BAT     -0,006%   KTC [-0,607 ; +0,629]   chua 0
```

### Ba điều đọc được, điều thứ hai là điều quyết định

**1. Gỡ chốt lời cứng KHÔNG làm hỏng gì.** Kỳ vọng cao hơn ở mọi ngưỡng
in-sample và cao hơn ngoài mẫu (+0,616% so với +0,426%). Nhưng chênh lệch
ấy **không phân biệt được với 0**:

```
chenh lech TAT - BAT = +0,190%   SE 0,638   KTC 95% [-1,061 ; +1,440]
```

**2. Trên alpha — thước quyết định của bất biến 6 — hai luật GIỐNG HỆT
NHAU.** −0,008% và −0,006%, cách nhau 0,002 điểm phần trăm, cả hai đều
chứa 0. Nghĩa là phần kỳ vọng dôi ra của bản TẮT được mua bằng **thời gian
ở trong thị trường**, không phải bằng kỹ năng:

```
nam giu TB   20,3 ngay (TAT)  vs  17,4 ngay (BAT)   -> dai hon 17%
so lenh         386           vs     430            -> it vong quay hon
```

Giữ lâu hơn thì rổ chuẩn trong cùng khoảng ấy cũng lãi hơn, nên alpha
không đổi. Đây đúng là cái bẫy bất biến 6 sinh ra để bắt.

**3. Thứ chốt lời cứng THẬT SỰ làm là giảm phương sai, không phải tăng
lợi nhuận.** σ 10,18% → 7,72%, tức **giảm 24%**. Đó là một tác dụng có
thật và đo được — nó chỉ không phải tác dụng mà cái tên "chốt lời" gợi ra.

### Và bí ẩn "19 lệnh vàng" trong sổ thật đã có lời giải

Sổ thật: 19 lệnh `TAKE_PROFIT`, **19/19 thắng**, trung bình **+17,23%**;
93 lệnh còn lại −2,567%. Trông như thể luật cũ là nguồn của toàn bộ lợi
nhuận.

Lượt BẬT ngoài mẫu cho ra **đúng cùng một hình dạng**:

```
TAKE_PROFIT   55 lenh   55/55 thang   +17,81%
con lai      375 lenh                  -2,12%
```

Đó không phải dấu hiệu luật cũ tốt. **Đó là hình dạng mà MỌI luật chốt lời
cứng đều tạo ra**: một khối thắng chắc chắn ở mức chốt, cạnh một khối thua
lớn hơn nhiều. Và phản chứng nay đã đo được — dưới luật hiện hành, cùng thị
trường ấy cho kỳ vọng **cao hơn**, không thấp hơn.

Cảnh báo ghi ngày 23/08 (*"đừng đọc thành luật mới tệ hơn"*) là đúng, và
giờ nó là một câu đo được chứ không còn là một lời nhắc thận trọng.

### Hai điều phải nhớ khi trích số từ hai lượt này

- **Cả hai đều dùng đòn bẩy**: vốn triển khai 145% / 137% trung bình,
  524% / 533% đỉnh. Mọi con số CỘNG DỒN từ hai lượt này là của một tài
  khoản vay được (bất biến 7b). Kỳ vọng mỗi lệnh và alpha thì tính theo
  từng lệnh nên không dính.
- Số lệnh cần để kỳ vọng loại được số 0:

```
TAT   TB +0,616%  sigma 10,18%  ->  1.050 lenh   (2,7x so voi 386 hien co)
BAT   TB +0,426%  sigma  7,72%  ->  1.261 lenh   (2,9x so voi 430)
```

Bản TẮT cần ÍT mẫu hơn để chứng minh — kỳ vọng tăng nhiều hơn phần σ giảm.

### Kết luận cho ô C5

Câu hỏi "luật nào sẽ chạy nếu mở cổng" nay đã trả lời được: **luật hiện
hành, và nó không tệ hơn luật cũ.** Nhưng nó cũng không có alpha — cả hai
đều không.

Nên phép đo này **không** mở khoá ô C5. Nó chỉ gỡ một lý do để trì hoãn:
không còn nghi ngờ rằng việc gỡ chốt lời cứng đã âm thầm làm hỏng thứ gì.

---

## CỔNG C5 ĐÃ MỞ, VÀ NHỮNG GÌ PHẢI DỰNG TRƯỚC ĐÓ (24/08/2026)

`CHO_PHEP_MO_LENH_MOI = True`, ngưỡng 62.

**Lý do mở KHÔNG phải vì tìm thấy lợi thế.** Mọi phép đo alpha đều chứa số
0: rho điểm cuối −0,019 · alpha walk-forward −0,011% · alpha sổ +0,090% ·
hai luật chốt lời giống hệt nhau · năm chỉ số cơ bản không cái nào sống sót
qua Bonferroni.

Lý do là ba điều đo được, cộng lại:

1. **Cấu hình chạy TRỰC TIẾP chưa bao giờ được đo.** Backtest đo một hệ bị
   cắt tay chân — không có lịch sử TradingView và tin tức nên 2 agent là
   hằng số, 2 agent là công tắc ba nấc. Sáu agent đầy đủ chỉ đo được tiến
   về phía trước. Giữ cổng đóng bảo đảm nó không bao giờ được đo.
2. **Chờ thêm dữ liệu không phải một lựa chọn.** Cả 113 lệnh được ghi trong
   258 giây ngày 07/08/2026. Giữ đóng thì bằng chứng tiến-về-trước đứng mãi
   ở 0 lệnh, không phải "113 và chờ thêm". Số học: cần 1.050 lệnh để kỳ
   vọng loại được số 0, tức ~23 năm ở nhịp 45 lệnh/năm; alpha cần 22.601
   lệnh, tức không bao giờ.
3. **Điều kiện mở lại ghi trong chính mã ĐÃ ĐẠT.** 5D chọn ngưỡng 62 trên
   khoảng A, đo trên khoảng B, A ∩ B = ∅. Thứ không đạt là ý nghĩa thống kê
   — vốn chưa bao giờ nằm trong điều kiện. Siết thêm sau khi đã thấy kết
   quả là tự đổi thước, cùng họ với bất biến 7.

### Ba thứ dựng trước khi mở

| | |
|---|---|
| `TRAN_VON_CAM_KET_PCT = 100` | sổ thật từng chạm **208%** vốn cam kết |
| `run_daily` NHẬP `BUY_THRESHOLD` | trước đó cầm **50,0** song song với 62 |
| `dieu_kien_dong_lai()` | nêu TRƯỚC khi có dữ liệu |

**Ngưỡng đôi là lỗi nguy hiểm nhất trong ba.** `run_daily.BUY_THRESHOLD =
50.0` chạy song song với `paper_trading.BUY_THRESHOLD = 62` — cổng đóng nên
hai con số chưa bao giờ gặp nhau. Mở cổng mà không sửa thì hệ thống chạy ở
50 trong khi mọi phép đo ngoài mẫu đều đo ở 62. Và 50,0 chính là "quán
quân" của 20 vòng tối ưu trên cùng dữ liệu — đúng thứ bất biến 7 cấm.

Gác cũ `test_run_daily_khong_chep_cung_nguong_mua` đỏ khi đổi sang nhập, vì
nó đòi một lệnh gán tại chỗ. Đã siết chặt hơn thay vì nới: **cấm khai báo
lại, kể cả khai đúng 62**. Bằng nhau hôm nay không cứu được — bản sao không
sai vào ngày nó ra đời, nó sai vào ngày bản gốc đổi và nó thì không.

### Điều kiện đóng lại — nêu trước, không chế sau

```
>= 60 lenh tien-ve-truoc DA DONG   VA   can tren KTC 95% cua ky vong < 0
```

Vế thứ hai cố ý khắt khe: với σ ≈ 10% một chuỗi âm ngắn là chuyện thường,
đóng cổng vì nó là phản ứng với nhiễu. `report()` in trạng thái mỗi phiên.
`lenh_tien_ve_truoc()` loại cả lô mô phỏng 07/08 lẫn lệnh thiếu
`created_at` — bằng chứng chưa rõ nguồn gốc không được tính là bằng chứng.

### GIÁ CỦA TRẦN — và ba lần đo, hai lần sai

| | lệnh | kỳ vọng | von_tb | von_đỉnh | alpha |
|---|---|---|---|---|---|
| không trần | 386 | +0,616% | 145% | 524% | −0,008% |
| **có trần** | **390** | **+0,614%** | 143% | 524% | −0,011% |

**Trần không tốn gì — và cũng không chặn được gì trong backtest.** Vốn
triển khai không hề giảm.

Vì `_mo_phong` chạy **theo mã**: xong toàn bộ lịch sử FPT rồi mới sang ACB.
Nên tại mọi điểm quyết định chỉ có vị thế của mã đang chạy đang mở. Trong
khi `paper_metrics` dựng lại vốn triển khai theo LỊCH trên toàn bộ mã.

> **Các con số đòn bẩy 145% / 524% / 1372% mô tả một danh mục mà máy chưa
> bao giờ thực sự nắm.** Chúng đúng như một mô tả về độ chồng lấn của tập
> lệnh, nhưng không phải một quyết định máy đã ra — và không ràng buộc danh
> mục nào kiểm định được trong máy này. Giá trị của trần nằm ở đường chạy
> THẬT, nơi `run_daily` quét cả rổ trong cùng một phiên và nơi 208% đã xảy
> ra.

**Hai lần đo trước đều sai, và cả hai lần con số trông đủ hợp lý để báo
cáo.**

*Lần một* — 142 lệnh, tưởng là "trần cắt 63% số lệnh". Thật ra là **4 lệnh
mồ côi chiếm 93,8% hạn mức**: lệnh còn mở lúc hết dữ liệu của một mã không
bao giờ được đóng, nằm lại trong DB suốt phần còn lại của lượt chạy. Trước
khi có trần thì vô hại (`[x for x in lenh if x.status == CLOSED]` lặng lẽ
bỏ chúng ra); có trần rồi thì chúng ăn vào hạn mức của mọi mã sau. Vá bằng
`dong_so_sach()`: OPEN đóng ở giá phiên cuối với lý do `HET_DU_LIEU`,
PENDING **xoá** vì chúng chưa bao giờ khớp.

*Lần hai* — kỳ vọng −0,419%, alpha −1,044%, tưởng là "trần làm hệ thống
lỗ". Con số đổi quá nhiều cho 4 lệnh thêm vào nên mở sổ ra đếm:

```
BAF  vao  23.440,0  ra  23,27  -> -99,90%
FRT  vao 138.120,0  ra 141,32  -> -99,90%
HAX  vao  16.000,0  ra  15,86  -> -99,90%
VTP  vao  97.880,0  ra 100,30  -> -99,90%
```

Bốn mã cùng −99,90% không phải bốn mã cùng sập. **Nghìn đồng gặp VNĐ** —
đúng bẫy trong bảng "hỏng âm thầm" của `NGUYEN-TAC-DO-LUONG.md`, và đúng
thứ docstring của `run_session` cảnh báo dài dòng. Giá thô được truyền vào
`dong_so_sach` mà thiếu `price_multiplier`.

Đáng chú ý: lỗi này đẩy kết quả **xấu đi** — ngược hướng quy tắc số 1 mô
tả. Nó vẫn sai y như vậy. Hướng của thiên lệch là một chỉ báo, không phải
một phép kiểm.

Nay `dong_so_sach` **tự chặn**: giá đóng lệch quá **10 lần** so với giá vào
thì ném `ValueError`. Biên độ sàn 7–15% một phiên nên 10 lần không thể là
biến động. Ném chứ không tự nhân 1000 — tự sửa nghĩa là đoán xem người gọi
*định* nói gì.

---

## SAU KHI MỞ CỔNG — thứ tự ưu tiên đổi (24/08/2026)

Cổng đóng thì một kết luận sai chỉ nằm trong báo cáo. Cổng mở rồi thì nó
sinh ra lệnh. Ba việc làm ngay sau đó:

### 1. "0 lệnh" phải nói được vì sao

`execute_daily_scan` bỏ qua một mã bằng `break` khi nguồn trả `SYNTHETIC`
(mất kết nối → `data_collectors` sinh giá bằng `np.random`) hoặc khi không
đủ 20 nến. **Cả hai nhánh im lặng hoàn toàn.** Một ngày cả 71 mã mất nguồn
cho ra đúng cùng một báo cáo với một ngày không có tín hiệu nào.

Đã kiểm: dữ liệu SYNTHETIC **không** tới được `run_session` — nhánh `break`
chặn trước. Vấn đề là sự im lặng, không phải dữ liệu bịa.

Nay đếm theo lý do, in ra, và thêm dòng "Số mã quét được" vào báo cáo phiên.
Quét được dưới **một nửa** rổ thì báo động: phiên đó không kết luận được gì
về thị trường, nó chỉ kết luận được rằng nguồn đang hỏng. Cảnh báo đi bằng
văn bản chứ **không** bằng mã thoát — một job đỏ sinh báo động giả che mất
chính thứ chuông sinh ra để canh.

### 2. Post-mortem: thiếu thành phần thì KHÔNG được đoán

```python
c_trend = current_breakdown.get("trend_score", 50)   # ban cu
```

Với dung sai ±5 trên ba chiều, một toạ độ bịa vẫn khớp được một mẫu và trừ
**12 điểm** trên thang 100 — trong khi ngưỡng mua là 62. Đường này đang
chấm điểm thật: `save_memory()` bật cho sổ thật từ 21/08, cổng mở từ 24/08.

Nay fail-closed cả hai chiều, cùng kỷ luật module đã tuyên bố cho
`phien_hoc`. Dùng `is None` chứ không `not` — điểm 0 là giá trị hợp lệ, và
`momentum` đo được là **luôn** trả 0.

Một đột biến **sống sót** ở lần đầu: test dùng mẫu (65,65,100) rồi bỏ
`trend_score`, nhưng |50−65| = 15 > dung sai 5 nên bản cũ cũng không khớp —
xanh cả hai bên. Con số bịa chỉ cắn khi bộ nhớ có mẫu ở gần nó, và đó đúng
là điều sẽ xảy ra khi bộ nhớ lớn dần.

### 3. Lần thứ BA cùng một lỗi — nên vá theo hệ thống

```
22/08  tools/kiem_ban_sach.py       — cong kiem ban sach
23/08  experiment_fundamentals.py   — script quyet TRONG_SO_CO_BAN
24/08  extend_history.py            — lenh CLAUDE.md bao nen chay
```

Cả ba chết ở `print` đầu tiên vì console cp1258, TRƯỚC khi làm được việc gì.
Không lần nào có test đỏ, vì test **import** module chứ không **chạy** nó.

`tests/test_script_chay_duoc_tren_windows.py` quét toàn repo: mọi file có
`if __name__ == "__main__"` và có `print` đều phải gọi `reconfigure`, xác
nhận bằng AST. 15 script, tất cả đều đạt sau khi vá thêm
`tools/dung_lai_bo_nho.py` và `tools/nap_service_account.py`.

Kèm một chốt tự soi: gác phải nhìn thấy ≥12 script. Bộ lọc hỏng trả về 2
file thì test trên vẫn xanh mà chẳng gác gì.

Chạy được rồi, `extend_history.py --check` nói ra một điều chưa ai biết:

```
Moc chung som nhat cua CA RO: 2026-02-06
Phien it nhat: 132 (GEL) · nhieu nhat: 1210 (DIG)
```

### Dọn nhánh

15 nhánh đã merged, mỗi nhánh **0 commit riêng** so với `main`, đã xoá khỏi
remote. SHA ghi lại trong commit dọn dẹp phòng khi cần
`git push origin <sha>:refs/heads/<tên>`.

Còn lại `main` và `du-lieu/lam-moi-co-ban`.

---

## NỐI TRƯỢT GIÁ VÀO — VÀ KẾT QUẢ CÓ Ý NGHĨA THỐNG KÊ ĐẦU TIÊN CỦA DỰ ÁN
## (24/08/2026)

`truot_gia.py` và `vong_doi_lenh.py` có 29 test và tồn tại từ lâu, nhưng
cho tới hôm nay **không file nào ngoài test của chính chúng import**. Sổ
lệnh vẫn coi mọi lệnh khớp TOÀN BỘ, NGAY, ở đúng giá mong muốn. Cuối mỗi
báo cáo có câu *"Giao dịch thật còn có trượt giá, khớp một phần và tâm lý
— kết quả thực tế sẽ thấp hơn"*. Câu đó đúng, nhưng nó là **lời cảnh báo,
không phải phép đo**.

### Đường nối

| | qua module nào | vì sao |
|---|---|---|
| **vào lệnh** | `vong_doi_lenh.dat_lenh` → `khop_trong_nen` | dùng cả hai module: lô chẵn, biên độ ±7%, trần thanh khoản mỗi nến, khớp một phần, rồi mới tới trượt giá |
| **ra lệnh** | `truot_gia(..., BAN, ...)` | **không** qua vòng đời lệnh — một vị thế đang mở phải thoát được, không thể "sàn từ chối" rồi kẹt lại vĩnh viễn |

Khớp một phần thì `size_pct` giảm theo tỷ lệ thực khớp — giữ nguyên là ghi
vào sổ một vị thế chưa bao giờ tồn tại. Sàn từ chối thì **xoá** lệnh
PENDING, không mở rồi đóng ngay: một lệnh không khớp không phải một giao
dịch lãi/lỗ 0%.

### In-sample: −0,43 điểm phần trăm mỗi lệnh, ở MỌI ngưỡng

```
nguong    TAT      BAT     chenh    WR TAT   WR BAT
    45  +0,305   -0,141   -0,446     26,9     24,9
    48  +0,389   -0,043   -0,432     27,8     26,1
    50  +0,548   +0,116   -0,432     28,5     26,9
    52  +0,545   +0,109   -0,436     28,9     27,4
    55  +0,721   +0,300   -0,421     29,6     27,9
    58  +0,883   +0,452   -0,431     30,3     28,4
    62  +1,310   +0,888   -0,422     31,9     29,0
```

Chênh lệch **gần như bằng nhau ở cả bảy ngưỡng**. Đó là dấu hiệu mô hình
hành xử đúng: chi phí thực thi là chi phí **mỗi lệnh**, không co giãn theo
độ chọn lọc. Nếu nó biến động mạnh theo ngưỡng thì phải nghi ngờ trước.

Ngưỡng chọn vẫn là 62 ở cả hai bên — trượt giá không đổi thứ tự các ngưỡng.

### Ngoài mẫu: đổi KẾT LUẬN, không chỉ đổi con số

```
        lenh   ky vong    WR     von_tb   alpha      KTC 95%
TAT      390   +0,614%   26,9%    143%   -0,011%   [-0,766 ; +0,832]  chua 0
BAT      385   -0,291%   25,5%    139%   -0,927%   [-1,689 ; -0,076]  LOAI 0
```

> **Đây là kết quả có ý nghĩa thống kê đầu tiên trong toàn bộ lịch sử dự
> án. Và nó âm.**
>
> Với chi phí thực thi thực tế, chiến lược **thua rổ chuẩn 0,927% mỗi
> lệnh**, khoảng tin cậy 95% loại được số 0 — đo trên vùng dữ liệu chứng
> minh được là chưa thể đã bị nhìn.

Bốn lần trước dự án cho ra số đẹp rồi hoá ra vô nghĩa. Đây là lần đầu một
con số **xấu** đạt mức có ý nghĩa. Cùng một kỷ luật đo lường, hướng ngược
lại.

Cách đọc đúng: rổ chuẩn mua một lần rồi giữ, trả chi phí thực thi **hai
lần**. Chiến lược quay vòng 385 lệnh, trả **770 lần**. Lợi thế của nó vốn
đã không phân biệt được với 0; cộng chi phí quay vòng vào thì phần âm lộ ra.

### Kết quả KHÔNG phụ thuộc giả định vốn danh mục

`VON_DANH_MUC_VND = 1 tỷ` là giả định cần để đổi `size_pct` sang **số cổ
phiếu** — mà số cổ phiếu là thứ quyết định tác động thị trường. Đã kiểm
độ nhạy ở giá vào trung vị 16.100đ của chính tập lệnh OOS:

```
von (ty)    so CP   ty trong  chenh lech  tac dong   tong %
     0,1    1.100     0,0006          50         9    0,311
     0,5    5.900     0,0029          50        21    0,311
     1,0   11.800     0,0059          50        30    0,311   <- dang dung
     5,0   59.000     0,0295          50        66    0,621
    20,0  236.000     0,1180          50       133    0,932
```

**Từ 100 triệu tới 1 tỷ, chi phí y hệt nhau.** Tác động thị trường (9đ,
21đ, 30đ) quá nhỏ để đẩy qua bước giá kế tiếp. Cái tốn tiền là **bước giá
50đ** — một sự thật của lưới giá, không phải lựa chọn mô hình. Kết luận
trên đó vững trong toàn bộ dải danh mục cá nhân.

Chỉ từ 5 tỷ trở lên tác động mới bắt đầu cộng thêm một bước.

### Công tắc BẬT mặc định từ hôm nay

```python
MO_PHONG_TRUOT_GIA = True
VON_DANH_MUC_VND = 1_000_000_000
```

**Mọi con số đo TRƯỚC 24/08/2026 trong docs đều KHÔNG có chi phí thực thi.**
Đọc chúng thì phải trừ hao khoảng 0,43 điểm phần trăm mỗi lệnh — kể cả kỳ
vọng sổ +0,79%, kể cả alpha +0,090%, kể cả mọi bảng walk-forward.

### Hai đột biến sống sót ở lần đầu

**1. "công tắc mặc định BẬT" vẫn xanh** — mọi test đều monkeypatch công
tắc nên mặc định chưa bao giờ được khẳng định. Đã ghim.

**2. "nhân hệ số giá vào cả `volume`" vẫn xanh** — và đây là cái nguy hiểm.
`run_session` nhân mọi giá trị trong `bar` với `price_multiplier` để quy
nghìn đồng về VNĐ. Nhân nhầm cả khối lượng thì tỷ trọng nhỏ đi **1.000
lần**, tác động thị trường gần như biến mất, trượt giá tụt còn đúng một
bước giá — mà kết quả vẫn trông hợp lý hoàn toàn. Test cũ gọi thẳng
`paper_trading` nên không bao giờ đi qua chỗ đó. Đã thêm test chặn
`fill_pending` và soi nến nó nhận được.

### Một test cũ đỏ, và nó đỏ đúng chỗ

`test_gia_vao_dung_bang_gia_mo_cua_phien_khop` khẳng định giá vào **bằng
đúng** giá mở cửa. Bất biến nó khoá là bất biến 1 — khớp ở phiên SAU ngày
tín hiệu, không nhìn trộm giá đóng cửa phiên tín hiệu — và bất biến đó vẫn
nguyên. Chỉ phép so bằng-tuyệt-đối là hỏng.

Đã thay bằng hai điều kiện, cộng lại **chặt hơn** phép so cũ: giá vào phải
≥ giá mở cửa (trượt sai chiều là đang tặng tiền cho mình) và ≤ 2% trên giá
mở cửa (trượt cỡ đó là mô hình hỏng, không phải chi phí).

564 test xanh · đột biến 6/6 đỏ · 0 CHẶN · 3.11 sạch.

---

## RÀ SOÁT CODE CHẾT — VÀ MỘT NÚM VẶN GIẢ
## (28/08/2026)

Kiểm kê bằng **AST**, không bằng grep chuỗi. Lý do không phải là sự cầu
kỳ: `"news" in src` khớp cả chữ trong chú thích, mà `master_agent.py` đầy
chú thích nói về news. Grep sẽ báo "còn dùng" cho đúng thứ đã chết.

Mốc: **564 test xanh** trước → **571** sau (+7 test gác mới). 3.11 sạch.
Điểm chấm **không dịch một ly** — đo lại bằng cùng kịch bản trước/sau:
60 / 68 / 64 / 60 / 56 / 52, y hệt.

### Đã xoá

| Thứ | Ở đâu | Vì sao chắc là chết |
|---|---|---|
| `tradingview_mcp.py`, 106 dòng | gốc repo | Bản sao thứ hai của `TradingViewCollectorAgent`. AST: không file nào import; không .md nào nhắc. |
| Nhánh `if bull_total < 0:` | `debate_agents.py:352` | Sàn cấu trúc của `bull_total` là **+1,5**; đo 262 lượt thật, thấp nhất +1,50. |
| Khoá `"news": 0.0` × 3 | `master_agent.py` | Không biểu thức nào đọc `weights["news"]`. |
| 24 import thừa | 14 file | Tên chỉ xuất hiện đúng một lần trong file — chính dòng import. |

`from __future__ import annotations` **không** bị đụng tới ở bất kỳ file
nào. Máy quét gắn cờ nó ở 20 file vì nó không phải một cái tên được dùng
— nhưng nó là chỉ thị biên dịch, và gỡ nó ra là làm hỏng CI 3.11. Đây là
cái bẫy lớn nhất của việc "dọn import tự động".

### Núm vặn giả — thứ đáng kể nhất tìm được

Cả ba bộ trọng số động mang khoá `"news": 0.0`, mà biểu thức
`pre_debate_score` không hề nhắc tới `weights["news"]`. Đặt `0.25` vào đó
thì **không có gì xảy ra**: chạy xong, số không đổi, không ai biết mình
vừa không làm gì. Đúng dạng "silent pass" mà `NGUYEN-TAC-DO-LUONG.md`
cảnh báo, chỉ khác là nó nằm ở chỗ người ta tưởng mình đang chỉnh chiến
lược.

Chọn **gỡ khoá** chứ không phải nối `news_norm` vào tổng. Nối vào thì
0,0 × NaN = NaN — `normalize()` kẹp bằng `max/min`, mà NaN đi qua `max/min`
không đoán trước được, nên một điểm tin tức hỏng sẽ đầu độc cả điểm chấm.
Gỡ khoá không thêm rủi ro nào và vẫn đóng được cái bẫy.

`news_norm` vẫn được tính, vì `score_breakdown["news_score"]` hiển thị nó.
Nó là số để NHÌN, không phải số để CHẤM — nay đã ghi thành lời tại chỗ.

### Bốn phép soi KHÔNG tìm thấy gì

Cũng là kết quả, và là kết quả tốt:

| Soi cái gì | Thấy |
|---|---|
| Định nghĩa trùng tên trong cùng phạm vi (bản sau đè bản trước) | 0 |
| Lệnh nằm sau `return` / `raise` / `continue` / `break` | 0 |
| Method của lớp không nơi nào nhắc tên | 0 |
| Import vòng | 0 |

### Hai hàng rào mới, cả hai đều qua đột biến

**`tests/test_dau_hieu_tranh_luan.py`** — quy ước dấu của Debate Council:
Bull chỉ dương, Bear chỉ âm, Devil chỉ âm. Phép cộng
`bull*0,4 + bear*0,4 + devil*0,2` chỉ có nghĩa "hai phe triệt tiêu nhau"
khi quy ước đó đúng, mà không dòng nào trong `debate_agents.py` phát biểu
nó thành lời. Phá quy ước thì điểm vẫn nằm trong ±8 và vẫn trông hợp lý.
Đột biến 4/4 đỏ.

**`tests/test_trong_so_that_su_duoc_dung.py`** — mọi khoá trong bộ trọng
số phải thực sự được nhân vào điểm, và ngược lại. Gác cả hai chiều: khoá
thừa là núm vặn giả, khoá thiếu là `KeyError` ở đúng nhánh đó. Đột biến
3/3 đỏ — kể cả đột biến **quên một hạng tử** (bỏ `risk_norm * weights["risk"]`
khỏi tổng), thứ mà một test so-điểm-cuối bình thường sẽ không bắt được.

### Nghi chết nhưng KHÔNG xoá — chờ người quyết

| Thứ | Vì sao dừng tay |
|---|---|
| `top_stocks_screener.py` (57 dòng) | Mồ côi thật, nhưng là **năng lực riêng** (quét song song top 5), không phải bản sao. Xoá là bỏ một tính năng, khác với dọn trùng lặp. |
| `google_sheets_sync.get_gspread_client()` | Không ai gọi, nhưng docstring nói rõ nó là **cửa thoát hiểm soi lỗi bằng tay**. Chết theo nghĩa đếm lời gọi, sống theo nghĩa chủ ý. |
| 9 script `optimize_*` / `run_*_test.py` ở gốc repo | Có thể là **nguồn gốc** của những con số đang nằm trong docs. Xoá trước khi truy nguồn là mất dấu vết đo lường. |
| `test_trailing_sim.py` ở gốc repo | Có trong git nhưng nằm ngoài `tests/`, nên pytest không hề chạy nó. Một test không ai chạy là tệ hơn không có test. |
| `*.db` ở gốc repo | Dữ liệu đo lường. Không đụng. |

### Một chuyện nhỏ phát hiện lúc chạy

`tools/kiem_cu_phap_311.py` đỏ nếu chạy **song song** với `pytest`: có test
tạo thư mục tạm ngay trong gốc repo (`tmpXXXX/vi_pham_tam.py`), trình kiểm
duyệt đi vào đúng lúc nó đang bị xoá. Không phải lỗi cú pháp — nhưng nó
nói rằng có test đang ghi file tạm vào repo thay vì vào thư mục tạm của hệ
thống. Chạy tuần tự thì sạch.

571 test xanh · đột biến 7/7 đỏ · 0 CHẶN · 3.11 sạch.

---

## GỐC RỄ CỦA CỔNG C5 — BỐN NGUYÊN NHÂN, VÀ MỘT CHUỖI TÁM MẮT XÍCH
## (28/08/2026)

Tài liệu này viết để một phiên khởi động TRẮNG TRÍ NHỚ vẫn sửa được cổng
C5 mà không phải đào lại git. Đọc mục này trước khi động vào
`paper_metrics.dieu_kien_dong_lai()` hay `paper_trading.CHO_PHEP_MO_LENH_MOI`.

### Trạng thái đo được ngày 28/08/2026

```
Tổng lệnh trong sổ    : 113   (đã đóng 112, đang mở 1)
Lô ghi hàng loạt      : 1 lô — 113 lệnh trong 0 giây
Lệnh TIẾN-VỀ-TRƯỚC    : 0
Điều kiện đóng        : 0/60 — chưa đủ để kết luận
Kỳ vọng toàn sổ       : +0,792%  KTC 95% [-0,688 ; +2,323]  (CHƯA có chi phí)
σ mỗi lệnh            : 8,21%
```

Ngoài mẫu, KHI BẬT chi phí thực thi (đo cùng ngày, n=385):
kỳ vọng **−0,291%**, alpha **−0,927%**, KTC alpha [−1,689 ; −0,076] **loại 0**.

### Nguyên nhân 1 — hiệu chuẩn theo THẢM HOẠ, không theo BẤT LỢI

Điều kiện viết trong `0f67047`, 26/08/2026 15:51. Chú thích cạnh hằng số:

> *"Với σ ≈ 10%/lệnh, 60 lệnh cho SE ≈ 1,3% — đủ để một kỳ vọng âm nặng
> (dưới −2,5%) lộ ra, và chưa đủ để nhiễu bình thường kích hoạt."*

**Phép tính lực phát hiện ĐÃ được làm, và nó ĐÚNG.** Tính lại với σ đo
thật (8,21%) ra ngưỡng −2,08%, khớp với −2,5% ước ở σ ≈ 10%.

Sai không nằm ở số học mà ở MỤC TIÊU: quy tắc hỏi *"hệ thống có hỏng nặng
không?"* (−2,5%/lệnh) trong khi câu cần hỏi là *"hệ thống có tệ hơn mua rồi
giữ không?"* (−0,927%/lệnh). Lệch nhau **8 lần độ lớn**.

### Nguyên nhân 2 — chỉ định giá MỘT loại sai lầm

Thông điệp `0f67047` lập luận đúng một chiều:

> *"'Kỳ vọng âm' thôi chưa đủ: với σ ~10% một chuỗi âm ngắn là chuyện
> thường, đóng cổng vì nó là phản ứng với nhiễu."*

Sai lầm loại I (đóng nhầm vì nhiễu) được tính toán và chống lại. Sai lầm
loại II (**để mở trong khi đang lỗ thật**) không được nhắc một lần. Cái giá
hai bên không đối xứng: đóng nhầm mất cơ hội quan sát, để mở nhầm mất tiền
suốt thời gian chờ.

### Nguyên nhân 3 — quy tắc bị đóng băng, hệ đo lường vẫn chạy tiếp

```
21/08  5d9c3c8  walk-forward báo alpha kèm KTC   -> công cụ SẴN SÀNG
24/08  be446b0  mở cổng, alpha ≈ 0               -> tiền đề: "không đo được lợi thế"
26/08  0f67047  viết điều kiện, mục tiêu −2,5%   -> hiệu chuẩn theo kỳ vọng
28/08  79a8d32  nối chi phí thực thi             -> alpha ≈0 --> −0,927%
```

Giữa 26/08 và 28/08 **sổ lệnh không đổi một dòng**. Cái đổi là mô hình về
hiện thực. Quy tắc không trở nên sai — thế giới nó được viết cho đã biến mất.

Vì sao dùng kỳ vọng chứ không alpha: **KHÔNG phải vì thiếu công cụ** — đã
kiểm, `vs_benchmark()` trả `alpha` kèm `ci` từ trước `0f67047`, và commit đó
không hề đụng vào `vs_benchmark`. Lý do thật: lúc ấy alpha là +0,090% KTC
[−1,166; +1,391], tức KHÔNG PHÂN BIỆT ĐƯỢC VỚI 0 — mà không thể hiệu chuẩn
một phép kiểm cho hiệu ứng độ lớn 0 (câu hỏi "bao nhiêu lệnh để phát hiện
alpha = 0" phân kỳ). Kỳ vọng là đại lượng duy nhất khi ấy có độ lớn nhìn
thấy được. Lựa chọn đó HỢP LÝ với thông tin lúc đó.

### Nguyên nhân 4 — điều kiện KHÔNG CÓ AI THI HÀNH (nặng nhất)

`dieu_kien_dong_lai()` được gọi đúng MỘT chỗ trong toàn dự án: bên trong
`paper_metrics.report()` — một hàm **nối chuỗi ký tự**.

```python
if _dk["dat"]:
    add("   🔴 ĐIỀU KIỆN ĐÓNG LẠI ĐÃ ĐẠT — nêu trước ngày 24/08/2026.")
    add("   Đặt CHO_PHEP_MO_LENH_MOI = False rồi báo người dùng.")
```

Khi đạt, nó thêm một CÂU VĂN nhờ con người đi sửa mã nguồn. Không nhánh nào
đóng cổng. Và câu văn đó đi đâu:

```
report() -> latest_daily_report.md -> actions/upload-artifact -> zip, giữ 14 ngày
```

`chuong-bao-quet.yml` không kiểm gì về C5: không `::error::`, không mở issue,
không báo động. **Kể cả nếu điều kiện có lực phát hiện 100%, nó vẫn không
đóng được cổng.** Đây đúng mẫu "silent pass" mà dự án săn lùng khắp nơi —
hàng rào an toàn hoá ra là một chuỗi ký tự.

### Chuỗi tám mắt xích — cái nào lành, cái nào gãy

Liệt kê cả mắt LÀNH là cố ý: không có chúng thì không ai biết đã soi hết hay
chưa.

| # | Mắt xích | Kiểm bằng | Trạng thái |
|---|---|---|---|
| 1 | Lệnh mới có `created_at` | đọc INSERT | ✅ `now_vn().timestamp()`, ghi mọi lệnh |
| 2 | Lệnh quét thật không bị lọc nhầm thành "lô mô phỏng" | **chạy** | ✅ 3 lệnh/phiên cùng ngày tín hiệu → 0 lô |
| 3 | Lệnh đóng lại được để mà đếm | đo sổ | ✅ trung vị 6 ngày, TB 12,5, p90 32, max 89 |
| 4 | Đủ lệnh tích luỹ trong thời gian hợp lý | đo OOS | ✅ ~2,17 lệnh mở/phiên (71 mã, ngưỡng 62) |
| 5 | Alpha tính được trên đường chạy thật | **chạy** | ✅ `run_daily.py:249` truyền rổ chuẩn VN-INDEX |
| 6 | Đo đúng đại lượng | đọc mã | ❌ kỳ vọng, không phải alpha |
| 7 | Ngưỡng có lực phát hiện | tính lại | ❌ chỉnh cho −2,5%, thực tế −0,927% |
| 8 | Có thứ gì HÀNH ĐỘNG khi điều kiện đạt | tra toàn repo | ❌ không có gì |

Mắt 5 lành là tin tốt cho phương án sửa: **điều kiện dựa trên alpha làm được
ngay**, không phải xây thêm hạ tầng.

### Lực phát hiện — vì sao đổi một chữ là đổi hẳn bài toán

σ = 8,21%; điều kiện đóng ⟺ trung bình quan sát < −1,96·σ/√n.

```
     n   phải thấp hơn   xác suất ĐÓNG (mu=-0,291%)   ~thời gian
    60          -2,08%                        4,6%     1,3 tháng
   200          -1,14%                        7,2%     4,4 tháng
  1000          -0,51%                       20,1%    21,9 tháng
  6248          -0,21%                       80,0%    11,4 NĂM
```

| đo cái gì | mức thật | n để đạt 80% lực | thời gian |
|---|---|---|---|
| kỳ vọng | −0,291% | 6.248 | **11,4 năm** |
| **alpha** | **−0,927%** | **595** | **13 tháng** |

Nhịp: ~2,17 lệnh MỞ/phiên. 60 lệnh **ĐÃ ĐÓNG** ≈ 28 phiên + trễ nắm giữ
≈ **37 phiên ≈ 1,7 tháng** (con số 1,3 tháng nêu trước đó là của lệnh MỞ,
lạc quan hơn thực tế).

### Ba giả định yếu — cả ba đều đẩy theo hướng LẠC QUAN

1. σ = 8,21% đo từ 112 lệnh **chưa có chi phí thực thi**.
2. Nhịp 2,17 lệnh/phiên suy từ vùng OOS 2022-01 → 2025-02, chế độ thị
   trường khác, và walk-forward chạy `stride=2`.
3. Vốn trung bình OOS 139% ⇒ lệnh chồng lệnh (bất biến 7b). Các lệnh chồng
   nhau chia sẻ cùng cú sốc thị trường ⇒ **cỡ mẫu hiệu dụng nhỏ hơn n** ⇒
   mọi con số lực phát hiện ở trên là lạc quan.

### CHỖ TỐI CHƯA KIỂM — ứng viên nguyên nhân thứ 5

**Bất đối xứng gói vnstock.** Máy cá nhân chạy gói tài trợ; GitHub Actions
và Streamlit Cloud chạy gói miễn phí. Nếu lượng dữ liệu lịch sử khác nhau
làm điểm chấm khác nhau, thì **σ = 8,21% và nhịp 2,17 lệnh/phiên là số của
một hệ thống khác** với hệ thống thật sự sinh lệnh từ 31/08.

Chưa liệt vào danh sách nguyên nhân vì CHƯA ĐO. Cách đo: chạy cùng một mã
chấm điểm trên cả hai gói rồi so điểm — phải làm từ CI, không làm được từ
máy cá nhân. **Việc này rẻ và nên làm trước khi viết lại điều kiện.**

### Đề xuất: điều khoản sửa đổi có kiểm soát

Nguyên tắc "viết quy tắc dừng TRƯỚC khi có dữ liệu" bảo vệ trước một thứ:
chọn ngưỡng theo kết quả. Nó KHÔNG dự liệu tình huống chính hệ đo lường tiến
bộ và làm tiền đề của quy tắc sụp đổ. Đề xuất bổ sung:

> Một quy tắc dừng được phép viết lại khi — và chỉ khi — cả ba đồng thời đúng:
> 1. **Tiền đề của nó bị bác bỏ bằng một phép đo mới**, không phải kết quả ra xấu;
> 2. **Chưa có một điểm dữ liệu kết quả nào** thuộc loại quy tắc đang chờ;
> 3. **Bản cũ, bản mới và lý do đổi đều được ghi lại.**

Tính tới 28/08/2026 cả ba đều thoả (0 lệnh tiến-về-trước). **Sau 09:00 thứ
Hai 31/08, điều kiện 2 vĩnh viễn không còn thoả** — phiên quét tự động đầu
tiên có chi phí thực thi sẽ chạy, và từ đó mọi sửa đổi dù có lý đến đâu cũng
không chứng minh được nó không phải chọn quy tắc theo kết quả.

### Nếu viết lại, phải kèm hàng rào

Điểm mù sinh ra lỗi này — chỉ nghĩ về sai lầm loại I — sẽ lặp lại ở quy tắc
kế tiếp nếu chỉ sửa con số mà không sửa quy trình. Đề nghị:

- **Mọi ngưỡng dừng phải công bố lực phát hiện ở MỨC HIỆU ỨNG THỰC TẾ**, không
  chỉ ở mức thảm hoạ, và có test bắt buộc điều đó.
- **Mọi điều kiện an toàn phải có nơi HÀNH ĐỘNG**, không chỉ nơi in ra. Test
  phải chứng minh: điều kiện đạt ⇒ có thứ gì đó thay đổi trạng thái, không
  phải chỉ thêm một dòng chữ.

---

## CỔNG C5 ĐÃ ĐÓNG LẠI — VÀ VÌ SAO PHẢI ĐÓNG BẰNG TAY (29/08/2026)

Đọc sau mục "GỐC RỄ CỦA CỔNG C5" (28/08). Mục này sửa một khẳng định của
mục đó và ghi ba chỗ hỏng mới cùng họ.

### Sổ thật không nằm ở máy này

Mọi con số ngày 28/08 đo trên `paper_trades.db` ở máy cá nhân. **File đó
đứng yên từ 20/08/2026.** Sổ thật nằm trên Google Sheets: `run_daily.py`
kéo về đầu mỗi lượt và đẩy lên ở cuối. Kéo về ngày 29/08 (bản sao trong
thư mục tạm, không đụng file gốc):

```
Sheet : 117 lệnh · 15.714 quyết định
Máy   : 113 lệnh · 13.589 quyết định   <- ảnh chụp 20/08, đã cũ 9 ngày
```

Sửa lại: **"0 lệnh tiến-về-trước" đúng với ảnh chụp 20/08, SAI với sản
xuất.** Bài học lặp lại lần thứ n: đo trạng thái sống bằng một bản sao
chết thì con số ra đúng cú pháp và sai sự thật.

### Bốn lệnh tiến-về-trước đầu tiên của dự án

| # | Mã | Điểm | Tín hiệu | Ghi lúc | Trạng thái |
|---|---|---|---|---|---|
| 114 | NAF | 62 | 2026-08-28 | 28/08 21:13 | PENDING |
| 115 | STB | 65 | 2026-08-28 | 28/08 21:13 | PENDING |
| 116 | TCB | 63 | 2026-08-28 | 28/08 21:14 | PENDING |
| 117 | HUT | 65 | 2026-08-28 | 28/08 21:16 | PENDING |

Lượt quét 28/08 21:13 là lượt **đầu tiên chạy ngưỡng 62** trên đường tự
động. Mọi lượt trước (26/08 → 28/08 00:17) đều bị `LY_DO_C5` chặn ở
ngưỡng 50 — mã cũ. Lượt đầu tiên chạy mã mới mở 4 lệnh ngay lập tức.

Lượt kế (29/08 01:10) quét 67/71 mã, điểm cao nhất 60, không mở thêm. Bốn
mã vắng mặt đúng là bốn mã đang có lệnh chờ — chúng bị bỏ qua TRƯỚC khi
ghi quyết định, nên không để lại dòng lý do nào. Chỗ mù nhỏ, cùng họ với
"0 lệnh phải nói được vì sao".

### Ba chỗ hỏng mới, cùng một họ với nguyên nhân 4

1. **Điều kiện không nhìn thấy lệnh chưa đóng.** `dieu_kien_dong_lai()`
   báo `0/60` trong khi sổ đã có 4 lệnh cam kết. Nó lọc
   `status == "CLOSED"`, nên PENDING và OPEN vô hình với chính phép kiểm
   sinh ra để canh chúng.

2. **Đóng cổng KHÔNG huỷ lệnh chờ.** `fill_pending()` khớp bằng giá mở
   cửa phiên sau và không hề đọc `CHO_PHEP_MO_LENH_MOI`. Bốn lệnh trên
   VẪN khớp sáng 31/08. Đã chọn giữ chúng làm điểm dữ liệu tiến-về-trước
   đầu tiên; cờ chỉ chặn lệnh MỚI.

3. **Báo cáo phiên nói ngược với việc nó vừa làm.** Template trong
   `run_daily.py` viết cứng `⛔ DỪNG mở vị thế mới (ô C5)`. Đúng lúc viết
   (20/08), sai từ 24/08. Lượt 28/08 21:13 **mở 4 lệnh** và báo cáo của
   chính lượt đó nói đang dừng mở vị thế mới — suốt 5 ngày không ai đọc
   ra điều ngược lại từ báo cáo.

### Hai tin tốt cho phương án sửa

- **Mắt xích 5 (alpha) chắc hơn tưởng.** `backtest/cache/` bị gitignore
  nên runner luôn sạch và tải VN-INDEX mới mỗi lượt → rổ chuẩn trên
  đường sản xuất luôn tươi. (Cache ở máy cá nhân cũ tới 2026-08-20, trễ
  6 phiên, `market_filter.status()` báo cổng C1 cục bộ **không dùng
  được** — phải làm mới trước khi đo lại ở đây.)

- **Chỗ tối đo được ngay, không cần dựng job CI.** Bảng `decisions` lưu
  đủ từng thành phần điểm kèm `signal_date`. Sản xuất chạy gói vnstock
  miễn phí; chấm lại 71 mã với `signal_date = 2026-08-28` ở máy (gói tài
  trợ) rồi so từng thành phần là xong phép đo. Trong dữ liệu sản xuất
  ngày 28/08 đã thấy: `momentum_score = 62,5` (backtest luôn 50 — tức 4
  agent "sống dậy" đúng như giả thiết mở cổng), và `tv_bonus = 0` (tức
  TradingView vẫn đóng góp 0 kể cả khi chạy thật).

### Đã làm ngày 29/08

- `paper_trading.CHO_PHEP_MO_LENH_MOI = False` — đóng **bằng tay**,
  không phải do điều kiện kích hoạt. Kèm khối ghi chú nêu rõ ba lý do và
  ba việc phải xong trước khi mở lại.
- `LY_DO_C5` viết lại. Bản cũ nói "chờ Phase 5D chọn ngưỡng bằng
  walk-forward hợp lệ" — sai từ 24/08, vì ngưỡng 62 CHÍNH LÀ kết quả của
  Phase 5D. Một lý do sai ghi vào 13.589 dòng quyết định thì mọi lần đọc
  lại sổ về sau đều đọc nhầm.
- `run_daily.trang_thai_c5()` — trạng thái C5 in ra báo cáo nay SUY RA từ
  cờ. Tách ra mức module vì một chuỗi nằm giữa hàm quét 300 dòng cần cả
  mạng lẫn sổ lệnh mới chạm tới được, tức là không test được, tức là lại
  một câu chữ không ai canh.
- `tests/test_c5_noi_that.py` — 7 test, ba tầng khoá: hàm trả đúng hai
  nhánh · template không chứa hằng chuỗi tự khẳng định C5 · template có
  nội suy đúng hai biến. Thêm một test đọc AST `paper_trading.py` để
  khẳng định cờ đang `False` **trong mã nguồn** (không đọc giá trị lúc
  chạy: vài file test gán cờ ở mức module và rò sang mọi test sau).
  Đột biến 4/4 đỏ.

### Bước 1 ĐÃ XONG — điều kiện dừng nay có nơi HÀNH ĐỘNG

`run_daily.thi_hanh_dieu_kien_dung(trades, dat_co)` chạy ngay sau khi mở
sổ và **trước** vòng quét. Đạt điều kiện thì nó TẮT `CHO_PHEP_MO_LENH_MOI`
cho lượt đó — mọi mã sau đó nhận `LY_DO_C5` và không mã nào vào lệnh. Đây
là lần đầu điều kiện đổi được một **trạng thái** thay vì thêm một dòng chữ.

Bốn thứ nó KHÔNG làm, ghi thẳng trong docstring, vì một hàng rào bị tưởng
nhầm phạm vi còn tệ hơn không có hàng rào:

1. không huỷ lệnh PENDING — `fill_pending()` không đọc cờ này;
2. không đóng vị thế đang mở — dừng MỞ THÊM khác với thoát hàng;
3. **không phải chốt một cửa.** Cờ chỉ sống trong tiến trình đó; lượt sau
   tính lại từ đầu. Kho ngoài chỉ có hai bảng `trades` và `decisions` —
   không có chỗ nào ghi được một lá cờ sống qua nhiều lượt chạy trên
   nhiều runner. Chốt bền duy nhất vẫn là dòng `CHO_PHEP_MO_LENH_MOI =
   False` trong MÃ NGUỒN, do người sửa, khoá bởi `test_c5_noi_that.py`;
4. **không làm đỏ lượt quét.**

Điểm 4 là một cái bẫy suýt sập vào. `tools/chuong_bao_quet.py` đếm lượt
`conclusion == "success"` của workflow "Quét sổ lệnh" để biết một ngày có
được quét không. Làm đỏ workflow đó vì cổng C5 sẽ sinh ra báo động giả
"ngày này không có lượt quét nào" — báo động giả sinh ra từ một cảnh báo
thật, che mất đúng thứ chuông kia sinh ra để canh. `quet-so-lenh.yml` đã
ghi nguyên văn cảnh báo này cho bước cảnh báo nội phiên; đây là cùng cái
bẫy, ở chỗ khác.

Nên chuông C5 tách riêng: `tools/canh_cong_c5.py` +
`.github/workflows/canh-cong-c5.yml`, chạy 09:30 UTC (16:30 ICT) các ngày
làm việc. Nó kêu **chỉ khi có việc chưa ai làm** — điều kiện đạt VÀ cổng
vẫn mở trong mã nguồn. Điều kiện đạt mà cổng đã đóng là trạng thái ĐÚNG;
kêu lúc đó là dạy người ta bỏ qua chuông. Kéo sổ hỏng thì cũng kêu: một
cái chuông im lặng vì không nhìn thấy gì còn tệ hơn không có chuông, vì
nó tạo cảm giác đang được canh.

Khoá bởi `tests/test_thi_hanh_dieu_kien_dung.py` — 10 test, **đột biến
7/7 đỏ**, trong đó có một đột biến dời khối thi hành xuống SAU vòng quét
(muộn đúng một phiên — phiên đáng lẽ không được có) và một đột biến thay
hàm đặt cờ bằng hàm rỗng.

### Còn lại — thứ tự làm

1. **Đo chỗ tối** — chấm lại 71 mã `signal_date = 2026-08-28`, so với
   `decisions` của lượt 21:13. Làm mới cache VN-INDEX trước.
2. **Viết lại điều kiện theo alpha** (nguyên nhân 1+2+3), ngưỡng suy từ
   lực phát hiện ở mức hiệu ứng thật, định giá cả sai lầm loại II, và
   đếm cả lệnh PENDING/OPEN vào phần đã cam kết.
3. **Hàng rào quy trình** — test buộc mọi ngưỡng dừng công bố lực phát
   hiện ở mức hiệu ứng thực tế, và buộc mọi điều kiện an toàn có nơi
   hành động.

---

## BƯỚC 2 — ĐO CHỖ TỐI. GÓI VNSTOCK KHÔNG PHẢI VẤN ĐỀ; CỬA SỔ DỮ LIỆU MỚI LÀ
## (29/08/2026)

Đo trên **cả 71 mã**, cùng một thời điểm, dữ liệu tới hết phiên 2026-08-28.
Ba đường chấm điểm, tách riêng từng hiệu ứng:

```
A — đường QUÉT TỰ ĐỘNG   run_daily.py:263  60 ngày lịch  ->  44 phiên
C — cùng mã, cửa sổ dài   420 ngày lịch                  -> 301 phiên
B — đường ỨNG DỤNG        app.py + DataOrchestrator (TradingView THẬT)
```

### Kết quả — ba phép so, ba kết luận khác hẳn nhau

| Phép so | Lệch TB | \|Lệch\| TB | Lớn nhất | ≥5 điểm | **ĐỔI QUYẾT ĐỊNH** |
|---|---|---|---|---|---|
| Gói vnstock (miễn phí → tài trợ) | −0,19 | 0,46 | −5 | 1/67 | **0/67** |
| TradingView (C → B) | +0,25 | 0,59 | +8 | 1/71 | **0/71** |
| **Cửa sổ dữ liệu (A → C)** | **−3,10** | **5,86** | **−16** | **32/71** | **6/71** |

**Chỗ tối nghi ngờ hôm 28/08 — gói vnstock — đã đo và KHÔNG phải vấn đề.**
Điểm sản xuất (CI, gói miễn phí) so với điểm máy này (gói tài trợ), cùng cửa
sổ 60 ngày: lệch trung bình 0,46 điểm, **không mã nào đổi quyết định**. Khớp
với `requirements.txt`: khác biệt của hạng gói là số kỳ BCTC (8 vs không
giới hạn) và hạn mức request — mà `TRONG_SO_CO_BAN = 0.0` nên BCTC đóng góp 0.

**TradingView cũng không phải vấn đề.** 0/71 mã đổi quyết định. Lý do:
`DataOrchestrator.collect_and_handoff()` GHI ĐÈ `tv_indicators` bằng chỉ báo
tự tính từ OHLCV, và bỏ hẳn chỉ báo TradingView mang đơn vị giá. Thứ duy
nhất còn lại của TradingView là `tv_recommendation` → `tv_bonus` (±4, ±8), và
59/71 mã hôm đó là NEUTRAL nên bonus bằng 0.

### Cửa sổ dữ liệu: sáu mã đổi quyết định, ba trong số đó ĐÃ THÀNH LỆNH

```
HHP   54 -> 66   KHÔNG MUA -> MUA
MSR   53 -> 67   KHÔNG MUA -> MUA
HDB   56 -> 65   KHÔNG MUA -> MUA
NAF   62 -> 61   MUA -> KHÔNG MUA      <- lệnh #114, PENDING
TCB   63 -> 60   MUA -> KHÔNG MUA      <- lệnh #116, PENDING
HUT   65 -> 53   MUA -> KHÔNG MUA      <- lệnh #117, PENDING
```

**Ba trong bốn lệnh tiến-về-trước đầu tiên chỉ tồn tại vì cửa sổ 44 phiên.**
Chỉ STB sống sót, và nó còn mạnh lên (65 → 76).

### Cơ chế — cửa sổ ngắn làm liệt agent xu hướng

Bóc từng thành phần bảy mã trên:

| Mã | `trend_score` A→C | `risk_score` A→C | điểm cuối |
|---|---|---|---|
| STB | 65 → **100** | 50 → 40 | +11 |
| HHP | 65 → **100** | 55 → 50 | +12 |
| MSR | 65 → **100** | 50 → 30 | +14 |
| HDB | 65 → **100** | 75 → 40 | +9 |
| HUT | 50 → **15** | 45 → **10** | −12 |
| TCB | 65 → 60 | 25 → 15 | −3 |
| NAF | 65 → 70 | 50 → 50 | −1 |

`momentum_score` và `volume_score` **không đổi một mã nào** — chúng chỉ cần
cửa sổ ngắn. Toàn bộ chênh lệch đến từ `trend` và `risk`.

Nguyên nhân trực tiếp: `DataOrchestrator._compute_local_indicators()` trả
`None` cho `SMA50` khi dưới 50 phiên và `SMA200` khi dưới 200 phiên. Với 44
phiên, cả hai đều `None`, nên các luật của agent xu hướng dùng chúng bị bỏ
qua — `trend_score` kẹt trong dải 35/50/65 và **không bao giờ chạm 100 hay
15**. Agent rủi ro thì tính biến động, drawdown, Sharpe trên 44 phiên thay
vì 301.

Đây cũng là lời giải cho một kết luận cũ: `MO-XE-KIEN-TRUC.md` ghi
*"trend — 3 giá trị — công tắc 3 nấc"*. **Đó chưa bao giờ là tính chất của
mã nguồn. Đó là tính chất của CỬA SỔ.** Cho đủ lịch sử thì agent xu hướng
trải từ 15 tới 100.

### Vì sao điều này nghiêm trọng hơn cả bốn nguyên nhân của cổng C5

Ngưỡng 62 do Phase 5D chọn bằng walk-forward. `walkforward.py:213` gọi
`run_session(so, sym, df.iloc[: t + 1], ...)` — **cửa sổ MỞ RỘNG**, bắt đầu
từ `min_history = 60` phiên rồi lớn dần tới hết cache (2020–2022 trở đi sau
khi `extend_history` chạy). Tức ngưỡng 62 được hiệu chuẩn trên phân phối
điểm của cửa sổ DÀI.

`run_daily.py:263` cho cửa sổ **60 ngày lịch, cố định — 44 phiên**.

> **Ngưỡng đang chạy trong sản xuất được hiệu chuẩn cho một phân phối điểm
> khác với phân phối điểm mà nó đang được áp lên.**

Không ai chọn điều đó. `start_date = now - 60 days` là một dòng viết cho tốc
độ, và nó âm thầm quyết định luật chấm điểm nào được phép chạy. Đúng mẫu
"núm vặn giả" — chỉ khác là núm này CÓ tác dụng, tác dụng lớn nhất hệ thống,
và không được ghi ở đâu.

### Chưa đo — phải kiểm sau khi đổi

1. **Gói miễn phí có phục vụ nổi 420 ngày OHLCV không.** Bằng chứng gián
   tiếp: CI đang kéo VN-INDEX từ 2020-01-01 (1.655 phiên) mỗi lượt và cổng
   C1 sống, nên OHLCV dài không bị chặn theo hạng. Nhưng chỉ số khác cổ
   phiếu — phải so điểm sản xuất với điểm máy sau lượt quét đầu tiên.
2. **`tv_recommendation` không tái lập.** Hai lần chạy cách nhau chưa tới
   một giờ, thị trường ĐÃ ĐÓNG, MSR đổi từ `STRONG_BUY` sang `NEUTRAL`
   (điểm B 75 → 67). Bất biến 2 nói chấm cùng một gói dữ liệu hai lần phải
   ra cùng một điểm. Với `tv_bonus` thì không. Hiện vô hại vì bonus không
   đổi quyết định mã nào, nhưng phải ghi.
3. Phép đo này là **một ngày, 71 mã**. Con số 6/71 là ảnh chụp, không phải
   tỷ lệ ổn định.

### Chốt con số: 1095 ngày, và cái giá của nó

Đo tiếp trên cùng 71 mã, ba lát cắt từ **một** lần tải mỗi mã. Ba mã
(GVR, PNJ, ACV) rơi vào dữ liệu mô phỏng trong lượt đó — đã loại, còn 68:

| Bước | \|lệch\| TB | ≥5 điểm | **Đổi quyết định** |
|---|---|---|---|
| 44 → 288 phiên (60 → 420 ngày) | 5,51 | 29/68 | **6/68** |
| 288 → 747 phiên (420 → 1095 ngày) | 1,97 | 10/68 | **1/68** |

Sáu mã đổi ở bước đầu **trùng khớp hoàn toàn** với lượt đo độc lập trước
đó (HHP, MSR, NAF, TCB, HDB, HUT). Hai lượt riêng biệt cho cùng kết quả —
điểm chấm tái lập được.

Bước thứ hai nhỏ hơn nhiều nhưng không bằng 0: TCB 60 → **62**, tức nó đi
qua ngưỡng theo chiều ngược lại. Cũng vì thế mà chọn 1095 chứ không dừng ở
420: ngưỡng 62 được hiệu chuẩn trên cửa sổ MỞ RỘNG của walk-forward, nên
điểm phải sinh ra từ một cửa sổ gần với nó nhất có thể.

**Giá phải trả, đo thật (tải + chấm, 8 mã):**

```
 420 ngày (301 phiên)  ->  2,35 s/mã  ->  71 mã ≈  4,0 phút
1095 ngày (747 phiên)  ->  8,88 s/mã  ->  71 mã ≈ 11,7 phút
```

Chấm điểm chỉ tốn 0,02–0,03 s/mã — toàn bộ chi phí nằm ở tải dữ liệu. Vì
thế `quet-so-lenh.yml` nới `timeout-minutes` từ **25 lên 40**: 25 phút cho
cả sáu bước với cửa sổ 1095 là quá sát.
`tests/test_cua_so_du_lieu_quet.py` khoá cặp này lại — cửa sổ ≥1000 ngày mà
timeout <40 phút thì test đỏ.

**Phải kiểm sau lượt quét đầu tiên:** thời gian chạy thật trên runner của
GitHub (chậm hơn máy cá nhân), và số phiên mà gói MIỄN PHÍ trả về cho
1095 ngày. Nếu CI chỉ nhận được ít phiên hơn thì cửa sổ dài chỉ là danh
nghĩa — so `decisions.components` của lượt đó với điểm chấm ở máy.

### Một cái bẫy gặp phải khi đo — và chỗ mã nguồn ĐÃ chặn nó

Ba mã cho điểm khác nhau giữa hai lượt đo (ACV 58 vs 48, PNJ 56 vs 59,
GVR 57 vs 54). Nghi ngờ đầu tiên là điểm chấm không tái lập — **sai**.

Nguyên nhân: `VNStockCollectorAgent.collect()` thử `vci` rồi `kbs`; hỏng cả
hai thì trả `_generate_fallback_df()` — **một chuỗi random walk** — kèm
`status="SYNTHETIC"`. Hôm đó mạng có nhiều `Read timed out`, ba mã rơi vào
nhánh đó, và **kịch bản đo của tôi không kiểm `status`** nên đã chấm điểm
trên giá bịa. Dấu vết nhận ra được: chúng có 783 phiên trong 1095 ngày —
đúng số ngày làm việc (`freq='B'`), không phải số phiên giao dịch thật (747).

`run_daily.py:285` thì CÓ chặn: `if res.get("status") != "OK": ... break`,
đếm vào `bo_qua` và bỏ mã đó. **Đường sản xuất không bao giờ chấm trên dữ
liệu mô phỏng.** Lỗi nằm ở công cụ đo, không ở hệ thống.

Cũng đã kiểm và loại một nghi ngờ khác: `vci` trả 301 phiên cho cửa sổ 420
ngày còn `kbs` trả 288 — chênh 13 dòng, nhưng đó là do `vci` trả sớm hơn
ngày yêu cầu, không phải dòng trùng. Giá khớp nhau tới từng chữ số và
**điểm chấm từ hai nguồn giống hệt nhau** trên cả 5 mã thử.

### CI đỏ ngay lượt đầu — và cái guard lẽ ra phải bắt được

Lượt kiểm định đầu tiên của thay đổi này ĐỎ, chặn merge:

```
FAILED tests/test_cua_so_du_lieu_quet.py::test_cua_so_dai_thi_workflow…
        ModuleNotFoundError: No module named 'yaml'
```

Test mới đọc `timeout-minutes` bằng `import yaml`. Xanh ở máy vì streamlit
kéo theo PyYAML; đỏ trên runner sạch vì `kiem-dinh.yml` chỉ cài
`requirements.txt` cộng `pytest`, và **PyYAML không nằm trong đó**.

Đã có sẵn một guard cho đúng loại lỗi này — `tests/test_requirements.py` —
nhưng nó tự giới hạn phạm vi, ghi rõ trong docstring:

> *"Phạm vi: chỉ file .py ở GỐC dự án. tests/ và tools/ không nằm trong
> đường chạy của Actions."*

**Tiền đề đó sai.** Cả ba workflow đều chạy mã trong hai thư mục ấy:
`kiem-dinh.yml` chạy `pytest tests/` và `tools/chan_bia_so_lieu.py`;
`chuong-bao-quet.yml` chạy `tools/chuong_bao_quet.py`;
`canh-cong-c5.yml` chạy `tools/canh_cong_c5.py`.

Đã sửa cả hai đầu:

- Test đọc `timeout-minutes` bằng tay, không thêm phụ thuộc nào. Đưa một
  thư viện vào `requirements.txt` chỉ để test đọc một con số là trả giá ở
  đường chạy sản xuất cho tiện lợi của test.
- `test_requirements.py` thêm phép kiểm phủ `tests/` và `tools/`, ngoại lệ
  duy nhất là `pytest` (CI cài riêng). Đột biến: thêm lại `import yaml` vào
  một test → guard ĐỎ.

Cùng một hình dạng với nguyên nhân 4 của cổng C5: **một luật có ghi phạm vi
hẹp, phạm vi ấy hết đúng, và không có gì báo khi nó hết đúng.**

---

## BƯỚC 3 — ĐIỀU KIỆN DỪNG BẢN 2: ĐO BẰNG ALPHA (29/08/2026)

### Bản cũ, ghi lại nguyên văn để đối chiếu

```
TOI_THIEU_LENH_DE_DONG = 60
đóng ⟺ ≥60 lệnh tiến-về-trước ĐÃ ĐÓNG  và  cận trên KTC 95% của KỲ VỌNG < 0
```

Điều khoản sửa đổi đòi ba điều cùng đúng mới được viết lại: tiền đề bị bác
bỏ bằng một **phép đo mới** (không phải vì kết quả ra xấu), **chưa có điểm
dữ liệu kết quả nào** thuộc loại quy tắc đang chờ, và **bản cũ, bản mới, lý
do đổi đều được ghi**. Ngày 29/08/2026 cả ba thoả: bốn lệnh tiến-về-trước
đầu tiên còn PENDING, chưa lệnh nào đóng.

### Bản mới

```
n < 150              chưa đủ để kết luận
150 ≤ n < 596        ĐÓNG nếu cận TRÊN của KTC (z=2,30) < 0        [biên HẠI]
n ≥ 596              ĐÓNG TRỪ KHI cận DƯỚI của KTC (z=1,96) > 0    [đảo gánh
                     nặng chứng minh, sau khi đã đủ cỡ mẫu nêu trước]
```

`n` là số lệnh tiến-về-trước **đã đóng và khớp được cặp ngày với rổ chuẩn
VN-INDEX**. Thiếu rổ chuẩn thì điều kiện **không kết luận gì** và nói ra
điều đó — không lặng lẽ quay về kỳ vọng.

### Bốn hằng số, và vì sao chúng có giá trị đó

| Hằng số | Giá trị | Suy từ đâu |
|---|---|---|
| `SIGMA_ALPHA` | 8,075%/lệnh | KTC của phép đo OOS n=385: nửa độ rộng 0,8065 → SE 0,4115 → σ = 0,4115·√385 |
| `MUC_BAT_LOI` | −0,927%/lệnh | mức bất lợi **đo được** ngoài mẫu khi bật chi phí thực thi |
| `N_DAY_DU` | 596 | `co_mau_cho_luc()` — 80% lực phát hiện ở `MUC_BAT_LOI`, hai phía 5% |
| `N_TOI_THIEU` | 150 | ≈25% thông tin của `N_DAY_DU` |

`N_DAY_DU` **không được gõ tay**: `co_mau_cho_luc()` tính ra nó và một test
bắt hai bên phải khớp. Đây chính là chỗ bản 1 sai — nó chọn 60 từ một ước
lượng σ ≈ 10% cho một mục tiêu (−2,5%) không phải mức hiệu ứng thực tế.

`docs` từng ghi 595; con số đúng khi làm tròn LÊN là 596. Chênh một lệnh,
không đổi đặc tính, nhưng mã phải khớp chính công thức của nó.

### Vì sao hai giá trị z khác nhau

Biên HẠI được đánh giá **liên tục** — mỗi lượt quét, tới 12 lượt một ngày.
Nhìn nhiều lần ở cùng một mức thì xác suất chạm biên do nhiễu cộng dồn.
Mô phỏng 40.000 lần, đánh giá ở MỌI n từ 150:

```
z = 1,96  ->  sai lầm loại I 11,7%
z = 2,30  ->                  5,8%     <- chọn
z = 2,50  ->                  3,7%
```

Mốc `N_DAY_DU` thì là **một** phép kiểm tại một điểm, không nhìn lặp, nên
giữ z = 1,96.

### Đặc tính đo được (40.000 lần mô phỏng, σ = 8,075%)

| μ thật | ĐÓNG | vì hại | vì chưa chứng minh | n trung bình |
|---|---|---|---|---|
| −2,000% | 100,0% | 100,0% | 0,0% | 161 |
| −0,927% | 100,0% | 81,1% | 18,9% | 335 |
| −0,500% | 100,0% | 39,1% | 60,9% | 482 |
| 0,000% | 99,6% | **5,8%** | 93,8% | 580 |
| +0,500% | 79,7% | 0,4% | 79,3% | 686 |
| +0,927% | 27,6% | 0,0% | 27,6% | 890 |
| +2,000% | **0,0%** | 0,0% | 0,0% | 995 |

Hai dòng khó chịu nhất, đọc cho đúng:

- **μ = 0 → đóng 99,6%.** Đúng ý đồ. Bản 1 sẽ chạy vô hạn ở dòng này vì nó
  chỉ biết đóng khi có HẠI đo được. Đây là chỗ sai lầm loại II được định giá.
- **μ = +0,5% → đóng 79,7%.** Một lợi thế THẬT nhưng nhỏ hơn mức thiết kế
  (±0,927%) cần ~2.050 lệnh mới phân biệt được với 0. Dự án không chạy đủ
  dài cho mức đó, nên nó chọn dừng thay vì chạy tiếp bằng hy vọng. Đây là
  một lựa chọn **được nêu ra**, không phải một điểm mù.

### Bốn nguyên nhân — trạng thái sau bước 3

| # | Nguyên nhân | Trạng thái |
|---|---|---|
| 1 | Hiệu chuẩn theo thảm hoạ, không theo bất lợi | ✅ ngưỡng suy từ `co_mau_cho_luc()` ở `MUC_BAT_LOI` |
| 2 | Chỉ định giá sai lầm loại I | ✅ biên đảo gánh nặng tại `N_DAY_DU` |
| 3 | Đo sai đại lượng (kỳ vọng thay vì alpha) | ✅ `vs_benchmark`, và AST cấm gọi lại `expectancy_significant` |
| 4 | Không có ai thi hành | ✅ đã sửa ở bước 1 (28/08) |

Thêm một lỗi phát hiện trong lúc sửa: bản 1 **đếm mù lệnh chưa đóng** — ngày
29/08 sổ có 4 lệnh PENDING mà nó báo "0/60". Bản 2 đếm và nói ra
(`n_cam_ket`), và trả cờ `do_duoc` để người gọi phân biệt "chưa tới ngưỡng"
với "không đo được" mà không phải so chuỗi.

Chuông `tools/canh_cong_c5.py` nay **kêu khi không đo được**. Một cái chuông
im lặng vì không nhìn thấy gì thì tệ hơn không có chuông.

### Kiểm định

`tests/test_dieu_kien_dung_alpha.py` — 14 test. Đột biến **8/8 đỏ**: quay về
đo kỳ vọng · bỏ biên đảo gánh nặng · biên hại không nới rộng · ngưỡng gõ tay
· thiếu rổ chuẩn vẫn kết luận · bỏ đếm lệnh đã cam kết · hàm đặt cờ rỗng ·
tắt cờ cả khi chưa đạt.

---

## BƯỚC 4 — HÀNG RÀO QUY TRÌNH (29/08/2026)

Sửa riêng cổng C5 thì lần sau một điều kiện khác sẽ hỏng y hệt. Hai điểm
mù sinh ra nó là điểm mù của **quy trình**, không của một hàm:

- **Ngưỡng chọn bằng trực giác.** Bản 1 hiệu chuẩn để bắt −2,5%/lệnh
  trong khi mức bất lợi thật là −0,927%.
- **Điều kiện không có nơi hành động.** Bản 1 chỉ được gọi trong
  `report()`, một hàm nối chuỗi.

`tests/test_hang_rao_quy_trinh.py` rào cả hai bằng **một sổ đăng ký**:

```python
DIEU_KIEN_AN_TOAN = {
    "dieu_kien_dong_lai": {
        "module": pm,
        "thi_hanh": rd.thi_hanh_dieu_kien_dung,
        "co": (pt, "CHO_PHEP_MO_LENH_MOI"),
        "nguong": "N_DAY_DU",
        "luc": (pm.MUC_BAT_LOI, pm.SIGMA_ALPHA),
    },
}
```

Tám phép kiểm, chia ba nhóm:

**Không điều kiện nào được nằm ngoài sổ.** Quét AST ba file ảnh hưởng kết
quả tìm mọi hàm `dieu_kien_*`; thấy một hàm chưa khai → đỏ. Khai nó thì
buộc phải nói ra nơi thi hành và ngưỡng — không khai được nửa vời.

**Ngưỡng phải SUY TỪ lực phát hiện.** Với mỗi điều kiện, ngưỡng phải bằng
`co_mau_cho_luc(mức, σ)`. Và mức hiệu ứng phải là một **hằng số có tên** ở
mức module, không phải một con số rời trong công thức — đặt tên cho một giả
định là bước đầu để ai đó cãi nó.

**Điều kiện đạt thì trạng thái phải ĐỔI THẬT.** Chạy thật, không đọc mã:
dựng một sổ lệnh chắc chắn đạt, gọi hàm thi hành, rồi kiểm lá cờ đã đổi
`True → False`. Kèm hai vế ngược: chưa đạt thì KHÔNG được đụng vào trạng
thái (một hàng rào tự sập khi chưa cần thì sớm muộn bị gỡ), và điều kiện
phải có nơi thi hành NGOÀI `report()`.

**Và lực phát hiện phải được ĐO, không chỉ công bố.** Hai phép kiểm mô
phỏng đúng cách mã đánh giá — liên tục, mỗi lượt quét — bằng chính các hằng
số mã đang dùng: lực ≥70% ở `MUC_BAT_LOI`, sai lầm loại I ≤10%. Một phép
kiểm nữa đo loại I của z=1,96 để chứng minh vì sao phải nới lên 2,30; nếu
con số đó thay đổi thì chú thích trong mã cũng phải viết lại.

### Đột biến 7/7 đỏ

```
thêm một điều kiện an toàn mà không khai      -> đỏ
ngưỡng gõ tay (596 -> 400)                    -> đỏ
hiệu chuẩn cho mức thảm hoạ (−0,927 -> −2,5)  -> đỏ
điều kiện đạt nhưng không đổi trạng thái      -> đỏ
đụng vào trạng thái kể cả khi chưa đạt        -> đỏ
biên hại không nới rộng dù nhìn liên tục      -> đỏ
chỉ còn report() gọi điều kiện                -> đỏ
```

Đột biến thứ ba đáng chú ý: nó tái tạo **đúng** nguyên nhân 1 của cổng C5 —
hiệu chuẩn cho thảm hoạ thay vì cho bất lợi thực tế. Từ nay lỗi đó không
thể vào repo mà không làm đỏ CI.

### Bốn nguyên nhân — trạng thái cuối

| # | Nguyên nhân | Sửa ở |
|---|---|---|
| 1 | Hiệu chuẩn theo thảm hoạ | bước 3 · rào ở bước 4 |
| 2 | Chỉ định giá sai lầm loại I | bước 3 · rào ở bước 4 |
| 3 | Đo sai đại lượng (kỳ vọng ≠ alpha) | bước 3 |
| 4 | Không có ai thi hành | bước 1 · rào ở bước 4 |

Thêm hai lỗi tìm ra trong lúc sửa, đều đã vá và đều đã rào: báo cáo phiên
viết cứng trạng thái cổng (bước 1), và cửa sổ dữ liệu 44 phiên khiến ngưỡng
62 được áp lên một phân phối điểm khác với phân phối đã hiệu chuẩn nó
(bước 2).


---

## BƯỚC 5 — DỰNG ĐỒ ĐO TRƯỚC LƯỢT CHẠY THẬT ĐẦU TIÊN (31/08/2026)

Bốn bước trên sửa cổng C5 vào cuối tuần, khi không có phiên nào chạy. Thứ
Hai 31/08 là **ngày đầu tiên toàn bộ thay đổi gặp thị trường thật**, và
cũng là ngày bốn lệnh chờ đầu tiên khớp. Trước khi nó chạy, dựng đồ đo.

### Trạng thái đã chốt lúc 08:15, TRƯỚC lượt quét đầu tiên

```
sổ thật (Google Sheets) : 117 lệnh · 15.714 quyết định
bốn lệnh chờ            : NAF 62 · STB 65 · TCB 63 · HUT 65 — tín hiệu
                          2026-08-28, còn PENDING, chưa lệnh nào khớp
quyết định hôm nay      : 0 (chưa có lượt quét nào)
cờ trong mã nguồn       : CHO_PHEP_MO_LENH_MOI = False
đối chiếu rò rỉ         : 0 quyết định vào lệnh kể từ 29/08 trên 15.714 dòng
điều kiện dừng          : 0/150 lệnh có đối chiếu — chưa đủ để kết luận
```

Có mốc "trước" thì sau mới nói được cái gì đã đổi. Không có nó thì mọi
quan sát chiều nay đều là một con số không có gốc so.

### Nhịp cron GitHub đã xấu đi hẳn — đo lại trên 30 lượt gần nhất

`CLAUDE.md` ghi "6/12 nhịp mỗi ngày = 50%, trễ điển hình 5→90 phút" (đo
13→21/08). Đo lại 31/08, giờ đã quy về ICT:

| Ngày | Số lượt | Giờ chạy (ICT) |
|---|---|---|
| 24 · 25 · 26/08 | 6 mỗi ngày | 10:10 → 15:43, rải đều trong phiên |
| **27/08** | **2** | **19:38 · 00:16 (hôm sau)** |
| **28/08** | **2** | **21:12 · 01:08 (hôm sau)** |

Hai phiên gần nhất **không có lượt quét nào trong giờ giao dịch** — trễ
không còn tính bằng phút mà bằng 6–10 tiếng. Chuông `chuong_bao_quet.py`
KHÔNG kêu, và nó đúng: nó đếm "ngày đó có lượt quét thành công nào không",
mà cả hai ngày đều có.

Điều đang còn đúng: `evaluate_open()` chấm trên nến NGÀY, nên lượt sau
đóng cửa là lượt quyết định — hai ngày đó vẫn được quét đầy đủ, và bốn
lệnh chờ chính là sản phẩm của một lượt như vậy. Nhưng hệ quả cho việc
quan sát hôm nay phải nói thẳng: **không có gì bảo đảm lượt quét rơi vào
giờ ta đang nhìn.** Nút "Run workflow" của `quet-so-lenh.yml` là đường
chạy tay khi cần một lượt đúng lúc.

### Cửa sổ dữ liệu: `start` CÓ được tôn trọng — đo tại máy, hạng silver

Nghi ngờ ban đầu là nguồn trả về một số nến cố định bất kể khoảng xin.
Đo bốn cửa sổ trên FPT:

| Xin | Nhận | Phiên/ngày |
|---|---|---|
| 60 ngày | 45 phiên | 0,750 |
| 420 ngày | 303 phiên | 0,721 |
| 1095 ngày | **784 phiên** | 0,716 |
| 2200 ngày | 1573 phiên | 0,715 |

Nhất quán. Nguồn chỉ **đệm thêm ~5% ở đầu** (xin từ 2023-09-01, trả từ
2023-07-10), không cắt. Mười mã đo cùng lúc — gồm cả bốn mã đang PENDING
— đều đúng 784 phiên, 0 mã dưới mốc 50 phiên.

**Nhưng đó là hạng silver.** Con số của gói MIỄN PHÍ trên runner vẫn là
chỗ tối, đúng như `CLAUDE.md` ghi. Không có cách nào đo nó từ máy này.

### Dụng cụ 1 — mỗi lượt quét tự đo cửa sổ nó nhận được

`run_daily.phien_ky_vong()` + `bao_cua_so_du_lieu()`. Ba lựa chọn thiết kế:

**Kỳ vọng ĐO ĐƯỢC, không gõ tay.** Số phiên kỳ vọng lấy từ chính chuỗi
VN-INDEX kéo trên máy đang quét, đếm những phiên nằm trong cửa sổ. Một
công thức "52 tuần × 5 ngày trừ lễ" không biết runner hôm nay thấy gì;
chuỗi chỉ số thì biết, và nó tự đúng lại khi lịch nghỉ đổi. Dựng không
được thì trả `None` và NÓI RA — không đoán một con số thay thế, vì một kỳ
vọng bịa ra đẻ ra cảnh báo giả hoặc im lặng giả.

**Đi bằng `::notice::`.** Nhật ký chạy trả 403 cho người chưa đăng nhập;
annotation thì đọc được qua API công khai. Đã kiểm lại đường đó còn sống.
Cùng lý do đã ghi cho khối thi hành điều kiện dừng.

**Cảnh báo bằng `::warning::`, KHÔNG bằng mã thoát.** Làm đỏ lượt quét sẽ
khiến `chuong_bao_quet.py` báo giả "ngày này không có lượt quét nào" —
đúng cái bẫy đã ghi hai lần trong repo này.

Ngưỡng `TY_LE_PHIEN_TOI_THIEU = 0,80` và nó KHÔNG tinh tế: khoảng cần
phân biệt là 6% (44/747 phiên — cấu hình trước 29/08) so với ~100%.

### Dụng cụ 2 — cổng đóng phải CHỨNG MINH ĐƯỢC là nó chặn

`tools/canh_cong_c5.kiem_ro_ri()`. `kiem()` sẵn có hỏi "điều kiện đạt
chưa, cổng còn mở không" — cả hai vế đọc từ **mã nguồn**. Hàm mới hỏi câu
chỉ **dữ liệu** trả lời được: kể từ mốc đóng, đã có vị thế mới nào được mở
chưa. Đó là khác biệt giữa *đã khai là chặn* và *đã chặn*.

`acted = 1` là dấu hiệu đúng vì `record_decision` chỉ được gọi từ
`consider_entry`, và `fill_pending` KHÔNG ghi quyết định — nên bốn lệnh
chờ khớp sáng nay không làm chuông kêu oan. Một phép kiểm AST khoá đúng
tính chất đó lại, để ngày nào `fill_pending` đổi thì test đỏ TRƯỚC khi
chuông kêu oan trên sổ thật.

Ngày đóng cổng chuyển từ **chú thích** thành hằng số
`paper_trading.NGAY_DONG_CONG_C5` — một ngày nằm trong chú thích thì
không ai đối chiếu được.

### Đột biến 14/14 đỏ

```
DỤNG CỤ 1                                      DỤNG CỤ 2
không bao giờ cảnh báo            -> đỏ        không bao giờ báo rò rỉ        -> đỏ
ngưỡng tỷ lệ nới tới vô dụng      -> đỏ        bỏ qua mốc đóng cổng           -> đỏ
bịa kỳ vọng khi phép đo hỏng      -> đỏ        đối chiếu cả khi cổng đang MỞ  -> đỏ
gỡ dây: máy quét không gọi nữa    -> đỏ        kết quả không vào mã thoát     -> đỏ
cảnh báo làm ĐỎ lượt quét         -> đỏ        mốc quên múi giờ (lệch 7h)     -> đỏ
bỏ đếm số mã dưới mốc SMA50       -> đỏ        fill_pending ghi quyết định    -> đỏ
cảnh báo không nói ngưỡng nào     -> đỏ        mốc đóng đặt ở tương lai       -> đỏ
```

612 → 629 test xanh · Python 3.11 sạch · `chan_bia_so_lieu` 0 CHẶN.

Một gác CÓ SẴN đã bắt tôi trong lúc làm: `test_run_daily_khong_chep_cung_nguong_mua`
đỏ vì tôi viết số 62 vào một docstring của `run_daily.py`. Bốn lần "62"
khác trong file nằm trong chú thích `#` nên gác bỏ qua; docstring là chuỗi
thật nên nó bắt. Gác đúng, đã sửa thành "ngưỡng mua".

### Còn phải đọc sau lượt quét — hai câu hỏi, và cách đọc câu trả lời

**1. Gói miễn phí trả về bao nhiêu phiên?** Đọc annotation `::notice::`
của lượt quét. Trung vị ≈ 784 thì cửa sổ 1095 ngày là thật trên CI và
`docs/STATE.md` mục "BƯỚC 2" khép lại. Trung vị ≈ 44 thì `::warning::` sẽ
tự nổ, và ngưỡng mua đang chạy trên một phân phối khác — phải xử lý trước
mọi việc khác.

**2. Bước quét mất bao lâu?** Đọc `steps` của job qua API công khai —
bước "Quét thị trường và cập nhật sổ lệnh". Nền ở cửa sổ 60 ngày: 318
giây (28/08). Đo tại máy ở 1095 ngày: 8,88 s/mã ≈ 11,7 phút.
`timeout-minutes` đang là 40.

Và một quan sát nữa, không cần dụng cụ: **bốn lệnh chờ có khớp không.**
Chúng phải khớp — `fill_pending()` không đọc cờ C5. Không khớp mà cũng
không có lý do ghi lại thì đó là một lỗi mới.

> Ba trong bốn lệnh ấy (NAF, TCB, HUT) do cấu hình 44 phiên sinh ra —
> cấu hình nay không còn tồn tại. **Bốn điểm dữ liệu kết quả đầu tiên của
> dự án thuộc về một hệ thống khác với hệ thống sẽ sinh ra các lệnh sau.**
> Ghi ở đây để không ai gộp chúng vào một chuỗi rồi đọc như một chuỗi.


---

## BƯỚC 6 — LƯỢT CHẠY THẬT ĐẦU TIÊN, VÀ Ô C1 ĐẾM SAI ĐƠN VỊ (31/08/2026)

### Thị trường nghỉ lễ Quốc khánh 31/08 → 02/09

Ba ngày làm việc liên tiếp không có phiên — một cấu hình hệ thống chưa
từng chạy qua. Ba hệ quả đã kiểm bằng cách chạy, không bằng suy luận:

- **Bốn lệnh chờ KHÔNG khớp**, đúng như thiết kế. `fill_pending` có chốt
  `session_date <= signal_date thì bỏ qua`, mà nến cuối vẫn là 28/08 —
  bằng đúng ngày tín hiệu. Chúng đợi phiên 03/09.
- **Cron GitHub vẫn nổ T2–T6**, không biết lịch nghỉ Việt Nam. Các lượt đó
  chấm lại nến thứ Sáu. Cổng đóng nên vô hại.
- **Phép thử cổng dời sang 03/09.**

### Lượt chạy tay 09:17 — cả ba câu hỏi đều có đáp án

Bấm `workflow_dispatch` vì cron đã trễ 6–10 tiếng hai phiên liền, và hai
phép đo dựng ở bước 5 chỉ lấy được lúc máy quét đang chạy.

**1. Cửa sổ dữ liệu trên gói MIỄN PHÍ — chỗ tối của BƯỚC 2 đã đóng.**
Annotation `::notice::` của lượt chạy:

```
CỬA SỔ DỮ LIỆU: 71 mã · trung vị 784 phiên (ít nhất 138 · nhiều nhất 784)
· 0 mã dưới 50 phiên — mốc SMA50/SMA200 trả None
· kỳ vọng 746 phiên theo VN-INDEX tới 2026-08-28
```

**784 phiên — đúng bằng con số máy local hạng silver.** Gói miễn phí phục
vụ đủ cửa sổ 1095 ngày cho cổ phiếu; giới hạn của gói nằm ở BCTC và hạn
mức request, không ở lịch sử giá. Và **0 mã dưới mốc 50 phiên**: SMA50 và
SMA200 tính được cho cả rổ, nên `trend_score` không còn kẹt ở ba nấc.
Ngưỡng 62 nay được áp lên đúng phân phối điểm đã hiệu chuẩn nó.

Mốc "ít nhất 138" là một mã mới niêm yết — trên mốc 50, không ảnh hưởng.

**2. Thời gian bước quét: 492 giây (8,2 phút)** ở cửa sổ 1095 ngày, so với
318 giây ở cửa sổ 60 ngày. `timeout-minutes` để 40 là rộng rãi. Runner
nhanh hơn máy local (đo 11,7 phút) — dự phòng nằm đúng chiều an toàn.

**3. Cổng C5 chặn THẬT trên đường chạy sản xuất.** 67 quyết định ghi mới,
ngày tín hiệu 2026-08-28:

```
điểm ≥ 62      : 3 mã — cả 3 mang skip_reason "ô C5 ĐÓNG (29/08/2026)…"
đã vào lệnh    : 0
phân bố điểm   : 20s:1 · 30s:12 · 40s:34 · 50s:17 · 60s:3
đối chiếu rò rỉ: 0 quyết định vào lệnh kể từ 29/08 trên 15.781 dòng
```

Đây là lần đầu cổng gặp tín hiệu thật đạt ngưỡng và chặn được. Trước hôm
nay mọi khẳng định "cổng đang đóng" đều chỉ là đọc mã nguồn.

### Ô C1 đếm bằng NGÀY LÀM VIỆC, không bằng PHIÊN

Kỳ nghỉ này lôi ra một lỗi có sẵn. `_tre_phien` đếm bằng
`pd.bdate_range` — T2 tới T6 — nhưng thị trường nghỉ lễ:

```
31/08 → 1     01/09 → 2     02/09 → 3     03/09 → 4   ⚠️ vượt ngưỡng 3
```

Sáng thứ Năm 03/09, phiên ĐẦU TIÊN mở lại, bộ đếm cũ báo trễ 4 phiên
trong khi dữ liệu chỉ cũ **một** phiên. Tết 2027 sẽ cho 8–9.

Hai hậu quả, và cái thứ hai nặng hơn nhiều:

- `status()` in "Cổng VN-INDEX: TẮT" trong báo cáo phiên — báo sai. Nó
  không đổi quyết định nào (`status()` chỉ in), nhưng một dòng "TẮT" sai
  làm người đọc quen bỏ qua dòng "TẮT" thật.
- `is_vni_bullish()` **ném `CacheQuaHanError` và dừng cả phiên quét** nếu
  nguồn giá cổ phiếu có nến 03/09 trước khi chuỗi VN-INDEX có. Lệch thật
  là một phiên; bộ đếm cũ gọi nó là bốn, và bốn thì vượt ngưỡng.

### Sửa: lịch lấy từ chính chuỗi giá

`vnstock` không có API lịch giao dịch — đã kiểm. Nhưng **chuỗi giá chính
là bản ghi phiên**: thị trường có phiên thì có nến. `run_daily` nạp lịch
từ rổ đang quét qua `market_filter.ghi_nhan_lich_phien()`, một lần, ngay
sau mã đầu tiên tải được và TRƯỚC khi chấm nó — để mã đầu và mã cuối dùng
cùng một lịch.

**Cái bẫy, và chốt chặn cho nó.** Nếu chính lịch cũng cũ hơn mốc thì phép
đếm ra 0 và ô C1 tắt lặng lẽ — đúng thứ nó sinh ra để bắt. Nên lịch chỉ
được dùng khi nó PHỦ TỚI mốc; không phủ thì lùi về đếm ngày làm việc, và
`status()` trả thêm cờ `uoc_tinh` để một con số nghỉ lễ không trông giống
một con số cache chết.

Báo cáo sau quét nay đối chiếu với **phiên cuối của rổ**, không với
`date.today()`: ngày nghỉ lễ không phải một phiên bị lỡ.

Bốn tình huống, đo bằng cách chạy:

| Tình huống | Ngày làm việc | Phiên thật | Đúng? |
|---|---|---|---|
| Nghỉ lễ, hai nguồn cùng ở 28/08 | 3 | **0** | ✅ |
| 03/09, chỉ số chậm 1 phiên | 4 → **NỔ** | **1** | ✅ không nổ |
| Cache chết thật (07/08 vs 20/08) | 9 | **9** | ✅ vẫn nổ |
| Lịch cũ hơn mốc | 4 | **4** (lùi) | ✅ không tắt lặng lẽ |

### Đột biến 8/8 đỏ

```
bỏ chốt chặn lịch cũ hơn mốc        -> đỏ    lệch một phiên (tính cả ngày cuối) -> đỏ
bỏ qua lịch, luôn đếm ngày làm việc -> đỏ    status không bao giờ nói ước tính  -> đỏ
nạp lịch TÍCH LUỸ thay vì ghi đè    -> đỏ    máy quét không nạp lịch nữa        -> đỏ
_lich_phu_toi luôn báo CÓ           -> đỏ    báo cáo đối chiếu với hôm nay      -> đỏ
```

Đột biến "tích luỹ thay vì ghi đè" canh bất biến 2: lịch nạp lại phải ghi
đè, không cộng dồn, nếu không lượt sau đếm trên một lịch khác lượt trước —
đúng cơ chế `sl_pattern_memory.json` đã làm cùng input ra 47 và 59.

629 → 636 test xanh · Python 3.11 sạch · `chan_bia_so_lieu` 0 CHẶN.

### Còn lại cho thứ Năm 03/09

Bốn lệnh chờ khớp ở giá mở cửa. Đó là bốn điểm dữ liệu kết quả đầu tiên
của dự án — và ba trong bốn (NAF, TCB, HUT) do cấu hình 44 phiên sinh ra,
cấu hình nay không còn tồn tại.


---

## BƯỚC 7 — TRẦN CỦA ĐẶC TRƯNG, VÀ RÀO SO VỚI THẾ GIỚI (31/08/2026)

Xuất phát từ một câu hỏi tưởng là về mô hình: *rho ≈ 0 vì sáu agent không
chứa tín hiệu, hay vì bộ trọng số tay gộp chúng sai cách?* Trả lời xong thì
câu hỏi lớn hơn lộ ra, và nó không phải câu hỏi về mô hình.

### Thiết kế trước, chạy sau — và thiết kế đã bác kế hoạch đầu tiên

Kế hoạch ban đầu: đo trên vùng sạch, nhịp 20 phiên. **Tính lực phát hiện
trước khi chạy thì nó không đủ.**

```
vùng sạch 25.219 phiên  −min_history 250 −purge 21  →  16.276 quan sát
nhãn 20 phiên chồng lấn → chia (h+1) → 23,8 khối/mã × 33 mã = n hiệu dụng 784
|rho| nhỏ nhất phát hiện được (80% lực)  : 0,100
rào hoà vốn kinh tế @top5%               : 0,048
```

Chạy xong mà ra "không có tín hiệu" thì đó là **thiếu bằng chứng, không
phải bằng chứng vắng mặt**. Ba con số phải đo trước khi thiết kế:

| Đo | Kết quả | Hệ quả |
|---|---|---|
| Nhãn nào giữ được cỡ mẫu | thô **+0,368** · vượt rổ **−0,012** | Nhãn thô làm 68 mã sụp còn **2,6 mã độc lập**. Bắt buộc dùng nhãn vượt rổ — trùng bất biến 6. |
| Đặc trưng có nghèo như `MO-XE` ghi | trend **10** · mom **17** · sr **7** · điểm **61** nấc | Không. Con số cũ là tính chất của cửa sổ 44 phiên. |
| Chấm điểm mất bao lâu | **15,6 ms**/phiên | Toàn cache 8,5 phút. Chấm một lần, mọi horizon dùng lại. |

### Chặng 1 — cận trên trong mẫu

Khớp mô hình tuyến tính trên **toàn bộ** dữ liệu, không giữ lại phần nào.
Đây là cận trên đúng nghĩa: không quy trình trung thực nào vượt được điểm
tối ưu trong mẫu. Sàn nhiễu dựng bằng **hoán vị dịch vòng theo mã** (1.000
lần, seed 0) — giữ tự tương quan trong mã và cấu trúc chéo, chỉ phá liên
kết đặc trưng↔nhãn, nên nó tự nuốt phần lạm phát do khớp trong mẫu.

Chấm 63.389 phiên / 69 mã, 512 giây:

```
                         h=5      h=10     h=20     rào hoà vốn @top5%
Điểm hệ thống (0 tham số) −0,0117  −0,0050  +0,0040  0,101 · 0,070 · 0,048
Trần A — 5 điểm agent      0,0115   0,0093   0,0071
Trần B — 8 chỉ báo thô     0,0234   0,0443   0,0640
sàn nhiễu (hoán vị)        0,0446   0,0609   0,0839
```

> **Mọi con số rào trong mục này tính ở chi phí 0,89%/vòng — tức ĐÃ gồm
> phí Sở sửa cùng ngày (PR #33).** Bản chạy đầu dùng 0,83% và cho
> 0,094 · 0,065 · 0,045. `experiment_tran_dac_trung.py` lấy phí THẲNG từ
> `paper_metrics.ROUND_TRIP_COST_PCT` nên rào tự dịch khi hằng số phí đổi
> — không có bản sao nào để trôi ra khỏi nhau.

**Điểm hệ thống ở h=5 khác 0 có ý nghĩa, và ÂM** (sàn nhiễu đối xứng
[−0,010 ; +0,023]). Cùng dấu với −0,019 mà `MO-XE` đo độc lập trên 10 mã.

### Chứng cứ dương — bước quyết định, không phải kết quả null

Không có bước này thì *"không tìm thấy gì"* và *"máy đo hỏng"* trông y hệt
nhau. Tiêm một đặc trưng giả có mức tương quan **biết trước**:

| Tiêm | h=5 bắt được? | h=20 bắt được? |
|---|---|---|
| không có gì | ❌ đúng | ❌ đúng |
| nửa rào | ✅ **CÓ** | ❌ không |
| **đúng bằng rào** | ✅ **CÓ** | ❌ **không** |
| 1,5× rào | ✅ CÓ | ✅ CÓ |

**h=5: phép đo hoạt động** → kết quả null ở đó là bằng chứng vắng mặt thật.
**h=20: tiêm đúng rào mà máy vẫn im** → kết quả "dưới sàn nhiễu" ở h=20
KHÔNG đọc được.

> **Lỗi khai báo trước, ghi lại để không lặp.** Test chính được khai là
> h=20 vì nó khớp nhịp nắm giữ thật 20,3 ngày. Bảng lực — viết TRƯỚC lượt
> chạy — đã ghi h=20 là "sát biên". Chọn test chính theo **ý nghĩa kinh tế**
> thay vì theo **lực phát hiện** là sai. Kết luận h=5/h=10 vẫn đứng vì lực
> của chúng được xác lập trước lượt chạy, không phải chọn ra sau khi thấy số.

**Cổng sang chặng 2: ĐÓNG.** Tiêu chí khai trước — *vượt phân vị 95 hoán vị
VÀ ≥ rào hoà vốn* — không đạt vế nào, ở nhịp nào. Chặng 2 (trần phi tuyến)
và chặng 3 (xác nhận trên vùng sạch) **không chạy**, và **vùng sạch 25.219
phiên vẫn nguyên vẹn, chưa bị nhìn**.

### Hiệu chuẩn ngoài — chỗ dữ liệu nội bộ không trả lời được

Rào hoà vốn của dự án là 0,041–0,086 tuỳ nhịp. Câu hỏi không tự trả lời
được: *mức đó so với thứ ngành thật sự đạt được thì thế nào?*

```
Factor cổ phiếu điển hình (IC công bố)        rho 0,020 – 0,050
Gu–Kelly–Xiu 2020 — trần thực nghiệm          rho 0,057 – 0,063
  R² ngoài mẫu theo tháng 0,33–0,40%, cây + mạng nơ-ron,
  ~900 biến dự báo, cổ phiếu Mỹ, 60 năm dữ liệu
──────────────────────────────────────────────────────────────
Rào dự án · h=5    0,101   CAO HƠN mọi kết quả đã công bố
Rào dự án · h=10   0,070   trên cả mức "mạnh" của ngành
Rào dự án · h=20   0,048   trong vùng, biên an toàn ≈ 0
Rào dự án · h=60   0,026   lần đầu có biên thật
```

**Ở nhịp 5 và 10, rào cao hơn cả kết quả tốt nhất thế giới từng công bố**
(0,101 và 0,070 so với trần GKX 0,063).
Nghĩa là dù đặc trưng có tín hiệu đi nữa, cấu hình đó vẫn không thể lãi.
Vấn đề không nằm ở việc tìm mô hình tốt hơn.

**Anomaly được ghi nhận ở Việt Nam là ĐẢO CHIỀU, không phải momentum.**
Tài liệu về HOSE: danh mục "kẻ thua" vượt "kẻ thắng" 1,80% và 2,17% ở tháng
thứ hai và thứ ba. Momentum VN yếu và biến mất khi kiểm soát rủi ro; chỉ
tồn tại ở nhịp dài (hình thành 6 tháng, nắm 9 tháng). Mà điểm của dự án bị
chi phối bởi `trend` và `momentum` — tương quan 0,76 với nhau, trọng số lớn
nhất. Ba đường độc lập chỉ cùng một hướng.

> **Đây là giả thuyết để kiểm, KHÔNG phải chiến lược.** Ba cảnh báo: nghiên
> cứu chạy trên mẫu cũ và phần lớn không khử thiên lệch sống sót; hiệu ứng
> có thể đã phân rã; và tài liệu về chi phí nói chiến lược đảo chiều **chết
> vì chi phí ở nhóm vốn hoá nhỏ**, chỉ sống ở vốn hoá lớn.
>
> Nếu kiểm: giả thuyết đến TỪ TÀI LIỆU NGOÀI, cố định trước khi nhìn dữ
> liệu — nên hợp lệ với bất biến 7 và 8. Lật dấu SAU khi thấy số âm thì
> không.

**Nghiên cứu gần dự án nhất đã cho cùng phán quyết.** 1.400 cổ phiếu, 24
thị trường cận biên, 1997–2008, dữ liệu khử thiên lệch sống sót: hơn 30
chiến lược đã công bố cho alpha có ý nghĩa; sau khi tính hoa hồng, chênh
mua-bán, quy mô và ràng buộc cấm bán khống thì **chỉ một nhúm còn lãi**.
Kết quả −0,927% của dự án là điều **bình thường** ở lớp thị trường này.

### Đòn bẩy lớn nhất là SỐ VỊ THẾ, không phải tín hiệu

Luật cơ bản của quản lý chủ động: `IR = TC × IC × √BR`. Dự án đã đo được
rằng nhãn vượt rổ giữa các mã gần như độc lập (−0,012) nên breadth khả dụng
rất lớn — nhưng BR đếm **vị thế đã vào**, không phải mã có sẵn.

| Cấu hình | BR/năm | IC | TC | IR |
|---|---|---|---|---|
| Hiện tại — ~45 lệnh/năm, ~3 vị thế | 45 | 0,030 | 0,20 | **0,040** |
| Nếu IC đạt mức GKX, vẫn 3 vị thế | 45 | 0,063 | 0,20 | 0,085 |
| Giữ 15 vị thế thay vì 3 | 225 | 0,030 | 0,50 | **0,225** |
| 15 vị thế + IC mức GKX | 225 | 0,063 | 0,50 | 0,473 |

Có tín hiệu tốt nhất thế giới cũng không cứu được breadth quá nhỏ. Và điều
này khớp với chính con số dự án đã tự tính — *"cần 1.050 lệnh, ~23 năm ở
nhịp 45 lệnh/năm"*. Cùng một hiện tượng nhìn từ phía thống kê. **Tăng số vị
thế gạt cả hai nút thắt bằng một cần, và không cần thêm tín hiệu nào.**

### Dự án đã tự phát minh lại một khung có sẵn tên

| Dự án đang có | Tên trong tài liệu | Phần chưa có |
|---|---|---|
| Bất biến 7 — cấm lấy cực đại của N lần thử | **Deflated Sharpe Ratio** (Bailey & López de Prado 2014) | Công thức **chiết khấu định lượng** theo số lần thử, thay vì cấm tuyệt đối |
| `co_mau_cho_luc()` | **Minimum Track Record Length** | Bản chuẩn tính cả **độ lệch và độ nhọn** — phân phối của dự án lệch mạnh (trung vị −0,40% trong khi kỳ vọng +2,17%) |
| Bất biến 8 — vùng kiểm định ở quá khứ | **Probability of Backtest Overfitting** | Một CON SỐ thay cho một quy tắc định tính |

### Đã sửa trong ngày: phí Sở giao dịch (PR #33)

Bảng phí của công ty chứng khoán tách riêng phí Sở với hoa hồng, nên đọc
lướt chỉ thấy hai dòng. Khoản 0,03%/chiều bị bỏ sót từ đầu.

```
trước : 0,15% ×2 + 0,10%            = 0,40%
nay   : 0,15% ×2 + 0,03% ×2 + 0,10% = 0,46%
```

Rổ chuẩn trong `ro_chuan_tu_chuoi_gia` là **gộp** — `(p_ra − p_vao)/p_vao`,
không trừ phí nào — còn `vs_benchmark` lấy `net_return_pct() − chuẩn`. Nên
**alpha dịch đúng −0,06 đpt: −0,927% → −0,987%.** Đại số trên mã nguồn,
không phải suy đoán.

`MUC_BAT_LOI = −0.927` **cố ý GIỮ nguyên**: nó là con số đo được bằng một
lượt walk-forward thật, và `N_DAY_DU = 596` suy ra từ nó. Gõ tay thành
−0,987 là thay một con số đo bằng một con số suy. Cập nhật khi walk-forward
chạy lại với chi phí mới.

Đột biến 5/5 đỏ. Test cũ derive công thức từ hằng số nên gỡ
`EXCHANGE_FEE_PCT` khỏi CẢ hai nơi thì vẫn xanh — vì vậy test mới **ghim**
con số 0,46%, và đối chiếu trực tiếp hai bản công thức song song
(`Trade.net_return_pct()` vs `paper_metrics.ROUND_TRIP_COST_PCT`).

**Con số trong repo vẫn LẠC QUAN:** 0,15%/chiều là cận DƯỚI của dải bán lẻ
thật (0,15–0,35%). Với công ty đắt hơn, vòng đủ tới 0,76%. Và Bộ Tài chính
đã **đề xuất** thuế 20% trên lãi vốn chuyển nhượng chứng khoán — mới là đề
xuất, nhưng nếu ban hành thì mọi phép tính chi phí phải làm lại.

### Việc tiếp, xếp theo đòn bẩy

1. **Tăng số vị thế đồng thời (3 → 15).** IR ×5,6 ở cùng IC, đồng thời tăng
   lực đo. Động vào `consider_entry` và trần vốn — cần thiết kế và đo riêng.
2. **Kéo dài nhịp nắm giữ.** h=60 đưa rào xuống 0,024. Nhưng dữ liệu hiện
   có không đủ lực đo ở nhịp đó, nên là quyết định bằng **lý lẽ kinh tế**,
   biết trước rằng nó sẽ không kiểm định được sớm.
3. **Kiểm giả thuyết đảo chiều** ở nhóm vốn hoá lớn, một lần, khai trước.

**Cổng C5 giữ ĐÓNG.** Không phát hiện nào ở đây tạo ra lý do mở.

### Tái lập

```bash
python experiment_tran_dac_trung.py --chung-cu-duong
```

Chạy không có cờ đó thì script TỰ NÓI ra rằng kết quả chưa đọc được. Đó là
chủ ý: một dòng "DƯỚI sàn nhiễu" không phân biệt được "không có tín hiệu"
với "phép đo thiếu lực", và dự án này đã bốn lần đọc nhầm một con số theo
hướng có lợi.


---

## BƯỚC 8 — DANH MỤC THẬT, VÀ LẦN THỨ NĂM MỘT CON SỐ ĐẸP TAN RA (31/08/2026)

Xuất phát từ một cần gạt tưởng là nhỏ: *giữ 15 vị thế thay vì 5*. Đọc mã
thì cần gạt đó hoá ra **không đo được**, và lý do dẫn tới một phép đo lớn
hơn nhiều.

### Vì sao cần gạt số vị thế không đo được bằng công cụ cũ

`walkforward._mo_phong` chạy `for sym ... for t` — xong toàn bộ lịch sử FPT
rồi mới sang ACB. Cộng với chốt trong `consider_entry`:

```python
elif self.open_position(symbol) is not None:
    skip = "đã có vị thế đang mở"
```

**Số vị thế đồng thời THẬT ở chế độ đó luôn bằng MỘT.** `TRAN_VON_CAM_KET_PCT`
không bao giờ chạm. Nên mọi thay đổi về cỡ vị thế chỉ co đường vốn lại, không
sinh thêm một lệnh nào — cần gạt hoàn toàn vô hình.

Đã thêm `_mo_phong(..., theo_ngay=False)` (PR #36). Mặc định TẮT, nên không
con số walk-forward nào đã công bố bị đổi âm thầm.

### Phản chứng: cùng dữ liệu, khác duy nhất thứ tự vòng lặp

71 mã · vùng IS · ngưỡng 62 · stride 2 · `che_do_hoc="co_san"`:

| | theo mã (cũ) | **THEO NGÀY (mới)** |
|---|---|---|
| số lệnh | 820 | **214** |
| **kỳ vọng mỗi lệnh** | **+0,83%** | **−0,093%** |
| alpha | −0,110% (không ý nghĩa) | −0,370% (không ý nghĩa) |
| vị thế đồng thời | TB 13,9 · đỉnh **54** | TB **4,2** · đỉnh 7 |
| vốn cam kết | TB 211% · đỉnh **1049%** | TB 57% · đỉnh **100,0%** |
| ngày vượt 100% | 714/962 | 25/889 |

> **Đây là lần thứ NĂM một con số đẹp của dự án tan ra khi đo đúng — và là
> lần đầu đo được bằng PHẢN CHỨNG thay vì chỉ cảnh báo.** Bất biến 7b mô tả
> cơ chế từ lâu ("cộng dồn lệnh chồng lấn là đòn bẩy trá hình"), nhưng chưa
> ai chạy hai lượt để thấy độ lớn. **606 trong 820 lệnh cũ đòi vốn tài khoản
> không có.**

### Cách đọc thứ hai — ĐÃ ĐO, VÀ ĐÃ SAI

Kỳ vọng là trung bình **mỗi lệnh**, nên bỏ bớt lệnh lẽ ra không đổi nó. Nó
đổi vì **tập lệnh đổi**. Giả thuyết tôi đưa ra khi thấy con số:

> *Trần chặn theo thứ tự đến trước, nên nó loại đúng các cụm tín hiệu — mà
> cụm nổ ra lúc thị trường mạnh, tức đúng lúc lợi nhuận tốt. Trần đang cắt
> vào phần ngon.*

**Đo xong thì giả thuyết đó SAI.** Nới trần bằng cách giảm cỡ vị thế (mục
tiêu 15 thay vì 4,2) mở thêm 365 lệnh — và những lệnh thêm vào **xấu hơn**
nhóm cũ, chứ không tốt hơn:

| | sizing cũ (4,2 vị thế) | **sizing mới (15)** |
|---|---|---|
| số lệnh | 214 | **579** (2,7×) |
| vị thế đồng thời | TB 4,2 · trung vị 4 · đỉnh 7 | TB **9,7** · trung vị **11** |
| **kỳ vọng mỗi lệnh** | −0,093% | **−0,193%** |
| **alpha** | −0,370% | **−0,545%** |
| vốn TB · đỉnh | 57,5% · 100,0% | 49,2% · 100,0% |

Giữ lại giả thuyết sai ở đây có chủ đích: nó nghe hợp lý, nó đến từ dữ liệu,
và nó vẫn sai. Đó đúng là hình dạng của bốn lần trước.

### Số vị thế thật: 4,2 — không phải 5,3, cũng không phải 3

`paper_trading.py:245` ghi *"ở mức trung bình 18,8% thì 100% ≈ 5,3 vị thế"*.
Đó là một **chú thích**, suy từ cỡ trung bình chia vào trần. Đo thật:

```
size_pct     : trung vị 16,9% · TB 18,7%  (chú thích ghi 18,8% — sát)
k/c stop     : trung vị 0,0515 · TB 0,0543
vị thế thật  : TB 4,2 · trung vị 4 · đỉnh 7
```

### Ba cảnh báo phải đọc kèm

1. **Đây là vùng IS** — vùng đã bị hàng trăm vòng loop nhìn qua. Không phải
   OOS. Mọi con số trên là in-sample.
2. **Alpha KHÔNG có ý nghĩa ở cả hai chế độ.** 214 lệnh là quá ít; cận trên
   KTC vẫn chứa 0.
3. **Con số "đỉnh vốn 130,7%" trong phần đếm theo lịch là artifact của chính
   phép đếm đó** — sổ lệnh tự ghi đỉnh **100,0%**. `pd.bdate_range` không
   biết lịch nghỉ VN và đếm cả ngày lệnh chưa khớp. Đúng cùng loại artifact
   đã sinh ra 1049% ở chế độ cũ. Số đúng là con số sổ lệnh ghi.

### Thiết kế sizing — suy ra, không gõ

```
mục tiêu 15 vị thế dưới trần 100%  ->  cỡ trung bình 100/15 = 6,67%
account_risk_pct = 6,67 × 0,0515 (k/c stop trung vị đo được) = 0,343
```

Hai chốt `[5,0 ; 33,3]` gần như không phải đụng: với risk 0,343 và khoảng
cách stop 4–6,5%, `size` rơi vào 5,3–8,6%.

**Cảnh báo viết TRƯỚC khi đo, và nó đúng:** `IR = TC × IC × √BR` — nếu
IC ≈ 0 thì IR = 0 bất kể BR. Thêm vị thế **không tạo ra alpha từ hư không**;
nó chia trung bình trên nhiều mẫu hơn, tức **thu hẹp nhiễu quanh alpha đang
có**. Cần gạt này làm câu trả lời **đến nhanh hơn, không đẹp hơn**.

Đo xong: đúng như vậy, và theo chiều khó chịu. 2,7× số lệnh làm khoảng tin
cậy hẹp lại đáng kể — nhưng thứ nó đang hội tụ về là **âm** (−0,545%, vẫn
chưa loại được 0 ở 579 lệnh).

**Kết luận về cần gạt:** nó hoạt động đúng như thiết kế — 4,2 → 9,7 vị thế
đồng thời, 214 → 579 lệnh, trần vẫn giữ đúng 100,0%. Giá trị của nó là **tốc
độ phân giải**, không phải lợi nhuận. Và nó KHÔNG phải lý do để mở cổng C5:
mọi con số ở đây là in-sample, và cả hai cấu hình đều cho alpha âm.

### WALK-FORWARD ĐẦY ĐỦ Ở CHẾ ĐỘ DANH MỤC — CON SỐ QUYẾT ĐỊNH

Lượt đầu tiên của dự án chọn ngưỡng trên IS rồi đo trên OOS **với một danh
mục có thật**. Sizing cũ (4,2 vị thế), chi phí đã gồm phí Sở.

**Dải IS** — và bảng này tự nó là một bài học:

```
ngưỡng   số lệnh   lợi nhuận   kỳ vọng   win rate
  45      287       −33,27%     −0,93      23,7%   << nhiều mẫu nhất
  50      278       −30,61%     −0,88      28,8%
  48      273       −15,68%     −0,37      26,0%
  52      270       −17,61%     −0,51      27,4%
  55      259        +8,97%     +0,11      28,2%
  58      245        +8,61%     +0,16      26,9%   << luật chọn lấy dòng này
  62      214        +4,41%     −0,09      26,2%
```

Luật nêu trước (≥30 lệnh, kỳ vọng cao nhất) chọn **58**. Dòng nhiều mẫu
nhất là 45 với kỳ vọng **−0,93**.

**Kết quả OOS ở ngưỡng 58:**

```
số lệnh              : 181
kỳ vọng mỗi lệnh     : −1,54%
win rate             : 21,5%
lợi nhuận cộng dồn   : −40,41%
alpha khớp từng lệnh : −1,99%/lệnh   KTC 95% [−2,95 ; −0,92]
                       → THUA CHUẨN CÓ Ý NGHĨA
vốn triển khai       : 51% trung bình · 100% đỉnh
```

> **Ngưỡng tốt nhất trên IS là ngưỡng tệ nhất trên OOS.** Bất biến 7 và 8
> đang tự chứng minh chúng tồn tại vì lý do gì, trên chính dữ liệu của dự án.

**So với con số OOS cũ (chế độ theo mã):**

| | theo mã (mọi báo cáo trước) | **THEO NGÀY (danh mục thật)** |
|---|---|---|
| alpha | −0,927% | **−1,99%** |
| KTC 95% | [−1,689 ; −0,076] | **[−2,95 ; −0,92]** |
| loại được 0 | vừa đủ | **dứt khoát** |

Bất lợi thật **hơn gấp đôi** con số dự án vẫn dùng. Ba nguồn, theo thứ tự
độ lớn: (1) danh mục thật thay cho đòn bẩy ẩn, (2) ngưỡng 58 do luật chọn
thay vì 62, (3) phí Sở +0,06 đpt.

### `MUC_BAT_LOI = −0.927` NAY ĐÃ CŨ — cần người quyết

`paper_metrics.MUC_BAT_LOI` ghi mức bất lợi ĐO ĐƯỢC, và `N_DAY_DU = 596`
suy ra từ nó. Cả hai dựa trên lượt walk-forward chế độ theo mã — cấu hình
nay biết là dựng trên đòn bẩy chưa bao giờ tồn tại.

Ở mức −1,99%, cỡ mẫu cho 80% lực tụt từ **596 xuống ~129 lệnh**.

**Chưa sửa, và cố ý.** Đây là hằng số của một điều kiện an toàn; đổi nó sau
khi nhìn số mới là việc phải nêu ra chứ không lặng lẽ làm, kể cả khi hướng
đổi là *thận trọng hơn*. Hàng rào `tests/test_hang_rao_quy_trinh.py` cũng
sẽ đòi chứng minh lại. Để người quyết.

**Cổng C5 vẫn ĐÓNG, và kết quả này củng cố việc đóng.**

### Tái lập

```bash
python walkforward.py --theo-ngay     # toàn bộ walk-forward, chế độ mới
```


---

## BƯỚC 9 — ĐẢO CHIỀU BỊ BÁC BỎ, VÀ MỘT DỤNG CỤ ĐI KIỂM TỰ SAI (01/09/2026)

Việc thứ ba trong danh sách cuối BƯỚC 7: *"kiểm giả thuyết đảo chiều ở
nhóm vốn hoá lớn, một lần, khai trước."* Đã chạy. Giả thuyết bị **bác bỏ**
ở ô chính, với chứng cứ dương đứng sau nên đó là bằng chứng vắng mặt thật.

Thứ đắt hơn nằm ở đường đi. Tôi viết thêm một phép hiệu chuẩn để kiểm sàn
nhiễu, nó báo sàn nhiễu hỏng nặng ở mọi nhịp, và **chính nó mới là cái
hỏng** — dựng ngưỡng bằng một đường thứ hai thì sàn nhiễu cũ đúng ở cả năm
nhịp. Nếu tin phép hiệu chuẩn ấy thì BƯỚC 7 lẫn BƯỚC 9 đều đã bị tuyên là
không đọc được.

### Bản khai trước nằm ở một commit RIÊNG, trước lượt chạy

`51adc88` chứa **chỉ** `experiment_dao_chieu.py` — thiết kế, bảng lực,
luật quyết định — và không có một con số kết quả nào. Kết quả nằm ở commit
sau. Lịch sử git vì thế tự chứng minh thứ tự, không cần ai tin lời kể.

Ba thứ được chốt trước khi nhìn bất kỳ tương quan nào:

| Chốt trước | Nội dung |
|---|---|
| **Nguồn giả thuyết** | Tài liệu ngoài về HOSE (kẻ thua vượt kẻ thắng 1,80% và 2,17% ở tháng 2 và 3). Không đến từ dữ liệu dự án → hợp lệ với bất biến 7 và 8. |
| **Dấu** | ÂM. Một rho DƯƠNG có ý nghĩa **bác bỏ** giả thuyết, không phải "tìm thấy tín hiệu". Luật này nằm trong hàm `phan_xu`, không nằm trong đầu người đọc. |
| **Ô chính** | J=21 h=21, chọn theo **lực phát hiện**. |

### Ô chính chọn theo LỰC, và đó là chỗ BƯỚC 7 đã sai

Bảng lực tính TRƯỚC lượt chạy. Ba đại lượng dựng nên nó — cỡ mẫu, n hiệu
dụng, độ lệch chuẩn của nhãn — đều không phụ thuộc liên kết đặc trưng↔nhãn,
nên chọn thiết kế theo chúng không phải là nhìn trộm.

```
   J    h   quan sát   n hiệu dụng   phát hiện 80%   rào @5%   đủ lực?
  21   21     73.584         3.345           0,043     0,044      CÓ   <- Ô CHÍNH
  10   10     74.343         6.758           0,030     0,066      CÓ
   5    5     74.693        12.449           0,022     0,095      CÓ
  21   42     72.135         1.678           0,061     0,031     không
  21   63     70.686         1.104           0,075     0,025     không
```

**Phát hiện của tài liệu nằm ở tháng 2–3, tức h=42 — và ô đó KHÔNG đủ lực.**
Chọn nó làm ô chính vì nó "khớp tài liệu" là đúng lỗi BƯỚC 7 tự ghi lại:
chọn theo ý nghĩa kinh tế trong khi bảng lực đã ghi là sát biên. Ô chính vì
thế là (21, 21) — đảo chiều một tháng cổ điển, ô duy nhất vừa được tài liệu
đỡ vừa đủ lực. Các ô còn lại vẫn chạy, kèm nhãn khai trước.

### Kết quả

69 mã · 73.584 quan sát · nhãn vượt rổ · hoán vị dịch vòng 1.000 lần · seed 0:

```
   J    h   quan sát    n_eff       rho   nhiễu5%      rào   phán xử
  21   21    73.584     3345   +0,0018   −0,0180    0,044   không vượt sàn nhiễu   <<< Ô CHÍNH
  10   10    74.343     6758   +0,0140   −0,0140    0,066   không vượt sàn nhiễu
   5    5    74.693    12449   −0,0017   −0,0104    0,095   không vượt sàn nhiễu
  21   42    72.135     1678   −0,0258   −0,0213    0,031   vượt nhiễu, dưới rào   (khai trước: không đọc được)
  21   63    70.686     1104   −0,0349   −0,0265    0,025   "ĐẠT"                  (khai trước: không đọc được)
```

**Ô chính: +0,0018, tức ngược dấu giả thuyết và bằng không.** Chứng cứ
dương ở đúng ô đó qua sạch: tiêm 0 thì im, tiêm nửa rào thì kêu, tiêm đúng
rào thì kêu. Nên đây là **bằng chứng vắng mặt**, không phải thiếu bằng chứng.

Lực thật còn tốt hơn bản khai trước, vì sàn nhiễu đo được HẸP hơn lý thuyết
(sd 0,0151 so với 1/√n_eff = 0,0173 — nhãn vượt rổ bị ràng buộc tổng bằng 0
mỗi ngày nên phương sai co lại):

```
n hiệu dụng thật    4.386   (khai trước 3.345)
phát hiện 80% thật  0,0375  (khai trước 0,043) — nay DƯỚI rào 0,044
lực nếu hiệu ứng đúng bằng mức tài liệu công bố (−0,063)  : 99,9%
lực nếu hiệu ứng chỉ bằng NỬA mức công bố      (−0,032)  : 81,4%
lực nếu hiệu ứng đúng bằng rào hoà vốn         (−0,044)  : 95,7%
```

> **Nếu hiệu ứng đảo chiều mà tài liệu công bố có mặt trong dữ liệu này ở
> đúng độ lớn đó, phép đo đã bắt được nó gần như chắc chắn.** Nó không có
> mặt. Ngay cả một nửa độ lớn ấy cũng bị loại với 81% lực.

### Sàn nhiễu có đáng tin không — hỏi hai lần, hai câu trả lời cãi nhau

Ô duy nhất cho ra "ĐẠT" là h=63, ô đã khai trước là không đọc được. Trước
khi nói bất cứ điều gì về nó, phải hỏi ngược lại: *máy đo có im khi KHÔNG
có gì không?* Chứng cứ dương không hỏi câu đó.

Hỏi bằng hai cách, và **hai cách trả lời trái nhau**. Đó mới là kết quả
đáng giá nhất của ngày.

#### Cách 1 — đếm báo động giả (`--chung-cu-am`)

Dựng đặc trưng **giả** bằng cách dịch vòng chính đặc trưng thật trong từng
mã, rồi chạy hết quy trình. Tỷ lệ "âm có ý nghĩa" phải xấp xỉ 5%:

```
           ô   báo giả          KTC 95%   ngưỡng  đọc được?
  J=21 h=21      14.0% [  9.9% ;  19.5%]   10.0%  KHÔNG — chưa chứng minh được
  J=21 h=42      19.0% [ 14.2% ;  25.0%]   10.0%  KHÔNG — chưa chứng minh được
  J=21 h=63      30.5% [ 24.5% ;  37.2%]   10.0%  KHÔNG — chưa chứng minh được
  Fail-closed: cần CẬN TRÊN dưới ngưỡng, không phải điểm ước lượng.
```

Đọc thẳng thì đây là một dụng cụ hỏng nặng, hỏng ở mọi nhịp, hỏng theo
chiều dễ ra phát hiện.

#### Cách 2 — đo thẳng ngưỡng (`--nguong-hieu-chuan`)

Không đi qua hoán vị nhãn. Dựng luôn phân phối của thống kê khi không có
liên kết rồi lấy phân vị 5%. Rẻ hơn cách 1 hàng trăm lần vì mỗi lượt chỉ
là **một** phép tính tương quan, không phải một sàn nhiễu 200 hoán vị:

```
           ô       rho  nhiễu5% cũ  ngưỡng mới   null TB  null sd  đổi phán xử?
  J=21 h=21      0.0018     -0.0188     -0.0170    0.0054   0.0149  không (không -> không)
  J=10 h=10      0.0140     -0.0142     -0.0141    0.0024   0.0105  không (không -> không)
  J=5 h=5      -0.0017     -0.0100     -0.0104    0.0010   0.0072  không (không -> không)
  J=21 h=42     -0.0258     -0.0241     -0.0219    0.0024   0.0154  không (có ý nghĩa -> có ý nghĩa)
  J=21 h=63     -0.0349     -0.0250     -0.0275   -0.0018   0.0160  không (có ý nghĩa -> có ý nghĩa)
  Ngưỡng mới CHẶT hơn thì chỉ xoá được một 'ĐẠT', không tạo ra 'ĐẠT' mới.
```

Hai ngưỡng **khớp ở cả năm nhịp**, chênh nhiều nhất 0,0025, và **không ô
nào đổi phán xử**. Ở ba nhịp giữa, sàn nhiễu hoán vị còn hơi CHẶT hơn.

#### Cái sai là CÁCH 1, và cơ chế đo được bằng số

`chung_cu_am` dịch vòng ĐẶC TRƯNG rồi vẫn dựng sàn nhiễu bằng cách xáo
NHÃN. Độ dịch hiệu dụng khi đó là **hiệu** của hai phép dịch — và hiệu ấy
quấn vòng, nên nó nuốt phải các độ dịch NHỎ, đúng những độ dịch mà phép
kiểm thật loại trừ theo thiết kế (`k >= h+1`). Sàn nhiễu của nó bị kéo lên
và nó tự báo động giả.

Dải bị nuốt rộng đúng `2(h+1)/n`, với n ≈ 1.070 phiên mỗi mã:

| nhịp | dải bị nuốt `2(h+1)/n` | báo giả vượt mức 5% | tỷ số |
|---|---|---|---|
| h=21 | 4,1% | +9,0 đpt | 2,2 |
| h=42 | 8,0% | +14,0 đpt | 1,8 |
| h=63 | 12,0% | +25.5 đpt | 2,1 |

Tỷ số gần như hằng số quanh 2, và khoảng tin cậy của cả ba đều chứa 2.
Dòng h=63 là một **tiên đoán ra trước** khi lượt chạy tới ô đó — dự kiến
+20 đpt, đo được +25,5 [19,5 ; 32,2]. Không phải một lời giải thích ghép
vào sau khi đã thấy số.

> **Một phép hiệu chuẩn cũng là một phép đo, nên nó cũng sai được.** Hôm
> nay dụng cụ đi kiểm sai, còn dụng cụ bị kiểm thì đúng. Chỉ chạy cách 1
> thì BƯỚC 7 và BƯỚC 9 đều đã bị tuyên là không đọc được — một kết luận
> sai, đắt, và nghe rất có kỷ luật.
>
> Kết quả *"dụng cụ hỏng"* phải được đối chiếu đúng như kết quả *"tìm thấy
> tín hiệu"*: nó cũng đẹp theo cách riêng, vì nó cho phép gạt bỏ mọi thứ
> khó chịu mà vẫn tỏ ra nghiêm khắc.

Giữ cả hai trong repo, có chủ đích: một phép hiệu chuẩn nghe rất hợp lý mà
vẫn sai thì đáng giữ hơn một phép hiệu chuẩn đúng.

#### Và một lỗi thứ hai, trong cùng phép đo đó

Bản đầu của `chung_cu_am` chạy **40 lượt** rồi in `5,0%` và `30,0%` như hai
con số. Lượt chạy lại khác hạt giống cho `10,0%` và `17,5%`. Với tỷ lệ thật
~14%, sai số chuẩn của 40 lượt là 5,5 điểm phần trăm — cả bốn con số nằm
trong nhiễu của nhau.

Bất biến 5 — *"mọi con số phải kèm khoảng tin cậy"* — được đọc trong cùng
phiên và vẫn lọt, vì phần đầu óc đang canh bất biến 5 thì canh **kết quả**,
còn con số này nằm ở **dụng cụ**. Đã sửa ba chỗ, mỗi chỗ một gác kèm đột
biến:

| Sửa | Vì sao |
|---|---|
| 40 → **200 lượt** | để một ô hiệu chuẩn thật CHỨNG MINH ĐƯỢC là dưới ngưỡng |
| tỷ lệ → **khoảng Wilson** | khoảng chuẩn trả `[0 ; 0]` khi đếm 0 lần — biến "chưa thấy" thành "chắc chắn không có" |
| phán xử → **fail-closed** | đọc được chỉ khi **cận trên** dưới ngưỡng, không phải điểm ước lượng |

Kèm một gác bắt số lượt **tự biện minh được**: nếu một ô hiệu chuẩn hoàn
hảo vẫn cho cận trên vượt ngưỡng thì cờ hiệu chuẩn chỉ là trang trí.

### Bảng lực khai trước đã ĐÁNH GIÁ THẤP cỡ mẫu hiệu dụng

Hệ quả thứ hai của việc đo thẳng, và nó chạm tới cả BƯỚC 7. Bảng lực dùng
công thức quen `n_eff = n/(h+1)` cho nhãn chồng lấn. Độ lệch chuẩn ĐO ĐƯỢC
của phân phối null nói khác:

```
        n_eff theo công thức   n_eff suy từ sd đo được   tỷ lệ
h = 21          3.345                   4.504            1,3×
h = 42          1.678                   4.219            2,5×
h = 63          1.104                   3.906            3,5×
```

Công thức càng sai khi nhịp càng dài. Giả thuyết hợp lý nhất — **chưa
kiểm**: nhãn vượt rổ đã bỏ thành phần thị trường chung, mà đó là nguồn dai
dẳng nhất của tự tương quan, nên phần chồng lấn còn lại tốn ít cỡ mẫu hơn
công thức giả định.

Phải nói rõ: **nhãn "thiếu lực" dán cho h=42 và h=63 dựa trên một công
thức nay biết là bi quan.** Nhưng nhãn ấy dán TRƯỚC lượt chạy nên nó ở
lại — gỡ nhãn sau khi đã thấy số là đúng thứ bất biến 7 cấm, kể cả khi lý
do gỡ là một lý do kỹ thuật đúng.

### h=63: không phải phát hiện, nhưng nay là câu hỏi CÓ ĐỊA CHỈ

Ô ấy cho rho −0,0349, vượt cả sàn nhiễu hoán vị (−0,0250) lẫn ngưỡng đo
trực tiếp (−0,0275), và nằm TRÊN rào hoà vốn 0,025. Một phía, p ≈ 0,019.

Ba lý do nó vẫn KHÔNG phải kết quả, cả ba có trước con số:

1. Khai trước là không đọc được. Nhãn đó ở lại.
2. **Năm ô cùng lúc.** Bonferroni cho ngưỡng 0,01; p = 0,019 không qua.
3. Chặng 2 của chính bản khai trước — xác nhận trên vùng sạch — chỉ chạy
   nếu **ô chính** ĐẠT. Ô chính không đạt, nên chặng 2 KHÔNG chạy và
   25.219 phiên sạch vẫn nguyên vẹn.

Việc đúng cho lần sau: **một** phép kiểm khai trước riêng cho h=63, tính
lực bằng độ lệch chuẩn ĐO ĐƯỢC (0,0160) chứ không bằng công thức. Ở mức
hiệu ứng 0,035 cần sd ≤ 0,0141, tức khoảng **1,3× dữ liệu hiện có** — lần
đầu một câu hỏi của dự án này nằm trong tầm với thay vì cần hàng chục năm.

### Bản khai trước đã trả đúng thứ nó sinh ra để trả

Nếu quét năm ô rồi báo cáo ô đẹp nhất, tiêu đề hôm nay sẽ là:

> *"Tìm thấy đảo chiều ở nhịp 63 phiên: rho −0,035, vượt sàn nhiễu VÀ trên
> rào hoà vốn 0,025."*

Câu đó sai vì **hai** lý do độc lập, và cả hai được ghi trước khi con số
xuất hiện: ô ấy khai trước là thiếu lực, và năm ô chạy cùng lúc thì
Bonferroni đòi p < 0,01 trong khi nó cho 0,019. Đây là lần đầu trong dự án
một bản khai trước chặn được một phát hiện giả **ngay ở lượt chạy đầu**,
thay vì phải phát hiện ngược lại vài ngày sau.

### Phân tầng thanh khoản — không đỡ giả thuyết, mà cũng không đủ lực

Tài liệu nói đảo chiều **chết vì chi phí ở vốn hoá nhỏ**, chỉ sống ở vốn
hoá lớn. Xếp hạng dựng nhân quả (trung vị 250 phiên tính tới hết phiên T,
xếp hạng chéo trong đúng ngày đó — xếp bằng trung vị toàn mẫu là nhìn trộm):

```
tầng    quan sát   n_eff       rho   nhiễu5%     rào
lớn       20.921     951   +0,0267   −0,0362   0,048
nhỏ       19.897     904   +0,0119   −0,0168   0,044
```

Cả hai tầng đều **dương**, tức ngược chiều giả thuyết, và không tầng nào có
ý nghĩa. Cắt còn một phần ba làm n hiệu dụng chia ba TRONG KHI rào ở nhóm
lớn lại CAO HƠN vì σ nhỏ hơn — hai chiều cùng xấu, đã nói trước khi chạy.
Nên đây là quan sát, không phải kết luận.

### Ba điều phải đọc kèm, và một trong ba làm kết luận MẠNH hơn

1. **Giai đoạn khác.** Cache dự án là 2021-10 → 2026-08; tài liệu HOSE chạy
   trên mẫu cũ hơn nhiều. Hiệu ứng có thể đã phân rã. Đây là một trong ba
   cảnh báo đã viết ở BƯỚC 7 trước khi chạy.
2. **Thiên lệch sống sót làm kết luận MẠNH hơn, không yếu đi.** Rổ là ảnh
   chụp hôm nay, nên mã rớt hẳn không có mặt — mà đó đúng là *"kẻ thua
   không hồi phục"*. Bỏ chúng ra làm nhóm thua còn lại trông TỐT hơn thực
   tế, tức **thổi phồng** đảo chiều đo được. Đo ra ≈ 0 trên một mẫu đã
   nghiêng về phía có đảo chiều thì hiệu ứng thật ≤ 0.
3. **Đây là kiểm sự TỒN TẠI của tín hiệu, không phải kiểm một chiến lược.**
   Không lệnh nào được mở, không cần gạt nào được vặn.

### Hệ quả cho BƯỚC 7 — không rút lại gì

BƯỚC 7 dùng cùng `san_nhieu` ở h=5/10/20. Phép đo thẳng hôm nay xác nhận
sàn nhiễu ấy đúng ở h=5, 10, 21, 42 và 63 — nên **mọi kết luận của BƯỚC 7
đứng nguyên**, và "h=20 không đọc được" vẫn dựa đúng vào lý do cũ của nó là
chứng cứ dương, không phải một khuyết tật của sàn nhiễu.

Cái phải ghi thêm là bảng lực của BƯỚC 7: `|rho| phát hiện được 0,100` ở
h=20 tính bằng đúng công thức `n/(h+1)` nay biết là bi quan. Con số thật
nhiều khả năng thấp hơn. Điều đó **không** cứu được kết luận null nào — nó
chỉ nói phép đo hồi ấy mạnh hơn nó tự nghĩ.

### Cổng C5 giữ ĐÓNG

Không phát hiện nào ở đây tạo ra lý do mở. Một giả thuyết bị bác bỏ không
làm alpha −1,99% khá lên.

### Tái lập

```bash
python experiment_dao_chieu.py --chung-cu-duong --phan-tang   # ket qua chinh
python experiment_dao_chieu.py --nguong-hieu-chuan            # nguong duong 2
python experiment_dao_chieu.py --chung-cu-am                  # ~50 phut
```

Lệnh thứ hai là bắt buộc trước khi tin một phán xử ở nhịp dài — và nó rẻ.
Lệnh thứ ba giữ lại phép hiệu chuẩn ĐÃ SAI, có chủ đích: nó là bằng chứng
đọc lại được cho mục "Cái sai là CÁCH 1".
