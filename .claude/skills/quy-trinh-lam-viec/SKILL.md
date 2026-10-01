---
name: quy-trinh-lam-viec
description: Quy trinh bat buoc cho MOI viec trong du an vibe_preview - doc, sua, them test, them gac, do luong, chay, commit, bao cao. Dung NGAY khi bat dau bat cu viec gi trong repo nay, truoc khi doc hay sua file dau tien, va moi lan quay lai sau khi bi ngat. Cung dung khi sap sua thu anh huong toi KET QUA DO (diem so, co vi the, chi phi, nguong, cong an toan, backtest, walk-forward), khi mot con so dep len sau thay doi, khi viet mot gac moi, khi va nhieu cho trong mot file, hoac khi can chay bo test va cho ket qua.
---

# Quy trình làm việc — vibe_preview

> **File này chỉ giữ LUẬT HIỆN HÀNH** (BƯỚC 145, 30/09/2026): nó được nạp
> mỗi lần gọi skill nên mỗi KB ở đây là chi phí trả ở mọi lượt gọi tiếp
> theo. Lý do dài, số đo và sự cố của từng luật nằm ở
> `docs/lich-su/SKILL-md-2026-09-30.md` (bản nguyên văn) và
> `references/loi-da-mac.md` (bảng lỗi). Cách làm chi tiết: `references/`.

Dự án đã **năm lần** cho ra con số đẹp mà sau đó vô nghĩa, và một lượt rà
lại một phiên đếm được **11 lỗi quy trình**. Không lỗi nào là lỗi suy nghĩ;
tất cả là lỗi thao tác lặp lại.

**Quy tắc số 1 — nếu một thay đổi làm con số đẹp lên đáng kể, giả định
đầu tiên phải là CÓ LỖI.** Số xấu đi là chiều an toàn.

**Quy tắc số 2 — không có lệnh thì không có số.** Mọi con số viết vào tài
liệu, báo cáo hay commit phải được tính TRONG PHIÊN NÀY, kèm lệnh tái lập
được. Ước lượng thì phải gọi nó là ước lượng (từng suýt ghi "≈40s" cho thứ
đo được 167,7s).

**Quy tắc số 3 — MỖI BƯỚC đều phải đi qua sổ tay NotebookLM** (người dùng
chốt 18/09/2026). Mỗi mục trong `docs/soat-notebooklm.json` phải mang
`cau_hoi` nguyên văn, một `o_thoat` là chuỗi con của chính câu ấy, và một
kết quả: `phat_hien` khác rỗng, hoặc `khong_tim_thay_gi: true`. Ô
`khong_soat_vi` **không còn được nhận** cho một BƯỚC. Không hỏi được thì
**BÁO người dùng**, không ghi ô thoát. Gác:
`tests/test_soat_notebooklm.py::test_TU_MOC_BAT_BUOC_moi_BUOC_deu_phai_HOI_THAT`.
Cách làm từng thao tác: `references/soat-cheo-notebooklm.md`. Phạm vi là
BƯỚC, không phải ĐO.

Chỗ đã trượt 19/27 lượt nằm ở **CÂU HỎI**, không ở công cụ: hỏi *"tài liệu
nói gì về MÃ của tôi"* thì nó không thấy mã; hỏi *"có chỗ nào NÓI NGƯỢC kết
luận tôi sắp viết"* thì luôn có đích. Trả *"không tìm thấy câu nào nói
ngược"* là kết quả hợp lệ. Dựng câu hỏi và ghi sổ bằng `tools/so_tay.py hoi`
· `ghi`, không gõ tay.

---

## Bước 0 — Mở phiên (30 giây, không được bỏ)

```bash
git -C <repo> status --short && git -C <repo> branch --show-current
```

Đọc bằng tool Read (hook `tools/cua_doc_bat_buoc.py` chỉ đếm Read):
`docs/HANDOFF.md` → `docs/STATE.md` (mục cuối) → `NGUYEN-TAC-DO-LUONG.md` →
`MO-XE-KIEN-TRUC.md`. Rồi liệt kê **thứ đang bị chặn theo ngày** và không
đọc sớm. Đọc hai dòng của bản tin mở phiên nếu chúng hiện ra: `SOÁT CHÉO
còn nợ n` (soát rồi khai vào `docs/soat-notebooklm.json`) và `SOÁT QUY TRÌNH:
n ngày trước` (quá nhịp 2 ngày → `tools/soat_loi_khai_cu.py`).

Luật nạp skill ở mọi phiên nằm trong `~/.claude/rules/vibe-preview.md`
(nạp bất kể phiên mở ở đâu). Đường ngoài repo đổi dưới chân: kiểm bằng
`tools/kiem_duong_ngoai_repo.py`.

---

## Bước 1 — Trước khi viết, và trước khi nói KHÔNG LÀM ĐƯỢC

**Điều 1 — tìm xem đã có lời giải chưa.**

```bash
./.venv/Scripts/python.exe tools/ho_so.py <ten file>
grep -rn "<khai niem>" tests/ tools/ --include=*.py | head -20
```

`tools/ho_so.py` gom test, BƯỚC, ĐO và dòng bảng lỗi nhắc file ấy; mọi dòng
là một địa chỉ `grep` lại được, không tóm tắt (cửa `tools/cua_ho_so.py` tự
chạy nó). Lời giải nhiều lần nằm sẵn trong test kèm docstring — đọc trước
khi viết lại.

**Điều 1b — một ĐẶC TẢ KỸ THUẬT thì đọc nguyên văn, không đọc qua tầng nén**
(lỗi 67): tóm tắt dùng để biết CHỖ ĐÁNG NHÌN, không để KẾT LUẬN. Mỗi mục `##
ĐO n` trong `docs/TIEU-CHI-DOC-TRUOC.md` phải mang `**Đã tra trùng:** BƯỚC n
— …` hoặc `**Không khai được là đã tra vì:** …`; gác:
`tests/test_do_phai_khai_da_tra.py`.

**Điều 2 — một câu "không làm được" (hay "CHƯA ĐO ĐƯỢC") phải ĐO LẠI hoặc
nói rõ nó chưa được kiểm trong phiên này.** Trước khi viết *chưa đo được*,
chạy phép đo rẻ nhất chạm tới nó — với thứ dự án đã làm thì quần thể gần như
luôn là lịch sử git (`git log -S` cho mã, `git log --grep` cho việc đã làm);
lỗi 97 sống 3 giờ vì bỏ qua bước này. Và **nêu ĐƯỜNG đã thử, đừng nêu MỤC
TIÊU**: "`file_upload` không dùng được vì trang không có ô nhập file" đúng
mãi; "không nạp được nguồn" sai ngay khi có đường thứ hai.

---

## Bước 2 — Sửa: MỘT đường duy nhất

```python
import sys; sys.path.insert(0, "tools")
from va_an_toan import thay, dot_bien
thay("paper_metrics.py", "N_TOI_THIEU = 113", "N_TOI_THIEU = 120")
```

`tools/va_an_toan.py` đọc/ghi ở **chế độ văn bản**, neo viết bằng `\n`, neo
phải khớp **đúng một lần** hoặc nổ, ghi qua file tạm rồi đổi tên. **KHÔNG
tự viết neo theo byte** (5/11 lỗi một ngày). Luật "giữ CRLF" cũ đã bị bác:
trong index toàn file là LF, quy ước xuống dòng trên đĩa không ảnh hưởng
thứ được commit.

**Suy ra, đừng gõ.** Một ngưỡng gõ tay ở hai chỗ sẽ trôi ra khỏi nhau.

---

## Bước 3 — Đột biến mọi gác mới. VÒNG LẶP, không phải một lượt

```python
dot_bien("paper_metrics.py", "z=2,30", "z=1,00",
         ["-m", "pytest", "tests/test_dieu_kien_dung_alpha.py", "-q"])
```

**Lặp cho tới khi MỌI đột biến đều đỏ.** Một phát sống sót là câu trả lời:
gác chưa canh chỗ đó. Sửa gác rồi chạy lại cả bộ. Nhưng trước khi sửa gác,
hỏi phát ấy có THẬT SỰ đổi hành vi ở chỗ đang canh không (phát thiết kế sai
cũng sống sót). Lượt đục **không được để rác**: `va_an_toan.kiem_khong_de_rac()`
nổ và gọi tên mục mới ở gốc repo — xoá tay rồi thiết kế lại, đừng tắt gác.

Bốn điều bắt buộc:

1. **Phép đục đi qua đúng HÀM ĐANG PHÁN**, không qua hàm trích.
2. **Phát đầu tiên: dựng lại nguyên văn lỗi thật.** Gác có bắt được đúng
   thứ nó sinh ra để bắt không.
3. **Gác một phép SUY RA thì kiểm HÌNH DẠNG biểu thức bằng AST**, không
   kiểm giá trị nó cho ra (giá trị trùng tại một điểm là chuyện thường).
4. **MÁY ĐO cũng phải bị nghi ngờ như GÁC** — một gác sai thì ĐỎ, còn một
   máy đo sai chỉ **in ra một con số** (lỗi 61: năm máy đo liên tiếp hẹp hơn
   thứ chúng đo, cả năm cho con số nghe hợp lý). Thói quen đã cứu:
   - **In DỮ LIỆU THÔ ngay dưới con số** (lượt quét chỉ in `0` gần thành
     kết luận "quần thể rỗng", trong khi hai ca nằm ngay trong bản in thô).
   - **Bắt máy đo đi qua một ca THẬT đã biết trước.**
   - **Trước khi tin kết quả ÂM, hỏi: mẫu này CÓ KHẢ NĂNG cho kết quả DƯƠNG
     không?** (lỗi 66: vốn đỉnh 99,9 không bao giờ chạm phép thử `> 100`).
   - **NỀN NHIỄU của một phép hiệu chuẩn phải cùng TÍNH CHẤT THỐNG KÊ với
     thứ nó hiệu chuẩn, VÀ phải RỜI khỏi nhãn** (lỗi 94): nền trắng thì null
     hẹp hơn thật; nền là chính cột thật thì ô "không tiêm gì" đo lại chính
     nó; đúng là cột thật DỊCH VÒNG trong từng mã. Giữ đủ ô "không tiêm gì".
   - **Hỏi phép đo có đi qua một BẢN GHI NHỚ nào không** (lỗi 75): năm
     payload cùng `session_id` chạm nhánh "đã bơm rồi" → 110 ms thay vì 410
     ms. Đổi khoá của mọi bản ghi nhớ giữa các lượt.
   - **Một phán quyết về LỰC phải là một TỶ LỆ, không phải một lượt rút**
     (lỗi 99): một lượt tiêm ở nhịp biên là đồng xu 70/30; lặp 30 lần bắt
     21/30.

Ba mẫu hay sống sót nhất và các bẫy khác: `references/bay.md`.

---

## Bước 4 — Năm cổng gác, ĐÚNG THỨ TỰ, KHÔNG song song

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/kq.log 2>&1
./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py
./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo
./.venv/Scripts/python.exe tools/kiem_test_chay_rieng.py --im
./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py
```

Cổng 5 đo thứ **BỊ MẤT** (bốn cổng đầu đo thứ đang có; một lệnh `cat >` đè
mất 40 phép kiểm trong khi cả bốn cổng XANH). Nó không cấm giảm (gộp test
trùng hợp lệ) mà buộc khai lý do: `--cap-nhat --ly-do "<vì sao>"`. **Thêm
test cũng phải cập nhật mốc** (mốc trôi tụt lại là lỗ hổng tăng dần).

- Vài test ghi thư mục tạm vào gốc repo → chạy song song cho **đỏ giả**.
- Mã thoát **2** của cổng 2 và 4 là *chưa kiểm được*, không phải sạch.
- `PYTHONIOENCODING=utf-8` cho mọi lệnh có tiếng Việt. **Ghi ra file log,
  đừng pipe qua `tail`** (đệm hết output; và mã thoát của ống là của `tail`,
  luôn 0 — `&&` đi tiếp dù pytest đỏ). Đừng sửa file khi một lượt chạy đang
  bay. Chi tiết: `references/cong-thuc-chay.md`.
- Số cổng là con số đếm thứ có thật nên nó trôi:
  `tests/test_bo_cong_khop_CI.py` suy danh sách từ `.github/workflows/kiem-dinh.yml`.
- **Sửa `SKILL.md` hay `references/` thì chạy MỘT file này TRƯỚC** (11 giây):
  `./.venv/Scripts/python.exe -m pytest tests/test_skill_quy_trinh.py -q`
  Nó bắt tên file viết TRẦN thiếu tiền tố thư mục (git không biết cái tên
  ấy). **KHÔNG viết tên file trần ra đây làm ví dụ** — ghi chú cảnh báo lỗi
  ấy tự chứa nó và từng làm đỏ ba lượt cổng, mỗi lượt ~9 phút.

---

## Bước 5 — Giao

- **KHÔNG đẩy thẳng `main`** — nhánh → PR. `main` có ruleset active từ
  21/08/2026 (bắt PR, bắt `kiem-dinh` xanh strict, cấm force-push và xoá);
  `.github/workflows/kiem-dinh.yml` chạy cả trên `push` nên đẩy thẳng thì CI chạy SAU cánh cửa.
- **Tự merge được** (người dùng chốt 08/09/2026) khi đủ **cả ba**:
  (1) **năm** cổng ở Bước 4 xanh tại máy; (2) **MỌI** check của PR `pass`
  — mỗi PR có HAI dòng `kiem-dinh`, dòng sau hay còn `pending`, đọc một
  dòng rồi merge là merge khi CI chưa xong; (3) không còn câu hỏi chờ người
  dùng.

  ```bash
  gh pr checks <so>          # doc HET, dung doc dong dau
  gh pr merge <so> --merge --delete-branch
  gh pr view <so> --json state,mergeCommit
  ```

- **Merge xong phải KIỂM, không tin mã thoát:** `pr view` cho `state=MERGED`
  và mã băm hợp nhất, rồi `git pull` + tìm nội dung vừa thêm trong `main`.
- Commit body **ASCII**, và **CÓ** `Co-Authored-By` (đo 23/09: 80/100 commit
  không merge từ 09/09, quy ước đổi từ 12/09). **Kiểm bản ĐÃ GHI** (lỗi 93):
  `git log -1 --format=%B` rồi tìm ký tự ngoài ASCII bằng Python; `grep`
  thành công khi TÌM THẤY, tức mã thoát 0 đúng lúc muốn dừng.
- Ghi vào `docs/STATE.md` cả **kết quả lẫn giả thuyết bị bác** và **ước lượng
  đã sai** — giả thuyết sai nghe hợp lý là thứ đáng giữ nhất.

---

## Bước 6 — Cập nhật chính file này (bắt buộc)

Mỗi lỗi mới → thêm một dòng vào `references/loi-da-mac.md`, rồi hỏi: **máy
chặn được không?** Được thì thêm luật vào `tools/cua_bash_an_toan.LUAT` hoặc
một cổng mới, kèm test. Luật mới phải **khai nguồn** (ngày sự cố, hoặc
`CHƯA CÓ SỰ CỐ` kèm tên file quy ước); gác:
`tests/test_cua_quy_trinh.py::test_moi_luat_deu_khai_NGUON`.

**Giữ skill gọn:** lý do dài, số đo và sự cố của một luật đi vào
`references/loi-da-mac.md` hoặc `docs/STATE.md`, KHÔNG vào file này. Một
BƯỚC không sửa `SKILL.md` trừ khi nó đổi một LUẬT.

---

## Cửa tự động — KIỂM TRƯỚC KHI TIN

```bash
./.venv/Scripts/python.exe tools/kiem_cua_song.py
```

Nó so bản khai `docs/cua-du-an.json` với `~/.claude/settings.json` và gọi
tên từng cửa chưa được chép (mã thoát 0 đủ · 1 thiếu · 2 chưa kiểm được).
**Bảy cửa chỉ đăng ký ở MỘT nơi**, `~/.claude/settings.json`, đường dẫn
tuyệt đối — bản trong repo khai cùng lúc thì mỗi hook chạy HAI LẦN (đo
10/09/2026, khoá bởi `tests/test_cua_song.py::test_settings_CUA_REPO_khong_duoc_dang_ky_hook_nao`).

| Cửa | Khi nào | Làm gì |
|---|---|---|
| `tools/cua_mo_phien.py` | SessionStart | nhắc gọi skill · mốc ngày đang chặn · dòng `CUA: n/m song` |
| `tools/cua_doc_bat_buoc.py` | Pre · Read/Write/Edit | chưa đọc tài liệu bắt buộc thì chặn sửa file ảnh hưởng kết quả |
| `tools/cua_bash_an_toan.py` | Pre · Bash\|PowerShell | chặn hình dạng lệnh đã cắn thật |
| `tools/chan_bia_so_lieu.py` | Post · Write/Edit | quét mẫu bịa số liệu |
| `tools/cua_ghi_an_toan.py` | Post · Write/Edit | file còn 0 byte sau lượt ghi |
| `tools/chan_bia_so_lieu.py --quet-thay-doi` | Stop | soát lại file đã đổi |

- **`python --version` KHÔNG phải phép thử của cả bảy** (lỗi 25): nó đi qua
  đúng MỘT hook, cửa Bash. Một phép thử đo MỘT cửa không phải phán quyết về
  bảy.
- Hook mới chỉ có hiệu lực từ **PHIÊN SAU**. Hook không thấy gì đi qua Bash
  trừ cửa Bash. Thêm cửa lên toàn cục thì bơm payload giả từ một cwd ngoài
  repo TRƯỚC (lỗi 15: công cụ đúng trong repo có thể sai khi gọi từ nơi khác).

---

## Luồng thông tin thứ hai — NotebookLM

Người dùng chốt 10/09/2026: dùng thường xuyên nhưng **không dựa hoàn toàn**
vào nó. Giá trị là một luồng **độc lập** — đọc tài liệu mà không mang theo
giả định của phiên này. Thao tác: `references/soat-cheo-notebooklm.md`.

**Dùng khi:** trước một phép đo lớn (soát tiêu chí đã khai); sau khi viết một
kết luận (tìm chỗ nói ngược); khi tài liệu dài đã bị vá nhiều lần.

**Ba giới hạn, và nó lớn:**
1. **Nó chỉ thấy TÀI LIỆU, không thấy MÃ.** Loại lỗi nặng nhất (tài liệu lệch
   mã: `N_DAY_DU` 596/451, cờ C5) nó không bắt được cái nào.
2. **Mọi phát hiện phải tự kiểm lại** bằng `grep` hoặc đọc mã.
3. **Nó không thay được Quy tắc 2.**

Nói đúng trong báo cáo: *"NotebookLM chỉ ra chỗ X, tôi kiểm lại bằng
<lệnh> và nó đúng/sai"*, không *"theo NotebookLM thì X"*.

**Luật hỏi (mỗi cái từ một lượt bịa thật):**
- **Mọi câu gửi phải mang LỐI THOÁT tường minh** (*"If that file is NOT among
  your sources, say exactly that and do not guess."*). Thiếu nó, sổ tay BỊA
  cả trích dẫn lẫn tên file; con số đúng bọc trong bằng chứng bịa là hình
  dạng khó thấy nhất. Hỏi một DÒNG thì lối thoát phải nói *"nếu không tìm
  thấy dòng ấy"* — phủ đúng cái đang hỏi, không phủ cái chứa nó.
- **Ngôn ngữ:** hỏi bằng **TIẾNG ANH**, mỗi câu kèm dòng `Answer in
  Vietnamese.` (chốt 17/09/2026, lý do người dùng chưa nêu). Báo cáo,
  `phat_hien`, `phan_quyet` vẫn tiếng Việt; trích dẫn tài liệu giữ tiếng
  Việt. `cau_hoi` trong sổ ghi NGUYÊN VĂN câu đã gửi.
- **Đối chiếu trích dẫn bằng dụng cụ, đừng tự `grep`:**
  `./.venv/Scripts/python.exe tools/doi_chieu_trich_dan.py "<trích dẫn>"`
  (0 khớp · 1 lệch · 2 chưa kiểm được). Sổ tay lột dấu nhấn Markdown, dấu
  `> ` blockquote và ngắt dòng cứng — `grep` một dòng vu oan 4/15 câu thật.
  Nó cũng nói lệch từ ký tự thứ mấy.
- **Sổ tay có thể trích đúng chữ nhưng SAI TÊN FILE** (BƯỚC 119); dụng cụ
  in cả tên file. Một dấu 🔴/`~~` ở cấp MỤC không phủ từng câu trong mục.
- **Câu ÂM cũng phải kiểm** (*"không tìm thấy"* từng sai hai lần): `grep` từ
  khoá tiếng Việt của chính dự án sau mọi câu âm. Lối thoát chặn nó BỊA, không
  chặn nó BỎ SÓT.
- **Ô thoát đòi lý do cụ thể vẫn có thể thành câu thần chú** (lỗi 86: sáu mục
  liên tiếp viện dẫn cùng một phát hiện đúng). Chuỗi bỏ qua là một đại lượng
  — bản tin mở phiên nói ra từ 3 mục trở lên (`tools/cua_mo_phien.chuoi_khong_soat()`).
  Gác so chữ đã đo và bỏ: sáu lời khai ấy giống nhau *ít hơn* mức trung bình.

**Đo độ tươi TRƯỚC mỗi lượt hỏi**, không nhớ từ lượt trước: hỏi *"số BƯỚC lớn
nhất trong các nguồn"* (kèm lối thoát) rồi so `grep -c '^## BƯỚC' docs/STATE.md`.
Phép BỎ CHỌN nguồn không sống qua phiên. Lệch thì làm tươi — **THÊM TRƯỚC, XOÁ
SAU** (xoá trước có một cửa sổ sổ rỗng; bản trùng còn làm sổ trả lời SAI:
BƯỚC 95 thay vì 96). Nguồn là URL `raw.githubusercontent.com/…/<mã băm 40 ký
tự>/<file>` (ghim băm, tránh CDN chậm một commit), đổi tên nguồn thành
`<file> @<7 ký tự băm>`, nhắm nút xoá theo tham chiếu cây trợ năng chứ không
theo pixel, và đọc **nhãn** trên hộp xác nhận. Cách làm chi tiết ở
`references/soat-cheo-notebooklm.md`.

**Xoá nguồn:** hỏi người dùng trước (xoá là vĩnh viễn) — **TRỪ** bản trùng
của đúng nguồn vừa dán lại ở bước THÊM. Không có gác máy cho luật này (thao
tác trình duyệt không để dấu vết trong repo); đây là kỷ luật, không phải cơ chế.

**Nguồn của sổ tay gồm cả `docs/lich-su/*.md`** (từ BƯỚC 150) — quần thể
`tools/doi_chieu_trich_dan.py` phủ chúng, để trích dẫn từ bản nguyên văn cũ
vẫn đối chiếu được.

### Nhịp soát định kỳ (2 ngày)

Cập nhật đã chạy theo sự kiện (Bước 6); nửa chưa có cơ chế là **soát lại thứ
ĐÃ CÓ**:

```bash
./.venv/Scripts/python.exe tools/soat_loi_khai_cu.py
./.venv/Scripts/python.exe tools/kiem_duong_ngoai_repo.py
```

Cái đầu in mọi **lời khai phủ định có nêu tên** còn sống trong các tài liệu
(quét theo họ từ `PHU_DINH` — *không nhập · gọi · dùng · chạm* nằm trong đó,
*không đọc · có · còn* cố ý ngoài; đọc con số bằng lệnh, đừng ghim). Ghi kết
quả vào `docs/soat-dinh-ky.json`; *"vẫn đúng"* là kết quả hợp lệ. Cái thứ hai
bắt con trỏ ngoài repo đã chết; nó **cố ý không phải một cổng** (đường nằm ở
thư mục nhà của máy này nên trên CI sẽ đỏ mọi lượt) — nhưng kết quả của nó
vẫn vào sổ, ô `duong_ngoai_repo` (lỗi 117: ba lượt bỏ trống). Giữ một đường
đã chết: `<!-- duong-da-chet: <lý do> -->` ở CUỐI chính dòng ấy; dòng trong
`docs/lich-su/` tự là sử liệu.

---

## Ranh giới không vượt qua

- **Không đặt lệnh thật.** Agent chuẩn bị → người xác nhận → người đặt lệnh.
- Không commit secrets, `*.db`, `sl_pattern_memory.json`, `backtest/cache/`.
- **Không xoá file `*.db` ở gốc repo** — dữ liệu đo của người dùng. Hỏi trước.
- Không ép hạng vnstock trong mã nguồn. Không ghi tài liệu skill của vnstock
  ra đĩa (giấy phép cấm).
- App không được tự push lên repo nó đang chạy.
- **Không đọc dữ liệu đã khai trước trước ngày đã hẹn** (`docs/HANDOFF.md`
  mục 5).
