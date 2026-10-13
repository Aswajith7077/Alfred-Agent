"""Downloads the sherpa-onnx diarization models into models/diarization/ (gitignored).

Run with: cd backend/apps && python diarization/download_models.py
"""
import tarfile
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "diarization"

SEGMENTATION_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    "speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
)
EMBEDDING_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    "speaker-recongition-models/3dspeaker_speech_campplus_sv_en_voxceleb_16k.onnx"
)


def download(url: str, dest: Path):
    if dest.exists():
        print(f"✓ already present: {dest}")
        return
    print(f"downloading {url} -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    seg_archive = MODELS_DIR / "sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
    download(SEGMENTATION_URL, seg_archive)

    seg_dir = MODELS_DIR / "sherpa-onnx-pyannote-segmentation-3-0"
    if not seg_dir.exists():
        print(f"extracting {seg_archive}")
        with tarfile.open(seg_archive, "r:bz2") as tar:
            tar.extractall(MODELS_DIR)
    seg_archive.unlink(missing_ok=True)

    embedding_model = MODELS_DIR / "3dspeaker_speech_campplus_sv_en_voxceleb_16k.onnx"
    download(EMBEDDING_URL, embedding_model)

    print("Done. Models in", MODELS_DIR)


if __name__ == "__main__":
    main()
