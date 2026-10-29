---
name: dow-theory-analysis
description: Đọc và giải thích Lý thuyết Dow (Charles Dow, Hamilton, Rhea) — thủy triều, con sóng, gợn sóng; xu hướng chính và xu hướng phụ; chuỗi đỉnh–đáy kiểu Dow; hai chỉ số phải xác nhận nhau; "xu hướng chính đã đổi chiều chưa" theo Dow. Dùng khi người dùng nhắc Dow Theory, Charles Dow, Hamilton, Rhea, primary / secondary trend, thủy triều – con sóng – gợn sóng. KHÔNG dùng cho BOS, CHoCH, order block, FVG (thuộc skill SMC) hay pha tích lũy / phân phối / Spring / UTAD (thuộc skill Wyckoff) khi câu hỏi không nhắc Dow. Đây là skill đọc cấu trúc, không phải quy trình làm việc của repo (quy trình là skill quy-trinh-lam-viec).
---

# Lý thuyết Dow — đọc đúng nguồn, nói đúng độ tin

> **Nguồn gốc bản này.** Bản nháp do **người dùng soạn** (`SKILL-dow-theory-analysis.md`, 29/10/2026). Bản trong repo là bản đã **sửa theo báo cáo nghiên cứu 29/10/2026** (BƯỚC 244; đọc nguyên văn Nelson 1902 và Hamilton 1922, các nguồn thứ cấp được gắn nhãn). Đặc tả mô-đun đọc cấu trúc: `docs/thiet-ke-dow-cau-truc.md`. **Mô-đun ấy chưa có mã** — không nói với người dùng rằng app đang hiện thủy triều hay con sóng cho tới khi nó vào `main`.

## 0. Thứ bậc khi trả lời

**Dow = thủy triều** (hướng lớn, đọc ở khung ngày / tuần). Wyckoff và SMC là chi tiết BÊN DƯỚI nó (vùng giá, sự kiện, điểm vào). Fibonacci nằm dưới cùng và không tự kết luận hướng. Câu hỏi thuần về BOS / CHoCH hay thuần về pha Wyckoff thì để skill tương ứng trả lời; skill này chỉ chen vào để nói **thủy triều đang ở đâu** và **bằng chứng ở mức nào**.

Dự án này **không đặt lệnh thật** và cấu trúc Dow ở đây là **CHỈ ĐỂ HIỆN**: chưa có phép đo nào cho thấy nó có lợi thế (đặc tả mục 9). Đừng viết câu có tính dự báo.

## 1. Ba nhãn nguồn — gắn vào MỌI khẳng định

- **[Dow]** — Charles Dow, xã luận 1900–02 (Nelson, *The ABC of Stock Speculation*, 1902). Nguồn gốc.
- **[Hamilton]** — *The Stock Market Barometer*, 1922. Nguồn gốc, thế hệ sau; có phần Dow không viết.
- **[Rhea / hiện đại]** — Rhea 1932, Schannep 2008, Murphy: chỉ đọc qua trích dẫn thứ cấp. Mọi thứ ở đây là **cách đọc của người đi sau**, không phải lời Dow.
- **[loại suy]** — tương ứng sang Wyckoff / SMC mà **chưa nguồn nào xác nhận**.

## 2. Ba chuyển động — độ dài KHÔNG thống nhất giữa các nguồn

| | Dow 1902 | Hamilton 1922 | Rhea (thứ cấp) |
|---|---|---|---|
| **Chính** (thủy triều) | "ít nhất bốn năm" / 4–6 năm | "một đến ba năm" | — |
| **Phụ** (con sóng) | 10–60 ngày, trung bình 30–40 | vài ngày đến nhiều tuần | 3 tuần – 3 tháng |
| **Nhỏ** (gợn sóng) | biến động hằng ngày | biến động hằng ngày | — |

Không nguồn nào nói "xu hướng chính kéo dài vài tháng". Hỏi độ dài thì nêu CẢ HAI cách đọc và nói chúng khác nhau.

**Biên độ con sóng:** [Dow] ít nhất **3/8 (37,5%)** của nhịp chính (xã luận 20/07/1901, nói trước hết về cổ phiếu riêng — quy tắc kinh nghiệm, không phải thống kê hiệu chỉnh); [Rhea, thứ cấp] **1/3 – 2/3**; [Schannep, thứ cấp] hơn 3% và cỡ 8 phiên. **Đây không phải mức Fibonacci 38,2 / 61,8%**: 1/3 và 2/3 không bằng chúng, và Nelson lẫn Hamilton không nhắc Fibonacci. Rhea tự nhận chưa hai người nào chọn con sóng giống nhau.

## 3. Các nguyên lý — nguồn nào nói gì

1. **Thị trường phản ánh tất cả.** Có trong truyền thống Dow; ở lượt nghiên cứu này chưa kiểm câu chữ của nguồn cho nguyên lý riêng này. Dùng như tiền đề, đừng trích dẫn.
2. **Ba chuyển động.** [Dow] xem mục 2.
3. **Xu hướng chính có ba giai đoạn.** [Rhea, qua Brown–Goetzmann–Kumar] ba giai đoạn của một thị trường tăng là *tin tưởng hồi phục → đáp ứng lợi nhuận cải thiện → đầu cơ / lạm phát*. **Đó KHÔNG phải "smart money tích luỹ → công chúng → phân phối".** Câu chuyện người hiểu biết mua lặng lẽ rồi bán cho đám đông xuất hiện trong Nelson chỉ ở một đoạn do Nelson gán cho **một người chào hàng**, không nằm trong các chương của Dow. Chu kỳ tích luỹ – markup – phân phối – markdown là khung **Wyckoff**, tách riêng.
4. **Hai chỉ số phải xác nhận nhau.** [Hamilton] (không có trong các xã luận của Dow như Nelson gom): hai chỉ số củng cố nhau; bất đồng thì hiếm khi là xu hướng chính. Không cần phá cùng ngày. **Tín hiệu chính kinh điển cần CẢ HAI** chỉ số phá cực trị của con sóng. "Non-confirmation" nghĩa là **bất đồng giữa hai chỉ số** (Hamilton tr. 6) — không phải thuật ngữ về hình dạng đỉnh–đáy.
5. **Khối lượng là nguyên lý YẾU.** [Hamilton tr. 177] khối lượng "ít ý nghĩa hơn người ta tưởng", chỉ có nghĩa tương đối. Dùng làm tín hiệu phụ, không làm điều kiện.
6. **Xu hướng tiếp diễn cho tới khi có tín hiệu rõ ràng.** [Dow, Nelson tr. 40] thị trường tăng chừng nào mỗi đỉnh sau cao hơn đỉnh trước; giảm khi một đáy thấp hơn các đáy trước. Dow cũng nói khó phân biệt cuối một nhịp tăng với một nhịp điều chỉnh sâu.

## 4. Đỉnh–đáy và đảo chiều

- **Tăng:** chuỗi đỉnh cao dần (HH) và đáy cao dần (HL). **Giảm:** LH và LL. Đỉnh *bằng* đỉnh trước chưa phải đỉnh mới. (Dow chỉ đòi đỉnh sau cao hơn; đòi cả đáy cao dần là cách đọc vận hành chặt hơn của dự án.)
- **Mốc phủ định:** trong xu hướng tăng là đáy HL bảo vệ cấu trúc; đóng cửa xuyên xuống dưới nó là cảnh báo.
- **Đảo chiều kinh điển [Rhea, thứ cấp]:** sau một con sóng đủ điều kiện, **cả hai chỉ số** cùng phá cực trị của con sóng (đáy cho thị trường gấu, đỉnh cho thị trường bò). Blay (thứ cấp, gắn với người bán dịch vụ) lưu ý Dow chưa từng gọi chúng là "tín hiệu".
- **Một chuỗi giá đơn lẻ:** đóng cửa phá đáy HL / đỉnh LH gần nhất chỉ là **cảnh báo cấu trúc** (cùng bản chất CHoCH của SMC) — không phải tín hiệu Dow đúng nghĩa vì thiếu chỉ số thứ hai. Đừng nói "xác nhận đảo chiều chính" cho một mã hay một chỉ số đơn lẻ.
- **"Failure swing":** là thuật ngữ RSI của J. Welles Wilder (1978), **không có** trong Nelson hay Hamilton. Một số trang cho rằng Murphy gán "failure / non-failure swing" cho Dow nhưng chưa xác minh được. Không xếp hạng độ tin cậy nào cho nó.

## 5. Luật pivot của mô-đun (khi nó có) — để lời giải thích khớp mã

Đặc tả đầy đủ ở `docs/thiet-ke-dow-cau-truc.md`; ở đây chỉ nhắc để skill không nói lệch mã:
- Hai cấp pivot (nội bộ, swing) tính **nhân quả** trên giá đóng cửa: mỗi pivot có **ngày xảy ra** và **ngày biết** (muộn hơn). Chỉ được dùng nó từ ngày biết trở đi.
- Phá mốc tính bằng **giá đóng cửa vượt pivot đã được xác nhận TRƯỚC nến phá**, một lần mỗi pivot; cùng chiều thiên hướng là BOS, ngược chiều là CHoCH.
- Giá bằng nhau (trong nửa bước giá) không phải đỉnh mới hay phá mốc.
- Pivot đang chờ xác nhận là *tạm* — không dùng làm mốc.
- Mặc định hiển thị và lưới tham số: đặc tả mục 5.3, 5.8. Chưa có kết quả đo nào cho thấy chúng cho lợi thế.

## 6. "Chỉ giá đóng cửa"

Các chỉ số Dow–Jones được tính từ giá đóng cửa (Hamilton, phụ lục tr. 288–289), nên dữ liệu thời Dow **không có râu nến**. Đó là **thực tế của dữ liệu**, không phải một luật bảo bỏ râu nến vì "quét thanh khoản" — cách giải thích sau là lớp hiện đại thêm vào. Dự án dùng đóng cửa làm nền và coi râu nến là phép cắt riêng.

## 7. Việt Nam — chỉ nêu cái có nguồn

- Biên độ phiên với cổ phiếu thường: HOSE ±7%, HNX ±10%, UPCoM ±15%. Có tin ngày 01/10/2026 rằng cổ phiếu HNX chuyển sang HOSE từ 28/12/2026 và chưa rõ biên độ mới; cơ quan quản lý mới đang nghiên cứu (chưa quyết) biên độ rộng hơn, giao dịch xuyên trưa, rút ngắn thanh toán.
- Thanh toán cổ phiếu **T+2**; từ 29/08/2022 cổ phiếu mua về bán được trong buổi chiều T+2. Nguồn không ghi chu kỳ nào lẻ hơn thế; đừng nêu một chu kỳ thanh toán khác.
- **Chưa có số đo nào cho Việt Nam:** thời gian con sóng ở VN, mức "nhanh và gắt hơn", "xác suất thất bại của cổ phiếu khi VN-INDEX giảm" và "phần con sóng mới đã đi mất khi tín hiệu tới" đều **không có nguồn**; đừng nêu con số. Không tìm thấy nghiên cứu Lý thuyết Dow nào cho VN-INDEX; các nghiên cứu luật kỹ thuật VN tìm thấy chỉ ở dạng tóm tắt và dừng ở cỡ 2012.
- Chuỗi chỉ số thứ hai cho nguyên lý hai chỉ số: ứng viên VN30, VNMidcap, VNSmallcap hoặc chỉ số ngành. Số tin tức về mức tập trung của VN30 **chưa xác minh**; nếu VN30 gần trùng VN-INDEX thì "xác nhận" giữa chúng gần như tầm thường. Độ rộng thị trường (tỷ lệ mã trên MA) là khái niệm về sau, không phải của Dow.
- Chuỗi giá sau sự kiện quyền (chia thưởng, cổ tức) cần giá điều chỉnh; chuỗi chưa điều chỉnh sinh ra một cú rơi cơ học giống CHoCH giả.

## 8. Bằng chứng về lợi nhuận — nói đúng mức

- Cowles (1933) về các lời gọi thị trường của Hamilton: kết luận "ngang tung đồng xu" (qua mô tả của BGK).
- Brown–Goetzmann–Kumar (1998, bản làm việc; số đọc bằng OCR): các lời gọi của Hamilton 1902–1929 có chứa thông tin, nhưng không có phí giao dịch, alpha Jensen ≈ 3%/năm với sai số chuẩn xấp xỉ 2%, và nghiên cứu **không kiểm** bộ luật Rhea / Schannep.
- Rink (2023, 41 chỉ số): khả năng dự đoán của các luật kỹ thuật mờ dần; phí vừa phải xoá phần lớn lợi nhuận.
- Con số hiệu suất của Schannep đến từ trang gắn với người bán dịch vụ, chưa ai kiểm độc lập.
- Kết luận cho người dùng: có thể dùng Dow làm **ngôn ngữ mô tả cấu trúc**; không có bằng chứng nó cho lợi thế giao dịch ở thị trường này.

## 9. Tương ứng với Wyckoff và SMC — chỉ MỘT cái có nguồn

| Dow | Wyckoff / SMC | Trạng thái |
|---|---|---|
| "Line" (vùng đi ngang vài tuần, Hamilton tr. 6–7, 172–173; là vùng tích luỹ hoặc phân phối) | Vùng giao dịch Wyckoff (tích luỹ / phân phối) | **Có nguồn** cho chồng lấn thuật ngữ; chưa nguồn nào nói chúng là một |
| Con sóng | Tái tích luỹ / tái phân phối | [loại suy] — con sóng là nhịp ngược định nghĩa bằng biên độ và thời gian, tái tích luỹ là một VÙNG |
| Thủy triều | Swing structure / khung lớn | [loại suy] |
| Gợn sóng | Internal structure / inducement | [loại suy] |
| Đỉnh/đáy bị phá bằng đóng cửa | BOS / CHoCH | [loại suy vận hành]: BOS / CHoCH là phá-cùng / phá-ngược thiên hướng; nguồn gốc lịch sử từ Dow **chưa xác minh** |
| Dow tiếp diễn / đảo chiều | SOS + LPS / SOW + LPSY | [loại suy] — chưa nguồn nào |

Wyckoff có phải bắt nguồn từ Dow hay không: chưa tìm thấy nguồn xác nhận; đừng khẳng định. Pha A–E của Wyckoff thuộc MỘT vùng giao dịch, không phải của Dow.

## 10. Quy trình trả lời một mã / một chỉ số

1. **Thủy triều?** Khung ngày (và tuần nếu có). Nêu chuỗi đỉnh–đáy gần nhất kèm mốc giá, ngày xảy ra và (nếu mô-đun có) ngày biết. Mốc phủ định còn nguyên bằng giá đóng cửa không?
2. **Có con sóng đang chạy không?** Nêu biên độ so với nhịp chính trước đó và số phiên; nói rõ nó **chưa kết thúc** hay đã có pivot xác nhận. Đừng gọi nhịp đang chạy là xong.
3. **Chu kỳ (nếu cần):** vùng đi ngang do skill Wyckoff / `pha_wyckoff` đọc; ngoài vùng thì chỉ nói *xu hướng tăng / giảm đọc từ cấu trúc*, không gán "tích luỹ" hay "phân phối" từ thủy triều. Đáp án "chưa đủ bằng chứng" là hợp lệ.
4. **Phản biện bắt buộc:** nêu ít nhất một điều trên biểu đồ đi ngược nhận định, và một điều nhận định không biết (ví dụ chỉ có một chuỗi giá, không có chỉ số thứ hai).

## 11. Khung trả lời

- **Bức tranh:** thủy triều · con sóng · gợn sóng, mỗi cái kèm nhãn nguồn nếu trích lý thuyết.
- **Mốc:** mốc phủ định (giá đóng cửa), ngày biết, những gì đã *tạm*.
- **Đối chiếu (nếu người dùng cần):** bản dịch sang Wyckoff / SMC — ghi rõ cái nào [loại suy].
- **Giới hạn:** chuỗi đơn lẻ không xác nhận được xu hướng chính theo Dow; không có phép đo lợi thế; dữ liệu VN chưa có số riêng.
- Đây là đọc hiểu cấu trúc kỹ thuật và quản trị rủi ro, **không phải lời khuyên đầu tư**. Dự án không đặt lệnh thật: agent chuẩn bị, người dùng xác nhận và tự đặt.
