# 文件位置: bigworld_blender_exporter/utils/math_utils.py
# Math utilities for BigWorld exporter

import math
from mathutils import Vector, Matrix


def blender_to_bigworld_matrix():
    """Z-up (Blender) → Y-up (BigWorld) 坐标系转换矩阵"""
    return Matrix([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, -1, 0, 0],
        [0, 0, 0, 1],
    ])


def bigworld_to_blender_matrix():
    """Y-up (BigWorld) → Z-up (Blender) 坐标系转换矩阵"""
    return Matrix([
        [1, 0, 0, 0],
        [0, 0, -1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ])


# ----------------------------
# 坐标系转换
# ----------------------------

def convert_position(pos):
    """Blender Z-up position → BigWorld Y-up"""
    x, y, z = pos
    return [x, z, -y]


def convert_direction(dir_vec):
    """Blender Z-up direction → BigWorld Y-up"""
    x, y, z = dir_vec
    return [x, z, -y]


# ----------------------------
# 向量压缩
# ----------------------------

def compress_dir_to_u16x2(vec3):
    """
    将单位向量压缩为 (u16, u16)，范围 [0,65535]。
    用球面坐标 (phi, theta) 映射。
    """
    v = Vector(vec3)
    if v.length_squared == 0:
        v = Vector((0.0, 0.0, 1.0))
    else:
        v.normalize()

    phi = math.atan2(v.y, v.x)  # [-pi, pi]
    theta = math.asin(max(-1.0, min(1.0, v.z)))  # [-pi/2, pi/2]

    phi01 = (phi + math.pi) / (2.0 * math.pi)
    theta01 = (theta + math.pi/2.0) / math.pi

    u = int(round(phi01 * 65535))
    w = int(round(theta01 * 65535))
    return u, w


def compress_normal(normal):
    return compress_dir_to_u16x2(normal)


def compress_tangent(tangent):
    return compress_dir_to_u16x2(tangent)


def compress_binormal(binormal):
    return compress_dir_to_u16x2(binormal)


# ----------------------------
# 包围盒与 extent
# ----------------------------

def calculate_bounding_box(vertices):
    """根据顶点列表计算 AABB。顶点为包含 'position' 的字典。"""
    if not vertices:
        return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]

    min_coords = [float("inf")] * 3
    max_coords = [float("-inf")] * 3

    for v in vertices:
        p = v.get("position", (0.0, 0.0, 0.0))
        for i in range(3):
            if p[i] < min_coords[i]:
                min_coords[i] = p[i]
            if p[i] > max_coords[i]:
                max_coords[i] = p[i]

    return min_coords, max_coords


def calculate_extent(bmin, bmax):
    """
    返回 extent = 包围球半径 = AABB 对角线长度的一半
    """
    dx = bmax[0] - bmin[0]
    dy = bmax[1] - bmin[1]
    dz = bmax[2] - bmin[2]
    diag = math.sqrt(dx*dx + dy*dy + dz*dz)
    return diag / 2.0
