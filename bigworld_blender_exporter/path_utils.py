import os

def normalize_path(p: str) -> str:
    if not p:
        return ""
    p = p.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p.strip()

def exists_case_sensitive(path: str) -> bool:
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return False
    parts = path.split(os.sep)
    cur = parts[0]
    for part in parts[1:]:
        try:
            items = os.listdir(cur)
        except Exception:
            return False
        if part not in items:
            return False
        cur = os.path.join(cur, part)
    return True

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def find_fx_candidates(res_root: str, fx_name: str, search_dirs=None):
    fx_name = normalize_path(fx_name or "")
    if not fx_name:
        return []
    candidates = []
    if search_dirs is None:
        search_dirs = [
            "shaders/std_effects",
            "shaders",
            "shaders/environment",
            "shaders/characters",
            "shaders/particles",
            ""
        ]
    direct_full = os.path.join(res_root, fx_name)
    if os.path.exists(direct_full):
        rel = os.path.relpath(direct_full, res_root)
        return [normalize_path(rel)]
    basename = os.path.basename(fx_name)
    for sd in search_dirs:
        base = os.path.join(res_root, sd) if sd else res_root
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            for f in files:
                if f.lower() == basename.lower():
                    rel = os.path.relpath(os.path.join(root, f), res_root)
                    rel = normalize_path(rel)
                    if rel not in candidates:
                        candidates.append(rel)
    return candidates
