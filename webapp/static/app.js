(() => {
  const els = {
    messages: document.getElementById("messages"),
    empty: document.getElementById("emptyState"),
    form: document.getElementById("form"),
    input: document.getElementById("input"),
    send: document.getElementById("btnSend"),
    newChat: document.getElementById("btnNew"),
    appName: document.getElementById("appName"),
    modelLabel: document.getElementById("modelLabel"),
    statusPill: document.getElementById("statusPill"),
    tokenBox: document.getElementById("tokenBox"),
    accessToken: document.getElementById("accessToken"),
    tgLink: document.getElementById("tgLink"),
  };

  let sessionId = localStorage.getItem("jarvis_session_id") || "";
  let busy = false;

  const savedToken = localStorage.getItem("jarvis_web_token") || "";
  if (savedToken) els.accessToken.value = savedToken;

  els.accessToken?.addEventListener("change", () => {
    localStorage.setItem("jarvis_web_token", els.accessToken.value.trim());
  });

  function headers() {
    const h = { "Content-Type": "application/json" };
    const t = (els.accessToken?.value || "").trim();
    if (t) h["X-Web-Token"] = t;
    return h;
  }

  function hideEmpty() {
    if (els.empty) els.empty.style.display = "none";
  }

  function showEmpty() {
    els.messages.innerHTML = "";
    // re-create empty state simply
    const div = document.createElement("div");
    div.className = "empty";
    div.id = "emptyState";
    div.innerHTML = `
      <div class="empty-icon">✦</div>
      <h2>Hỏi gì cũng được</h2>
      <p>Giống Grok — chat nhanh. Web + Telegram dùng chung AI.</p>
      <div class="suggestions">
        <button type="button" data-q="Giải thích Python async/await ngắn gọn">Python async</button>
        <button type="button" data-q="Viết API FastAPI hello world">FastAPI hello</button>
        <button type="button" data-q="So sánh bot Telegram và web chat AI">Telegram vs Web</button>
      </div>`;
    els.messages.appendChild(div);
    div.querySelectorAll("[data-q]").forEach((b) =>
      b.addEventListener("click", () => {
        els.input.value = b.getAttribute("data-q");
        els.form.requestSubmit();
      })
    );
  }

  function addMessage(role, text) {
    hideEmpty();
    const row = document.createElement("div");
    row.className = `msg ${role}`;
    const av = document.createElement("div");
    av.className = "avatar";
    av.textContent = role === "user" ? "U" : "T";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    const roleEl = document.createElement("div");
    roleEl.className = "role";
    roleEl.textContent = role === "user" ? "Bạn" : "TungDevAI";
    const body = document.createElement("div");
    body.className = "content";
    body.innerHTML = formatMarkdown(text);
    bubble.appendChild(roleEl);
    bubble.appendChild(body);
    row.appendChild(av);
    row.appendChild(bubble);
    els.messages.appendChild(row);
    els.messages.scrollTop = els.messages.scrollHeight;
    return body;
  }

  function formatMarkdown(text) {
    if (!text) return "";
    // escape HTML
    let s = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    // fenced code
    s = s.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
      return `<pre><code class="lang-${lang || "txt"}">${code.replace(/\n$/, "")}</code></pre>`;
    });
    // inline code
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    // bold
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return s;
  }

  function setBusy(v) {
    busy = v;
    els.send.disabled = v;
    els.input.disabled = v;
  }

  async function sendMessage(text) {
    if (!text.trim() || busy) return;
    setBusy(true);
    addMessage("user", text.trim());
    const bodyEl = addMessage("assistant", "");
    bodyEl.parentElement.classList.add("typing");
    bodyEl.textContent = "";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          message: text.trim(),
          session_id: sessionId,
          stream: true,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      let full = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          let data;
          try {
            data = JSON.parse(line.slice(6));
          } catch {
            continue;
          }
          if (data.type === "meta" && data.session_id) {
            sessionId = data.session_id;
            localStorage.setItem("jarvis_session_id", sessionId);
          } else if (data.type === "delta") {
            full += data.text || "";
            bodyEl.innerHTML = formatMarkdown(full);
            els.messages.scrollTop = els.messages.scrollHeight;
          } else if (data.type === "error") {
            throw new Error(data.message || "Lỗi AI");
          }
        }
      }
      bodyEl.parentElement.classList.remove("typing");
      if (!full) bodyEl.textContent = "(không có phản hồi)";
    } catch (e) {
      bodyEl.parentElement.classList.remove("typing");
      bodyEl.innerHTML = `<span style="color:var(--danger)">Lỗi: ${escapeHtml(
        e.message
      )}</span>`;
      els.statusPill.textContent = "● lỗi";
      els.statusPill.classList.add("err");
    } finally {
      setBusy(false);
      els.input.focus();
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  els.form.addEventListener("submit", (e) => {
    e.preventDefault();
    const t = els.input.value;
    els.input.value = "";
    autosize();
    sendMessage(t);
  });

  els.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      els.form.requestSubmit();
    }
  });

  function autosize() {
    els.input.style.height = "auto";
    els.input.style.height = Math.min(els.input.scrollHeight, 160) + "px";
  }
  els.input.addEventListener("input", autosize);

  els.newChat.addEventListener("click", async () => {
    if (sessionId) {
      try {
        await fetch("/api/clear", {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({ session_id: sessionId }),
        });
      } catch (_) {}
    }
    sessionId = "";
    localStorage.removeItem("jarvis_session_id");
    showEmpty();
  });

  document.querySelectorAll("[data-q]").forEach((b) =>
    b.addEventListener("click", () => {
      els.input.value = b.getAttribute("data-q");
      els.form.requestSubmit();
    })
  );

  async function boot() {
    try {
      const res = await fetch("/api/config");
      const cfg = await res.json();
      els.appName.textContent = cfg.app_name || "TungDevAI";
      document.title = cfg.app_name || "TungDevAI";
      els.modelLabel.textContent = `${cfg.provider} · ${cfg.model}`;
      if (cfg.telegram_bot) els.tgLink.href = cfg.telegram_bot;
      if (cfg.auth_required) {
        els.tokenBox.hidden = false;
      }
      els.statusPill.textContent = "● online";
      els.statusPill.classList.remove("err");
    } catch (e) {
      els.modelLabel.textContent = "offline";
      els.statusPill.textContent = "● offline";
      els.statusPill.classList.add("err");
    }
  }

  boot();
  els.input.focus();
})();
