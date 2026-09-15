"""Trần vốn: phép so phải trừ bụi float, và phải in đủ số lẻ để đọc được.

LỖI 65 (15/09/2026) — `_capital_deployment` cộng dồn `+size` rồi `-size`
theo từng mốc ngày. Mọi `size_pct` là bội số của 0,1 điểm, mà 0,1 không
biểu diễn chính xác được bằng nhị phân. Một danh mục chạm **đúng** trần
100% cho ra `100.0000000000001`, và ba chỗ tự viết `> 100.0` cùng kêu
"ĐÒN BẨY ẨN" trong khi `consider_entry` vừa giữ trần chính xác từng chữ số.

Hai mặt của cùng một lỗi, và test này canh cả hai:

  PHÁN   ba nơi so với trần phải đi qua `paper_metrics.vuot_tran_von()`
  IN     vốn đỉnh in `.0f` thì 99,9 · 100,0 · 100,4 ra cùng chuỗi "100%",
         nên người đọc không kiểm được phán quyết bằng chính con số bên cạnh

Ca thật dùng ở đây KHÔNG phải số bịa: 18 vị thế mở ngày 2023-05-17 trong
lượt D của ĐO 9, đọc thẳng từ `wf_oos.db` của lượt ấy.
"""
import ast
import sys
from decimal import Decimal
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import paper_metrics  # noqa: E402
import walkforward as wf  # noqa: E402
from paper_trading import TRAN_VON_CAM_KET_PCT, Trade  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

#: 18 vị thế đang mở ngày 2023-05-17, lượt D của ĐO 9 (15/09/2026).
#: (mã, ngày vào, ngày ra, size_pct) — đọc từ sổ của chính lượt chạy ấy.
CA_THAT = [
    ("AAA", "2023-05-09", "2023-06-19", 5.3),
    ("CII", "2023-05-09", "2023-05-26", 6.1),
    ("GIL", "2023-05-09", "2023-06-05", 5.3),
    ("HHP", "2023-05-09", "2023-05-26", 5.3),
    ("HUT", "2023-05-09", "2023-07-17", 6.0),
    ("MBS", "2023-05-09", "2023-07-31", 5.3),
    ("MSR", "2023-05-09", "2023-05-18", 5.3),
    ("NAF", "2023-05-09", "2023-07-31", 5.3),
    ("NVL", "2023-05-09", "2023-05-26", 5.3),
    ("OIL", "2023-05-09", "2023-05-25", 6.0),
    ("PVD", "2023-05-09", "2023-07-05", 7.9),
    ("SHS", "2023-05-09", "2023-05-19", 5.3),
    ("VCB", "2023-05-09", "2023-05-18", 4.2),
    ("VIX", "2023-05-09", "2023-05-18", 5.3),
    ("VTP", "2023-05-09", "2023-05-24", 5.3),
    ("DHG", "2023-05-15", "2023-06-27", 5.3),
    ("BAF", "2023-05-17", "2023-05-18", 3.3),
    ("DPM", "2023-05-17", "2023-05-22", 8.2),
]

#: Ca TỐI THIỂU tái lập được bụi từ đầu tới cuối, tìm bằng dò máy.
#:
#: VÌ SAO KHÔNG DÙNG THẲNG 18 VỊ THẾ THẬT: bụi ở lượt D không sinh ra từ 18
#: vị thế ấy — nó là dư tích luỹ của **297 lệnh** đã vào trước mốc 2023-05-17.
#: Cộng riêng 18 vị thế cho ra 99,99999999999999, tức DƯỚI trần. Dấu của bụi
#: đổi theo cả lịch sử phép cộng, nên một fixture 18 dòng KHÔNG tái lập được
#: lỗi thật — và nếu cứ viết như thế thì test xanh mà chẳng đo gì.
#:
#: Năm con số dưới đây cộng Decimal ra ĐÚNG 100,0 và cộng float ra
#: 100,00000000000001 — cùng cơ chế, cỡ nhỏ nhất dò được.
CA_TOI_THIEU = [
    ("AAA", "2023-05-09", "2023-06-08", 22.8),
    ("BBB", "2023-05-09", "2023-06-09", 19.7),
    ("CCC", "2023-05-09", "2023-06-10", 20.7),
    ("DDD", "2023-05-09", "2023-06-11", 20.6),
    ("EEE", "2023-05-09", "2023-06-12", 16.2),
]

#: Bụi đo được trên lượt D thật (đỉnh float 100,0000000000001 so với
#: Decimal 100,0000). Dùng làm biên DƯỚI của dung sai.
BUI_DO_DUOC = 1e-13

#: Bước yết của `size_pct`. Dùng làm biên TRÊN: một vị thế thật không thể
#: nhỏ hơn bước yết, nên dung sai phải nhỏ hơn hẳn nó.
BUOC_YET_SIZE_PCT = 0.1


def _lenh(ma: str, vao: str, ra: str, size: float, i: int) -> Trade:
    return Trade(id=i, symbol=ma, signal_date=vao, entry_date=vao,
                 entry_price=20_000.0, exit_date=ra, exit_price=20_500.0,
                 exit_reason="TAKE_PROFIT", stop_loss=19_000.0,
                 take_profit=24_000.0, size_pct=size, entry_score=62,
                 status="CLOSED")


def _dung(bang: list) -> list[Trade]:
    return [_lenh(ma, vao, ra, size, i)
            for i, (ma, vao, ra, size) in enumerate(bang, start=1)]


def test_tran_giu_DUNG_tren_ca_that():
    """18 vị thế thật ngày đỉnh: tổng chính xác là ĐÚNG 100,0.

    Đây là điều báo cáo đã gọi là "ĐÒN BẨY ẨN". `consider_entry` giữ trần
    chính xác tới chữ số cuối — không có một xu nào vay mượn. Thứ hỏng nằm
    ở phép so, không ở cái trần.
    """
    chinh_xac = sum(Decimal(str(s)) for _, _, _, s in CA_THAT)
    assert chinh_xac == Decimal("100.0"), (
        f"ca thật phải chạm ĐÚNG trần 100%, đo được {chinh_xac}")
    assert not paper_metrics.vuot_tran_von(float(chinh_xac)), (
        "chạm đúng trần mà vẫn bị kêu vượt — đây là lỗi 65")
    print(f"PASS  ca thật 18 vị thế cộng chính xác = {chinh_xac} (trần giữ "
          f"đúng), và không bị kêu vượt")


def test_ca_toi_thieu_tai_lap_bui_va_khong_bi_keu_nham():
    """Dựng lại CƠ CHẾ của lỗi thật, đi trọn đường `_capital_deployment`.

    Ba khẳng định, và khẳng định GIỮA mới là cái làm test này có nghĩa:
    nếu bụi biến mất thì test không còn đo gì cả, và nó phải ĐỎ chứ không
    được âm thầm xanh.
    """
    _, dinh = paper_metrics._capital_deployment(_dung(CA_TOI_THIEU))

    chinh_xac = sum(Decimal(str(s)) for _, _, _, s in CA_TOI_THIEU)
    assert chinh_xac == Decimal("100.0"), (
        f"ca tối thiểu phải chạm ĐÚNG trần, đo được {chinh_xac}")

    assert dinh > TRAN_VON_CAM_KET_PCT, (
        f"bụi float đã biến mất (đỉnh = {dinh!r}). Test này chỉ đo được "
        f"cái gì đó khi phép cộng float còn sinh dư — nếu "
        f"_capital_deployment đổi sang số chính xác thì XOÁ test này, "
        f"đừng nới nó.")

    assert not paper_metrics.vuot_tran_von(dinh), (
        f"đỉnh {dinh!r} là trần giữ ĐÚNG (tổng chính xác {chinh_xac}), "
        f"mà vuot_tran_von vẫn kêu đòn bẩy. Đây là lỗi 65.")

    print(f"PASS  ca tối thiểu: chính xác {chinh_xac} · float {dinh!r} "
          f"· không kêu nhầm")


def test_vuot_that_thi_van_phai_bat():
    """Dung sai KHÔNG được nuốt một lần vượt trần thật.

    Mốc nhỏ nhất đáng bắt là MỘT bước yết (0,1 điểm) — dưới mức đó thì
    không có vị thế nào tồn tại được.
    """
    tran = TRAN_VON_CAM_KET_PCT
    for pct, phai_keu in ((tran + BUOC_YET_SIZE_PCT, True),
                          (137.0, True),
                          (224.0, True),
                          (tran, False),
                          (99.9, False),
                          (0.0, False)):
        assert paper_metrics.vuot_tran_von(pct) is phai_keu, (
            f"vuot_tran_von({pct}) phải là {phai_keu}")
    print("PASS  vượt thật (>= 1 bước yết) vẫn bị bắt, chạm đúng trần thì không")


def test_chua_do_duoc_khong_phai_khong_vuot():
    """`None` trả False vì chưa đo được, KHÔNG vì đã kết luận là an toàn.

    Phân biệt này là luật của dự án (`kiem_cu_phap_311` mã thoát 2, ba
    trạng thái của `vnstock_goi.kiem_goi`). Ghi ra đây để lần sau không ai
    đọc `False` thành "đã kiểm và sạch".
    """
    assert paper_metrics.vuot_tran_von(None) is False
    print("PASS  None -> False, và lý do đã ghi trong docstring hàm")


def test_dung_sai_nam_giua_hai_bien_DO_DUOC():
    """Ngưỡng phải lớn hơn hẳn bụi và nhỏ hơn hẳn một vị thế thật.

    Không kiểm ngưỡng bằng một con số gõ lại — kiểm nó bằng hai đại lượng
    ĐO ĐƯỢC mà nó phải nằm giữa. Nới ngưỡng tới chỗ nuốt được một bước yết
    là làm hỏng đúng thứ trần sinh ra để giữ.
    """
    ds = paper_metrics.DUNG_SAI_VON_PCT
    assert ds > BUI_DO_DUOC * 100, (
        f"dung sai {ds} quá chật so với bụi đo được {BUI_DO_DUOC}")
    assert ds < BUOC_YET_SIZE_PCT / 100, (
        f"dung sai {ds} quá rộng — nó tiến sát bước yết "
        f"{BUOC_YET_SIZE_PCT}, tức bắt đầu nuốt được vị thế thật")
    print(f"PASS  dung sai {ds:g} nằm giữa bụi {BUI_DO_DUOC:g} và bước yết "
          f"{BUOC_YET_SIZE_PCT:g}")


def _cay(ten_file: str) -> ast.Module:
    return ast.parse((GOC / ten_file).read_text(encoding="utf-8"))


#: Tên các đại lượng vốn-cam-kết. So bất kỳ tên nào trong đây với một hằng
#: số >= 100 là tự viết lại phép phán — đúng hình dạng lỗi 65.
TEN_VON = ("peak_capital_deployed_pct", "avg_capital_deployed_pct",
           "von_dinh", "von_tb")

BA_NOI = ("paper_metrics.py", "walkforward.py", "app.py")


def _ten_cua(nut: ast.AST) -> str:
    if isinstance(nut, ast.Attribute):
        return nut.attr
    if isinstance(nut, ast.Subscript) and isinstance(nut.slice, ast.Constant):
        return str(nut.slice.value)
    if isinstance(nut, ast.Name):
        return nut.id
    return ""


def test_khong_noi_nao_con_tu_viet_phep_so_voi_tran():
    """Quét AST, KHÔNG quét văn bản.

    Gác kiểu `"> 100.0" in src` sẽ khớp cả dòng chú thích giải thích lỗi
    này — mà file nào cũng có một dòng như thế sau hôm nay. Xem
    `CLAUDE.md` mục "Gác phải đọc AST, không đọc `in`".
    """
    pham = []
    for ten_file in BA_NOI:
        for nut in ast.walk(_cay(ten_file)):
            if not isinstance(nut, ast.Compare):
                continue
            if _ten_cua(nut.left) not in TEN_VON:
                continue
            for so_sanh in nut.comparators:
                if (isinstance(so_sanh, ast.Constant)
                        and isinstance(so_sanh.value, (int, float))
                        and so_sanh.value >= TRAN_VON_CAM_KET_PCT):
                    pham.append(f"{ten_file}:{nut.lineno}")
    assert not pham, (
        "còn nơi tự so vốn cam kết với hằng số trần thay vì gọi "
        f"paper_metrics.vuot_tran_von(): {pham}")
    print(f"PASS  {len(BA_NOI)} file, 0 phép so tự viết")


def test_ca_ba_noi_deu_GOI_ham_phan():
    """Không đủ khi không ai tự viết — phải có người GỌI.

    Xoá hẳn cả phép so lẫn lời gọi thì test trên vẫn xanh. Test này bắt
    phần còn lại: mỗi file phải thật sự hỏi hàm phán.
    """
    for ten_file in BA_NOI:
        goi = [n for n in ast.walk(_cay(ten_file))
               if isinstance(n, ast.Call)
               and _ten_cua(n.func) in ("vuot_tran_von", "_vuot_tran")]
        assert goi, (
            f"{ten_file} không gọi vuot_tran_von lần nào — phép so trần "
            f"đã biến mất khỏi file này")
    print(f"PASS  {len(BA_NOI)} file đều gọi hàm phán")


def test_bao_cao_in_du_so_le_de_doc_duoc_phan_quyet():
    """Ba giá trị khác nhau quanh trần phải cho ba dòng khác nhau.

    Ở `.0f` thì 99,9 · 100,0 · 100,4 đều in ra "100%" — người đọc thấy
    cảnh báo bên cạnh một con số trông như đúng trần và không kiểm được
    gì. Đó là nửa thứ hai của lỗi 65, và nó sống sót qua mọi phép sửa
    phần phán quyết.
    """
    goc = {"so_lenh": 792, "ky_vong": -1.15, "win_rate": 22.3,
           "net_pct": -28.89, "alpha": -1.40, "alpha_ktc": (-1.83, -0.97),
           "alpha_ket_luan": "thua chuan co y nghia", "alpha_so_lenh": 792,
           "alpha_bo_qua": 0, "mau_dau": 44, "mau_hoc_them": 0,
           "che_do_hoc": "co_san", "von_tb": 55.0}

    dong = {}
    for dinh in (99.9, 100.0, 100.4):
        bao = "\n".join(wf.dong_bao_cao_oos(dict(goc, von_dinh=dinh)))
        dong[dinh] = [d for d in bao.splitlines() if "vốn triển khai" in d][0]
        keu = "vượt 100%" in bao
        assert keu is (dinh > 100.0), (
            f"vốn đỉnh {dinh}: cảnh báo = {keu}, không khớp sự thật")

    assert len(set(dong.values())) == 3, (
        f"ba mức vốn đỉnh khác nhau in ra cùng một dòng: {dong}")
    print("PASS  99,9 · 100,0 · 100,4 cho ba dòng phân biệt được")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_") and callable(ham):
            ham()
    print("\nTAT CA XANH")
