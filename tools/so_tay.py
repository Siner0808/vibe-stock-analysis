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
    python tools/so_tay.py chia-state --bam <commit> [--js]

BƯỚC 246 (30/10/2026) — làm việc với trang bằng LỆNH JS do máy dựng (leader dán vào trình
duyệt; mọi lệnh ĐỒNG BỘ, không hẹn giờ — khung ẩn bóp `setTimeout`, xem `LAN_CHUP_GIONG`):

    python tools/so_tay.py lay-nhan                  # JS đọc nhãn nguồn `<tệp> @<băm>`
    python tools/so_tay.py do-tuoi <tệp nhãn> [--tom-tat]   # nhãn so với git, KHÔNG hỏi mô hình
    python tools/so_tay.py xoa-nhat-ky --buoc 1..4   # JS xoá nhật ký chat, đọc hộp xác nhận
    python tools/so_tay.py hoi … --js                # JS ĐIỀN câu hỏi (từ chối > 3.800 UTF-16)
    python tools/so_tay.py bam-gui --dai N           # JS bấm Gửi (sau ~1 giây)
    python tools/so_tay.py chup --truoc N            # JS chụp câu trả lời; lặp tới xong:true
    python tools/so_tay.py kiem-tra-loi <tệp> --sha256 <băm của trang>   # bắt tay

`ghi` nhận thêm `tra_loi_tep` + `tra_loi_sha256` + `trich_dan_tep` (bắt tay, lưu `tra_loi`)
và `nhan_nguon_tep` (sinh `nguon` và `_do_tuoi` từ git). Cách làm đầy đủ:
`.claude/skills/quy-trinh-lam-viec/references/soat-cheo-notebooklm.md`.

`muc.json` gồm `buoc`, `cau_hoi` (NGUYÊN VĂN câu đã gửi), và hoặc
`phat_hien` (danh sách `noi_dung` · `tu_kiem` · `phan_quyet`) hoặc
`khong_tim_thay_gi: true` kèm `_tu_kiem_cau_am`. Tuỳ chọn: `_do_tuoi`.

Từ BƯỚC 164 (Quy tắc 3 thu hẹp, người dùng "Đồng ý" 08/10/2026) có thêm đường
thứ hai cho BƯỚC KHÔNG đổi luật: `muc.json` chỉ gồm `buoc` và `khong_bat_buoc_vi`
(lý do cụ thể). `ghi` hỏi MÁY (`tools/buoc_cham_luat.py`, lịch sử git) xem BƯỚC có
chạm file luật không — chạm thì TỪ CHỐI, phải hỏi thật. `dem` đếm mục đã hỏi thật
và mục có phán quyết THẬT trong một khoảng BƯỚC (số liệu của LO-TRINH.md).
Mã thoát: 0 ghi được · 1 bị từ chối (in lý do) · 2 dùng sai lệnh.

Từ BƯỚC 202 (16/10/2026, người dùng chọn "Dán 3 phần, repo giữ nguyên"):
`docs/STATE.md` KHÔNG nạp vào sổ tay bằng URL nữa. Nạp bằng URL thì bộ nạp lưu
đủ tệp (trình xem nguồn hiện tới BƯỚC cuối) nhưng MÔ HÌNH chỉ đọc được một khúc
đầu, và nạp lại dừng đúng chỗ cũ. `chia-state` cắt tệp tại các dòng `## BƯỚC n`
thành khúc <= `CO_PHAN_TOI_DA` để DÁN (ô "Văn bản đã sao chép");
`--js` in lệnh JS tải tệp ở đúng commit, kiểm số byte rồi cắt sẵn từng khúc.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import subprocess
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


def lenh_dien_cau(cau: str, giu_lich_su: bool = False) -> str:
    """Lệnh JS (cho `javascript_tool`) ĐIỀN `cau` vào ô chat của sổ tay. Chưa gửi.

    Nhúng câu bằng `json.dumps` nên nháy đơn, nháy kép, tiếng Việt đi nguyên văn. Nút Gửi còn
    khoá ngay sau sự kiện `input` (đo 29/09: bấm lúc ấy không gửi gì) và trang không cho hẹn giờ
    (xem `LAN_CHUP_GIONG`), nên gửi là LỆNH THỨ HAI, `lenh_bam_gui`, chạy sau ~1 giây. Kết quả
    in độ dài ô (đưa nguyên cho `lenh_bam_gui`) và số trả lời đã có TRƯỚC khi gửi (đưa cho
    `lenh_chup_tra_loi`). TỪ CHỐI dựng lệnh khi câu dài hơn `TRAN_GUI` đơn vị UTF-16: nút Gửi
    khoá từ 3.901 mà không báo gì. Lệnh JS cũng TỪ CHỐI điền khi nhật ký chat còn trả lời
    (xoá nhật ký là bất đồng bộ — leader đo 30/10: bước 4 ngay sau bước 3 còn thấy 1), trừ khi
    `giu_lich_su` (cố ý hỏi tiếp trong cùng cuộc trò chuyện).
    """
    n = _dai16(cau)
    if n > TRAN_GUI:
        raise TuChoi(f"cau hoi dai {n} don vi UTF-16 > tran {TRAN_GUI} (nut Gui khoa tu "
                     f"{TRAN_NUT_GUI_DO + 1}, do 30/10/2026) — rut ngan ket luan hoac bot vi du")
    return (
        f"let kq = 'KHONG THAY O CHAT'; const ta = document.querySelector('{O_CHAT}');"
        f" const truoc = document.querySelectorAll({json.dumps(O_TRA_LOI)}).length;"
        f" if (ta && truoc > 0 && {'false' if giu_lich_su else 'true'}) kq = 'TU CHOI · nhat ky chat con ' + truoc"
        " + ' tra loi: xoa nhat ky (xoa-nhat-ky) va cho buoc 4 = 0 truoc khi dien'; else if (ta) {"
        " Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')"
        f".set.call(ta, {json.dumps(cau, ensure_ascii=False)});"
        " ta.dispatchEvent(new Event('input', {bubbles: true}));"
        " kq = 'DA DIEN · o co ' + ta.value.length + ' ky tu · tra loi truoc: ' + truoc"
        " + ' · doi 1 giay roi chay bam-gui --dai ' + ta.value.length; } kq")


def lenh_bam_gui(dai: int) -> str:
    """Lệnh JS BẤM Gửi — chỉ khi ô chat có đúng `dai` đơn vị UTF-16 và nút Gửi đã mở khoá.

    Trang có HAI nút `Gửi`; nút số 0 luôn khoá (ô "Nghiên cứu nhanh"), nút của ô chat là nút ở
    gần ô nhất khi leo cây từ ô chat (đo 30/10/2026). Khoá thì trả `NUT GUI VAN KHOA` và không
    bấm gì: chạy lại sau ~1 giây.
    """
    if not isinstance(dai, int) or isinstance(dai, bool) or dai < 1:
        raise TuChoi(f"`dai` phai la so nguyen >= 1: {dai!r}")
    return (
        f"let kq = 'KHONG THAY O CHAT'; const ta = document.querySelector('{O_CHAT}');"
        " if (ta) { let el = ta, b = null;"
        " while (el && !b) { el = el.parentElement;"
        " b = el && el.querySelector('button[aria-label=\"Gửi\"]'); }"
        f" if (ta.value.length !== {dai}) kq = 'TU CHOI · o chat co ' + ta.value.length + ' ky tu, can {dai}';"
        " else if (!b) kq = 'KHONG THAY NUT GUI';"
        " else if (b.disabled) kq = 'NUT GUI VAN KHOA · chay lai sau 1 giay';"
        f" else {{ b.click(); kq = 'DA BAM GUI · o co {dai} ky tu luc bam'; }} }} kq")

# ── BƯỚC 246: sổ tay chuyên nghiệp hơn — chặn gửi quá dài, xoá lịch sử có đọc hộp xác nhận,
# ── chờ trả lời xong, bắt tay SHA-256, đo độ tươi bằng NHÃN nguồn ────────────────────────────

#: Nút Gửi của ô chat khoá khi chuỗi JS dài >= 3901 đơn vị UTF-16 (ĐO 30/10/2026, leader,
#: bisection trên các tiền tố của một câu 4.423 ký tự; không có bộ đếm hay `maxlength`).
TRAN_NUT_GUI_DO = 3_900
#: Trần của CÔNG CỤ: chừa 100 đơn vị. Quá thì `lenh_dien_cau` từ chối dựng lệnh.
TRAN_GUI = 3_800
#: Câu trả lời nằm ở đây (đo 30/10/2026); `.individual-message` gồm cả câu hỏi lẫn trả lời
#: nên KHÔNG dùng để đếm hay đọc trả lời nữa.
O_TRA_LOI = ".to-user-container .message-text-content"
MUC_MENU_XOA = "Xoá nhật ký trò chuyện"
#: Câu trong hộp xác nhận — công cụ chỉ bấm "Xoá" khi hộp mang ĐÚNG câu này.
CAU_XAC_NHAN_XOA = "Bạn sắp xoá toàn bộ nhật ký trò chuyện của sổ ghi chú này"
NUT_XOA = "Xoá"
#: LỆNH JS CỦA MODULE NÀY KHÔNG HẸN GIỜ. Leader đo 30/10/2026: khi cửa sổ Claude không hiện,
#: `document.hidden` là true và trình duyệt bóp `setTimeout` đến mức MỘT `await setTimeout(750)`
#: không xong trong 45 s (công cụ giết JS ở 45 s); `await crypto.subtle.digest` thì xong. Nên chờ
#: là việc của người gọi: mỗi lệnh đọc/bấm MỘT lần rồi trả về, "xong" là CHUỖI lần chụp giống nhau.
#: "Xong" = 3 lần chụp liên tiếp cùng sha256, và lần đầu cách lần cuối >= 2 giây (`Date.now()`
#: chạy bình thường khi ẩn).
LAN_CHUP_GIONG = 3
KHOANG_CHUP_TOI_THIEU_MS = 2_000
#: Dòng trạng thái khi sổ tay đang nghĩ ("Analyzing the documents...\nexpand_more") ngắn hơn
#: ngần này và kết thúc bằng `expand_more`; câu trả lời thật bắt đầu "Thoughts\nexpand_more\n".
DO_DAI_TRANG_THAI = 200

_JS_HAM = r"""  const hien = e => e.getClientRects().length > 0;
  const gon = s => (s || '').normalize('NFC').replace(/\s+/g, ' ').trim();
  const dem = () => document.querySelectorAll(@@O_TRA_LOI@@).length;
"""

#: Bốn BƯỚC xoá nhật ký, mỗi bước một lệnh ĐỒNG BỘ; người gọi chờ ~1 giây giữa hai bước để trang vẽ.
JS_XOA_BUOC = {
    1: r"""(() => {
@@HAM@@  const nut = [...document.querySelectorAll('button')].filter(hien);
  const i = nut.findIndex(b => /chia sẻ|share/i.test((b.getAttribute('aria-label') || '') + ' ' + gon(b.innerText)));
  let bam = i >= 0 ? nut[i + 1] : null;
  if (!bam || !/more_vert/.test(bam.innerText || ''))
    bam = nut.find(b => gon(b.innerText) === 'more_vert' && !b.getAttribute('aria-label') && b.getBoundingClientRect().top < 100);
  if (!bam) return 'TU CHOI · khong thay nut menu tren thanh dau · cac nut o thanh dau: ' + JSON.stringify(nut.filter(b => b.getBoundingClientRect().top < 100).map(b => [b.getAttribute('aria-label'), gon(b.innerText).slice(0, 20)]));
  bam.click();
  return 'DA BAM NUT MENU · tra loi hien co ' + dem() + ' · doi 1 giay roi chay buoc 2';
})()""",
    2: r"""(() => {
@@HAM@@  const muc = [...document.querySelectorAll('[role="menuitem"], button')]
    .filter(e => hien(e) && gon(e.innerText).includes(@@MUC@@))
    .sort((a, b) => gon(a.innerText).length - gon(b.innerText).length)[0];
  if (!muc) return 'TU CHOI · menu khong co muc "Xoá nhật ký trò chuyện" (chua mo menu? chay lai buoc 1)';
  muc.click();
  return 'DA CHON MUC XOA NHAT KY · doi 1 giay roi chay buoc 3';
})()""",
    3: r"""(() => {
@@HAM@@  const hop = [...document.querySelectorAll('[role="dialog"]')].filter(d => hien(d) && gon(d.innerText).includes(@@CAU@@));
  if (!hop.length) return 'TU CHOI · khong co hop thoai HIEN mang DUNG cau xac nhan · cac hop thoai: ' + JSON.stringify([...document.querySelectorAll('[role="dialog"]')].map(d => [hien(d), gon(d.innerText).slice(0, 120)]));
  const xoa = [...hop[0].querySelectorAll('button')].filter(b => gon(b.innerText) === @@NUT@@);
  if (xoa.length !== 1) return 'TU CHOI · hop thoai co ' + xoa.length + ' nut "Xoá" (can dung 1)';
  const truoc = dem();
  xoa[0].click();
  return 'DA BAM XOA · tra loi truoc ' + truoc + ' · doi 1 giay roi chay buoc 4';
})()""",
    4: r"""(() => {
@@HAM@@  const con = dem();
  return 'tra loi con ' + con + (con === 0 ? ' · XONG, co the gui' : ' · CHUA 0: xoa khong dong bo, chay lai buoc 4 cho toi khi = 0 (dung gui khi con > 0)');
})()""",
}

#: Một lần CHỤP câu trả lời mới nhất. Trạng thái giữa hai lần chụp nằm trong `window.__chupSoTay`.
JS_CHUP_TRA_LOI = r"""await (async () => {
  const TRUOC = @@TRUOC@@;
  const ds = document.querySelectorAll(@@O_TRA_LOI@@);
  const cuoi = ds.length ? ds[ds.length - 1] : null;
  const moi = ds.length > TRUOC && !!cuoi;
  const t = moi ? cuoi.innerText : '';
  const dang_nghi = !t.trim() || (t.trim().length < @@DO_DAI@@ && /expand_more\s*$/.test(t));
  const ra = {so_tra_loi: ds.length, truoc: TRUOC, moi: moi, dang_nghi: dang_nghi, xong: false, giong: 0, khoang_ms: 0, dai16: t.length};
  if (!moi || dang_nghi) { window.__chupSoTay = null; ra.dau = t.slice(0, 80); return ra; }
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t));
  const sha = [...new Uint8Array(h)].map(x => x.toString(16).padStart(2, '0')).join('');
  const nay = Date.now(), cu = window.__chupSoTay;
  const chay = (cu && cu.truoc === TRUOC && cu.sha === sha) ? cu : {truoc: TRUOC, sha: sha, dem: 0, t0: nay};
  chay.dem++;
  window.__chupSoTay = chay;
  ra.sha256 = sha; ra.giong = chay.dem; ra.khoang_ms = nay - chay.t0;
  ra.xong = chay.dem >= @@GIONG@@ && ra.khoang_ms >= @@KHOANG@@;
  if (ra.xong) {
    ra.text = t;
    ra.trich_dan = [...cuoi.querySelectorAll('button.citation-marker span[aria-label]')]
      .map(s => s.getAttribute('aria-label'))
      .map(a => { const m = a.match(/^(\d+): ([\s\S]*)$/); return m ? {n: +m[1], nguon: m[2]} : {n: null, nguon: a}; });
    const vh = c => (c < 32 && c !== 10) || c === 127 || c === 160 || (c >= 0x200b && c <= 0x200f)
      || c === 0x2028 || c === 0x2029 || (c >= 0x202a && c <= 0x202e) || c === 0x2060 || c === 0xfeff;
    ra.vo_hinh = [];
    for (let i = 0; i < t.length && ra.vo_hinh.length < 50; i++) {
      const c = t.charCodeAt(i);
      if (vh(c)) ra.vo_hinh.push([i, c.toString(16)]);
    }
  }
  return ra;
})()"""

JS_LAY_NHAN = r"""(() => {
  const d = [...new Set([...document.querySelectorAll('button[aria-label]')].map(b => b.getAttribute('aria-label')).filter(a => /@[0-9a-f]{7}/.test(a)))];
  return d.length + ' nhan\n' + d.join('\n');
})()"""


def _dien(mau: str, **tham_so) -> str:
    """Điền `@@TÊN@@` bằng JSON của giá trị — chuỗi tiếng Việt đi nguyên văn."""
    for k, v in tham_so.items():
        mau = mau.replace(f"@@{k}@@", json.dumps(v, ensure_ascii=False))
    if "@@" in mau:
        raise TuChoi(f"mau JS con cho trong: {mau[mau.index('@@'):][:30]!r}")
    return mau


def lenh_xoa_nhat_ky(buoc: int) -> str:
    """Lệnh JS ĐỒNG BỘ cho MỘT trong bốn bước xoá nhật ký chat của sổ tay — và CHỈ nhật ký chat.

    1 bấm nút ⋮ ở thanh đầu · 2 chọn mục `Xoá nhật ký trò chuyện` · 3 đọc hộp xác nhận và bấm
    "Xoá" · 4 đếm trả lời còn lại. Người gọi chờ ~1 giây giữa hai bước (không hẹn giờ trong
    trang: xem `LAN_CHUP_GIONG`).

    Người dùng cho phép thường trực (29/10/2026: *"Cho phép, đọc lại hộp xác nhận trước khi
    bấm (Recommended)"*). "Đọc lại hộp" là mã, không phải lời dặn: bước 3 đọc MỌI hộp thoại,
    chọn cái HIỆN và mang đúng `CAU_XAC_NHAN_XOA`, chỉ bấm nút "Xoá" của CÁI ĐÓ; hộp khác (xoá
    nguồn, xoá sổ tay…) thì trả `TU CHOI` và không bấm gì. Hộp thoại xuất hiện hai lần trong
    DOM và một hộp chọn emoji ẩn cũng mang `role=dialog` (đo 30/10/2026), nên lọc theo chữ và độ hiện.
    """
    if buoc not in JS_XOA_BUOC:
        raise TuChoi(f"buoc xoa nhat ky phai la {sorted(JS_XOA_BUOC)}: {buoc!r}")
    mau = JS_XOA_BUOC[buoc].replace("@@HAM@@", _JS_HAM)
    return _dien(mau, O_TRA_LOI=O_TRA_LOI, MUC=MUC_MENU_XOA, CAU=CAU_XAC_NHAN_XOA, NUT=NUT_XOA)


def lenh_chup_tra_loi(truoc: int) -> str:
    """Lệnh JS CHỤP câu trả lời mới nhất một lần: `{xong, giong, khoang_ms, sha256, …}`.

    `truoc` = số trả lời đã có TRƯỚC khi gửi (`lenh_dien_cau` in nó); chỉ tin phần tử trả lời
    thứ `truoc + 1` trở đi, nên một câu trả lời CŨ trong lịch sử không bị nhận nhầm. Không hẹn giờ:
    người gọi chạy lại cho tới khi `xong: true` (`LAN_CHUP_GIONG` lần chụp liên tiếp cùng sha256,
    cách nhau >= `KHOANG_CHUP_TOI_THIEU_MS`). Chỉ khi xong mới trả `text`, `trich_dan`, `vo_hinh`.
    """
    if not isinstance(truoc, int) or isinstance(truoc, bool) or truoc < 0:
        raise TuChoi(f"`truoc` phai la so nguyen >= 0: {truoc!r}")
    return _dien(JS_CHUP_TRA_LOI, TRUOC=truoc, O_TRA_LOI=O_TRA_LOI, DO_DAI=DO_DAI_TRANG_THAI,
                 GIONG=LAN_CHUP_GIONG, KHOANG=KHOANG_CHUP_TOI_THIEU_MS)


def lenh_lay_nhan() -> str:
    """Lệnh JS đọc nhãn mọi nguồn (`<tệp> @<băm 7>`) — tab Nguồn phải đang mở."""
    return JS_LAY_NHAN


# ── bắt tay SHA-256 ───────────────────────────────────────────────────────────

def kiem_tra_loi(noi_dung: bytes, sha_trang: str) -> dict:
    """Từ chối nếu tệp trả lời KHÁC câu trang đã băm. Trả `{sha256, dai16}`.

    Chép lại bằng tay một câu trả lời dài mất âm thầm ký tự vô hình (`\\t\\u200b` trong công
    thức toán, 30/10/2026); băm SHA-256 của `innerText` do TRANG tính là nhân chứng.
    """
    sha_trang = sha_trang.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha_trang):
        raise TuChoi(f"sha256 cua trang phai la 64 ky tu hex: {sha_trang[:20]!r}")
    sha = hashlib.sha256(noi_dung).hexdigest()
    if sha != sha_trang:
        raise TuChoi(f"BAT TAY LECH: tep {len(noi_dung)} byte co sha256 {sha[:16]}…, trang bam "
                     f"{sha_trang[:16]}… — tep phai la ban sao NGUYEN VAN `text` (UTF-8, xuong dong LF), "
                     "khong chep lai bang tay")
    try:
        van = noi_dung.decode("utf-8")
    except UnicodeDecodeError as e:
        raise TuChoi(f"tep tra loi khong phai UTF-8: {e}") from e
    return {"sha256": sha, "dai16": _dai16(van)}


NHAN_TRICH_DAN = re.compile(r"(\d+): (\S.*)")


def doc_trich_dan(van_ban: str) -> list[dict]:
    """Mỗi dòng `<n>: <nhãn nguồn>` -> `{n, nguon}`, giữ thứ tự và bản lặp như trang."""
    ra = []
    for i, d in enumerate(van_ban.splitlines(), 1):
        if not d.strip():
            continue
        m = NHAN_TRICH_DAN.fullmatch(d.strip())
        if not m:
            raise TuChoi(f"tep trich dan dong {i} sai khuon '<n>: <nhan nguon>': {d[:60]!r}")
        ra.append({"n": int(m[1]), "nguon": m[2].strip()})
    return ra


def _dung_tra_loi(muc: dict) -> dict | None:
    """`tra_loi` của mục sổ từ BA ô: tệp trả lời, sha256 của trang, tệp trích dẫn."""
    o = ("tra_loi_tep", "tra_loi_sha256", "trich_dan_tep")
    co = [k for k in o if muc.get(k)]
    if not co:
        return None
    if len(co) != len(o):
        raise TuChoi(f"khai du ca ba o {o} hoac khong o nao; thieu {[k for k in o if k not in co]}")
    try:
        noi = Path(muc["tra_loi_tep"]).read_bytes()
        td = Path(muc["trich_dan_tep"]).read_text(encoding="utf-8")
    except OSError as e:
        raise TuChoi(f"khong doc duoc tep: {e}") from e
    kq = kiem_tra_loi(noi, muc["tra_loi_sha256"])
    return {"sha256": kq["sha256"], "dai16": kq["dai16"], "trich_dan": doc_trich_dan(td)}


# ── độ tươi bằng NHÃN nguồn ────────────────────────────────────────────────────

NHAN_NGUON = re.compile(
    r"(?P<tep>\S+) @(?P<bam>[0-9a-f]{7,40})"
    r"(?: phan(?P<k>\d+)/(?P<n>\d+)(?: \(BUOC (?P<a>\d+)-(?P<b>\d+)\))?)?")
#: Thư mục thử khi đổi tên nhãn thành đường dẫn repo: gốc, `docs/`, thư mục skill.
THU_MUC_NGUON = ("", "docs/", ".claude/skills/quy-trinh-lam-viec/")
TEP_STATE = "docs/STATE.md"


class KhongKiemDuoc(RuntimeError):
    """Git không trả lời — không được báo "tươi" khi chưa đo được."""


def _git_that(*args: str) -> tuple[int, str]:
    r = subprocess.run(["git", "-C", str(GOC), *args], capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def doc_nhan(van_ban: str) -> tuple[list[str], list[str]]:
    """(nhãn đúng khuôn, dòng LẠ). Bỏ dòng trống và dòng đầu `<n> nhan` của `lenh_lay_nhan`."""
    dung, la = [], []
    for d in van_ban.splitlines():
        d = d.strip()
        if not d or re.fullmatch(r"\d+ nhan", d):
            continue
        (dung if NHAN_NGUON.fullmatch(d) else la).append(d)
    return dung, la


def _doi_ten(ten: str, da_theo_doi: set[str]) -> list[str]:
    """Các đường dẫn repo khớp tên nhãn (`STATE.md` -> `docs/STATE.md`). Suy ra, không bảng gõ tay."""
    return [p for pre in THU_MUC_NGUON if (p := pre + ten) in da_theo_doi]


def do_tuoi(nhan: list[str], la: list[str] = (), git=_git_that, so_voi: str = "HEAD",
            ky_vong: list[str] = NGUON_MAC_DINH, co_phan: int | None = None) -> dict:
    """So từng nhãn `<tệp> @<băm>` với git. KHÔNG hỏi mô hình.

    Mỗi nguồn: `TUOI` (tệp không đổi giữa băm và `so_voi`) · `CU` · `KHONG_RO_BAM` (băm không
    phải commit của repo này) · `KHONG_THAY_TEP` / `MO_HO` (nhãn không đổi được ra đúng một tệp
    theo dõi). `docs/STATE.md` dán thành khúc: nhãn `phanK/N` so khúc K ở băm với khúc K ở
    `so_voi` (cùng `chia_state`), nên khúc đầu không bị coi cũ chỉ vì cuối tệp dài thêm.
    Thiếu = tệp của `ky_vong` không có nhãn nào (STATE: khúc 1..N' không có nhãn).
    """
    co_phan = co_phan or CO_PHAN_TOI_DA
    rc, ls = git("ls-files")
    rc2, ma = git("rev-parse", "--short=7", so_voi)
    if rc or rc2:
        raise KhongKiemDuoc("git ls-files / rev-parse that bai")
    theo_doi = set(ls.splitlines())
    ma = ma.strip()
    kho: dict[tuple[str, str], list] = {}

    def khuc(rev: str) -> list[str]:
        if ("khuc", rev) not in kho:
            r, van = git("show", f"{rev}:{TEP_STATE}")
            if r:
                raise KhongKiemDuoc(f"git show {rev}:{TEP_STATE} that bai")
            try:
                kho[("khuc", rev)] = [van[a:b] for a, b in chia_state(van, co_phan)]
            except TuChoi as e:
                raise KhongKiemDuoc(str(e)) from e
        return kho[("khuc", rev)]

    ra, da_co, khuc_co = [], set(), set()
    for dong in nhan:
        m = NHAN_NGUON.fullmatch(dong)
        ung = _doi_ten(m["tep"], theo_doi)
        d = {"nhan": dong, "tep": ung[0] if len(ung) == 1 else None}
        if len(ung) != 1:
            d["trang_thai"] = "MO_HO" if ung else "KHONG_THAY_TEP"
        elif git("rev-parse", "--verify", "--quiet", m["bam"] + "^{commit}")[0]:
            d["trang_thai"] = "KHONG_RO_BAM"
        elif ung[0] == TEP_STATE and m["k"]:
            k = int(m["k"])
            khuc_co.add(k)
            moi, cu = khuc(so_voi), khuc(m["bam"])
            tuoi = k <= len(moi) and k <= len(cu) and moi[k - 1] == cu[k - 1]
            d["trang_thai"] = "TUOI" if tuoi else "CU"
        else:
            r = git("diff", "--quiet", m["bam"], so_voi, "--", ung[0])[0]
            if r not in (0, 1):
                raise KhongKiemDuoc(f"git diff {m['bam']} {so_voi} -- {ung[0]} ma {r}")
            d["trang_thai"] = "TUOI" if r == 0 else "CU"
        if d["tep"]:
            da_co.add(d["tep"])
        ra.append(d)

    thieu = []
    for ten in ky_vong:
        ung = _doi_ten(ten, theo_doi)
        if len(ung) != 1:
            thieu.append(f"{ten} (khong doi duoc ra dung mot tep theo doi)")
        elif ung[0] == TEP_STATE:
            if khuc_co or ung[0] not in da_co:
                thieu += [f"{TEP_STATE} phan{k}/{len(khuc(so_voi))}"
                          for k in range(1, len(khuc(so_voi)) + 1) if k not in khuc_co]
        elif ung[0] not in da_co:
            thieu.append(ung[0])
    xau = [d for d in ra if d["trang_thai"] != "TUOI"]
    return {"so_voi": so_voi, "ma_so_voi": ma, "nguon": ra, "thieu": thieu, "la": list(la),
            "ket_luan": "TUOI" if not (xau or thieu or la) else "CU"}


def tom_tat_do_tuoi(kq: dict) -> str:
    """MỘT dòng cho ô `_do_tuoi` — sinh từ kết quả đo, không gõ tay, không do mô hình nói."""
    xau = [f"{d['nhan']} = {d['trang_thai']}" for d in kq["nguon"] if d["trang_thai"] != "TUOI"]
    return (f"ĐO BẰNG NHÃN, không hỏi mô hình (`tools/so_tay.py do-tuoi`, so với {kq['so_voi']} "
            f"{kq['ma_so_voi']}): {len(kq['nguon'])} nguồn, {len(kq['nguon']) - len(xau)} tươi"
            + (f"; không tươi: {'; '.join(xau)}" if xau else "")
            + (f"; THIẾU: {'; '.join(kq['thieu'])}" if kq["thieu"] else "")
            + (f"; nhãn LẠ: {'; '.join(kq['la'])}" if kq["la"] else "")
            + f" — kết luận {kq['ket_luan']}.")


def _dung_nguon_va_do_tuoi(muc: dict, git) -> tuple[list[str], str] | None:
    """Từ `nhan_nguon_tep` -> (`nguon`, `_do_tuoi`). Khai tay `nguon`/`_do_tuoi` kèm nó thì từ chối."""
    if not muc.get("nhan_nguon_tep"):
        return None
    if muc.get("nguon") is not None or muc.get("_do_tuoi"):
        raise TuChoi("`nhan_nguon_tep` sinh `nguon` va `_do_tuoi`: khong khai tay hai o do cung luc")
    try:
        van = Path(muc["nhan_nguon_tep"]).read_text(encoding="utf-8")
    except OSError as e:
        raise TuChoi(f"khong doc duoc tep nhan nguon: {e}") from e
    nhan, la = doc_nhan(van)
    if not nhan:
        raise TuChoi("tep nhan nguon khong co nhan nao — tab Nguon chua mo? (doc 0 nguon la MAU HONG)")
    try:
        kq = do_tuoi(nhan, la, git or _git_that)
    except KhongKiemDuoc as e:
        raise TuChoi(f"CHUA KIEM DUOC do tuoi: {e}") from e
    return nhan, tom_tat_do_tuoi(kq)


def kiem_muc(muc: dict) -> None:
    """Ném `TuChoi` nếu mục sai khuôn. Không đọc, không ghi file."""
    buoc = str(muc.get("buoc", ""))
    if not buoc.startswith(("BƯỚC ", "ĐO ")):
        raise TuChoi(f"`buoc` sai: {buoc!r}")
    cau = str(muc.get("cau_hoi", ""))
    if "\n" in cau:
        raise TuChoi("`cau_hoi` co xuong dong — trong o chat Enter la GUI")
    if _dai16(cau) > TRAN_GUI:
        raise TuChoi(f"`cau_hoi` dai {_dai16(cau)} don vi UTF-16 > tran {TRAN_GUI}: nut Gui khoa tu "
                     f"{TRAN_NUT_GUI_DO + 1}, nen khong the la cau da gui")
    if O_THOAT not in cau:
        raise TuChoi("`cau_hoi` thieu LOI THOAT nguyen van — so tay se bia (BƯỚC 107)")
    if "answer in vietnamese" not in cau.lower():
        raise TuChoi("`cau_hoi` khong doi tra loi tieng Viet")
    nguon = muc.get("nguon")
    if nguon is not None and any(not isinstance(x, str) or len(x.strip()) < 2 for x in nguon):
        raise TuChoi("`nguon` phai la DANH SACH ten nguon (moi ten >= 2 ky tu) — mot CHUOI "
                     "qua list() thanh tung ky tu (loi 192)")
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


def ghi(muc: dict, so: Path = SO, ngay: str | None = None, cham_luat=None, git=None) -> dict:
    """Kiểm rồi mới ghi. Giữ nguyên định dạng file (JSON indent 2, UTF-8).

    `cham_luat(n) -> [file đổi]` để test thay máy đọc git; mặc định đọc lịch sử thật.
    `git(*args) -> (mã, đầu ra)` thay máy đọc git của phép đo độ tươi.

    Từ BƯỚC 246 mục hỏi thật có thể mang (tuỳ chọn): `tra_loi_tep` + `tra_loi_sha256` +
    `trich_dan_tep` (BẮT TAY: sha256 tệp phải khớp sha256 trang đã băm, lệch thì từ chối và
    không chạm sổ) -> ô `tra_loi`; `nhan_nguon_tep` (nhãn nguồn như trang hiện) -> `nguon`
    và `_do_tuoi` SINH ra từ git, không từ lời mô hình.
    """
    if "khong_bat_buoc_vi" in muc:
        return _ghi_khong_bat_buoc(muc, so, ngay, cham_luat)
    kiem_muc(muc)
    tra_loi = _dung_tra_loi(muc)
    nguon_tuoi = _dung_nguon_va_do_tuoi(muc, git)
    s = so.read_text(encoding="utf-8")
    d = json.loads(s)
    buoc = muc["buoc"]
    if buoc in d["soat"]:
        raise TuChoi(f"{buoc} da co trong so — khong ghi de")
    dong = {"ngay": ngay or datetime.date.today().isoformat(),
            "nguon": nguon_tuoi[0] if nguon_tuoi else list(muc.get("nguon") or NGUON_MAC_DINH)}
    if nguon_tuoi:
        dong["_do_tuoi"] = nguon_tuoi[1]
    elif muc.get("_do_tuoi"):
        dong["_do_tuoi"] = muc["_do_tuoi"]
    dong["cau_hoi"] = muc["cau_hoi"]
    dong["o_thoat"] = O_THOAT
    if tra_loi:
        dong["tra_loi"] = tra_loi
    if muc.get("khong_tim_thay_gi") is True:
        dong["khong_tim_thay_gi"] = True
        dong["phat_hien"] = []
        dong["_tu_kiem_cau_am"] = muc["_tu_kiem_cau_am"]
    else:
        dong["phat_hien"] = muc["phat_hien"]
    d["soat"][buoc] = dong
    so.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dong


#: Ô "Văn bản đã sao chép" của sổ tay nhận tối đa ĐÚNG 500.000 ký tự, đếm theo
#: đơn vị UTF-16 của ô nhập (đo 16/10/2026, BƯỚC 202: 500.000 thì nút Chèn mở,
#: 500.001 thì khoá).
TRAN_O_DAN = 500_000
#: Cỡ tối đa một khúc `docs/STATE.md` khi DÁN (BƯỚC 202). Đo 16/10/2026: nạp URL
#: nguyên tệp (1,31 triệu ký tự) thì mô hình dừng ở ký tự ~352.490, nạp lại dừng
#: đúng chỗ ấy; dán ba khúc ~437 nghìn ký tự thì một khúc hụt ~7.800 ký tự cuối.
#: Con số này là mức ĐÃ ĐO đọc trọn — hạ nữa nếu một lần đo độ tươi thấy hụt.
CO_PHAN_TOI_DA = 350_000
TIEU_DE_BUOC = re.compile(r"^## BƯỚC (\d+)", re.M)
RAW = "https://raw.githubusercontent.com/Siner0808/vibe-stock-analysis"


def _dai16(s: str) -> int:
    """Độ dài theo đơn vị UTF-16 — cách ô dán của sổ tay (và chuỗi JS) đếm."""
    return len(s.encode("utf-16-le")) // 2


def chia_state(van_ban: str, co_toi_da: int = CO_PHAN_TOI_DA) -> list[tuple[int, int]]:
    """Cắt `docs/STATE.md` thành các khúc `[đầu, cuối)` để DÁN vào sổ tay.

    HÀM THUẦN. Chỉ cắt NGAY TRƯỚC một dòng `## BƯỚC n`, không cắt giữa một BƯỚC;
    mỗi khúc <= `co_toi_da` đơn vị UTF-16; ghép các khúc lại đúng nguyên văn.
    THAM LAM từ đầu tệp: STATE chỉ dài thêm ở cuối, nên ranh giới các khúc đầu
    đứng yên giữa hai lần làm tươi — thường chỉ khúc cuối phải dán lại. Một BƯỚC
    dài hơn trần thì TỪ CHỐI (không có chỗ cắt hợp lệ).
    """
    moc = [m.start() for m in TIEU_DE_BUOC.finditer(van_ban)]
    khuc: list[tuple[int, int]] = []
    dau = vua = 0
    for m in moc + [len(van_ban)]:
        if _dai16(van_ban[dau:m]) > co_toi_da:
            khuc.append((dau, vua))
            dau = vua
            if _dai16(van_ban[dau:m]) > co_toi_da:
                raise TuChoi(f"mot BUOC dai hon tran {co_toi_da} (tu ky tu {dau}) — "
                             "khong cat giua BUOC; ha tran thi phai tach BUOC ay")
        vua = m
    khuc.append((dau, len(van_ban)))
    return khuc


def ke_hoach_chia(van_ban: str, bam: str, co_toi_da: int = CO_PHAN_TOI_DA) -> list[dict]:
    """Mỗi khúc một dòng: nhãn nguồn, khoảng BƯỚC, vị trí UTF-16 (cho `slice` của JS)."""
    khuc = chia_state(van_ban, co_toi_da)
    ra = []
    for i, (a, b) in enumerate(khuc, 1):
        so = [int(x) for x in TIEU_DE_BUOC.findall(van_ban[a:b])]
        tu, den = (min(so), max(so)) if so else (0, 0)
        ra.append({
            "nhan": f"STATE.md @{bam[:7]} phan{i}/{len(khuc)} (BUOC {tu}-{den})",
            "dau16": _dai16(van_ban[:a]), "cuoi16": _dai16(van_ban[:b]),
            "dai16": _dai16(van_ban[a:b]), "byte": len(van_ban[a:b].encode("utf-8")),
            "buoc_tu": tu, "buoc_den": den,
            "buoc_cuoi_vi_tri": so[-1] if so else 0,
        })
    return ra


def lenh_js_chia(bam: str, tong_byte: int, ke_hoach: list[dict]) -> str:
    """Lệnh JS (cho `javascript_tool`): tải STATE ở ĐÚNG commit, kiểm byte, cắt sẵn.

    Kết quả nằm ở `window.__phanState = [[nhãn, văn bản], …]`; lệch byte thì
    `null` — không dán một bản khác commit đã ghim.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", bam):
        raise TuChoi(f"can ma bam DU 40 ky tu (ghim commit, khong ghim nhanh): {bam!r}")
    cat = ", ".join(f"[{json.dumps(k['nhan'], ensure_ascii=False)}, {k['dau16']}, {k['cuoi16']}]"
                    for k in ke_hoach)
    return (
        f"const r = await fetch('{RAW}/{bam}/docs/STATE.md'); const t = await r.text();"
        " const n = new TextEncoder().encode(t).length;"
        f" window.__phanState = (n === {tong_byte}) ? [{cat}].map(([h, a, b]) => [h, t.slice(a, b)]) : null;"
        " window.__phanState ? window.__phanState.map(([h, p]) => h + ' · ' + p.length)"
        f" : ('LECH BYTE: tai ' + n + ', can {tong_byte}')")


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
                        help="in LENH JS dien cau hoi vao o chat (loi 113); chua gui")
        ap.add_argument("--giu-lich-su", action="store_true",
                        help="cho phep dien khi nhat ky chat chua rong (mac dinh TU CHOI)")
        a = ap.parse_args(argv[1:])
        try:
            cau = dung_cau_hoi(a.buoc, a.ket_luan, a.vi_du)
            print(lenh_dien_cau(cau, a.giu_lich_su) if a.js else cau)
            print(f"cau hoi dai {_dai16(cau)} don vi UTF-16 (tran gui {TRAN_GUI})", file=sys.stderr)
        except TuChoi as e:
            print(f"TU CHOI: {e}", file=sys.stderr)
            return 1
        return 0
    if argv and argv[0] == "lay-nhan":
        print(lenh_lay_nhan())
        return 0
    if argv and argv[0] in ("xoa-nhat-ky", "chup", "bam-gui"):
        import argparse
        ap = argparse.ArgumentParser(prog=f"so_tay.py {argv[0]}")
        ap.add_argument({"xoa-nhat-ky": "--buoc", "chup": "--truoc", "bam-gui": "--dai"}[argv[0]],
                        type=int, required=True,
                        help={"xoa-nhat-ky": "buoc 1-4 (moi buoc MOT lenh, cho ~1 giay giua hai buoc)",
                              "chup": "so tra loi da co TRUOC khi gui (lenh `hoi --js` in ra)",
                              "bam-gui": "do dai o chat (UTF-16) `hoi --js` da in ra"}[argv[0]])
        a = ap.parse_args(argv[1:])
        try:
            print(lenh_xoa_nhat_ky(a.buoc) if argv[0] == "xoa-nhat-ky"
                  else lenh_chup_tra_loi(a.truoc) if argv[0] == "chup" else lenh_bam_gui(a.dai))
        except TuChoi as e:
            print(f"TU CHOI: {e}", file=sys.stderr)
            return 1
        return 0
    if argv and argv[0] == "kiem-tra-loi":
        import argparse
        ap = argparse.ArgumentParser(prog="so_tay.py kiem-tra-loi")
        ap.add_argument("tep")
        ap.add_argument("--sha256", required=True, help="sha256 do TRANG tinh")
        a = ap.parse_args(argv[1:])
        try:
            kq = kiem_tra_loi(Path(a.tep).read_bytes(), a.sha256)
        except OSError as e:
            print(f"CHUA DOC DUOC tep: {e}", file=sys.stderr)
            return 2
        except TuChoi as e:
            print(f"TU CHOI: {e}", file=sys.stderr)
            return 1
        print(f"KHOP · sha256 {kq['sha256']} · {kq['dai16']} don vi UTF-16")
        return 0
    if argv and argv[0] == "do-tuoi":
        import argparse
        ap = argparse.ArgumentParser(prog="so_tay.py do-tuoi")
        ap.add_argument("tep_nhan", help="nhan nguon, moi dong mot nhan (ket qua cua `lay-nhan`)")
        ap.add_argument("--so-voi", default="HEAD", help="commit dem lam 'moi' (mac dinh HEAD)")
        ap.add_argument("--tom-tat", action="store_true", help="chi in dong cho o `_do_tuoi`")
        a = ap.parse_args(argv[1:])
        try:
            nhan, la = doc_nhan(Path(a.tep_nhan).read_text(encoding="utf-8"))
            if not nhan:
                print("TU CHOI: tep khong co nhan nao — tab Nguon chua mo? (doc 0 nguon la MAU HONG)",
                      file=sys.stderr)
                return 1
            kq = do_tuoi(nhan, la, so_voi=a.so_voi)
        except (OSError, KhongKiemDuoc) as e:
            print(f"CHUA KIEM DUOC: {e}", file=sys.stderr)
            return 2
        if a.tom_tat:
            print(tom_tat_do_tuoi(kq))
        else:
            for d in kq["nguon"]:
                print(f"{d['trang_thai']:<14} {d['nhan']}  ->  {d['tep']}")
            for t in kq["thieu"]:
                print(f"{'THIEU':<14} {t}")
            for t in kq["la"]:
                print(f"{'NHAN_LA':<14} {t}")
            print(f"KET LUAN {kq['ket_luan']} · so voi {kq['so_voi']} {kq['ma_so_voi']} · "
                  f"{len(kq['nguon'])} nguon")
        return 0 if kq["ket_luan"] == "TUOI" else 1
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
    if argv and argv[0] == "chia-state":
        import argparse
        ap = argparse.ArgumentParser(prog="so_tay.py chia-state")
        ap.add_argument("--bam", default="HEAD", help="commit (mac dinh HEAD)")
        ap.add_argument("--co-toi-da", type=int, default=CO_PHAN_TOI_DA)
        ap.add_argument("--js", action="store_true", help="in LENH JS tai + cat san")
        a = ap.parse_args(argv[1:])
        import subprocess
        try:
            bam = subprocess.run(["git", "-C", str(GOC), "rev-parse", a.bam], check=True,
                                 capture_output=True, text=True).stdout.strip()
            raw = subprocess.run(["git", "-C", str(GOC), "show", f"{bam}:docs/STATE.md"],
                                 check=True, capture_output=True).stdout
        except (OSError, subprocess.CalledProcessError) as e:
            print(f"CHUA DOC DUOC docs/STATE.md o {a.bam}: {e}", file=sys.stderr)
            return 2
        try:
            kh = ke_hoach_chia(raw.decode("utf-8"), bam, a.co_toi_da)
            if a.js:
                print(lenh_js_chia(bam, len(raw), kh))
                return 0
        except TuChoi as e:
            print(f"TU CHOI: {e}", file=sys.stderr)
            return 1
        print(f"docs/STATE.md @{bam} · {len(raw):,} byte · {len(kh)} khuc <= {a.co_toi_da:,} ky tu")
        for k in kh:
            print(f"  {k['nhan']:<44} {k['dai16']:>8,} ky tu {k['byte']:>9,} byte"
                  f" · tieu de cuoi (vi tri) BUOC {k['buoc_cuoi_vi_tri']}")
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
