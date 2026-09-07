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
./.venv/Scripts/python.exe -m pytest tests/ -q | tail -5
```

`tail` đệm toàn bộ output tới khi ống đóng. Với một lượt chạy nền thì
không đọc được gì cho tới lúc nó xong — và rồi sẽ ngồi hỏi "xong chưa".
Đếm được **ít nhất 10 lượt gọi công cụ** như vậy trong một phiên.

`tools/cua_bash_an_toan.py` chặn `pytest … | tail`.

---

## Chờ: KHÔNG poll

Chạy nền thì hệ thống **tự báo** khi xong. Hỏi lại giữa chừng chỉ tốn
lượt gọi và nhận về màn hình trống (xem trên).

Nếu thật sự cần thấy tiến độ giữa chừng: đọc file log, và nhớ Python
**đệm stdout khi ghi vào file** — muốn thấy ngay thì `python -u`.

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

## Bốn cổng, tuần tự, không song song

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q > /tmp/g1.log 2>&1
./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py
./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo
./.venv/Scripts/python.exe tools/kiem_test_chay_rieng.py --im > /tmp/g4.log 2>&1
```

Vài test ghi thư mục tạm vào **gốc repo**, nên hai tiến trình pytest cùng
lúc cho **đỏ giả**. Đây là ràng buộc thật, không phải sở thích.

Thời gian đo 07/09/2026 ở máy local: cổng 1 ≈ 150s · cổng 4 ≈ 220s.

---

## Đọc mã thoát cho đúng

| Cổng | 0 | 1 | 2 |
|---|---|---|---|
| `tools/kiem_cu_phap_311.py` | sạch | có file không nạp được bằng 3.11 | **chưa kiểm được** |
| `tools/kiem_test_chay_rieng.py` | sạch | có file đỏ khi chạy riêng | **chưa kiểm được** |
| `tools/chan_bia_so_lieu.py --quet-repo` | 0 CHẶN | có mẫu mức CHẶN | — |

**2 không phải là sạch.** Trên CI nó là lỗi: runner chính là môi trường
mà công cụ nói nó chưa kiểm được.
