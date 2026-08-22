"""pha_wyckoff.py — đọc pha Wyckoff từ nến ngày.

VÌ SAO CÓ FILE NÀY
──────────────────
Ô "Pha Wyckoff" trên giao diện từng hiển thị `Pha C — Wyckoff Spring` cho
mọi mã có điểm ≥ 60. Không có phân tích cấu trúc nào đứng sau nhãn đó — nó
chỉ là điểm số chia thành bốn khoảng, đội lốt một kết luận về hành vi dòng
tiền lớn. Ngày 21/08/2026 nhãn bị gỡ và thay bằng "Vùng điểm ≥ 60 (điểm
cuối, không phải pha Wyckoff)".

File này làm phần việc mà cái nhãn kia đã hứa: đọc tương quan giá–khối
lượng, dựng hai biên của vùng dao động, và gọi tên pha KHI CÓ BẰNG CHỨNG.

BA ĐIỀU KHIẾN MODULE NÀY KHÁC MỘT BỘ NHẬN DẠNG MẪU HÌNH THÔNG THƯỜNG
────────────────────────────────────────────────────────────────────
1. **"Chưa đủ bằng chứng" là một câu trả lời hợp lệ, và thường là câu
   đúng.** Pha B của tích luỹ và pha B của phân phối trông giống hệt nhau
   — đi ngang, chán, khối lượng thấp. Đoán bừa một hướng ở đó không phải
   phân tích, mà là bịa. Mọi nhánh không đủ bằng chứng đều trả về
   `pha=None` kèm lý do cụ thể, không trả về một pha "an toàn".

2. **Biên vùng được dựng từ phần nền, sự kiện được tìm ở phần sau.** Nếu
   lấy min/max trên toàn bộ đoạn rồi hỏi "có nến nào thủng sàn không" thì
   câu trả lời luôn là KHÔNG — chính cây thủng sâu nhất đã định nghĩa ra
   cái sàn. Vòng lặp logic đó sinh ra một bộ nhận dạng không bao giờ kêu,
   cùng họ với những phép kiểm báo xanh trên 0 mẫu ở dự án này. Nên đoạn
   sau cao trào bị cắt làm hai: `nền` (định nghĩa sàn/trần) và `gần đây`
   (tìm Spring/UTAD/SOS/SOW). Hai phần không giao nhau.

3. **Bằng chứng phản biện là bắt buộc.** `phan_bien` không bao giờ rỗng.
   Một kết luận không kèm điều kiện phủ định thì không kiểm chứng được,
   và thứ không kiểm chứng được thì không đo được.

GIỚI HẠN — ĐỌC TRƯỚC KHI TIN KẾT QUẢ
────────────────────────────────────
· Chỉ đọc MỘT khung thời gian (nến ngày của gói dữ liệu được đưa vào).
  Vùng tích luỹ trên khung ngày có thể chỉ là một nhịp chỉnh trong phân
  phối trên khung tuần. Module không biết điều đó.
· Không đối chiếu VN-INDEX. Cổ phiếu Việt Nam đồng pha với chỉ số rất
  cao, nên phần lớn mã chỉ đang phản chiếu thị trường.
· Biên độ HOSE ±7% làm cao trào bị trải ra vài phiên thay vì gói trong
  một cây nến biên độ rộng. Vì vậy cao trào ở đây đo bằng CỤM ba phiên,
  không đo bằng một nến.
· Thanh khoản thấp làm tín hiệu khối lượng nhiễu. Module không tự nâng
  ngưỡng nghi ngờ theo thanh khoản — người đọc phải tự trừ hao.

Kết quả module này KHÔNG tham gia chấm điểm giao dịch. Nó là một lớp đọc
cấu trúc để người xem hiểu bối cảnh; đưa nó vào công thức điểm là thay đổi
mọi con số lịch sử của sổ lệnh, và theo quy tắc số 1 của
`NGUYEN-TAC-DO-LUONG.md` thì một thay đổi như vậy phải được ĐO trước.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# ── Ngưỡng, đặt tên hết để không có số ma trong nhánh quyết định ──────
COT_BAT_BUOC = ("open", "high", "low", "close", "volume")

TOI_THIEU_NEN = 60          # dưới mức này thì chưa có gì để đọc
CUA_SO_CAU_TRUC = 120       # chỉ đọc cấu trúc ĐANG diễn ra, không đọc cả lịch sử
CUM_CAO_TRAO = 3            # cao trào đo bằng cụm 3 phiên (biên độ HOSE ±7%)
BOI_KL_CAO_TRAO = 1.8       # cụm phải nặng gấp ngần này lần nền mới gọi là cao trào
NHIP_AR = 10                # AR phải xuất hiện trong ngần này phiên sau cao trào
BIEN_AR_TOI_THIEU = 0.03    # AR phải đi được 3% mới coi là nhịp bật/sụt thật
TOI_THIEU_PHIEN_NEN = 15    # nền ngắn hơn thì hai biên chưa có nghĩa
TOI_DA_PHIEN_NEN = 60       # nền dài hơn thì min/max là cả con sóng, không phải vùng
CUA_SO_SU_KIEN = 10         # sự kiện phải nằm trong ngần này phiên mới là "hiện tại"
VI_TRI_DAY = 0.35           # dưới mức này của phạm vi 120 phiên là "vùng đáy"
VI_TRI_DINH = 0.65          # trên mức này là "vùng đỉnh"
BIEN_DO_VUNG_TOI_DA = 0.35  # rộng hơn thì đó là xu hướng, không phải vùng đi ngang
NGUONG_RA_VUNG = 0.02       # đóng cửa phải vượt biên 2% mới tính là ra khỏi vùng
PHIEN_XAC_NHAN_RA_VUNG = 3  # và phải giữ được ngần này phiên
BOI_KL_CAN_KIET = 0.8       # khối lượng dưới mức này so với nền là "cạn kiệt"
BOI_KL_MANH = 1.5           # trên mức này là "khối lượng lớn"
PHIEN_PHA_A = 30            # vùng non hơn ngần này phiên thì còn ở pha A
BIEN_TEST_LAI = 0.015       # Test coi là chạm lại đáy Spring nếu trong 1,5%

TANG, GIAM, TRUNG_TINH = "tang", "giam", "trung_tinh"

_CANH_PHAI = ("Cạnh phải của biểu đồ luôn mơ hồ — sơ đồ Wyckoff chỉ hiển "
              "nhiên khi nhìn lại.")


@dataclass(frozen=True)
class PhaWyckoff:
    """Kết quả đọc cấu trúc. `pha=None` nghĩa là KHÔNG kết luận được."""

    pha: str | None
    cau_truc: str
    su_kien: str | None
    do_tin: str
    nhan_ngan: str
    nhan_day: str
    huong: str
    san: float | None
    tran: float | None
    so_phien_nen: int
    bang_chung: tuple[str, ...]
    phan_bien: tuple[str, ...]
    phu_dinh: str

    @property
    def ket_luan_duoc(self) -> bool:
        return self.pha is not None


def _khong(ly_do: str) -> PhaWyckoff:
    """Không kết luận được — và nói rõ vì sao, chứ không trả về pha trung tính."""
    return PhaWyckoff(
        pha=None, cau_truc="CHƯA XÁC ĐỊNH", su_kien=None,
        do_tin="chưa đủ bằng chứng",
        nhan_ngan="Chưa đủ bằng chứng",
        nhan_day=f"Chưa đủ bằng chứng — {ly_do}",
        huong=TRUNG_TINH, san=None, tran=None, so_phien_nen=0,
        bang_chung=(), phan_bien=(_CANH_PHAI,),
        phu_dinh="Chưa có kết luận nào để phủ định.")


def _thieu_cot(df) -> list[str]:
    if df is None:
        return list(COT_BAT_BUOC)
    return [c for c in COT_BAT_BUOC if c not in getattr(df, "columns", [])]


def _chuan_hoa(df: pd.DataFrame, he_so_gia: float) -> pd.DataFrame:
    """Ép kiểu số, nhân hệ số giá, đánh lại chỉ số từ 0.

    Hệ số giá nhận từ ngoài (`data_quality.price_multiplier`) vì nguồn
    vnstock trả nghìn đồng còn sổ lệnh dùng VNĐ — trộn hai thang đo là
    cái bẫy đã ghi trong `NGUYEN-TAC-DO-LUONG.md`. Ở đây nó chỉ ảnh hưởng
    các mốc giá in ra, không ảnh hưởng nhánh quyết định (mọi so sánh đều
    là tỷ lệ), nhưng nhân một lần ngay đầu vẫn rẻ hơn nhớ nhân ở cuối.
    """
    ra = df.tail(CUA_SO_CAU_TRUC).copy()
    for c in COT_BAT_BUOC:
        ra[c] = pd.to_numeric(ra[c], errors="coerce")
    ra = ra.dropna(subset=list(COT_BAT_BUOC))
    for c in ("open", "high", "low", "close"):
        ra[c] = ra[c] * he_so_gia
    return ra.reset_index(drop=True)


def _tim_cao_trao(w: pd.DataFrame):
    """(chỉ số nến cuối cụm cao trào, bội khối lượng) hoặc (None, 0).

    Cửa sổ tìm bị chặn CẢ HAI ĐẦU, và đó là chỗ dễ làm sai nhất.

    Chặn đầu phải vì cao trào sát mép biểu đồ thì phía sau chưa có nền để
    dựng hai biên — gọi tên pha lúc đó là đoán.

    Chặn đầu trái vì một biểu đồ thường chứa nhiều cấu trúc chồng nhau.
    Cụm khối lượng lớn nhất trong 120 phiên có thể thuộc một cấu trúc ĐÃ
    KẾT THÚC từ mấy tháng trước; neo vào nó thì "vùng dao động" trải dài
    cả con sóng và min/max của nó không còn là sàn/trần của cái gì cả. Đo
    trên dữ liệu thật ngày 22/08/2026: bỏ chặn trái cho ra "vùng" rộng
    96% ở VHM và 61% ở SSI — những con số đó tự nó nói rằng phép đọc sai.
    """
    kl_tb = float(w["volume"].mean())
    if kl_tb <= 0:
        return None, 0.0
    cum = w["volume"].rolling(CUM_CAO_TRAO).sum()
    phai = len(w) - (TOI_THIEU_PHIEN_NEN + CUA_SO_SU_KIEN)
    trai = max(0, len(w) - (TOI_DA_PHIEN_NEN + CUA_SO_SU_KIEN))
    tim = cum.iloc[trai:max(trai, phai)].dropna()
    if tim.empty:
        return None, 0.0
    i = int(tim.idxmax())
    return i, float(cum.iloc[i] / (kl_tb * CUM_CAO_TRAO))


def _vi_tri_trong_pham_vi(w: pd.DataFrame) -> float | None:
    """Giá hiện tại nằm ở đâu trong phạm vi cả cửa sổ. 0 = đáy, 1 = đỉnh.

    Bước 1 của phương pháp: định vị bối cảnh lớn TRƯỚC khi soi nến gần
    nhất. Vùng đi ngang ở đáy sau một đợt giảm mới là nghi vấn tích luỹ;
    cùng hình dạng đó ở đỉnh lại là nghi vấn phân phối.
    """
    day, dinh = float(w["low"].min()), float(w["high"].max())
    if dinh <= day:
        return None
    return (float(w["close"].iloc[-1]) - day) / (dinh - day)


def _co_ar(sau: pd.DataFrame, cao_trao_ban: bool) -> bool:
    """Có nhịp bật (AR) sau cao trào bán, hay nhịp sụt sau cao trào mua.

    Không có AR thì không có trần (hoặc sàn) để vẽ, mà theo phương pháp
    thì thiếu hai đường biên là không gọi được tên pha.
    """
    nhip = sau.iloc[1:1 + NHIP_AR]
    if nhip.empty:
        return False
    if cao_trao_ban:
        goc = float(sau["low"].iloc[0])
        return goc > 0 and (float(nhip["high"].max()) - goc) / goc >= BIEN_AR_TOI_THIEU
    goc = float(sau["high"].iloc[0])
    return goc > 0 and (goc - float(nhip["low"].min())) / goc >= BIEN_AR_TOI_THIEU


def _tim_spring(gan: pd.DataFrame, san: float):
    """Nến thủng sàn rồi đóng cửa trở lại trong vùng. None nếu không có."""
    for i in range(len(gan)):
        if float(gan["low"].iloc[i]) < san <= float(gan["close"].iloc[i]):
            return i
    return None


def _tim_utad(gan: pd.DataFrame, tran: float):
    """Nến vượt trần rồi tụt trở lại trong vùng. None nếu không có."""
    for i in range(len(gan)):
        if float(gan["high"].iloc[i]) > tran >= float(gan["close"].iloc[i]):
            return i
    return None


def _co_test_lai(gan: pd.DataFrame, i_spring: int) -> bool:
    """Có phiên thử lại đáy Spring với khối lượng nhỏ hơn chính nó không.

    Đây là thứ biến "nhiều khả năng" thành "đã xác nhận": Spring nói cung
    đã cạn, Test chứng minh điều đó bằng cách quay lại mà không ai bán nữa.
    """
    day = float(gan["low"].iloc[i_spring])
    kl = float(gan["volume"].iloc[i_spring])
    for i in range(i_spring + 1, len(gan)):
        cham = float(gan["low"].iloc[i]) <= day * (1 + BIEN_TEST_LAI)
        if cham and float(gan["volume"].iloc[i]) < kl:
            return True
    return False


def _ra_vung(gan: pd.DataFrame, san: float, tran: float) -> str | None:
    """"tren" / "duoi" nếu giá đã rời hẳn vùng, None nếu còn trong vùng."""
    if len(gan) < PHIEN_XAC_NHAN_RA_VUNG:
        return None
    dong = gan["close"].iloc[-PHIEN_XAC_NHAN_RA_VUNG:]
    if (dong > tran * (1 + NGUONG_RA_VUNG)).all():
        return "tren"
    if (dong < san * (1 - NGUONG_RA_VUNG)).all():
        return "duoi"
    return None


def _doi_chieu_boi_canh(cau_truc: str, do_tin: str, vi_tri: float | None,
                        cao_trao_ban: bool | None, so_phien: int):
    """(độ tin đã hiệu chỉnh, các bằng chứng phản biện theo bối cảnh).

    HAI PHÉP ĐỐI CHIẾU NÀY PHẢI CHẠY TRÊN CẤU TRÚC ĐÃ KẾT LUẬN, KHÔNG PHẢI
    TRÊN HƯỚNG CỦA ĐIỂM NEO. Bản đầu làm ngược, và smoke test ACB ngày
    22/08/2026 lôi nó ra: nhãn hiện "Pha C — Spring · TÍCH LUỸ · đã xác
    nhận" trong khi ngay dòng bằng chứng đầu tiên ghi "cao trào MUA". Một
    kết luận tự mâu thuẫn với bằng chứng của chính nó mà vẫn để độ tin
    "đã xác nhận" thì tệ hơn không kết luận.

    Không loại bỏ nhánh mâu thuẫn, vì tái tích luỹ và tái phân phối là
    chuyện có thật. Chỉ nói thẳng ra rằng chuỗi kinh điển không khớp, và
    hạ độ tin xuống.
    """
    if cau_truc not in ("TÍCH LUỸ", "PHÂN PHỐI"):
        return do_tin, []

    la_tich_luy = cau_truc == "TÍCH LUỸ"
    them = []

    if cao_trao_ban is not None and cao_trao_ban != la_tich_luy:
        them.append(
            f"Mâu thuẫn với điểm neo: sự kiện đọc ra {cau_truc.lower()}, "
            f"nhưng cụm cao trào mở ra vùng này là cao trào "
            f"{'bán' if cao_trao_ban else 'mua'}. Chuỗi kinh điển đi từ cao "
            f"trào {'bán' if la_tich_luy else 'mua'}. Đây nhiều khả năng là "
            f"{'tái tích luỹ' if la_tich_luy else 'tái phân phối'} — cùng "
            f"hình dạng nhưng bằng chứng yếu hơn.")
        if do_tin == "đã xác nhận":
            do_tin = "nhiều khả năng"

    if vi_tri is not None:
        if la_tich_luy and vi_tri > VI_TRI_DINH:
            them.append(
                f"Đọc là tích luỹ nhưng giá đang ở {vi_tri * 100:.0f}% phạm "
                f"vi {so_phien} phiên. Tích luỹ xảy ra ở ĐÁY sau một đợt "
                f"giảm; ở vùng đỉnh thì đây nhiều khả năng là tái phân phối "
                f"đội lốt.")
        elif not la_tich_luy and vi_tri < VI_TRI_DAY:
            them.append(
                f"Đọc là phân phối nhưng giá đang ở {vi_tri * 100:.0f}% phạm "
                f"vi {so_phien} phiên. Phân phối xảy ra ở ĐỈNH sau một đợt "
                f"tăng; ở vùng đáy thì đây nhiều khả năng là tái tích luỹ.")
    return do_tin, them


def _dung(pha, cau_truc, su_kien, do_tin, huong, san, tran, so_phien_nen,
          bang_chung, phan_bien, phu_dinh, *, vi_tri=None,
          cao_trao_ban=None, so_phien_cua_so=0) -> PhaWyckoff:
    do_tin, them = _doi_chieu_boi_canh(cau_truc, do_tin, vi_tri,
                                       cao_trao_ban, so_phien_cua_so)
    ten = f"Pha {pha}" + (f" — {su_kien}" if su_kien else "")
    return PhaWyckoff(
        pha=pha, cau_truc=cau_truc, su_kien=su_kien, do_tin=do_tin,
        nhan_ngan=ten,
        nhan_day=f"{ten} · {cau_truc} · {do_tin} · nền {so_phien_nen} phiên",
        huong=huong, san=round(san, 2), tran=round(tran, 2),
        so_phien_nen=so_phien_nen,
        bang_chung=tuple(bang_chung),
        phan_bien=tuple(phan_bien) + tuple(them) + (_CANH_PHAI,),
        phu_dinh=phu_dinh)


def doc_pha(df: pd.DataFrame | None, he_so_gia: float = 1.0) -> PhaWyckoff:
    """Đọc pha Wyckoff từ bảng nến ngày (tăng dần theo thời gian).

    Hàm thuần: cùng một bảng vào thì cùng một kết quả ra, không đọc file
    trạng thái, không gọi mạng. Chỉ nhìn dữ liệu có trong bảng, nên không
    thể nhìn trộm tương lai — bất biến 1 và 2 được giữ bằng cấu trúc chứ
    không bằng kỷ luật.
    """
    thieu = _thieu_cot(df)
    if thieu:
        return _khong(f"thiếu cột {', '.join(thieu)}")
    if len(df) < TOI_THIEU_NEN:
        return _khong(f"chỉ có {len(df)} phiên, cần ít nhất {TOI_THIEU_NEN}")

    w = _chuan_hoa(df, he_so_gia)
    if len(w) < TOI_THIEU_NEN:
        return _khong(f"chỉ có {len(w)} phiên dùng được sau khi loại dòng hỏng")

    i_neo, boi_kl = _tim_cao_trao(w)
    if i_neo is None:
        return _khong("khối lượng bằng 0 — không đọc được nỗ lực/kết quả")

    j0 = max(0, i_neo - CUM_CAO_TRAO)
    lech = float(w["close"].iloc[i_neo]) - float(w["close"].iloc[j0])
    if lech == 0:
        return _khong("cụm khối lượng lớn nhất không đổi giá — "
                      "không phân biệt được cao trào bán với cao trào mua")
    # Tên biến nói rõ đây là hướng của ĐIỂM NEO, không phải kết luận.
    # Bản đầu gọi nó `tich_luy` và chính cái tên đó dẫn tới việc dùng nó
    # thay cho cấu trúc đã kết luận ở phần đối chiếu bối cảnh.
    cao_trao_ban = lech < 0

    sau = w.iloc[i_neo:].reset_index(drop=True)
    if not _co_ar(sau, cao_trao_ban):
        return _khong("không thấy nhịp bật/sụt tự động (AR) sau cao trào — "
                      "chưa vẽ được hai đường biên")

    nen = sau.iloc[:-CUA_SO_SU_KIEN]
    gan = sau.iloc[-CUA_SO_SU_KIEN:].reset_index(drop=True)
    if len(nen) < TOI_THIEU_PHIEN_NEN:
        return _khong(f"nền mới {len(nen)} phiên, cần ít nhất "
                      f"{TOI_THIEU_PHIEN_NEN} phiên mới có hai biên có nghĩa")

    san = float(nen["low"].min())
    tran = float(nen["high"].max())
    if san <= 0:
        return _khong("giá không dương — dữ liệu hỏng")
    bien_do = (tran - san) / san
    if bien_do > BIEN_DO_VUNG_TOI_DA:
        return _khong(f"biên độ nền {bien_do * 100:.0f}% quá rộng để gọi là "
                      f"vùng đi ngang — giá đang trong xu hướng, chưa hình "
                      f"thành vùng dao động")

    kl_nen = float(nen["volume"].mean())
    n_nen = len(nen)
    ten_cau_truc = "TÍCH LUỸ" if cao_trao_ban else "PHÂN PHỐI"

    vi_tri = _vi_tri_trong_pham_vi(w)
    chung = [f"Cao trào {'bán' if cao_trao_ban else 'mua'} neo ở cụm "
             f"{CUM_CAO_TRAO} phiên nặng {boi_kl:.1f}x khối lượng nền.",
             f"Hai biên dựng từ {n_nen} phiên nền: sàn {san:,.0f} — "
             f"trần {tran:,.0f} (rộng {bien_do * 100:.1f}%)."]
    if vi_tri is not None:
        chung.append(f"Bối cảnh {len(w)} phiên: giá đang ở mức "
                     f"{vi_tri * 100:.0f}% phạm vi (0% = đáy, 100% = đỉnh).")

    phan = []
    if boi_kl < BOI_KL_CAO_TRAO:
        phan.append(f"Cao trào chỉ {boi_kl:.1f}x nền, dưới ngưỡng "
                    f"{BOI_KL_CAO_TRAO}x — điểm neo của cả câu chuyện yếu.")
    if n_nen < PHIEN_PHA_A:
        phan.append(f"Định luật 2 (nguyên nhân–kết quả): nền mới {n_nen} "
                    f"phiên, nguyên nhân nhỏ thì kết quả nhỏ.")
    # Hai phép đối chiếu bối cảnh nằm trong `_dung()`, vì chúng phải chạy
    # trên cấu trúc ĐÃ KẾT LUẬN chứ không trên hướng của điểm neo.
    boi_canh = dict(vi_tri=vi_tri, cao_trao_ban=cao_trao_ban,
                    so_phien_cua_so=len(w))

    pd_tich = f"Đóng cửa dưới sàn {san:,.0f} → đã đọc sai, đây không phải tích luỹ."
    pd_phan = f"Đóng cửa trên trần {tran:,.0f} → đã đọc sai, đây không phải phân phối."

    # ── Pha E: giá đã rời hẳn vùng ────────────────────────────────────
    huong_ra = _ra_vung(gan, san, tran)
    if huong_ra == "tren":
        return _dung("E", "TÍCH LUỸ", "Markup", "đã xác nhận", TANG,
                     san, tran, n_nen,
                     chung + [f"{PHIEN_XAC_NHAN_RA_VUNG} phiên gần nhất đều "
                              f"đóng trên trần {tran:,.0f} quá "
                              f"{NGUONG_RA_VUNG * 100:.0f}%."],
                     phan, pd_tich, **boi_canh)
    if huong_ra == "duoi":
        return _dung("E", "PHÂN PHỐI", "Markdown", "đã xác nhận", GIAM,
                     san, tran, n_nen,
                     chung + [f"{PHIEN_XAC_NHAN_RA_VUNG} phiên gần nhất đều "
                              f"đóng dưới sàn {san:,.0f} quá "
                              f"{NGUONG_RA_VUNG * 100:.0f}%."],
                     phan, pd_phan, **boi_canh)

    # ── Pha D: SOS / SOW — phá biên kèm khối lượng ────────────────────
    manh = gan[(gan["close"] > tran * (1 + NGUONG_RA_VUNG))
               & (gan["volume"] > kl_nen)]
    if len(manh):
        boi = float(manh["volume"].iloc[-1]) / kl_nen
        return _dung("D", "TÍCH LUỸ", "SOS",
                     "đã xác nhận" if boi >= BOI_KL_MANH else "nhiều khả năng",
                     TANG, san, tran, n_nen,
                     chung + [f"Nến vượt trần {tran:,.0f} với khối lượng "
                              f"{boi:.1f}x nền — cầu áp đảo cung."],
                     phan, pd_tich, **boi_canh)

    yeu = gan[(gan["close"] < san * (1 - NGUONG_RA_VUNG))
              & (gan["volume"] > kl_nen)]
    if len(yeu):
        boi = float(yeu["volume"].iloc[-1]) / kl_nen
        return _dung("D", "PHÂN PHỐI", "SOW",
                     "đã xác nhận" if boi >= BOI_KL_MANH else "nhiều khả năng",
                     GIAM, san, tran, n_nen,
                     chung + [f"Nến thủng sàn {san:,.0f} với khối lượng "
                              f"{boi:.1f}x nền — cung áp đảo cầu."],
                     phan, pd_phan, **boi_canh)

    # ── Pha C: Spring / UTAD — bẫy hai đầu ────────────────────────────
    i_sp = _tim_spring(gan, san)
    if i_sp is not None:
        boi = float(gan["volume"].iloc[i_sp]) / kl_nen
        co_test = _co_test_lai(gan, i_sp)
        bc = [f"Nến thủng sàn {san:,.0f} xuống "
              f"{float(gan['low'].iloc[i_sp]):,.0f} rồi đóng cửa trở lại "
              f"trong vùng, khối lượng {boi:.1f}x nền."]
        pb = list(phan)
        if boi <= BOI_KL_CAN_KIET:
            bc.append("Khối lượng cạn kiệt ở cây thủng — không có cung thật.")
        elif boi >= BOI_KL_MANH:
            bc.append("Khối lượng lớn mà giá không rơi thêm — lực bán đang "
                      "bị hấp thụ (định luật 3: nỗ lực lớn, kết quả nhỏ).")
        else:
            pb.append(f"Khối lượng cây thủng {boi:.1f}x nền — không cạn kiệt "
                      f"mà cũng không đủ lớn để nói là hấp thụ. Phần lớn cú "
                      f"thủng hỗ trợ là thủng thật, không phải Spring.")
        if co_test:
            bc.append("Đã có phiên thử lại đáy Spring với khối lượng nhỏ hơn "
                      "— cung cạn được xác nhận.")
        else:
            pb.append("Chưa có phiên Test lại đáy Spring. Thiếu Test thì "
                      "Spring vẫn có thể là thủng thật đang diễn ra.")
        return _dung("C", "TÍCH LUỸ", "Spring",
                     "đã xác nhận" if (co_test and boi <= BOI_KL_CAN_KIET)
                     else "nhiều khả năng",
                     TANG, san, tran, n_nen, chung + bc, pb, pd_tich,
                     **boi_canh)

    i_ut = _tim_utad(gan, tran)
    if i_ut is not None:
        boi = float(gan["volume"].iloc[i_ut]) / kl_nen
        bc = [f"Nến vượt trần {tran:,.0f} lên "
              f"{float(gan['high'].iloc[i_ut]):,.0f} rồi tụt trở lại trong "
              f"vùng, khối lượng {boi:.1f}x nền — bẫy người mua breakout."]
        pb = list(phan)
        if boi < BOI_KL_MANH:
            pb.append(f"Khối lượng cây vượt trần chỉ {boi:.1f}x nền. UTAD "
                      f"thật thường đi kèm khối lượng lớn; mức này cũng có "
                      f"thể chỉ là một nhịp phá biên hụt bình thường.")
        return _dung("C", "PHÂN PHỐI", "UTAD",
                     "đã xác nhận" if boi >= BOI_KL_MANH else "nhiều khả năng",
                     GIAM, san, tran, n_nen, chung + bc, pb, pd_phan,
                     **boi_canh)

    # ── Pha A: vùng còn non, mới qua cao trào + AR ────────────────────
    if n_nen < PHIEN_PHA_A:
        return _dung("A", ten_cau_truc, None,
                     "nhiều khả năng" if boi_kl >= BOI_KL_CAO_TRAO
                     else "chưa đủ bằng chứng",
                     TRUNG_TINH, san, tran, n_nen,
                     chung + ["Đã có cao trào và nhịp AR, chưa thấy sự kiện "
                              "pha C hay pha D nào."],
                     phan + ["Nhịp hồi trong xu hướng giảm trông y hệt AR. "
                             "Nếu các đỉnh sau vẫn thấp dần thì đây là hồi "
                             "kỹ thuật, không phải pha A."],
                     pd_tich if cao_trao_ban else pd_phan, **boi_canh)

    # ── Pha B: đi ngang, KHÔNG phân định được hướng ───────────────────
    return _dung("B", "CHƯA PHÂN ĐỊNH", None, "chưa đủ bằng chứng",
                 TRUNG_TINH, san, tran, n_nen,
                 chung + [f"Đi ngang {n_nen} phiên trong vùng, chưa có "
                          f"Spring cũng chưa có UTAD."],
                 phan + ["Pha B của tích luỹ và pha B của phân phối trông "
                         "giống hệt nhau. Khác biệt chỉ lộ ra ở pha C."],
                 f"Thủng {san:,.0f} rồi đóng lại trong vùng → nghiêng tích "
                 f"luỹ. Vượt {tran:,.0f} rồi tụt lại → nghiêng phân phối. "
                 f"Trước một trong hai, mọi kết luận về hướng đều là đoán.",
                 **boi_canh)
