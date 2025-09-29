import os
import json
import configparser

CFG_PATH = os.path.join(os.path.dirname(__file__), "config", "exporter.cfg")
FX_MAP_PATH = os.path.join(os.path.dirname(__file__), "config", "fx_map.json")
FX_PARAM_MAP_PATH = os.path.join(os.path.dirname(__file__), "config", "fx_param_map.json")

DEFAULT_CFG = {
    "unitScale": "0.01",
    "materialKind": "0",
    "collisionFlags": "0",
    "bone_count": "17",
    "auto_fx_mode": "true",
    "default_fx": "shaders/std_effects/lightonly.fx",
    "res_root": "res",
    "normal_mapped": "true",
    "primitives_binary": "true",
    "prefer_dds": "true",
    "max_uv_layers": "2",
    "force_static_hierarchy": "true",
    "strict_case_check": "true"
}

DEFAULT_FX_PARAM_MAP = {
    "shaders/std_effects/lightonly.fx": {
        "diffuse": "diffuseMap",
        "normal": "normalMap",
        "specular": "specularMap",
        "roughness": "roughnessMap",
        "metallic": "specularMap",
        "light": "lightMap",
        "detail": "detailMap"
    }
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

def load_json(path: str, default_obj=None):
    if not os.path.exists(path):
        return default_obj if default_obj is not None else {}
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except Exception:
        return default_obj if default_obj is not None else {}

def load_fx_map():
    return load_json(FX_MAP_PATH, {})

def load_fx_param_map():
    return load_json(FX_PARAM_MAP_PATH, DEFAULT_FX_PARAM_MAP)
