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


def test_CUA_THOAT_trong_NHAY_NGUOC_la_MO_TA_chu_khong_phai_DUNG(tmp_path):
    """Lần thứ BA công cụ tố chính nó, và cùng một họ với hai lần trước.

    Dòng 96 của bảng lỗi — dòng ghi lại chính lỗi này — **mô tả** cú pháp
    cửa thoát trong dấu nháy ngược. Bản trước đọc đoạn mô tả ấy thành một
    cửa thoát đang **dùng**, và xếp một đường chết thành "sử liệu". Kết
    quả tình cờ đúng, **lý do thì sai** — nên sai ở mọi ca khác.

    Cùng hình dạng `SKILL.md` Bước 4: *"KHÔNG viết tên file trần ra đây
    làm ví dụ"*.
    """
    goc = _cay(tmp_path,
               "cach khai: `<!-- duong-da-chet: ly do -->` ke ben "
               "`~/mat/mo-ta.md`\n"
               "that su khai: `~/mat/that.md` "
               "<!-- duong-da-chet: co that -->\n")
    ket = K.phan_loai(K.thu_thap(goc), _nha(tmp_path, "con/song.md"))
    assert {d for _, _, d in ket["chet"]} == {"~/mat/mo-ta.md"}
    assert {d for _, _, d in ket["su_lieu"]} == {"~/mat/that.md"}


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


def test_BAN_LUU_la_SU_LIEU_theo_TEN_FILE_chu_khong_theo_CHU_tren_dong(tmp_path):
    """Lỗi 118 (lượt soát 8, 01/10/2026): BƯỚC 145 thêm hai bản lưu vào
    `TAI_LIEU` dùng chung, nên công cụ này đọc cả chúng — và bản lưu KHÔNG
    được sửa, tức không mang nổi cửa thoát. Ba lần nêu `~/.claude/CLAUDE.md`
    trong bản lưu thành ba con trỏ chết không bao giờ gỡ được.

    Phán theo TÊN FILE: một dòng ở tài liệu SỐNG nhắc chữ `docs/lich-su/`
    vẫn phải ra chết.
    """
    ban_luu = "docs/lich-su/CLAUDE-md-2026-09-30.md"
    assert ban_luu in K.TAI_LIEU and ban_luu.startswith(K.BAN_LUU)
    goc = _cay(tmp_path, "> đích `~/mat/a.md` bị ghi.\n", ten=ban_luu)
    # tài liệu SỐNG cũng nằm dưới `docs/` — bắt phép so tiền tố quá rộng
    _cay(tmp_path, "| `~/mat/a.md` | bản cũ ở `docs/lich-su/` |\n",
         ten="docs/HANDOFF.md")
    ket = K.phan_loai(K.thu_thap(goc), _nha(tmp_path, "con/song.md"))
    assert ket["su_lieu"] == [(ban_luu, 1, "~/mat/a.md")]
    assert ket["chet"] == [("docs/HANDOFF.md", 1, "~/mat/a.md")]


def test_BAN_LUU_THAT_khong_bao_gio_ra_CHET(tmp_path):
    """Trên repo THẬT, nhà RỖNG (mọi đường đều vắng): không bản ghi nào của
    bản lưu được rơi vào `chet`. Đối chứng dương: bản lưu PHẢI có đường để
    xét, kẻo phép thử xanh vì quần thể rỗng.
    """
    ket = K.phan_loai(K.thu_thap(GOC), _nha(tmp_path))
    cua_ban_luu = [r for o in ket.values() for r in o
                   if r[0].startswith(K.BAN_LUU)]
    assert cua_ban_luu, "ban luu khong con duong ~/ nao - phep thu rong"
    assert not [r for r in ket["chet"] if r[0].startswith(K.BAN_LUU)]


# Đường BIẾT CHẾT từ BƯỚC 139 (file chỉ chứa khối vnai, người dùng gỡ) và
# BƯỚC 151 (đích ghi của vnai). Danh sách tay, có chủ ý: CI không đọc được
# thư mục nhà của máy khác (lỗi 14), nhưng đọc được LỜI KHAI của chính dự
# án về đường nào đã chết (lỗi 121).
DA_BIET_CHET = ("~/.claude/CLAUDE.md", "~/.claude/rules/ecc/", "~/AGENTS.md")


def test_DUONG_DA_BIET_CHET_o_tai_lieu_song_deu_mang_CUA_THOAT(tmp_path):
    """Lỗi 121: BƯỚC 151 chạy lệnh thứ hai (`sau luot: 0 chet`) RỒI mới thêm
    hai dòng bảng lỗi nhắc `~/.claude/CLAUDE.md` — hai con trỏ chết chui
    vào SAU phép đo, và mã thoát thật là 1 suốt ba ngày tới lượt 9. Gác này
    dựng một thư mục nhà chứa MỌI đường tài liệu nêu, TRỪ ba đường đã khai
    chết; khi đó bản ghi nào còn ở rổ `chet` là một lần nêu đường chết mà
    không kèm cửa thoát — bất kể ai thêm nó sau khi đo.
    """
    ban_ghi = K.thu_thap(GOC)
    tat_ca = {b[2] for b in ban_ghi}
    nha = tmp_path / "nha"
    nha.mkdir()
    for d in sorted(tat_ca - set(DA_BIET_CHET)):
        p = nha / d[2:]
        if any(o != d and o.startswith(d.rstrip("/") + "/") for o in tat_ca):
            p.mkdir(parents=True, exist_ok=True)
        elif not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x", encoding="utf-8")
    ket = K.phan_loai(ban_ghi, nha)
    # đối chứng dương: mọi đường trong danh sách PHẢI còn được nêu ở tài liệu
    # sống VÀ đã khai lý do — kẻo gác xanh vì danh sách trỏ vào hư không.
    # (Không đòi chiều ngược: một cửa thoát phủ cả dòng, nên đường còn sống
    # nằm cùng dòng cũng hiện ở `su_lieu`.)
    trong = K.phan_loai(ban_ghi, tmp_path / "nha_trong")  # không đường nào còn
    da_khai = {r[2] for r in trong["su_lieu"] if not r[0].startswith(K.BAN_LUU)}
    assert set(DA_BIET_CHET) <= da_khai, (
        "mot duong trong DA_BIET_CHET khong con o tai lieu song nao - go no "
        f"khoi danh sach: {sorted(set(DA_BIET_CHET) - da_khai)}")
    assert not ket["chet"], (
        "duong DA BIET CHET duoc nhac ma khong co cua thoat: "
        f"{ket['chet']}")


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
