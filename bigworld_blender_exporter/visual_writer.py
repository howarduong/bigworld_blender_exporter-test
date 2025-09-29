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
    # 简单递归收集静态层级（Static with nodes）
    nodes = []
    def rec(o):
        nodes.append(o)
        for c in o.children:
            rec(c)
    rec(obj)
    return nodes

def _write_materials(vf, primitives_meta, material_fx_map):
    vf.write("    material\n")
    for pg in primitives_meta.get("primitive_groups", []):
        midx = pg["material_index"]
        mat_info = material_fx_map.get(midx, {})
        identifier = mat_info.get("name", f"mat_{midx}")
        fx = mat_info.get("fx", "")
        vf.write(f"      EffectMaterial {identifier}\n")
        if fx:
            vf.write(f"        fx {fx}\n")
        # property 写入（基于名称粗判；可替换为真实节点属性映射）
        for t in mat_info.get("textures", []):
            lower = t.lower()
            if "normal" in lower:
                pname = "normalMap"
            elif "rough" in lower:
                pname = "roughnessMap"
            elif "spec" in lower or "gloss" in lower or "metal" in lower:
                pname = "specularMap"
            elif "light" in lower:
                pname = "lightMap"
            elif "detail" in lower:
                pname = "detailMap"
            else:
                pname = "diffuseMap"
            vf.write("        property\n")
            vf.write(f"          string {pname} {t}\n")
            vf.write("        endproperty\n")
        vf.write("      endEffectMaterial\n")
    vf.write("    endmaterial\n")

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

        # 写主节点
        vf.write("  node\n")
        vf.write(f"    {obj.name}\n")
        vf.write("    transform\n")
        _write_matrix(vf, mat_local)

        # renderSet + geometry
        vf.write("    renderSet\n")
        vf.write("      geometry\n")
        vf.write("        base\n")
        vf.write("        primitive\n")
        # 兼容明文和二进制：二进制 meta['file']；明文 meta['vertices_file']/['indices_file']
        if "file" in primitives_meta and primitives_meta["file"]:
            vf.write(f"          resource {primitives_meta['file']}\n")
        else:
            vf.write(f"          vertices {primitives_meta['vertices_file']}\n")
            vf.write(f"          indices {primitives_meta['indices_file']}\n")
        vf.write("        endprimitive\n")
        vf.write("      endgeometry\n")
        vf.write("    endrenderSet\n")

        # 材质
        _write_materials(vf, primitives_meta, material_fx_map)

        # boundingBox + materialKind/collisionFlags
        bb = primitives_meta.get("bounding_box", {"min":(0,0,0),"max":(0,0,0)})
        vf.write("  boundingBox\n")
        vf.write(f"    {bb['min'][0]} {bb['min'][1]} {bb['min'][2]}\n")
        vf.write(f"    {bb['max'][0]} {bb['max'][1]} {bb['max'][2]}\n")
        vf.write("  materialKind\n")
        vf.write(f"    {materialKind}\n")
        vf.write("  collisionFlags\n")
        vf.write(f"    {collisionFlags}\n")

        # 可扩展：写子节点层级（本版仅写主节点；如需可递归 _collect_hierarchy(obj)）
        vf.write("EndNodeSection\n")

    rel = normalize_path(os.path.join(rel_visual_dir, visual_basename))
    return rel
