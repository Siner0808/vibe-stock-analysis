"""Gác của các lệnh JS trình duyệt trong `tools/so_tay.py` (BƯỚC 246).

Vì sao phải CHẠY JS chứ không chỉ tìm chuỗi trong nó. Phiên con không có trình duyệt: lệnh
JS do Python dựng, leader dán vào trình duyệt và đọc kết quả. Một gác kiểu `"Xoá" in js`
vẫn xanh khi lệnh bấm nhầm hộp thoại "Xoá nguồn". Nên các ca dưới đây dựng một DOM GIẢ
(`KHUNG_DOM`, có bộ chọn `tag.lớp[thuộc-tính]` và quan hệ hậu duệ), chạy lệnh bằng `node`
với đồng hồ giả, rồi đọc xem nút nào bị bấm.

LỆNH JS KHÔNG ĐƯỢC HẸN GIỜ. Leader đo 30/10/2026: khi cửa sổ Claude không hiện,
`document.hidden` là true và trình duyệt bóp `setTimeout` đến mức một `await setTimeout(750)`
không xong trong 45 s (bản đầu của BƯỚC 246 chờ 38 s trong trang và chết đúng như vậy), còn
`await crypto.subtle.digest` thì xong. Nên `setTimeout` của DOM giả NỔ nếu lệnh gọi nó, và một
gác đọc chuỗi cấm `setTimeout`/`requestAnimationFrame`/`setInterval` trong mọi lệnh.

DOM giả chỉ chứng minh LOGIC của lệnh (bấm hay không bấm, "xong" khi nào, băm gì). Nó không
chứng minh bộ chọn khớp trang thật — phần ấy do leader chạy lệnh trong trình duyệt và STATE
ghi kết quả thô. `node` có sẵn ở runner `ubuntu-latest`; thiếu `node` thì các ca chạy JS bị bỏ
qua, các ca đọc chuỗi vẫn chạy.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
import so_tay as st  # noqa: E402

NODE = shutil.which("node")
can_node = pytest.mark.skipif(NODE is None, reason="khong co node")

KHUNG_DOM = r"""
let now = 0;
Date.now = () => now;
const avan = (ms) => { now += ms; };
globalThis.setTimeout = () => { throw new Error('setTimeout bi CAM trong lenh JS (khung an bop timer)'); };
globalThis.requestAnimationFrame = globalThis.setTimeout;
globalThis.setInterval = globalThis.setTimeout;
const doc_tu_khoa = (s) => { const re = /([a-z][a-z0-9]*)|\.([\w-]+)|\[([\w-]+)(?:="([^"]*)")?\]/g; let m;
  const o = {tag: null, cls: [], attrs: []};
  while ((m = re.exec(s))) { if (m[1]) o.tag = m[1]; else if (m[2]) o.cls.push(m[2]); else o.attrs.push([m[3], m[4]]); }
  return o; };
class El {
  constructor(tag, o = {}, cha = null) {
    this.tag = tag; this.cls = o.cls || []; this.attrs = o.attrs || {}; this.vis = o.vis !== false;
    this.top = o.top ?? 500; this.text = o.text ?? ''; this.onclick = o.onclick || null; this.clicks = 0;
    this.disabled = !!o.disabled; this._v = ''; this.sukien = [];
    this.children = []; this.cha = cha; if (cha) cha.children.push(this);
  }
  get parentElement() { return this.cha; }
  get value() { return this._v; }
  set value(v) { this._v = v; }
  get innerText() { return typeof this.text === 'function' ? this.text() : this.text; }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  getClientRects() { return this.vis ? [{}] : []; }
  getBoundingClientRect() { return {top: this.top, left: 0}; }
  dispatchEvent(e) { this.sukien.push(e.type); return true; }
  click() { this.clicks++; if (this.onclick) this.onclick(this); }
  closest(sel) { const p = doc_tu_khoa(sel); for (let e = this; e; e = e.cha) if (e.khop && e.khop(p)) return e; return null; }
  remove() { this.cha.children = this.cha.children.filter(c => c !== this); }
  all() { return this.children.flatMap(c => [c, ...c.all()]); }
  khop(p) { return (!p.tag || p.tag === this.tag) && p.cls.every(c => this.cls.includes(c))
    && p.attrs.every(([k, v]) => k in this.attrs && (v === undefined || this.attrs[k] === v)); }
  qsa(sel) {
    const ra = [];
    for (const alt of sel.split(',')) {
      const phan = alt.trim().split(/\s+(?![^\[]*\])/).map(doc_tu_khoa);
      for (const e of this.all()) {
        if (!e.khop(phan[phan.length - 1])) continue;
        let i = phan.length - 2, a = e.cha;
        while (i >= 0 && a) { if (a.khop && a.khop(phan[i])) i--; a = a.cha; }
        if (i < 0 && !ra.includes(e)) ra.push(e);
      }
    }
    return this.all().filter(e => ra.includes(e));
  }
  querySelectorAll(sel) { return this.qsa(sel); }
  querySelector(sel) { return this.qsa(sel)[0] || null; }
}
globalThis.HTMLTextAreaElement = El;     // `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')`
const document = new El('document');
globalThis.document = document;
globalThis.window = globalThis;
const mk = (tag, o, cha) => new El(tag, o, cha || document);
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
// Chạy MỘT lệnh JS như `javascript_tool`: biểu thức cuối là kết quả (`kq` trần ở lệnh nhiều câu).
const chay = async (code) => {
  const c = code.trim();
  const than = /\bkq\s*$/.test(c) ? c.replace(/\bkq\s*$/, 'return kq') : 'return ' + c;
  return await new AsyncFunction(than)();
};
const ra = (o) => process.stdout.write(JSON.stringify(o));
"""


def chay_js(tmp_path: Path, lenh: dict, kich_ban: str) -> dict:
    """`lenh` là {tên: mã JS}; kịch bản (JS) dựng cây DOM, gọi `await chay(L.tên)` và `ra({…})`."""
    (tmp_path / "kb.js").write_text(
        KHUNG_DOM + "\nconst L = " + json.dumps(lenh, ensure_ascii=False) + ";\n(async () => {\n"
        + kich_ban + "\n})().catch(e => { console.error(e.stack); process.exit(3); });\n", encoding="utf-8")
    r = subprocess.run([NODE, str(tmp_path / "kb.js")], capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-1500:]
    return json.loads(r.stdout)


# ── xoá nhật ký: bốn bước, mỗi bước một lệnh đồng bộ ──────────────────────────────────────

CAU_HOP = ("Xoá nhật ký trò chuyện của sổ ghi chú này Bạn sắp xoá toàn bộ nhật ký trò chuyện của "
           "sổ ghi chú này. Bạn không thể huỷ thao tác này.")


def kich_ban_xoa(hop: str, muc_menu: str = None) -> str:
    """Dựng thanh đầu + menu + hộp; chạy bước 1..4. `hop` là JS dựng các hộp thoại sau khi chọn mục."""
    muc = json.dumps(muc_menu or "delete\nXoá nhật ký trò chuyện\nNhật ký của bạn được giữ riêng tư.",
                     ensure_ascii=False)
    return r"""
const trl = [0, 1, 2].map(i => mk('div', {cls: ['message-text-content'], text: 'tl' + i},
  mk('div', {cls: ['to-user-container']})));
mk('button', {attrs: {'aria-label': 'Chia sẻ'}, text: 'share', top: 20});
const xoa_bam = [];
const mk_hop = (text, vis, them_xoa) => { const h = mk('div', {attrs: {role: 'dialog'}, text, vis});
  const huy = mk('button', {text: 'Huỷ'}, h);
  const xoa = mk('button', {text: 'Xoá', onclick: () => { trl.forEach(t => t.cha.remove()); }}, h);
  if (them_xoa) mk('button', {text: 'Xoá'}, h);
  return [huy, xoa]; };
const kebab = mk('button', {text: 'more_vert', top: 20, onclick: () => {
  mk('div', {attrs: {role: 'menuitem'}, text: MUC, onclick: () => { HOP }});
}});
mk('div', {attrs: {role: 'dialog'}, text: 'bang emoji', vis: false});
const kq = [];
for (const b of [1, 2, 3, 4]) { avan(1000); kq.push(await chay(L['b' + b])); }
ra({kq, xoa: xoa_bam.map(b => b.clicks), con: document.querySelectorAll('.to-user-container .message-text-content').length,
    kebab: kebab.clicks});
""".replace("MUC", muc).replace("HOP", hop)


def lenh_xoa():
    return {f"b{i}": st.lenh_xoa_nhat_ky(i) for i in (1, 2, 3, 4)}


HOP_DUNG = f"xoa_bam.push(...mk_hop({json.dumps(CAU_HOP, ensure_ascii=False)}, true)); mk_hop({json.dumps(CAU_HOP, ensure_ascii=False)}, false);"


@can_node
def test_XOA_bon_buoc_dong_bo_bam_DUNG_nut_Xoa_va_tra_loi_ve_0(tmp_path):
    r = chay_js(tmp_path, lenh_xoa(), kich_ban_xoa(HOP_DUNG))
    k = r["kq"]
    assert k[0].startswith("DA BAM NUT MENU") and k[1].startswith("DA CHON MUC")
    assert k[2].startswith("DA BAM XOA") and "truoc 3" in k[2] and k[3].startswith("tra loi con 0") and "XONG" in k[3], r
    assert r["xoa"] == [0, 1], r          # nút Huỷ không bấm, nút Xoá bấm đúng 1 lần
    assert r["con"] == 0 and r["kebab"] == 1


@can_node
def test_XOA_hop_thoai_KHAC_thi_TU_CHOI_va_khong_bam_Xoa(tmp_path):
    """Hộp "Xoá nguồn?" cũng có nút "Xoá". Bấm nó là mất nguồn — không được xảy ra."""
    hop = "xoa_bam.push(...mk_hop('Xoá nguồn? Bạn sắp xoá nguồn STATE.md khỏi sổ ghi chú này.', true));"
    r = chay_js(tmp_path, lenh_xoa(), kich_ban_xoa(hop))
    assert r["kq"][2].startswith("TU CHOI"), r
    assert r["xoa"] == [0, 0] and r["con"] == 3, r


@can_node
def test_XOA_chi_co_hop_AN_mang_dung_cau_thi_TU_CHOI(tmp_path):
    """Bản trùng ẩn trong DOM không được bấm: lọc theo độ hiện."""
    hop = f"xoa_bam.push(...mk_hop({json.dumps(CAU_HOP, ensure_ascii=False)}, false));"
    r = chay_js(tmp_path, lenh_xoa(), kich_ban_xoa(hop))
    assert r["kq"][2].startswith("TU CHOI"), r
    assert r["xoa"] == [0, 0] and r["con"] == 3, r


@can_node
def test_XOA_cau_xac_nhan_lech_mot_chu_thi_TU_CHOI(tmp_path):
    lech = CAU_HOP.replace("sắp xoá toàn bộ nhật ký", "sắp xoá toàn bộ nguồn")
    hop = f"xoa_bam.push(...mk_hop({json.dumps(lech, ensure_ascii=False)}, true));"
    r = chay_js(tmp_path, lenh_xoa(), kich_ban_xoa(hop))
    assert r["kq"][2].startswith("TU CHOI") and r["xoa"] == [0, 0], r


@can_node
def test_XOA_hop_co_HAI_nut_Xoa_thi_TU_CHOI(tmp_path):
    hop = f"xoa_bam.push(...mk_hop({json.dumps(CAU_HOP, ensure_ascii=False)}, true, true));"
    r = chay_js(tmp_path, lenh_xoa(), kich_ban_xoa(hop))
    assert r["kq"][2].startswith("TU CHOI") and "2 nut" in r["kq"][2], r
    assert r["xoa"] == [0, 0] and r["con"] == 3


@can_node
def test_XOA_buoc_3_khi_chua_co_hop_thoai_nao_thi_TU_CHOI(tmp_path):
    kb = r"""
mk('div', {cls: ['message-text-content'], text: 'tl'}, mk('div', {cls: ['to-user-container']}));
ra({kq: await chay(L.b3), con: document.querySelectorAll('.message-text-content').length});
"""
    r = chay_js(tmp_path, lenh_xoa(), kb)
    assert r["kq"].startswith("TU CHOI · khong co hop thoai HIEN") and r["con"] == 1, r


@can_node
def test_XOA_khong_thay_nut_menu_thi_TU_CHOI_va_liet_ke_nut(tmp_path):
    kb = r"""
mk('button', {attrs: {'aria-label': 'Chia sẻ'}, text: 'share', top: 20});
mk('button', {attrs: {'aria-label': 'Cài đặt'}, text: 'settings', top: 20});
ra({kq: await chay(L.b1)});
"""
    r = chay_js(tmp_path, lenh_xoa(), kb)
    assert r["kq"].startswith("TU CHOI · khong thay nut menu") and "Cài đặt" in r["kq"], r


@can_node
def test_XOA_menu_khong_co_muc_xoa_nhat_ky_thi_TU_CHOI(tmp_path):
    kb = r"""
mk('div', {attrs: {role: 'menuitem'}, text: 'Sao chép sổ ghi chú'});
ra({kq: await chay(L.b2)});
"""
    r = chay_js(tmp_path, lenh_xoa(), kb)
    assert r["kq"].startswith("TU CHOI · menu khong co muc"), r


# ── chụp trả lời ──────────────────────────────────────────────────────────────────────────

TRANG_THAI = "Analyzing the documents...\nexpand_more"
CAU_TRA_LOI = "Thoughts\nexpand_more\nKhông tìm thấy câu nào nói ngược. 💡 x_t\t​ = 1. " + "Đoạn dài. " * 40


def kich_ban_chup(text_js: str, lan: list, truoc: int = 0, so_cu: int = 0, trich_dan: bool = True,
                  nut_sao_chep: str = "co") -> str:
    """`text_js`: biểu thức JS của câu trả lời MỚI, đọc biến `giai_doan`. `lan`: danh sách (ms trước lần
    chụp, giai đoạn). Trả danh sách kết quả mỗi lần chụp."""
    return (r"""
let khung_cu = null;
for (let i = 0; i < SO_CU; i++) { khung_cu = mk('div', {cls: ['to-user-container']});
  mk('div', {cls: ['message-text-content'], text: 'tra loi CU ' + i + ' '.repeat(300) + 'chu'}, khung_cu); }
let giai_doan = 0;
const goc = mk('div', {cls: ['to-user-container']});
const moi = mk('div', {cls: ['message-text-content'], text: () => (TEXT)}, goc);
if (TRICH) for (const [n, nhan] of [[1, 'CLAUDE.md @a877ca6'], [13, 'STATE.md @61221db phan1/5 (BUOC 2-40)'], [13, 'STATE.md @61221db phan1/5 (BUOC 2-40)']])
  mk('span', {attrs: {'aria-label': n + ': ' + nhan}}, mk('button', {cls: ['citation-marker']}, moi));
mk('span', {attrs: {'aria-label': 'khong phai trich dan'}}, moi);
const NHAN_SAO = 'Sao chép câu trả lời của mô hình vào bảng nhớ tạm', KHAC = ['Đánh giá câu trả lời là tốt', 'Lưu tin nhắn vào ghi chú'];
if (NUT === 'co') for (const a of [NHAN_SAO, ...KHAC]) mk('button', {attrs: {'aria-label': a}}, goc);
if (NUT === 'khac') for (const a of KHAC) mk('button', {attrs: {'aria-label': a}}, goc);
if (NUT === 'cu') mk('button', {attrs: {'aria-label': NHAN_SAO}}, khung_cu);
const kq = [];
for (const [ms, gd] of LAN) { avan(ms); giai_doan = gd; kq.push(await chay(L.chup)); }
ra({kq});
""").replace("SO_CU", str(so_cu)).replace("TEXT", text_js).replace("TRICH", "true" if trich_dan else "false").replace("NUT", json.dumps(nut_sao_chep)) \
        .replace("LAN", json.dumps(lan))


def _cau() -> str:
    return json.dumps(CAU_TRA_LOI, ensure_ascii=False)


def _chup(tmp_path, truoc=0, **kw):
    return chay_js(tmp_path, {"chup": st.lenh_chup_tra_loi(truoc)}, kich_ban_chup(truoc=truoc, **kw))["kq"]


@can_node
def test_CHUP_xong_sau_3_lan_giong_nhau_cach_du_2_giay_va_tra_text_sha_trich_dan(tmp_path):
    text = f"giai_doan === 0 ? {json.dumps(TRANG_THAI)} : giai_doan === 1 ? 'Thoughts\\nexpand_more\\nmot nua' : {_cau()}"
    kq = _chup(tmp_path, text_js=text, lan=[[1000, 0], [1500, 1], [1500, 2], [1500, 2], [1500, 2]])
    assert [k["xong"] for k in kq] == [False, False, False, False, True], kq
    assert [k["giong"] for k in kq] == [0, 1, 1, 2, 3]
    assert kq[0]["dang_nghi"] is True and "text" not in kq[1] and "text" not in kq[3]   # chưa xong thì không trả text
    x = kq[4]
    assert x["text"] == CAU_TRA_LOI
    assert x["sha256"] == hashlib.sha256(CAU_TRA_LOI.encode("utf-8")).hexdigest()
    assert x["dai16"] == st._dai16(CAU_TRA_LOI) and x["dai16"] != len(CAU_TRA_LOI)   # 💡 = 2 đơn vị
    assert x["khoang_ms"] == 3000
    assert x["trich_dan"] == [{"n": 1, "nguon": "CLAUDE.md @a877ca6"},
                              {"n": 13, "nguon": "STATE.md @61221db phan1/5 (BUOC 2-40)"},
                              {"n": 13, "nguon": "STATE.md @61221db phan1/5 (BUOC 2-40)"}]
    assert ["9", "200b"] == [h for _, h in x["vo_hinh"]]       # \t và U+200B được liệt kê, \n thì không


@can_node
def test_CHUP_bat_tay_THAT_tep_ghi_tu_ket_qua_khop_kiem_tra_loi(tmp_path):
    kq = _chup(tmp_path, text_js=_cau(), lan=[[1000, 2], [1000, 2], [1000, 2]])
    x = kq[-1]
    assert x["xong"] is True
    tep = tmp_path / "tl.txt"
    tep.write_bytes(x["text"].encode("utf-8"))
    assert st.kiem_tra_loi(tep.read_bytes(), x["sha256"])["dai16"] == x["dai16"]


@can_node
def test_CHUP_thieu_nut_sao_chep_trong_khung_thi_CHUA_xong_du_3_lan_giong_nhau_cach_xa(tmp_path):
    """Điều kiện thứ ba (leader, 30/10: một ảnh chụp 253 ký tự của bản PHÁT DỞ đã qua phép thử "không đang nghĩ")."""
    for che_do, so_cu in (("khong", 0), ("khac", 0), ("cu", 1)):    # không nút · nút khác nhãn · nút ở khung CŨ
        kq = _chup(tmp_path, truoc=so_cu, so_cu=so_cu, text_js=_cau(), lan=[[3000, 2]] * 4, nut_sao_chep=che_do)
        assert [k["giong"] for k in kq] == [1, 2, 3, 4] and not any(k["xong"] for k in kq), (che_do, kq)
        assert all(k["co_nut_sao_chep"] is False for k in kq), che_do
    co = _chup(tmp_path, text_js=_cau(), lan=[[3000, 2]] * 3)
    assert co[-1]["xong"] is True and co[-1]["co_nut_sao_chep"] is True, co


@can_node
def test_CHUP_du_3_lan_nhung_cach_nhau_duoi_2_giay_thi_CHUA_xong(tmp_path):
    kq = _chup(tmp_path, text_js=_cau(), lan=[[100, 2], [100, 2], [100, 2]])
    assert kq[-1]["giong"] == 3 and kq[-1]["khoang_ms"] == 200 and kq[-1]["xong"] is False, kq
    kq = _chup(tmp_path, text_js=_cau(), lan=[[100, 2], [100, 2], [100, 2], [1800, 2]])
    assert kq[-1]["giong"] == 4 and kq[-1]["xong"] is True, kq


@can_node
def test_CHUP_van_doi_noi_dung_giua_cac_lan_thi_giong_ve_1_va_KHONG_xong(tmp_path):
    text = "'Thoughts\\nexpand_more\\n' + 'x'.repeat(250) + giai_doan"
    kq = _chup(tmp_path, text_js=text, lan=[[1500, i] for i in range(8)])
    assert all(k["giong"] == 1 and not k["xong"] for k in kq), kq


@can_node
def test_CHUP_doi_noi_dung_o_lan_cuoi_dat_lai_bo_dem(tmp_path):
    text = "'Thoughts\\nexpand_more\\n' + 'x'.repeat(250) + giai_doan"
    kq = _chup(tmp_path, text_js=text, lan=[[1500, 5], [1500, 5], [1500, 6], [1500, 6]])
    assert [k["giong"] for k in kq] == [1, 2, 1, 2] and not any(k["xong"] for k in kq), kq


@can_node
def test_CHUP_dong_trang_thai_xen_giua_thi_DAT_LAI_bo_dem(tmp_path):
    """A, A, [đang nghĩ], A: lần cuối là lần chụp THỨ NHẤT của một chuỗi mới, không phải thứ ba."""
    text = f"giai_doan === 0 ? {json.dumps(TRANG_THAI)} : {_cau()}"
    kq = _chup(tmp_path, text_js=text, lan=[[1000, 2], [1000, 2], [1000, 0], [1000, 2]])
    assert [k["giong"] for k in kq] == [1, 2, 0, 1] and not any(k["xong"] for k in kq), kq


@can_node
def test_CHUP_chi_con_dong_trang_thai_thi_CHUA_xong_va_xoa_bo_dem(tmp_path):
    kq = _chup(tmp_path, text_js=json.dumps(TRANG_THAI), lan=[[3000, 0]] * 4)
    assert all(k["dang_nghi"] and not k["xong"] and k["giong"] == 0 for k in kq), kq


@can_node
def test_CHUP_khong_nhan_tra_loi_CU_con_trong_lich_su(tmp_path):
    """`truoc` = 2: hai trả lời cũ ổn định; trả lời MỚI vẫn là dòng trạng thái -> chưa xong, `moi` đúng."""
    kq = _chup(tmp_path, truoc=2, so_cu=2, text_js=json.dumps(TRANG_THAI), lan=[[3000, 0]] * 3)
    assert kq[-1]["xong"] is False and kq[-1]["so_tra_loi"] == 3 and kq[-1]["moi"] is True, kq


@can_node
def test_CHUP_khong_co_phan_tu_moi_thi_khong_nhan_ban_cu_du_on_dinh(tmp_path):
    kb = r"""
for (let i = 0; i < 2; i++) mk('div', {cls: ['message-text-content'], text: 'tra loi CU ' + ' '.repeat(300) + 'chu'}, mk('div', {cls: ['to-user-container']}));
const kq = [];
for (let i = 0; i < 4; i++) { avan(3000); kq.push(await chay(L.chup)); }
ra({kq});
"""
    kq = chay_js(tmp_path, {"chup": st.lenh_chup_tra_loi(2)}, kb)["kq"]
    assert all(not k["xong"] and k["moi"] is False and k["so_tra_loi"] == 2 for k in kq), kq


@can_node
def test_CHUP_bo_dem_cong_don_cung_truoc_va_phan_tu_moi_phu_thuoc_truoc(tmp_path):
    """Cùng `truoc`: lần 2 đếm 2. `truoc` = số trả lời hiện có thì không còn trả lời MỚI."""
    kb = r"""
const goc = mk('div', {cls: ['to-user-container']});
mk('div', {cls: ['message-text-content'], text: 'Thoughts\nexpand_more\n' + 'y'.repeat(300)}, goc);
const a = await chay(L.t0); avan(3000); const a2 = await chay(L.t0); avan(3000);
const b = await chay(L.t1);
ra({a: a.giong, a2: a2.giong, b_moi: b.moi});
"""
    r = chay_js(tmp_path, {"t0": st.lenh_chup_tra_loi(0), "t1": st.lenh_chup_tra_loi(1)}, kb)
    assert r == {"a": 1, "a2": 2, "b_moi": False}, r


@can_node
def test_CHUP_cau_hoi_lap_lai_cung_cau_tra_loi_khong_ke_thua_bo_dem_cua_lan_hoi_truoc(tmp_path):
    """Hỏi LẠI đúng câu cũ -> trả lời mới có CÙNG sha với trả lời cũ. `truoc` khác thì đếm lại từ 1."""
    kb = r"""
for (let i = 0; i < 2; i++) mk('div', {cls: ['message-text-content'], text: 'Thoughts\nexpand_more\n' + 'y'.repeat(300)}, mk('div', {cls: ['to-user-container']}));
const a = await chay(L.t0); avan(3000); const a2 = await chay(L.t0); avan(3000); const a3 = await chay(L.t0);
avan(3000);
const b = await chay(L.t1);
ra({a: a.giong, a3: a3.giong, b_moi: b.moi, b_giong: b.giong, b_xong: b.xong});
"""
    r = chay_js(tmp_path, {"t0": st.lenh_chup_tra_loi(0), "t1": st.lenh_chup_tra_loi(1)}, kb)
    assert r == {"a": 1, "a3": 3, "b_moi": True, "b_giong": 1, "b_xong": False}, r


@can_node
def test_LAY_NHAN_chi_lay_nut_mang_ma_bam_va_bo_ban_trung(tmp_path):
    kb = r"""
for (const a of ['CLAUDE.md @a877ca6', 'STATE.md @61221db phan5/5 (BUOC 212-234)', 'CLAUDE.md @a877ca6', 'Tuỳ chọn khác', 'Gửi'])
  mk('button', {attrs: {'aria-label': a}});
mk('span', {attrs: {'aria-label': 'span.md @a877ca6'}});
ra({kq: await chay(L.nhan)});
"""
    r = chay_js(tmp_path, {"nhan": st.lenh_lay_nhan()}, kb)
    assert r["kq"].splitlines() == ["2 nhan", "CLAUDE.md @a877ca6", "STATE.md @61221db phan5/5 (BUOC 212-234)"]
    nhan, la = st.doc_nhan(r["kq"])
    assert len(nhan) == 2 and la == []


# ── điền câu hỏi rồi bấm Gửi: HAI lệnh, không hẹn giờ ─────────────────────────────────────

def kich_ban_gui(nut_khoa: bool) -> str:
    return r"""
mk('button', {attrs: {'aria-label': 'Gửi'}, disabled: true}, mk('div', {}));           // nút số 0: ô "Nghiên cứu nhanh"
mk('div', {cls: ['message-text-content'], text: 'cu'}, mk('div', {cls: ['to-user-container']}));
const khung = mk('div', {});
const ta = mk('textarea', {attrs: {'aria-label': 'Hộp truy vấn'}}, khung);
const gui = mk('button', {attrs: {'aria-label': 'Gửi'}, disabled: KHOA}, mk('div', {}, khung));
const r1 = await chay(L.dien);
const r_sai = await chay(L.bam_sai);
const r2 = await chay(L.bam);
ra({r1, r_sai, r2, gia_tri: ta.value, su_kien: ta.sukien, bam: gui.clicks});
""".replace("KHOA", "true" if nut_khoa else "false")


@can_node
def test_GUI_hai_lenh_dien_roi_bam_chi_bam_nut_cua_O_CHAT_khi_do_dai_khop(tmp_path):
    cau = st.dung_cau_hoi("BƯỚC 1", "k" * 60, ["câu có 'nháy đơn' và \"nháy kép\" 💡"])
    n = st._dai16(cau)
    lenh = {"dien": st.lenh_dien_cau(cau, giu_lich_su=True), "bam": st.lenh_bam_gui(n),
            "bam_sai": st.lenh_bam_gui(n + 1)}
    r = chay_js(tmp_path, lenh, kich_ban_gui(nut_khoa=False))
    assert r["gia_tri"] == cau and r["su_kien"] == ["input"]
    assert r["r1"] == f"DA DIEN · o co {n} ky tu · tra loi truoc: 1 · doi 1 giay roi chay bam-gui --dai {n}", r
    assert r["r_sai"].startswith("TU CHOI · o chat co")      # đã bấm sai độ dài: chưa có cú bấm nào
    assert r["r2"] == f"DA BAM GUI · o co {n} ky tu luc bam" and r["bam"] == 1, r


@can_node
def test_DIEN_va_BAM_xoa_bo_dem_cua_chup_nhung_BAM_bi_tu_choi_thi_khong_xoa(tmp_path):
    """Leader 30/10: bộ đếm `window.__chupSoTay` còn nguyên (giong 3) sau lượt trước -> lượt sau xong ngay."""
    cau = "hoi gi do"
    kb = r"""
mk('div', {cls: ['message-text-content'], text: 'cu'}, mk('div', {cls: ['to-user-container']}));
const khung = mk('div', {});
const ta = mk('textarea', {attrs: {'aria-label': 'Hộp truy vấn'}}, khung);
const gui = mk('button', {attrs: {'aria-label': 'Gửi'}, disabled: false}, mk('div', {}, khung));
window.__chupSoTay = {dem: 3};
await chay(L.dien);
const sau_dien = window.__chupSoTay;
window.__chupSoTay = {dem: 3};
await chay(L.bam_sai);
const sau_bam_sai = window.__chupSoTay;
await chay(L.bam);
ra({sau_dien, sau_bam_sai, sau_bam: window.__chupSoTay, bam: gui.clicks});
"""
    lenh = {"dien": st.lenh_dien_cau(cau, True), "bam": st.lenh_bam_gui(len(cau)), "bam_sai": st.lenh_bam_gui(len(cau) + 1)}
    r = chay_js(tmp_path, lenh, kb)
    assert r == {"sau_dien": None, "sau_bam_sai": {"dem": 3}, "sau_bam": None, "bam": 1}, r


@can_node
def test_DIEN_tu_choi_khi_nhat_ky_chat_con_tra_loi_vi_xoa_la_bat_dong_bo(tmp_path):
    """Leader đo 30/10: bước 4 chạy ngay sau bước 3 còn thấy 1 trả lời; vài giây sau mới 0."""
    cau = "hoi gi do"
    r = chay_js(tmp_path, {"dien": st.lenh_dien_cau(cau), "bam": st.lenh_bam_gui(len(cau)),
                           "bam_sai": st.lenh_bam_gui(1)}, kich_ban_gui(nut_khoa=False))
    assert r["r1"].startswith("TU CHOI · nhat ky chat con 1 tra loi") and r["gia_tri"] == "", r
    assert r["su_kien"] == [] and r["bam"] == 0 and r["r2"].startswith("TU CHOI"), r   # ô rỗng -> bấm cũng từ chối


@can_node
def test_DIEN_nhat_ky_rong_thi_dien_binh_thuong_khong_can_giu_lich_su(tmp_path):
    kb = r"""
const khung = mk('div', {});
const ta = mk('textarea', {attrs: {'aria-label': 'Hộp truy vấn'}}, khung);
mk('button', {attrs: {'aria-label': 'Gửi'}, disabled: false}, mk('div', {}, khung));
ra({r1: await chay(L.dien), gia_tri: ta.value});
"""
    r = chay_js(tmp_path, {"dien": st.lenh_dien_cau("hoi gi do")}, kb)
    assert r["gia_tri"] == "hoi gi do" and r["r1"].startswith("DA DIEN · o co 9 ky tu · tra loi truoc: 0"), r


@can_node
def test_XOA_buoc_4_con_tra_loi_thi_noi_CHUA_0_va_dung_gui(tmp_path):
    kb = r"""
mk('div', {cls: ['message-text-content'], text: 'tl'}, mk('div', {cls: ['to-user-container']}));
ra({kq: await chay(L.b4)});
"""
    r = chay_js(tmp_path, lenh_xoa(), kb)
    assert r["kq"].startswith("tra loi con 1 · CHUA 0") and "dung gui" in r["kq"], r


@can_node
def test_GUI_nut_van_khoa_thi_KHONG_bam_va_noi_ro(tmp_path):
    cau = "hoi gi do"
    r = chay_js(tmp_path, {"dien": st.lenh_dien_cau(cau, True), "bam": st.lenh_bam_gui(len(cau)),
                           "bam_sai": st.lenh_bam_gui(1)}, kich_ban_gui(nut_khoa=True))
    assert r["r2"].startswith("NUT GUI VAN KHOA") and r["bam"] == 0, r


@can_node
def test_MOI_lenh_JS_bien_dich_duoc(tmp_path):
    """Một lỗi cú pháp ở đây tốn một lượt leader dán và chờ. `new AsyncFunction` biên dịch, không chạy."""
    nap = ("const A = Object.getPrototypeOf(async function () {}).constructor;"
           "const c = require('fs').readFileSync(process.argv[2], 'utf8').trim();"
           "new A(/\\bkq$/.test(c) ? c.replace(/\\bkq$/, 'return kq') : 'return ' + c);console.log('BIEN DICH OK');")
    (tmp_path / "bd.js").write_text(nap, encoding="utf-8")
    for ten, js in tat_ca_lenh().items():
        (tmp_path / f"{ten}.js").write_text(js, encoding="utf-8")
        r = subprocess.run([NODE, str(tmp_path / "bd.js"), str(tmp_path / f"{ten}.js")],
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0 and "BIEN DICH OK" in r.stdout, (ten, r.stderr[-800:])


# ── gác đọc chuỗi: chạy cả khi không có node ────────────────────────────────────────────────

def tat_ca_lenh() -> dict:
    cau = st.dung_cau_hoi("BƯỚC 1", "k" * 60, ["một câu"])
    d = {f"xoa{i}": st.lenh_xoa_nhat_ky(i) for i in (1, 2, 3, 4)}
    d.update(dien=st.lenh_dien_cau(cau), bam=st.lenh_bam_gui(st._dai16(cau)),
             chup=st.lenh_chup_tra_loi(3), nhan=st.lenh_lay_nhan())
    return d


def test_KHONG_lenh_JS_nao_hen_gio_vi_khung_an_bop_setTimeout():
    """Leader đo 30/10/2026: `document.hidden` -> một `await setTimeout(750)` không xong trong 45 s."""
    for ten, js in tat_ca_lenh().items():
        for cam in ("setTimeout", "setInterval", "requestAnimationFrame", "new Promise"):
            assert cam not in js, (ten, cam)
    # chuỗi còn lại duy nhất cho phép `await`: băm. Không `await` nào khác.
    assert "await crypto.subtle.digest" in st.lenh_chup_tra_loi(0)
    for ten, js in tat_ca_lenh().items():
        if ten != "chup":
            assert "await" not in js, ten


def test_KHONG_lenh_JS_nao_mang_escape_unicode_hay_ky_tu_ngat_dong_unicode():
    """Leader chạy 30/10: `\\u2028` trong một regex literal bị đường truyền đổi thành ký tự LINE SEPARATOR
    thật -> "SyntaxError: Invalid regular expression: missing /". Quy tắc: không `\\uXXXX` nào trong
    lệnh (so mã ký tự bằng `charCodeAt`), và không U+2028/U+2029/U+0085 thật."""
    for ten, js in tat_ca_lenh().items():
        assert "\\u" not in js, (ten, js[js.index("\\u") - 30: js.index("\\u") + 30])
        for ky_tu in ("\u2028", "\u2029", "\u0085", "\r"):
            assert ky_tu not in js, (ten, hex(ord(ky_tu)))


def test_GUI_tu_choi_dung_lenh_khi_cau_dai_hon_TRAN_va_noi_ro_do_dai():
    ok = "a" * st.TRAN_GUI
    assert st.lenh_dien_cau(ok)
    with pytest.raises(st.TuChoi) as e:
        st.lenh_dien_cau("a" * (st.TRAN_GUI + 1))
    assert str(st.TRAN_GUI + 1) in str(e.value)


def test_GUI_do_dai_dem_theo_UTF16_khong_theo_ky_tu():
    """💡 là 2 đơn vị UTF-16 (như `String.length` của JS), 1 ký tự Python."""
    cau = "💡" * (st.TRAN_GUI // 2 + 1)
    assert len(cau) <= st.TRAN_GUI < st._dai16(cau)
    with pytest.raises(st.TuChoi):
        st.lenh_dien_cau(cau)


def test_TRAN_GUI_chua_bien_100_duoi_gioi_han_DA_DO():
    assert st.TRAN_NUT_GUI_DO == 3_900 and st.TRAN_GUI == st.TRAN_NUT_GUI_DO - 100


def test_DIEN_in_so_tra_loi_truoc_khi_gui_va_dem_theo_O_TRA_LOI_va_khong_bam():
    js = st.lenh_dien_cau(st.dung_cau_hoi("BƯỚC 1", "k" * 60, ["z"]))
    assert json.dumps(st.O_TRA_LOI) in js and "tra loi truoc: ' + truoc" in js
    assert "click()" not in js and 'textarea[aria-label="Hộp truy vấn"]' in js
    assert "querySelector('textarea')" not in js        # lỗi 113: textarea ĐẦU TIÊN là ô tìm nguồn web


def test_KIEM_MUC_tu_choi_cau_hoi_dai_hon_tran_gui():
    dai = st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["z" * st.TRAN_GUI])
    muc = {"buoc": "BƯỚC 9999", "cau_hoi": dai, "phat_hien": [
        {"noi_dung": "n", "tu_kiem": "grep -n x CLAUDE.md -> 1", "phan_quyet": "THẬT."}]}
    with pytest.raises(st.TuChoi, match="UTF-16"):
        st.kiem_muc(muc)
    muc["cau_hoi"] = st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["z"])
    st.kiem_muc(muc)


def test_XOA_chuoi_chua_cau_xac_nhan_nut_Xoa_va_loc_theo_chu_va_do_hien():
    js = st.lenh_xoa_nhat_ky(3)
    assert json.dumps(st.CAU_XAC_NHAN_XOA, ensure_ascii=False) in js
    assert json.dumps(st.MUC_MENU_XOA, ensure_ascii=False) in st.lenh_xoa_nhat_ky(2)
    assert "hien(d) && gon(d.innerText).includes(" in js
    assert "gon(b.innerText) ===" in js and "xoa.length !== 1" in js
    assert all("@@" not in st.lenh_xoa_nhat_ky(i) for i in (1, 2, 3, 4))
    for xau in (0, 5, "3", None):
        with pytest.raises(st.TuChoi):
            st.lenh_xoa_nhat_ky(xau)


def test_XOA_cau_xac_nhan_la_NGUYEN_VAN_cau_leader_do_ngay_30_10():
    assert st.CAU_XAC_NHAN_XOA == "Bạn sắp xoá toàn bộ nhật ký trò chuyện của sổ ghi chú này"
    assert st.MUC_MENU_XOA == "Xoá nhật ký trò chuyện" and st.NUT_XOA == "Xoá"


def test_CHUP_tham_so_dung_hang_so_va_TRUOC_la_so_nguyen_khong_am():
    js = st.lenh_chup_tra_loi(7)
    assert "const TRUOC = 7;" in js
    assert f"chay.dem >= {st.LAN_CHUP_GIONG}" in js and f"ra.khoang_ms >= {st.KHOANG_CHUP_TOI_THIEU_MS}" in js
    assert (st.LAN_CHUP_GIONG, st.KHOANG_CHUP_TOI_THIEU_MS) == (3, 2_000)
    for xau in (-1, "3", 2.5, True):
        with pytest.raises(st.TuChoi):
            st.lenh_chup_tra_loi(xau)


def test_BAM_GUI_tham_so_dai_la_so_nguyen_duong():
    assert "ta.value.length !== 123" in st.lenh_bam_gui(123)
    for xau in (0, -4, "5", 1.5, True):
        with pytest.raises(st.TuChoi):
            st.lenh_bam_gui(xau)


def test_KHONG_con_doc_tra_loi_bang_individual_message():
    for ten, js in tat_ca_lenh().items():
        assert "individual-message" not in js, ten
    cach_lam = (GOC / ".claude" / "skills" / "quy-trinh-lam-viec" / "references"
                / "soat-cheo-notebooklm.md").read_text(encoding="utf-8")
    assert "individual-message" not in cach_lam


def test_CLI_cac_lenh_in_JS_dung_voi_ham():
    def cli(*a):
        return subprocess.run([sys.executable, str(GOC / "tools" / "so_tay.py"), *a],
                              capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    for i in (1, 2, 3, 4):
        assert cli("xoa-nhat-ky", "--buoc", str(i)).stdout.strip() == st.lenh_xoa_nhat_ky(i)
    assert cli("chup", "--truoc", "4").stdout.strip() == st.lenh_chup_tra_loi(4)
    assert cli("bam-gui", "--dai", "77").stdout.strip() == st.lenh_bam_gui(77)
    assert cli("lay-nhan").stdout.strip() == st.lenh_lay_nhan()
    arg = ["hoi", "--buoc", "BƯỚC 1", "--ket-luan", "k" * 60, "--vi-du", "một câu"]
    cau = cli(*arg).stdout.strip()
    assert cli(*arg, "--js").stdout.strip() == st.lenh_dien_cau(cau)
    assert cli(*arg, "--js", "--giu-lich-su").stdout.strip() == st.lenh_dien_cau(cau, True) != st.lenh_dien_cau(cau)
    for xau in (["chup", "--truoc", "-2"], ["xoa-nhat-ky", "--buoc", "9"], ["bam-gui", "--dai", "0"]):
        r = cli(*xau)
        assert r.returncode == 1 and "TU CHOI" in r.stderr, xau
    dai = cli("hoi", "--buoc", "BƯỚC 1", "--ket-luan", "k" * 60, "--vi-du", "z" * 4000, "--js")
    assert dai.returncode == 1 and "TU CHOI" in dai.stderr and not dai.stdout.strip()
