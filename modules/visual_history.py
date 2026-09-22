"""Local, bounded recovery snapshots, independent for every visual window."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from modules.visual_brief import save_project


class VisualHistory:
    def __init__(self, root=None, keep=12):
        self.root = Path(root) if root else Path.home() / '.arquitecto_prompts' / 'visual_drafts'
        self.session = uuid4().hex
        self.keep = keep
        self.digest = None

    def save(self, refs, fields):
        digest = hashlib.sha256(json.dumps(fields, sort_keys=True).encode())
        for ref in refs:
            digest.update(json.dumps([ref.name, ref.role, ref.image.size]).encode())
            digest.update(ref.image.tobytes())
        fingerprint = digest.hexdigest()
        if fingerprint == self.digest:
            return
        folder = self.root / self.session
        folder.mkdir(parents=True, exist_ok=True)
        name = datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.gprompt'
        save_project(folder / name, refs, fields)
        self.digest = fingerprint
        for old in sorted(folder.glob('*.gprompt'))[:-self.keep]:
            old.unlink()

    def versions(self):
        if not self.root.exists():
            return []
        return sorted(self.root.glob('*/*.gprompt'), key=lambda p: p.stat().st_mtime, reverse=True)


def version_label(path):
    """Read only bounded text metadata for the recovery picker."""
    import zipfile
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.getinfo("project.json").file_size > 1000000:
                raise ValueError("Oversize metadata")
            fields = json.loads(archive.read("project.json"))["fields"]
        name = str(fields.get("project_name") or fields.get("idea") or "Proyecto")
        model = str(fields.get("model", ""))[:35]
        stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m %H:%M:%S")
        return f"{stamp} · {' '.join(name.split())[:65]} · {model}"
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
        return path.stem + " · No se puede leer el resumen"
