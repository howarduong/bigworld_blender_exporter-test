# 文件位置: bigworld_blender_exporter/utils/validation.py
# Data validation utilities for BigWorld export

import bpy
from .. import config
from .logger import get_logger

logger = get_logger("validation")

def validate_mesh(obj):
    """Validate mesh object for export"""
    if not hasattr(obj.data, 'vertices'):
        return False, config.ERROR_NO_MESH
    if len(obj.data.vertices) > config.MAX_VERTICES_PER_MESH:
        return False, config.ERROR_TOO_MANY_VERTICES
    if len(obj.data.polygons) * 3 > config.MAX_TRIANGLES_PER_MESH:
        return False, config.ERROR_TOO_MANY_TRIANGLES
    if not obj.data.uv_layers:
        return False, config.ERROR_NO_UV
    return True, None

def validate_armature(obj):
    """Validate armature object for export"""
    if obj.type != 'ARMATURE':
        return False, "Object is not an armature (对象不是骨架)"
    
    armature = obj.data
    if len(armature.bones) > config.MAX_BONES:
        return False, config.ERROR_INVALID_BONE_COUNT
    
    return True, None

def validate_scene(context):
    """Validate entire scene for export"""
    issues = []
    
    # Check for objects to export
    objects_to_check = []
    if context.scene.bigworld_export.export_selected:
        objects_to_check = [obj for obj in context.selected_objects if obj.type in ['MESH', 'ARMATURE']]
    else:
        objects_to_check = [obj for obj in context.scene.objects if obj.type in ['MESH', 'ARMATURE']]
    
    if not objects_to_check:
        issues.append("No objects to export (没有可导出的对象)")
        return issues
    
    # Validate each object
    for obj in objects_to_check:
        if obj.type == 'MESH':
            valid, msg = validate_mesh(obj)
            if not valid:
                issues.append(f"{obj.name}: {msg}")
        elif obj.type == 'ARMATURE':
            valid, msg = validate_armature(obj)
            if not valid:
                issues.append(f"{obj.name}: {msg}")
    
    # Check for materials
    for obj in objects_to_check:
        if obj.type == 'MESH' and not obj.data.materials:
            issues.append(f"{obj.name}: {config.WARNING_NO_MATERIAL}")
    
    # Check for UV layers
    for obj in objects_to_check:
        if obj.type == 'MESH' and len(obj.data.uv_layers) > 1:
            issues.append(f"{obj.name}: {config.WARNING_MULTIPLE_UV}")
    
    return issues

def fix_scene(context):
    """Auto-fix common export issues"""
    fixes_applied = 0
    
    # Get objects to fix
    objects_to_fix = []
    if context.scene.bigworld_export.export_selected:
        objects_to_fix = [obj for obj in context.selected_objects if obj.type in ['MESH', 'ARMATURE']]
    else:
        objects_to_fix = [obj for obj in context.scene.objects if obj.type in ['MESH', 'ARMATURE']]
    
    for obj in objects_to_fix:
        if obj.type == 'MESH':
            # Fix mesh issues
            mesh = obj.data
            
            # Add default material if none
            if not mesh.materials:
                mat = bpy.data.materials.new(name=f"{obj.name}_Material")
                mat.use_nodes = True
                mesh.materials.append(mat)
                fixes_applied += 1
                logger.info(f"Added default material to {obj.name}")
            
            # Add UV layer if none
            if not mesh.uv_layers:
                mesh.uv_layers.new(name="UVMap")
                fixes_applied += 1
                logger.info(f"Added UV layer to {obj.name}")
            
            # Triangulate if needed
            if not all(len(poly.vertices) == 3 for poly in mesh.polygons):
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.quads_convert_to_tris()
                bpy.ops.object.mode_set(mode='OBJECT')
                fixes_applied += 1
                logger.info(f"Triangulated {obj.name}")
    
    return fixes_applied

def validate_export_settings(settings):
    """Validate export settings"""
    issues = []
    
    if not settings.export_path:
        issues.append("Export path not set (未设置导出路径)")
    
    if settings.global_scale <= 0:
        issues.append("Invalid scale value (无效的缩放值)")
    
    if settings.start_frame >= settings.end_frame:
        issues.append("Invalid frame range (无效的帧范围)")
    
    return issues
