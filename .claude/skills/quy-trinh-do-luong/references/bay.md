# Những cái bẫy đã sập thật — đọc khi gác mới của bạn xanh ngay lần đầu

Mọi mục dưới đây là chuyện **đã xảy ra trong dự án này**, không phải khả
năng lý thuyết. Kèm ngày để tra lại `docs/STATE.md`.

---

## Ba mẫu đột biến hay sống sót nhất

### 1. Test kiểm lại chính nó

Test **dựng lại công thức của mã** rồi so hai bên. Nó kiểm công thức của
test, không kiểm công thức của mã — nên mọi đột biến giữ nguyên **giá trị**
tại điểm đang thử đều sống sót.

Ba lần trong một ngày (31/08/2026):

| Đột biến sống sót | Vì sao lọt |
|---|---|
| nhánh `theo_ngay` thành no-op | test kiểm `lich_theo_ngay` như hàm THUẦN, không kiểm nhánh CÓ GỌI nó |
| `TRAN * N / 225` thay cho `TRAN / N` | cho đúng 6,667 tại N=15; kể cả `CỠ × N == TRẦN` cũng mù |
| matcher hook đổi thành `NotebookEdit` | test đọc `command`, bỏ qua `matcher` |

**Cách chặn:** kiểm hình dạng biểu thức bằng AST, và kiểm cả **chỗ nối** —
"hàm X có tồn tại" khác "nhánh Y có gọi X".

### 2. Gác đọc `in` thay vì đọc AST

`"chi_so_moi_nhat" in src` khớp cả chữ trong khối chú thích ngay phía trên.
Càng viết chú thích trung thực thì gác kiểu `in` càng dễ vô hiệu. Đã đục
thử ngày 22/08/2026: xoá hẳn lời gọi trong thân hàm, **cả hai gác vẫn xanh**.

Mọi khẳng định *"file X có gọi Y"* phải đi qua
`tests/test_no_fabricated_data.py::_ten_da_nhap_va_goi()`.

### 3. Công cụ kiểm tra không chạy được

Cũng là cổng xanh giả. `tools/kiem_ban_sach.py` nổ `UnicodeEncodeError`
ngay dòng `print` đầu tiên vì thiếu `encoding="utf-8"`. Lỗi đó tái diễn
**ba lần** (22, 23, 24/08/2026) trước khi có gác toàn repo
`tests/test_script_chay_duoc_tren_windows.py`.

Mọi script có `__main__` và `print` phải gọi:

```python
sys.stdout.reconfigure(encoding="utf-8")
```

---

## Thay đổi không đo được

Nếu không có phép đo nào chứng minh thay đổi đúng, **dừng lại và tìm xem
cái gì đang chặn phép đo** — thường đó mới là việc thật.

Ví dụ thật (31/08/2026): cần gạt "giữ 15 vị thế thay vì 5" hoá ra vô hình,
vì `walkforward._mo_phong` chạy **theo mã** nên số vị thế đồng thời luôn
bằng 1 và trần vốn không bao giờ chạm. Đổi sizing khi đó chỉ co đường vốn
lại, không sinh thêm một lệnh nào. Việc thật là làm backtest biết tới danh
mục, không phải đổi hằng số.

---

## Cạm bẫy số liệu

| Bẫy | Hỏng thế nào | Kiểm bằng |
|---|---|---|
| Đơn vị giá | vnstock trả **nghìn đồng**, agent trả VNĐ → `low <= stop_loss` luôn đúng | `data_quality.price_multiplier()` |
| `volume` bị nhân hệ số giá | tỷ trọng nhỏ đi 1.000 lần, trượt giá gần như biến mất, kết quả vẫn trông hợp lý | test riêng soi nến `fill_pending` nhận được |
| `download()` | bỏ qua mã đã có cache → mã tải lần đầu 13 tháng sẽ **mãi mãi** 13 tháng | dùng `extend_history()` |
| Cửa sổ dữ liệu | dưới 50 phiên thì SMA50/SMA200 trả `None`, `trend_score` kẹt 3 nấc | `run_daily.bao_cua_so_du_lieu()` |
| Nhãn lợi nhuận thô | tương quan chéo +0,368 → 68 mã sụp còn **2,6 mã độc lập** | dùng nhãn **vượt rổ** (bất biến 6) |
| Lệnh chồng lấn | cộng dồn vào toàn bộ vốn = đòn bẩy trá hình. Đo được 211% TB, đỉnh 1049% | `Performance.avg_capital_deployed_pct` |
| Thiên lệch sống sót | rổ là ảnh chụp hôm nay; mã đã rớt không có mặt | **chưa xử lý** — mọi kết quả vẫn lạc quan hơn thực tế |

---

## Bất biến không được làm hỏng

- `tests/test_post_mortem.py::test_cham_diem_khong_doi_khi_chay_lai`
  — cùng input phải ra cùng điểm
- `tests/test_paper_trading.py::test_duong_von_khong_phu_thuoc_thu_tu_ban_ghi`
  — drawdown dựng theo **thời gian**, không theo id
- `tests/test_hang_rao_quy_trinh.py` — sổ đăng ký điều kiện an toàn. Thêm
  một hàm `dieu_kien_*` mà không khai → đỏ

---

## Máy chạy 3.13, CI chạy 3.11

`pytest` xanh tại máy **không** bảo đảm CI xanh. Cú pháp có từ 3.12 nạp
bình thường ở máy rồi làm `ast.parse` nổ trên runner (đã xảy ra 21/08/2026:
f-string PEP 701 trong `run_daily.py`, 319 test xanh tại máy, CI đỏ ngay
bước đầu).

`ast.parse(feature_version=(3,11))` **KHÔNG** bắt được — nó không hạ cấp bộ
tách token. Phải chạy bằng một trình thông dịch 3.11 thật, và
`tools/kiem_cu_phap_311.py` làm việc đó, kể cả với python nhúng trong
heredoc của workflow YAML.
