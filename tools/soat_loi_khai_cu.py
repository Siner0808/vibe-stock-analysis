"""Danh sách việc cho lượt SOÁT LẠI QUY TRÌNH — lời khai phủ định còn sống.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 16/09/2026 người dùng chốt: soát lại skill và cửa của dự án theo nhịp
**2 ngày**. Đo trước khi nhận, và phép đo đổi cái đích:

    SKILL.md + bang loi co SUA 9 tren 14 ngay gan nhat

Tức việc **cập nhật** đã chạy hằng ngày theo sự kiện — `SKILL.md` Bước 6 lo
việc ấy, mỗi lỗi mới là một dòng mới. Đặt nhịp 2 ngày lên đó là đặt một
nhịp THẤP HƠN nhịp đang có.

Nửa chưa bao giờ có cơ chế là nửa kia: **soát lại thứ ĐÃ CÓ**. Riêng ngày
16/09 hai câu cũ bị bắt gặp do TÌNH CỜ:

    "cua Bash khong ghi nhat ky ... Ghi ra day, CHUA LAM"   (BUOC 65)
        -> nhat ky da co tu 14/09, va tools/soat_nhat_ky_cua.py doc no
    "dac ta noi chay MOT lan / BUOC 49 noi HAI lan -- mot trong hai da cu"
        -> khong cau nao cu; hai ban khai khac nhau ca ba truong, sau ngay

Không công cụ nào chỉ ra chúng. Một lượt "soát lại" không có danh sách thì
nó là một lời hứa — và dự án này đã đo được rằng lời hứa thì trôi.

NÓ CHỌN QUẦN THỂ NÀO, VÀ VÌ SAO HẸP
───────────────────────────────────
Quét thô mọi dòng mang chữ phủ định trên bảy tài liệu: **187 dòng**. Không
ai soát 187 dòng mỗi hai ngày, và một công cụ không dùng nổi thì bị bỏ qua
— đúng cái vòng nó sinh ra để cắt. Ba phép siết, mỗi phép có lý do:

  1. **bỏ dòng bảng** (`| … |`) — bảng lỗi là SỬ LIỆU, lời khai trong đó
     mô tả lúc ấy và phải giữ nguyên.
  2. **bỏ dòng đã mang dấu bác bỏ** (🔴 ⚠️ ~~…~~ "ĐÃ BỊ BÁC") — đã có
     người soát rồi, và quy ước dự án là giữ lại bản cũ kèm dấu.
  3. **phải NÊU TÊN một thành phần** (`` `tools/x.py` ``) — chỉ loại ấy mới
     kiểm lại được bằng máy: có cái tên thì có chỗ để chạy `grep`.

Còn **15 dòng**. Đo 16/09/2026.

`docs/STATE.md` CỐ Ý không nằm trong danh sách: nó là nhật ký chỉ-thêm, lời
khai trong một BƯỚC cũ mô tả ngày ấy và **không phải** thứ cần sửa. Chỗ
chống lại nó là `SKILL.md` Bước 1 điều 2 — *một câu "không làm được" chép
từ ghi chú thì phải ĐO LẠI* — chứ không phải đi vá lịch sử.

NÓ KHÔNG PHÁN — nó chỉ ra CHỖ ĐÁNG NHÌN
───────────────────────────────────────
Giống hệt lời khai về NotebookLM trong `SKILL.md`. Mỗi dòng in ra là một
địa chỉ để mở ra xem, không phải một kết luận rằng câu ấy đã sai.

NÓ TỪNG BẢO NGƯỜI TA GHI VÀO MỘT CHỖ NÓ KHÔNG ĐỌC (sửa 18/09/2026)
──────────────────────────────────────────────────────────────────
Bản đầu kết bằng *"ghi kết quả lượt soát vào `docs/soat-dinh-ky.json`"* rồi
**không bao giờ đọc file ấy**. Một ống một chiều: nó đòi một bản ghi mà
chính nó không dùng được.

Đo trước khi sửa — dựng lại cây tài liệu của hai commit trong thư mục tạm
rồi gọi chính `loi_khai_con_song`, nên phép đo không đi qua bản sao nào của
logic này:

    16/09 (441b2d4)   15 loi khai
    18/09 (4861040)   16 loi khai
    ra khoi danh sach : 0 dong
    ca HAI dong luot 16/09 da phan xu : van con nguyen trong danh sach

Lượt soát 16/09 phán xử hai dòng và đánh dấu một dòng **đúng quy ước dự
án** — giữ nguyên câu gốc, thêm ô ⚠️ NGAY DƯỚI. `DA_CO_DAU` đọc TỪNG DÒNG
nên nó không thấy ô dấu ở dòng kế. Phạm vi của phép lọc hẹp hơn đơn vị của
quy ước: cùng họ lỗi 73 và lỗi 80.

Hệ quả thật, không phải lý thuyết: danh sách chỉ mọc dài, một lượt soát
không để lại dấu vết nào trong chính bản in, nên lượt sau mở lại đúng những
dòng lượt trước vừa mở — và phần đuôi chưa ai động tới thì mãi không ai
động tới.

**Phép sửa KHÔNG phải xoá dòng đã soát.** Một câu phán *"THẬT, vẫn đúng"*
hôm nay vẫn cũ được ngày mai; xoá nó khỏi danh sách là dựng đúng cái im
lặng mà nhịp soát sinh ra để phá. Nó **xếp** và **ghi chú**: chưa ai mở thì
lên trước, đã soát thì xuống dưới kèm NGÀY và PHÁN QUYẾT.

Khớp bằng **nguyên văn dòng** (`dong` trong sổ), không bằng số dòng — số
dòng trôi mỗi lần tài liệu dài ra, và hai mục ngày 16/09 đã trôi 1706→1873
và 1740→1907 chỉ trong hai ngày. Câu đổi chữ thì nó lại hiện ra như chưa
ai mở, và đó là hành vi ĐÚNG: câu đã khác thì phán quyết cũ không còn nói
về nó nữa.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SO_DINH_KY = GOC / "docs" / "soat-dinh-ky.json"

TAI_LIEU = [
    ".claude/skills/quy-trinh-lam-viec/SKILL.md",
    ".claude/skills/quy-trinh-lam-viec/references/loi-da-mac.md",
    ".claude/skills/quy-trinh-lam-viec/references/bay.md",
    ".claude/skills/quy-trinh-lam-viec/references/cong-thuc-chay.md",
    "CLAUDE.md",
    "docs/HANDOFF.md",
    "NGUYEN-TAC-DO-LUONG.md",
]

#: Họ thứ hai — ``không nhập / gọi / dùng / chạm`` — thêm ở lượt soát 5
#: (24/09/2026). Đó là lời khai về QUAN HỆ giữa các mảnh mã, loại mục nhanh
#: nhất khi mã đổi, và danh sách cũ mù hẳn trước nó. Ca thật: `HANDOFF` mục 5
#: ghi *"Repo **không nhập** `vnstock_data` ở đâu cả"* ngày 18/09; từ 22/09
#: `fetch_khoi_ngoai.py` nhập nó, và câu ấy sống trần tới khi BƯỚC 118 tình cờ
#: vấp phải. Đo trước khi thêm, cùng bộ lọc của công cụ:
#:
#:     khong nhap +2 · khong goi +1 · khong dung +1 · khong cham +1
#:     khong doc +11 · khong co +9 · khong con +3     <- KHONG them
#:
#: Ba từ sau kéo vào chủ yếu LUẬT và văn xuôi (*"gác phải đọc AST, không đọc
#: `in`"*), không phải khẳng định về mã — thêm chúng là quay lại con số 187.
PHU_DINH = re.compile(
    r"(chưa bao giờ|chưa ai|không ai|chưa có|chưa làm|chưa đo|chưa được"
    r"|chưa kiểm|không tồn tại|không ghi"
    r"|không nhập|không gọi|không dùng|không chạm)", re.I)
DA_CO_DAU = ("🔴", "⚠️", "ĐÃ BỊ BÁC", "đã bị thay", "ĐÃ ĐO", "ĐÃ TRUY", "~~")
#: Một cái tên trong dấu nháy ngược. `()` ở cuối được nhận, vì dự án
#: viết tên hàm đúng kiểu ấy suốt — `kiem_goi()`, `_doc()`, `chay()`.
#:
#: Bản đầu (12/09/2026) bỏ sót `()`, và lời khai của chính phép lọc là
#: *"lời khai phủ định CÓ NÊU TÊN"* — mà `_doc()` thì có nêu tên. Đo
#: 21/09/2026 trên đúng quần thể này: sửa xong danh sách đi từ **19 lên
#: 21 dòng**, tức lỗ hổng nhỏ nhưng có thật, và một trong hai dòng nó bỏ
#: sót là ca `_doc()` — cái tên mà `tests/test_tai_lieu_khop_ten_ma.py`
#: sinh ra để canh.
CO_TEN = re.compile(r"`[A-Za-z_][\w./:-]*(\(\))?`")


RE_BUOC = re.compile(r"^##\s+(BƯỚC\s+(\d+))\s*—")


def buoc_chua_khai(van_state: str, da_khai, moc: int) -> list[str]:
    """`## BƯỚC n` với n >= `moc` mà chưa có tên trong `da_khai`. HÀM THUẦN.

    MỘT bản cài đặt, hai nơi gọi: `tools/cua_mo_phien.py` (bản tin mở
    phiên) và `tests/test_soat_notebooklm.py` (gác). Bản đầu ngày
    16/09/2026 viết hai lần, rồi thêm một gác bắt hai bản khớp nhau — và
    **đục thử cho thấy gác ấy vô dụng**: khi mọi mục đã khai thì cả hai
    vế đều RỖNG, nên hai đột biến vào hook sống sót cả hai. Một phép so
    hai tập rỗng không phân biệt được gì; đó là lỗi 66.

    Bỏ bản thứ hai rẻ hơn và chắc hơn là canh cho hai bản khớp nhau —
    `SKILL.md` Bước 2: *"Suy ra, đừng gõ. Một ngưỡng gõ tay ở hai chỗ sẽ
    trôi ra khỏi nhau."* Điều ấy đúng với mã y như với ngưỡng.

    Neo vào ĐẦU DÒNG và CẤP tiêu đề, không đọc sự XUẤT HIỆN của chữ
    "BƯỚC" — nó nằm hàng chục lần trong văn xuôi của chính `STATE.md`.
    """
    da_khai = set(da_khai)
    ra: list[str] = []
    for d in van_state.splitlines():
        m = RE_BUOC.match(d)
        if m and int(m.group(2)) >= moc:
            ten = re.sub(r"\s+", " ", m.group(1))
            if ten not in da_khai and ten not in ra:
                ra.append(ten)
    return ra


def loi_khai_con_song(goc: Path = GOC) -> list[tuple[str, int, str]]:
    """(file, dòng, nội dung) — mọi lời khai phủ định CÓ NÊU TÊN, chưa đánh dấu."""
    ra: list[tuple[str, int, str]] = []
    for ten in TAI_LIEU:
        p = goc / ten
        if not p.exists():
            continue
        for i, d in enumerate(p.read_text(encoding="utf-8",
                                          errors="replace").splitlines(), 1):
            if not PHU_DINH.search(d):
                continue
            if d.lstrip().startswith("|"):
                continue
            if any(x in d for x in DA_CO_DAU):
                continue
            if not CO_TEN.search(d):
                continue
            ra.append((ten, i, d.strip()))
    return ra


def da_soat(so: dict) -> dict[str, tuple[str, str]]:
    """{nguyên-văn-dòng: (ngày, phán quyết)} — HÀM THUẦN, nhận sổ đã nạp.

    Khoá là **nguyên văn dòng**, không phải số dòng. Phát hiện nào chưa khai
    `dong` thì không vào bảng — và đó là chiều hỏng AN TOÀN: dòng ấy hiện ra
    như chưa ai mở, tức lượt sau mở lại nó. Chiều hỏng nguy hiểm là ngược
    lại — đánh dấu "đã soát" cho một dòng chưa ai soát — và khoá nguyên văn
    không tạo ra được chiều ấy.

    Lượt gần nhất thắng: cùng một dòng soát hai lần thì ngày sau đè ngày
    trước.
    """
    bang: dict[str, tuple[str, str]] = {}
    for luot in sorted(so.get("lan_soat", []), key=lambda x: x.get("ngay", "")):
        for pd in luot.get("phat_hien", []):
            d = (pd.get("dong") or "").strip()
            if d:
                bang[d] = (luot.get("ngay", ""), pd.get("phan_quyet", ""))
    return bang


def xep(ra, bang) -> list[tuple[str, int, str, tuple[str, str] | None]]:
    """CHƯA AI MỞ lên trước, giữ nguyên thứ tự file/dòng trong mỗi nhóm.

    KHÔNG bỏ dòng nào. Một câu phán "THẬT, vẫn đúng" hôm nay vẫn cũ được
    ngày mai — xoá nó khỏi danh sách là dựng lại đúng cái im lặng mà nhịp
    soát sinh ra để phá.
    """
    kem = [(f, i, nd, bang.get(nd.strip())) for f, i, nd in ra]
    return ([x for x in kem if x[3] is None]
            + [x for x in kem if x[3] is not None])


def so_tro_vao_hu_khong(bang, ra) -> list[str]:
    """Dòng trong SỔ không còn khớp lời khai sống nào.

    Hai nguyên nhân, và công cụ KHÔNG phân biệt được — nên nó chỉ ra chỗ,
    không phán: câu đã được sửa (tốt, việc đã xong), hoặc `dong` ghi sai
    ngay từ đầu (lời khai ấy chưa bao giờ trỏ vào đâu).
    """
    song = {nd.strip() for _, _, nd in ra}
    return sorted(d for d in bang if d not in song)


def main(tham_so: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--im", action="store_true",
                    help="chỉ in con số, dùng khi gọi từ công cụ khác")
    a = ap.parse_args(tham_so)   # None -> doc sys.argv; list -> goi duoc tu test

    ra = loi_khai_con_song()
    try:
        so = json.loads(SO_DINH_KY.read_text(encoding="utf-8"))
    except Exception:
        so = {}
    bang = da_soat(so)
    kem = xep(ra, bang)
    chua = [x for x in kem if x[3] is None]

    if not a.im:
        print("LỜI KHAI PHỦ ĐỊNH CÒN SỐNG — mở ra xem, đừng tin sẵn\n"
              + "=" * 64)
        nhom_cu = None
        f_cu = None
        for f, dong, noi_dung, dau in kem:
            nhom = dau is None
            if nhom != nhom_cu:
                print("\n--- CHƯA AI MỞ ---" if nhom
                      else "\n--- ĐÃ SOÁT (mở lại được, không phải đã xong) ---")
                nhom_cu, f_cu = nhom, None
            if f != f_cu:
                print(f"\n{f}")
                f_cu = f
            print(f"  {dong:5}  {noi_dung[:150]}")
            if dau:
                print(f"         ↳ soát {dau[0]} — {dau[1][:110]}")
        print("\n" + "=" * 64)

    print(f"{len(ra)} lời khai · {len(TAI_LIEU)} tài liệu"
          f" · chưa ai mở: {len(chua)}")
    if not a.im:
        print(f"PHẠM VI: {len(TAI_LIEU)} tài liệu, và `docs/STATE.md` CỐ Ý "
              "KHÔNG nằm trong đó —\n         nó là nhật ký chỉ-thêm, lời "
              "khai trong một BƯỚC cũ mô tả NGÀY ẤY.\n         Một con số "
              "ở đây KHÔNG nói gì về lời khai nằm trong STATE.md.")

    if not a.im:
        lac = so_tro_vao_hu_khong(bang, ra)
        if lac:
            print(f"\n{len(lac)} dòng trong sổ không còn khớp lời khai nào — "
                  "câu đã sửa, hoặc `dong` ghi sai:")
            for d in lac:
                print(f"   {d[:100]}")
        print("\nMỗi dòng là một ĐỊA CHỈ để kiểm lại, không phải một phán "
              "quyết rằng nó đã sai.\nGhi kết quả lượt soát vào "
              "docs/soat-dinh-ky.json — kèm `dong` là NGUYÊN VĂN dòng, "
              "để lượt sau\nthấy được nó đã được mở.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
