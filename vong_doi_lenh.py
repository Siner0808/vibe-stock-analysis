"""
vong_doi_lenh.py
──────────────────────────────────────────────────────────────────────
Vòng đời một lệnh: đặt → khớp một phần → khớp đủ / huỷ / từ chối.

VÌ SAO CẦN
──────────
Sổ lệnh giấy hiện coi mỗi lệnh là khớp TOÀN BỘ ngay tại giá mong muốn. Đó
là giả định thầm lặng và nó luôn nghiêng về phía làm kết quả đẹp lên:

  - Lệnh 500.000 cổ phiếu vào một nến chỉ giao dịch 90.000 cổ phiếu thì
    không thể khớp đủ. Sổ hiện tại vẫn ghi khớp đủ.
  - Lệnh đặt ngoài biên độ ±7% bị sàn TỪ CHỐI, không phải khớp.
  - Lệnh lẻ dưới 100 cổ phiếu không đặt được trên HOSE.

Module này là máy trạng thái thuần, KHÔNG đụng vào paper_trading.py — file
đó đang khoá hai bất biến quan trọng và không nên rẽ nhánh vì việc này.

BIÊN ĐỘ VÀ THANH KHOẢN
──────────────────────
  Biên độ HOSE      ±7% quanh giá tham chiếu
  Lô chẵn           100 cổ phiếu
  Trần khớp mỗi nến TY_LE_KHOP_TOI_DA của khối lượng nến

Tỷ lệ khớp tối đa là GIẢ ĐỊNH, không phải số đo: thực tế phụ thuộc mình
đứng ở đâu trong sổ lệnh. Mặc định 10% — nghĩa là không bao giờ giả định
mình lấy được quá một phần mười thanh khoản của nến. Con số này chưa ai
kiểm định trên thị trường Việt Nam; đổi nó thì kết quả đổi theo.

Xem NGUYEN-TAC-DO-LUONG.md và truot_gia.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from truot_gia import BAN, MUA, khoi_luong_hop_le, truot_gia

# Trạng thái
MOI = "MOI"                     # đã đặt, chưa khớp gì
KHOP_MOT_PHAN = "KHOP_MOT_PHAN"
KHOP_DU = "KHOP_DU"
HUY = "HUY"
TU_CHOI = "TU_CHOI"

BIEN_DO = 0.07                  # ±7% HOSE
TY_LE_KHOP_TOI_DA = 0.10        # giả định: tối đa 10% khối lượng nến
SO_NEN_CHO_TOI_DA = 9           # hết một phiên không khớp đủ thì huỷ phần dư


class LenhError(ValueError):
    """Lệnh không hợp lệ — ném ngay khi đặt, không để nó đi tiếp."""


@dataclass
class Lenh:
    ma: str
    huong: str
    khoi_luong: int
    gia_muc_tieu: float
    gia_tham_chieu: float
    san: str = "HOSE"

    trang_thai: str = MOI
    da_khop: int = 0
    tien_da_khop: float = 0.0        # tổng giá trị đã khớp, để tính giá bình quân
    so_nen_da_cho: int = 0
    ly_do: str = ""
    lan_khop: list[dict] = field(default_factory=list)

    # ── Số liệu dẫn xuất ─────────────────────────────────────────────
    @property
    def con_lai(self) -> int:
        return self.khoi_luong - self.da_khop

    @property
    def gia_binh_quan(self) -> float | None:
        """Giá khớp bình quân gia quyền. None khi chưa khớp gì — KHÔNG trả 0,
        vì 0 sẽ lẫn với một mức giá thật ở mọi phép tính phía sau."""
        return self.tien_da_khop / self.da_khop if self.da_khop else None

    @property
    def xong(self) -> bool:
        return self.trang_thai in (KHOP_DU, HUY, TU_CHOI)

    def gioi_han_gia(self) -> tuple[float, float]:
        """Trần và sàn theo biên độ quanh giá tham chiếu."""
        return (self.gia_tham_chieu * (1 - BIEN_DO),
                self.gia_tham_chieu * (1 + BIEN_DO))


def dat_lenh(ma: str, huong: str, khoi_luong: int, gia_muc_tieu: float,
             gia_tham_chieu: float, san: str = "HOSE") -> Lenh:
    """Kiểm tra rồi tạo lệnh. Lệnh không hợp lệ bị TỪ CHỐI ngay, kèm lý do.

    Từ chối ở đây thay vì ném ngoại lệ với hai lỗi cuối, vì "sàn từ chối
    lệnh" là một kết cục có thật của vòng đời, cần ghi vào sổ chứ không
    phải sự cố lập trình.
    """
    if huong not in (MUA, BAN):
        raise LenhError(f"huong phải là {MUA!r} hoặc {BAN!r}, nhận {huong!r}")
    if gia_tham_chieu <= 0:
        raise LenhError(f"giá tham chiếu phải dương, nhận {gia_tham_chieu}")

    kl = khoi_luong_hop_le(khoi_luong)
    lenh = Lenh(ma=ma.upper(), huong=huong, khoi_luong=kl,
                gia_muc_tieu=float(gia_muc_tieu),
                gia_tham_chieu=float(gia_tham_chieu), san=san)

    if kl == 0:
        lenh.trang_thai = TU_CHOI
        lenh.ly_do = (f"khối lượng {khoi_luong} nhỏ hơn một lô chẵn (100) — "
                      f"HOSE không nhận lệnh lẻ")
        return lenh

    san_gia, tran_gia = lenh.gioi_han_gia()
    if not (san_gia <= gia_muc_tieu <= tran_gia):
        lenh.trang_thai = TU_CHOI
        lenh.ly_do = (f"giá {gia_muc_tieu:,.0f} ngoài biên độ ±{BIEN_DO:.0%} "
                      f"[{san_gia:,.0f} ; {tran_gia:,.0f}]")
    return lenh


def khop_trong_nen(lenh: Lenh, nen: dict,
                   ty_le_khop_toi_da: float = TY_LE_KHOP_TOI_DA,
                   he_so_tac_dong: float = 1.0) -> dict:
    """Cho lệnh gặp một nến. Khớp được bao nhiêu thì khớp, phần dư chờ tiếp.

    Trả bản ghi lần khớp này. Lệnh đã xong thì không làm gì thêm.
    """
    if lenh.xong:
        return {"khop": 0, "ly_do": f"lệnh đã {lenh.trang_thai}"}

    lenh.so_nen_da_cho += 1

    # Giá phải nằm trong khoảng nến mới khớp được. Lệnh mua ở giá thấp hơn
    # đáy nến thì cả phiên đó không ai bán cho mình.
    thap, cao = float(nen["low"]), float(nen["high"])
    voi_toi = (lenh.gia_muc_tieu >= thap) if lenh.huong == MUA else (lenh.gia_muc_tieu <= cao)
    if not voi_toi:
        ban_ghi = {"khop": 0, "ly_do": "giá đặt không với tới khoảng giá của nến"}
        lenh.lan_khop.append(ban_ghi)
        _het_kien_nhan(lenh)
        return ban_ghi

    kl_nen = float(nen.get("volume") or 0)
    tran_khop = khoi_luong_hop_le(int(kl_nen * ty_le_khop_toi_da))
    khop = min(lenh.con_lai, tran_khop)

    if khop <= 0:
        ban_ghi = {"khop": 0,
                   "ly_do": f"thanh khoản nến chỉ cho khớp {tran_khop} CP"}
        lenh.lan_khop.append(ban_ghi)
        _het_kien_nhan(lenh)
        return ban_ghi

    t = truot_gia(lenh.gia_muc_tieu, lenh.huong, nen, khop,
                  lenh.san, he_so_tac_dong)
    lenh.da_khop += khop
    lenh.tien_da_khop += khop * t["gia_khop"]
    lenh.trang_thai = KHOP_DU if lenh.con_lai == 0 else KHOP_MOT_PHAN

    ban_ghi = {"khop": khop, "gia_khop": t["gia_khop"],
               "truot_vnd": t["truot_vnd"], "truot_pct": t["truot_pct"],
               "ty_trong_kl": t["ty_trong_kl"], "ly_do": "OK"}
    lenh.lan_khop.append(ban_ghi)
    _het_kien_nhan(lenh)
    return ban_ghi


def _het_kien_nhan(lenh: Lenh) -> None:
    """Hết phiên mà chưa khớp đủ thì huỷ phần dư.

    Lệnh treo vô hạn là thứ không tồn tại: cuối phiên sàn xoá hết lệnh chưa
    khớp. Không mô hình hoá việc đó thì sổ sẽ có những lệnh 'sắp khớp' tồn
    tại mãi mãi.
    """
    if lenh.xong or lenh.so_nen_da_cho < SO_NEN_CHO_TOI_DA:
        return
    lenh.trang_thai = HUY
    lenh.ly_do = (f"hết {SO_NEN_CHO_TOI_DA} nến chờ, huỷ phần dư "
                  f"{lenh.con_lai}/{lenh.khoi_luong} CP")


def doi_soat(lenh: Lenh) -> dict:
    """Đối soát ý định với thực tế. Đây là phép đo, không phải báo cáo đẹp.

    `lech_pct` là chênh lệch giữa giá mình muốn và giá bình quân thật sự
    khớp — con số mà sổ lệnh hiện tại luôn coi bằng 0.
    """
    tt = {
        "ma": lenh.ma, "huong": lenh.huong, "trang_thai": lenh.trang_thai,
        "muon_khop": lenh.khoi_luong, "da_khop": lenh.da_khop,
        "ty_le_khop": (lenh.da_khop / lenh.khoi_luong) if lenh.khoi_luong else 0.0,
        "gia_muc_tieu": lenh.gia_muc_tieu,
        "gia_binh_quan": lenh.gia_binh_quan,
        "so_lan_khop": sum(1 for x in lenh.lan_khop if x.get("khop", 0) > 0),
        "so_nen_da_cho": lenh.so_nen_da_cho,
        "ly_do": lenh.ly_do,
    }
    if lenh.gia_binh_quan is None:
        tt["lech_vnd"] = None
        tt["lech_pct"] = None
    else:
        lech = abs(lenh.gia_binh_quan - lenh.gia_muc_tieu)
        tt["lech_vnd"] = lech
        tt["lech_pct"] = 100.0 * lech / lenh.gia_muc_tieu
    return tt
