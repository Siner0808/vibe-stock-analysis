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

> **Đã đi được một bước theo hướng đó (22/08/2026):** `fundamental_agent.py`
> đọc BCTC thật và hiện lên giao diện. Nhưng **trọng số của nó bằng 0**, nên
> nó CHƯA thay đổi con số nào ở trên. Đọc mục "Agent Cơ Bản" bên dưới trước
> khi định bật — bật rồi thấy lãi tăng là kịch bản của quy tắc số 1, không
> phải bằng chứng.
>
> **Phép đo ĐÃ CHẠY (23/08/2026) — và nó nói ĐỪNG bật.** Cache BCTC nay là
> 71 mã × 34 kỳ (hạng silver), nhưng cache GIÁ chỉ lùi tới 2021-10 nên còn
> **19 kỳ dùng được**. Kết quả trên 1.267 quan sát:
>
> | | IC TB | sau Bonferroni (5 chỉ số) |
> |---|---|---|
> | roe · roa | +0,027 · −0,040 | chứa 0 — **0/12 ô lưới có tín hiệu** |
> | leverage | **+0,100** | chứa 0 (7/12 ô, bền nhất) |
> | growth_profit | −0,077 | chứa 0 |
> | earnings_yield | +0,025 | chứa 0 |
>
> **Không chỉ số nào sống sót qua Bonferroni.** Nặng hơn thế: `leverage`
> dương và `growth_profit` âm đều **ngược dấu** với cách agent chấm
> (`_cham_an_toan` trừ 8 điểm cho nợ vay cao, `_cham_tang_truong` cộng 10
> cho tăng trưởng tốt). Còn ROE — thứ `_cham_sinh_loi` cộng tới 12 điểm —
> là nhiễu ở cả 12 ô lưới. Bật trọng số dương là đẩy điểm ngược hướng dữ
> liệu. Lý do để trọng số bằng 0 nay là *đã đo, và phép đo không ủng hộ*.
>
> Điều kiện xem lại: cache giá lùi được về 2018 (19 kỳ → ~30), hoặc rổ có
> thêm mã đã huỷ niêm yết. KHÔNG phải chạy lại với tham số khác cho tới khi
> ra số đẹp. Chi tiết và 12 ô lưới: `docs/STATE.md`, mục 23/08/2026.

Lưu ý phạm vi: các agent "chết" ở trên là chết **trong backtest/paper
trading** vì không có lịch sử TradingView và tin tức. Trên app chạy trực tiếp
chúng sẽ sống dậy — nhưng khi đó lại không đo được. Đây là mâu thuẫn cốt lõi
của dự án: *phần đo được thì không có tín hiệu, phần có thể có tín hiệu thì
không đo được.*

---

## Pha Wyckoff và Agent Cơ Bản — hai ô từng bị gỡ vì không có thật

Ngày 21/08/2026 hai thứ trên giao diện bị gỡ vì chúng hứa một thành phần
không tồn tại: nhãn `Pha C — Wyckoff Spring` (thật ra là điểm số chia bốn
khoảng) và ô `Fundamental Agent · BCTC Q2` (thật ra `grep -rn "fundamental"
master_agent.py` trả về rỗng). Ngày 22/08/2026 cả hai được trả lại, lần này
có mã nguồn đứng sau.

### `pha_wyckoff.doc_pha(df, he_so_gia)`

Hàm thuần, không đọc file trạng thái, không gọi mạng. **KHÔNG tham gia chấm
điểm** — nó là một lớp đọc bối cảnh.

Ba chỗ dễ sửa sai, đều đã có test và đột biến canh:

1. **Biên vùng dựng từ phần `nền`, sự kiện tìm ở phần `gần đây`.** Hai phần
   không giao nhau. Lấy min/max trên cả đoạn thì chính cây thủng sâu nhất
   định nghĩa ra cái sàn, nên `low < san` không bao giờ đúng — bộ nhận dạng
   không bao giờ kêu mà vẫn xanh.
2. **Cửa sổ tìm cao trào chặn cả hai đầu.** Bỏ chặn trái, đo trên dữ liệu
   thật: "vùng dao động" rộng 96% ở VHM, 61% ở SSI.
3. **`_doi_chieu_boi_canh()` chạy trên cấu trúc ĐÃ KẾT LUẬN, không trên
   hướng điểm neo.** Bản đầu làm ngược và smoke test ACB lôi ra: nhãn hiện
   "TÍCH LUỸ · đã xác nhận" ngay trên dòng bằng chứng ghi "cao trào MUA".

Tỷ lệ "chưa đủ bằng chứng" cao (20/40 mã VN100) là **đúng kỷ luật của
phương pháp**. Đừng nới ngưỡng cho ra nhãn đẹp hơn — đó đúng là cách cái
nhãn cũ ra đời.

### `fundamental_agent.FundamentalAgent`

Đọc bảng `ratio` theo năm từ vnstock/KBS. Bốn cái bẫy đã ghi ở đầu file đó;
quan trọng nhất: **`total_assets`, `owners_equity`,
`profit_after_tax_...` trong bảng ratio là TĂNG TRƯỞNG %, không phải số dư**
(FPT 2022 cho `total_assets = -3,81`), và **ngân hàng có bộ chỉ tiêu khác
hẳn** (không có `net_margin`, `debt_to_equity`, `interest_coverage`).

**HAI cái van, đừng nhầm chúng với nhau:**

| Van | Mặc định | Mở ra thì sao |
|---|---|---|
| `master_agent.TRONG_SO_CO_BAN` | `0.0` | Điểm cơ bản bắt đầu dịch điểm giao dịch. Đây là quyết định ĐO LƯỜNG, và phép đo đã chạy 23/08/2026: 19 kỳ dùng được, không chỉ số nào sống sót qua Bonferroni, hai khối chấm điểm ngược dấu dữ liệu. |
| `MasterConsensusAgent(doc_co_ban=...)` | `False` | **Đây là rào chắn chống nhìn trộm, không phải công tắc hiệu năng.** Bảng chỉ số theo năm là trạng thái HIỆN TẠI, đã gồm điều chỉnh hồi tố, không kèm ngày công bố. Bật cho `backtest/engine.py` hay `paper_runner.py` là chấm phiên 2022 bằng số liệu 2025. |

`run_full_analysis()` — đường phân tích một mã tại hiện tại — là chỗ DUY
NHẤT bật `doc_co_ban=True`.

Điểm cơ bản tham gia theo dạng **cộng lệch** `(điểm − 50) × trọng số`, cố ý
không trộn vào bộ trọng số động phía trên: trọng số 0 cho ra đúng con số như
trước khi có agent này, và điều đó kiểm được bằng mắt.

---

## Năm màu bảng giá — `mau_bang_gia.py`

Bảng giá Việt Nam có **năm** màu, và ba trong số đó là kết luận chứ không
phải phép so sánh:

| màu | trạng thái | biến |
|---|---|---|
| tím `--c-p` | giá TRẦN | `bg-tran` |
| xanh lá `--c-g` | tăng | `bg-tang` |
| vàng cam `--c-a` | tham chiếu | `bg-tc` |
| đỏ `--c-r` | giảm | `bg-giam` |
| xanh lam `--c-b` | giá SÀN | `bg-san` |

**Không bao giờ suy ra trần bằng ngưỡng phần trăm.** Đo phiên 21/08/2026:
SSI trần ở **+6,96%**, còn SHS tăng **+8,16%** mà KHÔNG trần. Mọi ngưỡng
cứng tô sai ít nhất một trong hai. Trần là `tham_chiếu × (1 + biên)` làm
tròn xuống theo bước giá, biên khác nhau theo sàn, và tham chiếu KHÔNG phải
`close.iloc[-2]` vào ngày giao dịch không hưởng quyền.

Sở công bố sẵn cả ba con số — `Trading(source="vci").price_board([ma])` trả
`listing/ceiling`, `listing/floor`, `listing/ref_price`, `listing/trading_date`.
Module này ĐỌC chúng và cố ý **không có hàm tính trần**.

Hệ quả đã chọn: **không đọc được bảng giá thì không được nói trần/sàn**,
tụt xuống ba màu. Bảng giá còn phải chứng minh được là của ĐÚNG phiên đang
hiện (chặn ngày), và giá đóng cửa phải nằm trong biên độ nhận được (điều
kiện phủ định) — sáng thứ Hai bảng đã lật sang phiên mới trong khi nến vẫn
là thứ Sáu.

Phần trăm hiển thị đi theo **tham chiếu đang dùng**, không theo
`close.iloc[-2]`. Dùng lẫn thì màu và số nói hai chuyện khác nhau về cùng
một phiên.

### Ô VN-Index trên topbar

Gọi `market_filter.chi_so_moi_nhat()`, KHÔNG phải `get_vni_df()`. Hai đường
cố ý khác nhau: bộ lọc ưu tiên cache trên đĩa (backtest phải tất định),
topbar ưu tiên mạng (phải là phiên gần nhất). Đo 22/08/2026: cache 1.734,24
(20/08) vs mạng 1.768,12 (21/08). Nhãn ô luôn kèm **ngày phiên** để số cũ
không giả dạng số mới.

---

## Gác phải đọc AST, không đọc `in`

Ngày 22/08/2026 hai gác mới viết bằng `"chi_so_moi_nhat" in src` được đem
đục thử — xoá hẳn lời gọi trong thân hàm — và **cả hai vẫn xanh**, vì tên
đó còn nằm trong khối chú thích ngay phía trên.

Càng viết chú thích kỹ thì gác kiểu `in` càng dễ vô hiệu. Mọi khẳng định
"file X CÓ GỌI Y" phải đi qua `_ten_da_nhap_va_goi()` trong
`tests/test_no_fabricated_data.py`. Gác dạng văn bản chỉ còn dùng cho thứ
thật sự là văn bản — CSS nằm trong chuỗi, chẳng hạn.

Một công cụ kiểm tra không chạy được cũng là cổng xanh giả: cùng ngày,
`tools/kiem_ban_sach.py` nổ `UnicodeEncodeError` ngay dòng print đầu tiên
vì thiếu `encoding="utf-8"` trong `sys.stdout.reconfigure`.

### Test KIỂM LẠI CHÍNH NÓ — lỗi mắc BA LẦN trong ngày 31/08/2026

Khác với lỗi `in` ở trên, và nguy hiểm hơn vì nó trông đúng hoàn toàn.

Mẫu: test **dựng lại công thức của mã** rồi so hai bên. Nó kiểm công thức
của test, không kiểm công thức của mã — nên mọi đột biến giữ nguyên GIÁ TRỊ
tại điểm đang thử đều sống sót.

| Lần | Đột biến sống sót | Vì sao lọt |
|---|---|---|
| `theo_ngay` | nhánh mới thành no-op, chạy lại vòng theo mã | test kiểm `lich_theo_ngay` như hàm THUẦN, không kiểm nhánh CÓ GỌI nó |
| sizing | `TRAN * N / 225` — cho đúng 6,667 tại N=15 | test tự dựng lại công thức; mọi phép so giá trị đều mù, kể cả `CỠ × N == TRẦN` |
| hook | matcher đổi thành `NotebookEdit` | test đọc `command`, bỏ qua `matcher` — hook tồn tại nhưng không nối vào đâu |

Cả ba đều **chỉ đột biến mới tìm ra**. Không lần nào bộ test tự phát hiện.

**Quy tắc rút ra: gác một phép SUY RA thì phải kiểm HÌNH DẠNG biểu thức
bằng AST, không kiểm giá trị nó cho ra.** Giá trị trùng nhau tại một điểm
là chuyện thường; cấu trúc sai thì sai ở mọi điểm khác.

```python
v = _gan("CO_MUC_TIEU_PCT")                       # ast.Assign -> value
assert isinstance(v.op, ast.Div)                  # CHIA, không phải NHÂN
assert v.left.id == "TRAN_VON_CAM_KET_PCT"
assert v.right.id == "SO_VI_THE_MUC_TIEU"
```

Và hệ quả thứ hai: **viết đột biến TRƯỚC khi tin một gác mới.** Ba lần trên
đều là gác vừa viết xong, vừa xanh, và vừa vô dụng.

### Hook KHÔNG thấy gì đi qua Bash — và quy ước của dự án đi đúng đường đó

`PostToolUse` khớp `Write|Edit`. Nhưng quy ước "vá lớn thì viết một file
`.py` rồi chạy nó" (xem mục CRLF) đi qua **Bash**. Quy ước tự vô hiệu hoá
cái gác của chính nó.

Đo ngày 31/08/2026: một phiên sửa 6 file mà hook không chạy lần nào.
`--quet-repo` có được gọi, nhưng vì người nhớ ra chứ không vì máy bắt.

**Đã đóng:** hook `Stop` chạy `chan_bia_so_lieu.py --quet-thay-doi` — quét
chỉ file git báo đã đổi, 0,5 giây thay vì 24. Cửa sổ im lặng thu từ "tới
lúc push" xuống "tới lúc dừng phiên". CI vẫn quét toàn repo.

Khoá bởi `tests/test_hang_rao_tu_dong.py`, và test đó kiểm CẢ MATCHER —
xem bảng trên.

Lỗi đó tái diễn hai lần nữa (`experiment_fundamentals.py` 23/08, `extend_history.py`
24/08 — cả hai đều là công cụ đo lường). Từ 24/08 có gác toàn repo:
`tests/test_script_chay_duoc_tren_windows.py` — mọi file có `__main__` và có
`print` đều phải gọi `reconfigure`, xác nhận bằng AST. Test **import** module
chứ không **chạy** nó, nên không lần nào có test đỏ.

---

## Hạng gói vnstock — thứ đã mua khác thứ đang chạy

Ngày 22/08/2026: tài khoản Silver (hạn 22/11/2026), app chạy như gói miễn
phí. **BCTC bị cắt còn 8/34 kỳ, hạn mức 60 thay vì 300 req/phút.** Không lỗi,
không cảnh báo.

Gốc ở `vnai/beam/auth.py`: `_detect_tier()` gọi `_check_vnii_tier()`, package
`vnii` chưa cài nên `ImportError` bị nuốt và hàm rơi xuống `return "free"`.
Việc cắt số kỳ nằm ở `vnai/beam/fundamental.py`, `PERIOD_LIMITS['free'] = 8`
còn `['silver'] = None` (không giới hạn) — **máy chủ vẫn gửi đủ, vnai cắt tại
máy**.

`vnstock_goi.kiem_goi()` hỏi máy chủ rồi so với hạng cục bộ. Ba trạng thái:
`KHỚP` / `LỆCH` / `CHƯA KIỂM ĐƯỢC`. Trạng thái thứ ba bắt buộc — mất mạng mà
trả "khớp" thì phép kiểm này thành đúng thứ nó sinh ra để bắt.

**Không bao giờ ép hạng trong mã nguồn.** Ghi `authenticator._cached_tier =
"silver"` sẽ làm app tiếp tục khẳng định silver sau ngày hết hạn rồi cắt dữ
liệu sai mà không ai biết.

### Đã cài xong (22/08/2026) — hai bước, bước hai không hiển nhiên

Bốn gói **không có trên PyPI công khai**. Đường thật, đọc ra từ mã của `vnii`:

```
GET  /api/packages                      # công khai: vnii + vnstock-installer
GET  /api/vnstock/packages/list         # Bearer <key> -> accessible / locked
POST /api/vnstock/packages/download     # -> downloadUrl
```

`vnstock_pipeline` **bị KHOÁ ở hạng silver** — `license/verify` liệt kê nó
nhưng `packages/list` mới là bảng đúng. Tệp tải về mang tên `.whl` nhưng nội
dung là sdist `.tar.gz`; tên thật nằm trong header gzip.

1. **`vnii`** sửa việc nhận diện hạng. Cài là xong.
2. **`vnstock_data` và `vnstock_ta` vẫn ném `SystemExit` khi import** cho tới
   khi có `~/.vnstock/user.json`. Phép kiểm ở `vnstock_ta/utils/env.py::idv()`
   chỉ đòi tệp đó tồn tại với trường `user` khác rỗng — một tệp đánh dấu đã
   chạy setup, do `vnstock_installer.api.create_user_info()` tạo (mặc định ghi
   `"user": "vnstock_installer"`). `vnii` ghi `auth_state.json`, **không** ghi
   `user.json`.

`fetch_fundamentals.py` tự tải lại cả rổ khi hạng đổi, nhờ sổ tay
`_hang_da_tai.json`. Không có sổ tay đó thì 60 file CSV tải lúc hạng free ở
lại vĩnh viễn với 8 kỳ — đúng cái bẫy `download()` trong
`NGUYEN-TAC-DO-LUONG.md`.

### KHÔNG đổi `import vnstock` sang `import vnstock_data` mà chưa đo

Banner của thư viện giục đổi. Đổi thì được, nhưng nó **thay đổi con số**,
không chỉ thay đổi cách gọi. Đo ngày 23/08/2026 (chi tiết trong
`docs/STATE.md`):

| | `vnstock` (đang dùng) | `vnstock_data` 3.2.8 |
|---|---|---|
| hình dạng bảng | rộng: `item_id` × cột năm | dài: `period·id·name·unit·value` |
| khoá | `roe` | `RT_PRT_ROE` |
| **ROE của FPT 2025** | **23.59** | **0.2359** (nhãn vẫn ghi `%`) |
| KBS: chỉ tiêu có số (2025) | 58/58 | 10/60 — VCI được 45/60 |
| dòng ngân hàng ở mã phi ngân hàng | không có | **0.0**, không phải NaN |

Ba hàng cuối đều hỏng ÂM THẦM. Lệch 100 lần làm mọi mã đọc ra "ROE thấp";
KBS mất chỉ tiêu buộc phải đổi nguồn sang VCI (tức đổi NGUỒN SỐ LIỆU, thuộc
`NGUYEN-TAC-DO-LUONG.md`); và `RT_BANK_NIM = 0.0` làm
`fundamental_agent._doc()` chấm FPT bằng thước ngân hàng.

**Tài liệu `vnstock_3.2.8_schema_migration_reference.csv` sai ở phần `ratio`:**
33/60 mã không khớp thư viện 3.2.8 thật. Ba tiền tố bị đổi tên —
`RT_AST_*`→`RT_ASSETS_*`, `RT_BNK_*`→`RT_BANK_*`, `RT_VAL_*`→`RT_VALUE_*`.
Ba bảng còn lại khớp 100%. Bám tài liệu thì mất im lặng cả nhóm định giá,
ngân hàng và tài sản. Tệp đó thuộc khu vực thành viên — **không đưa vào repo**.

### Bất đối xứng local / CI — VĨNH VIỄN, và là chủ ý

| Nơi | Hạng | BCTC | Hạn mức | OHLCV |
|---|---|---|---|---|
| Máy local | silver | không giới hạn (đo được 34 kỳ) | 300/phút | 784 phiên / 1095 ngày |
| GitHub Actions · Streamlit Cloud | free | 8 kỳ | 60/phút | **784 phiên — y hệt** |

Cột OHLCV đo ngày 31/08/2026 trên cả hai nơi. Bất đối xứng CHỈ nằm ở BCTC
và hạn mức; lịch sử giá thì không — điều này quan trọng vì lịch sử giá là
thứ ngưỡng mua được hiệu chuẩn trên đó.

Cả hai nơi kia chạy `pip install -r requirements.txt`, mà bốn gói này không
cài được từ đó. **Khai báo chúng trong `requirements.txt` làm CI và cloud
hỏng ngay ở bước cài** — hỏng toàn bộ, kể cả phần không đụng dữ liệu tài trợ.

Hệ quả: **không mã nào ở gốc dự án được `import vnstock_data` ở mức module.**
Dùng thì import bên trong hàm, bọc `try/except`, có đường lui. Hai gác trong
`tests/test_requirements.py` khoá cả hai điều này.

`vnstock_goi.kiem_goi()` báo **LỆCH trên cloud vĩnh viễn** — đó là báo ĐÚNG.

**Tài liệu skill của vnstock KHÔNG được commit vào repo.** Giấy phép ghi rõ
*"Zero Disk Persistence… Do not save, dump, or write these files to the
user's local disk"*. Nạp lúc chạy bằng `vnai.load_skill("<slug>")`.

`vnai.setup_agent_environment()` chính là thứ ghi đè `AGENTS.md` ở gốc dự án.

---

## Sổ lệnh giấy KHÔNG phải bản ghi tích luỹ — kiểm trước khi trích số

Đo 23/08/2026: cả **113 lệnh** trong `paper_trades.db` có `created_at` nằm
trong **258 giây** ngày 07/08/2026, trong khi `signal_date` của chúng trải
2024-01-05 → 2026-06-26 (**903 ngày**). Không dòng nào ghi sau đó.
`created_at` có trong `sheets_store._COLS` nên lần khôi phục sau sự cố
12/08 giữ nguyên dấu thời gian gốc.

Sổ ấy chưa bao giờ tích luỹ một lệnh nào từ việc quét tiến về phía trước.
Bảng `decisions` thì ngược lại — vẫn chạy thật, 5.071 quyết định riêng
tháng 08/2026.

`paper_metrics.tom_tat_lo_ghi()` phát hiện việc này **từ chính dữ liệu**,
không cần thêm cột. Ba ngưỡng, và ngưỡng thứ ba mới là cái phân biệt: một
phiên bận rộn mở 20 lệnh trong 30 giây trông y hệt một lượt mô phỏng nếu
chỉ nhìn `created_at` — khác ở chỗ 20 lệnh ấy **cùng một ngày tín hiệu**.
Cảnh báo hiện ở cả `report()` lẫn tab Sổ lệnh của app; hai gác AST trong
`tests/test_no_fabricated_data.py` khoá cả hai đường.

**Hệ quả khi đọc mọi con số về sổ:** kỳ vọng +0,79%, KTC, alpha +0,090%,
drawdown — tất cả vẫn đúng như phép tính, nhưng chúng nói về **một lượt mô
phỏng**, không phải về kết quả tích luỹ qua từng phiên quét.

### Chốt lời cứng đã bị gỡ — và việc gỡ nó KHÔNG làm hỏng gì

`evaluate_open()` không còn nhánh nào so `high` với `take_profit`. Cột
`take_profit` vẫn được tính và ghi, vẫn không có gì đọc nó để ra quyết
định. Công tắc `CHOT_LOI_CUNG` (mặc định **False**) dựng ra để ĐO, không
phải để bật.

Hai lượt walk-forward đầy đủ, cùng dữ liệu, khác duy nhất công tắc:

| | ngoài mẫu | alpha | σ | nắm giữ TB |
|---|---|---|---|---|
| **TẮT** (hiện hành) | +0,616%/lệnh | −0,008% | 10,18% | 20,3 ngày |
| BẬT (luật cũ) | +0,426%/lệnh | −0,006% | 7,72% | 17,4 ngày |

Chênh lệch kỳ vọng +0,190% có KTC [−1,061 ; +1,440] — **chứa 0**. Và trên
alpha, thước quyết định của bất biến 6, hai luật **giống hệt nhau**. Phần
kỳ vọng dôi ra của bản TẮT mua bằng thời gian ở trong thị trường (dài hơn
17%), tức beta.

Thứ chốt lời cứng thật sự làm là **giảm phương sai 24%**, không phải tăng
lợi nhuận.

**Bí ẩn "19 lệnh vàng" trong sổ đã có lời giải.** Sổ thật: 19 lệnh
`TAKE_PROFIT`, 19/19 thắng, +17,23%; 93 lệnh còn lại −2,567%. Lượt BẬT
ngoài mẫu cho đúng cùng hình dạng: 55 lệnh TP, 55/55 thắng, +17,81%; 375
lệnh còn lại −2,12%. Đó không phải dấu hiệu luật cũ tốt — **đó là hình dạng
mà mọi luật chốt lời cứng đều tạo ra.**

---

## CỔNG MỞ LỆNH ĐÃ BẬT (24/08/2026) — ba thứ đi kèm, đừng tách rời

```python
paper_trading.CHO_PHEP_MO_LENH_MOI = True    # nguong 62
paper_trading.TRAN_VON_CAM_KET_PCT = 100.0
paper_metrics.dieu_kien_dong_lai()           # neu TRUOC khi co du lieu
```

**Lý do bật KHÔNG phải vì tìm thấy lợi thế.** Mọi phép đo alpha vẫn chứa số
0. Lý do là: **cấu hình chạy trực tiếp chưa bao giờ được đo**, và nó chỉ đo
được tiến về phía trước — đúng mâu thuẫn cốt lõi ghi ở đầu file này. Giữ
cổng đóng bảo đảm nó không bao giờ được đo, vì sổ 113 lệnh không phải bản
ghi tích luỹ (xem mục trên) nên bằng chứng tiến-về-trước đang là **0**.

Số học: cần 1.050 lệnh để kỳ vọng loại được số 0 (~23 năm ở nhịp 45
lệnh/năm), alpha cần 22.601 lệnh. "Chờ thêm dữ liệu rồi quyết" không phải
một lựa chọn.

**ĐÓNG LẠI KHI** ≥60 lệnh tiến-về-trước đã đóng VÀ cận trên KTC 95% của kỳ
vọng < 0. `report()` in trạng thái mỗi phiên. Đừng chế điều kiện khác sau
khi đã nhìn số — đó là bất biến 7 đổi hướng.

### Trần vốn cam kết — chặn được, nhưng CHỈ ở đường chạy thật

`avg_capital_deployed_pct` chỉ **báo cáo** sau khi việc đã rồi. Sổ thật
từng chạm **208%**. Nay `consider_entry` từ chối lệnh mới khi tổng `size_pct`
đang mở + lệnh mới > 100%, đếm cả `PENDING`.

**Trần KHÔNG chặn được gì trong backtest, và đó không phải lỗi của trần.**
`walkforward._mo_phong` chạy **theo mã** — xong toàn bộ lịch sử FPT rồi mới
sang ACB — nên tại mọi điểm quyết định chỉ có vị thế của mã đang chạy. Hệ
quả phải nhớ khi đọc số:

> Các con số đòn bẩy 145% / 524% / 1372% trong mọi báo cáo walk-forward mô
> tả một danh mục **máy chưa bao giờ thực sự nắm**. Chúng đúng như mô tả về
> độ chồng lấn theo lịch của tập lệnh, nhưng không phải quyết định máy đã
> ra — và **không ràng buộc danh mục nào kiểm định được trong máy này.**

Đo giá của trần: 386 → 390 lệnh, kỳ vọng +0,616% → +0,614%, alpha −0,008%
→ −0,011%. Không tốn gì.

### Một ngưỡng mua, một chỗ

`run_daily` **NHẬP** `BUY_THRESHOLD` từ `paper_trading`. Trước 24/08 nó cầm
`50.0` song song với `62` — cổng đóng nên hai con số chưa bao giờ gặp nhau.
Gác cấm khai báo lại, **kể cả khai đúng 62**: bản sao không sai vào ngày nó
ra đời, nó sai vào ngày bản gốc đổi và nó thì không.

### Lệnh mồ côi trong backtest

Lệnh còn mở lúc hết dữ liệu của một mã nằm lại trong DB suốt lượt chạy.
Trước khi có trần thì vô hại; có trần rồi thì chúng ăn vào hạn mức của mọi
mã sau. `dong_so_sach()` đóng sổ cuối mỗi mã — OPEN đóng ở giá phiên cuối
(`HET_DU_LIEU`), PENDING **xoá** vì chưa bao giờ khớp.

**PHẢI nhân `price_multiplier` khi gọi nó.** Quên là mọi lệnh mồ côi đóng ở
−99,90% (nghìn đồng gặp VNĐ) và kéo kỳ vọng OOS từ +0,616% xuống −0,419%.
Đã xảy ra thật. Nay hàm tự ném `ValueError` khi giá lệch quá 10 lần so với
giá vào — biên độ sàn là 7–15% một phiên nên 10 lần không thể là biến động.

---

## Ba lỗi im lặng đã đóng sau khi mở cổng (24/08/2026)

Cổng đóng thì một kết luận sai chỉ nằm trong báo cáo. Cổng mở rồi thì nó
sinh ra lệnh.

| Chỗ | Hỏng thế nào | Nay |
|---|---|---|
| `execute_daily_scan` | mã bị bỏ qua (SYNTHETIC / thiếu nến) **im lặng** — cả rổ mất nguồn ra đúng cùng báo cáo với "không có tín hiệu" | đếm theo lý do; quét dưới **một nửa** rổ thì báo động trong báo cáo phiên |
| `post_mortem_learning` | `.get("trend_score", 50)` — toạ độ bịa vẫn khớp mẫu với dung sai ±5 và trừ **12 điểm** thật | fail-closed cả khi tra phạt lẫn khi ghi mẫu; `is None` chứ không `not` vì điểm 0 hợp lệ |
| 3 script | thiếu `sys.stdout.reconfigure` nên chết ở `print` đầu tiên, chưa bao giờ chạy nổi trên Windows | `tests/test_script_chay_duoc_tren_windows.py` quét toàn repo bằng AST |

Cái thứ ba là lần thứ **BA** cùng một lỗi (`kiem_ban_sach` 22/08,
`experiment_fundamentals` 23/08, `extend_history` 24/08). Vá từng file là
cách sửa ba lần đầu; gác toàn repo là cách sửa lần thứ tư. Test **import**
module chứ không **chạy** nó, nên không lần nào có test đỏ.

---

## CHI PHÍ THỰC THI ĐÃ BẬT (24/08/2026) — mọi số cũ phải trừ hao

```python
paper_trading.MO_PHONG_TRUOT_GIA = True
paper_trading.VON_DANH_MUC_VND = 1_000_000_000
```

`truot_gia.py` + `vong_doi_lenh.py` từng là hai module mồ côi: 29 test,
không file nào ngoài test của chính chúng import. Nay `fill_pending` đi qua
`vong_doi_lenh` (lô chẵn · biên độ ±7% · trần thanh khoản mỗi nến · khớp
một phần) và `evaluate_open` đi qua `truot_gia` khi bán.

**Giá phải trả, đo bằng hai lượt walk-forward trên cùng dữ liệu:**

| | lệnh | kỳ vọng | alpha | KTC 95% |
|---|---|---|---|---|
| TẮT (mọi số trước 24/08) | 390 | +0,614% | −0,011% | [−0,766 ; +0,832] chứa 0 |
| **BẬT** (từ nay) | 385 | **−0,291%** | **−0,927%** | **[−1,689 ; −0,076] LOẠI 0** |

> **Đây là kết quả có ý nghĩa thống kê ĐẦU TIÊN của dự án, và nó âm.** Với
> chi phí thực thi thực tế, chiến lược thua rổ chuẩn 0,927% mỗi lệnh trên
> vùng chứng minh được là chưa thể đã bị nhìn.
>
> Cách đọc: rổ chuẩn mua một lần rồi giữ, trả chi phí **hai lần**. Chiến
> lược quay vòng 385 lệnh, trả **770 lần**. Lợi thế vốn đã không phân biệt
> được với 0; cộng chi phí quay vòng vào thì phần âm lộ ra.

In-sample: **−0,43 điểm phần trăm mỗi lệnh, gần như bằng nhau ở cả bảy
ngưỡng** (45 → 62). Ổn định như vậy là dấu hiệu mô hình đúng — chi phí thực
thi là chi phí MỖI LỆNH, không co giãn theo độ chọn lọc.

**Kết luận KHÔNG phụ thuộc giả định vốn 1 tỷ.** Ở giá vào trung vị 16.100đ,
từ 100 triệu tới 1 tỷ chi phí y hệt nhau (0,311% một chiều): tác động thị
trường quá nhỏ để đẩy qua bước giá kế tiếp. Cái tốn tiền là **bước giá
50đ** — sự thật của lưới giá, không phải lựa chọn mô hình. Chỉ từ 5 tỷ trở
lên tác động mới cộng thêm một bước.

**MỌI con số trong tài liệu này đo TRƯỚC 24/08/2026 đều không có chi phí
thực thi** — kỳ vọng sổ +0,79%, alpha +0,090%, mọi bảng walk-forward. Trừ
hao ~0,43 điểm phần trăm mỗi lệnh khi đọc chúng.

**`volume` KHÔNG được nhân `price_multiplier`.** `run_session` nhân mọi giá
trị trong `bar` để quy nghìn đồng về VNĐ; nhân nhầm khối lượng thì tỷ trọng
nhỏ đi 1.000 lần, trượt giá tụt còn một bước giá, và kết quả vẫn trông hợp
lý hoàn toàn. Có test riêng chặn `fill_pending` để soi nến nó nhận được.

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

### Cảnh báo nội phiên — thứ tự bước là bắt buộc, không phải sở thích

`evaluate_open()` chấm trên nến NGÀY, mà trong phiên nến ngày đã phản ánh
cái đáy vừa tạo. Nên một vị thế thủng stop-loss lúc 10:30 sẽ bị chính nhịp
quét kế tiếp đóng ngay. **Đặt bước cảnh báo SAU bước quét thì nó luôn thấy
lệnh đã đóng và KHÔNG BAO GIỜ KÊU.** Bản đầu đặt sai đúng như vậy.

Thứ tự đúng, đã xác nhận trên runner ngày 22/08/2026:
`kéo sổ → cảnh báo → quét → đối chiếu`.

Cảnh báo đi bằng `::warning::` và `$GITHUB_STEP_SUMMARY`, **không** bằng mã
thoát: `tools/chuong_bao_quet.py` đếm `conclusion == "success"` để biết một
ngày có được quét không, nên một cảnh báo thật làm job đỏ sẽ sinh ra báo
động giả che mất chính thứ chuông sinh ra để canh.

**Canh gác khi sổ rỗng.** `quet()` chỉ gọi hàm tải nến khi CÓ vị thế đang
mở, nên với 113 lệnh đã đóng và 0 lệnh mở thì `intraday_data.tai()` không
chạy lần nào. Mà 0 vị thế không phải chuyện tạm: ngưỡng mua để trống VÀ
VN-INDEX dưới MA50. `quet_va_canh_gac()` nạp thử một mã khi sổ rỗng — hỏi
một **khoảng** 10 ngày chứ không hỏi riêng hôm nay, vì nhịp 09:00 chạy
trước khi nến 30 phút đầu tiên kịp đóng và "hôm nay 0 nến" là bình thường.
Chi tiết: `docs/STATE.md`, mục 22/08/2026.

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
python tools/chan_bia_so_lieu.py --quet-repo       # quét mẫu bịa số toàn repo
python tools/chan_bia_so_lieu.py --quet-thay-doi  # chỉ file đã đổi (hook Stop)
python tools/kiem_cu_phap_311.py                  # NAY CI CŨNG CHẠY — xem dưới
```

### Máy chạy 3.13, CI chạy 3.11 — khoảng cách đó ẩn được lỗi

`pytest` xanh tại máy **không** bảo đảm CI xanh. Cú pháp có từ 3.12 nạp bình
thường ở máy rồi làm `ast.parse` nổ trên runner.

Đã xảy ra 21/08/2026: một biểu thức điều kiện xuống dòng ngay trong ô thay
thế của f-string (PEP 701, chỉ có từ 3.12) trong `run_daily.py`. 319 test
xanh tại máy, CI đỏ ngay bước đầu, hai test `test_no_fabricated_data` báo
`File "<unknown>", line 83`.

`ast.parse(src, feature_version=(3, 11))` **KHÔNG** bắt được — `feature_version`
không hạ cấp bộ tách token, mà f-string đổi ở đúng tầng đó. Phải chạy bằng
một trình thông dịch 3.11 thật. `tools/kiem_cu_phap_311.py` tự tìm nó
(`PYTHON311`, bản uv, hoặc `py -0p`), tự kiểm mình bằng một đoạn 3.12-mới
trước khi kiểm repo, và phân biệt "chưa kiểm được" (mã thoát 2) với "sạch"
(mã thoát 0).

**Từ 22/08/2026 nó kiểm cả python nhúng trong workflow YAML.** Bước cảnh báo
nội phiên có hơn 70 dòng python nằm trong heredoc — chạy trên runner y hệt
một file `.py`, nhưng `rglob("*.py")` không thấy và không test nào import.
`doan_nhung()` trích mọi heredoc **có trích dẫn** (`<<'X'`) rồi kiểm cùng
lượt. Heredoc **không** trích dẫn bị bỏ qua có chủ đích: shell nội suy `$…`
trước khi python thấy, nên thứ trên đĩa không phải thứ chạy thật. Số đoạn
nhúng được in cùng số file để một số 0 ở đó nhìn thấy được.

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

## Bộ nhớ hậu nghiệm — hai nơi CỐ Ý lệch nhau

```
backtest (walkforward.chay)  ->  co_san   : dùng 44 mẫu, KHÔNG ghi thêm
đường chạy thật (run_daily)  ->  tích luỹ : dùng 44 mẫu, CÓ ghi thêm
```

Lệch này là **quyết định, không phải sơ sót** (21/08/2026). Backtest đo một
bộ nhớ đứng yên để phép đo tái lập được; sổ thật vẫn gom mẫu tiếp.

Hệ quả phải biết khi đọc số: con số ngoài mẫu nói về cấu hình `co_san`,
không nói về cấu hình đang chạy thật. Hôm nay khác biệt đó nhỏ — đo được
rằng 44 mẫu gần như không đổi kết quả gì — nhưng sẽ lớn dần nếu bộ nhớ lớn
dần.

**Bộ nhớ này đã bão hoà, không phải thiếu mẫu.** 44 mẫu chỉ gồm **2** bộ ba
khác nhau, phủ 3,2% số quyết định. Trần trên là 2 và thêm lệnh không nâng
được: bộ nhớ chỉ học từ lệnh ĐÃ MỞ, mà 113/113 lệnh trong lịch sử đều rơi
vào đúng 2 ô (`trend 65 · mom 65 · vol 100` và `… vol 93,8`), vì cổng mua
chỉ mở ở góc đó. Chi tiết và số liệu:
`docs/ket-qua-bo-nho-rieng-20260821.md`.

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
market_filter.status()           # bộ lọc VN-INDEX có thật sự bật không
market_filter.chi_so_moi_nhat()  # topbar lấy được phiên nào, từ nguồn nào
data_quality.price_multiplier()  # vnstock trả nghìn đồng vs agent trả VNĐ
mau_bang_gia.doc_bang_gia("SSI") # trần/sàn/tham chiếu thật, `loi` nói vì sao thiếu
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

---

## Dọn code chết — cái bẫy đã gặp

Đã rà 28/08/2026. Ghi lại để lần sau khỏi vấp:

1. **Dùng AST, đừng dùng grep.** `"news" in src` khớp cả chữ trong chú
   thích. File càng nhiều chú thích trung thực thì grep càng nói dối.
2. **`from __future__ import annotations` KHÔNG phải import thừa.** Mọi
   máy quét sẽ gắn cờ nó ở ~20 file. Gỡ ra là CI 3.11 đỏ.
3. **Khoá cấu hình không ai đọc nguy hiểm hơn code không ai chạy.** Code
   chết thì im lặng; núm vặn giả thì mời người ta vặn. Bộ trọng số từng
   mang `"news": 0.0` mà biểu thức điểm không hề đọc tới.
4. **Xoá trùng lặp, đừng xoá năng lực.** `tradingview_mcp.py` là bản sao
   thứ hai của thứ đã có → xoá. `top_stocks_screener.py` mồ côi nhưng là
   tính năng riêng → để lại cho người quyết.
5. **Chạy `tools/kiem_cu_phap_311.py` khi pytest đã xong**, không song
   song: có test ghi thư mục tạm vào gốc repo và gây đỏ giả.

Hai hàng rào mới đáng biết:
`tests/test_trong_so_that_su_duoc_dung.py` bắt mọi khoá trọng số không
được nhân vào điểm (và mọi hạng tử bị quên khỏi tổng).
`tests/test_dau_hieu_tranh_luan.py` khoá quy ước dấu Bull(+)/Bear(−)/Devil(−).

---

## Cổng C5 — đọc trước khi sửa

> **TRẠNG THÁI 29/08/2026 — CỔNG ĐANG ĐÓNG.**
> `paper_trading.CHO_PHEP_MO_LENH_MOI = False`, đóng **bằng tay**, không
> phải do điều kiện kích hoạt. Khoá bởi `tests/test_c5_noi_that.py` — mở
> lại thì phải sửa cả test đó, có chủ đích.
>
> **Sổ THẬT nằm trên Google Sheets, không phải `paper_trades.db` ở máy.**
> File ở máy đứng yên từ 20/08/2026; đo trạng thái bằng nó là đo một bản
> sao chết, và ngày 28/08 đã sai đúng như vậy một lần.
>
> **Bốn lệnh tiến-về-trước đầu tiên đã tồn tại** — NAF 62 · STB 65 ·
> TCB 63 · HUT 65, tín hiệu 2026-08-28, và tới 02/09/2026 cả bốn **vẫn
> `PENDING`**. Câu "chúng khớp sáng 31/08" ở bản trước là SAI: không có
> phiên nào sau 28/08 để lấy giá mở cửa. Cơ chế thì vẫn đúng —
> `fill_pending()` không đọc cờ C5, nên đóng cổng KHÔNG huỷ lệnh chờ.
> Xem `docs/STATE.md`, BƯỚC 11.
>
> **Cổng đóng nay ĐỐI CHIẾU ĐƯỢC, không chỉ khai (31/08/2026).**
> `tools/canh_cong_c5.kiem_ro_ri()` hỏi sổ lệnh — chứ không hỏi mã nguồn —
> rằng kể từ `paper_trading.NGAY_DONG_CONG_C5` đã có vị thế mới nào được
> mở chưa. Đo 31/08: **0 trên 15.714 quyết định.** Và mỗi lượt quét nay tự
> đo cửa sổ dữ liệu nó NHẬN ĐƯỢC (`run_daily.bao_cua_so_du_lieu`), phát ra
> bằng `::notice::` để đọc được qua API công khai. Chi tiết:
> `docs/STATE.md`, mục **"BƯỚC 5"**.
>
> Chi tiết: `docs/STATE.md`, mục **"CỔNG C5 ĐÃ ĐÓNG LẠI"** (29/08/2026).

Phân tích gốc rễ đầy đủ: `docs/STATE.md`, mục **"GỐC RỄ CỦA CỔNG C5"**
(28/08/2026). Tóm tắt để khỏi sửa nhầm:

> **BẢN 2 đã thay bản 1 ngày 29/08/2026.** Điều kiện nay đo **alpha khớp
> từng lệnh**, ngưỡng suy từ `co_mau_cho_luc()` (596 lệnh cho 80% lực phát
> hiện ở −0,927%), và có **biên đảo gánh nặng**: đủ cỡ mẫu nêu trước mà
> chưa chứng minh được lợi thế thì ĐÓNG. Sai lầm loại I 5,8%; một hệ thống
> alpha = 0 bị đóng 99,6%; alpha = +2% không bao giờ bị đóng. Chi tiết và
> bảng đặc tính: `docs/STATE.md`, mục **"BƯỚC 3 — ĐIỀU KIỆN DỪNG BẢN 2"**.
>
> **Hàng rào quy trình:** `tests/test_hang_rao_quy_trinh.py` giữ một SỔ
> ĐĂNG KÝ điều kiện an toàn. Thêm một hàm `dieu_kien_*` mà không khai →
> test đỏ. Khai rồi thì buộc chứng minh hai điều: ngưỡng bằng
> `co_mau_cho_luc()`, và điều kiện đạt thì lá cờ ĐỔI THẬT (chạy, không đọc
> mã). Đột biến 7/7 đỏ, gồm cả đột biến tái tạo đúng nguyên nhân 1.
>
> Bốn nguyên nhân dưới đây là của BẢN 1, giữ lại để không ai sửa ngược.

`paper_metrics.dieu_kien_dong_lai()` bản 1 hỏng vì **bốn** lý do, không phải một:

1. Hiệu chuẩn để bắt **thảm hoạ** (−2,5%/lệnh), trong khi cái có thật là
   **bất lợi** (−0,927%/lệnh alpha). Phép tính hồi đó ĐÚNG; mục tiêu sai.
2. Chỉ định giá sai lầm loại I (đóng nhầm vì nhiễu). Loại II — để mở trong
   khi đang lỗ — không được nhắc một lần.
3. Quy tắc ghim vào ảnh chụp hiểu biết ngày 26/08; ngày 28/08 chi phí thực
   thi làm alpha từ ≈0 xuống −0,927%. Tiền đề sụp, quy tắc không đi theo.
4. **Nặng nhất: điều kiện KHÔNG CÓ AI THI HÀNH.** Nó chỉ được gọi trong
   `report()` và chỉ thêm một câu chữ vào một tệp zip lưu 14 ngày trên
   GitHub Actions. Đạt hay không đạt đều không đóng được cổng.
   → **Đã sửa 29/08/2026.** `run_daily.thi_hanh_dieu_kien_dung()` chạy
   trước vòng quét và TẮT cờ cho lượt đó; chuông riêng
   `tools/canh_cong_c5.py` + `canh-cong-c5.yml` làm đỏ một workflow RIÊNG
   (làm đỏ lượt quét sẽ khiến `chuong_bao_quet.py` báo giả "ngày này
   không có lượt quét nào"). Cờ trong tiến trình KHÔNG sống qua lượt sau
   — chốt bền vẫn là dòng trong mã nguồn.

Đo đúng đại lượng đổi hẳn bài toán: **kỳ vọng cần 11,4 năm để đạt 80% lực
phát hiện; alpha cần 13 tháng.** Alpha đã tính được trên đường chạy thật
(`run_daily.py:249` truyền rổ chuẩn VN-INDEX) — không phải xây thêm gì.

**Đã đo 29/08/2026 — và chỗ tối hoá ra nằm chỗ khác.** Đo cả 71 mã, dữ liệu
tới hết 2026-08-28, tách ba hiệu ứng (chi tiết: `docs/STATE.md`, mục "BƯỚC 2
— ĐO CHỖ TỐI"):

| Hiệu ứng | \|lệch\| TB | Đổi quyết định |
|---|---|---|
| Gói vnstock (miễn phí ↔ tài trợ) | 0,46 điểm | **0/67** |
| TradingView thật ↔ không có | 0,59 điểm | **0/71** |
| **Cửa sổ dữ liệu 44 phiên ↔ 301 phiên** | **5,86 điểm** | **6/71** |

Gói vnstock KHÔNG phải vấn đề. TradingView cũng không. Thứ quyết định là
`run_daily.py:263` — `start_date = now - 60 days` cho **44 phiên**, trong
khi `walkforward.py:213` truyền `df.iloc[:t+1]` (cửa sổ MỞ RỘNG, hàng trăm
phiên) và `app.py` dùng 420 ngày (~301 phiên).

Dưới 50 phiên thì `_compute_local_indicators()` trả `None` cho SMA50 và
SMA200, nên các luật của agent xu hướng dùng chúng bị bỏ qua: `trend_score`
kẹt ở 35/50/65, không bao giờ chạm 100 hay 15. **Ngưỡng 62 do walk-forward
chọn trên phân phối điểm của cửa sổ DÀI, đang được áp lên điểm của cửa sổ
NGẮN.** Ba trong bốn lệnh PENDING (NAF, TCB, HUT) chỉ tồn tại vì cửa sổ đó.

Kèm theo: `MO-XE-KIEN-TRUC.md` ghi "trend — công tắc 3 nấc" — đó chưa bao
giờ là tính chất của mã nguồn, đó là tính chất của CỬA SỔ.

**ĐÃ ĐO 31/08/2026 — gói miễn phí phục vụ ĐỦ cửa sổ dài.** Annotation của
lượt quét trên runner: 71 mã, **trung vị 784 phiên**, ít nhất 138, **0 mã
dưới mốc 50 phiên**. Đúng bằng con số máy local hạng silver. Giới hạn của
gói nằm ở BCTC và hạn mức request, KHÔNG ở lịch sử giá — nên SMA50/SMA200
tính được cho cả rổ và ngưỡng 62 chạy trên đúng phân phối đã hiệu chuẩn
nó. Chi tiết: `docs/STATE.md`, mục **"BƯỚC 6"**.

**Chưa đo:** `tv_recommendation` KHÔNG tái lập — MSR đổi `STRONG_BUY` →
`NEUTRAL` trong chưa tới một giờ khi thị trường đã đóng (bất biến 2).

**Hạn — CHƯA qua. Đoạn dưới đây từng ghi ngược, sửa 01/09/2026.**

Bản trước viết: *"Bốn lệnh chờ khớp sáng 31/08/2026, nên điều kiện 2 của
điều khoản sửa đổi hết hiệu lực từ mốc đó."* **Sai.** Đọc thẳng sổ thật
trên Google Sheets ngày 01/09/2026: bốn lệnh NAF · STB · TCB · HUT vẫn
`PENDING`, `entry_date` và `entry_price` đều là `None`. Chúng chưa bao giờ
khớp.

Nên: **kết quả tiến-về-trước đã đóng = 0, và điều kiện 2 vẫn thoả.** Mọi
quy tắc dừng viết sau mốc này vẫn phải ghi rõ nó được viết khi trong tay
có bao nhiêu kết quả — yêu cầu đó không đổi, chỉ có con số là 0 chứ không
phải 4.

**Việc treo đó đã ĐÓNG (02/09/2026): không có lỗi nào cả.** Chưa hề có
phiên nào sau 28/08 — 31/08, 01/09 và 02/09 đều không có nến ở cả ba
endpoint vnstock (OHLCV theo mã, VN-INDEX kéo thẳng từ mạng bỏ qua cache,
nến 30 phút nội phiên). `fill_pending()` bỏ qua vì
`session_date <= signal_date`, đúng thiết kế: không có nến thì không có
giá mở cửa để khớp. Trước đó **17 ngày quét liên tiếp đều trễ 0 phiên**.
Chi tiết: `docs/STATE.md`, BƯỚC 11.
