# utils/vertex_compression.py
# -*- coding: utf-8 -*-

import math
from typing import List, Tuple

U16_MAX = 65535
U8_MAX = 255

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def normalize3(x: float, y: float, z: float) -> Tuple[float, float, float]:
    n = math.sqrt(x*x + y*y + z*z)
    if n <= 1e-20:
        return 0.0, 0.0, 1.0
    return x/n, y/n, z/n

# Spherical mapping based 2D encoding of unit normal/tangent/binormal to u16x2.
# This uses azimuth/elevation packing for stable quantization and simple decode.
def compress_dir_to_u16x2(nx: float, ny: float, nz: float) -> Tuple[int, int]:
    nx, ny, nz = normalize3(nx, ny, nz)
    # azimuth phi in [-pi, pi], elevation theta in [-pi/2, pi/2]
    phi = math.atan2(ny, nx)           # [-pi, pi]
    theta = math.asin(clamp(nz, -1.0, 1.0))  # [-pi/2, pi/2]

    # map to [0,1]
    phi01 = (phi + math.pi) / (2.0 * math.pi)
    theta01 = (theta + math.pi/2.0) / math.pi

    u = int(clamp(round(phi01 * U16_MAX), 0, U16_MAX))
    v = int(clamp(round(theta01 * U16_MAX), 0, U16_MAX))
    return u, v

def decompress_u16x2_to_dir(u: int, v: int) -> Tuple[float, float, float]:
    phi01 = clamp(u / U16_MAX, 0.0, 1.0)
    theta01 = clamp(v / U16_MAX, 0.0, 1.0)

    phi = phi01 * (2.0 * math.pi) - math.pi
    theta = theta01 * math.pi - math.pi/2.0

    # reconstruct unit vector
    x = math.cos(theta) * math.cos(phi)
    y = math.cos(theta) * math.sin(phi)
    z = math.sin(theta)
    return normalize3(x, y, z)

def quantize_weights_3(weights: List[float]) -> Tuple[int, int, int]:
    """
    Quantize up to 3 weights to u8 (0..255).
    Store only w0, w1 in the vertex; w2 is derived as 255 - w0 - w1.
    Returns tuple (w0, w1, w2) in bytes for convenience.
    """
    # pad/cut to 3, normalize
    w = sorted(weights, reverse=True)[:3]
    if len(w) < 3:
        w += [0.0] * (3 - len(w))
    s = sum(w)
    if s <= 1e-20:
        w = [1.0, 0.0, 0.0]
    else:
        w = [clamp(x / s, 0.0, 1.0) for x in w]

    # initial quantization
    q0 = int(round(w[0] * U8_MAX))
    q1 = int(round(w[1] * U8_MAX))
    # derive q2 to preserve sum = 255
    q2 = U8_MAX - q0 - q1
    # clamp after derivation
    q0 = max(0, min(U8_MAX, q0))
    q1 = max(0, min(U8_MAX, q1))
    q2 = max(0, min(U8_MAX, q2))
    return q0, q1, q2

def quantize_indices_3(indices: List[int]) -> Tuple[int, int, int]:
    """
    Quantize up to 3 bone indices to u8 (0..255).
    Missing indices are filled with 0.
    """
    idx = indices[:3]
    if len(idx) < 3:
        idx += [0] * (3 - len(idx))
    return (idx[0] & 0xFF), (idx[1] & 0xFF), (idx[2] & 0xFF)

def pack_uv(u: float, v: float) -> Tuple[float, float]:
    """
    UV pass-through with optional clamping or wrap normalization if desired.
    Keep as 32-bit float pair for formats using f32x2.
    """
    return float(u), float(v)

def blender_to_bigworld_matrix(m: List[List[float]]) -> List[List[float]]:
    """
    Convert Blender Z-up to BigWorld Y-up using a fixed axis mapping.
    Apply R_yup = R_zup * M, where M maps axes:
      X' = X
      Y' = Z
      Z' = -Y
    Represented by:
      [[1,0,0,0],
       [0,0,1,0],
       [0,-1,0,0],
       [0,0,0,1]]
    Multiplying m (4x4) by this matrix on the right.
    """
    M = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0,-1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    # matrix multiply: result = m * M
    res = [[0.0]*4 for _ in range(4)]
    for r in range(4):
        for c in range(4):
            res[r][c] = sum(m[r][k] * M[k][c] for k in range(4))
    return res
