# Phần C — nguồn giá nào phục vụ cửa sổ nào (mạng thật, chỉ đọc)

Lệnh (cwd = cây làm việc; chạy 16/11/2026): `../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_280/dbg_C3.py; ../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_280/dbg_C2.py`

## `dbg_C3_out.txt`

```
chuoi nguon dau tien: {'ACB': 'entrade', 'VNINDEX': 'vndirect'}
ACB 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
FPT 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
HPG 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
PVS 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
SHS 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
BSR 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
VGI 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
ACV 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
MSR 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
OIL 180d:entrade 420d:entrade 800d:entrade 1095d:entrade 1583d:vndirect(bo entrade)
VNINDEX 180d:vndirect 420d:vndirect 800d:vndirect 1095d:vndirect 1583d:vndirect
```

## `dbg_C2_out.txt`

```
ACB narrow: entrade [] 156 wide: vndirect [('entrade', 'hai nến rơi vào cùng một ngày phiên')] 1208
   open so ngay lech: 46 / 156 max |d| 0.005000000000002558
   high so ngay lech: 45 / 156 max |d| 0.005000000000002558
   low so ngay lech: 48 / 156 max |d| 0.005000000000002558
   close so ngay lech: 49 / 156 max |d| 0.005000000000002558
   volume so ngay lech: 6 / 156 max |d| 19091.0
  mau: [{'time': Timestamp('2026-04-02 00:00:00'), 'close_n': 20.33, 'close_w': 20.334}, {'time': Timestamp('2026-07-24 00:00:00'), 'close_n': 22.5, 'close_w': 22.5}, {'time': Timestamp('2026-11-13 00:00:00'), 'close_n': 20.35, 'close_w': 20.35}]
PVS narrow: entrade [] 156 wide: vndirect [('entrade', 'hai nến rơi vào cùng một ngày phiên')] 1208
   open so ngay lech: 111 / 156 max |d| 0.005000000000002558
   high so ngay lech: 111 / 156 max |d| 0.005000000000002558
   low so ngay lech: 111 / 156 max |d| 0.005000000000002558
   close so ngay lech: 111 / 156 max |d| 0.005000000000002558
   volume so ngay lech: 156 / 156 max |d| 56194.0
  mau: [{'time': Timestamp('2026-04-02 00:00:00'), 'close_n': 33.5, 'close_w': 33.499}, {'time': Timestamp('2026-07-24 00:00:00'), 'close_n': 28.5, 'close_w': 28.499}, {'time': Timestamp('2026-11-13 00:00:00'), 'close_n': 28.7, 'close_w': 28.7}]
VNINDEX narrow: vndirect [] 157 wide: vndirect [] 1208
   open so ngay lech: 0 / 157 max |d| 0.0
   high so ngay lech: 0 / 157 max |d| 0.0
   low so ngay lech: 0 / 157 max |d| 0.0
   close so ngay lech: 0 / 157 max |d| 0.0
   volume so ngay lech: 0 / 157 max |d| 0.0
  mau: [{'time': Timestamp('2026-04-02 00:00:00'), 'close_n': 1694.82, 'close_w': 1694.82}, {'time': Timestamp('2026-07-24 00:00:00'), 'close_n': 1686.11, 'close_w': 1686.11}, {'time': Timestamp('2026-11-16 00:00:00'), 'close_n': 1743.27, 'close_w': 1743.27}]
```
