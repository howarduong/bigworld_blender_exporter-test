import os
import json
import configparser

CFG_PATH = os.path.join(os.path.dirname(__file__), "config", "exporter.cfg")
FX_MAP_PATH = os.path.join(os.path.dirname(__file__), "config", "fx_map.json")

DEFAULT_CFG = {
    "unitScale": "0.1",
    "materialKind": "0",
    "collisionFlags": "0",
    "bone_count": "17",
    "auto_fx_mode": "true",
    "default_fx": "shaders/std_effects/lightonly.fx",
    "res_root": "res",
    "normal_mapped": "false"
}

def ensure_config():
    cfg = configparser.ConfigParser()
    if not os.path.exists(CFG_PATH):
        os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
        cfg["exporter"] = DEFAULT_CFG
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            cfg.write(f)
    cfg.read(CFG_PATH, encoding="utf-8")
    return cfg

def get_config():
    cfg = ensure_config()
    return cfg["exporter"]

def load_fx_map():
    if not os.path.exists(FX_MAP_PATH):
        return {}
    try:
        return json.load(open(FX_MAP_PATH, "r", encoding="utf-8"))
    except Exception:
        return {}
