"""Pineapple Corp Command Center — unified FastAPI dashboard + Chainlit chatbot.

Run (single command):
    uvicorn dashboard:app --port 8050
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
ASSET_JSON = DATA_DIR / "asset_inventory.json"
CHAT_PATH = "/chat"

app = FastAPI(title="Pineapple Corp Command Center")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ---------------------------------------------------------------------------
# Mount Chainlit as a sub-app at /chat
# ---------------------------------------------------------------------------
from chainlit.utils import mount_chainlit  # noqa: E402

mount_chainlit(app=app, target=str(BASE_DIR / "app.py"), path=CHAT_PATH)


# ---------------------------------------------------------------------------
# Mappings for Figma-style display
# ---------------------------------------------------------------------------

CRITICALITY_TO_STATUS = {
    "critical": "Quarantined",
    "high": "Investigating",
    "medium": "Secure",
    "low": "Secure",
}

TYPE_TO_ICON = {
    "firewall": "shield",
    "server": "server",
    "switch": "network",
    "router": "router",
    "workstation": "monitor",
    "laptop": "laptop",
    "database": "database",
    "siem": "eye",
    "edr": "scan",
    "ids": "radar",
    "ndr": "activity",
    "proxy": "globe",
    "mfa": "key-round",
    "pam": "lock",
    "web_server": "globe",
    "file_server": "hard-drive",
    "email_server": "mail",
    "dns": "at-sign",
    "backup": "archive",
    "dr_site": "cloud",
    "nas": "hard-drive",
    "access_point": "wifi",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_assets() -> dict:
    """Load asset inventory JSON, return full payload (metadata + assets)."""
    if not ASSET_JSON.exists():
        return {"metadata": {}, "assets": []}
    with open(ASSET_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize_assets(assets: list[dict]) -> dict:
    """Build summary counts from asset list."""
    by_type: dict[str, int] = {}
    by_criticality: dict[str, int] = {}
    by_zone: dict[str, int] = {}

    for a in assets:
        t = a.get("type", "unknown")
        c = a.get("criticality", "unknown")
        z = a.get("network_zone", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        by_criticality[c] = by_criticality.get(c, 0) + 1
        by_zone[z] = by_zone.get(z, 0) + 1

    return {
        "total": len(assets),
        "by_type": by_type,
        "by_criticality": by_criticality,
        "by_zone": by_zone,
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = load_assets()
    assets = data.get("assets", [])
    metadata = data.get("metadata", {})
    summary = summarize_assets(assets)

    config = {
        "adapter_path": os.getenv("LORA_ADAPTER_PATH", "not set"),
        "max_seq_length": os.getenv("MAX_SEQ_LENGTH", "2048"),
        "max_new_tokens": os.getenv("MAX_NEW_TOKENS", "512"),
        "temperature": os.getenv("TEMPERATURE", "0.1"),
        "retrieval_top_k": os.getenv("RETRIEVAL_TOP_K", "4"),
        "attention_backend": os.getenv("ATTENTION_BACKEND", "auto"),
        "asset_connector": os.getenv("ASSET_CONNECTOR", "none"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "assets": assets,
        "metadata": metadata,
        "summary": summary,
        "chat_path": CHAT_PATH,
        "status_map": CRITICALITY_TO_STATUS,
        "type_icons": TYPE_TO_ICON,
        "config": config,
    })


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/assets")
async def api_assets():
    return JSONResponse(load_assets())


@app.post("/api/assets/refresh")
async def api_refresh_assets():
    """Run refresh_assets.py as a subprocess and return the result."""
    script = BASE_DIR / "scripts" / "refresh_assets.py"
    python = sys.executable
    try:
        result = subprocess.run(
            [python, str(script)],
            capture_output=True, text=True, timeout=30,
            cwd=str(BASE_DIR),
        )
        success = result.returncode == 0
        return JSONResponse({
            "success": success,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }, status_code=200 if success else 500)
    except subprocess.TimeoutExpired:
        return JSONResponse({"success": False, "error": "Refresh timed out (30s)"}, status_code=504)
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.get("/api/health")
async def api_health():
    """Lightweight health check (no model loading)."""
    data = load_assets()
    return JSONResponse({
        "status": "ok",
        "asset_count": len(data.get("assets", [])),
        "asset_inventory_exists": ASSET_JSON.exists(),
        "chat_path": CHAT_PATH,
    })
