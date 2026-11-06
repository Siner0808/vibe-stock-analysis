"""Gửi bản tin cuối ngày của sổ lệnh ẢO tới Telegram — CHỈ ĐỌC sổ (BƯỚC 258, mốc B2 / T3).

    python tools/gui_ban_tin_telegram.py chuan-bi [--ngay YYYY-MM-DD]
    python tools/gui_ban_tin_telegram.py gui
    python tools/gui_ban_tin_telegram.py kiem-tra-kenh

Ba lệnh con, workflow `gui-ban-tin-telegram.yml` gọi lần lượt:

· `chuan-bi` — kéo sổ THẬT vào DB tạm (cùng đường với `tools/ban_tin.py`), chọn ngày bằng
  `tin_telegram.chon_ngay`, dựng bản tin, ghi `.ban_tin_telegram/tin.txt` và in ba dòng
  `san_sang=` · `ngay=` · `khoa=` vào `$GITHUB_OUTPUT`. KHÔNG cần secret Telegram. Không có gì để
  gửi (không phải phiên, sổ chưa có ngày mới) là mã thoát 0 với `san_sang=false`; không đọc được
  sổ là mã thoát 2 (job đỏ — GitHub gửi email).
· `gui` — đọc `tin.txt`, tách ≤ 4096 ký tự, POST `sendMessage`. Thiếu `TELEGRAM_BOT_TOKEN` hay
  `TELEGRAM_CHAT_ID` thì `::warning::` rồi thoát 0 (chưa cấu hình không phải sự cố). Telegram trả
  lỗi thì thoát 1. Gửi XONG mới ghi dấu `.ban_tin_telegram/da_gui/<ngày>.txt` (workflow lưu dấu
  ấy vào cache, khoá `khoa_da_gui`).
· `kiem-tra-kenh` — một tin ngắn, không phải bản tin, không đụng dấu "đã gửi"; để người dùng
  thử secret vừa đặt.

TOKEN KHÔNG BAO GIỜ được in: URL của Bot API chứa token, nên mọi lỗi được che bằng
`tin_telegram.che_bi_mat` và chỉ in loại lỗi + mã HTTP + `description` của Telegram.

Mã thoát: 0 xong hoặc bỏ qua có chủ đích · 1 Telegram từ chối · 2 không đọc được sổ / dùng sai lệnh.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import ban_tin  # noqa: E402
import doc_so_that  # noqa: E402
import tin_telegram as tt  # noqa: E402
from paper_trading import BUY_THRESHOLD  # noqa: E402

THU_MUC = ".ban_tin_telegram"
TEP_TIN = "tin.txt"
THU_MUC_DAU = "da_gui"
MUI_GIO_VN = datetime.timezone(datetime.timedelta(hours=7))
THOI_GIAN_CHO_GIAY = 30
SO_LAN_THU_LAI_429 = 2
TOI_DA_CHO_429_GIAY = 30
GIAN_CACH_GIUA_TIN_GIAY = 1.0
TIN_KIEM_TRA = ("Kênh Telegram của bản tin cuối ngày hoạt động. "
                "Đây là tin thử, không phải bản tin.")


class LoiTelegram(Exception):
    """Telegram từ chối hoặc không gọi được. Thông điệp đã được che bí mật."""


def _cli_ban_tin():
    """`tools/ban_tin.py` (CLI đọc sổ) — nạp theo đường dẫn vì tên trùng module gốc `ban_tin`."""
    spec = importlib.util.spec_from_file_location("ban_tin_cli", GOC / "tools" / "ban_tin.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def post_http(url: str, payload: dict, timeout: int = THOI_GIAN_CHO_GIAY) -> tuple[int, dict]:
    """POST JSON, trả (mã HTTP, thân JSON). Lỗi mạng cho nổ — người gọi che bí mật."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ma, tho = r.status, r.read()
    except urllib.error.HTTPError as e:
        ma, tho = e.code, e.read()
    try:
        than = json.loads(tho.decode("utf-8"))
    except ValueError:
        than = {}
    return ma, than if isinstance(than, dict) else {}


def gui_cac_tin(cac_tin: list[str], token: str, chat_id: str, post=post_http,
                ngu=time.sleep) -> int:
    """Gửi lần lượt từng tin; trả số tin đã gửi. Lỗi thì nổ `LoiTelegram` (đã che token).

    Chỉ thử lại khi 429 (Telegram nói rõ CHƯA gửi). Hết giờ chờ hay lỗi mạng thì KHÔNG thử lại:
    tin có thể đã tới, gửi lại là gửi đôi.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    da_gui = 0
    for i, tin in enumerate(cac_tin):
        if i:
            ngu(GIAN_CACH_GIUA_TIN_GIAY)
        for lan in range(SO_LAN_THU_LAI_429 + 1):
            try:
                ma, than = post(url, {"chat_id": chat_id, "text": tin,
                                      "disable_web_page_preview": True})
            except Exception as e:
                raise LoiTelegram(tt.che_bi_mat(
                    f"không gọi được Telegram ({type(e).__name__}: {e}); tin "
                    f"{i + 1}/{len(cac_tin)} có thể đã tới hoặc chưa", token, chat_id)) from None
            if ma == 200 and than.get("ok") is True:
                da_gui += 1
                break
            if ma == 429 and lan < SO_LAN_THU_LAI_429:
                cho = (than.get("parameters") or {}).get("retry_after")
                ngu(min(float(cho), TOI_DA_CHO_429_GIAY) if isinstance(cho, (int, float))
                    else 5.0)
                continue
            raise LoiTelegram(tt.che_bi_mat(
                f"Telegram trả HTTP {ma} cho tin {i + 1}/{len(cac_tin)}: "
                f"{than.get('description') or 'không có mô tả'}", token, chat_id))
    return da_gui


def ghi_dau_ra(cap: dict, env=None) -> None:
    """Ghi `khoá=giá trị` vào `$GITHUB_OUTPUT`; ngoài Actions thì in ra màn hình."""
    env = os.environ if env is None else env
    dong = "".join(f"{k}={v}\n" for k, v in cap.items())
    duong = env.get("GITHUB_OUTPUT")
    if duong:
        with open(duong, "a", encoding="utf-8") as f:
            f.write(dong)
    else:
        print(dong, end="")


def _hom_nay_vn() -> str:
    return datetime.datetime.now(MUI_GIO_VN).date().isoformat()


def chuan_bi(a, keo=None, vni=None, hom_nay=None, thu_muc: Path | None = None) -> int:
    thu_muc = thu_muc or Path(THU_MUC)
    cli = _cli_ban_tin()
    try:
        ra = (keo or doc_so_that.keo_ve_so_tam)()
    except Exception as e:
        print(f"::error::Không đọc được sổ — {type(e).__name__}: {e}")
        return 2  # bia-ok: mã thoát tiến trình (2 = không đọc được sổ), không phải số đo
    if ra is None:
        print("::error::Kho ngoài chưa cấu hình — không đọc được sổ, không đoán gì cả.")
        return 2
    so, _bao_cao = ra
    bang = cli.doc_ba_bang(so.db)

    if a.ngay:
        ngay, ly_do, canh_bao = a.ngay, "", None
    else:
        q = tt.chon_ngay(ban_tin.ngay_gan_nhat(bang["quyet_dinh"]), hom_nay or _hom_nay_vn())
        ngay, ly_do, canh_bao = q.ngay, q.ly_do, q.canh_bao
    if canh_bao:
        print(f"::warning::{canh_bao}")
    if ngay is None:
        print(f"::notice::Không gửi bản tin — {ly_do}.")
        ghi_dau_ra({"san_sang": "false", "ngay": "", "khoa": ""})
        return 0

    try:
        vni_df = (vni or cli._vni_mac_dinh)()
    except Exception as e:
        print(f"[canh bao] khong doc duoc VN-INDEX — {type(e).__name__}: {e}", file=sys.stderr)
        vni_df = None
    bt = ban_tin.lap_ban_tin(bang["quyet_dinh"], bang["lenh"], bang["nhat_ky"],
                             vni_df, ngay, BUY_THRESHOLD)
    van_ban = tt.markdown_sang_van_ban(ban_tin.ban_tin_markdown(bt))
    if not bt.co_quyet_dinh:
        print(f"::notice::Không gửi bản tin — sổ không có quyết định nào cho ngày {ngay}.")
        ghi_dau_ra({"san_sang": "false", "ngay": ngay, "khoa": ""})
        return 0
    thu_muc.mkdir(parents=True, exist_ok=True)
    (thu_muc / TEP_TIN).write_text(van_ban, encoding="utf-8")
    print(f"Đã dựng bản tin ngày {ngay}: {len(van_ban)} ký tự, "
          f"{len(tt.chia_tin(van_ban))} tin.")
    ghi_dau_ra({"san_sang": "true", "ngay": ngay, "khoa": tt.khoa_da_gui(ngay)})
    return 0


def _doc_secret(env) -> tuple[str, str] | None:
    thieu = tt.thieu_secret(env)
    if thieu:
        print(f"::warning::Chưa đặt secret {', '.join(thieu)} — bỏ qua việc gửi Telegram "
              f"(không phải sự cố). Đặt ở Settings → Secrets and variables → Actions.")
        return None
    return env[tt.BIEN_TOKEN].strip(), env[tt.BIEN_CHAT_ID].strip()


def gui(a, env=None, post=post_http, ngu=time.sleep, thu_muc: Path | None = None) -> int:
    env = os.environ if env is None else env
    thu_muc = thu_muc or Path(THU_MUC)
    kenh = _doc_secret(env)
    if kenh is None:
        return 0
    token, chat_id = kenh
    tep = thu_muc / TEP_TIN
    if not tep.is_file():
        print("::error::Không thấy bản tin đã dựng (lệnh `chuan-bi` chưa chạy hoặc hỏng).")
        return 2
    cac_tin = tt.chia_tin(tep.read_text(encoding="utf-8"))
    if not cac_tin:
        print("::error::Bản tin rỗng — không gửi.")
        return 2
    try:
        n = gui_cac_tin(cac_tin, token, chat_id, post=post, ngu=ngu)
    except LoiTelegram as e:
        print(f"::error::{e}")
        return 1  # bia-ok: mã thoát tiến trình (1 = Telegram từ chối), không phải số đo
    print(f"Đã gửi {n} tin Telegram.")
    ngay = (a.ngay or "").strip()
    if ngay:
        dau = thu_muc / THU_MUC_DAU
        dau.mkdir(parents=True, exist_ok=True)
        (dau / f"{ngay}.txt").write_text("đã gửi\n", encoding="utf-8")
    return 0


def kiem_tra_kenh(env=None, post=post_http, ngu=time.sleep) -> int:
    env = os.environ if env is None else env
    kenh = _doc_secret(env)
    if kenh is None:
        return 0
    try:
        gui_cac_tin([TIN_KIEM_TRA], kenh[0], kenh[1], post=post, ngu=ngu)
    except LoiTelegram as e:
        print(f"::error::{e}")
        return 1  # bia-ok: mã thoát tiến trình (1 = Telegram từ chối), không phải số đo
    print("Đã gửi tin thử.")
    return 0


def main(argv=None, **kw) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="lenh", required=True)
    p1 = sub.add_parser("chuan-bi")
    p1.add_argument("--ngay", help="ép ngày tín hiệu YYYY-MM-DD (bỏ qua lịch và độ tuổi)")
    p2 = sub.add_parser("gui")
    p2.add_argument("--ngay", help="ngày của bản tin, để ghi dấu 'đã gửi'")
    sub.add_parser("kiem-tra-kenh")
    a = ap.parse_args(argv)
    if getattr(a, "ngay", None):
        try:
            datetime.date.fromisoformat(a.ngay)
        except ValueError:
            ap.error(f"--ngay phải là YYYY-MM-DD, nhận {a.ngay!r}")
    if a.lenh == "chuan-bi":
        return chuan_bi(a, **kw)
    if a.lenh == "gui":
        return gui(a, **kw)
    return kiem_tra_kenh(**kw)


if __name__ == "__main__":
    raise SystemExit(main())
