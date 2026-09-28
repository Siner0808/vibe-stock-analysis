# Soát chéo bằng sổ tay NotebookLM — CÁCH LÀM

Tài liệu tham khảo của skill `quy-trinh-lam-viec`, không phải skill riêng:
dự án cố ý giữ **một** skill (`tests/test_skill_quy_trinh.py::test_CHI_CO_MOT_skill_quy_trinh`).
Đọc nó mỗi lần làm Quy tắc 3.

Mỗi BƯỚC phải qua sổ tay (người dùng chốt 18/09/2026). File này là
**cách làm**; luật và lý do nằm ở `SKILL.md` — Quy tắc 3 và mục *Luồng
thông tin thứ hai — NotebookLM*.
Mọi dòng dưới đây đến từ một lượt đã hỏng thật.

Sổ tay chỉ đọc **TÀI LIỆU**, không đọc mã, và nguồn của nó là **bản chụp**
lúc nạp. Nó là một luồng đọc độc lập, không phải trọng tài.

---

## Chặng 1 — Mở sổ (trình duyệt TRONG Claude Code, KHÔNG Chrome)

Người dùng chốt 24/09: `mcp__Claude_Browser__*`, không mở Chrome (RAM).

```
navigate  https://notebook.google.com/notebook/039ade07-6eeb-4863-b892-1b920e9a94bf
```

Đọc `location.host` bằng `javascript_tool`:

- `accounts.google.com` → **nhờ người dùng đăng nhập** trong khung ấy rồi
  làm việc khác trong lúc chờ. Đăng nhập KHÔNG sống qua phiên mới hay khi
  khung bị đóng (đo 25/09, 27/09). **Không bao giờ tự nhập mật khẩu.**
- `notebook.google.com` → tiếp.

## Chặng 2 — Dựng câu hỏi bằng MÁY, không gõ tay

```bash
./.venv/Scripts/python.exe tools/so_tay.py hoi --buoc "BƯỚC n" \
    --ket-luan "<kết luận SẮP VIẾT, cụ thể, có tên file/hàm/con số>" \
    --vi-du "<các câu nghi ngờ, viết một chuỗi: a statement that ..., or that ...>"
```

Nó đóng khuôn bốn chỗ đã hỏng: **một dòng** (Enter trong ô chat là GỬI),
**lối thoát** nguyên văn (thiếu thì sổ tay BỊA — BƯỚC 107), **miễn trừ câu
đã có dấu** 🔴/*HẾT ĐÚNG* (thiếu thì hàng chục mâu thuẫn giả), **đòi trả lời
tiếng Việt** (câu hỏi tiếng Anh — chốt 17/09).

**Hỏi về MỘT KẾT LUẬN CỤ THỂ, kèm VÍ DỤ câu nghi ngờ.** Câu hỏi rộng
(*"câu nào bị câu khác nói ngược"*) trả *"không tìm thấy"* SAI (25/09); câu
hỏi cụ thể trả 4/4 trích dẫn khớp. Và hỏi *"có chỗ nào NÓI NGƯỢC kết luận
tôi sắp viết"*, đừng hỏi *"tài liệu nói gì về MÃ của tôi"* — nó không thấy mã.

## Chặng 3 — Gửi

```
find  "Đặt câu hỏi hoặc tạo nội dung"      -> ref của ô chat
computer left_click ref · type <câu hỏi> · key Return      (browser_batch)
```

`textarea` **đầu tiên** của trang là ô *"Tìm nguồn mới trên web"* — gõ nhầm
rồi Enter sẽ đi tìm nguồn. Luôn chọn theo placeholder.

## Chặng 4 — Đọc trả lời

`javascript_tool` chết ở **45 giây**: mỗi lượt chờ ≤ 25 s, gọi lại nhiều lần.

```js
const all = [...document.querySelectorAll('.individual-message')];
all.slice(-2).map(e => e.innerText.slice(0, 5000))
```

Phần tử áp chót phải là **đúng câu vừa gửi** — lịch sử chat còn sau khi
đăng nhập lại, nên phần tử cuối có thể là câu trả lời CŨ. Còn chữ
*"Thoughts…"* / *"Investigating…"* mà chưa có đoạn trả lời là chưa xong.

## Chặng 5 — Tự kiểm, CẢ hai chiều

- **Mỗi phát hiện: mở file ra đối chiếu** (`sed -n`/`grep -n`). Sổ tay từng
  trích đúng chữ nhưng SAI TÊN FILE (BƯỚC 119).
- **Câu ÂM cũng phải kiểm** — *"không tìm thấy"* từng sai hai lần (24/09,
  BƯỚC 127). `grep` các từ khoá của chính các ví dụ trên tài liệu sống, và
  quét **nhiều dòng** khi cụm từ có thể bị ngắt dòng (BƯỚC 128: ba trên sáu
  câu lọt `grep` một dòng).
- Một dấu ở cấp MỤC không phủ từng câu trong mục (24/09).

## Chặng 6 — Ghi sổ bằng MÁY

Viết mục ra một tệp JSON trong thư mục nháp (NGOÀI repo), rồi:

```bash
./.venv/Scripts/python.exe tools/so_tay.py ghi <tệp JSON ấy>
```

```json
{"buoc": "BƯỚC n", "cau_hoi": "<NGUYÊN VĂN câu đã gửi>",
 "phat_hien": [{"noi_dung": "...", "tu_kiem": "<LỆNH đã chạy -> kết quả>", "phan_quyet": "THẬT. ..."}]}
```

hoặc `"khong_tim_thay_gi": true` kèm `"_tu_kiem_cau_am": "<LỆNH grep -> kết quả>"`.
`phan_quyet` mở đầu bằng `THẬT` · `SAI` · `CHƯA KIỂM ĐƯỢC` — **không phải
"ĐÚNG"** (BƯỚC 129 đỏ vì đúng chữ ấy). Công cụ từ chối và **không chạm file**
nếu sai khuôn; gác `tests/test_soat_notebooklm.py` vẫn là cửa cuối.

## Nạp lại nguồn — khi sổ cũ hơn `main`

Nguồn là bản chụp. Ghi `_do_tuoi` vào mục sổ khi không nạp lại. Nạp lại —
**THÊM TRƯỚC, XOÁ SAU** (`SKILL.md`, mục *CÁCH LÀM TƯƠI*; lý do đo 17/09: xoá
trước có một cửa sổ sổ rỗng, và bản trùng gỡ được còn sổ rỗng thì không):

1. Tab **Nguồn** (giao diện hẹp chỉ có danh sách nguồn trong DOM khi tab ấy
   đang chọn — đọc ra 0 nguồn ở tab khác là MẪU hỏng, không phải sổ rỗng).
   Ghi lại nhãn của mọi nguồn đang có.
2. **Thêm nguồn** → **Trang web** → ô `textarea` *"Nhập URL"* nhận nhiều URL,
   mỗi dòng một URL (repo công khai), **ghim mã băm commit**, không `main`:
   `https://raw.githubusercontent.com/Siner0808/vibe-stock-analysis/<mã băm đủ 40 ký tự>/<file>`
   Đo trước bằng `curl -w '%{http_code} %{size_download}'` so với
   `git show <mã băm>:<file> | wc -c` — 28/09: 11/11 trả 200, khớp từng byte.
   Ghim băm tránh CDN chậm một commit sau merge, và làm bản mới khác bản cũ
   ngay trên nhãn.
3. **Xoá bản cũ** — chỉ những bản vừa có bản thay ở bước 2 (không phải hỏi;
   xoá nguồn nào khác thì HỎI người dùng). Menu *"Tuỳ chọn khác"* → **Xoá
   nguồn**; đọc **nhãn** trên hộp xác nhận (`Xoá <nhãn>?`) rồi mới bấm. Bấm
   bằng `.click()` trong JS và lọc `offsetParent !== null` — dialog cũ còn sót
   trong DOM, bấm theo toạ độ rơi vào lớp vô hình.
4. **Đổi tên nguồn** thành `<file> @<7 ký tự băm>` — mặc định nhãn là URL
   đầy đủ; giữ băm ngắn thì độ tươi đọc được ngay trên nhãn. Ô tên nhận giá
   trị qua setter gốc + sự kiện `input`, rồi bấm **Lưu**.
5. **Đo độ tươi**: hỏi số BƯỚC lớn nhất trong `docs/STATE.md` kèm lối thoát,
   so với `git show <mã băm>:docs/STATE.md | grep '^## BƯỚC' | tail -1`.

> 🔴 **Bản 27/09 (BƯỚC 130) của mục này ghi XOÁ trước, THÊM sau** — ngược thứ
> tự `SKILL.md` đã chốt từ 17/09, và ngược cả luật xoá nguồn: xoá một nguồn
> CHƯA có bản thay là việc phải hỏi người dùng. Hôm ấy người dùng đã cho phép
> nên không có hậu quả; sửa ở BƯỚC 137 (28/09/2026).

Không có `input[type=file]` (đo 08/09): "Tải tệp lên" mở hộp thoại hệ điều
hành, không điều khiển được. Đường nạp là URL.

## Không làm

- Không mở Chrome, không dùng `claude-in-chrome` trừ khi người dùng nói thẳng.
- Không chép một phát hiện vào tài liệu khi chưa mở file đối chiếu.
- Không dùng `khong_soat_vi` cho một BƯỚC — ô ấy đóng từ BƯỚC 108.
  Không hỏi được thì **BÁO người dùng**, không ghi ô thoát.
