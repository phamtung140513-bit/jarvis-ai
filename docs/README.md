# Jarvis AI — Landing (GitHub Pages)

Trang tĩnh marketing cho bot Telegram.

## Xem local

Mở `index.html` bằng trình duyệt, hoặc:

```powershell
cd C:\Users\Admin\Jarvis-AI\docs
python -m http.server 8080
```

→ http://127.0.0.1:8080

## Deploy GitHub Pages

1. Tạo repo trên GitHub (public hoặc private + Pages enabled).
2. Push source (có thư mục `docs/` + workflow).
3. Repo **Settings → Pages**:
   - Source: **GitHub Actions**  
   - hoặc **Deploy from branch** → branch `main` → folder `/docs`
4. URL:
   - `https://<user>.github.io/<repo>/`
   - Custom domain: Settings → Pages → Custom domain (CNAME)

Workflow: `.github/workflows/pages.yml` tự deploy khi push `docs/`.

## Sửa nội dung

| File | Việc |
|------|------|
| `index.html` | Text, giá, link bot |
| `styles.css` | Giao diện |
| `assets/` | Ảnh avatar |

Link bot mặc định: `https://t.me/grokapiai_bot`  
Support: `@usertungpham`
