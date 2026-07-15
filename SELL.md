# Hướng dẫn bán TungDevAI

Bạn có **2 cách kiếm tiền** với repo này.

---

## Cách 1 — Bán *truy cập bot* (SaaS) ⭐ dễ nhất

Bạn host bot, khách trả tiền → nhận **mã** → `/activate`.

### Setup chủ shop

1. `.env`:
   ```env
   OWNER_TELEGRAM_IDS=8258128591
   APP_NAME=ShopAI Bot
   SUPPORT_CONTACT=@your_zalo_or_telegram
   PAYMENT_INFO=CK xong gui bill cho admin
   CURRENCY=VND
   PUBLIC_BUY_ENABLED=true

   # QR ngân hàng (VietQR tự sinh)
   BANK_ID=mb
   BANK_ACCOUNT=0123456789
   BANK_ACCOUNT_NAME=NGUYEN VAN A
   BANK_TRANSFER_CONTENT=AI TUNGDEV
   # hoặc ảnh QR sẵn: PAYMENT_QR_PATH=./assets/qr-bank.png
   ```

   Khách gõ `/buy` hoặc `/qr basic` → bot gửi **ảnh QR** (có số tiền theo gói).
2. Chạy `python launcher.py`
3. Trên Telegram (tài khoản owner):
   - `/gencode basic` → lấy mã
   - Gửi mã cho khách sau khi nhận tiền
4. **Tự động (vietqr-pay):** CK xong → webhook → bot auto-active + nhắn mã  
   **Thủ công:** admin `/gencode basic` → khách `/activate JV-XXXXX-XXXXX`

### Bảng giá mặc định (sửa trong `product/plans.py`)

| Gói | Giá gợi ý | Quota |
|-----|-----------|--------|
| Trial | 0đ / 3 ngày | 20 tin/ngày |
| Basic | 49.000đ / 30 ngày | 100 tin/ngày |
| Pro | 99.000đ / 30 ngày | 500 tin/ngày |
| Business | 199.000đ / 30 ngày | Không giới hạn |

### Lệnh admin

| Lệnh | Việc |
|------|------|
| `/admin` | Menu admin |
| `/stats` | Users + tin hôm nay |
| `/users` | Danh sách khách |
| `/gencode basic` | Tạo mã bán |
| `/adduser ID pro 30` | Tặng / gán gói |
| `/deluser ID` | Khóa khách |

### Kênh bán

- Facebook group dev / freelancer
- Telegram channel + bot link
- Shopee / website: giao *mã kích hoạt* sau thanh toán
- White-label: đổi `APP_NAME`, tagline, payment

---

## Cách 2 — Bán *source / cài đặt* (white-label)

Bán code cho người khác tự chạy bot riêng.

1. Đặt bí mật license:
   ```env
   LICENSE_SECRET=chuoi-bi-mat-cua-ban
   REQUIRE_SOFTWARE_LICENSE=true
   ```
2. Tạo key cho khách:
   ```bash
   python tools/gen_license.py --customer "ten_khach" --days 365
   ```
3. Gửi cho khách:
   - source (zip) **không** kèm `.env` của bạn
   - `SOFTWARE_LICENSE_KEY=JV-...`
   - `LICENSE_SECRET` (hoặc bản build nhúng secret)
4. Giá gợi ý: 1.5–5 triệu / bản cài + setup

CLI mã SaaS (không cần Telegram):

```bash
python tools/gen_access_code.py --plan pro --days 30
```

---

## Checklist trước khi bán

- [ ] Đổi `APP_NAME`, `SUPPORT_CONTACT`, `PAYMENT_INFO`
- [ ] Owner ID đúng
- [ ] AI key (Groq/OpenRouter) đủ quota hoặc trả phí
- [ ] Không public `.env` / token
- [ ] Test `/buy` → `/gencode` → `/activate` trên acc phụ
- [ ] Ghi rõ: AI third-party, không cam kết uptime 100%

---

## Lưu ý pháp lý (ngắn)

- Không bán lại API key của bên thứ ba như “Grok unlimited” nếu ToS cấm.
- Ghi rõ bot dùng model free/trả phí nào.
- Hóa đơn / chính sách hoàn tiền do bạn tự quy định.

---

## Upsell

1. Setup trọn gói (cài VPS + bot) +500k–1tr  
2. Custom brand + keyboard  
3. Thêm plugin GitHub / Docker  
4. Gói agency nhiều bot  

Chúc bán chạy!
