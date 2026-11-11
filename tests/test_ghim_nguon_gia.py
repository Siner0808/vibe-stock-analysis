"""`fetch_one` phải GHIM được nguồn — hai nguồn là hai hệ số điều chỉnh (và hai định nghĩa khối lượng).

VÌ SAO CÓ FILE NÀY
──────────────────
Thời `vnstock`, `fetch_one` thử lần lượt `kbs → tcbs → vci → dnse` và lấy cái đầu tiên
có dữ liệu. Nó **không ghi lại nguồn nào đã trả lời**.

Lượt kéo `backtest/cache_2018/` ngày 11/09/2026: 123 mã từ `kbs`, **2 mã
từ `vci`** (HT1, TCH). Không vì `kbs` thiếu — hỏi lại sau đó, `kbs` trả
đủ 1.995 phiên cho cả hai. Một lần hỏng tạm thời, im lặng.

Và giá hai nguồn **không bằng nhau**:

    TCH  1988/1995 dong lech · ty le vci/kbs TB 0,9971
    HT1   116/1995 dong lech · TB 0,99998
    FPT  1499/1995 dong lech · TB 0,99966

Phần lớn là một hệ số gần đều nên triệt tiêu trong lợi nhuận, nhưng
không đều tuyệt đối. **Một rổ trộn hai nguồn là một rổ trộn hai hệ số**,
và không ai biết vì hàm im lặng.

Cùng họ lỗi 30: thứ gây hại không phải việc rơi nguồn, mà việc rơi nguồn
KHÔNG ĐƯỢC HỎI.

BƯỚC 267 (11/11/2026): `vnstock` bị hãng gỡ; nguồn nay là `nguon_gia_cong_khai`
(cổ phiếu: Entrade → VNDirect → VPS; VN-Index: VNDirect → iBoard → VPS). Nguyên tắc giữ
nguyên — thêm một lý do: các nguồn công khai khác nhau cả ở KHỐI LƯỢNG (iBoard cộng khối lượng
thoả thuận ở HNX/UPCoM: SHS 29/02/2024 37.000.850 so với 27.899.376). Test dưới đây giả MẠNG
(`nguon_gia_cong_khai._http_json`), không giả `vnstock`.
"""
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import nguon_gia_cong_khai as ngk  # noqa: E402
from backtest import data as bt_data  # noqa: E402

HOST = {"entrade": "services.entrade.com.vn", "vndirect": "dchart-api.vndirect.com.vn",
        "vps": "histdatafeed.vps.com.vn", "iboard": "iboard-api.ssi.com.vn"}


def _phan_hoi(co_du_lieu: bool):
    """Phản hồi dạng UDF của một nguồn: 30 phiên TỔNG HỢP, hoặc `no_data`."""
    if not co_du_lieu:
        return {"s": "no_data"}
    t = [1_767_225_600 + 86400 * i for i in range(30)]        # 30 ngày liên tiếp từ 01/01/2026, 00:00 UTC
    c = [20.0 + 0.1 * i for i in range(30)]
    return {"t": t, "o": c, "h": [x + 0.2 for x in c], "l": [x - 0.2 for x in c], "c": c,
            "v": [1_000_000] * 30, "s": "ok"}


def _dung_mang_gia(monkeypatch, co_du_lieu: set[str]):
    """Mạng giả: chỉ các nguồn trong `co_du_lieu` có dữ liệu; ghi mọi nguồn được hỏi."""
    da_hoi: list[str] = []

    def http(url, accept="*/*"):
        ten = next(t for t, h in HOST.items() if h in url)
        da_hoi.append(ten)
        return _phan_hoi(ten in co_du_lieu)

    monkeypatch.setattr(ngk, "_http_json", http)
    monkeypatch.setattr(ngk, "NGHI_GIUA_LAN_GOI_GIAY", 0.0)
    return da_hoi


def test_MAC_DINH_di_dung_thu_tu_va_lay_cai_dau_co_du_lieu(monkeypatch):
    """Không truyền `nguon` thì thử đúng thứ tự chuỗi cổ phiếu, lấy nguồn đầu có dữ liệu."""
    da_hoi = _dung_mang_gia(monkeypatch, {"vndirect"})
    df = bt_data.fetch_one("TCH", "2026-01-01", "2026-01-30", pause=0.0)
    assert df is not None and not df.empty
    assert da_hoi == ["entrade", "vndirect"], da_hoi
    assert df.attrs["nguon"] == "vndirect"
    print(f"PASS  mặc định: hỏi {da_hoi} rồi dừng ở nguồn có dữ liệu")


def test_GHIM_mot_nguon_thi_KHONG_roi_sang_nguon_khac(monkeypatch):
    """Ghim `vps` mà `vps` hỏng thì phải trả None, KHÔNG âm thầm lấy `vndirect`.

    Đây là cả lý do tham số này tồn tại: thà không có dữ liệu còn hơn có
    dữ liệu từ một hệ số khác mà không ai biết.
    """
    da_hoi = _dung_mang_gia(monkeypatch, {"vndirect"})
    df = bt_data.fetch_one("TCH", "2026-01-01", "2026-01-30", nguon="vps", pause=0.0)
    assert df is None, "ghim vps mà vẫn rơi sang nguồn khác"
    assert da_hoi == ["vps"], da_hoi
    print("PASS  ghim một nguồn: chỉ hỏi nguồn ấy, hỏng thì trả None")


def test_GHIM_nguon_CO_du_lieu_thi_lay_duoc(monkeypatch):
    da_hoi = _dung_mang_gia(monkeypatch, {"vps", "vndirect"})
    df = bt_data.fetch_one("FPT", "2026-01-01", "2026-01-30", nguon="vps", pause=0.0)
    assert df is not None and not df.empty
    assert da_hoi == ["vps"], da_hoi
    print("PASS  ghim nguồn có dữ liệu: lấy đúng nguồn ấy, không hỏi nguồn nào khác")


def test_GHIM_mot_DANH_SACH_nguon(monkeypatch):
    """Cho phép một danh sách hẹp, vẫn chặn hơn mặc định ba nguồn."""
    da_hoi = _dung_mang_gia(monkeypatch, {"vps"})
    df = bt_data.fetch_one("X", "2026-01-01", "2026-01-30", nguon=("entrade", "vndirect"), pause=0.0)
    assert df is None
    assert da_hoi == ["entrade", "vndirect"], da_hoi
    print("PASS  ghim danh sách: chỉ hỏi trong danh sách ấy")


def test_GHIM_ten_nguon_cu_cua_vnstock_la_loi_thang(monkeypatch):
    """`kbs/tcbs/vci/dnse` không còn: ghim một tên cũ phải NỔ chứ không lặng lẽ thành 'mặc định'."""
    da_hoi = _dung_mang_gia(monkeypatch, {"entrade"})
    with pytest.raises(ValueError, match="kbs"):
        bt_data.fetch_one("FPT", "2026-01-01", "2026-01-30", nguon="kbs")
    assert da_hoi == []


def test_DANH_SACH_MAC_DINH_van_la_nguon_da_do():
    """Đổi thứ tự nguồn là đổi hệ số điều chỉnh VÀ định nghĩa khối lượng của cả rổ — phải cố ý."""
    assert bt_data.NGUON_MAC_DINH_CO_PHIEU == ("entrade", "vndirect", "vps"), (
        f"thứ tự nguồn cổ phiếu đã đổi: {bt_data.NGUON_MAC_DINH_CO_PHIEU}\n"
        "Đổi thứ tự là đổi nguồn trả lời cho những mã mà nguồn đầu hỏng, "
        "tức đổi hệ số điều chỉnh và khối lượng của chúng. Đọc `docs/STATE.md` BƯỚC 267.")
    assert bt_data.NGUON_MAC_DINH_CHI_SO == ("vndirect", "iboard", "vps"), bt_data.NGUON_MAC_DINH_CHI_SO
    print(f"PASS  thứ tự nguồn mặc định: {bt_data.NGUON_MAC_DINH_CO_PHIEU} · {bt_data.NGUON_MAC_DINH_CHI_SO}")
