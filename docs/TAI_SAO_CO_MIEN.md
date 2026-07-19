# Vi sao co mien GitHub ma van can 7860?

## Thuc te ky thuat

| | GitHub Pages | Server 7860 |
|--|--------------|-------------|
| Host free | Co | May ban / VPS |
| Hien thi HTML/CSS/JS | Co | Co |
| Chay Python + giu API key bi mat | **KHONG** | **CO** |
| Chat AI that | Can goi server | Chinh no la server |

GitHub Pages **chi host file tinh**.  
API key Groq/xAI **khong** duoc de trong file GitHub (ai cung lay duoc).

Vay:
- `github.io` = giao dien (mien dep, free)
- `7860` = nao AI + key (chay o may/VPS)

---

## 3 cach dung dung

### A) Chi dung local (don gian nhat)
- Khong can mien
- Mo: http://127.0.0.1:7860/
- GitHub Pages chi de gioi thieu (landing)

### B) Mien GitHub + may ban online (tunnel free)
1. May ban chay `python -m webapp.server`
2. Cloudflare Tunnel / ngrok tao link public → tro ve 7860
3. Admin / config dat API URL = link tunnel
4. User mo: https://jarvisai-tung.github.io/
   → chat van goi duoc AI (qua tunnel)

**Luu y:** may ban phai BAT + co mang.

### C) Mien that 1 link (chuyen nghiep)
- Thue VPS (~50-120k/thang) hoac free tier Render/Railway/Fly
- Chay ca web + API tren VPS
- 1 domain: `https://tenmien.com` (UI + API cung mien)
- **Khong can** 7860 tren may nha

---

## Ket luan

| Muc tieu | Lam gi |
|----------|--------|
| Chat o nha | Chi can 7860 |
| Co mien dep, van free, may nha bat | GitHub Pages + Tunnel |
| Mien public 24/7, khong can may nha | VPS / cloud |

File `MO_JARVIS.bat` / `CHAY_SERVER.bat` = cach A.
Xem `HUONG_DAN_TUNNEL.md` neu chon cach B.
