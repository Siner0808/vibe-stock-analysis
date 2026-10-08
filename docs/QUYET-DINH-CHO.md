# HÀNG ĐỢI QUYẾT ĐỊNH CHỜ NGƯỜI DÙNG

**Sổ sống.** Mỗi mục là MỘT câu hỏi dành cho người dùng, để leader trình trong
MỘT phiên quyết định (`docs/LO-TRINH.md`, mục A5). Dựng ở BƯỚC 165 (08/10/2026).

Luật của sổ này (gác: `tests/test_quyet_dinh_cho.py`, bộ đọc: `tools/quyet_dinh_cho.py`):

- Mục KHÔNG bị xoá; chỉ đổi trạng thái. Mã `Q1…Qn` liền nhau, không đứt quãng.
- `chờ` phải có NGUỒN (mỗi `tệp:dòng` đi kèm một trích `«…»` còn nguyên văn trong tệp), ít nhất hai LỰA CHỌN, một ĐỀ XUẤT và dữ kiện đã kiểm kèm lệnh + ngày.
- `đã quyết` phải có câu trả lời NGUYÊN VĂN của người dùng và ngày.
- `hết hiệu lực` (câu hỏi không còn đối tượng) phải có BẰNG CHỨNG: lệnh + ngày chạy. Đây KHÔNG phải `đã quyết`: không ai trả lời.
- Số dòng đúng tại `main` `8440239` lúc viết; tệp đổi thì dòng trôi, nên gác đòi trích còn nguyên văn và dòng không vượt độ dài tệp. Tách `docs/STATE.md` theo tháng (A4) sẽ làm gác đỏ ở mọi nguồn trỏ vào nó: đó là tín hiệu đúng, sửa nguồn theo tệp mới.
- Cột "Đề xuất" là ĐỀ XUẤT do phiên soạn viết nháp cho leader; chưa ai quyết, leader sửa trước khi trình.
- Dữ kiện đo hôm nay (08/10/2026) đều chỉ đọc; không đọc sổ lệnh thật hay Sheets, không gọi vnstock.

Cách đọc nhanh: `./.venv/Scripts/python.exe tools/quyet_dinh_cho.py`.

---

## Q1 — Đường quét thật có nạp 44 mẫu bộ nhớ hậu nghiệm (chỉ đọc) như backtest không?

**Trạng thái:** chờ

**Nguồn:** `docs/HANDOFF.md:563 «Bộ nhớ hậu nghiệm trên đường quét thật»` · `CLAUDE.md:164 «quyết định của người dùng, chưa có»` · `docs/STATE.md:19218 «SOÁT ĐỊNH KỲ 7: ĐƯỜNG QUÉT THẬT CHƯA BAO GIỜ DÙNG BỘ NHỚ»` (BƯỚC 140, lỗi 112) · `docs/STATE.md:19312 «Việc cho người dùng quyết»`

**Ảnh hưởng:** hành vi giao dịch ảo. Backtest dùng 44 mẫu đứng yên (`co_san`, mức phạt −12 ở ca khớp), còn đường quét thật chạy với bộ nhớ rỗng, nên điểm của hai nơi lệch nhau (44 so với 0). Đổi bên nào cũng đổi lệnh nào được mở ở đường thật hoặc đổi cách đọc số backtest.

**Lựa chọn:**
- (a) Giữ như đang chạy: đường thật 0 mẫu, không phạt, lệch backtest có tên. Hệ quả: không đổi lệnh nào; vế "tích luỹ" của đường thật vẫn chưa từng xảy ra ở nơi nó chạy; mọi so sánh backtest với sổ thật phải đọc kèm chỗ lệch này.
- (b) Nạp 44 mẫu chỉ đọc vào đường thật NHƯNG đi qua vòng xác nhận tầng 3 như một ứng viên (`CLAUDE.md:161 «đổi điểm phải qua vòng xác nhận của tầng 3»` đòi đổi điểm phải qua vòng ấy). Hệ quả: tốn một suất khai (≤ 1 ứng viên mỗi tháng dương lịch, tháng 10 đã dùng cho UV-001), phán quyết chỉ ở phiên có nhãn thứ 252; trong lúc chờ đường thật vẫn không phạt.
- (c) Nạp thẳng qua workflow, không qua vòng xác nhận (ngoại lệ có chủ ý so với dòng 161 của `CLAUDE.md`). Hệ quả: khớp backtest ngay; BƯỚC 140 đo trên sổ rằng 3 trong 11 lệnh tiến-về-trước (STB, TCB, DCL) lẽ ra đã bị chặn; chạm workflow hoặc `run_daily` và cần một ĐO ký trước.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), ghi chỗ lệch 44 so với 0 vào mọi báo cáo so backtest với sổ thật. Nếu người dùng muốn nạp, đi đường (b), không đi (c). Lý do: quyết định 25/09 "44 mẫu chỉ giữ làm lịch sử" đọc được theo cả hai nghĩa (BƯỚC 140) nên không suy hướng từ nó.

**Dữ kiện đã kiểm (08/10/2026):**
- `git check-ignore -v sl_pattern_memory.json` cho `.gitignore:50`: tệp bộ nhớ không vào git.
- `git grep -n "sl_pattern" -- .github` chỉ ra MỘT dòng chú thích ở `kiem-dinh.yml:50`, không có ở `quet-so-lenh.yml`: workflow quét không khôi phục tệp.
- `gh run view 37751112790 --repo Siner0808/vibe-stock-analysis --log` rồi lọc `Post-mortem: [^|]*mẫu` cho "BẬT · 0 mẫu, đều từ lệnh thật đã đóng": lượt quét thành công mới nhất (08/10/2026 08:37Z, cây `0a991e1`) vẫn 0 mẫu. Con số 71/71 lượt của BƯỚC 140 đo ngày 29/09/2026, KHÔNG chạy lại hôm nay.
- Tệp ở máy (`vibe_preview/sl_pattern_memory.json`, 26.969 byte, sửa lần cuối 21/08) có 44 mục: đọc bằng `json.load` rồi `len`.

---

## Q2 — Vế thứ ba của điều kiện dừng (đủ cỡ mẫu mà chưa chứng minh được lợi thế thì ĐÓNG cổng lệnh ảo) có giữ nguyên không?

**Trạng thái:** chờ

**Nguồn:** `docs/STATE.md:18053 «vế thứ ba của nó»` (BƯỚC 125) · `docs/HANDOFF.md:385 «vế 3 điều kiện dừng của cổng lệnh ảo»` · `docs/STATE.md:17578 «không phải lý do tắt agent»` (BƯỚC 122, quyết định 25/09) · `docs/STATE.md:18058 «Hướng có thể: ở tầng 3, điều kiện dừng đổi nghĩa»`

**Ảnh hưởng:** hành vi giao dịch ảo. Từ số lệnh tiến-về-trước đã đóng bằng `N_DAY_DU`, `paper_metrics.dieu_kien_dong_lai` đóng cổng mở lệnh trừ khi cận dưới của khoảng tin cậy dương. Mục tiêu dự án (BƯỚC 122) nói kết quả đo "không có lợi thế" không phải lý do tắt agent, trong khi BƯỚC 125 chỉ ra vế này sẽ tắt đúng trong ca đó. Chưa kích hoạt: chưa ai ước lượng khi nào sổ chạm `N_DAY_DU`.

**Lựa chọn:**
- (a) Giữ nguyên. Hệ quả: đủ cỡ mẫu mà chưa chứng minh được thì agent ngừng mở lệnh mới; đúng thiết kế "không lợi thế thì dừng" (bảng mô phỏng trong docstring: μ thật bằng 0 thì đóng 99,7%) nhưng agent ngừng học trên lệnh mới, trái tinh thần BƯỚC 122.
- (b) Đổi nghĩa vế 3 thành "lùi về phiên bản trước" (tầng 3) thay cho "ngừng đặt lệnh". Hệ quả: chưa có khái niệm phiên bản nào đang chạy (UV-001 chưa đọc); phải thiết kế mới, sửa `dieu_kien_dong_lai`, `run_daily.thi_hanh_dieu_kien_dung` và test, và ngưỡng đổi phải qua một ĐO ký trước.
- (c) Bỏ vế 3, giữ hai vế đầu (chỉ đóng khi alpha âm đo được). Hệ quả: agent chạy vô hạn khi không ai chứng minh được nó có hại, đúng điều vế 3 sinh ra để tránh; đổi sau khi đã nhìn số thì đụng bất biến 7.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** giữ (a) làm mặc định, đưa (b) thành một mục thiết kế của giai đoạn C (sân đấu phương án có khái niệm phiên bản), và chốt bằng văn bản TRƯỚC khi sổ chạm `N_TOI_THIEU`, vì sau đó mọi thay đổi bị nghi là chế điều kiện sau khi nhìn số.

**Dữ kiện đã kiểm (08/10/2026):**
- `./.venv/Scripts/python.exe -c "import paper_metrics as p; print(p.N_DAY_DU, p.N_TOI_THIEU, p.MUC_BAT_LOI)"` in `451 113 -0.92`; trong `CLAUDE.md`: `N_DAY_DU` = 451 lệnh, `N_TOI_THIEU` = 113.
- `sed -n 540,556p paper_metrics.py` cho docstring ghi vế thứ ba "n ≥ N_DAY_DU: ĐÓNG TRỪ KHI cận DƯỚI của KTC (z=1,96) > 0".
- Số lệnh đã đóng của sổ thật KHÔNG đọc hôm nay (đề bài cấm đọc Sheets): đọc bằng `tools/doc_so_that.py` khi cần.

---

## Q3 — Địa chỉ (URL) app Streamlit Cloud là gì, để kiểm việc treo từ BƯỚC 127?

**Trạng thái:** chờ

**Nguồn:** `docs/HANDOFF.md:384 «địa chỉ app Streamlit Cloud»` · `docs/STATE.md:18220 «chỉ triển khai từ»` (BƯỚC 127) · `docs/STATE.md:19432 «địa chỉ app vẫn chờ người dùng»` (BƯỚC 141)

**Ảnh hưởng:** chỉ kiểm vận hành; không đổi hành vi giao dịch (quét chạy ở GitHub Actions) và không đổi số đo. Điều chưa biết: Streamlit Cloud có đọc dòng `--extra-index-url` trong `requirements.txt` để cài `vnstock` và `vnai` ghim bản từ kho hãng không, và tab nhật ký "vì sao" (BƯỚC 141) có chạy trên Cloud không. PR #169 vào `main` từ 27/09/2026, đã 11 ngày chưa ai mở app để đọc.

**Lựa chọn:**
- (a) Người dùng đưa URL trong phiên quyết định; leader mở app bằng trình duyệt của leader và ghi kết quả vào `docs/STATE.md`. Hệ quả: đóng việc treo; URL của app công khai không phải bí mật nhưng cũng chưa có chỗ nào trong repo.
- (b) Người dùng tự mở app và báo "lên" hay "treo / lỗi cài gói". Hệ quả: không cần đưa URL, nhưng kết quả mất chi tiết lỗi nên khó tìm gốc.
- (c) Bỏ việc kiểm. Hệ quả: app công khai có thể đã hỏng từ 27/09 mà không ai biết; không ảnh hưởng sổ lệnh ảo.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), vì kiểm một lần tốn vài phút và là cách duy nhất biết `requirements.txt` ghim có chạy trên Cloud.

**Dữ kiện đã kiểm (08/10/2026):**
- `grep -rIl "streamlit\.app" --exclude-dir=.git --exclude-dir=.venv .` (chạy ở gốc repo) không ra tệp nào: repo không lưu URL.
- `gh api repos/Siner0808/vibe-stock-analysis --jq .homepage` cho `null`; mô tả repo không nêu URL; repo ở chế độ `public`.

---

## Q4 — "Mã thiếu giá thì từ chối cả bảng giá" của máy chấm xác nhận có giữ không, hay nới?

**Trạng thái:** chờ

**Nguồn:** `docs/STATE.md:21218 «CẢ bảng bị từ chối»` (BƯỚC 161, "chọn có chủ ý") · `docs/STATE.md:21258 «vẫn đòi phủ giá cho MỌI phiên chấm được»` (BƯỚC 162, rủi ro 3) · `docs/STATE.md:21260 «Một mã tạm ngừng giao dịch giữa chừng chặn cả bảng kéo»` (BƯỚC 162, rủi ro 5) · `cham_xac_nhan.py:23 «rồi từ chối cả bảng»`

**Ảnh hưởng:** số đo (tầng 3). Hai tài liệu đều ghi "nới là quyết định của người dùng". Giá thiếu ở một mã, một phiên bất kỳ trong cửa sổ chấm thì cả lượt chấm nổ, kể cả khi chỗ thiếu nằm SAU mốc đọc 252 phiên. Một mã tạm ngừng giao dịch giữa chừng chặn cả bảng kéo cho tới khi người kéo bỏ mã ấy bằng tay. Không đổi hành vi giao dịch ảo. Tần suất mã thiếu giá CHƯA đo (cần bộ kéo thật chạy trên máy có vnstock).

**Lựa chọn:**
- (a) Giữ bảo thủ như hiện tại. Hệ quả: không bao giờ điền giá; nhưng nếu một mã bị tạm ngừng, lượt chấm dừng cho tới khi người kéo bỏ mã khỏi bảng, và bỏ mã sau khi đã thấy kết quả có thể là chọn lọc (rổ chuẩn của nhãn là trung bình các mã của bảng, nên bỏ mã đổi cả rổ).
- (b) Nới theo quy tắc KÝ TRƯỚC: tự loại mã thiếu giá khỏi bảng theo một ngưỡng khai trước và ghi tên mã bị loại vào phán quyết. Hệ quả: sửa `cham_xac_nhan.kiem_phu` và bộ kéo `keo_bang_gia.keo`, thêm test; cần một ĐO ký trước vì đổi rổ chuẩn; làm sau khi đã nhìn số thì đụng bất biến 7.
- (c) Chưa quyết: giữ (a) cho tới khi bộ kéo thật chạy và đếm được mã thiếu giá (việc kế BƯỚC 162, mục (2)), rồi quyết với số trong tay. Hệ quả: hoãn nhưng không mất gì, vì mốc đọc còn xa (ước lượng đầu tháng 11/2027, `docs/LO-TRINH.md`).

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (c): giữ (a) tới khi có số đếm thật; chỉ khi bộ kéo thật cho thấy mã thiếu giá hay gặp mới mở (b) như một ĐO ký trước.

**Dữ kiện đã kiểm (08/10/2026):**
- `git grep -n "thieu gia trong cua so" -- cham_xac_nhan.py` ra dòng 242 (nơi `kiem_phu` từ chối); `git grep -n "rồi từ chối cả bảng" -- cham_xac_nhan.py` ra dòng 23.
- `git log -1 --format=%h -- keo_bang_gia.py cham_xac_nhan.py` ra `b14d270` (BƯỚC 162): hai tệp chưa đổi từ khi nêu rủi ro.
- Tần suất mã thiếu giá CHƯA đo: bộ kéo thật chưa chạy trên dữ liệu thật (BƯỚC 162, việc kế (2)); hôm nay không gọi vnstock.

---

## Q5 — Giữ hay xoá `scratch/luu_do18/` (18 tệp dữ liệu ĐO 18)?

**Trạng thái:** hết hiệu lực

**Nguồn:** `docs/HANDOFF.md:387 «xoá hẳn»` (khối cuối ngày 27/09: "Xoá hẳn thì hỏi người dùng") · `docs/STATE.md:19529 «scratch/luu_do18/wt_do18_p1»` · `docs/LO-TRINH.md:169 «giữ hay xoá»` (mục A5 liệt kê câu này)

**Ảnh hưởng:** chỉ dọn dẹp, cộng một hệ quả tái lập. Thư mục đã KHÔNG còn: BƯỚC 142 (`docs/STATE.md:19529`) tính "582 lệnh trong 35 tháng = 16,6 lệnh/tháng" trực tiếp từ `luu_do18/wt_do18_p1/wf_oos.db` ("chỉ đọc"), và con số ấy nay không chạy lại được từ đường dẫn đã ghi. `docs/STATE.md:19594` (ĐO 22) trỏ tới `../luu_do20/…`, thư mục này cũng đã mất.

**Lựa chọn:**
- (a) Ghi nhận thư mục đã mất và đánh dấu chỗ trích đường dẫn đã chết (STATE chỉ thêm: một dòng đánh dấu ở BƯỚC có việc thêm, không sửa mục cũ). Hệ quả: trung thực về chuyện "582 lệnh / 16,6 lệnh mỗi tháng" không tái lập được; không tốn đo đạc.
- (b) Dựng lại con số nhịp lệnh từ `scratch/luu_do22/` (4 tệp `wf_oos.db` của ĐO 22) hoặc từ một lượt chạy mới. Hệ quả: có số mới tái lập được, nhưng KHÁC số cũ (ĐO 22 đo 619 lệnh ở dòng theo ngày, không phải 582), nên phải gọi nó là số mới.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a) ngay, (b) chỉ khi một BƯỚC sau cần chính nhịp lệnh đó. Có một câu chỉ người dùng trả lời được và không chặn việc gì: thư mục đã bị xoá khi nào và bởi ai (repo không ghi dấu vết; người dùng cho phép xoá hẳn chưa từng được ghi lại).

**Bằng chứng (lệnh + ngày):** ngày 08/10/2026, `ls -d /c/Users/cuong/.gemini/antigravity/scratch/luu_do18*` báo "No such file or directory"; `find /c/Users/cuong/.gemini -maxdepth 6 ( -iname "luu_do18*" -o -iname "luu_do20*" -o -iname "wt_do18*" -o -iname "wt_do20*" )` không ra gì; `ls /c/Users/cuong/.gemini/antigravity/scratch` chỉ còn `luu_do22`.

**Dữ kiện đã kiểm (08/10/2026):**
- `find /c/Users/cuong/.gemini/antigravity/scratch/luu_do22 -type f` ra 8 tệp (4 nhật ký `.log` và 4 `wf_oos.db`), tổng 39.194.748 byte (`find … -printf '%s\n'` cộng lại). Thư mục này còn nguyên; hỏi giữ hay xoá nó là câu của lúc khác, KHÔNG nằm trong sổ này và không bị đụng hôm nay.
- Chỉ ĐỌC; không xoá, không di chuyển tệp nào ngoài repo.

---

## Q6 — `vnii` 0.2.6 gửi thêm tên hàm đang gọi (trường `operation`) mỗi lần kiểm giấy phép: chấp nhận hay chặn?

**Trạng thái:** chờ

**Nguồn:** `docs/HANDOFF.md:622 «gửi thêm tên hàm đang gọi»` · `docs/STATE.md:17152 «gửi thêm trường»` (BƯỚC 118, ĐO 17)

**Ảnh hưởng:** chỉ riêng tư; không đổi hành vi giao dịch và không đổi số đo. Công tắc `disable_telemetry()` người dùng bật 18/09/2026 thuộc `vnai` và không phủ đường này (docstring của `vnii` ghi "used only for telemetry"). Chưa đo, chưa chặn.

**Lựa chọn:**
- (a) Chấp nhận: `vnii` là gói đóng của hãng, kiểm giấy phép cần nó, và dữ liệu gửi chỉ là tên hàm. Hệ quả: không đổi gì; ghi rõ ranh giới này vào tài liệu để không ai nghĩ telemetry đã tắt hoàn toàn.
- (b) Cho một phiên con ĐO trước: xem `vnii` gửi những trường nào (chỉ đọc mã đã cài, không gọi mạng), rồi mới quyết chặn hay không. Hệ quả: tốn một BƯỚC; chặn đường này có thể làm kiểm giấy phép hỏng và đẩy hạng gói về `free` (`CLAUDE.md`: `vnai/beam/auth.py` nuốt lỗi rồi rơi về "free"), nên cách chặn phải khảo sát riêng.
- (c) Hỏi hãng về trường này, như đã làm với báo lỗi `vnstock_ezchart` (Q8). Hệ quả: chậm, phụ thuộc hãng.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a) tạm thời, kèm một dòng ranh giới; chỉ mở (b) nếu người dùng coi tên hàm là dữ liệu nhạy cảm.

**Dữ kiện đã kiểm (08/10/2026):**
- `./.venv/Scripts/python.exe -m pip list` (lọc `vnii`) ra `vnii 0.2.6`: phiên bản đang cài trùng bản đã nêu ở BƯỚC 118.
- Lệnh trên không chạm mạng và không gọi `vnii`. Chưa ai đo trường nào ngoài `operation` được gửi.

---

## Q7 — Dữ liệu BCTC `backtest/fundamentals/` nằm trong repo công khai: giữ hay chuyển ra ngoài?

**Trạng thái:** chờ

**Nguồn:** `docs/HANDOFF.md:609 «trong repo công khai»` (kèm "Người dùng kiểm điều khoản; chi tiết trong báo cáo audit") · `docs/STATE.md` BƯỚC 121 (audit toàn hệ thống; báo cáo đầy đủ là Artifact riêng tư của người dùng, repo chỉ có bản tóm tắt)

**Ảnh hưởng:** pháp lý và dọn dẹp, cộng một phụ thuộc của test. Repo ở chế độ `public`. Bản ghi không nói điều khoản dữ liệu của nguồn cho phép hay cấm, vì việc kiểm điều khoản thuộc người dùng và kết quả chưa được ghi lại. Tệp `tests/test_cache_bctc_du_ky.py` đọc đúng thư mục này (`KHO = GOC / "backtest" / "fundamentals"`).

**Lựa chọn:**
- (a) Giữ, sau khi người dùng đọc điều khoản và xác nhận cho phép. Hệ quả: không đổi gì; ghi kết quả đọc điều khoản (nguyên văn câu trả lời) vào sổ này để khép mục.
- (b) Chuyển ra ngoài repo: bỏ khỏi chỉ mục git, thêm vào `.gitignore`, và sửa `tests/test_cache_bctc_du_ky.py` để bỏ qua có điều kiện khi thiếu dữ liệu. Hệ quả: các commit cũ vẫn chứa tệp, vì `main` có ruleset cấm force-push nên lịch sử không viết lại được; đo IC BCTC (BƯỚC 53) không tái lập được trên CI nếu không có dữ liệu.
- (c) Giữ chỉ các tệp mà test thực sự cần, chuyển phần còn lại. Hệ quả: giảm diện phơi bày; cần liệt kê tệp nào test dùng.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** người dùng đọc điều khoản trước (việc duy nhất agent không làm hộ được), rồi chọn (a) nếu được phép, (b) hoặc (c) nếu không. Chưa có điều khoản trong tay thì chưa thể đề xuất nghiêng về phía nào.

**Dữ kiện đã kiểm (08/10/2026):**
- `git ls-files backtest/fundamentals | wc -l` ra `217` tệp; `git ls-files -z backtest/fundamentals | xargs -0 du -ck | tail -1` ra khoảng `5884` KB.
- `gh api repos/Siner0808/vibe-stock-analysis --jq .visibility` ra `public`.
- `grep -rln "fundamentals/" tests` (và các tệp mã gốc) chỉ ra `tests/test_cache_bctc_du_ky.py` là nơi đọc thư mục này trong test.

---

## Q8 — Gửi báo lỗi đóng gói của `vnstock_ezchart` cho hãng, hay giữ bản vá tại máy mãi?

**Trạng thái:** chờ

**Nguồn:** `docs/HANDOFF.md:628 «Báo lỗi đã soạn»` · `docs/STATE.md:17188 «HỎNG HAI LỚP»` (BƯỚC 119)

**Ảnh hưởng:** chỉ dọn dẹp và ranh giới với hãng; không đổi hành vi giao dịch hay số đo. Máy chạy bản vá tại máy `1.0.2+vibe1` (ba dòng `pyproject.toml`, không đụng mã). Khi hãng phát hành bản sửa, `tools/so_ban_goi.py` báo lệch ở hạng `QUYET DINH SO` và bản vá phải được thay bằng bản chính thức.

**Lựa chọn:**
- (a) Người dùng gửi báo lỗi đã soạn cho hãng. Hệ quả: hãng có thể sửa gốc; bản vá tại máy được thay khi có bản chính thức; vị trí bản nháp báo lỗi cần được leader nêu rõ khi trình (bản ghi không nêu đường dẫn).
- (b) Không gửi, giữ bản vá mãi. Hệ quả: máy khác (hoặc cài mới) gặp lại đúng lỗi thiếu `static/` và hai phụ thuộc khai là tuỳ chọn; `tools/so_ban_goi.py` tiếp tục báo lệch ở hạng quyết định.

**Đề xuất của leader (ĐỀ XUẤT, phiên A5 soạn nháp, chưa ai quyết):** (a), vì báo đã soạn xong, chi phí của người dùng là một lần gửi.

**Dữ kiện đã kiểm (08/10/2026):**
- `./.venv/Scripts/python.exe -m pip list` (lọc `ezchart`) ra `vnstock_ezchart 1.0.2+vibe1`: bản vá vẫn đang chạy.
- Chưa kiểm hãng đã phát hành bản sửa chưa (cần mạng ngoài kho hãng; hôm nay không gọi).

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
