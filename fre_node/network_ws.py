import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List

import websockets

from .config import P2P_PORT, PEERS_FILE, P2P_PRIVKEY_ENV, P2P_BAN_THRESHOLD
from .utils import load_signing_key, sign_message, verify_signature_raw
from .validator_set import load_validators


def load_peers() -> List[str]:
    path = Path(PEERS_FILE)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return [p for p in data if isinstance(p, str)]
    except Exception:
        return []
    return []


class P2PNode:
    """
    WebSocket P2P minimal :
    - messages JSON signés (Ed25519)
    - HELLO, BLOCK, TX, REQUEST_BLOCKS, REQUEST_HEADERS
    - ban score simple sur messages invalides
    """

    def __init__(self, handler_callback):
        self.handler_callback = handler_callback
        self.peers = set(load_peers())
        self.ban_score: Dict[str, int] = {}
        self.validators = load_validators()
        self.signing_key = None
        self.pubkey_b64 = None
        if P2P_PRIVKEY_ENV:
            try:
                self.signing_key = load_signing_key(P2P_PRIVKEY_ENV)
                self.pubkey_b64 = self.signing_key.verify_key.encode().hex()
            except Exception:
                self.signing_key = None

    async def start_server(self):
        if not self.signing_key:
            print("[P2P] No private key set, P2P disabled")
            return
        async with websockets.serve(self._handle_conn, "0.0.0.0", P2P_PORT):
            print(f"[P2P] WebSocket server on {P2P_PORT}")
            await asyncio.Future()  # run forever

    async def connect_peers(self):
        if not self.signing_key:
            return
        for peer in list(self.peers):
            try:
                async with websockets.connect(f"ws://{peer}:{P2P_PORT}") as ws:
                    await self._send_hello(ws)
            except Exception:
                continue

    async def _handle_conn(self, websocket, path):
        try:
            async for raw in websocket:
                await self._process_message(raw, websocket)
        except Exception:
            return

    async def _process_message(self, raw: str, websocket):
        try:
            msg = json.loads(raw)
        except Exception:
            return
        if not self._validate_message(msg):
            sender = self._sender_from_msg(msg)
            self._inc_ban(sender)
            return
        # dispatch to handler
        self.handler_callback(msg)

        # respond to requests
        if msg.get("type") == "HELLO":
            await self._send_hello(websocket)

    def _sender_from_msg(self, msg: dict):
        return msg.get("from", "")

    def _inc_ban(self, sender: str):
        if not sender:
            return
        self.ban_score[sender] = self.ban_score.get(sender, 0) + 1
        if self.ban_score[sender] >= P2P_BAN_THRESHOLD:
            print(f"[P2P] Banned {sender}")

    def _validate_message(self, msg: dict) -> bool:
        required = {"type", "payload", "ts", "from", "sig"}
        if not all(k in msg for k in required):
            return False
        sender = msg["from"]
        sig = msg["sig"]
        payload = {
            "type": msg["type"],
            "payload": msg["payload"],
            "ts": msg["ts"],
            "from": sender,
        }
        try:
            raw = json.dumps(payload, sort_keys=True).encode()
            return verify_signature_raw(sender, raw, sig)
        except Exception:
            return False

    async def _send_hello(self, websocket):
        msg = self._build_message("HELLO", {"node": self.pubkey_b64, "ts": int(time.time())})
        await websocket.send(json.dumps(msg))

    def _build_message(self, msg_type: str, payload: dict) -> dict:
        if not self.signing_key:
            raise RuntimeError("P2P signing key missing")
        base = {
            "type": msg_type,
            "payload": payload,
            "ts": int(time.time()),
            "from": self.pubkey_b64,
        }
        raw = json.dumps(base, sort_keys=True).encode()
        sig = sign_message(self.signing_key, raw)
        base["sig"] = sig
        return base

    async def broadcast(self, msg_type: str, payload: dict):
        if not self.signing_key:
            return
        msg = self._build_message(msg_type, payload)
        for peer in list(self.peers):
            try:
                async with websockets.connect(f"ws://{peer}:{P2P_PORT}") as ws:
                    await ws.send(json.dumps(msg))
            except Exception:
                continue

    # Convenience wrappers
    async def broadcast_block(self, block: dict):
        await self.broadcast("BLOCK", block)

    async def broadcast_tx(self, tx: dict):
        await self.broadcast("TX", tx)
