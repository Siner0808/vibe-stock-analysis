"""Phần MÁY của lượt soát định kỳ, chạy hằng tuần trên CI — BƯỚC 164 (giai đoạn A2).

VÌ SAO CÓ FILE NÀY
──────────────────
Người dùng chốt 16/09/2026 soát lại quy trình mỗi 2 ngày; ngày 08/10/2026 người
dùng "Đồng ý" giảm phần việc quy trình: *soát tự động mỗi tuần*. Nhịp trong
`cua_mo_phien.NHIP_SOAT_NGAY` thành 7, và phần máy làm được không cần chờ một
phiên mở lên: `.github/workflows/soat-tuan.yml` chạy file này mỗi tuần.

NÓ LÀM GÌ
─────────
1. Đọc danh sách lời khai phủ định còn sống (`soat_loi_khai_cu.loi_khai_con_song`)
   và cho biết bao nhiêu câu CHƯA AI MỞ theo `docs/soat-dinh-ky.json`.
2. Cho biết lượt soát gần nhất cách đây bao nhiêu ngày và có quá nhịp không.
3. Cho biết BƯỚC nào đã tới mốc mà chưa có dòng trong `docs/soat-notebooklm.json`.

Kết quả đi vào `$GITHUB_STEP_SUMMARY` (Markdown) và `::warning::` (chú thích).
Nó KHÔNG làm đỏ job chỉ vì có lời khai cần phán: cùng luật chuông của dự án
(`CLAUDE.md`, mục *Quét tự động*) — đỏ job vì một việc người phải làm là báo
động giả, và báo động giả dạy người ta bỏ qua chuông. Job chỉ đỏ khi MÁY hỏng
(không đọc được sổ hay tài liệu): chưa kiểm được không phải là sạch.

NÓ KHÔNG LÀM GÌ — khai thẳng
────────────────────────────
- KHÔNG phán lời khai đúng hay sai. Phần ấy là lượt soát của agent mỗi tuần
  (`SKILL.md`, mục *Nhịp soát định kỳ*): mỗi dòng in ra là một ĐỊA CHỈ để mở.
- KHÔNG chạy `tools/kiem_duong_ngoai_repo.py`: nó đo các đường NGOÀI repo trên
  máy người dùng (thư mục nhà, `~/.claude/…`); trên runner mọi đường ấy vắng
  mặt nên nó sẽ đỏ mỗi lượt (`SKILL.md` đã ghi nó cố ý không phải một cổng).
- KHÔNG gọi mạng, KHÔNG `import vnstock` hay gói nào ngoài thư viện chuẩn: job
  không cần `pip install` nên cũng không dính chuyện gói bị cách ly.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import cua_mo_phien as mp  # noqa: E402
import soat_loi_khai_cu as sk  # noqa: E402

TOI_DA_DONG_IN = 30


class ChuaDoc(RuntimeError):
    """Máy không đọc được nguồn — job phải ĐỎ (chưa kiểm được ≠ sạch)."""


def doc_nguon(goc: Path = GOC) -> dict:
    """Gom các số máy đọc được. Ném `ChuaDoc` nếu một nguồn hỏng."""
    try:
        so_dk = json.loads((goc / "docs" / "soat-dinh-ky.json").read_text(encoding="utf-8"))
        so_tay = json.loads((goc / "docs" / "soat-notebooklm.json").read_text(encoding="utf-8"))
        thieu_so = sk.buoc_chua_khai(
            (goc / "docs" / "STATE.md").read_text(encoding="utf-8"),
            so_tay["soat"], int(so_tay["_moc_buoc"]))
        ra = sk.loi_khai_con_song(goc)
    except (OSError, ValueError, KeyError) as e:
        raise ChuaDoc(f"khong doc duoc nguon soat: {e}") from e
    if not ra:
        raise ChuaDoc("loi_khai_con_song() tra RONG — may quet dang doc hut tai lieu "
                      "(mot may khong thay gi cung cho '0 loi khai')")
    bang = sk.da_soat(so_dk)
    luot = so_dk.get("lan_soat") or []
    if not luot:
        raise ChuaDoc("docs/soat-dinh-ky.json khong co luot soat nao")
    ngay_cuoi = max(dt.date.fromisoformat(x["ngay"]) for x in luot)
    return {"khoi": sk.xep(ra, bang), "so_loi_khai": len(ra),
            "ngay_cuoi": ngay_cuoi, "so_luot": len(luot),
            "thieu_so": thieu_so}


def danh_gia(nguon: dict, hom_nay: dt.date, nhip: int) -> dict:
    """HÀM THUẦN. Biến số máy đọc được thành các điều cần NÓI RA."""
    chua = [x for x in nguon["khoi"] if x[3] is None]
    tre = (hom_nay - nguon["ngay_cuoi"]).days
    return {"chua_mo": chua, "so_loi_khai": nguon["so_loi_khai"],
            "tre_ngay": tre, "qua_han": tre >= nhip, "nhip": nhip,
            "ngay_cuoi": nguon["ngay_cuoi"], "so_luot": nguon["so_luot"],
            "thieu_so": list(nguon["thieu_so"])}


def _thoat(s: str) -> str:
    """Thoát ký tự đặc biệt của chú thích GitHub Actions (`%`, CR, LF)."""
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def canh_bao(kq: dict) -> list[str]:
    """Các dòng `::warning::`. KHÔNG có `::error::` — luật chuông."""
    ra = []
    if kq["chua_mo"]:
        ra.append("::warning title=Soát tuần — lời khai chưa ai mở::" + _thoat(
            f"{len(kq['chua_mo'])}/{kq['so_loi_khai']} lời khai phủ định có nêu tên "
            f"chưa có phán quyết trong docs/soat-dinh-ky.json. Lượt soát kế tiếp "
            f"mở chúng ra (tools/soat_loi_khai_cu.py)."))
    if kq["qua_han"]:
        ra.append("::warning title=Soát tuần — quá nhịp::" + _thoat(
            f"lượt soát gần nhất {kq['ngay_cuoi'].isoformat()} cách đây "
            f"{kq['tre_ngay']} ngày (nhịp {kq['nhip']} ngày)."))
    if kq["thieu_so"]:
        ra.append("::warning title=Soát tuần — BƯỚC chưa khai sổ tay::" + _thoat(
            "chưa có dòng trong docs/soat-notebooklm.json: "
            + ", ".join(kq["thieu_so"][:8])))
    return ra


def tom_tat_md(kq: dict, hom_nay: dt.date) -> str:
    d = [f"### Soát tuần — phần máy ({hom_nay.isoformat()})", "",
         f"- Lời khai phủ định còn sống: **{kq['so_loi_khai']}**, "
         f"chưa ai mở: **{len(kq['chua_mo'])}**.",
         f"- Lượt soát gần nhất: **{kq['ngay_cuoi'].isoformat()}** "
         f"(lượt thứ {kq['so_luot']}), cách **{kq['tre_ngay']}** ngày, nhịp "
         f"{kq['nhip']} ngày — {'QUÁ NHỊP' if kq['qua_han'] else 'còn trong nhịp'}.",
         f"- BƯỚC chưa khai sổ tay: **{len(kq['thieu_so'])}**"
         + (f" ({', '.join(kq['thieu_so'][:8])})" if kq["thieu_so"] else "") + "."]
    if kq["chua_mo"]:
        d += ["", "Chưa ai mở (địa chỉ để mở ra xem, **không phải** phán quyết rằng câu đã sai):", ""]
        for f, dong, nd, _ in kq["chua_mo"][:TOI_DA_DONG_IN]:
            d.append(f"- `{f}:{dong}` — {nd[:140].replace('|', '/')}")
        if len(kq["chua_mo"]) > TOI_DA_DONG_IN:
            d.append(f"- … và {len(kq['chua_mo']) - TOI_DA_DONG_IN} câu nữa")
    d += ["", "**Không nằm trong job này:** phán quyết đúng/sai từng lời khai (lượt soát của "
          "agent), và `tools/kiem_duong_ngoai_repo.py` (đo đường NGOÀI repo trên máy người "
          "dùng; trên runner nó đỏ mỗi lượt)."]
    return "\n".join(d) + "\n"


def main(argv: list[str] | None = None) -> int:
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tom-tat", help="tệp để NỐI Markdown vào (vd. $GITHUB_STEP_SUMMARY)")
    a = ap.parse_args(argv)
    hom_nay = dt.date.today()
    try:
        kq = danh_gia(doc_nguon(), hom_nay, mp.NHIP_SOAT_NGAY)
    except ChuaDoc as e:
        print(f"::error title=Soát tuần — máy chưa đọc được::{_thoat(str(e))}")
        return 2
    md = tom_tat_md(kq, hom_nay)
    if a.tom_tat:
        with open(a.tom_tat, "a", encoding="utf-8") as f:
            f.write(md)
    else:
        print(md)
    for dong in canh_bao(kq):
        print(dong)
    print(f"soat-tuan: {kq['so_loi_khai']} loi khai · chua ai mo {len(kq['chua_mo'])}"
          f" · luot cuoi {kq['tre_ngay']} ngay truoc · thieu so {len(kq['thieu_so'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
