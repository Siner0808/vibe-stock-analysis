# Thiết kế C1 — Sân đấu: nhiều phương án bóng chạy song song, mỗi phương án một tài khoản ảo

**Mốc:** C1 (`docs/LO-TRINH.md`, giai đoạn C). **Duyệt hướng:** người dùng, 28/10/2026, trong phiên leader (BƯỚC 238).
**Trạng thái:** đặc tả **ĐÃ CHỐT** ngày 28/10/2026; chưa có dòng mã nào. Bản đầu của đặc tả (cùng ngày) để hai chỗ mang nhãn *"đề xuất — người dùng chốt khi duyệt đặc tả"* (độ dài khối ở mục 8.3, thước 1 ở mục 8.2) và năm câu mở khác; người dùng đã trả lời cả bảy, nguyên văn ở mục 15. Nhãn "đề xuất" còn nằm trong văn bản làm LỊCH SỬ, mỗi chỗ kèm dòng *ĐÃ CHỐT*.

Tài liệu này là đề bài cho các phiên làm mã. Luật chung của dự án (vá file, đột biến, năm cổng, giao PR) nằm ở skill `quy-trinh-lam-viec` — đi theo nó, đừng chép lại vào đây. Mọi `file:dòng` bên dưới được `grep` lại ở cây `9cb325e` ngày 28/10/2026; số dòng trôi theo mã, tên hàm thì không.

---

## 1. Mục đích và liên kết với T4

`docs/LO-TRINH.md` :206: *"C1 — Nhiều phương án bóng chạy song song, mỗi phương án một tài khoản ảo riêng."* Tiêu chí ra khỏi lộ trình T4 (:61): *"Sân đấu có ít nhất 3 phương án bóng so với rổ, kèm khoảng tin cậy."*

C1 dựng **sân đấu**: ba phương án bóng THĂM DÒ, một tài khoản "đường thật phát lại", một tài khoản rổ đều, mỗi tài khoản có tiền mặt, vị thế, khớp lệnh, phí và đường vốn riêng, cùng ăn một chuỗi tín hiệu đã ghi. Mỗi phương án được so với rổ và so với đường thật, kèm khoảng tin cậy có **độ phủ đã đo**. Ba phương án thăm dò đủ vế "ít nhất 3" của T4; vế "khoảng tin cậy" là mục 8.

Điều C1 **không** là: không là đường lên bản (mục 14), không là vòng xác nhận của tầng 3 (`cham_bong.py`), không đổi K. C2 (tách thăm dò / xác nhận) và C3 (đề xuất tự soạn) đứng sau.

## 2. Quyết định của người dùng (nguyên văn lựa chọn, 28/10/2026)

| Câu hỏi | Trả lời |
|---|---|
| Nhịp độ | Sau câu *"tôi muốn đẩy nhanh tiến độ"*: *"Bắt đầu C ngay, C1 trước (Recommended)"* (giai đoạn C kéo sớm từ 01/12/2026) và *"Hoãn việc quy trình không chặn (Recommended)"* |
| Ba phương án bóng đầu tiên (đều lớp THĂM DÒ: không bao giờ lên bản, không tính vào K) | *"Nghỉ sau lỗ + độ rộng + kế hoạch B6 (Recommended)"* |
| Cách phát lại | *"Phát lại thuần, không ghi Sheets (Recommended)"* |
| Cách dựng bộ máy | *"Đồng ý cách A (Recommended)"* |
| Thống kê và hiển thị | *"Duyệt, giao phiên con viết đặc tả (Recommended)"* |

Hệ quả đã chốt từng điều:

1. **Ba phương án** (mục 3). (1) nghỉ sau lỗ 7 ngày lịch — ĐO 30. (2) độ rộng thị trường thay cổng VN-INDEX — ĐO 32. (3) vào lệnh theo kế hoạch B6 — mốc C7 ở `docs/LO-TRINH.md` :211.
2. **Phát lại thuần.** Đầu vào chỉ là tab `decisions` đã ghi, tab `ke_hoach` (có từ BƯỚC 195, 15/10/2026) và giá. KHÔNG ghi Sheets. Dữ liệu trước ngày khai của một phương án mang nhãn **"đã nhìn"** và báo riêng. Pha tiến-về-trước của sổ bắt đầu ở tín hiệu ≥ 2026-08-28 (`tools/doc_so_that.py` :87, cờ `--moc-tin-hieu`).
3. **Cách A: chạy bộ máy THẬT.** `paper_trading.consider_entry` (:794) và phần thoát lệnh nhận cờ qua tham số/cấu hình thay vì biến module; mặc định không đổi nên đường thật không đổi. **Gác ĐẦU TIÊN là phép thử tương đương**: phát lại với cờ mặc định phải ra ĐÚNG các lệnh của sổ thật. Đã loại cách B (chấm lại điểm bằng `walkforward.py`: vi phạm quy ước 1 của `cham_bong.py` :13, *"điểm đã ghi"*) và cách C (dựng bộ máy tối giản mới).
4. **Thống kê và hiển thị** (mục 8–10): lợi nhuận mỗi phiên của mỗi tài khoản trừ rổ, mỗi phương án còn so với đường thật; giữ alpha từng lệnh của `paper_metrics.vs_benchmark` (:264); KTC bootstrap khối CÓ CẶP; độ phủ đo bằng mô phỏng ở n = 40, 113, 252 trước khi in "95%"; không Reality Check / Romano-Wolf ở C1; tab app chỉ-đọc "🏟️ Sân đấu" + `tools/san_dau.py` chỉ-đọc; biểu ngữ "THĂM DÒ — không bao giờ lên bản".
5. **Chia bốn BƯỚC**, mỗi BƯỚC một lát cắt dọc, `Mốc: C1` (mục 12).
6. **Ngoài phạm vi** (mục 14): không ghi Sheets; không đường lên bản; không đổi K hay `docs/ung-vien.json`; **UV-001 không bao giờ hiện như một bóng** — nó chỉ được đọc đúng một lần ở 252 phiên có nhãn (`cham_bong.py` quy ước 5, :28), và hiện P&L của nó dọc đường là nhìn trộm.

## 3. Ba phương án và bộ cờ

| Mã | Phương án | Cờ ở nguồn | Ghi chép đo |
|---|---|---|---|
| PB-001 | Nghỉ 7 ngày lịch sau lệnh LỖ, cùng mã | `paper_trading.NGHI_SAU_LO_NGAY` = 0 mặc định (:313); đặt 7 | ĐO 30, kết cục A⁺, gác lại (STATE BƯỚC 221, 227, 228) |
| PB-002 | Độ rộng thị trường thay cổng VN-INDEX | `paper_trading.DO_RONG_NGUONG` = 0 mặc định (:353) đặt 0,50; `paper_trading.CONG_VNI_BAT` = True mặc định (:347) đặt False | ĐO 32, kết cục A⁺, gác lại (STATE BƯỚC 224, 225, 227) |
| PB-003 | Vào lệnh theo kế hoạch B6 | không phải cờ — luật khớp vào (mục 7) | `docs/LO-TRINH.md` :211 (C7); ĐO 25 kết cục B |

PB-002 là **một bộ hai cờ tương tác**: tắt cổng VN-INDEX và bật cổng độ rộng đi cùng nhau; tách ra là sai ý (độ rộng *thay* cổng, không *thêm vào*). Giá trị 0,50 là giá trị lượt B của ĐO 32 (`paper_trading.py` :352, trong chú thích của cờ); chép lại từ `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 32 ở BƯỚC 3, không gõ từ trí nhớ.

Cả ba ở lớp **`tham_do`**: không tính vào K, không có đường tới `UV-`. Đây là ba phương án đã được ĐO trên cache (ĐO 30, 32) và ĐO 25 — sân đấu cho chúng một lượt thử **tiến-về-trước**, không phải một phép đo thứ hai trên dữ liệu cũ.

## 4. Kiến trúc và luồng dữ liệu

Khuôn B1: một module THUẦN ở gốc repo + một dụng cụ I/O ở `tools/` cùng tên (`hau_kiem_loi.py` + `tools/hau_kiem_loi.py`).

```
Google Sheets (CHỈ ĐỌC)               Giá (CHỈ ĐỌC)
  tab decisions ─┐                      cache lịch sử cục bộ / đường giá của app
  tab ke_hoach  ─┤                      │  OHLCV các mã + VN-INDEX
  tab trades   ──┤ (chỉ cho phép thử    │
                 ▼  tương đương)        ▼
        tools/san_dau.py  (I/O: kéo vào DB TẠM như tools/doc_so_that.py, đọc giá)
                 │  dữ liệu thô -> khung bảng
                 ▼
        san_dau.py  (THUẦN, không mạng, không đĩa, không đồng hồ)
          ├─ phat_lai(cau_hinh, quyet_dinh, gia, ke_hoach)  -> TaiKhoan
          │     mỗi phiên, mỗi mã: MỘT bước tài khoản dùng chung
          │     (paper_runner: bước phiên chung, mục 5) trên PaperTradingJournal(":memory:")
          ├─ ro_deu(gia) -> TaiKhoan "rổ"
          ├─ loi_nhuan_phien(tai_khoan) -> chuỗi lợi nhuận mỗi phiên
          └─ khoang_tin_cay_cap(...), do_phu(...), bang_san_dau(...)
                 │
        ┌────────┴─────────┐
        ▼                  ▼
  tools/san_dau.py     app.py: tab "🏟️ Sân đấu"
  (in bảng, kiểm        (CHỈ ĐỌC, CHỈ IN — không tính lại, không ghi)
   tương đương, đo phủ)
```

1. **Mỗi tài khoản = một `PaperTradingJournal(":memory:")`** + một `CauHinhVao`. Bộ máy khớp lệnh, phí, trượt giá, bước giá, lô chẵn, khoá biên, trần vốn, cắt lỗ, trailing là bộ máy THẬT (cách A). Phí và trượt giá **KHÔNG** là cờ của phương án: cùng một thị trường cho mọi tài khoản. Phương án nào đòi đổi chúng là một thị trường khác, ngoài C1.
2. **Điểm là điểm ĐÃ GHI** (quy ước 1, `cham_bong.py` :13; quy ước 2 — mỗi (mã, phiên) một lần, giữ dòng ghi sau cùng — :20, cùng cách `cham_bong.doc_quyet_dinh` :109 làm). `san_dau.py` KHÔNG gọi `paper_runner._analyze` (:168) hay `MasterConsensusAgent`: gác AST (mục 11).
3. **Cái bộ máy cần mà sổ không ghi: giá vào / cắt lỗ / chốt lời.** `consider_entry` đọc `result["analyses"]["risk"]["recommendations"]` (`paper_trading.py` :837–:862). Tab `decisions` KHÔNG mang chúng (cột: `score`, `recommendation`, `acted`, `skip_reason`, `components`, `reasons`, `data_quality` — `paper_trading.py` :606). Chúng là **hàm thuần của giá**: `analysis_agents.RiskManagementAgent` (:361) dựng `stop_loss_price` từ ATR (`sl_fraction` ở :448, kẹp 4%–6,5%) và `entry_price` từ giá đóng cửa. Nên phát lại dựng lại ĐÚNG phần rủi ro ấy (chỉ agent rủi ro, trên lịch sử cắt tới hết ngày tín hiệu, cùng `DataOrchestrator._compute_local_indicators` như `_analyze`), KHÔNG chấm lại điểm. Việc dựng lại này được **chứng minh** bằng phép thử tương đương: với mọi lệnh thật, `stop_loss`, `take_profit`, `size_pct`, `entry_price` dựng lại phải bằng cột tương ứng của tab `trades` (mục 6).
4. **Ba nguồn dữ liệu ngoài điểm, mỗi nguồn một "độ phủ" phải in ra**, vì thiếu dữ liệu đầu vào không được phép lặng lẽ thành "không chặn":
   - VN-INDEX tại ngày tín hiệu (cổng của PB-001 không cần; cổng mặc định cần): `market_filter.is_vni_bullish` (:267) đọc cache toàn cục và nổ `CacheQuaHanError` khi cache cũ. Phát lại đưa nó vào qua **nguồn tiêm được** (mục 5), cùng phép so MA50 `<=` ngày tín hiệu.
   - Độ rộng thị trường: `do_rong.do_rong_mac_dinh` (:81) đọc cache 71 mã. Cờ ở nguồn nói *"độ rộng thiếu thì không chặn"* (`paper_trading.py` :351). Trong sân đấu điều đó là **bẫy**: ngày cache chưa tới thì PB-002 âm thầm thành đường thật. Luật của C1: ngày nào thiếu độ rộng thì phiên ấy **bị loại khỏi cửa sổ của PB-002** và đếm trong cột "độ phủ cổng"; không bao giờ coi là "không chặn". **SỬA 29/10/2026 (BƯỚC 242, người dùng: *"Tính từ cùng nguồn giá của bản phát lại (Recommended)"*):** độ rộng dựng từ CHÍNH các khung giá mà bản phát lại dùng (`san_dau.co_tu_gia`), nên có giá là có độ rộng; ngày độ rộng VẪN thiếu thì phiên ấy bị loại khỏi cửa sổ so sánh của **MỌI** tài khoản (đường thật, mọi phương án, rổ — không chỉ PB-002), phương án có cổng độ rộng KHÔNG mở lệnh nào ở ngày ấy (nguồn trả 0,0 để bộ máy chặn, vì bộ máy hiểu None là "không chặn"), và lệnh có ngày tín hiệu ở đó không vào số lệnh, nhãn, đường vốn hay alpha từng lệnh của tài khoản nào. Hệ quả khai thẳng: tập mã tính độ rộng là tập mã có quyết định, KHÁC tập "mọi mã của thư mục cache" mà `do_rong.do_rong_mac_dinh` dùng.
   - Giá các mã và rổ: tới ngày nào. Phiên-mã không có nến thì không có khớp, không có đóng; đếm và in.
5. **Phiên-mã thiếu điểm** (không có dòng quyết định): không chấm thoát theo điểm (`current_score=None`), không xét mở lệnh; đếm theo tài khoản. Phép thử tương đương đòi số này bằng 0 trong cửa sổ của nó.
6. **Thứ tự xử lý mã trong một phiên** = thứ tự `(at, seq)` của dòng quyết định được giữ (trần vốn phụ thuộc thứ tự mở lệnh trong phiên). Đây là rủi ro đã biết: lượt quét nhiều lần trong ngày có thể đổi thứ tự. Phép thử tương đương là máy phát hiện; nếu nó đỏ vì thứ tự, đặc tả được sửa trước khi đi tiếp, không "chỉnh cho khớp".
7. **Cửa sổ kế toán.** Mọi tài khoản bắt đầu ở cùng một phiên: tín hiệu đầu tiên ≥ `NGAY_MO_CONG` = 2026-09-28 (cổng mở lệnh mở từ ngày ấy, `CLAUDE.md` mục *Sổ lệnh giấy*, STATE BƯỚC 138). Trước ngày ấy `CHO_PHEP_MO_LENH_MOI` = False và sổ thật không có lệnh mới; để phương án bóng giao dịch trong tháng đó là so táo với cam (phần chênh với đường thật khi ấy là "cổng mở hay đóng", không phải luật của phương án). Nhãn dữ liệu (độc lập với cửa sổ):
   - tín hiệu < 2026-08-28: lượt MÔ PHỎNG lịch sử, không phải tiến-về-trước — không vào thống kê nào;
   - 2026-08-28 ≤ tín hiệu < `khai_ngay` của phương án: **"đã nhìn"**, báo riêng;
   - tín hiệu ≥ `khai_ngay`: **"chưa nhìn"**, báo riêng.
   Vị thế mở trước `NGAY_MO_CONG` còn sống ở ngày ấy (nếu có) được **chép nguyên văn từ sổ thật vào MỌI tài khoản** (kể cả bóng) lúc bắt đầu, để sai khác giữa các tài khoản chỉ còn là luật. Số này đo ở BƯỚC 2 bằng `tools/doc_so_that.py`, KHÔNG ghi ở đây (Quy tắc 2).

## 5. Hợp đồng sửa bộ máy (BƯỚC 1)

Mục tiêu: **hành vi đường thật giữ nguyên từng bit**, chứng minh bằng test.

1. **`CauHinhVao`** — dataclass `frozen=True` ở `paper_trading.py`, cạnh các cờ. Trường: `cho_phep_mo_lenh_moi`, `buy_threshold`, `tran_von_cam_ket_pct`, `cong_vni_bat`, `do_rong_nguong`, `nghi_sau_lo_ngay`, `loc_imom_phan_vi`, `chot_sut_giam_nguong`, `chot_sut_giam_phien`, `exit_signal_threshold`, `max_hold_sessions`, `chot_loi_cung`, `luat_vao` (mục 7; mặc định `"MO_CUA_SAU"`, hoặc `"KE_HOACH_B6"`). Tên trường = tên cờ ở nguồn, chữ thường. `luat_vao` là CỜ CHỌN; đối tượng `luat_khop` truyền cho `fill_pending` được dựng từ nó (và từ dòng `ke_hoach`) ở bộ phát lại, không nằm trong cấu hình.
2. **`CauHinhVao.tu_module()`** dựng cấu hình bằng ĐỌC biến module **tại lúc gọi**. Mọi nơi hiện đặt cờ bằng cách gán biến module (`tools/do30_nghi_sau_lo.py`, `tools/do32_do_rong.py`, test dùng `monkeypatch`) vẫn đúng nghĩa, vì không ai bắt họ đổi.
3. **`consider_entry(..., cau_hinh=None)`**, **`evaluate_open(..., cau_hinh=None)`**, **`ngay_ra_lo_gan(..., cau_hinh=None)`**, **`dang_dong_bang(..., cau_hinh=None)`**, **`fill_pending(..., luat_khop=None)`**: `None` → `CauHinhVao.tu_module()` / hành vi hiện tại. Thân hàm đọc `cau_hinh.<trường>` thay cho tên module trần. Hàm cổng phụ (`do_rong_bi_chan` :359, `phan_vi_imom_bi_loc` :329) nhận ngưỡng qua tham số, giữ nguyên chữ ký cũ khi gọi không tham số.
4. **Nguồn tiêm được** `NguonThiTruong` (giao thức hai hàm): `vni_tren_ma50(ngay) -> bool` và `do_rong(ngay) -> float | None`. Mặc định (`None`) gọi `market_filter.is_vni_bullish` và `do_rong.do_rong_mac_dinh` đúng như hôm nay, kể cả để `CacheQuaHanError` đi ra ngoài. **C1 chỉ tiêm được hai nguồn này**; IMOM và chốt sụt giảm của sổ (`chot_sut_giam.lich_phien_mac_dinh`) giữ đường module — nên máy kiểm sổ phương án (mục 11) từ chối mọi phương án bật `loc_imom_phan_vi` hay `chot_sut_giam_nguong` cho tới khi có nguồn tiêm cho chúng.
5. **Bước phiên chung.** Rút thứ tự bốn bước của `paper_runner.run_session` (:259; thứ tự ghi ở docstring đầu `paper_runner.py`: khớp vào → khớp ra → xét thoát → xét vào) ra MỘT hàm `buoc_phien(nhat_ky, ma, lich_su, nen, ngay, san, cau_hinh, cham_diem, chi_khop)`, trong đó `cham_diem` là hàm trả `result`. `run_session` thành vỏ mỏng: truyền `cham_diem = lambda: _analyze(...)`. Phát lại truyền `cham_diem` trả `result` dựng từ dòng đã ghi + phần rủi ro dựng lại. **Một chỗ giữ thứ tự bốn bước**, nên phát lại không thể trôi khỏi đường thật về thứ tự (ý "một bước tài khoản dùng chung" mượn từ martex-quant, mục 13).
6. **Chứng minh không đổi hành vi (gác của BƯỚC 1):**
   - toàn bộ test hiện có xanh KHÔNG sửa;
   - một test "vàng" chạy MỘT kịch bản nhiều mã, nhiều phiên (kể cả cổng VN-INDEX, trần vốn, cắt lỗ, thoát theo điểm, trần giữ lệnh, lệnh bị chặn) qua `run_session`; bảng kết quả kỳ vọng nhúng trong test được sinh bằng mã **TRƯỚC khi sửa** (lệnh sinh ghi ở docstring, chạy trên `main` `9cb325e`);
   - gác AST: mỗi cờ trong `CauHinhVao` chỉ được đọc ở `tu_module()`; hàm trong lớp `PaperTradingJournal` không còn đọc tên cờ trần (đột biến: thêm lại một lần đọc trần → đỏ);
   - `paper_trading` vẫn không nhập `san_dau` (mục 11).
7. Cờ ĐO đã có (`LOC_IMOM_PHAN_VI`, `CHOT_SUT_GIAM_*`, `DUNG_MUC_FIBONACCI`, `MO_PHONG_TRUOT_GIA`, `VON_DANH_MUC_VND`) **không** đổi chỗ ở trừ những cờ nằm trong danh sách 1. Phần còn lại là thị trường chung.

## 6. Phép thử tương đương — định nghĩa

Đây là gác đầu tiên của cách A. Hai tầng, vì một tầng không đủ:

**Tầng A — trong CI, offline, dữ liệu tổng hợp.** Một kịch bản nhiều mã/nhiều phiên dựng sẵn (giá + điểm + rủi ro viết tay). Chạy một lần bằng `run_session` (đường thật, `_analyze` được thay bằng bản kịch bản), một lần bằng `phat_lai` với `CauHinhVao.tu_module()`. Bảng `trades` hai bên **bằng nhau từng cột** (`symbol`, `signal_date`, `entry_date`, `entry_price`, `exit_date`, `exit_price`, `exit_reason`, `stop_loss`, `take_profit`, `size_pct`, `entry_score`, `status`). Tầng A chứng minh bộ phát lại = bộ chạy thật *về cơ chế*, độc lập với dữ liệu Sheets.

**Tầng B — trên sổ thật, chạy bằng tay mỗi BƯỚC chạm sân đấu (`tools/san_dau.py tuong-duong`).** Kéo tab `decisions`, `trades` vào DB TẠM (đường `tools/doc_so_that.py` :`keo_ve_so_tam`, chỉ đọc), phát lại cờ mặc định từ `NGAY_MO_CONG`, rồi so với các lệnh thật có `signal_date` trong cửa sổ:
- cùng tập khoá `(symbol, signal_date)`;
- mọi cột ở Tầng A bằng nhau;
- số phiên-mã thiếu điểm = 0; số phiên-mã thiếu nến = 0.
Khác một ô nào → **đỏ**, in từng sai khác, không có "dung sai". Kết quả (số lệnh so, số khớp) ghi vào STATE của BƯỚC đó; số ấy do lệnh tính, không do đặc tả này.

**Giới hạn khai thẳng.** Bộ máy thật đổi hành vi ở BƯỚC 209 và 212 (20–21/10/2026: khoá biên, cắt lỗ ở phiên chỉ-khớp) và thêm cờ ở BƯỚC 221–226. Lệnh mở bằng bộ máy cũ có thể khác khi phát lại bằng bộ máy hiện hành mà KHÔNG phải lỗi của phát lại. Vì thế Tầng B khai ngày bắt đầu của nó = `max(NGAY_MO_CONG, ngày tín hiệu đầu tiên mà cả đời lệnh nằm dưới bộ máy hiện hành)`, và BƯỚC 2 in cả hai ngày. Nếu cửa sổ ấy quá ít lệnh để phán, BƯỚC 2 **không đóng**: nêu số lệnh thật còn lại, và việc tiếp (chờ thêm lệnh đóng) là việc của người dùng. Tầng A vẫn bắt buộc xanh.

## 7. Mô hình khớp B6 (PB-003) — dùng lại của ĐO 25

Nguồn: `tools/do25_ke_hoach_vao_lenh.py::tim_khop` (:178), phép đo thăm dò đã ký (kết cục B, BƯỚC 179).

- Đầu vào của một tín hiệu: dòng tab `ke_hoach` theo khoá `(symbol, signal_date)` (cột `phan_quyet`, `vung_day`, `vung_tran`, `so_phien_cho`; `so_ke_hoach.py` :35).
- `MUA_NGAY` → vào như đường thật (mở cửa phiên sau). `BO_QUA` và `CHUA_LAP_DUOC` → không vào lệnh (như ĐO 25: *"mọi phán quyết khác không nắm giữ"*). Tín hiệu đủ điểm mà **không có dòng `ke_hoach`** → không vào lệnh và được ĐẾM trong "thiếu kế hoạch", không đoán.
- `CHO_VUNG` → lệnh giới hạn mua ở `vung_tran`, hiệu lực `so_phien_cho` phiên kể từ phiên SAU ngày tín hiệu (`ke_hoach_vao_lenh.SO_PHIEN_CHO` = 5, :117). **Khớp nghiêm** (cái đã ký ở ĐO 25, không phải biến thể "chạm là khớp"): khớp ở phiên d đầu tiên có `low(d)` ≤ `vung_tran` trừ MỘT bước giá (`truot_gia.buoc_gia`); giá khớp cơ sở = `min(open(d), vung_tran)`. Không khớp hết hạn → lệnh bị huỷ, không giữ.
- Giá khớp cơ sở đi qua `PaperTradingJournal._khop_that` (trượt giá, lô chẵn, biên) như mọi lệnh khác — khác ĐO 25 (đo thăm dò chưa tính ma sát) và đúng ý "bộ máy thật".
- **Chỉ ĐỔI LUẬT VÀO.** Cắt lỗ, cỡ vị thế, chốt, trailing, thoát theo điểm, trần giữ lệnh đều của bộ máy (SL từ phần rủi ro dựng lại, không phải `cat_lo` của kế hoạch). Một thay đổi một yếu tố; dùng `cat_lo` là phương án khác (mục 15, quyết định 4c — ĐÃ CHỐT).
- Hook trong bộ máy: `fill_pending(..., luat_khop=None)` (mục 5). `luat_khop` là đối tượng có `xet(lenh, ngay, nen) -> (khop, gia_co_so, het_han)`. Lệnh hết hạn được phát lại đổi sang trạng thái riêng `EXPIRED` **bằng SQL ở bộ phát lại trên DB bộ nhớ**, không thêm trạng thái vào lớp `Status` của đường thật (đường thật không bao giờ sinh nó; `von_dang_cam_ket` :781 chỉ đếm `OPEN`/`PENDING` nên tự giải phóng vốn).
- **Dùng chung `tim_khop`** (BƯỚC 4): chuyển hàm ra một module thuần dùng chung (`khop_gioi_han.py`); `tools/do25_ke_hoach_vao_lenh.py` nhập lại và vẫn export tên cũ để `tests/test_do25_ke_hoach_vao_lenh.py` (gọi `D.tim_khop`) giữ xanh KHÔNG sửa.
- **Dữ liệu bắt đầu muộn hơn.** Tab `ke_hoach` có từ BƯỚC 195 (15/10/2026). PB-003 có cửa sổ riêng bắt đầu ở tín hiệu có `ke_hoach` đầu tiên (đo bằng lệnh ở BƯỚC 4, không ghi ở đây); so sánh PB-003 với đường thật và rổ chỉ trên **cửa sổ chung** của cặp (mục 15, quyết định 4b — ĐÃ CHỐT).

## 8. Thống kê

### 8.1 Chuỗi đo

Mỗi tài khoản có **chuỗi lợi nhuận mỗi phiên** `r_t` tính bằng **điểm phần trăm vốn**, cộng dồn (không tái đầu tư: `size_pct` là phần trăm vốn ban đầu — `paper_trading.py` :294):
- ~~vị thế đang giữ ở phiên t đóng góp `w × (đóng cửa_t / đóng cửa_{t-1} − 1)`, `w = size_pct/100`;~~ **THAY THẾ 29/10/2026 (lỗi 197, BƯỚC 242; người dùng: *"Nhận Δgiá/giá vào (Recommended)"*):** vị thế đang giữ ở phiên t đóng góp `w × (đóng cửa_t − đóng cửa_{t-1}) / giá vào`, `w = size_pct/100` (lệnh giữ SỐ CỔ PHIẾU cố định, đúng nghĩa *"không tái đầu tư"*). Câu cũ tự mâu thuẫn với gác bảo toàn ngay bên dưới: tổng các lợi nhuận đơn mỗi phiên không bằng lợi nhuận đơn cả kỳ (+10% rồi −10% cộng 0, nhân −1%), nên không thể bằng `size_pct/100 × net_return_pct` "sai số số học". Chia cho giá vào thì các đoạn phiên thu gọn về `w × (giá ra − giá vào) / giá vào`. Cài ở `san_dau.dong_gop_lenh`;
- phiên khớp vào: từ giá vào tới đóng cửa; phiên khớp ra: từ đóng cửa phiên trước tới giá ra (cùng hiệu giá, chia cho giá vào);
- phí khứ hồi trừ ở phiên khớp ra, đúng phần `gross_return_pct − net_return_pct` của lệnh đó.
**Gác bảo toàn:** với mỗi lệnh đã đóng, tổng đóng góp qua các phiên = `size_pct/100 × net_return_pct` (sai số số học). Máy đo hỏng im lặng (skill `quy-trinh-lam-viec`, Bước 3 điều 4): đường vốn sai thì mọi KTC đều sai mà vẫn trông hợp lý.

**Rổ** = rổ đều trọng số của `paper_runner.build_benchmark` (:484) áp theo phiên: lợi nhuận mỗi phiên = trung bình lợi nhuận một phiên của các mã đủ nến hai phiên liền. Tài khoản rổ luôn đầu tư 100%.

### 8.2 Hai thước, một chỗ tính

- **Thước 1 — tài khoản trừ rổ, khớp mức đầu tư:** `x_t = r_t(tài khoản) − e_t × r_t(rổ)`, `e_t` = tổng `size_pct/100` đang cam kết ở đầu phiên t. *Bản đầu ghi "đề xuất — người dùng chốt khi duyệt đặc tả"; **ĐÃ CHỐT 28/10/2026**, người dùng: "Khớp mức giải ngân (Recommended)" (mục 15, quyết định 2).* Lý do của đề xuất: nếu trừ thẳng rổ 100% thì tài khoản chỉ cầm 56% vốn (con số cũ của ĐO 22, CLAUDE.md) sẽ thua rổ trong thị trường lên chỉ vì tiền mặt, không vì chọn mã. Cột thứ hai LUÔN in cạnh: `r_t(tài khoản) − r_t(rổ)` thô. Phiên `e_t = 0` cho `x_t = 0` và **được đếm riêng** ("phiên không giữ"), không làm tăng n hiệu dụng.
- **Thước 2 — phương án trừ đường thật:** `d_t = r_t(phương án) − r_t(đường thật phát lại)`, chỉ trên các phiên của cửa sổ chung.
- **Alpha từng lệnh** của `paper_metrics.vs_benchmark` (:264) giữ nguyên, tính riêng cho từng tài khoản trên các lệnh đã đóng của nó. Đó là một ĐỐI TƯỢNG KHÁC (mẫu = lệnh, bootstrap độc lập từng lệnh, ngưỡng n ≥ 10 của nó); không được "đối chiếu" hai KTC với nhau.

### 8.3 KTC bootstrap khối CÓ CẶP

Thống kê: **trung bình** của chuỗi (`x_t` hoặc `d_t`). Cộng dồn trên cửa sổ = trung bình × n (in cạnh, không có KTC riêng).
- **Có cặp** nghĩa là: mỗi lần rút, MỘT bộ khối được chọn và áp cho mọi chuỗi liên quan (với `x_t` và `d_t` đã là chuỗi hiệu nên cặp nằm sẵn trong chuỗi; hàm vẫn nhận hai chuỗi A, B và rút khối chung để tính KTC của `mean(A) − mean(B)` — dùng cho cả hai thước và cho phép thử độ phủ ở dạng cặp).
- Bootstrap khối vòng, khối cố định `L`, rút `ceil(n/L)` khối, cắt về n; 5000 lần rút (cùng `VONG` với `paper_metrics.vs_benchmark`), khoảng phân vị 2,5–97,5, hạt giống cố định 0.
- 🔴 **THAY THẾ ở BƯỚC 248 (30/10/2026): độ dài khối KHÔNG còn là 10 phiên cố định mà là quy tắc Politis–White tính từ chính chuỗi (mục 8.4b khoản 6). Bản 10 phiên dưới đây giữ làm LỊCH SỬ — nó đã được đo lại dưới mô hình sinh đúng và THẤT BẠI ở n = 40 (84,4–87,2%).** Người dùng 29/10/2026: *"Sửa cách tính trước lần đọc thật đầu tiên (Recommended)"*; 30/10/2026: *"Duyệt, sửa câu KTC (Recommended)"*.
- **Độ dài khối `L` = 10 phiên — ĐÃ CHỐT 28/10/2026, người dùng: *"10 phiên (Recommended)"* (mục 15, quyết định 1).** Bản đầu ghi nó là *"đề xuất — người dùng chốt khi duyệt đặc tả"*. Lý do của đề xuất:
  - thời gian giữ lệnh trung bình của hệ là 20,3 phiên (`cham_bong.py` :82, `NHIP`); hai phiên cách nhau dưới chừng đó cùng chịu các vị thế đang mở nên `x_t` tự tương quan, và khối phải đủ dài để giữ nó;
  - nửa chu kỳ giữ lệnh là điểm giữa: dài hơn nữa (≥ 21) làm số khối quá ít ở mẫu ngắn, ngắn hơn (quy tắc `n^(1/3)` cho 3–6 phiên ở n = 40–252) bỏ sót phần lớn phụ thuộc đã biết;
  - nó được **ghim trước khi thấy dữ liệu thật** và chỉ đổi bằng một commit sửa đặc tả TRƯỚC lượt đọc đầu tiên trên dữ liệu thật (không đổi sau khi nhìn).
  Ở n = 40 chỉ có 4 khối: KTC sẽ rộng/thiếu phủ — đó chính là điều phép thử độ phủ (8.4) phải nói ra bằng nhãn "mẫu quá ngắn", không phải điều để chỉnh `L` cho đẹp.
- BƯỚC 3 in thêm độ phủ ở `L ∈ {5, 10, 21}` làm bảng nhạy cảm (thông tin, không dùng để chọn `L`).

### 8.4 Phép thử độ phủ — đo trước khi in "95%"

`prism` tự báo độ phủ 0,908 cho KTC danh nghĩa 95% ở 250 kỳ (*tác giả tự báo*, mục 13): bootstrap khối thiếu phủ ở mẫu ngắn là chuyện đã biết, nên C1 không in "95%" trần.
- 🔴 **MÔ HÌNH SINH Ở DÒNG DƯỚI SAI, đã thay ở BƯỚC 248 (mục 8.4b): "tự tương quan do vị thế chồng nhau (trung bình trượt cửa sổ 20 phiên của nhiễu)" cho tự tương quan bậc 1 cỡ 0,9 mà chuỗi thật không có (0,04); mọi độ phủ dưới 90% của BƯỚC 243 là hệ quả. Số lần lặp nay là 10.000, mô hình là GARCH(1,1) đuôi t.**
- **Mô phỏng (bản của BƯỚC 243, đã thay):** với n ∈ {40, 113, 252}, 2000 lần lặp, mỗi lần dựng một cặp chuỗi có trung bình thật bằng 0 và cấu trúc giống thứ cần đo: thành phần chung giữa hai chuỗi (cặp), tự tương quan do vị thế chồng nhau (trung bình trượt cửa sổ 20 phiên của nhiễu), đuôi dày (phân phối t, 4 bậc tự do), và đoạn không giữ (e_t = 0). Đếm tỷ lệ KTC chứa 0, cho cả `mean(A) − mean(B)` (dạng cặp) và `mean(x)` (một chuỗi).
- **Cố định trước khi chạy:** hạt giống, số lần lặp, mô hình sinh, lưới n (khai ở đặc tả này; sửa là sửa đặc tả). Kết quả ghi vào `docs/san-dau-do-phu.json` (dữ liệu đo, commit cùng BƯỚC 3; app chỉ ĐỌC file ấy).
- **Hiển thị:** KTC luôn in dạng *"KTC danh nghĩa 95% — độ phủ đo được <p>% (n=<n lưới>, khối=PW)"* (BƯỚC 248; trước đó `L=10`). n thực không có trên lưới → dùng điểm lưới lớn nhất ≤ n; n < 40 → *"mẫu quá ngắn"*, không in KTC. **Độ phủ < 90% → nhãn "mẫu quá ngắn: độ phủ đo được dưới 90%"** cạnh KTC. Ngưỡng 90% do người dùng duyệt.
- Phép thử độ phủ dùng chính hàm KTC của app (cùng mã, không bản sao), nên "độ phủ đã đo" là độ phủ của thứ đang in.

### 8.4b KHAI TRƯỚC của BƯỚC 248 (30/10/2026) — sửa cách tính KTC cho tới khi độ phủ ≥ 90%

> Khai ở một commit RIÊNG, TRƯỚC khi chạy độ phủ của BẤT KỲ ứng viên nào dưới mô hình mới (lúc khai chỉ có một độ phủ trong tay: bảng của BƯỚC 243 dưới mô hình CŨ, đã nằm trong `docs/san-dau-do-phu.json`). Người dùng 29/10/2026: *"Sửa cách tính trước lần đọc thật đầu tiên (Recommended)"*; 30/10/2026 (ký ĐO 34): *"Duyệt, sửa câu KTC (Recommended)"* — dùng hàm KTC sân đấu theo cách được khoá ở việc này (độ phủ ≥ 90%), cách tính được chọn trên mô phỏng sân đấu, không nhìn số Dow; và *"Giữ cả hai (Recommended)"* (Lát 4 in cấu hình KTC và phải KHỚP bản ghi, lệch là K0; không hạ ngưỡng 90%). Mô tả mô hình ở dòng "Mô phỏng" của mục 8.4 trên đây là MÔ HÌNH CŨ; mục này thay nó.

**1. Mô hình sinh CŨ sai, và đã đo vì sao (việc 1).** Giả thuyết ban đầu của leader (tự tương quan dài hơn khối) chính là điều mô hình cũ GIẢ ĐỊNH, chưa bao giờ được đo. Lệnh: `./.venv/Scripts/python.exe tools/san_dau.py kiem-mo-hinh --cache C:\Users\cuong\Vibe_Stock_Analysis\vibe_cache_goc_20260911 --hop-garch` (cache `acf6dca1…`, 71 mã, 1.217 phiên; chỉ thống kê MÔ TẢ trên giá đóng cửa; chuỗi "thật" là tài khoản vào lệnh NGẪU NHIÊN trừ e×rổ, KHÔNG dùng lệnh hay lãi nào của sổ thật). Kết quả (commit `0eb1524`):
- tự tương quan bậc 1 của x_t: tài khoản ngẫu nhiên 0,034–0,043 qua sáu cỡ (giữ 10–60 phiên, e trung bình 0,19–0,59); rổ đều 0,092; trung vị 69 mã 0,059; ngưỡng nhiễu 2/√n = 0,057. Các bậc 2 · 5 · 10 · 20 · 30 · 40 · 60 in ra: trong ±0,03. Hệ số phương sai (1 + 2·Σ(1−k/n)·ρ_k, 60 bậc) của x_t: 0,97–1,15.
- MÔ HÌNH CŨ (trung bình trượt 20 phiên của nhiễu t): bậc 1 = 0,87–0,94 và hệ số phương sai 8,5–16 (n = 252 và 1.000, ba dạng). Trung bình trượt của nhiễu mô tả lợi nhuận của một cửa sổ 20 phiên, KHÔNG phải đóng góp MỖI PHIÊN của một sổ vị thế: trọng số biết trước nên lợi nhuận mỗi phiên không tự tương quan, hai vị thế cùng mở không làm hai ngày liền nhau cùng dấu. Mọi độ phủ dưới 90% của BƯỚC 243 là hệ quả của giả định ấy; không dùng được để chọn cách tính.
- phần thật sự phụ thuộc là PHƯƠNG SAI THEO CỤM: ACF của |x_t| = 0,19–0,34 ở bậc 1, rơi tới ~0,04 ở bậc 20–30; độ nhọn thừa 2,4–5; rổ đều 4,0. Mô hình MỚI: nhiễu GARCH(1,1) đuôi t, `GARCH_ALPHA` = 0,14 · `GARCH_BETA` = 0,81 · `GARCH_NU` = 7,5 (hợp lý cực đại chung 30 tài khoản: 0,137 · 0,809 · 7,54 và 0,149 · 0,794 · 7,43 ở hai lượt; từng tài khoản 0,10–0,17 · 0,75–0,86 · 5,4–8,6), chuẩn hoá phương sai 1, KHÔNG tự tương quan ở mức. Giữ NGUYÊN ba giả định chưa đo được: thành phần chung giữa A và B `TY_TRONG_CHUNG` = 0,5 (hai tài khoản ngẫu nhiên độc lập cho 0,024; còn hai tài khoản chung vị thế thì không đo được ở đây), mặt nạ không giữ (vào giữ 0,10 mỗi phiên, đoạn giữ dài 15 phiên), hạt giống `[hat, n]`. Chúng được ghi là giả định ở nhãn của kết quả.
- chuỗi `tho` của mô hình mới khớp thật ở các đại lượng đã hợp (ACF |x| bậc 1/5/10/20: 0,15 · 0,12 · 0,09 · 0,045 so với thật 0,20 · 0,14 · 0,10 · 0,044; độ nhọn 2,9 so với 2,7). Các dạng có đoạn không giữ có độ nhọn lớn hơn thật (4,5–7,6): chiều KHẮT KHE hơn cho phép thử.
- Giới hạn khai thẳng: chuỗi "thật" là NULL (vào lệnh ngẫu nhiên). Một phương án có tín hiệu, hay Dow (đoạn giữ theo thủy triều, 71 mã), có thể có kỳ vọng có điều kiện đổi theo chế độ và vì thế tự tương quan lớn hơn; độ phủ trên chuỗi ĐÓ không được đo. Vì vậy cấu hình chốt còn được đo thêm dưới mô hình CĂNG THẲNG (tự hồi quy bậc 1 φ = 0,15, cao hơn mọi số đo được), để BÁO CÁO, không để chọn.

**2. Mô phỏng dùng để chọn (khai CỐ ĐỊNH).** Mô hình MỚI ở mục 1; n ∈ {40, 113, 252}; ba dạng `cap` · `mot_chuoi` · `tho` (như mục 8.4); **10.000** lần lặp mỗi ô (thay 2.000: một ô tốn khoảng 1 giây với 2.000 lần, nên 10.000 chỉ tốn thêm vài chục giây và hạ sai số Monte Carlo ở p = 0,9 từ 0,0067 xuống 0,0030); hạt giống mô phỏng 0 (đặt hạt `[0, n]`); KTC phân vị 2,5–97,5, 5.000 lần rút, hạt bootstrap 0; "phủ" = khoảng KHÉP chứa 0 (như `do_phu_mot_o`).

**3. Tiêu chí đạt (khai CỐ ĐỊNH).** Một ứng viên ĐẠT khi và chỉ khi **cả 9 ô** (3 dạng × 3 giá trị n) có độ phủ đo được ≥ 0,90 (so ước lượng điểm, ngưỡng của người dùng, KHÔNG hạ). Ứng viên không xác định ở một n (khối dài hơn n) thì ô đó KHÔNG đạt. Kiểm lại ở hạt 1 và 2 chỉ để BÁO CÁO: ô nào của cấu hình đã chốt dưới 0,90 ở hạt kiểm lại thì nêu thẳng trong báo cáo và hỏi, KHÔNG đổi cấu hình đã chốt.

**4. Danh sách ứng viên, THEO THỨ TỰ; ứng viên ĐẦU TIÊN đạt thì được CHỐT và KHÔNG thử ứng viên nào sau nó để chọn.** Chỉ khác nhau ở độ dài khối của bootstrap khối vòng CÓ CẶP (mọi thứ khác của `ktc_khoi_co_cap` giữ nguyên); thứ tự đi từ dài tới ngắn (dè dặt trước, vì không biết tự tương quan của chuỗi thật có lớn hơn số đo hay không):
1. `L` = 42 (leader; giả thuyết "tự tương quan dài hơn khối ~20 phiên").
2. `L` = 63 (leader; cùng giả thuyết).
3. `L` = 21 (cột nhạy cảm đã có ở mục 8.3).
4. `L` tự động theo Politis–White (2004) có hiệu chỉnh Patton–Politis–White (2009), dạng khối vòng. Lý do thêm: sau mục 1, tự tương quan thật gần 0 và có thể khác nhau giữa các chuỗi, nên một số cố định không thể đúng cho mọi chuỗi; đây là quy tắc chuẩn chọn khối từ CHÍNH chuỗi. Định nghĩa đầy đủ (chuỗi dùng là x, hay a−b ở dạng cặp, vì thống kê là trung bình của nó): n phần tử; ρ̂(k) tự tương quan mẫu; `K_N` = max(5, ⌈log10 n⌉); `m_max` = ⌈√n⌉ + `K_N`; m̂ = số nguyên m nhỏ nhất sao cho |ρ̂(m+j)| < 2·√(log10(n)/n) với mọi j = 1..`K_N` (không có thì m̂ = `m_max`); `M` = 2·max(m̂, 1); cửa sổ phẳng λ(s) = 1 khi |s| ≤ ½, 2(1−|s|) khi ½ < |s| ≤ 1, 0 khi |s| > 1; R̂(k) = tự hiệp phương sai mẫu chia n; ĝ = Σ_{k=−M..M} λ(k/M)·R̂(k); Ĝ = Σ_{k=−M..M} λ(k/M)·|k|·R̂(k); `b` = ((4/3)^(−1)·2·Ĝ²/ĝ²)^(1/3)·n^(1/3) = (1,5·(Ĝ/ĝ)²)^(1/3)·n^(1/3); ĝ ≤ 0 (hay chuỗi hằng) thì `L` = 1; ngược lại `L` = làm tròn của min(`b`, ⌈min(3√n, n/3)⌉), tối thiểu 1.
5. `L` = 10 (cách đang chạy, người dùng chốt 28/10/2026; mô hình mới có thể đã đủ cho nó).
6. `L` = ⌈n^(1/3)⌉ (quy tắc ngón tay cái cho khối, bị bác ở mục 8.3 vì "bỏ sót phụ thuộc", nay có số đo về phụ thuộc).
7. `L` = 5 (cột nhạy cảm đã có ở mục 8.3).
8. KHÔNG chạy: lấy mẫu lại theo lệnh / theo khoảng nắm giữ. Lý do: mô hình sinh ở mục 1 là chuỗi mỗi phiên, không có lệnh để lấy mẫu lại; dựng thêm một mô hình sinh cấp lệnh SAU KHI ứng viên 1–7 thất bại là chế điều kiện theo kết quả. Nếu 1–7 đều không đạt thì BƯỚC DỪNG, không đổi mặc định nào của `bang`, và hỏi người dùng (ĐO 34 (d)) — kể cả có nên dựng mô hình cấp lệnh hay không.

Ứng viên 1 và 2 được dự kiến THẤT BẠI theo cấu trúc ở n = 40 (khối dài hơn chuỗi); chúng vẫn được chạy để ghi lại bảng, vì đó là việc leader giao, không vì có hy vọng.

**5. Chốt.** Cấu hình đạt đầu tiên thành mặc định của `ktc_khoi_co_cap` và của nhãn trong `bang`; bản ghi (độ dài khối hay tên quy tắc, 5.000 lần rút, phân vị, hạt, bảng độ phủ 9 ô) nằm ở `docs/san-dau-do-phu.json` (khoá `cau_hinh_khoa`) và ở `docs/STATE.md`; một test đòi mặc định trong mã BẰNG bản ghi. Lát 4 của Dow in cấu hình KTC của nó và phải khớp bản ghi này.

**6. KẾT QUẢ (BƯỚC 248, 30/10/2026) — CHỐT: bootstrap khối vòng CÓ CẶP với độ dài khối theo quy tắc Politis–White (ứng viên 4).** Lệnh tái lập: `./.venv/Scripts/python.exe tools/san_dau.py do-phu --chon` (chạy ứng viên theo thứ tự, dừng ở ứng viên đầu tiên đạt, mô hình mới, 10.000 lần lặp mỗi ô, hạt 0; không ghi file) và `./.venv/Scripts/python.exe tools/san_dau.py do-phu --kiem` (đo lại toàn bộ và so với `docs/san-dau-do-phu.json`). Độ phủ đo được (%), danh nghĩa 95%, tiêu chí đạt ≥ 90 ở cả 9 ô:

| ứng viên | n | `cap` | `mot_chuoi` | `tho` |
|---|---|---|---|---|
| `L` = 42 | 40 | — | — | — |
| `L` = 42 | 113 | 81,36 | 81,37 | 81,18 |
| `L` = 42 | 252 | 88,06 | 88,96 | 88,93 |
| `L` = 63 | 40 | — | — | — |
| `L` = 63 | 113 | 74,13 | 74,21 | 74,37 |
| `L` = 63 | 252 | 84,76 | 85,85 | 85,29 |
| `L` = 21 | 40 | 76,99 | 77,99 | 73,53 |
| `L` = 21 | 113 | 88,17 | 87,55 | 88,36 |
| `L` = 21 | 252 | 91,37 | 91,96 | 92,17 |
| **PW — ĐẠT, CHỐT** | 40 | 91,22 | 91,96 | 91,71 |
| **PW — ĐẠT, CHỐT** | 113 | 93,20 | 92,79 | 93,48 |
| **PW — ĐẠT, CHỐT** | 252 | 94,29 | 94,48 | 94,42 |

Ứng viên 1 và 2 không xác định ở n = 40 (khối dài hơn chuỗi) như đã dự kiến, và cũng dưới 90% ở n = 113 (74–81%) và n = 252 (85–89%); ứng viên 3 hỏng ở n = 40 (73,5–78,0%) và n = 113 (87,5–88,4%). **Cấu hình khoá: `DO_DAI_KHOI` = "PW", 5.000 lần rút, phân vị 2,5–97,5, hạt bootstrap 0**, bản ghi ở khoá `cau_hinh_khoa` của `docs/san-dau-do-phu.json` (gác `tests/test_san_dau_cau_hinh_khoa.py`). Sai số Monte Carlo lớn nhất của một ô là 0,28 điểm phần trăm (`sai_so_monte_carlo_toi_da`); ô thấp nhất của cấu hình chốt là 91,22% (n = 40, `cap`).

Kiểm lại (CHỈ BÁO CÁO, không đổi cấu hình): hạt 1 nhỏ nhất 91,40%, hạt 2 nhỏ nhất 91,40% — cả hai lượt đủ 9 ô ≥ 90%. Mô hình CĂNG THẲNG (tự hồi quy bậc 1 φ = 0,15, cao hơn mọi số đo được): n = 40 cho 89,26 (`cap`) · 90,27 (`mot_chuoi`) · 89,26 (`tho`) — **hai ô dưới 90%**; n = 113 và 252: 91,22–93,10%. Hiểu đúng: nếu chuỗi thật có tự tương quan bậc 1 cỡ 0,15 thì ở n = 40 độ phủ thật là ~89%, gần ngưỡng chứ không xa. Nhãn "độ phủ đo được 91,x%" ở n = 40 vì thế nói về MÔ HÌNH SINH, như mục 8.4 vốn nói.

Thông tin sau khi chốt (KHÔNG dùng để chọn; chạy `do-phu --chon --ung-vien L10,L5`): `L` = 10 cho 85,89 · 87,19 · 84,35% ở n = 40 (hỏng), `L` = 5 cho 89,71 · 90,91 · 89,56% ở n = 40 (hai ô dưới 90%). Tức khối 10 phiên mà người dùng chốt 28/10 sẽ chưa đủ ngay cả dưới mô hình đúng.

### 8.5 Không làm ở C1

Không Reality Check / Romano-Wolf / White: ba phương án thăm dò không lên bản nên không có "chọn người thắng" cần sửa chọn lọc; thứ đó đi cùng lớp xác nhận ở C2/C3.

## 9. Sổ phương án `docs/phuong-an-bong.json`

Khuôn `docs/ung-vien.json` (`cham_bong.SO_UNG_VIEN`), nhưng là một FILE RIÊNG: ứng viên tầng 3 đếm vào K; phương án bóng thăm dò không.

```json
{
  "_ghi_chu": "...",
  "phuong_an": {
    "PB-001": {
      "lop": "tham_do",
      "bo_co": {"nghi_sau_lo_ngay": 7},
      "khai_ngay": "YYYY-MM-DD",
      "commit": null,
      "mo_ta": "...", "ly_do": "..."
    }
  }
}
```

| Trường | Nghĩa |
|---|---|
| id (khoá) | `PB-nnn`; tiền tố `UV-` bị cấm |
| `lop` | `"tham_do"` (duy nhất ở C1). `"xac_nhan"` bị máy từ chối cho tới C2 |
| `bo_co` | các cờ ghi đè, khoá phải là tên trường của `CauHinhVao` (kể cả `luat_vao`), kiểu giá trị đúng; chỉ những cờ mà C1 có nguồn tiêm (mục 5, khoản 4) |
| `khai_ngay` | `YYYY-MM-DD` giờ VN = ngày commit đầu tiên có dòng này |
| `commit` | `null` lúc khai; điền MỘT lần ở commit sau = mã băm đầy đủ của commit đầu tiên có dòng (diễn giải của đặc tả — mục 15, quyết định 4a, ĐÃ CHỐT) |

**Cách chứng "ngày khai"** (khuôn `cham_bong.vi_pham_tien_dang_ky` :465 và `tests/test_tien_dang_ky_git.py` :78): một file chỉ cho thấy trạng thái HIỆN TẠI, nên máy đọc LỊCH SỬ GIT, đi theo từng cạnh cha → con của HEAD (commit gộp có hai cha). Luật, phán trên mỗi cạnh:
- (a) dòng mới phải mang `commit: null`;
- (e) `khai_ngay` = ngày COMMITTER (`%cI`) giờ VN của commit đầu tiên có dòng — khai lùi ngày là nhận dữ liệu đã nhìn làm "chưa nhìn";
- (b) `lop`, `bo_co`, `mo_ta`, `ly_do`, `khai_ngay` không đổi ở mọi phiên bản sau;
- (c) `commit` chỉ đi `null` → mã băm, đúng một lần, và mã băm ấy phải bằng commit đầu tiên có dòng (kiểm bằng git);
- (d) không dòng nào bị xoá;
- (f) `lop` ∈ {`tham_do`}; id mang `PB-`; `bo_co` hợp lệ (mục trên).
Repo nông thì ĐỎ chứ không xanh im (CI đã `fetch-depth: 0`). Test mới `tests/test_phuong_an_bong_git.py` (BƯỚC 3) dựng các luật trên repo git tạm trong `tmp_path` và chạy thêm một lần trên repo thật; phần đi theo cạnh có thể rút chung với test cũ nếu test cũ giữ xanh KHÔNG sửa.

**Hệ quả của việc khai:** PB-001..003 đều đã được ĐO trên cache (ĐO 30, 32) hay đo thăm dò (ĐO 25) TRƯỚC ngày khai, nên chúng KHÔNG "chưa nhìn" ở dữ liệu cũ; sân đấu chỉ cho nhãn "chưa nhìn" với tín hiệu ≥ `khai_ngay`. Ngày khai của chúng là ngày commit sổ ở BƯỚC 3 — KHÔNG phải ngày của đặc tả này.

## 10. Ứng dụng và dòng lệnh

### 10.1 Tab "🏟️ Sân đấu" (BƯỚC 4)

Thêm vào `st.tabs([...])` (`app.py` :1769, cạnh tab "bóng" của tầng 3 — hai thứ khác nhau và tab mới KHÔNG đọc dữ liệu của tab kia).
- **CHỈ ĐỌC**: không nút ghi, không đẩy Sheets, không ghi file. Đầu vào: cùng lần đọc sổ lệnh của các tab khác + giá qua nút bấm kiểu "📥 Tải giá…" (`app.py` :670), phát lại trong bộ nhớ, giữ ở `session_state`. Nếu thiếu dữ liệu thì NÓI thiếu gì, không hiện số.
- **Biểu ngữ trên cùng, không tắt được:** *"THĂM DÒ — không bao giờ lên bản"*.
- **Mỗi hàng một tài khoản** — đường thật phát lại, PB-001, PB-002, PB-003, rổ. Cột: số lệnh (đóng / đang mở) · lãi/lỗ (điểm phần trăm vốn, cộng dồn) · alpha so rổ ± KTC (thước 1) · alpha từng lệnh (`vs_benchmark`) · sụt giảm tối đa của đường vốn · số phiên · "đã nhìn / chưa nhìn" · độ phủ cổng · nhãn độ phủ KTC (mục 8.4). Mỗi phương án thêm một hàng "so với đường thật" (thước 2).
- **Biểu đồ đường vốn** cho cả năm tài khoản.
- Nhãn "đã nhìn" và "chưa nhìn" ở HAI khối riêng, không cộng.

### 10.2 `tools/san_dau.py` (BƯỚC 2 trở đi)

Lệnh con: `bang` (in bảng), `tuong-duong` (Tầng B, mục 6), `do-phu` (BƯỚC 3, ghi `docs/san-dau-do-phu.json`). CHỈ ĐỌC với sổ và Sheets: kéo vào DB TẠM bằng đường của `tools/doc_so_that.py`, không `push`, không `pull` vào sổ nào khác, không ghi `*.db` ở gốc repo. Mọi file có `__main__` và `print` gọi `sys.stdout.reconfigure(encoding="utf-8")`.

## 11. Gác (AST, theo khuôn `tests/test_ke_hoach_vao_lenh.py` và `tests/test_doc_so_that.py`)

| Gác | Nội dung | Khuôn |
|---|---|---|
| G1 không ghi | `san_dau.py` và `tools/san_dau.py` không GỌI hàm nào trong tập ghi (`push`, `write_all`, `append_rows`, `ghi_ke_hoach`, `record_trade`, `update_trade`, `write_text`, `write_bytes`, `to_csv`, `to_json`, `dump`); mọi chỗ dựng `PaperTradingJournal` truyền ĐÚNG `":memory:"` hoặc một đường dưới `gettempdir()`; không `open` chế độ ghi | `tests/test_doc_so_that.py` :`test_DUNG_CU_khong_goi_mot_ham_GHI_nao` |
| G2 đường thật không nhập nó | chỉ `app.py`, `tools/san_dau.py` (và test) được nhập `san_dau`; `paper_trading`, `paper_runner`, `paper_metrics`, `run_daily`, `master_agent`, `analysis_agents`, `walkforward`, `sheets_store`, `cham_bong`, `hau_kiem_loi`, `ban_tin`, `backtest/` cấm | `tests/test_ke_hoach_vao_lenh.py` :1066 và :1081 |
| G3 module thuần | mức module chỉ nhập thư viện chuẩn + `pandas`/`numpy`; các nhập nặng (`paper_trading`, `analysis_agents`, `data_collectors`) nằm trong hàm; không đồng hồ, không mạng | `tests/test_ke_hoach_vao_lenh.py` :1089 |
| G4 không chấm lại điểm | `san_dau.py` không nhắc tên `_analyze`, `MasterConsensusAgent`, `run_full_analysis`, `run_session`; chỉ được dựng `RiskManagementAgent` cho phần rủi ro | quy ước 1 `cham_bong.py` :13 |
| G5 UV-001 không hiện | không hằng chuỗi `UV-`, `ung-vien`, không tên `SO_UNG_VIEN`, `doc_so_ung_vien`, `diem_ung_vien` trong `san_dau.py` / `tools/san_dau.py`; sổ phương án bị từ chối id `UV-` | `cham_bong.py` :28 |
| G6 nhãn | hàm in KTC là NƠI DUY NHẤT ghép chuỗi "95%" và luôn kèm độ phủ; biểu ngữ "THĂM DÒ — không bao giờ lên bản" có trong tab; tab không có `st.button` ghi | mục 8.4, 10.1 |
| G7 sổ phương án | luật (a)–(f) mục 9 | `tests/test_tien_dang_ky_git.py` |
| G8 cờ ↔ sổ | khoá của `bo_co` ⊆ trường `CauHinhVao`; mỗi trường chỉ-đọc ở `tu_module()` (mục 5, khoản 6) | `tests/test_hang_rao_quy_trinh.py` (khuôn sổ đăng ký) |

Mỗi gác mới đi qua vòng đột biến (Bước 3 của skill): thêm một lời gọi ghi → G1 đỏ; nhập `san_dau` từ `paper_trading` → G2 đỏ; gọi `_analyze` → G4 đỏ; in "95%" trần → G6 đỏ.

## 12. Bốn BƯỚC, mỗi BƯỚC một lát cắt dọc (`Mốc: C1`)

Số BƯỚC do leader cấp lúc giao việc. Mỗi BƯỚC qua năm cổng, đột biến mọi gác, PR riêng.

**Lát 1 — tiền tái cấu trúc (không thêm tính năng).** Mục 5: `CauHinhVao`, nguồn tiêm được, bước phiên chung, `luat_khop` (mặc định `None`, chưa dùng). *Xong khi:* toàn bộ test cũ xanh không sửa; test "vàng" mục 5 khoản 6 xanh; gác AST đọc cờ xanh và đỏ với đột biến; STATE ghi lệnh sinh bảng vàng. Chưa có `san_dau.py`.

**Lát 2 — bộ phát lại với cờ mặc định + phép thử tương đương.** `san_dau.py` (`phat_lai` với `CauHinhVao.tu_module()`, dựng lại phần rủi ro, nhãn dữ liệu), `tools/san_dau.py` lệnh `tuong-duong`, gác G1–G5 cho phần có mặt. *Xong khi:* Tầng A xanh trong CI; Tầng B chạy trên sổ thật và hoặc xanh (in số lệnh so được) hoặc dừng với lý do nêu số (mục 6, "Giới hạn"); số vị thế mang sang `NGAY_MO_CONG` đã đo và ghi; STATE ghi ngày bắt đầu hai tầng.

**Lát 3 — hai phương án cờ + rổ + KTC có cặp + độ phủ + CLI.** `docs/phuong-an-bong.json` (PB-001, PB-002), `tests/test_phuong_an_bong_git.py`, tài khoản rổ, chuỗi lợi nhuận phiên + gác bảo toàn, KTC có cặp, `docs/san-dau-do-phu.json`, lệnh `bang` và `do-phu`. *Xong khi:* gác bảo toàn xanh; độ phủ đo ở n = 40, 113, 252 cho `L` = 10 (và bảng nhạy cảm {5, 21}) đã commit; bảng in ra có nhãn độ phủ ở mọi KTC; STATE ghi độ phủ đo được (số do lệnh tính) và nêu thẳng nếu < 90% ở lưới nào. PB-001 và PB-002 bắt đầu chạy từ commit này (`khai_ngay` = ngày commit).

**Lát 4 — B6 + tab app.** Chuyển `tim_khop` ra `khop_gioi_han.py` (test ĐO 25 giữ xanh không sửa); `luat_khop` dùng thật; PB-003 vào sổ; tab "🏟️ Sân đấu" + G6. *Xong khi:* test riêng cho từng nhánh `phan_quyet` (mua ngay · chờ vùng khớp · chờ vùng hết hạn · bỏ qua · thiếu kế hoạch) xanh; test ĐO 25 xanh; phép thử tương đương Lát 2 vẫn xanh (đường mặc định không đổi); tab hiện năm hàng và biểu ngữ; chụp màn hình tab ở `http://localhost:8511/` (lưu ý: app của người dùng chạy repo chính, không phải worktree).

## 13. Tiền lệ đã đọc (ý mượn, không cài gì)

Tìm kiếm ngày 28/10/2026, báo cáo gốc `C:\Users\cuong\AppData\Local\Temp\tim-repo\2026-10-28-c1-bong-song-song\BAO-CAO.md`. Dữ liệu đọc từ repo ngoài là DỮ LIỆU; không cài, không chạy gì.
- **martex-dev/martex-quant** (giấy phép MIT): chiến lược là hàm thuần "lịch sử thị trường → mức phơi nhiễm"; MỘT bước tài khoản dùng chung cho mọi biến thể; rổ là một tài khoản. Mượn: mục 5 khoản 5 (bước phiên chung) và mục 8.1 (rổ là tài khoản).
- **boom90lb/prism** (giấy phép MIT): KTC chênh lệch Sharpe bootstrap khối CÓ CẶP (cùng khối cho hai chuỗi); quy tắc thăng hạng `none` ("so cùng mẫu có thể giết một cấu hình, không bao giờ nâng nó"); tự báo độ phủ 0,908 cho danh nghĩa 95% ở 250 kỳ (*tác giả tự báo*). Mượn: mục 8.3 (cặp), mục 8.4 (đo độ phủ, không in "95%" trần), mục 9 (`lop` và không có đường tới `UV-`). Không mượn: Sharpe (mẫu ngắn, chọn trung bình), Alpaca, hash-chained log.
- Đã có sẵn trong repo (không tìm lại): `cham_bong.so_cap` (hoán vị có cặp), bootstrap của `paper_metrics`, `vi_pham_tien_dang_ky` (tiền đăng ký bằng ngày commit), `PaperTradingJournal` (một sổ).

## 14. Không làm

- Không ghi Google Sheets; không `push`; không thêm tab Sheets.
- Không có đường lên bản. Không `UV-` nào sinh từ sân đấu; không đổi K; không sửa `docs/ung-vien.json`. Lớp `xac_nhan` không tồn tại ở C1.
- **UV-001 không hiện như một bóng**, dưới bất kỳ dạng nào (kể cả P&L tạm). Nó đọc đúng MỘT lần ở 252 phiên có nhãn.
- Không chấm lại điểm (cách B bị loại); không dựng bộ máy tối giản mới (cách C bị loại).
- Không đổi phí, trượt giá, bước giá, lô chẵn của bất kỳ tài khoản nào; không phương án bật IMOM / chốt sụt giảm (chưa có nguồn tiêm).
- Không Reality Check / Romano-Wolf (C2/C3).
- Không viết lại `docs/LO-TRINH.md` ở BƯỚC này (ghi chú "C kéo sớm" gộp vào lần sửa kế, theo người dùng). Không đổi file luật nào.
- Không dùng kết quả sân đấu để đổi ngưỡng, điểm hay đường thật (bất biến 7).

## 15. Câu hỏi mở — ĐÃ CHỐT 28/10/2026

Bản đầu của đặc tả (28/10/2026) để bảy câu mở, mỗi câu kèm khuyến nghị; hai trong số đó (1 và 2) mang nhãn *"đề xuất — người dùng chốt khi duyệt đặc tả"*. Người dùng đã trả lời cả bảy cùng ngày, theo lời leader chuyển. Bảng dưới giữ cả **đề xuất ban đầu** (để lịch sử còn thấy) và **quyết định**; từ đây chỉ quyết định có hiệu lực. Sửa một quyết định sau khi có dữ liệu thật là sửa đặc tả bằng một commit riêng, trước lượt đọc đầu tiên (bất biến 7).

| # | Đề xuất ban đầu (nhãn) | Quyết định — nguyên văn của người dùng, 28/10/2026 | Hiệu lực |
|---|---|---|---|
| 1 | Độ dài khối `L` = 10 phiên *(đề xuất — người dùng chốt khi duyệt đặc tả)*; thay thế 5, 21 hoặc `ceil(n^(1/3))` | *"10 phiên (Recommended)"* | `L` = 10, ghim trước dữ liệu thật (mục 8.3) |
| 2 | Thước 1: trừ rổ KHỚP MỨC ĐẦU TƯ (`r − e×rổ`) kèm cột thô (`r − rổ`) *(đề xuất — người dùng chốt khi duyệt đặc tả)* | *"Khớp mức giải ngân (Recommended)"* | thước 1 là thước chính; cột thô LUÔN in cạnh (mục 8.2) |
| 3 | Cửa sổ kế toán bắt đầu 28/09/2026 (ngày cổng mở lệnh mở), không phải 28/08 | *"28/09/2026, khi cổng mở (Recommended)"* | `NGAY_MO_CONG` = 2026-09-28 (mục 4, khoản 7) |
| 4a | Trường `commit` của sổ phương án = mã băm của commit đầu tiên có dòng, điền một lần ở commit sau | *"Duyệt cả bốn (Recommended)"* | mục 9 |
| 4b | PB-003 có cửa sổ riêng ngắn hơn (tab `ke_hoach` có từ 15/10/2026); so với đường thật và rổ chỉ trên cửa sổ chung của từng cặp | *"Duyệt cả bốn (Recommended)"* | mục 7 |
| 4c | PB-003 chỉ đổi LUẬT VÀO; cắt lỗ, cỡ vị thế, thoát là của bộ máy; `cat_lo` của kế hoạch để sau | *"Duyệt cả bốn (Recommended)"* | mục 7 |
| 4d | Tab app tính lại trong bộ nhớ khi bấm nút; `tools/san_dau.py` là bản chuẩn để tái lập; không file kết quả do app ghi | *"Duyệt cả bốn (Recommended)"* | mục 10.1 |

Ghi chú: các câu 4a–4d được hỏi chung một hộp (bốn điểm của phiên con), người dùng trả lời một lần cho cả bốn; bảng ghi cùng một câu trả lời ở bốn hàng vì thế.

Không còn câu mở nào. Việc tiếp theo là giao Lát 1 (mục 12).
