(() => {
  const tokenInput = document.getElementById("token");
  const saveTokenBtn = document.getElementById("saveToken");
  const clearTokenBtn = document.getElementById("clearToken");
  const valName = document.getElementById("valName");
  const valPub = document.getElementById("valPub");
  const valPriv = document.getElementById("valPriv");
  const valStake = document.getElementById("valStake");
  const valStatus = document.getElementById("valStatus");
  const generateKeysBtn = document.getElementById("generateKeys");
  const loadProfileBtn = document.getElementById("loadProfile");
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

  const loadToken = () => localStorage.getItem("fre_validator_token") || "";
  const saveToken = (t) => localStorage.setItem("fre_validator_token", t || "");
  const headers = () => {
    const h = { "Content-Type": "application/json" };
    const tok = loadToken();
    if (tok) h["X-Admin-Token"] = tok;
    return h;
  };

  tokenInput.value = loadToken();

  saveTokenBtn.onclick = () => {
    const t = tokenInput.value.trim();
    if (!t) {
      actionStatus.textContent = "Token manquant.";
      return;
    }
    saveToken(t);
    actionStatus.textContent = "Token enregistré.";
    maybeHideModal();
    refreshStatus();
  };
  clearTokenBtn.onclick = () => {
    saveToken("");
    tokenInput.value = "";
    actionStatus.textContent = "Token effacé.";
  };

  const handleResponse = async (res) => {
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  };

  const refreshStatus = async () => {
    quickStatus.textContent = "Chargement...";
    try {
      const res = await fetch(`${apiBase}/admin/status`, { headers: headers() });
      const data = await handleResponse(res);
      quickStatus.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      quickStatus.textContent = "Erreur: " + e.message;
    }
  };

  const restartService = async (service) => {
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
    logOutput.textContent = "Mise à jour en cours...";
    try {
      const res = await fetch(`${apiBase}/admin/update`, { method: "POST", headers: headers() });
      const data = await handleResponse(res);
      logOutput.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      logOutput.textContent = "Erreur: " + e.message;
    }
  };

  const saveValidator = async () => {
    valStatus.textContent = "Sauvegarde...";
    try {
      const res = await fetch(`${apiBase}/admin/validator`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          name: valName.value.trim(),
          public_key: valPub.value.trim(),
          private_key: valPriv.value.trim(),
          stake: parseInt(valStake.value || "1", 10)
        })
      });
      const data = await handleResponse(res);
      valStatus.textContent = "OK";
      logOutput.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      valStatus.textContent = "Erreur: " + e.message;
    }
  };

  const loadProfile = async () => {
    valStatus.textContent = "Chargement...";
    try {
      const res = await fetch(`${apiBase}/admin/validator/info`, { headers: headers() });
      const data = await handleResponse(res);
      if (data.validator) {
        valName.value = data.validator.name || "";
        valPub.value = data.validator.pubkey || data.validator.public_key || "";
        valStake.value = data.validator.stake || 1;
      }
      if (data.private_key) {
        valPriv.value = data.private_key;
      }
      rewardsBox.textContent = JSON.stringify(data.rewards || {}, null, 2);
      quickStatus.textContent = JSON.stringify(data.validator || {}, null, 2);
      valStatus.textContent = "Profil chargé.";
    } catch (e) {
      valStatus.textContent = "Erreur: " + e.message;
    }
  };

  restartNodeBtn.onclick = () => restartService("fre_node");
  restartDashBtn.onclick = () => restartService("fre_dashboard");
  runUpdateBtn.onclick = runUpdate;
  refreshStatusBtn.onclick = refreshStatus;
  document.getElementById("saveValidator").onclick = saveValidator;
  loadProfileBtn.onclick = loadProfile;
  generateKeysBtn.onclick = async () => {
    valStatus.textContent = "Génération en cours...";
    try {
      if (!window.crypto || !window.crypto.subtle) throw new Error("WebCrypto indisponible");
      const keyPair = await window.crypto.subtle.generateKey(
        { name: "Ed25519" },
        true,
        ["sign", "verify"]
      );
      const pub = await window.crypto.subtle.exportKey("raw", keyPair.publicKey);
      const priv = await window.crypto.subtle.exportKey("pkcs8", keyPair.privateKey);
      const b64url = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
      valPub.value = b64url(pub);
      valPriv.value = b64url(priv);
      valStatus.textContent = "Clés générées (local, non envoyées).";
    } catch (e) {
      valStatus.textContent = "Erreur génération: " + e.message;
    }
  };

  // Wi-Fi domestique (stockage local)
  const loadWifi = () => {
    wifiSsid.value = localStorage.getItem("fre_wifi_ssid") || "";
    wifiPass.value = localStorage.getItem("fre_wifi_pass") || "";
  };
  saveWifiBtn.onclick = () => {
    localStorage.setItem("fre_wifi_ssid", wifiSsid.value.trim());
    localStorage.setItem("fre_wifi_pass", wifiPass.value);
    wifiStatus.textContent = "Wi‑Fi enregistré localement.";
  };

  applyWifiBtn.onclick = async () => {
    wifiStatus.textContent = "Application en cours... (le hotspot peut s'arrêter)";
    try {
      const res = await fetch(`${apiBase}/admin/wifi`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          ssid: wifiSsid.value.trim(),
          password: wifiPass.value,
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
    tonAddr.value = localStorage.getItem("fre_ton_addr") || "";
  };
  saveTonBtn.onclick = () => {
    localStorage.setItem("fre_ton_addr", tonAddr.value.trim());
    tonStatus.textContent = "Adresse TON enregistrée localement.";
  };

  // Modal token
  const modal = document.getElementById("tokenModal");
  const modalInput = document.getElementById("tokenModalInput");
  const modalSave = document.getElementById("tokenModalSave");
  const modalCancel = document.getElementById("tokenModalCancel");

  const showModal = () => {
    modal.classList.remove("hidden");
    modalInput.value = loadToken();
  };
  const hideModal = () => modal.classList.add("hidden");
  const maybeHideModal = () => {
    if (loadToken()) hideModal();
  };

  modalSave.onclick = () => {
    const t = modalInput.value.trim();
    if (!t) {
      actionStatus.textContent = "Token manquant.";
      return;
    }
    saveToken(t);
    tokenInput.value = loadToken();
    hideModal();
    refreshStatus();
  };
  modalCancel.onclick = () => hideModal();

  // Chargement des données locales
  loadWifi();
  loadTon();

  if (!loadToken()) {
    showModal();
  } else {
    refreshStatus();
  }
})();
