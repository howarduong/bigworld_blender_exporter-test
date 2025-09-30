# bigworld_blender_exporter/core/export_engine.py

import bpy
import os
import threading
from ..export.model_exporter import ModelExporter
from ..utils.logger import logger

def export_project(res_root, target_dir):
    """
    主入口统一调度并发模型、动画、材质批量导出，提升性能，防止GUI阻塞。
    """
    logger.info(f"开始导出到: {target_dir} (res根目录: {res_root})")
    os.makedirs(target_dir, exist_ok=True)
    jobs = []
    mesh_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if not mesh_objs:
        mesh_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    def export_one(obj):
        try:
            me = ModelExporter(obj, res_root, target_dir)
            me.export()
        except Exception as ex:
            logger.error(f"对象[{obj.name}]导出失败: {ex}")

    threads = []
    for obj in mesh_objs:
        t = threading.Thread(target=export_one, args=(obj,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    logger.info(f"全部模型导出完成（共{len(mesh_objs)}个对象）")
