# 文件位置: bigworld_blender_exporter/formats/bsp_format.py
# -*- coding: utf-8 -*-
"""
Write BSP data section for BigWorld .primitives files.

Section layout (appended after index section data):
- 64 bytes: "bsp" ASCII identifier (zero padded)
- u32: nodeCount
- u32: triangleCount
- nodes: array of nodes (each node: plane [f32*4], childA i32, childB i32, triStart u32, triCount u32)
- triangles: array of triangles (each: 3 * u32 vertex indices)

Notes:
- Internal nodes should set triCount = 0 and triStart = 0 (or undefined) and point to valid child indices.
- Leaf nodes must set triStart/triCount to a valid contiguous range inside the triangle array and childA/childB = -1.
"""

import struct
from typing import Dict, Tuple, List
from ..utils.binary_writer import write_bytes, write_u32, write_f32
from ..utils.validation import ValidationError

BSP_IDENTIFIER = "bsp"


def _pad_64bytes_ascii(name: str) -> bytes:
    b = name.encode("ascii", errors="strict")
    if len(b) > 64:
        raise ValidationError(f"BSP identifier exceeds 64 bytes: {name}")
    return b.ljust(64, b"\x00")


def _validate_bsp_payload(bsp_data: Dict) -> Tuple[List[Dict], List[Tuple[int, int, int]]]:
    if bsp_data is None:
        return [], []
    nodes = bsp_data.get("nodes", [])
    triangles = bsp_data.get("triangles", [])

    # Basic type checks
    if not isinstance(nodes, list) or not isinstance(triangles, list):
        raise ValidationError("BSP data must contain 'nodes' (list) and 'triangles' (list)")

    # Nodes validate
    for i, n in enumerate(nodes):
        if "plane" not in n or len(n["plane"]) != 4:
            raise ValidationError(f"BSP node {i} missing plane (nx,ny,nz,d)")
        for k in ("childA", "childB", "triStart", "triCount"):
            if k not in n:
                raise ValidationError(f"BSP node {i} missing key '{k}'")

        ca, cb = int(n["childA"]), int(n["childB"])
        ts, tc = int(n["triStart"]), int(n["triCount"])
        if (ca == -1 and cb == -1):
            # leaf: must have a valid range
            if tc < 0:
                raise ValidationError(f"BSP leaf node {i} has negative triCount")
        else:
            # internal: children must be valid indices
            if not (0 <= ca < len(nodes) and 0 <= cb < len(nodes)):
                raise ValidationError(f"BSP internal node {i} children out of range: {ca}, {cb}")

    # Triangle validate
    for t in triangles:
        if not (isinstance(t, (list, tuple)) and len(t) == 3):
            raise ValidationError(f"BSP triangle must be 3 indices, got: {t}")
        if t[0] < 0 or t[1] < 0 or t[2] < 0:
            raise ValidationError(f"BSP triangle indices must be non-negative, got: {t}")

    return nodes, triangles


def write_bsp_section(f, bsp_data: Dict) -> None:
    """
    Append BSP section to .primitives file.

    bsp_data expected:
      - nodes: List[Dict] with keys:
          plane: (nx, ny, nz, d) as floats
          childA: int (left child index or -1)
          childB: int (right child index or -1)
          triStart: int (start triangle index)
          triCount: int (triangle count)
      - triangles: List[Tuple[int, int, int]] (vertex indices)

    Writes an empty section (0 nodes, 0 triangles) if bsp_data is None or empty.
    """
    nodes, triangles = _validate_bsp_payload(bsp_data)

    # Identifier
    write_bytes(f, _pad_64bytes_ascii(BSP_IDENTIFIER))

    # Counts
    write_u32(f, len(nodes))
    write_u32(f, len(triangles))

    # Nodes
    for n in nodes:
        nx, ny, nz, d = map(float, n["plane"])
        write_f32(f, nx); write_f32(f, ny); write_f32(f, nz); write_f32(f, d)
        f.write(struct.pack("<i", int(n["childA"])))
        f.write(struct.pack("<i", int(n["childB"])))
        write_u32(f, int(n["triStart"]))
        write_u32(f, int(n["triCount"]))

    # Triangles
    for t in triangles:
        write_u32(f, int(t[0])); write_u32(f, int(t[1])); write_u32(f, int(t[2]))
