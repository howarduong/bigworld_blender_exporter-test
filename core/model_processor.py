# 文件位置: bigworld_blender_exporter/core/model_processor.py
# Model data processing for BigWorld export (aligned to official .primitives/.visual requirements)

import bpy
import bmesh
from mathutils import Vector
from ..utils import logger, math_utils
from ..utils.validation import validate_mesh, validate_armature
from ..utils.vertex_compression import (
    compress_dir_to_u16x2,
    quantize_weights_3,
    quantize_indices_3,
)
from .. import config


class ModelProcessor:
    """负责模型数据的收集与处理"""

    def __init__(self):
        pass

    def process(self, obj, settings):
        logger.info(f"Processing mesh object: {obj.name}")

        # 验证 mesh
        valid, msg = validate_mesh(obj)
        if not valid:
            logger.error(f"Mesh validation failed for {obj.name}: {msg}")
            return None

        mesh = obj.data

        # 应用 modifiers
        if settings.apply_modifiers:
            mesh = self._apply_modifiers(obj, mesh)

        # 三角化
        if settings.triangulate_mesh:
            mesh = self._triangulate_mesh(mesh)

        mesh.calc_loop_triangles()

        # 收集顶点数据
        vertices, indices, groups = self._collect_geometry(obj, mesh, settings)

        # 计算 bounding box
        bbox_min, bbox_max = math_utils.calculate_bounding_box(vertices)
        extent = math_utils.calculate_extent(bbox_min, bbox_max)

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

    def _collect_geometry(self, obj, mesh, settings):
        vertices = []
        indices = []
        primitive_groups = []

        uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        armature = obj.find_armature()
        vertex_groups = obj.vertex_groups

        # 按材质分组
        mat_to_group = {}
        for tri in mesh.loop_triangles:
            mat_index = tri.material_index
            if mat_index not in mat_to_group:
                mat_to_group[mat_index] = {
                    "startIndex": len(indices),
                    "numPrims": 0,
                    "startVertex": len(vertices),
                    "numVertices": 0,
                    "material": None,  # 稍后由 material_processor 填充
                }

            for loop_index in tri.loops:
                loop = mesh.loops[loop_index]
                v = mesh.vertices[loop.vertex_index]

                # 位置
                pos = list(v.co)
                if settings.coordinate_system == "Y_UP":
                    pos = math_utils.convert_position(pos)

                # 法线
                nrm = list(loop.normal)
                if settings.coordinate_system == "Y_UP":
                    nrm = math_utils.convert_direction(nrm)

                # UV
                uv = [0.0, 0.0]
                if uv_layer:
                    uv = [uv_layer[loop_index].uv[0], uv_layer[loop_index].uv[1]]

                # 骨骼权重
                bone_idx, bone_w = [0, 0, 0], [0.0, 0.0, 0.0]
                if armature and vertex_groups:
                    bone_data = self._get_vertex_bone_weights(v, vertex_groups, armature)
                    bone_idx, bone_w = bone_data["indices"], bone_data["weights"]

                # 压缩权重
                q0, q1, q2 = quantize_weights_3(bone_w)
                b0, b1, b2 = quantize_indices_3(bone_idx)

                # 切线/副法线（简化）
                tangent = [1.0, 0.0, 0.0]
                binormal = [0.0, 1.0, 0.0]

                vertex_data = {
                    "position": pos,
                    "normal": nrm,
                    "uv": uv,
                    "bone_idx": [b0, b1, b2],
                    "bone_w": [q0, q1, q2],
                    "tangent": tangent,
                    "binormal": binormal,
                }
                vertices.append(vertex_data)
                indices.append(len(vertices) - 1)

            mat_to_group[mat_index]["numPrims"] += 1
            mat_to_group[mat_index]["numVertices"] = len(vertices) - mat_to_group[mat_index]["startVertex"]

        # 转换为列表
        for g in mat_to_group.values():
            primitive_groups.append(g)

        return vertices, indices, primitive_groups

    def _get_vertex_bone_weights(self, vertex, vertex_groups, armature):
        influences = []
        for group in vertex.groups:
            if group.weight > 0:
                group_name = vertex_groups[group.group].name
                bone_index = self._find_bone_index(armature, group_name)
                if bone_index >= 0:
                    influences.append((bone_index, group.weight))
        influences.sort(key=lambda x: x[1], reverse=True)
        influences = influences[:3]
        total = sum(w for _, w in influences)
        if total > 0:
            influences = [(i, w / total) for i, w in influences]
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


def register():
    pass

def unregister():
    pass
