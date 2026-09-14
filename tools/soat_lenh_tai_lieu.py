"""Soát mọi dòng lệnh trong TÀI LIỆU bằng chính cửa gác Bash của dự án.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 14/09/2026 đo được **30 dòng lệnh** nằm trong tài liệu của repo mà
`tools/cua_bash_an_toan.py` — cửa gác Bash của chính dự án — sẽ chặn nếu
có ai gõ chúng. Mười ba dòng trong số đó là **chỉ dẫn sống**: thứ người
đọc hôm nay chép ra rồi chạy.

Chỗ đau nhất nằm ở luật `python-he-thong`. Nó tự khai nguồn:

    "CHUA CO SU CO ghi ngay - QUY UOC, chep tu `docs/HANDOFF.md` muc 1."

Mà `docs/HANDOFF.md` mục 1 vi phạm đúng luật ấy **ba lần**. Cái gác dẫn
một tài liệu ra làm nguồn cho luật của nó, và tài liệu ấy làm ngược lại
điều nó dạy. Không ai thấy, vì chưa có gì đối chiếu hai bên.

KIỂM CƠ CHẾ, KHÔNG KIỂM CHỮ
───────────────────────────
Công cụ này **gọi thẳng `cua_bash_an_toan.kiem()`** — đúng hàm cửa Bash
dùng để phán — lên từng dòng trích từ khối ```bash của tài liệu. Nên khi
luật đổi thì phép soát đổi theo; không có bản sao nào để trôi ra khỏi
nhau. Đó là bài học lỗi 38/44: đừng hỏi *văn bản có chứa chữ gì*, hãy
hỏi *cơ chế phán ra sao*.

KHÔNG CẤM, BUỘC NÓI RA
──────────────────────
Tài liệu về lỗi thì phải chép được **nguyên văn lệnh đã gây lỗi** —
sửa nó là xoá mất bằng chứng. Nên cửa thoát giống hệt `# bia-ok:`:

    # lenh-xau-ok: <ly do>

đặt trên chính dòng ấy, hoặc trên dòng chú thích liền ngay trước nó,
bên trong cùng khối lệnh. Lý do rỗng hoặc chung chung thì bị từ chối.

Sổ nhật ký chỉ-thêm (`docs/STATE.md`) được miễn ở mức FILE, khai trong
`docs/tai-lieu-nhat-ky.json` kèm lý do — mọi dòng lệnh trong đó là bản
ghi của lệnh ĐÃ CHẠY ngày ấy, không phải chỉ dẫn cho hôm nay.

Mã thoát: 0 sạch · 1 có vi phạm · 2 chưa kiểm được.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DAU = "# lenh-xau-ok:"
DAI_TOI_THIEU = 24
KHAI_NHAT_KY = "docs/tai-lieu-nhat-ky.json"

_KHOI = re.compile(r"^```(?:bash|sh|shell)\s*$")
_HET = re.compile(r"^```\s*$")


def ly_do_hop_le(ly_do: str) -> bool:
    """Lý do phải đủ dài. Hàm THUẦN.

    Bản đầu còn một tập từ chung chung (`ok`, `co y`, `vi du`…) bên cạnh
    phép đo độ dài. **Vòng lặp đột biến chứng minh nó là mã chết**: phần
    tử dài nhất trong tập là 9 ký tự, mà phép đo độ dài chạy trước với
    ngưỡng 24 — nên nhánh ấy không bao giờ quyết định được gì. Đổi nó
    thành `return True` mà cả bộ test vẫn xanh.

    Đã gỡ. Độ dài là phép đo duy nhất, đúng như ba cửa thoát cùng họ của
    dự án: `# van-ban-ok:` (20), `khong_soat_vi` (25), và dòng *"Không có
    dụng cụ vì:"* (30). Một luật nói ra được thì hơn hai luật mà một cái
    không chạy.
    """
    return len(" ".join(ly_do.split()).strip()) >= DAI_TOI_THIEU


def kiem_khai(nhat_ky: dict[str, str]) -> list[str]:
    """Tên các file được khai miễn kèm lý do KHÔNG hợp lệ. Hàm THUẦN.

    Miễn ở mức file là quyết định nặng nhất công cụ này cho phép, nên nó
    là chỗ phải soi kỹ nhất — chứ không phải chỗ tin cậy sẵn.
    """
    return [ten for ten, ly_do in sorted(nhat_ky.items())
            if not ly_do_hop_le(ly_do)]


def soat_nhieu(files, nhat_ky: dict[str, str], doc, kiem):
    """Soát nhiều file. Trả `(vi phạm, danh sách file ĐÃ soát)`.

    Trả luôn danh sách đã soát chứ không chỉ vi phạm: một lỗi làm công cụ
    bỏ qua **mọi** file cũng cho ra 0 vi phạm, và không có con số thứ hai
    thì hai trạng thái ấy không phân biệt được. Vòng lặp đột biến tìm ra
    đúng chỗ này — phát *"miễn TẤT CẢ các file"* sống sót ở bản đầu.

    `doc(duong)` trả nội dung, `kiem` là `cua_bash_an_toan.kiem`; cả hai
    truyền vào để thử được bằng mẫu dựng tay (lỗi 34).
    """
    vi_pham, da_soat = [], []
    for d in files:
        if d in nhat_ky:
            continue
        da_soat.append(d)
        vi_pham += soat_mot_file(d, doc(d), kiem)
    return vi_pham, da_soat


def _dau_tren_dong(dong: str) -> str | None:
    """Trả lý do nếu dòng mang dấu cho phép, ngược lại None."""
    i = dong.find(DAU)
    if i < 0:
        return None
    return dong[i + len(DAU):].strip()


def tach_lenh(noi_dung: str) -> list[tuple[int, str, str | None]]:
    """Mọi dòng LỆNH trong khối ```bash, kèm lý do cho phép nếu có.

    Trả `(số dòng 1-based, lệnh, lý do hoặc None)`. Dòng trống và dòng
    chú thích KHÔNG phải lệnh — nên chính dấu cho phép không tự kích
    hoạt phép soát. Hàm THUẦN, không đọc đĩa.
    """
    ra: list[tuple[int, str, str | None]] = []
    trong_khoi = False
    chu_thich_gan_nhat: str | None = None
    for so, dong in enumerate(noi_dung.split("\n"), start=1):
        tuot = dong.strip()
        if not trong_khoi:
            if _KHOI.match(tuot):
                trong_khoi = True
                chu_thich_gan_nhat = None
            continue
        if _HET.match(tuot):
            trong_khoi = False
            continue
        if not tuot:
            # Dòng trống XOÁ dấu. Nhờ vậy luật đọc đúng một câu: dấu phải
            # nằm trên chính dòng lệnh, hoặc trên dòng chú thích LIỀN NGAY
            # trước nó. Không có dòng trống nào chen vào giữa được.
            chu_thich_gan_nhat = None
            continue
        if tuot.startswith("#"):
            chu_thich_gan_nhat = tuot
            continue
        ly_do = _dau_tren_dong(dong)
        if ly_do is None and chu_thich_gan_nhat is not None:
            ly_do = _dau_tren_dong(chu_thich_gan_nhat)
        ra.append((so, tuot, ly_do))
        chu_thich_gan_nhat = None
    return ra


def soat_mot_file(duong: str, noi_dung: str, kiem) -> list[tuple]:
    """Vi phạm của một file. `kiem` là `cua_bash_an_toan.kiem`.

    Nhận `kiem` qua tham số chứ không gọi thẳng, để thử được bằng mẫu
    dựng tay — một gác chỉ chạy trên đầu vào thật thì mọi phép nới đều
    sống sót (lỗi 34).
    """
    vi_pham = []
    for so, lenh, ly_do in tach_lenh(noi_dung):
        trung = kiem(lenh)
        if not trung:
            continue
        if ly_do is not None and ly_do_hop_le(ly_do):
            continue
        vi_pham.append((duong, so, lenh, [t[0] for t in trung], ly_do))
    return vi_pham


def doc_khai_nhat_ky(goc: Path) -> dict[str, str]:
    """Các file được miễn ở mức FILE, kèm lý do. Thiếu file khai = rỗng."""
    f = goc / KHAI_NHAT_KY
    if not f.exists():
        return {}
    kh = json.loads(f.read_text(encoding="utf-8"))
    return {k: v for k, v in kh.get("nhat_ky", {}).items()}


def _file_md(goc: Path) -> list[str]:
    ra = subprocess.run(["git", "ls-files", "*.md"], cwd=str(goc),
                        capture_output=True, text=True)
    if ra.returncode != 0:
        raise RuntimeError(ra.stderr.strip() or "git ls-files that bai")
    return [d for d in ra.stdout.split("\n") if d.strip()]


def main(argv: list[str] | None = None) -> int:
    # `argv` truyen vao duoc de goi tu test. `None` giu dung nghia chuan
    # cua argparse — doc sys.argv — nen chay tay khong doi gi; test thi
    # truyen `[]` de khong nhai phai co cua pytest.
    ap = argparse.ArgumentParser(description="Soat lenh trong tai lieu")
    ap.add_argument("--goc", default=str(GOC))
    ts = ap.parse_args(argv)
    goc = Path(ts.goc).resolve()

    try:
        import cua_bash_an_toan as cb
    except Exception as e:
        print(f"CHUA KIEM DUOC — khong nap duoc cua_bash_an_toan: {e}",
              file=sys.stderr)
        return 2
    try:
        files = _file_md(goc)
    except Exception as e:
        print(f"CHUA KIEM DUOC — {e}", file=sys.stderr)
        return 2

    nhat_ky = doc_khai_nhat_ky(goc)
    hong = kiem_khai(nhat_ky)
    if hong:
        print(f"CHUA KIEM DUOC — {KHAI_NHAT_KY}: ly do khong hop le cho "
              f"{', '.join(hong)}", file=sys.stderr)
        return 2

    def doc(d: str) -> str:
        return (goc / d).read_text(encoding="utf-8", errors="replace")

    vi_pham, da_soat = soat_nhieu(files, nhat_ky, doc, cb.kiem)
    print(f"{len(files)} file .md · soat {len(da_soat)} · "
          f"{len(files) - len(da_soat)} khai la so nhat ky")
    if not vi_pham:
        print(f"OK — khong dong lenh nao trong tai lieu bi cua Bash chan")
        return 0

    print(f"\nCHAN {len(vi_pham)} dong:\n")
    for d, so, lenh, luat, ly_do in vi_pham:
        print(f"  {d}:{so}")
        print(f"      {lenh[:96]}")
        print(f"      luat: {', '.join(luat)}")
        if ly_do is not None:
            print(f"      dau CO nhung ly do khong hop le: {ly_do!r}")
    print(f"\nCach dung: sua lenh cho dung, hoac neu day la nguyen van mot")
    print(f"lenh DA GAY LOI thi ghi `{DAU} <ly do>` ngay tren dong do.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
