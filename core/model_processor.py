# 文件位置: bigworld_blender_exporter/core/model_processor.py
# -*- coding: utf-8 -*-
"""
Model data processing for BigWorld export (aligned to official .primitives/.visual requirements)

改进点：
- 集成 collision_processor，生成 BSP 数据
- 集成 hardpoint_processor，收集 HardPoints 和 Portals
- 输出结构中增加 bsp_data / hardpoints / portals
"""

import bpy
import bmesh
from mathutils import Vector
from typing import Dict, Any
from ..utils import logger, math_utils
from ..utils.validation import validate_mesh
from .. import config
from .collision_processor import CollisionProcessor
from .hardpoint_processor import HardpointProcessor

LOG = logger.get_logger("model_processor")


class ModelProcessor:
    """负责模型数据的收集与处理"""

    def __init__(self):
        self.collision_proc = CollisionProcessor()
        self.hp_proc = HardpointProcessor()

    def process(self, obj, settings) -> Dict[str, Any]:
        """
        收集并处理一个 Blender Mesh 对象，返回用于 .primitives/.visual 的数据包。

        返回结构：
        {
          "vertices": List[Dict],
          "indices": List[int],
          "primitive_groups": List[Tuple],
          "bbox_min": "x y z",
          "bbox_max": "x y z",
          "extent": float,
          "vertex_count": int,
          "triangle_count": int,
          "has_armature": bool,
          "materials": List[Dict],
          "bsp_data": Dict,          # 碰撞 BSP 数据
          "hardpoints": List[Dict],  # HP_ 前缀对象
          "portals": List[Dict],     # PORTAL_ 前缀对象
        }
        """
        LOG.info(f"Processing mesh object: {obj.name}")

        # 验证
        valid, msg = validate_mesh(obj)
        if not valid:
            LOG.error(f"Mesh validation failed for {obj.name}: {msg}")
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

        # 计算包围盒与 extent
        bbox_min_vec, bbox_max_vec = math_utils.calculate_bounding_box(vertices)
        extent = math_utils.calculate_extent(bbox_min_vec, bbox_max_vec)
        bbox_min = f"{bbox_min_vec[0]:.6f} {bbox_min_vec[1]:.6f} {bbox_min_vec[2]:.6f}"
        bbox_max = f"{bbox_max_vec[0]:.6f} {bbox_max_vec[1]:.6f} {bbox_max_vec[2]:.6f}"

        # 碰撞 BSP
        bsp_data = {}
        if getattr(settings, "export_collision", True):
            bsp_data = self.collision_proc.collect_bsp_for_object(obj)

        # HardPoints & Portals
        hp_portals = self.hp_proc.collect(obj)

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
            "bsp_data": bsp_data,
            "hardpoints": hp_portals.get("hardpoints", []),
            "portals": hp_portals.get("portals", []),
        }

        LOG.info(f"Processed {len(vertices)} vertices and {len(indices)} indices for {obj.name}")
        return model_data

    # ------------------------
    # Internal helpers
    # ------------------------
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
        if mesh.uv_layers.active:
            try:
                mesh.calc_tangents()
            except Exception:
                pass

    def _collect_geometry(self, obj, mesh, settings):
        vertices = []
        indices = []
        primitive_groups = []
        uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        armature = obj.find_armature()
        vertex_groups = obj.vertex_groups if obj.vertex_groups else None

        mat_to_group = {}

        for tri in mesh.loop_triangles:
            mat_index = tri.material_index if tri.material_index is not None else -1
            if mat_index not in mat_to_group:
                mat_to_group[mat_index] = {
                    "startIndex": len(indices),
                    "numPrims": 0,
                    "startVertex": len(vertices),
                    "numVertices": 0,
                    "material": self._material_name(obj, mat_index),
                }

            tri_vertex_indices = []
            for loop_index in tri.loops:
                loop = mesh.loops[loop_index]
                v = mesh.vertices[loop.vertex_index]

                # 位置
                pos = list(v.co)
                if getattr(settings, "coordinate_system", "Z_UP") == "Y_UP":
                    pos = math_utils.convert_position(pos)

                # 法线
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
                    try:
                        n_vec = Vector(nrm).normalized()
                        t_vec = t.normalized()
                        b_vec = n_vec.cross(t_vec)
                        sign = getattr(loop, "bitangent_sign", 1.0)
                        b_vec = b_vec * sign
                        binormal = [b_vec.x, b_vec.y, b_vec.z]
                    except Exception:
                        pass

                # 骨骼权重
                bone_idx = [0, 0, 0]
                bone_w = [0.0, 0.0, 0.0]
                if armature and vertex_groups:
                    indices_w = self._get_vertex_bone_weights(v, vertex_groups, armature)
                    bone_idx, bone_w = indices_w["indices"], indices_w["weights"]

                vertex_data = {
                    "position": pos,
                    "normal": nrm,
                    "uv0": uv,
                    "tangent": tangent,
                    "binormal": binormal,
                    "bone_idx": bone_idx,
                    "bone_w": bone_w,
                }
                vertices.append(vertex_data)
                tri_vertex_indices.append(len(vertices) - 1)

            indices.extend(tri_vertex_indices)
            mat_to_group[mat_index]["numPrims"] += 1
            mat_to_group[mat_index]["numVertices"] = (
                len(vertices) - mat_to_group[mat_index]["startVertex"]
            )

        for g in mat_to_group.values():
            primitive_groups.append(
                (g["startIndex"], g["numPrims"], g["startVertex"], g["numVertices"])
            )

        return vertices, indices, primitive_groups

        def _get_vertex_bone_weights(self, vertex, vertex_groups, armature):
        """
        收集单个顶点的骨骼索引和权重，最多保留前三个影响。
        返回 dict: { "indices": [i0,i1,i2], "weights": [w0,w1,w2] }
        """
        influences = []
        for g in vertex.groups:
            if g.weight > 0:
                group_name = vertex_groups[g.group].name
                # 在 armature 中找到对应骨骼索引
                bone_index = -1
                if group_name in armature.data.bones:
                    bone_index = list(armature.data.bones.keys()).index(group_name)
                if bone_index >= 0:
                    influences.append((bone_index, g.weight))

        # 按权重排序，取前三个
        influences.sort(key=lambda x: x[1], reverse=True)
        influences = influences[:3]

        indices = [0, 0, 0]
        weights = [0.0, 0.0, 0.0]
        for i, (idx, w) in enumerate(influences):
            indices[i] = idx
            weights[i] = w

        # 归一化权重
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]

        return {"indices": indices, "weights": weights}

    def _material_name(self, obj, mat_index):
        if mat_index < 0 or mat_index >= len(obj.material_slots):
            return "default"
        mat = obj.material_slots[mat_index].material
        return mat.name if mat else "default"

    def _collect_materials(self, obj):
        """收集对象的材质名称列表"""
        mats = []
        for slot in obj.material_slots:
            if slot.material:
                mats.append(slot.material.name)
        return mats
