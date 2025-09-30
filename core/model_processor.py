# 文件位置: bigworld_blender_exporter/core/model_processor.py
# Model data processing for BigWorld export (aligned to official .primitives/.visual requirements)

import bpy
import bmesh
from mathutils import Vector
from ..utils import logger, math_utils
from ..utils.validation import validate_mesh
from .. import config


class ModelProcessor:
    """负责模型数据的收集与处理"""

    def __init__(self):
        pass

    def process(self, obj, settings):
            """
            收集并处理一个 Blender Mesh 对象，返回用于 .primitives/.visual 的数据包。
            返回结构：
              {
                "vertices": List[Dict],          # 每顶点属性：position/normal/uv/tangent/binormal/bone_idx/bone_w
                "indices": List[int],            # 三角形索引，按材质分组但连续写入
                "primitive_groups": List[Tuple], # (startIndex, numPrims, startVertex, numVertices)
                "bbox_min": "x y z",
                "bbox_max": "x y z",
                "extent": float,
                "vertex_count": int,
                "triangle_count": int,
                "has_armature": bool,
                "materials": List[Dict],         # [{ name, index }]
              }
            """
            logger.info(f"Processing mesh object: {obj.name}")

            # 验证
            valid, msg = validate_mesh(obj)
            if not valid:
                logger.error(f"Mesh validation failed for {obj.name}: {msg}")
                return None

            mesh = obj.data

            # 应用 modifiers
            if getattr(settings, "apply_modifiers", True):
                mesh = self._apply_modifiers(obj, mesh)

            # 三角化
            if getattr(settings, "triangulate_mesh", True):
                mesh = self._triangulate_mesh(mesh)

            # 计算三角形与切线
            mesh.calc_loop_triangles()
            self._ensure_tangents(mesh)

            # 收集几何数据
            vertices, indices, groups = self._collect_geometry(obj, mesh, settings)

            # 计算包围盒与 extent（字符串形式符合 .visual/.model）
            bbox_min_vec, bbox_max_vec = math_utils.calculate_bounding_box(vertices)
            extent = math_utils.calculate_extent(bbox_min_vec, bbox_max_vec)
            bbox_min = f"{bbox_min_vec[0]:.6f} {bbox_min_vec[1]:.6f} {bbox_min_vec[2]:.6f}"
            bbox_max = f"{bbox_max_vec[0]:.6f} {bbox_max_vec[1]:.6f} {bbox_max_vec[2]:.6f}"

            model_data = {
                "vertices": vertices,
                "indices": indices,
                "primitive_groups": groups,
                "bbox_min": bbox_min,
                "bbox_max": bbox_max,
                "extent": extent,
                "vertex_count": len(vertices),
                "triangle_count": len(indices) // 3,
                "has_armature": obj.find_armature() is not None,
                "materials": self._collect_materials(obj),
            }

            logger.info(f"Processed {len(vertices)} vertices and {len(indices)} indices for {obj.name}")
            return model_data

    def _apply_modifiers(self, obj, mesh):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        return obj_eval.to_mesh()

    def _triangulate_mesh(self, mesh):
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        return mesh

    def _ensure_tangents(self, mesh):
        # 在有 UV 的情况下计算切线，以便写入 .primitives
        if mesh.uv_layers.active:
            try:
                mesh.calc_tangents()
            except Exception:
                # 某些情况下（无足够 UV/法线）会失败，保持切线为空即可
                pass

    def _collect_geometry(self, obj, mesh, settings):
        vertices = []
        indices = []
        primitive_groups = []

        uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        armature = obj.find_armature()
        vertex_groups = obj.vertex_groups if obj.vertex_groups else None

        # 按材质分组，跟踪组起始与统计
        mat_to_group = {}

        # 遍历每个三角形
        for tri in mesh.loop_triangles:
            mat_index = tri.material_index if tri.material_index is not None else -1

            # 初始化材质组
            if mat_index not in mat_to_group:
                mat_to_group[mat_index] = {
                    "startIndex": len(indices),
                    "numPrims": 0,
                    "startVertex": len(vertices),
                    "numVertices": 0,
                    "material": self._material_name(obj, mat_index),
                }

            # 为三角形的3个顶点构建顶点数据
            tri_vertex_indices = []
            for loop_index in tri.loops:
                loop = mesh.loops[loop_index]
                v = mesh.vertices[loop.vertex_index]

                # 位置
                pos = list(v.co)
                if getattr(settings, "coordinate_system", "Z_UP") == "Y_UP":
                    pos = math_utils.convert_position(pos)

                # 法线（优先用 loop.normal）
                nrm = list(loop.normal) if hasattr(loop, "normal") else list(v.normal)
                if getattr(settings, "coordinate_system", "Z_UP") == "Y_UP":
                    nrm = math_utils.convert_direction(nrm)

                # UV
                uv = [0.0, 0.0]
                if uv_layer:
                    uv = [uv_layer[loop_index].uv[0], uv_layer[loop_index].uv[1]]

                # 切线/副法线
                tangent = [1.0, 0.0, 0.0]
                binormal = [0.0, 1.0, 0.0]
                if hasattr(loop, "tangent"):
                    t = Vector(loop.tangent)
                    tangent = [t.x, t.y, t.z]

                    # binormal 由法线与切线计算，并考虑 bitangent_sign
                    # b = sign * normalize(cross(n, t))
                    try:
                        n_vec = Vector(nrm).normalized()
                        t_vec = t.normalized()
                        b_vec = n_vec.cross(t_vec)
                        sign = getattr(loop, "bitangent_sign", 1.0)
                        b_vec = b_vec * sign
                        binormal = [b_vec.x, b_vec.y, b_vec.z]
                    except Exception:
                        pass

                # 骨骼权重（最多3个）
                bone_idx = [0, 0, 0]
                bone_w = [0.0, 0.0, 0.0]
                if armature and vertex_groups:
                    indices_w = self._get_vertex_bone_weights(v, vertex_groups, armature)
                    bone_idx, bone_w = indices_w["indices"], indices_w["weights"]

                vertex_data = {
                    "position": pos,
                    "normal": nrm,
                    "uv0": uv,            # primitives_format 支持 uv0/uv
                    "tangent": tangent,
                    "binormal": binormal,
                    "bone_idx": bone_idx, # 原始索引（后续在 primitives_format 中量化）
                    "bone_w": bone_w,     # 原始权重（后续在 primitives_format 中量化）
                }

                vertices.append(vertex_data)
                tri_vertex_indices.append(len(vertices) - 1)

            # 将三角形索引写入（顺序为 0,1,2）
            indices.extend(tri_vertex_indices)

            # 三角形计数 +1（不是每个顶点）
            mat_to_group[mat_index]["numPrims"] += 1

            # 更新组内顶点数量
            mat_to_group[mat_index]["numVertices"] = (
                len(vertices) - mat_to_group[mat_index]["startVertex"]
            )

        # 转换为 (startIdx, numPrims, startVtx, numVtx) 结构
        for g in mat_to_group.values():
            primitive_groups.append(
                (g["startIndex"], g["numPrims"], g["startVertex"], g["numVertices"])
            )

        return vertices, indices, primitive_groups

    def _get_vertex_bone_weights(self, vertex, vertex_groups, armature):
        """提取一个顶点的骨骼权重（最多3个，归一化）"""
        influences = []
        for g in vertex.groups:
            if g.weight > 0:
                group_name = vertex_groups[g.group].name
                bone_index = self._find_bone_index(armature, group_name)
                if bone_index >= 0:
                    influences.append((bone_index, g.weight))

        # 取前三个最大权重
        influences.sort(key=lambda x: x[1], reverse=True)
        influences = influences[:3]

        # 归一化
        total = sum(w for _, w in influences)
        if total > 0:
            influences = [(i, w / total) for i, w in influences]

        # 填充到3个
        bone_indices = [i for i, _ in influences] + [0] * (3 - len(influences))
        bone_weights = [w for _, w in influences] + [0.0] * (3 - len(influences))

        return {"indices": bone_indices, "weights": bone_weights}

    def _find_bone_index(self, armature, bone_name):
        for i, bone in enumerate(armature.data.bones):
            if bone.name == bone_name:
                return i
        return -1

    def _collect_materials(self, obj):
        materials = []
        for i, mat_slot in enumerate(obj.material_slots):
            if mat_slot.material:
                mat = mat_slot.material
                materials.append({
                    "name": mat.name,
                    "index": i,
                })
        return materials

    def _material_name(self, obj, mat_index):
        if mat_index is None or mat_index < 0:
            return ""
        try:
            slot = obj.material_slots[mat_index]
            return slot.material.name if slot and slot.material else ""
        except Exception:
            return ""


def register():
    pass


def unregister():
    pass
