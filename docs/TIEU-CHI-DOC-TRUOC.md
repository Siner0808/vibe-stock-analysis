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


---

## ĐO 9 — Fibonacci vào ĐƯỜNG SINH LỆNH: có đổi alpha không? (khai 15/09/2026)

**Đã tra trùng:** **BƯỚC 78** (15/09/2026) dựng `muc_fibonacci` nhưng **chỉ
để hiện** — chưa lượt đo nào đưa nó vào đường sinh lệnh. **BƯỚC 8** đo méo
mó đòn bẩy, không liên quan. Công tắc `CHOT_LOI_CUNG` đã được đo một lần
(`CLAUDE.md` mục *"Chốt lời cứng đã bị gỡ"*: phương sai −24%, alpha không
đổi) — ĐO 9 **dùng lại** kết quả ấy làm **phép kiểm dụng cụ**, không đo lại
nó như một phát hiện mới.

**Dụng cụ đọc:** `tools/do9_fibonacci_duong_lenh.py`

### Câu hỏi

`muc_fibonacci.doc_muc()` cho SL và TP **suy từ cấu trúc giá**. Đường sinh
lệnh hiện dùng SL theo ATR (kẹp 4–6,5%) và TP **+20% cứng** — một hằng số
không liên quan tới mã nào cả.

Câu hỏi: **thay chúng bằng mức Fibonacci có đổi alpha khớp từng lệnh
không?**

### Điều đã biết TRƯỚC khi chạy, và nó làm hiệu ứng nhỏ lại

Đo 15/09 trên rổ cache (BƯỚC 78): **80/125 mã** dựng được mức, và trong 80
mã đó **62 mã KHÔNG vừa ngân sách rủi ro 4–6,5%**. Theo hai quyết định cài
đặt dưới đây, Fibonacci chỉ áp được cho **≈18/125 mã ≈ 14% rổ**.

> **Khai trước:** hiệu ứng sẽ NHỎ vì mẫu áp dụng nhỏ. Một Δalpha lớn ở cỡ
> mẫu này là dấu hiệu LỖI, không phải dấu hiệu tốt — xem kết cục 3.

### HAI quyết định cài đặt, chốt TRƯỚC khi chạy

Chọn sau khi thấy số là bất biến 7 đổi hướng. Nên chốt ở đây:

1. **`ket_luan_duoc = False`** (không đủ bằng chứng cấu trúc) → **dùng ATR
   như cũ**. KHÔNG bỏ lệnh. Bỏ lệnh sẽ đổi **tập lệnh**, và khi đó khác
   biệt quan sát được không quy được cho vế nào — đúng lỗi 21.
2. **`vua_ngan_sach = False`** (rủi ro > 6,5%) → **dùng ATR như cũ**. Ngân
   sách rủi ro là ràng buộc đã chọn của hệ thống; nới nó là đổi hai thứ
   cùng lúc.

### HỆ QUẢ XUÔI DÒNG, khai trước vì nó KHÔNG hiển nhiên

`consider_entry` tính cỡ vị thế bằng **rủi ro chia khoảng cách SL**:

```python
sl_pct_dist = (entry_price - stop_loss) / entry_price
size        = account_risk_pct / sl_pct_dist
```

Nên **đổi SL là đổi luôn CỠ VỊ THẾ**. SL Fibonacci rộng hơn → cỡ nhỏ
hơn → vốn cam kết thấp hơn → trần vốn ít chạm hơn → **tập lệnh xáo**.

> Đây là hệ quả xuôi dòng của **đúng một biến** (SL), không phải một
> biến thứ hai — nên phép so A↔B vẫn quy được về một vế. Nhưng nó
> **không** phải phép so cùng-tập-lệnh-khác-SL, và bản báo cáo phải
> nói ra điều đó. Đúng bài học ĐO 2, nơi câu *"tập tín hiệu không
> đổi"* bị đọc thành *"tập lệnh không đổi"* và tập lệnh xáo 15–27%.

**Phải đo và ghi:** cỡ vị thế trung bình, vốn cam kết trung bình/đỉnh,
và tỷ lệ xáo tập lệnh — ở CẢ BỐN lượt. Thiếu ba con số đó thì không
đọc alpha.

### Bốn lượt, chế độ THEO NGÀY, trượt giá BẬT

Chế độ theo ngày vì đó là **dòng duy nhất có danh mục thật** (vốn đỉnh đúng
100%) và là dòng đáng tin nhất theo bất biến 7.

| lượt | SL | mức TP | `CHOT_LOI_CUNG` | vai trò |
|---|---|---|---|---|
| **A** | ATR | +20% | TẮT | **đối chứng** = hiện hành |
| **B** | **Fibonacci** | +20% | TẮT | chỉ đổi **SL** |
| **C** | ATR | +20% | **BẬT** | chỉ đổi **công tắc** — PHÉP KIỂM DỤNG CỤ |
| **D** | **Fibonacci** | **Fibonacci** | **BẬT** | đổi cả ba |

**Chỉ ba phép so đọc được:** A↔B (SL) · A↔C (công tắc) · C↔D (mức TP, với
công tắc đã bật). So A↔D là so ba thứ cùng lúc — **không đọc**.

### PHÉP KIỂM DỤNG CỤ — chạy trước, và nó có quyền dừng cả phép đo

Lượt C phải tái lập hình dạng đã biết của `CHOT_LOI_CUNG=True`: **phương sai
giảm đáng kể, alpha KHÔNG đổi trong phạm vi KTC**. Nếu C cho alpha nhảy vọt
hoặc phương sai không giảm → **dụng cụ bẩn, dừng, không đọc B và D**.

### Hai chốt chặn TRƯỚC khi đọc bất kỳ con số nào

- **Vốn đỉnh phải = 100%** ở cả bốn lượt. Vượt → bất biến 7b, số cộng dồn
  là của một tài khoản vay được. Không đọc.
- **Số lệnh OOS không được rơi quá 30%** so với lượt A. Rơi nhiều → tập
  lệnh đã khác hẳn, không còn là phép so.

### Bảng kết cục — ký TRƯỚC, đọc alpha của A↔B

| # | điều kiện | đọc thế nào |
|---|---|---|
| **1** | \|Δalpha\| < ½ bề rộng KTC của A | **Không phân biệt được.** Fibonacci SL không đổi gì ở cỡ mẫu này. **Đây là kết cục DỰ KIẾN** — rho ≈ 0, và chỉ ~14% lệnh đổi SL. |
| **2** | Δalpha < 0, vượt ½ bề rộng | Fibonacci SL **làm xấu đi**. Kết luận: đừng đưa vào. |
| **3** | Δalpha > 0, vượt ½ bề rộng | **NGHI NGỜ TRƯỚC — quy tắc số 1.** Chỉ ~14% lệnh đổi SL mà alpha nhảy vượt nửa KTC là dấu hiệu LỖI. Phải truy nguyên nhân TRƯỚC khi ghi là kết quả. |
| **4** | tập lệnh xáo > 10% | Vẫn đọc alpha, **nhưng phải ghi rõ**: đây KHÔNG phải phép so cùng-tập-lệnh. Hệ quả xuôi dòng của một biến — đúng như ĐO 2 (xáo 15%/27%). |

### Điều KHÔNG được làm sau khi thấy số

- Không nới biên 4–6,5% cho Fibonacci "vừa" hơn.
- Không đổi hai mức 0,5/0,618 hay 1,272/1,618 rồi chạy lại.
- Không đổi chế độ hay ngưỡng để tìm một ô đẹp hơn.

Cả ba đều là **bất biến 7**: quét N cấu hình rồi lấy cái đẹp nhất là đo độ
may của phép tìm kiếm.

### Mặc định sau phép đo

Công tắc `DUNG_MUC_FIBONACCI` mặc định **TẮT**, và **chỉ đổi mặc định nếu
kết cục là 2 hoặc 3-đã-truy-xong**. Kết cục 1 → giữ TẮT, vì "không phân biệt
được" không phải lý do để đổi một thứ đang chạy.

---

## ĐO 10 — `vnstock` 4.0.7 → 4.0.8: thư viện có đổi CON SỐ không? (khai 17/09/2026)

**Dụng cụ đọc:** `tools/do10_nang_vnstock.py` — chạy hai lượt,
`truoc` (trước khi nâng) rồi `sau` (sau khi nâng).

**Đã tra trùng:** **BƯỚC 87** (16/09/2026) quyết định **không** nâng
`vnstock` 4.0.8 — nhưng lý do ở đó là *"không ai hỏi"*, và nó **không đo
gì** về 4.0.8. Không BƯỚC nào khác chạm tới bản này. Phép đo `vnai` 2.6.0
cùng ngày là **thư viện khác**, và nó dừng ở phép so mã nguồn vì hai file
quyết định dữ liệu giống hệt từng byte — ở đây thì **không**.

**Người dùng hỏi ngày 17/09/2026.** Đó là thứ đổi, không phải dữ kiện nào.

### Vì sao bản này KHÔNG đọc được bằng phép so mã nguồn

`vnai` 2.6.0 đóng lại nhanh vì hai file quyết định dữ liệu — `PERIOD_LIMITS`
và `_detect_tier` — **giống hệt từng byte**. Tải bánh xe 4.0.8 về so
(KHÔNG cài), kết quả khác hẳn:

```
4.0.7 : 130 file .py      4.0.8 : 129 file .py
THEM  : core/utils/{block_detect,circuit,retry}.py
MAT   : core/base/{__init__,provider,registry}.py · core/utils/proxy_manager.py
DOI   : 52 file
```

**Mọi file trên đường dữ liệu đều đổi**, không sót cái nào:

```
api/quote.py · api/financial.py · api/trading.py · api/listing.py
explorer/vci/{quote,financial,listing,trading,company}.py
explorer/kbs/{quote,financial,listing,trading,company}.py
core/utils/parser.py   46.301 -> 39.097 byte   (-16%)
```

Nên câu hỏi *"nó có đổi số không"* **không trả lời được bằng cách đọc mã**.
Phải kéo dữ liệu thật, cùng tham số, trước và sau.

**Ràng buộc phụ thuộc đã kiểm:** 4.0.8 đòi `vnai>=2.6.0` (máy có 2.6.0, nâng
hôm qua) và `vnstock_ezchart>=1.0.2` (máy có 1.0.2). Cả hai **đã thoả** —
phép nâng này không kéo theo gói nào khác.

**Bề mặt repo dùng, đã đếm:** chỉ ba lối công khai — `from vnstock import
Quote, Trading, Finance`, `from vnstock.api.quote import Quote`,
`from vnstock.api.financial import Finance`. **Không** file nào chạm bốn
module bị gỡ. Nên phép nâng không làm hỏng lối gọi; câu hỏi duy nhất còn
lại là **con số**.

### Bốn đại lượng, và vì sao mỗi cái đọc được ở mức nào

| | đại lượng | đọc được gì |
|---|---|---|
| **A** | `Quote(ma, source).history(start, end, "1D")` trên khoảng ĐÃ ĐÓNG | **từng ô** — dữ liệu đã đóng thì bất biến |
| **B** | `Trading(source="vci").price_board([...])` | **chỉ TẬP CỘT** |
| **C** | `Finance(ma, source).ratio()` | **số kỳ + tập cột** |
| **D** | `vnstock_goi.kiem_goi()` | nguyên dòng |

**Giới hạn nêu trước, và nó quyết định cách đọc từng ô.** A đo trên khoảng
**đã đóng** (2024-01-02 → 2024-03-29) nên nó **phải** bất biến: nếu nó đổi
thì đó là thư viện đổi, **không phải thị trường đổi**. B thì ngược lại —
bảng giá đổi theo từng phiên, nên so giá trị ở đó là so hai thời điểm khác
nhau; chỉ **tập cột** mới là lời hứa của thư viện. C nằm giữa: số kỳ và tập
cột là hợp đồng, còn giá trị thì nguồn có thể điều chỉnh hồi tố.

Ba mã: **FPT · VCB · SSI** — hai sàn, ba ngành, và cả ba nằm trong rổ dự án
đang dùng.

### BẢNG ĐỌC — ký trước, không sửa sau khi thấy số

```
A khac DU MOT O                         ->  KHONG NANG
B hoac C doi TAP COT                    ->  KHONG NANG
A giong het + B,C tap cot giong + D giong ->  NANG DUOC, neu 5 cong xanh
khong keo duoc du lieu (mang, han muc)  ->  CHUA KET LUAN DUOC, khong nang
```

**Ba ô, không phải hai** — cùng quy ước với `lich_giao_dich.chan_doan` và
`vnstock_goi.kiem_goi`. Ô thứ ba bắt buộc: một lượt kéo hỏng mà bị đọc
thành *"không đổi gì"* là đúng lỗi 66.

**Ô `KHÔNG NÂNG` là ô làm bảng này thành phép kiểm.** Chỉ có ô "nâng được"
thì đây là một lời tiên tri không thể sai.

### Điều KHÔNG hứa

Phép đo này **không** nói 4.0.8 tốt hay xấu. Nó trả lời đúng một câu: *bản
mới có làm đổi những con số dự án đang đứng trên không.* Ba module mới —
`circuit.py`, `retry.py`, `block_detect.py` — là cơ chế chống chặn và thử
lại; tác dụng của chúng chỉ lộ ra khi nguồn chặn, tức **ngoài tầm** một
lượt kéo bình thường. Ghi ra để sau này không ai đọc kết quả này rộng hơn
nó có.

---

## Kết quả ĐO 10 — chạy 17/09/2026, đọc theo bảng đã ký

**Dụng cụ đọc:** `tools/do10_nang_vnstock.py`

Tiêu chí vào nhánh lúc **10:26:56**, lượt chụp `truoc` bắt đầu **10:27:01**
— năm giây sau, và **trước khi đổi một gói nào**.

| | 4.0.7 | 4.0.8 | |
|---|---|---|---|
| **A** FPT · VCB · SSI | 65 dòng · 6 cột | 65 dòng · 6 cột | **băm SHA-256 giống hệt cả ba** |
| **B** bảng giá | 82 cột | 82 cột | tập cột y nguyên |
| **C** `ratio()` × 3 | 54 kỳ · 19 cột | 54 kỳ · 19 cột | y nguyên |
| **D** `kiem_goi()` | `KHỚP · silver/silver` | giống hệt | |

```
PHAN QUYET: NANG DUOC
```

**Phép nâng chỉ chạm đúng một gói.** `pip freeze` trước/sau khác **một
dòng** — dòng `vnstock`. Cài bằng `--no-deps` vì hai sàn phụ thuộc mới
(`vnai>=2.6.0`, `vnstock_ezchart>=1.0.2`) **đã thoả từ trước**, nên không
có gói nào bị kéo theo.

Chạy lại phép so trên bản tải thẳng từ PyPI (chứ không phải bánh xe tạm
trong thư mục scratch) — **cùng kết quả**.

### Điều bảng đã ký KHÔNG hỏi, và hoá ra là câu hỏi lớn hơn

Xem `docs/STATE.md` BƯỚC 94.

---

## ĐO 11 — `streamlit` 1.60.0 → 1.64.0: bản CI đang phục vụ người dùng có chạy được ở máy này không? (khai 17/09/2026)

**Dụng cụ đọc:** `tools/do11_nang_streamlit.py` — chạy hai lượt, `truoc`
(trước khi nâng) rồi `sau` (sau khi nâng).

**Đã tra trùng:** **BƯỚC 94** (17/09/2026) là chỗ vế lệch này được đo ra,
và nó cố ý **không** sửa trong cùng PR — *"nó là một phép nâng khác và cần
bảng đọc riêng"*. Đây là bảng đọc ấy. Không BƯỚC nào khác trong
`docs/STATE.md` chạm tới `streamlit` như một đại lượng.

**Một lượt quét thăm dò ĐÃ CHẠY TRƯỚC KHI KÝ, và đây là chỗ khai nó.** Nó
đếm **quần thể**: 185 file `.py` quét, **24** tên `st.*` được gọi, **0**
tên thiếu ở 1.60.0. Nó **không** phải lượt `truoc`, và nó không đọc được
gì về 1.64.0 — phán quyết của bảng này là một phép **SO giữa hai lượt**,
mà lượt thứ hai chưa tồn tại lúc ký. Khai ra vì lỗi 79 vừa dạy đúng bài
ấy: một dữ kiện không ai hỏi thì không ai biết.

### Vì sao câu hỏi này KHÁC câu hỏi của ĐO 10

ĐO 10 hỏi *thư viện có đổi CON SỐ không*. `streamlit` **không nằm trên
đường dữ liệu** — nó không kéo giá, không chấm điểm, không sinh lệnh. Nên
câu hỏi ở đây là câu khác: **bản mà CI và Streamlit Cloud đang chạy có
chạy được ở máy này không.**

Chiều của phép nâng cũng ngược. Ở ĐO 10 máy local đuổi theo PyPI; ở đây
máy local đuổi theo **bản đang phục vụ người dùng**. `requirements.txt`
khai `streamlit` **không có sàn** — trần trụi một dòng, không cả `>=` —
nên Cloud lấy bản mới nhất ở mỗi lượt deploy.

### Bốn đại lượng, và mỗi cái đọc được ở mức nào

| | đại lượng | đọc được gì |
|---|---|---|
| **A** | tập tên `st.*` repo gọi, suy bằng AST | tên nào **biến mất** |
| **B** | mọi từ khoá tại mọi lời gọi `st.X(kw=…)`, so với `inspect.signature` | chữ ký nào **siết lại** |
| **C** | ba module `import streamlit` nạp trong tiến trình riêng | nạp có **nổ** không |
| **D** | `streamlit run app.py` headless → `/_stcore/health` | máy chủ có **dựng được** không |

**GIỚI HẠN NÊU TRƯỚC, và nó quyết định cách đọc cả bảng.** Không ô nào
trong bốn ô đọc được thứ người dùng thật sự nhìn — **trang đã dựng**. D
chỉ chứng minh máy chủ trả lời; nó không chứng minh một widget nào vẽ
đúng. Bốn ô này bắt **loại hỏng ồn ào** (tên mất · chữ ký siết · import
nổ · máy chủ chết) và **không** bắt **loại hỏng im lặng** (một widget đổi
cách hiển thị, một khoảng cách lệch đi). Vế im lặng ấy ĐO 11 **không đọc
được** — nói ra ở đây thay vì để người đọc tự suy ra sau.

A và B **suy từ AST, không gõ tay**: thêm một `st.*` mới vào app thì quần
thể tự rộng ra theo. B là ô sắc hơn A, vì cách một thư viện giao diện phế
truất thường là **giữ tên, bỏ tham số**.

### BẢNG ĐỌC — ký trước, không sửa sau khi thấy số

```
A  mot ten BIEN MAT                        ->  KHONG NANG
B  mot tu khoa bi CHOI THEM                ->  KHONG NANG
C  mot module dang nap duoc ma NAP NO      ->  KHONG NANG
D  may chu dang dung duoc ma KHONG DUNG    ->  KHONG NANG
   bon o GIONG hoac TOT LEN                ->  NANG DUOC, neu 5 cong xanh
   khong chay duoc mot luot nao            ->  CHUA KET LUAN DUOC, khong nang
```

**Ba ô, không phải hai** — cùng quy ước với `vnstock_goi.kiem_goi` và ĐO
10. Ô thứ ba bắt buộc: một lượt không chạy nổi mà bị đọc thành *"không đổi
gì"* là đúng lỗi 66.

**Ô `KHÔNG NÂNG` là thứ làm bảng này thành phép kiểm.** Chỉ có ô "nâng
được" thì đây là một lời tiên tri không thể sai.

### Và nếu phán quyết LÀ `KHÔNG NÂNG` thì phải làm gì

Khi ấy vế lệch **ở lại**, và đó **không** phải trạng thái an toàn: nó
nghĩa là mọi cổng xanh đang xanh trên một bản mà máy này chưa bao giờ
chạy. Việc phải làm khi đó là **ghim sàn `streamlit` trong
`requirements.txt`** để CI thôi trôi, rồi khai lý do — chứ không phải im
lặng để nguyên. Khai điều này TRƯỚC, vì một nhánh không có việc đi kèm là
một nhánh sẽ bị bỏ qua.

---

## Kết quả ĐO 11 — chạy 17/09/2026, đọc theo bảng đã ký

**Dụng cụ đọc:** `tools/do11_nang_streamlit.py`

Tiêu chí vào nhánh lúc **13:50:14** (commit `f6284c1`), lượt chụp `truoc`
bắt đầu **13:50:18** — bốn giây sau, và **trước khi đổi một gói nào**.

| | 1.60.0 | 1.64.0 | |
|---|---|---|---|
| **A** 27 tên `st.*` | 27 có · 0 thiếu | 27 có · 0 thiếu | không tên nào mất |
| **B** 19 cặp (tên, từ khoá) | 19 nhận · 0 chối | 19 nhận · 0 chối | không chữ ký nào siết |
| **C** 3 module nạp | 3/3 | 3/3 | |
| **D** `/_stcore/health` | `ok` sau 3,5s | `ok` sau 1,1s | 0 traceback cả hai |

```
PHAN QUYET: NANG DUOC
```

**Phép nâng chạm ĐÚNG HAI gói, và gói thứ hai đi XUỐNG.** `pip freeze`
trước/sau khác hai dòng:

```
streamlit   1.60.0  ->  1.64.0     nang
websockets  17.0.1  ->  16.1.1     HA, vi streamlit 1.64 ghim `<17`
```

`websockets` 16.1.1 đúng bằng bản CI đang chạy, nên phép hạ ấy **thu hẹp**
bất đối xứng chứ không mở rộng.

### Một dòng cảnh báo của `pip` mà bảng đã ký KHÔNG có ô cho nó

```
pyppeteer 2.0.0 requires websockets<11.0, but you have websockets 16.1.1
```

Đọc thẳng chứ không đoán, ba lượt, và kết luận đi **ngược** vẻ ngoài của nó:

- `pyppeteer` do `requests-html` kéo về; `requests-html` có
  `Required-by:` **rỗng** — không gói nào cần nó.
- Không file nào trong repo nạp `requests_html`; và trong toàn bộ
  `site-packages`, không gói nào nạp nó ngoài chính nó.
- Nhật ký CI: **0 lần** xuất hiện `pyppeteer` hay `requests-html`. CI chưa
  bao giờ có hai gói ấy.
- Và ràng buộc là `<11.0`, trong khi máy **đã** ở `17.0.1` **trước** phép
  nâng. Xung đột ấy **có sẵn**; phép nâng không tạo ra nó, chỉ làm `pip`
  nói ra.

Nên nó không vào bảng đọc, và cũng không bị bỏ qua: nó là **hai gói mồ côi
chỉ có ở máy này**.

### Giới hạn của ĐO 11, nhắc lại sau khi có số

Bốn ô không ô nào nhìn **trang đã dựng**. D chứng minh máy chủ trả lời
`ok`; nó không chứng minh một widget nào vẽ đúng. Điều đó đã khai **trước**
khi chạy, và nó vẫn đúng sau khi chạy.

### Điều bảng đã ký KHÔNG hỏi, và hoá ra lớn hơn

Xem `docs/STATE.md` BƯỚC 95.

---

## ĐO 12 — `plotly` 6.9.0 → 7.1.0: biểu đồ có nói chuyện khác đi không? (khai 17/09/2026)

**Dụng cụ đọc:** `tools/do12_nang_plotly.py` — chạy hai lượt, `truoc`
(trước khi nâng) rồi `sau` (sau khi nâng).

**Đã tra trùng:** **BƯỚC 95** (17/09/2026) là chỗ vế lệch này được đo ra,
và nó nêu đích danh *"vế đáng làm tiếp"*. Không BƯỚC nào khác trong
`docs/STATE.md` chạm tới `plotly` như một đại lượng.

### Vì sao bản này KHÁC hai phép nâng trước, và khác theo chiều nguy hơn

`vnstock` 4.0.8 và `streamlit` 1.64.0 là **bản phụ**. Đây là **bản
CHÍNH** — 6 → 7 — và nó ở đúng thư viện vẽ mọi biểu đồ người dùng nhìn.
Streamlit Cloud cài từ `requirements.txt` nên **người dùng đang xem biểu
đồ do 7.1.0 vẽ**, trong khi mọi lượt kiểm ở máy này chạy trên 6.9.0.

Bề mặt repo dùng thì nhỏ, và đã đếm bằng AST: `go.Figure` · `go.Candlestick`
· `go.Scatter` · `go.Bar` · `make_subplots`, ở hai file (`app.py`,
`trade_review.py`).

### DỮ LIỆU và TRANG TRÍ là hai câu hỏi khác nhau

Một phép nâng bản CHÍNH gần như **chắc chắn** đổi vài mặc định trình bày.
Nếu bảng đọc chỉ hỏi *"đặc tả figure có giống hệt không"* thì nó đã tự
định sẵn câu trả lời `KHÔNG NÂNG` — một lời tiên tri không thể sai theo
chiều ngược lại, và cũng vô dụng y như vậy.

Nên bảng này tách ba, và chỉ hai phần đầu có quyền phán:

| | đo gì | quyền phán |
|---|---|---|
| **D1** | **dữ liệu từng trace** — loại trace, và các mảng `x`/`y`/`open`/`high`/`low`/`close`/`text` | **CÓ** |
| **D2** | **hình và chú thích trong layout** — đường cắt lỗ · chốt lời, vạch ngày tín hiệu, dải *"agent chưa biết vùng này"* | **CÓ** |
| **E** | phần còn lại của layout — template, màu nền, lề, chiều cao, legend | **KHÔNG** — ghi ra để đọc |

D2 **có** quyền phán vì nó không phải trang trí: đường cắt lỗ mang một
con số người đọc hành động theo. Xếp nó vào trang trí là đúng cái lỗi
`TP1 chỉ-để-hiện` vừa sửa sáng nay.

### Bốn đại lượng

| | đại lượng | đọc được gì |
|---|---|---|
| **A** | tập tên `go.*` + `make_subplots` repo gọi, suy bằng AST | tên nào **biến mất** |
| **B** | mọi từ khoá tại mọi lời gọi, so với `inspect.signature` | chữ ký nào **siết lại** |
| **C** | `trade_review` nạp trong tiến trình riêng | nạp có **nổ** không |
| **D** | `trade_review.build_figure()` trên một bảng giá **cố định** | biểu đồ có nói chuyện khác đi không |

**D là ô sắc nhất, và đây là lý do nó dựng được.** `build_figure()` là
hàm **thuần**: nhận một `DataFrame` và một lệnh, trả một `go.Figure`,
không chạm mạng và không đọc file trạng thái. Nó là biểu đồ **hoàn
chỉnh** duy nhất của dự án dựng được mà không cần một lượt Streamlit
chạy — và nó là mã đang giao, không phải mã dựng riêng để đo.

Bảng giá đầu vào **sinh bằng công thức đóng**, không dùng ngẫu nhiên và
không đọc cache: cùng một đầu vào ở cả hai lượt là điều kiện để phép so
quy được về một vế.

**GIỚI HẠN NÊU TRƯỚC.** Không ô nào nhìn **biểu đồ đã vẽ ra trong trình
duyệt**. D so **đặc tả** figure — thứ plotly gửi sang trình duyệt — chứ
không so các điểm ảnh. Một thay đổi nằm hoàn toàn trong phần JavaScript
của plotly, không chạm đặc tả, thì ĐO 12 **không đọc được**. Vế ấy nói ra
ở đây thay vì để người đọc tự suy.

Và `app.py` có một biểu đồ thứ hai (`make_subplots` + `go.Candlestick` +
`go.Bar`) nằm **trong thân script Streamlit**, nên nó không gọi rời được.
ĐO 12 **không** đo biểu đồ ấy; nó chỉ đo rằng các tên và từ khoá biểu đồ
ấy dùng vẫn còn sống (ô A và B). Dựng lại biểu đồ ấy trong dụng cụ đo sẽ
là *test kiểm lại chính nó* — lỗi đã mắc ba lần ngày 31/08/2026.

### BẢNG ĐỌC — ký trước, không sửa sau khi thấy số

```
A  mot ten BIEN MAT                        ->  KHONG NANG
B  mot tu khoa bi CHOI THEM                ->  KHONG NANG
C  trade_review dang nap duoc ma NAP NO    ->  KHONG NANG
D1 bam DU LIEU cua trace DOI               ->  KHONG NANG
D2 bam HINH + CHU THICH DOI                ->  KHONG NANG
E  bam phan con lai cua layout DOI         ->  GHI RA, khong tu no quyet dinh
   A B C D1 D2 giong het                   ->  NANG DUOC, neu 5 cong xanh
   khong dung duoc figure o mot luot nao    ->  CHUA KET LUAN DUOC, khong nang
```

**Ba ô, không phải hai** — cùng quy ước với ĐO 10 và ĐO 11.

**Ô `KHÔNG NÂNG` ở đây có xác suất thật sự xảy ra**, khác hai phép nâng
trước. Nếu nó xảy ra thì **đừng nâng**, và việc phải làm là **ghim
`plotly<7` trong `requirements.txt`** — vì khi ấy bản đang phục vụ người
dùng là bản vẽ sai, và im lặng để nguyên nghĩa là để nó tiếp tục sai.
Khai điều này TRƯỚC, cùng lý do đã khai ở ĐO 11.

---

## Kết quả ĐO 12 — chạy 17/09/2026, đọc theo bảng đã ký

**Dụng cụ đọc:** `tools/do12_nang_plotly.py`

Tiêu chí vào nhánh lúc **14:18:50** (commit `dd422b2`), lượt chụp `truoc`
cùng giây đó, và **trước khi đổi một gói nào**.

| | 6.9.0 | 7.1.0 | |
|---|---|---|---|
| **A** 5 tên (`Figure` `Candlestick` `Scatter` `Bar` `make_subplots`) | 5 có · 0 thiếu | 5 có · 0 thiếu | |
| **B** 28 cặp (tên, từ khoá) | 28 nhận · 0 chối | 28 nhận · 0 chối | |
| **C** `trade_review` nạp | 1/1 | 1/1 | |
| **D1** dữ liệu 3 trace | `a92d5f6b…` | `a92d5f6b…` | **giống hệt** |
| **D2** 4 hình · 3 chú thích | `24b3bd2f…` | `24b3bd2f…` | **giống hệt** |
| **E** phần còn lại của layout | `cf068641…` | `edc5d910…` | **ĐỔI** — không chặn |

```
PHAN QUYET: NANG DUOC
```

Phép nâng chạm **đúng một gói**: `pip freeze` trước/sau khác một dòng.

### Ô E đổi CÁI GÌ — đào tới từng lá

Khoá đổi duy nhất là `template`. Đào xuống lá:

```
template 6.9.0 : 343 la      7.1.0 : 339 la
chi o 6.9.0    : 4 la        chi o 7.1.0 : 0
cung khoa khac gia tri : 0
```

Bốn lá mất, và cả bốn cùng một chỗ:

```
data.scattermapbox[0].marker.colorbar.outlinewidth
data.scattermapbox[0].marker.colorbar.ticks
data.scattermapbox[0].type
layout.mapbox.style
```

`plotly` 7 gỡ họ `mapbox`. Dự án **không dùng biểu đồ bản đồ** — bề mặt
đếm bằng AST chỉ có `Figure` · `Candlestick` · `Scatter` · `Bar` ·
`make_subplots`.

Và **mọi khoá dự án TỰ ĐẶT đều giống hệt**, đọc từng cái:

```
plot_bgcolor  paper_bgcolor  height  margin  xaxis  legend  hovermode
-> GIONG ca bay
```

### Dụng cụ phải sửa giữa chừng, và bảng đọc thì KHÔNG

Lượt so đầu tiên in ra đúng một dòng: *"E đổi"*. Ảnh chụp chỉ giữ **băm**,
nên nó nói được **rằng** có đổi mà không nói được **đổi cái gì** — đúng
hình dạng lỗi 78, lần này bắt được ngay ở lượt dùng đầu tiên.

Dụng cụ nay chụp thêm nội dung và in ra khoá nào đổi. **Bảng đọc không
đổi một chữ** — đây là thêm chi tiết vào bản in, không phải thêm hay bớt
một tiêu chí. Hai lượt chụp đã chạy lại từ đầu ở cả hai bản.

---

## ĐO 13 — `urllib3` 1.26.20 → 2.8.0: dữ liệu về có đổi một ô nào không? (khai 18/09/2026)

**Dụng cụ đọc:** `tools/do13_nang_urllib3.py` — chạy hai lượt, `truoc`
(trước khi nâng) rồi `sau` (sau khi nâng).

**Đã tra trùng:** **BƯỚC 105** (18/09/2026) là chỗ vế lệch này được gọi
tên, và nó ghi thẳng *"chưa ai đo"*. Bảy chỗ khác trong `CLAUDE.md`,
`docs/HANDOFF.md` và `docs/STATE.md` đều chỉ **nhắc** khoảng cách ấy, không
chỗ nào đo. ĐO 10 có kéo OHLCV nhưng đo `vnstock`, không đo tầng HTTP dưới
nó — nên dụng cụ ĐO 13 **dùng lại** `do10_nang_vnstock._bam_bang()` thay
vì viết một phép băm thứ hai.

### CHIỀU CỦA PHÉP NÂNG NÀY NGƯỢC VỚI BA PHÉP TRƯỚC — đọc kỹ chỗ này

ĐO 10 · 11 · 12 đều là *"máy này đang tụt lại, đuổi theo bản CI đã chạy"*.
ĐO 13 cũng vậy về hình thức, nhưng hệ quả của ô `KHÔNG NÂNG` thì khác hẳn:

```
requirements.txt KHONG ghim urllib3 (no la phu thuoc gian tiep cua requests)
  -> CI          cai ban moi nhat  =  2.8.0
  -> Streamlit Cloud cung duong ay =  2.8.0
  -> may local                     =  1.26.20   <- ke duy nhat o 1.x
```

**Người dùng đang chạy trên 2.x rồi.** Nên nếu dữ liệu ĐỔI, kết luận
không phải *"đừng nâng máy local"* — nó là **mọi con số đo ở máy này đều
đo trên một tầng HTTP khác tầng đang phục vụ**, và việc phải làm là ghim
`urllib3<2` trong `requirements.txt` để kéo **sản xuất** về đúng bản đã đo.
Đó là một hành động nặng hơn ĐO 12, và nó được khai ở đây TRƯỚC khi thấy
số.

### Bề mặt, ĐO chứ không đoán

```
requests 2.34.2   khai `urllib3<3,>=1.26`   -> CA HAI ban nam trong dai
repo goi requests: DUNG HAI cho
    vnstock_goi.py     requests.get (params, timeout)
    chatbot_agent.py   requests.post (headers, json, timeout)
duong DU LIEU that:
    vnstock/core/utils/client.py::send_request  -> requests.get / requests.post
vnstock/vnai dung API urllib3 truc tiep:  KHONG
    (`block_detect.py` co nhac ten, nhung trong DOCSTRING, va co y KHONG
     dung ham cua urllib3)
```

Nên urllib3 **có** trên đường dữ liệu: mọi dòng OHLCV dự án chấm đều đi
qua `requests` → urllib3. Nhưng bề mặt repo chạm tới nó thì **rất mỏng** —
không `Retry`, không `HTTPAdapter`, không `verify=False`, không `proxies`.

### ĐỐI CHỨNG quyết định ô D có ĐỌC ĐƯỢC hay không

Đây là chỗ khác ĐO 12 về bản chất: ĐO 12 so hai `go.Figure` dựng từ một
bảng giá **sinh bằng công thức đóng**, nên hai lượt chắc chắn cùng đầu
vào. ĐO 13 phải **gọi mạng**, và một endpoint có thể trả khác nhau vì lý
do chẳng liên quan gì tới urllib3 — dự án đã gặp đúng chuyện ấy một lần
(HT1 · TCH, một lượt kéo hỏng tạm thời).

Nên **D0 chạy TRƯỚC D1, trên CÙNG MỘT bản urllib3**: kéo hai lượt cùng
khoảng, cùng mã. Hai lượt ấy khác nhau thì endpoint không tất định, và khi
đó D1 **không nói được gì về urllib3** — nó nói về endpoint. Bỏ D0 đi thì
một khác biệt ngẫu nhiên sẽ bị đọc thành một phán quyết về thư viện.

### Năm đại lượng

| | đại lượng | quyền phán |
|---|---|---|
| **A** | `import requests` trong tiến trình riêng, và `urllib3.__version__` nó thật sự nạp | **CÓ** |
| **B** | hai cặp (hàm, từ khoá) repo gọi, so với `inspect.signature` của `requests` | **CÓ** |
| **C** | `vnstock…client.send_request` — chữ ký còn nhận đúng tham số cũ | **CÓ** |
| **D0** | *đối chứng*: hai lượt kéo CÙNG bản, cùng khoảng đã đóng | quyết định D1 có đọc được |
| **D1** | băm CSV của OHLCV một khoảng **đã đóng**, so hai bản urllib3 | **CÓ**, nếu D0 đạt |
| **E** | thời gian mỗi lượt kéo | **KHÔNG** — ghi ra để đọc |

**E không có quyền phán**, và lý do đáng nói: urllib3 2.x đổi cách gộp kết
nối, nên thời gian gần như chắc chắn khác. Cho nó quyền phán là tự định
sẵn `KHÔNG NÂNG` — đúng cái bẫy ĐO 12 đã gọi tên ở ô E của nó.

### BẢNG ĐỌC — ký trước, không sửa sau khi thấy số

```
A  import NO o mot ban                     ->  KHONG NANG
B  mot tu khoa bi CHOI                     ->  KHONG NANG
C  send_request DOI chu ky                 ->  KHONG NANG
D0 hai luot CUNG BAN khac nhau             ->  CHUA KET LUAN DUOC, khong nang
D1 bam DU LIEU doi (khi D0 dat)            ->  KHONG NANG, va ghim urllib3<2
E  thoi gian doi                           ->  GHI RA, khong tu no quyet dinh
   A B C D1 giong het va D0 dat            ->  NANG DUOC, neu 5 cong xanh
   khong goi duoc mang o mot luot nao      ->  CHUA KET LUAN DUOC, khong nang
```

**Ba ô, không phải hai** — cùng quy ước ĐO 10 · 11 · 12.

### GIỚI HẠN NÊU TRƯỚC — và ở phép đo này chúng LỚN

Nói ra đây thay vì để người đọc tự suy, vì một lượt xanh rất dễ bị đọc
rộng hơn thứ nó giao:

1. **Phép đo chạm ĐÚNG MỘT endpoint, MỘT khoảng, trên một đường mạng
   lành.** Nó **không** đo: TLS/SSL, chứng chỉ, `Retry`, chuyển hướng,
   proxy, gộp kết nối khi tải nặng, hay hành vi lúc endpoint trả lỗi.
2. **Và đó đúng là vùng urllib3 2.x đổi nhiều nhất.** Tức ĐO 13 đo phần
   dự án **dùng**, không đo phần thư viện **đổi**. Một lượt xanh nói
   *"đường dữ liệu bình thường cho cùng byte"*, nó **không** nói
   *"2.x an toàn"*.
3. **Cổng CI đã chạy 2.8.0 nhiều ngày và đều xanh — điều đó nói ít hơn
   vẻ ngoài.** Gần như mọi phép kiểm của dự án chạy **offline**; chúng
   chứng minh đường *nạp* sống, không chứng minh đường *dữ liệu*.
4. **Đường POST của `chatbot_agent.py` KHÔNG được đo** — nó cần khoá
   Gemini, và khoá không đi qua tay agent. Ô B vẫn kiểm chữ ký của lời
   gọi ấy, nhưng không ai gọi nó thật trong phép đo này.
5. **`pyarrow` 24 → 25 không nằm trong ĐO này.** Nó là vế lệch bản CHÍNH
   thứ hai và cần một bảng riêng; gộp hai phép nâng vào một lượt là đúng
   cái lỗi `--stride 1` đã bị cấm ngày 09/09.

---

## Kết quả ĐO 13 — chạy 18/09/2026, đọc theo bảng đã ký

**Dụng cụ đọc:** `tools/do13_nang_urllib3.py`

Tiêu chí vào nhánh lúc **10:45:00** (commit `2eb86f2`), lượt chụp `truoc`
lúc **10:45:06** — sáu giây sau, và **trước khi đổi một gói nào**.

| | 1.26.20 | 2.8.0 | |
|---|---|---|---|
| **A** `import requests` trong tiến trình riêng | nạp · requests 2.34.2 | nạp · requests 2.34.2 | |
| **B** 2 hàm · 5 từ khoá | 5 nhận · **0 chối** | 5 nhận · **0 chối** | |
| **C** `send_request` | 7 tham số | 7 tham số | |
| **D0** đối chứng hai lượt cùng bản | **đạt** | **đạt** | |
| **D1** VCB · FPT · HPG, 65 dòng mỗi mã | `dd46716e94e6d682` · `43ea00780eb70566` · `7e6455b6fbd23535` | **giống hệt cả ba** | ✅ |
| **E** giây mỗi lượt kéo | 4,22 / 0,79 | 2,83 / 0,81 | ghi ra |

**PHÁN QUYẾT: `NÂNG ĐƯỢC`** — A, B, C, D1 giống hệt; D0 đạt ở cả hai chân.

### D0 là thứ làm D1 đọc được

Không có nó, ba băm giống nhau cũng chỉ là ba băm giống nhau — không ai
biết endpoint có tất định hay không. D0 chạy **trước** mọi phép so chéo
bản, và nó đạt ở **cả hai** chân, nên phép so quy được về một vế: bản
urllib3.

### E không có quyền phán, và số liệu cho thấy vì sao

Lượt kéo đầu 4,22s → 2,83s, lượt thứ hai 0,79s → 0,81s. Chênh lệch giữa
lượt một và lượt hai **trong cùng một chân** (4,22 so với 0,79) lớn hơn
hẳn chênh lệch giữa hai chân — tức đại lượng này bị chi phối bởi thứ
khác (gộp kết nối, cache tầng dưới), không bởi bản thư viện. Cho nó quyền
phán là tự định sẵn `KHÔNG NÂNG`.

### Một dòng `ERROR` trong lượt cài — đọc, không lướt

```
pyppeteer 2.0.0 requires urllib3<2.0.0, but you have urllib3 2.8.0
```

**Bất động, ba đường xác nhận độc lập:**

```
1. pyppeteer KHONG TON TAI tren CI      (92 goi, khong co no)
2. repo khong nhap pyppeteer            (cot suy ra cua so_ban_goi.py)
3. CI chay DUNG to hop nay va van xanh  (urllib3 2.8.0 + requests 2.34.2)
```

Cùng hình dạng xung đột `websockets` đã đọc ngày 17/09, thêm một vế mới:
vế **CI vắng mặt**. `pyppeteer` tới từ `requests-html`, và cả hai nằm
trong nhóm **39 gói chỉ có ở máy này**.

### Vế đã khai trước mà KHÔNG xảy ra, ghi ra để lần sau khỏi lo

Bảng ký trước nói: nếu D1 đổi thì phải ghim `urllib3<2` trong
`requirements.txt` để kéo **sản xuất** về bản đã đo. Nhánh ấy **không
được dùng** — D1 giống hệt, nên `requirements.txt` giữ nguyên, và
`urllib3` vẫn là phụ thuộc gián tiếp không ghim.

---

## ĐO 14 — dữ liệu khối ngoại có BACKTEST được không? (khai 22/09/2026)

**Dụng cụ đọc:** `tools/do14_kha_thi_khoi_ngoai.py`

**Đã tra trùng:** **BƯỚC 53** (11/09/2026) — lần **duy nhất** dự án kéo một
nguồn ĐỘC LẬP về rồi đo IC. Kết quả ở đó: không chỉ số nào phân biệt được
với 0 trên 2.099 quan sát, và `leverage` — chỉ số duy nhất từng có tín hiệu
thô — **mất** nó khi cỡ mẫu tăng. Hai chỗ khác trong `docs/STATE.md` chỉ
**nhắc tên** API khối ngoại, không chỗ nào kéo một dòng: dòng 1672 và dòng
1856, cả hai thuộc mục ngày 22/08/2026 và cả hai đọc từ tài liệu nhà cung
cấp. Chữ *"khối ngoại"* xuất hiện **0 lần** trong `docs/STATE.md`.

### Hai tên trong cùng một tài liệu, và chỉ MỘT tên có thật

Dò trước khi ký, không kéo một ô dữ liệu nào:

```
docs/STATE.md:1672   Market().equity(sym).foreign_flow(start, end)   -> CO THAT
docs/STATE.md:1856   insights.flow.foreign()                         -> vnstock_data.insights KHONG TON TAI
```

Tên thứ hai viết trần ở đây **có chủ ý** — nó là một cái tên đã chết, và
quy ước của dự án cấm viết nó trong dấu nháy ngược vì máy quét không phân
biệt được *nhắc lại* với *trỏ tới*.

Phép dò ấy là lý do bảng dưới đây không phải diễn kịch — đúng bài học của
ô `pyarrow` trong `docs/HANDOFF.md` mục 5: **một bảng tiêu chí chỉ gồm ô
không-đọc-được là diễn kịch.** Ở đây API có thật, và docstring của nó tự
khai *"Historical or daily foreign buy/sell volume and value"*.

### ĐO GÌ — và nói trước cái KHÔNG đo

Đây là phép đo **TÍNH KHẢ THI**, không phải phép đo **TÍN HIỆU**. Mọi ô
ĐẠT ở dưới đều **không** nói gì về việc khối ngoại có dự báo được lợi
nhuận hay không. Viết ra đây trước, vì chiều đọc rộng hơn phạm vi là chiều
đã cắn dự án này ở lỗi 73 · 80 · 88 · 90.

### Ba ô, ngưỡng ký TRƯỚC khi thấy số

| ô | câu hỏi | ĐẠT | KHÔNG ĐẠT |
|---|---|---|---|
| **A · ĐỘ SÂU** | chuỗi lùi được tới đâu (xin từ 2015-01-01, mã FPT) | ngày sớm nhất **≤ 2021-10-01** | > 2021-10-01 |
| **B · ĐỘ PHỦ** | bao nhiêu mã của rổ chuẩn 71 mã có dữ liệu | **≥ 60/71** | < 60/71, và **< 36/71** là hỏng hẳn |
| **C · ĐỌC ĐƯỢC** | bảng có cột ngày và cột ròng không | có cả hai, suy được đơn vị | thiếu một trong hai |

Vì sao mốc ô A là **2021-10-01**: đó là chỗ cache giá mặc định bắt đầu.
Chuỗi khối ngoại không phủ được vùng ấy thì không ghép được vào
walk-forward hiện hành. Mốc **2018-09-13** (cache rộng của ĐO 4) là mức
ĐẠT MẠNH, không phải điều kiện.

### Bốn kết cục, và cách đọc từng cái

```
KET CUC 1   A dat  +  B dat     ->  dung duoc. Buoc sau la mot phep do IC
                                    thiet ke theo dung khuon BUOC 53.
KET CUC 2   A dat  +  B khong   ->  chi dung duoc cho mot nhom ma. KHONG
                                    dung duoc lam agent cho ca ro.
KET CUC 3   A khong             ->  KHONG backtest duoc. Khi ay khoi ngoai
                                    roi vao dung o cua TradingView va tin
                                    tuc: "phan co the co tin hieu thi khong
                                    do duoc" — va cau ay thanh mot cau DA DO.
KET CUC 4   API no / bi khoa    ->  CHUA KIEM DUOC. Ma thoat 2.
```

**Kết cục 4 KHÔNG được đọc thành kết cục 3.** Gói `vnstock_pipeline` đã
từng bị khoá ở hạng silver trong khi `license/verify` vẫn liệt kê nó — một
lần khoá hạng trông y hệt một nguồn không có dữ liệu, nếu không phân biệt.

### ĐỐI CHỨNG DƯƠNG — điều kiện để một kết quả ÂM đọc được

Một chuỗi NGẮN có hai cách giải thích ngược nhau: *nguồn chỉ phục vụ từng
ấy ngày*, hoặc *tham số ngày của tôi bị bỏ qua*. Không tách được thì con số
nói về **dụng cụ**, không nói về **nguồn** — đúng lỗi 66.

Nên mỗi lượt chạy kéo thêm `ohlcv` qua **đúng cùng một đối tượng, đúng cùng
khoảng ngày, đúng cùng tên tham số vừa dùng được**. OHLCV là ca đã biết
trước là dương.

```
ohlcv DAI  +  foreign_flow NGAN   ->  noi ve NGUON, doc duoc
ohlcv NGAN +  foreign_flow NGAN   ->  CHUA KIEM DUOC, ma thoat 2
```

### Ô D — point-in-time, CHƯA kiểm được trong một phiên

Một chuỗi bị sửa lại về sau (restate) trông **y hệt** một chuỗi không bị
sửa, nếu chỉ đọc một lần. Đây là vế nguy hiểm nhất: bảng chỉ số theo năm
của `fundamental_agent` hỏng đúng kiểu ấy, và `CLAUDE.md` gọi rào chắn
chống nhìn trộm ở đó là *"không phải công tắc hiệu năng"*.

Nên lượt hôm nay chỉ **CHỤP**: băm SHA-256 cửa sổ cố định `2025-01-02` →
`2025-06-30` của FPT, lưu CSV. Phép so nằm ở mốc ngày dưới đây.

**Mốc đọc: 29/09/2026.** Kéo lại đúng cửa sổ ấy, so băm.

```
bam GIONG HET   ->  cua so nay KHONG bi sua lai trong 7 ngay. Chua chung
                    minh duoc "khong bao gio sua", chi thu hep duoc.
bam KHAC        ->  chuoi CO bi sua lai. Moi phep do dung no phai chup
                    du lieu tai thoi diem, khong duoc keo lai ve sau.
```

Điều kiện đọc: chỉ đọc vào hoặc sau 29/09/2026, không đọc sớm.

### Ba điều bắt buộc của lượt chạy

1. **In dữ liệu thô ngay dưới con số** (lỗi 61) — năm dòng đầu của bảng,
   nguyên văn, kèm tên cột.
2. **Chạy hai lượt, phải ra cùng số** (bất biến 2).
3. **Quy tắc số 1 áp dụng ngược ở đây.** Ô ĐẠT là chiều dễ chịu — nó mở ra
   một hướng làm việc mới. Nên một ô ĐẠT phải kiểm bằng mắt trên dữ liệu
   thô, không tin con số tổng.

---

## ĐO 15 — khối ngoại có DỰ BÁO được lợi nhuận không? (khai 22/09/2026)

**Dụng cụ đọc:** `experiment_khoi_ngoai.py` · dữ liệu:
`fetch_khoi_ngoai.py`

**Đã tra trùng:** **BƯỚC 53** (11/09/2026) — cùng câu hỏi, khác nguồn: IC
của năm chỉ số BCTC, 2.099 quan sát, 0/5 qua Bonferroni. **BƯỚC 7**
(31/08/2026) — cùng *quần thể* và cùng *bộ máy*: 69 mã, 63.389 phiên, cách
gộp tuyến tính tối ưu trong mẫu cho rho **0,0115** ở h=5, dưới sàn nhiễu
**0,0446**. **BƯỚC 9** (01/09/2026) — đối chiếu sàn nhiễu bằng đường thứ
hai. **BƯỚC 112** (22/09/2026) — ĐO 14, nguồn dữ liệu này dùng được.
Chưa BƯỚC nào đo IC của khối ngoại.

### KHÔNG VIẾT LẠI BỘ MÁY — nhập lại nó

`experiment_tran_dac_trung.py` đã có đủ, và cả năm thứ đều là thứ đắt để
dựng lại: nhãn **vượt rổ** (bất biến 6), sàn nhiễu **hoán vị dịch vòng
theo mã** (đã đối chiếu bằng đường thứ hai ở năm nhịp), **chứng cứ dương**
tiêm tín hiệu biết trước, **rào hoà vốn** suy từ `ROUND_TRIP_COST_PCT`, và
`MIN_HIST = 250`. ĐO 15 chỉ thay **tập đặc trưng**.

Hai lần trong ba ngày (05/09 và 07/09) lời giải nằm sẵn trong repo và vẫn
bị viết lại từ đầu — lỗi 41. Mục này khai trước rằng nó sẽ không lặp.

### CÁI NÀY ĐO MỘT CẬN TRÊN, KHÔNG ĐO MỘT CHIẾN LƯỢC

Cửa sổ dùng được là **2021-10-14 → 2026-09-03**, và theo **bất biến 8**
đó là vùng **đã bị nhìn nhiều nhất**. Nên phép đo này mượn đúng khuôn
BƯỚC 7: đo **trong mẫu**, cố ý, và đọc kết quả như một **cận trên**.

```
IC trong mau DUOI san nhieu  ->  cau hoi DONG LAI, va dong ma KHONG
                                 tieu mot phien sach nao
IC trong mau TREN san nhieu  ->  CHUA la tin hieu. No chi noi rang mot
                                 phep do ngoai mau tren du lieu sach la
                                 dang lam.
```

Vế thứ hai phải khai ở đây, trước khi thấy số: **một ô vượt sàn nhiễu
KHÔNG cho phép bật bất cứ thứ gì.**

### NĂM ĐẶC TRƯNG, KHAI TRƯỚC — thêm bớt sau khi thấy số là bất biến 7

Tất cả đều **không thứ nguyên** và chỉ dùng dữ liệu tới hết phiên T:

```
kn_ty_trong_5    sum(net_vol,5)  / sum(volume,5)
kn_ty_trong_20   sum(net_vol,20) / sum(volume,20)
kn_ap_luc_5      (sum(buy_val,5)-sum(sell_val,5)) / (sum(buy_val,5)+sum(sell_val,5))
kn_z_20          sum(net_val,20) chuan hoa trong-ma bang trung binh/do lech 250 phien
kn_cuong_do_20   (sum(buy_val,20)+sum(sell_val,20)) / sum(close*volume,20)
```

`kn_cuong_do_20` **không có hướng** — nó đo mức tham gia, không đo mua hay
bán. Giữ nó vì một đại lượng không hướng mà có IC khác 0 là dấu hiệu rò rỉ
chứ không phải tín hiệu, tức nó làm việc của một ô đối chứng.

**KHÔNG có đặc trưng nào ĐẾM THEO THỜI GIAN** — không *"bao nhiêu phiên kể
từ lần mua ròng gần nhất"*. Lý do đo được hôm nay (BƯỚC 112): tỷ lệ phiên
`net_val == 0` đi từ 16,5% (2015) xuống **đúng 0,0%** ở 2025–2026, nên mọi
đặc trưng đếm sẽ trôi theo **cấu tạo dữ liệu**, và xu thế ấy trùng hướng
với thời gian.

**Năm đặc trưng ⇒ Bonferroni α = 0,05/5 = 0,01**, đúng như BƯỚC 53.

### HAI NHỊP, VÀ CHÚNG KHÔNG ĐỌC GIỐNG NHAU

`h = 5` và `h = 21`, cả hai nằm trong `NHIP_DA_DOI_CHIEU`. Nhưng theo
BƯỚC 7, chỉ **h=5** có chứng cứ dương: ở h=20 phép đo không bắt được cả
tín hiệu tiêm ở mức rào hoà vốn.

```
chung cu duong KEU o h    ->  ket qua null o h la BANG CHUNG VANG MAT
chung cu duong IM o h     ->  ket qua null o h chi la THIEU LUC
```

Chứng cứ dương **phải chạy trong chính lượt này**, không chép kết quả
31/08 sang — tập đặc trưng khác thì lực khác.

### BỐN KẾT CỤC

```
KET CUC 1  >=1 dac trung vuot san nhieu (sau Bonferroni) VA vuot rao hoa
           von  ->  dang mot phep do NGOAI MAU tren du lieu sach
KET CUC 2  vuot san nhieu, DUOI rao hoa von  ->  phan biet duoc voi 0,
           vo dung ve kinh te. Ghi lai, khong lam gi tiep
KET CUC 3  khong dac trung nao vuot san nhieu, VA chung cu duong KEU
           ->  BANG CHUNG VANG MAT o nhip ay. Cau hoi dong lai
KET CUC 4  chung cu duong IM  ->  THIEU LUC, khong doc duoc. Khong duoc
           bao cao chung mot cau voi ket cuc 3
```

### BA ĐIỀU BẮT BUỘC CỦA LƯỢT CHẠY

1. **Đếm biến thiên SAU khi ghép**, không trên chuỗi thô (BƯỚC 112). Một
   chuỗi giàu trên lịch có thể sụp thành vài giá trị ở đúng tập quan sát
   được dùng — `sl_pattern_memory.json` trông 6.327 mẫu mà chỉ có 2 bộ ba.
2. **In độ phủ ghép**: bao nhiêu phiên có giá mà thiếu khối ngoại. ĐO 14
   đo FPT được 0; cả rổ thì chưa ai đo.
3. **Quy tắc số 1.** Một IC vượt sàn nhiễu là chiều dễ chịu. Trước khi tin,
   kiểm `kn_cuong_do_20` — ô không hướng. Nếu nó cũng vượt thì thứ đo được
   nhiều khả năng là một dạng rò rỉ, không phải hướng của dòng tiền.

## ĐO 16 — nhịp 21 phiên: tín hiệu khối ngoại của ĐO 15 có LẶP LẠI ngoài mẫu? (khai 24/09/2026)

**Dụng cụ đọc:** `experiment_khoi_ngoai_nhip_dai.py` · dữ liệu:
`backtest/cache_2018/`, `backtest/cache/` và `backtest/cache_khoi_ngoai/`
— **không chạm mạng**.

**Đã tra trùng:** **BƯỚC 113** (22/09/2026) — ĐO 15, cùng năm đặc trưng,
cùng bộ máy; h=21 ra kết cục 4. **BƯỚC 7** (31/08/2026) — nơi hình dạng
*một lượt tiêm* sinh ra. **BƯỚC 9** (01/09/2026) — sàn nhiễu đã đối chiếu ở
h=21, và tiền lệ hai chặng. **BƯỚC 13** (02/09/2026) — tiền lệ *"hai phía,
cố ý, dù giả thuyết có hướng"*. **BƯỚC 55** (12/09/2026) — `cache_2018/`
(kéo 11/09) khớp `cache/` trung vị 0 ở 32/33 mã. **BƯỚC 53** (11/09/2026)
— 2/71 mã của `cache_2018/` lấy từ nguồn khác. Chưa BƯỚC nào đo khối ngoại
trên `cache_2018/`.

### MỘT CÂU HỎI

ĐO 15 đo **trong mẫu** và thấy ở h=21 `kn_z_20` cho IC **+0,0557**, cao hơn
rào hoà vốn 0,0488. **Dự báo ấy — giữ nguyên, không khớp lại — có đứng được
trên dữ liệu mà năm đặc trưng khối ngoại chưa từng nhìn không?**

### HAI TẬP, TÁCH THEO KHOÁ `(mã, ngày)`

```
tap HUAN LUYEN   bang DO 15, backtest/cache/                     da nhin
tap KIEM         bang cache_2018 TRU bang DO 15, theo khoa       chua nhin
```

Tách theo **khoá**, không theo một mốc ngày: bảng ĐO 15 bắt đầu ở mỗi mã
một ngày khác, nên một mốc chung sẽ hoặc bỏ sót phiên chưa nhìn, hoặc lẫn
phiên đã nhìn. Mã có dưới **60** quan sát trong tập kiểm thì bỏ — mã quá
ngắn thì sàn nhiễu để nguyên không dịch, và phép tiêm không dịch được nền.

```bash
./.venv/Scripts/python.exe experiment_khoi_ngoai_nhip_dai.py --do-luc
```

```
bang DO 15   60.261 quan sat
bang gop    112.058
chua nhin    51.797
TAP KIEM     51.771   67 ma   2019-10-10 -> 2026-08-06
             bo BAF (26 quan sat kiem)
             truoc 2021-10-14: 32.007 · sau: 19.764
```

Phần **sau** mốc 2021-10-14 là những phiên nằm ngoài bảng ĐO 15 dù ở trong
khoảng lịch của nó. Vùng lịch ấy **đã bị các vòng tối ưu giá nhìn** (bất
biến 8), nhưng những quan sát này **chưa bao giờ** được dùng để đo khối
ngoại, và năm đặc trưng này chưa từng tồn tại lúc các vòng ấy chạy.

**Không chạm mạng.** Kéo lại khối ngoại trước 29/09/2026 là đọc sớm phép
kiểm point-in-time đã hẹn (`docs/HANDOFF.md` mục 5).

### DỰ BÁO VÀ PHÉP KIỂM, KHAI TRƯỚC

- **Dự báo:** `kn_z_20`, **dấu + đã khai**, lấy từ ĐO 15. Không tham số nào
  được chọn trên tập kiểm.
- **Thống kê:** IC hạng của `kn_z_20` với nhãn vượt rổ 21 phiên, trên tập
  kiểm.
- **Sàn nhiễu:** hoán vị dịch vòng trong từng mã (`E.san_nhieu`), **2.000**
  vòng, hạt giống **20260924**.
- **Rào:** `E.rao_hoa_von()` trên nhãn của **tập kiểm** — **0,0376**, không
  mượn 0,0488 của ĐO 15.
- **HAI PHÍA, α = 0,05.** Một IC có ý nghĩa mà **ngược** dấu đã khai là
  *không lặp lại*.
- **Số phụ, KHÔNG vào phán quyết:** IC của bốn đặc trưng còn lại; cách gộp
  tuyến tính **khớp trên tập huấn luyện** rồi áp nguyên lên tập kiểm.

### HAI PHÍA — và vì sao bản người dùng duyệt là MỘT phía

Bản thiết kế người dùng chọn (phương án B, trong ba phương án) là **một
phía**, kèm dòng *"lực 86% nếu kiểm một phía"*. Lý do lúc ấy: lực **hai**
phía đo bằng một script tạm ra **39/50 = 78%**, dưới chuẩn 80%.

Rồi hai việc xảy ra trước khi ký:

1. **Sổ tay trả *"không tìm thấy câu nào nói ngược"*, và tự kiểm bằng `grep`
   tìm ra BƯỚC 13:** *"Vẫn chọn hai phía vì dữ liệu này đã bị nhìn một lần,
   đúng theo chiều đó. Một phía sau khi đã nhìn là thứ không cãi được với
   người đọc hoài nghi"* — và gác của nó có một phát đục *"đổi sang một phía
   'để đủ lực'"*. Lý do gốc không chuyển sang đây (tập kiểm chưa ai nhìn),
   nhưng vế *"để đủ lực"* thì đúng là việc tôi vừa làm.
2. **Đo lại bằng dụng cụ trong repo, trên tập đã bỏ BAF:** lực **hai phía
   41/50 = 82%**. Con số 78% tính trên tập còn BAF — 26 quan sát, quá ngắn
   để dịch vòng.

Lý do duy nhất để chọn một phía hết, nên **thiết kế đổi về hai phía** —
chiều **chặt hơn** phương án đã duyệt. Một phía chỉ còn là tuỳ chọn
`--mot-phia`, để tái lập con số của bản đầu (42/50).

### CHẶNG 2 KHI CHẶNG 1 CHƯA CHÍNH THỨC ĐẠT — khai thẳng

Tiền lệ BƯỚC 9: *"chặng 2 chỉ chạy nếu ô chính ĐẠT"*. Chặng 1 ở đây là ĐO 15
ở h=21, và nó **chưa đạt** — kết cục 4. ĐO 16 đi lệch tiền lệ ấy **có chủ
đích**, vì một phát hiện của chính lượt chuẩn bị này:

```
lap lai CHINH phep tiem cua DO 15 (hai phia, Bonferroni 0,01), 30 luot
h=21  khong co gi  bat  0/30   dung bang rao  bat 21/30   IC do TB +0,0551
h=5   khong co gi  bat  0/30   dung bang rao  bat 30/30   IC do TB +0,1203
```

```bash
./.venv/Scripts/python.exe experiment_khoi_ngoai_nhip_dai.py --do-luc --cua-so-do15 --r 30 --alpha 0.01 --hat 20260945
./.venv/Scripts/python.exe experiment_khoi_ngoai_nhip_dai.py --do-luc --cua-so-do15 --r 30 --alpha 0.01 --hat 20260929 --nhip 5
```

Kết cục 4 của ĐO 15 dựa trên **MỘT lượt rút**, và ở h=21 một lượt rút là
một đồng xu nghiêng 70/30 (**lỗi 99**). Pha loãng bị bác trong cùng lượt:
IC đo được TB +0,0551, nhỉnh hơn mức tiêm 0,0488. Đo bằng 50 lượt, α =
0,05 hai phía, cửa sổ ĐO 15 bắt **45/50 = 90%**:

```bash
./.venv/Scripts/python.exe experiment_khoi_ngoai_nhip_dai.py --do-luc --cua-so-do15
```

**Kết cục 4 của ĐO 15 KHÔNG bị lật.** Nó đã ký, và dưới luật của chính nó
lực chỉ 70%. Thứ đổi là **lý do để không làm chặng 2**: lý do ấy dựa trên
một phán quyết lực không đứng vững khi đo lại.

### PHÁN QUYẾT "ĐỌC ĐƯỢC": NHIỀU LƯỢT

`dung bang rao` bắt **≥ 80%** trong **50** lượt, **VÀ** `khong co gi` bắt
**≤ ngưỡng nhị thức** (50 lượt, α = 0,05 → ≤ 5, suy bằng `nguong_im()`).
Dưới **30 lượt** thì không được phán đọc được, dù tỷ lệ đẹp đến đâu.

### LỰC, ĐO TRƯỚC KHI KÝ — không tính một IC thật nào

`--do-luc` chỉ dùng tín hiệu **GIẢ** tiêm trên nền đã rời nhãn, và null của
dự báo dựng bằng hoán vị phá liên kết. Cả hai không mang thông tin về tín
hiệu.

```
TAP KIEM · rao 0,0376 (sigma nhan 11,476%) · 50 luot · 400 vong · HAI PHIA
  khong co gi    bat  3/50       nguong im <= 5    -> im
  dung bang rao  bat 41/50 = 82% IC do TB +0,0498  -> DU LUC
  -> DOC DUOC
```

Phép tiêm dùng hạt giống riêng **20260925**, nên lượt chính sẽ ra **đúng
41/50** — nó đo lại, không rút lại. 82% sát chuẩn 80%, và sai số chuẩn của
một tỷ lệ trên 50 lượt là khoảng 5 điểm; ghi ra để không ai đọc nó như một
biên rộng.

### NĂM Ô KẾT CỤC

```
KET CUC 4   khong doc duoc  ->  ket qua KHONG doc duoc du no dep hay xau
KET CUC 3   doc duoc, p >= 0,05  HOAC  co y nghia ma NGUOC dau  ->  KHONG
            LAP LAI. Nhip 21 DONG
KET CUC 2   doc duoc, p < 0,05, dung dau, IC + 1,96 x SD < rao  ->  LAP LAI
            nhung DUOI RAO CHAC. Nhip 21 DONG ve kinh te
KET CUC 2b  doc duoc, p < 0,05, dung dau, rao - 1,96 x SD <= IC <= rao  ->
            LAP LAI, SAT RAO. KHONG dong duoc
KET CUC 1   doc duoc, p < 0,05, dung dau, IC > rao  ->  LAP LAI VA VUOT RAO
            NGOAI MAU
```

`SD` = độ lệch chuẩn null của **chính** dự báo trên tập kiểm.

**Kết cục 2 VÔ NGHIỆM trên tập này, đo trước khi ký:** null của chính
`kn_z_20` (400 vòng, ước lượng) có SD **0,0188**, và sàn hai phía là |IC| >
**0,0354**. Kết cục 2 đòi IC < 0,0376 − 1,96 × 0,0188 = **+0,0007**, trong
khi vượt sàn đòi IC > **+0,0354**. Không IC nào thoả cả hai. Và vì sàn
0,0354 nằm sát rào 0,0376, ô 2b chỉ là một dải hẹp: trên thực tế kết quả
rơi vào **3** (không lặp lại) hoặc **1** (vượt rào). Cùng hình dạng BƯỚC 13
đã ghi: *"điều khoản rào hôm nay là chữ chết"*.

### QUY TẮC 1, KHAI TRƯỚC — cho kết cục 1

Kết cục 1 sẽ là **bằng chứng ngoài mẫu đầu tiên** của dự án cho một tín hiệu
vượt rào — tức đúng chiều dễ chịu. Trước khi viết nó:

- ô không hướng `kn_cuong_do_20` trên tập kiểm phải **không** vượt sàn
  (hai phía, 0,05). Vượt thì thứ đo được nhiều khả năng là rò rỉ;
- **tiền kiểm dụng cụ ĐÃ CHẠY:** `--tai-lap-do15` cho rào **0,0488** ·
  `kn_z_20` **+0,0557** · cận trên **+0,0851** — khớp BƯỚC 113 từng chữ số;
- **kết cục 1 KHÔNG bật gì.** IC vượt rào chưa phải một chiến lược: bước kế
  tiếp là một phép đo walk-forward với giữ lệnh 21 phiên, có tiêu chí ký
  riêng.

### GIÁ PHẢI TRẢ

Sau ĐO 16, **không còn quan sát nào trên máy chưa bị nhìn** với năm đặc
trưng khối ngoại ở h=21. Người dùng chọn điều đó (phương án B) giữa ba
phương án, khi đã được báo đoạn này chỉ tiêu được một lần.

### MỖI KẾT CỤC DẪN TỚI ĐÂU

**Không kết cục nào bật gì trong đường sinh lệnh.** Kết cục 3 hoặc 2 ghi vào
`docs/HANDOFF.md` mục 2 như câu trả lời cho *"giữ lâu hơn có cứu được
không"*: **không**, với năm đặc trưng này. Kết cục 2b: câu hỏi còn mở và
không còn dữ liệu sạch trên máy. Kết cục 1: câu hỏi chuyển thành một phép
đo chiến lược.
