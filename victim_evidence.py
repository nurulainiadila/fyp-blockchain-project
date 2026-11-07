
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
