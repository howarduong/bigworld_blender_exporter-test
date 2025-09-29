import os
import struct
import bpy
import bmesh
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger

LOG = setup_logger()

def write_primitives_binary(obj, tmp_res_root, rel_primitives_dir="primitives", config=None):
    """
    写出二进制 .primitives 文件，符合 BigWorld File Grammar Guide
    """
    if config is None:
        config = {}
    out_dir = os.path.join(tmp_res_root, rel_primitives_dir)
    ensure_dir(out_dir)

    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    mesh = obj_eval.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()

    mesh.calc_normals_split()
    mesh.calc_tangents()

    verts = []
    indices = []
    vert_map = {}
    idx_counter = 0
    groups = {}

    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None

    for poly in mesh.polygons:
        tri = []
        for li in poly.loop_indices:
            loop = mesh.loops[li]
            v = mesh.vertices[loop.vertex_index]
            co = (v.co.x, v.co.y, v.co.z)
            n = (loop.normal.x, loop.normal.y, loop.normal.z)
            uv = (0.0, 0.0)
            if uv_layer:
                uv = (uv_layer[li].uv.x, uv_layer[li].uv.y)
            tangent = (loop.tangent.x, loop.tangent.y, loop.tangent.z, loop.bitangent_sign)
            key = (co, n, uv, tangent)
            if key not in vert_map:
                vert_map[key] = idx_counter
                verts.append((co, n, uv, tangent))
                idx_counter += 1
            tri.append(vert_map[key])
        midx = poly.material_index
        groups.setdefault(midx, []).append(tri)

    vcount = len(verts)
    icount = sum(len(g) for g in groups.values()) * 3
    index_format = "H" if vcount < 65535 else "I"

    base = f"{obj.name}_base"
    prim_fname = f"{base}.primitives"
    prim_path = os.path.join(out_dir, prim_fname)

    with open(prim_path, "wb") as f:
        # header
        f.write(struct.pack("<I", vcount))
        f.write(struct.pack("<I", icount))
        # vertices
        for co, n, uv, t in verts:
            f.write(struct.pack("<3f3f2f4f", *co, *n, *uv, *t))
        # indices
        for midx, tris in groups.items():
            for tri in tris:
                for idx in tri:
                    f.write(struct.pack("<" + index_format, idx))

    rel = normalize_path(os.path.join(rel_primitives_dir, prim_fname))
    LOG.info(f"[primitives-binary] {obj.name} v={vcount} i={icount}")
    return {
        "file": rel,
        "vertex_count": vcount,
        "index_count": icount,
        "groups": groups
    }
