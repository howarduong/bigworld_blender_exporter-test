import os
from .path_utils import find_fx_candidates, normalize_path
from .config_utils import get_config, load_fx_map, load_fx_param_map

def resolve_fx_for_material(fx_hint: str, res_root: str, auto_mode=True, default_fx=None, material_name=None, shader_guess=None):
    cfg_default_fx = default_fx or get_config().get("default_fx", "shaders/std_effects/lightonly.fx")
    fx_hint = normalize_path(fx_hint or "")
    fx_map = load_fx_map()

    # 1) 直接路径
    if fx_hint:
        direct_full = os.path.normpath(os.path.join(res_root, fx_hint))
        if os.path.exists(direct_full):
            return (fx_hint, "ok", [fx_hint])

    # 2) 材质名映射
    if material_name and material_name in fx_map:
        mapped = normalize_path(fx_map[material_name])
        full = os.path.normpath(os.path.join(res_root, mapped))
        if os.path.exists(full):
            return (mapped, "candidate_used", [mapped])

    # 3) shader_guess 映射
    if shader_guess and shader_guess in fx_map:
        mapped = normalize_path(fx_map[shader_guess])
        full = os.path.normpath(os.path.join(res_root, mapped))
        if os.path.exists(full):
            return (mapped, "candidate_used", [mapped])

    # 4) 模糊搜索
    search_key = fx_hint or (material_name or "")
    candidates = find_fx_candidates(res_root, search_key)
    if candidates:
        return (candidates[0], "candidate_used", candidates)

    # 5) 默认 fx
    default_full = os.path.normpath(os.path.join(res_root, cfg_default_fx))
    if os.path.exists(default_full):
        return (normalize_path(cfg_default_fx), "default_used", [])

    return ("", "missing", [])

def map_texture_to_property(fx_path: str, tex_name_or_path: str) -> str:
    """
    根据 fx 参数表将贴图名称/路径映射到 shader property 名。
    """
    fx_params_map = load_fx_param_map()
    params = fx_params_map.get(normalize_path(fx_path), fx_params_map.get("shaders/std_effects/lightonly.fx", {}))
    key = "diffuse"
    low = tex_name_or_path.lower()
    if "normal" in low:
        key = "normal"
    elif "rough" in low:
        key = "roughness"
    elif "spec" in low or "gloss" in low or "metal" in low:
        key = "specular"
    elif "light" in low:
        key = "light"
    elif "detail" in low:
        key = "detail"
    return params.get(key, "diffuseMap")
