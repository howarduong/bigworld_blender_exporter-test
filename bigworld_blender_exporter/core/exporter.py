# 文件位置: bigworld_blender_exporter/core/exporter.py
# Main exporter class for BigWorld Blender Exporter (改进版)


# -*- coding: utf-8 -*-
"""
core/exporter.py
BigWorld Blender Exporter 主导出类
"""

import os
import bpy
import shutil

from ..formats import (
    primitives_format,
    visual_format,
    material_format,
    model_format,
    animation_format,
)
from ..utils import path_utils, logger, validation

log = logger.get_logger("core.exporter")


class BigWorldExporter:
    def __init__(self, res_root: str):
        self.res_root = res_root
        # 初始化目录
        self.model_dir = path_utils.get_model_dir(res_root)
        self.mat_dir = path_utils.get_material_dir(res_root)
        self.map_dir = path_utils.get_map_dir(res_root)
        self.anim_dir = path_utils.get_animation_dir(res_root)

    def _copy_texture(self, tex_path: str, base_name: str, suffix: str = "_diffuse") -> str:
        """
        复制贴图到 maps/ 下，并返回相对路径
        """
        if not tex_path or not os.path.exists(tex_path):
            log.warning(f"Texture not found: {tex_path}")
            return ""

        ext = os.path.splitext(tex_path)[1].lower()
        dst_name = f"{base_name}{suffix}{ext}"
        dst_path = os.path.join(self.map_dir, dst_name)

        try:
            shutil.copy2(tex_path, dst_path)
            log.info(f"Copied texture: {dst_path}")
        except Exception as e:
            log.error(f"Failed to copy texture {tex_path}: {e}")

        return f"maps/{dst_name}"

    def export_object(self, obj: bpy.types.Object, shader_path="shaders/std_effects/normalmap_specmap.fx"):
        """
        导出 Blender 对象为 BigWorld 模型
        """
        base_name = obj.name

        # === 1. 导出 primitives ===
        prim_path = os.path.join(self.model_dir, f"{base_name}.primitives")
        vbytes = primitives_format.serialize_vertices(obj.data)
        ibytes = primitives_format.serialize_indices(obj.data)
        primitives_format.write_primitives_file(
            filepath=prim_path,
            base_name=base_name,
            vertices_bytes=vbytes,
            indices_bytes=ibytes,
        )

        # === 2. 导出材质 (mfm) ===
        textures = {}
        if obj.active_material and obj.active_material.node_tree:
            for node in obj.active_material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    tex_path = bpy.path.abspath(node.image.filepath)
                    tex_rel = self._copy_texture(tex_path, base_name)
                    if tex_rel:
                        textures["diffuseMap"] = tex_rel

        mfm_path = os.path.join(self.mat_dir, f"{base_name}.mfm")
        material_format.export_material_file(
            filepath=mfm_path,
            base_name=base_name,
            shader_path=shader_path,
            textures=textures,
        )

        # === 3. 导出 visual ===
        visual_path = os.path.join(self.model_dir, f"{base_name}.visual")
        visual_format.export_visual_file(
            filepath=visual_path,
            base_name=base_name,
            vertices_tag=f"{base_name}.vertices",
            indices_tag=f"{base_name}.indices",
            material_rel_path=path_utils.to_res_relative(mfm_path, self.res_root),
            shader_path=shader_path,
            textures=[(k, v) for k, v in textures.items()],
            bounding_box=((0, 0, 0), (1, 1, 1)),  # TODO: 从 mesh 计算真实包围盒
        )

        # === 4. 导出 model ===
        model_path = os.path.join(self.model_dir, f"{base_name}.model")
        model_format.export_model_file(
            filepath=model_path,
            model_data={
                "visual": f"models/{base_name}/{base_name}",  # 不带扩展名
                "materials": [base_name],
                "bbox_min": "0 0 0",
                "bbox_max": "1 1 1",
                "extent": 10.0,
            },
        )

        # === 5. 导出动画（如果有） ===
        anim_data = {
            "name": f"{base_name}_idle",
            "frame_rate": 30.0,
            "duration": 0.0,
            "loop": True,
            "channels": [],
        }
        anim_path = os.path.join(self.anim_dir, f"{base_name}_idle.animation")
        animation_format.export_animation_file(anim_path, anim_data)

        # === 6. 验证 ===
        validation.validate_export(self.res_root, base_name)

        log.info(f"Export completed for {base_name}")
