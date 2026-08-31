---
name: quy-trinh-do-luong
description: Quy trinh bat buoc khi sua bat cu thu gi anh huong toi KET QUA DO trong vibe_preview - diem so, co vi the, chi phi, nguong, cong an toan, backtest, walk-forward. Dung khi sap sua mot trong nhung thu do, khi them mot gac moi, hoac khi mot con so dep len sau thay doi.
---

# Quy trình sửa thứ ảnh hưởng tới kết quả đo

Dự án này đã **năm lần** cho ra con số đẹp mà sau đó hoá ra vô nghĩa. Không
lần nào cố ý. Quy trình dưới đây là thứ còn lại sau năm lần đó.

**Quy tắc số 1 — nếu một thay đổi làm con số đẹp lên đáng kể, giả định đầu
tiên phải là CÓ LỖI.** Số xấu đi là chiều an toàn.

---

## Bước 0 — Đọc trước khi chạm

Bắt buộc, và hook `tools/cua_doc_bat_buoc.py` chỉ ép được khi bạn dùng
Read/Write/Edit — **đi qua Bash thì không ai chặn**. Tự đọc:

| File | Cho biết |
|---|---|
| `NGUYEN-TAC-DO-LUONG.md` | 8 bất biến đo lường |
| `MO-XE-KIEN-TRUC.md` | thành phần nào đang chạy thật, cái nào là trang trí |
| `docs/STATE.md` (mục cuối) | đã đo được gì, cái gì chưa kiểm được |

Rồi hỏi **phép đo nào sẽ chứng minh thay đổi này đúng** — trước khi sửa,
không phải sau. Nếu câu trả lời là "không đo được", xem `references/bay.md`
mục *"Thay đổi không đo được"*.

## Bước 1 — Sửa

```bash
./.venv/Scripts/python.exe        # python hệ thống KHÔNG có numpy
```

**Vá lớn: viết một file `.py` rồi chạy nó. Không dùng bash heredoc trên file
repo** — `sed -i` của mingw làm hỏng CRLF và ký tự không phải ASCII.

Khuôn vá, và hai dòng quan trọng nhất là `count(cu) != 1` với `newline`:

```python
s = F.read_text(encoding="utf-8").replace("\r\n", "\n")
for cu, moi in CAP:
    if s.count(cu) != 1:          # neo mơ hồ = dừng, không đoán
        print(f"DUNG: neo khop {s.count(cu)} lan"); sys.exit(1)
    s = s.replace(cu, moi, 1)
F.write_text(s, encoding="utf-8", newline="\r\n")   # repo dùng CRLF
```

**Suy ra, đừng gõ.** Một ngưỡng gõ tay ở hai chỗ sẽ trôi ra khỏi nhau —
`run_daily` từng cầm `50.0` trong khi `paper_trading` cầm `62`.

## Bước 2 — Đột biến mọi gác mới

Gác vừa viết, vừa xanh, và vừa vô dụng là chuyện **thường xuyên**: ngày
31/08/2026 xảy ra ba lần trong một phiên. Viết đột biến rồi mới tin.

```
sửa mã cho SAI theo đúng cách gác phải bắt -> chạy bộ test -> phải ĐỎ
khôi phục -> so khớp TỪNG BYTE
```

**Gác một phép SUY RA thì kiểm HÌNH DẠNG biểu thức bằng AST, không kiểm giá
trị nó cho ra.** Giá trị trùng nhau tại một điểm là chuyện thường; cấu trúc
sai thì sai ở mọi điểm khác.

```python
v = _gan("CO_MUC_TIEU_PCT")
assert isinstance(v.op, ast.Div)                    # CHIA, không phải NHÂN
assert v.left.id == "TRAN_VON_CAM_KET_PCT"
```

Ba mẫu đột biến hay sống sót nhất: `references/bay.md`.

## Bước 3 — Ba cổng gác, ĐÚNG THỨ TỰ

Thứ tự là bắt buộc, không phải sở thích — có test ghi thư mục tạm vào gốc
repo và gây đỏ giả nếu chạy song song.

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q            # 1. TRƯỚC
./.venv/Scripts/python.exe tools/kiem_cu_phap_311.py      # 2. SAU khi pytest xong
./.venv/Scripts/python.exe tools/chan_bia_so_lieu.py --quet-repo   # 3.
```

Mã thoát 2 của cổng 2 nghĩa là **chưa kiểm được**, không phải sạch.

## Bước 4 — Giao

- **KHÔNG đẩy thẳng `main`** (branch protection). Tạo nhánh, push, rồi
  **nói rõ với người dùng là họ phải tự mở PR** — `gh` không cài trên máy này.
- Commit body **ASCII**, không `Co-Authored-By`.
- Ghi vào `docs/STATE.md` cả **kết quả lẫn giả thuyết đã bị bác**. Giả
  thuyết sai nghe hợp lý là thứ đáng giữ nhất.

## Ranh giới không vượt qua

- **Không đặt lệnh thật.** Agent chuẩn bị → người xác nhận → người đặt lệnh.
- Không commit secrets, `*.db`, `sl_pattern_memory.json`, `backtest/cache/`.
- **Không xoá file `*.db` ở gốc repo** — dữ liệu đo của người dùng. Hỏi trước.
- Không ép hạng vnstock trong mã nguồn.
- Không ghi tài liệu skill của vnstock ra đĩa (giấy phép cấm).
- App không được tự push lên repo nó đang chạy.
