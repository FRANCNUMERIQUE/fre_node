(() => {
  const tokenInput = document.getElementById("token");
  const saveTokenBtn = document.getElementById("saveToken");
  const clearTokenBtn = document.getElementById("clearToken");
  const valName = document.getElementById("valName");
  const valPub = document.getElementById("valPub");
  const valPriv = document.getElementById("valPriv");
  const valStake = document.getElementById("valStake");
  const valStatus = document.getElementById("valStatus");
  const refreshStatusBtn = document.getElementById("refreshStatus");
  const quickStatus = document.getElementById("quickStatus");
  const restartNodeBtn = document.getElementById("restartNode");
  const restartDashBtn = document.getElementById("restartDash");
  const runUpdateBtn = document.getElementById("runUpdate");
  const actionStatus = document.getElementById("actionStatus");
  const logOutput = document.getElementById("logOutput");

  const loadToken = () => localStorage.getItem("fre_admin_token") || "";
  const saveToken = (t) => localStorage.setItem("fre_admin_token", t || "");
  const headers = () => {
    const h = { "Content-Type": "application/json" };
    const tok = loadToken();
    if (tok) h["X-Admin-Token"] = tok;
    return h;
  };

  tokenInput.value = loadToken();

  saveTokenBtn.onclick = () => {
    saveToken(tokenInput.value.trim());
    actionStatus.textContent = "Token enregistré.";
    maybeHideModal();
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

  restartNodeBtn.onclick = () => restartService("fre_node");
  restartDashBtn.onclick = () => restartService("fre_dashboard");
  runUpdateBtn.onclick = runUpdate;
  refreshStatusBtn.onclick = refreshStatus;
  document.getElementById("saveValidator").onclick = saveValidator;

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
    saveToken(modalInput.value.trim());
    tokenInput.value = loadToken();
    hideModal();
    refreshStatus();
  };
  modalCancel.onclick = () => hideModal();

  if (!loadToken()) {
    showModal();
  } else {
    refreshStatus();
  }
  // si token existe déjà, on a déjà lancé refreshStatus
})();
