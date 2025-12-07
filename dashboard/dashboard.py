from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import requests
import socket
from pathlib import Path


app = FastAPI(title="FRE Dashboard")

# ------------------------------
# Détection IP locale Raspberry
# ------------------------------
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

local_ip = get_local_ip()
node_api_url = f"http://{local_ip}:8500"

print("Node API URL ->", node_api_url)

# ------------------------------
# HTML + STATIC
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ============================================
#   🔥🔥🔥  ROUTES API (AJOUT MINIMAL)
# ============================================

@app.get("/api/node_status")
def node_status():
    try:
        r = requests.get(f"{node_api_url}/status", timeout=2)
        return r.json()
    except:
        return JSONResponse({"error": "Node offline"}, status_code=404)


@app.get("/api/block_latest")
def block_latest():
    try:
        r = requests.get(f"{node_api_url}/block/latest", timeout=2)
        return r.json()
    except:
        return JSONResponse({"error": "Node offline"}, status_code=404)


@app.get("/api/state")
def state():
    try:
        r = requests.get(f"{node_api_url}/state", timeout=2)
        return r.json()
    except:
        return JSONResponse({"error": "Node offline"}, status_code=404)


@app.get("/api/mempool")
def mempool():
    try:
        r = requests.get(f"{node_api_url}/mempool", timeout=2)
        return r.json()
    except:
        return JSONResponse({"error": "Node offline"}, status_code=404)


# ------------------------------
# Démarrage manuel (debug)
# ------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
