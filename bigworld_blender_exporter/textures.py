import os
import shutil
import bpy
from .path_utils import normalize_path, ensure_dir
from .logger import setup_logger

LOG = setup_logger()

def export_image(image: bpy.types.Image, tmp_res_root: str, res_root: str, prefer_dds=False, color_space="srgb"):
    """
    导出 Blender Image 到 tmp_res_root/textures 下，返回相对res的路径。
    color_space: "srgb" 或 "linear"（法线贴图推荐linear）
    """
    if not image:
        return ""
    target_dir = os.path.join(tmp_res_root, "textures")
    ensure_dir(target_dir)
    # 原路径
    src_path = bpy.path.abspath(image.filepath_raw) if image.filepath_raw else ""
    # 目标文件名
    basename = os.path.basename(src_path) if src_path else (image.name + ".png")
    out_path = os.path.join(target_dir, basename)
    try:
        if src_path and os.path.exists(src_path):
            shutil.copy2(src_path, out_path)
            LOG.info(f"[texture] copy {src_path} -> {out_path} ({color_space})")
        else:
            # packed或未保存
            image.filepath_raw = out_path
            image.save_render(out_path)
            LOG.info(f"[texture] save_render {image.name} -> {out_path} ({color_space})")
    except Exception as e:
        LOG.error(f"[texture] fail {image.name}: {e}")
        return ""
    # 可选：DDS转换（保留hook）
    # if prefer_dds:
    #     try:
    #         # 调用外部工具texconv/nvtt进行转换
    #         pass
    #     except Exception as e:
    #         LOG.warning(f"[texture] dds convert failed: {e}")
    rel = normalize_path(os.path.relpath(out_path, tmp_res_root))
    return rel
