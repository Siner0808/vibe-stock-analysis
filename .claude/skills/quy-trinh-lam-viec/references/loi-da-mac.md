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
| 10 | không biết dự án có skill tới giữa buổi | hệ thống tự hiện | ❌ | `tools/cua_mo_phien.py` **chưa bao giờ chạy** — xem lỗi 14 |
| 11 | dùng `-s` rồi tưởng lỗi mã hoá là lỗi sống | tự kiểm | ✅ | `cong-thuc-chay.md` |
| 12 | ghim `.venv/Scripts/python.exe` — đường Windows, CI là Linux | **CI**, sau 4 cổng xanh | ✅ | `test_script_chay_duoc_tren_windows` |
| 13 | kết luận từ lượt quét HẸP trong khi lượt quét RỘNG còn đang chạy | lượt rộng xong sau, nói ngược lại | ⚠️ một phần | `cong-thuc-chay.md` |
| 14 | **sáu cửa chưa bao giờ chạy** — phiên luôn mở ngoài repo | phép thử ở phiên sau | ⚠️ một phần | `~/.claude/rules/ecc/common/vibe-preview.md` |

**Tám trên mười bốn máy chặn được.** Lỗi 4 hoá ra không phải lỗi thao
tác mà là một LUẬT SAI (mục dưới). Năm cái còn lại — 6, 8, 9, 13, 14 —
là kỷ luật đọc và kỷ luật số; chúng thành Quy tắc số 2, Bước 1, Bước 4,
`cong-thuc-chay.md` và file rules toàn cục.

### Lỗi 14 — cái máy dựng để chặn lỗi 10 cần đúng điều kiện mà lỗi 10 phá vỡ

Ngày 07/09/2026 dựng xong sáu cửa và ghi vào tài liệu rằng
`tools/cua_doc_bat_buoc.py` "cưỡng chế" việc đọc tài liệu bắt buộc. Ngày
08/09/2026 đo lại: **câu đó sai.** Tôi đọc vì tôi nhớ, không vì bị chặn.

Claude Code chỉ nạp `<repo>/.claude/settings.json` khi **thư mục dự án
của phiên** là repo. Mọi phiên của dự án này đều mở ở `C:\Users\cuong`.

Bốn phép đo, ngày 08/09/2026:

| Đo gì | Kết quả |
|---|---|
| `ls ~/.claude/projects/` | chỉ `C--Users-cuong`, `C--Users-cuong-vn-stock-toolkit` — **không có repo** |
| `vibe_da_doc_*.json` trong TEMP | chỉ 3 tên fixture của bộ test, không id phiên thật |
| `python --version` (luật `python-he-thong` khớp, `kiem()` xác nhận) | **chạy được** → cửa Bash chết |
| lặp lại sau `cd` và sau `change_directory` | **vẫn chạy được** → đổi thư mục giữa phiên KHÔNG nạp hook |

`main()` của cửa Bash trả mã **2** và in ra stderr, nên nếu nó có chạy
thì không thể im lặng. Đây là bằng chứng phủ định, không phải suy đoán.

**Nhưng tuyến toàn cục thì sống.** `~/.claude/settings.json` đã có sẵn
`tools/chan_bia_so_lieu.py` với đường dẫn tuyệt đối. Ghi một file `.py` thăm dò
vào repo lúc 08:51 → một file mốc `chan_bia_*.moc` mới xuất hiện đúng
lúc đó. Cửa toàn cục chạy bất kể phiên mở ở đâu.

Phân biệt được nhờ đọc `main()`: nó thoát **trước** khi ghi mốc nếu file
nằm ngoài repo. Nếu không đọc, "không có mốc" hôm nay đã bị đọc nhầm
thành "cửa toàn cục cũng chết" — một kết luận sai từ một quan sát đúng.

**Vì sao chỉ ⚠️ một phần:** phép kiểm `python --version` không tự chạy
được từ trong repo — nếu cửa chết thì chẳng có gì chạy để phát hiện ra
điều đó. Và **cố ý KHÔNG** dựng test canh file rules toàn cục: nó nằm
ngoài repo, ở đường dẫn Windows, nên một test như thế sẽ đỏ trên CI
Linux — đúng hình dạng của lỗi 12.

### Lỗi 13 — trả lời trước khi phép đo xong

Chạy hai lượt quét cùng câu hỏi: một lượt **hẹp** trên một file, một
lượt **rộng** toàn repo. Lượt rộng quá 120 giây nên bị đẩy sang chạy
nền. Tôi trả lời bằng lượt hẹp — và lượt rộng xong sau đó, **nói ngược
lại**.

Cụ thể: kết luận *"dự án không mô hình hoá phí giao dịch"* trong khi
`paper_trading.py` có đủ ba hằng số phí và `Trade.net_return_pct()`
trừ thẳng chúng ra. Sai theo chiều làm kết quả trông **tệ hơn** thực
tế — hiếm, vì quy tắc số 1 nói lỗi đo lường thường nghiêng chiều ngược.

Luật: **một lượt quét bị đẩy sang chạy nền là một phép đo CHƯA XONG.**
Đợi nó, hoặc nói rõ kết luận này chỉ đúng trong phạm vi đã quét.

Bốn cái đầu là **cùng một lỗi**: tự chế cách xử lý xuống dòng. Đó là lý
do `tools/va_an_toan.py` tồn tại.

### Lỗi 12 đáng sợ nhất trong bảng, vì bốn cổng đều XANH

Nó chỉ lộ ra ở CI. Bốn cổng chạy trên máy Windows, và cả bốn không thể
thấy một đường dẫn Windows là sai — ở đây nó **đúng**.

Cùng lớp bất đối xứng đã cắn hai lần trước (31/08/2026), và bài học nằm
sẵn trong docstring của `tests/test_hang_rao_tu_dong.py`: *"Trên Linux CI
nó phải trông vào `sys.executable`"*. Tôi không đọc — **lỗi số 9, lần thứ
tư trong ngày**.

Trớ trêu hơn: cùng buổi đó tôi viết `tools/kiem_test_chay_rieng.py` dùng
`sys.executable` ĐÚNG, rồi viết `tools/va_an_toan.py` dùng đường ghim cứng
SAI. Cùng một người, cùng một giờ, hai lựa chọn ngược nhau — đó là lý do
luật phải nằm trong MÁY chứ không nằm trong đầu.

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
6. **Tên gác nhắc trong bảng này bị canh** — `tests/test_skill_quy_trinh.py`
   bắt tên module test viết trần và tên luật của cửa Bash phải có thật.
   Đổi tên một gác mà quên bảng thì đỏ, không im.
