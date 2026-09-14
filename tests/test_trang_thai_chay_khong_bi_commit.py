"""Gác: trạng thái chạy — `*.db`, `backtest/cache*/`, bộ nhớ hậu nghiệm —
không được nằm trong INDEX của git.

VÌ SAO CÓ FILE NÀY
──────────────────
Ngày 12/08/2026 commit `e2f98b4` ghi đè `paper_trades.db` bằng kết quả
backtest in-sample: **96/113 lệnh thật biến mất**, vị thế ACB đang mở bị
xoá. Đó là sự cố nặng nhất lịch sử dự án.

Nguyên nhân để file ấy **có thể** bị commit nằm ngay trong `.gitignore`, và
chính file đó ghi lại: *"Trước đây chỉ chặn `paper_custom*.db` nên
`paper_trades.db` lọt qua"*. Một luật che đúng vào ngày nó ra đời, và sai
vào ngày có một cái tên khác.

Ba hàng rào đã dựng sau sự cố đều nằm ở tầng **ứng dụng**:
`PaperTradingJournal.__init__` mặc định từ chối, `guard_not_real_ledger()`,
`avg_capital_deployed_pct` kêu khi đòn bẩy ẩn. **Không cái nào canh cái
INDEX.** Và `.gitignore` KHÔNG bảo vệ một file đã được theo dõi — thêm một
lần `git add -f`, hay một dòng luật bị thu hẹp, là đủ.

Bên BÍ MẬT đã có gác từ 03/09/2026 (`tests/test_bi_mat_bi_che.py`), cùng
cơ chế, cùng lỗ. Bên SỔ LỆNH thì chưa bao giờ — tới 14/09/2026.

HAI CÂU HỎI KHÁC NHAU, PHẢI HỎI CẢ HAI
──────────────────────────────────────
1. **Index có sạch không** — `git ls-files`. Trả lời "hôm nay có gì lọt".
2. **Luật che có còn sống không** — `git check-ignore --no-index`. Trả lời
   "ngày mai có lọt được không".

Câu 1 một mình thì xanh suốt cho tới đúng cái commit làm hỏng. Câu 2 một
mình thì mù với file đã lọt từ trước.

Hỏi GIT, đừng đọc lại `.gitignore` rồi tự diễn giải — dựng lại luật của
git trong test là kiểm công thức của test, không kiểm hành vi của git.
Cùng luật với `tests/test_bi_mat_bi_che.py`.

ĐIỀU NÀY KHÔNG ĐÒI XOÁ FILE
───────────────────────────
17 file `.db` đang nằm ở gốc repo là **dữ liệu đo của người dùng**, và
`CLAUDE.md` cấm xoá chúng. Gác này hỏi về INDEX, không hỏi về đĩa.
"""
import subprocess
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent

#: Những đường dẫn phải bị che, kèm LÝ DO. Tên file thật trong lịch sử dự
#: án, không phải tên bịa: `paper_trades.db` là file bị ghi đè ngày 12/08,
#: `paper_custom20loop_18m_loop_11.db` là sổ in-sample đã nạp đè lên nó.
PHAI_BI_CHE = [
    ("paper_trades.db", "so lenh THAT — file bi ghi de ngay 12/08/2026"),
    ("paper_custom20loop_18m_loop_11.db", "so in-sample da nap de len no"),
    ("paper_trades_seeded_insample.db", "ban da doi ten sau su co"),
    ("backtest/cache/VNINDEX.csv", "cache gia — ban neo tai lap"),
    ("backtest/cache_2018/FPT.csv", "cache cua DO 4, tro bang VIBE_CACHE_DIR"),
    ("sl_pattern_memory.json", "bo nho hau nghiem — trang thai chay"),
]

#: Mẫu `git ls-files` và tên gọi người đọc được.
KHONG_DUOC_THEO_DOI = [
    ("*.db", "file so lenh"),
    ("backtest/cache*", "cache du lieu"),
    ("sl_pattern_memory.json", "bo nho hau nghiem"),
]


def _git_o(thu_muc: Path, *tham_so: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *tham_so], cwd=str(thu_muc),
                          capture_output=True, text=True)


def _git(*tham_so: str) -> subprocess.CompletedProcess:
    return _git_o(GOC, *tham_so)


def git_theo_doi(mau: str) -> list[str]:
    """File khớp `mau` mà GIT đang theo dõi. Git trả lời, không phải ta."""
    r = _git("ls-files", "--", mau)
    assert r.returncode == 0, (
        f"`git ls-files -- {mau}` thất bại: {r.stderr.strip()}. "
        f"CHƯA KIỂM ĐƯỢC không phải SẠCH.")
    return [d for d in r.stdout.splitlines() if d.strip()]


def bi_che(duong_dan: str, thu_muc: Path = GOC) -> bool:
    """`--no-index` là BẮT BUỘC.

    Thiếu nó, `git check-ignore` **bỏ qua file đang được theo dõi** và trả
    "không bị che" bất kể luật viết gì — nên câu trả lời sẽ nói về tình
    trạng theo dõi chứ không nói về luật. Bài học đã ghi ở
    `tests/test_bi_mat_bi_che.py`.

    `thu_muc` mở ra để phép đục thử đi qua ĐÚNG hàm này trên một repo
    dựng riêng — xem `test_KHONG_INDEX_la_BAT_BUOC…`. Trên repo thật
    chưa file nào lọt index, nên ở đó cờ ấy chưa canh được gì.
    """
    return _git_o(thu_muc, "check-ignore", "--no-index", "-q",
                  duong_dan).returncode == 0


# ───────────────── câu 1: index hôm nay có sạch không ─────────────────

@pytest.mark.parametrize("mau,ten", KHONG_DUOC_THEO_DOI)
def test_KHONG_trang_thai_chay_nao_nam_trong_index(mau, ten):
    """Sự cố 12/08/2026 bắt đầu bằng đúng một dòng như thế trong index."""
    lot = git_theo_doi(mau)
    assert not lot, (
        f"{len(lot)} {ten} ĐANG bị git theo dõi: {lot[:5]}\n"
        f"Đây là đường đi của sự cố 12/08/2026 (96/113 lệnh thật biến mất).\n"
        f"Gỡ khỏi index bằng `git rm --cached`, ĐỪNG xoá file trên đĩa — "
        f"đó là dữ liệu đo của người dùng.")


def test_MAY_DO_tu_chung_minh_no_bat_duoc():
    """Không có phép kiểm này thì ba phép trên xanh cả khi nó không hỏi gì.

    Một lỗi gõ trong lời gọi `git ls-files` cho ra danh sách rỗng, và rỗng
    thì mọi `assert not lot` đều qua. Đục thử đi qua ĐÚNG hàm đang phán:
    hỏi nó một mẫu chắc chắn CÓ, và đòi nó trả về khác rỗng.
    """
    co = git_theo_doi("*.py")
    assert len(co) > 50, (
        f"`git ls-files -- *.py` chỉ thấy {len(co)} file — máy đo đang hỏng "
        f"hoặc hỏi sai chỗ, nên ba phép kiểm index ở trên KHÔNG kiểm gì.")


# ───────────────── câu 2: luật che ngày mai còn sống không ─────────────

@pytest.mark.parametrize("duong_dan,ly_do", PHAI_BI_CHE)
def test_moi_duong_trang_thai_chay_deu_BI_CHE(duong_dan, ly_do):
    """Dựng lại NGUYÊN VĂN lỗi lịch sử.

    `.gitignore` từng chỉ có `paper_custom*.db`, nên `paper_trades.db` —
    tên không khớp mẫu ấy — lọt qua và bị commit. Thu `*.db` về một mẫu
    hẹp hơn sẽ làm đúng dòng `paper_trades.db` ở đây đỏ.
    """
    assert bi_che(duong_dan), (
        f"`{duong_dan}` KHÔNG bị git che — {ly_do}.\n"
        f"Kiểm bằng: git check-ignore -v --no-index {duong_dan}")


def test_BAN_MAU_va_MA_NGUON_van_commit_duoc():
    """Gác chặt tay quá thì người ta gỡ nó, nên phải chứng minh nó không
    che nhầm thứ PHẢI được commit."""
    for duong_dan in (".streamlit/secrets.toml.example",
                      "paper_metrics.py", "backtest/__init__.py"):
        assert not bi_che(duong_dan), (
            f"`{duong_dan}` bị che nhầm — luật trong `.gitignore` đang rộng "
            f"hơn chủ đích và sẽ giấu mất thành phần thật.")


def test_KHONG_INDEX_la_BAT_BUOC__chung_minh_trong_mot_repo_rieng(tmp_path):
    """Đục thử bỏ `--no-index` SỐNG SÓT ở lượt đầu (14/09/2026).

    Nó sống sót vì đúng một lý do: trên repo này chưa file nào lọt vào
    index, nên hai câu hỏi đang cho cùng câu trả lời. Tức hôm nay cờ ấy
    **chưa canh gì** — và một phát sống sót là một câu trả lời, không phải
    "gần đạt".

    Chỗ nó canh chỉ xuất hiện khi file ĐÃ bị theo dõi, tức đúng lúc gác
    này cần nói thật nhất. Dựng lại tình huống ấy trong một repo riêng ở
    thư mục tạm — không đụng repo thật.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git_o(repo, "init", "-q").returncode == 0, "khong dung duoc repo thu"
    (repo / ".gitignore").write_text("*.db\n", encoding="utf-8")
    (repo / "so.db").write_text("x", encoding="utf-8")
    # `-f` la duong duy nhat dua mot file da bi che vao index — va dung la
    # duong su co 12/08/2026 di qua.
    assert _git_o(repo, "add", "-f", "so.db").returncode == 0

    # Đi qua ĐÚNG hàm đang phán, không dựng lại lời gọi git ở đây.
    khong = _git_o(repo, "check-ignore", "-q", "so.db").returncode

    assert bi_che("so.db", repo), (
        "CÓ `--no-index`: git phải trả lời về LUẬT, và luật `*.db` nói là che")
    assert khong == 1, (
        "KHÔNG có `--no-index`: git bỏ qua file đang được theo dõi và trả "
        "'không bị che'. Nếu phép kiểm này đỏ thì hành vi của git đã đổi, "
        "và cả gác lẫn `tests/test_bi_mat_bi_che.py` phải đọc lại.")


def test_LUAT_CHE_khong_duoc_thu_hep_am_tham():
    """Hai cách vô hiệu hoá gác này mà không sửa một dòng logic nào: rút
    `PHAI_BI_CHE` xuống còn một dòng, hoặc bỏ mẫu `*.db` khỏi
    `KHONG_DUOC_THEO_DOI`. Ghim lại cả hai tập.
    """
    assert {d for d, _ in PHAI_BI_CHE} == {
        "paper_trades.db",
        "paper_custom20loop_18m_loop_11.db",
        "paper_trades_seeded_insample.db",
        "backtest/cache/VNINDEX.csv",
        "backtest/cache_2018/FPT.csv",
        "sl_pattern_memory.json",
    }, "PHAI_BI_CHE bị đổi — gỡ một đường có chủ đích thì sửa cả tập này"
    assert {m for m, _ in KHONG_DUOC_THEO_DOI} == {
        "*.db", "backtest/cache*", "sl_pattern_memory.json",
    }, "KHONG_DUOC_THEO_DOI bị đổi — thu hẹp là bỏ gác, phải có chủ đích"
