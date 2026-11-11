# Thiết kế C4 — Thị trường giả có lợi thế cài sẵn: chứng minh vòng học chạy đúng (T6)

**Mốc:** C4 (`docs/LO-TRINH.md`, giai đoạn C). **Duyệt hướng:** người dùng, 06/11/2026, trong phiên leader (BƯỚC 259): *"C4 — thị trường giả (T6) (Recommended)"* — mở bằng MỘT đặc tả chỉ có chữ; người dùng duyệt đặc tả trước khi có dòng mã nào.
**Trạng thái:** đặc tả **ĐÃ CHỐT ĐỦ BẢY CÂU**: người dùng trả lời Q1, Q2, Q3, Q7 ngày 06/11/2026 và Q4, Q5, Q6 ngày 07/11/2026 (mục 2, mục 14). Không còn câu mở. Mã bắt đầu từ BƯỚC 261 (Lát 1, mục 8); Lát 2–5 chưa có mã. Nhãn *[Qn: ĐÃ CHỐT]* trong văn bản trỏ về mục 2 và mục 14. Bản đầu của đặc tả (commit `2c4c5c6`) để cả bảy câu ở dạng bản thảo, và bản trước ngày 07/11/2026 gọi Q4 · Q5 · Q6 là *mặc định, người dùng chưa chọn*; cả hai còn ở lịch sử git.

Tài liệu này là đề bài cho các phiên làm mã. Luật chung (vá file, đột biến, năm cổng, giao PR) nằm ở skill `quy-trinh-lam-viec` — đi theo nó. Mọi `file:dòng` bên dưới được `grep` lại ở cây `3d87a20` ngày 06/11/2026; số dòng trôi theo mã, tên hàm thì không. Con số nào không kèm lệnh là **ước lượng** và được gọi là ước lượng (Quy tắc 2).

---

## 1. Mục đích và liên kết với T6

`docs/LO-TRINH.md` :235: *"C4 — Thị trường giả có lợi thế cài sẵn, để chứng minh cả vòng học chạy đúng."* Tiêu chí v1.0 T6 (:86): *"Vòng học đã chứng minh trên thị trường giả có lợi thế cài sẵn: nó tìm ra, xác nhận và nâng cấp đúng."*

Lý do tồn tại, nói thẳng: trên thị trường thật vòng xác nhận chỉ phán MỘT lần cho mỗi ứng viên (`cham_bong.py` quy ước 5) và UV-001 là ứng viên duy nhất trong sổ. Nếu lần phán duy nhất ấy ra "đang chậm", không ai biết là *không có lợi thế* hay *vòng không bắt nổi lợi thế*. Thị trường giả trả lời nửa sau: ta tự cài một lợi thế biết trước độ lớn và đếm xem vòng có bắt được nó không, và có im lặng khi không có gì. Nó **không** nói gì về thị trường thật (mục 11).

Điều C4 **không** là: không chạm sổ thật, không chạm UV-001, không đọc Sheets, không đổi điểm hay ngưỡng của đường thật, không phải agent soạn ứng viên (C3), không nối "nâng cấp" vào đường thật (mục 5.5, *[Q3: ĐÃ CHỐT]*).

## 2. Quyết định của người dùng

| Câu hỏi | Trả lời |
|---|---|
| Mở C4 như thế nào | *"C4 — thị trường giả (T6) (Recommended)"* (06/11/2026): bắt đầu bằng một BƯỚC đặc tả chỉ có chữ; người dùng duyệt trước khi viết mã |
| Q1 — "tìm ra" khi C3 chưa tồn tại | *"Bộ đề xuất cơ sở (Recommended)"* (06/11/2026): bộ đề xuất cơ sở trong C4 (mục 5.1); C3 sau này chạy lại cùng tiêu chí A |
| Q2 — độ trung thực | *"Hai tầng (Recommended)"* (06/11/2026): Tầng 1 quyết định trực tiếp + Tầng 2 qua đường ống thật (mục 4.1) |
| Q3 — "nâng cấp" đi tới đâu | *"Chỉ trong thị trường giả (Recommended)"* (06/11/2026): không nối vào `master_agent`, ngưỡng mua đứng yên (mục 5.4–5.5) |
| Q7 — số thế hệ | *"Một đời (Recommended)"* (06/11/2026): sau một nâng cấp thị trường dừng (mục 5.4 khoản 6) |
| Q4 — ứng viên đang chờ đọc khi có nâng cấp | *"Huỷ, K vẫn tính (Recommended)"* (07/11/2026): huỷ, đánh dấu `bi_huy_vi_nang_cap`, K vẫn đếm (mục 5.4 khoản 5) |
| Q5 — K khi bộ đề xuất quét 11 spec, khai 3 | *"K = số đã khai (Recommended)"* (07/11/2026): K là số ứng viên đã KHAI, không phải số đã quét (mục 5.3) |
| Q6 — mức đạt, ba mức lợi thế, số thị trường | *"Như bản nháp (Recommended)"* (07/11/2026): các ngưỡng và R của mục 6 đúng như bản nháp |

## 3. Bước 0 — bản đồ THẬT của "vòng học" (đọc từ mã, không từ trí nhớ)

Chữ "vòng học" xuất hiện ở `CLAUDE.md` (*"đổi điểm phải qua vòng xác nhận của tầng 3"*), `docs/STATE.md` :17595 (*"nhận thì agent **tự lên phiên bản** và **báo người dùng ngay**"*) và T6. Đi từng vế của T6 xuống mã:

| Vế | Có gì trong mã hôm nay | Địa chỉ | Kết luận |
|---|---|---|---|
| **Khai** một ứng viên | Sổ `docs/ung-vien.json`; khuôn chỉ nhận `loai: trong_so` — bộ trọng số trên đúng năm thành phần điểm đã ghi (`THANH_PHAN`); trần 1 ứng viên mỗi tháng dương lịch; K = số dòng đã khai; cổng tiền đăng ký đọc lịch sử git | `cham_bong.py` :79 :100 :101 :140 :249 :254 :290; `tests/test_tien_dang_ky_git.py` | **CÓ** |
| **Xác nhận** | `cham_bong.phan_quyet` :226 — đường DUY NHẤT tới phép so cặp; chỉ phán ở đúng `MOC_DOC` = 252 phiên CÓ NHÃN đầu tiên kể từ ngày khai, cần ≥ `MIN_MA` = 40 mã đủ dữ liệu; Δ = IC(ứng viên) − IC(điểm đã ghi), null hoán vị MÃ cùng một hoán vị cho hai điểm; p hai phía theo xấp xỉ chuẩn của null; `trang_thai` :259 trả `QUA` / `THUA` / `DANG CHAM` / `CHUA TOI MOC`. Nhãn là log lợi nhuận 21 phiên vượt rổ đều (`experiment_tran_dac_trung.nhan_vuot_ro` :179). Bên gọi: `cham_xac_nhan.cham` :348, `cham_mot` :320, chạy TAY bằng `tools/cham_xac_nhan.py` | `cham_bong.py` :83 :86 :91 :168 :226 :259; `cham_xac_nhan.py` :320 :348 | **CÓ** — chạy TAY có chủ ý, không workflow nào gọi (`app.py` :2487; `docs/LO-TRINH.md` danh sách chờ mục (3): *"ĐÓNG, không cần cron"*, vì module là phát lại thuần) |
| **Tìm ra** một ứng viên | Không có bộ đề xuất. Ứng viên do người viết bằng lập luận (`docs/ung-vien.json` UV-001 *"Bỏ risk_score…"*). Vòng sàng — thứ duy nhất từng cố tìm trên dữ liệu — đã **ngừng dùng** từ BƯỚC 155 sau khi ĐO 23 không đạt (`tools/sang_ung_vien.py` :1). C3 (agent tự soạn đề xuất, `docs/LO-TRINH.md` :234; T5 :85) mới là một dòng lộ trình, chưa có đặc tả | `docs/LO-TRINH.md` :85 :234 | **KHÔNG CÓ** |
| **Nâng cấp** | Không có. Không module nào đọc kết quả `QUA` để làm gì: nhãn *"Đạt — đủ điều kiện nâng cấp"* (`cham_bong.py` :405) chỉ là CHỮ trên app. Điểm đang chạy là bộ trọng số gõ cứng trong `master_agent.py` :189 :193 :195 (ba chế độ), cộng đè `momentum_norm = max(…, 65)` :190–191, rồi tranh luận, harness, và `int()` khi ghi (`paper_trading.py` :731). `git log -S"nang_cap" -- '*.py'` và `git log -S"phien_ban_diem" -- '*.py'` đều rỗng (06/11/2026) | `master_agent.py` :189–236 | **KHÔNG CÓ** |

Hai điều rút ra, nói thẳng vì T6 viết như thể cả bốn vế đã có:

**(1) Hai trên bốn vế của T6 chưa tồn tại.** "Tìm ra" và "nâng cấp" là việc phải THIẾT KẾ, không phải việc phải CHỨNG MINH. Một thị trường giả chỉ chứng minh được thứ đã có mã; với hai vế kia C4 phải tự dựng phiên bản tối thiểu của chúng **trong thế giới giả** (mục 5) và nói rõ chúng chưa phải đường thật.

**(2) Nâng cấp thật thiếu sáu mảnh**, ghi ra để người đọc không tưởng C4 làm xong là sản phẩm có tính năng ấy:
1. *Bộ đề xuất* — không có (C3).
2. *Sổ phiên bản điểm* — "bản đang chạy" là hằng số trong mã, không phải dữ liệu có ngày hiệu lực. Tab `decisions` KHÔNG có cột phiên bản (`paper_trading.py` :724 ghi `score`, `components`… không ghi bản nào) nên sau một lần đổi không thể quy dòng nào về bản nào.
3. *Bộ chấm đọc phiên bản* — `master_agent` không đọc file trọng số nào; ứng viên là tổ hợp TUYẾN TÍNH của năm thành phần, còn điểm đang chạy thì không (đổi chế độ, đè momentum, tranh luận). "Áp ứng viên" nghĩa là thay cả biểu thức cuối, bỏ chế độ trọng số động — một thay đổi lớn hơn chữ "đổi trọng số".
4. *Ngưỡng mua* — `BUY_THRESHOLD` = 62 (`paper_trading.py` :78) là một chỗ duy nhất, hiệu chuẩn cho phân phối điểm CŨ; điểm mới có phân phối khác nên cùng ngưỡng cho số lệnh khác. Vòng xác nhận đo IC, không đo số lệnh.
5. *Ứng viên đang chờ đọc* — mỗi ứng viên đọc sau 252 phiên, trần 1 khai mỗi tháng, nên ở trạng thái ổn định có chừng 12 ứng viên cùng chờ. Một lần nâng cấp giữa chừng làm chuỗi "điểm đã ghi" của mọi ứng viên còn lại đổi bản ở giữa cửa sổ: phép so cặp không còn là "ứng viên so với bản đang chạy lúc khai".
6. *Báo người dùng* — T3 (đường giao bản tin) chưa có; "báo ngay" chưa có kênh.

Mảnh 1 thuộc C3. Mảnh 2–4 và 6 là ĐỔI LUẬT đường thật (cần NotebookLM và người dùng duyệt riêng). Mảnh 5 là một lỗ hổng của VÒNG ngay cả khi mọi thứ khác xong — nó là câu mở 4.

**Nhãn khai thẳng (đọc `experiment_tran_dac_trung.py` :185–188, 06/11/2026).** Docstring nói "vào ở giá mở cửa T+1" nhưng mã tính `ln(close)` dịch `−h−1` trừ `ln(close)` dịch `−1` — tức đóng cửa T+1 tới đóng cửa T+22, vì bảng giá của `cham_xac_nhan._nhan` chỉ có cột `close`. Với thị trường giả điều này có nghĩa: lợi thế cài sẵn phải nằm trong lợi nhuận các phiên T+2 … T+22, không phải phiên T+1. Không sửa gì ở BƯỚC này; ghi để người sau khỏi trượt một phiên.

**Vòng "học" bằng lời không thuộc vòng này.** Hậu kiểm bằng lời (B1), sổ bài học (B3) chỉ ĐỌC lệnh đã đóng và không đổi điểm; bộ nhớ hậu nghiệm giữ 0 mẫu (`CLAUDE.md`, Q1). T6 chỉ nói về vòng khai → xác nhận → phiên bản.

## 4. Thị trường giả

### 4.1 Nguyên tắc

1. **Lợi thế biết trước, đo bằng nhãn.** Mọi lợi thế được cài ở mức *thông tin*: một nhân tố ẩn `z` quyết định phần kỳ vọng của lợi nhuận vượt rổ các phiên T+2…T+22, và chỉ một thành phần điểm ("thành phần mang") đọc được `z` (có nhiễu). Độ lớn lợi thế là **ΔIC_true** của một ứng viên cho trước, tính bằng CHÍNH hàm IC của `cham_bong` (`E.rho_hang`) trên một mẫu rất dài do cùng bộ sinh tạo ra (oracle, 4.5) — không phải một tham số tự khai.
2. **Cách ly tuyệt đối với thế giới thật.** Không đọc Sheets, không đọc `docs/ung-vien.json` hay `docs/phuong-an-bong.json` thật, không `PaperTradingJournal` nào ngoài `":memory:"`, không file nào ngoài thư mục dữ liệu tạm; sổ ứng viên giả là MỘT dict trong bộ nhớ (cùng khuôn, đi qua `cham_bong.kiem_so_ung_vien`). Ngày giả nằm ở dải 2100-01-04 trở đi: ngoài lịch công bố (`lich_giao_dich` chỉ phủ 2026) và cách xa mọi dòng thật, nên `cham_xac_nhan.kiem_lich` đếm là "ngoài lịch" chứ không kiểm sai, và một dòng giả lọt vào sổ thật sẽ lộ ngay. Đo 06/11/2026: OHLC nhất quán ở năm 2100 cho `validate_ohlcv` mức OK (script tạm; Lát 1 đưa nó thành test).
3. **Hai tầng**, vì một tầng không đủ:
   - **Tầng 1 — "quyết định trực tiếp".** Bộ sinh dựng thẳng các dòng đúng khuôn tab `decisions` (`symbol`, `signal_date`, `score` NGUYÊN như `paper_trading.py` :731, `components` là JSON năm thành phần, `at`, `seq`) và bảng giá `close`. Không chạy agent. Rẻ (ước lượng: dưới một giây một thị trường) nên chạy được hàng nghìn lần — cần cho các tỷ lệ. Nó kiểm VÒNG (khai → xác nhận → phiên bản), vốn chỉ nhìn thấy dòng quyết định và `close`.
   - **Tầng 2 — "qua đường ống thật".** Bộ sinh dựng khung OHLCV đầy đủ có nhân tố ẩn; chấm điểm bằng `paper_runner._analyze` THẬT (lịch sử cắt tới từng phiên, như walk-forward); phát lại bằng `san_dau.phat_lai` với `CauHinhVao` và nguồn tiêm (mục 4.9). Đắt (ước lượng ~5 phút một thị trường một lõi; mục 9) nên số lần ít. Nó kiểm rằng thứ Tầng 1 giả định — *agent thật truyền được lợi thế vào thành phần điểm, và ống dẫn không rò* — là đúng.
   *[Q2: ĐÃ CHỐT — hai tầng]*

### 4.2 Mô hình sinh (Tầng 1)

Các thông số dưới đây KHAI trước (mục 6); sửa là sửa đặc tả và đổi dòng hạt.

- **Mã và phiên.** 60 mã (≥ `MIN_MA` = 40, ít hơn 71 mã thật để bảng không tưởng là bản chép). Lịch: ngày làm việc thứ Hai–Sáu từ 2100-01-04, không ngày nghỉ. Độ dài và mốc: 4.6.
- **Lợi nhuận ngày.** `r = nhân tố thị trường + nhân tố ngành + riêng mã + kỳ vọng cài sẵn`. Nhân tố thị trường và sáu nhân tố ngành là bước ngẫu nhiên t; phần riêng mã là GARCH(1,1) đuôi t với ba hằng số ĐÃ ĐO trên giá thật ở BƯỚC 248 (`san_dau.GARCH_ALPHA` :1067, `GARCH_BETA` :1068, `GARCH_NU` :1069) — dùng lại, không đo lại. Sáu nhân tố ngành có mặt VÌ phép so cặp hoán vị MÃ (`cham_bong.so_cap`) giả định mã có thể hoán vị được; ngành làm hai mã cùng ngành không hoán đổi vô tội, và bộ sinh phải không làm hỏng phép kiểm null chỉ vì nó quá sạch. Lợi nhuận ngày kẹp ±7% (biên HOSE).
- **Nhân tố ẩn `z`.** Mỗi mã một chuỗi AR(1) chuẩn hoá, hệ số ngày φ_z. Kỳ vọng cài sẵn của lợi nhuận vượt rổ ở ngày s bằng `κ · z` ở ngày s − 2 chia cho 21: gộp 21 phiên T+2…T+22 cho nhãn có kỳ vọng ≈ `κ · trung bình(z)` quanh T, đúng cửa sổ của `nhan_vuot_ro` (mục 3, "Nhãn khai thẳng"). `κ` là NÚM LỢI THẾ (4.4); φ_z khai ở Lát 1.
- **Năm thành phần điểm.** Mỗi thành phần là hàm đơn điệu của (nhiễu riêng + hệ số · `z` nếu là thành phần mang), rời rạc hoá về số nấc ĐÃ ĐO của agent thật (`MO-XE-KIEN-TRUC.md` bảng Tầng 2: momentum 17, trend 10, sr 7, risk 8, volume 13; thang 0–100), và tương quan hạng giữa các thành phần khớp bảng ở cùng file (đo ở bản đầu của file, 564–573 phiên: trend–momentum ≈ 0,76; volume–trend/momentum ≈ 0,44–0,49; sr, risk gần độc lập) — bằng cách sinh từ một nhân tố chung nhiễu RIÊNG, không phải từ `z`. **Thành phần mang = `volume_score`** (một thành phần có trọng số vừa phải ở cả ba chế độ, nên ứng viên "tăng volume" có đất để hơn điểm đang chạy; chọn trước, không chọn theo kết quả).
- **Điểm đã ghi giả.** `score = int(tổ hợp tuyến tính của năm thành phần theo bộ trọng số mặc định 0,25 · 0,25 · 0,20 · 0,15 · 0,15 (master_agent.py :195) + nhiễu tranh luận nhỏ)`. Có `int()` vì bản thật làm vậy và nó tạo hoà hạng mà ứng viên dạng số thực không có — nếu bỏ, phép so cặp sạch hơn thật và mọi tỷ lệ phát hiện lạc quan (Quy tắc 1). Chế độ trọng số động và đè momentum KHÔNG mô phỏng ở Tầng 1: đó là phần Tầng 2 kiểm.

### 4.3 Họ ứng viên đối chứng và ba loại

Mọi ứng viên có dạng `trong_so` trên năm thành phần (`cham_bong.kiem_spec` :140). Với thành phần mang = `volume_score`, ba loại có ΔIC_true biết trước (tính bằng oracle, 4.5; ΔIC so với điểm đã ghi):

| Loại | Định nghĩa | ΔIC_true |
|---|---|---|
| **G** (tốt) | tăng trọng số `volume_score` (ví dụ mono-volume `{volume_score: 1,0}`), phần còn lại bỏ | dương, = k × MDE₈₀ ở lượt có lợi thế (4.4) |
| **Z** (không) | đổi chỗ trọng số của hai thành phần KHÔNG mang (trend ↔ momentum) | ≈ 0 (cả hai độc lập với `z`) |
| **H** (hại) | bỏ thành phần mang (mọi thành phần trừ volume, chuẩn hoá) | âm |

**Họ F = 11 spec** cho bộ đề xuất (mục 5.1): 5 mono (`{c: 1,0}` cho từng thành phần), 5 bỏ-một (bộ mặc định 0,25 · 0,25 · 0,20 · 0,15 · 0,15 bỏ thành phần c, chuẩn hoá về tổng 1 — chính dạng của UV-001), và 1 đều (0,2 mỗi thành phần). G, Z, H đều là phần tử của F hoặc tổ hợp xác định được từ F; Lát 1 chốt danh sách tường minh.

### 4.4 Độ lớn lợi thế so với MDE của bước xác nhận

- **MDE₈₀(K, W, M)** của C4 = ΔIC_true nhỏ nhất của ứng viên G mà tại đó `cham_bong.phan_quyet` (W = `MOC_DOC` = 252, M = 60 mã, ngưỡng `0,05 / K` hai phía, null 2000 hoán vị, hạt cố định) trả `QUA` ở ≥ 80% thị trường. Nó là kết quả ĐO của Lát 2, trên dòng hạt hiệu chuẩn, KHÔNG phải số gõ trong tài liệu này.
- **Các mức cài sẵn:** **0×** (thị trường NULL, 4.7), **0,5×**, **1×**, **2×** MDE₈₀. Mức 2× là mức chính (kỳ vọng bắt gần như chắc chắn nếu vòng đúng); 1× kiểm khớp hiệu chuẩn (kỳ vọng ≈ 80%); 0,5× mô tả (vòng *được phép* bỏ sót lợi thế dưới MDE — không phải lỗi, nhưng phải thấy đường cong).
- `κ` cho từng mức được tìm bằng dò nhị phân sao cho ΔIC_true(G) khớp mục tiêu ±10% (kiểm bằng oracle); bản ghi nằm ở `docs/thi-truong-gia-hieu-chuan.json` (Lát 2).
- **Chỉ để lấy hướng — không dùng làm MDE:** ĐO 21 (`docs/TIEU-CHI-DOC-TRUOC.md` :3474–3506, cache thật, tiêm vào IC TUYỆT ĐỐI chứ không vào ΔIC cặp) cho 252 phiên bắt một ứng viên đúng bằng rào hoà vốn (IC trung bình 0,057) 23/30 ở K = 1 và 13/30 ở K = 20. Số đó nói vòng này kén lợi thế; MDE₈₀ của thị trường giả sẽ không nhỏ.

### 4.5 Oracle — sự thật cài sẵn tách khỏi máy đo

Mỗi thị trường sinh mang theo bảng "sự thật": ΔIC_true của từng spec trong F so với điểm đã ghi, tính trên một mẫu dài gấp nhiều lần cửa sổ (ví dụ 5.000 phiên × 60 mã, CÙNG tham số, hạt riêng), bằng `E.rho_hang`. Oracle KHÔNG BAO GIỜ được gọi từ vòng học (gác AST, mục 7); nó chỉ dùng để (a) đặt `κ`, (b) chấm đúng/sai sau khi vòng đã quyết, (c) phép kiểm máy đo: ở NULL, |ΔIC_true| của mọi spec phải nhỏ hơn hai lần sai số Monte Carlo của chính nó.

### 4.6 Dòng thời gian của một thị trường

Phiên đánh số 0…T−1 (Tầng 2 thêm 250 phiên khởi động đứng trước cho agent; chúng không có dòng quyết định).
- **Cửa sổ đã nhìn** `S` = 126 phiên có quyết định: bộ đề xuất chỉ thấy phần này (126 là giá trị giữa của lưới W trong ĐO 21: 21 · 63 · 126 · 252).
- **Ngày khai:** phiên đầu tiên của tháng dương lịch kế tiếp ba lần liên tiếp (trần `TRAN_MOI_THANG` = 1 đọc theo THÁNG DƯƠNG LỊCH của `khai_ngay`, nên cách 21 phiên không đủ bảo đảm hai ngày khác tháng). Ứng viên thứ i đọc ở 252 phiên có nhãn đầu tiên kể từ ngày khai của nó (`cham_xac_nhan.BIEN_KHAI_NGAY` :58, biên `>=`).
- **Cửa sổ tiến-về-trước** `F` = 126 phiên sau lần đọc đầu tiên dẫn tới nâng cấp, để đo lợi ích sau nâng cấp (6, tiêu chí C2).
- Độ dài tổng ước chừng 570 phiên ở Tầng 1; Lát 1 chốt con số bằng cộng các đoạn trên, không gõ.

### 4.7 Thị trường NULL — đối chứng dương tính giả

Cùng bộ sinh, cùng mọi thông số, `κ = 0`. Mọi spec có ΔIC_true = 0. Vòng chạy y hệt. Đây là phần quan trọng ngang phần có lợi thế: một vòng "tìm ra" mọi thứ không có giá trị gì. NULL có hai việc: (a) đếm tỷ lệ báo động giả của bước xác nhận so với mức danh nghĩa; (b) lượng "chance" cho bộ đề xuất (mục 6 tiêu chí A).

### 4.8 Hạt

`numpy.random.default_rng([luong, chi_so])`, cùng kiểu `[hat, n]` của mục 8.4b khoản 2 đặc tả C1. Năm dòng, KHÔNG BAO GIỜ trộn:

| `luong` | Việc | Số thị trường (R) |
|---|---|---|
| 1 | hiệu chuẩn `κ` và MDE₈₀ | theo lưới của Lát 2 |
| 2 | lượt chính, có lợi thế (0,5× · 1× · 2×), Tầng 1 | 400 mỗi mức |
| 3 | lượt chính, NULL, Tầng 1 | 1.000 |
| 4 | Tầng 2 (NULL và 2×) | 100 mỗi loại |
| 5 | chẩn đoán SAU khi đã nhìn kết quả | tuỳ |

Sửa đặc tả sau khi đã nhìn một kết quả thì dòng hạt của bản sửa là 6, 7… (mục 6, "Quy tắc đọc"). Dòng 5 không bao giờ được dùng để chọn lại.

### 4.9 Cắm vào bộ máy thật (Tầng 2)

- **`CauHinhVao`** (`paper_trading.py` :513): tài khoản của thị trường giả dùng `CauHinhVao.tu_module()` làm cơ sở, ghi đè bằng `dataclasses.replace` như `san_dau.cau_hinh_tu_phuong_an` :232; không cờ module nào bị gán.
- **`NguonThiTruong`** (:567): `san_dau.NguonVni` :117 dựng từ chuỗi VN-INDEX GIẢ (chính nhân tố thị trường, cộng dồn) và `san_dau.NguonDoRong` :169 dựng từ `san_dau.co_tu_gia` :218 trên 60 khung giá giả — cả hai là nguồn TIÊM; `cong_vni_bat` mà thiếu nguồn thì `phat_lai` đã nổ sẵn (`san_dau.py` :467+). Nhờ vậy bộ máy không bao giờ đọc `backtest/cache` hay `market_filter.is_vni_bullish` trên giá giả.
- **Phát lại:** `san_dau.phat_lai` :467 nhận `quyet_dinh` (dòng sinh ở Tầng 2), `gia` (khung giả, giá "nghìn đồng" như nguồn thật để `price_multiplier` chạy đúng), `nguon`; mỗi tài khoản một sổ `":memory:"` (`san_dau.TaiKhoan`). Đi qua `paper_runner.buoc_phien` :286, cùng thứ tự bốn bước với đường thật.
- **Phép thử tương đương cho thế giới giả:** với MỘT thị trường Tầng 2, chạy `paper_runner.run_session` trực tiếp (chấm điểm bằng `_analyze` thật) và `san_dau.phat_lai` (điểm đã ghi) — bảng `trades` hai bên bằng nhau từng cột `san_dau.COT_TUONG_DUONG`. Cùng tinh thần Tầng A của mục 6 đặc tả C1.
- **Sổ thật không bị chạm** (gác G1, mục 7): `PaperTradingJournal` chỉ nhận `":memory:"`; `ghi_nhat_ky` luôn False; không nhập `sheets_store`.

## 5. Vòng học trong thế giới giả

Bốn bộ phận. **Bộ XÁC NHẬN dùng CHÍNH `cham_bong` và `cham_xac_nhan` (không bản sao)**; ba bộ phận còn lại là phần C4 phải dựng, và được gắn nhãn "chưa phải đường thật".

### 5.1 Tìm ra — bộ đề xuất cơ sở *[Q1: ĐÃ CHỐT]*

Hàm thuần `de_xuat(dong_quyet_dinh_da_nhin, gia_da_nhin) -> danh sách spec có thứ tự`. Cơ sở: với mỗi spec trong F (4.3), tính Δ = IC(spec) − IC(điểm đã ghi) trên MỌI phiên có nhãn của cửa sổ đã nhìn (126 phiên) bằng cùng `cham_bong.ma_tran_cap` + `E.rho_hang` (KHÔNG chạy `so_cap`: không có "phán" ở dữ liệu đã nhìn); xếp theo Δ giảm; khai **3 spec đầu**, mỗi spec một tháng (4.6), theo thứ hạng. Quy tắc cố định trước: ràng buộc hoà bằng thứ tự đặt tên spec; chỉ khai spec có Δ > 0 (nếu ít hơn 3 spec dương thì khai ít hơn — không ép đủ).
Đây KHÔNG phải C3: không lập luận, không bản tiền đăng ký bằng lời, không cổng khả thi. Nó là một đối thủ rẻ mà vòng phải thắng, và là CHỖ CẮM (giao thức một hàm) để C3 chạy lại cùng tiêu chí sau này.

### 5.2 Khai — sổ ứng viên giả

Dict cùng khuôn `docs/ung-vien.json`, mỗi lần khai đi qua `cham_bong.kiem_so_ung_vien` (nên trần 1/tháng và `qua_sang: null` tự áp). Sổ KHÔNG ghi ra đĩa. Cổng tiền đăng ký bằng git (`tests/test_tien_dang_ky_git.py`) không áp (không có git trong thế giới giả); thay bằng bất biến thời gian có test: bộ đề xuất chỉ thấy dữ liệu ≤ ngày khai − 1, mọi phán chỉ dùng dòng ≥ `tu_ngay_doc(khai_ngay)` (:266).

### 5.3 Xác nhận

`cham_xac_nhan.cham` :348 trên dòng quyết định giả và một bảng giá giả đã `phan_tich_bang_gia` (`nguon` ∈ {vci, kbs}, một `keo_luc` — nhãn giả nhưng đúng khuôn). K = số ứng viên đã khai trong sổ giả **tại lúc đọc** (đúng `cham_bong.nguong`) *[Q5: ĐÃ CHỐT, "K = số đã khai"; K = số đã KHAI, không phải số đã quét]*. Hạt hoán vị = `cham_xac_nhan.HAT_RNG` :63, 2000 hoán vị — mặc định thật, không đổi cho thế giới giả.

### 5.4 Nâng cấp — phiên bản điểm trong thế giới giả *[Q3, Q4 và Q7: ĐÃ CHỐT]*

Hàm thuần `nang_cap(so_phien_ban, ket_qua_xac_nhan, ma_ung_vien, phien_doc) -> so_phien_ban_moi`. Luật:
1. Chỉ `trang_thai == "QUA"` tạo phiên bản mới. `THUA`, `DANG CHAM`, `CHUA TOI MOC`, `CHUA DU DU LIEU` không.
2. Phiên bản mới có `spec` bằng **đúng** spec đã khai (so sánh bằng, không làm tròn), kèm bằng chứng (mã ứng viên, p, Δ, n_phien, K, hạt).
3. **Hiệu lực từ phiên SAU phiên đọc** (bất biến 1: điểm của phiên T chỉ dùng dữ liệu tới T; một phiên bản thông báo ở cuối T chưa chấm được T).
4. Sau nâng cấp, `score` ghi từ phiên hiệu lực = `int(diem_ung_vien(spec, components))` — phiên bản mới là tổ hợp tuyến tính của thành phần, đúng nghĩa ứng viên.
5. **Ứng viên đang chờ đọc khi có nâng cấp** *[Q4: ĐÃ CHỐT, "Huỷ, K vẫn tính"]*: HUỶ, đánh dấu `bi_huy_vi_nang_cap`, K vẫn đếm; muốn thử lại thì khai lại so với bản mới.
6. Một thế hệ trong C4 *[Q7: ĐÃ CHỐT, "Một đời"]*: sau một nâng cấp thị trường không có nâng cấp thứ hai.

### 5.5 Nâng cấp **không** nối vào đường thật *[Q3: ĐÃ CHỐT]*

`nang_cap` làm việc trên sổ phiên bản trong bộ nhớ. Không dòng nào của `master_agent`, `paper_trading`, `run_daily` nhập nó. Sáu mảnh thiếu ở mục 3 (2) là việc của một BƯỚC khác — đổi luật đường thật, cần NotebookLM và người dùng duyệt. C4 chứng minh VÒNG; việc đặt vòng lên đường thật là bước kế, và C4 để lại hợp đồng của nó (đầu vào/đầu ra của `nang_cap`, bất biến 1–6 ở trên) làm đặc tả cho bước ấy.

## 6. Tiêu chí đạt/trượt — KHAI TRƯỚC khi chạy bất kỳ thị trường nào

> **Các ngưỡng và số thị trường (R) dưới đây là QUYẾT ĐỊNH của người dùng (Q6, 07/11/2026: *"Như bản nháp (Recommended)"*).** Phần đã chốt trước (Q1, Q2, Q3, Q7) quyết định *loại* tiêu chí nào có mặt; Q6 chốt các con số. Sửa bảng này sau khi đã chạy một thị trường nào là sửa đặc tả bằng commit riêng và chạy lại trên dòng hạt mới (mục 4.8).

Mọi con số dưới đây được chọn từ phép tính nhị thức KHÔNG phụ thuộc kết quả mô phỏng. Lệnh tái lập (06/11/2026):

```bash
./.venv/Scripts/python.exe -c "from scipy.stats import binom as b; print(1-b.cdf(75,1000,.05), b.cdf(75,1000,.10), 1-b.cdf(359,400,.95), 1-b.cdf(359,400,.90), 1-b.cdf(359,400,.85), 1-b.cdf(319,400,.85), 1-b.cdf(319,400,.75), b.ppf(.999,1000,3/11))"
```

(cho 0,0003 · 0,0038 · 1,0 · 0,542 · 0,0021 · 0,9972 · 0,0108 · 317.)

**Định nghĩa.** *Báo động* = một ứng viên có `p < 0,05 / K` (QUA hoặc THUA). *Tìm ra* = spec đứng đầu họ F theo oracle nằm trong 3 spec bộ đề xuất đã khai. Mỗi thị trường chạy HAI thủ tục trên CÙNG dữ liệu: (i) **bộ ba** G · Z · H khai tay ở ba tháng liên tiếp, K = 3 (đo nhóm B); (ii) **chuỗi** bộ đề xuất → xác nhận → nâng cấp (đo nhóm A, C).

| # | Tiêu chí | Thị trường | R | Ngưỡng ĐẠT | Vì sao ngưỡng ấy (nhị thức) |
|---|---|---|---|---|---|
| **A** | **Tìm ra** — spec tốt nhất theo oracle nằm trong ba spec được khai | 2× | 400 | ≥ 320 (80%) | nếu tỷ lệ thật 85% → qua 99,7%; nếu 75% → qua 1,1% |
| **A0** | đối chứng *chance*: spec G được bộ đề xuất khai ở NULL không quá mức ngẫu nhiên | NULL | 1.000 | ≤ 317 (31,7%) | ngẫu nhiên là 3/11 = 27,3%; 317 là phân vị 99,9% của nhị thức; quá ngưỡng → lỗi bộ sinh hoặc bộ đề xuất rò, không phải "tìm ra" |
| **B1** | **Im khi không có gì** — thị trường có ≥ 1 báo động ở bộ ba | NULL | 1.000 | ≤ 75 (7,5%) | danh nghĩa 5%: nếu đúng 5% → sai-trượt 0,03%; nếu thật 10% → qua 0,4% |
| **B2** | **Bắt cái có** — ứng viên G của bộ ba bị `QUA` | 2× | 400 | ≥ 360 (90%) | nếu thật 95% → qua ≈ 100%; 90% → 54%; 85% → 0,2% |
| **B3** | **Chọn lọc** — ứng viên Z (ΔIC_true = 0) bị báo động | 2× | 400 | ≤ 20 (5%) | mức danh nghĩa mỗi ứng viên 1,67%; 20/400 là 3 lần mức ấy |
| **B4** | **Không khen cái hại** — ứng viên H của bộ ba bị `QUA` | 0,5× · 1× · 2× | tất cả | **0** | bất biến, không phải tỷ lệ: H có ΔIC_true < 0 nên `QUA` (Δ > 0) chỉ xảy ra nếu dấu bị đảo hoặc nhãn rò; ở NULL một `QUA` của H là báo động giả, đã tính ở B1 |
| **C1** | **Nâng cấp đúng luật** — mọi bất biến 5.4 khoản 1–4 | mọi thị trường, cả hai tầng | tất cả | **0 vi phạm** | tất định; một vi phạm là lỗi mã |
| **C2** | **Nâng cấp có ích** — ΔIC thực hiện của phiên bản mới so với bản cũ trên `F` = 126 phiên tiến-về-trước, trung bình qua các thị trường có nâng cấp | 2× | mọi thị trường có nâng cấp | cận dưới KTC 95% (bootstrap qua thị trường, 5000 lần, hạt 0) > 0 | lợi thế thật dương → phải thấy dương |
| **C3** | **Không nâng cấp ma** — thị trường có ≥ 1 `QUA` | NULL | 1.000 | ≤ 50 (5%) | danh nghĩa một phía ≈ 2,5%; nếu đúng → sai-trượt ≈ 0; nếu thật 5% → qua 54% |
| **P** | **Tầng 2: ống dẫn** — (P1) dòng quyết định do `_analyze` thật sinh đúng khuôn và `data_quality` = OK; (P2) phép thử tương đương của 4.9 bằng nhau từng cột; (P3) IC của thành phần mang với nhãn > 0 (lợi thế *đã đi qua* agent thật); (P4) gác G1–G5 xanh | NULL và 2× | 100 mỗi loại | P1, P2, P4: 0 vi phạm. P3: thấy ở ≥ 90/100 thị trường 2× | P1, P2, P4 tất định; P3 là tỷ lệ, 90% chọn thấp hơn B2 vì chuỗi qua agent thật nhiễu hơn (ước lượng, chưa đo) |
| **PT** | **Tầng 2: nhất quán tỷ lệ** — báo động ở NULL ≤ 12/100; G `QUA` ở 2× ≥ 85/100 | NULL, 2× | 100 | như vế trái | chỉ là kiểm khớp Tầng 1, KHÔNG phải chứng cứ riêng (R = 100: nếu thật 5% → sai-trượt 0,15%; nếu thật 10% vẫn qua 80% — lực yếu, khai thẳng) |

**Báo cáo, không phán:** đường cong 0,5× · 1× (tỷ lệ bắt G, tìm ra, nâng cấp); với 1×, tỷ lệ bắt G phải nằm trong dải 99% quanh 80% = [299 ; 340]/400 (khớp hiệu chuẩn; ra ngoài thì máy đo hiệu chuẩn có vấn đề → kết cục "không đọc được"); mức độ bảo thủ của B1 (nếu < 2,5% thì nói vòng thiếu nhạy); ΔIC thực hiện sau nâng cấp ở NULL.

**Kết cục (khai trước, cùng kiểu các ĐO khác):**
- **ĐẠT** — mọi tiêu chí trên đạt. T6 được ghi *ĐÃ chứng minh*, kèm giới hạn mục 11.
- **TRƯỢT ở tiêu chí X** — vòng có lỗi hoặc thiếu lực ở đúng bộ phận X (A: bộ đề xuất; B: xác nhận; C: nâng cấp; P: ống dẫn). Ghi nguyên văn. KHÔNG hạ ngưỡng, KHÔNG đổi bộ sinh cho đẹp; sửa bộ phận sai rồi chạy lại trên **dòng hạt mới** (bất biến 7).
- **KHÔNG ĐỌC ĐƯỢC** — máy đo hỏng: oracle ở NULL ngoài hai lần sai số Monte Carlo; ΔIC_true của G ngoài ±10% mục tiêu; tái lập hạt không bằng bit; bộ sinh không qua `validate_ohlcv` mức OK. Sửa máy, chạy lại cả bảng.

Số thị trường (R) và dòng hạt được CỐ ĐỊNH ở đây vì lý do kép: đủ để tách nhị thức nêu trên, và chạy được (mục 9). R KHÔNG được tăng sau khi nhìn kết quả "trượt sát ngưỡng" (đó là cách chọn cực đại, bất biến 7).

## 7. Gác (AST, khuôn `tests/test_san_dau.py` và `tests/test_doc_so_that.py`)

| Gác | Nội dung |
|---|---|
| G1 không ghi | các module thị trường giả và dụng cụ không GỌI hàm ghi (`push`, `write_all`, `append_rows`, `ghi_ke_hoach`, `record_trade`, `write_text`, `to_csv`, `dump`…) trừ `va_an_toan.ghi` ở dụng cụ khi ghi bảng hiệu chuẩn/kết quả của chính nó; mọi `PaperTradingJournal` truyền đúng `":memory:"`; không `open` chế độ ghi ngoài thư mục tạm |
| G2 đường thật không nhập nó | `paper_trading`, `paper_runner`, `paper_metrics`, `run_daily`, `master_agent`, `analysis_agents`, `walkforward`, `sheets_store`, `cham_bong`, `cham_xac_nhan`, `hau_kiem_loi`, `ban_tin`, `san_dau` cấm nhập module thị trường giả (chiều ngược lại — nó nhập `cham_bong`, `san_dau` — là chủ ý) |
| G3 không thấy thế giới thật | không hằng chuỗi `ung-vien`, `phuong-an-bong`, `UV-`, không tên `SO_UNG_VIEN`, `doc_so_ung_vien`, không nhập `sheets_store`, `keo_bang_gia`, `doc_so_that`; không đọc `backtest/cache*` |
| G4 oracle cách ly | tên oracle không xuất hiện trong module vòng học (`de_xuat`, `nang_cap`, hàm chạy vòng); oracle chỉ do bộ sinh và dụng cụ chấm gọi |
| G5 ngày giả | mọi ngày bộ sinh tạo ≥ 2100-01-04; `lich_giao_dich.co_phien` trả `None` cho chúng |
| G6 không chấm lại | bước xác nhận đi qua `cham_bong.phan_quyet` (không gọi `so_cap` trực tiếp); bản sao thuật toán IC/hoán vị trong module mới bị cấm |
| G7 bất biến thời gian | bộ đề xuất chỉ nhận dữ liệu ≤ ngày khai − 1 (test dựng dữ liệu có "mồi" sau ngày khai: kết quả không được đổi); nâng cấp hiệu lực từ phiên sau phiên đọc |

Mỗi gác đi qua vòng đột biến (Bước 3 của skill): thêm một lời gọi ghi → G1 đỏ; nhập module giả từ `master_agent` → G2 đỏ; đọc `docs/ung-vien.json` → G3 đỏ; gọi oracle từ `de_xuat` → G4 đỏ; đổi năm 2100 thành 2026 → G5 đỏ.

## 8. Năm lát cắt dọc (`Mốc: C4`)

Số BƯỚC do leader cấp. Mỗi BƯỚC qua năm cổng, đột biến mọi gác, PR riêng. Lát 5 chạm file luật nên phải hỏi sổ tay thật.

**Lát 1 — bộ sinh Tầng 1 + NULL + oracle.** Module thuần ở gốc repo (tên chốt khi viết mã) sinh `ThiTruongGia`: dòng quyết định đúng khuôn `decisions`, bảng giá `close`, sổ sự thật. *Xong khi:* tái lập bit theo hạt; số nấc/tương quan thành phần khớp bảng MO-XE trong dung sai khai ở test; `int()` hoà hạng có mặt; ΔIC_true của spec Z ≈ 0 và của B < 0 ở mức có lợi thế; NULL: mọi |ΔIC_true| < 2 sai số Monte Carlo; G1, G3, G5. Chưa có bước xác nhận, chưa có vòng.

**Lát 2 — hiệu chuẩn MDE₈₀ và đường cong lực.** Dụng cụ ở `tools/` (`hieu-chuan`) chạy `cham_xac_nhan.cham` trên thị trường giả, dò `κ`, đo MDE₈₀(K = 3, W = 252, M = 60). *Xong khi:* `docs/thi-truong-gia-hieu-chuan.json` được commit (dòng hạt 1), bao gồm bảng "ΔIC_true → tỷ lệ bắt"; chạy lại ra đúng bảng (`--kiem`); độ lệch ±10% ở bốn mức; NULL smoke: không báo động quá ngưỡng B1 ở lượt nhỏ (chỉ là kiểm máy, không phải kết quả T6).

**Lát 3 — vòng học khép kín trên Tầng 1.** `de_xuat`, sổ giả, xác nhận qua `cham_xac_nhan.cham`, `nang_cap`, kiểm tiến-về-trước, dụng cụ `chay-vong` in từng bước của MỘT thị trường. *Xong khi:* mỗi bất biến 5.4 có test dựng ca (QUA → nâng; THUA → không; DANG CHAM → không; ứng viên đang chờ → huỷ; hiệu lực từ phiên sau); G2, G4, G6, G7; một thị trường mẫu chạy từ đầu tới cuối có biên bản thấy được. Chưa có tỷ lệ nào.

**Lát 4 — Tầng 2: qua đường ống thật.** Bộ sinh OHLCV có `z` (khối lượng mang lợi thế), chấm bằng `paper_runner._analyze`, phát lại bằng `san_dau.phat_lai` với `CauHinhVao` và `NguonVni`/`NguonDoRong`. *Xong khi:* P1, P2, P4 xanh trên ít nhất một thị trường; P3 đo ở một lượt thử nhỏ; chi phí một thị trường ĐO bằng lệnh và ghi vào STATE (thay con số ước lượng ở mục 9).

**Lát 5 — khai tiêu chí + lượt chạy chính thức.** (a) Chép bảng mục 6 vào `docs/TIEU-CHI-DOC-TRUOC.md` thành một ĐO mới, ở **commit riêng đẩy TRƯỚC khi lượt chạy tồn tại** — chạm file luật nên BƯỚC này hỏi sổ tay thật. (b) Chạy dòng hạt 2, 3, 4 một lần; ghi `docs/thi-truong-gia-ket-qua.json`; đọc kết cục theo bảng đã ký. (c) STATE và `docs/LO-TRINH.md`: T6 ghi ĐÃ/CHƯA chứng minh theo kết cục, không viết lại tiêu chí. *Xong khi:* kết cục ghi nguyên văn, kể cả TRƯỢT.

## 9. Chi phí — ƯỚC LƯỢNG, chưa có lệnh trong repo

- Một lần `paper_runner._analyze` trên lịch sử giả 300–330 phiên: 7,5–8,3 ms (hai lượt chạy tạm 06/11/2026, 30 lần mỗi lượt, một lõi; máy 16 lõi). Đây là số đo của một script tạm không nằm trong repo — Lát 4 thay bằng lệnh có trong repo.
- Tầng 2, một thị trường: ~ 60 mã × ~570 phiên có quyết định ≈ 34.000 lần chấm ≈ 4–5 phút một lõi. 100 thị trường NULL + 100 thị trường 2× trên 16 lõi ≈ 1–1,5 giờ (ước lượng). Tầng 1: ước lượng dưới một giây một thị trường, nên R = 1.000 + 3 × 400 chạy trong vài chục phút.

## 10. Tiền lệ trong repo (dùng lại, không dựng lại)

- Phép tiêm tín hiệu biết trước và null hoán vị MÃ: ĐO 15/16/21 (`tools/do21_luc_vong_xac_nhan.py`). C4 là phiên bản *đầy đủ vòng* của phép tiêm ấy.
- Hằng số GARCH-t đã đo trên giá thật: `san_dau.py` :1067–1069 (BƯỚC 248).
- Phát lại qua `buoc_phien` và phép thử tương đương: `docs/thiet-ke-c1-san-dau.md` mục 5–6.
- Khuôn đặc tả có KHAI TRƯỚC, kết cục A/B/C ký sẵn, hạt `[hat, n]`: `docs/thiet-ke-c1-san-dau.md` mục 8.4b.

## 11. Điều T6 KHÔNG chứng minh

- **Không nói thị trường thật có lợi thế.** Đích 2 vẫn do UV-001 và C5 quyết.
- **Không nói vòng bắt được mọi loại lợi thế.** Khuôn ứng viên chỉ là `trong_so` trên năm thành phần giá (`cham_bong.LOAI_SPEC`); lợi thế nằm ngoài tập ấy (khối ngoại, ngành, sự kiện) vòng này không bao giờ thấy, giả hay thật.
- **Không đo lợi nhuận.** Bước xác nhận đo IC; một ứng viên IC cao hơn có thể cho alpha từng lệnh thấp hơn sau chi phí. Tầng 2 in alpha trước/sau nâng cấp để tham khảo, KHÔNG thành tiêu chí.
- **Không chứng minh đường thật nâng cấp được** (mục 5.5, sáu mảnh thiếu).
- Mô hình sinh là *một* họ. Nó khớp thật ở các đại lượng đã chọn (số nấc, tương quan thành phần, GARCH-t) và khác ở mọi thứ chưa đo; một vòng đạt T6 trên đó vẫn có thể hỏng ở một cấu trúc chưa nghĩ tới. Đó là lý do tiêu chí A0 và B1 đo cả chiều không có gì.

## 12. Không làm

- Không ghi Sheets, không chạm `*.db`, `docs/ung-vien.json`, `docs/phuong-an-bong.json`; không `UV-` giả trong sổ thật.
- Không đưa `nang_cap` vào đường thật; không đổi điểm, ngưỡng, cổng, khớp lệnh.
- Không dựng C3 (agent soạn ứng viên). Không Reality Check / Romano-Wolf.
- Không tab app cho C4 (kết quả sống ở STATE và `docs/thi-truong-gia-ket-qua.json`).
- Không viết lại `docs/LO-TRINH.md` quá chỗ hàng C4/T6 và dòng C1 đã cũ (BƯỚC 259).

## 13. Quy tắc ghi chép khi làm mã

Mọi lệch giữa đặc tả này và mã thật được ghi thành mục "Ghi chú thi công" ở cuối file này (khuôn mục 16 của đặc tả C1), TRƯỚC khi có số nào của lượt chạy chính.

## 14. Câu hỏi mở

### 14.1 Đã chốt 06/11/2026

| Câu | Quyết định (nguyên văn nhãn người dùng chọn) | Hiệu lực |
|---|---|---|
| Q1 | *"Bộ đề xuất cơ sở (Recommended)"* | mục 5.1; tiêu chí A, A0; C3 chạy lại sau |
| Q2 | *"Hai tầng (Recommended)"* | mục 4.1; tiêu chí P, PT |
| Q3 | *"Chỉ trong thị trường giả (Recommended)"* | mục 5.4–5.5; không nối `master_agent`; ngưỡng mua đứng yên |
| Q7 | *"Một đời (Recommended)"* | mục 5.4 khoản 6 |

### 14.2 Đã chốt 07/11/2026

| Câu | Quyết định (nguyên văn nhãn người dùng chọn) | Hiệu lực |
|---|---|---|
| Q4 | *"Huỷ, K vẫn tính (Recommended)"* | mục 5.4 khoản 5: ứng viên đang chờ đọc bị huỷ khi có nâng cấp, đánh dấu `bi_huy_vi_nang_cap`, K vẫn đếm |
| Q5 | *"K = số đã khai (Recommended)"* | mục 5.3: K = số đã KHAI, đúng `cham_bong.so_da_sang`; 11 spec chỉ được quét ở dữ liệu đã nhìn |
| Q6 | *"Như bản nháp (Recommended)"* | mục 6: các ngưỡng và R như bản nháp (NULL ≤ 7,5% ở R = 1.000; 2× bắt G ≥ 90% và tìm ra ≥ 80% ở R = 400) |

### 14.3 Câu mở còn lại

Không có. Đổi một quyết định ở 14.1 hay 14.2 sau Lát 1 là sửa đặc tả bằng commit riêng và phải chạy lại trên dòng hạt mới (mục 6).

### 14.4 Các lựa chọn Q4 · Q5 · Q6 đã được đưa ra (giữ làm lịch sử)

Người dùng chọn phương án (a) ở cả ba câu. Hai phương án còn lại giữ lại để người sau hiểu cái gì đã bị bỏ.

**Q4 — Ứng viên đang chờ đọc khi một ứng viên khác được nâng cấp?** (Hệ quả của việc mỗi ứng viên đọc sau 252 phiên, trần 1 khai mỗi tháng: lúc nâng cấp luôn còn ứng viên chờ.)
- (a) **Huỷ, đánh dấu, K vẫn đếm; muốn thử lại thì khai lại so với bản mới.** **(người dùng chọn 07/11/2026)** Sạch nhất: không ứng viên nào bị đọc trên chuỗi đổi bản giữa chừng.
- (b) Cho đọc tiếp, so với bản hiệu lực từng phiên, gắn nhãn *"đọc qua đổi phiên bản"* — giữ ứng viên nhưng phép so cặp không còn đúng nghĩa.
- (c) Đọc theo LÔ: ứng viên khai trong cùng đợt đọc cùng ngày, nâng tối đa một người thắng mỗi đợt — đổi cả quy ước "mỗi ứng viên đọc sau 252 phiên của riêng nó" (đụng `cham_bong.py` quy ước 5).

**Q5 — K tính theo gì khi bộ đề xuất quét 11 spec nhưng chỉ khai 3?**
- (a) **K = số đã KHAI (đúng luật hiện hành `cham_bong.so_da_sang`)**; 11 spec được quét ở dữ liệu đã nhìn, phán ở dữ liệu chưa nhìn. **(người dùng chọn 07/11/2026)**
- (b) K = số đã QUÉT (11) — chặt hơn, theo tinh thần quy ước 4 ("sàng là chỗ đã nhìn nhiều lần"); lực của vòng giảm rõ (ngưỡng 0,05/11).
- (c) Chạy cả hai và báo cáo, nhưng tiêu chí chính theo (a).

**Q6 — Mức đạt, ba mức lợi thế và số thị trường (mục 6).** Bản nháp: NULL ≤ 7,5% báo động ở R = 1.000; 2× MDE₈₀: G bị bắt ≥ 90% và spec đúng được tìm ra ≥ 80% ở R = 400; ba mức 0,5× · 1× · 2× (MDE₈₀ là số ĐO ở Lát 2, không phải số khai).
- (a) **Như mục 6.** **(người dùng chọn 07/11/2026)**
- (b) Chặt hơn: NULL ≤ 6,5%, 2× ≥ 95%, R_NULL = 2.000 (lực phân biệt tốt hơn, chạy lâu gấp đôi).
- (c) Nới: NULL ≤ 10%, 2× ≥ 80% — dễ đạt, nhưng 10% đã gấp đôi mức danh nghĩa.

## 15. Ghi chú thi công Lát 1 (BƯỚC 261, 10/11/2026) — chỗ mã khác đặc tả, và vì sao

Ghi sau khi viết mã, TRƯỚC khi có số nào của một lượt chạy chính (mục 13). Module `thi_truong_gia.py` (gốc repo), test `tests/test_thi_truong_gia.py`. Mỗi điểm là một chỗ mà mục 4 hay mục 8 nói khác thứ làm được, hoặc một hằng số mà mục 4.2 để "khai ở Lát 1":

1. **"B < 0" của mục 8 Lát 1 đọc là H.** Mục 4.3 đã đổi tên ứng viên hại từ B thành H (trùng chữ B của điểm đã ghi); câu ở mục 8 còn chữ cũ. Test: ΔIC_true của H (`bo_volume_score`) < 0 ở mức có lợi thế.
2. **Z là đổi chỗ trend ↔ sr, KHÔNG phải trend ↔ momentum.** Mục 4.3 nêu trend ↔ momentum, nhưng cả hai cùng trọng số 0,25 (`master_agent.py` nhánh `else`) nên đổi chỗ cho ĐÚNG bộ trọng số mặc định: Δ chỉ còn do `int()`, một đối chứng suy biến (hai điểm gần như trùng; ước đoán, CHƯA đo: null của phép so cặp hẹp nên một lệch hệ thống nhỏ do `int()` có thể thành p nhỏ). trend và sr có độ phân tán gần nhau (nấc 0–100 và 6,2–100) nên đổi chỗ gần như giữ độ lệch chuẩn của điểm. Chọn TRƯỚC khi nhìn ΔIC của nó. Họ F giữ nguyên 11 spec; oracle chấm 12 (F cộng Z).
3. **Tổng số phiên Tầng 1 là 594, không phải ~570.** Mục 4.6 nói "ước chừng 570; Lát 1 chốt bằng cộng các đoạn". Cộng bằng `thi_truong_gia.dong_thoi_gian()`: S = 126; ba ngày khai ở phiên 128 · 150 · 172 (2100-07-01 · 2100-08-02 · 2100-09-01, đầu tháng dương lịch thứ 1–3 sau tháng chứa phiên 125); đọc ở khai + 251 + 22 = 401 · 423 · 445 (phiên có nhãn thứ 252 từ ngày khai cần giá tới +22); tổng = 445 + F + 22 + 1 = 594 (F = 126 phiên tiến-về-trước, mỗi phiên cần nhãn nên thêm 22 phiên giá). Ước 570 thiếu hai khoản 22 phiên. Test dựng lại bằng `pandas.bdate_range` và kiểm bằng nhãn THẬT `E.nhan_vuot_ro` (ứng viên i có đúng 252 phiên có nhãn từ ngày khai ở phiên đọc; F phiên cuối vừa khít).
4. **Hằng số KHAI ở Lát 1** (mục 4.2 chỉ để ngỏ φ_z; phần còn lại là cái mã buộc phải có số). Tất cả CHƯA hiệu chuẩn vào giá thật, và `tests/test_thi_truong_gia.py::test_cac_hang_KHAI_ghim_dung_gia_tri_da_ghi_o_ghi_chu_thi_cong` ghim chúng: φ_z = 0,97 (AR(1) ngày của z); AR(1) ngày của nhiễu riêng từng thành phần 0,90 (chỉ báo bền theo ngày); phần của z trong tiềm ẩn của `volume_score` b = 0,5 (a = √(1 − b²), nhiễu riêng được phóng 1/a để tương quan QUAN SÁT được vẫn là bảng MO-XE); độ lệch chuẩn ngày 0,010 (thị trường, bước t ν = 7,5) · 0,007 (mỗi ngành, bước t) · 0,015 (riêng mã, GARCH-t của BƯỚC 248); mỗi ngành 10 mã liền nhau, hệ số 1; nhiễu tranh luận N(0 ; 0,45) kẹp ±0,9; giá đầu U(10 ; 50) nghìn đồng; mã `GIA01`…`GIA60`. Giá trị các nấc là chuỗi ĐỀU từ biên dưới tới biên trên của bảng MO-XE (bảng chỉ cho số nấc và hai biên), mỗi nấc xác suất bằng nhau; tương quan hạng sinh bằng copula chuẩn (Pearson = 2·sin(πρ/6)).
5. **Chỗ sinh KHÁC thật, khai thẳng.** Điểm sinh có 85 giá trị khác nhau trong 7–91; điểm thật 61 nấc trong 23–83 (`MO-XE-KIEN-TRUC.md`, đo 31/08/2026). Mục 4.2 chỉ đòi khớp số nấc và tương quan của năm THÀNH PHẦN, không đòi khớp điểm cuối; nhưng điểm cuối sinh rộng hơn, nên mọi số liệu về số lệnh vượt ngưỡng của thị trường giả không nói gì về đường thật.
6. **κ chưa hiệu chuẩn ở Lát 1.** `kappa` là tham số của `sinh_thi_truong`; test dùng 0,01 (giá trị thử, không phải mức 0,5× · 1× · 2× MDE₈₀ của Lát 2). Ở 0,01: ΔIC_true của G = 0,0418, sai số MC 0,0057; của H = −0,0129 ± 0,0014; của Z = −0,0012 ± 0,0019 (lệnh ở STATE BƯỚC 261).
7. **Sai số MC của oracle một mẫu 5.000 phiên là ~14% ΔIC của G.** Mục 8 Lát 2 đòi κ khớp mục tiêu ±10% bằng oracle; với 0,0057/0,0418 = 14% ở κ = 0,01 thì một oracle 5.000 phiên không đủ (sai số tỷ lệ nghịch √số phiên: ước lượng cần ≥ 2 lần số phiên). Lát 2 phải chọn: tăng mẫu oracle, hoặc lấy trung bình nhiều oracle; mục 4.5 giữ nguyên ở BƯỚC này.
8. **Tiêu chí "mọi |ΔIC_true| < 2 sai số MC ở NULL" (mục 4.5 (c), mục 6 "KHÔNG ĐỌC ĐƯỢC", mục 8 Lát 1) đọc theo từng thị trường thì báo nhầm cỡ 43%.** Đo (30 thị trường NULL, dòng thử 9001, 12 spec mỗi thị trường): 13/30 thị trường có ít nhất một spec ngoài 2 sai số, trong khi 91,1% số ô (thị trường × spec) nằm trong; sd(Δ/sai số) = 1,15. Nghĩa là sai số MC được ước lượng gần đúng (hơi thấp), nhưng 12 spec cùng lúc thì "mọi spec" trượt gần nửa số thị trường dù máy đo tốt. Test của Lát 1 vì thế khoá TỶ LỆ ô (≥ 85%, sd trong 0,7–1,5, |trung bình| < 0,5 trên 4 thị trường × 12 spec) và hàm `spec_ngoai_hai_se` đo từng thị trường; Lát 5 phải khai lại tiêu chí máy đo thành tỷ lệ TRƯỚC khi chạy, và đó là việc đổi đặc tả nên cần người dùng duyệt cùng lúc với việc chép bảng mục 6 vào `docs/TIEU-CHI-DOC-TRUOC.md`.
9. **`sum()` của Python 3.12+ cộng số thực CÓ BÙ (Neumaier), 3.11 thì không**; máy chạy 3.13, CI 3.11. `cham_bong.diem_ung_vien` dùng `sum()` nên tự nó khác nhau giữa hai bản ở bit cuối (ví dụ 28,8 và 28,799999999999997 ở cùng một ô). `thi_truong_gia.diem_spec` cộng thẳng bằng vectơ; test đòi cùng điểm tới 1e-9, không đòi trùng bit. Hệ quả cho oracle: hoà hạng của một spec chỉ có thể lệch ở những cặp ô mà hai tổng bằng nhau về toán học nhưng khác ở bit cuối — hiếm và cùng chiều ở cả hai điểm.
10. **Tầng 1 không có OHLC; phép thử `validate_ohlcv` năm 2100 (mục 4.1 khoản 2) dựng khung OHLCV từ `close`** (mở = đóng hôm trước, cao/thấp ± 0,2%, khối lượng hằng) và đòi mức OK, kèm phép thử ngược: bẻ một phiên (cao < thấp) thì mức lên cao hơn OK. Nó chỉ chứng minh `data_quality` không từ chối NGÀY 2100; bộ sinh OHLCV đầy đủ là việc của Lát 4.
11. **Nhân tố ẩn z KHÔNG nằm trên `ThiTruongGia`** (chỉ `_sinh_loi` trả `z`, cho test); oracle thì nằm ở trường `su_that` của chính đối tượng ấy. Một vòng học nhận `ThiTruongGia` không có đường chạm tới z, nhưng `su_that` ở ngay cạnh: việc vòng học không đọc nó là gác G4 (không gọi oracle từ vòng học), việc của Lát 3 khi vòng học tồn tại.
12. **Dòng hạt.** Oracle dùng `[luong, chi_so, 1]` (hạt RIÊNG, mục 4.5); test dùng dòng 9001, ngoài năm dòng chính và ngoài dãy 6, 7… Trong lúc dựng, MỘT lượt thăm dò chạy dòng 2 (chi_so 1) và dòng 5 (chi_so 1…30) CHỈ ở mức oracle (không bước xác nhận nào tồn tại để nhìn kết quả). Khi Lát 5 chạy dòng 2 và 5, các thị trường ấy đã bị oracle nhìn một lần; nêu ra để không ai tưởng chúng còn nguyên.
13. **Không làm ở Lát 1 (thuộc Lát 2–5):** bước xác nhận, bộ đề xuất, sổ ứng viên giả, nâng cấp, hiệu chuẩn κ và MDE₈₀, Tầng 2, gác G2 · G4 · G6 · G7. Gác G2 (đường thật không nhập module thị trường giả) cũng ở Lát 3; trước đó chỉ có chiều ngược lại: `tests/test_san_dau.py::test_G2_duong_that_KHONG_nhap_san_dau` thêm `thi_truong_gia.py` vào danh sách được nhập `san_dau`.

