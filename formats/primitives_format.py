# 文件位置: bigworld_blender_exporter/formats/primitives_format.py
# -*- coding: utf-8 -*-
"""
BigWorld .primitives writer aligned to official section layout.

Sections (in order):
1) Vertex Data Section:
   - 64 bytes: vertex format identifier ASCII, zero padded
   - u32: number_of_vertices
   - raw_vertex_data: serialized per-vertex bytes (layout depends on format)

2) Index Data Section:
   - 64 bytes: index format identifier ASCII ("list" for 16-bit, "list32" for 32-bit), zero padded
   - u32: number_of_indices
   - u32: number_of_primitive_groups
   - raw_index_data: serialized indices (LE, 16-bit or 32-bit)
   - raw_primitive_data: for each group, four u32 in order: startIdx, numPrims, startVtx, numVtx

3) BSP Data Section (optional):
   - 64 bytes: "bsp" identifier ASCII, zero padded
   - u32: nodeCount
   - u32: triangleCount
   - nodes + triangles payload
"""

from typing import List, Dict, Tuple
from .vertex_formats import get_vertex_format, VertexFormat
from ..utils.vertex_compression import (
    compress_dir_to_u16x2,
    quantize_weights_3,
    quantize_indices_3,
    pack_uv,
)
from ..utils.binary_writer import (
    write_bytes, write_u8, write_u16, write_u32, write_f32, create_directory
)
from ..utils.logger import get_logger
from ..utils.validation import ValidationError
from .bsp_format import write_bsp_section

logger = get_logger("primitives_format")


def export_primitives_file(
    filepath: str,
    vertices: List[Dict],
    indices: List[int],
    primitive_groups: List[Tuple[int, int, int, int]],
    vertex_format_name: str = "xyznuvtb",
    use_32bit_index: bool = False,
    bsp_data: Dict = None,
) -> None:
    """
    Write a .primitives file with vertex, index, and optional BSP sections.

    Parameters:
      - filepath: output path (will create parent directories)
      - vertices: list of per-vertex dictionaries, must contain required attributes for the chosen format
      - indices: list of triangle indices (flattened), contiguous per group
      - primitive_groups: list of tuples (startIdx, numPrims, startVtx, numVtx)
      - vertex_format_name: identifier registered in formats/vertex_formats.py
      - use_32bit_index: True to force 32-bit indices ("list32"), otherwise 16-bit ("list")
      - bsp_data: optional collision BSP payload, appended after index section
    """
    fmt = get_vertex_format(vertex_format_name)
    logger.info(
        f"Export .primitives: {filepath} | fmt={fmt.identifier} | verts={len(vertices)} | "
        f"idx={len(indices)} | groups={len(primitive_groups)} | bsp={'yes' if bsp_data else 'no'}"
    )

    _validate_inputs(vertices, indices, primitive_groups, fmt)
    create_directory(filepath)

    with open(filepath, "wb") as f:
        _write_vertex_section(f, vertices, fmt)
        _write_index_section(f, indices, primitive_groups, use_32bit_index)
        if bsp_data is not None:
            write_bsp_section(f, bsp_data)


def _validate_inputs(
    vertices: List[Dict],
    indices: List[int],
    primitive_groups: List[Tuple[int, int, int, int]],
    fmt: VertexFormat,
) -> None:
    if len(vertices) == 0:
        raise ValidationError("No vertices provided for .primitives export")

    # check vertex attributes presence
    required_keys = {a.name for a in fmt.attributes}
    for i, vtx in enumerate(vertices):
        missing = [k for k in required_keys if k not in vtx]
        if missing:
            raise ValidationError(
                f"Vertex {i} missing attributes for format '{fmt.identifier}': {missing}"
            )

    if len(indices) == 0:
        raise ValidationError("No indices provided for .primitives export")
    if any(ix < 0 for ix in indices):
        raise ValidationError("Indices must be non-negative")
    max_ix = max(indices)
    if max_ix >= len(vertices):
        raise ValidationError(f"Index {max_ix} exceeds vertex count {len(vertices)}")

    if len(primitive_groups) == 0:
        raise ValidationError("No primitive groups provided; at least one group is required")

    for gidx, (startIdx, numPrims, startVtx, numVtx) in enumerate(primitive_groups):
        if startIdx < 0 or numPrims <= 0 or startVtx < 0 or numVtx <= 0:
            raise ValidationError(f"Primitive group {gidx} has invalid stats: {(startIdx, numPrims, startVtx, numVtx)}")

        end_idx_byte = startIdx + numPrims * 3 - 1
        if end_idx_byte >= len(indices):
            raise ValidationError(
                f"Primitive group {gidx} exceeds index buffer length: end={end_idx_byte}, len={len(indices)}"
            )

        end_vtx = startVtx + numVtx - 1
        if end_vtx >= len(vertices):
            raise ValidationError(
                f"Primitive group {gidx} exceeds vertex buffer length: end={end_vtx}, len={len(vertices)}"
            )


def _pad_64bytes_ascii(name: str) -> bytes:
    b = name.encode("ascii", errors="strict")
    if len(b) > 64:
        raise ValidationError(f"Identifier exceeds 64 bytes: {name}")
    return b.ljust(64, b"\x00")


def _write_vertex_section(f, vertices: List[Dict], fmt: VertexFormat) -> None:
    write_bytes(f, _pad_64bytes_ascii(fmt.identifier))
    write_u32(f, len(vertices))
    for vtx in vertices:
        _write_vertex(f, vtx, fmt)


def _write_index_section(
    f,
    indices: List[int],
    primitive_groups: List[Tuple[int, int, int, int]],
    use_32bit_index: bool,
) -> None:
    index_fmt_name = "list32" if use_32bit_index else "list"
    write_bytes(f, _pad_64bytes_ascii(index_fmt_name))
    write_u32(f, len(indices))
    write_u32(f, len(primitive_groups))

    if use_32bit_index:
        for ix in indices:
            write_u32(f, ix)
    else:
        if max(indices) > 0xFFFF:
            raise ValidationError("Indices exceed 16-bit range; enable use_32bit_index=True")
        for ix in indices:
            write_u16(f, ix)

    for (startIdx, numPrims, startVtx, numVtx) in primitive_groups:
        write_u32(f, startIdx)
        write_u32(f, numPrims)
        write_u32(f, startVtx)
        write_u32(f, numVtx)


def _write_vertex(f, vtx: Dict, fmt: VertexFormat) -> None:
    """Serialize one vertex according to the chosen VertexFormat."""
    for attr in fmt.attributes:
        if attr.name == "position":
            x, y, z = vtx["position"]
            write_f32(f, x); write_f32(f, y); write_f32(f, z)
        elif attr.name == "normal":
            nx, ny, nz = vtx["normal"]
            u, v = compress_dir_to_u16x2((nx, ny, nz))
            write_u16(f, u); write_u16(f, v)
        elif attr.name == "uv0":
            u, v = pack_uv(*(vtx.get("uv0") or vtx.get("uv") or (0.0, 0.0)))
            write_f32(f, u); write_f32(f, v)
        elif attr.name == "tangent":
            tx, ty, tz = vtx.get("tangent", (1.0, 0.0, 0.0))
            u, v = compress_dir_to_u16x2((tx, ty, tz))
            write_u16(f, u); write_u16(f, v)
        elif attr.name == "binormal":
            bx, by, bz = vtx.get("binormal", (0.0, 1.0, 0.0))
            u, v = compress_dir_to_u16x2((bx, by, bz))
            write_u16(f, u); write_u16(f, v)
        elif attr.name == "bone_idx":
            b0, b1, b2 = quantize_indices_3(vtx.get("bone_idx") or vtx.get("bone_indices") or [])
            write_u8(f, b0); write_u8(f, b1); write_u8(f, b2)
        elif attr.name == "bone_w":
            # expects a list of weights (float)
            w0, w1, w2 = quantize_weights_3(
                vtx.get("bone_w") or vtx.get("bone_weights") or []
            )
            # we only store w0, w1; w2 is implied by sum=255, i.e. w2 = 255 - (w0 + w1)
            write_u8(f, w0)
            write_u8(f, w1)
        else:
            raise ValidationError(f"Unsupported vertex attribute in layout: {attr.name}")


if __name__ == "__main__":
    # Simple self-test: write a dummy .primitives with 1 triangle (no BSP)
    import os
    test_vertices = [
        {"position": (0.0, 0.0, 0.0), "normal": (0.0, 0.0, 1.0), "uv0": (0.0, 0.0), "tangent": (1.0, 0.0, 0.0), "binormal": (0.0, 1.0, 0.0)},
        {"position": (1.0, 0.0, 0.0), "normal": (0.0, 0.0, 1.0), "uv0": (1.0, 0.0), "tangent": (1.0, 0.0, 0.0), "binormal": (0.0, 1.0, 0.0)},
        {"position": (0.0, 1.0, 0.0), "normal": (0.0, 0.0, 1.0), "uv0": (0.0, 1.0), "tangent": (1.0, 0.0, 0.0), "binormal": (0.0, 1.0, 0.0)},
    ]
    test_indices = [0, 1, 2]
    test_groups = [(0, 1, 0, 3)]
    out_path = os.path.join(os.path.dirname(__file__), "test_output.primitives")
    export_primitives_file(out_path, test_vertices, test_indices, test_groups, "xyznuvtb", False, bsp_data=None)
    print(f"Dummy .primitives written to {out_path}")
