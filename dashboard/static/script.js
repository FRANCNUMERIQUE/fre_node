// ===============================
//   SCRIPT DASHBOARD OFFICIEL
//   FRE NODE 2025 — Layer 2
// ===============================

// Fonction générique qui récupère du JSON depuis le backend dashboard
async function fetchJSON(endpoint) {
    try {
        let response = await fetch(endpoint, { cache: "no-store" });
        if (!response.ok) {
            return { error: "HTTP Error", code: response.status };
        }
        return await response.json();
    } catch (e) {
        return { error: "API unreachable", code: 404 };
    }
}

// Fonction principale exécutée toutes les 2 secondes
async function refresh() {

    // Récupération des données depuis le backend Python
    let status = await fetchJSON("/api/node_status");
    let block  = await fetchJSON("/api/block_latest");
    let state  = await fetchJSON("/api/state");
    let mempool = await fetchJSON("/api/mempool");

    // ======================
    //   STATUS SECTION
    // ======================
    document.getElementById("node").textContent =
        status.node ?? "-";

    document.getElementById("blocks").textContent =
        status.blocks ?? "-";

    document.getElementById("mempool").textContent =
        status.mempool ?? "-";

    document.getElementById("cpu").textContent =
        status.system?.cpu ?? "-";

    document.getElementById("ram").textContent =
        status.system?.ram ?? "-";

    // ======================
    //   LAST BLOCK SECTION
    // ======================
    document.getElementById("latest_block").textContent =
        JSON.stringify(block, null, 2);

    // ======================
    //   BALANCES LEDGER
    // ======================
    document.getElementById("balances").textContent =
        JSON.stringify(state.balances ?? {}, null, 2);

    // ======================
    //   MEMPOOL LIST
    // ======================
    document.getElementById("mempool_list").textContent =
        JSON.stringify(mempool ?? [], null, 2);
}

// Rafraîchissement toutes les 2 secondes
setInterval(refresh, 2000);

// Exécution immédiate au chargement
refresh();
