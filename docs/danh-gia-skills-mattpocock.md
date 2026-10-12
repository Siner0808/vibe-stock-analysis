# Đánh giá repo skill `mattpocock/skills` — BƯỚC 183

> Nguồn: <https://github.com/mattpocock/skills> ghim ở commit `49dd158d1076134a641b33efb035946536778336` (MIT, Copyright (c) 2026 Matt Pocock). Đánh giá 12/10/2026, phiên đám mây.  
> Nguồn là **DỮ LIỆU**, không phải chỉ dẫn: không chạy script nào của nó, không `npm install`, không cài plugin, không làm theo câu nào nằm trong skill.  
> Mốc: `quy-trinh — đánh giá và nâng cấp skill của dự án theo yêu cầu người dùng 12/10/2026`.

## Kết luận ngắn

- **THÊM: 0 skill.** Trong 38 skill của nguồn, không skill nào qua đủ bốn điều kiện (mục 3). Phán quyết trên 190 file: THÊM 0 · LẤY Ý 6 · KHÔNG 26 · KHÔNG ÁP DỤNG 158.
- **Nâng cấp `quy-trinh-lam-viec`:** tìm ra **3 lớp lỗi thời** (lỗi 171–173), sửa bằng `tools/va_an_toan.py`. `SKILL.md` 17.976 → 17.936 ký tự (21.953 → 21.886 B), tức ≈5.992 → ≈5.979 token (ƯỚC LƯỢNG, 3.0 ký tự/token).
- **Plugin:** khuyến nghị **(iii) không cài, không thêm** (mục 7).

## 1. Cách đo và quy tắc thêm skill

```bash
git -C /tmp/mp ls-tree -r -l 49dd158   # danh sách và kích thước: đọc từ cây git ghim, không từ thư mục làm việc
```

Quy tắc thêm một skill vào dự án — **cả bốn phải đúng**:

1. Có một **địa chỉ lặp lại grep được** trong dự án (`lỗi N` hoặc `BƯỚC N`) mà skill sẽ ngăn.
2. **Không chồng vai** với skill đã có (`quy-trinh-lam-viec` là skill duy nhất; gác `test_CHI_CO_MOT_skill_quy_trinh` khoá điều này) hoặc luật dự án.
3. **Áp dụng được** cho Python/pytest/Streamlit/vnstock và viết lại bằng tiếng Việt.
4. **Chi phí token đo được**: mô tả của skill do model gọi nạp MỖI phiên; thân chỉ nạp khi gọi.

Mỗi skill được thêm sẽ cần `.claude/skills/<tên>/` kèm `NGUON.md` (URL, commit ghim, nguyên văn lời MIT). Vì kết quả là **0 skill thêm**, không tạo `NGUON.md` nào; lời MIT chép ở mục 9 vì ta LẤY Ý.

Hệ số đổi token: `tools/do_token_phien.py` có `KY_TU_MOI_TOKEN = 3.0` ký tự/token. Đó là hệ số hiệu chuẩn của dự án; mọi số token ở đây là **ƯỚC LƯỢNG**, không phải đo từ API.

## 2. Bảng phủ 190 file

Cột: đường dẫn · byte · nó là gì · phán quyết (THÊM / LẤY Ý / KHÔNG / KHÔNG ÁP DỤNG).

| đường dẫn | byte | nó là gì | phán quyết |
|---|---|---|---|
| `.agents/adr/0001-explicit-setup-pointer-only-for-hard-dependencies.md` | 1154 | ADR nội bộ: chỉ trỏ tới `/setup-matt-pocock-skills` khi skill phụ thuộc cứng vào cấu hình repo | KHÔNG ÁP DỤNG — quy ước của repo nguồn về issue tracker |
| `.agents/adr/0002-ship-as-a-claude-code-plugin.md` | 6562 | ADR nội bộ: phát hành bộ skill như plugin Claude Code, hoãn plugin Codex | KHÔNG ÁP DỤNG — dùng làm dữ liệu cho mục 5, không có ý để lấy vào skill |
| `.agents/install-block.md` | 5258 | Khối lệnh cài chính tắc cho từng agent (Claude Code, Codex, Copilot, VS Code, Gemini, skills.sh) | KHÔNG ÁP DỤNG — nguồn của lệnh cài ở mục 5; KHÔNG chạy |
| `.agents/invocation.md` | 3850 | Quy ước skill do người gọi vs do model gọi (`disable-model-invocation`), cách gọi skill khác bằng Skill tool | KHÔNG ÁP DỤNG — là bằng chứng đo chi phí mô tả ở mục 3/5 |
| `.agents/writing-docs.md` | 12953 | Cách viết trang docs cho từng skill của repo nguồn | KHÔNG ÁP DỤNG |
| `.changeset/README.md` | 512 | README sinh tự động của công cụ `@changesets/cli` | KHÔNG ÁP DỤNG |
| `.changeset/ask-matt-read-skill-first.md` | 196 | Mảnh changelog: `ask-matt` đọc SKILL.md trước khi mô tả một skill | KHÔNG — dự án chỉ có 1 skill, đã có Bước 1 điều 2 |
| `.changeset/code-review-standards-and-subagents.md` | 368 | Mảnh changelog: `code-review` tìm file chuẩn code và chạy hai sub-agent ở foreground | KHÔNG |
| `.changeset/config.json` | 380 | Cấu hình changesets (changelog qua GitHub, baseBranch main) | KHÔNG ÁP DỤNG |
| `.changeset/diagnosing-bugs-prove-mutation.md` | 232 | Mảnh changelog: `diagnosing-bugs` pha 5 phải `diff` đột biến với bản gốc trước khi tin phép đỏ | LẤY Ý — thành mệnh đề *"thay vào phải làm AST ĐỔI"* của gác `test_VI_DU_neo_chay_duoc` |
| `.changeset/github-tracker-external-pr-list.md` | 236 | Mảnh changelog: sửa mẫu tracker GitHub (`authorAssociation`) | KHÔNG ÁP DỤNG |
| `.changeset/grilling-yes-accepts-recommendation.md` | 155 | Mảnh changelog: `grilling` đặt câu hỏi để "yes" = nhận đáp án đề xuất | KHÔNG |
| `.changeset/handoff-temp-dir.md` | 166 | Mảnh changelog: `handoff` nêu rõ thư mục tạm của hệ điều hành | KHÔNG |
| `.changeset/implement-skill-tool-wording.md` | 148 | Mảnh changelog: `implement` gọi Skill tool thay vì `/skill` trần | KHÔNG ÁP DỤNG |
| `.changeset/implement-ticket-reference.md` | 190 | Mảnh changelog: `implement` lấy ticket theo tham chiếu từ tracker | KHÔNG ÁP DỤNG |
| `.changeset/setup-tracker-fixes.md` | 384 | Mảnh changelog: sửa `setup-matt-pocock-skills` (nhãn, glab, `--json`) | KHÔNG ÁP DỤNG |
| `.changeset/tdd-seam-tradeoffs.md` | 181 | Mảnh changelog: `tdd` ghi chú mỗi seam bắt được gì, bỏ sót gì | KHÔNG |
| `.changeset/teach-quiz-answer-position.md` | 105 | Mảnh changelog: `teach` xáo vị trí đáp án đúng | KHÔNG ÁP DỤNG |
| `.changeset/teach-workspace-root.md` | 126 | Mảnh changelog: `teach` ghi workspace ở thư mục đang chạy | KHÔNG ÁP DỤNG |
| `.changeset/to-tickets-sub-issues.md` | 342 | Mảnh changelog: `to-tickets` tạo ticket con (sub-issue) | KHÔNG ÁP DỤNG |
| `.changeset/wayfinder-labels-refs-research-prs.md` | 315 | Mảnh changelog: sửa `wayfinder` (nhãn, tham chiếu, PR nghiên cứu) | KHÔNG ÁP DỤNG |
| `.changeset/wizard-template-fixes-2.md` | 397 | Mảnh changelog: sửa `template.sh` của `wizard` (dấu nháy `.env`, `tput`) | KHÔNG ÁP DỤNG |
| `.changeset/wizard-template-fixes.md` | 454 | Mảnh changelog: sửa `template.sh` của `wizard` (Readline, symlink `.env`) | KHÔNG ÁP DỤNG |
| `.claude-plugin/marketplace.json` | 605 | Danh mục marketplace `mattpocock` trỏ vào plugin `mattpocock-skills` (`source: ./`) | KHÔNG ÁP DỤNG — dữ liệu mục 5; KHÔNG cài |
| `.claude-plugin/plugin.json` | 1690 | Manifest plugin v1.3.1: 27 đường dẫn skill; không có khoá hooks/mcp/commands/agents | KHÔNG ÁP DỤNG — dữ liệu mục 5 |
| `.github/ISSUE_TEMPLATE/bug.yml` | 1455 | Mẫu issue báo lỗi của repo nguồn | KHÔNG ÁP DỤNG |
| `.github/ISSUE_TEMPLATE/config.yml` | 254 | Cấu hình mẫu issue của repo nguồn | KHÔNG ÁP DỤNG |
| `.github/ISSUE_TEMPLATE/idea.yml` | 1585 | Mẫu issue đề xuất ý tưởng của repo nguồn | KHÔNG ÁP DỤNG |
| `.github/workflows/needs-info.yml` | 1362 | Workflow nhãn `needs-info` của repo nguồn | KHÔNG ÁP DỤNG — KHÔNG chạy, không sao chép workflow |
| `.github/workflows/release.yml` | 780 | Workflow phát hành bằng changesets (`npx changeset tag`) | KHÔNG ÁP DỤNG — KHÔNG chạy |
| `.github/workflows/triage-label.yml` | 547 | Workflow gắn nhãn triage của repo nguồn | KHÔNG ÁP DỤNG — KHÔNG chạy |
| `.gitignore` | 21 | Một dòng gitignore của repo nguồn | KHÔNG ÁP DỤNG |
| `.out-of-scope/frozen-misc-skills.md` | 1384 | Quyết định: skill trong `misc/` bị đóng băng, không sửa lỗi | KHÔNG — cho thấy `misc/` không được bảo trì |
| `.out-of-scope/harness-name-collisions.md` | 1606 | Quyết định: KHÔNG đổi tên skill để tránh trùng lệnh dựng sẵn; dùng tên có tiền tố plugin (`/mattpocock-skills:research`) | KHÔNG ÁP DỤNG — là dữ liệu va chạm tên ở mục 5 |
| `.out-of-scope/lazy-load-writing-for-agents.md` | 740 | Quyết định: `retro` luôn nạp `writing-for-agents`, không nạp lười | KHÔNG ÁP DỤNG |
| `.out-of-scope/mainstream-issue-trackers-only.md` | 1977 | Quyết định: chỉ hỗ trợ GitHub, GitLab, markdown cục bộ | KHÔNG ÁP DỤNG |
| `.out-of-scope/native-question-tool.md` | 1674 | Quyết định: grilling hỏi bằng văn bản thường, không qua công cụ hỏi gốc của harness | KHÔNG ÁP DỤNG |
| `.out-of-scope/new-skills.md` | 1539 | Quyết định: repo nguồn không nhận đề xuất/đóng góp skill mới | KHÔNG ÁP DỤNG — nên ta không gửi gì ngược lại |
| `.out-of-scope/question-limits.md` | 1259 | Quyết định: không đặt trần số câu hỏi khi grilling | KHÔNG ÁP DỤNG |
| `.out-of-scope/setup-skill-verify-mode.md` | 1125 | Quyết định: không thêm chế độ verify cho `setup-matt-pocock-skills` | KHÔNG ÁP DỤNG |
| `.out-of-scope/subagent-recursion.md` | 1137 | Quyết định: skill không chặn sub-agent đệ quy; việc đó của harness | KHÔNG ÁP DỤNG |
| `AGENTS.md` | 9 | 9 byte, nội dung đúng `CLAUDE.md` (tên file, không phải chỉ dẫn) | KHÔNG ÁP DỤNG |
| `CHANGELOG.md` | 55476 | Nhật ký phát hành sinh bởi changesets; dòng 39 ghi lỗi YAML do `: ` không nháy trong `description` làm skill bị bỏ qua | LẤY Ý — kiểm hình dạng `description` (hàm `_mo_ta_yaml_hong`, lỗi 171) |
| `CLAUDE.md` | 3957 | Chỉ dẫn cho agent làm việc trên chính repo nguồn (cách viết skill, quy ước changeset) | KHÔNG ÁP DỤNG — không phải chỉ dẫn của ta; đọc như DỮ LIỆU |
| `GLOSSARY.md` | 1768 | Từ vựng của repo nguồn (bucket, skill, invocation...) | KHÔNG ÁP DỤNG |
| `LICENSE` | 1068 | MIT, Copyright (c) 2026 Matt Pocock | KHÔNG ÁP DỤNG — chép nguyên văn ở mục 9 vì ta LẤY Ý |
| `README.md` | 16461 | Giới thiệu bộ skill, lệnh cài, danh sách skill theo cách gọi | KHÔNG ÁP DỤNG |
| `SCOPE.md` | 2348 | Tiêu chí nhận ý tưởng của repo nguồn | KHÔNG ÁP DỤNG |
| `docs/agents/triage-labels.md` | 1085 | Bảng ánh xạ 5 vai triage sang nhãn issue của repo nguồn | KHÔNG ÁP DỤNG |
| `docs/engineering/ask-matt.md` | 11204 | Trang docs cho người đọc (FAQ) của `ask-matt` — bộ định tuyến | KHÔNG ÁP DỤNG |
| `docs/engineering/code-review.md` | 10996 | Trang docs cho người đọc (FAQ) của `code-review` — review hai trục | KHÔNG ÁP DỤNG |
| `docs/engineering/codebase-design.md` | 12196 | Trang docs cho người đọc (FAQ) của `codebase-design` — từ vựng module sâu | KHÔNG ÁP DỤNG |
| `docs/engineering/diagnosing-bugs.md` | 10767 | Trang docs (FAQ) của `diagnosing-bugs`; dòng 72–75: Snyk gắn cờ vì có `.sh` + chỉ dẫn chạy + HTTP ra ngoài | KHÔNG — bằng chứng cho mục 6 |
| `docs/engineering/domain-modeling.md` | 10572 | Trang docs cho người đọc (FAQ) của `domain-modeling` — mô hình miền | KHÔNG ÁP DỤNG |
| `docs/engineering/grill-with-docs.md` | 9857 | Trang docs cho người đọc (FAQ) của `grill-with-docs` — phỏng vấn + ghi tài liệu | KHÔNG ÁP DỤNG |
| `docs/engineering/implement-spec.md` | 9764 | Trang docs (FAQ) của `implement-spec`; dòng 68: worktree chỉ chứa thứ git theo dõi, test đọc fixture bị gitignore có thể SKIP lặng lẽ | LẤY Ý — mục *Phiên đám mây* của `cong-thuc-chay.md` (lỗi 173): đọc lý do skip bằng `-rs` |
| `docs/engineering/implement.md` | 10258 | Trang docs cho người đọc (FAQ) của `implement` — triển khai một ticket | KHÔNG ÁP DỤNG |
| `docs/engineering/improve-codebase-architecture.md` | 11764 | Trang docs cho người đọc (FAQ) của `improve-codebase-architecture` — tìm cơ hội làm sâu module | KHÔNG ÁP DỤNG |
| `docs/engineering/pr.md` | 8079 | Trang docs cho người đọc (FAQ) của `pr` — thân PR | KHÔNG ÁP DỤNG |
| `docs/engineering/prototype.md` | 9516 | Trang docs cho người đọc (FAQ) của `prototype` — prototype bỏ đi | KHÔNG ÁP DỤNG |
| `docs/engineering/research.md` | 9356 | Trang docs cho người đọc (FAQ) của `research` — nghiên cứu nguồn gốc | KHÔNG ÁP DỤNG |
| `docs/engineering/resolving-merge-conflicts.md` | 5486 | Trang docs cho người đọc (FAQ) của `resolving-merge-conflicts` — giải xung đột merge; KHÔNG có thư mục skill tương ứng trong cây (trang mồ côi) | KHÔNG ÁP DỤNG |
| `docs/engineering/retro.md` | 8828 | Trang docs cho người đọc (FAQ) của `retro` — nhìn lại phiên | KHÔNG ÁP DỤNG |
| `docs/engineering/setup-matt-pocock-skills.md` | 9132 | Trang docs cho người đọc (FAQ) của `setup-matt-pocock-skills` — cấu hình repo | KHÔNG ÁP DỤNG |
| `docs/engineering/tdd.md` | 10363 | Trang docs cho người đọc (FAQ) của `tdd` — phát triển hướng kiểm thử | KHÔNG ÁP DỤNG |
| `docs/engineering/to-spec.md` | 8502 | Trang docs cho người đọc (FAQ) của `to-spec` — hội thoại → spec | KHÔNG ÁP DỤNG |
| `docs/engineering/to-tickets.md` | 10896 | Trang docs cho người đọc (FAQ) của `to-tickets` — spec → ticket | KHÔNG ÁP DỤNG |
| `docs/engineering/triage.md` | 12893 | Trang docs cho người đọc (FAQ) của `triage` — phân loại issue | KHÔNG ÁP DỤNG |
| `docs/engineering/wayfinder.md` | 15582 | Trang docs cho người đọc (FAQ) của `wayfinder` — lập bản đồ việc lớn | KHÔNG ÁP DỤNG |
| `docs/engineering/wizard.md` | 9571 | Trang docs cho người đọc (FAQ) của `wizard` — sinh wizard bash | KHÔNG ÁP DỤNG |
| `docs/productivity/grill-me.md` | 6581 | Trang docs cho người đọc (FAQ) của `grill-me` — phỏng vấn kỹ | KHÔNG ÁP DỤNG |
| `docs/productivity/grilling.md` | 10243 | Trang docs cho người đọc (FAQ) của `grilling` — phỏng vấn kỹ (lõi) | KHÔNG ÁP DỤNG |
| `docs/productivity/handoff.md` | 8794 | Trang docs cho người đọc (FAQ) của `handoff` — bàn giao phiên | KHÔNG ÁP DỤNG |
| `docs/productivity/teach.md` | 12422 | Trang docs cho người đọc (FAQ) của `teach` — dạy học | KHÔNG ÁP DỤNG |
| `docs/productivity/to-questionnaire.md` | 7815 | Trang docs cho người đọc (FAQ) của `to-questionnaire` — quyết định → bảng câu hỏi | KHÔNG ÁP DỤNG |
| `docs/productivity/wait-what.md` | 3611 | Trang docs cho người đọc (FAQ) của `wait-what` — nói lại cho dễ hiểu | KHÔNG ÁP DỤNG |
| `docs/productivity/writing-for-agents.md` | 7699 | Trang docs cho người đọc (FAQ) của `writing-for-agents` — viết tài liệu cho agent | KHÔNG ÁP DỤNG |
| `package-lock.json` | 49290 | Khoá phụ thuộc npm (công cụ phát hành changesets) | KHÔNG ÁP DỤNG — KHÔNG `npm install` |
| `package.json` | 597 | Khai báo npm của repo nguồn (changesets, script phát hành) | KHÔNG ÁP DỤNG — KHÔNG `npm install` |
| `scripts/link-skills.sh` | 2240 | Script bash liên kết skill vào thư mục đích; dòng 56 có `rm -rf "$target"` | KHÔNG ÁP DỤNG — KHÔNG chạy; xem mục 6 |
| `scripts/list-skills.sh` | 168 | Script bash liệt kê skill | KHÔNG ÁP DỤNG — KHÔNG chạy |
| `scripts/sync-plugin-version.mjs` | 1429 | Script Node đồng bộ phiên bản plugin.json với package.json | KHÔNG ÁP DỤNG — KHÔNG chạy |
| `skills/deprecated/README.md` | 160 | README bucket `deprecated` (đang rỗng) | KHÔNG ÁP DỤNG |
| `skills/engineering/README.md` | 4287 | README bucket `engineering` liệt kê các skill | KHÔNG ÁP DỤNG |
| `skills/engineering/ask-matt/PHASE-BOUNDARIES.md` | 4249 | Khi nào tiếp tục trong cùng phiên, khi nào mở phiên mới (vùng thông minh ~150k token) | KHÔNG — dự án đã có luật HANDOFF/STATE cho ranh giới phiên |
| `skills/engineering/ask-matt/SKILL.md` | 12594 | SKILL.md `ask-matt` — Bộ định tuyến: hỏi tình huống rồi chỉ ra skill hoặc luồng phù hợp (luồng chính ý tưởng → giao). Mô tả 83 B, thân 12443 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — định tuyến 38 skill; ta thêm 0 skill nên không có gì để định tuyến |
| `skills/engineering/ask-matt/agents/openai.yaml` | 137 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/code-review/SKILL.md` | 6670 | SKILL.md `code-review` — Review diff từ một điểm cố định theo hai trục (Standards, Spec) bằng hai sub-agent song song, gộp báo cáo. Mô tả 421 B, thân 6209 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG — không có địa chỉ lỗi N lặp lại; trùng vai cổng; mô tả 421 B là mô tả lớn nhất bộ, trả MỌI phiên |
| `skills/engineering/code-review/agents/openai.yaml` | 100 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/codebase-design/DEEPENING.md` | 2553 | Cách làm sâu một cụm module nông an toàn theo loại phụ thuộc | KHÔNG |
| `skills/engineering/codebase-design/DESIGN-IT-TWICE.md` | 2665 | Mẫu sub-agent song song thiết kế hai giao diện (Ousterhout) | KHÔNG |
| `skills/engineering/codebase-design/SKILL.md` | 6446 | SKILL.md `codebase-design` — Từ vựng module sâu: module, interface, seam, adapter, depth, leverage, locality. Mô tả 265 B, thân 6137 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG — ví dụ thuần TypeScript/hướng đối tượng; không có địa chỉ lỗi N; 265 B mô tả mỗi phiên |
| `skills/engineering/codebase-design/agents/openai.yaml` | 102 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/diagnosing-bugs/SKILL.md` | 8664 | SKILL.md `diagnosing-bugs` — Vòng chẩn đoán: dựng vòng phản hồi bấm được trước (pha 1), rồi giả thuyết, đo, sửa, kiểm lại. Mô tả 156 B, thân 8464 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | LẤY Ý — ý dòng 125 (`diff` chứng minh đột biến có hiệu lực) thành mệnh đề của gác mới; cả skill thì trùng vai Bước 3 nên không thêm |
| `skills/engineering/diagnosing-bugs/agents/openai.yaml` | 103 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/diagnosing-bugs/scripts/hitl-loop.template.sh` | 1316 | Script bash mẫu ~30 dòng, `read -r -p` dừng chờ người; skill chỉ dẫn agent CHẠY nó | KHÔNG ÁP DỤNG — KHÔNG chạy; xem mục 6 |
| `skills/engineering/domain-modeling/ADR-FORMAT.md` | 2733 | Định dạng ADR (`docs/adr/0001-slug.md`) | KHÔNG — dự án ghi quyết định ở `docs/STATE.md` |
| `skills/engineering/domain-modeling/GLOSSARY-FORMAT.md` | 2300 | Định dạng `GLOSSARY.md` | KHÔNG |
| `skills/engineering/domain-modeling/SKILL.md` | 3346 | SKILL.md `domain-modeling` — Xây và mài mô hình miền: chất vấn thuật ngữ, viết `GLOSSARY.md` và ADR ngay khi chúng kết tinh. Mô tả 151 B, thân 3151 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG — dự án đã có sổ quyết định; không có địa chỉ lỗi N lặp lại về thuật ngữ |
| `skills/engineering/domain-modeling/agents/openai.yaml` | 101 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/grill-with-docs/SKILL.md` | 247 | SKILL.md `grill-with-docs` — Gốc 247 B chỉ gọi Skill tool hai lần: `grilling` rồi `domain-modeling`. Mô tả 106 B, thân 66 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — không có nội dung riêng |
| `skills/engineering/grill-with-docs/agents/openai.yaml` | 145 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/implement-spec/SKILL.md` | 2780 | SKILL.md `implement-spec` — Triển khai cả spec trên một nhánh tích hợp: đọc ticket như đồ thị tác vụ, chạy các sub-agent triển khai song song trên biên giới sẵn sàng, mỗi cái một worktree. Mô tả 59 B, thân 2647 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — cần issue tracker và `/setup-matt-pocock-skills`; quy trình giao việc của ta là phiếu leader → PR |
| `skills/engineering/implement-spec/agents/openai.yaml` | 168 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/implement/SKILL.md` | 622 | SKILL.md `implement` — Làm một ticket: lấy ticket theo tham chiếu, gọi `tdd` tại các seam đã thoả thuận, chạy kiểm kiểu rồi toàn bộ test, gọi `code-review`, commit. Mô tả 62 B, thân 491 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — gắn với tracker; Bước 4 đã là bản Python/pytest của chuỗi này |
| `skills/engineering/implement/agents/openai.yaml` | 139 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/improve-codebase-architecture/HTML-REPORT.md` | 6641 | Định dạng báo cáo HTML một file, Tailwind + Mermaid tải từ CDN | KHÔNG ÁP DỤNG |
| `skills/engineering/improve-codebase-architecture/SKILL.md` | 6000 | SKILL.md `improve-codebase-architecture` — Quét codebase tìm cơ hội làm sâu module, xuất báo cáo HTML trực quan rồi phỏng vấn người dùng về cái họ chọn. Mô tả 125 B, thân 5786 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — mục tiêu AI-navigability của TypeScript; báo cáo HTML dùng CDN Tailwind/Mermaid |
| `skills/engineering/improve-codebase-architecture/agents/openai.yaml` | 166 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/pr/CREDITS.md` | 604 | Ghi công Dex Horthy (humanlayer) cho menu hình minh hoạ trong PR | KHÔNG ÁP DỤNG |
| `skills/engineering/pr/SKILL.md` | 4169 | SKILL.md `pr` — Mẫu thân PR: Summary (sơ đồ nhỏ nhất cho thấy thay đổi), Evidence trước/sau, cửa một chiều hay hai chiều. Mô tả 29 B, thân 3919 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG — không có địa chỉ lỗi N lặp lại; thân PR đã có mẫu trong phiếu |
| `skills/engineering/pr/agents/openai.yaml` | 93 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/prototype/LOGIC.md` | 6036 | Nhánh logic: một file HTML có nút bấm điều khiển máy trạng thái | KHÔNG ÁP DỤNG |
| `skills/engineering/prototype/SKILL.md` | 2931 | SKILL.md `prototype` — Prototype bỏ đi để trả lời một câu hỏi thiết kế: nhánh logic (HTML một file) hoặc nhánh UI (nhiều biến thể trên một route). Mô tả 179 B, thân 2714 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG ÁP DỤNG — sinh giao diện web; app của ta là Streamlit và mọi câu hỏi thiết kế được trả lời bằng đo |
| `skills/engineering/prototype/UI.md` | 6913 | Nhánh UI: nhiều biến thể giao diện trên một route, đổi bằng tham số URL | KHÔNG ÁP DỤNG |
| `skills/engineering/prototype/agents/openai.yaml` | 100 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/research/SKILL.md` | 794 | SKILL.md `research` — Chạy một agent nền điều tra câu hỏi từ nguồn chính thống, ghi kết quả thành một file Markdown có trích dẫn. Mô tả 238 B, thân 519 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG — trùng tên lệnh dựng sẵn `/research` của harness khác; không có địa chỉ lỗi N lặp lại |
| `skills/engineering/research/agents/openai.yaml` | 94 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/retro/SKILL.md` | 4369 | SKILL.md `retro` — Nhìn lại một phiên và đề xuất đổi MÔI TRƯỜNG của agent (con trỏ điều hướng, kiểm tự động, luật review, AGENTS.md, công cụ). Mô tả 46 B, thân 4258 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG — vai đã có, kèm máy; ý 'no-op' ta đã làm ở BƯỚC 145 |
| `skills/engineering/retro/agents/openai.yaml` | 146 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/setup-matt-pocock-skills/SKILL.md` | 6978 | SKILL.md `setup-matt-pocock-skills` — Cấu hình repo cho các skill engineering: chọn issue tracker, từ vựng nhãn triage, bố cục tài liệu miền. Mô tả 182 B, thân 6712 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — phụ thuộc cứng của nhóm skill tracker; ta không dùng issue tracker |
| `skills/engineering/setup-matt-pocock-skills/agents/openai.yaml` | 152 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/setup-matt-pocock-skills/domain.md` | 2042 | Mẫu cách skill đọc `GLOSSARY.md`/ADR của repo | KHÔNG ÁP DỤNG |
| `skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md` | 4117 | Mẫu tracker GitHub (`gh`) | KHÔNG ÁP DỤNG |
| `skills/engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md` | 3816 | Mẫu tracker GitLab (`glab`) | KHÔNG ÁP DỤNG |
| `skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md` | 1810 | Mẫu tracker markdown cục bộ (`.scratch/`) | KHÔNG ÁP DỤNG |
| `skills/engineering/setup-matt-pocock-skills/triage-labels.md` | 1057 | Mẫu ánh xạ nhãn triage | KHÔNG ÁP DỤNG |
| `skills/engineering/tdd/SKILL.md` | 3629 | SKILL.md `tdd` — Vòng đỏ → xanh với seam thoả thuận trước, test qua giao diện công khai, chỉ mock ở ranh giới hệ thống. Mô tả 149 B, thân 3448 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG — ví dụ TypeScript; ta đã có luật mạnh hơn (đột biến đến khi MỌI phát đỏ) |
| `skills/engineering/tdd/agents/openai.yaml` | 87 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/tdd/mocking.md` | 1481 | Khi nào mock: chỉ ở ranh giới hệ thống | KHÔNG — Bước 3 + `NGUYEN-TAC-DO-LUONG.md` đã bao phủ |
| `skills/engineering/tdd/tests.md` | 2214 | Ví dụ test tốt/xấu (TypeScript) | KHÔNG |
| `skills/engineering/to-spec/SKILL.md` | 3043 | SKILL.md `to-spec` — Biến cuộc hội thoại hiện tại thành spec và đăng lên tracker, không phỏng vấn. Mô tả 151 B, thân 2825 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — cần tracker và nhãn `ready-for-agent` |
| `skills/engineering/to-spec/agents/openai.yaml` | 135 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/to-tickets/SKILL.md` | 5812 | SKILL.md `to-tickets` — Chia kế hoạch/spec thành các ticket đạn đường (tracer bullet), mỗi ticket khai ticket nó bị chặn bởi. Mô tả 247 B, thân 5495 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — cần tracker; mốc của ta đã là `**Mốc:**` trong STATE |
| `skills/engineering/to-tickets/agents/openai.yaml` | 146 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/triage/AGENT-BRIEF.md` | 7942 | Cách viết bản tóm tắt cho agent trên issue | KHÔNG ÁP DỤNG |
| `skills/engineering/triage/OUT-OF-SCOPE.md` | 4667 | Thư mục `.out-of-scope/` lưu các yêu cầu bị từ chối | KHÔNG — dự án ghi giả thuyết bị bác ở `docs/STATE.md` |
| `skills/engineering/triage/SKILL.md` | 6558 | SKILL.md `triage` — Máy trạng thái phân loại issue và PR ngoài, viết bản tóm tắt cho agent, mọi bình luận mở đầu bằng lời khai AI. Mô tả 136 B, thân 6356 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — ta không nhận issue ngoài |
| `skills/engineering/triage/agents/openai.yaml` | 135 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/wayfinder/SKILL.md` | 12380 | SKILL.md `wayfinder` — Lập bản đồ việc lớn hơn một phiên làm vé quyết định trên tracker, giải từng vé cho tới khi đường tới đích hiện rõ. Mô tả 197 B, thân 12114 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — tracker; lộ trình đã duyệt 08/10/2026 |
| `skills/engineering/wayfinder/agents/openai.yaml` | 144 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/wizard/SKILL.md` | 4123 | SKILL.md `wizard` — Sinh một wizard bash tương tác dẫn người qua các bước chỉ người làm được (mở URL, dán khoá, ghi `.env`, `gh secret set`). Mô tả 313 B, thân 3775 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG ÁP DỤNG — người dùng trên Windows; template.sh 9.498 B là script chạy được, ta cấm chạy |
| `skills/engineering/wizard/agents/openai.yaml` | 96 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/engineering/wizard/template.sh` | 9498 | Template bash 9.498 B (xoá màn hình, mở URL, `ask_secret`, ghi `.env`, `gh secret set`) để agent sao chép | KHÔNG ÁP DỤNG — KHÔNG chạy |
| `skills/in-progress/README.md` | 1676 | README bucket `in-progress`: beta, loại khỏi plugin | KHÔNG ÁP DỤNG |
| `skills/in-progress/chief-of-staff/SKILL.md` | 2112 | SKILL.md `chief-of-staff` — Theo đuổi mục tiêu dài hạn trong một phiên bằng cách điều phối sub-agent và lịch. Mô tả 74 B, thân 1964 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — bản beta, bị loại khỏi plugin |
| `skills/in-progress/chief-of-staff/agents/openai.yaml` | 184 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/in-progress/claude-handoff/SKILL.md` | 1424 | SKILL.md `claude-handoff` — Bàn giao hội thoại cho một agent nền mới qua `claude --bg --name . Mô tả 97 B, thân 1196 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; NGOÀI plugin | KHÔNG — bản beta; mở tiến trình agent nền là hành động ra ngoài, không an toàn để bật |
| `skills/in-progress/claude-handoff/agents/openai.yaml` | 141 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/in-progress/loop-me/SKILL.md` | 2522 | SKILL.md `loop-me` — Phỏng vấn người dùng về các quy trình lặp lại để viết thành spec workflow trong workspace. Mô tả 78 B, thân 2312 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — bản beta |
| `skills/in-progress/loop-me/agents/openai.yaml` | 140 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/in-progress/setup-ts-deep-modules/SKILL.md` | 7546 | SKILL.md `setup-ts-deep-modules` — Gắn dependency-cruiser vào repo TypeScript để mỗi gói là một module sâu. Mô tả 185 B, thân 7280 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — TypeScript |
| `skills/in-progress/setup-ts-deep-modules/agents/openai.yaml` | 149 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/in-progress/setup-ts-deep-modules/dependency-cruiser.config.cjs` | 3712 | Cấu hình dependency-cruiser cho TypeScript | KHÔNG ÁP DỤNG |
| `skills/in-progress/writing-beats/SKILL.md` | 4855 | SKILL.md `writing-beats` — Giai đoạn khai thác cho viết bài: ghép chất liệu thô thành hành trình các nhịp. Mô tả 111 B, thân 4671 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — viết bài, bản beta |
| `skills/in-progress/writing-beats/agents/openai.yaml` | 142 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/in-progress/writing-fragments/SKILL.md` | 3558 | SKILL.md `writing-fragments` — Giai đoạn khám phá cho viết bài: khai thác mảnh vụn bằng phỏng vấn. Mô tả 57 B, thân 3424 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — viết bài, bản beta |
| `skills/in-progress/writing-fragments/agents/openai.yaml` | 140 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/in-progress/writing-shape/SKILL.md` | 5922 | SKILL.md `writing-shape` — Giai đoạn khai thác cho viết bài: tạo hình bài viết từng đoạn từ chất liệu thô. Mô tả 79 B, thân 5770 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — viết bài, bản beta |
| `skills/in-progress/writing-shape/agents/openai.yaml` | 144 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/misc/README.md` | 684 | README bucket `misc`: công cụ ít dùng, không quảng bá trong plugin | KHÔNG ÁP DỤNG |
| `skills/misc/git-guardrails-claude-code/SKILL.md` | 2313 | SKILL.md `git-guardrails-claude-code` — Cài hook PreToolUse chặn lệnh git nguy hiểm (`push`, `reset --hard`, `clean -f`, `branch -D`...) trước khi chạy. Mô tả 243 B, thân 2015 B; do model gọi: mô tả nạp MỖI phiên; NGOÀI plugin | KHÔNG — `misc/` bị đóng băng ở nguồn (`.out-of-scope/frozen-misc-skills.md`); ta có cửa mạnh hơn |
| `skills/misc/git-guardrails-claude-code/agents/openai.yaml` | 112 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/misc/git-guardrails-claude-code/scripts/block-dangerous-git.sh` | 507 | Hook bash chặn `git push`, `reset --hard`, `clean -f`...; in *"The user has prevented you from doing this."* | KHÔNG ÁP DỤNG — KHÔNG chạy; ta có `tools/cua_bash_an_toan.py` |
| `skills/misc/migrate-to-shoehorn/SKILL.md` | 2795 | SKILL.md `migrate-to-shoehorn` — Chuyển test từ `as` sang `@total-typescript/shoehorn` để truyền dữ liệu từng phần. Mô tả 168 B, thân 2579 B; do model gọi: mô tả nạp MỖI phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — TypeScript |
| `skills/misc/migrate-to-shoehorn/agents/openai.yaml` | 110 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/misc/scaffold-exercises/SKILL.md` | 3589 | SKILL.md `scaffold-exercises` — Dựng cấu trúc thư mục bài tập qua lint `ai-hero-cli`. Mô tả 204 B, thân 3338 B; do model gọi: mô tả nạp MỖI phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — khoá học của tác giả |
| `skills/misc/scaffold-exercises/agents/openai.yaml` | 108 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/misc/setup-pre-commit/SKILL.md` | 2258 | SKILL.md `setup-pre-commit` — Cài Husky + lint-staged (Prettier) + kiểm kiểu + test cho pre-commit. Mô tả 238 B, thân 1975 B; do model gọi: mô tả nạp MỖI phiên; NGOÀI plugin | KHÔNG ÁP DỤNG — Node/Husky; ta là Python |
| `skills/misc/setup-pre-commit/agents/openai.yaml` | 99 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/productivity/README.md` | 1481 | README bucket `productivity` | KHÔNG ÁP DỤNG |
| `skills/productivity/grill-me/SKILL.md` | 157 | SKILL.md `grill-me` — Gốc 157 B chỉ gọi Skill tool với `grilling`. Mô tả 51 B, thân 38 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — không có nội dung riêng |
| `skills/productivity/grill-me/agents/openai.yaml` | 137 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/productivity/grilling/SKILL.md` | 2049 | SKILL.md `grilling` — Phỏng vấn người dùng theo cây quyết định, từng vòng cả biên giới câu hỏi, mỗi câu kèm đáp án đề xuất. Mô tả 152 B, thân 1860 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | KHÔNG — leader không liên lạc được trong phiên đám mây; không có địa chỉ lỗi N lặp lại |
| `skills/productivity/grilling/agents/openai.yaml` | 113 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/productivity/handoff/SKILL.md` | 940 | SKILL.md `handoff` — Nén hội thoại thành tài liệu bàn giao lưu ở thư mục tạm, kèm danh sách skill nên gọi và che thông tin nhạy cảm. Mô tả 86 B, thân 730 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG — dự án đã có HANDOFF tự duy trì |
| `skills/productivity/handoff/agents/openai.yaml` | 141 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/productivity/teach/GLOSSARY-FORMAT.md` | 2122 | Định dạng từ vựng cho workspace dạy học | KHÔNG ÁP DỤNG |
| `skills/productivity/teach/LEARNING-RECORD-FORMAT.md` | 2747 | Định dạng bản ghi học tập | KHÔNG ÁP DỤNG |
| `skills/productivity/teach/MISSION-FORMAT.md` | 1540 | Định dạng `MISSION.md` (lý do học) | KHÔNG ÁP DỤNG |
| `skills/productivity/teach/RESOURCES-FORMAT.md` | 1924 | Định dạng `RESOURCES.md` (nguồn tin cậy) | KHÔNG ÁP DỤNG |
| `skills/productivity/teach/SKILL.md` | 9733 | SKILL.md `teach` — Dạy người dùng một kỹ năng qua nhiều phiên trong một workspace có MISSION, RESOURCES, GLOSSARY, bản ghi học tập. Mô tả 61 B, thân 9554 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — 9.554 B thân cho một việc ngoài phạm vi dự án |
| `skills/productivity/teach/agents/openai.yaml` | 139 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/productivity/to-questionnaire/SKILL.md` | 2904 | SKILL.md `to-questionnaire` — Biến quyết định người dùng không tự trả lời được thành bảng câu hỏi cho người khác điền. Mô tả 88 B, thân 2740 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — ta đã có khuôn câu hỏi `tools/so_tay.py hoi` |
| `skills/productivity/to-questionnaire/agents/openai.yaml` | 166 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/productivity/wait-what/SKILL.md` | 396 | SKILL.md `wait-what` — Yêu cầu agent nói lại tin nhắn trước theo ASD-STE100 Simplified Technical English và từ vựng `GLOSSARY.md`. Mô tả 52 B, thân 275 B; do người gọi (`disable-model-invocation`), mô tả KHÔNG nạp mỗi phiên; trong plugin | KHÔNG ÁP DỤNG — tiếng Anh kỹ thuật giản lược; người dùng cần tiếng Việt |
| `skills/productivity/wait-what/agents/openai.yaml` | 158 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |
| `skills/productivity/writing-for-agents/SKILL-MECHANICS.md` | 2629 | Nhánh riêng cho skill: frontmatter, chọn cách gọi, skill router | LẤY Ý — chỉ dùng để kiểm hình dạng `description` (cùng CHANGELOG.md:39) |
| `skills/productivity/writing-for-agents/SKILL.md` | 10886 | SKILL.md `writing-for-agents` — Tham chiếu viết tài liệu cho agent: con trỏ ngữ cảnh (pointer), tải nhận thức vs tải ngữ cảnh, thang tiết lộ dần, một nguồn sự thật, săn câu 'no-op'. Mô tả 103 B, thân 10736 B; do model gọi: mô tả nạp MỖI phiên; trong plugin | LẤY Ý — ý 'một nguồn sự thật' + 'no-op' (dòng 78, 81) thành sửa E6; thêm skill thì trùng luật BƯỚC 145 nên không |
| `skills/productivity/writing-for-agents/agents/openai.yaml` | 102 | Metadata giao diện Codex (tên hiển thị, mô tả ngắn, `allow_implicit_invocation`) | KHÔNG ÁP DỤNG — giao diện Codex, ta dùng Claude Code |

Kiểm máy phủ bảng (so cột đường dẫn của mục 2 với cây git ghim):

```bash
comm -3 <(git -C /tmp/mp ls-tree -r --name-only 49dd158 | sort) <(sed -n '/^## 2\./,/^## 3\./p' docs/danh-gia-skills-mattpocock.md | grep -oP '^\| `\K[^`]+(?=` \| [0-9]+ \|)' | sort) | awk '{ if (substr($0,1,1)=="\t") th++; else tm++ } END { print "thiếu " tm+0 " · thừa " th+0 }'
```

In ra `thiếu 0 · thừa 0` khi bảng phủ đủ 190 file, không dòng nào thừa (`thiếu` = có trong cây mà không có trong bảng; `thừa` = có trong bảng mà không có trong cây).

## 3. Từng skill (38)

Cột `mô tả B` là phần được nạp MỖI phiên **chỉ khi** skill do model gọi; skill do người gọi (`disable-model-invocation: true`) không vào danh sách nạp (`.agents/invocation.md`). `thân B` chỉ trả khi gọi. Chồng lấn: chỉ so được với luật dự án và skill trong repo; **skill cấp người dùng (`~/.claude`) không nhìn thấy được từ phiên đám mây** (mục 8).

| skill | cách gọi · plugin | mô tả B | thân B | tóm tắt | chồng lấn | phán quyết |
|---|---|---|---|---|---|---|
| `ask-matt` (engineering) | người gọi · plugin: có | 83 | 12443 | Bộ định tuyến: hỏi tình huống rồi chỉ ra skill hoặc luồng phù hợp (luồng chính ý tưởng → giao). Đọc SKILL.md của skill đích trước khi mô tả nó. | Không chồng lấn: dự án chỉ có 1 skill, `ask-matt` định tuyến trong bộ nguồn. | KHÔNG ÁP DỤNG — định tuyến 38 skill; ta thêm 0 skill nên không có gì để định tuyến |
| `code-review` (engineering) | model gọi · plugin: có | 421 | 6209 | Review diff từ một điểm cố định theo hai trục (Standards, Spec) bằng hai sub-agent song song, gộp báo cáo. Có sẵn danh sách mùi code Fowler làm nền. | Chồng với cổng `kiem-dinh` + `tools/chan_bia_so_lieu.py --quet-repo` về vai kiểm; trùng tên lệnh dựng sẵn của harness (`.out-of-scope/harness-name-collisions.md`). | KHÔNG — không có địa chỉ lỗi N lặp lại; trùng vai cổng; mô tả 421 B là mô tả lớn nhất bộ, trả MỌI phiên |
| `codebase-design` (engineering) | model gọi · plugin: có | 265 | 6137 | Từ vựng module sâu: module, interface, seam, adapter, depth, leverage, locality. Dùng chung cho skill khác khi cần nói về thiết kế. | Vai trùng một phần với `MO-XE-KIEN-TRUC.md` (đo thành phần nào chạy thật). | KHÔNG — ví dụ thuần TypeScript/hướng đối tượng; không có địa chỉ lỗi N; 265 B mô tả mỗi phiên |
| `diagnosing-bugs` (engineering) | model gọi · plugin: có | 156 | 8464 | Vòng chẩn đoán: dựng vòng phản hồi bấm được trước (pha 1), rồi giả thuyết, đo, sửa, kiểm lại. Pha 5 yêu cầu `diff` đột biến với bản gốc trước khi tin phép đỏ. | Chồng với Bước 3 (đột biến) và `references/bay.md` của `quy-trinh-lam-viec`. | LẤY Ý — ý dòng 125 (`diff` chứng minh đột biến có hiệu lực) thành mệnh đề của gác mới; cả skill thì trùng vai Bước 3 nên không thêm |
| `domain-modeling` (engineering) | model gọi · plugin: có | 151 | 3151 | Xây và mài mô hình miền: chất vấn thuật ngữ, viết `GLOSSARY.md` và ADR ngay khi chúng kết tinh. Tạo file lười, khi có thứ để ghi. | Vai ADR trùng `docs/STATE.md` (mục BƯỚC) và `NGUYEN-TAC-DO-LUONG.md`. | KHÔNG — dự án đã có sổ quyết định; không có địa chỉ lỗi N lặp lại về thuật ngữ |
| `grill-with-docs` (engineering) | người gọi · plugin: có | 106 | 66 | Gốc 247 B chỉ gọi Skill tool hai lần: `grilling` rồi `domain-modeling`. | Phụ thuộc hai skill ở trên. | KHÔNG ÁP DỤNG — không có nội dung riêng |
| `implement` (engineering) | người gọi · plugin: có | 62 | 491 | Làm một ticket: lấy ticket theo tham chiếu, gọi `tdd` tại các seam đã thoả thuận, chạy kiểm kiểu rồi toàn bộ test, gọi `code-review`, commit. | Chồng với Bước 4 (năm cổng). | KHÔNG ÁP DỤNG — gắn với tracker; Bước 4 đã là bản Python/pytest của chuỗi này |
| `implement-spec` (engineering) | người gọi · plugin: có | 59 | 2647 | Triển khai cả spec trên một nhánh tích hợp: đọc ticket như đồ thị tác vụ, chạy các sub-agent triển khai song song trên biên giới sẵn sàng, mỗi cái một worktree. | Không chồng lấn; dự án không dùng tracker + worktree song song. | KHÔNG ÁP DỤNG — cần issue tracker và `/setup-matt-pocock-skills`; quy trình giao việc của ta là phiếu leader → PR |
| `improve-codebase-architecture` (engineering) | người gọi · plugin: có | 125 | 5786 | Quét codebase tìm cơ hội làm sâu module, xuất báo cáo HTML trực quan rồi phỏng vấn người dùng về cái họ chọn. | Chồng một phần với `MO-XE-KIEN-TRUC.md`. | KHÔNG ÁP DỤNG — mục tiêu AI-navigability của TypeScript; báo cáo HTML dùng CDN Tailwind/Mermaid |
| `pr` (engineering) | model gọi · plugin: có | 29 | 3919 | Mẫu thân PR: Summary (sơ đồ nhỏ nhất cho thấy thay đổi), Evidence trước/sau, cửa một chiều hay hai chiều. Ghi công Dex Horthy. | Thân PR của ta do phiếu giao quy định từng lần. | KHÔNG — không có địa chỉ lỗi N lặp lại; thân PR đã có mẫu trong phiếu |
| `prototype` (engineering) | model gọi · plugin: có | 179 | 2714 | Prototype bỏ đi để trả lời một câu hỏi thiết kế: nhánh logic (HTML một file) hoặc nhánh UI (nhiều biến thể trên một route). | Không chồng; dự án cấm thành phần trang trí chưa đo (`MO-XE-KIEN-TRUC.md`). | KHÔNG ÁP DỤNG — sinh giao diện web; app của ta là Streamlit và mọi câu hỏi thiết kế được trả lời bằng đo |
| `research` (engineering) | model gọi · plugin: có | 238 | 519 | Chạy một agent nền điều tra câu hỏi từ nguồn chính thống, ghi kết quả thành một file Markdown có trích dẫn. | Chồng với luồng NotebookLM (Quy tắc 3) về vai 'luồng thông tin thứ hai'. | KHÔNG — trùng tên lệnh dựng sẵn `/research` của harness khác; không có địa chỉ lỗi N lặp lại |
| `retro` (engineering) | người gọi · plugin: có | 46 | 4258 | Nhìn lại một phiên và đề xuất đổi MÔI TRƯỜNG của agent (con trỏ điều hướng, kiểm tự động, luật review, AGENTS.md, công cụ). Tìm câu 'no-op' trong file chỉ dẫn lớn. | Chồng với Bước 6 của `quy-trinh-lam-viec` và `soat-tuan.yml` (soát định kỳ). | KHÔNG — vai đã có, kèm máy; ý 'no-op' ta đã làm ở BƯỚC 145 |
| `setup-matt-pocock-skills` (engineering) | người gọi · plugin: có | 182 | 6712 | Cấu hình repo cho các skill engineering: chọn issue tracker, từ vựng nhãn triage, bố cục tài liệu miền. | Không chồng lấn. | KHÔNG ÁP DỤNG — phụ thuộc cứng của nhóm skill tracker; ta không dùng issue tracker |
| `tdd` (engineering) | model gọi · plugin: có | 149 | 3448 | Vòng đỏ → xanh với seam thoả thuận trước, test qua giao diện công khai, chỉ mock ở ranh giới hệ thống. | Chồng với Bước 3 (đột biến vòng lặp) và gác AST; `NGUYEN-TAC-DO-LUONG.md`. | KHÔNG — ví dụ TypeScript; ta đã có luật mạnh hơn (đột biến đến khi MỌI phát đỏ) |
| `to-spec` (engineering) | người gọi · plugin: có | 151 | 2825 | Biến cuộc hội thoại hiện tại thành spec và đăng lên tracker, không phỏng vấn. | Không chồng lấn. | KHÔNG ÁP DỤNG — cần tracker và nhãn `ready-for-agent` |
| `to-tickets` (engineering) | người gọi · plugin: có | 247 | 5495 | Chia kế hoạch/spec thành các ticket đạn đường (tracer bullet), mỗi ticket khai ticket nó bị chặn bởi. | Chồng nhẹ với `docs/LO-TRINH.md` (giai đoạn, mốc). | KHÔNG ÁP DỤNG — cần tracker; mốc của ta đã là `**Mốc:**` trong STATE |
| `triage` (engineering) | người gọi · plugin: có | 136 | 6356 | Máy trạng thái phân loại issue và PR ngoài, viết bản tóm tắt cho agent, mọi bình luận mở đầu bằng lời khai AI. | Không chồng lấn. | KHÔNG ÁP DỤNG — ta không nhận issue ngoài |
| `wayfinder` (engineering) | người gọi · plugin: có | 197 | 12114 | Lập bản đồ việc lớn hơn một phiên làm vé quyết định trên tracker, giải từng vé cho tới khi đường tới đích hiện rõ. | Chồng với `docs/LO-TRINH.md` + `docs/QUYET-DINH-CHO.md`. | KHÔNG ÁP DỤNG — tracker; lộ trình đã duyệt 08/10/2026 |
| `wizard` (engineering) | model gọi · plugin: có | 313 | 3775 | Sinh một wizard bash tương tác dẫn người qua các bước chỉ người làm được (mở URL, dán khoá, ghi `.env`, `gh secret set`). | Không chồng lấn. | KHÔNG ÁP DỤNG — người dùng trên Windows; template.sh 9.498 B là script chạy được, ta cấm chạy |
| `chief-of-staff` (in-progress) | người gọi · plugin: không | 74 | 1964 | Theo đuổi mục tiêu dài hạn trong một phiên bằng cách điều phối sub-agent và lịch. | Không chồng lấn. | KHÔNG ÁP DỤNG — bản beta, bị loại khỏi plugin |
| `claude-handoff` (in-progress) | người gọi · plugin: không | 97 | 1196 | Bàn giao hội thoại cho một agent nền mới qua `claude --bg --name ... -- "$(cat <file>)"`. | Trùng `docs/HANDOFF.md`; tự khởi chạy tiến trình agent. | KHÔNG — bản beta; mở tiến trình agent nền là hành động ra ngoài, không an toàn để bật |
| `loop-me` (in-progress) | người gọi · plugin: không | 78 | 2312 | Phỏng vấn người dùng về các quy trình lặp lại để viết thành spec workflow trong workspace. | Không chồng lấn. | KHÔNG ÁP DỤNG — bản beta |
| `setup-ts-deep-modules` (in-progress) | người gọi · plugin: không | 185 | 7280 | Gắn dependency-cruiser vào repo TypeScript để mỗi gói là một module sâu. | Không chồng lấn. | KHÔNG ÁP DỤNG — TypeScript |
| `writing-beats` (in-progress) | người gọi · plugin: không | 111 | 4671 | Giai đoạn khai thác cho viết bài: ghép chất liệu thô thành hành trình các nhịp. | Không chồng lấn. | KHÔNG ÁP DỤNG — viết bài, bản beta |
| `writing-fragments` (in-progress) | người gọi · plugin: không | 57 | 3424 | Giai đoạn khám phá cho viết bài: khai thác mảnh vụn bằng phỏng vấn. | Không chồng lấn. | KHÔNG ÁP DỤNG — viết bài, bản beta |
| `writing-shape` (in-progress) | người gọi · plugin: không | 79 | 5770 | Giai đoạn khai thác cho viết bài: tạo hình bài viết từng đoạn từ chất liệu thô. | Không chồng lấn. | KHÔNG ÁP DỤNG — viết bài, bản beta |
| `git-guardrails-claude-code` (misc) | model gọi · plugin: không | 243 | 2015 | Cài hook PreToolUse chặn lệnh git nguy hiểm (`push`, `reset --hard`, `clean -f`, `branch -D`...) trước khi chạy. | Trùng và yếu hơn `tools/cua_bash_an_toan.py` (luật khai nguồn sự cố, đã bị đột biến). | KHÔNG — `misc/` bị đóng băng ở nguồn (`.out-of-scope/frozen-misc-skills.md`); ta có cửa mạnh hơn |
| `migrate-to-shoehorn` (misc) | model gọi · plugin: không | 168 | 2579 | Chuyển test từ `as` sang `@total-typescript/shoehorn` để truyền dữ liệu từng phần. | Không chồng lấn. | KHÔNG ÁP DỤNG — TypeScript |
| `scaffold-exercises` (misc) | model gọi · plugin: không | 204 | 3338 | Dựng cấu trúc thư mục bài tập qua lint `ai-hero-cli`. | Không chồng lấn. | KHÔNG ÁP DỤNG — khoá học của tác giả |
| `setup-pre-commit` (misc) | model gọi · plugin: không | 238 | 1975 | Cài Husky + lint-staged (Prettier) + kiểm kiểu + test cho pre-commit. | Chồng ý với 5 cổng của Bước 4 (chạy ở CI/tay). | KHÔNG ÁP DỤNG — Node/Husky; ta là Python |
| `grill-me` (productivity) | người gọi · plugin: có | 51 | 38 | Gốc 157 B chỉ gọi Skill tool với `grilling`. | Phụ thuộc `grilling`. | KHÔNG ÁP DỤNG — không có nội dung riêng |
| `grilling` (productivity) | model gọi · plugin: có | 152 | 1860 | Phỏng vấn người dùng theo cây quyết định, từng vòng cả biên giới câu hỏi, mỗi câu kèm đáp án đề xuất. | Gần `tools/so_tay.py hoi` về hình dạng câu hỏi nhưng khác vai (hỏi NGƯỜI, không hỏi sổ tay). | KHÔNG — leader không liên lạc được trong phiên đám mây; không có địa chỉ lỗi N lặp lại |
| `handoff` (productivity) | người gọi · plugin: có | 86 | 730 | Nén hội thoại thành tài liệu bàn giao lưu ở thư mục tạm, kèm danh sách skill nên gọi và che thông tin nhạy cảm. | Trùng `docs/HANDOFF.md` và `docs/STATE.md`. | KHÔNG — dự án đã có HANDOFF tự duy trì |
| `teach` (productivity) | người gọi · plugin: có | 61 | 9554 | Dạy người dùng một kỹ năng qua nhiều phiên trong một workspace có MISSION, RESOURCES, GLOSSARY, bản ghi học tập. | Không chồng lấn. | KHÔNG ÁP DỤNG — 9.554 B thân cho một việc ngoài phạm vi dự án |
| `to-questionnaire` (productivity) | người gọi · plugin: có | 88 | 2740 | Biến quyết định người dùng không tự trả lời được thành bảng câu hỏi cho người khác điền. | Chồng nhẹ với mục 'Câu hỏi chờ leader' của phiếu giao. | KHÔNG ÁP DỤNG — ta đã có khuôn câu hỏi `tools/so_tay.py hoi` |
| `wait-what` (productivity) | người gọi · plugin: có | 52 | 275 | Yêu cầu agent nói lại tin nhắn trước theo ASD-STE100 Simplified Technical English và từ vựng `GLOSSARY.md`. | Không chồng lấn. | KHÔNG ÁP DỤNG — tiếng Anh kỹ thuật giản lược; người dùng cần tiếng Việt |
| `writing-for-agents` (productivity) | model gọi · plugin: có | 103 | 10736 | Tham chiếu viết tài liệu cho agent: con trỏ ngữ cảnh (pointer), tải nhận thức vs tải ngữ cảnh, thang tiết lộ dần, một nguồn sự thật, săn câu 'no-op'. | Chồng với luật 'giữ skill gọn' của `SKILL.md` (BƯỚC 145). | LẤY Ý — ý 'một nguồn sự thật' + 'no-op' (dòng 78, 81) thành sửa E6; thêm skill thì trùng luật BƯỚC 145 nên không |

### Kết quả: THÊM 0 · LẤY Ý 2 skill (cùng vài file khác)

`THÊM 0` là kết quả hợp lệ. Trên 38 skill: KHÔNG ÁP DỤNG 25 (cần issue tracker, TypeScript/Node hoặc việc ngoài phạm vi); KHÔNG 11 (trùng vai với `quy-trinh-lam-viec` hoặc luật dự án, hoặc không có địa chỉ lỗi lặp lại); LẤY Ý 2 (ý dùng được nhưng đủ nhỏ để đi vào skill hiện có). Ngoài skill, hai file khác cũng LẤY Ý: `CHANGELOG.md` và trang `docs/engineering/implement-spec.md`.

| LẤY Ý | nguồn `path:line` | đã vào đâu | địa chỉ grep |
|---|---|---|---|
| Chứng minh đột biến có hiệu lực trước khi tin phép đỏ | `skills/engineering/diagnosing-bugs/SKILL.md:125` · `.changeset/diagnosing-bugs-prove-mutation.md:5` | mệnh đề *"thay vào phải làm AST ĐỔI"* của gác ví dụ chạy được | `tests/test_skill_quy_trinh.py::test_VI_DU_neo_chay_duoc` · lỗi 171 |
| `description` YAML sai hình dạng (`: ` không nháy) làm skill bị bỏ qua lặng lẽ | `CHANGELOG.md:39` · `skills/productivity/writing-for-agents/SKILL-MECHANICS.md` | kiểm hình dạng `description` KHÔNG `import yaml` (PyYAML không có trong `requirements.txt`) | `tests/test_skill_quy_trinh.py::_mo_ta_yaml_hong` · lỗi 171 |
| Một nguồn sự thật + săn câu 'no-op' | `skills/productivity/writing-for-agents/SKILL.md:78` · `:79` · `:81` | gỡ đoạn lặp thứ đã có ở `references/` (E6, E7); dòng 79: bảng cửa của `SKILL.md` là *bản sao* của `docs/cua-du-an.json`, nên hàng thiếu là hệ quả (E5) | `SKILL.md` BƯỚC 145 · lỗi 172 |
| Worktree chỉ có thứ git theo dõi: test đọc fixture bị gitignore có thể SKIP lặng lẽ | `docs/engineering/implement-spec.md:68` | mục *Phiên đám mây* của `cong-thuc-chay.md`: đọc lý do skip bằng `-rs` | `references/cong-thuc-chay.md` · lỗi 173 |

## 4. Kiểm `SKILL.md` và `references/` từng dòng

Mỗi sửa một dòng: vị trí cũ · vì sao lỗi thời/sai (kèm lệnh kiểm) · văn bản mới · nguồn cảm hứng (`path:line` trong `/tmp/mp`) nếu có. Lệnh kiểm chạy ở gốc repo ngày 12/10/2026.

| # | vị trí cũ | vì sao lỗi thời/sai · lệnh kiểm | văn bản mới | nguồn cảm hứng |
|---|---|---|---|---|
| E1 | `SKILL.md` Bước 2, ví dụ `thay("paper_metrics.py", "N_TOI_THIEU = 113", …)` | neo chưa từng có trong mã: `grep -c "N_TOI_THIEU = 113" paper_metrics.py` → 0; `N_TOI_THIEU = round(N_DAY_DU / 4)` là giá trị SUY RA nên `thay()` nổ `NeoMoHo`. Sinh ở `2c88dfe` (07/09/2026) | `thay("tools/do_token_phien.py", "NGUONG_GHI_LAI = 200_000", …)`: `grep -c "NGUONG_GHI_LAI = 200_000" tools/do_token_phien.py` → 1 | — |
| E2 | `SKILL.md` Bước 3, ví dụ `dot_bien(…, "z=2,30", "z=1,00", …)` | neo khớp **2** lần, cả hai trong chú thích `#:`: `grep -c "z=2,30" paper_metrics.py` → 2 → `dot_bien` nổ | neo `"Z_BIEN_HAI = 2.30"`: `grep -c "Z_BIEN_HAI = 2.30" paper_metrics.py` → 1 | `skills/engineering/diagnosing-bugs/SKILL.md:125` |
| E3 | `tools/va_an_toan.py` docstring *CÁCH DÙNG* | chép đúng hai ví dụ chết ở E1–E2 (`git show HEAD:tools/va_an_toan.py \| grep -n -e N_TOI_THIEU -e z=2,30` → dòng 38, 40) | hai ví dụ chạy được như E1–E2 | — |
| E4 | `SKILL.md` Bước 2, sau câu về LF | không có gác cho các ví dụ lệnh Python | thêm một câu trỏ `tests/test_skill_quy_trinh.py::test_VI_DU_neo_chay_duoc` | `CHANGELOG.md:39` |
| E5 | `SKILL.md` bảng *Cửa tự động*: *"Bảy cửa"* nhưng 6 hàng | thiếu `tools/cua_ho_so.py`, hook thứ bảy khai ở `docs/cua-du-an.json` từ `a42d8bd` (15/09/2026): `git show HEAD:.claude/skills/quy-trinh-lam-viec/SKILL.md \| grep -c "^\| .tools/"` → 6 | thêm hàng `cua_ho_so.py` (Pre · Read/Edit) | `skills/productivity/writing-for-agents/SKILL.md:79` |
| E6 | `SKILL.md` mục NotebookLM, đoạn *"độ tươi"* | lặp 5 dòng của `references/soat-cheo-notebooklm.md`, mục *Nạp lại nguồn* (`grep -n -e raw.githubusercontent -e "7 ký tự" references/soat-cheo-notebooklm.md` → dòng 132, 142) | còn 3 dòng: giữ luật THÊM TRƯỚC XOÁ SAU + trỏ mục tham chiếu | `skills/productivity/writing-for-agents/SKILL.md:78` |
| E7 | `SKILL.md`: câu *"Đường ngoài repo đổi dưới chân…"* và câu *"Gác so chữ đã đo và bỏ…"* | câu thứ nhất lặp với mục *Nhịp soát định kỳ* (`grep -n kiem_duong_ngoai_repo SKILL.md` → dòng 335 còn); câu thứ hai là lịch sử, bản đầy đủ ở `docs/lich-su/SKILL-md-2026-09-30.md:664` | gỡ cả hai | `skills/productivity/writing-for-agents/SKILL.md:81` |
| E8 | `SKILL.md` *Chỗ đã trượt 19/27 lượt* | con số không ngày | thêm *(đo 18/09/2026)* | — |
| E9 | `SKILL.md` Bước 4, *Chi tiết: `references/cong-thuc-chay.md`* | công thức đó chỉ có cho máy local Windows | trỏ thêm tới mục *Phiên đám mây (không `.venv`, không `vnstock`)* | `docs/engineering/implement-spec.md:68` |
| E10 | `references/loi-da-mac.md`, câu sau dòng tự khai của bảng: *"Tám mươi lăm trên một trăm năm mươi… Năm cái còn lại — 6, 8, 9, 13, 14"* | `tools/doc_bang_loi.py` chỉ đọc phần in đậm; văn xuôi đứng nguyên từ `910dcf7` (08/09/2026). `./.venv/Scripts/python.exe tools/doc_bang_loi.py` in 85/150 cạnh câu nói *"năm cái"* trong khi 65 dòng chưa bị máy chặn | *"Tám mươi sáu trên một trăm năm mươi ba"* (con số máy đếm) + trỏ lệnh thay vì liệt kê | — |
| E11 | `references/loi-da-mac.md` cuối bảng | thiếu ba lỗi của chính phiên này | hàng **171** (ví dụ chết, ✅ một hình dạng), **172** (đại lượng thứ hai cạnh con số được máy đọc, ⚠️), **173** (công thức đám mây rải rác, ❌); `docs/loi-phan-lop.json` khai ba lớp | — |
| E12 | `references/cong-thuc-chay.md` mục *Năm cổng* | thời gian *"cổng 1 ≈ 150s · cổng 4 ≈ 220s"* đo 07/09/2026 ở máy local; phiên đám mây khác hẳn | đánh dấu 🔴 số cũ, thêm số đo 12/10/2026 | — |
| E13 | `references/soat-cheo-notebooklm.md` | không có đường dành cho phiên đám mây không mở được sổ tay | mục *Phiên đám mây*: `buoc_cham_luat.py` → nếu chạm luật thì `so_tay.py hoi`, dán câu hỏi vào thân PR, mở PR DRAFT | `BƯỚC 161–164, 166, 182` trong `docs/STATE.md` |

**Báo cáo, không sửa** (ngoài phạm vi skill): `docs/cua-du-an.json:20` và `tools/kiem_cua_song.py:53` vẫn viết *"báo 0/6"* khi đã có bảy cửa (`grep -n "0/6" docs/cua-du-an.json tools/kiem_cua_song.py`).

### Số đo trước/sau của `SKILL.md`

```bash
git show HEAD:.claude/skills/quy-trinh-lam-viec/SKILL.md | wc -mc    # trước: ký tự, byte
wc -mc .claude/skills/quy-trinh-lam-viec/SKILL.md                    # sau
```

| | ký tự | byte | token ƯỚC LƯỢNG (3,0 ký tự/token) |
|---|---|---|---|
| trước | 17976 | 21953 | ≈5992 |
| sau | 17936 | 21886 | ≈5979 |
| mô tả (frontmatter) | không đổi | 511 | ≈170 |

Trần của gác `tests/test_do_token_phien.py` là 18.000 ký tự: còn dư 64 ký tự.

### Luật nào bị đổi?

**Không có luật cũ nào bị đổi.** Chín sửa trên là con trỏ chết, ví dụ chết, bảng thiếu hàng, con số không ngày và đoạn lặp. **Thêm một luật mới**: *ví dụ lệnh Python trong skill phải chạy được* (E4, gác `test_VI_DU_neo_chay_duoc`; lỗi 171). Hai câu bị gỡ ở E7 không phải luật: một lặp, một là lịch sử.

## 5. Plugin: số đo

- `plugin.json` v1.3.1: 1690 B, khoá `name · version · description · author · homepage · repository · license · keywords · skills`. **Không** có khoá `hooks`, `mcpServers`, `commands`, `agents`.
- Tổng `description`: trường `description` của chính `plugin.json` 154 B; mô tả 27 skill đóng gói = **3.888 B** (cả 38 skill: 5.422 B). Trong 27 có 11 skill do model gọi (mô tả nạp MỖI phiên) = **2.156 B**; 16 skill do người gọi không vào danh sách nạp.
- Ước lượng token (hệ số 3.0, nguồn tiếng Anh nên đây là cận TRÊN): cận trên nạp mỗi phiên ≈ 719 token (11 skill); nếu một ngày `disable-model-invocation` bị bỏ qua thì ≈ 1296 token (27 skill). Cộng thêm phần định dạng của danh sách (tên, dấu phân cách) KHÔNG đo được ở đây. Dự án hiện trả ≈170 token cho mô tả của `quy-trinh-lam-viec`.
- Thân skill chỉ nạp khi gọi. 11 skill model gọi cộng 50.932 B thân; thân lớn nhất trong 27 skill đóng gói là `ask-matt` (12.443 B), `wayfinder` (12.114 B), `writing-for-agents` (10.736 B).
- **Hook / MCP / lệnh / script**: plugin đóng gói **không có hook, MCP server, lệnh hay agent**. File chạy được nằm trong skill đóng gói: `skills/engineering/diagnosing-bugs/scripts/hitl-loop.template.sh` (chạy khi skill chỉ dẫn) và `skills/engineering/wizard/template.sh`. Ngoài plugin: `skills/misc/git-guardrails-claude-code/scripts/block-dangerous-git.sh`, `scripts/link-skills.sh`, `scripts/list-skills.sh`, `scripts/sync-plugin-version.mjs`, `skills/in-progress/setup-ts-deep-modules/dependency-cruiser.config.cjs`.
- **Va chạm tên**: đọc `.out-of-scope/harness-name-collisions.md` — tác giả từ chối đổi tên skill. Các tên có nguy cơ trùng lệnh dựng sẵn của harness: `/code-review`, `/research`, `/prototype`; cách đi qua là gọi có tiền tố plugin (`/mattpocock-skills:research`). Với dự án: không trùng `quy-trinh-lam-viec`; trùng với skill cấp người dùng thì **không kiểm được** (mục 8).
- **Lệnh cài (từ `.agents/install-block.md`, KHÔNG chạy)**:

```bash
claude plugin install mattpocock-skills@claude-plugins-official
```

  Đường thay thế qua marketplace của chính repo nguồn (`.claude-plugin/marketplace.json`, `source: ./`):

```bash
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock
```

- **Lệnh gỡ**: repo nguồn KHÔNG ghi lệnh gỡ (`grep -ni uninstall` trên cây ghim chỉ trúng một câu về `triage`). Lệnh con có thật theo `claude plugin --help` (đọc trợ giúp, không chạy):

```bash
claude plugin uninstall mattpocock-skills
```

  Chưa thử vì không cài. Kèm `--keep-data` nếu muốn giữ `~/.claude/plugins/data/{id}/`; `claude plugin details <tên>` in kho thành phần và chi phí token ước tính của chính Claude Code — chỉ chạy được SAU khi cài, nên đây là bước đo nên làm nếu người dùng quyết định cài.

## 6. Đáng ngờ

Không câu nào trong nguồn cố điều khiển agent đọc báo cáo này. Những chỗ chạm tới hành động ra ngoài hoặc trông giống chỉ dẫn gửi agent — trích nguyên văn, KHÔNG làm theo:

1. `skills/in-progress/claude-handoff/SKILL.md:8` — *"…launch a background agent seeded with it as its prompt: `claude --bg --name \"<descriptive name>\" -- \"$(cat <summary file>)\"`"*: tự mở tiến trình agent nền với toàn bộ bản tóm tắt làm prompt. Ngoài plugin (bản beta).
2. `skills/misc/git-guardrails-claude-code/scripts/block-dangerous-git.sh` — in *"BLOCKED: … The user has prevented you from doing this."* và `exit 2`: câu gửi thẳng cho agent để chặn lệnh; chặn cả `git push` mọi dạng. Ngoài plugin.
3. `skills/engineering/retro/SKILL.md:13` — *"This may mean searching through session logs on this machine."*: đọc nhật ký phiên của máy người dùng.
4. `docs/engineering/diagnosing-bugs.md:75` — tác giả thừa nhận Snyk gắn cờ vì skill đóng gói *"a shipped `.sh` file, instructions to run it, and outbound HTTP"* (`hitl-loop.template.sh`); tác giả coi là báo động giả, ta KHÔNG chạy script.
5. `scripts/link-skills.sh:56` — `rm -rf "$target"`: xoá thư mục đích nếu nó là thư mục thật chứ không phải liên kết.
6. `skills/engineering/setup-matt-pocock-skills/domain.md:11` — *"proceed silently. Don't flag their absence"*: lệnh im lặng khi thiếu tài liệu.
7. `.github/workflows/*.yml` dùng `secrets.GITHUB_TOKEN`/`github.token`, `package.json` có script — không đụng tới.

Không có chuỗi mã hoá, URL ngoài lạ, hay chỉ dẫn gửi dữ liệu ra ngoài. Lệnh quét: `git -C /tmp/mp grep -n -i -E "ignore (all |any )?(previous|prior)|exfiltrat|base64|wget "` → 0 dòng (kể cả `CHANGELOG.md`).

## 7. Khuyến nghị duy nhất

**(iii) Không cài plugin, không thêm skill nào.** Lý do: (a) 0/38 skill qua bốn điều kiện — 20 cần tracker hoặc TypeScript, 10 trùng vai, 3 chỉ có ý nhỏ đã đi vào skill hiện có; (b) chi phí cận trên ≈719 token mỗi phiên cho mô tả (cận trên, ước lượng) để đổi lấy thứ dự án đã có; (c) cài tạo bề mặt mới (`hitl-loop.template.sh`, `template.sh`, va chạm tên `/code-review` `/research` `/prototype`) mà không gì trong dự án đòi hỏi; (d) gác `test_CHI_CO_MOT_skill_quy_trinh` hiện khoá "đúng một skill". Không chọn (ii) vì ta không viết lại skill nguồn nào; phần giá trị đã nhận được là bản nâng cấp `quy-trinh-lam-viec`.

**Việc nên làm nếu người dùng vẫn muốn thử plugin:** cài trong một cấu hình riêng, chạy `claude plugin details mattpocock-skills` để đo chi phí token thật, rồi `claude plugin uninstall mattpocock-skills`; không nên cài vào máy làm việc chính trước khi đo.

## 8. Giới hạn

- **Skill cấp người dùng (`~/.claude/skills`) không nhìn thấy được** từ phiên đám mây; cột *chồng lấn* chỉ so với luật và skill trong repo.
- Số token là **ước lượng** (3,0 ký tự/token); không đo bằng API. Danh sách nạp của Claude Code có thể thêm phần định dạng không đo được.
- Lệnh gỡ chưa thử (không cài). Danh sách chính thức `claude-plugins-official` có thể chậm hơn commit ghim: nếu cài từ đó, phiên bản có thể khác `49dd158`.
- Đọc nguồn: `CHANGELOG.md` (55 KB) và `package-lock.json` được lướt có chọn lọc (dòng 39 của CHANGELOG và quét từ khoá), 188 file còn lại đọc tiêu đề và thân đủ để phán quyết; `docs/**` là trang người đọc, mô tả theo tiêu đề và các mục FAQ trúng từ khoá. Trong phạm vi đã quét; không phải mọi dòng được đọc kỹ như nhau.
- Không chạy script nguồn, không cài plugin, không chạm `~/.claude`.
- Gác mới `test_VI_DU_neo_chay_duoc`: neo nằm trong chuỗi thông báo vẫn qua; không chạy pytest. Còn hở được khai ở hàng 171 của `references/loi-da-mac.md`.

## 9. Giấy phép (MIT) — lời gốc

Ý tưởng ở mục 3 và 4 đến từ repo `mattpocock/skills`. Văn bản ta viết là của dự án, KHÔNG chép nguyên văn skill nguồn. Lời cấp phép chép nguyên văn:

```text
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

