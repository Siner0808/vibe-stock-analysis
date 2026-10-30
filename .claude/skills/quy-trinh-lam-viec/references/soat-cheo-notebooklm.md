# Soát chéo bằng sổ tay NotebookLM — CÁCH LÀM

Tài liệu tham khảo của skill `quy-trinh-lam-viec`, không phải skill riêng:
dự án cố ý giữ **một** skill (`tests/test_skill_quy_trinh.py::test_CHI_CO_MOT_skill_quy_trinh`).
Đọc nó mỗi lần làm Quy tắc 3.

BƯỚC đổi một luật hoặc một kết luận đo phải qua sổ tay; người dùng chốt
18/09/2026 cho MỌI BƯỚC rồi "Đồng ý" thu hẹp ngày 08/10/2026 (từ BƯỚC 164,
BƯỚC ≤ 163 giữ luật cũ). File này là **cách làm**; luật và lý do nằm ở
`SKILL.md` — Quy tắc 3 và mục *Luồng thông tin thứ hai — NotebookLM*.
Mọi dòng dưới đây đến từ một lượt đã hỏng thật.

**Cách làm viết lại ở BƯỚC 246 (30/10/2026)** sau khi người dùng đòi làm việc với
NotebookLM *"chuyên nghiệp hơn"* và chọn *"A ngay, thử notebooklm-py sau bằng tài khoản
riêng (Recommended)"*: thứ tự một lượt soát là **độ tươi → xoá nhật ký chat → kiểm độ dài →
gửi → chờ xong → lưu có bắt tay → tự kiểm bằng `grep` → ghi sổ**. Mỗi bước có một lệnh của
`tools/so_tay.py` (JS do máy dựng, không gõ tay). Lệnh JS chạy trong trình duyệt của leader:
phiên con không có trình duyệt, nên đưa leader đường dẫn tệp JS và nhận lại kết quả THÔ.

**Bước 0 của mỗi BƯỚC từ 164 — phải hỏi hay không?** Hỏi máy, không tự nghĩ:

```bash
./.venv/Scripts/python.exe tools/buoc_cham_luat.py 164
```

In `CHAM LUAT [file…]` thì **hỏi thật** (các chặng dưới). In `khong cham luat`
thì có thể ghi MỘT dòng thay vì hỏi — tệp mục (JSON tạm, ngoài repo) chỉ gồm `buoc` và
`khong_bat_buoc_vi` (lý do cụ thể, không dán lại lý do của BƯỚC khác), rồi
`./.venv/Scripts/python.exe tools/so_tay.py ghi <tệp mục>`; `ghi` hỏi lại máy và
từ chối nếu BƯỚC chạm file luật. Máy chỉ thấy FILE: BƯỚC viết một kết luận đo mới
chỉ trong `docs/STATE.md` thì máy khai "không chạm" — tự hỏi mình trước khi tin nó.
Hỏi thật vẫn luôn được phép, kể cả khi máy cho miễn.

Sổ tay chỉ đọc **TÀI LIỆU**, không đọc mã, và nguồn của nó là **bản chụp**
lúc nạp. Nó là một luồng đọc độc lập, không phải trọng tài. **Mọi phát hiện phải tự kiểm
lại, kể cả câu "không tìm thấy".**

---

## Chặng 1 — Mở sổ (trình duyệt TRONG Claude Code, KHÔNG Chrome)

Người dùng chốt 24/09: `mcp__Claude_Browser__*`, không mở Chrome (RAM).

```
navigate  https://notebook.google.com/notebook/039ade07-6eeb-4863-b892-1b920e9a94bf
```

Từ 30/10/2026 trang có tên **Gemini Notebook** ở máy chủ `notebook.google.com` (địa chỉ cũ
`notebooklm.google.com` chuyển hướng qua đăng nhập Google rồi tới đây). Đọc `location.host` bằng
`javascript_tool`:

- `accounts.google.com` → **nhờ người dùng đăng nhập** trong khung ấy rồi
  làm việc khác trong lúc chờ. Đăng nhập KHÔNG sống qua phiên mới hay khi
  khung bị đóng (đo 25/09, 27/09). **Không bao giờ tự nhập mật khẩu.**
- `notebook.google.com` → tiếp.

Giao diện hẹp là loại có tab (**Nguồn** | **Trò chuyện** | **Studio**): lệnh dưới chỉ thấy phần
tử của tab đang mở.

## Chặng 2 — Độ tươi: đo bằng NHÃN, không hỏi mô hình

Nhãn mỗi nguồn là `<tệp> @<băm 7 ký tự>` (đặt lúc nạp, xem *Nạp lại nguồn*). Git biết tệp đã đổi
chưa kể từ băm ấy; mô hình thì không (29/10/2026 nó trả lạc đề câu hỏi độ tươi của BƯỚC 241).

1. Mở tab **Nguồn**. Đưa leader `lay-nhan`:

   ```bash
   ./.venv/Scripts/python.exe tools/so_tay.py lay-nhan > <thư mục nháp>/lay_nhan.js
   ```

   Kết quả có dòng đầu `<n> nhan` rồi mỗi nhãn một dòng (số nguồn hiện cạnh ô chat, ví dụ
   "(19)", phải bằng n; đọc ra 0 nhãn là MẪU hỏng, không phải sổ rỗng). Leader lưu vào một tệp. Phép BỎ CHỌN nguồn không sống qua phiên: đọc nhãn mỗi lượt. Nhãn
   lấy từ `aria-label` của NÚT nguồn, **không bao giờ** gỡ từ một câu trả lời của mô hình (đo 30/10:
   nó gộp 19 nhãn trên MỘT dòng cách nhau bằng dấu cách).
2. Đo:

   ```bash
   ./.venv/Scripts/python.exe tools/so_tay.py do-tuoi <tệp nhãn>              # từng nguồn
   ./.venv/Scripts/python.exe tools/so_tay.py do-tuoi <tệp nhãn> --tom-tat    # MỘT dòng cho `_do_tuoi`
   ```

   Mỗi nguồn là `TUOI` (tệp không đổi giữa băm và `HEAD`) · `CU` · `KHONG_RO_BAM` · `KHONG_THAY_TEP`
   · `MO_HO`; thêm `THIEU` (tệp của `NGUON_MAC_DINH` không có nhãn nào) và `NHAN_LA`. Riêng
   `docs/STATE.md` dán thành khúc nên so từng khúc với khúc cùng số ở `HEAD` (nhãn
   `phanK/N`): BƯỚC thêm ở cuối không làm các khúc đầu cũ đi. Mã thoát 0 tươi hết · 1 có
   chỗ cũ/thiếu · 2 chưa đo được (git hỏng). Lệnh chỉ BÁO; chọn nguồn nào là việc của người dùng.
3. `CU`/`THIEU` thì làm tươi (mục *Nạp lại nguồn*) trước khi hỏi, hoặc chấp nhận và để dòng
   `--tom-tat` vào mục sổ. **`_do_tuoi` do máy sinh** — tệp mục khai `nhan_nguon_tep: <tệp nhãn>`
   và `ghi` tự điền `nguon` + `_do_tuoi` từ git (khai tay cả hai kèm nó thì bị từ chối).

## Chặng 3 — Xoá nhật ký trò chuyện (quyền thường trực, có giới hạn)

Lịch sử chat còn nguyên sau đăng nhập lại và mô hình trả lời LẠI câu cũ (29/10/2026, BƯỚC 241), nên
mỗi lượt soát bắt đầu từ nhật ký rỗng.

**Quyền của người dùng, nguyên văn, 29/10/2026:** *"Cho phép, đọc lại hộp xác nhận trước khi bấm
(Recommended)"* — leader được **xoá nhật ký trò chuyện của sổ tay trước mỗi lượt soát**. Giới hạn:
- CHỈ nhật ký trò chuyện. **Không bao giờ** xoá nguồn hay sổ tay (xoá nguồn vẫn theo mục *Nạp lại
  nguồn*: chỉ bản vừa có bản thay, còn lại hỏi người dùng).
- Phải đọc hộp xác nhận trước khi bấm. Việc đọc nằm trong lệnh, không trong trí nhớ. Bốn lệnh, MỖI
  lệnh một lần gọi đồng bộ, chờ ~1 giây giữa hai lệnh cho trang vẽ:
  `./.venv/Scripts/python.exe tools/so_tay.py xoa-nhat-ky --buoc 1` (bấm nút ⋮ ở thanh đầu) ·
  `--buoc 2` (chọn mục `Xoá nhật ký trò chuyện`) · `--buoc 3` (đọc MỌI hộp thoại — hộp hiện hai lần
  trong DOM và một hộp chọn emoji ẩn cũng mang `role=dialog` — chọn cái HIỆN và mang đúng câu
  `Bạn sắp xoá toàn bộ nhật ký trò chuyện của sổ ghi chú này`, chỉ bấm nút `Xoá` của hộp ấy; hộp khác
  → `TU CHOI ·…` và không bấm gì) · `--buoc 4` (đếm trả lời còn lại — xoá là BẤT ĐỒNG BỘ: đo 30/10, bước 4 ngay sau bước 3 còn thấy 1 và vài giây sau mới thấy 0. **Chạy lại bước 4 cho tới khi = 0; không gửi khi còn > 0**; lệnh điền câu hỏi cũng từ chối điền khi nhật ký còn trả lời, trừ `--giu-lich-su`).
- Thấy `TU CHOI` thì DỪNG, đọc chẩn đoán trong chuỗi trả về, đừng bấm tay thay máy. Quyền này chỉ phủ
  nhật ký trò chuyện.

## Vì sao KHÔNG lệnh JS nào hẹn giờ (đo 30/10/2026, leader)

Khi cửa sổ Claude không hiện, `document.hidden` là `true` (`visibilityState` "hidden") và trình duyệt
bóp `setTimeout` đến mức MỘT `await new Promise(r => setTimeout(r, 750))` đứng riêng không xong trong
45 s — công cụ giết JS ở 45 s. Đọc đồng bộ thì tức thì; `await crypto.subtle.digest(...)` VẪN xong khi
ẩn (thử hai lần). Bản đầu của BƯỚC 246 chờ 38 s ngay trong trang và chết đúng như vậy. Hệ quả:
mọi lệnh của `tools/so_tay.py` đọc hoặc bấm MỘT lần rồi trả về; **việc chờ là của người gọi**
(chạy lại lệnh), và "xong" là chuỗi lần chụp giống nhau chứ không phải một lần đọc. **Mỗi lệnh đi qua MỘT lần `javascript_tool`, không qua `browser_batch`** (đường truyền làm hỏng chuỗi JS dài), và lệnh không mang `\uXXXX` nào: `\u2028`/`\u2029` trong một regex literal bị đổi thành ký tự ngắt dòng thật và lệnh không biên dịch được (lỗi 199, 30/10/2026; so mã ký tự bằng `charCodeAt`). Gác:
`tests/test_so_tay_trinh_duyet.py::test_KHONG_lenh_JS_nao_hen_gio_vi_khung_an_bop_setTimeout`.

## Chặng 4 — Dựng câu hỏi bằng MÁY, không gõ tay

```bash
./.venv/Scripts/python.exe tools/so_tay.py hoi --buoc "BƯỚC n" \
    --ket-luan "<kết luận SẮP VIẾT, cụ thể, có tên file/hàm/con số>" \
    --vi-du "<các câu nghi ngờ, viết một chuỗi: a statement that ..., or that ...>"
```

Nó đóng khuôn bốn chỗ đã hỏng: **một dòng** (Enter trong ô chat là GỬI),
**lối thoát** nguyên văn (thiếu thì sổ tay BỊA — BƯỚC 107), **miễn trừ câu
đã có dấu** 🔴/*HẾT ĐÚNG* (thiếu thì hàng chục mâu thuẫn giả), **đòi trả lời
tiếng Việt** (câu hỏi tiếng Anh — chốt 17/09).

**Độ dài tối đa 3.800 đơn vị UTF-16** (`TRAN_GUI`). Đo 30/10/2026: nút Gửi mở ở ≤ 3.900 và khoá
ở ≥ 3.901, KHÔNG có bộ đếm hay báo lỗi — câu dài hơn chỉ là nút Gửi khoá. `hoi … --js` từ chối
dựng lệnh và nói rõ độ dài; `ghi` cũng từ chối `cau_hoi` dài hơn. Đơn vị là của JS (`String.length`):
ký tự như 💡 tính 2. Dài quá thì rút kết luận hoặc bớt ví dụ, đừng chia câu thành hai lượt.

**Hỏi về MỘT KẾT LUẬN CỤ THỂ, kèm VÍ DỤ câu nghi ngờ.** Câu hỏi rộng
(*"câu nào bị câu khác nói ngược"*) trả *"không tìm thấy"* SAI (25/09); câu
hỏi cụ thể trả 4/4 trích dẫn khớp. Và hỏi *"có chỗ nào NÓI NGƯỢC kết luận
tôi sắp viết"*, đừng hỏi *"tài liệu nói gì về MÃ của tôi"* — nó không thấy mã.

## Chặng 5 — Gửi: ĐIỀN rồi BẤM, hai lệnh

```bash
./.venv/Scripts/python.exe tools/so_tay.py hoi --buoc "BƯỚC n" --ket-luan "…" --vi-du "…" --js   # điền
./.venv/Scripts/python.exe tools/so_tay.py bam-gui --dai <độ dài lệnh trước in ra>                # ~1 giây sau
```

Lệnh điền chọn ô chat theo nhãn `Hộp truy vấn` (`textarea` **đầu tiên** của trang là ô *"Tìm nguồn
mới trên web"* — lỗi 113: một lệnh tự viết đã gửi câu hỏi vào đó), KHÔNG bấm gì, và in
`DA DIEN · o co <D> ky tu · tra loi truoc: <N>`. **Ghi D và N.** Nút Gửi còn khoá ngay sau sự kiện
`input` (đo 29/09) nên bấm là lệnh thứ hai: nó chỉ bấm khi ô chat có ĐÚNG D đơn vị (chống bấm khi
ô đang chứa thứ khác) và nút đã mở khoá; khoá thì trả `NUT GUI VAN KHOA` — gọi lại sau ~1 giây.
Trang có HAI nút `Gửi` (nút số 0 luôn khoá, ô "Nghiên cứu nhanh"); lệnh leo cây từ ô chat nên lấy nút
gần ô chat nhất.

## Chặng 6 — Chờ trả lời xong: CHỤP lặp lại

```bash
./.venv/Scripts/python.exe tools/so_tay.py chup --truoc N
```

Mỗi lần gọi chụp câu trả lời thứ N+1 trở đi MỘT lần (cách nhau bằng độ trễ của lần gọi công cụ, 1–3 s)
và trả `{xong, giong, khoang_ms, sha256, dang_nghi, dai16, …}`. **Xong = 3 lần chụp liên tiếp cùng
sha256, lần đầu cách lần cuối ≥ 2 giây, VÀ khung câu trả lời có nút sao chép** (`co_nut_sao_chep`); bộ đếm nằm trong trang (`window.__chupSoTay`), đổi nội dung
hay gặp dòng trạng thái kiểu *"Analyzing the documents...\nexpand_more"* là đếm lại từ 1. Câu trả lời
thật bắt đầu `Thoughts\nexpand_more\n`. Đo 30/10/2026 (BƯỚC 245): xong sau ~105 s. Điều kiện nút sao chép: leader thấy ba nút (*Sao chép câu trả lời của mô hình vào bảng nhớ tạm* ·
*Đánh giá câu trả lời là tốt/không tốt* · *Lưu tin nhắn vào ghi chú*) CÓ MẶT trong `.to-user-container` cuối
LÚC XONG (30/10/2026); sự VẮNG MẶT của chúng trong lúc đang phát CHƯA được chụp. Nên điều kiện này chỉ
làm `xong` đến muộn hơn, không chứng minh một bản phát dở thiếu nút. Chốt chặn chính vẫn là ba lần chụp
cùng sha256: lượt nghiệm thu BƯỚC 246 có một ảnh chụp 253 ký tự của bản phát dở đã qua phép thử
"không đang nghĩ" (`dang_nghi: false`, `giong: 1`), và chỉ không bị nhận nhầm vì lần chụp kế đổi sha256.
Nếu một khung ẩn dừng cập nhật DOM giữa chừng thì bản phát dở có thể trông như đã xong. Chỉ khi
`xong: true` lệnh mới trả thêm `text`, `trich_dan: [{n, nguon}]` (đọc thẳng từ
`button.citation-marker span[aria-label="<n>: <nhãn nguồn>"]`, số lặp liệt kê đúng như trang) và
`vo_hinh` (vị trí và mã của tab, ký tự rộng-không và ký tự điều khiển, để dựng lại tệp đúng từng byte).

## Chặng 7 — Lưu CÓ BẮT TAY

Leader lưu hai tệp ngoài repo: `text` đúng từng byte (UTF-8, xuống dòng LF) và `trich_dan` mỗi dòng
`<n>: <nhãn>`. Trang tính SHA-256 của `innerText`; máy tính SHA-256 của tệp; lệch thì **từ chối**:

```bash
./.venv/Scripts/python.exe tools/so_tay.py kiem-tra-loi <tệp trả lời> --sha256 <sha256 trang trả>
```

Mã thoát 0 khớp · 1 lệch (in cả hai băm) · 2 không đọc được tệp. Lý do: chép tay một câu trả lời
dài làm rơi ký tự VÔ HÌNH (`\t` + U+200B trong công thức toán, 30/10/2026) mà chữ nhìn vẫn y hệt.
Lệch thì dựng lại tệp từ `text` KHÔNG qua gõ tay, đừng "sửa cho khớp". Đừng đọc câu trả lời để làm
phát hiện từ tệp chưa khớp.

## Chặng 8 — Tự kiểm, CẢ hai chiều

- **Mỗi phát hiện: mở file ra đối chiếu** (`sed -n`/`grep -n`). Sổ tay từng
  trích đúng chữ nhưng SAI TÊN FILE (BƯỚC 119). `trich_dan` cho biết nó TRÍCH từ nguồn nào, không
  cho biết câu ấy còn đúng.
- **Câu ÂM cũng phải kiểm** — *"không tìm thấy"* đã sai nhiều lần (hai ca đầu 24/09,
  BƯỚC 127). `grep` các từ khoá của chính các ví dụ trên tài liệu sống, và
  quét **nhiều dòng** khi cụm từ có thể bị ngắt dòng (BƯỚC 128: ba trên sáu
  câu lọt `grep` một dòng).
- Một dấu ở cấp MỤC không phủ từng câu trong mục (24/09).
- Đối chiếu trích dẫn bằng dụng cụ: `./.venv/Scripts/python.exe tools/doi_chieu_trich_dan.py "<trích dẫn>"`.

## Chặng 9 — Ghi sổ bằng MÁY

Viết mục ra một tệp JSON trong thư mục nháp (NGOÀI repo), rồi:

```bash
./.venv/Scripts/python.exe tools/so_tay.py ghi <tệp JSON ấy>
```

```json
{"buoc": "BƯỚC n", "cau_hoi": "<NGUYÊN VĂN câu đã gửi>",
 "nhan_nguon_tep": "<tệp nhãn của Chặng 2>",
 "tra_loi_tep": "<tệp trả lời>", "tra_loi_sha256": "<sha256 trang trả>", "trich_dan_tep": "<tệp trích dẫn>",
 "phat_hien": [{"noi_dung": "...", "tu_kiem": "<LỆNH đã chạy -> kết quả>", "phan_quyet": "THẬT. ..."}]}
```

hoặc `"khong_tim_thay_gi": true` kèm `"_tu_kiem_cau_am": "<LỆNH grep -> kết quả>"`.
`phan_quyet` mở đầu bằng `THẬT` · `SAI` · `CHƯA KIỂM ĐƯỢC` — **không phải
"ĐÚNG"** (BƯỚC 129 đỏ vì đúng chữ ấy). Công cụ từ chối và **không chạm file**
nếu sai khuôn; gác `tests/test_soat_notebooklm.py` vẫn là cửa cuối.

Ba ô mới (đều tuỳ chọn; mục cũ vẫn hợp lệ):
- `tra_loi_tep` + `tra_loi_sha256` + `trich_dan_tep` — khai đủ cả ba hoặc không ô nào. `ghi` chạy
  lại bắt tay; khớp thì mục mang `tra_loi: {sha256, dai16, trich_dan: [{n, nguon}]}` như DỮ LIỆU
  (đường dẫn tạm không vào sổ; chính câu trả lời không vào sổ, chỉ băm của nó).
- `nhan_nguon_tep` — sinh `nguon` (đúng nhãn trang hiện) và `_do_tuoi` (dòng `--tom-tat`), so với `HEAD`
  hoặc với `nhan_nguon_so_voi` (ví dụ `origin/main`: nguồn của sổ tay nên phản chiếu `main`).

## Nạp lại nguồn — khi `do-tuoi` báo CU hoặc THIEU

Nguồn là bản chụp. Ghi `_do_tuoi` vào mục sổ khi không nạp lại (Chặng 2 sinh sẵn). Nạp lại —
**THÊM TRƯỚC, XOÁ SAU** (`SKILL.md`, mục *CÁCH LÀM TƯƠI*; lý do đo 17/09: xoá
trước có một cửa sổ sổ rỗng, và bản trùng gỡ được còn sổ rỗng thì không):

1. Tab **Nguồn** (giao diện hẹp chỉ có danh sách nguồn trong DOM khi tab ấy
   đang chọn — đọc ra 0 nguồn ở tab khác là MẪU hỏng, không phải sổ rỗng).
   Ghi lại nhãn của mọi nguồn đang có (`lay-nhan`).
2. **Thêm nguồn** → **Trang web** → ô `textarea` *"Nhập URL"* nhận nhiều URL,
   mỗi dòng một URL (repo công khai), **ghim mã băm commit**, không `main`:
   `https://raw.githubusercontent.com/Siner0808/vibe-stock-analysis/<mã băm đủ 40 ký tự>/<file>`
   Đo trước bằng `curl -w '%{http_code} %{size_download}'` so với
   `git show <mã băm>:<file> | wc -c` — 28/09: 11/11 trả 200, khớp từng byte.
   Ghim băm tránh CDN chậm một commit sau merge, và làm bản mới khác bản cũ
   ngay trên nhãn.

   **RIÊNG `docs/STATE.md`: DÁN thành khúc, KHÔNG nạp URL** (BƯỚC 202, 16/10/2026,
   người dùng chọn *"Dán 3 phần, repo giữ nguyên"*). Nạp bằng URL thì bộ nạp lưu
   ĐỦ tệp — trình xem nguồn hiện tới BƯỚC cuối — nhưng MÔ HÌNH chỉ đọc được một
   khúc đầu: @3c2fd2c (1.616.807 byte) dừng giữa câu ở ký tự ~352.490, nạp lại
   dừng đúng chỗ ấy; từ 1.583.623 byte trở lên 8/9 lượt nạp cụt. Cách làm:
   - `./.venv/Scripts/python.exe tools/so_tay.py chia-state --bam <mã băm> --js`
     in lệnh JS: tải tệp ở ĐÚNG commit, kiểm số byte, cắt sẵn tại dòng
     `## BƯỚC n` thành khúc ≤ `CO_PHAN_TOI_DA` ký tự (`window.__phanState`).
     Bỏ `--js` thì in nhãn và cỡ từng khúc.
   - Mỗi khúc: **Thêm nguồn** → **Văn bản đã sao chép** → ô `textarea`
     *"Văn bản được dán"* (setter gốc + sự kiện `input`; ô nhận tối đa ĐÚNG
     500.000 ký tự, quá là nút **Chèn** khoá) → **Chèn** → đổi tên đúng nhãn
     lệnh in ra (`STATE.md @<băm> phanK/N (BUOC a-b)`).
   - Làm tươi: dán ĐỦ các khúc của commit mới, đo từng khúc (bước 5), rồi mới
     xoá MỌI khúc cũ — nhãn mang băm nên không lẫn hai đời.
3. **Xoá bản cũ** — chỉ những bản vừa có bản thay ở bước 2 (không phải hỏi;
   xoá nguồn nào khác thì HỎI người dùng). Menu *"Tuỳ chọn khác"* → **Xoá
   nguồn**; đọc **nhãn** trên hộp xác nhận (`Xoá <nhãn>?`) rồi mới bấm. Bấm
   bằng `.click()` trong JS và lọc theo độ hiện — dialog cũ còn sót
   trong DOM, bấm theo toạ độ rơi vào lớp vô hình.
4. **Đổi tên nguồn** thành `<file> @<7 ký tự băm>` — mặc định nhãn là URL
   đầy đủ; giữ băm ngắn thì độ tươi đọc được ngay trên nhãn. Ô tên nhận giá
   trị qua setter gốc + sự kiện `input`, rồi bấm **Lưu**. Tìm nút menu
   bằng ô chọn của CHÍNH nguồn ấy (`closest('.single-source-container')`, nút
   `aria-label="Tuỳ chọn khác"`), đọc lại tên cũ trong ô trước khi Lưu, đếm
   lại danh sách sau khi đổi — leo cây DOM tìm `more_vert` từng đổi nhầm tên
   `SKILL.md` (lỗi 180).
5. **Đo lại bằng nhãn** (`lay-nhan` rồi `do-tuoi`: mọi nguồn `TUOI`, không `THIEU`) **và đo độ đọc
   TRỌN của mô hình**, việc nhãn không đo được: với từng khúc `docs/STATE.md` hỏi câu chứa HAI cụm
   chỉ có trong ~150 ký tự cuối của khúc, kèm câu đứng ngay trước nó. Đừng hỏi *"hai câu cuối"*
   (16/10: sổ trả một gạch đầu dòng cách cuối 3.923 ký tự dù vẫn nhìn tới cuối), cũng đừng hỏi
   *"số BƯỚC lớn nhất"* của khúc (tiêu đề không theo thứ tự số: 152 đứng sau 153). Các câu đo này
   làm bẩn nhật ký chat: xoá nó (Chặng 3) trước câu hỏi thật.

> ⚠️ **15/10/2026 (BƯỚC 196, lỗi 179): làm bước 5 TRÊN BẢN MỚI TRƯỚC bước 3.**
> Một lượt nạp có thể bị CẮT CỤT mà không báo lỗi: `docs/STATE.md` @9ec0556
> (1.583.623 byte) nạp HAI lần đều dừng ở BƯỚC 122 — sổ không thấy BƯỚC 123,
> 160, 190 — trong khi @3194422 (1.571.526 byte) nạp cùng ngày đọc tới BƯỚC 193.
> Nguyên nhân chưa rõ (kích thước gần như nhau). ⚠️ HẾT ĐÚNG 16/10/2026 (BƯỚC 202):
> đã đo — bộ nạp lưu ĐỦ, cái cụt là góc nhìn của MÔ HÌNH lúc trả lời; `docs/STATE.md`
> nay DÁN thành khúc (bước 2). Thứ tự an toàn: thêm (2) → đổi
> tên (4) → đo bản MỚI (5) → mới xoá bản cũ (3). Hỏi thẳng tiêu đề BƯỚC
> cuối (`'## BƯỚC n'` có hay không) để phân biệt cắt cụt với đọc sót; bản mới
> cụt thì giữ bản cũ và khai độ chậm ở `_do_tuoi`.

> 🔴 **Bản 27/09 (BƯỚC 130) của mục này ghi XOÁ trước, THÊM sau** — ngược thứ
> tự `SKILL.md` đã chốt từ 17/09, và ngược cả luật xoá nguồn: xoá một nguồn
> CHƯA có bản thay là việc phải hỏi người dùng. Hôm ấy người dùng đã cho phép
> nên không có hậu quả; sửa ở BƯỚC 137 (28/09/2026).

Không có `input[type=file]` (đo 08/09): "Tải tệp lên" mở hộp thoại hệ điều
hành, không điều khiển được. Đường nạp là URL — trừ `docs/STATE.md`, DÁN thành
khúc (bước 2, BƯỚC 202).

## Phiên đám mây — không mở được sổ tay, không hỏi được leader

Phiên đám mây không có trình duyệt tới NotebookLM, và leader không nhắn lại được trong
lúc phiên chạy: mọi báo cáo nằm trong thân PR. Câu *"phải hỏi mà không hỏi được thì BÁO
người dùng"* (mục *Không làm* dưới đây) nghĩa là:

1. Hỏi máy BƯỚC có chạm luật không (lệnh `tools/buoc_cham_luat.py` ở đầu file, dùng python của venv).
2. **Không chạm** → ghi một dòng `khong_bat_buoc_vi` bằng `tools/so_tay.py ghi` như thường.
3. **Chạm** (ví dụ BƯỚC sửa `SKILL.md`) → KHÔNG tự bịa mục sổ và KHÔNG ghi
   `docs/soat-notebooklm.json`. Dựng câu hỏi bằng MÁY:

   ```bash
   /tmp/venv_ci/bin/python tools/so_tay.py hoi --buoc "BƯỚC n" --ket-luan "<kết luận sắp viết>" --vi-du "<câu nghi ngờ>"
   ```

   Dán nguyên văn vào thân PR, dưới tiêu đề **"Câu hỏi sổ tay chờ leader"**. Mở PR ở dạng
   **DRAFT** và gọi tên cổng đỏ chờ: `test_TU_MOC_BAT_BUOC_moi_BUOC_deu_phai_HOI_THAT`.
   Leader hỏi, ghi mục sổ, và đẩy vào chính nhánh.
4. Mọi cổng khác phải xanh. Đỏ này là đỏ CHỜ, khác đỏ MÔI TRƯỜNG
   (`references/cong-thuc-chay.md`, mục *Phiên đám mây*).

Chứng cứ: BƯỚC 164 (Quy tắc 3 thu hẹp, máy phán bằng git) và phiếu giao BƯỚC 183.

## Công cụ khác đã cân nhắc

`notebooklm-py` (CLI không chính thức điều khiển NotebookLM): **chờ người dùng tạo tài khoản
riêng**; nếu dùng thì là CLI trong môi trường tách biệt, **không MCP**, không dependency của repo.
Chưa dùng, chưa cài (người dùng chọn *"A ngay, thử notebooklm-py sau bằng tài khoản riêng
(Recommended)"*, 29/10/2026).

## Không làm

- Không mở Chrome, không dùng `claude-in-chrome` trừ khi người dùng nói thẳng.
- Không chép một phát hiện vào tài liệu khi chưa mở file đối chiếu.
- Không xoá nguồn hay sổ tay bằng quyền ở Chặng 3 — quyền ấy chỉ phủ nhật ký trò chuyện.
- Không dùng `khong_soat_vi` cho một BƯỚC — ô ấy đóng từ BƯỚC 108 và KHÔNG
  mở lại ở BƯỚC 164. Phải hỏi mà không hỏi được thì **BÁO người dùng**, không
  ghi ô thoát. `khong_bat_buoc_vi` là ô khác: chỉ cho BƯỚC mà máy xác nhận không
  phải hỏi (Bước 0 ở đầu file).
