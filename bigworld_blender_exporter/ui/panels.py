# 文件位置: bigworld_blender_exporter/ui/panels.py
# UI Panel definitions for BigWorld exporter

import bpy
from bpy.types import Panel
import os


def _count_scene_assets(context):
    sel_objs = list(context.selected_objects)
    all_objs = list(context.scene.objects)
    meshes_sel = sum(1 for o in sel_objs if o.type == 'MESH')
    arm_sel = sum(1 for o in sel_objs if o.type == 'ARMATURE')
    meshes_all = sum(1 for o in all_objs if o.type == 'MESH')
    arm_all = sum(1 for o in all_objs if o.type == 'ARMATURE')
    actions = len(bpy.data.actions)
    mats = len(bpy.data.materials)
    return {
        "sel_objs": len(sel_objs),
        "meshes_sel": meshes_sel,
        "arm_sel": arm_sel,
        "meshes_all": meshes_all,
        "arm_all": arm_all,
        "actions": actions,
        "materials": mats,
    }


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
        scene = context.scene
        settings = scene.bigworld_export
        stats = _count_scene_assets(context)

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

        # Transform / Coordinate system
        box = layout.box()
        box.label(text="Transform 变换:", icon='ORIENTATION_LOCAL')
        col = box.column(align=True)
        col.prop(settings, "global_scale", text="Scale 缩放")
        col.prop(settings, "coordinate_system", text="Coords 坐标系")

        # Export buttons
        layout.separator()
        col = layout.column(align=True)
        col.scale_y = 1.2
        if context.selected_objects:
            text = f"Export Selected ({stats['sel_objs']}) 导出选中"
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

        # Status and scene stats
        layout.separator()
        box = layout.box()
        box.label(text="Status 状态:", icon='INFO')
        if hasattr(context.scene, 'bigworld_export_status'):
            box.label(text=context.scene.bigworld_export_status)
        else:
            box.label(text="Ready 就绪")
        box.separator()
        row = box.row(align=True)
        row.label(text=f"Meshes 网格: {stats['meshes_sel']}/{stats['meshes_all']}")
        row.label(text=f"Armatures 骨架: {stats['arm_sel']}/{stats['arm_all']}")
        row = box.row(align=True)
        row.label(text=f"Actions 动作库: {stats['actions']}")
        row.label(text=f"Materials 材质: {stats['materials']}")


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
        settings = context.scene.bigworld_export

        # Mesh settings
        box = layout.box()
        box.label(text="Mesh Options 网格选项:", icon='MESH_DATA')
        col = box.column(align=True)
        col.prop(settings, "apply_modifiers", text="Apply Modifiers 应用修改器")
        col.prop(settings, "triangulate_mesh", text="Triangulate 三角化")
        col.prop(settings, "optimize_mesh", text="Optimize 优化")
        col.separator()
        col.prop(settings, "smoothing_angle", text="Smoothing 平滑角度")
        col.prop(settings, "vertex_format", text="Format 格式")

        # Data export
        box = layout.box()
        box.label(text="Export Data 导出数据:", icon='FILE')
        col = box.column(align=True)
        col.prop(settings, "export_tangents", text="Tangents 切线")
        col.prop(settings, "export_vertex_colors", text="Vertex Colors 顶点色")

        # LOD settings
        box = layout.box()
        box.label(text="LOD Settings LOD设置:", icon='MOD_SIMPLIFY')
        col = box.column(align=True)
        col.prop(settings, "generate_lods", text="Generate LODs 生成LOD")
        if settings.generate_lods:
            col.prop(settings, "lod_levels", text="Levels 级别")

        # Per-object LOD distances
        if context.active_object and hasattr(context.active_object, "bigworld_model"):
            obj_settings = context.active_object.bigworld_model
            col.separator()
            col.label(text="LOD Distances LOD距离:")
            col.prop(obj_settings, "lod_distance_1", text="LOD 1")
            col.prop(obj_settings, "lod_distance_2", text="LOD 2")
            col.prop(obj_settings, "lod_distance_3", text="LOD 3")

        # Per-object settings
        if context.active_object and hasattr(context.active_object, "bigworld_model"):
            box = layout.box()
            box.label(text="Object Settings 对象设置:", icon='OBJECT_DATA')
            obj_settings = context.active_object.bigworld_model
            col = box.column(align=True)
            col.prop(obj_settings, "collision_type", text="Collision 碰撞")
            col.prop(obj_settings, "bsp_type", text="BSP Type BSP类型")
            col.separator()
            row = col.row(align=True)
            row.prop(obj_settings, "is_static", text="Static 静态")
            row.prop(obj_settings, "cast_shadow", text="Cast Shadow 投射阴影")
            col.prop(obj_settings, "receive_shadow", text="Receive Shadow 接收阴影")
            col.prop(obj_settings, "extent", text="Extent 范围")


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
        return context.scene.bigworld_export.export_animation

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bigworld_export

        box = layout.box()
        box.label(text="Animation Export 动画导出:", icon='ACTION')
        col = box.column(align=True)
        col.prop(settings, "frame_rate", text="Frame Rate 帧率")
        col.prop(settings, "start_frame", text="Start Frame 起始帧")
        col.prop(settings, "end_frame", text="End Frame 结束帧")
        col.prop(settings, "bake_animation", text="Bake Animation 烘焙动画")
        col.prop(settings, "optimize_keyframes", text="Optimize Keyframes 优化关键帧")

        # 动画导出按钮
        layout.separator()
        layout.operator("export.bigworld_animation", text="Export Animation 导出动画", icon='ACTION')


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
        return context.scene.bigworld_export.export_materials

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bigworld_export

        box = layout.box()
        box.label(text="Material Export 材质导出:", icon='MATERIAL')
        col = box.column(align=True)
        col.prop(settings, "texture_path", text="Texture Path 贴图路径")
        col.prop(settings, "copy_textures", text="Copy Textures 复制贴图")
        col.prop(settings, "convert_to_dds", text="Convert to DDS 转DDS")


class BIGWORLD_PT_advanced_settings(Panel):
    """Advanced settings panel"""
    bl_label = "Advanced Settings"
    bl_idname = "BIGWORLD_PT_advanced_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BigWorld"
    bl_parent_id = "BIGWORLD_PT_export_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bigworld_export

        # Performance settings
        box = layout.box()
        box.label(text="Performance 性能:", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(settings, "optimize_mesh", text="Optimize Mesh 优化网格")
        col.prop(settings, "optimize_keyframes", text="Optimize Keyframes 优化关键帧")

        # File settings
        box = layout.box()
        box.label(text="File Settings 文件设置:", icon='FILE')
        col = box.column(align=True)
        col.prop(settings, "copy_textures", text="Copy Textures 复制贴图")
        col.prop(settings, "convert_to_dds", text="Convert to DDS 转DDS")

        # Debug settings
        box = layout.box()
        box.label(text="Debug 调试:", icon='CONSOLE')
        col = box.column(align=True)
        col.prop(settings, "export_vertex_colors", text="Export Vertex Colors 导出顶点色")
        col.prop(settings, "export_tangents", text="Export Tangents 导出切线")


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

        # 注意：此按钮依赖操作符 "export.bigworld_selected" 是否存在
        # 为避免报错，保持你仓库当前写法；若操作符不存在，可改为使用 "export.bigworld_model" 并要求启用“仅选中”
        col.operator("export.bigworld_selected", text="Export Selected 导出选中", icon='RESTRICT_SELECT_OFF')
