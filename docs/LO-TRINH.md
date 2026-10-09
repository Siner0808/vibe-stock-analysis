# LỘ TRÌNH — hai đích, năm giai đoạn

**Người dùng duyệt khung ngày 08/10/2026** (câu trả lời nguyên văn ở mục
*Quyết định*). Bản này chép NỘI DUNG trang leader trình ngày ấy; giai đoạn A
bắt đầu từ BƯỚC 164. Mã mốc (`A1`, `B2`, `H1`…) là địa chỉ để mỗi BƯỚC trỏ tới:
từ BƯỚC 164, mục BƯỚC trong `docs/STATE.md` phải có một dòng `**Mốc:** <mã>`
(hoặc `**Mốc:** quy-trinh — <lý do>` cho việc quy trình thuần). Gác:
`tests/test_moc_lo_trinh.py`.

> **Luật của file này (cùng luật HANDOFF): KHÔNG ghim con số sẽ trôi.** Ngày
> và điều kiện ra của giai đoạn là QUYẾT ĐỊNH (ổn định). Số đo thì có NGÀY và
> LỆNH tái lập kèm theo, hoặc được gọi thẳng là ƯỚC LƯỢNG. Phần *Ý tưởng* là
> ĐỀ XUẤT CHƯA ĐO.

Sửa file này là sửa một LUẬT: nó nằm trong danh sách file luật của Quy tắc 3
(`tools/buoc_cham_luat.py`), nên BƯỚC nào chạm nó phải hỏi sổ tay thật.

---

## Quyết định (nguyên văn trả lời của người dùng, 08/10/2026)

Hộp hỏi ở phiên leader. Mỗi dòng: câu hỏi → câu trả lời **nguyên văn**.

| Câu hỏi | Trả lời |
|---|---|
| Khung lộ trình "hai đích + năm giai đoạn" | *"duyệt"* |
| Giảm phần việc quy trình: soát tự động mỗi tuần, chỉ hỏi NotebookLM cho những BƯỚC đổi kết luận đo hoặc đổi luật | *"Đồng ý"* |
| Khoá Claude API | *"Để tới giai đoạn B (Recommended)"* — chưa đặt; không BƯỚC nào của giai đoạn A làm gì về khoá |
| Bắt đầu giai đoạn A | *"Làm ngay"* |

## Quyết định (nguyên văn trả lời của người dùng, 09/10/2026)

Phiên quyết định A5, hộp hỏi ở phiên leader (BƯỚC 166). Mã Q trỏ vào `docs/QUYET-DINH-CHO.md`.

| Mã | Câu hỏi | Trả lời |
|---|---|---|
| Q1 | Đường quét thật có nạp 44 mẫu bộ nhớ không | *"Giữ 0 mẫu (Recommended)"* |
| Q2 | Vế 3 của điều kiện dừng | *"Giữ tạm, sửa ở GĐ C (Recommended)"* — giữ luật hiện tại; giai đoạn C thiết kế lại thành "lùi về phiên bản trước" thay vì ngừng đặt lệnh, chốt bằng văn bản trước khi sổ đủ mẫu (mốc **C6** dưới đây) |
| Q3 | Địa chỉ app Streamlit Cloud | người dùng đưa URL; **cố ý không lưu trong repo công khai** (app dùng khoá API trả phí của người dùng) |
| Q4 | Mã thiếu giá thì từ chối cả bảng | *"Chờ số đếm thật (Recommended)"* |
| Q5 | `luu_do18` / `luu_do20` | *"Xoá cả hai (Recommended)"* (02/10/2026), xác nhận lại *"Đưa lại vào Thùng rác"* (09/10/2026) |
| Q6 · Q8 | `vnii` gửi `operation` · báo lỗi `vnstock_ezchart` | *"Theo đề xuất cả hai (Recommended)"* |
| Q7 | Dữ liệu BCTC trong repo công khai | *"Tôi đọc điều khoản rồi báo (Recommended)"* — vẫn CHỜ |
| Q10 (A4) | Tách `docs/STATE.md` theo tháng | *"Không tách (Recommended)"* |

---

## Hai đích

Hai đích chạy theo hai nhịp khác nhau; gộp chúng vào một là lý do dự án trông
như không có đích. Đích 1 ta tự quyết được ngày về. Đích 2 do dữ liệu quyết nhịp.

### Đích 1 — "máy học được", v1.0 vào **28/02/2027**

Agent tự giao dịch ảo, tự rút bài học, minh bạch. Nghiệm thu bằng bảy tiêu chí
đo được:

- **T1** — Chạy tự động 20 phiên liền, không ai phải can thiệp.
- **T2** — Mọi lệnh đóng có bài học bằng lời và nhãn nguyên nhân trong vòng 1 phiên.
- **T3** — Bản tin cuối ngày của agent tới tay người dùng.
- **T4** — Sân đấu có ít nhất 3 phương án bóng so với rổ, kèm khoảng tin cậy.
- **T5** — Agent tự soạn ít nhất 1 đề xuất ứng viên mỗi tháng; người dùng duyệt một chạm.
- **T6** — Vòng học đã chứng minh trên thị trường giả có lợi thế cài sẵn: nó tìm ra, xác nhận và nâng cấp đúng.
- **T7** — Việc quy trình chiếm tối đa 1/3 số BƯỚC mỗi tuần.

### Đích 2 — "có lợi thế thật", phán quyết đầu tiên **≈ đầu tháng 11/2027** (ƯỚC LƯỢNG)

Trang đã duyệt ghi **03/11/2027**; cách đếm của mã cho **04/11/2027** (mục dưới).
Một phiên chênh nằm trong sai số của một ước lượng dựa vào lịch nghỉ chưa công
bố. Dữ liệu quyết nhịp; đẩy nhanh hơn thì phá kỷ luật đo. Hai đồng hồ dữ liệu:

- **H1** — UV-001 (`docs/ung-vien.json`) được đọc đúng MỘT lần, ở phiên có nhãn
  thứ `cham_bong.MOC_DOC`. Nhãn của phiên T cần giá tới T+22 (`cham_bong.NHIP` + 1),
  nên cần `MOC_DOC` + `NHIP` + 1 phiên giao dịch kể từ ngày khai 02/10/2026.
- **H2** — Điều kiện dừng C5 cần `paper_metrics.N_TOI_THIEU` lệnh đóng mới kết
  luận được. Nhịp vào lệnh chưa ổn định, nên mốc này là một **khoảng ƯỚC LƯỢNG
  rộng** (leader ước: từ quý 1/2027 tới quý 1/2028), không phải một ngày.

Kỳ vọng thật lòng: bản khai UV-001 ghi kết cục hợp lý là `DANG CHAM`, chưa phải
`QUA`. Đích 2 có thể kết thúc bằng "họ tín hiệu này không có lợi thế" — đó là một
kết quả hợp lệ, và là lý do Đích 1 phải đứng được độc lập.

**Ngày đầu tháng 11/2027 là ƯỚC LƯỢNG, và cách tính lại** (đo 08/10/2026):

```bash
./.venv/Scripts/python.exe -c "import lich_giao_dich as l, cham_bong as cb; print(len(l.cac_phien('2026-10-01','2026-12-31')), cb.MOC_DOC + cb.NHIP + 1)"
```

In **65 274**: 65 phiên từ 02/10 tới hết 2026 (`cac_phien` loại ngày đầu nên mốc
là `2026-10-01`), và 274 = 252 + 21 + 1 phiên cần. Còn 274 − 65 = **209 phiên của
năm 2027**. Hàm của app, `cham_xac_nhan.tien_do_theo_lich("2026-10-02", "2026-12-31")`,
cho cùng 65 phiên lịch và 43 phiên có nhãn (= 65 − 22), khớp con số 274.

**Chỗ lệch với trang đã duyệt:** trang ghi 273 phiên ("252 phiên có nhãn + 21 phiên
nhãn") và 208 phiên của 2027, tức đếm NHIP mà quên cộng 1 (nhãn dùng giá T+1 tới
T+22, `nhan_vuot_ro`). Một phiên — nhưng đây là một **ước lượng đã sai** nhỏ, ghi
lại để không ai tính lại từ 273.

Lịch nghỉ 2027 CHƯA công bố (`lich_giao_dich.PHU_TOI` là `2026-12-31`). Giả định
của leader để ra ngày: **11 ngày nghỉ trong tuần** (1/1; năm ngày Tết Nguyên đán
04–05/02 và 08–10/02; Giỗ Tổ 16/04; 30/04; 03/05 bù 01/05; 02–03/09) — SUY ĐOÁN,
không phải lịch của Sở. Với giả định ấy, phiên thứ 209 của 2027 rơi vào
**04/11/2027** (phiên thứ 208, ngày trang đã duyệt: 03/11/2027). Không có ngày nghỉ
nào thì rơi vào 20/10/2027. Khi Sở công bố lịch 2027 (thường cuối 2026): thêm ngày
nghỉ vào `lich_giao_dich.NGAY_NGHI`, nới `PHU_TOI`, rồi đếm lại bằng chính hàm trên.
Tab *Kiểm định chiến lược* của app sẽ hiện "chưa tính được" từ 01/01/2027 nếu không
làm (`docs/STATE.md` BƯỚC 162).

---

## Chẩn đoán — vì sao làm mỗi ngày mà không thấy đích

Số đo ngày **08/10/2026**; mỗi dòng ghi lệnh. Số nào phiên viết file này không
chạy lại được thì nói thẳng.

1. **Thứ đo được đang trả lời KHÔNG.** Điểm cuối không dự báo được lợi nhuận;
   walk-forward theo ngày với trượt giá BẬT loại được số 0 và âm; ba nguồn dữ liệu
   độc lập đã đo xong, không nguồn nào vượt rào phí. Số cụ thể nằm ở bảng ĐO 22
   và mục *Trạng thái đo được* của `CLAUDE.md` (đó là bản ghi các ĐO đã hoàn
   thành, không phải số tính lại hôm nay).
2. **Agent chưa học gì trên đường chạy thật.** Bộ nhớ hậu nghiệm có 0 mẫu ở mọi
   lượt quét CI đã đếm (`docs/STATE.md` BƯỚC 140). Nhật ký "vì sao" đã ghi nhưng
   chưa có bước rút bài học: P2c chờ khoá API do người dùng tự đặt. Một vòng xác
   nhận của tầng 3 phán MỘT lần ở phiên có nhãn thứ 252, tức khoảng 13 tháng kể
   từ ngày khai (ƯỚC LƯỢNG: 274 phiên ÷ ~21 phiên/tháng).
3. **Quy trình đang lấy phần của sản phẩm.** Phần dòng thêm vào repo là mã sản
   phẩm, 30 ngày tới 08/10/2026:

   ```bash
   git log --since=2026-09-08 --until=2026-10-09 --no-merges --numstat --format= | awk -F'\t' '$1 ~ /^[0-9]+$/ { f=$3; if (f ~ /^\.claude\//) k="skill"; else if (f ~ /^docs\// || f ~ /\.md$/) k="tai_lieu"; else if (f ~ /^tests\//) k="test"; else if (f ~ /^tools\//) k="cong_cu"; else if (f ~ /^\.github\//) k="workflow"; else if (f !~ /\//) k="ma_goc"; else k="khac"; s[k]+=$1; t+=$1 } END { for (k in s) printf "%s %d %.1f%%\n", k, s[k], 100*s[k]/t; print "tong", t }'
   ```

   Ra (phiên viết file này, trên cây `0a991e1`): `ma_goc` 4086 dòng = **6,3%** của
   65.077; `tai_lieu` 41,3%; `test` 30,0%; `cong_cu` 18,2%; `skill` 4,1%. Cách gom
   (thư mục đầu; `ma_goc` = file ở gốc repo) là cách của phiên này; trang leader
   trình cho cùng 6,3% với tỷ lệ `tai_lieu` 38,8%, nên cách gom của hai bên
   khác nhau ở phần tài liệu, không ở phần mã sản phẩm.
4. **Sổ tay NotebookLM bắt được ít dần.** Mục BƯỚC có `cau_hoi` và ít nhất một
   phán quyết mở đầu `THẬT` (đo 08/10/2026, cây `0a991e1`):

   ```bash
   ./.venv/Scripts/python.exe tools/so_tay.py dem --tu 1 --den 129
   ./.venv/Scripts/python.exe tools/so_tay.py dem --tu 130 --den 162
   ```

   Ra **25/30** cho BƯỚC ≤ 129 và **6/33** cho BƯỚC 130–162. 22 trong 33 mục
   gần đây trả "không tìm thấy" (`khong_tim_thay_gi`), và câu "không tìm thấy" đã
   sai nhiều lần — `grep` mới bắt được (`docs/STATE.md` BƯỚC 127, 160, 162, 163).
   `docs/STATE.md` nặng khoảng 1,2 MB: `git show origin/main:docs/STATE.md | wc -c`
   ra 1.206.210 lúc đo.
5. **Phiên 08/10 KHÔNG tái lập được hai số của leader**, vì đề bài cấm đọc sổ
   lệnh/Sheets: *"9 lệnh ảo đã đóng trên 113 cần cho C5"* (leader đo bằng
   `tools/doc_so_that.py`) và *"UV-001: 5 phiên đã qua trên 273"*. Số sau đếm lại
   được từ lịch, không cần sổ: 5 phiên giao dịch THEO LỊCH từ 02/10 tới 08/10
   (gồm 08/10, chưa kiểm nến đã đóng; `cham_xac_nhan.tien_do_theo_lich("2026-10-02", "2026-10-08")`
   ra 5 phiên lịch và 0 phiên có nhãn) — và mẫu số đúng là 274, không phải 273 (mục
   Đích 2). Số trước vẫn là số của leader, chưa tái lập trong phiên này. Không chép
   lãi hay lỗ của lệnh tiến-về-trước vào đây (bất biến 7).

**Thứ đã làm đúng và phải giữ:** kỷ luật đo đã chặn năm con số đẹp giả (lớn nhất
+636,11%); sổ ảo trung thực chạy từ 28/09; tầng 3 đã ký trước đầy đủ (UV-001, mốc
đọc, máy chấm, bộ kéo giá). Đây là nền móng; phần nhà bên trên còn mỏng.

---

## Năm giai đoạn

Làn trên là việc của ta (A→E). Làn dưới là đồng hồ dữ liệu (H1, H2), chạy song
song và không đẩy nhanh được. **Mốc sản phẩm** = mọi mã trừ nhóm A và `quy-trinh`.

### A — Dọn đường (giảm thuế quy trình) · 09/10 → 25/10/2026

- **A1** — `docs/LO-TRINH.md` vào repo; mỗi BƯỚC khai mốc nó phục vụ, có gác kiểm. *(BƯỚC 164)*
- **A2** — Soát định kỳ: từ nhịp 2 ngày sang nhịp 7 ngày; phần máy làm được chạy
  tự động hằng tuần trên CI (`.github/workflows/soat-tuan.yml`), phần PHÁN lời khai
  vẫn là lượt soát của agent. *(BƯỚC 164)*
- **A3** — NotebookLM chỉ bắt buộc cho BƯỚC đổi một luật hoặc một kết luận đo
  (người dùng duyệt 08/10); BƯỚC khác khai vì sao không hỏi. *(BƯỚC 164)*
- **A4** — ~~Tách `docs/STATE.md` theo tháng, giữ một mục lục.~~ **ĐÃ BỎ 09/10/2026** (Q10, người dùng: *"Không tách (Recommended)"*). *(Nếu sau này làm lại: phải đổi `moc_lo_trinh.TEP_STATE` — gác `tests/test_moc_lo_trinh.py` đòi quần thể khác rỗng nên sẽ đỏ nếu quên.)*
- **A5** — Dọn hàng đợi quyết định đang chờ người dùng: 44 mẫu bộ nhớ trên đường
  thật · vế 3 điều kiện dừng · URL Streamlit Cloud · "mã thiếu giá thì từ chối cả
  bảng" · giữ hay xoá `scratch/luu_do18`. *(danh sách của leader 08/10; BƯỚC 165 dựng sổ `docs/QUYET-DINH-CHO.md`, BƯỚC 166 ghi quyết định 09/10/2026: đã quyết Q1–Q6 · Q8–Q10; còn CHỜ Q7, Q11, Q12)*

**Ra khỏi giai đoạn khi:** ít nhất 2/3 số BƯỚC mỗi tuần phục vụ một **mốc sản
phẩm**. Đo bằng cách đọc dòng `**Mốc:**` của các BƯỚC trong tuần
(`grep -n '^\*\*Mốc:\*\*' docs/STATE.md`, ngày nằm ở tiêu đề BƯỚC); chưa có công
cụ đếm, và chưa có tuần nào đủ dữ liệu.

### B — Agent biết nói (hoàn tất tầng 2) · 26/10 → 30/11/2026

- **B1** — P2c: hậu kiểm bằng lời cho mọi lệnh đóng. *(cần khoá `ANTHROPIC_API_KEY` do người dùng tự đặt, có trần chi tiêu; người dùng đã hoãn tới đầu giai đoạn B)*
- **B2** — Bản tin cuối ngày: thị trường, agent đã làm gì, vì sao, học được gì.
- **B3** — Sổ bài học với nhãn nguyên nhân: thị trường chung, ngành, tín hiệu sai, cắt lỗ sát, gap. *(ĐÃ DỰNG 09/10/2026, sớm hơn lịch giai đoạn B: BƯỚC 167 `so_bai_hoc.py` — mỗi lệnh ảo đã đóng có một bài học CHỈ ĐỌC, phân rã bốn phần thị trường + ngành + riêng mã/tín hiệu + chi phí, kèm cờ gap và cắt lỗ sát; BƯỚC 168 sửa nút tải giá; BƯỚC 169 chuông đo tiêu chí ra khỏi B. Còn mở hai câu hiệu chuẩn ở `docs/STATE.md` BƯỚC 167: giữ bốn phần hay ba, `so_bai_hoc.N_PHIEN_SAU_THOAT` = 5 có hợp lý không.)*
- **B4** — Bảng sức khoẻ hệ thống thay cho phần lớn soát tay.

**Ra khi:** 100% lệnh đóng có bài học trong vòng 1 phiên. *(Đo hằng ngày từ BƯỚC 169: `tools/chuong_bai_hoc.py`, workflow `chuong-bai-hoc.yml`, đỏ = email. Quần thể là lệnh tiến-về-trước đã đóng, mở từ `so_bai_hoc.NGAY_NHAT_KY_BAT_DAU`; lệnh mở trước nhật ký không tính và không điền bù — Q13 ở `docs/QUYET-DINH-CHO.md`, chờ người dùng. Hạn tính theo PHIÊN giao dịch. "Có bài học" của chuông hiện là nửa ĐÓNG của nhật ký + phân rã được, tức phần NHÃN; vế "bằng lời" mà T2 đòi cần B1 và chuông CHƯA đo.)*

### C — Sân đấu phương án → v1.0 · 01/12/2026 → 28/02/2027

- **C1** — Nhiều phương án bóng chạy song song, mỗi phương án một tài khoản ảo riêng.
- **C2** — Tách hai loại: "thăm dò" (không tính K, không bao giờ lên bản) và "xác nhận".
- **C3** — Agent tự soạn đề xuất ứng viên hằng tháng: lập luận, bản tiền đăng ký, ước lực; kèm cổng khả thi loại ứng viên mà IC hoà vốn cần có vượt trần IC đã đo của nguồn nó dùng.
- **C4** — Thị trường giả có lợi thế cài sẵn, để chứng minh cả vòng học chạy đúng.
- **C6** — Thiết kế lại vế 3 của điều kiện dừng thành "lùi về phiên bản trước" thay vì ngừng đặt lệnh (người dùng 09/10/2026, Q2). Phải chốt bằng văn bản TRƯỚC khi sổ thật chạm `paper_metrics.N_TOI_THIEU` lệnh tiến-về-trước đã đóng; sau mốc ấy mọi thay đổi bị nghi là chế điều kiện sau khi nhìn số (bất biến 7). Mã bỏ qua `C5` vì trùng tên cổng C5.

**Ra khi:** đủ bảy tiêu chí T1–T7 của Đích 1.

### D — Nguồn mới, vòng quay thấp · 01/03/2027 → 30/09/2027

- **D1** — Lịch sự kiện: ngày giao dịch không hưởng quyền, kỳ review ETF, ngày công bố kết quả kinh doanh.
- **D2** — Điều chỉnh giá theo sự kiện quyền. ĐO 24 nghi SSI lệch hệ số 1,25 và MBB 1,20 (`docs/STATE.md` mục chẩn đoán sau kết cục ĐO 24); đó là SUY LUẬN, CHƯA KIỂM.
- **D3** — Ứng viên vòng quay thấp: giữ tối thiểu N phiên, thoát theo thời gian thay vì cắt lỗ sát.
- **D4** — Chế độ "bạn so với agent".

**Mốc giữa kỳ:** C5 có thể chạm `paper_metrics.N_TOI_THIEU` lệnh đóng; đọc lần đầu đúng luật.

### E — Phán quyết · 01/10/2027 → 31/12/2027

- **E1** — Đọc UV-001 đúng MỘT lần (≈ đầu tháng 11/2027, ƯỚC LƯỢNG — mục Đích 2).
- **E2** — Kịch bản xanh: agent tự áp dụng và báo người dùng ngay; bàn thêm chế độ gợi ý lệnh thật (agent chuẩn bị, người dùng xác nhận và tự đặt — dự án KHÔNG đặt lệnh thật).
- **E3** — Kịch bản đỏ: ghi "họ tín hiệu này không có lợi thế", chuyển sang họ khác. Người dùng vẫn giữ một năm nhật ký học và điểm hiệu chuẩn của chính mình.

**Ra khi:** có quyết định v2 bằng văn bản.

---

## Tính năng sẽ phát minh (chín, đều giữ nguyên lõi)

Lõi: agent tự đặt lệnh ảo, tự học, sổ minh bạch để người dùng học theo.

- Giai đoạn B: bản tin cuối ngày (**B2**) · sổ bài học (**B3**) · bảng sức khoẻ (**B4**).
- Giai đoạn C: sổ giả thuyết (ý tưởng → thăm dò → xác nhận → qua hoặc bị bác) ·
  sân đấu phương án (**C1**) · agent tự soạn ứng viên (**C3**) · phòng tập thị
  trường giả (**C4**).
- Giai đoạn D: lịch sự kiện (**D1**) · "bạn so với agent" (**D4**).

---

## Ý tưởng — ĐỀ XUẤT CHƯA ĐO

Năm ý tưởng đánh vào chỗ tắc. **Mỗi ý là đề xuất, chưa đo. Ý nào đổi cách đo
phải qua một ĐO ký trước (`docs/TIEU-CHI-DOC-TRUOC.md`) và người dùng duyệt**
trước khi vào mã. Chúng không có mã mốc: một BƯỚC không được viện chúng làm mốc
cho tới khi đã thành một đầu việc có mã ở trên.

- Kiểm định đọc lúc nào cũng hợp lệ (e-value, dãy khoảng tin cậy): theo dõi hằng
  ngày, dừng sớm khi bằng chứng mạnh mà không phồng sai lầm loại I. Áp từ UV-002;
  UV-001 giữ mốc đã ký. Cái giá: ở cỡ mẫu cố định nó kém lực hơn một chút. Cần một
  ĐO mô phỏng so lực và sai lầm loại I với mốc cố định.
- Ngân sách alpha trực tuyến (alpha-investing, FDR trực tuyến như LORD, SAFFRON):
  cho dòng giả thuyết đến dần; phát hiện đúng thì được trả lại ngân sách, nên mười
  ứng viên không còn nghĩa là ngưỡng chia mười.
- Học sau mỗi lệnh ở tầng phân vốn: Thompson sampling phân vốn ảo giữa các phương
  án bóng sau từng lệnh đóng. Chỉ để thăm dò; luật lên phiên bản vẫn qua vòng xác nhận.
- Chi phí trước, thị trường sau: mỗi ứng viên khai vòng quay dự kiến và IC hoà
  vốn; cổng khả thi loại ngay ứng viên cần IC cao hơn trần đã đo của nguồn nó
  dùng (khối ngoại: cận trên 0,0387 so với rào 0,1031 — `docs/STATE.md` BƯỚC 113).
- Kiểm chứng cái máy, tách khỏi thị trường: đối chứng dương đầu-cuối trên thị
  trường giả có lợi thế cài sẵn (nhật ký → bài học → ứng viên → sân đấu → xác
  nhận). Nếu máy không tìm ra lợi thế ta biết chắc là có, đừng tin nó trên thị trường thật.

---

## Tài nguyên, kiến thức, rủi ro

- **Khoá `ANTHROPIC_API_KEY`**: người dùng tự đặt (GitHub và Streamlit secrets),
  có trần chi tiêu tháng; mở giai đoạn B. Chi phí CHƯA đo — đo ở tuần đầu giai
  đoạn B. **Chưa đặt; giai đoạn A không làm gì về khoá.**
- **20 phút mỗi tuần của người dùng** cho một phiên quyết định (hàng đợi: **A5**).
- **Tín dụng đám mây** hết hạn 05/11/2026: dồn cho BƯỚC thuần mã của A–B (ước
  lượng của leader: 5–9 BƯỚC).
- **Hạn mức Pro**: leader dùng Opus cho quyết định; việc thường giao phiên con Sonnet.
- Kiến thức cần thêm: sự kiện quyền (cổ tức, chia tách, phát hành); lịch review
  ETF và thành phần rổ theo lịch sử (thiên lệch sống sót hiện ghi là "không xử lý
  được bằng nguồn đang có"); thống kê tuần tự; danh mục có tính phí; vi cấu trúc
  HOSE (biên độ, lô chẵn, ATO/ATC, room ngoại); một đợt tra cứu ngoài (deep
  research) về các hiệu ứng có cơ sở kinh tế trên thị trường Việt Nam.
- Rủi ro: phụ thuộc `vnstock` (từng bị cách ly trên PyPI 25–26/09); GitHub Actions
  trễ ở khung chuông (`CLAUDE.md`, mục *Quét tự động*); tín hiệu thưa (nhịp vào
  lệnh chưa ổn định); một người vận hành, quyết định đọng lại thì cả dự án đứng;
  xác suất UV-001 qua là thấp ngay từ bản khai.
