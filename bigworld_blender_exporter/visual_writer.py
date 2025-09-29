import os
import bpy
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger
from .fx_checker import map_texture_to_property

LOG = setup_logger()

def _write_matrix(vf, m):
    vf.write(f"      {m[0][0]} {m[0][1]} {m[0][2]} {m[0][3]}\n")
    vf.write(f"      {m[1][0]} {m[1][1]} {m[1][2]} {m[1][3]}\n")
    vf.write(f"      {m[2][0]} {m[2][1]} {m[2][2]} {m[2][3]}\n")
    vf.write(f"      {m[3][0]} {m[3][1]} {m[3][2]} {m[3][3]}\n")

def _collect_hierarchy(obj):
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
        # property 写入（严格使用 fx 参数映射）
        for t in mat_info.get("textures", []):
            pname = map_texture_to_property(fx or "shaders/std_effects/lightonly.fx", t)
            vf.write("        property\n")
            vf.write(f"          string {pname} {t}\n")
            vf.write("        endproperty\n")
        vf.write("      endEffectMaterial\n")
    vf.write("    endmaterial\n")

def write_visual_for_object(obj, primitives_meta, material_fx_map, tmp_res_root, rel_visual_dir="visuals", materialKind=0, collisionFlags=0, force_static_hierarchy=True):
    out_dir = os.path.join(tmp_res_root, rel_visual_dir)
    ensure_dir(out_dir)
    visual_basename = f"{obj.name}.visual"
    visual_path = os.path.join(out_dir, visual_basename)
    LOG.info(f"[visual] write {visual_path}")

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

        # 节点层级（Static with nodes）
        nodes = _collect_hierarchy(obj) if force_static_hierarchy else [obj]
        for node in nodes:
            try:
                mat_local = node.matrix_local
            except Exception:
                mat_local = bpy.Matrix.Identity(4)
            vf.write("  node\n")
            vf.write(f"    {node.name}\n")
            vf.write("    transform\n")
            _write_matrix(vf, mat_local)
            # 只在主节点挂几何；子节点为空节点（可按需扩展为每子节点挂几何）
            if node == obj:
                vf.write("    renderSet\n")
                vf.write("      geometry\n")
                vf.write("        base\n")
                vf.write("        primitive\n")
                if "file" in primitives_meta and primitives_meta["file"]:
                    vf.write(f"          resource {primitives_meta['file']}\n")
                else:
                    vf.write(f"          vertices {primitives_meta['vertices_file']}\n")
                    vf.write(f"          indices {primitives_meta['indices_file']}\n")
                vf.write("        endprimitive\n")
                vf.write("      endgeometry\n")
                vf.write("    endrenderSet\n")
                _write_materials(vf, primitives_meta, material_fx_map)

        # boundingBox + materialKind/collisionFlags（全局）
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
