# Biên bản mẫu của vòng học trên thị trường giả (BƯỚC 290)

Do `tools/chay_vong_thi_truong_gia.py --ghi` sinh; một thị trường, không phải kết quả.

Sinh lại CÓ CHỦ Ý ở BƯỚC 300: bộ đề xuất xếp 11 spec theo z = (Δ − μ)/σ thay vì Δ thô (`docs/thiet-ke-c4-thi-truong-gia.md` mục 21.1), nên thứ tự các hàng và ba spec được khai đổi; Δ từng spec không đổi so với bản BƯỚC 290. Các cột in ra vẫn là Δ và IC, không in z.

```text
THỊ TRƯỜNG GIẢ — dòng hạt 9001, chỉ số 1, κ = 0.044587  (60 mã GIA01…GIA60, 594 phiên 2100-01-04 → 2102-04-13)
(Một thị trường là một biên bản minh hoạ. KHÔNG có tỷ lệ nào ở đây; đó là Lát 5.)

BƯỚC 1 — BỘ ĐỀ XUẤT CƠ SỞ (chỉ thấy phiên 0…125; 104 phiên có nhãn, 60 mã). Δ = IC(spec) − IC(điểm đã ghi):
    1. mono_volume_score    Δ = +0.1593  (IC spec +0.2530, IC đã ghi +0.0937)   ← khai
    2. deu                  Δ = +0.0224  (IC spec +0.1161, IC đã ghi +0.0937)   ← khai
    3. bo_trend_score       Δ = +0.0564  (IC spec +0.1501, IC đã ghi +0.0937)   ← khai
    4. bo_momentum_score    Δ = +0.0399  (IC spec +0.1336, IC đã ghi +0.0937)
    5. mono_sr_score        Δ = +0.0041  (IC spec +0.0978, IC đã ghi +0.0937)
    6. mono_risk_score      Δ = -0.0303  (IC spec +0.0633, IC đã ghi +0.0937)
    7. bo_risk_score        Δ = -0.0048  (IC spec +0.0889, IC đã ghi +0.0937)
    8. bo_sr_score          Δ = -0.0189  (IC spec +0.0748, IC đã ghi +0.0937)
    9. mono_momentum_score  Δ = -0.0785  (IC spec +0.0152, IC đã ghi +0.0937)
   10. mono_trend_score     Δ = -0.1050  (IC spec -0.0113, IC đã ghi +0.0937)
   11. bo_volume_score      Δ = -0.0583  (IC spec +0.0354, IC đã ghi +0.0937)
   khai 3 spec đầu có Δ > 0, mỗi spec một tháng: mono_volume_score, deu, bo_trend_score

BƯỚC 2 — KHAI (sổ ứng viên giả trong bộ nhớ; K = 3 ứng viên đã khai)
   DX1 = mono_volume_score    khai phiên 128 (2100-07-01), đọc phiên 401 (2101-07-19)
   DX2 = deu                  khai phiên 150 (2100-08-02), đọc phiên 423 (2101-08-18)
   DX3 = bo_trend_score       khai phiên 172 (2100-09-01), đọc phiên 445 (2101-09-19)

BƯỚC 3 — XÁC NHẬN (`cham_xac_nhan.cham`: đọc ở đúng 252 phiên có nhãn, ngưỡng 0,05/K, null hoán vị mã)
   DX1 đọc phiên 401 (2101-07-19): K = 3, ngưỡng 0.01667, 252 phiên × 60 mã → QUA  (Δ = +0.1630, p = 5.14e-11)

BƯỚC 4 — NÂNG CẤP (chỉ trong thị trường giả; một đời)
   phiên bản 1 từ DX1: spec {"volume_score": 1.0}
   đọc ở phiên 401, HIỆU LỰC TỪ PHIÊN SAU: phiên 402 (2101-07-20)
   bằng chứng: p = 5.14e-11, Δ = +0.1630, 252 phiên, K = 3, hạt 20261007
   huỷ vì nâng cấp (K vẫn đếm = 3): DX2, DX3
   trạng thái cuối: DX1 = QUA, DX2 = bi_huy_vi_nang_cap, DX3 = bi_huy_vi_nang_cap

BƯỚC 5 — KIỂM TIẾN-VỀ-TRƯỚC (chỉ phiên từ phiên hiệu lực trở đi)
   từ 2101-07-20: 126/126 phiên có nhãn × 60 mã
   IC điểm đã ghi +0.0268, IC phiên bản mới +0.1803, ΔIC thực hiện = +0.1535  (một thị trường, không có KTC)

BƯỚC 6 — SỰ THẬT (oracle, đọc SAU khi vòng đã quyết; vòng không thấy nó)
   mono_volume_score    ΔIC_true = +0.1423 ± 0.0041   (đã khai)
   deu                  ΔIC_true = +0.0048 ± 0.0009   (đã khai)
   bo_trend_score       ΔIC_true = +0.0220 ± 0.0022   (đã khai)
   doi_cho_trend_sr     ΔIC_true = +0.0013 ± 0.0015
   bo_volume_score      ΔIC_true = -0.0463 ± 0.0012
   (mẫu oracle 5000 phiên, hạt [9001, 1, 1]; ± là sai số Monte Carlo ước lượng)
```
