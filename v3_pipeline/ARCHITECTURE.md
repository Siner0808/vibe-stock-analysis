# 🏗️ KIẾN TRÚC PIPELINE V3 - ANTIGRAVITY QUANT ENGINE

## Cấu trúc thư mục:
```
v3_pipeline/
├── layer0_data_quality.py      # TẦNG 0: Data Quality Gate
├── layer0_5_macro_filter.py    # TẦNG 0.5: Lọc Vĩ Mô & Xếp hạng RS
├── layer1_ingestion.py         # TẦNG 1: Thu thập đa khung D + W
├── layer2_wyckoff_engine.py    # TẦNG 2: Wyckoff Engine Đa Khung
├── layer3_debate_council.py    # TẦNG 3: Hội Đồng Phản Biện 3 Chiều
├── layer4_risk_sizing.py       # TẦNG 4: Rủi Ro & Position Sizing
├── layer5_learning.py          # TẦNG 5: Tự Học & Calibration
├── layer6_report.py            # TẦNG 6: Báo Cáo Luận Điểm → Telegram
└── run_pipeline.py             # ENTRY POINT: Chạy toàn bộ Pipeline
```
