import os
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def write_model_for_object(obj, visual_rel_path, tmp_res_root,
                           rel_model_dir="models",
                           bounding_box=None,
                           material_names=None):
    """
    写出 BigWorld .model 文件，严格对齐官方规范：
    - 根标签 <model>
    - nodefullVisual: 只写基础名（不带路径、不带扩展名）
    - extent/visibilityBox: min/max 三维盒子
    - materialNames: 每个材质一个 <name>
    - skeleton/animations/actions: 空占位
    """
    out_dir = os.path.join(tmp_res_root, rel_model_dir)
    ensure_dir(out_dir)
    model_name = f"{obj.name}.model"
    model_path = os.path.join(out_dir, model_name)
    LOG.info(f"[model] write {model_path}")

    # 取 .visual 文件的基础名（不带扩展名）
    visual_base = os.path.splitext(os.path.basename(visual_rel_path))[0]

    # bounding box
    bb_min = bounding_box["min"] if bounding_box else (-1.0, -1.0, -1.0)
    bb_max = bounding_box["max"] if bounding_box else (1.0, 1.0, 1.0)

    # 材质名列表
    names = material_names or []

    with open(model_path, "w", encoding="utf-8") as mf:
        mf.write("<model>\n")

        # nodefullVisual
        mf.write(f"  <nodefullVisual> {visual_base} </nodefullVisual>\n")

        # materialNames
        mf.write("  <materialNames>\n")
        for n in names:
            mf.write(f"    <name> {n} </name>\n")
        mf.write("  </materialNames>\n")

        # extent
        mf.write("  <extent>\n")
        mf.write(f"    <min> {bb_min[0]} {bb_min[1]} {bb_min[2]} </min>\n")
        mf.write(f"    <max> {bb_max[0]} {bb_max[1]} {bb_max[2]} </max>\n")
        mf.write("  </extent>\n")

        # visibilityBox
        mf.write("  <visibilityBox>\n")
        mf.write(f"    <min> {bb_min[0]} {bb_min[1]} {bb_min[2]} </min>\n")
        mf.write(f"    <max> {bb_max[0]} {bb_max[1]} {bb_max[2]} </max>\n")
        mf.write("  </visibilityBox>\n")

        # skeleton / animations / actions
        mf.write("  <skeleton/>\n")
        mf.write("  <animations/>\n")
        mf.write("  <actions/>\n")

        mf.write("</model>\n")

    rel = normalize_path(os.path.join(rel_model_dir, model_name))
    return rel
