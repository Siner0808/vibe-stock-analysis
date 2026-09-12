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

## 1. BỐN LỆNH ĐẦU TIÊN

```bash
pytest tests/ -q
# So với lượt chạy gần nhất trên main, ĐỪNG so với một con số ghi sẵn.
# Đỏ ở đâu thì dừng ở đó. Bộ test này lớn dần mỗi ngày.

python tools/kiem_cu_phap_311.py
# CHẠY SAU pytest, không song song. Máy dùng 3.13, CI dùng 3.11 --
# cú pháp 3.12 nạp được ở máy rồi làm CI đỏ ngay bước đầu.

python tools/chan_bia_so_lieu.py --quet-repo
# Kỳ vọng: 0 CHẶN. Số cảnh báo thì đổi, không phải tiêu chí.

python tools/kiem_test_chay_rieng.py
# MỌI file test phải xanh khi chạy MỘT MÌNH. ~200s, tuần tự (song song
# cho đỏ giả). Mã thoát 2 = CHƯA KIỂM ĐƯỢC, không phải sạch.
# CI cũng chạy; chạy tay khi vừa sửa hoặc thêm test.
```

**Trước khi sửa bất cứ thứ gì liên quan tới KẾT QUẢ, đọc hai file:**
`NGUYEN-TAC-DO-LUONG.md` (8 bất biến) và `MO-XE-KIEN-TRUC.md`.

> 🔴 **Bản trước ghi *"có hook `PreToolUse` chặn nếu chưa đọc"* — CHƯA
> ĐÚNG (08/09/2026).** Cửa ấy có tồn tại, nhưng cửa của repo chỉ được
> nạp khi **phiên được mở ở chính thư mục repo**, và điều đó chưa xảy
> ra lần nào. Kiểm trong một lệnh: `python --version` — bị chặn thì
> cửa sống, in ra số hiệu Python thì cửa chết và việc đọc hai file
> trên là **kỷ luật của người**, không phải ràng buộc của máy.
> `docs/STATE.md` BƯỚC 40.

> **Quy trình đầy đủ nằm ở skill `quy-trinh-lam-viec`** — gọi nó ngay khi
> bắt đầu bất cứ việc gì trong repo này, TRƯỚC khi đọc hay sửa file đầu
> tiên. Nó có: cách vá file (một đường duy nhất), vòng lặp đột biến, bốn
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
| sổ lệnh thật có gì | kéo từ Google Sheets — **KHÔNG** đọc `paper_trades.db` ở máy |
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

**Trạng thái đo lường, một câu:** dự án hiện **không có kết quả nào loại
được số 0**. Chi tiết ở `docs/STATE.md` BƯỚC 25.

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

- ~~**12/09/2026** — tiêu chí về cơ chế rơi nhịp cron~~ **ĐÃ ĐỌC ĐÚNG
  HẠN 12/09/2026:** A = 258,05 phút · B = 2 lượt/ngày → **ô thứ tư,
  TƯƠNG HỢP, chưa phân biệt được**. Không đại lượng nào động đậy so với
  BƯỚC 20/28, nên không có thông tin phân biệt. Dự đoán thứ hai ĐÚNG:
  ba chuông **rơi 0/15 ngày-chuông**, và không commit nào chạm file
  chuông trong tuần ấy nên số 0 ấy sạch. Lệnh đọc:
  `tools/do_roi_nhip.py`. BƯỚC 54.
- **17/09/2026** — tiêu chí về việc dời cron ba chuông, khai trước ngày
  03/09. Nền 247 phút.

**Cần người quyết:**

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
- **Đổi mặc định `do_tre_khop` sang 1 — ĐÃ CHỐT 10/09/2026: đổi, nhưng
  KHÔNG đổi rời.** Gộp vào **lần đo lại đầy đủ tiếp theo**, để mặc định
  mới và bảng số mới ra đời cùng một lúc. Lý do người dùng nêu: đổi bây
  giờ thì có một quãng tài liệu ghi một đằng, chạy ra một nẻo — đúng hình
  dạng lệch đã cắn dự án này nhiều lần (`N_DAY_DU` 596/451, cờ C5).

  Việc cụ thể khi tới lúc: đổi mặc định trong `walkforward.py`, sửa
  `tests/test_do2_lich_ghe.py::test_DIEU_KIEN_1_mac_dinh_cho_lich_Y_HET_hom_nay`
  cho khớp chủ đích mới, chạy lại bảng bốn lượt, thay bảng trong
  `CLAUDE.md` trong CÙNG một PR.

**Chưa truy:**

- ~~chênh lệch số lệnh 385 so với 376~~ **ĐÃ TRUY 12/09/2026 (ĐO 5):**
  **mã bị LOẠI bằng phép đo** — commit 28/08 và commit 31/08 chạy trên
  cùng cache hôm nay cho **tập lệnh giống hệt từng dòng**, 376/376, cùng
  ngưỡng 62. Và **tiền đề của câu hỏi bị bác bằng số học**: 9/385 mang
  trọng số 2,3%, nên 9 lệnh chênh có kỳ vọng TB −0,207% là hoàn toàn
  bình thường — *"alpha khớp nên 9 lệnh không thật"* chưa bao giờ đứng
  vững. Không còn dị thường nào cần giải thích. Vế cache **không đo
  được**: lượt kéo 03/09 đã ghi lại đúng toàn bộ rổ 71 mã. BƯỚC 55.
- **khoảng cách chi phí thực thi IS/OOS** — còn hai giả thuyết chưa ai
  đo. ĐO 4 thêm một dữ kiện: vùng OOS rộng gấp ba mà chi phí dòng
  theo-ngày **giảm** 0,66 → 0,48, tức không nghiêng về giả thuyết *"OOS
  thanh khoản mỏng hơn"*. Quan sát, **không phải** phép đo thiết kế cho
  câu hỏi ấy, nên chưa loại được gì.
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
