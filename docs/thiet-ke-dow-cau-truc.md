# Thiết kế — Đọc cấu trúc giá theo Lý thuyết Dow (swing / internal, BOS / CHoCH, thủy triều – con sóng) và ghép chu kỳ Wyckoff 4 giai đoạn

**Mốc:** B5 (mượn — xem mục 14, câu 2: `docs/LO-TRINH.md` chưa có dòng nào cho việc đọc cấu trúc giá; B5 là dòng gần nhất: "CHỈ ĐỂ HIỆN, không vào chấm điểm, đường lệnh ảo hay backtest").
**Duyệt hướng:** người dùng, 29/10/2026, trong phiên leader (BƯỚC 244). **Trạng thái:** BẢN ĐẶC TẢ, **chưa có dòng mã nào**; bảy câu mở ở mục 14 ĐÃ CHỐT 29/10/2026. Việc kế: BƯỚC khai ĐO (Lát 0b), rồi Lát 1.

Tài liệu này là đề bài cho các phiên làm mã, theo khuôn `docs/thiet-ke-c1-san-dau.md`. Luật chung (vá file, đột biến, năm cổng, giao PR) ở skill `quy-trinh-lam-viec` — đi theo nó, đừng chép lại vào đây. Hai nguồn bằng chứng nằm NGOÀI repo, nên mọi khẳng định bên dưới đều kèm mục của chúng:

- **NC** = báo cáo nghiên cứu Lý thuyết Dow, `C:\Users\cuong\AppData\Local\Temp\nghien-cuu\2026-10-29-dow\BAO-CAO.md` (trích văn bản gốc Nelson 1902 và Hamilton 1922 đọc nguyên văn; Rhea 1932, Murphy, Schannep chỉ đọc qua trích dẫn — NC §0). Ví dụ "NC §8 R4" = mục 8, quy tắc R4.
- **TR** = báo cáo tìm tiền lệ mã nguồn mở, `C:\Users\cuong\AppData\Local\Temp\tim-repo\2026-10-29-dow-smc\BAO-CAO.md`. Ví dụ "TR §5.1".

Hai đường ấy có thể mất khi thư mục tạm bị dọn; các câu trích cần thiết đã được chép ngay trong tài liệu này. Mọi `file:dòng` của repo được `grep` ở cây `7e0218c` ngày 29/10/2026; số dòng trôi theo mã, tên hàm thì không.

---

## 1. Mục đích, và điều tài liệu này KHÔNG là

Người dùng muốn dự án có phần **đọc cấu trúc giá** theo Lý thuyết Dow và đối chiếu với SMC (BOS, CHoCH, cấu trúc swing / internal) và Wyckoff (tích luỹ, markup, phân phối, markdown). Câu hỏi gốc: dự án đã có đủ các thành phần ấy chưa. Mục 3 trả lời bằng kiểm kê; mục 5–9 là thiết kế phần còn thiếu.

Nó **không** là: một tín hiệu giao dịch, một thành phần của điểm, một đề xuất ứng viên tầng 3, hay một lời hứa có lợi thế. Dự án đã đo rằng điểm cuối không dự báo được lợi nhuận (`CLAUDE.md`, mục *Trạng thái đo được*) và Fibonacci / Wyckoff đã nằm ở "CHỈ ĐỂ HIỆN" (`CLAUDE.md`, cùng mục). Cấu trúc Dow đi cùng đường đó: **hiện trước, đo sau, và chưa có kết quả đo nào đứng sau nó** — mục 9 khai phép đo chỉ-đọc ký trước nhưng KHÔNG chạy nó ở BƯỚC này.

## 2. Quyết định của người dùng (29/10/2026, nguyên văn)

Lời mở đầu: *"Tôi muốn nó thêm vào dự án mình, nhưng trước tiên hãy tìm hiểu thêm."* · *"Dự án của mình có SMC nhưng tôi không biết có đầy đủ các thành phần" BOS, CHoCH, Swing/Internal Structure này không. Tương tự như Wyckoff (Tích lũy, Markup, Phân phối, Markdown)."* · *"hãy nghiên cứu sâu hơn về lý thuyết DOW. Khi đã hoàn thiện hãy áp nó vào dự án sao cho hợp lý."*

| Câu hỏi | Trả lời |
|---|---|
| Phạm vi | *"Module + hiển thị + đo chỉ-đọc (Recommended)"* |
| Nơi đặt skill | *"Trong repo, .claude/skills (Recommended)"* |
| Wyckoff | *"Ghép chu kỳ 4 giai đoạn, chưa thêm sự kiện (Recommended)"* |

Hệ quả đã chốt: (1) một MODULE thuần mới + một ô trên app + một phép đo chỉ-đọc ký trước; (2) skill Dow nằm trong repo (`.claude/skills/dow-theory-analysis/SKILL.md`, viết lại từ bản nháp của người dùng ở mục 12); (3) chu kỳ 4 giai đoạn GHÉP từ hai thứ đã có — `pha_wyckoff.doc_pha` cho phần trong vùng, thủy triều cho phần ngoài vùng — và **không** thêm sự kiện Wyckoff nào (LPS, LPSY, ST, tái tích luỹ / tái phân phối để sau).

## 3. Kiểm kê repo — dự án đã có gì (đã `grep`, 29/10/2026)

| Thành phần người dùng hỏi | Có trong repo? | Bằng chứng |
|---|---|---|
| Swing / internal structure (đỉnh–đáy xoay chiều theo hai cấp) | **KHÔNG** | `git grep -i -I -n "swing\|zigzag\|fractal\|choch\|break of structure" 7e0218c -- '*.py' '*.md' ':!tests'` (cây TRƯỚC BƯỚC này) ra 0 dòng. `git log --all -S"CHoCH" --oneline` 0 commit |
| BOS / CHoCH | **KHÔNG** | cùng lệnh trên |
| HH / HL / LH / LL | **KHÔNG** | `TrendAgent` (`analysis_agents.py`, lớp `TrendAnalysisAgent`) chấm bằng EMA20, SMA50, SMA200, ADX và một luật giá so MA10 / MA20 (`MO-XE-KIEN-TRUC.md`, mục *Điều này nghĩa là gì*) — thước trung bình động, không phải cấu trúc đỉnh–đáy |
| "Smart Money" | chỉ là TÊN | `app.py:1306–1309`: "Smart Money Flow %" = `last_vol / avg_vol − 1` — một tỷ lệ khối lượng, không phải khái niệm SMC |
| Pivot | chỉ pivot sàn cổ điển | `analysis_agents.py:330–337`: `(H+L+C)/3` của phiên cuối, R1, S1 — không dò đỉnh–đáy |
| Wyckoff: tích luỹ / phân phối / pha A–E, cao trào, AR, Spring, UTAD, Test, SOS, SOW | **CÓ** | `pha_wyckoff.py` — `doc_pha` (`:309`), hằng số (`:61–78`), lớp `PhaWyckoff` (`:87`); đọc `df.tail(CUA_SO_CAU_TRUC)` = 120 phiên (`:62`, `:136`); nền / gần đây không giao nhau (`:346–347`); "Chưa đủ bằng chứng" là câu trả lời hợp lệ (`:109–118`) |
| Wyckoff: Markup, Markdown | **một phần** | chỉ là pha E SAU KHI giá rời vùng (`pha_wyckoff.py:392–405`): `Markup` thuộc `TÍCH LUỸ`, `Markdown` thuộc `PHÂN PHỐI`. Không có "xu hướng đang chạy mà chưa từng có vùng được nhận ra" |
| Wyckoff: LPS / LPSY, ST, tái tích luỹ / tái phân phối | **KHÔNG** | tái tích luỹ / tái phân phối chỉ xuất hiện như một câu phản biện (`pha_wyckoff.py:266–273`, `:284–288`) |
| Chu kỳ 4 giai đoạn như một TRẠNG THÁI xu hướng | **KHÔNG** | chưa có hàm nào trả "đang ở giai đoạn nào" ngoài vùng |
| Mức Fibonacci | **CÓ**, uỷ thác biên vùng | `muc_fibonacci.doc_muc` lấy biên vùng từ `pha_wyckoff` (`CLAUDE.md`), không tự dò đỉnh–đáy |

Hai điểm rút ra cho thiết kế: (a) ô "Pha Wyckoff" ở thanh bên (`app.py:1387`) đọc từ `df` của BIỂU ĐỒ — `days_back = 180` ngày lịch (`app.py:1031`, `:1070`, ≈ 124 phiên theo chú thích `:1076`), còn cửa sổ phân tích dài hơn (`NGAY_LICH_SU_PHAN_TICH = 420`, `app.py:1085`, ≈ 285 phiên theo chú thích `:1084`). Cấp swing cần nhiều pivot hơn thế; mục 7.3 xử lý. (b) Phần hiển thị và phần chấm điểm đã tách bằng gác AST (`tests/test_ke_hoach_vao_lenh.py:1066`, `:1081`, `:1089`) — cùng khuôn được dùng lại ở mục 8.

## 4. Nền bằng chứng — Lý thuyết Dow nói gì và KHÔNG nói gì

Chỉ nêu cái mô-đun dùng. Còn lại ở NC.

1. **Xu hướng là chuỗi đỉnh–đáy.** Dow (Nelson 1902, tr. 40, NC §1.7): thị trường tăng chừng nào mỗi đỉnh sau cao hơn đỉnh trước; giảm khi một đáy thấp hơn các đáy trước. Dow cũng cảnh báo khó phân biệt cuối một nhịp tăng với một nhịp điều chỉnh sâu bất thường. → cơ sở của HH / HL / LH / LL (mục 5.6) và thủy triều (mục 5.8).
2. **Ba chuyển động; độ dài KHÔNG thống nhất giữa các nguồn** (NC §1.1): chính — Dow 1902 "ít nhất bốn năm" / 4–6 năm, Hamilton 1922 "một đến ba năm"; phụ — Dow 10–60 ngày, Hamilton "vài ngày đến nhiều tuần", Rhea (qua Blay, thứ cấp) 3 tuần–3 tháng; nhỏ — biến động hằng ngày. Bản nháp "vài tháng đến nhiều năm" / "vài tuần đến vài tháng" là diễn đạt gộp, không là trích nguồn nào.
3. **Biên độ con sóng:** Dow ≥ 3/8 (37,5%) của nhịp chính (Nelson tr. 43; xã luận 20/07/1901 nói trước hết về cổ phiếu riêng — quy tắc kinh nghiệm, không phải thống kê hiệu chỉnh); Rhea (thứ cấp) 1/3–2/3; Schannep (thứ cấp, gắn với người bán dịch vụ) > 3% và khoảng 8 phiên (NC §1.2, §2). **1/3–2/3 không phải 38,2–61,8% Fibonacci**, và không có chữ "Fibonacci" nào trong Nelson hay Hamilton (NC §7 dòng 43, §9 mục 3).
4. **Chỉ giá đóng cửa — là THỰC TẾ DỮ LIỆU, không phải luật "bỏ râu nến".** Các chỉ số Dow–Jones được tính từ giá đóng cửa (Hamilton 1922, phụ lục tr. 288–289, NC §1.4); không có nến, không có râu. Việc đòi "đóng cửa vượt mốc mới tính" là quy ước hiện đại; mô-đun lấy đóng cửa làm **nền** và râu nến làm phép cắt (ablation, mục 9).
5. **Xác nhận giữa hai chỉ số** (Công nghiệp và Vận tải) là nguyên lý thời Hamilton–Rhea, không có trong các xã luận của chính Dow như Nelson gom (NC §1.5). Tín hiệu chính kinh điển cần CẢ HAI chỉ số phá cực trị của con sóng (NC §1.7 mục 3). **Một chuỗi giá duy nhất không đọc ra được tín hiệu Dow đúng nghĩa** — nên CHoCH / BOS của mô-đun này là "cảnh báo cấu trúc", không là "tín hiệu Dow" (NC §4.2). Phần hai chỉ số = PHẦN 2 (mục 10).
6. **Khối lượng là nguyên lý yếu** (Hamilton tr. 177: "ít ý nghĩa hơn người ta tưởng", NC §1.6). Mô-đun không dùng khối lượng; chỉ có phép cắt (ablation) ở mục 9.
7. **"Vùng đi ngang" (line):** Hamilton tr. 172–173 gọi là vùng tích luỹ hoặc phân phối (NC §1.3). Đây là điểm DUY NHẤT mà nguồn xác nhận sự chồng lấn thuật ngữ với Wyckoff (NC §5 dòng 1); mọi tương ứng khác (con sóng ~ tái tích luỹ, BOS ~ SOS + LPS, CHoCH ~ SOW + LPSY, gợn sóng ~ inducement) là **loại suy**, chưa có nguồn (NC §5, §7).
8. **Không có bằng chứng Dow dùng được cho lợi nhuận** ở thị trường này: Cowles cho Hamilton là "tung đồng xu"; BGK (1998, bản làm việc, OCR) tìm thấy thông tin trong các lời gọi của Hamilton 1902–1929 nhưng không có phí giao dịch, alpha ≈ 3%/năm không rõ có ý nghĩa, và KHÔNG kiểm bộ luật Rhea / Schannep; Rink (2023) trên 41 chỉ số thấy khả năng dự đoán mờ dần và phí giết phần lớn lợi nhuận; không tìm thấy nghiên cứu Dow nào cho VN-INDEX (NC §3, §9 mục 9–10). → mục 9 đặt "không tín hiệu" là kết cục bình thường, không phải thất bại của việc dựng.

## 5. Mô-đun `cau_truc_gia.py` — hợp đồng

Tên mô-đun do đặc tả đặt (đổi tên là việc của Lát 1, kèm sửa mục này). Một module THUẦN ở gốc repo, khuôn `pha_wyckoff.py` và `ke_hoach_vao_lenh.py`: không mạng, không đĩa, không đồng hồ, không trạng thái chạy.

### 5.1 Vào / ra

- **Vào:** bảng nến ngày tăng dần theo thời gian, cột bắt buộc `time`, `high`, `low`, `close`; `volume` tuỳ chọn (chỉ để gắn cờ phiên không giao dịch); tham số chọn bộ dò và ngưỡng. Hệ số giá `price_multiplier` (`data_quality.py:162`) nhận ngoài như `doc_pha` nhận `he_so_gia` — chỉ để suy bước giá.
- **Ra:** MỘT **nhật ký sự kiện chỉ-thêm** (`nhat_ky`) + các hàm đọc nhật ký tại thời điểm `t`. Lý do chỉ-thêm: nếu một bản ghi pivot đổi trạng thái theo thời gian ("bị thay"), thì cùng bản ghi ấy khác nhau giữa lượt chạy cắt ở `t` và lượt chạy đủ — phép thử bất biến khi cắt (mục 8.1) không còn phát biểu được. Mọi thay đổi là MỘT dòng mới với `ngay_biet` riêng của nó.

### 5.2 Hai thời điểm trên MỌI pivot và MỌI sự kiện

| Trường | Nghĩa |
|---|---|
| `ngay_xay_ra` | ngày của nến mang cực trị (pivot) hoặc nến đóng cửa phá mốc (sự kiện) |
| `ngay_biet` | ngày của nến ĐẦU TIÊN mà việc đó có thể tính được chỉ từ dữ liệu tới hết nến ấy. Pivot: `ngay_biet` > `ngay_xay_ra` (độ trễ ≥ 1 phiên). Sự kiện phá mốc: `ngay_biet` = `ngay_xay_ra` (đóng cửa vượt mốc là biết ngay khi nến đóng) |
| `chi_so_xay_ra`, `chi_so_biet` | chỉ số hàng tương ứng (đo độ trễ bằng phiên, không bằng ngày lịch) |

Mọi bản tin hiển thị và mọi phép đo chỉ được dùng một bản ghi từ nến có chỉ số ≥ `chi_so_biet`. Khuôn mượn từ TR §5.1 (`LocalExtreme{index, price, conf_index, conf_price}` của neurotrader888, giấy phép MIT — mượn ý, viết lại, không chép).

### 5.3 Bộ dò pivot: ba họ, một mặc định hiển thị

Ba họ, mỗi họ có LƯỚI tham số (NC §8 R1, R1b, R3; TR §5.1–5.2). Mọi ô lưới đều được báo ở phép đo (mục 9); lưới KHÔNG được thu hẹp sau khi thấy kết quả.

| Họ | Định nghĩa trên giá ĐÓNG CỬA | `ngay_biet` | Lưới `(nội bộ, swing)` |
|---|---|---|---|
| **ATR** (mặc định) | trạng thái máy: theo dõi cực trị đang chờ; một ĐỈNH được xác nhận ở nến đầu tiên có `close_t ≤ đỉnh_chờ − k × ATR14_t`; ĐÁY đối xứng | nến xác nhận (độ trễ thay đổi theo dữ liệu) | `k`: (2,3) · (2,4) · (3,4) |
| **Fractal** | nến `i` có `close_i` lớn hơn NGHIÊM NGẶT `close` của `N` nến mỗi bên (đáy ngược lại) | `i + N` | `N`: (3,8) · (5,13) · (3,13) · (5,50) |
| **ZigZag %** | đảo chiều khi giá đóng cửa lùi ≥ θ so với cực trị đang chạy | nến lùi đủ θ | θ: (5%,10%) · (5%,15%) · (7%,15%) |

Giá trị lưới là giá trị đề xuất của NC §8 R1 / R1b / R3 và mặc định của LuxAlgo (5, 50) ở R7; ATR(14) theo R1b. **ATR dùng `high`, `low`, `close` chỉ để ĐO ĐỘ BIẾN ĐỘNG** (ngưỡng đảo chiều); đỉnh–đáy và phép phá mốc vẫn lấy từ `close` (R9 là phép cắt dùng râu nến). ATR tính theo trung bình đơn 14 phiên của true range, chỉ dùng các nến ≤ `t` (nhân quả); 14 là quy ước chuẩn, không dò.

**Mặc định hiển thị: họ ATR, `(k_nội bộ, k_swing) = (2, 4)`. Lý do, chốt TRƯỚC khi có bất kỳ số đo nào:**
1. ATR cho ngưỡng tỷ lệ theo biến động từng mã — mã VN có biên độ ngày và ATR khác nhau nhiều (TR §5.1); ngưỡng cố định N phiên hay θ% bỏ qua điều đó.
2. Pivot ATR **không bao giờ bị thay thế** (xen kẽ có sẵn do cấu trúc) nên nhật ký không cần dòng "thay thế" cho mặc định; họ Fractal và ZigZag cần luật xen kẽ R2 (mục 5.5).
3. `(2, 4)` là hai đầu của lưới `k ∈ {2,3,4}` ở NC §8 R1b: khoảng cách gấp đôi giữa hai cấp làm hai cấp ít trùng pivot nhất trong lưới. Đây là lập luận cấu trúc, **không dựa vào lợi nhuận** — lợi nhuận không được xem trước phép đo ký ở mục 9.

Hai cấp là HAI bộ dò độc lập với hai ngưỡng (kiểu LuxAlgo: `leg(size)` với `size` 50 và 5, TR §5.2), không phải thăng cấp đệ quy (kiểu neurotrader888, TR §5.1). Lý do: mỗi cấp chỉ phụ thuộc dữ liệu tới `t` của chính nó, nên chứng minh bất biến khi cắt đơn giản hơn; thăng cấp thêm độ trễ và trạng thái chéo cấp. Thăng cấp để lại làm phép cắt, không vào Lát 1–3. **Nhãn trên giao diện nói thẳng đây là xấp xỉ:** không có thư viện nào làm phép tách Dow chính / phụ thật (TR §6), và hai cấp pivot không phải "chính / phụ / nhỏ" của Dow (NC §5 dòng 6).

**Động cơ chạy tăng dần.** Bộ dò là một hàm `cap_nhat(trang_thai, nen) → (trang_thai, các_dòng_nhật_ký_mới)`; `doc_cau_truc(df)` chỉ là vòng lặp trên nó. Phép thử mục 8.1 đòi: chạy cả bảng == chạy từng nến, và chạy `df[:t+1]` == nhật ký chạy đủ cắt ở `ngay_biet ≤ t`. Pivot CHỜ (cực trị đang theo dõi, chưa xác nhận) **không bao giờ** vào nhật ký, không có nhãn, không là mốc phá — nó chỉ hiện như "đỉnh/đáy tạm" ở lớp trình bày, kèm chữ *tạm* (NC §8 R2 cột cuối: nhánh cuối của zigzag là đo bằng hồi tưởng).

Khi một nến xác nhận pivot mà nó đã chứa sẵn cực trị của chặng mới, cực trị chờ của chặng mới là cực trị của các `close` trong `(chỉ số pivot, t]` — KHÔNG phải chỉ `close_t`, vì ngưỡng ATR đổi theo phiên và nến trước `t` có thể cao hơn `close_t` mà chưa đủ ngưỡng ở phiên ấy.

### 5.4 Giá bằng nhau trên lưới bước giá; kịch trần / sàn; phiên không giao dịch

- **Bằng nhau.** Giá đóng cửa VN nằm trên lưới bước giá (`truot_gia.BUOC_GIA`, `truot_gia.py:61–65`; `buoc_gia`, `:70`). Hai giá coi là **bằng nhau** khi chênh nhau dưới nửa bước giá của mức giá ấy (đổi sang VNĐ bằng hệ số giá, bước giá theo sàn tra bằng `san_giao_dich`). Hệ quả: (i) cực trị chờ chỉ bị thay khi giá vượt NGHIÊM NGẶT qua nửa bước (cực trị cũ giữ, đỉnh bằng không thay đỉnh cũ); (ii) mốc bị phá chỉ khi đóng cửa vượt mốc quá nửa bước; (iii) nhãn so hai đỉnh liền kề trả `bằng` (không ép HH hay LH) — theo Dow, đỉnh KHÔNG vượt đỉnh trước thì không phải xu hướng tăng xác nhận (NC §1.7 mục 1). Hai bản sao của lỗi này đã thấy ngoài đời: Kaltsit coi hai đỉnh cùng giá là "không có đỉnh mới" qua `!= shift(1)` và PyIndicators đánh `≥` ở cả hai nến (TR §5.3–5.4); đặc tả đòi so TỪNG sự kiện, không so "giá đổi".
- **Giới hạn khai thẳng.** Nguồn giá điều chỉnh LÙI sau sự kiện quyền (`su_kien_quyen.py`, đầu tệp) nên phần lịch sử trước sự kiện có giá nhân hệ số `f ≤ 1`; nửa bước giá của lưới tính theo giá HIỆN không co theo `f` (ước lượng sai số: cỡ `1 − f`, **chưa đo**). Ảnh hưởng chỉ ở các ca bằng giá chính xác; Lát 1 đếm số ca bằng giá và số ca gần-bằng-giá trên cache (mô tả, không đọc lợi nhuận) trước khi phán nửa bước có đủ không.
- **Kịch trần / sàn.** Mô-đun KHÔNG tự suy trần từ phần trăm (`CLAUDE.md`, mục màu bảng giá). Nó dùng đúng phép phân loại đã có cho nến một giá: `vong_doi_lenh.khoa_bien` (`vong_doi_lenh.py:199`; nến cao = thấp VÀ |giá ÷ tham chiếu − 1| ≥ 0,9 × biên độ — hằng `:55`), biên độ sàn từ `data_quality.EXCHANGE_LIMITS` (`data_quality.py:199`: HOSE 0,07 · HNX 0,10 · UPCOM 0,15). Nến khoá biên mang cờ `khoa_bien ∈ {KICH_TRAN, KICH_SAN}` trên MỌI pivot và sự kiện lấy từ nến ấy. **Không bỏ nến, không sửa giá**: một pha phá mốc xảy ra ở nến kịch sàn là một sự kiện có thật nhưng KHÔNG thi hành được (bên bán chặn), và phép đo (mục 9) báo riêng "bỏ các sự kiện phá mốc ở nến khoá biên" cạnh số đầy đủ (NC §8 phần "Baselines and hygiene": khoá biên là chỗ tín hiệu không thi hành được).
- **Phiên không giao dịch** (`volume = 0`, cao = thấp = đóng cửa phiên trước): giữ nến (Hamilton dùng giá đóng cửa trước cho cổ phiếu không giao dịch trong ngày, NC §1.4); gắn cờ `khong_giao_dich`. Nến này không tạo cực trị mới (giá bằng giá trước), nhưng ATR lấy true range = 0 cho nến ấy, nên số nến như vậy được đếm và báo trong phần mô tả của Lát 1.
- **Quyền điều chỉnh giá.** Mô-đun KHÔNG điều chỉnh giá: nhận chuỗi đúng như nguồn trả (`VNStockCollectorAgent` — điều chỉnh lùi, `su_kien_quyen.py`). Mọi phép so của mô-đun là so thứ tự hoặc so tỷ lệ trong cùng một chuỗi, và ngưỡng ATR co giãn cùng chuỗi; nên trên phần lịch sử trước sự kiện (chỉ nhân một hệ số đồng đều), thứ tự và sự kiện không đổi — chuỗi KHÔNG điều chỉnh sẽ lại thấy một cú rơi cơ học ở ngày giao dịch không hưởng quyền, một CHoCH giả (nguyên nhân: giá thị trường rơi cơ học, `su_kien_quyen.py` đầu tệp). Hệ quả cho phép đo: giá in ra trên giao diện là giá THEO CƠ SỞ HÔM NAY của nguồn, và phép đo trên cache `acf6dca1…` mang cơ sở điều chỉnh của ngày kéo cache (phải nêu băm cache, theo luật đọc bảng của `CLAUDE.md`, BƯỚC 199). Chuỗi VN-INDEX không điều chỉnh. **Điều chưa kiểm:** nguồn điều chỉnh có sửa lại các mốc cũ giữa hai lần kéo hay không — phép thử bất biến khi cắt (mục 8.1) chạy trên MỘT bản chụp, nên nó chứng minh mã, không chứng minh dữ liệu.

### 5.5 Xen kẽ

Bộ ATR xen kẽ đỉnh–đáy ngay trong cấu trúc máy trạng thái. Hai họ còn lại phải thực thi luật R2 (NC §8): hai pivot cùng loại liên tiếp thì giữ cái cực trị hơn; pivot chỉ **chung cuộc** khi pivot đối loại kế tiếp được xác nhận. Cài bằng dòng nhật ký chỉ-thêm (`xac_nhan` rồi `thay_the`, mỗi dòng có `ngay_biet` riêng); cấm tái dùng mã của `smartmoneyconcepts` (xoá pivot hồi tố trên toàn chuỗi, ép nến đầu và nến cuối làm pivot, TR §5.5).

### 5.6 Nhãn HH / HL / LH / LL

Mỗi pivot được so với pivot CÙNG LOẠI kề trước ở CÙNG cấp: cao hơn → `HH` (đỉnh) / `HL` (đáy); thấp hơn → `LH` / `LL`; trong nửa bước giá → `bằng`. Nhãn là một trường của dòng pivot, biết cùng `ngay_biet` của nó (pivot cùng loại kề trước đã biết từ trước). Khuôn: LuxAlgo so `currentLevel` với `lastLevel` (TR §5.2), PyIndicators so với pivot cùng loại (TR §5.3).

### 5.7 BOS / CHoCH theo cấp

Mỗi cấp giữ một **thiên hướng** `thien_huong ∈ {tang, giam, chua_co}` và, cho mỗi pivot đã xác nhận, một cờ `da_pha`.

1. Ở nến `t`, trước hết xét phá mốc với các pivot có `chi_so_biet ≤ t − 1` (**chỉ các pivot đã biết TRƯỚC nến phá**); sau đó mới ghi các pivot được xác nhận ở chính nến `t`.
2. Đóng cửa vượt đỉnh gần nhất chưa bị phá quá nửa bước giá → phá lên; đóng cửa lùi dưới đáy gần nhất chưa bị phá quá nửa bước giá → phá xuống. Mỗi pivot bị phá tối đa MỘT lần (cờ `da_pha`).
3. Phá **cùng chiều** thiên hướng hiện có → `BOS`; **ngược chiều** → `CHoCH`; sau sự kiện, thiên hướng đổi theo chiều phá. Đây là luật LuxAlgo (`ta.crossover(close, mức)`, một lần mỗi pivot; BOS khi cùng thiên hướng, CHoCH khi ngược, TR §5.2). Mượn ý, KHÔNG chép mã (giấy phép CC BY-NC-SA 4.0; repo công khai).
4. **Khác LuxAlgo ở một chỗ, có chủ ý:** khi `thien_huong = chua_co` (sự kiện đầu tiên của chuỗi) ghi `KHOI_DAU`, không ghi BOS. Chưa có cấu trúc nào trước đó để "tiếp diễn".
5. Mỗi sự kiện mang: loại (`BOS` · `CHOCH` · `KHOI_DAU`), chiều, cấp, `ngay_xay_ra = ngay_biet`, pivot bị phá (chỉ số, giá, **và `ngay_biet` của nó, luôn < ngày sự kiện**), cờ `khoa_bien`.
6. LuxAlgo còn lọc sự kiện nội bộ trùng mức với swing và lọc hình dạng nến (TR §5.2); Lát 2 KHÔNG làm hai bộ lọc ấy. Mỗi cấp đứng một mình, và hai cấp được hiển thị riêng.

### 5.8 Trạng thái Dow theo mã

Tính từ nhật ký tại `t`; mỗi thành phần mang `ngay_biet`.

- **Thủy triều** (xu hướng chính, đọc ở cấp **swing**): `tang` nếu đỉnh swing đã biết gần nhất là `HH` VÀ đáy swing đã biết gần nhất là `HL`; `giam` nếu `LH` và `LL`; còn lại `lan` (gồm cả khi có nhãn `bằng`, và khi chưa đủ hai đỉnh + hai đáy → `chua_du_bang_chung`). Đây là cách đọc vận hành của dự án (khuôn Kaltsit, TR §5.4), chặt hơn lời Dow (chỉ đòi đỉnh sau cao hơn đỉnh trước, NC §1.7 mục 1). Có thêm cờ `canh_bao_dao_chieu` khi thiên hướng swing hiện tại ngược thủy triều (đã có CHoCH swing nhưng nhãn chưa đổi) — hiển thị cờ, KHÔNG đổi nhãn thủy triều.
- **Mốc phủ định:** trong thủy triều `tang` là đáy swing đã biết gần nhất (đáy `HL` bảo vệ cấu trúc); trong `giam` là đỉnh swing đã biết gần nhất. Đóng cửa vượt qua nửa bước giá là CHoCH swing. Nêu mức, `ngay_xay_ra`, `ngay_biet`.
- **Con sóng** (phản ứng thứ cấp). Một **nhịp ngược** đi từ một pivot nội bộ đến pivot nội bộ đối loại kế tiếp, NGƯỢC chiều thủy triều. Nhịp ngược **đủ điều kiện** khi thỏa CẢ HAI (VÀ):
  - **biên độ:** ≥ 3/8 (37,5%) của nhịp chính tính từ đáy swing liền trước đến đỉnh của nhịp ngược (thủy triều `tang`; đối xứng cho `giam`) — giá trị của Dow (Nelson tr. 43, NC §1.2);
  - **thời gian:** ≥ 10 phiên giao dịch.
  Lưới (báo cáo ở mục 9, KHÔNG thu hẹp): biên độ ∈ {3%, 1/3, 3/8} (Schannep-ish, Rhea, Dow — NC §8 R4) × thời gian ∈ {8, 10, 15} phiên × {VÀ, HOẶC}. **Mặc định hiển thị: 3/8 VÀ 10 phiên.** Lý do chọn, trước khi có số đo: 3/8 là con số duy nhất từ nguồn gốc Dow; 10 phiên là điểm giữa lưới và trùng cận dưới "10 đến 60 ngày" của Dow (Nelson tr. 39; Nelson không nêu ngày lịch hay phiên giao dịch — NC §1.1 không phân định, nên đây là cách đọc của đặc tả). Rhea thừa nhận chưa hai học trò nào đồng ý một cách chọn con sóng (NC §1.2) — nhãn giao diện nói thẳng điều đó.
  - Một nhịp ngược **đang chạy** không được phân loại là xong (NC §8 R4). Giao diện có thể nói "đang rơi X% từ đỉnh Y sau N phiên — đã đủ điều kiện tạm" vì biên độ và thời gian chỉ tăng khi nhịp còn chạy; chữ *tạm* bắt buộc, và nhịp chỉ vào nhật ký KHI pivot kết thúc được xác nhận.

Dow còn đòi **hai** chỉ số xác nhận (NC §1.5); với một chuỗi, "tín hiệu chính" vắng mặt có chủ ý: ô trạng thái KHÔNG bao giờ nói "xác nhận xu hướng chính". Nó nói thủy triều (đọc từ nhãn), mốc phủ định, và cảnh báo.

### 5.9 Hình dạng dữ liệu ra (gợi ý, Lát 1–2 chốt)

```python
@dataclass(frozen=True)
class Pivot:               # một dòng nhật ký
    cap: str               # "noi_bo" | "swing"
    loai: str              # "dinh" | "day"
    ngay_xay_ra: str; chi_so_xay_ra: int
    ngay_biet: str;   chi_so_biet: int
    gia: float
    nhan: str              # "HH"|"HL"|"LH"|"LL"|"bang"|"chua_co"
    khoa_bien: str | None; khong_giao_dich: bool

@dataclass(frozen=True)
class SuKienPha:           # BOS / CHOCH / KHOI_DAU
    cap: str; loai: str; chieu: str
    ngay_xay_ra: str; ngay_biet: str
    pivot_bi_pha: Pivot    # pivot_bi_pha.chi_so_biet < chi_so_xay_ra
    khoa_bien: str | None
```

Mã thật được gác bằng test; đoạn trên chỉ để thống nhất tên trường giữa các lát.

## 6. Chu kỳ 4 giai đoạn — GHÉP, không phát minh

Hàm `ghep_chu_ky(cau_truc, pha)` nhận trạng thái Dow ở mục 5.8 và một `PhaWyckoff` (mô-đun này chỉ ĐỌC nó; **`pha_wyckoff.py` không được sửa**). Trả `ChuKy4(giai_doan, nguon, ly_do, ghi_chu)` với `giai_doan ∈ {Tích luỹ, Markup, Phân phối, Markdown, chưa đủ bằng chứng}`.

1. **Trong vùng** (`pha.ket_luan_duoc` và `pha.pha ≠ "E"`):
   - `pha.cau_truc = "TÍCH LUỸ"` → **Tích luỹ**, `nguon = pha_wyckoff`;
   - `pha.cau_truc = "PHÂN PHỐI"` → **Phân phối**, `nguon = pha_wyckoff`;
   - `pha.cau_truc = "CHƯA PHÂN ĐỊNH"` (pha B, `pha_wyckoff.py:490`) → `chưa đủ bằng chứng`, lý do "trong vùng đi ngang, chưa phân định tích luỹ hay phân phối".
2. **Rời vùng** (`pha.pha = "E"`): `Markup` / `Markdown` theo `pha.su_kien` (`pha_wyckoff.py:392–405`), `nguon = pha_wyckoff`.
3. **Ngoài vùng — Wyckoff không kết luận** (`pha.ket_luan_duoc` sai: gồm cả "biên độ nền quá rộng, giá đang trong xu hướng", `pha_wyckoff.py:357–360`): thủy triều `tang` → **Markup**, `giam` → **Markdown**, `nguon = thuy_trieu`, kèm ghi chú cố định "không có vùng đi ngang nào được nhận ra; đây là xu hướng đọc từ cấu trúc, không phải pha Wyckoff". `lan` hoặc `chua_du_bang_chung` → `chưa đủ bằng chứng`. **Từ thủy triều KHÔNG BAO GIỜ suy ra Tích luỹ hay Phân phối** (cần một vùng đi ngang, do `pha_wyckoff` nhận ra).
4. **Mâu thuẫn không bị ghi đè.** Khi `pha_wyckoff` kết luận và thủy triều ngược hướng — ví dụ pha E `Markup` mà thủy triều đang `giam` — hiển thị cả hai, thêm ghi chú "thủy triều swing chưa xác nhận" và KHÔNG đổi nhãn. Lý do: sau khi giá rời vùng, cấu trúc swing có độ trễ nên mâu thuẫn ở đoạn đầu là bình thường; còn ở pha A–D, việc thủy triều ngược hướng là hình dạng kinh điển (tích luỹ xuất hiện sau xu hướng giảm). Không ghi đè nghĩa là thứ gì sai đều nhìn thấy được.
5. "Chưa đủ bằng chứng" là một giá trị hợp lệ đứng ngang hàng, và tỷ lệ của nó cao là **đúng kỷ luật** (`CLAUDE.md`: 20/40 mã VN100 ở `pha_wyckoff`) — đặc tả cấm nới ngưỡng cho nhãn đẹp hơn.
6. **Chưa làm** (theo quyết định *"chưa thêm sự kiện"*): LPS · LPSY · ST · tái tích luỹ / tái phân phối. Chúng cần sửa `pha_wyckoff.py` hoặc một bộ dò riêng và để sau, khi đã có số đo của phần này.

Tham chiếu nguồn: bốn giai đoạn tích luỹ–markup–phân phối–markdown là khung Wyckoff riêng, không phải của Dow (NC §5 dòng 3–4); mô-đun ghi `nguon` trên nhãn để người đọc không đọc nhầm.

## 7. Ô trên app — CHỈ ĐỂ HIỆN

### 7.1 Vị trí và nội dung

Cạnh ô "Pha Wyckoff" ở khung "📊 Tín hiệu nhanh" (`app.py:1387`, lưới hai cột, `app.py:418`): thêm HAI ô sát sau nó — "Thủy triều (cấu trúc)" và "Chu kỳ 4 giai đoạn". Mỗi ô là một dòng ngắn; chi tiết trong một khối có thể mở (pivot gần nhất ở hai cấp với `ngay_xay_ra` / `ngay_biet`, mốc phủ định, BOS / CHoCH gần nhất theo cấp, con sóng đang chạy hay vừa xong, nguồn của chu kỳ 4 giai đoạn, cờ khoá biên). Hiển thị:

- mỗi trạng thái kèm **"biết từ <ngày>"** — ngày của nến đầu tiên có thể tính ra nó, không phải ngày xảy ra;
- pivot / đỉnh–đáy tạm có chữ *tạm*;
- "chưa đủ bằng chứng" là câu trả lời hợp lệ, hiện bằng màu trung tính (`neu`), không bằng màu cảnh báo;
- giá hiển thị theo cơ sở điều chỉnh HÔM NAY của nguồn (mục 5.4).

### 7.2 Quy tắc lời

1. **Không một chữ nào hứa dự báo.** Cấm trong mọi chuỗi hiển thị của mô-đun và của khối: *sẽ*, *dự báo*, *tín hiệu mua*, *tín hiệu bán*, *khuyến nghị*, *đáng mua*, *đảo chiều chắc chắn*, *xác nhận xu hướng chính* (mô-đun một chuỗi không có xác nhận hai chỉ số). Test đọc các hằng chuỗi bằng AST (mục 8.3), có đột biến.
2. **CHoCH / BOS gọi là "cảnh báo cấu trúc"**, không gọi là "tín hiệu Dow" (NC §4.2).
3. Một dòng cố định ở chân khối: *"Đọc cấu trúc giá, không dự báo. Chưa có phép đo nào cho thấy cấu trúc này cho lợi thế; xem docs/thiet-ke-dow-cau-truc.md."* (nội dung cập nhật khi có kết cục ĐO ở mục 9 — lúc ấy thêm số ĐO và kết cục).
4. Nhãn hai cấp ghi "xấp xỉ": cấp nội bộ / cấp swing không đồng nhất với nhỏ / phụ / chính của Dow (mục 5.3).
5. Ô KHÔNG đổi điểm, `dyn_rec`, phán quyết kế hoạch, hay `result`.

### 7.3 Cửa sổ dữ liệu

`df` của biểu đồ chỉ dài ≈ 124 phiên (mục 3). Ô cấu trúc dùng cửa sổ riêng, nạp bằng cùng `load_stock_data` (cache 300 s). Độ dài cần thiết **chưa đo**: Lát 3 đếm, trên 71 mã của cache, số pivot swing đủ ở 124, ≈ 285 và 784 phiên (mô tả thuần), rồi ghim cửa sổ trước khi viết ô; nếu mã không đủ pivot thì ô nói "chưa đủ bằng chứng (cấp swing: n đỉnh, m đáy)" thay vì hạ ngưỡng.

## 8. Gác

### 8.1 Bất biến khi cắt (gác chính — chứng minh không nhìn trộm)

Khuôn đề xuất ở TR §7 mục 1. Phép thử: với MỖI `t` (không chỉ 20 điểm), `doc_cau_truc(df.iloc[:t+1])` và `doc_cau_truc(df)` phải cho nhật ký **y hệt** trên mọi dòng có `chi_so_biet ≤ t`; không dung sai, so bằng nhau chính xác. Chạy trên: (a) chuỗi tổng hợp có hạt giống cố định (bước ngẫu nhiên có cụm biến động); (b) chuỗi dựng tay có đáp số biết trước — bước ngẫu nhiên không chứng minh được rằng pivot nằm ĐÚNG chỗ; (c) ca khó: giá bằng nhau trên lưới, phiên khoá biên, phiên `volume = 0`, chuỗi ngắn hơn khởi động ATR; (d) chạy tăng dần == chạy cả bảng. Ngoài ra Tầng B (tay, trên cache thật, ghi vào STATE): cùng phép thử trên một mẫu mã, **kèm một ca đã biết** — đỉnh VN-INDEX tháng 04/2022 tra bằng lệnh trên cache, không gõ ngày vào đặc tả (SKILL, Bước 3 điều 4: máy đo bị nghi như gác).

### 8.2 Gác AST: không cửa sổ căn giữa

Đọc `ast` của `cau_truc_gia.py` (không đọc chuỗi; chú thích và docstring không lọt). Cấm: tham số `center=True`; `shift` với đối số âm hoặc `UnaryOp(USub)`; chỉ số dạng `…[t + k]` với `t` là biến vòng lặp chính; `np.roll`, `scipy.signal.argrelextrema` / `find_peaks` / `argrelmax` / `argrelmin` (đều nhìn hai phía). Khuôn lỗi thật: `smartmoneyconcepts` dùng `shift(-(N//2))` và cửa sổ lăn căn giữa (`smc.py:151–163`, TR §5.5; leader xác nhận `smc.py:155`) và hàm `market_structure_break` của PyIndicators gán pivot tại chính nến pivot (TR §5.3). Quần thể gác phải KHÁC RỖNG (lỗi 66): test tự đếm số nút AST mà nó duyệt.

### 8.3 Gác nhập: đường chấm điểm không nhập mô-đun

Khuôn `tests/test_ke_hoach_vao_lenh.py:1066–1103`:

- **Người được nhập** (danh sách đóng, đúng tên): `app.py` và dụng cụ đo của mục 9 (`tools/do_dow_cau_truc.py` — tên chốt ở Lát 4). File mới nào nhập mô-đun đều đỏ.
- **Cấm nhập** (tham số hoá): `paper_trading.py` · `paper_runner.py` · `paper_metrics.py` · `master_agent.py` · `analysis_agents.py` · `debate_agents.py` · `news_sentiment_agent.py` · `fundamental_agent.py` · `data_collectors.py` · `walkforward.py` · `sheets_store.py` · `run_daily.py` · `ke_hoach_vao_lenh.py` · `muc_fibonacci.py` · `san_dau.py` · `cham_bong.py` · `hau_kiem_loi.py` · `ban_tin.py` · mọi file dưới `backtest/`.
- **Mô-đun chỉ nhập** thư viện chuẩn, `pandas`, `numpy`, và (nhập nặng nằm trong hàm hoặc dưới `TYPE_CHECKING`) `truot_gia`, `data_quality`, `san_giao_dich`, `pha_wyckoff`, `vong_doi_lenh` (cho `khoa_bien`). Không đồng hồ (`now`, `today`), không mạng (`read_csv`, `get`, `request`, `urlopen`).
- **Ở `app.py`:** các biến nhận kết quả mô-đun chỉ xuất hiện trong khối hiển thị; không đối số của `consider_entry`, `lap_ke_hoach`, `run_full_analysis`, `ghi_*`. Gác yếu hơn các gác trên (không chứng minh được "không rò" bằng AST) và đặc tả nói thẳng điều đó.
- **Lời:** test đọc mọi hằng chuỗi hiển thị bằng AST và đòi vắng các từ cấm ở mục 7.2.

### 8.4 Kế hoạch đột biến (SKILL, Bước 3)

Mỗi gác mới đi qua `va_an_toan.dot_bien` lặp cho tới khi MỌI đột biến đều đỏ, và phát đầu tiên dựng lại NGUYÊN VĂN lỗi thật (gác đó bắt được thứ nó sinh ra để bắt chứ). Danh sách tối thiểu (mỗi dòng: đột biến → gác phải đỏ):

| # | Đột biến | Gác bắt |
|---|---|---|
| 1 | gán `ngay_biet = ngay_xay_ra` cho pivot (xác nhận ngay tại nến cực trị) | bất biến khi cắt (8.1) |
| 2 | ATR / ngưỡng dùng nến `t+1` (`shift(-1)`) | 8.2 và 8.1 |
| 3 | cửa sổ lăn `center=True` | 8.2 |
| 4 | phá mốc dùng pivot được xác nhận ở CHÍNH nến phá | test "chỉ pivot biết trước" (5.7 khoản 1) |
| 5 | `>` thành `>=` ở phép phá mốc (đóng bằng mốc thành phá) | test giá bằng (5.4) |
| 6 | bỏ dung sai nửa bước giá ở cực trị chờ | test giá bằng |
| 7 | hoán đổi BOS ↔ CHoCH | test thiên hướng (5.7 khoản 3) |
| 8 | bỏ cờ `da_pha` (một pivot phá nhiều lần) | test "một lần mỗi pivot" |
| 9 | đưa pivot CHỜ vào nhãn HH/HL | test "pivot chờ không vào nhật ký" |
| 10 | con sóng: `VÀ` thành `HOẶC` | test biên độ × thời gian |
| 11 | thủy triều chỉ cần `HH` (bỏ `HL`) | test thủy triều |
| 12 | chu kỳ: ghi đè Wyckoff bằng thủy triều khi mâu thuẫn | test "mâu thuẫn không bị ghi đè" |
| 13 | chu kỳ: suy `Tích luỹ` từ thủy triều | test "thủy triều không suy tích luỹ/phân phối" |
| 14 | bỏ cờ `khoa_bien` | test nến khoá biên |
| 15 | thêm `import` mô-đun vào `paper_trading.py` | 8.3 |
| 16 | thêm một chuỗi hiển thị chứa "dự báo" | gác lời (8.3) |

Một phát sống sót là câu trả lời: gác chưa canh chỗ đó; trước khi sửa gác, hỏi phát ấy có THẬT SỰ đổi hành vi không.

## 9. Phép đo chỉ-đọc — BẢN NHÁP KHAI TRƯỚC (CHƯA KÝ)

### 9.1 Có đưa vào `docs/TIEU-CHI-DOC-TRUOC.md` ở BƯỚC này không?

**Không. Giữ làm bản nháp trong tài liệu này; ký ở một BƯỚC riêng ngay sau khi người dùng duyệt đặc tả, TRƯỚC Lát 1.** Lý do, theo luật của chính repo:

1. `docs/TIEU-CHI-DOC-TRUOC.md` là FILE LUẬT (`tools/buoc_cham_luat.py`, `FILE_LUAT`; `SKILL.md` Quy tắc 3): BƯỚC chạm nó phải HỎI SỔ TAY thật (`cau_hoi`, `o_thoat`, kết quả). BƯỚC này không đổi luật nào; chạm file ấy làm nó mất tư cách `khong_bat_buoc_vi` mà không đem lại gì.
2. Khuôn ký của repo là: người dùng duyệt bản nháp (*"Duyệt cả bản nháp (Recommended)"* — ĐO 32, `docs/TIEU-CHI-DOC-TRUOC.md`), sổ tay hỏi thật TRƯỚC commit ký, rồi ký ở **MỘT COMMIT RIÊNG, TRƯỚC khi có mã và lượt chạy** (ĐO 32, đầu mục). Người dùng chưa duyệt bản nháp; ký trước khi duyệt là đóng đinh một văn bản có thể đổi theo câu trả lời ở mục 14.
3. Mục `## ĐO n` phải mang `**Đã tra trùng:**` hoặc `**Không khai được là đã tra vì:**` (`tests/test_do_phai_khai_da_tra.py`); phần tra trùng ở dưới đã làm ở phiên này nhưng phải được làm lại lúc ký (cây `main` sẽ đã đổi).

**Hệ quả sắp xếp:** vì khai TRƯỚC mã là điều ĐO 32 đã làm, chuỗi BƯỚC là: duyệt đặc tả → BƯỚC khai ĐO (sổ tay hỏi thật, commit riêng) → Lát 1 → Lát 2 → Lát 3 → Lát 4 (chạy). Giữa lúc khai và lúc chạy, các lát dựng mô-đun chỉ được in số MÔ TẢ (độ trễ, số sự kiện, tỷ lệ nhấp nháy) — **không đọc lợi nhuận** (bất biến 7).

### 9.2 Bản nháp khai trước

> **Số hiệu.** `ĐO <n>` — số lớn nhất hiện có trong `docs/TIEU-CHI-DOC-TRUOC.md` là ĐO 33 (`grep -n "^## ĐO" docs/TIEU-CHI-DOC-TRUOC.md`, 29/10/2026); đọc lại số lớn nhất LÚC KÝ, không giữ 34.
> **Họ thử.** Một họ riêng (cấu trúc giá), KHÔNG cùng họ ba phép ĐO 31–33 của sổ ảo. Phép đo THĂM DÒ (`docs/LO-TRINH.md` C2: không tính K, không bao giờ lên bản); không đổi đường chạy thật.

**Câu hỏi.** Nếu giữ một mã khi và chỉ khi thủy triều cấp swing (mục 5.8) là `tang` — biết tới hết nến `t`, vào ở giá mở cửa phiên `t+1`, ra khi điều kiện hết — thì lợi nhuận mỗi ngày của danh mục đó, trừ phần rổ cùng mức đầu tư, đổi bao nhiêu so với (i) cầm rổ, (ii) luật SMA200, (iii) luật time-series momentum, (iv) vào–ra ngẫu nhiên cùng thời gian nắm giữ — sau phí? Và CHoCH cấp swing có đi kèm lợi nhuận kế tiếp khác ngày ngẫu nhiên cùng mã cùng tháng không?

**Giả thuyết (đều là giả thuyết KHÔNG, phép đo có thể bác nó, và kết cục "không phân biệt được" là bình thường).**
- **H1 (trạng thái):** Δ = trung bình `x_t` của danh mục "thủy triều swing = tăng" ≠ 0 so với từng chuẩn (i)–(iv).
- **H2 (sự kiện):** sau CHoCH-lên cấp swing, lợi nhuận mã trừ rổ trong 21 phiên (từ mở cửa `t+1`) khác ngày ngẫu nhiên cùng mã cùng tháng lịch; sau CHoCH-xuống thì ngược lại. Chỉ ĐỌC lợi nhuận, không có vị thế bán khống (khả năng bán khống của nhà đầu tư cá nhân trên sàn VN chưa được nguồn nào xác nhận — NC §8 cuối).
- **H3 (mô tả, KHÔNG có suy diễn thống kê):** VN-INDEX như MỘT chuỗi: đếm sự kiện cấp swing và độ trễ. Cổ điển Dow cho ≈ một tín hiệu mỗi 1–3 năm mỗi chỉ số, nên lực rất thấp (NC §8 "Baselines and hygiene").

**Quần thể và cửa sổ.** 71 mã của `vn100_symbols.CUSTOM_WATCHLIST_SYMBOLS` (`vn100_symbols.py:28`), cache giá `acf6dca1…` (băm đọc lại LÚC KÝ bằng `tools/do25_ke_hoach_vao_lenh.py::bam_thu_muc`). Vùng đọc kết cục chính: với mỗi mã, các phiên có `time` < mốc của mã trong `docs/moc_du_lieu_sach.json` (`moc_theo_ma`) — vùng mà các vòng tối ưu của dự án chưa thể nhìn (bất biến 8); các phiên trước vùng ấy dùng làm KHỞI ĐỘNG của bộ dò, không tính lợi nhuận. Vùng sau mốc báo RIÊNG, ghi "đã nhìn bởi các vòng tối ưu khác"; không gộp. Kết cục chính chỉ đọc MỘT LẦN. (Cache là ảnh chụp rổ hiện tại, nên có thiên lệch sống sót: nó thổi kỳ vọng, không thổi alpha khớp mức — NGUYEN-TAC-DO-LUONG.md, bảng "chỗ hỏng âm thầm".)

**Luật ghim (một giá trị cho mỗi tham số; ĐO không thử giá trị khác).**
- Mặc định hiển thị: ATR(14) `(k_nội bộ, k_swing) = (2, 4)`; con sóng 3/8 VÀ 10 phiên (mục 5.3, 5.8). **Lợi nhuận chính (H1, H2) chỉ đọc ở mặc định.** Mọi ô còn lại của lưới (mục 5.3: 10 ô; con sóng: 18 ô, chỉ để ĐẾM) báo ĐỦ trong phụ lục, kèm câu "ô tốt nhất không phải một kết quả"; không ô nào được dùng để đổi mặc định.
- Vào lệnh: mở cửa phiên `t+1`; ra: mở cửa phiên sau phiên điều kiện hết. Khớp bằng cùng cơ chế sổ ảo cho các ràng buộc đã đo: nến kịch trần một giá thì lệnh mua huỷ; ra gặp kịch sàn thì chờ phiên mở khoá (`vong_doi_lenh.khoa_bien`, NGUYEN-TAC-DO-LUONG.md bất biến 3).
- Phí: `paper_metrics.ROUND_TRIP_COST_PCT` mỗi vòng, và một lượt độ nhạy ở 0,76% (cận trên của dải bán lẻ, `CLAUDE.md`); trượt giá bước giá theo `truot_gia` như tầng 2.
- Mỗi mã nặng `1/71` khi đang giữ (không đòn bẩy, mức đầu tư `e_t ≤ 1`); phần còn lại là tiền mặt.
- Chuẩn: (i) rổ đều trọng số 71 mã, không phí ngoài một vòng mua đầu và bán cuối; (ii) mã giữ khi đóng cửa > SMA200 của chính nó, biết tới hết `t`; (iii) trọng số mỗi mã = trung bình của dấu lợi nhuận 21, 63, 252 phiên, cắt về [0, 1] — dạng long-only của tín hiệu 1/3/12 tháng (Hurst–Ooi–Pedersen, NC §3.4, §8); (iv) vào–ra ngẫu nhiên: cho mỗi mã, cùng số khoảng nắm giữ và cùng độ dài từng khoảng, đặt ở ngày bắt đầu ngẫu nhiên, 1.000 lượt rút, **kèm** một lượt bản đồng bộ thời gian (dịch vòng chuỗi trạng thái của mã đi một số phiên ngẫu nhiên ≥ 252) để cắt bỏ phần "đúng thời điểm" nhưng giữ cấu trúc kéo dài.
- Thước đo chính: `x_t = r_t(danh mục) − e_t × r_t(rổ)` (khuôn thước 1 của `docs/thiet-ke-c1-san-dau.md` mục 8.2), cộng dồn ở điểm phần trăm vốn. Cột thô `r_t(danh mục) − r_t(rổ)` LUÔN in cạnh. Đối tượng sánh với alpha từng lệnh (`paper_metrics.vs_benchmark`) báo thêm, tách riêng (mẫu = khoảng nắm giữ; hai đối tượng KHÁC nhau, không đối chiếu KTC với nhau).
- KTC: bootstrap khối vòng CÓ CẶP, khối 10 phiên, 5.000 lượt rút, khoảng phân vị 2,5–97,5, hạt giống cố định 0 (khuôn C1, `docs/thiet-ke-c1-san-dau.md` mục 8.3–8.4), dùng lại HÀM KTC của Lát 3 sân đấu khi đã vào `main`; nếu chưa vào thì ĐO chờ, **không viết bản sao thứ hai**. Độ phủ đo bằng mô phỏng trước khi in "95%" (cùng mục 8.4).
- H2 dùng KTC theo cụm ngày (sự kiện cùng ngày giữa các mã tương quan với nhau bởi yếu tố thị trường); chuẩn = ngày ngẫu nhiên cùng mã cùng tháng lịch (kiểm soát chế độ thị trường), 1.000 lượt rút.

**Đối chứng của máy đo (trượt thì K0).**
- (i) Luật "luôn giữ" = cầm rổ trừ đúng MỘT vòng phí mỗi mã (đồng nhất thức).
- (ii) Hạt ngẫu nhiên: chuẩn (iv) đồng bộ thời gian cho kỳ vọng ≈ lợi nhuận thị trường trong khoảng 2 sai số chuẩn của chính nó.
- (iii) **Tiêm lợi thế giả** (khuôn BƯỚC 113, lỗi 99): thêm vào lợi nhuận một lợi thế bằng nửa rào hoà vốn của luật đang đo, vào các ngày trạng thái = tăng; phép đo phải bắt được ở tỷ lệ ≥ 80% trên 30 lượt lặp (không phải một lượt — lỗi 99). Nếu không bắt được, phán quyết "không tín hiệu" ở lực đó là vô nghĩa và báo thẳng.
- (iv) **Ca thật đã biết:** trên một mã, tái dựng thủ công 3 pivot / 1 CHoCH bằng cách đọc bảng giá, rồi đối chiếu với nhật ký của mô-đun từng dòng.
- (v) Phép thử bất biến khi cắt ở mục 8.1 xanh trên cache thật cho cả 71 mã.
- (vi) Băm cache trước và sau lượt chạy bằng nhau.

**Thống kê chính.** Δ_(i) = trung bình `x_t` của danh mục Dow − của chuẩn (i), tương tự (ii), (iii); phần trăm các lượt rút ngẫu nhiên (iv) mà Dow thắng; số khoảng nắm giữ; số sự kiện CHoCH-lên / xuống; tất cả kèm KTC và nhãn độ phủ.

**Kết cục (ký trước).** Ngưỡng SUY RA lúc chạy từ nửa bề rộng KTC của chuẩn (i) (cách ĐO 30–33): nhỏ = một nửa, lớn = một lần.
- **K0:** một đối chứng (i)–(vi) trượt.
- **A — không phân biệt được:** |Δ_(i)| ≤ ngưỡng nhỏ, hoặc KTC của Δ_(i) chứa 0 VÀ cả hai Δ_(ii), Δ_(iii) chứa 0. **Đây là kết cục MẶC ĐỊNH được kỳ vọng.** Hành động: ghi STATE; ô giữ nguyên "chỉ để hiện".
- **A⁺ — tốt hơn vừa:** ngưỡng nhỏ < Δ_(i) ≤ ngưỡng lớn, KTC loại 0, và Dow thắng ≥ 95% lượt rút (iv), và Δ_(ii) hoặc Δ_(iii) cũng loại 0. Hành động: báo người dùng; KHÔNG tự khai ứng viên tầng 3.
- **B — Quy tắc 1:** Δ_(i) > ngưỡng lớn. Giả định CÓ LỖI: soát phép thử bất biến khi cắt (8.1), phân bố độ trễ, và tìm nhìn trộm (mô-đun hay máy đo) TRƯỚC khi đọc tiếp; báo người dùng.
- **C — xấu đi:** Δ_(i) < −ngưỡng nhỏ, KTC loại 0. Ghi STATE; ý gác lại.
- KTC của chuẩn (i) chứa 0 hay không, và ngưỡng IS khác nhau — báo kèm.

**Báo kèm (không quyết định kết cục).** Toàn lưới 10 ô × H1 / H2; bản không có sự kiện nến khoá biên; phép cắt râu nến (R9); phép cắt khối lượng (R8: khối lượng nhịp lên so nhịp xuống chia trung bình 60 phiên, NC §8 R8); độ trễ `chi_so_biet − chi_so_xay_ra` (trung vị, phân vị 90) mỗi cấp; số sự kiện mỗi mã mỗi năm; tỷ lệ sự kiện lật lại trong 3 phiên (TR §7 mục 3–4); vùng sau mốc sạch.

**Điều ĐO này KHÔNG làm.** Không đổi đường chạy thật, sổ thật, điểm, ngưỡng, hay `pha_wyckoff`. Không thử tham số khác sau khi ký. Không bán khống. Không phần hai chỉ số (mục 10). Không đọc sổ thật. Không đọc lợi nhuận trước ngày ký và trước khi 8.1 xanh trên cache thật.

**Đã tra trùng (làm lại lúc ký).** Ở phiên viết bản nháp (29/10/2026): `git grep -i -I "swing\|zigzag\|fractal\|choch\|break of structure\|dow theory" -- '*.py' '*.md'` ngoài `tests/` — 0 dòng; `git log --all -i --grep "swing\|choch\|dow theory\|zigzag\|market structure"` — năm commit, không cái nào về cấu trúc đỉnh–đáy (chúng khớp chữ "cấu trúc giá" của `pha_wyckoff` và Fibonacci). Tiền lệ gần nhất: BƯỚC 223 (ĐO 31, momentum đặc thù 12 tháng làm bộ lọc — kết cục A) cho chuẩn kiểu momentum; BƯỚC 179 (ĐO 25) cho cách đo theo MỖI TÍN HIỆU. Không có phép đo nào của dự án về xu hướng kiểu Dow, SMA200 như luật vào lệnh, hay time-series momentum như luật vào lệnh. Điểm xu hướng của `TrendAgent` đã được đo là một thành phần của điểm cuối (rho = −0,028, KTC [−0,104 ; +0,064], `MO-XE-KIEN-TRUC.md`) — khác đối tượng.

## 10. PHẦN 2 — mức thị trường (nguyên lý hai chỉ số): ĐỂ SAU, kiểm trước

Dow đòi hai chỉ số xác nhận nhau (mục 4.5). Với một chuỗi giá duy nhất, phần này không làm được; nó nằm ngoài các lát ở mục 11. Cần kiểm TRƯỚC khi thiết kế:

1. **Chuỗi nào lấy được qua vnstock.** `market_filter.get_vni_df` chỉ nạp `VNINDEX` (`market_filter.py:189–196`). Chưa biết nguồn có trả `VN30`, `VNMidcap`, `VNSmallcap`, và các chỉ số ngành (`VNFIN`, `VNREAL`, `VNIT`, nêu tên ở NC §6.3) với lịch sử đủ dài và đúng nhãn hay không. Lệnh kiểm viết ở phần mở đầu của PHẦN 2, và hạng gói phải ĐỌC (`vnstock_goi.kiem_goi`), không suy. Lưu ý: `backtest/data.py:45–51` giữ `VN30_SNAPSHOT` là **rổ mã** (ảnh chụp 08/2026, có thiên lệch sống sót), không phải chuỗi chỉ số.
2. **VN30 gần như trùng VN-INDEX.** Số liệu tin tức: VN30 ≈ 59% vốn hoá thị trường, Vingroup ≈ 23% vốn hoá thị trường và 39,5% VN30 (NC §6.3). **CHƯA XÁC MINH** — chênh lệch định nghĩa; nếu đúng thì "xác nhận" giữa hai chuỗi gần như tầm thường. Ứng viên chuỗi thứ hai thông tin hơn: VNMidcap / VNSmallcap hoặc tách ngành (NC §6.3). Không nguồn nào xác lập một tương đương "Vận tải" cho Việt Nam.
3. Độ rộng thị trường (tỷ lệ mã trên MA) KHÔNG phải của Dow (NC §6.3); dự án đã có `do_rong.py` (ĐO 32) — nếu dùng thì gọi đúng tên.
4. Luật hai chỉ số (NC §8 R5, R6) có cửa sổ lệch `w ∈ {0, 5, 10, 21, không giới hạn}` giữa hai lần phá mốc — lưới thêm; lực rất thấp (một tín hiệu mỗi 1–3 năm).

Việc đầu của PHẦN 2 là lệnh kiểm mục 1 (không viết mã giao dịch, không đọc kết cục); nó chỉ được mở khi người dùng muốn (mục 14, câu 4).

## 11. Các lát cắt, mỗi lát một BƯỚC, `Mốc:` theo mục 14 câu 2 (thứ tự đã chốt: Lát 0b trước Lát 1)

Số BƯỚC do leader cấp lúc giao việc. Mỗi lát qua năm cổng, đột biến mọi gác, PR riêng. **Đặc tả này (BƯỚC 244) là lát 0.**

**Lát 0b — khai ĐO (không mã).** Ký mục 9.2 vào `docs/TIEU-CHI-DOC-TRUOC.md` ở một commit RIÊNG, sau khi người dùng duyệt bản nháp; sổ tay hỏi thật; làm lại phần tra trùng; số `ĐO n` đọc lúc ký. *Xong khi:* mục ĐO có `**Đã tra trùng:**`, `tests/test_do_phai_khai_da_tra.py` xanh, sổ tay có mục thật, và (nếu người dùng chọn) mốc B5 / dòng LO-TRINH thống nhất.

**Lát 1 — lõi pivot + nhật ký + bất biến khi cắt.** `cau_truc_gia.py` với bộ dò ATR (mặc định) và hai họ còn lại ở mức tối thiểu để lưới tồn tại; hai cấp; hai thời điểm; xen kẽ; nhãn HH/HL/LH/LL; giá bằng; cờ khoá biên / không giao dịch; **chưa có** BOS/CHoCH, trạng thái Dow, chu kỳ, app. Gác 8.1, 8.2 và 8.3 (phần nhập mô-đun). Dụng cụ `tools/` chỉ-đọc in MÔ TẢ trên cache: phân bố độ trễ mỗi cấp, số pivot mỗi mã mỗi năm, số ca giá bằng / gần-bằng-giá, số nến khoá biên và không giao dịch (KHÔNG đọc lợi nhuận). *Xong khi:* 8.1 xanh trên chuỗi tổng hợp và trên cache thật (Tầng B, ghi STATE); mọi đột biến mục 8.4 thuộc Lát 1 (1, 2, 3, 5, 6, 9, 14) đỏ; số ca giá bằng đã đếm và quyết định "nửa bước giá có đủ" ghi STATE; không dòng nào trong `paper_*`, `pha_wyckoff.py` đổi.

**Lát 2 — sự kiện và trạng thái Dow, chu kỳ 4 giai đoạn.** BOS / CHoCH / KHOI_DAU theo cấp; thủy triều, mốc phủ định, con sóng; `ghep_chu_ky`. *Xong khi:* 8.1 mở rộng cho sự kiện và trạng thái xanh; đột biến còn lại ở 8.4 (4, 7, 8, 10, 11, 12, 13) đỏ; ca dựng tay có đáp số biết trước cho từng nhánh `ghep_chu_ky` (kể cả pha B → chưa đủ bằng chứng, pha E mâu thuẫn thủy triều); số liệu mô tả mới (số sự kiện mỗi mã mỗi năm, tỷ lệ lật lại trong 3 phiên) ghi STATE.

**Lát 3 — ô trên app.** Hai ô cạnh "Pha Wyckoff", khối chi tiết, cửa sổ dữ liệu riêng (mục 7.3), gác lời (8.3) và gác nhập cho `app.py`. *Xong khi:* bảng đếm pivot swing ở ba cửa sổ ghi STATE và cửa sổ đã ghim; gác lời xanh với đột biến 16; chụp màn hình ô ở `http://localhost:8511/` (lưu ý: app của người dùng chạy repo chính, không phải worktree); mở app trên một mã có kết luận và một mã "chưa đủ bằng chứng".

**Lát 4 — dụng cụ ĐO và lượt chạy.** `tools/do_dow_cau_truc.py` (tên chốt lúc này) theo mục 9.2; chuẩn (i)–(iv); đối chứng (i)–(vi); chạy MỘT lần trên vùng sạch. *Xong khi:* đối chứng xanh; kết cục (K0 / A / A⁺ / B / C) ghi `docs/STATE.md`; ô trên app cập nhật dòng chân khối kèm số ĐO và kết cục; **nếu kết cục B → dừng và soát theo Quy tắc 1 trước mọi việc khác**.

Lát 3 độc lập với Lát 4 về mã; thứ tự là để người dùng có thể xem ô trước khi có số đo, như Wyckoff và Fibonacci.

## 12. Skill `.claude/skills/dow-theory-analysis/SKILL.md`

Người dùng soạn bản nháp (`C:\Users\cuong\OneDrive\Desktop\dow-theory-analysis\SKILL-dow-theory-analysis.md`); bản trong repo được viết lại từ đó theo NC §7 và §9, ghi nguồn bản gốc. Những sửa đã làm (bảng chi tiết: NC §7):

- bỏ hoặc gắn nhãn các con số KHÔNG có nguồn (bản nháp :147 "20%–30%", :150 "2–6 tuần", :151 "xác suất rất cao");
- sửa "Non-confirmation + Failure Swing": non-confirmation là bất đồng giữa HAI chỉ số (Hamilton tr. 6); "failure swing" là thuật ngữ RSI của Wilder (1978), không có trong Nelson hay Hamilton, xếp hạng "tin cậy cao nhất" không có nguồn;
- 3/8 (Dow) và 1/3–2/3 (Rhea) thay cho "= Fibonacci 38,2–61,8%";
- thanh toán T+2 (cổ phiếu bán được từ chiều T+2 kể từ 29/08/2022; NC §6.2) thay cho chữ không có nguồn;
- Dow không định nghĩa pha "smart money"; Rhea nêu ba giai đoạn khác (tin tưởng hồi phục · đáp ứng lợi nhuận · đầu cơ), và câu chuyện "người hiểu biết mua lặng lẽ" trong Nelson là lời một người chào hàng (NC §5 dòng 3);
- khối lượng là nguyên lý YẾU (Hamilton tr. 177);
- chỉ cặp "line ≈ vùng giao dịch Wyckoff" có nguồn; mọi tương ứng khác ghi là LOẠI SUY;
- "chỉ giá đóng cửa" là thực tế dữ liệu thời Dow, không phải luật bỏ râu nến;
- luật pivot khớp với mô-đun (mục 5);
- `description` thu hẹp vào từ khoá riêng của Dow để không tranh với các skill SMC / Wyckoff của người dùng về BOS / CHoCH; thứ bậc: **Dow = thủy triều; Wyckoff / SMC là chi tiết bên dưới; Fibonacci dưới cùng**.

**Công cụ của repo yêu cầu gì cho một skill thứ hai (đã kiểm):**
- `tests/test_skill_quy_trinh.py::test_CHI_CO_MOT_skill_quy_trinh` khẳng định `.claude/skills/*/SKILL.md` có ĐÚNG một skill — thêm skill Dow làm nó đỏ.
- `tools/cua_mo_phien.py:75–80` (`ten_skill`) đọc mọi `SKILL.md` dưới `.claude/skills/` và bản tin mở phiên in từng tên là *"QUY TRÌNH BẮT BUỘC — gọi skill `<tên>` TRƯỚC khi đọc hay sửa file đầu tiên"* (`cua_mo_phien.py:264–267`) — nghĩa là skill Dow sẽ bị gọi nhầm là quy trình bắt buộc ở MỌI phiên.
- Cách xử lý trong BƯỚC này: một danh sách đóng `SKILL_PHU` ở `tools/cua_mo_phien.py` khai các skill KHÔNG phải quy trình; `ten_skill()` loại chúng; test "chỉ một skill quy trình" đếm phần còn lại, và có thêm test cho mỗi skill phụ (frontmatter hợp lệ, `description` không tự nhận là quy trình, vắng các câu sai đã bác). Skill phụ mới mà chưa khai thì test đỏ (an toàn theo chiều ồn ào). Chỉ `quy-trinh-lam-viec` vẫn là file luật (`tools/buoc_cham_luat.py`, `FILE_LUAT`); skill Dow KHÔNG phải file luật.

## 13. Không làm

- Không đưa mô-đun vào điểm, ngưỡng, cổng mở lệnh, kế hoạch vào lệnh, hay sổ ảo; không dùng nó làm bộ lọc của bất kỳ ứng viên tầng 3 nào (đó là một ĐO riêng + người dùng duyệt).
- Không sửa `pha_wyckoff.py`, `muc_fibonacci.py`, `analysis_agents.py`.
- Không thêm sự kiện Wyckoff (LPS, LPSY, ST, tái tích luỹ / phân phối).
- Không cài, không nhập `smartmoneyconcepts`, PyIndicators hay mã LuxAlgo; không chép mã từ repo ngoài (TR §5; giấy phép LuxAlgo CC BY-NC-SA 4.0, Kaltsit không giấy phép).
- Không phần hai chỉ số; không "line" / vùng đi ngang kiểu Hamilton (luật R6 cần hai chỉ số, NC §8).
- Không bán khống trong phép đo; không tối ưu tham số trên kết quả; không chọn ô tốt nhất của lưới.
- Không đọc lợi nhuận của luật này trước khi khai ĐO được ký.
- Không điều chỉnh giá trong mô-đun.
- Không nói "tín hiệu Dow" cho một chuỗi giá đơn lẻ.

## 14. Câu hỏi mở — ĐÃ CHỐT 29/10/2026

Bản đầu của đặc tả (29/10/2026) để bảy câu mở, mỗi câu một khuyến nghị. Leader chuyển câu trả lời của người dùng cùng ngày. Bảng dưới ghi **quyết định** (bốn câu có trích nguyên văn; ba câu còn lại người dùng không phản đối khuyến nghị được đặt làm mặc định — đó KHÔNG phải một trích dẫn) cạnh **đề xuất ban đầu** ở danh sách ngay sau; từ đây chỉ quyết định có hiệu lực.

| # | Quyết định | Nguồn |
|---|---|---|
| 1 | Ký ĐO ở một BƯỚC riêng, TRƯỚC Lát 1 (mục 9.1 và 11: Lát 0b) | *"BƯỚC riêng ngay sau khi duyệt, trước Lát 1 (Recommended)"* |
| 2 | Tạm mượn mốc **B5**; thêm MỘT dòng riêng cho việc này ở lần sửa `docs/LO-TRINH.md` kế | khuyến nghị đặt làm mặc định, người dùng không phản đối (không phải trích dẫn) |
| 3 | Ô chỉ nói cấp swing + chu kỳ 4 giai đoạn; cấp nội bộ và BOS / CHoCH nội bộ nằm trong phần mở rộng (mục 7.1) | *"Swing + chu kỳ trên ô, Internal trong phần mở rộng (Recommended)"* |
| 4 | PHẦN 2 (hai chỉ số) sau khi có kết cục ĐO phần một (mục 10) | *"Sau khi có kết quả ĐO phần 1 (Recommended)"* |
| 5 | Giữ mặc định ATR (2,4) và con sóng 3/8 VÀ 10 phiên (mục 5.3, 5.8) | *"Giữ (Recommended)"* |
| 6 | Phép đo chỉ mua / đứng ngoài, không bán khống (mục 9.2) | khuyến nghị đặt làm mặc định, người dùng không phản đối (không phải trích dẫn) |
| 7 | Chấp nhận danh sách đóng `SKILL_PHU` (mục 12) | khuyến nghị đặt làm mặc định, người dùng không phản đối (không phải trích dẫn) |

Hệ quả cho các lát (mục 11): Lát 0b (khai ĐO, sổ tay hỏi thật, commit riêng) đứng TRƯỚC Lát 1; ô ở Lát 3 chỉ hiện cấp swing + chu kỳ, khối mở rộng chứa cấp nội bộ; PHẦN 2 không có lát nào cho tới khi ĐO phần một có kết cục. Đề xuất ban đầu, giữ làm lịch sử:

1. **Khi nào ký ĐO?** (a) BƯỚC riêng ngay sau khi duyệt đặc tả, TRƯỚC Lát 1 *(khuyến nghị — đúng khuôn ĐO 32: khai trước mã, commit riêng)*; (b) gộp với Lát 4; (c) bỏ phép đo, chỉ hiện.
2. **Mốc trong `docs/LO-TRINH.md`.** (a) Tạm mượn **B5** (hiện cấu trúc, chỉ để hiện) và thêm MỘT dòng mới cho việc này ở lần sửa `LO-TRINH.md` kế — nó đã có hai ghi chú chờ gộp (`docs/HANDOFF.md` mục 5: dòng B1; "C kéo sớm"); file luật nên cần sổ tay hỏi thật, vì thế không sửa riêng *(khuyến nghị)*; (b) sửa `LO-TRINH.md` ngay trong BƯỚC khai ĐO; (c) ghi `quy-trinh — …` (không khớp bản chất).
3. **Hiển thị hai cấp.** Ô ngắn chỉ nói cấp swing + chu kỳ 4 giai đoạn; cấp nội bộ và BOS / CHoCH nội bộ nằm trong khối mở *(khuyến nghị — cấp nội bộ nhiều và nhiễu)*; hay hiện cả hai cấp ngay trên ô.
4. **PHẦN 2 (hai chỉ số) bao giờ?** (a) Sau khi có kết cục ĐO phần một; chỉ mở lệnh kiểm chuỗi vnstock (mục 10 khoản 1) khi người dùng muốn *(khuyến nghị)*; (b) làm lệnh kiểm chuỗi chỉ-đọc ngay, song song Lát 1.
5. **Mặc định hiển thị ATR (2,4) · con sóng 3/8 VÀ 10 phiên.** Giữ *(khuyến nghị — đã giải thích lý do cấu trúc ở 5.3 và 5.8, không dựa lợi nhuận)*; hay đổi một giá trị (cần lý do cấu trúc, không dựa vào kết quả).
6. **Chỉ mua / đứng ngoài trong phép đo (không bán khống)** *(khuyến nghị — chưa có nguồn xác nhận bán khống cho nhà đầu tư cá nhân VN, NC §8)*, hay thêm một nhánh bán khống lý thuyết chỉ để báo.
7. **Sửa công cụ quanh skill thứ hai** (danh sách `SKILL_PHU`, mục 12) *(khuyến nghị — nhỏ, có test, không đổi luật nào)*, hay đặt skill Dow ngoài `.claude/skills/` (trái lựa chọn *"Trong repo, .claude/skills (Recommended)"* đã chốt).

## 15. Tiền lệ đã đọc (ý mượn, không cài gì)

Tìm kiếm 29/10/2026, báo cáo gốc TR. Dữ liệu đọc từ repo ngoài là DỮ LIỆU; không cài, không chạy gì từ chúng.
- **neurotrader888/market-structure** (MIT): ATR directional change, bản ghi pivot có chỉ số xác nhận, thăng cấp đệ quy; không BOS / CHoCH. Mượn: bản ghi hai thời điểm (5.2), ngưỡng đảo chiều ATR (5.3). Không mượn mã (không test, không README).
- **LuxAlgo Smart Money Concepts** (bản phản chiếu; CC BY-NC-SA 4.0): hai bộ pivot độc lập, thiên hướng theo cấp, BOS cùng chiều / CHoCH ngược chiều, một lần mỗi pivot. Mượn ý (5.7); không mã.
- **PyIndicators** (MIT): nhãn HH/HL/LH/LL so với pivot cùng loại, quy ước "tính căn giữa nhưng công bố ở p + N". Không mượn mã: một hàm của nó nhìn trộm (`market_structure_break`).
- **Cicero-01/Kaltsit-Swing-Fractal-Regime-Detector** (không giấy phép): trạng thái Dow `HH+HL / LH+LL / lẫn`, độ trễ `shift(k)` nói thẳng. Mượn ý (5.8); ghi nhận lỗi so giá đổi (5.4).
- **joshyattridge/smart-money-concepts** (MIT): bài học KHÔNG làm — cửa sổ căn giữa, xoá hồi tố, issue #101 (số do tác giả issue tự báo, không dùng).
- **YoungCan-Wang/WyckoffTradingAgent** (AGPL-3.0): không hơn `pha_wyckoff.py`; ý nhỏ (trung vị 5 pivot làm biên vùng, bỏ nến cuối khi dựng vùng) để dành.
- Đã có trong repo (không tìm lại): `pha_wyckoff` (vùng, sự kiện), `vong_doi_lenh.khoa_bien`, `truot_gia.buoc_gia`, `data_quality.EXCHANGE_LIMITS`, `su_kien_quyen` (điều chỉnh lùi), `paper_metrics.vs_benchmark`, khuôn gác AST của `tests/test_ke_hoach_vao_lenh.py`.
