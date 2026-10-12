"""Gác của gác: `tests/conftest.py` có thật sự chặn test đọc/ghi VN-INDEX THẬT không (BƯỚC 184).

VÌ SAO CÓ FILE NÀY
──────────────────
`conftest.gac_khong_doc_vnindex_that` biến một test gọi `market_filter.get_vni_df()`
THẬT thành test ĐỎ. Nhưng một gác chết (luôn cho qua) trông y hệt một repo sạch:
hai test rò đã được vá, nên chúng xanh dù gác còn sống hay đã chết. Chỉ một test
CỐ Ý chạm hàm thật mới phân biệt được hai trường hợp — và test ấy phải chạy trong
một tiến trình pytest RIÊNG, vì chính gác đang canh tiến trình hiện tại.

Cách làm: dựng một thư mục tạm có `conftest.py` nạp NGUYÊN VĂN fixture và hook của
`tests/conftest.py` (không chép lại — chép thì kiểm bản chép), chạy một file test
mẫu trong tiến trình con, rồi đọc kết quả từng test bằng JUnit XML.

Mỗi ca dưới đây là một tình huống thật:

  a  gọi hàm thật, `CACHE_DIR` mặc định      -> ĐỎ, nêu tên test + cách sửa
  b  code của test NUỐT lỗi của gác          -> vẫn ĐỎ (hook `pytest_runtest_call`)
  c  `CACHE_DIR` -> tmp_path, `fetch_one` giả -> XANH (đúng ca của
     `test_noi_cache_an_toan.py`; gác không được chặn nó)
  d  vá `is_vni_bullish`                     -> XANH
  e  vá `get_vni_df`                         -> XANH
  f, g  hai test liền nhau: bản bọc được trả lại giữa hai test (không bọc chồng)
  h  `cache_clear` / `cache_info` vẫn dùng được qua bản bọc
  k  hàm THẬT không được chạy khi gác chặn (kể cả để rồi mới ném lỗi: lúc ấy nó
     đã đọc đĩa hoặc tải mạng)
  i  chạy với `VIBE_CACHE_DIR` đặt sẵn (CI/máy dùng cache riêng): `CACHE_DIR` chưa
     ai vá vẫn là đường cần canh
"""
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent

_CONFTEST_TAM = '''\
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "conftest_goc_cua_repo", pathlib.Path({duong!r}))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)

# Chỉ nạp ĐÚNG gác cần thử (không nạp `tra_lai_analyze`).
gac_khong_doc_vnindex_that = _m.gac_khong_doc_vnindex_that
pytest_runtest_call = _m.pytest_runtest_call
'''

_TEST_MAU = '''\
import functools
import sys

sys.path.insert(0, {goc!r})

import market_filter
from backtest import data as btd

# Ống nghe đặt TRƯỚC khi gác bọc: nó đếm số lần hàm "thật" (từ góc nhìn của gác)
# bị chạy. Gác chặn đúng thì số đó là 0.
LAN_CHAY_THAT = []
_that = market_filter.get_vni_df


# `lru_cache` THẬT, như `market_filter.get_vni_df`: nếu chỉ là hàm trơn có gắn
# `cache_clear` bằng tay thì `functools.wraps` của gác sao chép thuộc tính ấy và
# gác quên gắn lại `cache_clear` cũng không ai thấy.
@functools.lru_cache(maxsize=1)
def _ong_nghe():
    LAN_CHAY_THAT.append(1)
    return _that()


market_filter.get_vni_df = _ong_nghe
GOC_VNI = _ong_nghe


def test_a_goi_that_thi_do():
    market_filter.get_vni_df()


def test_b_nuot_loi_van_do():
    try:
        market_filter.get_vni_df()
    except AssertionError:
        pass


def test_c_tro_tmp_path_thi_qua(tmp_path, monkeypatch):
    monkeypatch.setattr(btd, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(btd, "fetch_one", lambda *a, **k: None)
    market_filter.get_vni_df.cache_clear()
    try:
        assert market_filter.get_vni_df() is None
    finally:
        market_filter.get_vni_df.cache_clear()


def test_d_va_is_vni_bullish_thi_qua(monkeypatch):
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda *a, **k: True)
    assert market_filter.is_vni_bullish("2024-01-02") is True


def test_e_va_get_vni_df_thi_qua(monkeypatch):
    monkeypatch.setattr(market_filter, "get_vni_df", lambda: None)
    assert market_filter.is_vni_bullish("2024-01-02") is True


def test_f_bao_boc_mot_lop():
    assert market_filter.get_vni_df is not GOC_VNI
    assert market_filter.get_vni_df.__wrapped__ is GOC_VNI


def test_g_van_mot_lop_sau_test_truoc():
    assert market_filter.get_vni_df.__wrapped__ is GOC_VNI


def test_h_cache_clear_va_cache_info_dung_duoc():
    market_filter.get_vni_df.cache_clear()
    assert market_filter.get_vni_df.cache_info().currsize == 0


def test_k_ham_that_khong_chay_khi_gac_chan():
    # test_a và test_b (trên) bị chặn; hàm thật mà từng chạy ở đó thì đã đọc
    # đĩa/mạng. Lần chạy DUY NHẤT hợp lệ là test_c (CACHE_DIR đã trỏ tmp_path).
    assert len(LAN_CHAY_THAT) == 1
'''

_TEST_MAU_ENV = '''\
import sys

sys.path.insert(0, {goc!r})

import market_filter
from backtest import data as btd


def test_i_CACHE_DIR_tu_moi_truong_chua_va_van_bi_canh(monkeypatch):
    monkeypatch.setattr(btd, "fetch_one", lambda *a, **k: None)  # không ra mạng
    market_filter.get_vni_df()
'''


def _chay_rieng(tmp, mau: str, vibe_cache_dir: str | None, so_ca: int) -> dict:
    """Chạy `mau` (nội dung một file test) trong tiến trình pytest riêng.

    Trả {tên test: (kết quả, thông điệp)}. `so_ca` là số test PHẢI thấy: một
    XML rỗng không được đọc thành "mọi ca đều xanh".
    """
    tmp.mkdir()
    (tmp / "conftest.py").write_text(
        _CONFTEST_TAM.format(duong=str(GOC / "tests" / "conftest.py")),
        encoding="utf-8")
    (tmp / "test_mau.py").write_text(mau.format(goc=str(GOC)), encoding="utf-8")
    xml = tmp / "kq.xml"
    moi_truong = dict(os.environ, PYTHONIOENCODING="utf-8")
    # Tiến trình con phải thấy đúng môi trường ta khai, không phải môi trường
    # của lượt chạy này (cổng 1 chạy dưới PYTEST_ADDOPTS tuỳ ý).
    moi_truong.pop("VIBE_CACHE_DIR", None)
    # Hermetic: một plugin tuỳ ý trong PYTEST_ADDOPTS (ví dụ ống nghe đo đạc bọc
    # `get_vni_df`) sẽ chen thêm một lớp giữa gác và hàm thật — làm hỏng chính
    # các phép kiểm số lớp bọc của file này.
    moi_truong.pop("PYTEST_ADDOPTS", None)
    if vibe_cache_dir is not None:
        moi_truong["VIBE_CACHE_DIR"] = vibe_cache_dir
    kq = subprocess.run(
        [sys.executable, "-m", "pytest", str(tmp / "test_mau.py"), "-q",
         "-p", "no:cacheprovider", "--tb=short", f"--junitxml={xml}",
         "-o", "junit_family=xunit2"],
        cwd=str(tmp), capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=moi_truong, timeout=240)
    assert xml.exists(), (
        "tiến trình con không ghi JUnit XML — chưa kiểm được:\n"
        + (kq.stdout or "")[-800:] + (kq.stderr or "")[-800:])
    ra = {}
    for tc in ET.parse(xml).getroot().iter("testcase"):
        loi = tc.find("failure")
        if loi is None:
            loi = tc.find("error")
        ra[tc.get("name")] = (
            "DO" if loi is not None else "XANH",
            (loi.get("message") or "") + (loi.text or "") if loi is not None else "")
    assert len(ra) == so_ca, f"phải có {so_ca} ca mẫu, thấy {len(ra)}: {sorted(ra)}"
    return ra


@pytest.fixture(scope="module")
def ket_qua(tmp_path_factory):
    """Ca mẫu a..h, k — `CACHE_DIR` là đường mặc định của repo."""
    return _chay_rieng(tmp_path_factory.mktemp("gac_vnindex") / "mac_dinh",
                       _TEST_MAU, None, 9)


@pytest.fixture(scope="module")
def ket_qua_env(tmp_path_factory):
    """Ca i — `VIBE_CACHE_DIR` đặt sẵn, `CACHE_DIR` là đường do môi trường chỉ."""
    tmp = tmp_path_factory.mktemp("gac_vnindex_env")
    return _chay_rieng(tmp / "env", _TEST_MAU_ENV, str(tmp / "cache_rieng"), 1)


def test_a_goi_that_tren_cache_cua_repo_la_DO_va_noi_ten_test_va_cach_sua(ket_qua):
    kq, msg = ket_qua["test_a_goi_that_thi_do"]
    assert kq == "DO"
    assert "test_a_goi_that_thi_do" in msg, "thông điệp phải nêu TÊN test"
    assert "is_vni_bullish" in msg and "tmp_path" in msg, (
        "thông điệp phải nêu cách sửa (vá hàm, hoặc trỏ CACHE_DIR sang tmp_path)")


def test_b_test_nuot_loi_cua_gac_van_DO(ket_qua):
    kq, msg = ket_qua["test_b_nuot_loi_van_do"]
    assert kq == "DO"
    assert "test_b_nuot_loi_van_do" in msg


def test_c_CACHE_DIR_tro_tmp_path_thi_XANH(ket_qua):
    assert ket_qua["test_c_tro_tmp_path_thi_qua"][0] == "XANH", \
        ket_qua["test_c_tro_tmp_path_thi_qua"][1]


@pytest.mark.parametrize("ten", [
    "test_d_va_is_vni_bullish_thi_qua",
    "test_e_va_get_vni_df_thi_qua",
])
def test_d_e_va_tuong_minh_thi_XANH(ket_qua, ten):
    assert ket_qua[ten][0] == "XANH", ket_qua[ten][1]


@pytest.mark.parametrize("ten", [
    "test_f_bao_boc_mot_lop",
    "test_g_van_mot_lop_sau_test_truoc",
    "test_h_cache_clear_va_cache_info_dung_duoc",
])
def test_f_g_h_boc_duoc_tra_lai_va_cache_clear_dung_duoc(ket_qua, ten):
    assert ket_qua[ten][0] == "XANH", ket_qua[ten][1]


def test_k_ham_that_khong_duoc_chay_khi_gac_chan(ket_qua):
    assert ket_qua["test_k_ham_that_khong_chay_khi_gac_chan"][0] == "XANH", \
        ket_qua["test_k_ham_that_khong_chay_khi_gac_chan"][1]


def test_i_CACHE_DIR_do_VIBE_CACHE_DIR_chi_ra_van_bi_canh(ket_qua_env):
    kq, msg = ket_qua_env["test_i_CACHE_DIR_tu_moi_truong_chua_va_van_bi_canh"]
    assert kq == "DO", "CACHE_DIR chưa vá (kể cả do biến môi trường chỉ) phải bị canh"
    assert "test_i_CACHE_DIR_tu_moi_truong" in msg
