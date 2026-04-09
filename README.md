# AI-Driven Incident Response with RAG

An applied security AI project for generating incident response playbooks that are grounded in retrieved documentation and organization-specific asset context.

The repo combines three tracks in one place:

- a public-facing command center dashboard for demonstrations,
- a local RAG + LoRA backend that generates IR playbooks,
- and selected data-preparation scripts that support the training workflow.

> [!IMPORTANT]
> The public dashboard is live at **https://pineapple-corp.vercel.app**.  
> The full AI assistant is not permanently hosted there. During demos, the dashboard connects to a local GPU-backed backend through a tunnel. Outside demo sessions, visitors may see the dashboard in "AI Chat Offline" mode.

## Quick links

- Live dashboard: https://pineapple-corp.vercel.app
- Local backend app: [`RAG-Chatbot/`](./RAG-Chatbot/)
- Public static frontend: [`vercel-dashboard/`](./vercel-dashboard/)
- Data pipeline scripts: [`helper_scripts/`](./helper_scripts/)

## Project snapshot

| Area | Details |
| --- | --- |
| Focus | Incident response playbook generation with RAG |
| Core model path | Local LoRA adapter loaded with Unsloth |
| Retrieval stack | LlamaIndex + ChromaDB |
| UI surfaces | FastAPI dashboard + Chainlit chat + Vercel static dashboard |
| Asset context | Mock inventory today, connector-based refresh pipeline in place |
| Current maturity | Research / demo prototype, not production IR automation |

Pineapple Corp is a fictional demo environment used to showcase the workflow with realistic but sample infrastructure data.

## Why this project exists

Traditional playbooks are static. Real incidents are not.

This project explores a more adaptive workflow: retrieve relevant IR knowledge at inference time, combine it with an organization's asset inventory, and generate playbooks that reference actual systems, tools, zones, and roles instead of only generic guidance.

The goal is not "chatbot for cybersecurity." The goal is a system that can answer prompts like:

- "Generate a ransomware playbook for the file server in the datacenter."
- "What should we do first if lateral movement is suspected via SMB?"
- "Which assets are most relevant if this alert involves the domain controller and Splunk?"

## What the system does

- Generates incident response playbooks for scenarios such as ransomware, phishing, malware, data breach, credential abuse, and related IR cases.
- Uses retrieval to ground answers in local documents instead of relying only on model priors.
- Enriches responses with asset inventory context so output can reference hostnames, IPs, network zones, and security controls.
- Exposes the backend through a local FastAPI dashboard and embedded Chainlit chat interface.
- Ships a separate static Vercel dashboard for public demos and portfolio visibility.
- Includes the application code plus selected scripts used to support the retraining pipeline.

## Architecture

```text
User
  |
  +--> Public demo dashboard (Vercel)
  |       vercel-dashboard/public
  |       |
  |       +--> /api/config returns CHAT_BACKEND
  |       +--> iframe loads /chat from tunneled backend when available
  |
  +--> Local full-stack demo
          RAG-Chatbot/dashboard.py
              |
              +--> FastAPI dashboard
              +--> Chainlit mounted at /chat
              +--> app.py loads LoRA adapter with Unsloth
              +--> rag_index.py retrieves docs from ChromaDB
              +--> scripts/refresh_assets.py writes asset JSON + Markdown
```

## Repository map

```text
.
|-- README.md
|-- RAG-Chatbot/
|-- helper_scripts/
|-- vercel-dashboard/
`-- .gitignore
```

### Key directories

- [`RAG-Chatbot/`](./RAG-Chatbot/)  
  Main backend application. Contains the FastAPI dashboard, Chainlit app, retrieval pipeline, connectors, templates, and scripts for rebuilding the index and refreshing assets.

- [`vercel-dashboard/`](./vercel-dashboard/)  
  Static public dashboard deployed to Vercel. This is the cleanest entry point for external visitors and recruiters.

- [`helper_scripts/`](./helper_scripts/)  
  Selected data transformation and dataset-preparation scripts used to build the incident-response corpus.

## Main components

### 1. Public dashboard

The public dashboard is the portfolio-facing surface of the project.

- Location: [`vercel-dashboard/`](./vercel-dashboard/)
- Live URL: https://pineapple-corp.vercel.app
- Function: present a polished command center UI with asset inventory, incident widgets, and an embedded AI chat panel when a backend is available
- Backend integration: reads `CHAT_BACKEND` from a small serverless endpoint in [`vercel-dashboard/api/config.js`](./vercel-dashboard/api/config.js)

Important limitation: the Vercel deployment is intentionally lightweight. It does not host the model itself.

### 2. Local RAG + LoRA backend

The backend lives in [`RAG-Chatbot/`](./RAG-Chatbot/) and does the actual reasoning work.

It currently:

- loads a local LoRA adapter via Unsloth,
- builds or loads a Chroma-backed RAG index,
- infers retrieval filters from the user's query,
- resolves directly mentioned IPs and hostnames to assets,
- injects asset inventory context into the prompt,
- and returns a playbook through Chainlit.

The local dashboard entry point is [`RAG-Chatbot/dashboard.py`](./RAG-Chatbot/dashboard.py), which serves the dashboard and mounts the chat UI at `/chat`.

### 3. Asset context layer

The asset layer is one of the more interesting pieces of the project.

Instead of treating the organization as abstract infrastructure, the system can attach inventory context like:

- hostnames,
- IP addresses,
- network zones,
- tool ownership,
- criticality,
- and system roles.

Today the default connector is a realistic mock environment with 24 sample assets such as domain controllers, Splunk, CrowdStrike, Palo Alto firewalls, Veeam backup, and core network infrastructure.

The refresh path is implemented in [`RAG-Chatbot/scripts/refresh_assets.py`](./RAG-Chatbot/scripts/refresh_assets.py), with connector selection handled by [`RAG-Chatbot/connectors/registry.py`](./RAG-Chatbot/connectors/registry.py). Supported connectors in the repo today:

- `mock`
- `nmap`

### 4. Training and research support

The repo still includes selected implementation artifacts behind the model behavior:

- transformation scripts for converting, deduplicating, merging, and enriching IR examples,
- asset profiles used to make outputs more organization-aware,
- and mapping data used to support synthetic data generation experiments.

Raw datasets, private working notes, bulky notebooks, and presentation assets are intentionally left out of the public repo.

## Quick start

### Option A: Visit the public demo

Open:

```text
https://pineapple-corp.vercel.app
```

This is the fastest way to see the UI. If the live AI backend is not attached, the dashboard still loads and the asset view remains functional.

### Option B: Run the full local stack

#### Prerequisites

- Python with the dependencies from [`RAG-Chatbot/requirements.txt`](./RAG-Chatbot/requirements.txt)
- A local LoRA adapter directory
- A CUDA-capable environment if you want practical local inference performance
- Optional: `cloudflared` if you want to expose the local backend to the public dashboard

#### 1. Install dependencies

```powershell
cd RAG-Chatbot
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### 2. Create your environment file

```powershell
Copy-Item .env.example .env
```

At minimum, set:

```env
LORA_ADAPTER_PATH=C:\path\to\your\ir_assistant_lora
DATA_DIR=./data
CHROMA_PERSIST_DIR=./chroma_db
ASSET_CONNECTOR=mock
```

#### 3. Build or refresh the retrieval index

```powershell
python scripts/rebuild_index.py
```

#### 4. Start the unified local dashboard

```powershell
uvicorn dashboard:app --port 8050
```

Then open:

```text
http://localhost:8050
```

### Option C: Connect the local backend to the public dashboard

If you want the public Vercel dashboard to load your local AI assistant:

```powershell
cloudflared tunnel --url http://localhost:8050
```

Take the generated tunnel URL and set the Vercel environment variable:

```text
CHAT_BACKEND=https://your-tunnel-url.trycloudflare.com/chat
```

Redeploy the Vercel project, then the public dashboard will embed your live local assistant.

## How retrieval and grounding work

The backend uses a mix of document retrieval and structured asset grounding.

### Retrieval flow

1. Local documents are loaded from `DATA_DIR`.
2. LlamaIndex builds or loads a Chroma vector store.
3. Query metadata filters are inferred for incident type and document domain when possible.
4. Top matches are retrieved and concatenated into prompt context.
5. If relevant assets are mentioned directly by hostname or IP, those are injected into the prompt as prioritized context.
6. The LoRA-adapted model generates the final playbook.

### Why the asset layer matters

Without asset context, a model tends to produce generic instructions like "check the EDR" or "review the SIEM."

With asset context, the same system can produce responses closer to:

- isolate `srv-dc-01`,
- review `siem-splunk-01`,
- block traffic on `fw-perimeter-01`,
- restore from `backup-veeam-01`.

That is the main design goal of the project.

## Data and model notes

- The public repo keeps the application code and selected data-prep scripts, but omits raw datasets and large training notebooks.
- The repo does **not** include large model artifacts or adapter exports in version control.
- Local exports such as LoRA adapters and other generated artifacts are intentionally ignored by Git.
- The remaining helper scripts reflect an iterative retraining workflow for improving asset-aware playbook behavior.

## What is intentionally omitted from the public repo

- Raw training datasets and intermediate JSONL variants
- Local research notebooks and Colab working files
- Internal runbooks and private working notes
- Presentation images, QR assets, and other demo collateral
- Local exports, vector stores, adapter weights, and generated caches

## Current limitations

- The public deployment is dashboard-first, not a permanently hosted LLM service.
- Default asset data is realistic but synthetic unless you switch to a live connector.
- This is not production-hardened SOAR infrastructure.
- Authentication, authorization, audit boundaries, and enterprise controls are incomplete.
- The public repo is curated for visitors, while broader research and working materials remain local-only.

## Roadmap

- Add more real-world connectors beyond `mock` and `nmap`
- Improve always-on hosting for the inference layer
- Expand evaluation and regression testing for playbook quality
- Continue retraining on hybrid asset-aware datasets
- Broaden threat-intelligence grounding and incident-type coverage

## Supporting material

- [`RAG-Chatbot/README.md`](./RAG-Chatbot/README.md)

## Author

Built by **Ryan Balungeli** as an applied AI + cybersecurity project focused on dynamic incident-response assistance.
