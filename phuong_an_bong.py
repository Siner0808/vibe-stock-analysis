"""Sổ phương án BÓNG của sân đấu C1 — luật của file `docs/phuong-an-bong.json` (BƯỚC 242, Lát 3a).

Module THUẦN (không git, không đĩa, không mạng): phán MỘT phiên bản sổ, và phán một phiên bản so với
các phiên bản CHA của nó trong git (`docs/thiet-ke-c1-san-dau.md` mục 9). Phần ĐI THEO CẠNH lịch sử
git nằm ở `tests/test_phuong_an_bong_git.py` (khuôn `tests/test_tien_dang_ky_git.py`); phần dựng
cấu hình từ một dòng sổ nằm ở `san_dau.cau_hinh_tu_phuong_an`.

Khuôn `cham_bong.vi_pham_tien_dang_ky`, nhưng sổ này KHÔNG phải sổ ứng viên: phương án bóng thăm dò
không tính vào K và không có đường lên bản. Vì thế id mang tiền tố `PB-` và chỉ tiền tố ấy được nhận.

Sáu luật, phán trên MỖI cạnh cha → con:
  (a) dòng MỚI (không cha nào có) phải mang `commit: null`;
  (e) `khai_ngay` = ngày COMMITTER (giờ VN) của commit đầu tiên có dòng — khai lùi ngày là nhận dữ
      liệu đã nhìn làm "chưa nhìn";
  (b) `lop`, `bo_co`, `mo_ta`, `ly_do`, `khai_ngay` không đổi ở mọi phiên bản sau;
  (c) `commit` chỉ đi `null` → mã băm đầy đủ, đúng MỘT lần, và mã băm ấy phải bằng commit đầu tiên
      có dòng (`commit_dau`, do bộ đi theo cạnh tính bằng git);
  (d) không dòng nào của một cha bị xoá;
  (f) `lop` ∈ {`tham_do`}; id mang `PB-`; `bo_co` hợp lệ (`vi_pham_bo_co`).
"""
from __future__ import annotations

import re
from typing import Any

#: Lớp phương án. `xac_nhan` bị từ chối cho tới C2 (đặc tả mục 9).
LOP_HOP_LE = ("tham_do",)

#: Id hợp lệ: `PB-nnn`.
MAU_ID = re.compile(r"^PB-\d{3}$")

#: Ngày khai: `YYYY-MM-DD`.
MAU_NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: Mã băm đầy đủ của một commit git.
MAU_BAM = re.compile(r"^[0-9a-f]{40}$")

#: Trường KHÔNG được đổi sau commit khai. `commit` là trường duy nhất điền sau.
TRUONG_BAT_BIEN = ("lop", "bo_co", "mo_ta", "ly_do", "khai_ngay")

#: Cờ của `CauHinhVao` mà C1 CHƯA có nguồn tiêm (đặc tả mục 5 khoản 4): IMOM và chốt sụt giảm của sổ
#: giữ đường module, nên không phương án nào được ghi đè chúng.
CO_CHUA_TIEM = ("loc_imom_phan_vi", "chot_sut_giam_nguong", "chot_sut_giam_phien")

_THIEU = object()


def kieu_co() -> dict[str, str]:
    """{tên trường của `CauHinhVao`: kiểu khai ở nguồn (`bool`, `int`, `float`, `str`)}."""
    import dataclasses

    import paper_trading as pt
    return {f.name: str(f.type) for f in dataclasses.fields(pt.CauHinhVao)}


def _dung_kieu(kieu: str, v: Any) -> bool:
    if kieu == "bool":
        return isinstance(v, bool)
    if kieu == "int":
        return isinstance(v, int) and not isinstance(v, bool)
    if kieu == "float":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if kieu == "str":
        return isinstance(v, str)
    return False


def vi_pham_bo_co(bo_co: Any) -> list[str]:
    """Vi phạm của MỘT `bo_co`: phải là dict không rỗng; khoá là tên trường của `CauHinhVao` (kể cả
    `luat_vao`), kiểu giá trị đúng; không khoá nào thuộc `CO_CHUA_TIEM`; `luat_vao` thuộc `LUAT_VAO`."""
    import paper_trading as pt

    if not isinstance(bo_co, dict) or not bo_co:
        return ["bo_co phai la dict khong rong (f)"]
    kieu = kieu_co()
    loi = []
    for khoa, v in bo_co.items():
        if khoa not in kieu:
            loi.append(f"bo_co co khoa {khoa!r} khong phai truong cua CauHinhVao (f)")
        elif khoa in CO_CHUA_TIEM:
            loi.append(f"bo_co {khoa!r}: chua co nguon tiem trong C1 (f)")
        elif not _dung_kieu(kieu[khoa], v):
            loi.append(f"bo_co {khoa!r}={v!r}: kieu phai la {kieu[khoa]} (f)")
        elif khoa == "luat_vao" and v not in pt.LUAT_VAO:
            loi.append(f"bo_co luat_vao={v!r}: chi nhan {pt.LUAT_VAO} (f)")
    return loi


def _vi_pham_dong(ma: str, d: Any) -> list[str]:
    """Luật (f) cho MỘT dòng: id, lớp, bo_co, dạng của `khai_ngay` và `commit`."""
    loi = []
    if not MAU_ID.match(ma):
        loi.append(f"{ma}: id phai co dang PB-nnn (f)")
    if not isinstance(d, dict):
        return loi + [f"{ma}: dong khong phai dict (f)"]
    if d.get("lop") not in LOP_HOP_LE:
        loi.append(f"{ma}: lop {d.get('lop')!r} khong thuoc {LOP_HOP_LE} (f)")
    loi += [f"{ma}: {x}" for x in vi_pham_bo_co(d.get("bo_co"))]
    kn = d.get("khai_ngay")
    if not (isinstance(kn, str) and MAU_NGAY.match(kn)):
        loi.append(f"{ma}: khai_ngay {kn!r} khong phai YYYY-MM-DD (f)")
    cm = d.get("commit", _THIEU)
    if cm is _THIEU or not (cm is None or (isinstance(cm, str) and MAU_BAM.match(cm))):
        loi.append(f"{ma}: commit {cm!r} phai la null hoac ma bam day du 40 ky tu (f)")
    for t in ("mo_ta", "ly_do"):
        if not (isinstance(d.get(t), str) and d[t].strip()):
            loi.append(f"{ma}: thieu {t} (f)")
    return loi


def vi_pham_so(so: Any) -> list[str]:
    """Luật (f) cho MỘT phiên bản sổ (đứng một mình, không cần git)."""
    pa = so.get("phuong_an") if isinstance(so, dict) else None
    if not isinstance(pa, dict):
        return ["khong doc duoc khoa phuong_an"]
    loi = []
    for ma, d in pa.items():
        loi += _vi_pham_dong(ma, d)
    return loi


def vi_pham_tien_dang_ky(con: dict, cha: list[dict], ngay_commit: str,
                         commit_dau: dict[str, str]) -> list[str]:
    """Phán một phiên bản sổ (`con`) so với MỌI phiên bản cha của nó trong git. Rỗng là sạch.

    `cha` rỗng = commit tạo file; commit gộp có hai cha — dòng có ở MỘT cha là dòng đã khai.
    `ngay_commit` = ngày COMMITTER của `con` theo giờ VN. `commit_dau` = {id: mã băm đầy đủ của commit
    đầu tiên có dòng ấy} do bộ đi theo cạnh tính; thiếu id thì luật (c) không thể xác nhận một mã băm.
    """
    loi = vi_pham_so(con)
    pa = con.get("phuong_an") if isinstance(con, dict) else None
    if not isinstance(pa, dict):
        return loi
    pa_cha = [c["phuong_an"] for c in cha
              if isinstance(c, dict) and isinstance(c.get("phuong_an"), dict)]
    for ma, d in pa.items():
        if not isinstance(d, dict) or any(ma in u for u in pa_cha):
            continue
        if d.get("commit", _THIEU) is not None:
            loi.append(f"{ma}: commit khai phai mang commit null (a)")
        if d.get("khai_ngay") != ngay_commit:
            loi.append(f"{ma}: khai_ngay {d.get('khai_ngay')} khac ngay commit khai "
                       f"{ngay_commit} gio VN (e)")
    for u in pa_cha:
        for ma, p in u.items():
            if ma not in pa:
                loi.append(f"{ma}: dong da khai bi xoa (d)")
                continue
            d = pa[ma]
            if not isinstance(d, dict) or not isinstance(p, dict):
                continue
            doi = [t for t in TRUONG_BAT_BIEN if d.get(t, _THIEU) != p.get(t, _THIEU)]
            if doi:
                loi.append(f"{ma}: sua truong da khai {doi} (b)")
            c_p, c_c = p.get("commit", _THIEU), d.get("commit", _THIEU)
            if c_p is None:
                hop_le = c_c is None or (isinstance(c_c, str) and c_c == commit_dau.get(ma, _THIEU))
            else:
                hop_le = c_c == c_p
            if not hop_le:
                loi.append(f"{ma}: commit {c_p!r} -> {c_c!r}; chi duoc null -> ma bam cua commit "
                           f"dau tien co dong ({commit_dau.get(ma)!r}) mot lan (c)")
    return loi
