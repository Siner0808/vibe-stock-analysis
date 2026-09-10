"""CỬA NÀO ĐANG SỐNG — đọc được, không phải suy ra.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 10/09/2026 tìm ra nguyên nhân chính xác của chuyện "cửa chết" kéo
dài ba ngày. Nó KHÔNG phải "sáu cửa chết". Nó là:

  1. Thư mục dự án của mọi phiên là `C:\\Users\\cuong`, chưa bao giờ là
     repo. Bằng chứng: `~/.claude/projects/` không có thư mục nào mã hoá
     đường dẫn repo.
  2. Nên `<repo>/.claude/settings.json` — nơi khai SÁU hook — chưa bao
     giờ được nạp.
  3. Ngày 08/09 BỐN hook được chép sang `~/.claude/settings.json` bằng
     đường dẫn TUYỆT ĐỐI. Bốn cửa đó chạy bình thường suốt từ đó.
  4. **HAI hook không được chép**: `cua_bash_an_toan.py` và
     `cua_mo_phien.py`. Đó là lý do DUY NHẤT chúng chưa bao giờ chạy.

Và lỗi diễn giải đi kèm, nặng hơn cái hỏng: tài liệu dạy chạy
`python --version` rồi đọc kết quả thành phán quyết về **cả sáu** cửa.
Lệnh ấy chỉ đi qua ĐÚNG MỘT hook — `cua_bash_an_toan`, một trong hai cửa
chưa đăng ký. Ngày 10/09/2026 tôi nói "cửa chết" ba lần trong khi bốn cửa
đang chạy và có nhật ký chứng minh.

**Một phép thử đo MỘT cửa không phải phán quyết về SÁU.** Đó là lỗi 22
(*"không thấy nó chặn" ≠ "nó không chặn"*) ở một tầng khác: ở đây phép
thử có chạy, có kết quả đúng, và vẫn bị đọc rộng hơn phạm vi của nó.

CÁCH DÙNG

    ./.venv/Scripts/python.exe tools/kiem_cua_song.py
    ./.venv/Scripts/python.exe tools/kiem_cua_song.py --mot-dong

Mã thoát:  0 = mọi hook khai trong repo đều có bản toàn cục
           1 = có hook CHƯA đăng ký toàn cục → nó chỉ chạy nếu phiên mở
               ở chính thư mục repo, điều chưa từng xảy ra
           2 = CHƯA KIỂM ĐƯỢC (không đọc được một trong hai file)

Trạng thái thứ ba bắt buộc, cùng lý do như ba cổng cùng loại: một công cụ
không chạy được mà trả 0 thì chính nó là cổng xanh giả.
"""
import argparse
import json
import pathlib
import re
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
SETTINGS_REPO = GOC / ".claude" / "settings.json"
SETTINGS_TOAN_CUC = pathlib.Path.home() / ".claude" / "settings.json"

#: Lệnh hook trông như: python "<đường dẫn nào đó>/tools/x.py" [--co]
#: Hai file khai cùng một công cụ bằng hai đường dẫn khác nhau — repo
#: dùng `${CLAUDE_PROJECT_DIR:-.}`, toàn cục dùng đường tuyệt đối — nên
#: so bằng TÊN FILE cộng tham số, không so bằng nguyên chuỗi.
_MAU = re.compile(r'([A-Za-z0-9_]+\.py)"?\s*(.*)$')


def dau_van_tay(lenh: str) -> str | None:
    """Rút (tên công cụ + tham số) khỏi một chuỗi lệnh hook."""
    khop = _MAU.search(lenh.strip())
    if not khop:
        return None
    ten, tham_so = khop.group(1), " ".join(khop.group(2).split())
    return f"{ten} {tham_so}".strip()


def doc_hook(d: dict) -> set[tuple[str, str, str]]:
    """{(sự kiện, matcher, dấu vân tay)} của mọi hook kiểu `command`."""
    ra = set()
    for su_kien, nhom in (d.get("hooks") or {}).items():
        for m in nhom or []:
            matcher = str(m.get("matcher") or "")
            for hk in m.get("hooks") or []:
                if hk.get("type") != "command":
                    continue
                van_tay = dau_van_tay(str(hk.get("command") or ""))
                if van_tay:
                    ra.add((su_kien, matcher, van_tay))
    return ra


def so_sanh(repo: dict | None,
            toan_cuc: dict | None) -> tuple[int, list[tuple[str, str, str]],
                                            int]:
    """Hàm THUẦN. Trả (mã thoát, danh sách hook THIẾU, tổng hook của repo).

    "Thiếu" = khai trong settings của repo mà KHÔNG có bản tương ứng ở
    settings toàn cục. Một hook như thế chỉ chạy khi phiên được mở ở
    chính thư mục repo — điều chưa từng xảy ra lần nào.
    """
    if repo is None or toan_cuc is None:
        return 2, [], 0
    cua_repo = doc_hook(repo)
    cua_toan_cuc = doc_hook(toan_cuc)
    thieu = sorted(cua_repo - cua_toan_cuc)
    return (1 if thieu else 0), thieu, len(cua_repo)


def _doc(duong: pathlib.Path) -> dict | None:
    try:
        return json.loads(duong.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def bao_cao(mot_dong: bool = False) -> tuple[int, str]:
    ma, thieu, tong = so_sanh(_doc(SETTINGS_REPO), _doc(SETTINGS_TOAN_CUC))
    if ma == 2:
        # Tien to `CUA:` giu NGUYEN o ca ba trang thai. Mot dong bien mat
        # khoi ban tin la dung che do hong dong nay sinh ra de chan: doc
        # gia khong phan biet duoc "khong co cua nao thieu" voi "khong ai
        # hoi". CI bat duoc ngay 10/09/2026 — may khong co
        # ~/.claude/settings.json thi ban tin mat han dong trang thai.
        if mot_dong:
            return 2, "CUA: chua kiem duoc (khong doc duoc settings.json)"
        return 2, "CHUA KIEM DUOC — khong doc duoc mot trong hai settings.json"
    song = tong - len(thieu)
    if mot_dong:
        if thieu:
            ten = ", ".join(sorted({v.split()[0] for _, _, v in thieu}))
            return ma, f"CUA: {song}/{tong} song · CHUA dang ky toan cuc: {ten}"
        return ma, f"CUA: {song}/{tong} song"

    d = [f"Hook khai trong settings CUA REPO : {tong}",
         f"Trong so do co ban TOAN CUC       : {song}"]
    if not thieu:
        d.append("")
        d.append("OK — moi hook deu co ban toan cuc bang duong dan tuyet doi,")
        d.append("nen chung chay bat ke phien mo o dau.")
        return ma, "\n".join(d)
    d.append("")
    d.append(f"CHAN — {len(thieu)} hook CHUA co ban toan cuc:")
    for su_kien, matcher, van_tay in thieu:
        d.append(f"   {su_kien:<13} matcher={matcher or '-':<24} {van_tay}")
    d.append("")
    d.append("Nhung hook nay CHI chay khi phien duoc mo o chinh thu muc repo.")
    d.append("Tinh toi 10/09/2026 dieu do CHUA XAY RA lan nao — kiem bang")
    d.append("`ls ~/.claude/projects/`. Chep chung sang ~/.claude/settings.json")
    d.append("bang duong dan TUYET DOI thi chung chay bat ke phien mo o dau.")
    return ma, "\n".join(d)


def main() -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Cua nao dang song")
    ap.add_argument("--mot-dong", action="store_true", dest="mot_dong",
                    help="in gon mot dong, cho cua mo phien")
    a = ap.parse_args()
    ma, loi_nhan = bao_cao(a.mot_dong)
    print(loi_nhan)
    return ma


if __name__ == "__main__":
    sys.exit(main())
