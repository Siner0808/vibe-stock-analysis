# Lỗi quy trình đã mắc — thêm một dòng mỗi lần có lỗi mới

Đây là **bảng đếm**, không phải bài học đạo đức. Mỗi dòng phải trả lời
được: *máy chặn được không, và đã chặn chưa.*

Cột "bắt bởi" quan trọng ngang cột "lỗi": lỗi bắt được **bằng tình cờ**
là lỗi sẽ tái diễn.

---

## Rà phiên 07/09/2026 — 11 lỗi trong một phiên

| # | Lỗi | Bắt bởi | Máy chặn? | Đã chặn bằng |
|---|---|---|---|---|
| 1 | neo vá dùng `\n` trên file CRLF (×3) | chính script | ✅ | `va_an_toan.thay()` |
| 2 | neo vá dùng `\r\n` trên file LF | chính script | ✅ | `va_an_toan.thay()` |
| 3 | tiếng Việt trong `b"..."` → SyntaxError | Python | ✅ | `va_an_toan` (chế độ văn bản) |
| 4 | file mới ghi LF trong repo "CRLF" (×2) | trí nhớ | — | **luật đó SAI**, đã bác |
| 5 | hai heredoc một lệnh → áp nửa số thay đổi | tình cờ | ✅ | `cua_bash_an_toan` `hai-heredoc` |
| 6 | ước 40s, thật 167,7s (sai 4×, chiều nịnh) | tình cờ đi tính | ⚠️ một phần | Quy tắc số 2 |
| 7 | `pytest \| tail` chạy nền → ≥10 lượt hỏi "xong chưa" | tự nhận ra muộn | ✅ | `cua_bash_an_toan` `pytest-qua-ong` |
| 8 | sửa `CLAUDE.md` khi pytest đang chạy | trí nhớ | ⚠️ một phần | Bước 4, dòng cuối |
| 9 | không tìm lời giải sẵn có (lần 2/3 ngày) | đọc lại | ⚠️ một phần | Bước 1 |
| 10 | không biết dự án có skill tới giữa buổi | hệ thống tự hiện | ✅ | Bước 0 (`ls .claude/skills/`) |
| 11 | dùng `-s` rồi tưởng lỗi mã hoá là lỗi sống | tự kiểm | ✅ | `cong-thuc-chay.md` |

**Bảy trên mười một máy chặn được.** Ba cái còn lại là kỷ luật đọc và
kỷ luật số — chúng thành Quy tắc số 2, Bước 1 và Bước 4.

Bốn cái đầu là **cùng một lỗi**: tự chế cách xử lý xuống dòng. Đó là lý
do `tools/va_an_toan.py` tồn tại.

### Lỗi số 4 hoá ra là một LUẬT SAI, không phải một thao tác sai

Đo lại mới thấy: index 412/412 file text là LF thuần, `core.autocrlf =
true`, không `.gitattributes`. Quy ước xuống dòng của bản trên đĩa
**không ảnh hưởng tới thứ được commit**. Luật "giữ CRLF" — nằm trong
`CLAUDE.md` và skill cũ — là nguyên nhân của lỗi 1, 2, 3, 4.

**Một luật sai gây ra nhiều lỗi hơn là không có luật.**

---

## Trước đó (từ `docs/STATE.md`)

| Ngày | Lỗi | Máy chặn? | Đã chặn bằng |
|---|---|---|---|
| 05/09 | `write_text(newline=…)` làm file rỗng 0 byte | ✅ | `tools/cua_ghi_an_toan.py` |
| 05/09 | gác đọc cờ an toàn **lúc chạy** | ✅ | `test_c5_noi_that` (đọc NGUỒN) |
| 05/09 | tự chứng minh đi qua hàm TRÍCH, không qua hàm PHÁN | ⚠️ | Bước 3, điều 1 |
| 04–05/09 | 5 lần gác vừa viết xong đã vô dụng | ✅ | Bước 3 (vòng lặp đột biến) |
| 07/09 | gác RẼ NHÁNH theo cờ bị rò | ✅ | `test_gac_khong_phu_thuoc_thu_tu` |
| 07/09 | 7 test âm thầm phụ thuộc cờ bị rò | ✅ | `tools/kiem_test_chay_rieng.py` |
| 31/08 | hook đổi matcher, test không kiểm matcher | ✅ | `test_hang_rao_tu_dong`, `test_cua_quy_trinh` |
| 22–24/08 | thiếu `stdout.reconfigure` (3 lần) | ✅ | `test_script_chay_duoc_tren_windows` |

---

## Cách thêm dòng mới

1. Ghi lỗi vào bảng trên, kèm **cách nó bị bắt**.
2. Hỏi: máy chặn được không?
3. Chặn được → thêm luật vào `tools/cua_bash_an_toan.LUAT` hoặc dựng cổng
   mới, **kèm test hai chiều** (mẫu xấu phải bị bắt, mẫu tốt phải được
   tha).
4. Luật mới phải khai nguồn: **ngày sự cố**, hoặc dấu `CHƯA CÓ SỰ CỐ`
   kèm tên file quy ước.
5. Đục thử luật mới. Chưa đục thì chưa tin.
