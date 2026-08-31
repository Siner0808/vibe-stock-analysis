---
name: dividend-accounting-rules
description: Quy chuẩn kế toán tài chính và chống ảo giác (anti-hallucination) khi tính toán lãi/lỗ danh mục chứng khoán Việt Nam liên quan đến Cổ tức (tiền mặt, cổ phiếu thưởng, phát hành thêm). Dùng khi phân tích danh mục, đánh giá hiệu quả đầu tư, giải thích chênh lệch giá vốn, tránh bẫy tính trùng "lãi ảo" khi nhận cổ tức.
version: 1.0.0
last_updated: 24/08/2026
---

# Quy Tắc Hạch Toán Cổ Tức & Chống Ảo Giác Lãi/Lỗ Danh Mục

Quy chuẩn này nhằm loại bỏ hoàn toàn các lỗi sai logic và ảo giác toán học phổ biến khi tính toán hiệu quả đầu tư, giá vốn và lãi/lỗ của danh mục chứng khoán Việt Nam (HOSE, HNX, UPCOM) khi có sự kiện chia cổ tức (tiền mặt, cổ phiếu thưởng, quyền mua).

---

## 1. NGUYÊN LÝ BẤT BIẾN CỦA CỔ TỨC (DIVIDEND IRRELEVANCE)

1. **Bản chất Zero-Sum tại ngày Giao Dịch Không Hưởng Quyền (GDKHQ - $t_0$):**
   - Hành vi chia cổ tức **KHÔNG TỰ SINH RA MỘT ĐỒNG LÃI NÀO**.
   - Vào ngày GDKHQ, Sở Giao dịch Chứng khoán tự động điều chỉnh giảm giá tham chiếu của cổ phiếu:
     - **Cổ tức tiền mặt:** Thị giá bị trừ đúng bằng số tiền mặt nhận được ($P' = P - D$).
     - **Cổ tức cổ phiếu / Cổ phiếu thưởng:** Thị giá bị pha loãng theo tỷ lệ phát hành thêm ($P' = \frac{P}{1 + r}$).
   - **Tổng tài sản nhà đầu tư tại $t_0$ là không đổi**, thậm chí bị hao hụt do phải chịu **5% thuế TNCN** trên cổ tức nhận được.

2. **Lãi/Lỗ thực sự chỉ đến từ đâu?**
   - Chỉ khi cổ phiếu **tăng giá trên sàn sau ngày chốt quyền** (Capital Gain / hiện tượng "lấp gap sau chia") thì nhà đầu tư mới có lãi thật.
   - Nếu sau ngày chốt quyền, thị giá cổ phiếu tiếp tục giảm so với giá tham chiếu sau điều chỉnh $\rightarrow$ **Nhà đầu tư bị LỖ THẬT**.

---

## 2. CẠM BẪY CHÍ MẠNG: LỖI CỘNG TRÙNG 2 LẦN (DOUBLE-COUNTING PITFALL)

> [!CAUTION]
> **CẤM TUYỆT ĐỐI SAI LẦM SAU:**
> Lấy `Giá vốn sau điều chỉnh` đem so sánh với `Giá thị trường` nhưng lại **CỘNG THÊM khoản "Tiền cổ tức chờ về" hoặc "Cổ phiếu thưởng"** vào kết quả để biến vị thế đang lỗ thành lãi!

### ❌ Vì sao đây là lỗi sai nghiêm trọng?
1. Giá vốn hiển thị trên hầu hết các ứng dụng chứng khoán (VPS, SSI, TCBS, VNDirect...) **ĐÃ ĐƯỢC TỰ ĐỘNG ĐIỀU CHỈNH GIẢM** sau ngày GDKHQ tương ứng với cổ tức.
2. Khoản "Tiền cổ tức chờ về" thực chất là phần tiền **đã bị bóc tách từ thị giá cổ phiếu của chính nhà đầu tư** vào ngày chốt quyền.
3. Nếu:
   $$\text{Giá thị trường hiện tại} < \text{Giá vốn sau điều chỉnh}$$
   Thì nhà đầu tư **ĐANG THỰC SỰ LỖ** do thị giá sụt giảm sau ngày chia. Việc cộng thêm cổ tức vào lúc này là hành vi **tính trùng cổ tức 2 lần**, tạo ra mức lãi ảo vô căn cứ.

---

## 3. CÔNG THỨC CHUẨN XÁC TÍNH TOÁN LÃI / LỖ DANH MỤC

### Cách 1: Tính theo Giá vốn đã điều chỉnh (Phương pháp phổ biến trên App)
$$\text{Lãi / Lỗ vị thế} = \text{Tổng khối lượng (gồm cả CP thưởng)} \times (\text{Giá thị trường hiện tại} - \text{Giá vốn sau điều chỉnh})$$

* Nếu $\text{Giá thị trường} < \text{Giá vốn sau điều chỉnh} \rightarrow$ **Vị thế đang LỖ THỰC TẾ**.
* Điểm hòa vốn thực tế = **Giá vốn sau điều chỉnh**.

---

### Cách 2: Tính theo Dòng tiền thực tế (Cash In / Cash Out)
$$\text{Lãi / Lỗ ròng} = \Big(\text{Giá trị CK thị trường} + \text{Tiền mặt khả dụng} + \text{Tiền cổ tức chờ về} \times 0.95\Big) - \text{Tổng tiền vốn thực nạp mua ban đầu}$$

* $\text{Tiền cổ tức chờ về} \times 0.95$: Đã khấu trừ 5% thuế thu nhập cá nhân theo luật định.

---

## 4. CHECKLIST 4 BƯỚC XÁC MINH TRƯỚC KHI TRẢ LỜI LÃI/LỖ

Mỗi khi người dùng hỏi về lãi/lỗ hoặc chụp ảnh màn hình danh mục có cổ tức:

1. [ ] **Kiểm tra trạng thái Giá vốn:** Giá vốn trên bảng là Giá vốn GỐC ban đầu hay Giá vốn ĐÃ ĐIỀU CHỈNH sau ngày GDKHQ?
2. [ ] **Kiểm tra độ chênh lệch Giá:** $\Delta P = P_{\text{Thị trường}} - P_{\text{Giá vốn}}$.
   - Nếu $\Delta P < 0 \rightarrow$ Kết luận ngay: Vị thế đang **LỖ KỸ THUẬT VÀ LỖ THỰC TẾ**.
3. [ ] **Kiểm tra Tổng KL:** Tổng KL hiển thị đã bao gồm cổ phiếu thưởng / cổ tức cổ phiếu chờ về chưa? (Nếu đã bao gồm, không được nhân thêm một lần nữa).
4. [ ] **Giải thích minh bạch:** Làm rõ khoản "Tiền cổ tức chờ về" chỉ là tiền hoàn lại do bị trừ thị giá, không phải lợi nhuận phát sinh thêm ngoài biến động giá cổ phiếu.

---

## 5. CASE STUDY THỰC TẾ (ĐIỂN HÌNH VPS SMARTONE)

**Dữ liệu thực tế:**
- Mua 4.300 SSI, được thưởng 20% cổ tức cổ phiếu (+860 CP) $\rightarrow$ Tổng KL = 5.160 CP.
- Cổ tức tiền mặt: 1.000 đ/CP $\rightarrow$ Tiền chờ về: 4.300.000 đ.
- Giá vốn sau điều chỉnh: `24.421 đ`.
- Giá thị trường hiện tại: `21.500 đ`.

**Phân tích chuẩn xác:**
- Thị giá ($21.500$) < Giá vốn điều chỉnh ($24.421$) $\rightarrow$ Lỗ $2.921$ đ/CP.
- Tổng lỗ SSI = $5.160 \times (21.500 - 24.421) = \mathbf{-15.072.360 \text{ VNĐ}}$.
- **Kết luận:** Tài khoản đang **LỖ 15.072.360 đ (-11.96%)**. Khoản tiền cổ tức chờ về chỉ là tiền hoàn lại từ thị giá bị trừ, không biến vị thế này thành lãi.
