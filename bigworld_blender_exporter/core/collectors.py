# 文件位置: bigworld_blender_exporter/core/collectors.py
# Data collectors for BigWorld Blender Exporter

import bpy
import bmesh
from mathutils import Matrix
from ..utils import logger


class MeshCollector:
    """收集网格数据：顶点、法线、UV、切线、权重"""

    def collect(self, obj, settings):
        if obj.type != 'MESH':
            return None

        mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
        bm = bmesh.new()
        bm.from_mesh(mesh)

        if settings.triangulate_mesh:
            bmesh.ops.triangulate(bm, faces=bm.faces)

        bm.to_mesh(mesh)
        bm.free()

        vertices = [v.co[:] for v in mesh.vertices]
        normals = [v.normal[:] for v in mesh.vertices]
        indices = [loop.vertex_index for poly in mesh.polygons for loop in poly.loop_indices]

        uvs = []
        if mesh.uv_layers.active:
            uv_layer = mesh.uv_layers.active.data
            uvs = [uv_layer[li].uv[:] for li in range(len(uv_layer))]

        colors = []
        if settings.export_vertex_colors and mesh.vertex_colors.active:
            color_layer = mesh.vertex_colors.active.data
            colors = [color_layer[li].color[:] for li in range(len(color_layer))]

        bbox_min = [min(v[i] for v in vertices) for i in range(3)]
        bbox_max = [max(v[i] for v in vertices) for i in range(3)]

        obj.to_mesh_clear()

        return {
            "vertices": vertices,
            "normals": normals,
            "indices": indices,
            "uvs": uvs,
            "colors": colors,
            "bbox_min": bbox_min,
            "bbox_max": bbox_max,
            "extent": max(bbox_max[i] - bbox_min[i] for i in range(3)),
        }


class SkeletonCollector:
    """收集骨架数据：骨骼层级、矩阵、权重绑定"""

    def collect(self, obj, settings):
        if obj.type != 'ARMATURE':
            return None

        armature = obj.data
        bones = []
        for bone in armature.bones:
            bones.append({
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else "",
                "head": bone.head_local[:],
                "tail": bone.tail_local[:],
                "matrix": bone.matrix_local[:],
            })
        return bones


class AnimationCollector:
    """收集动画数据：关键帧、采样率、压缩"""

    def collect(self, obj, action, settings):
        if not action:
            return None

        fps = settings.sample_rate or 30
        start = int(settings.start_frame)
        end = int(settings.end_frame)

        anim_data = {"name": action.name, "frames": []}
        for frame in range(start, end + 1, int(30 / fps)):
            bpy.context.scene.frame_set(frame)
            mat = obj.matrix_world.copy()
            anim_data["frames"].append({
                "frame": frame,
                "matrix": [list(row) for row in mat],
            })
        return anim_data


class MaterialCollector:
    """收集材质数据：Shader、贴图路径、参数"""

    def collect(self, obj, settings):
        mats = []
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
            mat_info = {
                "name": mat.name,
                "shader": "shaders/std_effects.fx",
                "textures": {},
                "parameters": {},
            }
            if mat.use_nodes and settings.bake_materials:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        mat_info["textures"][node.label or node.name] = bpy.path.abspath(node.image.filepath)
            mats.append(mat_info)
        return mats


# -------------------------
# 注册
# -------------------------
def register():
    pass


def unregister():
    pass
