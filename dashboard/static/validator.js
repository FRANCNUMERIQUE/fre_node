(() => {
  // DOM references
  const tokenInput = document.getElementById("token");
  const saveTokenBtn = document.getElementById("saveToken");
  const clearTokenBtn = document.getElementById("clearToken");

  const valName = document.getElementById("valName");
  const valPub = document.getElementById("valPub");
  const valPriv = document.getElementById("valPriv");
  const valStake = document.getElementById("valStake");
  const valStatus = document.getElementById("valStatus");

  const generateKeysBtn = document.getElementById("generateKeys");
  const regenerateKeysBtn = document.getElementById("regenerateKeys");
  const saveValidatorBtn = document.getElementById("saveValidator");

  const refreshStatusBtn = document.getElementById("refreshStatus");
  const quickStatus = document.getElementById("quickStatus");
  const restartNodeBtn = document.getElementById("restartNode");
  const restartDashBtn = document.getElementById("restartDash");
  const runUpdateBtn = document.getElementById("runUpdate");
  const actionStatus = document.getElementById("actionStatus");
  const logOutput = document.getElementById("logOutput");

  const wifiSsid = document.getElementById("wifiSsid");
  const wifiPass = document.getElementById("wifiPass");
  const wifiStatus = document.getElementById("wifiStatus");
  const saveWifiBtn = document.getElementById("saveWifi");
  const applyWifiBtn = document.getElementById("applyWifi");

  const tonAddr = document.getElementById("tonAddr");
  const tonStatus = document.getElementById("tonStatus");
  const saveTonBtn = document.getElementById("saveTon");

  const rewardsBox = document.getElementById("rewardsBox");

  // Token storage
  const loadToken = () => localStorage.getItem("fre_validator_token") || "";
  const saveToken = (t) => localStorage.setItem("fre_validator_token", t || "");
  const headers = () => {
    const h = { "Content-Type": "application/json" };
    const tok = loadToken();
    if (tok) h["X-Admin-Token"] = tok;
    return h;
  };

  // Helpers
  const handleResponse = async (res) => {
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
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
    actionStatus.textContent = `Redémarrage ${service}...`;
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
    logOutput.textContent = "Mise à jour en cours...";
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
      valStatus.textContent = "Profil chargé.";
    } catch (e) {
      valStatus.textContent = "Erreur: " + e.message;
    }
  };

  // Generate keys (local fallback to backend)
  const generateKeys = async () => {
    if (!valStatus) return;
    valStatus.textContent = "Génération en cours...";
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
      if (!data.public_key || !data.private_key) throw new Error("Réponse invalide");
      return { pub: data.public_key, priv: data.private_key };
    };

    try {
      let keys;
      try {
        keys = await generateLocal();
        valStatus.textContent = "Clés générées localement.";
      } catch (e) {
        keys = await generateRemote();
        valStatus.textContent = "Clés générées côté nœud.";
      }
      if (valPub) valPub.value = keys.pub;
      if (valPriv) valPriv.value = keys.priv;
    } catch (e) {
      valStatus.textContent = "Erreur génération: " + e.message;
    }
  };

  const regenerateKeys = async () => {
    const warning = "Re-générer va invalider les clés actuelles. Sauvegardez-les avant de continuer. Continuer ?";
    if (!window.confirm(warning)) {
      if (valStatus) valStatus.textContent = "Re-génération annulée.";
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
    if (wifiStatus) wifiStatus.textContent = "Wi‑Fi enregistré localement.";
  };
  const applyWifi = async () => {
    if (!wifiStatus) return;
    wifiStatus.textContent = "Application en cours... (le hotspot peut s'arrêter)";
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
      wifiStatus.textContent = data.message || "Wi‑Fi appliqué. Le nœud bascule en client.";
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
    if (tonStatus) tonStatus.textContent = "Adresse TON enregistrée localement.";
  };

  // Modal token
  const modal = document.getElementById("tokenModal");
  const modalInput = document.getElementById("tokenModalInput");
  const modalSave = document.getElementById("tokenModalSave");
  const modalCancel = document.getElementById("tokenModalCancel");

  const showModal = () => {
    if (modal) modal.classList.remove("hidden");
    if (modalInput) modalInput.value = loadToken();
  };
  const hideModal = () => {
    if (modal) modal.classList.add("hidden");
  };

  // Bind handlers
  if (saveTokenBtn) saveTokenBtn.onclick = () => {
    const t = tokenInput?.value.trim() || "";
    if (!t) {
      if (actionStatus) actionStatus.textContent = "Token manquant.";
      return;
    }
    saveToken(t);
    if (actionStatus) actionStatus.textContent = "Token enregistré.";
    hideModal();
    refreshStatus();
  };
  if (clearTokenBtn) clearTokenBtn.onclick = () => {
    saveToken("");
    if (tokenInput) tokenInput.value = "";
    if (actionStatus) actionStatus.textContent = "Token effacé.";
  };
  if (modalSave) modalSave.onclick = () => {
    const t = modalInput?.value.trim() || "";
    if (!t) {
      if (actionStatus) actionStatus.textContent = "Token manquant.";
      return;
    }
    saveToken(t);
    if (tokenInput) tokenInput.value = t;
    hideModal();
    refreshStatus();
  };
  if (modalCancel) modalCancel.onclick = hideModal;

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
  if (!loadToken()) {
    showModal();
  } else {
    refreshStatus();
  }
})();
