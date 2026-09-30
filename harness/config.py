"""Load config.json and resolve every path relative to the repo root."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config(path=None):
    cfg_path = Path(path) if path else ROOT / "config.json"
    if not cfg_path.exists():
        raise SystemExit(f"Config file not found: {cfg_path}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    # Environment overrides, handy for quick experiments without editing the file.
    if os.environ.get("WIKI_MODEL"):
        cfg["model"] = os.environ["WIKI_MODEL"]
    if os.environ.get("WIKI_OLLAMA_URL"):
        cfg["ollama_url"] = os.environ["WIKI_OLLAMA_URL"]
    cfg["backend"] = os.environ.get("WIKI_BACKEND", "ollama")
    return cfg


def p(cfg, key):
    """Absolute path for a config key such as 'raw_dir'."""
    return ROOT / cfg[key]
