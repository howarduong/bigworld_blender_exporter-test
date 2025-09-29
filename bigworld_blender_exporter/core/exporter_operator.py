# 文件位置: bigworld_blender_exporter/core/exporter_operator.py
# Blender导出操作符，集成原子写入、自检、可选部署、回滚、manifest生成

import bpy
from .exporter import BigWorldExporter
from ..utils.logger import get_logger

logger = get_logger("exporter_operator")

class EXPORT_OT_bigworld(bpy.types.Operator):
    bl_idname = "export_scene.bigworld"
    bl_label = "Export BigWorld Model"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            # 1. 原子写入到临时目录
            import tempfile, shutil, os
            temp_dir = tempfile.mkdtemp(prefix="bw_export_")
            logger.info(f"临时导出目录: {temp_dir}")
            settings = context.scene.bigworld_export_settings
            settings.export_path = temp_dir
            exporter = BigWorldExporter(context, settings)
            exporter.export()
            # 2. 自检（可扩展Level1-3）
            # TODO: 调用自检脚本
            # 3. 可选部署到目标目录
            final_dir = settings.final_output_path or settings.export_path
            for fname in os.listdir(temp_dir):
                shutil.move(os.path.join(temp_dir, fname), os.path.join(final_dir, fname))
            # 4. manifest生成
            manifest_path = os.path.join(final_dir, "export_manifest.txt")
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write("BigWorld导出清单\n")
                for fname in os.listdir(final_dir):
                    f.write(fname + "\n")
            logger.info(f"导出完成，清单: {manifest_path}")
            return {'FINISHED'}
        except Exception as e:
            logger.error(f"导出失败: {e}")
            # 5. 回滚
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(EXPORT_OT_bigworld)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_bigworld)
