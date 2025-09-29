import os
import shutil
import bpy
from .path_utils import normalize_path, ensure_dir
from .logger import setup_logger

LOG = setup_logger()

def export_image(image: bpy.types.Image, tmp_res_root: str, res_root: str, prefer_dds=False):
    """
    Export a Blender image to tmp_res_root preserving a relative path layout similar to res_root.
    Returns the res-root-relative path (using forward slashes).
    tmp_res_root: full path to temporary export's res root (e.g. /.../tmp_export/20230901/res)
    res_root: configured project res root name (e.g. 'res') used to compute relative paths
    """
    if image is None:
        return ""
    # Determine source path
    # If image is packed or has no filepath, write it out to tmp in images/
    src_path = bpy.path.abspath(image.filepath_raw) if image.filepath_raw else ""
    # Create target dir under tmp_res_root textures/
    target_subdir = os.path.join(tmp_res_root, "textures")
    ensure_dir(target_subdir)
    if src_path and os.path.exists(src_path):
        basename = os.path.basename(src_path)
        out_path = os.path.join(target_subdir, basename)
        try:
            shutil.copy2(src_path, out_path)
            LOG.info(f"Copied image {src_path} -> {out_path}")
        except Exception:
            # fallback: save image data
            try:
                image.save_render(out_path)
                LOG.info(f"Saved image by image.save_render to {out_path}")
            except Exception as e:
                LOG.error(f"Failed to write image {image.name}: {e}")
                return ""
    else:
        # packed or untitled: write to target_subdir with image.name
        ext = ".png"
        basename = f"{image.name}{ext}"
        out_path = os.path.join(target_subdir, basename)
        try:
            image.filepath_raw = out_path
            image.save_render(out_path)
            LOG.info(f"Exported packed/unsaved image {image.name} -> {out_path}")
        except Exception as e:
            LOG.error(f"Failed to export image {image.name}: {e}")
            return ""
    # Optional: convert to DDS using external tool if prefer_dds True (not implemented)
    # e.g., call texconv or nvtt here. Keep original for now.
    rel = os.path.relpath(out_path, tmp_res_root)
    rel = normalize_path(rel)
    # The engine expects paths relative to res root; we return rel prefixed by nothing (caller will join)
    return rel
