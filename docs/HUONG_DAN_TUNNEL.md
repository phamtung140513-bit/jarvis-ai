# GitHub Pages + Tunnel (mien public, free)

Muc tieu:
- User mo: https://phamtung140513-bit.github.io/jarvis-ai/
- AI van chay bang key tren may ban (port 7860)
- Dung Cloudflare Tunnel (free, khong can mo port router)

## Buoc 1 — Cai cloudflared

1. Tai: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
2. Hoac winget:
   ```
   winget install --id Cloudflare.cloudflared
   ```

## Buoc 2 — Bat server TungDevAI

```bat
C:\Users\Admin\Jarvis-AI\CHAY_SERVER.bat
```

Doi den khi thay: `Uvicorn running on http://0.0.0.0:7860`

## Buoc 3 — Mo tunnel

```bat
C:\Users\Admin\Jarvis-AI\MO_TUNNEL.bat
```

Se hien link dang:
```
https://xxxx-xx-xx.trycloudflare.com
```

**Copy link do.**

## Buoc 4 — Gan API vao web GitHub

1. Mo: https://phamtung140513-bit.github.io/jarvis-ai/j-panel.html
2. O "API server" dan: `https://xxxx.trycloudflare.com` (khong co / cuoi)
3. Dang nhap admin key
4. Luu (neu co o Backend URL)

Hoac sua `docs/config.json` tren repo:

```json
{
  "apiBase": "https://xxxx.trycloudflare.com",
  "telegramBot": "https://t.me/grokapiai_bot",
  "appName": "TungDevAI"
}
```

Roi push GitHub.

## Buoc 5 — User dung

Mo: https://phamtung140513-bit.github.io/jarvis-ai/

Chat se goi tunnel → may ban → Groq.

## Luu y

- May ban TAT = web chat chet
- Link trycloudflare.com **doi moi lan** chay tunnel (tru khi dung named tunnel + domain Cloudflare)
- De 24/7 that: thue VPS, khong can tunnel
