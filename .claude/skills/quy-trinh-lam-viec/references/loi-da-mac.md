# Lỗi quy trình đã mắc — thêm một dòng mỗi lần có lỗi mới

Đây là **bảng đếm**, không phải bài học đạo đức. Mỗi dòng phải trả lời
được: *máy chặn được không, và đã chặn chưa.*

Cột "bắt bởi" quan trọng ngang cột "lỗi": lỗi bắt được **bằng tình cờ**
là lỗi sẽ tái diễn.

> **Đọc bảng này thành SỐ:**
>
> ```bash
> ./.venv/Scripts/python.exe tools/doc_bang_loi.py
> ```
>
> Bảng không có cột **lớp** và cột **tuổi thọ** — chúng nằm ở
> `docs/loi-phan-lop.json`, tách ra vì sửa 34 dòng markdown là đúng loại
> thao tác đã sinh ra lỗi 1–3. Công cụ ghép hai bên rồi in ra: lớp nào
> còn sinh lỗi mới, một lỗi sống bao lâu trước khi bị bắt, và con số nào
> có lệnh đứng sau.
>
> **Số lỗi mỗi ngày KHÔNG phải thước** — nó tăng khi ta đào kỹ hơn. Đo
> 11/09/2026: bốn trên sáu lỗi tìm ra hôm ấy đã nằm sẵn từ 1 tới 16 ngày
> trước. Hai thước thật là **lớp nào đã im** và **tuổi thọ có ngắn lại
> không**.

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
| 23 | `cat > <file>` **đè mất một file test 40 phép kiểm đã có** — không kiểm file tồn tại chưa | đếm test: 834 thay vì 874. **Bốn cổng đều XANH** | ✅ | `cua_bash_an_toan` `heredoc-ghi-file-repo` (luật CÓ SẴN, cửa đang chết — lỗi 14) **+ từ 10/09/2026 `tools/kiem_so_test_khong_giam.py`, chạy trên CI nên KHÔNG phụ thuộc hook** |

| 24 | một câu ĐÚNG trong hợp đồng đã ký (*tập TÍN HIỆU* không đổi) được đọc thành một câu khác (*tập LỆNH* không đổi) — không điều kiện nào hỏi tập lệnh, nên nó không bao giờ được đo | tự đi đếm sau khi bảng đã đọc xong | ⚠️ một phần | chưa có luật; quy ước mới ở `docs/TIEU-CHI-DOC-TRUOC.md`: mọi câu *"X không đổi"* phải kèm lệnh kiểm X |

| 25 | một phép thử đo ĐÚNG MỘT cửa (`python --version` chỉ đi qua hook matcher `Bash`) được đọc thành phán quyết về **cả sáu** — câu "sáu cửa chết" chép lại ba ngày, trong khi bốn cửa vẫn chạy và có nhật ký | tự đo lại: một lượt Read sinh đúng **một** dòng nhật ký, đúng giây ấy | ✅ | `tools/kiem_cua_song.py` + dòng `CUA: n/m song` trong bản tin mở phiên |

| 26 | dựng một báo cáo BA trạng thái mà trạng thái *"chưa kiểm được"* **đánh mất tiền tố nhận dạng của chính nó**, nên dòng trạng thái biến mất khỏi bản tin — im đúng chỗ nó sinh ra để lên tiếng | CI đỏ trong khi **năm cổng tại máy đều xanh** (runner không có `~/.claude/settings.json`) | ✅ | `tests/test_cua_song.py::test_dong_CUA_van_CO_MAT_khi_KHONG_doc_duoc_settings` — mô phỏng môi trường CI, không phụ thuộc vào nó |

| 27 | **chép** một hook sang nơi đăng ký thứ hai mà không hỏi điều gì xảy ra khi **cả hai** nơi cùng nạp — hai ngày sau đo ra: mỗi hook chạy **HAI LẦN**, nhân đôi chính cái nhật ký đang dùng làm bằng chứng | phiên `claude -p` chạy với cwd đặt ở repo | ✅ | `tests/test_cua_song.py::test_settings_CUA_REPO_khong_duoc_dang_ky_hook_nao`; bản khai tách sang `docs/cua-du-an.json` |

| 28 | khẳng định *"PR này chưa chạm mã nguồn"* mà **không chạy `git diff --stat`** — nhánh tạo chồng lên nhánh khác nên mang theo commit lạ | cổng thứ năm: 916 so với 918 | ✅ | `tools/kiem_so_test_khong_giam.py` — số test là dấu vân tay của NỘI DUNG nhánh |

| 29 | một luật của cửa khai nguồn là *"quan sát về môi trường"* — không ngày, không lệnh — và lời khai ấy **sai**: lệnh nó cấm chạy trót lọt, mã thoát 0 | tự đo lại trên hai nhánh ném đi, sau 4 ngày | ✅ | `test_moi_luat_deu_khai_NGUON` gỡ cụm "môi trường" khỏi danh sách nguồn hợp lệ — câu về môi trường là PHÉP ĐO, phải có ngày |
| 30 | ba luật của cửa khớp **sự xuất hiện** của một chữ thay vì **vai trò** của nó; một luật tên là `…-file-repo` mà biểu thức **chưa bao giờ nhìn đường dẫn** | đếm được 8 chặn NHẦM / 3 chặn ĐÚNG trong hai ngày | ✅ | `cua_bash_an_toan.boc_va_tach()` + `DIEU_KIEN_THEM` + bảng TỐT/XẤU hai chiều |
| 31 | một phép kiểm đã ký **không thể đỏ**: nó so cache TRƯỚC với SAU khi kéo, mà phép hợp nhất giữ dòng cũ nên hai bên luôn bằng nhau | đo thẳng bản fetch thô trước khi hợp nhất | ⚠️ một phần | quy ước mới: mọi tiêu chí phải nói ra **đầu vào nào làm nó đỏ** |

| 32 | quy một đường dẫn về quy ước của HĐH **này** rồi hỏi `pathlib` của HĐH **kia** — `C:/Users/…` trên Linux không có `/` đầu nên bị đọc là TƯƠNG ĐỐI, và cửa chặn nhầm đúng cái mẫu nó vừa được sửa để tha | **CI đỏ ở lượt đầu, năm cổng tại máy đều xanh** | ✅ | `test_DUONG_TRONG_REPO_doc_giong_nhau_tren_MOI_he_dieu_hanh` — cấp cả bốn quy ước đường dẫn, không phụ thuộc nơi chạy |

| 33 | một con số về "34 kỳ BCTC" **không nói nó nói về BẢNG NÀO** — `balance`/`income` có 34 kỳ, `ratio` chỉ 2–4, và câu chữ không phân biệt (vế *"ratio là bảng agent đọc"* ở bản đầu **đã bị bác** — xem lỗi 36) | đếm lại khi điều kiện xem lại tưởng đã thoả, sau 16 ngày | ✅ | `tests/test_cache_bctc_du_ky.py` — mọi chỗ nhắc "34 kỳ" phải nói rõ bảng trong CÙNG mệnh đề |
| 34 | gác mới chỉ chạy trên dữ liệu SẠCH, nên **mọi đột biến NỚI LỎNG nó đều sống sót** — nới một phép kiểm ra thì nó vẫn xanh trên đầu vào sạch | đục thử: 3/6 sống, cả ba đều là phép nới | ✅ | tách phép phán thành hàm thuần rồi thử bằng CẢ đầu vào phải-qua LẪN phải-chặn |

| 35 | dòng tự khai ở cuối bảng này được **cộng dồn** mỗi lần thêm một lỗi thay vì **đếm lại** — lệch +1 suốt ba ngày, qua hơn mười commit | `tools/doc_bang_loi.py` ngay lượt chạy đầu tiên | ✅ | chính công cụ ấy: nó đọc số viết bằng chữ tiếng Việt rồi đối chiếu với số đếm được, mã thoát 1 khi lệch |

| 36 | suy một ĐƯỜNG ĐỌC từ chỗ trùng TÊN BẢNG mà không đọc `source=` và `period=` — ba đường cùng nhắc `ratio` hoá ra khác nguồn, khác độ mịn, khác cả chỗ lấy; kết luận sai đã lên `main` | tự truy tiếp cùng ngày, khi đi đo việc treo | ✅ | `tests/test_cache_bctc_du_ky.py` đọc bằng **AST** rằng phép đo IC không đọc `ratio`, và hai đường kia dùng hai nguồn khác nhau |

| 37 | đọc **ngược quy ước trả về** của `dot_bien` (True = đột biến BỊ GIẾT) trong script gọi nó — báo *"0/10 đỏ"* cho một bộ thật ra **10/10 đỏ**, tức một gác tốt báo cáo thành gác vô dụng | chính con số 0/10 vô lý, cùng phiên | ✅ | `va_an_toan.dot_bien_bo()` giữ quy ước ở MỘT chỗ và trả **danh sách phát sống sót** — rỗng là lành, nên đọc ngược một danh sách khó hơn đọc ngược một `bool` |
| 38 | viết một phép kiểm dạng `assert "tên" not in <mã nguồn>` rồi **chính docstring giải thích vì sao không đọc tên ấy** làm nó đỏ — đúng cái bẫy `in` mà `CLAUDE.md` đã ghi thành mục riêng | lượt chạy đầu tiên của chính test ấy | ✅ **một hình dạng** | `tests/test_gac_van_ban_phai_khai.py` (12/09/2026) chặn **đúng một hình dạng cú pháp**: `<định danh> in <biến gán từ .read_text()>`, phải kèm `# van-ban-ok: <lý do>`. Mẫu dựng tay trong gác ấy chính là nguyên văn lỗi này. **Lớp thì CHƯA đóng** — cùng ngày, hai hiện thân khác lọt qua (`"x" in c` trong một phép duyệt danh sách chuỗi), xem lỗi 44 |

| 39 | ký một phép đo có **nhóm chứng** mà không kiểm nhóm chứng có tồn tại không — ĐO 5b khai xong mới lộ ra nhóm chứng **rỗng theo cấu tạo**: 53 file chưa bị chạm đều nằm NGOÀI rổ đo | chính dụng cụ tự dừng ở lượt chạy đầu | ⚠️ một phần | dụng cụ trả mã thoát 2 và nói *"một nhóm rỗng → KHÔNG đọc được"*; nhưng phép đếm cỡ nhóm phải chạy **trước khi ký**, và chưa có gác nào bắt điều đó |
| 40 | nêu một **"chỗ không khớp"** bằng trực giác số học thay vì bằng phép tính — *"9 lệnh khác thì kỳ vọng đã phải dịch nhiều hơn thế"* sai, 9/385 chỉ mang trọng số 2,3%; nó điều hướng tám ngày | bấm máy khi đi đo chính nó | ⚠️ một phần | quy tắc 2 áp cho **lập luận** chứ không riêng kết quả: một câu về độ lớn cũng là một con số, và cũng cần một lệnh |

| 41 | chạy một phép đo **88,8 phút** mà sổ đã có câu trả lời — ĐO 5 dựng lại BƯỚC 25 (04/09), bằng đúng phương pháp worktree BƯỚC 25 đã mô tả; và chính phiên 04/09 vừa đo ra 376/376 vừa viết câu hỏi *"vì sao 385 ≠ 376"* vào `HANDOFF` | NotebookLM, một câu hỏi | ⚠️ một phần | `docs/soat-notebooklm.json` + `tests/test_soat_notebooklm.py` buộc khai một lượt soát chéo cho mỗi phép đo; soát chéo là thứ tìm ra nó |
| 42 | bỏ qua một **chỉ dẫn thường trực** ghi ở BA nơi (`SKILL.md`, rules toàn cục, bộ nhớ phiên) suốt bốn phép đo liên tiếp — người dùng phải nhắc **hai lần** | người dùng | ✅ | gác trên: một chỉ dẫn không có cơ chế thì nó chỉ là một lời nhắc, và lời nhắc thì trôi |

| 43 | một **bảng kết cục đã ký KHÔNG phủ kín** không gian đầu vào, và mã đọc nó có một nhánh `else` **dồn im lặng** cả vùng hở vào một ô — 1.250/10.201 điểm lưới của ĐO 6 | tự rà lại dụng cụ của chính mình sau khi đã công bố | ✅ | `tools/do6_tach_chi_phi.py` trả trạng thái thứ năm `NGOAI_BANG`; `tests/test_do6_tach_chi_phi.py` rà **toàn lưới** và bắt mọi ô chỉ được nhận điểm mà mô tả của nó phủ |

| 44 | mắc **lỗi 38 thêm hai lần nữa trong cùng ngày**, ở hai hình dạng gác vừa dựng KHÔNG thấy — một lần vì docstring của dụng cụ, một lần vì banner in ra màn hình, cả hai cùng nói *"KHÔNG đọc `paper_trades.db`"* | chính phép kiểm ấy đỏ oan, hai lượt liền | ⚠️ một phần | bỏ hẳn lối quét chuỗi, kiểm **cơ chế**: dụng cụ phải gọi `tempfile.gettempdir()` và đi qua `keo_so_co_thu_lai`. Lớp *đọc sự xuất hiện thay vì vai trò* vẫn CHƯA có gác chung, và có lẽ không có |

**Hai mươi bảy trên bốn mươi bốn máy chặn được.** Lỗi 4 hoá ra không phải lỗi
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


### Lỗi 25 — một phép thử hẹp, một kết luận rộng

Tài liệu dạy, và dạy ở **ba** chỗ cùng lúc:

> Chạy `python --version`. Bị chặn → sáu cửa đang sống. In ra số hiệu
> Python → **sáu cửa đang chết**.

Vế sau sai. Lệnh ấy đi qua đúng **một** hook: `PreToolUse` matcher `Bash`.
Bốn cửa `Read/Write/Edit` và `Stop` không nằm trên đường đi của nó.

Đo ngày 10/09/2026: bốn cửa ấy **đang chạy**, và chứng minh được bằng một
lượt Read — đúng một dòng mới trong nhật ký, đúng giây ấy. Cùng buổi đó
tôi nói "cửa chết" **ba lần**.

Nguyên nhân thật hẹp hơn nhiều: ngày 08/09 bốn hook được chép lên
`~/.claude/settings.json` bằng đường dẫn tuyệt đối; **hai hook thì
không** — và `python --version` tình cờ thử đúng một trong hai.

**Khác lỗi 22 ở đâu.** Lỗi 22: phép thử **hỏng**, nên không đo được gì.
Lỗi 25: phép thử **chạy và đúng**, nhưng phạm vi kết luận rộng hơn phạm vi
phép đo. Cái thứ hai khó thấy hơn vì không có gì trông sai cả.

**Quy ước rút ra:** trước khi viết một câu về N thành phần, hỏi phép thử
này chạm vào mấy thành phần. Chạm một thì viết về một.

Máy chặn được: `tools/kiem_cua_song.py` đọc trạng thái **từng** cửa, và
cửa mở phiên in nó ra mỗi lần khởi động, nên không ai còn phải suy.


### Lỗi 26 — trạng thái "chưa biết" phải tự xưng tên

Cả BƯỚC 48 viết về một chuyện: không ai **đọc** được trạng thái cửa, nên
ai cũng phải **suy**. Bản sửa là một công cụ ba trạng thái in ra một dòng
`CUA: n/m song`.

Rồi trạng thái thứ ba của chính công cụ ấy trả một thông điệp không mang
tiền tố `CUA:` — nên trên máy không có `~/.claude/settings.json`, bản tin
**mất hẳn dòng trạng thái**. Đúng cái im lặng vừa đi sửa.

Năm cổng tại máy xanh hết. CI đỏ, vì runner không có file cấu hình của
người dùng — một trục bất đối xứng local/CI chưa từng ghi trong dự án.

**Bài học rộng hơn cái cửa này:** một báo cáo ba trạng thái mà trạng thái
thứ ba im lặng thì thực tế chỉ còn hai, và cái thứ ba bị đọc thành *"không
có gì để nói"*. Trạng thái *"tôi không biết"* phải ồn ngang hai trạng thái
kia — nó là thông tin, không phải sự vắng mặt của thông tin.

Cùng gốc với luật *mã thoát 2 = chưa kiểm được* của bốn công cụ cổng: ở đó
tín hiệu là mã thoát, ở đây là một dòng chữ, và dòng chữ thì dễ quên hơn.

**Sửa ở NGUỒN, không sửa ở test.** Và phép kiểm mới **mô phỏng** môi trường
CI thay vì phụ thuộc vào nó — một test chỉ đỏ trên runner là một test không
ai chạy được lúc đang viết.


### Lỗi 27 — chép một đăng ký là tạo ra một trạng thái mới

Ngày 08/09/2026 bốn hook được chép từ `<repo>/.claude/settings.json` sang
`~/.claude/settings.json` để chúng chạy bất kể phiên mở ở đâu. Bản repo để
nguyên. Ngày 10/09 tôi chép thêm hai hook nữa theo đúng cách đó.

Không ai hỏi: **điều gì xảy ra khi cả hai nơi cùng nạp?**

Đo ngày 10/09: mở phiên ở repo thì **cả hai file cùng nạp và mỗi hook chạy
HAI LẦN**. Hai bản ghi `hook_success` riêng cho `SessionStart`, phân biệt
được bằng `statusMessage` của từng file.

Cái đắt không phải thời gian chạy. Nó **nhân đôi nhật ký
`cua_doc_bat_buoc`**, mà cùng sáng hôm ấy tôi dùng số dòng nhật ký làm bằng
chứng "bốn cửa đang sống". Phép đếm ấy sẽ sai gấp đôi ở đúng những phiên mở
tại repo — tức đúng những phiên người ta mở ra để đi kiểm cửa.

**Quy tắc rút ra: chép một đăng ký sang nơi thứ hai không phải là "thêm một
đường dự phòng", nó là tạo ra một trạng thái mới — "cả hai cùng có hiệu
lực" — và trạng thái ấy phải được đo trước khi tin.**

Bản vá 08/09 đúng về mục tiêu và bỏ sót một hệ quả. Cùng họ với lỗi 21
(một luật chọn tham số cũng là một trục) và lỗi 24 (một câu đúng bị đọc rộng
hơn phạm vi): ở cả ba, thứ gây hại không phải điều được làm sai, mà là điều
không được hỏi.


### Lỗi 28 — khẳng định về một diff mà không đọc diff

PR #85 khai *"chưa kéo một mã nào, chưa chạm mã nguồn"*. Nhánh có **hai**
commit: tiêu chí ĐO 4, và thay đổi mặc định của ĐO 3. Tôi tạo nhánh ĐO 4
chồng lên nhánh ĐO 3 thay vì từ `main`, rồi viết câu ấy mà không chạy
`git diff --stat`.

Thứ tôi khẳng định nằm cách **một lệnh**.

**Cổng thứ năm bắt được**, lần thứ hai trong ngày — và lần này ở một công
dụng không ai thiết kế: **số test là dấu vân tay của NỘI DUNG nhánh**, nên
một nhánh mang thêm mã sẽ lộ ra dù thân PR nói gì.

**Quy tắc rút ra: mọi câu về phạm vi một PR phải đọc từ `git diff`, không
đọc từ trí nhớ về việc mình vừa làm gì.**

Cùng họ với lỗi 24 và 25: điều gây hại không phải việc làm sai, mà là việc
không được hỏi — ở đây là một câu hỏi rẻ tới mức không ai nghĩ phải hỏi.


### Lỗi 29 — một luật sống bằng lời khai chưa ai đo

`cua_bash_an_toan` có một luật cấm xoá nhiều nhánh trong một lệnh — tên
nó viết trần ở đây là xoa-nhieu-nhanh, **không** đặt trong nháy ngược,
vì nó đã bị gỡ và một cái tên đã chết thì không được viết như một địa chỉ
còn sống (`docs/HANDOFF.md` mục 4). Luật ấy khai nguồn là *"quan sát về
môi trường: lệnh dạng này bị chặn ở đây"*. Không ngày, không lệnh, không
tra lại được.

Đo 11/09/2026 trên hai nhánh ném đi: `git push origin --delete a b` chạy
**trót lọt, mã thoát 0**, xoá được cả hai.

Luật bị **gỡ**, không phải sửa. Một luật không có nguồn hợp lệ thì không
có gì để sửa.

**Chỗ để lọt, và đó mới là phần đáng vá:** `test_moi_luat_deu_khai_NGUON`
chấp nhận cụm *"môi trường"* ngang hàng với một file quy ước. Nhưng quy
ước thì nằm trong file đọc được, còn **một câu về môi trường là một phép
đo** — nó phải có ngày. Cụm ấy đã bị gỡ khỏi danh sách.

Cùng họ với lỗi 17, và lần này ở trong chính công cụ dựng ra để chặn lỗi.

### Lỗi 30 — cửa đọc SỰ XUẤT HIỆN, không đọc VAI TRÒ

`CLAUDE.md` ghi từ 22/08/2026: *"Gác phải đọc AST, không đọc `in`"* — viết
cho test Python, **chưa bao giờ áp cho cửa Bash**.

Đếm hai ngày 10–11/09/2026: **8 chặn NHẦM / 3 chặn ĐÚNG**. Ba hình dạng:

- `git push -u origin nhanh && git branch -a | grep main`
  → `main` là đối số của `grep`, không phải đích của `git push`
- `gh pr create --body "... rm paper_trades.db ..."`
  → văn bản MÔ TẢ một lệnh xấu, không phải lệnh xấu
- `cat > /c/Users/…/Temp/x.py <<'EOF'`
  → ghi ra TEMP; luật tên `heredoc-ghi-file-repo` mà **biểu thức chưa
  bao giờ nhìn đường dẫn**

Cái thứ ba đáng đọc kỹ nhất: **tên luật mô tả đúng thứ nó phải làm, và
mã thì không làm thứ đó** — suốt từ ngày nó ra đời. Không ai đọc lại tên
để đối chiếu với biểu thức.

**Quy tắc rút ra: tên một luật là một lời hứa. Đọc lại nó và hỏi biểu
thức có giữ lời không.**

### Lỗi 31 — một phép kiểm đã ký KHÔNG THỂ ĐỎ

Tiêu chí ĐO 4, phép kiểm 2: *"so từng dòng vùng chồng lấn, TRƯỚC và SAU
khi kéo; lệch một dòng là DỪNG"*.

Nhưng `backtest/data.extend_history()` hợp nhất bằng
`drop_duplicates(subset="time", keep="first")` với cache đứng **trước** —
dòng cũ luôn thắng. So trước-với-sau thì **luôn bằng nhau**, bất kể nguồn
trả về gì. Phép kiểm không thể đỏ.

Rủi ro nó sinh ra để bắt thì có thật: đo thẳng bản fetch thô ngày
11/09/2026, hệ số điều chỉnh của nguồn đã đổi tới **−1,2%** so với cache
trên 1.172/1.217 phiên của VNM.

**Quy tắc rút ra: một tiêu chí phải nói ra ĐẦU VÀO NÀO LÀM NÓ ĐỎ.** Viết
xong thì hỏi ngược: "cái gì phải xảy ra để dòng này chặn tôi?" Không trả
lời được thì nó là trang trí.

Cùng họ với lỗi 24: một câu đúng về mặt chữ, đặt sai chỗ nó cần đứng.


### Lỗi 32 — hỏi sai hệ điều hành về một đường dẫn

Vá cho lỗi 30 cần biết *"đường dẫn này có trong repo không"*. Bản đầu quy
`/c/Users/…` của Git Bash về `C:/Users/…` rồi hỏi
`pathlib.Path.is_absolute()`.

Trên Windows: đúng. Trên Linux: `C:/Users/…` **không** có dấu `/` đầu nên
`PosixPath` đọc nó là TƯƠNG ĐỐI, rơi vào nhánh *"tương đối thì coi như
trong repo"*, và cửa **chặn nhầm đúng cái mẫu nó vừa được sửa để tha**.

**Năm cổng tại máy đều xanh. CI đỏ ở lượt đầu tiên.**

Đó là công dụng của CI mà không phép kiểm local nào thay được: nó chạy ở
một HĐH khác. Cùng hình dạng với lỗi 26 — chỗ đó là `~/.claude/
settings.json` không tồn tại trên runner; chỗ này là quy ước đường dẫn.

**Quy tắc rút ra: một phép kiểm về đường dẫn phải so bằng CHUỖI đã chuẩn
hoá, đừng mượn ngữ nghĩa của HĐH đang chạy.** Và test phải MÔ PHỎNG cả
hai quy ước, đừng chờ tình cờ chạy ở nơi kia.

Cùng họ với lỗi 15: *một công cụ đúng trong repo có thể sai khi được gọi
từ nơi khác.* Ở đây "nơi khác" là một hệ điều hành khác.


### Lỗi 33 — một con số không nói nó nói về cái gì

`CLAUDE.md` ghi ngày 23/08/2026: *"Cache BCTC nay là 71 mã × 34 kỳ"*, và
đặt điều kiện xem lại agent cơ bản là *"cache giá lùi được về 2018"*.

Ngày 11/09/2026 vế giá **đạt**. Điều kiện vẫn không thoả, vì đếm lại:

```
ratio    15 ky khac nhau · MOI MA chi 2-4   <- fundamental_agent DOC bang nay
balance  34 ky
income   34 ky
```

Câu *"34 kỳ"* đúng cho hai bảng và **sai cho bảng thứ ba** — bảng duy
nhất được đọc. Nó sống **16 ngày**.

> Bản đầu của dòng này ghi *"19 ngày"*, lấy từ ngày PHÉP ĐO chạy
> (23/08). Câu chữ vào `CLAUDE.md` ngày **26/08** (`ec9be2f`), nên tuổi
> thọ của LỖI là 16. Sửa 11/09/2026, khi cột tuổi thọ buộc phải nêu ra
> ngày sinh của nó — một con số bắt được một con số.

**Ràng buộc đã ĐỔI CHỖ mà không ai thấy:** trước là cache giá, nay là
cache `ratio`. Một điều kiện viết theo ràng buộc cũ sẽ báo "đã thoả" ở
đúng lúc nó không thoả.

Cùng hình dạng `N_DAY_DU` 596/451 và cờ C5 `True`/`False`: **một câu đúng
về thứ này được đọc thành đúng về thứ kia.** Lần này thứ bị nhầm là một
cái BẢNG, không phải một hằng số.

**Quy tắc rút ra: một con số về dữ liệu phải nói ra nó đếm CÁI GÌ, trong
cùng mệnh đề.** "34 kỳ" là vô nghĩa; "34 kỳ ở bảng `balance`" thì kiểm
được.

### Lỗi 34 — gác chỉ thấy dữ liệu sạch thì mọi phép NỚI đều sống

Đục thử gác của lỗi 33: **3 trên 6 đột biến sống sót**, và cả ba cùng một
loại — chúng **nới lỏng** gác (cửa sổ tìm từ 60 lên 400 ký tự, bội số so
sánh từ 2 xuống 1, bỏ hẳn phép so).

Lý do hiển nhiên sau khi thấy: gác chỉ chạy trên `CLAUDE.md` **thật**, tức
trên đầu vào đã sạch. Nới một phép kiểm ra thì nó vẫn xanh trên dữ liệu
sạch. Chỉ một đầu vào **phải bị chặn** mới giết được chúng.

Dự án đã viết luật này rồi, ở `tests/test_cua_quy_trinh.py`:

> **HAI CHIỀU, LUÔN LUÔN.** Một cửa chặn mọi thứ cũng vô dụng y như một
> cửa không chặn gì — nên mỗi phép kiểm có cả mẫu XẤU lẫn mẫu TỐT.

Luật ấy viết cho cửa Bash, và **không được áp cho gác tài liệu**. Cách
sửa: tách phép phán thành **hàm thuần**, rồi thử nó bằng cả hai chiều —
không phải chỉ chạy nó lên file thật.

Sau khi sửa: **7/7 đột biến đỏ**.

**Quy tắc rút ra: một gác chỉ được thử trên đầu vào thật là một gác chưa
được thử.** Đầu vào thật hôm nay sạch; nó không nói gì về việc gác có
chặn được cái bẩn hay không.


### Lỗi 35 — con số tổng của chính bảng lỗi đã trôi ba ngày

Cuối bảng có một câu dạng *"Hai mươi mốt trên ba mươi tư máy chặn được."*
Viết bằng **chữ**, nên không máy nào từng đối chiếu nó với bảng.

`tools/doc_bang_loi.py` đếm ngay lượt chạy đầu tiên: bảng khai **22**,
đếm được **21**. Dựng lại từng bản trong git:

```
d019f9f  07/09  "Tam tren muoi ba"            that  8/13   dung
910dcf7  08/09  "Tam tren muoi bon"           that  7/14   LECH tu day
40820cf  08/09  "Chin tren muoi lam"          that  8/15
5615f09  08/09  "Muoi mot tren muoi chin"     that 10/19
955fc6b  10/09  "Muoi ba tren hai muoi bon"   that 12/24
HEAD     11/09  "Hai muoi hai tren ba muoi tu" that 21/34
```

Lệch **đúng +1 suốt ba ngày**, vì con số được **cộng dồn** mỗi lần thêm
một dòng thay vì **đếm lại**. Một lần cộng sai rồi mọi lần sau kế thừa.

Đúng lớp `chua-do`, và ở chỗ trớ trêu nhất: **bảng đếm lỗi tự nó chứa một
con số chưa ai đếm.**

Còn một tầng nữa đáng ghi. Lượt chạy đầu của công cụ ra **19/34**, không
phải 21 — vì nó tách cột bằng `split("|")`, mà hai dòng của bảng viết
`` `pytest \| tail` `` với dấu ống **đã thoát**. Tách thô cắt nhầm giữa ô
mô tả, đẩy mọi cột sau sang một bậc. Đó là **lỗi 30 ở một chỗ mới**: đọc
SỰ XUẤT HIỆN của ký tự `|` thay vì vai trò NGĂN CỘT của nó.

**Quy tắc rút ra: một con số tổng phải do LỆNH sinh ra, không do người
cộng dồn.** Nếu buộc phải viết nó ra bằng chữ thì phải có phép kiểm đọc
lại chữ ấy.


### Lỗi 36 — suy một đường đọc từ chỗ trùng tên

Sáng 11/09/2026 tôi thấy hai chỗ cùng nhắc bảng `ratio`:

```
backtest/fundamentals/*_ratio.csv     chi 2-4 ky moi ma
fundamental_agent.py                  docstring: "doc bang ratio"
```

và kết luận: *"`ratio` là bảng agent thật sự đọc, nên điều kiện xem lại
agent cơ bản không thoả — dừng, đừng đo IC."* Kết luận ấy **lên `main`**.

Đọc tiếp hai dòng nữa thì thấy ba đường khác hẳn nhau:

| đường | nguồn | độ mịn | lấy ở đâu |
|---|---|---|---|
| cache `*_ratio.csv` | VCI | quý | đĩa — **không ai đọc** |
| `fundamental_agent` | **KBS** | **năm** | gọi mạng lúc chạy |
| phép đo IC | — | quý | **chỉ** `_income` + `_balance` |

Chữ `ratio` xuất hiện **0 lần** trong `experiment_fundamentals.py`.

**Hệ quả thật:** đếm bằng chính dụng cụ định nghĩa đại lượng ấy thì số kỳ
dùng được là **31**, không phải 4 — **điều kiện ĐÃ THOẢ**, và tôi đã dừng
sai lý do. Chạy tiếp thì ra một kết quả đáng giá: chỉ số duy nhất từng có
tín hiệu thô (`leverage`) **mất** tín hiệu khi cỡ mẫu tăng 65%.

**Quy tắc rút ra: trùng TÊN không phải cùng ĐƯỜNG.** Một khẳng định về
"mã X đọc dữ liệu Y" phải đi theo lời gọi — đọc `source=`, `period=`,
đường dẫn — chứ không suy từ chỗ hai nơi cùng dùng một chữ.

Cùng họ lỗi 30 và 35, và cả ba cùng một hình dạng: **đọc sự xuất hiện của
một chữ thay vì vai trò của nó.** Lỗi 30 ở dấu `|` trong lệnh shell, lỗi
35 ở dấu `|` trong bảng markdown, lỗi 36 ở tên một bảng dữ liệu.


### Lỗi 37 — đọc ngược quy ước trả về của chính dụng cụ đục thử

Ngày 12/09/2026, đục thử một gác mới bằng mười phát. Script in ra:

```
0/10 do
SONG SOT: tieu chi KHONG THE DO, hai o bac bo tron lam mot, ... (ca 10)
```

Đọc đúng thì phải dừng lại: một bộ mười phát mà **không phát nào** bị bắt,
trong khi bộ test vừa viết có hẳn một phép kiểm cho từng phát, là chuyện gần
như không thể. Con số vô lý ấy là thứ cứu lượt này.

Nguyên nhân nằm ở một dòng:

```python
ket = dot_bien(F, cu, moi, BO)
if ket:                 # <- doc la "song sot"
    song.append(ten)
```

`dot_bien` trả `True` khi đột biến **bị giết**. Docstring của nó nói rõ
(*"Trả True khi kết quả đúng `mong_doi` ("DO" = lệnh phải thất bại)"*) và
tôi đã không đọc. Thật ra **10/10 đỏ**.

**Chiều của lỗi mới là chỗ đáng ghi.** Nó báo động GIẢ, tức chiều an toàn —
tôi đi tìm một lỗ hổng không có. Cùng một dòng đọc ngược ở chiều kia sẽ in
"10/10 đỏ" cho một bộ **0/10** và không ai biết. Lần này may.

Cùng họ với bẫy `pytest ... | tail` (lỗi 26): **đọc một giá trị trạng thái
theo quy ước mình tưởng, thay vì quy ước nó khai.** Ở đó là mã thoát của ống,
ở đây là `bool` của hàm.

**Máy chặn được:** `va_an_toan.dot_bien_bo()` nay chạy cả bộ và trả **danh
sách phát sống sót**. Rỗng là lành. Không còn chỗ cho người gọi tự dịch một
`bool`, và một danh sách khác rỗng thì không đọc thành "ổn" được.

### Lỗi 38 — tài liệu hoá một cái bẫy không ngăn được việc mắc lại nó

Cùng phiên, cùng file. Tôi viết một phép kiểm khoá đúng bài học BƯỚC 28:

```python
ma = duong.read_text(encoding="utf-8")
assert "conclusion" not in ma, "dung cu dang loc theo ket cuc"
```

Nó đỏ ngay lượt chạy đầu — vì **docstring của chính dụng cụ** giải thích
*vì sao nó không lọc theo kết cục*, và câu giải thích ấy chứa đúng chữ đó.

`CLAUDE.md` có hẳn một mục tên **"Gác phải đọc AST, không đọc `in`"**, mở
đầu bằng hai gác mắc đúng lỗi này ngày 22/08/2026. Tôi đã đọc mục ấy trong
cùng phiên, ở bước đọc tài liệu bắt buộc.

**Điều rút ra không phải "phải cẩn thận hơn".** Là: một cái bẫy được tài
liệu hoá rõ ràng, đọc trong cùng phiên, vẫn bị mắc lại — nên **tài liệu
không phải cơ chế chặn**. Thứ chặn được là bắt phép kiểm đi qua AST, và
`_chuoi_khong_phai_docstring()` trong `tests/test_do_roi_nhip.py` làm việc
đó: gom mọi chuỗi hằng TRỪ docstring.

Chưa chặn toàn cục: không có gác nào bắt được một `assert "x" not in <văn
bản>` mới viết ra trong `tests/`. Đó là lý do dòng 38 mang dấu ⚠️.


### Lỗi 39 — ký một phép đo mà chưa đếm nhóm chứng

ĐO 5b (12/09/2026) dựng trên một thí nghiệm tự nhiên: `backtest/cache/` mang
hai thế hệ file, **53 file kéo 06–08/08** làm nhóm chứng và **72 file kéo
03/09** làm nhóm thử. Tiêu chí được viết đầy đủ, ký, qua năm cổng, vào
`main`.

Chạy xong mới lộ: **nhóm chứng rỗng.** Không phải ít mã — **không mã nào.**

```
nhom 08/08:  53 file  ->   0 file nam trong ro do (khong ma nao co moc)
nhom 03/09:  71 file  ->  71/71 nam trong ro
```

Lượt kéo 03/09 ghi lại đúng toàn bộ rổ đo, nên 53 file kia đều là mã **ngoài
rổ** — không mốc, không vùng OOS, không so được gì.

Một truy vấn duy nhất trước khi ký sẽ bắt được: *đếm xem mỗi nhóm còn bao
nhiêu mã sau khi lọc*. Tôi đã đếm **file**, và không đếm **mã dùng được**.

**Quy tắc rút ra: một thiết kế có nhóm chứng phải ĐẾM cỡ hai nhóm trước khi
ký, không phải sau khi chạy.** Cùng họ lỗi 31 — ở đó một ô không thể đỏ, ở
đây một nhóm không thể có mẫu; cả hai làm phép đo mất khả năng phân biệt
trước khi nó bắt đầu.

Phần làm đúng: tiêu chí đã tách sẵn *"phép đo không chạy được"* khỏi *"phép
đo chạy và không thấy gì"*, nên kết quả rỗng không bị đọc thành kết quả âm.

### Lỗi 40 — một "chỗ không khớp" nêu bằng trực giác, không bằng phép tính

Ngày 04/09/2026 tôi ghi vào `docs/STATE.md`:

> *"`CLAUDE.md` ghi 385 lệnh; `d777480` chạy hôm nay ra 376. Alpha và kỳ
> vọng khớp tới ba chữ số nhưng số lệnh lệch 9. **Nếu 9 lệnh thật sự khác
> thì kỳ vọng đã phải dịch nhiều hơn thế.** Chưa truy tiếp."*

Câu in đậm là một khẳng định **định lượng**. Nó chưa bao giờ được tính. Nó
sống **tám ngày** và điều hướng cả một phép đo.

Bấm máy, 10 giây:

```
385 x -0,291 = -112,035        376 x -0,293 = -110,168
9 lenh chenh -> tong -1,867 -> TB -0,207%
```

Chín lệnh ấy lãi trung bình **−0,207%** so với **−0,293%** của toàn mẫu.
Bình thường. Và kể cả nếu chúng lãi trung bình **+5%**, kỳ vọng cũng chỉ
dịch **0,124 điểm** — vẫn "khớp tới hai chữ số". Chín trên 385 mang trọng
số 2,3%; ràng buộc ấy lỏng, chưa bao giờ chặt.

**Quy tắc rút ra: quy tắc số 2 áp cho LẬP LUẬN, không riêng cho KẾT QUẢ.**
*"Đã phải dịch nhiều hơn thế"* là một câu về độ lớn, tức một con số, tức
cần một lệnh. Một câu như vậy không có lệnh đứng sau thì không được dùng
để mở — hay để đóng — một câu hỏi.

Cùng họ lỗi 6 (ước 40s, thật 167,7s): chỗ nguy hiểm không phải con số bịa,
mà là **con số không ai nghĩ là con số**.


### Lỗi 41 — đo lại một thứ sổ đã đo, bằng đúng phương pháp sổ đã ghi

Ngày 12/09/2026, ĐO 5 chạy hai lượt walk-forward — **88,8 phút** — để trả
lời: *chênh lệch 385 so với 376 lệnh ngoài mẫu là do MÃ hay do CACHE?*

Kết quả: `79a8d32` và `d777480` trên cùng cache hôm nay đều cho **376**.

`docs/STATE.md` BƯỚC 25, viết **04/09/2026**, đã có đúng bảng ấy:

```
79a8d32  28/08  376 lenh
d777480  31/08  376 lenh
```

Và đã mô tả đúng phương pháp tôi tưởng là của mình:

> *"`backtest/cache/` bị gitignore nên nó KHÔNG đổi khi checkout mã cũ.
> Dựng worktree ở commit nền rồi chạy mã cũ trên dữ liệu hôm nay."*

**Chỗ mỉa mai nằm sâu hơn.** Việc treo trong `HANDOFF` ghi *"lượt chạy lại
ngày 04/09 (385 so với 376)"* — con số 376 ấy **chính là** con số BƯỚC 25.
Phiên ngày 04/09 vừa đo ra nó, vừa viết câu hỏi về nó vào sổ bàn giao, mà
không thấy bảng của chính mình đã loại vế mã.

Cùng họ **lỗi 9**: *không tìm lời giải sẵn có trước khi tự viết lời giải.*
Khác ở cái giá — lần trước là vài phút gõ lại, lần này là 88,8 phút máy và
hai lượt CI.

**Quy tắc rút ra: trước một phép đo TỐN KÉM, tra sổ bằng một luồng ĐỘC LẬP,
không bằng trí nhớ của chính mình.** `grep` chỉ tìm được thứ mình đã biết
tên; ở đây cái tên đúng là "BƯỚC 25", và tôi không biết mình cần nó.

### Lỗi 42 — một chỉ dẫn thường trực ghi ở ba nơi vẫn trôi

Ngày 10/09/2026 người dùng chốt: dùng NotebookLM thường xuyên như một luồng
độc lập. Chỉ dẫn ấy được ghi vào **ba** nơi: mục riêng trong `SKILL.md`,
thư mục rules toàn cục, và bộ nhớ phiên.

Nó trôi qua **bốn** phép đo liên tiếp — ĐO 1, 2, 3, 4 — rồi qua cả ĐO 5 và
ĐO 6 của ngày 12/09. Người dùng phải nhắc **lần thứ hai**, kèm câu *"vấn đề
này tôi đã note 2 lần"*, mới được làm.

Cùng ngày, **một câu hỏi duy nhất** gửi công cụ ấy lôi ra lỗi 41.

**Quy tắc rút ra, và nó là quy tắc về CƠ CHẾ chứ không về ý chí: một chỉ
dẫn thường trực không có gác thì nó chỉ là một lời nhắc, và lời nhắc thì
trôi.** Ghi ở ba nơi thay vì một nơi không đổi điều đó — nó chỉ làm việc bỏ
sót trông khó tin hơn khi nhìn lại.

Gác: `docs/soat-notebooklm.json` + `tests/test_soat_notebooklm.py`. Nó
không ép phải soát; nó ép phải **khai** đã soát hay chưa. Cùng cơ chế
`# bia-ok:` — mục đích không phải cấm, mà là buộc nói ra.

Và nó **không** bắt được việc soát hời hợt. Nó chỉ làm việc bỏ sót không im
lặng được nữa. Đó là đúng thứ đã hỏng, không hơn.


### Lỗi 43 — một bảng bốn ô không phủ kín, và nhánh `else` bịa nghĩa cho chỗ hở

Sáng 12/09/2026 tôi ký bảng đọc của ĐO 6 với **bốn** kết cục:

```
1  TAC DONG >= 50%  VA  BUOC GIA < 25%
2  BUOC GIA >= 50%  VA  TAC DONG < 25%
3  ca hai >= 25%
4  ca hai < 25%
```

Rồi viết dụng cụ đọc nó bằng `if / elif / elif / else`. Chiều cùng ngày, rà
lưới 101×101:

```
1.250 / 10.201 diem KHONG ung voi mo ta nao
vung: mot ve nam trong [25%, 50%), ve kia duoi 25%
ca 1.250 diem bi nhanh `else` don vao KET CUC 4
```

Kết cục 4 nói *"cả hai vế đều < 25%"*. Một điểm như (30%, 10%) **không**
thoả câu đó, mà vẫn được đọc thành kết cục 4.

**Kết luận đã công bố không bị ảnh hưởng** — điểm thật (74,6% · 45,6%) rơi
vào ô 3 và khớp đúng mô tả ô 3. Nhưng đó là **may**, không phải thiết kế.

**Khác lỗi 31, và khác ở chỗ quan trọng.** Lỗi 31 là một ô *không thể đạt
tới* — phép kiểm mất khả năng phân biệt. Ở đây cả bốn ô **đều** đạt tới
được; thứ hỏng là bảng không **phủ kín**, và mã lặng lẽ lấp chỗ hở bằng một
ô có sẵn. Một cái là lỗ hổng ở đầu ra, một cái là lỗ hổng ở đầu vào.

**Cách sửa KHÔNG phải nới ngưỡng** — tiêu chí cấm thẳng điều đó sau khi thấy
số. Cách sửa là thêm một trạng thái thứ năm `NGOAI_BANG`, cùng lý do
`tools/kiem_cu_phap_311.py` phải có mã thoát 2 *"chưa kiểm được"* và
`vnstock_goi.kiem_goi()` phải có `CHƯA KIỂM ĐƯỢC`:

> **"Không biết" là một câu trả lời, và nó không được giả dạng một câu trả
> lời khác.**

**Quy tắc rút ra: một bảng n ô phải được rà trên TOÀN không gian đầu vào,
không chỉ ở n điểm đại diện.** Thử một điểm cho mỗi ô chứng minh ô ấy đạt
tới được — nó **không** chứng minh n ô cộng lại phủ kín. Hai việc khác
nhau, và tôi đã làm việc thứ nhất rồi tưởng đã làm cả hai.


### Lỗi 44 — một dấu ✅ hứa nhiều hơn thứ nó giao

Sáng 12/09/2026 tôi dựng `tests/test_gac_van_ban_phai_khai.py` và nâng dòng
38 từ ⚠️ lên **✅**. Chiều cùng ngày, viết `tests/test_doc_so_that.py`, tôi
mắc lại **hai lần nữa**:

```
lan 3:  assert "paper_trades" not in <moi chuoi hang cua file>
        -> DO OAN vi DOCSTRING giai thich *vi sao KHONG doc so o may*

lan 4:  cung phep kiem, sau khi da bo docstring ra
        -> DO OAN vi mot BANNER in ra man hinh noi dung cau ay
```

Gác vừa dựng **không thấy cả hai**. Nó canh đúng một hình dạng cú pháp —
`<định danh> in <biến gán từ .read_text()>` — còn đây là `"x" in c` trong
một phép duyệt danh sách chuỗi. Giới hạn ấy **đã được khai trước** khi dựng
gác (*"mở rộng ra là quay lại con số 407"*), nên gác không sai; **cái sai là
dấu ✅ tôi đặt cho dòng 38**, vì nó đọc thành *"lớp này đã đóng"*.

**Hai điều rút ra, và điều thứ hai quan trọng hơn:**

1. **Nhắc một cái tên KHÁC với làm điều đó.** Cả bốn lần đều là một phép
   kiểm hỏi *"văn bản có chứa chữ X không"* trong khi điều cần biết là
   *"mã có LÀM việc X không"*. Đường đúng là kiểm **cơ chế**: dụng cụ phải
   gọi `tempfile.gettempdir()` và đi qua `keo_so_co_thu_lai`.

2. **Một dấu ✅ phải nói rõ nó chặn được CÁI GÌ.** Dòng 38 nay ghi
   *"✅ một hình dạng"* kèm tên hình dạng ấy. Một ô ✅ không nêu phạm vi là
   một lời hứa rộng hơn cái gác, và nó làm người đọc sau thôi cảnh giác ở
   đúng chỗ vẫn còn hở.

Lớp *đọc sự xuất hiện của một chữ thay vì vai trò của nó* — lỗi 30, 35, 36,
38, 44 — vẫn **chưa có gác chung**, và có lẽ không có: nó là một hình dạng
**tư duy**, không phải một hình dạng **cú pháp**. Thứ dựng được là gác cho
từng hiện thân, và đếm cho đúng còn bao nhiêu hiện thân chưa có gác.
