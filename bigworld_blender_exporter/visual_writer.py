import os
import bpy
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def _write_matrix(vf, m):
    vf.write(f"      {m[0][0]} {m[0][1]} {m[0][2]} {m[0][3]}\n")
    vf.write(f"      {m[1][0]} {m[1][1]} {m[1][2]} {m[1][3]}\n")
    vf.write(f"      {m[2][0]} {m[2][1]} {m[2][2]} {m[2][3]}\n")
    vf.write(f"      {m[3][0]} {m[3][1]} {m[3][2]} {m[3][3]}\n")

def _collect_hierarchy(obj):
    # 简化：仅导出选中对象一层（可扩展为递归导出 Static with nodes）
    return [obj]

def write_visual_for_object(obj, primitives_meta, material_fx_map, tmp_res_root, rel_visual_dir="visuals", materialKind=0, collisionFlags=0):
    out_dir = os.path.join(tmp_res_root, rel_visual_dir)
    ensure_dir(out_dir)
    visual_basename = f"{obj.name}.visual"
    visual_path = os.path.join(out_dir, visual_basename)
    LOG.info(f"[visual] write {visual_path}")

    try:
        mat_local = obj.matrix_local
    except Exception:
        mat_local = bpy.Matrix.Identity(4)

    with open(visual_path, "w", encoding="utf-8") as vf:
        vf.write("version\n")
        vf.write("  1\n")
        vf.write("NodeSection\n")
        vf.write("SceneRoot\n")
        vf.write("  transform\n")
        vf.write("    1 0 0 0\n")
        vf.write("    0 1 0 0\n")
        vf.write("    0 0 1 0\n")
        vf.write("    0 0 0 1\n")
        # 节点（可扩展多节点层级）
        vf.write("  node\n")
        vf.write(f"    {obj.name}\n")
        vf.write("    transform\n")
        _write_matrix(vf, mat_local)
        # 几何引用
        vf.write("    geometry\n")
        vf.write("      base\n")
        vf.write("      primitive\n")
        vf.write(f"        vertices {primitives_meta['vertices_file']}\n")
        vf.write(f"        indices {primitives_meta['indices_file']}\n")
        vf.write("      endprimitive\n")
        # 材质与属性
        vf.write("    material\n")
        for pg in primitives_meta.get("primitive_groups", []):
            midx = pg["material_index"]
            mat_info = material_fx_map.get(midx, {})
            identifier = mat_info.get("name", f"mat_{midx}")
            fx = mat_info.get("fx", "")
            vf.write(f"      EffectMaterial {identifier}\n")
            if fx:
                vf.write(f"        fx {fx}\n")
            # property 名映射（根据材质节点粗略判断）
            # 这里使用通用名：diffuseMap/normalMap/specularMap/roughnessMap
            # 如果 textures 列表中有“normal”命名，映射为 normalMap
            for t in mat_info.get("textures", []):
                lower = t.lower()
                if "normal" in lower:
                    pname = "normalMap"
                elif "rough" in lower:
                    pname = "roughnessMap"
                elif "spec" in lower or "gloss" in lower or "metal" in lower:
                    pname = "specularMap"
                else:
                    pname = "diffuseMap"
                vf.write("        property\n")
                vf.write(f"          string {pname} {t}\n")
                vf.write("        endproperty\n")
            vf.write("      endEffectMaterial\n")
        vf.write("    endmaterial\n")
        # boundingBox + materialKind/collisionFlags
        bb = primitives_meta.get("bounding_box", {"min":(0,0,0),"max":(0,0,0)})
        vf.write("  boundingBox\n")
        vf.write(f"    {bb['min'][0]} {bb['min'][1]} {bb['min'][2]}\n")
        vf.write(f"    {bb['max'][0]} {bb['max'][1]} {bb['max'][2]}\n")
        vf.write("  materialKind\n")
        vf.write(f"    {materialKind}\n")
        vf.write("  collisionFlags\n")
        vf.write(f"    {collisionFlags}\n")
        vf.write("EndNodeSection\n")

    rel = normalize_path(os.path.join(rel_visual_dir, visual_basename))
    return rel
