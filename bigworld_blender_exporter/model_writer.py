import os
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def write_model_for_object(obj, visual_rel_path, tmp_res_root, rel_model_dir="models", bounding_box=None, material_names=None):
    out_dir = os.path.join(tmp_res_root, rel_model_dir)
    ensure_dir(out_dir)
    model_name = f"{obj.name}.model"
    model_path = os.path.join(out_dir, model_name)
    LOG.info(f"[model] write {model_path}")
    visual_base = os.path.splitext(os.path.basename(visual_rel_path))[0]
    bb_min = bounding_box["min"] if bounding_box else (-1,-1,-1)
    bb_max = bounding_box["max"] if bounding_box else (1,1,1)
    names = material_names or []

    with open(model_path, "w", encoding="utf-8") as mf:
        mf.write("<model>\n")
        mf.write(f"  nodefullVisual {visual_base}\n")
        # extent
        mf.write("  extent\n")
        mf.write(f"    {bb_min[0]} {bb_min[1]} {bb_min[2]}\n")
        mf.write(f"    {bb_max[0]} {bb_max[1]} {bb_max[2]}\n")
        mf.write("  endextent\n")
        # visibilityBox（与extent同）
        mf.write("  visibilityBox\n")
        mf.write(f"    {bb_min[0]} {bb_min[1]} {bb_min[2]}\n")
        mf.write(f"    {bb_max[0]} {bb_max[1]} {bb_max[2]}\n")
        mf.write("  endvisibilityBox\n")
        # materialNames
        mf.write("  materialNames\n")
        for n in names:
            mf.write(f"    {n}\n")
        mf.write("  endmaterialNames\n")
        # 占位：animations/actions
        mf.write("  animations\n")
        mf.write("  endanimations\n")
        mf.write("  actions\n")
        mf.write("  endactions\n")
        mf.write("</model>\n")

    rel = normalize_path(os.path.join(rel_model_dir, model_name))
    return rel
