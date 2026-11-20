# Bảng trước/sau của app, BƯỚC 288 (AppTest, 3 lần, trung vị)

Lệnh (20/11/2026 12:33–12:38 ICT, một IP nhà, trong phiên giao dịch; đọc Sheets CHỈ ĐỌC, không ghi gì):
`bash ../vibe_logs_288/chay_app_288_sau.sh` rồi `../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_288/aggregate_288_ts.py`.
"Trước" = cây `main` `9bd6831`; "sau" = nhánh `tang-toc/gop-cua-so-288` (cây làm việc có phương án C). Xen kẽ trước, sau,
trước, sau, trước, sau; mỗi lượt là MỘT tiến trình mới (bộ nhớ rỗng, không `vnstock`), nghỉ 25 giây giữa các lượt. Cách đo của
BƯỚC 280 (`docs/do-toc-do-app-280/bang_truoc_sau.md`): `make_app_288.py` dựng bản sao `app.py` có mốc giờ, `do_app_288.py` chạy
`streamlit.testing.v1.AppTest` và bọc từng lượt `requests` (số lượt và giây mạng theo từng mục).

```
so lan chay: {'truoc': 3, 'sau': 3}

| kich ban | truoc (trung vi, cac lan) | sau (trung vi, cac lan) | doi |
|---|---|---|---|
| S1 mo lan dau (lanh) | 11.60 s (13.51, 11.30, 11.60) | 9.53 s (9.53, 9.53, 9.60) | -2.07 s |
| S2 chay lai (am) | 0.55 s (0.55, 0.61, 0.53) | 0.54 s (0.54, 0.59, 0.52) | -0.02 s |
| S3 doi ma ACB->FPT | 3.55 s (3.55, 3.40, 3.59) | 1.95 s (2.01, 1.95, 1.86) | -1.60 s |
| S4 chay lai sau doi ma | 0.52 s (0.52, 0.65, 0.51) | 0.58 s (0.60, 0.52, 0.58) | +0.06 s |
| S5 radio khung D->W | 0.50 s (0.49, 0.59, 0.50) | 0.58 s (0.58, 0.47, 0.58) | +0.08 s |
| S6 selectbox trong tab | 0.52 s (0.52, 0.54, 0.45) | 0.58 s (0.58, 0.45, 0.58) | +0.06 s |

ngoai le trong cac lan chay: {'truoc': [], 'sau': []}

### S1_cold_first_load: trung vi theo muc (giay) va so lan goi mang
| muc | truoc s | sau s | HTTP truoc | HTTP sau |
|---|---|---|---|---|
| I run_full_analysis block (if triggered) | 3.06 | 3.04 | 42 | 42 |
| D Sheets read (_doc_so_ban_tin + so_lenh) | 2.57 | 2.29 | 4 | 4 |
| S col_chart (3-timeframe chart) | 2.51 | 1.00 | 3 | 1 |
| tab Lich su giao dich | 0.58 | 0.52 | 0 | 0 |
| A imports (master_agent, collectors, ...) | 0.53 | 0.53 | 0 | 0 |
| tab Tai khoan Gia lap | 0.53 | 0.53 | 0 | 0 |
| L load_stock_data (prices) | 0.46 | 0.44 | 1 | 1 |
| F VN-Index topbar fetch | 0.44 | 0.36 | 1 | 1 |
| B page_config + CSS | 0.24 | 0.23 | 0 | 0 |
tong so lan goi HTTP (trung vi): truoc 51, sau 49

### S3_change_symbol_ACB_to_FPT: trung vi theo muc (giay) va so lan goi mang
| muc | truoc s | sau s | HTTP truoc | HTTP sau |
|---|---|---|---|---|
| S col_chart (3-timeframe chart) | 1.78 | 0.33 | 2 | 0 |
| I run_full_analysis block (if triggered) | 0.96 | 0.71 | 5 | 5 |
| L load_stock_data (prices) | 0.48 | 0.46 | 1 | 1 |
| tab Lich su giao dich | 0.10 | 0.10 | 0 | 0 |
| P cau_truc (2nd load_stock_data) | 0.06 | 0.05 | 0 | 0 |
| tab Ban tin | 0.03 | 0.03 | 0 | 0 |
| D Sheets read (_doc_so_ban_tin + so_lenh) | 0.03 | 0.03 | 0 | 0 |
| tab Kiem dinh chien luoc | 0.01 | 0.01 | 0 | 0 |
| tab Vi the | 0.00 | 0.00 | 0 | 0 |
tong so lan goi HTTP (trung vi): truoc 8, sau 6

### tung lan goi mang cua muc S col_chart / L / F / P (lan chay 1), S1
truoc
   [F VN-Index topbar fetc]  0.394s dchart-api.vndirect.com.vn/dchart/history?symbol=VNINDEX
   [L load_stock_data (pri]  0.413s services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol=ACB
   [S col_chart (3-timefra]  0.459s services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol=ACB
   [S col_chart (3-timefra]  0.573s dchart-api.vndirect.com.vn/dchart/history?symbol=ACB
   [S col_chart (3-timefra]  0.603s dchart-api.vndirect.com.vn/dchart/history?symbol=VNINDEX
sau
   [F VN-Index topbar fetc]  0.304s dchart-api.vndirect.com.vn/dchart/history?symbol=VNINDEX
   [L load_stock_data (pri]  0.391s services.entrade.com.vn/chart-api/v2/ohlcs/stock?symbol=ACB
   [S col_chart (3-timefra]  0.580s dchart-api.vndirect.com.vn/dchart/history?symbol=VNINDEX
```

Đọc đúng: mục `S col_chart` (biểu đồ 3 khung) từ **2,51 s → 1,00 s** lúc mở lần đầu (3 lượt mạng → 1: chỉ còn VN-INDEX 1.583 ngày)
và **1,78 s → 0,33 s** lúc đổi mã (2 lượt → 0). Wall S1 −2,07 s, S3 −1,60 s. Các mục khác (Sheets, `run_full_analysis`) lệch trong
nhiễu giữa các lượt (S1 "trước" dao động 11,30–13,51 s). Con số thiết kế đo riêng ở `docs/do-toc-do-app-288/thiet_ke_truoc_khi_cai.md`
(2,81 s → 1,33 s, −1,48 s trên đường dữ liệu, 7 mã × 3 vòng) là cận THẬN TRỌNG hơn; AppTest cho nhiều hơn vì còn bớt hai lần
`normalize/validate` và hai lần dựng khung ở phía CPU. Lượt mạng của biểu đồ ngày ở S1 "sau" vẫn là một (Entrade 1.583 ngày, ghi ở mục `L`).

**Giới hạn (nói thẳng):** một IP nhà, một buổi trưa trong phiên giao dịch; AppTest KHÔNG dựng DOM, JSON Plotly, websocket; Cloud chưa
đo (như BƯỚC 280 mục H). Ba lượt mỗi nhánh, khoảng giữa các lượt rộng (S1 trước 11,30–13,51 s), nên chênh dưới ~0,3 s không đọc được.
Các dòng S4–S6 "sau" cao hơn "trước" 0,06–0,08 s: trong nhiễu của lượt chạy lại ấm (không lượt mạng nào ở các kịch bản ấy).
