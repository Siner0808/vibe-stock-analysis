"""Đường giao bản tin cuối ngày qua Telegram (BƯỚC 258, mốc B2 / tiêu chí T3).

Phủ: `tin_telegram.py` (hàm thuần) · `tools/gui_ban_tin_telegram.py` (HTTP bị thay bằng hàm giả —
KHÔNG test nào chạm mạng) · `.github/workflows/gui-ban-tin-telegram.yml` (đọc bằng văn bản vì
`pyyaml` không nằm trong `requirements.txt`) · gác AST (module thuần, công cụ chỉ đọc sổ, token
không bao giờ vào một dòng in).

Mỗi gác ở đây có đột biến đi kèm (`docs/STATE.md` BƯỚC 258).
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib
import re
import sys
import urllib.error
import urllib.request

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import duyet_repo  # noqa: E402
import tin_telegram as tt  # noqa: E402
from paper_trading import BUY_THRESHOLD  # noqa: E402
from test_ban_tin import D, _lap, _SoChiDoc, _sheet_day_du, _so_tam, _vni  # noqa: E402

import ban_tin as bt  # noqa: E402

WF = GOC / ".github" / "workflows" / "gui-ban-tin-telegram.yml"
TOKEN = "123456:ABC-gia-lap-token-khong-that"
CHAT = "-1001234567890"


def _cli():
    spec = importlib.util.spec_from_file_location(
        "gui_ban_tin_cli", GOC / "tools" / "gui_ban_tin_telegram.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(autouse=True)
def _khong_mang(monkeypatch):
    """Mọi lời gọi `urlopen` trong file này là LỖI — HTTP phải đi qua `post` giả."""
    def no(*a, **k):
        raise AssertionError("test chạm mạng (urlopen)")
    monkeypatch.setattr(urllib.request, "urlopen", no)


# ─────────────────────────────────────────────────────────────────────
# 1. markdown -> văn bản thuần
# ─────────────────────────────────────────────────────────────────────
def test_markdown_sang_van_ban_bo_ky_hieu_giu_chu():
    md = ("## 📰 Bản tin cuối ngày 2026-10-09\n\n### 1. Thị trường\n\n"
          "- VN-INDEX đóng cửa **1,717.00**\n  - Hậu kiểm máy: `x`\n"
          "- **3 mã** (AAA, BBB) — _ghi chú nghiêng_\n---\n_Bản tin đọc từ sổ lệnh ẢO._")
    v = tt.markdown_sang_van_ban(md)
    assert v.splitlines() == [
        "📰 Bản tin cuối ngày 2026-10-09", "", "1. Thị trường", "",
        "• VN-INDEX đóng cửa 1,717.00", "  • Hậu kiểm máy: x",
        "• 3 mã (AAA, BBB) — ghi chú nghiêng", tt.DONG_NGANG,
        "Bản tin đọc từ sổ lệnh ẢO."]


def test_gach_duoi_trong_ma_ly_do_khong_bi_cao():
    v = tt.markdown_sang_van_ban("- **AAA** — thoát vì STOP_LOSS, DA_CO_VI_THE và a_b_c")
    assert "STOP_LOSS" in v and "DA_CO_VI_THE" in v and "a_b_c" in v


def test_ban_tin_that_khong_con_ky_hieu_markdown():
    v = tt.markdown_sang_van_ban(bt.ban_tin_markdown(_lap()))
    for dong in v.splitlines():
        assert not dong.lstrip().startswith("#"), dong
        assert "**" not in dong and "`" not in dong, dong
    assert "Bản tin cuối ngày 2026-10-09" in v and "Đã chấm" in v


# ─────────────────────────────────────────────────────────────────────
# 2. chia tin
# ─────────────────────────────────────────────────────────────────────
def test_tin_ngan_la_mot_tin_nguyen_van():
    assert tt.chia_tin("a\nb\nc") == ["a\nb\nc"]
    assert tt.chia_tin("") == [] and tt.chia_tin("\n \n") == []


def _bo_tien_to(tin):
    return [re.sub(r"^\(\d+/\d+\) ", "", t) for t in tin]


def test_chia_o_ranh_gioi_dong_moi_tin_duoi_gioi_han_va_khong_mat_dong():
    dong = [f"dòng số {i:04d} " + "x" * 90 for i in range(200)]
    tin = tt.chia_tin("\n".join(dong), gioi_han=1000)
    assert len(tin) > 1
    for i, t in enumerate(tin, 1):
        assert tt.do_dai(t) <= 1000
        assert t.startswith(f"({i}/{len(tin)}) ")
    ghep = []
    for t in _bo_tien_to(tin):
        ghep += t.split("\n")
    assert ghep == dong                       # đủ, đúng thứ tự, không dòng nào bị cắt giữa chừng


def test_gioi_han_mac_dinh_la_4096_va_do_bang_utf16():
    assert tt.GIOI_HAN_KY_TU == 4096
    assert tt.do_dai("a😀") == 3              # emoji ngoài BMP = 2 đơn vị
    # 6 x 400 emoji = 4800 đơn vị UTF-16 nhưng chỉ 2400 ký tự Python: đo bằng len() sẽ để lọt
    tin = tt.chia_tin("\n".join(["😀" * 400] * 6))
    assert len(tin) == 2 and all(tt.do_dai(t) <= 4096 for t in tin)


def test_mot_dong_dai_hon_gioi_han_duoc_cat_o_dau_cach_roi_cat_cung():
    # 103 - 16 = 87 không chia hết cho 5 (độ dài "abcd "): cắt cứng sẽ rơi GIỮA một từ
    tin = tt.chia_tin("abcd " * 50 + "\n" + "y" * 500, gioi_han=103)
    assert all(tt.do_dai(t) <= 103 for t in tin)
    assert "".join(_bo_tien_to(tin)).count("y") == 500
    tu = [w for t in _bo_tien_to(tin) for w in t.split() if "y" not in w]
    assert tu and set(tu) == {"abcd"}, "dòng có dấu cách phải cắt ở dấu cách, không cắt giữa từ"


def test_tin_vua_khit_tran_van_nam_chung_mot_tin():
    """Biên: tổng đúng bằng `gioi_han - CHO_CHUA_TIEN_TO` thì KHÔNG tách (so `>` chứ không `>=`)."""
    tran = 100 - tt.CHO_CHUA_TIEN_TO
    khit = "a" * 40 + "\n" + "b" * (tran - 41)
    assert tt.do_dai(khit) == tran
    cum = tt.chia_tin(khit + "\n" + "c" * 30, gioi_han=100)           # tổng 115 > 100 nên phải tách
    assert [c.split(") ", 1)[1] for c in cum] == [khit, "c" * 30]
    # gói gọn dưới giới hạn thì không bị đánh số
    assert tt.chia_tin(khit, gioi_han=tt.do_dai(khit)) == [khit]


# ─────────────────────────────────────────────────────────────────────
# 3. chọn ngày · khoá · secret · che bí mật
# ─────────────────────────────────────────────────────────────────────
def test_chon_ngay_phien_hom_nay_thi_gui():
    q = tt.chon_ngay("2026-10-09", "2026-10-09")
    assert q.ngay == "2026-10-09" and q.canh_bao is None


def test_chon_ngay_lay_ngay_cua_so_khi_luot_quet_tre_qua_nua_dem():
    assert tt.chon_ngay("2026-10-09", "2026-10-10").ngay == "2026-10-09"   # 01:35 sáng hôm sau


def test_chon_ngay_chu_nhat_sau_thu_sau_van_con_han_thu_ba_thi_het():
    assert tt.chon_ngay("2026-10-09", "2026-10-12").ngay == "2026-10-09"   # cách 3 ngày
    q = tt.chon_ngay("2026-10-09", "2026-10-13")                            # cách 4 ngày
    assert q.ngay is None and "cũ 4 ngày" in q.ly_do


def test_chon_ngay_khong_phai_phien_thi_khong_gui():
    q = tt.chon_ngay("2026-09-02", "2026-09-02")                  # Quốc khánh
    assert q.ngay is None and "không phải phiên" in q.ly_do
    assert tt.chon_ngay("2026-10-10", "2026-10-10").ngay is None  # thứ Bảy


def test_chon_ngay_so_trong_tuong_lai_hay_rong_thi_khong_gui():
    assert tt.chon_ngay("2026-10-12", "2026-10-09").ngay is None
    assert "không có quyết định" in tt.chon_ngay(None, "2026-10-09").ly_do
    assert tt.chon_ngay("rác", "2026-10-09").ngay is None


def test_chon_ngay_ngoai_lich_van_gui_nhung_canh_bao():
    q = tt.chon_ngay("2027-01-05", "2027-01-05")
    assert q.ngay == "2027-01-05" and "ngoài" in q.canh_bao


def test_khoa_da_gui_theo_ngay_va_chi_nhan_ngay_hop_le():
    assert tt.khoa_da_gui("2026-10-09") == "ban-tin-telegram-da-gui-2026-10-09"
    assert tt.khoa_da_gui("2026-10-09 00:00:00") == "ban-tin-telegram-da-gui-2026-10-09"
    assert tt.khoa_da_gui("2026-10-09") != tt.khoa_da_gui("2026-10-08")
    with pytest.raises(ValueError):
        tt.khoa_da_gui("hôm nay")


def test_thieu_secret_hai_ten_dung_va_rong_hay_khoang_trang_la_thieu():
    assert (tt.BIEN_TOKEN, tt.BIEN_CHAT_ID) == ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
    assert tt.thieu_secret({}) == ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    assert tt.thieu_secret({"TELEGRAM_BOT_TOKEN": "x", "TELEGRAM_CHAT_ID": "  "}) == [
        "TELEGRAM_CHAT_ID"]
    assert tt.thieu_secret({"TELEGRAM_BOT_TOKEN": "x", "TELEGRAM_CHAT_ID": "1"}) == []


def test_che_bi_mat_thay_moi_lan_xuat_hien_va_bo_qua_chuoi_rong():
    s = f"lỗi {TOKEN} rồi lại {TOKEN} và chat {CHAT}"
    ra = tt.che_bi_mat(s, TOKEN, CHAT, "", "  ")
    assert TOKEN not in ra and CHAT not in ra and ra.count("***") == 3
    assert tt.che_bi_mat("không có gì", "") == "không có gì"


# ─────────────────────────────────────────────────────────────────────
# 4. Gửi (HTTP giả)
# ─────────────────────────────────────────────────────────────────────
class Post:
    """Hàm `post` giả: ghi lại mọi lời gọi, trả lần lượt các phản hồi dựng sẵn."""

    def __init__(self, *phan_hoi):
        self.phan_hoi = list(phan_hoi)
        self.goi = []

    def __call__(self, url, payload, timeout=0):
        self.goi.append((url, payload))
        p = self.phan_hoi.pop(0)
        if isinstance(p, Exception):
            raise p
        return p


OK = (200, {"ok": True, "result": {}})


def test_gui_dung_url_payload_va_dem_tin():
    cli, post, ngu = _cli(), Post(OK, OK), []
    n = cli.gui_cac_tin(["tin một", "tin hai"], TOKEN, CHAT, post=post, ngu=ngu.append)
    assert n == 2
    assert post.goi[0][0] == f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    assert post.goi[0][1] == {"chat_id": CHAT, "text": "tin một", "disable_web_page_preview": True}
    assert "parse_mode" not in post.goi[0][1] and post.goi[1][1]["text"] == "tin hai"
    assert ngu == [cli.GIAN_CACH_GIUA_TIN_GIAY]        # nghỉ giữa hai tin, không nghỉ trước tin đầu


def test_429_thi_cho_dung_retry_after_roi_thu_lai():
    cli = _cli()
    post = Post((429, {"ok": False, "parameters": {"retry_after": 7}}), OK)
    ngu = []
    assert cli.gui_cac_tin(["a"], TOKEN, CHAT, post=post, ngu=ngu.append) == 1
    assert len(post.goi) == 2 and ngu == [7.0]


def test_429_cho_toi_da_va_het_luot_thu_thi_no():
    cli = _cli()
    r429 = (429, {"ok": False, "description": "Too Many Requests", "parameters": {"retry_after": 999}})
    post, ngu = Post(r429, r429, r429), []
    with pytest.raises(cli.LoiTelegram) as e:
        cli.gui_cac_tin(["a"], TOKEN, CHAT, post=post, ngu=ngu.append)
    assert len(post.goi) == 1 + cli.SO_LAN_THU_LAI_429
    assert ngu == [float(cli.TOI_DA_CHO_429_GIAY)] * cli.SO_LAN_THU_LAI_429
    assert "429" in str(e.value) and "Too Many Requests" in str(e.value)


@pytest.mark.parametrize("ma", [400, 401, 403, 404, 500])
def test_loi_khac_khong_thu_lai_va_noi_description_khong_noi_token(ma):
    cli = _cli()
    post = Post((ma, {"ok": False, "error_code": ma, "description": "Unauthorized"}))
    with pytest.raises(cli.LoiTelegram) as e:
        cli.gui_cac_tin(["a"], TOKEN, CHAT, post=post, ngu=lambda s: None)
    assert len(post.goi) == 1
    assert f"HTTP {ma}" in str(e.value) and "Unauthorized" in str(e.value)
    assert TOKEN not in str(e.value) and CHAT not in str(e.value)


def test_ok_true_nhung_ma_http_khac_200_van_la_loi():
    cli = _cli()
    with pytest.raises(cli.LoiTelegram):
        cli.gui_cac_tin(["a"], TOKEN, CHAT, post=Post((500, {"ok": True})), ngu=lambda s: None)


def test_gio_viet_nam_la_utc_cong_7():
    import datetime
    assert _cli().MUI_GIO_VN.utcoffset(None) == datetime.timedelta(hours=7)


def test_200_nhung_ok_khong_phai_true_van_la_loi():
    cli = _cli()
    with pytest.raises(cli.LoiTelegram):
        cli.gui_cac_tin(["a"], TOKEN, CHAT, post=Post((200, {"ok": False})), ngu=lambda s: None)
    with pytest.raises(cli.LoiTelegram):
        cli.gui_cac_tin(["a"], TOKEN, CHAT, post=Post((200, {})), ngu=lambda s: None)


def test_loi_mang_khong_thu_lai_vi_tin_co_the_da_toi_va_token_bi_che():
    cli = _cli()
    post = Post(urllib.error.URLError(f"timeout khi gọi /bot{TOKEN}/sendMessage"))
    with pytest.raises(cli.LoiTelegram) as e:
        cli.gui_cac_tin(["a", "b"], TOKEN, CHAT, post=post, ngu=lambda s: None)
    assert len(post.goi) == 1                               # KHÔNG gửi lại
    assert TOKEN not in str(e.value) and "***" in str(e.value) and "URLError" in str(e.value)
    assert e.value.__cause__ is None                        # `from None`: traceback không mang URL


def test_post_http_that_dung_urlopen_bi_thay_va_doc_than_loi(monkeypatch):
    cli, thay = _cli(), {}

    class Tra:
        status = 200

        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    def gia(req, timeout=0):
        thay["url"], thay["body"], thay["timeout"] = req.full_url, req.data, timeout
        thay["ct"] = req.get_header("Content-type")
        thay["method"] = req.get_method()
        return Tra()
    monkeypatch.setattr(urllib.request, "urlopen", gia)
    assert cli.post_http("https://x/y", {"a": 1}) == (200, {"ok": True})
    assert thay == {"url": "https://x/y", "body": b'{"a": 1}', "timeout": cli.THOI_GIAN_CHO_GIAY,
                    "ct": "application/json", "method": "POST"}

    def loi(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {},
                                     __import__("io").BytesIO(b'{"ok":false,"description":"d"}'))
    monkeypatch.setattr(urllib.request, "urlopen", loi)
    assert cli.post_http("https://x/y", {}) == (401, {"ok": False, "description": "d"})

    def rac(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 502, "Bad", {}, __import__("io").BytesIO(b"<html>"))
    monkeypatch.setattr(urllib.request, "urlopen", rac)
    assert cli.post_http("https://x/y", {}) == (502, {})


# ─────────────────────────────────────────────────────────────────────
# 5. Lệnh con `gui` · `kiem-tra-kenh`
# ─────────────────────────────────────────────────────────────────────
ENV = {"TELEGRAM_BOT_TOKEN": TOKEN, "TELEGRAM_CHAT_ID": CHAT}


def _co_tin(tmp_path, noi_dung="Bản tin thử"):
    (tmp_path / "tin.txt").write_text(noi_dung, encoding="utf-8")
    return tmp_path


def _args(cli, *argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ngay")
    return ap.parse_args(list(argv))


def test_gui_thieu_secret_la_canh_bao_ma_thoat_0_va_khong_goi_mang(tmp_path, capsys):
    cli = _cli()
    for env in ({}, {"TELEGRAM_BOT_TOKEN": TOKEN}, {"TELEGRAM_CHAT_ID": CHAT},
                {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": CHAT}):
        post = Post()
        assert cli.gui(_args(cli, "--ngay", D), env=env, post=post,
                       thu_muc=_co_tin(tmp_path)) == 0
        out = capsys.readouterr().out
        assert out.startswith("::warning::") and "không phải sự cố" in out
        assert post.goi == []
        assert not (tmp_path / "da_gui").exists()          # chưa gửi thì KHÔNG ghi dấu


def test_gui_thanh_cong_ghi_dau_theo_ngay_va_khong_in_token(tmp_path, capsys):
    cli, post = _cli(), Post(OK)
    assert cli.gui(_args(cli, "--ngay", D), env=ENV, post=post, thu_muc=_co_tin(tmp_path)) == 0
    out = capsys.readouterr()
    assert TOKEN not in out.out + out.err and CHAT not in out.out + out.err
    assert (tmp_path / "da_gui" / f"{D}.txt").is_file()
    assert post.goi[0][1]["text"] == "Bản tin thử"


def test_gui_telegram_loi_thi_ma_1_khong_ghi_dau_va_khong_lo_token(tmp_path, capsys):
    cli = _cli()
    post = Post((401, {"ok": False, "description": "Unauthorized"}))
    assert cli.gui(_args(cli, "--ngay", D), env=ENV, post=post, thu_muc=_co_tin(tmp_path)) == 1
    out = capsys.readouterr()
    assert out.out.startswith("::error::") and "Unauthorized" in out.out
    assert TOKEN not in out.out + out.err
    assert not (tmp_path / "da_gui").exists()              # hỏng thì lượt sau phải gửi lại được


def test_gui_nhieu_tin_hong_o_tin_hai_thi_khong_ghi_dau(tmp_path):
    cli = _cli()
    dai = "\n".join(f"dòng {i} " + "x" * 80 for i in range(120))     # ~10.000 ký tự: 3 tin
    post = Post(OK, (500, {"ok": False, "description": "boom"}))
    assert cli.gui(_args(cli, "--ngay", D), env=ENV, post=post,
                   thu_muc=_co_tin(tmp_path, dai), ngu=lambda s: None) == 1
    assert len(post.goi) == 2 and not (tmp_path / "da_gui").exists()


def test_gui_khong_co_tin_da_dung_hay_tin_rong_la_ma_2(tmp_path):
    cli = _cli()
    assert cli.gui(_args(cli, "--ngay", D), env=ENV, post=Post(), thu_muc=tmp_path) == 2
    assert cli.gui(_args(cli, "--ngay", D), env=ENV, post=Post(),
                   thu_muc=_co_tin(tmp_path, "\n \n")) == 2


def test_kiem_tra_kenh_gui_mot_tin_thu_va_khong_ghi_dau(tmp_path, capsys):
    cli, post = _cli(), Post(OK)
    assert cli.kiem_tra_kenh(env=ENV, post=post) == 0
    assert [p[1]["text"] for p in post.goi] == [cli.TIN_KIEM_TRA]
    assert "không phải bản tin" in cli.TIN_KIEM_TRA
    assert cli.kiem_tra_kenh(env={}, post=Post()) == 0
    assert capsys.readouterr().out.count("::warning::") == 1
    assert cli.kiem_tra_kenh(env=ENV, post=Post((403, {"description": "Forbidden"}))) == 1


# ─────────────────────────────────────────────────────────────────────
# 6. Lệnh con `chuan-bi` (đọc sổ giả, không mạng)
# ─────────────────────────────────────────────────────────────────────
def _chuan_bi(tmp_path, monkeypatch, sheet=None, hom_nay=D, vni=None, ngay=None):
    cli = _cli()
    dau_ra = tmp_path / "dau_ra.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(dau_ra))
    j, bc = _so_tam(tmp_path, sheet or _sheet_day_du())
    thu = tmp_path / "tm"
    ma = cli.chuan_bi(_args(cli, *(["--ngay", ngay] if ngay else [])), keo=lambda: (j, bc),
                      vni=vni or (lambda: _vni(("2026-10-08", 1700), ("2026-10-09", 1717, 1700))),
                      hom_nay=hom_nay, thu_muc=thu)
    ra = dict(d.split("=", 1) for d in dau_ra.read_text(encoding="utf-8").splitlines()) \
        if dau_ra.exists() else {}
    return ma, ra, thu


def test_chuan_bi_dung_ban_tin_ghi_tep_va_ba_dau_ra(tmp_path, monkeypatch):
    ma, ra, thu = _chuan_bi(tmp_path, monkeypatch)
    assert ma == 0
    assert ra == {"san_sang": "true", "ngay": D, "khoa": tt.khoa_da_gui(D)}
    van = (thu / "tin.txt").read_text(encoding="utf-8")
    assert "Bản tin cuối ngày 2026-10-09" in van and "Đã chấm 2 mã" in van
    assert "VN-INDEX đóng cửa 1,717.00" in van and "**" not in van
    assert f"đạt ngưỡng {BUY_THRESHOLD:g}" in van            # ngưỡng của đường chạy thật, không gõ lại
    assert "Không phải khuyến nghị đặt lệnh thật." in van


def test_chuan_bi_sau_nua_dem_van_lay_ngay_cua_so(tmp_path, monkeypatch):
    ma, ra, _ = _chuan_bi(tmp_path, monkeypatch, hom_nay="2026-10-10")
    assert ma == 0 and ra["san_sang"] == "true" and ra["ngay"] == D


def test_chuan_bi_so_cu_qua_thi_khong_gui_va_khong_tao_tep(tmp_path, monkeypatch, capsys):
    ma, ra, thu = _chuan_bi(tmp_path, monkeypatch, hom_nay="2026-10-20")
    assert ma == 0 and ra == {"san_sang": "false", "ngay": "", "khoa": ""}
    assert not (thu / "tin.txt").exists()
    assert "::notice::Không gửi bản tin" in capsys.readouterr().out


def test_chuan_bi_so_rong_khong_gui_ma_thoat_0(tmp_path, monkeypatch):
    ma, ra, _ = _chuan_bi(tmp_path, monkeypatch, sheet=_SoChiDoc())
    assert ma == 0 and ra["san_sang"] == "false"


def test_chuan_bi_ngay_ep_khong_co_quyet_dinh_thi_khong_gui(tmp_path, monkeypatch, capsys):
    ma, ra, thu = _chuan_bi(tmp_path, monkeypatch, ngay="2026-10-08")
    assert ma == 0 and ra["san_sang"] == "false" and not (thu / "tin.txt").exists()
    assert "sổ không có quyết định nào cho ngày 2026-10-08" in capsys.readouterr().out


def test_chuan_bi_khong_doc_duoc_so_la_ma_2(tmp_path, monkeypatch, capsys):
    cli = _cli()
    assert cli.chuan_bi(_args(cli), keo=lambda: None, thu_muc=tmp_path) == 2
    assert "::error::" in capsys.readouterr().out

    def no():
        raise OSError("hết hạn mức")
    assert cli.chuan_bi(_args(cli), keo=no, thu_muc=tmp_path) == 2
    assert "hết hạn mức" in capsys.readouterr().out


def test_chuan_bi_vni_hong_van_ra_ban_tin_co_ghi_chu(tmp_path, monkeypatch):
    def hong():
        raise RuntimeError("mất mạng")
    ma, ra, thu = _chuan_bi(tmp_path, monkeypatch, vni=hong)
    assert ma == 0 and ra["san_sang"] == "true"
    assert "không đọc được bảng giá" in (thu / "tin.txt").read_text(encoding="utf-8")


def test_ghi_dau_ra_khong_co_github_output_thi_in(capsys):
    _cli().ghi_dau_ra({"a": "1"}, env={})
    assert capsys.readouterr().out == "a=1\n"


def test_main_lenh_con_va_ngay_sai_dinh_dang():
    cli = _cli()
    with pytest.raises(SystemExit) as e:
        cli.main(["chuan-bi", "--ngay", "09/10/2026"])
    assert e.value.code == 2
    with pytest.raises(SystemExit):
        cli.main([])
    assert cli.main(["kiem-tra-kenh"], env={}) == 0


def test_hom_nay_vn_la_ngay_iso():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", _cli()._hom_nay_vn())


# ─────────────────────────────────────────────────────────────────────
# 7. AST: module thuần · công cụ chỉ đọc sổ · token không vào dòng in
# ─────────────────────────────────────────────────────────────────────
def _cay(duong):
    return ast.parse((GOC / duong).read_text(encoding="utf-8"))


def _nhap_va_goi(cay):
    nhap, goi = set(), set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            nhap.add((n.module or "").split(".")[0])
        elif isinstance(n, ast.Call):
            f = n.func
            goi.add(f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else "")
    return nhap, goi


def test_module_thuan_chi_nhap_thu_vien_chuan_va_lich_va_khong_vao_ra():
    nhap, goi = _nhap_va_goi(_cay("tin_telegram.py"))
    assert nhap <= {"__future__", "datetime", "re", "typing", "lich_giao_dich"}, nhap
    assert not ({"print", "open", "write_text", "urlopen", "now", "today", "utcnow", "sleep",
                 "getenv", "environ", "input"} & goi), sorted(goi)


def test_chi_cong_cu_gui_duoc_nhap_tin_telegram_va_duong_giao_dich_khong():
    ten_cam = {"run_daily.py", "paper_trading.py", "paper_runner.py", "paper_metrics.py",
               "master_agent.py", "analysis_agents.py", "debate_agents.py", "walkforward.py",
               "sheets_store.py", "google_sheets_sync.py", "ban_tin.py", "app.py"}
    nguoi_nhap = set()
    bo = {"tests", ".venv", ".git", "__pycache__", "node_modules"}
    for p in duyet_repo.duyet(GOC, "*.py"):
        if set(p.relative_to(GOC).parts) & bo:
            continue
        nhap, _ = _nhap_va_goi(ast.parse(p.read_text(encoding="utf-8")))
        if "tin_telegram" in nhap:
            nguoi_nhap.add(p.relative_to(GOC).as_posix())
    assert nguoi_nhap == {"tools/gui_ban_tin_telegram.py"}, nguoi_nhap
    assert not (nguoi_nhap & ten_cam)


def test_cong_cu_gui_khong_ghi_so_khong_nhap_kho_ngoai_va_chi_doc_qua_duong_keo_an_toan():
    cay = _cay("tools/gui_ban_tin_telegram.py")
    nhap, goi = _nhap_va_goi(cay)
    assert not ({"sheets_store", "google_sheets_sync", "requests", "gspread"} & nhap), nhap
    assert not ({"push", "write_all", "append_rows", "pull", "record_trade", "update_trade",
                 "record_decision", "commit", "executemany", "executescript", "execute",
                 "unlink", "rmtree", "to_csv"} & goi), sorted(goi)
    tham_chieu = {n.attr for n in ast.walk(cay) if isinstance(n, ast.Attribute)}
    assert "keo_ve_so_tam" in tham_chieu
    assert "reconfigure" in ast.unparse(cay) and "sys.stdout" in ast.unparse(cay)


def test_ngay_bien_token_va_chat_id_chi_vao_in_hay_loi_khi_boc_trong_che_bi_mat():
    """Mọi `print(...)` và `LoiTelegram(...)` trong công cụ: nếu nhắc tên `token`/`chat_id`/
    `kenh` thì nhắc BÊN TRONG một lời gọi `che_bi_mat`."""
    cay = _cay("tools/gui_ban_tin_telegram.py")
    nhay_cam = {"token", "chat_id", "kenh"}
    n_kiem = 0
    for n in ast.walk(cay):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in {"print", "LoiTelegram"}):
            continue
        n_kiem += 1
        trong_che = set()
        for c in ast.walk(n):
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) \
                    and c.func.attr == "che_bi_mat":
                trong_che |= {id(x) for x in ast.walk(c)}
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and x.id in nhay_cam:
                assert id(x) in trong_che, f"dòng {n.lineno}: `{x.id}` có thể bị in ra"
    assert n_kiem >= 8, "gác không thấy đủ lời gọi print/LoiTelegram — bộ duyệt hỏng?"


def test_post_http_la_noi_duy_nhat_goi_urlopen_va_chi_toi_api_telegram_qua_gui_cac_tin():
    cay = _cay("tools/gui_ban_tin_telegram.py")
    ham = [n for n in cay.body if isinstance(n, ast.FunctionDef)
           and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                   and c.func.attr == "urlopen" for c in ast.walk(n))]
    assert [h.name for h in ham] == ["post_http"]
    nguon = ast.unparse(cay)
    assert nguon.count("api.telegram.org") == 1 and nguon.count("/sendMessage") == 1


# ─────────────────────────────────────────────────────────────────────
# 8. Workflow (đọc văn bản, bỏ dòng chú thích)
# ─────────────────────────────────────────────────────────────────────
def _wf_dong():
    return [d for d in WF.read_text(encoding="utf-8").splitlines()
            if d.strip() and not d.lstrip().startswith("#")]


def _wf():
    return "\n".join(_wf_dong())


def _buoc():
    """Danh sách bước: mỗi bước = chuỗi các dòng bắt đầu từ `      - `."""
    ra, hien, trong = [], None, False
    for d in _wf_dong():
        if d.startswith("    steps:"):
            trong = True
            continue
        if not trong:
            continue
        if d.startswith("      - "):
            hien = [d]
            ra.append(hien)
        elif hien is not None:
            hien.append(d)
    return ["\n".join(b) for b in ra]


def _chi_so(buoc, mau):
    xs = [i for i, b in enumerate(buoc) if mau in b]
    assert len(xs) == 1, f"{mau!r}: thấy {len(xs)} bước"
    return xs[0]


def test_workflow_bam_vao_dung_ten_workflow_quet_va_khong_co_cron():
    ten = re.search(r"^name:\s*(.+)$", (GOC / ".github/workflows/quet-so-lenh.yml")
                    .read_text(encoding="utf-8"), re.M).group(1).strip()
    w = _wf()
    assert f'workflows: ["{ten}"]' in w, f"tên workflow quét đang là {ten!r}"
    assert "types: [completed]" in w and "workflow_run:" in w
    assert "schedule:" not in w and "cron" not in w, "giờ cron là đoán (GitHub trễ 4–10 giờ)"


def test_job_chi_chay_khi_luot_quet_success_hoac_bam_tay():
    assert ("if: github.event_name != 'workflow_run' || "
            "github.event.workflow_run.conclusion == 'success'") in _wf()


def test_concurrency_rieng_va_khong_huy_luot_dang_chay():
    w = _wf()
    assert "group: gui-ban-tin-telegram" in w and "cancel-in-progress: false" in w
    assert "group: quet-so-lenh" not in w


def test_quyen_chi_doc_va_khong_ghi_so_hay_chay_quet():
    w = _wf()
    assert re.search(r"permissions:\n  contents: read\n", w)
    for cam in ("run_daily", "sheets_store", "push(", "paper_trading", "gh workflow run",
                "contents: write", "issues: write"):
        assert cam not in w, cam


def test_secret_dung_hai_ten_va_token_chi_nam_o_ba_buoc_can_no():
    w = _wf()
    assert set(re.findall(r"secrets\.(TELEGRAM_\w+)", w)) == {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}
    buoc = _buoc()
    co_token = [b for b in buoc if "secrets.TELEGRAM_BOT_TOKEN" in b]
    assert len(co_token) == 3
    assert {("kiem-tra-kenh" in b) or ("gui --ngay" in b) or ("id: kenh" in b) for b in co_token} == {True}
    # không bước nào IN token ra; chỉ `::add-mask::` được nhắc nó trong `run`
    for b in buoc:
        for d in b.splitlines():
            if "$TELEGRAM_BOT_TOKEN" in d:
                assert "::add-mask::" in d or "-n " in d or "-z " in d, d
    assert '"::add-mask::$TELEGRAM_BOT_TOKEN"' in w


def test_thieu_secret_la_warning_roi_thoat_0_khong_exit_1():
    b = _buoc()[_chi_so(_buoc(), "id: kenh")]
    assert "::warning::" in b and "co=false" in b and "co=true" in b
    assert "exit" not in b                                       # không làm đỏ job
    for ten in ("setup-python", "pip install", "id: tin", "kiem-tra-kenh"):
        assert "steps.kenh.outputs.co == 'true'" in _buoc()[_chi_so(_buoc(), ten)], ten
    # bước dựng bản tin bị bỏ qua thì `san_sang` rỗng và mọi bước sau (tra dấu, gửi, ghi dấu) đứng yên
    assert "steps.tin.outputs.san_sang == 'true'" in _buoc()[_chi_so(_buoc(), "id: dau")]


def test_thu_tu_dung_ban_tin_tra_dau_gui_ghi_dau():
    buoc = _buoc()
    i = [_chi_so(buoc, m) for m in ("id: tin", "id: dau", "id: gui", "actions/cache/save")]
    assert i == sorted(i) and len(set(i)) == 4
    assert _chi_so(buoc, "id: kenh") < _chi_so(buoc, "setup-python") < _chi_so(buoc, "id: tin")


def test_khoa_dau_da_gui_lay_tu_dau_ra_cua_cong_cu_o_ca_hai_cho_va_chi_tra_cuu_truoc_khi_gui():
    buoc = _buoc()
    tra, ghi = buoc[_chi_so(buoc, "id: dau")], buoc[_chi_so(buoc, "actions/cache/save")]
    for b in (tra, ghi):
        assert "key: ${{ steps.tin.outputs.khoa }}" in b
        assert "path: .ban_tin_telegram/da_gui" in b
    assert "actions/cache/restore@" in tra and "lookup-only: true" in tra
    assert "run_id" not in _wf() and "github.sha" not in ghi


def test_chi_gui_khi_san_sang_va_chua_co_dau_va_chi_ghi_dau_khi_buoc_gui_thanh_cong():
    buoc = _buoc()
    gui = buoc[_chi_so(buoc, "id: gui")]
    assert "steps.tin.outputs.san_sang == 'true'" in gui
    assert "steps.dau.outputs.cache-hit != 'true'" in gui
    ghi = buoc[_chi_so(buoc, "actions/cache/save")]
    assert "if: steps.gui.outcome == 'success'" in ghi
    assert "steps.dau.outputs.cache-hit == 'true'" in buoc[_chi_so(buoc, "đã gửi ở lượt trước")]
    assert "gui --ngay" in gui


def test_dau_ra_workflow_doc_la_dau_ra_cong_cu_ghi(tmp_path, monkeypatch):
    doc = set(re.findall(r"steps\.tin\.outputs\.(\w+)", _wf()))
    _, ra, _ = _chuan_bi(tmp_path, monkeypatch)
    assert doc <= set(ra), (doc, set(ra))
    assert doc == {"san_sang", "ngay", "khoa"}


def test_dispatch_co_o_kiem_tra_kenh_va_job_tat_telemetry_vnstock():
    w = _wf()
    assert "workflow_dispatch:" in w and "kiem_tra_kenh:" in w and "type: boolean" in w
    assert 'VNSTOCK_TELEMETRY: "off"' in w
    assert "pip install -r requirements.txt" in w


def test_lenh_chay_cong_cu_la_ba_lenh_con_that():
    cli = _cli()
    lenh = set(re.findall(r"tools/gui_ban_tin_telegram\.py (\S+)", _wf()))
    assert lenh == {"kiem-tra-kenh", "chuan-bi", "gui"}
    assert callable(cli.main)


# ─────────────────────────────────────────────────────────────────────
# 9. Tài liệu khớp
# ─────────────────────────────────────────────────────────────────────
def test_moi_workflow_trong_thu_muc_co_mat_trong_bang_handoff_muc_2():
    handoff = (GOC / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
    thieu = [p.name for p in sorted((GOC / ".github" / "workflows").glob("*.yml"))
             if f"`{p.name}`" not in handoff]
    assert not thieu, f"workflow chưa có trong bảng HANDOFF mục 2: {thieu}"
    hang = [d for d in handoff.splitlines() if d.startswith("| `gui-ban-tin-telegram.yml`")]
    assert len(hang) == 1
    assert "TELEGRAM_BOT_TOKEN" in hang[0] and "TELEGRAM_CHAT_ID" in hang[0]
    assert "STREAMLIT_SECRETS_TOML" in hang[0]


def test_con_so_workflow_trong_tai_lieu_khop_so_file():
    n = len(list((GOC / ".github" / "workflows").glob("*.yml")))
    chu = {8: "Tám", 9: "Chín", 10: "Mười"}[n]
    handoff = (GOC / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
    assert f"**{chu} workflow đang bật**" in handoff
    claude = (GOC / "CLAUDE.md").read_text(encoding="utf-8")
    assert f"**{chu} workflow bật**" in claude
