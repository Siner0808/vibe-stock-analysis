# Cơ chế học có giúp gì không — đo lại trên các lượt ĐỘC LẬP

> 21/08/2026. Thay cho phụ lục A/B trong `ket-qua-walkforward-20260820.md`,
> vì phép đo hôm đó dính một lỗi làm bảy lượt dò ngưỡng không độc lập.

## Vì sao phải đo lại

`post_mortem_learning._ENGINE_CACHE` giữ **một** engine cho cả tiến trình, và
`record_sl_trade()` nối thêm vào `sl_patterns` của engine đó. Nên trong
`walkforward.chay()`, bảy lượt dò ngưỡng cộng lượt OOS dùng chung một bộ nhớ
**đang lớn dần**.

Đo được: ba lệnh cắt lỗ liên tiếp đưa bộ nhớ từ 44 lên 47 mẫu, dù không mẫu
nào được ghi ra đĩa. Docstring cũ của `walkforward.py` ghi *"bộ nhớ GIỮ
NGUYÊN 44 mẫu gốc suốt lượt chạy"* — sai.

Hệ quả: lượt ngưỡng 62 khởi động với bộ nhớ to hơn lượt ngưỡng 45. Bảy lượt
không độc lập, mà chọn lượt tốt nhất trong một dải không độc lập chính là
bất biến 7. **Mọi con số `post_mortem=True` đo trước 21/08/2026 đều dính lỗi
này.**

Nay mỗi lượt có bộ nhớ riêng, dựng lại từ đầu — `dat_lai_engine()`.

## Ba chế độ, ba câu hỏi tách bạch

| | Bộ nhớ đầu lượt | Trong lượt | Câu hỏi |
|---|---|---|---|
| `tat` | rỗng hẳn | — | mốc để so |
| `co_san` | 44 mẫu từ lệnh thật | **chỉ đọc** | bộ nhớ *đang có* giúp gì? |
| `tich_luy` | rỗng | lớn dần | việc *tích luỹ* giúp gì? |

Bản đầu để `co_san` vừa nạp 44 mẫu vừa tích luỹ tiếp — chạy thử thấy nó học
thêm 52 mẫu trong một lượt. Khi đó nó đo một hiệu ứng **gộp** và không quy
được cho bên nào. Đã tách bằng công tắc `chi_doc`.

### Mặc định là `co_san`

Chạy `python walkforward.py` không tham số thì được `co_san`: đo hệ thống
**đang chạy**, có bộ nhớ 44 mẫu của nó, thay vì đo một cấu hình không ai dùng.

Đánh đổi phải biết: `tat` không dựa vào hàng rào nào cả, còn `co_san` thì có.
Bộ nhớ 44 mẫu dựng từ lệnh có tín hiệu 2024-01 → 2026-06, tức nằm trong vùng
IS, trong khi vùng OOS nằm **trước** đó — nên con số ngoài mẫu ở chế độ này
chỉ đúng chừng nào ba hàng rào còn đúng: `as_of`, `phien_hien_tai`, và việc
mẫu thiếu `phien_hoc` bị bỏ. Cả ba có test riêng ở `tests/test_post_mortem.py`
và `tests/test_truc_thoi_gian_thu_hai.py`. **Test nào trong số đó hỏng thì
con số `co_san` mất giá trị** — chạy lại bằng `--che-do-hoc tat` để có một
phép đo không phụ thuộc hàng rào.

Và `co_san` **không** phải bản sao chính xác của đường chạy thật: sổ lệnh
thật vừa dùng bộ nhớ vừa tích luỹ tiếp, còn `co_san` là chỉ đọc. Hôm nay
khác biệt đó nhỏ — đo được rằng 44 mẫu gần như không đổi kết quả gì — nhưng
nó sẽ lớn dần khi bộ nhớ lớn dần, và lúc ấy phải đo lại.

## Kết quả ngoài mẫu

71 mã có vùng IS · 33 mã có vùng OOS · stride 2

| | `tat` | `co_san` | `tich_luy` |
|---|---|---|---|
| ngưỡng chọn trên IS | 62,0 | 62,0 | **50,0** |
| lệnh OOS | 408 | 386 | 646 |
| **alpha khớp từng lệnh** | **−0,160%** | **−0,008%** | **−0,062%** |
| **KTC 95%** | **[−0,903 ; +0,646]** | **[−0,797 ; +0,845]** | **[−0,596 ; +0,530]** |
| mẫu học thêm (lượt OOS) | 0 | 0 | 388 |
| thời gian chạy | 27,7 phút | 28,8 phút | 30,7 phút |

**Cả ba khoảng tin cậy đều chứa 0. Cả ba điểm ước lượng đều âm.** Không chế
độ nào phân biệt được với việc cầm đều cả rổ, và ba chế độ không phân biệt
được với nhau — các khoảng chồng lên nhau gần như hoàn toàn.

Khoảng của `tich_luy` hẹp hơn **không phải** vì nó chính xác hơn, mà vì nó
có 646 lệnh thay vì 408.

## Bằng chứng mạnh hơn cái bảng trên

Kỳ vọng trong mẫu theo ngưỡng, ba chế độ:

```
ngưỡng     45     48     50     52     55     58     62
tat      +0,30  +0,38  +0,52  +0,56  +0,82  +1,00  +1,52     đơn điệu tăng
co_san   +0,30  +0,39  +0,55  +0,54  +0,72  +0,88  +1,31     gần như đơn điệu
tich_luy +0,59  +0,73  +0,78  +0,70  +0,60  +0,68  +0,44     ĐỈNH ở 50 rồi tụt
```

Không có bộ nhớ, quan hệ **đơn điệu sạch**: ngưỡng càng cao thì chất lượng
lệnh trong mẫu càng tốt, không một ngoại lệ. Win rate cũng vậy: 26,8% →
32,3%.

Bật tích luỹ thì quan hệ đó **vỡ**. Kỳ vọng đạt đỉnh ở ngưỡng 50 rồi đi
xuống, và ở ngưỡng 62 — nơi chất lượng đáng lẽ cao nhất — nó lại thấp nhất
dải. Số lệnh cũng tụt mạnh: 332 thay vì 871.

Một quan hệ đơn điệu bị bẻ thành hình răng cưa là dấu hiệu **thêm nhiễu**,
không phải thêm tín hiệu. Hôm 20/08 tôi đã thấy hình răng cưa này nhưng phép
đo khi đó dính lỗi dùng chung bộ nhớ nên không kết luận được. Nay nó tái lập
trên các lượt độc lập.

`co_san` gần như trùng khít `tat` (2.200 / 2.006 / 1.834 lệnh so với
2.200 / 2.008 / 1.841). **44 mẫu hiện có gần như không làm gì cả.**

## Trả lời thẳng

> Cơ chế học có giúp gì không?

Không có bằng chứng nó giúp, theo cả hai nghĩa:

- **Bộ nhớ đang có (44 mẫu):** gần như không đổi kết quả gì.
- **Việc tích luỹ (đến 976 mẫu/lượt):** đổi kết quả, nhưng theo hướng phá vỡ
  một quan hệ vốn sạch, và alpha vẫn âm và vẫn chứa 0.

Nói cho công bằng: cũng **không** kết luận được rằng nó gây hại, vì các
khoảng tin cậy chồng lên nhau.

Chỗ nghẽn không nằm ở cơ chế học mà ở **đầu vào**. Sáu agent đều tính từ cùng
một chuỗi giá; bộ nhớ post-mortem chỉ ghi lại các tổ hợp của chính ba con số
đó, nên nó không thể biết thứ mà giá chưa biết. Xem `MO-XE-KIEN-TRUC.md`.

---

## Đính chính: alpha `+0,428%` trong tài liệu 20/08 là SAI

Tài liệu đó ghi cho lượt `tat`, ngưỡng 62, 408 lệnh:

```
alpha khớp từng lệnh    +0,428%      KTC 95% [−0,375% ; +1,275%]
```

Post-mortem tắt thì mô phỏng tất định, nên chạy lại ra **đúng 408 lệnh**, và
kỳ vọng **+0,431%** trùng khít con số cũ — tập lệnh đúng là một. Nhưng alpha
thì không.

Dựng rổ chuẩn ba cách khác nhau trên **cùng 408 lệnh đó**, `bỏ qua 0` cả ba:

| Rổ chuẩn | Số mã | Lợi nhuận TB của rổ | alpha | KTC 95% |
|---|---|---|---|---|
| chỉ vùng OOS *(cách đang dùng)* | 33 | +0,720% | **−0,160%** | [−0,903 ; +0,646] |
| toàn bộ dữ liệu | 71 | +0,494% | +0,052% | [−0,708 ; +0,851] |
| chỉ vùng IS | 71 | +0,285% | +0,247% | [−0,536 ; +1,062] |

**Không cách nào cho ra +0,428%.** Muốn có con số đó thì rổ chuẩn phải lãi
≈ 0,003% — gần như đứng yên suốt cả giai đoạn. Mọi rổ dựng được từ dữ liệu
này đều lãi từ +0,285% đến +0,720%. Con số cũ được so với một rổ mà dữ liệu
không chống đỡ.

Cách đang dùng là **chỉ vùng OOS**: rổ chuẩn phải là đúng cái vũ trụ mà
chiến lược có thể đã giao dịch trong vùng đó. Lấy cả 71 mã là đưa vào những
mã không có dữ liệu sạch ở vùng OOS — mà đó chính là những mã đã bị các vòng
tối ưu nhìn qua.

**Điều đáng lo hơn cả con số sai:** dấu của alpha **không bền** trước định
nghĩa rổ chuẩn — nó lật từ −0,160% sang +0,247% chỉ vì đổi rổ. Cả ba khoảng
đều chứa 0, nên kết luận *"không khác chuẩn"* vẫn đứng. Nhưng bất cứ ai
trích một điểm ước lượng ở đây mà không nói rõ rổ chuẩn nào thì đang trích
một con số vô nghĩa.

Từ nay `_mo_phong()` tự tính alpha và `main()` tự in ra, kèm số lệnh bị bỏ.
Trước hôm nay công cụ đo ngoài mẫu **không in alpha** — nó in kỳ vọng, win
rate và lợi nhuận cộng dồn, tức trả lời "lãi hơn 0 không" trong khi câu cần
trả lời là "giỏi hơn cầm đều cả rổ không". Người đọc sẽ đọc cái được in.
