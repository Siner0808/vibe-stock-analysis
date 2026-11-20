# Lượt mạng THẬT: nến app (một lượt 1.583 ngày, Entrade khử trùng, cắt) so với nến `run_daily` chấm, 71 mã

Yêu cầu của leader (golden phải có một lượt mạng thật, không chỉ phát lại; BƯỚC 280 mục H dặn đúng điều này).

Lệnh (20/11/2026, cây làm việc `tang-toc/gop-cua-so-288`, chạy từ gốc repo; CHỈ ĐỌC, tuần tự, nghỉ 0,4 s giữa các mã, 0 lần chạm sổ/Sheets/`run_daily`):

    ./.venv/Scripts/python.exe -X utf8 tools/doi_chieu_gop_cua_so_288.py

Với mỗi mã công cụ gọi `VNStockCollectorAgent().collect` mặc định cho cửa sổ 1.095 ngày (đúng thứ `run_daily` chấm) và 180 ngày, rồi
`gia_mot_lan.tai_mot_lan` với lượt tải rộng 1.583 ngày đi chuỗi `chuoi_cho_app` (bản sao hai hàm tải của `app.py`), và so TỪNG BYTE (`DataFrame.equals` + dtype từng cột),
bỏ nến của ngày `den` (nến đang giao dịch đổi theo giờ).

Kết quả (đầu ra nguyên văn: `mang_that_71_ma_out.txt`): **71 giống · 0 lệch · 0 chưa kiểm được / 71**. Mọi mã: nến quét 785 (BAF có 785; GEL 194 vì niêm yết muộn) giống từng byte, hàng lệch 0;
nến biểu đồ 131 giống từng byte; nguồn cửa sổ rộng = `entrade` ở cả 71 mã (nghĩa là phép khử trùng chạy và Entrade qua kiểm).

Cùng hàm `doi_chieu_mot_ma` chạy ngoại tuyến trong CI trên JSON thô đã chụp (`tests/du_lieu/entrade_khu_trung_288.json.gz`: ACB, DHG, AAA, SHS; `tests/test_gop_cua_so_288.py`).
Chạy lại lượt mạng thật bất cứ lúc nào bằng lệnh trên (mã thoát 0 giống hết · 1 có mã lệch · 2 chưa kiểm được).

**Giới hạn:** một IP nhà, một buổi trưa; nến ngày hôm nay bị bỏ khỏi phép so sánh. Hành vi nguồn từ IP Cloud/Actions chưa đo.
