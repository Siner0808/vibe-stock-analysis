# Phần D — gói tin trước/sau khi thêm hai nguồn Báo Xây dựng vào `aviation_logistics` (4 mã × 3 vòng xen kẽ, mạng thật, chỉ đọc)

Lệnh (chạy 16/11/2026 ~15:20–15:35 ICT; mỗi lượt MỘT tiến trình mới, nghỉ 20 giây giữa hai lượt; cây "cũ" = `main` `2f925ea`
ở `vibe_preview`, cây "mới" = nhánh `sua/nguon-tin-hang-khong-281` ở `vibe_wt_281`, mỗi bên chạy bằng mã CỦA CÂY ĐÓ):

```
cd <cây> && ../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_281/do_goi_tin_281.py <cu|moi>_<vòng> goi_<cu|moi>_<vòng>.json HVN ACV VSC ACB
../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_281/so_goi_tin_281.py     # bảng dưới
../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_281/khac_bai_281.py       # so từng BÀI (mục "Đọc")
```

`do_goi_tin_281.py` là bản chép NGUYÊN VĂN của `do_goi_tin_280.py` (BƯỚC 280): `NewsOrchestrator(mã).collect_and_handoff()`
(cùng đường app dùng) rồi `NewsSentimentAgent().analyze(gói)` và `normalize` trích nguyên văn từ `master_agent.py`. Không ghi sổ, không
Google Sheets, không `run_daily`. Vòng 1 và 2: cũ → mới; vòng 3 đảo thứ tự (mới → cũ) cho khỏi thiên về một bên. Mã: ba mã của rổ về hàng không /
cảng / logistics theo phán đoán (HVN, ACV, VSC) và một mã khác (ACB). sha256 `news_collectors.py`: cũ `d5b243bcf1f1`, mới `8fe9b0be1ba4`.

## Bảng (articles = số bài của nhóm `aviation_logistics`; `news_score` = điểm tin app hiện)

| vòng | mã | articles nhóm hàng không cũ → mới | `total_articles` | `news_score` | `sentiment_score` |
|---|---|---|---|---|---|
| 1 | HVN | 0 → 8 | 192 → 200 | 50,8 → 50,8 | 1,54 → 1,54 |
| 1 | ACV | 0 → 8 | 192 → 200 | 51,4 → 51,4 | 2,86 → 2,86 |
| 1 | VSC | 0 → 8 | 192 → 200 | 50,8 → 50,8 | 1,54 → 1,54 |
| 1 | ACB | 0 → 8 | 192 → 200 | 51,0 → 51,0 | 1,98 → 1,98 |
| 2 | HVN | 0 → 8 | 192 → 194 | 50,8 → 50,8 | 1,54 → 1,63 |
| 2 | ACV | 0 → 8 | 192 → 194 | 51,4 → 51,5 | 2,86 → 3,07 |
| 2 | VSC | 0 → 8 | 192 → 194 | 50,8 → 50,8 | 1,54 → 1,63 |
| 2 | ACB | 0 → 8 | 192 → 194 | 51,0 → 51,1 | 1,98 → 2,11 |
| 3 | HVN | 0 → 8 | 192 → 200 | 51,1 → 50,8 | 2,29 → 1,54 |
| 3 | ACV | 0 → 8 | 192 → 200 | 51,8 → 51,4 | 3,61 → 2,86 |
| 3 | VSC | 0 → 8 | 192 → 200 | 51,1 → 50,8 | 2,29 → 1,54 |
| 3 | ACB | 0 → 8 | 192 → 200 | 51,4 → 51,0 | 2,73 → 1,98 |

Nhóm hàng không: **0 → 8 bài ở cả 12 cặp** (2 nguồn × `max_items` 4); bốn mã nhận CÙNG tám bài (gói ngành không phụ thuộc mã:
`news_collectors.py`, `SectorNewsAgent.collect` nhận `symbol` rồi bỏ qua). Tám bài của vòng 1 (HVN): bốn bài hàng không đầu của `hang-khong.rss` (Vietnam
Airlines tuyển dụng ...; Vietjet lập cú đúp giải thưởng ... — nhãn POSITIVE; Chủ động từ sớm, ngăn nguy cơ gián đoạn hoạt động bay; Sun PhuQuoc Airways khai trương ...)
và bốn bài đầu của `hang-hai.rss` (Chấn Nam ... nạo vét luồng hàng hải; Cận cảnh tàu hàng quốc tịch Panama mắc cạn ...; Muốn trở thành cảng xanh ...; Trang bị kỹ năng an toàn, giúp
ngư dân Cửa Lò ... — bài cuối LẠC chủ đề). Nguồn ghi `BaoXayDung`, vùng `domestic`, thể loại `aviation_logistics`.

## Đọc: `news_score` KHÔNG đổi vì nguồn mới — và đây là điều ĐÃ BIẾT trước khi đo

Chữ của leader cho người dùng đã nói thẳng: tin của nhóm ngành này chỉ hiện ở phần tin tức, không vào điểm (`news_sentiment_agent.py:138` chỉ lấy
`global_macro`, `securities_finance`, `banking`, `macro` vào `sector_key_score`; `master_agent.py:178-184`: `news_norm` chỉ để hiển thị, không vào
`pre_debate_score`). Gác: `tests/test_nguon_hang_khong_281.py::test_diem_tong_va_diem_agent_khong_doi_khi_nhom_hang_khong_co_bai` (tám bài TÍCH CỰC trong nhóm không
nhích `sentiment_score` hay `score`) và `::test_chi_bon_nhom_vao_diem_tong_va_khong_co_hang_khong` (AST). Điều ĐỔI: `total_articles` (+8) và nhóm hàng không (0 → 8 bài).

**Điểm nhích ở vòng 2 và 3 KHÔNG do nguồn mới** (Quy tắc 1: số đổi thì tìm nguyên nhân trước khi nói "không sao"). So từng BÀI giữa hai lượt (`khac_bai_281.py`, bỏ nhóm hàng không):

- vòng 1 cũ ↔ mới: 2 bài đổi (CNBC · hai chỗ), tất cả NEUTRAL; điểm bằng nhau ở mọi mã.
- vòng 2 cũ ↔ mới: nguồn ThanhNien (`domestic`) trả **0 bài ở lượt mới** thay vì 6 (vòng 2 mới: `domestic` 68 → 62, `total_articles` 194 chứ không phải 200). Một nguồn tải hỏng trong MỘT lượt; điểm nhích 0,1 vì sáu bài ThanhNien bị mất. Mã và danh sách nguồn của ThanhNien không đổi ở nhánh này.
- vòng 3 cũ ↔ mới: 2 bài Bloomberg đổi (một bài NEGATIVE đổi sang NEUTRAL) → `news_score` 51,1 → 50,8. Nhưng CHÍNH cây CŨ cũng đổi giữa vòng 1 và vòng 3: **cũ_1 ↔ cũ_3: 5 bài khác nhau (Bloomberg, CNBC, CoinDesk), `news_score` HVN 50,8 → 51,1**. Tức là **nhịp đổi tiêu đề của các nguồn quốc tế** (và độ sống của một nguồn) làm điểm nhích 0,1–0,4 giữa hai lượt cách nhau vài phút, trên cùng một mã nguồn.

Kết luận hẹp, đúng phạm vi: ở những cặp mà nội dung các nguồn KHÁC không đổi (vòng 1, cả bốn mã), điểm tin và `sentiment_score` **bằng nhau từng chữ số**; ở các cặp còn lại điểm khác nhau, và **nguyên nhân là nguồn khác trên hai lượt tải chứ không phải nhóm hàng không** (bảng so từng bài ở `khac_bai_281.out`). Chưa đo "điểm tin khi một bài hàng không mang nhãn mạnh" vì điểm không đọc nhóm này (đọc cả gác AST ở trên).

## Thời gian (lượt LẠNH = mã đầu của tiến trình)

**Hai kết quả KHÔNG khớp nhau; nói cả hai, chưa giải thích được.**

1. Ba vòng đầu của bảng trên (HVN, mã đầu của tiến trình, lượt lạnh): cũ 2,82 · 4,0 · 2,93 s → mới 5,28 · 6,58 · 5,7 s, tức **mới chậm hơn khoảng 2,5–2,8 s ở cả ba cặp** (các mã sau, đọc từ bộ nhớ chung, 0,5–1,2 s ở cả hai bên).
2. Đo lại SAU đó (cùng ngày, ~15:40–15:55 ICT; lệnh `do_thoi_gian_goi_281.py HVN`, ba cặp cũ/mới, và `do_goi_tin_281.py` thêm hai cặp, vòng 4–5): gói tin lạnh **cũ 2,90 · 3,07 · 2,88 s, mới 2,99 · 3,16 · 3,11 s** (chênh +0,1…+0,2 s); vòng 4–5 cũ 2,8 · 2,9, mới 2,9 · 2,9 (hết chênh). Trong lượt có bọc giờ từng nguồn, hai nguồn baoxaydung.vn tải 1,05–1,59 s TRONG bể nhưng KHÔNG phải nguồn chậm nhất (chậm nhất 2,1–2,8 s là venturebeat/bloomberg/cnbc/coindesk/oilprice). Cả nhóm ngành đo riêng: lạnh cũ 2,01 · 2,08 · 2,02 s, mới 2,09 · 2,04 · 1,95 s (`do_thoi_gian_281.py`); baoxaydung.vn riêng 0,33–0,46 s mỗi nguồn.

Điều chắc chắn (8 cặp cũ/mới lạnh, mã HVN): ở 5 cặp sau mới không chậm hơn cũ quá 0,2 s; ở 3 cặp đầu thì chậm 2,5–2,8 s. **Nguyên nhân của ba cặp đầu CHƯA RÕ** (ba cặp đầu không bọc giờ từng nguồn nên không biết nguồn nào chậm; vòng 2 còn có ThanhNien trả 0 bài, dấu hiệu mạng chập chờn lúc ấy). Cần nói với người dùng để họ biết: nếu nguồn mới chậm ở Cloud thì nó làm lượt mở đầu chậm hơn (bể phẳng đợi nguồn chậm nhất; hạn `HAN_MOT_NGUON` vẫn chặn), ngược chiều một phần tăng tốc của BƯỚC 280. Chưa đo trên Cloud, từ IP của Cloud hay Actions.

Dữ liệu: `thoi_gian_281.out`, `thoi_gian_goi_281.out`, `lap_lanh_281.out` ở `../vibe_logs_281/`.

## Dữ liệu thô

`../vibe_logs_281/goi_cu_{1,2,3}.json`, `goi_moi_{1,2,3}.json` (từng bài), `so_goi_tin_281.out`, `khac_bai_281.out`.
