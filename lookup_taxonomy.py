"""
Vnstock Taxonomy Lookup Helper
Tra cứu chuẩn hóa tên cột & chỉ số báo cáo tài chính Vnstock
"""

import pandas as pd

TAXONOMY_FILE = "vnstock_taxonomy.csv"

def search_taxonomy(query: str, report_type: str = None) -> pd.DataFrame:
    """
    Tìm kiếm thông tin chỉ tiêu trong bộ từ điển Vnstock.
    
    Args:
        query (str): Từ khóa tìm kiếm (tên tiếng Việt, tên cột, hoặc Taxonomy ID).
        report_type (str, optional): 'balance_sheet', 'income_statement', 'cash_flow', 'ratio'.
    
    Returns:
        pd.DataFrame: Danh sách các chỉ tiêu phù hợp.
    """
    df = pd.read_csv(TAXONOMY_FILE)
    
    if report_type:
        df = df[df['Report Type'] == report_type]
        
    mask = (
        df['Item Name (VI)'].fillna('').str.contains(query, case=False) |
        df['Unified UI Column'].fillna('').str.contains(query, case=False) |
        df['Taxonomy ID (Long Format)'].fillna('').str.contains(query, case=False) |
        df['VCI Old Key'].fillna('').str.contains(query, case=False)
    )
    return df[mask][['Report Type', 'Taxonomy ID (Long Format)', 'Item Name (VI)', 'Unified UI Column']]

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "lợi nhuận"
    res = search_taxonomy(q)
    print(f"Kết quả tìm kiếm cho từ khóa: '{q}' ({len(res)} mục)")
    print(res.to_string(index=False))
