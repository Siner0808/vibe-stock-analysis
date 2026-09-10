"""Ba điều kiện của phép CÀI ĐẶT ĐO 2 — ký 09/09/2026.

`docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 2 — điều khoản bổ sung":

  1. tham số mới ở giá trị mặc định cho ra kết quả Y HỆT hôm nay
  2. tập phiên được CHẤM không đổi
  3. tập phiên RA QUYẾT ĐỊNH không đổi

VÌ SAO KIỂM TRÊN LỊCH GHÉ, KHÔNG KIỂM TRÊN KẾT QUẢ MÔ PHỎNG

Bản đầu của phép kiểm này định dựng một fixture chạy hết đường ống rồi so
kết quả. Thử ngày 09/09/2026 trên một chuỗi giá sinh có hạt giống: **0
lệnh**, vì `data_quality` trả `BLOCK` và bộ lọc VN-INDEX chặn phiên đầu.
Cả hai phụ thuộc `backtest/cache/` — thứ **không có trên CI**. Một phép
kiểm chỉ chạy được ở máy local thì vắng mặt đúng chỗ nó cần có mặt.

Nhưng cơ chế DUY NHẤT mà tham số mới có thể làm đổi kết quả là làm đổi
**lịch ghé**. Nên tách lịch thành hàm thuần rồi kiểm thẳng trên nó: không
cache, không agent, chạy được mọi nơi, và khoá đúng thứ cần khoá.

Phép so đầu-cuối thì đã có sẵn, không tốn gì thêm: lượt 1 của ĐO 1 ở cấu
hình mặc định phải ra lại 379 lệnh · alpha −0,68% · KTC [−1,47 ; +0,21],
con số đã tái lập hai lần trong hai ngày.
"""
import ast
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import walkforward as wf


def _mac_dinh(ten_ham: str, ten_tham_so: str):
    """Giá trị mặc định của một tham số, đọc bằng AST từ nguồn.

    Đọc NGUỒN chứ không đọc chữ ký lúc chạy: một mặc định bị vá ở chỗ
    khác trong phiên vẫn qua được phép đọc lúc chạy.
    """
    cay = ast.parse((GOC / "walkforward.py").read_text(encoding="utf-8"))
    h = [n for n in ast.walk(cay)
         if isinstance(n, ast.FunctionDef) and n.name == ten_ham][0]
    ten = [a.arg for a in h.args.args]
    vt = ten.index(ten_tham_so)
    lech = len(ten) - len(h.args.defaults)
    return h.args.defaults[vt - lech]


def test_MAC_DINH_o_ben_GOI_la_T_CONG_1():
    """`_mo_phong` và `chay` mặc định khớp T+1 — ĐỔI ngày 10/09/2026.

    Đường chạy thật khớp T+1; backtest mặc định từng khớp T+2 như một tác
    dụng phụ của `stride` mà không ai chọn. ĐO 2 đo được cái giá của việc
    ấy: alpha lệch **+0,12 → +0,13 điểm**, nhỏ hơn một phần sáu bề rộng
    KTC. Người dùng chốt đổi mặc định, và chốt luôn rằng nó phải đi CÙNG
    một lượt đo lại đầy đủ (`docs/TIEU-CHI-DOC-TRUOC.md` mục ĐO 3).

    Phép kiểm này tồn tại vì một mặc định trôi ngược lại sẽ **không làm
    test nào đỏ** — nó chỉ âm thầm đổi mọi con số walk-forward về sau.
    """
    for ten in ("_mo_phong", "chay"):
        m = _mac_dinh(ten, "do_tre_khop")
        assert isinstance(m, ast.Constant) and m.value == 1, (
            f"{ten}: do_tre_khop mặc định {ast.dump(m)} — phải là 1 (T+1)")
    print("PASS  _mo_phong và chay mặc định T+1")


def test_HAI_HAM_THUAN_van_giu_ky_hieu_None():
    """`diem_ghe` và `lich_theo_ngay` mặc định vẫn `None`, CÓ CHỦ Ý.

    `None` ở hai hàm ấy là **ký hiệu ngữ nghĩa** — *"bằng `stride`"* —
    không phải một chính sách. Hai điều kiện người dùng ký ngày 09/09
    (`test_DIEU_KIEN_1...` và `1b`) kiểm đúng ký hiệu đó.

    Nên khi đổi chính sách sang T+1 ngày 10/09, chỗ đổi là bên GỌI, không
    phải hai hàm này. Đổi ký hiệu ở đây sẽ làm hai điều kiện đã ký mất ý
    nghĩa mà vẫn xanh — chúng sẽ kiểm một câu khác với câu đã ký.
    """
    for ten in ("diem_ghe", "lich_theo_ngay"):
        m = _mac_dinh(ten, "do_tre_khop")
        assert isinstance(m, ast.Constant) and m.value is None, (
            f"{ten}: ký hiệu None đã bị đổi — hai điều kiện đã ký nay "
            f"kiểm một câu khác với câu được ký")
    print("PASS  hai hàm thuần giữ nguyên ký hiệu None")


def _luoi(n: int, min_history: int, stride: int) -> list:
    """Đúng biểu thức đang chạy hôm nay, viết lại ở đây làm mốc so."""
    return list(range(min_history, n, stride))


def test_DIEU_KIEN_1_mac_dinh_cho_lich_Y_HET_hom_nay():
    """Mặc định `None` phải cho ra ĐÚNG lịch của hôm nay, không thêm phiên nào.

    Đây là điều kiện mạnh nhất trong ba, và là thứ duy nhất chứng minh
    được rằng phép tách không kéo theo gì khác. Hỏng nó thì DỪNG, không
    chạy lượt nào — một mặc định làm đổi số cũ nghĩa là ĐO 2 lại đo hai
    thứ, y như lựa chọn 2 đã bị loại.
    """
    for n, mh, st in ((420, 60, 2), (300, 60, 3), (100, 60, 1), (61, 60, 2)):
        cho = [(t, False) for t in _luoi(n, mh, st)]
        assert wf.diem_ghe(n, mh, st) == cho, (
            f"n={n} min_history={mh} stride={st}: mặc định đã đổi lịch")
    print("PASS  điều kiện 1 — mặc định cho lịch y hệt hôm nay")


def test_DIEU_KIEN_1b_do_tre_bang_stride_cung_KHONG_doi_gi():
    """`do_tre_khop == stride` là chính cấu hình hôm nay, viết tường minh.

    Hôm nay độ trễ khớp BẰNG `stride` — đó là tác dụng phụ không ai chọn,
    và là lý do ĐO 2 tồn tại. Nên đặt tham số đúng bằng `stride` phải cho
    ra lịch y hệt: nếu không, phép tách đã hiểu sai chính thứ nó tách.
    """
    for n, mh, st in ((420, 60, 2), (300, 60, 3), (250, 60, 5)):
        assert wf.diem_ghe(n, mh, st, st) == wf.diem_ghe(n, mh, st), (
            f"stride={st}: do_tre_khop=stride khác mặc định")
    print("PASS  điều kiện 1b — do_tre_khop = stride ≡ hôm nay")


def test_DIEU_KIEN_2_va_3_tap_phien_CHAM_va_QUYET_DINH_khong_doi():
    """Phiên ghé-thêm CHỈ để khớp. Lưới chấm/quyết định đứng yên.

    Đếm chứ không đọc mã: tập `t` có `chi_khop=False` phải bằng đúng lưới
    `stride`, với MỌI giá trị của `do_tre_khop`.

    Đây là chỗ phân biệt hướng 3 với hướng 2 đã bị loại. Hướng 2 (chạy
    `--stride 1`) làm số điểm quyết định gấp đôi, nên tập lệnh khác hẳn và
    khác biệt quan sát được không quy được cho vế nào.
    """
    n, mh, st = 420, 60, 2
    luoi = set(_luoi(n, mh, st))
    for k in (1, 2, 3, 5):
        lich = wf.diem_ghe(n, mh, st, k)
        cham = {t for t, chi_khop in lich if not chi_khop}
        assert cham == luoi, (
            f"do_tre_khop={k}: tập phiên CHẤM đổi — thừa "
            f"{sorted(cham - luoi)}, thiếu {sorted(luoi - cham)}")
    print("PASS  điều kiện 2 và 3 — lưới chấm/quyết định đứng yên")


def test_do_tre_1_thi_lenh_sinh_o_t_khop_o_t_cong_1():
    """Cái phép đo này SINH RA để làm: khớp ở T+1 thay vì T+2.

    Lệnh sinh ở một phiên trên lưới khớp ở phiên KẾ TIẾP ĐƯỢC GHÉ. Nên
    với `do_tre_khop=1`, phiên `t+1` phải có mặt trong lịch — và phải có
    mặt với cờ CHỈ-KHỚP, không phải như một điểm quyết định mới.
    """
    n, mh, st = 200, 60, 2
    lich = dict(wf.diem_ghe(n, mh, st, 1))
    for t in _luoi(n, mh, st):
        if t + 1 >= n:
            continue
        assert t + 1 in lich, f"phiên {t + 1} không được ghé -> không khớp được"
        assert lich[t + 1] is True, (
            f"phiên {t + 1} được ghé để LÀM CẢ BA VIỆC — đó là hướng 2, "
            f"không phải hướng 3")
    print("PASS  do_tre_khop=1 -> ghé t+1, chỉ để khớp")


def test_do_tre_KHONG_HOP_LE_thi_no_chu_khong_doan():
    """0 hay số âm là một câu hỏi vô nghĩa, không phải một mặc định."""
    import pytest
    for xau in (0, -1):
        with pytest.raises(ValueError):
            wf.diem_ghe(420, 60, 2, xau)
    print("PASS  do_tre_khop <= 0 -> nổ")


def _du_lieu_nho():
    import pandas as pd
    ngay = pd.bdate_range("2024-01-01", periods=80).strftime("%Y-%m-%d")
    n = len(ngay)
    return pd.DataFrame({"time": ngay, "open": [10.0] * n, "high": [10.4] * n,
                         "low": [9.7] * n, "close": [10.1] * n,
                         "volume": [1_000_000.0] * n})


def test_chi_khop_KHONG_goi_analyze_va_final_score_la_None(tmp_path,
                                                           monkeypatch):
    """Cờ phải tới được `run_session` và đổi HÀNH VI, không chỉ tồn tại.

    Ba lịch ghé ở trên là hàm THUẦN — chúng chứng minh lịch đúng, không
    chứng minh cờ đi tới đâu. `CLAUDE.md` có sẵn một đột biến sống sót
    đúng hình dạng này: hook tồn tại, matcher đổi, không nối vào đâu cả.

    ĐỐI CHỨNG là nửa quan trọng của test. Không có nó, phép kiểm vẫn xanh
    trong một thế giới mà `_analyze` không bao giờ chạm tới được vì lý do
    khác — và khi ấy nó không đo cái nó tưởng nó đo. Đúng lỗi 22, mắc
    cùng ngày 09/09/2026.
    """
    import pytest

    import paper_runner as pr
    from paper_trading import PaperTradingJournal

    df = _du_lieu_nho()
    bar = {"open": 10.0, "high": 10.4, "low": 9.7, "close": 10.1,
           "volume": 1_000_000.0}

    def no_duoc_goi(*a, **k):
        raise AssertionError("_analyze bị gọi trong phiên CHỈ-KHỚP")

    monkeypatch.setattr(pr, "_analyze", no_duoc_goi)
    so = PaperTradingJournal(str(tmp_path / "wf_test_chi_khop.db"))
    try:
        st = pr.run_session(so, "AAA", df, bar, "2024-04-19", chi_khop=True)
        assert st["final_score"] is None, (
            f"phiên CHỈ-KHỚP không chấm điểm, mà final_score = "
            f"{st['final_score']!r}. Một con số ở đây sẽ đi vào báo cáo "
            f"như thể có ai đã chấm.")
        assert st["opened"] == 0 and st["closed"] == 0

        # ĐỐI CHỨNG: cùng lời gọi, chi_khop=False, PHẢI nổ.
        with pytest.raises(AssertionError):
            pr.run_session(so, "AAA", df, bar, "2024-04-22", chi_khop=False)
    finally:
        so.db.close()
    print("PASS  chi_khop=True bỏ qua _analyze · đối chứng có nổ")


def test_MO_PHONG_truyen_DUNG_lich_xuong_tung_phien(tmp_path, monkeypatch):
    """Vòng lặp -> `_chay_mot_phien` -> `run_session`: khoá CẢ chuỗi.

    Ba test lịch ở trên là hàm thuần; test `chi_khop` ở trên gọi thẳng
    `run_session`. Giữa hai đầu ấy có hai mắt xích không phép kiểm nào
    chạm tới — và một đột biến ở giữa (`chi_khop=ck` thành `False`) sẽ
    sống sót cả hai.

    Đây đúng bảng "đột biến sống sót" trong `CLAUDE.md`: gác tồn tại, đầu
    này đúng, đầu kia đúng, mà dây ở giữa đứt.
    """
    ghi = []
    monkeypatch.setattr(
        wf, "_chay_mot_phien",
        lambda so, sym, df, t, nguong, chi_khop=False:
            ghi.append((sym, t, chi_khop)))

    df = _du_lieu_nho()
    for do_tre in (None, 1):
        ghi.clear()
        wf._mo_phong({"AAA": df}, 50.0,
                     str(tmp_path / f"wf_lich_{do_tre}.db"),
                     stride=2, min_history=60, che_do_hoc="tat",
                     duong_bo_nho=None, do_tre_khop=do_tre)
        cho = [("AAA", t, ck)
               for t, ck in wf.diem_ghe(len(df), 60, 2, do_tre)]
        assert ghi == cho, (
            f"do_tre_khop={do_tre}: lịch không xuống tới từng phiên. "
            f"Nhận {len(ghi)} lời gọi, chờ {len(cho)}.")
    print("PASS  _mo_phong truyền đúng lịch xuống từng phiên")


def test_chay_mot_phien_TRUYEN_co_xuong_run_session(monkeypatch):
    """Mắt xích `_chay_mot_phien` -> `run_session`.

    Đột biến M6 (09/09/2026) sống sót qua sáu test đầu: `_chay_mot_phien`
    nhận cờ rồi truyền `chi_khop=False` xuống. Lịch đúng, `run_session`
    đúng, dây giữa hai đầu đứt — và không phép kiểm nào đi qua nó, vì test
    lan truyền monkeypatch chính `_chay_mot_phien`.
    """
    import paper_runner as pr

    ghi = []
    monkeypatch.setattr(pr, "run_session",
                        lambda *a, **k: ghi.append(k.get("chi_khop")))
    df = _du_lieu_nho()
    wf._chay_mot_phien(None, "AAA", df, 70, 50.0, chi_khop=True)
    wf._chay_mot_phien(None, "AAA", df, 70, 50.0, chi_khop=False)
    assert ghi == [True, False], f"cờ không xuống tới run_session: {ghi}"
    print("PASS  _chay_mot_phien truyền cờ xuống run_session")


def test_CA_HAI_che_do_deu_truyen_lich_dung(tmp_path, monkeypatch):
    """Chế độ THEO NGÀY cũng phải truyền cờ — đột biến M8 sống sót vì thiếu.

    Hai vòng lịch là hai bản mã riêng, và `CLAUDE.md` đã ghi sẵn rằng đó
    chính là chỗ hai chế độ trôi ra khỏi nhau. Kiểm một chế độ rồi tin cả
    hai là đúng cách đột biến `theo_ngay` sống sót ngày 31/08/2026.
    """
    ghi = []
    monkeypatch.setattr(
        wf, "_chay_mot_phien",
        lambda so, sym, df, t, nguong, chi_khop=False:
            ghi.append((sym, t, chi_khop)))

    du_lieu = {"AAA": _du_lieu_nho(), "BBB": _du_lieu_nho()}
    for theo_ngay in (False, True):
        for do_tre in (None, 1):
            ghi.clear()
            wf._mo_phong(du_lieu, 50.0,
                         str(tmp_path / f"wf_{theo_ngay}_{do_tre}.db"),
                         stride=2, min_history=60, che_do_hoc="tat",
                         duong_bo_nho=None, theo_ngay=theo_ngay,
                         do_tre_khop=do_tre)
            if theo_ngay:
                cho = [(sym, t, ck) for _, sym, t, ck in
                       wf.lich_theo_ngay(du_lieu, 60, 2, do_tre)]
            else:
                cho = [(sym, t, ck) for sym in sorted(du_lieu)
                       for t, ck in wf.diem_ghe(len(du_lieu[sym]), 60, 2,
                                                do_tre)]
            assert ghi == cho, (
                f"theo_ngay={theo_ngay} do_tre_khop={do_tre}: lịch sai. "
                f"nhận {len(ghi)} lời gọi, chờ {len(cho)}")
    print("PASS  cả hai chế độ truyền đúng lịch, cả hai giá trị do_tre_khop")
