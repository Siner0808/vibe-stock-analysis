"""Skill `quy-trinh-lam-viec` phải nói ĐÚNG về repo, không chỉ nói hay.

Một skill là tài liệu, và tài liệu mục ruỗng im lặng: nó trỏ tới file đã
đổi tên, test đã xoá, lệnh không còn chạy — mà không gì kêu. Phiên sau đọc
nó rồi làm theo, và làm sai.

Đây đúng lỗi `Pha C — Wyckoff Spring` và `Fundamental Agent · BCTC Q2`: hai
ô trên giao diện hứa một thành phần không tồn tại, tồn tại nhiều ngày trước
khi ai đó `grep` thử.

File này kiểm mọi thứ skill KHẲNG ĐỊNH là có thật.
"""
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

THU_MUC_SKILL = GOC / ".claude" / "skills"
SKILL = THU_MUC_SKILL / "quy-trinh-lam-viec" / "SKILL.md"
BAY = SKILL.parent / "references" / "bay.md"

# Mọi file tham chiếu đều bị soi như SKILL.md — một trỏ dẫn chết ở đó cũng
# dẫn người đọc đi sai y hệt.
THAM_CHIEU = sorted((SKILL.parent / "references").glob("*.md"))


def test_skill_ton_tai_va_frontmatter_hop_le():
    assert SKILL.exists(), f"không có {SKILL.relative_to(GOC).as_posix()}"
    src = SKILL.read_text(encoding="utf-8")
    assert src.startswith("---\n"), "thiếu frontmatter YAML"
    fm = src.split("---", 2)[1]
    ten = re.search(r"^name:\s*(\S+)", fm, re.M)
    mo_ta = re.search(r"^description:\s*(.+)", fm, re.M)
    assert ten and mo_ta, "frontmatter thiếu name hoặc description"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", ten.group(1)), (
        f"name phải kebab-case: {ten.group(1)!r}")
    assert ten.group(1) == SKILL.parent.name, (
        f"name {ten.group(1)!r} khác tên thư mục {SKILL.parent.name!r}")
    assert "<" not in fm and ">" not in fm, "frontmatter không được có < >"
    assert len(mo_ta.group(1)) > 60, "description quá ngắn để làm điều kiện kích hoạt"
    print(f"PASS  skill {ten.group(1)} · frontmatter hợp lệ")


def _duong_dan_nhac_toi(src: str) -> set:
    """Mọi đường dẫn kiểu `abc/xyz.md` hoặc `abc.py` nằm trong dấu backtick."""
    ra = set()
    for m in re.finditer(r"`([A-Za-z0-9_./-]+\.(?:py|md|json|yml))`", src):
        ra.add(m.group(1))
    return ra


def _git_biet(d: str) -> bool | None:
    """git CÓ BIẾT đường dẫn này không — theo dõi HOẶC cố ý bỏ qua.

    Trả None khi không hỏi được git (bản tải zip): người gọi lùi về kiểm
    sự tồn tại trên đĩa.

    Vì sao không kiểm `Path.exists()`: máy dev có TRẠNG THÁI CHẠY mà CI
    không có. `sl_pattern_memory.json` được SKILL.md nhắc tới chính vì nó
    là thứ CẤM COMMIT — nó gitignore, nên nó tồn tại ở máy và vắng mặt
    trên runner. Bản đầu của gác này kiểm `exists()` và vì thế xanh tại
    máy, đỏ trên CI (31/08/2026). Đúng cùng lớp bất đối xứng với "máy chạy
    3.13, CI chạy 3.11", chỉ khác chỗ nó là trạng thái file chứ không phải
    cú pháp.
    """
    import subprocess

    def _chay(lenh):
        try:
            return subprocess.run(lenh, cwd=GOC, capture_output=True,
                                  text=True, timeout=10)
        except Exception:
            return None

    r = _chay(["git", "ls-files", "--error-unmatch", d])
    if r is None:
        return None
    if r.returncode == 0:
        return True
    r2 = _chay(["git", "check-ignore", "-q", d])
    if r2 is None:
        return None
    return r2.returncode == 0


def test_moi_file_skill_nhac_toi_deu_CO_THAT():
    """Trỏ tới file git KHÔNG BIẾT là hứa một thành phần không có.

    "git không biết" khác "không có trên đĩa": file gitignore thì git biết
    và cố ý bỏ qua — đó là mention hợp lệ. Chỉ tên gõ sai hoặc file đã đổi
    tên mới làm git ngơ ngác.
    """
    thieu = []
    for f in [SKILL] + THAM_CHIEU:
        for d in _duong_dan_nhac_toi(f.read_text(encoding="utf-8")):
            goc_skill = SKILL.parent.relative_to(GOC)
            tuong_doi = [
                d,
                (goc_skill / d).as_posix(),
                # file tham chiếu nhắc tên trần của file anh em cùng thư mục
                (goc_skill / "references" / d).as_posix(),
            ]
            ket = [_git_biet(x) for x in tuong_doi]
            if any(k is True for k in ket):
                continue
            if all(k is None for k in ket):     # không có git -> lùi về đĩa
                if any((GOC / x).exists() for x in tuong_doi):
                    continue
            thieu.append(f"{f.name} -> {d}")
    assert not thieu, "skill trỏ tới file git không biết:\n  " + "\n  ".join(thieu)
    print("PASS  mọi file skill nhắc tới đều được git biết")


def test_moi_TEST_skill_nhac_toi_deu_CO_THAT(monkeypatch):
    """Tên test mục ruỗng nhanh nhất — chúng bị đổi tên khi refactor."""
    src = "\n".join(f.read_text(encoding="utf-8")
                    for f in [SKILL] + THAM_CHIEU)
    thieu = []
    for m in re.finditer(r"`(tests/\w+\.py)::(\w+)`", src):
        f, ham = GOC / m.group(1), m.group(2)
        if not f.exists() or f"def {ham}" not in f.read_text(encoding="utf-8"):
            thieu.append(f"{m.group(1)}::{ham}")
    # Hàm nhắc tới không kèm đường dẫn file
    monkeypatch.syspath_prepend(str(GOC / "tools"))
    import duyet_repo                    # bỏ tệp tạm của test khác (BƯỚC 211, luật 4)
    for ham in ("_ten_da_nhap_va_goi",):
        if ham in src:
            co = any(f"def {ham}" in p.read_text(encoding="utf-8")
                     for p in duyet_repo.liet_ke(GOC, "tests", "*.py"))
            if not co:
                thieu.append(ham)
    assert not thieu, "skill trỏ tới test không tồn tại:\n  " + "\n  ".join(thieu)
    print("PASS  mọi test skill nhắc tới đều có thật")


def _token_nhay_nguoc(src: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"`([^`\n]{1,70})`", src)]


def _tat_ca_token_skill() -> list[str]:
    """Mọi token nháy ngược trong skill. NỔ nếu rỗng.

    Bộ trích hỏng -> 0 token -> CẢ HAI gác tên dưới đều xanh vì không có
    gì để soi. Tách thành hàm riêng CÓ CHỦ ĐÍCH: để phép chặn số 0 nằm
    thẳng trong thân test thì đột biến `assert tong` -> `assert True`
    **sống sót** (đục thử 07/09/2026), vì đường chạy êm không bao giờ
    chạm tới nó. Cùng bẫy với `va_an_toan.kiem_hoan_tra`.
    """
    ra = []
    for f in [SKILL] + THAM_CHIEU:
        ra += _token_nhay_nguoc(f.read_text(encoding="utf-8"))
    if not ra:
        raise AssertionError(
            "không trích được token nháy ngược nào từ skill — bộ trích "
            "hỏng, và hai gác tên sẽ xanh mà không kiểm gì")
    return ra


def _ten_module_test_chet(src: str, co_that) -> list[str]:
    """PHÉP PHÁN. Tên module test viết TRẦN mà không có file tương ứng.

    `co_that` là hàm `ten -> bool`, để tự chứng minh được mà không phải
    dựng file thật trên đĩa.

    Tách riêng CÓ CHỦ ĐÍCH: để phép phán nằm thẳng trong thân test thì
    đột biến `if False and ...` **sống sót** — hôm nay đục thử và nó sống
    thật, vì một gác kiểm "không có vi phạm" không phân biệt được với một
    gác kiểm gì cả khi hiện chưa có vi phạm nào.
    """
    return [t for t in _token_nhay_nguoc(src)
            if re.fullmatch(r"test_[a-z0-9_]+", t) and not co_that(t)]


def _ten_luat_chet(src: str, co_that: set) -> list[str]:
    """PHÉP PHÁN. Tên luật kebab nhắc CÙNG DÒNG với cửa Bash mà không có thật.

    Chỉ soi dòng có nhắc `cua_bash_an_toan`: một chữ kebab ở chỗ khác
    không phải tên luật, và gác kêu oan thì bị tắt (BƯỚC 31).
    """
    ra = []
    for dong in src.splitlines():
        if "cua_bash_an_toan" not in dong:
            continue
        ra += [t for t in _token_nhay_nguoc(dong)
               if re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)+", t)
               and t not in co_that]
    return ra


_XAU_TEN = [
    ("tên module test đã đổi tên",
     "bảng ghi `test_gac_da_bi_xoa_roi` là chỗ đã chặn"),
    ("tên module test gõ sai một chữ",
     "xem `test_cua_quy_trinnh` để biết thêm"),
]
_TOT_TEN = [
    ("tên module test có thật", "khoá bởi `test_cua_quy_trinh`"),
    ("đường dẫn đầy đủ, gác khác lo", "xem `tests/test_cua_quy_trinh.py`"),
    ("chữ thường bình thường, không phải tên test", "chạy `pytest` là xong"),
]

_XAU_LUAT = [
    ("tên luật đã đổi", "`cua_bash_an_toan` `pytest-qua-ong-da-doi-ten`"),
    ("tên luật bịa", "chặn bởi `cua_bash_an_toan` `luat-khong-co-that`"),
]
_TOT_LUAT = [
    ("tên luật có thật", "`cua_bash_an_toan` `hai-heredoc`"),
    ("kebab ở dòng KHÁC, không phải tên luật",
     "xem `references/loi-da-mac.md` và `mot-chu-kebab-bat-ky`"),
    ("dòng có cửa Bash nhưng không có kebab nào",
     "`tools/cua_bash_an_toan.py` là PreToolUse"),
]


def test_SAN_chong_vacuity_NO_khi_khong_trich_duoc_gi(tmp_path, monkeypatch):
    """Lưới chống-xanh-giả phải tự chứng minh, không chỉ tồn tại."""
    rong = tmp_path / "rong.md"
    rong.write_text("khong co token nao ca\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "SKILL", rong)
    monkeypatch.setattr(sys.modules[__name__], "THAM_CHIEU", [])
    try:
        _tat_ca_token_skill()
    except AssertionError:
        print("PASS  0 token -> nổ, không xanh giả")
        return
    raise AssertionError("không trích được token nào mà vẫn im lặng")


def test_MAY_DO_ten_tu_chung_minh_no_bat_duoc():
    """Mẫu đã biết là xấu phải bị bắt; mẫu đã biết là tốt phải được tha.

    Không có phần này thì hai gác dưới chỉ chứng minh được rằng **hôm nay
    chưa có vi phạm** — không chứng minh được rằng chúng bắt được vi phạm.
    """
    co = {"test_cua_quy_trinh", "test_skill_quy_trinh"}
    for ten, src in _XAU_TEN:
        assert _ten_module_test_chet(src, co.__contains__), f"BỎ SÓT: {ten}"
    for ten, src in _TOT_TEN:
        assert not _ten_module_test_chet(src, co.__contains__), f"KÊU OAN: {ten}"

    luat = {"hai-heredoc", "pytest-qua-ong"}
    for ten, src in _XAU_LUAT:
        assert _ten_luat_chet(src, luat), f"BỎ SÓT: {ten}"
    for ten, src in _TOT_LUAT:
        assert not _ten_luat_chet(src, luat), f"KÊU OAN: {ten}"

    print(f"PASS  bắt {len(_XAU_TEN) + len(_XAU_LUAT)} xấu, "
          f"tha {len(_TOT_TEN) + len(_TOT_LUAT)} tốt")


def test_moi_TEN_MODULE_TEST_tran_deu_co_that():
    """Tên module test viết TRẦN — không đuôi `.py`, không đường dẫn.

    `test_moi_file_skill_nhac_toi_deu_CO_THAT` ở trên chỉ bắt dạng có đuôi
    (`tests/x.py`). Bảng trong `references/loi-da-mac.md` lại viết trần —
    ví dụ tên module của gác phụ-thuộc-thứ-tự — nên năm cái tên như thế
    đang LỌT: đổi tên một file test là bảng trỏ vào hư không, im lặng.

    Đo 07/09/2026: 5 tên trần trong ba file skill, cả 5 đều có thật. Gác
    này khoá con số 0 chỗ chết, KHÔNG khoá con số 5.
    """
    def _co(t):
        return (GOC / "tests" / f"{t}.py").exists()

    tong = len(_tat_ca_token_skill())      # nổ nếu bộ trích hỏng
    thieu = []
    for f in [SKILL] + THAM_CHIEU:
        thieu += [f"{f.name} -> {t}" for t in
                  _ten_module_test_chet(f.read_text(encoding="utf-8"), _co)]
    assert not thieu, ("skill nhắc tên module test không tồn tại:\n  "
                       + "\n  ".join(thieu))
    print(f"PASS  {tong} token nháy ngược · mọi tên module test đều có thật")


def test_moi_TEN_LUAT_cua_bash_nhac_toi_deu_co_that():
    """Tên luật trong `tools/cua_bash_an_toan.py` cũng mục ruỗng được.

    Bảng lỗi ghi tên luật để chỉ ra luật nào đã chặn lỗi nào. Đổi tên luật
    thì cột "đã chặn bằng" thành vô nghĩa mà không gì kêu.

    Chỉ soi token kebab nằm CÙNG DÒNG với tên module cửa Bash — một chữ
    kebab ở chỗ khác không phải tên luật, và một gác kêu oan thì bị tắt
    (`docs/STATE.md` BƯỚC 31).
    """
    sys.path.insert(0, str(GOC / "tools"))
    import cua_bash_an_toan as cb

    co_that = {ten for ten, _, _ in cb.LUAT}
    assert co_that, "LUAT rỗng — gác này thành vô nghĩa"
    thieu = []
    for f in [SKILL] + THAM_CHIEU:
        thieu += [f"{f.name}: {t!r}" for t in
                  _ten_luat_chet(f.read_text(encoding="utf-8"), co_that)]
    assert not thieu, (
        f"skill nhắc tên luật không có trong LUAT: {thieu}\n"
        f"Luật đang có: {sorted(co_that)}")
    print(f"PASS  tên luật nhắc trong skill đều có trong LUAT "
          f"({len(co_that)} luật)")


CAC_CONG = ("-m pytest tests/", "tools/kiem_cu_phap_311.py",
            "tools/chan_bia_so_lieu.py --quet-repo",
            "tools/kiem_test_chay_rieng.py")


def test_bon_cong_gac_dung_thu_tu_va_dung_ten():
    """Thứ tự là bắt buộc: có test ghi thư mục tạm vào GỐC REPO, nên hai
    tiến trình pytest cùng lúc cho đỏ giả.

    Cổng thứ tư thêm 07/09/2026 (`docs/STATE.md` BƯỚC 34). Danh sách ghim
    ở `CAC_CONG` chứ không viết thẳng trong thân test: để thân test tự
    dựng lại danh sách thì đột biến "bỏ một cổng" sống sót.
    """
    src = SKILL.read_text(encoding="utf-8")
    thu_tu = [src.find(x) for x in CAC_CONG]
    thieu = [c for c, i in zip(CAC_CONG, thu_tu) if i < 0]
    assert not thieu, f"skill thiếu cổng gác: {thieu}"
    assert thu_tu == sorted(thu_tu), (
        f"cổng gác sai thứ tự trong skill: "
        f"{[c for _, c in sorted(zip(thu_tu, CAC_CONG))]}")
    print(f"PASS  {len(CAC_CONG)} cổng gác, đúng thứ tự")


def test_skill_NHAC_hai_quy_tac_dung_dau():
    """Quy tắc 2 thêm 07/09/2026 và nó là quy tắc duy nhất chống được lỗi
    ước lượng — thứ không phép đo nào bắt được, chỉ thói quen bắt được."""
    src = SKILL.read_text(encoding="utf-8").lower()
    # so KHÔNG phân biệt hoa thường: luật là NỘI DUNG, không phải cách viết
    # hoa. Ghim đúng chữ hoa sẽ đỏ vì một câu viết lại cho xuôi tai.
    assert "con số đẹp lên đáng kể" in src, "skill bỏ Quy tắc số 1"
    assert "không có lệnh thì không có số" in src, "skill bỏ Quy tắc số 2"
    print("PASS  skill giữ cả hai quy tắc đứng đầu")


def test_CHI_CO_MOT_skill_quy_trinh():
    """Hai skill cùng tự nhận là quy trình hiện hành = lỗi kinh điển ở đây.

    `docs/STATE.md` BƯỚC 33 và 34 đều là biến thể của "hai chỗ nói về cùng
    một thứ, một chỗ đã hết đúng". Một skill thừa còn tệ hơn, vì nó được
    nạp TỰ ĐỘNG.

    BƯỚC 244: repo có thêm skill ĐỌC MỘT LĨNH VỰC (`dow-theory-analysis`).
    Luật nới đúng một nấc: skill nào không phải quy trình phải được khai trong
    `cua_mo_phien.SKILL_PHU` (danh sách đóng); phần còn lại vẫn phải là ĐÚNG
    MỘT skill quy trình. Skill mới chưa khai thì test này đỏ.
    """
    import cua_mo_phien as mp
    ds = sorted(p.parent.name for p in THU_MUC_SKILL.glob("*/SKILL.md"))
    quy_trinh = [t for t in ds if t not in mp.SKILL_PHU]
    assert quy_trinh == ["quy-trinh-lam-viec"], (
        f"skill chưa khai là phụ và không phải quy trình duy nhất: {quy_trinh}")
    assert set(mp.SKILL_PHU) <= set(ds), (
        f"SKILL_PHU khai skill không có trên đĩa: {sorted(set(mp.SKILL_PHU) - set(ds))}")
    # bản tin mở phiên chỉ được gọi skill QUY TRÌNH là bắt buộc
    assert mp.ten_skill() == quy_trinh
    print(f"PASS  đúng một skill quy trình: {quy_trinh[0]}; skill phụ: {list(mp.SKILL_PHU)}")


#: Câu sai đã bị báo cáo nghiên cứu 29/10/2026 bác khỏi bản nháp của người dùng
#: (BƯỚC 244; `docs/thiet-ke-dow-cau-truc.md` mục 12). Skill phụ mà chép lại là
#: đưa ngược lỗi đã sửa. Cố ý tìm CHUỖI NGUYÊN VĂN của bản nháp.
CAU_DA_BAC = {
    "dow-theory-analysis": (
        "T+2.5",            # chu kỳ thanh toán không có nguồn nào ghi
        "20% – 30%", "20%–30%",     # "phần con sóng mới đã đi mất": không nguồn
        "2 – 6 tuần", "2–6 tuần",   # độ dài con sóng ở VN: không có phép đo nào
        "độ tin cậy cao nhất",      # xếp hạng "failure swing": không có nguồn gốc
        "tương đương vùng",         # "1/3–2/3 = vùng Fibonacci": sai số học
    ),
}


def _skill_phu():
    import cua_mo_phien as mp
    return list(mp.SKILL_PHU)


@pytest.mark.parametrize("ten", _skill_phu())
def test_SKILL_PHU_frontmatter_hop_le_va_khong_tu_nhan_la_quy_trinh(ten):
    duong = THU_MUC_SKILL / ten / "SKILL.md"
    assert duong.exists(), f"SKILL_PHU khai {ten} nhưng không có {duong}"
    src = duong.read_text(encoding="utf-8")
    assert src.startswith("---\n"), "thiếu frontmatter YAML"
    fm = src.split("---", 2)[1]
    t = re.search(r"^name:\s*(\S+)", fm, re.M)
    mo = re.search(r"^description:\s*(.+)", fm, re.M)
    assert t and mo, "frontmatter thiếu name hoặc description"
    assert t.group(1) == ten, f"name {t.group(1)!r} khác tên thư mục {ten!r}"
    assert "<" not in fm and ">" not in fm, "frontmatter không được có < >"
    assert len(mo.group(1)) > 60, "description quá ngắn để làm điều kiện kích hoạt"
    mota = mo.group(1).lower()
    assert "bắt buộc" not in mota, (
        "skill phụ tự nhận BẮT BUỘC trong description — đó là nhãn riêng của "
        "skill quy trình")
    assert "không dùng" in mota, (
        "description phải nêu rõ KHÔNG dùng cho việc gì, để không tranh kích hoạt "
        "với các skill SMC / Wyckoff của người dùng")
    print(f"PASS  skill phụ {ten}: frontmatter hợp lệ, không tự nhận là quy trình")


@pytest.mark.parametrize("ten", _skill_phu())
def test_SKILL_PHU_khong_chep_lai_cau_da_bi_bac(ten):
    src = (THU_MUC_SKILL / ten / "SKILL.md").read_text(encoding="utf-8")
    cam = CAU_DA_BAC.get(ten)
    assert cam, f"skill phụ {ten} chưa khai CAU_DA_BAC (có thể là rỗng có lý do)"
    co = [c for c in cam if c in src]
    assert not co, f"skill {ten} chép lại câu đã bị bác: {co}"
    print(f"PASS  skill phụ {ten}: vắng {len(cam)} câu đã bị bác")


def test_skill_NHAC_ranh_gioi_khong_dat_lenh_that():
    """Ranh giới nặng nhất của dự án. Skill mà bỏ nó thì skill sai."""
    src = SKILL.read_text(encoding="utf-8")
    assert "Không đặt lệnh thật" in src, "skill không nhắc ranh giới đặt lệnh"
    # Ca 6 lan chu `main` va 3 lan `PR` deu nam trong khoi "Buoc 5 — Giao",
    # nen go khoi ay ra thi phep kiem nay DO. Duc thu 12/09/2026: 1/1 do.
    # van-ban-ok: SKILL.md la markdown, va suc phan biet DA DUOC DO
    assert "main" in src and "PR" in src, "skill không nhắc luật nhánh/PR"
    print("PASS  skill giữ ranh giới đặt lệnh và luật nhánh")


# ── Ví dụ lệnh trong skill phải CHẠY ĐƯỢC (BƯỚC 183, lỗi 171) ─────────────
#
# `SKILL.md` Bước 2–3 và docstring của `tools/va_an_toan.py` dạy hai lời gọi
# `thay()` / `dot_bien()`. Cả hai ví dụ chết ngay từ ngày viết (07/09/2026,
# `2c88dfe`) và sống 35 ngày: neo `N_TOI_THIEU = 113` chưa từng có trong mã
# (đó là giá trị SUY RA: `round(N_DAY_DU / 4)`), neo `z=2,30` khớp HAI lần và
# cả hai nằm trong chú thích — nên kể cả sửa cho khớp một lần thì đột biến
# cũng không đổi hành vi nào. `test_moi_file_skill_nhac_toi_deu_CO_THAT` chỉ
# kiểm TÊN file, không kiểm ví dụ có chạy được hay không.
#
# GIỚI HẠN, khai thẳng (lỗi 44): "AST đổi" là điều kiện CẦN, không phải
# ĐỦ. Gác chỉ chặn neo nằm trọn trong chú thích hoặc docstring; một neo nằm
# trong một chuỗi thông báo vẫn qua. Nó cũng KHÔNG chạy pytest.

#: Số lời gọi tối thiểu gác phải soi được: hai trong SKILL.md (Bước 2, Bước 3)
#: và hai trong docstring của `va_an_toan.py`. Dưới mức này là bộ trích hỏng.
SAN_VI_DU = 4


def _khoi_python_trong_md(src: str) -> list[str]:
    return re.findall(r"```python\n(.*?)\n```", src, re.S)


def _khoi_cach_dung_trong_docstring(src_py: str) -> list[str]:
    """Khối mã thụt lề sau dòng `CÁCH DÙNG` trong docstring module."""
    import ast
    import textwrap

    doc = ast.get_docstring(ast.parse(src_py)) or ""
    moc = doc.find("CÁCH DÙNG")
    return [textwrap.dedent(doc[moc:].split("\n", 1)[1])] if moc >= 0 else []


def _ast_khong_docstring(src: str) -> str:
    """`ast.dump` của file, bỏ docstring: chú thích vốn không vào AST."""
    import ast

    cay = ast.parse(src)
    for nut in ast.walk(cay):
        if isinstance(nut, (ast.Module, ast.ClassDef, ast.FunctionDef,
                            ast.AsyncFunctionDef)):
            dau = nut.body[0] if nut.body else None
            if (isinstance(dau, ast.Expr) and isinstance(dau.value, ast.Constant)
                    and isinstance(dau.value.value, str)):
                nut.body = nut.body[1:] or [ast.Pass()]
    return ast.dump(cay)


def _vi_du_lenh_chet(khoi: str, goc: Path) -> tuple[int, list[str]]:
    """PHÉP PHÁN. Mỗi lời gọi `thay()` / `dot_bien()` trong `khoi` phải chạy được.

    Trả `(số lời gọi đã soi, danh sách lỗi)`. Chạy được nghĩa là: file có;
    neo khớp ĐÚNG MỘT lần (luật của `va_an_toan`); với file `.py`, thay neo
    làm file vẫn parse được và làm AST (bỏ docstring) ĐỔI; với `dot_bien`,
    file test nêu trong `lenh` có thật. Tách riêng khỏi thân test để đục
    thử được phép phán (cùng lý do `_ten_module_test_chet`).
    """
    import ast

    try:
        cay = ast.parse(khoi)
    except SyntaxError as e:
        return 0, [f"khối python không parse được: {e.msg}"]
    dem, loi = 0, []
    for nut in ast.walk(cay):
        if not (isinstance(nut, ast.Call) and isinstance(nut.func, ast.Name)
                and nut.func.id in ("thay", "dot_bien")):
            continue
        ten = nut.func.id
        chuoi = [a.value for a in nut.args
                 if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        if len(chuoi) < 3:
            continue       # mẩu mã minh hoạ lỗi cũ (biến, không hằng) — không phải ví dụ
        dem += 1
        duong, cu, moi = chuoi[:3]
        p = goc / duong
        if not p.is_file():
            loi.append(f"{ten}({duong!r}): file không có")
            continue
        src = p.read_text(encoding="utf-8")
        if src.count(cu) != 1:
            loi.append(f"{ten}({duong!r}): neo {cu!r} khớp {src.count(cu)} lần, "
                       f"phải đúng 1")
            continue
        if duong.endswith(".py"):
            try:
                doi = (_ast_khong_docstring(src.replace(cu, moi, 1))
                       != _ast_khong_docstring(src))
            except SyntaxError:
                loi.append(f"{ten}({duong!r}): thay neo làm file không parse được")
                continue
            if not doi:
                loi.append(f"{ten}({duong!r}): neo {cu!r} chỉ nằm trong chú thích "
                           f"hoặc docstring — đột biến không đổi hành vi")
        if ten == "dot_bien" and len(nut.args) > 3 and isinstance(nut.args[3], ast.List):
            for a in nut.args[3].elts:
                if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                        and a.value.endswith(".py") and not (goc / a.value).is_file()):
                    loi.append(f"dot_bien({duong!r}): file test {a.value!r} không có")
    return dem, loi


def _soi_tat_ca_vi_du(khoi: list[str], goc: Path) -> list[str]:
    """Soi mọi khối; NỔ nếu soi được ít hơn `SAN_VI_DU` lời gọi.

    Tách khỏi thân test CÓ CHỦ ĐÍCH (cùng `_tat_ca_token_skill`): để phép chặn
    số 0 nằm trong thân test thì đột biến "bỏ sàn" sống sót, vì đường chạy
    êm không bao giờ chạm tới nó (đục thử 12/10/2026: 1/13 sống).
    """
    dem, loi = 0, []
    for k in khoi:
        n, l = _vi_du_lenh_chet(k, goc)
        dem += n
        loi += l
    if dem < SAN_VI_DU:
        raise AssertionError(
            f"chỉ soi được {dem} lời gọi (sàn {SAN_VI_DU}) — bộ trích hỏng, "
            f"và gác sẽ xanh mà không kiểm gì")
    return loi


_VI_DU_XAU = [
    ("neo không có thật",
     {"m.py": "X = 1\n"}, 'thay("m.py", "X = 9", "X = 2")'),
    ("neo khớp hai lần",
     {"m.py": "A = 1\nB = 1\n"}, 'thay("m.py", "= 1", "= 2")'),
    ("neo chỉ nằm trong chú thích (đúng ca z=2,30 cũ)",
     {"m.py": "# Z = 2.3\nY = 1\n"}, 'thay("m.py", "Z = 2.3", "Z = 1.0")'),
    ("neo chỉ nằm trong docstring",
     {"m.py": '"""Z = 2.3"""\nY = 1\n'}, 'thay("m.py", "Z = 2.3", "Z = 1.0")'),
    ("file không có", {}, 'thay("khong_co.py", "a", "b")'),
    ("thay neo làm file hết parse được",
     {"m.py": "X = 1\n"}, 'thay("m.py", "X = 1", "X = (")'),
    ("dot_bien trỏ tới file test không có",
     {"m.py": "X = 1\n"},
     'dot_bien("m.py", "X = 1", "X = 2", ["-m", "pytest", "tests/khong_co.py"])'),
]
_VI_DU_TOT = [
    ("neo thật, đổi hành vi", {"m.py": "X = 1\n"},
     'thay("m.py", "X = 1", "X = 2")'),
    ("neo thật, file có docstring ở chỗ khác", {"m.py": '"""doc"""\nX = 1\n'},
     'thay("m.py", "X = 1", "X = 2")'),
    ("neo nằm trong lời gọi hàm (đổi chuỗi hằng là đổi AST)",
     {"m.py": 'print("a")\n'}, 'thay("m.py", \'print("a")\', \'print("b")\')'),
    ("dot_bien với file test có thật",
     {"m.py": "X = 1\n", "tests/t.py": "pass\n"},
     'dot_bien("m.py", "X = 1", "X = 2", ["-m", "pytest", "tests/t.py", "-q"])'),
]


def test_VI_DU_gac_tu_chung_minh_bat_dung_hinh_dang_chet(tmp_path):
    """Mẫu đã biết là chết phải bị bắt; mẫu đã biết là sống phải được tha.

    Không có phần này thì `test_VI_DU_neo_chay_duoc` chỉ chứng minh được
    rằng HÔM NAY hai ví dụ chạy được — không chứng minh gác bắt được ví dụ
    chết (một gác kiểm "không có vi phạm" không phân biệt được với một gác
    kiểm gì cả, lỗi 34).
    """
    def _chay(tep, khoi):
        for ten, nd in tep.items():
            (tmp_path / ten).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / ten).write_text(nd, encoding="utf-8")
        return _vi_du_lenh_chet(khoi, tmp_path)

    for ten, tep, khoi in _VI_DU_XAU:
        dem, loi = _chay(tep, khoi)
        assert loi, f"BỎ SÓT: {ten}"
    for ten, tep, khoi in _VI_DU_TOT:
        dem, loi = _chay(tep, khoi)
        assert dem == 1 and not loi, f"KÊU OAN: {ten}: {loi}"
    assert _vi_du_lenh_chet("x = 1\n", tmp_path) == (0, [])
    # mẩu minh hoạ lỗi cũ dùng biến, không dùng hằng: bỏ qua, KHÔNG đếm vào sàn
    assert _vi_du_lenh_chet('dot_bien(F, cu, moi, BO)', tmp_path) == (0, [])
    assert SAN_VI_DU == 4, "hạ sàn là một quyết định, không phải một lần sửa lặng lẽ"
    try:
        _soi_tat_ca_vi_du([], tmp_path)
    except AssertionError:
        pass
    else:
        raise AssertionError("không soi được lời gọi nào mà vẫn im lặng")
    print(f"PASS  bắt {len(_VI_DU_XAU)} ví dụ chết, tha {len(_VI_DU_TOT)} ví dụ sống")


def test_VI_DU_neo_chay_duoc():
    """Ví dụ `thay()` / `dot_bien()` trong skill và trong `va_an_toan.py` phải
    chạy được trên mã HIỆN HÀNH — neo có thật, đúng một lần, đổi hành vi."""
    khoi = []
    for f in [SKILL] + THAM_CHIEU:
        khoi += _khoi_python_trong_md(f.read_text(encoding="utf-8"))
    khoi += _khoi_cach_dung_trong_docstring(
        (GOC / "tools" / "va_an_toan.py").read_text(encoding="utf-8"))
    loi = _soi_tat_ca_vi_du(khoi, GOC)       # nổ nếu bộ trích hỏng
    assert not loi, "ví dụ trong skill không chạy được:\n  " + "\n  ".join(loi)
    print(f"PASS  mọi ví dụ thay()/dot_bien() đều chạy được trên mã hiện hành "
          f"({len(khoi)} khối python)")


# ── `description` không được mang hình dạng làm YAML đọc khác dòng thô ────
#
# Nguồn: `CHANGELOG.md:39` của `mattpocock/skills` (#911) — một `: ` không
# nháy trong `description` làm khối frontmatter thành YAML sai và công cụ
# nạp skill BỎ QUA sáu skill, không lỗi. `test_skill_ton_tai_va_frontmatter_hop_le`
# in "frontmatter hợp lệ" mà chỉ so bằng regex. Không `import yaml`: PyYAML
# không nằm trong `requirements.txt`, và `tests/test_cua_so_du_lieu_quet.py`
# đã ghi một lần xanh-ở-máy-đỏ-trên-CI vì đúng việc ấy.

def _mo_ta_yaml_hong(gia_tri: str) -> str | None:
    """PHÉP PHÁN. Lý do `gia_tri` (không nháy) bị YAML đọc khác dòng thô, hoặc None."""
    g = gia_tri.strip()
    if g[:1] in ('"', "'"):
        return None                       # có nháy: YAML đọc theo nháy
    if ": " in g or g.endswith(":"):
        return "dấu ':' + khoảng trắng trong giá trị không nháy"
    if " #" in g:
        return "' #' mở chú thích YAML — phần sau bị cắt"
    if g[:1] and g[:1] in "!&*[]{}|>%@`":
        return f"ký tự đầu {g[:1]!r} là ký hiệu YAML"
    return None


def test_MO_TA_frontmatter_khong_mang_hinh_dang_lam_YAML_hong():
    xau = ["Dung khi: viet gac", "Dung khi viet gac # ghi chu", "*dung* khi viet",
           "Chu ky:", "[a, b] la danh sach"]
    tot = ["Quy trinh bat buoc - doc, sua, them test", '"Dung khi: da quote"',
           "Cau co dau phay, dau gach - va (ngoac)"]
    for g in xau:
        assert _mo_ta_yaml_hong(g), f"BỎ SÓT: {g!r}"
    for g in tot:
        assert not _mo_ta_yaml_hong(g), f"KÊU OAN: {g!r}"
    fm = SKILL.read_text(encoding="utf-8").split("---", 2)[1]
    mo_ta = re.search(r"^description:\s*(.+)", fm, re.M)
    assert mo_ta, "frontmatter thiếu description"
    ly_do = _mo_ta_yaml_hong(mo_ta.group(1))
    assert ly_do is None, f"description của skill: {ly_do}"
    print("PASS  description không mang hình dạng làm YAML đọc sai")


# ── Bảng cửa trong skill phải phủ MỌI hook đã khai (BƯỚC 183, lỗi 172) ─────
#
# `SKILL.md` mục "Cửa tự động" nói BẢY cửa nhưng bảng chỉ có sáu hàng: thiếu
# `tools/cua_ho_so.py`, hook thứ bảy, đã khai ở `docs/cua-du-an.json` từ khi
# nó ra đời. `tools/kiem_cua_song.py` so bản khai với `~/.claude/settings.json`
# (không có trên CI); không gác nào so bản khai với BẢNG NGƯỜI ĐỌC.

#: Số hook đã khai (đo 12/10/2026 ở `docs/cua-du-an.json`). Sàn chống bộ đọc
#: hỏng: đọc ra ít hơn thì NỔ chứ không "sạch". Thêm hook thì nâng sàn có chủ đích.
SAN_CUA = 7


def _cua_thieu_trong_bang(hooks: dict, bang: str, san: int | None = None) -> list[str]:
    """PHÉP PHÁN. Tên script hook đã khai mà `bang` không nhắc tới.

    NỔ nếu đọc được ít hơn `san` (mặc định `SAN_CUA`) hook.
    """
    lenh = [h.get("command", "") for nhom in hooks.values() for muc in nhom
            for h in muc.get("hooks", [])]
    if len(lenh) < (SAN_CUA if san is None else san):
        raise AssertionError(f"chỉ đọc được {len(lenh)} hook — bộ đọc hỏng")
    ten = sorted({m for c in lenh for m in re.findall(r"tools/(\w+\.py)", c)})
    return [t for t in ten if t not in bang]


def test_BANG_CUA_trong_SKILL_phu_du_moi_hook_da_khai():
    import json

    # máy đo tự chứng minh: thiếu một hàng thì phải bị bắt, đủ thì được tha
    mau = {"Stop": [{"hooks": [{"command": 'python "x/tools/a_cua.py"'},
                               {"command": 'python "x/tools/b_cua.py" --co'}]}]}
    assert _cua_thieu_trong_bang(mau, "| `tools/a_cua.py` | Stop |", san=2) == ["b_cua.py"]
    assert _cua_thieu_trong_bang(mau, "tools/a_cua.py tools/b_cua.py", san=2) == []
    assert SAN_CUA == 7, "hạ sàn là một quyết định, không phải một lần sửa lặng lẽ"
    try:
        _cua_thieu_trong_bang({}, "bất kỳ")
    except AssertionError:
        pass
    else:
        raise AssertionError("đọc được 0 hook mà vẫn im lặng")

    khai = json.loads((GOC / "docs" / "cua-du-an.json").read_text(encoding="utf-8"))
    hooks = khai["hooks"]
    src = SKILL.read_text(encoding="utf-8")
    bang = src.split("## Cửa tự động", 1)[1].split("\n## ", 1)[0]
    thieu = _cua_thieu_trong_bang(hooks, bang)
    assert not thieu, ("bảng 'Cửa tự động' trong SKILL.md thiếu hook đã khai ở "
                       f"docs/cua-du-an.json: {thieu}")
    print("PASS  bảng cửa trong skill phủ mọi hook đã khai")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
