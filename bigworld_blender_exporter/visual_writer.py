import os
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def write_visual_for_object(obj, primitives_meta, material_fx_map, tmp_res_root, rel_visual_dir="visuals"):
    """
    primitives_meta: metadata returned from primitives_writer for this object
    material_fx_map: dict mapping material_slot_index -> { 'name': mat_name, 'fx': resolved_fx_relative_path, 'textures': [rel paths] }
    Writes a .visual file under tmp_res_root/<rel_visual_dir> and returns the relative base name.
    """
    out_dir = os.path.join(tmp_res_root, rel_visual_dir)
    ensure_dir(out_dir)
    visual_basename = f"{obj.name}.visual"
    visual_path = os.path.join(out_dir, visual_basename)
    LOG.info(f"Writing .visual {visual_path}")
    # Basic NodeSection with a Scene root and a mesh node
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
        vf.write("  node\n")
        vf.write(f"    {obj.name}\n")
        vf.write("    transform\n")
        # write object's local transform as identity (assume applied)
        vf.write("      1 0 0 0\n")
        vf.write("      0 1 0 0\n")
        vf.write("      0 0 1 0\n")
        vf.write("      0 0 0 1\n")
        vf.write("    geometry\n")
        vf.write("      base\n")
        # geometry details reference primitive files
        vf.write("      primitive\n")
        vf.write(f"        vertices {primitives_meta['vertices_file']}\n")
        vf.write(f"        indices {primitives_meta['indices_file']}\n")
        vf.write("      endprimitive\n")
        # materials / primitive groups
        vf.write("    material\n")
        for pg in primitives_meta.get("primitive_groups", []):
            midx = pg["material_index"]
            mat_info = material_fx_map.get(midx)
            if mat_info:
                identifier = mat_info.get("name", f"mat_{midx}")
                fx = mat_info.get("fx", "")
                vf.write(f"      EffectMaterial {identifier}\n")
                vf.write(f"        fx {fx}\n")
                # write texture properties if present
                for t in mat_info.get("textures", []):
                    vf.write(f"        property\n")
                    vf.write(f"          string texture {t}\n")
                    vf.write(f"        endproperty\n")
                vf.write(f"      endEffectMaterial\n")
            else:
                vf.write(f"      EffectMaterial mat_{midx}\n")
                vf.write("        fx shaders/std_effects/lightonly.fx\n")
                vf.write("      endEffectMaterial\n")
        vf.write("    endmaterial\n")
        # bounding box
        bb = primitives_meta.get("bounding_box", {"min":(0,0,0),"max":(0,0,0)})
        vf.write("  boundingBox\n")
        vf.write(f"    {bb['min'][0]} {bb['min'][1]} {bb['min'][2]}\n")
        vf.write(f"    {bb['max'][0]} {bb['max'][1]} {bb['max'][2]}\n")
        vf.write("EndNodeSection\n")
    rel = normalize_path(os.path.join(rel_visual_dir, visual_basename))
    return rel
