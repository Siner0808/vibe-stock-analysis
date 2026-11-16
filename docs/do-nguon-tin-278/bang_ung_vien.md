| feed | nơi khai | lớp | ứng viên / bỏ | bằng chứng |
|---|---|---|---|---|
| `https://vnexpress.net/rss/chung-khoan.rss` | Domestic | moved_to_html (200) | bỏ | trang mục vnexpress.net/rss (chi_muc_1.log) không còn mục chứng khoán; kinh-doanh.rss đã được khai và ok |
| `https://baodautu.vn/sitemap/rss` | Domestic | parse_error (200) | bỏ | trang mục baodautu.vn/rss.html trả 200 nhưng KHÔNG có liên kết .rss/.xml nào theo bộ lọc của công cụ (chưa tìm được) |
| `https://cafef.vn/ngan-hang.rss` | Domestic, Sector:banking | dead_url (404) | `https://cafef.vn/tai-chinh-ngan-hang.rss` | thu_ung_vien.md: ok, 50 bài; có trên chi_muc_1.log (cafef.vn/rss.chn) |
| `https://vietstock.vn/rss/830/chung-khoan.rss` | Domestic, Sector:securities_finance | html_not_feed (200) | `https://vietstock.vn/144/chung-khoan.rss` | thu_ung_vien.md: ok, 30 bài; có trên chi_muc_1.log (vietstock.vn/rss). Phương án phụ: /830/chung-khoan/co-phieu.rss, ok 20 bài |
| `https://ndh.vn/thi-truong/chung-khoan.rss` | Domestic | dead_url (404) | bỏ | trang mục ndh.vn/rss trả 404 |
| `https://feeds.reuters.com/reuters/businessNews` | International, Sector:securities_finance | dead_host (ConnectionError) | bỏ | tên máy chủ không còn tra được (NameResolutionError) |
| `https://feeds.reuters.com/reuters/companyNews` | International, Sector:oil_gas | dead_host (ConnectionError) | bỏ | như trên |
| `https://finance.yahoo.com/news/rss/` | International | dead_url (404) | bỏ | 404; trang mục finance.yahoo.com/rss/ trả 404 |
| `https://www.investing.com/rss/news.rss` | International | timeout (ReadTimeout) | bỏ | bắt tay TLS quá hạn từ máy này (chi_muc_1.log); chưa biết có phải chặn theo IP |
| `https://www.investing.com/rss/market_overview.rss` | International | timeout (ReadTimeout) | bỏ | như trên |
| `https://www.sbv.gov.vn/webcenter/rss?_afrLoop=0&lang=vi&catId=559` | Macro | dead_url (404) | bỏ | chuyển 302 sang /vi/webcenter/rss... rồi 404; trang mục sbv.gov.vn/vi/webcenter/rss trả 404 |
| `https://mof.gov.vn/webcenter/rss?catId=439&lang=vi` | Macro | moved_to_html (200) | bỏ | chuyển về trang chủ; mof.gov.vn/rss cũng trả trang HTML 2.003 byte |
| `https://feeds.reuters.com/reuters/economicNews` | Macro, Sector:global_macro | dead_host (ConnectionError) | bỏ | như trên |
| `https://www.imf.org/en/News/rss?type=pressRelease` | Macro | dead_url (404) | bỏ | 404 (JSON 48 byte); trang mục imf.org/en/News/RSS cũng 404 |
| `https://www.worldbank.org/en/news/rss` | Macro | dead_url (404) | bỏ | 404; trang mục worldbank.org/en/about/rss 404 |
| `https://vietstock.vn/rss/830/ngan-hang.rss` | Sector:banking | html_not_feed (200) | `https://vietstock.vn/757/tai-chinh/ngan-hang.rss` | thu_ung_vien.md: ok, 20 bài; có trên chi_muc_1.log |
| `https://feeds.reuters.com/reuters/financialServicesAndRealEstateNews` | Sector:banking | dead_host (ConnectionError) | bỏ | như trên |
| `https://batdongsan.com.vn/tin-tuc-nha-dat.rss` | Sector:real_estate | dead_url (404) | bỏ | chuyển 301 sang wiki.batdongsan.com.vn rồi 404; trang mục batdongsan.com.vn/rss trả 403 |
| `https://cafef.vn/cong-nghe.rss` | Sector:technology | dead_url (404) | `https://cafef.vn/kinh-te-so.rss` | thu_ung_vien.md: ok, 50 bài; chủ đề gần nhất trên trang mục (không có mục công nghệ): cần người duyệt |
| `https://www.steelorbis.com/rss/news` | Sector:steel_materials | dead_url (404) | bỏ | 404; trang mục steelorbis.com/rss/ trả 404 |
| `https://cafef.vn/dau-khi.rss` | Sector:oil_gas | dead_url (404) | bỏ | 404; trang mục cafef.vn/rss.chn (25 liên kết) không có mục này |
| `https://cafef.vn/nong-nghiep.rss` | Sector:agriculture | dead_url (404) | bỏ | 404; trang mục cafef.vn/rss.chn (25 liên kết) không có mục này |
| `https://www.agweb.com/rss.xml` | Sector:agriculture | blocked (403) | bỏ | 403 cả hai User-Agent (tool, cột lop_ua_trinh_duyet); chưa tìm trang mục |
| `https://cafef.vn/hang-tieu-dung.rss` | Sector:consumer_retail | dead_url (404) | bỏ | 404; trang mục cafef.vn/rss.chn (25 liên kết) không có mục này |
| `https://cafef.vn/duoc-pham.rss` | Sector:healthcare_pharma | dead_url (404) | bỏ | 404; trang mục cafef.vn/rss.chn (25 liên kết) không có mục này |
| `https://www.fiercepharma.com/rss/xml` | Sector:healthcare_pharma | blocked (403) | bỏ | 403 cả hai User-Agent; chưa tìm trang mục |
| `https://cafef.vn/giao-thong.rss` | Sector:aviation_logistics | dead_url (404) | bỏ | 404; trang mục cafef.vn/rss.chn (25 liên kết) không có mục này |
| `https://simpleflying.com/feed/` | Sector:aviation_logistics | dead_host (ConnectionError) | bỏ | máy chủ đóng kết nối không trả lời (RemoteDisconnected) cả khi vào trang mục |
| `https://cafef.vn/dien-luc.rss` | Sector:electricity_energy | dead_url (404) | bỏ | 404; trang mục cafef.vn/rss.chn (25 liên kết) không có mục này |
| `https://cafef.vn/chung-khoan.rss` | Sector:securities_finance | dead_url (404) | `https://cafef.vn/thi-truong-chung-khoan.rss` | thu_ung_vien.md: ok, 50 bài; TRÙNG với nguồn Domestic đã khai (đổi thì khai lặp) |
| `https://cafef.vn/det-may.rss` | Sector:textiles_apparel | dead_url (404) | bỏ | 404; trang mục cafef.vn/rss.chn (25 liên kết) không có mục này |
| `https://www.just-style.com/rss.ashx` | Sector:textiles_apparel | dead_url (404) | `https://www.just-style.com/feed/` | thu_ung_vien.md: ok, 10 bài; trang mục just-style.com/rss/ chuyển hướng sang /feed/ |

Địa chỉ duy nhất không ok: 32; số lần khai: 37.
Có ứng viên đã tải ok >= 1 bài: 6; bỏ/chưa tìm được: 26.
