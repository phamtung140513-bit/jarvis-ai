/**
 * TungDevAI Chat — user-facing only (no admin UI).
 * Admin page is separate: /j-panel.html (secret URL).
 */
(() => {
  const LS_API = "jarvis_api_base_v2";
  const LS_USER_TOKEN = "jarvis_user_token_v2";
  const LS_GOOGLE = "jarvis_google_session_v1";
  const LS_GOOGLE_USER = "jarvis_google_user_v1";
  const LS_CHATS = "jarvis_chats_v3"; // stable key — survives tab close
  const LS_ACTIVE = "jarvis_active_chat_v3";
  const LS_SID = "jarvis_sid_v3";
  const MAX_IMAGES = 4;
  const MAX_EDGE = 1280;
  const JPEG_Q = 0.82;

  const $ = (id) => document.getElementById(id);
  const els = {
    authGate: $("authGate"),
    app: $("app"),
    googleBtnWrap: $("googleBtnWrap"),
    authHint: $("authHint"),
    authErr: $("authErr"),
    authOk: $("authOk"),
    tabLogin: $("tabLogin"),
    tabRegister: $("tabRegister"),
    formLogin: $("formLogin"),
    formRegister: $("formRegister"),
    loginEmail: $("loginEmail"),
    loginPassword: $("loginPassword"),
    regName: $("regName"),
    regEmail: $("regEmail"),
    regPassword: $("regPassword"),
    regCode: $("regCode"),
    btnSendCode: $("btnSendCode"),
    codeHint: $("codeHint"),
    btnGoogleFallback: $("btnGoogleFallback"),
    sidebar: $("sidebar"),
    backdrop: $("backdrop"),
    history: $("history"),
    messages: $("messages"),
    welcome: $("welcome"),
    form: $("form"),
    input: $("input"),
    send: $("btnSend"),
    btnNew: $("btnNew"),
    btnLogout: $("btnLogout"),
    btnOpenSidebar: $("btnOpenSidebar"),
    btnCloseSidebar: $("btnCloseSidebar"),
    btnPlus: $("btnPlus"),
    fileImage: $("fileImage"),
    attachPreview: $("attachPreview"),
    modelChip: $("modelChip"),
    appNameLabel: $("appNameLabel"),
    chatTitle: $("chatTitle"),
    statusDot: $("statusDot"),
    tgLink: $("tgLink"),
    userAvatar: $("userAvatar"),
    userChipBtn: $("userChipBtn"),
    userPill: $("userPill"),
    userPillImg: $("userPillImg"),
    userPillName: $("userPillName"),
    welcomeName: $("welcomeName"),
  };

  let googleUser = null;
  let googleSession = localStorage.getItem(LS_GOOGLE) || "";
  let serverOnline = false;
  let lastModel = "";
  let serverConfig = {
    google_client_id: "",
    google_auth_required: false,
    auth_required: false,
    email_auth: true,
  };

  let cfgPublic = { apiBase: "", telegramBot: "https://t.me/grokapiai_bot" };
  let pendingImages = [];
  let chats = [];
  let activeId = null;
  let busy = false;
  let sendCodeCooldown = 0;
  let sessionId = localStorage.getItem(LS_SID) || localStorage.getItem("jarvis_sid_v2") || "";

  /**
   * Same domain as the web UI by default (empty apiBase => location.origin).
   * On GitHub Pages (static only) there is no API — force local server URL.
   */
  function apiBase() {
    const host = (location.hostname || "").toLowerCase();
    // Static GitHub Pages cannot run Python API
    if (host.indexOf("github.io") !== -1) {
      const fromLs = (localStorage.getItem(LS_API) || "").trim().replace(/\/$/, "");
      return fromLs || "http://127.0.0.1:7860";
    }
    const fromLs = (localStorage.getItem(LS_API) || "").trim().replace(/\/$/, "");
    if (fromLs) return fromLs;
    const fromCfg = (cfgPublic.apiBase || "").trim().replace(/\/$/, "");
    if (fromCfg) return fromCfg;
    // Same origin (http://127.0.0.1:7860 or VPS domain)
    return (location.origin || "").replace(/\/$/, "");
  }

  function userToken() {
    return (localStorage.getItem(LS_USER_TOKEN) || "").trim();
  }

  function userHeaders(extra) {
    const h = Object.assign({ "Content-Type": "application/json" }, extra || {});
    const t = userToken();
    if (t) h["X-Web-Token"] = t;
    if (googleSession) h["X-User-Session"] = googleSession;
    return h;
  }

  function showApp() {
    if (els.authGate) els.authGate.classList.add("hidden");
    if (els.app) els.app.classList.remove("hidden");
  }

  function showGate(tab) {
    if (els.authGate) els.authGate.classList.remove("hidden");
    if (els.app) els.app.classList.add("hidden");
    if (tab) switchAuthTab(tab);
    clearAuthMsgs();
    renderGoogleButton();
  }

  function isLoggedIn() {
    return !!(googleSession && googleUser);
  }

  function clearAuthMsgs() {
    if (els.authErr) {
      els.authErr.classList.add("hidden");
      els.authErr.textContent = "";
    }
    if (els.authOk) {
      els.authOk.classList.add("hidden");
      els.authOk.textContent = "";
    }
  }

  function showAuthErr(msg) {
    if (els.authOk) els.authOk.classList.add("hidden");
    if (els.authErr) {
      els.authErr.classList.remove("hidden");
      els.authErr.textContent = String(msg || "Loi");
    }
  }

  function showAuthOk(msg) {
    if (els.authErr) els.authErr.classList.add("hidden");
    if (els.authOk) {
      els.authOk.classList.remove("hidden");
      els.authOk.textContent = String(msg || "");
    }
  }

  function switchAuthTab(tab) {
    const isLogin = tab !== "register";
    if (els.tabLogin) els.tabLogin.classList.toggle("active", isLogin);
    if (els.tabRegister) els.tabRegister.classList.toggle("active", !isLogin);
    if (els.formLogin) els.formLogin.classList.toggle("hidden", !isLogin);
    if (els.formRegister) els.formRegister.classList.toggle("hidden", isLogin);
    clearAuthMsgs();
  }

  function refreshUserChip() {
    if (!els.modelChip) return;
    if (!isLoggedIn()) {
      if (els.appNameLabel) els.appNameLabel.textContent = cfgPublic.appName || "TungDevAI";
      els.modelChip.textContent = "Dang nhap";
      els.modelChip.classList.add("login-cta");
      if (els.userPillName) els.userPillName.textContent = "Dang nhap";
      if (els.userAvatar) els.userAvatar.src = "assets/bot-avatar.jpg";
      if (els.userPillImg) els.userPillImg.src = "assets/bot-avatar.jpg";
      return;
    }
    els.modelChip.classList.remove("login-cta");
    const u = googleUser || {};
    const email = u.email || "";
    if (serverOnline && lastModel) {
      els.modelChip.textContent = lastModel;
    } else if (serverOnline) {
      els.modelChip.textContent = email || "online";
    } else {
      // offline: still show email, not "server offline" as identity
      els.modelChip.textContent = email || "offline";
    }
  }

  function applyUserUi(user) {
    googleUser = user || null;
    if (!user) {
      refreshUserChip();
      return;
    }
    const name = user.name || user.email || "User";
    if (els.userPillName) els.userPillName.textContent = name;
    if (els.welcomeName) els.welcomeName.textContent = name.split(" ")[0] || name;
    if (els.appNameLabel) els.appNameLabel.textContent = name;
    if (user.picture) {
      if (els.userPillImg) els.userPillImg.src = user.picture;
      if (els.userAvatar) els.userAvatar.src = user.picture;
    } else {
      if (els.userPillImg) els.userPillImg.src = "assets/bot-avatar.jpg";
      if (els.userAvatar) els.userAvatar.src = "assets/bot-avatar.jpg";
    }
    if (els.userPill) els.userPill.title = user.email || name;
    refreshUserChip();
  }

  function onAuthSuccess(data) {
    googleSession = data.session_token;
    localStorage.setItem(LS_GOOGLE, googleSession);
    localStorage.setItem(LS_GOOGLE_USER, JSON.stringify(data.user || {}));
    applyUserUi(data.user);
    showApp();
    loadChats();
    activeId =
      localStorage.getItem(LS_ACTIVE) || (chats[0] ? chats[0].id : null);
    renderHistory();
    renderMessages();
    bindSuggestions();
    pingServer();
  }

  function logoutGoogle() {
    if (googleSession) {
      fetch(apiBase() + "/api/auth/logout", {
        method: "POST",
        headers: { "X-User-Session": googleSession },
      }).catch(function () {});
    }
    googleSession = "";
    googleUser = null;
    localStorage.removeItem(LS_GOOGLE);
    localStorage.removeItem(LS_GOOGLE_USER);
    applyUserUi(null);
    showGate("login");
  }

  async function parseJsonResponse(r) {
    const text = await r.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
    if (!r.ok) {
      const d = data.detail;
      let msg = text || "Request failed";
      if (typeof d === "string") msg = d;
      else if (Array.isArray(d)) msg = d.map(function (x) { return x.msg || x; }).join("; ");
      else if (d) msg = JSON.stringify(d);
      throw new Error(msg);
    }
    return data;
  }

  async function handleGoogleCredential(response) {
    try {
      clearAuthMsgs();
      if (els.authHint) els.authHint.textContent = "Dang xac thuc Google...";
      const r = await fetch(apiBase() + "/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: response.credential }),
      });
      const data = await parseJsonResponse(r);
      if (els.authHint) els.authHint.textContent = "";
      onAuthSuccess(data);
    } catch (e) {
      if (els.authHint) els.authHint.textContent = "";
      showAuthErr(e.message || e);
    }
  }

  function renderGoogleButton() {
    const clientId = serverConfig.google_client_id || "";
    if (els.btnGoogleFallback) els.btnGoogleFallback.classList.add("hidden");
    if (!clientId) {
      if (els.googleBtnWrap) {
        els.googleBtnWrap.innerHTML =
          '<p class="auth-hint" style="margin:0">Google chua cau hinh (GOOGLE_CLIENT_ID). Van dung duoc email.</p>';
      }
      return;
    }
    if (typeof google === "undefined" || !google.accounts || !google.accounts.id) {
      if (els.authHint) els.authHint.textContent = "Dang tai Google SDK...";
      if (els.btnGoogleFallback) els.btnGoogleFallback.classList.remove("hidden");
      setTimeout(renderGoogleButton, 400);
      return;
    }
    if (els.authHint && !els.authHint.textContent) {
      /* keep other hints */
    }
    google.accounts.id.initialize({
      client_id: clientId,
      callback: handleGoogleCredential,
      auto_select: false,
      cancel_on_tap_outside: true,
    });
    if (els.googleBtnWrap) {
      els.googleBtnWrap.innerHTML = "";
      google.accounts.id.renderButton(els.googleBtnWrap, {
        theme: "outline",
        size: "large",
        shape: "pill",
        text: "continue_with",
        width: 320,
      });
    }
  }

  async function restoreGoogleSession() {
    if (!googleSession) return false;
    try {
      const r = await fetch(apiBase() + "/api/auth/me", {
        headers: { "X-User-Session": googleSession },
        cache: "no-store",
      });
      if (!r.ok) {
        googleSession = "";
        googleUser = null;
        localStorage.removeItem(LS_GOOGLE);
        localStorage.removeItem(LS_GOOGLE_USER);
        return false;
      }
      const j = await r.json();
      applyUserUi(j.user);
      showApp();
      return true;
    } catch (e) {
      try {
        const cached = JSON.parse(localStorage.getItem(LS_GOOGLE_USER) || "null");
        if (cached) {
          applyUserUi(cached);
          showApp();
          return true;
        }
      } catch (e2) {
        /* ignore */
      }
      return false;
    }
  }

  async function sendRegisterCode() {
    clearAuthMsgs();
    const email = (els.regEmail && els.regEmail.value || "").trim();
    if (!email) {
      showAuthErr("Nhap email de nhan ma");
      return;
    }
    if (els.btnSendCode) els.btnSendCode.disabled = true;
    try {
      const r = await fetch(apiBase() + "/api/auth/send-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, purpose: "register" }),
      });
      const data = await parseJsonResponse(r);
      let msg = data.message || "Da gui ma xac thuc.";
      if (data.dev_code) {
        msg = "Ma xac thuc (dev): " + data.dev_code + " — nhap vao o Ma xac thuc.";
        if (els.regCode) els.regCode.value = data.dev_code;
      }
      showAuthOk(msg);
      if (els.codeHint) els.codeHint.textContent = data.sent ? "Kiem tra hop thu (va spam)." : "";
      // cooldown UI
      sendCodeCooldown = 45;
      const tick = function () {
        if (!els.btnSendCode) return;
        if (sendCodeCooldown <= 0) {
          els.btnSendCode.disabled = false;
          els.btnSendCode.textContent = "Gui ma";
          return;
        }
        els.btnSendCode.textContent = "Gui lai (" + sendCodeCooldown + "s)";
        sendCodeCooldown -= 1;
        setTimeout(tick, 1000);
      };
      tick();
    } catch (e) {
      if (els.btnSendCode) {
        els.btnSendCode.disabled = false;
        els.btnSendCode.textContent = "Gui ma";
      }
      showAuthErr(e.message || e);
    }
  }

  async function submitLogin(e) {
    if (e) e.preventDefault();
    clearAuthMsgs();
    const email = (els.loginEmail && els.loginEmail.value || "").trim();
    const password = (els.loginPassword && els.loginPassword.value || "");
    if (!email || !password) {
      showAuthErr("Nhap email va mat khau");
      return;
    }
    try {
      if (els.authHint) els.authHint.textContent = "Dang dang nhap...";
      const r = await fetch(apiBase() + "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: password }),
      });
      const data = await parseJsonResponse(r);
      if (els.authHint) els.authHint.textContent = "";
      onAuthSuccess(data);
    } catch (err) {
      if (els.authHint) els.authHint.textContent = "";
      showAuthErr(err.message || err);
    }
  }

  async function submitRegister(e) {
    if (e) e.preventDefault();
    clearAuthMsgs();
    const email = (els.regEmail && els.regEmail.value || "").trim();
    const password = (els.regPassword && els.regPassword.value || "");
    const code = (els.regCode && els.regCode.value || "").trim();
    const name = (els.regName && els.regName.value || "").trim();
    if (!email || !password) {
      showAuthErr("Nhap email va mat khau");
      return;
    }
    if (password.length < 6) {
      showAuthErr("Mat khau toi thieu 6 ky tu");
      return;
    }
    if (!code) {
      showAuthErr("Bam Gui ma roi nhap ma 6 so tu email");
      return;
    }
    try {
      if (els.authHint) els.authHint.textContent = "Dang tao tai khoan...";
      const r = await fetch(apiBase() + "/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email,
          password: password,
          code: code,
          name: name,
        }),
      });
      const data = await parseJsonResponse(r);
      if (els.authHint) els.authHint.textContent = "";
      onAuthSuccess(data);
    } catch (err) {
      if (els.authHint) els.authHint.textContent = "";
      showAuthErr(err.message || err);
    }
  }

  function openLoginFromChip() {
    if (isLoggedIn()) return;
    showGate("login");
  }

  async function loadPublicConfig() {
    try {
      const r = await fetch("config.json?v=6", { cache: "no-store" });
      if (r.ok) {
        const j = await r.json();
        cfgPublic = Object.assign(cfgPublic, j);
      }
    } catch (e) {
      /* use defaults */
    }
    if (els.tgLink && cfgPublic.telegramBot) els.tgLink.href = cfgPublic.telegramBot;
    if (els.appNameLabel && cfgPublic.appName) els.appNameLabel.textContent = cfgPublic.appName;
  }

  function _slimChats(list) {
    // Drop big base64 images so localStorage never blows quota
    return list.map(function (c) {
      return {
        id: c.id,
        title: c.title,
        updated: c.updated,
        sessionId: c.sessionId || "",
        messages: (c.messages || []).map(function (m) {
          return {
            role: m.role,
            content: m.content || "",
            // keep at most 1 small image marker, not full data url if huge
            images: (m.images || []).length
              ? m.images.filter(function (img) {
                  return typeof img === "string" && img.length < 200000;
                }).slice(0, 2)
              : [],
          };
        }),
      };
    });
  }

  function loadChats() {
    try {
      // migrate old keys if present
      var raw =
        localStorage.getItem(LS_CHATS) ||
        localStorage.getItem("jarvis_pages_chats_v2") ||
        localStorage.getItem("jarvis_pages_chats_v1") ||
        "[]";
      chats = JSON.parse(raw);
    } catch (e) {
      chats = [];
    }
    if (!Array.isArray(chats)) chats = [];
  }

  function persistChats() {
    try {
      localStorage.setItem(LS_CHATS, JSON.stringify(_slimChats(chats)));
      if (activeId) localStorage.setItem(LS_ACTIVE, activeId);
      if (sessionId) localStorage.setItem(LS_SID, sessionId);
    } catch (e) {
      // Quota: strip all images and retry
      try {
        chats.forEach(function (c) {
          (c.messages || []).forEach(function (m) {
            m.images = [];
          });
        });
        localStorage.setItem(LS_CHATS, JSON.stringify(_slimChats(chats)));
      } catch (e2) {
        console.warn("persistChats failed", e2);
      }
    }
  }

  // Save when closing tab / switching away
  window.addEventListener("beforeunload", function () {
    persistChats();
  });
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") persistChats();
  });

  function uid() {
    return Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
  }

  function setStatus(ok) {
    els.statusDot.classList.toggle("ok", ok);
    els.statusDot.classList.toggle("err", !ok);
  }

  async function pingServer() {
    try {
      const r = await fetch(apiBase() + "/api/health", { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const j = await r.json();
      lastModel = j.model || "";
      serverOnline = true;
      setStatus(true);
      refreshUserChip();
      return j;
    } catch (e) {
      serverOnline = false;
      setStatus(false);
      refreshUserChip();
      return null;
    }
  }

  function activeChat() {
    return chats.find((c) => c.id === activeId) || null;
  }

  function renderHistory() {
    els.history.innerHTML = "";
    const sorted = chats.slice().sort((a, b) => b.updated - a.updated);
    sorted.forEach((c) => {
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
    });
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
    return s
      .split(/\n{2,}/)
      .map((p) => "<p>" + p.replace(/\n/g, "<br>") + "</p>")
      .join("");
  }

  function renderMessages() {
    const chat = activeChat();
    els.messages.innerHTML = "";
    if (!chat || !chat.messages.length) {
      els.messages.appendChild(els.welcome);
      els.welcome.style.display = "";
      bindSuggestions();
      els.chatTitle.textContent = "TungDevAI";
      return;
    }
    els.chatTitle.textContent = chat.title || "Chat";
    chat.messages.forEach((m) => appendMsg(m.role, m.content, m.images || [], false));
    scrollBottom();
  }

  function appendMsg(role, content, images, scroll) {
    if (!images) images = [];
    if (scroll === undefined) scroll = true;
    if (els.welcome && els.welcome.parentElement) els.welcome.remove();
    const row = document.createElement("div");
    row.className = "msg " + role;
    const av = document.createElement("div");
    av.className = "avatar";
    av.textContent = role === "user" ? "U" : "T";
    const body = document.createElement("div");
    body.className = "body";
    const roleEl = document.createElement("div");
    roleEl.className = "role";
    roleEl.textContent = role === "user" ? "Ban" : "TungDevAI";
    body.appendChild(roleEl);
    if (images.length) {
      const wrap = document.createElement("div");
      wrap.className = "msg-images";
      images.forEach((src) => {
        const img = document.createElement("img");
        img.src = src;
        img.alt = "Anh";
        wrap.appendChild(img);
      });
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
      sessionId: "",
    };
    chats.unshift(c);
    activeId = c.id;
    sessionId = "";
    localStorage.removeItem(LS_SID);
    localStorage.removeItem("jarvis_sid_v2");
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
      chip.innerHTML = '<img alt="p" /><button type="button" class="rm">X</button>';
      chip.querySelector("img").src = src;
      chip.querySelector(".rm").onclick = () => {
        pendingImages.splice(i, 1);
        renderAttachPreview();
      };
      els.attachPreview.appendChild(chip);
    });
  }

  function fileToDataUrl(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(r.result);
      r.onerror = () => reject(new Error("read fail"));
      r.readAsDataURL(file);
    });
  }

  function compressImage(dataUrl) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        let w = img.width;
        let h = img.height;
        if (w > MAX_EDGE || h > MAX_EDGE) {
          const r = Math.min(MAX_EDGE / w, MAX_EDGE / h);
          w = Math.round(w * r);
          h = Math.round(h * r);
        }
        const c = document.createElement("canvas");
        c.width = w;
        c.height = h;
        c.getContext("2d").drawImage(img, 0, 0, w, h);
        resolve(c.toDataURL("image/jpeg", JPEG_Q));
      };
      img.onerror = () => resolve(dataUrl);
      img.src = dataUrl;
    });
  }

  async function addFiles(fileList) {
    const files = Array.prototype.filter.call(fileList, (f) => f.type.indexOf("image/") === 0);
    for (let i = 0; i < files.length && pendingImages.length < MAX_IMAGES; i++) {
      try {
        let d = await fileToDataUrl(files[i]);
        d = await compressImage(d);
        pendingImages.push(d);
      } catch (e) {
        console.warn(e);
      }
    }
    renderAttachPreview();
  }

  /** Chat via backend — API keys stay on server */
  async function sendMessage(text) {
    text = (text || "").trim();
    const images = pendingImages.slice();
    if ((!text && !images.length) || busy) return;

    // Images: note for now backend is text; attach as context note
    let payloadText = text;
    if (images.length) {
      payloadText =
        (text || "Toi gui kem anh (base64 rut gon).") +
        "\n\n[User attached " +
        images.length +
        " image(s) in browser UI — backend text path: mo ta/yeu cau xu ly anh neu model vision server ho tro sau.]";
    }

    const chat = ensureChat();
    chat.messages.push({ role: "user", content: text, images: images });
    if (chat.title === "Chat moi") {
      const t = text || "Anh";
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
      const res = await fetch(apiBase() + "/api/chat", {
        method: "POST",
        headers: userHeaders(),
        body: JSON.stringify({
          message: payloadText,
          session_id: sessionId,
          stream: true,
        }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error("Server " + res.status + ": " + errText.slice(0, 200));
      }

      const ctype = res.headers.get("content-type") || "";
      let full = "";
      if (ctype.indexOf("text/event-stream") !== -1 && res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        while (true) {
          const chunk = await reader.read();
          if (chunk.done) break;
          buf += decoder.decode(chunk.value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop() || "";
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.indexOf("data:") !== 0) continue;
            const data = line.slice(5).trim();
            if (!data || data === "[DONE]") continue;
            try {
              const j = JSON.parse(data);
              if (j.type === "meta" && j.session_id) {
                sessionId = j.session_id;
                localStorage.setItem(LS_SID, sessionId);
                var ac = activeChat();
                if (ac) ac.sessionId = sessionId;
                persistChats();
              }
              if (j.type === "delta" && j.text) {
                full += j.text;
                contentEl.innerHTML = formatMarkdown(full);
                scrollBottom();
              }
              if (j.type === "error") throw new Error(j.message || "stream error");
            } catch (e) {
              if (e.message && e.message !== "stream error" && !(e instanceof SyntaxError)) throw e;
            }
          }
        }
      } else {
        const j = await res.json();
        full = j.reply || "";
        if (j.session_id) {
          sessionId = j.session_id;
          localStorage.setItem(LS_SID, sessionId);
          var ac2 = activeChat();
          if (ac2) ac2.sessionId = sessionId;
        }
      }

      contentEl.parentElement.parentElement.classList.remove("typing");
      if (!full) throw new Error("Server tra ve rong. Kiem tra webapp dang chay?");
      contentEl.innerHTML = formatMarkdown(full);
      chat.messages.push({ role: "assistant", content: full });
      chat.updated = Date.now();
      persistChats();
      renderHistory();
      setStatus(true);
    } catch (err) {
      contentEl.parentElement.parentElement.classList.remove("typing");
      contentEl.innerHTML = formatMarkdown(
        "**Loi ket noi server**\n\n" +
          String(err.message || err) +
          "\n\nChu y:\n" +
          "1. Chay server: `python -m webapp.server` (port 7860)\n" +
          "2. Mo dung: http://127.0.0.1:7860/\n" +
          "3. User khong can API key"
      );
      setStatus(false);
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
    els.input.style.height = "auto";
    els.input.style.height = Math.min(els.input.scrollHeight, 180) + "px";
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

  els.btnPlus.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!busy) els.fileImage.click();
  });
  els.fileImage.addEventListener("change", () => {
    if (els.fileImage.files && els.fileImage.files.length) addFiles(els.fileImage.files);
    els.fileImage.value = "";
  });

  els.btnNew.addEventListener("click", newChat);
  if (els.btnLogout) els.btnLogout.addEventListener("click", logoutGoogle);
  if (els.btnOpenSidebar) els.btnOpenSidebar.addEventListener("click", openSidebar);
  if (els.btnCloseSidebar) els.btnCloseSidebar.addEventListener("click", closeSidebar);
  if (els.backdrop) els.backdrop.addEventListener("click", closeSidebar);

  if (els.tabLogin) els.tabLogin.addEventListener("click", function () { switchAuthTab("login"); });
  if (els.tabRegister) els.tabRegister.addEventListener("click", function () { switchAuthTab("register"); });
  if (els.formLogin) els.formLogin.addEventListener("submit", submitLogin);
  if (els.formRegister) els.formRegister.addEventListener("submit", submitRegister);
  if (els.btnSendCode) els.btnSendCode.addEventListener("click", sendRegisterCode);
  if (els.userChipBtn) els.userChipBtn.addEventListener("click", openLoginFromChip);
  if (els.userPill) els.userPill.addEventListener("click", openLoginFromChip);

  // Boot — email/Google gate then chats
  (async function boot() {
    await loadPublicConfig();
    try {
      const r = await fetch(apiBase() + "/api/config", { cache: "no-store" });
      if (r.ok) {
        serverConfig = Object.assign(serverConfig, await r.json());
      }
    } catch (e) {
      if (els.authHint) {
        els.authHint.textContent =
          "Khong ket noi server " + apiBase() + " — chay: python -m webapp.server";
      }
    }

    // Require login when server says so (email and/or Google)
    const needAuth = !!(
      serverConfig.auth_required ||
      serverConfig.google_auth_required
    );
    let ok = await restoreGoogleSession();
    if (!ok) {
      if (needAuth) {
        showGate("login");
        ok = false;
      } else {
        // Optional auth: still show login chip, allow browsing
        applyUserUi(null);
        showApp();
        ok = true;
      }
    }

    loadChats();
    activeId =
      localStorage.getItem(LS_ACTIVE) ||
      (chats[0] ? chats[0].id : null);
    if (activeId && !chats.find(function (c) { return c.id === activeId; })) {
      activeId = chats[0] ? chats[0].id : null;
    }
    var cur = activeChat();
    if (cur && cur.sessionId) {
      sessionId = cur.sessionId;
      localStorage.setItem(LS_SID, sessionId);
    }
    if (ok) {
      renderHistory();
      renderMessages();
      bindSuggestions();
      await pingServer();
      if (sessionId && isLoggedIn()) {
        try {
          const r = await fetch(
            apiBase() +
              "/api/chat/history?session_id=" +
              encodeURIComponent(sessionId),
            { headers: userHeaders(), cache: "no-store" }
          );
          if (r.ok) {
            const j = await r.json();
            if (
              j.messages &&
              j.messages.length &&
              cur &&
              (!cur.messages || !cur.messages.length)
            ) {
              cur.messages = j.messages.map(function (m) {
                return { role: m.role, content: m.content, images: [] };
              });
              persistChats();
              renderMessages();
            }
          }
        } catch (e) {
          /* offline ok */
        }
      }
    } else {
      renderGoogleButton();
    }
  })();
})();
