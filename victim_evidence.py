
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_FOLDER = Path("local_vault") / "victim_uploads"

ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".pdf", ".txt"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def save_victim_evidence(uploaded_file):

    if uploaded_file is None:
        return None

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type.")

    file_bytes = uploaded_file.getvalue()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 10 MB limit.")

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    EVIDENCE_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    file_id = uuid.uuid4().hex
    filename = f"{file_id}{extension}"
    file_path = EVIDENCE_FOLDER / filename

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    file_path.write_bytes(file_bytes)

    return {
        "file_path": str(file_path),
        "sha256": file_hash,
        "captured_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "original_filename": Path(uploaded_file.name).name
    }

def save_captured_evidence(source_path):
    source_path = Path(source_path)

    if not source_path.is_file():
        raise FileNotFoundError("Captured evidence file not found.")

    extension = source_path.suffix.lower()

    if extension not in {".png", ".html"}:
        raise ValueError("Unsupported captured evidence type.")

    file_bytes = source_path.read_bytes()

    if not file_bytes:
        raise ValueError("Captured evidence file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("Captured evidence exceeds 10 MB.")

    EVIDENCE_FOLDER.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = EVIDENCE_FOLDER / filename

    destination.write_bytes(file_bytes)

    return {
        "file_path": str(destination),
        "sha256": hashlib.sha256(file_bytes).hexdigest(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "original_filename": source_path.name
    }
