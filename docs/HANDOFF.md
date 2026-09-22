# HANDOFF — bắt đầu từ đâu

**Viết lại 05/09/2026.** Bản trước ghi ngày 19/08 và **mọi khẳng định sự
kiện trong nó đã sai** — xem mục 6.

Ba tài liệu, ba vai:

| File | Là gì | Đổi nhiều không |
|---|---|---|
| `docs/HANDOFF.md` (file này) | *bắt đầu từ đâu* — đọc hết trong 5 phút | phải cập nhật mỗi khi trạng thái đổi |
| `docs/STATE.md` | *nhật ký từng bước* — đo được gì, cái gì chưa kiểm được | chỉ THÊM, không sửa mục cũ |
| `CLAUDE.md` | *kiến trúc và luật chơi* | ít đổi nhất |

Hai file mâu thuẫn thì file mới hơn đúng: `HANDOFF` → `STATE` → `CLAUDE.md`.

> ⚠️ **Chính quy tắc ưu tiên đó là lý do file này nguy hiểm khi cũ.** Nó
> đứng đầu thứ tự, nên một câu lạc hậu ở đây đè lên hai file kia. Bản
> 19/08 sống 16 ngày và bảo người đọc *"nếu số test khác 218 thì dừng
> lại"* — trong khi bộ test đã đi từ 218 lên hơn 800.
>
> **Nguyên tắc cho bản này: KHÔNG ghim con số sẽ đổi.** Ghi *cách lấy*
> con số, đừng ghi con số. Chỗ nào buộc phải có số thì đó là **quyết
> định**, không phải phép đo — và quyết định thì hiếm khi đổi.

---

## 1. NĂM LỆNH ĐẦU TIÊN

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q
# So với lượt chạy gần nhất trên main, ĐỪNG so với một con số ghi sẵn.
# Đỏ ở đâu thì dừng ở đó. Bộ test này lớn dần mỗi ngày.

./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py
# CHẠY SAU pytest, không song song. Máy dùng 3.13, CI dùng 3.11 --
# cú pháp 3.12 nạp được ở máy rồi làm CI đỏ ngay bước đầu.

./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo
# Kỳ vọng: 0 CHẶN. Số cảnh báo thì đổi, không phải tiêu chí.

./.venv/Scripts/python.exe tools/kiem_test_chay_rieng.py
# MỌI file test phải xanh khi chạy MỘT MÌNH. ~200s, tuần tự (song song
# cho đỏ giả). Mã thoát 2 = CHƯA KIỂM ĐƯỢC, không phải sạch.
# CI cũng chạy; chạy tay khi vừa sửa hoặc thêm test.

./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py
# Cổng THỨ NĂM, thêm 10/09/2026. Bốn cổng trên đo thứ ĐANG CÓ; cổng này
# là cổng đầu tiên đo thứ BỊ MẤT. Nó không cấm giảm, nó buộc khai lý do:
# `--cap-nhat --ly-do "<vì sao>"`. THÊM test cũng phải cập nhật mốc.
```

> 🔴 **Mục này ghi *"BỐN LỆNH"* và bốn dòng `python …` cho tới
> 14/09/2026.** Cả hai đều sai, và cái thứ hai sai theo kiểu buồn cười
> nhất: luật `python-he-thong` của `tools/cua_bash_an_toan.py` **khai
> nguồn của nó chính là mục này**, rồi mục này vi phạm nó ba lần. Nay có
> `tools/soat_lenh_tai_lieu.py` chạy chính `kiem()` của cửa Bash lên mọi
> khối lệnh trong tài liệu. `docs/STATE.md` BƯỚC 62.

**Trước khi sửa bất cứ thứ gì liên quan tới KẾT QUẢ, đọc hai file:**
`NGUYEN-TAC-DO-LUONG.md` (8 bất biến) và `MO-XE-KIEN-TRUC.md`.

> 🔴 **CẢ KHỐI CẢNH BÁO CŨ Ở ĐÂY ĐÃ BỊ BÁC — đo lại 10/09/2026, và
> nó vẫn nằm đây tới 14/09.** Bản 08/09 viết *"cửa chưa chạy lần nào"*
> và dạy một phép thử: *"chạy `python --version`; in ra số hiệu Python
> thì cửa chết"*.
>
> **Hai vế, hai cái sai khác nhau.** Cửa nay đăng ký ở
> `~/.claude/settings.json` bằng đường dẫn tuyệt đối nên **chạy bất kể
> phiên mở ở đâu** — sáu trên sáu. Còn phép thử kia đi qua **đúng MỘT**
> hook (`cua_bash_an_toan`, matcher `Bash`); nó không nói được gì về
> năm cửa `Read/Write/Edit` và `Stop`. Đó là **lỗi 25** — một phép thử
> đo một cửa bị đọc thành phán quyết về sáu.
>
> **Đọc trạng thái, đừng suy ra nó:**
>
> ```bash
> ./.venv/Scripts/python.exe tools/kiem_cua_song.py
> ```
>
> Mã thoát 0 đủ · 1 thiếu · 2 chưa kiểm được. Bản tin mở phiên cũng in
> một dòng `CUA: n/m song`. `docs/STATE.md` BƯỚC 40 · 48 · **62**.

> **Quy trình đầy đủ nằm ở skill `quy-trinh-lam-viec`** — gọi nó ngay khi
> bắt đầu bất cứ việc gì trong repo này, TRƯỚC khi đọc hay sửa file đầu
> tiên. Nó có: cách vá file (một đường duy nhất), vòng lặp đột biến, **năm**
> cổng gác đúng thứ tự, công thức chạy-và-chờ, và bảng **lỗi đã mắc** kèm
> cột "máy chặn được chưa".
>
> Nó thay skill `quy-trinh-do-luong` cũ (07/09/2026) — hai skill cùng tự
> nhận là quy trình hiện hành thì đúng lỗi mà dự án này gặp liên tục.

---

## 2. HỆ THỐNG ĐANG Ở TRẠNG THÁI NÀO

**Cách hỏi, thay vì tin con số ở đây:**

| Muốn biết | Hỏi bằng |
|---|---|
| cổng mở lệnh đang mở hay đóng | `paper_trading.py`, dòng gán `CHO_PHEP_MO_LENH_MOI` |
| sổ lệnh thật có gì | `tools/doc_so_that.py` — kéo từ Google Sheets vào một DB **tạm**; **KHÔNG** đọc `paper_trades.db` ở máy |
| bộ lọc VN-INDEX có thật sự bật | `market_filter.status()` |
| gói vnstock đang chạy ở hạng nào | `vnstock_goi.kiem_goi()` |
| điều kiện dừng đang ở đâu | `paper_metrics.dieu_kien_dong_lai()` |

**Ba điều là QUYẾT ĐỊNH, không phải phép đo — chúng ổn định:**

1. **Cổng mở lệnh mới đang ĐÓNG**, đóng bằng tay từ 29/08/2026. Khoá bởi
   `tests/test_c5_noi_that.py`, và test ấy đọc từ NGUỒN chứ không đọc giá
   trị lúc chạy. Mở lại là một hành vi có cân nhắc, phải sửa cả test.
2. **Sổ lệnh THẬT nằm trên Google Sheets.** File `.db` ở máy đứng yên từ
   20/08/2026; đo trạng thái bằng nó là đo một bản sao chết. Đã sai đúng
   như vậy một lần ngày 28/08.
3. **Ngưỡng của điều kiện dừng được SUY RA, không gõ tay.** Muốn biết giá
   trị thì đọc mã, đừng đọc con số trong tài liệu — kể cả tài liệu này.

**Trạng thái đo lường, một câu:** dự án **CÓ một kết quả loại được số
0, và nó ÂM.** Chế độ theo ngày, trượt giá BẬT — alpha quanh **−0,8 tới
−0,9%**, KTC nằm trọn dưới 0, ở vốn đỉnh **đúng 100%**. Ba lượt độc lập
cho cùng kết luận: ĐO 1 (09/09) · ĐO 3 (10/09) · ĐO 4 (11/09).
`docs/STATE.md` BƯỚC 44 · 50 · 52. Con số hiện hành thì đọc bảng ĐO 3
trong `CLAUDE.md`, đừng đọc ở đây.

> 🔴 **CÂU CŨ Ở ĐÂY HẾT ĐÚNG TỪ 09/09/2026 VÀ VẪN ĐỨNG TỚI 14/09.** Nó
> ghi *"dự án hiện không có kết quả nào loại được số 0"* — viết
> 05/09 (`d1b100a3`), và đúng vào ngày ấy.
>
> **Phép sửa ĐÃ ĐƯỢC VIẾT — nhưng viết vào file THẤP HƠN.** Cùng câu ấy
> nằm ở `docs/STATE.md` BƯỚC 25, và ở đó nó được đánh dấu 🔴 ngay hôm
> **09/09** (`feb760d6`). File này thì không. Mà thứ tự ưu tiên của
> chính dự án là `HANDOFF` → `STATE` → `CLAUDE.md`, nên người đọc
> **đúng luật** dừng lại ở câu sai và không bao giờ tới chỗ đã sửa.
>
> Chiều của cái sai đáng chú ý: nó giấu một kết quả **XẤU**. Nó làm
> trạng thái dự án nghe như *chưa kết luận được gì*, trong khi phép đo
> đã kết luận — và kết luận ngược phía chiến lược. Lỗi 57.


**Trạng thái DỮ LIỆU, một câu — mới 22/09/2026:** ba nguồn độc lập mà dự
án nêu tên từ tháng Tám **nay đã đo hết**, và không nguồn nào cho một lợi
thế dùng được.

| nguồn | ở đâu | kết quả |
|---|---|---|
| BCTC theo quý | BƯỚC 53 | 2.099 quan sát · **0/5** qua Bonferroni — có dữ liệu, không tín hiệu |
| khối ngoại | BƯỚC 113 | 61.339 quan sát · cận trên **+0,0387** so với rào hoà vốn **0,1031** — **có** tín hiệu, nhỏ hơn phí **2,66 lần** |
| giao dịch nội bộ | BƯỚC 114 | **0/71 mã** qua `Company(nguon, ma).insider_trading()` — không có dữ liệu qua đường này |

**Hệ quả cho việc lập kế hoạch, và nó khác hẳn hệ quả cũ.** `CLAUDE.md` và
`MO-XE-KIEN-TRUC.md` viết *"nguyên nhân gốc là thiếu dữ liệu độc lập"* khi
chưa nguồn nào được đo; cả hai chỗ nay đã đánh dấu. Dữ liệu độc lập **có**
và **đo được** — thứ chặn là **chi phí thực thi**: tín hiệu 0,0387 hoà vốn
ở chi phí vòng **0,334%**, hiện hành **0,89%**.

Nên cách đọc *"cứ thêm nguồn là sẽ có tín hiệu"* đã đóng. Hướng còn mở đi
theo chiều ngược: **giảm số vòng quay**, không thêm agent — rổ chuẩn mua
một lần trả phí hai lần, chiến lược quay 500 lệnh trả 1.000 lần.

> **Hai giới hạn phải đọc kèm, đừng bỏ:**
> - Cửa sổ 2021-10 → 2026-09 nằm trọn trong vùng **đã bị nhìn nhiều nhất**
>   (bất biến 8), nên 0,0387 là cận trên **TRONG MẪU**, không phải ước
>   lượng ngoài mẫu.
> - Ở nhịp 21 phiên phép đo **không đủ lực** — chứng cứ dương không bắt
>   nổi tín hiệu tiêm đúng bằng rào — nên con số ở nhịp ấy **không đọc
>   được**, kể cả khi nó đẹp hơn.

> 🔴 **Ô này thêm 22/09/2026, và lý do nó phải nằm Ở ĐÂY chứ không chỉ ở
> `docs/STATE.md`:** sáng cùng ngày tôi viết BƯỚC 113 và 114 vào `STATE`,
> đánh dấu `CLAUDE.md` và `MO-XE-KIEN-TRUC.md`, rồi **để nguyên file
> này** — đúng hình dạng **lỗi 57** mà ô đỏ ngay trên mô tả: phép sửa
> viết vào file THẤP HƠN trong khi `HANDOFF` đứng đầu thứ tự ưu tiên.
> Người đọc **đúng luật** sẽ dừng ở đây và không bao giờ tới chỗ đã ghi.

---

## 3. NĂM RÀNG BUỘC KHI LÀM VIỆC

Ba cái đầu rút ra từ lỗi thật hồi tháng Tám, và **cả ba đều nghiêng cùng
một hướng: làm hệ thống trông đỡ hỏng hơn thực tế.** Cái thứ tư thêm ngày
05/09/2026, cái thứ năm ngày 07/09/2026.

1. **Truy vấn ngày phải dùng `substr(signal_date,1,10)`, không so chuỗi.**
   Bảng quyết định có hai định dạng thời gian. Một lượt kiểm chứng mất
   1.266/2.617 dòng vì đúng lỗi này, rồi báo con số hụt ra như bằng chứng.

2. **Cấm tự chế phép tính lợi nhuận.** Chỉ gọi `paper_metrics.compute()`.
   Tự cộng dồn phần trăm từng lệnh từng sinh ra một con số gấp 9 lần con
   số thật, bằng đúng cơ chế đã tạo ra bốn lần trước.

3. **Claim về HÀNH VI của một hàm phải chứng minh bằng CHẠY hàm đó.** Đọc
   thấy `_STATUS = {"active": False}` ở dòng khởi tạo không có nghĩa là
   `status()` trả `False`.

4. **Một gác mới thì phải ĐỤC THỬ trước khi tin, và phép đục phải đi qua
   đúng cái hàm đang phán.** Trong hai ngày 04–05/09 có **năm** lần một
   gác vừa viết xong, vừa xanh, và không kiểm gì cả. Bốn lần đầu phải để
   đột biến chứng minh; lần thứ năm ẩn sau THỨ TỰ CHẠY TEST và chỉ lộ ra
   vì tình cờ đỏ đúng chiều. Xem `docs/STATE.md` BƯỚC 29–31.

5. **Sửa xong một hình dạng lỗi thì phải QUÉT xem nó còn ở đâu nữa —
   trước khi ghi là đã xong.** Sửa một chỗ là sửa một chỗ, không phải sửa
   một lớp. Ngày 05/09 lỗi "gác đọc cờ lúc chạy" được vá tại chỗ đang
   viết rồi dừng; ngày 07/09 một lượt quét AST tìm ra nó **đã nằm sẵn**
   ở `test_tran_von_cam_ket.py`. Xem `docs/STATE.md` BƯỚC 33.

   Kèm theo, và đây là vế hay bị bỏ: **tìm xem repo đã giải chưa trước
   khi tự viết lời giải.** Cả hai lần — cờ C5 ngày 05/09 và chỗ này —
   lời giải nằm sẵn trong `tests/test_c5_noi_that.py` kèm docstring nói
   rõ lý do.

### Và một quy tắc về cách tìm

**Kiểm tĩnh chỉ bắt được thứ đã biết tên.** Grep và AST đều từng bỏ sót
một thẻ giao diện dán cứng con số; chỉ render rồi đọc màn hình mới thấy.
Muốn tìm cái chưa biết thì phải chạy thật, không chỉ đọc mã.

---

## 4. BỐN LỚP LỖI TÀI LIỆU — bốn luật khác nhau

Ngày 05/09/2026 vá xong bốn lớp; chúng không thay thế nhau được.

| Lớp | Luật | Gác |
|---|---|---|
| tên trỏ tới thứ không tồn tại | phải tồn tại, không ngoại lệ | `tests/test_tai_lieu_khop_ten_ma.py` |
| giá trị hiện tại vắng mặt | phải có ở ≥1 chỗ kề tên | `tests/test_tai_lieu_khop_hang_so.py` |
| giá trị cũ để trần | được ở lại, **nhưng phải đánh dấu** | cùng file trên |
| giờ cron lệch mã | suy từ cron, phải kề tên workflow | `tests/test_lich_cron_chuong.py` |

**Quy ước đánh dấu:** một con SỐ cũ được giữ lại kèm ghi chú (🔴 / ⚠️ /
"đã bị thay" / "đo lại ngày…") — đó là lịch sử đo lường, đừng xoá. Nhưng
một cái TÊN đã chết thì **không** được viết dạng `` `module.tên` `` nữa,
vì máy quét không phân biệt được *nhắc lại* với *trỏ tới*.

---

## 5. VIỆC ĐANG TREO

**Chờ tới ngày, đừng đọc sớm:**

- **29/09/2026 — chuỗi khối ngoại có bị SỬA LẠI về sau không.** ĐO 14 đã
  chụp cửa sổ cố định `2025-01-02` → `2025-06-30` của FPT: **119 dòng**,
  sha256 `bf5c67d2…f81332`. Kéo lại đúng cửa sổ ấy rồi so băm. Giống hệt
  thì thu hẹp được khả năng chuỗi bị restate — **không** chứng minh được
  *"không bao giờ sửa"*. Khác thì mọi phép đo dùng nó phải chụp dữ liệu
  tại thời điểm, không kéo lại về sau. Lệnh đọc:
  `tools/do14_kha_thi_khoi_ngoai.py`. `docs/STATE.md` BƯỚC 112.

- ~~**12/09/2026** — tiêu chí về cơ chế rơi nhịp cron~~ **ĐÃ ĐỌC ĐÚNG
  HẠN 12/09/2026:** A = 258,05 phút · B = 2 lượt/ngày → **ô thứ tư,
  TƯƠNG HỢP, chưa phân biệt được**. Không đại lượng nào động đậy so với
  BƯỚC 20/28, nên không có thông tin phân biệt. Dự đoán thứ hai ĐÚNG:
  ba chuông **rơi 0/15 ngày-chuông**, và không commit nào chạm file
  chuông trong tuần ấy nên số 0 ấy sạch. Lệnh đọc:
  `tools/do_roi_nhip.py`. BƯỚC 54.
- ~~**17/09/2026** — tiêu chí về việc dời cron ba chuông~~ **ĐÃ ĐỌC ĐÚNG
  HẠN 17/09/2026: DỜI KHÔNG CÓ TÁC DỤNG.** Trung vị trễ **263,13 phút** so
  với nền **247**, tức tăng +16,13 — trong khi ngưỡng đã ký là *dưới 60 thì
  có tác dụng, trên 120 thì không*. Con số mới **không bước ra khỏi dải
  4–4,7 giờ** BƯỚC 19 đo trên lịch cũ, nên giả thuyết *"trễ do phút trong
  giờ"* bị bác. **KHÔNG dời lại** — lịch hiện tại vô hại, chỉ là không có
  ích, và điều kiện *"không nhịp nào sớm hơn bản cũ"* vẫn có lý do của nó.
  Đọc lúc n = 9/10 và chứng minh được ngày thứ mười không lật được phán
  quyết (cận 260,59–277,01, cùng một ô). Lệnh đọc:
  `tools/do20_doi_cron.py`. BƯỚC 89.
  **Đã đọc lại ở n = 10 ngày 18/09/2026:** trung vị **277,01 phút**, chênh
  nền **+30,01**, 0 ngày rơi nhịp — **bằng đúng cận trên đã ký**, không dư
  một phần trăm phút. Phán quyết giữ nguyên. BƯỚC 101.

**Cần người quyết:**

- ~~**`vnstock_data` 3.2.8 KHÔNG import được nữa**~~ **XONG 18/09/2026:**
  nâng **3.3.0**, `vnstock_ta` khỏi theo (nó vỡ vì `import vnstock_data`,
  một gốc hai symptom). **Không cần người dùng đưa gì** — khoá nằm sẵn ở
  `~/.vnstock/api_key.json` và `vnii` tự đọc. Repo **không nhập
  `vnstock_data` ở đâu cả**, nên không có con số nào đổi và không cần bảng
  tiêu chí. `docs/STATE.md` BƯỚC 104.
- ~~**`urllib3` máy 1.26.20 · CI 2.8.0 — khoảng cách bản CHÍNH, CHƯA AI ĐO.**~~
  **ĐÃ ĐO 18/09/2026 (ĐO 13): NÂNG ĐƯỢC.** Máy nay 2.8.0. Dữ liệu OHLCV
  **không đổi một ô** — băm CSV ba mã giống hệt từng chữ, và ô đối chứng
  D0 đạt ở cả hai chân nên phép so quy được về một vế. `docs/STATE.md`
  BƯỚC 106.
- ~~**`pyarrow` 24.0.0 → 25.0.1** — vế lệch bản CHÍNH cuối cùng~~
  **NGƯỜI DÙNG CHỐT BỎ QUA (18/09/2026).** Lý do đo được, không phải
  cảm tính:

  ```
  repo nhap pyarrow          : KHONG  (AST, tools/so_ban_goi.goi_repo_nhap)
  pyarrow la phu thuoc cua   : streamlit · vnstock_news
  streamlit nhap no o        : 7 file, deu trong dataframe/ va elements/arrow.py
  ```

  Nên phần đáng lo — tuần tự hoá dataframe khi vẽ bảng — nằm **bên trong
  Streamlit**, chỗ dự án không gọi rời được để đo. Một ĐO 14 dựng ra sẽ đo
  được vế *"import có nổ không"* và **không** đo được vế đáng lo; câu trả
  lời trung thực nhất của nó là *"không đo được phần quan trọng"*.
  **Một bảng tiêu chí chỉ có ô không-đọc-được là diễn kịch** — cùng lý do
  ĐO 13 không cần bảng cho `vnstock_data`.

  Hệ quả phải nhớ: máy local ở 24.0.0, CI và Streamlit Cloud ở 25.0.1, và
  **khoảng cách ấy CỐ Ý để lại**. `tools/so_ban_goi.py` vẫn in nó ở hạng
  `con lai` mỗi lượt chạy — nó không im, chỉ là không ai định đóng.
- *(đoạn cũ, giữ để đối chiếu)*
  Nó nằm ở hạng `con lai` nên công cụ không kêu, nhưng `requests` — gói
  repo **CÓ** nhập — chạy trên nó, và 1.x với 2.x khác hành vi. Nâng là
  một phép **ĐO**, cần tiêu chí ký trước; cùng hạng với `pyarrow`
  24.0.0 → 25.0.1. `docs/STATE.md` BƯỚC 105.
- *(đoạn cũ, giữ để đối chiếu)* Không
  phải *"chưa nâng"* — **import là nổ**:

  ```bash
  ./.venv/Scripts/python.exe -c "import vnstock_data"
  ```

  ```
  ImportError: cannot import name 'ProxyConfig'
               from 'vnstock.core.utils.client'
  ```

  Vỡ từ lượt nâng `vnstock` 4.0.8 (ĐO 10, 17/09). **Repo không hề gì** —
  luật cấm `import vnstock_data` ở mức module và mọi chỗ dùng đều bọc
  `try/except`, nên 1.202 test vẫn xanh. Nhưng nó đổi hạng việc nâng lên
  3.3.0 từ *nên làm* thành *phải làm*, và bản 3.3.0 **đổi CON SỐ** (ROE
  23,59 so với 0,2359) nên phải đo lại. Trình cài đòi **khoá của người
  dùng**, và khoá không đi qua tay agent. `docs/STATE.md` BƯỚC 103.
- ~~**Bảng số mục "CHI PHÍ THỰC THI" trong `CLAUDE.md`** cần một lượt đo
  đầy đủ ở cấu hình hiện hành.~~ **XONG** — ĐO 3 (10/09) cho cấu hình mặc
  định, ĐO 4 (11/09) cho cỡ mẫu rộng hơn. Hai bảng, hai câu hỏi, cùng kết
  luận. `docs/STATE.md` BƯỚC 50 và **BƯỚC 52**.
- ~~**Cache BCTC bảng `ratio` chỉ có 2–4 kỳ**~~ **ĐÃ TRUY 11/09/2026:**
  NGUỒN cắt (VCI chỉ phục vụ 4 quý cho bảng ấy), công cụ không hỏng. Và
  **không ai đọc bảng đó** — phép đo IC dùng `_income`+`_balance`, còn
  `fundamental_agent` gọi KBS/năm qua mạng. Điều kiện xem lại agent cơ
  bản **ĐÃ THOẢ** (19 → 31 kỳ) và **đã đo xong**: không chỉ số nào phân
  biệt được với 0, `leverage` mất tín hiệu khi cỡ mẫu tăng. BƯỚC 53.
- ~~**HT1 và TCH đến từ `vci`**~~ **ĐÃ TRUY:** `kbs` trả đủ dữ liệu cho
  cả hai — lượt kéo gặp một lần hỏng tạm thời. Giá hai nguồn KHÁC nhau
  (TCH: 1988/1995 dòng, tỷ lệ TB 0,9971), nên bảng ĐO 4 có **2/71 mã
  trên hệ số khác**. KHÔNG kéo lại — sửa cache là làm ĐO 4 không tái lập
  được. Gốc đã sửa: `fetch_one(nguon=...)` ghim được nguồn.
- ~~**Chạy lại walk-forward với `stride=1`.**~~ **XONG 10/09/2026, và
  KHÔNG bằng `stride=1`** — bằng `--do-tre-khop 1`, vì `stride=1` đổi cùng
  lúc hai thứ. Δ alpha +0,13 / +0,12 điểm, cả hai nhỏ hơn một phần sáu bề
  rộng KTC. `docs/STATE.md` BƯỚC 46.
- ~~**Đổi mặc định `do_tre_khop` sang 1**~~ **XONG 10/09/2026 — và xong
  CÙNG NGÀY dòng này được viết ra đây.** Mặc định đổi ở `1d4a43c`
  (14:41), bảng số thay ở `c7d335b` (17:22), **cùng một PR (#86)** —
  đúng chốt của người dùng. Dòng *"cần người quyết"* này viết lúc
  **08:59** cùng ngày (`955fc6b`), tức nó sống hơn việc của nó **5 giờ
  42 phút**, rồi ở lại thêm **bốn ngày**. Đọc trạng thái, đừng tin dòng
  này:

  ```bash
  ./.venv/Scripts/python.exe -c "import walkforward as w, inspect; print(inspect.signature(w.chay).parameters['do_tre_khop'].default)"
  ```

  Chốt của người dùng thì **giữ lại, vì nó là LÝ DO và lý do không hết
  hạn**: đổi mặc định và thay bảng số phải ra đời cùng một lúc, để không
  có quãng tài liệu ghi một đằng chạy ra một nẻo — đúng hình dạng lệch
  đã cắn dự án này nhiều lần (`N_DAY_DU` 596/451, cờ C5).

**Chưa truy:**

- ~~chênh lệch số lệnh 385 so với 376~~ **ĐÃ TRUY 12/09/2026 (ĐO 5):**
  **mã bị LOẠI bằng phép đo** — commit 28/08 và commit 31/08 chạy trên
  cùng cache hôm nay cho **tập lệnh giống hệt từng dòng**, 376/376, cùng
  ngưỡng 62. Và **tiền đề của câu hỏi bị bác bằng số học**: 9/385 mang
  trọng số 2,3%, nên 9 lệnh chênh có kỳ vọng TB −0,207% là hoàn toàn
  bình thường — *"alpha khớp nên 9 lệnh không thật"* chưa bao giờ đứng
  vững. Không còn dị thường nào cần giải thích. Vế cache **không đo
  được**: lượt kéo 03/09 đã ghi lại đúng toàn bộ rổ 71 mã. BƯỚC 55.
- ~~**khoảng cách chi phí thực thi IS/OOS** — hai giả thuyết chưa ai
  đo~~ **ĐÃ ĐO 12/09/2026 (ĐO 6): CẢ HAI ĐỀU ĐÚNG.** Chúng chưa bao giờ
  là đối thủ. Nến ngoài mẫu mỏng **2,5 lần** (7,32 → 2,93 triệu CP) VÀ
  giá vào thấp hơn **35%** (24.750đ → 16.000đ), mà giá thấp còn làm lệnh
  nhiều cổ phiếu hơn 1,54 lần — ba đường cộng dồn, tỷ trọng khối lượng
  tăng 3,1 lần. Phán quyết theo bảng đã ký là **kết cục 3 (chưa tách
  được)**, và lý do nó không tách được chính là *cả hai cơ chế cùng
  chạy*. BƯỚC 56.
- ~~**72 file mang một nến cuối DỞ**~~ **ĐÃ ĐO 11/09/2026:** sai số
  `close` trung vị **0,721%**, lớn nhất 5,76% — cùng bậc với alpha, nên
  không nhỏ. Nhưng phiên ấy nằm **SAU mọi mốc**, tức trọn trong vùng
  TRONG MẪU, nên **không chạm được một con số alpha ngoài mẫu nào**. Nó
  chỉ có thể dịch ngưỡng IS — mà ĐO 4 chạy trên cache KHÔNG có nến dở
  **chọn lại đúng 62/45**, y hệt ĐO 3. Phép so đã chạy, không phải lập
  luận. Cache cũ giữ nguyên. BƯỚC 53.

---

## 6. BẢN TRƯỚC ĐÃ SAI Ở ĐÂU

Giữ danh sách này để thấy một file "bắt đầu từ đâu" mục ruỗng nhanh thế
nào. Bản 19/08 khẳng định, và tới 05/09 thì:

| Bản trước ghi | Thực tế 05/09 |
|---|---|
| `pytest` kỳ vọng **218 passed**, khác thì dừng | hơn 800 |
| nhánh `sua-chua/phase-0`, chưa merge vào `main` | đã merge từ lâu; nay làm trên nhánh + PR |
| `kiem-dinh.yml` **chưa vào repo** | đã có trong `.github/workflows/` |
| `walkforward_vn100.py` **vẫn còn trong repo** | đã đổi đuôi `.broken` từ 20/08 |
| `truot_gia` và `vong_doi_lenh` là **module mồ côi** | đã nối vào đường khớp lệnh từ 24/08 |
| `sl_pattern_memory.json` có **6.327 mẫu** | 44 mục |
| `_phase0_snapshot.tar.gz` còn trong repo, cần dọn | đã dọn |
| **14 ngày không mở được lệnh** vì cache VN-INDEX đóng băng | đã sửa |
| sổ: 113 lệnh, 1 vị thế mở, `+14,24%` | 117 lệnh, 3 vị thế mở; và `+14,24%` là một trong năm con số đã bị bác |
| **năm ô C1–C5 đang chặn**, cần người quyết | cả năm đã có câu trả lời |

Lịch sử đầy đủ nằm ở `docs/STATE.md` — file này không giữ lịch sử.

---

## 7. CÁCH LÀM VIỆC ĐÃ DÙNG — nên giữ

```
viết test -> CHẠY, phải ĐỎ -> sửa tối thiểu -> test XANH
   -> pytest toàn bộ -> ĐỤC THỬ gác mới -> commit trên NHÁNH -> PR
```

Bước "phải ĐỎ trước" không phải hình thức: có lần **204 test xanh mà
không bắt được một lỗi nghiêm trọng nào** — cổng đóng băng mười ba ngày,
điểm báo cáo là hằng số, giao diện công bố một con số đã bị bác. Sửa
trước rồi viết test sau chỉ sinh ra một test nữa cũng xanh và cũng vô
dụng.

Bước "đục thử" cũng vậy, và nó mới là bước hay bị bỏ. Xem ràng buộc 4.

**Không push thẳng lên `main`** — nhánh, rồi PR. Lý do KHÔNG phải
branch protection (`main` không hề được bảo vệ — đo 08/09/2026): mà vì
`.github/workflows/kiem-dinh.yml` chạy cả trên `push`, nên đẩy thẳng thì
CI chạy **sau**
khi mã đã vào `main`.

Merge thì agent tự làm được từ 08/09/2026, với ba điều kiện ở
`SKILL.md` Bước 5 — quan trọng nhất: **mọi** check `pass`, vì mỗi PR có
hai dòng `kiem-dinh` và dòng thứ hai hay còn `pending`.
