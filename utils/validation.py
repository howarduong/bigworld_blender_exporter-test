# 文件位置: bigworld_blender_exporter/utils/validation.py
# -*- coding: utf-8 -*-
"""
Validation and auto-fix utilities for BigWorld exporter
"""

import os
import bpy
import bmesh
from ..utils.logger import get_logger

logger = get_logger("validation")


class ValidationError(Exception):
    pass


# ----------------------------
# Mesh / Armature validation
# ----------------------------
def validate_mesh(obj):
    if obj.type != "MESH":
        return False, "Object is not a mesh"
    if not obj.data.vertices:
        return False, "Mesh has no vertices"
    if not obj.data.polygons:
        return False, "Mesh has no faces"
    if not obj.data.uv_layers:
        logger.warning(f"Mesh {obj.name} has no UV layer")
    return True, ""


def validate_armature(obj):
    if obj.type != "ARMATURE":
        return False, "Object is not an armature"
    if not obj.data.bones:
        return False, "Armature has no bones"
    return True, ""


# ----------------------------
# Primitives validation
# ----------------------------
def validate_primitives(vertices, indices, primitive_groups):
    if not vertices:
        raise ValidationError("No vertices in primitives")
    if not indices:
        raise ValidationError("No indices in primitives")
    if not primitive_groups:
        raise ValidationError("No primitive groups in primitives")

    max_index = max(indices)
    if max_index >= len(vertices):
        raise ValidationError(f"Index {max_index} exceeds vertex count {len(vertices)}")

    for g in primitive_groups:
        start_idx, num_prims, start_vtx, num_vtx = (
            g["startIndex"], g["numPrims"], g["startVertex"], g["numVertices"]
        )
        if start_idx + num_prims * 3 > len(indices):
            raise ValidationError("Primitive group exceeds index buffer length")
        if start_vtx + num_vtx > len(vertices):
            raise ValidationError("Primitive group exceeds vertex buffer length")


# ----------------------------
# Visual validation
# ----------------------------
def validate_visual(visual_data, export_root):
    if "nodes" not in visual_data or not visual_data["nodes"]:
        raise ValidationError("Visual has no nodes")
    if "primitives" not in visual_data:
        raise ValidationError("Visual missing primitives reference")

    prim_path = os.path.join(export_root, visual_data["primitives"])
    if not os.path.exists(prim_path):
        logger.warning(f"Primitives file not found: {prim_path}")

    groups = visual_data.get("primitive_groups", [])
    if not groups:
        raise ValidationError("Visual has no primitive groups")

    for g in groups:
        if "material" not in g or not g["material"]:
            logger.warning("Primitive group missing material reference")
        else:
            mat_path = os.path.join(export_root, g["material"])
            if not os.path.exists(mat_path):
                logger.warning(f"Material file not found: {mat_path}")


# ----------------------------
# Model validation
# ----------------------------
def validate_model(model_data, export_root):
    if "visual" not in model_data:
        raise ValidationError("Model missing visual reference")

    vis_path = os.path.join(export_root, model_data["visual"])
    if not os.path.exists(vis_path):
        logger.warning(f"Visual file not found: {vis_path}")

    for anim in model_data.get("animations", []):
        if "nodes" not in anim:
            raise ValidationError("Animation entry missing nodes path")
        anim_path = os.path.join(export_root, anim["nodes"])
        if not os.path.exists(anim_path):
            logger.warning(f"Animation file not found: {anim_path}")
        if anim.get("frameRate", 0) <= 0:
            raise ValidationError("Animation frameRate must be > 0")
        if anim.get("lastFrame", 0) < anim.get("firstFrame", 0):
            raise ValidationError("Animation lastFrame < firstFrame")


# ----------------------------
# Material validation
# ----------------------------
def validate_material(material_data):
    if "identifier" not in material_data:
        raise ValidationError("Material missing identifier")
    if "fx" not in material_data:
        raise ValidationError("Material missing fx shader path")
    if "materialKind" not in material_data:
        raise ValidationError("Material missing materialKind")

    for p in material_data.get("properties", []):
        if "name" not in p or "type" not in p or "value" not in p:
            raise ValidationError("Material property missing fields")
        if p["type"] == "Vector4":
            if not (isinstance(p["value"], (list, tuple)) and len(p["value"]) == 4):
                raise ValidationError(f"Property {p['name']} must be Vector4 of length 4")
        if p["type"] == "Float":
            try:
                float(p["value"])
            except Exception:
                raise ValidationError(f"Property {p['name']} must be float")
        if p["type"] == "Bool":
            if not isinstance(p["value"], (bool, int)):
                raise ValidationError(f"Property {p['name']} must be bool")
        if p["type"] == "Int":
            if not isinstance(p["value"], int):
                raise ValidationError(f"Property {p['name']} must be int")


# ----------------------------
# Auto Fix
# ----------------------------
def fix_scene():
    """
    自动修复场景：
      - 为没有 UV 的网格生成默认 UV
      - 重算法线和切线
      - 归一化骨骼权重
    """
    logger.info("Running auto-fix on scene...")

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            mesh = obj.data
            # UV
            if not mesh.uv_layers:
                logger.warning(f"Mesh {obj.name} missing UVs, generating default UV map")
                bm = bmesh.new()
                bm.from_mesh(mesh)
                uv_layer = bm.loops.layers.uv.new("UVMap")
                for face in bm.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = (0.0, 0.0)
                bm.to_mesh(mesh)
                bm.free()

            # Normals & tangents
            mesh.calc_normals()
            if mesh.uv_layers.active:
                try:
                    mesh.calc_tangents()
                except Exception:
                    logger.warning(f"Mesh {obj.name} failed to calc tangents")

            # 骨骼权重归一化
            if obj.vertex_groups:
                for v in mesh.vertices:
                    total = sum([g.weight for g in v.groups])
                    if total > 0:
                        for g in v.groups:
                            g.weight /= total

    logger.info("Auto-fix complete.")
