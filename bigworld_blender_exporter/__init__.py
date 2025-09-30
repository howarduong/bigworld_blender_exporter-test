# 文件位置: bigworld_blender_exporter/__init__.py
# BigWorld Blender Exporter Plugin - Main Init File

bl_info = {
    "name": "BigWorld Engine Exporter",
    "author": "BigWorld Exporter Team",
    "version": (1, 0, 1),
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
    EnumProperty,
    PointerProperty
)
from bpy.types import (
    AddonPreferences
)
import os
import sys

# Add the addon directory to Python path
addon_dir = os.path.dirname(os.path.realpath(__file__))
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

# Import modules (保持与现有结构一致)
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


# Registration classes（与现有类清单严格一致）
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
    self.layout.operator(
        operators.EXPORT_OT_bigworld_model.bl_idname,
        text="BigWorld Model (.model)"
    )


def _apply_logger_level_from_prefs():
    # 根据插件偏好设置调整日志级别
    try:
        prefs = bpy.context.preferences.addons[__name__].preferences
        lvl = getattr(prefs, "log_level", "INFO")
        logger.set_level(log, lvl)
        log.info(f"Logger level set to {lvl}")
    except Exception:
        # 在注册早期可能取不到上下文，忽略
        pass


def register():
    # 保护性注册，避免重复注册导致异常
    log.info("Registering BigWorld Exporter addon...")

    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            # 已注册则跳过
            pass

    # 菜单挂载
    try:
        bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    except Exception:
        pass

    # 注册属性（PointerProperty 需防止重复定义）
    if not hasattr(bpy.types.Scene, "bigworld_export"):
        bpy.types.Scene.bigworld_export = PointerProperty(type=properties.BigWorldExportSettings)

    if not hasattr(bpy.types.Object, "bigworld_model"):
        bpy.types.Object.bigworld_model = PointerProperty(type=properties.BigWorldModelSettings)

    if not hasattr(bpy.types.Action, "bigworld_animation"):
        bpy.types.Action.bigworld_animation = PointerProperty(type=properties.BigWorldAnimationSettings)

    if not hasattr(bpy.types.Material, "bigworld_material"):
        bpy.types.Material.bigworld_material = PointerProperty(type=properties.BigWorldMaterialSettings)

    # 应用日志级别
    _apply_logger_level_from_prefs()

    log.info("BigWorld Exporter addon registered successfully")


def unregister():
    log.info("Unregistering BigWorld Exporter addon...")

    # 菜单卸载
    try:
        bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    except Exception:
        pass

    # 取消属性注册（存在才删除）
    if hasattr(bpy.types.Scene, "bigworld_export"):
        del bpy.types.Scene.bigworld_export
    if hasattr(bpy.types.Object, "bigworld_model"):
        del bpy.types.Object.bigworld_model
    if hasattr(bpy.types.Action, "bigworld_animation"):
        del bpy.types.Action.bigworld_animation
    if hasattr(bpy.types.Material, "bigworld_material"):
        del bpy.types.Material.bigworld_material

    # 反注册类
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

    log.info("BigWorld Exporter addon unregistered")


if __name__ == "__main__":
    register()
