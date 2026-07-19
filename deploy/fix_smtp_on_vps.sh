set -e
cd /opt/Jarvis-AI
# Ensure SMTP flags (password must already be set by user)
grep -q '^SMTP_HOST=' .env && sed -i 's/^SMTP_HOST=.*/SMTP_HOST=smtp.gmail.com/' .env || echo 'SMTP_HOST=smtp.gmail.com' >> .env
grep -q '^SMTP_USER=' .env && sed -i 's/^SMTP_USER=.*/SMTP_USER=tung140513@gmail.com/' .env || echo 'SMTP_USER=tung140513@gmail.com' >> .env
grep -q '^SMTP_FROM=' .env && sed -i 's/^SMTP_FROM=.*/SMTP_FROM=TungDevAI <tung140513@gmail.com>/' .env || echo 'SMTP_FROM=TungDevAI <tung140513@gmail.com>' >> .env
grep -q '^SMTP_PORT=' .env && sed -i 's/^SMTP_PORT=.*/SMTP_PORT=587/' .env || echo 'SMTP_PORT=587' >> .env
grep -q '^SMTP_TLS=' .env && sed -i 's/^SMTP_TLS=.*/SMTP_TLS=true/' .env || echo 'SMTP_TLS=true' >> .env
grep -q '^AUTH_DEV_SHOW_CODE=' .env && sed -i 's/^AUTH_DEV_SHOW_CODE=.*/AUTH_DEV_SHOW_CODE=false/' .env || echo 'AUTH_DEV_SHOW_CODE=false' >> .env
echo "=== SMTP config (password hidden) ==="
grep -E '^SMTP_|^AUTH_DEV' .env | sed 's/PASSWORD=.*/PASSWORD=***/'
echo "=== If SMTP_PASSWORD empty, edit: nano .env ==="
systemctl restart tungdevai-web
sleep 2
systemctl is-active tungdevai-web
curl -s -o /dev/null -w "web:%{http_code}\n" http://127.0.0.1:7860/auth.js
