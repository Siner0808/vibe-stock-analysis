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

**Đã tra trùng:** (bổ sung 14/09/2026) tra 65 tiêu đề `docs/STATE.md` — **không mục nào** đo lại bảng chi phí trước 09/09/2026. Bảng cũ đến từ 24/08 và chưa bao giờ qua tiền đăng ký, nên không có phép đo nào để trùng. ĐO 1 chính là **BƯỚC 44**, phép đo đầu tiên có hợp đồng ký trước.

> **Dụng cụ đọc:** `tools/do1_chi_phi_thuc_thi.py` — mỗi lượt một tiến
> trình riêng, chạy tuần tự.

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

**Đã tra trùng:** (bổ sung 14/09/2026) **BƯỚC 17 · 21 · 23 · 24 · 26** đều đã chạm độ trễ khớp và `stride`. KHÔNG trùng, và lý do chính là nội dung mục này: thí nghiệm `stride` (BƯỚC 23–24) đổi **cùng lúc hai thứ**, nên nó không tách được độ trễ khớp ra. Đó là vì sao ĐO 2 tồn tại.

> **Dụng cụ đọc:** `tools/do2_do_tre_khop.py` — bốn lượt, ngưỡng ghim
> tay 62/50.

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
| 09/09/2026 | **ĐO 2 — ký điều khoản bổ sung**, cả ba mục | người dùng | phép tách · ba điều kiện cài đặt · ghim ngưỡng tay 62/50. Chưa viết dòng mã nào |
| 10/09/2026 | **ĐO 2 — bốn lượt ĐÃ ĐỌC**, kết cục 1 cả hai phép so | — | hai lượt đối chứng tái lập đúng từng chữ số. Lộ ra lỗi 24 |
| 10/09/2026 | **chốt đổi mặc định `do_tre_khop` sang 1** | người dùng | nhưng gộp vào lần đo lại đầy đủ tiếp theo, KHÔNG đổi rời |
| 10/09/2026 | **ĐO 3 — khai tiêu chí**, trước khi đổi dòng mã nào | — | bảng CHI PHÍ THỰC THI ở mặc định T+1. Phép kiểm dụng cụ: nếu IS chọn lại 62/50 thì hai dòng trượt-giá-BẬT phải ra lại đúng số ĐO 2 |
| 10/09/2026 | **ĐO 4 — khai tiêu chí**, trước khi kéo một mã nào | — | kéo cache về 2018. Dữ liệu mới đổ TRỌN vào vùng OOS. Thiên lệch sống sót khai trước làm nghi phạm số một nếu alpha đẹp lên |

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

---

## ĐO 2 — điều khoản bổ sung, khai TRƯỚC dòng mã đầu tiên

**Đã tra trùng:** (bổ sung 14/09/2026) cùng mạch với mục ĐO 2 ở trên — **BƯỚC 21 · 23 · 24**. Điều khoản bổ sung không mở câu hỏi mới, nó siết cách đọc của đúng phép đo ấy, nên không có chỗ trùng mới.

> **Dụng cụ đọc:** `tools/do2_do_tre_khop.py`, cùng dụng cụ với mục
> ĐO 2 ở trên.

> ✍️ **ĐÃ KÝ 09/09/2026 — cả ba mục, không sửa một điều kiện nào.**
>
> | Mục | Người dùng chốt |
> |---|---|
> | Phép tách | **Ký** — ghé mọi phiên để KHỚP, giữ lưới `stride` cho CHẤM và QUYẾT ĐỊNH |
> | Ba điều kiện cài đặt | **Ký cả ba** — kể cả điều kiện 1: mặc định phải ra số y hệt, sai thì DỪNG |
> | Ngưỡng | **Ký** — ghim tay 62 / 50, không để luật tự chọn |
>
> Chữ ký nằm trong git **trước** dòng mã đầu tiên của ĐO 2. Đó là toàn bộ
> điểm của mục này: sau khi thấy số, mọi thay đổi ở đây đều để lại dấu
> trong `git log`.

### Vì sao cần thêm điều khoản

Người dùng đã chốt **hướng 3** ngày 09/09/2026: tách độ trễ khớp khỏi
`stride` bằng một tham số riêng. Nhưng bản cài đặt hiển nhiên nhất của
hướng 3 **tái tạo lại đúng vấn đề của hướng 2**, chỉ ở một tầng sâu hơn:
cho mô phỏng ghé thêm phiên để khớp sớm hơn thì `evaluate_open` cũng chạy
thêm, tức độ mịn phát hiện chạm stop-loss đổi theo. Lại hai thứ đổi cùng
lúc.

Và ĐO 1 vừa cho thấy hình dạng ấy không hiếm: **lỗi 21** — một luật chọn
tham số cũng là một cái trục, và nó ẩn kỹ hơn một tham số gõ tay.

### Đọc mã: `run_session` làm BỐN việc, chỉ hai việc là đắt

`paper_runner.run_session`, theo đúng thứ tự:

| # | việc | gọi gì | cần `_analyze`? |
|---|---|---|---|
| 1 | **KHỚP** lệnh chờ và lệnh đóng | `fill_pending` · `fill_closing` | **không** |
| 2 | **CHẤM** và đóng vị thế đang mở | `_analyze` + `evaluate_open` | có |
| 3 | **RA QUYẾT ĐỊNH** mở lệnh mới | `_analyze` + `consider_entry` | có |
| 4 | trả `final_score` cho báo cáo | — | — |

`_analyze` kéo cả chuỗi agent — đó là toàn bộ chi phí của một phiên.
**`stride` sinh ra để thưa hoá phần ĐẮT.** Nhưng nó đang thưa hoá luôn
phần RẺ, và đó đúng là chỗ độ trễ khớp bị dính vào nó.

### Phép tách đề xuất

Ghé **mọi** phiên để KHỚP; ghé **các phiên cách nhau `stride`** để CHẤM và
RA QUYẾT ĐỊNH.

```
hom nay   (stride=2)   ghe: t, t+2, t+4 ...   ca ba viec, cung luc
de xuat                ghe: t, t+1, t+2 ...   KHOP moi phien
                       ghe: t, t+2, t+4 ...   CHAM + QUYET DINH nhu cu
```

**Lưới chấm KHÔNG đổi.** Đúng những phiên đang được `evaluate_open` soi
hôm nay thì vẫn được soi, không hơn không kém. Phiên `t+1` vẫn **không**
được chấm — nên một cây thủng stop-loss ở `t+1` vẫn vô hình, y như hôm
nay. Đó là chủ đích: giữ nguyên mọi thứ trừ đúng một biến.

**Tập điểm quyết định KHÔNG đổi.** `consider_entry` vẫn chỉ chạy trên lưới
`stride`, nên tập tín hiệu là **cùng một tập** — khác hẳn hướng 2, nơi số
điểm quyết định gấp đôi và tập lệnh khác hẳn.

Chi phí máy tăng ít: phiên ghé-thêm không gọi `_analyze`.

### Một hệ quả cơ học PHẢI nêu trước, và nó KHÔNG phải biến thứ hai

Lệnh sinh ở `t` nay khớp ở `t+1` thay vì `t+2`. Lưới chấm đứng yên, nên
khoảng từ **lúc vào** tới **lần chấm đầu tiên** co từ 2 phiên xuống 1.

Đó là **hệ quả xuôi dòng của chính biến đang đo** (vào sớm hơn một phiên),
không phải một biến độc lập được thay đổi cùng lúc. Ghi ra vì nếu không
ghi, nó sẽ được phát hiện sau khi thấy số và khi ấy không phân biệt được
với một lời biện minh.

### Ba điều kiện của phép CÀI ĐẶT — kiểm trước khi tin con số

Phép đo chỉ đọc được nếu cả ba đúng, và cả ba phải được chứng minh bằng
test **trước** khi chạy lượt nào:

1. **Tham số mới ở giá trị mặc định cho ra kết quả Y HỆT hôm nay.** Không
   phải "gần bằng" — y hệt, từng chữ số, trên cùng dữ liệu. Đây là điều
   kiện mạnh nhất và là thứ duy nhất chứng minh được rằng phép tách không
   kéo theo gì khác.
2. **Tập phiên được CHẤM không đổi** giữa hai cấu hình. Kiểm bằng cách
   đếm, không bằng cách đọc mã.
3. **Tập phiên RA QUYẾT ĐỊNH không đổi** giữa hai cấu hình. Như trên.

Điều kiện 1 hỏng thì **dừng**, không chạy lượt nào. Một tham số mặc định
làm đổi số cũ nghĩa là phép tách đã kéo theo một thứ khác, và khi đó ĐO 2
đo hai thứ y như hướng 2.

### Đại lượng chính, và hướng dự kiến — khai trước

**`alpha` cùng `alpha_ktc` trên OOS**, so giữa hai cấu hình chỉ khác độ
trễ khớp. Bốn lượt như ĐO 1 (hai chế độ × hai độ trễ), và **ngưỡng phải
được ghim bằng tay ở giá trị ĐO 1 đã chọn** — 62 cho theo mã, 50 cho theo
ngày. Đó là bài học lỗi 21: để luật tự chọn ngưỡng là thêm một trục.

`CLAUDE.md` đã nêu *"vào muộn một phiên đáng lẽ làm kết quả xấu đi"*, nên
T+2 → T+1 **được dự kiến làm alpha ĐẸP LÊN**.

| Kết cục | Đọc thế nào |
|---|---|
| alpha đẹp lên, mức đẹp lên **nhỏ hơn** bề rộng KTC | phù hợp dự kiến, không có gì bất thường |
| alpha **xấu đi** | ngược dự kiến → sai ở hướng suy luận, hoặc ở phép cài đặt. Đi tìm TRƯỚC khi tin. |
| alpha đẹp lên **hơn một nửa bề rộng KTC** | quy tắc số 1: giả định đầu tiên là **có lỗi**. Kiểm bốn thứ ở ĐO 1 trước khi ghi vào tài liệu. |

### Nếu không tách sạch được ba việc

Thì câu trả lời là **"hướng 3 không khả thi"**, và ĐO 2 dừng ở đó. Không
lặng lẽ tụt về hướng 2 — một con số không diễn giải được, đặt cạnh một
bảng vừa mới đo lại, là đúng cách dự án này đã năm lần tự lừa mình.


---

## Kết quả ĐO 2 — chạy 09/09/2026, đọc 10/09/2026 theo bảng đã ký

Thứ tự đọc đã cam kết và đã theo: thời gian chạy → bốn mã thoát → hai lượt
đối chứng → mới tới T+1.

**Phép kiểm dụng cụ ĐẠT.** Hai lượt đối chứng (`do_tre_khop=None`) ra lại
đúng từng chữ số con số ĐO 1: theo mã 379 · −0,68% · [−1,47 ; +0,21] ·
48%/180%; theo ngày 508 · −0,94% · [−1,57 ; −0,28] · 53%/100%.

| phép so | alpha T+2 → T+1 | Δ | nửa bề rộng KTC | **kết cục** |
|---|---|---|---|---|
| theo mã 62 | −0,68% → −0,55% | **+0,13** | 0,840 | **1** |
| theo ngày 50 | −0,94% → **−0,82%** | **+0,12** | 0,645 | **1** |

Cả hai là **kết cục 1**: đẹp lên đúng hướng dự kiến, mức đẹp lên nhỏ hơn
một phần sáu bề rộng KTC. Không có gì bất thường, không chạm quy tắc số 1.

Dòng theo ngày ở T+1 vẫn **loại được số 0**: KTC [−1,47 ; −0,15], 546
lệnh, vốn đỉnh đúng 100%.

**Một điều khoản của chính mục này hoá ra thiếu.** Câu *"tập tín hiệu là
cùng một tập"* đúng, nhưng không có điều kiện nào nói về tập **LỆNH**, và
tập lệnh xáo 15% (theo mã) / 27% (theo ngày). Cơ chế đã đo và quy được về
đúng một biến — `docs/STATE.md` BƯỚC 46, và lỗi 24.

**Rút cho lần khai trước sau:** mọi câu *"X không đổi"* trong tiêu chí phải
kèm **lệnh kiểm X**. Ba điều kiện của ĐO 2 đều có test; câu về tập lệnh
thì không, nên nó không sai — nó chỉ chưa bao giờ được hỏi.


---

## ĐO 3 — bảng CHI PHÍ THỰC THI ở cấu hình hiện hành, mặc định T+1

**Đã tra trùng:** (bổ sung 14/09/2026) **BƯỚC 44** (ĐO 1) đo đúng bốn dòng ấy. KHÔNG trùng vì mặc định đã đổi sang T+1 sau **BƯỚC 46**, nên bảng ĐO 1 không còn mô tả cấu hình đang chạy — và chính ĐO 3 chứng minh điều đó khi ngưỡng theo-ngày nhảy 50 → 45.

> **Khai ngày 10/09/2026, TRƯỚC khi đổi một dòng mã nào và trước lượt chạy
> đầu tiên.** Đây là lần thứ ba dự án làm đúng thứ tự ấy.

### Vì sao chạy

Ba việc treo gộp làm một, theo đúng chốt của người dùng ngày 10/09:

1. **Đổi mặc định `do_tre_khop` sang 1.** Đường chạy thật khớp T+1; backtest
   mặc định vẫn T+2. Đã chốt: đổi, nhưng **không đổi rời** — mặc định mới và
   bảng số mới phải ra đời trong CÙNG một PR, để không tồn tại quãng tài
   liệu ghi một đằng chạy ra một nẻo.
2. **Bảng "CHI PHÍ THỰC THI" trong `CLAUDE.md` đang bị đánh dấu lạc hậu.**
3. **Hai chỗ chưa truy** — đọc kèm, xem mục dưới.

### Đúng MỘT biến đổi, và nó KHÔNG phải `diem_ghe`

`diem_ghe(n, min_history, stride, do_tre_khop=None)` giữ nguyên: `None` ở đó
là **ký hiệu ngữ nghĩa** *"bằng `stride`"*, không phải một chính sách. Hai
điều kiện người dùng đã ký ngày 09/09 —
`test_DIEU_KIEN_1_mac_dinh_cho_lich_Y_HET_hom_nay` và `1b` — kiểm đúng ký
hiệu ấy, nên chúng **phải vẫn xanh sau thay đổi**. Xanh là điều kiện để tin
rằng phép đổi chỉ chạm chính sách.

Thứ đổi là mặc định ở **bên gọi**: `_mo_phong`, `chay`, và cờ CLI —
`None` → `1`. Kèm một phép kiểm mới khoá mặc định ấy, để nó không trôi lại.

Không đổi gì khác: `stride=2` · `min_history=60` · `che_do_hoc=co_san` ·
**cache giá KHÔNG kéo dài** (xem mục cuối).

### Đại lượng chính

**alpha khớp từng lệnh + KTC 95% trên OOS**, bốn dòng như ĐO 1: hai công
tắc trượt giá × hai chế độ mô phỏng, mỗi lượt tự chọn ngưỡng trên IS.

### Phép kiểm dụng cụ — MIỄN PHÍ, và phải đọc TRƯỚC alpha

ĐO 2 đã đo T+1 ở ngưỡng **ghim tay** 62/50. Nên:

| nếu vòng dò IS chọn | thì | đọc thế nào |
|---|---|---|
| **62 (theo mã) và 50 (theo ngày)** | hai dòng trượt-giá-BẬT phải ra lại **đúng từng chữ số** số ĐO 2 T+1: theo mã **398 lệnh · −0,55% · [−1,38 ; +0,37]**; theo ngày **546 lệnh · −0,82% · [−1,47 ; −0,15]** | lệch → **bảng KHÔNG đọc được**, đi tìm lỗi trước |
| ngưỡng **khác** 62/50 | hai dòng ấy **không so được** với ĐO 2 | ghi ra, **đừng ép so**. Và bản thân việc ngưỡng đổi là thông tin: luật chọn ngưỡng nhạy với độ trễ khớp — một trục nữa, đúng hình dạng lỗi 21 |

### Ba kết cục, khai trước

| kết cục | đọc thế nào |
|---|---|
| Bảng mới ≈ ĐO 1 dịch đi **+0,12 → +0,13** điểm (mức ĐO 2 đã đo) | phù hợp dự kiến — thay bảng trong `CLAUDE.md` |
| alpha đẹp lên **hơn nửa bề rộng KTC** | **quy tắc số 1**: giả định đầu tiên là CÓ LỖI. Kiểm trước khi ghi. |
| alpha **đổi DẤU** — dương và loại được số 0 | quy tắc số 1 ở mức mạnh nhất. **KHÔNG ghi vào tài liệu**, không công bố, đi tìm lỗi. Dự án đã năm lần cho ra số đẹp hoá ra vô nghĩa; một cú lật dấu sau khi đổi đúng một mặc định là ứng viên thứ sáu, không phải một phát hiện. |

**Vì sao dự kiến KHÔNG đổi dấu:** ĐO 1 đo được alpha **không có** chi phí
thực thi là **−0,03%**, KTC gần đối xứng quanh 0. Vào sớm một phiên không
tạo ra lợi thế, nó chỉ bớt trả chi phí — nên trần trên của phép đổi này là
"tiến về 0", không phải "vượt lên trên".

### Hai việc CHƯA TRUY, đọc kèm trong cùng lượt

**1. Khoảng cách 0,43 (trong mẫu) so với 0,65–0,91 (ngoài mẫu).** Ba giả
thuyết chưa loại được: OOS thanh khoản mỏng hơn · tập lệnh khác nên trung
vị giá vào khác · **con số 0,43 đo ở một bản mã cũ hơn**.

Lượt này sinh ra một con số IS **mới, ở bản mã hiện hành**. So nó với 0,43:

- ra **≈0,43** → giả thuyết thứ ba **bị loại**, còn hai.
- ra **khác đáng kể** → giả thuyết thứ ba được củng cố, và con số 0,43 trong
  `CLAUDE.md` phải bị đánh dấu là đo ở bản cũ.

**2. Chênh 385 so với 376 lệnh** giữa bảng `CLAUDE.md` và lượt chạy lại
04/09, trong khi alpha và kỳ vọng khớp tới 3 chữ số. Ghi lại số lệnh IS/OOS
của lượt này để có mốc thứ ba.

### Cache giá KHÔNG được kéo dài trong lượt này

`extend_history.py --check` ngày 10/09: rổ bắt đầu **2021-10**, nhiều phiên
nhất 1.217 (DIG). Và một phép hỏi thẳng vnstock cùng ngày cho thấy **nguồn
CÓ dữ liệu từ 2017-08** (FPT, 2.271 nến) — tức cache thiếu, kéo được.

**Nhưng không kéo trong lượt này.** Kéo cache đổi DỮ LIỆU mà mọi backtest
chạy trên đó, nên bảng mới sẽ khác ĐO 1 vì **hai** lý do cùng lúc và không
quy được cho vế nào. Đó đúng là thứ lỗi 21 và hướng 2 của ĐO 2 đã dạy.

Việc kéo cache là một phép đo RIÊNG, cần tiêu chí riêng, và phải chạy SAU.

### Dụng cụ

`tools/do1_chi_phi_thuc_thi.py`, mỗi lượt một tiến trình riêng. Thời gian:
ĐO 1 mất **157,7 phút** cho bốn lượt; lượt này **ước lượng cùng bậc**, và
thời gian chạy đã đo được là không phải hằng số (46,1 so với 36,1 phút cho
cùng cấu hình ở hai ngày khác nhau).


---

## ĐO 4 — kéo cache giá về 2018

**Đã tra trùng:** (bổ sung 14/09/2026) **BƯỚC 50** (ĐO 3) đo cùng bốn dòng trên cache mặc định. KHÔNG trùng vì ĐO 4 đổi đúng **một** thứ — cache kéo về 2018, tức cỡ mẫu — và giữ nguyên mọi tham số khác.

> **Dụng cụ đọc:** `tools/do1_chi_phi_thuc_thi.py`, chạy với biến môi
> trường `VIBE_CACHE_DIR` trỏ vào cache 2018.

> **Khai ngày 10/09/2026, TRƯỚC khi kéo một mã nào.** Phép đo này đổi
> **dữ liệu** mà mọi con số walk-forward đã công bố được tính trên đó, nên
> tiêu chí của nó nặng hơn ĐO 3 chứ không nhẹ hơn.

### Điều kiện tiên quyết — ĐÃ ĐO, và nó thoả

`CLAUDE.md` ghi điều kiện xem lại agent cơ bản: *"cache giá lùi được về
2018 (19 kỳ → ~30)"*. Câu ấy viết **23/08/2026** và nằm im 18 ngày mà không
ai hỏi nó có thoả được không. Đo 10/09/2026:

```
extend_history.py --check : ro bat dau 2021-10 · nhieu phien nhat 1.217 (DIG)
hoi thang vnstock (FPT)   : 2.271 nen · som nhat 2017-08-07
```

**Nguồn CÓ dữ liệu 2018. Cache thiếu, không phải nguồn không có.**

### Điều bất ngờ, và nó đổi hẳn giá trị của phép đo

```python
truoc = ngay < str(moc)[:10]
return df[truoc], df[~truoc]      # (OOS, IS)
```

**Mọi phiên TRƯỚC mốc là OOS.** Đây là bất biến 8 — vùng kiểm định nằm ở
QUÁ KHỨ, vì hàng trăm vòng tối ưu đã chạy trên cache kéo tới hôm nay nên
giai đoạn gần nhất là giai đoạn đã bị nhìn nhiều nhất.

Hệ quả: dữ liệu kéo về **đổ TRỌN vào vùng ngoài mẫu**. Và nó chưa thể đã
bị nhìn theo nghĩa mạnh nhất — nó **không nằm trong cache** khi các vòng
tối ưu ấy chạy.

Hiện OOS là **25.219/80.939 phiên = 31,2%**, trên **33/71 mã** có vùng OOS
đủ dài. Kéo thêm ~3,5 năm là phần tăng cỡ mẫu ngoài mẫu **lớn nhất còn
lại** — mà cỡ mẫu chính là ràng buộc siết nhất của dự án: alpha cần
**22.601 lệnh** để loại được số 0, OOS hiện có ~500.

Đây là lý do thật để chạy ĐO 4, và nó lớn hơn lý do ban đầu (mở khoá BCTC).

### Đúng MỘT biến đổi

Kéo cache. Không đổi mã, không đổi ngưỡng, không đổi `stride`,
`min_history`, `che_do_hoc`, không đổi mặc định nào.

`docs/moc_du_lieu_sach.json` **KHÔNG được sửa**. Mốc là ảnh chụp *"dữ liệu
nào đã tồn tại khi các vòng tối ưu chạy"* — sửa nó là sửa định nghĩa của
vùng kiểm định sau khi đã biết mình muốn gì.

### BỐN phép kiểm dụng cụ, theo THỨ TỰ BẮT BUỘC

**Không đọc bất kỳ con số nào cho tới khi cả bốn qua.**

**1. Sao lưu trước khi kéo.** `backtest/cache/` **đã gitignore** nên không
có lưới an toàn nào từ git. Chép nguyên thư mục ra ngoài repo trước khi
chạy. Không sao lưu thì không kéo.

**2. Vùng CHỒNG LẤN phải giống HỆT từng dòng.** Đây là rủi ro kỹ thuật số
một: một số nguồn trả hệ số điều chỉnh giá KHÁC nhau khi đổi khoảng ngày
yêu cầu. Nếu các dòng 2021-10 → nay đổi sau khi kéo, thì **mọi con số cũ
mất tính tái lập VÀ dữ liệu mới bị nhiễm** cùng lúc.

So từng dòng, từng mã, vùng chồng lấn, trước và sau. **Lệch một dòng nào
là DỪNG** — không phải "sai số nhỏ", mà là dừng.

**3. Kéo phải THUẦN CỘNG THÊM ở phía trái.** Số dòng của vùng chồng lấn
không đổi; chỉ có dòng mới xuất hiện trước mốc cũ.

**4. Chạy lại ĐO 3 trên cache đã kéo, LỌC về đúng khoảng cũ** → phải ra
lại **đúng từng chữ số** bảng ĐO 3. Đây là phép kiểm đầu-cuối; ba phép trên
kiểm dữ liệu, phép này kiểm cả đường ống.

### Đại lượng chính

| # | đại lượng | đọc thế nào |
|---|---|---|
| 1 | **số kỳ BCTC dùng được** (nay 19) | đếm lại, **đừng giả định** ra ~30. Không tăng tới ≥28 thì điều kiện xem lại KHÔNG thoả — dừng, đừng đo IC. |
| 2 | **số mã có vùng OOS** (nay 33/71) và **số phiên OOS** (nay 25.219) | tăng bao nhiêu |
| 3 | **alpha khớp từng lệnh + KTC** trên OOS mở rộng | xem ba kết cục dưới |
| 4 | **IC các chỉ số cơ bản sau Bonferroni** | chỉ đọc khi đại lượng 1 thoả |

### Thiên lệch sống sót — phân tích thẳng, khai TRƯỚC

Rổ là **ảnh chụp hôm nay**. Kéo về 2018 nghĩa là đo giai đoạn 2018–2021 của
những mã **hôm nay còn trong rổ**, tức những mã đã thắng. Mã đã huỷ niêm
yết hay rớt khỏi rổ không có mặt. `NGUYEN-TAC-DO-LUONG.md` đã ghi:
*"chưa xử lý — mọi kết quả vẫn lạc quan hơn thực tế"*. Kéo càng xa, thiên
lệch càng lớn.

**Nhưng nó KHÔNG tác động đều lên mọi đại lượng, và chỗ khác nhau mới là
chỗ đáng đọc:**

| đại lượng | thiên lệch tác động thế nào |
|---|---|
| kỳ vọng mỗi lệnh · lợi nhuận cộng dồn · win rate | **đẹp lên trực tiếp.** Đừng đọc chúng như bằng chứng về gì cả. |
| **alpha khớp từng lệnh** | rổ chuẩn **LÀ chính rổ ấy** — mỗi lệnh so với cầm đều cả rổ trong đúng khoảng nó nắm. Thiên lệch nâng **cả hai vế**, nên nó **phần lớn triệt tiêu ở bậc nhất**. |

**Phần không triệt tiêu, và chưa ai đo:** chiến lược chỉ ở trong thị trường
một phần thời gian, còn rổ chuẩn thì nắm suốt khoảng so sánh. Nếu thiên
lệch nâng lợi nhuận **đều theo thời gian**, vế nắm-suốt hưởng nhiều hơn và
alpha **xấu đi**, không đẹp lên. Nếu nó dồn vào vài cú bứt phá mà chiến
lược tình cờ bắt được, alpha đẹp lên.

**Không đoán chiều.** Ghi ra ở đây để khi thấy số thì đã có sẵn hai lời
giải thích cạnh tranh, thay vì chọn lời giải thích hợp ý sau khi nhìn.

### Ba kết cục, khai trước

| kết cục | đọc thế nào |
|---|---|
| alpha **xấu đi hoặc đứng yên**, KTC hẹp lại vì nhiều lệnh hơn | phù hợp dự kiến. Đây là kết cục **đáng tin nhất**: cỡ mẫu tăng mà kết luận không đổi thì kết luận mạnh lên. |
| alpha **đẹp lên nhưng vẫn chứa 0** | cỡ mẫu tăng, kết luận vẫn là "không phân biệt được với rổ chuẩn". Ghi, đừng mừng. |
| alpha **đẹp lên và LOẠI được số 0 theo chiều dương** | **quy tắc số 1 ở mức mạnh nhất.** KHÔNG ghi vào tài liệu, KHÔNG công bố. Đây sẽ là con số đẹp thứ sáu của dự án, và bốn con số trước đều có một cơ chế giải thích được — ở đây cơ chế ấy **đã có tên trước khi chạy**: thiên lệch sống sót trên một rổ ảnh-chụp-hôm-nay kéo về 2018. Phải loại nó trước, bằng một rổ có mã đã rớt, hoặc không kết luận. |

### Việc KHÔNG được làm trong lượt này

- **Không sửa `docs/moc_du_lieu_sach.json`.**
- **Không đổi ngưỡng, tham số, hay mặc định nào** — ĐO 3 vừa ghim chúng.
- **Không kéo một phần rổ rồi so với phần chưa kéo.** Hai nửa rổ khác
  khoảng dữ liệu thì không so được, và cái lệch sẽ bị đọc thành tín hiệu.
- **Không chạy khi ĐO 3 chưa đọc xong.** Kéo cache trước khi có bảng ĐO 3
  làm bảng ấy khác ĐO 1 vì hai lý do cùng lúc.

### Ước lượng thời gian — nói rõ là ƯỚC LƯỢNG

**Chưa đo.** Chưa ai chạy `extend_history.py` kéo 71 mã về 2018 nên không
có con số. Việc đầu tiên của lượt chạy là kéo **một mã** và bấm giờ, rồi
mới nhân lên — và nói ra rằng phép nhân ấy là ước lượng.

Hạn mức đã biết: 300 req/phút ở hạng silver tại máy, 60 ở gói miễn phí.


---

## ĐO 4 — BẢN BỔ SUNG, khai 11/09/2026 TRƯỚC lượt chạy

**Đã tra trùng:** (bổ sung 14/09/2026) cùng mạch với mục ĐO 4 ở trên — **BƯỚC 50 · BƯỚC 52**. Bản bổ sung chỉ thêm điều khoản đọc cho đúng phép đo ấy, không mở câu hỏi mới.

> Bản ký 10/09 vẫn đứng. Mục này **sửa hai phép kiểm dụng cụ** và nói rõ
> vì sao. Không mục nào ở đây được viết sau khi nhìn một con số kết quả —
> những con số có mặt dưới đây đều là phép đo về **dữ liệu**, chạy xong
> trước khi bất kỳ lượt walk-forward nào bắt đầu.

### Vì sao phải sửa: phép kiểm 2 KHÔNG THỂ ĐỎ

Bản ký viết: *"so từng dòng vùng chồng lấn, TRƯỚC và SAU khi kéo; lệch
một dòng là DỪNG"*.

Nhưng `backtest/data.extend_history()` hợp nhất bằng

```python
merged.drop_duplicates(subset="time", keep="first")
```

với cache đứng **trước** trong `concat` — tức **dòng cũ luôn thắng**. So
trước-với-sau thì hai bên **luôn bằng nhau**, bất kể nguồn trả về gì.
Phép kiểm ấy không có đầu vào nào làm nó đỏ.

Rủi ro nó sinh ra để bắt thì **có thật**. Đo thẳng bản fetch thô ngày
11/09/2026, trước khi hợp nhất:

| mã | chồng lấn | dòng `close` lệch | tỷ lệ fetch/cache |
|---|---|---|---|
| VNM | 1.217 | **1.172** | TB 1,0024 · min **0,9887** |
| VCB | 1.160 | 381 | TB 1,0012 · min **0,9882** |
| FPT | 1.217 | 834 | TB 1,0002 · min 0,9958 |
| ANV | 1.201 | 82 | TB 0,9993 · min 0,9943 |

Lệch có **cấu trúc theo năm**, không phải nhiễu, và không phải làm tròn —
giả thuyết ấy đã bị loại: cả hai bên đều 2 chữ số, và làm tròn bản fetch
về 1 chữ số làm lệch **nhiều hơn**. Biên độ tới **−1,2%**, đúng cỡ một
lần điều chỉnh cổ tức.

**Đây là lỗi 31**, và nó lớn hơn một phép kiểm hỏng: bốn phép kiểm đã ký
chứa một **mâu thuẫn nội tại** mà chỉ phép đo mới lộ ra —

> không thể cùng lúc có *"vùng chồng lấn không đổi"* (phép kiểm 2–3) và
> *"một hệ số điều chỉnh đồng nhất trên cả chuỗi"*.

Giữ dòng cũ thì có vết sẹo ở chỗ nối. Lấy dòng mới thì mọi số đã công bố
mất tính tái lập.

### Người dùng chốt 11/09/2026: tách làm hai cache

```
backtest/cache/        nguyen ven, dong bang — BAN NEO tai lap cho
                       moi so DO 1 / DO 2 / DO 3 da cong bo
backtest/cache_2018/   keo tron khoang trong MOT luot -> toan chuoi
                       MOT he so dieu chinh, khong co cho noi
```

Bản sao đã kiểm băm của cache neo nằm ngoài repo:
`.gemini/antigravity/scratch/vibe_cache_goc_20260911` (125 file, băm gộp
khớp với bản trong repo tại thời điểm chép).

Cơ chế trỏ: biến môi trường `VIBE_CACHE_DIR`, đọc lúc import — vì
`tools/do1_chi_phi_thuc_thi.py` chạy mỗi lượt trong một **tiến trình
riêng**, mà biến toàn cục không đi theo sang tiến trình con.

**Không đặt biến thì đường dẫn y hệt trước, tới từng ký tự.** Đó là một
mệnh đề, nên nó có phép kiểm đứng sau:
`tests/test_cache_tro_duoc.py`, 5 phép kiểm, đục thử 5/5 đỏ. Trong đó
một phép kiểm cố ý chạy ở **tiến trình con** — reload trong tiến trình
cha sẽ xanh trong khi tiến trình con vẫn đọc cache cũ, và đó đúng là cái
bẫy phép kiểm này phải tránh.

### Phép kiểm dụng cụ — BẢN ĐANG DÙNG

Phép kiểm 1 (sao lưu) **giữ nguyên** và đã làm xong.

**2. (THAY) Cache mới phải PHỦ TRỌN cache cũ về mặt NGÀY.** Không được
mất một mã nào, không được mất một phiên nào ở phía phải. Đây là phép
kiểm CÓ THỂ ĐỎ — khác bản cũ.

> Đã chạy: **0 mã thiếu · 0 phiên mất** trên 125/125 mã.

**3. (THAY) Không hợp nhất, nên không có vùng chồng lấn để so.** Thay
vào đó đòi **tính đồng nhất của NGUỒN**: mọi mã phải được trả lời bởi
cùng một nguồn, vì hai nguồn là hai hệ số.

> Đã chạy: **123 mã `kbs`, 2 mã `vci` — HT1 và TCH.** Không đạt tuyệt
> đối. Hai mã ấy được **khai ra ở đây trước khi chạy**, và mọi kết luận
> phải chịu được việc bỏ chúng ra.

**4. (THAY) Không thể đòi "ra lại đúng từng chữ số" bảng ĐO 3.** Giá
vùng trong mẫu cũng đổi, nên phép kiểm ấy mất nghĩa. Thay bằng:

> Chạy lại **trọn vẹn** ĐO 3 trên cache mới, cùng mã, cùng tham số, cùng
> dụng cụ. Kết quả là một bảng ĐO 3 **thứ hai**, đọc như một phép đo độc
> lập trên nền dữ liệu rộng hơn — **không** phải một phép tái lập.

### Dự đoán phải nói TRƯỚC: ngưỡng có thể đổi

Giá vùng **trong mẫu** cũng đổi (tới 1,2%), mà ngưỡng do luật IS chọn
trên chính vùng ấy. Nên **luật có thể chọn ra một số khác 62/45**.

ĐO 3 đã cho thấy đúng chuyện này: đổi độ trễ khớp làm ngưỡng theo-ngày
nhảy 50 → 45. Đó là **lỗi 21**, và đây là trục thứ tư nó xuất hiện.

**Cách đọc, khai trước:**

| ngưỡng ĐO 4 chọn | đọc thế nào |
|---|---|
| **trùng** 62/45 | so được với ĐO 3 theo từng dòng. Khác biệt quy về đúng một vế: dữ liệu. |
| **khác** 62/45 | dòng đó **KHÔNG so được** với ĐO 3. Ghi ra, **không ép so** — y như dòng theo-ngày của ĐO 3. |

### Hai điều KHAI TRƯỚC vì chúng làm kết quả kém sạch

1. **Nguồn không đồng nhất:** HT1 và TCH trả lời bởi `vci`, 123 mã còn
   lại bởi `kbs`. 2/125.
2. **Trần 8 năm có thật, kể cả ở hạng silver.** `kiem_goi()` trả
   `KHỚP · silver · 300 req/phút · còn hạn 22/11/2026`, vậy mà 112/125 mã
   bắt đầu đúng **2018-09-13** — đúng 8 năm tính ngược từ ngày kéo.
   *"Về 2018"* đạt **2018-09**, không phải 2018-01. Và cửa sổ ấy **lùi
   dần mỗi ngày**, nên lượt kéo sau sẽ không ra lại đúng khoảng này.

### Nến ĐANG DỞ — hai chỗ, cả hai đã xử lý trước lượt chạy

**Trong cache MỚI:** lượt kéo chạy lúc 10:14 giờ VN, thị trường đóng cửa
15:00, nên dòng 2026-09-11 là nến nội phiên. **Đã bỏ 123 dòng**, thuần
trừ đi. Dòng cuối nay là 2026-09-10.

Căn cứ là **lịch**, không phải tỷ lệ khối lượng: phiên chưa đóng thì nến
chưa xong. Tỷ lệ khối lượng (trung vị 30%) chỉ là bằng chứng phụ.

**Trong cache CŨ:** 72 file kết thúc bằng nến dở của phiên 2026-09-03 —
trung vị **16%** khối lượng, không file nào bình thường.

```
ma    cache CU        cache MOI       gap
FPT      806.100      4.098.200      5,08 lan
VNM      531.500      3.947.400      7,43 lan
VCB    1.311.300      8.465.900      6,46 lan
LPB      172.800      3.233.600     18,71 lan
```

**Cache cũ KHÔNG được sửa.** Sửa nó là phá mất chính thứ khiến nó có giá
trị — vai trò bản neo tái lập. Lỗi ấy đã tự khỏi ở cache mới, nơi phiên
2026-09-03 được kéo từ một phiên đã đóng.

> Hệ quả phải nhớ khi đọc bảng ĐO 3 cũ: nó được tính với 72 mã mang một
> nến cuối thiếu khối lượng, nằm ở rìa phải, tức vùng TRONG mẫu. Ảnh
> hưởng nhỏ nhưng **khác 0**, và chưa ai đo nó lớn bao nhiêu.

### Ước lượng thời gian — và nói rõ nó là ƯỚC LƯỢNG

ĐO 3 chạy **134,1 phút** trên cache cũ. Cách suy ra con số mới:

```
vung IS  : KHONG doi (cung khoang ngay) -> vong do 7 nguong khong doi
vung OOS : 25.219 -> 147.464 phien (gap ~5,8 lan), nhung OOS chi chay
           MOT luot con IS chay BAY luot
=> phan viec tang khoang 29%  ->  170-180 phut
```

**Đây là ước lượng từ một mô hình, không phải phép đo.** Và ĐO 1 đã cho
thấy cùng một cấu hình chạy lệch **27%** theo tải máy (46,1 so với 36,1
phút), nên con số thật phải được bấm giờ, không được suy.

### Ba kết cục — GIỮ NGUYÊN bản ký 10/09

Không sửa một chữ. Đặc biệt vế thứ ba: alpha đẹp lên **và** loại được số
0 theo chiều dương thì **KHÔNG ghi vào tài liệu, KHÔNG công bố** — thiên
lệch sống sót đã có tên từ trước khi chạy, và kéo càng xa thì nó càng
lớn. Kéo về 2018 là kéo xa nhất từ trước tới nay.


---

## ĐO 5 — chênh 385/376: MÃ hay CACHE? (khai 12/09/2026, trước lượt chạy)

**Không khai được là đã tra vì:** lượt làm ngày 12/09 **KHÔNG tra**, và nó hoá ra **TRÙNG BƯỚC 25** — cùng phép so, cùng kết quả 376/376, cùng phương pháp worktree. Mất 88,8 phút. Đó là lỗi 41. Ghi nguyên trạng thay vì khai bù một lời khai chưa từng tồn tại.

> **Không có dụng cụ vì:** bản đọc chạy một lần rồi nằm lại ở thư mục
> tạm, và hai worktree chứa `wf_oos.db` đã bị gỡ ngay sau lượt chạy —
> nên **con số của mục này không tái lập được** nếu không chạy lại cả
> 88,8 phút. Ghi ra thay vì để người sau tưởng có lệnh.
>
> Việc ấy ít hại hơn vẻ ngoài của nó: **ĐO 5 là bản trùng** của
> `docs/STATE.md` BƯỚC 25 (04/09/2026), nơi cùng phép so đã chạy và
> cùng cho 376/376. Xem BƯỚC 57.

### Câu hỏi, treo từ 04/09/2026

`CLAUDE.md` bản 28/08 ghi **385 lệnh** OOS; lượt chạy ngày 04/09 ở commit
`d777480` ra **376**. Alpha (−0,927 so −0,932) và kỳ vọng (−0,291 so −0,293)
khớp tới **ba chữ số**.

Đó mới là chỗ lạ: nếu chín lệnh thật sự khác nhau thì kỳ vọng đã phải dịch
nhiều hơn thế. Một trong hai con số đang nói về thứ khác với thứ nó nhận.

### Ba cơ chế ĐÃ BỊ LOẠI trước khi chạy (12/09, đọc `git log`, không chạy gì)

| cơ chế | phán quyết |
|---|---|
| `dong_so_sach` xoá lệnh `PENDING` mồ côi | **BÁC** — có từ `25523f5`/`0cce9a5` (26/08), trước **cả hai** lượt |
| `bo_qua`: lệnh không ghép được cặp ngày rổ chuẩn | **BÁC** — đếm từ `d0ea188` (20/08), trước cả hai lượt |
| số lệnh và alpha đếm trên hai dân số khác nhau | **BÁC** — `alpha_so_lenh` không hề được in cho tới `feb760d` (09/09, lỗi 20), nên nó áp cho **CẢ HAI** con số như nhau |

Loại ba cơ chế bằng cách đọc lịch sử là rẻ. Phần còn lại thì không.

### Hai lượt, đúng MỘT biến đổi

| lượt | mã nguồn | vì sao chọn commit này |
|---|---|---|
| **A** | `79a8d32` (28/08 10:57) | chính commit công bố con số **385** |
| **B** | `d777480` (31/08 14:56) | chính commit lượt 04/09 chạy, ra **376** |

Mọi thứ khác giữ **y hệt** giữa hai lượt:

- cùng `backtest/cache/` hôm nay — 125 file, 2021-10-14 → 2026-09-03
- cùng `sl_pattern_memory.json` (chép vào cả hai worktree)
- cùng máy, cùng `.venv`, chạy **tuần tự**, mỗi lượt một tiến trình riêng
- `docs/moc_du_lieu_sach.json` — **đã kiểm bằng `diff`: giống hệt** ở hai commit
- mặc định cả hai: `stride=2` · `min_history=60` · `che_do_hoc=co_san` ·
  chế độ **theo mã** · `MO_PHONG_TRUOT_GIA = True` (kiểm bằng `--help` cho
  ba cái đầu và `git show <commit>:paper_trading.py` cho cái cuối)

### Đại lượng chính

**Số lệnh OOS** ở chế độ theo-mã.

Kèm theo, và bắt buộc: **tập lệnh** (mã · ngày vào · ngày ra) đọc thẳng từ
`wf_oos.db` mà mỗi lượt để lại — để **diff**, chứ không chỉ đếm. Một con số
bằng nhau do hai tập khác nhau bù trừ là thứ phép đếm không thấy.

### Phép kiểm dụng cụ — ĐỌC TRƯỚC SỐ LỆNH

**Ngưỡng KHÔNG ghim được** ở cả hai commit: không commit nào có cờ
`--nguong`, luật tự chọn trên IS. Nên trước khi đọc bất cứ con số nào:

```
hai luot chon CUNG mot nguong   ->  phep so DOC DUOC
hai luot chon KHAC nguong       ->  KHONG EP SO. Bao ra va dung.
```

Khác ngưỡng thì khác biệt quan sát được gồm **cả ngưỡng lẫn mã**, không quy
được cho vế nào — đúng **lỗi 21**, thứ đã làm hỏng một nửa bảng ĐO 1.

### Ba kết cục, khai TRƯỚC

```
A == B            ->  MA KHONG PHAI NGUYEN NHAN.
                      Ket luan la "khong phai ma", KHONG phai "la cache".

|A - B| == 9      ->  MA LA NGUYEN NHAN, va diff hai tap lenh goi ten
                      dung chin lenh ay. Doc co che tu chinh chin lenh do.

khac 0 va khac 9  ->  MA gop MOT PHAN. Phan con lai CHUA QUY DUOC.
                      Ghi thang nhu vay, khong lap bang mot lap luan.
```

### CACHE ĐÃ ĐỔI TRONG CỬA SỔ — đo được, không phải phỏng đoán

Bản đầu của mục này viết *"cache 28/08 không còn tồn tại vì chưa bản nào
được lưu lại"*, nghe như một sơ sót. **Sai, và người dùng sửa lại ngay:**
nội dung ấy bị **ghi đè có chủ đích** bởi một lượt kéo đã quyết.

Dấu vết trên đĩa, đọc bằng `ls -l --time-style` chứ không nhớ:

```
mtime backtest/cache/*.csv      2 file   2026-08-06
                               51 file   2026-08-08
                               72 file   2026-09-03  09:40-09:41
backtest/cache/VNINDEX.csv               2026-09-03  09:45
```

**Đúng 72 file** — chính 72 mã mang nến dở phiên 2026-09-03 đã truy ngày
11/09 (BƯỚC 53). Lượt kéo ấy nằm **giữa** hai lượt 385 (28/08) và 376
(04/09).

Nên vế "cache" không còn là một khả năng mơ hồ. Nó là **một sự kiện có
ngày, có giờ, có số file, và có một quyết định đứng sau**.

### Một đầu vào thứ BA, phát hiện khi soát thiết kế

`consider_entry` gọi **`is_vni_bullish(signal_date)`** (`paper_trading.py`,
có ở CẢ HAI commit). Backtest vì thế đọc `backtest/cache/VNINDEX.csv` —
file cũng bị ghi lại ngày 03/09, lúc 09:45.

Và `15f5794` (03/09) ghi thẳng rằng trước đó **VNINDEX đứng ở 20/08** và
`status()` báo *trễ 7 phiên · cổng TẮT*. Tức bộ lọc thị trường có thể đã ở
hai trạng thái khác nhau giữa hai lượt.

Thiết kế hai worktree **khống chế được** đầu vào này — cả A lẫn B đều đọc
`VNINDEX.csv` hôm nay. Đó chính là điều làm phép so cô lập được MÃ. Nhưng
nó cũng nghĩa là phép so này **không tái dựng** trạng thái VNINDEX của
28/08, và điều đó phải được nhớ khi đọc kết quả.

### Hệ quả cho ba kết cục — siết lại, khai TRƯỚC

Kết cục `A == B` nay đọc được **mạnh hơn** bản đầu: mã không phải nguyên
nhân, và thứ còn lại trong cửa sổ là **lượt kéo 03/09** (72 file giá +
VNINDEX). Vẫn **không** được gọi đó là bằng chứng — phép đo này không chạm
tới nội dung cache cũ, thứ đã bị ghi đè. Nó là **giả thuyết còn lại duy
nhất được nêu tên**, khác hẳn *"chắc là cache"*.

Một suy luận hỗ trợ, ghi **trước** để không bịa ra sau khi thấy số:
`chia_vung` trả `df[ngày < mốc]` làm OOS, nên dữ liệu thêm ở **rìa phải**
không đổi một phiên OOS nào. Lượt kéo 03/09 chỉ chạm được OOS nếu nó **ghi
lại cả hàng lịch sử** (hệ số điều chỉnh đổi — đúng thứ ĐO 4 đo được giữa
hai nguồn, tới −1,2%), chứ không phải chỉ nối thêm vào đuôi. **Chưa ai đo
điều đó**, và nó không đo được sau khi bản cũ đã bị ghi đè.

### Điều KHÔNG được làm sau khi thấy số

Đổi ba kết cục · đổi cấu hình rồi chạy lại cho tới khi ra 9 · bỏ phép kiểm
ngưỡng · hay dựng một cơ chế mới vừa khít con số vừa thấy rồi gọi nó là kết
luận. Ba cơ chế ở bảng trên bị loại **trước** khi chạy, đúng để chuyện đó
không xảy ra.

### Ước lượng thời gian — nói rõ nó là ƯỚC LƯỢNG

ĐO 1 lượt 1, cùng `stride`, cùng rổ: **36,1 phút**. Cùng cấu hình ấy chạy
hôm 08/09: **46,1 phút** — lệch 27% theo tải máy. Hai lượt ước **70–95
phút**. Đây là ước lượng, không phải phép đo.


---

## ĐO 5b — một lượt kéo có GHI LẠI hàng lịch sử không? (khai 12/09/2026)

**Đã tra trùng:** (bổ sung 14/09/2026) nhánh con của ĐO 5, xem **BƯỚC 55**. Nó **không chạy được** (nhóm chứng rỗng theo cấu tạo), nên không có phép đo nào để trùng — và đó cũng là lý do nó không có dụng cụ.

> **Không có dụng cụ vì:** phép đo này **không chạy được** — nhóm chứng
> rỗng theo cấu tạo (53 file chưa bị lượt 03/09 chạm đều nằm NGOÀI rổ
> đo 71 mã). Một dụng cụ cho một thiết kế không chạy được là dụng cụ
> cho một phép đo không tồn tại. Xem BƯỚC 55 và lỗi 39.

> **Khai lúc lượt A của ĐO 5 đang chạy, TRƯỚC khi thấy một con số nào của
> A hay B.** Viết sớm có chủ đích: nếu chờ tới lúc biết `A == B` rồi mới
> khai thì bảng đọc này ra đời sau khi đã biết mình cần nó nói gì.

### Câu hỏi, và vì sao nó quyết định cách đọc ĐO 5

`chia_vung` trả `df[ngày < mốc]` làm OOS. Nên một lượt kéo **chỉ nối thêm
vào đuôi** thì không thể đổi một phiên OOS nào. Nó chỉ chạm được OOS nếu nó
**ghi lại cả hàng lịch sử** — mà điều đó xảy ra được: hệ số điều chỉnh của
nguồn có thể đổi, và ĐO 4 đã đo chênh tới **−1,2%** giữa hai nguồn.

Chưa ai đo việc này. Nó không đo được trên cache 28/08 (đã bị ghi đè), nhưng
**đo được trên một thí nghiệm tự nhiên còn nguyên trên đĩa.**

### Thí nghiệm tự nhiên — hai nhóm, có nhóm chứng

`backtest/cache/` mang hai thế hệ, phân biệt bằng `mtime`:

```
53 file   keo 06-08/08/2026     <- NHOM CHUNG: chua bi luot 03/09 cham
72 file   keo 03/09/2026 09:40  <- NHOM THU
```

`backtest/cache_2018/` là một lượt kéo **thứ ba**, ngày 11/09, và nó phủ
cùng khoảng thời gian. Nó đóng vai **thước chung** cho cả hai nhóm.

### Đại lượng

Với mỗi mã có mặt ở **cả hai** thư mục và có vùng OOS không rỗng: so `close`
trên các ngày chung **nằm trước mốc của chính mã đó** (tức trong vùng OOS).

```
ty le      = cache_2018.close / cache.close
dai luong  = trung vi |ty le - 1| cua ma do
```

Rồi gộp theo nhóm và đọc **trung vị của trung vị**, kèm số mã mỗi nhóm.

### Bốn cách đọc, khai TRƯỚC

```
1. CA HAI nhom ~ 0        ->  luot keo KHONG ghi lai hang lich su khac di.
   (trung vi < 0,001)         Luot 03/09 khong doi duoc gia OOS. Ve "cache
                              doi gia OOS" bi LOAI. Ve "cache doi qua
                              VNINDEX" van con nguyen.

2. nhom 08/08 LECH RO,    ->  he so dieu chinh DOI theo thoi diem keo, va
   nhom 03/09 ~ 0             ban 03/09 khop ban 11/09. Luot keo CO ghi lai
                              lich su -> luot 03/09 DOI DUOC gia OOS cua 72
                              ma. Cache la co che SONG.

3. HAI nhom lech NHU NHAU ->  khac biet den tu NGUON chu khong tu thoi
                              diem. Phep so KHONG doc duoc ve thoi diem keo.
                              Noi thang, khong ep.

4. nhom 03/09 lech ma     ->  NGUOC du kien. Phai truy, khong duoc lap.
   nhom 08/08 khong
```

### Giới hạn phải nêu TRƯỚC, và nó thật

**Không lượt kéo nào trước 11/09 ghi lại NGUỒN đã trả lời.** Đó đúng là lỗ
hổng `fetch_one(nguon=...)` vá ngày 11/09 (BƯỚC 53). Nên với một mã bất kỳ,
tôi **không kiểm được** lượt 08/08 hay 03/09 lấy từ `kbs` hay đã rơi xuống
`tcbs`/`vci`.

Hệ quả: một mã lệch có thể lệch vì **nguồn**, không vì **thời điểm**. Gộp
nhiều mã làm nhẹ chuyện đó nhưng **không khử được nó**. Vì thế cách đọc số
3 tồn tại, và vì thế kết quả dương ở đây là **gợi ý**, không phải quan hệ
nhân quả.

Loại trừ khai trước: **HT1 và TCH** — đã đo ngày 11/09 rằng `cache_2018` lấy
hai mã ấy từ `vci` trong khi 123 mã còn lại từ `kbs`. Giữ chúng lại là cố ý
trộn nguồn vào phép so.

### Điều KHÔNG được làm sau khi thấy số

Đổi bốn cách đọc · đổi ngưỡng 0,001 · bỏ nhóm chứng · hay gộp cách đọc 3
vào cách đọc 1 vì cả hai đều "không thấy hiệu ứng thời điểm". Cách đọc 1 nói
*phép đo chạy và không thấy gì*; cách đọc 3 nói *phép đo không chạy được*.
Hai chuyện khác nhau.


---

## ĐO 6 — khoảng cách chi phí thực thi IS/OOS: THANH KHOẢN hay GIÁ VÀO?

**Đã tra trùng:** (bổ sung 14/09/2026) khoảng cách IS/OOS được **nêu** ở **BƯỚC 50** và nhắc lại ở **BƯỚC 52**, nhưng không mục nào **đo** nó — cả hai đều ghi thẳng *"chưa ai đo"*. ĐO 6 là lần đầu.

> **Dụng cụ đọc:** `tools/do6_tach_chi_phi.py` — chép vào repo ngày
> 12/09/2026 (BƯỚC 59) sau khi phát hiện bản đầu nằm ở thư mục tạm.

*(khai 12/09/2026, trước lượt chạy đầu tiên)*

### Việc treo cuối cùng không bị chặn theo ngày

ĐO 3 (10/09) đo sạch, cùng lượt chạy, cùng ngưỡng 62:

```
trong mau (nguong 62)  : 0,39 diem moi lenh
ngoai mau (1 vs 3)     : 0,63 diem moi lenh     lon hon ~62%
```

Giả thuyết *"0,43 đo ở bản mã cũ"* đã bị loại — cả hai con số đến từ cùng
một lượt. Còn **hai** khả năng, và chưa ai đo:

1. **vùng OOS thanh khoản mỏng hơn** → tác động thị trường lớn hơn
2. **tập lệnh khác nên trung vị giá vào khác** → bước giá 50đ chiếm tỷ lệ
   phần trăm lớn hơn

### Vì sao hai giả thuyết ấy TÁCH ĐƯỢC

`truot_gia.truot_gia()` **đã trả sẵn bảng tách khoản** — không phải một con
số trần trụi:

```python
"phan_chenh_lech": min(tick, thuc_te)   # BUOC GIA   -> gia thuyet 2
"phan_tac_dong":   bien_do * sqrt(ty_trong)  # TAC DONG -> gia thuyet 1
"ty_trong_kl":     khoi_luong_lenh / khoi_luong_nen
```

Hai giả thuyết ứng với **hai trường khác nhau của cùng một hàm**. Không cần
dựng mô hình mới; chỉ cần gọi hàm ấy trên hai dân số lệnh và đọc hai cột.

### Một lượt chạy, hai vùng, KHÁC ĐÚNG MỘT THỨ

`walkforward.py` ở `HEAD`, mặc định (theo mã · `stride=2` · `min_history=60`
· `che_do_hoc=co_san` · `do_tre_khop=1`), trên `backtest/cache/` — tức đúng
cấu hình ĐO 3.

Một lượt sinh ra cả hai dân số cần so:

```
wf_is_62.db   lenh TRONG MAU  o nguong 62
wf_oos.db     lenh NGOAI MAU  o nguong luat tu chon
```

Cùng mã, cùng cache, cùng bộ nhớ, cùng tiến trình. **Khác đúng một thứ:
vùng.**

### PHÉP KIỂM DỤNG CỤ — đọc TRƯỚC mọi con số khác

```
luat chon lai nguong 62  ->  IS(62) va OOS(62) so duoc. Doc tiep.
luat chon nguong KHAC    ->  KHONG EP SO. Bao ra va dung.
```

Khác ngưỡng thì hai dân số khác nhau ở **cả vùng lẫn độ chọn lọc** — đúng
lỗi 21, thứ đã làm hỏng một nửa bảng ĐO 1.

### Đại lượng

Với **mỗi lệnh** ở mỗi vùng, gọi `truot_gia()` hai lần — chiều **MUA** trên
nến vào, chiều **BÁN** trên nến ra — rồi đọc:

| đại lượng | đơn vị | vế nó nói về |
|---|---|---|
| `buoc_gia / gia × 100` | % | **giả thuyết 2** — giá vào thấp thì bước giá nặng hơn |
| `phan_tac_dong / gia × 100` | % | **giả thuyết 1** — thanh khoản mỏng thì tác động lớn hơn |
| `ty_trong_kl` | tỷ lệ | **giả thuyết 1**, đo thẳng |
| giá vào | đồng | trung vị, để đọc vế 2 bằng mắt |

Đọc **trung vị** mỗi vùng, và cả hai chiều cộng lại (một lệnh trả chi phí
hai lần).

### Bốn kết cục, khai TRƯỚC

Khoảng cách phải giải thích là **0,24 điểm mỗi lệnh** (0,63 − 0,39).

```
1. TAC DONG (OOS - IS) x2 giai thich >= 50% cua 0,24
   va BUOC GIA giai thich < 25%              ->  GIA THUYET 1 (thanh khoan)

2. BUOC GIA (OOS - IS) x2 giai thich >= 50%
   va TAC DONG giai thich < 25%              ->  GIA THUYET 2 (gia vao)

3. ca hai deu >= 25%                         ->  CHUA TACH DUOC. Noi thang,
                                                 khong chon ve to hon.

4. ca hai deu < 25%                          ->  chenh 0,24 den tu CHO KHAC:
                                                 lo chan, khop mot phan, vong
                                                 doi lenh — ba thu nam o
                                                 `vong_doi_lenh.py`, KHONG o
                                                 `truot_gia.py`. Do la mot
                                                 PHAT HIEN, khong phai that bai.
```

### Giới hạn phải nêu TRƯỚC

**Phép tách này chỉ phủ trượt giá, không phủ toàn bộ chi phí thực thi.**
`CLAUDE.md` liệt kê tầng hai gồm **bốn** thứ: bước giá · tác động thị trường
· lô chẵn · vòng đời lệnh. Hai thứ đầu nằm trong `truot_gia.py` và tách được
ở đây; hai thứ sau nằm trong `vong_doi_lenh.py` và **không** nằm trong bảng
tách khoản này.

Vì thế kết cục 4 là một khả năng thật, và nó phải đọc được thành *"chi phí
nằm ở hai thành phần kia"* chứ không thành *"phép đo hỏng"*.

Thứ hai: lệnh trong sổ đã khớp ở giá **đã trượt** (mặc định `HEAD` bật trượt
giá). Gọi lại `truot_gia()` trên `entry_price` là tính trượt **của một giá đã
trượt** — lệch một bước ở tầng hai. Chấp nhận được vì đại lượng đọc là **tỷ
lệ giữa hai vùng**, không phải mức tuyệt đối; nhưng nó là lý do **không**
được lấy con số ở đây đem so thẳng với 0,39 hay 0,63.

Thứ ba: **không có nhóm chứng.** Hai vùng khác nhau về thời gian, về rổ mã có
mặt, và về thiên lệch sống sót. Kết quả là **gợi ý về cơ chế**, không phải
quan hệ nhân quả — cùng câu đã ghi cho ĐO 4 và cho ô h = 63.

*(Bài học ĐO 5b, hôm nay: một thiết kế có nhóm phải ĐẾM cỡ nhóm trước khi ký.
Ở đây đã đếm — ĐO 3 cho **399 lệnh OOS** và vòng dò IS ở ngưỡng 62 cho hàng
trăm lệnh. Cả hai nhóm đều không rỗng.)*

### Điều KHÔNG được làm sau khi thấy số

Đổi bốn kết cục · đổi mốc 50%/25% · bỏ phép kiểm ngưỡng · hay chọn vế lớn
hơn khi rơi vào kết cục 3.

### Ước lượng thời gian — nói rõ nó là ƯỚC LƯỢNG

ĐO 3 lượt 1 (cùng cấu hình): **34,9 phút**. Lượt A của ĐO 5 sáng nay, cùng
cache, cùng `stride`: **34,6 phút**. Ước **30–50 phút** cho một lượt. Phần
tách khoản chạy sau, tính bằng giây.


---

## ĐO 7 — "bắt CÙNG PHIÊN" là phép đo hay là giả định? (khai 14/09/2026)

**Đã tra trùng:** (bổ sung 14/09/2026) dụng cụ đọc bảng lỗi ra đời 11/09/2026 và được rà lại ở **BƯỚC 59**. Không mục nào hỏi lại con số *"bắt CÙNG PHIÊN"* có phải một phép đo không — nó được in ra và được trích, thế thôi. ĐO 7 là lần đầu.

**Dụng cụ đọc:** `tools/doc_bang_loi.py`

### Câu hỏi

`tools/doc_bang_loi.py` in một dòng tiêu đề:

```
bat CUNG PHIEN : 31/45
```

Tôi đã **trích con số ấy trong báo cáo cuối ngày nhiều hôm liền** như một
thước cho sức khoẻ quy trình. Nhưng `docs/loi-phan-lop.json` ghi rằng
**23** trong số đó có `nguon = "suy-tu-bang"`, mà chính từ vựng của file
ấy định nghĩa `suy-tu-bang` là

> *"suy từ cột 'bắt bởi' của bảng — **KHÔNG phải phép đo**, chỉ là đọc lại
> thứ đã ghi"*.

Câu hỏi: **trong 23 dòng ấy, bao nhiêu dòng có một CƠ CHẾ nổ, và bao nhiêu
dòng chỉ là một NGƯỜI tình cờ thấy?** Hai thứ đó cho ra cùng một con số 0,
nhưng chúng không nói cùng một điều.

### Vì sao câu hỏi này quan trọng

Một cơ chế nổ (`CI đỏ`, `lượt chạy đầu tiên của chính test ấy`) **chứng
minh** lỗi không sống quá lượt chạy kế tiếp. Một người tình cờ thấy
(`tình cờ`, `trí nhớ`, `đọc lại`) **không chứng minh gì về tuổi thọ** —
lỗi có thể đã nằm đó nhiều ngày, và cái ngày ta nhìn thấy nó chỉ là ngày
ta tình cờ nhìn đúng chỗ.

Gán `song_ngay = 0` cho vế sau là **giả định**, và giả định ấy nghiêng về
phía làm quy trình trông khoẻ hơn thực tế — đúng chiều **Quy tắc số 1**.

### GIỚI HẠN CỦA CHÍNH BẢN KHAI NÀY — nêu trước, và nó thật

**Tôi đã đọc 23 cụm từ trong cột "bắt bởi" TRƯỚC khi viết bản khai này.**
Nên đây **không** phải một lượt khai mù. Tôi chưa tính bất kỳ con số tổng
nào, và luật phân loại dưới đây viết ra trước khi tính — nhưng nó được
viết bởi một người đã thấy dữ liệu thô. Ghi ra để người đọc sau trừ hao
đúng mức, thay vì tưởng đây là một lượt tiền đăng ký như ĐO 1–6.

### Luật phân loại, khai TRƯỚC khi tính

Mỗi dòng đang mang `nguon = "suy-tu-bang"` được đọc lại theo cột *"bắt
bởi"* của chính nó, và **chỉ theo cột ấy**:

| xếp vào | khi cột "bắt bởi" nói tới | vì sao |
|---|---|---|
| **`co-che`** | một lượt chạy MÁY: test, CI, cổng, đục thử, script, lượt đếm tự động, một công cụ tự dừng | máy chạy ở thời điểm xác định → 0 là một phép ĐỌC |
| **`nguoi-thay`** | một người: tình cờ, trí nhớ, đọc lại, tự đi đếm, hệ thống tự hiện ra, một lượt chạy SAU nói ngược lại | không ràng buộc thời điểm lỗi SINH RA → 0 là một GIẢ ĐỊNH |

Biên giới, khai trước để khỏi lách sau:

- *"CI đỏ"* → **`co-che`**, kể cả khi CI chạy ở ngày hôm sau: CI là một
  cơ chế chạy đều, khoảng cách tối đa là một lượt đẩy.
- *"lượt rộng xong sau, nói ngược lại"* → **`nguoi-thay`**: lượt chạy sau
  là một lượt đo MỚI, nó không nói gì về lúc lỗi ra đời.
- *"hệ thống tự hiện"* → **`nguoi-thay`**: cái hiện ra là công cụ, không
  phải lỗi; việc nối hai thứ vẫn do người làm.
- Mơ hồ, không xếp dứt khoát được → **`nguoi-thay`**. Chiều an toàn là
  chiều làm quy trình trông XẤU hơn, không phải đẹp hơn.

### Đại lượng

```
A = so dong xep vao `co-che`
B = so dong xep vao `nguoi-thay`          A + B = 23
C = trong B, bao nhieu dong DO LAI DUOC bang git
```

### Bốn kết cục, khai TRƯỚC

| # | điều kiện | đọc thế nào |
|---|---|---|
| 1 | **B = 0** | thước cũ đứng vững; "31/45" là một phép đọc, không phải giả định. Không đổi gì. |
| 2 | **0 < B ≤ 5** | thước hơi rộng hơn bằng chứng. Tách từ vựng, KHÔNG sửa con số nào cho tới khi đo được. |
| 3 | **B > 5** | **thước cũ không dùng trích dẫn được như đang trích.** Dòng tiêu đề phải tự tách hai vế, và tôi phải ghi một dòng lỗi cho việc đã trích nó nhiều ngày. |
| 4 | **A = 0** | toàn bộ 23 dòng là giả định — đọc lại toàn bộ cách phân lớp, đừng vá. |

### Điều KHÔNG được làm sau khi thấy số

- **Không** sửa `song_ngay` của một dòng `nguoi-thay` thành một con số
  đoán. Không đo được thì để `chua-do` — *"Không biết" là một câu trả
  lời, và nó không được giả dạng một câu trả lời khác.*
- **Không** dời biên giới `co-che` / `nguoi-thay` sau khi thấy A và B.
- **Không** đọc kết quả này thành *"quy trình tệ hơn ta tưởng"*. Nó chỉ
  nói **bằng chứng mỏng hơn ta tưởng**. Hai câu ấy khác nhau.


---

## ĐO 8 — số học đường vốn: cài đặt của ta so với một cài đặt ĐỘC LẬP (khai 14/09/2026)

**Đã tra trùng:** (bổ sung 14/09/2026, tức SAU khi phép đo đã chạy — lỗi 53) **BƯỚC 8** đã định lượng méo mó đòn bẩy từ 31/08/2026 (606/820 lệnh đòi vốn tài khoản không có). KHÔNG trùng: BƯỚC 8 đổi **tập lệnh** (820 → 214) bằng cách đổi thứ tự vòng lặp; ĐO 8 **giữ nguyên** tập lệnh và chỉ đổi cách mô hình hoá tài khoản.

**Dụng cụ đọc:** `tools/do8_doi_chung_duong_von.py`

### Câu hỏi

`paper_metrics.compute()` dựng đường vốn bằng **cộng dồn tuần tự theo ngày
đóng**:

```python
equity = 100.0
for t in closed sorted by exit_date:
    equity *= 1 + (net_return_pct / 100) * (size_pct / 100)
```

Hai lệnh **chồng lấn theo thời gian** vẫn được nhân nối tiếp — tức vốn của
lệnh sau hưởng lãi của lệnh trước, điều chưa từng xảy ra. Bất biến 7b gọi
đó là **đòn bẩy trá hình**, và dự án hiện chỉ **cảnh báo** bằng
`avg_capital_deployed_pct`, chưa bao giờ **định lượng** khoảng cách.

Câu hỏi: **một tài khoản tiền mặt THẬT, vốn cố định, không vay, chạy trên
ĐÚNG tập lệnh ấy, cho lợi nhuận bao nhiêu?**

### Vì sao cần một cài đặt độc lập

Dự án đã **năm lần** cho ra số đẹp vô nghĩa, và ít nhất hai lần nằm ở đúng
tầng này: `+636,11%` (đòn bẩy 2,2 lần) và đường vốn dựng theo `id` thay vì
theo thời gian (23,0% so với 30,7%). Một phép kiểm do **chính tác giả** viết
lại không bắt được lỗi của chính tác giả — đó là bài học lỗi 34 và của cả
mục *"Test KIỂM LẠI CHÍNH NÓ"* trong `CLAUDE.md`.

Nên vế đối chứng phải là **mã của người khác**: `vectorbt`, một thư viện
backtest vector hoá, 9.083 sao, mô hình danh mục có ràng buộc tiền mặt thật
(`cash_sharing`, `SizeType.TargetPercent`).

### RANH GIỚI GIẤY PHÉP — quyết trước, không bàn sau

`vectorbt` dùng **Apache-2.0 with Commons Clause** — GitHub trả
`NOASSERTION` vì nó KHÔNG phải giấy phép nguồn mở OSI. Repo này **công
khai**. Nên:

- **KHÔNG** đưa vào `requirements.txt`. CI và Streamlit Cloud không bao giờ
  cài nó — cùng lựa chọn đã áp cho bốn gói vnstock.
- **KHÔNG** cài vào `.venv` chính. Đo thử 14/09/2026: cài vào đó sẽ nâng
  **pandas 2.3.3 → 3.0.5** và **numpy 2.2.6 → 2.5.3**. Một bước nhảy major
  của pandas đổi số của cả dự án — đúng địa hạt quy tắc số 1.
- Nó sống trong **một venv RIÊNG**, và dụng cụ gọi nó qua tiến trình con,
  trao đổi bằng file. Không mã nào của repo `import vectorbt` ở mức module.

### Đại lượng

```
A = total_net_pct cua paper_metrics.compute()      (cong don tuan tu)
B = loi nhuan cuoi ky cua MOT tai khoan tien mat that, von co dinh,
    khong vay, chay tren DUNG tap lenh ay          (vectorbt)
C = avg_capital_deployed_pct        D = peak_capital_deployed_pct
```

### PHÉP KIỂM DỤNG CỤ — đọc TRƯỚC mọi con số khác

Hai ca dựng tay, **đáp số tính được bằng tay**, nên không vế nào được tin
trước:

| ca | tập lệnh | đáp số đúng, tính tay |
|---|---|---|
| **1** | hai lệnh **KHÔNG** chồng lấn, mỗi lệnh `size_pct=100` | cộng dồn tuần tự LÀ đúng → A phải bằng B |
| **2a** | hai lệnh **CHỒNG LẤN HOÀN TOÀN**, mỗi lệnh `size_pct=50`, `+10%` và `−5%` | `A = 102,375` · `B = 102,500` → **A < B** |
| **2b** | **BA** lệnh chồng lấn, mỗi lệnh `size_pct=50` → cam kết **150%** | tài khoản thật **không cấp vốn nổi** lệnh thứ ba |

**Nếu ca 1 không cho A = B trong dung sai `1e-6` tương đối thì tôi đã cấu
hình vectorbt SAI, và không con số nào khác đọc được.** Dừng, sửa cấu hình,
chạy lại — **không** đọc ca 3.

### SỬA MỘT KỲ VỌNG ĐÃ KHAI — số học tính tay bác nó, TRƯỚC khi chạy

Bản khai đầu (commit `207da19`, 11:11:03) viết cho ca 2: *"A phải LỚN HƠN
B"*. **Sai**, và cái bác nó không phải một lượt chạy — là số học tính tay:

```
Pi(1 + w_i r_i) = 1 + Sigma w_i r_i + Sigma_{i<j} w_i w_j r_i r_j
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      SO HANG CHEO
```

Cộng dồn tuần tự cho **tích**, tài khoản thật cho **tổng có trọng số**.
Khoảng cách chính là số hạng chéo, và **dấu của nó đi cả hai chiều**: hai
lệnh cùng lãi thì tích lớn hơn tổng, một lãi một lỗ thì tích NHỎ hơn.

```
ca 2a  +10% va -5%  : 1,05 x 0,975 = 1,023750  <  0,5x1,10 + 0,5x0,95 = 1,0250
hai lenh cung +10%  : 1,05 x 1,05  = 1,102500  >  0,5x1,10 + 0,5x1,10 = 1,1000
```

**Hệ quả cho cách đọc, và nó lớn hơn phép sửa:** *"cộng dồn lệnh chồng lấn
là đòn bẩy trá hình"* (bất biến 7b) **không** có nghĩa là cộng dồn luôn
thổi số lên. Méo mó có **HAI phần**, và chúng khác hẳn nhau:

| phần | là gì | bậc |
|---|---|---|
| **số hạng chéo** | tích thay vì tổng với lệnh ĐỒNG THỜI | bậc hai, dấu đi hai chiều |
| **cấp vốn** | vốn cam kết vượt 100% — tài khoản thật KHÔNG cấp nổi | bậc nhất, **luôn** thổi lên |

Ca 2b thêm vào đúng để tách hai phần ấy. Phần **cấp vốn** mới là thứ đã
tạo ra `+636,11%` ngày 12/08/2026 ở đòn bẩy 2,2 lần.

> Ghi lại phép sửa này thay vì lặng lẽ sửa: một kỳ vọng đã ký mà bị bác
> **trước khi chạy**, bởi số học chứ không bởi số liệu, là thứ đáng giữ
> nhất trong một bản khai. Nó cũng là bằng chứng bản khai được đọc lại
> chứ không chỉ được viết ra.

### Ba ca, và ca 3 mới là ca có ý nghĩa

Ca 3 chạy trên **sổ lệnh thật** đã đóng băng thành file để tái lập được
(bài học BƯỚC 60: một phép đo chỉ chạy được một lần là một phép đo chỉ-đọc).

### Bốn kết cục, khai TRƯỚC

| # | điều kiện | đọc thế nào |
|---|---|---|
| 1 | `\|A − B\| ≤ 0,5` điểm **VÀ** `D ≤ 100%` | số học hai bên khớp; tập lệnh này không có đòn bẩy trá hình. Không đổi gì. |
| 2 | `\|A − B\| > 0,5` điểm **VÀ** `D > 100%` | **khoảng cách LÀ đòn bẩy trá hình, và nay đo được** thay vì chỉ được cảnh báo. Ghi con số vào tài liệu; KHÔNG sửa `compute()` trong cùng PR. |
| 3 | `\|A − B\| > 0,5` điểm **NHƯNG** `D ≤ 100%` | chỉ còn **số hạng chéo** giải thích được. Nếu độ lớn không khớp số hạng chéo tính tay thì một trong hai cài đặt sai, và giả định đầu tiên là **của TA** (quy tắc số 1). |
| 4 | `B > A` trên tập lệnh có `D > 100%` | bất ngờ: phần cấp vốn lẽ ra **luôn** thổi A lên. **Phải truy**, không được nhận. |

### Giới hạn phải nêu TRƯỚC, và chúng thật

1. **Phép đo này KHÔNG nói gì về chiến lược.** Nó chỉ hỏi: *hai cài đặt có
   cùng số học không*. Alpha, kỳ vọng, ngưỡng — không đại lượng nào trong
   ĐO 8 chạm tới.
2. **Chi phí TẮT ở CẢ HAI VẾ.** Mô hình trượt giá của vectorbt là **phần
   trăm của giá** (`enums.py`: *"Slippage in percentage of Order.price"*),
   trong khi chi phí của ta do **bước giá 50đ** quyết định — hai thứ khác
   hẳn. Bật lên là so hai mô hình chi phí, không phải so số học.
3. **Không so được về khớp lệnh.** vectorbt không có biên độ ±7%, không có
   trần thanh khoản mỗi nến, không có vòng đời lệnh. Nên tập lệnh phải
   được **truyền vào** cả hai vế y hệt, không bên nào tự sinh lệnh.
4. **Một mình vectorbt không phải trọng tài.** Ở ca 1 và 2, trọng tài là
   **số học tính bằng tay**. vectorbt chỉ là vế thứ ba để ca 3 đọc được.

### Điều KHÔNG được làm sau khi thấy số

- **Không** sửa `paper_metrics.compute()` trong cùng PR với phép đo. Đo và
  sửa trong một lượt thì không ai đọc được cái nào có trước.
- **Không** đọc kết cục 2 thành *"mọi con số cũ của dự án đều sai"*. Bất
  biến 7b đã nói điều đó từ đầu; ĐO 8 chỉ thay một cảnh báo định tính bằng
  một con số.
- **Không** đổi dung sai `0,5` điểm sau khi thấy `A − B`.
- **Không** bỏ ca 1 nếu nó đỏ. Ca 1 đỏ nghĩa là dụng cụ sai, và mọi con số
  sau đó vô nghĩa.
