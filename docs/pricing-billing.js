/**
 * Web checkout: autobank (vietqr-pay) + auto activate web plan
 */
(() => {
  const LS_SESSION = "jarvis_google_session_v1";
  const LS_API = "jarvis_api_base_v2";

  function apiBase() {
    const host = (location.hostname || "").toLowerCase();
    if (host === "127.0.0.1" || host === "localhost") {
      return (location.origin || "").replace(/\/$/, "");
    }
    if (host.indexOf("github.io") !== -1) {
      return (localStorage.getItem(LS_API) || "http://127.0.0.1:7860").replace(
        /\/$/,
        ""
      );
    }
    return (location.origin || "").replace(/\/$/, "");
  }

  function session() {
    return (localStorage.getItem(LS_SESSION) || "").trim();
  }

  function headers() {
    const h = { "Content-Type": "application/json" };
    const s = session();
    if (s) h["X-User-Session"] = s;
    return h;
  }

  const modal = document.getElementById("payModal");
  const els = {
    title: document.getElementById("payTitle"),
    sub: document.getElementById("paySub"),
    qr: document.getElementById("payQr"),
    amount: document.getElementById("payAmount"),
    content: document.getElementById("payContent"),
    orderId: document.getElementById("payOrderId"),
    status: document.getElementById("payStatus"),
    hint: document.getElementById("payHint"),
    openPage: document.getElementById("payOpenPage"),
    goChat: document.getElementById("payGoChat"),
    close: document.getElementById("payClose"),
  };

  let pollTimer = null;

  function openModal() {
    if (modal) modal.classList.remove("hidden");
  }
  function closeModal() {
    if (modal) modal.classList.add("hidden");
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  if (els.close) els.close.onclick = closeModal;
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });
  }

  async function createOrder(plan) {
    if (!session()) {
      location.href =
        "login.html?next=" + encodeURIComponent("pricing.html?buy=" + plan);
      return;
    }
    openModal();
    if (els.title) els.title.textContent = "Đang tạo QR…";
    if (els.status) els.status.textContent = "…";
    if (els.qr) els.qr.removeAttribute("src");
    if (els.goChat) els.goChat.classList.add("hidden");

    try {
      const r = await fetch(apiBase() + "/api/billing/create-order", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ plan: plan }),
      });
      const text = await r.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text };
      }
      if (!r.ok) {
        const d = data.detail;
        throw new Error(
          typeof d === "string" ? d : d?.message || text || "Lỗi tạo đơn"
        );
      }

      if (els.title) els.title.textContent = "Mua gói " + (data.plan_name || plan);
      if (els.sub) els.sub.textContent = data.hint || "Quét QR · CK đúng nội dung";
      if (els.amount)
        els.amount.textContent =
          Number(data.amount || 0).toLocaleString("vi-VN") + " ₫";
      if (els.content) els.content.textContent = data.content || "—";
      if (els.orderId) els.orderId.textContent = data.orderId || "—";
      if (els.status) {
        els.status.textContent = "Đang chờ thanh toán…";
        els.status.style.color = "#fbbf24";
      }
      if (els.qr && data.qrImageUrl) {
        els.qr.src = data.qrImageUrl;
        els.qr.alt = "QR " + (data.orderId || "");
      }
      if (els.openPage) {
        if (data.payPage) {
          els.openPage.href = data.payPage;
          els.openPage.classList.remove("hidden");
        } else {
          els.openPage.classList.add("hidden");
        }
      }
      startPoll(data.orderId);
    } catch (e) {
      if (els.status) {
        els.status.textContent = "Lỗi";
        els.status.style.color = "#f87171";
      }
      if (els.hint) els.hint.textContent = String(e.message || e);
    }
  }

  function startPoll(orderId) {
    if (!orderId) return;
    if (pollTimer) clearInterval(pollTimer);
    let n = 0;
    pollTimer = setInterval(async () => {
      n += 1;
      if (n > 200) {
        clearInterval(pollTimer);
        pollTimer = null;
        if (els.hint)
          els.hint.textContent =
            "Hết thời gian chờ. Nếu đã CK, F5 chat hoặc nhắn support kèm mã đơn.";
        return;
      }
      try {
        const r = await fetch(
          apiBase() +
            "/api/billing/order-status?order_id=" +
            encodeURIComponent(orderId),
          { headers: headers(), cache: "no-store" }
        );
        if (!r.ok) return;
        const data = await r.json();
        const st = String(data.status || "").toLowerCase();
        if (st === "paid") {
          clearInterval(pollTimer);
          pollTimer = null;
          if (els.status) {
            els.status.textContent = "✅ Đã thanh toán — gói đã kích hoạt";
            els.status.style.color = "#4ade80";
          }
          if (els.hint)
            els.hint.textContent =
              "Xong! Vào chat, bấm avatar sẽ thấy gói mới (GPT/DeepSeek theo gói).";
          if (els.goChat) els.goChat.classList.remove("hidden");
          if (data.user) {
            try {
              localStorage.setItem(
                "jarvis_google_user_v1",
                JSON.stringify(data.user)
              );
            } catch (e) {}
          }
        }
      } catch (e) {
        /* ignore transient */
      }
    }, 3000);
  }

  document.querySelectorAll(".js-buy").forEach((btn) => {
    btn.addEventListener("click", () => {
      const plan = btn.getAttribute("data-plan") || "basic";
      createOrder(plan);
    });
  });

  // Deep-link: pricing.html?buy=pro
  try {
    const q = new URLSearchParams(location.search).get("buy");
    if (q && /^(basic|pro|business)$/i.test(q)) {
      setTimeout(() => createOrder(q.toLowerCase()), 400);
    }
  } catch (e) {}
})();
