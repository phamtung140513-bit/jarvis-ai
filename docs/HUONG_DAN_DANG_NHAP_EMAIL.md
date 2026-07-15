# Dang nhap / Dang ky (email + Google)

Giong ChatGPT / Claude / Gemini:

1. **Dang ky** bang email → bam **Gui ma** → nhan ma 6 so → tao tai khoan
2. **Dang nhap** bang email + mat khau
3. **Tiep tuc voi Google** (neu da set `GOOGLE_CLIENT_ID`)

## Chay local

```bat
cd C:\Users\Admin\Jarvis-AI
.venv\Scripts\python.exe -m webapp.server
```

Mo: http://127.0.0.1:7860/

## .env

```env
WEB_AUTH_REQUIRED=true
AUTH_DEV_SHOW_CODE=true

# --- SMTP (gui ma that ve email) ---
# Gmail: bat 2FA, tao App Password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=ban@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM=TungDevAI <ban@gmail.com>

# --- Google (tuy chon) ---
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
```

### Dev (chua co SMTP)

De `SMTP_HOST` trong. Server se **hien ma xac thuc tren form** (`dev_code`) de ban test dang ky.

Production: cau hinh SMTP va dat `AUTH_DEV_SHOW_CODE=false`.

## API

| Method | Path | Mo ta |
|--------|------|--------|
| POST | `/api/auth/send-code` | Gui ma OTP `{email, purpose:"register"}` |
| POST | `/api/auth/register` | `{email, password, code, name}` |
| POST | `/api/auth/login` | `{email, password}` |
| POST | `/api/auth/google` | `{credential}` GIS JWT |
| GET | `/api/auth/me` | Header `X-User-Session` |
| POST | `/api/auth/logout` | Dang xuat |

## UI

- Man hinh dang nhap: tab **Dang nhap** / **Dang ky**
- Sidebar (khi chua login): dong **Dang nhap** — bam de mo form
- Khong con hien `server offline` o cho ten user; trang thai online la cham xanh/do tren header
