"""Soát chéo bằng sổ tay NotebookLM — DỰNG câu hỏi và GHI sổ, hai việc hay sai.

Vì sao có file này (BƯỚC 130, 27/09/2026). Mỗi BƯỚC khi đó phải hỏi sổ tay
(`SKILL.md` Quy tắc 3; từ BƯỚC 164 chỉ BƯỚC đổi luật/kết luận đo, xem cuối
docstring), và mỗi lượt hỏi có năm chỗ đã từng hỏng bằng tay:

  1. câu hỏi có XUỐNG DÒNG  -> Enter trong ô chat là GỬI, câu bị cắt làm mảnh
  2. thiếu LỐI THOÁT        -> sổ tay BỊA thay vì từ chối (BƯỚC 107)
  3. hỏi RỘNG               -> trả "không tìm thấy" sai; hỏi về MỘT kết luận
                               kèm ví dụ câu nghi ngờ thì trả đúng (25/09)
  4. quên miễn trừ câu ĐÃ CÓ DẤU -> báo hàng chục mâu thuẫn giả
  5. ghi sổ sai khuôn       -> `phan_quyet` "ĐÚNG." thay cho "THẬT." (BƯỚC 129)

`dung_cau_hoi()` đóng khuôn 1–4; `ghi()` kiểm 5 cùng các luật của
`tests/test_soat_notebooklm.py`, TRƯỚC khi chạm vào sổ.

Thêm một luật mà gác sổ không đòi: câu trả lời ÂM (`khong_tim_thay_gi`) phải
kèm `_tu_kiem_cau_am` — ngày 24/09 sổ tay trả "không tìm thấy" và bỏ sót hai
tiền lệ nằm ngay trong nguồn; BƯỚC 127 lặp lại đúng hình dạng ấy.

Dùng:

    python tools/so_tay.py hoi --buoc "BƯỚC 130" --ket-luan "..." --vi-du "..." --vi-du "..."
    python tools/so_tay.py ghi <muc.json>
    python tools/so_tay.py dem --tu 130 --den 162

`muc.json` gồm `buoc`, `cau_hoi` (NGUYÊN VĂN câu đã gửi), và hoặc
`phat_hien` (danh sách `noi_dung` · `tu_kiem` · `phan_quyet`) hoặc
`khong_tim_thay_gi: true` kèm `_tu_kiem_cau_am`. Tuỳ chọn: `_do_tuoi`.

Từ BƯỚC 164 (Quy tắc 3 thu hẹp, người dùng "Đồng ý" 08/10/2026) có thêm đường
thứ hai cho BƯỚC KHÔNG đổi luật: `muc.json` chỉ gồm `buoc` và `khong_bat_buoc_vi`
(lý do cụ thể). `ghi` hỏi MÁY (`tools/buoc_cham_luat.py`, lịch sử git) xem BƯỚC có
chạm file luật không — chạm thì TỪ CHỐI, phải hỏi thật. `dem` đếm mục đã hỏi thật
và mục có phán quyết THẬT trong một khoảng BƯỚC (số liệu của LO-TRINH.md).
Mã thoát: 0 ghi được · 1 bị từ chối (in lý do) · 2 dùng sai lệnh.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
from buoc_cham_luat import so_buoc  # noqa: E402  (BƯỚC 164: một bản cài đặt)

SO = GOC / "docs" / "soat-notebooklm.json"

#: Lối thoát — NGUYÊN VĂN câu các lượt 127–129 đã gửi.
O_THOAT = ("If you find nothing in the sources that contradicts it, "
           "say exactly that and do not invent one.")
DOI_TRA_LOI_VIET = "Answer in Vietnamese."
MIEN_TRU_DA_DANH_DAU = ("A dated record that already carries a later marker "
                        "such as a red circle or 'HẾT ĐÚNG' is not a "
                        "contradiction.")
#: Tiền tố phán quyết mà `tests/test_soat_notebooklm.py::HOP_LE` nhận.
HOP_LE = ("THẬT", "SAI", "CHƯA KIỂM ĐƯỢC")
#: Mười ba nguồn của sổ tay — nạp lại 01/10/2026 từ `main` `89fe760` (BƯỚC 150):
#: thêm hai bản lưu NGUYÊN VĂN `CLAUDE.md` / `SKILL.md` trước khi rút gọn (BƯỚC 145).
#: Thêm `LO-TRINH.md` và `QUYET-DINH-CHO.md` ở BƯỚC 166 (09/10/2026) — mười lăm nguồn:
#: sổ tay từng bỏ sót câu A4 vì lộ trình không nằm trong nguồn nào. Leader đã nạp hai
#: nguồn này vào sổ tay thật trước lượt hỏi BƯỚC 166 (mục sổ ghi 15 nguồn).
NGUON_MAC_DINH = [
    "CLAUDE.md", "MO-XE-KIEN-TRUC.md", "NGUYEN-TAC-DO-LUONG.md", "STATE.md",
    "HANDOFF.md", "SKILL.md", "references/loi-da-mac.md", "references/bay.md",
    "references/cong-thuc-chay.md", "docs/TIEU-CHI-DOC-TRUOC.md",
    "references/soat-cheo-notebooklm.md",
    "lich-su/CLAUDE-md-2026-09-30.md", "lich-su/SKILL-md-2026-09-30.md",
    "LO-TRINH.md", "QUYET-DINH-CHO.md",
]


class TuChoi(ValueError):
    """Mục sổ hoặc câu hỏi sai khuôn — không ghi gì."""


def _mot_dong(s: str) -> str:
    return " ".join(s.split())


def dung_cau_hoi(buoc: str, ket_luan: str, vi_du: list[str]) -> str:
    """Một câu hỏi MỘT DÒNG, hỏi về MỘT kết luận, kèm ví dụ câu nghi ngờ."""
    buoc, ket_luan = _mot_dong(buoc), _mot_dong(ket_luan)
    vi_du = [_mot_dong(v) for v in vi_du if v.strip()]
    if not buoc.startswith(("BƯỚC ", "ĐO ")):
        raise TuChoi(f"buoc phai mo dau bang 'BƯỚC ' hoac 'ĐO ': {buoc!r}")
    if len(ket_luan) < 40:
        raise TuChoi("ket_luan qua ngan — hoi RONG thi so tay tra 'khong tim thay' sai")
    if not vi_du:
        raise TuChoi("can it nhat mot vi du cau nghi ngo (bai hoc 25/09)")
    cau = (f"I am about to write {buoc} into docs/STATE.md: {ket_luan.rstrip('.')}. "
           "Is there ANY place in your sources that CONTRADICTS these conclusions "
           "or would become FALSE once they are written? For example: "
           f"{', '.join(vi_du)}. Quote each such sentence exactly and name the "
           f"file and heading. {MIEN_TRU_DA_DANH_DAU} {O_THOAT} {DOI_TRA_LOI_VIET}")
    assert "\n" not in cau
    return cau


#: Ô chat chọn theo NHÃN. `textarea` ĐẦU TIÊN của trang là ô "Tìm nguồn mới
#: trên web" — lỗi 113: ngày 29/09 câu hỏi BƯỚC 142 đi vào đó.
O_CHAT = 'textarea[aria-label="Hộp truy vấn"]'


def lenh_gui(cau: str) -> str:
    """Lệnh JS (cho `javascript_tool`) gửi `cau` vào ô chat của sổ tay.

    Nhúng câu bằng `json.dumps` nên nháy đơn, nháy kép, tiếng Việt đi nguyên
    văn. Nút Gửi còn khoá ngay sau sự kiện `input` (đo 29/09: bấm lúc ấy
    không gửi gì), nên chờ tới khi nó mở rồi mới bấm, và trả lại độ dài ô
    sau khi bấm — 0 nghĩa là đã gửi.
    """
    return (
        f"let kq = 'KHONG THAY O CHAT'; const ta = document.querySelector('{O_CHAT}');"
        " if (ta) {"
        " Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')"
        f".set.call(ta, {json.dumps(cau, ensure_ascii=False)});"
        " ta.dispatchEvent(new Event('input', {bubbles: true}));"
        " let el = ta, b = null;"
        " while (el && !b) { el = el.parentElement;"
        " b = el && el.querySelector('button[aria-label=\"Gửi\"]'); }"
        " for (let i = 0; i < 20 && b && b.disabled; i++)"
        " await new Promise(r => setTimeout(r, 250));"
        " kq = 'NUT GUI VAN KHOA';"
        " if (b && !b.disabled) { b.click();"
        " await new Promise(r => setTimeout(r, 500));"
        " kq = 'DA BAM GUI · o con ' + ta.value.length + ' ky tu'; } } kq")


def kiem_muc(muc: dict) -> None:
    """Ném `TuChoi` nếu mục sai khuôn. Không đọc, không ghi file."""
    buoc = str(muc.get("buoc", ""))
    if not buoc.startswith(("BƯỚC ", "ĐO ")):
        raise TuChoi(f"`buoc` sai: {buoc!r}")
    cau = str(muc.get("cau_hoi", ""))
    if "\n" in cau:
        raise TuChoi("`cau_hoi` co xuong dong — trong o chat Enter la GUI")
    if O_THOAT not in cau:
        raise TuChoi("`cau_hoi` thieu LOI THOAT nguyen van — so tay se bia (BƯỚC 107)")
    if "answer in vietnamese" not in cau.lower():
        raise TuChoi("`cau_hoi` khong doi tra loi tieng Viet")
    pds = muc.get("phat_hien") or []
    am = muc.get("khong_tim_thay_gi") is True
    if bool(pds) == am:
        raise TuChoi("khai DUNG MOT trong hai: `phat_hien` khac rong, hoac `khong_tim_thay_gi: true`")
    if am and len(str(muc.get("_tu_kiem_cau_am", "")).strip()) < 40:
        raise TuChoi("cau AM phai kem `_tu_kiem_cau_am` (>= 40 ky tu, co LENH) — so tay tung bo sot (24/09)")
    for i, pd in enumerate(pds):
        if not str(pd.get("noi_dung", "")).strip():
            raise TuChoi(f"phat_hien[{i}] thieu `noi_dung`")
        if len(str(pd.get("tu_kiem", "")).strip()) < 15:
            raise TuChoi(f"phat_hien[{i}] `tu_kiem` thieu hoac qua ngan — phai la LENH da chay")
        pq = str(pd.get("phan_quyet", "")).strip().upper()
        if not pq.startswith(HOP_LE):
            raise TuChoi(f"phat_hien[{i}] `phan_quyet` phai mo dau bang {HOP_LE}, co {pq[:20]!r}")


def dem_hoi_that(so: dict, tu: int, den: int) -> tuple[int, int]:
    """(số mục `BƯỚC n` tu<=n<=den có `cau_hoi`, số mục trong đó có phán quyết THẬT).

    HÀM THUẦN. Đếm MỤC, không đếm phát hiện: một mục có ba phát hiện THẬT vẫn
    là một mục. `cau_hoi` có mặt = đã HỎI THẬT (mục `khong_soat_vi` và mục
    `khong_bat_buoc_vi` không có ô này).
    """
    from buoc_cham_luat import co_phan_quyet_that

    hoi = that = 0
    for ten, d in so.items():
        n = so_buoc(ten)
        if n is None or not tu <= n <= den or not isinstance(d, dict):
            continue
        if not str(d.get("cau_hoi") or "").strip():
            continue
        hoi += 1
        that += co_phan_quyet_that(d)
    return hoi, that


def _ghi_khong_bat_buoc(muc: dict, so: Path, ngay: str | None, cham_luat) -> dict:
    """Đường KHÔNG hỏi: hợp lệ chỉ khi MÁY xác nhận BƯỚC không chạm file luật."""
    from buoc_cham_luat import loi_o_khong_bat_buoc

    buoc = str(muc.get("buoc", ""))
    n = so_buoc(buoc)
    if n is None:
        raise TuChoi(f"`buoc` phai co dang 'BƯỚC <so>': {buoc!r}")
    d = json.loads(so.read_text(encoding="utf-8"))
    moc = d.get("_moc_chi_hoi_khi_doi_luat")
    if not isinstance(moc, int):
        raise TuChoi("so thieu `_moc_chi_hoi_khi_doi_luat` — chua co luat thu hep")
    if n < moc:
        raise TuChoi(f"{buoc} < BƯỚC {moc}: truoc moc thu hep, MOI BUOC deu phai hoi that")
    if buoc in d["soat"]:
        raise TuChoi(f"{buoc} da co trong so — khong ghi de")
    dong = {"ngay": ngay or datetime.date.today().isoformat(),
            "khong_bat_buoc_vi": muc["khong_bat_buoc_vi"]}
    # Mang theo ca cac o thua cua `muc` (vd. `cau_hoi`) de may bat duoc noi nuoc doi.
    khac = {k: v for k, v in muc.items() if k != "buoc"}
    loi = loi_o_khong_bat_buoc({**d["soat"], buoc: {**khac, **dong}}, moc,
                               cham_luat or _file_cua_buoc_that)
    if loi:
        raise TuChoi("; ".join(loi))
    d["soat"][buoc] = dong
    so.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dong


def _file_cua_buoc_that(n: int) -> list[str]:
    from buoc_cham_luat import NEO_LICH_SU, file_cua_buoc

    return file_cua_buoc(GOC, n, neo=NEO_LICH_SU)[0]


def ghi(muc: dict, so: Path = SO, ngay: str | None = None, cham_luat=None) -> dict:
    """Kiểm rồi mới ghi. Giữ nguyên định dạng file (JSON indent 2, UTF-8).

    `cham_luat(n) -> [file đổi]` để test thay máy đọc git; mặc định đọc lịch sử thật.
    """
    if "khong_bat_buoc_vi" in muc:
        return _ghi_khong_bat_buoc(muc, so, ngay, cham_luat)
    kiem_muc(muc)
    s = so.read_text(encoding="utf-8")
    d = json.loads(s)
    buoc = muc["buoc"]
    if buoc in d["soat"]:
        raise TuChoi(f"{buoc} da co trong so — khong ghi de")
    dong = {"ngay": ngay or datetime.date.today().isoformat(),
            "nguon": list(muc.get("nguon") or NGUON_MAC_DINH)}
    if muc.get("_do_tuoi"):
        dong["_do_tuoi"] = muc["_do_tuoi"]
    dong["cau_hoi"] = muc["cau_hoi"]
    dong["o_thoat"] = O_THOAT
    if muc.get("khong_tim_thay_gi") is True:
        dong["khong_tim_thay_gi"] = True
        dong["phat_hien"] = []
        dong["_tu_kiem_cau_am"] = muc["_tu_kiem_cau_am"]
    else:
        dong["phat_hien"] = muc["phat_hien"]
    d["soat"][buoc] = dong
    so.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dong


def main(argv: list[str]) -> int:
    for _luong in (sys.stdout, sys.stderr):
        try:
            _luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if len(argv) >= 1 and argv[0] == "hoi":
        import argparse
        ap = argparse.ArgumentParser(prog="so_tay.py hoi")
        ap.add_argument("--buoc", required=True)
        ap.add_argument("--ket-luan", required=True)
        ap.add_argument("--vi-du", action="append", default=[])
        ap.add_argument("--js", action="store_true",
                        help="in LENH JS gui cau hoi vao o chat (loi 113)")
        a = ap.parse_args(argv[1:])
        try:
            cau = dung_cau_hoi(a.buoc, a.ket_luan, a.vi_du)
            print(lenh_gui(cau) if a.js else cau)
        except TuChoi as e:
            print(f"TU CHOI: {e}", file=sys.stderr)
            return 1
        return 0
    if argv and argv[0] == "dem":
        import argparse
        ap = argparse.ArgumentParser(prog="so_tay.py dem")
        ap.add_argument("--tu", type=int, required=True)
        ap.add_argument("--den", type=int, required=True)
        a = ap.parse_args(argv[1:])
        hoi, that = dem_hoi_that(json.loads(SO.read_text(encoding="utf-8"))["soat"],
                                 a.tu, a.den)
        print(f"BƯỚC {a.tu}-{a.den}: {hoi} muc da HOI THAT, {that} muc co phan quyet "
              f"THẬT ({that}/{hoi})")
        return 0
    if len(argv) == 2 and argv[0] == "ghi":
        try:
            muc = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"CHUA DOC DUOC tep muc: {e}", file=sys.stderr)
            return 2
        try:
            dong = ghi(muc)
        except TuChoi as e:
            print(f"TU CHOI: {e}", file=sys.stderr)
            return 1
        if "khong_bat_buoc_vi" in dong:
            print(f"da ghi {muc['buoc']} · KHONG hoi (may xac nhan khong cham file luat)")
            return 0
        print(f"da ghi {muc['buoc']} · {len(dong['phat_hien'])} phat hien"
              + (" · khong tim thay gi" if dong.get("khong_tim_thay_gi") else ""))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
