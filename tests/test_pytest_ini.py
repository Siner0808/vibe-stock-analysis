"""Gác: `pytest` trần ở gốc repo chỉ được thu test trong `tests/`.

VÌ SAO CÓ FILE NÀY
──────────────────
Audit 25/09/2026 (`docs/STATE.md` BƯỚC 121, phát hiện ma_app_script-03):
repo không có file cấu hình pytest nào, nên `pytest` gõ trần ở gốc dùng mẫu
mặc định `test_*.py` / `*_test.py` và THU cả ba script gốc khớp mẫu ấy.
Thu tức là import, tức là chạy mã mức module — và hai trong ba script đó
`os.remove()` hai file `.db` đo lường mà `docs/kho-db-goc-repo.md` xếp vào
mục GIỮ. Một lệnh vô hại quen tay là đủ xoá bằng chứng.

VÌ SAO GÁC NÀY ĐỌC FILE CHỨ KHÔNG CHẠY `pytest`
────────────────────────────────────────────────
Phép thử hành vi tự nhiên nhất — chạy `pytest --collect-only` trần rồi xem
nó thu gì — sẽ, trong đúng lượt đục thử bỏ dòng `testpaths`, **thu và chạy
chính hai script xoá `.db`**. Một gác mà lượt đột biến của nó phá dữ liệu
người dùng thì không được phép tồn tại. Nên gác đọc `pytest.ini`.
"""
import configparser
import pathlib

GOC = pathlib.Path(__file__).resolve().parent.parent


def _cau_hinh() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    doc_duoc = cp.read(GOC / "pytest.ini", encoding="utf-8")
    assert doc_duoc, "không có pytest.ini ở gốc repo"
    assert cp.has_section("pytest"), "pytest.ini thiếu mục [pytest]"
    return cp


def test_testpaths_CHI_la_tests():
    cp = _cau_hinh()
    assert cp.has_option("pytest", "testpaths"), (
        "pytest.ini không khai testpaths — `pytest` trần sẽ thu script gốc")
    assert cp.get("pytest", "testpaths").split() == ["tests"], (
        "testpaths phải là đúng một thư mục `tests`: "
        f"đang là {cp.get('pytest', 'testpaths')!r}")


def test_khong_co_file_cau_hinh_pytest_thu_hai():
    """pytest dừng ở file cấu hình ĐẦU TIÊN nó tìm thấy. Thêm một file khác
    (`pyproject.toml` có `[tool.pytest.ini_options]`, `tox.ini`, `setup.cfg`)
    ở gốc thì thứ tự ưu tiên quyết định file nào thắng — và `pytest.ini`
    vốn thắng, nhưng một người đọc sẽ không biết điều đó. Một nơi, một luật.
    """
    khac = [ten for ten in ("pyproject.toml", "tox.ini", "setup.cfg")
            if (GOC / ten).exists()]
    assert not khac, (
        f"có thêm file cấu hình ở gốc: {khac} — gom cấu hình pytest về "
        "pytest.ini, hoặc sửa gác này có chủ đích")
