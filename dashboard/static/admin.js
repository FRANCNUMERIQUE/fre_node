(() => {
  const tokenInput = document.getElementById("token");
  const saveTokenBtn = document.getElementById("saveToken");
  const clearTokenBtn = document.getElementById("clearToken");
  const refreshStatusBtn = document.getElementById("refreshStatus");
  const restartNodeBtn = document.getElementById("restartNode");
  const restartDashBtn = document.getElementById("restartDash");
  const runUpdateBtn = document.getElementById("runUpdate");
  const servicesStatus = document.getElementById("servicesStatus");
  const updateLog = document.getElementById("updateLog");
  const quickStatus = document.getElementById("quickStatus");
  const valName = document.getElementById("valName");
  const valPub = document.getElementById("valPub");
  const valPriv = document.getElementById("valPriv");
  const valStake = document.getElementById("valStake");
  const valStatus = document.getElementById("valStatus");

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
    alert("Token enregistré localement (localStorage).");
  };
  clearTokenBtn.onclick = () => {
    saveToken("");
    tokenInput.value = "";
  };

  const handleResponse = async (res) => {
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  };

  const refreshStatus = async () => {
    servicesStatus.textContent = "Chargement...";
    quickStatus.textContent = "Chargement...";
    try {
      const res = await fetch(`${apiBase}/admin/status`, { headers: headers() });
      const data = await handleResponse(res);
      servicesStatus.textContent = JSON.stringify(data.services, null, 2);
      quickStatus.textContent = JSON.stringify(data.node, null, 2);
    } catch (e) {
      servicesStatus.textContent = "Erreur: " + e.message;
    }
  };

  const restartService = async (service) => {
    servicesStatus.textContent = `Redémarrage ${service}...`;
    try {
      const res = await fetch(`${apiBase}/admin/service/restart`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ service })
      });
      const data = await handleResponse(res);
      servicesStatus.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      servicesStatus.textContent = "Erreur: " + e.message;
    }
  };

  const runUpdate = async () => {
    updateLog.textContent = "Mise à jour en cours...";
    try {
      const res = await fetch(`${apiBase}/admin/update`, {
        method: "POST",
        headers: headers()
      });
      const data = await handleResponse(res);
      updateLog.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      updateLog.textContent = "Erreur: " + e.message;
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
    } catch (e) {
      valStatus.textContent = "Erreur: " + e.message;
    }
  };

  refreshStatusBtn.onclick = refreshStatus;
  restartNodeBtn.onclick = () => restartService("fre_node");
  restartDashBtn.onclick = () => restartService("fre_dashboard");
  runUpdateBtn.onclick = runUpdate;
  const saveValidatorBtn = document.getElementById("saveValidator");
  saveValidatorBtn.onclick = saveValidator;

  refreshStatus();
})();
