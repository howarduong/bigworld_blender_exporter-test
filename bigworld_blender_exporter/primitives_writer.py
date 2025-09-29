import os
import bpy
import bmesh
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def triangulate_eval_mesh(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    mesh = obj_eval.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(mesh)
    bm.free()
    return obj_eval, mesh

def gather_mesh_data(obj, need_tangent=False):
    obj_eval, mesh = triangulate_eval_mesh(obj)
    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
    has_uv = uv_layer is not None
    mesh.calc_normals_split()
    if need_tangent and has_uv:
        try:
            mesh.calc_tangents()
        except Exception:
            LOG.warning("calc_tangents failed; fallback without tangent")
            need_tangent = False

    verts = []
    vert_map = {}
    idx_counter = 0
    material_groups = {}

    for poly in mesh.polygons:
        if len(poly.loop_indices) != 3:
            LOG.debug(f"Non-tri polygon on {obj.name} count={len(poly.loop_indices)}")
        tri = []
        for li in poly.loop_indices:
            loop = mesh.loops[li]
            v = mesh.vertices[loop.vertex_index]
            co = (round(v.co.x,6), round(v.co.y,6), round(v.co.z,6))
            n = (round(loop.normal.x,6), round(loop.normal.y,6), round(loop.normal.z,6))
            uv = (0.0, 0.0)
            if has_uv:
                uv = (round(uv_layer[li].uv.x,6), round(uv_layer[li].uv.y,6))
            tangent = (0.0,0.0,0.0,1.0)
            if need_tangent and hasattr(loop, "tangent"):
                tangent = (
                    round(loop.tangent.x,6),
                    round(loop.tangent.y,6),
                    round(loop.tangent.z,6),
                    round(getattr(loop, "bitangent_sign", 1.0),6)
                )
            key = (co, n, uv, tangent if need_tangent else None)
            if key not in vert_map:
                vert_map[key] = idx_counter
                verts.append({"co":co, "n":n, "uv":uv, "t":tangent if need_tangent else None})
                idx_counter += 1
            tri.append(vert_map[key])
        midx = poly.material_index
        if midx not in material_groups:
            material_groups[midx] = []
        material_groups[midx].extend(tri)

    # bbox
    xs = [v["co"][0] for v in verts] if verts else [0]
    ys = [v["co"][1] for v in verts] if verts else [0]
    zs = [v["co"][2] for v in verts] if verts else [0]
    bbox = {"min": (min(xs), min(ys), min(zs)), "max": (max(xs), max(ys), max(zs))}
    obj_eval.to_mesh_clear()

    return {
        "vertices": verts,
        "material_groups": material_groups,
        "vertex_count": len(verts),
        "index_count": sum(len(v) for v in material_groups.values()),
        "has_uv": has_uv,
        "need_tangent": need_tangent,
        "bounding_box": bbox
    }

def write_primitives_for_object(obj, tmp_res_root, rel_primitives_dir="primitives", config=None):
    if config is None:
        config = {}
    out_dir = os.path.join(tmp_res_root, rel_primitives_dir)
    ensure_dir(out_dir)
    need_tangent = bool(config.get("normal_mapped", False))
    data = gather_mesh_data(obj, need_tangent=need_tangent)

    verts = data["vertices"]
    groups = data["material_groups"]
    vcount = data["vertex_count"]
    icount = data["index_count"]
    index_format = "list" if vcount < 65535 else "list32"
    vertex_format = "xyznuv" + ("t" if data["need_tangent"] else "")

    base = f"{obj.name}_base"
    verts_fname = f"{base}.vertices"
    idx_fname = f"{base}.indices"
    verts_path = os.path.join(out_dir, verts_fname)
    idx_path = os.path.join(out_dir, idx_fname)

    # vertices
    with open(verts_path, "w", encoding="utf-8") as vf:
        vf.write(f"vertex_format {vertex_format}\n")
        vf.write(f"vertex_count {vcount}\n")
        for v in verts:
            co, n, uv = v["co"], v["n"], v["uv"]
            line = f"{co[0]} {co[1]} {co[2]} {n[0]} {n[1]} {n[2]} {uv[0]} {uv[1]}"
            if v["t"] is not None:
                t = v["t"]
                line += f" {t[0]} {t[1]} {t[2]} {t[3]}"
            vf.write(line + "\n")

    # indices + primitive groups
    with open(idx_path, "w", encoding="utf-8") as inf:
        inf.write(f"index_format {index_format}\n")
        inf.write(f"index_count {icount}\n")
        inf.write(f"primitive_group_count {len(groups)}\n")
        # 写每组的起始与数量（单位：三角形）
        start_tri = 0
        group_table = []
        for midx, idxs in groups.items():
            tri_count = len(idxs) // 3
            inf.write(f"primitive_group {midx} {start_tri} {tri_count}\n")
            group_table.append({"material_index": midx, "start": start_tri, "tri_count": tri_count})
            start_tri += tri_count
        # 写具体索引
        for midx, idxs in groups.items():
            for i in range(0, len(idxs), 3):
                a, b, c = idxs[i], idxs[i+1], idxs[i+2]
                inf.write(f"{a} {b} {c}\n")

    rel_verts = normalize_path(os.path.join(rel_primitives_dir, verts_fname))
    rel_indices = normalize_path(os.path.join(rel_primitives_dir, idx_fname))
    LOG.info(f"[primitives] {obj.name} v={vcount} i={icount} format(v={vertex_format}, i={index_format})")

    return {
        "vertices_file": rel_verts,
        "indices_file": rel_indices,
        "vertex_count": vcount,
        "index_count": icount,
        "vertex_format": vertex_format,
        "index_format": index_format,
        "primitive_groups": group_table,
        "bounding_box": data["bounding_box"]
    }
