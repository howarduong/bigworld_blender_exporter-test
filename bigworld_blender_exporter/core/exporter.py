# -*- coding: utf-8 -*-
"""
core/exporter.py
BigWorld Blender Exporter 主导出类（增强版）
- 包围盒计算（世界空间）
- 扩展贴图处理（diffuse/normal/specular/metallic/roughness）
- 动画采集层（从 Action/F-Curves）
- 多材质支持（多个 primitiveGroup + 独立 .mfm）
"""

import os
import math
import shutil
import xml.etree.ElementTree as ET
import bpy

from ..formats import (
    primitives_format,
    material_format,
    model_format,
    animation_format,
)
from ..utils import path_utils, logger, validation

log = logger.get_logger("core.exporter")


# -----------------------------
# 通用辅助
# -----------------------------
def _safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return float(default)


def _vec3_text(v):
    return f"{float(v[0]):.6f} {float(v[1]):.6f} {float(v[2]):.6f}"


# -----------------------------
# 包围盒计算（世界空间）
# -----------------------------
def compute_world_bbox(obj: bpy.types.Object):
    """
    返回 ((minx,miny,minz),(maxx,maxy,maxz))，来自 obj 的评估网格，应用世界矩阵
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    try:
        if not mesh or len(mesh.vertices) == 0:
            return (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)

        wm = obj.matrix_world
        minx = miny = minz = math.inf
        maxx = maxy = maxz = -math.inf
        for v in mesh.vertices:
            co = wm @ v.co
            minx = min(minx, co.x)
            miny = min(miny, co.y)
            minz = min(minz, co.z)
            maxx = max(maxx, co.x)
            maxy = max(maxy, co.y)
            maxz = max(maxz, co.z)

        return (minx, miny, minz), (maxx, maxy, maxz)
    finally:
        eval_obj.to_mesh_clear()


# -----------------------------
# 贴图复制
# -----------------------------
def copy_texture_to_maps(tex_path: str, maps_dir: str, out_name: str) -> str:
    """
    复制贴图到 maps/ 下，返回相对路径 maps/xxx.dds/png/...
    out_name 不含扩展名；目标扩展沿用源文件扩展
    """
    if not tex_path or not os.path.exists(tex_path):
        return ""
    ext = os.path.splitext(tex_path)[1].lower()
    dst_name = f"{out_name}{ext}"
    dst_path = os.path.join(maps_dir, dst_name)
    try:
        shutil.copy2(tex_path, dst_path)
        return f"maps/{dst_name}"
    except Exception as e:
        log.error(f"Failed to copy texture {tex_path}: {e}")
        return ""


def collect_textures_from_material(mat: bpy.types.Material, res_root: str, base_name: str) -> dict:
    """
    从材质节点树采集常见贴图并复制到 maps/
    返回字典：
      {
        "diffuseMap": "maps/xxx",
        "normalMap": "maps/xxx",
        "specularMap": "maps/xxx",
        "metallicMap": "maps/xxx",
        "roughnessMap": "maps/xxx"
      }
    """
    result = {}
    if not mat or not mat.node_tree:
        return result

    maps_dir = path_utils.get_map_dir(res_root)

    def image_path_from_node(node):
        if node and getattr(node, "image", None):
            return bpy.path.abspath(node.image.filepath)
        return ""

    # 寻找关键节点
    bsdf = None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            bsdf = n
            break

    # diffuse(Base Color)
    diffuse_path = ""
    if bsdf and bsdf.inputs.get("Base Color") and bsdf.inputs["Base Color"].is_linked:
        from_node = bsdf.inputs["Base Color"].links[0].from_node
        if from_node.type == "TEX_IMAGE":
            diffuse_path = image_path_from_node(from_node)

    # normal
    normal_path = ""
    if bsdf and bsdf.inputs.get("Normal") and bsdf.inputs["Normal"].is_linked:
        nm_node = bsdf.inputs["Normal"].links[0].from_node
        # Normal Map 常见链：NormalMapNode -> TexImage
        if nm_node.type == "NORMAL_MAP" and nm_node.inputs["Color"].is_linked:
            tex_node = nm_node.inputs["Color"].links[0].from_node
            if tex_node.type == "TEX_IMAGE":
                normal_path = image_path_from_node(tex_node)
        elif nm_node.type == "TEX_IMAGE":
            normal_path = image_path_from_node(nm_node)

    # specular
    spec_path = ""
    if bsdf and bsdf.inputs.get("Specular") and bsdf.inputs["Specular"].is_linked:
        s_node = bsdf.inputs["Specular"].links[0].from_node
        if s_node.type == "TEX_IMAGE":
            spec_path = image_path_from_node(s_node)

    # metallic
    metallic_path = ""
    if bsdf and bsdf.inputs.get("Metallic") and bsdf.inputs["Metallic"].is_linked:
        m_node = bsdf.inputs["Metallic"].links[0].from_node
        if m_node.type == "TEX_IMAGE":
            metallic_path = image_path_from_node(m_node)

    # roughness
    rough_path = ""
    if bsdf and bsdf.inputs.get("Roughness") and bsdf.inputs["Roughness"].is_linked:
        r_node = bsdf.inputs["Roughness"].links[0].from_node
        if r_node.type == "TEX_IMAGE":
            rough_path = image_path_from_node(r_node)

    # 拷贝
    if diffuse_path:
        result["diffuseMap"] = copy_texture_to_maps(diffuse_path, maps_dir, f"{base_name}_diffuse")
    if normal_path:
        result["normalMap"] = copy_texture_to_maps(normal_path, maps_dir, f"{base_name}_normal")
    if spec_path:
        result["specularMap"] = copy_texture_to_maps(spec_path, maps_dir, f"{base_name}_spec")
    if metallic_path:
        result["metallicMap"] = copy_texture_to_maps(metallic_path, maps_dir, f"{base_name}_metal")
    if rough_path:
        result["roughnessMap"] = copy_texture_to_maps(rough_path, maps_dir, f"{base_name}_rough")

    # 清理空值
    for k in list(result.keys()):
        if not result[k]:
            result.pop(k, None)

    return result


# -----------------------------
# 动画采集层
# -----------------------------
def collect_animation_from_action(arm_obj: bpy.types.Object, action: bpy.types.Action, frame_rate: float = 30.0):
    """
    从 Action/F-Curves 采集动画关键帧为 animation_data
    要求 arm_obj 是 Armature 对象
    """
    anim = {
        "name": action.name if action else "unnamed",
        "frame_rate": frame_rate,
        "duration": 0.0,
        "loop": True,
        "channels": [],
    }
    if not arm_obj or not action:
        return anim

    # 收集所有关键帧时间
    times = set()
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            times.add(_safe_float(kp.co[0], 0.0))
    if not times:
        return anim

    min_f = min(times)
    max_f = max(times)
    anim["duration"] = (max_f - min_f) / frame_rate

    # 采样每个骨骼在这些帧的 TRS
    arm = arm_obj
    wm = arm.matrix_world

    # 确保动画设置使用当前 action
    arm.animation_data_create()
    arm.animation_data.action = action

    times_sorted = sorted(times)

    for bone in arm.pose.bones:
        ch = {"bone": bone.name, "keyframes": []}
        for f in times_sorted:
            bpy.context.scene.frame_set(int(f))

            m = wm @ bone.matrix
            pos = m.to_translation()
            rot = m.to_quaternion()
            sca = m.to_scale()

            ch["keyframes"].append({
                "time": (f - min_f) / frame_rate,
                "position": (pos.x, pos.y, pos.z),
                "rotation": (rot.x, rot.y, rot.z, rot.w),
                "scale": (sca.x, sca.y, sca.z),
            })

        anim["channels"].append(ch)

    return anim


# -----------------------------
# 多材质可视化写出（直接写 .visual）
# -----------------------------
def write_visual_with_groups(filepath: str,
                             base_name: str,
                             bbox: tuple,
                             material_groups: list,
                             primitives_tags: tuple):
    """
    写入支持多个 primitiveGroup 的 .visual
    material_groups: [
        {
            "id": int,
            "identifier": "<mat name>",
            "fx": "shaders/...",
            "textures": [("diffuseMap","maps/..."), ("normalMap","maps/..."), ...]
        }, ...
    ]
    primitives_tags: (vertices_tag, indices_tag)
    """
    root = ET.Element(f"{base_name}.visual")

    # renderSet + geometry
    render_set = ET.SubElement(root, "renderSet")
    geometry = ET.SubElement(render_set, "geometry")

    v_elem = ET.SubElement(geometry, "vertices")
    v_elem.text = primitives_tags[0]

    p_elem = ET.SubElement(geometry, "primitive")
    p_elem.text = primitives_tags[1]

    # 多个 primitiveGroup
    for g in material_groups:
        pg = ET.SubElement(geometry, "primitiveGroup")
        pg.set("id", str(g.get("id", 0)))
        mat = ET.SubElement(pg, "material")

        ident = ET.SubElement(mat, "identifier")
        ident.text = g.get("identifier", f"{base_name}")

        fx = ET.SubElement(mat, "fx")
        fx.text = g.get("fx", "shaders/std_effects/normalmap_specmap.fx")

        for (prop_name, tex_rel) in g.get("textures", []):
            prop = ET.SubElement(mat, "property")
            prop.set("name", prop_name)
            tex = ET.SubElement(prop, "Texture")
            tex.text = tex_rel

    # boundingBox
    bb_elem = ET.SubElement(root, "boundingBox")
    min_elem = ET.SubElement(bb_elem, "min")
    min_elem.text = _vec3_text(bbox[0])
    max_elem = ET.SubElement(bb_elem, "max")
    max_elem.text = _vec3_text(bbox[1])

    # 写文件
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    ET.ElementTree(root).write(filepath, encoding="utf-8", xml_declaration=True)


# -----------------------------
# 导出类
# -----------------------------
class BigWorldExporter:
    def __init__(self, res_root: str):
        self.res_root = res_root
        # 初始化目录
        self.model_dir = path_utils.get_model_dir(res_root)
        self.mat_dir = path_utils.get_material_dir(res_root)
        self.map_dir = path_utils.get_map_dir(res_root)
        self.anim_dir = path_utils.get_animation_dir(res_root)

    def export_object(self, obj: bpy.types.Object, shader_path="shaders/std_effects/normalmap_specmap.fx"):
        """
        导出 Blender 对象为 BigWorld 模型（含多材质、包围盒、贴图、动画）
        """
        base_name = obj.name

        # === 1. Primitives ===
        prim_path = os.path.join(self.model_dir, f"{base_name}.primitives")
        vbytes = primitives_format.serialize_vertices(obj.data)
        ibytes = primitives_format.serialize_indices(obj.data)
        primitives_format.write_primitives_file(
            filepath=prim_path,
            base_name=base_name,
            vertices_bytes=vbytes,
            indices_bytes=ibytes,
        )

        # === 2. 包围盒（世界空间） ===
        bbox_min, bbox_max = compute_world_bbox(obj)

        # === 3. 多材质 + 贴图处理 ===
        material_groups = []
        mat_names_for_model = []

        # 遍历材质槽，为每个槽生成一个独立的 .mfm 与 primitiveGroup
        for idx, slot in enumerate(getattr(obj, "material_slots", [])):
            mat = slot.material
            ident_name = mat.name if mat else f"{base_name}_mat_{idx}"
            mat_names_for_model.append(ident_name)

            textures = collect_textures_from_material(mat, self.res_root, f"{base_name}_{ident_name}") if mat else {}

            # 为每个材质生成/复用 .mfm
            mfm_path = os.path.join(self.mat_dir, f"{ident_name}.mfm")
            material_format.export_material_file(
                filepath=mfm_path,
                base_name=ident_name,
                shader_path=shader_path,
                textures=textures,
            )

            # primitiveGroup
            material_groups.append({
                "id": idx,
                "identifier": ident_name,
                "fx": shader_path,
                "textures": [(k, v) for k, v in textures.items()]
            })

        # 如果没有材质槽，生成一个默认组
        if not material_groups:
            ident_name = f"{base_name}_mat_0"
            mfm_path = os.path.join(self.mat_dir, f"{ident_name}.mfm")
            material_format.export_material_file(
                filepath=mfm_path,
                base_name=ident_name,
                shader_path=shader_path,
                textures={}
            )
            material_groups.append({
                "id": 0,
                "identifier": ident_name,
                "fx": shader_path,
                "textures": []
            })
            mat_names_for_model.append(ident_name)

        # === 4. Visual（支持多材质 primitiveGroup） ===
        visual_path = os.path.join(self.model_dir, f"{base_name}.visual")
        write_visual_with_groups(
            filepath=visual_path,
            base_name=base_name,
            bbox=(bbox_min, bbox_max),
            material_groups=material_groups,
            primitives_tags=(f"{base_name}.vertices", f"{base_name}.indices")
        )

        # === 5. Model ===
        model_path = os.path.join(self.model_dir, f"{base_name}.model")
        model_format.export_model_file(
            filepath=model_path,
            model_data={
                "visual": f"models/{base_name}/{base_name}",  # 不带扩展名
                "materials": mat_names_for_model,
                "bbox_min": _vec3_text(bbox_min),
                "bbox_max": _vec3_text(bbox_max),
                "extent": 10.0,
            },
        )

        # === 6. 动画（采集 Armature 的当前 Action） ===
        # 如果对象绑定了 Armature 修改器，则尝试导出其 Action
        arm_obj = None
        for mod in getattr(obj, "modifiers", []):
            if mod.type == "ARMATURE" and mod.object and mod.object.type == "ARMATURE":
                arm_obj = mod.object
                break

        if arm_obj and arm_obj.animation_data and arm_obj.animation_data.action:
            action = arm_obj.animation_data.action
            fps = float(bpy.context.scene.render.fps) if bpy.context and bpy.context.scene else 30.0
            anim_data = collect_animation_from_action(arm_obj, action, frame_rate=fps)
            anim_path = os.path.join(self.anim_dir, f"{base_name}_{action.name}.animation")
            animation_format.export_animation_file(anim_path, anim_data)
        else:
            # 没有动画则生成一个空占位（可选）
            anim_data = {
                "name": f"{base_name}_idle",
                "frame_rate": 30.0,
                "duration": 0.0,
                "loop": True,
                "channels": [],
            }
            anim_path = os.path.join(self.anim_dir, f"{base_name}_idle.animation")
            animation_format.export_animation_file(anim_path, anim_data)

        # === 7. 验证 ===
        validation.validate_export(self.res_root, base_name)

        log.info(f"Export completed for {base_name}")
