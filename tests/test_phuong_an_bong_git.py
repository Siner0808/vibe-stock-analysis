"""Cổng TIỀN ĐĂNG KÝ của sổ PHƯƠNG ÁN BÓNG `docs/phuong-an-bong.json`, đọc bằng LỊCH SỬ GIT — BƯỚC 242
(Lát 3a của C1; `docs/thiet-ke-c1-san-dau.md` mục 9, gác G7 mục 11).

Khuôn `tests/test_tien_dang_ky_git.py` (cùng máy đọc blob, cùng đi theo CẠNH cha → con của HEAD, cùng
repo nông thì ĐỎ), khác ở sáu luật của `phuong_an_bong.vi_pham_tien_dang_ky`:
  (a) dòng mới mang `commit: null`;           (b) lop / bo_co / mo_ta / ly_do / khai_ngay không đổi;
  (c) `commit` null → mã băm của COMMIT ĐẦU TIÊN có dòng, đúng một lần — mã băm này KIỂM BẰNG GIT, nên bộ
      đi theo cạnh tính `commit_dau` {id: commit đầu tiên có dòng} từ chính lịch sử;
  (d) không xoá dòng;                         (e) khai_ngay = ngày COMMITTER giờ VN;
  (f) lop ∈ {tham_do}, id `PB-nnn`, bo_co hợp lệ.

Sổ thật chỉ có các dòng đã khai, nên từng luật được thử trên repo git tạm dựng trong `tmp_path`; một test
chạy trên repo thật và phải đi qua commit tạo sổ — máy đo không thấy gì cũng cho "0 vi phạm".

LƯU Ý GIAO PR: luật (c) và (e) gắn với MÃ BĂM và NGÀY của commit đầu tiên có dòng. Hợp nhất PR bằng
`--merge`; squash đổi cả hai và làm cổng này đỏ trên `main`.
"""
import json
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pytest

import cham_bong as cb
import phuong_an_bong as pab
from test_tien_dang_ky_git import _chay, _doc_blob, _git  # noqa: E402  (máy đọc blob dùng chung)

SO = "docs/phuong-an-bong.json"
BAM_GIA = "0123456789abcdef0123456789abcdef01234567"


# ── máy đọc lịch sử ──────────────────────────────────────────────────────

def vi_pham_lich_su(repo, duong: str = SO) -> tuple[list[str], list[str], dict]:
    """(vi phạm, các commit ĐÃ phán, {id: mã băm commit đầu tiên có dòng}) trên mọi commit tổ tiên của HEAD."""
    if _chay(repo, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise RuntimeError("repo NONG (shallow): lich su bi cat, cong tien dang ky "
                           "mu — CI phai checkout voi fetch-depth: 0")
    commit = [d.split() for d in
              _chay(repo, "log", "--format=%H %cI %P", "--topo-order", "HEAD").decode().splitlines()
              if d.strip()]
    hoi = "".join(f"{c[0]}:{duong}\n" for c in commit).encode()
    blob = {}
    for c, t in zip(commit, _chay(repo, "cat-file", "--batch-check",
                                  dau_vao=hoi).decode().splitlines()):
        blob[c[0]] = None if t.endswith(" missing") else t.split()[0]
    so = _doc_blob(repo, {b for b in blob.values() if b})

    def ids(b):
        v = so.get(b) if b else None
        pa = v.get("phuong_an") if isinstance(v, dict) else None
        return set(pa) if isinstance(pa, dict) else set()

    # Commit đầu tiên có dòng = commit mà dòng có ở đó và KHÔNG cha nào có. `--topo-order` đảo lại: cha
    # đứng trước con, nên lần đầu gặp một id là commit đầu tiên theo thứ tự lịch sử.
    commit_dau: dict = {}
    for ma, _, *cha in reversed(commit):
        moi = ids(blob[ma]) - set().union(*[ids(blob[p]) for p in cha]) if cha else ids(blob[ma])
        for i in sorted(moi):
            commit_dau.setdefault(i, ma)

    loi, da_phan = [], []
    for ma, luc, *cha in commit:
        b, b_cha = blob[ma], [blob[p] for p in cha]
        if b is None and not any(b_cha):
            continue
        if cha and all(x == b for x in b_cha):
            continue
        da_phan.append(ma)
        hong = [x for x in [b, *b_cha] if x and isinstance(so[x], Exception)]
        if hong:
            loi.append(f"{ma[:7]}: khong doc duoc JSON ({so[hong[0]]})")
            continue
        con = so[b] if b else {"phuong_an": {}}
        loi += [f"{ma[:7]}: {v}" for v in
                pab.vi_pham_tien_dang_ky(con, [so[x] for x in b_cha if x], cb.ngay_vn(luc), commit_dau)]
    return loi, da_phan, commit_dau


# ── repo tạm ─────────────────────────────────────────────────────────────

def _pb(ngay: str, commit=None, **doi) -> dict:
    d = {"lop": "tham_do", "bo_co": {"nghi_sau_lo_ngay": 7}, "khai_ngay": ngay, "commit": commit,
         "mo_ta": f"thu {ngay}", "ly_do": "test"}
    d.update(doi)
    return d


def _ghi(repo, pa: dict, ngay: str, ngay_tac_gia: str | None = None) -> str:
    p = repo / SO
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps({"phuong_an": pa}, ensure_ascii=False, indent=1), encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "x", ngay=ngay, ngay_tac_gia=ngay_tac_gia)
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def kho(tmp_path):
    """Repo tạm có sổ rỗng — đúng khởi điểm của một sổ mới."""
    repo = tmp_path / "kho"
    repo.mkdir()
    _git(repo, "init", "-q")
    _ghi(repo, {}, "2026-10-01T09:00:00+07:00")
    return repo


#: Giờ VN: 10:00 ngày 05/10 → 2026-10-05.
T1 = "2026-10-05T10:00:00+07:00"
T2 = "2026-10-06T10:00:00+07:00"
T3 = "2026-10-07T10:00:00+07:00"
T4 = "2026-10-08T10:00:00+07:00"


def _chi_thich(loi):
    return [l[l.rindex("("):] for l in loi]


def test_LICH_SU_SACH_khai_null_roi_dien_ma_bam_dau_tien_mot_lan_thi_KHONG_vi_pham(kho):
    c1 = _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05", c1), "PB-002": _pb("2026-10-06")}, T2)
    loi, da_phan, dau = vi_pham_lich_su(kho)
    assert loi == [], loi
    assert len(da_phan) == 3, "commit tao so + hai commit doi so"
    assert dau["PB-001"] == c1 and set(dau) == {"PB-001", "PB-002"}


def test_a_COMMIT_KHAI_mang_commit_khac_null_thi_DO(kho):
    _ghi(kho, {"PB-001": _pb("2026-10-05", BAM_GIA)}, T1)
    loi, _, _ = vi_pham_lich_su(kho)
    assert _chi_thich(loi) == ["(a)"], loi


@pytest.mark.parametrize("truong, gia_tri_moi", [
    ("khai_ngay", "2026-10-04"),
    ("mo_ta", "mo ta viet lai sau khi thay ket qua"),
    ("ly_do", "ly do khac"),
    ("lop", "xac_nhan"),
    ("bo_co", {"nghi_sau_lo_ngay": 9}),
])
def test_b_SUA_truong_da_khai_thi_DO(kho, truong, gia_tri_moi):
    _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05", **{truong: gia_tri_moi})}, T2)
    loi, _, _ = vi_pham_lich_su(kho)
    assert any("(b)" in l and truong in l for l in loi), loi


def test_c_commit_phai_la_COMMIT_DAU_TIEN_co_dong__ma_bam_cua_commit_khac_thi_DO(kho):
    c1 = _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    c2 = _ghi(kho, {"PB-001": _pb("2026-10-05"), "PB-002": _pb("2026-10-06")}, T2)
    assert c1 != c2
    # điền mã băm của commit THỨ HAI (không phải commit đầu tiên có PB-001)
    _ghi(kho, {"PB-001": _pb("2026-10-05", c2), "PB-002": _pb("2026-10-06")}, T3)
    loi, _, _ = vi_pham_lich_su(kho)
    assert _chi_thich(loi) == ["(c)"], loi


def test_c_commit_dien_dung_nhung_o_commit_sau_nua_van_sach(kho):
    c1 = _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05"), "PB-002": _pb("2026-10-06")}, T2)
    _ghi(kho, {"PB-001": _pb("2026-10-05", c1), "PB-002": _pb("2026-10-06")}, T3)
    loi, _, _ = vi_pham_lich_su(kho)
    assert loi == [], loi


@pytest.mark.parametrize("sau", [None, "khac", 7, "0123456789abcdef"])
def test_c_commit_DA_DIEN_thi_khong_doi_nua(kho, sau):
    c1 = _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05", c1)}, T2)
    _ghi(kho, {"PB-001": _pb("2026-10-05", sau)}, T3)
    loi, _, _ = vi_pham_lich_su(kho)
    assert any("(c)" in l for l in loi), loi


def test_c_commit_dien_mot_ma_bam_KHONG_phai_40_ky_tu_hex_thi_DO(kho):
    _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05", "abc123")}, T2)
    loi, _, _ = vi_pham_lich_su(kho)
    assert any("(c)" in l for l in loi) and any("(f)" in l for l in loi), loi


def test_d_XOA_dong_da_khai_thi_DO(kho):
    _ghi(kho, {"PB-001": _pb("2026-10-05"), "PB-002": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05")}, T2)
    loi, _, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(d)" in loi[0] and "PB-002" in loi[0], loi


def test_d_XOA_CA_FILE_thi_DO(kho):
    _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _git(kho, "rm", "-q", SO)
    _git(kho, "commit", "-q", "-m", "xoa", ngay=T2)
    loi, _, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(d)" in loi[0], loi


@pytest.mark.parametrize("luc_commit, khai_ngay, ky_vong", [
    (T1, "2026-10-05", []),
    (T1, "2026-10-04", ["(e)"]),                      # khai lùi một ngày
    (T1, "2026-10-06", ["(e)"]),                      # khai tới — cũng sai
    # 17:30 UTC ngày 05 = 00:30 giờ VN ngày 06: ngày theo giờ VN, không theo UTC.
    ("2026-10-05T17:30:00+00:00", "2026-10-06", []),
    ("2026-10-05T17:30:00+00:00", "2026-10-05", ["(e)"]),
])
def test_e_khai_ngay_la_ngay_COMMIT_KHAI_theo_GIO_VN(kho, luc_commit, khai_ngay, ky_vong):
    _ghi(kho, {"PB-001": _pb(khai_ngay)}, luc_commit)
    loi, _, _ = vi_pham_lich_su(kho)
    assert _chi_thich(loi) == ky_vong, loi


def test_e_ngay_TAC_GIA_lui_khong_cuu_duoc_commit_khai(kho):
    """Rebase giữ ngày tác giả cũ; cổng đọc ngày COMMITTER (chiều chặt)."""
    _ghi(kho, {"PB-001": _pb("2026-10-05")}, T2, ngay_tac_gia=T1)
    loi, _, _ = vi_pham_lich_su(kho)
    assert _chi_thich(loi) == ["(e)"], loi


@pytest.mark.parametrize("dong, ky_vong", [
    ({"PB-001": _pb("2026-10-05", lop="xac_nhan")}, "lop"),
    ({"UV-001": _pb("2026-10-05")}, "id"),
    ({"PB-1": _pb("2026-10-05")}, "id"),
    ({"PB-001": _pb("2026-10-05", bo_co={"khong_co_co_nay": 1})}, "truong"),
    ({"PB-001": _pb("2026-10-05", bo_co={"nghi_sau_lo_ngay": "bay"})}, "kieu"),
    ({"PB-001": _pb("2026-10-05", bo_co={"cong_vni_bat": 0})}, "kieu"),
    ({"PB-001": _pb("2026-10-05", bo_co={"loc_imom_phan_vi": 0.2})}, "nguon tiem"),
    ({"PB-001": _pb("2026-10-05", bo_co={"chot_sut_giam_nguong": 0.15})}, "nguon tiem"),
    ({"PB-001": _pb("2026-10-05", bo_co={"luat_vao": "LUAT_LA"})}, "luat_vao"),
    ({"PB-001": _pb("2026-10-05", bo_co={})}, "khong rong"),
    ({"PB-001": _pb("2026-10-05", mo_ta="")}, "mo_ta"),
    ({"PB-001": _pb("5/10/2026")}, "khai_ngay"),
    ({"PB-001": _pb("2026-10-05", bo_co={"chot_sut_giam_phien": 20})}, "nguon tiem"),
    ({"PB-001": _pb("2026-10-05", bo_co={"do_rong_nguong": True})}, "kieu"),
])
def test_f_dong_khong_hop_le_thi_DO(kho, dong, ky_vong):
    _ghi(kho, dong, T1)
    loi, _, _ = vi_pham_lich_su(kho)
    assert any("(f)" in l for l in loi), loi


def _nhanh_hien_tai(repo) -> str:
    return _git(repo, "branch", "--show-current").strip()


def test_GOP_hai_nhanh_GIU_DU_dong_cua_CA_HAI_cha_thi_SACH(kho):
    chinh = _nhanh_hien_tai(kho)
    _git(kho, "checkout", "-q", "-b", "nhanh")
    _ghi(kho, {"PB-002": _pb("2026-10-05")}, T1)
    _git(kho, "checkout", "-q", chinh)
    _ghi(kho, {"PB-001": _pb("2026-10-06")}, T2)
    _git(kho, "merge", "-q", "--no-commit", "-s", "ours", "nhanh", ngay=T3)
    _ghi(kho, {"PB-001": _pb("2026-10-06"), "PB-002": _pb("2026-10-05")}, T3)
    loi, _, dau = vi_pham_lich_su(kho)
    # PB-002 có ở cha THỨ HAI: không phải dòng mới của commit gộp, nên ngày gộp (07/10) không được so với
    # khai_ngay 05/10 của nó.
    assert loi == [], loi
    assert set(dau) == {"PB-001", "PB-002"}


def test_GOP_lam_MAT_dong_chi_co_o_CHA_THU_HAI_thi_DO(kho):
    chinh = _nhanh_hien_tai(kho)
    _git(kho, "checkout", "-q", "-b", "nhanh")
    _ghi(kho, {"PB-002": _pb("2026-10-05")}, T1)
    _git(kho, "checkout", "-q", chinh)
    _ghi(kho, {"PB-001": _pb("2026-10-06")}, T2)
    _git(kho, "merge", "-q", "-s", "ours", "-m", "gop", "nhanh", ngay=T3)
    loi, _, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(d)" in loi[0] and "PB-002" in loi[0], loi


def test_GOP_bang_merge_commit_giu_ma_bam_dien_o_commit_sau__dung_cach_giao_PR(kho):
    """Cách giao PR: nhánh khai dòng (commit C1), điền mã băm của C1 (commit C2), rồi gộp bằng merge vào
    nhánh chính đã tiến thêm một commit. Cổng sạch ở HEAD là commit gộp."""
    chinh = _nhanh_hien_tai(kho)
    _git(kho, "checkout", "-q", "-b", "pr")
    c1 = _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05", c1)}, T2)
    _git(kho, "checkout", "-q", chinh)
    (kho / "khac.txt").write_text("x", encoding="utf-8")
    _git(kho, "add", "-A")
    _git(kho, "commit", "-q", "-m", "khac", ngay=T3)
    _git(kho, "merge", "-q", "--no-ff", "-m", "gop", "pr", ngay=T4)
    loi, _, dau = vi_pham_lich_su(kho)
    assert loi == [], loi
    assert dau["PB-001"] == c1


def test_SQUASH_doi_ma_bam_va_ngay__cong_DO_nen_PR_phai_hop_nhat_bang_merge(kho):
    """Bằng chứng cho dòng cảnh báo ở đầu file: squash tạo commit MỚI mang cả `commit` đã điền lẫn
    `khai_ngay` cũ; commit ấy là commit đầu tiên có dòng và nó mang mã băm khác, ngày khác."""
    chinh = _nhanh_hien_tai(kho)
    _git(kho, "checkout", "-q", "-b", "pr")
    c1 = _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    _ghi(kho, {"PB-001": _pb("2026-10-05", c1)}, T2)
    _git(kho, "checkout", "-q", chinh)
    _git(kho, "merge", "-q", "--squash", "pr")
    _git(kho, "commit", "-q", "-m", "squash", ngay=T4)
    loi, _, _ = vi_pham_lich_su(kho)
    assert any("(a)" in l for l in loi) and any("(e)" in l for l in loi), loi


def test_JSON_HONG_o_mot_phien_ban_thi_DO(kho):
    (kho / SO).write_text("{khong phai json", encoding="utf-8")
    _git(kho, "add", "-A")
    _git(kho, "commit", "-q", "-m", "hong", ngay=T1)
    loi, _, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "JSON" in loi[0], loi


def test_REPO_NONG_thi_NO_khong_xanh_im(kho, tmp_path):
    _ghi(kho, {"PB-001": _pb("2026-10-05")}, T1)
    nong = tmp_path / "nong"
    _git(tmp_path, "clone", "-q", "--depth", "1", kho.resolve().as_uri(), str(nong))
    assert _git(nong, "rev-parse", "--is-shallow-repository").strip() == "true"
    with pytest.raises(RuntimeError, match="NONG"):
        vi_pham_lich_su(nong)


def test_LICH_SU_THAT_cua_so_phuong_an_bong_SACH():
    """Repo thật. Đỏ ở repo nông (CI thiếu `fetch-depth: 0`) — chủ ý. Phải đi qua commit tạo từng dòng:
    máy đo không thấy gì cũng cho "0 vi phạm"."""
    loi, da_phan, dau = vi_pham_lich_su(GOC)
    so = json.loads((GOC / SO).read_text(encoding="utf-8"))
    assert {"PB-001", "PB-002"} <= set(so["phuong_an"]), "sổ thật thiếu PB-001 / PB-002"
    for ma in so["phuong_an"]:
        assert ma in dau and dau[ma] in da_phan, f"máy đọc lịch sử không đi qua commit khai {ma}"
        # ngày khai khớp ngày COMMITTER của commit đầu tiên (luật (e), kiểm riêng ở đây bằng git thô)
        luc = _chay(GOC, "log", "-1", "--format=%cI", dau[ma]).decode().strip()
        assert so["phuong_an"][ma]["khai_ngay"] == cb.ngay_vn(luc), ma
    assert loi == [], loi


def test_SO_THAT_hop_le_khong_can_git():
    so = json.loads((GOC / SO).read_text(encoding="utf-8"))
    assert pab.vi_pham_so(so) == []
    assert not [k for k in so["phuong_an"] if not k.startswith("PB-")]
    assert all(d["lop"] == "tham_do" for d in so["phuong_an"].values())


# ── máy đo của chính cổng: phép thử đơn vị trên hàm thuần ────────────────

def test_vi_pham_tien_dang_ky_thuan__tung_luat_mot_dong():
    c = {"PB-001": _pb("2026-10-05")}
    assert pab.vi_pham_tien_dang_ky({"phuong_an": c}, [], "2026-10-05", {}) == []
    # khai lùi
    assert any("(e)" in l for l in pab.vi_pham_tien_dang_ky({"phuong_an": c}, [], "2026-10-06", {}))
    # cha có dòng, con điền mã băm khớp commit_dau
    cha = {"phuong_an": c}
    con = {"phuong_an": {"PB-001": _pb("2026-10-05", BAM_GIA)}}
    assert pab.vi_pham_tien_dang_ky(con, [cha], "2026-10-09", {"PB-001": BAM_GIA}) == []
    assert any("(c)" in l for l in pab.vi_pham_tien_dang_ky(con, [cha], "2026-10-09", {"PB-001": "f" * 40}))
    assert any("(c)" in l for l in pab.vi_pham_tien_dang_ky(con, [cha], "2026-10-09", {}))
    # xoá
    assert any("(d)" in l for l in pab.vi_pham_tien_dang_ky({"phuong_an": {}}, [cha], "2026-10-09", {}))
    # sổ hỏng
    assert pab.vi_pham_tien_dang_ky({}, [], "2026-10-05", {}) == ["khong doc duoc khoa phuong_an"]
