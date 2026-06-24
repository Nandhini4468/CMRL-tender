import shutil
from pathlib import Path
from typing import List, Dict


def get_bidder_folders(master_folder: str) -> List[Dict]:
    """Return list of dicts with bidder name and folder path."""
    master = Path(master_folder)
    if not master.exists():
        return []
    bidders = []
    for item in sorted(master.iterdir()):
        if item.is_dir():
            files = list_bidder_files(str(item))
            bidders.append({"name": item.name, "path": str(item), "files": files})
    return bidders


def list_bidder_files(folder: str) -> List[Dict]:
    """List all supported documents in a bidder folder."""
    supported = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".docx"}
    folder_path = Path(folder)
    files = []
    for f in folder_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in supported:
            files.append({"name": f.name, "path": str(f), "ext": f.suffix.lower()})
    return files


def save_uploaded_file(uploaded_file, dest_dir: str) -> str:
    """Save a Streamlit UploadedFile to disk and return the path."""
    dest = Path(dest_dir) / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


def save_uploaded_folder(uploaded_files, bidder_name: str, master_dir: str) -> str:
    """Save multiple uploaded files under master_dir/bidder_name/."""
    bidder_dir = Path(master_dir) / bidder_name
    bidder_dir.mkdir(parents=True, exist_ok=True)
    for uf in uploaded_files:
        dest = bidder_dir / uf.name
        with open(dest, "wb") as f:
            f.write(uf.getbuffer())
    return str(bidder_dir)


def clean_chroma_collection(persist_dir: str, collection_name: str):
    """Delete a ChromaDB collection directory to allow re-indexing."""
    import chromadb
    client = chromadb.PersistentClient(path=persist_dir)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
