# bigworld_blender_exporter/utils/path.py

import os
import bpy
from bpy.path import abspath, relpath, native_pathsep

def norm_path(path):
    "统一斜杠，兼容跨平台"
    if not path:
        return ""
    return os.path.normpath(path).replace('\\', '/')

def get_res_root(scene=None):
    """自动获取res主目录（可拓展从项目设置/首选项获取），支持UI配置"""
    # 这里以UI面板配置为主，可替换为os.path
    sc = bpy.context.scene if scene is None else scene
    return norm_path(getattr(getattr(sc, "bigworld_exporter_settings", None), "res_root", ""))

def abs2res_relpath(abs_path, res_root):
    """将绝对路径转res目录下相对路径，BigWorld专用"""
    abs_path = norm_path(abs_path)
    res_root = norm_path(res_root)
    if not abs_path or not res_root:
        return abs_path
    if not abs_path.startswith(res_root):
        # 允许用户自定义，但记录警告
        from .logger import logger
        logger.warn(f"路径[{abs_path}]不在res目录[{res_root}]内！")
        return abs_path
    rel = os.path.relpath(abs_path, res_root)
    return rel.replace('\\','/')

def ensure_res_path(file_path, res_root):
    """确保路径已转为res相对，供.mfm/.model引用"""
    path = norm_path(file_path)
    if path.startswith(res_root):
        return abs2res_relpath(file_path, res_root)
    return file_path
