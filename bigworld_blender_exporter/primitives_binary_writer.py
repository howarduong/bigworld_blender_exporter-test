import os
import struct
import bpy
import bmesh
from math import isfinite
from .path_utils import ensure_dir, normalize_path
from .logger import setup_logger
from .config_utils import get_config

LOG = setup_logger()

def _safe_float(x: float) -> float:
    return float(x) if (x is not None and isfinite(x)) else 0.0

def _triangulate_eval_mesh(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    mesh = obj_eval.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(mesh)
    bm.free()
    return obj_eval, mesh

def _gather_binary_data(obj, need_tangent=True, max_uv_layers=2, unit_scale=1.0):
    obj_eval, mesh = _triangulate_eval_mesh(obj)
    uv_layers = mesh.uv_layers
    uv_count = min(len(uv_layers), max_uv_layers)
    mesh.calc_normals_split()
    if need_tangent and uv_count > 0:
        try:
            mesh.calc_tangents()
        except Exception:
            LOG.warning("calc_tangents failed; fallback without tangent")
            need_tangent = False

    uv_data_layers = [uv_layers[i].data for i in range(uv_count)] if uv_count > 0 else []

    verts = []
    vert_map = {}
    groups = {}

    for poly in mesh.polygons:
        tri = []
        for li in poly.loop_indices:
            loop = mesh.loops[li]
            v = mesh.vertices[loop.vertex_index]
            co = (round(_safe_float(v.co.x * unit_scale),6),
                  round(_safe_float(v.co.y * unit_scale),6),
                  round(_safe_float(v.co.z * unit_scale),6))
            n  = (round(_safe_float(loop.normal.x),6),
                  round(_safe_float(loop.normal.y),6),
                  round(_safe_float(loop.normal.z),6))
            uvs = []
            for uv_layer in uv_data_layers:
                uv = (round(_safe_float(uv_layer[li].uv.x),6),
                      round(_safe_float(uv_layer[li].uv.y),6))
                uvs.append(uv)
            t = None
            if need_tangent and hasattr(loop, "tangent"):
                t = (
                    round(_safe_float(loop.tangent.x),6),
                    round(_safe_float(loop.tangent.y),6),
                    round(_safe_float(loop.tangent.z),6),
                    round(_safe_float(getattr(loop, "bitangent_sign", 1.0)),6)
                )
            key = (co, n, tuple(uvs), t if need_tangent else None)
            if key not in vert_map:
                vert_map[key] = len(verts)
                verts.append({"co": co, "n": n, "uvs": uvs, "t": t})
            tri.append(vert_map[key])
        midx = poly.material_index
        groups.setdefault(midx, []).extend(tri)

    xs = [v["co"][0] for v in verts] if verts else [0.0]
    ys = [v["co"][1] for v in verts] if verts else [0.0]
    zs = [v["co"][2] for v in verts] if verts else [0.0]
    bbox = {"min": (min(xs), min(ys), min(zs)), "max": (max(xs), max(ys), max(zs))}

    obj_eval.to_mesh_clear()

    vcount = len(verts)
    tri_total = sum(len(v) for v in groups.values()) // 3
    icount = tri_total * 3
    return {
        "verts": verts,
        "groups": groups,
        "vertex_count": vcount,
        "index_count": icount,
        "uv_count": uv_count,
        "need_tangent": need_tangent,
        "bounding_box": bbox
    }

def write_primitives_binary(obj, tmp_res_root, rel_primitives_dir="primitives", config=None):
    """
    二进制 .primitives 写出：严格包含头、组表、顶点缓冲、索引缓冲。
    头格式（小端）：
      uint32 vertex_count
      uint32 index_count
      uint32 uv_count
      uint32 tangent_flag (0/1)
      uint32 group_count
      group_count * { uint32 material_index, uint32 start_tri, uint32 tri_count }
    顶点：
      float3 pos, float3 normal, uv_count * float2, [float4 tangent]
    索引：
      uint16/uint32（依据 vertex_count）
    """
    if config is None:
        config = {}
    out_dir = os.path.join(tmp_res_root, rel_primitives_dir)
    ensure_dir(out_dir)

    unit_scale = float(get_config().get("unitScale", 1.0))
    need_tangent = bool(config.get("normal_mapped", True))
    max_uv_layers = int(config.get("max_uv_layers", 2))

    data = _gather_binary_data(obj, need_tangent=need_tangent, max_uv_layers=max_uv_layers, unit_scale=unit_scale)
    vcount = data["vertex_count"]
    icount = data["index_count"]
    uv_count = data["uv_count"]
    tangent_flag = 1 if data["need_tangent"] else 0
    groups = data["groups"]

    index_is_16 = vcount < 65535
    index_fmt = "<H" if index_is_16 else "<I"

    base = f"{obj.name}_base"
    prim_fname = f"{base}.primitives"
    prim_path = os.path.join(out_dir, prim_fname)

    # 组表构造
    start_tri = 0
    group_table = []
    ordered_groups = []
    for midx, idxs in groups.items():
        tri_count = len(idxs) // 3
        group_table.append({"material_index": midx, "start": start_tri, "tri_count": tri_count})
        ordered_groups.append((midx, idxs))
        start_tri += tri_count

    with open(prim_path, "wb") as f:
        # header
        f.write(struct.pack("<I", vcount))
        f.write(struct.pack("<I", icount))
        f.write(struct.pack("<I", uv_count))
        f.write(struct.pack("<I", tangent_flag))
        f.write(struct.pack("<I", len(group_table)))
        for g in group_table:
            f.write(struct.pack("<III", int(g["material_index"]), int(g["start"]), int(g["tri_count"])))

        # vertex buffer
        for v in data["verts"]:
            co = v["co"]; n = v["n"]; uvs = v["uvs"]; t = v["t"]
            f.write(struct.pack("<3f3f", _safe_float(co[0]), _safe_float(co[1]), _safe_float(co[2]),
                                         _safe_float(n[0]), _safe_float(n[1]), _safe_float(n[2])))
            for i in range(uv_count):
                uv = uvs[i] if i < len(uvs) else (0.0, 0.0)
                f.write(struct.pack("<2f", _safe_float(uv[0]), _safe_float(uv[1])))
            if tangent_flag and t is not None:
                f.write(struct.pack("<4f", _safe_float(t[0]), _safe_float(t[1]), _safe_float(t[2]), _safe_float(t[3])))
            elif tangent_flag:
                f.write(struct.pack("<4f", 0.0, 0.0, 1.0, 1.0))

        # index buffer
        for midx, idxs in ordered_groups:
            for i in range(0, len(idxs), 3):
                a, b, c = idxs[i], idxs[i+1], idxs[i+2]
                f.write(struct.pack(index_fmt, int(a)))
                f.write(struct.pack(index_fmt, int(b)))
                f.write(struct.pack(index_fmt, int(c)))

    rel = normalize_path(os.path.join(rel_primitives_dir, prim_fname))
    LOG.info(f"[primitives-binary] {obj.name} v={vcount} i={icount} uv={uv_count} tangent={bool(tangent_flag)} idx16={index_is_16} unitScale={unit_scale}")
    return {
        "file": rel,
        "vertex_count": vcount,
        "index_count": icount,
        "primitive_groups": group_table,
        "bounding_box": data["bounding_box"],
        "uv_layer_count": uv_count,
        "tangent": bool(tangent_flag),
        "index_is_16": index_is_16
    }
