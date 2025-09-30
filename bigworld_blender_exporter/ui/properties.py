# 文件位置: bigworld_blender_exporter/ui/properties.py
# Property definitions for BigWorld exporter

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    FloatVectorProperty,
)
from bpy.types import PropertyGroup
from .. import config


class BigWorldExportSettings(PropertyGroup):
    """Main export settings"""

    # Export path
    export_path: StringProperty(
        name="Export Path",
        description="导出路径 (Export path)",
        default="",
        subtype='DIR_PATH'
    )

    # Export options
    export_selected: BoolProperty(
        name="Selected Only",
        description="仅导出选中对象 (Export selected objects only)",
        default=True
    )
    export_mesh: BoolProperty(
        name="Export Mesh",
        description="导出网格 (Export mesh data)",
        default=True
    )
    export_skeleton: BoolProperty(
        name="Export Skeleton",
        description="导出骨架 (Export skeleton data)",
        default=True
    )
    export_animation: BoolProperty(
        name="Export Animation",
        description="导出动画 (Export animation data)",
        default=False
    )
    export_materials: BoolProperty(
        name="Export Materials",
        description="导出材质 (Export material data)",
        default=True
    )
    export_collision: BoolProperty(
        name="Export Collision",
        description="导出碰撞 (Export collision data)",
        default=False
    )
    export_portals: BoolProperty(
        name="Export Portals",
        description="导出门户 (Export portal data)",
        default=True
    )
    export_lod: BoolProperty(
        name="Export LOD",
        description="导出LOD (Export LOD data)",
        default=True
    )

    # Transform settings
    global_scale: FloatProperty(
        name="Scale",
        description="全局缩放 (Global scale factor)",
        default=1.0,
        min=0.001,
        max=1000.0
    )
    coordinate_system: EnumProperty(
        name="Coordinate System",
        description="坐标系 (Coordinate system)",
        items=[
            ('Y_UP', 'Y-Up (BigWorld)', 'Y轴向上 (Y-axis up)'),
            ('Z_UP', 'Z-Up (Blender)', 'Z轴向上 (Z-axis up)')
        ],
        default='Y_UP'
    )

    # Mesh settings
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="应用修改器 (Apply modifiers before export)",
        default=True
    )
    triangulate_mesh: BoolProperty(
        name="Triangulate",
        description="三角化网格 (Triangulate mesh before export)",
        default=True
    )
    optimize_mesh: BoolProperty(
        name="Optimize",
        description="优化网格 (Optimize mesh data)",
        default=True
    )
    smoothing_angle: FloatProperty(
        name="Smoothing Angle",
        description="平滑角度 (Smoothing angle in degrees)",
        default=30.0,
        min=0.0,
        max=180.0
    )
    vertex_format: EnumProperty(
        name="Vertex Format",
        description="顶点格式 (Vertex data format)",
        items=[
            ('STANDARD', 'Standard', '标准格式 (Standard format)'),
            ('SIMPLE', 'Simple', '简单格式 (Simple format)'),
            ('SKINNED', 'Skinned', '骨骼格式 (Skinned format)')
        ],
        default='STANDARD'
    )
    max_weights: IntProperty(
        name="Max Weights",
        description="每顶点最大骨骼权重数 (Max bone weights per vertex)",
        default=4,
        min=1,
        max=8
    )

    # Data export
    export_tangents: BoolProperty(
        name="Export Tangents",
        description="导出切线 (Export tangent data)",
        default=True
    )
    export_vertex_colors: BoolProperty(
        name="Export Vertex Colors",
        description="导出顶点色 (Export vertex color data)",
        default=False
    )

    # LOD settings
    generate_lods: BoolProperty(
        name="Generate LODs",
        description="生成LOD (Generate Level of Detail)",
        default=False
    )
    lod_levels: IntProperty(
        name="LOD Levels",
        description="LOD级别数 (Number of LOD levels)",
        default=3,
        min=1,
        max=5
    )

    # Animation settings
    frame_rate: IntProperty(
        name="Frame Rate",
        description="帧率 (Animation frame rate)",
        default=30,
        min=1,
        max=120
    )
    start_frame: IntProperty(
        name="Start Frame",
        description="起始帧 (Start frame)",
        default=1,
        min=0
    )
    end_frame: IntProperty(
        name="End Frame",
        description="结束帧 (End frame)",
        default=250,
        min=1
    )
    bake_animation: BoolProperty(
        name="Bake Animation",
        description="烘焙动画 (Bake animation to keyframes)",
        default=True
    )
    optimize_keyframes: BoolProperty(
        name="Optimize Keyframes",
        description="优化关键帧 (Optimize keyframes)",
        default=True
    )
    sample_rate: IntProperty(
        name="Sample Rate",
        description="动画采样率 (Animation sample rate fps)",
        default=30,
        min=1,
        max=240
    )

    # Material settings
    texture_path: StringProperty(
        name="Texture Path",
        description="贴图路径 (Texture file path)",
        default="textures"
    )
    copy_textures: BoolProperty(
        name="Copy Textures",
        description="复制贴图 (Copy texture files)",
        default=True
    )
    convert_to_dds: BoolProperty(
        name="Convert to DDS",
        description="转换为DDS格式 (Convert textures to DDS format)",
        default=False
    )
    bake_materials: BoolProperty(
        name="Bake Materials",
        description="烘焙节点材质 (Bake node-based materials to textures)",
        default=False
    )

    # Advanced
    report_path: StringProperty(
        name="Report Path",
        description="导出报告路径 (Export report path)",
        default="//bigworld_export/report.txt"
    )
    preset_path: StringProperty(
        name="Preset Path",
        description="预设文件路径 (Preset file path)",
        default="//bigworld_export/preset.json"
    )


class BigWorldModelSettings(PropertyGroup):
    """Per-object model settings"""

    # Collision settings
    collision_type: EnumProperty(
        name="Collision Type",
        description="碰撞类型 (Collision type)",
        items=config.COLLISION_TYPES,
        default='NONE'
    )
    bsp_type: EnumProperty(
        name="BSP Type",
        description="BSP类型 (BSP type)",
        items=config.BSP_TYPES,
        default='NONE'
    )

    # Rendering settings
    is_static: BoolProperty(
        name="Static",
        description="静态对象 (Static object)",
        default=True
    )
    cast_shadow: BoolProperty(
        name="Cast Shadow",
        description="投射阴影 (Cast shadows)",
        default=True
    )
    receive_shadow: BoolProperty(
        name="Receive Shadow",
        description="接收阴影 (Receive shadows)",
        default=True
    )

    extent: FloatVectorProperty(
        name="Extent",
        description="对象范围 (Object extent)",
        default=(1.0, 1.0, 1.0),
        subtype='XYZ',
        size=3
    )

    # LOD distances
    lod_distance_1: FloatProperty(
        name="LOD 1 Distance",
        description="LOD 1 距离",
        default=10.0,
        min=0.0
    )
    lod_distance_2: FloatProperty(
        name="LOD 2 Distance",
        description="LOD 2 距离",
        default=30.0,
        min=0.0
    )
    lod_distance_3: FloatProperty(
        name="LOD 3 Distance",
        description="LOD 3 距离",
        default=60.0,
        min=0.0
    )


class BigWorldAnimationSettings(PropertyGroup):
    """Per-action animation settings"""

    animation_name: StringProperty(
        name="Animation Name",
        description="动画名称 (Animation name)",
        default=""
    )
    loop: BoolProperty(
        name="Loop",
        description="循环播放 (Loop animation)",
        default=True
    )
    compression: EnumProperty(
        name="Compression",
        description="压缩级别 (Compression level)",
        items=[
            ('NONE', 'None 无', '不压缩'),
            ('LOW', 'Low 低', '低压缩'),
            ('MEDIUM', 'Medium 中', '中等压缩'),
            ('HIGH', 'High 高', '高压缩')
        ],
        default='MEDIUM'
    )
    sample_rate: IntProperty(
        name="Sample Rate",
        description="动画采样率 (fps)",
        default=30,
        min=1,
        max=240
    )
    keyframe_threshold: FloatProperty(
        name="Keyframe Threshold",
        description="关键帧压缩阈值 (Keyframe reduction threshold)",
        default=0.001,
        min=0.0,
        max=1.0
    )


class BigWorldMaterialSettings(PropertyGroup):
    """Per-material settings"""

    material_name: StringProperty(
        name="Material Name",
        description="材质名称 (Material name)",
        default=""
    )
    material_type: EnumProperty(
        name="Material Type",
        description="材质类型 (Material type)",
        items=[
            ('STANDARD', 'Standard 标准', '标准材质'),
            ('TERRAIN', 'Terrain 地形', '地形材质'),
            ('CUSTOM', 'Custom 自定义', '自定义材质')
        ],
        default='STANDARD'
    )
    shader_path: StringProperty(
        name="Shader Path",
        description="Shader路径 (Shader file path)",
        default=""
    )
    texture_path: StringProperty(
        name="Texture Path",
        description="贴图路径 (Texture path)",
        default=""
    )
    use_relative_paths: BoolProperty(
        name="Use Relative Paths",
        description="使用相对路径 (Use relative texture paths)",
        default=True
    )
    bake_material: BoolProperty(
        name="Bake Material",
        description="烘焙节点材质 (Bake node-based material to texture)",
        default=False
    )


# -------------------------
# 注册
# -------------------------
classes = (
    BigWorldExportSettings,
    BigWorldModelSettings,
    BigWorldAnimationSettings,
    BigWorldMaterialSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
