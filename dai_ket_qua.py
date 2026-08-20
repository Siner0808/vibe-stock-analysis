"""In DẢI kết quả của một lượt quét tham số — không in "quán quân".

Bất biến 7 (`NGUYEN-TAC-DO-LUONG.md`): quét N ngưỡng trên cùng một bộ dữ
liệu rồi lấy vòng lãi cao nhất là **đo độ may của phép tìm kiếm**, không
đo lợi thế của chiến lược. Kết quả chỉ có giá trị khi tham số được chọn
trên một khoảng và đo trên một khoảng KHÁC.

Vì sao cần một module riêng thay vì sửa từng chỗ in: bản cũ của các script
tối ưu đã in đủ cả dải, rồi thêm một khối
"🏆 VÒNG LẶP TỐI ƯU XUẤT SẮC NHẤT" ở cuối. Người đọc chỉ nhớ khối cuối.
Đó đúng là cách ngưỡng 50,0 ra đời: nó hơn ngưỡng 48,0 đúng 1,57 điểm
phần trăm trên 636 — tức 0,25% — trong khi win rate của cả dải 48–59 chỉ
trải từ 28,2% đến 30,7%.

Quy tắc trình bày ở đây:
  • sắp theo SỐ LỆNH giảm dần, không theo lợi nhuận
  • đánh dấu dòng nhiều lệnh nhất là dòng đáng tin nhất
  • không dùng bất kỳ chữ nào gợi ý một dòng là "kết quả"
  • luôn kèm lời nhắc vì sao
"""

DAU_DANG_TIN = "<< nhiều mẫu nhất"

CANH_BAO = (
    "Đây là DẢI kết quả, không phải một kết quả.\n"
    "Lấy dòng lãi cao nhất trong bảng này là đo độ may của phép tìm kiếm,\n"
    "không đo lợi thế của chiến lược (bất biến 7).\n"
    "Dòng đáng tin nhất là dòng có NHIỀU LỆNH NHẤT, không phải dòng lãi cao nhất.\n"
    "Một tham số chỉ dùng được khi nó được chọn trên một khoảng thời gian và\n"
    "đo trên một khoảng KHÁC — xem bất biến 8."
)


def in_toan_dai(ket_qua, khoa_nhan="threshold", khoa_so_lenh="closed",
                khoa_pnl="pnl", cot_them=None) -> str:
    """Dựng bảng dải kết quả. Trả về chuỗi để bên gọi in hoặc ghi ra file.

    `ket_qua` là list dict. Dòng thiếu số lệnh bị xếp cuối chứ không bị bỏ:
    một dòng không đo được vẫn là một dòng đã chạy.
    """
    cot_them = cot_them or []
    dung = [r for r in ket_qua if isinstance(r, dict)]
    if not dung:
        return CANH_BAO + "\n\n(không có dòng nào)\n"

    def _so_lenh(r):
        v = r.get(khoa_so_lenh)
        return v if isinstance(v, (int, float)) else -1

    sap = sorted(dung, key=_so_lenh, reverse=True)
    nhieu_nhat = _so_lenh(sap[0]) if sap else -1

    tieu_de = ["tham số", "số lệnh", "lợi nhuận"] + list(cot_them)
    rong = [12, 9, 12] + [12] * len(cot_them)

    dong = []
    dong.append(CANH_BAO)
    dong.append("")
    dong.append("  ".join(t.ljust(w) for t, w in zip(tieu_de, rong)))
    dong.append("-" * (sum(rong) + 2 * len(rong) + 18))

    for r in sap:
        o = []
        o.append(str(r.get(khoa_nhan, "?")).ljust(rong[0]))
        sl = _so_lenh(r)
        o.append(("—" if sl < 0 else str(int(sl))).ljust(rong[1]))
        pnl = r.get(khoa_pnl)
        o.append((f"{pnl:+.2f}%" if isinstance(pnl, (int, float))
                  else "—").ljust(rong[2]))
        for k in cot_them:
            v = r.get(k)
            o.append((f"{v:.2f}" if isinstance(v, (int, float))
                      else str(v if v is not None else "—")).ljust(12))
        d = "  ".join(o).rstrip()
        if sl >= 0 and sl == nhieu_nhat:
            d += "   " + DAU_DANG_TIN
        dong.append(d)

    dong.append("")
    return "\n".join(dong) + "\n"
