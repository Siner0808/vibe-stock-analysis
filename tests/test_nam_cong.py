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
from pathlib import Path

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
    kq = nam_cong.chay(cong=_cong_gia(tmp_path), thu_muc_log=tmp_path / "log", cwd=tmp_path)
    assert [c["ma"] for c in kq] == [0] * 5
    moc = _moc(tmp_path)
    assert max(bd for bd, _ in moc) < min(xong for _, xong in moc), moc


def test_THOI_GIAN_moi_cong_la_cua_CHINH_no_khong_phai_cua_cong_cham_dung_truoc(tmp_path):
    """Lỗi thật 16/10: chờ theo thứ tự nên cả năm cổng ghi 383 s của cổng 1."""
    cong = _cong_gia(tmp_path, ngu=0.05)
    so1, ten1, doi1 = cong[0]
    cong[0] = (so1, ten1, [*doi1[:3], "1.2", doi1[4]])     # cổng 1 ngủ 1,2 s, các cổng sau 0,05 s
    kq = nam_cong.chay(cong=cong, thu_muc_log=tmp_path / "log", cwd=tmp_path)
    assert kq[0]["giay"] >= 1.1
    assert all(c["giay"] < 0.9 for c in kq[1:]), [round(c["giay"], 2) for c in kq]


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
    assert nam_cong.main(["--thu-muc-log", str(tmp_path / "log")]) == 1
    ra = capsys.readouterr().out
    assert "cong3=2" in ra and "cong1=0" in ra and "cổng 3 (mã 2)" in ra


def test_MA_THOAT_ca_nam_xanh_thi_tra_0_va_moi_cong_mot_log(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(nam_cong, "CONG", _cong_gia(tmp_path, ngu=0.1))
    monkeypatch.setattr(nam_cong, "GOC", tmp_path)
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
