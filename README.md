# vibe-stock-analysis

Hệ thống phân tích và **paper trading** cổ phiếu Việt Nam — 71 mã thuộc 16
ngành, dữ liệu từ [vnstock](https://vnstocks.com), giao diện Streamlit.

Nhưng thứ đáng đọc trong repo này không phải hệ thống giao dịch. Nó là
**nhật ký của một dự án cố gắng tự chứng minh mình sai**, và phần lớn thời
gian là thành công.

> ### ⚠️ Đọc trước khi dùng
> - **Không phải khuyến nghị đầu tư.** Không có gì ở đây nên dùng để ra
>   quyết định mua bán.
> - **Không đặt lệnh thật.** Máy chuẩn bị → người xác nhận → **người** đặt
>   lệnh. Không có đường nào trong mã nguồn nối tới tài khoản chứng khoán.
> - **Hệ thống này chưa chứng minh được lợi thế nào.** Xem ngay mục dưới.

---

## Kết quả đo được — đặt lên đầu, không giấu xuống cuối

**Kết quả có ý nghĩa thống kê đầu tiên của dự án là một kết quả ÂM.**

Walk-forward ngoài mẫu, bật chi phí thực thi thật (bước giá 50đ, lô chẵn,
biên độ ±7%, khớp một phần):

| | số lệnh | kỳ vọng/lệnh | alpha khớp từng lệnh | KTC 95% |
|---|---|---|---|---|
| tắt chi phí | 390 | +0,614% | −0,011% | [−0,766 ; +0,832] **chứa 0** |
| **bật chi phí** | 385 | **−0,291%** | **−0,927%** | **[−1,689 ; −0,076] LOẠI 0** |

Cách đọc: rổ đối chiếu mua một lần rồi giữ, trả chi phí **hai** lần. Chiến
lược quay vòng 385 lệnh, trả **770** lần. Lợi thế vốn đã không phân biệt
được với 0; cộng chi phí quay vòng vào thì phần âm lộ ra.

Và điểm số — thứ toàn bộ kiến trúc sinh ra để tính — **không dự báo được
lợi nhuận**:

```
tương quan hạng giữa điểm tại phiên T và lợi nhuận 20 phiên sau:
    rho = −0,019      KTC 95% [−0,100 ; +0,064]
```

Không thành phần nào trong sáu agent có tương quan khác 0 một cách có ý
nghĩa. Cách gộp tuyến tính **tối ưu trong mẫu** của năm điểm agent — tức
cận trên tuyệt đối, không cách gộp nào tốt hơn tồn tại — cho rho 0,0115 ở
nhịp 5 phiên, dưới sàn nhiễu 0,0446.

### Năm lần con số đẹp hoá ra vô nghĩa

`+22,42%` · `+14,88%` · `+14,24%` · `+636,11%` — và lần thứ năm là chính
giao diện công bố `+636,11%` suốt nhiều ngày sau khi con số ấy đã bị bác.

Không lần nào có ai cố ý. Mỗi lần đều là một lỗi kỹ thuật nhỏ, âm thầm, và
**luôn nghiêng về phía làm kết quả đẹp lên**. Con số +636,11% tái lập được
chính xác — nó không bịa; nó chỉ dùng đòn bẩy 2,2 lần mà không ai để ý.

Từ đó có **quy tắc số 1** của repo này:

> Nếu một thay đổi làm con số đẹp lên đáng kể, giả định đầu tiên phải là
> **có lỗi**.

---

## Thứ khiến repo này khác thường

Phần lớn công sức không nằm ở chiến lược, mà ở **dụng cụ đo và hàng rào
chống tự lừa mình**.

**Khai trước, tách commit.** Thiết kế phép kiểm được commit **một mình**,
kết quả nằm ở commit sau — nên lịch sử git chứng minh được thứ tự, không ai
phải tin lời hứa. Lần đầu áp dụng, nó lập tức có tác dụng: ô duy nhất cho
ra "ĐẠT" trong phép kiểm đảo chiều đúng là ô đã khai trước là **không đọc
được**. Không có bản khai, dòng tiêu đề đã là *"tìm thấy đảo chiều, rho
−0,035, trên rào hoà vốn"*.

**Đột biến mọi hàng rào mới.** Một gác vừa viết xong, vừa xanh, thường là
một gác vô dụng — đã xảy ra ba lần trong một ngày. Nên mỗi gác mới đều bị
đục thử: sửa mã cho sai đi, test phải ĐỎ. Hôm gần nhất: 24/24 đỏ.

**Gác đọc AST, không đọc `in`.** `"tên_hàm" in src` khớp cả chữ trong khối
chú thích — càng viết chú thích trung thực thì gác kiểu ấy càng dễ vô hiệu.
Và gác một phép **suy ra** thì phải kiểm *hình dạng* biểu thức, không kiểm
*giá trị* nó cho ra: giá trị trùng nhau tại một điểm là chuyện thường, cấu
trúc sai thì sai ở mọi điểm khác.

**Dụng cụ phải tự khai khi nó không dùng được.** Một cái chuông im lặng vì
không nhìn thấy gì thì tệ hơn không có chuông — nó tạo cảm giác đang được
canh. Mọi phép kiểm ở đây phân biệt ba trạng thái: *đạt* / *không đạt* /
**chưa kiểm được**, và trạng thái thứ ba không bao giờ được gộp vào trạng
thái đầu.

**Đối chiếu bằng nguồn ngoài.** Bảng lịch nghỉ giao dịch không được chép từ
báo rồi tin: nó phải tái lập đúng chuỗi phiên quan sát được (162/162 phiên,
lệch 0 ở cả hai chiều). Bản chép đầu tiên sai một ngày, và phép đối chiếu
bắt được.

**719 test**, chạy offline không cần mạng lẫn credential. CI kiểm cả cú
pháp Python 3.11 cho từng file *và* cho python nhúng trong workflow YAML —
máy phát triển chạy 3.13, và khoảng cách đó đã ẩn được lỗi một lần.

---

## Chạy thử

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # rồi điền
```

```bash
pytest tests/ -q          # 719 test, không cần mạng
streamlit run app.py      # giao diện
python run_daily.py       # một lượt quét + cập nhật sổ lệnh
```

Không cấu hình `secrets.toml` thì phần kho ngoài tắt sạch, app vẫn chạy.
**Đừng bao giờ commit file đó** — nó đã nằm trong `.gitignore`.

---

## Kiến trúc — bản vẽ và bản thật

| File | Là gì |
|---|---|
| `architecture_diagram.html` | bản mô tả tham vọng ban đầu |
| `architecture_diagram_v2.html` | bản đã vá 7 lỗ hổng thiết kế |
| **`architecture_asbuilt.html`** | **thứ đo được khi chạy thật** |

Ba bản đầu mô tả thứ *nên* chạy. Chỉ bản as-built mô tả thứ *đang* chạy.
Khi hai bên lệch nhau, bản as-built đúng.

Sơ đồ vẽ 6 agent độc lập, một tầng tranh luận đa chiều và một chốt chặn an
toàn. Đo trên 573 phiên: **1 agent là hằng số**, tầng tranh luận điều chỉnh
±0,9 điểm trên thang 100 (trung bình đúng bằng 0), và chốt chặn an toàn
kích hoạt **0%**. Bỏ hẳn cả hai tầng cuối: 572/573 phiên cho cùng quyết
định.

Nguyên nhân không phải mã kém, mà là **thiếu dữ liệu độc lập** — sáu agent
đều tính từ cùng một chuỗi giá, nên về lý thuyết chúng không tạo được thông
tin ngoài thứ đã có trong chuỗi đó.

> Đây là mâu thuẫn cốt lõi của dự án: *phần đo được thì không có tín hiệu,
> phần có thể có tín hiệu thì không đo được.*

---

## Tài liệu

| File | Vai trò |
|---|---|
| [`NGUYEN-TAC-DO-LUONG.md`](NGUYEN-TAC-DO-LUONG.md) | **8 bất biến đo lường.** Đọc trước khi sửa bất cứ thứ gì liên quan tới kết quả |
| [`MO-XE-KIEN-TRUC.md`](MO-XE-KIEN-TRUC.md) | Mổ xẻ 5 tầng: thành phần nào thật sự chạy, thành phần nào là trang trí |
| [`CLAUDE.md`](CLAUDE.md) | Kiến trúc và luật chơi — thứ ít đổi nhất |
| [`docs/STATE.md`](docs/STATE.md) | Nhật ký từng bước: đo được gì, cái gì chưa kiểm được, cái gì đã sai |
| [`docs/HANDOFF.md`](docs/HANDOFF.md) | Bàn giao 19/08/2026 — **đã cũ**, giữ làm mốc lịch sử |

Hai file đầu là bắt buộc, và có hook chặn ở `tools/cua_doc_bat_buoc.py`.

---

## Trạng thái hiện tại

**Cổng mở lệnh (C5) đang ĐÓNG**, đóng bằng tay, khoá bởi test.

Bằng chứng tiến-về-trước đã đóng: **0**. Sổ 117 lệnh trên kho ngoài chưa
bao giờ tích luỹ một lệnh nào từ việc quét tiến về phía trước — mọi con số
lịch sử nói về *một lượt mô phỏng*, không phải kết quả tích luỹ.

Số học không dễ chịu: cần ~1.050 lệnh để kỳ vọng loại được số 0 (~23 năm ở
nhịp 45 lệnh/năm); alpha cần 22.601 lệnh. *"Chờ thêm dữ liệu rồi quyết"*
không phải một lựa chọn khả thi, và repo này ghi rõ điều đó thay vì lảng
tránh.

---

## Giấy phép

Chưa có. Mặc định là **giữ toàn quyền** — nếu bạn muốn dùng lại, hãy mở
issue hỏi trước.

Dữ liệu thị trường thuộc về nhà cung cấp tương ứng. Tài liệu kỹ thuật của
gói vnstock **không** được lưu trong repo này theo đúng giấy phép của nó.
