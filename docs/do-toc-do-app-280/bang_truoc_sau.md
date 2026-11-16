# Bảng trước/sau của app (AppTest, 3 lần, trung vị)

Lệnh: `bash ../vibe_logs_280/chay_do_280.sh` rồi `../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_280/aggregate_280.py`. "Trước" = cây `main` `485e8ed`; "sau" = nhánh `sua/tang-toc-dot-2-280`. Xen kẽ trước, sau, trước, sau, trước, sau; mỗi lượt là MỘT tiến trình mới (bộ nhớ trong tiến trình rỗng, không `vnstock`), nghỉ 25 giây giữa các lượt.

```
so lan chay: {'truoc': 3, 'sau': 3}
| kich ban | truoc (trung vi, cac lan) | sau (trung vi, cac lan) | doi |
|---|---|---|---|
| S1 mo lan dau (lanh) | 15.74 s (14.91, 15.74, 15.99) | 10.95 s (13.00, 10.95, 10.48) | -4.78 s |
| S2 chay lai (am) | 0.51 s (0.51, 0.60, 0.51) | 0.54 s (0.64, 0.54, 0.53) | +0.03 s |
| S3 doi ma ACB->FPT | 4.03 s (4.18, 3.82, 4.03) | 3.41 s (3.32, 3.41, 3.42) | -0.62 s |
| S4 chay lai sau doi ma | 0.54 s (0.57, 0.46, 0.54) | 0.54 s (0.54, 0.54, 0.62) | +0.01 s |
| S5 radio khung D->W | 0.48 s (0.51, 0.48, 0.47) | 0.49 s (0.47, 0.49, 0.55) | +0.01 s |
| S6 selectbox trong tab | 0.51 s (0.51, 0.43, 0.52) | 0.51 s (0.49, 0.51, 0.61) | +0.00 s |
ngoai le trong cac lan chay: {'truoc': [], 'sau': []}
### S1_cold_first_load: trung vi theo muc (giay) va so lan goi mang
| muc | truoc s | sau s | HTTP truoc | HTTP sau |
|---|---|---|---|---|
| D Sheets read (_doc_so_ban_tin + so_lenh) | 4.56 | 2.33 | 9 | 4 |
| I run_full_analysis block (if triggered) | 4.51 | 2.74 | 42 | 40 |
| S col_chart (3-timeframe chart) | 2.56 | 2.36 | 3 | 3 |
| P cau_truc (2nd load_stock_data) | 0.70 | 0.06 | 1 | 0 |
| A imports (master_agent, collectors, ...) | 0.47 | 0.52 | 0 | 0 |
| tab Lich su giao dich | 0.49 | 0.50 | 0 | 0 |
| tab Tai khoan Gia lap | 0.46 | 0.47 | 0 | 0 |
| F VN-Index topbar fetch | 0.36 | 0.39 | 1 | 1 |
| L load_stock_data (prices) | 0.30 | 0.39 | 1 | 1 |
tong so lan goi HTTP (trung vi): truoc 57, sau 49
### S3_change_symbol_ACB_to_FPT: trung vi theo muc (giay) va so lan goi mang
| muc | truoc s | sau s | HTTP truoc | HTTP sau |
|---|---|---|---|---|
| S col_chart (3-timeframe chart) | 1.81 | 1.75 | 2 | 2 |
| P cau_truc (2nd load_stock_data) | 0.71 | 0.06 | 1 | 0 |
| I run_full_analysis block (if triggered) | 0.67 | 0.68 | 5 | 5 |
| L load_stock_data (prices) | 0.36 | 0.48 | 1 | 1 |
| tab Lich su giao dich | 0.09 | 0.23 | 0 | 0 |
| D Sheets read (_doc_so_ban_tin + so_lenh) | 0.04 | 0.04 | 0 | 0 |
| tab Ban tin | 0.03 | 0.04 | 0 | 0 |
| tab Vi the | 0.01 | 0.00 | 0 | 0 |
| tab Kiem dinh chien luoc | 0.01 | 0.00 | 0 | 0 |
tong so lan goi HTTP (trung vi): truoc 9, sau 8
```
