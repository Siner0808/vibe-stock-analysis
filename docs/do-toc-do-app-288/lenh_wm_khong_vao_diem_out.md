# Đầu ra nguyên văn

Lệnh (20/11/2026, cwd = cây làm việc):

    grep -rn "khung_thoi_gian\|NGAY_LICH_CHO_KHUNG_THANG\|gop_nen\|nen_ngay_da_dong\|_nen_ba_khung" --include=*.py . | grep -v "^./tests/\|^./.venv\|^./khung_thoi_gian.py"

```
./app.py:38:import khung_thoi_gian as _kt
./app.py:1167:    ngay_rong = max(days_back, _NGAY_LICH_DOW, _kt.NGAY_LICH_CHO_KHUNG_THANG)
./app.py:1703:def _nen_ba_khung(ma, san, bay_gio):
./app.py:1708:    `load_stock_data_cat` cho đúng thứ `load_stock_data` từng cho. Cửa sổ xin là `NGAY_LICH_CHO_KHUNG_THANG`, suy từ
./app.py:1713:    tu = (bay_gio - timedelta(days=_kt.NGAY_LICH_CHO_KHUNG_THANG)
./app.py:1720:    return ({"D": _kt.nen_ngay_da_dong(d, bay_gio),
./app.py:1721:             "W": _kt.gop_nen(d, "W", bay_gio, tu_ngay=dau),
./app.py:1722:             "M": _kt.gop_nen(d, "M", bay_gio, tu_ngay=dau)},
./app.py:1813:        nen_vn, he_vn, loi = _nen_ba_khung("VNINDEX", "HOSE", bay_gio)
./app.py:1852:    _nen_ck, _he_so_ck, _loi_ck = _nen_ba_khung(symbol, exchange, end_date)
./app.py:1857:        key="khung_thoi_gian_chon", label_visibility="collapsed")
./ke_hoach_vao_lenh.py:103:#: MA của giá đóng cửa. Khớp `khung_thoi_gian.CHU_KY_MA_NGAN` (test giữ).
./tools/doi_chieu_gop_cua_so_288.py:65:    import khung_thoi_gian as kt
./tools/doi_chieu_gop_cua_so_288.py:91:    ngay_rong = max(NGAY_BIEU_DO, NGAY_QUET, kt.NGAY_LICH_CHO_KHUNG_THANG)
```
