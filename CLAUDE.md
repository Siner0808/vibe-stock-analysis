# CLAUDE.md — Bàn giao ngữ cảnh cho Claude Code

Hệ thống phân tích cổ phiếu Việt Nam. Streamlit + Python 3.11, dữ liệu từ
vnstock. Phát triển local → commit → push GitHub → Streamlit Cloud tự deploy.

> **BẮT ĐẦU Ở ĐÂY: đọc `docs/HANDOFF.md` trước tiên.**
> Ba tài liệu, ba vai trò khác nhau:
> - `docs/HANDOFF.md` — *bắt đầu từ đâu*: ba lệnh chạy đầu tiên, năm ô đang
>   chặn, ba ràng buộc khi làm việc. Ngắn, đọc hết trong 5 phút.
> - `docs/STATE.md` — *nhật ký từng Phase*: Gate nào đã qua, đo được gì,
>   cái gì chưa kiểm được.
> - `CLAUDE.md` (file này) — *kiến trúc và luật chơi*, thứ ít đổi nhất.
>
> Hai file mâu thuẫn thì file mới hơn đúng, theo thứ tự
> `HANDOFF` → `STATE` → `CLAUDE.md`.

---

## Đọc hai file này TRƯỚC KHI sửa bất cứ thứ gì liên quan tới kết quả

| File | Nội dung | Vì sao bắt buộc |
|---|---|---|
| `NGUYEN-TAC-DO-LUONG.md` | 8 bất biến đo lường | Dự án đã **5 lần** cho ra số đẹp mà sau đó hoá ra vô nghĩa (+22,42% · +14,88% · +14,24% · +636,11%, và lần thứ năm là chính giao diện công bố +636,11% suốt nhiều ngày — xem `docs/STATE.md`). Không lần nào cố ý — đều là lỗi kỹ thuật nhỏ, và **lỗi đo lường gần như không bao giờ làm kết quả xấu đi**. |
| `MO-XE-KIEN-TRUC.md` | Đo thực tế 573 phiên | Cho biết thành phần nào đang thật sự chạy, thành phần nào là trang trí. |

**Quy tắc số 1: nếu một thay đổi làm con số đẹp lên đáng kể, giả định đầu
tiên phải là có lỗi.**

`AGENTS.md` do vnstock tự đồng bộ nên **sẽ bị ghi đè** — đừng đặt luật dự án
ở đó. Luật nằm ở `NGUYEN-TAC-DO-LUONG.md` và file này.

---

## Sự cố 12/08/2026 — đã xử lý xong, giữ lại để không lặp lại

Commit `e2f98b4` **ghi đè sổ lệnh thật bằng kết quả backtest in-sample**:
96/113 lệnh thật biến mất, vị thế ACB đang mở (tín hiệu 27/05, khớp 29/05,
giá 21.110) bị xoá. Nguyên nhân: ba script tối ưu kết thúc bằng
`os.remove("paper_trades.db")` rồi seed lại bằng vòng lãi cao nhất trong 20
vòng chạy trên cùng dữ liệu.

Đã khôi phục và dọn xong: không còn `.db` nào bị git theo dõi,
`backtest/cache/` đã gỡ khỏi index, sổ in-sample đổi tên thành
`paper_trades_seeded_insample.db`.

**Đường dẫn tới sự cố đã bị đóng (19/08/2026):** gác chống ghi đè nay nằm
trong `PaperTradingJournal.__init__`, mặc định **từ chối** — mở
`paper_trades.db` phải khai báo `cho_phep_so_that=True`. Bản cũ đặt gác ở
phía người gọi và truyền hằng số tên file scratch, nên nó không bao giờ có
thể kích hoạt.

---

## Trạng thái đo được — đọc trước khi đề xuất tính năng mới

Trên 573 phiên của 10 mã (2021-10 → 2026-08):

- **Điểm cuối không dự báo được lợi nhuận.** rho = −0,019 với lợi nhuận 20
  phiên sau, KTC 95% [−0,100 ; +0,064]. Walk-forward alpha −0,36%.
- **2 agent là hằng số** (`news` 1 giá trị, `momentum` luôn trả 0 — giá trị
  65 đến từ dòng ghi đè trong `master_agent.py`).
- **2 agent là công tắc 3 nấc** (`trend`, `sr` — mất 4/5 luật vì thiếu
  TradingView).
- **2 agent còn tín hiệu**: `volume` (12 giá trị), `risk` (9 giá trị).
- **Tầng tranh luận điều chỉnh ±0,9 điểm** trên thang 100, trung bình −0,00.
  **Safety Harness kích hoạt 0%.** Bỏ hẳn cả hai: 572/573 phiên cho cùng
  quyết định.

**Hệ quả cho việc lập kế hoạch:** thêm agent hoặc thêm tầng vào một hệ có
rho ≈ 0 thì không cải thiện được gì. Nguyên nhân gốc là **thiếu dữ liệu độc
lập**, không phải thiếu logic. Sáu agent hiện tại đều tính từ cùng một chuỗi
giá nên về lý thuyết không tạo được thông tin ngoài thứ đã có trong chuỗi đó.
Hướng đúng: BCTC theo quý, giao dịch nội bộ, khối ngoại mua ròng —
`financial_collector.py` đã có sẵn đường lấy dữ liệu.

Lưu ý phạm vi: các agent "chết" ở trên là chết **trong backtest/paper
trading** vì không có lịch sử TradingView và tin tức. Trên app chạy trực tiếp
chúng sẽ sống dậy — nhưng khi đó lại không đo được. Đây là mâu thuẫn cốt lõi
của dự án: *phần đo được thì không có tín hiệu, phần có thể có tín hiệu thì
không đo được.*

---

## Ranh giới không vượt qua

- **Không đặt lệnh thật.** Agent chuẩn bị → người xác nhận → người đặt lệnh.
- **Không commit secrets.** Key nằm ở `.streamlit/secrets.toml` (đã gitignore).
- **Không commit trạng thái chạy.** `*.db`, `sl_pattern_memory.json`,
  `backtest/cache/` — ghi đè `paper_trades.db` bằng kết quả in-sample là xoá
  mất bằng chứng duy nhất chưa bị tối ưu chạm vào. Đã xảy ra một lần rồi.
- **App không được tự push lên repo nó đang chạy.** Streamlit Cloud redeploy
  mỗi lần có push → sẽ thành vòng lặp.

## Bẫy triển khai Streamlit Cloud

Ổ đĩa **tạm**: app ngủ khi không dùng, redeploy mỗi lần push, và mọi file app
tự ghi ra đều mất. `st.session_state` và `@st.cache_data` chỉ nằm trong RAM.

Hệ quả với `paper_trades.db`: trên cloud app khởi động với bản .db được
commit, nhưng mọi lệnh ghi sau đó **không sống sót**.

**Đã dựng kho ngoài: `sheets_store.py`.** SQLite vẫn là máy chạy, Google
Sheets là kho bền. Không đồng bộ hai chiều — hai chiều sinh xung đột, mà
xung đột trên sổ lệnh nghĩa là mất bằng chứng.

| Bảng | Cách đẩy | Vì sao |
|---|---|---|
| `decisions` | chỉ thêm dòng có `seq` lớn hơn | bảng chỉ-thêm, 9.002 dòng, không ghi lại |
| `trades` | soi gương toàn phần | lệnh đổi trạng thái và stop_loss được nâng |

Bốn bất biến, khoá bởi `tests/test_sheets_store.py` (14 test, chạy offline
không cần mạng lẫn credential nhờ `InMemorySheet`):

1. `pull()` **từ chối** ghi vào sổ đang có dữ liệu, trừ khi
   `allow_overwrite=True` — đúng cách 96/113 lệnh biến mất ngày 12/08
2. lệch cấu trúc cột thì **nổ**, không đoán
3. `id` và `seq` giữ nguyên khi khôi phục — đánh số lại làm lần đẩy sau
   nhân đôi dữ liệu
4. vòng đẩy–kéo không mất gì, kể cả NULL cột chữ và chuỗi rỗng (hai nghĩa
   khác nhau của ô trống, khai báo tách bạch ở `_NULLABLE_TEXT_COLS`)

Đã kiểm trên sổ thật: 113 lệnh + 9.002 decisions đẩy–kéo ra **giống hệt
từng bản ghi**.

Cấu hình ở `.streamlit/secrets.toml` (`GOOGLE_SHEET_KEY` +
`[gcp_service_account]`); hướng dẫn dựng 6 bước nằm trong
`secrets.toml.example`. Không cấu hình thì tắt sạch, app chạy như cũ.
`run_daily.py` tự đẩy cuối mỗi phiên quét; tab Sổ lệnh có nút đẩy tay và
hiện trạng thái kho.

## Quét tự động — nay chỉ còn MỘT nơi (21/08/2026)

| Nơi | Nhịp khai báo | Trạng thái |
|---|---|---|
| Task Scheduler (`VibeStock_QuetPhien`) | 09:10 → 15:10, mỗi 30 phút, T2–T6 | **Disabled** — chạy lần cuối 20/08 lúc 10:40 |
| GitHub Actions (`quet-so-lenh.yml`) | `0,30 2-4` và `0,30 6-8` UTC, T2–T6 | đang chạy |

Đo lại trên 35 nhịp (13→21/08/2026), thay cho con số "~1/7" ghi ngày
14/08 — con số đó đo trên một ngày duy nhất và **sai**:

```
Ngày làm việc đủ (17→20/08) : 6/12 nhịp mỗi ngày  = 50%
Toàn giai đoạn              : 32/84               = 38%
Nổ đúng phút đã hẹn         : 1/32 lần
Trễ điển hình               : 5 → 90 phút
```

Ba hệ quả, cái thứ ba quan trọng nhất:

1. **Mất khoảng một nửa số nhịp.** GitHub gộp nhịp trễ: nhịp sau tới khi
   nhịp trước chưa chạy thì nhịp trước bị bỏ.
2. **Việc né giờ nghỉ trưa không còn hiệu lực.** Cron cố tình bỏ trống
   giờ 05 UTC (11:30–13:00 ICT), nhưng nhịp 04:30 bị trễ đã rơi vào
   05:03, 05:04, 05:25 và 05:56 UTC — tức 12:03 → 12:56 giờ VN.
3. **"Giờ lệch nhau 10 phút để tránh chạy trùng" là bảo vệ tưởng tượng.**
   Với sai số ±90 phút, hai nơi có thể chạy chồng bất cứ lúc nào. Cơ chế
   `concurrency` trong workflow chỉ ngăn Actions chồng Actions, nó không
   biết gì về máy local. Cái thật sự giữ an toàn là kéo-trước-khi-quét
   cộng chốt chặn trong `push()`, không phải khoảng lệch giờ.

**Điều đang còn đúng: mỗi ngày đều có ít nhất một lượt quét sau giờ đóng
cửa.** 4/4 ngày có lượt chạy trong 15:29 → 15:33 giờ VN (đóng cửa 15:00).
Vì `evaluate_open()` chấm trên nến NGÀY, lượt sau đóng cửa là lượt quyết
định — nhịp trong phiên chủ yếu để thấy sớm, không đổi kết quả.

Đó là lý do tắt Task Scheduler chấp nhận được. Nhưng nó cũng nghĩa là
**không còn lưới dự phòng**: một ngày mà mọi lượt Actions đều hỏng thì
ngày đó không được quét.

**Đã có chuông (21/08/2026):** `.github/workflows/chuong-bao-quet.yml`
chạy 09:00 UTC (16:00 ICT) mỗi ngày làm việc, soát **ba** ngày làm việc
gần nhất và để lượt chạy đỏ nếu ngày nào không có lượt quét thành công
nào. Soát ba ngày vì chính chuông cũng chạy bằng cron GitHub và cũng bị
rơi nhịp — một nhịp chuông rơi thì nhịp hôm sau vẫn bắt được. Cửa sổ im
lặng thu từ một nhịp xuống ba nhịp liên tiếp, không xuống 0.

### Ba kiểu hỏng của một lượt Actions — chỉ kiểu đầu là ồn ào

| Kiểu | `status` / `conclusion` | Có báo không |
|---|---|---|
| Chạy rồi hỏng | `completed` / `failure` | ✅ đỏ, GitHub gửi email |
| Nhịp bị rơi | không có lượt nào | ❌ im — chuông bắt |
| **Kẹt hàng đợi** | `queued` / `None` | ❌ im hoàn toàn |

Kiểu thứ ba tìm ra ngày 21/08: lượt 19/08 lúc 04:08 UTC vẫn `queued` sau
hai ngày, chưa từng chạy. Không đỏ nên không có email, không xanh nên
không quét được gì. Vì thế chuông chỉ đếm `conclusion == "success"` —
`queued` và `cancelled` đều KHÔNG được coi là đã quét.

**Điều kiện để hai nơi cùng ghi mà không hỏng: PHẢI kéo từ Sheets trước
khi quét.** `run_daily.py` làm việc đó ngay đầu `execute_daily_scan()`.

Không kéo trước thì mỗi nơi đánh số `seq` theo sổ riêng. Ví dụ thật ngày
14/08: sheet ở seq 9.422, sổ máy kẹt ở 9.142. Máy quét xong sinh seq
9.143–9.212, mà `push()` chỉ đẩy dòng có seq > 9.422 — **70 quyết định vừa
ghi bị bỏ qua lặng lẽ**. Không nổ, không log, chỉ mất.

Kéo hỏng thì `run_daily.py` **dừng phiên quét** chứ không quét tiếp trên sổ
cũ rồi đẩy đè lên dữ liệu mới hơn.

Ngược lại, Config ngưỡng nên nằm trong repo dưới dạng file: git chính là cơ
chế versioning, và việc app không ghi được vào đó lại đúng với nguyên tắc
"luật chỉ đổi khi qua kiểm định".

---

## Lệnh hay dùng

```bash
streamlit run app.py              # chạy app
python run_daily.py               # quét VN100, cập nhật sổ lệnh
python paper_runner.py            # chạy paper trading
python extend_history.py --check  # kiểm tra độ phủ dữ liệu

pytest tests/ -q                          # toàn bộ test
pytest tests/test_post_mortem.py          # khoá tính tái lập của chấm điểm
python tools/chan_bia_so_lieu.py --quet-repo   # quét mẫu bịa số toàn repo
```

**`walkforward_vn100.py` đã đổi đuôi thành `.broken` (20/08/2026)** — bản
thay thế là **`walkforward.py`**. Đừng dùng file cũ làm nguồn
số "ngoài mẫu". Nó chạy `run_simulation` **một lần** trên toàn khoảng rồi lọc
`exit_date` để gọi là OOS; ngưỡng 50,0 nhập sẵn thay vì chọn trên in-sample;
mốc chia là `datetime.now() - 182 ngày` nên OOS luôn là giai đoạn **gần nhất**
— đúng giai đoạn đã bị hàng trăm vòng loop nhìn qua (bất biến 8). Nó còn
`os.remove("sl_pattern_memory.json")` ngay khi khởi động. Bản đúng ở
`git show 025507c`.

Hai test đang khoá bất biến quan trọng, đừng làm hỏng:
- `tests/test_post_mortem.py::test_cham_diem_khong_doi_khi_chay_lai` — cùng
  input phải ra cùng điểm
- `tests/test_paper_trading.py::test_duong_von_khong_phu_thuoc_thu_tu_ban_ghi`
  — drawdown dựng theo thời gian, không theo id

## Hook chặn bịa số liệu — chạy tự động

`.claude/settings.json` đăng ký `tools/chan_bia_so_lieu.py` làm PostToolUse
hook: sau mỗi Write/Edit, file được phân tích bằng AST và **chặn** nếu thấy
mẫu đã làm hỏng dự án này.

| Luật | Mức | Mẫu |
|---|---|---|
| R1 | CHẶN | `getattr(o, "tên", <số>)` — mặc định là con số |
| R2 | CHẶN | tên trường không tồn tại nhưng rất giống trường thật |
| R3 | CHẶN | `except … → return <số>` — nuốt lỗi rồi thay bằng số |
| R4 | cảnh báo | `.get("k", <số khác 0/1/100>)` |
| R5 | cảnh báo | `x = max(x, <số>)` |

Cửa thoát: `# bia-ok: <lý do>` trên chính dòng đó hoặc trong khối chú thích
ngay trên. **Bắt buộc có lý do** — `# bia-ok:` rỗng bị từ chối. Mục đích
không phải cấm, mà là buộc nói ra vì sao con số này không phải bịa.

Miễn trừ: `tests/`, `scratch/`, `.venv/`, và mọi file ngoài gốc dự án.

Hook từng tìm ra chính lỗi nó sinh ra để chặn — `getattr(t,
'position_size_pct', 30)` ở `app.py` và `run_daily.py`. **Đã sửa xong**, cả
hai file nay dùng `t.size_pct` thật.

**Hai giới hạn của hook, phải biết:** nó là `PostToolUse` nên chạy *sau* khi
ghi (chuông báo cháy, không phải cửa chống cháy), và matcher chỉ bắt
`Write|Edit` của Claude Code — sửa từ IDE, Antigravity, tay người,
`git checkout`, `git merge` đều không kích hoạt. Vì thế có
`--quet-repo` để CI quét toàn bộ; xem `.github/workflows/kiem-dinh.yml`.

## Kiểm tra định kỳ những chỗ hỏng âm thầm

```python
market_filter.status()        # bộ lọc VN-INDEX có thật sự bật không
data_quality.price_multiplier()  # vnstock trả nghìn đồng vs agent trả VNĐ
```

---

## Sơ đồ kiến trúc — cái nào nói thật

| File | Là gì |
|---|---|
| `architecture_diagram.html` (v1) | Bản mô tả tham vọng ban đầu |
| `architecture_diagram_v2.html` | Bản đã vá 7 lỗ hổng thiết kế |
| **`architecture_asbuilt.html`** | **Thứ đo được khi chạy thật — dùng cái này để đối chiếu** |

Ba bản đầu mô tả thứ *nên* chạy. Chỉ bản as-built mô tả thứ *đang* chạy.
Khi hai bên lệch nhau, bản as-built đúng.
