# Đột biến BƯỚC 281 (16/11/2026)

Lệnh: `cd ../vibe_wt_281 && ../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_281/dot_281.py` (nhật ký thô `../vibe_logs_281/dot_281.log`).
Mọi đột biến đi qua `tools/va_an_toan.dot_bien_bo` (hoàn tra từng byte, kiểm không để rác); lệnh chạy là `pytest` MỘT file test với `-x`.

## Gác mới `tests/test_nguon_hang_khong_281.py` — 11/11 đỏ

| phát | sửa gì | kết quả |
|---|---|---|
| M0 | dựng lại LỖI THẬT: nhóm `aviation_logistics` lại rỗng (hai nguồn bị xoá) | ĐỎ |
| M1 | `hang-khong.rss` → `hang-khong.xml` | ĐỎ |
| M2 | `hang-hai`: vùng `domestic` → `international` | ĐỎ |
| M3 | nhãn `BaoXayDung` → `BaoXayDungX` (một nguồn) | ĐỎ |
| M4 | bỏ nguồn thứ hai (`hang-hai`) | ĐỎ |
| M5 | thêm nguồn thứ ba (`duong-sat.rss`) | ĐỎ |
| M6 | khai lặp `hang-khong.rss` ở nhóm `securities_finance` | ĐỎ |
| M7 | đổi thứ tự hai nguồn | ĐỎ |
| M8 | `max_items` 4 → 6 ở `SectorNewsAgent.collect` | ĐỎ |
| M9 | thể loại bài ghi `"corporate"` thay vì tên nhóm | ĐỎ |
| M10 | `total_articles` bỏ phần tổng các nhóm ngành | ĐỎ |

## Gác cũ đã cập nhật `tests/test_sua_nguon_tin_279.py` — 7/7 đỏ (chọn lọc M0 M1 M2 M4 M5 M6 M7)

Nhật ký in `SONG  M10` ở khối này và dòng "7/8 do": **đó là lỗi LỌC của script, không phải một đột biến sống sót.** Bộ lọc `p[0][:2] in (...)` khớp
tiền tố `M1` nên kéo cả `M10` vào; `M10` (`total_articles`) không thuộc nhiệm vụ của file 279, và file mới đã bắt nó (khối trên, đỏ). Bảy đột biến
CÓ chủ ý chạy trên file 279 đều đỏ.

## `news_sentiment_agent.py` — 1/1 đỏ

S1: thêm `"aviation_logistics"` vào danh sách bốn nhóm của `sector_key_score` → ĐỎ (hai gác: AST danh sách và hành vi cùng điểm).

## `run_daily.py` — 1/1 đỏ

R1: `run_daily.py` nhập `news_collectors` → ĐỎ (`test_duong_quet_khong_nhap_news_collectors`).

Phát đầu của khối mới (M0) là lỗi thật đã xảy ra ở BƯỚC 279 (nhóm hết nguồn, 0 bài); các phát M8/M10 canh đúng chỗ BƯỚC này dựa vào (4 bài/nguồn; tổng gói tin).
**Điều chưa thử:** đột biến thêm một nguồn vào nhóm KHÁC có cùng tên miền (M6 chỉ thử `securities_finance`); gác theo tên miền (`test_khong_dia_chi_baoxaydung_nao_khac_o_bat_ky_nhom_nao`) phủ chung.
