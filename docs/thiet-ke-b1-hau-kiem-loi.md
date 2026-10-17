# Thiết kế B1 — hậu kiểm bằng lời cho mỗi lệnh ảo đã đóng

**Mốc:** B1 (`docs/LO-TRINH.md`, giai đoạn B). **Duyệt:** người dùng duyệt từng phần ngày
17/10/2026 trong phiên leader (BƯỚC 203). **Trạng thái:** thiết kế; chưa có dòng mã nào.

Tài liệu này là đề bài cho phiên làm mã. Luật chung của dự án (vá file, đột biến, năm cổng,
giao PR) nằm ở skill `quy-trinh-lam-viec` — đi theo nó, đừng chép lại vào đây.

---

## 1. Quyết định của người dùng (nguyên văn lựa chọn, 17/10/2026)

| Câu hỏi | Trả lời |
|---|---|
| Đoạn hậu kiểm dùng vào đâu? | *"Chỉ để bạn đọc (Recommended)"* |
| Model nào? | *"Opus 5.5 (Recommended)"* |
| Đoạn văn có những phần nào? | *"Kể lại và giải thích nhãn"*, *"Nói rõ điều một lệnh KHÔNG chứng minh"*, *"Điều nên theo dõi ở các lệnh sau"*, *"Một điểm kiến thức"* (cả bốn) |
| Trần chi tiêu mỗi tháng? | *"5 $ mỗi tháng (Recommended)"* |
| Chạy ở đâu, lưu vào đâu? | *"B: workflow riêng + tab mới (Recommended)"* |
| Phần 1–4 của thiết kế | *"Đúng, sang phần 2"* · *"Đúng, sang phần 3"* · *"Đúng, sang phần 4"* · *"Đúng, viết bản thiết kế"* |

Quyết định cũ còn hiệu lực: Q9 (`docs/QUYET-DINH-CHO.md`) — khoá `ANTHROPIC_API_KEY` do người
dùng tự đặt khi giai đoạn B mở (26/10/2026), có trần chi tiêu. Q13 — lệnh mở trước nhật ký
không tính vào tiêu chí ra khỏi B, không điền bù.

## 2. Mục đích và ranh giới

Mỗi lệnh ảo đã đóng có MỘT đoạn văn tiếng Việt do Claude viết từ số máy đã tính (nhật ký "vì
sao" + sổ bài học B3), để **người dùng đọc và học**. Đây là vế *"bằng lời"* của T2 và của tiêu
chí ra khỏi giai đoạn B (`docs/LO-TRINH.md`).

**CHỈ ĐỂ HIỆN**, cùng khuôn B6: đoạn văn hiện trên app, bản tin và tab Sheets của nó; nó KHÔNG
vào đường sinh lệnh, điểm, ngưỡng, điều kiện dừng, backtest hay vòng xác nhận tầng 3. Không
module nào trên các đường ấy được đọc tab `hau_kiem`.

## 3. Thành phần

```
Quét (quet-so-lenh.yml, không đổi)        Workflow mới hau-kiem-loi.yml (ngày làm việc)
run_daily -> tab nhat_ky  ──đọc──▶  1. chọn lệnh ĐÃ ĐÓNG chưa có dòng DAT ở tab hau_kiem
                                     2. tải giá các mã cùng ngành (đường giá của nút app)
                                     3. dựng dữ kiện: dòng nhật ký + bài học (so_bai_hoc)
                                     4. gọi Claude -> bốn trường văn
                                     5. máy kiểm đầu ra (mục 6)
                                     6. THÊM một dòng vào tab hau_kiem  ──▶  app + bản tin CHỈ ĐỌC
```

1. **`hau_kiem_loi.py` — module THUẦN** (khuôn `so_ke_hoach.py`, `so_bai_hoc.py`): nhận dữ liệu,
   trả dữ liệu; không nhập `anthropic`, không gọi mạng, không ghi đĩa. Mức module chỉ nhập
   thư viện chuẩn (`sheets_store` nhập file này để lấy lược đồ); các hàm cần `so_bai_hoc`,
   `nhat_ky_vi_sao`, `paper_metrics` nhập chúng TRONG hàm (BƯỚC 203). Chứa:
   - `COT_HAU_KIEM` — lược đồ tab (mục 7), một chỗ; `sheets_store` suy từ đây.
   - `du_kien(dong_nk, bai_hoc)` — bộ dữ kiện gửi đi. Chỉ chứa số ĐÃ tính bởi
     `nhat_ky_vi_sao` và `so_bai_hoc`; không công thức thứ hai.
   - `LUAT_VIET` — bảng luật viết (mục 6). `LOI_DAN` (lời dặn hệ thống) DỰNG TỪ bảng này, và
     `kiem_dau_ra()` kiểm theo chính bảng này: luật nói với model và luật máy kiểm là một.
   - `kiem_dau_ra(ket_qua, du_kien) -> list[vi phạm]`.
   - `GIA_USD_MOI_TRIEU` + `chi_phi_uoc(usage)` — mục 5.
   - `can_viet(dong_nk, dong_hk)` — lệnh nào cần viết (mục 4, bước 1).
2. **`tools/hau_kiem_loi.py` — phần chạy.** Chỗ DUY NHẤT nhập `anthropic`, nhập TRONG hàm (cùng
   luật với `vnstock_data`). Có `--thu`: in dữ kiện + lời dặn của từng lệnh sẽ viết, KHÔNG gọi
   API, không cần khoá.
3. **`sheets_store`** — tab `hau_kiem`: CHỈ THÊM dòng, khoá (`trade_id`, `lan`); hàm đọc cho
   app. Khuôn `ke_hoach` (BƯỚC 195): lệch cột thì cảnh báo, không dừng gì khác.
4. **`.github/workflows/hau-kiem-loi.yml`** — cron ngày làm việc sau giờ quét + `workflow_dispatch`.
   Khoá `ANTHROPIC_API_KEY` chỉ ở job này. Thư viện `anthropic` ghim `==` trong một file
   requirements RIÊNG (`requirements-hau-kiem.txt`) mà chỉ workflow này và `kiem-dinh.yml` cài
   (để test thấy gói thật) — Streamlit Cloud không cài nó. `tests/test_requirements.py` đọc thêm
   file ấy cho `tools/` và `tests/`, kèm gác: chỉ phần chạy được nhập `anthropic`, và nhập trong
   hàm (BƯỚC 203). Merge ở trạng thái
   TẮT (`gh workflow disable`) cho tới khi có khoá.
   - **Bẫy:** đừng cho workflow này chung `concurrency.group` với `quet-so-lenh`. Một nhóm của
     GitHub giữ tối đa MỘT lượt chờ; lượt chờ mới HUỶ lượt chờ cũ — lượt quét đang chờ có thể bị
     lượt hậu kiểm thay chỗ. Dùng nhóm riêng `hau-kiem-loi`. Đọc tab `nhat_ky` trong lúc quét
     đang đẩy có thể thiếu dòng; dòng thiếu được lượt sau nhặt (khoá là `trade_id`).
5. **Hiện ra:** app — khối sổ bài học (tab "📜 Lịch sử giao dịch"); bản tin B2 (`ban_tin.py`).
   Chỉ hiện dòng `DAT` mới nhất của mỗi lệnh, nhãn *"Claude viết · chỉ để đọc · máy chỉ kiểm số
   và câu chữ"*, bảng phân rã của máy đặt ngay cạnh.
6. **Chuông bài học** (`tools/chuong_bai_hoc.py`, `so_bai_hoc.do_phu_bai_hoc`): thêm vế "có lời" —
   lệnh đóng có dòng `DAT` trong vòng 1 phiên. Quần thể: lệnh đóng SAU ngày bật B1 (khuôn Q13,
   không điền bù).
7. **Cột `hau_kiem_loi` của `nhat_ky_vi_sao.COT_NHAT_KY` để trống, KHÔNG gỡ**: gỡ là đổi lược đồ
   tab `nhat_ky` (lệch cột thì `pull()` nổ). Sửa docstring ở dòng mô tả cột: đoạn văn nằm ở tab
   `hau_kiem` (B1).

## 4. Luồng một lượt chạy

1. Đọc tab `nhat_ky` và tab `hau_kiem` (chỉ đọc). Lệnh cần viết = ĐÃ CÓ bài học theo đúng
   tiêu chí của chuông (`so_bai_hoc.ly_do_thieu_bai_hoc` là None: nửa ĐÓNG và rổ chuẩn — BƯỚC 203)
   VÀ chưa có dòng `DAT` VÀ có ít hơn `SO_LAN_TOI_DA` = 2 dòng không `DAT`. Lệnh chạm 2 lần hỏng: không gọi nữa, in `::warning::` gọi tên để người xem.
2. Tải giá các mã cùng ngành qua đúng đường giá mà nút "📥 Tải giá…" của app dùng (rút phần
   không phụ thuộc Streamlit ra một hàm dùng chung; không viết đường giá thứ hai). Thiếu giá thì
   bài học nói "chưa đủ dữ liệu" như trên app — không đoán.
3. Cờ **cắt lỗ sát** cần giá `so_bai_hoc.N_PHIEN_SAU_THOAT` phiên SAU ngày ra, nên lúc viết (≤ 1
   phiên sau ngày ra) nó gần như luôn "chưa đủ dữ liệu". Đoạn văn nói đúng như vậy; app vẫn hiện
   cờ sống bên cạnh khi có. Không viết lại đoạn văn sau 5 phiên.
4. Kiểm trần tiền (mục 5) TRƯỚC mỗi lời gọi. Tối đa `SO_LENH_MOI_LUOT` = 10 lệnh mỗi lượt.
5. Gọi API (mục 5) → kiểm đầu ra (mục 6) → thêm MỘT dòng vào tab `hau_kiem` cho MỌI phản hồi có
   `usage` (kể cả bị từ chối, bị cắt, bị bác) để tổng tiền trong tab luôn đủ.

## 5. Lời gọi API

Bằng SDK Python chính thức. Mỗi lệnh một lời gọi, không hội thoại:

```python
client.beta.messages.create(
    model="claude-opus-5-5",
    max_tokens=8000,                 # gồm cả phần suy nghĩ; là trần tiền của một lời gọi
    system=LOI_DAN,
    messages=[{"role": "user", "content": <du_kien dạng JSON + yêu cầu>}],
    output_config={"effort": "medium",
                   "format": {"type": "json_schema", "schema": SCHEMA_BON_TRUONG}},
    betas=["server-side-fallback-2026-07-01"], fallbacks="default",
)
```

- **Schema bốn trường**, đều `string`, cả bốn `required`, `additionalProperties: false`:
  `ke_lai` · `khong_chung_minh` · `theo_doi` · `kien_thuc`.
- **Luật của Opus 5.5** (sai là lỗi 400 hoặc đọc nhầm): không gửi trường `thinking` (luôn bật;
  `disabled` và `budget_tokens` bị từ chối), không `temperature`/`top_p`/`top_k`, không prefill
  lượt assistant. Đọc chữ từ khối `type == "text"`, không từ `content[0]` (khối `thinking` đứng
  trước). Đọc bảng giá, model ID và tham số lúc làm mã bằng skill `claude-api` — đừng tin trí nhớ
  hay tài liệu này nếu hai bên lệch.
- **Effort:** bắt đầu `medium` (mặc định của Opus 5.5, đặt TƯỜNG MINH). Lượt chạy thật đầu tiên
  là phép đo (mục 9); hạ `low` hay giữ là quyết định của người dùng sau khi đọc.
- **`fallbacks="default"`** (bật theo khuyến nghị của Anthropic; người dùng giữ ở phần 2): bị bộ
  lọc an toàn từ chối thì máy chủ chạy lại trên model khác. Ghi `response.model` vào cột
  `model_phuc_vu` — đoạn nào không phải Opus 5.5 viết thì sổ nói ra. Batch API không nhận
  `fallbacks` (một lý do không dùng Batch).
- **`stop_reason`:**
  - `end_turn` → parse JSON từ khối `text` → kiểm (mục 6) → `DAT` hoặc `BI_BAC`.
  - `refusal` (cả chuỗi model từ chối) → `TU_CHOI`, ghi `stop_details.category`.
  - `max_tokens` → `CAT_CUT`.
- **Lỗi:** SDK tự thử lại 2 lần với 429 · 5xx · lỗi mạng; còn hỏng thì `::warning::`, không ghi
  dòng (không có `usage`), lượt sau làm lại. `AuthenticationError` · `PermissionDeniedError` ·
  `BadRequestError` → job ĐỎ (thoát khác 0): khoá sai hoặc yêu cầu sai hình dạng thì mọi lệnh
  đều hỏng, người dùng phải nhận email. Thiếu khoá hoặc không đọc được Sheets → ĐỎ.
- **Tiền:**
  - `chi_phi_uoc(usage)` nhân MỌI token với giá CAO NHẤT trong `GIA_USD_MOI_TRIEU` — bảng gồm
    Opus 5.5 và các model mà `fallbacks="default"` có thể chuyển sang (đọc
    `allowed_fallback_models` từ Models API lúc làm mã). Ước DƯ, không bao giờ ước thiếu. Có
    `usage.iterations` (model dự phòng đã chạy) thì lấy tổng các bước khi nó lớn hơn số cấp trên.
  - Trước mỗi lời gọi: tổng `chi_phi_usd_uoc` của các dòng trong THÁNG DƯƠNG LỊCH hiện tại (giờ
    Việt Nam, theo `viet_luc`) + trần một lời gọi > `TRAN_USD_THANG` = 5 → dừng lượt,
    `::warning::`. Trạng thái nằm trên Sheets, không ở runner.
  - Trần một lời gọi = số byte UTF-8 của `LOI_DAN` + nội dung gửi đi, nhân giá vào cao nhất
    (mỗi token chứa ít nhất một byte nên đây là cận TRÊN của token vào — kiểm giả định này bằng
    `count_tokens` trên một mẫu lúc làm mã) + `max_tokens` × giá ra cao nhất.
  - Trần cứng thật sự là trần chi tiêu của workspace trong Anthropic Console, người dùng tự đặt.
    Trần trong mã là lớp thứ hai.
- **Không dùng:** prompt caching và Batch API — mỗi lượt 1–3 lệnh, lợi không đáng kể.

## 6. Luật viết và máy kiểm (`LUAT_VIET`)

Đoạn văn chỉ thành `DAT` khi qua MỌI luật. Mỗi luật có một mã, một câu dặn model và một hàm kiểm.

| Mã | Luật | Máy kiểm |
|---|---|---|
| `so-co-nguon` | Mọi con số có nguồn (Quy tắc 2) | Mọi số trong bốn trường — phần trăm, số thập phân dấu phẩy, ngày — khớp một số trong `du_kien`. Làm tròn đúng số chữ số đã viết là khớp (−3,4567 → "−3,46%"). Ngày khớp theo giá trị, không theo định dạng. Phần kiến thức cũng không có số ví dụ tự đặt. Số kiểu Anh như `53,500` nằm trong CHUỖI nguồn (lý do vào lệnh của sổ thật) được nhận theo cả hai cách đọc; văn của model vẫn đọc dấu phẩy là thập phân (BƯỚC 204, đo bằng `--thu`). |
| `mot-lenh` | Không kết luận từ một lệnh (bất biến 5) | Cấm "chứng minh", "chắc chắn", "luôn luôn", "agent sai" — trừ khi đứng sau "không"/"chưa". "Tín hiệu sai" chỉ được dùng khi `du_kien` có `cach_goi`. |
| `khong-khuyen-nghi` | Không là lời khuyên đầu tư | Cấm "nên mua", "nên bán", "hãy mua", "hãy bán", "khuyến nghị" — trừ khi đứng sau "không"/"chưa". *(Bản duyệt đầu có "mua vào", "bán ra": bỏ ở BƯỚC 203 vì chúng bác nhầm văn tự nhiên như "giá mua vào ngày …".)* |
| `ma-co-nguon` | Không nhắc mã lạ | Mọi mã (ba ký tự in hoa đứng riêng) trong văn phải nằm trong một chuỗi của `du_kien` — mã của lệnh, mã cùng ngành, mã nhắc trong lý do vào — hoặc trong danh sách chữ viết tắt hợp lệ `VIET_TAT` (HOSE, RSI, ATR, ATC, …) đặt một chỗ. |
| `gia-thuyet-dan-nhan` | Giả thuyết phải dán nhãn | `theo_doi` mở đầu bằng "Chưa kiểm:". |
| `do-dai` | Gọn | `ke_lai` ≤ 180 từ; ba trường còn lại mỗi trường ≤ 80 từ. |

Bị bác → dòng `BI_BAC`, cột `ly_do_bac` ghi mã luật và đoạn vi phạm; app không hiện. Tối đa 2
dòng không `DAT` mỗi lệnh (mục 4).

**Giới hạn — nói ra trên app, không giấu:** máy bắt số bịa, câu cấm và mã lạ. Nó KHÔNG bắt được
một lập luận sai dùng toàn số đúng (gán nhầm nguyên nhân). Vì thế bảng phân rã của máy luôn đứng
cạnh đoạn văn.

## 7. Lược đồ tab `hau_kiem` (`COT_HAU_KIEM`)

Thứ tự cột là hợp đồng với tab (khuôn `COT_NHAT_KY`): `trade_id` · `lan` · `symbol` ·
`exit_date` · `trang_thai` (`DAT` / `BI_BAC` / `TU_CHOI` / `CAT_CUT`) · `ly_do_bac` · `ke_lai` ·
`khong_chung_minh` · `theo_doi` · `kien_thuc` · `model_yeu_cau` · `model_phuc_vu` · `effort` ·
`bam_loi_dan` · `bam_du_kien` · `token_vao` · `token_ra` · `chi_phi_usd_uoc` · `stop_reason` ·
`viet_luc`.

`bam_loi_dan` và `bam_du_kien` (sha256 rút gọn) cho biết đoạn văn được viết theo lời dặn nào,
từ dữ kiện nào — lời dặn đổi về sau thì đoạn cũ vẫn truy được nguồn.

## 8. Kiểm thử — offline, không tốn tiền

- **Client giả** trả đúng hình dạng phản hồi Opus 5.5: khối `thinking` rỗng TRƯỚC khối `text`;
  đủ `end_turn` · `refusal` (có `stop_details`) · `max_tokens` · model dự phòng viết thay
  (`response.model` khác); lỗi 429/5xx → cảnh báo; 401/400 → thoát khác 0.
- Mỗi luật của `LUAT_VIET` có ca đạt và ca bác. **Phát đột biến đầu tiên dựng lại lỗi thật:** một
  con số bịa nghe hợp lý ("lỗ 4,8%" khi dữ kiện là −5,21).
- **Gác AST:** module thuần không nhập `anthropic`; phần chạy nhập nó trong hàm; lời gọi không
  có `temperature`/`top_p`/`top_k`/`thinking`; model ID đúng chuỗi `claude-opus-5-5`; `LOI_DAN`
  dựng từ `LUAT_VIET`; `du_kien` gọi hàm của `so_bai_hoc`/`nhat_ky_vi_sao`, không tự tính.
- Tiền và lặp: chạm trần thì dừng trước lời gọi; lệnh có `DAT` không gọi lại; 2 dòng hỏng thì dừng.
- Đột biến mọi gác, lặp tới khi mọi phát đều đỏ (skill quy trình, Bước 3).

## 9. Triển khai

| Khi nào | Việc | Ai |
|---|---|---|
| Từ 17/10, trước 26/10 | Module thuần, phần chạy, tab, chỗ hiện trên app/bản tin, vế "có lời" của chuông; workflow merge ở trạng thái TẮT. Mỗi phần một BƯỚC, **Mốc:** B1. | agent |
| Khi phần chạy xong | `--thu` trên các lệnh đã đóng có nhật ký đầy đủ: in đúng dữ kiện + lời dặn sẽ gửi. Người dùng đọc, duyệt nội dung trước khi tốn đồng nào. | agent chạy, người dùng đọc |
| 26/10/2026 | Tạo khoá trong Anthropic Console (nên một workspace riêng, trần 5 $/tháng); thêm secret `ANTHROPIC_API_KEY` trên GitHub. Agent không bao giờ thấy khoá. | người dùng |
| Sau đó | Agent bật workflow, chạy tay một lượt = **phép đo**: viết cho mọi lệnh đã đóng có nhật ký đầy đủ (người dùng duyệt viết cho lệnh cũ — ngoài quần thể của chuông). Ghi chi phí thật (từ `usage`) và tỷ lệ `DAT` vào `docs/STATE.md`; người dùng đọc rồi chọn effort. | agent chạy, người dùng quyết |

Sổ tay NotebookLM: B1 không đổi luật hay kết luận đo → các BƯỚC khai `khong_bat_buoc_vi`,
`tools/buoc_cham_luat.py` xác nhận. BƯỚC nào chạm `docs/LO-TRINH.md` thì hỏi thật.

## 10. Ước lượng — CHƯA ĐO

Giá lấy từ bảng của skill `claude-api` (cập nhật 06/10/2026): Opus 5.5 4 $/20 $ mỗi triệu token
vào/ra. Giả định ~3.000 token vào và 300–400 từ tiếng Việt ra kèm phần suy nghĩ ở effort
`medium` → **ƯỚC LƯỢNG ~0,05–0,14 $ mỗi lệnh, ~2–3,5 $ mỗi tháng** với ≤ 25 lệnh đóng mỗi tháng.
Con số thật đến từ lượt đo ở mục 9; đừng chép ước lượng này vào nơi khác như một số đo.

## 11. Không làm

- Không cho agent hay tầng 3 đọc đoạn văn (người dùng chọn "Chỉ để bạn đọc").
- Không viết lại đoạn văn khi cờ cắt lỗ sát chín muồi sau 5 phiên.
- Không Batch API, không prompt caching, không dùng cột `hau_kiem_loi` của nhật ký.
- Không điền bù vế "có lời" của chuông cho lệnh đóng trước ngày bật B1.
