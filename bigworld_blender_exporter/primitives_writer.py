import os
import math
import struct
import bpy
import bmesh
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def triangulate_mesh(obj):
    """Return a temporary mesh datablock that is triangulated and has applied transforms."""
    me = obj.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me)
    bm.free()
    return me

def gather_mesh_data(obj, calc_tangent=False):
    """Collect vertex attributes and per-face indices. Returns dict with vertices list and groups."""
    # Ensure evaluated depsgraph for modifiers
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    mesh = obj_eval.to_mesh()
    # Triangulate if needed
    # Use bmesh triangulation on a copy if faces are n-gons
    # For simplicity, use mesh already triangulated by modifiers or above
    verts = []
    vert_map = {}  # (co, normal, uv) -> index
    indices = []
    material_groups = {}  # mat_index -> list of triangles as indices into final index buffer
    # Ensure active UV layer
    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
    has_uv = uv_layer is not None
    # Normals
    mesh.calc_normals_split()
    if calc_tangent and has_uv:
        try:
            mesh.calc_tangents()
        except Exception:
            LOG.warning("calc_tangents failed")
            calc_tangent = False
    loop_index_to_vertex_index = {}
    idx_counter = 0
    for poly in mesh.polygons:
        if len(poly.loop_indices) != 3:
            # fallback: triangulate using bmesh
            LOG.debug(f"Non-tri poly found on {obj.name}, count {len(poly.loop_indices)}")
        tri = []
        for lidx in poly.loop_indices:
            loop = mesh.loops[lidx]
            v = mesh.vertices[loop.vertex_index]
            co = (round(v.co.x,6), round(v.co.y,6), round(v.co.z,6))
            normal = (round(loop.normal.x,6), round(loop.normal.y,6), round(loop.normal.z,6))
            uv = (0.0, 0.0)
            if has_uv:
                uv = (round(uv_layer[lidx].uv.x,6), round(uv_layer[lidx].uv.y,6))
            tangent = (0.0,0.0,0.0,0.0)
            if calc_tangent and hasattr(loop, "tangent"):
                tangent = (round(loop.tangent.x,6), round(loop.tangent.y,6), round(loop.tangent.z,6), round(loop.bitangent_sign if hasattr(loop, "bitangent_sign") else 1.0,6))
            key = (co, normal, uv, tangent)
            if key not in vert_map:
                vert_map[key] = idx_counter
                verts.append({"co":co, "normal":normal, "uv":uv, "tangent":tangent})
                idx_counter += 1
            tri.append(vert_map[key])
        # add tri to material group
        midx = poly.material_index
        if midx not in material_groups:
            material_groups[midx] = []
        material_groups[midx].extend(tri)
    # cleanup
    obj_eval.to_mesh_clear()
    vertex_count = len(verts)
    index_count = sum(len(v) for v in material_groups.values())
    return {
        "vertices": verts,
        "material_groups": material_groups,
        "vertex_count": vertex_count,
        "index_count": index_count,
        "has_uv": has_uv,
        "calc_tangent": calc_tangent
    }

def write_primitives_for_object(obj, tmp_res_root, rel_primitives_dir="primitives", config=None):
    """
    Writes primitives files for obj to tmp_res_root/<rel_primitives_dir> and returns metadata dict.
    metadata contains vertices_file (rel), indices_file (rel), vertex_count, index_count, vertex_format, index_format, primitive_groups
    """
    if config is None:
        config = {}
    out_dir = os.path.join(tmp_res_root, rel_primitives_dir)
    ensure_dir(out_dir)
    LOG.info(f"Writing primitives for object {obj.name} to {out_dir}")
    # compute tangent requirement
    need_tangent = config.get("normal_mapped", False)
    mesh_data = gather_mesh_data(obj, calc_tangent=need_tangent)
    verts = mesh_data["vertices"]
    material_groups = mesh_data["material_groups"]
    vertex_count = mesh_data["vertex_count"]
    index_count = mesh_data["index_count"]
    has_uv = mesh_data["has_uv"]
    calc_tangent = mesh_data["calc_tangent"]
    # choose index format
    index_format = "list" if vertex_count < 65535 else "list32"
    vertex_format = "xyznuv"
    if calc_tangent:
        vertex_format = "xyznuvt"  # t stands for tangent (packed)
    # write vertices file (text .vertices)
    base_name = f"{obj.name}_base"
    verts_fname = f"{base_name}.vertices"
    verts_path = os.path.join(out_dir, verts_fname)
    with open(verts_path, "w", encoding="utf-8") as vf:
        vf.write(f"vertex_format {vertex_format}\n")
        vf.write(f"vertex_count {vertex_count}\n")
        for v in verts:
            co = v["co"]
            n = v["normal"]
            uv = v["uv"]
            line = f"{co[0]} {co[1]} {co[2]} {n[0]} {n[1]} {n[2]} {uv[0]} {uv[1]}"
            if calc_tangent:
                t = v["tangent"]
                line += f" {t[0]} {t[1]} {t[2]} {t[3]}"
            vf.write(line + "\n")
    # write indices file (text .indices)
    indices_fname = f"{base_name}.indices"
    indices_path = os.path.join(out_dir, indices_fname)
    with open(indices_path, "w", encoding="utf-8") as inf:
        inf.write(f"index_format {index_format}\n")
        inf.write(f"index_count {index_count}\n")
        # primitive groups
        prim_count = len(material_groups)
        inf.write(f"primitive_group_count {prim_count}\n")
        # For each material group we will write start/num/start_vrtx/num_vrtx style
        # For simplicity we will list triangles consecutively per group
        cur_start = 0
        for midx, idx_list in material_groups.items():
            num_prims = len(idx_list) // 3
            # start vertex offset within this group's vertex stream = 0 (we use shared vertex buffer)
            inf.write(f"primitive_group {midx} {cur_start} {num_prims}\n")
            cur_start += num_prims
        # Now write triangles
        for midx, idx_list in material_groups.items():
            # write each triangle as three indices per line
            for i in range(0, len(idx_list), 3):
                a, b, c = idx_list[i], idx_list[i+1], idx_list[i+2]
                inf.write(f"{a} {b} {c}\n")
    # compute bounding box for the visual writer convenience
    xs = [v["co"][0] for v in verts] if verts else [0]
    ys = [v["co"][1] for v in verts] if verts else [0]
    zs = [v["co"][2] for v in verts] if verts else [0]
    bbox = {"min": (min(xs), min(ys), min(zs)), "max": (max(xs), max(ys), max(zs))}
    rel_verts = normalize_path(os.path.join(rel_primitives_dir, verts_fname))
    rel_indices = normalize_path(os.path.join(rel_primitives_dir, indices_fname))
    return {
        "vertices_file": rel_verts,
        "indices_file": rel_indices,
        "vertex_count": vertex_count,
        "index_count": index_count,
        "vertex_format": vertex_format,
        "index_format": index_format,
        "primitive_groups": [{"material_index": k, "triangle_count": len(v)//3} for k,v in material_groups.items()],
        "bounding_box": bbox
    }
