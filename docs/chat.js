/**
 * Jarvis Chat — static ChatGPT-style UI for GitHub Pages.
 * Calls OpenAI-compatible /chat/completions from the browser.
 */
(() => {
  const STORAGE_CFG = "jarvis_pages_cfg_v1";
  const STORAGE_CHATS = "jarvis_pages_chats_v1";

  const PRESETS = {
    groq: {
      base: "https://api.groq.com/openai/v1",
      model: "llama-3.3-70b-versatile",
      label: "Groq",
    },
    openrouter: {
      base: "https://openrouter.ai/api/v1",
      model: "openrouter/auto",
      label: "OpenRouter",
    },
    xai: {
      base: "https://api.x.ai/v1",
      model: "grok-3-mini",
      label: "xAI",
    },
    custom: {
      base: "https://api.openai.com/v1",
      model: "gpt-4o-mini",
      label: "Custom",
    },
  };

  const DEFAULT_SYSTEM = `Bạn là Jarvis — trợ lý AI thông minh (web tĩnh + Telegram bot cùng thương hiệu).
Trả lời tiếng Việt khi user dùng tiếng Việt. Rõ ràng, có cấu trúc, code block khi cần.
Không bịa API; nếu không chắc hãy nói rõ.`;

  const $ = (id) => document.getElementById(id);
  const els = {
    sidebar: $("sidebar"),
    backdrop: $("backdrop"),
    history: $("history"),
    messages: $("messages"),
    welcome: $("welcome"),
    form: $("form"),
    input: $("input"),
    send: $("btnSend"),
    btnNew: $("btnNew"),
    btnSettings: $("btnSettings"),
    btnTopSettings: $("btnTopSettings"),
    btnOpenSidebar: $("btnOpenSidebar"),
    btnCloseSidebar: $("btnCloseSidebar"),
    modelChip: $("modelChip"),
    chatTitle: $("chatTitle"),
    statusDot: $("statusDot"),
    modal: $("settingsModal"),
    cfgPreset: $("cfgPreset"),
    cfgBase: $("cfgBase"),
    cfgKey: $("cfgKey"),
    cfgModel: $("cfgModel"),
    cfgSystem: $("cfgSystem"),
    cfgStream: $("cfgStream"),
    btnSave: $("btnSaveSettings"),
    btnTest: $("btnTest"),
    testOut: $("testOut"),
  };

  /** @type {{id:string,title:string,messages:{role:string,content:string}[],updated:number}[]} */
  let chats = [];
  /** @type {string|null} */
  let activeId = null;
  let busy = false;

  function loadCfg() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_CFG) || "{}");
    } catch {
      return {};
    }
  }

  function saveCfg(cfg) {
    localStorage.setItem(STORAGE_CFG, JSON.stringify(cfg));
    refreshModelChip();
  }

  function getCfg() {
    const c = loadCfg();
    return {
      preset: c.preset || "groq",
      base: (c.base || PRESETS.groq.base).replace(/\/$/, ""),
      key: c.key || "",
      model: c.model || PRESETS.groq.model,
      system: c.system || DEFAULT_SYSTEM,
      stream: c.stream !== false,
    };
  }

  function loadChats() {
    try {
      chats = JSON.parse(localStorage.getItem(STORAGE_CHATS) || "[]");
    } catch {
      chats = [];
    }
    if (!Array.isArray(chats)) chats = [];
  }

  function persistChats() {
    localStorage.setItem(STORAGE_CHATS, JSON.stringify(chats));
  }

  function uid() {
    return Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
  }

  function refreshModelChip() {
    const c = getCfg();
    els.modelChip.textContent = c.key
      ? `${c.model}`
      : "chưa có API key";
    els.statusDot.classList.toggle("ok", Boolean(c.key));
    els.statusDot.classList.toggle("err", !c.key);
  }

  function activeChat() {
    return chats.find((c) => c.id === activeId) || null;
  }

  function renderHistory() {
    els.history.innerHTML = "";
    const sorted = [...chats].sort((a, b) => b.updated - a.updated);
    for (const c of sorted) {
      const row = document.createElement("div");
      row.className = "hist-item" + (c.id === activeId ? " active" : "");
      row.innerHTML = `<span class="title"></span><button type="button" class="del" title="Xóa">✕</button>`;
      row.querySelector(".title").textContent = c.title || "Chat mới";
      row.querySelector(".title").addEventListener("click", () => selectChat(c.id));
      row.addEventListener("click", (e) => {
        if (e.target.closest(".del")) return;
        selectChat(c.id);
      });
      row.querySelector(".del").addEventListener("click", (e) => {
        e.stopPropagation();
        deleteChat(c.id);
      });
      els.history.appendChild(row);
    }
  }

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let s = escapeHtml(text);
    s = s.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
      return `<pre><code class="lang-${lang || "txt"}">${code.replace(/\n$/, "")}</code></pre>`;
    });
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|\n)[*-] (.+)/g, "$1• $2");
    // paragraphs
    s = s
      .split(/\n{2,}/)
      .map((p) => `<p>${p.replace(/\n/g, "<br>")}</p>`)
      .join("");
    return s;
  }

  function renderMessages() {
    const chat = activeChat();
    els.messages.innerHTML = "";
    if (!chat || chat.messages.length === 0) {
      els.messages.appendChild(els.welcome);
      els.welcome.style.display = "";
      bindSuggestions();
      els.chatTitle.textContent = "Jarvis";
      return;
    }
    els.chatTitle.textContent = chat.title || "Chat";
    for (const m of chat.messages) {
      appendMsg(m.role, m.content, false);
    }
    scrollBottom();
  }

  function appendMsg(role, content, scroll = true) {
    if (els.welcome && els.welcome.parentElement) {
      els.welcome.remove();
    }
    const row = document.createElement("div");
    row.className = `msg ${role}`;
    const av = document.createElement("div");
    av.className = "avatar";
    av.textContent = role === "user" ? "U" : "J";
    const body = document.createElement("div");
    body.className = "body";
    const roleEl = document.createElement("div");
    roleEl.className = "role";
    roleEl.textContent = role === "user" ? "Bạn" : "Jarvis";
    const contentEl = document.createElement("div");
    contentEl.className = "content";
    if (role === "assistant") contentEl.innerHTML = formatMarkdown(content);
    else contentEl.textContent = content;
    body.appendChild(roleEl);
    body.appendChild(contentEl);
    row.appendChild(av);
    row.appendChild(body);
    els.messages.appendChild(row);
    if (scroll) scrollBottom();
    return contentEl;
  }

  function scrollBottom() {
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function newChat() {
    const c = {
      id: uid(),
      title: "Chat mới",
      messages: [],
      updated: Date.now(),
    };
    chats.unshift(c);
    activeId = c.id;
    persistChats();
    renderHistory();
    renderMessages();
    closeSidebar();
    els.input.focus();
  }

  function selectChat(id) {
    activeId = id;
    renderHistory();
    renderMessages();
    closeSidebar();
  }

  function deleteChat(id) {
    chats = chats.filter((c) => c.id !== id);
    if (activeId === id) activeId = chats[0]?.id || null;
    persistChats();
    renderHistory();
    renderMessages();
  }

  function ensureChat() {
    if (!activeChat()) newChat();
    return activeChat();
  }

  function setBusy(v) {
    busy = v;
    els.send.disabled = v;
    els.input.disabled = v;
  }

  function openSettings() {
    const c = getCfg();
    els.cfgPreset.value = c.preset in PRESETS ? c.preset : "custom";
    els.cfgBase.value = c.base;
    els.cfgKey.value = c.key;
    els.cfgModel.value = c.model;
    els.cfgSystem.value = c.system;
    els.cfgStream.checked = c.stream;
    els.testOut.hidden = true;
    els.modal.showModal();
  }

  function applyPreset(name) {
    const p = PRESETS[name];
    if (!p || name === "custom") return;
    els.cfgBase.value = p.base;
    els.cfgModel.value = p.model;
  }

  async function chatCompletion(messages, { stream }) {
    const cfg = getCfg();
    if (!cfg.key) {
      throw new Error("Chưa có API key. Mở Cài đặt (⚙️) và dán key Groq/OpenRouter.");
    }
    const url = `${cfg.base}/chat/completions`;
    const body = {
      model: cfg.model,
      messages: [{ role: "system", content: cfg.system }, ...messages],
      temperature: 0.7,
      stream: Boolean(stream),
    };
    const headers = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${cfg.key}`,
    };
    // OpenRouter optional headers
    if (cfg.base.includes("openrouter")) {
      headers["HTTP-Referer"] = location.origin;
      headers["X-Title"] = "Jarvis AI Pages";
    }

    const res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`API ${res.status}: ${t.slice(0, 280)}`);
    }
    return res;
  }

  async function readStream(res, onDelta) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    let full = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() || "";
      for (const line of lines) {
        const s = line.trim();
        if (!s.startsWith("data:")) continue;
        const data = s.slice(5).trim();
        if (data === "[DONE]") continue;
        try {
          const json = JSON.parse(data);
          const delta = json.choices?.[0]?.delta?.content;
          if (delta) {
            full += delta;
            onDelta(full);
          }
        } catch {
          /* ignore partial */
        }
      }
    }
    return full;
  }

  async function sendMessage(text) {
    text = (text || "").trim();
    if (!text || busy) return;

    const cfg = getCfg();
    if (!cfg.key) {
      openSettings();
      els.testOut.hidden = false;
      els.testOut.className = "test-out err";
      els.testOut.textContent = "Cần API key trước khi chat (Groq free tại console.groq.com).";
      return;
    }

    const chat = ensureChat();
    chat.messages.push({ role: "user", content: text });
    if (chat.title === "Chat mới") {
      chat.title = text.slice(0, 40) + (text.length > 40 ? "…" : "");
    }
    chat.updated = Date.now();
    persistChats();
    renderHistory();

    els.input.value = "";
    autoResize();
    appendMsg("user", text);
    const contentEl = appendMsg("assistant", "");
    contentEl.parentElement.parentElement.classList.add("typing");
    contentEl.textContent = "";

    setBusy(true);
    try {
      const apiMessages = chat.messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      if (cfg.stream) {
        const res = await chatCompletion(apiMessages, { stream: true });
        const full = await readStream(res, (partial) => {
          contentEl.innerHTML = formatMarkdown(partial);
          scrollBottom();
        });
        contentEl.parentElement.parentElement.classList.remove("typing");
        if (!full) throw new Error("API trả về rỗng (có thể CORS hoặc model sai).");
        contentEl.innerHTML = formatMarkdown(full);
        chat.messages.push({ role: "assistant", content: full });
      } else {
        const res = await chatCompletion(apiMessages, { stream: false });
        const data = await res.json();
        const full = data.choices?.[0]?.message?.content?.trim() || "";
        contentEl.parentElement.parentElement.classList.remove("typing");
        if (!full) throw new Error("API trả về rỗng.");
        contentEl.innerHTML = formatMarkdown(full);
        chat.messages.push({ role: "assistant", content: full });
      }
      chat.updated = Date.now();
      persistChats();
      renderHistory();
      els.statusDot.classList.add("ok");
      els.statusDot.classList.remove("err");
    } catch (err) {
      contentEl.parentElement.parentElement.classList.remove("typing");
      const msg = err?.message || String(err);
      contentEl.innerHTML = formatMarkdown(
        `❌ **Lỗi:** ${msg}\n\n` +
          `Gợi ý:\n` +
          `- Kiểm tra API key / model trong ⚙️\n` +
          `- Một số API chặn CORS từ github.io → dùng **OpenRouter** hoặc tắt Stream\n` +
          `- Lấy Groq free: https://console.groq.com`
      );
      // remove empty assistant bubble content from history if failed mid-way
      els.statusDot.classList.add("err");
      els.statusDot.classList.remove("ok");
    } finally {
      setBusy(false);
      scrollBottom();
    }
  }

  function bindSuggestions() {
    els.messages.querySelectorAll("[data-q]").forEach((b) => {
      b.onclick = () => {
        els.input.value = b.getAttribute("data-q") || "";
        els.form.requestSubmit();
      };
    });
  }

  function autoResize() {
    const ta = els.input;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  }

  function openSidebar() {
    els.sidebar.classList.add("open");
    els.backdrop.hidden = false;
  }
  function closeSidebar() {
    els.sidebar.classList.remove("open");
    els.backdrop.hidden = true;
  }

  // Events
  els.form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(els.input.value);
  });
  els.input.addEventListener("input", autoResize);
  els.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      els.form.requestSubmit();
    }
  });
  els.btnNew.addEventListener("click", newChat);
  els.btnSettings.addEventListener("click", openSettings);
  els.btnTopSettings.addEventListener("click", openSettings);
  els.btnOpenSidebar?.addEventListener("click", openSidebar);
  els.btnCloseSidebar?.addEventListener("click", closeSidebar);
  els.backdrop?.addEventListener("click", closeSidebar);

  els.cfgPreset.addEventListener("change", () => applyPreset(els.cfgPreset.value));

  els.btnSave.addEventListener("click", () => {
    saveCfg({
      preset: els.cfgPreset.value,
      base: els.cfgBase.value.trim().replace(/\/$/, ""),
      key: els.cfgKey.value.trim(),
      model: els.cfgModel.value.trim(),
      system: els.cfgSystem.value.trim() || DEFAULT_SYSTEM,
      stream: els.cfgStream.checked,
    });
    els.testOut.hidden = false;
    els.testOut.className = "test-out ok";
    els.testOut.textContent = "Đã lưu trên trình duyệt này.";
    setTimeout(() => els.modal.close(), 400);
  });

  els.btnTest.addEventListener("click", async () => {
    // temporarily apply form values for test
    saveCfg({
      preset: els.cfgPreset.value,
      base: els.cfgBase.value.trim().replace(/\/$/, ""),
      key: els.cfgKey.value.trim(),
      model: els.cfgModel.value.trim(),
      system: els.cfgSystem.value.trim() || DEFAULT_SYSTEM,
      stream: false,
    });
    els.testOut.hidden = false;
    els.testOut.className = "test-out";
    els.testOut.textContent = "Đang test…";
    try {
      const res = await chatCompletion(
        [{ role: "user", content: "Trả lời đúng 1 từ: OK" }],
        { stream: false }
      );
      const data = await res.json();
      const t = data.choices?.[0]?.message?.content || "";
      els.testOut.className = "test-out ok";
      els.testOut.textContent = `OK — model phản hồi: ${t.slice(0, 80)}`;
    } catch (err) {
      els.testOut.className = "test-out err";
      els.testOut.textContent = err.message || String(err);
    }
  });

  // Boot
  loadChats();
  activeId = chats[0]?.id || null;
  refreshModelChip();
  renderHistory();
  renderMessages();
  bindSuggestions();

  // First visit without key → open settings once
  if (!getCfg().key && !localStorage.getItem("jarvis_pages_seen_settings")) {
    localStorage.setItem("jarvis_pages_seen_settings", "1");
    setTimeout(openSettings, 400);
  }
})();
