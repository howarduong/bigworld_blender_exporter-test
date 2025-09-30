# bigworld_blender_exporter/ui/panel.py

import bpy
from bpy.props import StringProperty, PointerProperty, BoolProperty
from bpy.types import Panel, Operator, PropertyGroup
from ..utils.path import get_res_root
from ..core.export_engine import export_project
from ..utils.logger import logger

class ExportSettings(PropertyGroup):
    res_root: StringProperty(name="res目录",
        description="设置BigWorld工程的资源res目录（绝对路径）",
        subtype='DIR_PATH')
    target_folder: StringProperty(name="目标导出目录",
        subtype='DIR_PATH')
    open_folder: BoolProperty(name="导出后打开文件夹", default=False)

class BIGWORLD_PT_exporter_panel(Panel):
    bl_label = "BigWorld Exporter"
    bl_idname = "BIGWORLD_PT_exporter_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BigWorld"

    def draw(self, context):
        settings = context.scene.bigworld_exporter_settings
        layout = self.layout

        layout.prop(settings, "res_root")
        layout.prop(settings, "target_folder")
        layout.prop(settings, "open_folder")
        layout.operator("bigworld.export", icon='EXPORT')

class BIGWORLD_OT_export(Operator):
    bl_idname = "bigworld.export"
    bl_label = "导出（符合BigWorld）"

    def execute(self, context):
        settings = context.scene.bigworld_exporter_settings
        if not settings.res_root or not settings.target_folder:
            self.report({"WARNING"}, "请先设置res目录和目标导出目录！")
            return {"CANCELLED"}
        try:
            export_project(settings.res_root, settings.target_folder)
            if settings.open_folder:
                import subprocess, sys
                subprocess.Popen(["explorer" if sys.platform == "win32" else "open", settings.target_folder])
            self.report({"INFO"}, "导出成功！")
            return {"FINISHED"}
        except Exception as ex:
            logger.error(f"导出异常: {ex}")
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}

def register():
    bpy.utils.register_class(ExportSettings)
    bpy.utils.register_class(BIGWORLD_PT_exporter_panel)
    bpy.utils.register_class(BIGWORLD_OT_export)
    bpy.types.Scene.bigworld_exporter_settings = PointerProperty(type=ExportSettings)

def unregister():
    bpy.utils.unregister_class(BIGWORLD_PT_exporter_panel)
    bpy.utils.unregister_class(BIGWORLD_OT_export)
    del bpy.types.Scene.bigworld_exporter_settings
