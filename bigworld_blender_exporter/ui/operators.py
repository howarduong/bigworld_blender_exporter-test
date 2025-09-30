# 文件位置: bigworld_blender_exporter/ui/operators.py
# Operator definitions for BigWorld exporter

import bpy
from bpy.types import Operator
import os
from ..core.exporter import BigWorldExporter
from ..utils.logger import get_logger
from ..config import save_preset, load_preset

log = get_logger("operators")


# -------------------------
# 模型导出
# -------------------------
class EXPORT_OT_bigworld_model(Operator):
    bl_idname = "export.bigworld_model"
    bl_label = "Export Model 导出模型"
    bl_description = "Export selected or all models to BigWorld format\n导出选中或全部模型为BigWorld格式"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export
            if not settings.export_path:
                self.report({'ERROR'}, "Please set export path! 请设置导出路径！")
                return {'CANCELLED'}

            os.makedirs(settings.export_path, exist_ok=True)
            exporter = BigWorldExporter(context, settings)
            log.info("Starting model export...")
            exporter.export_models()   # ✅ 改为 export_models()
            self.report({'INFO'}, f"Model export finished! Exported to: {settings.export_path}")
            if hasattr(context.scene, 'bigworld_export_status'):
                context.scene.bigworld_export_status = "Export complete 导出完成"
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Model export failed: {str(e)}")
            self.report({'ERROR'}, f"Model export failed: {str(e)}")
            if hasattr(context.scene, 'bigworld_export_status'):
                context.scene.bigworld_export_status = f"Error 错误: {str(e)}"
            return {'CANCELLED'}


# -------------------------
# 动画导出
# -------------------------
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

            os.makedirs(os.path.join(settings.export_path, "animations"), exist_ok=True)
            exporter = BigWorldExporter(context, settings)
            log.info("Starting animation export...")
            exporter.export_animations()   # ✅ 改为 export_animations()
            self.report({'INFO'}, f"Animation export finished! Exported to: {settings.export_path}")
            if hasattr(context.scene, 'bigworld_export_status'):
                context.scene.bigworld_export_status = "Animation export complete 动画导出完成"
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Animation export failed: {str(e)}")
            self.report({'ERROR'}, f"Animation export failed: {str(e)}")
            if hasattr(context.scene, 'bigworld_export_status'):
                context.scene.bigworld_export_status = f"Error 错误: {str(e)}"
            return {'CANCELLED'}


# -------------------------
# 批量导出
# -------------------------
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
                exporter = BigWorldExporter(context, settings)
                exporter.export_models()   # ✅ 批量导出时默认导出模型
                exported_count += 1
            context.window.scene = original_scene
            self.report({'INFO'}, f"Batch export finished! Exported {exported_count} scenes.")
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Batch export failed: {str(e)}")
            self.report({'ERROR'}, f"Batch export failed: {str(e)}")
            return {'CANCELLED'}


# -------------------------
# 导出选中
# -------------------------
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
            exporter.export_models()   # ✅ 改为 export_models()
            self.report({'INFO'}, f"Selected objects export finished! Exported {len(context.selected_objects)} objects.")
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Selected export failed: {str(e)}")
            self.report({'ERROR'}, f"Selected export failed: {str(e)}")
            return {'CANCELLED'}


# -------------------------
# 验证与修复 / 预设 / 报告
# -------------------------
class BIGWORLD_OT_validate_scene(Operator):
    bl_idname = "bigworld.validate_scene"
    bl_label = "Validate Scene 验证场景"
    bl_description = "Validate scene data for export\n验证场景数据以便导出"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            from ..utils.validation import validate_scene
            issues = validate_scene(context)
            if not issues:
                self.report({'INFO'}, "Scene validation passed! 场景验证通过！")
            else:
                for issue in issues:
                    self.report({'WARNING'}, issue)
                self.report({'INFO'}, f"Found {len(issues)} issues. 发现 {len(issues)} 个问题。")
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Validation failed: {str(e)}")
            self.report({'ERROR'}, f"Validation failed: {str(e)}")
            return {'CANCELLED'}


class BIGWORLD_OT_fix_scene(Operator):
    bl_idname = "bigworld.fix_scene"
    bl_label = "Fix Scene 自动修复"
    bl_description = "Automatically fix common issues for export\n自动修复常见导出问题"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            from ..utils.validation import fix_scene
            fixed = fix_scene(context)
            if fixed == 0:
                self.report({'INFO'}, "No issues found to fix 无需修复")
            else:
                self.report({'INFO'}, f"Fixed {fixed} issues 修复了 {fixed} 个问题")
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Fix scene failed: {str(e)}")
            self.report({'ERROR'}, f"Fix scene failed: {str(e)}")
            return {'CANCELLED'}


class BIGWORLD_OT_save_preset(Operator):
    bl_idname = "bigworld.save_preset"
    bl_label = "Save Preset 保存预设"
    bl_description = "Save current export settings to preset file\n保存当前导出设置为预设文件"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export
            save_preset(settings, "default")
            self.report({'INFO'}, "Preset saved")
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Save preset failed: {str(e)}")
            self.report({'ERROR'}, f"Save preset failed: {str(e)}")
            return {'CANCELLED'}


class BIGWORLD_OT_load_preset(Operator):
    bl_idname = "bigworld.load_preset"
    bl_label = "Load Preset 加载预设"
    bl_description = "Load export settings from preset file\n从预设文件加载导出设置"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export
            load_preset(settings, "default")
            self.report({'INFO'}, "Preset loaded")
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Load preset failed: {str(e)}")
            self.report({'ERROR'}, f"Load preset failed: {str(e)}")
            return {'CANCELLED'}


class BIGWORLD_OT_open_report(Operator):
    bl_idname = "bigworld.open_report"
    bl_label = "Open Report 打开报告"
    bl_description = "Open the last export report file\n打开最近的导出报告文件"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export
            path = bpy.path.abspath(settings.report_path)
            if os.path.exists(path):
                if os.name == 'nt':
                    os.startfile(path)
                else:
                    os.system(f'open "{path}"')
                self.report({'INFO'}, f"Opened report: {path}")
            else:
                self.report({'WARNING'}, "Report file not found 报告文件未找到")
            return {'FINISHED'}
        except Exception as e:
            log.error(f"Open report failed: {str(e)}")
            self.report({'ERROR'}, f"Open report failed: {str(e)}")
            return {'CANCELLED'}


# -------------------------
# 注册
# -------------------------
classes = (
    EXPORT_OT_bigworld_model,
    EXPORT_OT_bigworld_animation,
    EXPORT_OT_bigworld_batch,
    EXPORT_OT_bigworld_selected,
    BIGWORLD_OT_validate_scene,
    BIGWORLD_OT_fix_scene,
    BIGWORLD_OT_save_preset,
    BIGWORLD_OT_load_preset,
    BIGWORLD_OT_open_report,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

