# CLAUDE.md — Bàn giao ngữ cảnh cho Claude Code

Hệ thống phân tích cổ phiếu Việt Nam. Streamlit + Python 3.11, dữ liệu từ
vnstock. Phát triển local → commit → push GitHub → Streamlit Cloud tự deploy.

---

## Đọc hai file này TRƯỚC KHI sửa bất cứ thứ gì liên quan tới kết quả

| File | Nội dung | Vì sao bắt buộc |
|---|---|---|
| `NGUYEN-TAC-DO-LUONG.md` | 8 bất biến đo lường | Dự án đã 3 lần cho ra số đẹp mà sau đó hoá ra vô nghĩa (+22,42% · +14,88% · +14,24%). Không lần nào cố ý — đều là lỗi kỹ thuật nhỏ, và **lỗi đo lường gần như không bao giờ làm kết quả xấu đi**. |
| `MO-XE-KIEN-TRUC.md` | Đo thực tế 573 phiên | Cho biết thành phần nào đang thật sự chạy, thành phần nào là trang trí. |

**Quy tắc số 1: nếu một thay đổi làm con số đẹp lên đáng kể, giả định đầu
tiên phải là có lỗi.**

`AGENTS.md` do vnstock tự đồng bộ nên **sẽ bị ghi đè** — đừng đặt luật dự án
ở đó. Luật nằm ở `NGUYEN-TAC-DO-LUONG.md` và file này.

---

## Việc đang dở — làm trước tiên

Phiên 13/08/2026 phát hiện commit `e2f98b4` đã **ghi đè sổ lệnh thật bằng kết
quả backtest in-sample**: 96/113 lệnh thật biến mất, vị thế ACB đang mở
(vào 27/05, giá 21.110) bị xoá.

Bản sạch đã trích sẵn ra `paper_trades_RECOVERED_e9c5113.db` (113 lệnh,
9.002 decisions). `.gitignore` đã sửa `paper_custom*.db` → `*.db`.

Còn lại phần git chưa chạy:

```bash
del .git\index.lock        # lock cũ còn sót, chặn mọi lệnh git
del __probe.txt            # file rác

git rm --cached paper_trades.db
ren paper_trades.db paper_trades_seeded_insample.db
ren paper_trades_RECOVERED_e9c5113.db paper_trades.db

git add .gitignore
git commit -m "fix: go paper_trades.db khoi git, khoi phuc so lenh that"
```

Ngoài ra `backtest/cache/` có trong `.gitignore` nhưng **23 file vẫn đang bị
track** (gitignore không áp dụng cho file đã track). Cần `git rm --cached -r
backtest/cache/` nếu muốn dứt điểm.

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

## Quét tự động — HAI nơi cùng chạy

| Nơi | Nhịp | Chạy khi |
|---|---|---|
| Task Scheduler (`VibeStock_QuetPhien`) | 09:10 → 15:10, mỗi 30 phút, T2–T6 | máy bật |
| GitHub Actions (`.github/workflows/quet-so-lenh.yml`) | `*/30 2-8 * * 1-5` UTC | luôn luôn |

Đo ngày 14/08/2026: lịch GitHub chỉ nổ ~1/7 nhịp — nó là "cố gắng hết sức",
ưu tiên thấp, bỏ nhịp khi tải cao. Máy chạy đúng phút nhưng cần bật. Hai
nơi bù cho nhau. Giờ lệch nhau 10 phút để tránh chạy trùng.

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
python walkforward_vn100.py       # walk-forward (chọn tham số 1 khoảng, đo khoảng khác)
python extend_history.py --check  # kiểm tra độ phủ dữ liệu

pytest tests/ -q                  # toàn bộ test
pytest tests/test_post_mortem.py  # khoá tính tái lập của chấm điểm
```

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

Hook tìm ra chính lỗi nó sinh ra để chặn: `getattr(t, 'position_size_pct',
30)` còn sống ở `app.py` (2 chỗ) và `run_daily.py` — luôn trả 30 cho mọi vị
thế, trong khi chỉ 5/113 lệnh thật có `size_pct = 30`.

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
