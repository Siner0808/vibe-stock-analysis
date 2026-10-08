"""Máy phán "BƯỚC này có đổi LUẬT không" bằng LỊCH SỬ GIT — BƯỚC 164 (giai đoạn A3).

Người dùng "Đồng ý" ngày 08/10/2026 thu hẹp Quy tắc 3: chỉ BƯỚC đổi luật hoặc
kết luận đo phải hỏi sổ tay thật. Nếu vế "có đổi luật không" là lời khai thì nó
thành ô thoát mới (lỗi 86), nên `tools/buoc_cham_luat.py` đọc thứ không nằm trong
tay người khai: danh sách file mà PR đưa BƯỚC vào đã đổi.

Mọi ca dựng trên repo git tạm (`tmp_path`) — gồm đủ ba hình dạng PR (commit
gộp một cục, `--no-ff` nhiều commit, nhánh chưa gộp), vì một máy đo git chỉ thử
trên MỘT hình dạng thì xanh trên bản hỏng ở hai hình dạng kia. Ba ca cuối chạy
trên lịch sử THẬT (ca BƯỚC 162/163 đã nằm trong `main`); chúng đỏ ở repo nông
(CI đặt `fetch-depth: 0`), chủ ý.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import buoc_cham_luat as b  # noqa: E402

STATE = "docs/STATE.md"


# ── repo tạm ─────────────────────────────────────────────────────────────

def _git(repo, *args) -> str:
    env = dict(os.environ)
    env.pop("GIT_DIR", None)
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false",
                        *args], cwd=str(repo), env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"git {' '.join(args)} loi: {r.stderr}"
    return r.stdout


def _ghi(repo, ten: str, noi_dung: str, them: bool = False) -> None:
    p = repo / ten
    p.parent.mkdir(parents=True, exist_ok=True)
    if them and p.exists():
        noi_dung = p.read_text(encoding="utf-8") + noi_dung
    p.write_text(noi_dung, encoding="utf-8", newline="\n")


def _cam(repo, thong_diep="x") -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", thong_diep)
    return _git(repo, "rev-parse", "HEAD").strip()


def _tieu_de(n: int, rest: str = "mot buoc") -> str:
    return f"## BƯỚC {n} — {rest}\nnoi dung\n"


@pytest.fixture
def kho(tmp_path):
    repo = tmp_path / "kho"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _ghi(repo, STATE, "# So\n" + _tieu_de(163, "truoc moc"))
    _ghi(repo, "CLAUDE.md", "luat 1\n")
    _ghi(repo, "docs/x.md", "x\n")
    _cam(repo, "goc")                   # commit goc = neo (xem `_neo`)
    return repo


def _neo(repo) -> str:
    """Neo lịch sử của repo tạm: commit gốc duy nhất. Mọi BƯỚC thêm sau nó."""
    return _git(repo, "rev-list", "--max-parents=0", "HEAD").strip()


# ── hình dạng 1: commit gộp một cục (squash) ──────────────────────────────

def test_SQUASH_commit_dua_BUOC_vao_cung_voi_CLAUDE_md_thi_CHAM(kho):
    _ghi(kho, STATE, _tieu_de(164), them=True)
    _ghi(kho, "CLAUDE.md", "luat 1\nluat 2\n")
    _cam(kho)
    cham, files, nguon = b.buoc_cham_luat(kho, 164, neo=_neo(kho))
    assert cham and files == ["CLAUDE.md"], (files, nguon)
    assert "da vao" in nguon


def test_SQUASH_commit_chi_sua_tai_lieu_thuong_thi_KHONG_cham(kho):
    _ghi(kho, STATE, _tieu_de(164), them=True)
    _ghi(kho, "docs/x.md", "x\ny\n")
    _ghi(kho, "tools/moi.py", "pass\n")
    _cam(kho)
    cham, files, _ = b.buoc_cham_luat(kho, 164, neo=_neo(kho))
    assert not cham and files == [], files
    assert set(b.file_cua_buoc(kho, 164, neo=_neo(kho))[0]) == {
        STATE, "docs/x.md", "tools/moi.py"}


# ── hình dạng 2: `--no-ff` nhiều commit (PR gộp kiểu merge) ───────────────

def test_NO_FF_luat_sua_o_commit_TRUOC_tieu_de_o_commit_SAU_van_CHAM(kho):
    """Ca khiến một máy chỉ nhìn commit chứa tiêu đề mù: CLAUDE.md đổi ở commit
    đầu của nhánh, tiêu đề BƯỚC vào ở commit cuối, hai commit khác nhau."""
    _git(kho, "checkout", "-q", "-b", "pr")
    _ghi(kho, "CLAUDE.md", "luat 1\nluat doi\n")
    _cam(kho, "sua luat")
    _ghi(kho, STATE, _tieu_de(164), them=True)
    _cam(kho, "ghi BUOC")
    _git(kho, "checkout", "-q", "main")
    _git(kho, "merge", "-q", "--no-ff", "-m", "gop pr", "pr")
    cham, files, nguon = b.buoc_cham_luat(kho, 164, neo=_neo(kho))
    assert cham and "CLAUDE.md" in files, (files, nguon)
    # va commit ma may chon la commit GOP, khong phai commit chua tieu de
    assert b.commit_dua_buoc_vao(kho, 164, neo=_neo(kho)) == \
        _git(kho, "rev-parse", "HEAD").strip()


# ── hình dạng 3: nhánh chưa gộp, và cây làm việc ──────────────────────────

def test_NHANH_CHUA_GOP_tinh_ca_commit_nhanh_va_sua_chua_commit(kho):
    _git(kho, "checkout", "-q", "-b", "pr")
    _ghi(kho, "docs/TIEU-CHI-DOC-TRUOC.md", "## ĐO 1 — x\n")
    _cam(kho, "them DO")
    _ghi(kho, STATE, _tieu_de(164), them=True)          # CHUA commit
    cham, files, nguon = b.buoc_cham_luat(kho, 164, neo=_neo(kho))
    assert cham and files == ["docs/TIEU-CHI-DOC-TRUOC.md"], (files, nguon)
    assert "CHUA vao" in nguon


def test_FILE_CHUA_THEO_DOI_cung_tinh(kho):
    _git(kho, "checkout", "-q", "-b", "pr")
    _ghi(kho, STATE, _tieu_de(164), them=True)
    _cam(kho)
    _ghi(kho, "docs/LO-TRINH.md", "moi tinh\n")          # untracked
    cham, files, _ = b.buoc_cham_luat(kho, 164, neo=_neo(kho))
    assert cham and files == ["docs/LO-TRINH.md"], files


def test_DIEM_TACH_khong_phai_dau_nhanh_goc__sua_luat_cua_main_khong_tinh_cho_PR(kho):
    """`main` tiến lên và đổi CLAUDE.md SAU khi PR tách ra. Cây PR vì thế lệch
    CLAUDE.md so với đầu `main`, nhưng đó không phải việc của PR."""
    _git(kho, "checkout", "-q", "-b", "pr")
    _ghi(kho, STATE, _tieu_de(164), them=True)
    _ghi(kho, "docs/x.md", "x\npr\n")
    _cam(kho, "pr")
    _git(kho, "checkout", "-q", "main")
    _ghi(kho, "CLAUDE.md", "luat 1\nluat cua main\n")
    _cam(kho, "main doi luat")
    _git(kho, "checkout", "-q", "pr")
    cham, files, _ = b.buoc_cham_luat(kho, 164, neo=_neo(kho))
    assert not cham and "CLAUDE.md" not in files, files


# ── tìm tiêu đề ───────────────────────────────────────────────────────────

def test_BUOC_16_khong_khop_BUOC_164_va_tieu_de_cap_ba_khong_tinh(kho):
    _ghi(kho, STATE, _tieu_de(16, "ngan"), them=True)
    _ghi(kho, "CLAUDE.md", "luat 1\nluat boi BUOC 16\n")
    c16 = _cam(kho, "BUOC 16")
    _ghi(kho, STATE, "### BƯỚC 164 — cap ba, khong phai muc\n", them=True)
    _cam(kho, "cap ba")
    assert b.commit_dua_buoc_vao(kho, 164, neo=_neo(kho)) is None
    _ghi(kho, STATE, _tieu_de(164, "that"), them=True)
    _ghi(kho, "docs/x.md", "x\n164\n")
    c164 = _cam(kho, "BUOC 164")
    assert b.commit_dua_buoc_vao(kho, 164, neo=_neo(kho)) == c164
    assert b.commit_dua_buoc_vao(kho, 16, neo=_neo(kho)) == c16
    assert not b.buoc_cham_luat(kho, 164, neo=_neo(kho))[0]
    assert b.buoc_cham_luat(kho, 16, neo=_neo(kho))[0]


def test_BUOC_16_khong_khop_BUOC_164_khi_164_vao_TRUOC_va_16_chua_co(kho):
    """Phát đục P3 (BƯỚC 164, lô A): bỏ dấu cách cuối mẫu `-G^## BƯỚC {n} ` sống sót ở
    ca trên vì ở đó BƯỚC 16 vào TRƯỚC 164 — lấy commit CŨ NHẤT thì vô tình ra đúng.
    Hai ca dưới đảo thứ tự: 164 vào trước, hỏi về 16 (chưa có, hoặc vào sau) thì
    mẫu cụt `BƯỚC 16` sẽ trả commit của 164. Với mẫu đúng: None / commit của 16."""
    _ghi(kho, STATE, _tieu_de(164, "vao truoc"), them=True)
    _ghi(kho, "CLAUDE.md", "luat 1\nluat boi BUOC 164\n")
    c164 = _cam(kho, "BUOC 164")
    assert b.commit_dua_buoc_vao(kho, 16, neo=_neo(kho)) is None
    assert b.commit_dua_buoc_vao(kho, 164, neo=_neo(kho)) == c164
    _ghi(kho, STATE, _tieu_de(16, "vao sau"), them=True)
    c16 = _cam(kho, "BUOC 16")
    assert b.commit_dua_buoc_vao(kho, 16, neo=_neo(kho)) == c16
    assert not b.buoc_cham_luat(kho, 16, neo=_neo(kho))[0]
    assert b.buoc_cham_luat(kho, 164, neo=_neo(kho))[0]


def test_COMMIT_CU_NHAT_la_commit_dua_BUOC_vao__sua_tieu_de_ve_sau_khong_dich_no(kho):
    _ghi(kho, STATE, _tieu_de(164, "ban dau"), them=True)
    _ghi(kho, "CLAUDE.md", "luat 1\nluat doi\n")
    c_dau = _cam(kho, "dua vao")
    p = kho / STATE
    p.write_text(p.read_text(encoding="utf-8").replace("ban dau", "sua tieu de"),
                 encoding="utf-8", newline="\n")
    _cam(kho, "sua tieu de")
    assert b.commit_dua_buoc_vao(kho, 164, neo=_neo(kho)) == c_dau
    assert b.buoc_cham_luat(kho, 164, neo=_neo(kho))[0]


def test_LUAT_sua_SAU_khi_BUOC_da_vao_main_khong_tinh_nguoc_cho_BUOC(kho):
    _ghi(kho, STATE, _tieu_de(164), them=True)
    _cam(kho, "BUOC 164")
    _ghi(kho, "CLAUDE.md", "luat 1\nluat doi o BUOC sau\n")
    _cam(kho, "BUOC 165 sua luat")
    assert not b.buoc_cham_luat(kho, 164, neo=_neo(kho))[0]


def test_BUOC_nam_ngay_o_COMMIT_GOC_khong_cha_van_doc_duoc(tmp_path):
    repo = tmp_path / "goc"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _ghi(repo, STATE, "# So\n" + _tieu_de(1))
    _ghi(repo, "CLAUDE.md", "luat\n")
    _cam(repo, "goc")
    cham, files, nguon = b.buoc_cham_luat(repo, 1)
    assert cham and "da vao" in nguon, (files, nguon)
    assert set(b.file_cua_buoc(repo, 1)[0]) == {STATE, "CLAUDE.md"}


# ── chỗ máy phải NỔ, không xanh im ────────────────────────────────────────

def test_REPO_NONG_thi_NO(kho, tmp_path):
    _ghi(kho, STATE, _tieu_de(164), them=True)
    _cam(kho)
    nong = tmp_path / "nong"
    _git(tmp_path, "clone", "-q", "--depth", "1", kho.resolve().as_uri(), str(nong))
    with pytest.raises(b.LoiLichSu, match="NONG"):
        b.file_cua_buoc(nong, 164)


def test_KHONG_co_nhanh_goc_thi_NO(kho):
    _git(kho, "branch", "-q", "-m", "main", "thanh-lam-nhanh-chinh")
    with pytest.raises(b.LoiLichSu, match="nhanh goc"):
        b.file_cua_buoc(kho, 164)


def test_NEO_khong_phai_to_tien_cua_HEAD_thi_NO(kho):
    _git(kho, "checkout", "-q", "-b", "la")
    _ghi(kho, "docs/x.md", "la\n")
    la = _cam(kho)
    _git(kho, "checkout", "-q", "main")
    with pytest.raises(b.LoiLichSu, match="neo"):
        b.commit_dua_buoc_vao(kho, 164, neo=la)


# ── phép phán thuần ───────────────────────────────────────────────────────

@pytest.mark.parametrize("ly_do", ["khong can", "không cần", "khong quan trong",
                                   "n/a", "-", "sau", "Khong Can"])
def test_LY_DO_mo_ho_ngan_deu_bi_chan_boi_DO_DAI_nen_khong_can_danh_sach_rieng(ly_do):
    """Phát đục P14 (BƯỚC 164, lô A): phép kiểm `ly.lower() in LY_DO_MO_HO` sống sót vì
    mọi phần tử của nó đều < `LY_DO_TOI_THIEU` ký tự — phép kiểm độ dài đã bắt hết
    trước khi nó được hỏi. Đó là mã CHẾT, nên đã gỡ cả danh sách chứ không thêm ca
    giả. Ca này khoá lý do gỡ: mọi câu thần chú ngắn vẫn bị chặn, bằng độ dài."""
    loi = b.loi_khong_bat_buoc("BƯỚC 170", {"khong_bat_buoc_vi": ly_do}, [])
    assert loi and "qua ngan" in loi[0], (ly_do, loi)
    assert not hasattr(b, "LY_DO_MO_HO"), "danh sach chet duoc them lai"


def test_LY_DO_dung_NGUONG_25_ky_tu_la_hop_le():
    """Biên của phép kiểm độ dài (`<` chứ không `<=`): 24 ký tự đỏ, 25 ký tự xanh."""
    assert b.loi_khong_bat_buoc("BƯỚC 170", {"khong_bat_buoc_vi": "x" * 24}, [])
    assert b.loi_khong_bat_buoc("BƯỚC 170", {"khong_bat_buoc_vi": "x" * 25}, []) == []
    # khoang trang hai dau khong duoc cong vao do dai
    assert b.loi_khong_bat_buoc("BƯỚC 170",
                                {"khong_bat_buoc_vi": "  " + "x" * 24 + "  "}, [])


def test_FILE_LUAT_la_dung_sau_file_nguoi_dung_duyet_va_deu_ton_tai():
    assert b.FILE_LUAT == (
        "CLAUDE.md", "NGUYEN-TAC-DO-LUONG.md", "MO-XE-KIEN-TRUC.md",
        ".claude/skills/quy-trinh-lam-viec/SKILL.md",
        "docs/TIEU-CHI-DOC-TRUOC.md", "docs/LO-TRINH.md")
    thieu = [f for f in b.FILE_LUAT if not (GOC / f).is_file()]
    assert not thieu, (
        f"file luat khong ton tai: {thieu} — doi ten/xoa mot file luat se lang "
        f"le go no khoi danh sach canh; sua FILE_LUAT CO CHU DICH")


def test_file_luat_bi_cham_khop_DUNG_DUONG_DAN_khong_khop_chuoi_con():
    assert b.file_luat_bi_cham(["CLAUDE.md", "docs/STATE.md"]) == ["CLAUDE.md"]
    assert b.file_luat_bi_cham(["docs/CLAUDE.md", "tests/CLAUDE.md.bak",
                                "CLAUDE.md.old", "tools/LO-TRINH.md"]) == []
    assert b.file_luat_bi_cham([]) == []


def test_so_buoc_doc_dung_ten_muc_so():
    assert b.so_buoc("BƯỚC 164") == 164
    assert b.so_buoc("BƯỚC 70-73") == 70
    assert b.so_buoc("ĐO 5") is None and b.so_buoc("BƯỚC") is None
    assert b.so_buoc("BƯỚC 16x") is None


def test_bang_doi_chieu_xep_dung_bon_o_va_bo_BUOC_chua_hoi():
    so = {"BƯỚC 1": {"cau_hoi": "c", "phat_hien": [{"phan_quyet": "THẬT. ok"}]},
          "BƯỚC 2": {"cau_hoi": "c", "phat_hien": [{"phan_quyet": "SAI. x"}]},
          "BƯỚC 3": {"cau_hoi": "c", "phat_hien": [], "khong_tim_thay_gi": True},
          "BƯỚC 4": {"cau_hoi": "c", "phat_hien": [{"phan_quyet": "thật. thuong"}]},
          "BƯỚC 5": {"khong_bat_buoc_vi": "ly do"}}
    kq = b.bang_doi_chieu({1: True, 2: True, 3: False, 4: False, 5: False, 9: True}, so)
    assert kq == {"cham_that": [1], "cham_khong_that": [2],
                  "khong_cham_that": [4], "khong_cham_khong_that": [3]}, kq


# ── lịch sử THẬT ──────────────────────────────────────────────────────────

def test_LICH_SU_THAT_BUOC_162_chinh_CLAUDE_md_nen_CHAM_luat():
    """PR #208 (hợp nhất bằng `--merge`) sửa MỘT câu luật trong CLAUDE.md — ghi ở
    `docs/STATE.md` BƯỚC 162 (*"`CLAUDE.md` đổi MỘT câu (nó là một LUẬT)"*). Máy
    đọc git phải thấy điều người viết tự khai."""
    cham, files, nguon = b.buoc_cham_luat(GOC, 162, neo="13c32a0")
    assert cham and "CLAUDE.md" in files, (files, nguon)
    assert "da vao" in nguon


def test_LICH_SU_THAT_BUOC_163_chi_soat_tai_lieu_nen_KHONG_cham_luat():
    """PR #209: lượt soát định kỳ 11 — sửa HANDOFF, sổ, tool; không file luật nào."""
    cham, files, nguon = b.buoc_cham_luat(GOC, 163, neo="0334323")
    assert not cham and files == [], (files, nguon)
    assert "docs/STATE.md" in b.file_cua_buoc(GOC, 163, neo="0334323")[0]


def test_BUOC_164_that_cham_file_luat():
    """BƯỚC 164 đổi chính Quy tắc 3 (SKILL.md, CLAUDE.md) và thêm LO-TRINH.md."""
    cham, files, nguon = b.buoc_cham_luat(GOC, 164, neo=b.NEO_LICH_SU)
    assert cham, (files, nguon)
    assert {"docs/LO-TRINH.md", ".claude/skills/quy-trinh-lam-viec/SKILL.md",
            "CLAUDE.md"} <= set(files), files
