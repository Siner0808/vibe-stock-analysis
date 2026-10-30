"""Gác của BẮT TAY SHA-256 và ĐO ĐỘ TƯƠI BẰNG NHÃN trong `tools/so_tay.py` (BƯỚC 246).

Hai việc cũ được thay bằng máy:
  * chép câu trả lời của sổ tay sang tệp bằng tay -> ký tự vô hình rơi mất không ai biết
    (30/10/2026: `\\t\\u200b` trong công thức toán). Nay trang băm `innerText`, `kiem_tra_loi`
    băm tệp, lệch thì TỪ CHỐI và `ghi` không chạm sổ;
  * hỏi sổ tay "số BƯỚC lớn nhất trong nguồn" để đo độ tươi -> 29/10 nó trả lạc đề (trả lời
    lại câu hỏi cũ trong lịch sử chat). Nay nhãn nguồn `<tệp> @<băm>` được so với git.

Độ tươi được thử trên MỘT KHO GIT THẬT dựng trong `tmp_path` (không giả lệnh git), để
`git diff --quiet` / `rev-parse` / `show` chạy thật.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
import so_tay as st  # noqa: E402

TL = "Thoughts\nexpand_more\nKhông tìm thấy. x_t\t​ = 1 💡\n"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ── bắt tay ──────────────────────────────────────────────────────────────

def test_BAT_TAY_khop_tra_sha_va_do_dai_UTF16():
    kq = st.kiem_tra_loi(TL.encode("utf-8"), _sha(TL.encode("utf-8")).upper() + "\n")
    assert kq == {"sha256": _sha(TL.encode("utf-8")), "dai16": st._dai16(TL)}


def test_BAT_TAY_lech_mot_ky_tu_vo_hinh_la_TU_CHOI():
    """Chép tay rơi mất `\\u200b`: văn bản NHÌN y hệt, sha khác -> phải bị từ chối."""
    mat = TL.replace("​", "")
    with pytest.raises(st.TuChoi, match="BAT TAY LECH"):
        st.kiem_tra_loi(mat.encode("utf-8"), _sha(TL.encode("utf-8")))


def test_BAT_TAY_CRLF_la_lech_khong_duoc_tu_chuan_hoa():
    with pytest.raises(st.TuChoi, match="BAT TAY LECH"):
        st.kiem_tra_loi(TL.replace("\n", "\r\n").encode("utf-8"), _sha(TL.encode("utf-8")))


@pytest.mark.parametrize("sha", ["", "abc", "z" * 64, "a" * 63])
def test_BAT_TAY_sha_trang_sai_khuon_la_TU_CHOI(sha):
    with pytest.raises(st.TuChoi, match="64 ky tu hex"):
        st.kiem_tra_loi(TL.encode("utf-8"), sha)


def test_BAT_TAY_tep_khong_phai_UTF8_la_TU_CHOI():
    b = b"\xff\xfe\xfa"
    with pytest.raises(st.TuChoi, match="UTF-8"):
        st.kiem_tra_loi(b, _sha(b))


def test_TRICH_DAN_doc_dung_khuon_va_giu_ban_lap():
    van = "1: CLAUDE.md @a877ca6\n13: STATE.md @61221db phan1/5 (BUOC 2-40)\n\n13: STATE.md @61221db phan1/5 (BUOC 2-40)\n"
    assert st.doc_trich_dan(van) == [
        {"n": 1, "nguon": "CLAUDE.md @a877ca6"},
        {"n": 13, "nguon": "STATE.md @61221db phan1/5 (BUOC 2-40)"},
        {"n": 13, "nguon": "STATE.md @61221db phan1/5 (BUOC 2-40)"}]
    assert st.doc_trich_dan("") == []
    for xau in ("CLAUDE.md @a877ca6", "x: CLAUDE.md", "1:CLAUDE.md", "1: "):
        with pytest.raises(st.TuChoi, match="dong 1"):
            st.doc_trich_dan(xau)


def test_TRICH_DAN_nhan_ca_dang_JSON_cua_lenh_chup_va_tu_choi_JSON_sai_khuon():
    assert st.doc_trich_dan("[]") == st.doc_trich_dan("  [ ] ") == []
    assert st.doc_trich_dan('[{"n": 2, "nguon": " CLAUDE.md @a877ca6 "}]') == [{"n": 2, "nguon": "CLAUDE.md @a877ca6"}]
    for xau in ("[", '[{"n": 0, "nguon": "x"}]', '[{"n": true, "nguon": "x"}]', '[{"n": 1}]',
                '[{"n": 1, "nguon": ""}]', '[1]', '[{"n": 1, "nguon": "x", "them": 1}]'):
        with pytest.raises(st.TuChoi):
            st.doc_trich_dan(xau)


def _muc_tl(tmp_path, sha=None, **thay):
    (tmp_path / "tl.txt").write_bytes(TL.encode("utf-8"))
    (tmp_path / "td.txt").write_text("1: CLAUDE.md @a877ca6\n2: STATE.md @61221db phan1/5 (BUOC 2-40)\n",
                                     encoding="utf-8")
    cau = st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["a statement that y"])
    m = {"buoc": "BƯỚC 9999", "cau_hoi": cau,
         "phat_hien": [{"noi_dung": "CLAUDE.md: mot cau", "tu_kiem": "grep -n 'mot cau' CLAUDE.md -> dong 1",
                        "phan_quyet": "THẬT."}],
         "tra_loi_tep": str(tmp_path / "tl.txt"), "tra_loi_sha256": sha or _sha(TL.encode("utf-8")),
         "trich_dan_tep": str(tmp_path / "td.txt")}
    m.update(thay)
    return m


@pytest.fixture
def so_tam(tmp_path):
    p = tmp_path / "soat-notebooklm.json"
    d = json.loads((GOC / "docs" / "soat-notebooklm.json").read_text(encoding="utf-8"))
    d["soat"] = {k: v for k, v in d["soat"].items()
                 if not (isinstance(v, dict) and "khong_bat_buoc_vi" in v)}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def test_GHI_luu_sha256_do_dai_va_trich_dan_nhu_DU_LIEU(tmp_path, so_tam):
    dong = st.ghi(_muc_tl(tmp_path), so=so_tam, ngay="2026-10-30")
    assert dong["tra_loi"] == {"sha256": _sha(TL.encode("utf-8")), "dai16": st._dai16(TL),
                               "trich_dan": [{"n": 1, "nguon": "CLAUDE.md @a877ca6"},
                                             {"n": 2, "nguon": "STATE.md @61221db phan1/5 (BUOC 2-40)"}]}
    doc_lai = json.loads(so_tam.read_text(encoding="utf-8"))["soat"]["BƯỚC 9999"]
    assert doc_lai["tra_loi"] == dong["tra_loi"]
    assert "tra_loi_tep" not in doc_lai and "tra_loi_sha256" not in doc_lai   # đường dẫn tạm không vào sổ


def test_GHI_bat_tay_lech_thi_TU_CHOI_va_KHONG_cham_so(tmp_path, so_tam):
    truoc = so_tam.read_bytes()
    with pytest.raises(st.TuChoi, match="BAT TAY LECH"):
        st.ghi(_muc_tl(tmp_path, sha="0" * 64), so=so_tam, ngay="2026-10-30")
    assert so_tam.read_bytes() == truoc


@pytest.mark.parametrize("bo", ["tra_loi_tep", "tra_loi_sha256", "trich_dan_tep"])
def test_GHI_khai_thieu_mot_trong_ba_o_thi_TU_CHOI(tmp_path, so_tam, bo):
    truoc = so_tam.read_bytes()
    m = _muc_tl(tmp_path)
    del m[bo]
    with pytest.raises(st.TuChoi, match="ca ba o"):
        st.ghi(m, so=so_tam, ngay="2026-10-30")
    assert so_tam.read_bytes() == truoc


def test_GHI_tep_trich_dan_sai_khuon_hoac_vang_thi_TU_CHOI(tmp_path, so_tam):
    truoc = so_tam.read_bytes()
    m = _muc_tl(tmp_path)
    Path(m["trich_dan_tep"]).write_text("khong co so\n", encoding="utf-8")
    with pytest.raises(st.TuChoi, match="sai khuon"):
        st.ghi(m, so=so_tam, ngay="2026-10-30")
    with pytest.raises(st.TuChoi, match="khong doc duoc tep"):
        st.ghi(_muc_tl(tmp_path, trich_dan_tep=str(tmp_path / "vang.txt")), so=so_tam, ngay="2026-10-30")
    assert so_tam.read_bytes() == truoc


def test_GHI_khong_khai_o_nao_thi_muc_cu_van_hop_le_va_khong_co_tra_loi(tmp_path, so_tam):
    m = _muc_tl(tmp_path)
    for k in ("tra_loi_tep", "tra_loi_sha256", "trich_dan_tep"):
        del m[k]
    assert "tra_loi" not in st.ghi(m, so=so_tam, ngay="2026-10-30")


def test_CLI_kiem_tra_loi_ma_thoat_0_khop_1_lech_2_khong_doc_duoc(tmp_path):
    tep = tmp_path / "tl.txt"
    tep.write_bytes(TL.encode("utf-8"))

    def cli(*a):
        return subprocess.run([sys.executable, str(GOC / "tools" / "so_tay.py"), "kiem-tra-loi", *a],
                              capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    ok = cli(str(tep), "--sha256", _sha(TL.encode("utf-8")))
    assert ok.returncode == 0 and "KHOP" in ok.stdout, ok
    lech = cli(str(tep), "--sha256", "1" * 64)
    assert lech.returncode == 1 and "BAT TAY LECH" in lech.stderr
    vang = cli(str(tmp_path / "khong-co.txt"), "--sha256", "1" * 64)
    assert vang.returncode == 2 and "Traceback" not in vang.stderr


# ── độ tươi bằng nhãn: KHO GIT THẬT ─────────────────────────────────────────

def _chay_git(repo: Path, *a: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *a], capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, (a, r.stderr)
    return r.stdout.strip()


def _viet(repo: Path, rel: str, van: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(van.encode("utf-8"))


def _state(*so_buoc: int) -> str:
    return "".join(f"## BƯỚC {n}\n" + f"nội dung của bước {n} " * 6 + "\n\n" for n in so_buoc)


@pytest.fixture
def kho(tmp_path):
    """Hai commit. c1: CLAUDE.md, HANDOFF, SKILL, STATE(BƯỚC 1-3). c2: CLAUDE.md đổi, STATE thêm BƯỚC 4."""
    r = tmp_path / "kho"
    r.mkdir()
    _chay_git(r, "init", "-q")
    _viet(r, "CLAUDE.md", "luat v1\n")
    _viet(r, "docs/HANDOFF.md", "ban giao\n")
    _viet(r, ".claude/skills/quy-trinh-lam-viec/SKILL.md", "skill\n")
    _viet(r, "docs/STATE.md", _state(1, 2, 3))
    _chay_git(r, "add", "-A")
    _chay_git(r, "commit", "-q", "-m", "c1")
    c1 = _chay_git(r, "rev-parse", "--short=7", "HEAD")
    _viet(r, "CLAUDE.md", "luat v2\n")
    _viet(r, "docs/STATE.md", _state(1, 2, 3, 4))
    _chay_git(r, "add", "-A")
    _chay_git(r, "commit", "-q", "-m", "c2")
    c2 = _chay_git(r, "rev-parse", "--short=7", "HEAD")

    def git(*a):
        x = subprocess.run(["git", "-C", str(r), *a], capture_output=True)
        return x.returncode, x.stdout.decode("utf-8", errors="replace")
    return r, c1, c2, git


KY_VONG = ["CLAUDE.md", "HANDOFF.md", "SKILL.md"]


def _trang_thai(kq):
    return {d["nhan"]: d["trang_thai"] for d in kq["nguon"]}


def test_DO_TUOI_tep_khong_doi_la_TUOI_tep_doi_giua_hai_commit_la_CU(kho):
    _, c1, c2, git = kho
    kq = st.do_tuoi([f"CLAUDE.md @{c1}", f"HANDOFF.md @{c1}", f"SKILL.md @{c1}"], git=git, ky_vong=KY_VONG)
    assert _trang_thai(kq) == {f"CLAUDE.md @{c1}": "CU", f"HANDOFF.md @{c1}": "TUOI", f"SKILL.md @{c1}": "TUOI"}
    assert kq["ket_luan"] == "CU" and kq["thieu"] == []
    assert kq["ma_so_voi"] == c2
    moi = st.do_tuoi([f"CLAUDE.md @{c2}", f"HANDOFF.md @{c1}", f"SKILL.md @{c2}"], git=git, ky_vong=KY_VONG)
    assert moi["ket_luan"] == "TUOI", moi


def test_DO_TUOI_ten_nhan_doi_ra_duong_dan_bang_thu_muc_khong_bang_bang_go_tay(kho):
    _, c1, _, git = kho
    kq = st.do_tuoi([f"SKILL.md @{c1}", f"HANDOFF.md @{c1}"], git=git, ky_vong=[])
    assert [d["tep"] for d in kq["nguon"]] == [".claude/skills/quy-trinh-lam-viec/SKILL.md", "docs/HANDOFF.md"]


def test_DO_TUOI_thieu_nguon_ky_vong_duoc_goi_ten(kho):
    _, c1, _, git = kho
    kq = st.do_tuoi([f"CLAUDE.md @{c1}"], git=git, ky_vong=KY_VONG)
    assert kq["thieu"] == ["docs/HANDOFF.md", ".claude/skills/quy-trinh-lam-viec/SKILL.md"]
    assert kq["ket_luan"] == "CU"


def test_DO_TUOI_ky_vong_khong_doi_ra_dung_mot_tep_cung_bi_goi_ten(kho):
    _, c1, _, git = kho
    kq = st.do_tuoi([f"CLAUDE.md @{c1}"], git=git, ky_vong=["CLAUDE.md", "khong-co.md"])
    assert kq["thieu"] == ["khong-co.md (khong doi duoc ra dung mot tep theo doi)"]


def test_DO_TUOI_bam_la_khong_phai_commit_cua_repo(kho):
    _, c1, _, git = kho
    kq = st.do_tuoi(["CLAUDE.md @deadbee"], git=git, ky_vong=[])
    assert kq["nguon"][0]["trang_thai"] == "KHONG_RO_BAM" and kq["ket_luan"] == "CU"


def test_DO_TUOI_nhan_khong_doi_ra_tep_va_nhan_mo_ho(kho):
    r, c1, _, git = kho
    _viet(r, "SKILL.md", "ban trung o goc\n")           # SKILL.md ở gốc VÀ ở thư mục skill
    _chay_git(r, "add", "-A")
    kq = st.do_tuoi([f"khong-co.md @{c1}", f"SKILL.md @{c1}"], git=git, ky_vong=[])
    assert [d["trang_thai"] for d in kq["nguon"]] == ["KHONG_THAY_TEP", "MO_HO"]
    assert kq["ket_luan"] == "CU"


def test_DO_TUOI_dong_la_trong_tep_nhan_lam_ket_luan_CU(kho):
    _, c1, c2, git = kho
    nhan, la = st.doc_nhan(f"2 nhan\nCLAUDE.md @{c2}\n\nDriveFile (pasted)\n")
    assert nhan == [f"CLAUDE.md @{c2}"] and la == ["DriveFile (pasted)"]
    kq = st.do_tuoi(nhan, la, git=git, ky_vong=["CLAUDE.md"])
    assert kq["ket_luan"] == "CU" and kq["la"] == la


def test_DO_TUOI_git_hong_thi_NO_khong_bao_tuoi():
    with pytest.raises(st.KhongKiemDuoc):
        st.do_tuoi(["CLAUDE.md @abcdef0"], git=lambda *a: (128, ""), ky_vong=[])

    def hong_diff(*a):
        return (2, "") if a[0] == "diff" else ((0, "CLAUDE.md\n") if a[0] == "ls-files" else (0, "abcdef0\n"))
    with pytest.raises(st.KhongKiemDuoc):
        st.do_tuoi(["CLAUDE.md @abcdef0"], git=hong_diff, ky_vong=[])


@pytest.mark.parametrize("co, trang_thai, thieu", [
    # mỗi BƯỚC dài 132 ký tự. 270: hai BƯỚC một khúc -> BƯỚC 4 dài thêm khúc 2 (CU), không khúc mới
    (270, ["TUOI", "CU"], []),
    # 200: một BƯỚC một khúc -> BƯỚC 4 là khúc MỚI (THIẾU), ba khúc cũ vẫn tươi
    (200, ["TUOI", "TUOI", "TUOI"], ["docs/STATE.md phan4/4"]),
])
def test_DO_TUOI_STATE_theo_khuc_khuc_dau_van_tuoi_khuc_cuoi_cu_va_khuc_moi_THIEU(kho, co, trang_thai, thieu):
    r, c1, c2, git = kho
    cu = (r / "docs/STATE.md").read_text(encoding="utf-8")
    kh1 = st.ke_hoach_chia(subprocess.run(["git", "-C", str(r), "show", f"{c1}:docs/STATE.md"],
                                          capture_output=True, text=True, encoding="utf-8").stdout, c1, co)
    kh2 = st.ke_hoach_chia(cu, c2, co)
    assert len(kh1) == len(trang_thai) and len(kh2) >= len(kh1), (len(kh1), len(kh2))
    nhan = [f"STATE.md @{c1} phan{i}/{len(kh1)} (BUOC {k['buoc_tu']}-{k['buoc_den']})"
            for i, k in enumerate(kh1, 1)]
    kq = st.do_tuoi(nhan, git=git, ky_vong=["STATE.md"], co_phan=co)
    assert [d["trang_thai"] for d in kq["nguon"]] == trang_thai, kq    # BƯỚC thêm ở CUỐI không làm khúc đầu cũ đi
    assert kq["thieu"] == thieu, kq
    assert kq["ket_luan"] == "CU"
    # đủ khúc mới nhất, cùng băm c2 -> tươi hết
    nhan2 = [f"STATE.md @{c2} phan{i}/{len(kh2)} (BUOC {k['buoc_tu']}-{k['buoc_den']})"
             for i, k in enumerate(kh2, 1)]
    ok = st.do_tuoi(nhan2, git=git, ky_vong=["STATE.md"], co_phan=co)
    assert ok["ket_luan"] == "TUOI" and ok["thieu"] == [], ok


def test_DO_TUOI_STATE_nap_nguyen_tep_khong_khuc_thi_khong_bi_goi_thieu_khuc(kho):
    _, c1, c2, git = kho
    kq = st.do_tuoi([f"STATE.md @{c2}"], git=git, ky_vong=["STATE.md"])
    assert kq["thieu"] == [] and kq["ket_luan"] == "TUOI"
    cu = st.do_tuoi([f"STATE.md @{c1}"], git=git, ky_vong=["STATE.md"])
    assert cu["nguon"][0]["trang_thai"] == "CU"


def test_TOM_TAT_la_MOT_dong_nhac_ten_nguon_cu_va_thieu(kho):
    _, c1, _, git = kho
    kq = st.do_tuoi([f"CLAUDE.md @{c1}", f"HANDOFF.md @{c1}"], git=git, ky_vong=KY_VONG)
    t = st.tom_tat_do_tuoi(kq)
    assert "\n" not in t and "không hỏi mô hình" in t
    assert f"CLAUDE.md @{c1} = CU" in t and "THIẾU" in t and "SKILL.md" in t
    assert "2 nguồn, 1 tươi" in t and t.endswith("kết luận CU.")


def test_GHI_nhan_nguon_sinh_nguon_va_do_tuoi_tu_git_khong_tu_loi_khai(kho, tmp_path, so_tam):
    _, c1, c2, git = kho
    (tmp_path / "nhan.txt").write_text(f"3 nhan\nCLAUDE.md @{c2}\nHANDOFF.md @{c1}\nSKILL.md @{c1}\n", encoding="utf-8")
    cau = st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["a statement that y"])
    m = {"buoc": "BƯỚC 9999", "cau_hoi": cau, "nhan_nguon_tep": str(tmp_path / "nhan.txt"),
         "phat_hien": [{"noi_dung": "n", "tu_kiem": "grep -n x CLAUDE.md -> 1", "phan_quyet": "THẬT."}]}
    # NGUON_MAC_DINH có 15 tên, ở kho thử chỉ 3 tệp: phần thiếu phải hiện ra, không bị nuốt
    dong = st.ghi(m, so=so_tam, ngay="2026-10-30", git=git)
    assert dong["nguon"] == [f"CLAUDE.md @{c2}", f"HANDOFF.md @{c1}", f"SKILL.md @{c1}"]
    assert dong["_do_tuoi"].startswith("ĐO BẰNG NHÃN") and "THIẾU" in dong["_do_tuoi"]
    assert "nhan_nguon_tep" not in dong


def test_GHI_nhan_nguon_so_voi_mot_commit_khac_HEAD(kho, tmp_path, so_tam):
    """`nhan_nguon_so_voi` chọn mốc so sánh: c1 là HEAD~1 nên CLAUDE.md @c1 TƯƠI so với c1 mà CŨ so với HEAD."""
    r, c1, c2, git = kho
    (tmp_path / "nhan.txt").write_text(f"CLAUDE.md @{c1}\n", encoding="utf-8")
    cau = st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["a statement that y"])
    m = {"buoc": "BƯỚC 9999", "cau_hoi": cau, "nhan_nguon_tep": str(tmp_path / "nhan.txt"),
         "phat_hien": [{"noi_dung": "n", "tu_kiem": "grep -n x CLAUDE.md -> 1", "phan_quyet": "THẬT."}]}
    cu = st.ghi({**m, "nhan_nguon_so_voi": c1}, so=so_tam, ngay="2026-10-30", git=git)
    assert f"so với {c1} {c1}" in cu["_do_tuoi"] and "CLAUDE.md @" + c1 + " = " not in cu["_do_tuoi"]
    moi = st.ghi({**m, "buoc": "BƯỚC 9998"}, so=so_tam, ngay="2026-10-30", git=git)
    assert f"CLAUDE.md @{c1} = CU" in moi["_do_tuoi"] and f"so với HEAD {c2}" in moi["_do_tuoi"]


def test_GHI_nhan_nguon_ket_hop_khai_tay_nguon_hoac_do_tuoi_la_TU_CHOI(kho, tmp_path, so_tam):
    _, c1, _, git = kho
    (tmp_path / "nhan.txt").write_text(f"CLAUDE.md @{c1}\n", encoding="utf-8")
    cau = st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["a statement that y"])
    co = {"buoc": "BƯỚC 9999", "cau_hoi": cau, "nhan_nguon_tep": str(tmp_path / "nhan.txt"),
          "phat_hien": [{"noi_dung": "n", "tu_kiem": "grep -n x CLAUDE.md -> 1", "phan_quyet": "THẬT."}]}
    truoc = so_tam.read_bytes()
    for them in ({"_do_tuoi": "toi noi tuoi roi"}, {"nguon": ["CLAUDE.md @1234567"]}):
        with pytest.raises(st.TuChoi, match="khong khai tay"):
            st.ghi({**co, **them}, so=so_tam, ngay="2026-10-30", git=git)
    (tmp_path / "nhan.txt").write_text("\n2 nhan\n", encoding="utf-8")
    with pytest.raises(st.TuChoi, match="MAU HONG"):
        st.ghi(co, so=so_tam, ngay="2026-10-30", git=git)
    assert so_tam.read_bytes() == truoc


def test_GHI_do_tuoi_khong_do_duoc_thi_TU_CHOI_va_khong_cham_so(tmp_path, so_tam):
    (tmp_path / "nhan.txt").write_text("CLAUDE.md @abcdef0\n", encoding="utf-8")
    cau = st.dung_cau_hoi("BƯỚC 9999", "x" * 60, ["a statement that y"])
    m = {"buoc": "BƯỚC 9999", "cau_hoi": cau, "nhan_nguon_tep": str(tmp_path / "nhan.txt"),
         "phat_hien": [{"noi_dung": "n", "tu_kiem": "grep -n x CLAUDE.md -> 1", "phan_quyet": "THẬT."}]}
    truoc = so_tam.read_bytes()
    with pytest.raises(st.TuChoi, match="CHUA KIEM DUOC"):
        st.ghi(m, so=so_tam, ngay="2026-10-30", git=lambda *a: (128, ""))
    assert so_tam.read_bytes() == truoc


def test_CLI_do_tuoi_tren_repo_that_ma_thoat_va_tom_tat(tmp_path):
    head = subprocess.run(["git", "-C", str(GOC), "rev-parse", "--short=7", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    nhan = tmp_path / "nhan.txt"
    nhan.write_text(f"CLAUDE.md @{head}\n", encoding="utf-8")

    def cli(*a):
        return subprocess.run([sys.executable, str(GOC / "tools" / "so_tay.py"), "do-tuoi", *a],
                              capture_output=True, text=True, encoding="utf-8", cwd=str(GOC))
    r = cli(str(nhan))
    assert r.returncode == 1 and "TUOI           CLAUDE.md" in r.stdout and "THIEU" in r.stdout, r
    assert "KET LUAN CU" in r.stdout
    t = cli(str(nhan), "--tom-tat")
    assert t.returncode == 1 and t.stdout.count("\n") == 1 and "ĐO BẰNG NHÃN" in t.stdout
    nhan.write_text("0 nhan\n", encoding="utf-8")
    rong = cli(str(nhan))
    assert rong.returncode == 1 and "MAU HONG" in rong.stderr
    vang = cli(str(tmp_path / "vang.txt"))
    assert vang.returncode == 2 and "Traceback" not in vang.stderr


def test_MAC_DINH_ky_vong_la_NGUON_MAC_DINH_va_moi_ten_doi_duoc_ra_DUNG_MOT_tep_that():
    """Gác chống trôi: đổi tên/xoá một tệp nguồn mà quên cập nhật NGUON_MAC_DINH -> đỏ."""
    rc, ls = st._git_that("ls-files")
    theo_doi = set(ls.splitlines())
    hong = {t: st._doi_ten(t, theo_doi) for t in st.NGUON_MAC_DINH
            if len(st._doi_ten(t, theo_doi)) != 1}
    assert not hong, hong
