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
commit, nhưng mọi lệnh ghi sau đó **không sống sót**. Nếu cần vòng học chạy
được trên cloud, dữ liệu phải đẩy ra dịch vụ ngoài (Google Sheets qua
gspread là lựa chọn đã bàn — miễn phí, mở ra soi tay được).

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
