# Kho `.db` ở gốc repo — bản kê trước lượt dọn 10/09/2026

Mọi file `.db` ở gốc repo đều **đã gitignore**, nên không file nào từng
được commit. Chúng là kết quả chạy tại máy, và tới 10/09/2026 chúng chiếm
**0.63 GB**.

Luật của dự án là **không xoá `.db` ở gốc repo mà chưa hỏi** — đó là dữ
liệu đo của người dùng. Người dùng chốt xoá ngày 10/09/2026, giới hạn ở
*"file không dùng đến hoặc đã cũ"*. File này là bản kê lập **trước** lượt
xoá, để con số của thứ bị xoá vẫn còn dấu sau khi các byte đã đi.

Số lệnh và số quyết định dưới đây đọc thẳng từ từng file bằng SQLite,
không gõ tay.

---

## GIỮ — 9 file, 105 MB

Được trích dẫn trong tài liệu/mã nguồn, hoặc là bằng chứng của một phát
hiện chưa ai kiểm độc lập.

| file | MB | ngày | lệnh | quyết định | vì sao giữ |
|---|---:|---|---:|---:|---|
| `do2_1.db` | 11 | 2026-09-09 | 379 | 8936 | ĐO 2 lượt 1 · bằng chứng lỗi 24 (xáo tập lệnh) |
| `do2_2.db` | 11 | 2026-09-09 | 398 | 8956 | ĐO 2 lượt 2 · bằng chứng lỗi 24 |
| `do2_3.db` | 11 | 2026-09-09 | 509 | 8604 | ĐO 2 lượt 3 · docs/STATE.md BƯỚC 46 |
| `do2_4.db` | 11 | 2026-09-09 | 547 | 8599 | ĐO 2 lượt 4 · bằng chứng lỗi 24 |
| `paper_custom20loop_18m_loop_11.db` | 20 | 2026-08-12 | 1126 | 19134 | +636,11% tái lập được từ đây · NGUYEN-TAC-DO-LUONG.md |
| `paper_oos_2024_2025.db` | 4 | 2026-08-07 | 183 | 3855 | đầu ra của run_oos_test.py |
| `paper_trades.db` | 13 | 2026-08-20 | 113 | 13589 | sổ lệnh đang chạy · app.py + hai workflow đọc |
| `paper_trades_seeded_insample.db` | 15 | 2026-08-12 | 1787 | 13840 | bằng chứng sự cố 12/08/2026 · CLAUDE.md |
| `paper_vn100_18m.db` | 8 | 2026-08-07 | 347 | 7605 | đầu ra của run_vn100_18m_test.py |

---

## ĐÃ XOÁ — 31 file, 0.52 GB

Không file nào được trích dẫn ở bất cứ đâu trong repo. Mọi con số rút ra
từ chúng đều đã nằm trong tài liệu **và** có lệnh tái lập:
`tools/do1_chi_phi_thuc_thi.py` cho nhóm `wf_*`, `walkforward.py` cho các
lượt quét ngưỡng, `run_oos_test.py` / `run_vn100_18m_test.py` cho phần
còn lại.

| file | MB | ngày | lệnh | quyết định | ghi chú |
|---|---:|---|---:|---:|---|
| `paper_custom20loop_18m_loop_10.db` | 20 | 2026-08-12 | 1215 | 18738 |  |
| `paper_custom20loop_18m_loop_12.db` | 21 | 2026-08-12 | 999 | 19903 |  |
| `paper_custom20loop_18m_loop_17.db` | 22 | 2026-08-12 | 608 | 21891 |  |
| `paper_custom20loop_18m_loop_18.db` | 22 | 2026-08-12 | 527 | 22326 |  |
| `paper_custom20loop_18m_loop_19.db` | 23 | 2026-08-12 | 429 | 22751 |  |
| `paper_custom20loop_18m_loop_20.db` | 23 | 2026-08-12 | 365 | 23215 |  |
| `paper_custom20loop_18m_loop_9.db` | 19 | 2026-08-12 | 1304 | 18318 |  |
| `paper_custom71_18m_loop_1.db` | 17 | 2026-08-11 | 1899 | 15847 |  |
| `paper_custom71_18m_loop_10.db` | 23 | 2026-08-11 | 329 | 23509 |  |
| `paper_custom71_18m_loop_2.db` | 18 | 2026-08-11 | 1656 | 16753 |  |
| `paper_custom71_18m_loop_3.db` | 19 | 2026-08-11 | 1494 | 17479 |  |
| `paper_custom71_18m_loop_4.db` | 19 | 2026-08-11 | 1302 | 18331 |  |
| `paper_custom71_18m_loop_5.db` | 20 | 2026-08-11 | 1123 | 19146 |  |
| `paper_custom71_18m_loop_6.db` | 21 | 2026-08-11 | 936 | 20296 |  |
| `paper_custom71_18m_loop_7.db` | 21 | 2026-08-11 | 775 | 21061 |  |
| `paper_custom71_18m_loop_8.db` | 22 | 2026-08-11 | 606 | 21896 |  |
| `paper_custom71_18m_loop_9.db` | 23 | 2026-08-11 | 428 | 22765 |  |
| `paper_full_learning.db` | 13 | 2026-08-10 | 1051 | 12597 |  |
| `paper_oos_vn100.db` | 5 | 2026-08-10 | 170 | 5410 |  |
| `vn30_test.db` | 4 | 2026-08-06 | 205 | 4260 |  |
| `vn30_test2.db` | 4 | 2026-08-06 | 143 | 4220 |  |
| `wf_chan_doan.db` | 0 | 2026-09-09 | 0 | 180 |  |
| `wf_is_45.db` | 18 | 2026-09-09 | 2190 | 12424 |  |
| `wf_is_48.db` | 19 | 2026-09-09 | 1970 | 13519 |  |
| `wf_is_50.db` | 19 | 2026-09-09 | 1799 | 14376 |  |
| `wf_is_52.db` | 20 | 2026-09-09 | 1647 | 15240 |  |
| `wf_is_55.db` | 21 | 2026-09-09 | 1377 | 16580 |  |
| `wf_is_58.db` | 23 | 2026-09-09 | 1148 | 18038 |  |
| `wf_is_62.db` | 24 | 2026-09-09 | 829 | 19987 |  |
| `wf_oos.db` | 11 | 2026-09-09 | 379 | 8936 |  |
| `wf_thu_fixture.db` | 1 | 2026-09-09 | 0 | 540 |  |

---

## Một điều đọc ra được từ chính bản kê này

`wf_oos.db` (ĐO 1, 09/09 lúc 16:56) và `do2_1.db` (ĐO 2 lượt đối chứng,
09/09 lúc 17:17) có **379 lệnh và 8.936 quyết định — y hệt nhau**. Hai
tiến trình riêng, hai dụng cụ riêng, cách nhau 20 phút.

Bất biến 2 (*"chấm cùng một gói dữ liệu hai lần phải ra cùng một điểm"*)
tới nay luôn được kiểm ở tầng **con số báo cáo**. Đây là lần đầu nó khớp
ở tầng **bản ghi thô** — cùng số dòng trong cả hai bảng.
