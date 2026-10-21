# Thiết kế ý 5 — tra tiền lệ, chỉ để hiện

**Mốc:** B3 (`docs/LO-TRINH.md`, giai đoạn B — sổ bài học: người dùng học từ sổ). **Duyệt:** người dùng
chốt từng phần ngày 20/10/2026 trong phiên leader (BƯỚC 210). **Trạng thái:** thiết kế; chưa có dòng mã
nào. **Làm mã SAU ĐO 29** (kho dựng từ sổ OOS của máy đo cuối cùng, mục 3).

Tài liệu này là đề bài cho phiên làm mã. Luật chung của dự án (vá file, đột biến, năm cổng, giao PR)
nằm ở skill `quy-trinh-lam-viec` — đi theo nó, đừng chép lại vào đây.

---

## 1. Quyết định của người dùng (nguyên văn lựa chọn, 20/10/2026)

| Câu hỏi | Trả lời |
|---|---|
| Bàn ý nào trong bảng 7 ý tưởng (tra ngoài 15–16/10)? | *"Ý 5: tra tiền lệ kNN (Recommended)"* |
| Kho tiền lệ lấy từ đâu? | *"Mô phỏng trước, sổ thật thêm dần (Recommended)"* |
| Hai tín hiệu "giống nhau" khi nào? (lần 1) | *"Cùng bối cảnh (Recommended)"* — ngành × VN-Index trên/dưới MA50 × dải điểm. 🔴 **HẾT ĐÚNG cùng ngày** — xem dòng cuối |
| Khối tiền lệ hiện ở đâu? | *"Trong nhật ký lệnh (Recommended)"* |
| Bản nháp và lịch | *"Ổn, làm sau bước sửa khớp (Recommended)"* |
| "Giống" (lần 2, sau số đếm mục 4) | *"Dải điểm × độ cao VNI (Recommended)"* |

Ý tưởng đến từ một lượt tra ngoài; theo quy ước người dùng chốt 16/10, nó chỉ thành việc sau khi người
dùng duyệt (bảng trên).

## 2. Mục đích và ranh giới

- **Để HỌC, không để dự báo.** Với mỗi lệnh trong nhật ký, khối này cho người dùng xem lại những lệnh cũ
  có cùng bối cảnh đã kết thúc ra sao.
- **Điểm không dự báo được lợi nhuận** (`CLAUDE.md`, rho = −0,019), nên tỷ lệ thắng của một nhóm tiền lệ
  gần như chỉ là tỷ lệ nền cộng nhiễu. Một khối chỉ in *"2/7 thắng"* dạy người xem đọc tín hiệu từ nhiễu —
  đúng thứ Quy tắc 1 chống. Vì thế tỷ lệ nền và độ bất định LUÔN nằm cạnh số của nhóm (mục 6).
- **CHỈ ĐỂ HIỆN.** Không vào điểm, ngưỡng, lệnh, kế hoạch vào lệnh hay bộ nhớ hậu nghiệm. Gác AST ở mục 8.
- Khác `post_mortem_learning` (mẫu cắt lỗ khớp ±5 trên ba điểm thành phần, TRỪ điểm, đường thật giữ 0 mẫu
  theo Q1): ý 5 không tác động, xét cả thắng lẫn thua, và khoá nhóm không dùng điểm thành phần — 44/44 mẫu
  cũ chỉ có hai tổ hợp, điểm thành phần quá thô để "giống" có nghĩa.

## 3. Kho tiền lệ

| phần | nguồn | lệnh nào | nhãn |
|---|---|---|---|
| mô phỏng | sổ OOS dòng "BẬT · theo ngày" của máy đo CUỐI CÙNG trên cache `acf6dca1…` (sau ĐO 29; nếu ĐO 29 chưa xong thì lượt B của ĐO 28) | đã đóng, điểm vào ≥ `paper_trading.BUY_THRESHOLD` (suy ra, không gõ) | "mô phỏng" |
| thật | nhật ký (tab `nhat_ky`, app đang đọc qua `_doc_so_ban_tin()` — MỘT đường đọc Sheets) | đã có nửa ĐÓNG | "thật" |

- Lý do lọc điểm: lượt walk-forward chọn ngưỡng 45 trên IS nên 498/617 lệnh OOS có điểm dưới 62 — không
  lệnh thật nào ở dải ấy (đo 20/10/2026, mục 4).
- Phần mô phỏng là MỘT tệp JSON trong repo (không phải `*.db`), dựng bằng `tools/dung_kho_tien_le.py` (viết
  khi làm mã), mỗi dòng: `ma` · `ngay_tin_hieu` · `ngay_vao` · `ngay_ra` · `diem_vao` · `vni_pct_tren_ma50` ·
  `loi_nhuan_rong_pct` · `ly_do_thoat`. Đầu tệp ghi: băm cache, commit của lượt chạy, số ĐO, ngưỡng IS, lệnh dựng.
- `vni_pct_tren_ma50` của phần mô phỏng tính bằng ĐÚNG `nhat_ky_vi_sao.vni_so_voi_ma50` trên
  `market_filter.get_vni_df()` của cùng cache — cùng hàm sổ thật đã dùng khi ghi bối cảnh (BƯỚC 132).
- `loi_nhuan_rong_pct` của phần mô phỏng tính bằng đúng hàm sổ thật dùng (sau phí tầng 1), không công thức
  thứ hai.

## 4. Thế nào là "giống" — khoá nhóm

Khoá = (dải điểm vào, nấc VN-Index cao hơn MA50 ngày tín hiệu):

- dải điểm: [`BUY_THRESHOLD`, 70) · [70, ∞);
- nấc VN-Index: [0%, 2%) · [2%, 5%) · [5%, ∞) theo `vni_pct_tren_ma50`; dưới 0 (cổng mở lệnh lẽ ra đã chặn)
  hoặc thiếu → nhóm riêng "không xếp được", không gộp.

**Vì sao không theo bản lần 1.** Cổng mở lệnh bỏ qua mọi tín hiệu khi VN-Index dưới MA50
(`paper_trading.py`, `consider_entry`), nên chiều "trên/dưới MA50" luôn là "trên": đo 617/617 lệnh OOS. Số đếm
20/10/2026 trên 119 lệnh OOS điểm ≥ 62 — CHỈ ĐẾM, không nhìn kết cục:

| khoá | số nhóm | lệnh có nhóm ≥ 10 tiền lệ |
|---|---|---|
| ngành × dải điểm | 28 | 29/119 (24%) |
| chỉ ngành | 14 | 64/119 (54%) |
| **dải điểm × nấc VN-Index** | 6 | **107/119 (90%)** |
| ngành × nấc VN-Index | 36 | 21/119 (18%) |

Ba nấc 2% / 5% chọn theo số lệnh mỗi nấc trên cả kho (396 / 180 / 41), chưa ai nhìn kết cục. Đổi biên SAU
khi nhìn kết cục = bất biến 7; muốn đổi thì quyết lại cùng người dùng.

## 5. Chống nhìn tương lai

Tiền lệ của một lệnh chỉ gồm lệnh có **ngày RA < ngày VÀO** của lệnh đang xem: kết cục chỉ biết khi lệnh đã
đóng — cùng ý hàng rào `phien_hoc` của `post_mortem_learning`. Lệnh mô phỏng (2021–2026) đều đóng trước lệnh
thật đầu tiên (09/2026); hàng rào vẫn áp cho mọi lệnh, không dựa vào sự trùng hợp ấy.

## 6. Cách hiện (chi tiết nhật ký, cạnh hậu kiểm B1)

```
Tiền lệ lúc vào lệnh — điểm 62–69 · VN-Index cao hơn MA50 0–2%
  n tiền lệ (a mô phỏng, b thật): x thắng · y thua · z hoà — thắng p% [KTC 95%: lo ; hi]
  Nền (mọi tiền lệ có trước ngày vào): thắng P% [lo ; hi]
  → "không phân biệt được với nền" khi KTC của nhóm chứa P
  3 ca gần nhất: mã · ngày vào → ngày ra · lợi nhuận ròng · nhãn
```

- "Thắng / thua / hoà" = `so_bai_hoc.ket_qua_lenh` (lợi nhuận ròng sau phí) — một định nghĩa với sổ bài học.
- KTC 95% của tỷ lệ: Wilson.
- Nhóm dưới `N_TOI_THIEU_TIEN_LE` = 10: in *"chưa đủ tiền lệ (n = …)"*, không in tỷ lệ, không nới khoá.

## 7. Thành phần

- `tien_le.py` — module THUẦN: `khoa_nhom`, `chon_tien_le(kho, lenh)`, `tom_tat(...)`; không đọc mạng, đĩa
  hay Sheets.
- `tools/dung_kho_tien_le.py` — dựng tệp JSON phần mô phỏng (mục 3); chạy lại được, in băm cache và commit.
- `app.py` — khối "Tiền lệ" trong chi tiết nhật ký; lỗi đọc → `st.caption`, không sập tab.

## 8. Kiểm thử và gác

- Offline, kho giả tính tay: khoá nhóm ở mọi biên (61,99/62/69,99/70; 1,99/2/4,99/5; âm; thiếu);
  hàng rào ngày ra < ngày vào (cùng ngày phải BỊ loại); nhóm 9/10 tiền lệ; KTC chứa/không chứa nền.
- Gác CHỈ ĐỂ HIỆN (AST): đường sinh lệnh và đo (`paper_trading`, `run_daily`, `paper_runner`, `master_agent`,
  `walkforward`, …) không nhập `tien_le`.
- Gác một định nghĩa: `tien_le` gọi `so_bai_hoc.ket_qua_lenh`; dụng cụ dựng kho gọi
  `nhat_ky_vi_sao.vni_so_voi_ma50`.
- Đột biến mọi gác mới, vòng lặp tới khi đỏ hết.

## 9. Triển khai

1. Sau khi ĐO 29 merge: dựng kho từ sổ OOS lượt B của ĐO 29 (lưu như `scratch/luu_do28/`).
2. PR 1 — `tien_le.py` + dụng cụ + tệp kho + test. PR 2 — khối trên app; kiểm bằng mắt ở `localhost:8511`.
3. Không đổi luật hay kết luận đo → sổ tay khai `khong_bat_buoc_vi` nếu `tools/buoc_cham_luat.py` xác nhận.

## 10. Ước lượng — CHƯA ĐO

Tỷ lệ thắng của bất kỳ nhóm nào: chưa ai nhìn. Cỡ tệp kho (≈ 119 dòng nếu kho là lượt B của ĐO 28): ước lượng.

## 11. Không làm

Không khoảng cách điểm thành phần (kNN thật) — điểm quá thô (mục 2). Không chiều ngành (mục 4). Không dùng
kết cục tiền lệ để lọc hay xếp hạng tín hiệu. Không gọi API. Không đổi ngưỡng, điểm, lệnh hay sổ.
