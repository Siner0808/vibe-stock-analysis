"""VẾ ĐỐI CHỨNG của ĐO 8 — chạy bằng MỘT TRÌNH THÔNG DỊCH KHÁC.

File này KHÔNG chạy trong môi trường của dự án, và đó là chủ đích.

VÌ SAO NÓ NẰM Ở ĐÂY, NGOÀI `tools/`
───────────────────────────────────
`tests/test_requirements.py` đòi mọi import trong `tools/*.py` phải có
trong `requirements.txt`, vì ba workflow đều chạy mã ở đó. File này import
`vectorbt`, và `vectorbt` **không được** vào `requirements.txt`:

  • Giấy phép **Apache-2.0 with Commons Clause** — GitHub trả
    `NOASSERTION` vì nó KHÔNG phải giấy phép nguồn mở OSI. Repo này công
    khai.
  • Đo 14/09/2026: cài nó vào `.venv` chính sẽ nâng **pandas 2.3.3 →
    3.0.5** và **numpy 2.2.6 → 2.5.3**. Một bước nhảy major của pandas
    đổi số của cả dự án — đúng địa hạt quy tắc số 1.

Nên nó sống trong một venv RIÊNG và được gọi qua tiến trình con. Việc nó
nằm ngoài tập file CI quét **không phải cách lách gác** — nó được khai
tường minh ở `tests/test_doi_chung_ngoai_venv.py`, đúng lối
*không cấm, buộc nói ra* của `# bia-ok:`.

DỰNG LẠI VENV ẤY
────────────────
```
./.venv/Scripts/python.exe -m venv <thu-muc-NGOAI-repo>
<thu-muc>/Scripts/python.exe -m pip install vectorbt
```

NÓ TÍNH GÌ
──────────
Nhận một danh sách lệnh đã biết trước lãi/lỗ, rồi hỏi **vectorbt**:
*một tài khoản tiền mặt duy nhất, vốn cố định, không vay, cầm đúng những
lệnh ấy thì cuối kỳ còn bao nhiêu?*

Mỗi LỆNH thành một "tài sản" giả với chuỗi giá đi từ `1.0` lúc vào tới
`1+r` lúc ra. Cả rổ nằm trong MỘT nhóm với `cash_sharing=True`, nên chỉ
có một két tiền — đó chính là ràng buộc mà phép cộng dồn tuần tự của
`paper_metrics.compute()` không có.

**Phí và trượt giá TẮT HẲN.** Mô hình trượt giá của vectorbt là phần trăm
của giá; chi phí của dự án này do bước giá 50đ quyết định. Bật lên là so
hai mô hình chi phí, không phải so số học.
"""
import json
import sys


def tinh(lenh: list[dict], von_dau: float = 100.0) -> dict:
    """Giá trị cuối kỳ của MỘT tài khoản tiền mặt, do vectorbt tính.

    `lenh`: mỗi phần tử có `vao` · `ra` (chỉ số thanh, số nguyên),
    `size_pct` (% danh mục) và `ret_pct` (lãi/lỗ ròng %).
    """
    import numpy as np
    import pandas as pd
    import vectorbt as vbt

    if not lenh:
        return {"von_cuoi": von_dau, "loi_nhuan_pct": 0.0, "so_lenh": 0}

    n_thanh = max(l["ra"] for l in lenh) + 2
    cot = [f"L{i}" for i in range(len(lenh))]

    gia = pd.DataFrame(1.0, index=pd.RangeIndex(n_thanh), columns=cot)
    co = pd.DataFrame(np.nan, index=pd.RangeIndex(n_thanh), columns=cot)

    for i, l in enumerate(lenh):
        vao, ra = int(l["vao"]), int(l["ra"])
        # Giá đi TUYẾN TÍNH từ 1.0 tới 1+r, rồi đứng yên. Tuyến tính để
        # giá trị đánh dấu giữa chừng có nghĩa; phép so chỉ đọc CUỐI KỲ.
        dich = 1.0 + l["ret_pct"] / 100.0
        if ra > vao:
            gia.iloc[vao:ra + 1, i] = np.linspace(1.0, dich, ra - vao + 1)
        gia.iloc[ra:, i] = dich
        # Vào: nhắm tỷ trọng size_pct của TỔNG giá trị nhóm. Ra: về 0.
        co.iloc[vao, i] = l["size_pct"] / 100.0
        co.iloc[ra, i] = 0.0

    # `size_type` truyền VÔ HƯỚNG, không truyền bảng. Một bảng có NaN là
    # bảng FLOAT, và vectorbt tra giá trị enum trong một bảng số NGUYÊN —
    # `KeyError: 5.0`, đo được 14/09/2026. NaN trong `size` mới là cách
    # nói "thanh này không có lệnh".
    dm = vbt.Portfolio.from_orders(
        close=gia, size=co,
        size_type=vbt.portfolio.enums.SizeType.TargetPercent,
        direction=vbt.portfolio.enums.Direction.LongOnly,
        group_by=True, cash_sharing=True,     # MỘT két tiền cho cả rổ
        init_cash=von_dau,
        fees=0.0, fixed_fees=0.0, slippage=0.0,   # TẮT HẲN, xem docstring
        freq="1D",
    )
    cuoi = float(np.asarray(dm.value()).reshape(-1)[-1])
    return {"von_cuoi": cuoi,
            "loi_nhuan_pct": (cuoi / von_dau - 1.0) * 100.0,
            "so_lenh": len(lenh),
            "vectorbt": vbt.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__}


def main() -> int:
    """Đọc JSON ở stdin, in JSON ra stdout. Không đụng file nào của repo."""
    try:
        vao = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"loi": f"khong doc duoc dau vao: {e}"}))
        return 2
    try:
        ra = tinh(vao["lenh"], float(vao.get("von_dau", 100.0)))
    except Exception as e:
        # KHÔNG nuốt lỗi rồi trả một con số. Vế đối chứng im lặng hỏng là
        # thứ nguy hiểm nhất ở đây: nó biến phép so thành phép tự xác nhận.
        print(json.dumps({"loi": f"{type(e).__name__}: {e}"}))
        return 2
    print(json.dumps(ra))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
