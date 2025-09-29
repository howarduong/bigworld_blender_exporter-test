import os
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def write_model_for_object(obj, visual_rel_path, tmp_res_root, rel_model_dir="models"):
    """
    Writes a minimal .model referencing the visual_rel_path (relative to res root)
    visual_rel_path: e.g. visuals/MyMesh.visual (string)
    returns relative model path
    """
    out_dir = os.path.join(tmp_res_root, rel_model_dir)
    ensure_dir(out_dir)
    # model base name same as object
    model_name = f"{obj.name}.model"
    model_path = os.path.join(out_dir, model_name)
    LOG.info(f"Writing .model {model_path}")
    # Visual path should be without extension in some BigWorld samples; here we use base visual name
    visual_base = os.path.splitext(os.path.basename(visual_rel_path))[0]
    with open(model_path, "w", encoding="utf-8") as mf:
        mf.write("<model>\n")
        mf.write(f"  nodefullVisual {visual_base}\n")
        # extent placeholder (min max)
        mf.write("  extent\n")
        mf.write("    -1 -1 -1\n")
        mf.write("    1 1 1\n")
        mf.write("  endextent\n")
        mf.write("  materialNames\n")
        mf.write("  endmaterialNames\n")
        mf.write("</model>\n")
    rel = normalize_path(os.path.join(rel_model_dir, model_name))
    return rel
