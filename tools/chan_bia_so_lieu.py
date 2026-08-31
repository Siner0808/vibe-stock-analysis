#!/usr/bin/env python3
"""
chan_bia_so_lieu.py — hook chặn mẫu bịa số liệu.

Chạy như PostToolUse hook của Claude Code sau mỗi Write/Edit. Đọc JSON từ
stdin, phân tích file vừa sửa bằng AST, và CHẶN nếu thấy mẫu đã từng làm
hỏng dự án này.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 12/08/2026, `google_sheets_sync.py` đọc `t.position_size_pct` trong
khi lớp Trade tên trường là `size_pct`. getattr không tìm thấy nên rơi về
mặc định và ghi **hằng số 30** cho mọi lệnh — 108/113 lệnh bị ghi sai. Con
số 30% nhân với số lệnh chồng lấn chính là phép tính đẻ ra "+636,11%".

Không ai cố ý. Đó là một dòng `getattr(o, "ten_sai", 30)` trông vô hại.
Con người review sẽ bỏ qua; máy thì không.

Quy luật của dự án: **lỗi đo lường gần như không bao giờ làm kết quả xấu
đi.** Nên hook này chặn theo hướng một chiều — nghi ngờ thì dừng.

DÙNG AST, KHÔNG DÙNG REGEX
──────────────────────────
Regex bắt nhầm chuỗi, chú thích, và tên biến chứa từ khoá. AST chỉ thấy mã
thật sự chạy.

CỬA THOÁT
─────────
Thêm `# bia-ok: <lý do>` ngay dòng đó hoặc dòng ngay trên. Bắt buộc có lý
do — mục đích không phải cấm tuyệt đối, mà là buộc người viết nói ra vì
sao con số này không phải bịa.

Tự kiểm thử:  python tools/chan_bia_so_lieu.py --tu-kiem-tra
"""
from __future__ import annotations

import ast
import re
import difflib
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

# Hook được đăng ký ở HAI nơi: ~/.claude/settings.json (bảo vệ mọi phiên
# trên máy này, kể cả khi mở Claude Code từ thư mục khác) và .claude/
# settings.json trong repo (đi theo dự án cho người khác). Khi cwd đúng là
# repo thì cả hai cùng nạp và hook chạy hai lần — cùng một file, cùng một
# nội dung, báo trùng hai lần.
#
# Chống trùng theo NỘI DUNG chứ không theo thời gian: cùng file + cùng hash
# trong CUA_SO_TRUNG giây thì lần sau im lặng. Nội dung đổi -> hash đổi ->
# báo lại ngay, nên không bao giờ nuốt mất một lỗi thật.
CUA_SO_TRUNG = 5.0

GOC_DU_AN = Path(__file__).resolve().parent.parent

# Thư mục được miễn: test và scratch dựng dữ liệu giả là đúng việc của chúng.
MIEN_TRU = ("tests", "scratch", ".venv", "backtest/cache", "__pycache__")

CUA_THOAT = "bia-ok:"

# Vật chứa kiểu tuỳ chọn/cấu hình: getattr trên chúng là đọc CỜ, không phải
# đọc số đo. `getattr(args, "no_summary", False)` hoàn toàn hợp lệ, và
# argparse.Namespace không có lược đồ để đối chiếu tên trường.
VAT_CHUA_TUY_CHON = {"args", "arg", "opts", "options", "cfg", "config",
                     "ns", "namespace", "params", "kwargs", "settings", "self"}

# Số bị coi là "trung tính" khi kẹp biên — 0/1/100 thường là biên hợp lệ
# của thang điểm, không phải giá trị bịa.
SO_TRUNG_TINH = {0, 1, 100, 0.0, 1.0, 100.0, -1, -1.0}

#: Chuỗi trông như một trường f-string: {ten}, {ten.attr}, {ten:.1f}, {ten!r}
MAU_O_TRONG = re.compile(r"\{[A-Za-z_][A-Za-z0-9_.\[\]'\"]*(?:![rsa])?(?::[^{}]*)?\}")

#: Từ vựng khẳng định trạng thái vận hành. Dán cứng một trong số này làm
#: GIÁ TRỊ MẶC ĐỊNH nghĩa là "coi như đang chạy tốt cho tới khi có bằng
#: chứng ngược lại" — mà bằng chứng ngược lại thì không ai đi lấy.
TU_TRANG_THAI = {"OK", "SYNCED", "LIVE", "ACTIVE", "HEALTHY", "CONNECTED",
                 "ONLINE", "READY", "PASS", "VALID", "NORMAL"}


class PhatHien:
    def __init__(self, dong: int, ma: str, chan: bool, thong_diep: str,
                 goi_y: str = "") -> None:
        self.dong, self.ma, self.chan = dong, ma, chan
        self.thong_diep, self.goi_y = thong_diep, goi_y


# ── Tiện ích AST ─────────────────────────────────────────────────────
def _la_so(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return not isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _la_so(node.operand)
    return False


def _gia_tri_so(node: ast.AST):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp):
        v = _gia_tri_so(node.operand)
        return -v if isinstance(node.op, ast.USub) else v
    return None


def _chuoi(node: ast.AST):
    return node.value if isinstance(node, ast.Constant) and isinstance(
        node.value, str) else None


def _ten(node: ast.AST):
    return node.id if isinstance(node, ast.Name) else None


# ── Thu thập tên trường của mọi dataclass trong dự án ────────────────
def thu_thap_truong(goc: Path) -> dict[str, set[str]]:
    """{ten_lop: {ten_truong}} — dùng để bắt tên trường viết sai."""
    ket_qua: dict[str, set[str]] = {}
    for f in goc.glob("*.py"):
        try:
            cay = ast.parse(f.read_text(encoding="utf-8"))
        except (SyntaxError, OSError, UnicodeDecodeError):
            continue
        for n in ast.walk(cay):
            if not isinstance(n, ast.ClassDef):
                continue
            co_dataclass = any(
                (_ten(d) == "dataclass")
                or (isinstance(d, ast.Call) and _ten(d.func) == "dataclass")
                or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
                for d in n.decorator_list)
            if not co_dataclass:
                continue
            ket_qua[n.name] = {
                t.target.id for t in n.body
                if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)}
    return ket_qua


def _gan_nhat(ten: str, moi_truong: dict[str, set[str]]) -> tuple[str, str]:
    """Trả (ten_truong_gan_nhat, ten_lop) nếu đủ giống, ngược lại ('','').

    Chỉ báo khi tín hiệu MẠNH, vì báo nhầm là con đường nhanh nhất để hook
    bị tắt:

    a) Bao hàm — `size_pct` nằm trong `position_size_pct`. Đây đúng là hình
       dạng của lỗi thật: người viết thêm tiền tố/hậu tố vào tên trường.
       Tỷ lệ giống của cặp đó chỉ 0,64 nên ngưỡng đơn thuần bỏ sót nó.
    b) Rất giống (>= 0,9) — `entry_scores` vs `entry_score`, sai một ký tự.

    Tên nào đã là trường thật thì im lặng ngay.
    """
    if any(ten in truong for truong in moi_truong.values()):
        return ("", "")

    for lop, truong in moi_truong.items():
        for t in truong:
            if len(t) >= 5 and (t in ten or ten in t):
                return (t, lop)

    tot_nhat, diem, lop_tot = "", 0.0, ""
    for lop, truong in moi_truong.items():
        for t in truong:
            d = difflib.SequenceMatcher(None, ten, t).ratio()
            if d > diem:
                tot_nhat, diem, lop_tot = t, d, lop
    return (tot_nhat, lop_tot) if diem >= 0.9 else ("", "")


# ── Bộ dò ────────────────────────────────────────────────────────────
# Hàm điều phối: `return 0` trong đó là MÃ THOÁT tiến trình, không phải số
# đo. Chính hook này bị nó chặn oan ngay lần đầu — `except: return 0` trong
# main() nghĩa là "không chặn", chứ không phải "đo được 0".
HAM_MA_THOAT = {"main", "cli", "chay_tat_ca", "run"}


class BoDo(ast.NodeVisitor):
    def __init__(self, moi_truong: dict[str, set[str]], la_test: bool) -> None:
        self.moi_truong = moi_truong
        self.la_test = la_test
        self.ham_hien_tai: list[str] = []
        self.phat_hien: list[PhatHien] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for m in list(node.args.defaults) + list(node.args.kw_defaults):
            if (m is not None and not self.la_test
                    and isinstance(m, ast.Constant) and isinstance(m.value, str)
                    and m.value.strip().upper() in TU_TRANG_THAI):
                self._them(
                    node.lineno, "R8", True,
                    f'tham số mặc định {m.value!r} — khẳng định trạng thái.',
                    'Người gọi quên truyền thì hàm tự nhận là mọi thứ đang tốt.')
        self.ham_hien_tai.append(node.name)
        self.generic_visit(node)
        self.ham_hien_tai.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def _trong_ham_ma_thoat(self) -> bool:
        return bool(self.ham_hien_tai) and self.ham_hien_tai[-1] in HAM_MA_THOAT

    def _them(self, *a, **kw) -> None:
        self.phat_hien.append(PhatHien(*a, **kw))

    def visit_Call(self, node: ast.Call) -> None:
        ten_ham = _ten(node.func)

        ten_ham = ten_ham or ""

        # `_them` la cua ra van ban cua chinh bo do nay — no cung dinh
        # dung loi R7, xem chu thich cua R4 ben duoi.
        goi = ten_ham or (node.func.attr
                          if isinstance(node.func, ast.Attribute) else "")
        if goi in ("print", "warning", "error", "info", "_them"):
            for a in node.args:
                self._soi_o_trong(a, "in ra")

        # R8 — mặc định là một từ khẳng định trạng thái
        vi_tri = None
        if ten_ham == "getattr" and len(node.args) >= 3:
            vi_tri = node.args[2]
        elif (isinstance(node.func, ast.Attribute) and node.func.attr == "get"
              and len(node.args) >= 2):
            vi_tri = node.args[1]
        if (vi_tri is not None and not self.la_test
                and isinstance(vi_tri, ast.Constant)
                and isinstance(vi_tri.value, str)
                and vi_tri.value.strip().upper() in TU_TRANG_THAI):
            self._them(
                node.lineno, "R8", True,
                f'mặc định là {vi_tri.value!r} — khẳng định trạng thái chưa kiểm.',
                'Thiếu dữ liệu mà trả về "đang tốt" thì phía sau không phân '
                'biệt được "đo được là tốt" với "không đo được".')

        # R1/R2 — getattr(obj, "ten", mac_dinh)
        if ten_ham == "getattr" and len(node.args) >= 2:
            khoa = _chuoi(node.args[1])
            # Mặc định boolean = đọc cờ bật/tắt, không phải đọc số đo.
            mac_dinh_co = (len(node.args) >= 3
                           and isinstance(node.args[2], ast.Constant)
                           and isinstance(node.args[2].value, bool))
            tuy_chon = _ten(node.args[0]) in VAT_CHUA_TUY_CHON
            if khoa:
                gan, lop = _gan_nhat(khoa, self.moi_truong) \
                    if not (tuy_chon or mac_dinh_co) else ("", "")
                if gan:
                    self._them(
                        node.lineno, "R2", True,
                        f'getattr đọc trường "{khoa}" — không lớp nào có trường này.',
                        f'Ý bạn là "{gan}" (của {lop})? Trường sai làm getattr '
                        f'luôn rơi về mặc định, tức mọi bản ghi nhận cùng một '
                        f'giá trị bịa. Đây đúng là lỗi size_pct/position_size_pct.')
                if len(node.args) >= 3 and _la_so(node.args[2]) and not self.la_test:
                    v = _gia_tri_so(node.args[2])
                    self._them(
                        node.lineno, "R1", True,
                        f'getattr(..., "{khoa}", {v}) — mặc định là con số.',
                        'Trường thiếu thì phải NỔ hoặc trả None, không được '
                        'lặng lẽ thay bằng số. Một con số bịa trông y hệt số đo '
                        'thật ở mọi khâu phía sau.')

        # R4 — d.get("khoa", <so khac 0>)
        if (isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                and len(node.args) >= 2 and _la_so(node.args[1])
                and not self.la_test):
            v = _gia_tri_so(node.args[1])
            if v not in SO_TRUNG_TINH:
                khoa = _chuoi(node.args[0]) or "?"
                self._them(
                    node.lineno, "R4", False,
                    f'.get("{khoa}", {v}) — thiếu dữ liệu thì thay bằng {v}.',
                    f'Nếu {v} là số đo thật thì phải lấy từ nguồn; nếu là mặc '
                    'định thì ghi rõ bằng "# bia-ok: <lý do>".')

        self.generic_visit(node)

    def _soi_o_trong(self, nut, ngu_canh: str) -> None:
        """R7 — chuỗi mang {ten} mà KHÔNG phải f-string thì in ra nguyên văn."""
        if self.la_test or not isinstance(nut, ast.Constant):
            return
        if not isinstance(nut.value, str) or not MAU_O_TRONG.search(nut.value):
            return
        khop = MAU_O_TRONG.search(nut.value).group(0)
        self._them(
            nut.lineno, "R7", True,
            f'{ngu_canh} một chuỗi chứa {khop} nhưng thiếu tiền tố `f`.',
            'Nó sẽ in ra nguyên văn thay vì giá trị. Đã xảy ra hai lần: nhãn '
            'ngưỡng trong báo cáo phiên, và chính lời khuyên của bộ dò này. '
            'Thêm `f`, hoặc dùng .format() nếu cố ý làm hằng mẫu.')

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.op, ast.Add):
            self._soi_o_trong(node.value, "cộng dồn")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        # R8 — trường có chú thích kiểu, mặc định là một từ trạng thái.
        # Đây là `MarketDataPacket.data_quality: str = "OK"`: gốc của
        # 12.984/12.984 dòng decisions ghi 'OK', và là lý do nhánh
        # `elif quality != "OK"` trong consider_entry() không bao giờ đúng.
        v = node.value
        if (not self.la_test and isinstance(v, ast.Constant)
                and isinstance(v.value, str)
                and v.value.strip().upper() in TU_TRANG_THAI):
            self._them(
                node.lineno, "R8", True,
                f'mặc định là {v.value!r} — khẳng định trạng thái chưa ai kiểm.',
                'Một trường trạng thái mặc định "tốt" nghĩa là mọi bản ghi đều '
                'nói "tốt" cho tới khi có ai đó chủ động đặt khác — và không ai '
                'đi làm việc đó. Để None rồi buộc bên tạo phải điền.')
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        # R3 — nuốt lỗi rồi trả về một con số
        for con in node.body:
            if isinstance(con, ast.Return) and con.value is not None \
                    and _la_so(con.value) and not self.la_test \
                    and not self._trong_ham_ma_thoat():
                v = _gia_tri_so(con.value)
                self._them(
                    con.lineno, "R3", True,
                    f'except ... -> return {v}: lỗi bị nuốt, thay bằng con số.',
                    'Hỏng mà vẫn trả số nghĩa là phía sau không phân biệt được '
                    f'"đo được {v}" với "không đo được". Ném lỗi, hoặc trả None.')
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # R5 — x = max(x, <so>) : nâng sàn một giá trị đã đo
        if (len(node.targets) == 1 and isinstance(node.value, ast.Call)
                and _ten(node.value.func) in ("max", "min")
                and len(node.value.args) == 2 and not self.la_test):
            dich = _ten(node.targets[0])
            nguon = [_ten(a) for a in node.value.args]
            so = [a for a in node.value.args if _la_so(a)]
            if dich and dich in nguon and so:
                v = _gia_tri_so(so[0])
                if v not in SO_TRUNG_TINH:
                    self._them(
                        node.lineno, "R5", False,
                        f'{dich} = {_ten(node.value.func)}({dich}, {v}) — '
                        f'ghi đè giá trị đã đo bằng hằng số.',
                        'Đây là mẫu `momentum_norm = max(momentum_norm, 65.0)`: '
                        'điểm số trông như do agent tính, thật ra do dòng này '
                        'đặt ra.')
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # R6 — `x or <số>` : thiếu giá trị đo thì thay bằng hằng số
        if isinstance(node.op, ast.Or) and not self.la_test:
            for gia_tri in node.values[1:]:
                if not _la_so(gia_tri):
                    continue
                v = _gia_tri_so(gia_tri)
                if v in SO_TRUNG_TINH:
                    continue
                self._them(
                    node.lineno, "R6", False,
                    f'... or {v} — thiếu giá trị thật thì thay bằng hằng số.',
                    f'Đây là mẫu `t.entry_price or 22750.0` từng sống trong '
                    f'app.py: khi dữ liệu vắng mặt, phía sau không phân biệt '
                    f'được "đo được {v}" với "không đo được". Để None rồi xử '
                    f'lý tường minh, hoặc hiện dấu gạch.')
                break
        self.generic_visit(node)


# ── Chạy ─────────────────────────────────────────────────────────────
def _co_marker(dong_van: str) -> bool:
    """Có `# bia-ok:` KÈM lý do không. Rỗng thì không tính."""
    return CUA_THOAT in dong_van and bool(
        dong_van.split(CUA_THOAT, 1)[1].strip())


def co_cua_thoat(dong_ma: list[str], dong: int) -> bool:
    """`# bia-ok: lý do` ở chính dòng đó, hoặc trong khối chú thích ngay trên.

    Quét ngược qua các dòng chú thích liền kề, không chỉ một dòng — lý do
    tử tế thường dài hơn một dòng, và phạt người viết dài là khuyến khích
    viết cụt.
    """
    i = dong - 1
    if 0 <= i < len(dong_ma) and _co_marker(dong_ma[i]):
        return True

    i -= 1
    while 0 <= i < len(dong_ma) and dong_ma[i].strip().startswith("#"):
        if _co_marker(dong_ma[i]):
            return True
        i -= 1
    return False


def kiem_tra(duong_dan: Path) -> list[PhatHien]:
    ma = duong_dan.read_text(encoding="utf-8")
    try:
        cay = ast.parse(ma)
    except SyntaxError:
        return []                        # file đang dở; Python sẽ tự báo

    tuong_doi = duong_dan.relative_to(GOC_DU_AN).as_posix()
    la_test = tuong_doi.startswith("tests/")

    bo_do = BoDo(thu_thap_truong(GOC_DU_AN), la_test)
    bo_do.visit(cay)

    dong_ma = ma.splitlines()
    return [p for p in bo_do.phat_hien if not co_cua_thoat(dong_ma, p.dong)]


def da_bao_gan_day(duong_dan: Path, ma_nguon: str) -> bool:
    """Đã báo đúng file + đúng nội dung này trong vài giây gần đây chưa.

    Khoá theo HASH nội dung, không theo thời gian sửa: nội dung đổi thì hash
    đổi và báo lại ngay, nên không bao giờ nuốt mất một lỗi thật. Chỉ nuốt
    đúng thứ cần nuốt — lần chạy thứ hai của cùng một hook trên cùng một
    file y hệt.
    """
    dau = hashlib.sha256(
        f"{duong_dan}\n{ma_nguon}".encode("utf-8")).hexdigest()[:32]
    moc = Path(tempfile.gettempdir()) / f"chan_bia_{dau}.moc"
    try:
        if moc.exists() and (time.time() - moc.stat().st_mtime) < CUA_SO_TRUNG:
            return True
        moc.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        return False                     # không ghi được mốc thì cứ báo
    return False


def trong_pham_vi(duong_dan: Path) -> bool:
    if duong_dan.suffix != ".py" or not duong_dan.exists():
        return False
    try:
        tuong_doi = duong_dan.relative_to(GOC_DU_AN).as_posix()
    except ValueError:
        return False                     # ngoài dự án
    return not any(tuong_doi.startswith(m) or f"/{m}/" in f"/{tuong_doi}"
                   for m in MIEN_TRU if m != "tests")


def main() -> int:
    # Console Windows mặc định cp1258 -> in tiếng Việt và emoji sẽ nổ
    # UnicodeEncodeError, và hook chết là hook không bảo vệ được gì.
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    try:
        du_lieu = json.load(sys.stdin)
    except Exception:
        return 0

    thô = (du_lieu.get("tool_input", {}).get("file_path")
           or du_lieu.get("tool_response", {}).get("filePath"))
    if not thô:
        return 0

    duong_dan = Path(str(thô)).resolve()
    if not trong_pham_vi(duong_dan):
        return 0

    try:
        if da_bao_gan_day(duong_dan, duong_dan.read_text(encoding="utf-8")):
            return 0                     # lần chạy trùng của hook thứ hai
    except OSError:
        pass

    try:
        phat_hien = kiem_tra(duong_dan)
    except Exception as e:
        # Hook hỏng thì báo, nhưng không chặn công việc.
        print(json.dumps({"systemMessage":
                          f"⚠️ chan_bia_so_lieu lỗi: {type(e).__name__}: {e}"},
                         ensure_ascii=False))
        return 0

    if not phat_hien:
        return 0

    chan = [p for p in phat_hien if p.chan]
    ten = duong_dan.name

    dong_bao = []
    for p in sorted(phat_hien, key=lambda x: x.dong):
        muc = "CHẶN" if p.chan else "CẢNH BÁO"
        dong_bao.append(f"  [{p.ma}/{muc}] {ten}:{p.dong} — {p.thong_diep}")
        if p.goi_y:
            dong_bao.append(f"      → {p.goi_y}")

    than = "\n".join(dong_bao)

    if chan:
        ly_do = (
            f"🚫 CHẶN BỊA SỐ LIỆU — {len(chan)} lỗi trong {ten}\n\n{than}\n\n"
            "Sổ lệnh là bằng chứng. Một con số bịa trông y hệt số đo thật ở mọi "
            "khâu phía sau, nên phải chặn ngay tại chỗ ghi.\n"
            "Sửa cho đúng nguồn dữ liệu, hoặc nếu thật sự chính đáng thì thêm "
            "`# bia-ok: <lý do>` — bắt buộc có lý do.\n"
            "Xem NGUYEN-TAC-DO-LUONG.md.")
        print(json.dumps({
            "decision": "block",
            "reason": ly_do,
            "systemMessage": f"🚫 Chặn {len(chan)} mẫu bịa số liệu trong {ten}",
        }, ensure_ascii=False))
        return 0

    print(json.dumps({
        "systemMessage": f"⚠️ {len(phat_hien)} cảnh báo bịa số liệu trong {ten}",
        "hookSpecificOutput": {"hookEventName": "PostToolUse",
                               "additionalContext": than},
    }, ensure_ascii=False))
    return 0


def quet_repo() -> int:
    """Quét TOÀN BỘ dự án. Trả 1 nếu có phát hiện mức CHẶN.

    Vì sao cần chế độ này: hook PostToolUse chỉ chạy SAU khi ghi và chỉ bắt
    Write/Edit của Claude Code — sửa từ IDE, Antigravity, tay người,
    `git checkout` hay `git merge` đều không kích hoạt. 15 commit UI gần
    nhất đi vào repo theo đúng đường đó. Chế độ này để CI chạy: cửa chống
    cháy, không phải chuông báo cháy.
    """
    for luong in (sys.stdout, sys.stderr):
        try:
            luong.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    tong_chan = tong_canh_bao = 0
    for duong_dan in sorted(GOC_DU_AN.rglob("*.py")):
        if not trong_pham_vi(duong_dan):
            continue
        try:
            phat_hien = kiem_tra(duong_dan)
        except Exception as e:
            print(f"  [LỖI] {duong_dan.name}: {type(e).__name__}: {e}")
            continue
        for p in sorted(phat_hien, key=lambda x: x.dong):
            muc = "CHẶN" if p.chan else "CẢNH BÁO"
            ten = duong_dan.relative_to(GOC_DU_AN).as_posix()
            print(f"  [{p.ma}/{muc}] {ten}:{p.dong} — {p.thong_diep}")
            if p.goi_y:
                print(f"      → {p.goi_y}")
            if p.chan:
                tong_chan += 1
            else:
                tong_canh_bao += 1

    print(f"\nQuét xong: {tong_chan} CHẶN · {tong_canh_bao} cảnh báo")
    if tong_chan:
        print("Sửa cho đúng nguồn dữ liệu, hoặc thêm `# bia-ok: <lý do>` "
              "— bắt buộc có lý do. Xem NGUYEN-TAC-DO-LUONG.md.")
    return 1 if tong_chan else 0


if __name__ == "__main__":
    if "--tu-kiem-tra" in sys.argv:
        from test_chan_bia_so_lieu import chay_tat_ca  # type: ignore
        sys.exit(chay_tat_ca())
    if "--quet-repo" in sys.argv:
        sys.exit(quet_repo())
    sys.exit(main())
