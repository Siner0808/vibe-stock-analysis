# docs/lich-su — bản lưu NGUYÊN VĂN, không tự nạp vào phiên

Tạo ở BƯỚC 145 (30/09/2026). Hai file bên cạnh là bản chép **từng byte** của
`CLAUDE.md` (135.639 byte) và `.claude/skills/quy-trinh-lam-viec/SKILL.md`
(56.141 byte) tại commit `1aadda5`, trước khi rút gọn:

| Bản lưu | Bản hiện hành |
|---|---|
| `CLAUDE-md-2026-09-30.md` | `CLAUDE.md` — chỉ luật hiện hành |
| `SKILL-md-2026-09-30.md` | `.claude/skills/quy-trinh-lam-viec/SKILL.md` |

**Vì sao tách:** `CLAUDE.md` và `SKILL.md` được nạp vào ngữ cảnh — `CLAUDE.md`
mỗi khi phiên đọc một file trong repo/worktree (và gắn lại khi file đổi trên
đĩa), `SKILL.md` mỗi lần gọi skill. Ở hai phiên dự án, ngữ cảnh ~465k token
được gửi lại ở MỖI lượt gọi công cụ (98,5–98,7% token là đọc lại cache), và
hai file này chiếm ~36k + ~15k token mỗi bản. Đo bằng
`./.venv/Scripts/python.exe tools/do_token_phien.py <phiên>.jsonl` và
`tools/do_token_phien.py --tai-lieu`.

**Cách tìm lại một khẳng định cũ:** nhiều chỗ trong `docs/STATE.md`,
`docs/TIEU-CHI-DOC-TRUOC.md` và `references/loi-da-mac.md` viết "`CLAUDE.md`
mục X" theo nghĩa **lúc ấy**. Mục X còn trong `CLAUDE.md` hiện hành thì đọc
ở đó; không còn thì nó nằm ở đây:

```bash
grep -n "<từ khoá>" docs/lich-su/CLAUDE-md-2026-09-30.md
```

**Trạng thái của các file này:** lịch sử, không phải luật. Khối 🔴 "HẾT
ĐÚNG" trong đó vẫn giữ nguyên dấu; đừng trích một con số ở đây làm giá trị
hiện hành — đọc mã hoặc `docs/HANDOFF.md`. Chúng nằm trong quần thể của
`tools/doi_chieu_trich_dan.py` và `tools/soat_loi_khai_cu.py`, và là nguồn
của sổ tay NotebookLM, để trích dẫn từ lịch sử vẫn đối chiếu được.

**Không sửa các bản lưu.** Cần ghi thêm điều gì về lịch sử thì ghi vào
`docs/STATE.md`.
