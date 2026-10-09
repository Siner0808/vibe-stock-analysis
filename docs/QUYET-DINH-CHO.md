# HÀNG ĐỢI QUYẾT ĐỊNH CHỜ NGƯỜI DÙNG

**Sổ sống.** Mỗi mục là MỘT câu hỏi dành cho người dùng, để leader trình trong
MỘT phiên quyết định (`docs/LO-TRINH.md`, mục A5). Dựng ở BƯỚC 165 (08/10/2026); BƯỚC 166 (09/10/2026) ghi các câu người dùng đã trả lời trong phiên quyết định A5 và thêm Q10–Q12.

Luật của sổ này (gác: `tests/test_quyet_dinh_cho.py`, bộ đọc: `tools/quyet_dinh_cho.py`):

- Mục KHÔNG bị xoá; chỉ đổi trạng thái. Mã `Q1…Qn` liền nhau, không đứt quãng.
- `chờ` phải có NGUỒN (mỗi `tệp:dòng` đi kèm một trích `«…»` còn nguyên văn trong tệp), ít nhất hai LỰA CHỌN, một ĐỀ XUẤT và dữ kiện đã kiểm kèm lệnh + ngày.
- `đã quyết` phải có câu trả lời NGUYÊN VĂN của người dùng và ngày.
- `hết hiệu lực` (câu hỏi không còn đối tượng) phải có BẰNG CHỨNG: lệnh + ngày chạy. Đây KHÔNG phải `đã quyết`: không ai trả lời. Ngày 09/10/2026 chưa mục nào dùng trạng thái này (Q5, mục duy nhất từng dùng nó, hoá ra đã được người dùng quyết); khuôn vẫn giữ và gác chạy nó trên một mẫu dựng sẵn.
- Số dòng đúng tại `main` `e00fbbe` lúc viết lại (BƯỚC 166); tệp đổi thì dòng trôi, nên gác đòi trích còn nguyên văn và dòng không vượt độ dài tệp. Tách `docs/STATE.md` theo tháng (A4) đã BỎ (Q10), nên các nguồn trỏ vào `docs/STATE.md` không bị làm trôi bởi việc đó.
- Cột "Đề xuất" là ĐỀ XUẤT do phiên soạn viết nháp cho leader; mục `chờ` còn giữ nó, mục `đã quyết` giữ lại làm sử liệu.
- Dữ kiện đo 08/10/2026 đều chỉ đọc; không đọc sổ lệnh thật hay Sheets, không gọi vnstock. Dữ kiện 09/10/2026 ghi rõ ai đo: "leader đo" (trình duyệt, máy của người dùng) hay "BƯỚC 166 chạy lại".

Cách đọc nhanh: `./.venv/Scripts/python.exe tools/quyet_dinh_cho.py`.

---

## Q1 — Đường quét thật có nạp 44 mẫu bộ nhớ hậu nghiệm (chỉ đọc) như backtest không?

**Trạng thái:** đã quyết

**Nguồn:** `docs/HANDOFF.md:576 «Bộ nhớ hậu nghiệm trên đường quét thật»` · `CLAUDE.md:164 «đường thật **giữ 0 mẫu**»` · `docs/STATE.md:19218 «SOÁT ĐỊNH KỲ 7: ĐƯỜNG QUÉT THẬT CHƯA BAO GIỜ DÙNG BỘ NHỚ»` (BƯỚC 140, lỗi 112) · `docs/STATE.md:19312 «Việc cho người dùng quyết»`

**Ảnh hưởng:** hành vi giao dịch ảo. Backtest dùng 44 mẫu đứng yên (`co_san`, mức phạt −12 ở ca khớp), còn đường quét thật chạy với bộ nhớ rỗng, nên điểm của hai nơi lệch nhau (44 so với 0). Đổi bên nào cũng đổi lệnh nào được mở ở đường thật hoặc đổi cách đọc số backtest.

**Lựa chọn:**
- (a) Giữ như đang chạy: đường thật 0 mẫu, không phạt, lệch backtest có tên. Hệ quả: không đổi lệnh nào; vế "tích luỹ" của đường thật vẫn chưa từng xảy ra ở nơi nó chạy; mọi so sánh backtest với sổ thật phải đọc kèm chỗ lệch này.
- (b) Nạp 44 mẫu chỉ đọc vào đường thật NHƯNG đi qua vòng xác nhận tầng 3 như một ứng viên (`CLAUDE.md:161 «đổi điểm phải qua vòng xác nhận của tầng 3»` đòi đổi điểm phải qua vòng ấy). Hệ quả: tốn một suất khai (≤ 1 ứng viên mỗi tháng dương lịch, tháng 10 đã dùng cho UV-001), phán quyết chỉ ở phiên có nhãn thứ 252; trong lúc chờ đường thật vẫn không phạt.
- (c) Nạp thẳng qua workflow, không qua vòng xác nhận (ngoại lệ có chủ ý so với dòng 161 của `CLAUDE.md`). Hệ quả: khớp backtest ngay; BƯỚC 140 đo trên sổ rằng 3 trong 11 lệnh tiến-về-trước (STB, TCB, DCL) lẽ ra đã bị chặn; chạm workflow hoặc `run_daily` và cần một ĐO ký trước.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), ghi chỗ lệch 44 so với 0 vào mọi báo cáo so backtest với sổ thật. Nếu người dùng muốn nạp, đi đường (b), không đi (c). Lý do: quyết định 25/09 "44 mẫu chỉ giữ làm lịch sử" đọc được theo cả hai nghĩa (BƯỚC 140) nên không suy hướng từ nó.

**Trả lời nguyên văn (09/10/2026):** *"Giữ 0 mẫu (Recommended)"* — tức phương án (a).

**Hệ quả / việc kế:** không đổi mã, workflow hay ngưỡng. `CLAUDE.md` mục "Bộ nhớ hậu nghiệm" ghi quyết định; mọi báo cáo so backtest (44 mẫu) với sổ thật (0 mẫu) phải nêu chỗ lệch 44↔0. Muốn nạp về sau thì đi đường (b).

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `grep -n "giữ 0 mẫu" CLAUDE.md` cho dòng 164 (quyết định đã vào luật).
- Lúc hỏi (08/10/2026): `git check-ignore -v sl_pattern_memory.json` cho `.gitignore:50`: tệp bộ nhớ không vào git; `git grep -n "sl_pattern" -- .github` chỉ ra MỘT dòng chú thích ở `kiem-dinh.yml:50`, không có ở `quet-so-lenh.yml`: workflow quét không khôi phục tệp.
- Lúc hỏi (08/10/2026): `gh run view 37751112790 --repo Siner0808/vibe-stock-analysis --log` rồi lọc `Post-mortem: [^|]*mẫu` cho "BẬT · 0 mẫu, đều từ lệnh thật đã đóng": lượt quét thành công mới nhất khi ấy (08/10/2026 08:37Z, cây `0a991e1`) vẫn 0 mẫu. Con số 71/71 lượt của BƯỚC 140 đo ngày 29/09/2026, KHÔNG chạy lại.

---

## Q2 — Vế thứ ba của điều kiện dừng (đủ cỡ mẫu mà chưa chứng minh được lợi thế thì ĐÓNG cổng lệnh ảo) có giữ nguyên không?

**Trạng thái:** đã quyết

**Nguồn:** `docs/STATE.md:18053 «vế thứ ba của nó»` (BƯỚC 125) · `docs/HANDOFF.md:396 «vế 3 điều kiện dừng của cổng lệnh ảo»` · `docs/STATE.md:17578 «không phải lý do tắt agent»` (BƯỚC 122, quyết định 25/09) · `docs/STATE.md:18058 «Hướng có thể: ở tầng 3, điều kiện dừng đổi nghĩa»`

**Ảnh hưởng:** hành vi giao dịch ảo. Từ số lệnh tiến-về-trước đã đóng bằng `N_DAY_DU`, `paper_metrics.dieu_kien_dong_lai` đóng cổng mở lệnh trừ khi cận dưới của khoảng tin cậy dương. Mục tiêu dự án (BƯỚC 122) nói kết quả đo "không có lợi thế" không phải lý do tắt agent, trong khi BƯỚC 125 chỉ ra vế này sẽ tắt đúng trong ca đó. Chưa kích hoạt: chưa ai ước lượng khi nào sổ chạm `N_DAY_DU`.

**Lựa chọn:**
- (a) Giữ nguyên. Hệ quả: đủ cỡ mẫu mà chưa chứng minh được thì agent ngừng mở lệnh mới; đúng thiết kế "không lợi thế thì dừng" (bảng mô phỏng trong docstring: μ thật bằng 0 thì đóng 99,7%) nhưng agent ngừng học trên lệnh mới, trái tinh thần BƯỚC 122.
- (b) Đổi nghĩa vế 3 thành "lùi về phiên bản trước" (tầng 3) thay cho "ngừng đặt lệnh". Hệ quả: chưa có khái niệm phiên bản nào đang chạy (UV-001 chưa đọc); phải thiết kế mới, sửa `dieu_kien_dong_lai`, `run_daily.thi_hanh_dieu_kien_dung` và test, và ngưỡng đổi phải qua một ĐO ký trước.
- (c) Bỏ vế 3, giữ hai vế đầu (chỉ đóng khi alpha âm đo được). Hệ quả: agent chạy vô hạn khi không ai chứng minh được nó có hại, đúng điều vế 3 sinh ra để tránh; đổi sau khi đã nhìn số thì đụng bất biến 7.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** giữ (a) làm mặc định, đưa (b) thành một mục thiết kế của giai đoạn C (sân đấu phương án có khái niệm phiên bản), và chốt bằng văn bản TRƯỚC khi sổ chạm `N_TOI_THIEU`, vì sau đó mọi thay đổi bị nghi là chế điều kiện sau khi nhìn số.

**Trả lời nguyên văn (09/10/2026):** *"Giữ tạm, sửa ở GĐ C (Recommended)"* — mô tả lựa chọn người dùng đã thấy: "Giữ luật hiện tại; giai đoạn C thiết kế lại thành 'lùi về phiên bản trước' thay vì ngừng đặt lệnh. Chốt bằng văn bản trước khi sổ đủ mẫu."

**Hệ quả / việc kế:** không đổi mã. `docs/LO-TRINH.md` thêm mốc **C6** (cố ý bỏ qua `C5` vì trùng tên cổng C5): thiết kế lại vế 3, chốt bằng văn bản TRƯỚC khi sổ thật chạm `N_TOI_THIEU` lệnh tiến-về-trước đã đóng.

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `grep -n "C6" docs/LO-TRINH.md` cho mốc mới.
- Lúc hỏi (08/10/2026): `./.venv/Scripts/python.exe -c "import paper_metrics as p; print(p.N_DAY_DU, p.N_TOI_THIEU, p.MUC_BAT_LOI)"` in `451 113 -0.92`; trong `CLAUDE.md`: `N_DAY_DU` = 451 lệnh, `N_TOI_THIEU` = 113.
- Lúc hỏi (08/10/2026): `sed -n 540,556p paper_metrics.py` cho docstring ghi vế thứ ba "n ≥ N_DAY_DU: ĐÓNG TRỪ KHI cận DƯỚI của KTC (z=1,96) > 0".
- Số lệnh đã đóng của sổ thật KHÔNG đọc: đọc bằng `tools/doc_so_that.py` khi cần.

---

## Q3 — Địa chỉ (URL) app Streamlit Cloud là gì, để kiểm việc treo từ BƯỚC 127?

**Trạng thái:** đã quyết

**Nguồn:** `docs/HANDOFF.md:395 «địa chỉ app Streamlit Cloud»` · `docs/STATE.md:18220 «chỉ triển khai từ»` (BƯỚC 127) · `docs/STATE.md:19432 «địa chỉ app vẫn chờ người dùng»` (BƯỚC 141)

**Ảnh hưởng:** chỉ kiểm vận hành; không đổi hành vi giao dịch (quét chạy ở GitHub Actions) và không đổi số đo. Điều chưa biết: Streamlit Cloud có đọc dòng `--extra-index-url` trong `requirements.txt` để cài `vnstock` và `vnai` ghim bản từ kho hãng không, và tab nhật ký "vì sao" (BƯỚC 141) có chạy trên Cloud không. PR #169 vào `main` từ 27/09/2026, đã 11 ngày chưa ai mở app để đọc.

**Lựa chọn:**
- (a) Người dùng đưa URL trong phiên quyết định; leader mở app bằng trình duyệt của leader và ghi kết quả vào `docs/STATE.md`. Hệ quả: đóng việc treo; URL của app công khai không phải bí mật nhưng cũng chưa có chỗ nào trong repo.
- (b) Người dùng tự mở app và báo "lên" hay "treo / lỗi cài gói". Hệ quả: không cần đưa URL, nhưng kết quả mất chi tiết lỗi nên khó tìm gốc.
- (c) Bỏ việc kiểm. Hệ quả: app công khai có thể đã hỏng từ 27/09 mà không ai biết; không ảnh hưởng sổ lệnh ảo.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), vì kiểm một lần tốn vài phút và là cách duy nhất biết `requirements.txt` ghim có chạy trên Cloud.

**Trả lời nguyên văn (09/10/2026):** người dùng đưa URL và nói *"địa chỉ app streamlit tôi đã mở thành công trong trình duyệt của bạn"* — tức phương án (a). **URL KHÔNG ghi vào repo** (repo công khai; app dùng khoá API trả phí của người dùng: `VNSTOCK_API_KEY` hạng silver, `GEMINI_API_KEY`): [URL do người dùng đưa, cố ý không lưu trong repo công khai].

**Hệ quả / việc kế:** việc treo từ BƯỚC 127 KHÉP: dòng `--extra-index-url` CÓ hiệu lực trên Cloud, và Cloud chạy hạng **silver**, không phải free (giả thuyết cũ bị bác, `CLAUDE.md` mục "Bất đối xứng" đã sửa). Còn chưa đo: BCTC và hạn mức trên Cloud; hạng trên GitHub Actions. Telemetry `vnstock` trên Cloud còn bật → Q11.

**Dữ kiện đã kiểm (09/10/2026):**
- Leader đo, trình duyệt: app chạy, khởi động lại 01:35:49 UTC từ `main` (sau merge #211). Nhật ký "Manage app": `Using uv pip install.` · ` + vnai==2.6.2` · ` + vnstock==4.0.9` · ` + vnstock-ezchart==1.0.2` · `Python dependencies were installed from /mount/src/vibe-stock-analysis/requirements.txt using uv.`; cũng in `✓ API key đã được lưu thành công!`.
- Leader đo, trình duyệt: bảng trạng thái của app hiện `🎫 Gói vnstock · silver · hết hạn 2026-11-22 · ● ĐÚNG`. BƯỚC 166 chạy lại: `grep -n '"● ĐÚNG" if _goi.dat' app.py` cho dòng 853: chữ "ĐÚNG" chỉ in khi `vnstock_goi.kiem_goi().dat`.
- Leader đo: `gh run view 37780109821 --log | grep -i "API key"` (lượt `quet-so-lenh` thành công 08/10 12:54Z) cũng in `✓ API key đã được lưu thành công!`. Hạng gói trên Actions CHƯA đọc.
- Tab "📜 Lịch sử giao dịch" có khối "📓 Nhật ký 'vì sao' của lệnh ảo" đọc từ Google Sheets, chạy được (số lệnh của sổ KHÔNG chép vào tài liệu).
- Lúc hỏi (08/10/2026): `grep -rIl "streamlit\.app" --exclude-dir=.git --exclude-dir=.venv .` không ra tệp nào: repo không lưu URL; `gh api repos/Siner0808/vibe-stock-analysis --jq .homepage` cho `null`; repo ở chế độ `public`.

---

## Q4 — "Mã thiếu giá thì từ chối cả bảng giá" của máy chấm xác nhận có giữ không, hay nới?

**Trạng thái:** đã quyết

**Nguồn:** `docs/STATE.md:21218 «CẢ bảng bị từ chối»` (BƯỚC 161, "chọn có chủ ý") · `docs/STATE.md:21258 «vẫn đòi phủ giá cho MỌI phiên chấm được»` (BƯỚC 162, rủi ro 3) · `docs/STATE.md:21260 «Một mã tạm ngừng giao dịch giữa chừng chặn cả bảng kéo»` (BƯỚC 162, rủi ro 5) · `cham_xac_nhan.py:23 «rồi từ chối cả bảng»`

**Ảnh hưởng:** số đo (tầng 3). Hai tài liệu đều ghi "nới là quyết định của người dùng". Giá thiếu ở một mã, một phiên bất kỳ trong cửa sổ chấm thì cả lượt chấm nổ, kể cả khi chỗ thiếu nằm SAU mốc đọc 252 phiên. Một mã tạm ngừng giao dịch giữa chừng chặn cả bảng kéo cho tới khi người kéo bỏ mã ấy bằng tay. Không đổi hành vi giao dịch ảo. Tần suất mã thiếu giá CHƯA đo (cần bộ kéo thật chạy trên máy có vnstock).

**Lựa chọn:**
- (a) Giữ bảo thủ như hiện tại. Hệ quả: không bao giờ điền giá; nhưng nếu một mã bị tạm ngừng, lượt chấm dừng cho tới khi người kéo bỏ mã khỏi bảng, và bỏ mã sau khi đã thấy kết quả có thể là chọn lọc (rổ chuẩn của nhãn là trung bình các mã của bảng, nên bỏ mã đổi cả rổ).
- (b) Nới theo quy tắc KÝ TRƯỚC: tự loại mã thiếu giá khỏi bảng theo một ngưỡng khai trước và ghi tên mã bị loại vào phán quyết. Hệ quả: sửa `cham_xac_nhan.kiem_phu` và bộ kéo `keo_bang_gia.keo`, thêm test; cần một ĐO ký trước vì đổi rổ chuẩn; làm sau khi đã nhìn số thì đụng bất biến 7.
- (c) Chưa quyết: giữ (a) cho tới khi bộ kéo thật chạy và đếm được mã thiếu giá (việc kế BƯỚC 162, mục (2)), rồi quyết với số trong tay. Hệ quả: hoãn nhưng không mất gì, vì mốc đọc còn xa (ước lượng đầu tháng 11/2027, `docs/LO-TRINH.md`).

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (c): giữ (a) tới khi có số đếm thật; chỉ khi bộ kéo thật cho thấy mã thiếu giá hay gặp mới mở (b) như một ĐO ký trước.

**Trả lời nguyên văn (09/10/2026):** *"Chờ số đếm thật (Recommended)"* — tức phương án (c).

**Hệ quả / việc kế:** giữ (a) cho tới khi bộ kéo thật chạy và đếm được mã thiếu giá (việc kế BƯỚC 162, mục (2)); khi có số đếm thì mở lại câu hỏi như một mục mới của sổ này (mục này không bị xoá). Không đổi mã.

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `git log -1 --format=%h -- keo_bang_gia.py cham_xac_nhan.py` ra `b14d270` (BƯỚC 162): hai tệp chưa đổi từ khi nêu rủi ro.
- Lúc hỏi (08/10/2026): `git grep -n "thieu gia trong cua so" -- cham_xac_nhan.py` ra dòng 242 (nơi `kiem_phu` từ chối); `git grep -n "rồi từ chối cả bảng" -- cham_xac_nhan.py` ra dòng 23.
- Tần suất mã thiếu giá CHƯA đo: bộ kéo thật chưa chạy trên dữ liệu thật (BƯỚC 162, việc kế (2)); không gọi vnstock.

---

## Q5 — Giữ hay xoá `scratch/luu_do18/` (18 tệp dữ liệu ĐO 18)?

**Trạng thái:** đã quyết

**Nguồn:** `docs/HANDOFF.md:398 «xoá hẳn»` (khối cuối ngày 27/09: "Xoá hẳn thì hỏi người dùng") · `docs/STATE.md:19529 «scratch/luu_do18/wt_do18_p1»` · `docs/LO-TRINH.md:182 «giữ hay xoá»` (mục A5 liệt kê câu này)

**Ảnh hưởng:** dọn dẹp, cộng một hệ quả tái lập. BƯỚC 142 (`docs/STATE.md:19529`) tính "582 lệnh trong 35 tháng = 16,6 lệnh/tháng" trực tiếp từ `luu_do18/wt_do18_p1/wf_oos.db` ("chỉ đọc"), và ĐO 22 (`docs/STATE.md:19594`) trỏ tới `../luu_do20/…`. Hai thư mục đã được người dùng quyết xoá (02/10/2026) và nằm trong Thùng rác, nên các đường ấy KHÔNG chạy lại được; muốn có số thì chạy lại từ commit đã ghim (vài giờ máy).

**Lựa chọn:**
- (a) Ghi nhận việc xoá và đánh dấu chỗ trích đường dẫn đã chết (STATE chỉ thêm: một dòng đánh dấu ở BƯỚC có việc thêm, không sửa mục cũ). Hệ quả: trung thực về chuyện "582 lệnh / 16,6 lệnh mỗi tháng" không tái lập được từ đường đã ghi; không tốn đo đạc.
- (b) Dựng lại con số nhịp lệnh từ `scratch/luu_do22/` (4 tệp `wf_oos.db` của ĐO 22) hoặc từ một lượt chạy mới. Hệ quả: có số mới tái lập được, nhưng KHÁC số cũ (ĐO 22 đo 619 lệnh ở dòng theo ngày, không phải 582), nên phải gọi nó là số mới.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a) ngay, (b) chỉ khi một BƯỚC sau cần chính nhịp lệnh đó. (Nháp BƯỚC 165 viết "thư mục đã mất" và hỏi "ai xoá, khi nào" — cả hai SAI, xem chuỗi sự kiện dưới.)

**Trả lời nguyên văn (02/10/2026):** *"Xoá cả hai (Recommended)"* — hộp hỏi của phiên leader, 04:57Z, kèm lời giải thích: "Xoá hai thư mục cũ thì số của ĐO 18 và ĐO 20 vẫn tái lập được bằng cách chạy lại từ commit đã ghim, nhưng mất vài giờ máy."

**Xác nhận lại (09/10/2026):** sau khi leader báo sai nguồn gốc, người dùng chọn *"Khôi phục cả hai (Recommended)"*; khi leader đính chính (thư mục bị xoá theo chính quyết định của người dùng), người dùng chọn *"Đưa lại vào Thùng rác"*. Câu trả lời CÓ HIỆU LỰC cuối cùng: xoá.

**Hệ quả / việc kế:** `luu_do18/…` (BƯỚC 142) và `luu_do20/…` (ĐO 22) KHÔNG chạy lại được từ đường đã ghi; chạy lại từ commit đã ghim nếu cần số. `docs/STATE.md` chỉ thêm, nên con trỏ cũ trong STATE giữ nguyên và được ghi chú ở BƯỚC 166; dòng nêu đường ở `docs/HANDOFF.md` mang cửa thoát `duong-da-chet` theo quy ước của `tools/kiem_duong_ngoai_repo.py`. `luu_do22` giữ nguyên.

**Dữ kiện đã kiểm (09/10/2026):** chuỗi sự kiện theo lời leader (bản ghi phiên của leader), BƯỚC 166 không tự kiểm được vì Thùng rác nằm ở máy của người dùng:
- 02/10/2026 04:57Z: hộp hỏi "Hai thư mục lưu sổ OOS của các phép đo cũ đang chiếm ổ đĩa: luu_do18 (330 MB) và luu_do20 (593 MB)…" → *"Xoá cả hai (Recommended)"*.
- 02/10/2026 04:58Z: leader chuyển cả hai vào Thùng rác bằng `[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(<thư mục>, 'OnlyErrorDialogs', 'SendToRecycleBin')`, và chỉ ghi vào bộ nhớ riêng của leader, KHÔNG ghi vào repo — vì thế BƯỚC 165 không tìm thấy quyết định này.
- 09/10/2026: leader đo Thùng rác bằng PowerShell `(New-Object -ComObject Shell.Application).Namespace(10).Items()` lọc tên `luu_do`: `luu_do18` (18 tệp, 345.117.362 byte), `luu_do20` (36 tệp, 621.727.714 byte), ngày xoá 02/10/2026 11:58 SA, đường gốc `C:\Users\cuong\.gemini\antigravity\scratch`.
- 09/10/2026: người dùng chọn khôi phục; leader khôi phục bằng `InvokeVerb('undelete')`, đo khớp từng byte; sau đính chính, người dùng chọn đưa lại vào Thùng rác; leader chuyển lại lúc 08:54 sáng 09/10 (giờ VN) bằng cùng lệnh `DeleteDirectory` ở trên. Trạng thái cuối: `luu_do18`, `luu_do20` trong Thùng rác (còn khôi phục được); `luu_do22` giữ nguyên.
- Bằng chứng cũ của BƯỚC 165 (08/10/2026): `ls -d /c/Users/cuong/.gemini/antigravity/scratch/luu_do18*` báo "No such file or directory" — ĐÚNG với `ls`, SAI khi đọc thành "không ai biết ai xoá": thư mục nằm trong Thùng rác.

---

## Q6 — `vnii` 0.2.6 gửi thêm tên hàm đang gọi (trường `operation`) mỗi lần kiểm giấy phép: chấp nhận hay chặn?

**Trạng thái:** đã quyết

**Nguồn:** `docs/HANDOFF.md:635 «gửi thêm tên hàm đang gọi»` · `docs/STATE.md:17152 «gửi thêm trường»` (BƯỚC 118, ĐO 17)

**Ảnh hưởng:** chỉ riêng tư; không đổi hành vi giao dịch và không đổi số đo. Công tắc `disable_telemetry()` người dùng bật 18/09/2026 thuộc `vnai` và không phủ đường này (docstring của `vnii` ghi "used only for telemetry"). Chưa đo, chưa chặn.

**Lựa chọn:**
- (a) Chấp nhận: `vnii` là gói đóng của hãng, kiểm giấy phép cần nó, và dữ liệu gửi chỉ là tên hàm. Hệ quả: không đổi gì; ghi rõ ranh giới này vào tài liệu để không ai nghĩ telemetry đã tắt hoàn toàn.
- (b) Cho một phiên con ĐO trước: xem `vnii` gửi những trường nào (chỉ đọc mã đã cài, không gọi mạng), rồi mới quyết chặn hay không. Hệ quả: tốn một BƯỚC; chặn đường này có thể làm kiểm giấy phép hỏng và đẩy hạng gói về `free` (`CLAUDE.md`: `vnai/beam/auth.py` nuốt lỗi rồi rơi về "free"), nên cách chặn phải khảo sát riêng.
- (c) Hỏi hãng về trường này, như đã làm với báo lỗi `vnstock_ezchart` (Q8). Hệ quả: chậm, phụ thuộc hãng.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a) tạm thời, kèm một dòng ranh giới; chỉ mở (b) nếu người dùng coi tên hàm là dữ liệu nhạy cảm.

**Trả lời nguyên văn (09/10/2026):** *"Theo đề xuất cả hai (Recommended)"* — hỏi gộp Q6 và Q8; với Q6 là phương án (a): chấp nhận `vnii` gửi `operation`, ghi rõ ranh giới.

**Hệ quả / việc kế:** không đổi mã. Ranh giới ghi ở `docs/HANDOFF.md` (dòng `vnii`): telemetry `vnai` tắt ở máy, đường `vnii` vẫn gửi tên hàm; telemetry `vnstock` trên Cloud và Actions còn bật → hỏi ở Q11.

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `grep -n "Người dùng chấp nhận 09/10/2026" docs/HANDOFF.md` cho dòng ghi ranh giới.
- Lúc hỏi (08/10/2026): `./.venv/Scripts/python.exe -m pip list` (lọc `vnii`) ra `vnii 0.2.6`: phiên bản đang cài trùng bản đã nêu ở BƯỚC 118. Lệnh không chạm mạng và không gọi `vnii`; chưa ai đo trường nào ngoài `operation` được gửi.

---

## Q7 — Dữ liệu BCTC `backtest/fundamentals/` nằm trong repo công khai: giữ hay chuyển ra ngoài?

**Trạng thái:** chờ

**Nguồn:** `docs/HANDOFF.md:622 «trong repo công khai»` (kèm "Người dùng kiểm điều khoản; chi tiết trong báo cáo audit") · `docs/STATE.md` BƯỚC 121 (audit toàn hệ thống; báo cáo đầy đủ là Artifact riêng tư của người dùng, repo chỉ có bản tóm tắt)

**Ảnh hưởng:** pháp lý và dọn dẹp, cộng một phụ thuộc của test. Repo ở chế độ `public`. Bản ghi không nói điều khoản dữ liệu của nguồn cho phép hay cấm, vì việc kiểm điều khoản thuộc người dùng và kết quả chưa được ghi lại. Tệp `tests/test_cache_bctc_du_ky.py` đọc đúng thư mục này (`KHO = GOC / "backtest" / "fundamentals"`).

**Lựa chọn:**
- (a) Giữ, sau khi người dùng đọc điều khoản và xác nhận cho phép. Hệ quả: không đổi gì; ghi kết quả đọc điều khoản (nguyên văn câu trả lời) vào sổ này để khép mục.
- (b) Chuyển ra ngoài repo: bỏ khỏi chỉ mục git, thêm vào `.gitignore`, và sửa `tests/test_cache_bctc_du_ky.py` để bỏ qua có điều kiện khi thiếu dữ liệu. Hệ quả: các commit cũ vẫn chứa tệp, vì `main` có ruleset cấm force-push nên lịch sử không viết lại được; đo IC BCTC (BƯỚC 53) không tái lập được trên CI nếu không có dữ liệu.
- (c) Giữ chỉ các tệp mà test thực sự cần, chuyển phần còn lại. Hệ quả: giảm diện phơi bày; cần liệt kê tệp nào test dùng.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** người dùng đọc điều khoản trước (việc duy nhất agent không làm hộ được), rồi chọn (a) nếu được phép, (b) hoặc (c) nếu không. Chưa có điều khoản trong tay thì chưa thể đề xuất nghiêng về phía nào.

**Ghi nhận 09/10/2026 (CHƯA phải quyết định cuối):** người dùng trả lời *"Tôi đọc điều khoản rồi báo (Recommended)"* — mục vẫn `chờ` cho tới khi người dùng báo kết quả đọc điều khoản.

**Dữ kiện đã kiểm (08/10/2026):**
- `git ls-files backtest/fundamentals | wc -l` ra `217` tệp; `git ls-files -z backtest/fundamentals | xargs -0 du -ck | tail -1` ra khoảng `5884` KB.
- `gh api repos/Siner0808/vibe-stock-analysis --jq .visibility` ra `public`.
- `grep -rln "fundamentals/" tests` (và các tệp mã gốc) chỉ ra `tests/test_cache_bctc_du_ky.py` là nơi đọc thư mục này trong test.

---

## Q8 — Gửi báo lỗi đóng gói của `vnstock_ezchart` cho hãng, hay giữ bản vá tại máy mãi?

**Trạng thái:** đã quyết

**Nguồn:** `docs/HANDOFF.md:642 «Báo lỗi đã soạn»` · `docs/STATE.md:17188 «HỎNG HAI LỚP»` (BƯỚC 119)

**Ảnh hưởng:** chỉ dọn dẹp và ranh giới với hãng; không đổi hành vi giao dịch hay số đo. Máy chạy bản vá tại máy `1.0.2+vibe1` (ba dòng `pyproject.toml`, không đụng mã). Khi hãng phát hành bản sửa, `tools/so_ban_goi.py` báo lệch ở hạng `QUYET DINH SO` và bản vá phải được thay bằng bản chính thức.

**Lựa chọn:**
- (a) Người dùng gửi báo lỗi đã soạn cho hãng. Hệ quả: hãng có thể sửa gốc; bản vá tại máy được thay khi có bản chính thức; vị trí bản nháp báo lỗi cần được leader nêu rõ khi trình (bản ghi không nêu đường dẫn).
- (b) Không gửi, giữ bản vá mãi. Hệ quả: máy khác (hoặc cài mới) gặp lại đúng lỗi thiếu `static/` và hai phụ thuộc khai là tuỳ chọn; `tools/so_ban_goi.py` tiếp tục báo lệch ở hạng quyết định.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), vì báo đã soạn xong, chi phí của người dùng là một lần gửi.

**Trả lời nguyên văn (09/10/2026):** *"Theo đề xuất cả hai (Recommended)"* — hỏi gộp Q6 và Q8; với Q8 là phương án (a), kèm cách làm: leader soạn lại báo lỗi, NGƯỜI DÙNG gửi hãng.

**Hệ quả / việc kế:** bản nháp gốc của BƯỚC 119 nằm ở thư mục tạm của phiên cũ và đã mất, nên leader soạn lại NGOÀI repo (`C:\Users\cuong\.gemini\antigravity\scratch\vibe_handoff\bao-loi-vnstock-ezchart.md`, trên máy người dùng); người dùng gửi. Bản vá `1.0.2+vibe1` giữ cho tới khi hãng phát hành bản sửa.

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `curl -s https://pypi.org/pypi/vnstock-ezchart/json` rồi đọc `info.version` ra `1.0.2`, các bản `['0.0.3', '1.0.1', '1.0.2']`: hãng chưa phát hành bản sửa.
- Leader đo: GitHub `vnstock-hq/vnstock_ezchart` commit mới nhất vẫn `23d5129`; repo hãng chưa có issue nào ⇒ lỗi chưa sửa.
- Lúc hỏi (08/10/2026): `./.venv/Scripts/python.exe -m pip list` (lọc `ezchart`) ra `vnstock_ezchart 1.0.2+vibe1`: bản vá vẫn đang chạy.

---

## Q9 — Khoá `ANTHROPIC_API_KEY` cho P2c / B1 (hậu kiểm lệnh đóng bằng lời): khi nào đặt?

**Trạng thái:** đã quyết

**Nguồn:** `docs/LO-TRINH.md:28 «Khoá Claude API»` · `docs/STATE.md:21373 «Khoá Claude API →»` (BƯỚC 164, hộp hỏi ở phiên leader)

**Ảnh hưởng:** hành vi của agent (tầng 2: bài học bằng lời cho mọi lệnh đóng). Chưa có khoá thì P2c / B1 chưa chạy; không đổi lệnh nào, không đổi số đo.

**Lựa chọn:**
- (a) Để tới giai đoạn B (26/10/2026). Hệ quả: giai đoạn A không làm gì về khoá; người dùng tự đặt khoá (GitHub và Streamlit secrets) cùng một trần chi tiêu tháng khi B mở.
- (b) Đặt ngay trong giai đoạn A. Hệ quả: P2c chạy sớm hơn, tốn chi phí chưa được đo.

**Trả lời nguyên văn (08/10/2026):** *"Để tới giai đoạn B (Recommended)"*

**Còn lại cho người dùng (không phải câu hỏi mới):** tới đầu giai đoạn B tự đặt khoá và trần chi tiêu; chi phí chưa đo, đo ở tuần đầu giai đoạn B (`docs/LO-TRINH.md`, mục Tài nguyên).

**Dữ kiện đã kiểm (08/10/2026):**
- `git grep -n "ANTHROPIC_API_KEY" -- docs/LO-TRINH.md` ra các dòng nêu khoá là việc của người dùng, giai đoạn A không đặt.

---

## Q10 — Có tách `docs/STATE.md` theo tháng (A4) không?

**Trạng thái:** đã quyết

**Nguồn:** `docs/LO-TRINH.md:179 «Tách `docs/STATE.md` theo tháng, giữ một mục lục.»` (mục A4, nay đánh dấu ĐÃ BỎ)

**Ảnh hưởng:** tài liệu và công cụ đọc. `docs/STATE.md` nặng khoảng 1,2 MB (`docs/LO-TRINH.md`, chẩn đoán 4); tách nó đổi `moc_lo_trinh.TEP_STATE`, `tools/buoc_cham_luat.py` và làm gác `tests/test_quyet_dinh_cho.py` đỏ ở mọi nguồn trỏ vào nó. Không đổi hành vi giao dịch hay số đo.

**Lựa chọn:**
- (a) Tách theo tháng, giữ một mục lục. Hệ quả: các phiên không phải nạp cả 1,2 MB; nhưng đổi quần thể của ba gác và mọi con trỏ `docs/STATE.md:dòng`.
- (b) Không tách. Hệ quả: giữ nguyên công cụ và con trỏ; phiên đọc phần cuối bằng `offset` như đang làm.

**Trả lời nguyên văn (09/10/2026):** *"Không tách (Recommended)"* — tức phương án (b).

**Hệ quả / việc kế:** `docs/LO-TRINH.md` đánh dấu A4 ĐÃ BỎ (mã A4 vẫn đọc được cho `tests/test_moc_lo_trinh.py`). Lý do leader nêu (câu hỏi gửi sổ tay, `docs/soat-notebooklm.json` mục BƯỚC 166): phép đo A4 của leader cho lợi ≈ 0 so với 7 test hỏng, 199 trên 219 con trỏ chết và hai công cụ (`tools/ho_so.py`, `tools/doi_chieu_trich_dan.py`) hỏng lặng lẽ. Lệnh đo ấy không có trong đề bài của BƯỚC 166 nên chưa tái lập được trong phiên này — đó là số đo của leader, không phải của phiên viết sổ.

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `wc -c docs/STATE.md` đo kích thước hiện tại của tệp (đọc bằng lệnh, không chép con số vào tài liệu).
- `grep -n "A4" docs/LO-TRINH.md` cho dòng 179 đã đánh dấu ĐÃ BỎ.

---

## Q11 — Có đặt `VNSTOCK_TELEMETRY=off` trên Streamlit Cloud và GitHub Actions, cho khớp quyết định tắt telemetry ở máy (18/09/2026)?

**Trạng thái:** chờ

**Nguồn:** `docs/HANDOFF.md:637 «`disable_telemetry()` bật 18/09 là của `vnai`»` · `docs/STATE.md:15348 «trường `VNSTOCK_TELEMETRY`»`

**Ảnh hưởng:** riêng tư, không đổi hành vi giao dịch hay số đo. Nhật ký Cloud (leader đọc 09/10/2026) có dòng `[vnstock] Thư viện gửi số liệu đo lường tuỳ chọn (tên hàm, thời gian chạy, lỗi)… Tắt: đặt VNSTOCK_TELEMETRY=off hoặc gọi vnai.disable_telemetry()`: telemetry `vnstock` đang BẬT ở hai nơi chạy trực tiếp, trong khi máy đã tắt từ 18/09/2026. Đặt biến là sửa secrets/biến môi trường của Cloud và `env:` của workflow.

**Lựa chọn:**
- (a) Đặt `VNSTOCK_TELEMETRY=off` ở cả hai: Streamlit Cloud (secrets hoặc biến môi trường) và GitHub Actions (`env:` của workflow quét). Hệ quả: khớp tinh thần 18/09; rẻ; chạm workflow nên cần một BƯỚC riêng và gác (`tests/test_bo_cong_khop_CI.py`); không biết trước hãng có coi biến này như điều kiện cấp hạng không (chưa đo).
- (b) Chỉ đặt ở Actions hoặc chỉ ở Cloud. Hệ quả: nửa vời; một nơi vẫn gửi.
- (c) Giữ nguyên, ghi ranh giới "telemetry chỉ tắt ở máy". Hệ quả: không đổi gì; hai nơi chạy trực tiếp tiếp tục gửi tên hàm và thời gian chạy.

**Đề xuất của leader (ĐỀ XUẤT, phiên 09/10 soạn nháp, chưa ai quyết):** (a): bật `off` ở cả hai — rẻ, cùng tinh thần quyết định 18/09; làm bằng một BƯỚC riêng có kiểm xem hạng gói (`kiem_goi`) và quét có đổi không.

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `git grep -n "VNSTOCK_TELEMETRY" -- . ':!docs' ':!tests'` không ra dòng nào: không workflow, không `app.py`, không cấu hình nào của repo đặt biến này.
- Leader đo, trình duyệt: nhật ký "Manage app" của Cloud in dòng `[vnstock] Thư viện gửi số liệu đo lường tuỳ chọn…` nói trên. Nhật ký Actions chưa đọc để tìm dòng này.
- Chỉ GHI câu hỏi: chưa sửa workflow hay secrets nào.

---

## Q12 — Mặc định thanh trượt "Ngưỡng mua" trên app (50) có nên theo `BUY_THRESHOLD` (62) của đường giao dịch không?

**Trạng thái:** chờ

**Nguồn:** `app.py:453 «NGUONG_MUA_MAC_DINH = 50.0»` · `app.py:697 «Ngưỡng mua Multi-Agent (pts)»` · `paper_trading.py:77 «BUY_THRESHOLD = 62»`

**Ảnh hưởng:** hiển thị của app công khai, không đổi lệnh ảo nào (đường giao dịch dùng `paper_trading.BUY_THRESHOLD`). Thanh trượt `app.py:697` mặc định `NGUONG_MUA_MAC_DINH = 50.0`, và app in "thấp hơn ngưỡng mua 50.0 pts" (`app.py:1396`) trong khi sổ lệnh ảo mua ở 62: người xem app thấy một ngưỡng khác với ngưỡng thật của đường giao dịch.

**Lựa chọn:**
- (a) Mặc định thanh trượt = `BUY_THRESHOLD` nhập từ `paper_trading`; thanh trượt vẫn chỉnh được trong khoảng 40–65. Hệ quả: app khớp đường giao dịch; một ngưỡng, một chỗ (`CLAUDE.md`: "Một ngưỡng mua, một chỗ"); đổi hiển thị mặc định của app công khai; cần sửa `app.py` và test.
- (b) Giữ 50 và ghi chú trên app rằng đó chỉ là ngưỡng xem thử. Hệ quả: không đổi mã giao dịch; người xem vẫn có thể hiểu nhầm.
- (c) Giữ nguyên. Hệ quả: không đổi gì.

**Đề xuất của leader (ĐỀ XUẤT, phiên 09/10 soạn nháp, chưa ai quyết):** (a): mặc định = `BUY_THRESHOLD` nhập từ `paper_trading`, thanh trượt vẫn chỉnh được.

**Dữ kiện đã kiểm (09/10/2026):**
- BƯỚC 166 chạy lại: `grep -n "NGUONG_MUA_MAC_DINH" app.py` ra dòng 453 (`= 50.0`), 600 và 698 (nơi dùng); `grep -n "^BUY_THRESHOLD" paper_trading.py` ra dòng 77 (`= 62`).
- Chỉ GHI câu hỏi: không sửa `app.py`.

---

## Đã quét và loại khỏi hàng đợi (08/10/2026)

Các câu dưới đây từng đứng ở "cần người quyết" hay "chờ người dùng" nhưng đã có quyết định hoặc tiền đề của chúng đã hết đúng. Không phải mục Q, không có gác riêng; nguồn để tra lại:

- Bật lại ba workflow: ĐÃ BẬT 28/09/2026 (`docs/HANDOFF.md`, dòng "bật lại ba workflow ✅ bật 28/09"; BƯỚC 138).
- Tab `nhat_ky` rỗng trên Google Sheet: người dùng quyết "ĐỂ YÊN" 28/09/2026 (`docs/HANDOFF.md`, khối cuối ngày 28/09; BƯỚC 136). Không có câu nguyên văn trong bản ghi nên không đưa vào Q dưới dạng `đã quyết`.
- Bước giá theo sàn: ĐÃ QUYẾT 29/09/2026, phương án A, ĐÃ SỬA (BƯỚC 143).
- Hướng chiến lược (A hay B): ĐÃ CHỌN 25/09/2026, không phải A (BƯỚC 122).
- Nâng stop trên nến chưa đóng: ĐÃ QUYẾT 25/09, ĐÃ LÀM 26/09 (BƯỚC 123).
- `pyarrow` 24 so với 25: người dùng chốt bỏ qua 18/09/2026.
- Biên `khai_ngay` ký `>=`: người dùng duyệt 07/10/2026 (BƯỚC 161).
- Rủi ro 1 của BƯỚC 162 (số mã đủ ở 252 phiên): tiền đề hết đúng từ BƯỚC 146; chỉ còn một ĐO độ phủ ký trước, không phải quyết định của người dùng.
- "Đã hỏi người dùng có ghi thành một dòng bảng lỗi không" (cuối BƯỚC 127): lỗi 106 đã vào `references/loi-da-mac.md`.
- Audit BƯỚC 121 còn phát hiện chưa vá (`docs/HANDOFF.md:577`, "14/19 đã vá"): việc sửa theo lộ trình, không có câu nào chờ người dùng; danh sách 5 phát hiện còn lại nằm trong báo cáo riêng tư nên phiên này không kiểm.
