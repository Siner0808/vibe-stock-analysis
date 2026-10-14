"""Vẽ sơ đồ "Một ngày của agent" cho README — HAI tệp SVG (nền sáng, nền tối).

    ./.venv/Scripts/python.exe tools/ve_so_do_mot_ngay.py          # ghi lại hai tệp
    ./.venv/Scripts/python.exe tools/ve_so_do_mot_ngay.py --kiem   # chỉ so, lệch thì thoát 1

VÌ SAO CÓ FILE NÀY (BƯỚC 186, 13/10/2026)
──────────────────────────────────────────
README là trang đầu tiên người lạ đọc, nên sơ đồ ở đó phải vẽ CƠ CHẾ đang chạy,
không vẽ tên gọi. Mỗi nhãn dưới đây đọc từ mã, không từ trí nhớ (lỗi 146):

  * thứ tự một lượt — `run_daily.execute_daily_scan`: kéo sổ từ Sheets (hỏng thì
    DỪNG) → `thi_hanh_dieu_kien_dung` TRƯỚC vòng quét → vòng 71 mã → nửa ĐÓNG của
    nhật ký "vì sao" (`hoan_tat_nhat_ky`) → `sheets_store.push`;
  * từng mã — `paper_runner.run_session`: bỏ nến đang dở → `fill_pending` /
    `fill_closing` ở giá MỞ CỬA → đang giữ thì `evaluate_open`, không thì
    `consider_entry`;
  * bảy cổng, ĐÚNG thứ tự trong `PaperTradingJournal.consider_entry`;
  * cách thoát — `evaluate_open`: cắt lỗ/chốt lời khớp trong phiên, đảo tín hiệu
    và giữ quá hạn thành lệnh CHỜ bán, lãi +5% dời stop về hoà vốn.

Đổi cơ chế ở một trong các hàm trên thì sửa NHÃN ở đây và chạy lại lệnh đầu.
`tests/test_so_do_mot_ngay.py` đòi hai tệp SVG khớp từng byte với hàm `ve()`, nên
sửa tay một tệp SVG sẽ đỏ — nguồn sự thật là file này.

Hai tệp chứ không một: README hiển thị ảnh qua thẻ `<img>`, nơi `currentColor`
không theo theme của GitHub; `<picture>` chọn tệp theo `prefers-color-scheme`.
"""
from __future__ import annotations

import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
THU_MUC = GOC / "docs" / "hinh"
TEN = {"sang": "mot-ngay-cua-agent-sang.svg", "toi": "mot-ngay-cua-agent-toi.svg"}

#: Bảng màu bám theo bảng màu Primer của GitHub cho từng nền.
MAU = {
    "sang": {"chu": "#1f2328", "phu": "#59636e", "nen_hop": "#f6f8fa",
             "vien": "#d1d9e0", "nhan": "#cf222e", "nen": "#ffffff"},
    "toi": {"chu": "#f0f6fc", "phu": "#9198a1", "nen_hop": "#151b23",
            "vien": "#3d444d", "nhan": "#f85149", "nen": "#0d1117"},
}

RONG, CAO = 1120, 560
PHONG = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"


def _x(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _chu(x, y, s, m, co=13, dam=False, mau=None, neo="middle"):
    trong = ' font-weight="600"' if dam else ""
    return (f'<text x="{x}" y="{y}" font-size="{co}" text-anchor="{neo}"{trong} '
            f'fill="{mau or m["chu"]}">{_x(s)}</text>')


def _so(x, y, n, m, mau=None):
    """Huy hiệu số thứ tự: vòng tròn vẽ bằng SVG (ký tự ①② đổi dạng theo phông)."""
    return (f'<circle cx="{x}" cy="{y}" r="9" fill="{mau or m["chu"]}"/>'
            f'<text x="{x}" y="{y + 4}" font-size="11" font-weight="700" '
            f'text-anchor="middle" fill="{m["nen"]}">{n}</text>')


def _hop(x, y, w, h, m, dong, vien=None, net=1.2):
    """Hộp bo góc; `dong` = [(chữ, đậm?), ...] căn giữa theo chiều dọc."""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
           f'fill="{m["nen_hop"]}" stroke="{vien or m["vien"]}" stroke-width="{net}"/>']
    buoc = 16
    y0 = y + h / 2 - (len(dong) - 1) * buoc / 2 + 4
    for i, (s, dam) in enumerate(dong):
        out.append(_chu(x + w / 2, y0 + i * buoc, s, m, 13 if dam else 11.5, dam,
                        None if dam else m["phu"]))
    return "\n".join(out)


def _ten(x1, y1, x2, y2, m, nhan=None, nx=None, ny=None, net=False, mau=None):
    """Mũi tên thẳng (hoặc gấp khúc nếu truyền list điểm qua x1=[...])."""
    mau = mau or m["phu"]
    gach = ' stroke-dasharray="5 4"' if net else ""
    out = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{mau}" '
           f'stroke-width="1.4"{gach} marker-end="url(#mui)"/>']
    if nhan:
        out.append(_chu(nx, ny, nhan, m, 11, mau=m["phu"]))
    return "\n".join(out)


def _duong(diem, m, nhan=None, nx=None, ny=None, net=False):
    d = " ".join(f"{x},{y}" for x, y in diem)
    gach = ' stroke-dasharray="5 4"' if net else ""
    out = [f'<polyline points="{d}" fill="none" stroke="{m["phu"]}" stroke-width="1.4"'
           f'{gach} marker-end="url(#mui)"/>']
    if nhan:
        out.append(_chu(nx, ny, nhan, m, 11, mau=m["phu"]))
    return "\n".join(out)


def ve(nen: str) -> str:
    m = MAU[nen]
    p = []
    a = p.append

    # ── Cột trái: sổ thật và người đọc ──────────────────────────────
    a(f'<path d="M20,58 a75,10 0 0,0 150,0 v52 a75,10 0 0,1 -150,0 z" '
      f'fill="{m["nen_hop"]}" stroke="{m["vien"]}" stroke-width="1.2"/>')
    a(f'<ellipse cx="95" cy="58" rx="75" ry="10" fill="{m["nen_hop"]}" '
      f'stroke="{m["vien"]}" stroke-width="1.2"/>')
    a(_chu(95, 92, "Sổ lệnh ảo", m, 13, True))
    a(_chu(95, 109, "Google Sheets", m, 11.5, mau=m["phu"]))
    a(_ten(95, 122, 95, 272, m, "đọc", 112, 200))
    a(_hop(20, 275, 150, 92, m, [("App Streamlit", True), ("sổ lệnh", False),
                                 ("bài học có nhãn", False), ("bản tin cuối ngày", False)]))

    # ── Hàng trên: năm chặng của MỘT lượt quét ──────────────────────
    hang = [
        (215, "Kéo sổ về", "hỏng → dừng cả lượt", None),
        (400, "Điều kiện dừng", "alpha khớp từng lệnh", m["nhan"]),
        (600, "Quét 71 mã", "từng mã, xem dưới", None),
        (785, "Nhật ký «vì sao»", "điền nửa ĐÓNG", None),
        (970, "Đẩy sổ lên", "chỉ thêm dòng mới", None),
    ]
    W = 140
    for so, (x, t, s, v) in enumerate(hang, 1):
        a(_hop(x, 50, W + (10 if x == 400 else 0), 60, m, [(t, True), (s, False)],
               vien=v, net=1.8 if v else 1.2))
        a(_so(x + 4, 52, so, m, v))
    a(_ten(170, 80, 213, 80, m, "kéo", 191, 72))
    for x1, x2 in ((355, 398), (550, 598), (740, 783), (925, 968)):
        a(_ten(x1, 80, x2, 80, m))
    a(_duong([(1040, 48), (1040, 30), (95, 30), (95, 46)], m,
             "đẩy: quyết định mới, lệnh, nhật ký", 560, 24))

    # ── Khung dưới: MỘT mã trong vòng 71 mã ─────────────────────────
    a(f'<rect x="215" y="150" width="895" height="395" rx="10" fill="none" '
      f'stroke="{m["vien"]}" stroke-width="1.2" stroke-dasharray="6 4"/>')
    a(_so(234, 166, 3, m))
    a(_chu(250, 170, "với mỗi mã", m, 12, True, neo="start"))
    a(_ten(670, 110, 670, 148, m, "lần lượt", 700, 134))

    a(_hop(235, 190, 150, 56, m, [("Giá ngày (vnstock)", True), ("bỏ nến đang dở", False)]))
    a(_hop(425, 190, 175, 56, m, [("Khớp lệnh chờ", True), ("ở giá MỞ CỬA phiên này", False)]))
    a(_ten(385, 218, 423, 218, m))
    # Hình thoi "Đang giữ mã?"
    a(f'<polygon points="690,186 750,218 690,250 630,218" fill="{m["nen_hop"]}" '
      f'stroke="{m["vien"]}" stroke-width="1.2"/>')
    a(_chu(690, 216, "Đang giữ", m, 12, True))
    a(_chu(690, 231, "mã này?", m, 12, True))
    a(_ten(600, 218, 628, 218, m))

    # Nhánh CÓ: xét thoát
    a(_hop(800, 178, 290, 84, m, [("Chấm điểm · xét thoát", True),
                                  ("cắt lỗ / chốt lời: khớp ngay trong phiên", False),
                                  ("đảo tín hiệu, giữ quá hạn: chờ bán phiên sau", False),
                                  ("lãi +5%: dời stop về hoà vốn", False)]))
    a(_ten(750, 218, 798, 218, m, "có", 772, 210))

    # Nhánh KHÔNG: chấm điểm → bảy cổng → lệnh chờ
    a(_hop(615, 300, 150, 56, m, [("6 agent chấm điểm", True), ("điểm 0–100", False)]))
    a(_ten(690, 250, 690, 298, m, "không", 712, 278))
    cong = ["1  VN-INDEX ≥ MA50", "2  dữ liệu dùng được", "3  điểm ≥ ngưỡng mua",
            "4  chưa giữ mã này", "5  có cắt lỗ + chốt lời", "6  cờ mở lệnh (do bước 2 đặt)",
            "7  trần vốn 100%"]
    a(f'<rect x="810" y="285" width="280" height="160" rx="8" fill="{m["nen_hop"]}" '
      f'stroke="{m["vien"]}" stroke-width="1.2"/>')
    a(_chu(950, 305, "7 cổng, xét theo thứ tự", m, 13, True))
    for i, s in enumerate(cong):
        mau = m["nhan"] if s.startswith("6") else m["phu"]
        a(_chu(830, 326 + i * 16, s, m, 11.5, mau=mau, neo="start"))
    a(_ten(765, 328, 808, 328, m, "điểm", 787, 320))

    a(_hop(615, 395, 150, 56, m, [("Lệnh CHỜ mua", True), ("khớp ở phiên sau", False)]))
    a(_ten(808, 423, 767, 423, m, "qua cả 7", 788, 415))
    a(_duong([(615, 423), (512, 423), (512, 248)], m,
             "phiên sau", 548, 415, net=True))

    # Mọi kết cục → một dòng quyết định
    a(_hop(235, 478, 855, 44, m, [("Mọi mã → 1 dòng quyết định: mở lệnh, đang giữ, "
                                   "hoặc bị chặn ở cổng nào", True)]))
    a(_ten(950, 445, 950, 476, m, "bị chặn: ghi lý do", 1020, 466))
    a(_ten(690, 451, 690, 476, m))
    a(_duong([(1090, 262), (1100, 262), (1100, 500), (1092, 500)], m))

    noi_dung = "\n".join(p)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {RONG} {CAO}" '
        f'width="{RONG}" height="{CAO}" role="img" font-family="{PHONG}" '
        f'aria-label="Một lượt quét: kéo sổ từ Google Sheets, xét điều kiện dừng, '
        f'quét 71 mã (khớp lệnh chờ ở giá mở cửa, xét thoát nếu đang giữ, nếu không '
        f'thì chấm điểm và qua 7 cổng thành lệnh chờ khớp ở phiên sau), điền nhật ký, '
        f'đẩy sổ lên; app đọc sổ.">\n'
        f'<defs><marker id="mui" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{m["phu"]}"/></marker></defs>\n'
        f"{noi_dung}\n</svg>\n"
    )


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else argv
    lech = []
    for nen, ten in TEN.items():
        duong = THU_MUC / ten
        moi = ve(nen)
        if "--kiem" in argv:
            cu = duong.read_text(encoding="utf-8") if duong.exists() else None
            if cu != moi:
                lech.append(ten)
            continue
        sys.path.insert(0, str(GOC / "tools"))
        from va_an_toan import ghi
        THU_MUC.mkdir(parents=True, exist_ok=True)
        ghi(duong, moi)
        print(f"ghi {duong.relative_to(GOC).as_posix()} ({len(moi)} ký tự)")
    if lech:
        print("LECH (sửa SVG tay hoặc chưa chạy lại):", ", ".join(lech))
        return 1
    if "--kiem" in argv:
        print("OK — hai tệp SVG khớp hàm ve()")
    return 0


if __name__ == "__main__":
    sys.exit(main())
