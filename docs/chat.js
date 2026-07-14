/**
 * Jarvis Chat - static ChatGPT-style UI for GitHub Pages.
 * Supports text + images (OpenAI-compatible vision models).
 * UI strings use plain ASCII Vietnamese to avoid encoding issues.
 */
(() => {
  const STORAGE_CFG = "jarvis_pages_cfg_v1";
  const STORAGE_CHATS = "jarvis_pages_chats_v1";
  const MAX_IMAGES = 4;
  const MAX_EDGE = 1280;
  const JPEG_Q = 0.82;

  const PRESETS = {
    groq: {
      base: "https://api.groq.com/openai/v1",
      model: "llama-3.3-70b-versatile",
      label: "Groq",
    },
    "groq-vision": {
      base: "https://api.groq.com/openai/v1",
      model: "meta-llama/llama-4-scout-17b-16e-instruct",
      label: "Groq Vision",
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

  const DEFAULT_SYSTEM =
    "Ban la Jarvis - tro ly AI thong minh (web + Telegram).\n" +
    "Tra loi tieng Viet khi user dung tieng Viet. Ro rang, co cau truc, code block khi can.\n" +
    "Khi user gui anh: mo ta / phan tich / tra loi cau hoi ve anh.\n" +
    "Khong bia API; neu khong chac hay noi ro.";

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
    btnPlus: $("btnPlus"),
    fileImage: $("fileImage"),
    attachPreview: $("attachPreview"),
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

  let pendingImages = [];
  let chats = [];
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
    const preset = c.preset || "groq";
    const def = PRESETS[preset] || PRESETS.groq;
    return {
      preset,
      base: (c.base || def.base).replace(/\/$/, ""),
      key: c.key || "",
      model: c.model || def.model,
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
    try {
      localStorage.setItem(STORAGE_CHATS, JSON.stringify(chats));
    } catch {
      for (const c of [...chats].sort((a, b) => a.updated - b.updated)) {
        for (const m of c.messages) {
          if (m.images && m.images.length) m.images = [];
        }
        try {
          localStorage.setItem(STORAGE_CHATS, JSON.stringify(chats));
          break;
        } catch {
          /* continue */
        }
      }
    }
  }

  function uid() {
    return Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
  }

  function refreshModelChip() {
    const c = getCfg();
    els.modelChip.textContent = c.key ? String(c.model) : "chua co API key";
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
      row.innerHTML =
        '<span class="title"></span><button type="button" class="del" title="Xoa">X</button>';
      row.querySelector(".title").textContent = c.title || "Chat moi";
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
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let s = escapeHtml(text);
    s = s.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
      return (
        '<pre><code class="lang-' +
        (lang || "txt") +
        '">' +
        code.replace(/\n$/, "") +
        "</code></pre>"
      );
    });
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|\n)[*-] (.+)/g, "$1• $2");
    s = s
      .split(/\n{2,}/)
      .map((p) => "<p>" + p.replace(/\n/g, "<br>") + "</p>")
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
      appendMsg(m.role, m.content, m.images || [], false);
    }
    scrollBottom();
  }

  function appendMsg(role, content, images, scroll) {
    if (images === undefined) images = [];
    if (scroll === undefined) scroll = true;
    if (els.welcome && els.welcome.parentElement) {
      els.welcome.remove();
    }
    const row = document.createElement("div");
    row.className = "msg " + role;
    const av = document.createElement("div");
    av.className = "avatar";
    av.textContent = role === "user" ? "U" : "J";
    const body = document.createElement("div");
    body.className = "body";
    const roleEl = document.createElement("div");
    roleEl.className = "role";
    roleEl.textContent = role === "user" ? "Ban" : "Jarvis";
    body.appendChild(roleEl);

    if (images && images.length) {
      const wrap = document.createElement("div");
      wrap.className = "msg-images";
      for (const src of images) {
        const img = document.createElement("img");
        img.src = src;
        img.alt = "Anh";
        img.addEventListener("click", () => window.open(src, "_blank"));
        wrap.appendChild(img);
      }
      body.appendChild(wrap);
    }

    const contentEl = document.createElement("div");
    contentEl.className = "content";
    if (role === "assistant") contentEl.innerHTML = formatMarkdown(content || "");
    else contentEl.textContent = content || "";
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
      title: "Chat moi",
      messages: [],
      updated: Date.now(),
    };
    chats.unshift(c);
    activeId = c.id;
    clearPendingImages();
    persistChats();
    renderHistory();
    renderMessages();
    closeSidebar();
    els.input.focus();
  }

  function selectChat(id) {
    activeId = id;
    clearPendingImages();
    renderHistory();
    renderMessages();
    closeSidebar();
  }

  function deleteChat(id) {
    chats = chats.filter((c) => c.id !== id);
    if (activeId === id) activeId = chats[0] ? chats[0].id : null;
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
    if (els.btnPlus) els.btnPlus.disabled = v;
  }

  function clearPendingImages() {
    pendingImages = [];
    renderAttachPreview();
  }

  function renderAttachPreview() {
    if (!els.attachPreview) return;
    if (!pendingImages.length) {
      els.attachPreview.hidden = true;
      els.attachPreview.innerHTML = "";
      return;
    }
    els.attachPreview.hidden = false;
    els.attachPreview.innerHTML = "";
    pendingImages.forEach((src, i) => {
      const chip = document.createElement("div");
      chip.className = "attach-chip";
      chip.innerHTML =
        '<img alt="preview" /><button type="button" class="rm" title="Go">X</button>';
      chip.querySelector("img").src = src;
      chip.querySelector(".rm").addEventListener("click", () => {
        pendingImages.splice(i, 1);
        renderAttachPreview();
      });
      els.attachPreview.appendChild(chip);
    });
  }

  function fileToDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error("Khong doc duoc file anh"));
      reader.readAsDataURL(file);
    });
  }

  function compressImage(dataUrl) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;
        const max = MAX_EDGE;
        if (width > max || height > max) {
          const r = Math.min(max / width, max / height);
          width = Math.round(width * r);
          height = Math.round(height * r);
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL("image/jpeg", JPEG_Q));
      };
      img.onerror = () => resolve(dataUrl);
      img.src = dataUrl;
    });
  }

  async function addFiles(fileList) {
    const files = Array.prototype.slice
      .call(fileList)
      .filter((f) => f.type.indexOf("image/") === 0);
    for (let i = 0; i < files.length; i++) {
      if (pendingImages.length >= MAX_IMAGES) break;
      try {
        let data = await fileToDataUrl(files[i]);
        data = await compressImage(data);
        pendingImages.push(data);
      } catch (e) {
        console.warn(e);
      }
    }
    renderAttachPreview();
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

  function toApiMessages(messages) {
    return messages.map((m) => {
      if (m.role === "assistant") {
        return { role: "assistant", content: m.content || "" };
      }
      const imgs = m.images || [];
      if (!imgs.length) {
        return { role: "user", content: m.content || "" };
      }
      const parts = [];
      const text =
        (m.content || "").trim() || "Hay xem anh va phan tich / tra loi.";
      parts.push({ type: "text", text: text });
      for (let i = 0; i < imgs.length; i++) {
        parts.push({
          type: "image_url",
          image_url: { url: imgs[i] },
        });
      }
      return { role: "user", content: parts };
    });
  }

  async function chatCompletion(messages, opts) {
    const stream = opts && opts.stream;
    const cfg = getCfg();
    if (!cfg.key) {
      throw new Error("Chua co API key. Mo Cai dat va dan key Groq/OpenRouter.");
    }
    const url = cfg.base + "/chat/completions";
    const body = {
      model: cfg.model,
      messages: [{ role: "system", content: cfg.system }].concat(messages),
      temperature: 0.7,
      stream: Boolean(stream),
    };
    const headers = {
      "Content-Type": "application/json",
      Authorization: "Bearer " + cfg.key,
    };
    if (cfg.base.indexOf("openrouter") !== -1) {
      headers["HTTP-Referer"] = location.origin;
      headers["X-Title"] = "Jarvis AI Pages";
    }

    const res = await fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error("API " + res.status + ": " + t.slice(0, 320));
    }
    return res;
  }

  async function readStream(res, onDelta) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    let full = "";
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      buf += decoder.decode(chunk.value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() || "";
      for (let i = 0; i < lines.length; i++) {
        const s = lines[i].trim();
        if (s.indexOf("data:") !== 0) continue;
        const data = s.slice(5).trim();
        if (data === "[DONE]") continue;
        try {
          const json = JSON.parse(data);
          const delta =
            json.choices &&
            json.choices[0] &&
            json.choices[0].delta &&
            json.choices[0].delta.content;
          if (delta) {
            full += delta;
            onDelta(full);
          }
        } catch (e) {
          /* ignore */
        }
      }
    }
    return full;
  }

  async function sendMessage(text) {
    text = (text || "").trim();
    const images = pendingImages.slice();
    if ((!text && !images.length) || busy) return;

    const cfg = getCfg();
    if (!cfg.key) {
      openSettings();
      els.testOut.hidden = false;
      els.testOut.className = "test-out err";
      els.testOut.textContent = "Can API key truoc khi chat.";
      return;
    }

    if (images.length && /llama-3\.3-70b|versatile|deepseek-chat/i.test(cfg.model)) {
      const ok = confirm(
        "Model hien tai co the khong ho tro anh.\n\n" +
          "Nen chon preset Groq vision trong Cai dat.\n\n" +
          "Van gui tiep?"
      );
      if (!ok) {
        openSettings();
        return;
      }
    }

    const chat = ensureChat();
    chat.messages.push({ role: "user", content: text, images: images });
    if (chat.title === "Chat moi") {
      const t = text || "Anh dinh kem";
      chat.title = t.slice(0, 40) + (t.length > 40 ? "..." : "");
    }
    chat.updated = Date.now();
    persistChats();
    renderHistory();

    els.input.value = "";
    autoResize();
    clearPendingImages();
    appendMsg("user", text, images);
    const contentEl = appendMsg("assistant", "", [], true);
    contentEl.parentElement.parentElement.classList.add("typing");
    contentEl.textContent = "";

    setBusy(true);
    try {
      const apiMessages = toApiMessages(chat.messages);

      if (cfg.stream) {
        const res = await chatCompletion(apiMessages, { stream: true });
        const full = await readStream(res, (partial) => {
          contentEl.innerHTML = formatMarkdown(partial);
          scrollBottom();
        });
        contentEl.parentElement.parentElement.classList.remove("typing");
        if (!full) throw new Error("API tra ve rong (CORS / model / vision).");
        contentEl.innerHTML = formatMarkdown(full);
        chat.messages.push({ role: "assistant", content: full });
      } else {
        const res = await chatCompletion(apiMessages, { stream: false });
        const data = await res.json();
        const full =
          (data.choices &&
            data.choices[0] &&
            data.choices[0].message &&
            data.choices[0].message.content &&
            data.choices[0].message.content.trim()) ||
          "";
        contentEl.parentElement.parentElement.classList.remove("typing");
        if (!full) throw new Error("API tra ve rong.");
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
      const msg = (err && err.message) || String(err);
      contentEl.innerHTML = formatMarkdown(
        "**Loi:** " +
          msg +
          "\n\n" +
          "Goi y khi gui anh:\n" +
          "- Cai dat preset **Groq vision**\n" +
          "- Model: `meta-llama/llama-4-scout-17b-16e-instruct`\n" +
          "- Anh toi da 4 tam\n" +
          "- Key free: https://console.groq.com"
      );
      els.statusDot.classList.add("err");
      els.statusDot.classList.remove("ok");
    } finally {
      setBusy(false);
      scrollBottom();
    }
  }

  function bindSuggestions() {
    const nodes = els.messages.querySelectorAll("[data-q]");
    for (let i = 0; i < nodes.length; i++) {
      nodes[i].onclick = function () {
        els.input.value = this.getAttribute("data-q") || "";
        els.form.requestSubmit();
      };
    }
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

  function pickImageFromDevice() {
    const input = document.getElementById("fileImage");
    if (!input) {
      alert("Khong tim thay o chon anh. Thu Ctrl+F5.");
      return;
    }
    input.value = "";
    input.click();
  }

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

  els.input.addEventListener("paste", (e) => {
    const items = e.clipboardData && e.clipboardData.items;
    if (!items) return;
    const files = [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image/") === 0) {
        const f = items[i].getAsFile();
        if (f) files.push(f);
      }
    }
    if (files.length) {
      e.preventDefault();
      addFiles(files);
    }
  });

  els.form.addEventListener("dragover", (e) => {
    e.preventDefault();
    els.form.classList.add("drag");
  });
  els.form.addEventListener("dragleave", () => els.form.classList.remove("drag"));
  els.form.addEventListener("drop", (e) => {
    e.preventDefault();
    els.form.classList.remove("drag");
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
      addFiles(e.dataTransfer.files);
    }
  });

  // Plus button: open device image picker
  (function wirePlus() {
    const btn = document.getElementById("btnPlus");
    const input = document.getElementById("fileImage");
    if (!btn || !input) {
      console.error("Jarvis: btnPlus or fileImage missing");
      return;
    }
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (busy) return;
      pickImageFromDevice();
    });
    input.addEventListener("change", function () {
      if (input.files && input.files.length) addFiles(input.files);
      input.value = "";
    });
  })();

  els.btnNew.addEventListener("click", newChat);
  els.btnSettings.addEventListener("click", openSettings);
  els.btnTopSettings.addEventListener("click", openSettings);
  if (els.btnOpenSidebar) els.btnOpenSidebar.addEventListener("click", openSidebar);
  if (els.btnCloseSidebar) els.btnCloseSidebar.addEventListener("click", closeSidebar);
  if (els.backdrop) els.backdrop.addEventListener("click", closeSidebar);

  els.cfgPreset.addEventListener("change", function () {
    applyPreset(els.cfgPreset.value);
  });

  els.btnSave.addEventListener("click", function () {
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
    els.testOut.textContent = "Da luu tren trinh duyet nay.";
    setTimeout(function () {
      els.modal.close();
    }, 400);
  });

  els.btnTest.addEventListener("click", async function () {
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
    els.testOut.textContent = "Dang test...";
    try {
      const res = await chatCompletion(
        [{ role: "user", content: "Tra loi dung 1 tu: OK" }],
        { stream: false }
      );
      const data = await res.json();
      const t =
        (data.choices &&
          data.choices[0] &&
          data.choices[0].message &&
          data.choices[0].message.content) ||
        "";
      els.testOut.className = "test-out ok";
      els.testOut.textContent = "OK - " + String(t).slice(0, 80);
    } catch (err) {
      els.testOut.className = "test-out err";
      els.testOut.textContent = err.message || String(err);
    }
  });

  loadChats();
  activeId = chats[0] ? chats[0].id : null;
  refreshModelChip();
  renderHistory();
  renderMessages();
  bindSuggestions();

  if (!getCfg().key && !localStorage.getItem("jarvis_pages_seen_settings")) {
    localStorage.setItem("jarvis_pages_seen_settings", "1");
    setTimeout(openSettings, 400);
  }
})();
