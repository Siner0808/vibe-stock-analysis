"""mau_bang_gia.py — năm màu bảng giá Việt Nam, và điều kiện để được nói "TRẦN".

Bảng giá Việt Nam dùng năm màu, không phải hai:

    tím       giá TRẦN     — kịch biên độ trên
    xanh lá   TĂNG         — trên tham chiếu, chưa trần
    vàng cam  THAM CHIẾU   — đúng bằng tham chiếu
    đỏ        GIẢM         — dưới tham chiếu, chưa sàn
    xanh lam  giá SÀN      — kịch biên độ dưới

VÌ SAO KHÔNG TỰ TÍNH TRẦN/SÀN
─────────────────────────────
Cách rẻ tiền là `pct >= 6.9` thì gọi là trần. Nó SAI, và sai theo kiểu êm
ái nhất: đúng phần lớn thời gian nên không ai kiểm lại.

  • Biên độ khác nhau theo sàn (HOSE 7%, HNX 10%, UPCOM 15%) và khác nữa
    ở phiên chào sàn hoặc phiên giao dịch lại sau đình chỉ.
  • Giá trần là `tham_chiếu × (1 + biên)` LÀM TRÒN XUỐNG theo bước giá,
    mà bước giá lại phụ thuộc mức giá. SSI 21/08/2026: 19.400 × 1,07 =
    20.758 → làm tròn xuống bước 50 → 20.750, tức +6,96% chứ không phải 7%.
  • Tham chiếu KHÔNG phải giá đóng cửa phiên trước vào ngày giao dịch
    không hưởng quyền. Chuỗi giá lịch sử đã điều chỉnh hồi tố, nên lấy
    `close.iloc[-2]` làm tham chiếu là sai đúng vào những ngày dễ nhầm nhất.

Sở giao dịch công bố sẵn cả ba con số. `Trading().price_board()` trả
`listing/ceiling`, `listing/floor`, `listing/ref_price`. Đọc số thật rẻ hơn
và đúng hơn suy lại luật.

HỆ QUẢ ĐÃ CHỌN: KHÔNG CÓ BẢNG GIÁ THÌ KHÔNG ĐƯỢC NÓI TRẦN/SÀN
──────────────────────────────────────────────────────────────
Không đọc được bảng giá, hoặc bảng giá thuộc phiên khác với nến đang hiện,
thì hàm này tụt xuống ba màu (tăng / tham chiếu / giảm) so với giá đóng cửa
phiên trước. Nó KHÔNG đoán trần. Mất một màu tím còn hơn tô tím một mã
không hề trần — người xem không có cách nào phát hiện màu sai.

Điều kiện phủ định: giá đóng cửa của một phiên KHÔNG THỂ nằm ngoài biên độ
của chính phiên đó. Nằm ngoài nghĩa là biên độ nhận được thuộc phiên khác;
khi đó biên độ bị vứt bỏ chứ không được dùng.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Giá trên bảng tính bằng ĐỒNG và luôn là bội của bước giá (nhỏ nhất 10đ),
#: còn giá từ nến là float sau khi nhân hệ số đơn vị (20.75 × 1000 =
#: 20750.000000000004). Nửa đồng đủ để so bằng mà không bao giờ gộp nhầm
#: hai mức giá khác nhau.
DUNG_SAI = 0.5

#: VN-INDEX yết hai chữ số thập phân, nên nửa đơn vị nhỏ nhất là 0,005 điểm.
DUNG_SAI_CHI_SO = 0.005

TRAN = "tran"
TANG = "tang"
THAM_CHIEU = "tham_chieu"
GIAM = "giam"
SAN = "san"
KHONG_BIET = "khong_biet"

_NHAN = {
    TRAN: "TRẦN",
    TANG: "TĂNG",
    THAM_CHIEU: "THAM CHIẾU",
    GIAM: "GIẢM",
    SAN: "SÀN",
    KHONG_BIET: "CHƯA BIẾT",
}

#: Lớp CSS tương ứng, định nghĩa trong `app.py`. Giữ cùng một tiền tố `bg-`
#: để tìm được cả hai đầu bằng một lần grep.
_LOP = {
    TRAN: "bg-tran",
    TANG: "bg-tang",
    THAM_CHIEU: "bg-tc",
    GIAM: "bg-giam",
    SAN: "bg-san",
    KHONG_BIET: "bg-kb",
}

_MUI_TEN = {
    TRAN: "▲", TANG: "▲", THAM_CHIEU: "=", GIAM: "▼", SAN: "▼",
    KHONG_BIET: "",
}


@dataclass(frozen=True)
class MauGia:
    """Kết luận màu cho một phiên, kèm căn cứ đã dùng để kết luận."""

    ma: str
    nguon: str
    tham_chieu: float | None
    tran: float | None
    san: float | None
    thay_doi: float | None
    phan_tram: float | None
    ghi_chu: str = ""

    @property
    def nhan(self) -> str:
        return _NHAN[self.ma]

    @property
    def lop_css(self) -> str:
        return _LOP[self.ma]

    @property
    def mui_ten(self) -> str:
        return _MUI_TEN[self.ma]

    @property
    def biet_bien_do(self) -> bool:
        """Có biết biên độ của phiên này không — tức có quyền nói trần/sàn."""
        return self.tran is not None and self.san is not None


def mau_cho_phien(dong_cua: float | None,
                  dong_cua_truoc: float | None = None,
                  ngay_nen: str | None = None,
                  bang: dict | None = None,
                  dung_sai: float = DUNG_SAI) -> MauGia:
    """Màu bảng giá cho phiên đang hiển thị.

    `dong_cua`, `dong_cua_truoc` tính bằng ĐỒNG (đã nhân hệ số đơn vị).
    `ngay_nen` là ngày của cây nến đang hiện, dạng ``YYYY-MM-DD``.
    `bang` là dict do `doc_bang_gia()` trả về, hoặc None.

    `dung_sai` là NỬA ĐƠN VỊ NHỎ NHẤT mà con số được yết. Giá cổ phiếu yết
    theo đồng nên 0,5đ; VN-INDEX yết hai chữ số thập phân nên 0,005 điểm.
    Dùng nhầm dung sai của giá cho chỉ số sẽ nuốt mọi phiên đổi dưới nửa
    điểm thành "tham chiếu".

    Bảng giá chỉ được dùng khi CHỨNG MINH được nó thuộc đúng phiên này:
    có ngày ở cả hai phía và hai ngày bằng nhau. Thiếu một trong hai thì
    biên độ bị bỏ qua — không phải vì nó chắc chắn sai, mà vì không có cách
    nào biết nó đúng.
    """
    if dong_cua is None:
        return MauGia(KHONG_BIET, "không có giá đóng cửa",
                      None, None, None, None, None)

    tham_chieu = tran = san = None
    nguon = ""
    ghi_chu = ""

    if bang:
        ngay_bang = bang.get("ngay")
        thieu = [k for k in ("tham_chieu", "tran", "san")
                 if bang.get(k) is None]
        if thieu:
            ghi_chu = f"bảng giá thiếu {', '.join(thieu)}"
        elif not ngay_nen or not ngay_bang:
            ghi_chu = ("không đối chiếu được ngày giữa bảng giá và nến — "
                       "bỏ qua biên độ")
        elif str(ngay_bang)[:10] != str(ngay_nen)[:10]:
            ghi_chu = (f"bảng giá thuộc phiên {str(ngay_bang)[:10]}, nến "
                       f"thuộc phiên {str(ngay_nen)[:10]} — bỏ qua biên độ")
        elif (dong_cua > float(bang["tran"]) + dung_sai
                or dong_cua < float(bang["san"]) - dung_sai):
            # Điều kiện phủ định. Giá đóng cửa nằm ngoài biên độ của chính
            # phiên đó là chuyện KHÔNG XẢY RA trên sàn thật, nên dữ liệu
            # đang mâu thuẫn và biên độ này không dùng được.
            ghi_chu = (f"giá {dong_cua:,.0f} nằm ngoài biên độ "
                       f"{float(bang['san']):,.0f}–{float(bang['tran']):,.0f} "
                       f"— biên độ không thuộc phiên này, đã bỏ")
        else:
            tham_chieu = float(bang["tham_chieu"])
            tran = float(bang["tran"])
            san = float(bang["san"])
            nguon = (f"bảng giá {bang.get('san_gd') or 'sở'} "
                     f"phiên {str(ngay_bang)[:10]}")

    if tham_chieu is None:
        if dong_cua_truoc is None:
            return MauGia(KHONG_BIET, "không có tham chiếu",
                          None, None, None, None, None, ghi_chu)
        tham_chieu = float(dong_cua_truoc)
        nguon = "giá đóng cửa phiên trước (KHÔNG biết biên độ)"

    thay_doi = dong_cua - tham_chieu
    phan_tram = (thay_doi / tham_chieu * 100.0) if tham_chieu else 0.0

    if tran is not None and abs(dong_cua - tran) <= dung_sai:
        ma = TRAN
    elif san is not None and abs(dong_cua - san) <= dung_sai:
        ma = SAN
    elif thay_doi > dung_sai:
        ma = TANG
    elif thay_doi < -dung_sai:
        ma = GIAM
    else:
        ma = THAM_CHIEU

    return MauGia(ma, nguon, tham_chieu, tran, san, thay_doi, phan_tram,
                  ghi_chu)


def doc_bang_gia(ma: str) -> dict:
    """Đọc trần / sàn / tham chiếu THẬT của một mã từ bảng giá sở.

    Luôn trả dict, không bao giờ ném. Đọc được thì `loi` là None; không đọc
    được thì mọi con số là None và `loi` nói vì sao — giao diện phải phân
    biệt được "không trần" với "không biết có trần hay không".

    Đây là một cú gọi MẠNG. Nơi gọi tự lo cache.
    """
    trong = {"tham_chieu": None, "tran": None, "san": None, "ngay": None,
             "san_gd": None, "gia_khop": None, "loi": None}
    try:
        try:
            from vnstock_auth import ensure_api_key
            ensure_api_key()
        except Exception:
            pass

        from vnstock import Trading

        bang = Trading(source="vci").price_board([ma.upper()])
        if bang is None or len(bang) == 0:
            return {**trong, "loi": f"bảng giá không có mã {ma.upper()}"}

        # vnstock 4.x trả cột MultiIndex ("listing", "ceiling"); bản khác
        # trả cột phẳng. Ép về một dạng để phần dưới chỉ có một đường chạy.
        cot = {}
        for c in bang.columns:
            ten = "/".join(str(x) for x in c) if isinstance(c, tuple) else str(c)
            cot[ten] = c
        hang = bang.iloc[0]

        def _lay(*ten_cot):
            for t in ten_cot:
                if t in cot:
                    v = hang[cot[t]]
                    if v is not None and str(v) not in ("", "nan", "None"):
                        return v
            return None

        def _so(*ten_cot):
            v = _lay(*ten_cot)
            try:
                return None if v is None else float(v)
            except (TypeError, ValueError):
                return None

        ngay = _lay("listing/trading_date", "trading_date")
        ket = {
            "tham_chieu": _so("listing/ref_price", "match/reference_price",
                              "ref_price"),
            "tran": _so("listing/ceiling", "match/ceiling_price", "ceiling"),
            "san": _so("listing/floor", "match/floor_price", "floor"),
            "ngay": None if ngay is None else str(ngay)[:10],
            "san_gd": _lay("listing/exchange", "exchange"),
            "gia_khop": _so("match/match_price", "match_price"),
            "loi": None,
        }
        if ket["tham_chieu"] is None or ket["tran"] is None or ket["san"] is None:
            ket["loi"] = "bảng giá không có đủ trần/sàn/tham chiếu"
        return ket
    except Exception as e:
        return {**trong, "loi": f"{type(e).__name__}: {str(e)[:110]}"}
