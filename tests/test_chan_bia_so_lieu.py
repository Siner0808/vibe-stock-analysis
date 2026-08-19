"""Test hook chặn bịa số liệu.

Hai nửa quan trọng ngang nhau:
  1. BẮT ĐƯỢC dòng đã gây ra sự cố thật (getattr tên sai -> hằng số 30)
  2. KHÔNG BÁO NHẦM mã lành. Hook nhiễu là hook bị tắt, mà hook bị tắt thì
     bằng không có.

Chạy offline:  python3 tests/test_chan_bia_so_lieu.py
"""
import os
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import chan_bia_so_lieu as hook


def _do(ma: str, ten_file: str = "thu.py") -> list:
    """Chạy bộ dò trên một đoạn mã, trả list phát hiện."""
    with tempfile.TemporaryDirectory(dir=str(GOC)) as d:
        f = Path(d) / ten_file
        f.write_text(ma, encoding="utf-8")
        return hook.kiem_tra(f)


def _ma(phat_hien) -> set:
    return {p.ma for p in phat_hien}


# ── 1. Bắt đúng sự cố thật ───────────────────────────────────────────
def test_bat_dung_dong_gay_su_co_12_08():
    """Dòng thật từ google_sheets_sync.py bản đầu."""
    p = _do('rows.append([getattr(t, "position_size_pct", 30)])')
    assert "R1" in _ma(p), f"không bắt được mặc định số: {_ma(p)}"
    assert "R2" in _ma(p), f"không bắt được tên trường sai: {_ma(p)}"
    goi_y = " ".join(x.goi_y for x in p)
    assert "size_pct" in goi_y, f"phải gợi ý đúng tên trường: {goi_y}"
    assert all(x.chan for x in p), "cả hai lỗi này phải CHẶN"
    print(f"PASS  bắt được getattr(t,'position_size_pct',30) -> {sorted(_ma(p))}, "
          f"gợi ý đúng 'size_pct'")


def test_ten_truong_sai_bi_bat_du_khong_co_mac_dinh_so():
    p = _do('x = getattr(trade, "entry_scores", None)')
    assert "R2" in _ma(p)
    assert "entry_score" in " ".join(x.goi_y for x in p)
    print("PASS  tên trường sai bị bắt kể cả khi mặc định là None")


def test_nuot_loi_roi_tra_ve_so():
    p = _do("def f():\n"
            "    try:\n"
            "        return do_gia()\n"
            "    except Exception:\n"
            "        return 50\n")
    assert "R3" in _ma(p)
    assert any(x.chan for x in p if x.ma == "R3")
    print("PASS  except -> return 50 bị chặn")


def test_nang_san_gia_tri_da_do():
    """Mẫu momentum_norm = max(momentum_norm, 65.0) trong master_agent.py."""
    p = _do("momentum_norm = max(momentum_norm, 65.0)")
    assert "R5" in _ma(p)
    print("PASS  bắt được max(x, 65.0) — điểm số do dòng này đặt ra")


def test_get_voi_mac_dinh_so_khac_khong():
    p = _do('v = packet.get("volume", 1500000)')
    assert "R4" in _ma(p)
    print("PASS  .get('volume', 1500000) bị cảnh báo")


# ── 2. KHÔNG báo nhầm mã lành ────────────────────────────────────────
def test_khong_bao_nham_getattr_ten_dung():
    p = _do('x = getattr(t, "size_pct", None)')
    assert p == [], f"tên trường ĐÚNG mà vẫn báo: {[x.thong_diep for x in p]}"
    print("PASS  getattr tên đúng + mặc định None -> im lặng")


def test_khong_bao_nham_bien_hop_le():
    """max(0, x) / min(x, 100) là kẹp biên thang điểm, không phải bịa."""
    p = _do("diem = max(diem, 0)\ndiem = min(diem, 100)\n")
    assert p == [], f"kẹp biên hợp lệ bị báo: {[x.thong_diep for x in p]}"
    print("PASS  kẹp biên 0/100 không bị báo nhầm")


def test_khong_bao_nham_chuoi_va_chu_thich():
    """Regex sẽ dính; AST thì không."""
    p = _do('s = "getattr(t, \\"position_size_pct\\", 30)"\n'
            "# getattr(t, 'position_size_pct', 30)\n")
    assert p == [], f"chuỗi/chú thích bị coi là mã: {[x.thong_diep for x in p]}"
    print("PASS  chuỗi và chú thích không bị coi là mã")


def test_khong_bao_nham_get_mac_dinh_trung_tinh():
    p = _do('n = d.get("so_lenh", 0)\nr = d.get("ty_le", 1)\n')
    assert p == [], f"mặc định trung tính bị báo: {[x.thong_diep for x in p]}"
    print("PASS  .get(k, 0) và .get(k, 1) không bị báo nhầm")


def test_file_trong_tests_duoc_mien():
    """Test dựng dữ liệu giả là đúng việc của nó."""
    ma = 'x = getattr(t, "size_pct", 30)\nv = d.get("volume", 999)\n'
    f = GOC / "tests" / "__tam_kiem_tra_mien_tru.py"
    try:
        f.write_text(ma, encoding="utf-8")
        p = hook.kiem_tra(f)
        assert "R1" not in _ma(p) and "R4" not in _ma(p), \
            f"tests/ phải được miễn R1/R4: {_ma(p)}"
    finally:
        if f.exists():
            f.unlink()
    print("PASS  file trong tests/ được miễn R1/R4")


# ── 3. Cửa thoát ─────────────────────────────────────────────────────
def test_cua_thoat_co_ly_do_thi_qua():
    p = _do('x = getattr(cfg, "so_phien_toi_da", 60)  # bia-ok: hằng số cấu hình\n')
    assert p == [], f"cửa thoát có lý do mà vẫn chặn: {[x.thong_diep for x in p]}"
    print("PASS  '# bia-ok: <lý do>' cho qua")


def test_cua_thoat_dong_ngay_tren_cung_duoc():
    p = _do("# bia-ok: ngưỡng mặc định khi thiếu cấu hình\n"
            'x = getattr(cfg, "nguong", 62)\n')
    assert p == []
    print("PASS  cửa thoát đặt ở dòng ngay trên cũng được")


def test_cua_thoat_ly_do_nhieu_dong():
    """Lý do tử tế thường dài hơn một dòng; phạt người viết dài là khuyến
    khích viết cụt."""
    p = _do("def f():\n"
            "    try:\n"
            "        return doc()\n"
            "    except Exception:\n"
            "        # bia-ok: thiếu ngày thì coi như vừa vào lệnh, để một\n"
            "        # bản ghi hỏng không làm sập cả phiên quét.\n"
            "        return 0\n")
    assert p == [], f"lý do nhiều dòng bị bỏ qua: {[x.thong_diep for x in p]}"
    print("PASS  lý do viết nhiều dòng vẫn được chấp nhận")


def test_khong_bao_nham_getattr_tren_argparse():
    """getattr(args, 'no_summary', False) là đọc CỜ, không phải số đo."""
    p = _do("if not getattr(args, 'no_summary', False):\n    pass\n")
    assert p == [], f"argparse bị báo nhầm: {[x.thong_diep for x in p]}"
    print("PASS  getattr trên args/cfg + mặc định bool -> im lặng")


def test_cua_thoat_khong_ly_do_thi_khong_qua():
    """Bắt buộc nói ra vì sao — đó mới là mục đích."""
    p = _do('x = getattr(cfg, "nguong", 62)  # bia-ok:\n')
    assert "R1" in _ma(p), "cửa thoát rỗng phải bị từ chối"
    print("PASS  '# bia-ok:' rỗng không được chấp nhận")


# ── 4. Phạm vi & độ bền ──────────────────────────────────────────────
def test_file_ngoai_du_an_bi_bo_qua():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "ngoai.py"
        f.write_text('x = getattr(t, "position_size_pct", 30)', encoding="utf-8")
        assert hook.trong_pham_vi(f) is False
    print("PASS  file ngoài dự án không bị đụng tới")


def test_file_khong_phai_python_bi_bo_qua():
    assert hook.trong_pham_vi(GOC / "README.md") is False
    assert hook.trong_pham_vi(GOC / "khong_ton_tai.py") is False
    print("PASS  file không phải .py hoặc không tồn tại -> bỏ qua")


def test_ma_loi_cu_phap_khong_lam_vo_hook():
    """Edit dở dang không được làm hook nổ."""
    p = _do("def f(:\n  pass\n")
    assert p == []
    print("PASS  mã lỗi cú pháp -> hook im lặng, không vỡ")


def test_ma_that_cua_du_an_khong_bi_bao_nham():
    """Chạy trên toàn bộ mã nguồn thật. Nếu hook báo lung tung ở đây thì
    nó sẽ bị tắt trong một tuần."""
    bo_qua = {"google_sheets_sync.py"}      # đã sửa, giữ để đối chiếu
    bao = {}
    for f in GOC.glob("*.py"):
        if f.name in bo_qua:
            continue
        chan = [p for p in hook.kiem_tra(f) if p.chan]
        if chan:
            bao[f.name] = [f"{p.ma}:{p.dong} {p.thong_diep}" for p in chan]
    assert not bao, f"mã thật bị chặn nhầm: {bao}"
    print(f"PASS  quét {len(list(GOC.glob('*.py')))} file thật -> 0 chặn nhầm")


def test_return_0_trong_main_la_ma_thoat_khong_phai_so_do():
    """Chính hook này bị nó chặn oan ngay lần đầu: `except: return 0` trong
    main() nghĩa là "không chặn", chứ không phải "đo được 0"."""
    p = _do("def main():\n"
            "    try:\n"
            "        x = doc()\n"
            "    except Exception:\n"
            "        return 0\n"
            "    return 0\n")
    assert p == [], f"mã thoát bị coi là số đo: {[x.thong_diep for x in p]}"
    print("PASS  return 0 trong main() -> mã thoát, không bị chặn")


def test_return_0_trong_ham_do_luong_van_bi_chan():
    """Nới cho main() không được nới cho hàm đo."""
    p = _do("def so_phien_nam_giu(a, b):\n"
            "    try:\n"
            "        return tinh(a, b)\n"
            "    except Exception:\n"
            "        return 0\n")
    assert "R3" in _ma(p), "hàm đo lường vẫn phải bị chặn"
    print("PASS  return 0 trong hàm đo lường vẫn bị chặn")


def test_chong_bao_trung():
    """Hook đăng ký ở cả settings người dùng lẫn settings dự án sẽ chạy hai
    lần trên cùng một file. Lần hai phải im."""
    import hashlib
    import tempfile as tf
    from pathlib import Path as P

    ma = 'x = getattr(t, "position_size_pct", 30)\n'
    f = GOC / "__tam_chong_trung.py"
    dau = hashlib.sha256(f"{f.resolve()}\n{ma}".encode()).hexdigest()[:32]
    moc = P(tf.gettempdir()) / f"chan_bia_{dau}.moc"
    try:
        if moc.exists():
            moc.unlink()
        f.write_text(ma, encoding="utf-8")
        lan1 = hook.da_bao_gan_day(f.resolve(), ma)
        lan2 = hook.da_bao_gan_day(f.resolve(), ma)
        assert lan1 is False, "lần đầu phải báo"
        assert lan2 is True, "lần hai (hook trùng) phải im"

        # nội dung đổi -> phải báo lại ngay, không được nuốt lỗi thật
        ma2 = 'y = getattr(t, "position_size_pct", 30)\n'
        assert hook.da_bao_gan_day(f.resolve(), ma2) is False
    finally:
        for x in (f, moc):
            if x.exists():
                x.unlink()
    print("PASS  chạy trùng -> im; nội dung đổi -> báo lại ngay")


def chay_tat_ca() -> int:
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n===== {len(fns) - failed}/{len(fns)} test PASS =====")
    return 1 if failed else 0



# ── 5. Chế độ quét toàn repo cho CI ──────────────────────────────────
def test_quet_repo_bat_duoc_mau_chan():
    """`--quet-repo` phải trả 1 khi có file vi phạm mức CHẶN.

    Hook PostToolUse chỉ chạy SAU khi ghi và chỉ bắt Write/Edit của Claude
    Code — sửa từ IDE, Antigravity, tay người, `git checkout` hay
    `git merge` đều không kích hoạt. Chế độ này để CI chạy: cửa chống
    cháy, không phải chuông báo cháy.
    """
    with tempfile.TemporaryDirectory(dir=str(GOC)) as d:
        Path(d, "vi_pham_tam.py").write_text(
            'x = getattr(t, "position_size_pct", 30)\n', encoding="utf-8")
        assert hook.quet_repo() == 1, (
            "quét toàn repo KHÔNG bắt được mẫu R1/R2 mức CHẶN")
    print("PASS  --quet-repo trả 1 khi có mẫu chặn")


def test_repo_hien_tai_sach_o_muc_chan():
    """Bất biến: mã nguồn đang có KHÔNG chứa mẫu bịa số mức CHẶN.

    Test này là thứ CI dựa vào. Nó đỏ nghĩa là một mẫu đã từng làm hỏng dự
    án vừa quay lại — đọc output để biết file và dòng nào.
    """
    assert hook.quet_repo() == 0, (
        "repo có mẫu bịa số liệu mức CHẶN — xem danh sách in ở trên")
    print("PASS  repo sạch ở mức CHẶN")


if __name__ == "__main__":
    sys.exit(chay_tat_ca())
