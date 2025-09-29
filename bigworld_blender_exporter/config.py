# 文件位置: bigworld_blender_exporter/config.py
# Configuration constants and defaults

import os
import json
import bpy
from .utils.logger import get_logger

logger = get_logger("config")

# -------------------------
# Version info
# -------------------------
PLUGIN_VERSION = (1, 0, 0)
BIGWORLD_VERSION = "2.0.1"

# -------------------------
# File extensions
# -------------------------
MODEL_EXT = ".model"
VISUAL_EXT = ".visual"
PRIMITIVES_EXT = ".primitives"
ANIMATION_EXT = ".animation"
MATERIAL_EXT = ".mfm"

# -------------------------
# Binary format constants
# -------------------------
PRIMITIVES_MAGIC = 0x42570100  # BigWorld primitives magic number
PRIMITIVES_VERSION = 0x01000000

# -------------------------
# Vertex formats
# -------------------------
VERTEX_FORMAT_STANDARD = "xyznuviiiwwtb"
VERTEX_FORMAT_SIMPLE = "xyznuv"
VERTEX_FORMAT_SKINNED = "xyznuviiiww"

VERTEX_FORMATS = {
    'STANDARD': {
        'format': VERTEX_FORMAT_STANDARD,
        'size': 44,  # bytes per vertex
        'description': "标准格式 (Standard format with tangents)"
    },
    'SIMPLE': {
        'format': VERTEX_FORMAT_SIMPLE,
        'size': 24,
        'description': "简单格式 (Simple format without skinning)"
    },
    'SKINNED': {
        'format': VERTEX_FORMAT_SKINNED,
        'size': 36,
        'description': "骨骼格式 (Skinned format without tangents)"
    }
}

# -------------------------
# Coordinate system
# -------------------------
COORD_SYSTEM_BLENDER = "Z_UP"
COORD_SYSTEM_BIGWORLD = "Y_UP"

# -------------------------
# Animation defaults
# -------------------------
DEFAULT_FPS = 30
DEFAULT_START_FRAME = 1
DEFAULT_END_FRAME = 250
MAX_BONE_INFLUENCES = 3
MAX_BONES = 256

# -------------------------
# Material defaults
# -------------------------
DEFAULT_SHADER = "shaders/std_effects.fx"
DEFAULT_TEXTURE_PATH = "maps"
SUPPORTED_TEXTURE_FORMATS = ['.dds', '.tga', '.png', '.jpg', '.bmp']

# -------------------------
# LOD settings
# -------------------------
LOD_DISTANCES = [10.0, 25.0, 50.0, 100.0]
LOD_REDUCTION_RATIOS = [1.0, 0.5, 0.25, 0.1]

# -------------------------
# Export defaults
# -------------------------
DEFAULT_SCALE = 1.0
DEFAULT_SMOOTHING_ANGLE = 30.0  # degrees

# -------------------------
# Collision types
# -------------------------
COLLISION_TYPES = [
    ('NONE', 'None', '无碰撞 (No collision)'),
    ('BOX', 'Box', '盒体碰撞 (Box collision)'),
    ('SPHERE', 'Sphere', '球体碰撞 (Sphere collision)'),
    ('CYLINDER', 'Cylinder', '圆柱体碰撞 (Cylinder collision)'),
    ('MESH', 'Mesh', '网格碰撞 (Mesh collision)'),
    ('CONVEX', 'Convex Hull', '凸包碰撞 (Convex hull collision)')
]

# -------------------------
# BSP types
# -------------------------
BSP_TYPES = [
    ('NONE', 'None', '无BSP (No BSP)'),
    ('SOLID', 'Solid', '实体 (Solid BSP)'),
    ('PORTAL', 'Portal', '门户 (Portal BSP)'),
    ('DETAIL', 'Detail', '细节 (Detail BSP)')
]

# -------------------------
# Material types
# -------------------------
MATERIAL_TYPES = [
    ('STANDARD', 'Standard', '标准材质 (Standard material)'),
    ('SKINNED', 'Skinned', '骨骼材质 (Skinned material)'),
    ('EFFECT', 'Effect', '特效材质 (Effect material)'),
    ('FLORA', 'Flora', '植被材质 (Flora material)'),
    ('WATER', 'Water', '水体材质 (Water material)')
]

# -------------------------
# Paths
# -------------------------
ANIMATIONS_SUBFOLDER = "animations"
TEXTURES_SUBFOLDER = "textures"
MODELS_SUBFOLDER = "models"
MATERIALS_SUBFOLDER = "materials"

# -------------------------
# Validation limits
# -------------------------
MAX_VERTICES_PER_MESH = 65535
MAX_TRIANGLES_PER_MESH = 65535
MAX_UV_CHANNELS = 4
MAX_VERTEX_COLORS = 2

# -------------------------
# Error / Warning / Info messages
# -------------------------
ERROR_NO_MESH = "对象没有网格数据 (Object has no mesh data)"
ERROR_NO_UV = "网格没有UV贴图 (Mesh has no UV map)"
ERROR_TOO_MANY_VERTICES = f"顶点数超过限制 {MAX_VERTICES_PER_MESH} (Too many vertices)"
ERROR_TOO_MANY_TRIANGLES = f"三角形数超过限制 {MAX_TRIANGLES_PER_MESH} (Too many triangles)"
ERROR_NO_ARMATURE = "没有找到骨架 (No armature found)"
ERROR_INVALID_BONE_COUNT = f"骨骼数超过限制 {MAX_BONES} (Too many bones)"

WARNING_NO_MATERIAL = "网格没有材质 (Mesh has no material)"
WARNING_MULTIPLE_UV = "多个UV层将只导出活动层 (Multiple UV layers, only active will be exported)"
WARNING_NON_TRIANGULATED = "网格未三角化 (Mesh is not triangulated)"

INFO_EXPORT_START = "开始导出 (Starting export)"
INFO_EXPORT_COMPLETE = "导出完成 (Export complete)"
INFO_COLLECTING_DATA = "收集数据 (Collecting data)"
INFO_WRITING_FILES = "写入文件 (Writing files)"
INFO_OPTIMIZING = "优化数据 (Optimizing data)"

# -------------------------
# Preset save/load
# -------------------------
PRESET_FILE = os.path.join(bpy.utils.user_resource('SCRIPTS'), "bigworld_export_presets.json")


def save_preset(settings, name="default"):
    """保存导出预设到 JSON 文件"""
    try:
        presets = {}
        if os.path.exists(PRESET_FILE):
            with open(PRESET_FILE, "r", encoding="utf-8") as f:
                presets = json.load(f)

        presets[name] = {
            "export_path": settings.export_path,
            "export_selected": settings.export_selected,
            "export_mesh": settings.export_mesh,
            "export_skeleton": settings.export_skeleton,
            "export_animation": settings.export_animation,
            "export_materials": settings.export_materials,
            "triangulate_mesh": settings.triangulate_mesh,
            "apply_modifiers": settings.apply_modifiers,
            "bake_materials": settings.bake_materials,
            "sample_rate": settings.sample_rate,
            "start_frame": settings.start_frame,
            "end_frame": settings.end_frame,
            "report_path": settings.report_path,
        }

        with open(PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4)

        logger.info(f"Preset '{name}' saved to {PRESET_FILE}")
    except Exception as e:
        logger.error(f"Failed to save preset: {str(e)}")


def load_preset(settings, name="default"):
    """从 JSON 文件加载导出预设"""
    try:
        if not os.path.exists(PRESET_FILE):
            logger.warning("No preset file found")
            return

        with open(PRESET_FILE, "r", encoding="utf-8") as f:
            presets = json.load(f)

        if name not in presets:
            logger.warning(f"Preset '{name}' not found")
            return

        preset = presets[name]
        for key, value in preset.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        logger.info(f"Preset '{name}' loaded")
    except Exception as e:
        logger.error(f"Failed to load preset: {str(e)}")
