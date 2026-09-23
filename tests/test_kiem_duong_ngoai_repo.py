"""Gác cho `tools/kiem_duong_ngoai_repo.py` — máy đo con trỏ ngoài repo.

Máy đo nguy hiểm hơn gác: một gác sai thì ĐỎ, một máy đo sai thì chỉ **in
ra một con số** (`SKILL.md` Bước 3, điều 4). File này đục vào đúng chỗ nó
phán, không đục vào hàm trích.

Phát đầu tiên dựng lại **nguyên văn lỗi thật của chính nó**: bản đầu đoán
cái dấu và xếp SAI cả 2/2 ca không-tồn-tại. Xem
`test_DAU_tren_dong_KHONG_bien_mot_duong_CHET_thanh_SU_LIEU`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import kiem_duong_ngoai_repo as K  # noqa: E402
import soat_loi_khai_cu as S  # noqa: E402


def _cay(tmp_path: Path, noi_dung: str, ten: str = "CLAUDE.md") -> Path:
    (tmp_path / ten).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ten).write_text(noi_dung, encoding="utf-8")
    return tmp_path


def _nha(tmp_path: Path, *co: str) -> Path:
    nha = tmp_path / "nha"
    for c in co:
        p = nha / c
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    nha.mkdir(exist_ok=True)
    return nha


# ── phát đầu: dựng lại nguyên văn lỗi thật ───────────────────────────

def test_DAU_tren_dong_KHONG_bien_mot_duong_CHET_thanh_SU_LIEU(tmp_path):
    """Bản đầu nhận mọi `⚠️ 🔴 ~~ "đã xoá"` ở BẤT KỲ đâu trên dòng.

    Đo 23/09/2026: cả 2/2 ca nó xếp "sử liệu" đều xếp SAI, và cả hai
    trượt về phía IM LẶNG.

    - `loi-da-mac.md:45` — ⚠️ ở đó là GIÁ TRỊ một ô bảng, nói về việc
      "máy chặn được chưa", không nói gì về đường dẫn.
    - `CLAUDE.md:87` — chữ "bị xoá" nói về SÁU FILE KHÁC; chính đường
      dẫn đang xét được khai là "bị cắt", tức CÒN SỐNG.

    Hai dòng dưới đây là hai ca ấy, rút gọn. Cả hai phải ra **chết**.
    """
    goc = _cay(tmp_path,
               "| 14 | cua chua chay | phep thu | ⚠️ mot phan "
               "| `~/da/mat.md` |\n"
               "> sáu file bị xoá hẳn, `~/cung/mat.md` bị cắt 5.227 ký tự.\n")
    ket = K.phan_loai(K.thu_thap(goc), _nha(tmp_path, "con/song.md"))
    chet = {d for _, _, d in ket["chet"]}
    assert chet == {"~/da/mat.md", "~/cung/mat.md"}, (
        "mot dau o dau do tren dong KHONG phai loi khai ve duong dan nay")
    assert ket["su_lieu"] == []


def test_CUA_THOAT_RONG_khong_duoc_nhan(tmp_path):
    """`# bia-ok:` rỗng bị từ chối; cửa thoát ở đây theo đúng luật ấy.

    Mục đích không phải cấm giữ, mà buộc NÓI RA vì sao cái tên này được
    phép trỏ vào hư không.
    """
    goc = _cay(tmp_path,
               "a `~/mat/mot.md` <!-- duong-da-chet: -->\n"
               "b `~/mat/hai.md` <!-- duong-da-chet:    -->\n"
               "c `~/mat/ba.md` <!-- duong-da-chet: do X -->\n")
    ket = K.phan_loai(K.thu_thap(goc), _nha(tmp_path, "con/song.md"))
    assert {d for _, _, d in ket["chet"]} == {"~/mat/mot.md", "~/mat/hai.md"}
    assert {d for _, _, d in ket["su_lieu"]} == {"~/mat/ba.md"}


# ── đối chứng dương: phân biệt "tài liệu sai" với "phép đo sai" ──────

def test_KHONG_DUONG_NAO_TON_TAI_thi_CHUA_KIEM_DUOC_chu_khong_phai_tat_ca_CHET():
    """Sai thư mục nhà thì MỌI đường đều "mất" — và đó là lỗi của PHÉP ĐO.

    Không có vế này, một lượt chạy trên CI Linux sẽ in ra "36 con trỏ
    chết" và nghe hoàn toàn hợp lý. Lỗi 61.
    """
    assert K.phan_dinh({"co": [], "su_lieu": [], "chet": [("a", 1, "~/x")]}) == 2
    assert K.phan_dinh({"co": [], "su_lieu": [("a", 1, "~/x")], "chet": []}) == 2


def test_QUAN_THE_RONG_thi_CHUA_KIEM_DUOC():
    assert K.phan_dinh({"co": [], "su_lieu": [], "chet": []}) == 2


def test_CO_duong_ton_tai_thi_phan_dinh_doc_dung_hai_o_con_lai():
    co = [("a", 1, "~/co")]
    assert K.phan_dinh({"co": co, "su_lieu": [], "chet": []}) == 0
    assert K.phan_dinh({"co": co, "su_lieu": [("b", 2, "~/s")],
                        "chet": []}) == 0
    assert K.phan_dinh({"co": co, "su_lieu": [],
                        "chet": [("c", 3, "~/c")]}) == 1


# ── cách nó ĐẾM, và cách nó cắt chuỗi ───────────────────────────────

def test_HAI_DUONG_TREN_MOT_DONG_dem_HAI_LAN(tmp_path):
    """Đếm theo LẦN NÊU, không theo dòng — `CLAUDE.md:780` nêu ba đường."""
    goc = _cay(tmp_path, "`~/a.md` và `~/b.md` và `~/c.md`\n")
    ban_ghi = K.thu_thap(goc)
    assert len(ban_ghi) == 3
    assert {b[1] for b in ban_ghi} == {1}


def test_DAU_CAU_cuoi_cau_bi_cat_nhung_GACH_CHEO_thi_GIU(tmp_path):
    """`~/.claude/projects/` là THƯ MỤC — cắt `/` là hỏi sai câu hỏi."""
    goc = _cay(tmp_path, "x ~/mot/thu-muc/ và ~/mot/file.md.\n")
    assert {b[2] for b in K.thu_thap(goc)} == {"~/mot/thu-muc/",
                                              "~/mot/file.md"}


def test_NHAY_NGUOC_va_DAU_CACH_dung_duoc_duong(tmp_path):
    """Lớp ký tự phải dừng ở biên đoạn mã inline, không nuốt chữ sau."""
    goc = _cay(tmp_path, "nap vao `~/.claude/settings.json` bang duong dan\n")
    assert [b[2] for b in K.thu_thap(goc)] == ["~/.claude/settings.json"]


# ── quần thể, và quyết định KHÔNG đưa vào CI ────────────────────────

def test_QUAN_THE_dung_chung_chu_KHONG_go_lai(tmp_path):
    """Hai công cụ soi cùng bảy tài liệu. Gõ lại là để chúng trôi khỏi nhau.

    "Suy ra, đừng gõ" — `SKILL.md` Bước 2.
    """
    assert K.TAI_LIEU is S.TAI_LIEU


def test_CONG_CU_NAY_CO_Y_KHONG_nam_trong_CI():
    """Một cổng luôn đỏ là một cổng bị tắt, và gác bị tắt thì bằng không.

    Quyết định này KHÔNG phải của hôm nay — bảng lỗi dòng 14 đã ghi:
    *"cố ý KHÔNG dựng test canh file rules toàn cục: nó nằm ngoài repo,
    ở đường dẫn Windows, nên một test như thế sẽ đỏ trên CI Linux"*.

    Gác ở đây để lần sau ai đó muốn "cho chắc" thì phải bác lời khai
    trên trước, chứ không lặng lẽ thêm một dòng vào workflow.
    Tiền lệ cùng hạng: `tools/kiem_cua_song.py`, cũng 0 workflow.
    """
    ten = "kiem_duong_ngoai_repo"
    co = [p.name for p in (GOC / ".github" / "workflows").glob("*.yml")
          if ten in p.read_text(encoding="utf-8")]
    assert co == [], (
        f"{ten} xuat hien trong {co}. No doc THU MUC NHA cua may nay; "
        "runner CI khong co cac duong ay nen no se do moi luot.")


def test_kiem_cua_song_van_la_TIEN_LE_chu_khong_phai_loi_khai_suong():
    """Lời khai "tiền lệ" ở trên phải ĐO LẠI, không được chép.

    `SKILL.md` Bước 1 điều 2: một câu chép từ ghi chú thì phải đo lại.
    """
    co = [p.name for p in (GOC / ".github" / "workflows").glob("*.yml")
          if "kiem_cua_song" in p.read_text(encoding="utf-8")]
    assert co == []


# ── chạy thật, không chỉ gọi hàm ────────────────────────────────────

@pytest.mark.parametrize("co_them", [[], ["--nha", "."]])
def test_CHAY_THAT_ra_ma_thoat_doc_duoc(co_them):
    """Một công cụ không chạy được cũng là một cổng xanh giả."""
    kq = subprocess.run(
        [sys.executable, str(GOC / "tools" / "kiem_duong_ngoai_repo.py"),
         *co_them],
        capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    assert kq.returncode in (0, 1, 2)
    assert "ĐƯỜNG DẪN NGOÀI REPO" in kq.stdout or "CHƯA KIỂM ĐƯỢC" in kq.stdout


def test_BAO_CAO_in_DU_LIEU_THO_chu_khong_nen_thanh_mot_con_so(tmp_path):
    """Lỗi 78: một cảnh báo không ai đọc là một cảnh báo không tồn tại.

    Báo cáo phải gọi tên từng file và từng số dòng, để người đọc kiểm
    được phán quyết bằng chính dữ liệu bên cạnh nó.
    """
    ket = {"co": [("CLAUDE.md", 5, "~/co.md")],
           "su_lieu": [],
           "chet": [("docs/HANDOFF.md", 42, "~/mat.md")]}
    ra = K.bao_cao(ket, K.phan_dinh(ket))
    assert "docs/HANDOFF.md:42" in ra
    assert "~/mat.md" in ra
    assert "CLAUDE.md:5" in ra


def test_BAO_CAO_khi_CHUA_KIEM_DUOC_khong_duoc_doc_thanh_tai_lieu_sai():
    ket = {"co": [], "su_lieu": [], "chet": [("a", 1, "~/x")]}
    ra = K.bao_cao(ket, K.phan_dinh(ket))
    assert "CHƯA KIỂM ĐƯỢC" in ra
    assert "phép đo" in ra
