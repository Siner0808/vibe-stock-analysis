# vibe-stock-analysis

[![kiem-dinh](https://github.com/Siner0808/vibe-stock-analysis/actions/workflows/kiem-dinh.yml/badge.svg?branch=main)](https://github.com/Siner0808/vibe-stock-analysis/actions/workflows/kiem-dinh.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/giao%20di%E1%BB%87n-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Chỉ giao dịch ảo](https://img.shields.io/badge/giao%20d%E1%BB%8Bch-ch%E1%BB%89%20%E1%BA%A2O-6e7781)

**Một agent tự giao dịch ẢO cổ phiếu Việt Nam, tự ghi bài học sau mỗi lệnh — và một bộ
dụng cụ đo được dựng để bắt chính nó nói dối.**

71 mã thuộc 16 ngành · giá ngày từ điểm cuối công khai (đến 10/11/2026: [vnstock](https://vnstocks.com)) · quét tự động trên GitHub
Actions · sổ lệnh ảo trên Google Sheets · giao diện Streamlit.

> [!WARNING]
> **Không phải khuyến nghị đầu tư, và không đặt lệnh thật.** Máy chuẩn bị → người xác
> nhận → **người** đặt lệnh; không có đường nào trong mã nối tới tài khoản chứng khoán.
> Tới nay hệ thống **chưa chứng minh được lợi thế nào** — xem [Kết quả](#kết-quả-đo-được).

---

## Một ngày của agent

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/hinh/mot-ngay-cua-agent-toi.svg">
  <img alt="Một lượt quét: kéo sổ từ Google Sheets, xét điều kiện dừng, quét 71 mã (khớp lệnh chờ ở giá mở cửa; đang giữ thì xét thoát; không giữ thì chấm điểm và qua 7 cổng thành lệnh chờ khớp ở phiên sau), điền nhật ký, đẩy sổ lên (quyết định và kế hoạch thêm dòng, lệnh và nhật ký soi gương); hậu kiểm bằng lời (B1) chạy ở workflow riêng và thêm dòng vào tab hau_kiem; app đọc sổ." src="docs/hinh/mot-ngay-cua-agent-sang.svg">
</picture>

Mỗi **lượt quét** chạy trên GitHub Actions trong ngày giao dịch, **sau đóng cửa** (từ BƯỚC 256, 05/11/2026,
người dùng duyệt): giờ **cron khai** là 15:35 và 17:05 giờ VN (nhịp chính và nhịp dự phòng), vì động cơ chỉ
ghi sổ trên nến ngày đã đóng (từ 15:30). GitHub vẫn gộp và trễ nhịp (4–10 giờ). Lịch cũ khai 12 nhịp trong
phiên; **giờ đo thật của lịch cũ** (05/11/2026, 40 lượt `quet-so-lenh` theo lịch gần nhất, 08/10–04/11): 0
lượt được tạo trước 13:53 giờ VN, 10 lượt tạo 13:53–14:59, 30 lượt tạo từ 15:00 — nên ca sáng không chạy
trong mẫu ấy và phần lớn lượt quét đã là lượt sau đóng cửa. Lệnh: `gh run list --workflow quet-so-lenh.yml --limit 40 --event schedule --json createdAt`,
đổi giờ UTC sang giờ VN. Lệnh mới **không bao giờ** khớp ở giá của phiên ra tín hiệu — nó chờ giá mở
cửa phiên sau. Mỗi ngày làm việc có bốn chuông canh; **giờ cron** của chúng: không có lượt quét nào
thành công (16:23), điều kiện dừng đã đạt mà cổng vẫn mở (16:43), lệnh đóng quá một phiên chưa có
bài học (16:53), có phiên mà không có nến mới (17:17). **Giờ đo thật** (cùng ngày đo, 40 lượt mỗi
chuông; `chuong-bai-hoc` mới có 19): bốn chuông trễ trung vị 6,1–6,5 giờ so với giờ cron, nhỏ nhất
4,1, lớn nhất 10,2 giờ. Ngoài vòng quét, một workflow riêng (cron 18:17 giờ VN) viết hậu kiểm bằng
lời cho lệnh đã đóng và thêm vào tab `hau_kiem` (B1); sau mỗi lượt quét thành công, một workflow nữa gửi bản tin
cuối ngày tới Telegram của người dùng, tối đa một lần mỗi ngày phiên (T3, BƯỚC 258). App chỉ ĐỌC sổ; ngoài vòng này nó còn các
lớp **chỉ để xem** — phân tích cơ bản, pha Wyckoff, mức Fibonacci, bảng giá năm màu (ba màu ở CI/Cloud từ BƯỚC 267), kế hoạch vào
lệnh từng mã, cấu trúc giá theo Lý thuyết Dow, nến tuần/tháng.

## Kết quả đo được

Đặt lên đầu, không giấu xuống cuối:

| Câu hỏi | Kết quả | Nguồn |
|---|---|---|
| Điểm tổng hợp có dự báo lợi nhuận 20 phiên sau? | rho **−0,019**, KTC 95% [−0,100 ; +0,064] — **không** | 573 phiên / 10 mã, [`MO-XE-KIEN-TRUC.md`](MO-XE-KIEN-TRUC.md) |
| Walk-forward ngoài mẫu, chi phí thực thi thật, danh mục theo ngày | 650 lệnh · alpha **−1,73%/lệnh**, KTC [−2,28 ; −1,17] — **thua rổ chuẩn** | ĐO 28 + 29, 20–21/10/2026 (máy đo hiện hành) · bảng đầy đủ ở [`CLAUDE.md`](CLAUDE.md) |
| Kế hoạch vào lệnh (vùng chờ, cắt lỗ theo cấu trúc) có hơn mua mọi tín hiệu? | Δ alpha **+0,21** điểm %, KTC [−0,16 ; +0,57] — **chưa phân biệt được** | ĐO 25, 12/10/2026 · [`docs/STATE.md`](docs/STATE.md) BƯỚC 179 |

Nguyên nhân gốc không nằm ở mã: cả sáu agent tính từ **cùng một chuỗi giá**. *Phần đo được
thì không có tín hiệu; phần có thể có tín hiệu thì chưa đo được.*

## Vì sao repo này đáng đọc

Dự án đã **năm lần** cho ra con số rất đẹp rồi hoá ra vô nghĩa — `+22,42%`, `+14,88%`,
`+14,24%`, `+636,11%` (đòn bẩy ẩn 2,2 lần), và lần thứ năm là chính giao diện vẫn khoe
`+636,11%` nhiều ngày sau khi con số ấy đã bị bác. Không lần nào cố ý. Từ đó có:

> **Quy tắc số 1 — nếu một thay đổi làm con số đẹp lên đáng kể, giả định đầu tiên là CÓ LỖI.**

Phần lớn công sức vì thế nằm ở hàng rào chống tự lừa mình:

- 🧾 **Khai trước, đo sau.** Tiêu chí của phép đo được ký và commit **riêng**, trước khi chạy
  và trước khi thấy số ([`docs/TIEU-CHI-DOC-TRUOC.md`](docs/TIEU-CHI-DOC-TRUOC.md)) — lịch sử git
  chứng minh thứ tự, không ai phải tin lời hứa.
- 🧬 **Đột biến mọi hàng rào mới.** Sửa mã cho sai đi, test phải ĐỎ; một gác vừa viết xong mà
  chưa bị đục thử được coi là chưa có.
- 🚦 **Ba trạng thái, không hai.** Mọi phép kiểm phân biệt *đạt* / *không đạt* / **chưa kiểm
  được** — và trạng thái thứ ba không bao giờ được gộp vào trạng thái đầu.
- 📓 **Nhật ký ghi cả cái sai.** [`docs/STATE.md`](docs/STATE.md) giữ từng bước: đo được gì, giả
  thuyết nào bị bác, ước lượng nào đã trượt; bảng lỗi quy trình ghi từng lỗi và "máy chặn được
  chưa".

## Lộ trình

Hai đích, nhịp khác nhau ([`docs/LO-TRINH.md`](docs/LO-TRINH.md), người dùng duyệt 08/10/2026):

- **Đích 1 — "máy học được"**, v1.0 ngày **28/02/2027**: agent tự giao dịch ảo, tự rút bài
  học, minh bạch; nghiệm thu bằng bảy tiêu chí đo được.
- **Đích 2 — "có lợi thế thật"**: ứng viên đầu tiên (UV-001) đã khai công khai từ 02/10/2026 và
  chỉ được đọc **một lần**, khoảng đầu tháng 11/2027 (ƯỚC LƯỢNG). Kết cục "không có lợi thế" là
  một kết quả hợp lệ.

## Chạy thử

Cần Python 3.11. Sau khi clone, tạo một môi trường ảo tên `.venv` trong thư mục repo, rồi
(đường dưới là của Windows; Linux/macOS dùng `.venv/bin/python`):

```bash
git clone https://github.com/Siner0808/vibe-stock-analysis.git
cd vibe-stock-analysis
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m streamlit run app.py
./.venv/Scripts/python.exe -m pytest tests/ -q
```

Lệnh cuối chạy toàn bộ test — offline, không cần mạng hay khoá. Kho ngoài (Google Sheets) là tuỳ chọn: chép `.streamlit/secrets.toml.example` thành
`.streamlit/secrets.toml` rồi điền; không cấu hình thì phần ấy tắt sạch, app vẫn chạy.
**Đừng commit file `secrets.toml`.**

## Tài liệu

| Bắt đầu từ | Để biết |
|---|---|
| [`docs/HANDOFF.md`](docs/HANDOFF.md) | hệ thống đang ở đâu, lệnh đầu tiên nên chạy |
| [`docs/LO-TRINH.md`](docs/LO-TRINH.md) | đi tới đâu, theo mốc nào |
| [`NGUYEN-TAC-DO-LUONG.md`](NGUYEN-TAC-DO-LUONG.md) | tám bất biến đo lường — đọc trước khi sửa bất cứ thứ gì chạm kết quả |
| [`MO-XE-KIEN-TRUC.md`](MO-XE-KIEN-TRUC.md) | thành phần nào chạy thật, thành phần nào là trang trí (phần "số nấc" đã hết đúng từ 31/08/2026, kết luận thì còn) |
| [`docs/hinh/mot-ngay-cua-agent-sang.svg`](docs/hinh/mot-ngay-cua-agent-sang.svg) | luồng chạy hằng ngày, sinh từ mã bởi `tools/ve_so_do_mot_ngay.py` |
| [`architecture_asbuilt.html`](architecture_asbuilt.html) | **bản chụp 13/08/2026**, không phải luồng đang chạy: phần "số nấc" và nút `paper_trades.db` đã hết đúng |
| [`docs/STATE.md`](docs/STATE.md) | nhật ký từng bước |
| [`CLAUDE.md`](CLAUDE.md) · [`.claude/skills/quy-trinh-lam-viec/`](.claude/skills/quy-trinh-lam-viec/SKILL.md) | luật hiện hành và quy trình bắt buộc cho người lẫn agent AI |

## Giấy phép

Chưa có. Mặc định là **giữ toàn quyền** — muốn dùng lại, hãy mở issue hỏi trước. Dữ liệu thị
trường thuộc nhà cung cấp tương ứng; tài liệu kỹ thuật của gói vnstock **không** được lưu trong
repo này, đúng giấy phép của nó.
