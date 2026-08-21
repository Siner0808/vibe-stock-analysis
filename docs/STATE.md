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
