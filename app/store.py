"""Provider 配置存储 - 从 ~/.expense-helper/providers.json 读取 active provider"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


def get_store_dir() -> Path:
    return Path.home() / ".expense-helper"


def get_providers_path() -> Path:
    return get_store_dir() / "providers.json"


def load_providers_config() -> Dict[str, Any]:
    path = get_providers_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def get_active_provider() -> Optional[Dict[str, Any]]:
    config = load_providers_config()
    if not config:
        return None
    active_id = config.get("active_id", "")
    providers = config.get("providers", [])
    for p in providers:
        if p.get("id") == active_id:
            return p
    return providers[0] if providers else None
