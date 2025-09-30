# bigworld_blender_exporter/__init__.py

bl_info = {
    "name": "BigWorld Blender Model Exporter Test",
    "description": "将Blender模型、动画、材质导出为BigWorld官方标准格式，完整.res相对路径支持。",
    "author": "BigWorld Blender Exporter Contributors",
    "version": (0, 9, 0),
    "blender": (2, 80, 0),
    "location": "3D视图 > 工具栏 > BigWorld",
    "warning": "",
    "category": "Import-Export",
}

from .ui import panel

def register():
    panel.register()

def unregister():
    panel.unregister()
