#!/usr/bin/env python3
"""
nap_service_account.py — nạp file JSON service account vào secrets.toml.

VÌ SAO CÓ CÔNG CỤ NÀY
─────────────────────
Google cho tải service account dưới dạng JSON, nhưng Streamlit đọc TOML.
Chuyển tay là chỗ hỏng nhiều nhất, vì `private_key` dài ~1.700 ký tự và
phải nằm trên MỘT dòng với các ký tự `\\n` giữ nguyên theo nghĩa đen. Chỉ
cần trình soạn thảo tự xuống dòng là key hỏng, và thông báo lỗi khi đó
("Could not deserialize key data") không hề chỉ ra nguyên nhân thật.

Công cụ này chạy hoàn toàn trên máy bạn. Nó KHÔNG in giá trị bí mật ra
màn hình — chỉ in tên trường và vân tay rút gọn để đối chiếu.

DÙNG
────
    # Có key mới tải về (sau khi xoay key):
    python tools/nap_service_account.py ~/Downloads/gen-lang-...json

    # Chỉ muốn lấy phần dán lên cloud từ secrets.toml đang có:
    python tools/nap_service_account.py --tu-secrets

Cả hai đều ghi ra `.streamlit/secrets_cloud_paste.txt` — phần cần dán THÊM
vào Streamlit Cloud. File đó đã được gitignore sẵn theo luật `*.txt`.

Bản dán KHÔNG gồm VNSTOCK_API_KEY và GEMINI_API_KEY: trên cloud chúng đang
có giá trị thật, còn bản local đang rỗng — dán đè sẽ xoá mất key đang chạy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Console Windows mặc định cp1258, không mã hoá nổi tiếng Việt. Thiếu
# dòng này thì script chết ở lệnh print đầu tiên, TRƯỚC khi làm được
# việc gì — và một công cụ không chạy được cũng là một cổng xanh giả.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

GOC = Path(__file__).resolve().parent.parent
SECRETS = GOC / ".streamlit" / "secrets.toml"
BAN_DAN = GOC / ".streamlit" / "secrets_cloud_paste.txt"
KHOI = "[gcp_service_account]"

TRUONG = ("type", "project_id", "private_key_id", "private_key",
          "client_email", "client_id", "auth_uri", "token_uri",
          "auth_provider_x509_cert_url", "client_x509_cert_url",
          "universe_domain")


def _toml_khoi(sa: dict) -> str:
    """Dựng khối TOML. json.dumps lo phần escape `\\n` trong private_key —
    đúng thứ mà chuyển tay hay làm hỏng."""
    dong = [KHOI]
    for k in TRUONG:
        dong.append(f"{k} = {json.dumps(sa[k], ensure_ascii=False)}")
    return "\n".join(dong) + "\n"


def _thay_khoi(noi_dung: str, khoi_moi: str) -> str:
    """Thay khối [gcp_service_account], giữ nguyên phần còn lại kèm chú thích."""
    dong = noi_dung.splitlines(keepends=True)
    dau = next((i for i, d in enumerate(dong) if d.strip() == KHOI), None)
    if dau is None:
        return noi_dung.rstrip("\n") + "\n\n" + khoi_moi

    cuoi = len(dong)
    for i in range(dau + 1, len(dong)):
        s = dong[i].strip()
        if s.startswith("[") and s.endswith("]"):
            cuoi = i
            break
    return "".join(dong[:dau]) + khoi_moi + "".join(dong[cuoi:])


def _ghi_ban_dan(khoi: str) -> None:
    import tomllib
    sheet_key = tomllib.loads(
        SECRETS.read_text(encoding="utf-8")).get("GOOGLE_SHEET_KEY", "")
    BAN_DAN.write_text(
        "# Dán THÊM phần này vào Streamlit Cloud > Settings > Secrets.\n"
        "# GIỮ NGUYÊN dòng VNSTOCK_API_KEY đang có sẵn trên đó.\n\n"
        f'GOOGLE_SHEET_KEY = "{sheet_key}"\n\n' + khoi,
        encoding="utf-8")


def _tu_secrets() -> int:
    """Dựng bản dán từ secrets.toml đang có — không cần file JSON mới."""
    import tomllib
    if not SECRETS.exists():
        print(f"❌ Chưa có {SECRETS.relative_to(GOC)}")
        return 1
    d = tomllib.loads(SECRETS.read_text(encoding="utf-8"))
    sa = d.get("gcp_service_account")
    if not sa:
        print(f"❌ {SECRETS.relative_to(GOC)} chưa có khối {KHOI}")
        return 1
    thieu = [k for k in TRUONG if not str(sa.get(k, "")).strip()]
    if thieu:
        print(f"❌ Thiếu {len(thieu)} trường: {', '.join(thieu)}")
        return 1

    _ghi_ban_dan(_toml_khoi(sa))
    print(f"✅ Đã ghi bản dán: {BAN_DAN.relative_to(GOC)}")
    print()
    print("Đối chiếu (không in giá trị bí mật):")
    print(f"  GOOGLE_SHEET_KEY : {d.get('GOOGLE_SHEET_KEY', '')}")
    print(f"  client_email     : {sa['client_email']}")
    print(f"  private_key_id   : {str(sa['private_key_id'])[:8]}…")
    print(f"  private_key      : {len(sa['private_key'])} ký tự")
    print()
    print(f"Mở file trên, chép toàn bộ, dán THÊM vào Streamlit Cloud.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--tu-secrets":
        return _tu_secrets()

    if len(argv) != 2:
        print(__doc__)
        return 2

    nguon = Path(argv[1]).expanduser()
    if not nguon.exists():
        print(f"❌ Không thấy file: {nguon}")
        return 1

    try:
        sa = json.loads(nguon.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ Không phải JSON hợp lệ: {e}")
        return 1

    thieu = [k for k in TRUONG if k not in sa or not str(sa[k]).strip()]
    if thieu:
        print(f"❌ File JSON thiếu {len(thieu)} trường: {', '.join(thieu)}")
        print("   Tải đúng file 'Create new key -> JSON' của service account.")
        return 1

    if not str(sa["private_key"]).startswith("-----BEGIN PRIVATE KEY-----"):
        print("❌ private_key không đúng định dạng PEM.")
        return 1

    khoi = _toml_khoi(sa)

    if SECRETS.exists():
        cu = SECRETS.read_text(encoding="utf-8")
        SECRETS.write_text(_thay_khoi(cu, khoi), encoding="utf-8")
        print(f"✅ Đã cập nhật {KHOI} trong {SECRETS.relative_to(GOC)}")
    else:
        SECRETS.parent.mkdir(parents=True, exist_ok=True)
        SECRETS.write_text(khoi, encoding="utf-8")
        print(f"✅ Đã tạo {SECRETS.relative_to(GOC)}")

    _ghi_ban_dan(khoi)
    print(f"✅ Đã ghi phần dán lên cloud: {BAN_DAN.relative_to(GOC)}")
    print()
    print("Đối chiếu (không in giá trị bí mật):")
    print(f"  client_email   : {sa['client_email']}")
    print(f"  project_id     : {sa['project_id']}")
    print(f"  private_key_id : {str(sa['private_key_id'])[:8]}…")
    print(f"  private_key    : {len(sa['private_key'])} ký tự, "
          f"{sa['private_key'].count(chr(10))} dòng")
    print()
    print("Tiếp theo:")
    print(f"  1. Mở {BAN_DAN.relative_to(GOC)}, chép toàn bộ")
    print("  2. Dán THÊM vào Streamlit Cloud > Settings > Secrets")
    print("  3. Xoá key CŨ trong Google Cloud Console nếu chưa xoá")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
