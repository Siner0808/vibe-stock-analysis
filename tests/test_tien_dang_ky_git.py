"""Cổng TIỀN ĐĂNG KÝ của sổ ứng viên, đọc bằng LỊCH SỬ GIT — BƯỚC 153 (P3c-1).

Vì sao: `docs/ung-vien.json` ghi *"khai TRƯỚC khi chạy vòng sàng, không sửa,
không xoá dòng đã khai"*, nhưng một file chỉ cho thấy trạng thái HIỆN TẠI. Sửa
`mo_ta` sau khi thấy kết quả, khai lùi ngày, hay xoá một ứng viên rớt (giấu mẫu
số K) đều để lại một file hợp khuôn. Chỉ lịch sử mới chứng được thứ tự.

Năm luật, phán bởi `cham_bong.vi_pham_tien_dang_ky` trên MỖI cạnh cha → con
của HEAD mà file đổi:
  (a) commit đầu tiên có một ứng viên phải mang `qua_sang: null`;
  (b) khai_ngay / mo_ta / ly_do / spec không đổi ở mọi phiên bản sau;
  (c) `qua_sang` chỉ đổi null → true/false MỘT lần;
  (d) không dòng nào bị xoá;
  (e) khai_ngay = ngày commit khai, giờ VN — ngày COMMITTER (`%cI`), không
      phải ngày tác giả: rebase/amend đẩy nó về sau (chiều chặt), còn ngày tác
      giả giữ được ngày cũ qua rebase (chiều lỏng).

Đi theo CẠNH chứ không theo một dãy thẳng: commit gộp có hai cha, và một phép
gộp có thể xoá dòng chỉ có ở cha thứ hai — đi một dãy thẳng theo cha đầu thì
không thấy.

REPO NÔNG THÌ ĐỎ, không xanh im: `actions/checkout` mặc định `fetch-depth: 1`
cho đúng một commit không cha — mọi dòng hiện tại trông như "vừa khai", và sổ
rỗng thì cổng xanh mà chưa đọc gì. CI đặt `fetch-depth: 0`
(`.github/workflows/kiem-dinh.yml`); ai gỡ nó thì test này đỏ chứ không mù.

Sổ thật đang rỗng, nên từng luật được thử trên repo git tạm dựng trong
`tmp_path`; một test chạy trên repo thật và phải đi qua commit tạo sổ (BƯỚC
144, `1aadda5`) — máy đo không thấy gì cũng cho "0 vi phạm".
"""
import json
import os
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import pytest

import cham_bong as cb

SO = "docs/ung-vien.json"
#: Commit tạo sổ (BƯỚC 144, PR #189, squash vào `main`) — ca THẬT máy đo phải đi qua.
COMMIT_TAO_SO = "1aadda5"


# ── máy đọc lịch sử ──────────────────────────────────────────────────────

def _chay(repo, *args, dau_vao: bytes | None = None) -> bytes:
    r = subprocess.run(["git", "-c", "log.showSignature=false", *args], cwd=str(repo),
                       input=dau_vao, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: "
                           f"{r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def _doc_blob(repo, ids: set) -> dict:
    """{mã blob: sổ đã parse, hoặc ValueError nếu không phải JSON}."""
    if not ids:
        return {}
    ra = _chay(repo, "cat-file", "--batch", dau_vao="".join(f"{i}\n" for i in ids).encode())
    kq, i = {}, 0
    while i < len(ra):
        j = ra.index(b"\n", i)
        ma, _, co = ra[i:j].decode().split()
        noi = ra[j + 1:j + 1 + int(co)]
        i = j + 1 + int(co) + 1
        try:
            kq[ma] = json.loads(noi.decode("utf-8"))
        except ValueError as e:
            kq[ma] = e
    return kq


def vi_pham_lich_su(repo, duong: str = SO) -> tuple[list[str], list[str]]:
    """(vi phạm, các commit ĐÃ phán) trên mọi commit tổ tiên của HEAD.

    Một commit được phán khi file của nó khác file của ít nhất một cha (hoặc
    nó tạo file). Bốn lời gọi git cho cả repo, không một lời mỗi commit.
    """
    if _chay(repo, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise RuntimeError("repo NONG (shallow): lich su bi cat, cong tien dang ky "
                           "mu — CI phai checkout voi fetch-depth: 0")
    commit = [d.split() for d in
              _chay(repo, "log", "--format=%H %cI %P", "HEAD").decode().splitlines()
              if d.strip()]
    hoi = "".join(f"{c[0]}:{duong}\n" for c in commit).encode()
    blob = {}
    for c, t in zip(commit, _chay(repo, "cat-file", "--batch-check",
                                  dau_vao=hoi).decode().splitlines()):
        blob[c[0]] = None if t.endswith(" missing") else t.split()[0]
    so = _doc_blob(repo, {b for b in blob.values() if b})
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
        con = so[b] if b else {"ung_vien": {}}
        loi += [f"{ma[:7]}: {v}" for v in
                cb.vi_pham_tien_dang_ky(con, [so[x] for x in b_cha if x], cb.ngay_vn(luc))]
    return loi, da_phan


# ── repo tạm ─────────────────────────────────────────────────────────────

def _git(repo, *args, ngay: str | None = None, ngay_tac_gia: str | None = None) -> str:
    env = dict(os.environ)
    if ngay:
        env["GIT_COMMITTER_DATE"] = ngay
        env["GIT_AUTHOR_DATE"] = ngay_tac_gia or ngay
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *args], cwd=str(repo), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"git {' '.join(args)} loi: {r.stderr}"
    return r.stdout


def _uv(ngay: str, qua=None, **doi) -> dict:
    d = {"khai_ngay": ngay, "mo_ta": f"thu {ngay}", "ly_do": "test", "qua_sang": qua,
         "spec": {"loai": "trong_so", "trong_so": {"trend_score": 0.5, "volume_score": 0.5}}}
    d.update(doi)
    return d


def _ghi(repo, uv: dict, ngay: str, ngay_tac_gia: str | None = None) -> None:
    p = repo / SO
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps({"ung_vien": uv}, ensure_ascii=False, indent=1), encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "x", ngay=ngay, ngay_tac_gia=ngay_tac_gia)


@pytest.fixture
def kho(tmp_path):
    """Repo tạm có sổ rỗng — đúng khởi điểm của sổ thật."""
    repo = tmp_path / "kho"
    repo.mkdir()
    _git(repo, "init", "-q")
    _ghi(repo, {}, "2026-10-01T09:00:00+07:00")
    return repo


#: Giờ VN: 10:00 ngày 05/10 → 2026-10-05.
T1 = "2026-10-05T10:00:00+07:00"
T2 = "2026-10-06T10:00:00+07:00"
T3 = "2026-10-07T10:00:00+07:00"


def test_LICH_SU_SACH_khai_null_roi_sang_mot_lan_thi_KHONG_vi_pham(kho):
    _ghi(kho, {"UV-001": _uv("2026-10-05")}, T1)
    _ghi(kho, {"UV-001": _uv("2026-10-05", True),
               "UV-002": _uv("2026-10-06")}, T2)
    _ghi(kho, {"UV-001": _uv("2026-10-05", True),
               "UV-002": _uv("2026-10-06", False)}, T3)
    loi, da_phan = vi_pham_lich_su(kho)
    assert loi == [], loi
    assert len(da_phan) == 4, "commit tao so + ba commit doi so"
    print("PASS  khai null -> sang true/false mot lan: 0 vi pham, 4 commit da phan")


def test_a_COMMIT_KHAI_mang_ket_qua_sang_thi_DO(kho):
    _ghi(kho, {"UV-001": _uv("2026-10-05", True)}, T1)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(a)" in loi[0], loi
    print(f"PASS  (a) {loi}")


@pytest.mark.parametrize("truong, gia_tri_moi", [
    ("khai_ngay", "2026-10-04"),
    ("mo_ta", "mo ta viet lai sau khi thay ket qua"),
    ("ly_do", "ly do khac"),
    ("spec", {"loai": "trong_so", "trong_so": {"trend_score": 1.0}}),
])
def test_b_SUA_truong_da_khai_thi_DO(kho, truong, gia_tri_moi):
    _ghi(kho, {"UV-001": _uv("2026-10-05")}, T1)
    _ghi(kho, {"UV-001": _uv("2026-10-05", **{truong: gia_tri_moi})}, T2)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(b)" in loi[0] and truong in loi[0], loi


@pytest.mark.parametrize("dau, sau", [(True, False), (False, True), (True, None),
                                      (False, None), (True, 1)])
def test_c_qua_sang_DA_DIEN_thi_khong_doi_nua(kho, dau, sau):
    _ghi(kho, {"UV-001": _uv("2026-10-05")}, T1)
    _ghi(kho, {"UV-001": _uv("2026-10-05", dau)}, T2)
    _ghi(kho, {"UV-001": _uv("2026-10-05", sau)}, T3)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(c)" in loi[0], loi


def test_c_null_sang_KIEU_KHAC_bool_thi_DO(kho):
    _ghi(kho, {"UV-001": _uv("2026-10-05")}, T1)
    _ghi(kho, {"UV-001": _uv("2026-10-05", "true")}, T2)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(c)" in loi[0], loi


def test_d_XOA_dong_da_khai_thi_DO__ke_ca_dong_rot_sang(kho):
    _ghi(kho, {"UV-001": _uv("2026-10-05"), "UV-002": _uv("2026-10-05")}, T1)
    _ghi(kho, {"UV-001": _uv("2026-10-05", True), "UV-002": _uv("2026-10-05", False)}, T2)
    _ghi(kho, {"UV-001": _uv("2026-10-05", True)}, T3)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(d)" in loi[0] and "UV-002" in loi[0], loi


def test_d_XOA_CA_FILE_thi_DO(kho):
    _ghi(kho, {"UV-001": _uv("2026-10-05")}, T1)
    _git(kho, "rm", "-q", SO)
    _git(kho, "commit", "-q", "-m", "xoa", ngay=T2)
    loi, _ = vi_pham_lich_su(kho)
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
    _ghi(kho, {"UV-001": _uv(khai_ngay)}, luc_commit)
    loi, _ = vi_pham_lich_su(kho)
    assert [l[l.rindex("("):] for l in loi] == ky_vong, loi


def test_e_ngay_TAC_GIA_lui_khong_cuu_duoc_commit_khai(kho):
    """Rebase giữ ngày tác giả cũ; cổng đọc ngày COMMITTER (chiều chặt)."""
    _ghi(kho, {"UV-001": _uv("2026-10-05")}, T2, ngay_tac_gia=T1)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(e)" in loi[0], loi


def _nhanh_hien_tai(repo) -> str:
    return _git(repo, "branch", "--show-current").strip()


def test_GOP_hai_nhanh_GIU_DU_dong_cua_CA_HAI_cha_thi_SACH(kho):
    chinh = _nhanh_hien_tai(kho)
    _git(kho, "checkout", "-q", "-b", "nhanh")
    _ghi(kho, {"UV-002": _uv("2026-10-05")}, T1)
    _git(kho, "checkout", "-q", chinh)
    _ghi(kho, {"UV-001": _uv("2026-10-06")}, T2)
    _git(kho, "merge", "-q", "--no-commit", "-s", "ours", "nhanh", ngay=T3)
    _ghi(kho, {"UV-001": _uv("2026-10-06"), "UV-002": _uv("2026-10-05")}, T3)
    loi, _ = vi_pham_lich_su(kho)
    # UV-002 có ở cha THỨ HAI: không phải dòng mới của commit gộp, nên ngày gộp
    # (07/10) không được so với khai_ngay 05/10 của nó.
    assert loi == [], loi
    print("PASS  gop hai nhanh giu du dong: 0 vi pham")


def test_GOP_lam_MAT_dong_chi_co_o_CHA_THU_HAI_thi_DO(kho):
    chinh = _nhanh_hien_tai(kho)
    _git(kho, "checkout", "-q", "-b", "nhanh")
    _ghi(kho, {"UV-002": _uv("2026-10-05")}, T1)
    _git(kho, "checkout", "-q", chinh)
    _ghi(kho, {"UV-001": _uv("2026-10-06")}, T2)
    # -s ours: kết quả gộp = cha đầu, UV-002 của cha thứ hai biến mất.
    _git(kho, "merge", "-q", "-s", "ours", "-m", "gop", "nhanh", ngay=T3)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "(d)" in loi[0] and "UV-002" in loi[0], loi
    print(f"PASS  gop xoa dong cua cha thu hai: {loi}")


def test_JSON_HONG_o_mot_phien_ban_thi_DO(kho):
    (kho / SO).write_text("{khong phai json", encoding="utf-8")
    _git(kho, "add", "-A")
    _git(kho, "commit", "-q", "-m", "hong", ngay=T1)
    loi, _ = vi_pham_lich_su(kho)
    assert len(loi) == 1 and "JSON" in loi[0], loi


def test_REPO_NONG_thi_NO_khong_xanh_im(kho, tmp_path):
    _ghi(kho, {"UV-001": _uv("2026-10-05")}, T1)
    nong = tmp_path / "nong"
    _git(tmp_path, "clone", "-q", "--depth", "1", kho.resolve().as_uri(), str(nong))
    assert _git(nong, "rev-parse", "--is-shallow-repository").strip() == "true"
    with pytest.raises(RuntimeError, match="NONG"):
        vi_pham_lich_su(nong)
    print("PASS  repo nong -> RuntimeError, khong xanh im")


def test_LICH_SU_THAT_cua_so_ung_vien_SACH():
    """Repo thật. Đỏ ở repo nông (CI thiếu `fetch-depth: 0`) — chủ ý."""
    loi, da_phan = vi_pham_lich_su(GOC)
    assert any(h.startswith(COMMIT_TAO_SO) for h in da_phan), (
        f"may doc lich su khong di qua commit tao so {COMMIT_TAO_SO}: {da_phan}")
    assert loi == [], loi
    print(f"PASS  lich su that: {len(da_phan)} commit doi so, 0 vi pham")
