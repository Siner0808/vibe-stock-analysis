"""Bảng kiểm XÁC ĐỊNH cho một ứng viên do MÁY soạn, chạy TRƯỚC khi người dùng thấy nó — BƯỚC 305.

Đặc tả: `vibe_logs_y23/DAC-TA-Y2.md` (nháp 25/11/2026; người dùng *"duyệt"* 25/11/2026 cùng ba khuyến nghị
mục 5). Ý mượn KHUNG của `edge-strategy-reviewer` (tradermonty/claude-trading-skills, MIT): kết luận PASS ·
REVISE · REJECT, và danh sách khai bắt buộc (bỏ ngỏ thì PASS bị hạ xuống REVISE). Không chép mã hay chữ,
không mượn trọng số nào của họ.

HÀM THUẦN: `kiem_phieu(phieu, so)` chỉ đọc hai dict nó nhận và trả `{"ket_luan", "muc"}`. KHÔNG BAO GIỜ:
đổi điểm/trọng số/ngưỡng của sổ; mở khoá một ứng viên (PASS không phải được duyệt, người dùng vẫn duyệt một
chạm, `qua_sang` luôn null, PASS không vào K); thay phép thử đã khai trước (không chấm, không tính IC);
đọc kết quả (không nhập `cham_xac_nhan`, `paper_*`, `sheets_store`, `run_daily`, không đọc giá/`*.db`/Sheets);
ghi sổ hay ghi file; tự nối vào `vong_hoc_gia`. Gác AST: `tests/test_kiem_de_xuat.py` mục 10.

PHIẾU = ứng viên cộng hai trường bảng kiểm cần, do bên soạn KHAI:
    {"ma": "UV-002",                                  # tuỳ chọn: bỏ dòng chính nó khỏi phép so với sổ
     "spec": {"loai": "trong_so", "trong_so": {...}},
     "dan_xuat": {"loai": "mono"|"bo_mot"|"deu"|"doi_cho"|"tay", "tham_so": [tên thành phần]},
     "da_doc_ket_qua_som": false}
Bốn dạng đầu của `dan_xuat.loai` đúng là bốn dạng của họ F (`thi_truong_gia.ho_spec_f`): `mono` = một thành
phần mang cả trọng số (tham_so: [c]); `bo_mot` = bộ mặc định bỏ c rồi chuẩn hoá về tổng 1 (tham_so: [c]);
`deu` = năm trọng số 0,2 (tham_so: []); `doi_cho` = bộ mặc định đổi chỗ trọng số của hai thành phần
(tham_so: [a, b]). `tay` = trọng số gõ tay (tham_so tuỳ ý, chỉ để đọc).

CÁC NGƯỠNG là ƯỚC LƯỢNG, chọn TRƯỚC khi nhìn kết quả của bất kỳ ứng viên nào và KHÔNG suy từ dữ liệu
(đặc tả mục 2); người dùng duyệt đúng bảng này. Chỉnh chúng theo kết quả ứng viên là vi phạm bất biến 7.
"""
from __future__ import annotations

PASS, REVISE, REJECT = "PASS", "REVISE", "REJECT"
_HANG = {PASS: 0, REVISE: 1, REJECT: 2}

#: Chép từ `cham_bong.THANH_PHAN` và `cham_bong.LOAI_SPEC`; module KHÔNG nhập `cham_bong` (nó kéo theo
#: `experiment_tran_dac_trung`, mà bảng kiểm không được ở gần phép chấm). `tests/test_kiem_de_xuat.py`
#: khoá hai bản chép bằng chính nguồn.
THANH_PHAN = ("trend_score", "momentum_score", "volume_score", "sr_score", "risk_score")
LOAI_SPEC = ("trong_so",)
#: Chép từ `thi_truong_gia.TRONG_SO_MAC_DINH` (= nhánh `else` của `master_agent`, bộ trọng số mặc định).
CO_SO = {"trend_score": 0.25, "momentum_score": 0.25, "volume_score": 0.20,
         "sr_score": 0.15, "risk_score": 0.15}

#: Mục 1: số tham số tự do của một phiếu `tay` = số trọng số > 0 trừ 1.
TU_DO_REVISE = 3
TU_DO_REJECT = 4
#: Mục 2: một trọng số `tay` phải là bội của bước này.
BUOC_TRONG_SO = 0.05
#: Mục 3: L1 tới bộ mặc định dưới sàn này là quá gần bản đang chạy để có lực.
SAN_L1 = 0.10
#: Mục 1: sai số tối đa của từng trọng số khi dựng lại phiếu đã khai nhãn từ `CO_SO`.
DUNG_SAI_DUNG_LAI = 1e-4
#: Mục 4: hai spec trùng khi MỌI |Δw| không quá sai số này.
DUNG_SAI_TRUNG = 1e-4
#: Mục 4: cùng tập thành phần dương với ít nhất ngần này dòng khác thì REVISE.
SO_DONG_CUNG_HO = 2

LOAI_DAN_XUAT = ("mono", "bo_mot", "deu", "doi_cho", "tay")
TEN_MUC = ("THAM_SO_TU_DO", "DO_CHINH_XAC", "QUA_GAN_BAN_CHAY", "TRUNG_LAP", "KHAI_BAT_BUOC")


# ── đọc đầu vào, nổ ValueError khi hỏng (không đoán) ─────────────────────────────────────────────────────

def _trong_so(spec) -> dict:
    """{thành phần: trọng số} đủ năm thành phần (vắng = 0). Cùng luật `cham_bong.kiem_spec`."""
    if not isinstance(spec, dict) or spec.get("loai") not in LOAI_SPEC:
        raise ValueError(f"loai ung vien khong nhan: {spec!r}")
    ts = spec.get("trong_so")
    if not isinstance(ts, dict) or not ts:
        raise ValueError("trong_so rong")
    la = set(ts) - set(THANH_PHAN)
    if la:
        raise ValueError(f"thanh phan ngoai tap: {sorted(la)}")
    try:
        w = {k: (float(ts[k]) if k in ts else 0.0) for k in THANH_PHAN}
    except (TypeError, ValueError):
        raise ValueError("trong so khong phai so") from None
    if any(x < 0 for x in w.values()):
        raise ValueError("trong so am")
    if abs(sum(w.values()) - 1.0) > 1e-9:
        raise ValueError("tong trong so phai bang 1")
    return w


def _dan_xuat(dx) -> tuple[str, list]:
    if not isinstance(dx, dict) or dx.get("loai") not in LOAI_DAN_XUAT:
        raise ValueError(f"dan_xuat.loai phai thuoc {LOAI_DAN_XUAT}: {dx!r}")
    ts = dx.get("tham_so")
    if not isinstance(ts, list) or any(t not in THANH_PHAN for t in ts):
        raise ValueError(f"dan_xuat.tham_so phai la danh sach ten thanh phan: {ts!r}")
    loai = dx["loai"]
    so_luong = {"mono": 1, "bo_mot": 1, "deu": 0, "doi_cho": 2}
    if loai in so_luong and len(ts) != so_luong[loai]:
        raise ValueError(f"dan_xuat {loai} can dung {so_luong[loai]} tham so, co {len(ts)}")
    if len(set(ts)) != len(ts):
        raise ValueError("dan_xuat.tham_so lap ten")
    return loai, ts


def _hang_so(so) -> dict:
    """{mã: trọng số} của MỌI dòng sổ, theo thứ tự sổ."""
    uv = so.get("ung_vien") if isinstance(so, dict) else None
    if not isinstance(uv, dict):
        raise ValueError("so thieu khoa ung_vien")
    ra = {}
    for ma, d in uv.items():
        try:
            ra[ma] = _trong_so(d["spec"] if isinstance(d, dict) and "spec" in d else None)
        except ValueError as e:
            raise ValueError(f"{ma}: {e}") from None
    return ra


# ── dựng lại từ bộ mặc định ──────────────────────────────────────────────────────────────────────────────

def _dung_lai(loai: str, ts: list) -> dict:
    if loai == "mono":
        return {k: (1.0 if k == ts[0] else 0.0) for k in THANH_PHAN}
    if loai == "bo_mot":
        con = {k: w for k, w in CO_SO.items() if k != ts[0]}
        tong = sum(con.values())
        return {k: (con[k] / tong if k in con else 0.0) for k in THANH_PHAN}
    if loai == "deu":
        return {k: 1.0 / len(THANH_PHAN) for k in THANH_PHAN}
    w = dict(CO_SO)                                      # doi_cho
    w[ts[0]], w[ts[1]] = w[ts[1]], w[ts[0]]
    return w


def _muc(stt: int, ket_qua: str, ly_do: str, do) -> dict:
    return {"stt": stt, "ten": TEN_MUC[stt - 1], "ket_qua": ket_qua, "ly_do": ly_do, "do": do}


# ── năm mục ──────────────────────────────────────────────────────────────────────────────────────────────

def _muc1(w: dict, dx) -> dict:
    if dx is None:
        return _muc(1, REVISE, "chưa khai dan_xuat nên chưa kiểm được số tham số tự do", None)
    loai, ts = dx
    if loai != "tay":
        lech = max(abs(w[k] - d) for k, d in _dung_lai(loai, ts).items())
        if lech <= DUNG_SAI_DUNG_LAI:
            return _muc(1, PASS, f"khớp bản dựng lại từ bộ mặc định ({loai}): 0 tham số tự do", 0)
        return _muc(1, REJECT, f"khai sai nhãn: không khớp bản dựng lại {loai} {ts} "
                               f"(lệch lớn nhất {lech:.4g} > {DUNG_SAI_DUNG_LAI:g})", 0)
    tu_do = sum(x > 0 for x in w.values()) - 1
    if tu_do >= TU_DO_REJECT:
        return _muc(1, REJECT, f"{tu_do} tham số tự do (>= {TU_DO_REJECT})", tu_do)
    if tu_do == TU_DO_REVISE:
        return _muc(1, REVISE, f"{tu_do} tham số tự do", tu_do)
    return _muc(1, PASS, f"{tu_do} tham số tự do", tu_do)


def _muc2(w: dict, dx) -> dict:
    if dx is None:
        return _muc(2, REVISE, "chưa khai dan_xuat nên chưa kiểm được độ chính xác của trọng số", None)
    if dx[0] != "tay":
        return _muc(2, PASS, "phiếu đã khai nhãn dựng lại được: không soát bội của 0,05", [])
    le = [k for k, x in w.items() if abs(x / BUOC_TRONG_SO - round(x / BUOC_TRONG_SO)) > 1e-6]
    if le:
        return _muc(2, REVISE, f"trọng số gõ tay không là bội của {BUOC_TRONG_SO:g}: {le}", le)
    return _muc(2, PASS, f"mọi trọng số là bội của {BUOC_TRONG_SO:g}", [])


def _muc3(w: dict) -> dict:
    l1 = round(sum(abs(w[k] - CO_SO[k]) for k in THANH_PHAN), 9)
    if l1 == 0:
        return _muc(3, REJECT, "trùng đúng bộ trọng số đang chạy (L1 = 0): không có lực mà vẫn tăng K", l1)
    if l1 < SAN_L1:
        return _muc(3, REVISE, f"quá gần bộ đang chạy: L1 = {l1:g} < {SAN_L1:g}", l1)
    return _muc(3, PASS, f"L1 = {l1:g} tới bộ đang chạy (sàn {SAN_L1:g})", l1)


def _muc4(w: dict, khac: dict) -> dict:
    duong = {k for k in THANH_PHAN if w[k] > 0}
    trung = [m for m, v in khac.items() if max(abs(w[k] - v[k]) for k in THANH_PHAN) <= DUNG_SAI_TRUNG]
    cung_ho = [m for m, v in khac.items() if {k for k in THANH_PHAN if v[k] > 0} == duong]
    do = {"trung": trung, "cung_ho": cung_ho}
    if trung:
        return _muc(4, REJECT, f"trùng dòng đã khai {trung} (mọi |Δw| <= {DUNG_SAI_TRUNG:g})", do)
    if len(cung_ho) >= SO_DONG_CUNG_HO:
        return _muc(4, REVISE, f"cùng tập thành phần dương với {len(cung_ho)} dòng khác: {cung_ho}", do)
    return _muc(4, PASS, f"không trùng dòng nào; cùng họ với {len(cung_ho)} dòng", do)


def _muc5(phieu: dict) -> dict:
    dx, doc = phieu.get("dan_xuat"), phieu.get("da_doc_ket_qua_som")
    if doc is not None and not isinstance(doc, bool):
        raise ValueError(f"da_doc_ket_qua_som phai la true/false: {doc!r}")
    thieu = [t for t, v in (("dan_xuat", dx), ("da_doc_ket_qua_som", doc)) if v is None]
    do = {"thieu": thieu, "da_doc_ket_qua_som": doc}
    if doc is True:
        return _muc(5, REJECT, "đã đọc kết quả trước ngày hẹn (docs/HANDOFF.md mục 5)", do)
    if thieu:
        return _muc(5, REVISE, f"bỏ ngỏ trường khai bắt buộc: {thieu}", do)
    return _muc(5, PASS, "đã khai đủ và chưa đọc kết quả sớm", do)


# ── điểm vào ─────────────────────────────────────────────────────────────────────────────────────────────

def kiem_phieu(phieu: dict, so: dict) -> dict:
    """Chạy năm mục trên MỘT phiếu và sổ ứng viên (`docs/ung-vien.json` đã đọc). Chỉ trả chữ.

    `ket_luan` là mục NẶNG NHẤT (REJECT > REVISE > PASS); không có điểm tổng. Đầu vào hỏng thì nổ
    ValueError (công cụ dòng lệnh đổi nó thành "chưa kiểm được"), không đoán.
    """
    if not isinstance(phieu, dict):
        raise ValueError("phieu phai la mot dict")
    w = _trong_so(phieu.get("spec"))
    dx = None if phieu.get("dan_xuat") is None else _dan_xuat(phieu["dan_xuat"])
    khac = {m: v for m, v in _hang_so(so).items() if m != phieu.get("ma")}
    muc = [_muc1(w, dx), _muc2(w, dx), _muc3(w), _muc4(w, khac), _muc5(phieu)]
    return {"ket_luan": max((m["ket_qua"] for m in muc), key=_HANG.__getitem__), "muc": muc}
