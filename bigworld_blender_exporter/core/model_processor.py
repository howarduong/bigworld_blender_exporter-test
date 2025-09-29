# 文件位置: bigworld_blender_exporter/core/model_processor.py
# Model data processing for BigWorld export

import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from ..utils import logger
from ..utils import math_utils
from ..utils.validation import validate_mesh, validate_armature
from .. import config

class ModelProcessor:
    """
    Responsible for collecting and processing model data.
    负责模型数据的收集与处理。
    """
    
    def __init__(self):
        self.vertex_cache = {}
        self.index_cache = {}

    def process(self, obj, settings):
        """Process mesh object for export"""
        logger.info(f"Processing mesh object: {obj.name}")
        
        # Validate mesh
        valid, msg = validate_mesh(obj)
        if not valid:
            logger.error(f"Mesh validation failed for {obj.name}: {msg}")
            return None
        
        # Get mesh data
        mesh = obj.data
        
        # Apply modifiers if requested
        if settings.apply_modifiers:
            mesh = self._apply_modifiers(obj, mesh)
        
        # Triangulate if requested
        if settings.triangulate_mesh:
            mesh = self._triangulate_mesh(mesh)
        
        # Ensure triangulated faces and recalc normals via BMesh for compatibility
        mesh.calc_loop_triangles()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        
        # Collect vertex data
        vertices = self._collect_vertices(obj, mesh, settings)
        
        # Build sequential indices matching the vertices list
        indices = list(range(len(vertices)))
        
        # Calculate bounding box
        bbox_min, bbox_max = math_utils.calculate_bounding_box(vertices)
        
        # Build model data
        model_data = {
            'vertices': vertices,
            'indices': indices,
            'bbox_min': bbox_min,
            'bbox_max': bbox_max,
            'extent': math_utils.calculate_extent(bbox_min, bbox_max),
            'vertex_count': len(vertices),
            'triangle_count': len(indices) // 3,
            'has_armature': obj.find_armature() is not None,
            'materials': self._collect_materials(obj)
        }
        
        logger.info(f"Processed {len(vertices)} vertices and {len(indices)} indices for {obj.name}")
        return model_data

    def process_armature(self, obj, settings):
        """Process armature object for export"""
        logger.info(f"Processing armature object: {obj.name}")
        
        # Validate armature
        valid, msg = validate_armature(obj)
        if not valid:
            logger.error(f"Armature validation failed for {obj.name}: {msg}")
            return None
        
        armature_data = {
            'bones': [],
            'bone_count': 0,
            'root_bone': None
        }
        
        # Get armature data
        armature = obj.data
        
        # Process bones
        for bone in armature.data.bones:
            bone_data = {
                'name': bone.name,
                'parent': bone.parent.name if bone.parent else None,
                'head': list(bone.head_local),
                'tail': list(bone.tail_local),
                'matrix': [list(row) for row in bone.matrix_local],
                'length': bone.length
            }
            armature_data['bones'].append(bone_data)
        
        armature_data['bone_count'] = len(armature_data['bones'])
        
        # Find root bone
        for bone in armature_data['bones']:
            if bone['parent'] is None:
                armature_data['root_bone'] = bone['name']
                break
        
        logger.info(f"Processed {armature_data['bone_count']} bones for {obj.name}")
        return armature_data

    def _apply_modifiers(self, obj, mesh):
        """Apply modifiers to mesh"""
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        return obj_eval.data

    def _triangulate_mesh(self, mesh):
        """Triangulate mesh"""
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        return mesh

    def _collect_vertices(self, obj, mesh, settings):
        """Collect vertex data from mesh"""
        vertices = []
        # 获取所有UV层
        uv_layers = list(mesh.uv_layers) if mesh.uv_layers else []
        uv_layer_active = mesh.uv_layers.active if mesh.uv_layers else None
        # 获取顶点色
        vcol_layer = mesh.vertex_colors.active if mesh.vertex_colors else None
        # 骨骼
        armature = obj.find_armature()
        vertex_groups = obj.vertex_groups

        for loop_tri in mesh.loop_triangles:
            for loop_index in loop_tri.loops:
                loop = mesh.loops[loop_index]
                vertex = mesh.vertices[loop.vertex_index]
                # 位置
                position = list(vertex.co)
                # 法线
                normal = list(vertex.normal)
                # 多UV层
                uvs = []
                for uv_layer in uv_layers:
                    uv_data = uv_layer.data[loop_index]
                    uvs.append([uv_data.uv[0], uv_data.uv[1]])
                # 兼容原有格式，uv字段为活动层
                uv = [0.0, 0.0]
                if uv_layer_active:
                    uv_data = uv_layer_active.data[loop_index]
                    uv = [uv_data.uv[0], uv_data.uv[1]]
                # 顶点色
                vertex_color = [1.0, 1.0, 1.0, 1.0]
                if vcol_layer and settings.export_vertex_colors:
                    vcol_data = vcol_layer.data[loop_index]
                    vertex_color = [vcol_data.color[0], vcol_data.color[1], vcol_data.color[2], vcol_data.color[3]]
                # 骨骼权重
                bone_indices = [0, 0, 0]
                bone_weights = [0.0, 0.0, 0.0]
                if armature and vertex_groups:
                    bone_data = self._get_vertex_bone_weights(vertex, vertex_groups, armature)
                    bone_indices = bone_data['indices']
                    bone_weights = bone_data['weights']
                # 切线、副法线
                tangent = [0.0, 0.0, 0.0]
                binormal = [0.0, 0.0, 0.0]
                if settings.export_tangents:
                    tangent, binormal = self._calculate_tangent_binormal(loop, mesh)
                # 构建顶点数据
                vertex_data = {
                    'position': position,
                    'normal': normal,
                    'uv': uv,
                    'uvs': uvs,
                    'vertex_color': vertex_color,
                    'bone_indices': bone_indices,
                    'bone_weights': bone_weights,
                    'tangent': tangent,
                    'binormal': binormal
                }
                vertices.append(vertex_data)
        
        return vertices

    def _collect_indices(self, mesh):
        """Deprecated: indices are generated sequentially to match collected vertices."""
        return []

    def _get_vertex_bone_weights(self, vertex, vertex_groups, armature):
        """Get bone weights for vertex"""
        bone_indices = [0, 0, 0]
        bone_weights = [0.0, 0.0, 0.0]
        
        # Get vertex group influences
        influences = []
        for group in vertex.groups:
            if group.weight > 0:
                group_name = vertex_groups[group.group].name
                # Find bone index in armature
                bone_index = self._find_bone_index(armature, group_name)
                if bone_index >= 0:
                    influences.append((bone_index, group.weight))
        
        # Sort by weight and take top 3
        influences.sort(key=lambda x: x[1], reverse=True)
        influences = influences[:3]
        
        # Normalize weights
        total_weight = sum(w for _, w in influences)
        if total_weight > 0:
            influences = [(i, w/total_weight) for i, w in influences]
        
        # Fill bone data
        for i, (bone_index, weight) in enumerate(influences):
            bone_indices[i] = bone_index
            bone_weights[i] = weight
        
        return {
            'indices': bone_indices,
            'weights': bone_weights
        }

    def _find_bone_index(self, armature, bone_name):
        """Find bone index in armature"""
        for i, bone in enumerate(armature.data.bones):
            if bone.name == bone_name:
                return i
        return -1

    def _calculate_tangent_binormal(self, loop, mesh):
        """Calculate tangent and binormal for vertex"""
        # This is a simplified calculation
        # In practice, you'd need proper tangent space calculation
        normal = Vector(loop.normal)
        
        # Create arbitrary tangent perpendicular to normal
        if abs(normal.z) < 0.9:
            tangent = Vector((1, 0, 0))
        else:
            tangent = Vector((0, 1, 0))
        
        tangent = tangent - tangent.dot(normal) * normal
        tangent.normalize()
        
        binormal = normal.cross(tangent)
        binormal.normalize()
        
        return list(tangent), list(binormal)

    def _collect_materials(self, obj):
        """Collect material information"""
        materials = []
        
        for i, mat_slot in enumerate(obj.material_slots):
            if mat_slot.material:
                mat = mat_slot.material
                material_info = {
                    'name': mat.name,
                    'index': i,
                    'use_nodes': mat.use_nodes,
                    'diffuse_color': list(mat.diffuse_color),
                    'specular_color': list(mat.specular_color),
                    'roughness': mat.roughness,
                    'metallic': mat.metallic
                }
                materials.append(material_info)
        
        return materials

def register():
    pass

def unregister():
    pass
