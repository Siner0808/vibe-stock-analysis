# Đo thiết kế TRƯỚC khi cài (pha 1 của BƯỚC 288, 20/11/2026 11:35–12:40 ICT, một IP nhà, trong phiên giao dịch)

Mọi lệnh chạy từ `vibe_wt_288` với `../vibe_preview/.venv/Scripts/python.exe -X utf8 <script>` (script ở `../vibe_logs_288/`, ngoài repo như
các BƯỚC đo trước; JSON thô 3 nguồn × 71 mã + VNINDEX ở `../vibe_logs_288/raw/`). Không gọi `intraday_data.tai`, không đụng `vnstock_auth`, không ghi Sheets.

## 1. Thời gian: mức tiết kiệm THẬT, và đính chính con số "~2,4 s" của BƯỚC 280

STATE BƯỚC 280 mục I viết *"còn ~2,4 s lúc mở lần đầu"*. Đo lại bằng AppTest (`chay_app_288.sh` → `aggregate_288.py`): 2,4–2,5 s là TỔNG
mục `S col_chart` (3 lượt mạng: Entrade 1.583 ngày bị loại 0,43 s · VNDirect cổ phiếu 0,51 s · VNDirect VN-INDEX 0,54 s, cộng ≈ 1 s CPU), KHÔNG phải mức
tiết kiệm: gộp xong vẫn còn một lượt tải cổ phiếu và lượt VN-INDEX.

Đo từng thiết kế (`do_thoi_gian.py`; 7 mã ACB FPT HPG SHS ACV VNM MWG × 3 vòng, thứ tự thiết kế xoay vòng, MỘT tiến trình, bộ nhớ rỗng; mỗi lượt là
`VNStockCollectorAgent().collect` THẬT, đủ kiểm định). Đường dữ liệu "mở lần đầu": L (1.095 ngày) + cổ phiếu 1.583 ngày + VNINDEX 1.583 ngày.

| thiết kế | trung vị tổng (21 lượt) | lượt mạng | giây mạng | tiết kiệm |
|---|---|---|---|---|
| hiện tại (main) | 2,81 s | 4 | 1,88 | — |
| A: bỏ lượt thử Entrade cho cửa sổ dài | 2,12 s | 3 | 1,49 | −0,69 s |
| B: một lượt VNDirect, cắt | 1,44 s | 2 | 1,10 | −1,37 s |
| **C: một lượt Entrade khử trùng, cắt (ĐÃ CÀI)** | **1,33 s** | 2 | 0,99 | **−1,48 s** |

## 2. Lỗi "hai nến một ngày" của Entrade (`an_loi_entrade.py`, `an_loi_entrade2.py`, `an_gio.py`, `an_gio2.py`, `an_khu_trung.py`)

Đầu ra: `loi_entrade_70_cap_out.txt` (cạnh file này), `khu_trung_ba_cap_sai_out.txt`.
- 67/71 mã có ngày trùng trong cửa sổ 1.583 ngày (xin từ 13/01/2022); **0/71** trong cửa sổ quét (1.095 ngày, từ 04/07/2023, 785 nến). Không dính: BAF, GEL, VCK, VPL.
- Chỉ **ba ngày**: 27/12/2022 (67 mã), 07/04/2023 (DHG, MSR), 10/04/2023 (AAA) = **70 cặp** (mã, ngày). Hai nến khác nhau ở mốc giờ (00:00 / 02:00 UTC) và ở cả năm cột (open 60 cặp, high 63, low 64, close 66, volume 70; không cặp nào giống hệt).
- Phép khử "giữ nến khối lượng lớn hơn": đúng ở 67 cặp 27/12/2022 (khớp VNDirect, khối lượng lệch ≤ 0,1%; |Δclose| trung vị 0,003 nghìn đồng; nến bị bỏ lệch khối lượng trung vị 65%);
  **SAI ở ba cặp tháng 04/2023** — AAA 10/04/2023 (khối lượng nến giữ lệch VNDirect 11%), DHG 07/04/2023 (52%), MSR 07/04/2023 (73%): không nến nào khớp VNDirect, hai mảnh dở.

## 3. Làm tròn giữa ba nguồn (`an_lam_tron.py`; `an_lam_tron.log`, `an_lam_tron_tol.log` ở `../vibe_logs_288/`), cửa sổ quét, 58.183 hàng chung Entrade ∩ VNDirect

| so sánh | hàng khác ≥ 1 cột, chính xác | dung sai giá 0,0051 / KL 1% | dung sai giá 0,0101 / KL 5% |
|---|---|---|---|
| Entrade vs VNDirect (71 mã) | 80,95% | 40,12% | 12,14% |
| Entrade vs VPS | 86,90% | 37,89% | 7,50% |
| VNDirect vs VPS | 87,32% | 7,85% | 5,31% |
| HNX (HUT MBS PVS SHS) Entrade vs VNDirect | 100% | 66,68% | 62,00% |
| UPCoM (ACV MSR OIL) | 100% | 72,75% | 50,99% |
| HOSE (64 mã) | 78,80% | 36,83% | 7,04% |
| VN-INDEX VNDirect vs VPS | 100% | 77,63% | 71,60% (close giống hệt; open/high/low khác 8–14%) |

Entrade làm tròn 2 chữ số thập phân, VNDirect 3 — phần lớn "khác chính xác" chỉ là làm tròn; sau khi nới một tick vẫn còn 7–12% hàng khác ở HOSE và 50–67% ở HNX/UPCoM (hai hệ số điều chỉnh khác nhau).

## 4. Bất biến của `run_daily` (`do_bat_bien.py`, 71 mã)

R0 = `VNStockCollectorAgent().collect(mã, hôm nay − 1.095, hôm nay)` THẬT: 785 nến, 71/71 mã do Entrade phục vụ. Các thiết kế dựng lại OFFLINE bằng chính `collect`, thay
`ngk._http_json` bằng bộ phát lại JSON thô LỌC theo `from`/`to` (bỏ nến NGÀY HÔM NAY, còn dở).

| thiết kế | nến Dow (785) so R0, từng byte | nến biểu đồ 180 |
|---|---|---|
| A | không đụng đường `collect` mặc định (nến tuần/tháng đổi ở 4 mã niêm yết muộn) | — |
| B (một lượt VNDirect) | **0/71** giống; 80% hàng khác; max |Δ| open 2,98 · high 1,33 · low 3,96 · close 1,77 nghìn đồng; 68/71 mã lệch cửa sổ 1 ngày (VNDirect đã có nến dở hôm nay, Entrade chưa) | 0/71 giống |
| **C** | **71/71 giống từng byte, 0/54.187 hàng khác** | 71/71 giống |

Nến tuần/tháng trên app, C so với hiện tại (VNDirect), 71 mã: tuần 16.009 nến, **4.147 (25,9%)** lệch `close` > 0,0051, max |Δ| 1,30; tháng 3.641 nến, **940 (25,8%)**, max 1,07;
không mã nào lệch SỐ nến; khối lượng lệch > 1%: 745 nến tuần, 245 nến tháng.

**Bài học thao tác (đã khai ở STATE BƯỚC 288):** lượt đầu của bộ phát lại trả nguyên JSON 1.583 ngày cho mọi cửa sổ nên kiểm "trùng ngày" của `dung_khung` (chạy TRƯỚC khi cắt vào cửa sổ) nổ ở cả cửa sổ 1.095 ngày
— máy đo tự tạo ra kết luận "Entrade hỏng ở 67/71 mã". Sửa bằng cách lọc theo `from`/`to` như máy chủ rồi kiểm 71/71 bằng chính R0 thật.
