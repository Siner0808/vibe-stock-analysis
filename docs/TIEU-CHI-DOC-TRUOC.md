# Tiêu chí đọc — khai TRƯỚC khi chạy

> **Vì sao có file này.** Bất biến 7 và 8 cấm chọn quy tắc sau khi đã nhìn
> số. Cách duy nhất thi hành được điều đó là **viết tiêu chí ra, commit,
> rồi mới chạy** — để nó không thể sửa sau. File này là hợp đồng, không
> phải ghi chú.
>
> Mỗi mục dưới đây phải được người dùng chốt trước khi lượt chạy tương ứng
> bắt đầu. Khai ngày nào thì ghi ngày ấy.

---

## Đính chính trước tiên: "~2,5 giờ mỗi lượt" là con số CHƯA AI ĐO

Ngày 08/09/2026 tôi nhắc con số ấy nhiều lần như một sự thật. Đo lại:

```
grep -rn "2,5 giờ|2,5h|150 phút" --include=*.md .   ->  KHONG CO trong repo
walkforward.py:167  # `che_do_hoc="tat"` đi từ 8,1 lên 27,7 phút.
```

Số đo **duy nhất** có trong mã là **8,1–27,7 phút** cho một lượt (khác nhau
tuỳ cache phân tích được dùng lại hay không). Con số 2,5 giờ đến từ một
dòng bàn giao, không từ một lượt chạy.

Đây đúng là `references/loi-da-mac.md` **lỗi 16** — chép một kết luận rồi
phát ra như phép đo của mình — và nó lặp lại **trong cùng ngày** tôi viết
lỗi 16 vào skill.

### Con số THẬT, đo ngày 08/09/2026

Chạy `walkforward.py` ở **cấu hình mặc định** (`che_do_hoc=co_san`, theo mã,
`stride=2`, `min_history=60`), toàn bộ output vào một log ngoài repo:

```
bat dau : 16:49:11
ket thuc: 17:35:17
ma thoat: 0
       -> 46 phut 06 giay  (2.766 giay)
```

Lượt chạy trọn vẹn, không phải chết giữa chừng: log 42 dòng, **0 Traceback**,
0 error, có đủ tiêu đề `WALK-FORWARD`, mục in-sample và mục ngoài mẫu.

**Cả hai con số trước đó đều sai, theo hai hướng ngược nhau:**

| Con số | Ở đâu | Thực tế |
|---|---|---|
| ~2,5 giờ | không ở đâu cả — một dòng bàn giao | **cao gấp ~3,3 lần** |
| 8,1–27,7 phút | `walkforward.py:167` | đo ở chế độ `tat`; mặc định là `co_san` nên **thấp hơn thực tế** |

Chế độ `tat` cho `dat_lai_engine(enabled=False)`, mà nhánh xoá cache chỉ chạy
khi `may.enabled` — nên `tat` **không** xoá cache, còn `co_san` thì có, và
còn phải tra bộ nhớ hậu nghiệm mỗi phiên. Con số 27,7 phút chưa bao giờ là
cận trên của cấu hình mặc định.

**Ba giới hạn của con số 46 phút — đọc kèm, đừng tách rời:**

1. **Máy này, hôm nay, đang tải nặng.** Cùng buổi, hai lượt cổng gác chạy
   chậm gấp đôi lượt sáng (358s so với 149s). 46 phút là số trong điều kiện
   ấy, không phải hằng số.
2. **Một trong bốn lượt của ĐO 1.** Ba lượt kia (`--theo-ngay`, và hai lượt
   tắt trượt giá) **chưa đo**. Chế độ theo ngày duyệt lịch khác hẳn — không
   có lý do gì để tin chúng bằng nhau.
3. **Không suy ra được cho `stride=1`.** Gấp đôi điểm quyết định có thể gấp
   đôi thời gian hoặc hơn. Đó là một phép đo khác.

**Alpha của lượt này CHƯA ĐỌC.** Log nằm nguyên trong scratchpad
(`wf_mac_dinh.log`) và chỉ được mở sau khi tiêu chí ở dưới được chốt — đọc
trước thì mọi tiêu chí khai sau đó đều vô giá trị, và đó đúng là thứ bất
biến 7 cấm.

### Giá phải trả của con số bịa — đo được ngày 09/09/2026

Hỏi thẳng người dùng: *"Có phải bạn hoãn hai phép đo vì tin mỗi lượt tốn
~2,5 giờ không?"* Trả lời: **đúng, hoãn vì tưởng tốn nửa buổi.**

Nên lỗi 16 lần này không dừng ở một câu sai trong tài liệu. Nó **đổi một
quyết định**, và giữ hai phép đo nằm im. Đây là lần đầu dự án đo được cái
giá của một con số không ai chạy — không phải "một dòng cần sửa", mà **một
việc không được làm**.

Ghi ra vì nó đổi cách đọc mọi ước lượng khác trong tài liệu này: một con số
sai theo hướng làm việc gì đó trông đắt hơn thực tế cũng nguy hiểm như một
con số làm kết quả đẹp lên — chỉ khác là nó không để lại dấu vết nào trong
một lượt chạy, vì lượt chạy ấy không bao giờ xảy ra.

---

## ĐO 1 — Bảng "CHI PHÍ THỰC THI" ở cấu hình hiện hành

### Vì sao cần

`CLAUDE.md` mục CHI PHÍ THỰC THI có một bảng số đã được đánh dấu **lạc
hậu**: dòng BẬT ghi `alpha −0,927%`, `KTC [−1,689; −0,076] LOẠI 0` — kết
quả có ý nghĩa thống kê duy nhất dự án từng có. Nó đo trên mã ngày 31/08,
ở **vốn cam kết trung bình 138,66%**, tức đòn bẩy 1,39 lần — đúng thứ bất
biến 7b bắt phải chia ra rồi đo lại.

Đo lại 04/09 trên HEAD ở chế độ mặc định: **379 lệnh · alpha −0,676% · KTC
[−1,470; +0,211] — CHỨA 0.** Nên hiện dự án **không có kết quả nào loại
được số 0**, và bảng trong tài liệu vẫn là bảng cũ.

> ✅ **ĐÃ CHẠY 09/09/2026 — xem "Kết quả" ở cuối file.** Hai câu trên mô
> tả tình trạng **trước** lượt đo, và được giữ nguyên có chủ đích: đó là
> tiền đề mà hợp đồng này được ký, nên sửa nó đi là xoá mất bối cảnh của
> chữ ký. Câu *"không có kết quả nào loại được số 0"* nay đã hết đúng.

### Chạy gì

Bốn lượt: hai công tắc × hai chế độ mô phỏng.

| # | `MO_PHONG_TRUOT_GIA` | chế độ | lệnh |
|---|---|---|---|
| 1 | `True` (hiện hành) | theo mã (mặc định) | `walkforward.py` |
| 2 | `True` | theo ngày | `walkforward.py --theo-ngay` |
| 3 | `False` | theo mã | qua script đặt cờ trước khi gọi `chay()` |
| 4 | `False` | theo ngày | như trên, kèm `theo_ngay=True` |

`stride` và `min_history` giữ **nguyên mặc định** (2 và 60) ở cả bốn lượt —
đổi chúng là đổi câu hỏi, xem ĐO 2.

Công tắc ở `paper_trading.py:329`, không có biến môi trường ghi đè, nên
lượt 3–4 đặt cờ trong một **script chạy** chứ **không sửa mã nguồn**.

### Đại lượng chính, và nó là DUY NHẤT

**`alpha` cùng `alpha_ktc` trên vùng OOS**, ở ngưỡng do chính lượt chạy
chọn trên IS. Không phải `ky_vong`, không phải `net_pct`, không phải
`win_rate` — bất biến 6.

### Ba kết cục, và hành động cho từng cái

| Kết cục | Nghĩa | Hành động đã cam kết |
|---|---|---|
| **A · cận TRÊN của KTC < 0** | alpha âm một cách đo được | Cổng C5 **giữ đóng**. Thay bảng số trong `CLAUDE.md` bằng số mới. Ngừng dò ngưỡng — dò thêm là đo độ may của phép tìm kiếm (bất biến 7). |
| **B · KTC chứa 0** | không phân biệt được với rổ chuẩn | Cổng C5 **giữ đóng**, theo đúng tinh thần "đảo gánh nặng" đã nằm sẵn trong `paper_metrics.dieu_kien_dong_lai()`. Thay bảng số. **Không đổi một tham số nào.** |
| **C · cận DƯỚI của KTC > 0** | alpha dương đo được | **KHÔNG mở cổng.** Đây là chiều đáng ngờ nhất — quy tắc số 1. Bắt buộc bốn phép kiểm ở mục dưới TRƯỚC khi tin con số. |

Kết cục C là chỗ file này tồn tại. Dự án đã **năm lần** cho ra số đẹp rồi
hoá ra vô nghĩa, và cả năm lần đều nghiêng về phía đẹp lên.

> ✍️ **ĐÃ KÝ 09/09/2026 — người dùng chốt NGUYÊN bảng ba kết cục và bốn
> phép kiểm, không sửa một ngưỡng nào.**
>
> Từ mốc này bảng trên là **ràng buộc**, không phải đề xuất. Nhìn thấy số
> rồi mới đổi nó là đúng thứ bất biến 7 cấm — và vì bảng đã nằm trong một
> commit trước lượt chạy, việc đổi ấy để lại dấu trong `git log`.

### Bốn phép kiểm bắt buộc khi gặp kết cục C

1. **`von_tb` ≤ 100%.** Vượt là đòn bẩy trá hình (bất biến 7b) — chia tỷ
   trọng cho đúng bội số rồi đo lại, con số cũ **không đọc được**.
2. **Chạy lại lần thứ hai, cùng lệnh, phải ra số y hệt** (bất biến 2).
   Lệch một chữ số là có trạng thái rò rỉ giữa hai lượt.
3. **`alpha_bo_qua` so với `so_lenh`.** Bao nhiêu lệnh bị loại vì không
   khớp được cặp ngày với rổ chuẩn. Bỏ qua nhiều thì alpha nói về một tập
   con, không nói về chiến lược.
4. **`so_ma_oos`.** Vùng OOS có bao nhiêu mã. Bản đo 07/08/2026 chỉ có
   22/50 mã trong vùng kiểm định — kết quả khi ấy nói về 22 mã đó.

### Phải báo cáo KÈM, không được tách rời

Mỗi dòng kết quả đi kèm: `so_lenh` · `von_tb` · `von_dinh` ·
`alpha_so_lenh` · `alpha_bo_qua` · `so_ma_is` · `so_ma_oos` · **thời gian
chạy thật**.

Trong dải kết quả, **dòng đáng tin nhất là dòng có nhiều lệnh nhất**,
không phải dòng alpha cao nhất (bất biến 7).

### Điều KHÔNG được làm sau khi thấy số

- Đổi ngưỡng, đổi `stride`, đổi `min_history`, đổi rổ mã, rồi chạy lại tới
  khi số đẹp hơn. Đó là bất biến 7 và 8.
- Chọn dòng có alpha cao nhất trong dải IS rồi gọi nó là kết quả.
- Mở cổng C5 vì một kết quả backtest. Cổng C5 đóng/mở theo
  `dieu_kien_dong_lai()` trên **lệnh tiến-về-trước đã đóng** (nay n = 1),
  không theo walk-forward.

---

## ĐO 2 — `stride=1`: câu hỏi hiện tại KHÔNG trả lời được

### Vì sao nó được nêu ra

`CLAUDE.md` ghi: backtest khớp ở **T+2**, đường chạy thật khớp ở **T+1**.
Đo trên sổ thật: 43/43 lệnh mô phỏng đúng T+2, 4/4 lệnh tiến-về-trước đúng
T+1. Chưa ai đo việc lệch ấy đổi kết quả bao nhiêu.

### Vì sao chạy `--stride 1` KHÔNG trả lời được câu đó

`stride` chỉ xuất hiện ở hai vòng lịch:

```python
# walkforward.py:193 va :295
for t in range(min_history, len(df), stride)
```

Nó quyết định **phiên nào được ghé**, và lệnh khớp ở phiên **được ghé kế
tiếp**. Nên `stride=2 → 1` đổi **cùng lúc hai thứ**:

- **số điểm quyết định** — gấp đôi, nên tập lệnh khác hẳn, không phải cùng
  tập lệnh với giá vào khác;
- **độ trễ khớp** — T+2 thành T+1.

Một khác biệt quan sát được **không quy được cho vế nào**. Đó là biến gây
nhiễu, không phải chi tiết kỹ thuật.

### Ba lựa chọn, cần người dùng chốt

| | Làm gì | Trả lời được câu gì |
|---|---|---|
| **1** | Không chạy | — |
| **2** | Chạy `--stride 1`, đọc có giới hạn | *"Gộp của điểm quyết định dày gấp đôi VÀ khớp sớm một phiên thì đổi bao nhiêu"* — **không** phải câu hỏi gốc |
| **3** | Tách độ trễ khớp khỏi `stride` bằng một tham số riêng, có test, rồi mới đo | Đúng câu hỏi gốc |

**Đề xuất: 3, hoặc 1.** Lựa chọn 2 tốn cùng chừng ấy máy mà cho một con số
không diễn giải được — và một con số không diễn giải được, đặt cạnh một
bảng đang lạc hậu, là đúng cách dự án này đã năm lần tự lừa mình.

> ✍️ **ĐÃ CHỐT 09/09/2026 — lựa chọn 3.**
>
> Tách độ trễ khớp khỏi `stride` bằng một tham số riêng, có test, rồi mới
> đo. Thứ tự bắt buộc, và nó là lý do mục dưới nằm ở đây chứ không nằm sau:
> **tiêu chí đọc được khai TRƯỚC khi tham số kia được viết ra một dòng
> nào.** Viết mã trước rồi mới khai tiêu chí thì tiêu chí đã bị hình dạng
> của mã định hướng, kể cả khi chưa ai chạy lượt nào.

### Tiêu chí đọc của lựa chọn 3 — khai trước khi viết tham số

Đại lượng chính vẫn là **alpha OOS cùng KTC**, so giữa hai cấu hình chỉ
khác độ trễ khớp.

**Hướng dự kiến phải nêu TRƯỚC.** `CLAUDE.md` đã nêu: *"vào muộn một phiên
đáng lẽ làm kết quả xấu đi"*, nên chuyển từ T+2 (muộn) sang T+1 (sớm hơn,
khớp đường chạy thật) **được dự kiến làm alpha ĐẸP LÊN**.

Vì thế:

| Kết cục | Đọc thế nào |
|---|---|
| alpha đẹp lên, và mức đẹp lên **nhỏ hơn** bề rộng KTC | phù hợp dự kiến, không có gì bất thường |
| alpha **xấu đi** | ngược dự kiến → có thể sai ở hướng suy luận, hoặc ở phép cài đặt. Đi tìm trước khi tin. |
| alpha đẹp lên **hơn một nửa bề rộng KTC** | quy tắc số 1: giả định đầu tiên là **có lỗi**. Kiểm bốn thứ ở ĐO 1 trước khi ghi vào tài liệu. |

---

## Ghi chép

| Ngày | Mục | Người chốt | Ghi chú |
|---|---|---|---|
| 08/09/2026 | soạn lần đầu, chưa chạy lượt nào | — | chờ chốt ĐO 1 và lựa chọn 1/2/3 của ĐO 2 |
| 09/09/2026 | **ĐO 1 — ký nguyên bảng ba kết cục + bốn phép kiểm** | người dùng | không sửa ngưỡng nào |
| 09/09/2026 | **ĐO 2 — chốt lựa chọn 3** | người dùng | tách độ trễ khớp khỏi `stride`, có test, rồi mới đo |
| 09/09/2026 | xác nhận hai phép đo bị hoãn **vì con số "2,5 giờ"** | người dùng | số thật 46 phút → xếp lại lịch chạy |
| 09/09/2026 | **ĐO 1 — bốn lượt ĐÃ CHẠY**, 08:59 → 11:36 | — | tiêu chí vào `main` lúc 08:30, trước lượt đầu 29 phút. Kết cục A và B — xem mục dưới |

---

## Kết quả ĐO 1 — chạy 09/09/2026, đọc theo bảng đã ký

**Trình tự, ghi ra để kiểm được:** tiêu chí vào `main` lúc **08:30:48**
(PR #73, `984f990`); ba chữ ký ở PR #74; lượt chạy đầu tiên bắt đầu
**08:59:12**; lượt cuối xong **11:36:56**. Không dòng nào của bảng ba kết
cục bị sửa sau 08:30 — `git log docs/TIEU-CHI-DOC-TRUOC.md` là bằng chứng.

| # | trượt giá | chế độ | ngưỡng IS | lệnh OOS | alpha | KTC 95% | kết cục | vốn TB · đỉnh | phút |
|---|---|---|---|---|---|---|---|---|---|
| 1 | BẬT | theo mã | 62 | 379 | −0,68% | [−1,47 ; +0,21] | **B** | 48% · 180% | 36,1 |
| 2 | BẬT | theo ngày | 50 | **508** | **−0,94%** | **[−1,57 ; −0,28]** | **A** | 53% · **100%** | 32,9 |
| 3 | TẮT | theo mã | 62 | 376 | −0,03% | [−0,86 ; +0,87] | B | 49% · 173% | 33,9 |
| 4 | TẮT | theo ngày | 50 | 497 | −0,03% | [−0,71 ; +0,72] | B | 53% · 100% | 54,9 |

Cả bốn: 71 mã IS · 33 mã OOS · bộ nhớ 44 mẫu, học thêm 0 · **0 lệnh bị bỏ
khi ghép rổ chuẩn** · cả bốn mã thoát 0 · log 46–49 dòng, 0 Traceback.

### Hành động, theo đúng cam kết

Kết cục A và B cam kết **cùng một việc**, nên không có gì phải cân nhắc:

- ✅ **Cổng C5 giữ đóng.** Nó đang đóng; không đổi gì.
- ✅ **Thay bảng số trong `CLAUDE.md`** — mục "CHI PHÍ THỰC THI ĐÃ BẬT".
- ✅ **Không đổi một tham số nào.**
- ✅ **Ngừng dò ngưỡng** (điều khoản riêng của kết cục A).

Bốn phép kiểm bắt buộc chỉ áp cho kết cục C, nhưng **cả bốn đều thoả**:
`von_tb` 48–53% ≤ 100% · chạy lại ra số y hệt · 0 lệnh bị bỏ · 33 mã OOS.

### Phép kiểm số 2 đã chạy MIỄN PHÍ, và nó xanh

Log 46 phút ngày 08/09 chạy đúng cấu hình lượt 1. Đặt cạnh nhau: **379
lệnh · −0,68% · [−1,47 ; +0,21] · 48%/180%** — trùng từng chữ số, hai
ngày, hai tiến trình độc lập. Bất biến 2 giữ.

### Dụng cụ tự chứng minh nó hoạt động

Nếu lượt 1 và lượt 3 cho alpha y hệt nhau thì cờ `MO_PHONG_TRUOT_GIA`
không có tác dụng và cả bảng vô nghĩa. Chúng khác nhau (−0,68 so với
−0,03), và lượt 2 khác lượt 4 (−0,94 so với −0,03).

### MỘT CHỖ BẢNG NÀY KHÔNG ĐỌC ĐƯỢC

Ngưỡng do chính lượt chạy chọn trên IS, ra **62 cho theo-mã, 50 cho
theo-ngày**. Nên **1 vs 2** và **3 vs 4** khác nhau ở *cả* chế độ *lẫn*
ngưỡng — không quy được cho vế nào. Chỉ **1 vs 3** và **2 vs 4** đọc được.

Đây đúng hình dạng của vấn đề `stride` trong ĐO 2, xuất hiện lại ở một
chỗ không ai lường trước: **luật chọn ngưỡng**. Bài học chung: một phép so
2×2 chỉ là 2×2 khi mọi thứ ngoài trục đang xét được ghim, và "được chọn tự
động theo luật đã nêu trước" **không** đồng nghĩa với "được ghim".

### Điều dụng cụ KHÔNG báo cáo được, và đã vá

Điều khoản "Phải báo cáo KÈM" đòi `alpha_so_lenh`. `walkforward.main()`
**chưa bao giờ in trường đó** — nó có trong dict từ đầu, và
`tests/test_walkforward.py` đã khoá việc nó CÓ MẶT, nhưng không gì bắt nó
đi ra tới người đọc. Phải chạy hết 157,7 phút mới lộ.

Đã vá cùng ngày: `walkforward.dong_bao_cao_oos()` tách thành hàm thuần,
`alpha_so_lenh` và `alpha_bo_qua` in **luôn luôn** kể cả bằng 0, và
`test_bao_cao_OOS_in_DU_moi_truong_hop_dong_BAT_bao_cao` kiểm GIÁ TRỊ chứ
không kiểm nhãn. Ba đột biến, 3/3 đỏ.
