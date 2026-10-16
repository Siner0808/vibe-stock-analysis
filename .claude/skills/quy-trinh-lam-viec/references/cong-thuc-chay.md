# Công thức chạy và chờ

Mọi dòng ở đây đến từ một lượt mất thời gian thật trong phiên 07/09/2026.

---

## Môi trường

```bash
export PYTHONIOENCODING=utf-8
./.venv/Scripts/python.exe        # KHONG dung `python` he thong
```

Thiếu `PYTHONIOENCODING` thì mọi lệnh in tiếng Việt ra thẳng terminal sẽ
nổ `UnicodeEncodeError` (cp1258 trên máy này).

---

## Ghi ra log, ĐỪNG pipe

```bash
# DUNG
./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/kq.log 2>&1

# SAI
# lenh-xau-ok: mẫu phản ví dụ, nguyên văn hình dạng mục này dạy tránh
./.venv/Scripts/python.exe -m pytest tests/ -q | tail -5
```

`tail` đệm toàn bộ output tới khi ống đóng. Với một lượt chạy nền thì
không đọc được gì cho tới lúc nó xong — và rồi sẽ ngồi hỏi "xong chưa".
Đếm được **ít nhất 10 lượt gọi công cụ** như vậy trong một phiên.

`tools/cua_bash_an_toan.py` chặn `pytest … | tail`.

**Và có lý do THỨ HAI, im lặng hơn (08/09/2026):** mã thoát của một ống là
mã thoát của lệnh **cuối**, tức `tail`, tức **luôn 0**. Nên
`pytest … | tail && <viec tiep>` chạy tiếp dù pytest đỏ. Một phép kiểm bị
nuốt mã thoát không phải phép kiểm. Xem `loi-da-mac.md` lỗi 18.

---

## Chờ: KHÔNG poll — và cũng KHÔNG kết luận sớm

Chạy nền thì hệ thống **tự báo** khi xong. Hỏi lại giữa chừng chỉ tốn
lượt gọi và nhận về màn hình trống (xem trên).

Nếu thật sự cần thấy tiến độ giữa chừng: đọc file log, và nhớ Python
**đệm stdout khi ghi vào file** — muốn thấy ngay thì `python -u`.

> **Một lượt quét bị đẩy sang chạy nền là một phép đo CHƯA XONG.**
>
> Ngày 07/09/2026: chạy một lượt grep **hẹp** trên một file và một lượt
> **rộng** toàn repo cho cùng câu hỏi. Lượt rộng quá 120 giây nên chạy
> nền. Tôi trả lời bằng lượt hẹp; lượt rộng xong sau và **nói ngược
> lại** — kết luận đã phát ra là sai.
>
> Đợi nó, hoặc nói rõ: *"trong phạm vi đã quét"*. Đừng phát biểu như
> thể đã quét hết.

---

## `-s` không phải điều kiện của bộ test

`pytest -s` tắt bắt stdout, nên mọi `print` tiếng Việt đi thẳng ra
terminal và nổ `UnicodeEncodeError`. Bộ test thật **không** dùng `-s`.

> Ngày 07/09/2026 tôi chạy `-s`, thấy đỏ, và suýt báo cáo đó là một lỗi
> sống của dự án. Chạy lại không có `-s`: xanh. Cờ tôi tự thêm vào, không
> phải điều kiện của hệ thống.

Muốn xem `print` mà không nổ: `PYTHONIOENCODING=utf-8` rồi mới `-s`.

---

## Đừng sửa file khi một lượt chạy đang bay

pytest đọc file **lúc chạy test**, không phải lúc collect. Sửa
`CLAUDE.md` giữa chừng thì 14 file test đọc nó có thể thấy bản dở dang.

Lỡ rồi thì chạy lại đúng những file đọc file vừa sửa:

```bash
./.venv/Scripts/python.exe -m pytest $(grep -ln "CLAUDE.md" tests/*.py | tr '\n' ' ') -q
```

---

## Năm cổng — một lệnh, chạy cùng lúc (BƯỚC 201)

```bash
./.venv/Scripts/python.exe tools/nam_cong.py --thu-muc-log /tmp/nc > /tmp/nc.txt 2>&1
```

Từng cổng lẻ (cùng lệnh `tools/nam_cong.py` chạy bên trong):

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/g1.log 2>&1
./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py
./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo
./.venv/Scripts/python.exe tools/kiem_test_chay_rieng.py --im > /tmp/g4.log 2>&1
./.venv/Scripts/python.exe tools/kiem_so_test_khong_giam.py
```

> 🔴 **Tiêu đề mục này ghi *"Bốn cổng"* cho tới 14/09/2026**, bốn ngày
> sau khi cổng thứ năm ra đời. Đúng hình dạng lệch mà dự án đã trả giá
> nhiều lần — `N_DAY_DU` 596/451, cờ C5. Nay có
> `tests/test_bo_cong_khop_CI.py` bắt danh sách cổng trong tài liệu phải
> khớp danh sách CI thật sự chạy.

Vài test ghi thư mục tạm vào **gốc repo**, nên hai tiến trình pytest cùng
lúc cho **đỏ giả**. Đây là ràng buộc thật, không phải sở thích.
> ⚠️ **HẾT ĐÚNG 16/10/2026 (BƯỚC 201):** ràng buộc ấy có MỘT nguồn —
> `tests/test_chan_bia_so_lieu.py` đặt thư mục tạm `tmp…` có file mẫu ở gốc, test quét repo ở
> tiến trình khác đọc đúng lúc nó bị xoá (`FileNotFoundError`, 3/158 file mỗi vòng
> 8 tiến trình). Nguồn đã dọn: file tạm của test chỉ ở `.tam_test/`, nơi
> `tools/duyet_repo.py` bỏ qua (luật 3) → 0/158 ở hai vòng. Năm cổng chạy cùng lúc
> bằng `tools/nam_cong.py`; số đo ở `docs/STATE.md` BƯỚC 201.

Thời gian đo 07/09/2026 ở máy local: cổng 1 ≈ 150s · cổng 4 ≈ 220s.
🔴 **HẾT ĐÚNG:** bộ test đã lớn lên (874 test ngày 09/09/2026, hơn 3.000 nay) —
số hiện hành ở mục *Phiên đám mây* dưới đây; đừng chờ "150s" rồi kết luận
cổng treo.

---

## Đọc mã thoát cho đúng

| Cổng | 0 | 1 | 2 |
|---|---|---|---|
| `tools/kiem_cu_phap_311.py` | sạch | có file không nạp được bằng 3.11 | **chưa kiểm được** |
| `tools/kiem_test_chay_rieng.py` | sạch | có file đỏ khi chạy riêng | **chưa kiểm được** |
| `tools/chan_bia_so_lieu.py --quet-repo` | 0 CHẶN | có mẫu mức CHẶN | — |

**2 không phải là sạch.** Trên CI nó là lỗi: runner chính là môi trường
mà công cụ nói nó chưa kiểm được.

---

## Phiên đám mây (không `.venv`, không `vnstock`)

Đo 12/10/2026 (BƯỚC 183) trên container Linux, Python 3.13. Mọi lệnh ở trên viết cho
máy Windows (`./.venv/Scripts/python.exe`); ở đây KHÔNG có `.venv/`, không có
`vnstock`/`vnai` (kho hãng `vnstocks.com/api/simple` bị proxy chặn: `curl` trả
`CONNECT tunnel failed, response 403`; PyPI vẫn với tới). Công thức này từng được dựng lại
từ đầu ở mười mục BƯỚC 171–182 của `docs/STATE.md`
(`grep -c "Năm cổng (đám mây" docs/STATE.md` → 10).

**1. Dựng venv ngoài repo.** `pip install` của Python hệ thống nổ `TypeError … 'NoneType'`
ở bộ giải phụ thuộc, nên phải đi qua venv:

```bash
# lenh-xau-ok: python3 hệ thống chỉ để TẠO venv; mọi lệnh sau đi qua python của venv
python3 -m venv /tmp/venv_ci
grep -v -e '^#' -e '^--' -e '^vnstock' -e '^vnai' requirements.txt > /tmp/req_dam_may.txt
/tmp/venv_ci/bin/pip install -q pytest -r /tmp/req_dam_may.txt
```

Dòng `grep` bỏ chú thích, dòng `--extra-index-url` và hai gói của kho hãng
(`vnstock`, `vnai`); phần còn lại cài từ PyPI (đo: 12 gói, 43 giây).

**2. Năm cổng**, log ra file — cùng lệnh như mục trên, thay python (hoặc một lệnh:
`/tmp/venv_ci/bin/python tools/nam_cong.py --thu-muc-log /tmp/nc`, BƯỚC 201):

```bash
/tmp/venv_ci/bin/python -m pytest tests/ -q -rs > /tmp/g1.log 2>&1
/tmp/venv_ci/bin/python tools/kiem_cu_phap_311.py
/tmp/venv_ci/bin/python tools/chan_bia_so_lieu.py --quet-repo
/tmp/venv_ci/bin/python tools/kiem_test_chay_rieng.py --im > /tmp/g4.log 2>&1
/tmp/venv_ci/bin/python tools/kiem_so_test_khong_giam.py
```

Cổng 2 tự tìm `python3.11` trên PATH (`/usr/bin/python3.11` có sẵn). Nếu không có, nó trả mã
thoát **2** (chưa kiểm được), không phải xanh.

**3. Thời gian đo** (12/10/2026): cổng 1 ≈ 568s · cổng 2 ≈ 1s · cổng 3 ≈ 2s ·
cổng 4 ≈ 730s · cổng 5 ≈ 3s. Chúng đổi theo tải máy; nói ra là một khoảng.

**4. Đỏ và skip ĐÃ BIẾT ở môi trường này** (3127 test: 3123 pass · 1 đỏ · 3 skip):

| test | trạng thái | vì sao |
|---|---|---|
| `tests/test_requirements.py::test_goi_tu_kho_hang_GHIM_DUNG_ban_va_KHOP_ban_dang_chay` | đỏ MÔI TRƯỜNG | không có `vnstock`/`vnai` để so bản ghim; không phải lỗi của thay đổi |
| `tests/test_cache_bctc_du_ky.py` | skip | dữ liệu BCTC chỉ nằm ở máy người dùng |
| `tests/test_vnstock_goi.py` | skip | `vnai` không có ở môi trường này |
| `tests/test_tai_lieu_khop_hang_so.py` | skip | đoạn được canh đã gỡ hẳn |

Một test đọc dữ liệu bị `.gitignore` sẽ **skip lặng lẽ** ở đây (worktree/clone chỉ có thứ
git theo dõi), và xanh ở đây không bằng xanh ở máy người dùng. Luôn thêm `-rs` để đọc
LÝ DO skip; nếu một test lẽ ra phải chạy mà skip, nói ra trong báo cáo.

**5. Đọc sai thì mất 10 phút.** Đỏ môi trường (bảng trên) khác đỏ CHỜ (ví dụ mục sổ tay
chưa có, `references/soat-cheo-notebooklm.md`, mục *Phiên đám mây*): cả hai đều đỏ ở cổng 1,
nhưng chỉ cái đầu là thứ phiên này không sửa được.
