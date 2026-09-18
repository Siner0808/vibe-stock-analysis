"""Mở phiên: nhắc quy trình và các mốc ngày đang chặn — hook `SessionStart`.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 07/09/2026 dự án đã có sẵn một skill quy trình, và tôi làm việc **nửa
buổi** rồi mới biết — hệ thống tự hiện nó ra giữa chừng. Đó là lỗi số 10
trong `references/loi-da-mac.md`.

Vá bằng cách viết "Bước 0: `ls .claude/skills/`" vào chính skill ấy là một
vòng tròn: phải đọc skill mới biết phải đi tìm skill. **Một luật nằm trong
đầu thì không phải luật** — câu đó rút ra từ lỗi số 12 cùng ngày, khi tôi
áp dụng đúng một quy tắc ở một file rồi vi phạm nó ở file kế tiếp sau một
giờ.

File này là cơ chế: harness chạy nó lúc mở phiên, không phụ thuộc ai nhớ.

NGUYÊN TẮC THIẾT KẾ
───────────────────
1. **KHÔNG BAO GIỜ CHẶN.** Luôn thoát 0, nuốt mọi lỗi. Một hook mở phiên
   mà làm hỏng phiên thì tệ hơn không có.
2. **Suy ra, đừng gõ.** Tên skill đọc từ `.claude/skills/`, mốc ngày đọc
   từ `docs/HANDOFF.md`. Gõ tay vào đây là tạo thêm một chỗ lệch nữa —
   đúng thứ cả tuần này đi vá.
3. **Ngắn.** Nhắc nhiều thì thành nhiễu, mà nhiễu thì bị bỏ qua.
"""
import datetime as dt
import json
import pathlib
import re
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
HANDOFF = GOC / "docs" / "HANDOFF.md"
STATE = GOC / "docs" / "STATE.md"
SO_SOAT = GOC / "docs" / "soat-notebooklm.json"
SO_DINH_KY = GOC / "docs" / "soat-dinh-ky.json"
THU_MUC_SKILL = GOC / ".claude" / "skills"

#: Nhịp soát lại quy trình, người dùng chốt 16/09/2026. KHÔNG phải nhịp
#: *cập nhật*: việc ấy đã chạy theo sự kiện ở Bước 6, và đo được là SKILL
#: cùng bảng lỗi có sửa **9 trên 14 ngày** gần nhất — đặt nhịp 2 ngày lên
#: đó là đặt một nhịp THẤP HƠN nhịp đang có.
#:
#: Nhịp này nhắm nửa chưa bao giờ có cơ chế: **soát lại thứ ĐÃ CÓ**. Riêng
#: ngày 16/09 hai câu cũ bị bắt gặp do TÌNH CỜ — *"cửa Bash không ghi nhật
#: ký"* (nhật ký đã có từ 14/09) và mâu thuẫn BƯỚC 49 sống sáu ngày với dữ
#: kiện lật ngược nó nằm ngay trong câu khai ra nó.
NHIP_SOAT_NGAY = 2

#: Từ bao nhiêu lượt `khong_soat_vi` LIÊN TIẾP thì bản tin phải nói ra.
#:
#: Ba, và con số này KHÔNG phải một ngưỡng thống kê — tỷ lệ nền của sổ là
#: 30/43 ≈ 70%, nên một chuỗi 3 xảy ra ~34% thời gian do ngẫu nhiên. Nó là
#: một ngưỡng **chi phí**: báo nhầm tốn đúng một dòng chữ, còn bỏ sót thì
#: tốn đúng cái đã xảy ra ngày 18/09/2026 — sáu lượt liên tiếp, và người
#: dùng phải nhắc lần thứ tư.
#:
#: Dòng này KHÔNG chặn gì. Nó nói ra lúc MỞ PHIÊN, chỗ còn quyền chọn —
#: đúng hình dạng đã cứu chính vấn đề này ngày 16/09.
NGUONG_CHUOI_BO_SOAT = 3

RE_NGAY = re.compile(r"\*\*(\d{2})/(\d{2})/(\d{4})\*\*")


def ten_skill() -> list[str]:
    """Đọc từ đĩa, không gõ tay — đổi tên skill thì lời nhắc đi theo."""
    try:
        return sorted(p.parent.name for p in THU_MUC_SKILL.glob("*/SKILL.md"))
    except OSError:
        return []


def moc_ngay_con_chan(hom_nay: dt.date | None = None) -> list[tuple[dt.date, str]]:
    """Mốc ngày trong mục "Chờ tới ngày" của HANDOFF mà CHƯA tới hạn.

    PHÉP PHÁN, tách riêng để tự chứng minh được: đưa vào một `hom_nay` cố
    định thì kết quả phải đổi theo, và đó là thứ đột biến sẽ nhắm tới.
    """
    hom_nay = hom_nay or dt.date.today()
    try:
        src = HANDOFF.read_text(encoding="utf-8")
    except OSError:
        return []

    kh = re.search(r"\*\*Chờ tới ngày[^\n]*\*\*\n(.*?)(?=\n\*\*|\n## )",
                   src, re.S)
    if not kh:
        return []

    ra = []
    for dong in re.split(r"\n(?=- )", kh.group(1)):
        m = RE_NGAY.search(dong)
        if not m:
            continue
        try:
            ngay = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        if ngay <= hom_nay:
            continue                      # tới hạn rồi thì không còn chặn
        mo_ta = re.sub(r"\s+", " ", dong.split("—", 1)[-1]).strip(" -.")
        ra.append((ngay, mo_ta[:70]))
    return sorted(ra)


def trang_thai_cua() -> str:
    """Một dòng: bao nhiêu cửa đang thật sự chạy được.

    Có mặt vì tới 10/09/2026 không ai ĐỌC được trạng thái này — phải suy
    ra từ `python --version`, một phép thử chỉ đi qua ĐÚNG MỘT trong sáu
    cửa. Ba ngày liền câu "sáu cửa chết" được chép lại trong khi bốn cửa
    vẫn đang chạy. Xem `tools/kiem_cua_song.py`.
    """
    try:
        from kiem_cua_song import bao_cao
        return bao_cao(mot_dong=True)[1]
    except Exception:
        return "CUA: chua kiem duoc (tools/kiem_cua_song.py)"


def buoc_chua_khai_soat() -> list[str]:
    """`## BƯỚC n` từ mốc trở đi mà chưa có dòng khai trong sổ soát chéo.

    SUY RA TỪ ĐĨA — nguyên tắc 2 ở đầu file. Mốc đọc từ `_moc_buoc` trong
    chính sổ, đúng con số `tests/test_soat_notebooklm.py` dùng; gõ lại ở
    đây là tạo chỗ lệch thứ hai.

    Có mặt vì ngày 16/09/2026 người dùng phải nhắc **lần thứ ba** rằng
    NotebookLM không được dùng. Gác ở bộ test bắt được điều đó — nhưng nó
    chỉ đỏ lúc CHẠY TEST, tức sau khi việc đã làm xong. Dòng này nói ra
    lúc MỞ PHIÊN, khi còn quyền chọn.
    """
    try:
        sys.path.insert(0, str(GOC / "tools"))
        from soat_loi_khai_cu import buoc_chua_khai

        so = json.loads(SO_SOAT.read_text(encoding="utf-8"))
        return buoc_chua_khai(STATE.read_text(encoding="utf-8"),
                              so["soat"], int(so["_moc_buoc"]))
    except Exception:
        return []


def moc_bat_buoc_hoi() -> int | None:
    """Mốc BƯỚC từ đó ô thoát `khong_soat_vi` KHÔNG còn được nhận.

    Người dùng chốt 18/09/2026: **mỗi BƯỚC đều phải đi qua sổ tay**. Con số
    đọc từ `_moc_bat_buoc_hoi` trong chính sổ — đúng con số
    `tests/test_soat_notebooklm.py` dùng. Gõ lại nó ở đây là tạo chỗ lệch
    thứ hai, và dự án đã trả giá cho đúng hình dạng đó (`N_DAY_DU` 596/451).

    `None` khi chưa đọc được: im lặng, đừng đoán một con số. Cùng lý do
    `ngay_tu_lan_soat_quy_trinh()` phân biệt `None` với `0`.
    """
    try:
        so = json.loads(SO_SOAT.read_text(encoding="utf-8"))
        m = so.get("_moc_bat_buoc_hoi")
        return int(m) if isinstance(m, int) and not isinstance(m, bool) else None
    except Exception:
        return None


def chuoi_khong_soat(so: dict | None = None) -> list[str]:
    """Dãy mục CUỐI SỔ liên tiếp nhau đều khai `khong_soat_vi`. HÀM THUẦN.

    VÌ SAO ĐẾM CHUỖI, VÀ VÌ SAO KHÔNG SO CHỮ — lỗi 86, đo 18/09/2026
    ─────────────────────────────────────────────────────────────────
    Giả thuyết đầu tiên là *"các lý do viện dẫn cùng một sự kiện sẽ giống
    nhau về CHỮ"*, nên gác nên cấm lặp lý do. **Đo trước khi dựng, và phép
    đo BÁC nó:**

        sau muc cua loi 86, giua CHUNG voi nhau : trung binh 0,131
        moi cap CON LAI trong so                : trung binh 0,099
        cap giong nhau nhat ca so               : 0,653  (BUOC 84 <-> 85)
        khong cap nao trong 435 cap dat 0,70

    Sáu lời khai ấy giống nhau **còn ít hơn** mức trung bình. Chúng không
    bị chép — mỗi lượt là một lý do thật sự khác, thật sự cụ thể, và
    **chính điều đó làm chúng vô hình**. Một gác so chữ sẽ im lặng đúng
    lúc cần kêu.

    Thứ lặp lại là **sự kiện được viện dẫn**, không phải chữ: *"bản chụp"*
    ở 4/6, *"file .py"* ở 4/6, *"quần thể"* · *"lỗi 66"* ở 3/6. Máy không
    đọc được điều đó.

    Nên đại lượng duy nhất còn lại mà máy đọc được là **độ dài chuỗi**. Nó
    không phán lý do đúng hay sai — nó chỉ làm cái hình dạng ấy **không
    còn vô hình được nữa**.

    Đếm theo THỨ TỰ GHI trong sổ, không theo ngày: nhiều mục cùng một
    ngày, và thứ tự ghi mới là thứ tự người ta đi qua chúng.
    """
    try:
        if so is None:
            so = json.loads(SO_SOAT.read_text(encoding="utf-8"))["soat"]
        ra: list[str] = []
        for ten, d in reversed(list(so.items())):
            if not isinstance(d, dict):
                continue
            if "khong_soat_vi" not in d:
                break
            ra.append(ten)
        return list(reversed(ra))
    except Exception:
        return []


def ngay_tu_lan_soat_quy_trinh(hom_nay: dt.date | None = None) -> int | None:
    """Số ngày kể từ lượt soát lại quy trình gần nhất; `None` nếu chưa đọc được.

    `None` và `0` là hai chuyện khác nhau — sổ hỏng thì im, đừng báo "vừa
    soát hôm nay". Cùng lý do `kiem_cu_phap_311.py` có mã thoát 2.
    """
    try:
        ds = json.loads(SO_DINH_KY.read_text(encoding="utf-8"))["lan_soat"]
        if not ds:
            return None
        moi = max(dt.date.fromisoformat(x["ngay"]) for x in ds)
        return ((hom_nay or dt.date.today()) - moi).days
    except Exception:
        return None


def ban_tin(hom_nay: dt.date | None = None) -> str:
    hom_nay = hom_nay or dt.date.today()
    d = ["┌─ vibe_preview ─────────────────────────────────────────────"]
    for t in ten_skill():
        d.append(f"│ QUY TRÌNH BẮT BUỘC — gọi skill `{t}` TRƯỚC khi đọc")
        d.append("│ hay sửa file đầu tiên. Nó có: cách vá file (một đường")
        d.append("│ duy nhất), vòng lặp đột biến, năm cổng gác đúng thứ tự.")
    if not ten_skill():
        d.append("│ ⚠️  không thấy skill quy trình nào trong .claude/skills/")

    d.append("│")
    d.append(f"│ {trang_thai_cua()}")

    thieu = buoc_chua_khai_soat()
    tre = ngay_tu_lan_soat_quy_trinh(hom_nay)
    chuoi = chuoi_khong_soat()
    if (thieu or (tre is not None and tre >= NHIP_SOAT_NGAY)
            or len(chuoi) >= NGUONG_CHUOI_BO_SOAT):
        d.append("│")
    if len(chuoi) >= NGUONG_CHUOI_BO_SOAT:
        them = " …" if len(chuoi) > 3 else ""
        d.append(f"│ ⚠️  {len(chuoi)} lượt LIÊN TIẾP khai `khong_soat_vi`: "
                 f"{' · '.join(chuoi[-3:])}{them}")
        d.append("│   Mỗi lý do có thể đúng mà chuỗi vẫn sai — lỗi 86.")
        d.append("│   Đo lại quần thể sổ tay trước khi khai lượt thứ "
                 f"{len(chuoi) + 1}.")
    if thieu:
        them = " …" if len(thieu) > 4 else ""
        d.append(f"│ SOÁT CHÉO còn nợ {len(thieu)}: "
                 f"{' · '.join(thieu[:4])}{them}")
        m = moc_bat_buoc_hoi()
        if m is None:
            d.append("│   khai vào docs/soat-notebooklm.json — phát hiện, hoặc lý do")
        else:
            d.append("│   khai vào docs/soat-notebooklm.json — PHÁT HIỆN, không")
            d.append(f"│   phải lý do: từ BƯỚC {m} mỗi BƯỚC phải HỎI (quy tắc 3).")
    if tre is not None and tre >= NHIP_SOAT_NGAY:
        d.append(f"│ SOÁT QUY TRÌNH: lần gần nhất {tre} ngày trước "
                 f"(nhịp {NHIP_SOAT_NGAY} ngày)")
        d.append("│   danh sách việc: tools/soat_loi_khai_cu.py")

    chan = moc_ngay_con_chan(hom_nay)
    if chan:
        d.append("│")
        d.append("│ CHẶN THEO NGÀY — đừng đọc sớm:")
        for ngay, mo_ta in chan:
            con = (ngay - hom_nay).days
            d.append(f"│   {ngay.strftime('%d/%m/%Y')} (còn {con} ngày) — {mo_ta}")
    d.append("└────────────────────────────────────────────────────────────")
    return "\n".join(d)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        print(ban_tin())
    except Exception:
        pass                       # mở phiên KHÔNG BAO GIỜ được hỏng vì đây
    return 0


if __name__ == "__main__":
    sys.exit(main())
