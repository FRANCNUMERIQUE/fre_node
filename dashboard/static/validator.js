(() => {
  const $ = (id) => document.getElementById(id);

  // DOM
  const tokenInput = $("token");
  const saveTokenBtn = $("saveToken");
  const clearTokenBtn = $("clearToken");
  const generateTokenBtn = $("generateAdminToken");
  const tokenModal = $("tokenModal");
  const tokenModalInfo = $("tokenModalInfo");
  const tokenModalInput = $("tokenModalInput");
  const tokenModalStatus = $("tokenModalStatus");
  const tokenModalSave = $("tokenModalSave");
  const tokenModalCancel = $("tokenModalCancel");

  const valName = $("valName");
  const valPub = $("valPub");
  const valPriv = $("valPriv");
  const valStake = $("valStake");
  const valStatus = $("valStatus");

  const generateKeysBtn = $("generateKeys");
  const regenerateKeysBtn = $("regenerateKeys");
  const saveValidatorBtn = $("saveValidator");

  const refreshStatusBtn = $("refreshStatus");
  const quickStatus = $("quickStatus");
  const restartNodeBtn = $("restartNode");
  const restartDashBtn = $("restartDash");
  const runUpdateBtn = $("runUpdate");
  const actionStatus = $("actionStatus");
  const logOutput = $("logOutput");

  const wifiSsid = $("wifiSsid");
  const wifiPass = $("wifiPass");
  const wifiStatus = $("wifiStatus");
  const saveWifiBtn = $("saveWifi");
  const applyWifiBtn = $("applyWifi");

  const tonAddr = $("tonAddr");
  const tonStatus = $("tonStatus");
  const saveTonBtn = $("saveTon");

  const rewardsBox = $("rewardsBox");

  // Token helpers
  const loadToken = () => localStorage.getItem("fre_validator_token") || "";
  const saveToken = (t) => localStorage.setItem("fre_validator_token", t || "");
  const headers = () => {
    const h = { "Content-Type": "application/json" };
    const tok = loadToken();
    if (tok) h["X-Admin-Token"] = tok;
    return h;
  };

  const handleResponse = async (res) => {
    const text = await res.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch (e) { data = text; }
    if (!res.ok) {
      const msg = (data && data.error) || (data && data.detail) || text || res.statusText;
      throw new Error(msg);
    }
    return data;
  };

  // Admin token flow
  const showModal = (needsGeneration = false) => {
    if (tokenModal) tokenModal.classList.remove("hidden");
    if (tokenModalInput) tokenModalInput.value = loadToken();
    if (tokenModalInfo) {
      tokenModalInfo.textContent = needsGeneration
        ? "Aucun token admin n'est encore defini. Generez-le pour deverrouiller le node."
        : "Collez le token admin (non partage).";
    }
    if (tokenModalStatus) tokenModalStatus.textContent = "";
    if (generateTokenBtn) generateTokenBtn.style.display = needsGeneration ? "inline-block" : "none";
  };

  const hideModal = () => {
    if (tokenModal) tokenModal.classList.add("hidden");
  };

  const fetchTokenStatus = async () => {
    try {
      const data = await handleResponse(await fetch(`${apiBase}/admin/token/status`));
      return !!data.set;
    } catch (e) {
      return false;
    }
  };

  const generateAdminToken = async () => {
    if (tokenModalStatus) tokenModalStatus.textContent = "Generation en cours...";
    try {
      const data = await handleResponse(await fetch(`${apiBase}/admin/token/generate`, { method: "POST" }));
      const tok = data.token || "";
      if (!tok) throw new Error("Token absent dans la reponse");
      saveToken(tok);
      if (tokenInput) tokenInput.value = tok;
      if (tokenModalInput) tokenModalInput.value = tok;
      if (tokenModalStatus) tokenModalStatus.textContent = "Token genere et enregistre localement.";
      hideModal();
      refreshStatus();
      loadProfile();
    } catch (e) {
      if (tokenModalStatus) tokenModalStatus.textContent = "Erreur: " + e.message;
    }
  };

  const ensureTokenFlow = async () => {
    const tokenSet = await fetchTokenStatus();
    const stored = loadToken();
    if (!tokenSet) {
      showModal(true);
      return;
    }
    if (!stored) {
      showModal(false);
      return;
    }
    if (tokenInput) tokenInput.value = stored;
    refreshStatus();
    loadProfile();
  };

  // Status/services
  const refreshStatus = async () => {
    if (!quickStatus) return;
    quickStatus.textContent = "Chargement...";
    try {
      const res = await fetch(`${apiBase}/admin/status`, { headers: headers() });
      const data = await handleResponse(res);
      quickStatus.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      quickStatus.textContent = "Erreur: " + e.message;
    }
  };

  // Restart services / update
  const restartService = async (service) => {
    if (!actionStatus) return;
    actionStatus.textContent = `Redemarrage ${service}...`;
    try {
      const res = await fetch(`${apiBase}/admin/service/restart`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ service })
      });
      const data = await handleResponse(res);
      actionStatus.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      actionStatus.textContent = "Erreur: " + e.message;
    }
  };

  const runUpdate = async () => {
    if (!logOutput) return;
    logOutput.textContent = "Mise a jour en cours...";
    try {
      const res = await fetch(`${apiBase}/admin/update`, { method: "POST", headers: headers() });
      const data = await handleResponse(res);
      logOutput.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      logOutput.textContent = "Erreur: " + e.message;
    }
  };

  // Validator save
  const saveValidator = async () => {
    if (!valStatus) return;
    valStatus.textContent = "Sauvegarde...";
    try {
      const res = await fetch(`${apiBase}/admin/validator`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          name: (valName?.value || "").trim(),
          public_key: (valPub?.value || "").trim(),
          private_key: (valPriv?.value || "").trim(),
          stake: parseInt(valStake?.value || "1", 10)
        })
      });
      const data = await handleResponse(res);
      valStatus.textContent = "OK";
      if (logOutput) logOutput.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      valStatus.textContent = "Erreur: " + e.message;
    }
  };

  // Load profile
  const loadProfile = async () => {
    if (!valStatus) return;
    valStatus.textContent = "Chargement...";
    try {
      const res = await fetch(`${apiBase}/admin/validator/info`, { headers: headers() });
      const data = await handleResponse(res);
      if (data.validator) {
        if (valName) valName.value = data.validator.name || "";
        if (valPub) valPub.value = data.validator.pubkey || data.validator.public_key || "";
        if (valStake) valStake.value = data.validator.stake || 1;
      }
      if (data.private_key && valPriv) {
        valPriv.value = data.private_key;
      }
      if (rewardsBox) rewardsBox.textContent = JSON.stringify(data.rewards || {}, null, 2);
      if (quickStatus) quickStatus.textContent = JSON.stringify(data.validator || {}, null, 2);
      valStatus.textContent = "Profil charge.";
    } catch (e) {
      valStatus.textContent = "Erreur: " + e.message;
    }
  };

  // Generate keys (local fallback to backend)
  const generateKeys = async () => {
    if (!valStatus) return;
    valStatus.textContent = "Generation en cours...";
    const b64url = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

    const generateLocal = async () => {
      if (!window.crypto || !window.crypto.subtle) throw new Error("WebCrypto indisponible");
      const keyPair = await window.crypto.subtle.generateKey(
        { name: "Ed25519" },
        true,
        ["sign", "verify"]
      );
      const pub = await window.crypto.subtle.exportKey("raw", keyPair.publicKey);
      const priv = await window.crypto.subtle.exportKey("pkcs8", keyPair.privateKey);
      return { pub: b64url(pub), priv: b64url(priv) };
    };

    const generateRemote = async () => {
      const res = await fetch(`${apiBase}/admin/validator/generate`, { headers: headers() });
      const data = await handleResponse(res);
      if (!data.public_key || !data.private_key) throw new Error("Reponse invalide");
      return { pub: data.public_key, priv: data.private_key };
    };

    try {
      let keys;
      try {
        keys = await generateLocal();
        valStatus.textContent = "Cles generees localement.";
      } catch (e) {
        keys = await generateRemote();
        valStatus.textContent = "Cles generees cote noeud.";
      }
      if (valPub) valPub.value = keys.pub;
      if (valPriv) valPriv.value = keys.priv;
    } catch (e) {
      valStatus.textContent = "Erreur generation: " + e.message;
    }
  };

  const regenerateKeys = async () => {
    const warning = "Re-generer va invalider les cles actuelles. Sauvegardez-les avant de continuer. Continuer ?";
    if (!window.confirm(warning)) {
      if (valStatus) valStatus.textContent = "Re-generation annulee.";
      return;
    }
    await generateKeys();
  };

  // Wi-Fi domestique (stockage local + apply)
  const loadWifi = () => {
    if (wifiSsid) wifiSsid.value = localStorage.getItem("fre_wifi_ssid") || "";
    if (wifiPass) wifiPass.value = localStorage.getItem("fre_wifi_pass") || "";
  };
  const saveWifiLocal = () => {
    if (wifiSsid) localStorage.setItem("fre_wifi_ssid", wifiSsid.value.trim());
    if (wifiPass) localStorage.setItem("fre_wifi_pass", wifiPass.value);
    if (wifiStatus) wifiStatus.textContent = "Wi-Fi enregistre localement.";
  };
  const applyWifi = async () => {
    if (!wifiStatus) return;
    wifiStatus.textContent = "Application en cours... (le hotspot peut s'arreter)";
    try {
      const res = await fetch(`${apiBase}/admin/wifi`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          ssid: (wifiSsid?.value || "").trim(),
          password: wifiPass?.value || "",
          country: "FR"
        })
      });
      const data = await handleResponse(res);
      wifiStatus.textContent = data.message || "Wi-Fi applique. Le noeud bascule en client.";
    } catch (e) {
      wifiStatus.textContent = "Erreur: " + e.message;
    }
  };

  // Wallet TON (stockage local)
  const loadTon = () => {
    if (tonAddr) tonAddr.value = localStorage.getItem("fre_ton_addr") || "";
  };
  const saveTonLocal = () => {
    if (tonAddr) localStorage.setItem("fre_ton_addr", tonAddr.value.trim());
    if (tonStatus) tonStatus.textContent = "Adresse TON enregistree localement.";
  };

  // Bind handlers
  if (saveTokenBtn) saveTokenBtn.onclick = () => {
    const t = tokenInput?.value.trim() || "";
    if (!t) {
      if (actionStatus) actionStatus.textContent = "Token manquant.";
      return;
    }
    saveToken(t);
    if (actionStatus) actionStatus.textContent = "Token enregistre.";
    hideModal();
    refreshStatus();
    loadProfile();
  };

  if (clearTokenBtn) clearTokenBtn.onclick = () => {
    saveToken("");
    if (tokenInput) tokenInput.value = "";
    if (actionStatus) actionStatus.textContent = "Token efface.";
  };

  if (tokenModalSave) tokenModalSave.onclick = () => {
    const t = tokenModalInput?.value.trim() || "";
    if (!t) {
      if (tokenModalStatus) tokenModalStatus.textContent = "Token manquant.";
      return;
    }
    saveToken(t);
    if (tokenInput) tokenInput.value = t;
    if (tokenModalStatus) tokenModalStatus.textContent = "Token enregistre localement.";
    hideModal();
    refreshStatus();
    loadProfile();
  };

  if (tokenModalCancel) tokenModalCancel.onclick = hideModal;
  if (generateTokenBtn) generateTokenBtn.onclick = generateAdminToken;

  if (refreshStatusBtn) refreshStatusBtn.onclick = refreshStatus;
  if (restartNodeBtn) restartNodeBtn.onclick = () => restartService("fre_node");
  if (restartDashBtn) restartDashBtn.onclick = () => restartService("fre_dashboard");
  if (runUpdateBtn) runUpdateBtn.onclick = runUpdate;

  if (saveValidatorBtn) saveValidatorBtn.onclick = saveValidator;
  if (generateKeysBtn) generateKeysBtn.onclick = generateKeys;
  if (regenerateKeysBtn) regenerateKeysBtn.onclick = regenerateKeys;

  if (saveWifiBtn) saveWifiBtn.onclick = saveWifiLocal;
  if (applyWifiBtn) applyWifiBtn.onclick = applyWifi;

  if (saveTonBtn) saveTonBtn.onclick = saveTonLocal;

  // Init
  loadWifi();
  loadTon();
  if (tokenInput) tokenInput.value = loadToken();
  ensureTokenFlow();
})();
