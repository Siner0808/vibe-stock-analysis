---
name: quy-trinh-lam-viec
description: Quy trinh bat buoc cho MOI viec trong du an vibe_preview - doc, sua, them test, them gac, do luong, chay, commit, bao cao. Dung NGAY khi bat dau bat cu viec gi trong repo nay, truoc khi doc hay sua file dau tien, va moi lan quay lai sau khi bi ngat. Cung dung khi sap sua thu anh huong toi KET QUA DO (diem so, co vi the, chi phi, nguong, cong an toan, backtest, walk-forward), khi mot con so dep len sau thay doi, khi viet mot gac moi, khi va nhieu cho trong mot file, hoac khi can chay bo test va cho ket qua.
---

# Quy trình làm việc — vibe_preview

Dự án này đã **năm lần** cho ra con số đẹp mà sau đó hoá ra vô nghĩa, và
ngày 07/09/2026 một lượt rà lại **một phiên duy nhất** đếm được **11 lỗi
quy trình**. Không lỗi nào là lỗi suy nghĩ; tất cả là lỗi thao tác lặp
lại. File này là thứ còn lại sau cả hai.

**Quy tắc số 1 — nếu một thay đổi làm con số đẹp lên đáng kể, giả định
đầu tiên phải là CÓ LỖI.** Số xấu đi là chiều an toàn.

**Quy tắc số 2 — không có lệnh thì không có số.** Mọi con số viết vào tài
liệu, báo cáo hay commit phải được tính TRONG PHIÊN NÀY, kèm lệnh tái lập
được. Ước lượng thì phải gọi nó là ước lượng. Ngày 07/09/2026 tôi suýt
ghi "≈40s" cho một thứ đo được là **167,7s** — sai hơn bốn lần, và sai
theo chiều làm việc mình vừa làm trông rẻ hơn thực tế.

---

## Bước 0 — Mở phiên (30 giây, không được bỏ)

```bash
git -C <repo> status --short && git -C <repo> branch --show-current
ls <repo>/.claude/skills/            # quy trinh nao dang co san
```

Đọc, bằng tool Read (hook `tools/cua_doc_bat_buoc.py` chỉ đếm Read):
`docs/HANDOFF.md` → `docs/STATE.md` (mục cuối) → `NGUYEN-TAC-DO-LUONG.md`
→ `MO-XE-KIEN-TRUC.md`.

Rồi liệt kê **thứ đang bị chặn theo ngày** và không đọc sớm.

> Ngày 07/09/2026 tôi làm việc nửa buổi rồi mới biết dự án có skill quy
> trình — hệ thống tự hiện nó ra giữa chừng.
>
> **Tưởng đã thành cơ chế, nhưng chưa.** `tools/cua_mo_phien.py` được
> đăng ký làm hook `SessionStart` ngày 07/09/2026 — và tới 08/09/2026 đo
> ra là **nó chưa bao giờ chạy**, cùng năm cửa còn lại. Xem
> `references/loi-da-mac.md` lỗi 14.
>
> Viết "Bước 0: đi tìm skill" vào chính skill là một vòng tròn — phải đọc
> skill mới biết phải đi tìm skill. Vòng tròn ấy hiện được cắt ở
> `~/.claude/rules/ecc/common/vibe-preview.md`, file nạp vào **mọi** phiên
> bất kể mở ở đâu.

---

## Bước 1 — Trước khi viết, và trước khi nói KHÔNG LÀM ĐƯỢC

**Điều 1 — tìm xem đã có lời giải chưa.**

```bash
grep -rn "<khai niem>" tests/ tools/ --include=*.py | head -20
```

**Hai lần trong ba ngày** (05/09 và 07/09) lời giải nằm sẵn trong
`tests/test_c5_noi_that.py`, kèm docstring nói thẳng lý do, và tôi vẫn
tự viết lại từ đầu. Chép lời giải ra chỗ mới thì rẻ; đọc trước khi viết
mới là thứ khó.

**Điều 2 — một câu "không làm được" chép từ ghi chú thì phải ĐO LẠI,
hoặc nói rõ nó chưa được kiểm trong phiên này.**

Và khi viết ra một câu như thế, **nêu ĐƯỜNG đã thử, đừng nêu MỤC TIÊU**:

| Viết thế này | Không viết thế này |
|---|---|
| "`file_upload` không dùng được vì trang không có ô nhập file" | "không nạp được nguồn" |
| "cửa Bash không chạy vì phiên mở ngoài repo" | "hook của dự án hỏng" |

Câu bên trái đúng mãi mãi. Câu bên phải sai ngay khi có đường thứ hai —
và ngày 08/09/2026 nó sống **ba ngày** trước khi người dùng hỏi lại.
`references/loi-da-mac.md` lỗi 16.

---

## Bước 2 — Sửa: MỘT đường duy nhất

```python
import sys; sys.path.insert(0, "tools")
from va_an_toan import thay, dot_bien

thay("paper_metrics.py", "N_TOI_THIEU = 113", "N_TOI_THIEU = 120")
```

`tools/va_an_toan.py` đọc/ghi ở **chế độ văn bản**, neo viết bằng `\n`
bình thường và khớp trên mọi file, neo phải khớp **đúng một lần** hoặc
nổ, ghi qua file tạm rồi đổi tên.

**KHÔNG tự viết neo theo byte.** Ngày 07/09/2026, 5 trong 11 lỗi đến từ
đúng chỗ đó: neo `\n` trên file CRLF (3 lần), neo `\r\n` trên file LF (1
lần), tiếng Việt trong `b"..."` (1 lần).

> ### Một luật cũ ĐÃ BỊ BÁC — đừng làm theo bản cũ
>
> `CLAUDE.md` và skill trước từng ghi *"repo dùng CRLF, phải giữ CRLF"*.
> Đo 07/09/2026:
>
> ```
> trong INDEX (thu that duoc commit) : 412/412 file text la LF thuan
> trong working copy                 : 370 CRLF · 41 LF · 1 tron lan
> core.autocrlf = true, khong .gitattributes
> ```
>
> Git quy đổi cả hai chiều. **Quy ước xuống dòng của bản trên đĩa không
> ảnh hưởng tới thứ được commit.** Luật cũ không chỉ thừa — nó là nguyên
> nhân của 5 lỗi kể trên, vì nó đẩy người ta sang thao tác byte.

**Suy ra, đừng gõ.** Một ngưỡng gõ tay ở hai chỗ sẽ trôi ra khỏi nhau.

---

## Bước 3 — Đột biến mọi gác mới. VÒNG LẶP, không phải một lượt

```python
dot_bien("paper_metrics.py", "z=2,30", "z=1,00",
         ["-m", "pytest", "tests/test_dieu_kien_dung_alpha.py", "-q"])
```

**Lặp cho tới khi MỌI đột biến đều đỏ.** Một phát sống sót không phải
"gần đạt" — nó là câu trả lời: gác chưa canh chỗ đó. Sửa gác rồi chạy
lại cả bộ đột biến, đừng chỉ chạy lại phát vừa hỏng.

Ba điều bắt buộc, cả ba từ sự cố thật:

1. **Phép đục phải đi qua đúng HÀM ĐANG PHÁN**, không qua hàm trích.
2. **Phát đầu tiên phải là: dựng lại nguyên văn lỗi thật.** Đó là câu hỏi
   duy nhất đáng hỏi — *gác có bắt được đúng thứ nó sinh ra để bắt không.*
3. **Gác một phép SUY RA thì kiểm HÌNH DẠNG biểu thức bằng AST**, không
   kiểm giá trị nó cho ra.

Ba mẫu hay sống sót nhất, và bốn cái bẫy khác: `references/bay.md`.

---

## Bước 4 — Năm cổng gác, ĐÚNG THỨ TỰ, KHÔNG song song

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/kq.log 2>&1
./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py
./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo
./.venv/Scripts/python.exe tools/kiem_test_chay_rieng.py --im
./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py
```

> **Cổng thứ năm thêm ngày 10/09/2026, và nó khác bốn cổng kia về
> LOẠI.** Bốn cổng đầu đo thứ **đang có**: test còn lại xanh không, cú
> pháp nạp được không, có mẫu bịa số không, file chạy riêng có xanh
> không. **Không cổng nào so với thứ ĐÃ TỪNG CÓ.**
>
> Ngày 09/09/2026 một lệnh `cat >` đè mất 40 phép kiểm đã có. Cả bốn
> cổng đều XANH. Thứ duy nhất bắt được là một con số đọc bằng mắt: 834
> thay vì 874. Cổng thứ năm là cổng đầu tiên của dự án đo thứ **BỊ MẤT**.
>
> Nó **không cấm giảm** — gộp hai test trùng là dọn dẹp hợp lệ. Nó buộc
> khai lý do, đúng cơ chế `# bia-ok:`:
>
> ```bash
> ./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py --cap-nhat
> ./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py --cap-nhat --ly-do "<vi sao>"
> ```
>
> **Thêm test cũng phải cập nhật mốc.** Không phải khắt khe thừa: mốc
> trôi tụt lại phía sau thì lỗ hổng đúng bằng khoảng cách đó, và nó lớn
> dần mà không ai thấy. Lý do khai vào `docs/moc_so_test.json` và nằm
> trong diff.

Vài test ghi thư mục tạm vào gốc repo → chạy song song cho **đỏ giả**.

> **Sửa `SKILL.md` hay `references/` thì chạy MỘT file này TRƯỚC:**
>
> ```bash
> ./.venv/Scripts/python.exe -m pytest tests/test_skill_quy_trinh.py -q
> ```
>
> **11 giây**, và nó bắt đúng thứ hay sai nhất: **tên file viết TRẦN,
> thiếu tiền tố thư mục** — git không biết cái tên ấy nên nó là một lời
> hứa về thành phần không có. Ngày 08/09/2026 tôi trả giá **ba lượt cổng
> đầy đủ, mỗi lượt ~9 phút** cho đúng lỗi ấy, ba lần trong một ngày.
>
> **KHÔNG viết tên file trần ra đây làm ví dụ** — lượt thứ ba đỏ đúng vì
> ghi chú cảnh báo lỗi ấy tự chứa nó.
>
> **Và ĐỪNG nối phép kiểm này bằng `| tail`.** Mã thoát của một ống là mã
> thoát của lệnh CUỐI, tức `tail`, tức luôn 0 — `&&` sau đó đi tiếp dù
> pytest đỏ. Luật `pytest-qua-ong` của cửa Bash sinh ra vì `tail` ĐỆM
> output; đây là mặt thứ hai của nó, và mặt này im lặng hơn.

Mã thoát **2** của cổng 2 và 4 nghĩa là *chưa kiểm được*, **không** phải
sạch.

Cách chạy và chờ: `references/cong-thuc-chay.md`. Tóm tắt ba dòng:

- `PYTHONIOENCODING=utf-8` cho mọi lệnh có tiếng Việt.
- **Ghi ra file log, đừng pipe qua `tail`.** `tail` đệm hết output tới
  lúc ống đóng; với lượt chạy nền thì bạn không đọc được gì.
- **Đừng sửa file khi một lượt chạy đang bay.** Nếu lỡ, chạy lại đúng
  những file đọc file vừa sửa.

---

## Bước 5 — Giao

- **KHÔNG đẩy thẳng `main`** — nhưng KHÔNG phải vì `main` bị khoá.
  Đo 08/09/2026: `gh api repos/.../branches/main/protection` trả **404
  "Branch not protected"**. Lý do thật nằm ở chỗ khác:
  `.github/workflows/kiem-dinh.yml` chạy trên **cả `push` lẫn
  `pull_request`**, nên đẩy
  thẳng thì CI chạy SAU khi mã đã nằm trên `main` — một cái cổng chạy
  sau cánh cửa. Đi qua PR thì nó chạy TRƯỚC.

- **Tự merge được, và từ 08/09/2026 thì tự merge** — người dùng đã
  quyết. Nhưng chỉ khi **đủ cả ba**:

  1. Bốn cổng ở Bước 4 xanh tại máy.
  2. **MỌI** check của PR là `pass`. Không `pending`, không `fail`.
  3. Không còn câu hỏi nào đang chờ người dùng quyết.

  ```bash
  gh pr checks <so>          # doc HET, dung doc dong dau
  gh pr merge <so> --merge --delete-branch
  gh pr view <so> --json state,mergeCommit
  ```

  > **Cái bẫy của điều 2.** `kiem-dinh` hiện **HAI dòng** cho mỗi PR —
  > một từ `push`, một từ `pull_request`. Ngày 08/09/2026 dòng đầu đã
  > `pass` trong khi dòng sau còn `pending`. Đọc một dòng rồi merge là
  > merge khi CI chưa xong.

- **Merge xong phải KIỂM, không tin mã thoát:** `pr view` cho
  `state=MERGED` và mã băm hợp nhất, rồi `git pull` + `git branch -a`
  + tìm nội dung vừa thêm trong `main`.

- **Hai lý do CŨ của luật này đều đã bị BÁC**, đừng chép lại chúng:
  *"`gh` không cài trên máy này"* (nay có, 2.100.0, đã đăng nhập) và
  *"`main` có branch protection"* (404). `references/loi-da-mac.md`
  lỗi 17.
- Commit body **ASCII**, không `Co-Authored-By`.
- Ghi vào `docs/STATE.md` cả **kết quả lẫn giả thuyết đã bị bác**, và cả
  **ước lượng đã sai**. Giả thuyết sai nghe hợp lý là thứ đáng giữ nhất.

---

## Bước 6 — Cập nhật chính file này (bắt buộc, không phải tuỳ)

Mỗi lỗi mới → thêm một dòng vào `references/loi-da-mac.md`, rồi hỏi:
**máy chặn được không?** Chặn được thì thêm luật vào
`tools/cua_bash_an_toan.LUAT` hoặc một cổng mới, kèm test.

Luật mới phải **khai nguồn**: ngày sự cố, hoặc dấu `CHƯA CÓ SỰ CỐ` kèm
tên file quy ước. `tests/test_cua_quy_trinh.py::test_moi_luat_deu_khai_NGUON`
bắt điều đó — và ở lượt chạy đầu tiên nó bắt **4/8 luật của chính tác giả
nó**, cả bốn viết quy ước bằng giọng "đã xảy ra".

---

## Cửa tự động — KIỂM TRƯỚC KHI TIN

**Chạy `python --version` trước tiên.** Luật `python-he-thong` chặn đúng
hình dạng đó và trả mã 2 kèm thông báo. Bị chặn → cửa sống. In ra số hiệu
Python → **sáu cửa đang chết**, và mọi dòng trong bảng dưới là mô tả một
thứ không xảy ra.

Cửa của repo (`.claude/settings.json`) chỉ được nạp khi **phiên được mở ở
chính thư mục repo**. `cd` hay `change_directory` giữa phiên đều không
nạp — đo 08/09/2026, hai lượt độc lập. Cửa đăng ký ở
`~/.claude/settings.json` bằng **đường dẫn tuyệt đối** thì chạy bất kể
phiên mở ở đâu. Từ 08/09/2026 có **bốn** cửa nằm ở đó (xem cột dưới).

| Cửa | Khi nào | Đăng ký ở | Làm gì |
|---|---|---|---|
| `tools/cua_mo_phien.py` | **SessionStart** | repo | nhắc gọi skill + liệt kê mốc ngày đang chặn |
| `tools/cua_doc_bat_buoc.py` | Pre · Read/Write/Edit | repo **+ toàn cục** | chưa đọc tài liệu bắt buộc thì chặn sửa file ảnh hưởng kết quả |
| `tools/cua_bash_an_toan.py` | Pre · Bash | repo | chặn hình dạng lệnh đã cắn thật |
| `tools/chan_bia_so_lieu.py` | Post · Write/Edit | repo **+ toàn cục** | quét mẫu bịa số liệu |
| `tools/cua_ghi_an_toan.py` | Post · Write/Edit | repo **+ toàn cục** | file còn 0 byte sau lượt ghi |
| `tools/chan_bia_so_lieu.py --quet-thay-doi` | Stop | repo **+ toàn cục** | soát lại file đã đổi |

Cột **Đăng ký ở** là cột quan trọng nhất: "repo" nghĩa là *chỉ chạy khi
phiên mở ở repo*, và tính tới 08/09/2026 điều đó chưa xảy ra lần nào —
tức hai cửa còn mang mỗi nhãn "repo" (`cua_mo_phien`, `cua_bash_an_toan`)
vẫn đang chết.

Bốn cửa "toàn cục" bật ngày 08/09/2026. Đục thử ngay lúc bật đã lôi ra
một lỗi sống — xem `references/loi-da-mac.md` lỗi 15: **một công cụ đúng
trong repo có thể sai ngay khi được gọi từ nơi khác.** Thêm cửa nào lên
toàn cục thì phải bơm payload giả vào nó từ một cwd ngoài repo TRƯỚC.

**Hook chỉ có hiệu lực từ PHIÊN SAU.** Thêm hook giữa phiên thì phiên đó
vẫn chạy như cũ. Và **hook không thấy gì đi qua Bash trừ cửa Bash** —
mọi thao tác file qua shell đều lọt ba cửa còn lại.

---

## Luồng thông tin thứ hai — NotebookLM

Người dùng chốt ngày 10/09/2026: **dùng NotebookLM thường xuyên, nhưng
không dựa hoàn toàn vào nó.** Giá trị của nó nằm ở chỗ nó là một luồng
**độc lập** — nó đọc tài liệu mà không mang theo giả định của phiên làm
việc này.

**Dùng nó khi nào**

- Trước một phép đo lớn: nhờ nó soát tiêu chí đã khai xem có mâu thuẫn
  với tài liệu cũ không.
- Sau khi viết một kết luận: nhờ nó tìm chỗ trong tài liệu **nói ngược**
  lại kết luận ấy.
- Khi một tài liệu dài đã bị vá nhiều lần và không rõ chỗ nào còn đúng.

**Giới hạn phải nhớ — và nó lớn**

1. **Nó chỉ thấy TÀI LIỆU, không thấy MÃ.** Loại lỗi nặng nhất của dự án
   này là *tài liệu lệch mã* — `N_DAY_DU` ghi 596 trong khi mã là 451,
   cờ C5 ghi `True` trong khi mã là `False`. NotebookLM **không bắt được
   một cái nào trong số đó**, vì cả hai vế nó đọc đều là tài liệu.
2. **Mọi phát hiện của nó phải tự kiểm lại**, bằng `grep` hoặc bằng cách
   đọc mã. Nó chỉ ra CHỖ đáng nhìn; nó không phán được cái gì đúng.
3. **Nó không thay được Quy tắc số 2.** Một con số do nó nhắc lại vẫn là
   con số chưa có lệnh đứng sau.

**Cách nói đúng về nó trong báo cáo:** *"NotebookLM chỉ ra chỗ X, tôi
kiểm lại bằng <lệnh> và nó đúng/sai"* — chứ không phải *"theo
NotebookLM thì X"*. Vế sau là mượn thẩm quyền của một công cụ không có
thẩm quyền đó.

---

## Ranh giới không vượt qua

- **Không đặt lệnh thật.** Agent chuẩn bị → người xác nhận → người đặt lệnh.
- Không commit secrets, `*.db`, `sl_pattern_memory.json`, `backtest/cache/`.
- **Không xoá file `*.db` ở gốc repo** — dữ liệu đo của người dùng. Hỏi trước.
- Không ép hạng vnstock trong mã nguồn.
- Không ghi tài liệu skill của vnstock ra đĩa (giấy phép cấm).
- App không được tự push lên repo nó đang chạy.
- **Không đọc dữ liệu đã khai trước trước ngày đã hẹn.** Xem
  `docs/HANDOFF.md` mục 5.
