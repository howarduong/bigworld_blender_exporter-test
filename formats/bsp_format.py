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
"""

import struct
from typing import List, Dict, Tuple
from ..utils.binary_writer import write_bytes, write_u32, write_f32
from ..utils.validation import ValidationError

BSP_IDENTIFIER = "bsp"

def _pad_64bytes_ascii(name: str) -> bytes:
    b = name.encode("ascii", errors="strict")
    if len(b) > 64:
        raise ValidationError(f"BSP identifier exceeds 64 bytes: {name}")
    return b.ljust(64, b"\x00")


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

    If bsp_data is empty or missing keys, this function writes an empty section header with zero counts.
    """
    nodes = bsp_data.get("nodes", [])
    triangles = bsp_data.get("triangles", [])

    # Identifier
    write_bytes(f, _pad_64bytes_ascii(BSP_IDENTIFIER))

    # Counts
    write_u32(f, len(nodes))
    write_u32(f, len(triangles))

    # Nodes
    for n in nodes:
        plane = n.get("plane", (0.0, 0.0, 1.0, 0.0))
        childA = int(n.get("childA", -1))
        childB = int(n.get("childB", -1))
        triStart = int(n.get("triStart", 0))
        triCount = int(n.get("triCount", 0))

        write_f32(f, float(plane[0]))
        write_f32(f, float(plane[1]))
        write_f32(f, float(plane[2]))
        write_f32(f, float(plane[3]))

        f.write(struct.pack("<i", childA))
        f.write(struct.pack("<i", childB))
        write_u32(f, triStart)
        write_u32(f, triCount)

    # Triangles
    for t in triangles:
        if len(t) != 3:
            raise ValidationError(f"BSP triangle must have 3 indices, got: {t}")
        write_u32(f, int(t[0]))
        write_u32(f, int(t[1]))
        write_u32(f, int(t[2]))
