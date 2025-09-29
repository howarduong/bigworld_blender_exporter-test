# -*- coding: utf-8 -*-
"""
path_utils.py
路径处理工具函数，用于 BigWorld Blender Exporter
"""

import os


def normalize_path(path: str) -> str:
    """
    将路径统一为正斜杠分隔符
    """
    if not path:
        return ""
    return path.replace("\\", "/")


def to_res_relative(path: str, res_root: str) -> str:
    """
    将绝对路径转换为相对 res/ 的路径，并统一为正斜杠
    - path: 绝对路径
    - res_root: res 根目录的绝对路径
    """
    if not path or not res_root:
        return normalize_path(path)

    rel = os.path.relpath(path, res_root)
    return normalize_path(rel)


def ensure_subdir(res_root: str, subdir: str) -> str:
    """
    确保 res/ 下的子目录存在，如果不存在则创建
    返回该子目录的绝对路径
    """
    abs_path = os.path.join(res_root, subdir)
    os.makedirs(abs_path, exist_ok=True)
    return normalize_path(abs_path)


def get_model_dir(res_root: str) -> str:
    """返回 models/ 目录绝对路径"""
    return ensure_subdir(res_root, "models")


def get_material_dir(res_root: str) -> str:
    """返回 materials/ 目录绝对路径"""
    return ensure_subdir(res_root, "materials")


def get_map_dir(res_root: str) -> str:
    """返回 maps/ 目录绝对路径"""
    return ensure_subdir(res_root, "maps")


def get_animation_dir(res_root: str) -> str:
    """返回 animations/ 目录绝对路径"""
    return ensure_subdir(res_root, "animations")
