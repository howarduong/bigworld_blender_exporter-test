# 文件位置: bigworld_blender_exporter/formats/vertex_formats.py
# -*- coding: utf-8 -*-
"""
Vertex format registry for .primitives writer.

- Defines the exact serialization layout (order, type, byte size).
- Provides validation helpers to ensure vertex dictionaries match the chosen format.
- Aligns with primitives_format.py attribute names and packing logic.

Supported formats:
  - xyznuvtb           (static mesh with tangents/binormals)
  - xyznuviiiwwtb      (skinned mesh with up to 3 influences, tangents/binormals)
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple


# ----------------------------
# Data structures
# ----------------------------
@dataclass(frozen=True)
class VertexAttribute:
    # logical attribute name (must match primitives_format packing keys)
    name: str
    # storage type annotation (for reference/UI; writer decides exact packing)
    dtype: str
    # byte size of this attribute in serialized vertex (for stride calculation)
    byte_size: int


@dataclass(frozen=True)
class VertexFormat:
    # BigWorld vertex format name written to 64B header in .primitives
    identifier: str
    # ordered attributes; the order MUST match writer serialization
    attributes: List[VertexAttribute]
    # total vertex stride size in bytes (sum of attribute sizes)
    vertex_size: int
    # whether format contains bone indices/weights (skinning)
    has_skinning: bool


# ----------------------------
# Attribute definitions
# ----------------------------
def _attr(name: str, dtype: str, byte_size: int) -> VertexAttribute:
    return VertexAttribute(name=name, dtype=dtype, byte_size=byte_size)

# Common attributes aligned to primitives_format packing logic
POSITION_F32x3 = _attr("position", "f32x3", 12)
NORMAL_U16x2   = _attr("normal",   "u16x2", 4)   # compressed
UV_F32x2       = _attr("uv0",      "f32x2", 8)
TANGENT_U16x2  = _attr("tangent",  "u16x2", 4)   # compressed
BINORMAL_U16x2 = _attr("binormal", "u16x2", 4)   # compressed
BONE_IDX_U8x3  = _attr("bone_idx", "u8x3", 3)    # up to 3 influences
BONE_W_U8x2    = _attr("bone_w",   "u8x2", 2)    # store w0,w1; w2 = 255 - w0 - w1 (implicit)


# ----------------------------
# Registered formats
# ----------------------------
REGISTERED_FORMATS: Dict[str, VertexFormat] = {
    # Static mesh with tangents/binormals
    "xyznuvtb": VertexFormat(
        identifier="xyznuvtb",
        attributes=[
            POSITION_F32x3,
            NORMAL_U16x2,
            UV_F32x2,
            TANGENT_U16x2,
            BINORMAL_U16x2,
        ],
        vertex_size=(
            POSITION_F32x3.byte_size +
            NORMAL_U16x2.byte_size +
            UV_F32x2.byte_size +
            TANGENT_U16x2.byte_size +
            BINORMAL_U16x2.byte_size
        ),
        has_skinning=False,
    ),

    # Skinned mesh (up to 3 bone influences) with tangents/binormals
    "xyznuviiiwwtb": VertexFormat(
        identifier="xyznuviiiwwtb",
        attributes=[
            POSITION_F32x3,
            NORMAL_U16x2,
            UV_F32x2,
            BONE_IDX_U8x3,
            BONE_W_U8x2,
            TANGENT_U16x2,
            BINORMAL_U16x2,
        ],
        vertex_size=(
            POSITION_F32x3.byte_size +
            NORMAL_U16x2.byte_size +
            UV_F32x2.byte_size +
            BONE_IDX_U8x3.byte_size +
            BONE_W_U8x2.byte_size +
            TANGENT_U16x2.byte_size +
            BINORMAL_U16x2.byte_size
        ),
        has_skinning=True,
    ),
}


# ----------------------------
# Public API
# ----------------------------
def get_vertex_format(name: str) -> VertexFormat:
    fmt = REGISTERED_FORMATS.get(name)
    if not fmt:
        raise ValueError(f"Unsupported vertex format: {name}")
    return fmt


def list_formats() -> List[Tuple[str, int, bool]]:
    """
    Overview for UI: (identifier, vertex_size, has_skinning)
    """
    return [(v.identifier, v.vertex_size, v.has_skinning) for v in REGISTERED_FORMATS.values()]


def required_keys(fmt: VertexFormat) -> List[str]:
    """
    Return the list of required vertex dictionary keys in the exact serialization order.
    """
    return [a.name for a in fmt.attributes]


def validate_vertex_dict(vtx: Dict, fmt: VertexFormat) -> List[str]:
    """
    Validate a single vertex dictionary against the format.
    Returns a list of missing keys (empty if valid).
    """
    missing = []
    for a in fmt.attributes:
        if a.name not in vtx:
            # allow uv alias "uv" for "uv0"
            if a.name == "uv0" and ("uv" in vtx):
                continue
            missing.append(a.name)
    return missing


def validate_vertices(vertices: List[Dict], fmt: VertexFormat) -> Tuple[bool, str]:
    """
    Validate a list of vertex dictionaries. Returns (ok, message).
    """
    if not vertices:
        return False, "No vertices provided"

    for i, vtx in enumerate(vertices):
        missing = validate_vertex_dict(vtx, fmt)
        if missing:
            return False, f"Vertex {i} missing attributes for format '{fmt.identifier}': {missing}"

    return True, "OK"
