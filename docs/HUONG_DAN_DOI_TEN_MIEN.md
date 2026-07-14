# Đổi “tên miền” web Jarvis

Hiện tại web free là:

```text
https://phamtung140513-bit.github.io/jarvis-ai/
```

## Quan trọng

Trên GitHub, tên **`jarvis-ai` đã bị người khác chiếm**  
(user: https://github.com/JARVIS-AI) → **không** tạo được `https://jarvis-ai.github.io/` free.

---

## Cách 1 — Free: `jarvisai.github.io` (gần “jarvis-ai”)

Tên **`jarvisai`** đang trống (kiểm tra lúc setup).

### Bước A — Tạo Organization

1. Mở: https://github.com/organizations/plan  
2. Chọn plan **Free**  
3. Organization name: **`jarvisai`**  
4. Create  

### Bước B — Repo site gốc

1. Trong org `jarvisai`, tạo repo tên **đúng**:  
   **`jarvisai.github.io`**  
   (public, không README)

2. Trên máy (PowerShell):

```powershell
cd C:\Users\Admin\Jarvis-AI
$env:Path = "C:\Program Files\Git\bin;C:\Program Files\GitHub CLI;" + $env:Path

# remote mới (org site)
git remote remove origin-org 2>$null
git remote add origin-org https://github.com/jarvisai/jarvisai.github.io.git

# đẩy docs lên root site: dùng branch main + Pages /docs
# HOẶC copy nội dung docs lên root — cách đơn giản: Pages folder /docs
git push -u origin-org main
```

3. Org repo → **Settings → Pages**  
   - Source: **Deploy from a branch**  
   - Branch: `main`  
   - Folder: **`/docs`**  
   - Save  

4. URL free:

```text
https://jarvisai.github.io/
https://jarvisai.github.io/landing.html
```

> Muốn tên khác free: `jarvis-ai-vn` → `https://jarvis-ai-vn.github.io/` (cùng quy trình).

---

## Cách 2 — Domain riêng `jarvis-ai.com` / `.vn` (trả phí)

1. Mua domain (Namecheap, Cloudflare, Nhà đăng ký VN…)  
   Ví dụ: `jarvis-ai.com` hoặc `jarvisai.vn`

2. Trong repo đang có Pages (`phamtung140513-bit/jarvis-ai`):  
   **Settings → Pages → Custom domain** → nhập `jarvis-ai.com`

3. DNS (Cloudflare/DNS provider):

| Type  | Name | Value |
|-------|------|--------|
| CNAME | `@` hoặc `www` | `phamtung140513-bit.github.io` |

Với apex `@` nhiều nhà cung cấp cần **A record** theo docs GitHub:

```text
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

4. File `docs/CNAME` (sau khi set custom domain GitHub có thể tự tạo):

```text
jarvis-ai.com
```

5. Bật **Enforce HTTPS** khi DNS xanh.

URL:

```text
https://jarvis-ai.com/
```

---

## Cách 3 — Giữ link hiện tại (không đổi)

```text
https://phamtung140513-bit.github.io/jarvis-ai/
```

Vẫn free, ổn định. Có thể rút gọn bằng bit.ly / t.me link.

---

## Gợi ý

| Muốn | Làm |
|------|-----|
| Free, ngắn | Org **`jarvisai`** → `https://jarvisai.github.io/` |
| Đúng chữ jarvis-ai | Mua domain **`jarvis-ai.com`** |
| Nhanh nhất | Dùng link hiện tại |

Nhắn mình chọn **1 / 2 / 3** để cấu hình tiếp (CNAME, push org…).
