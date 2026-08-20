"""Phương án C — bộ nhớ chỉ được sinh từ lệnh THẬT, và phải khai nguồn gốc.

Đo ngày 20/08/2026 trên `sl_pattern_memory.json`:

    6.327 mẫu · 100 mã · tín hiệu 2021-11 → 2026-07
    trường nói vòng nào / dữ liệu nào sinh ra:  KHÔNG CÓ
    khớp một lệnh THẬT trong sổ:      56/6.327 =  0,89%
    không ứng với lệnh thật nào:   6.271/6.327 = 99,1%

Rổ thật 71 mã, sổ thật 113 lệnh — không cách nào sinh ra 6.327 mẫu từ 100
mã. Toàn bộ là dư lượng của các vòng seed/tối ưu in-sample, gồm cả những
vòng đã bị bất biến 7 tuyên bố vô hiệu.

Vì sao KHÔNG chọn phương án B (giữ file, ghi provenance): thông tin để truy
nguồn **không tồn tại**. Các vòng sinh ra nó đã bị `os.remove()` xoá.

Phương án C giữ nguyên cơ chế, chỉ thay dữ liệu bẩn bằng dữ liệu thật. Hệ
quả đo được: độ phủ 49,4% → 0,9%, tức cơ chế gần như vô hiệu. Đó là câu
trả lời trung thực với 44 lệnh cắt lỗ, và nó lớn lên trung thực khi sổ dày
lên — khác hẳn một cơ chế bịa đang trừ 12 điểm cho 92,5% tín hiệu.

Điều kiện sống còn: mỗi mẫu phải MANG NGUỒN. Không có nó thì sau vài tháng
C thoái hoá đúng thành cái blob không truy nguồn được như hiện nay.
"""
import json
import sys
import tempfile
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import post_mortem_learning as pml

BD = {"trend_score": 65, "momentum_score": 60, "volume_score": 55}


def test_ghi_mau_KHONG_co_nguon_thi_bi_tu_choi():
    """Không khai nguồn thì không được vào bộ nhớ."""
    with tempfile.TemporaryDirectory() as d:
        e = pml.PostMortemLearningEngine(str(Path(d) / "m.json"), enabled=True)
        ok = e.record_sl_trade("AAA", 70, BD, [], signal_date="2026-01-05")
        assert ok is False, "ghi được mẫu không có nguồn gốc"
        assert e.sl_patterns == []
    print("PASS  mẫu không khai nguồn bị từ chối")


def test_ghi_mau_co_nguon_thi_duoc_va_luu_du_provenance():
    with tempfile.TemporaryDirectory() as d:
        e = pml.PostMortemLearningEngine(str(Path(d) / "m.json"), enabled=True)
        ok = e.record_sl_trade("AAA", 70, BD, ["lý do"],
                               signal_date="2026-01-05",
                               trade_id=42, nguon="paper_trades.db")
        assert ok is True
        p = e.sl_patterns[0]
        for truong in ("nguon", "trade_id", "ghi_luc"):
            assert truong in p, f"thiếu trường {truong}: {sorted(p)}"
        assert p["trade_id"] == 42
    print("PASS  mẫu có nguồn được ghi, kèm đủ provenance")


def test_nap_file_cu_thi_BO_QUA_mau_khong_co_nguon_va_NOI_RA():
    """File 6.327 mẫu hiện tại không có provenance — phải bị bỏ, không im."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "m.json"
        f.write_text(json.dumps([
            {"symbol": "OLD", "signal_date": "2024-01-01", "entry_score": 60,
             "trend_score": 65, "momentum_score": 60, "volume_score": 55},
            {"symbol": "NEW", "signal_date": "2024-02-01", "entry_score": 60,
             "trend_score": 65, "momentum_score": 60, "volume_score": 55,
             "nguon": "paper_trades.db", "trade_id": 7},
        ]), encoding="utf-8")

        ra = io.StringIO()
        with redirect_stdout(ra):
            e = pml.PostMortemLearningEngine(str(f), enabled=True)

    assert len(e.sl_patterns) == 1 and e.sl_patterns[0]["symbol"] == "NEW", (
        f"nạp cả mẫu không nguồn: {[p['symbol'] for p in e.sl_patterns]}")
    assert "1" in ra.getvalue(), f"bỏ mẫu mà không nói ra: {ra.getvalue()!r}"
    print("PASS  mẫu không nguồn bị bỏ khi nạp, và có nói ra")


def test_dung_lai_tu_so_lenh_chi_lay_lenh_CAT_LO_that():
    """Công cụ dựng lại chỉ được đọc lệnh đã đóng bằng cắt lỗ."""
    sys.path.insert(0, str(GOC / "tools"))
    import dung_lai_bo_nho as dl

    import paper_trading as pt
    pt.CHO_PHEP_MO_LENH_MOI = True

    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "s.db")
        j = pt.PaperTradingJournal(db)
        j.db.execute(
            "INSERT INTO trades (symbol, signal_date, entry_date, entry_price,"
            " exit_date, exit_price, exit_reason, status, stop_loss,"
            " take_profit, size_pct, entry_score, components, reasons)"
            " VALUES ('AAA','2026-01-05','2026-01-06',100,'2026-02-01',90,"
            " 'STOP_LOSS','CLOSED',90,120,10,70,?,'[]')",
            (json.dumps(BD),))
        j.db.execute(
            "INSERT INTO trades (symbol, signal_date, entry_date, entry_price,"
            " exit_date, exit_price, exit_reason, status, stop_loss,"
            " take_profit, size_pct, entry_score, components, reasons)"
            " VALUES ('BBB','2026-01-05','2026-01-06',100,'2026-02-01',120,"
            " 'TAKE_PROFIT','CLOSED',90,120,10,70,?,'[]')",
            (json.dumps(BD),))
        j.db.commit()
        j.db.close()

        mau = dl.dung_lai(db)

    assert len(mau) == 1 and mau[0]["symbol"] == "AAA", (
        f"lấy cả lệnh không phải cắt lỗ: {[m['symbol'] for m in mau]}")
    assert mau[0]["nguon"] and mau[0]["trade_id"]
    print("PASS  chỉ dựng lại từ lệnh CẮT LỖ thật, kèm nguồn")


def test_khong_con_khang_dinh_Self_Improving():
    """Gate 6 điều kiện 3: hoặc bỏ dòng đó, hoặc nó mô tả đúng thứ đang chạy.

    "Self-Improving AI (Post-Mortem Memory Loop ACTIVE)" sai ở hai mức:
      • bộ nhớ cũ là 6.271/6.327 mẫu không truy được về lệnh nào — nó không
        học, nó lặp lại kết quả của chính các vòng tối ưu;
      • `save_memory()` không được gọi ở BẤT KỲ đâu, nên nó không tích luỹ.
    """
    import ast
    import tokenize

    vi_pham = []
    for f in sorted(GOC.glob("*.py")):
        with open(f, "rb") as fh:
            toks = list(tokenize.tokenize(fh.readline))
        # Chỉ soi CHUỖI: một chú thích giải thích vì sao câu đó sai thì
        # không phải là tái phạm câu đó.
        for t in toks:
            if t.type == tokenize.STRING and "Self-Improving" in t.string:
                vi_pham.append(f"{f.name}:{t.start[0]}")
    assert not vi_pham, (
        "vẫn khẳng định 'Self-Improving' ở: " + ", ".join(vi_pham))
    print("PASS  không còn khẳng định Self-Improving trong chuỗi in ra")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()
