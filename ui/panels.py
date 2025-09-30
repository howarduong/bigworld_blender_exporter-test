# 文件位置: bigworld_blender_exporter/ui/panels.py
# -*- coding: utf-8 -*-
"""
UI Panel definitions for BigWorld exporter
"""

import bpy
from bpy.types import Panel


class BIGWORLD_PT_export_panel(Panel):
    """Main export panel"""
    bl_label = "BigWorld Exporter"
    bl_idname = "BIGWORLD_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BigWorld"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bw_exporter

        # Export path
        col = layout.column(align=True)
        col.label(text="Export Settings 导出设置:", icon='EXPORT')
        col.prop(settings, "export_path", text="Path 路径")

        # Export options
        box = layout.box()
        box.label(text="Export Options 导出选项:", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(settings, "export_selected", text="Selected Only 仅选中")
        col.separator()
        row = col.row(align=True)
        row.prop(settings, "export_mesh", text="Mesh 网格", icon='MESH_DATA')
        row.prop(settings, "export_skeleton", text="Skeleton 骨架", icon='ARMATURE_DATA')
        row = col.row(align=True)
        row.prop(settings, "export_animation", text="Animation 动画", icon='ACTION')
        row.prop(settings, "export_materials", text="Materials 材质", icon='MATERIAL')
        col.prop(settings, "export_collision", text="Collision 碰撞", icon='PHYSICS')

        # Transform
        box = layout.box()
        box.label(text="Transform 变换:", icon='ORIENTATION_LOCAL')
        col = box.column(align=True)
        col.prop(settings, "global_scale", text="Scale 缩放")
        col.prop(settings, "coordinate_system", text="Coords 坐标系")

        # Export buttons
        layout.separator()
        col = layout.column(align=True)
        col.scale_y = 1.5
        if context.selected_objects:
            text = f"Export Selected ({len(context.selected_objects)}) 导出选中"
        else:
            text = "Export All 导出全部"
        col.operator("export.bigworld_model", text=text, icon='EXPORT')
        if settings.export_animation:
            col.operator("export.bigworld_animation", text="Export Animations 导出动画", icon='ACTION')

        # Validation
        layout.separator()
        row = layout.row(align=True)
        row.operator("bigworld.validate_scene", text="Validate 验证", icon='CHECKMARK')
        row.operator("bigworld.fix_scene", text="Auto Fix 自动修复", icon='TOOL_SETTINGS')

        # Status
        layout.separator()
        box = layout.box()
        box.label(text="Status 状态:", icon='INFO')
        if hasattr(context.scene, 'bigworld_export_status'):
            box.label(text=context.scene.bigworld_export_status)
        else:
            box.label(text="Ready 就绪")


class BIGWORLD_PT_model_settings(Panel):
    """Model settings panel"""
    bl_label = "Model Settings"
    bl_idname = "BIGWORLD_PT_model_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BigWorld"
    bl_parent_id = "BIGWORLD_PT_export_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bw_exporter

        # Mesh settings
        box = layout.box()
        box.label(text="Mesh Options 网格选项:", icon='MESH_DATA')
        col = box.column(align=True)
        col.prop(settings, "apply_modifiers", text="Apply Modifiers 应用修改器")
        col.prop(settings, "triangulate_mesh", text="Triangulate 三角化")
        col.separator()
        col.prop(settings, "vertex_format", text="Format 格式")
        col.prop(settings, "use_32bit_index", text="Force 32-bit Indices 强制32位索引")

        # Data export
        box = layout.box()
        box.label(text="Export Data 导出数据:", icon='FILE')
        col = box.column(align=True)
        col.prop(settings, "export_tangents", text="Tangents 切线")
        col.prop(settings, "export_vertex_colors", text="Vertex Colors 顶点色")


class BIGWORLD_PT_animation_settings(Panel):
    """Animation settings panel"""
    bl_label = "Animation Settings"
    bl_idname = "BIGWORLD_PT_animation_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BigWorld"
    bl_parent_id = "BIGWORLD_PT_export_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.bw_exporter.export_animation

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bw_exporter

        box = layout.box()
        box.label(text="Animation Export 动画导出:", icon='ACTION')
        col = box.column(align=True)
        col.prop(settings, "frame_rate", text="Frame Rate 帧率")
        col.prop(settings, "start_frame", text="Start Frame 起始帧")
        col.prop(settings, "end_frame", text="End Frame 结束帧")
        col.prop(settings, "optimize_keyframes", text="Optimize Keyframes 优化关键帧")
        col.prop(settings, "loop_animation", text="Loop 循环")
        col.prop(settings, "cognate", text="Cognate 同源")
        col.prop(settings, "alpha", text="Alpha 混合")

        # Markers UI
        col.label(text="Markers 事件标记:")
        row = col.row()
        row.template_list("UI_UL_list", "bw_animation_markers",
                          settings, "markers",
                          settings, "marker_index")
        col.operator("bigworld.add_marker", text="Add Marker 添加标记")
        col.operator("bigworld.remove_marker", text="Remove Marker 删除标记")


class BIGWORLD_PT_material_settings(Panel):
    """Material settings panel"""
    bl_label = "Material Settings"
    bl_idname = "BIGWORLD_PT_material_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BigWorld"
    bl_parent_id = "BIGWORLD_PT_export_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.bw_exporter.export_materials

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bw_exporter

        box = layout.box()
        box.label(text="Material Export 材质导出:", icon='MATERIAL')
        col = box.column(align=True)
        col.prop(settings, "texture_path", text="Texture Path 贴图路径")
        col.prop(settings, "copy_textures", text="Copy Textures 复制贴图")
        col.prop(settings, "convert_to_dds", text="Convert to DDS 转换DDS")

        # 扩展属性
        col.separator()
        col.prop(settings, "alphaTestEnable", text="Alpha Test 启用透明测试")
        col.prop(settings, "doubleSided", text="Double Sided 双面渲染")
        col.prop(settings, "collisionFlags", text="Collision Flags 碰撞标志")
        col.prop(settings, "zBufferWrite", text="Z Buffer Write 深度写入")
        col.prop(settings, "castShadow", text="Cast Shadow 投射阴影")
        col.prop(settings, "receiveShadow", text="Receive Shadow 接收阴影")


class BIGWORLD_PT_batch_export(Panel):
    """Batch export panel"""
    bl_label = "Batch Export"
    bl_idname = "BIGWORLD_PT_batch_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BigWorld"
    bl_parent_id = "BIGWORLD_PT_export_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Batch Export 批量导出:", icon='EXPORT')
        col = box.column(align=True)
        col.operator("export.bigworld_batch", text="Export All Scenes 导出所有场景", icon='SCENE_DATA')
        col.operator("export.bigworld_selected", text="Export Selected 导出选中", icon='RESTRICT_SELECT_OFF')
