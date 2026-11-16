# Phần D — gói tin trước/sau khi bỏ investing.com (3 mã × 2 vòng xen kẽ, mạng thật)

Lệnh (cwd = cây làm việc; chạy 16/11/2026): `../vibe_logs_280/so_goi_tin_280.py (đọc goi_{cu,moi}_{1,2}.json do do_goi_tin_280.py ghi)`

## `so_goi_tin_280.out`

```
vong 1: sha256 news_collectors cu b6edd0f3e09b moi d5b243bcf1f1
  HPG: total 192->192  news_score 49.8->49.8  sentiment -0.31->-0.31  Investing.com cu 0 moi 0  nguon khac nhau: {}
  ACB: total 192->192  news_score 50.1->50.1  sentiment 0.13->0.13  Investing.com cu 0 moi 0  nguon khac nhau: {}
  PVS: total 192->192  news_score 49.8->49.8  sentiment -0.31->-0.31  Investing.com cu 0 moi 0  nguon khac nhau: {}
vong 2: sha256 news_collectors cu b6edd0f3e09b moi d5b243bcf1f1
  HPG: total 192->192  news_score 49.8->49.8  sentiment -0.31->-0.31  Investing.com cu 0 moi 0  nguon khac nhau: {}
  ACB: total 192->192  news_score 50.1->50.1  sentiment 0.13->0.13  Investing.com cu 0 moi 0  nguon khac nhau: {}
  PVS: total 192->192  news_score 49.8->49.8  sentiment -0.31->-0.31  Investing.com cu 0 moi 0  nguon khac nhau: {}
giay HPG (lan dau, tai lanh): {'cu_1': 4.8, 'cu_2': 5.45, 'moi_1': 3.01, 'moi_2': 3.08}
```

## `goi_cu_1.out`

```
[cu_1] HPG: 4.8s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
[cu_1] ACB: 0.9s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=0.13 news_score=50.1
[cu_1] PVS: 1.1s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
```

## `goi_moi_1.out`

```
[moi_1] HPG: 3.0s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
[moi_1] ACB: 0.7s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=0.13 news_score=50.1
[moi_1] PVS: 0.6s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
```

## `goi_cu_2.out`

```
[cu_2] HPG: 5.5s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
[cu_2] ACB: 0.6s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=0.13 news_score=50.1
[cu_2] PVS: 0.6s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
```

## `goi_moi_2.out`

```
[moi_2] HPG: 3.1s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
[moi_2] ACB: 0.6s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=0.13 news_score=50.1
[moi_2] PVS: 0.6s total=192 nhom={'domestic': 68, 'international': 40, 'macro': 12, 'sector': 72} sentiment=-0.31 news_score=49.8
```
