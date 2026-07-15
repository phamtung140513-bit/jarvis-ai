# Deploy TungDevAI lên VPS (bot chạy 24/7, không cần bật máy)

## 1. Chọn VPS

| Nhu cầu | Gợi ý |
|--------|--------|
| **Chỉ bot chat + /buy QR tĩnh** | 1 vCPU · **1GB RAM** · Ubuntu 22.04 · ~50–120k/tháng |
| **Bot + vietqr-pay + webhook** | 1 vCPU · **1–2GB RAM** · Ubuntu 22.04 |

Hãng hay dùng: **Contabo**, **Vultr**, **DigitalOcean**, **Lightsail**, VPS VN (Vietnix, Bizfly…).

Khi mua xong bạn có:

- IP public (vd `203.0.113.10`)
- User `root` (hoặc `ubuntu`) + mật khẩu / file SSH key

---

## 2. Kết nối SSH (từ Windows)

PowerShell:

```powershell
ssh root@IP_VPS_CUA_BAN
```

Lần đầu gõ `yes` rồi nhập mật khẩu.

---

## 3. Cài Docker trên VPS (cách dễ, khuyến nghị)

```bash
apt update && apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker --version
docker compose version
```

---

## 4. Đưa code lên VPS

### Cách A — Git (nếu có repo)

```bash
mkdir -p /opt && cd /opt
git clone URL_REPO_CUA_BAN jarvis
cd jarvis
```

### Cách B — Copy từ máy Windows (không cần Git)

Trên **máy Windows** (PowerShell), trong thư mục project:

```powershell
# Chỉ bot (không copy .venv)
scp -r C:\Users\Admin\Jarvis-AI root@IP_VPS:/opt/Jarvis-AI

# (Tuỳ chọn) kèm pay
scp -r C:\Users\Admin\vietqr-pay root@IP_VPS:/opt/vietqr-pay
```

> **Không** copy `.venv` và `node_modules` nếu file quá nặng — cài lại trên VPS.  
> **Có** copy file `.env` (hoặc tạo mới trên VPS).

Nếu `scp` báo không có lệnh: cài [OpenSSH Client](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse) hoặc dùng WinSCP (giao diện kéo-thả).

---

## 5. Cấu hình `.env` trên VPS

```bash
cd /opt/Jarvis-AI
nano .env
```

Các dòng **bắt buộc**:

```env
TELEGRAM_BOT_TOKEN=...          # từ @BotFather
OWNER_TELEGRAM_IDS=8258128591   # ID Telegram của bạn
ALLOWED_TELEGRAM_IDS=8258128591
AI_PROVIDER=groq
AI_API_KEY=...                  # key Groq free

PUBLIC_BUY_ENABLED=true
BANK_ID=hdbank
BANK_ACCOUNT=...
BANK_ACCOUNT_NAME=...
```

### Chỉ bot (đơn giản — đủ chạy 24/7)

Tắt / để trống pay nếu chưa cần auto:

```env
# VIETQR_PAY_URL=
PAYMENT_WEBHOOK_ENABLED=false
```

Khách `/buy` → QR theo `BANK_*` hoặc ảnh; bạn duyệt bill + `/gencode` thủ công.

### Bot + vietqr-pay (auto sau CK)

Trong **TungDevAI** `.env`:

```env
VIETQR_PAY_URL=http://127.0.0.1:3000
PAYMENT_WEBHOOK_ENABLED=true
PAYMENT_WEBHOOK_HOST=0.0.0.0
PAYMENT_WEBHOOK_PORT=8787
PAYMENT_WEBHOOK_SECRET=doi_secret_manh_o_day
```

Trong **vietqr-pay** `.env`:

```env
PORT=3000
PUBLIC_BASE_URL=https://pay.domain-cua-ban.com   # sau khi có domain + HTTPS
JARVIS_FULFILL_URL=http://127.0.0.1:8787/internal/orders/paid
JARVIS_FULFILL_SECRET=doi_secret_manh_o_day      # trùng bot
TELEGRAM_BOT_TOKEN=...
TELEGRAM_NOTIFY_CHAT_ID=8258128591
BANK_CODE=hdbank
BANK_ACCOUNT=...
BANK_ACCOUNT_NAME=...
```

Webhook VietQR partner cần **HTTPS public** (domain + Cloudflare Tunnel / Nginx).  
Chỉ polling Telegram thì **không cần** mở port vào bot.

---

## 6. Chạy bằng Docker Compose (bot)

Trong `/opt/Jarvis-AI` đã có `docker-compose.yml`:

```bash
cd /opt/Jarvis-AI
docker compose up -d --build
docker compose logs -f
```

Thấy log kiểu: `Bot @grokapiai_bot ready — polling` là OK.

Lệnh hữu ích:

```bash
docker compose ps
docker compose restart
docker compose logs --tail 50
docker compose down          # dừng
```

---

## 7. (Tuỳ chọn) Chạy vietqr-pay bằng Docker

Tạo file `/opt/vietqr-pay/Dockerfile` nếu chưa có (xem `deploy/vietqr.Dockerfile` trong repo bot), rồi:

```bash
cd /opt/vietqr-pay
docker build -t vietqr-pay .
docker run -d --name vietqr-pay --restart unless-stopped \
  --network host \
  --env-file .env \
  vietqr-pay
```

Hoặc dùng `docker-compose.full.yml` trong thư mục TungDevAI (bot + pay cùng mạng).

---

## 8. Cách không Docker (Python trực tiếp + systemd)

```bash
apt install -y python3 python3-venv python3-pip
cd /opt/Jarvis-AI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Service:

```bash
cp deploy/jarvis.service /etc/systemd/system/jarvis.service
# Sửa User/path nếu cần
systemctl daemon-reload
systemctl enable --now jarvis
systemctl status jarvis
journalctl -u jarvis -f
```

---

## 9. Kiểm tra bot sống

1. Telegram → bot → `/start`
2. Trên VPS: `docker compose logs --tail 20` (thấy `Update id=... handled`)
3. Tắt máy Windows → bot **vẫn** reply

---

## 10. Bảo mật tối thiểu

```bash
# Firewall: chỉ SSH (và 80/443 nếu có web)
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
```

- Đổi mật khẩu root / dùng SSH key  
- **Không** public file `.env`  
- Đổi `PAYMENT_WEBHOOK_SECRET` khác chuỗi mặc định  

---

## Tóm tắt chi phí

| Mục | Phí |
|-----|-----|
| VPS 1GB | ~50–120k/tháng |
| Domain (tuỳ chọn, cho webhook) | ~0–200k/năm |
| Groq free tier | 0đ (có giới hạn) |
| Telegram bot | 0đ |

**Bước tiếp theo của bạn:** mua VPS Ubuntu → gửi mình **IP** (không gửi mật khẩu trên chat công khai) → làm tiếp SSH + copy code + `docker compose up`.
