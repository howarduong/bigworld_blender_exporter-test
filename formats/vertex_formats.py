# formats/vertex_formats.py
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass(frozen=True)
class VertexAttribute:
    # name: logical attribute name
    name: str
    # dtype: storage type, e.g., f32x3, u16x2, u8x3
    dtype: str
    # size in bytes for this attribute
    byte_size: int

@dataclass(frozen=True)
class VertexFormat:
    # BigWorld vertex format name written in .primitives 64B header
    identifier: str
    # ordered attributes serialization layout
    attributes: List[VertexAttribute]
    # total vertex size in bytes
    vertex_size: int
    # whether format contains bone indices/weights
    has_skinning: bool

def _attr(name: str, dtype: str, byte_size: int) -> VertexAttribute:
    return VertexAttribute(name=name, dtype=dtype, byte_size=byte_size)

# Common attribute definitions
POSITION_F32x3   = _attr("position", "f32x3", 12)
NORMAL_U16x2     = _attr("normal",   "u16x2", 4)   # compressed 2D encoding of unit vector
UV_F32x2         = _attr("uv0",      "f32x2", 8)
TANGENT_U16x2    = _attr("tangent",  "u16x2", 4)   # compressed
BINORMAL_U16x2   = _attr("binormal", "u16x2", 4)   # compressed
BONE_IDX_U8x3    = _attr("bone_idx", "u8x3", 3)    # up to 3 influences
BONE_W_U8x2      = _attr("bone_w",   "u8x2", 2)    # store w0,w1 in bytes, w2 = 255 - w0 - w1

# Registered formats aligned to common BigWorld usage
# Note: The serialization order must exactly match the identifier’s expected layout.
REGISTERED_FORMATS: Dict[str, VertexFormat] = {
    # Static mesh with tangents
    "xyznuvtb": VertexFormat(
        identifier="xyznuvtb",
        attributes=[
            POSITION_F32x3,
            NORMAL_U16x2,
            UV_F32x2,
            TANGENT_U16x2,
            BINORMAL_U16x2,
        ],
        vertex_size=POSITION_F32x3.byte_size
                    + NORMAL_U16x2.byte_size
                    + UV_F32x2.byte_size
                    + TANGENT_U16x2.byte_size
                    + BINORMAL_U16x2.byte_size,
        has_skinning=False
    ),
    # Skinned mesh with up to 3 bone influences + tangents
    "xyznuviiiwwtb": VertexFormat(
        identifier="xyznuviiiwwtb",
        attributes=[
            POSITION_F32x3,
            NORMAL_U16x2,
            UV_F32x2,
            # iii (bone indices) and ww (weights quantized)
            BONE_IDX_U8x3,
            BONE_W_U8x2,
            TANGENT_U16x2,
            BINORMAL_U16x2,
        ],
        vertex_size=POSITION_F32x3.byte_size
                    + NORMAL_U16x2.byte_size
                    + UV_F32x2.byte_size
                    + BONE_IDX_U8x3.byte_size
                    + BONE_W_U8x2.byte_size
                    + TANGENT_U16x2.byte_size
                    + BINORMAL_U16x2.byte_size,
        has_skinning=True
    ),
}

def get_vertex_format(name: str) -> VertexFormat:
    fmt = REGISTERED_FORMATS.get(name)
    if not fmt:
        raise ValueError(f"Unsupported vertex format: {name}")
    return fmt

def list_formats() -> List[Tuple[str, int, bool]]:
    """
    Returns a concise overview for UI:
    (identifier, vertex_size, has_skinning)
    """
    return [(v.identifier, v.vertex_size, v.has_skinning) for v in REGISTERED_FORMATS.values()]
