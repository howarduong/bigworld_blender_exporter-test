import os

def normalize_path(p: str) -> str:
    if not p:
        return ""
    p = p.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p.strip()

def exists_case_sensitive(path: str) -> bool:
    """
    严格大小写敏感存在性检查：逐级目录项比对名称。
    """
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return False
    parts = []
    # 处理盘符或根
    drive, tail = os.path.splitdrive(path)
    if drive:
        parts.append(drive + os.sep)
        rel = tail.lstrip(os.sep)
    else:
        if path.startswith(os.sep):
            parts.append(os.sep)
            rel = path[len(os.sep):]
        else:
            parts.append("")
            rel = path
    chunks = [c for c in rel.split(os.sep) if c]
    cur = parts[0] if parts[0] else chunks[0] if chunks else ""
    start_idx = 0 if parts[0] else 1
    for i in range(start_idx, len(chunks)):
        try:
            items = os.listdir(cur)
        except Exception:
            return False
        if chunks[i] not in items:
            return False
        cur = os.path.join(cur, chunks[i])
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
