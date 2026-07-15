# Hướng dẫn ra miền tĩnh GitHub Pages (TungDevAI)

Landing đã nằm trong `docs/` — chỉ cần đưa lên GitHub.

## 0. Cài Git (máy bạn chưa có `git` trong PATH)

1. Tải: https://git-scm.com/download/win  
2. Cài xong **mở lại** PowerShell / CMD  
3. Kiểm tra: `git --version`

Hoặc (Admin PowerShell):

```powershell
winget install --id Git.Git -e --source winget
```

## 1. Xem trang local trước

```powershell
cd C:\Users\Admin\Jarvis-AI\docs
python -m http.server 8080
```

- **Web chat (ChatGPT-style):** http://127.0.0.1:8080/  
- **Landing / giá:** http://127.0.0.1:8080/landing.html  

Lần đầu mở chat → ⚙️ dán **Groq API key** (free): https://console.groq.com

## 2. Tạo repo trên GitHub

1. Vào https://github.com/new  
2. Tên gợi ý: `TungDevAI` hoặc `jarvis-landing`  
3. **Public** (Pages free dễ) hoặc Private (cần plan cho private Pages)  
4. **Không** tick README nếu sẽ push từ máy  

## 3. Push code (PowerShell)

```powershell
cd C:\Users\Admin\Jarvis-AI

git init
git branch -M main

# Chỉ add file an toàn — KHÔNG add .env (token bot / API key)
git add docs .github README.md .gitignore jarvis.cmd cli
git add ai telegram product database plugins webapp tools deploy
git add bot.py launcher.py config.py requirements.txt .env.example
git add start-services.ps1 watch-services.ps1 BAT_DAU_BOT.cmd SELL.md DEPLOY_VPS.md
git add Dockerfile docker-compose.yml docker-compose.full.yml

git status
# Kiểm tra: .env KHÔNG được list

git config user.name "YourName"
git config user.email "you@example.com"
git commit -m "Add TungDevAI + GitHub Pages landing"

# Đổi YOUR_USER / YOUR_REPO
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

## 4. Bật GitHub Pages

**Cách A — GitHub Actions (khuyến nghị)**  
1. Repo → **Settings → Pages**  
2. Source: **GitHub Actions**  
3. Đợi workflow **Deploy GitHub Pages** xanh  
4. URL: `https://YOUR_USER.github.io/YOUR_REPO/`

**Cách B — Branch /docs**  
1. Settings → Pages  
2. Branch: `main` → folder **`/docs`** → Save  
3. URL tương tự  

## 5. Domain riêng (tuỳ chọn)

Ví dụ `jarvis.tenban.com`:

1. Pages → **Custom domain** → nhập domain  
2. DNS:
   - `CNAME` → `YOUR_USER.github.io`  
   - hoặc A record theo docs GitHub  
3. Bật **Enforce HTTPS**

File `docs/CNAME` (nếu cần):

```
jarvis.tenban.com
```

## 6. Bảo mật

- **Không** commit `.env` (có `TELEGRAM_BOT_TOKEN`, API key)  
- Repo public: chỉ landing + source sạch; secret giữ máy / VPS  
- Nếu lỡ push token → **revoke** token BotFather + API key ngay  

## Sửa link / giá

Mở `docs/index.html` — tìm `@grokapiai_bot`, giá 49k/99k/199k, support `@usertungpham`.
