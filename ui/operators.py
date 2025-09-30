# 文件位置: bigworld_blender_exporter/ui/operators.py
# Operator definitions for BigWorld exporter

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from ..core.exporter import BigWorldExporter
from ..utils.logger import get_logger
import os

class EXPORT_OT_bigworld_model(Operator):
    bl_idname = "export.bigworld_model"
    bl_label = "Export Model 导出模型"
    bl_description = "Export selected or all models to BigWorld format\n导出选中或全部模型为BigWorld格式"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            settings = context.scene.bigworld_export
            logger = get_logger("operators")
            from ..utils.validation import validate_export_settings, validate_scene
            
            # Validate export path
            if not settings.export_path:
                self.report({'ERROR'}, "Please set export path! 请设置导出路径！")
                return {'CANCELLED'}

            # Validate export settings
            setting_issues = validate_export_settings(settings)
            if setting_issues:
                # Show first as error, rest as warnings
                self.report({'ERROR'}, setting_issues[0])
                for issue in setting_issues[1:]:
                    self.report({'WARNING'}, issue)
                return {'CANCELLED'}

            # Validate scene readiness
            scene_issues = validate_scene(context)
            if scene_issues:
                self.report({'ERROR'}, scene_issues[0])
                for issue in scene_issues[1:]:
                    self.report({'WARNING'}, issue)
                return {'CANCELLED'}
            
            # Create export directory if it doesn't exist
            os.makedirs(settings.export_path, exist_ok=True)
            
            # Initialize exporter
            exporter = BigWorldExporter(context, settings)
            
            # Start export process
            logger.info("Starting model export...")
            exporter.export()
            
            self.report({'INFO'}, f"Model export finished! Exported to: {settings.export_path}")
            # Update status text
            if hasattr(context.scene, 'bigworld_export_status'):
                context.scene.bigworld_export_status = "Export complete 导出完成"
            return {'FINISHED'}
            
        except Exception as e:
            logger = get_logger("operators")
            logger.error(f"Export failed: {str(e)}")
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            if hasattr(context.scene, 'bigworld_export_status'):
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
            logger = get_logger("operators")
            from ..utils.validation import validate_export_settings
            
            if not settings.export_path:
                self.report({'ERROR'}, "Please set export path! 请设置导出路径！")
                return {'CANCELLED'}

            # Validate settings (frame range, scale, etc.)
            setting_issues = validate_export_settings(settings)
            if setting_issues:
                self.report({'ERROR'}, setting_issues[0])
                for issue in setting_issues[1:]:
                    self.report({'WARNING'}, issue)
                return {'CANCELLED'}
            
            # Create animations subfolder
            anim_path = os.path.join(settings.export_path, "animations")
            os.makedirs(anim_path, exist_ok=True)
            
            # Find objects with animation data
            animated_objects = []
            for obj in context.selected_objects:
                if obj.animation_data and obj.animation_data.action:
                    animated_objects.append(obj)
            
            if not animated_objects:
                self.report({'WARNING'}, "No animated objects found! 未找到动画对象！")
                return {'CANCELLED'}
            
            # Export animations
            from ..core.animation_processor import AnimationProcessor
            processor = AnimationProcessor()
            
            for obj in animated_objects:
                action = obj.animation_data.action
                anim_data = processor.process(obj, action, settings)
                
                # Write animation file
                anim_file = os.path.join(anim_path, f"{obj.name}.animation")
                from ..formats.animation_format import export_animation_file
                export_animation_file(anim_file, anim_data)
            
            self.report({'INFO'}, f"Animation export finished! Exported {len(animated_objects)} animations.")
            if hasattr(context.scene, 'bigworld_export_status'):
                context.scene.bigworld_export_status = "Animation export complete 动画导出完成"
            return {'FINISHED'}
            
        except Exception as e:
            logger = get_logger("operators")
            logger.error(f"Animation export failed: {str(e)}")
            self.report({'ERROR'}, f"Animation export failed: {str(e)}")
            if hasattr(context.scene, 'bigworld_export_status'):
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
            logger = get_logger("operators")
            
            if not settings.export_path:
                self.report({'ERROR'}, "Please set export path! 请设置导出路径！")
                return {'CANCELLED'}
            
            # Export all scenes
            original_scene = context.scene
            exported_count = 0
            
            for scene in bpy.data.scenes:
                # Switch to scene
                context.window.scene = scene
                
                # Export scene
                exporter = BigWorldExporter(context, settings)
                exporter.export()
                exported_count += 1
            
            # Restore original scene
            context.window.scene = original_scene
            
            self.report({'INFO'}, f"Batch export finished! Exported {exported_count} scenes.")
            return {'FINISHED'}
            
        except Exception as e:
            logger = get_logger("operators")
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
            logger = get_logger("operators")
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
            from ..utils.validation import validate_scene
            logger = get_logger("operators")
            
            issues = validate_scene(context)
            
            if not issues:
                self.report({'INFO'}, "Scene validation passed! 场景验证通过！")
                return {'FINISHED'}
            else:
                # Report issues
                for issue in issues:
                    self.report({'WARNING'}, issue)
                
                self.report({'INFO'}, f"Found {len(issues)} issues. 发现 {len(issues)} 个问题。")
                return {'FINISHED'}
                
        except Exception as e:
            logger = get_logger("operators")
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
            logger = get_logger("operators")
            
            fixes_applied = fix_scene(context)
            
            if fixes_applied:
                self.report({'INFO'}, f"Applied {fixes_applied} fixes! 应用了 {fixes_applied} 个修复！")
            else:
                self.report({'INFO'}, "No fixes needed! 无需修复！")
            
            return {'FINISHED'}
            
        except Exception as e:
            logger = get_logger("operators")
            logger.error(f"Auto fix failed: {str(e)}")
            self.report({'ERROR'}, f"Auto fix failed: {str(e)}")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(EXPORT_OT_bigworld_model)
    bpy.utils.register_class(EXPORT_OT_bigworld_animation)
    bpy.utils.register_class(EXPORT_OT_bigworld_batch)
    bpy.utils.register_class(EXPORT_OT_bigworld_selected)
    bpy.utils.register_class(BIGWORLD_OT_validate_scene)
    bpy.utils.register_class(BIGWORLD_OT_fix_scene)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_bigworld_model)
    bpy.utils.unregister_class(EXPORT_OT_bigworld_animation)
    bpy.utils.unregister_class(EXPORT_OT_bigworld_batch)
    bpy.utils.unregister_class(EXPORT_OT_bigworld_selected)
    bpy.utils.unregister_class(BIGWORLD_OT_validate_scene)
    bpy.utils.unregister_class(BIGWORLD_OT_fix_scene)
