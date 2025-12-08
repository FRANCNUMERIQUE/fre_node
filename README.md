FRE Node
========

Nœud FRE minimal (démo/dev) : API FastAPI, consensus PoA simplifié, dashboard FastAPI/Jinja2, hotspot Wi‑Fi intégré.

Prérequis
---------
- Python 3.10+
- systemd (fre_node.service, fre_dashboard.service, fre_portal.service optionnel)
- git

Installation rapide
-------------------
1) Cloner :
   - `git clone https://github.com/FRANCNUMERIQUE/fre_node.git`
   - `cd fre_node`
2) Installer services + hotspot :
   - `bash update/install_update.sh`
   (crée le venv, installe dépendances, active fre_node, fre_dashboard, hotspot hostapd/dnsmasq, NAT, wpa_supplicant@wlan0_sta)

Points d’accès / services
-------------------------
- Hotspot : SSID `FRE_NODE_01`, mot de passe `frevalidator`, IP AP `192.168.50.1/24`
- Dashboard : http://192.168.50.1:80 (fre_portal) ou http://<ip>:8080
- API : http://<ip>:8500
- Portal : `fre_portal.service` bind sur port 80 si présent

Admin token
-----------
- Un token admin est requis pour les actions sensibles (profil validateur, redémarrage, update).
- Génération via la page `/validator` (modal). Token stocké localement côté navigateur.
- Token persistant dans `fre_node/db/admin_token.json` (ou env `FRE_ADMIN_TOKEN`).

Profil validateur (UI)
----------------------
- Page : http://192.168.50.1/validator (ou /validator sur l’IP LAN).
- Sections : token admin, génération/enregistrement des clés, statut services, Wi‑Fi domestique (stockage local), wallet TON (stockage local), commandes principales (restart node/dashboard, update), journal.
- Génération de clés : WebCrypto côté navigateur (fallback backend).

Mode double AP + client (wlan0 + wlan0_sta)
-------------------------------------------
- AP : hostapd/dnsmasq sur wlan0 (192.168.50.1/24).
- Client : interface virtuelle `wlan0_sta` (wpa_supplicant + dhclient) pour rejoindre le Wi‑Fi domestique ; NAT via `fre_nat.service`.
- Config domestique : éditer `/etc/wpa_supplicant/wpa_supplicant-wlan0_sta.conf` (copié depuis `hotspot/wpa_supplicant-wlan0_sta.conf.example`) puis `systemctl restart wpa_supplicant@wlan0_sta.service dhclient-wlan0_sta.service`.

Diagnostic
----------
- `bash diagnose.sh` : vérifie services, API, blockchain, ledger, mempool, port 8500, dashboard (HTTP).
- Statut services : `sudo systemctl status fre_node fre_dashboard hostapd dnsmasq wpa_supplicant@wlan0_sta fre_nat dhclient-wlan0_sta`.

Transactions de test (dev)
--------------------------
- `FRE_DEV_MODE=true` (défaut) permet des TX de test. Nonce initial = 0.
- Format `tx_v1` :
  ```json
  {
    "version": "tx_v1",
    "type": "transfer",
    "chain_id": "fre-local",
    "timestamp": 1234567890,
    "from": "<address>",
    "to": "<address>",
    "amount": 10,
    "fee": 1,
    "nonce": 0,
    "pubkey": "<base64url ed25519>",
    "signature": "<base64url>"
  }
  ```
- Exemple (signature factice) :
  `curl -X POST http://127.0.0.1:8500/tx -H "Content-Type: application/json" -d '{"version":"tx_v1","type":"transfer","chain_id":"fre-local","timestamp":1700000000,"from":"alice","to":"bob","amount":10,"fee":1,"nonce":0,"pubkey":"test","signature":"test"}'`
- Bloc produit toutes les 5 s si la mempool n’est pas vide.

Wallet helper
-------------
- `fre_node/wallet.py` pour générer/signer une TX.
- Exemple :
  ```python
  from fre_node.wallet import Wallet
  w = Wallet.create(); w.save("wallet.json")
  tx = w.create_tx(to="dest_address", amount=10, nonce=0)
  ```

Mises à jour automatiques
-------------------------
- `update/install_update.sh` installe un cron à 02:00 UTC → `update/update_node.sh` (git pull, pip install, restart, backup léger).

Mempool (pro)
-------------
- Persistance disque (`db/mempool.json`), TTL 10 min, anti-duplication.
- Priorité par `fee` décroissant puis ancienneté.
- Taille max configurable (`MEMPOOL_MAX_SIZE`).
