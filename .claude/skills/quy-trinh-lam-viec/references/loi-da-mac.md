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
| 15 | bật một cửa lên TOÀN CỤC mà chưa thử nó ngoài repo | **đục thử** ngay sau khi bật | ✅ | `test_hang_rao_tu_dong` (3 test hành vi) |
| 16 | chép một kết luận từ ghi chú rồi phát ra như phép đo của mình | **người dùng hỏi lại**, sau 3 ngày | ⚠️ một phần | Bước 1, điều 2 |
| 17 | luật đúng nhưng CẢ HAI lý do của nó chưa ai đo — 4 PR phải quay lại chờ người | **người dùng hỏi lại**, cùng ngày | ⚠️ một phần | Bước 1, điều 2 (lần 2 trong ngày) |
| 18 | dựng phép kiểm nhanh rồi nối bằng `\| tail` — mã thoát của ống là của `tail`, luôn 0 | cổng đầy đủ, lượt thứ ba | ✅ | `cua_bash_an_toan` `pytest-qua-ong` — **luật CÓ SẴN, cửa đang chết (lỗi 14)** |
| 19 | backtick trong `python -c "…"` — bash nuốt khối mã trước khi Python thấy | đọc lại file | ✅ | `cua_bash_an_toan` `backtick-trong-python-c` (luật mới) |
| 20 | một trường CÓ trong kết quả mà **không ai in ra** — test khoá nó có mặt trong dict vẫn xanh | chạy hết 157,7 phút rồi đọc log | ✅ | `tests/test_walkforward.py::test_bao_cao_OOS_in_DU_moi_truong_hop_dong_BAT_bao_cao` (luật mới) |
| 21 | tưởng một phép so 2×2 là 2×2, trong khi luật chọn tham số kéo theo một trục nữa | đọc bảng sau khi đã chạy xong | ❌ | — |
| 22 | kết luận "cửa chết" từ một phép thử dùng thao tác **HỎNG** — cửa chạy TRƯỚC thao tác nên không bao giờ được gọi | tự đo lại sau khi thêm nhật ký, **cùng ngày, sau 2 lần báo sai** | ⚠️ một phần | `tools/cua_doc_bat_buoc.py` ghi nhật ký mỗi lần chạy · `tests/test_cua_doc_bat_buoc.py` (4 test mới) |
| 23 | `cat > <file>` **đè mất một file test 40 phép kiểm đã có** — không kiểm file tồn tại chưa | đếm test: 834 thay vì 874. **Bốn cổng đều XANH** | ✅ | `cua_bash_an_toan` `heredoc-ghi-file-repo` — **luật CÓ SẴN, cửa đang chết (lỗi 14)**, y hệt lỗi 18 |

| 24 | một câu ĐÚNG trong hợp đồng đã ký (*tập TÍN HIỆU* không đổi) được đọc thành một câu khác (*tập LỆNH* không đổi) — không điều kiện nào hỏi tập lệnh, nên nó không bao giờ được đo | tự đi đếm sau khi bảng đã đọc xong | ⚠️ một phần | chưa có luật; quy ước mới ở `docs/TIEU-CHI-DOC-TRUOC.md`: mọi câu *"X không đổi"* phải kèm lệnh kiểm X |

**Mười ba trên hai mươi bốn máy chặn được.** Lỗi 4 hoá ra không phải lỗi
thao tác mà là một LUẬT SAI (mục dưới). Năm cái còn lại — 6, 8, 9, 13, 14 —
là kỷ luật đọc và kỷ luật số; chúng thành Quy tắc số 2, Bước 1, Bước 4,
`cong-thuc-chay.md` và file rules toàn cục.

### Lỗi 23 — đè mất 40 phép kiểm, và BỐN CỔNG ĐỀU XANH

Ngày 09/09/2026, viết test cho ĐO 2:

```bash
cat > tests/test_do_tre_khop.py <<'PYEOF'
```

File ấy **đã tồn tại** với 40 phép kiểm — bộ gác của `do_tre_khop.py`, công
cụ đo độ trễ khớp lệnh. Tôi không kiểm nó có sẵn hay chưa. Cả 40 biến mất.

**Luật máy chặn việc này ĐÃ CÓ SẴN, và nó khớp chính xác.** Chạy
`cua_bash_an_toan.kiem()` trên đúng lệnh đó:

```
[('heredoc-ghi-file-repo', 'Ghi đè file nguồn bằng heredoc... Cách đúng:
  dùng tool Write/Edit, hoặc `tools/va_an_toan.thay()`.')]
```

Cửa không nổ vì `tools/cua_bash_an_toan.py` chỉ đăng ký ở
`.claude/settings.json` **của repo** — tuyến chưa bao giờ chạy. Đây là **lần
thứ hai** lỗi 14 sinh ra một lỗi thật qua một luật đã tồn tại, sau lỗi 18.

#### Chỗ đáng sợ hơn: KHÔNG cổng nào bắt được

| cổng | vì sao mù |
|---|---|
| `pytest tests/` | 834 test **passed** — ít test hơn vẫn là xanh |
| `chan_bia --quet-repo` | quét mẫu bịa số, không đếm test |
| `kiem_cu_phap_311` | file vẫn nạp được bằng 3.11 |
| `kiem_test_chay_rieng` | file vẫn xanh khi chạy một mình |

Và CI cũng vậy — nó chạy đúng bốn cổng ấy.

**Thứ duy nhất bắt được là một con số:** 834, trong khi tôi vừa thêm 9 test
vào một bộ 865. Nếu tôi không nhìn tổng số, PR đã merge với 40 phép kiểm bị
xoá lặng lẽ, và mọi cổng vẫn xanh.

#### Hai câu rút ra

1. **`cat > file` là một thao tác PHÁ HUỶ.** Dùng tool Write/Edit — chúng
   từ chối ghi đè một file chưa đọc. Muốn dùng shell thì kiểm tồn tại
   trước, và đó chính là thứ luật `heredoc-ghi-file-repo` cưỡng chế.
2. **Bốn cổng không đo được thứ bị MẤT.** Chúng kiểm những gì có mặt: mã
   nạp được, test xanh, không mẫu bịa số. Không cổng nào so với lần trước,
   nên mọi kiểu xoá — test, gác, một nhánh trong hàm — đều đi qua im lặng.
   Đó là một lỗ hổng của bộ cổng, không phải của lần này.

### Lỗi 22 — một phép thử dùng thao tác HỎNG không kiểm được cái gì cả

Ngày 09/09/2026 tôi kết luận **hai lần**, và nói với người dùng cả hai
lần, rằng `tools/cua_doc_bat_buoc.py` không cưỡng chế được. Bằng chứng:
gọi `Edit` lên một file được bảo vệ, và nó **không bị chặn**.

Cả hai lần phép thử ấy dùng một `old_string` **không tồn tại trong file**.
Thao tác hỏng ở khâu kiểm tra, và một hook chạy TRƯỚC thao tác thì không
bao giờ được gọi. Phép thử không đo cái nó tưởng nó đo — nó đo rằng một
`Edit` hỏng thì hỏng.

Làm lại bằng một `Edit` **hợp lệ**: cửa nổ, ghi `CHO-QUA-da-doc-du`, cho
qua vì phiên ấy đã đọc đủ hai tài liệu. **Cửa vẫn luôn hoạt động.**

Ba thứ rút ra, và cái thứ ba mới là cái đắt:

1. **Phép thử một cái cửa phải dùng thao tác HỢP LỆ.** Thao tác hỏng dừng
   ở một tầng trước cửa.
2. **"Không thấy nó chặn" ≠ "nó không chặn".** Còn một khả năng thứ ba
   luôn có mặt: nó chưa bao giờ được hỏi.
3. **Cửa im lặng ở nhánh nhường đường là thứ làm phép thử sai kéo dài
   được.** Ba khả năng — không chạy · chạy rồi nhường đường · chạy rồi mã
   thoát bị bỏ qua — trông giống hệt nhau từ bên ngoài. Nay cửa ghi một
   dòng **mỗi lần được gọi**, kể cả khi nhường đường, nên câu hỏi "cửa có
   chạy không" thành một phép đọc file.

Cùng họ với lỗi 15 và 20: thứ hỏng không phải logic, mà là **việc không
quan sát được logic ấy có chạy hay không**.

### Lỗi 21 — một luật chọn tham số cũng là một cái trục

`docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 1 dựng một bảng 2×2: hai công tắc
`MO_PHONG_TRUOT_GIA` nhân hai chế độ mô phỏng, `stride` và `min_history`
ghim nguyên mặc định. Trông như đã ghim hết.

Chạy xong mới thấy **ngưỡng mua không được ghim** — nó do chính lượt chạy
chọn trên in-sample theo luật đã khai trước (≥30 lệnh, rồi kỳ vọng cao
nhất). Luật ấy ra **62 cho chế độ theo mã, 50 cho chế độ theo ngày**. Nên
hai dòng khác chế độ cũng khác ngưỡng, và một nửa số phép so trong bảng
không quy được cho vế nào.

**"Được chọn tự động theo luật khai trước" KHÔNG đồng nghĩa với "được
ghim".** Một luật chọn tham số là một cái trục nữa, và nó ẩn kỹ hơn một
tham số gõ tay vì nó *trông* như kỷ luật.

Cùng hình dạng với vấn đề `stride` ở ĐO 2 — nơi một tham số kéo theo hai
hệ quả — nhưng ở đây nó không nằm trong mã, nó nằm trong **quy trình**.
Trước khi chạy một phép so, liệt kê mọi thứ đổi giữa hai nhánh, kể cả thứ
do máy tự chọn.

### Lỗi 20 — một trường trong dict mà không ai in ra

`docs/TIEU-CHI-DOC-TRUOC.md` bắt báo cáo kèm `alpha_so_lenh`.
`walkforward.py` có trường ấy trong kết quả từ đầu, và
`tests/test_walkforward.py` đã có một test khoá việc nó **CÓ MẶT trong
dict**. Test xanh. Trường vẫn không bao giờ được in.

Phải chạy hết bốn lượt — 157,7 phút — rồi đọc log mới thấy thiếu.

**Một trường nằm trong kết quả mà không đi ra tới người đọc thì với người
đọc nó không tồn tại.** Khoá một đầu là chưa đủ: phải khoá cả "có trong
kết quả" lẫn "có trong báo cáo".

Và gác cho đầu thứ hai phải kiểm **giá trị**, không kiểm nhãn — nhãn còn
nguyên mà in nhầm trường thì phép kiểm nhãn vẫn xanh. Đó đúng là hình
dạng "test kiểm lại chính nó" đã cắn ba lần ngày 31/08/2026.

### Lỗi 19 — backtick đi qua shell trước khi tới Python

Vá tài liệu bằng `python -c "…"`, và trong chuỗi có một khối mã
markdown mở bằng ba dấu backtick. Bash **nội suy** chúng trước khi
Python nhìn thấy chuỗi, nên khối mã bị thay bằng kết quả chạy lệnh —
tức rỗng. File nhận về một khoảng trắng ở đúng chỗ đáng ra có ví dụ.

```
/usr/bin/bash: line 2: $'bashn\n pytest': command not found
/usr/bin/bash: line 2: bon: No such file or directory
```

Hai dòng ấy là tất cả cảnh báo nhận được, và chúng lẫn giữa output
bình thường. `thay()` vẫn báo thành công vì neo khớp đúng một lần —
**nó không có cách nào biết nội dung thay vào đã bị rút ruột.**

Cùng gốc với luật `heredoc-ghi-file-repo` (04–05/09/2026): shell nội
suy `$` và backtick trước khi nội dung tới đĩa. Khác lối vào, nên luật
cũ không bắt được — nay có luật riêng `backtick-trong-python-c`.

**Cách đúng, và nó nằm sẵn trong Bước 2:** vá lớn thì viết một file
`.py` rồi chạy nó. Tool Write ghi file, không qua shell, nên backtick
an toàn. Tôi biết luật ấy và vẫn dùng `python -c` vì nó *nhanh hơn* —
rồi mất thêm hai lượt để sửa.

### Lỗi 18 — một phép kiểm bị nuốt mã thoát KHÔNG phải phép kiểm

Sau khi trả giá hai lượt cổng ~9 phút cho cùng một lỗi tên file trần, tôi
dựng một phép kiểm nhanh 11 giây chạy trước. Rồi viết nó thế này:

```bash
pytest tests/test_skill_quy_trinh.py -q | tail -2 && <bon cong>
```

**Mã thoát của một ống là mã thoát của lệnh CUỐI** — tức `tail`, tức luôn
0. Nên `&&` đi tiếp dù pytest đỏ, và phép kiểm vừa dựng ra không chặn được
gì. Tôi mất lượt cổng thứ BA cho cùng cái lỗi.

Cùng họ với bài học lớn nhất của dự án: **một gác không thể đỏ thì không
phải gác.** Ở đây gác đỏ thật — nhưng không ai nghe được tiếng nó.

> **Cửa Bash ĐÃ CÓ luật cho đúng lệnh này.** Đo 08/09/2026:
> `cua_bash_an_toan.kiem()` trên chính chuỗi lệnh ấy trả
> `[pytest-qua-ong]`. Luật viết từ 07/09, khớp chính xác, và **không thể
> nổ** vì phiên này mở ngoài repo.
>
> **Lỗi 14 trực tiếp gây ra lỗi 18, trong cùng một ngày.** Đó là cái giá
> cụ thể của việc sáu cửa chưa bao giờ chạy — không phải rủi ro trừu
> tượng, mà là ba lượt cổng và gần nửa giờ.

Luật `pytest-qua-ong` sinh ra vì `tail` **đệm output**. Đây là mặt thứ
hai, chưa ai ghi: `tail` **nuốt mã thoát**. Mặt này im lặng hơn.

### Lỗi 17 — luật ĐÚNG, lý do SAI

Luật *"người dùng tự mở và merge PR"* nêu hai lý do: *"`gh` không cài
trên máy này"* và *"`main` có branch protection"*. Ngày 08/09/2026 cả
hai đều bị bác — `gh` đã cài, và `gh api .../branches/main/protection`
trả **404 "Branch not protected"**.

Nhưng vế *"không đẩy thẳng `main`"* vẫn ĐÚNG, vì một lý do chưa ai viết:
`.github/workflows/kiem-dinh.yml` chạy trên **cả `push` lẫn
`pull_request`**, nên đẩy thẳng
thì CI chạy SAU khi mã đã vào `main` — cổng đặt sau cánh cửa.

**Một luật đúng với lý do sai vẫn sẽ bị bác.** Hôm nay ba lần, cùng hình
dạng: luật CRLF (lỗi 4), câu "hook đang cưỡng chế" (lỗi 14), và cái này.

Giá phải trả tính được: bốn PR trong ngày đều dừng chờ người dùng, ba lượt
đầu tôi còn soạn sẵn toàn văn nội dung PR để họ dán tay. Toàn bộ phần đó là
công vô ích do một câu chưa ai đo.

Cùng thuốc với lỗi 16 — **Bước 1, điều 2** — và đây là lần thứ hai áp nó
trong một ngày. `docs/STATE.md` BƯỚC 43.

### Lỗi 16 — lỗi nằm ở lúc NÉN phép đo thành một câu

Bàn giao ghi: *"không nạp lại nguồn vào NotebookLM bằng máy được, nó
không có `input[type=file]`."* Tôi chép lại và phát ra như sự thật đã
kiểm. Người dùng hỏi *"trước đó bạn làm được, sao nay không?"* — và làm
được thật.

**Phép đo gốc ĐÚNG**, đo lại 08/09 vẫn đúng: 0 `input[type=file]` kể cả
shadow DOM 5 lớp và iframe cùng origin; `file_upload` đòi `ref` lúc chạy
dù lược đồ khai không bắt buộc. Không có gì để trách phép đo.

**Kết luận thì rộng hơn phép đo.** *"Đường upload bị chặn"* thành *"không
nạp được"* — hai câu chỉ bằng nhau nếu upload là đường DUY NHẤT. Nó không
phải: cùng hộp thoại có nút "Trang web", và repo công khai nên nạp thẳng
`raw.githubusercontent.com` được, cả bốn file trong một lượt.

**Luật: một câu "không làm được" phải nêu ĐƯỜNG đã thử, không nêu MỤC
TIÊU.** "file_upload không dùng được vì không có ô nhập file" thì đúng
mãi mãi; "không nạp được" thì sai ngay khi có đường thứ hai.

Vì sao chỉ ⚠️ một phần: máy không đọc được văn xuôi để phân biệt hai câu
ấy. Chỗ chặn được là **kỷ luật viết** — nén một phép đo thành một dòng
bàn giao là lúc dễ mất phạm vi nhất, và dòng ấy sẽ sống lâu hơn trí nhớ
của người viết ra nó.

`docs/STATE.md` BƯỚC 42.

### Lỗi 15 — sự mơ hồ TIỀM ẨN thành lỗi SỐNG khi bối cảnh chạy đổi

Chuyển cửa `Stop` lên `~/.claude/settings.json` để nó chạy ở mọi phiên.
Đục thử ngay sau khi bật: từ cwd ngoài repo, nó **quét toàn repo và in 30
dòng cảnh báo**. Ở cuối mỗi phiên của mọi dự án khác.

Nguyên nhân không phải cwd — `file_da_doi()` đã chạy git với
`cwd=GOC_DU_AN` từ đầu. Nó trả `[]` cho **hai** nghĩa: *không hỏi được
git* và *git nói không có gì đổi*. Lựa chọn ấy đúng khi cửa chỉ chạy
trong repo; sai từ giây nó chạy ở nơi khác. **Mã không đổi một dòng —
thứ đổi là nơi nó được gọi.**

Sửa bằng ba trạng thái (`None` / `[]` / `[...]`), đúng lối sẵn có của
`tools/kiem_cu_phap_311.py` và `tools/kiem_test_chay_rieng.py`.

Và tôi đã **nói ra chẩn đoán sai trước khi đo** — báo là do cwd. Cùng họ
với lỗi 13, chỉ khác khoảng cách: một lượt gọi thay vì một lượt quét nền.

`docs/STATE.md` BƯỚC 41.

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


### Lỗi 24 — một câu đúng, đọc thành một câu khác

Hợp đồng ĐO 2 viết, và viết đúng:

> **Tập điểm quyết định KHÔNG đổi.** `consider_entry` vẫn chỉ chạy trên
> lưới `stride`, nên tập tín hiệu là **cùng một tập** — khác hẳn hướng 2,
> nơi số điểm quyết định gấp đôi và **tập lệnh khác hẳn**.

Hai danh từ khác nhau trong một câu, và vế sau đem *tập lệnh* ra chê hướng
2. Người đọc — kể cả người viết — rời câu ấy với ấn tượng rằng ở hướng 3
tập lệnh cũng đứng yên.

Đo sau khi chạy: **xáo 15% ở theo mã, 27% ở theo ngày.** Tín hiệu thì đúng
là cùng một tập; thứ đổi là tín hiệu nào được **nhận**, vì hai chốt sau của
`consider_entry` đọc trạng thái sổ chứ không đọc điểm.

Ba điều kiện đã ký đều có test và đều xanh. Không điều kiện nào sai. Cái
thiếu là **không có điều kiện nào hỏi về tập lệnh** — và một câu khẳng định
không kèm phép kiểm thì không phân biệt được với một câu chưa ai hỏi.

**Quy ước rút ra:** trong tiêu chí khai trước, mọi câu *"X không đổi"* phải
kèm lệnh kiểm X. Nếu không kiểm được thì viết là *chưa kiểm*, đừng viết là
*không đổi*.

Cùng hình dạng với lỗi 21 ở một tầng khác: ở lỗi 21 một trục ẩn sau một
LUẬT trông như kỷ luật; ở đây một đại lượng ẩn sau một CÂU trông như đã
được bảo đảm.
