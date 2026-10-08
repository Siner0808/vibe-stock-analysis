"""Workflow `soat-tuan.yml` và `tools/soat_tuan.py` — BƯỚC 164 (giai đoạn A2).

Người dùng "Đồng ý" ngày 08/10/2026: soát định kỳ tự động mỗi tuần. Phần máy làm
được chạy trên runner; phần PHÁN lời khai vẫn là lượt soát của agent. Các gác
dưới đây giữ ba điều dễ trôi: (1) nhịp 7 ngày khớp dòng hạn của HANDOFF, (2) job
KHÔNG đỏ vì có lời khai cần phán (luật chuông: báo động giả), (3) job không kéo
gói ngoài thư viện chuẩn và không chạy máy đo đường ngoài repo.
"""
import ast
import datetime as dt
import json
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))

import cua_mo_phien as mp  # noqa: E402
import soat_tuan as st  # noqa: E402

WF = GOC / ".github" / "workflows" / "soat-tuan.yml"
TOOL = GOC / "tools" / "soat_tuan.py"


def _wf() -> str:
    return WF.read_text(encoding="utf-8")


def _dong_lenh(van: str) -> str:
    """Bỏ dòng chú thích: gác này hỏi workflow LÀM gì, không hỏi nó NÓI gì."""
    return "\n".join(d for d in van.splitlines() if not d.lstrip().startswith("#"))


# ── nhịp ─────────────────────────────────────────────────────────────────

def test_NHIP_la_7_ngay_quyet_dinh_nguoi_dung_08_10_2026():
    """Người dùng chốt 2 ngày (16/09/2026) rồi "Đồng ý" soát tự động mỗi tuần
    (08/10/2026). Ghim như một QUYẾT ĐỊNH — nâng hay hạ nó phải sửa test này."""
    assert mp.NHIP_SOAT_NGAY == 7


def test_HAN_luot_ke_trong_HANDOFF_bang_ngay_luot_cuoi_cong_NHIP():
    """Hạn = ngày LÀM lượt trước + nhịp (lượt 11 làm 08/10 → lượt 12 hạn 15/10).
    Lượt 11 từng ghi hạn tính từ ngày HẠN của lượt 10 chứ không từ ngày LÀM
    (BƯỚC 163) — gác này đọc thẳng từ sổ để lỗi ấy không quay lại."""
    so = json.loads((GOC / "docs" / "soat-dinh-ky.json").read_text(encoding="utf-8"))
    luot = so["lan_soat"]
    cuoi = max(dt.date.fromisoformat(x["ngay"]) for x in luot)
    ke = len(luot) + 1
    van = " ".join((GOC / "docs" / "HANDOFF.md").read_text(encoding="utf-8").split())
    m = re.search(rf"Lượt {ke}: (\d{{2}})/(\d{{2}})", van)
    assert m, f"HANDOFF khong neu han cua luot {ke}"
    han = dt.date(cuoi.year, int(m.group(2)), int(m.group(1)))
    assert han == cuoi + dt.timedelta(days=mp.NHIP_SOAT_NGAY), (han, cuoi)


# ── phép phán thuần ──────────────────────────────────────────────────────

def _nguon(chua_mo=0, da_mo=1, ngay_cuoi=dt.date(2026, 10, 8), thieu=()):
    khoi = ([("a.md", i, f"loi khai {i}", None) for i in range(chua_mo)]
            + [("b.md", i, f"da mo {i}", ("2026-10-01", "THẬT")) for i in range(da_mo)])
    return {"khoi": khoi, "so_loi_khai": len(khoi), "ngay_cuoi": ngay_cuoi,
            "so_luot": 11, "thieu_so": list(thieu)}


def test_QUA_HAN_dung_ranh_gioi_nhip():
    hn = dt.date(2026, 10, 15)
    assert st.danh_gia(_nguon(), hn, 7)["qua_han"] is True          # 7 ngày = tới hạn
    assert st.danh_gia(_nguon(), dt.date(2026, 10, 14), 7)["qua_han"] is False
    assert st.danh_gia(_nguon(), hn, 7)["tre_ngay"] == 7


def test_CANH_BAO_chi_xuat_hien_khi_co_dieu_can_noi():
    sach = st.canh_bao(st.danh_gia(_nguon(), dt.date(2026, 10, 9), 7))
    assert sach == []
    ban = st.canh_bao(st.danh_gia(_nguon(chua_mo=2, thieu=["BƯỚC 170"]),
                                  dt.date(2026, 10, 20), 7))
    assert len(ban) == 3 and all(d.startswith("::warning ") for d in ban), ban
    assert "2/3" in ban[0] and "quá nhịp" in ban[1] and "BƯỚC 170" in ban[2]


def test_KHONG_BAO_GIO_phat_error_vi_co_loi_khai_can_phan():
    """Luật chuông: việc người phải làm KHÔNG làm đỏ job."""
    kq = st.danh_gia(_nguon(chua_mo=40, thieu=["BƯỚC 1"]), dt.date(2027, 1, 1), 7)
    assert not any("::error" in d for d in st.canh_bao(kq))


def test_THOAT_ky_tu_dac_biet_cua_chu_thich():
    assert st._thoat("a%b\nc\rd") == "a%25b%0Ac%0Dd"


def test_TOM_TAT_markdown_nen_co_so_do_va_chan_danh_sach_dai():
    kq = st.danh_gia(_nguon(chua_mo=45), dt.date(2026, 10, 9), 7)
    md = st.tom_tat_md(kq, dt.date(2026, 10, 9))
    assert "chưa ai mở: **45**" in md and "và 15 câu nữa" in md
    assert md.count("\n- `a.md:") == st.TOI_DA_DONG_IN
    assert "kiem_duong_ngoai_repo" in md, "tom tat phai noi ro phan KHONG chay"


# ── máy đọc thật ─────────────────────────────────────────────────────────

def test_DOC_NGUON_THAT_cho_ra_so_hop_ly_va_main_thoat_0(tmp_path, capsys):
    nguon = st.doc_nguon()
    assert nguon["so_loi_khai"] > 10, "may quet doc hut tai lieu"
    assert nguon["so_luot"] >= 11
    ra = tmp_path / "tom_tat.md"
    assert st.main(["--tom-tat", str(ra)]) == 0
    assert "Soát tuần" in ra.read_text(encoding="utf-8")
    assert "soat-tuan:" in capsys.readouterr().out


def test_MAY_HONG_thi_DO_khong_xanh_im(tmp_path):
    """Thư mục không có tài liệu nào → `ChuaDoc` (job đỏ), không phải '0 lời khai'."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "soat-dinh-ky.json").write_text(
        json.dumps({"lan_soat": [{"ngay": "2026-10-08"}]}), encoding="utf-8")
    (tmp_path / "docs" / "soat-notebooklm.json").write_text(
        json.dumps({"soat": {}, "_moc_buoc": 81}), encoding="utf-8")
    (tmp_path / "docs" / "STATE.md").write_text("# s\n", encoding="utf-8")
    with pytest.raises(st.ChuaDoc, match="RONG"):
        st.doc_nguon(tmp_path)
    (tmp_path / "docs" / "soat-dinh-ky.json").unlink()
    with pytest.raises(st.ChuaDoc, match="khong doc duoc"):
        st.doc_nguon(tmp_path)


def test_DUNG_CU_khong_nhap_goi_ngoai_thu_vien_chuan():
    """Job không `pip install`, nên mọi import phải là thư viện chuẩn hoặc tools/."""
    cay = ast.parse(TOOL.read_text(encoding="utf-8"))
    ten = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ten |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ten.add(n.module.split(".")[0])
    cho_phep = set(sys.stdlib_module_names) | {"cua_mo_phien", "soat_loi_khai_cu"}
    la = ten - cho_phep
    assert not la, f"soat_tuan.py nhap goi ngoai thu vien chuan: {sorted(la)}"
    assert "vnstock" not in ten


# ── workflow ─────────────────────────────────────────────────────────────

def test_WORKFLOW_cron_MOT_lan_moi_tuan_va_cho_chay_tay():
    van = _wf()
    cron = re.findall(r"^\s*-\s*cron:\s*'([^']+)'\s*$", van, re.M)
    assert len(cron) == 1, cron
    phut, gio, ngay_thang, thang, thu = cron[0].split()
    assert (ngay_thang, thang) == ("*", "*") and thu.isdigit() and 0 <= int(thu) <= 6, (
        f"cron {cron[0]!r} khong phai mot lan moi tuan")
    assert "workflow_dispatch:" in van


def test_WORKFLOW_chay_dung_cong_cu_va_ghi_ra_STEP_SUMMARY():
    lenh = _dong_lenh(_wf())
    assert 'python tools/soat_tuan.py --tom-tat "$GITHUB_STEP_SUMMARY"' in lenh


def test_WORKFLOW_khong_lam_do_job_vi_loi_khai_va_khong_keo_goi():
    lenh = _dong_lenh(_wf())
    for cam in ("exit 1", "::error", "pip install", "vnstock", "kiem_duong_ngoai_repo",
                "continue-on-error"):
        assert cam not in lenh, f"workflow chua {cam!r}"
    assert "permissions:\n  contents: read" in lenh


def test_WORKFLOW_ghi_ro_ly_do_khong_chay_cong_cu_do_duong_ngoai_repo():
    """Lý do viết bằng lời, KHÔNG nêu tên công cụ: gác `test_CONG_CU_NAY_CO_Y_KHONG_nam_trong_CI`
    (file test của công cụ ấy) cấm tên ấy xuất hiện trong mọi workflow."""
    van = _wf()
    assert "KHÔNG CHẠY công cụ đo đường NGOÀI repo" in van
    assert "kiem_duong_ngoai_repo" not in van  # van-ban-ok: dang kiem VAN BAN workflow (YAML), khong co ma nguon de doc bang AST


def test_WORKFLOW_khong_vien_doi_phut_de_ne_tre():
    """CLAUDE.md, mục Quét tự động: đổi cron sang lệch :00/:30 KHÔNG có tác dụng
    (BƯỚC 89, 101). Workflow chỉ được nhắc điều đó như một lời PHỦ NHẬN."""
    van = _wf()
    assert "KHÔNG cứu" in van and "đừng viện nó" in van


# ── phát đục lô B (BƯỚC 164): sáu chỗ của máy hằng tuần chưa có gác ───────────────

def _goc_tam(tmp_path, ngay=("2026-10-08", "2026-10-01")):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "soat-dinh-ky.json").write_text(
        json.dumps({"lan_soat": [{"ngay": n} for n in ngay]}), encoding="utf-8")
    (tmp_path / "docs" / "soat-notebooklm.json").write_text(
        json.dumps({"soat": {}, "_moc_buoc": 81}), encoding="utf-8")
    (tmp_path / "docs" / "STATE.md").write_text("# s\n", encoding="utf-8")
    return tmp_path


def test_DOC_NGUON_lay_NGAY_MOI_NHAT_va_dem_dung_so_luot(tmp_path, monkeypatch):
    """Lượt không xếp theo thứ tự: ngày cuối phải là `max`, số lượt là độ dài danh sách."""
    monkeypatch.setattr(st.sk, "loi_khai_con_song",
                        lambda goc=None: [("a.md", 1, "loi khai mot")])
    nguon = st.doc_nguon(_goc_tam(tmp_path, ("2026-10-01", "2026-10-08", "2026-10-03")))
    assert nguon["ngay_cuoi"] == dt.date(2026, 10, 8)
    assert nguon["so_luot"] == 3


def test_MAIN_may_hong_thi_in_error_va_tra_ma_2(monkeypatch, capsys):
    """Chỉ MÁY hỏng mới được đỏ job (`::error`, mã 2); lời khai cần phán thì không."""
    def hong(*a, **k):
        raise st.ChuaDoc("khong doc duoc nguon")
    monkeypatch.setattr(st, "doc_nguon", hong)
    assert st.main([]) == 2
    out = capsys.readouterr().out
    assert out.startswith("::error title=") and "khong doc duoc nguon" in out


def test_TOM_TAT_NOI_THEM_vao_tep_co_san_khong_ghi_de(tmp_path):
    """`$GITHUB_STEP_SUMMARY` có thể đã chứa chữ của bước khác trong cùng job."""
    ra = tmp_path / "summary.md"
    ra.write_text("bước trước đã viết\n", encoding="utf-8")
    assert st.main(["--tom-tat", str(ra)]) == 0
    van = ra.read_text(encoding="utf-8")
    assert van.startswith("bước trước đã viết\n") and "Soát tuần" in van


def test_CAT_8_BUOC_chua_khai_o_ca_canh_bao_lan_tom_tat():
    thieu = [f"B{n:02d}" for n in range(1, 13)]
    kq = st.danh_gia(_nguon(thieu=thieu), dt.date(2026, 10, 9), 7)
    cb = [d for d in st.canh_bao(kq) if "BƯỚC chưa khai" in d][0]
    md = st.tom_tat_md(kq, dt.date(2026, 10, 9))
    for van in (cb, md):
        ten = {t.strip(" ,.()") for t in van.replace(":", " ").split()}
        assert {"B01", "B08"} <= ten and "B09" not in ten, van
    assert "**12**" in md
