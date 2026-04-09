import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from rag_index import RAGIndexConfig, create_or_load_index  # noqa: E402


def _resolve_path(base_dir: Path, value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return str(path.resolve())


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")

    data_dir = _resolve_path(REPO_ROOT, os.getenv("DATA_DIR", "data"))
    chroma_persist_dir = _resolve_path(REPO_ROOT, os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
    chroma_collection = os.getenv("CHROMA_COLLECTION", "irp_docs")
    embedding_model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(
            f"Data directory not found: {data_dir}. "
            "Create it and add IR documents before rebuilding the index."
        )

    Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)

    metadata_path = os.path.join(chroma_persist_dir, "index_meta.json")
    config = RAGIndexConfig(
        data_dir=data_dir,
        chroma_persist_dir=chroma_persist_dir,
        chroma_collection=chroma_collection,
        metadata_path=metadata_path,
    )

    _, metadata = create_or_load_index(
        config=config,
        embed_model=Settings.embed_model,
        force_rebuild=True,
    )

    print("Index rebuild complete.")
    print(f"- backend: {metadata.get('index_backend')}")
    print(f"- collection: {metadata.get('collection')}")
    print(f"- index_source: {metadata.get('index_source')}")
    print(f"- indexed_docs: {metadata.get('indexed_docs')}")
    print(f"- vector_count: {metadata.get('vector_count')}")
    print(f"- last_refresh_at: {metadata.get('last_refresh_at')}")


if __name__ == "__main__":
    main()
