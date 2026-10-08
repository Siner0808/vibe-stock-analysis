# CLAUDE.md — Luật hiện hành của dự án

Hệ thống phân tích cổ phiếu Việt Nam. Streamlit + Python 3.11, dữ liệu từ
vnstock. Phát triển local → PR → `main` → Streamlit Cloud tự deploy.

> **File này chỉ giữ LUẬT HIỆN HÀNH** (BƯỚC 145, 30/09/2026). Nó được nạp
> vào ngữ cảnh mỗi phiên — mỗi KB ở đây là chi phí trả ở MỌI lượt gọi công
> cụ. Lịch sử (khối 🔴 "HẾT ĐÚNG", các bảng đo đã bị thay, sự cố đã xử lý)
> nằm ở **`docs/lich-su/CLAUDE-md-2026-09-30.md`** (bản nguyên văn) và
> `docs/STATE.md`. Tìm lại một khẳng định cũ: `grep -n "<từ khoá>"
> docs/lich-su/CLAUDE-md-2026-09-30.md`.
>
> **BẮT ĐẦU Ở ĐÂY: `docs/HANDOFF.md`** (ba lệnh đầu tiên, mốc đang chặn,
> ba ràng buộc). Ưu tiên khi mâu thuẫn: `HANDOFF` → `STATE` → file này.
>
> **LỘ TRÌNH: `docs/LO-TRINH.md`** — hai đích, năm giai đoạn, người dùng duyệt
> 08/10/2026. Mỗi BƯỚC từ 164 khai một dòng `**Mốc:** <mã>` trong `docs/STATE.md`.
>
> **Luật giữ file này gọn:** một BƯỚC KHÔNG sửa `CLAUDE.md` trừ khi nó đổi
> một LUẬT. Số đo, kết quả một ĐO, trạng thái sổ → `docs/STATE.md` và
> `docs/HANDOFF.md`. Chú thích "đã hết đúng" viết ở đó, không viết ở đây.

---

## Đọc trước khi sửa bất cứ thứ gì liên quan tới kết quả

| File | Nội dung |
|---|---|
| `NGUYEN-TAC-DO-LUONG.md` | 8 bất biến đo lường. Dự án đã **5 lần** cho ra số đẹp mà sau đó vô nghĩa (+22,42% · +14,88% · +14,24% · +636,11% và giao diện công bố +636,11% nhiều ngày). Không lần nào cố ý; **lỗi đo lường gần như không bao giờ làm kết quả xấu đi.** |
| `MO-XE-KIEN-TRUC.md` | Đo thực tế: thành phần nào đang chạy thật, thành phần nào là trang trí. |

- **Quy tắc 1 — số đẹp lên đáng kể thì giả định đầu tiên là CÓ LỖI.** Số
  xấu đi là chiều an toàn.
- **Quy tắc 2 — không có lệnh thì không có số.** Mọi con số viết vào tài
  liệu hay commit phải được tính trong phiên này, kèm lệnh tái lập được.
  Ước lượng thì gọi nó là ước lượng.
- **Quy tắc 3 — BƯỚC đổi một luật hoặc một kết luận đo thì đi qua sổ tay
  NotebookLM; BƯỚC khác khai vì sao không hỏi, và máy xác nhận bằng lịch sử git**
  (từ BƯỚC 164, người dùng "Đồng ý" 08/10/2026; BƯỚC ≤ 163 giữ luật cũ; `SKILL.md`).
- Quy trình bắt buộc: skill `quy-trinh-lam-viec`. Cửa tự động đọc bằng
  `./.venv/Scripts/python.exe tools/kiem_cua_song.py`, không suy ra.

### `AGENTS.md` và ba file toàn cục — đừng cập nhật `AGENTS.md`

`vnai` (kích hoạt bởi `import vnstock_data`) ghi khối bootstrap vào bốn đích,
nhưng từ 18/09/2026 người dùng đã **TẮT cả bốn** (`enabled=False`, BƯỚC 103):

| đích | đường dẫn | ghi chú |
|---|---|---|
| `project` | `<repo>/AGENTS.md` | vnai BỎ QUA vì file mang dấu mốc đời cũ |
| `antigravity` | `~/.gemini/GEMINI.md` | bị ghi khi còn bật |
| `claude` | `~/.claude/CLAUDE.md` | bị ghi khi còn bật <!-- duong-da-chet: DICH ghi cua vnai, khong phai file dang co; file chi chua khoi vnai, nguoi dung go sau BUOC 126, vang tu BUOC 139 (29/09) --> |
| `codex` | `~/.codex/AGENTS.md` | bị ghi khi còn bật |

`AGENTS.md` của repo an toàn **vì nó CŨ** (mở đầu `# Vnstock Vibe Onboarding`,
thiếu câu kết `(End of Bootstrap…)`); cập nhật nó là gỡ mất cái khiên. Luật
dự án đặt ở `NGUYEN-TAC-DO-LUONG.md` và file này. Đảo công tắc bằng
`enable_agent_setup()` — đó là quyết định của người dùng. Gác:
`tests/test_dich_ghi_de_cua_vnai.py`. `docs/STATE.md` BƯỚC 91, 103.

---

## Trạng thái đo được — đọc trước khi đề xuất tính năng mới

Trên 573 phiên / 10 mã (2021-10 → 2026-08): điểm cuối **không dự báo được
lợi nhuận** (rho = −0,019 với lợi nhuận 20 phiên sau, KTC 95%
[−0,100 ; +0,064]); walk-forward alpha −0,36%. Tầng tranh luận chỉnh ±0,9
điểm, Safety Harness kích hoạt 0%; bỏ cả hai vẫn 572/573 phiên cùng quyết
định. "Agent là hằng số / công tắc 3 nấc" là tính chất của **CỬA SỔ dữ
liệu**, không của mã (cửa sổ dài 63.389 phiên / 69 mã: `momentum` 17 nấc,
`trend` 10, `sr` 7, `risk` 8, `volume` 13; chỉ `news` là hằng số).

**Hệ quả:** thêm agent hay tầng vào một hệ có rho ≈ 0 không cải thiện được
gì; nguyên nhân gốc là **thiếu dữ liệu độc lập** — cả sáu agent tính từ cùng
một chuỗi giá. Ba nguồn độc lập đã đo (không nguồn nào cứu được):

| nguồn | kết quả | BƯỚC |
|---|---|---|
| BCTC theo quý | không chỉ số nào phân biệt được với 0 trên 2.099 quan sát | 53 |
| khối ngoại mua ròng | có tín hiệu nhưng nhỏ hơn rào hoà vốn 2,66 lần | 113 |
| giao dịch nội bộ | `insider_trading()` của `vnstock_data` trả 0/71 mã | 114 |

Mâu thuẫn cốt lõi: *phần đo được thì không có tín hiệu, phần có thể có tín
hiệu thì không đo được* (trên app chạy trực tiếp các agent "chết" trong
backtest sống lại nhưng không đo được).

### Agent cơ bản, Wyckoff, Fibonacci, màu bảng giá — CHỈ ĐỂ HIỆN

- `fundamental_agent.FundamentalAgent` đọc bảng `ratio` **theo năm** từ
  KBS. Cẩn thận: `total_assets`/`owners_equity` trong `ratio` là TĂNG
  TRƯỞNG %, không phải số dư; ngân hàng có bộ chỉ tiêu khác hẳn. Trọng số
  `master_agent.TRONG_SO_CO_BAN` = **0** (đã đo, không ủng hộ bật). Cờ
  `doc_co_ban` mặc định `False` là **rào chắn chống nhìn trộm** (bảng năm
  hiện tại đã hồi tố): chỉ `run_full_analysis()` bật nó.
- `pha_wyckoff.doc_pha` — hàm thuần, KHÔNG chấm điểm. Biên vùng dựng từ
  phần `nền`, sự kiện tìm ở phần `gần đây`, hai phần không giao nhau. Tỷ
  lệ "chưa đủ bằng chứng" cao (20/40 mã VN100) là **đúng kỷ luật** — đừng
  nới ngưỡng cho nhãn đẹp hơn.
- `muc_fibonacci.doc_muc` — uỷ thác biên vùng cho `pha_wyckoff.doc_pha`,
  không tự dò đỉnh–đáy. **Không vào đường sinh lệnh** (ĐO 9, BƯỚC 79: Δalpha
  +0,22 trên nửa bề rộng KTC 0,57). `paper_trading.DUNG_MUC_FIBONACCI` mặc
  định TẮT. 78% mã dựng được mức có SL "dưới cấu trúc" vượt biên rủi ro
  4–6,5% (BƯỚC 78).
- `mau_bang_gia.doc_bang_gia` — bảng giá VN có **năm** màu (trần tím, tăng
  xanh lá, tham chiếu vàng, giảm đỏ, sàn xanh lam). **Không bao giờ suy
  trần bằng ngưỡng phần trăm** (SSI trần ở +6,96%, SHS +8,16% mà không
  trần): module ĐỌC `ceiling/floor/ref_price` từ `Trading.price_board`,
  không có hàm tính trần. Không đọc được bảng giá → tụt xuống ba màu. Ô
  VN-Index ở topbar gọi `market_filter.chi_so_moi_nhat()` (ưu tiên MẠNG),
  KHÔNG phải `get_vni_df()` (ưu tiên cache) và luôn kèm ngày phiên.

---

## Sổ lệnh giấy, cổng mở lệnh, điều kiện dừng

- **Không đặt lệnh thật.** Agent chuẩn bị → người xác nhận → người đặt lệnh.
- **Sổ THẬT nằm trên Google Sheets**, không phải `paper_trades.db` ở máy
  (file ấy đứng yên từ 20/08/2026). Đọc trạng thái bằng
  `./.venv/Scripts/python.exe tools/doc_so_that.py`; con số về sổ tự trôi,
  không gác được bằng test — **đừng chép nó vào tài liệu**.
- Sổ 113 lệnh lịch sử là một lượt MÔ PHỎNG (`created_at` gom trong 258 giây,
  `signal_date` trải 903 ngày), không phải bản ghi tích luỹ. Mọi số về nó
  (kỳ vọng, alpha, drawdown) đúng như phép tính nhưng nói về mô phỏng.
  `paper_metrics.tom_tat_lo_ghi()` tự phát hiện điều này từ dữ liệu.
- **Cổng mở lệnh MỞ** (`docs/STATE.md` BƯỚC 125; ĐANG chạy từ 28/09/2026,
  BƯỚC 138): `paper_trading.CHO_PHEP_MO_LENH_MOI = True`, ngưỡng mua
  `BUY_THRESHOLD` = 62, `TRAN_VON_CAM_KET_PCT` = 100. Lý do mở KHÔNG phải
  đã thấy lợi thế (mọi phép đo alpha còn chứa số 0) mà vì cấu hình chạy
  trực tiếp chỉ đo được **tiến về phía trước**. Đóng lại bằng tay = sửa
  dòng ấy và `tests/test_c5_noi_that.py` cùng lúc, có chủ đích.
- **Điều kiện dừng** `paper_metrics.dieu_kien_dong_lai()` đo **alpha khớp
  từng lệnh**; hai ngưỡng SUY RA từ `co_mau_cho_luc()` ở
  `MUC_BAT_LOI` = −0,920% (không gõ tay): `N_DAY_DU` = 451 lệnh (80% lực
  phát hiện), `N_TOI_THIEU` = 113. Dưới `N_TOI_THIEU`: chưa đủ để kết luận.
  Giữa hai ngưỡng: ĐÓNG nếu cận TRÊN KTC (z = 2,30) < 0. Từ `N_DAY_DU`: ĐÓNG
  **trừ khi** cận DƯỚI KTC (z = 1,96) > 0 (đảo gánh nặng). Đừng chế điều
  kiện khác sau khi đã nhìn số (bất biến 7). `run_daily.thi_hanh_dieu_kien_dung()`
  chạy trước vòng quét và TẮT cờ cho lượt đó; chuông riêng
  `tools/canh_cong_c5.py` + `canh-cong-c5.yml`. `tests/test_hang_rao_quy_trinh.py`
  giữ sổ đăng ký điều kiện an toàn (thêm hàm `dieu_kien_*` mà không khai → đỏ).
- **Trần vốn** `size_pct` mở + chờ ≤ 100% chỉ chặn được ở đường chạy thật;
  backtest chạy **theo mã** nên mọi con số đòn bẩy 145%/524%/1372% trong
  báo cáo walk-forward là một danh mục máy chưa bao giờ nắm.
  `dong_so_sach()` đóng lệnh mồ côi cuối mỗi mã và **PHẢI nhân
  `price_multiplier`** (quên → mọi lệnh mồ côi đóng ở −99,90%).
- **Một ngưỡng mua, một chỗ:** `run_daily` NHẬP `BUY_THRESHOLD`, cấm khai
  báo lại kể cả khai đúng 62.
- Chốt lời cứng đã gỡ (`CHOT_LOI_CUNG` mặc định False): kỳ vọng chênh +0,190%
  có KTC chứa 0, alpha hai luật giống hệt; nó chỉ giảm phương sai 24%.
- **Tín hiệu:** cửa sổ dữ liệu quét phải DÀI (~784 phiên; cửa sổ 44 phiên
  làm `trend_score` kẹt 35/50/65 và lệch ngưỡng 62). `run_daily` chỉ ghi sổ
  trên nến ĐÃ ĐÓNG (`data_quality.nen_cuoi_dang_do`). `tv_recommendation`
  của đường giao dịch ghim `"NEUTRAL"` (`tests/test_duong_giao_dich_khong_doc_tradingview.py`).

### Bộ nhớ hậu nghiệm

Backtest dùng 44 mẫu đứng yên (`co_san`, không ghi thêm); `run_daily` ở mã
là `tich_luy`. Nhưng đường quét thật chạy trên Actions với bộ nhớ RỖNG
(`sl_pattern_memory.json` bị gitignore): 71/71 lượt quét ghi "0 mẫu" — vế
"tích luỹ" chưa từng xảy ra ở nơi nó chạy (BƯỚC 140). Người dùng chốt
25/09: 44 mẫu chỉ giữ làm lịch sử; đổi điểm phải qua vòng xác nhận của tầng 3 (một vòng
kể từ 02/10, BƯỚC 155: khai thẳng, ≤ 1 mỗi tháng; vòng sàng đã bỏ; vòng ấy chỉ PHÁN
MỘT LẦN, ở đúng 252 phiên có nhãn đầu tiên, BƯỚC 162).
Dùng 44 mẫu ở đường thật hay không: **quyết định của người dùng, chưa có.**

---

## Chi phí thực thi — mọi số cũ phải trừ hao

Ma sát có **hai tầng**. Tầng 1 luôn bật, không công tắc: phí môi giới + phí
Sở + thuế bán, `paper_metrics.ROUND_TRIP_COST_PCT` = 0,46% một vòng mua–bán
(cận DƯỚI của dải bán lẻ thật, công ty đắt có thể tới 0,76%). Tầng 2 là
`truot_gia.py` + `vong_doi_lenh.py` (bước giá, tác động thị trường, lô chẵn,
vòng đời lệnh), công tắc `paper_trading.MO_PHONG_TRUOT_GIA` = True,
`VON_DANH_MUC_VND` = 1 tỷ. `volume` KHÔNG được nhân `price_multiplier`.
Bước giá 50đ là sự thật của lưới giá HOSE ở dải 10–50 nghìn; HNX/UPCoM là
100đ ở mọi mức. Mô hình từng áp nhầm thang HOSE cho 7 mã (4 HNX, 3 UPCoM);
đã sửa ở BƯỚC 143 — `san_giao_dich.py` (bảng chụp 71 mã, tra sàn theo MÃ),
`tools/kiem_san_giao_dich.py` so lại với `Listing` hai nguồn.

**Bảng hiện hành** — ĐO 18 (26/09/2026, sổ đã làm trung thực) cho hai dòng
TẮT; ĐO 22 (30/09/2026, sau BƯỚC 143 sửa bước giá HNX/UPCoM) cho hai dòng BẬT.
Alpha là thước quyết định (bất biến 6):

| trượt giá | chế độ | ngưỡng IS | lệnh OOS | alpha | KTC 95% | vốn TB · đỉnh |
|---|---|---|---|---|---|---|
| BẬT | theo mã | 62 | 397 | −1,16% | [−2,00 ; −0,25] LOẠI 0 | 51% · 191% |
| BẬT | **theo ngày** | 45 | **619** | **−1,68%** | [−2,24 ; −1,08] LOẠI 0 | 56% · **100%** |
| TẮT | theo mã | 62 | 399 | −0,41% | [−1,24 ; +0,48] chứa 0 | 51% · 191% |
| TẮT | theo ngày | 45 | 582 | −0,72% | [−1,33 ; −0,07] LOẠI 0 | 58% · 100% |

- Chi phí thực thi (TẮT − BẬT) nay **0,75** (theo mã) · **0,96** (theo ngày)
  điểm mỗi lệnh; cộng thêm ~0,5 điểm/lệnh vì bản mã trước BƯỚC 123 ghi gap
  dưới SL ở đúng giá SL (115/387 lệnh cắt lỗ bị gap). **Trừ hao 0,75–0,96 +
  ~0,5 khi đọc mọi số đo trước 26/09/2026.**
- **Dòng theo ngày là dòng đáng tin nhất:** nhiều lệnh nhất, chế độ duy nhất
  có danh mục thật (vốn đỉnh đúng 100% = trần vốn CÓ chặn), và loại được
  số 0. Bốn lần đo độc lập cho cùng kết luận.
- **Chỉ so 1↔3 và 2↔4** (cùng ngưỡng, khác mỗi công tắc). Ngưỡng do chính
  lượt chạy chọn trên IS, nên so theo mã với theo ngày là so cả chế độ lẫn
  ngưỡng. Độ trễ khớp đổi thì ngưỡng nhảy (62/50 → 62/45).
- Kết luận **không phụ thuộc vốn 1 tỷ**: cái tốn tiền là bước giá, không
  phải tác động thị trường (chỉ từ 5 tỷ mới cộng thêm một bước).
- Cache lùi tới 2018 (ĐO 4, vùng ngoài mẫu 68 mã) cho cùng kết luận: kỳ vọng nhảy >1 điểm do thiên
  lệch sống sót, alpha đứng yên; dòng theo mã có vốn đỉnh 422% — lợi nhuận
  cộng dồn của nó là đúng hình dạng con số +636,11%.
- Thời gian chạy walk-forward lệch tới 27% theo tải máy: nói ra là một khoảng.

### Backtest khớp T+1 (mặc định từ 10/09/2026)

`walkforward` mặc định `do_tre_khop=1`, khớp như đường chạy thật. Bản cũ
khớp T+2 vì `stride` thưa hoá luôn phiên KHỚP; đo (ĐO 2): đổi sang T+1 chỉ
dịch alpha +0,12–0,13, nhỏ hơn một phần sáu bề rộng KTC. **Đừng dùng
`--stride 1`** để đo độ trễ (đổi cả số điểm quyết định lẫn độ trễ). Đường
đúng: `--do-tre-khop 1`, ngưỡng ghim tay. `walkforward_vn100.py` đã đổi đuôi
`.broken` — bản đúng là `walkforward.py`.

---

## Dữ liệu và gói vnstock

- **Hạng gói:** đã mua silver, app từng chạy như free (`vnai/beam/auth.py`
  nuốt `ImportError` của `vnii` rồi rơi xuống `"free"`; `PERIOD_LIMITS`
  cắt BCTC còn 8 kỳ tại máy). `vnstock_goi.kiem_goi()` có ba trạng thái
  `KHỚP` / `LỆCH` / `CHƯA KIỂM ĐƯỢC` (mất mạng không được trả "khớp"). **Không
  bao giờ ép hạng trong mã** (`authenticator._cached_tier = "silver"`).
- **Không `import vnstock_data` ở mức module.** Bốn gói tài trợ không có
  trên PyPI công khai nên không nằm trong `requirements.txt`; dùng thì
  import trong hàm, bọc `try/except`, có đường lui. `vnstock_data` cần
  `~/.vnstock/user.json` (do `vnstock_installer.api.create_user_info()` tạo).
- **KHÔNG đổi `import vnstock` sang `import vnstock_data` mà chưa đo:** ROE
  lệch 100 lần (ROE FPT 2025 = 23.59 ↔ 0.2359 nhãn `%`), KBS mất chỉ tiêu
  (10/60 ↔ 58/58), `RT_BANK_NIM = 0.0` khiến `fundamental_agent.doc_chi_so()`
  xếp mã phi ngân hàng sang thước ngân hàng. Tài liệu migration `ratio` sai
  33/60 mã — tệp ấy thuộc khu vực thành viên, **không đưa vào repo**.
- **Tài liệu skill của vnstock KHÔNG ghi ra đĩa** (giấy phép cấm); nạp lúc
  chạy bằng `vnai.load_skill("<slug>")`.
- **Ghim bản:** từ BƯỚC 127 `vnstock==4.0.9`, `vnai==2.6.2` lấy từ kho hãng
  (`--extra-index-url https://vnstocks.com/api/simple`; PyPI cách ly cả hai).
  `tests/test_requirements.py` đỏ khi bản đang chạy lệch bản ghim. Nâng bản
  nghĩa là đo lại và sửa ghim.

## Bất đối xứng local / CI — VĨNH VIỄN, và là chủ ý

| Nơi | Hạng | BCTC | Hạn mức | OHLCV |
|---|---|---|---|---|
| Máy local | silver | không giới hạn (`balance`/`income` 34 kỳ; `ratio` chỉ 2–4 kỳ mỗi mã) | 300/phút | 784 phiên / 1095 ngày |
| GitHub Actions · Streamlit Cloud | free | 8 kỳ | 60/phút | **784 phiên — y hệt** |

Bất đối xứng KHÔNG CHỈ nằm ở BCTC và hạn mức ⚠️ (câu cũ khai đủ, thiếu vế này): nó còn ở **bản thư viện**.
`requirements.txt` khai bản `vnstock`/`vnai` bằng ghim `==` (BƯỚC 127), nhưng
các gói khác vẫn khai bằng **sàn** (`>=`) nên mỗi lượt CI lấy bản MỚI NHẤT
trong khi máy cài một lần rồi đứng yên. Khoảng lệch phải **đo, không suy**
(chúng đổi theo ngày):

```bash
./.venv/Scripts/python.exe tools/so_ban_goi.py
```

Nó chia ba hạng, in đủ tên và hai số hiệu của từng gói lệch, mã thoát
0/1/2 (không chạm quyết định / có chạm / chưa kiểm được). Quần thể là **giao
của hai bên đọc được** (lỗi 80: dụng cụ tự khai bảy tên gõ tay chỉ thấy 1 trong
32 lệch). Lịch sử lệch bản chính (`streamlit`, `plotly`, `urllib3`) đã đóng
ở BƯỚC 95–96, 106; còn `pyarrow` 24 → 25. Lớp lệch còn lại luôn phải đọc
bằng lệnh trên, không đọc ở đây. `vnstock_goi.kiem_goi()` báo LỆCH trên
cloud vĩnh viễn — đó là báo ĐÚNG.

---

## Quét tự động — Actions là nơi duy nhất

Task Scheduler `VibeStock_QuetPhien` đã **Disabled** từ 21/08/2026. Quét chạy
ở GitHub Actions (`quet-so-lenh.yml`; ba workflow `quet-so-lenh` · `canh-cong-c5`
· `chuong-nguon-dung` bật lại 28/09/2026, BƯỚC 138 — tắt lại: `gh workflow
disable <tên>.yml`). Đặc tính đã đo, hãy tin hơn lịch cron:

- GitHub gộp và trễ nhịp: `quet-so-lenh` mỗi ngày làm việc chỉ chạy ~2/12
  nhịp từ 27/08; ba chuông ở khung 09:00–10:00 UTC trễ trung vị **4–4,7
  GIỜ**. Đổi cron sang lệch `:00/:30` **không có tác dụng** (BƯỚC 89, 101).
- Nên "né giờ nghỉ trưa" và "lệch giờ 10 phút để khỏi trùng" là bảo vệ tưởng
  tượng. An toàn thật là **kéo sổ từ Sheets TRƯỚC khi quét** (`run_daily`
  làm ngay đầu `execute_daily_scan()`; kéo hỏng thì dừng phiên) cộng chốt
  chặn trong `push()`. Không kéo trước → `seq` lệch, `push()` bỏ qua dòng
  mới lặng lẽ (14/08: 70 quyết định mất).
- **Chuông** `chuong-bao-quet.yml` chạy 09:23 UTC (16:23 ICT) mỗi ngày làm
  việc, soát **ba** ngày gần nhất, đỏ nếu ngày nào không có lượt `success`.
  Chỉ đếm `conclusion == "success"` (kẹt `queued` không đỏ, không email).
- **Cảnh báo nội phiên** đi bằng `::warning::` + `$GITHUB_STEP_SUMMARY`,
  KHÔNG bằng mã thoát (làm đỏ job quét sẽ sinh báo động giả cho chuông).
  Thứ tự **bắt buộc**: `kéo sổ → cảnh báo → quét → đối chiếu` (đặt cảnh báo
  sau quét thì lệnh đã đóng, không bao giờ kêu). Sổ rỗng thì
  `quet_va_canh_gac()` nạp thử một mã, hỏi một **khoảng** 10 ngày.
- Lượt quét sau đóng cửa là lượt quyết định (`evaluate_open()` chấm trên nến
  ngày).

## Sổ ngoài: `sheets_store.py`

SQLite là máy chạy, Google Sheets là kho bền, **không đồng bộ hai chiều**.

| Bảng | Cách đẩy |
|---|---|
| `decisions` | chỉ thêm dòng có `seq` lớn hơn |
| `trades`, `nhat_ky` | soi gương toàn phần (đổi trạng thái/stop được nâng) |

Bốn bất biến (`tests/test_sheets_store.py`, offline nhờ `InMemorySheet`):
`pull()` **từ chối** ghi vào sổ đang có dữ liệu trừ `allow_overwrite=True`;
lệch cột thì **nổ**; `id`/`seq` giữ nguyên khi khôi phục; vòng đẩy–kéo không
mất gì (NULL ≠ chuỗi rỗng). Cấu hình `.streamlit/secrets.toml`
(`GOOGLE_SHEET_KEY` + `[gcp_service_account]`, xem `secrets.toml.example`);
không cấu hình thì tắt sạch.

**Streamlit Cloud có ổ đĩa TẠM**: mọi file app tự ghi đều mất khi ngủ/redeploy.
App **không được tự push** lên repo nó chạy (vòng lặp redeploy).

---

## Luật làm việc (đều từ sự cố thật)

**Vá file:** chỉ bằng `tools/va_an_toan.py` (chế độ VĂN BẢN, neo `\n` khớp
đúng một lần, ghi qua file tạm). Trong index toàn file text là LF; CRLF
trên đĩa là do `core.autocrlf` — quy ước xuống dòng KHÔNG ảnh hưởng thứ được
commit, và luật "giữ CRLF" cũ đã bị bác (nó sinh 4 lỗi neo-byte trong một
phiên). Cấm `cat >`/`sed -i`/heredoc ghi đè file nguồn (cửa Bash chặn).

**Gác phải đọc AST, không đọc `in`.** `"ten" in src` khớp cả chú thích, nên
xoá lời gọi mà gác vẫn xanh. Mọi khẳng định "file X CÓ GỌI Y" đi qua
`_ten_da_nhap_va_goi()` trong `tests/test_no_fabricated_data.py`. Gác dạng
văn bản chỉ còn cho thứ thật sự là văn bản (CSS trong chuỗi). Công cụ kiểm
tra không chạy được cũng là cổng xanh giả (`kiem_ban_sach` nổ
`UnicodeEncodeError`).

**Test KIỂM LẠI CHÍNH NÓ** (lỗi mắc ba lần một ngày): test dựng lại công thức
của mã rồi so hai bên thì chỉ kiểm công thức của test; mọi đột biến giữ
nguyên GIÁ TRỊ tại điểm đang thử đều sống sót. **Gác một phép SUY RA thì
kiểm HÌNH DẠNG biểu thức bằng AST, không kiểm giá trị.** Và **viết đột biến
TRƯỚC khi tin một gác mới** — ba lần trên đều là gác vừa xanh, vừa vô dụng.
`va_an_toan.dot_bien` lặp cho tới khi MỌI đột biến đều đỏ.

**Gác không RẼ NHÁNH theo giá trị lúc chạy của một cờ** (pytest nạp mọi
module lúc collect nên cờ do thứ tự collect quyết định): rẽ nhánh thì đọc
NGUỒN bằng AST; khẳng định thì đọc lúc chạy. Gác:
`tests/test_gac_khong_phu_thuoc_thu_tu.py`. Mỗi file test phải **xanh khi
chạy một mình** (`tools/kiem_test_chay_rieng.py`, cổng 4).

**Mã tài liệu phải khớp mã thật:** `tests/test_tai_lieu_khop_ten_ma.py` bắt
`module.tên` trỏ vào chỗ không tồn tại (đã chết thì viết trần tên, không viết
dạng `module.tên` trong dấu nháy ngược). `tests/test_tai_lieu_khop_hang_so.py`
đòi giá trị HIỆN TẠI của hằng số cổng C5 (`N_DAY_DU`, `N_TOI_THIEU`,
`MUC_BAT_LOI`, `ROUND_TRIP_COST_PCT`) nằm kề TÊN hằng số; **số cũ được giữ
nhưng phải ĐÁNH DẤU** (🔴/⚠️/HẾT ĐÚNG) — số cũ để trần là bẫy.

**Hook bịa số liệu** `tools/chan_bia_so_lieu.py` (PostToolUse `Write|Edit`,
CHẶN R1–R3, cảnh báo R4–R6; cửa thoát `# bia-ok: <lý do>` bắt buộc có lý do):
R1 `getattr(o,"tên",<số>)`, R2 tên trường giống nhưng không tồn tại, R3
`except … → return <số>`, R4 `.get("k",<số>)`, R5 `x = max(x,<số>)`, R6 `x
or <số>`. Nó là chuông, không phải cửa chống cháy; chỉ thấy Write/Edit của
Claude Code (CI quét toàn repo bằng `--quet-repo`). **Cảnh báo không ai đọc là
cảnh báo không tồn tại:** file nào đã dọn sạch thì cảnh báo của nó thành
bức tường bằng một test riêng (`test_chatbot_khong_bia_va_khong_chet.py`).

**Cửa tự động:** bảy cửa đăng ký MỘT nơi, `~/.claude/settings.json`, đường
dẫn tuyệt đối (repo `.claude/settings.json` không khai hook — khai ở cả hai
thì mỗi hook chạy HAI LẦN). Khai ở `docs/cua-du-an.json`; đọc trạng thái
bằng `tools/kiem_cua_song.py`. `python --version` KHÔNG phải phép thử của cả
bảy (nó chỉ đi qua cửa Bash). Cửa Bash canh tool `Bash|PowerShell`.

**Máy 3.13, CI 3.11:** cú pháp có từ 3.12 (f-string PEP 701) nạp được ở máy
rồi nổ trên runner; `ast.parse(feature_version=…)` KHÔNG bắt được. Cổng 2
(`tools/kiem_cu_phap_311.py`) chạy trình thông dịch 3.11 thật, kiểm cả python
nhúng trong heredoc có trích dẫn của workflow YAML. Mọi file có `__main__`
và `print` phải gọi `sys.stdout.reconfigure(encoding="utf-8")`
(`tests/test_script_chay_duoc_tren_windows.py`).

**Dọn code chết:** dùng AST, đừng grep; `from __future__ import annotations`
KHÔNG phải import thừa (gỡ là CI 3.11 đỏ); khoá cấu hình không ai đọc nguy
hiểm hơn code không ai chạy (`tests/test_trong_so_that_su_duoc_dung.py`,
`tests/test_dau_hieu_tranh_luan.py` khoá trọng số và quy ước dấu
Bull(+)/Bear(−)/Devil(−)); xoá trùng lặp, đừng xoá năng lực.

## Ranh giới không vượt qua

- **Không đặt lệnh thật.** Không commit secrets (`.streamlit/secrets.toml`),
  `*.db`, `sl_pattern_memory.json`, `backtest/cache/`. **Không xoá `*.db` ở
  gốc repo** — dữ liệu đo của người dùng, hỏi trước. Sự cố 12/08/2026
  (`e2f98b4` ghi đè sổ thật bằng backtest in-sample, mất 96/113 lệnh) nay bị
  đóng ở `PaperTradingJournal.__init__`: mở `paper_trades.db` phải khai
  `cho_phep_so_that=True`.
- **Không đẩy thẳng `main`** — nhánh → PR. `main` có ruleset active từ
  21/08/2026 (bắt PR, bắt `kiem-dinh` xanh ở chế độ strict, cấm force-push và
  xoá) và `kiem-dinh.yml` chạy cả trên `push`.
- **Không ép hạng vnstock** trong mã. Không ghi tài liệu skill vnstock ra đĩa.
- Sơ đồ kiến trúc: chỉ **`architecture_asbuilt.html`** nói thật về thứ
  đang chạy; v1/v2 là tham vọng.

## Lệnh hay dùng

```bash
streamlit run app.py                                            # chạy app
./.venv/Scripts/python.exe run_daily.py                         # quét VN100, cập nhật sổ
./.venv/Scripts/python.exe paper_runner.py                      # chạy paper trading
./.venv/Scripts/python.exe extend_history.py --check            # độ phủ dữ liệu
./.venv/Scripts/python.exe tools/doc_so_that.py                 # sổ lệnh THẬT đang có gì

# NĂM CỔNG, tuần tự, KHÔNG song song (vài test ghi thư mục tạm vào gốc repo nên
# chạy song song cho ĐỎ GIẢ). Ghi ra file log, đừng pipe qua `tail`.
./.venv/Scripts/python.exe -m pytest tests/ -q                  # cổng 1
./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py            # cổng 2 — CI cũng chạy
./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo      # cổng 3
./.venv/Scripts/python.exe tools/kiem_test_chay_rieng.py --im         # cổng 4 — xanh MỘT MÌNH
./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py           # cổng 5 — thứ BỊ MẤT

./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-thay-doi  # chỉ file đã đổi (hook Stop)
./.venv/Scripts/python.exe tools/soat_lenh_tai_lieu.py          # lệnh trong tài liệu có chạy được
```

Kiểm định kỳ những chỗ hỏng âm thầm: `market_filter.status()` (bộ lọc
VN-INDEX có bật thật không), `data_quality.price_multiplier()` (nghìn đồng
↔ VNĐ), `mau_bang_gia.doc_bang_gia("SSI")`.
