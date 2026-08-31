"""
vn100_symbols.py
──────────────────────────────────────────────────────────────────────
Danh mục Theo dõi Tùy chỉnh (Custom Watchlist theo 16 Ngành Ngành hàng).
Thay thế toàn bộ rổ VN50 / VN100 theo yêu cầu người dùng.
"""

SECTOR_WATCHLIST = {
    "Dầu khí": ["BSR", "PVD", "PVS", "PLX", "OIL"],
    "Tài nguyên cơ bản": ["HPG", "HHP", "HSG", "NKG", "MSR"],
    "Hàng & Dịch vụ công nghiệp": ["VSC", "GEX", "PVT", "VTP"],
    "Thực phẩm & Đồ uống": ["VNM", "HAG", "MSN", "BAF", "NAF"],
    "Y tế": ["DHG", "DCL"],
    "Ngân hàng": ["STB", "VCB", "LPB", "BID", "CTG", "TCB", "HDB", "SHB", "MBB", "ACB"],
    "Bất động sản": ["NVL", "VHM", "KDH", "PDR", "DIG", "VRE", "VIC", "DXG", "NLG", "BCM"],
    "Công nghệ thông tin": ["FPT"],
    "Hóa chất": ["AAA", "DPM", "DCM", "GVR"],
    "Xây dựng & Vật liệu": ["CII", "HHV", "VCG", "GEL", "PC1"],
    "Ô tô": ["HAX", "HUT"],
    "Hàng cá nhân & Gia dụng": ["PNJ", "GIL"],
    "Bán lẻ": ["FRT", "MWG"],
    "Dịch vụ & Giải trí": ["VJC", "VPL", "HVN", "ACV"],
    "Điện, Nước & Khí đốt": ["POW", "GAS", "PLX"],
    "Dịch vụ tài chính": ["VIX", "SSI", "VCI", "HCM", "SHS", "VND", "MBS", "VCK"]
}

# Tạo danh sách các mã độc nhất (Unique symbols list)
CUSTOM_WATCHLIST_SYMBOLS = [
    # Dầu khí
    "BSR", "PVD", "PVS", "PLX", "OIL",
    # Tài nguyên cơ bản
    "HPG", "HHP", "HSG", "NKG", "MSR",
    # Hàng & Dịch vụ công nghiệp
    "VSC", "GEX", "PVT", "VTP",
    # Thực phẩm & Đồ uống
    "VNM", "HAG", "MSN", "BAF", "NAF",
    # Y tế
    "DHG", "DCL",
    # Ngân hàng
    "STB", "VCB", "LPB", "BID", "CTG", "TCB", "HDB", "SHB", "MBB", "ACB",
    # Bất động sản
    "NVL", "VHM", "KDH", "PDR", "DIG", "VRE", "VIC", "DXG", "NLG", "BCM",
    # Công nghệ thông tin
    "FPT",
    # Hóa chất
    "AAA", "DPM", "DCM", "GVR",
    # Xây dựng & Vật liệu
    "CII", "HHV", "VCG", "GEL", "PC1",
    # Ô tô
    "HAX", "HUT",
    # Hàng cá nhân & Gia dụng
    "PNJ", "GIL",
    # Bán lẻ
    "FRT", "MWG",
    # Dịch vụ & Giải trí
    "VJC", "VPL", "HVN", "ACV",
    # Điện, Nước & Khí đốt
    "POW", "GAS",
    # Dịch vụ tài chính
    "VIX", "SSI", "VCI", "HCM", "SHS", "VND", "MBS", "VCK"
]

# Alias để tương thích 100% với toàn bộ pipeline hiện có
VN100_SYMBOLS = CUSTOM_WATCHLIST_SYMBOLS
