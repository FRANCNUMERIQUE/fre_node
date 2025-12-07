# FRE Node — Point d'accès Wi‑Fi autonome

Ce dossier contient des exemples de configuration pour transformer un Raspberry Pi en hotspot local, accessible via `fre-node.local` (mDNS).

## 1) Paquets requis
```bash
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq avahi-daemon
# désactiver l’auto-démarrage, on l’activera via systemd
sudo systemctl disable hostapd dnsmasq
```

## 2) IP statique sur wlan0
`/etc/dhcpcd.conf` (exemple) :
```
interface wlan0
  static ip_address=192.168.50.1/24
  nohook wpa_supplicant
```
Redémarrer `dhcpcd` ou le Pi.

## 3) hostapd (point d’accès)
Copier et adapter `hotspot/hostapd.conf.example` vers `/etc/hostapd/hostapd.conf`, puis définir dans `/etc/default/hostapd` :
```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```
Modifiez `ssid`, `wpa_passphrase`, `country_code`, `channel` selon votre cas.

## 4) dnsmasq (DHCP + DNS local)
Sauvegarder l’original :
```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```
Placer `hotspot/dnsmasq.conf.example` dans `/etc/dnsmasq.conf`. Ajuster la plage DHCP si besoin.

## 5) mDNS (fre-node.local)
Avahi est installé par `avahi-daemon`. Optionnel : publier le service HTTP via `/etc/avahi/services/fre-node.service` :
```xml
<?xml version="1.0" standalone='no'?><!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">FRE Node</name>
  <service>
    <type>_http._tcp</type>
    <port>80</port>
  </service>
</service-group>
```

## 6) Services systemd
Activer au démarrage :
```bash
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl enable avahi-daemon
```
Si vous utilisez le portail dashboard sur le port 80, activez aussi `fre_portal.service` (fourni dans `system/`) après avoir ajusté les chemins :
```bash
sudo cp system/fre_portal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fre_portal.service
sudo systemctl start fre_portal.service
```

## 7) Accès utilisateur
- Connexion Wi‑Fi : SSID (ex.) `FRE_NODE_01`, mot de passe `frevalidator`.
- Navigateur : `http://fre-node.local` (mDNS) ou `http://192.168.50.1`.

## 8) Sécurité / personnalisation
- Changez le mot de passe Wi‑Fi.
- Ajustez `country_code`/`channel`.
- Option fallback : laisser wpa_supplicant pour se connecter à un Wi‑Fi connu et activer le hotspot seulement si aucun réseau n’est disponible.
