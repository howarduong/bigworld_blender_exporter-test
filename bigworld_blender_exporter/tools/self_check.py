import os, json, sys

def main():
    base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "tmp_export"))
    if not os.path.isdir(base):
        print("未找到 tmp_export 目录")
        return 1
    dirs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
    if not dirs:
        print("tmp_export 下不存在导出目录")
        return 1
    latest = sorted(dirs)[-1]
    tmp_dir = os.path.join(base, latest)
    res_root = os.path.join(tmp_dir, "res")
    manifest = os.path.join(tmp_dir, "export_manifest.json")
    if not os.path.exists(manifest):
        print("未找到清单文件 export_manifest.json")
        return 1
    data = json.load(open(manifest, "r", encoding="utf-8"))
    errors = []
    for em in data:
        pm = em.get("primitives", {})
        for rel in [pm.get("vertices_file",""), pm.get("indices_file",""), em.get("visual",""), em.get("model","")]:
            if not rel:
                errors.append(f"清单缺少路径：{rel}")
                continue
            full = os.path.normpath(os.path.join(res_root, rel))
            if not os.path.exists(full):
                errors.append(f"缺失文件 {full}")
    if errors:
        print("自检失败：")
        for e in errors:
            print(" -", e)
        return 2
    print("自检通过：所有文件存在")
    return 0

if __name__ == "__main__":
    sys.exit(main())
