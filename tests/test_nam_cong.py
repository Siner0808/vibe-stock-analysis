"""BƯỚC 201 — `tools/nam_cong.py`: năm cổng CHẠY CÙNG LÚC (người dùng 16/10/2026: "làm A+B, ép máy chạy đa nhân").

Hai điều phải giữ:
  1. Bộ cổng KHÔNG đổi — đúng tập công cụ CI chạy (`.github/workflows/kiem-dinh.yml`).
  2. "Cùng lúc" là THẬT — mọi cổng khởi động trước khi chờ cổng nào; `--tuan-tu`
     là đường lui chạy từng cổng một.
Cổng giả ở đây là `python -c` ngắn, chạy trong thư mục tạm; không chạy bộ test thật.
"""
from __future__ import annotations

import ast
import re
import sys
import textwrap
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import nam_cong  # noqa: E402

_CONG_CU = re.compile(r"tools/([a-z_0-9]+)\.py")


def _cong_gia(tmp_path: Path, ma: dict[int, int] | None = None, ngu: float = 0.6):
    """Năm cổng giả: mỗi cổng ghi giờ BẮT ĐẦU, ngủ `ngu` giây, ghi giờ XONG, thoát `ma[so]`."""
    ma = ma or {}
    ra = []
    for so in range(1, 6):
        moc = tmp_path / f"moc{so}.txt"
        lenh = ("import time,sys,pathlib; p=pathlib.Path(sys.argv[1]); "
                "p.write_text(str(time.time())+'\\n'); time.sleep(float(sys.argv[2])); "
                "p.write_text(p.read_text()+str(time.time())); sys.exit(int(sys.argv[3]))")
        ra.append((so, f"gia {so}", ["-c", lenh, str(moc), str(ngu), str(ma.get(so, 0))]))
    return ra


def _moc(tmp_path: Path) -> list[tuple[float, float]]:
    out = []
    for so in range(1, 6):
        bd, xong = (tmp_path / f"moc{so}.txt").read_text().split()
        out.append((float(bd), float(xong)))
    return out


#: Cổng giả CHỜ (BƯỚC 207): ghi mốc BẮT ĐẦU; chờ tới khi mọi tệp mốc trong argv[4:] có ít nhất
#: argv[3] dòng (quá 30 s thì thoát 3); ngủ argv[2] giây; ghi mốc XONG. Phép thử dựa vào thứ
#: tự SỰ KIỆN giữa các cổng thay vì một số giây tuyệt đối, nên khởi động chậm không làm đỏ.
_CONG_CHO = textwrap.dedent("""
    import pathlib, sys, time
    p = pathlib.Path(sys.argv[1])
    p.write_text(str(time.time()) + "\\n")
    can, khac = int(sys.argv[3]), [pathlib.Path(x) for x in sys.argv[4:]]
    han = time.time() + 30
    while not all(q.exists() and len(q.read_text().split()) >= can for q in khac):
        if time.time() > han:
            sys.exit(3)
        time.sleep(0.01)
    time.sleep(float(sys.argv[2]))
    p.write_text(p.read_text() + str(time.time()))
""")


def _cong_cho(moc: Path, ngu: float, can: int, khac: list[Path]) -> list[str]:
    return ["-c", _CONG_CHO, str(moc), str(ngu), str(can), *map(str, khac)]


def test_CONG_dung_tap_cong_CI_chay():
    """Không thêm, không bớt cổng: tập công cụ trùng tập trong workflow CI."""
    yml = (GOC / ".github" / "workflows" / "kiem-dinh.yml").read_text(encoding="utf-8")
    ci = set(_CONG_CU.findall(yml)) | ({"pytest"} if "pytest" in yml else set())  # van-ban-ok: workflow YAML là văn bản, không phải mã Python
    cua_ta = set()
    for _, _, doi_so in nam_cong.CONG:
        noi = " ".join(doi_so)
        cua_ta |= set(_CONG_CU.findall(noi))
        if "pytest" in noi:
            cua_ta.add("pytest")
    assert cua_ta == ci, (cua_ta, ci)
    assert [so for so, _, _ in nam_cong.CONG] == [1, 2, 3, 4, 5]
    assert "nam_cong" not in ci, "nam_cong không được là một cổng của CI (gác bộ cổng sẽ đòi tên nó)"


def test_CUNG_LUC_moi_cong_bat_dau_truoc_khi_cong_nao_xong(tmp_path):
    """Mỗi cổng giả chỉ ghi mốc XONG khi đã thấy mốc BẮT ĐẦU của cả năm cổng (BƯỚC 207).

    Bản cũ ngủ 0,6 s rồi so: dưới 16 tiến trình bận, độ lệch lúc khởi động đã lên 0,51 s —
    còn 0,13 s là đỏ giả. Rào thì không cần giấc ngủ nào: bản chạy cùng lúc qua rào ngay,
    bản chạy lần lượt để cổng 1 chờ tới hạn rồi thoát 3.
    """
    moc = [tmp_path / f"moc{so}.txt" for so in range(1, 6)]
    cong = [(so, f"gia {so}", _cong_cho(moc[so - 1], 0, 1, moc)) for so in range(1, 6)]
    kq = nam_cong.chay(cong=cong, thu_muc_log=tmp_path / "log", cwd=tmp_path)
    assert [c["ma"] for c in kq] == [0] * 5, "thoát 3: có cổng chờ hết hạn mà chưa thấy cả năm bắt đầu"
    moc = _moc(tmp_path)
    assert max(bd for bd, _ in moc) < min(xong for _, xong in moc), moc


#: Cổng 1 giả ngủ chừng này SAU KHI bốn cổng kia đã ghi mốc XONG; bốn cổng kia ngủ `_NGU_NHANH`.
_NGU_CONG_CHAM = 3.0
_NGU_NHANH = 0.05


def _cong_thoi_gian(tmp_path: Path):
    """Năm cổng giả của phép thử thời gian: cổng 1 chậm, chỉ bắt đầu ngủ khi bốn cổng kia xong."""
    cong = _cong_gia(tmp_path, ngu=_NGU_NHANH)
    so1, ten1, _ = cong[0]
    moc = [tmp_path / f"moc{so}.txt" for so in range(1, 6)]
    cong[0] = (so1, ten1, _cong_cho(moc[0], _NGU_CONG_CHAM, 2, moc[1:]))
    return cong


def test_THOI_GIAN_moi_cong_la_cua_CHINH_no_khong_phai_cua_cong_cham_dung_truoc(tmp_path):
    """Lỗi thật 16/10: chờ theo thứ tự nên cả năm cổng ghi 383 s của cổng 1.

    So TƯƠNG ĐỐI với cổng 1, không so với một số giây tuyệt đối (BƯỚC 207): bản cũ đòi mỗi
    cổng nhanh < 0,9 s và đỏ ở cổng 4 mọi lượt máy tải nặng ngày 17/10 — riêng khởi động
    Python đã vượt mức ấy. Cổng 1 giả chỉ bắt đầu ngủ `_NGU_CONG_CHAM` giây SAU khi bốn
    cổng kia ghi mốc XONG, nên khởi động chậm bao nhiêu cũng không xoá được khoảng cách:
      - đo đúng: giây cổng 1 − giây cổng k ≥ `_NGU_CONG_CHAM` − (lúc cổng k thoát hẳn
        + một nhịp hỏi 0,2 s của `nam_cong.chay`);
      - lỗi 16/10 (cổng k chỉ được ghi giờ khi cổng 1 xong): hiệu ấy chỉ còn độ lệch
        lúc KHỞI ĐỘNG giữa cổng 1 và cổng k (vài lời gọi `Popen`).
    Ranh giới đặt ở giữa: một nửa `_NGU_CONG_CHAM`. Cận dưới (mỗi cổng ≥ giấc ngủ của chính
    nó) chỉ chặt hơn khi máy rảnh, nên tải không làm nó đỏ.
    """
    kq = nam_cong.chay(cong=_cong_thoi_gian(tmp_path), thu_muc_log=tmp_path / "log", cwd=tmp_path)
    giay = [round(c["giay"], 2) for c in kq]
    assert [c["ma"] for c in kq] == [0] * 5, (giay, "cổng 1 giả thoát 3: bốn cổng kia không xong trong 30 s")
    assert kq[0]["giay"] >= _NGU_CONG_CHAM, giay
    assert all(c["giay"] >= _NGU_NHANH for c in kq[1:]), giay
    assert all(kq[0]["giay"] - c["giay"] >= _NGU_CONG_CHAM / 2 for c in kq[1:]), giay


def test_TUAN_TU_cong_sau_bat_dau_sau_khi_cong_truoc_xong(tmp_path):
    kq = nam_cong.chay(cong=_cong_gia(tmp_path, ngu=0.2), thu_muc_log=tmp_path / "log",
                       cwd=tmp_path, tuan_tu=True)
    assert [c["ma"] for c in kq] == [0] * 5
    moc = _moc(tmp_path)
    for (_, xong_truoc), (bd_sau, _) in zip(moc, moc[1:]):
        assert bd_sau >= xong_truoc


def test_MA_THOAT_mot_cong_hong_thi_ca_luot_tra_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(nam_cong, "CONG", _cong_gia(tmp_path, ma={3: 2}, ngu=0.1))
    monkeypatch.setattr(nam_cong, "GOC", tmp_path)
    monkeypatch.setattr(nam_cong, "co_xdist", lambda python: False)
    assert nam_cong.main(["--thu-muc-log", str(tmp_path / "log")]) == 1
    ra = capsys.readouterr().out
    assert "cong3=2" in ra and "cong1=0" in ra and "cổng 3 (mã 2)" in ra


def test_MA_THOAT_ca_nam_xanh_thi_tra_0_va_moi_cong_mot_log(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(nam_cong, "CONG", _cong_gia(tmp_path, ngu=0.1))
    monkeypatch.setattr(nam_cong, "GOC", tmp_path)
    monkeypatch.setattr(nam_cong, "co_xdist", lambda python: False)
    assert nam_cong.main(["--thu-muc-log", str(tmp_path / "log")]) == 0
    assert sorted(p.name for p in (tmp_path / "log").iterdir()) == [f"cong{i}.log" for i in range(1, 6)]
    assert "Cả năm cổng thoát 0" in capsys.readouterr().out


def test_AST_ban_cung_luc_khoi_dong_HET_roi_moi_cho():
    """Hình dạng: trong nhánh cùng lúc, mọi `bat_dau` nằm trong MỘT biểu thức dựng danh sách
    đứng TRƯỚC vòng `.wait()` — không phải khởi động rồi chờ từng cái."""
    cay = ast.parse((GOC / "tools" / "nam_cong.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "chay")
    dung = [n for n in ham.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "dang_chay" for t in n.targets)]
    assert len(dung) == 1 and isinstance(dung[0].value, ast.ListComp)
    vong_cho = [n for n in ham.body if isinstance(n, ast.For)
                and isinstance(n.iter, ast.Name) and n.iter.id == "dang_chay"]
    assert vong_cho and vong_cho[0].lineno > dung[0].lineno


# ── BƯỚC 222/236: cổng 1 Ở MÁY mặc định song song bằng pytest-xdist; CI giữ MỘT tiến trình ──

def test_CONG1_MAC_DINH_song_song_khi_CO_xdist(monkeypatch):
    """BƯỚC 236: không xin gì cả, có xdist thì cổng 1 chạy `-n auto`; bốn cổng kia không đổi."""
    monkeypatch.setattr(nam_cong, "co_xdist", lambda python: True)
    cong, ghi_chu = nam_cong.cong_may(python="py-gia")
    assert cong[0][2] == [*nam_cong.CONG[0][2], "-n", "auto"]
    assert cong[1:] == nam_cong.CONG[1:], "chỉ cổng 1 đổi"
    assert "SONG SONG" in ghi_chu


def test_CONG1_MAC_DINH_thieu_xdist_thi_lui_mot_tien_trinh_va_noi_ro(monkeypatch):
    """Máy không cài pytest-xdist (venv của phiên đám mây): lùi về một tiến trình, không nổ."""
    monkeypatch.setattr(nam_cong, "co_xdist", lambda python: False)
    cong, ghi_chu = nam_cong.cong_may(python="py-gia")
    assert cong == nam_cong.CONG
    assert "MỘT tiến trình" in ghi_chu and "thiếu pytest-xdist" in ghi_chu


def test_CONG1_ep_MOT_tien_trinh_du_co_xdist(monkeypatch):
    """`--mot-tien-trinh` thắng xdist: đường lui. Cũng không được hỏi xdist làm gì (không tốn một
    tiến trình con) khi người dùng đã ép."""
    hoi = []
    monkeypatch.setattr(nam_cong, "co_xdist", lambda python: hoi.append(python) or True)
    cong, ghi_chu = nam_cong.cong_may(python="py-gia", mot_tien_trinh=True)
    assert cong == nam_cong.CONG and "--mot-tien-trinh" in ghi_chu and "thiếu" not in ghi_chu
    assert hoi == []


def test_co_xdist_HOI_chinh_trinh_thong_dich_duoc_truyen(tmp_path):
    """Hỏi TIẾN TRÌNH CON của đúng trình thông dịch được truyền: trình đang chạy test trả đúng như
    `find_spec` của nó; một đường không tồn tại trả False, không nổ."""
    import importlib.util
    assert nam_cong.co_xdist(sys.executable) is (importlib.util.find_spec("xdist") is not None)
    assert nam_cong.co_xdist(str(tmp_path / "khong_co_python.exe")) is False


def _main_ghi_cong(tmp_path, monkeypatch, co_xdist: bool):
    """Dựng `main` với năm cổng giả; trả hàm `chay_main(*cờ)` -> (mã thoát, cổng 1 đã nhận, stdout)."""
    monkeypatch.setattr(nam_cong, "CONG", _cong_gia(tmp_path, ngu=0.1))
    monkeypatch.setattr(nam_cong, "GOC", tmp_path)
    monkeypatch.setattr(nam_cong, "co_xdist", lambda python: co_xdist)
    nhan = {}
    that = nam_cong.chay

    def chay_ghi(cong=None, **kw):
        nhan["cong"] = cong
        return that(cong=cong, **kw)

    monkeypatch.setattr(nam_cong, "chay", chay_ghi)
    dem = iter(range(100))

    def chay_main(capsys, *co):
        ma = nam_cong.main(["--thu-muc-log", str(tmp_path / f"log{next(dem)}"), *co])
        return ma, nhan["cong"][0][2], capsys.readouterr().out

    return chay_main


def test_MAIN_mac_dinh_song_song_va_in_cach_chay_cong1(tmp_path, monkeypatch, capsys):
    chay_main = _main_ghi_cong(tmp_path, monkeypatch, co_xdist=True)
    ma, cong1, ra = chay_main(capsys)
    assert ma == 0 and cong1[-2:] == ["-n", "auto"] and "SONG SONG" in ra


def test_MAIN_mot_tien_trinh_ep_cong1_khong_chia_tien_trinh(tmp_path, monkeypatch, capsys):
    chay_main = _main_ghi_cong(tmp_path, monkeypatch, co_xdist=True)
    ma, cong1, ra = chay_main(capsys, "--mot-tien-trinh")
    assert ma == 0 and "-n" not in cong1 and "--mot-tien-trinh" in ra and "SONG SONG" not in ra


def test_MAIN_thieu_xdist_mac_dinh_mot_tien_trinh_va_in_dong_lui(tmp_path, monkeypatch, capsys):
    chay_main = _main_ghi_cong(tmp_path, monkeypatch, co_xdist=False)
    ma, cong1, ra = chay_main(capsys)
    assert ma == 0 and "-n" not in cong1 and "thiếu pytest-xdist" in ra


def test_MAIN_song_song_van_duoc_nhan_va_giong_mac_dinh(tmp_path, monkeypatch, capsys):
    """Lệnh cũ trong tài liệu và phiếu giao còn `--song-song`: phải parse được, làm đúng như mặc định
    (cả khi có lẫn không xdist), và không đi chung được với `--mot-tien-trinh`."""
    for co in (True, False):
        chay_main = _main_ghi_cong(tmp_path, monkeypatch, co_xdist=co)
        mac_dinh = chay_main(capsys)
        cu = chay_main(capsys, "--song-song")
        assert cu[:2] == mac_dinh[:2] and cu[0] == 0, (co, cu, mac_dinh)
    with pytest.raises(SystemExit) as loi:
        nam_cong.main(["--song-song", "--mot-tien-trinh"])
    assert loi.value.code == 2


def test_MAIN_tuan_tu_la_truc_khac_khong_dung_den_cong1_song_song(tmp_path, monkeypatch, capsys):
    chay_main = _main_ghi_cong(tmp_path, monkeypatch, co_xdist=True)
    ma, cong1, ra = chay_main(capsys, "--tuan-tu")
    assert ma == 0 and cong1[-2:] == ["-n", "auto"] and "TUẦN TỰ" in ra


def test_CONG_goc_cong1_khong_mang_san_song_song():
    """`CONG` là bản MẪU theo CI (một tiến trình); song song chỉ được thêm trong `cong_may`. Nếu
    `-n` lọt vào `CONG` thì `--mot-tien-trinh` ép không nổi và cổng 1 bị thêm `-n` hai lần."""
    assert not set(nam_cong.CONG[0][2]) & {"-n", "--numprocesses", "--dist", "auto"}


def test_CI_cong1_van_MOT_tien_trinh():
    """Phép thử "cả bộ chung một tiến trình" (bắt test làm bẩn trạng thái của test khác) sống ở CI:
    lệnh pytest của workflow không chia tiến trình, và workflow không cài pytest-xdist."""
    yml = (GOC / ".github" / "workflows" / "kiem-dinh.yml").read_text(encoding="utf-8")
    lenh = [d for d in yml.splitlines() if "-m pytest" in d]  # van-ban-ok: workflow YAML là văn bản
    assert lenh, "workflow phải còn lệnh pytest"
    for d in lenh:
        assert not re.search(r"(^|\s)(-n|--numprocesses|--dist)(\s|=|$)", d), d
    assert "xdist" not in yml  # van-ban-ok: workflow YAML là văn bản, không phải mã Python
