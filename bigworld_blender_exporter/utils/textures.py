# 文件位置: bigworld_blender_exporter/utils/textures.py
# 贴图导出与格式处理工具，支持packed、相对路径、可选格式转换

import bpy
import os
from ..utils.logger import get_logger

logger = get_logger("textures")

def export_texture(image, export_dir, options=None):
    """
    导出Blender贴图到指定目录，支持packed、相对路径、格式转换
    :param image: bpy.types.Image
    :param export_dir: 导出目录
    :param options: dict，可选项：format、force_unpack、relative_path
    :return: 导出后相对路径
    """
    if not image:
        logger.warning("无效贴图对象")
        return None
    options = options or {}
    # 1. 处理packed贴图
    if image.packed_file and options.get('force_unpack', True):
        image.unpack(method='USE_ORIGINAL')
    # 2. 目标文件名与格式
    ext = options.get('format', image.file_format.lower() if hasattr(image, 'file_format') else 'png')
    name = os.path.splitext(os.path.basename(image.filepath))[0] + '.' + ext
    export_path = os.path.join(export_dir, name)
    # 3. 导出贴图
    try:
        image.save_render(export_path)
        logger.info(f"导出贴图: {export_path}")
    except Exception as e:
        logger.error(f"贴图导出失败: {e}")
        return None
    # 4. 返回相对路径
    if options.get('relative_path', True):
        rel_path = os.path.relpath(export_path, export_dir)
        return rel_path
    return export_path

def convert_texture_format(image_path, target_format):
    """
    将贴图文件转换为目标格式（如jpg、png、dds等）
    :param image_path: 源文件路径
    :param target_format: 目标格式
    :return: 新文件路径
    """
    from PIL import Image as PILImage
    try:
        img = PILImage.open(image_path)
        new_path = os.path.splitext(image_path)[0] + '.' + target_format
        img.save(new_path)
        logger.info(f"贴图格式转换: {image_path} -> {new_path}")
        return new_path
    except Exception as e:
        logger.error(f"贴图格式转换失败: {e}")
        return None
