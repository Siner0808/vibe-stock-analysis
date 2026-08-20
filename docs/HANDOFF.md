# HANDOFF — vibe_preview → Claude Code

**Ngày:** 19/08/2026 · **Từ:** phiên Cowork (audit + Phase 0/1A/1B/3A–3D/4)
**Nhánh:** `sua-chua/phase-0` · 6 commit · **chưa push, chưa merge vào `main`**
**Bộ test:** 204 → **218 passed, 0 failed**

Đọc file này trước. `CLAUDE.md` là luật chơi; `docs/STATE.md` là nhật ký chi
tiết từng Phase; file này là *bắt đầu từ đâu*.

---

## 0. BA LỆNH ĐẦU TIÊN — chạy trước khi làm bất cứ gì

```bash
pytest tests/ -q
# kỳ vọng: 218 passed. Nếu KHÁC 218 -> dừng lại, báo ngay.
# Mốc 218 đo trên bản sao Linux/Python 3.11. Chưa ai chạy trên máy này.

python -c "import toml; print(toml.__version__)"
# `toml` KHÔNG có trong requirements.txt. Thiếu nó thì phiên quét 09:10
# sẽ DỪNG (hành vi mới, đúng ý) thay vì âm thầm bỏ qua Google Sheets.
# Lỗi -> pip install toml

python run_daily.py
# Lượt chạy THẬT đầu tiên với vnstock live + secrets.toml thật. Chưa ai
# kiểm. Kỳ vọng: báo cáo phiên có >1 giá trị điểm (trước đây luôn là 50,0).
```

Ba lệnh trên là toàn bộ phần "chưa kiểm được" của phiên trước. Chúng không
sửa gì; chúng chỉ nói cho bạn biết bản sửa có sống được trên máy thật không.

---

## 1. HỆ THỐNG ĐANG Ở TRẠNG THÁI NÀO

- **14 ngày không mở được lệnh nào.** Không phải vì code hỏng — vì cổng
  VN-INDEX đọc `backtest/cache/VNINDEX.csv` **đóng băng ở 2026-08-07**, và
  `is_vni_bullish()` trả `False` cho **mọi ngày tương lai, vĩnh viễn** (đã
  chạy hàm thật để xác nhận: `is_vni_bullish('2030-01-01') = False`).
  Trong khi đó `market_filter.status()` vẫn báo `active: True`.
- Sổ lệnh: **113 lệnh** (112 đóng, 1 ACB đang mở), 12.564 quyết định.
  `total_net_pct = +14,24%` · WR 25,0% · KTC kỳ vọng **chứa 0**.
- `avg_capital_deployed_pct = 29%` nhưng **`peak = 208%`** → đòn bẩy ẩn.
- Đây là **Phase 2**, chưa động tới. Xem mục 3.

---

## 2. ĐÃ SỬA GÌ (6 commit)

| Commit | Nội dung | Gate |
|---|---|---|
| `6a54e90` | `run_session()` trả điểm THẬT; bỏ `s.get("score", 50.0)` | ✅ báo cáo có 5 giá trị điểm (52·53·59·63·64) thay vì 1 |
| `e70b5f6` | Gỡ 16 hằng số bịa khỏi `app.py`, đọc sổ qua `paper_metrics.compute()` | ✅ Playwright: HTTP 200, 0 traceback, text render sạch |
| `955a2ec` | `chan_bia_so_lieu.py --quet-repo` cho CI | ✅ 0 CHẶN · 35 cảnh báo |
| `a679a8b` | Gác sổ thật vào `__init__`; `push()` phát hiện mất dòng; commit stop ngay | ✅ 7 test viết trước, đều đỏ trước khi sửa |
| `aceade1` | `secrets.toml` có mặt mà không đọc được → nổ | ✅ |
| `3ce52fe` | Cập nhật `CLAUDE.md` + `NGUYEN-TAC-DO-LUONG.md` mục 7 | — |

**Ba con số trên giao diện, trước → sau:**

```
+636,11%  ->  +14,24%      (sổ thật, qua compute())
1.787 lệnh ->  113 lệnh
WR 61,2%  ->  25,0%
```

Cộng hai banner từng bị xoá trong hai commit UI ngày 18/08, nay hiện lại:
cảnh báo KTC chứa 0, và cảnh báo đòn bẩy 208%.

---

## 3. NĂM Ô ĐANG CHẶN — cần người dùng quyết, ĐỪNG tự chọn

Kế hoạch đầy đủ ở file `ke-hoach-sua-vibe-preview.md` (người dùng có bản
trong khung chat; nếu không thấy thì hỏi).

| # | Câu hỏi | Chặn Phase | Khuyến nghị của phiên trước |
|---|---|---|---|
| **C1** | Cache VN-INDEX quá hạn: cho lệnh qua, hay dừng phiên quét? | 2A | Dừng phiên quét (ngưỡng 3 phiên) |
| **C2** | Giữ hai nơi quét (máy + Actions) hay rút về một? | 3E | Một nơi |
| **C3** | App trên cloud: "chưa có dữ liệu" hay đọc Google Sheets? | 5 | Đã tạm làm "chưa có dữ liệu" ở 1B |
| **C4** | Bất biến 7 & 8: dựng lại walk-forward từ `025507c`, hay bỏ? | 5D | Dựng lại |
| **C5** | Ngưỡng mua: giữ 50,0 · về 62 · hay để trống? | 2 | **Để trống + dừng mở lệnh mới** |

> ### ⚠️ C5 là ô nguy hiểm nhất
> Ngay giây phút Phase 2 gỡ cổng VN-INDEX, `consider_entry()` sẽ chạy tới
> dòng so ngưỡng và **mở lệnh ở lượt quét kế tiếp**. Không có bước trung
> gian nào để xem lại.
>
> Ngưỡng 50,0 hiện tại là "QUÁN QUÂN TỐI ƯU" của lần thứ tư (+636,11%) —
> cực đại của 20 vòng chạy trên cùng dữ liệu, tức chính con số mà
> `NGUYEN-TAC-DO-LUONG.md` mục 7 đã tuyên bố vô hiệu. Và 20 vòng đó **không
> độc lập**: `_ANALYZE_CACHE`/`_ENGINE_CACHE` ở mức module, 8 luồng chung
> `sl_patterns`, chạy lại ra bảng khác.
>
> **Không gỡ cổng trước khi C5 có câu trả lời.**

---

## 4. BA RÀNG BUỘC KHI LÀM VIỆC — rút ra từ lỗi thật trong phiên trước

Một lượt kiểm chứng độc lập đã mắc cả ba lỗi này, và **cả ba đều nghiêng
cùng một hướng: làm hệ thống trông đỡ hỏng hơn thực tế.**

1. **Truy vấn ngày phải dùng `substr(signal_date,1,10)`, không so chuỗi.**
   Bảng `decisions` có hai định dạng (`' 00:00:00'` và `' 07:00:00'`).
   `'2026-08-17 07:00:00' <= '2026-08-17'` là `False` — lượt kiểm chứng
   trước mất **1.266/2.617 dòng** vì đúng lỗi này, rồi báo con số hụt ra
   như bằng chứng nghi ngờ bản audit.

2. **Cấm tự chế phép tính lợi nhuận. Chỉ gọi `paper_metrics.compute()`.**
   Lượt trước tự cộng dồn phần trăm từng lệnh và sinh ra `+133,47%` — gấp 9
   lần con số thật — bằng đúng cơ chế đã tạo ra bốn lần trước (bỏ qua tỷ
   trọng vốn, bất biến 4; bỏ qua lệnh chồng lấn, bất biến 7b).

3. **Claim về HÀNH VI của một hàm phải chứng minh bằng CHẠY hàm đó.**
   Lượt trước kết luận `market_filter` "đã được sửa" vì đọc thấy
   `_STATUS = {"active": False}` ở dòng khởi tạo. Chạy thật:
   `status()` trả `active: True` với cache cũ 12 ngày.

### Và một quy tắc nữa, rút ra từ chính phiên này

**Kiểm tĩnh chỉ bắt được thứ đã biết tên.** Grep và AST của hai bản audit
đều bỏ sót thẻ "Trạng thái hệ thống AI" trong `app.py` dán cứng
`39 Mẫu · ● SYNCED` — trong khi `sl_pattern_memory.json` có **6.327** mẫu.
Chỉ smoke test bằng trình duyệt mới lộ ra. Muốn tìm cái chưa biết thì phải
**render rồi đọc màn hình**, không chỉ grep.

---

## 5. CÒN NỢ — đã đo, chưa sửa, cố ý

### Việc chỉ người dùng làm được

- **`.github/workflows/kiem-dinh.yml` chưa vào repo.** File đã soạn xong
  (người dùng có bản trong khung chat) nhưng công cụ từ xa không ghi được
  file workflow. Cần đặt vào `.github/workflows/` rồi `git add`.
- **Branch protection.** Streamlit Cloud deploy theo push và **không nghe
  lệnh GitHub Actions** — workflow chỉ báo đỏ, không chặn được. Phải bật
  `Settings → Branches → Require status checks` → chọn `kiem-dinh`, và làm
  việc trên nhánh, chỉ merge khi xanh. Đây là thay đổi *thói quen*.
- **Dọn rác git:** `.git/*.lock` và `.git/_cu_*` (phiên trước chỉ đổi tên
  được, không xoá được qua cầu nối). Và chuyển `_phase0_snapshot.tar.gz`
  (2,9 MB, bản sao lưu bằng chứng) ra **ngoài** repo.

### Món nợ đã hiện rõ

- **35 cảnh báo** từ `--quet-repo`, mức CHẶN sạch:
  `chatbot_agent.py` 18 (cùng bệnh `.get("...score", 50)` với lỗi vừa sửa),
  `post_mortem_learning.py` 6, `debate_agents.py` 6,
  `master_agent.py` 1 (`momentum_norm = max(momentum_norm, 65.0)` — dòng đã
  biến momentum thành hàm của trend+volume).
- **`sl_pattern_memory.json`: 6.327 mẫu hình từ 100 mã**, rổ thật 71 mã, sổ
  thật 113 lệnh → toàn bộ là dư lượng seed/tối ưu in-sample. Với dung sai
  ±5 trên 3 chiều, xác suất khớp gần như 1 → **gần mọi tín hiệu bị trừ 12
  điểm** trên thang 100, trong khi ngưỡng mua là 50,0.
  Nghịch lý: `save_memory()` **không được gọi từ đâu cả**, nên file đóng
  băng ở 10/08 và bất biến 2 đang được giữ **nhờ tai nạn**. Thêm lại một
  dòng `engine.save_memory()` là quay về đúng lỗi 47-vs-59, và không test
  nào đỏ. Đây là **Phase 6**, làm cuối vì cần Gate 5A để đo.
- **`BCG` dừng ở 2025-10-08 — cache cũ 10 tháng**, vẫn được chấm điểm bình
  thường. Không có chốt độ tươi cho cache backtest. (BVH, SSB dừng 31/07;
  VCF dừng 06/08.)
- **`truot_gia.py` và `vong_doi_lenh.py` là module mồ côi** — mô hình hoá
  trượt giá, khớp một phần, biên độ ±7%, lô chẵn, T+2,5, có 29 test, và
  **chỉ được import bởi test của chính chúng**. Nối vào sẽ làm mọi kết quả
  xấu đi (đúng hướng) nhưng đổi ý nghĩa toàn bộ sổ lệnh cũ — việc riêng.
- **`walkforward_vn100.py` không còn là walk-forward** và `os.remove`
  `sl_pattern_memory.json` ngay khi khởi động. Người dùng đã quyết bỏ. Tài
  liệu đã sửa chỗ trỏ; **file vẫn còn trong repo** — chưa đổi tên/xoá.

### Cố ý KHÔNG sửa (ngoài phạm vi từng Phase)

`run_daily.py:136` hằng số `>= 50.0` trùng lặp `BUY_THRESHOLD` (hôm nay hai
giá trị bằng nhau nên sửa là suy đoán) · pill `● Sheets Synced` và
`LIVE DATA`/`LIVE SYNC` trong `app.py` (khẳng định trạng thái không kiểm
chứng — cùng họ với `status()`, thuộc Phase 2) · tab "Báo cáo 3 phiên" in
cùng một điểm cho cả ba khung giờ như thể ba phiên khác nhau.

---

## 6. THỨ TỰ ĐỀ XUẤT

1. Ba lệnh ở mục 0.
2. Đặt `kiem-dinh.yml` + bật branch protection.
3. Xin người dùng trả lời **C1–C5**.
4. **Phase 2** (cổng VN-INDEX + cổng chất lượng dữ liệu) — chỉ sau khi có
   C1 và C5. Lưu ý: mở cổng chất lượng dữ liệu nhiều khả năng làm hệ thống
   **chặn nhiều hơn**, không ít hơn — hiện `data_quality` bị đóng đinh
   `"OK"` cho **12.564/12.564** quyết định.
5. Phase 3E (cần C2) · Phase 5A/5B (không cần ô nào) · Phase 5D (cần C4).
6. Phase 6 cuối cùng.

**Một việc *không* nên làm:** thêm agent hoặc thêm tầng. `MO-XE-KIEN-TRUC.md`
đã đo rho = −0,019 và kết luận nguyên nhân gốc là thiếu dữ liệu độc lập.
Audit không tìm được gì phản bác — ngược lại, tìm thấy hai agent đang chạy
trên NaN (`if sma50 and sma200` với `nan` là truthy → `nan > nan` False →
trừ 2 điểm và ghi chuỗi "Bear Market" vào `signals` như quan sát được) và
một tầng học chạy trên dư lượng in-sample.

---

## 7. CÁCH LÀM VIỆC ĐÃ DÙNG — nên giữ

Mọi bản sửa trong 6 commit đều theo cùng một vòng:

```
viết test -> CHẠY, phải ĐỎ -> sửa tối thiểu -> test XANH
   -> pytest toàn bộ, không đỏ thêm -> smoke test thật -> commit
```

Bước "phải ĐỎ trước" không phải hình thức. Phase 0 đo được: **204 test xanh
mà không bắt được một CRITICAL nào** — cổng đóng băng 13 ngày, điểm báo cáo
là hằng số, giao diện công bố +636,11%. Sửa trước rồi viết test sau chỉ sinh
ra test thứ 205 cũng xanh và cũng vô dụng.

Hai lần trong phiên, quy trình này bắt được lỗi của chính người viết:
- bộ phát hiện mất dòng ở `push()` bản đầu so **mình `seq`** → không bắt
  được cả sự cố 14/08 lẫn test của chính nó (phải là `(seq, symbol,
  signal_date)`);
- bước CI "kiểm test chạy khi không có mạng" bản đầu dùng `subprocess.call`
  → tiến trình con là Python mới, patch không theo sang, **gác giả chạy
  xanh**. Đã chứng minh bằng cách cho tiến trình con `connect(pypi.org:443)`.
