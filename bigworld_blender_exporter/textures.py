import os
import shutil
import subprocess
import bpy
from .path_utils import normalize_path, ensure_dir
from .logger import setup_logger

LOG = setup_logger()

def _try_texconv(png_path: str, out_dir: str, dds_format="DXT5") -> str:
    """
    使用 texconv 将 png/jpg 转为 dds，返回 dds 路径；失败返回空串。
    需要系统安装 texconv (Windows) 或 nvtt (跨平台)。
    """
    dds_path = os.path.splitext(png_path)[0] + ".dds"
    cmd = ["texconv", "-f", dds_format, "-o", out_dir, png_path]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0 and os.path.exists(dds_path):
            LOG.info(f"[texture] DDS converted: {dds_path}")
            return dds_path
        else:
            LOG.warning(f"[texture] texconv failed ({proc.returncode}): {proc.stderr.strip()}")
    except Exception as e:
        LOG.warning(f"[texture] texconv not available: {e}")
    return ""

def export_image(image: bpy.types.Image, tmp_res_root: str, res_root: str, prefer_dds=False, color_space="srgb"):
    """
    导出 Blender Image 到 tmp_res_root/textures，下返回相对res的路径。
    color_space: "srgb" 或 "linear"（法线贴图推荐linear）
    prefer_dds: True 时尝试调用 texconv 转 DDS
    """
    if not image:
        return ""
    target_dir = os.path.join(tmp_res_root, "textures")
    ensure_dir(target_dir)

    src_path = bpy.path.abspath(image.filepath_raw) if image.filepath_raw else ""
    basename = os.path.basename(src_path) if src_path else (image.name + ".png")
    out_path = os.path.join(target_dir, basename)

    try:
        if src_path and os.path.exists(src_path):
            shutil.copy2(src_path, out_path)
            LOG.info(f"[texture] copy {src_path} -> {out_path} ({color_space})")
        else:
            image.filepath_raw = out_path
            image.save_render(out_path)
            LOG.info(f"[texture] save_render {image.name} -> {out_path} ({color_space})")
    except Exception as e:
        LOG.error(f"[texture] fail {image.name}: {e}")
        return ""

    if prefer_dds:
        dds_path = _try_texconv(out_path, os.path.dirname(out_path), dds_format="DXT5")
        if dds_path and os.path.exists(dds_path):
            rel = normalize_path(os.path.relpath(dds_path, tmp_res_root))
            return rel

    rel = normalize_path(os.path.relpath(out_path, tmp_res_root))
    return rel
