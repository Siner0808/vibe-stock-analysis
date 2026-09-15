"""Mức Fibonacci cho vùng mua, cắt lỗ và chốt lời — HÀM THUẦN, chỉ để HIỆN.

VÌ SAO CÓ FILE NÀY
──────────────────
Bảng "Kế hoạch vào lệnh" trên app hiện ghi **"Vùng giá mua đề xuất"** rồi in
ra đúng **giá đóng cửa phiên gần nhất** (`app.py`). Nhãn hứa một *vùng* và
một *đề xuất*; giá trị là dữ liệu thô. Cùng lớp với hai ô đã bị gỡ ngày
21/08/2026 vì *"hứa một thành phần không tồn tại"*.

Và chốt lời đang là **+20% cứng** (`analysis_agents.py`) — một hằng số không
liên quan gì tới cấu trúc giá của chính mã đó.

ĐIỀU PHẢI NÓI TRƯỚC, VÀ NÓI TO
──────────────────────────────
Fibonacci tính từ **chính chuỗi giá** mà sáu agent đang dùng. Kết luận đã đo
của dự án: rho ≈ 0, và *"thêm agent hoặc thêm tầng vào một hệ có rho ≈ 0 thì
không cải thiện được gì — nguyên nhân gốc là thiếu dữ liệu độc lập"*
(`CLAUDE.md`, `MO-XE-KIEN-TRUC.md`).

Nên module này **KHÔNG** hứa thêm lợi thế dự báo, và không được dùng để hứa.
Nó làm đúng một việc nhỏ hơn: thay một hằng số bằng một mức **suy từ cấu
trúc giá của chính mã đó**, tất định và tái lập được.

Nếu có ai đem nó vào đường sinh lệnh rồi thấy số đẹp lên — **quy tắc số 1**:
giả định đầu tiên là CÓ LỖI.

BA RÀNG BUỘC CẤU TRÚC
─────────────────────
1. **Không tự dò đỉnh–đáy.** Biên vùng lấy từ `pha_wyckoff.doc_pha()` —
   hàm thuần đã có, đã có test và đột biến canh. Viết bộ dò thứ hai là tạo
   ra hai định nghĩa "nền giá" rồi để chúng trôi khỏi nhau.
2. **Không đủ bằng chứng thì KHÔNG bịa vùng.** `doc_pha` trả *"chưa đủ bằng
   chứng"* cho khoảng một nửa rổ VN100. Ở đó module này nói KHÔNG CÓ, đúng
   tiền lệ của `mau_bang_gia`: *"không đọc được bảng giá thì không được nói
   trần/sàn"*.
3. **ĐƠN VỊ đi vào bằng đơn vị đi ra.** `he_so_gia` truyền thẳng cho
   `doc_pha`; module này không quy đổi gì thêm. Dự án đã trả giá cho chỗ
   nghìn-đồng gặp VNĐ nhiều lần.
"""
from __future__ import annotations

from dataclasses import dataclass

import pha_wyckoff

#: Vùng mua là khoảng giữa hai mức thoái lui KINH ĐIỂN, đo TỪ TRẦN xuống.
#: Đây là một VÙNG (hai số), không phải một điểm — đó là toàn bộ lý do có
#: file này.
MUC_VUNG = (0.500, 0.618)

#: Mức mở rộng cho mục tiêu, đo TỪ SÀN lên. `1.0` chính là trần, nên hai
#: mức này luôn nằm TRÊN trần.
MUC_MO_RONG = (1.272, 1.618)

#: Biên rủi ro mỗi lệnh, đo từ ĐỈNH vùng mua xuống — ca xấu nhất, vì
#: đó là giá cao nhất người ta có thể mua trong vùng.
#:
#: KHÔNG phải con số của riêng file này: đây đúng là biên mà
#: `analysis_agents.py` đang kẹp SL theo ATR vào (`max(0.04, min(0.065,
#: …))`). Giữ chung một biên thì rủi ro mỗi lệnh nằm trong dải đã chọn, và
#: hai con SL so sánh được với nhau.
#:
#: Hai chỗ này bị khoá lại bởi `tests/test_muc_fibonacci.py::
#: test_BIEN_SL_phai_KHOP_nguong_ATR_trong_analysis_agents`. Nó đọc bằng
#: REGEX neo vào `sl_fraction =`, không phải AST: hai số ấy là literal
#: nằm trong một biểu thức, không phải hằng số có tên. Sửa một bên mà
#: quên bên kia thì đỏ.
SL_HEP_NHAT = 0.040
SL_RONG_NHAT = 0.065


@dataclass(frozen=True)
class MucFibonacci:
    """Kết quả. `vung_mua=None` nghĩa là KHÔNG kết luận được — xem `ly_do`."""

    ly_do: str
    san: float | None
    tran: float | None
    vung_mua: tuple[float, float] | None
    sl: float | None
    sl_pct: float | None
    vua_ngan_sach: bool
    tp1: float | None
    tp2: float | None
    vi_tri_gia: str
    nhan: str

    @property
    def ket_luan_duoc(self) -> bool:
        return self.vung_mua is not None


def _khong(ly_do: str) -> MucFibonacci:
    """Không kết luận được — và nói rõ vì sao, chứ không trả về một vùng
    trung tính. Một vùng bịa nguy hiểm hơn một ô trống."""
    return MucFibonacci(
        ly_do=ly_do, san=None, tran=None, vung_mua=None,
        sl=None, sl_pct=None, vua_ngan_sach=False, tp1=None, tp2=None,
        vi_tri_gia="KHÔNG XÁC ĐỊNH",
        nhan=f"Chưa đủ bằng chứng — {ly_do}")


def _vi_tri(gia: float, thap: float, cao: float) -> str:
    if gia < thap:
        return "DƯỚI VÙNG"
    if gia > cao:
        return "TRÊN VÙNG"
    return "TRONG VÙNG"


def doc_muc(df, he_so_gia: float = 1.0) -> MucFibonacci:
    """Đọc mức Fibonacci từ bảng nến ngày (tăng dần theo thời gian).

    Hàm THUẦN: cùng một bảng vào thì cùng một kết quả ra, không đọc file
    trạng thái, không gọi mạng, không nhìn quá dòng cuối của `df`. Bất biến
    1 và 2 được giữ bằng cấu trúc, không bằng kỷ luật — y như `pha_wyckoff`.
    """
    pha = pha_wyckoff.doc_pha(df, he_so_gia)
    if not pha.ket_luan_duoc:
        return _khong(pha.nhan_day)
    if pha.san is None or pha.tran is None:
        return _khong("đọc được pha nhưng thiếu biên vùng")

    san, tran = float(pha.san), float(pha.tran)
    bien = tran - san
    if bien <= 0:
        return _khong(f"biên vùng không dương (sàn {san}, trần {tran})")

    thap = tran - MUC_VUNG[1] * bien      # 0,618 — đáy vùng mua
    cao = tran - MUC_VUNG[0] * bien       # 0,500 — đỉnh vùng mua

    # ── SL, và một mâu thuẫn KHÔNG giấu được ────────────────────────
    #
    # SL đặt DƯỚI SÀN: thủng sàn là cấu trúc bị phủ định, không phải nhiễu.
    # Nhưng một nền RỘNG thì không thể vừa "SL dưới cấu trúc" vừa "rủi ro
    # mỗi lệnh ≤ 6,5%" — hai điều kiện ấy đánh nhau, và bản nháp đầu của
    # file này kẹp bừa cho ra một con số, khiến SL rơi VÀO GIỮA vùng mua.
    # Một phép kiểm tham số bắt được ngay ở lượt chạy đầu.
    #
    # Lời giải không phải kẹp cho ra số, mà là NÓI RA: mức vẫn hiện, kèm
    # cờ `vua_ngan_sach=False`. Refuse-or-flag, đừng bịa.
    #
    # Sàn 4%: đừng đặt stop chặt hơn nhiễu thường ngày. Đo từ ĐỈNH vùng
    # mua vì đó là ca xấu nhất — mua ở giá cao nhất trong vùng.
    sl = min(san, cao * (1.0 - SL_HEP_NHAT))
    rui_ro = (cao - sl) / cao if cao > 0 else 0.0
    vua = SL_HEP_NHAT <= rui_ro <= SL_RONG_NHAT

    tp1 = san + MUC_MO_RONG[0] * bien
    tp2 = san + MUC_MO_RONG[1] * bien

    gia_cuoi = float(df["close"].iloc[-1]) * he_so_gia
    vi_tri = _vi_tri(gia_cuoi, thap, cao)

    # KHONG lam tron moc gia o day. Nguon vnstock tra NGHIN DONG (FPT =
    # 71,2) va nhieu ma co gia quanh 21,19 — lam tron ve 0 chu so o tang
    # TINH la pha mat gan 1% ngay trong phep tinh. Lam tron la viec cua
    # tang HIEN. Ban nhap dau lam tron o day va hai phep kiem bat duoc:
    # don vi khong nhan dung 1.000, va sl_pct lech khoi chinh cong thuc
    # cua no.
    return MucFibonacci(
        ly_do="",
        san=san, tran=tran,
        vung_mua=(thap, cao),
        sl=sl, sl_pct=round(rui_ro * 100, 1), vua_ngan_sach=vua,
        tp1=tp1, tp2=tp2,
        vi_tri_gia=vi_tri,
        nhan=(f"Nền {pha.so_phien_nen} phiên · sàn {san:,.0f} – trần "
              f"{tran:,.0f} · giá đang {vi_tri.lower()}"
              + ("" if vua else
                 f" · ⚠️ rủi ro {rui_ro * 100:.1f}% VƯỢT biên "
                 f"{SL_RONG_NHAT * 100:.1f}% — nền quá rộng, "
                 f"setup KHÔNG vừa ngân sách rủi ro")))
