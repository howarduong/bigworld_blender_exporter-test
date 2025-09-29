# 文件位置: bigworld_blender_exporter/__init__.py
# BigWorld Blender Exporter Plugin - Main Init File

bl_info = {
    "name": "BigWorld Engine Exporter",
    "author": "BigWorld Exporter Team",
    "version": (1, 0, 0),
    "blender": (4, 5, 3),
    "location": "View3D > Sidebar > BigWorld",
    "description": "导出模型到BigWorld引擎格式 (Export models to BigWorld Engine format)",
    "warning": "",
    "doc_url": "https://github.com/howarduong/BigWorld-Engine-2.0.1",
    "category": "Import-Export",
}

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty
)
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
    AddonPreferences
)
import os
import sys

# Add the addon directory to Python path
addon_dir = os.path.dirname(os.path.realpath(__file__))
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

# Import modules
from .ui import panels, operators, properties
from .core import exporter
from .utils import logger

# Initialize logger
log = logger.get_logger("bigworld_exporter")

class BigWorldExporterPreferences(AddonPreferences):
    bl_idname = __name__

    default_export_path: StringProperty(
        name="Default Export Path",
        description="默认导出路径 (Default export path)",
        default="",
        subtype='DIR_PATH'
    )
    
    auto_check_update: BoolProperty(
        name="Auto-check for Update",
        description="自动检查更新 (Auto-check for updates)",
        default=False
    )
    
    log_level: EnumProperty(
        name="Log Level",
        description="日志级别 (Log level)",
        items=[
            ('DEBUG', 'Debug', '调试 (Debug)'),
            ('INFO', 'Info', '信息 (Info)'),
            ('WARNING', 'Warning', '警告 (Warning)'),
            ('ERROR', 'Error', '错误 (Error)')
        ],
        default='INFO'
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "default_export_path")
        layout.prop(self, "auto_check_update")
        layout.prop(self, "log_level")

# Registration
classes = [
    BigWorldExporterPreferences,
    properties.BigWorldExportSettings,
    properties.BigWorldModelSettings,
    properties.BigWorldAnimationSettings,
    properties.BigWorldMaterialSettings,
    operators.EXPORT_OT_bigworld_model,
    operators.EXPORT_OT_bigworld_animation,
    operators.EXPORT_OT_bigworld_batch,
    operators.BIGWORLD_OT_validate_scene,
    operators.BIGWORLD_OT_fix_scene,
    panels.BIGWORLD_PT_export_panel,
    panels.BIGWORLD_PT_model_settings,
    panels.BIGWORLD_PT_animation_settings,
    panels.BIGWORLD_PT_material_settings,
    panels.BIGWORLD_PT_advanced_settings,
]

def menu_func_export(self, context):
    self.layout.operator(operators.EXPORT_OT_bigworld_model.bl_idname, 
                        text="BigWorld Model (.model)")

def register():
    log.info("Registering BigWorld Exporter addon...")
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    # Register properties
    bpy.types.Scene.bigworld_export = PointerProperty(type=properties.BigWorldExportSettings)
    bpy.types.Object.bigworld_model = PointerProperty(type=properties.BigWorldModelSettings)
    bpy.types.Action.bigworld_animation = PointerProperty(type=properties.BigWorldAnimationSettings)
    bpy.types.Material.bigworld_material = PointerProperty(type=properties.BigWorldMaterialSettings)
    
    log.info("BigWorld Exporter addon registered successfully")

def unregister():
    log.info("Unregistering BigWorld Exporter addon...")
    
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    # Unregister properties
    del bpy.types.Scene.bigworld_export
    del bpy.types.Object.bigworld_model
    del bpy.types.Action.bigworld_animation
    del bpy.types.Material.bigworld_material
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    log.info("BigWorld Exporter addon unregistered")

if __name__ == "__main__":
    register()