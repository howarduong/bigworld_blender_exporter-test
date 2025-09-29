import os
from .path_utils import find_fx_candidates, normalize_path
from .config_utils import get_config, load_fx_map

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

    # 3) shader_guess（根据节点类型）
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

    # 6) 失败
    return ("", "missing", [])
