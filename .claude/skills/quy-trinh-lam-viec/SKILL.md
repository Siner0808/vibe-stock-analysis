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

**Quy tắc số 3 — MỖI BƯỚC đều phải đi qua sổ tay.** Người dùng chốt
18/09/2026. Từ **BƯỚC 108**, ô thoát `khong_soat_vi` **không còn được
nhận** cho một BƯỚC: mỗi mục trong `docs/soat-notebooklm.json` phải mang
`cau_hoi` nguyên văn, một `o_thoat` là **chuỗi con của chính câu ấy**, và
một kết quả — `phat_hien` khác rỗng, hoặc `khong_tim_thay_gi: true`. Gác:
`tests/test_soat_notebooklm.py::test_TU_MOC_BAT_BUOC_moi_BUOC_deu_phai_HOI_THAT`,
mốc đọc từ `_moc_bat_buoc_hoi` trong chính sổ.

> **Vì sao luật này nằm Ở ĐÂY, không nằm ở mục NotebookLM cuối file.** Mục
> ấy có từ 10/09/2026 và bị bỏ qua đủ để người dùng phải nhắc **bốn lần**.
> Đo 16/09/2026: nó là thứ duy nhất trong file này **không nằm trong một
> Bước có số** — và tôi thi hành các Bước có số. Quy tắc 1 và 2 đứng ở đây
> thì được thi hành; nên luật này đứng cạnh chúng.
>
> **Đo quần thể TRƯỚC khi siết, 18/09/2026**, từ mốc cũ `_moc_buoc` = 81:
>
> ```
> 27 BUOC bi doi khai  ->   8 HOI THAT  ·  19 bo qua       70% bo qua
> ca so                ->  13 HOI THAT  ·  30 bo qua  / 43 muc
> ```
>
> 70% không phải một lượt trượt — nó là **tỷ lệ nền**. Lỗi 86 là sáu lượt
> liên tiếp và gác BƯỚC 107 kéo chuỗi ấy về 0; nhưng chuỗi bằng 0 ở tỷ lệ
> nền 70% chỉ nghĩa là các lượt bỏ qua **xen kẽ** đủ để không thành chuỗi.
>
> **Một BƯỚC mà bằng chứng là MÃ vẫn hỏi được — và đây đúng là chỗ 19 lượt
> kia đã trượt.** Từng lý do một đều đúng, vì công cụ ấy thật sự chỉ thấy
> TÀI LIỆU. Chỗ trượt nằm ở **câu hỏi**:
>
> ```
> hoi SAI : "tai lieu cua anh noi gi ve MA cua toi?"   -> no khong thay, dung
> hoi DUNG: "co cho nao NOI NGUOC lai ket luan toi sap viet khong?"
> ```
>
> Mọi BƯỚC đều kết thúc bằng một kết luận **viết vào tài liệu**, nên câu
> hỏi thứ hai luôn có đích. Trả lời *"không tìm thấy câu nào nói ngược"*
> là một **kết quả hợp lệ** — khai `khong_tim_thay_gi: true`, đừng khai là
> không soát.
>
> **Không hỏi được thì đó là việc phải BÁO, không phải việc ghi vào ô
> thoát.** Ô ấy ra đời để khỏi phải BỊA; nó đã thành chỗ để khỏi phải HỎI.
>
> **Phạm vi là BƯỚC, không phải ĐO** — mọi ĐO đều kết thúc bằng một BƯỚC
> trong `docs/STATE.md`, và gác một quần thể thì hai quần thể không trôi
> khỏi nhau được.
>
> **Giới hạn của gác, khai thẳng:** nó đọc được *có hỏi hay không*, nó
> **không** đọc được *hỏi có tử tế không*. Bảng lỗi 86 nói trước điều đó —
> *"một gác đếm chỉ dạy người ta xen một câu hỏi lấy lệ"*. Thứ đứng ở chỗ
> ấy là ba đòi hỏi về **chất** của câu hỏi, không phải về số lượng.

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

**Và đọc hai dòng còn lại của bản tin mở phiên, nếu chúng hiện ra:**

| dòng | nghĩa là | làm gì |
|---|---|---|
| `SOÁT CHÉO còn nợ n` | có BƯỚC chưa khai đã soát chéo hay chưa | soát, rồi khai vào `docs/soat-notebooklm.json` |
| `SOÁT QUY TRÌNH: n ngày trước` | quá nhịp 2 ngày | `tools/soat_loi_khai_cu.py` cho danh sách việc |

> **Hai dòng này thêm ngày 16/09/2026, và lý do thì đáng đọc.** Hôm ấy
> người dùng hỏi vì sao cả một phiên trôi qua không dùng NotebookLM lần
> nào — **lần nhắc thứ ba**. Đo ra ba việc:
>
> 1. Mục NotebookLM của skill này nằm ở **cuối file, sau Bước 6** — thứ
>    duy nhất không nằm trong một Bước có số. Tôi thi hành các Bước có số.
> 2. Gác `tests/test_soat_notebooklm.py` **có thật** từ 12/09, nhưng nó
>    canh `## ĐO n`. Hôm ấy sinh **0 ĐO và 5 BƯỚC**, nên nó im lặng đúng
>    theo phạm vi của chính nó. **Cái gác không yếu — nó ngắm quần thể
>    khác với quần thể công việc thật.**
> 3. Bảy cửa không cửa nào liên quan. Hai lượt `grep` khớp chữ "otebook"
>    là `NotebookEdit`, một tên tool của Claude Code.
>
> Nay quần thể của gác là **BƯỚC từ mốc `_moc_buoc` trở đi**, và bản tin
> nói ra lúc MỞ PHIÊN — chỗ còn quyền chọn — thay vì chỉ đỏ lúc chạy test,
> khi việc đã xong.

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
> `~/.claude/rules/vibe-preview.md`, file nạp vào **mọi** phiên bất kể
> mở ở đâu.
>
> ⚠️ **ĐƯỜNG DẪN ẤY ĐỔI NGÀY 22/09/2026, và câu này trỏ vào chỗ trống
> tròn một ngày.** File vốn nằm ở `.../rules/ecc/common/` — chung thư
> mục với gói ECC mà **không** phải nội dung ECC. Lượt gỡ ECC dời nó ra
> `rules/` rồi xoá thư mục cũ.
>
> **Cơ chế không hỏng; chỉ địa chỉ hỏng** — và đó là hình dạng khó thấy
> nhất, vì người đọc đi theo, không thấy file, rồi kết luận cơ chế đã
> chết. Cùng họ với lỗi 95, khác một chiều: lỗi 95 sai ngay ngày viết,
> câu này đúng ngày viết rồi **hỏng vì thế giới đổi dưới chân nó**.
>
> Lệnh đọc: `tools/kiem_duong_ngoai_repo.py`.

---

## Bước 1 — Trước khi viết, và trước khi nói KHÔNG LÀM ĐƯỢC

**Điều 1 — tìm xem đã có lời giải chưa.**

```bash
./.venv/Scripts/python.exe tools/ho_so.py <ten file>
grep -rn "<khai niem>" tests/ tools/ --include=*.py | head -20
```

> `tools/ho_so.py` gom bốn nguồn ĐÃ ĐO về một file — test nào import nó,
> BƯỚC nào trong `docs/STATE.md` nhắc nó, ĐO nào khai nó, dòng bảng lỗi nào
> lấy nó làm chỗ hỏng. **Nó không tóm tắt gì cả**: mọi dòng in ra là một địa
> chỉ `grep` lại được. Cửa `tools/cua_ho_so.py` tự chạy nó mỗi lần mở một
> file đủ dày (đo 15/09/2026: 23 trên 52 file `.py` ở gốc repo).

**Điều 1b — một ĐẶC TẢ KỸ THUẬT thì đọc nguyên văn, không đọc qua tầng
nén** (thêm 15/09/2026, lỗi 67). Một bản tóm tắt do mô hình đọc hộ dùng được
để biết CHỖ ĐÁNG NHÌN, không dùng được để KẾT LUẬN. Ngày ấy một bản nén
khẳng định `PreToolUse` không bơm được ngữ cảnh, và cả một vòng thiết kế
xoay theo nó trước khi trang đặc tả — đọc thẳng — nói ngược lại.

> **Với một PHÉP ĐO thì điều này nay có gác** (14/09/2026). Mỗi mục
> `## ĐO n` trong `docs/TIEU-CHI-DOC-TRUOC.md` phải mang một trong hai
> dòng — `**Đã tra trùng:** BƯỚC n — …` hoặc
> `**Không khai được là đã tra vì:** …` — và mọi số hiệu BƯỚC được khai
> phải CÓ THẬT trong `docs/STATE.md`.
>
> Gác: `tests/test_do_phai_khai_da_tra.py`. Nó **không** biết lời khai
> có đúng không; nó chặn đúng một thứ — **một phép đo đã ký mà không ai
> nói được đã tra trùng hay chưa**. Hai lỗi sinh ra nó: lỗi 41 (ĐO 5
> trùng BƯỚC 25, mất 88,8 phút) và lỗi 53 (ĐO 8 bỏ qua BƯỚC 8).

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

> **Một phát sống sót cũng có thể là phát ĐƯỢC THIẾT KẾ SAI.** Trước khi
> đi sửa gác, hỏi: đột biến này có THẬT SỰ đổi hành vi ở chỗ đang canh
> không? Ngày 17/09/2026 một phát dời phép chụp xuống sau `ghi()` nhưng
> vẫn trước lượt chạy — tức vẫn chụp đúng lúc — nên nó sống sót một cách
> vô nghĩa, và suýt làm một cái gác đang đúng bị đem ra sửa.

> **Và lượt đục thử không được để lại RÁC.** `dot_bien` hoàn trả file nó
> VÁ, nhưng đột biến có thể làm mã chạy GHI RA CHỖ KHÁC — lỗi 76. Nay
> `va_an_toan.kiem_khong_de_rac()` nổ và gọi tên mọi mục mới ở gốc repo.
> Nếu nó nổ: **xoá tay rồi thiết kế lại phát ấy**, đừng tắt gác.

Bốn điều bắt buộc, cả bốn từ sự cố thật:

1. **Phép đục phải đi qua đúng HÀM ĐANG PHÁN**, không qua hàm trích.
2. **Phát đầu tiên phải là: dựng lại nguyên văn lỗi thật.** Đó là câu hỏi
   duy nhất đáng hỏi — *gác có bắt được đúng thứ nó sinh ra để bắt không.*
3. **Gác một phép SUY RA thì kiểm HÌNH DẠNG biểu thức bằng AST**, không
   kiểm giá trị nó cho ra.
4. **MÁY ĐO cũng phải bị nghi ngờ như GÁC** — và nó nguy hiểm hơn, vì một
   gác sai thì ĐỎ, còn một máy đo sai thì chỉ **in ra một con số**.

   Ngày 14–15/09/2026, **năm** máy đo liên tiếp hẹp hơn thứ chúng đo, và
   cả năm đều cho một con số nghe hợp lý: `0 ca`, `0 ca`, `sống sót`,
   `16/20`, `15/33`. Lỗi 61.

   Những thói quen đã cứu cả năm lần, và không lần nào là sự cẩn thận.
   **Không đếm chúng ở đây** — bản trước ghi *"Hai thói quen"* rồi
   đứng trên BA gạch đầu dòng, và nay là bốn. Cùng hình dạng với
   *"bốn cổng"* và *"chín luật"*: một con số đếm thứ có thật thì nó
   trôi, nên đừng ghim nó cạnh thứ nó đếm.

   - **In DỮ LIỆU THÔ ngay dưới con số.** Nếu lượt quét heredoc chỉ in
     `0`, tôi đã kết luận *"quần thể rỗng, không đo được"* — nghe rất
     hợp lý, và sai: hai ca nằm ngay trong bản in bên dưới.
   - **Bắt máy đo đi qua một ca THẬT đã biết trước.** Biết trước câu ở
     `HANDOFF` có tồn tại là thứ duy nhất chứng minh được lượt quét ra
     `0 ca` là hỏng, chứ không phải sạch.
   - **Trước khi tin một kết quả ÂM, hỏi: mẫu này CÓ KHẢ NĂNG cho kết
     quả DƯƠNG không?**

   - **NỀN NHIỄU của một phép hiệu chuẩn phải cùng TÍNH CHẤT THỐNG KÊ với
     thứ nó hiệu chuẩn, VÀ phải RỜI khỏi nhãn** (thêm 22/09/2026, lỗi 94).
     Hai đòi hỏi ngược nhau, và bỏ vế nào cũng cho ra một phép đo tự khen
     mình:

     ```
     nen NHIEU TRANG        -> null HEP hon that -> hieu chuan mot bai DE
                               HON bai that roi tuyen bai that la doc duoc
     nen la CHINH COT THAT  -> o "khong tiem gi" hoa ra la DO LAI cot ay
                               -> phep hieu chuan tu kiem thu no di kiem
     nen = cot that DICH VONG trong tung ma  -> DUNG ca hai ve
     ```

     Và **giữ đủ ô "không tiêm gì"**. Một phép hiệu chuẩn chỉ có các mức
     *nửa rào / đúng rào / 1,5× rào* thì không bao giờ phát hiện được rằng
     chính nó đang tự kêu trên hư không — ngày 22/09/2026 đúng ô ấy là thứ
     duy nhất tố ra hai bản hỏng liên tiếp. (thêm 15/09/2026, lỗi 66). Đo lượt C của ĐO 9
     thấy vốn đỉnh **99,9** với bụi float 1e-14, tôi kết luận *"bụi bị
     loại"* rồi suy ra hai lượt kia vượt trần thật. Vô hiệu: 99,9
     không bao giờ chạm phép thử `> 100.0`, nên mẫu ấy **không thể**
     cho kết quả dương dù sự thật là gì. Một kết quả âm từ một mẫu nằm
     ngoài vùng phép thử phân biệt được thì nói về **mẫu**, không nói
     về **giả thuyết**. Lượt D chạm đúng 100 và lật ngược nó trong hai
     phút — lại là điều bắt buộc ngay ở trên cứu.
   - **Hỏi phép đo có đi qua một BẢN GHI NHỚ nào không** (thêm
     17/09/2026, lỗi 75). Đo giá của cửa `cua_ho_so` bằng năm lượt bơm
     payload `Read` giả cho trung vị **110 ms**, và suýt thành kết luận
     *"cửa rẻ"*. Cả năm payload mang **cùng một `session_id`**, nên bốn
     lượt sau rơi vào nhánh im lặng *"đã bơm file này trong phiên này"*.
     Đo lại, mỗi lượt một phiên khác: **410 ms**. Máy đo không hẹp — nó
     đo đúng thứ nó chạm, chỉ là thứ nó chạm không phải thứ nó khai.
     Nên: đổi **khoá** của mọi bản ghi nhớ giữa các lượt — phiên, tiến
     trình, file đệm, khoá `@cache`. Và dữ liệu thô lại là thứ cứu:
     `395 · 112 · 110 · 108 · 107` không đọc xuôi được.

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

> **Số cổng là một con số ĐẾM THỨ CÓ THẬT, nên nó trôi.** Cổng thứ
> năm ra đời 10/09/2026; tới 14/09 vẫn còn **bốn** chỗ viết *"bốn
> cổng"* — kể cả điều kiện tự merge ngay ở Bước 5 dưới đây — và tên
> `kiem_so_test_khong_giam` xuất hiện **0 lần** trong `CLAUDE.md`,
> `docs/HANDOFF.md`, `README.md` và `references/cong-thuc-chay.md`.
>
> Nay `tests/test_bo_cong_khop_CI.py` suy danh sách cổng từ
> `.github/workflows/kiem-dinh.yml` — thứ **thật sự chạy** — rồi bắt
> mọi khối lệnh trong tài liệu đã đặt tên từ hai cổng trở lên phải
> đặt tên đủ. `docs/STATE.md` BƯỚC 62.

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

  1. **Năm** cổng ở Bước 4 xanh tại máy.
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
- Commit body **ASCII**, và **CÓ** `Co-Authored-By`.

  > 🔴 **VẾ THỨ HAI TỪNG GHI NGƯỢC, và nó sống 11 ngày.** Câu cũ là
  > *"không `Co-Authored-By`"*. Đo 23/09/2026 ở lượt SOÁT QUY TRÌNH
  > thứ tư, đếm trên chính lịch sử git:
  >
  > ```
  > commit KHONG merge, tu 09/09  :  100
  >     co dong Co-Authored-By    :   80
  > commit cuoi cung KHONG co     :  11/09/2026
  > ```
  >
  > Tức quy ước đã đổi từ **12/09/2026** và câu ở đây không đi theo. Đây
  > là hình dạng quen: một lời khai về THỰC HÀNH thì mục ruỗng khi thực
  > hành đổi, mà không cổng nào đọc được thông điệp commit — cùng lý do
  > lỗi 81, 89 và 93 không gác được. Lệnh đo lại:
  >
  > ```bash
  > git log --no-merges --format=%B | grep -c Co-Authored-By
  > ```

  > **KIỂM BẢN ĐÃ GHI, ĐỪNG KIỂM BẢN SẮP GHI** (lỗi 93, 22/09/2026).
  >
  > ```bash
  > ./.venv/Scripts/python.exe -c "import subprocess as s; v=s.run(['git','log','-1','--format=%B'],capture_output=True,text=True,encoding='utf-8').stdout; d=[i for i,x in enumerate(v.splitlines(),1) if any(ord(c)>126 for c in x)]; print('dong ngoai ASCII:', d or 'khong')"
  > ```
  >
  > Hai lý do, cả hai đã cắn trong một lượt giao:
  >
  > 1. **`grep` thành công khi TÌM THẤY**, tức mã thoát **0** đúng lúc ta
  >    muốn dừng. Nối `&& git commit` sau một phép kiểm `grep` là để nó
  >    chạy tiếp đúng khi có lỗi. Cùng cơ chế luật `pytest-qua-ong`.
  > 2. Một lượt vá thông điệp có thể **không chạm được file** — đường dẫn
  >    kiểu MSYS `/c/Users/...` truyền vào Python nổ `FileNotFoundError` —
  >    rồi `--amend` đọc lại đúng bản cũ. Chỉ phép kiểm đọc **commit** mới
  >    thấy; phép kiểm đọc **file** thì không.
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

**Chạy cái này trước tiên** — nó ĐỌC trạng thái, không bắt bạn suy ra:

```bash
./.venv/Scripts/python.exe tools/kiem_cua_song.py
```

Nó so hook khai trong `.claude/settings.json` của repo với bản ở
`~/.claude/settings.json`, và gọi tên từng cửa chưa được chép. Mã thoát
0 đủ · 1 thiếu · 2 chưa kiểm được. Bản tin mở phiên cũng in một dòng
`CUA: n/m song`.

> ### `python --version` KHÔNG phải phép thử của sáu cửa — lỗi 25
>
> Bản trước của mục này viết: *"Bị chặn → cửa sống. In ra số hiệu Python
> → sáu cửa đang chết."* **Vế sau sai**, và nó sống ba ngày.
>
> Lệnh ấy đi qua đúng **MỘT** hook: `cua_bash_an_toan`, `PreToolUse`
> matcher `Bash`. Nó không nói được gì về bốn cửa `Read/Write/Edit` và
> `Stop`. Ngày 10/09/2026 tôi chép lại câu ấy ba lần trong một buổi,
> trong khi bốn cửa kia đang chạy và có nhật ký chứng minh — đo bằng
> một lượt Read: đúng một dòng mới, đúng giây ấy.
>
> **Một phép thử đo MỘT cửa không phải phán quyết về SÁU.** Cùng họ với
> lỗi 22, nhưng khó thấy hơn: ở lỗi 22 phép thử hỏng nên không đo gì; ở
> đây phép thử CHẠY, cho kết quả ĐÚNG, rồi bị đọc rộng hơn phạm vi nó
> có.

Cửa của repo (`.claude/settings.json`) chỉ được nạp khi **phiên được mở ở
chính thư mục repo**. `cd` hay `change_directory` giữa phiên đều không
nạp — đo 08/09/2026, hai lượt độc lập. Cửa đăng ký ở
`~/.claude/settings.json` bằng **đường dẫn tuyệt đối** thì chạy bất kể
phiên mở ở đâu. Từ 08/09/2026 có **bốn** cửa nằm ở đó (xem cột dưới).

| Cửa | Khi nào | Đăng ký ở | Làm gì |
|---|---|---|---|
| `tools/cua_mo_phien.py` | **SessionStart** | toàn cục | nhắc gọi skill · liệt kê mốc ngày đang chặn · in dòng `CUA: n/m song` |
| `tools/cua_doc_bat_buoc.py` | Pre · Read/Write/Edit | toàn cục | chưa đọc tài liệu bắt buộc thì chặn sửa file ảnh hưởng kết quả |
| `tools/cua_bash_an_toan.py` | Pre · Bash | toàn cục | chặn hình dạng lệnh đã cắn thật |
| `tools/chan_bia_so_lieu.py` | Post · Write/Edit | toàn cục | quét mẫu bịa số liệu |
| `tools/cua_ghi_an_toan.py` | Post · Write/Edit | toàn cục | file còn 0 byte sau lượt ghi |
| `tools/chan_bia_so_lieu.py --quet-thay-doi` | Stop | toàn cục | soát lại file đã đổi |

**Từ 10/09/2026 cả sáu chỉ đăng ký ở MỘT nơi: `~/.claude/settings.json`,
bằng đường dẫn tuyệt đối.** Nên chúng chạy bất kể phiên mở ở đâu, và cột
"Đăng ký ở" không còn là chỗ để lo nữa.

> **Vì sao gỡ bản trong repo.** Trước đó bốn cửa đăng ký ở **cả hai** nơi.
> Ngày 10/09/2026 đo trực tiếp bằng một phiên `claude -p` chạy với cwd đặt
> ở repo: settings của repo **CÓ** nạp, và khi đó **cả hai file cùng nạp
> nên mỗi hook chạy HAI LẦN** — hai bản ghi `hook_success` riêng cho
> `SessionStart`, phân biệt được bằng `statusMessage` của từng file.
>
> **Và chính vế "phân biệt được bằng `statusMessage`" là chỗ gỡ một mâu
> thuẫn sống sáu ngày.** Đặc tả hook viết *"cùng một handler khai ở nhiều
> file settings thì chạy MỘT lần"*; câu trên nói HAI. Đo lại 16/09/2026:
> hai bản khai ấy khác nhau ở cả ba trường (`command`, `timeout`,
> `statusMessage`), nên chúng chưa bao giờ là *"cùng một handler"*. Hai
> câu đều đúng. Ca giống hệt từng byte thì **chưa đo được** — `claude -p`
> trên máy này hết hạn OAuth. `docs/STATE.md` BƯỚC 82.
>
> Chạy đôi làm **nhân đôi nhật ký `cua_doc_bat_buoc`**, mà nhật ký ấy đang
> được dùng làm bằng chứng "cửa có sống không". Vì cả sáu đã có bản toàn
> cục, bản trong repo không mang lại chức năng nào và chỉ mang một mối
> nguy — nên nó được gỡ.
>
> Phần **khai** sáu cửa dự án muốn có chuyển sang `docs/cua-du-an.json`;
> `tools/kiem_cua_song.py` so bản khai ấy với settings toàn cục. Trên một
> máy mới nó báo 0/6 — đúng thông điệp cần có, thay vì im lặng chạy đôi.
> Khoá bởi `tests/test_cua_song.py::
> test_settings_CUA_REPO_khong_duoc_dang_ky_hook_nao`.

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

> ### 🔴 MỘT Ô THOÁT ĐÒI LÝ DO CỤ THỂ VẪN LÀ Ô THOÁT — lỗi 86, 18/09/2026
>
> Sáng 18/09 một phép đo lôi ra rằng quần thể sổ tay hẹp hơn quần thể công
> việc: *công cụ soát định kỳ quét BẢY tài liệu · sổ tay nạp NĂM nguồn ·
> giao nhau đúng BA*. Phát hiện ấy **đúng**.
>
> Rồi nó thành một **câu thần chú**. **Sáu mục liên tiếp** khai
> `khong_soat_vi` viện dẫn nó, mỗi lượt một biến thể nghe rất hợp lý —
> *bằng chứng nằm ngoài repo* · *bằng chứng là MÃ* · *bản chụp cũ hơn lời
> khai*. Đếm ra: hôm ấy **1 hỏi thật / 6 bỏ qua**, toàn sổ **30/43**.
> Người dùng phải hỏi thẳng, **lần nhắc thứ tư**.
>
> **BA LUẬT, và cái thứ ba là cái khó nhất:**
>
> 1. **Một lời khai *"quần thể không chứa câu trả lời"* phải ĐO LẠI, không
>    được chép.** Quần thể đổi khi nạp thêm nguồn, và nạp thêm nguồn là
>    việc **cộng vào, đảo lại được** — luật xoá nguồn chỉ quản việc XOÁ.
> 2. **Thấy quần thể thiếu thì ĐÓNG nó, đừng viện dẫn nó.** Phép sửa nằm
>    ngay trong chính phép đo; hôm ấy tôi nghĩ ra nó buổi sáng rồi hoãn.
> 3. **Chuỗi bỏ qua là một đại lượng — nó có trong bản tin mở phiên.**
>    `tools/cua_mo_phien.chuoi_khong_soat()` đếm số mục CUỐI SỔ liên tiếp
>    đều khai `khong_soat_vi`; từ **3** trở lên bản tin nói ra và gọi tên
>    chúng. Nó **không chặn** — nó làm một hình dạng vô hình thành nhìn
>    thấy được, đúng chỗ còn quyền chọn.
>
> **GÁC HIỂN NHIÊN HƠN ĐÃ ĐO VÀ BỎ — đừng dựng lại nó.** Ý đầu tiên là
> *cấm lặp lý do*. Đo 435 cặp trong sổ:
>
> ```
> sau muc cua loi 86, giua CHUNG voi nhau : trung binh 0,131
> moi cap CON LAI trong so                : trung binh 0,099
> cap giong nhau nhat ca so               : 0,653  (hai muc KHONG lien quan)
> khong cap nao dat 0,70
> ```
>
> Sáu lời khai ấy giống nhau **còn ít hơn** mức trung bình. Chúng không bị
> chép — mỗi lượt là một lý do thật sự khác, và **chính điều đó làm chúng
> vô hình**. Một gác so chữ sẽ im lặng đúng lúc cần kêu. Thứ lặp lại là
> **sự kiện được viện dẫn**, không phải chữ, và máy không đọc được điều đó.

> ### ⚠️ CÁCH HỎI QUYẾT ĐỊNH NÓ BỊA HAY KHÔNG — BƯỚC 107, 18/09/2026
>
> Ba câu hỏi trong một phiên tách được đúng một biến:
>
> | file có trong nguồn? | câu hỏi có LỐI THOÁT? | kết quả |
> |---|---|---|
> | **có** | **không** | **BỊA tiêu đề** |
> | **KHÔNG** | **không** | **BỊA cả trích dẫn LẪN tên file** |
> | **có** | **có** | **chính xác từng chữ** |
>
> Hai câu đầu đối chiếu bằng `grep`: **0 dòng khớp**. Câu thứ hai nặng hơn
> — nó **trích một file không nằm trong nguồn**, mà **số hiệu thì đúng** vì
> suy được từ một file khác. *Con số đúng bọc trong bằng chứng bịa* là hình
> dạng khó thấy nhất.
>
> **LUẬT: mọi câu gửi sổ tay phải mang một LỐI THOÁT tường minh** — ví dụ
> *"If that file is NOT among your sources, say exactly that and do not
> guess."* Thiếu nó, **sổ tay bịa thay vì từ chối**.
>
> Vế này mạnh hơn luật cũ *"phải tự kiểm lại mọi phát hiện"*: nó nói **cách
> hỏi**, không chỉ nói cách đọc. Cả hai đều phải giữ.
>
> **TINH CHỈNH BƯỚC 108, cùng ngày: `0 dòng khớp` CHƯA đủ để kết tội bịa.**
> Một câu hỏi CÓ lối thoát vẫn cho trích dẫn `grep` ra 0 dòng — vì sổ tay
> **lột dấu nhấn Markdown**. Nó dẫn `"Không: nó chỉ đọc VĂN BẢN."`; câu
> thật ở `docs/STATE.md` dòng 6800 là `**Không:** nó chỉ đọc VĂN BẢN.`
>
> 🔴 **VÀ CÂU "GREP LẠI MỘT CHUỖI CON" VẪN HẸP — lỗi 88, 21/09/2026.** Ba
> lớp nhiễu, không phải một. Đối chiếu 15 trích dẫn trong một lượt:
>
> ```
> grep TUNG DONG, giu dau nhan        ->   8 khop  ·  4 nghi BIA
> bo dau nhan, noi lien dong          ->  11 khop  ·  3 nghi BIA
> bo THEM dau trich dan `> `          ->  14 khop  ·  1 BIA that
> ```
>
> Lớp 2 là **ngắt dòng cứng ~76 ký tự**, lớp 3 là **dấu `> ` của
> blockquote**. Mỗi lớp một mình đủ làm một câu THẬT trả về 0 dòng — tức
> phép tự kiểm của lượt đầu **vu oan 4 trên 15**.
>
> **ĐỪNG tự grep nữa — chạy dụng cụ:**
>
> ```bash
> ./.venv/Scripts/python.exe tools/doi_chieu_trich_dan.py "<trích dẫn>"
> ```
>
> Ba ô: **0** khớp · **1** lệch · **2** chưa kiểm được. Khi lệch nó nói
> **lệch từ ký tự thứ mấy**, tức phân biệt *bịa hẳn* với *trích đúng một
> đoạn rồi chế thêm*. `docs/STATE.md` BƯỚC 109.
>
> ⚠️ **VÀ Ô THOÁT PHẢI PHỦ ĐÚNG CÁI ĐANG HỎI, không phủ cái CHỨA nó.** Câu
> hỏi 21/09 có lối thoát — *"If docs/STATE.md is NOT among your sources,
> say exactly that and do not guess"* — và sổ tay vẫn bịa một dòng tiêu đề,
> vì file **có** trong nguồn, thứ không có là **dòng** được hỏi. Hỏi một
> DÒNG thì lối thoát phải nói *"nếu không tìm thấy dòng ấy"*.

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

### NGÔN NGỮ — hỏi bằng TIẾNG ANH, đòi trả lời bằng TIẾNG VIỆT

**Người dùng chốt 17/09/2026.** Mọi câu gửi sổ tay viết bằng **tiếng
Anh**, và mỗi câu phải mang theo một dòng đòi nó trả lời bằng **tiếng
Việt**:

```
Answer in Vietnamese.
```

**Lý do người dùng CHƯA NÊU, và tôi không suy hộ.** Ghi ra đúng như vậy:
một lý do bịa còn tệ hơn không có lý do, vì lần sau người ta sẽ cãi với
cái lý do bịa thay vì hỏi lại người dùng.

**Ba thứ KHÔNG đổi:**

- **Báo cáo cho người dùng vẫn tiếng Việt.** Quy ước này chạm đúng một
  đoạn đường: *tôi ↔ sổ tay*. Không chạm đoạn *tôi ↔ người dùng*.
- **`phat_hien`, `phan_quyet`, `khong_soat_vi` vẫn tiếng Việt** — chúng
  là ghi chép của dự án, không phải câu gửi đi.
- **Trích dẫn nguyên văn tài liệu thì giữ tiếng Việt.** Tài liệu dự án
  viết tiếng Việt, nên một câu hỏi đàng hoàng thường phải dẫn lại chúng.
  Bắt câu hỏi sạch dấu tiếng Việt sẽ đẩy người hỏi sang *kể lại* thay vì
  *dẫn lại* — và một bản kể lại là một tầng nén, đúng thứ lỗi 67 cấm.

**`cau_hoi` trong `docs/soat-notebooklm.json` từ mốc này ghi NGUYÊN VĂN
câu đã gửi**, không còn là bản tóm tắt tiếng Việt.

Gác: `tests/test_soat_notebooklm.py::test_CAU_HOI_tu_MOC_NGON_NGU_phai_DOI_TRA_LOI_TIENG_VIET`,
mốc đọc từ `_moc_ngon_ngu` trong chính sổ.

> **Giới hạn của gác, khai thẳng:** nó chỉ kiểm rằng câu hỏi **có mang
> dòng đòi trả lời tiếng Việt**. Nó **không** kiểm được phần còn lại có
> thật sự là tiếng Anh không — vì như đã nói ở trên, một câu hỏi hợp lệ
> có quyền chứa tiếng Việt trong phần trích dẫn. Nửa ấy là kỷ luật, không
> phải cơ chế; đừng đọc một lượt xanh thành *"câu hỏi đã viết bằng tiếng
> Anh"*.

### CƠ CHẾ, không phải lời nhắc (16/09/2026)

```
docs/soat-notebooklm.json   moi DO va moi BUOC tu `_moc_buoc` phai khai
                            `phat_hien` XOR `khong_soat_vi`
                            tu `_moc_bat_buoc_hoi`: o thoat KHONG con  <- quy tac 3
tools/cua_mo_phien.py       ban tin mo phien in so muc con no, VA goi ten moc
tests/test_soat_notebooklm  do khi thieu, khi ly do rong/chung chung,
                            va khi mot BUOC tu moc ay con khai `khong_soat_vi`
```

**ĐO ĐỘ TƯƠI TRƯỚC KHI HỎI, mỗi lượt, không nhớ từ lượt trước.** Hỏi sổ
tay *"số hiệu BƯỚC lớn nhất xuất hiện trong các nguồn"* rồi đối chiếu
`grep -c '^## BƯỚC' docs/STATE.md`. Đo 16/09/2026: sổ tay **73**, repo
**85** — lệch 12 BƯỚC, tức nó không thấy chính phép đo mình định nhờ soát.
Ngày 14/09 con số ấy là 41 so với 73.

**Và phép BỎ CHỌN nguồn không sống qua phiên.** Ngày 15/09 bốn bản chụp cũ
được bỏ chọn, còn 5 nguồn; ngày 16/09 cả 9 được tích lại. Một câu *"đã bỏ
chọn"* vì thế mô tả một trạng thái tạm, không phải một phép sửa.

**CÁCH LÀM TƯƠI, khi độ tươi đo ra là lệch** (dựng 16/09/2026, BƯỚC 88).
Nguồn URL là **ảnh chụp**, không phải liên kết sống, và menu của nó chỉ có
`Xoá nguồn` · `Đổi tên nguồn` — **không có nút làm mới**. Nên:

```
1. doc va GHI chinh xac cac URL dang co  (tu cay tro nang, khong go tay)
2. MO hop "Them nguon" de KIEM duong khoi phuc  <- TRUOC khi xoa gi
3. DAN LAI ca cum trong MOT luot  (ngan cach bang DAU CACH)   <- THEM truoc
4. XOA cac ban CU                                              <- XOA sau
5. do lai so hieu BUOC lon nhat
```

Bước 2 là bước đáng giữ: **kiểm đường khôi phục trước khi phá thứ đang
có**. Giới hạn sổ là 300 nguồn nên chỗ chứa không phải ràng buộc.

> **BƯỚC 4 NHẮM THEO THAM CHIẾU, ĐỪNG NHẮM THEO PIXEL** (23/09/2026).
> Hai bản của cùng một URL **không phân biệt được bằng tên** — danh sách
> cắt tên ở khoảng 100 ký tự. Nhắm theo toạ độ thì một lượt xoá đã mở
> đúng hộp xác nhận của một bản **MỚI**; hôm ấy thu phóng trang còn tự
> nhảy giữa các lượt chụp và cửa sổ tự co lại, nên mọi toạ độ đều trôi.
>
> Cây trợ năng cho mỗi nguồn một tham chiếu riêng **và** một tham chiếu
> cho nút `⋮` của nó. Chuỗi này thì xác định:
>
> ```
> doc cay tro nang  ->  ref cua tung nguon + ref nut ...
> bam ref nut ...   ->  tim "Xoa nguon" theo ten  ->  bam theo ref
> DOC URL tren hop xac nhan  ->  Xoa neu la ban TRUNG, Huy neu khong
> ```
>
> Hộp xác nhận in **URL đầy đủ**, nên nó là chỗ duy nhất đọc được danh
> tính thật của nguồn trước khi xoá. Đo 23/09: bốn lượt mở, **hai lượt
> huỷ** vì hộp nêu một bản **duy nhất** chứ không phải bản trùng.
>
> **Và xoá xong thì phải ĐO bản còn lại tươi hay cũ** — xoá một bản của
> mỗi cặp không nói gì về bản sống sót. Cách rẻ: `git log` file ấy để
> tìm một câu chỉ có ở bản mới, hỏi sổ tay câu ấy **kèm lối thoát**, rồi
> đối chiếu bằng `tools/doi_chieu_trich_dan.py`. Nếu `git log` cho thấy
> file **không đổi** trong khoảng giữa hai bản chụp thì khỏi đo: hai bản
> giống hệt nhau.

> **Bước 3 và 4 ĐỔI CHỖ ngày 17/09/2026, và lý do là một phép đo.** Bản
> 16/09 xoá trước, thêm sau, vì thêm-trước sinh bản trùng. Nhưng xoá-trước
> có một cửa sổ trong đó **sổ của người dùng rỗng**, và bản trùng thì gỡ
> được còn sổ rỗng thì không. Nên đảo lại.
>
> **Và bản trùng KHÔNG chỉ là chuyện gọn gàng — đo được nó làm sổ trả lời
> SAI.** Ở trạng thái 10 nguồn (mỗi file hai bản, một cũ một mới), câu hỏi
> độ tươi ra **BƯỚC 95**; xoá đúng một bản `docs/STATE.md` cũ thì cùng
> câu hỏi ấy ra **BƯỚC 96**, đúng bằng repo. Một bản chụp cũ nằm cạnh
> bản mới
> **kéo câu trả lời về phía nó**. Nên bước 4 là bắt buộc, không phải dọn
> dẹp.
>
> **Đo 17/09/2026: 87 → 96**, đúng bằng repo.
>
> ⚠️ **`raw.githubusercontent.com` có CDN.** Một bản chụp lấy ngay sau khi
> merge có thể chậm một commit. Đó là lý do phải **đo lại** ở bước 5 chứ
> không tin là xong.

Đo 16/09/2026: **73 → 87**, đúng bằng repo.

### XOÁ NGUỒN — hỏi người dùng trước, TRỪ bản trùng vừa tự tạo

Luật gốc, người dùng đặt **08/09/2026**: *xoá nguồn là vĩnh viễn, hỏi
người dùng trước, đừng tự quyết.*

**Thu hẹp 17/09/2026, do chính người dùng chốt sau khi tôi vượt rào:**

```
xoa mot ban TRUNG cua nguon vua dan lai o buoc 3   ->  KHONG phai hoi
xoa bat ky nguon nao KHAC                          ->  HOI NGUOI DUNG
```

Ranh giới sắc, không mờ: **bước 4 của thủ tục làm tươi chỉ được xoá đúng
những bản mà bước 3 vừa tạo ra bản thay thế.** Nội dung của chúng lấy lại
được từ chính URL vừa dán — mất cũng dựng lại được trong một lượt. Một
nguồn KHÔNG phải bản trùng thì có thể là bản duy nhất, và *vĩnh viễn* ở
đó nghĩa đúng như chữ.

> **KHÔNG CÓ GÁC MÁY CHO LUẬT NÀY, và đây là chỗ nói ra điều đó.**
>
> Xoá nguồn là một thao tác trong trình duyệt, trên tài khoản người dùng.
> Nó **không để lại dấu vết nào trong repo**, nên không cổng nào thấy.
>
> Và một gác kiểu *"phải khai vào sổ khi có xoá nguồn"* thì **bắt được số
> không**: ai quên hỏi thì cũng quên khai. Một cái gác canh chính lời khai
> của người khai là một cái gác rỗng — cùng họ với `gac-hong`, chỉ khác là
> nó rỗng ngay từ lúc thiết kế.
>
> Đây là **kỷ luật**, không phải cơ chế. Ghi ra để lần sau không ai tốn
> thời gian đi dựng một cái gác không dựng được.

Người dùng đề xuất nhịp cho việc *"update skill và hook"*. Đo trước khi
nhận, và phép đo **đổi cái đích**:

```
SKILL.md + bang loi CO SUA 9 tren 14 ngay gan nhat
```

Việc **cập nhật** đã chạy theo sự kiện ở Bước 6 — mỗi lỗi mới là một dòng
mới. Đặt nhịp 2 ngày lên đó là đặt một nhịp **thấp hơn** nhịp đang có.

Nửa chưa bao giờ có cơ chế là **soát lại thứ ĐÃ CÓ**. Riêng ngày 16/09 hai
câu cũ bị bắt gặp do **tình cờ**: *"cửa Bash không ghi nhật ký … chưa làm"*
(nhật ký đã có từ 14/09) và mâu thuẫn BƯỚC 49 sống sáu ngày.

```bash
./.venv/Scripts/python.exe tools/soat_loi_khai_cu.py
```

**Và một lớp nó KHÔNG thấy, đo 23/09/2026.** Lời khai phạm vi của nó là ba bức tường — *phủ định · có nêu tên · trong repo* — nên một câu **khẳng định** nêu một **đường dẫn ngoài repo** lọt cả ba:

```bash
./.venv/Scripts/python.exe tools/kiem_duong_ngoai_repo.py
```

0 sạch · 1 có con trỏ chết · 2 chưa kiểm được. **Nó cố ý không phải một cổng** — đường dẫn nằm ở thư mục nhà của máy này, nên trên CI nó sẽ đỏ mọi lượt; xem bảng lỗi dòng 14, chỗ dự án đã quyết đúng điều ấy. Muốn giữ một đường đã chết thì khai `<!-- duong-da-chet: <lý do> -->` ngay trên dòng ấy; lý do rỗng không được nhận.

Nó in mọi **lời khai phủ định có nêu tên** còn sống trong bảy tài liệu —
15 dòng, siết từ 187 bằng ba phép lọc có lý do. Ghi kết quả vào
`docs/soat-dinh-ky.json`; một lượt soát kết luận *"vẫn đúng"* là kết quả
hợp lệ và phải ghi được, nếu không sổ chỉ chứa tin xấu.

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
