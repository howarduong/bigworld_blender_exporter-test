import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty

class BigWorldAddonPreferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "default_export_path")
        layout.prop(self, "show_advanced")


def register():
    bpy.utils.register_class(BigWorldAddonPreferences)
    BigWorldAddonPreferences.default_export_path = bpy.props.StringProperty(
        name="Default Export Path",
        description="默认导出路径 (Default export path)",
        default="",
        subtype='DIR_PATH'
    )
    BigWorldAddonPreferences.show_advanced = bpy.props.BoolProperty(
        name="Show Advanced Options",
        description="显示高级选项 (Show advanced options)",
        default=False
    )

def unregister():
    bpy.utils.unregister_class(BigWorldAddonPreferences)
