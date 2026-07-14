# Jarvis Web Chat (GitHub Pages)

Giao diện **kiểu ChatGPT**, host **miễn phí** trên GitHub Pages (static).

| File | Vai trò |
|------|---------|
| `index.html` | **Web chat** (trang chính) |
| `chat.css` / `chat.js` | UI + gọi API |
| `landing.html` | Landing marketing / giá |
| `styles.css` | CSS landing |

## Xem local

```powershell
cd C:\Users\Admin\Jarvis-AI\docs
python -m http.server 8080
```

- Chat: http://127.0.0.1:8080/  
- Landing: http://127.0.0.1:8080/landing.html  

## Dùng chat (quan trọng)

GitHub Pages **không chạy Python/backend**. Chat gọi API AI **từ trình duyệt**:

1. Mở web → ⚙️ **Cài đặt API**
2. Preset **Groq (free)**  
3. Dán key từ https://console.groq.com  
4. Model: `llama-3.3-70b-versatile`  
5. **Lưu** → chat  

Key chỉ nằm trong `localStorage` máy bạn — **không** đưa lên GitHub.

### Nếu lỗi CORS

Một số API chặn gọi từ `*.github.io`:

- Thử **OpenRouter** (preset)  
- Hoặc tắt **Stream**  
- Hoặc trỏ Base URL sang backend Jarvis của bạn (VPS / tunnel) nếu có CORS

## Deploy free

1. Push repo lên GitHub  
2. **Settings → Pages** → GitHub Actions (hoặc branch `/docs`)  
3. URL: `https://USER.github.io/REPO/`

Chi tiết: [HUONG_DAN_GITHUB_PAGES.md](HUONG_DAN_GITHUB_PAGES.md)
