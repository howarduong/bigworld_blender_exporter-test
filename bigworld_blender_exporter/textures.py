import os
import shutil
import subprocess
import bpy
from .path_utils import normalize_path, ensure_dir
from .logger import setup_logger

LOG = setup_logger()

def _run_texconv(src_path: str, out_dir: str, dds_format: str, srgb: bool) -> str:
    """
    调用 texconv 转换为 dds，生成 mipmap。
    dds_format 示例：DXT5（漫反射），BC5（法线）。
    srgb: True 为 sRGB（DXT5），False 为 Linear（BC5）。
    """
    try:
        args = ["texconv", "-f", dds_format, "-o", out_dir, "-m", "0", src_path]
        if srgb:
            args += ["-srgb"]
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            LOG.warning(f"[texture] texconv failed: {proc.stderr.strip()}")
            return ""
        dds_path = os.path.splitext(src_path)[0] + ".dds"
        if os.path.exists(dds_path):
            LOG.info(f"[texture] DDS converted: {dds_path}")
            return dds_path
        # texconv有时输出到 out_dir，尝试定位
        dname = os.path.basename(src_path)
        dds_guess = os.path.join(out_dir, os.path.splitext(dname)[0] + ".dds")
        return dds_guess if os.path.exists(dds_guess) else ""
    except Exception as e:
        LOG.warning(f"[texture] texconv not available: {e}")
        return ""

def export_image(image: bpy.types.Image, tmp_res_root: str, res_root: str, prefer_dds=False, color_space="srgb"):
    """
    导出 Blender Image 到 tmp_res_root/textures 下，返回相对res的路径。
    color_space: "srgb"（漫反射）或 "linear"（法线）
    prefer_dds: True 时尝试转换为 DDS（DXT5/BC5），失败回退 PNG
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
        # sRGB: 漫反射 DXT5；Linear: 法线 BC5
        is_srgb = (color_space.lower() == "srgb")
        fmt = "DXT5" if is_srgb else "BC5"
        dds_path = _run_texconv(out_path, os.path.dirname(out_path), fmt, srgb=is_srgb)
        if dds_path and os.path.exists(dds_path):
            rel = normalize_path(os.path.relpath(dds_path, tmp_res_root))
            return rel

    rel = normalize_path(os.path.relpath(out_path, tmp_res_root))
    return rel
