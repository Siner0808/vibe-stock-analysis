# Đọc Google Sheets (chỉ đọc), cũ / một batch / một batch + decisions A:H

Lệnh (cwd = cây làm việc; chạy 16/11/2026): `../vibe_preview/.venv/Scripts/python.exe -X utf8 ../vibe_logs_280/do_sheets_280.py`

## `sheets_280_out.txt`

```
rep 0 cu_BUOC275_5get_all_values: doc 3.60 s, HTTP 6 (khong gom ket noi), tab loi []
rep 0 A_mot_batch_ca_tab: doc 1.64 s, HTTP 1 (khong gom ket noi), tab loi []
rep 0 B_mot_batch_decisions_A_H: doc 0.87 s, HTTP 1 (khong gom ket noi), tab loi []
rep 1 A_mot_batch_ca_tab: doc 1.59 s, HTTP 1 (khong gom ket noi), tab loi []
rep 1 B_mot_batch_decisions_A_H: doc 0.92 s, HTTP 1 (khong gom ket noi), tab loi []
rep 1 cu_BUOC275_5get_all_values: doc 3.51 s, HTTP 6 (khong gom ket noi), tab loi []
rep 2 B_mot_batch_decisions_A_H: doc 0.93 s, HTTP 1 (khong gom ket noi), tab loi []
rep 2 cu_BUOC275_5get_all_values: doc 3.39 s, HTTP 6 (khong gom ket noi), tab loi []
rep 2 A_mot_batch_ca_tab: doc 1.44 s, HTTP 1 (khong gom ket noi), tab loi []
cu_BUOC275_5get_all_values       trung vi 3.51 s  [3.6, 3.51, 3.39]  HTTP [6, 6, 6]
A_mot_batch_ca_tab               trung vi 1.59 s  [1.64, 1.59, 1.44]  HTTP [1, 1, 1]
B_mot_batch_decisions_A_H        trung vi 0.92 s  [0.87, 0.92, 0.93]  HTTP [1, 1, 1]
doi chung A_mot_batch_ca_tab voi duong cu:
   ban_tin: BANG NHAU (22465 dong quyet_dinh)
   nhat_ky: BANG NHAU (16 dong)
   ke_hoach: BANG NHAU (96 dong)
   hau_kiem: BANG NHAU (27 dong)
doi chung B_mot_batch_decisions_A_H voi duong cu:
   ban_tin: BANG NHAU (22465 dong quyet_dinh)
   nhat_ky: BANG NHAU (16 dong)
   ke_hoach: BANG NHAU (96 dong)
   hau_kiem: BANG NHAU (27 dong)
so dong theo tab (duong cu): {'nhat_ky': 17, 'trades': 134, 'decisions': 22466, 'hau_kiem': 28, 'ke_hoach': 97}
```
