# RAG-Chatbot

A document-grounded chatbot using LlamaIndex retrieval + Chainlit UI + local LoRA-based generation.

## What This Uses

- Retrieval: LlamaIndex + Chroma vector store from your `data/` documents
- Embeddings: `BAAI/bge-small-en-v1.5`
- Generation: local Unsloth model with your trained LoRA adapter

## Installation

1. Clone repo:

   ```bash
   git clone https://github.com/ryanflash66/RAG-Chatbot.git
   cd RAG-Chatbot
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Create a `.env` file in project root:

You can start from the sample file:

```bash
cp .env.example .env
```

PowerShell equivalent:

```powershell
Copy-Item .env.example .env
```

```env
LORA_ADAPTER_PATH=/content/drive/MyDrive/irp_exports/ir_assistant_lora
DATA_DIR=./data
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
MAX_SEQ_LENGTH=2048
MAX_NEW_TOKENS=512
TEMPERATURE=0.1
RETRIEVAL_TOP_K=4
RETRIEVAL_ENABLE_FILTERS=true
SOURCE_SNIPPET_CHARS=220
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=irp_docs
SHOW_SOURCES=false
ATTENTION_BACKEND=auto
SHOW_STARTUP_CHECKLIST=true
```

### Required

- `LORA_ADAPTER_PATH` (required): path to saved adapter folder containing files like `adapter_model.safetensors` and `adapter_config.json`

### Optional

- `MAX_SEQ_LENGTH` (default `2048`)
- `MAX_NEW_TOKENS` (default `512`)
- `TEMPERATURE` (default `0.1`)
- `RETRIEVAL_TOP_K` (default `4`)
- `RETRIEVAL_ENABLE_FILTERS` (default `true`): infer metadata filters from query intent and auto-fallback to unfiltered retrieval if no matches are found
- `SOURCE_SNIPPET_CHARS` (default `220`): max excerpt length per source item (`0` disables excerpts)
- `DATA_DIR` (default `./data`)
- `EMBEDDING_MODEL` (default `BAAI/bge-small-en-v1.5`)
- `CHROMA_PERSIST_DIR` (default `./chroma_db`)
- `CHROMA_COLLECTION` (default `irp_docs`)
- `SHOW_SOURCES` (default `false`): include retrieved source list in responses
- `ATTENTION_BACKEND` (default `auto`): choose `auto`, `sdpa`, or `xformers`
- `SHOW_STARTUP_CHECKLIST` (default `true`): set to `false` to disable the auto test checklist message at chat start

## Usage

1. Place source documents in `data/`.
2. Ensure `LORA_ADAPTER_PATH` points to your adapter folder.
3. Build or refresh the index:

   ```bash
   python scripts/rebuild_index.py
   ```

4. Run:

   ```bash
   chainlit run app.py
   ```

5. Open `http://localhost:8000`.
6. In chat, send `/health` (or `/backend`) to view backend/model/index status.

## Runtime Notes

- Colab GPU and local GPU are both supported.
- Index data is persisted in `CHROMA_PERSIST_DIR` (default `./chroma_db`).
- Retrieval can apply inferred metadata filters and automatically fall back to unfiltered search when filtered results are empty.
- If no relevant context is retrieved, the app still returns a best-effort answer.
- `/health` (or `/status`) prints current runtime health details.

### Cross-machine robustness

- Recommended default: `ATTENTION_BACKEND=auto`
- If a newer GPU fails with xformers kernel errors, set `ATTENTION_BACKEND=sdpa`
- Use `/backend` in chat to inspect backend selection, reason, and GPU capability

### Scheduled index refresh (Windows)

Use Windows Task Scheduler for periodic rebuilds (recommended over in-app scheduling):

```powershell
python scripts/rebuild_index.py
```

Suggested cadence for local-doc workflows: every 6-24 hours, or after document updates.

## Project Structure

```text
RAG-Chatbot/
├── app.py
├── data/
├── chroma_db/
├── scripts/rebuild_index.py
├── requirements.txt
└── README.md
```
