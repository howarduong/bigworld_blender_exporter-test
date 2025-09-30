# 文件位置: bigworld_blender_exporter/core/exporter.py
# Main exporter orchestrating the pipeline

import bpy
import os
from ..utils import logger
from .model_processor import ModelProcessor
from .animation_processor import AnimationProcessor
from .material_processor import MaterialProcessor
from ..formats import model_format, visual_format, primitives_format, animation_format, material_format
from ..config import MODELS_SUBFOLDER, ANIMATIONS_SUBFOLDER, MATERIALS_SUBFOLDER
from ..utils.validation import ValidationError


class BigWorldExporter:
    """主导出器类，负责整体导出流程"""

    def __init__(self, context, settings):
        self.context = context
        self.settings = settings
        self.model_data = {}
        self.material_data = {}
        self.animation_data = {}

    def export(self):
        logger.info("开始导出流程 Start export process")
        self.collect_data()
        self.validate()
        self.write_files()
        logger.info("导出完成 Export finished")

    def collect_data(self):
        logger.info("收集数据 Collecting data")

        for obj in self.context.selected_objects:
            # 模型
            model = ModelProcessor().process(obj, self.settings)
            self.model_data[obj.name] = model

            # 材质
            mats = MaterialProcessor().process(obj, self.settings)
            self.material_data[obj.name] = mats

            # 动画
            if self.settings.export_animation and obj.animation_data and obj.animation_data.action:
                anim_data = AnimationProcessor().process(obj, obj.animation_data.action, self.settings)
                self.animation_data[obj.name] = anim_data

    def validate(self):
        logger.info("验证数据 Validating data")
        # TODO: 实现更详细的数据完整性检查
        for name, model in self.model_data.items():
            if not model.get("vertices") or not model.get("indices"):
                raise ValidationError(f"Model {name} has no geometry data")

    def write_files(self):
        logger.info("写入文件 Writing files")

        export_root = self.settings.export_path or "."
        models_dir = os.path.join(export_root, MODELS_SUBFOLDER)
        anims_dir = os.path.join(export_root, ANIMATIONS_SUBFOLDER)
        mats_dir = os.path.join(export_root, MATERIALS_SUBFOLDER)

        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(anims_dir, exist_ok=True)
        os.makedirs(mats_dir, exist_ok=True)

        for obj_name, model in self.model_data.items():
            if not model:
                continue
            base_name = obj_name

            # ----------------------------
            # .primitives
            # ----------------------------
            primitives_path_rel = f"{MODELS_SUBFOLDER}/{base_name}.primitives"
            primitives_path = os.path.join(export_root, primitives_path_rel)
            vertices = model.get("vertices", [])
            indices = model.get("indices", [])
            groups = model.get("primitive_groups", [])
            primitives_format.export_primitives_file(
                primitives_path,
                vertices,
                indices,
                groups,
                vertex_format_name=getattr(self.settings, "vertex_format", "xyznuvtb"),
                use_32bit_index=getattr(self.settings, "use_32bit_index", False),
            )

            # ----------------------------
            # .mfm
            # ----------------------------
            mats = self.material_data.get(obj_name, [])
            for i, mat in enumerate(mats):
                mat_name = f"{base_name}_{i}"
                material_rel = f"{MATERIALS_SUBFOLDER}/{mat_name}.mfm"
                material_path = os.path.join(export_root, material_rel)
                material_format.export_material_file(material_path, mat)
                # 将材质路径写回 primitive_groups
                if i < len(groups):
                    groups[i]["material"] = material_rel

            # ----------------------------
            # .visual
            # ----------------------------
            visual_info = {
                "nodes": [{"name": "root", "matrix": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}],
                "world_space": False,
                "primitives": primitives_path_rel,
                "primitive_groups": groups,
                "bbox_min": f"{model['bbox_min'][0]:.6f} {model['bbox_min'][1]:.6f} {model['bbox_min'][2]:.6f}",
                "bbox_max": f"{model['bbox_max'][0]:.6f} {model['bbox_max'][1]:.6f} {model['bbox_max'][2]:.6f}",
            }
            visual_path_rel = f"{MODELS_SUBFOLDER}/{base_name}.visual"
            visual_path = os.path.join(export_root, visual_path_rel)
            visual_format.export_visual_file(visual_path, visual_info)

            # ----------------------------
            # .model
            # ----------------------------
            model_info = {
                "visual": visual_path_rel,
                "parent": "",
                "extent": model.get("extent", 10.0),
                "bbox_min": visual_info["bbox_min"],
                "bbox_max": visual_info["bbox_max"],
                "bsp_model": "",
                "animations": [],
                "actions": [],
            }
            # 如果有动画，写入 animations
            if obj_name in self.animation_data:
                anim = self.animation_data[obj_name]
                anim_rel = f"{ANIMATIONS_SUBFOLDER}/{base_name}.animation"
                model_info["animations"].append({
                    "name": anim["name"],
                    "nodes": anim_rel,
                    "frameRate": anim["frame_rate"],
                    "firstFrame": 0,
                    "lastFrame": anim["frame_count"] - 1,
                })
            model_path = os.path.join(export_root, f"{MODELS_SUBFOLDER}/{base_name}.model")
            model_format.export_model_file(model_path, model_info)

            # ----------------------------
            # .animation
            # ----------------------------
            if obj_name in self.animation_data:
                anim = self.animation_data[obj_name]
                anim_path = os.path.join(anims_dir, f"{base_name}.animation")
                animation_format.export_animation_file(anim_path, anim)

    def _build_material_file_data(self, obj_name: str):
        """已废弃：旧的材质合并逻辑"""
        return {}


def register():
    pass

def unregister():
    pass
