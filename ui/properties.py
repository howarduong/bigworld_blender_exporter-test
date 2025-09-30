# 文件位置: bigworld_blender_exporter/ui/properties.py
# -*- coding: utf-8 -*-
"""
Blender UI properties for BigWorld exporter.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
    CollectionProperty,
)
from ..formats import vertex_formats


# 动画事件标记
class BW_AnimationMarker(bpy.types.PropertyGroup):
    name: StringProperty(name="Marker Name", default="event")
    frame: IntProperty(name="Frame", default=0)


class BW_ExporterProperties(bpy.types.PropertyGroup):
    # 基础导出设置
    start_frame: IntProperty(
        name="Start Frame",
        default=1,
        min=0,
        description="Start frame for animation export",
    )
    end_frame: IntProperty(
        name="End Frame",
        default=250,
        min=1,
        description="End frame for animation export",
    )
    frame_rate: FloatProperty(
        name="Frame Rate",
        default=30.0,
        min=1.0,
        description="Frame rate for animation export",
    )
    global_scale: FloatProperty(
        name="Global Scale",
        default=1.0,
        min=0.001,
        description="Global scale applied to exported data",
    )
    coordinate_system: EnumProperty(
        name="Coordinate System",
        items=[
            ("Z_UP", "Z Up (Blender)", "Use Blender's default Z-up"),
            ("Y_UP", "Y Up (BigWorld)", "Convert to BigWorld's Y-up"),
        ],
        default="Y_UP",
    )

    # 顶点格式（下拉菜单）
    def _vertex_format_items(self, context):
        return [(f.identifier, f.identifier, f"Stride={f.vertex_size} bytes, Skinning={f.has_skinning}")
                for f in vertex_formats.REGISTERED_FORMATS.values()]

    vertex_format: EnumProperty(
        name="Vertex Format",
        items=_vertex_format_items,
        description="Choose vertex format for .primitives export",
        default="xyznuvtb",
    )

    # 优化选项
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        default=True,
        description="Apply modifiers before export",
    )
    triangulate_mesh: BoolProperty(
        name="Triangulate Mesh",
        default=True,
        description="Triangulate mesh before export",
    )
    optimize_keyframes: BoolProperty(
        name="Optimize Keyframes",
        default=True,
        description="Remove redundant keyframes during animation export",
    )

    # 动画 flags
    loop_animation: BoolProperty(
        name="Loop",
        default=False,
        description="Mark animation as looping",
    )
    cognate: BoolProperty(
        name="Cognate",
        default=False,
        description="Mark animation as cognate",
    )
    alpha: BoolProperty(
        name="Alpha",
        default=False,
        description="Mark animation as alpha",
    )

    # 动画事件标记
    markers: CollectionProperty(type=BW_AnimationMarker)

    # 碰撞体导出
    export_collision: BoolProperty(
        name="Export Collision",
        default=True,
        description="Export BSP collision data from COL_ meshes",
    )

    # 材质扩展属性
    alphaTestEnable: BoolProperty(
        name="Alpha Test",
        default=False,
        description="Enable alpha test in material",
    )
    doubleSided: BoolProperty(
        name="Double Sided",
        default=False,
        description="Render material double sided",
    )
    collisionFlags: IntProperty(
        name="Collision Flags",
        default=0,
        description="Collision flags for material",
    )


# 注册
classes = (
    BW_AnimationMarker,
    BW_ExporterProperties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bw_exporter = bpy.props.PointerProperty(type=BW_ExporterProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.bw_exporter
