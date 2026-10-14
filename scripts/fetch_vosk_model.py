"""Download the Vosk small English speech model into models/.

The model is ~68MB, so it is deliberately NOT committed to this repository.
Run this once after cloning:

    python scripts/fetch_vosk_model.py

It writes to models/vosk-model-small-en-us-0.15/, which is the path
config.json points at (stt.model).
"""

from __future__ import annotations

import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
ROOT = Path(__file__).resolve().parent.parent
TARGET_PARENT = ROOT / "models"
TARGET = TARGET_PARENT / MODEL_NAME


def main() -> int:
    if TARGET.exists():
        print(f"Already present: {TARGET}")
        return 0

    TARGET_PARENT.mkdir(parents=True, exist_ok=True)
    archive = TARGET_PARENT / f"{MODEL_NAME}.zip"

    print(f"Downloading {MODEL_URL}")
    try:
        with urllib.request.urlopen(MODEL_URL, timeout=60) as resp, archive.open(
            "wb"
        ) as out:
            shutil.copyfileobj(resp, out)
    except Exception as exc:  # noqa: BLE001
        print(f"Download failed: {exc}")
        print(f"Fetch it manually from {MODEL_URL}")
        return 1

    size_mb = archive.stat().st_size / (1024 * 1024)
    print(f"Downloaded {size_mb:.1f} MB, extracting...")

    try:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(TARGET_PARENT)
    except zipfile.BadZipFile:
        print("Archive is corrupt - delete it and retry.")
        archive.unlink(missing_ok=True)
        return 1
    finally:
        archive.unlink(missing_ok=True)

    if not TARGET.exists():
        print(f"Extraction did not produce {TARGET}")
        return 1

    print(f"Done -> {TARGET}")
    print("Now run: python talk_for_me.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())