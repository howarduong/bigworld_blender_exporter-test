# 文件位置: bigworld_blender_exporter/core/exporter.py
# Main exporter class for BigWorld Blender Exporter

import bpy
import os
from ..utils import logger
from ..formats import model_format, visual_format, primitives_format, animation_format, material_format
from ..config import MODELS_SUBFOLDER, ANIMATIONS_SUBFOLDER, MATERIALS_SUBFOLDER
from .collectors import MeshCollector, SkeletonCollector, AnimationCollector, MaterialCollector


class BigWorldExporter:
    """主导出器类，负责整体导出流程"""

    def __init__(self, context, settings):
        self.context = context
        self.settings = settings
        self.mesh_data = {}
        self.skeleton_data = {}
        self.animation_data = {}
        self.material_data = {}
        self.report_lines = []

    # -------------------------
    # 公共方法
    # -------------------------
    def _get_objects(self):
        if self.settings.export_selected and self.context.selected_objects:
            return self.context.selected_objects
        return self.context.scene.objects

    def _write_report(self, success=True):
        try:
            report_path = bpy.path.abspath(self.settings.report_path or "./export_report.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                for line in self.report_lines:
                    f.write(line + "\n")
                f.write("\n")
                f.write("Export SUCCESS\n" if success else "Export FAILED\n")
            logger.info(f"Report written to {report_path}")
        except Exception as e:
            logger.error(f"Failed to write report: {str(e)}")

    # -------------------------
    # 导出模型
    # -------------------------
    def export_models(self):
        logger.info("开始导出模型 Start model export")
        self.report_lines.append("=== BigWorld Export Report (Models) ===")
        try:
            self.collect_meshes()
            self.validate()
            self.write_model_files()
            self._write_report(success=True)
            logger.info("模型导出完成 Model export finished")
        except Exception as e:
            logger.error(f"Model export failed: {str(e)}")
            self.report_lines.append(f"ERROR: {str(e)}")
            self._write_report(success=False)
            raise

    def collect_meshes(self):
        logger.info("收集网格和材质 Collecting meshes/materials")
        mesh_collector = MeshCollector()
        mat_collector = MaterialCollector()
        for obj in self._get_objects():
            if self.settings.export_mesh and obj.type == 'MESH':
                mesh = mesh_collector.collect(obj, self.settings)
                if mesh:
                    self.mesh_data[obj.name] = mesh
                else:
                    logger.warning(f"MeshCollector returned None for {obj.name}")
            if self.settings.export_materials:
                mats = mat_collector.collect(obj, self.settings)
                if mats:
                    self.material_data[obj.name] = mats

    def write_model_files(self):
        logger.info("写入模型文件 Writing model files")
        export_root = bpy.path.abspath(self.settings.export_path or ".")
        models_dir = os.path.join(export_root, MODELS_SUBFOLDER)
        mats_dir = os.path.join(export_root, MATERIALS_SUBFOLDER)
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(mats_dir, exist_ok=True)

        for obj_name, mesh in self.mesh_data.items():
            try:
                base_name = obj_name

                # .primitives
                primitives_path_rel = f"{MODELS_SUBFOLDER}/{base_name}.primitives"
                primitives_path = os.path.join(export_root, primitives_path_rel)
                vertices = mesh.get("vertices", [])
                indices = mesh.get("indices", [])
                primitives_format.export_primitives_file(
                    primitives_path, vertices, indices, getattr(self.settings, "vertex_format", "STANDARD")
                )

                # .mfm
                material_info = self._build_material_file_data(obj_name)
                material_rel = f"{MATERIALS_SUBFOLDER}/{base_name}.mfm"
                material_path = os.path.join(export_root, material_rel)
                material_format.export_material_file(material_path, material_info)

                # .visual
                visual_info = {
                    "world_space": "false",
                    "node": "root",
                    "primitives": primitives_path_rel,
                    "material": material_rel,
                    "start_index": 0,
                    "end_index": len(indices),
                    "start_vertex": 0,
                    "end_vertex": len(vertices),
                    "bbox_min": f"{mesh['bbox_min'][0]:.6f} {mesh['bbox_min'][1]:.6f} {mesh['bbox_min'][2]:.6f}",
                    "bbox_max": f"{mesh['bbox_max'][0]:.6f} {mesh['bbox_max'][1]:.6f} {mesh['bbox_max'][2]:.6f}",
                }
                visual_path_rel = f"{MODELS_SUBFOLDER}/{base_name}.visual"
                visual_path = os.path.join(export_root, visual_path_rel)
                visual_format.export_visual_file(visual_path, visual_info)

                # .model
                model_info = {
                    "visual": visual_path_rel,
                    "parent": "",
                    "extent": mesh.get("extent", 10.0),
                    "bbox_min": f"{mesh['bbox_min'][0]:.6f} {mesh['bbox_min'][1]:.6f} {mesh['bbox_min'][2]:.6f}",
                    "bbox_max": f"{mesh['bbox_max'][0]:.6f} {mesh['bbox_max'][1]:.6f} {mesh['bbox_max'][2]:.6f}",
                    "bsp_model": "",
                }
                model_path = os.path.join(export_root, f"{MODELS_SUBFOLDER}/{base_name}.model")
                model_format.export_model_file(model_path, model_info)

                self.report_lines.append(f"Exported model: {obj_name}")
            except Exception as e:
                logger.error(f"Failed to export {obj_name}: {str(e)}")
                self.report_lines.append(f"ERROR: Failed to export {obj_name}: {str(e)}")

    # -------------------------
    # 导出动画
    # -------------------------
    def export_animations(self):
        logger.info("开始导出动画 Start animation export")
        self.report_lines.append("=== BigWorld Export Report (Animations) ===")
        try:
            self.collect_animations()
            self.write_animation_files()
            self._write_report(success=True)
            logger.info("动画导出完成 Animation export finished")
        except Exception as e:
            logger.error(f"Animation export failed: {str(e)}")
            self.report_lines.append(f"ERROR: {str(e)}")
            self._write_report(success=False)
            raise

    def collect_animations(self):
        logger.info("收集动画 Collecting animations")
        anim_collector = AnimationCollector()
        for obj in self._get_objects():
            if self.settings.export_animation and obj.animation_data:
                if obj.animation_data.action:
                    anim = anim_collector.collect(obj, obj.animation_data.action, self.settings)
                    if anim:
                        self.animation_data[f"{obj.name}_{obj.animation_data.action.name}"] = anim
                if obj.animation_data.nla_tracks:
                    for track in obj.animation_data.nla_tracks:
                        for strip in track.strips:
                            if strip.action:
                                anim = anim_collector.collect(obj, strip.action, self.settings)
                                if anim:
                                    self.animation_data[f"{obj.name}_{strip.action.name}"] = anim

    def write_animation_files(self):
        logger.info("写入动画文件 Writing animation files")
        export_root = bpy.path.abspath(self.settings.export_path or ".")
        anims_dir = os.path.join(export_root, ANIMATIONS_SUBFOLDER)
        os.makedirs(anims_dir, exist_ok=True)

        for anim_name, anim in self.animation_data.items():
            try:
                anim_file = os.path.join(anims_dir, f"{anim_name}.animation")
                animation_format.export_animation_file(anim_file, anim)
                self.report_lines.append(f"Exported animation: {anim_name}")
            except Exception as e:
                logger.error(f"Failed to export animation {anim_name}: {str(e)}")
                self.report_lines.append(f"ERROR: Failed to export animation {anim_name}: {str(e)}")

    # -------------------------
    # 验证
    # -------------------------
    def validate(self):
        logger.info("验证数据 Validating data")
        self.report_lines.append("Validating data...")

        issues = []
        for obj_name, mesh in self.mesh_data.items():
            if not mesh.get("vertices"):
                issues.append(f"{obj_name}: No vertices found")
            if self.settings.export_tangents and not mesh.get("uvs"):
                issues.append(f"{obj_name}: Missing UVs for tangent generation")
            if self.settings.max_weights > 0 and mesh.get("max_weights", 0) > self.settings.max_weights:
                issues.append(f"{obj_name}: Too many bone weights per vertex")

        if issues:
            for issue in issues:
                logger.warning(issue)
                self.report_lines.append(f"WARNING: {issue}")
        else:
            self.report_lines.append("Validation passed")

    # -------------------------
    # 材质合并
    # -------------------------
    def _build_material_file_data(self, obj_name: str):
        """Aggregate object material data into a single .mfm definition."""
        mats = self.material_data.get(obj_name, [])
        merged = {
            "name": obj_name,
            "shader": "shaders/std_effects.fx",
            "technique": "default",
            "textures": {},
            "parameters": {},
        }
        for m in mats:
            for k, v in m.get("textures", {}).items():
                merged["textures"][k] = v
            for k, v in m.get("parameters", {}).items():
                merged["parameters"][k] = v
        return merged


# -------------------------
# Blender 注册接口
# -------------------------
def register():
    pass


def unregister():
    pass
