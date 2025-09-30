# 文件位置: bigworld_blender_exporter/ui/operators.py
# Operator definitions for BigWorld exporter

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from ..core.exporter import BigWorldExporter
from ..utils.logger import get_logger
from ..utils.validation import (
    validate_export_settings,
    validate_scene,
    validate_primitives,
    validate_visual,
    validate_model,
    validate_material,
)
import os


logger = get_logger("operators")


class EXPORT_OT_bigworld_model(Operator):
    bl_idname = "export.bigworld_model"
    bl_label = "Export Model 导出模型"
    bl_description = "Export selected or all models to BigWorld format\n导出选中或全部模型为BigWorld格式"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export

            # 检查导出路径
            if not settings.export_path:
                self.report({'ERROR'}, "Please set export path! 请设置导出路径！")
                return {'CANCELLED'}

            # 验证导出设置
            setting_issues = validate_export_settings(settings)
            if setting_issues:
                self.report({'ERROR'}, setting_issues[0])
                for issue in setting_issues[1:]:
                    self.report({'WARNING'}, issue)
                return {'CANCELLED'}

            # 验证场景
            scene_issues = validate_scene(context)
            if scene_issues:
                self.report({'ERROR'}, scene_issues[0])
                for issue in scene_issues[1:]:
                    self.report({'WARNING'}, issue)
                return {'CANCELLED'}

            # 创建导出目录
            os.makedirs(settings.export_path, exist_ok=True)

            # 执行导出
            exporter = BigWorldExporter(context, settings)
            logger.info("Starting model export...")
            exporter.export()

            self.report({'INFO'}, f"Model export finished! Exported to: {settings.export_path}")
            context.scene.bigworld_export_status = "Export complete 导出完成"
            return {'FINISHED'}

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            context.scene.bigworld_export_status = f"Error 错误: {str(e)}"
            return {'CANCELLED'}


class EXPORT_OT_bigworld_animation(Operator):
    bl_idname = "export.bigworld_animation"
    bl_label = "Export Animation 导出动画"
    bl_description = "Export animation to BigWorld format\n导出动画为BigWorld格式"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export

            if not settings.export_path:
                self.report({'ERROR'}, "Please set export path! 请设置导出路径！")
                return {'CANCELLED'}

            # 验证导出设置
            setting_issues = validate_export_settings(settings)
            if setting_issues:
                self.report({'ERROR'}, setting_issues[0])
                for issue in setting_issues[1:]:
                    self.report({'WARNING'}, issue)
                return {'CANCELLED'}

            # 使用 BigWorldExporter 来保持和 .model 文件一致
            exporter = BigWorldExporter(context, settings)
            exporter.collect_data()

            if not exporter.animation_data:
                self.report({'WARNING'}, "No animations found! 未找到动画！")
                return {'CANCELLED'}

            exporter.write_files()

            self.report({'INFO'}, f"Exported {len(exporter.animation_data)} animations.")
            context.scene.bigworld_export_status = "Animation export complete 动画导出完成"
            return {'FINISHED'}

        except Exception as e:
            logger.error(f"Animation export failed: {str(e)}")
            self.report({'ERROR'}, f"Animation export failed: {str(e)}")
            context.scene.bigworld_export_status = f"Error 错误: {str(e)}"
            return {'CANCELLED'}


class EXPORT_OT_bigworld_batch(Operator):
    bl_idname = "export.bigworld_batch"
    bl_label = "Batch Export 批量导出"
    bl_description = "Batch export all scenes\n批量导出所有场景"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export

            if not settings.export_path:
                self.report({'ERROR'}, "Please set export path! 请设置导出路径！")
                return {'CANCELLED'}

            original_scene = context.scene
            exported_count = 0

            for scene in bpy.data.scenes:
                context.window.scene = scene
                scene_dir = os.path.join(settings.export_path, scene.name)
                os.makedirs(scene_dir, exist_ok=True)

                exporter = BigWorldExporter(context, settings)
                exporter.settings.export_path = scene_dir
                exporter.export()
                exported_count += 1

            context.window.scene = original_scene
            self.report({'INFO'}, f"Batch export finished! Exported {exported_count} scenes.")
            return {'FINISHED'}

        except Exception as e:
            logger.error(f"Batch export failed: {str(e)}")
            self.report({'ERROR'}, f"Batch export failed: {str(e)}")
            return {'CANCELLED'}


class EXPORT_OT_bigworld_selected(Operator):
    bl_idname = "export.bigworld_selected"
    bl_label = "Export Selected 导出选中"
    bl_description = "Export selected objects\n导出选中对象"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            if not context.selected_objects:
                self.report({'WARNING'}, "No objects selected! 未选中对象！")
                return {'CANCELLED'}

            settings = context.scene.bigworld_export
            settings.export_selected = True

            exporter = BigWorldExporter(context, settings)
            exporter.export()

            self.report({'INFO'}, f"Selected objects export finished! Exported {len(context.selected_objects)} objects.")
            return {'FINISHED'}

        except Exception as e:
            logger.error(f"Selected export failed: {str(e)}")
            self.report({'ERROR'}, f"Selected export failed: {str(e)}")
            return {'CANCELLED'}


class BIGWORLD_OT_validate_scene(Operator):
    bl_idname = "bigworld.validate_scene"
    bl_label = "Validate Scene 验证场景"
    bl_description = "Validate scene data for export\n验证场景数据以便导出"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            issues = validate_scene(context)
            if not issues:
                self.report({'INFO'}, "Scene validation passed! 场景验证通过！")
                return {'FINISHED'}
            else:
                for issue in issues:
                    self.report({'WARNING'}, issue)
                self.report({'INFO'}, f"Found {len(issues)} issues. 发现 {len(issues)} 个问题。")
                return {'FINISHED'}

        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            self.report({'ERROR'}, f"Validation failed: {str(e)}")
            return {'CANCELLED'}


class BIGWORLD_OT_fix_scene(Operator):
    bl_idname = "bigworld.fix_scene"
    bl_label = "Auto Fix 自动修复"
    bl_description = "Auto fix common export issues\n自动修复常见导出问题"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            from ..utils.validation import fix_scene
            fixes_applied = fix_scene(context)
            if fixes_applied:
                self.report({'INFO'}, f"Applied {fixes_applied} fixes! 应用了 {fixes_applied} 个修复！")
            else:
                self.report({'INFO'}, "No fixes needed! 无需修复！")
            return {'FINISHED'}

        except Exception as e:
            logger.error(f"Auto fix failed: {str(e)}")
            self.report({'ERROR'}, f"Auto fix failed: {str(e)}")
            return {'CANCELLED'}


# 注册
classes = (
    EXPORT_OT_bigworld_model,
    EXPORT_OT_bigworld_animation,
    EXPORT_OT_bigworld_batch,
    EXPORT_OT_bigworld_selected,
    BIGWORLD_OT_validate_scene,
    BIGWORLD_OT_fix_scene,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
