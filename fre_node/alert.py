import logging
import requests
from .config import DISCORD_WEBHOOK

log = logging.getLogger("fre_alert")

def send_discord(message: str) -> bool:
    if not DISCORD_WEBHOOK:
        log.debug("DISCORD_WEBHOOK non défini, pas d'envoi")
        return False
    payload = {"content": message}
    try:
        resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        if resp.status_code in (200, 204):
            return True
        log.warning("Discord webhook échec: %s %s", resp.status_code, resp.text[:200])
    except Exception as e:
        log.warning("Discord webhook exception: %s", e)
    return False
