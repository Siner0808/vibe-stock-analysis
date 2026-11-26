# Thiết kế C4 — Thị trường giả có lợi thế cài sẵn: chứng minh vòng học chạy đúng (T6)

**Mốc:** C4 (`docs/LO-TRINH.md`, giai đoạn C). **Duyệt hướng:** người dùng, 06/11/2026, trong phiên leader (BƯỚC 259): *"C4 — thị trường giả (T6) (Recommended)"* — mở bằng MỘT đặc tả chỉ có chữ; người dùng duyệt đặc tả trước khi có dòng mã nào.
**Trạng thái:** đặc tả **ĐÃ CHỐT ĐỦ BẢY CÂU**: người dùng trả lời Q1, Q2, Q3, Q7 ngày 06/11/2026 và Q4, Q5, Q6 ngày 07/11/2026 (mục 2, mục 14). Không còn câu mở trong Q1–Q7 (một câu MỚI, về bộ ba của Tầng 2, mở ở mục 19.5 và ĐÃ ĐÓNG ngày 21/11/2026, BƯỚC 294: mục 19.8). Mã bắt đầu từ BƯỚC 261 (Lát 1, mục 8); Lát 2 xong ở BƯỚC 289 (mục 16); **Lát 3 xong ở BƯỚC 290 (mục 17)**; **Lát 4 xong ở BƯỚC 292 (mục 18)**; **BƯỚC chuẩn bị Lát 5 xong ở BƯỚC 293 (mục 19): độ lệch lịch · bảng sự thật Tầng 2 · chi phí của vòng trên Tầng 2 đã làm, còn bộ ba G · Z · H của Tầng 2 CHỜ NGƯỜI DÙNG QUYẾT (mục 19.5)** — 🔴 HẾT ĐÚNG ngày 21/11/2026: người dùng đã quyết phương án 2 và **BƯỚC 294 đã đóng câu ấy** (G′ = `bo_momentum_score`, dải PT đo ở dòng hạt 1, mục 19.8–19.9; hàng PT của mục 6 đã viết lại); **Lát 5 (a) ĐÃ XONG ở BƯỚC 295 (23/11/2026): bảng mục 6 đã ký ở `docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 37 và dụng cụ chạy chính thức `tools/chay_chinh_thuc_thi_truong_gia.py` có mã; ~~Lát 5 (b), lượt chạy chính thức dòng hạt 2 · 3 · 4, CHƯA làm (BƯỚC 296).~~** 🔴 HẾT ĐÚNG 25/11/2026: **Lát 5 (b) ĐÃ XONG ở BƯỚC 296 (lượt chạy chính thức dòng hạt 2 · 3 · 4, mục 20): kết cục *"KẾT CỤC: TRƯỢT ở A0, PT"* (A0 = 421/1000, ngưỡng ≤ 317; PT: G′ `QUA` 41/100, dải [7 ; 26]); mười hai tiêu chí còn lại ĐẠT; T6 CHƯA chứng minh; không ngưỡng hay tiêu chí nào bị đổi.** Nhãn *[Qn: ĐÃ CHỐT]* trong văn bản trỏ về mục 2 và mục 14. Bản đầu của đặc tả (commit `2c4c5c6`) để cả bảy câu ở dạng bản thảo, và bản trước ngày 07/11/2026 gọi Q4 · Q5 · Q6 là *mặc định, người dùng chưa chọn*; cả hai còn ở lịch sử git.

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

*Ghi chú BƯỚC 294 (người dùng, 21/11/2026, mục 19.8):* ở **Tầng 2** tham chiếu của hàng PT ở mục 6 là **G′ = `bo_momentum_score`**, không phải G (ở Tầng 2 G chỉ +0,0066 ± 0,0047, mục 19.4); bộ ba G · Z · H và ba loại ở bảng trên vẫn là của Tầng 1, không viết lại ở đây.

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

> 🔴 **HẾT ĐÚNG cho ĐO 38 (khai trước ở BƯỚC 300, mục 21):** luật xếp "Δ giảm" và "3 spec đầu có Δ > 0" ở trên là luật của ĐO 37 (đã chạy, TRƯỢT ở A0, mục 20); bản sửa xếp theo z = (Δ − μ)/σ chuẩn hoá và khai spec có z > 0 VÀ Δ > 0 — công thức và luật khai ở mục 21.1. Đoạn trên giữ nguyên làm sử liệu.

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
| **PT** | **Tầng 2: nhất quán tỷ lệ** — báo động ở NULL ≤ 12/100; G′ = `bo_momentum_score` `QUA` ở 2× nằm trong dải 99% [7 ; 26]/100 (mục 19.8–19.9) | NULL, 2× | 100 | như vế trái | chỉ là kiểm khớp Tầng 1, KHÔNG phải chứng cứ riêng (R = 100: nếu thật 5% → sai-trượt 0,15%; nếu thật 10% vẫn qua 80% — lực yếu, khai thẳng) |

> **Hàng PT, vế G (BƯỚC 294, 21/11/2026):** người dùng quyết phương án 2 của mục 19.5, nguyên văn *"làm theo đề xuất của bạn đi, phương án nào tốt nhất thì làm"* (mục 19.8). Vế "G `QUA` ở 2× ≥ 85/100" được thay bằng G′ và dải 99% ở trên; dải tính từ ΔIC_true(G′) đo ở dòng hạt 1 (mục 19.9, `docs/thi-truong-gia-g-phay.json`). Vế NULL "≤ 12/100", R = 100 và mọi hàng khác của bảng KHÔNG đổi.

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

> 🔴 **HẾT ĐÚNG ở các con số: Lát 4 (BƯỚC 292) ĐÃ ĐO, thay ước lượng này; số đo và lệnh ở mục 18 khoản 4.** Tóm tắt: một thị trường 5,1 phút một lõi (đúng ước lượng 4–5 phút), nhưng 200 thị trường trên 12 tiến trình ≈ 2,5 giờ chỉ riêng chấm điểm, gấp đôi ước lượng 1–1,5 giờ dưới đây. Đoạn dưới giữ nguyên làm sử liệu.

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

Không có trong Q1–Q7. Câu mới về bộ ba G · Z · H của Tầng 2 (mở ở mục 19.5, BƯỚC 293) **ĐÃ ĐÓNG ngày 21/11/2026** (BƯỚC 294): người dùng *"làm theo đề xuất của bạn đi, phương án nào tốt nhất thì làm"* = phương án 2 (mục 19.8). Còn ngỏ cho Lát 5, không phải câu của người dùng: Z′ · H′ nếu Tầng 2 chạy bộ ba K = 3 (mục 19.8 khoản 7). Đổi một quyết định ở 14.1 hay 14.2 sau Lát 1 là sửa đặc tả bằng commit riêng và phải chạy lại trên dòng hạt mới (mục 6).

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

## 16. Ghi chú thi công Lát 2 (BƯỚC 289, 20/11/2026) — chỗ mã khác đặc tả, và vì sao

Ghi sau khi viết mã và chạy hiệu chuẩn, TRƯỚC khi có số nào của lượt chạy chính (mục 13). Dụng cụ `tools/hieu_chuan_thi_truong_gia.py`, test `tests/test_hieu_chuan_thi_truong_gia.py`, kết quả `docs/thi-truong-gia-hieu-chuan.json`. Mọi số dưới đây đọc ra từ file ấy bằng `./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_thi_truong_gia.py --in-bang` (không chạy lại thị trường nào); số nào chưa có lệnh ở đó thì có lệnh ở STATE BƯỚC 289.

1. **Chỉ dòng hạt 1, và máy chặn chứ không chỉ lời hứa.** Dụng cụ không có đối số dòng hạt; mọi đường vào bộ sinh (`thi_truong_gia.sinh_thi_truong`, `tinh_su_that`) đi qua `kiem_luong`, nổ với mọi dòng khác 1, kể cả khi file kết quả bị sửa tay sang dòng khác (`doc_ket_qua`). Gác AST: hàm nào gọi bộ sinh mà không gọi `kiem_luong` TRƯỚC thì đỏ. Mục 7 không đòi gác này; thêm vì bất biến 7.
2. **Hạt thị trường chia theo VAI TRÒ, mỗi thị trường dùng ĐÚNG MỘT lần** (khối 100.000 chỉ số mỗi vai trò, 10.000 mỗi điểm của lưới): lưới lực · bốn mức · NULL smoke · oracle tìm κ · oracle kiểm · thăm dò. Mục 4.8 chỉ nói `[luong, chi_so]`; không dùng chung thị trường giữa các κ (số ngẫu nhiên chung sẽ làm đường lực trơn hơn nhưng khiến sai số nhị thức và bootstrap nói thấp hơn thật).
3. **Oracle là TRUNG BÌNH 24 mẫu 5.000 phiên, hai tập độc lập (`or_tim` dò κ, `or_kiem` đối chiếu), không phải một mẫu.** Mục 15 khoản 7 đã báo một mẫu có sai số ~14% ΔIC của G ở κ = 0,01; với 24 mẫu sai số đo được là 2,5% ở κ = 0,010 và 1,3% ở κ = 0,020 (cột `se` của file), đúng cỡ 14%/√24 = 2,9%. Mục 4.5 giữ nguyên (mỗi mẫu vẫn tính bằng `thi_truong_gia.tinh_su_that`, không sửa Lát 1).
4. **Bốn mức đọc thế này:** κ được dò nhị phân trên `or_tim` cho tới khi ΔIC_true(G) khớp mục tiêu ±2% (`tol_nhi_phan`), rồi độ lệch ±10% của mục 8 đo trên `or_kiem` — mẫu KHÔNG tham gia việc chọn κ. Mức 0× là κ = 0 đúng nghĩa đen, nên "±10% của 0" vô nghĩa: tiêu chí là |ΔIC_true| < 2 sai số của chính mẫu kiểm. Độ lệch của ba mức dương đều ÂM (−5,3% · −3,1% · −2,5%) vì mẫu kiểm cho ΔIC thấp hơn mẫu tìm cùng κ (0,0733 so với 0,0756 ở "1×", chênh 1,5 lần sai số của hiệu); cùng một tập hạt oracle dùng cho mọi κ nên đó là MỘT lần rút, không phải ba bằng chứng.
5. **MDE₈₀ là điểm của một đường probit khớp trên 8 điểm lưới, kèm sai số bootstrap tham số; sai số ấy KHÔNG gồm nhiễu của oracle.** Khớp P(`QUA`) = Φ(a + b·ΔIC_true) bằng cực đại hợp lý. Pearson χ² của 11 điểm đã đo (8 lưới + 3 mức) so với đường khớp là 6,91 trên ~9 bậc tự do (phân vị 99,9% của χ²(9) là 27,88; lệnh `--in-bang`): đường probit không lệch rõ khỏi số đếm. Sai số bootstrap (0,0007) chỉ do R hữu hạn; cộng sai số oracle (~1,3% của 0,0756 ≈ 0,0010) và chênh giữa hai tập oracle ở ý 4, nói MDE₈₀ chính xác tới ~2–3% là trung thực, 0,9% là không.
6. **Bảng giá giả đi thẳng vào `cham_xac_nhan.cham` bằng dict, bỏ bước CSV (`dinh_dang_bang_gia` → `phan_tich_bang_gia`).** Mục 5.3 nói "đã phan_tich_bang_gia". Test chứng minh bỏ bước ấy không đổi kết quả (CSV đọc lại giá lệch ~1 ULP vì `pd.read_csv` dùng bộ đọc nhanh; `trang_thai` bằng nhau, Δ và p bằng nhau tới 1e-9 / 1e-6) và bảng giả qua được mọi phép kiểm của bước đó. **Phép thử ấy tìm ra một lỗi của chính dụng cụ lúc viết:** dải ngày giả KHÔNG nằm trong năm 2100 như câu "ở năm 2100" của mục 4.1 khoản 2 gợi ý — 594 phiên thứ Hai–Sáu từ 2100-01-04 tới 2102-04-13 — nên giờ kéo viết cứng "2101-01-01" bị `phan_tich_bang_gia` từ chối ("gia tu tuong lai"). Nay `keo_luc_gia` suy từ nến cuối. Lỗi không đổi một con số nào đã ghi (`cham` chỉ in lại `keo_luc`), nhưng là bài học: một hằng số ngày viết tay cho "dải giả" sai ngay khi dải đổi độ dài.
7. **Hạt hoán vị là mặc định thật `cham_xac_nhan.HAT_RNG` cho MỌI thị trường** (mục 5.3: "mặc định thật, không đổi cho thế giới giả"). Hai nghĩa: (a) đúng thứ đường thật làm với mỗi ứng viên; (b) cùng 2.000 hoán vị mã được dùng ở mọi thị trường, nên nhiễu của phép so cặp cùng nguồn giữa các thị trường. Chưa đo xem (b) có làm các tỷ lệ bắt tương quan nhau không; Lát 5 nên biết.
8. **NULL smoke dùng R = 500 thị trường κ = 0, không phải 1.000 của B1** (mục 8: "ở lượt nhỏ"). Ngưỡng là chính B1: ≤ 7,5% thị trường có ≥ 1 báo động (báo động = `p` < 0,05/3, cả `QUA` lẫn `THUA`, như mục 6). Với R = 500 ngưỡng là 37; nếu mỗi thị trường báo động đúng ở mức danh nghĩa (1 − (1 − 0,05/3)³ = 4,92%) thì kỳ vọng ~24,6 và xác suất trượt ~0,6% (nhị thức) — đây là một kiểm MÁY, không phải kết quả T6, và nó KHÔNG thay B1 của Lát 5.
9. **Hai quan sát cho Lát 5 (chưa phải kết quả, chỉ ở dòng hạt 1):** (a) ứng viên Z báo động ở 114/5.200 = 2,19% thị trường có lợi thế (82/4.000 = 2,05% ở lưới, 32/1.200 = 2,67% ở ba mức), trên mức danh nghĩa 1,67% mỗi ứng viên nhưng dưới ngưỡng B3 (5%) khai ở mục 6; (b) ứng viên H không bao giờ `QUA` ở mọi thị trường có lợi thế (0 trên 5.200), khớp B4. Ghi để Lát 5 không ngạc nhiên nếu Z ở 2× báo động hơn 1,67%; mục 15 khoản 2 đã nêu Z gần suy biến.
10. **Không làm ở Lát 2 (thuộc Lát 3–5):** bộ đề xuất, nâng cấp, `chay-vong`, Tầng 2, gác G2 · G4 · G6 · G7. Hiệu chuẩn KHÔNG chạm `thi_truong_gia.py`.

## 17. Ghi chú thi công Lát 3 (BƯỚC 290, 21/11/2026) — chỗ mã khác đặc tả, và vì sao

Ghi sau khi viết mã, TRƯỚC khi có số nào của lượt chạy chính (mục 13). Module `vong_hoc_gia.py` (gốc repo; nhận dữ liệu, không sinh thị trường), dụng cụ `tools/chay_vong_thi_truong_gia.py`, test `tests/test_vong_hoc_thi_truong_gia.py`, biên bản mẫu `docs/vong-hoc-thi-truong-gia-mau.md`. Lát này KHÔNG báo tỷ lệ nào; thị trường mẫu là một biên bản minh hoạ.

1. **Cửa sổ mà bộ đề xuất được thấy (mục 5.1 · 4.6 · 7 G7) có hai cách đọc; chọn cách (a).** Mục 5.1 nói Δ tính trên "mọi phiên có nhãn của cửa sổ đã nhìn (126 phiên)"; mục 4.6 nói bộ đề xuất "chỉ thấy phần này"; mục 7 G7 nói "chỉ nhận dữ liệu ≤ ngày khai − 1". (a) **Cửa sổ chặt**: dòng quyết định VÀ giá của đúng S = 126 phiên đầu (phiên 0…125); một phiên chỉ có nhãn khi giá đóng cửa T+22 nằm trong cửa sổ, nên **104** phiên có nhãn (phiên 0…103). (b) Dòng của 126 phiên đầu nhưng giá kéo tới ngày khai − 1 (ngày khai đầu là phiên 128, nên giá tới phiên 127): **106** phiên có nhãn (0…105). Chọn (a): ít dữ liệu hơn, khớp chữ "chỉ thấy phần này", và "ngày khai − 1" là cận TRÊN chứ không phải mục tiêu (125 < 127) nên (a) thoả cả ba mục. **Đây là lựa chọn của leader ngày 21/11/2026, KHÔNG phải quyết định của người dùng**; đổi sang (b) là đổi một hằng (`cuoi_nhin` trong `chay_vong`) và đổi một test. `S` là hằng có tên (`thi_truong_gia.SO_PHIEN_DA_NHIN`); test `test_G7_cua_so_nhin_la_hang_S_khong_phai_ngay_khai_tru_mot` ghim cả hai con số 126 và 104, và `test_G7_moi_sau_cua_so_khong_doi_dau_ra_cua_bo_de_xuat_gia_tai_chi_so_S_tro_di` là phép thử "mồi": giá và dòng từ phiên S trở đi bị thay bằng nhiễu, hạng của 11 spec phải y hệt.
2. **`nang_cap` có thêm một tham số.** Chữ ký ở mục 5.4 là `nang_cap(so_phien_ban, ket_qua_xac_nhan, ma_ung_vien, phien_doc)`, nhưng kết quả của `cham_xac_nhan.cham` không mang spec của ứng viên (chỉ mã, số, trạng thái), còn khoản 2 đòi spec của phiên bản mới BẰNG đúng spec đã khai. Nay thêm `so_ung_vien` (sổ giả) làm tham số thứ năm; `phien_doc` là CHỈ SỐ phiên (không phải ngày) nên "phiên sau" là `phien_doc + 1` mà không cần lịch. Khoản 4 (điểm ghi từ phiên hiệu lực) nằm ở hàm riêng `ap_phien_ban`, không ở `nang_cap`.
3. **Kiểm tiến-về-trước đo ΔIC của `int(diem_ung_vien)` so với điểm đã ghi, từ phiên hiệu lực, và KHÔNG có phán.** Khoản 4 viết điểm ghi sau nâng cấp là `int(diem_ung_vien(spec, components))`, nên phép so là IC của chuỗi nguyên ấy với IC của điểm đã ghi cũ (không phải IC của tổ hợp thực chưa cắt). Chỉ dùng dòng và giá từ phiên hiệu lực trở đi (không một giá nào ở phiên đọc hay trước đó; test ghim bằng máy ghi lời gọi `nhan_vuot_ro`), nhãn của phiên t dùng giá t+1…t+22 nên có `du_cua_so` nói cửa sổ có đủ F phiên có nhãn không. Một thị trường cho MỘT số, không KTC, không so với ngưỡng nào: bootstrap qua thị trường của tiêu chí C2 là việc của Lát 5. Cửa sổ F của ứng viên đọc đầu tiên nằm gọn trong thị trường (hiệu lực phiên 402, F + 22 phiên phía sau tới phiên 549 < 594); chỉ ứng viên khai SAU CÙNG vừa khít phiên cuối (mục 15 khoản 3).
4. **Dòng hạt: dụng cụ cho phép 1 và 9001, chặn 2 · 3 · 4 · 5; module vòng không có cửa vào bộ sinh.** `kiem_luong` của dụng cụ `chay-vong` theo khuôn của Lát 2 nhưng `LUONG_DUOC_PHEP = (1, 9001)` (9001 là dòng thử của test, mục 15 khoản 12); dòng 5 (chẩn đoán SAU khi đã nhìn kết quả) cũng bị chặn vì không dùng để dựng hay thử. `vong_hoc_gia` nhận `dong` và `gia` — không nhận `ThiTruongGia`, vì đối tượng ấy mang bảng sự thật của oracle (mục 15 khoản 11) — và không gọi bộ sinh; nên không có đường nào từ vòng tới một dòng hạt hay tới oracle. Oracle chỉ được dụng cụ chấm đọc SAU khi vòng đã quyết (gác G4, kèm phép thử thứ tự lời gọi). Lát này KHÔNG sinh thị trường nào của dòng 1: mọi test và biên bản mẫu ở dòng 9001.
5. **Cả ba ứng viên khai xong trước lần đọc đầu tiên, và vòng khẳng định điều đó.** Ba ngày khai ở phiên 128 · 150 · 172, lần đọc đầu ở phiên 401. `chay_vong` nổ nếu có ứng viên khai SAU phiên đọc đầu (đặc tả không nói lúc ấy làm gì), nên K tại lúc đọc luôn là số đã khai (3) và không có ứng viên "chưa khai" bị huỷ. Phiên đọc suy ra bằng `phien_khai + MOC_DOC − 1 + DO_TRE_NHAN`, và test kiểm CẢ HAI PHÍA bằng máy đo thật: ở phiên đọc − 1 còn 251 phiên có nhãn (`CHUA TOI MOC`), ở phiên đọc đủ 252.
6. **`cham_xac_nhan.cham` chấm lại mọi ứng viên của sổ ở mỗi lần đọc.** Ở lần đọc thứ hai nó tính lại cả ứng viên đã đọc (cùng kết quả, vì chỉ nhìn 252 phiên có nhãn đầu của mỗi ứng viên và hạt hoán vị cố định); vòng chỉ HÀNH ĐỘNG theo kết quả của ứng viên đang tới phiên đọc. Đây là chi phí, không phải hành vi; đổi sang `cham_mot` sẽ bỏ "xác nhận qua `cham`" của mục 8.
7. **Bộ đề xuất là chỗ cắm một hàm `(dong, gia) -> [{ten, spec, delta}]`** (mục 5.1 gọi nó "giao thức một hàm"): `chay_vong` nhận `de_xuat_fn`. Test dùng nó để dựng ca G · Z · H cho trước (THUA → DANG CHAM → QUA trong MỘT thị trường), vì bộ đề xuất cơ sở chỉ khai spec có Δ > 0 trên cửa sổ đã nhìn nên không tự khai H.
8. **Đánh dấu huỷ là khoá `bi_huy_vi_nang_cap: true` trên dòng của ứng viên trong sổ giả** (khuôn sổ `kiem_so_ung_vien` bỏ qua khoá lạ). Ứng viên vẫn nằm trong sổ nên `cham_bong.so_da_sang` và `nguong` không đổi: "K vẫn đếm" là tính chất của cách làm, và có test (K = 3, ngưỡng 0,05/3 trước và sau khi huỷ).
9. **Một quan sát từ MỘT thị trường mẫu, KHÔNG phải kết quả** (dòng 9001, chỉ số 1, κ mức 2×; `docs/vong-hoc-thi-truong-gia-mau.md`): trên cửa sổ đã nhìn bộ đề xuất xếp `mono_volume_score` Δ +0,159 (ΔIC_true của oracle +0,142 ± 0,004), nhưng hai spec khai tiếp theo có Δ +0,056 và +0,040 trên cửa sổ đã nhìn mà ΔIC_true chỉ +0,022 và +0,024. Đó là hình dạng "cực đại của nhiều lần thử được đọc là lợi thế" (bất biến 7) ngay trong bộ đề xuất; bước xác nhận (ngưỡng 0,05/K) là thứ phải chặn nó, nhưng ở thị trường mẫu hai ứng viên ấy bị huỷ trước khi đọc nên CHƯA thấy nó chặn hay không. Mới một thị trường; Lát 5 là nơi đo.
10. **`sum()` của Python 3.12+ ở `cham_bong.diem_ung_vien` có thể làm `int()` của điểm nâng cấp lệch một đơn vị ở một ô nằm đúng trên biên nguyên** (mục 15 khoản 9). Không test nào ghim một chữ số của biên bản mẫu; test so CẤU TRÚC (spec đã khai, trạng thái, phiên đọc và hiệu lực). Biên bản mẫu sinh ở Python 3.13; chưa chạy ở 3.11.
11. **Một gác sẵn có đã đỏ và được nới đúng hai chỗ: `tests/test_moc_doc.py::test_ma_tran_cap_chi_goi_voi_phien_toi_da_bang_MOC_DOC_ngoai_vong_sang_cu`.** Gác đòi `cham_bong.ma_tran_cap` chỉ được gọi ở `phan_quyet` (với `phien_toi_da=MOC_DOC`) và ở vòng sàng đã ngừng dùng. Mục 5.1 đòi bộ đề xuất dùng chính `ma_tran_cap` trên cửa sổ đã nhìn (không cắt 252, không `so_cap`), và kiểm tiến-về-trước (khoản 3) cũng cần nó; hai đặc tả đó mâu thuẫn với gác chữ-nghĩa chứ không với ý của gác (không đường nào tới một phán quyết mà không qua mốc). Nay gác miễn đúng hai hàm `vong_hoc_gia.de_xuat` và `vong_hoc_gia.kiem_tien_ve_truoc`, đòi cả hai có mặt (danh sách không nằm chơi) và đòi lời gọi còn lại vẫn là `phan_quyet` với `MOC_DOC`; gác G6 của lát này giữ chiều kia: `vong_hoc_gia.py` không gọi `so_cap`. Đột biến: thêm một lời gọi `ma_tran_cap` ở hàm thứ ba, bỏ mốc cắt ở `phan_quyet`, bỏ một miễn trừ, thêm một miễn trừ lạ — cả năm phát (hai chỗ thêm lời gọi) đỏ. Ghi ra vì đây là sửa một test không phải của lát này.
12. **Không làm ở Lát 3 (thuộc Lát 4–5):** Tầng 2, mọi tỷ lệ, tiêu chí A · A0 · B · C · P · PT (Lát 5), bootstrap của C2.

## 18. Ghi chú thi công Lát 4 (BƯỚC 292, 21/11/2026) — chỗ mã khác đặc tả, và vì sao

Ghi sau khi viết mã, TRƯỚC khi có số nào của lượt chạy chính (mục 13). Module `thi_truong_gia_tang2.py` (gốc repo), dụng cụ `tools/chay_tang2_thi_truong_gia.py`, test `tests/test_tang2_thi_truong_gia.py`. Lát này đo ống dẫn của MỘT thị trường (P1, P2, P4) và chạy MỘT thử nhỏ P3; KHÔNG có tỷ lệ nào của Lát 5 (không PT, không tỷ lệ trên 100 thị trường). Dòng hạt: chỉ 9001 (dòng thử, mục 15 khoản 12); dòng 2 · 3 · 4 · 5 bị chặn bởi cùng `kiem_luong` của dụng cụ `chay-vong`.

1. **Hằng KHAI của Tầng 2, và AI khai.** Đặc tả mục 4.2 chỉ chốt "khối lượng mang `z`"; số bắt buộc phải có là: `HE_SO_Z_KHOI_LUONG` = 0,4 (hệ số của `z` trong log khối lượng), `SIGMA_KHOI_LUONG` = 0,3, cỡ khối lượng trung vị 1.000.000 cổ phiếu, `SIGMA_CO_MA` = 0,7, lô 100, `SIGMA_GAP` = 0,003 (kẹp ±2%), `SIGMA_BIEN_TRONG_NGAY` = 0,006. **Chúng được chọn và ghim bằng test (`test_cac_hang_KHAI_ghim_dung_gia_tri_da_khai`) TRƯỚC khi có BẤT KỲ nhãn hay IC nào của Tầng 2 tồn tại** (commit `e8f1637`, trước lượt P3 đầu tiên); thứ đầu tiên người viết thấy từ `_analyze` là ba điểm mẫu trong một phép đo chi phí, rồi lượt đo chi phí và P1 — không có nhãn hay IC nào. **Đây là khai của leader ngày 21/11/2026 (chấp nhận hai hằng 0,4 và 0,3 làm giá trị KHAI sau báo cáo phase 1), KHÔNG phải quyết định của người dùng.** Không sửa sau P3: sửa là sửa đặc tả và đổi dòng hạt (6, 7…), đúng bất biến 7.
2. **Dòng thời gian Tầng 2 (mục 4.6): 250 phiên khởi động chiếm 250 ngày ĐẦU của lịch giả.** Ngày giả liền một mạch từ 2100-01-04 (gác G5 cấm ngày trước đó), nên phiên có quyết định đầu tiên là 2100-12-20 và phiên cuối 2103-03-29 (844 ngày, 594 có quyết định). Lát 1–3 không có khởi động nên không gặp chuyện này (xem khoản 12 về hệ quả với dòng thời gian của vòng).
3. **Khung OHLCV (mục 4.2 "bộ sinh OHLCV").** Lợi nhuận, `z` và hạt là CHÍNH `thi_truong_gia._sinh_loi` (không bản sao); phần thêm (mở cửa, râu nến, khối lượng) rút SAU nó và KHÔNG phụ thuộc `kappa`, nên thị trường NULL và thị trường có lợi thế cùng hạt có CÙNG khối lượng (có test). Biên ±7% giữ chặt; **phép thử `data_quality = OK` ở mọi dòng bắt được một lỗi của chính bộ sinh ở lượt chạy đầu**: lợi nhuận kẹp ở đúng biên làm `close/ref` vượt biên 1e-16 (làm tròn của `cumprod`), `np.clip` với cận dưới > cận trên trả cận trên (< đóng cửa), `validate_ohlcv` (so chặt) báo OHLC_INCONSISTENT và 3.451 dòng ra `data_quality = WARN` ở 5/60 mã. Phép thử đầu của tôi dung sai 1e-9 nên bỏ lọt; sửa (kẹp RỒI mới bảo đảm cao ≥ thân nến), test nay so CHẶT và đòi mẫu có ca chạm biên (một mẫu nhỏ không có ca nào nên xanh vô nghĩa: lỗi 66).
4. **CHI PHÍ ĐÃ ĐO, thay ước lượng ở mục 9.** Lệnh (máy 8 lõi vật lý / 16 lõi logic, Python 3.13.14, một tiến trình, thị trường dòng 9001 chỉ số 1, κ mức 2×): `./.venv/Scripts/python.exe -X utf8 tools/chay_tang2_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2 --tien-do` → **306,6 s tường · 304,7 s CPU** cho **35.640** lần `_analyze` (60 mã × 594 phiên) = **8,60 ms một lần** (sinh khung 0,04 s; mỗi mã min 4,5 · trung vị 5,1 · max 6,6 s); cùng lệnh ở mã TRƯỚC khi sửa lỗi khoản 3: 285,8 s (8,02 ms) — nhiễu giữa hai lượt cỡ 7%. Ước lượng mục 9 (4–5 phút, 7,5–8,3 ms) ĐÚNG ở cỡ một thị trường; lịch sử ở đây dài 251–844 dòng (ước lượng giả định 300–330) mà chi phí một lần chấm không phụ thuộc độ dài. Bộ nhớ ~120 MB một tiến trình. **Độ co giãn theo số tiến trình** (N tiến trình song song, mỗi tiến trình MỘT thị trường khác nhau, 8 mã đầu, `for i in $(seq 1 N); do ./.venv/Scripts/python.exe -X utf8 tools/chay_tang2_thi_truong_gia.py --luong 9001 --chi-so $i --muc 2 --so-ma-cham 8 & done; wait`; đọc dòng "chấm điểm"):

   | N tiến trình | ms một lần `_analyze` | lần chấm mỗi giây (cả máy) | 200 thị trường × 35.640 = 7.128.000 lần |
   |---|---|---|---|
   | 1 | 8,5 | ~118 | ~17 giờ |
   | 8 | 12,6 | ~635 | ~3,1 giờ |
   | 12 | 14,9 | ~805 | **~2,5 giờ** |
   | 16 | 16,5 | ~970 | ~2,0 giờ |

   **Lượt chạy Tầng 2 của Lát 5 (100 NULL + 100 ở 2×) vì thế ~2,5 giờ ở 12 tiến trình, CHỈ phần chấm điểm**, gấp đôi ước lượng 1–1,5 giờ của mục 9. Vì sao: máy có 8 lõi VẬT LÝ (16 logic), nên ước lượng "16 lõi" của mục 9 tính thừa; ở 12 tiến trình mỗi lần chấm chậm đi 1,7 lần so với một tiến trình. **Không gồm** bước xác nhận (`cham_xac_nhan.cham`, 2.000 hoán vị mỗi lần đọc), bộ đề xuất, và phát lại: chưa đo ở Tầng 2 (khoản 12).
5. **VN-INDEX giả (mục 4.9) là chỉ số bình quân đều của 60 mã, không phải "chính nhân tố thị trường cộng dồn".** `_sinh_loi` không trả nhân tố thị trường ra ngoài và Lát này không sửa `thi_truong_gia.py`; `vni_gia` dựng `1000 · TB(giá / giá đầu)` trên mọi ngày (cả khởi động, để có MA50 từ phiên đầu). Cùng hướng đi theo nhân tố thị trường (nhân tố chung của mọi mã) nhưng KHÔNG phải nó.
6. **P2 phủ cổng VN-INDEX, KHÔNG phủ cổng độ rộng.** `NguonDoRong(co_tu_gia(60 khung), vni=NguonVni(VN-INDEX giả))` được dựng và truyền vào `san_dau.phat_lai` đúng như mục 4.9, nhưng cấu hình mặc định (`CauHinhVao.tu_module()` hôm nay) có `do_rong_nguong` = 0 nên độ rộng không bị hỏi. Bật ngưỡng > 0 thì ĐƯỜNG THẬT (`run_session` không nhận nguồn) đọc độ rộng từ cache toàn cục — đúng thứ Tầng 2 cấm — nên cần một cách tiêm riêng ở phía đường thật; không làm ở Lát này. Hai điểm nữa: dòng quyết định của phép thử là dòng `cham_diem` của Tầng 2 (không phải sổ `decisions` của đường thật), kèm phép kiểm điểm mà `run_session` chấm lúc chạy bằng điểm đã ghi ở MỌI dòng sổ (524/524 trên thị trường thử; 0 lệch); và đường thật đọc cổng qua một BẢN SAO RIÊNG của `market_filter` (`vni_tiem_cho_duong_that`) vì `tests/test_sheets_store.py` ghim `market_filter.is_vni_bullish` thành hàm hằng ở mức module.
7. **Kết quả P1, P2, P4 (một thị trường, dòng 9001).** P1 (chỉ số 1, mức 2×, đủ 60 × 594): **ĐẠT, 0 vi phạm / 35.640 dòng** (cột bằng bảng `decisions` thật đọc từ sổ `:memory:`, `score` nguyên trong [5 ; 95], năm thành phần trong [0 ; 100], `data_quality` = OK, không trùng khoá, không dòng nào ở phần khởi động, `cham_bong.doc_quyet_dinh` đọc hết). P2 (`tests/test_tang2_thi_truong_gia.py::test_P2_phat_lai_ra_DUNG_cac_lenh_cua_duong_that_tung_o_cua_COT_TUONG_DUONG`; 8 mã × 80 phiên, 120 khởi động): **15 lệnh thật = 15 lệnh phát lại, 0 khác biệt ở mười hai cột `san_dau.COT_TUONG_DUONG`**; cổng VN-INDEX chặn 9 tín hiệu đủ điểm (phép thử không rỗng), có lệnh cắt lỗ, đóng và còn mở. P4: G1, G3, G4, G5 cho module và dụng cụ trong `test_P4_G1_den_G5_cung_xanh_cho_module_va_dung_cu_tang2`; G2 ở `tests/test_vong_hoc_thi_truong_gia.py::test_G2_*` (nay phủ cả module và dụng cụ Tầng 2) và `tests/test_san_dau.py::test_G2_duong_that_KHONG_nhap_san_dau` (module Tầng 2 được thêm vào danh sách được nhập `san_dau`, chiều nhập chủ ý của mục 7 G2).
8. **Hai quan sát về ĐƯỜNG THẬT (KHÔNG sửa; leader đưa vế đường thật vào danh sách chờ).** (a) `paper_runner._ANALYZE_CACHE` khoá bằng `(mã, số dòng, ngày cuối, ngày phiên)` cộng dấu vân bộ nhớ, KHÔNG chứa nội dung giá: hai thị trường giả cùng tên mã và lịch, khác hạt, va chạm và thị trường thứ hai nhận NGUYÊN kết quả của thị trường thứ nhất (test `test_BAY_khoa_cache_khong_chua_noi_dung_gia_hai_thi_truong_dung_khoa` chứng minh va chạm). Ở đường thật mã nào cũng có tên và ngày riêng nên chưa thấy hại; ở thế giới giả thì hại ngay, nên lượt chấm xoá cache trước, sau và sau mỗi nến. (b) `post_mortem_learning.get_learning_engine()` dựng engine mặc định bằng `PostMortemLearningEngine.__init__` → `load_memory`, đọc `sl_pattern_memory.json` từ thư mục hiện hành NGAY CẢ KHI engine tắt (đọc mã, rồi test dựng lại: engine mồi file hỏng không in cảnh báo vì lượt chấm đặt engine tắt trỏ vào đường không có file). Phụ: `urllib3` thăm dò IPv6 lúc nhập (một socket loopback, không lưu lượng); phép thử "tạo socket thì nổ" vì thế nạp module TRƯỚC rồi mới cài chốt.
9. **Chỗ điểm thật ở dữ liệu giả khác bảng đã đo (không chỉnh).** Một thị trường, κ mức 2×: điểm cuối 58 giá trị khác nhau trong 24…83 (thật: 61 nấc, 23…83), 20,2% dòng ≥ ngưỡng mua 62; số nấc năm thành phần trend 10 (thật 10) · momentum 16 (17) · volume 12 (13) · sr 7 (7) · **risk 10 nấc, 15…70 (thật 8 nấc, 10…45)**. Chỉ `risk_score` lệch cả số nấc lẫn khoảng; không chỉnh (leader, 21/11/2026), ghi để Lát 5 biết khi so số lệnh.
10. **P3 thử nhỏ (dòng 9001; 6 thị trường mức 2×, chỉ số 1–6, và 6 thị trường NULL làm đối chứng, chỉ số 11–16; chỉ số CHỌN TRƯỚC, không chọn lại).** Lệnh mỗi thị trường: `./.venv/Scripts/python.exe -X utf8 tools/chay_tang2_thi_truong_gia.py --luong 9001 --chi-so <i> --muc 2 --json` (NULL: `--muc 0`), 12 tiến trình song song, 564–570 s mỗi thị trường, cả lượt ~10 phút; mỗi thị trường 34.320 cặp (phiên, mã) có nhãn, P1 đạt ở cả 12. Đo: IC (tương quan hạng gộp, `E.rho_hang`) của từng thành phần với nhãn `E.nhan_vuot_ro`. **ĐẾM, không tỷ lệ:** IC của `volume_score` DƯƠNG ở **6/6** thị trường 2× (+0,114 · +0,094 · +0,090 · +0,113 · +0,105 · +0,113) và ở **4/6** thị trường NULL (+0,010 · +0,004 · +0,009 · −0,000 · −0,012 · +0,011; có dấu âm, tức máy đo có thể cho kết quả âm). Tiêu chí P3 của mục 6 (≥ 90/100 ở 2×) là việc của Lát 5; sáu thị trường không nói gì về tỷ lệ. **Nhưng phép đo lộ ra điều mục 4.1 khoản 1 không lường:** ở 2×, IC của `trend_score` là +0,136 · +0,169 · +0,102 · +0,130 · +0,117 · +0,097 và của `sr_score` là −0,130 · −0,163 · −0,103 · −0,113 · −0,107 · −0,111 — CÙNG cỡ hay LỚN HƠN của `volume_score` — còn `momentum_score` ≈ 0 (−0,036 … +0,017) và `risk_score` +0,005 … +0,061; ở NULL cả `trend` và `sr` trong ±0,03. Giải thích khả dĩ nhất: kỳ vọng cài sẵn `κ·z/21` nằm trong GIÁ và `z` bền (φ_z = 0,97), nên các chỉ báo thuần giá của agent thật (xu hướng, vùng giá) đọc được nó qua trôi giá — điều mà Tầng 1 loại trừ bằng cách sinh thành phần độc lập với giá. Hai dữ kiện khoá nó: NULL (κ = 0, khối lượng VẪN mang `z`) cho IC của `trend`/`sr` ≈ 0, và chẩn đoán dưới đây (κ mức 2×, khối lượng KHÔNG mang `z`) giữ nguyên chúng; thứ duy nhất phụ thuộc κ là giá. **Chẩn đoán SAU P3** (tắt `z` khỏi khối lượng chỉ trong tiến trình, KHÔNG sửa file; dòng 9001, chỉ số 21–23, mức 2×; dòng 5 bị chặn nên không dùng): IC của `trend` +0,143 · +0,114 · +0,120 và `sr` −0,143 · −0,109 · −0,102 GIỮ NGUYÊN, còn IC của `volume_score` rơi từ ~+0,10 xuống +0,050 · +0,045 · +0,052 — tức khoảng một nửa IC của `volume_score` không cần `z` trong khối lượng, nửa còn lại cần. Suy luận về nguồn của nửa đầu: OBV của agent khối lượng nhân DẤU biến động giá với khối lượng nên đọc được trôi giá; chưa tách OBV khỏi các luật khác của agent khối lượng. Hệ quả: ở Tầng 2 lợi thế đi vào điểm bằng nhiều thành phần chứ không chỉ `volume_score` (mục 4.1 khoản 1 và mục 4.2 viết "chỉ một thành phần điểm đọc được z"); với bộ ba G · Z · H của mục 4.3 (G tăng trọng số `volume_score`, Z đổi chỗ trend ↔ sr, H bỏ `volume_score`) ΔIC_true của Z KHÔNG còn ≈ 0 và của H KHÔNG còn chắc âm khi điểm do agent thật chấm. Không đổi mục 4 ở BƯỚC này (đó là sửa đặc tả, cần chạy lại trên dòng hạt mới): ghi vào "điều kiện trước Lát 5".
11. **Đột biến (24 phát, bộ đục ngoài repo `vibe_logs_292/mut_p2.py`; baseline 69 passed một lần trên mã chưa đục trước, lỗi 205): 23 đỏ, 1 sống sót TƯƠNG ĐƯƠNG.** P2 (12 phát: sàn HNX · ngưỡng 58 · bắt đầu lệch 1 phiên · kết thúc sớm 1 phiên · VN-INDEX đảo ngược · điểm ghi +1 · cổng cache toàn cục không cấm · đếm chặn VN luôn 0 · đường thật không tiêm VN-INDEX · `vni_gia` bỏ khởi động · đường thật bỏ một phiên · không trả lại `market_filter`), P3 (5 phát: nhãn lệch 1 phiên · đảo dấu IC · nhãn 20 phiên · IC của thành phần lấy cột điểm · đếm cặp không nhãn), P4 và cách ly (7 phát: mở file ghi · chuỗi `backtest` · dụng cụ nhắc oracle · ngày 2026 · sổ không phải `:memory:` · nhập `socket` · dụng cụ bỏ `kiem_luong`). Sống sót: **đổi sàn của phát lại sang HNX** — cột `exchange` không nằm trong mười hai cột `COT_TUONG_DUONG` và bước giá của mã giả `GIA01`… tra theo tên mã, không theo đối số sàn, nên mười hai cột không đổi trên thị trường này; tương đương với phép so đã khai. Lượt đầu của phase 1 (7 phát, 6 đỏ + 1 đối chứng tương đương) và phát "bỏ bảo đảm cao ≥ thân nến" (sống sót lúc test còn dung sai, đỏ sau khi so chặt) nằm trong cùng bộ.
12. **ĐIỀU KIỆN TRƯỚC LÁT 5 (việc của một BƯỚC chuẩn bị riêng, leader quyết định ngày 21/11/2026; KHÔNG làm ở Lát 4).** (a) ✅ **ĐÃ LÀM ở BƯỚC 293 (mục 19.1).** *Lệch dòng thời gian.* `thi_truong_gia.dong_thoi_gian()` tính ngày khai (đầu tháng dương lịch) trên lịch bắt đầu từ 2100-01-04; ở Tầng 2 phiên có quyết định thứ k nằm ở ngày thứ 250 + k của lịch, nên đầu tháng rơi vào phiên khác: đo (`vibe_logs_292/lech_lich.py`) ba ngày khai ở phiên **128 · 150 · 172** (Tầng 1) thành **139 · 160 · 183** (Tầng 2), ba lần đọc 401 · 423 · 445 thành 412 · 433 · 456, tổng phiên 594 thành **605**; dùng 594 làm số phiên có quyết định của Tầng 2 thì cửa sổ tiến-về-trước của ứng viên khai sau cùng không đủ. Cần tính lại dòng thời gian với độ lệch khởi động (không sửa `thi_truong_gia.py` ở Lát 4). (b) ✅ **ĐÃ ĐO ở BƯỚC 293 (mục 19.7).** *Chi phí của vòng trên Tầng 2*: bộ đề xuất, ba lần `cham_xac_nhan.cham` (2.000 hoán vị), kiểm tiến-về-trước — chưa đo; khoản 4 chỉ là chấm điểm. (c) ✅ **ĐÃ ĐO ở BƯỚC 293 (mục 19.2 – 19.5); bộ ba của Tầng 2 CHỜ NGƯỜI DÙNG QUYẾT.** *Cách đọc P3 và bộ ba G · Z · H sau phát hiện ở khoản 10*: lợi thế đi vào cả `trend`, `sr` lẫn `volume`; Lát 5 phải khai trước G · Z · H nào của Tầng 2 và ΔIC_true nào làm chuẩn (oracle Tầng 1 không chấm bằng agent thật). (d) *Phép tiêm độ rộng ở đường thật* (khoản 6) nếu Lát 5 muốn thử cổng độ rộng. (e) Số tiến trình và thời gian: ~2,5 giờ ở 12 tiến trình (khoản 4), dòng hạt 4.
13. **Không làm ở Lát 4 (thuộc Lát 5 hoặc BƯỚC chuẩn bị):** tỷ lệ PT, tỷ lệ P3 trên 100 thị trường, bộ đề xuất · xác nhận · nâng cấp trên dữ liệu Tầng 2, tiêu chí mục 6 chép vào `docs/TIEU-CHI-DOC-TRUOC.md`, sửa `thi_truong_gia.py`, `paper_runner`, `post_mortem_learning`, `master_agent` hay bất kỳ thứ gì của đường thật.

## 19. Chuẩn bị Lát 5 (BƯỚC 293, 21/11/2026) — bảng sự thật của Tầng 2 và bộ ba G · Z · H: ĐÃ QUYẾT 21/11/2026 (PHƯƠNG ÁN 2, mục 19.8–19.9)

**Trạng thái: ĐÃ QUYẾT ngày 21/11/2026 (BƯỚC 294) — phương án 2; xem 19.8 (quyết định và lời khai trước) và 19.9 (số đo ở dòng hạt 1).** Các mục 19.1–19.7 dưới đây là bản BƯỚC 293, giữ nguyên làm lịch sử; câu "chờ người dùng quyết" ngay dưới đây hết đúng. Câu gốc: mục này đo và nêu phương án; nó KHÔNG sửa mục 4 hay mục 6 và KHÔNG đổi ngưỡng nào. Sửa một dòng của mục 6 là sửa đặc tả bằng commit riêng (mục 6, "Quy tắc đọc"). Đây là việc (c) của mục 18 khoản 12; việc (a) (độ lệch lịch) ở mục 19.1 và việc (b) (chi phí của vòng trên Tầng 2) ở mục 19.7, cả hai đã làm.

**Số ở mục này là số THIẾT KẾ, đo ở dòng hạt 9001 (dòng thử), không phải kết quả T6.** Muốn dùng một ΔIC_true làm chuẩn tham chiếu cho Lát 5 thì phải đo lại trên dòng hạt khác 9001 (bất biến 7); xem 19.6.

### 19.1 Độ lệch lịch (việc (a)) — làm xong

`thi_truong_gia.dong_thoi_gian(lech)` có thêm tham số `lech` (mặc định 0; Tầng 1 ra ĐÚNG đầu ra cũ, có test so với bản cũ dán nguyên văn và ghim 128 · 150 · 172 / 401 · 423 · 445 / 594). `thi_truong_gia_tang2.dong_thoi_gian_2()` gọi nó với `lech` = 250 phiên khởi động. Đo lại bằng mã: ngày khai ở phiên **139 · 160 · 183** (2101-07-01 · 2101-08-01 · 2101-09-01), ba lần đọc ở **412 · 433 · 456**, tổng **605** phiên có quyết định — ĐÚNG ba bộ số đo ở mục 18 khoản 12a. Viết lại độc lập bằng `pandas.bdate_range` cho ra cùng số, và `vong_hoc_gia.phien_khai` đọc trên lịch của phiên có quyết định Tầng 2 cho ra cùng ba phiên khai (vòng vốn đã suy lịch từ dữ liệu nó nhận, nên phần sửa là SỐ PHIÊN cần sinh: 605, không phải 594). `sinh_thi_truong_2` nay mặc định 605. Biên bản mẫu của Lát 3 (`docs/vong-hoc-thi-truong-gia-mau.md`) tái lập từng dòng: 43/43 dòng giống nhau khi chạy lại `tools/chay_vong_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2`.

### 19.2 Đo gì, bằng gì

Oracle Tầng 2 (`tools/oracle_tang2_thi_truong_gia.py`) là bản Tầng 2 của oracle ở mục 4.5, cùng phép tính, khác nơi lấy điểm và thành phần:

* **Mẫu**: một mẫu dài CÙNG tham số, qua CHÍNH `thi_truong_gia_tang2.sinh_thi_truong_2` (cùng bộ sinh khung OHLCV, khối lượng mang `z`), hạt riêng `[luong, chi_so, 2]` (oracle Tầng 1 dùng `[luong, chi_so, 1]`), dòng hạt 9001 (dòng 1 hay 9001 qua cửa `kiem_luong`; dòng 2 · 3 · 4 · 5 chưa đụng). 5.000 phiên có quyết định mỗi mẫu, 60 mã, 250 khởi động.
* **Chấm**: bằng CHÍNH `thi_truong_gia_tang2.cham_diem_theo_ma` (đường của `cham_diem`: `paper_runner._analyze` thật, lịch sử cắt tới từng phiên), kèm **cửa sổ trượt 855 dòng** (= 250 khởi động + 605, lịch sử dài nhất một thị trường Tầng 2 từng đưa cho `_analyze`; đường quét thật cũng chỉ giữ ~784 phiên). Lý do cửa sổ: chi phí một lần chấm tăng theo độ dài lịch sử — đo một mã, 30 lần mỗi mốc: 5,8 ms ở 600 dòng, 6,2 ms ở 850, 7,1 ms ở 1.500, 7,8 ms ở 2.500, 9,0 ms ở 4.000 (mở rộng) so với 6,1 ms ở cửa sổ 844. Test chứng minh cửa sổ cắt đúng số dòng và `None` là mở rộng như cũ.
* **Điểm đã ghi** = `int(final_score)` (đúng cột `score` của `dong_quyet_dinh`); thành phần = `score_breakdown`.
* **ΔIC_true** của 12 spec (họ F cộng Z; G · Z · H là `mono_volume_score` · `doi_cho_trend_sr` · `bo_volume_score`) so với điểm đã ghi, bằng `E.rho_hang` trên nhãn `E.nhan_vuot_ro`; **sai số Monte Carlo** = độ lệch chuẩn giữa 10 khối phiên liền nhau / √10, ĐÚNG công thức của `thi_truong_gia.tinh_su_that` (có test so từng số với nó trên cùng một mẫu Tầng 1), gộp k mẫu độc lập bằng √(Σ se²)/k. Là ước lượng (mục 15 khoản 8 đã nêu giới hạn của nó).
* **IC đứng riêng** của từng thành phần và của điểm cuối với nhãn, cùng sai số khối.

Lệnh (cùng khuôn mọi mức; ở thư mục gốc repo, 12 tiến trình trên máy 8 lõi vật lý / 16 lõi logic, Python 3.13.14):

```bash
./.venv/Scripts/python.exe -X utf8 tools/oracle_tang2_thi_truong_gia.py --luong 9001 --muc 2 --so-phien 5000 --so-mau 2 --chi-so-dau 401 --so-tien-trinh 12 --json
```

`--muc 0` · `0.5` · `1` · `2` lấy κ từ `docs/thi-truong-gia-hieu-chuan.json`; `--kappa` đặt thẳng (κ gấp đôi mức 2× = 0,0892, κ = 0,125, κ gấp bốn = 0,1783). Chi phí đo được (cả sáu lượt cộng lại **3.057 s ≈ 51 phút** tường, trong ngân sách 60 phút; mức NULL và 2× hai mẫu mỗi mức, còn lại một mẫu; ở 12 tiến trình cỡ 700–1.050 lần `_analyze` mỗi giây, tức 11–17 ms mỗi lần trên mỗi tiến trình; lượt chạy chậm hơn ở κ cao và có chạy cả test song song):

| mức | số mẫu × phiên × mã | lần `_analyze` | giây | dòng `data_quality` ≠ OK | chỉ số mẫu |
|---|---|---|---|---|---|
| NULL (κ = 0) | 2 × 5.000 × 60 | 600.000 | 596 | 0 | 301, 302 |
| 0,5× (κ = 0,0096) | 1 × 5.000 × 60 | 300.000 | 340 | 0 | 601 |
| 1× (κ = 0,0198) | 1 × 5.000 × 60 | 300.000 | 332 | 1.902 | 501 |
| 2× (κ = 0,0446) | 2 × 5.000 × 60 | 600.000 | 581 | 2.261 | 401, 402 |
| κ gấp 2 của 2× (0,0892) | 1 × 5.000 × 60 | 300.000 | 395 | 3.541 | 701 |
| κ = 0,125 | 1 × 5.000 × 60 | 300.000 | 393 | 16.205 | 901 |
| κ gấp 4 của 2× (0,1783) | 1 × 5.000 × 60 | 300.000 | 421 | 32.657 | 801 |

(Các mức 0,5× · 1× · 2× dùng κ của Lát 2, đã hiệu chuẩn ở Tầng 1; ba mức κ cao hơn là để xem đường cong, không phải mức nào của mục 4.4.)

### 19.3 Kết quả

ΔIC_true so với điểm đã ghi (± sai số Monte Carlo). G · Z · H in đậm:

| spec | NULL | 0,5× | 1× | 2× | κ gấp 2 | κ 0,125 | κ gấp 4 |
|---|---|---|---|---|---|---|---|
| `mono_trend_score` | +0,0014 ± 0,0032 | −0,0071 ± 0,0042 | −0,0033 ± 0,0038 | +0,0215 ± 0,0044 | +0,0646 ± 0,0054 | +0,0870 ± 0,0061 | +0,1044 ± 0,0045 |
| `mono_momentum_score` | +0,0017 ± 0,0054 | −0,0082 ± 0,0052 | −0,0413 ± 0,0075 | −0,1172 ± 0,0055 | −0,2816 ± 0,0104 | −0,3861 ± 0,0111 | −0,4997 ± 0,0123 |
| `mono_volume_score` **G** | +0,0025 ± 0,0047 | +0,0028 ± 0,0042 | +0,0098 ± 0,0065 | +0,0066 ± 0,0047 | +0,0199 ± 0,0045 | +0,0355 ± 0,0074 | +0,0662 ± 0,0072 |
| `mono_sr_score` | −0,0024 ± 0,0076 | −0,0196 ± 0,0085 | −0,0681 ± 0,0067 | −0,2076 ± 0,0074 | −0,4399 ± 0,0063 | −0,5726 ± 0,0157 | −0,6791 ± 0,0062 |
| `mono_risk_score` | −0,0100 ± 0,0064 | −0,0080 ± 0,0071 | −0,0309 ± 0,0113 | −0,0808 ± 0,0064 | −0,1393 ± 0,0094 | −0,1655 ± 0,0075 | −0,2063 ± 0,0156 |
| `bo_trend_score` | −0,0022 ± 0,0054 | −0,0028 ± 0,0059 | −0,0329 ± 0,0070 | −0,1242 ± 0,0068 | −0,2920 ± 0,0054 | −0,3919 ± 0,0119 | −0,4914 ± 0,0105 |
| `bo_momentum_score` | −0,0002 ± 0,0017 | +0,0007 ± 0,0026 | +0,0081 ± 0,0030 | +0,0304 ± 0,0030 | +0,0688 ± 0,0047 | +0,0889 ± 0,0049 | +0,1020 ± 0,0039 |
| `bo_volume_score` **H** | −0,0008 ± 0,0017 | −0,0039 ± 0,0025 | −0,0135 ± 0,0017 | −0,0215 ± 0,0017 | −0,0446 ± 0,0027 | −0,0601 ± 0,0031 | −0,0916 ± 0,0031 |
| `bo_sr_score` | +0,0014 ± 0,0028 | +0,0009 ± 0,0040 | +0,0048 ± 0,0041 | +0,0281 ± 0,0027 | +0,0636 ± 0,0032 | +0,0864 ± 0,0034 | +0,0958 ± 0,0034 |
| `bo_risk_score` | +0,0015 ± 0,0012 | +0,0006 ± 0,0016 | +0,0019 ± 0,0022 | +0,0077 ± 0,0014 | +0,0085 ± 0,0015 | +0,0079 ± 0,0014 | −0,0020 ± 0,0022 |
| `deu` | −0,0011 ± 0,0012 | +0,0027 ± 0,0013 | −0,0005 ± 0,0017 | −0,0097 ± 0,0008 | −0,0314 ± 0,0018 | −0,0443 ± 0,0023 | −0,0675 ± 0,0029 |
| `doi_cho_trend_sr` **Z** | −0,0019 ± 0,0026 | −0,0002 ± 0,0029 | −0,0143 ± 0,0027 | −0,0635 ± 0,0031 | −0,1626 ± 0,0034 | −0,2257 ± 0,0074 | −0,2976 ± 0,0051 |

IC của từng thành phần đứng riêng với nhãn, và của điểm đã ghi:

| thành phần | NULL | 0,5× | 1× | 2× | κ gấp 2 | κ 0,125 | κ gấp 4 |
|---|---|---|---|---|---|---|---|
| `trend_score` | +0,0015 ± 0,0055 | +0,0080 ± 0,0061 | +0,0380 ± 0,0065 | +0,1253 ± 0,0055 | +0,2660 ± 0,0040 | +0,3408 ± 0,0094 | +0,3967 ± 0,0067 |
| `momentum_score` | +0,0017 ± 0,0029 | +0,0070 ± 0,0042 | +0,0000 ± 0,0047 | −0,0134 ± 0,0055 | −0,0801 ± 0,0123 | −0,1324 ± 0,0109 | −0,2073 ± 0,0101 |
| `volume_score` | +0,0025 ± 0,0028 | +0,0180 ± 0,0032 | +0,0511 ± 0,0038 | +0,1103 ± 0,0024 | +0,2213 ± 0,0025 | +0,2892 ± 0,0023 | +0,3585 ± 0,0029 |
| `sr_score` | −0,0024 ± 0,0051 | −0,0044 ± 0,0063 | −0,0268 ± 0,0047 | −0,1038 ± 0,0049 | −0,2385 ± 0,0054 | −0,3189 ± 0,0098 | −0,3868 ± 0,0025 |
| `risk_score` | −0,0100 ± 0,0052 | +0,0072 ± 0,0071 | +0,0104 ± 0,0082 | +0,0230 ± 0,0067 | +0,0621 ± 0,0065 | +0,0882 ± 0,0102 | +0,0861 ± 0,0109 |
| điểm đã ghi | +0,0000 ± 0,0053 | +0,0152 ± 0,0045 | +0,0413 ± 0,0060 | +0,1038 ± 0,0045 | +0,2014 ± 0,0048 | +0,2537 ± 0,0076 | +0,2923 ± 0,0067 |

Đối chiếu với Tầng 1 (`docs/thi-truong-gia-hieu-chuan.json`, `oracle_kiem`, trung bình 24 mẫu; cùng κ):

| | NULL | 0,5× | 1× | 2× |
|---|---|---|---|---|
| G, Tầng 1 | −0,0014 ± 0,0012 | +0,0358 ± 0,0012 | +0,0733 ± 0,0011 | +0,1474 ± 0,0011 |
| G, Tầng 2 (bảng trên) | +0,0025 ± 0,0047 | +0,0028 ± 0,0042 | +0,0098 ± 0,0065 | +0,0066 ± 0,0047 |
| Z, Tầng 1 | +0,0004 ± 0,0003 | +0,0010 ± 0,0002 | +0,0016 ± 0,0002 | +0,0028 ± 0,0002 |
| Z, Tầng 2 | −0,0019 ± 0,0026 | −0,0002 ± 0,0029 | −0,0143 ± 0,0027 | −0,0635 ± 0,0031 |
| H, Tầng 1 | +0,0002 ± 0,0003 | −0,0119 ± 0,0003 | −0,0241 ± 0,0003 | −0,0482 ± 0,0003 |
| H, Tầng 2 | −0,0008 ± 0,0017 | −0,0039 ± 0,0025 | −0,0135 ± 0,0017 | −0,0215 ± 0,0017 |

### 19.4 Điều đọc ra

1. **Máy đo qua phép thử NULL (mục 4.5 (c)).** Ở κ = 0, cả 12 spec có |ΔIC_true| < 2 sai số (|z| lớn nhất 1,6, ở `mono_risk_score`; hai mẫu 5.000 phiên); `data_quality` = OK ở 600.000/600.000 dòng. Phép thử này đọc theo mẫu gộp, không theo từng thị trường (mục 15 khoản 8).
2. **ΔIC_true(G) ở 2× là +0,0066 ± 0,0047 — không khác 0 (z = 1,4) — so với đích Tầng 1 là 2 × MDE₈₀ = 0,1513: bằng 4,4% đích.** Hai mẫu cho +0,0136 và −0,0005. G cũng ≈ 0 ở 0,5× (+0,0028) và 1× (+0,0098), và chỉ lên +0,0355 ở κ = 0,125, +0,0662 ở κ gấp bốn của 2×. Hàng PT của mục 6 đòi "G `QUA` ở 2× ≥ 85/100"; từ đường probit của Tầng 1 (a = −2,4214; b = 43,1447, `mde80.probit`) một ΔIC_true bằng +0,0066 cho P(`QUA`) ≈ 1,6% (dải 99% của 100 thị trường: 0–6). **Đọc nguyên văn thì vế G của PT không thể đạt ở κ của Tầng 1; và nó không đạt vì G không còn mang lợi thế, không phải vì vòng sai.** Chú ý dự đoán này giả định nhiễu của phép so cặp ở Tầng 2 bằng ở Tầng 1: chưa đo — đó chính là cái PT sẽ kiểm.
3. **Vì sao (đã đo, cơ chế là suy luận):** điểm đã ghi ĐÃ đọc lợi thế. Ở 2× IC của điểm đã ghi là +0,1038, sát IC của `volume_score` (+0,1103) và của `trend_score` (+0,1253): cộng `volume_score` đứng một mình chỉ hơn điểm đã ghi 0,0066. `sr_score` mang lợi thế NGƯỢC dấu (−0,1038) và `momentum_score` ≈ 0 (−0,0134). Hợp với mục 18 khoản 10: kỳ vọng cài sẵn `κ·z/21` nằm trong giá và `z` bền (φ_z = 0,97), nên chỉ báo thuần giá đọc được nó. Chưa đo nguyên nhân của dấu âm ở `sr_score`.
4. **Z KHÔNG còn ≈ 0: −0,0635 ± 0,0031 ở 2× (Tầng 1: +0,0028).** `trend_score` và `sr_score` mang lợi thế ngược dấu (+0,1253 và −0,1038) nên đổi chỗ hai trọng số làm hỏng điểm. Từ đường probit Tầng 1, P(`THUA`) của Z ở 2× ≈ 62%, so với B3 ≤ 5% (B3 là tiêu chí Tầng 1, không phải PT; nhưng nếu Tầng 2 đo Z thì nó sẽ báo động).
5. **H vẫn âm nhưng nhỏ hơn một nửa Tầng 1:** −0,0215 ± 0,0017 (Tầng 1: −0,0482). B4 (H không bao giờ `QUA`) còn đứng; P(`THUA`) của H ≈ 6,8%.
6. **Trong họ F chỉ ba spec hơn điểm đã ghi ở 2×, và đều nhỏ:** `bo_momentum_score` +0,0304 ± 0,0030 · `bo_sr_score` +0,0281 ± 0,0027 · `mono_trend_score` +0,0215 ± 0,0044 (mỗi spec bỏ bớt một thành phần ngược dấu hay nhiễu); phần còn lại ≤ +0,0077. Lớn nhất = 0,40 × MDE₈₀ của Tầng 1 (0,0756). Chọn spec lớn nhất trong 11 sau khi nhìn kết quả có độ thiên lệch của cực đại (bất biến 7): `bo_momentum_score` và `bo_sr_score` khác nhau 0,0023, trong phạm vi một sai số.
7. **Đường cong theo κ của `bo_momentum_score`:** +0,0007 (0,5×) · +0,0081 (1×) · +0,0304 (2×) · +0,0688 (κ gấp 2) · +0,0889 (κ = 0,125) · +0,1020 (κ gấp 4). Nội suy tuyến tính giữa hai điểm kề: ΔIC_true = 0,0801 (mức mà đường probit Tầng 1 cho P(`QUA`) = 85%) ở κ ≈ 0,109; 2 × MDE₈₀ = 0,1513 chưa đạt ở κ lớn nhất đã đo (0,1783 → 0,1020 = 1,35 × MDE₈₀) và đường đang cong xuống.
8. **Phụ — cảnh báo đơn vị ở κ cao.** Số dòng `data_quality` ≠ OK tăng theo κ (bảng 19.2): giá một mã trôi qua 1.000 nghìn đồng trong mẫu 5.000 phiên thì `data_quality.detect_unit_multiplier` báo `UNIT_INCONSISTENT` (đo trên 42.900 cửa sổ của mẫu 401: 324 cửa sổ WARN, tất cả mã này). Điểm không đổi vì `master_agent.NO_VERDICT_QUALITY` chỉ chặn `FAILED` và `SYNTHETIC`, còn hệ số đơn vị chỉ đi vào giá cắt lỗ/chốt lời bằng VNĐ (`analysis_agents`) — đọc mã, KHÔNG chạy lại để kiểm. Ở mức NULL và 0,5× không có dòng nào.

### 19.5 Hệ quả cho mục 6 nếu không đổi gì, và các phương án

**Hàng nào chạm.** Chỉ hai mệnh đề ở Tầng 2: vế "G `QUA` ở 2× ≥ 85/100" của PT. Vế "báo động ở NULL ≤ 12/100" của PT không chạm (cả 12 spec có ΔIC_true = 0 ở NULL theo 19.4 điều 1). P1 · P2 · P4 không chạm. P3 (IC của `volume_score` với nhãn > 0 ở ≥ 90/100 thị trường 2×) không chạm: IC ở 2× là +0,1103 ± 0,0024 và Lát 4 đếm 6/6 thị trường dương. Các hàng A · A0 · B1–B4 · C1–C3 là Tầng 1; bộ ba G · Z · H của Tầng 1 vẫn đúng như đã hiệu chuẩn (Z ≈ 0, H < 0).

Ba phương án cho vế G của PT (cả ba đều chỉ đổi cách đọc ở Tầng 2, không đổi bộ sinh của Tầng 1 và không làm lại hiệu chuẩn Lát 2):

* **Phương án 1 — Bỏ vế G của PT.** PT chỉ còn "báo động ở NULL ≤ 12/100". Chứng cứ "vòng bắt được lợi thế" chỉ nằm ở Tầng 1 (tiêu chí A · B · C); Tầng 2 chỉ chứng minh ống dẫn (P1–P4) và máy báo động giả. Chi phí thêm: 0. Hệ quả: PT không còn chứng minh gì về lực ở Tầng 2.
* **Phương án 2 — Thay G bằng G′ lấy từ oracle Tầng 2, đọc theo đường cong.** G′ = `bo_momentum_score` (hoặc `bo_sr_score`, cùng cỡ). Vế PT đổi thành: số thị trường 2× mà G′ `QUA` nằm trong dải 99% nhị thức quanh P(`QUA` | ΔIC_true Tầng 2 của G′) đọc từ đường probit Tầng 1 — với +0,0304 là P ≈ 13,4%, dải 99% của 100 thị trường **5–23** (với `bo_sr_score`, 11,3%: 4–20). Không đổi κ. PT thành phép kiểm thật rằng nhiễu của phép so cặp ở Tầng 2 bằng Tầng 1 (cái dự đoán ở điều 2 giả định). Chi phí thêm: đo lại ΔIC_true(G′) trên dòng hạt khác 9001 (xem 19.6; cỡ 4–6 mẫu 5.000 phiên ≈ 25–35 phút ở 12 tiến trình). Mặt yếu: ở P ≈ 13% lực để phát hiện lệch nhỏ chỉ ở mức dải 5–23; và ngưỡng "≥ 85/100" được viết lại, cần người dùng ký.
* **Phương án 3 — Hiệu chuẩn lại κ riêng cho Tầng 2 để G′ đạt mức tương đương.** Giữ nguyên chữ "≥ 85/100" nhưng với G′ = `bo_momentum_score` ở κ ≈ 0,125 (ΔIC_true +0,0889 = 1,18 × MDE₈₀ của Tầng 1; đường probit cho P(`QUA`) ≈ 92%, dải 99% 85–98). Hoặc κ ≈ 0,109 cho P = 85% (sát ngưỡng, dải 99% rộng 75–93). **Không đạt được "2 × MDE₈₀ = 0,1513"** nếu giữ mô hình sinh hiện tại: κ gấp bốn của 2× mới cho 1,35 × MDE₈₀. Chi phí thêm: một mức κ mới ở Tầng 2 chưa từng được hiệu chuẩn (cần đo ΔIC_true bằng nhiều mẫu hơn), κ cỡ 2,8 lần mức 2× của Tầng 1 (kỳ vọng cài sẵn 2,8 lần; IC của `trend_score` +0,34 so với +0,125), 5,4% dòng `data_quality` ≠ OK (19.4 điều 8), và điều chủ yếu: ở P ≈ 92% đường cong gần bão hoà nên PT kiểm khớp tệ nhất ở đúng chỗ ấy.

(Phương án "không làm gì": vế G của PT chắc chắn trượt, cỡ 2/100 so với ≥ 85/100, và T6 ghi *TRƯỢT ở PT* dù vòng không sai — không nên.)

**Khuyến nghị: Phương án 2.** Lý do: (1) chỉ đổi cách đọc ở Tầng 2; mọi con số của Tầng 1 và hiệu chuẩn Lát 2 giữ nguyên hiệu lực; (2) giữ cho PT một nội dung thật — nó kiểm đúng giả định chưa ai đo (nhiễu của phép so cặp qua agent thật bằng Tầng 1) — thay vì bỏ nó (phương án 1) hay đẩy κ tới vùng chưa hiệu chuẩn và gần bão hoà (phương án 3); (3) vế NULL của PT giữ nguyên, nên tỷ lệ báo động giả ở Tầng 2 vẫn được đo; (4) đúng tinh thần mục 6 ("PT chỉ là kiểm khớp Tầng 1, KHÔNG phải chứng cứ riêng"): nó nhắc Lát 5 rằng kết luận T6 nằm ở Tầng 1. Nếu người dùng muốn rẻ nhất và chấp nhận Tầng 2 không chứng minh lực thì phương án 1. Hai việc đi kèm mọi phương án: chọn G′ (nếu có) TRƯỚC khi chạy Lát 5 và đo lại ΔIC_true của nó trên dòng hạt khác 9001; và khai Z′ · H′ (nếu Tầng 2 muốn đo báo động của chúng) từ bảng 19.3: Z′ ≈ 0 là `mono_volume_score` (+0,0066 ± 0,0047) hoặc `bo_risk_score` (+0,0077 ± 0,0014, nhỏ nhưng khác 0); H′ < 0 là `bo_volume_score` (−0,0215) hoặc `bo_trend_score` (−0,1242, hại mạnh).

### 19.6 Giới hạn của số đo

* **Dòng hạt 9001 là dòng thử.** Chọn G′ sau khi nhìn bảng này là chọn cực đại của 11 spec trên chính dữ liệu đã nhìn; ΔIC_true tham chiếu dùng cho Lát 5 phải đo lại ở dòng khác (đề nghị dòng 1, khối chỉ số mới ngoài sáu khối của Lát 2; dòng 2 · 3 · 4 · 5 vẫn chặn).
* **Mẫu nhỏ ở các mức giữa:** 0,5× · 1× · κ gấp 2 · κ 0,125 · κ gấp 4 chỉ một mẫu 5.000 phiên, nên sai số Monte Carlo của chúng là sai số khối (ước lượng); hai mức có hai mẫu (NULL · 2×) cho độ lệch giữa các mẫu cùng cỡ với sai số khối (ví dụ G ở 2×: sai số khối 0,0047, độ lệch giữa hai mẫu / √2 = 0,0071) — chỉ hai mẫu nên không kết luận được hơn.
* **Dự đoán P(`QUA`) từ đường probit Tầng 1 là giả định, không phải số đo Tầng 2.** MDE₈₀ = 0,0756 đo ở Tầng 1 (điểm sinh thẳng); nhiễu của phép so cặp qua điểm của agent thật có thể khác.
* **Cửa sổ trượt 855 dòng** là lựa chọn của BƯỚC này (lý do ở 19.2); chưa đo nó đổi ΔIC_true bao nhiêu so với lịch sử mở rộng.
* **Một họ spec** (F cộng Z, trọng số mặc định 0,25 · 0,25 · 0,20 · 0,15 · 0,15): điểm thật của `master_agent` dùng trọng số động theo chế độ và đè momentum, nên "điểm đã ghi" không phải tổ hợp tuyến tính mặc định; spec trong F chỉ là một họ ứng viên, không phải điểm tốt nhất có thể.

### 19.7 Chi phí của vòng trên Tầng 2 (việc (b), BƯỚC 293)

Lệnh (thư mục gốc repo, 12 tiến trình chấm điểm, rồi 12 bản của vòng cùng lúc; dòng hạt 9001, chỉ số 1, κ mức 2×; 60 mã × 605 phiên có quyết định + 250 khởi động; Python 3.13.14):

```bash
./.venv/Scripts/python.exe -X utf8 tools/chay_vong_tang2_thi_truong_gia.py --luong 9001 --chi-so 1 --muc 2 --so-tien-trinh 12 --song-song 12 --json
```

**Bộ nối không đổi nghĩa nào của vòng** (không phải dừng-và-báo): `vong_hoc_gia.chay_vong` vốn chỉ nhận dòng quyết định và bảng giá, và suy lịch khai/đọc từ ngày của dữ liệu. Bộ nối là hai dòng: dòng của `thi_truong_gia_tang2.dong_quyet_dinh`, và bảng giá đóng cửa của các phiên CÓ quyết định (bỏ 250 khởi động). Test dựng cả thị trường 60 × 605 bằng `_analyze` giả và chạy vòng nguyên: phiên khai 139 · 160 · 183, phiên đọc 412 · 433 · 456, tổng 605.

Hai lượt đo cùng lệnh (số thứ nhất / số thứ hai; chênh nhau do tải máy, nên hai số được giữ cả):

| phần | lượt 1 | lượt 2 |
|---|---|---|
| sinh khung OHLCV | 0,04 s | 0,03 s |
| chấm điểm 36.300 lần `_analyze`, 12 tiến trình | 47,0 s (≈ 770 lần/giây) | 32,4 s (≈ 1.120 lần/giây) |
| bộ nối dòng + giá | 0,73 s | 0,36 s |
| vòng như Lát 3 (bộ đề xuất cơ sở) | 0,56 s; không khai ứng viên nào | 0,35 s; không khai ứng viên nào |
| vòng ép ba ứng viên (cận trên; G · H · `deu` ép sẵn) | 2,85 s | 1,74 s |
| trong đó ba lần `cham` (2.000 hoán vị) | 0,75 · 0,95 · 1,03 s | 0,48 · 0,63 · 0,58 s |
| 12 bản của vòng ép ba cùng lúc | 8,44 s tường; mỗi bản 4,07–4,36 s | 4,41 s tường; mỗi bản 2,21–2,56 s |

Đọc: ở thị trường này bộ đề xuất cơ sở KHÔNG khai gì (không spec nào có Δ > 0 trên 104 phiên có nhãn đã nhìn), nên vòng đúng như Lát 3 chỉ tốn 0,35–0,56 s; vòng ép ba ứng viên (G · H · `deu`: `DANG CHAM` · `THUA` · `THUA`, không nâng cấp) chạy cả ba lần `cham`. Đó là MỘT thị trường, không phải tỷ lệ. Kiểm tiến-về-trước chỉ chạy khi có nâng cấp nên chưa đo ở Tầng 2; nó là một lần `ma_tran_cap` cộng hai `rho_hang` trên 126 phiên, nhỏ hơn một lần `cham` (ƯỚC LƯỢNG, chưa đo).

**Ngoại suy cho Lát 5 Tầng 2 (100 NULL + 100 ở 2× = 200 thị trường), cận trên:**

* Vòng: ≤ 4,4 s mỗi thị trường khi 12 bản chạy cùng lúc → 200 × 4,4 / 12 ≈ 73 s; kể cả sinh và bộ nối khoảng 1–2 phút.
* Chấm điểm: 200 × 36.300 = 7.260.000 lần `_analyze` (khoản 4 mục 18 tính 7.128.000 ở 594 phiên). Ở 805 lần/giây của khoản 4: 2,5 giờ; ở 770–1.120 lần/giây của hai lượt đo này: 1,8–2,6 giờ.
* **Tổng ≈ 2,6 giờ (cận trên; khoản 4 nói 2,5 giờ chỉ riêng chấm điểm).** Chi phí của vòng cộng thêm khoảng một phút và không đổi ước lượng. Không gồm oracle tham chiếu của 19.6 (≈ 5–7 phút mỗi mẫu 5.000 phiên ở 12 tiến trình).

### 19.8 Quyết định của người dùng (21/11/2026) và LỜI KHAI TRƯỚC cho lượt đo G′ (BƯỚC 294)

**Quyết định.** Người dùng đã được nêu ba phương án của mục 19.5, kèm khuyến nghị phương án 2, và trả lời nguyên văn: *"làm theo đề xuất của bạn đi, phương án nào tốt nhất thì làm"* (21/11/2026). **Hiệu lực = phương án 2**: ở Tầng 2, thay G bằng G′ = `bo_momentum_score`; vế G của hàng PT đọc là *"số thị trường `QUA` nằm trong dải 99% nhị thức quanh dự đoán của đường cong Tầng 1"*; κ và hiệu chuẩn Lát 2 KHÔNG đổi; ΔIC_true tham chiếu của G′ phải đo lại ở dòng hạt khác 9001.

Mọi điều dưới đây được KHAI trong một commit riêng, TRƯỚC khi dòng hạt 1 sinh một mẫu Tầng 2 nào. Thời điểm commit là bằng chứng thứ tự; sửa một điều dưới đây sau khi đã nhìn số là sửa đặc tả bằng commit riêng và (mục 6, "Quy tắc đọc") đổi dòng hạt.

1. **G′ = `bo_momentum_score`, cố định.** Nó được chọn ở dòng 9001 (ΔIC_true +0,0304 ± 0,0030 ở 2×, mục 19.3). KHÔNG đổi sang `bo_sr_score` hay spec nào khác dù số mới ra thế nào (đổi sau khi nhìn là chọn cực đại, bất biến 7).
2. **Dòng tham chiếu = dòng hạt 1** (dòng hiệu chuẩn; mục 4.8 giao cho dòng 1 việc hiệu chuẩn, và ΔIC_true tham chiếu là một đại lượng hiệu chuẩn). Dòng 1 qua cửa `kiem_luong` sẵn có; cửa ấy KHÔNG đổi. **Hạt `[1, chi_so, 2]`** (hạt thứ ba 2 = `HAT_ORACLE_2`), chỉ số: **600001 · 600002 ở mức 2×; 600101 · 600102 ở NULL.** Vì sao các số ấy mới: Lát 2 chia chỉ số dòng 1 thành các khối 0, 100.000, 200.000, 300.000, 400.000 và 900.000 (`CHI_SO_GOC` trong `tools/hieu_chuan_thi_truong_gia.py`); khối 500.000–899.999 chưa có vai trò nào; oracle Tầng 2 của BƯỚC 293 chỉ chạy ở dòng 9001; và `git grep -n "600001\|600002\|600101\|600102"` ở cây trước commit này không trả dòng nào. Các chỉ số này KHÔNG dùng lại cho thứ gì khác ở dòng 1.
3. **Lệnh (cùng công cụ và cùng thiết lập với mục 19.2):**

```bash
./.venv/Scripts/python.exe -X utf8 tools/oracle_tang2_thi_truong_gia.py --luong 1 --muc 2 --so-phien 5000 --so-mau 2 --chi-so-dau 600001 --so-tien-trinh 12 --json
./.venv/Scripts/python.exe -X utf8 tools/oracle_tang2_thi_truong_gia.py --luong 1 --muc 0 --so-phien 5000 --so-mau 2 --chi-so-dau 600101 --so-tien-trinh 12 --json
```

   Hai mẫu 5.000 phiên × 60 mã, cửa sổ trượt 855 dòng mặc định của công cụ. Ngân sách ước lượng cỡ 20 phút tường (hai lượt 2 × 5.000 × 60 ở 581–596 s của mục 19.2). Mỗi lượt chạy MỘT lần, không chạy lại cho "đẹp hơn".
4. **Công thức dải** (cài trong `tools/dai_pt_tang2_thi_truong_gia.py`, đã có test và đột biến, commit cùng lời khai này): `p = Φ(a + b · ΔIC_true(G′))` với `a`, `b` là `mde80.probit` của `docs/thi-truong-gia-hieu-chuan.json` (Tầng 1), ΔIC_true(G′) là **điểm ước ở 2× đo ở dòng 1**; dải 99% hai phía của Nhị thức(100, p): `thấp` = k NHỎ NHẤT có P(X ≤ k) ≥ 0,005, `cao` = k NHỎ NHẤT có P(X ≤ k) ≥ 0,995. Dụng cụ tái lập đúng ba số của mục 19.5 cho dòng 9001 (`--delta 0.0304` → 13,4%, 5–23; `--delta 0.0281` → 11,3%, 4–20; `--delta 0.0066` → 1,6%, 0–6). Sai số Monte Carlo của ΔIC_true KHÔNG đi vào dải; dải hẹp hơn độ bất định thật, nên PT chỉ bắt được lệch lớn (đã nói ở 19.5). Dải ở ΔIC ± 1 sai số chỉ được in để tham khảo.
5. **Điều kiện DỪNG (báo cáo, không đi vòng):**
   * (S1) ΔIC_true(G′) ở 2×, dòng 1, không lớn hơn 0 quá 2 sai số Monte Carlo (z ≤ 2): G′ không mang lợi thế đo được.
   * (S2) ΔIC_true(G′) ở 2×, dòng 1, lệch khỏi +0,0304 (dòng 9001, sai số 0,0030) quá 3 sai số gộp √(se₁² + 0,0030²).
   * (S3) cận dưới của dải bằng 0.
   * (S4) phép thử NULL của mục 4.5 (c) rớt: ở κ = 0, MỘT spec trong 12 có |ΔIC_true| ≥ 2 sai số (mẫu gộp hai mẫu, đúng cách đọc của mục 19.4 điều 1; công cụ in dòng `spec có |ΔIC_true| ≥ 2 sai số (mẫu gộp)`), hoặc `data_quality` ≠ OK ở bất kỳ dòng nào.
   * (S5) bất kỳ bước nào cần một dòng hạt ngoài {1, 9001}.

   Dừng thì không sửa ngưỡng, không đổi G′, không chạy thêm cho tới khi đạt: ghi kết quả nguyên văn, và người dùng quyết.
6. **Việc làm tiếp nếu không dừng:** ghi số đo vào `docs/thi-truong-gia-g-phay.json`; tính dải bằng lệnh của khoản 4 với ΔIC_true đo được; viết lại MỘT vế của hàng PT ở mục 6 (G → G′, "≥ 85/100" → dải). Vế NULL "≤ 12/100", R = 100, và mọi hàng khác của mục 6 giữ nguyên.
7. **Không làm ở BƯỚC này:** Lát 5 (không tỷ lệ PT hay P3 nào trên 100 thị trường, không dòng 2–5), κ, tiêu chí A · B · C, `docs/TIEU-CHI-DOC-TRUOC.md` (việc của Lát 5, kèm một câu hỏi thật tới sổ tay), đường thật. **Còn để ngỏ cho Lát 5:** nếu Tầng 2 chạy bộ ba K = 3 thì Z′ · H′ khai thế nào (mục 19.5, hai việc đi kèm); đường probit của dải đã tính ở K = 3 nên dải chỉ đúng khi thị trường Tầng 2 cũng khai đủ ba ứng viên.

### 19.9 Số đo ở dòng hạt 1 và dải của PT (BƯỚC 294, 21/11/2026) — không điều kiện DỪNG nào bị chạm

Hai lượt chạy ĐÚNG hai lệnh của 19.8 khoản 3, mỗi lượt MỘT lần, sau commit khai trước `981aa25` (`git log -1 --format='%H %cI' 981aa25`: 2026-11-21T14:53:58+07:00; lượt 2× bắt đầu 14:54:10). Bản ghi đầy đủ (12 spec, IC đứng riêng, số liệu NULL, thời gian, môi trường): `docs/thi-truong-gia-g-phay.json`; test: `tests/test_pt_g_phay_tang2.py`. Máy 16 lõi logic, 12 tiến trình, Python 3.13.14.

| | dòng 1, mức 2× (chỉ số 600001 · 600002) | dòng 1, NULL (chỉ số 600101 · 600102) | tham chiếu dòng 9001, 2× (mục 19.3) |
|---|---|---|---|
| `bo_momentum_score` (G′) | **+0,0331 ± 0,0029** | +0,0008 ± 0,0020 | +0,0304 ± 0,0030 |
| thời gian một lượt (hai mẫu, 600.000 lần `_analyze`) | 542 s | 545 s | 581 s |
| dòng `data_quality` ≠ OK | 1.697 | 0 | 2.261 |

**Đối chiếu từng điều kiện DỪNG của 19.8 khoản 5:**
* (S1) ΔIC_true(G′) = +0,0331 ± 0,0029: z = 11,3 so với 0 (> 2) → không chạm.
* (S2) lệch so với dòng 9001 = +0,0027; sai số gộp √(0,0029² + 0,0030²) = 0,0042; = 0,63 sai số gộp (≤ 3) → không chạm.
* (S3) dải tính ra 7–26, cận dưới 7 ≠ 0 → không chạm.
* (S4) NULL: cả 12 spec |ΔIC_true| < 2 sai số (|z| lớn nhất 1,52, ở `bo_volume_score`; công cụ in `spec có |ΔIC_true| ≥ 2 sai số (mẫu gộp): không có`); `data_quality` = OK ở 600.000/600.000 dòng → không chạm.
* (S5) chỉ dùng dòng 1 và đọc số của dòng 9001 đã có; không dòng hạt nào khác → không chạm.

**Dải của PT.** Lệnh: `./.venv/Scripts/python.exe -X utf8 tools/dai_pt_tang2_thi_truong_gia.py --delta 0.033073041827246956 --se 0.0029307104631540676` → `p = Φ(−2,421383 + 43,144698 × 0,033073) = 0,1600`; dải 99% của 100 thị trường **7–26**. Hàng PT của mục 6 đọc: *G′ `QUA` ở 2× nằm trong [7 ; 26]/100*. Tham khảo, KHÔNG phải tiêu chí (sai số của ΔIC_true không đi vào dải): ở ΔIC − 1 sai số P = 13,1%, dải 5–22; ở ΔIC + 1 sai số P = 19,3%, dải 10–30. Dải dựng bằng ΔIC của dòng 9001 sẽ là 5–23 (mục 19.5); hai dải gối nhau gần hết.

**Điều đọc ra, và điều chưa kiểm:**
1. **G′ mang lợi thế ở dòng khác** (z = 11,3), cùng cỡ dòng 9001. Giá trị ở dòng 1 hơi LỚN hơn (+0,0331 so với +0,0304), tức không có dấu hiệu "lời nguyền người thắng": G′ được chọn là cực đại của 11 spec trên dòng 9001, và ở một mẫu độc lập nó không co lại.
2. **Hai spec khác đo ở dòng 1 (không dùng, không đổi G′):** `bo_sr_score` +0,0347 ± 0,0030 (ở dòng 9001 +0,0281), lớn hơn G′ 0,0016 — trong phạm vi một sai số, đúng như mục 19.4 điều 6 đã nói về hai spec này; G′ đã được cố định trước (19.8 khoản 1) nên KHÔNG đổi. `mono_volume_score` (G cũ) +0,0199 ± 0,0033 ở dòng 1 so với +0,0066 ± 0,0047 ở dòng 9001 (chênh 2,3 sai số gộp): vẫn chỉ bằng 13% đích 0,1513 của Tầng 1, nên kết luận của mục 19.4 điều 2 (G cũ không đạt "≥ 85/100" ở Tầng 2) không đổi, nhưng ΔIC_true(G) ở Tầng 2 không chắc ở mức +0,0066.
3. **Z và H ở dòng 1:** `doi_cho_trend_sr` −0,0647 ± 0,0029 (dòng 9001: −0,0635); `bo_volume_score` −0,0234 ± 0,0021 (−0,0215). IC đứng riêng ở 2×: trend +0,1236 · volume +0,1177 · sr −0,1118 · momentum −0,0204 · risk +0,0350 · điểm đã ghi +0,0978. Cơ chế của mục 19.4 điều 3 (điểm đã ghi đã đọc lợi thế qua giá) lặp lại ở dòng thứ hai.
4. **Dải chỉ dựa trên một điểm ước.** PT ở Lát 5 chỉ kiểm được rằng số `QUA` không lệch khỏi 16% đến mức vượt dải; ΔIC_true(G′) có bất định ±0,0029 (P từ 13% tới 19%), và dự đoán P(`QUA`) từ đường probit Tầng 1 vẫn là GIẢ ĐỊNH về nhiễu của phép so cặp qua agent thật (19.6) — đó chính là cái PT đo.
5. **Chưa đổi gì khác:** κ, hiệu chuẩn Lát 2, tiêu chí A · B · C, `docs/TIEU-CHI-DOC-TRUOC.md`, đường thật, và mọi hàng khác của mục 6. Ghi sổ tay: `docs/soat-notebooklm.json` mục BƯỚC 294. Chưa chạy một tỷ lệ PT hay P3 nào (Lát 5).

## 20. Ghi chú Lát 5 (b) (BƯỚC 296, 25/11/2026) — kết cục của lượt chạy chính thức: TRƯỢT ở A0 và PT

Dòng hạt 2 · 3 · 4 chạy MỘT lần bằng đúng lệnh của ĐO 37 (`docs/TIEU-CHI-DOC-TRUOC.md`); `--ket-cuc` in **KẾT CỤC: TRƯỢT ở A0, PT**. **A0 = 421/1000 (ngưỡng ≤ 317)** và **PT: G′ `QUA` 41/100, ngoài dải [7 ; 26]** (báo động NULL 7 ≤ 12 ĐẠT). A · B1–B4 · C1–C3 · P1–P4 ĐẠT. Không hạ ngưỡng, không đổi bộ sinh, không đổi mục 6 (mục 6, *Kết cục*): theo ĐO 37, sửa bộ phận sai rồi chạy lại trên dòng hạt MỚI. Bảng nguyên văn, ba khối kết quả (*Đã khai* · *Báo kèm* · *Sau khi nhìn*), thời gian từng dòng, lần ngắt và chạy tiếp của dòng 4: `docs/STATE.md` BƯỚC 296. Bản ghi: `docs/thi-truong-gia-ket-qua.json`.

Giả thuyết SAU KHI NHÌN (chưa kiểm trên dòng hạt mới): sd của ΔIC quan sát phụ thuộc spec và tầng, mà A0 (mức ngẫu nhiên 3/11) và dải PT (đường probit của G = `mono_volume_score` ở Tầng 1, áp cho G′ = `bo_momentum_score` ở Tầng 2) đều coi nó như nhau. Số đo ở `docs/STATE.md` BƯỚC 296 mục D; mục 19.6 và 19.9 khoản 4 đã khai trước chỗ giả định này.

## 21. Đặc tả sửa C4 — khai trước (ĐO 38 sẽ ký ở BƯỚC 303)

**Trạng thái:** KHAI TRƯỚC, BƯỚC 300 (25/11/2026), commit docs-only đứng TRƯỚC mọi lượt hiệu chuẩn và mọi mã của bản sửa. Nguồn: đặc tả nháp `DAC-TA-SUA-C4.md` của phiên con `c4sua` (ngoài repo), người dùng 25/11/2026: *"ok tiếp tục làm theo đề xuất của bạn"* (hướng sửa) và *"duyệt cả 4"* (bốn câu của đặc tả: A0 đo ở dòng hiệu chuẩn · PT vẫn PHÁN · M1 PHÁN ở ≤ 50/1.000 · P2 giữ cả 200 thị trường). Đánh số (quyết định của leader, không phải của người dùng): **ĐO 38 = sửa C4**, ĐO 39 = Dow phần 2; ý 3A không mang số ĐO.

Mục này KHÔNG viết lại mục 5.1, mục 6 hay mục 20 (lịch sử giữ nguyên: ĐO 37 chạy bằng chúng). Nhãn của từng con số: **Đã khai** = quy tắc/ngưỡng đặt trước khi có số đo của bản sửa; **Báo kèm** = in ra, không phán; **Sau khi nhìn** = số tính SAU khi đã nhìn dữ liệu của lỗi, chỉ để hiểu, không hiệu chuẩn; **ƯỚC LƯỢNG** = chưa có lệnh chạy trong repo.

### 21.1 Bộ đề xuất chuẩn hoá (thay mục 5.1 cho ĐO 38; mã: BƯỚC 300)

**Công thức (Đã khai).** Với mỗi spec s của họ F (11 spec) trên cửa sổ đã nhìn (104 phiên có nhãn, như mục 17 khoản 1): Δₛ = IC(C) − IC(B) như hôm nay, và **zₛ = (Δₛ − μₛ) / σₛ**, trong đó μₛ, σₛ là trung bình và độ lệch chuẩn CHÍNH XÁC của thống kê hoán vị mã mà `cham_bong.so_cap` dùng: null(π) = Σⱼ Aⱼ,π(j), với A = (RCᵀRY)/m_c − (RBᵀRY)/m_b (RB, RC, RY là hạng giữa của B, C, Y; m_b, m_c là chuẩn hoá của `so_cap`). Dạng đóng (Hoeffding 1951): **μ = ΣA / M** và **σ² = Σᵢⱼ(Aᵢⱼ − Āᵢ· − Ā·ⱼ + Ā··)² / (M − 1)** (M = số mã; mẫu số M − 1, như độ lệch chuẩn của một phân phối hoán vị đều, KHÔNG phải M). Không RNG, không hạt. Dữ liệu duy nhất là B, C, Y của cửa sổ đã nhìn: G7 giữ nguyên.

**Luật khai (Đã khai).** Xếp z GIẢM; hoà (sau làm tròn z đến **12 chữ số thập phân**, để khác biệt dấu chấm động không quyết định thứ hạng) theo tên spec; khai tối đa 3 spec có **z > 0 VÀ Δ > 0**. Spec phương sai 0 (m_b·m_c = 0 hoặc σ = 0; `so_cap` trả z = 0, p = 1) có z = 0 và KHÔNG bao giờ được khai, dù Δ = −IC(B) có thể > 0 (kẽ hở của luật thô). Đầu ra giữ khoá cũ và thêm `z`, `sd_null`.

**Số đã thấy (Sau khi nhìn; dòng thử 9001, chỉ số 1.000.001–1.008.000, 8.000 thị trường NULL Tầng 1; lệnh của phiên `c4sua`: `mp_a0.py --so 8000 --tien-trinh 3 --dau 1000001`):** bộ THÔ chọn G (`mono_volume_score`) ở 40,51%; bộ chuẩn hoá chọn G ở **26,77%** (SE 0,50), so với 3/11 = 27,27%. BƯỚC 300 tái lập con số 26,77% bằng MÃ THẬT trên cùng dòng thử; kết quả ghi ở `docs/STATE.md` BƯỚC 300, vẫn mang nhãn Sau khi nhìn.

### 21.2 A0 — mức ngẫu nhiên đo ở dòng hiệu chuẩn (phương án (B); Đã khai)

Ngưỡng A0 = `binom.ppf(0,999; 1000; p̂)`, trong đó p̂ là tỷ lệ G được bộ đề xuất chuẩn hoá chọn ở thị trường NULL Tầng 1 của **dòng 1, chỉ số ≥ 1.100.001** (khối chưa dùng: `CHI_SO_GOC` của dụng cụ hiệu chuẩn Lát 2 dừng ở 900.000; oracle Tầng 2 của G′ dùng 600.001–2 và 600.101–2), **N ≥ 20.000** thị trường, SE(p̂) = √(p̂(1 − p̂)/N). Luật ngưỡng ("phân vị 99,9% của nhị thức quanh mức ngẫu nhiên") đứng nguyên; chỉ mức ngẫu nhiên, vốn là giả định sai của ĐO 37 (đều 3/11), được thay bằng giá trị ĐO ở dòng tách khỏi dòng chấm. **p̂ đọc MỘT lần, không lặp để chọn.**

**Điều kiện DỪNG (Đã khai):** nếu **p̂ + 3·SE ≥ 0,3** thì DỪNG và báo người dùng: một bộ đề xuất xa 3/11 đến mức ấy nghĩa là bộ sinh hay luật khai đã lệch, không phải chỗ chỉnh ngưỡng. Không hạ, không nới tay.

Ví dụ minh hoạ (ƯỚC LƯỢNG, KHÔNG phải ngưỡng; lệnh: `./.venv/Scripts/python.exe -X utf8 -c "from scipy.stats import binom; print(binom.ppf(.999,1000,.2677), binom.ppf(.999,1000,3/11))"` → `312.0 317.0`): với p̂ = 0,2677 thì ngưỡng 312 (so với 317 của ĐO 37); chiều ra cho thấy bản sửa không thiên về dễ đạt.

### 21.3 PT — dải đo ở chính Tầng 2 (Đã khai)

Vế G′ của PT: G′ = `bo_momentum_score` (KHÔNG đổi sang `bo_sr_score`), κ mức 2×, Tầng 2, **dòng 1, chỉ số 1.200.001–1.200.200 (n_cal = 200)**. **k = số thị trường QUA theo đúng luật `trang_thai` (p < 0,05/3 và Δ > 0).** p ~ Beta(k + ½, n_cal − k + ½); số QUA của R = 100 thị trường chính thức ~ **Beta-nhị thức(100; k + ½; n_cal − k + ½)**; **dải 99% = [k nhỏ nhất có P(X ≤ k) ≥ 0,005 ; k nhỏ nhất có P(X ≤ k) ≥ 0,995]**. Vế NULL "báo động ≤ 12/100" GIỮ NGUYÊN. PT vẫn được PHÁN. Đo MỘT lần.

**Điều kiện DỪNG (Đã khai):** k / n_cal ngoài [0,2 ; 0,7], hoặc `data_quality` ≠ OK ở bất kỳ dòng nào → báo, không chạy lại cho đẹp. Dòng 4 (đã nhìn) KHÔNG dùng để hiệu chuẩn (tuần hoàn).

Ví dụ (ƯỚC LƯỢNG; số giả định, không phải đo; lệnh dùng `scipy.stats.betabinom(100, k + .5, n_cal − k + .5)` với k = 84, n_cal = 200): dải [27 ; 58]. Dạng giải tích (m, s, σ̄) chỉ để ĐỌC, không phán.

**Báo kèm (không phán):** Δ và p của G (`mono_volume_score`) ở cùng các thị trường Tầng 2; bảng 2×2 {G, G′} × {Tầng 1, Tầng 2} của (m, s, σ̄, P) với 1.000 thị trường Tầng 1 mức 2× ở dòng 1, chỉ số ≥ 1.300.001; sd của z NULL ở Tầng 2 (so [0,8 ; 1,25]); tỷ lệ chọn từng spec của bộ chuẩn hoá và χ² so với đều.

**Thật thà về sức PT:** hiệu chuẩn ở CÙNG spec, tầng và κ làm PT thành phép kiểm lặp lại và hiệu chuẩn p-value của bước xác nhận ở Tầng 2 (hai dòng hạt khác nhau cho cùng tỷ lệ QUA, và tỷ lệ ấy đúng cái p-value danh nghĩa ngụ ý). Nó bắt lỗi cấp-dòng-hạt hay không tất định; KHÔNG bắt lỗi hệ thống của chính Tầng 2.

### 21.4 NULL có nhớ (NULL-M) và tiêu chí M1 (Đã khai)

Thị trường NULL-M (Tầng 1, bộ sinh MỚI do L2 dựng; `_sinh_loi` giữ nguyên từng bit): thêm nhân tố ẩn NGÀNH dₛ(t) AR(1) với **φ_d = 0,97**, vào lợi nhuận qua κ_d·d/21 (kiểu `z`) và vào cả năm thành phần điểm với cùng hệ số; κ_d chọn sao cho IC(điểm đã ghi) ≈ 0,10 (cỡ đo ở Tầng 2 mức 2×). φ_d 0,97 là KHAI, chưa đo trên giá thật.

**M1 (PHÁN):** trên **1.000** thị trường NULL-M, Tầng 1, bộ ba G · Z · H (K = 3) và oracle tính ΔIC_true: *xác nhận nhầm* = ứng viên bị `QUA` mà ΔIC_true ≤ 0. ĐẠT nếu số thị trường có ≥ 1 xác nhận nhầm **≤ 50/1.000** (danh nghĩa một phía ≈ 2,5%; lệnh: `./.venv/Scripts/python.exe -X utf8 -c "from scipy.stats import binom; print(1-binom.cdf(50,1000,.025), binom.cdf(50,1000,.05))"` → 2,37e-06 và 0,5375: sai-trượt ≈ 0 nếu đúng; nếu thật 5% thì qua 54%). M1 là tiêu chí MỚI ngoài văn bản T6. **Báo kèm:** tỷ lệ báo động hai phía ở bộ ba (so B1 ≤ 75), sd và trung bình của z, tỷ lệ chuỗi nâng cấp ma (so C3). Trượt M1 nghĩa là bước xác nhận (hoán vị MÃ, không tách theo ngành) vỡ khi điểm và nhãn cùng đọc một nhân tố ngành bền: sửa PHÉP KIỂM, không hạ 50.

### 21.5 Dòng hạt và chỉ số (Đã khai)

Giữ NGUYÊN mọi tiêu chí còn lại của bảng ĐO 37 (A, B1–B4, C1–C3, P1–P4, vế NULL của PT, ba tiêu chí KHÔNG ĐỌC ĐƯỢC, G′ = `bo_momentum_score`, R mỗi ô). Dòng hạt MỚI: **6** Tầng 1 có lợi thế 0,5× · 1× · 2×, mỗi ô 400; **7** Tầng 1 NULL 1.000; **8** Tầng 2 NULL 100 + 2× 100 (P2 trên cả 200); **9** Tầng 1 NULL-M 1.000; **10** chẩn đoán SAU khi nhìn, chặn vĩnh viễn (như dòng 5). Hiệu chuẩn ở dòng 1: A0 chỉ số ≥ 1.100.001 (N ≥ 20.000), PT chỉ số 1.200.001–1.200.200, bảng 2×2 chỉ số ≥ 1.300.001. Dòng 2 · 3 · 4 · 5 và dòng 9001 ngoài các chỉ số đã nêu ở 21.1 KHÔNG dùng để hiệu chuẩn. **Mỗi phép đọc là MỘT LẦN** (p̂, k, kết cục dòng 6–9): không đọc lại để chọn.

Nhãn từ ĐO 38: A0 · PT · M1 = Đã khai; bảng 2×2, χ² của spec, sd z NULL = Báo kèm; mọi con số phiên 296 và phiên `c4sua` đã nói = Sau khi nhìn. Chi phí lượt chạy ≈ 10 giờ máy (ƯỚC LƯỢNG từ thời gian thật của BƯỚC 296: dòng 8 chiếm ≈ 6,2 giờ). Lát cắt: L1 (BƯỚC 300, bộ đề xuất) · L2 (BƯỚC 301, NULL-M và dụng cụ hiệu chuẩn) · ký ĐO 38 ở BƯỚC 303 (BƯỚC 302 là lượt soát định kỳ 19, việc khác) · lượt chạy ở BƯỚC 304.

### 21.6 Thủ tục κ_d của NULL-M và bốn lệnh hiệu chuẩn (BƯỚC 301; Đã khai, viết TRƯỚC mọi lượt chạy dòng 1)

Dụng cụ: `tools/hieu_chuan_sua_c4.py` (chỉ dòng hạt 1 và dòng thử 9001; mọi dòng 2–10 nổ). Bộ sinh NULL-M: hàm `_sinh_loi_m` trong `thi_truong_gia.py`; oracle riêng của NULL-M là `tinh_su_that_m` (oracle cũ không dùng được: nó rút mẫu dài không có nhân tố ngành).

**Thủ tục `kd` (leader chấp nhận 25/11/2026; mã thoát 4 khi thất bại):**
1. b_d = `HE_SO_D` = **0,5 CỐ ĐỊNH**, đúng hệ số `HE_SO_Z` đã khai cho z: không một số mới để chọn theo kết quả. φ_d = 0,97. Tiềm ẩn mới của mỗi thành phần = √(1 − b_d²) · tiềm ẩn cũ + b_d · d(t) (phương sai vẫn 1); z có κ = 0 (vẫn nằm trong volume_score như cũ).
2. Đại lượng đo: IC(điểm đã ghi) = hạng, gộp mọi phiên có nhãn × 60 mã, trên mẫu dài 5.000 phiên (`SO_PHIEN_SU_THAT`), hạt `[1, chỉ số, 301]`; mục tiêu **0,10** (cỡ đo ở Tầng 2 mức 2×, 0,098–0,104).
3. Lưới κ_d CỐ ĐỊNH, 9 điểm: 0,012 · 0,014 · … · 0,028 (bước 0,002). Không đổi sau khi chạy.
4. Khối chỉ số (dòng 1; `git grep` ở BƯỚC 301: không số nào trong 1.100.001–1.409.100 từng xuất hiện trong mã hay tài liệu): `1.400.001 + j·1.000 + t`, j = điểm lưới 0–8, t = 0…49 (khối TÌM, 50 mẫu mỗi điểm); khối KIỂM j = 9: 100 mẫu tại κ_d đã chọn. Cao nhất 1.409.100.
5. Luật chọn: IC_j = trung bình 50 mẫu; chọn κ_d có |IC_j − 0,10| nhỏ nhất (hoà → κ_d nhỏ hơn); không làm tròn, không nội suy.
6. **THẤT BẠI → DỪNG, báo, KHÔNG chọn lại, KHÔNG đổi lưới:** (a) lưới không kẹp 0,10; (b) IC giảm theo κ_d quá 2 sai số chuẩn giữa hai điểm liền; (c) điểm gần nhất nằm ở RÌA lưới; (d) |IC_chọn − 0,10| > 0,010 (±10% mục tiêu, như `DUNG_SAI_MUC` của Lát 2); (e) khối KIỂM: trung bình 100 mẫu ngoài [0,090 ; 0,110].
7. Chỉ khi không thất bại, κ_d trong khối `kd` được dùng cho thị trường NULL-M của dòng 9.

**Bốn việc, mỗi việc MỘT khối trong `docs/thi-truong-gia-hieu-chuan-do38.json`, đọc MỘT lần** (khối đã XONG không chạy lại, không ghi đè; khối đang dở chỉ chạy tiếp bằng `--tiep-tuc` và chỉ cùng mã băm git; cây git phải SẠCH; log ghi RA NGOÀI repo; `--dau` và `--so` ở dòng 1 phải là giá trị đã khai). Thứ tự kd → a0 → t1 → pt:

| việc | khối chỉ số (dòng 1) | nội dung |
|---|---|---|
| kd | 1.400.001–1.409.100 | κ_d theo 21.6 |
| a0 | 1.100.001–1.120.000 (N = 20.000) | p̂ của bộ đề xuất THẬT, ngưỡng `binom.ppf(0,999; 1000; p̂)`, luật DỪNG p̂ + 3·SE ≥ 0,3 (21.2); TỪ CHỐI chạy nếu đầu ra bộ đề xuất thiếu `z` |
| t1 | 1.300.001–1.301.000 | 1.000 thị trường Tầng 1 mức 2× cho G và G′ (bảng 2×2, Báo kèm) |
| pt | 1.200.001–1.200.200 (n_cal = 200) | k, dải Beta-nhị thức và luật DỪNG (21.3), chỉ chấm điểm và `cx.cham`; ghi thêm Δ, p của G và bộ ba cho bảng 2×2 |

```
./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec kd --luong 1 --so-tien-trinh 12
./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec a0 --luong 1 --so-tien-trinh 12
./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec t1 --luong 1 --so-tien-trinh 12
./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec pt --luong 1 --so-tien-trinh 12
```

Chạy tiếp: đúng lệnh ấy thêm `--tiep-tuc`. Đọc kết quả đã ghi: `--doc`. Mã thoát: 0 xong · 2 lỗi đối số · 3 cửa từ chối · 4 xong nhưng LUẬT DỪNG báo.

**Số thử (dòng thử 9001; nhãn THỬ, không phải số đo của bản sửa; chạy ở BƯỚC 301 bằng dụng cụ này):** kd chọn κ_d ≈ 0,018 ở 20 mẫu mỗi điểm lưới, IC lưới từ 0,066 đến 0,145 đơn điệu. Thời gian một tiến trình, ƯỚC LƯỢNG khi nhân lên: kd 0,2 s mỗi mẫu; a0 0,52 s mỗi thị trường (thay `z` giả vì lúc đó chưa có bộ chuẩn hoá); t1 1,5 s mỗi thị trường; pt 342 s mỗi thị trường (chạy cùng việc khác).

### 21.7 Hai quyết định của người dùng 26/11/2026 — cho BƯỚC 303 ký (M2 PHÁN; ĐO 27)

1. **M1 và M2.** Một lượt thử trên dòng 9001 (nhãn THỬ; κ_d = 0,018; 200 thị trường NULL-M, bộ ba G · Z · H qua `cx.cham` và oracle `tinh_su_that_m` của chính từng thị trường; script ngoài repo `vibe_logs_301/nhap/m1_thu.py` và `m1_tam.py`, Sau khi nhìn) cho thấy M1 viết nguyên văn gần như qua miễn phí: ΔIC_true trung bình của G = −0,0189 (mọi spec mono từ −0,019 đến −0,021), của Z = +0,0027, của H = −0,0026, nên xác nhận nhầm theo "QUA mà ΔIC_true ≤ 0" chỉ 1/200 thị trường. Cũng trên 200 thị trường ấy, z′ = (Δ − ΔIC_true) / σ_hoán-vị có sd ≈ 1,08 (G) · 1,17 (Z) · 1,10 (H) (σ suy ra từ p và Δ, thô). Người dùng chọn: *"Giữ M1 + phán thêm z′ (Recommended)"*, tức là: **GIỮ M1** (≤ 50/1.000, như 21.4) **và THÊM M2, PHÁN:** trên 1.000 thị trường NULL-M của dòng 9, độ lệch chuẩn GỘP của z′ = (Δ − ΔIC_true) / σ_hoán-vị qua bộ ba G · Z · H phải nằm trong **[0,8 ; 1,25]** (khoảng đã khai ở mục 3 và mục 8 của đặc tả nháp, KHÔNG chọn từ số thử ở trên). Tỷ lệ đuôi P(z′ > z_c) là **Báo kèm**. M2 là tiêu chí MỚI, đứng cạnh M1; BƯỚC 303 viết nó vào ĐO 38 nguyên văn.
2. **ĐO 27.** Người dùng chọn: *"Sổ không đổi thì chỉ ghi băm (Recommended)"*. Áp dụng ở BƯỚC 303, không thuộc BƯỚC 301.

## 22. Kết quả hiệu chuẩn của bản sửa C4 (BƯỚC 301, 26/11/2026; dòng hạt 1, MỖI VIỆC MỘT LẦN)

**Trạng thái:** số ĐO, không còn là khai trước. Leader chạy bốn việc của 21.6 từ cây `vibe_wt_301` ở mã băm **`b9779b55f0`** (cây SẠCH khi chạy; mọi khối của file ghi cùng mã băm ấy), mỗi việc bằng đúng lệnh ở 21.6 (`./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --viec <kd|a0|t1|pt> --luong 1 --so-tien-trinh 12`), theo thứ tự kd → a0 → t1 → pt; log ngoài repo `vibe_logs_301/hieu_chuan/{kd,a0,t1,pt}.log`; bản ghi `docs/thi-truong-gia-hieu-chuan-do38.json` (đọc lại: `./.venv/Scripts/python.exe -X utf8 tools/hieu_chuan_sua_c4.py --doc`, số in khớp log từng chữ). KHÔNG việc nào chạy lại; KHÔNG điều kiện DỪNG nào bị chạm. Thời gian thật (12 tiến trình): kd 27 s · a0 1.540 s · t1 201 s · pt 8.825 s.

**Nhãn.** *Đã khai* = quy tắc đặt ở 21.2 · 21.3 · 21.6 trước khi có số; *Báo kèm* = in ra, không phán; *Sau khi nhìn* = đọc của BƯỚC này sau khi đã thấy số, không hiệu chuẩn.

| việc | kết quả | nhãn |
|---|---|---|
| **kd** (dòng 1, chỉ số 1.400.001–1.409.100) | **κ_d = 0,018**, không thất bại (a–e đều không chạm). IC(điểm đã ghi) theo lưới 0,012 → 0,028: 0,0643 · 0,0763 · 0,0877 · **0,0960** · 0,1067 · 0,1191 · 0,1280 · 0,1353 · 0,1432 (đơn điệu). Khối KIỂM n = 100 tại κ_d = 0,018: IC **0,0965 ± 0,0010**, trong [0,090 ; 0,110]. | Đã khai (κ_d); IC lưới Báo kèm |
| **a0** (dòng 1, chỉ số 1.100.001–1.120.000, N = 20.000) | p̂ = **5.263/20.000 = 0,2631**, SE 0,0031, p̂ + 3·SE = 0,2724 < 0,3 (không dừng). **Ngưỡng A0 = binom.ppf(0,999 ; 1000 ; p̂) = 307** (ĐO 37: 317). | Đã khai |
| a0, báo kèm | trung bình 2,969 spec khai mỗi thị trường; tỷ lệ chọn từng spec từ 0,2351 (`mono_sr_score`) đến 0,2968 (`bo_sr_score`), G (`mono_volume_score`) = 0,2631; χ² của số lần chọn so với đều = 280,2 (10 bậc tự do). Lệnh: đọc `ket_qua.ty_le_theo_spec` trong bản ghi, χ² = Σ(o − e)²/e với o = tỷ lệ · N, e = tổng/11. | Báo kèm |
| **pt** (dòng 1, Tầng 2 mức 2×, chỉ số 1.200.001–1.200.200, n_cal = 200) | **k = 92** (92/200 = 0,46, trong [0,2 ; 0,7]), `data_quality` ≠ OK: 0 dòng; Beta(92,5 ; 108,5); **dải 99% của R = 100: [31 ; 62]**. | Đã khai |
| **t1** (dòng 1, Tầng 1 mức 2×, chỉ số 1.300.001–1.301.000, n = 1.000) | bảng 2×2 dưới đây; không dừng. | Báo kèm |

**Bảng 2×2** {G, G′} × {Tầng 1, Tầng 2} của (m = Δ trung bình, s = độ lệch chuẩn của Δ, σ̄ = σ hoán vị trung bình, P = tỷ lệ `QUA`); G′ = `bo_momentum_score`, G = `mono_volume_score`; hai tầng ở cùng κ 2× (Báo kèm):

| | Tầng 1 (n = 1.000) | Tầng 2 (n = 200) |
|---|---|---|
| G′ | m +0,0246 · s 0,0062 · σ̄ 0,0065 · QUA 930/1000 (P 0,930) | m +0,0325 · s 0,0158 · σ̄ 0,0140 · QUA 92/200 (P 0,460) |
| G | m +0,1486 · s 0,0247 · σ̄ 0,0248 · QUA 1000/1000 (P 1,000) | m +0,0106 · s 0,0274 · σ̄ 0,0276 · QUA 7/200 (P 0,035) |

Hai hàng còn lại của cùng bản ghi, cùng nhãn: Z (`doi_cho_trend_sr`) Tầng 1 m +0,0029 · s 0,0064 · σ̄ 0,0065 · QUA 26/1000; Tầng 2 m −0,0663 · s 0,0191 · σ̄ 0,0189 · QUA 0/200 (báo động hai phía 183/200). H (`bo_volume_score`) Tầng 1 m −0,0482 · s 0,0069 · σ̄ 0,0068 · QUA 0/1000; Tầng 2 m −0,0235 · s 0,0119 · σ̄ 0,0122 · QUA 0/200 (báo động 63/200).

**Đọc (Sau khi nhìn; không hiệu chuẩn, không phán):**
1. s/σ̄ (độ lệch chuẩn thực của Δ so với σ của hoán vị mà chính bước xác nhận chia cho) gần 1 ở mọi ô: Tầng 1 G′ 0,95 · G 1,00; Tầng 2 G′ 1,13 · G 0,99 (s, σ̄ đọc từ bản ghi; các ô s đo ở mức 2×, nơi Δ thay đổi theo thị trường nên s gồm cả dao động của Δ thật). Riêng G′ ở Tầng 2 s lớn hơn σ̄ 13%.
2. Cùng một κ cho cùng một G thì ở Tầng 2 G chỉ còn m = +0,0106 (Tầng 1: +0,1486) và QUA 3,5% (Tầng 1: 100%): tín hiệu của `volume_score` đi qua đường ống thật (chấm điểm bằng `_analyze`) yếu hơn nhiều so với tầng điểm sinh trực tiếp. Điều này đã là lý do G′ = `bo_momentum_score` được chọn ở Tầng 2 (19.8 khoản 1); bảng 2×2 là số đo đầu tiên đặt hai tầng cạnh nhau ở cùng κ và cùng luật `trang_thai`.
3. P(QUA) của G′ ở Tầng 2 = 0,46 so với 41/100 ở dòng 4 của ĐO 37 (BƯỚC 296, dòng hạt khác): cùng chiều, không mâu thuẫn (SE nhị thức 200 mẫu ≈ 3,5 điểm phần trăm).
4. p̂ = 0,2631 thấp hơn 3/11 = 0,2727 gần một điểm phần trăm (≈ 3 SE); chiều ra cho thấy bản sửa không thiên về dễ đạt: ngưỡng 307 thấp hơn 317 của ĐO 37.

**Điều CHƯA làm.** Chưa ký ĐO 38 (BƯỚC 303: sổ tay thật, TIEU-CHI-DOC-TRUOC, đổi dòng `max(ĐO) == 37` của `tests/test_chay_chinh_thuc_thi_truong_gia.py`, tổng quát hoá cửa, M2 ở mã); chưa chạy dòng 6–9 (BƯỚC 304); M1/M2 chưa có số ở dòng 9. Mọi con số 9001 ở 21.6–21.7 vẫn là số THỬ và KHÔNG được dùng thay các số trên.
