# bigworld_blender_exporter/export/model_exporter.py

import bpy
import struct
import os

from ..utils.path import abs2res_relpath, norm_path, get_res_root
from ..utils.logger import logger
from ..utils.binary_writer import BinaryWriter
from ..export.material_exporter import export_materials
from ..export.animation_exporter import export_animations

class ModelExporter:
    """
    BigWorld .model 文件导出器，实现官方模型格式，包括Mesh、材质、绑定骨骼与动画索引等。
    """

    def __init__(self, obj, res_root, target_dir):
        self.obj = obj
        self.res_root = res_root
        self.target_dir = target_dir
        self.errors = []

    def export(self, filename=None):
        """
        导出当前模型对象为符合BigWorld标准的.model文件与相关资源。
        """
        try:
            if filename is None:
                filename = f"{self.obj.name}.model"
            model_path = os.path.join(self.target_dir, filename)
            mesh = self._get_mesh_data()
            bones = self._get_armature_data()
            mats = export_materials(self.obj, self.res_root, self.target_dir)
            anims = export_animations(self.obj, self.res_root, self.target_dir)

            self._write_model_file(model_path, mesh, bones, mats, anims)
            logger.info(f".model导出成功: {model_path}")
            return model_path
        except Exception as ex:
            self.errors.append(str(ex))
            logger.error(f".model导出失败: {ex}")
            raise

    def _get_mesh_data(self):
        """提取当前对象的Mesh顶点、索引、UV等。"""
        obj = self.obj
        if obj.type != 'MESH':
            raise ValueError(f"仅支持Mesh对象导出，当前类型为: {obj.type}")
        mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
        mesh.calc_loop_triangles()
        pos = []
        normals = []
        uvs = []
        indices = []
        uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        for v in mesh.vertices:
            pos.append(v.co[:])
            normals.append(v.normal[:])
        for tri in mesh.loop_triangles:
            indices.extend(tri.vertices)
            if uv_layer:
                uvs.append([uv_layer[i].uv[:] for i in tri.loops])
            else:
                uvs.append([(0,0)]*3)
        # 可扩展导出骨骼权重等
        bpy.data.meshes.remove(mesh)
        return {
            "positions": pos,
            "normals": normals,
            "uvs": uvs,
            "indices": indices
        }

    def _get_armature_data(self):
        """获得骨骼父子关系，用于软绑定动画。"""
        if not self.obj.parent or self.obj.parent.type != 'ARMATURE':
            return None
        arm_obj = self.obj.parent
        bones = []
        for b in arm_obj.data.bones:
            bones.append({
                "name": b.name,
                "parent": b.parent.name if b.parent else None,
                "matrix_local": [list(r) for r in b.matrix_local]
            })
        return bones

    def _write_model_file(self, path, mesh, bones, mats, anims):
        """写BigWorld官方二进制.model结构，参考官方格式文档，以属性块布局"""
        with BinaryWriter(path) as writer:
            # Header
            writer.write_magic(b'BWMD')
            writer.write_uint32(1)  # version
            # Mesh Block
            writer.write_block('mesh', lambda w: self._write_mesh_block(w, mesh))
            # Bones
            if bones:
                writer.write_block('bones', lambda w: self._write_bone_block(w, bones))
            # Materials
            writer.write_block('materials', lambda w: self._write_materials_block(w, mats))
            # Animations (短索引)
            if anims:
                writer.write_block('animations', lambda w: self._write_anims_block(w, anims))
            writer.finalize()

    def _write_mesh_block(self, w, mesh):
        # 顶点数
        w.write_uint32(len(mesh['positions']))
        for v in mesh['positions']:
            w.write_vec3(v)
        # 法线
        w.write_uint32(len(mesh['normals']))
        for n in mesh['normals']:
            w.write_vec3(n)
        # UV
        w.write_uint32(len(mesh['uvs']))
        for uvs in mesh['uvs']:
            for uv in uvs:
                w.write_vec2(uv)
        # 索引
        w.write_uint32(len(mesh['indices']))
        for idx in mesh['indices']:
            w.write_uint32(idx)

    def _write_bone_block(self, w, bones):
        w.write_uint32(len(bones))
        for bone in bones:
            w.write_str(bone["name"])
            w.write_str(bone["parent"] or "")
            for row in bone["matrix_local"]:
                w.write_vec4(row)

    def _write_materials_block(self, w, mats):
        w.write_uint32(len(mats))
        for m in mats:
            # 路径全部转换为res相对
            rel_path = abs2res_relpath(m['file'], self.res_root)
            w.write_str(rel_path)
    
    def _write_anims_block(self, w, anims):
        w.write_uint32(len(anims))
        for a in anims:
            rel_path = abs2res_relpath(a['file'], self.res_root)
            w.write_str(a["name"])
            w.write_str(rel_path)
