"""
Bộ lọc cổ phiếu ngành Ngân hàng có ROE > 15%
Sử dụng Vnstock API để lấy số liệu tài chính mới nhất
"""

import sys
import pandas as pd
from vnstock.api.financial import Finance
import warnings
warnings.filterwarnings("ignore")

# Đảm bảo console Windows in đúng tiếng Việt và icon emoji
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BANK_SYMBOLS = [
    "VCB", "BID", "CTG", "TCB", "MBB", "ACB", "VPB", 
    "HDB", "VIB", "STB", "LPB", "TPB", "MSB", "OCB", 
    "SHB", "SSB", "NAB", "EIB"
]

def get_bank_ratios(symbol):
    try:
        f = Finance(symbol=symbol, source="VCI")
        df = f.ratio(period="year", lang="vi")
        if df is None or df.empty:
            return None
        
        # Lấy cột cuối cùng chứa dữ liệu số
        val_cols = [c for c in df.columns if c not in ["item", "item_en", "item_id"]]
        
        def get_val(item_name):
            row = df[df["item"] == item_name]
            if row.empty:
                return 0.0
            vals = row[val_cols].values.flatten()
            # Lấy giá trị số hợp lệ cuối cùng
            valid_vals = [v for v in vals if isinstance(v, (int, float)) and pd.notna(v) and v != 0]
            if valid_vals:
                return float(valid_vals[-1])
            return 0.0

        roe = get_val("ROE (%)")
        roa = get_val("ROA (%)")
        pe = get_val("P/E")
        pb = get_val("P/B")
        market_cap = get_val("Vốn hóa") / 1e12 # nghìn tỷ
        nim = get_val("Biên lãi thuần")
        casa = get_val("Tỷ lệ CASA")
        npl = get_val("Nợ xấu (%)")
        
        # Chuẩn hóa về phần trăm (%) nếu giá trị ở dạng thập phân (< 1.0)
        if 0 < roe < 1.0:
            roe *= 100
        if 0 < roa < 1.0:
            roa *= 100
        if 0 < nim < 1.0:
            nim *= 100
        if 0 < casa < 1.0:
            casa *= 100
        if 0 < npl < 1.0:
            npl *= 100
            
        return {
            "Mã CP": symbol,
            "ROE (%)": round(roe, 2),
            "ROA (%)": round(roa, 2),
            "P/E": round(pe, 2),
            "P/B": round(pb, 2),
            "NIM (%)": round(nim, 2),
            "CASA (%)": round(casa, 2),
            "Nợ xấu (%)": round(npl, 2),
            "Vốn hóa (nghìn tỷ)": round(market_cap, 1)
        }
    except Exception as e:
        return None

def main():
    print("=" * 85)
    print("🔍 ĐANG PHÂN TÍCH & SÀNG LỌC CỔ PHIẾU NGÂN HÀNG (TIÊU CHÍ: ROE > 15%)")
    print("=" * 85)
    
    data = []
    for s in BANK_SYMBOLS:
        print(f"-> Đang tải dữ liệu {s}...")
        r = get_bank_ratios(s)
        if r:
            data.append(r)
            
    df_all = pd.DataFrame(data)
    
    if not df_all.empty:
        # Lọc ROE >= 15.0% và sắp xếp giảm dần theo ROE
        df_filtered = df_all[df_all["ROE (%)"] >= 15.0].sort_values(by="ROE (%)", ascending=False)
        
        print("\n" + "=" * 85)
        print(f"🏆 DANH SÁCH {len(df_filtered)} CỔ PHIẾU NGÂN HÀNG ĐẠT TIÊU CHÍ (ROE >= 15%)")
        print("=" * 85)
        print(df_filtered.to_string(index=False))
        
        print("\n" + "=" * 85)
        print("💡 ĐÁNH GIÁ & GỢI Ý ĐẦU TƯ:")
        print("=" * 85)
        top3 = df_filtered.head(3)
        for _, row in top3.iterrows():
            print(f"⭐ Mã {row['Mã CP']}:")
            print(f"   • Khả năng sinh lời: ROE = {row['ROE (%)']}%, ROA = {row['ROA (%)']}%")
            print(f"   • Định giá: P/B = {row['P/B']}, P/E = {row['P/E']}")
            print(f"   • Chất lượng tài sản: NIM = {row['NIM (%)']}%, CASA = {row['CASA (%)']}%, Tỷ lệ nợ xấu = {row['Nợ xấu (%)']}%\n")
        print("=" * 85)

if __name__ == "__main__":
    main()
