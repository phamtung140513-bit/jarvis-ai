# Vì sao login không nên dùng ngrok free?

## Vấn đề ngrok free

| Vấn đề | Hậu quả |
|--------|---------|
| Màn **Visit Site** | User bấm Google → fail / redirect hỏng |
| Trả **HTML** thay JSON API | Chat hiện `<!DOCTYPE html>…assets.ngrok.com` |
| Cần header đặc biệt | Dễ quên → lỗi lạ |
| Free domain | Vẫn ổn hơn random URL, nhưng interstitial vẫn có |

## So sánh nhanh

| Cách | Google login | URL cố định | 24/7 PC tắt |
|------|--------------|-------------|-------------|
| **Ngrok free** | Dễ lỗi | Có (reserved) nhưng Visit Site | Không |
| **Cloudflare quick tunnel** | Tốt hơn nhiều | Đổi mỗi lần restart | Không |
| **Cloudflare named + domain** | Rất tốt | Có | Cần máy/VPS bật |
| **VPS + domain** | Tốt nhất | Có | **Có** |

## Cách đang khuyến nghị (máy nhà)

```bat
Desktop\BAT_TUNGDEVAI_ONLINE.bat
```

→ Bật web `7860` + **Cloudflare Tunnel** (`*.trycloudflare.com`)  
→ Cập nhật `docs/config.json` → `apiBase`  
→ GitHub Pages redirect login sang Cloudflare

### Google Cloud (mỗi lần URL tunnel đổi)

Thêm:

- Origin: `https://XXXX.trycloudflare.com`
- Redirect: `https://XXXX.trycloudflare.com/google-callback.html`

## Cách ngon nhất (production)

1. VPS (đã có hướng dẫn `KHONG_CAN_BAT_MAY_NHA.md`)
2. Domain riêng (`tungdevai.com` / …)
3. Cloudflare Tunnel **named** hoặc nginx reverse proxy
4. Google Console khai báo **1 lần**, không đổi

## Local (dev)

```text
http://127.0.0.1:7860/login.html
```

Không cần tunnel, Google login OK nếu đã thêm `http://127.0.0.1:7860` trong Console.
