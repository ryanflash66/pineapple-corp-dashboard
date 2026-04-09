import os
import traceback
from typing import Optional

import unsloth
import chainlit as cl
import torch
from unsloth.utils import attention_dispatch as unsloth_attention_dispatch
from llama_index.core.settings import Settings
from llama_index.core.vector_stores import (
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from unsloth import FastLanguageModel
from dotenv import load_dotenv

from rag_index import RAGIndexConfig, create_or_load_index, read_index_metadata

# Load environment vars from .env
load_dotenv()

# --- Asset connector: refresh inventory at startup ---
_ASSET_CONNECTOR_TYPE = os.getenv("ASSET_CONNECTOR", "").strip().lower()
if _ASSET_CONNECTOR_TYPE and _ASSET_CONNECTOR_TYPE != "none":
    try:
        from scripts.refresh_assets import refresh_assets

        _asset_count = refresh_assets()
        print(f"Asset connector | connector={_ASSET_CONNECTOR_TYPE} | assets={_asset_count}")
    except Exception as _asset_exc:
        print(f"Asset connector | FAILED: {_asset_exc} (continuing with existing data)")

LORA_ADAPTER_PATH = os.getenv("LORA_ADAPTER_PATH")
if not LORA_ADAPTER_PATH:
    raise ValueError(
        "LORA_ADAPTER_PATH not found in environment variables. "
        "Set it to your trained adapter folder path (for example: /content/drive/MyDrive/irp_exports/ir_assistant_lora)."
    )

if not os.path.isdir(LORA_ADAPTER_PATH):
    raise FileNotFoundError(f"Adapter path does not exist or is not a directory: {LORA_ADAPTER_PATH}")

required_adapter_files = ["adapter_config.json", "adapter_model.safetensors"]
missing_adapter_files = [
    name for name in required_adapter_files if not os.path.exists(os.path.join(LORA_ADAPTER_PATH, name))
]
if missing_adapter_files:
    print(f"Warning: missing expected adapter files: {missing_adapter_files}")

MAX_SEQ_LENGTH = int(os.getenv("MAX_SEQ_LENGTH", "2048"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
ASSET_TOP_K = int(os.getenv("ASSET_RETRIEVAL_TOP_K", "2"))
ASSET_CONTEXT_MAX_TOKENS = int(os.getenv("ASSET_CONTEXT_MAX_TOKENS", "256"))
ATTENTION_BACKEND_REQUESTED = os.getenv("ATTENTION_BACKEND", "auto").strip().lower()
SHOW_STARTUP_CHECKLIST = os.getenv("SHOW_STARTUP_CHECKLIST", "true").strip().lower() in {
    "1", "true", "yes", "on"
}
SHOW_SOURCES = os.getenv("SHOW_SOURCES", "false").strip().lower() in {
    "1", "true", "yes", "on"
}
RETRIEVAL_ENABLE_FILTERS = os.getenv("RETRIEVAL_ENABLE_FILTERS", "true").strip().lower() in {
    "1", "true", "yes", "on"
}
SOURCE_SNIPPET_CHARS = max(0, int(os.getenv("SOURCE_SNIPPET_CHARS", "220")))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_env_path(path_value: str) -> str:
    if os.path.isabs(path_value):
        return path_value
    return os.path.abspath(os.path.join(BASE_DIR, path_value))


DATA_DIR = resolve_env_path(os.getenv("DATA_DIR", "data"))
CHROMA_PERSIST_DIR = resolve_env_path(os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "irp_docs")
INDEX_METADATA_PATH = os.path.join(CHROMA_PERSIST_DIR, "index_meta.json")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ---------------------------------------------------------------------------
# Asset lookup: map IPs and hostnames to inventory entries for direct matching
# ---------------------------------------------------------------------------
import json as _json
import re as _re

_ASSET_IP_MAP: dict[str, dict] = {}
_ASSET_NAME_SET: set[str] = set()
_IP_PATTERN = _re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

_asset_json_path = os.path.join(DATA_DIR, "asset_inventory.json")
if os.path.exists(_asset_json_path):
    try:
        with open(_asset_json_path, "r", encoding="utf-8") as _af:
            _asset_data = _json.load(_af)
        for _a in _asset_data.get("assets", []):
            ip = _a.get("ip_or_subnet", "")
            name = _a.get("name", "")
            if ip and ip not in ("cloud", "DHCP"):
                _ASSET_IP_MAP[ip] = _a
            if name:
                _ASSET_NAME_SET.add(name.lower())
                _ASSET_IP_MAP[name.lower()] = _a
        print(f"Asset lookup | {len(_ASSET_NAME_SET)} hostnames, {len(_ASSET_IP_MAP)} entries")
    except Exception as _exc:
        print(f"Asset lookup | FAILED: {_exc}")


def resolve_query_assets(query: str) -> list[str]:
    """Find assets directly referenced by IP or hostname in the user query."""
    matched = {}
    query_lower = query.lower()
    # Match IPs
    for ip in _IP_PATTERN.findall(query):
        asset = _ASSET_IP_MAP.get(ip)
        if asset and asset["name"] not in matched:
            matched[asset["name"]] = asset
    # Match hostnames
    for name in _ASSET_NAME_SET:
        if name in query_lower:
            asset = _ASSET_IP_MAP.get(name)
            if asset and asset["name"] not in matched:
                matched[asset["name"]] = asset
    # Format as markdown lines matching training format
    lines = []
    for a in matched.values():
        lines.append(
            f"- {a['name']}: {a.get('vendor_product', '')} {a.get('type', '')}, "
            f"{a.get('network_zone', '')} ({a.get('ip_or_subnet', '')}), "
            f"{a.get('role', '')}, {a.get('notes', '')}, "
            f"{a.get('criticality', '')} criticality"
        )
    return lines

INCIDENT_QUERY_HINTS = {
    "ransomware": ["ransomware", "encrypt", "crypto locker", "double extortion", "ransom note"],
    "phishing": ["phishing", "spearphish", "credential theft", "email spoof", "bec", "business email"],
    "data_breach": ["data breach", "data leak", "exfil", "exfiltration", "pii exposure", "data loss"],
    "malware": ["malware", "trojan", "worm", "virus", "loader", "backdoor", "c2", "command and control"],
    "insider_threat": ["insider", "privilege abuse", "usb theft", "internal actor", "dropbox", "google drive"],
    "credential_dumping": ["dcsync", "credential dump", "pass the hash", "kerberoast", "golden ticket",
                           "ntds", "krbtgt", "mimikatz", "lsass", "dcsync"],
    "supply_chain": ["supply chain", "dependency compromise", "package compromise", "ci/cd",
                     "zero-day", "0-day", "zero day"],
    "ddos": ["ddos", "denial of service", "botnet", "flood", "brute force", "rate limit", "cryptojack"],
    "iot_ot": ["iot", "ot", "scada", "ics", "industrial control"],
}

IR_DOMAIN_HINTS = {
    "incident",
    "response",
    "playbook",
    "triage",
    "containment",
    "eradication",
    "recovery",
    "forensic",
    "soc",
    "siem",
    "edr",
}


def infer_query_filters(query: str) -> tuple[Optional[MetadataFilters], dict]:
    query_lower = query.lower()
    incident_type = None
    for label, hints in INCIDENT_QUERY_HINTS.items():
        if any(hint in query_lower for hint in hints):
            incident_type = label
            break

    wants_ir_domain = any(hint in query_lower for hint in IR_DOMAIN_HINTS)

    filters = []
    if incident_type:
        filters.append(
            MetadataFilter(
                key="incident_type",
                value=incident_type,
                operator=FilterOperator.EQ,
            )
        )
    if wants_ir_domain:
        filters.append(
            MetadataFilter(
                key="doc_domain",
                value="ir",
                operator=FilterOperator.EQ,
            )
        )

    if not filters:
        return None, {
            "incident_type": None,
            "doc_domain": None,
        }

    return (
        MetadataFilters(filters=filters, condition=FilterCondition.AND),
        {
            "incident_type": incident_type,
            "doc_domain": "ir" if wants_ir_domain else None,
        },
    )


_IR_ALL_KEYWORDS = set()
for _hints in INCIDENT_QUERY_HINTS.values():
    _IR_ALL_KEYWORDS.update(_hints)
_IR_ALL_KEYWORDS.update(IR_DOMAIN_HINTS)
_IR_ALL_KEYWORDS.update({
    "threat", "attack", "breach", "vulnerability", "vuln", "cve",
    "patch", "alert", "mitre", "nist", "detect", "investigate",
    "remediate", "escalat", "ioc", "indicator", "compromise",
    "dcsync", "credential", "lateral", "kerberos", "mimikatz",
    "exfiltrat", "zero-day", "brute", "ddos", "botnet",
})

CAPABILITIES_MESSAGE = (
    "I'm an IR Playbook assistant, specialized in generating incident response playbooks. "
    "I can help with:\n"
    "- Creating playbooks for specific incidents (ransomware, phishing, data breaches, malware, etc.)\n"
    "- Containment, eradication, and recovery strategies\n"
    "- SOC/SIEM/EDR triage and response procedures\n\n"
    "Try something like: *Create an IR playbook for ransomware lateral movement via SMB.*"
)


def is_ir_related(query: str) -> bool:
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in _IR_ALL_KEYWORDS)


def summarize_filter_hint(filter_hint: dict, fallback_used: bool) -> str:
    parts = []
    if filter_hint.get("incident_type"):
        parts.append(f"incident_type={filter_hint['incident_type']}")
    if filter_hint.get("doc_domain"):
        parts.append(f"doc_domain={filter_hint['doc_domain']}")
    if not parts:
        return "none"

    summary = ", ".join(parts)
    if fallback_used:
        summary += " (fallback=unfiltered)"
    else:
        summary += " (filtered)"
    return summary


def extract_result_text(result) -> str:
    node = getattr(result, "node", result)
    text = node.get_content().strip() if hasattr(node, "get_content") else str(node)
    return text


def is_xformers_kernel_error(exc: Exception) -> bool:
    error_text = str(exc)
    return (
        "memory_efficient_attention_forward" in error_text
        or "No operator found for `memory_efficient_attention_forward`" in error_text
        or "xformers" in error_text.lower()
    )


def configure_attention_backend() -> tuple[str, str]:
    global ATTENTION_BACKEND_REQUESTED

    valid_backends = {"auto", "sdpa", "xformers"}
    if ATTENTION_BACKEND_REQUESTED not in valid_backends:
        print(
            f"Unknown ATTENTION_BACKEND='{ATTENTION_BACKEND_REQUESTED}'. "
            "Falling back to 'auto'."
        )
        ATTENTION_BACKEND_REQUESTED = "auto"

    has_xformers = bool(getattr(unsloth_attention_dispatch, "HAS_XFORMERS", False))
    gpu_capability = torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None

    if ATTENTION_BACKEND_REQUESTED == "sdpa":
        unsloth_attention_dispatch.HAS_XFORMERS = False
        return "sdpa", "forced by ATTENTION_BACKEND=sdpa"

    if ATTENTION_BACKEND_REQUESTED == "xformers":
        if has_xformers:
            unsloth_attention_dispatch.HAS_XFORMERS = True
            return "xformers", "forced by ATTENTION_BACKEND=xformers"
        unsloth_attention_dispatch.HAS_XFORMERS = False
        return "sdpa", "xformers requested but unavailable; using sdpa"

    if not torch.cuda.is_available():
        unsloth_attention_dispatch.HAS_XFORMERS = False
        return "sdpa", "cpu runtime detected"

    if not has_xformers:
        unsloth_attention_dispatch.HAS_XFORMERS = False
        return "sdpa", "xformers unavailable; using sdpa"

    major_capability = gpu_capability[0] if gpu_capability else 0
    if major_capability > 9:
        unsloth_attention_dispatch.HAS_XFORMERS = False
        capability_label = f"{gpu_capability[0]}.{gpu_capability[1]}" if gpu_capability else "unknown"
        return "sdpa", f"auto fallback for newer GPU capability {capability_label}"

    unsloth_attention_dispatch.HAS_XFORMERS = True
    return "xformers", "auto-selected xformers backend"


ATTENTION_BACKEND_ACTIVE, ATTENTION_BACKEND_REASON = configure_attention_backend()
print(
    f"Attention backend | requested={ATTENTION_BACKEND_REQUESTED} | "
    f"active={ATTENTION_BACKEND_ACTIVE} | reason={ATTENTION_BACKEND_REASON}"
)

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=LORA_ADAPTER_PATH,
    max_seq_length=MAX_SEQ_LENGTH,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)
print(
    f"Using local LoRA backend | adapter={LORA_ADAPTER_PATH} | "
    f"device={DEVICE} | max_seq_length={MAX_SEQ_LENGTH}"
)

# Use a local embedding model instead of OpenAI
Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)

index_config = RAGIndexConfig(
    data_dir=DATA_DIR,
    chroma_persist_dir=CHROMA_PERSIST_DIR,
    chroma_collection=CHROMA_COLLECTION,
    metadata_path=INDEX_METADATA_PATH,
)

try:
    index, index_metadata = create_or_load_index(
        config=index_config,
        embed_model=Settings.embed_model,
        force_rebuild=False,
    )
    index_source = index_metadata.get("index_source", "unknown")
    indexed_docs = index_metadata.get("indexed_docs", "unknown")
    print(
        "Index ready | "
        f"backend={index_metadata.get('index_backend', 'chroma')} | "
        f"collection={index_metadata.get('collection', CHROMA_COLLECTION)} | "
        f"source={index_source}"
    )
except Exception as index_error:
    raise RuntimeError(
        "Failed to initialize RAG index. "
        "Ensure DATA_DIR has IR documents and Chroma dependencies are installed. "
        f"Error: {index_error}"
    ) from index_error


def get_index_status() -> dict:
    metadata = read_index_metadata(INDEX_METADATA_PATH)

    return {
        "index_backend": metadata.get("index_backend", "chroma"),
        "index_source": metadata.get("index_source", index_source),
        "indexed_docs": metadata.get("indexed_docs", indexed_docs),
        "vector_count": metadata.get("vector_count", "unknown"),
        "collection": metadata.get("collection", CHROMA_COLLECTION),
        "persist_dir": metadata.get("persist_dir", CHROMA_PERSIST_DIR),
        "last_refresh_at": metadata.get("last_refresh_at", "unknown"),
    }


def get_health_status() -> dict:
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        reserved_gb = round(torch.cuda.memory_reserved(0) / 1024 / 1024 / 1024, 3)
        gpu_capability = torch.cuda.get_device_capability(0)
        gpu_capability_str = f"{gpu_capability[0]}.{gpu_capability[1]}"
    else:
        device_name = "cpu"
        reserved_gb = 0.0
        gpu_capability_str = "N/A"

    index_status = get_index_status()

    return {
        "backend": "local_unsloth_lora",
        "device": DEVICE,
        "device_name": device_name,
        "gpu_compute_capability": gpu_capability_str,
        "adapter_path": LORA_ADAPTER_PATH,
        "missing_adapter_files": missing_adapter_files,
        "max_seq_length": MAX_SEQ_LENGTH,
        "max_new_tokens": MAX_NEW_TOKENS,
        "temperature": TEMPERATURE,
        "retrieval_top_k": TOP_K,
        "attention_backend_requested": ATTENTION_BACKEND_REQUESTED,
        "attention_backend_active": ATTENTION_BACKEND_ACTIVE,
        "attention_backend_reason": ATTENTION_BACKEND_REASON,
        "index_backend": index_status["index_backend"],
        "index_source": index_status["index_source"],
        "indexed_docs": index_status["indexed_docs"],
        "vector_count": index_status["vector_count"],
        "collection": index_status["collection"],
        "persist_dir": index_status["persist_dir"],
        "last_refresh_at": index_status["last_refresh_at"],
        "show_sources": SHOW_SOURCES,
        "retrieval_enable_filters": RETRIEVAL_ENABLE_FILTERS,
        "source_snippet_chars": SOURCE_SNIPPET_CHARS,
        "gpu_memory_reserved_gb": reserved_gb,
    }


startup_status = get_health_status()
print(
    "Startup health | "
    f"backend={startup_status['backend']} | "
    f"device={startup_status['device_name']} | "
    f"index={startup_status['index_source']} | "
    f"indexed_docs={startup_status['indexed_docs']} | "
    f"missing_adapter_files={startup_status['missing_adapter_files']}"
)


def build_prompt(user_question: str, context_text: str) -> str:
    has_asset_context = "Organization assets:" in context_text
    instruction = (
        "Generate an incident response playbook for the following security incident. "
        "Use the retrieved context to inform your response where relevant. "
        "If asset inventory context is provided, reference specific tools, "
        "hostnames, and network zones in your playbook steps. "
        "Include an 'Affected Assets' section listing each referenced asset and its role."
        if has_asset_context
        else
        "Generate an incident response playbook for the following security incident. "
        "Use the retrieved context to inform your response where relevant."
    )
    input_text = user_question
    if context_text and context_text != "No relevant context retrieved.":
        input_text += f"\n\nRetrieved context:\n{context_text}"

    return (
        "Below is an instruction that describes a task, paired with an input that provides further context. "
        "Write a response that appropriately completes the request.\n\n"
        f"### Instruction:\n{instruction}\n\n"
        f"### Input:\n{input_text}\n\n"
        "### Response:\n"
    )


def build_frontend_test_checklist() -> str:
    return "\n".join([
        "Frontend test checklist:",
        "1) Send `/health` and confirm adapter/device/index values.",
        "2) Prompt: Create an IR playbook for ransomware lateral movement via SMB.",
        "3) Prompt: What are the first 6 containment actions for suspected credential theft?",
        "4) Prompt: Based on uploaded docs, what escalation path should SOC follow?",
        "Pass criteria:",
        "- Output is IR-specific and actionable (triage, containment, eradication, recovery).",
        "- Output reflects retrieved document context, not only generic guidance.",
    ])


def build_sources_block(nodes) -> str:
    lines = []
    for idx, result in enumerate(nodes[:TOP_K], start=1):
        node = getattr(result, "node", result)
        metadata = getattr(node, "metadata", {}) or {}

        source = (
            metadata.get("source")
            or metadata.get("file_path")
            or metadata.get("filename")
            or "unknown"
        )
        section = metadata.get("section")
        score = getattr(result, "score", None)

        line = f"{idx}. {source}"
        if section and section != "N/A":
            line += f" | section: {section}"
        if isinstance(score, (int, float)):
            line += f" | score: {score:.3f}"

        if SOURCE_SNIPPET_CHARS > 0:
            snippet = extract_result_text(result)
            snippet = " ".join(snippet.split())
            if len(snippet) > SOURCE_SNIPPET_CHARS:
                snippet = snippet[:SOURCE_SNIPPET_CHARS].rstrip() + "..."
            if snippet:
                line += f" | excerpt: {snippet}"

        lines.append(line)

    return "\n".join(lines)


@cl.on_chat_start
async def factory():
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    cl.user_session.set("retriever", retriever)
    cl.user_session.set("startup_status", startup_status)
    print("on_chat_start: session initialized successfully")
    if SHOW_STARTUP_CHECKLIST:
        await cl.Message(content=build_frontend_test_checklist()).send()


@cl.on_message
async def main(message: cl.Message):
    try:
        msg_lower = message.content.strip().lower()

        if msg_lower in {"/help", "help", "what can you do", "what do you do"}:
            await cl.Message(content=CAPABILITIES_MESSAGE).send()
            return

        if msg_lower in {"/health", "/status", "health", "status", "/backend", "backend"}:
            status = get_health_status()
            cl.user_session.set("startup_status", status)
            lines = [
                "Backend health:",
                f"- backend: {status['backend']}",
                f"- device: {status['device_name']} ({status['device']})",
                f"- gpu_compute_capability: {status['gpu_compute_capability']}",
                f"- adapter_path: {status['adapter_path']}",
                f"- missing_adapter_files: {status['missing_adapter_files']}",
                f"- index_backend: {status['index_backend']}",
                f"- index_source: {status['index_source']}",
                f"- indexed_docs: {status['indexed_docs']}",
                f"- vector_count: {status['vector_count']}",
                f"- collection: {status['collection']}",
                f"- persist_dir: {status['persist_dir']}",
                f"- last_refresh_at: {status['last_refresh_at']}",
                f"- attention_backend_requested: {status['attention_backend_requested']}",
                f"- attention_backend_active: {status['attention_backend_active']}",
                f"- attention_backend_reason: {status['attention_backend_reason']}",
                f"- retrieval_top_k: {status['retrieval_top_k']}",
                f"- max_seq_length: {status['max_seq_length']}",
                f"- max_new_tokens: {status['max_new_tokens']}",
                f"- temperature: {status['temperature']}",
                f"- show_sources: {status['show_sources']}",
                f"- retrieval_enable_filters: {status['retrieval_enable_filters']}",
                f"- source_snippet_chars: {status['source_snippet_chars']}",
                f"- gpu_memory_reserved_gb: {status['gpu_memory_reserved_gb']}",
            ]
            await cl.Message(content="\n".join(lines)).send()
            return

        if not is_ir_related(message.content):
            await cl.Message(content=CAPABILITIES_MESSAGE).send()
            return

        retriever = cl.user_session.get("retriever")
        if retriever is None:
            retriever = index.as_retriever(similarity_top_k=TOP_K)
            cl.user_session.set("retriever", retriever)

        metadata_filters = None
        filter_hint = {"incident_type": None, "doc_domain": None}
        filter_fallback_used = False

        if RETRIEVAL_ENABLE_FILTERS:
            metadata_filters, filter_hint = infer_query_filters(message.content)

        try:
            if metadata_filters is not None:
                filtered_retriever = index.as_retriever(
                    similarity_top_k=TOP_K,
                    filters=metadata_filters,
                )
                nodes = await cl.make_async(filtered_retriever.retrieve)(message.content)
                if not nodes:
                    filter_fallback_used = True
                    nodes = await cl.make_async(retriever.retrieve)(message.content)
            else:
                nodes = await cl.make_async(retriever.retrieve)(message.content)
        except Exception as retrieval_exc:
            print(f"Retrieval error: {retrieval_exc}")
            await cl.Message(
                content=(
                    "Retrieval failed before generation. "
                    f"Error: {retrieval_exc}"
                )
            ).send()
            return

        context_chunks = []
        for node in nodes:
            text = extract_result_text(node)
            if text:
                context_chunks.append(text)

        context_text = "\n\n".join(context_chunks[:TOP_K]) if context_chunks else "No relevant context retrieved."
        print(f"on_message: retrieved {len(nodes)} nodes, {len(context_chunks)} with text")

        # --- Asset context injection ---
        try:
            asset_filter = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="doc_domain",
                        value="asset_inventory",
                        operator=FilterOperator.EQ,
                    )
                ]
            )
            asset_retriever = index.as_retriever(
                similarity_top_k=ASSET_TOP_K,
                filters=asset_filter,
            )
            asset_nodes = await cl.make_async(asset_retriever.retrieve)(message.content)
            asset_chunks = [extract_result_text(n) for n in asset_nodes if extract_result_text(n)]
        except Exception:
            asset_chunks = []

        # Direct IP/hostname resolution — these take priority over RAG-retrieved assets
        direct_asset_lines = resolve_query_assets(message.content)
        if direct_asset_lines:
            print(f"on_message: resolved {len(direct_asset_lines)} assets from query")

        if asset_chunks or direct_asset_lines:
            asset_text = "\n\n".join(asset_chunks) if asset_chunks else ""
            # Prepend directly-resolved assets so they get priority
            if direct_asset_lines:
                direct_text = "\n".join(direct_asset_lines)
                asset_text = f"{direct_text}\n{asset_text}" if asset_text else direct_text
            # Cap asset context to avoid overwhelming the model (trained on 5-8 assets)
            if ASSET_CONTEXT_MAX_TOKENS > 0:
                asset_ids = tokenizer.encode(asset_text, add_special_tokens=False)
                if len(asset_ids) > ASSET_CONTEXT_MAX_TOKENS:
                    asset_ids = asset_ids[:ASSET_CONTEXT_MAX_TOKENS]
                    asset_text = tokenizer.decode(asset_ids, skip_special_tokens=True)
                    # Trim to last complete line to avoid partial asset entries
                    last_newline = asset_text.rfind("\n")
                    if last_newline > 0:
                        asset_text = asset_text[:last_newline]
                    print(f"on_message: asset context capped to {ASSET_CONTEXT_MAX_TOKENS} tokens")
            context_text = f"{context_text}\n\nOrganization assets:\n{asset_text}"
            print(f"on_message: injected asset context ({len(direct_asset_lines)} direct + {len(asset_chunks)} RAG chunks)")

        # Budget-aware context truncation: ensure the prompt template
        # (instruction + ### Response marker) is never truncated.
        input_max_len = max(256, MAX_SEQ_LENGTH - MAX_NEW_TOKENS)
        template_prompt = build_prompt(message.content, "")
        template_tokens = len(tokenizer.encode(template_prompt, add_special_tokens=False))
        context_budget = input_max_len - template_tokens - 16  # 16-token safety margin

        if context_budget > 0:
            context_ids = tokenizer.encode(context_text, add_special_tokens=False)
            if len(context_ids) > context_budget:
                context_ids = context_ids[:context_budget]
                context_text = tokenizer.decode(context_ids, skip_special_tokens=True)
                print(f"on_message: context truncated to {context_budget} tokens (budget)")

        prompt = build_prompt(message.content, context_text)
        prompt_token_count = len(tokenizer.encode(prompt, add_special_tokens=False))
        print(f"on_message: prompt={prompt_token_count} tokens, input_max_len={input_max_len}")

        model_inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=input_max_len,
        )
        model_inputs = {key: value.to(DEVICE) for key, value in model_inputs.items()}

        def generate_once():
            return model.generate(
                input_ids=model_inputs["input_ids"],
                attention_mask=model_inputs.get("attention_mask"),
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=TEMPERATURE > 0,
                temperature=TEMPERATURE,
                pad_token_id=tokenizer.eos_token_id,
                use_cache=True,
            )

        print(f"on_message: starting generation (max_new_tokens={MAX_NEW_TOKENS})")
        try:
            output_ids = await cl.make_async(generate_once)()
        except Exception as exc:
            global ATTENTION_BACKEND_ACTIVE
            global ATTENTION_BACKEND_REASON

            if is_xformers_kernel_error(exc):
                previous_backend = ATTENTION_BACKEND_ACTIVE
                unsloth_attention_dispatch.HAS_XFORMERS = False
                ATTENTION_BACKEND_ACTIVE = "sdpa"
                ATTENTION_BACKEND_REASON = (
                    f"runtime fallback after xformers kernel error (previous={previous_backend})"
                )
                print(
                    "Generation backend fallback triggered: xformers kernel failed, switching to sdpa."
                )

                try:
                    output_ids = await cl.make_async(generate_once)()
                    cl.user_session.set("startup_status", get_health_status())
                except Exception as retry_exc:
                    print(f"Generation error after sdpa fallback: {retry_exc}")
                    await cl.Message(
                        content=(
                            "Generation failed after backend fallback. "
                            f"Error: {retry_exc}"
                        )
                    ).send()
                    return
            else:
                print(f"Generation error: {exc}")
                await cl.Message(
                    content=(
                        "Generation failed in the model backend. "
                        f"Error: {exc}"
                    )
                ).send()
                return

        if output_ids is None:
            print("Generation error: model returned no output IDs")
            await cl.Message(
                content=(
                    "Generation failed in the model backend. "
                    "No output IDs were produced."
                )
            ).send()
            return

        generated_ids = output_ids[0][model_inputs["input_ids"].shape[-1]:]
        print(f"on_message: generated {len(generated_ids)} new tokens")
        answer = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        print(f"on_message: decoded answer length={len(answer)}")

        retrieval_mode = summarize_filter_hint(filter_hint, filter_fallback_used)
        if SHOW_SOURCES and nodes:
            sources_block = build_sources_block(nodes)
            if sources_block:
                answer += f"\n\nSources:\n{sources_block}"
            if retrieval_mode != "none":
                answer += f"\n\nRetrieval filter: {retrieval_mode}"

        if not answer.strip():
            answer = (
                "Model returned an empty completion for this query. "
                "Please retry once; if it persists, lower MAX_NEW_TOKENS or set ATTENTION_BACKEND=sdpa."
            )

        await cl.Message(content=answer).send()
    except Exception as unhandled_exc:
        print("Unhandled on_message exception:")
        print(traceback.format_exc())
        await cl.Message(
            content=(
                "Unhandled backend error while processing the query. "
                f"Error: {unhandled_exc}"
            )
        ).send()
