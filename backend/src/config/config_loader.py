# config_loader.py

import yaml
from pathlib import Path

# 設定ファイルのパス
CONFIG_PATH = Path(__file__).parent / "settings.yaml"

def load_config() -> dict:
    """YAML設定ファイルを読み込む"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# グローバルで一度ロードしておく
config = load_config()
